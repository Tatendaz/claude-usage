#!/usr/bin/env python3
"""claude-usage for kitty: Claude quota drawn at the right edge of the tab bar.

kitty has no status bar, but its tab bar accepts a custom Python renderer.
This file draws kitty's normal tabs, then right-aligns the Claude quota
(this is the community "right status" pattern from kitty issue #4447).

Install — if you do NOT already have a custom tab bar (won't overwrite):
    cp -n kitty/tab_bar.py ~/.config/kitty/tab_bar.py
and in kitty.conf:
    tab_bar_style custom
    tab_bar_min_tabs 1

If you DO already have a ~/.config/kitty/tab_bar.py, don't replace it:
merge `status_text()` + `find_core()` into it and call
`_draw_right_status(screen)` at the end of your draw_tab.

Experimental: exercised via unit tests, not against every kitty version —
please report breakage.
"""

import os
import shutil
import subprocess
import sys
import time

try:  # only present inside kitty's runtime; tests import this file without it
    from kitty.tab_bar import (
        DrawData, ExtraData, Formatter, TabBarData,
        draw_attributed_string, draw_tab_with_separator,
    )
    KITTY = True
except ImportError:
    KITTY = False

REFRESH_SECONDS = 30
CORE_CANDIDATES = ("~/.local/bin/claude-usage",)

_cache = {"at": 0.0, "text": "✳ …", "proc": None}


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


def status_text(now=None):
    """Latest status line, refreshed at most every REFRESH_SECONDS.

    Never blocks: this runs inside kitty's tab redraw, so the CLI is
    launched fire-and-forget and collected on a later redraw; until then
    the previous text keeps showing.
    """
    now = time.monotonic() if now is None else now
    proc = _cache["proc"]
    if proc is not None:
        if proc.poll() is None:
            return _cache["text"]  # still running — collect next redraw
        _cache["proc"] = None
        try:
            text = (proc.stdout.read() if proc.stdout else "").strip()
            if text:
                _cache["text"] = text.splitlines()[0]
        except OSError:
            pass  # keep the previous text
        return _cache["text"]

    if now - _cache["at"] >= REFRESH_SECONDS:
        _cache["at"] = now
        core = find_core()
        if not core:
            _cache["text"] = "✳ claude-usage not installed"
        else:
            try:
                _cache["proc"] = subprocess.Popen(
                    [sys.executable, core], stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, text=True,
                )
            except OSError:
                pass  # keep the previous text
    return _cache["text"]


def _draw_right_status(screen):
    text = " " + status_text() + " "
    free = screen.columns - screen.cursor.x
    if len(text) > free:
        return
    draw_attributed_string(Formatter.reset, screen)
    screen.draw(" " * (free - len(text)))
    screen.draw(text)


if KITTY:
    def draw_tab(
        draw_data: DrawData, screen, tab: TabBarData, before: int,
        max_title_length: int, index: int, is_last: bool,
        extra_data: ExtraData,
    ) -> int:
        end = draw_tab_with_separator(
            draw_data, screen, tab, before, max_title_length, index,
            is_last, extra_data,
        )
        if is_last:
            _draw_right_status(screen)
        return end
