# Session: hardening CI around the one script nobody was testing

**Branch:** chore/ci-hardening-and-contributor-docs
**Date:** 2026-07-25

## Prompts
1. Audit this repo's CI: what it is, what the toolchain is, whether the
   tests actually run, whether shell linting is warranted, what the existing
   workflow gets wrong, and what a contributor is missing.
2. Implement the hardening: install the drafted `ci.yml`, resolve the
   duplicate `Tests` check name, fix the docs-gate injection defect, **write
   the missing shell tests with no new dependencies**, extend the coverage
   gate to cover shell, and write the contributor and community docs.

## Steps taken
- Re-read the audit rather than trusting memory of it, then re-derived the
  facts that the plan depended on: the 121-test baseline, the two `E731`
  sites, and the shape of `install.sh` / `uninstall.sh`.
- Wrote `tests/test_install.sh` before touching CI, because the audit's
  strongest finding was that the shell layer had no tests at all and the
  workflow around it was the easy half.
- **Proved the sandbox before trusting it.** The development machine had a
  real, working claude-usage install, so a leaky test would have destroyed
  something rather than a hypothetical. Ran the suite repeatedly back to back
  (dozens of `install.sh`/`uninstall.sh` invocations) inside a few seconds and
  compared **inodes**, not just checksums: the cache *directory* inode was
  unchanged, which is the direct disproof of `rm -rf` having run.
- Chased the one thing that did change. The cache file's checksum moved
  between some snapshots, which looked alarming until it traced back to a
  terminal adapter already running on the machine and polling the CLI:
  `save_cache()` writes via `tempfile.mkstemp` + `os.replace`. That is an
  atomic replace — new file inode, unchanged directory inode — exactly the
  signature observed, and not something either script under test can produce.
- Ran a negative control instead of asserting the interlock works: copied the
  suite, deliberately removed the `export HOME=...` line, and confirmed it
  aborts with exit 99 and the FATAL banner *before* executing anything.
- Proved the `ruff check .` trap empirically rather than repeating it from
  the audit: planted an `E731` in `bin/claude-usage`, confirmed
  `ruff check .` still reported "All checks passed!", confirmed the
  explicit-path invocation caught it, then restored the file and re-ran the
  suite.
- Extracted the docs-gate matcher into `.github/scripts/require-docs-entry.sh`
  so the fix could be exercised against real branch names instead of
  reasoned about, then ran the actual production script for the gate
  simulation rather than a re-implementation of it.
- Linted the workflows the way CI would: parsed both files with
  `yaml.safe_load`, then extracted every `run:` block to a temp file and ran
  `bash -n` and shellcheck over each one.

## Decisions
- **`ci.yml` owns testing; `pr-gate.yml`'s `tests` job was deleted.** Two
  files running the same suite would have burned double the minutes and
  handed branch protection two similarly-named `Tests` contexts to choose
  between. The split is now clean: `ci.yml` = correctness, `pr-gate.yml` =
  process.
- **Fixed the two `E731`s instead of shipping `--ignore E731`.** The audit
  proposed the flag so the job would be green on arrival, but a permanent
  exemption in a workflow outlives the memory of why it's there. Both were
  local helper lambdas; converting them to `def` is mechanical and both
  sites are already covered by the 121 tests. The `lint` job now runs ruff's
  defaults with nothing switched off.
- **Compared the slug with `=` rather than escaping it for `grep -E`.**
  Escaping is a pattern you can get subtly wrong forever; not building a
  regex at all cannot be. The date prefix is matched with a glob
  (`[0-9][0-9][0-9][0-9]-...`) against the filename, never against the slug.
- **No label bypass for the coverage gate.** The shared PR template offered
  a `skip-docs-gate` label, but no such logic exists in this repo's
  workflows, and shipping a template that promises a bypass which silently
  does nothing is the same class of defect this change was cleaning up. The
  template was adapted to say a maintainer decides; `main`'s protection
  already gives an admin the escape hatch.
- **`install-smoke` is macOS-only.** The audit's draft ran it on both
  runners, but once the assertions moved into `tests/test_install.sh` and the
  `shell` job ran that suite on Linux, an ubuntu leg here would have been a
  straight duplicate. macOS is the half that isn't otherwise covered, and it
  is where the platform actually shows: iTerm2 paths, and BSD rather than
  GNU `ln`/`readlink`/`stat`.
- **Documented `uninstall.sh`'s unconditional "removed cache" line rather
  than fixing it.** The task was to test these scripts, not change them; an
  asserted wart is a decision someone can revisit, an unasserted one is a
  trap.
- **Kept `tests/test_install.sh` under `tests/`** so the existing coverage
  gate's `tests/` exclusion keeps it out of the "source changed" set, and the
  new shell rule can point at `tests/*.sh` without a special case.
