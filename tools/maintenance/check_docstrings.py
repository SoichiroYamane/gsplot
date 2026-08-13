"""Audit canonical root documentation against the live public objects."""

from __future__ import annotations

import inspect
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

import gsplot
from gsplot._compat.root import _CANONICAL_EXPORTS
from gsplot._core.types import _PUBLIC_TYPE_ALIAS_DOCS

_NO_RAISES = {"as_mapping", "build_info", "default", "transparent", "white"}
_REVIEWED_DEFAULTS: dict[str, dict[str, object]] = {
    "colors": {"n": 10, "cmap": "viridis", "reverse": False},
    "index": {"labels": None, "loc": "out", "size": "large", "props": None},
    "inset": {
        "label": None,
        "zoom": False,
        "style": "paper",
        "zorder": 5,
        "zoom_zorder": None,
    },
    "label": {
        "xlabel": "",
        "ylabel": "",
        "xlim": None,
        "ylim": None,
        "xscale": "linear",
        "yscale": "linear",
        "xticks": None,
        "yticks": None,
        "minor": True,
        "xminor": None,
        "yminor": None,
        "pad": 5,
        "xpad": None,
        "ypad": None,
        "square": False,
        "index": False,
    },
    "legend": {
        "handles": None,
        "labels": None,
        "handler_map": None,
        "loc": "best",
        "frameon": False,
        "fancybox": False,
        "labelspacing": 0.3,
        "handlelength": None,
        "reverse": False,
        "replace": False,
        "props": None,
    },
    "line": {
        "series": None,
        "label": None,
        "c": None,
        "marker": "o",
        "ms": 7,
        "mew": 1.5,
        "mec": None,
        "mfc": None,
        "alpha_mfc": 0.2,
        "ls": "--",
        "lw": 1,
        "alpha": 1,
        "config": None,
        "props": None,
    },
    "paper": {"cycle": True},
    "read": {
        "loader": "genfromtxt",
        "delimiter": ",",
        "comments": "#",
        "skip_header": 0,
        "usecols": None,
        "unpack": True,
        "ndmin": 1,
        "dtype": float,
    },
    "save": {
        "formats": None,
        "dpi": 600,
        "crop": True,
        "pad": None,
        "show": True,
        "close": False,
        "create_parent": False,
        "overwrite": True,
        "transparent": False,
        "metadata": None,
    },
    "scatter": {
        "series": None,
        "label": None,
        "c": None,
        "marker": "o",
        "s": 1,
        "alpha": 1,
        "config": None,
        "props": None,
    },
    "square": {"aspect": 1},
    "subplots": {
        "nrows": None,
        "ncols": None,
        "mosaic": None,
        "size": "auto",
        "unit": "in",
        "sharex": False,
        "sharey": False,
        "squeeze": True,
        "width_ratios": None,
        "height_ratios": None,
        "subplot_kw": None,
        "fig": None,
        "clear": False,
        "layout": "auto",
        "style": "auto",
        "config": None,
        "figsize": None,
        "tight_layout": None,
        "constrained_layout": None,
    },
}


def _has_section(doc: str, section: str) -> bool:
    """Return whether a NumPy-style section heading is present."""

    return any(line.strip() == section for line in doc.splitlines())


def _section_lines(doc: str, section: str) -> tuple[str, ...]:
    """Return the body of one NumPy-style section."""

    lines = doc.splitlines()
    for index in range(len(lines) - 1):
        if lines[index].strip() != section or set(lines[index + 1].strip()) != {"-"}:
            continue
        body: list[str] = []
        for position in range(index + 2, len(lines)):
            if (
                position + 1 < len(lines)
                and lines[position].strip()
                and set(lines[position + 1].strip()) == {"-"}
            ):
                break
            body.append(lines[position])
        return tuple(body)
    return ()


def _documented_parameters(doc: str) -> set[str]:
    """Return normalized names declared by a NumPy Parameters section."""

    names: set[str] = set()
    for line in _section_lines(doc, "Parameters"):
        if not line or line != line.lstrip():
            continue
        declaration = line.split(":", 1)[0]
        for name in declaration.split(","):
            normalized = name.strip().strip("`").lstrip("*")
            if normalized:
                names.add(normalized)
    return names


def _check_reviewed_defaults(name: str, signature: inspect.Signature) -> list[str]:
    """Check user-visible concise defaults against the reviewed contract."""

    errors: list[str] = []
    for parameter_name, expected in _REVIEWED_DEFAULTS.get(name, {}).items():
        parameter = signature.parameters.get(parameter_name)
        if parameter is None:
            errors.append(
                f"{name}: reviewed default parameter {parameter_name!r} missing"
            )
        elif (
            type(parameter.default) is not type(expected)
            or parameter.default != expected
        ):
            errors.append(
                f"{name}: {parameter_name} default must be {expected!r}, "
                f"got {parameter.default!r}"
            )
    return errors


def _check_callable(name: str, value: Any) -> list[str]:
    """Check one canonical root function or method."""

    errors: list[str] = []
    doc = inspect.getdoc(value) or ""
    if not doc:
        errors.append(f"{name}: missing docstring")
        return errors
    try:
        signature = inspect.signature(value)
    except (TypeError, ValueError) as exc:
        errors.append(f"{name}: signature is not inspectable ({exc})")
        return errors
    parameters = tuple(
        parameter
        for parameter in signature.parameters.values()
        if parameter.name not in {"self", "cls"}
    )
    if parameters and not _has_section(doc, "Parameters"):
        errors.append(f"{name}: parameters require a Parameters section")
    elif parameters:
        expected_names = {parameter.name for parameter in parameters}
        documented_names = _documented_parameters(doc)
        missing = sorted(expected_names - documented_names)
        stale = sorted(documented_names - expected_names)
        if missing:
            errors.append(f"{name}: undocumented parameters: {', '.join(missing)}")
        if stale:
            errors.append(f"{name}: stale documented parameters: {', '.join(stale)}")
    if (
        not _has_section(doc, "Returns")
        and signature.return_annotation is not inspect.Signature.empty
    ):
        errors.append(f"{name}: return annotation requires a Returns section")
    elif signature.return_annotation is not inspect.Signature.empty and not any(
        line.strip() for line in _section_lines(doc, "Returns")
    ):
        errors.append(f"{name}: Returns section must document the returned value")
    if name.split(".")[-1] not in _NO_RAISES and not _has_section(doc, "Raises"):
        errors.append(f"{name}: validation/error contract requires a Raises section")
    if not _has_section(doc, "Examples"):
        errors.append(f"{name}: public callable requires an Examples section")
    errors.extend(_check_reviewed_defaults(name.split(".")[-1], signature))
    return errors


def _check_class(name: str, value: type[Any]) -> list[str]:
    """Check one public class, its fields, and public methods."""

    errors: list[str] = []
    doc = inspect.getdoc(value) or ""
    if not doc:
        return [f"{name}: missing class docstring"]
    if issubclass(value, BaseException):
        if not _has_section(doc, "Examples"):
            errors.append(f"{name}: public exception requires an Examples section")
        return errors
    if not _has_section(doc, "Examples"):
        errors.append(f"{name}: public constructor requires an Examples section")
    if is_dataclass(value):
        if not _has_section(doc, "Parameters"):
            errors.append(f"{name}: dataclass fields require a Parameters section")
        for item in fields(value):
            if item.name not in doc:
                errors.append(f"{name}: field {item.name!r} is not documented")
    for method_name, method in inspect.getmembers(value):
        if method_name.startswith("_"):
            continue
        if inspect.isroutine(method):
            errors.extend(_check_callable(f"{name}.{method_name}", method))
    return errors


def _check_root(repository_root: Path) -> list[str]:
    """Check root exports, re-export fidelity, and stable metadata values."""

    errors: list[str] = []
    type_aliases: set[str] = set()
    for name, (module_name, attribute_name) in _CANONICAL_EXPORTS.items():
        try:
            root_value = getattr(gsplot, name)
            module: ModuleType = __import__(module_name, fromlist=[attribute_name])
            canonical_value = getattr(module, attribute_name)
        except (AttributeError, ImportError) as exc:
            errors.append(f"{name}: cannot resolve canonical export ({exc})")
            continue
        if inspect.isfunction(canonical_value) or inspect.isclass(canonical_value):
            root_signature: inspect.Signature | None
            canonical_signature: inspect.Signature | None
            try:
                root_signature = inspect.signature(root_value)
                canonical_signature = inspect.signature(canonical_value)
            except (TypeError, ValueError):
                root_signature = canonical_signature = None
            if root_signature != canonical_signature:
                errors.append(
                    f"{name}: root signature differs from canonical signature"
                )
        if inspect.getdoc(root_value) != inspect.getdoc(canonical_value):
            errors.append(f"{name}: root docstring differs from canonical docstring")
        if inspect.isfunction(canonical_value):
            errors.extend(_check_callable(name, canonical_value))
        elif inspect.isclass(canonical_value):
            errors.extend(_check_class(name, canonical_value))
        else:
            type_aliases.add(name)

    version_doc = (
        inspect.getdoc(__import__("gsplot.version", fromlist=["__version__"])) or ""
    )
    for attribute in ("__version__", "__commit__"):
        if attribute not in version_doc:
            errors.append(f"gsplot.version: module docstring omits {attribute}")

    type_source = repository_root / "src" / "gsplot" / "_core" / "types.py"
    source = type_source.read_text(encoding="utf-8")
    documented_aliases = set(_PUBLIC_TYPE_ALIAS_DOCS)
    missing_aliases = sorted(type_aliases - documented_aliases)
    stale_aliases = sorted(documented_aliases - type_aliases)
    if missing_aliases:
        errors.append("undocumented public type aliases: " + ", ".join(missing_aliases))
    if stale_aliases:
        errors.append("stale public type alias docs: " + ", ".join(stale_aliases))
    for name, description in _PUBLIC_TYPE_ALIAS_DOCS.items():
        marker = f"# Public type alias: {name};"
        if marker not in source:
            errors.append(f"{type_source}: missing module comment for {name}")
        if not description.strip():
            errors.append(f"{name}: public type alias description is empty")
        if not _has_section(description, "Examples") or ">>>" not in description:
            errors.append(f"{name}: public type alias requires an executable example")
    return errors


def main() -> int:
    """Run the documentation audit and print all missing contract entries."""

    repository_root = Path(__file__).resolve().parents[2]
    errors = _check_root(repository_root)
    if errors:
        print("Canonical docstring audit failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Canonical docstring audit passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
