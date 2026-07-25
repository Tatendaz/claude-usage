# Troubleshooting

| Symptom | Meaning / fix |
|---|---|
| `claude-usage: command not found` | `install.sh` puts the CLI at `~/.local/bin/claude-usage` and never edits your shell config. Call it by full path, or add the directory once: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc`. |
| `✳ not logged in` | Log into Claude Code (`claude`) with a claude.ai account, or export `CLAUDE_CODE_OAUTH_TOKEN`. API-key/Bedrock/Vertex setups have no quota to show. |
| `✳ login expired — open claude` | The OAuth token expired; opening any `claude` session refreshes it. This tool deliberately never refreshes tokens itself (refresh tokens rotate — racing Claude Code could log you out). |
| `✳~ …` | API unreachable; showing your last good numbers. |
| `✳ rate-limited, retrying` | HTTP 429 from the endpoint. It shows your last cached values and tries again on the next poll — there is no growing backoff, so this clears once the endpoint does. |
| Keychain dialog every refresh | Click **Always Allow** (not "Allow") for "Claude Code-credentials". |
| Widget missing in iTerm2 | Python API enabled? Script running (Scripts → AutoLaunch)? Component dragged into the status bar layout? Scrolled to the bottom of the component menu — script components are listed after the built-ins? |

## First thing to run

```bash
~/.local/bin/claude-usage --check
```

It walks credentials → token → endpoint → windows and prints where the chain
breaks. Unlike the display formats, `--check` signals failure through its exit
code.

To confirm rendering is fine when the network or credentials are not:

```bash
~/.local/bin/claude-usage --demo --format long
```

See also: [How it works](HOW_IT_WORKS.md) · [CLI reference](CLI.md)
