"""Print a complete JSON inventory of the current public API boundary.

The inventory combines the root ``__all__``, lazy canonical and legacy
manifests, direct metadata attributes, and compatibility module paths recorded
in the migration guide. It is read-only and writes only JSON to standard
output.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import inspect
import json
import re
import sys
import warnings
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Final, get_origin

# Frozen from the reviewed v0.3.0 tag.  CI must not need Git history to know
# which compatibility names and documented module exports the 1.x window
# protects.
HISTORICAL_ROOT_ALL: Final[tuple[str, ...]] = (
    "get_cmap",
    "load_file",
    "load_file_fast",
    "axes",
    "axes_inset",
    "axes_inset_padding",
    "get_figure_size",
    "show",
    "hello_world",
    "config_load",
    "config_dict",
    "config_entry_option",
    "home",
    "pwd",
    "pwd_move",
    "pwd_main",
    "line",
    "line_colormap_solid",
    "line_colormap_dashed",
    "scatter",
    "scatter_colormap",
    "graph_square",
    "graph_square_axes",
    "graph_white",
    "graph_white_axes",
    "graph_transparent",
    "graph_transparent_axes",
    "graph_facecolor",
    "label",
    "label_add_index",
    "legend",
    "legend_axes",
    "legend_handlers",
    "legend_reverse",
    "legend_get_handlers",
    "legend_colormap",
    "ticks_off",
    "ticks_on",
    "ticks_on_axes",
    "title",
    "title_axes",
)
HISTORICAL_DIRECT_ATTRIBUTES: Final[tuple[str, ...]] = (
    "Config",
    "logger",
    "save_metadata",
    "__commit__",
    "__version__",
)
HISTORICAL_DOCUMENTED_MODULES: Final[dict[str, tuple[str, ...]]] = {
    "gsplot.color.colormap": ("get_cmap",),
    "gsplot.config.config": (
        "config_load",
        "config_dict",
        "config_entry_option",
    ),
    "gsplot.data.load_file": ("load_file", "load_file_fast"),
    "gsplot.figure.axes": ("axes",),
    "gsplot.figure.axes_inset": ("axes_inset", "axes_inset_padding"),
    "gsplot.figure.figure_tools": ("get_figure_size",),
    "gsplot.figure.show": ("show",),
    "gsplot.hello_world.hello_world": ("hello_world",),
    "gsplot.path.path": ("home", "pwd", "pwd_move", "pwd_main"),
    "gsplot.plot.line": ("line",),
    "gsplot.plot.line_colormap_dashed": ("line_colormap_dashed",),
    "gsplot.plot.line_colormap_solid": ("line_colormap_solid",),
    "gsplot.plot.scatter": ("scatter",),
    "gsplot.plot.scatter_colormap": ("scatter_colormap",),
    "gsplot.style.graph": (
        "graph_square",
        "graph_square_axes",
        "graph_white",
        "graph_white_axes",
        "graph_transparent",
        "graph_transparent_axes",
        "graph_facecolor",
    ),
    "gsplot.style.label": ("label", "label_add_index"),
    "gsplot.style.legend": (
        "legend",
        "legend_axes",
        "legend_handlers",
        "legend_reverse",
        "legend_get_handlers",
    ),
    "gsplot.style.legend_colormap": ("legend_colormap",),
    "gsplot.style.ticks": ("ticks_off", "ticks_on", "ticks_on_axes"),
    "gsplot.style.title": ("title", "title_axes"),
}


def _kind(value: Any) -> str:
    """Return a stable, small category for an inspected public value."""

    if get_origin(value) is not None:
        return "type_alias"
    if inspect.isclass(value):
        return "class"
    if inspect.isfunction(value):
        return "function"
    if inspect.ismodule(value):
        return "module"
    if callable(value):
        return "callable"
    return type(value).__name__


def _signature(value: Any, kind: str) -> str | None:
    """Return a signature when Python exposes one for ``value``."""

    if kind not in {"callable", "class", "function"}:
        return None
    try:
        return str(inspect.signature(value))
    except (TypeError, ValueError):
        return None


def _annotation(value: Any) -> str | None:
    """Format one annotation without exposing Python object addresses."""

    if value is inspect.Signature.empty:
        return None
    return inspect.formatannotation(value)


def _call_contract(value: Any, kind: str) -> dict[str, Any] | None:
    """Return structured parameters, defaults, and return annotation."""

    if kind not in {"callable", "class", "function"}:
        return None
    try:
        signature = inspect.signature(value)
    except (TypeError, ValueError):
        return None
    return {
        "parameters": [
            {
                "annotation": _annotation(parameter.annotation),
                "default": (
                    None
                    if parameter.default is inspect.Parameter.empty
                    else repr(parameter.default)
                ),
                "kind": parameter.kind.name,
                "name": parameter.name,
                "required": parameter.default is inspect.Parameter.empty,
            }
            for parameter in signature.parameters.values()
        ],
        "return_annotation": _annotation(signature.return_annotation),
    }


def _docstring_record(value: Any) -> dict[str, str] | None:
    """Return a compact, reproducible fingerprint of one public docstring."""

    docstring = inspect.getdoc(value)
    if docstring is None:
        return None
    return {
        "sha256": hashlib.sha256(docstring.encode("utf-8")).hexdigest(),
        "summary": docstring.splitlines()[0],
    }


def _manifest(value: object) -> dict[str, dict[str, str]]:
    """Normalize one finite lazy-export manifest for JSON output."""

    if not isinstance(value, dict):
        raise TypeError("lazy export manifest must be a dictionary")
    result: dict[str, dict[str, str]] = {}
    for name, target in value.items():
        if not (
            isinstance(name, str)
            and isinstance(target, tuple)
            and len(target) == 2
            and all(isinstance(part, str) for part in target)
        ):
            raise TypeError("lazy export manifest contains an invalid entry")
        result[name] = {"module": target[0], "attribute": target[1]}
    return dict(sorted(result.items()))


def _documented_compatibility_paths(path: Path) -> list[str]:
    """Read compatibility paths from first cells in the migration table."""

    paths: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if not cells:
            continue
        value = cells[0].strip("`")
        if value.startswith("gsplot.") and "(" not in value:
            paths.add(value)
    return sorted(paths)


def _type_checking_exports(path: Path) -> list[str]:
    """Return names made visible to static analyzers at the lazy root."""

    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if not (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        ):
            continue
        for child in ast.walk(node):
            if isinstance(child, (ast.Import, ast.ImportFrom)):
                names.update(
                    name
                    for name in (alias.asname or alias.name for alias in child.names)
                    if not name.startswith("_")
                )
            elif isinstance(child, ast.AnnAssign) and isinstance(
                child.target, ast.Name
            ):
                names.add(child.target.id)
    return sorted(names)


def _api_index_exports(path: Path) -> list[str]:
    """Return root names listed in the canonical autosummary index."""

    pattern = re.compile(r"^\s{3}gsplot\.([A-Za-z_]\w*)\s*$", re.MULTILINE)
    return pattern.findall(path.read_text(encoding="utf-8"))


def _compatibility_modules(paths: Iterable[str]) -> dict[str, list[str]]:
    """Import documented shims and record their declared public exports."""

    result: dict[str, list[str]] = {}
    root = sys.modules.get("gsplot")
    missing = object()
    previous: dict[str, object] = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            for path in sorted(paths):
                top_level = path.split(".", 2)[1]
                if root is not None and top_level not in previous:
                    previous[top_level] = root.__dict__.get(top_level, missing)
                module = importlib.import_module(path)
                result[path] = list(getattr(module, "__all__", ()))
    finally:
        if root is not None:
            for name, value in previous.items():
                if value is missing:
                    root.__dict__.pop(name, None)
                else:
                    root.__dict__[name] = value
    return result


def collect(
    module_name: str = "gsplot", migration_doc: Path | None = None
) -> dict[str, Any]:
    """Collect every reviewed root and documented compatibility surface."""

    module = importlib.import_module(module_name)
    names: Iterable[str] = getattr(module, "__all__", ())
    exports: list[dict[str, Any]] = []

    for name in names:
        value = getattr(module, name)
        kind = _kind(value)
        exports.append(
            {
                "name": name,
                "call_contract": _call_contract(value, kind),
                "docstring": _docstring_record(value),
                "kind": kind,
                "module": getattr(value, "__module__", None),
                "qualname": getattr(value, "__qualname__", None),
                "signature": _signature(value, kind),
            }
        )

    boundary = importlib.import_module(f"{module_name}._compat.root")
    if migration_doc is None:
        candidate = (
            Path(__file__).resolve().parents[2] / "docs/project/api-migration.md"
        )
        migration_doc = candidate if candidate.is_file() else None
    documented_paths = (
        _documented_compatibility_paths(migration_doc)
        if migration_doc is not None
        else []
    )
    metadata = [name for name in ("__commit__", "__version__") if hasattr(module, name)]
    root_source = Path(module.__file__).resolve()
    repository_root = Path(__file__).resolve().parents[2]
    api_index = repository_root / "docs/api_reference/apis.rst"

    return {
        "api_index": _api_index_exports(api_index) if api_index.is_file() else [],
        "canonical_manifest": _manifest(boundary._CANONICAL_EXPORTS),
        "compatibility_modules": _compatibility_modules(documented_paths),
        "documented_compatibility_paths": documented_paths,
        "exports": exports,
        "historical_baseline": {
            "documented_modules": {
                name: list(exports)
                for name, exports in sorted(HISTORICAL_DOCUMENTED_MODULES.items())
            },
            "root_all": list(HISTORICAL_ROOT_ALL),
            "root_direct_attributes": list(HISTORICAL_DIRECT_ATTRIBUTES),
            "tag": "v0.3.0",
        },
        "legacy_discoverable": list(boundary.legacy_names()),
        "legacy_manifest": _manifest(boundary._LEGACY_EXPORTS),
        "metadata_attributes": metadata,
        "module": module_name,
        "root_all": list(names),
        "type_checking_exports": _type_checking_exports(root_source),
    }


def main() -> None:
    """Parse arguments and print the inventory as deterministic JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module",
        default="gsplot",
        help="package module to inspect (default: gsplot)",
    )
    parser.add_argument(
        "--migration-doc",
        type=Path,
        help="migration matrix used to inventory documented compatibility paths",
    )
    args = parser.parse_args()
    print(
        json.dumps(
            collect(args.module, migration_doc=args.migration_doc),
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
