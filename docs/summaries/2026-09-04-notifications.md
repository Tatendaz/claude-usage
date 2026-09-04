# Session: Usage threshold notifications

**Branch:** feat/notifications
**Date:** 2026-09-04

## Prompts
1. "I want to implement notifications for usage (notification at 50% 80% 90%
   not sure how maybe as a mac notification or terminal or notification via
   claude on the phone). something like a way to configure it also. any ideas
   or suggestions?"
2. "We need to test all three and we need a way for the end user to be able to
   configure them. So usage on the weekly usage on the fable quarter, so
   notifications for these three things. But … I don't want to overwhelm the
   user, so maybe we can have a default, a minimalist setting, and if they're
   not happy, we can make 2 other recommendations and also ask where they
   would like to receive notifications. By default, maybe we choose the
   easiest one, but for now, let's do the terminal. Let's just test all three
   for now."
3. (mid-task) "I already downloaded the app, so just give me the instructions
   on what to do in my iPhone to set it up once you're done, so that we can
   test notifications for iOS."

4. "Screenshot of notification" (lock-screen banner from the ntfy app after the
   reinstall) and "make sure to update readme and the github pages about the
   feature".
5. "I want my notifications to be custom. So maybe also add that option when
   setting it up for a user. I want to receive notifications at 50%, 80%, and
   at 90% on all three avenues, so on my phone, terminal, and desktop
   notification." then "Actually, the 50%, 80%, and 90% make that standard."

6. "switch to desktop oh and does herdr support notifications if yes add
   support for it becuase I use claude in herdr"

## Steps taken
- Read `AGENTS.md`, `bin/claude-usage` (cache, `get_usage`, `normalize`,
  `main`), the test fixtures and the docs gate. Proposed piggybacking on the
  existing status-bar polling instead of a daemon, state in the cache keyed by
  window + reset time, and three stdlib-only channels; noted that a plugin
  cannot push to the Claude phone app, so ntfy is the phone path.
- Implemented the notifications block, the `get_usage(notify=)` hook, the
  `--notify-test` / `--no-notify` flags, and the `--check` line.
- Wrote 37 tests; patched `TestGetUsage` to isolate `CONFIG_FILE`. Suite:
  172 tests, all pass. `uvx ruff@0.14.2 check bin/claude-usage tests`: clean.
- Live test from the agent's shell with a config of all three channels and a
  random ntfy topic: `desktop` ✓ (osascript), `ntfy` ✓ (HTTP 200 from
  ntfy.sh), `terminal` ✗ — the agent's subprocess has no controlling
  terminal (`/dev/tty`: Device not configured). Handed the user the exact
  command to run in their own terminal window, plus the iPhone steps
  (subscribe to the topic in the ntfy app).
- Phone pushes did not arrive at first, even for the ntfy app's own test
  button; ntfy.sh held every message (checked with `poll=1`). Traced to the
  documented ntfy iOS bug ("push notifications stop arriving with no visible
  error, the only fix is reinstalling the app", maintainer in ntfy #1680).
  The user reinstalled the app; the next `--notify-test ntfy` pushed a banner.
- Local CodeRabbit CLI review (gate item 5) on the first commit: 2 major,
  2 minor. Fixed all four: an `flock` around the read-modify-write of the
  sent state (re-read from disk, persisted under the lock); record a level
  only after a channel delivered it so failures retry; `OverflowError` on
  `inf` levels; the privacy sentence now names the reset countdown too.
- Made `standard` (50/80/90) the default preset and added a "custom" levels
  option to the AGENTS.md setup flow. Wrote the user's own config: standard,
  all three channels.
- Docs: `docs/CLI.md` (incl. the reinstall tip), `README.md` (new
  Notifications section), `docs/index.html` + `docs/index.md` (new section,
  counts refreshed), `AGENTS.md`, this pair of entries.
- PR #18 review (server-side CodeRabbit, 3 threads): XDG path wording; catch
  exceptions from the notifier so the status line always prints (plus
  tolerate junk state values); release the lock during delivery — replaced
  the single locked section with the two-phase reservation
  (`notify_pending`, 60 s expiry for abandoned reservations). Tests for each.
- Default channel flipped to `desktop` on the user's word.
- herdr: found `herdr notification show <title> --body --sound` (CLI over the
  herdr socket) and the `[ui] tab_bar_right` `command` slot in herdr's docs.
  Added the `herdr` channel (`HERDR_BIN_PATH` or `herdr` on PATH), a herdr
  section in TERMINALS.md and AGENTS.md, and put both into the user's own
  config (claude-usage channels + herdr tab bar). The live toast test hit
  `protocol_mismatch` (herdr 0.8.2 CLI vs an older running server); a herdr
  restart is the fix, left to the user because it closes every pane
  including this session.

## Decisions
- No daemon: the check runs on every fresh fetch inside `get_usage()`. Costs
  nothing on cache hits; only fires when a level is crossed.
- One alert per window per crossing, highest level only on first sight, state
  keyed by `resets_at` so it re-arms after each reset.
- Presets over a free-form UI: `standard` (default, 50/80/90) / `minimal` /
  `early`, with `levels` for anyone who wants their own (the "custom" choice
  in the setup flow).
- Default channel: `terminal` at first, as asked; after seeing that it cannot
  fire from the iTerm2 status bar the user said "switch to desktop", so the
  default is `desktop`. The `/dev/tty` requirement of `terminal` stays
  documented in CLI.md and AGENTS.md.
- `desktop` also accepts `macos` as an alias.
- ntfy via JSON publish (unicode titles), random topic generated for the user,
  privacy note in the docs (a push carries the topic name, window name,
  percentage, and reset countdown; nothing else). CodeRabbit round 3 raised
  the example generator from 32 to 128 bits (`openssl rand -hex 16`).
