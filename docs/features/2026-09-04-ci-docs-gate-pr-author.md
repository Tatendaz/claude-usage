# Feature: Docs gate binds to the PR author, not the run actor

**Branch:** ci/docs-gate-pr-author
**Date:** 2026-09-04 local (2026-09-04 UTC)

## Summary
The `docs-gate` job in `.github/workflows/pr-gate.yml` now stands down when the
pull request *author* is `dependabot[bot]` (`github.event.pull_request.user.login`),
instead of when the run *actor* is (`github.actor`). Dependabot bumps keep
skipping the docs requirement no matter who last touched the branch.

## Motivation
`github.actor` is whoever triggered the current run. Pressing "Update branch"
on a Dependabot PR starts a new `pull_request: synchronize` run whose actor is
the human who clicked, the skip stops firing, and the gate demands docs entries
a bump PR will never have. (A plain re-run keeps the original actor; the person
re-running only shows up as `github.triggering_actor`.) This failure mode was
seen live on langchain-fde-curriculum #9 (a cryptography bump went red on the
docs gate after an "Update branch" push and was blocked by the required check
until Dependabot recreated the branch). The PR author is fixed for the life of
the PR, so it is the right handle.

## What changed
- `.github/workflows/pr-gate.yml`: the `docs-gate` condition is now
  `if: github.event.pull_request.user.login != 'dependabot[bot]'`, with a
  comment explaining why the author, not the actor, is the right handle.
- Nothing else in the file.

## Notes
- The author check is also the one GitHub's Dependabot automation guidance
  recommends: a later pusher can change the actor, but not the PR author.
- Human and agent PRs are unaffected — their author is never `dependabot[bot]`,
  so the docs gate still runs and still requires both entries.
- Rolled out from langchain-fde-curriculum #11, where the identical diff was
  reviewed.
