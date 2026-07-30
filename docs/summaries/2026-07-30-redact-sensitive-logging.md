# Session: redact credential-derived values in `--check`

**Branch:** fix/redact-sensitive-logging
**Date:** 2026-07-30

## Prompts
1. "Can you create prs fixing the stuff found in security tab for the 3 repos?" (CodeQL alerts from the 2026-07-28 security-baseline rollout; this repo: `py/clear-text-logging-sensitive-data` at `bin/claude-usage:665`)
2. "send me the links once you are done so I can merge them"

## Steps taken
- Traced the alert: `run_check` printed `meta["subscriptionType"]` straight
  from the OAuth blob returned by `load_credentials()`.
- Added `_safe_plan()` (closed whitelist + fail-closed description of
  unknown values) and switched the check row to it.
- Added `TestSafePlan` and `TestRunCheckRedaction` (mocked credentials and
  network per test conventions; asserts no `sk-ant` material on stdout).
- Ran `python3 -m unittest discover -s tests -v`.

## Decisions
- Whitelist over regex-sanitize: provably breaks the taint path and
  matches the AGENTS.md "never print credential material" rule; unknown
  plans deliberately render as `unrecognized (N chars)`.
