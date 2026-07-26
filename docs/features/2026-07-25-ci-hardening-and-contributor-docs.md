# Feature: a CI that can actually fail, and docs that say how to pass it

**Branch:** chore/ci-hardening-and-contributor-docs
**Date:** 2026-07-25

## Summary
The repo had one workflow, three jobs, and a green history — but the thing
it shipped hardest was the thing it checked least. `install.sh` is the front
door (README and AGENTS.md both tell users *and autonomous agents* to clone
and run it unattended against their own `$HOME`), and a PR could rewrite it,
`uninstall.sh` and `claude-usage.tmux` together with **zero** tests, zero
lint, and a fully green gate.

This change adds the missing test suite, adds a `CI` workflow around it, and
writes down the rules a contributor was previously expected to guess.

The headline is `tests/test_install.sh`: 15 plain-bash tests covering install,
uninstall, idempotency, both anti-clobber guards, and the exact
what-was-created-vs-what-was-removed set — all against a `mktemp -d` HOME.

## Motivation
Four gaps, in the order they matter:

1. **The shell layer was untested and ungated.** `uninstall.sh` runs
   `rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/claude-usage"`. For a script
   strangers are told to run unattended, "nobody has complained yet" is not
   a test strategy.
2. **The `python 3.9+` badge was unenforced.** CI proved 3.11 and nothing
   else. One `match` statement would have landed green and broken every user
   on a stock macOS `python3`.
3. **The docs gate failed correct PRs.** The branch slug was spliced into a
   `grep -E` pattern unescaped, so `feat/c++parser` and `feat/x[1]` were
   matched as regexes and reported as "missing" against a PR that had the
   file. The same pattern was unanchored, so branch `docs/gallery` was
   satisfied by an unrelated pre-existing `2026-01-01-picker-gallery.md`.
4. **Nothing was written down.** The Python floor lived only in a README
   badge; the docs-entry filename format, the `patch-1` trap, and the
   first-PR "pending approval" surprise were undocumented; and there was no
   private way to report a vulnerability in a tool that reads OAuth
   credentials out of the macOS Keychain.

## What changed

- **`tests/test_install.sh` (new, 15 tests).** Plain bash assertions — no
  bats, nothing to `pip install`, consistent with "No pip dependencies,
  ever". Each test gets a fresh `mktemp -d` with `HOME`, `XDG_CACHE_HOME`
  and `XDG_CONFIG_HOME` all redirected. A hard interlock re-checks all three
  immediately before every invocation of a script under test and aborts the
  run with exit 99 rather than let anything execute outside the sandbox.
  Coverage: fresh install creates exactly the CLI symlink and the iTerm2
  component and nothing else; the installed CLI renders `--demo` and
  `--format json` and writes no files; install is idempotent across three
  runs; both anti-clobber guards (a real file at the CLI path aborts, a
  foreign iTerm2 component is skipped) plus the mirror case that a component
  carrying our own marker *is* refreshed; uninstall removes every file it
  created and nothing that predated it, spares a foreign CLI, a foreign
  component and a symlink pointing elsewhere, deletes only its own cache
  directory, is idempotent, and is a clean no-op on a machine where nothing
  was ever installed; and neither script modifies the repo checkout.
- **`.github/workflows/ci.yml` (new).** `permissions: contents: read`;
  a `concurrency` group that cancels superseded PR runs but never cancels
  `main`; `timeout-minutes` on every job; both actions pinned to commit SHAs
  rather than mutable tags. Jobs: `tests` (3.9–3.14 on ubuntu plus a macOS
  leg — this is a macOS-first tool that was only ever tested on Linux),
  `pytest` (pinned `pytest==9.1.0`), `shell` (shellcheck + `bash -n` + the
  new suite), `install-smoke` (the macOS half of the installer suite), and
  `lint` (pinned `ruff==0.14.2`, `py_compile`, an AST assertion that the core
  CLI imports only stdlib modules, and an assertion that no pip manifest has
  appeared).
- **`.github/workflows/pr-gate.yml`.** Lost its `tests` job — `ci.yml` is now
  the single owner of testing, so the suite no longer runs twice per PR and
  branch protection isn't offered two similar `Tests` contexts. Gained
  `permissions`, `concurrency`, `timeout-minutes`, and SHA-pinned actions.
  The coverage gate's language list was trimmed to what this repo actually
  ships (it carried dead `_test.go` / `.java` / `_spec.rb` arms and one
  alternation that could only ever match a file named literally `test_`) and
  extended with a shell rule: a change to `install.sh`, `uninstall.sh` or
  `claude-usage.tmux` now requires a change to `tests/*.sh`.
- **`.github/scripts/require-docs-entry.sh` (new).** The docs-gate matcher,
  extracted from the workflow so shellcheck covers it and so it can be run by
  hand before pushing. It never builds a regex from the branch slug — the
  slug is compared with `=` — and it requires the basename to be exactly
  `<YYYY-MM-DD>-<slug>.md`. That fixes both the metacharacter failure and the
  substring match. Its error message also names the `patch-1` trap.
- **`bin/claude-usage`, `tests/test_claude_usage.py`.** The two pre-existing
  `E731` lambda assignments are now `def`s, so the `lint` job runs ruff's
  default rule set with no `--ignore` flag and no standing exemption. Pure
  refactor; both sites are covered by the existing 121 tests.
- **`CONTRIBUTING.md`.** Extended, not rewritten — Principles and "When the
  endpoint drifts" are untouched. New: the branch-name convention and the
  `patch-1` warning, the docs-entry format with a worked example, the local
  command list, the Python 3.9 floor spelled out in prose with the specific
  constructs to avoid, the `ruff check .` trap, the required-check names
  verbatim, the note that `main` is protected, and the first-PR "pending
  approval" surprise.
- **`SECURITY.md` (new).** There was no private disclosure path for a tool
  that reads OAuth credentials from the Keychain. States what the tool does
  with a token in six numbered claims, and defines a vulnerability as
  anything that breaks one of them.
- **`.github/CODEOWNERS`, `.github/PULL_REQUEST_TEMPLATE.md` (new).**
- **`.gitignore`.** Added `.ruff_cache/`, since contributors now run ruff.

## Notes
No user-visible behaviour changed. `--demo` output is byte-identical, the
JSON contract is untouched, and `install.sh` / `uninstall.sh` are not
modified at all — they are only now tested.

The suite documents one cosmetic wart rather than silently fixing it:
`uninstall.sh` prints `✓ removed cache` even when there was no cache, because
`rm -rf` succeeds against a path that never existed. It's asserted as current
behaviour so that changing it later is a deliberate decision.

`tests/test_install.sh` skips one case — "install without iTerm2 present" —
on any machine that has `/Applications/iTerm.app`, since `install.sh` keys off
that absolute path and a sandboxed `HOME` cannot hide it. It runs on the
Linux CI leg.
