import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from gsplot.version import __version__

sys.path.insert(0, os.path.abspath("../"))
project = "gsplot"
copyright = "2024, Giordano Mattoni, Soichiro Yamane"
author = "Giordano Mattoni, Soichiro Yamane"
version = __version__
master_doc = "index"
language = "en"


extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
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
templates_path = ["_templates"]
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


# Setting of napoleon
napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_use_param = True  # show parameter type
napoleon_use_rtype = True  # show return type
napoleon_use_ivar = True  # show instance variables
napoleon_preprocess_types = True
# napoleon_type_aliases = None
napoleon_attr_annotations = True
# napoleon_custom_sections = None
# napoleon_custom_sections = None
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonttion_for_references = True
napoleon_use_admonition_for_todo = True
napoleon_use_admonition_for_hints = True
napoleon_use_admonition_for_tips = True
napoleon_use_admonition_for_caution = True
napoleon_use_admonition_for_warning = True
napoleon_type_aliases = {
    "ndarray": "numpy.ndarray",
    "DataFrame": "pandas.DataFrame",
}


# https://sphinx-design.readthedocs.io/en/latest/get_started.html
# For using with MyST Parser, for Markdown documentation, it is recommended to use the colon_fence syntax extension:
myst_enable_extensions = ["colon_fence", "dollarmath", "amsmath", "deflist"]

# Setting of autodoc
autodoc_inherit_docstrings = True
autodoc_typehints = "none"
autodoc_default_options = {
    "members": True,
    "toctree": True,
    "undoc-members": True,
    "show-inheritance": True,
    "special-members": "__init__",
    "exclude-members": "__weakref__",
}

# Setting of copy button
copybutton_prompt_text = r">>> |\.\.\. |\$ "
copybutton_prompt_is_regexp = True
copybutton_only_copy_prompt_lines = True


def skip_members(app, what, name, obj, skip, options):
    """
    Skip members that are not included in __all__ of the module.
    Handles cases where the module or __all__ attribute is missing gracefully.

    Args:
        app (Sphinx): The Sphinx application object.
        what (str): The type of the object being documented (e.g., 'module', 'class').
        name (str): The name of the member being checked.
        obj (object): The member object.
        skip (bool): Whether the member is already marked to be skipped.
        options (object): Options given to the directive.

    Returns:
        bool: True if the member should be skipped, False otherwise.
    """
    try:
        # Ensure the object has a __module__ attribute
        if not hasattr(obj, "__module__"):
            return True  # Skip if the object has no module association

        # Get the module of the object
        module_name = obj.__module__

        # Check if the module is loaded and has an __all__ attribute
        module = sys.modules.get(module_name)
        if module and hasattr(module, "__all__"):
            # Skip the member if it is not in __all__
            if name not in module.__all__:
                return True

    except Exception as e:
        # Log the exception and skip the member gracefully
        app.warn(f"Error in skip_members: {e}")
        return True

    # If none of the conditions matched, use the default skip behavior
    return skip


# Sphinx Multiversion configuration
smv_tag_whitelist = r"^v\d+\.\d+\.\d+$"  # Matches tags in the format v1.0.0
smv_branch_whitelist = r"^main$"  # Includes the main branch
smv_remote_whitelist = r"^origin$"  # Uses the default remote
smv_released_pattern = r"^refs/tags/v.*$"  # Treats tags as release versions
smv_outputdir_format = (
    "{ref.name}"  # Sets the output directory to the branch or tag name
)


def generate_images():

    demo_path = Path(os.path.abspath("demo"))

    if not demo_path.exists():
        raise FileNotFoundError(f"Demo directory not found: {demo_path}")

    for py_file in demo_path.rglob("*.py"):
        path = Path(py_file).parent
        os.chdir(path)
        print(f"Executing: {py_file}")
        subprocess.run(["python", str(py_file)], check=True)


def setup(app):
    # Add Sphinx Multiversion configuration variables
    app.add_config_value("smv_metadata_path", None, "env")
    app.add_config_value("smv_current_version", None, "env")
    app.add_config_value("smv_tag_whitelist", smv_tag_whitelist, "env")
    app.add_config_value("smv_branch_whitelist", smv_branch_whitelist, "env")
    app.add_config_value("smv_remote_whitelist", smv_remote_whitelist, "env")
    app.add_config_value("smv_released_pattern", smv_released_pattern, "env")
    app.add_config_value("smv_outputdir_format", smv_outputdir_format, "env")

    # Generate images for the documentation from the demo scripts
    generate_images()

    generate_autosummary_list("gsplot", Path(__file__).parent / ".." / "gsplot")
    app.connect("autodoc-skip-member", skip_members)


project_root = Path(__file__).parent / ".."
sys.path.insert(0, str(project_root))


def generate_autosummary_list(root_package, base_path, exclude=None):
    """
    Generate a list of modules for autosummary dynamically, filtering by non-empty __all__.

    Parameters:
    - root_package: The root package name (e.g., 'gsplot')
    - base_path: The base directory where the package is located
    - exclude: List of modules to exclude

    Returns:
    - A list of module names with non-empty __all__
    """
    exclude = exclude or []
    modules = []
    base_path = Path(base_path)

    for module_path in base_path.rglob("*.py"):
        # Skip __init__.py files and excluded files
        if module_path.name == "__init__.py" or module_path.stem in exclude:
            continue

        # Build the full module name
        relative_path = module_path.relative_to(base_path).with_suffix("")
        module_name = f"{root_package}.{str(relative_path).replace('/', '.')}"

        # Load the module to check for __all__
        if has_non_empty_all(module_name):
            modules.append(module_name)

    return modules


def has_non_empty_all(module_name):
    """
    Check if the module has a non-empty __all__ attribute.

    Parameters:
    - module_name: The fully qualified module name

    Returns:
    - True if __all__ is defined and non-empty, otherwise False
    """
    try:
        module = importlib.import_module(module_name)
        return hasattr(module, "__all__") and bool(module.__all__)
    except Exception as e:
        print(f"Error loading module {module_name}: {e}")
        return False


# Example usage
root_package = "gsplot"
base_path = Path(__file__).parent / ".." / root_package

# Target file for autosummary
autosummary_file = Path(__file__).parent / "api_reference/apis.rst"

# Generate module list
autosummary_modules = generate_autosummary_list(root_package, base_path)

# Write the result to the RST file
with open(autosummary_file, "w") as f:
    f.write("📖 APIs\n")
    f.write("================\n\n")
    f.write(".. autosummary::\n")
    f.write("   :toctree: ./apis\n")
    f.write("\n")
    for module in autosummary_modules:
        f.write(f"   {module}\n")


# Function to run Git commands and retrieve tags and branches
def get_git_versions():
    # Get Git tags
    tags = subprocess.check_output(["git", "tag"], text=True).strip().split("\n")
    # Get Git branches
    branches = (
        subprocess.check_output(
            ["git", "branch", "--format", "%(refname:short)"], text=True
        )
        .strip()
        .split("\n")
    )
    return tags, branches


# Generate version information for the JSON
def generate_version_data():
    tags, branches = get_git_versions()

    # List to store JSON version data
    versions: list[dict[str, Any]] = []

    # Add development version (main branch)
    if "main" in branches:
        versions.append(
            {
                "name": "dev",
                "version": "main",
                "url": "https://soichiroyamane.github.io/gsplot/dev/",
            }
        )

    # Add tag versions
    for tag in sorted(tags, reverse=True):  # Sort tags in descending order
        if tag == tags[-1]:
            version_info = {
                "name": f"{tag} (stable)",  # Mark the latest tag as stable
                "version": f"{tag}",
                "url": f"https://soichiroyamane.github.io/gsplot/stable/",
                "preferred": True,
            }
        else:
            version_info = {
                "name": f"{tag}",
                "version": f"{tag}",
                "url": f"https://soichiroyamane.github.io/gsplot/{tag}/",
            }
        version_info = {
            key: str(value) if not isinstance(value, bool) else value
            for key, value in version_info.items()
        }
        versions.append(version_info)

    return versions


# Define the output directory and file name
output_dir = Path("_static")
output_file = output_dir / "switcher.json"


# Create the JSON file
def write_version_switcher():
    versions = generate_version_data()

    # Ensure the output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write version data to the JSON file
    with open(output_file, "w") as f:
        json.dump(versions, f, indent=2)


# Generate the version switcher JSON file
write_version_switcher()

json_url = "https://soichiroyamane.github.io/gsplot/stable/_static/switcher.json"
version_match = f"v{__version__}"


html_show_sphinx = False
html_theme = "pydata_sphinx_theme"
html_context = {
    "github_user": "SoichiroYamane",
    "github_repo": "gsplot",
    "github_version": "main",
    "doc_path": "docs",
    "default_mode": "dark",
}
# html_sidebars = {
#     "**": ["search-field.html", "sidebar-nav-bs.html", "sidebar-ethical-ads.html"]
# }
html_theme_options = {
    # "default_mode": "light",
    "logo": {
        "text": "gsplot 📈",
        "image_light": "_static/logo/logo_gsplot.svg",
        "image_dark": "_static/logo/logo_gsplot.svg",
    },
    "pygment_light_style": "manni",
    "pygment_dark_style": "monokai",
    "navbar_start": [
        "navbar-logo",
    ],
    "footer_start": ["copyright"],
    "footer_end": ["version-switcher"],
    "use_edit_page_button": True,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/SoichiroYamane/gsplot",
            "icon": "fa-brands fa-square-github",
            "type": "fontawesome",
        },
    ],
    "switcher": {
        "version_match": version_match,
        "json_url": json_url,
    },
}
html_static_path = ["_static"]

pygments_style = "monokai"  # Syntax highlighting
