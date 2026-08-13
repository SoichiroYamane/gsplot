"""Compare two committed gsplot revisions with a public-safe benchmark.

The benchmark never switches or writes the working tree. It exports each
revision into temporary storage, gives each source tree an isolated Python
environment backed by the same installed dependencies, and prints aggregate
JSON only. Raw timings, local paths, hostnames, and subprocess logs are never
included in the result.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import sysconfig
import tarfile
import tempfile
import time
import venv
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Final, Sequence

BASELINE_REF: Final = "782117f"
IMPORT_ITERATIONS: Final = 20
PLOT_ITERATIONS: Final = 10
DOCS_BUILDS: Final = 3
RELATIVE_THRESHOLD: Final = 0.15
ABSOLUTE_THRESHOLDS_MS: Final[dict[str, float]] = {
    "fresh_import": 10.0,
    "ordinary_line": 5.0,
    "ordinary_scatter": 5.0,
    "colored_line": 5.0,
    "docs_build": 1000.0,
}
PLOT_OPERATIONS: Final = (
    "ordinary_line",
    "ordinary_scatter",
    "colored_line",
)
_COMMIT_PATTERN: Final = re.compile(r"^[0-9a-f]{40}$")
_MAX_ARCHIVE_BYTES: Final = 200 * 1024 * 1024
_MAX_ARCHIVE_MEMBER_BYTES: Final = 25 * 1024 * 1024
_MAX_ARCHIVE_MEMBERS: Final = 20_000
_SHARED_SITE_PACKAGES: Final = Path(sysconfig.get_path("purelib"))


class BenchmarkError(RuntimeError):
    """Report a benchmark failure without machine-specific details."""


@dataclass(frozen=True)
class RevisionEnvironment:
    """One exported revision and the interpreter that imports it."""

    label: str
    ref: str
    commit: str
    source: Path
    python: Path


def compare_metric(
    baseline_ms: float,
    candidate_ms: float,
    absolute_threshold_ms: float,
) -> dict[str, float | bool]:
    """Return one relative-and-absolute material-regression decision."""

    if baseline_ms <= 0 or candidate_ms < 0 or absolute_threshold_ms < 0:
        raise ValueError("benchmark timings and thresholds must be finite and valid")
    values = (baseline_ms, candidate_ms, absolute_threshold_ms)
    if not all(value < float("inf") for value in values):
        raise ValueError("benchmark timings and thresholds must be finite and valid")

    delta_ms = candidate_ms - baseline_ms
    relative_delta = delta_ms / baseline_ms
    material = delta_ms > absolute_threshold_ms and relative_delta > RELATIVE_THRESHOLD
    return {
        "absolute_threshold_ms": absolute_threshold_ms,
        "baseline_ms_median": round(baseline_ms, 3),
        "candidate_ms_median": round(candidate_ms, 3),
        "delta_ms": round(delta_ms, 3),
        "delta_percent": round(relative_delta * 100.0, 3),
        "material_regression": material,
        "relative_threshold_percent": RELATIVE_THRESHOLD * 100.0,
    }


def _result_status(material_regressions: Sequence[str]) -> str:
    """Return the review state for the material-regression inventory."""

    return "investigate" if material_regressions else "pass"


def _resolve_commit(ref: str) -> str:
    """Resolve one non-option Git revision to a full commit identifier."""

    if not ref or ref.startswith("-") or "\x00" in ref or "\n" in ref:
        raise BenchmarkError("a benchmark revision is invalid")
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or _COMMIT_PATTERN.fullmatch(commit) is None:
        raise BenchmarkError("a benchmark revision could not be resolved")
    return commit


def _require_clean_tracked_tree() -> None:
    """Reject measurements that do not correspond to the candidate commit."""

    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BenchmarkError("the benchmark working tree could not be inspected")
    if result.stdout:
        raise BenchmarkError("tracked changes must be committed before benchmarking")


def _safe_archive_name(name: str) -> PurePosixPath:
    """Return one normalized relative archive path or reject it."""

    if not name or "\\" in name or "\x00" in name:
        raise BenchmarkError("a revision archive contains an unsafe member")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in name.split("/")):
        raise BenchmarkError("a revision archive contains an unsafe member")
    return path


def _archive_bytes(commit: str) -> bytes:
    """Return a bounded tar archive for one reviewed commit."""

    result = subprocess.run(
        ["git", "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode != 0:
        raise BenchmarkError("a benchmark revision could not be exported")
    if len(result.stdout) > _MAX_ARCHIVE_BYTES:
        raise BenchmarkError("a revision archive exceeds the benchmark limit")
    return result.stdout


def _extract_revision(commit: str, destination: Path) -> None:
    """Safely extract regular files and directories from ``git archive``."""

    archive = _archive_bytes(commit)
    destination.mkdir(parents=True, exist_ok=False)
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as stream:
            members = stream.getmembers()
            if len(members) > _MAX_ARCHIVE_MEMBERS:
                raise BenchmarkError("a revision archive has too many members")
            total_size = sum(member.size for member in members)
            if total_size > _MAX_ARCHIVE_BYTES:
                raise BenchmarkError("a revision archive exceeds the benchmark limit")
            for member in members:
                if member.size > _MAX_ARCHIVE_MEMBER_BYTES:
                    raise BenchmarkError("a revision archive member is too large")
                relative = _safe_archive_name(member.name)
                target = destination.joinpath(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                if not member.isfile():
                    raise BenchmarkError(
                        "a revision archive contains a non-regular member"
                    )
                target.parent.mkdir(parents=True, exist_ok=True)
                source = stream.extractfile(member)
                if source is None:
                    raise BenchmarkError("a revision archive member could not be read")
                with source, target.open("wb") as output:
                    shutil.copyfileobj(source, output)
                target.chmod(member.mode & 0o777)
    except (OSError, tarfile.TarError) as exc:
        raise BenchmarkError("a revision archive could not be extracted") from exc


def _python_in(environment: Path) -> Path:
    """Return the platform-specific interpreter in a virtual environment."""

    if os.name == "nt":
        return environment / "Scripts" / "python.exe"
    return environment / "bin" / "python"


def _prepare_revision(
    temporary_root: Path,
    *,
    label: str,
    ref: str,
    commit: str,
) -> RevisionEnvironment:
    """Export one revision and bind it ahead of shared dependencies."""

    root = temporary_root / label
    source = root / "source"
    environment = root / "environment"
    _extract_revision(commit, source)
    try:
        venv.EnvBuilder(
            clear=False,
            system_site_packages=False,
            with_pip=False,
        ).create(environment)
    except OSError as exc:
        raise BenchmarkError("a benchmark environment could not be created") from exc

    python = _python_in(environment)
    purelib_result = subprocess.run(
        [python, "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if purelib_result.returncode != 0:
        raise BenchmarkError("a benchmark environment could not be inspected")
    purelib = Path(purelib_result.stdout.strip())
    if not purelib.is_dir():
        raise BenchmarkError("a benchmark environment is incomplete")
    source_literal = repr(str(source / "src"))
    shared_literal = repr(str(_SHARED_SITE_PACKAGES))
    if not _SHARED_SITE_PACKAGES.is_dir():
        raise BenchmarkError("the shared benchmark environment is incomplete")
    try:
        (purelib / "gsplot-benchmark.pth").write_text(
            f"import sys; sys.path.insert(0, {shared_literal})\n"
            f"import sys; sys.path.insert(0, {source_literal})\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise BenchmarkError("a benchmark environment could not be configured") from exc
    return RevisionEnvironment(label, ref, commit, source, python)


def _sanitized_environment(cache_root: Path) -> dict[str, str]:
    """Return a minimal environment without inherited credentials or Python paths."""

    allowed = {
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
        "WINDIR",
    }
    environment = {key: value for key, value in os.environ.items() if key in allowed}
    environment.update(
        {
            "GSPLOT_DOCS_BASE_URL": "https://example.invalid/gsplot",
            "GSPLOT_DOCS_VERSION": "dev",
            "MPLBACKEND": "Agg",
            "MPLCONFIGDIR": str(cache_root / "matplotlib"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "SOURCE_DATE_EPOCH": "0",
            "XDG_CACHE_HOME": str(cache_root / "xdg-cache"),
            "XDG_CONFIG_HOME": str(cache_root / "xdg-config"),
        }
    )
    return environment


def _run_worker(
    revision: RevisionEnvironment,
    operation: str,
    iterations: int,
    environment: dict[str, str],
) -> Any:
    """Run an internal worker and parse its single JSON result."""

    result = subprocess.run(
        [
            revision.python,
            Path(__file__).resolve(),
            "_worker",
            operation,
            str(iterations),
            str(revision.source / "src"),
        ],
        cwd=revision.source,
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BenchmarkError(f"the {revision.label} {operation} worker failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise BenchmarkError(
            f"the {revision.label} {operation} worker returned invalid data"
        ) from exc


def _verify_source(module_file: str, source_root: str) -> None:
    """Ensure a worker imported gsplot from its exported revision."""

    try:
        Path(module_file).resolve().relative_to(Path(source_root).resolve())
    except ValueError as exc:
        raise BenchmarkError("a worker imported gsplot from the wrong source") from exc


def _worker_fingerprint(source_root: str) -> dict[str, str]:
    """Return only generic software and platform benchmark dimensions."""

    import matplotlib
    import numpy

    matplotlib.use("Agg", force=True)
    import gsplot

    _verify_source(gsplot.__file__, source_root)
    return {
        "backend": str(matplotlib.get_backend()),
        "implementation": platform.python_implementation(),
        "machine": platform.machine(),
        "matplotlib": matplotlib.__version__,
        "numpy": numpy.__version__,
        "platform": platform.system(),
        "python": platform.python_version(),
    }


def _worker_plot(operation: str, iterations: int, source_root: str) -> float:
    """Return one warmed plotting median from inside a revision environment."""

    if operation not in PLOT_OPERATIONS or iterations < 1:
        raise BenchmarkError("a plotting worker request is invalid")
    import matplotlib

    matplotlib.use("Agg", force=True)
    import matplotlib.pyplot as plt
    from matplotlib.axes import Axes

    import gsplot as gs

    _verify_source(gs.__file__, source_root)

    def invoke() -> None:
        figure, axis = gs.subplots()
        try:
            if not isinstance(axis, Axes):
                raise BenchmarkError("the plotting worker did not receive one Axes")
            if operation == "ordinary_line":
                gs.line(axis, [0, 1, 2], [0, 1, 4])
            elif operation == "ordinary_scatter":
                gs.scatter(axis, [0, 1, 2], [0, 1, 4])
            else:
                gs.cmap_line(axis, [0, 1, 2], [0, 1, 4], [0, 0.5, 1])
        finally:
            plt.close(figure)

    invoke()
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter_ns()
        invoke()
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
    return statistics.median(samples)


def _worker_main(arguments: Sequence[str]) -> int:
    """Execute an internal revision worker."""

    if len(arguments) != 4:
        return 2
    _, operation, raw_iterations, source_root = arguments
    try:
        iterations = int(raw_iterations)
        if operation == "fingerprint":
            value: Any = _worker_fingerprint(source_root)
        else:
            value = _worker_plot(operation, iterations, source_root)
    except (BenchmarkError, ImportError, OSError, TypeError, ValueError):
        return 2
    print(json.dumps(value, sort_keys=True))
    return 0


def _fresh_import_median(
    revision: RevisionEnvironment,
    environment: dict[str, str],
) -> float:
    """Measure fresh interpreter startup plus a side-effect-light import."""

    samples: list[float] = []
    for _ in range(IMPORT_ITERATIONS):
        started = time.perf_counter_ns()
        result = subprocess.run(
            [revision.python, "-c", "import gsplot"],
            cwd=revision.source,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        samples.append((time.perf_counter_ns() - started) / 1_000_000.0)
        if result.returncode != 0:
            raise BenchmarkError(f"the {revision.label} fresh import failed")
    return statistics.median(samples)


def _docs_build_ms(
    revision: RevisionEnvironment,
    temporary_root: Path,
    trial: int,
    environment: dict[str, str],
) -> float:
    """Measure one clean Sphinx build including all declared examples."""

    source = temporary_root / f"docs-{revision.label}-{trial}"
    output = temporary_root / f"docs-output-{revision.label}-{trial}"
    _extract_revision(revision.commit, source)
    started = time.perf_counter_ns()
    result = subprocess.run(
        [
            revision.python,
            "-m",
            "sphinx",
            "-W",
            "-b",
            "html",
            source / "docs",
            output,
        ],
        cwd=source,
        env=environment,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
    if result.returncode != 0:
        raise BenchmarkError(f"the {revision.label} documentation build failed")
    if not (output / "index.html").is_file():
        raise BenchmarkError(f"the {revision.label} documentation output is incomplete")
    return elapsed_ms


def _measure(
    baseline: RevisionEnvironment,
    candidate: RevisionEnvironment,
    temporary_root: Path,
    environment: dict[str, str],
) -> tuple[dict[str, dict[str, float | bool]], dict[str, str]]:
    """Measure both revisions and return comparisons plus environment data."""

    baseline_fingerprint = _run_worker(baseline, "fingerprint", 0, environment)
    candidate_fingerprint = _run_worker(candidate, "fingerprint", 0, environment)
    if baseline_fingerprint != candidate_fingerprint:
        raise BenchmarkError("benchmark revisions did not use the same environment")
    if not isinstance(baseline_fingerprint, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in baseline_fingerprint.items()
    ):
        raise BenchmarkError("the benchmark environment record is invalid")

    medians: dict[str, dict[str, float]] = {
        "fresh_import": {
            "baseline": _fresh_import_median(baseline, environment),
            "candidate": _fresh_import_median(candidate, environment),
        }
    }
    for operation in PLOT_OPERATIONS:
        medians[operation] = {
            "baseline": float(
                _run_worker(baseline, operation, PLOT_ITERATIONS, environment)
            ),
            "candidate": float(
                _run_worker(candidate, operation, PLOT_ITERATIONS, environment)
            ),
        }

    docs_samples: dict[str, list[float]] = {"baseline": [], "candidate": []}
    revisions = {"baseline": baseline, "candidate": candidate}
    for trial in range(DOCS_BUILDS):
        order = (
            ("baseline", "candidate") if trial % 2 == 0 else ("candidate", "baseline")
        )
        for label in order:
            docs_samples[label].append(
                _docs_build_ms(
                    revisions[label],
                    temporary_root,
                    trial,
                    environment,
                )
            )
    medians["docs_build"] = {
        label: statistics.median(samples) for label, samples in docs_samples.items()
    }

    comparisons = {
        name: compare_metric(
            values["baseline"],
            values["candidate"],
            ABSOLUTE_THRESHOLDS_MS[name],
        )
        for name, values in medians.items()
    }
    return comparisons, baseline_fingerprint


def run_benchmark(baseline_ref: str, candidate_ref: str) -> dict[str, Any]:
    """Run the fixed revision-pair protocol and return public-safe results."""

    _require_clean_tracked_tree()
    baseline_commit = _resolve_commit(baseline_ref)
    candidate_commit = _resolve_commit(candidate_ref)
    if baseline_commit == candidate_commit:
        raise BenchmarkError("baseline and candidate must be different commits")

    with tempfile.TemporaryDirectory(prefix="gsplot-benchmark-") as temporary_name:
        temporary_root = Path(temporary_name)
        cache_root = temporary_root / "cache"
        environment = _sanitized_environment(cache_root)
        baseline = _prepare_revision(
            temporary_root,
            label="baseline",
            ref=baseline_ref,
            commit=baseline_commit,
        )
        candidate = _prepare_revision(
            temporary_root,
            label="candidate",
            ref=candidate_ref,
            commit=candidate_commit,
        )
        comparisons, fingerprint = _measure(
            baseline,
            candidate,
            temporary_root,
            environment,
        )

    material = sorted(
        name
        for name, comparison in comparisons.items()
        if comparison["material_regression"]
    )
    return {
        "environment": fingerprint,
        "material_regressions": material,
        "metrics": comparisons,
        "protocol": {
            "docs_builds": DOCS_BUILDS,
            "fresh_import_iterations": IMPORT_ITERATIONS,
            "plot_iterations": PLOT_ITERATIONS,
            "plot_warmups": 1,
        },
        "revisions": {
            "baseline": {"commit": baseline_commit, "ref": baseline_ref},
            "candidate": {"commit": candidate_commit, "ref": candidate_ref},
        },
        "schema_version": 1,
        "status": _result_status(material),
    }


def main(arguments: Sequence[str] | None = None) -> int:
    """Parse revision arguments, execute the protocol, and print JSON."""

    selected = list(sys.argv[1:] if arguments is None else arguments)
    if selected[:1] == ["_worker"]:
        return _worker_main(selected)

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline",
        default=BASELINE_REF,
        help=f"reviewed baseline commit (default: {BASELINE_REF})",
    )
    parser.add_argument(
        "--candidate",
        default="HEAD",
        help="candidate commit (default: HEAD)",
    )
    args = parser.parse_args(selected)
    try:
        result = run_benchmark(args.baseline, args.candidate)
    except BenchmarkError as exc:
        parser.exit(2, f"benchmark failed: {exc}\n")
    except Exception:
        parser.exit(2, "benchmark failed unexpectedly; run the focused tests\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result["material_regressions"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
