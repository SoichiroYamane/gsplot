"""Integration checks for canonical Figure/Axes ownership and retention."""

import gc
import weakref

import matplotlib.pyplot as plt

import gsplot as gs


def test_canonical_operations_do_not_retain_closed_figures_or_axes() -> None:
    """Repeated canonical plots release caller-owned Matplotlib objects."""

    figure_refs: list[weakref.ReferenceType] = []
    axes_refs: list[weakref.ReferenceType] = []
    for index in range(8):
        figure, axis = gs.subplots()
        gs.line(axis, [0, 1], [index, index + 1])
        figure_refs.append(weakref.ref(figure))
        axes_refs.append(weakref.ref(axis))
        plt.close(figure)
        del axis, figure

    gc.collect()
    assert all(reference() is None for reference in figure_refs)
    assert all(reference() is None for reference in axes_refs)
