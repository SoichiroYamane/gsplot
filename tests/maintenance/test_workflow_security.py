"""Regression checks for security-sensitive workflow boundaries."""

from pathlib import Path

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "gh-pages-sphinx.yml"


def _step_block(workflow: str, name: str) -> str:
    """Return one named workflow step without relying on a YAML dependency."""

    marker = f"      - name: {name}\n"
    start = workflow.index(marker) + len(marker)
    remainder = workflow[start:]
    end = remainder.find("\n      - name:")
    return remainder if end == -1 else remainder[:end]


def test_pages_catalog_scopes_token_to_live_build_only() -> None:
    """Fixture builds stay unauthenticated while live builds use read access."""

    workflow = WORKFLOW.read_text(encoding="utf-8")
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
