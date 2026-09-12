# Feature: Stop repeat threshold alerts from reset-time jitter

**Branch:** fix/notify-reset-jitter
**Date:** 2026-09-12

## Summary
Threshold alerts fired on every status-bar poll instead of once per window.
The "already sent" ledger now keys each window on its reset time truncated to
the minute, so the same window is recognised across polls.

## Motivation
The usage API re-stamps `resets_at` with fresh microseconds on every fetch
(`…01:50:00.131071`, `…01:50:00.138753`, `…01:50:00.162641` for one 5-hour
window). The ledger key used the raw ISO timestamp, so each poll read as a
brand-new window and re-fired the 50% alert. With six iTerm2 status-bar
variants polling every 30 seconds this produced a push-notification storm on
every configured channel (ntfy, desktop, terminal, herdr).

## What changed
- `notify_state_key` drops seconds and microseconds from the reset time before
  building the ledger key. No real quota window resets more often than once a
  minute, so window identity is preserved.
- Regression test `test_reset_time_jitter_does_not_refire` covers the storm
  and confirms a window one minute apart still re-arms.

## Notes
Existing cache entries under the old key shape are pruned automatically on the
next poll (they no longer match a live window). On upgrade a user who already
received an alert for the current window may receive it once more; after that
the ledger is stable.
