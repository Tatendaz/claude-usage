# Feature: Dependabot cooldown, zizmor in CI, merge when clean

**Branch:** security/hardening-2026-10-25
**Date:** 2026-10-25

## Summary
Adds a Dependabot config with a 7-day cooldown, a zizmor job that scans the
workflows on every PR, and the owner's merge-when-clean job. Removes the old
Dependabot auto-merge workflow.

## Motivation
The October 2026 supply-chain attacks shipped as new versions of trusted
packages and actions. A 7-day cooldown keeps Dependabot from proposing a
release in its first week, when most bad releases are caught and pulled.
`dependabot-auto-merge.yml` merged Dependabot PRs on green CI with no review;
`merge-when-clean.yml` merges them only after a real review.

## What changed
- `.github/dependabot.yml` (new): `github-actions`, monthly, `cooldown:
  default-days: 7`, one group for minor + patch, at most 3 open PRs.
  Validated against the schemastore Dependabot schema.
- `.github/workflows/zizmor.yml` (new): `pipx run zizmor==1.31.1
  --min-severity high .github/workflows`, read-only token, checkout pinned.
- `.github/workflows/merge-when-clean.yml` (new): the owner's template v3,
  unchanged. Merges Dependabot (non-major) PRs and the owner's `security/*` or
  `automerge` PRs once CI is green, a real review ran and 0 threads are open.
- `.github/workflows/dependabot-auto-merge.yml`: removed.
- `tests/test_security.py`: removed `WorkflowTests`, which ran the merge step
  of the deleted workflow.

## Notes
- No package manager in this repo (stdlib-only Python and shell), so there is no
  package-manager cooldown to set.
- Security updates skip the cooldown; that is intended.
