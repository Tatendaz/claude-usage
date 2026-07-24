# Feature: previewed picker gallery in the README and on the site

**Branch:** docs/picker-gallery
**Date:** 2026-07-24

## Summary
The six iTerm2 picker entries shipped in v1.1.0 were described in the
README as a text table, with the screenshots hidden behind a collapsed
`<details>`. They're now a proper gallery — each entry named, explained in
a line, and shown as a real status bar capture, ordered widest to
smallest so you can pick by how much room your bar has. The landing page
gains the same gallery, and both get a clock mark next to the title.

## Motivation
The point of the v1.1.0 redesign is that you can *see* each option before
choosing it. Hiding the captures behind a fold and leading with a text
table undercut that. Ordering widest → smallest also matches the actual
decision being made — "how much space do I have?" — better than the
previous grouping by style.

The audit that came with it caught real drift: the landing page still
advertised the pre-v1.1.0 `⟲ reset date Jul 19 12:30am` format, which no
variant renders anymore.

## What changed
- `README.md`: the exemplar table and collapsed `<details>` are replaced
  by an inline gallery — Wide · Countdown, Wide · Inline, Medium,
  Compact · Countdown, Compact · Inline, Mini — each with a one-line
  explainer and its capture. Widest first. A 🕐 clock leads the title.
  Fixed alongside: the `--format long` sample showed
  `resets 12:30am (in 2h)`, which is self-contradictory (a reset two hours
  from now that lands after midnight would print its date); `--all` was in
  the synopsis but missing from the flag table; the upgrade note now names
  v1.0.0 instead of "this update"; the gallery heading is `####` so it
  nests under iTerm2 rather than reading as a sibling of the tmux and
  WezTerm sections.
- `docs/index.html`: new "Pick the look you want" section carrying the
  same six entries and captures. The header mark is now an inline SVG
  clock (`currentColor`, so it takes the accent in both themes — an emoji
  would have ignored the `color` rule the mark is styled with). Stale
  content fixed: the hero specimen line rendered the retired `reset date`
  label, and the "How it works" panel claimed ~640 lines and 87 tests
  (really ~790 and 121). The standalone figure in the "Why" section was
  removed — it was the same capture the gallery immediately below opens
  with, so the page showed one image twice within a screen of scrolling;
  its cross-terminal note moved to the gallery's closing line.

## Notes
No code changed — CLI, component, and JSON contract are untouched from
v1.1.0, so this is a documentation release.

`docs/img/iterm2-statusbar.png` is now unreferenced by both pages (it
shows the pre-v1.1.0 format). It's kept rather than deleted: the
2026-07-18 launch-site feature entry refers to it by name, and its raw
URL may be linked from launch-era social posts.
