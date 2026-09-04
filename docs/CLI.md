# CLI reference

```text
claude-usage [--format text|iterm|tmux|long|json] [--remaining]
             [--resets countdown|inline|tail|off] [--width wide|medium|compact|mini]
             [--buckets LIST] [--all] [--ttl N] [--force] [--check] [--demo]
             [--notify-test [CHANNEL]] [--no-notify]
```

`install.sh` puts the CLI at `~/.local/bin/claude-usage` — not on macOS's
default `PATH`, so the examples below use the full path.
[Add it to `PATH`](TROUBLESHOOTING.md) to type the bare name.

## Flags

| Flag | What it does |
|---|---|
| `--format long` | `/usage`-style panel with bars and reset times |
| `--format json` | machine-readable buckets + raw API response |
| `--remaining` | show quota **left** instead of used |
| `--resets countdown` | reset style: `countdown` (`⟲ reset in 3h`), `inline` (`⟲ resets 11pm`), `tail` (grouped at the end), `off`. Default: countdown in `iterm`, off elsewhere |
| `--width wide` | print one fixed iTerm2 size instead of the full width ladder: `wide`, `medium`, `compact`, `mini` (`--format iterm` only). `wide`/`compact` honor `--resets`; `medium`/`mini` never show resets. This is what the six iTerm2 picker entries use internally |
| `--buckets session,weekly_all` | choose which windows to show (key or label) |
| `--all` | include windows hidden by default (e.g. OAuth apps) |
| `--ttl 60` / `--force` | cache lifetime / bypass the cache |
| `--check` | verbose self-check (credentials, token, endpoint, windows) |
| `--demo` | render sample data — no credentials or network needed |
| `--notify-test` | send one test alert on every configured channel and report per channel; `--notify-test ntfy` tests just one (`terminal`, `desktop`, `ntfy`, `herdr`) |
| `--no-notify` | skip the threshold alerts for this one call |

## Environment

| Variable | Effect |
|---|---|
| `CLAUDE_USAGE_TTL` | cache lifetime in seconds |
| `CLAUDE_USAGE_ICON` | the leading icon (default `✳`) |
| `CLAUDE_USAGE_TITLE` | the title word; set to `""` to hide "Usage" |
| `CLAUDE_USAGE_RESETS` | default reset style for **every** format — handy for tmux, starship, and zsh, which have no flag of their own in your config |
| `CLAUDE_USAGE_RESET_LABEL` | word after the ⟲ icon; default "reset in" for countdowns, "resets" otherwise, `""` for the bare icon |
| `CLAUDE_USAGE_BIN` | path override for terminal components |
| `CLAUDE_USAGE_DEBUG=1` | verbose diagnostics on stderr |
| `CLAUDE_USAGE_NOTIFY` | alert channels, comma-separated (`terminal`, `desktop`, `ntfy`, `herdr`), or `off` |
| `CLAUDE_USAGE_NOTIFY_PRESET` | `standard` (default), `minimal`, or `early` — see [Notifications](#notifications) |
| `CLAUDE_USAGE_NOTIFY_LEVELS` | explicit alert percentages, e.g. `50,80,90` (overrides the preset) |
| `CLAUDE_USAGE_NOTIFY_BUCKETS` | which windows alert; default `session,weekly_all,weekly_scoped` |
| `CLAUDE_USAGE_NTFY_TOPIC` / `CLAUDE_USAGE_NTFY_SERVER` | ntfy topic (required for the `ntfy` channel) and server (default `https://ntfy.sh`) |

Every `CLAUDE_USAGE_NOTIFY*` variable overrides the matching key in the config file.

## Notifications

The CLI can alert you when a window crosses a percentage. The check rides on
the polling your status bar already does: each fresh fetch compares every
window against the levels, fires **one** alert per window per crossing, and
remembers what it sent in the cache until that window resets. A level counts
as sent only once at least one channel delivered it, so a failed send is
retried on the next fresh fetch; a lock file keeps two status bars refreshing
at the same moment from both alerting. No daemon, no extra process — but
nothing polls when no status bar (or prompt) is running.

Settings live in `~/.config/claude-usage/config.json` (`$XDG_CONFIG_HOME`
honored). The defaults, spelled out:

```json
{
  "notify": {
    "preset": "standard",
    "channels": ["desktop"],
    "buckets": ["session", "weekly_all", "weekly_scoped"],
    "ntfy_topic": ""
  }
}
```

**Presets** (or set `levels` yourself, e.g. `"levels": [40, 70]`):

| Preset | Alerts at | For |
|---|---|---|
| `standard` (default) | 50, 80, 90 % | pacing a week: a heads-up, then two reminders |
| `minimal` | 90 % | one alert per window, right before it runs out |
| `early` | 25, 50, 75, 90 % | heavy users who plan the whole week |
| custom | whatever you put in `levels` | e.g. `"levels": [40, 70]` — `levels` wins over `preset` |

**Windows**: the session, the all-models week, and every per-model week
(a Fable or Opus week matches `weekly_scoped`; `fable` or
`weekly_scoped:fable` picks one). Legacy names (`five_hour`, `seven_day`)
work too.

**Channels** — pick any mix:

| Channel | What happens | Needs |
|---|---|---|
| `terminal` | the terminal shows its own system notification (OSC 9; OSC 99 on kitty) | a real terminal window: prompts (zsh, starship) and the Claude Code statusline have one, iTerm2's status bar component and tmux's `#()` do not. Inside tmux: `set -g allow-passthrough on` |
| `desktop` (alias `macos`) | macOS notification via `osascript`; `notify-send` on Linux | macOS: allow notifications for **Script Editor** the first time |
| `herdr` | a toast inside [herdr](https://herdr.dev), the agent multiplexer, via `herdr notification show`; herdr's own `[ui.toast] delivery` decides whether that is an in-app toast, an outer-terminal notification, or an OS one | herdr installed with its server running. Works from anywhere on the machine, status bars included |
| `ntfy` | push to your phone through [ntfy](https://ntfy.sh) (free app, iOS + Android) | `ntfy_topic` set to a topic name you subscribe to in the app. Each push sends the topic name, the window name, the percentage, and the time to reset to `ntfy_server` (nothing else); anyone who knows the topic can read the alerts, so use a long random one (`claude-usage-$(openssl rand -hex 16)`) or run your own server |

Test the setup any time:

```console
$ ~/.local/bin/claude-usage --notify-test
claude-usage notification test
  · config: /Users/you/.config/claude-usage/config.json
  · preset: standard  levels: 50%, 80%, 90%
  · windows: session, weekly_all, weekly_scoped
  · channels: desktop, ntfy
  ✓ desktop
  ✓ ntfy
notification test passed (CLAUDE_USAGE_DEBUG=1 for details)
```

**iPhone pushes stop arriving?** That is a [known ntfy app bug](https://docs.ntfy.sh/known-issues/):
messages show up only when you open the app. Delete and reinstall the ntfy
app, subscribe to the topic again, then run `--notify-test ntfy`. Messages
sent before you subscribed never push; they only appear in the app's list.

Turn everything off with `"enabled": false` in the file or
`CLAUDE_USAGE_NOTIFY=off`. `--check` prints the effective notify settings.

## Sample output

```console
$ ~/.local/bin/claude-usage --format long
Claude usage  (updated 12s ago)
Current session            ██░░░░░░░░░░░░░░░░░░░░░░   8% used
                            resets 4:30pm (in 2h)
Current week (all models)  ██░░░░░░░░░░░░░░░░░░░░░░  10% used
                            resets Jul 21 1:00pm (in 3d)
Current week (Fable)       ████░░░░░░░░░░░░░░░░░░░░  17% used
                            resets Jul 21 1:00pm (in 3d)
```

## Exit codes

The CLI exits 0 even when it has no data — a status bar must never break on a
failed poll. Read the `error` field of `--format json` to detect trouble
programmatically. Only `--check` signals failure through its exit code.

See also: [How it works](HOW_IT_WORKS.md) · [Troubleshooting](TROUBLESHOOTING.md) ·
[AGENTS.md](../AGENTS.md) for the full JSON contract.
