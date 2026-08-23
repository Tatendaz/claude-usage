# Session: Agent-readable landing page

**Branch:** feat/agent-readiness
**Date:** 2026-08-22

## Prompts
Carried over from the Tatendaz/Tatendaz.github.io session that produced its PR #8:
1. "Improve how ready https://tatendaz.github.io is for agents. Current Is Agentic score:
   66/100 (Is Agentic readiness model based on Ora audit evidence). Implement the following
   fixes in priority order (failures first, then warnings): …" — nine audit items (content
   without JavaScript, agent-friendly 404s, Markdown content negotiation, agent instruction
   file, brand discoverability, JSON-LD, trust pages, developer-resource discoverability,
   MCP) with evidence and recommended fixes.
2. "can you also check subpages as well like yapui, claude-usage, etc.,"
3. Asked whether to fix the five project pages in their own repos; answer: "Yes, fix all
   five (Recommended)".
4. "and make sure the subpages achieve pairity also and use subagents to not fill the context
   window here"

## Steps taken
- Probed https://tatendaz.github.io/claude-usage/ over HTTP: 200, title/description/canonical set,
  product JSON-LD complete, 4,000+ chars of static text, but no `<main>`, no Markdown twin,
  no `rel="alternate"`/`rel="describedby"`, no link to `llms.txt`.
- Read the page source through the GitHub API (no `<main>`/`<nav>`, H1 inside `<header>`,
  inline CSS with no child selectors) and this repo's docs gate, test runner and CI.
- Patched `docs/index.html` with a shared script (`<main>` wrapper, head links, footer
  links); generated `docs/index.md` with an HTML→Markdown converter and hand-checked it
  (the sample status line and the "paste into Claude Code" prompt became code blocks; the "Where it renders" table got a header row).
- Added `tests/test_docs_site.py (unittest; also collected by pytest)` and ran `python3 -m unittest discover -s tests -v`.
- Second pass, from a subagent working only in this repo (prompt 4): compared the project
  page with the root site, which already had a custom 404, and found missing paths under
  `/claude-usage/` still showed GitHub's default page. Copied the landing page's chrome into
  `docs/404.html` (absolute URLs only, `noindex`, no canonical/alternate links, an
  "HTTP 404" label, the H1, one paragraph, the "Where to look next" list and a
  `<pre class="md">` block of Markdown pointers). Added `NotFoundPageTests` to
  `tests/test_docs_site.py` (title, robots, link rels, the Markdown block's shape and length,
  the text budget, every `href`/`src` absolute). Re-ran
  `python3 -m unittest discover -s tests -v` (135 tests), `ruff check` pinned to CI's 0.14.2,
  and the skill's coverage check.

## Decisions
- `<main>` wraps the header as well as the sections: the H1 lives in the header and the
  scanner only credits an H1 inside `<main>`.
- The twin is generated from the page, not copied from `README.md`, so it mirrors the page
  exactly and the test can hold the two together (same H1, every H2 present).
- No per-project `llms.txt`; the root file covers the whole host and already lists this
  project with its description and links.
- 404 links are absolute (`https://…` or `/claude-usage/…`), never relative: GitHub Pages
  serves the same `404.html` at any depth, so a relative `index.md` from `/claude-usage/a/b/`
  would point at the wrong directory. The inline `data:` favicon stays for the same reason
  (nothing to fetch, no path to break).
- The 404 keeps `rel="describedby"` → `llms.txt` (as a full URL) but has no canonical and no
  alternate link: a dead end has no canonical address and no Markdown twin.
