#!/bin/bash
# Install claude-usage: CLI to ~/.local/bin, iTerm2 component to AutoLaunch.
# Idempotent, and refuses to overwrite files it doesn't own.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
CLI="$BIN_DIR/claude-usage"
AUTOLAUNCH="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
COMPONENT="$AUTOLAUNCH/ClaudeUsage.py"
MARKER="dev.tatendazhou.claude-usage"

chmod +x "$REPO/bin/claude-usage"

# CLI symlink — never clobber a real file the user put there themselves.
if [ -e "$CLI" ] && [ ! -L "$CLI" ]; then
  echo "✗ $CLI already exists and is not a symlink — move it aside, then re-run." >&2
  exit 1
fi
mkdir -p "$BIN_DIR"
ln -sfn "$REPO/bin/claude-usage" "$CLI"
echo "✓ CLI:    $CLI -> $REPO/bin/claude-usage"

# iTerm2 component — only overwrite a previous copy of itself.
if [ -d "/Applications/iTerm.app" ] || [ -d "$HOME/Library/Application Support/iTerm2" ]; then
  if [ -f "$COMPONENT" ] && ! grep -q "$MARKER" "$COMPONENT"; then
    echo "· skipped iTerm2 component: $COMPONENT exists and wasn't installed by this project"
  else
    mkdir -p "$AUTOLAUNCH"
    cp "$REPO/iterm2/ClaudeUsage.py" "$COMPONENT"
    echo "✓ iTerm2: $COMPONENT"
  fi
else
  echo "· iTerm2 not found — skipped the status bar component (CLI still works)"
fi

cat <<'EOF'

Next steps (one-time, in iTerm2):
  1. Settings → General → Magic → check "Enable Python API"
     (accept the Python runtime download if iTerm2 offers it)
  2. Menu bar: Scripts → AutoLaunch → ClaudeUsage.py   (or restart iTerm2)
  3. Settings → Profiles → Session → check "Status bar enabled"
     → Configure Status Bar → drag "Claude Usage" into the active row
  4. Sanity check any time:  claude-usage --check

The first run may pop a macOS dialog asking to allow Keychain access to the
"Claude Code-credentials" item — click "Always Allow".

Other terminals (tmux, WezTerm, kitty, starship, zsh): see README.md.
If this plugin is useful, consider leaving a star:
  https://github.com/Tatendaz/claude-usage ⭐
EOF
