"""Validate and execute the repository's documentation examples."""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


class ExampleError(RuntimeError):
    """Raised when the executable-example contract is invalid."""


@dataclass(frozen=True)
class Example:
    """One validated executable example and its documentation contract."""

    identifier: str
    script: PurePosixPath
    page: PurePosixPath
    outputs: tuple[PurePosixPath, ...]


@dataclass(frozen=True)
class FileState:
    """Content and freshness state for one file-system entry."""

    kind: str
    size: int
    modified_ns: int
    digest: str


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_ENTRY_FIELDS = {"id", "script", "page", "outputs"}
_MANIFEST_FIELDS = {"schema_version", "examples"}
_OUTPUT_SUFFIXES = {".pdf", ".png"}


def _mapping(value: object, description: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExampleError(f"{description} must be an object")
    return value


def _safe_path(value: object, field: str, prefix: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ExampleError(f"{field} must be a normalized non-empty POSIX path")
    selected = PurePosixPath(value)
    if (
        selected.is_absolute()
        or selected.as_posix() != value
        or not selected.parts
        or selected.parts[0] != prefix
        or any(part in {"", ".", ".."} for part in selected.parts)
    ):
        raise ExampleError(f"{field} must stay under {prefix}/")
    return selected


def _resolved_inside(project_root: Path, selected: PurePosixPath, prefix: str) -> Path:
    boundary = (project_root / prefix).resolve()
    candidate = (project_root / selected).resolve(strict=False)
    if not candidate.is_relative_to(boundary):
        raise ExampleError(f"{selected.as_posix()} resolves outside {prefix}/")
    return candidate


def _read_manifest(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExampleError("could not read the examples manifest") from exc
    manifest = _mapping(value, "examples manifest")
    if set(manifest) != _MANIFEST_FIELDS:
        raise ExampleError("examples manifest has invalid top-level fields")
    if manifest["schema_version"] != 1 or not isinstance(manifest["examples"], list):
        raise ExampleError("examples manifest must use schema_version 1")
    return manifest


def load_manifest(
    project_root: Path, manifest_path: Path | None = None
) -> tuple[Example, ...]:
    """Load and fully validate the executable-example manifest."""

    root = project_root.resolve()
    examples_root = root / "examples"
    path = manifest_path or examples_root / "manifest.json"
    manifest = _read_manifest(path)
    examples: list[Example] = []
    identifiers: set[str] = set()
    scripts: set[PurePosixPath] = set()
    pages: set[PurePosixPath] = set()
    outputs: set[PurePosixPath] = set()

    for position, raw_entry in enumerate(manifest["examples"]):
        entry = _mapping(raw_entry, f"manifest entry {position}")
        if set(entry) != _ENTRY_FIELDS:
            raise ExampleError(f"manifest entry {position} has invalid fields")
        identifier = entry["id"]
        if not isinstance(identifier, str) or _IDENTIFIER.fullmatch(identifier) is None:
            raise ExampleError(f"manifest entry {position} has an invalid id")
        script = _safe_path(entry["script"], f"entry {position} script", "examples")
        page = _safe_path(entry["page"], f"entry {position} page", "docs")
        raw_outputs = entry["outputs"]
        if script.suffix != ".py" or not isinstance(raw_outputs, list):
            raise ExampleError(f"manifest entry {position} is not a Python example")
        selected_outputs = tuple(
            _safe_path(value, f"entry {position} output", "examples")
            for value in raw_outputs
        )
        if any(
            output.parent != script.parent or output.suffix not in _OUTPUT_SUFFIXES
            for output in selected_outputs
        ):
            raise ExampleError(
                f"manifest outputs for {script.as_posix()} must be PNG/PDF siblings"
            )
        if identifier in identifiers:
            raise ExampleError(f"manifest repeats id {identifier}")
        if script in scripts:
            raise ExampleError(f"manifest repeats script {script.as_posix()}")
        if page in pages:
            raise ExampleError(f"manifest repeats page {page.as_posix()}")
        duplicate_outputs = outputs.intersection(selected_outputs)
        if len(set(selected_outputs)) != len(selected_outputs) or duplicate_outputs:
            repeated = sorted(
                output.as_posix()
                for output in duplicate_outputs
                | {
                    output
                    for output in selected_outputs
                    if selected_outputs.count(output) > 1
                }
            )
            raise ExampleError("manifest repeats output(s): " + ", ".join(repeated))

        script_path = _resolved_inside(root, script, "examples")
        page_path = _resolved_inside(root, page, "docs")
        if not page.is_relative_to(PurePosixPath("docs/guides/examples")):
            raise ExampleError("manifest pages must stay under docs/guides/examples/")
        if not script_path.is_file():
            raise ExampleError(f"manifest script is missing: {script.as_posix()}")
        if not page_path.is_file():
            raise ExampleError(f"manifest page is missing: {page.as_posix()}")
        for output in selected_outputs:
            _resolved_inside(root, output, "examples")

        identifiers.add(identifier)
        scripts.add(script)
        pages.add(page)
        outputs.update(selected_outputs)
        examples.append(Example(identifier, script, page, selected_outputs))

    actual_scripts = {
        PurePosixPath(source.relative_to(root).as_posix())
        for source in examples_root.rglob("*.py")
        if source.is_file()
    }
    if scripts != actual_scripts:
        undeclared = sorted(path.as_posix() for path in actual_scripts - scripts)
        missing = sorted(path.as_posix() for path in scripts - actual_scripts)
        raise ExampleError(
            "examples manifest does not match executable scripts; "
            f"undeclared={undeclared}, missing={missing}"
        )

    generated_files = {
        PurePosixPath(source.relative_to(root).as_posix())
        for source in examples_root.rglob("*")
        if source.is_file() and source.suffix in _OUTPUT_SUFFIXES
    }
    undeclared_outputs = sorted(
        path.as_posix() for path in generated_files.difference(outputs)
    )
    if undeclared_outputs:
        raise ExampleError(
            "examples tree contains undeclared generated output(s): "
            + ", ".join(undeclared_outputs)
        )
    validate_documentation(root, examples)
    return tuple(examples)


def _relative_reference(page: PurePosixPath, target: PurePosixPath) -> str:
    return posixpath.relpath(target.as_posix(), start=page.parent.as_posix())


def validate_documentation(project_root: Path, examples: Sequence[Example]) -> None:
    """Require each manifest entry to use one source and all declared outputs."""

    for example in examples:
        text = (project_root / example.page).read_text(encoding="utf-8")
        script_reference = _relative_reference(example.page, example.script)
        directive = f"```{{literalinclude}} {script_reference}"
        if directive not in text:
            raise ExampleError(
                f"{example.page.as_posix()} must literal-include "
                f"{example.script.as_posix()}"
            )
        for output in example.outputs:
            reference = _relative_reference(example.page, output)
            if reference not in text:
                raise ExampleError(
                    f"{example.page.as_posix()} must reference {output.as_posix()}"
                )


def snapshot_tree(project_root: Path) -> dict[str, FileState]:
    """Return a content-aware snapshot of every non-directory examples entry."""

    root = project_root.resolve()
    examples_root = root / "examples"
    state: dict[str, FileState] = {}
    for selected in sorted(examples_root.rglob("*")):
        relative = selected.relative_to(root).as_posix()
        if selected.is_symlink():
            resolved = selected.resolve(strict=False)
            if not resolved.is_relative_to(examples_root.resolve()):
                raise ExampleError(f"{relative} is a symlink outside examples/")
            target = os.readlink(selected)
            info = selected.lstat()
            state[relative] = FileState(
                "symlink",
                info.st_size,
                info.st_mtime_ns,
                hashlib.sha256(target.encode()).hexdigest(),
            )
        elif selected.is_file():
            info = selected.stat()
            state[relative] = FileState(
                "file",
                info.st_size,
                info.st_mtime_ns,
                hashlib.sha256(selected.read_bytes()).hexdigest(),
            )
    return state


def validate_output_state(
    before: Mapping[str, FileState],
    after: Mapping[str, FileState],
    allowed: set[str],
    example_id: str,
) -> None:
    """Reject missing, stale, deleted, or cross-example file mutations."""

    changed = {path for path, state in after.items() if before.get(path) != state}
    changed.update(set(before).difference(after))
    unexpected = sorted(changed.difference(allowed))
    if unexpected:
        raise ExampleError(
            f"{example_id} changed files outside its output allowlist: "
            + ", ".join(unexpected)
        )
    missing = sorted(path for path in allowed if path not in after)
    if missing:
        raise ExampleError(
            f"{example_id} did not produce required output(s): " + ", ".join(missing)
        )
    stale = sorted(
        path for path in allowed if path in before and before[path] == after[path]
    )
    if stale:
        raise ExampleError(
            f"{example_id} left required output(s) unchanged: " + ", ".join(stale)
        )


def _isolated_environment(sandbox: Path) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name, value in os.environ.items():
        upper = name.upper()
        if (
            upper == "PYTHONPATH"
            or "TOKEN" in upper
            or "SECRET" in upper
            or "PASSWORD" in upper
            or "CREDENTIAL" in upper
            or "AUTH" in upper
            or "INDEX_URL" in upper
            or upper.startswith(("AWS_", "AZURE_", "GH_", "GITHUB_", "SSH_"))
            or upper in {"ALL_PROXY", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY"}
        ):
            continue
        environment[name] = value
    directories = {
        "HOME": sandbox / "home",
        "XDG_CACHE_HOME": sandbox / "xdg-cache",
        "XDG_CONFIG_HOME": sandbox / "xdg-config",
        "XDG_DATA_HOME": sandbox / "xdg-data",
        "MPLCONFIGDIR": sandbox / "matplotlib",
    }
    for directory in directories.values():
        directory.mkdir(parents=True)
    environment.update({name: str(path) for name, path in directories.items()})
    environment["MPLBACKEND"] = "Agg"
    return environment


def run_examples(
    project_root: Path,
    *,
    skip_execution: bool = False,
    announce: Callable[[str], None] = print,
) -> tuple[Example, ...]:
    """Validate and optionally run every manifest-covered example in isolation."""

    root = project_root.resolve()
    examples = load_manifest(root)
    if skip_execution:
        return examples
    for example in examples:
        before = snapshot_tree(root)
        announce(f"Running example: {example.script.as_posix()}")
        with tempfile.TemporaryDirectory(prefix="gsplot-example-") as temporary:
            result = subprocess.run(
                [sys.executable, "-I", "-B", example.script.name],
                cwd=root / example.script.parent,
                env=_isolated_environment(Path(temporary)),
                check=False,
            )
        if result.returncode != 0:
            raise ExampleError(
                f"{example.identifier} exited with status {result.returncode}"
            )
        after = snapshot_tree(root)
        validate_output_state(
            before,
            after,
            {output.as_posix() for output in example.outputs},
            example.identifier,
        )
    return examples
