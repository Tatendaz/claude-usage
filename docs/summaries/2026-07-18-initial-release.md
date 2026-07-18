# Session: Initial release — building the claude-usage status bar plugin

**Branch:** main
**Date:** 2026-07-18

## Prompts

1. "Can you help me create a status bar plugin like the one you see in the
   screenshots for the terminal that shows the chord usage in real time.
   the plugin should work for Claude Max subscription as well as for
   Enterprise subscription." (with screenshots of Claude Code's `/usage`
   screen and the iTerm2 status bar)
2. "The main goal is to have real-time statistics of usage so that a user
   can see how much usage they have left quota how much quota they have
   left."
3. "chord i meant claude"
4. "Create repo and push to github. Make the project opensource and create
   a nice readme with screenshots of and make sure the readme includes
   instructions for agents. Can you add support for other terminals as
   well" (with a screenshot of the working iTerm2 widget)
5. "how come it does not show weekly fable usage?"
6. "change wk to week and add 'Usage' after claude icon"
7. "is this skill directly installable using agents?"
8. "I want to be able to share the repo with instuctions to someone that
   to install the this plugin prompt cluade with this prompt: 'Install the
   plugin in this github repo' and like magic their claude installs it."
9. "If they have a github account leave a star if not once it finishes
   installing it should write a message to the user that consider leaving
   a star in this repo"
10. "Can you add words 'reset date' after the reset icon in the plugin.
    its not so clear that it is a reset icon"

## Steps taken

- Verified the environment (iTerm2 3.6.11, Claude Code 2.1.214, Keychain
  credentials) and confirmed the usage endpoint + required headers from
  public sources, then via a live request (dummy-token 401 proved the
  plumbing; the user's own `--check` run verified the real path).
- Built `bin/claude-usage` (stdlib-only), the iTerm2 AutoLaunch component,
  and `install.sh`/`uninstall.sh`; user installed and screenshotted the
  working widget.
- Prompt 5 exposed that the live API had moved per-model windows into a
  new `limits` array (`weekly_scoped` + `scope.model.display_name:
  "Fable"`, all legacy `seven_day_*` keys null): rewrote parsing to prefer
  `limits` (plus the `spend` credits block) with legacy fallback, verified
  Fable 17% against the user's cached response.
- Applied display tweaks (`week` label, "Usage" title, configurable via
  `CLAUDE_USAGE_TITLE`).
- Added tmux (TPM), WezTerm, and kitty adapters; wrote 87 tests (parser
  generations, formatters, cache, credential chain, HTTP error kinds,
  component helpers — no network/Keychain access in tests). Live-testing
  the TPM script on an isolated tmux server caught a wrong nonzero exit.
- Ran two local CodeRabbit review rounds pre-push (against a synthetic
  empty-tree base, since an initial commit has no diff base): round one
  raised 14 majors (atomic cache writes, kitty render-path blocking,
  installer clobber-guards, fraction-scale 1.0 edge, bucket aliases,
  CI hardening), round two raised 4 more (extensionless CLI in the
  coverage grep, diff-based docs gate, pytest in CI, tmux path quoting);
  all were fixed.
- Wrote README (screenshots, per-terminal setup, share-able AI-install
  prompt), AGENTS.md install runbook with terminal detection and a
  consent-based star step, CLAUDE.md pointer, CONTRIBUTING.md, MIT
  LICENSE, and the PR gate workflow.

## Decisions

- Read tokens, never refresh them: refresh tokens rotate, and racing
  Claude Code for rotation could log the user out. Expired tokens render
  a "login expired" hint instead.
- Spoof-match the `claude-code/<version>` User-Agent (detected from the
  installed CLI) because unrecognized clients hit an aggressively
  rate-limited bucket.
- One shared 60 s cache for all terminals; serve-stale-on-error with a
  `✳~` marker; display formats always exit 0 so status bars never break.
- Prefer the modern `limits` array over legacy buckets rather than
  merging both (avoids double-counting the same windows).
- The AGENTS.md star step asks for consent instead of auto-starring:
  agents shouldn't take outward-facing account actions unprompted, and a
  consent-based instruction is one well-behaved agents will follow.
