# Session: Security hardening

**Branch:** codex/security-hardening
**Date:** 2026-09-09

## Requests

1. "can you do a security audit of main? git pull first"
2. "The main goal is that I want to offer a corporate client to use it internally and they are a big enterprise"
3. "lets disable ntfy notifications for enterprise accounts/subscription and document it. Work on the rest of the issues found by the audit and submit a PR security-hardening"

## Work

Pulled main at 336d82d and audited the full source with an independent security
review. Reproduced redirect credential forwarding, tmux checkout-path command
execution, and a merge fallback that proceeded with pending checks. Identified
raw-response caching, diagnostic reflection, terminal control characters, and
incorrect third-party data-flow documentation.

Implemented enterprise and unknown-plan ntfy blocking, redirect rejection,
response allowlisting and cache migration, safe diagnostics/display text, encoded
tmux paths, and required-check merge gating. Pinned CI dependencies and the
ShellCheck checksum using official upstream repository metadata. Read main's
GitHub rules to confirm required checks and code-owner approval are configured;
no repository settings were changed.

Added offline regression tests, updated the security policy and enterprise/CLI
guides, and moved the README's detailed terminal gallery/setup to the terminal
guide. The source remains standard-library-only. Validation and the review
verdict are reported on the PR; no enterprise certification or SLA is claimed.

## CodeRabbit follow-up, 2026-09-10

The user asked to fix CodeRabbit comments and to expect its review after PR
updates. Addressed all three findings: conditional notification setup guidance,
the README notifications link, and case-insensitive redirect response headers.
The redirect test now asserts that the production guard runs and compares it
against a permissive control with mocked HTTP and HTTPS transports. Disabling
the guard demonstrably follows the redirect and forwards the synthetic header.
PR review remains part of the completion checks after pushes.

The follow-up review also found an outside-diff sentence claiming only
percentages leave the CLI. Replaced it with a token-focused rule and explicit
JSON/ntfy data descriptions. Completion guidance now requires reading full
review bodies as well as inline threads, since the watcher did not surface this
outside-diff comment.
