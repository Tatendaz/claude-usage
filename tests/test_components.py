"""Tests for the terminal components (iTerm2 and kitty helper logic).

Both files guard their host-specific imports, so they are importable — and
their subprocess/caching logic testable — without iTerm2 or kitty installed.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name, *path):
    loader = SourceFileLoader(name, os.path.join(ROOT, *path))
    spec = spec_from_loader(name, loader)
    mod = module_from_spec(spec)
    loader.exec_module(mod)
    return mod


iterm_mod = load("claude_usage_iterm", "iterm2", "ClaudeUsage.py")
kitty_mod = load("claude_usage_kitty", "kitty", "tab_bar.py")


class TestFindCore(unittest.TestCase):
    def make_bin(self):
        tmp = tempfile.NamedTemporaryFile(delete=False)
        self.addCleanup(os.unlink, tmp.name)
        return tmp.name

    def test_env_override_wins(self, mod=None):
        for mod in (iterm_mod, kitty_mod):
            path = self.make_bin()
            with mock.patch.dict(os.environ, {"CLAUDE_USAGE_BIN": path}):
                self.assertEqual(mod.find_core(), path)

    def test_which_fallback(self):
        for mod in (iterm_mod, kitty_mod):
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CLAUDE_USAGE_BIN", None)
                with mock.patch.object(mod.shutil, "which",
                                       return_value="/somewhere/claude-usage"):
                    self.assertEqual(mod.find_core(), "/somewhere/claude-usage")

    def test_candidate_path_then_none(self):
        for mod in (iterm_mod, kitty_mod):
            path = self.make_bin()
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("CLAUDE_USAGE_BIN", None)
                with mock.patch.object(mod.shutil, "which", return_value=None):
                    with mock.patch.object(mod, "CORE_CANDIDATES", (path,)):
                        self.assertEqual(mod.find_core(), path)
                    with mock.patch.object(mod, "CORE_CANDIDATES", ()):
                        self.assertIsNone(mod.find_core())


class TestITermRunCore(unittest.TestCase):
    def test_returns_stripped_stdout(self):
        fake = mock.Mock(stdout="✳ long line  \n", returncode=0)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run", return_value=fake):
            self.assertEqual(iterm_mod.run_core("wide", "countdown"), "✳ long line")

    def test_width_and_style_forwarded_to_cli(self):
        fake = mock.Mock(stdout="✳ x\n", returncode=0)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               return_value=fake) as run:
            iterm_mod.run_core("compact", "tail")
            self.assertEqual(run.call_args[0][0][-4:],
                             ["--width", "compact", "--resets", "tail"])

    def test_style_none_not_forwarded(self):
        fake = mock.Mock(stdout="✳ x\n", returncode=0)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               return_value=fake) as run:
            iterm_mod.run_core("medium", None)
            self.assertNotIn("--resets", run.call_args[0][0])
            self.assertEqual(run.call_args[0][0][-2:], ["--width", "medium"])

    def test_missing_core(self):
        with mock.patch.object(iterm_mod, "find_core", return_value=None):
            self.assertIn("install", iterm_mod.run_core("wide", "countdown"))

    def test_empty_output(self):
        fake = mock.Mock(stdout="", returncode=1)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run", return_value=fake):
            self.assertEqual(iterm_mod.run_core("wide", "countdown"), "✳ …")

    def test_timeout(self):
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("x", 25)):
            self.assertEqual(iterm_mod.run_core("wide", "countdown"), "✳ timeout")

    def test_oserror(self):
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               side_effect=OSError("boom")):
            self.assertIn("error", iterm_mod.run_core("wide", "countdown"))


class TestITermVariants(unittest.TestCase):
    """VARIANTS drives both the registered identifiers and the picker
    previews; these guard against typos and preview drift."""

    def test_six_variants(self):
        self.assertEqual(len(iterm_mod.VARIANTS), 6)

    def test_identifiers_unique(self):
        ids = ["dev.tatendazhou.claude-usage%s" % suffix
               for suffix, *_rest in iterm_mod.VARIANTS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_first_variant_keeps_original_identifier(self):
        # So upgrading in place doesn't orphan an already-configured bar.
        suffix, _label, _exemplar, width, style = iterm_mod.VARIANTS[0]
        self.assertEqual(suffix, "")
        self.assertEqual((width, style), ("wide", "countdown"))

    def test_rpc_names_unique_and_first_is_historic(self):
        # Regression: iTerm2 routes a status bar invocation to its handler
        # by function signature, so identical RPC names sent every variant
        # to the first handler — dragging Mini in rendered Wide's text.
        names = [iterm_mod.rpc_name(suffix)
                 for suffix, *_rest in iterm_mod.VARIANTS]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(names[0], "claude_usage_status")  # pre-split bars
        for name in names:
            self.assertTrue(name.isidentifier(), name)

    def test_widths_valid_and_style_pairing(self):
        for suffix, label, exemplar, width, style in iterm_mod.VARIANTS:
            self.assertIn(width, ("wide", "medium", "compact", "mini"), label)
            if width in ("medium", "mini"):
                self.assertIsNone(style, label)  # style-independent sizes
            else:
                self.assertIn(style, ("countdown", "inline", "tail", "off"), label)

    def test_exemplars_match_live_cli_output(self):
        # Catches drift between the hardcoded picker previews and what
        # --width/--resets actually render. "inline" prints the actual
        # wall-clock time and weekday (unlike countdown's "1h"/"2d", which
        # is a stable relative offset from --demo's fixed deltas), so those
        # two variants compare with the volatile tokens masked out instead
        # of byte-exact — otherwise this test would fail every run.
        core = os.path.join(ROOT, "bin", "claude-usage")
        clock_or_weekday = re.compile(
            r"\d{1,2}(:\d{2})?(am|pm)|Mon|Tue|Wed|Thu|Fri|Sat|Sun")
        for suffix, label, exemplar, width, style in iterm_mod.VARIANTS:
            cmd = [sys.executable, core, "--format", "iterm",
                  "--width", width, "--demo"]
            if style:
                cmd += ["--resets", style]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            actual, want = out.stdout.strip(), exemplar
            if style == "inline":
                actual = clock_or_weekday.sub("<T>", actual)
                want = clock_or_weekday.sub("<T>", want)
            self.assertEqual(actual, want, label)


def fake_proc(output, done=True):
    proc = mock.Mock()
    proc.poll.return_value = 0 if done else None
    proc.stdout.read.return_value = output
    return proc


class TestKittyStatusText(unittest.TestCase):
    """status_text runs inside kitty's tab redraw, so it must never block:
    it fires a Popen and collects the result on a later call."""

    def setUp(self):
        patcher = mock.patch.dict(kitty_mod._cache,
                                  {"at": 0.0, "text": "✳ …", "proc": None})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_fires_then_collects_and_caches(self):
        proc = fake_proc("✳ Usage 5h 8%\n")
        with mock.patch.object(kitty_mod, "find_core", return_value="/x"), \
             mock.patch.object(kitty_mod.subprocess, "Popen",
                               return_value=proc) as popen:
            # First call launches but returns the old text (non-blocking).
            self.assertEqual(kitty_mod.status_text(now=1000.0), "✳ …")
            # Second call collects the finished process.
            self.assertEqual(kitty_mod.status_text(now=1001.0), "✳ Usage 5h 8%")
            # Within the refresh window: cached, no new launch.
            kitty_mod.status_text(now=1010.0)
            self.assertEqual(popen.call_count, 1)
            # After the window: a new launch.
            kitty_mod.status_text(now=1000.0 + kitty_mod.REFRESH_SECONDS + 1)
            self.assertEqual(popen.call_count, 2)

    def test_still_running_process_does_not_block(self):
        proc = fake_proc("", done=False)
        with mock.patch.object(kitty_mod, "find_core", return_value="/x"), \
             mock.patch.object(kitty_mod.subprocess, "Popen",
                               return_value=proc) as popen:
            kitty_mod.status_text(now=1000.0)
            self.assertEqual(kitty_mod.status_text(now=1001.0), "✳ …")
            proc.stdout.read.assert_not_called()
            # Unfinished process is never abandoned for a new launch.
            kitty_mod.status_text(now=2000.0)
            self.assertEqual(popen.call_count, 1)

    def test_empty_output_keeps_previous_text(self):
        kitty_mod._cache["text"] = "✳ old"
        proc = fake_proc("")
        with mock.patch.object(kitty_mod, "find_core", return_value="/x"), \
             mock.patch.object(kitty_mod.subprocess, "Popen", return_value=proc):
            kitty_mod.status_text(now=1000.0)
            self.assertEqual(kitty_mod.status_text(now=1001.0), "✳ old")

    def test_popen_failure_keeps_previous_text(self):
        kitty_mod._cache["text"] = "✳ old"
        with mock.patch.object(kitty_mod, "find_core", return_value="/x"), \
             mock.patch.object(kitty_mod.subprocess, "Popen",
                               side_effect=OSError("boom")):
            self.assertEqual(kitty_mod.status_text(now=1000.0), "✳ old")
        self.assertIsNone(kitty_mod._cache["proc"])

    def test_missing_core_message(self):
        with mock.patch.object(kitty_mod, "find_core", return_value=None):
            self.assertIn("not installed", kitty_mod.status_text(now=1000.0))


if __name__ == "__main__":
    unittest.main()
