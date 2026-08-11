Historical module paths
=======================

The following module paths are retained as deprecation shims for downstream
0.x analysis scripts. They are forwarding-only compatibility paths and are not
the canonical API. New code should use the root names documented in
``apis.rst``.

.. list-table::
   :header-rows: 1

   * - Historical path
     - Replacement
   * - ``gsplot.plot.*``
     - ``gsplot.line``, ``gsplot.scatter``, and the ``gsplot.cmap_*`` family
   * - ``gsplot.figure.*``
     - ``gsplot.subplots``, ``gsplot.inset_axes``, ``gsplot.savefig``
   * - ``gsplot.style.*``
     - ``gsplot.style_axes``, ``gsplot.set_theme``, and explicit legend helpers
   * - ``gsplot.config.*``
     - ``gsplot.Config`` and ``gsplot.load_config``
   * - ``gsplot.data.*``
     - ``gsplot.read_array``
   * - ``gsplot.color.*``
     - ``gsplot.sample_cmap``
   * - ``gsplot.path.*``
     - ``pathlib.Path`` and explicit caller-owned paths

Each shim emits a ``DeprecationWarning`` when imported. The compatibility
window is the 0.4.x and 1.x lines; removal requires a separate public Issue.

Legacy reference pages
----------------------

The existing page paths remain buildable so published documentation links do
not disappear during the compatibility window:

.. toctree::
   :hidden:

   apis/gsplot.color.colormap
   apis/gsplot.config.config
   apis/gsplot.data.load_file
   apis/gsplot.figure.axes
   apis/gsplot.figure.axes_inset
   apis/gsplot.figure.figure_tools
   apis/gsplot.figure.show
   apis/gsplot.hello_world.hello_world
   apis/gsplot.path.path
   apis/gsplot.plot.line
   apis/gsplot.plot.line_colormap_dashed
   apis/gsplot.plot.line_colormap_solid
   apis/gsplot.plot.scatter
   apis/gsplot.plot.scatter_colormap
   apis/gsplot.style.graph
   apis/gsplot.style.label
   apis/gsplot.style.legend
   apis/gsplot.style.legend_colormap
   apis/gsplot.style.ticks
   apis/gsplot.style.title
