"""Regression checks for security-sensitive workflow boundaries."""

from pathlib import Path

WORKFLOW_ROOT = Path(__file__).parents[2] / ".github" / "workflows"
PAGES_WORKFLOW = WORKFLOW_ROOT / "gh-pages-sphinx.yml"
CI_WORKFLOW = WORKFLOW_ROOT / "ci.yml"
PUBLISH_WORKFLOW = WORKFLOW_ROOT / "publish_package.yml"


def _step_block(workflow: str, name: str) -> str:
    """Return one named workflow step without relying on a YAML dependency."""

    marker = f"      - name: {name}\n"
    start = workflow.index(marker) + len(marker)
    remainder = workflow[start:]
    end = remainder.find("\n      - name:")
    return remainder if end == -1 else remainder[:end]


def test_pages_catalog_scopes_token_to_live_build_only() -> None:
    """Fixture builds stay unauthenticated while live builds use read access."""

    workflow = PAGES_WORKFLOW.read_text(encoding="utf-8")
    catalog_job = workflow.split("\n  build:\n", 1)[0]
    fixture = _step_block(workflow, "Build pull-request fixture catalog")
    live = _step_block(workflow, "Build live catalog")

    assert "pull_request:" in catalog_job
    assert "permissions:\n      contents: read" in catalog_job
    assert "if: ${{ github.event_name == 'pull_request' }}" in fixture
    assert "GITHUB_TOKEN" not in fixture
    assert "if: ${{ github.event_name != 'pull_request' }}" in live
    assert "GITHUB_TOKEN: ${{ github.token }}" in live
    assert workflow.count("GITHUB_TOKEN:") == 1


def test_ci_package_job_builds_before_clean_install() -> None:
    """Pull requests validate exact artifacts in a source-free environment."""

    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    package_job = workflow.split("\n  package:\n", 1)[1]
    build = _step_block(workflow, "Build and inspect distributions")
    smoke = _step_block(workflow, "Smoke-test the installed wheel")

    assert "permissions:\n  contents: read" in workflow
    assert "python tools/maintenance/check_dist.py dist" in build
    assert "poetry build" in build
    assert "python -m venv" in smoke
    assert "--only-binary=:all:" in smoke
    assert '--forbid-source-root "$GITHUB_WORKSPACE"' in smoke
    assert package_job.index("Build and inspect distributions") < package_job.index(
        "Smoke-test the installed wheel"
    )
    assert "id-token: write" not in package_job


def test_publish_keeps_validation_outside_the_oidc_job() -> None:
    """Only reviewed artifacts cross from the read-only build into publishing."""

    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    build_job, publish_job = workflow.split("\n  publish:\n", 1)
    inspect_step = _step_block(workflow, "Inspect package distributions")
    smoke_step = _step_block(workflow, "Smoke-test the installed wheel")

    assert "permissions:\n  contents: read" in workflow
    assert "python tools/maintenance/check_dist.py dist" in inspect_step
    assert '--forbid-source-root "$GITHUB_WORKSPACE"' in smoke_step
    assert "id-token: write" not in build_job
    assert publish_job.count("id-token: write") == 1
    assert "needs: build" in publish_job
    assert "pypa/gh-action-pypi-publish@" in publish_job
