# Security Policy

`claude-usage` reads your Claude Code OAuth credentials and sends them to
Anthropic. That is a small but real trust surface, so it gets a written
policy.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Use GitHub's private reporting form:
[**Report a vulnerability**](https://github.com/Tatendaz/claude-usage/security/advisories/new)
(repository → **Security** → **Advisories** → *Report a vulnerability*).
That creates a private thread visible only to the maintainer.

If private advisories are unavailable to you, open a public issue titled
"Security contact request" containing no details, and you'll be invited to a
private thread.

Please include what you'd want if you were fixing it: the version
(`claude-usage --version`), your OS and terminal, what you did, what
happened, and what you expected. A minimal reproduction is worth more than a
long description. **Never paste a token, a raw `--format json` response, or
an unredacted `--check` transcript into any report** — see "Redaction" below.

You'll get an acknowledgement within a few days. This is a single-maintainer
hobby project, not a funded product: there is no SLA, no bug bounty, and no
paid triage. Fixes ship as fast as they reasonably can, and you'll be
credited in the release notes unless you'd rather not be.

## Supported versions

Only the latest release on `main` is supported. There are no maintenance
branches — if you're on an older tag, update before reporting.

## What this tool does with your credentials

Worth stating precisely, because it defines what counts as a vulnerability:

1. **It reads a token.** First match wins: `$CLAUDE_USAGE_TOKEN` →
   `$CLAUDE_CODE_OAUTH_TOKEN` → the macOS Keychain item
   `Claude Code-credentials` (read via `security find-generic-password`) →
   `~/.claude/.credentials.json`.
2. **It sends that token to exactly one place** —
   `https://api.anthropic.com/api/oauth/usage`, as an
   `Authorization: Bearer` header. Nowhere else. There is no telemetry, no
   analytics, and no third-party endpoint.
3. **It never persists the token.** The token is held in memory for one
   request and dropped. It is never printed, logged, or written to disk —
   including in `--debug` output and including on the error paths.
4. **It caches only percentages.** The response cache at
   `${XDG_CACHE_HOME:-~/.cache}/claude-usage/cache.json` holds usage
   percentages and reset timestamps. No token, and nothing that identifies
   the account.
5. **It never refreshes tokens.** Refresh tokens rotate, and racing Claude
   Code's own refresh could log you out. Renewal is Claude Code's job.
6. **It has no dependencies.** `bin/claude-usage` imports only the Python
   standard library, and CI asserts that on every PR. There is no
   `pip install` step in the install path, so there is no dependency-confusion
   or typosquatting surface.

Anything that breaks one of those six statements is a vulnerability. Please
report it.

## Things that are in scope

- The token reaching stdout, stderr, a log, a file, or any host other than
  `api.anthropic.com`.
- The cache file containing anything account-identifying.
- `install.sh` or `uninstall.sh` writing to, or deleting, a path outside the
  two they document (`~/.local/bin/claude-usage` and the iTerm2 AutoLaunch
  component) — including via a crafted `$HOME`, `$XDG_CACHE_HOME`, or repo
  path.
- Any path where a terminal adapter (iTerm2, tmux, kitty, WezTerm) surfaces
  credential material into a status bar, a title, or a scrollback buffer.
- A non-stdlib import appearing in `bin/claude-usage`.

## Things that are not vulnerabilities

- **The Keychain prompt.** macOS asking to allow access to
  `Claude Code-credentials` is the OS doing its job. Clicking "Always Allow"
  is a decision you make, not a bypass.
- **`--check` talking to the network.** That is its entire purpose. It is the
  one subcommand that performs a real authenticated request, which is why it
  must never run in CI.
- **A local attacker who already has your user account.** If someone can run
  code as you, they can read the Keychain themselves; this tool does not
  widen that.
- **The usage endpoint being undocumented or changing shape.** It is
  undocumented on purpose and drifts occasionally. That is a maintenance
  matter — see the "When the endpoint drifts" section of CONTRIBUTING.md.

## Redaction

If you need to share a payload, strip it first. `--format json` output can
carry account-shaped fields; percentages and reset timestamps are all a bug
report ever needs. The same rule applies to test fixtures: regression tests
use anonymized payloads only.
