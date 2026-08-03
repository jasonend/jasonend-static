"""
Property-based tests for the HTML cleaner (clean_html.py).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**
"""

import pathlib
import re
import tempfile

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from clean_html import PATTERNS, clean_file

# ---------------------------------------------------------------------------
# Canonical examples of each WordPress artifact element.
# These strings must match the PATTERNS defined in clean_html.py.
# ---------------------------------------------------------------------------

# (id, artifact_text) pairs – one per artifact type
ARTIFACT_EXAMPLES = [
    (
        "rss_feed",
        '<link rel="alternate" type="application/rss+xml" title="Site » Feed" href="/feed/">\n',
    ),
    (
        "comments_feed",
        '<link rel="alternate" type="application/rss+xml" title="Site » Comments Feed" href="/comments/feed/">\n',
    ),
    (
        "rsd",
        '<link rel="EditURI" type="application/rsd+xml" title="RSD" href="/xmlrpc.php?rsd">\n',
    ),
    (
        "wp_importmap",
        '<script id="wp-importmap" type="importmap">\n{"imports":{"@wordpress/interactivity":"/wp-includes/js/dist/script-modules/interactivity/index.min.js"}}\n</script>\n',
    ),
    (
        "modulepreload",
        '<link rel="modulepreload" href="/wp-includes/js/dist/script-modules/interactivity/index.min.js" id="@wordpress/interactivity-js-modulepreload" fetchpriority="low">\n',
    ),
    (
        "nav_view_module",
        '<script data-wp-router-options="{}" fetchpriority="low" id="@wordpress/block-library/navigation/view-js-module" src="/wp-includes/js/dist/script-modules/block-library/navigation/view.min.js" type="module"></script>\n',
    ),
    (
        "emoji_block",
        (
            '<script id="wp-emoji-settings" type="application/json">'
            '{"baseUrl":"https://s.w.org/images/core/emoji/17.0.0/72x72/"}'
            '</script>\n'
            '<script type="module">\n'
            'const x = 1;\n'
            '//# sourceURL=/wp-includes/js/wp-emoji-loader.min.js\n'
            '</script>\n'
        ),
    ),
]

# Just the artifact strings, for use in strategies
ARTIFACT_STRINGS = [text for _, text in ARTIFACT_EXAMPLES]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_and_clean(content: str) -> str:
    """Write content to a temp file, run clean_file(), return result."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        tmp_path = pathlib.Path(f.name)
    try:
        clean_file(tmp_path)
        return tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink(missing_ok=True)


def _is_artifact_present(text: str) -> bool:
    """Return True if any WordPress artifact pattern matches in text."""
    for pattern in PATTERNS:
        if re.search(pattern, text, flags=re.DOTALL):
            return True
    return False


def _remove_artifacts(text: str) -> str:
    """Apply all PATTERNS to text and return the cleaned string."""
    for pattern in PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    return text


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Strategy: pick a random non-empty subset of artifacts and join them
artifacts_strategy = st.lists(
    st.sampled_from(ARTIFACT_STRINGS),
    min_size=1,
    max_size=len(ARTIFACT_STRINGS),
).map("\n".join)

# Strategy: plain HTML-like text that contains none of the artifact patterns.
# We generate safe text by using printable ASCII minus characters that could
# accidentally create artifact snippets.  A short sentence is enough to check
# that non-artifact content is preserved.
safe_text_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("Lu", "Ll", "Nd", "Zs"),
        whitelist_characters="\n<>/=\" ",
    ),
    min_size=0,
    max_size=200,
).filter(lambda t: not _is_artifact_present(t))

# Full document strategy: surround a random set of artifacts with safe text
document_strategy = st.builds(
    lambda pre, artifacts, post: pre + artifacts + post,
    pre=safe_text_strategy,
    artifacts=artifacts_strategy,
    post=safe_text_strategy,
)

# Document that may or may not contain artifacts
any_document_strategy = st.builds(
    lambda pre, mid, post: pre + mid + post,
    pre=safe_text_strategy,
    mid=st.one_of(
        st.just(""),
        artifacts_strategy,
    ),
    post=safe_text_strategy,
)


# ---------------------------------------------------------------------------
# Property 1 – WordPress artifacts are stripped from all HTML pages
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9
# ---------------------------------------------------------------------------

@settings(max_examples=200)
@given(document_strategy)
def test_property1_artifacts_are_stripped(document: str):
    """**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**

    For any HTML document containing one or more WordPress artifact elements,
    none of those elements shall be present in the output after clean_file()
    runs.
    """
    cleaned = _write_and_clean(document)
    assert not _is_artifact_present(cleaned), (
        "Artifact pattern still matched in cleaned output.\n"
        f"Input snippet: {document[:300]!r}\n"
        f"Output snippet: {cleaned[:300]!r}"
    )


# ---------------------------------------------------------------------------
# Property 2 – HTML cleaning preserves non-artifact content
# Validates: Requirements 2.10
# ---------------------------------------------------------------------------

@settings(max_examples=200)
@given(any_document_strategy)
def test_property2_non_artifact_content_preserved(document: str):
    """**Validates: Requirements 2.10**

    For any HTML document, content that is not a WordPress artifact element
    shall be byte-for-byte identical in the cleaned output.
    """
    # Compute expected output by removing artifacts from the document
    expected = _remove_artifacts(document)
    actual = _write_and_clean(document)
    assert actual == expected, (
        "clean_file() altered non-artifact content.\n"
        f"Expected: {expected[:300]!r}\n"
        f"Actual:   {actual[:300]!r}"
    )


# ---------------------------------------------------------------------------
# Property 3 – HTML cleaner is idempotent
# Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.10
# ---------------------------------------------------------------------------

@settings(max_examples=200)
@given(any_document_strategy)
def test_property3_idempotent(document: str):
    """**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.10**

    Applying clean_file() twice shall produce the same result as applying it
    once.
    """
    once = _write_and_clean(document)
    twice = _write_and_clean(once)
    assert once == twice, (
        "clean_file() is not idempotent – second pass changed the output.\n"
        f"After 1st pass: {once[:300]!r}\n"
        f"After 2nd pass: {twice[:300]!r}"
    )


# ---------------------------------------------------------------------------
# Smoke tests – verify each canonical artifact is individually stripped
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("artifact_id,artifact_text", ARTIFACT_EXAMPLES)
def test_each_artifact_individually_stripped(artifact_id: str, artifact_text: str):
    """Each of the 7 canonical artifact types is removed when it appears alone."""
    document = f"<html>\n<head>\n{artifact_text}\n</head>\n<body>Hello</body>\n</html>\n"
    cleaned = _write_and_clean(document)
    assert artifact_text.strip() not in cleaned, (
        f"Artifact '{artifact_id}' was not stripped.\n"
        f"Cleaned output: {cleaned!r}"
    )
    assert "Hello" in cleaned, "Body content was unexpectedly removed."
