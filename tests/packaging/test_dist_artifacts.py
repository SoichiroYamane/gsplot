"""Tests for the fail-closed wheel and sdist validator."""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import tarfile
import zipfile
from pathlib import Path

from tools.maintenance import check_dist

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src" / "gsplot"
VERSION = "0.4.0"
METADATA = b"""Metadata-Version: 2.4
Name: gsplot
Version: 0.4.0
Summary: Concise publication-quality scientific plotting built on Matplotlib
License-Expression: MIT
License-File: LICENSE
Keywords: matplotlib,plotting,publication,scientific
Author: Giordano Mattoni
Requires-Python: >=3.10
Requires-Dist: matplotlib (>=3.9.0)
Requires-Dist: numpy (>=1.26.4)
Project-URL: Documentation, https://soichiroyamane.github.io/gsplot/stable/
Project-URL: Homepage, https://soichiroyamane.github.io/gsplot/
Project-URL: Issues, https://github.com/SoichiroYamane/gsplot/issues
Project-URL: Repository, https://github.com/SoichiroYamane/gsplot
Description-Content-Type: text/markdown

# gsplot
"""
WHEEL = b"""Wheel-Version: 1.0
Generator: gsplot-test
Root-Is-Purelib: true
Tag: py3-none-any

"""


def _record(files: dict[str, bytes], record_name: str) -> bytes:
    """Return a complete wheel RECORD for ``files``."""

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for name, data in sorted(files.items()):
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest())
        writer.writerow([name, f"sha256={digest.rstrip(b'=').decode()}", len(data)])
    writer.writerow([record_name, "", ""])
    return output.getvalue().encode()


def _add_tar_file(archive: tarfile.TarFile, name: str, data: bytes) -> None:
    """Add one deterministic regular file to a test sdist."""

    info = tarfile.TarInfo(name)
    info.size = len(data)
    info.mode = 0o644
    info.mtime = 0
    archive.addfile(info, io.BytesIO(data))


def _build_pair(dist_dir: Path, *, sdist_symlink: bool = False) -> tuple[Path, Path]:
    """Build one minimal valid artifact pair from the checked-out package."""

    dist_dir.mkdir()
    source_files, errors = check_dist._source_members(SOURCE_ROOT)
    assert errors == []
    dist_info = f"gsplot-{VERSION}.dist-info"
    record_name = f"{dist_info}/RECORD"
    wheel_files = dict(source_files)
    wheel_files[f"{dist_info}/METADATA"] = METADATA
    wheel_files[f"{dist_info}/WHEEL"] = WHEEL
    wheel_files[f"{dist_info}/licenses/LICENSE"] = (
        PROJECT_ROOT / "LICENSE"
    ).read_bytes()
    wheel_files[record_name] = _record(wheel_files, record_name)
    wheel_path = dist_dir / f"gsplot-{VERSION}-py3-none-any.whl"
    with zipfile.ZipFile(wheel_path, mode="w") as archive:
        for name, data in sorted(wheel_files.items()):
            archive.writestr(name, data)

    root = f"gsplot-{VERSION}"
    sdist_files = {
        f"{root}/LICENSE": (PROJECT_ROOT / "LICENSE").read_bytes(),
        f"{root}/PKG-INFO": METADATA,
        f"{root}/README.md": (PROJECT_ROOT / "README.md").read_bytes(),
        f"{root}/pyproject.toml": (PROJECT_ROOT / "pyproject.toml").read_bytes(),
    }
    sdist_files.update(
        {f"{root}/src/{name}": data for name, data in source_files.items()}
    )
    sdist_path = dist_dir / f"gsplot-{VERSION}.tar.gz"
    with tarfile.open(sdist_path, mode="w:gz") as archive:
        for name, data in sorted(sdist_files.items()):
            _add_tar_file(archive, name, data)
        if sdist_symlink:
            info = tarfile.TarInfo(f"{root}/escape")
            info.type = tarfile.SYMTYPE
            info.linkname = "../../outside"
            archive.addfile(info)
    return wheel_path, sdist_path


def test_valid_exact_artifact_pair_passes(tmp_path: Path) -> None:
    """Matching pure-Python artifacts preserve the complete source manifest."""

    dist_dir = tmp_path / "dist"
    _build_pair(dist_dir)

    assert check_dist.check(dist_dir, SOURCE_ROOT) == []


def test_unexpected_wheel_content_fails_closed(tmp_path: Path) -> None:
    """A file outside the package and dist-info manifests is rejected."""

    dist_dir = tmp_path / "dist"
    wheel, _ = _build_pair(dist_dir)
    with zipfile.ZipFile(wheel, mode="a") as archive:
        archive.writestr("docs/private.txt", b"unexpected")

    errors = check_dist.check(dist_dir, SOURCE_ROOT)

    assert "wheel contents differ from the exact package manifest" in errors


def test_non_regular_sdist_member_is_rejected(tmp_path: Path) -> None:
    """An sdist symlink cannot escape the exact regular-file manifest."""

    dist_dir = tmp_path / "dist"
    _build_pair(dist_dir, sdist_symlink=True)

    errors = check_dist.check(dist_dir, SOURCE_ROOT)

    assert any("non-regular member" in error for error in errors)


def test_archive_member_validation_rejects_traversal_and_duplicates() -> None:
    """Archive paths are checked without extraction."""

    errors = check_dist._validate_member_names(
        ["gsplot/file.py", "../outside", "gsplot//empty.py", "gsplot/file.py"]
    )

    assert "unsafe archive member: ../outside" in errors
    assert "unsafe archive member: gsplot//empty.py" in errors
    assert "duplicate archive member: gsplot/file.py" in errors


def test_stale_distribution_artifact_is_rejected(tmp_path: Path) -> None:
    """An upload directory cannot mix current and stale versions."""

    dist_dir = tmp_path / "dist"
    _build_pair(dist_dir)
    (dist_dir / "gsplot-0.3.0-py3-none-any.whl").write_bytes(b"stale")

    assert check_dist.check(dist_dir, SOURCE_ROOT) == [
        "distribution directory must contain exactly one wheel and one sdist"
    ]


def test_distribution_subdirectory_is_rejected(tmp_path: Path) -> None:
    """Only the exact upload files may exist in the distribution directory."""

    dist_dir = tmp_path / "dist"
    _build_pair(dist_dir)
    (dist_dir / "unexpected").mkdir()

    assert check_dist.check(dist_dir, SOURCE_ROOT) == [
        "distribution directory must contain exactly one wheel and one sdist"
    ]
