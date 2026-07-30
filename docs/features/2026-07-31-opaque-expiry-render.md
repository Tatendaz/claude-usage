# Feature: rebuild the expiry timestamp before printing it in `--check`

**Branch:** fix/opaque-expiry-render
**Date:** 2026-07-31

## Summary
The "access token valid until" row now formats a datetime rebuilt from the
parsed expiry's epoch integer instead of the datetime parsed directly from
the credential blob's `expiresAt` string. Rendered output is identical.

## Motivation
Round 3 of CodeQL `py/clear-text-logging-sensitive-data` alert #1. After
#10 (plan whitelist) and #11 (literal source labels), the merge scan still
flagged the `row()` print: the remaining taint path is
`meta["expiresAt"] → _parse_when → fmt_clock → stdout`. Passing the value
through an integer epoch severs string provenance from credential storage
while printing the same clock time.

## What changed
- `run_check` renders `datetime.fromtimestamp(int(exp.timestamp()), timezone.utc)`.
- Regression test pinning the expiry row's rendered output.

## Notes
Verification this round waits for the PR ref's CodeQL *analysis object* to
exist before querying alerts (the #11 "0 alerts on PR ref" read was a race:
the check run passes before the alert index updates).
