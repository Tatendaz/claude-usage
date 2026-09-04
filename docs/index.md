# claude-usage

**Your Claude quota, live in the terminal status bar.** Session, weekly, and per-model windows with reset times. The same numbers as `/usage`, always in view.

[View on GitHub](https://github.com/Tatendaz/claude-usage) [Install](#install-by-hand)

The line it keeps in your bar:

```text
✳ Usage 5h 18% ⟲ reset in 3h · week 12% · fable 19% ⟲ reset in 2d
```

## The AI installs it

The repo ships a machine-readable runbook, [AGENTS.md](https://github.com/Tatendaz/claude-usage/blob/main/AGENTS.md). Paste one line into Claude Code and the agent clones the repo, detects which terminal you're in, wires it up, and verifies its own work.

Paste into Claude Code:

```text
Install the plugin from https://github.com/Tatendaz/claude-usage
```

Works in any coding agent that can run shell commands. The one step it can't do for you is drag the widget into iTerm2's status bar, and it will tell you when.

## Why

You find out you hit your weekly limit when Claude tells you. Mid-task. The number existed the whole time; it was hidden behind a command you have to remember to run.

claude-usage makes remaining quota ambient, like a battery percentage, so you can check before starting something big.

## Pick the look you want

iTerm2's component list ships six ready-made entries, each previewed right where you drag it from — what you see is what you get, with nothing to configure afterward. They're shown widest first; choose whichever suits the room your bar has.

### Wide · Countdown default

Window labels, percentages, and how long until each window resets, counted down from now. The most informative, and the widest.

![Wide · Countdown: the status bar reading Usage 5h 7%, reset in 3h, week 26%, fable 46%, reset in 3d](https://tatendaz.github.io/claude-usage/img/picker-wide-countdown.png)

### Wide · Inline

The same information, but resets as wall-clock times and dates rather than countdowns. Pick this if you'd rather know *when* than *how long*.

![Wide · Inline: the status bar reading Usage 5h 7%, resets Sat, week 26%, fable 46%, resets Tue](https://tatendaz.github.io/claude-usage/img/picker-wide-inline.png)

### Medium

Labels and percentages, no reset times — for when resets are noise to you and you just want the numbers.

![Medium: the status bar reading Usage 5h 8%, week 27%, fable 46%](https://tatendaz.github.io/claude-usage/img/picker-medium.png)

### Compact · Countdown

Drops the labels and the word “Usage”, keeping percentages and bare countdown marks. Roughly a third the width of Wide, and still tells you when things reset.

![Compact · Countdown: the status bar reading 7%, 3h, 26%, 46%, 3d](https://tatendaz.github.io/claude-usage/img/picker-compact-countdown.png)

### Compact · Inline

The compact layout with clock times instead of countdowns.

![Compact · Inline: the status bar reading 8%, Sat, 27%, 46%, Tue](https://tatendaz.github.io/claude-usage/img/picker-compact-inline.png)

### Mini

Three percentages and nothing else, for a bar that's already full.

![Mini: the status bar reading 7%/26%/46%](https://tatendaz.github.io/claude-usage/img/picker-mini.png)

Every capture above is a real status bar; the green outline marks the component. tmux, WezTerm, kitty, and starship render the same line, and pick their width the same way.

## How it works

### Your existing login

Reads the Claude Code OAuth token already on your machine: env var, macOS Keychain, or `~/.claude/.credentials.json`. It never refreshes the token, and the token goes nowhere except api.anthropic.com.

### The official endpoint

Calls the same endpoint the `/usage` screen reads, so you get the real remaining percentage per window, not an estimate reconstructed from token logs.

### One shared cache

One on-disk cache feeds every terminal at once — 60 seconds by default, tunable with `CLAUDE_USAGE_TTL`. Offline shows your last good numbers marked `✳~`, an expired login says so, and display modes always exit 0, so your bar never breaks.

### One readable file

The core is ~1,289 lines of stdlib-only Python with zero dependencies and 183 tests, MIT licensed. You can read the whole thing before trusting it near your credentials.

## Get an alert before it runs out

Optional. The bar already polls, so the alerts ride on that: one notification per window each time it crosses 50, 80, or 90 percent, then silence until the window resets.

### Four channels, any mix

Your terminal's own notification (iTerm2, WezTerm, kitty, ghostty), a macOS notification, a toast inside herdr, or a push to your phone through the free ntfy app on iOS and Android. Pick any mix.

### Your levels

The default is 50, 80, and 90 percent. `minimal` is 90 only, `early` adds 25 and 75, or list your own percentages. It watches the session, the week, and every per-model week such as Fable.

### One file, one test

Settings live in `~/.config/claude-usage/config.json`. Run `claude-usage --notify-test` to fire a test on every channel and see which ones arrived. A notification carries only the window name, the percentage, and the time to reset.

## Install by hand

Three commands, then wire up your terminal with the [per-terminal guides](https://github.com/Tatendaz/claude-usage/blob/main/docs/TERMINALS.md).

```sh
git clone https://github.com/Tatendaz/claude-usage.git ~/.claude-usage
cd ~/.claude-usage && ./install.sh
~/.local/bin/claude-usage --check   # verifies credentials + endpoint end-to-end
```

**Where it renders**

| Terminal | How it renders |
|---|---|
| iTerm2 | Native status bar component via the Python API. |
| tmux | TPM plugin: `set -g @plugin 'Tatendaz/claude-usage'`, then a `#{claude_usage}` placeholder. |
| WezTerm | One `require` in wezterm.lua renders it in the right status area. |
| kitty | Tab bar integration (experimental). |
| herdr | Tab bar command slot, plus an in-app toast channel for the alerts. |
| starship, zsh | Prompt segment, or Claude Code's own statusline. Any bar that can run a command works. |

## FAQ

**Which Claude plans does it work with?**

Anything that signs into claude.ai: Pro, Max, Team, and Enterprise. API-key, Bedrock, and Vertex setups have no subscription quota windows, so there is nothing to display for them.

**Is it safe? Where does my token go?**

The core is one stdlib-only Python file you can read in five minutes. It reads your existing Claude Code credentials, sends the token to exactly one place (api.anthropic.com, over TLS), never writes or refreshes it, and stores only quota percentages in its local cache.

**Does it work on Windows?**

Via WSL, yes, today: the Linux path works unchanged with tmux or starship. Native Windows (WezTerm status bar, starship in PowerShell, Claude Code statusline) needs a small patch that is planned next.

**How is this different from ccusage or usage monitors?**

Those tools analyze local token logs to answer "what did I spend". claude-usage reads Anthropic's own quota endpoint to answer "what do I have left, and when does it reset". They are complementary; many people run both.

**What happens if Anthropic changes the endpoint?**

The endpoint is undocumented, so it can drift (it already changed shape once). The plugin degrades to a stale marker instead of breaking your bar, and all parsing goes through a single normalize() function built to adapt. Open an issue and it gets fixed fast.

---

HTML version: https://tatendaz.github.io/claude-usage/ · Source: https://github.com/Tatendaz/claude-usage · More work: https://tatendaz.github.io/ · Agent guide: https://tatendaz.github.io/llms.txt
