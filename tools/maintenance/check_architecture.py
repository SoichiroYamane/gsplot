"""Statically enforce the public package and dependency boundaries.

This checker deliberately uses only the standard library and source text.  It
must be safe to run before installing gsplot and must never import the package
whose boundaries it is checking.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

CANONICAL_PACKAGES = ("_core", "_config", "_figure", "_plot", "_style", "_io")
PRIVATE_PACKAGES = ("_compat",) + CANONICAL_PACKAGES
LEGACY_PACKAGES = (
    "base",
    "color",
    "config",
    "data",
    "figure",
    "hello_world",
    "path",
    "plot",
    "style",
)
RUNTIME_FORBIDDEN_ROOTS = ("tests", "demo", "examples", "tools")


def _module_name(path: Path, source_root: Path) -> str:
    """Return the import name represented by one source file."""

    relative = path.relative_to(source_root).with_suffix("")
    parts = ("gsplot",) + relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve_from(
    module: str, level: int, imported: str | None, *, is_package: bool = False
) -> str:
    """Resolve a relative import without importing any package."""

    parts = module.split(".") if is_package else module.split(".")[:-1]
    for _ in range(max(level - 1, 0)):
        if parts:
            parts.pop()
    if imported:
        parts.extend(imported.split("."))
    return ".".join(parts)


def _imports(
    tree: ast.AST, module: str, *, is_package: bool = False
) -> tuple[str, ...]:
    """Collect resolved import module names from one syntax tree."""

    result: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result.append(
                _resolve_from(module, node.level, node.module, is_package=is_package)
            )
    return tuple(result)


def _read_tree(path: Path) -> ast.Module:
    """Parse one source file with a useful failure location."""

    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise ValueError(f"could not parse {path}: {exc}") from exc


def _check_import_edges(source_root: Path) -> list[str]:
    """Reject imports that violate the documented dependency direction."""

    errors: list[str] = []
    legacy_roots = tuple(f"gsplot.{name}" for name in LEGACY_PACKAGES)
    canonical_roots = tuple(f"gsplot.{name}" for name in CANONICAL_PACKAGES)
    for path in sorted(source_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        module = _module_name(path, source_root)
        tree = _read_tree(path)
        for imported in _imports(tree, module, is_package=path.name == "__init__.py"):
            if module.startswith(canonical_roots):
                if imported.startswith("gsplot._compat") or imported.startswith(
                    legacy_roots
                ):
                    errors.append(
                        f"{path}: canonical module imports forbidden compatibility edge "
                        f"{imported}"
                    )
                if (
                    module.startswith("gsplot._core")
                    and imported == "matplotlib.pyplot"
                ):
                    errors.append(f"{path}: _core must not import matplotlib.pyplot")
            if imported == "matplotlib.pyplot" and module.startswith("gsplot._core"):
                errors.append(f"{path}: _core must not import matplotlib.pyplot")
            if module.startswith("gsplot") and imported.startswith(
                RUNTIME_FORBIDDEN_ROOTS
            ):
                errors.append(
                    f"{path}: runtime package imports repository-only module {imported}"
                )
    return errors


def _check_private_initializers(source_root: Path) -> list[str]:
    """Ensure every private implementation package is explicit."""

    errors: list[str] = []
    for package in PRIVATE_PACKAGES:
        initializer = source_root / package / "__init__.py"
        if not initializer.is_file():
            errors.append(f"missing private package initializer: {initializer}")
    return errors


def _check_shim(path: Path, source_root: Path) -> list[str]:
    """Check that one historical module contains forwarding code only."""

    errors: list[str] = []
    tree = _read_tree(path)
    module = _module_name(path, source_root)
    if not any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "_implementation"
            for target in node.targets
        )
        for node in tree.body
    ):
        errors.append(f"{path}: historical shim must assign _implementation")
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef)):
            errors.append(f"{path}: historical shim contains implementation code")
        if isinstance(node, (ast.FunctionDef,)) and node.name not in {
            "__getattr__",
            "__dir__",
        }:
            errors.append(
                f"{path}: historical shim defines unexpected function {node.name}"
            )
        if isinstance(node, ast.Import):
            errors.append(f"{path}: historical shim has a direct import")
        if isinstance(node, ast.ImportFrom):
            imported = _resolve_from(
                module,
                node.level,
                node.module,
                is_package=path.name == "__init__.py",
            )
            if imported != "gsplot._compat.shim":
                errors.append(
                    f"{path}: historical shim imports {imported}; only "
                    "gsplot._compat.shim is allowed"
                )
    return errors


def _check_shims(source_root: Path) -> list[str]:
    """Check all historical package files, including undocumented paths."""

    errors: list[str] = []
    for package in LEGACY_PACKAGES:
        directory = source_root / package
        if not directory.is_dir():
            errors.append(f"missing historical shim package: {directory}")
            continue
        for path in sorted(directory.rglob("*.py")):
            errors.extend(_check_shim(path, source_root))
    return errors


def _literal_names(value: ast.AST) -> set[str] | None:
    """Extract string names from a literal list or tuple."""

    if not isinstance(value, (ast.List, ast.Tuple, ast.Set)):
        return None
    names: set[str] = set()
    for item in value.elts:
        if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
            return None
        names.add(item.value)
    return names


def _check_root_manifest(source_root: Path) -> list[str]:
    """Ensure root ``__all__`` is the canonical manifest, not a second API."""

    path = source_root / "__init__.py"
    tree = _read_tree(path)
    public: set[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    public = _literal_names(node.value)
    if public is None:
        return [f"{path}: __all__ must be a literal canonical export list"]

    compatibility = _read_tree(source_root / "_compat" / "root.py")
    manifest: set[str] = set()
    for node in compatibility.body:
        value: ast.AST | None = None
        targets: tuple[ast.expr, ...] = ()
        if isinstance(node, ast.Assign):
            value = node.value
            targets = tuple(node.targets)
        elif isinstance(node, ast.AnnAssign):
            value = node.value
            targets = (node.target,)
        if any(
            isinstance(target, ast.Name) and target.id == "_CANONICAL_EXPORTS"
            for target in targets
        ) and isinstance(value, ast.Dict):
            for key in value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    manifest.add(key.value)
    if public != manifest:
        return [
            f"{path}: __all__ differs from _CANONICAL_EXPORTS; "
            f"missing={sorted(manifest - public)}, extra={sorted(public - manifest)}"
        ]
    return []


def check(repository_root: Path) -> list[str]:
    """Return all static architecture violations for ``repository_root``."""

    source_root = repository_root / "src" / "gsplot"
    if not source_root.is_dir():
        return [f"missing source package: {source_root}"]
    errors: list[str] = []
    errors.extend(_check_private_initializers(source_root))
    errors.extend(_check_import_edges(source_root))
    errors.extend(_check_shims(source_root))
    errors.extend(_check_root_manifest(source_root))
    return errors


def main() -> int:
    """Run the checker and print actionable violations."""

    repository_root = Path(__file__).resolve().parents[2]
    errors = check(repository_root)
    if errors:
        print("Architecture boundary check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Architecture boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
