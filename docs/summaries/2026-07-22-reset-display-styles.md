# Session: per-window reset times with selectable styles

**Branch:** feat/reset-display-styles
**Date:** 2026-07-22

## Steps taken
- Confirmed the gap against live data: the API reports distinct reset
  moments (session at a clock time today, weekly/Fable on a specific
  date) but only one appeared, only in the widest iTerm2 variant, with
  the ambiguous `⟲ reset date …` label.
- Mocked up three layouts (per-bucket inline, grouped tail, relative
  countdowns); countdown was chosen as the default with the wording
  "reset in" next to the ⟲ icon, and all three shipped as selectable
  options.
- Implemented in the core CLI: `--resets` flag + `CLAUDE_USAGE_RESETS`
  env, compact time formatters, dedupe of shared weekly resets, countdown
  parentheticals in `--format long`, additive
  `resets_in`/`resets_in_seconds` JSON fields.
- Refined after review on the bar: a shared reset now lands after the
  LAST bucket of its run (`… week 20% · fable 36% ⟲ reset in 5d`), the
  label word repeats at every ⟲ mark, and the iTerm2 ladder gained a
  bare-mark compact variant (`47% ⟲3h · 18% · 33% ⟲6d`) between the plain
  and slash forms — the word appears wherever ⟲ does, except compact,
  which stays minimal.
- Added an iTerm2 **Resets** knob; the component validates the knob text,
  forwards it as `--resets`, and wakes its refresh loop so a style change
  applies immediately.
- Removed the now-dead `pick_reset` heuristic and its tests; added 15
  tests (fixed-clock formatter units, dedupe/label behavior, per-format
  styles, env handling incl. junk values, knob validation, flag
  forwarding). Suite: 104 tests, all passing.

## Decisions
- Default stays quiet outside iTerm2: plain `text`/`tmux` output is
  unchanged unless `--resets`/env opts in, so existing configs don't grow
  wider silently.
- Weekday names only within 5 days: a weekly reset can be 7 days out,
  where a bare weekday would collide with today; beyond 5 days it prints
  the date (e.g. `Jul 28`).
- Reset label defaults are per-style ("reset in" / "resets");
  `CLAUDE_USAGE_RESET_LABEL` still overrides, `""` gives a bare icon.
