# Session: Clear the two open bugs before v1.3.1

**Branch:** fix/check-ntfy-blocked-and-spend-severity
**Date:** 2026-09-17

## Requests

1. "anything outstanding for this project?"
2. "go" (fix #22 and #23 in one PR, then tag v1.3.1)

## Work

Swept the repo: open PRs (none), open issues (#4, #20, #22, #23, #24), CI
runs, local branches, the release tag, and the launch kit. #22 and #23 were
still real on `main`; #24 has not fired yet; #4 and #20 are done in practice.

Fixed #23 by keeping `spend.severity` in `quota_data` under the same
three-value allowlist `limits` entries already use.

Fixed #22 by pulling the plan test out of `send_ntfy` into `ntfy_allowed`, then
using it in `run_check` to render `ntfy (blocked: unverified plan)`. Sharing
the function was the point: a second hand-written check would drift the same
way the original one did.

Added five tests (214 total), updated `docs/CLI.md` and the landing page count.

## Decisions

- Kept the marker wording aligned with the existing `--notify-test` hint rather
  than inventing new phrasing.
- Did not touch #24 in this PR. It needs a decision about branch protection
  (main requires one approval, so auto-merge cannot complete either way).
