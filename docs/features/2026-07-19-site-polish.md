# Feature: Landing page redesign - spacing, theme toggle, de-templated layout

**Branch:** docs/site-polish
**Date:** 2026-07-19

## Summary
Reworks `docs/index.html` after visual review of the live site: a generous and
consistent vertical rhythm, a manual light/dark toggle on top of the existing
system-preference support, and a layout pass that removes template-looking
patterns (fake terminal chrome, uniform card grids).

## Motivation
On the live site the section divider lines sat too close to the content around
them, the page only followed the OS theme with no way to switch, and several
elements read as generic generated design: a fake terminal window with
traffic-light dots in the hero, three near-identical card grids, decorative
middle-dot separators.

## What changed
- Spacing: one shared section rhythm (`--gap-section`, clamp 72-104px) applied
  above and below every full-bleed hairline, including the footer's; larger
  heading margins and row padding throughout.
- Theming: manual toggle (top right) that overrides the system preference and
  persists in `localStorage`; a `?theme=light|dark` URL override; light palette
  in the same cool-neutral family as the dark one, with the accent darkened for
  AA contrast on light backgrounds. Code and specimen blocks stay dark in both
  themes, like a terminal.
- Layout: left-aligned hero; the status line shown as a labeled type specimen
  instead of a fake window (no chrome, no blinking cursor); "How it works" as
  divided definition rows instead of cards; terminals as a real table; FAQ as
  divided rows instead of boxed cards.
- Copy trims to match: hero support line under 20 words, decorative middle-dot
  separators removed from labels and footer (the product's own output line
  keeps its real dots).

## Notes
- The `?theme=` override exists for screenshot QA and shareable links; it does
  not persist.
- No behavior change to the plugin itself; page-only.
