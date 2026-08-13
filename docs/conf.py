"""Sphinx configuration for the gsplot documentation."""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SITE_BASE_URL = "https://soichiroyamane.github.io/gsplot"
_DOCS_VERSION_PATTERN = re.compile(
    r"^v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$"
)

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
root_doc = "index"
master_doc = root_doc
language = "en"


@dataclass(frozen=True)
class DocsMetadata:
    """Normalized metadata shared by Sphinx, templates, and the switcher."""

    display_version: str
    version_match: str
    channel: str
    source_ref: str
    is_development: bool
    site_url: str


def _normalize_site_base_url(value: str) -> str:
    """Validate the public site URL used to construct canonical links."""

    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.netloc
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError("GSPLOT_DOCS_BASE_URL must be an absolute HTTP(S) URL")
    return normalized


def _resolve_docs_metadata(raw_version: str, base_url: str) -> DocsMetadata:
    """Resolve one explicit development or immutable release channel."""

    version = raw_version.strip()
    if version == "dev":
        return DocsMetadata(
            display_version="dev",
            version_match="dev",
            channel="dev",
            source_ref="main",
            is_development=True,
            site_url=f"{base_url}/dev",
        )
    match = _DOCS_VERSION_PATTERN.fullmatch(version)
    if match is None:
        raise RuntimeError(
            "GSPLOT_DOCS_VERSION must be `dev` or a strict X.Y.Z release"
        )
    display_version = ".".join(match.groups())
    tag = f"v{display_version}"
    return DocsMetadata(
        display_version=display_version,
        version_match=tag,
        channel=tag,
        source_ref=tag,
        is_development=False,
        site_url=f"{base_url}/{tag}",
    )


site_base_url = _normalize_site_base_url(
    os.environ.get("GSPLOT_DOCS_BASE_URL", DEFAULT_SITE_BASE_URL)
)
docs_metadata = _resolve_docs_metadata(
    os.environ.get("GSPLOT_DOCS_VERSION", "dev"), site_base_url
)
version = docs_metadata.display_version
release = docs_metadata.display_version

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinx_copybutton",
    "sphinxext.opengraph",
]

autosummary_generate = True
html_copy_source = False
html_show_sourcelink = False
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
add_module_names = False
modindex_common_prefix = ["gsplot."]
html_use_modindex = False
highlight_language = "python3"
numfig = True

# The published build must not depend on a live external inventory service.
# External references in user-facing pages use explicit links instead.
intersphinx_mapping = {}

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


def _safe_demo_path(value: object, field: str) -> str:
    """Return one normalized repository-relative demo path."""

    if not isinstance(value, str) or not value:
        raise RuntimeError(f"demo manifest {field} must be a non-empty string")
    selected = Path(value)
    if selected.is_absolute() or ".." in selected.parts or selected.parts[0] != "demo":
        raise RuntimeError(f"demo manifest {field} must stay under demo/")
    if selected.as_posix() != value:
        raise RuntimeError(f"demo manifest {field} must use normalized POSIX syntax")
    return value


def _load_demo_manifest(manifest_path: Path) -> dict[str, set[str]]:
    """Load and validate the explicit demo script/output inventory."""

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError("could not load the demo manifest") from exc
    if not isinstance(manifest, dict) or set(manifest) != {"schema_version", "demos"}:
        raise RuntimeError("demo manifest must contain schema_version and demos")
    if manifest["schema_version"] != 1 or not isinstance(manifest["demos"], list):
        raise RuntimeError("demo manifest must use schema_version 1 and a demos list")

    inventory: dict[str, set[str]] = {}
    claimed_outputs: set[str] = set()
    for position, entry in enumerate(manifest["demos"]):
        if not isinstance(entry, dict) or set(entry) != {"script", "outputs"}:
            raise RuntimeError(f"demo manifest entry {position} has invalid fields")
        script = _safe_demo_path(entry["script"], f"entry {position} script")
        outputs = entry["outputs"]
        if Path(script).suffix != ".py" or not isinstance(outputs, list):
            raise RuntimeError(f"demo manifest entry {position} is not a Python demo")
        if script in inventory:
            raise RuntimeError(f"demo manifest repeats script {script}")
        selected_outputs = {
            _safe_demo_path(output, f"entry {position} output") for output in outputs
        }
        if len(selected_outputs) != len(outputs):
            raise RuntimeError(f"demo manifest entry {position} repeats an output")
        if any(
            Path(output).parent != Path(script).parent
            or Path(output).suffix not in {".png", ".pdf"}
            for output in selected_outputs
        ):
            raise RuntimeError(
                f"demo manifest outputs for {script} must be PNG/PDF siblings"
            )
        duplicate_outputs = claimed_outputs & selected_outputs
        if duplicate_outputs:
            raise RuntimeError(
                "demo manifest assigns output more than once: "
                + ", ".join(sorted(duplicate_outputs))
            )
        claimed_outputs.update(selected_outputs)
        inventory[script] = selected_outputs
    return inventory


_DEMO_OUTPUTS = _load_demo_manifest(PROJECT_ROOT / "demo" / "manifest.json")


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
    """Reject unexpected, missing, or stale outputs from one demo run."""

    after = _file_state(PROJECT_ROOT / "demo")
    _validate_demo_output_state(before, after, allowed, demo_name)


def _validate_demo_output_state(
    before: dict[str, tuple[int, int]],
    after: dict[str, tuple[int, int]],
    allowed: set[str],
    demo_name: str,
) -> None:
    """Validate one demo's output snapshot without filesystem access."""

    changed = {path for path, state in after.items() if before.get(path) != state}
    changed.update(set(before) - set(after))
    unexpected = sorted(changed - allowed)
    if unexpected:
        raise RuntimeError(
            f"{demo_name} created, modified, or deleted files outside its "
            "output allowlist: " + ", ".join(unexpected)
        )
    missing = sorted(path for path in allowed if path not in after)
    if missing:
        raise RuntimeError(
            f"{demo_name} did not produce required output(s): " + ", ".join(missing)
        )
    stale = sorted(
        path for path in allowed if path in before and before[path] == after[path]
    )
    if stale:
        raise RuntimeError(
            f"{demo_name} left required output(s) unchanged: " + ", ".join(stale)
        )


def generate_images() -> None:
    """Run demo scripts so image assets match the checked-in examples.

    Each demo runs in a fresh Python process and in its own directory. This
    prevents a demo's working-directory or Matplotlib state from leaking into
    the Sphinx process and makes a non-zero demo exit code fail the docs build.
    Set ``GSPLOT_SKIP_DEMO_IMAGES=1`` when a build intentionally supplies its
    own pre-generated assets.
    """

    demo_path = PROJECT_ROOT / "demo"
    demo_files = sorted(demo_path.rglob("*.py"))
    if not demo_files:
        raise FileNotFoundError(f"No demo scripts found under {demo_path}")
    actual_scripts = {
        demo_file.relative_to(PROJECT_ROOT).as_posix() for demo_file in demo_files
    }
    declared_scripts = set(_DEMO_OUTPUTS)
    if actual_scripts != declared_scripts:
        missing = sorted(actual_scripts - declared_scripts)
        extra = sorted(declared_scripts - actual_scripts)
        raise RuntimeError(
            "demo manifest does not match executable scripts; "
            f"undeclared={missing}, missing={extra}"
        )
    if os.environ.get("GSPLOT_SKIP_DEMO_IMAGES") == "1":
        return

    for demo_file in demo_files:
        before = _file_state(demo_path)
        print(f"Running demo: {demo_file.relative_to(PROJECT_ROOT)}")
        subprocess.run(
            [sys.executable, "-B", str(demo_file)],
            cwd=demo_file.parent,
            env=_demo_environment(),
            check=True,
        )
        demo_name = demo_file.relative_to(PROJECT_ROOT).as_posix()
        _check_demo_outputs(before, _DEMO_OUTPUTS[demo_name], demo_name)


def setup(app):
    """Register repository-specific Sphinx hooks."""

    generate_images()
    app.connect("autodoc-skip-member", skip_members)


json_url = f"{site_base_url}/_meta/switcher.json"
version_match = docs_metadata.version_match
channel_label = (
    "the development documentation (main)"
    if docs_metadata.is_development
    else f"release {docs_metadata.version_match}"
)

html_show_sphinx = False
html_theme = "pydata_sphinx_theme"
html_context = {
    "github_user": "SoichiroYamane",
    "github_repo": "gsplot",
    "github_version": docs_metadata.source_ref,
    "doc_path": "docs",
    "default_mode": "dark",
    "gsplot_is_development": docs_metadata.is_development,
}
html_theme_options = {
    "announcement": f"You are reading {channel_label}.",
    "check_switcher": False,
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
templates_path = ["_templates"]
html_baseurl = f"{docs_metadata.site_url}/"
ogp_site_url = html_baseurl
ogp_canonical_url = html_baseurl
ogp_social_cards = {"enable": False}
ogp_image = "_static/logo/logo_title_gsplot.png"
ogp_image_alt = "gsplot documentation page preview"
html_static_path = ["_static"]
pygments_style = "monokai"
