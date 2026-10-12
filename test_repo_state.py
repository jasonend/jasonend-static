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
# Requirements 4.1, 4.2 – Cloudflare Pages hosting (no GitHub Pages deploy)
# ---------------------------------------------------------------------------

class TestPagesHosting:
    """Validates: Requirements 4.1, 4.2 (Cloudflare Pages, Git-connected)."""

    def test_legacy_gh_pages_workflow_removed(self):
        """static.yml (peaceiris gh-pages deploy) must not exist."""
        workflow_path = REPO_ROOT / ".github" / "workflows" / "static.yml"
        assert not workflow_path.exists(), (
            ".github/workflows/static.yml should be deleted after Pages move"
        )

    def test_ci_workflow_retained(self):
        """test.yml CI must still exist."""
        assert (REPO_ROOT / ".github" / "workflows" / "test.yml").exists(), (
            ".github/workflows/test.yml is missing"
        )

    def test_pages_headers_exists(self):
        """_headers must exist at output root for Cloudflare Pages."""
        assert (REPO_ROOT / "_headers").exists(), "_headers file does not exist"

    def test_pages_redirects_exists(self):
        """_redirects must exist at output root for www -> apex."""
        content = (REPO_ROOT / "_redirects").read_text()
        assert "www.jasonend.cloud" in content and "jasonend.cloud" in content, (
            "_redirects should map www to apex"
        )
