<!--
Thanks for contributing! The checklist below records this repository's
contribution requirements. CI enforces some of them — the tests, the
source-needs-tests rule and the docs entries. The rest (branch naming,
no secrets) a reviewer checks by eye, so a green build does not by itself
mean the checklist is satisfied.
-->

## What this changes

<!-- One or two sentences. What does this do, and why? -->

## Why

<!-- The problem being solved, or the capability being added. Link an issue with "Closes #N" if there is one. -->

## Checklist

- [ ] **Branch is named `<type>/<slug>`** — one of `feat/`, `fix/`, `docs/`, `chore/`, `refactor/`.
      GitHub's web "Edit this file" button creates branches named `patch-1`. CI won't reject
      the name itself, but the docs gate will then require `docs/features/<date>-patch-1.md`,
      and the naming convention is enforced by a reviewer.
- [ ] **Tests pass locally:** `python3 -m unittest discover -s tests -v`
      (and `./tests/test_install.sh` if you touched any shell script).
- [ ] **Source changes come with test changes.** CI hard-fails a source-only diff.
      A change to `install.sh`, `uninstall.sh` or `claude-usage.tmux` specifically
      requires a change to `tests/test_install.sh` — a Python test does not cover them.
      If your change genuinely cannot be tested, say why here; there is no label bypass,
      so a maintainer has to make that call explicitly.
- [ ] **`docs/features/<YYYY-MM-DD>-<slug>.md` exists** describing what changed and why.
- [ ] **`docs/summaries/<YYYY-MM-DD>-<slug>.md` exists** describing how the change came to be.
      Both are required here — `<slug>` is your branch name minus its `feat/`-style prefix.
- [ ] **`bin/claude-usage` still imports only the stdlib.** No pip dependencies, ever — CI asserts this.
- [ ] **Shell is clean:** `shellcheck -S style install.sh uninstall.sh claude-usage.tmux tests/test_install.sh`
- [ ] **No secrets, API keys, `.env` files, or real `--format json` output** are in the diff.
      Anonymize payloads to percentages only before pasting them into a test.

## Notes for the reviewer

<!-- Anything surprising, any tradeoff you made, anything you want a second opinion on. Delete if not needed. -->
