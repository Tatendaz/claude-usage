"""Checks that the GitHub Pages landing page (docs/index.html) stays agent-readable.

AI crawlers read the text inside <main>, the JSON-LD, and the Markdown twin that
<link rel="alternate" type="text/markdown"> points at. These tests keep those in
step with the HTML without touching the network.
"""

import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "claude-usage"
HTML = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
MD = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")


def visible_text(fragment: str) -> str:
    fragment = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", fragment, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", fragment))).strip()


def inline_text(fragment: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", fragment))).strip()


class DocsSiteTests(unittest.TestCase):
    def test_h1_and_content_live_inside_main(self):
        mains = re.findall(r"<main\b[^>]*>(.*?)</main>", HTML, re.S | re.I)
        self.assertEqual(len(mains), 1, "exactly one <main>")
        self.assertEqual(len(re.findall(r"<h1\b", HTML, re.I)), 1, "exactly one <h1>")
        self.assertEqual(len(re.findall(r"<h1\b", mains[0], re.I)), 1, "the <h1> must be inside <main>")
        self.assertGreaterEqual(len(visible_text(mains[0])), 500)

    def test_head_advertises_markdown_twin_and_llms_txt(self):
        self.assertIn(f'<link rel="alternate" type="text/markdown" href="/{SLUG}/index.md"', HTML)
        self.assertIn('<link rel="describedby" href="/llms.txt">', HTML)
        self.assertIn('href="https://tatendaz.github.io/llms.txt"', HTML)

    def test_markdown_twin_mirrors_the_page(self):
        self.assertTrue(MD.startswith("# "), "twin must start with an H1")
        h1 = inline_text(re.search(r"<h1\b[^>]*>(.*?)</h1>", HTML, re.S | re.I).group(1))
        self.assertEqual(MD.splitlines()[0][2:].strip(), h1)
        for h2 in re.findall(r"<h2\b[^>]*>(.*?)</h2>", HTML, re.S | re.I):
            self.assertIn("## " + inline_text(h2), MD)
        self.assertGreaterEqual(len(MD), 500)
        self.assertIn(f"HTML version: https://tatendaz.github.io/{SLUG}/", MD)
        self.assertIn("https://tatendaz.github.io/llms.txt", MD)
        self.assertNotRegex(MD, r"<(div|span|script|style)\b")


if __name__ == "__main__":
    unittest.main()
