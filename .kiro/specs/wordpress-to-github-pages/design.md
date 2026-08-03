# Design Document

## Overview

This document describes the technical design for converting the WordPress Simply Static export at the repository root into a clean, deployable GitHub Pages static site. The conversion is a one-time preparation task followed by an automated deployment pipeline.

The work divides into four discrete operations:

1. **Directory removal** — delete `wp-content/plugins/` and `author/jasonend/`
2. **HTML cleaning** — strip WordPress-specific `<link>` and `<script>` elements from the three retained HTML pages
3. **Configuration files** — create `.nojekyll` and `CNAME` at the repository root
4. **Workflow replacement** — rewrite `.github/workflows/static.yml` to use `peaceiris/actions-gh-pages`

There is no build step, no URL rewriting, and no dependency installation. All paths in the HTML are already root-relative and will resolve correctly on GitHub Pages.

---

## Architecture

```
Repository root (main branch)
├── index.html                    ← cleaned
├── about-jason/index.html        ← cleaned
├── validated/index.html          ← cleaned
├── .nojekyll                     ← created
├── CNAME                         ← created (jasonend.cloud)
├── .github/workflows/static.yml  ← replaced
├── wp-content/
│   ├── themes/twentytwentyfour/  ← retained as-is
│   └── uploads/2026/05/          ← retained as-is (189 files)
│
├── wp-content/plugins/           ← deleted entirely
└── author/jasonend/              ← deleted entirely
```

On push to `main`, the GitHub Actions workflow runs `peaceiris/actions-gh-pages`, which force-pushes the repository contents (minus `.git`) to the `gh-pages` branch. GitHub Pages serves the `gh-pages` branch under `jasonend.cloud`. A second repository serves the same content under `theenderles.com` via its own `CNAME` file.

### Data Flow

```
git push → main branch
    │
    └─► GitHub Actions: static.yml
            │
            ├─ actions/checkout@v4
            │       └─ checks out full repository to runner
            │
            └─ peaceiris/actions-gh-pages@v3
                    ├─ copies publish_dir (.) to temp directory
                    ├─ writes CNAME file (jasonend.cloud)
                    ├─ writes .nojekyll file
                    └─ force-pushes to gh-pages branch
                            │
                            └─► GitHub Pages CDN
                                    ├─ serves https://jasonend.cloud/
                                    ├─ serves https://jasonend.cloud/about-jason/
                                    └─ serves https://jasonend.cloud/validated/
```

---

## Components and Interfaces

### 1. Directory Removal

A direct `git rm -r` operation on two paths:

```bash
git rm -r wp-content/plugins/
git rm -r author/jasonend/
```

No logic is involved. The directories and all their descendants are removed from the Git index and the working tree.

### 2. HTML Cleaner

The HTML cleaner is a Python script (`clean_html.py`) that operates on each of the three HTML files. Python's `re` module (stdlib) is sufficient to locate and remove the target elements without introducing external dependencies.

#### Target elements

Each of the following elements is removed from every processed HTML page:

| ID / pattern | Element type | Attribute to match |
|---|---|---|
| RSS feed link | `<link rel="alternate" type="application/rss+xml">` | `href="/feed/"` |
| Comments RSS link | `<link rel="alternate" type="application/rss+xml">` | `href="/comments/feed/"` |
| RSD link | `<link rel="EditURI" type="application/rsd+xml">` | `href` starts with `/xmlrpc.php` |
| Import map | `<script id="wp-importmap" type="importmap">` | `id="wp-importmap"` |
| Modulepreload | `<link rel="modulepreload">` | `id="@wordpress/interactivity-js-modulepreload"` |
| Navigation view module | `<script>` | `id="@wordpress/block-library/navigation/view-js-module"` |
| Emoji settings | `<script id="wp-emoji-settings" type="application/json">` | `id="wp-emoji-settings"` |
| Emoji loader | `<script type="module">` | immediately follows wp-emoji-settings; source comment `/wp-includes/js/wp-emoji-loader.min.js` |

#### Approach: regex-based removal

The HTML files are large but structurally predictable — all WordPress-generated. The target elements each appear with stable, unique identifiers. A regex-based removal approach is simpler and safer than an HTML-parser approach here, because reconstructing the file from a parse tree risks altering whitespace and inline `<style>` blocks.

The cleaner reads each file as a string and applies a sequence of targeted `re.sub()` calls:

```python
import re, pathlib

PATTERNS = [
    # RSS feed link
    r'<link rel="alternate" type="application/rss\+xml"[^>]*href="/feed/"[^>]*>\n?',
    # Comments RSS feed link
    r'<link rel="alternate" type="application/rss\+xml"[^>]*href="/comments/feed/"[^>]*>\n?',
    # RSD link
    r'<link rel="EditURI"[^>]*href="/xmlrpc\.php[^"]*"[^>]*>\n?',
    # wp-importmap script block (multi-line)
    r'<script id="wp-importmap"[^>]*>.*?</script>\n?',
    # modulepreload link
    r'<link rel="modulepreload"[^>]*id="@wordpress/interactivity-js-modulepreload"[^>]*>\n?',
    # navigation view module script
    r'<script[^>]*id="@wordpress/block-library/navigation/view-js-module"[^>]*></script>\n?',
    # wp-emoji-settings block + immediately following emoji loader script
    r'<script id="wp-emoji-settings"[^>]*>.*?</script>\s*<script type="module">\s*.*?//# sourceURL=/wp-includes/js/wp-emoji-loader\.min\.js\s*</script>\n?',
]

def clean_file(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in PATTERNS:
        text = re.sub(pattern, "", text, flags=re.DOTALL)
    path.write_text(text, encoding="utf-8")

for html_file in [
    pathlib.Path("index.html"),
    pathlib.Path("about-jason/index.html"),
    pathlib.Path("validated/index.html"),
]:
    clean_file(html_file)
```

Each pattern uses `re.DOTALL` for multi-line script blocks. Single-line `<link>` tags use `[^>]*` to match attributes in any order. The emoji block pattern matches the `wp-emoji-settings` script and the immediately following inline `<script type="module">` loader as a unit, identified by the trailing source comment.

### 3. Configuration Files

**`.nojekyll`** — empty file placed at repository root. GitHub Pages detects presence, not content.

**`CNAME`** — plain-text file at repository root containing exactly:
```
jasonend.cloud
```

No trailing whitespace beyond a single newline. GitHub Pages reads this file on the `gh-pages` branch to bind the custom domain.

### 4. GitHub Actions Workflow

The existing `static.yml` uses the artifact-upload mechanism (`actions/upload-pages-artifact` + `actions/deploy-pages`). This is replaced with `peaceiris/actions-gh-pages@v3`, which force-pushes directly to the `gh-pages` branch.

**Replacement `static.yml`:**

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: ["main"]
  workflow_dispatch:

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy to gh-pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: .
          publish_branch: gh-pages
          cname: jasonend.cloud
```

Key decisions:
- `publish_dir: .` — deploy the entire repository root; no build step needed.
- `cname: jasonend.cloud` — `peaceiris/actions-gh-pages` writes the `CNAME` file into the `gh-pages` branch automatically, so the custom domain binding survives every deployment.
- `permissions: contents: write` — required for pushing to `gh-pages` branch. The old `pages: write` / `id-token: write` permissions for the artifact mechanism are no longer needed.
- `peaceiris/actions-gh-pages` also writes its own `.nojekyll` to the `gh-pages` branch by default, complementing the `.nojekyll` file tracked in the repository.
- On deploy failure the action exits non-zero, failing the workflow job and marking the run failed in the GitHub Actions UI.

### 5. Secondary Domain (theenderles.com)

The secondary domain requires the same site content served under a different CNAME. Recommended approach:

**Separate repository** — create a second GitHub repository containing the same content. Replace the `CNAME` file content with `theenderles.com`. Use the same `static.yml` workflow with `cname: theenderles.com`. Configure the `theenderles.com` DNS CNAME record to point to `<user>.github.io`.

This keeps the two deployments independent and avoids cross-repo authentication complexity. Both repositories are kept in sync manually or by pushing to both remotes from the same local clone.

---

## Data Models

This project contains no application data models — it is a static file repository. The relevant "data" are the file system artifacts and the YAML workflow configuration.

### Repository artifact inventory

| Path | Type | Disposition |
|---|---|---|
| `index.html` | HTML page | Retained, cleaned |
| `about-jason/index.html` | HTML page | Retained, cleaned |
| `validated/index.html` | HTML page | Retained, cleaned |
| `wp-content/uploads/2026/05/*.{jpg,png,pdf,jpeg}` | Media (189 files) | Retained as-is |
| `wp-content/themes/twentytwentyfour/**` | Theme assets | Retained as-is |
| `wp-content/plugins/**` | Plugin assets | Deleted |
| `author/jasonend/index.html` | Author archive | Deleted |
| `.nojekyll` | GH Pages control | Created (empty) |
| `CNAME` | GH Pages control | Created (`jasonend.cloud`) |
| `.github/workflows/static.yml` | CI/CD workflow | Replaced |

### Workflow YAML structure

```
static.yml
├── on.push.branches: ["main"]
├── on.workflow_dispatch
├── permissions.contents: write
└── jobs.deploy
    ├── runs-on: ubuntu-latest
    ├── steps[0]: actions/checkout@v4
    └── steps[1]: peaceiris/actions-gh-pages@v3
        ├── github_token: ${{ secrets.GITHUB_TOKEN }}
        ├── publish_dir: .
        ├── publish_branch: gh-pages
        └── cname: jasonend.cloud
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Workflow push fails (permissions, token) | Job exits non-zero; GitHub marks run failed; `gh-pages` branch unchanged |
| `gh-pages` branch conflict | `peaceiris/actions-gh-pages` uses force-push; conflicts cannot occur |
| HTML file missing during clean | `clean_file()` raises `FileNotFoundError`; script exits non-zero; commit not made |
| Regex matches nothing | `re.sub()` returns string unchanged; no error; file written back unchanged |
| CNAME DNS not configured | Site deploys but unreachable at custom domain; `<user>.github.io` fallback still works |
| `theenderles.com` second repo not created | Primary domain unaffected; only secondary domain is unavailable |

---

## Execution Order

The one-time preparation steps must be executed in this order before the first deployment:

1. Run `python clean_html.py` (modifies the three HTML files in-place)
2. Create `.nojekyll` at repository root (empty file)
3. Create `CNAME` at repository root containing `jasonend.cloud`
4. Delete `wp-content/plugins/` with `git rm -r wp-content/plugins/`
5. Delete `author/jasonend/` with `git rm -r author/jasonend/`
6. Replace `.github/workflows/static.yml` with the new workflow
7. `git add -A && git commit -m "Convert to GitHub Pages static site"`
8. `git push origin main`

After step 8, the workflow fires automatically and the `gh-pages` branch is created or updated.

---

## Testing Strategy

### Unit tests (example-based)

- Assert `CNAME` file exists and contains exactly `jasonend.cloud`
- Assert `.nojekyll` file exists at repository root
- Assert `wp-content/plugins/` directory does not exist
- Assert `author/jasonend/` directory does not exist
- Assert each of the three HTML files exists after cleaning
- Assert the workflow YAML triggers include `push: branches: ["main"]` and `workflow_dispatch`
- Assert the workflow YAML references `peaceiris/actions-gh-pages`

### Property tests

See Correctness Properties section below.

### Integration tests (post-deployment)

- HTTP GET `https://jasonend.cloud/` → status 200
- HTTP GET `https://jasonend.cloud/about-jason/` → status 200
- HTTP GET `https://jasonend.cloud/validated/` → status 200
- HTTP GET `https://jasonend.cloud/wp-content/uploads/2026/05/jasonend_cloud_logo.png` → status 200
- HTTP GET `https://jasonend.cloud/wp-content/plugins/akismet/_inc/akismet.js` → status 404
- HTTP GET `https://jasonend.cloud/author/jasonend/` → status 404

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: WordPress artifacts are stripped from all HTML pages

*For any* HTML document that contains one or more WordPress artifact elements (RSS feed links, RSD link, wp-importmap script, modulepreload link, navigation view module script, wp-emoji-settings block, emoji loader script), after the cleaner processes the document, none of those artifact elements shall be present in the output.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**

### Property 2: HTML cleaning preserves non-artifact content

*For any* HTML document, any content that is not a WordPress artifact element shall be byte-for-byte identical in the cleaned output as it was in the original input. The cleaner shall not alter, reorder, or remove content outside the defined removal targets.

**Validates: Requirements 2.10**

### Property 3: HTML cleaner is idempotent

*For any* HTML document, applying the cleaner twice shall produce the same result as applying it once. If a document is already free of WordPress artifact elements, the cleaner's output shall be identical to its input.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.10**
