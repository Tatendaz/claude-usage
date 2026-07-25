# Feature: ignore `.scratch/`

**Branch:** chore/gitignore-scratch
**Date:** 2026-07-25

## Summary
Adds `.scratch/` to `.gitignore`. One line, preventive — no scratch file has
ever been committed to this repo, and none is sitting untracked in the
checkout today.

## Motivation
Agents working on this repo are given a `.scratch/` directory for ephemeral
files — half-written scripts, captured command output, message drafts. The
convention places it at the *workspace* root, outside any checkout, which is
why nothing has ever leaked here: `git log --all -- .scratch` is empty and
`git ls-files .scratch/` returns nothing.

The reason to add the line anyway is that nothing enforces that placement. An
agent working inside the repo can create `.scratch/` just as easily, and at
that point a single `git add -A` sweeps it into a commit. The cost of
preventing that is one line; the cost of catching it after the fact is a
history rewrite.

The pattern is deliberately unanchored. `.scratch/` matches a directory of
that name at any depth, not just the repo root, which is what the rest of this
`.gitignore` already does — `__pycache__/`, `.pytest_cache/`, and `.DS_Store`
are all unanchored for the same reason. A scratch directory is ephemeral
wherever it lands, and there is no depth at which one should be tracked here,
so `/.scratch/` would narrow the guard for no gain and make this the only
anchored line in the file.

Recorded plainly because the claim that first prompted this was wrong: during
PR #7 the scratch files were reported as "untracked in the checkout." They
were in the workspace root one level up, outside the git tree, where
`git add -A` could never have reached them. The line is still worth adding,
but as a guard against a thing that has not happened rather than a fix for one
that did.

## What changed
- `.gitignore` — added `.scratch/`.

## Notes
No behaviour change, no user-visible surface, no test impact. If a `.scratch/`
directory is ever wanted *in* the repo and tracked, this line has to come out
first.
