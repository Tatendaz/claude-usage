# Enterprise deployment

Enterprise subscriptions can display quota and use local notifications. They
cannot send ntfy phone notifications. This includes custom ntfy servers and
`--notify-test ntfy`.

## How the subscription restriction works

Before each ntfy request, the CLI reads the current credential source and checks
its `subscriptionType`. Enterprise, missing, and unrecognized values block the
request before network access. Only recognized Free, Pro, Max, and Team values
permit ntfy. Configuration and environment channel overrides cannot disable
this check. Local `terminal`, `desktop`, and `herdr` channels still work.

Environment token overrides (`CLAUDE_USAGE_TOKEN` and
`CLAUDE_CODE_OAUTH_TOKEN`) do not carry subscription metadata, so they block
ntfy even if another credential store describes a personal subscription. The
CLI does not guess the plan from a token or reuse a cached plan after a login
change. A blocked notification test exits 1 and explains the restriction.

This is a safeguard in the distributed client, not an administrative enforcement
boundary against someone who can modify the program or credential files.
Corporate restrictions also need managed software integrity and outbound
network policy. Subscription metadata is read locally; it is not a signed
attestation of an account's plan.

## Data flows

- The CLI reads Claude Code OAuth credentials from the environment, macOS
  Keychain, or the credentials file. It uses the access token for the fixed
  HTTPS Anthropic usage endpoint. It does not refresh tokens. Redirects are
  rejected, and API error bodies are not logged.
- The cache and JSON `raw` field contain allowlisted quota fields rather than
  the full response. Cache files use mode 0600. Existing raw caches are
  sanitized on read. Window names remain API-provided text; review diagnostics
  before sharing them. Offline quota data may remain until uninstall or cache
  removal; the polling TTL controls freshness, not deletion.
- Non-enterprise users with recognized metadata can opt into ntfy. Those
  requests contain a topic and quota alert text, never the Claude OAuth token.
  HTTPS is required and redirects are rejected. Enterprise and unknown plans
  cannot use this channel.
- Local channels delegate delivery to the terminal, operating system, or herdr.
  Corporate policy should also govern lock-screen previews and those programs'
  own forwarding settings.

## Before a corporate pilot

Have client IT approve access to the existing Claude Code credential and the
undocumented usage endpoint. Test the actual Enterprise login, managed TLS/proxy
configuration, Python runtime, and chosen terminal on representative machines.
This source change does not establish vendor permission or SSO compatibility.

Distribute a reviewed, immutable revision through the client's managed software
channel. Verify its integrity, retain a rollback version, and test uninstall.
Do not have every employee independently install the moving main branch. Keep
required CI checks and code-owner protection active for updates. The CLI remains
standard-library-only; CI action dependencies are pinned separately.

Agree on supported platforms, a security contact, patch response expectations,
and support for upstream endpoint changes. The repository's existing support
policy provides no enterprise SLA or certification. These remain deployment
acceptance decisions, not guarantees provided by this PR.

Phone alerts also require the subscription used for the usage fetch to be
recognized and non-enterprise. Switching accounts while a fetch is in progress
cannot make an enterprise response eligible for ntfy delivery.
