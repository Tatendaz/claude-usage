#!/usr/bin/env python3
"""Claude Usage — iTerm2 status bar component.

Shows live Claude quota (5-hour session + weekly windows) in the iTerm2
status bar, e.g.:
    ✳ Usage 5h 18% ⟲ reset in 2h · week 9% · fable 15% ⟲ reset in 3d

The heavy lifting (credentials, API, caching) lives in the `claude-usage`
CLI; this script only polls it in the background and hands iTerm2 a set of
width variants to pick from. A component knob (Configure Status Bar →
Claude Usage) chooses how reset times are shown: countdown (default),
inline, tail, or off.

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
KNOB_RESETS = "claude_usage_resets"
RESET_STYLES = ("countdown", "inline", "tail", "off")

CORE_CANDIDATES = ("~/.local/bin/claude-usage",)


def knob_style(value):
    """Normalize the reset-style knob to a valid --resets value, or None
    (None → the CLI's own default; junk input must not break the bar)."""
    value = (value or "").strip().lower()
    return value if value in RESET_STYLES else None


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


def run_core(style=None):
    """Blocking call to the CLI; returns width variants, longest first."""
    core = find_core()
    if not core:
        return ["✳ claude-usage: run install.sh"]
    cmd = [sys.executable, core, "--format", "iterm"]
    if style:
        cmd += ["--resets", style]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        lines = [line for line in (out.stdout or "").splitlines() if line.strip()]
        return lines or ["✳ …"]
    except subprocess.TimeoutExpired:
        return ["✳ timeout"]
    except OSError as e:
        return ["✳ error: %s" % type(e).__name__]


latest = ["✳ …"]
style = {"value": None}   # from the knob; None → CLI default (countdown)
refresh_now = None        # asyncio.Event, created inside the iTerm2 loop


async def refresher():
    global latest
    loop = asyncio.get_event_loop()
    while True:
        result = await loop.run_in_executor(None, run_core, style["value"])
        if result:
            latest = result
        try:
            await asyncio.wait_for(refresh_now.wait(), REFRESH_SECONDS)
        except asyncio.TimeoutError:
            pass
        refresh_now.clear()


async def main(connection):
    global refresh_now
    refresh_now = asyncio.Event()
    asyncio.create_task(refresher())

    component = iterm2.StatusBarComponent(
        short_description="Claude Usage",
        detailed_description=(
            "Live Claude quota: 5-hour session and weekly windows, the same "
            "numbers as Claude Code's /usage screen. The Resets knob picks "
            "how reset times are shown: countdown (default), inline, tail, "
            "or off."
        ),
        knobs=[
            iterm2.StringKnob(
                "Resets (countdown · inline · tail · off)",
                "countdown", "", KNOB_RESETS),
        ],
        exemplar="✳ Usage 5h 18% ⟲ reset in 2h · week 9% · fable 15% "
                 "⟲ reset in 3d",
        update_cadence=DISPLAY_CADENCE,
        identifier=IDENTIFIER,
    )

    @iterm2.StatusBarRPC
    async def claude_usage_status(knobs):
        new = knob_style((knobs or {}).get(KNOB_RESETS))
        if new != style["value"]:
            style["value"] = new
            refresh_now.set()   # apply the new style promptly, not in ≤30s
        return latest

    await component.async_register(connection, claude_usage_status)


# iTerm2 executes AutoLaunch scripts directly; imports (e.g. tests) skip this.
if __name__ == "__main__":
    if iterm2 is None:
        sys.exit("This script runs inside iTerm2's Python runtime (see README).")
    iterm2.run_forever(main)
