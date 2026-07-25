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

The tmux format colors each window green / yellow / red as it fills.

## WezTerm

```bash
cp ~/.claude-usage/wezterm/claude-usage.lua ~/.config/wezterm/claude-usage.lua
```

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
