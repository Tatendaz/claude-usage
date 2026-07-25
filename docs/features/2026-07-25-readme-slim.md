# Feature: slim the README, move reference material into docs/

**Branch:** docs/readme-slim
**Date:** 2026-07-25

## Summary
The README had grown to 316 lines and 1,763 words carrying a full CLI
reference, six terminals' worth of config, the internals, and a
troubleshooting table — all of which a first-time visitor has to scroll past
to find out whether the thing is for them. That reference material now lives
in four pages under `docs/`, linked from a table at the bottom of the README.
The README is 137 lines and keeps every screenshot.

## Motivation
A README's job is to get a stranger from "what is this" to "it's running" in
under a minute. Everything past that point is documentation, and mixing the
two costs both: the fast path gets buried, and the reference is awkward to
scan inside a marketing page.

Nothing was cut for length's sake — every section that left the README exists
verbatim in `docs/`, and the README links to all of them.

## What changed
- `README.md`: 316 → 137 lines, 1,763 → 745 words, 22 → 7 headings. Kept the
  hero, the specimen line, both install paths, a tightened "What you get",
  the full six-entry iTerm2 picker gallery, and uninstall. Added a
  documentation table linking every page.
- `docs/CLI.md` (new): the flag table, the `CLAUDE_USAGE_*` environment
  variables (now a table rather than a paragraph), the `--format long`
  sample, and the exit-code contract that display formats depend on.
- `docs/TERMINALS.md` (new): tmux (TPM and plain), WezTerm, kitty, starship,
  plain zsh, and the Claude Code statusline. iTerm2 deliberately stays in the
  README — it's the only one with a picker, and it's the flagship path.
- `docs/HOW_IT_WORKS.md` (new): the credentials chain, the endpoint and its
  headers, the parsing preference order, the cache, and the
  undocumented-endpoint caveat. Carries the `/usage` screen capture.
- `docs/TROUBLESHOOTING.md` (new): the `✳` symptom table, plus `--check` and
  `--demo` as the first two things to run.
- `docs/index.html`: the "Install by hand" lead linked to
  `README#pick-your-terminal`, an anchor this change removes. Repointed at
  `docs/TERMINALS.md`.
- "For AI agents" collapsed from ten lines into the documentation table's
  `AGENTS.md` row; "Development" into its `CONTRIBUTING.md` row. Both
  documents already say everything those sections did.

## Notes
Documentation only — no code, no tests, no behavior change. The six picker
captures and the hero capture stay in the README; only
`docs/img/claude-usage-screen.png` moved, into `docs/HOW_IT_WORKS.md` beside
the parsing description it illustrates.

The badge that pointed at `#pick-your-terminal` now points at
`docs/TERMINALS.md`. Every relative link in the README and in the four new
pages was resolved against the working tree before commit.
