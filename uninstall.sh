#!/bin/bash
# Remove what install.sh created — and only what it created. Files that
# weren't installed by this project (a foreign claude-usage binary, someone
# else's ClaudeUsage.py) are left untouched. Repo files are never removed.
set -uo pipefail

CLI="$HOME/.local/bin/claude-usage"
COMPONENT="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch/ClaudeUsage.py"
MARKER="dev.tatendazhou.claude-usage"

if [ -L "$CLI" ]; then
  case "$(readlink "$CLI")" in
    */bin/claude-usage)
      rm -f "$CLI" && echo "✓ removed $CLI" ;;
    *)
      echo "· left $CLI (symlink points somewhere else)" ;;
  esac
elif [ -e "$CLI" ]; then
  echo "· left $CLI (not a symlink installed by this project)"
fi

if [ -f "$COMPONENT" ]; then
  if grep -q "$MARKER" "$COMPONENT"; then
    rm -f "$COMPONENT" && echo "✓ removed iTerm2 AutoLaunch component"
  else
    echo "· left $COMPONENT (not installed by this project)"
  fi
fi

rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/claude-usage" \
  && echo "✓ removed cache"

echo "Also remove the component from any status bar layout:"
echo "  iTerm2 → Settings → Profiles → Session → Configure Status Bar"
