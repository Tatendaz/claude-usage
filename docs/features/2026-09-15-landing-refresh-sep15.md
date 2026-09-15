# Feature: Landing page refresh for the v1.3.0 launch post

**Branch:** docs/landing-refresh-sep15
**Date:** 2026-09-15

## Summary
Brings the GitHub Pages landing page (and its Markdown twin) in line with
main after v1.3.0 and the notification fixes in PRs #21, #25, #26, and #27.
Content only; the design and CSS are unchanged.

## Motivation
The page still quoted numbers from July (183 tests, ~1,289 lines) and said
nothing about alerts above the fold. A launch post links here today, so every
claim on the page has to match the code it points at.

## What changed
- Hero tagline now mentions the optional alerts at 50, 80, and 90 percent.
- Meta, Open Graph, Twitter, and JSON-LD descriptions mention the alerts.
- "One readable file" now says about 1,500 lines and 209 tests, matching
  `wc -l bin/claude-usage` and `python3 -m unittest discover -s tests`.
- Alerts section states there is no daemon or extra process, that ntfy only
  talks to HTTPS servers, and that Enterprise subscriptions cannot use ntfy.
- Three em-dashes replaced with plain punctuation.
- `CONTRIBUTING.md` test counts corrected: 209 unittest cases, 16 install
  tests.

## Notes
`docs/index.md` mirrors every paragraph of the HTML; `tests/test_docs_site.py`
enforces that, so both files change together.
