# Session: Launch strategy + GitHub Pages landing site

**Branch:** docs/launch-site
**Date:** 2026-07-18

## Prompts

1. "Can we do the things we did for YapUI like create a github pages for it
   create twitter annoncement linkedin annoncemnt so taht I can start to get
   stars and usage for the plugin? Can you create a strategy for me for this?
   you can check my chat history to see what I did for yapui and also check on
   the web how people get people to use their open source tool and star the
   repository"
2. "How dificult would it be to add windows support?"
3. "How dificult would it be to add windows support? can windows work even?"
   (rephrase of the same question mid-turn)

## Steps taken

- Mined the YapUI launch sessions (transcripts + the github-social-kit launch
  folder + the yapui repo) with a subagent: recovered the Pages mechanism
  (docs/ folder on main, single self-contained index.html, .nojekyll, headless
  Chrome social preview), the exact posted X/LinkedIn texts, the Show HN draft,
  the channel sequencing, and the writing rules (no em-dashes, banned-word
  list, measured numbers only, link in first reply, honest limitations).
- Ran a parallel web-research subagent on 2025–2026 OSS launch practice: Show
  HN norms, Reddit self-promo rules, GitHub Trending mechanics, awesome-list
  submission processes (awesome-claude-code is issue-form only), prior art for
  this exact category (ccusage, Claude-Code-Usage-Monitor, ccstatusline).
- Wrote the launch kit at `github-social-kit/claude-usage release/`: strategy
  README with a dated calendar, x-posts.md, linkedin.md, show-hn.md, reddit.md,
  distribution.md.
- Built `docs/index.html` (self-contained landing page with AI-install prompt,
  FAQ + JSON-LD, OG/Twitter cards), rendered `docs/social-preview.png`
  (1280×640) with headless Chrome, added `docs/.nojekyll`.
- Visual QA via headless Chrome screenshots; fixed a `white-space` bug that
  collapsed the manual-install commands into one line.
- Assessed Windows support difficulty by reading the credential and version
  code paths (both already fail gracefully off-macOS; answer reported in chat).

## Decisions

- Pages from `main:/docs` (the YapUI mechanism) instead of a gh-pages branch
  or Actions deploy: one less moving part, and the images the page needs
  already live under `docs/img/`.
- The landing page makes the AI-install prompt the centerpiece; it is the
  product's most differentiated angle and the page's best demo.
- Positioning vs ccusage-class tools is "complementary, not rival": they
  answer "what did I spend", this answers "what do I have left".
- Marketing copy stays out of the repo (lives in github-social-kit) so the
  repo reads as a tool, not a funnel, under Hacker News scrutiny.
