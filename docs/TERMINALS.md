# Terminal setup

iTerm2 is covered in the [README](../README.md#iterm2-status-bar) — it's
the only one with a picker. Everything else is here.

All of these assume `./install.sh` has already put the CLI at
`~/.local/bin/claude-usage`.

## tmux

Already have a `status-right`? These lines **replace** it. Keep yours and drop
the placeholder into it instead — `#{claude_usage}` with TPM,
`#(~/.local/bin/claude-usage --format tmux)` without.

With [TPM](https://github.com/tmux-plugins/tpm):

```tmux
set -g @plugin 'Tatendaz/claude-usage'
set -g status-right '#{claude_usage} | %H:%M '
set -g status-interval 30
```

Without TPM:

```tmux
set -g status-right '#(~/.local/bin/claude-usage --format tmux) | %H:%M '
set -g status-interval 30
```

The tmux format colors each quota percentage green / yellow / red as it fills.
(Quota windows — the session and weekly ones. It does not touch your tmux
windows.)

## WezTerm

```bash
mkdir -p ~/.config/wezterm
cp ~/.claude-usage/wezterm/claude-usage.lua ~/.config/wezterm/claude-usage.lua
```

Unlike the kitty file below, this one is ours and overwriting it on a re-run is
the point — that is how you pick up a new version. If you edited it yourself,
copy your changes out first.

```lua
-- wezterm.lua
require('claude-usage').setup()
```

`setup()` owns the right status area. Use it **or** the handler below, not
both. If you already render your own right status, drop `setup()` and call
`text()` from inside your own handler — it has to run on every event, or the
number freezes at whatever it was when your config loaded:

```lua
local wezterm = require 'wezterm'
wezterm.on('update-right-status', function(window, _)
  local mine = wezterm.strftime('%H:%M')   -- replace with whatever you render
  window:set_right_status(mine .. '  ' .. require('claude-usage').text())
end)
```

## kitty (experimental)

kitty has no status bar, so this draws the quota at the right edge of the tab
bar (the community custom-tab-bar pattern).

kitty allows exactly one `tab_bar.py`, so `-n` refuses to clobber one you
already wrote. It copies silently, and skips silently — so check the file
rather than the exit status, which differs between BSD and GNU `cp`:

```bash
mkdir -p ~/.config/kitty
cp -n ~/.claude-usage/kitty/tab_bar.py ~/.config/kitty/tab_bar.py
grep -q _draw_right_status ~/.config/kitty/tab_bar.py \
  && echo "ready" || echo "yours was left alone — merge instead"
```

If it said merge, copy `status_text`, `find_core`, and `_draw_right_status`
out of `~/.claude-usage/kitty/tab_bar.py` into your own file by hand.

```conf
# kitty.conf
tab_bar_style custom
tab_bar_min_tabs 1
```

## herdr

[herdr](https://herdr.dev) is the agent multiplexer; its tab bar has a slot
that runs a command on an interval and shows the last line. In
`~/.config/herdr/config.toml`, add one `command` entry to the `tab_bar_right`
array under your existing `[ui]` table (TOML rejects a second `[ui]` header,
and a new `tab_bar_right` would replace the entries you already have):

```toml
[ui]
tab_bar_right = [
  { type = "command", command = "~/.local/bin/claude-usage", interval_seconds = 30, timeout_seconds = 15 },
  { type = "datetime", format = "%H:%M" },   # keep whatever was there
]
tab_bar_right_separator = " · "
```

Then `herdr config check`, then `herdr server reload-config`. The slot is plain text, so leave the
format at the default `text`. Alerts can land inside herdr too: put `herdr`
in the notification channels (see the [CLI reference](CLI.md#notifications)).

## starship

```toml
# ~/.config/starship.toml
[custom.claude_usage]
command = "~/.local/bin/claude-usage"
when = true
format = "[$output]($style) "
```

## Plain zsh (works in any terminal)

```zsh
# ~/.zshrc — appends to whatever RPROMPT you already have
claude_usage_rprompt() {
  : ${_claude_usage_base=$RPROMPT}   # your own RPROMPT, captured once
  RPROMPT="${_claude_usage_base:+$_claude_usage_base }$(~/.local/bin/claude-usage 2>/dev/null)"
}
precmd_functions+=(claude_usage_rprompt)
```

The capture has to happen inside the function: `precmd` runs after the rest of
your `.zshrc`, so reading `RPROMPT` any earlier would miss a prompt set below
this snippet.

## Claude Code statusline

Merge this key into `~/.claude/settings.json` (keep your existing keys):

```json
{ "statusLine": { "type": "command", "command": "~/.local/bin/claude-usage" } }
```

## Choosing a reset style

tmux, starship, and zsh call the CLI from a config string, so the easiest way
to change how resets render is the `CLAUDE_USAGE_RESETS` environment variable
rather than a flag. See the [CLI reference](CLI.md) for the available styles.

In tmux, set it on the server rather than in your shell. tmux runs status
commands from the server, which keeps the environment it was started with — so
an export added to `~/.zshrc` afterward does nothing until tmux restarts:

```bash
tmux set-environment -g CLAUDE_USAGE_RESETS inline
```

## iTerm2 status bar

Not on iTerm2? Skip to [tmux and other terminal integrations](#tmux).

`install.sh` already placed the component — these three steps are one-time:

1. **Settings → General → Magic → Enable Python API** (accept the Python
   runtime download if offered).
2. **Scripts → AutoLaunch → ClaudeUsage.py** to start it now (auto-starts
   with iTerm2 from then on).
3. **Settings → Profiles → Session → Status bar enabled → Configure Status
   Bar** → drag the **Claude Usage** entry you want into the row. Not seeing
   them? Scroll down — script components sit below the built-in ones.

You should now see `✳ Usage 5h 8% …` in the bar. Nothing there? →
[Troubleshooting](TROUBLESHOOTING.md).

Six entries, widest first. Each capture is a real status bar — the green
outline marks the component.

**Wide · Countdown** — the default. Labels, percentages, and how long until
each window resets.

![Wide · Countdown in the iTerm2 status bar](img/picker-wide-countdown.png)

**Wide · Inline** — same information, but resets as wall-clock times
(`⟲ resets 11pm`) instead of countdowns.

![Wide · Inline in the iTerm2 status bar](img/picker-wide-inline.png)

**Medium** — labels and percentages, no reset times.

![Medium in the iTerm2 status bar](img/picker-medium.png)

**Compact · Countdown** — drops the labels and the word "Usage", keeping
percentages and bare countdown marks (`47% ⟲3h`). About a third the width of
Wide.

![Compact · Countdown in the iTerm2 status bar](img/picker-compact-countdown.png)

**Compact · Inline** — the compact layout with clock times.

![Compact · Inline in the iTerm2 status bar](img/picker-compact-inline.png)

**Mini** — three percentages and nothing else, for a bar that's already full.

![Mini in the iTerm2 status bar](img/picker-mini.png)

Wide and Compact show each window's reset; windows that reset together — the
weeklies usually do — share one mark. Medium and Mini have no room for
resets. Two more styles, `tail` and full-width `off`, are available outside
the picker via `--resets` — see [the CLI reference](CLI.md).

*Upgrading from v1.0.0 and already had **Claude Usage** in your bar? It's
**Wide · Countdown** now — same identifier, nothing to re-add.*

## Notifications

Enterprise and unverified subscriptions cannot use ntfy. Use a local channel
instead. See [subscription restrictions](CLI.md#notifications).

The status bar already polls; the alerts ride on that. Each fresh fetch
compares the session, the week, and every per-model week (your Fable week,
say) against the levels and fires **one** alert per window per crossing. It
remembers what it sent until that window resets, so you are never nagged.

Three channels, any mix:

| Channel | What you get |
|---|---|
| `terminal` | the terminal's own notification (iTerm2, WezTerm, kitty, ghostty). Needs a real terminal window: prompts and the Claude Code statusline have one, the iTerm2 status bar component and tmux `#()` do not |
| `desktop` | a macOS notification (Linux: `notify-send`). The default |
| `herdr` | a toast inside [herdr](https://herdr.dev) if you run your agents there |
| `ntfy` | a push to your phone through the free [ntfy](https://ntfy.sh) app, iOS and Android |

Default levels are 50, 80, 90 % (`standard`). `minimal` is 90 % only,
`early` adds 25 and 75, or set your own `levels`. Configure it in
`~/.config/claude-usage/config.json` (or under `$XDG_CONFIG_HOME` if you set it):

```json
{
  "notify": {
    "preset": "standard",
    "channels": ["desktop", "ntfy"],
    "ntfy_topic": "claude-usage-8f3a19c2d4e6b7a1f0c9e8d7b6a5f4e3"
  }
}
```

Then check every channel at once:

```bash
~/.local/bin/claude-usage --notify-test
```

For the phone: install ntfy, subscribe to your topic name, done. Anyone who
knows the topic can read the alerts, so make it long and random
(`claude-usage-$(openssl rand -hex 16)`). The full
reference — env overrides, `--no-notify`, what leaves your machine, the
known ntfy iOS quirk — is in [the CLI reference](CLI.md#notifications).
