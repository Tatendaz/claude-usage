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
- Ran the full suite before pushing: 121 tests, all passing, no source
  changed.

## Decisions
- **iTerm2 stays in the README; the other five terminals move out.** It's the
  only one with a picker and the only one whose setup is a UI walkthrough
  rather than two lines of config. Splitting on "flagship vs. the rest" keeps
  the README's fast path intact without duplicating anything.
- **Moved, never deleted.** Every section that left the README exists verbatim
  in `docs/` and is linked from a table at the bottom. The point was to stop
  making visitors scroll past reference material, not to have less of it.
- **Four focused pages rather than one `docs/REFERENCE.md`.** They're linked
  individually from the README table, so a visitor navigates straight to
  troubleshooting or the flag table without scanning a combined page.
- **No version bump.** The previous docs-only change bumped a patch version,
  but that release also changed what the site advertised. This one changes
  no behavior, no output, and no claims about the plugin.
- **Environment variables became a table.** They were a single 7-line
  paragraph in the README; as a table in `docs/CLI.md` each variable is
  scannable, which is the whole reason to have a reference page.
