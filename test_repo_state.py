"""
Unit tests validating the prepared GitHub Pages repository state.

Validates: Requirements 1.1, 1.2, 3.1, 3.2, 4.1, 4.2, 6.3
"""

import os
import pathlib

import pytest

# Resolve the repository root as the directory this file lives in
REPO_ROOT = pathlib.Path(__file__).parent.resolve()


# ---------------------------------------------------------------------------
# Requirement 3.2 – CNAME file
# ---------------------------------------------------------------------------

class TestCNAME:
    """Validates: Requirements 3.2"""

    def test_cname_exists(self):
        """CNAME file must be present at the repository root."""
        assert (REPO_ROOT / "CNAME").exists(), "CNAME file does not exist"

    def test_cname_contains_primary_domain(self):
        """CNAME must contain exactly 'jasonend.cloud'."""
        content = (REPO_ROOT / "CNAME").read_text().strip()
        assert content == "jasonend.cloud", (
            f"CNAME should contain 'jasonend.cloud', got '{content}'"
        )


# ---------------------------------------------------------------------------
# Requirement 3.1 – .nojekyll file
# ---------------------------------------------------------------------------

class TestNoJekyll:
    """Validates: Requirements 3.1"""

    def test_nojekyll_exists(self):
        """.nojekyll file must be present at the repository root."""
        assert (REPO_ROOT / ".nojekyll").exists(), ".nojekyll file does not exist"


# ---------------------------------------------------------------------------
# Requirement 1.1 – plugins directory removed
# ---------------------------------------------------------------------------

class TestPluginsRemoved:
    """Validates: Requirements 1.1"""

    def test_plugins_directory_does_not_exist(self):
        """wp-content/plugins/ must not exist in the repository."""
        plugins_dir = REPO_ROOT / "wp-content" / "plugins"
        assert not plugins_dir.exists(), (
            f"wp-content/plugins/ should have been deleted but still exists at {plugins_dir}"
        )


# ---------------------------------------------------------------------------
# Requirement 1.2 – author page removed
# ---------------------------------------------------------------------------

class TestAuthorPageRemoved:
    """Validates: Requirements 1.2"""

    def test_author_jasonend_directory_does_not_exist(self):
        """author/jasonend/ must not exist in the repository."""
        author_dir = REPO_ROOT / "author" / "jasonend"
        assert not author_dir.exists(), (
            f"author/jasonend/ should have been deleted but still exists at {author_dir}"
        )


# ---------------------------------------------------------------------------
# Requirement 6.3 – required HTML pages retained
# ---------------------------------------------------------------------------

class TestRequiredHTMLPages:
    """Validates: Requirements 6.3"""

    @pytest.mark.parametrize("rel_path", [
        "index.html",
        "about-jason/index.html",
        "validated/index.html",
    ])
    def test_html_page_exists(self, rel_path):
        """Each required HTML page must exist at the expected path."""
        page = REPO_ROOT / rel_path
        assert page.exists(), f"Required page '{rel_path}' does not exist"


# ---------------------------------------------------------------------------
# Requirements 4.1, 4.2 – GitHub Actions deployment workflow
# ---------------------------------------------------------------------------

class TestDeploymentWorkflow:
    """Validates: Requirements 4.1, 4.2"""

    @pytest.fixture(scope="class")
    @classmethod
    def workflow_content(cls):
        workflow_path = REPO_ROOT / ".github" / "workflows" / "static.yml"
        assert workflow_path.exists(), (
            ".github/workflows/static.yml does not exist"
        )
        return workflow_path.read_text()

    def test_workflow_uses_peaceiris_action(self, workflow_content):
        """Workflow must use peaceiris/actions-gh-pages for deployment."""
        assert "peaceiris/actions-gh-pages" in workflow_content, (
            "static.yml does not reference peaceiris/actions-gh-pages"
        )

    def test_workflow_triggers_on_push_to_main(self, workflow_content):
        """Workflow must trigger on push to the 'main' branch."""
        assert 'branches: ["main"]' in workflow_content, (
            'static.yml does not contain \'branches: ["main"]\' trigger'
        )

    def test_workflow_supports_workflow_dispatch(self, workflow_content):
        """Workflow must support manual triggering via workflow_dispatch."""
        assert "workflow_dispatch" in workflow_content, (
            "static.yml does not contain workflow_dispatch trigger"
        )
