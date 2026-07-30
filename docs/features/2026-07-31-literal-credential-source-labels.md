# Feature: `--check` describes the credential source with fixed labels

**Branch:** fix/literal-credential-source-labels
**Date:** 2026-07-31

## Summary
The "credentials found (…)" row now prints one of four fixed labels —
`keychain`, `environment (CLAUDE_USAGE_TOKEN)`,
`environment (CLAUDE_CODE_OAUTH_TOKEN)`, `credentials file` — selected by
comparison, instead of echoing the `source` value returned by
`load_credentials()`.

## Motivation
Round 2 of CodeQL `py/clear-text-logging-sensitive-data` alert #1: the
post-merge scan of #10 kept the alert open because `source` is co-returned
with the token, so anything derived from it counts as credential-storage
data. Printing the credentials-file path in check output was also a mild
info leak in its own right.

## What changed
- `run_check` maps `source` onto comparison-selected literals before
  printing.
- New regression test: a credentials-file path never appears in `--check`
  output.

## Notes
Output for file-based credentials no longer shows the exact path — a
deliberate trade. Verified against the PR's own CodeQL analysis before
merge.
