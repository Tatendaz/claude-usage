#!/usr/bin/env bash
# Assert that a PR's own diff adds a docs entry named for its branch.
#
#   require-docs-entry.sh <docs-dir> <branch-slug> <diff-range>
#
# e.g. require-docs-entry.sh docs/features ci-hardening origin/main...HEAD
#
# The file must be named exactly <YYYY-MM-DD>-<slug>.md.
#
# ---------------------------------------------------------------------------
# Why this is a script and not four lines of `grep -E` in the workflow
# ---------------------------------------------------------------------------
# The original inline version was:
#
#     git diff --name-status --diff-filter=AR "$RANGE" -- docs/features/ \
#       | grep -E "docs/features/.*$BRANCH_SLUG\.md$"
#
# which had two defects, both of which fail a *correctly authored* PR:
#
#   1. REGEX INJECTION. $BRANCH_SLUG went into an ERE unescaped, so any branch
#      whose name contains a regex metacharacter was matched as a pattern
#      rather than as text. `feat/c++parser` and `feat/x[1]` both produced
#      "Missing docs/features/..." against a PR that had the file. This
#      version never builds a regex from the slug at all — the slug is
#      compared with `=`, a literal string comparison, so every character is
#      safe by construction.
#
#   2. SUBSTRING MATCHING. `docs/features/.*<slug>\.md$` is unanchored on the
#      left, so branch `docs/gallery` was satisfied by a pre-existing file
#      named `2026-01-01-picker-gallery.md`. Here the basename is required to
#      be exactly a `YYYY-MM-DD-` date followed by the whole slug and `.md`.
#
# Keeping it in a file also means shellcheck covers it (the CI shell job
# discovers scripts from `git ls-files`) and that the gate can be run by hand
# against a real branch before pushing.
# ---------------------------------------------------------------------------

set -uo pipefail

if [ "$#" -ne 3 ]; then
  echo "usage: $0 <docs-dir> <branch-slug> <diff-range>" >&2
  exit 2
fi

DOCS_DIR="$1"
SLUG="$2"
RANGE="$3"

if [ -z "$SLUG" ]; then
  echo "::error::Could not derive a branch slug — refusing to pass the docs gate." >&2
  exit 1
fi

# Only files this PR itself adds or renames count. An entry left in the tree
# by an older branch must not satisfy a new PR.
added="$(git diff --name-only --diff-filter=AR "$RANGE" -- "$DOCS_DIR/")"

matched=""
while IFS= read -r path; do
  [ -n "$path" ] || continue
  base="${path##*/}"

  # Require a literal YYYY-MM-DD- prefix. This is a glob, not a regex, and it
  # is matched against the filename — never against the slug.
  case "$base" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*) ;;
    *) continue ;;
  esac

  # Strip exactly the 11-character date prefix, then compare the remainder to
  # "<slug>.md" as plain text.
  rest="${base#????-??-??-}"
  if [ "$rest" = "$SLUG.md" ]; then
    matched="$path"
    break
  fi
done <<EOF
$added
EOF

if [ -n "$matched" ]; then
  echo "ok: $matched satisfies the $DOCS_DIR gate for slug '$SLUG'"
  exit 0
fi

{
  echo "::error::Missing $DOCS_DIR/<YYYY-MM-DD>-$SLUG.md in this PR's diff."
  echo
  echo "This PR's branch slug is: $SLUG"
  echo "So the gate wants a file added by this PR named exactly:"
  echo "    $DOCS_DIR/$(date -u +%Y-%m-%d)-$SLUG.md"
  echo
  if [ -n "$added" ]; then
    echo "Files this PR adds under $DOCS_DIR/:"
    printf '%s\n' "$added" | while IFS= read -r path; do
      [ -n "$path" ] && printf '    %s\n' "$path"
    done
  else
    echo "This PR adds no files under $DOCS_DIR/ at all."
  fi
  echo
  echo "If the slug looks wrong, check the branch name. GitHub's web"
  echo "\"Edit this file\" button creates branches called patch-1, which"
  echo "produces the slug 'patch-1'. Branch as <type>/<slug> instead —"
  echo "one of feat/ fix/ docs/ chore/ refactor/. See CONTRIBUTING.md."
} >&2
exit 1
