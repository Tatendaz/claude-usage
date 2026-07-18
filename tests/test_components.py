"""Tests for the terminal components (iTerm2 and kitty helper logic).

Both files guard their host-specific imports, so they are importable — and
their subprocess/caching logic testable — without iTerm2 or kitty installed.
"""

import os
import subprocess
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
    def test_returns_stdout_lines(self):
        fake = mock.Mock(stdout="long line\nshort\n\n", returncode=0)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run", return_value=fake):
            self.assertEqual(iterm_mod.run_core(), ["long line", "short"])

    def test_missing_core(self):
        with mock.patch.object(iterm_mod, "find_core", return_value=None):
            self.assertIn("install", iterm_mod.run_core()[0])

    def test_empty_output(self):
        fake = mock.Mock(stdout="", returncode=1)
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run", return_value=fake):
            self.assertEqual(iterm_mod.run_core(), ["✳ …"])

    def test_timeout(self):
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               side_effect=subprocess.TimeoutExpired("x", 25)):
            self.assertEqual(iterm_mod.run_core(), ["✳ timeout"])

    def test_oserror(self):
        with mock.patch.object(iterm_mod, "find_core", return_value="/x"), \
             mock.patch.object(iterm_mod.subprocess, "run",
                               side_effect=OSError("boom")):
            self.assertIn("error", iterm_mod.run_core()[0])


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
