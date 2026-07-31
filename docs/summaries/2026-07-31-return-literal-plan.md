# Session: SARIF-guided fix of the whitelist taint pass-through (round 4)

**Branch:** fix/return-literal-plan
**Date:** 2026-07-31

## Prompts
1. "Can you create prs fixing the stuff found in security tab for the 3 repos?"
2. "merged pr12" — after which the merge-commit scan still reported the
   alert, on a tree identical to the PR head that had scanned clean.

## Steps taken
- Compared trees (`git rev-parse <sha>^{tree}`): main and PR head identical,
  so PR-ref results can differ from main results on the same code.
- Downloaded the main analysis SARIF and read the code flow: source is the
  keychain OAuth blob, and the surviving path runs through `_safe_plan`'s
  `plan if plan in _KNOWN_PLANS` expression, which returns the tainted
  input object.
- Replaced it with an equality loop returning the tuple literal; added a
  test pinning the returned-object-is-a-module-literal property.
- Ran the suite; PR verification via SARIF results plus post-merge main
  scan before closing the alert.

## Decisions
- SARIF first, fix second: three earlier rounds fixed real (if lesser)
  leaks but were aimed by inference. The code flow would have pointed at
  the exact expression on day one.
- Keep rounds 2 and 3 (source labels, epoch rebuild): the SARIF confirms
  those flows are gone; they were real hygiene wins, not wasted motion.
