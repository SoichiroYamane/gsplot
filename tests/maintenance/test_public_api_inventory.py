"""Tests for the complete public and compatibility API inventory."""

from __future__ import annotations

import ast
import hashlib
import importlib
import inspect
from pathlib import Path

import gsplot
from gsplot._compat.root import resolve_legacy
from tools.maintenance.collect_public_api import (
    HISTORICAL_DOCUMENTED_MODULES,
    collect,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_inventory_combines_every_public_boundary() -> None:
    """Root, lazy, metadata, and documented surfaces stay distinguishable."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")

    assert inventory["root_all"] == gsplot.__all__
    assert set(inventory["canonical_manifest"]) == set(gsplot.__all__)
    assert len(inventory["api_index"]) == len(set(inventory["api_index"]))
    assert set(inventory["api_index"]) == set(gsplot.__all__)
    assert set(inventory["type_checking_exports"]) >= set(gsplot.__all__)
    assert set(inventory["type_checking_exports"]) >= set(
        inventory["legacy_manifest"]
    ) - set(gsplot.__all__)
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
    assert exports["MosaicSpec"]["kind"] == "type_alias"
    assert exports["MosaicSpec"]["signature"] is None

    for name, record in exports.items():
        if record["kind"] != "function":
            continue
        signature = inspect.signature(getattr(gsplot, name))
        assert all(
            parameter.kind is not inspect.Parameter.VAR_KEYWORD
            for parameter in signature.parameters.values()
        )
        assert "<object object at" not in str(signature)
        assert signature.return_annotation is not inspect.Signature.empty
        assert all(
            parameter.annotation is not inspect.Parameter.empty
            for parameter in signature.parameters.values()
        )


def test_canonical_manifest_targets_match_runtime_contract_records() -> None:
    """Targets, defaults, annotations, and docstrings cannot drift by layer."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")
    exports = {record["name"]: record for record in inventory["exports"]}

    for name, target_record in inventory["canonical_manifest"].items():
        target_module = importlib.import_module(target_record["module"])
        target = getattr(target_module, target_record["attribute"])
        runtime = getattr(gsplot, name)
        record = exports[name]

        assert runtime is target
        assert record["module"] == getattr(target, "__module__", None)
        assert record["qualname"] == getattr(target, "__qualname__", None)

        contract = record["call_contract"]
        if record["kind"] in {"callable", "class", "function"}:
            try:
                signature = inspect.signature(target)
            except (TypeError, ValueError):
                assert record["signature"] is None
                assert contract is None
                signature = None
            if signature is not None:
                assert record["signature"] == str(signature)
                assert contract is not None
                assert len(contract["parameters"]) == len(signature.parameters)
                for item, parameter in zip(
                    contract["parameters"],
                    signature.parameters.values(),
                    strict=True,
                ):
                    assert item == {
                        "annotation": (
                            None
                            if parameter.annotation is inspect.Parameter.empty
                            else inspect.formatannotation(parameter.annotation)
                        ),
                        "default": (
                            None
                            if parameter.default is inspect.Parameter.empty
                            else repr(parameter.default)
                        ),
                        "kind": parameter.kind.name,
                        "name": parameter.name,
                        "required": parameter.default is inspect.Parameter.empty,
                    }
                assert contract["return_annotation"] == (
                    None
                    if signature.return_annotation is inspect.Signature.empty
                    else inspect.formatannotation(signature.return_annotation)
                )
        else:
            assert record["signature"] is None
            assert contract is None

        docstring = inspect.getdoc(target)
        if docstring is None:
            assert record["docstring"] is None
        else:
            assert record["docstring"] == {
                "sha256": hashlib.sha256(docstring.encode("utf-8")).hexdigest(),
                "summary": docstring.splitlines()[0],
            }

        if record["kind"] in {"class", "function"}:
            assert record["docstring"] is not None


def test_historical_baseline_matches_every_retained_boundary() -> None:
    """The frozen v0.3 root and documented modules remain fully represented."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")
    historical = inventory["historical_baseline"]
    root_surface = set(historical["root_all"]) | set(
        historical["root_direct_attributes"]
    )

    assert root_surface == set(inventory["legacy_manifest"]) | set(
        inventory["metadata_attributes"]
    )
    assert historical["root_all"] == inventory["legacy_discoverable"]
    assert historical["documented_modules"] == inventory["compatibility_modules"]
    assert set(historical["documented_modules"]) == set(
        inventory["documented_compatibility_paths"]
    )


def test_documented_module_functions_forward_to_reviewed_root_adapters() -> None:
    """Legacy classes remain reachable, but documented functions do not fork code."""

    inventory = collect(migration_doc=PROJECT_ROOT / "docs/project/api-migration.md")
    for module_name, names in inventory["compatibility_modules"].items():
        module = importlib.import_module(module_name)
        for name in names:
            assert getattr(module, name) is resolve_legacy(name)


def test_overlapping_root_adapter_implementations_are_finite() -> None:
    """A concise signature cannot conceal a generic compatibility keyword bag."""

    source = PROJECT_ROOT / "src/gsplot/_compat/root_api.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    adapters = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef))
        and node.name in {"label", "legend", "line", "scatter", "show", "title"}
    }

    assert set(adapters) == {"label", "legend", "line", "scatter", "show", "title"}
    for node in adapters.values():
        assert node.args.vararg is None
        assert node.args.kwarg is None

    from gsplot._plot.basic import LINE_ADVANCED_OPTIONS, SCATTER_ADVANCED_OPTIONS

    line_parameters = {
        argument.arg
        for argument in (
            adapters["line"].args.posonlyargs
            + adapters["line"].args.args
            + adapters["line"].args.kwonlyargs
        )
    }
    scatter_parameters = {
        argument.arg
        for argument in (
            adapters["scatter"].args.posonlyargs
            + adapters["scatter"].args.args
            + adapters["scatter"].args.kwonlyargs
        )
    }
    assert set(LINE_ADVANCED_OPTIONS) <= line_parameters
    assert set(SCATTER_ADVANCED_OPTIONS) <= scatter_parameters


def test_frozen_historical_module_manifest_has_no_unreviewed_path() -> None:
    """The explicit v0.3 module baseline remains finite and fully qualified."""

    assert len(HISTORICAL_DOCUMENTED_MODULES) == 20
    assert all(name.startswith("gsplot.") for name in HISTORICAL_DOCUMENTED_MODULES)
    assert all(exports for exports in HISTORICAL_DOCUMENTED_MODULES.values())


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
