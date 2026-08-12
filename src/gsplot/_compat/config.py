"""Root-boundary configuration compatibility adapter.

Canonical configuration readers are strict.  This module is intentionally the
only root-facing place that translates a schema-less 0.x configuration file;
the result is a fresh canonical :class:`gsplot.Config` and no process-wide
configuration or Matplotlib state is changed.
"""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from os import PathLike
from pathlib import Path
from typing import Any

from .._config.model import Config
from .._config.schema import DEFAULT_CONFIG_NAME, read_json_file


def discover_config_path(
    *,
    cwd: str | Path | None = None,
    home: str | Path | None = None,
) -> Path | None:
    """Find a legacy ``gsplot.json`` using the documented compatibility order."""

    current = Path.cwd() if cwd is None else Path(cwd).expanduser()
    home_path = Path.home() if home is None else Path(home).expanduser()
    candidates = (
        current / DEFAULT_CONFIG_NAME,
        home_path / ".config" / "gsplot" / DEFAULT_CONFIG_NAME,
        home_path / DEFAULT_CONFIG_NAME,
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


def _legacy_mapping(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Translate the safe subset of a schema-less legacy mapping."""

    figure: dict[str, Any] = {}
    plotting: dict[str, Any] = {}
    source_figure = raw.get("figure")
    if isinstance(source_figure, Mapping):
        for key in (
            "figsize",
            "unit",
            "squeeze",
            "tight_layout",
            "constrained_layout",
        ):
            if key in source_figure:
                figure[key] = source_figure[key]

    source_plotting = raw.get("plotting")
    if isinstance(source_plotting, Mapping):
        for key in ("default_color", "default_cmap", "nonfinite"):
            if key in source_plotting:
                plotting[key] = source_plotting[key]

    rc_params = raw.get("rcParams")
    if isinstance(rc_params, Mapping) and "figsize" not in figure:
        legacy_size = rc_params.get("figure.figsize")
        if isinstance(legacy_size, (list, tuple)) and len(legacy_size) == 2:
            figure["figsize"] = list(legacy_size)

    # A non-inch unit without a size was not a valid canonical configuration;
    # dropping that isolated legacy value is safer than manufacturing a size.
    if figure.get("figsize") is None and figure.get("unit") not in {None, "in"}:
        figure.pop("unit", None)
    canonical_figure: dict[str, Any] = {}
    if "figsize" in figure:
        canonical_figure["size"] = figure["figsize"]
    if "unit" in figure:
        canonical_figure["unit"] = figure["unit"]
    if "squeeze" in figure:
        canonical_figure["squeeze"] = figure["squeeze"]
    tight = figure.get("tight_layout", False)
    constrained = figure.get("constrained_layout", False)
    if not isinstance(tight, bool) or not isinstance(constrained, bool):
        canonical_figure["layout"] = "invalid"
    elif tight and constrained:
        canonical_figure["layout"] = "invalid"
    elif tight:
        canonical_figure["layout"] = "tight"
    elif constrained:
        canonical_figure["layout"] = "constrained"
    else:
        canonical_figure["layout"] = "none"

    translated: dict[str, Any] = {"schema_version": 2}
    if canonical_figure:
        translated["figure"] = canonical_figure
    if plotting:
        translated["plotting"] = plotting
    return translated


def _warn_legacy_sections(raw: Mapping[str, Any]) -> None:
    """Explain ignored legacy facilities without exposing their values."""

    if any(key in raw for key in ("backend", "backends")):
        warnings.warn(
            "legacy backend configuration is ignored; call gsplot.use_backend() "
            "before creating a Figure",
            DeprecationWarning,
            stacklevel=3,
        )
    if any(key in raw for key in ("rich", "traceback")):
        warnings.warn(
            "legacy Rich/traceback configuration is ignored; use standard logging "
            "and explicit application configuration",
            DeprecationWarning,
            stacklevel=3,
        )
    if any(key in raw for key in ("logging", "log", "metadata", "yaml")):
        warnings.warn(
            "legacy logging, YAML, or metadata configuration is ignored; use "
            "standard logging, gsplot.write_meta(), and explicit JSON",
            DeprecationWarning,
            stacklevel=3,
        )
    known_sections = {
        "figure",
        "plotting",
        "rcParams",
        "backend",
        "backends",
        "rich",
        "traceback",
        "logging",
        "log",
        "metadata",
        "yaml",
    }
    unknown = sorted(key for key in raw if key not in known_sections)
    if unknown:
        warnings.warn(
            "legacy configuration section(s) are ignored: "
            + ", ".join(unknown)
            + "; migrate to the schema_version 2 figure/plotting sections",
            DeprecationWarning,
            stacklevel=3,
        )
    for section_name, allowed in (
        (
            "figure",
            {"figsize", "unit", "squeeze", "tight_layout", "constrained_layout"},
        ),
        ("plotting", {"default_color", "default_cmap", "nonfinite"}),
    ):
        section = raw.get(section_name)
        if isinstance(section, Mapping):
            section_unknown = sorted(key for key in section if key not in allowed)
            if section_unknown:
                warnings.warn(
                    f"legacy {section_name} option(s) are ignored: "
                    + ", ".join(section_unknown),
                    DeprecationWarning,
                    stacklevel=3,
                )
    if "rcParams" in raw:
        warnings.warn(
            "legacy rcParams are not applied; use Matplotlib rc_context() or "
            "explicit gsplot arguments",
            DeprecationWarning,
            stacklevel=3,
        )


def load_config(
    path: str | PathLike[str] | None = None,
) -> Config:
    """Load canonical configuration and translate one schema-less legacy file.

    Parameters
    ----------
    path
        Explicit JSON configuration file, or ``None`` to discover the first
        documented ``gsplot.json`` candidate.

    Returns
    -------
    Config
        A fresh immutable configuration value.

    Raises
    ------
    ConfigError
        If the selected file is missing, malformed, or violates the target
        schema.  A schema-less legacy file is translated with a warning.

    Examples
    --------
    >>> import gsplot as gs
    >>> config = gs.load_config(path=None)
    >>> config.schema_version
    2

    The canonical file format requires integer ``schema_version`` ``2``.  A
    schema-less file is accepted only through this root compatibility boundary,
    translated to the reviewed subset, and accompanied by a deprecation
    warning.  No legacy ``rcParams`` or function-entry state is applied.
    """

    selected: Path | None
    if path is not None:
        selected = Path(path)
    else:
        selected = discover_config_path()
    if selected is None:
        return Config()
    raw = read_json_file(selected)
    if "schema_version" in raw:
        return Config.from_mapping(raw)
    warnings.warn(
        "schema-less gsplot configuration is deprecated; migrate to schema_version 2",
        DeprecationWarning,
        stacklevel=2,
    )
    _warn_legacy_sections(raw)
    return Config.from_mapping(_legacy_mapping(raw))


__all__ = ["discover_config_path", "load_config"]
