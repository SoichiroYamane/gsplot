"""Explicit privacy-bounded metadata serialization."""

from __future__ import annotations

import json
import os
import tempfile
from os import PathLike
from pathlib import Path

from .._core.errors import MetadataError
from .._core.types import MetadataSnapshot
from .paths import resolve_path

MAX_METADATA_BYTES = 1_048_576


def _payload(snapshot: MetadataSnapshot) -> bytes:
    """Serialize the stable public metadata schema."""

    value: dict[str, object] = {
        "schema_version": snapshot.schema_version,
        "package_version": snapshot.package_version,
        "commit": snapshot.commit,
        "config_digest": snapshot.config_digest,
        "labels": dict(snapshot.labels),
    }
    try:
        encoded = (
            json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MetadataError("metadata snapshot is not JSON serializable") from exc
    if len(encoded) > MAX_METADATA_BYTES:
        raise MetadataError(f"metadata exceeds the {MAX_METADATA_BYTES}-byte limit")
    return encoded


def _parent(destination: Path, create_parent: bool) -> None:
    """Validate or explicitly create the destination parent."""

    parent = destination.parent
    if parent.exists() and not parent.is_dir():
        raise MetadataError(f"metadata parent is not a directory: {parent}")
    if not parent.exists():
        if not create_parent:
            raise MetadataError(f"metadata parent does not exist: {parent}")
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise MetadataError(f"could not create metadata parent: {parent}") from exc


def _exclusive(destination: Path, encoded: bytes) -> None:
    """Install a new file with no-replace semantics."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(destination, flags, 0o644)
    except OSError as exc:
        raise MetadataError(f"could not create metadata file: {destination}") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            destination.unlink()
        except OSError:
            pass
        raise MetadataError(f"could not write metadata file: {destination}") from exc


def _replace(destination: Path, encoded: bytes) -> None:
    """Atomically replace a destination through a same-directory temporary."""

    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            dir=destination.parent, prefix=f".{destination.name}.", suffix=".tmp"
        )
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, destination)
        temporary = None
    except OSError as exc:
        raise MetadataError(
            f"could not atomically replace metadata file: {destination}"
        ) from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass


def write_meta(
    snapshot: MetadataSnapshot,
    destination: str | PathLike[str],
    *,
    overwrite: bool = False,
    create_parent: bool = False,
) -> Path:
    """Write one stable UTF-8 metadata document to an explicit destination."""

    if not isinstance(snapshot, MetadataSnapshot):
        raise MetadataError("snapshot must be a gsplot MetadataSnapshot")
    if not isinstance(overwrite, bool) or not isinstance(create_parent, bool):
        raise MetadataError("overwrite and create_parent must be booleans")
    encoded = _payload(snapshot)
    path = resolve_path(destination, "destination")
    _parent(path, create_parent)
    if overwrite:
        _replace(path, encoded)
    else:
        if path.exists():
            raise MetadataError(f"metadata file already exists: {path}")
        _exclusive(path, encoded)
    return path


__all__ = ["write_meta", "MAX_METADATA_BYTES"]
