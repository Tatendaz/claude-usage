# Feature: Docs gate — Dependabot exemption

**Branch:** ci/docs-gate-dependabot-exempt
**Date:** 2026-08-01 local (2026-08-01 UTC)

## Summary
The docs gate now skips PRs authored by `dependabot[bot]`, matching the convention already used in familytreeapp and langchain-fde-curriculum.

## Motivation
The new account-wide Dependabot auto-merge workflow refuses to merge while any sibling check is red. Bots cannot write docs entries, so without this exemption every Dependabot PR would fail the gate and park forever.

## What changed
- `.github/workflows/pr-gate.yml`: the docs-gate job gains `if: github.actor != 'dependabot[bot]'` (on promptups, combined with the existing `pull_request` event guard).

## Notes
Human and agent PRs are unaffected.
