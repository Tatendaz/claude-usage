# Feature: slim the README, move reference material into docs/

**Branch:** docs/readme-slim
**Date:** 2026-07-25

## Summary
The README had grown to 316 lines and 1,763 words carrying a full CLI
reference, six terminals' worth of config, the internals, and a
troubleshooting table — all of which a first-time visitor has to scroll past
to find out whether the thing is for them. That reference material now lives
in four pages under `docs/`, linked from a table at the bottom of the README.
The README is 153 lines and keeps every screenshot.

## Motivation
A README's job is to get a stranger from "what is this" to "it's running" in
under a minute. Everything past that point is documentation, and mixing the
two costs both: the fast path gets buried, and the reference is awkward to
scan inside a marketing page.

Nothing was cut for length's sake — every section that left the README exists
verbatim in `docs/`, and the README links to all of them.

## What changed
- `README.md`: 316 → 153 lines, 1,763 → 804 words, 22 → 7 headings. Kept the
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

## Fixing the install path

A copy review caught the README telling people to run the CLI by bare name.
`install.sh` symlinks it to `~/.local/bin/claude-usage` and deliberately never
edits shell rc files, and `~/.local/bin` is not in macOS's default
`/etc/paths`. So `claude-usage --check` — the line immediately after
`./install.sh`, and the first thing a new user types — returned `command not
found`.

The review called the README the only offender. It was not: `docs/CLI.md`, the
agent-facing contract in `AGENTS.md`, and `install.sh`'s own closing output did
it too. All four are fixed here.

- `README.md` and `docs/index.html` now call `~/.local/bin/claude-usage`, as
  `AGENTS.md` and every terminal snippet already did, with a one-line `PATH`
  export offered for anyone who wants the bare name.
- `docs/TROUBLESHOOTING.md`: same fix in both runnable blocks, plus a new
  first table row for `command not found` — the most likely first failure had
  no entry.
- Uninstall was `./uninstall.sh`, which only resolves if you are still `cd`'d
  into the clone. Agent-installed users never were. Now
  `~/.claude-usage/uninstall.sh`.
- `docs/CLI.md`: the `--format long` sample was a runnable line starting with
  the bare name. Now the full path, with a note under the synopsis saying
  where the CLI lives and why the examples spell it out. The synopsis itself
  keeps the bare name — it is the command's name, not a line to copy.
- `AGENTS.md`: "Reading quota programmatically" handed agents
  `claude-usage --format json`. An agent running that in a fresh shell hits
  the same failure, and the install runbook 130 lines above already used the
  full path.
- `install.sh`: the worst instance, and the only one outside the docs. Its
  closing "Next steps" printed `4. Sanity check any time: claude-usage
  --check` — the installer handing you a command that fails, immediately
  after deciding not to touch your `PATH`. Now the full path, plus two lines
  naming the trade-off and giving the export for anyone who wants the bare
  name. Text inside the existing quoted heredoc; no logic added, so `$HOME`
  and `$PATH` stay literal and copyable.

Worth recording why this survived a review pass: on a machine that has the
`PATH` export — the author's does, from `.zprofile` — the bare name resolves
fine. `command -v claude-usage` succeeds locally and fails for a new user.
The check that catches this class is `/etc/paths`, not the local shell.

## Notes
No behavior change. The one non-documentation file touched is `install.sh`,
and only the text of its closing heredoc — no logic, no new branches, nothing
for a test to assert beyond the string itself. The six picker captures and the
hero capture stay in the README.
`docs/img/claude-usage-screen.png` appears in both places: it illustrates the
parsing description in `docs/HOW_IT_WORKS.md`, and it is the argument in the
README — the only capture that shows the same data the tool surfaces, which
is the whole pitch.

Two anchors moved with the "Pick your look (iTerm2)" → "iTerm2 status bar"
rename: `docs/TERMINALS.md` now points at `#iterm2-status-bar`, and the
section opens with a skip link to `#other-terminals` so the readers not on
iTerm2 do not scroll the 45-line gallery to find out it is not for them. The
badge that pointed at `#pick-your-terminal` points at `docs/TERMINALS.md`.
Every relative link and in-page anchor in the README and in the four new
pages was resolved against the working tree before commit.

## Late correction: a copy edit that broke a true claim

The README's feature bullet originally read "polled every 30 s through a
shared 60 s cache." The copy review tightened it to "refreshed every 30 s",
which reads better and is false: `iterm2/ClaudeUsage.py:35` sets
`REFRESH_SECONDS = 30` with the comment "how often we ask the CLI (which
itself caches ~60s)", so the widget asks every 30 s but the number behind it
can be up to a minute old. Restored to state both halves.

Caught while re-checking the cache claims after CodeRabbit flagged the same
class of error in `AGENTS.md`. `docs/HOW_IT_WORKS.md` had the third instance —
"for 60 s" with no mention that `CLAUDE_USAGE_TTL` and `--ttl N` override it.

The pattern worth keeping: a tightening pass optimises for how a line reads,
not for whether it is still true, so any edit that drops a qualifier needs
re-checking against source. Two of the three bad cache claims in this PR were
introduced by editing, not inherited.
