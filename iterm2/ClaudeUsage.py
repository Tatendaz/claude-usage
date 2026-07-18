#!/usr/bin/env python3
"""Claude Usage — iTerm2 status bar component.

Shows live Claude quota (5-hour session + weekly windows) in the iTerm2
status bar, e.g.:   ✳ 5h 18% · wk 9% · fable 15% ⟲ 12:29am

The heavy lifting (credentials, API, caching) lives in the `claude-usage`
CLI; this script only polls it in the background and hands iTerm2 a set of
width variants to pick from.

Installed by install.sh into:
  ~/Library/Application Support/iTerm2/Scripts/AutoLaunch/ClaudeUsage.py
Requires the iTerm2 Python API (Settings → General → Magic → Python API).
"""

import asyncio
import os
import shutil
import subprocess
import sys

try:
    import iterm2
except ImportError:  # running outside iTerm2's runtime (e.g. the test suite)
    iterm2 = None

REFRESH_SECONDS = 30      # how often we ask the CLI (which itself caches ~60s)
DISPLAY_CADENCE = 15      # how often iTerm2 re-reads the latest text
IDENTIFIER = "dev.tatendazhou.claude-usage"

CORE_CANDIDATES = ("~/.local/bin/claude-usage",)


def find_core():
    override = os.environ.get("CLAUDE_USAGE_BIN")
    if override and os.path.exists(os.path.expanduser(override)):
        return os.path.expanduser(override)
    found = shutil.which("claude-usage")
    if found:
        return found
    for candidate in CORE_CANDIDATES:
        path = os.path.expanduser(candidate)
        if os.path.exists(path):
            return path
    return None


def run_core():
    """Blocking call to the CLI; returns width variants, longest first."""
    core = find_core()
    if not core:
        return ["✳ claude-usage: run install.sh"]
    try:
        out = subprocess.run(
            [sys.executable, core, "--format", "iterm"],
            capture_output=True, text=True, timeout=25,
        )
        lines = [line for line in (out.stdout or "").splitlines() if line.strip()]
        return lines or ["✳ …"]
    except subprocess.TimeoutExpired:
        return ["✳ timeout"]
    except OSError as e:
        return ["✳ error: %s" % type(e).__name__]


latest = ["✳ …"]


async def refresher():
    global latest
    loop = asyncio.get_event_loop()
    while True:
        result = await loop.run_in_executor(None, run_core)
        if result:
            latest = result
        await asyncio.sleep(REFRESH_SECONDS)


async def main(connection):
    asyncio.create_task(refresher())

    component = iterm2.StatusBarComponent(
        short_description="Claude Usage",
        detailed_description=(
            "Live Claude quota: 5-hour session and weekly windows, the same "
            "numbers as Claude Code's /usage screen."
        ),
        knobs=[],
        exemplar="✳ Usage 5h 18% · week 9% · fable 15%",
        update_cadence=DISPLAY_CADENCE,
        identifier=IDENTIFIER,
    )

    @iterm2.StatusBarRPC
    async def claude_usage_status(knobs):
        return latest

    await component.async_register(connection, claude_usage_status)


# iTerm2 executes AutoLaunch scripts directly; imports (e.g. tests) skip this.
if __name__ == "__main__":
    if iterm2 is None:
        sys.exit("This script runs inside iTerm2's Python runtime (see README).")
    iterm2.run_forever(main)
