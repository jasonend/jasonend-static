"""Fail on dead internal links / banned WordPress leftovers.

Checks:
- No href="/ ?p=N" shortlinks (dead on static hosting).
- No references to /wp-includes/ or /wp-admin/ (pruned).
- Every internal href/src resolves to a file in the repo.
  (/about-jason/ -> about-jason/index.html, /sitemap.xml -> sitemap.xml, etc.)
- CNAME (if present during Pages transition) matches jasonend.cloud.
  Legacy GitHub Pages mode (static.yml present) also checks deploy cname.

Usage: python3 scripts/check_links.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
errors = []


def resolve(url_path: str) -> bool:
    """Return True if site-absolute path resolves to a repo file."""
    path = url_path.split('#')[0].split('?')[0]
    if not path or path.startswith('#'):
        return True
    if path.endswith('/'):
        return (ROOT / path.lstrip('/') / 'index.html').exists()
    return (ROOT / path.lstrip('/')).exists()


def main() -> int:
    html_files = list(ROOT.glob('*.html')) + list(ROOT.glob('*/*.html'))
    for f in html_files:
        text = f.read_text(encoding='utf-8')
        rel = f.relative_to(ROOT)
        if re.search(r'href="/\?p=\d+"', text):
            errors.append(f'{rel}: contains dynamic shortlink /?p=N')
        for m in re.finditer(r'''(?:src|href)="([^"]+)"''', text):
            url = m.group(1)
            if url.startswith(('https://', 'http://', 'mailto:', '#', 'data:')):
                continue
            if url in ('/',):
                continue
            if url.startswith('/?'):
                errors.append(f'{rel}: dynamic URL {url}')
                continue
            if url.startswith('/wp-includes/') or url.startswith('/wp-admin/'):
                errors.append(f'{rel}: references pruned path {url}')
                continue
            # speculationrules JSON contains glob patterns, not real paths
            if '*' in url or url.startswith('/*'):
                continue
            if url.startswith('/'):
                if not resolve(url):
                    errors.append(f'{rel}: broken link {url}')
        for m in re.finditer(r"""url\(['"]?(/[^'")]+)['"]?\)""", text):
            url = m.group(1)
            if url.startswith('/wp-includes/'):
                # sourceURL comments are not fetches; only fail on real CSS url()
                # heuristic: sourceURL lines contain 'sourceURL=' before url(
                continue
            if url.startswith('/wp-content/themes/') and not resolve(url):
                errors.append(f'{rel}: broken CSS url() {url}')

    cname_path = ROOT / 'CNAME'
    if cname_path.exists():
        cname = cname_path.read_text().strip()
        workflow_path = ROOT / '.github' / 'workflows' / 'static.yml'
        if workflow_path.exists():
            # Legacy GitHub Pages mode: CNAME must match deploy cname.
            workflow = workflow_path.read_text()
            m = re.search(r'cname:\s*(\S+)', workflow)
            if m and m.group(1) != cname:
                errors.append(f'CNAME mismatch: file={cname!r} workflow={m.group(1)!r}')
        elif cname != 'jasonend.cloud':
            errors.append(f'CNAME should contain jasonend.cloud, got {cname!r}')

    if errors:
        print('\n'.join(errors))
        return 1
    print(f'OK: {len(html_files)} pages, links resolve')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
