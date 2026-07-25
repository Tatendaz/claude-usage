# Session: slimming the README down to the fast path

**Branch:** docs/readme-slim
**Date:** 2026-07-25

## Prompts
1. "I have a some repos that I think have some over complicated readmes can
   you help?"
2. "do claude-usage and open a PR. Render the markdown from me in the browser
   or somewhere to see what you have done. I still want to keep screenshots
   of the different Claude usage menu bars, so that is important. The rest is
   up to you. Maybe instructions for agents can be a link to the agents.md
   file, if any, or something. The rest is up to you."
3. "text color is not visible maybe just a render issue" (with a screenshot of
   the preview page)
4. "also make sure the text is noce maybe ask Honey-copy to take a look as I
   want someone who comes here to quickly understand the product and install
   easily with no issues."
5. "coderabbit retuned with things to fix always watch for comments after. why
   did you stop checking?"
6. "you can fix the CLI reference also"

## Steps taken
- Measured every README across the account rather than guessing which were
  bloated — lines, words, heading count, badges, and table rows. `claude-usage`
  came second worst at 316 lines / 1,763 words / 22 headings, behind
  `langchain-fde-curriculum`; the user picked it to go first.
- Split the README by asking of each section: does a stranger need this to
  decide whether to install, or to get it running? Everything answering "no"
  moved to `docs/` — CLI reference, five terminals' configs, internals,
  troubleshooting.
- Kept all six iTerm2 picker captures and tightened only the prose around
  them. The gallery was 54 lines for 6 images; the images were never the
  problem.
- Grepped the whole tree for references to README anchors before committing.
  Found one: `docs/index.html` linked to `#pick-your-terminal`, which this
  change removes. Repointed it at `docs/TERMINALS.md`.
- Resolved every relative link in the README and the four new pages against
  the working tree — all fourteen README targets and all ten docs targets
  exist.
- Rendered the result through GitHub's own `/markdown` API into a tabbed
  local page (new README, old README, and the four new pages, images inlined
  as data URIs) and served it in the browser for review before opening the PR.
- Rebuilt the preview after the user reported unreadable text. The cause was
  the combined `github-markdown.css`, which flips text colour on
  `prefers-color-scheme: dark` while the page's card background stays
  hardcoded light — so on a Mac in dark mode the README rendered near-white
  text on white. Replaced it with the light and dark stylesheets fetched
  separately and each scoped under `[data-theme]`, plus an explicit toggle, so
  no media query can desynchronise text from background. Verified by
  screenshotting both themes headlessly, including with the OS dark preference
  forced.
- Took a copy review of the rewrite, which caught the install bug below and a
  set of line-level tightenings; applied them.
- Swept the whole tree for bare-name invocations rather than trusting the
  review's "only the README" claim, with a grep that ignores `~/`-prefixed and
  backticked matches. That is what turned up `install.sh`, three files after
  the ones already fixed.
- Verified by running rather than reading, after a round where checking a
  file's claims instead of its behaviour let two broken snippets through:
  executed `install.sh` and read its real output, and ran
  `--demo --format long` to confirm the documented sample still matches.
- Ran the full suite before pushing: 121 tests, all passing.

## Decisions
- **iTerm2 stays in the README; the other five terminals move out.** It's the
  only one with a picker and the only one whose setup is a UI walkthrough
  rather than two lines of config. Splitting on "flagship vs. the rest" keeps
  the README's fast path intact without duplicating anything.
- **Moved, never deleted.** Every section that left the README exists in full
  in `docs/` and is linked from a table at the bottom. The point was to stop
  making visitors scroll past reference material, not to have less of it. Not
  quite verbatim, though — the environment variables became a table, and the
  runnable lines were corrected once the bare-name bug surfaced. Content
  preserved, wording not frozen.
- **Four focused pages rather than one `docs/REFERENCE.md`.** They're linked
  individually from the README table, so a visitor navigates straight to
  troubleshooting or the flag table without scanning a combined page.
- **No version bump.** The previous docs-only change bumped a patch version,
  but that release also changed what the site advertised. This one changes
  no behavior, no output, and no claims about the plugin.
- **Environment variables became a table.** They were a single 7-line
  paragraph in the README; as a table in `docs/CLI.md` each variable is
  scannable, which is the whole reason to have a reference page.
- **Every runnable line now calls the CLI by full path.** The copy review
  found that `claude-usage --check`, the line right after `./install.sh`,
  could not have worked on a clean Mac: `install.sh` symlinks into
  `~/.local/bin` and deliberately never edits shell rc files, and that
  directory is not in `/etc/paths`. The review said the README was the only
  file making that assumption; that was wrong, and taking it at face value
  left three more in place for a round. `docs/CLI.md`'s sample, the
  "Reading quota programmatically" block in `AGENTS.md`, and — the one that
  actually reaches every user — step 4 of the "Next steps" `install.sh`
  prints on success, which handed you a failing command seconds after
  reporting that it worked. All of them, plus `docs/index.html` and both
  runnable blocks in `docs/TROUBLESHOOTING.md`, now use the full path, with a
  `PATH` export
  offered rather than required — the installer's not touching shell config is
  intentional. The one place the bare name stays is `docs/CLI.md`'s synopsis
  block: that is the command's name and its grammar, not a line to copy, and
  a 24-character path prefix would push its three aligned lines to five. A
  note directly under it says where the CLI lives and why the examples below
  spell the path out.
- **The `/usage` capture is in two places on purpose.** It illustrates the
  parsing description in `docs/HOW_IT_WORKS.md`, and it is also the README's
  argument: it is the only capture showing the data this tool surfaces, which
  is the pitch. Duplicating one image is cheaper than explaining it in prose.
- **The iTerm2 section is named for its terminal.** "Pick your look (iTerm2)"
  made roughly half of readers scroll a 45-line gallery to learn it was not
  for them. "iTerm2 status bar" plus a skip link to `#other-terminals` lets
  them leave immediately.
- Chased the PR-side review when it went quiet: mapped every submitted review
  to its commit SHA and found the newest pointed at `e6147ca` while the head
  was two commits further on. Both `@coderabbitai review` and `full review`
  had replied "Action performed" without submitting anything, because
  automatic reviews were paused. Resumed them and re-triggered; the review
  that eventually landed carried a major finding, so the silence had been
  hiding real problems rather than confirming their absence.
- Verified all three of that review's findings by execution rather than
  reading: drove `get_usage()` with a stubbed 429 to prove no backoff exists,
  tested `cp -n` in both the file-exists and file-absent cases to establish
  that it is silent either way, and syntax-checked the corrected WezTerm Lua
  with `luac -p`.
- Got caught generalising from one machine. The `cp -n` fix documented the
  exit status as the way to tell a copy from a skip, which is true for BSD
  `cp` and wrong for GNU — a Linux kitty user would have read the opposite of
  the truth. The local review flagged it. The rule that survives: running a
  command proves what it does *here*, and a doc claim needs to hold wherever
  the reader is. Now the doc greps the installed file for
  `_draw_right_status`, which is the same answer on every platform.
