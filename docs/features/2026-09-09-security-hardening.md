# Feature: Security hardening and enterprise notification policy

**Branch:** codex/security-hardening
**Date:** 2026-09-09

Enterprise and unverified subscriptions cannot send ntfy notifications, including
test alerts. Recognized personal and Team subscriptions retain HTTPS ntfy;
local notification channels remain available. The check reads current credential
metadata before every send and cannot be overridden by notification settings.
Token-only authentication has no subscription metadata and therefore blocks ntfy.

Authenticated usage and ntfy requests reject redirects. API error bodies are no
longer logged. An allowlist strips unknown response fields before caching and
JSON output; existing caches migrate on read. Display fields lose control
characters and tmux markup is escaped. TPM checkout paths are octal-encoded
before construction of a shell status job.

Dependabot merges now wait for required checks and stop on missing checks,
failure, or timeout. CI actions are pinned to commits, checkout credentials are
not persisted, and the ShellCheck download requires a pinned SHA-256 digest.

Security regression tests cover redirects, error reflection, cache migration,
terminal escapes, subscription restrictions, hostile checkout paths, and merge
failure paths. The enterprise guide documents data flows and remaining pilot
acceptance decisions. The JSON `raw` field is now filtered, a deliberate privacy
change for consumers that previously depended on arbitrary upstream fields.
