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
in full in `docs/`, and the README links to all of them. "In full" rather than
"verbatim": the content is all there, but reformatted where the new home made
it clearer (the environment variables became a table) and corrected where the
move exposed a stale line.

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

## Third review round: snippets that clobber existing config

The full PR review — which only ran after two triggers silently no-opped —
found three issues, all in pages this change created.

- **`docs/TERMINALS.md`, tmux (major).** Both snippets `set -g status-right`
  wholesale, so anyone who already had one lost it. They now open with what
  they replace and how to keep yours.
- **`docs/TERMINALS.md`, kitty (major).** The `cp` overwrote an existing
  custom `tab_bar.py`, and the "merge instead" warning sat nine lines *below*
  the command that destroyed the file. Now `cp -n`, which refuses to clobber,
  with the warning above it. `cp -n` is silent whether it copies or skips, so
  the doc first told readers to read the exit status — 0 copied, 1 skipped.
  That is BSD behaviour, verified on macOS, and GNU `cp` does not agree, so a
  Linux kitty user would have been told the opposite of the truth. Replaced
  with a `grep` for `_draw_right_status` in the installed file, which asks
  what actually happened rather than how this platform reports it. Tested in
  both the file-exists and file-absent cases.
- **`docs/TERMINALS.md`, WezTerm (minor).** The handler example referenced
  `my_status`, which is defined nowhere; pasting it raises "attempt to
  concatenate a nil value". This was a half-finished fix from the previous
  round — that round corrected *when* `text()` is called and left the
  undefined variable in place. Now a defined placeholder
  (`wezterm.strftime('%H:%M')`), and the prose says to use `setup()` or the
  handler, not both. Snippet syntax-checked with `luac -p`.
- **`docs/TROUBLESHOOTING.md` (minor).** The rate-limit row claimed "it backs
  off through the cache." It does not back off at all. On a 429 `get_usage()`
  returns the cached payload without advancing `fetched_at`, so the freshness
  check at `bin/claude-usage:223` stays false and every subsequent poll
  re-hits the endpoint. Confirmed by driving `get_usage()` with a stubbed
  429: three polls, three network attempts, `fetched_at` unchanged. Reworded
  to say what it does — serves the last cached values and retries next poll.

The tmux and kitty findings are the same defect as the zsh `RPROMPT` bug two
rounds earlier: an example that assumes the reader's config is empty. That
makes three separate instances in this PR, which is a pattern rather than
three accidents. A config snippet should be checked against "what if this
person already has one of these" before it ships.

The WezTerm guard exposed the same gap one section down: kitty's `cp` also
writes into `~/.config/kitty`, which does not exist for anyone who has never
written a `kitty.conf` — and the doc runs that copy *before* it tells you to
edit `kitty.conf`. Added `mkdir -p` there too, then ran the whole kitty block
against a synthetic empty `$HOME`: it installs cleanly with no `~/.config` at
all, and still leaves a pre-existing custom `tab_bar.py` untouched.

## Fourth round: two claims inherited from the old README

Both flagged by the local review, both pre-existing on `main` and moved into
`docs/TERMINALS.md` by this change, so this branch owns them now.

- **"colors each window"** (`main:README.md:151`). `fmt_tmux` colours the
  percentage text of each quota bucket. In a tmux document "window" means a
  tmux window, so the sentence read as a claim that the plugin recolours your
  windows. Now "each quota percentage", with the ambiguity named explicitly.
- **`CLAUDE_USAGE_RESETS` in tmux.** The section offered the variable as the
  easy way to change reset style, without saying that tmux runs status
  commands from the server, which holds the environment it started with.
  Adding the export to `~/.zshrc` does nothing to a running server.

Verified rather than asserted, on tmux 3.6b against an isolated socket
(`-L cutest`) so no real session was touched. A server started without the
variable, then given it via a shell export, saw `UNSET`; after
`tmux set-environment -g` it saw the value; a server started with the variable
present saw it. So the doc now says to set it on the server or restart tmux.

First two attempts at that test were wrong and worth noting: `display-message
-p '#(...)'` returned empty for every case, and a detached session logged "no
current client" because a status line with no attached client never renders,
so the `#()` never ran. An empty result looked like a finding and was actually
a broken harness — the same trap as reading silence from a review that never
ran.
