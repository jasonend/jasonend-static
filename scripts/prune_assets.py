"""Prune unreferenced files under wp-content/uploads/.

Evidence-based: a file is kept iff its site-absolute URL path appears
in any *.html page (including srcset). Everything else is dead weight
from the WordPress export (e.g. PDF JPG previews, unused thumbnails).

Usage:
    python3 scripts/prune_assets.py [--check] [--delete]

--check  exits non-zero if dead weight exists (for CI).
--delete deletes unreferenced files.
Default (no flags) lists unreferenced files + total size.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "wp-content" / "uploads"
PATTERN = r'/wp-content/uploads/[^\s"\')(),]+'


def collect_refs() -> set:
    html_files = list(ROOT.glob('*.html')) + list(ROOT.glob('*/*.html'))
    text = '\n'.join(p.read_text(encoding='utf-8') for p in html_files)
    return set(re.findall(PATTERN, text))


def unreferenced() -> list:
    refs = collect_refs()
    dead = []
    for f in sorted(UPLOADS.rglob('*')):
        if f.is_file():
            url = '/' + f.relative_to(ROOT).as_posix()
            if url not in refs:
                dead.append(f)
    return dead


def main() -> int:
    dead = unreferenced()
    total = sum(f.stat().st_size for f in dead)
    if '--delete' in sys.argv:
        for f in dead:
            f.unlink()
        print(f'Deleted {len(dead)} files, freed {total / 1e6:.1f} MB')
        return 0
    for f in dead:
        print('/' + f.relative_to(ROOT).as_posix())
    print(f'---\n{len(dead)} unreferenced files, {total / 1e6:.1f} MB', file=sys.stderr)
    if '--check' in sys.argv and dead:
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
