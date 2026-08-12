"""Tests for the complete public and compatibility API inventory."""

from __future__ import annotations

from pathlib import Path

import gsplot
from tools.maintenance.collect_public_api import collect

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_inventory_combines_every_public_boundary() -> None:
    """Root, lazy, metadata, and documented surfaces stay distinguishable."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")

    assert inventory["root_all"] == gsplot.__all__
    assert set(inventory["canonical_manifest"]) == set(gsplot.__all__)
    assert set(inventory["metadata_attributes"]) == {"__commit__", "__version__"}
    assert set(inventory["legacy_discoverable"]) <= set(inventory["legacy_manifest"])
    assert set(inventory["legacy_manifest"]) - set(
        inventory["legacy_discoverable"]
    ) == {"Config", "logger", "save_metadata"}
    assert "gsplot.plot.line" in inventory["documented_compatibility_paths"]
    assert "gsplot.style.label" in inventory["documented_compatibility_paths"]
    assert all(
        path.startswith("gsplot.")
        for path in inventory["documented_compatibility_paths"]
    )


def test_inventory_exports_have_reproducible_signatures() -> None:
    """Every advertised canonical name has one inspectable inventory record."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")
    exports = {record["name"]: record for record in inventory["exports"]}

    assert set(exports) == set(gsplot.__all__)
    assert exports["subplots"]["signature"] is not None
    assert exports["Config"]["kind"] == "class"
    assert exports["MosaicSpec"]["kind"] not in {"function", "module"}


def test_migration_matrix_names_every_lazy_root_entry() -> None:
    """No compatibility target can disappear behind the lazy facade."""

    migration = (PROJECT_ROOT / "docs/project/api-migration.md").read_text(
        encoding="utf-8"
    )
    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")

    for name in inventory["legacy_manifest"]:
        assert f"`{name}`" in migration


def test_migration_matrix_covers_documented_compatibility_pages() -> None:
    """Every generated historical submodule page appears in the inventory."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")
    documented_pages = {
        path.stem
        for path in (PROJECT_ROOT / "docs/api_reference/apis").glob("gsplot.*.rst")
        if path.stem.count(".") >= 2
    }

    assert set(inventory["documented_compatibility_paths"]) == documented_pages
