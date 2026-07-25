# CLI reference

```text
claude-usage [--format text|iterm|tmux|long|json] [--remaining]
             [--resets countdown|inline|tail|off] [--width wide|medium|compact|mini]
             [--buckets LIST] [--all] [--ttl N] [--force] [--check] [--demo]
```

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

## Sample output

```console
$ claude-usage --format long
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
