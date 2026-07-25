# Contributing

Thanks for helping! A few ground rules keep this project small and safe:

## Principles

- **`bin/claude-usage` stays stdlib-only.** No pip dependencies, ever —
  it must run on a bare macOS/Linux `python3`.
- **Never expose the token.** Credentials are read, used for one request,
  and forgotten. No printing, logging, or writing them anywhere.
- **Status bars must not break.** The CLI always exits 0 for display
  formats and degrades to a short human-readable line (`✳ n/a`, `✳~ …`).
- Terminal adapters stay thin: all logic lives in the CLI; adapters just
  poll it.

## Workflow

1. Branch from `main` (`feat/<slug>` or `fix/<slug>`).
2. Add tests for anything you change — the suite must stay free of
   network, Keychain, and real-cache access:
   `python3 -m unittest discover -s tests -v`
   If you touched a shell script, also run `./tests/test_install.sh`.
3. Add two docs entries (CI enforces both):
   - `docs/features/<date>-<branch-slug>.md` — what changed and why
   - `docs/summaries/<date>-<branch-slug>.md` — how the change came to be
4. Open a PR. CI runs tests, checks that source changes come with test
   changes, and checks the docs entries.

`main` is protected: pull requests are the only way in, force-pushes are
off, and a PR needs every required check green plus one approving review
from the code owner (@Tatendaz). You can't approve your own PR — GitHub
doesn't allow it — so everything gets a second pair of eyes.

## Branch names

`<type>/<slug>`, where type is `feat` `fix` `docs` `chore` or `refactor`.

This is load-bearing, not style: the docs gate strips that prefix, turns
any remaining `/` into `-`, and looks for docs files named after what's
left.

> Editing a file through GitHub's web UI creates a branch called
> `patch-1`. The gate will then demand `docs/features/<date>-patch-1.md`
> and fail your PR. Create a properly named branch instead.

## The two docs entries

Both are required, both must be **added by your PR** (an entry already in
the tree from someone else's branch won't do), and the filename must be
exactly `<YYYY-MM-DD>-<slug>.md`. Worked example:

    branch:  feat/tmux-theme-support
    slug:    tmux-theme-support
    files:   docs/features/2026-07-25-tmux-theme-support.md
             docs/summaries/2026-07-25-tmux-theme-support.md

Match the shape of the existing entries — features says what changed and
why, summaries says how it came to be (prompts, dead ends, decisions).

## Running the checks locally

Nothing to install for the tests. There is no `pip install`, no
`requirements.txt`, and there must never be one.

```sh
python3 -m unittest discover -s tests -v   # the documented runner: 121 tests
./tests/test_install.sh                    # install.sh / uninstall.sh: 15 tests
./tests/test_install.sh -v                 # ...with each assertion echoed
shellcheck -S style install.sh uninstall.sh claude-usage.tmux tests/test_install.sh
```

`tests/test_install.sh` is plain bash — no bats, nothing to install. It
runs the real `install.sh` and `uninstall.sh` against a `mktemp -d` HOME
with `HOME`, `XDG_CACHE_HOME` and `XDG_CONFIG_HOME` all redirected, and it
aborts the whole run rather than execute anything if that redirection ever
fails. Keep it that way: `uninstall.sh` does
`rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/claude-usage"`, so a test that
escaped its sandbox would delete a real person's cache.

**Python 3.9 is the floor.** The README badge says "python 3.9+" and CI now
enforces it across 3.9–3.14. Nothing 3.10+ may appear in `bin/claude-usage`
or the adapters: no `match`, no `X | Y` annotations, no `str.removeprefix`,
no `zoneinfo`/`tomllib`, and no bare
`datetime.fromisoformat("...Z")` — keep the existing
`.replace("Z", "+00:00")`, which is what makes that call work before 3.11.

If you run ruff, mind this trap:

```sh
ruff check .                     # WRONG — silently skips bin/claude-usage
ruff check bin/claude-usage iterm2/ClaudeUsage.py kitty/tab_bar.py tests/
```

Ruff's directory walk only picks up `*.py`, and the core CLI has no
extension, so `ruff check .` quietly ignores the main deliverable. CI
passes the paths explicitly for exactly this reason.

Never run `claude-usage --check` in CI, and don't add anything that would.
It makes a real authenticated request to `api.anthropic.com`. `--demo` is
the offline equivalent.

## Required checks

Your PR must be green on all of these before it can merge:

| Workflow | Check |
|---|---|
| CI | `Tests (py3.9, ubuntu-latest)` |
| CI | `Tests (py3.10, ubuntu-latest)` |
| CI | `Tests (py3.11, ubuntu-latest)` |
| CI | `Tests (py3.12, ubuntu-latest)` |
| CI | `Tests (py3.13, ubuntu-latest)` |
| CI | `Tests (py3.14, ubuntu-latest)` |
| CI | `Tests (py3.13, macos-latest)` |
| CI | `Tests (pytest)` |
| CI | `Shell (shellcheck + bash -n + install tests)` |
| CI | `Installer smoke (macOS)` |
| CI | `Lint (ruff)` |
| PR Gate | `Docs gate (features + summaries)` |
| PR Gate | `New code has new tests` |

`New code has new tests` fails a diff that changes source without changing
tests. It has a second rule on top: a change to `install.sh`,
`uninstall.sh` or `claude-usage.tmux` requires a change to
`tests/test_install.sh` specifically, because a Python test does not cover
a shell script. There is no label that bypasses either rule — if a change
genuinely can't be tested, say so in the PR and a maintainer decides.

> **First PR here?** Your workflow runs will sit at *"pending approval"*
> until a maintainer clicks "Approve and run". That's a GitHub policy for
> first-time contributors, not a broken build. Nothing is wrong; wait.

## When the endpoint drifts

The usage endpoint is undocumented and changes shape occasionally. Fixes
go in `normalize()` / `_from_limits()` / `_from_legacy()` with a
regression test using an **anonymized** payload (percentages only — strip
anything account-identifying from `--format json` output before pasting).
