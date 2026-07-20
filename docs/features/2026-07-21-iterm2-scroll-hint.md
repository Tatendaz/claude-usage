# Feature: README hint — scroll to find the iTerm2 component

**Branch:** docs/iterm2-scroll-hint
**Date:** 2026-07-21

## Summary
Adds a "scroll down" hint to the iTerm2 setup steps and the troubleshooting
table: iTerm2 lists script-provided components below all the built-in ones in
the status bar component menu, so Claude Usage sits below the fold and is
easy to miss.

## Motivation
A real install on a second machine stalled at the drag-into-status-bar step.
The component was installed, the script was running, and registration had
succeeded — the widget just wasn't visible in the component menu without
scrolling, which reads as "the install didn't work".

## What changed
- README iTerm2 step 3: added "Not seeing it? Scroll down — script
  components are listed below the built-in ones."
- README troubleshooting, "Widget missing in iTerm2" row: added the
  scrolled-to-the-bottom check.

## Notes
Docs-only; no code changes. AGENTS.md and install.sh were deliberately left
unchanged — the hint lives in the README only.
