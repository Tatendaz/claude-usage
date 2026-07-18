# Session: Landing page polish after live review

**Branch:** docs/site-polish
**Date:** 2026-07-19

## Prompts

1. "fix spacing and add light mode always add light and dark mode." (with six
   screenshots of the live site) "use skills to make sure it doesnt look like
   AI"
2. "THe long line spacing from everything else is too little" (clarifying that
   the section divider lines sat too close to surrounding content)

## Steps taken

- Read the user's `no-ai-slop` and `design-taste-frontend` skills and audited
  the live page against them. Confirmed real violations: div-built fake
  terminal window in the hero (a listed "#1 tell"), three uniform card grids,
  decorative middle-dot separators, centered hero, cramped divider spacing.
- Rewrote `docs/index.html`: shared `--gap-section` rhythm (clamp 72-104px)
  around every hairline, left-aligned hero, status line as an honest labeled
  specimen block, "How it works" as divided rows, terminals as a table, FAQ as
  divided rows, footer hairline made full-bleed to match sections.
- Added a manual theme toggle (persisted in localStorage, overrides
  `prefers-color-scheme`, `?theme=` URL override for QA), and a light palette
  in the same cool-neutral family with the accent darkened for AA contrast.
- QA'd dark, light, and full-page renders via headless Chrome screenshots
  before committing.

## Decisions

- Terminal-content blocks (specimen, install commands) stay dark in both
  themes: terminals are dark, and inverting them would fake the product.
- Kept the middle dots inside the rendered status line itself; that is the
  plugin's real output, and rewriting it would misrepresent the product.
- Manual toggle defaults to the system preference until the visitor picks,
  then persists their choice.
