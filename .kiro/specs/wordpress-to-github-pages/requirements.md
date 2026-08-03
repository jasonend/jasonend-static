# Requirements Document

## Introduction

This feature converts an existing WordPress Simply Static export located at the repository root into a clean, deployable GitHub Pages static site. The export contains 4 HTML pages, 189 media files, and theme assets from the TwentyTwentyFour theme. The conversion involves removing WordPress-specific artifacts (plugin directories, author page, broken server-side references in HTML), adding GitHub Pages configuration files, and replacing the existing GitHub Actions workflow with one that deploys to the `gh-pages` branch. The site will be served under two custom domains: `jasonend.cloud` (primary) and `theenderles.com` (secondary).

## Glossary

- **Export Root**: The repository directory at `/Users/jenderle/Downloads/simply-static-1-1785522833/`, which is also the repository root used for GitHub Pages deployment.
- **HTML Pages**: The three retained HTML files: `index.html`, `about-jason/index.html`, and `validated/index.html`.
- **Broken WordPress References**: HTML elements that reference WordPress server-side endpoints or unavailable JS modules that have no function in a static context: RSS feed `<link>` tags (`/feed/`, `/comments/feed/`), the RSD `<link>` tag pointing to `/xmlrpc.php?rsd`, the `wp-importmap` `<script>` block containing the `@wordpress/interactivity` import map, the `<link rel="modulepreload">` tag for `@wordpress/interactivity`, the navigation view module `<script>` tag with `id="@wordpress/block-library/navigation/view-js-module"`, and the emoji block consisting of the `<script id="wp-emoji-settings">` JSON block plus the immediately following inline `<script type="module">` emoji loader script.
- **Plugin Directory**: `wp-content/plugins/` and all of its contents (akismet, jwt-authentication-for-wp-rest-api, simply-static subdirectories).
- **Author Page**: The directory `author/jasonend/` and its `index.html`.
- **CNAME File**: A plain-text file named `CNAME` at the repository root containing a single domain name, used by GitHub Pages to serve the site under a custom domain.
- **Nojekyll File**: A file named `.nojekyll` at the repository root that instructs GitHub Pages to bypass Jekyll processing.
- **gh-pages Branch**: The Git branch used as the GitHub Pages publishing source.
- **Deployment Workflow**: The GitHub Actions YAML file at `.github/workflows/static.yml` that automates publishing to the `gh-pages` branch.
- **Primary Domain**: `jasonend.cloud` — the domain whose repository holds the CNAME file and serves as the canonical GitHub Pages source.
- **Secondary Domain**: `theenderles.com` — a second custom domain served from a separate deployment or repository.

---

## Requirements

### Requirement 1: Remove Unwanted Directories

**User Story:** As a site owner, I want plugin files and the author archive page removed from the repository, so that the deployed site does not serve irrelevant or potentially sensitive WordPress plugin assets.

#### Acceptance Criteria

1. THE Deployment Operator SHALL delete the `wp-content/plugins/` directory and all of its contents from the repository.
2. THE Deployment Operator SHALL delete the `author/jasonend/` directory and its `index.html` from the repository.
3. WHEN a browser requests any path that previously resolved to a deleted file, THE GitHub Pages Server SHALL return a 404 response because no corresponding file exists on the `gh-pages` branch.

---

### Requirement 2: Strip Broken WordPress References from HTML Pages

**User Story:** As a site visitor, I want the HTML pages to load without console errors or failed network requests caused by WordPress-only endpoints, so that the pages render cleanly in a static hosting environment.

#### Acceptance Criteria

1. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<link rel="alternate" type="application/rss+xml">` element whose `href` is `/feed/`.
2. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<link rel="alternate" type="application/rss+xml">` element whose `href` is `/comments/feed/`.
3. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<link rel="EditURI" type="application/rsd+xml">` element whose `href` begins with `/xmlrpc.php`.
4. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<script id="wp-importmap" type="importmap">` block that declares the `@wordpress/interactivity` import map.
5. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<link rel="modulepreload">` element whose `id` is `@wordpress/interactivity-js-modulepreload`.
6. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<script>` element whose `id` is `@wordpress/block-library/navigation/view-js-module`.
7. WHEN the HTML Cleaner processes `index.html`, THE HTML Cleaner SHALL remove the `<script id="wp-emoji-settings" type="application/json">` block together with the immediately following inline `<script type="module">` emoji loader script (the block whose source URL comment is `/wp-includes/js/wp-emoji-loader.min.js`).
8. THE HTML Cleaner SHALL apply acceptance criteria 1 through 7 identically to `about-jason/index.html`.
9. THE HTML Cleaner SHALL apply acceptance criteria 1 through 7 identically to `validated/index.html`.
10. WHEN the HTML Cleaner finishes processing a page, THE HTML Cleaner SHALL preserve all other HTML content in the page without modification.

---

### Requirement 3: Add GitHub Pages Configuration Files

**User Story:** As a site owner, I want the repository to include the necessary GitHub Pages control files, so that GitHub Pages serves the site correctly under the custom primary domain without Jekyll interference.

#### Acceptance Criteria

1. THE Deployment Operator SHALL create a file named `.nojekyll` at the repository root containing no content (empty file or a single newline).
2. THE Deployment Operator SHALL create a file named `CNAME` at the repository root containing the single line `jasonend.cloud` with no additional content.
3. WHEN GitHub Pages reads the `CNAME` file on the `gh-pages` branch, THE GitHub Pages Server SHALL serve the site at `https://jasonend.cloud`.
4. WHILE the `.nojekyll` file is present on the `gh-pages` branch, THE GitHub Pages Server SHALL bypass Jekyll build processing and serve files as-is.

---

### Requirement 4: Replace GitHub Actions Deployment Workflow

**User Story:** As a site owner, I want a GitHub Actions workflow that deploys the repository content to the `gh-pages` branch on every push to `main`, so that the live site updates automatically whenever changes are committed.

#### Acceptance Criteria

1. THE Deployment Workflow SHALL trigger on every push to the `main` branch.
2. THE Deployment Workflow SHALL support manual triggering via `workflow_dispatch`.
3. WHEN the Deployment Workflow runs, THE Deployment Workflow SHALL check out the full repository contents using `actions/checkout`.
4. WHEN the Deployment Workflow runs, THE Deployment Workflow SHALL publish the repository contents to the `gh-pages` branch using a dedicated GitHub Pages deployment action (such as `peaceiris/actions-gh-pages` or equivalent).
5. WHEN the Deployment Workflow publishes to the `gh-pages` branch, THE Deployment Workflow SHALL include the `CNAME` file so the custom domain binding is preserved after each deployment.
6. WHEN the Deployment Workflow publishes to the `gh-pages` branch, THE Deployment Workflow SHALL include the `.nojekyll` file so Jekyll processing remains disabled after each deployment.
7. THE Deployment Workflow SHALL replace the existing `static.yml` workflow that deploys via the GitHub Pages artifact upload mechanism.
8. IF the Deployment Workflow job fails, THEN THE Deployment Workflow SHALL exit with a non-zero status code so the failure is visible in the GitHub Actions run log.

---

### Requirement 5: Dual-Domain Availability

**User Story:** As a site owner, I want the site content available under both `jasonend.cloud` and `theenderles.com`, so that visitors reaching either domain see the same site.

#### Acceptance Criteria

1. THE Deployment Operator SHALL configure the primary repository's GitHub Pages to use `jasonend.cloud` as the custom domain, served via the `CNAME` file on the `gh-pages` branch.
2. WHERE a secondary domain deployment is used, THE Deployment Operator SHALL deploy the same repository content to a second GitHub Pages site (separate repository or a second deployment target) with a `CNAME` file containing `theenderles.com`.
3. WHEN a browser navigates to `https://theenderles.com`, THE GitHub Pages Server for the secondary domain SHALL serve the same HTML pages and assets as the primary domain.
4. THE Deployment Operator SHALL configure DNS CNAME or ALIAS records for both `jasonend.cloud` and `theenderles.com` to point to their respective GitHub Pages endpoints.

---

### Requirement 6: Retain Required Content

**User Story:** As a site owner, I want all media uploads, theme assets, and the three retained HTML pages to remain intact in the repository, so that the deployed site displays all intended content and styles.

#### Acceptance Criteria

1. THE Deployment Operator SHALL retain all 189 files under `wp-content/uploads/2026/05/` without modification.
2. THE Deployment Operator SHALL retain all files under `wp-content/themes/twentytwentyfour/` without modification.
3. THE Deployment Operator SHALL retain `index.html`, `about-jason/index.html`, and `validated/index.html` (after HTML cleaning per Requirement 2).
4. WHEN a browser requests a retained media file path, THE GitHub Pages Server SHALL return the file with HTTP status 200.
5. WHEN a browser requests a retained theme asset path, THE GitHub Pages Server SHALL return the file with HTTP status 200.
