"""Measure and enforce publication-example source budgets.

The checker is token- and AST-aware: comments are removed without treating a
``#`` inside a string as a comment, and true Python docstrings are excluded
from executable metrics. It writes no files and executes none of the measured
source.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import tokenize
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class Metrics:
    """Deterministic source measurements for one Python file."""

    physical_lines: int
    comment_free_lines: int
    comment_free_chars: int
    executable_lines: int
    executable_chars: int
    lexical_chars: int
    gsplot_calls: int


def _docstring_starts(tree: ast.AST) -> set[tuple[int, int]]:
    """Return source starts for AST-recognized docstring string tokens."""

    starts: set[tuple[int, int]] = set()
    containers = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        if not isinstance(node, containers) or not node.body:
            continue
        first = node.body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        starts.add((first.value.lineno, first.value.col_offset))
    return starts


def _without_docstrings(source: str, lines: Sequence[str], tree: ast.AST) -> list[str]:
    """Mask only AST-recognized docstring tokens while preserving other code."""

    selected = list(lines)
    starts = _docstring_starts(tree)
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.STRING or token.start not in starts:
            continue
        start_row, start_column = token.start
        end_row, end_column = token.end
        for row in range(start_row, end_row + 1):
            line = selected[row - 1]
            left = start_column if row == start_row else 0
            right = end_column if row == end_row else len(line)
            selected[row - 1] = line[:left] + " " * (right - left) + line[right:]
    return [line.rstrip() for line in selected]


def _without_comments(source: str) -> list[str]:
    """Return source lines with tokenizer-recognized comments removed."""

    lines = source.splitlines()
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        row, column = token.start
        lines[row - 1] = lines[row - 1][:column]
    return [line.rstrip() for line in lines]


def _gsplot_bindings(tree: ast.AST) -> tuple[set[str], set[str]]:
    """Return imported gsplot module aliases and direct callable bindings."""

    modules: set[str] = set()
    direct: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "gsplot":
                    modules.add(alias.asname or "gsplot")
        elif isinstance(node, ast.ImportFrom) and node.module == "gsplot":
            direct.update(alias.asname or alias.name for alias in node.names)
    return modules, direct


def _count_gsplot_calls(tree: ast.AST) -> int:
    """Count syntactic calls through imported gsplot root bindings."""

    modules, direct = _gsplot_bindings(tree)
    count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in modules
        ) or (isinstance(node.func, ast.Name) and node.func.id in direct):
            count += 1
    return count


def measure(path: Path) -> Metrics:
    """Measure one syntactically valid UTF-8 Python source without executing it."""

    source = sys.stdin.read() if path == Path("-") else path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    comment_free = _without_comments(source)
    comment_free_code = [line for line in comment_free if line.strip()]
    executable_source_lines = _without_docstrings(source, comment_free, tree)
    executable = [line for line in executable_source_lines if line.strip()]
    executable_source = "\n".join(executable_source_lines)
    ignored_tokens = {
        tokenize.ENDMARKER,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.NEWLINE,
        tokenize.NL,
        tokenize.ENCODING,
        tokenize.COMMENT,
    }
    lexical_chars = sum(
        len(token.string)
        for token in tokenize.generate_tokens(io.StringIO(executable_source).readline)
        if token.type not in ignored_tokens
    )
    return Metrics(
        physical_lines=len(source.splitlines()),
        comment_free_lines=len(comment_free_code),
        comment_free_chars=sum(len(line) for line in comment_free_code),
        executable_lines=len(executable),
        executable_chars=sum(len(line) for line in executable),
        lexical_chars=lexical_chars,
        gsplot_calls=_count_gsplot_calls(tree),
    )


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and minimally validate the versioned metrics manifest."""

    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("metrics manifest must use schema_version 1")
    if not isinstance(value.get("baselines"), dict) or not isinstance(
        value.get("budgets"), dict
    ):
        raise ValueError("metrics manifest requires baselines and budgets mappings")
    return value


def compare_expected(metrics: Metrics, expected: Mapping[str, object]) -> list[str]:
    """Return stable mismatch messages for one frozen baseline."""

    measured = asdict(metrics)
    mismatches = []
    for name, value in measured.items():
        if expected.get(name) != value:
            mismatches.append(f"{name}: expected {expected.get(name)!r}, got {value!r}")
    return mismatches


def check_budgets(
    metrics: Metrics,
    budgets: Mapping[str, object],
    issue_181: Mapping[str, object],
) -> list[str]:
    """Return violations of final maximums and Issue-181 reduction gates."""

    measured = asdict(metrics)
    violations: list[str] = []
    for name in (
        "physical_lines",
        "comment_free_lines",
        "comment_free_chars",
        "executable_lines",
        "executable_chars",
        "lexical_chars",
        "gsplot_calls",
    ):
        limit = budgets.get(name)
        value = measured[name]
        if not isinstance(limit, (int, float)) or isinstance(limit, bool):
            raise ValueError(f"budget {name!r} must be numeric")
        if value > limit:
            violations.append(f"{name}: maximum {limit}, got {value}")

    minimum = budgets.get("minimum_issue_181_reduction_percent")
    if not isinstance(minimum, (int, float)) or isinstance(minimum, bool):
        raise ValueError("minimum_issue_181_reduction_percent must be numeric")
    for name in ("executable_lines", "executable_chars"):
        baseline = issue_181.get(name)
        if not isinstance(baseline, (int, float)) or isinstance(baseline, bool):
            raise ValueError(f"Issue-181 baseline {name!r} must be numeric")
        reduction = (baseline - measured[name]) / baseline * 100.0
        if reduction < minimum:
            violations.append(
                f"{name}: requires {minimum:.1f}% reduction from Issue 181, "
                f"got {reduction:.2f}%"
            )
    return violations


def _table(records: Sequence[tuple[Path, Metrics]]) -> str:
    """Render stable tab-separated metric records."""

    names = tuple(Metrics.__dataclass_fields__)
    lines = ["path\t" + "\t".join(names)]
    for path, metrics in records:
        values = asdict(metrics)
        lines.append(
            "\t".join([path.as_posix(), *(str(values[name]) for name in names)])
        )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Measure requested sources and optionally enforce a frozen contract."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--expect")
    parser.add_argument("--check-budgets", action="store_true")
    args = parser.parse_args(argv)
    if (args.expect or args.check_budgets) and args.manifest is None:
        parser.error("--expect and --check-budgets require --manifest")
    if args.expect and len(args.paths) != 1:
        parser.error("--expect requires exactly one source path")

    records = [(path, measure(path)) for path in args.paths]
    failures: list[str] = []
    if args.manifest is not None:
        manifest = load_manifest(args.manifest)
        baselines = manifest["baselines"]
        if args.expect:
            expected = baselines.get(args.expect)
            if not isinstance(expected, dict):
                parser.error(f"unknown baseline {args.expect!r}")
            failures.extend(compare_expected(records[0][1], expected))
        if args.check_budgets:
            failures.extend(
                check_budgets(
                    records[0][1],
                    manifest["budgets"],
                    baselines["issue_181_repair"],
                )
            )

    if args.as_json:
        print(
            json.dumps(
                {path.as_posix(): asdict(metrics) for path, metrics in records},
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(_table(records))
    for failure in failures:
        print(f"error: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
