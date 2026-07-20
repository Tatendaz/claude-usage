# Session: README scroll hint for the iTerm2 component menu

**Branch:** docs/iterm2-scroll-hint
**Date:** 2026-07-21

## Steps taken
- Debugged a fresh install on a second machine where the Claude Usage
  component appeared to be missing from iTerm2's status bar component menu.
  The script was installed, running, and registered; the component was
  simply below the fold — iTerm2 lists script components after all the
  built-ins, and the menu needs scrolling.
- Added that hint to the README's iTerm2 setup step 3 and to the
  "Widget missing in iTerm2" troubleshooting row.

## Decisions
- Docs-only change, README only — AGENTS.md and install.sh left unchanged
  per request.
