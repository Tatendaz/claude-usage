# Feature: six pre-built, previewed iTerm2 status bar entries

**Branch:** feat/reset-display-styles
**Date:** 2026-07-24

## Summary
The iTerm2 component used to be one generic entry with a free-text
**Resets** knob (type `countdown`/`inline`/`tail`/`off` and hope) and an
automatic width-fit the component picked for you. Now there are six
fixed, pre-built entries in the "Configure Status Bar" picker, and each
one's preview (`exemplar`) shows exactly what it renders — no knob, no
guessing:

- **Wide · Countdown** (default) — `✳ Usage 5h 47% ⟲ reset in 3h · week 18% · fable 33% ⟲ reset in 6d`
- **Wide · Inline** — `✳ Usage 5h 47% ⟲ resets 11pm · week 18% · fable 33% ⟲ resets Jul 28`
- **Compact · Countdown** — `✳ 47% ⟲3h · 18% · 33% ⟲6d`
- **Compact · Inline** — `✳ 47% ⟲11pm · 18% · 33% ⟲Jul 28`
- **Medium** — `✳ Usage 5h 47% · week 18% · fable 33%`
- **Mini** — `✳ 47%/18%/33%`

`tail` and `off` at Wide/Compact size aren't in the list — `off` already
looks identical to Medium/Mini (there's nothing to add), and Tail was cut
to keep the picker to six meaningfully distinct entries rather than the
full 16-way (4 size × 4 style) cross, most of which would have been
duplicate-looking anyway (Medium and Mini never carry reset marks, so
they're identical across all four styles). Both remain available from the
CLI/tmux/starship side via `--resets`.

## Motivation
The previous knob (`iterm2/ClaudeUsage.py`, committed just before this)
solved *what* the reset styles look like, but not *how you pick one*: you
still had to drag a generically-named "Claude Usage" component, open its
config panel, and type a style name into a blank text field with no
preview of the result. iTerm2's status bar scripting API has no
dropdown/choice knob — only checkbox, free text, number, and color — so
the only way to give someone a real preview *before* they commit to a
choice is iTerm2's `exemplar` field, which is per-component. That forces
the fix to be "more components," not "a better knob."

## What changed
- `bin/claude-usage`: new `--width {wide,medium,compact,mini}` flag
  prints exactly one fixed-size rendering instead of the auto-fit ladder
  (`--format iterm` only). New `fmt_mini()` (extracted from `fmt_iterm()`'s
  inline slash-building) and `fmt_iterm_width()`. `fmt_iterm()`'s own
  output is unchanged — it now just calls `fmt_mini()` instead of
  duplicating the join.
- Fixed a latent bug this surfaced: `fmt_compact()` had no `"off"` branch
  — the ladder never called it that way (guarded by `if style != "off"`),
  so that path was dead code until `--width compact --resets off` became
  reachable. It was silently rendering reset marks despite `off`. Now it
  returns bare percentages like every other `off` output.
- `iterm2/ClaudeUsage.py`: rewritten around a `VARIANTS` table of
  (identifier suffix, label, exemplar, width, style) driving six
  `StatusBarComponent` registrations, each with its own background
  refresh loop calling `--width`/`--resets` directly. Removed entirely:
  the `Resets` knob, `knob_style()`, `KNOB_RESETS`, and the knob-change
  "refresh promptly" event plumbing — none of it is needed when each
  component's look is fixed at registration instead of runtime-configured.
  The first variant (Wide · Countdown) keeps the plugin's original
  identifier (`dev.tatendazhou.claude-usage`), so upgrading in place
  doesn't orphan a status bar that already has the old component in it.
- `README.md`: install steps and the width-ladder table replaced with the
  six-entry table; CLI reference gained `--width`.
- Tests: `TestITermKnobStyle` removed (the function is gone);
  `TestITermRunCore` updated for the new `run_core(width, style) -> str`
  signature (was `run_core(style=None) -> list[str]`); new
  `TestITermVariants` checks the `VARIANTS` table's shape (six entries,
  unique identifiers, the first keeps the original identifier, valid
  width/style pairing) and — the one that would actually catch a stale
  preview — asserts every hardcoded `exemplar` matches live
  `--width`/`--demo` output. `bin/claude-usage` gained direct coverage for
  `--width` and the `fmt_compact` off-branch fix. Suite: 118 tests, all
  passing.

## Notes
`--resets inline`'s exemplar text embeds a real clock time and weekday,
which drift with wall-clock time between when the string was written and
whenever the test suite runs — the exemplar-vs-live-output test masks
those two tokens out before comparing (`inline` variants only;
`countdown`'s relative buckets like "3h"/"6d" are stable because
`--demo`'s reset offsets are fixed deltas from "now" at invocation time,
so those are safe to assert byte-exact).
