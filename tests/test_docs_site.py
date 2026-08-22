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


def section(tag: str, doc: str = HTML) -> str:
    """Inner HTML of the single <tag>…</tag> element in doc."""
    found = re.findall(rf"<{tag}\b[^>]*>(.*?)</{tag}>", doc, re.S | re.I)
    assert len(found) == 1, f"expected exactly one <{tag}>, found {len(found)}"
    return found[0]


def squash(text: str) -> str:
    """Collapse whitespace and drop the characters Markdown adds for emphasis/code."""
    return re.sub(r"\s+", " ", text.replace("*", "").replace("`", "").replace("\\", "")).strip()


def block_text(fragment: str) -> str:
    """Visible text of one HTML block: <br> becomes a space, other tags vanish."""
    fragment = re.sub(r"<br\b[^>]*>", " ", fragment, flags=re.I)
    return squash(html.unescape(re.sub(r"<[^>]+>", "", fragment)))


def twin_plain(md: str) -> str:
    """The Markdown twin as plain text: no code blocks, links and images reduced to their text."""
    text = re.sub(r"```.*?```", " ", md, flags=re.S)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"(?m)^>\s?", "", text)
    return squash(text)


def text_blocks(main_html: str) -> list[str]:
    """Every paragraph and list item inside <main>, as plain text (empty ones dropped)."""
    blocks = re.findall(r"<(?:p|li)\b[^>]*>(.*?)</(?:p|li)>", main_html, re.S | re.I)
    return [t for t in (block_text(b) for b in blocks) if t]


class DocsSiteTests(unittest.TestCase):
    def test_h1_and_content_live_inside_main(self):
        main = section("main")
        self.assertEqual(len(re.findall(r"<h1\b", HTML, re.I)), 1, "exactly one <h1>")
        self.assertEqual(len(re.findall(r"<h1\b", main, re.I)), 1, "the <h1> must be inside <main>")
        self.assertGreaterEqual(len(block_text(main)), 500, "500+ chars of text inside <main>")

    def test_head_advertises_markdown_twin_and_llms_txt(self):
        head = section("head")
        self.assertIn(f'<link rel="alternate" type="text/markdown" href="/{SLUG}/index.md"', head)
        self.assertIn('<link rel="describedby" href="/llms.txt">', head)
        self.assertIn('href="https://tatendaz.github.io/llms.txt"', section("footer"))

    def test_markdown_twin_mirrors_the_page(self):
        self.assertTrue(MD.startswith("# "), "twin must start with an H1")
        self.assertEqual(MD.splitlines()[0][2:].strip(), block_text(section("h1")))
        for h2 in re.findall(r"<h2\b[^>]*>(.*?)</h2>", HTML, re.S | re.I):
            self.assertIn("## " + block_text(h2), MD)
        self.assertIn(f"HTML version: https://tatendaz.github.io/{SLUG}/", MD)
        self.assertIn("https://tatendaz.github.io/llms.txt", MD)
        self.assertNotRegex(MD, r"<(div|span|script|style)\b", "twin must be plain Markdown")

    def test_markdown_twin_carries_every_paragraph(self):
        blocks = text_blocks(section("main"))
        self.assertGreaterEqual(len(blocks), 10)
        plain = twin_plain(MD)
        for block in blocks:
            self.assertIn(block, plain, f"twin is missing the text: {block[:80]!r}")


if __name__ == "__main__":
    unittest.main()
