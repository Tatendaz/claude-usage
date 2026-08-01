# Feature: Dependabot patch/minor PRs merge themselves

**Branch:** ci/dependabot-auto-merge
**Date:** 2026-08-01 (UTC)

## Summary
Adds `.github/workflows/dependabot-auto-merge.yml`. Dependabot PRs that carry
a `semver-patch` or `semver-minor` bump are approved and merged without a
human; `semver-major` bumps are left alone, because a major can carry a
breaking change that a green CI run does not necessarily catch.

The workflow is a port of the one in `Tatendaz/Quant_Backtest_Platform`,
hardened before replication across the account's active repos.

## What changed
- **`.github/workflows/dependabot-auto-merge.yml` (new).** One job, gated on
  `github.event.pull_request.user.login == 'dependabot[bot]'` — the PR author,
  which a later pusher cannot spoof, rather than `github.actor`.
  `dependabot/fetch-metadata` (pinned to commit
  `25dd0e34f4fe68f24cc83900b1fe3fe149efef98`, v3.1.0) classifies the bump.
  Patch and minor then run an approve step and a merge step; anything else
  falls through and the PR waits.
- **Repo settings, applied alongside this PR.** `allow_auto_merge` enabled,
  and "Allow GitHub Actions to create and approve pull requests" turned on so
  the approve step can satisfy `main`'s one-review requirement.

## How the merge is gated
- `gh pr merge --auto --squash` is tried first. `main` has a required review
  but no required status checks, so if GitHub rejects `--auto` (nothing
  pending to arm against), the job falls back to polling
  `commits/<sha>/check-runs`, waiting for every sibling check to complete —
  itself excluded — and refuses to merge if any concluded as anything other
  than success, neutral or skipped. That keeps `CI` and `PR Gate` gating the
  merge even though neither is marked required on this repo.
- Both merge paths pass `--match-head-commit "$HEAD_SHA"`, pinning the merge
  to the commit this run classified. A push landing mid-run cannot merge under
  an earlier patch/minor verdict; its own `synchronize` run re-classifies it.
- `concurrency` is keyed on the PR number with `cancel-in-progress`, so a new
  push supersedes the in-flight run rather than racing it.

## Notes
`permissions` is raised to `contents: write` / `pull-requests: write` /
`checks: read`, because Dependabot-triggered runs get a read-only token by
default. Dependabot's branches live in this repo, so the elevation is the
one GitHub documents under "Automating Dependabot with GitHub Actions".

The approve step is `continue-on-error: true`. If the Actions approval
setting is ever turned back off, the merge step still runs and simply waits
on the missing review instead of failing the workflow.

Nothing the tool ships is affected — this is CI plumbing only.
