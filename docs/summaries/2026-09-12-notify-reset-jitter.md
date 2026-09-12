# Session: Stop repeat threshold alerts from reset-time jitter

**Branch:** fix/notify-reset-jitter
**Date:** 2026-09-12

## Requests

1. "I think Claude usage notifications have gone crazy. Can you investigate and fix why I'm getting so many?" (with screenshots of ~20 identical "Claude usage · 50% reached" ntfy pushes on phone and Mac)
2. "Most likely running multiple Claude sessions is triggering many of these."
3. "Submit a PR for this fix."

## Steps taken
- Searched for the sender: the iTerm2 AutoLaunch script `ClaudeUsage.py` runs
  the `claude-usage` CLI six times every 30 s; the CLI owns the alert logic.
- Read `~/.cache/claude-usage/cache.json`: the `notified` ledger held three
  keys for the same session window, differing only in microseconds of
  `resets_at`.
- Fixed `notify_state_key` to truncate the reset time to the minute.
- Added `test_reset_time_jitter_does_not_refire`; ran the unittest suite (199
  tests pass).
- Migrated the local cache to the new key shape and ran one poll to confirm no
  re-fire.
- Checked the "multiple sessions" hypothesis: Claude Code sessions and the
  status-line script do not call the CLI; the shared `notify.lock` already
  serialises the six status-bar polls. Session count only raises the usage
  number, it does not send alerts.

## Decisions
- Truncate to the minute rather than the second: the observed jitter was
  sub-second, but a minute is still far below any real window cadence and
  leaves margin.
- No cache migration code in the CLI: stale keys are pruned on the next poll
  and the worst case is one repeated alert after upgrade.
