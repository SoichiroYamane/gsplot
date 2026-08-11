"""Sphinx configuration for the gsplot documentation."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

try:
    import gsplot
except ImportError as exc:  # pragma: no cover - exercised by docs CI setup
    raise RuntimeError(
        "Sphinx requires an installed or editable gsplot package; "
        "run `poetry install` before building the documentation"
    ) from exc

__version__ = gsplot.__version__
package_file = Path(gsplot.__file__).resolve()
if package_file.parent.name != "gsplot":
    raise RuntimeError(f"unexpected gsplot package location: {package_file}")
if package_file.parent == PROJECT_ROOT / "gsplot":
    raise RuntimeError("documentation must not import a repository-root package")

project = "gsplot"
copyright = "2024, Giordano Mattoni and Soichiro Yamane"
author = "Giordano Mattoni and Soichiro Yamane"
default_docs_version = "dev" if __version__ == "0+unknown" else __version__
version = os.environ.get("GSPLOT_DOCS_VERSION", default_docs_version)
release = version
root_doc = "index"
master_doc = root_doc
language = "en"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinxext.opengraph",
    "sphinx_pyscript",
    "sphinx_tippy",
    "sphinx_togglebutton",
]

autosummary_generate = True
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
add_module_names = False
modindex_common_prefix = ["gsplot."]
html_use_modindex = False
highlight_language = "python3"
numfig = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/stable/", None),
}

# Napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_ivar = True
napoleon_preprocess_types = True
napoleon_attr_annotations = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_references = True
napoleon_use_admonition_for_todo = True
napoleon_use_admonition_for_hints = True
napoleon_use_admonition_for_tips = True
napoleon_use_admonition_for_caution = True
napoleon_use_admonition_for_warning = True
napoleon_type_aliases = {
    "ndarray": "numpy.ndarray",
    "DataFrame": "pandas.DataFrame",
}

# MyST
myst_enable_extensions = ["colon_fence", "dollarmath", "amsmath", "deflist"]

# Autodoc
autodoc_inherit_docstrings = True
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "toctree": True,
    "undoc-members": False,
    "show-inheritance": True,
    "special-members": "__init__",
    "exclude-members": "__weakref__",
}

# Copy button
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True


def skip_members(app, what, name, obj, skip, options):
    """Hide implementation details that are absent from a module's ``__all__``."""

    if not hasattr(obj, "__module__"):
        return True

    try:
        module = sys.modules.get(obj.__module__)
        public_names = getattr(module, "__all__", None)
    except Exception:  # pragma: no cover - defensive protection for autodoc
        logging.getLogger(__name__).exception(
            "Could not inspect %s while filtering autodoc members", name
        )
        return True

    if public_names is not None and name not in public_names:
        return True
    return skip


def _demo_environment() -> dict[str, str]:
    """Return an isolated, headless environment for a demo subprocess."""

    environment = os.environ.copy()
    environment.setdefault("MPLBACKEND", "Agg")
    # Demos must resolve the installed/editable package from the Poetry
    # environment, never a checkout-root path injected by the documentation
    # build.  Remove an inherited path so local shell state cannot mask it.
    environment.pop("PYTHONPATH", None)
    return environment


_DEMO_OUTPUTS = {
    "demo/0_hello_world": set(),
    "demo/1_axes": {"demo/1_axes/axes.png", "demo/1_axes/axes.pdf"},
    "demo/2_line_and_label": {
        "demo/2_line_and_label/line_and_label.png",
        "demo/2_line_and_label/line_and_label.pdf",
    },
    "demo/3_config": {
        "demo/3_config/config.png",
        "demo/3_config/config.pdf",
    },
    "demo/4_paper_plot": {
        "demo/4_paper_plot/SC_cal.png",
        "demo/4_paper_plot/SC_cal.pdf",
    },
    "demo/5_scatter": {
        "demo/5_scatter/scatter.png",
        "demo/5_scatter/scatter.pdf",
    },
    "demo/6_line_colormap": {
        "demo/6_line_colormap/line_colormap.png",
        "demo/6_line_colormap/line_colormap.pdf",
    },
    "demo/7_graph_white": {
        "demo/7_graph_white/graph_white.png",
        "demo/7_graph_white/graph_white.pdf",
    },
    "demo/8_graph_transparent": {
        "demo/8_graph_transparent/graph_transparent.png",
        "demo/8_graph_transparent/graph_transparent.pdf",
    },
    "demo/9_compatibility": {
        "demo/9_compatibility/compatibility.png",
        "demo/9_compatibility/compatibility.pdf",
    },
    "demo/10_subplots": {"demo/10_subplots/subplots.png"},
    "demo/11_directory": set(),
    "demo/test_plot": {
        "demo/test_plot/SC_cal.png",
        "demo/test_plot/SC_cal.pdf",
    },
}


def _file_state(root: Path) -> dict[str, tuple[int, int]]:
    """Return file size and timestamp state under ``root``."""

    return {
        path.relative_to(PROJECT_ROOT).as_posix(): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
        )
        for path in root.rglob("*")
        if path.is_file()
    }


def _check_demo_outputs(
    before: dict[str, tuple[int, int]], allowed: set[str], demo_name: str
) -> None:
    """Reject one demo's created, modified, or deleted files outside its allowlist."""

    after = _file_state(PROJECT_ROOT / "demo")
    changed = {path for path, state in after.items() if before.get(path) != state}
    changed.update(set(before) - set(after))
    unexpected = sorted(changed - allowed)
    if unexpected:
        raise RuntimeError(
            f"{demo_name} created, modified, or deleted files outside its "
            "output allowlist: " + ", ".join(unexpected)
        )


def generate_images() -> None:
    """Run demo scripts so image assets match the checked-in examples.

    Each demo runs in a fresh Python process and in its own directory. This
    prevents a demo's working-directory or Matplotlib state from leaking into
    the Sphinx process and makes a non-zero demo exit code fail the docs build.
    Set ``GSPLOT_SKIP_DEMO_IMAGES=1`` when a build intentionally supplies its
    own pre-generated assets.
    """

    if os.environ.get("GSPLOT_SKIP_DEMO_IMAGES") == "1":
        return

    demo_path = PROJECT_ROOT / "demo"
    demo_files = sorted(demo_path.rglob("*.py"))
    if not demo_files:
        raise FileNotFoundError(f"No demo scripts found under {demo_path}")

    for demo_file in demo_files:
        before = _file_state(demo_path)
        print(f"Running demo: {demo_file.relative_to(PROJECT_ROOT)}")
        subprocess.run(
            [sys.executable, "-B", str(demo_file)],
            cwd=demo_file.parent,
            env=_demo_environment(),
            check=True,
        )
        demo_name = demo_file.parent.relative_to(PROJECT_ROOT).as_posix()
        _check_demo_outputs(before, _DEMO_OUTPUTS[demo_name], demo_name)


# Sphinx Multiversion configuration
smv_tag_whitelist = r"^v\d+\.\d+\.\d+$"
smv_branch_whitelist = r"^main$"
smv_remote_whitelist = r"^origin$"
smv_released_pattern = r"^refs/tags/v.*$"
smv_outputdir_format = "{ref.name}"


def setup(app):
    """Register repository-specific Sphinx hooks and multiversion settings."""

    app.add_config_value("smv_metadata_path", None, "env")
    app.add_config_value("smv_current_version", None, "env")
    app.add_config_value("smv_tag_whitelist", smv_tag_whitelist, "env")
    app.add_config_value("smv_branch_whitelist", smv_branch_whitelist, "env")
    app.add_config_value("smv_remote_whitelist", smv_remote_whitelist, "env")
    app.add_config_value("smv_released_pattern", smv_released_pattern, "env")
    app.add_config_value("smv_outputdir_format", smv_outputdir_format, "env")
    generate_images()
    app.connect("autodoc-skip-member", skip_members)


json_url = "https://soichiroyamane.github.io/gsplot/_static/switcher.json"
version_match = "dev" if default_docs_version == "dev" else f"v{default_docs_version}"

html_show_sphinx = False
html_theme = "pydata_sphinx_theme"
html_context = {
    "github_user": "SoichiroYamane",
    "github_repo": "gsplot",
    "github_version": "main",
    "doc_path": "docs",
    "default_mode": "dark",
}
html_theme_options = {
    "logo": {
        "text": "gsplot 📈",
        "image_light": "_static/logo/logo_gsplot.svg",
        "image_dark": "_static/logo/logo_gsplot.svg",
    },
    "pygments_light_style": "manni",
    "pygments_dark_style": "monokai",
    "navbar_start": ["navbar-logo"],
    "footer_start": ["copyright"],
    "footer_end": ["version-switcher"],
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/SoichiroYamane/gsplot",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        }
    ],
    "switcher": {
        "version_match": version_match,
        "json_url": json_url,
    },
}
html_static_path = ["_static"]
pygments_style = "monokai"
