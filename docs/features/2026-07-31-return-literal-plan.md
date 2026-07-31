# Feature: `_safe_plan` returns the whitelist literal, not the input

**Branch:** fix/return-literal-plan
**Date:** 2026-07-31

## Summary
`_safe_plan` now matches the normalized plan against `_KNOWN_PLANS` with an
equality loop and returns the tuple's own literal. Behavior is identical;
the returned object no longer originates from the credential blob.

## Motivation
Round 4 of CodeQL `py/clear-text-logging-sensitive-data` alert #1, and the
first one guided by the analysis SARIF instead of inference. The code flow
shows the taint passing straight through round 1's whitelist:
`plan if plan in _KNOWN_PLANS else …` returns `plan` itself, and a
membership test is not a taint barrier, so the credential-derived string
object reaches the `row()` print. Returning the matched literal severs the
flow at the type level: nothing that ever touched the blob is returned.

## What changed
- Equality loop over `_KNOWN_PLANS`, returning `known` (the literal).
- Regression test pinning the barrier property (`result is` one of the
  module literals).

## Notes
Verification note for this alert's history: PR-ref analyses reported 0
results on a tree identical to a main scan that reported 1 (trees
`47f1791b` on both sides of #12). PR analyses are treated as necessary but
not sufficient; the post-merge scan of main is the authority.
