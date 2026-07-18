# Feature: Initial release — Claude quota in the terminal status bar

**Branch:** main
**Date:** 2026-07-18

## Summary
First public release: a status bar plugin that shows live Claude quota
(session, weekly, and per-model weekly windows — the same numbers as
Claude Code's `/usage` screen) in iTerm2, tmux, WezTerm, kitty, starship,
zsh, or the Claude Code statusline.

## Motivation
Claude Code only shows quota inside its own `/usage` screen. Anyone pacing
themselves against the 5-hour session window or the weekly caps has to
keep checking it manually. A status bar widget makes remaining quota
ambient — visible before starting token-heavy work.

## What changed
- `bin/claude-usage`: stdlib-only CLI — reads Claude Code OAuth
  credentials (env var → macOS Keychain → `~/.claude/.credentials.json`),
  queries `api.anthropic.com/api/oauth/usage`, caches 60 s, renders
  `text` / `iterm` / `tmux` / `long` / `json` formats, plus `--check`
  self-diagnostics and `--demo` sample rendering.
- Parses both response generations: the modern `limits` array (including
  `weekly_scoped` per-model windows such as the Fable week, and the
  `spend` credits block) and the legacy `five_hour`/`seven_day*` buckets
  with 0–1 vs 0–100 scale auto-detection.
- Terminal adapters: iTerm2 status bar component (AutoLaunch, Python API),
  TPM-compatible `claude-usage.tmux` (`#{claude_usage}` placeholder),
  `wezterm/claude-usage.lua`, experimental `kitty/tab_bar.py`, plus
  documented starship/zsh/Claude Code statusline snippets.
- `install.sh` / `uninstall.sh` (both refuse to touch files they don't
  own), `AGENTS.md` agent install runbook (with `CLAUDE.md` pointer), MIT
  license, CI gate workflow, and a test suite (87 tests; no network /
  Keychain / real-cache access).

## Notes
- The upstream endpoint is undocumented; on failure the widget degrades to
  `✳ n/a` / stale markers instead of breaking, and `normalize()` is the
  single place to adapt when the shape drifts.
- Works with claude.ai subscription auth (Pro/Max/Team/Enterprise).
  API-key/Bedrock/Vertex setups have no subscription windows to display.
- The CLI never refreshes OAuth tokens (rotation could log Claude Code
  out); an expired token renders "login expired — open claude".
