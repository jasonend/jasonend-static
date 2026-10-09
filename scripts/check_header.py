"""Fail if the site header drifts between pages.

The header must be byte-identical across index/about/validated except for
aria-current="page", which belongs on the current page's nav link only
(index has none). Catches the old class of bug where a header/nav edit
was applied to only some pages.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ['index.html', 'about-jason/index.html', 'validated/index.html']
SELF = {'index.html': None, 'about-jason/index.html': '/about-jason/',
        'validated/index.html': '/validated/'}
errors = []


def header_of(rel: str) -> str:
    text = (ROOT / rel).read_text(encoding='utf-8')
    m = re.search(r'<header.*?</header>', text, flags=re.DOTALL)
    if not m:
        errors.append(f'{rel}: no <header> found')
        return ''
    return m.group(0)


def main() -> int:
    headers = {rel: header_of(rel) for rel in PAGES}
    normalized = {rel: re.sub(r' aria-current="page"', '', h) for rel, h in headers.items()}
    base = normalized[PAGES[0]]
    for rel in PAGES[1:]:
        if normalized[rel] != base:
            errors.append(f'{rel}: header differs from index.html beyond aria-current')
    for rel in PAGES:
        links = re.findall(r'<a href="([^"]+)"( aria-current="page")?>([^<]+)</a>',
                           re.search(r'<nav.*?</nav>', headers[rel], flags=re.DOTALL).group(0))
        hrefs = sorted(h for h, _, _ in links)
        if hrefs != ['/about-jason/', '/validated/']:
            errors.append(f'{rel}: nav links {hrefs}')
        current = [h for h, a, _ in links if a]
        want = [SELF[rel]] if SELF[rel] else []
        if current != want:
            errors.append(f'{rel}: aria-current on {current}, want {want}')
    if errors:
        print('\n'.join(errors))
        return 1
    print('OK: headers consistent across 3 pages')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
