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

## Decisions
- No daemon: the check runs on every fresh fetch inside `get_usage()`. Costs
  nothing on cache hits; only fires when a level is crossed.
- One alert per window per crossing, highest level only on first sight, state
  keyed by `resets_at` so it re-arms after each reset.
- Presets over a free-form UI: `standard` (default, 50/80/90) / `minimal` /
  `early`, with `levels` for anyone who wants their own (the "custom" choice
  in the setup flow).
- Default channel `terminal`, as asked. Its `/dev/tty` requirement is written
  down in CLI.md, AGENTS.md and the feature entry with `desktop` as the
  recommendation for status-bar-only setups.
- `desktop` also accepts `macos` as an alias.
- ntfy via JSON publish (unicode titles), random topic generated for the user,
  privacy note in the docs (a push carries the topic name, window name,
  percentage, and reset countdown; nothing else). CodeRabbit round 3 raised
  the example generator from 32 to 128 bits (`openssl rand -hex 16`).
