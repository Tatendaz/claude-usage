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
3. Add two docs entries (CI enforces both):
   - `docs/features/<date>-<branch-slug>.md` — what changed and why
   - `docs/summaries/<date>-<branch-slug>.md` — how the change came to be
4. Open a PR. CI runs tests, checks that source changes come with test
   changes, and checks the docs entries.

## When the endpoint drifts

The usage endpoint is undocumented and changes shape occasionally. Fixes
go in `normalize()` / `_from_limits()` / `_from_legacy()` with a
regression test using an **anonymized** payload (percentages only — strip
anything account-identifying from `--format json` output before pasting).
