"""Run public-safe median benchmarks for the structural reform.

The command writes no files and prints only aggregate timing data.  It is a
diagnostic for the performance budget in the structural reform requirements,
not a CI correctness gate by itself.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from typing import Callable


def _median_ms(operation: Callable[[], None], iterations: int) -> float:
    """Return the median duration after one warm-up call."""

    operation()
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        operation()
        samples.append((time.perf_counter() - started) * 1000.0)
    return statistics.median(samples)


def _fresh_import_ms(iterations: int) -> float:
    """Measure fresh-process import time without publishing host details."""

    source = "import gsplot"
    samples: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        subprocess.run([sys.executable, "-c", source], check=True)
        samples.append((time.perf_counter() - started) * 1000.0)
    return statistics.median(samples)


def main() -> None:
    """Parse a minimum-30-iteration benchmark request and print JSON."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    if args.iterations < 30:
        parser.error("--iterations must be at least 30")

    def ordinary_line() -> None:
        import matplotlib.pyplot as plt

        import gsplot as gs

        figure, axis = gs.subplots()
        gs.line(axis, [0, 1, 2], [0, 1, 4])
        plt.close(figure)

    def ordinary_scatter() -> None:
        import matplotlib.pyplot as plt

        import gsplot as gs

        figure, axis = gs.subplots()
        gs.scatter(axis, [0, 1, 2], [0, 1, 4])
        plt.close(figure)

    def colored_line() -> None:
        import matplotlib.pyplot as plt

        import gsplot as gs

        figure, axis = gs.subplots()
        gs.cmap_line(axis, [0, 1, 2], [0, 1, 4], [0, 0.5, 1])
        plt.close(figure)

    result = {
        "iterations": args.iterations,
        "fresh_import_ms_median": _fresh_import_ms(args.iterations),
        "ordinary_line_ms_median": _median_ms(ordinary_line, args.iterations),
        "ordinary_scatter_ms_median": _median_ms(ordinary_scatter, args.iterations),
        "colored_line_ms_median": _median_ms(colored_line, args.iterations),
    }
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
