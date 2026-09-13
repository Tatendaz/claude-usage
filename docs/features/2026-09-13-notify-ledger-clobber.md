# Feature: Stop a fetcher's cache write from erasing the alert ledger

**Branch:** fix/notify-ledger-clobber
**Date:** 2026-09-13

## Summary
Threshold alerts still repeated when several status bars polled at the same
moment. The cache write that follows a fresh fetch now re-reads the "already
sent" ledger from disk under the notify lock instead of restoring the copy it
read before the request.

## Motivation
`get_usage` read the cache, made the network request, then wrote that same
dict back. The read happens before the request and the write after it, so the
`notified` / `notify_pending` keys in the dict were a snapshot from seconds
earlier. A sibling poller that alerted during the request had its record
overwritten, the next fetch read the alert as unsent, and it fired again.

The `notify_lock` around `maybe_notify` could not prevent this: the clobbering
write happened outside that lock, so it interleaved freely with the locked
updates. In one day this produced 121 alerts, including the same window
announced six times within a single second.

This is a second, independent cause of the storm fixed in
[reset-time jitter](2026-09-12-notify-reset-jitter.md). That one made a window
unrecognisable across polls; this one discards a record the tool had correctly
written.

## What changed
- New `save_quota(cache, data, now)` writes a fresh fetch: under `notify_lock`
  it drops the caller's `NOTIFY_LEDGER_KEYS` and takes them from the current
  file, then writes the quota payload. The caller's dict is updated to match,
  so it never carries a ledger the file has moved past.
- `get_usage` and `run_check` both write through it. They were the only two
  places that persisted a fetch.
- `notify_lock` now takes a real interprocess lock on native Windows as well.
  It used to `yield` unlocked when `fcntl` was missing, so both the alert
  ledger and this new merge were unprotected there. `_lock_file` picks
  `fcntl.flock` (Unix, WSL) or an `msvcrt` byte-range lock on the same file,
  and returns the matching unlock.
- Tests: `test_fetch_keeps_a_sibling_pollers_ledger` drives the real race
  through `get_usage` (a sibling records an alert while the request is in
  flight) and fails on the previous code. `TestSaveQuota` covers the merge,
  the empty-ledger case, and a second poller's write not re-firing an alert.

## Notes
The lock is held for a file read and a file write, never across the network
request or a delivery channel.

Review raised that the new merge leans on a lock that did nothing on native
Windows, so `notify_lock` now locks there too (see above). If the lock cannot
be taken at all — an unwritable cache directory, a platform with neither
module — the body still runs unsynchronised, because a status bar that alerts
twice beats one that stops updating.
