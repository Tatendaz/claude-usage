# Feature: GitHub Pages landing site + social preview

**Branch:** docs/launch-site
**Date:** 2026-07-18

## Summary
A self-contained GitHub Pages landing page (`docs/index.html`) and a 1280×640
social preview card (`docs/social-preview.png`), served from the `docs/` folder
on `main`. This is the project's shareable front door for non-GitHub audiences.

## Motivation
The launch plan drives traffic from Reddit, Hacker News, X, and LinkedIn. A
GitHub README works for developers already on GitHub; the landing page serves
everyone else: it leads with the one-line value proposition, the live-looking
status bar demo, and the paste-into-Claude install prompt, and it gives link
previews a proper Open Graph card instead of a bare repo link.

## What changed
- `docs/index.html`: single-file page, no external assets or requests. Dark
  theme with light-mode support via `prefers-color-scheme`. Sections: hero with
  an animated terminal mock of the real status line, the AI-install prompt with
  a copy button, why/how-it-works cards, manual install, per-terminal grid, FAQ.
  SEO head: canonical URL, Open Graph + Twitter cards pointing at the social
  preview, `SoftwareApplication` and `FAQPage` JSON-LD (FAQ text matches the
  visible text verbatim), emoji favicon as an SVG data URI.
- `docs/social-preview.png`: 1280×640 card rendered from a scratch HTML file
  via headless Chrome (109 KB, under GitHub's 1 MB limit). Referenced by the
  page's OG tags; also intended for upload as the repo's social preview image.
- `docs/.nojekyll`: makes Pages serve `docs/` as-is (no Jekyll pass).

## Notes
- Pages is enabled from `main:/docs` after this branch merges; the repo
  homepage field then points at https://tatendaz.github.io/claude-usage/.
- The uploaded repo social preview (Settings > General) cannot be set via API;
  that step stays manual.
- The hero screenshot (`docs/img/iterm2-statusbar.png`) predates the current
  display format ("Usage" title, "reset date" label); re-capture when
  convenient, no code change needed.
