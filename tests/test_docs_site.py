"""Checks that the GitHub Pages landing page (docs/index.html) stays agent-readable.

AI crawlers read the text inside <main>, the JSON-LD, and the Markdown twin that
<link rel="alternate" type="text/markdown"> points at. These tests keep those in
step with the HTML without touching the network. The custom 404 page (docs/404.html)
gets the same treatment: it must stay short, absolute-linked, and carry plain
Markdown pointers for agents.
"""

import html
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SLUG = "claude-usage"
HTML = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
MD = (ROOT / "docs" / "index.md").read_text(encoding="utf-8")
NOT_FOUND = (ROOT / "docs" / "404.html").read_text(encoding="utf-8")


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
        # Boilerplate-stripping extractors drop <header>/<nav>/<aside>/<footer> elements before counting.
        found = re.findall(r"<(header|nav|aside|footer)\b", main, re.I)
        self.assertEqual(found, [], f"boilerplate element(s) inside <main> would hide content: {found}")

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


class NotFoundPageTests(unittest.TestCase):
    """GitHub Pages serves docs/404.html, with a real 404 status, for every missing path under /claude-usage/."""

    def test_head_marks_the_page_as_a_dead_end(self):
        head = section("head", NOT_FOUND)
        self.assertIn("404", block_text(section("title", NOT_FOUND)))
        self.assertIn('<meta name="robots" content="noindex">', head)
        found = re.findall(r'<link\b[^>]*\brel="(canonical|alternate)"', head, re.I)
        self.assertEqual(found, [], f"a 404 page has no canonical URL and no Markdown twin: {found}")

    def test_main_carries_short_markdown_guidance(self):
        main = section("main", NOT_FOUND)
        found = re.findall(r"<(header|nav|aside|footer)\b", main, re.I)
        self.assertEqual(found, [], f"boilerplate element(s) inside <main> would hide content: {found}")
        self.assertLess(len(block_text(main)), 1500, "agents hit this page at every dead link; keep it short")
        blocks = re.findall(r'<pre class="md"[^>]*>(.*?)</pre>', main, re.S)
        self.assertEqual(len(blocks), 1, 'exactly one <pre class="md"> inside <main>')
        md = html.unescape(blocks[0]).strip()
        self.assertTrue(md.startswith("# 404"), f"the Markdown block must open with an H1: {md[:40]!r}")
        self.assertIn("## Where to look next", md)
        self.assertIn("- [Site map](https://tatendaz.github.io/sitemap.xml)", md)
        self.assertIn("- [llms.txt](https://tatendaz.github.io/llms.txt)", md)
        self.assertIn(f"https://tatendaz.github.io/{SLUG}/", md)
        self.assertLess(len(md), 700, "the Markdown block is a pointer list, not a page")
        self.assertNotRegex(md, r"<[a-z]+[\s>]", "the block must be plain Markdown, not HTML")

    def test_every_url_survives_any_path_depth(self):
        # The one file answers /claude-usage/a/b/c as well, so a relative href would resolve
        # under the wrong directory. Only root-anchored paths, full URLs, mailto:, inline
        # data: URIs (the favicon) and fragments are safe.
        urls = re.findall(r'\b(?:href|src)="([^"]*)"', NOT_FOUND)
        self.assertGreaterEqual(len(urls), 8)
        bad = [u for u in urls if not re.match(r"(/claude-usage/|https?://|mailto:|data:|#)", u)]
        self.assertEqual(bad, [], f"relative URL(s) would break at depth: {bad}")


if __name__ == "__main__":
    unittest.main()
