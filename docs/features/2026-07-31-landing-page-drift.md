# Feature: correct three drifted claims on the landing page

**Branch:** docs/landing-page-drift
**Date:** 2026-07-31

## Summary
The "How it works" panel on `docs/index.html` stated a line count, a test
count, and a cache duration that no longer matched the code. All three are
now correct.

## Motivation
Found by checking the live site against the running code after v1.1.1
shipped. Two of the three drifted *because of* v1.1.1: the credential
redaction work and its regression tests grew the core past the numbers the
page advertised, and nothing recomputes them.

The third is a gap in the v1.1.1 staleness sweep itself. Commits `d3f14d4`
and `e6147ca` corrected the "60-second cache" claim in `README.md`,
`AGENTS.md`, and `docs/HOW_IT_WORKS.md` — all three now say the 60 s is a
default — but `docs/index.html` was never brought in line, so the landing
page was the last place still promising a fixed number the code treats as
overridable.

## What changed
- `docs/index.html`, "One readable file": `~790 lines` → `~830 lines`
  (actual 827) and `121 tests` → `128 tests` (actual 128).
- `docs/index.html`, "One shared cache": the flat "A 60-second on-disk
  cache" becomes "60 seconds by default, tunable with
  `CLAUDE_USAGE_TTL`", matching how every other page words it and what
  `DEFAULT_TTL` at `bin/claude-usage:40` actually does.

## Notes
No code changed, so no version bump — this rides along to the next release
rather than justifying a v1.1.2 for three numbers.

Hand-maintained counts will drift again; the durable fix is a CI check that
recomputes them and fails when the page disagrees. Not done here, since it
is a build change rather than a docs correction, but worth doing before the
numbers are quoted in a third place.

Left alone deliberately: the FAQ answers "which plans" with "Pro, Max,
Team, and Enterprise", while `_KNOWN_PLANS` also recognizes `free`. Whether
free accounts are returned any quota windows is a product fact this repo's
code does not settle, so changing the claim would be guessing.
