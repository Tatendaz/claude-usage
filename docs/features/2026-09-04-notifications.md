# Feature: Usage threshold notifications (terminal, desktop, phone)

**Branch:** feat/notifications
**Date:** 2026-09-04

## Summary
`bin/claude-usage` can now alert the user when a quota window crosses a
percentage. Three channels, any mix: `terminal` (the terminal's own OSC 9 /
OSC 99 notification), `desktop` (macOS `osascript`, Linux `notify-send`), and
`ntfy` (push to the free ntfy phone app). Levels come from a preset —
`standard` (50/80/90, the default), `minimal` (90 %), `early` (25/50/75/90) — or
an explicit `levels` list (the "custom" option in the setup flow). The session, the all-models week, and every per-model week
(e.g. the Fable week) are watched by default. Config lives in
`~/.config/claude-usage/config.json`; every key has a `CLAUDE_USAGE_NOTIFY*`
env override. `--notify-test [CHANNEL]` sends one test alert and reports per
channel; `--no-notify` skips alerts for a call; `--check` prints the effective
settings.

## Motivation
The status bar shows the numbers, but nobody watches a status bar at the moment
a week runs out. The user asked for 50/80/90 alerts with a way to configure
them, without overwhelming people: hence one quiet default and two named
recommendations, plus a single "where do you want it" question in the agent
runbook.

## What changed
- `bin/claude-usage`: new notifications section (config loading,
  `notify_settings`, `notify_wants`, `due_notifications`, `notify_message`,
  the three senders, `send_notification`, `maybe_notify`, `run_notify_test`).
  `get_usage()` runs `maybe_notify()` on every **fresh** fetch (cache hits never
  re-check) and gained a `notify=` parameter. Sent state is stored in the cache
  under `notified`, keyed `<bucket key>|<resets_at>`, so an alert fires once per
  window per reset and re-arms when the window resets; entries for vanished
  windows are pruned. A window first seen above several levels fires only the
  highest one. A level is recorded only after at least one channel delivered
  it, so a failed send retries on the next fresh fetch. `maybe_notify()` holds
  an `flock` on `<cache dir>/notify.lock`, re-reads the state from disk, and
  persists it itself, so two status bars refreshing in the same second cannot
  both alert (Windows has no flock and runs unlocked). Stdlib only, as before.
- Terminal channel writes to `/dev/tty`, not stdout, because status bars
  capture stdout. That means it needs a controlling terminal: prompts and the
  Claude Code statusline have one; iTerm2's status bar component and tmux's
  `#()` do not (documented; `desktop` is the recommendation there). Inside tmux
  the sequence is wrapped for passthrough. Control characters are stripped from
  the text before it goes into an escape sequence.
- ntfy uses the JSON publish endpoint (unicode-safe titles), priority 4 at
  ≥ 90 %, 5 s timeout. A push carries the topic name, the window name, the
  percentage, and the time to reset, nothing else.
- `tests/test_claude_usage.py`: 42 new tests (settings/env/file precedence,
  presets, bucket matching incl. Fable and legacy aliases, crossing/re-arm/prune
  logic, message text, OSC sequences for plain/kitty/tmux, osascript escaping,
  ntfy payload, fan-out, `get_usage` integration, state persistence across
  runs, `--notify-test` and `--no-notify`). `TestGetUsage` now also isolates
  `CONFIG_FILE` so a fresh-fetch test can never read `~/.config` or fire a
  channel; failed-delivery retry, disk-state re-read, and the lock. 177 tests
  total.
- Docs: `docs/CLI.md` (flags, env, new Notifications section), `README.md`
  (bullet plus a Notifications section), the landing page `docs/index.html`
  and its twin `docs/index.md` (new "Get an alert before it runs out" section;
  line and test counts refreshed), `AGENTS.md` (a "Notifications (optional,
  ask first)" section with the one-question flow, a custom-levels option, and
  a pointer from step 5; development note about `CONFIG_FILE` isolation).

## Notes
- Alerts only fire while something runs the CLI (a status bar or prompt). A
  launchd/systemd timer for people with no poller is a possible follow-up.
- Default preset is `standard` (50/80/90) per the user's later call; the
  first cut shipped `minimal`.
- Default channel is `terminal` per the user's call for this round; the
  `/dev/tty` limitation above is the argument for flipping the default to
  `desktop` on macOS later.
- On macOS the first `desktop` alert may need Notifications enabled for
  "Script Editor" (osascript's identity).
- iPhone: the ntfy app has a known bug where pushes silently stop and messages
  only appear when the app is opened. Reinstalling the app fixed it during
  this session; documented in CLI.md.
