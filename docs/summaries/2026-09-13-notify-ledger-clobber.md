# Session: Notification storm, second cause

**Branch:** fix/notify-ledger-clobber
**Date:** 2026-09-13

## Requests

1. "Why is Claude-usage spamming me with notifications again?"
2. "A and create a pr with the fix" (A = fix the bug rather than mute the alerts)

## Work

The user had a screen of repeated "Claude usage · 50% / 90% reached" banners a
day after the reset-time jitter fix. Traced the sender to this CLI by its title
format, then polled the configured ntfy topic for the real delivery history
rather than guessing from the banners: 121 alerts in 48 hours, up to 27 in one
hour, and six identical messages stamped the same second. Same-second
duplicates ruled out channel duplication and a window resetting, and pointed at
concurrent pollers each treating an alert as unsent.

Read the write path. `get_usage` loaded the cache, fetched, and wrote the
loaded dict back — including `notified` and `notify_pending` as they stood
before the request, and outside the lock that `maybe_notify` uses. Any alert
recorded during the request was erased.

Added `save_quota`, which merges a fresh fetch into the on-disk cache under
`notify_lock` and keeps the file's ledger keys. Routed `get_usage` and
`run_check` through it. Wrote a regression test that reproduces the race at the
real call site and confirmed it fails against main before the change.

Checked the user-facing docs: `docs/CLI.md` already claims the lock stops two
status bars from both alerting. That claim was false before this change and is
true after it, so no wording changed.

201 tests pass, `ruff==0.14.2` is clean over the CI file list, and
`py_compile` passes. Work was done in a separate worktree so the user's live
`~/.local/bin/claude-usage` symlink kept serving their status bar.

## Notes

The account's weekly windows sat at 66% (all models) and 99% (Fable), so every
configured level was crossed and each erase re-fired all of them. The storm was
loud because usage was high, but the defect is independent of usage level.

## CodeRabbit round 1

The review flagged one major finding: `save_quota` reloads and replaces the
whole cache under `notify_lock`, which yielded without locking on native
Windows, so concurrent pollers there could still lose ledger entries.

The gap predates this branch — `maybe_notify` had the same exposure and the
docstring admitted it — and `docs/index.md` lists native Windows as a planned
port rather than a supported platform. It is still real, and the fix is small,
so it was fixed rather than argued: `_lock_file` now resolves `fcntl.flock` or
an `msvcrt` byte-range lock on the same file. Four tests cover the Unix path,
the Windows fallback (via `None` in `sys.modules` to make the `fcntl` import
fail), the body still running when no lock can be taken, and alerts still
de-duplicating in that unlocked case.

## CodeRabbit round 2

One minor finding, and a fair one: `test_unix_takes_and_releases_an_flock` did a
bare `import fcntl`, which raises on the native Windows the same round had just
taught the lock to support. The test now mocks the module through `sys.modules`
like the Windows test does, so it asserts the same `LOCK_EX` / `LOCK_UN` pair on
any platform. A separate `test_real_platform_lock_round_trips`, skipped on
Windows, still runs the unmocked POSIX path.
