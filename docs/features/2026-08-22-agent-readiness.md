# Feature: Agent-readable landing page — `<main>`, Markdown twin, llms.txt links

**Branch:** feat/agent-readiness
**Date:** 2026-08-22

## Summary
Makes `docs/index.html` (the GitHub Pages landing page at https://tatendaz.github.io/claude-usage/)
readable for AI agents the same way the root site is: the page content sits inside `<main>`,
a Markdown twin lives at `docs/index.md`, and the page advertises it with
`<link rel="alternate" type="text/markdown" href="/claude-usage/index.md">` plus
`<link rel="describedby" href="/llms.txt">`. Nothing visible changes apart from llms.txt and a "More work" link to the root site
in the footer. A custom `docs/404.html` replaces GitHub's default 404 page for missing paths
under `/claude-usage/`.

## Motivation
An Is Agentic audit of tatendaz.github.io (2026-08-22) showed the scanner counts text and the
H1 only inside `<main>`. This page had no `<main>`, so its 4,000+ characters of static text and
its H1 did not count. The root site's `llms.txt` (Tatendaz/Tatendaz.github.io PR #8) lists
this page; the page now points back at it and ships the Markdown twin that the
[llmstxt.org](https://llmstxt.org/) spec recommends (`index.md` next to `index.html`,
`rel="alternate"` to the twin, `rel="describedby"` to the covering `llms.txt`).

## What changed
- `docs/index.html`: `<main>` wraps the hero and every content section (the footer stays
  outside). The hero was a `<header>`; it is now `<div class="hero">` (CSS selector renamed,
  same rules) because boilerplate-stripping extractors drop `<header>` elements and would
  lose the H1 with it. The two `<link>` tags sit after the canonical; the footer gains llms.txt and a "More work" link to the root site.
  CSS: selector-only change (the one `header` rule is now `.hero`, same declarations); no layout
  change (the stylesheet has no child selectors or `main` rules).
- `docs/index.md`: Markdown twin of the page content, generated from the HTML and then
  hand-checked (the sample status line and the "paste into Claude Code" prompt became code blocks; the "Where it renders" table got a header row). It ends with links back to the HTML version, the
  source, the root site and `llms.txt`.
- Custom 404 — `docs/404.html`: GitHub Pages serves this file, with a real 404 status, for
  every missing path under `/claude-usage/` (until now visitors got GitHub's generic page).
  It carries the landing page's chrome (theme toggle, footer, inline styles), `noindex`, no
  canonical or alternate links, and only absolute URLs, because the one file also answers
  `/claude-usage/a/b/c` and a relative `index.md` would resolve under the wrong directory.
  `<main>` holds an "HTTP 404" label, the H1, one paragraph, a "Where to look next" list
  (project docs, `index.md`, source, `llms.txt`, `sitemap.xml`, home) and a
  `<pre class="md">` block that repeats those pointers as plain Markdown. Why: the Is
  Agentic "Agent-friendly 404s" check gives full credit only for a real 404 whose body
  carries short Markdown guidance, so an agent that hits a dead link can move on without
  parsing the page.
- `tests/test_docs_site.py (unittest; also collected by pytest)`: one `<main>`, one `<h1>` inside it, 500+ characters of text; the head links
  are present; the twin starts with the same H1, contains every H2 of the page, and is plain
  Markdown. For the 404: the title says 404, `noindex` is set, no canonical/alternate link,
  exactly one `<pre class="md">` inside `<main>` (starts with `# 404`, under 700 characters,
  no HTML tags, links the site map, `llms.txt` and the project docs), visible text under
  1,500 characters, and every `href`/`src` absolute. Run with
  `python3 -m unittest discover -s tests -v`.

## Notes
- When the landing page changes, update `docs/index.md` too; the test fails if an H2 goes
  missing from the twin or the H1 drifts.
- Real `Accept: text/markdown` negotiation is not possible on GitHub Pages (no custom
  headers); the twin plus the two links are the static equivalent.
- No per-project `llms.txt`: the root `/llms.txt` covers every path on the host and already
  describes this project.
