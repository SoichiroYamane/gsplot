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

_TYPE_ALIAS_COMMENTS = {
    "ColorSpec": "# Public type alias: ColorSpec",
    "MosaicSpec": "# Public type alias: MosaicSpec",
    "NormalizeSpec": "# Public type alias: NormalizeSpec",
    "Limit": "# Public type alias: Limit",
    "Scale": "# Public type alias: Scale",
    "TickSpec": "# Public type alias: TickSpec",
    "LabelRecord": "# Public type alias: LabelRecord",
    "LabelRecords": "# Public type alias: LabelRecords",
}
_NO_EXAMPLES = {
    "GsplotError",
    "ConfigError",
    "DataError",
    "LayoutError",
    "PlotError",
    "OutputError",
    "MetadataError",
}
_NO_RAISES = {"as_mapping", "build_info", "default", "transparent", "white"}


def _has_section(doc: str, section: str) -> bool:
    """Return whether a NumPy-style section heading is present."""

    return any(line.strip() == section for line in doc.splitlines())


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
    if (
        not _has_section(doc, "Returns")
        and signature.return_annotation is not inspect.Signature.empty
    ):
        errors.append(f"{name}: return annotation requires a Returns section")
    if name.split(".")[-1] not in _NO_RAISES and not _has_section(doc, "Raises"):
        errors.append(f"{name}: validation/error contract requires a Raises section")
    if name.split(".")[-1] not in _NO_EXAMPLES and not _has_section(doc, "Examples"):
        errors.append(f"{name}: public callable requires an Examples section")
    return errors


def _check_class(name: str, value: type[Any]) -> list[str]:
    """Check one public class, its fields, and public methods."""

    errors: list[str] = []
    doc = inspect.getdoc(value) or ""
    if not doc:
        return [f"{name}: missing class docstring"]
    if issubclass(value, BaseException):
        return errors
    if name not in _NO_EXAMPLES and not _has_section(doc, "Examples"):
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
    for name, (module_name, attribute_name) in _CANONICAL_EXPORTS.items():
        try:
            root_value = getattr(gsplot, name)
            module: ModuleType = __import__(module_name, fromlist=[attribute_name])
            canonical_value = getattr(module, attribute_name)
        except (AttributeError, ImportError) as exc:
            errors.append(f"{name}: cannot resolve canonical export ({exc})")
            continue
        if inspect.isfunction(canonical_value) or inspect.isclass(canonical_value):
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

    version_doc = (
        inspect.getdoc(__import__("gsplot.version", fromlist=["__version__"])) or ""
    )
    for attribute in ("__version__", "__commit__"):
        if attribute not in version_doc:
            errors.append(f"gsplot.version: module docstring omits {attribute}")

    type_source = repository_root / "src" / "gsplot" / "_core" / "types.py"
    source = type_source.read_text(encoding="utf-8")
    for name, marker in _TYPE_ALIAS_COMMENTS.items():
        if marker not in source:
            errors.append(f"{type_source}: missing module comment for {name}")
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
