# Session: Landing page refresh before the launch post

**Branch:** docs/landing-refresh-sep15
**Date:** 2026-09-15

## Prompts
1. "Bring the landing page up to date with the current state of main (v1.3.0
   plus PRs #21, #25, #26, #27), in time for a launch post today."
2. "Any test count on the page must match the real number exactly. Also check
   CONTRIBUTING.md and README for stale counts."
3. "Make sure the page covers notifications, the agent-install path, the six
   looks, per-model windows, zero dependencies, MIT. Keep every claim
   verifiable. No em-dashes, no filler. Keep the existing design."

## Steps taken
- Ran the suite: 209 tests pass. `tests/test_install.sh` reports 16 (15
  passed, 1 skipped). The page said 183; CONTRIBUTING said 121 and 15.
- Read `docs/CLI.md` Notifications and `bin/claude-usage` to confirm the
  channel list (terminal OSC 9/99, desktop, herdr, ntfy), the presets, the
  config path, `--notify-test`, the HTTPS-only ntfy rule, and the Enterprise
  block before writing any of it on the page.
- Edited `docs/index.html` and `docs/index.md` together so the Markdown twin
  test keeps passing. Replaced the three em-dashes.
- Checked the HTML tag balance with `html.parser` and that every relative
  link and image on the page resolves to a file in the repo.
- README already described alerts, the agent install, and per-model windows
  correctly, so it was left alone.

## Decisions
- Kept the existing alerts section rather than rewriting it; added the two
  facts it lacked (no daemon, ntfy security policy).
- Wrote "about 1,500 lines" instead of an exact figure so it does not go
  stale on the next small change.
