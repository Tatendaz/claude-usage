#!/usr/bin/env python3
"""Claude Usage — iTerm2 status bar components.

Six pre-built components, each a fixed size/style pair — drag the one you
want into Configure Status Bar and its picker preview is exactly what it
will show, no configuration knob to guess at:

    Wide · Countdown     ✳ Usage 5h 18% ⟲ reset in 1h · week 9% · fable 15% ⟲ reset in 2d
    Wide · Inline        ✳ Usage 5h 18% ⟲ resets 10:09pm · week 9% · fable 15% ⟲ resets Mon
    Compact · Countdown  ✳ 18% ⟲1h · 9% · 15% ⟲2d
    Compact · Inline     ✳ 18% ⟲10:09pm · 9% · 15% ⟲Mon
    Medium               ✳ Usage 5h 18% · week 9% · fable 15%
    Mini                 ✳ 18%/9%/15%

The heavy lifting (credentials, API, caching) lives in the `claude-usage`
CLI; each component just polls it in the background for its own fixed
--width/--resets pair (see VARIANTS below).

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

CORE_CANDIDATES = ("~/.local/bin/claude-usage",)

# (identifier suffix, picker label, picker preview, --width, --resets or None).
# The first entry keeps the plugin's original identifier (Wide · Countdown
# was always the default look), so upgrading in place doesn't orphan
# whatever a user already dragged into their status bar.
VARIANTS = (
    ("", "Wide · Countdown",
     "✳ Usage 5h 18% ⟲ reset in 1h · week 9% · fable 15% ⟲ reset in 2d",
     "wide", "countdown"),
    (".wide-inline", "Wide · Inline",
     "✳ Usage 5h 18% ⟲ resets 10:09pm · week 9% · fable 15% ⟲ resets Mon",
     "wide", "inline"),
    (".compact-countdown", "Compact · Countdown",
     "✳ 18% ⟲1h · 9% · 15% ⟲2d",
     "compact", "countdown"),
    (".compact-inline", "Compact · Inline",
     "✳ 18% ⟲10:09pm · 9% · 15% ⟲Mon",
     "compact", "inline"),
    (".medium", "Medium",
     "✳ Usage 5h 18% · week 9% · fable 15%",
     "medium", None),
    (".mini", "Mini",
     "✳ 18%/9%/15%",
     "mini", None),
)


def rpc_name(suffix):
    """RPC function name for a variant's status callback. iTerm2 routes a
    status bar invocation to its handler by function signature — not by
    component identifier — so every variant needs a distinct name: with a
    shared one, whichever variant registered first answered for all six
    (dragging Mini into the bar rendered Wide · Countdown's text). The
    default variant keeps the pre-split name so bars configured before
    the six-way split keep rendering."""
    if not suffix:
        return "claude_usage_status"
    return "claude_usage_status_" + suffix.lstrip(".").replace("-", "_")


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


def run_core(width, style):
    """Blocking call to the CLI; returns one fixed-size rendering."""
    core = find_core()
    if not core:
        return "✳ claude-usage: run install.sh"
    cmd = [sys.executable, core, "--format", "iterm", "--width", width]
    if style:
        cmd += ["--resets", style]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        text = (out.stdout or "").strip()
        return text or "✳ …"
    except subprocess.TimeoutExpired:
        return "✳ timeout"
    except OSError as e:
        return "✳ error: %s" % type(e).__name__


# Strong references to the refresher tasks — the event loop only holds
# tasks weakly, so a bare create_task() can be garbage-collected mid-loop.
_BACKGROUND_TASKS = set()


async def register_variant(connection, suffix, label, exemplar, width, style):
    latest = {"text": "✳ …"}

    async def refresher():
        loop = asyncio.get_event_loop()
        while True:
            try:
                latest["text"] = await loop.run_in_executor(
                    None, run_core, width, style)
            except Exception:  # a dead refresher would freeze the bar forever
                latest["text"] = "✳ error"
            await asyncio.sleep(REFRESH_SECONDS)

    task = asyncio.create_task(refresher())
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

    component = iterm2.StatusBarComponent(
        short_description="Claude Usage — %s" % label,
        detailed_description=(
            "Live Claude quota: 5-hour session and weekly windows, the same "
            "numbers as Claude Code's /usage screen. This entry is fixed at "
            "%s — drag a different \"Claude Usage\" entry from this list "
            "for another size or style." % label),
        knobs=[],
        exemplar=exemplar,
        update_cadence=DISPLAY_CADENCE,
        identifier="dev.tatendazhou.claude-usage%s" % suffix,
    )

    async def claude_usage_status(knobs):
        return latest["text"]

    claude_usage_status.__name__ = rpc_name(suffix)
    claude_usage_status.__qualname__ = claude_usage_status.__name__

    await component.async_register(
        connection, iterm2.StatusBarRPC(claude_usage_status))


async def main(connection):
    for suffix, label, exemplar, width, style in VARIANTS:
        await register_variant(connection, suffix, label, exemplar, width, style)


# iTerm2 executes AutoLaunch scripts directly; imports (e.g. tests) skip this.
if __name__ == "__main__":
    if iterm2 is None:
        sys.exit("This script runs inside iTerm2's Python runtime (see README).")
    iterm2.run_forever(main)
