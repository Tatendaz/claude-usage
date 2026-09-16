# Feature: Show blocked ntfy in --check, keep spend severity in JSON

**Branch:** fix/check-ntfy-blocked-and-spend-severity
**Date:** 2026-09-17

## Summary
`--check` now marks the ntfy channel as `ntfy (blocked: unverified plan)` when
the plan policy would refuse to push, and `--format json` reports the real
severity of the extra usage credits bucket instead of `null`.

## Motivation
Two leftovers from the security hardening in #21.

Issue #22: `send_ntfy` refuses enterprise, unknown, and env-token plans, but
`--check` still listed ntfy as a plain channel. A user on a blocked plan saw
ntfy "on", got no phone alerts, and had no hint why.

Issue #23: `quota_data` allowlisted `spend` down to `enabled` and `percent`,
while `_from_limits` still read `spend.severity` for the credits bucket. The
JSON output therefore always showed `"severity": null` for credits, even when
the API sent `warning` or `critical`.

## What changed
- `ntfy_allowed(meta)` holds the one plan test; `send_ntfy` and `run_check`
  both call it, so the two can no longer drift apart. `NTFY_PLANS` names the
  allowed plans.
- `run_check` renders `ntfy (blocked: unverified plan)` when that test fails.
  The wording matches the `--notify-test` hint.
- `quota_data` keeps `spend.severity` when it is one of `normal`, `warning`,
  `critical`, the same rule already used for `limits` entries.
- Tests: verified plans list ntfy plainly; env token and enterprise mark it
  blocked; spend severity survives the allowlist; an unknown severity is
  dropped. 214 tests.
- Docs: `docs/CLI.md` mentions the blocked marker; landing page test count.

## Notes
Closes #22 and #23. No behavior change for delivery itself: the plan policy
was already enforced in `send_ntfy`; this only makes it visible.
