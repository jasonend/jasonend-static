import re
import pathlib

PATTERNS = [
    # RSS feed link (Requirements 2.1)
    r'<link rel="alternate" type="application/rss\+xml"[^>]*href="/feed/"[^>]*>\n?',
    # Comments RSS feed link (Requirements 2.2)
    r'<link rel="alternate" type="application/rss\+xml"[^>]*href="/comments/feed/"[^>]*>\n?',
    # RSD link (Requirements 2.3)
    r'<link rel="EditURI"[^>]*href="/xmlrpc\.php[^"]*"[^>]*>\n?',
    # wp-importmap script block (multi-line) (Requirements 2.4)
    r'<script id="wp-importmap"[^>]*>.*?</script>\n?',
    # modulepreload link (Requirements 2.5)
    r'<link rel="modulepreload"[^>]*id="@wordpress/interactivity-js-modulepreload"[^>]*>\n?',
    # navigation view module script (Requirements 2.6)
    r'<script[^>]*id="@wordpress/block-library/navigation/view-js-module"[^>]*></script>\n?',
    # wp-emoji-settings block + immediately following emoji loader script (Requirements 2.7)
    r'<script id="wp-emoji-settings"[^>]*>.*?</script>\s*<script type="module">\s*.*?//# sourceURL=/wp-includes/js/wp-emoji-loader\.min\.js\s*</script>\n?',
]


def clean_file(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    for html_file in [
        pathlib.Path("index.html"),
        pathlib.Path("about-jason/index.html"),
        pathlib.Path("validated/index.html"),
    ]:
        clean_file(html_file)
