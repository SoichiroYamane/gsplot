Canonical API
=============

The root facade is the supported canonical import surface:

.. code-block:: python

   import gsplot as gs

The implementation packages under ``gsplot._*`` are private. Historical
module URLs remain available as compatibility references during the 0.4.x and
1.x lines, but they are not part of this canonical API index.

Functions
---------

.. autosummary::
   :toctree: ./apis

   gsplot.subplots
   gsplot.inset_axes
   gsplot.line
   gsplot.scatter
   gsplot.cmap_line
   gsplot.cmap_dash
   gsplot.cmap_scatter
   gsplot.sample_cmap
   gsplot.style_axes
   gsplot.title
   gsplot.suptitle
   gsplot.minor_ticks
   gsplot.box_aspect
   gsplot.panel_labels
   gsplot.fig_facecolor
   gsplot.legend
   gsplot.legends
   gsplot.legend_entries
   gsplot.cmap_legend
   gsplot.set_theme
   gsplot.savefig
   gsplot.show
   gsplot.load_config
   gsplot.read_array
   gsplot.write_meta
   gsplot.build_info
   gsplot.use_backend

Value types and errors
----------------------

.. autosummary::
   :toctree: ./apis

   gsplot.Config
   gsplot.AxisSpec
   gsplot.Theme
   gsplot.InsetSpec
   gsplot.MetadataSnapshot
   gsplot.BuildInfo
   gsplot.LegendEntries
   gsplot.GsplotError
   gsplot.ConfigError
   gsplot.DataError
   gsplot.LayoutError
   gsplot.PlotError
   gsplot.OutputError
   gsplot.MetadataError

Type aliases
------------

.. autosummary::
   :toctree: ./apis

   gsplot.MosaicSpec
   gsplot.NormalizeSpec
   gsplot.ColorSpec

.. toctree::
   :hidden:

   legacy-modules
