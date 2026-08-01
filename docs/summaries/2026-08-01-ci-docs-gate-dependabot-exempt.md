# Session: Docs gate — Dependabot exemption

**Branch:** ci/docs-gate-dependabot-exempt
**Date:** 2026-08-01 local (2026-08-01 UTC)

## Prompts
1. "Can you enable auto merge for dependabot PRs on my top 21 repos and port the dependabot-auto-merge.yml — do a review and just automerge the PR you create."

## Steps taken
Audited all docs gates after the auto-merge rollout; this repo's gate lacked a Dependabot exemption, which would park every future Dependabot PR against the auto-merge fallback's failed-check refusal. Added the same job-level exemption familytreeapp uses.

## Decisions
Job-level `if` on the docs-gate only; the other gate jobs pass naturally on lockfile-only bumps.
