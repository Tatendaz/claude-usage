"""Tests for the claude-usage core CLI (bin/claude-usage).

The CLI file has no .py extension, so it is loaded via SourceFileLoader.
No test touches the network, the Keychain, or the real cache.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timedelta, timezone
from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_loader
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin", "claude-usage")


def load_cli():
    loader = SourceFileLoader("claude_usage", BIN)
    spec = spec_from_loader("claude_usage", loader)
    mod = module_from_spec(spec)
    loader.exec_module(mod)
    return mod


cu = load_cli()


def utc(**delta):
    return datetime.now(timezone.utc) + timedelta(**delta)


def iso(dt):
    return dt.isoformat().replace("+00:00", "Z")


# Anonymized copy of a real July 2026 response: per-model weeks live in
# `limits`, the legacy seven_day_* keys are null.
MODERN_RESPONSE = {
    "five_hour": {"utilization": 8.0, "resets_at": iso(utc(hours=4)),
                  "limit_dollars": None},
    "seven_day": {"utilization": 10.0, "resets_at": iso(utc(days=3))},
    "seven_day_opus": None,
    "seven_day_sonnet": None,
    "extra_usage": {"is_enabled": False, "utilization": None},
    "limits": [
        {"kind": "session", "group": "session", "percent": 8,
         "severity": "normal", "resets_at": iso(utc(hours=4)),
         "scope": None, "is_active": False},
        {"kind": "weekly_all", "group": "weekly", "percent": 10,
         "severity": "normal", "resets_at": iso(utc(days=3)),
         "scope": None, "is_active": False},
        {"kind": "weekly_scoped", "group": "weekly", "percent": 17,
         "severity": "normal", "resets_at": iso(utc(days=3)),
         "scope": {"model": {"id": None, "display_name": "Fable"},
                   "surface": None},
         "is_active": True},
    ],
    "spend": {"used": {"amount_minor": 0}, "percent": 0, "severity": "normal",
              "enabled": False},
}


class TestParseWhen(unittest.TestCase):
    def test_iso_zulu(self):
        dt = cu._parse_when("2026-07-18T21:29:59Z")
        self.assertEqual(dt.tzinfo, timezone.utc)
        self.assertEqual(dt.hour, 21)

    def test_iso_offset_with_micros(self):
        dt = cu._parse_when("2026-07-18T21:29:59.638822+00:00")
        self.assertEqual(dt.minute, 29)

    def test_epoch_seconds_and_millis(self):
        secs = cu._parse_when(1784393752)
        millis = cu._parse_when(1784393752000)
        self.assertEqual(secs, millis)
        self.assertEqual(secs.year, 2026)

    def test_bad_input(self):
        self.assertIsNone(cu._parse_when(None))
        self.assertIsNone(cu._parse_when("not a date"))


class TestScopeName(unittest.TestCase):
    def test_model_display_name(self):
        entry = {"scope": {"model": {"display_name": "Fable"}, "surface": None}}
        self.assertEqual(cu._scope_name(entry), "Fable")

    def test_model_id_fallback(self):
        entry = {"scope": {"model": {"id": "claude-fable-5"}}}
        self.assertEqual(cu._scope_name(entry), "claude-fable-5")

    def test_surface_string(self):
        self.assertEqual(cu._scope_name({"scope": {"surface": "cowork"}}), "cowork")

    def test_surface_dict(self):
        entry = {"scope": {"surface": {"display_name": "Cowork"}}}
        self.assertEqual(cu._scope_name(entry), "Cowork")

    def test_no_scope(self):
        self.assertIsNone(cu._scope_name({"scope": None}))
        self.assertIsNone(cu._scope_name({}))


class TestNormalizeModern(unittest.TestCase):
    def test_limits_array_preferred_and_scoped_week_found(self):
        buckets = cu.normalize(MODERN_RESPONSE)
        self.assertEqual([b["key"] for b in buckets],
                         ["session", "weekly_all", "weekly_scoped:fable"])
        fable = buckets[2]
        self.assertEqual(fable["label"], "fable")
        self.assertEqual(fable["title"], "Current week (Fable)")
        self.assertEqual(fable["pct"], 17.0)
        self.assertTrue(fable["active"])
        self.assertEqual(fable["severity"], "normal")
        self.assertIsNotNone(fable["resets"])

    def test_known_kind_labels(self):
        buckets = cu.normalize(MODERN_RESPONSE)
        self.assertEqual(buckets[0]["label"], "5h")
        self.assertEqual(buckets[0]["title"], "Current session")
        self.assertEqual(buckets[1]["label"], "week")
        self.assertEqual(buckets[1]["title"], "Current week (all models)")

    def test_malformed_limit_entries_skipped(self):
        data = {"limits": [None, "x", {"kind": "session"},
                           {"kind": "session", "percent": "high"},
                           {"kind": "session", "percent": 5}]}
        buckets = cu.normalize(data)
        self.assertEqual(len(buckets), 1)
        self.assertEqual(buckets[0]["pct"], 5.0)

    def test_unknown_kind_without_scope(self):
        data = {"limits": [{"kind": "daily_all", "percent": 3}]}
        b = cu.normalize(data)[0]
        self.assertEqual(b["label"], "daily all")
        self.assertEqual(b["title"], "Daily all")

    def test_scoped_non_weekly_kind(self):
        data = {"limits": [{"kind": "session_scoped", "percent": 3,
                            "scope": {"model": {"display_name": "Opus"}}}]}
        b = cu.normalize(data)[0]
        self.assertEqual(b["label"], "opus")
        self.assertIn("Opus", b["title"])

    def test_percent_clamped(self):
        data = {"limits": [{"kind": "session", "percent": 140},
                           {"kind": "weekly_all", "percent": -3}]}
        buckets = cu.normalize(data)
        self.assertEqual(buckets[0]["pct"], 100.0)
        self.assertEqual(buckets[1]["pct"], 0.0)

    def test_spend_bucket_when_enabled(self):
        data = {"limits": [{"kind": "session", "percent": 1}],
                "spend": {"enabled": True, "percent": 42, "severity": "normal"}}
        buckets = cu.normalize(data)
        self.assertEqual(buckets[-1]["key"], "spend")
        self.assertEqual(buckets[-1]["label"], "credits")
        self.assertEqual(buckets[-1]["pct"], 42.0)

    def test_spend_ignored_when_disabled(self):
        buckets = cu.normalize(MODERN_RESPONSE)
        self.assertNotIn("spend", [b["key"] for b in buckets])


class TestNormalizeLegacy(unittest.TestCase):
    def test_fallback_when_no_limits_key(self):
        data = {"five_hour": {"utilization": 7, "resets_at": iso(utc(hours=1))},
                "seven_day": {"utilization": 10, "resets_at": iso(utc(days=2))}}
        buckets = cu.normalize(data)
        self.assertEqual([b["key"] for b in buckets], ["five_hour", "seven_day"])
        self.assertEqual(buckets[0]["pct"], 7.0)

    def test_fallback_when_limits_empty(self):
        data = {"limits": [],
                "five_hour": {"utilization": 7, "resets_at": None}}
        self.assertEqual(cu.normalize(data)[0]["key"], "five_hour")

    def test_fraction_scale_detected(self):
        data = {"five_hour": {"utilization": 0.07},
                "seven_day": {"utilization": 0.10}}
        buckets = cu.normalize(data)
        self.assertAlmostEqual(buckets[0]["pct"], 7.0)
        self.assertAlmostEqual(buckets[1]["pct"], 10.0)

    def test_bare_zero_one_read_as_percent(self):
        data = {"five_hour": {"utilization": 0},
                "seven_day": {"utilization": 1}}
        buckets = cu.normalize(data)
        self.assertEqual(buckets[0]["pct"], 0.0)
        self.assertEqual(buckets[1]["pct"], 1.0)

    def test_fractional_float_one_is_maxed_out(self):
        # A fraction-scale response at exactly 1.0 means 100% used, and
        # must not be confused with an integer 1 (= 1% on percent scale).
        data = {"five_hour": {"utilization": 1.0},
                "seven_day": {"utilization": 0.5}}
        buckets = cu.normalize(data)
        self.assertEqual(buckets[0]["pct"], 100.0)
        self.assertEqual(buckets[1]["pct"], 50.0)

    def test_unknown_model_bucket_labelled(self):
        data = {"seven_day_fable": {"utilization": 15}}
        b = cu.normalize(data)[0]
        self.assertEqual(b["label"], "fable")
        self.assertEqual(b["title"], "Current week (Fable)")

    def test_ordering_five_hour_first(self):
        data = {"seven_day": {"utilization": 2},
                "five_hour": {"utilization": 1}}
        self.assertEqual([b["key"] for b in cu.normalize(data)],
                         ["five_hour", "seven_day"])

    def test_null_and_junk_entries_ignored(self):
        data = {"seven_day_opus": None, "tangelo": None,
                "extra_usage": {"is_enabled": False, "utilization": None},
                "five_hour": {"utilization": 3}}
        self.assertEqual(len(cu.normalize(data)), 1)

    def test_empty_inputs(self):
        self.assertEqual(cu.normalize({}), [])
        self.assertEqual(cu.normalize(None), [])


class TestSelectBuckets(unittest.TestCase):
    def buckets(self):
        return cu.normalize({
            "five_hour": {"utilization": 5},
            "seven_day": {"utilization": 6},
            "seven_day_oauth_apps": {"utilization": 7},
        })

    def test_oauth_apps_hidden_by_default(self):
        keys = [b["key"] for b in cu.select_buckets(self.buckets(), None, False)]
        self.assertNotIn("seven_day_oauth_apps", keys)

    def test_all_keeps_everything(self):
        self.assertEqual(len(cu.select_buckets(self.buckets(), None, True)), 3)

    def test_spec_by_key_and_label(self):
        picked = cu.select_buckets(self.buckets(), "five_hour,week", False)
        self.assertEqual([b["key"] for b in picked], ["five_hour", "seven_day"])

    def test_unknown_spec_falls_back_to_all(self):
        self.assertEqual(len(cu.select_buckets(self.buckets(), "nope", False)), 3)

    def test_legacy_spec_matches_modern_keys(self):
        # A config written for the legacy shape (--buckets five_hour,seven_day)
        # keeps working after the account moves to the modern `limits` shape.
        modern = cu.normalize(MODERN_RESPONSE)
        picked = cu.select_buckets(modern, "five_hour,seven_day", False)
        self.assertEqual([b["key"] for b in picked], ["session", "weekly_all"])

    def test_modern_spec_matches_legacy_keys(self):
        legacy = cu.normalize({"five_hour": {"utilization": 5},
                               "seven_day": {"utilization": 6}})
        picked = cu.select_buckets(legacy, "session,weekly_all", False)
        self.assertEqual([b["key"] for b in picked], ["five_hour", "seven_day"])


class TestFormatters(unittest.TestCase):
    def demo_buckets(self):
        return cu.normalize(cu.demo_data())

    def test_pct_text_rounds_and_flags(self):
        b = cu._bucket("k", "l", "t", 89.6, None)
        self.assertEqual(cu.pct_text(b, remaining=False), "90%!")
        self.assertEqual(cu.pct_text(cu._bucket("k", "l", "t", 12.4, None), False), "12%")

    def test_pct_text_remaining(self):
        b = cu._bucket("k", "l", "t", 30, None)
        self.assertEqual(cu.pct_text(b, remaining=True), "70%")

    def test_fmt_text(self):
        out = cu.fmt_text(self.demo_buckets(), remaining=False, stale=False)
        self.assertTrue(out.startswith(cu.ICON + " Usage "), out)
        self.assertIn("5h 18%", out)
        self.assertIn("week 9%", out)
        self.assertIn("fable 15%", out)

    def test_fmt_text_stale_marker(self):
        out = cu.fmt_text(self.demo_buckets(), remaining=False, stale=True)
        self.assertIn("~", out.split()[0])

    def test_fmt_iterm_variants(self):
        lines = cu.fmt_iterm(self.demo_buckets(), False, False).splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[0].count("⟲ reset in "), 2)  # word at every mark
        self.assertNotIn("⟲", lines[1])                     # medium is plain
        self.assertIn("⟲", lines[2])                        # compact: bare marks
        self.assertNotIn("reset", lines[2])                 # …without the word
        self.assertRegex(lines[2], r"18% ⟲\d+[mh] · 9% · 15% ⟲\d+[hd]")
        self.assertEqual(lines[3].count("⟲"), 0)            # tightest fallback
        self.assertIn("18%/9%/15%", lines[3])

    def test_fmt_iterm_styles(self):
        buckets = self.demo_buckets()
        inline = cu.fmt_iterm(buckets, False, False, resets="inline").splitlines()
        self.assertEqual(inline[0].count("⟲ resets "), 2)
        self.assertRegex(inline[2], r"18% ⟲\S+ · 9% · 15% ⟲\S+")
        tail = cu.fmt_iterm(buckets, False, False, resets="tail").splitlines()
        self.assertIn(" ⟲ resets ", tail[0])
        self.assertIn(" · week ", tail[0].split("⟲")[1])
        self.assertRegex(tail[2], r"18%/9%/15% ⟲ \S+·\S+$")
        off = cu.fmt_iterm(buckets, False, False, resets="off").splitlines()
        self.assertEqual(len(off), 2)
        self.assertNotIn("⟲", "\n".join(off))

    def test_fmt_iterm_without_resets(self):
        buckets = [cu._bucket("session", "5h", "Current session", 4, None)]
        lines = cu.fmt_iterm(buckets, False, False).splitlines()
        self.assertEqual(len(lines), 2)

    def test_fmt_mini(self):
        self.assertEqual(cu.fmt_mini(self.demo_buckets(), False, False),
                         "✳ 18%/9%/15%")

    def test_fmt_iterm_width_matches_ladder(self):
        # wide/medium/compact/mini must be exactly the ladder's 4 lines when
        # nothing collapses (off is the only style that ever collapses lines).
        buckets = self.demo_buckets()
        for style in ("countdown", "inline", "tail"):
            ladder = cu.fmt_iterm(buckets, False, False, resets=style).splitlines()
            widths = [cu.fmt_iterm_width(buckets, False, False, w, style)
                     for w in ("wide", "medium", "compact", "mini")]
            self.assertEqual(ladder, widths, style)

    def test_fmt_iterm_width_medium_and_mini_ignore_resets(self):
        buckets = self.demo_buckets()
        for style in cu.RESET_STYLES:
            medium = cu.fmt_iterm_width(buckets, False, False, "medium", style)
            mini = cu.fmt_iterm_width(buckets, False, False, "mini", style)
            self.assertNotIn("⟲", medium, style)
            self.assertEqual(mini, "✳ 18%/9%/15%", style)

    def test_fmt_iterm_width_compact_off_has_no_marks(self):
        # Regression: fmt_compact used to have no "off" branch at all (the
        # ladder never called it that way), so it silently rendered marks.
        out = cu.fmt_iterm_width(self.demo_buckets(), False, False, "compact", "off")
        self.assertNotIn("⟲", out)
        self.assertEqual(out, "✳ 18% · 9% · 15%")

    def test_fmt_iterm_width_defaults_to_countdown(self):
        buckets = self.demo_buckets()
        default = cu.fmt_iterm_width(buckets, False, False, "wide", None)
        explicit = cu.fmt_iterm_width(buckets, False, False, "wide", "countdown")
        junk = cu.fmt_iterm_width(buckets, False, False, "wide", "bogus")
        self.assertEqual(default, explicit)
        self.assertEqual(junk, explicit)

    def test_tmux_color_thresholds(self):
        self.assertEqual(cu.tmux_color(59), "colour114")
        self.assertEqual(cu.tmux_color(60), "colour179")
        self.assertEqual(cu.tmux_color(84), "colour179")
        self.assertEqual(cu.tmux_color(85), "colour167")

    def test_fmt_tmux(self):
        out = cu.fmt_tmux(self.demo_buckets(), False, False)
        self.assertIn("#[fg=colour114]", out)
        self.assertIn("#[default]", out)

    def test_fmt_text_reset_styles(self):
        buckets = self.demo_buckets()
        self.assertNotIn("⟲", cu.fmt_text(buckets, False, False))  # default off
        countdown = cu.fmt_text(buckets, False, False, resets="countdown")
        self.assertRegex(countdown, r"5h 18% ⟲ reset in \d+[mh]")
        self.assertIn("week 9% ·", countdown)   # shared reset moves past week…
        self.assertRegex(countdown, r"fable 15% ⟲ reset in \d+[hd]")  # …to here
        inline = cu.fmt_text(buckets, False, False, resets="inline")
        self.assertRegex(inline, r"5h 18% ⟲ resets \S+ · week 9% · fable 15% ⟲ resets ")
        tail = cu.fmt_text(buckets, False, False, resets="tail")
        self.assertRegex(tail, r"fable 15% ⟲ resets .+ · week ")

    def test_fmt_tmux_reset_styles(self):
        buckets = self.demo_buckets()
        self.assertNotIn("⟲", cu.fmt_tmux(buckets, False, False))  # default off
        out = cu.fmt_tmux(buckets, False, False, resets="countdown")
        self.assertIn("#[fg=colour114]", out)
        self.assertIn("⟲ reset in ", out)

    def test_fmt_long(self):
        out = cu.fmt_long(self.demo_buckets(), False, None, False)
        self.assertIn("Current session", out)
        self.assertIn("Current week (Fable)", out)
        self.assertIn("█", out)
        self.assertIn("resets", out)
        self.assertRegex(out, r"resets .+ \(in \d+[mhd]\)")

    def test_fmt_long_remaining(self):
        out = cu.fmt_long(self.demo_buckets(), True, None, False)
        self.assertIn("% left)", out)

    def test_fmt_json_contract(self):
        payload = json.loads(cu.fmt_json(self.demo_buckets(), cu.demo_data(),
                                         1000.0, False, None))
        for field in ("fetched_at", "age_seconds", "stale", "error",
                      "buckets", "raw"):
            self.assertIn(field, payload)
        self.assertIsNone(payload["error"])
        self.assertFalse(payload["stale"])
        for bucket in payload["buckets"]:
            for field in ("key", "label", "title", "percent_used",
                          "percent_left", "resets_at", "resets_at_local",
                          "resets_in", "resets_in_seconds",
                          "severity", "active"):
                self.assertIn(field, bucket)
        fable = payload["buckets"][2]
        self.assertEqual(fable["key"], "weekly_scoped:fable")
        self.assertEqual(fable["label"], "fable")
        self.assertEqual(fable["title"], "Current week (Fable)")
        self.assertEqual(fable["percent_used"], 15.0)
        self.assertEqual(fable["percent_left"], 85.0)
        self.assertEqual(fable["severity"], "normal")
        self.assertTrue(fable["active"])
        self.assertTrue(fable["resets_at"])
        self.assertTrue(fable["resets_at_local"])
        self.assertRegex(fable["resets_in"], r"^\d+[mhd]$")
        self.assertGreater(fable["resets_in_seconds"], 0)

    def test_fmt_clock_today_vs_future(self):
        soon = datetime.now(timezone.utc)
        out_soon = cu.fmt_clock(soon)
        if soon.astimezone().date() == datetime.now().astimezone().date():
            self.assertNotRegex(out_soon, r"[A-Z][a-z]{2} \d")
        future = cu.fmt_clock(utc(days=3))
        self.assertRegex(future, r"[A-Z][a-z]{2} \d+ \d+:\d{2}(am|pm)")

    def test_error_line_kinds(self):
        self.assertIn("n/a", cu.error_line(None))
        self.assertIn("not logged in",
                      cu.error_line(cu.UsageError("no_creds", "x")))
        self.assertIn("login expired", cu.error_line(cu.UsageError("auth", "x")))
        self.assertIn("rate-limited",
                      cu.error_line(cu.UsageError("rate_limited", "x")))
        self.assertIn("offline", cu.error_line(cu.UsageError("network", "x")))


class TestResetRendering(unittest.TestCase):
    """The reset-time primitives behind --resets, on a fixed clock."""

    NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)

    def at(self, **delta):
        return self.NOW + timedelta(**delta)

    def test_fmt_countdown_units(self):
        cd = lambda **d: cu.fmt_countdown(self.at(**d), self.NOW)
        self.assertEqual(cd(seconds=30), "now")
        self.assertEqual(cd(minutes=-10), "now")   # overdue never goes negative
        self.assertEqual(cd(minutes=5), "5m")
        self.assertEqual(cd(minutes=59, seconds=59), "59m")
        self.assertEqual(cd(hours=1), "1h")
        self.assertEqual(cd(hours=23, minutes=59), "23h")
        self.assertEqual(cd(hours=24), "1d")
        self.assertEqual(cd(days=6, hours=5), "6d")

    def test_fmt_reset_short_today_is_clock(self):
        out = cu.fmt_reset_short(self.NOW, self.NOW)
        self.assertRegex(out, r"^\d{1,2}(:\d{2})?(am|pm)$")

    def test_fmt_reset_short_drops_zero_minutes(self):
        on_hour = self.NOW.astimezone().replace(minute=0, second=0, microsecond=0)
        self.assertNotIn(":", cu.fmt_reset_short(on_hour, self.NOW))
        half_past = on_hour.replace(minute=30)
        self.assertIn(":30", cu.fmt_reset_short(half_past, self.NOW))

    def test_fmt_reset_short_weekday_within_five_days(self):
        self.assertIn(cu.fmt_reset_short(self.at(days=3), self.NOW), cu.DAYS)

    def test_fmt_reset_short_date_beyond_five_days(self):
        self.assertRegex(cu.fmt_reset_short(self.at(days=10), self.NOW),
                         r"^[A-Z][a-z]{2} \d{1,2}$")

    def buckets(self):
        return [
            cu._bucket("session", "5h", "Current session", 47, self.at(hours=3)),
            cu._bucket("weekly_all", "week", "Current week (all models)", 18,
                       self.at(days=6, hours=1)),
            cu._bucket("weekly_scoped:fable", "fable", "Current week (Fable)",
                       33, self.at(days=6, hours=1)),
        ]

    def test_reset_suffixes_run_end_and_word_at_every_mark(self):
        out = cu.reset_suffixes(self.buckets(), "countdown", self.NOW)
        # The shared weekly reset lands after the run's LAST bucket (fable),
        # and every mark repeats the label word.
        self.assertEqual(out, [" ⟲ reset in 3h", "", " ⟲ reset in 6d"])

    def test_reset_suffixes_skips_bucket_without_reset(self):
        buckets = self.buckets()
        buckets[0]["resets"] = None
        out = cu.reset_suffixes(buckets, "countdown", self.NOW)
        self.assertEqual(out, ["", "", " ⟲ reset in 6d"])

    def test_reset_suffixes_distinct_weeklies_both_shown(self):
        buckets = self.buckets()
        buckets[1]["resets"] = self.at(days=2)   # week no longer matches fable
        out = cu.reset_suffixes(buckets, "countdown", self.NOW)
        self.assertEqual(out, [" ⟲ reset in 3h", " ⟲ reset in 2d",
                               " ⟲ reset in 6d"])

    def test_reset_suffixes_minimal_bare_marks(self):
        out = cu.reset_suffixes(self.buckets(), "countdown", self.NOW,
                                minimal=True)
        self.assertEqual(out, [" ⟲3h", "", " ⟲6d"])

    def test_reset_suffixes_inline_uses_absolute_times(self):
        out = cu.reset_suffixes(self.buckets(), "inline", self.NOW)
        self.assertTrue(out[0].startswith(" ⟲ resets "), out)
        self.assertEqual(out[1], "")
        self.assertTrue(out[2].startswith(" ⟲ resets "), out)

    def test_fmt_reset_tail_groups_distinct_resets(self):
        out = cu.fmt_reset_tail(self.buckets(), self.NOW)
        self.assertTrue(out.startswith(" ⟲ resets "), out)
        self.assertIn(" · week ", out)         # second distinct moment labelled
        self.assertNotIn("fable", out)         # duplicate moment shown once
        self.assertEqual(out.count("⟲"), 1)

    def test_fmt_reset_tail_minimal(self):
        out = cu.fmt_reset_tail(self.buckets(), self.NOW, minimal=True)
        self.assertTrue(out.startswith(" ⟲ "), out)
        self.assertIn("·", out)              # both moments, tight join
        self.assertNotIn("resets", out)      # no label word
        self.assertNotIn("week", out)        # no bucket labels

    def test_fmt_reset_tail_empty_without_resets(self):
        bucket = cu._bucket("session", "5h", "s", 4, None)
        self.assertEqual(cu.fmt_reset_tail([bucket], self.NOW), "")

    def test_reset_label_env_override(self):
        with mock.patch.object(cu, "_RESET_LABEL_ENV", "back in"):
            out = cu.reset_suffixes(self.buckets(), "countdown", self.NOW)
            self.assertEqual(out[0], " ⟲ back in 3h")
        with mock.patch.object(cu, "_RESET_LABEL_ENV", ""):
            out = cu.reset_suffixes(self.buckets(), "countdown", self.NOW)
            self.assertEqual(out[0], " ⟲ 3h")   # empty label → bare icon

    def test_fmt_compact_variants(self):
        out = cu.fmt_compact(self.buckets(), False, False, "countdown")
        self.assertNotIn("Usage", out)
        self.assertNotIn("fable", out)
        tail = cu.fmt_compact(self.buckets(), False, False, "tail")
        self.assertIn("47%/18%/33% ⟲ ", tail)


class TestCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir_patch = mock.patch.object(cu, "CACHE_DIR", self.tmp.name)
        self.file_patch = mock.patch.object(
            cu, "CACHE_FILE", os.path.join(self.tmp.name, "cache.json"))
        self.dir_patch.start()
        self.file_patch.start()
        self.addCleanup(self.dir_patch.stop)
        self.addCleanup(self.file_patch.stop)

    def test_round_trip(self):
        cu.save_cache({"data": {"x": 1}, "fetched_at": 5})
        self.assertEqual(cu.load_cache()["data"], {"x": 1})

    def test_missing_file(self):
        self.assertEqual(cu.load_cache(), {})


class TestClaudeCliVersion(unittest.TestCase):
    def test_uses_fresh_cached_version(self):
        cache = {"cli_version": "9.9.9", "cli_version_at": cu.time.time()}
        with mock.patch.object(cu.subprocess, "run") as run:
            self.assertEqual(cu.claude_cli_version(cache), "9.9.9")
            run.assert_not_called()

    def test_detects_from_cli(self):
        fake = mock.Mock(stdout="2.1.214 (Claude Code)", returncode=0)
        with mock.patch.object(cu.subprocess, "run", return_value=fake):
            self.assertEqual(cu.claude_cli_version({}), "2.1.214")

    def test_fallback_on_failure(self):
        with mock.patch.object(cu.subprocess, "run", side_effect=OSError):
            self.assertEqual(cu.claude_cli_version({}), cu.FALLBACK_CLI_VERSION)


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestFetchUsage(unittest.TestCase):
    def test_success(self):
        body = json.dumps({"limits": []}).encode()
        with mock.patch.object(cu.urllib.request, "urlopen",
                               return_value=FakeResponse(body)) as opened:
            self.assertEqual(cu.fetch_usage("tok", "1.0.0"), {"limits": []})
        req = opened.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer tok")
        self.assertEqual(req.get_header("Anthropic-beta"), cu.OAUTH_BETA)
        self.assertEqual(req.get_header("User-agent"), "claude-code/1.0.0")

    def http_error(self, code):
        return urllib.error.HTTPError(cu.API_URL, code, "err", {},
                                      io.BytesIO(b"{}"))

    def test_auth_errors(self):
        for code in (401, 403):
            with mock.patch.object(cu.urllib.request, "urlopen",
                                   side_effect=self.http_error(code)):
                with self.assertRaises(cu.UsageError) as ctx:
                    cu.fetch_usage("tok", "1.0.0")
                self.assertEqual(ctx.exception.kind, "auth")

    def test_rate_limited(self):
        with mock.patch.object(cu.urllib.request, "urlopen",
                               side_effect=self.http_error(429)):
            with self.assertRaises(cu.UsageError) as ctx:
                cu.fetch_usage("tok", "1.0.0")
            self.assertEqual(ctx.exception.kind, "rate_limited")

    def test_server_error(self):
        with mock.patch.object(cu.urllib.request, "urlopen",
                               side_effect=self.http_error(500)):
            with self.assertRaises(cu.UsageError) as ctx:
                cu.fetch_usage("tok", "1.0.0")
            self.assertEqual(ctx.exception.kind, "http")

    def test_network_error(self):
        with mock.patch.object(cu.urllib.request, "urlopen",
                               side_effect=urllib.error.URLError("down")):
            with self.assertRaises(cu.UsageError) as ctx:
                cu.fetch_usage("tok", "1.0.0")
            self.assertEqual(ctx.exception.kind, "network")


class TestGetUsage(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for attr, value in (("CACHE_DIR", self.tmp.name),
                            ("CACHE_FILE", os.path.join(self.tmp.name, "c.json"))):
            patcher = mock.patch.object(cu, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_fresh_cache_skips_fetch(self):
        cu.save_cache({"data": {"limits": []}, "fetched_at": cu.time.time()})
        with mock.patch.object(cu, "fetch_usage") as fetch:
            data, _, stale, err = cu.get_usage(ttl=60)
            fetch.assert_not_called()
        self.assertEqual(data, {"limits": []})
        self.assertFalse(stale)
        self.assertIsNone(err)

    def test_fetch_success_updates_cache(self):
        with mock.patch.object(cu, "load_credentials",
                               return_value=("tok", {}, "env")), \
             mock.patch.object(cu, "claude_cli_version", return_value="1.0.0"), \
             mock.patch.object(cu, "fetch_usage",
                               return_value={"limits": [1]}) as fetch:
            data, _, stale, err = cu.get_usage(ttl=60, force=True)
        fetch.assert_called_once()
        self.assertEqual(data, {"limits": [1]})
        self.assertIsNone(err)
        self.assertEqual(cu.load_cache()["data"], {"limits": [1]})

    def test_error_serves_stale_cache(self):
        old = cu.time.time() - 3600
        cu.save_cache({"data": {"limits": []}, "fetched_at": old})
        with mock.patch.object(cu, "load_credentials",
                               return_value=("tok", {}, "env")), \
             mock.patch.object(cu, "claude_cli_version", return_value="1.0.0"), \
             mock.patch.object(cu, "fetch_usage",
                               side_effect=cu.UsageError("network", "down")):
            data, fetched_at, stale, err = cu.get_usage(ttl=60)
        self.assertEqual(data, {"limits": []})
        self.assertTrue(stale)
        self.assertEqual(err.kind, "network")

    def test_no_creds_no_cache(self):
        with mock.patch.object(cu, "load_credentials",
                               return_value=(None, {}, None)):
            data, _, _, err = cu.get_usage(ttl=60)
        self.assertIsNone(data)
        self.assertEqual(err.kind, "no_creds")


class TestLoadCredentials(unittest.TestCase):
    def test_env_override_wins(self):
        env = {"CLAUDE_USAGE_TOKEN": "a", "CLAUDE_CODE_OAUTH_TOKEN": "b"}
        with mock.patch.dict(os.environ, env):
            token, _, source = cu.load_credentials()
        self.assertEqual((token, source), ("a", "env:CLAUDE_USAGE_TOKEN"))

    def test_setup_token_second(self):
        with mock.patch.dict(os.environ, {"CLAUDE_CODE_OAUTH_TOKEN": "b"}):
            os.environ.pop("CLAUDE_USAGE_TOKEN", None)
            token, _, source = cu.load_credentials()
        self.assertEqual((token, source), ("b", "env:CLAUDE_CODE_OAUTH_TOKEN"))

    def clean_env(self):
        return mock.patch.dict(os.environ, {}, clear=False)

    def test_keychain_then_file(self):
        creds = {"claudeAiOauth": {"accessToken": "kc", "subscriptionType": "max"}}
        with self.clean_env():
            os.environ.pop("CLAUDE_USAGE_TOKEN", None)
            os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with mock.patch.object(cu, "_keychain_credentials", return_value=creds):
                token, meta, source = cu.load_credentials()
        self.assertEqual(token, "kc")
        self.assertEqual(meta["subscriptionType"], "max")
        self.assertEqual(source, "keychain")

    def test_nothing_found(self):
        with self.clean_env():
            os.environ.pop("CLAUDE_USAGE_TOKEN", None)
            os.environ.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            with mock.patch.object(cu, "_keychain_credentials", return_value=None), \
                 mock.patch.object(cu, "_file_credentials", return_value=None):
                token, meta, source = cu.load_credentials()
        self.assertIsNone(token)
        self.assertIsNone(source)


class TestCheckAndDemo(unittest.TestCase):
    def test_demo_data_normalizes(self):
        buckets = cu.normalize(cu.demo_data())
        self.assertEqual(len(buckets), 3)
        self.assertEqual(buckets[2]["label"], "fable")

    def test_run_check_passes_with_mocked_endpoint(self):
        with mock.patch.object(cu, "load_credentials",
                               return_value=("tok", {"subscriptionType": "max"},
                                             "keychain")), \
             mock.patch.object(cu, "claude_cli_version", return_value="1.0.0"), \
             mock.patch.object(cu, "fetch_usage", return_value=cu.demo_data()), \
             mock.patch.object(cu, "save_cache"), \
             mock.patch.object(cu, "load_cache", return_value={}), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            code = cu.run_check(ttl=60)
        self.assertEqual(code, 0)
        self.assertIn("check passed", out.getvalue())

    def test_run_check_fails_without_creds(self):
        with mock.patch.object(cu, "load_credentials",
                               return_value=(None, {}, None)), \
             mock.patch.object(cu, "claude_cli_version", return_value="1.0.0"), \
             mock.patch.object(cu, "load_cache", return_value={}), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            code = cu.run_check(ttl=60)
        self.assertEqual(code, 1)
        self.assertIn("FAILED", out.getvalue())


class TestMainWithoutData(unittest.TestCase):
    def test_normal_mode_exits_zero_when_quota_unavailable(self):
        # Status bars must never break: display formats print a short error
        # line and exit 0 even with no credentials and no cache.
        err = cu.UsageError("no_creds", "no Claude Code credentials found")
        with mock.patch.object(cu, "get_usage",
                               return_value=(None, None, False, err)), \
             mock.patch.object(sys, "argv", ["claude-usage"]), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            cu.main()  # raising SystemExit(nonzero) would fail this test
        self.assertIn("not logged in", out.getvalue())

    def test_json_mode_reports_error_when_quota_unavailable(self):
        err = cu.UsageError("network", "down")
        with mock.patch.object(cu, "get_usage",
                               return_value=(None, None, False, err)), \
             mock.patch.object(sys, "argv", ["claude-usage", "--format", "json"]), \
             mock.patch("sys.stdout", new_callable=io.StringIO) as out:
            cu.main()
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["buckets"], [])
        self.assertIn("down", payload["error"])


class TestCliEndToEnd(unittest.TestCase):
    """Run the actual executable with --demo (no credentials, no network)."""

    def run_cli(self, *args, env=None):
        # Hermetic: a developer's exported CLAUDE_USAGE_* must not leak in.
        full_env = {k: v for k, v in os.environ.items()
                    if not k.startswith("CLAUDE_USAGE_")}
        full_env.update(env or {})
        result = subprocess.run([sys.executable, BIN, *args],
                                capture_output=True, text=True, timeout=30,
                                env=full_env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_demo_all_formats(self):
        self.assertIn("fable 15%", self.run_cli("--demo"))
        self.assertIn("% left", self.run_cli("--demo", "--remaining"))
        self.assertIn("#[fg=", self.run_cli("--demo", "--format", "tmux"))
        self.assertEqual(len(self.run_cli("--demo", "--format",
                                          "iterm").splitlines()), 4)
        self.assertIn("Current week (Fable)",
                      self.run_cli("--demo", "--format", "long"))

    def test_demo_reset_styles(self):
        iterm = self.run_cli("--demo", "--format", "iterm").splitlines()
        self.assertEqual(iterm[0].count("⟲ reset in "), 2)  # default: countdown
        self.assertIn("⟲", iterm[2])                        # compact, bare mark
        self.assertNotIn("reset", iterm[2])
        off = self.run_cli("--demo", "--format", "iterm", "--resets", "off")
        self.assertEqual(len(off.splitlines()), 2)
        self.assertIn("⟲ resets ", self.run_cli("--demo", "--resets", "inline"))
        self.assertRegex(self.run_cli("--demo", "--resets", "tail"),
                         r"⟲ resets .+ · week ")

    def test_resets_env_default(self):
        out = self.run_cli("--demo", env={"CLAUDE_USAGE_RESETS": "countdown"})
        self.assertIn("⟲ reset in ", out)
        junk = self.run_cli("--demo", env={"CLAUDE_USAGE_RESETS": "bogus"})
        self.assertNotIn("⟲", junk)              # invalid env must not break

    def test_reset_label_env(self):
        out = self.run_cli("--demo", "--resets", "countdown",
                           env={"CLAUDE_USAGE_RESET_LABEL": "back in"})
        self.assertIn("⟲ back in ", out)

    def test_demo_json_contract(self):
        payload = json.loads(self.run_cli("--demo", "--format", "json"))
        self.assertEqual(len(payload["buckets"]), 3)
        self.assertIn("percent_left", payload["buckets"][0])
        self.assertIn("resets_in", payload["buckets"][0])

    def test_bucket_filter(self):
        out = self.run_cli("--demo", "--buckets", "session")
        self.assertIn("5h", out)
        self.assertNotIn("fable", out)

    def test_width_prints_one_line(self):
        for w in ("wide", "medium", "compact", "mini"):
            out = self.run_cli("--demo", "--format", "iterm", "--width", w)
            self.assertEqual(len(out.splitlines()), 1, w)
        wide = self.run_cli("--demo", "--format", "iterm", "--width", "wide",
                            "--resets", "inline")
        self.assertIn("⟲ resets ", wide)
        mini = self.run_cli("--demo", "--format", "iterm", "--width", "mini",
                            "--resets", "inline")
        self.assertNotIn("⟲", mini)


if __name__ == "__main__":
    unittest.main()
