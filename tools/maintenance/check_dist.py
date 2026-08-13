"""Validate gsplot wheel and source-distribution contents without installing them.

The checker uses only the Python standard library so release and pull-request
workflows can inspect artifacts before they are uploaded or installed. It
prints no archive contents on success and never extracts untrusted members.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import re
import sys
import tarfile
import zipfile
from collections.abc import Mapping, Sequence
from email.message import Message
from email.parser import BytesParser
from email.policy import default
from pathlib import Path, PurePosixPath

_WHEEL_PATTERN = re.compile(
    r"^gsplot-(?P<version>[A-Za-z0-9][A-Za-z0-9_.+!]*)-py3-none-any\.whl$"
)
_SDIST_PATTERN = re.compile(
    r"^gsplot-(?P<version>[A-Za-z0-9][A-Za-z0-9_.+!]*)\.tar\.gz$"
)
_EXPECTED_SUMMARY = (
    "Concise publication-quality scientific plotting built on Matplotlib"
)
_EXPECTED_REQUIREMENTS = {"matplotlib (>=3.9.0)", "numpy (>=1.26.4)"}
_EXPECTED_URLS = {
    "Documentation": "https://soichiroyamane.github.io/gsplot/stable/",
    "Homepage": "https://soichiroyamane.github.io/gsplot/",
    "Issues": "https://github.com/SoichiroYamane/gsplot/issues",
    "Repository": "https://github.com/SoichiroYamane/gsplot",
}
_EXPECTED_KEYWORDS = {"matplotlib", "plotting", "publication", "scientific"}
_MAX_ARTIFACT_BYTES = 20 * 1024 * 1024
_MAX_MEMBER_BYTES = 5 * 1024 * 1024
_MAX_MEMBERS = 1000


def _member_error(name: str) -> str | None:
    """Return an error for an unsafe archive member name."""

    if not name or "\\" in name or "\x00" in name:
        return "archive contains an empty or non-POSIX member name"
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in name.split("/")):
        return f"unsafe archive member: {name}"
    return None


def _validate_member_names(names: Sequence[str]) -> list[str]:
    """Return duplicate and traversal errors for archive member names."""

    errors: list[str] = []
    seen: set[str] = set()
    for name in names:
        error = _member_error(name)
        if error is not None:
            errors.append(error)
        if name in seen:
            errors.append(f"duplicate archive member: {name}")
        seen.add(name)
    return errors


def _parse_metadata(data: bytes, *, label: str) -> tuple[Message | None, list[str]]:
    """Parse one core-metadata document."""

    try:
        return BytesParser(policy=default).parsebytes(data), []
    except (TypeError, ValueError) as exc:
        return None, [f"{label} metadata cannot be parsed: {type(exc).__name__}"]


def _project_urls(message: Message) -> tuple[dict[str, str], list[str]]:
    """Return normalized project URLs and malformed-field errors."""

    result: dict[str, str] = {}
    errors: list[str] = []
    for raw in message.get_all("Project-URL", []):
        if "," not in raw:
            errors.append("Project-URL metadata must contain a label and URL")
            continue
        label, url = (part.strip() for part in raw.split(",", 1))
        if not label or not url or label in result:
            errors.append("Project-URL metadata contains an empty or duplicate label")
            continue
        result[label] = url
    return result, errors


def _metadata_projection(message: Message) -> dict[str, object]:
    """Return fields that must agree between wheel and sdist metadata."""

    urls, _ = _project_urls(message)
    return {
        "Metadata-Version": message.get("Metadata-Version"),
        "Name": message.get("Name"),
        "Version": message.get("Version"),
        "Summary": message.get("Summary"),
        "License-Expression": message.get("License-Expression"),
        "License-File": tuple(message.get_all("License-File", [])),
        "Keywords": message.get("Keywords"),
        "Author": message.get("Author"),
        "Author-email": message.get("Author-email"),
        "Requires-Python": message.get("Requires-Python"),
        "Requires-Dist": tuple(sorted(message.get_all("Requires-Dist", []))),
        "Project-URL": tuple(sorted(urls.items())),
        "Description-Content-Type": message.get("Description-Content-Type"),
    }


def _check_metadata(message: Message, *, version: str, label: str) -> list[str]:
    """Validate public package metadata shared by both artifacts."""

    errors: list[str] = []
    expected_scalars = {
        "Metadata-Version": "2.4",
        "Name": "gsplot",
        "Version": version,
        "Summary": _EXPECTED_SUMMARY,
        "License-Expression": "MIT",
        "Author": "Giordano Mattoni",
        "Requires-Python": ">=3.10",
        "Description-Content-Type": "text/markdown",
    }
    for field, expected in expected_scalars.items():
        actual = message.get(field)
        if actual != expected:
            errors.append(f"{label} metadata field {field} must be {expected!r}")
    if message.get("Author-email") is not None:
        errors.append(f"{label} metadata must not publish an author email")
    if message.get_all("License-File", []) != ["LICENSE"]:
        errors.append(f"{label} metadata must declare only LICENSE")
    requirements = set(message.get_all("Requires-Dist", []))
    if requirements != _EXPECTED_REQUIREMENTS:
        errors.append(f"{label} metadata has unexpected runtime requirements")
    keywords = {
        value.strip() for value in (message.get("Keywords") or "").split(",") if value
    }
    if keywords != _EXPECTED_KEYWORDS:
        errors.append(f"{label} metadata has unexpected keywords")
    urls, url_errors = _project_urls(message)
    errors.extend(f"{label} {error}" for error in url_errors)
    if urls != _EXPECTED_URLS:
        errors.append(f"{label} metadata has unexpected project URLs")
    return errors


def _source_members(source_root: Path) -> tuple[dict[str, bytes], list[str]]:
    """Return the exact package-source files expected in an artifact."""

    errors: list[str] = []
    result: dict[str, bytes] = {}
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        relative = path.relative_to(source_root).as_posix()
        if path.is_symlink():
            errors.append(f"package source must not be a symlink: gsplot/{relative}")
            continue
        if path.suffix != ".py" and relative != "py.typed":
            errors.append(f"unsupported package source file: gsplot/{relative}")
            continue
        result[f"gsplot/{relative}"] = path.read_bytes()
    if "gsplot/__init__.py" not in result:
        errors.append("package source is missing gsplot/__init__.py")
    if "gsplot/py.typed" not in result:
        errors.append("package source is missing gsplot/py.typed")
    return result, errors


def _check_record(files: Mapping[str, bytes], record_name: str) -> list[str]:
    """Validate wheel RECORD paths, hashes, and sizes."""

    errors: list[str] = []
    try:
        rows = list(csv.reader(io.StringIO(files[record_name].decode("utf-8"))))
    except (KeyError, UnicodeDecodeError, csv.Error):
        return ["wheel RECORD is missing or malformed"]
    records: dict[str, tuple[str, str]] = {}
    for row in rows:
        if len(row) != 3 or row[0] in records:
            errors.append("wheel RECORD contains a malformed or duplicate row")
            continue
        records[row[0]] = (row[1], row[2])
    if set(records) != set(files):
        errors.append("wheel RECORD paths do not match archive members")
    for name, data in files.items():
        digest, size = records.get(name, ("", ""))
        if name == record_name:
            if digest or size:
                errors.append("wheel RECORD must leave its own hash and size empty")
            continue
        expected_digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest())
        expected_digest = expected_digest.rstrip(b"=").decode("ascii")
        if digest != f"sha256={expected_digest}" or size != str(len(data)):
            errors.append(f"wheel RECORD integrity mismatch: {name}")
    return errors


def _check_wheel(
    path: Path, source_files: Mapping[str, bytes], license_data: bytes
) -> tuple[str | None, Message | None, list[str]]:
    """Validate a pure-Python wheel without extracting it."""

    match = _WHEEL_PATTERN.fullmatch(path.name)
    if match is None:
        return None, None, ["wheel filename must be gsplot-VERSION-py3-none-any.whl"]
    version = match.group("version")
    errors: list[str] = []
    if path.stat().st_size > _MAX_ARTIFACT_BYTES:
        return version, None, ["wheel exceeds the artifact size limit"]
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            errors.extend(_validate_member_names(names))
            if len(infos) > _MAX_MEMBERS:
                return version, None, errors + ["wheel has too many members"]
            if any(item.flag_bits & 1 for item in infos):
                return version, None, errors + ["wheel contains an encrypted member"]
            if any(item.file_size > _MAX_MEMBER_BYTES for item in infos):
                return version, None, errors + ["wheel member exceeds the size limit"]
            if sum(item.file_size for item in infos) > _MAX_ARTIFACT_BYTES:
                return version, None, errors + ["wheel contents exceed the size limit"]
            if any(item.is_dir() for item in infos):
                errors.append("wheel must not contain explicit directory entries")
            files = {
                item.filename: archive.read(item) for item in infos if not item.is_dir()
            }
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return version, None, ["wheel is not a readable ZIP archive"]

    dist_info = f"gsplot-{version}.dist-info"
    metadata_name = f"{dist_info}/METADATA"
    wheel_name = f"{dist_info}/WHEEL"
    record_name = f"{dist_info}/RECORD"
    license_name = f"{dist_info}/licenses/LICENSE"
    expected_names = set(source_files) | {
        metadata_name,
        wheel_name,
        record_name,
        license_name,
    }
    if set(files) != expected_names:
        errors.append("wheel contents differ from the exact package manifest")
    for name, expected in source_files.items():
        if files.get(name) != expected:
            errors.append(f"wheel package file differs from source: {name}")
    if files.get(license_name) != license_data:
        errors.append("wheel license file differs from LICENSE")

    message, metadata_errors = _parse_metadata(
        files.get(metadata_name, b""), label="wheel"
    )
    errors.extend(metadata_errors)
    if message is not None:
        errors.extend(_check_metadata(message, version=version, label="wheel"))
    wheel_message, wheel_errors = _parse_metadata(
        files.get(wheel_name, b""), label="WHEEL"
    )
    errors.extend(wheel_errors)
    if wheel_message is not None:
        if wheel_message.get("Wheel-Version") != "1.0":
            errors.append("wheel must use Wheel-Version 1.0")
        if wheel_message.get("Root-Is-Purelib") != "true":
            errors.append("wheel must be a purelib distribution")
        if wheel_message.get_all("Tag", []) != ["py3-none-any"]:
            errors.append("wheel must use only the py3-none-any tag")
    errors.extend(_check_record(files, record_name))
    return version, message, errors


def _check_sdist(
    path: Path, source_files: Mapping[str, bytes], source_root: Path
) -> tuple[str | None, Message | None, list[str]]:
    """Validate a source distribution without extracting it."""

    match = _SDIST_PATTERN.fullmatch(path.name)
    if match is None:
        return None, None, ["sdist filename must be gsplot-VERSION.tar.gz"]
    version = match.group("version")
    root = f"gsplot-{version}"
    errors: list[str] = []
    files: dict[str, bytes] = {}
    directories: set[str] = set()
    if path.stat().st_size > _MAX_ARTIFACT_BYTES:
        return version, None, ["sdist exceeds the artifact size limit"]
    try:
        with tarfile.open(path, mode="r:gz") as archive:
            members = archive.getmembers()
            errors.extend(_validate_member_names([member.name for member in members]))
            if len(members) > _MAX_MEMBERS:
                return version, None, errors + ["sdist has too many members"]
            if any(member.size > _MAX_MEMBER_BYTES for member in members):
                return version, None, errors + ["sdist member exceeds the size limit"]
            if sum(member.size for member in members) > _MAX_ARTIFACT_BYTES:
                return version, None, errors + ["sdist contents exceed the size limit"]
            for member in members:
                if member.isdir():
                    directories.add(member.name)
                    continue
                if not member.isfile():
                    errors.append(f"sdist contains a non-regular member: {member.name}")
                    continue
                extracted = archive.extractfile(member)
                if extracted is None:
                    errors.append(f"sdist member cannot be read: {member.name}")
                    continue
                files[member.name] = extracted.read()
    except (OSError, tarfile.TarError):
        return version, None, ["sdist is not a readable gzip tar archive"]

    metadata_name = f"{root}/PKG-INFO"
    package_names = {f"{root}/src/{name}": data for name, data in source_files.items()}
    expected_files = set(package_names) | {
        f"{root}/LICENSE",
        f"{root}/README.md",
        f"{root}/pyproject.toml",
        metadata_name,
    }
    expected_directories = {
        str(parent)
        for name in expected_files
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    if not directories <= expected_directories:
        errors.append("sdist contains an unexpected directory entry")
    if set(files) != expected_files:
        errors.append("sdist contents differ from the exact source manifest")
    for name, expected in package_names.items():
        if files.get(name) != expected:
            errors.append(f"sdist package file differs from source: {name}")
    repository_root = source_root.parents[1]
    for relative in ("LICENSE", "README.md", "pyproject.toml"):
        expected = (repository_root / relative).read_bytes()
        if files.get(f"{root}/{relative}") != expected:
            errors.append(f"sdist project file differs from source: {relative}")

    message, metadata_errors = _parse_metadata(
        files.get(metadata_name, b""), label="sdist"
    )
    errors.extend(metadata_errors)
    if message is not None:
        errors.extend(_check_metadata(message, version=version, label="sdist"))
    return version, message, errors


def check(dist_dir: Path, source_root: Path) -> list[str]:
    """Return validation errors for one wheel/sdist pair."""

    if not dist_dir.is_dir():
        return ["distribution directory does not exist"]
    if not source_root.is_dir():
        return ["package source directory does not exist"]
    entries = sorted(dist_dir.iterdir())
    artifacts = [path for path in entries if path.is_file()]
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
    errors: list[str] = []
    if (
        len(entries) != 2
        or len(artifacts) != 2
        or any(path.is_symlink() for path in artifacts)
        or len(wheels) != 1
        or len(sdists) != 1
    ):
        return ["distribution directory must contain exactly one wheel and one sdist"]

    source_files, source_errors = _source_members(source_root)
    errors.extend(source_errors)
    license_data = (source_root.parents[1] / "LICENSE").read_bytes()
    wheel_version, wheel_metadata, wheel_errors = _check_wheel(
        wheels[0], source_files, license_data
    )
    sdist_version, sdist_metadata, sdist_errors = _check_sdist(
        sdists[0], source_files, source_root
    )
    errors.extend(wheel_errors)
    errors.extend(sdist_errors)
    if wheel_version != sdist_version:
        errors.append("wheel and sdist versions differ")
    if wheel_metadata is not None and sdist_metadata is not None:
        if _metadata_projection(wheel_metadata) != _metadata_projection(sdist_metadata):
            errors.append("wheel and sdist core metadata differ")
    return errors


def main() -> int:
    """Validate command-line artifact paths."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dist_dir", nargs="?", type=Path, default=Path("dist"))
    parser.add_argument("--source-root", type=Path, default=Path("src") / "gsplot")
    args = parser.parse_args()
    errors = check(args.dist_dir, args.source_root)
    if errors:
        print("Distribution artifact validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Distribution artifact validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
