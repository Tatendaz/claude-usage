<div align="center">

# 🕐 claude-usage

**Your Claude quota, live in the terminal status bar.**

Know how much you have left before you start something big — no `/usage`
check, no surprise mid-task. Every window Claude Code tracks: the 5-hour
session, the weekly, and per-model weeklies.

![claude-usage in the iTerm2 status bar](docs/img/picker-wide-countdown.png)

```text
✳ Usage 5h 8% ⟲ reset in 2h · week 10% · fable 17% ⟲ reset in 3d
```

It reads the same data Claude Code shows here:

<img src="docs/img/claude-usage-screen.png" width="640" alt="Claude Code /usage screen">

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python: stdlib only](https://img.shields.io/badge/python-3.9%2B%20·%20zero%20deps-3776AB.svg)](bin/claude-usage)
[![Terminals](https://img.shields.io/badge/iTerm2%20·%20tmux%20·%20WezTerm%20·%20kitty%20·%20starship-supported-brightgreen.svg)](docs/TERMINALS.md)

</div>

## Install

**Before you start:** you need to be logged into Claude Code with a claude.ai
account — any plan. (API key, Bedrock, and Vertex setups have no quota to
report.)

**With an AI agent** — paste this into Claude Code (or any coding agent):

> **Install the plugin from https://github.com/Tatendaz/claude-usage**

It reads [`AGENTS.md`](AGENTS.md), installs the CLI, detects your terminal,
wires it up, and verifies the result. The only thing it can't do is drag the
widget into iTerm2's status bar — it will tell you when.

**By hand:**

```bash
git clone https://github.com/Tatendaz/claude-usage.git ~/.claude-usage
cd ~/.claude-usage
./install.sh                       # CLI → ~/.local/bin, iTerm2 component → AutoLaunch
~/.local/bin/claude-usage --check  # verifies credentials + endpoint end-to-end
```

`~/.local/bin` isn't on macOS's default `PATH`. To type `claude-usage` bare:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

First run may pop a macOS Keychain dialog — click **Always Allow**, not
"Allow", or it asks again every refresh.

## What you get

- **Live quota** — session, weekly, and per-model windows with reset times,
  polled every 30 s through one shared cache, 60 s by default.
- **Every claude.ai plan** — whatever windows your plan has, you see. A Fable
  or Opus week shows up on its own; nothing to configure.
- **Zero dependencies** — one stdlib-only Python file. Everything else is a
  thin adapter.
- **Alerts, if you want them** — a terminal, macOS, or phone (ntfy) alert
  at 50, 80, and 90 % of each window, once per crossing per reset. See
  [Notifications](#notifications) below.
- **Fails honestly** — offline, it shows your last good numbers marked `✳~`;
  an expired login says so instead of showing zeros; `!` flags any window
  ≥ 90 % full.

## Terminal setup and notifications

For iTerm2 setup and the width gallery, see [terminal setup](docs/TERMINALS.md#iterm2-status-bar).
Local alerts and optional phone alerts are covered in the [CLI reference](docs/CLI.md#notifications).
Enterprise subscriptions cannot use ntfy. Missing or unknown subscription
metadata, including token-only login, also blocks ntfy; local alerts still work.
See [enterprise deployment](docs/ENTERPRISE.md) before a corporate rollout.

## Other terminals

tmux, WezTerm, kitty, starship, plain zsh, and the Claude Code statusline are
each a two-line setup — see **[docs/TERMINALS.md](docs/TERMINALS.md)**.

## Documentation

| | |
|---|---|
| [CLI reference](docs/CLI.md) | every flag, environment variable, and output format |
| [Terminal setup](docs/TERMINALS.md) | tmux, WezTerm, kitty, starship, zsh, statusline |
| [How it works](docs/HOW_IT_WORKS.md) | credentials, the endpoint, parsing, caching |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | what each `✳` message means and how to fix it |
| [AGENTS.md](AGENTS.md) | install runbook and JSON contract, written for AI agents |
| [CONTRIBUTING.md](CONTRIBUTING.md) | tests, docs gate, and the stdlib-only rule |

## Uninstall

```bash
~/.claude-usage/uninstall.sh   # removes the CLI link, iTerm2 component, and cache
```

---

If this plugin is useful, consider leaving a ⭐ — it helps others find it.

MIT © [Tatendaz](https://github.com/Tatendaz)
