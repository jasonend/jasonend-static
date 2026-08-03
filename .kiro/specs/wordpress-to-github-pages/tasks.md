# Implementation Plan: WordPress to GitHub Pages

## Overview

Convert the WordPress Simply Static export into a deployable GitHub Pages site by removing unused directories, cleaning HTML files of WordPress artifacts, adding GitHub Pages configuration files, and replacing the CI/CD workflow. A property-based test suite validates the HTML cleaner's correctness before everything is committed and pushed.

## Tasks

- [x] 1. Write the HTML cleaner script
  - [x] 1.1 Create `clean_html.py` at repository root
    - Implement `PATTERNS` list with all 8 regex patterns from the design (RSS feed, comments RSS, RSD, wp-importmap, modulepreload, navigation view module, emoji settings + loader)
    - Implement `clean_file(path)` function using `re.sub()` with `re.DOTALL`
    - Implement main block that calls `clean_file` on `index.html`, `about-jason/index.html`, and `validated/index.html`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x]* 1.2 Write property tests for the HTML cleaner
    - Use `hypothesis` library to generate HTML strings that may contain any subset of the 8 WordPress artifact elements (fabricated but structurally valid)
    - **Property 1: WordPress artifacts are stripped from all HTML pages** — for any generated document containing artifact elements, assert none are present after `clean_file()` runs
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**
    - **Property 2: HTML cleaning preserves non-artifact content** — for any generated document, assert that all non-artifact content is byte-for-byte identical in the cleaned output
    - **Validates: Requirements 2.10**
    - **Property 3: HTML cleaner is idempotent** — for any generated document, assert that `clean_file()` applied twice equals `clean_file()` applied once
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.10**
    - Write tests in `test_clean_html.py` at repository root; run with `python -m pytest test_clean_html.py`

- [x] 2. Checkpoint — ensure property tests pass
  - Run `python -m pytest test_clean_html.py` and confirm all properties pass. Ask the user if questions arise before continuing.

- [x] 3. Run the HTML cleaner and create configuration files
  - [x] 3.1 Run `clean_html.py` against the three HTML files
    - Execute `python clean_html.py` at repository root
    - Verify `index.html`, `about-jason/index.html`, and `validated/index.html` are modified in-place
    - _Requirements: 2.1–2.10_

  - [x] 3.2 Create `.nojekyll` at repository root
    - Create an empty file named `.nojekyll` at the repository root (no content required)
    - _Requirements: 3.1, 3.4_

  - [x] 3.3 Create `CNAME` at repository root
    - Create a file named `CNAME` containing exactly the line `jasonend.cloud` (single newline, no trailing whitespace)
    - _Requirements: 3.2, 3.3_

- [x] 4. Remove unwanted directories
  - [x] 4.1 Delete `wp-content/plugins/` from the Git index
    - Run `git rm -r wp-content/plugins/` to stage the removal of all plugin subdirectories (akismet, jwt-authentication-for-wp-rest-api, simply-static)
    - _Requirements: 1.1, 1.3_

  - [x] 4.2 Delete `author/jasonend/` from the Git index
    - Run `git rm -r author/jasonend/` to stage the removal of the author archive directory and its `index.html`
    - _Requirements: 1.2, 1.3_

- [x] 5. Replace the GitHub Actions deployment workflow
  - [x] 5.1 Overwrite `.github/workflows/static.yml` with the `peaceiris/actions-gh-pages` workflow
    - Replace the entire file content with the workflow defined in the design:
      - trigger: `push` to `main` and `workflow_dispatch`
      - `permissions: contents: write`
      - `actions/checkout@v4` step
      - `peaceiris/actions-gh-pages@v3` step with `publish_dir: .`, `publish_branch: gh-pages`, `cname: jasonend.cloud`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

- [x] 6. Write unit tests for repository state
  - [x]* 6.1 Write unit tests validating the prepared repository state
    - Write `test_repo_state.py` at repository root using Python's `unittest` or `pytest`
    - Assert `CNAME` exists and contains exactly `jasonend.cloud`
    - Assert `.nojekyll` exists at repository root
    - Assert `wp-content/plugins/` directory does not exist
    - Assert `author/jasonend/` directory does not exist
    - Assert `index.html`, `about-jason/index.html`, and `validated/index.html` all exist
    - Assert `.github/workflows/static.yml` contains `peaceiris/actions-gh-pages` and triggers on `push: branches: ["main"]` and `workflow_dispatch`
    - _Requirements: 1.1, 1.2, 3.1, 3.2, 4.1, 4.2, 6.3_

- [x] 7. Checkpoint — verify repository state
  - Run `python -m pytest test_repo_state.py` and confirm all unit tests pass. Ask the user if questions arise before continuing.

- [ ] 8. Commit and push to trigger deployment
  - [-] 8.1 Stage all changes and create the migration commit
    - Run `git add -A` to stage all deletions, modifications, and new files
    - Run `git commit -m "Convert to GitHub Pages static site"` to create the migration commit
    - _Requirements: 4.7_

  - [~] 8.2 Push `main` to trigger the GitHub Actions workflow
    - Run `git push origin main`
    - Confirm the workflow fires in the GitHub Actions tab and the `gh-pages` branch is created or updated
    - _Requirements: 4.1, 4.4_

- [ ] 9. Set up secondary domain (theenderles.com)
  - [~] 9.1 Create a second GitHub repository with the same content
    - Initialize a new local directory, copy all retained files from the primary repository (exclude `.git`)
    - Replace the `CNAME` file content with `theenderles.com`
    - Update `.github/workflows/static.yml` to set `cname: theenderles.com`
    - _Requirements: 5.2, 5.3_

  - [~] 9.2 Push the secondary repository and configure DNS
    - Push the secondary repository to a new GitHub remote
    - Configure the `theenderles.com` DNS CNAME record to point to `<user>.github.io`
    - Confirm the secondary workflow fires and the site is reachable at `https://theenderles.com`
    - _Requirements: 5.2, 5.3, 5.4_

- [~] 10. Final checkpoint — confirm both domains are live
  - Ensure all tests pass and both domains serve the expected content. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster run
- `clean_html.py` must be run (task 3.1) before committing — it modifies files in-place
- The `hypothesis` library is required for property tests; install with `pip install hypothesis pytest`
- Property tests operate on synthesized HTML strings, not the actual files, so they can run before the cleaner is executed
- Checkpoints at tasks 2, 7, and 10 ensure incremental validation at natural break points
- The secondary domain setup (task 9) is independent of all prior tasks and can be done any time after the primary deployment succeeds

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["3.1", "3.2", "3.3"] },
    { "id": 3, "tasks": ["4.1", "4.2", "5.1"] },
    { "id": 4, "tasks": ["6.1"] },
    { "id": 5, "tasks": ["8.1"] },
    { "id": 6, "tasks": ["8.2", "9.1"] },
    { "id": 7, "tasks": ["9.2"] }
  ]
}
```
