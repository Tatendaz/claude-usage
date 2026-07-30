# Feature: `--check` never echoes credential-blob values

**Branch:** fix/redact-sensitive-logging
**Date:** 2026-07-30

## Summary
`--check` printed `subscriptionType` verbatim from the keychain OAuth blob.
It now maps that value onto a closed set of known plan literals
(`pro`/`max`/`team`/`enterprise`/`free`) and describes — rather than
prints — anything unrecognized.

## Motivation
CodeQL (`py/clear-text-logging-sensitive-data`, alert #1) flagged the
self-check for logging data derived from credential storage. The repo rule
(AGENTS.md) is that nothing read from credential storage is echoed
verbatim; a malformed or attacker-shaped blob could otherwise put secret
material on stdout, which often lands in logs.

## What changed
- New `_safe_plan()` helper whitelists the plan string; unknown values
  print as `unrecognized (N chars)`.
- `run_check` uses it for the "subscription type" row.

## Notes
Future plan names will show as `unrecognized` until added to
`_KNOWN_PLANS` — a deliberate fail-closed trade. Resolves code scanning
alert #1.
