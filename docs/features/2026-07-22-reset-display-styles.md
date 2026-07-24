# Feature: reset times per window, in selectable styles

**Branch:** feat/reset-display-styles
**Date:** 2026-07-22

## Summary
Every window now shows when it resets, not just one. The 5-hour session
and the weekly windows (including per-model weeks like Fable) have their
own reset moments; previously only a single picked reset appeared, only in
the widest iTerm2 variant, labelled ambiguously (`⟲ reset date 11:00pm` —
reset of *what*?). Four display styles are available, user-selectable:

- `countdown` (default in iTerm2): `5h 47% ⟲ reset in 3h · week 18% · fable 33% ⟲ reset in 6d`
- `inline`: `5h 47% ⟲ resets 11pm · week 18% · fable 33% ⟲ resets Jul 28`
- `tail`: `5h 47% · week 18% · fable 33% ⟲ resets 11pm · week Jul 28`
- `off`: percentages only

The iTerm2 ladder has four widths — wide (marks with the label word),
medium (percentages only), compact (bare marks: `47% ⟲3h · 18% · 33% ⟲6d`),
and the slash form as the tightest fallback. Wherever ⟲ appears it carries
the word; only the compact variant goes minimal.

## Motivation
The Fable weekly window resets on a specific date and the session window
on its own 5-hour cycle, but the bar showed only one of them. The label
"reset date" plus a bare time didn't say which window it belonged to.

## What changed
- `bin/claude-usage`: new `--resets {countdown,inline,tail,off}` flag and
  `CLAUDE_USAGE_RESETS` env default (invalid values are ignored — status
  bars must not break). New formatters `fmt_countdown` ("now"/"38m"/"3h"/
  "6d") and `fmt_reset_short` (clock today, weekday within 5 days, month
  day beyond — a weekly reset can be 7 days out, where a bare weekday
  would be ambiguous). Every ⟲ mark carries the label word ("reset in"
  for countdowns, "resets" for absolute styles — the compact width
  variant drops the word; `CLAUDE_USAGE_RESET_LABEL`
  overrides, `""` gives the bare icon); a run of buckets whose resets
  render the same (the weeklies usually share one moment) shows the mark
  once, after the run's last bucket. `pick_reset` (the old single-reset
  heuristic) is gone.
- `--format iterm`: four width variants — the chosen style with words
  (countdown when unspecified), plain, bare-mark compact (`fmt_compact`),
  slash fallback.
- `--format text` / `--format tmux`: unchanged by default (prompt/tmux
  width is precious); opt in via `--resets` or the env var.
- `--format long`: reset lines gain a countdown, e.g.
  `resets 1:00pm (in 3d)`.
- `--format json`: additive `resets_in` and `resets_in_seconds` per
  bucket; contract documented in AGENTS.md.
- `iterm2/ClaudeUsage.py`: a **Resets** knob (Configure Status Bar)
  selects the style per component instance; the value is validated,
  forwarded as `--resets`, and applied promptly via an internal refresh
  wake-up instead of waiting out the 30 s poll.

## Notes
Default `text` output is byte-identical to before, so existing tmux/
starship/zsh/statusline configs render unchanged unless the user opts in.
The `CLAUDE_USAGE_RESET_LABEL` default changed from "reset date" to the
per-style words.
