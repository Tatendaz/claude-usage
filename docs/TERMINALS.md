# Terminal setup

iTerm2 is covered in the [README](../README.md#iterm2-status-bar) — it's
the only one with a picker. Everything else is here.

All of these assume `./install.sh` has already put the CLI at
`~/.local/bin/claude-usage`.

## tmux

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
-- or, if you already render your own right status:
--   my_status = require('claude-usage').text()
```

## kitty (experimental)

kitty has no status bar, so this draws the quota at the right edge of the tab
bar (the community custom-tab-bar pattern):

```bash
cp ~/.claude-usage/kitty/tab_bar.py ~/.config/kitty/tab_bar.py
```

```conf
# kitty.conf
tab_bar_style custom
tab_bar_min_tabs 1
```

Already have a custom `tab_bar.py`? Merge `status_text`, `find_core`, and
`_draw_right_status` into it instead of overwriting.

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
# ~/.zshrc
claude_usage_rprompt() { RPROMPT="$(~/.local/bin/claude-usage 2>/dev/null)" }
precmd_functions+=(claude_usage_rprompt)
```

## Claude Code statusline

Merge this key into `~/.claude/settings.json` (keep your existing keys):

```json
{ "statusLine": { "type": "command", "command": "~/.local/bin/claude-usage" } }
```

## Choosing a reset style

tmux, starship, and zsh call the CLI from a config string, so the easiest way
to change how resets render is the `CLAUDE_USAGE_RESETS` environment variable
rather than a flag. See the [CLI reference](CLI.md) for the available styles.
