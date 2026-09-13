# Feature: Identify an alert window by the window, not its reset stamp

**Branch:** fix/notify-window-identity
**Date:** 2026-09-13

## Summary
A threshold alert now fires once per window per level, even while the usage API
keeps re-stamping `resets_at`. The "already sent" ledger is keyed on the window
itself, with the reset time stored inside the record and compared with slack.

## Motivation
`resets_at` is re-stamped on every fetch and the value drifts. The first fix
([reset-time jitter](2026-09-12-notify-reset-jitter.md)) truncated it to the
minute, which covered microsecond drift. The drift is larger than that. Sampled
from the live endpoint, one weekly window reported:

```text
09:59:59.922129   ->  ledger key ...|09:59:00
10:00:00.319455   ->  ledger key ...|10:00:00
10:00:00.015092   ->  ledger key ...|10:00:00
09:59:59.700443   ->  ledger key ...|09:59:00
```

The weekly windows reset on the hour, so the drift straddles a boundary. Every
crossing produced a new ledger key; `due_notifications` pruned the old key as a
window that no longer existed and re-announced every crossed level. A week
parked at 99% alerted every couple of minutes, indefinitely.

Rounding cannot fix this. Every rounding has a boundary, and a reset time that
lands on the hour sits exactly on one — truncating to the hour instead would
split `09:59:59.9` and `10:00:00.2` just as badly.

Replaying those four sampled stamps three times over, against a single 99%
window: **7 alerts on the previous code, 1 on this one.**

## What changed
- `notify_state_key` returns the window key alone (`weekly_scoped:fable`), with
  no timestamp component.
- A ledger record is now `{"levels": [...], "resets": "<iso>"}`. `_same_window`
  treats a reset within `WINDOW_SLACK` (15 minutes) as the same window, so
  drift is absorbed; a reset beyond it means the window rolled over and every
  level re-arms. Real windows are 5 hours and 7 days apart.
- While a window holds, the record keeps its original stamp, so second-by-second
  drift cannot creep the anchor forward one fetch at a time.
- `due_notifications` takes a `reserved` map. A reservation from a concurrent
  poller always describes the poll happening now, so its levels count as sent
  whatever stamp they carry. This replaces merging reservations into the sent
  view, which the new record shape made ambiguous.

## Notes
Records written by earlier versions do not match the new shape, so each live
window alerts once more on upgrade and is then stored in the current shape.

`test_reset_time_drift_does_not_refire` replaces the old jitter test. It covers
microsecond drift and second-scale drift in both directions across a boundary.
The old test asserted that a window one minute later re-arms; that is now drift
rather than a new window, and asserting it was part of how this bug survived.
`test_a_rolled_over_window_re_arms` covers genuine rollover.
