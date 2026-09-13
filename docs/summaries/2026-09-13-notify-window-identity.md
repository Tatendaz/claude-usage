# Session: The notification storm was still running

**Branch:** fix/notify-window-identity
**Date:** 2026-09-13

## Requests

1. "I think I'm still facing the issue"
2. "Notification should only fire once when a condition is met. Right now I'm
   sitting at 99% and I keep getting notifications"

## Work

The owner was right and the previous two fixes were not enough. The ntfy topic
showed 147 alerts in 12 hours, still firing after the earlier fix was installed.
What had changed was the shape: the same-second bursts of six were gone, so the
concurrency fix had worked, but a single alert was still repeating every one to
two minutes.

The ledger on disk held `weekly_scoped:fable|2026-09-15T09:59:00+00:00` while a
live fetch returned `10:00:00.256361`. Feeding both stamps through
`notify_state_key` produced two different keys for one window. Sampling the
endpoint every nine seconds caught the drift crossing the boundary in both
directions, which confirmed the mechanism rather than inferring it.

Keyed the ledger on the window instead, with the reset stamp stored in the
record and compared against a 15-minute slack. Split reservation handling out of
the sent view into an explicit `reserved` argument, because the new record shape
made the old merge ambiguous.

Six existing tests asserted the old record shape. One of them,
`test_reset_time_jitter_does_not_refire`, also asserted that a window one minute
later re-arms — an assumption that helped this bug survive the previous fix. It
was replaced with drift coverage in both directions plus a separate rollover
test.

## Validation

Replayed the four sampled stamps three times against one 99% window: the merged
code fired 7 alerts, this code fired 1. The new drift test fails on merged main
with `drift to 2026-09-13 14:35:59.900000+00:00 refired`. 208 tests pass.

Caution worth recording: eight consecutive live polls fired nothing, but the
stamp did not drift during them, so that run proved nothing on its own. The
replay is the real evidence.
