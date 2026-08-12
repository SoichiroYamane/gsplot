"""Contract tests for the canonical ``import gsplot as gs`` facade."""

import matplotlib.pyplot as plt
import numpy as np

import gsplot as gs


def test_root_exposes_only_the_canonical_manifest_and_native_objects(tmp_path) -> None:
    """The short root vocabulary resolves to explicit, typed operations."""

    expected = {
        "subplots",
        "inset_axes",
        "line",
        "scatter",
        "cmap_line",
        "cmap_dash",
        "cmap_scatter",
        "sample_cmap",
        "style_axes",
        "title",
        "suptitle",
        "minor_ticks",
        "box_aspect",
        "panel_labels",
        "fig_facecolor",
        "legend",
        "legends",
        "legend_entries",
        "cmap_legend",
        "set_theme",
        "paper",
        "savefig",
        "show",
        "load_config",
        "read_array",
        "write_meta",
        "build_info",
        "use_backend",
        "Config",
        "AxisSpec",
        "Theme",
        "InsetSpec",
        "MetadataSnapshot",
        "BuildInfo",
        "LegendEntries",
        "GsplotError",
        "ConfigError",
        "DataError",
        "LayoutError",
        "PlotError",
        "OutputError",
        "MetadataError",
        "MosaicSpec",
        "NormalizeSpec",
        "ColorSpec",
        "AxesTarget",
        "PerTarget",
        "LineStyle",
        "Marker",
        "Unit",
        "SizePreset",
        "SizeSpec",
        "LayoutMode",
        "StyleMode",
        "Limit",
        "Scale",
        "TickSpec",
        "LabelRecord",
        "LabelRecords",
    }
    assert set(gs.__all__) == expected

    figure, ax = gs.subplots()
    assert gs.line(ax, [0, 1], [1, 2], props={"label": "line"})[0].axes is ax
    assert gs.scatter(ax, [0, 1], [2, 3]).axes is ax
    assert gs.cmap_line(ax, [0, 1], [1, 0], [0, 1]).axes is ax
    assert gs.cmap_scatter(ax, [0, 1], [1, 2], [0, 1]).axes is ax
    assert gs.title(ax, "signal").axes is ax
    assert gs.suptitle(figure, "experiment").figure is figure
    assert gs.legend(ax).axes is ax
    assert gs.build_info().commit is None
    assert gs.sample_cmap("viridis").shape == (10, 4)
    assert np.all(np.isfinite(gs.sample_cmap("viridis", count=2)))
    output = gs.savefig(figure, tmp_path / "figure", show=False)
    assert output[0].is_absolute()
    plt.close(figure)
