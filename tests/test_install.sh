#!/usr/bin/env bash
# Tests for install.sh and uninstall.sh.
#
# Plain bash assertions — no bats, no pip, nothing to install. The project
# rule is "No pip dependencies, ever" (CONTRIBUTING.md) and a contributor
# should need nothing but a shell and python3 to run the whole suite.
#
#   tests/test_install.sh        # quiet — one line per test
#   tests/test_install.sh -v     # also echo each script's output and every
#                                # individual assertion
#
# ---------------------------------------------------------------------------
# SAFETY
# ---------------------------------------------------------------------------
# install.sh writes into $HOME and uninstall.sh deletes from it, so every test
# runs against a throwaway HOME created by mktemp -d. HOME, XDG_CACHE_HOME and
# XDG_CONFIG_HOME are all redirected, and assert_sandboxed() re-checks all
# three immediately before every single invocation of a script under test.
#
# That interlock is not decorative. uninstall.sh does:
#
#     rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/claude-usage"
#
# A test that redirected HOME but forgot XDG_CACHE_HOME would aim a recursive
# delete at the developer's real cache directory. If the interlock ever sees a
# path outside the sandbox it aborts the entire run with exit 99 *before*
# executing anything.
# ---------------------------------------------------------------------------

# Every test case and every helper below is reached indirectly — the runner
# dispatches test cases by name (`"$name"`) and the cases call the helpers —
# so ShellCheck's "function is never invoked" heuristic fires on all of them.
# This must stay above the first command to apply to the whole file.
# shellcheck disable=SC2329

set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
REAL_HOME="${HOME:-}"
MARKER="dev.tatendazhou.claude-usage"

VERBOSE=0
if [ "${1:-}" = "-v" ] || [ "${1:-}" = "--verbose" ]; then
  VERBOSE=1
fi

SANDBOX=""
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0
CURRENT_FAILURES=0
SKIP_REASON=""
LAST_OUT=""
LAST_STATUS=0

# --------------------------------------------------------------------------
# Sandbox
# --------------------------------------------------------------------------

sandbox_up() {
  SANDBOX="$(mktemp -d "${TMPDIR:-/tmp}/claude-usage-tests.XXXXXX")"
  export HOME="$SANDBOX/home"
  export XDG_CACHE_HOME="$SANDBOX/home/.cache"
  export XDG_CONFIG_HOME="$SANDBOX/home/.config"
  mkdir -p "$HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME"

  # Nothing in the developer's environment may steer the CLI's output.
  local var
  for var in $(compgen -v CLAUDE_USAGE_ || true); do
    unset "$var"
  done
}

sandbox_down() {
  export HOME="$REAL_HOME"
  unset XDG_CACHE_HOME XDG_CONFIG_HOME
  # Belt and braces: only ever delete a path that looks like one we made.
  case "$SANDBOX" in
    */claude-usage-tests.??????*) rm -rf "$SANDBOX" ;;
  esac
  SANDBOX=""
}

# Hard interlock. Called before every script invocation; aborts the run
# rather than letting a script under test loose on the real machine.
assert_sandboxed() {
  local bad=""
  if [ -z "$SANDBOX" ]; then
    bad="SANDBOX is unset"
  else
    case "${HOME:-}" in "$SANDBOX"/*) ;; *) bad="$bad HOME='${HOME:-}'" ;; esac
    case "${XDG_CACHE_HOME:-}" in "$SANDBOX"/*) ;; *) bad="$bad XDG_CACHE_HOME='${XDG_CACHE_HOME:-}'" ;; esac
    case "${XDG_CONFIG_HOME:-}" in "$SANDBOX"/*) ;; *) bad="$bad XDG_CONFIG_HOME='${XDG_CONFIG_HOME:-}'" ;; esac
  fi
  if [ -n "${REAL_HOME:-}" ] && [ "${HOME:-}" = "$REAL_HOME" ]; then
    bad="$bad HOME is the real HOME"
  fi
  if [ -n "$bad" ]; then
    printf '\nFATAL: refusing to run a script under test outside the sandbox.\n' >&2
    printf '  sandbox:   %s\n' "$SANDBOX" >&2
    printf '  offending:%s\n' "$bad" >&2
    exit 99
  fi
}

# --------------------------------------------------------------------------
# Paths inside the sandbox
# --------------------------------------------------------------------------

cli_path()       { printf '%s/.local/bin/claude-usage' "$HOME"; }
iterm2_dir()     { printf '%s/Library/Application Support/iTerm2' "$HOME"; }
autolaunch_dir() { printf '%s/Scripts/AutoLaunch' "$(iterm2_dir)"; }
component_path() { printf '%s/ClaudeUsage.py' "$(autolaunch_dir)"; }

# install.sh installs the iTerm2 component when /Applications/iTerm.app OR
# ~/Library/Application Support/iTerm2 exists. Creating the latter makes the
# component branch fire identically on a Linux runner and a Mac.
pretend_iterm2_is_installed() { mkdir -p "$(iterm2_dir)"; }

# --------------------------------------------------------------------------
# Running the scripts under test
# --------------------------------------------------------------------------

run_script() {
  assert_sandboxed
  LAST_OUT="$("$REPO_ROOT/$1" 2>&1)"
  LAST_STATUS=$?
  if [ "$VERBOSE" -eq 1 ]; then
    printf '%s\n' "$LAST_OUT" | while IFS= read -r line; do
      printf '        | %s\n' "$line"
    done
  fi
}

install_sh()   { run_script install.sh; }
uninstall_sh() { run_script uninstall.sh; }

# --------------------------------------------------------------------------
# Snapshots — a stable, diffable listing of everything under the sandbox HOME
# --------------------------------------------------------------------------

snapshot() {
  (
    cd "$HOME" || exit 1
    find . -mindepth 1 \( -type d -o -type l -o -type f \) -print0 |
      while IFS= read -r -d '' path; do
        if [ -L "$path" ]; then
          printf 'link %s -> %s\n' "$path" "$(readlink "$path")"
        elif [ -d "$path" ]; then
          printf 'dir  %s\n' "$path"
        else
          printf 'file %s %s\n' "$path" "$(cksum <"$path" | cut -d' ' -f1)"
        fi
      done
  ) | LC_ALL=C sort
}

# --------------------------------------------------------------------------
# Assertions
# --------------------------------------------------------------------------

fail() {
  CURRENT_FAILURES=$((CURRENT_FAILURES + 1))
  printf '      x %s\n' "$*" >&2
}

pass() {
  if [ "$VERBOSE" -eq 1 ]; then
    printf '      . %s\n' "$*"
  fi
}

skip() { SKIP_REASON="$*"; }

assert_status() { # want desc
  if [ "$LAST_STATUS" -eq "$1" ]; then
    pass "$2"
  else
    fail "$2 — exit $LAST_STATUS, wanted $1. Output: $LAST_OUT"
  fi
}

assert_status_nonzero() { # desc
  if [ "$LAST_STATUS" -ne 0 ]; then
    pass "$1"
  else
    fail "$1 — exited 0, wanted a non-zero status. Output: $LAST_OUT"
  fi
}

assert_symlink_to() { # path want-target desc
  if [ ! -L "$1" ]; then
    fail "$3 — $1 is not a symlink"
    return
  fi
  local actual
  actual="$(readlink "$1")"
  if [ "$actual" = "$2" ]; then
    pass "$3"
  else
    fail "$3 — $1 -> $actual, wanted $2"
  fi
}

assert_file() { # path desc
  if [ -f "$1" ]; then pass "$2"; else fail "$2 — no such file: $1"; fi
}

assert_absent() { # path desc
  if [ -e "$1" ] || [ -L "$1" ]; then fail "$2 — still present: $1"; else pass "$2"; fi
}

assert_file_contains() { # path needle desc
  if [ ! -f "$1" ]; then
    fail "$3 — no such file: $1"
  elif grep -q -- "$2" "$1"; then
    pass "$3"
  else
    fail "$3 — $1 does not contain '$2'"
  fi
}

assert_output_contains() { # needle desc
  case "$LAST_OUT" in
    *"$1"*) pass "$2" ;;
    *) fail "$2 — output did not contain '$1'. Output: $LAST_OUT" ;;
  esac
}

assert_same_file() { # a b desc
  if cmp -s "$1" "$2"; then pass "$3"; else fail "$3 — $1 differs from $2"; fi
}

# Permission bits as octal. BSD (macOS) and GNU (Linux) stat have
# incompatible flags, and they are not safely interchangeable: GNU reads -f
# as --file-system and would treat '%Lp' as a *filename*, printing filesystem
# stats to stdout before failing. So probe with GNU's -c, which BSD rejects
# outright, and only then fall back to the BSD spelling.
file_mode() {
  if stat -c '%a' "$1" >/dev/null 2>&1; then
    stat -c '%a' "$1"          # GNU coreutils
  else
    stat -f '%Lp' "$1"         # BSD / macOS
  fi
}

assert_snapshots_equal() { # before after desc
  if [ "$1" = "$2" ]; then
    pass "$3"
  else
    fail "$3 — the tree changed:"
    diff <(printf '%s\n' "$1") <(printf '%s\n' "$2") >&2
  fi
}

# Every line present in $2 but not $1, i.e. what was added.
snapshot_added() { comm -13 <(printf '%s\n' "$1") <(printf '%s\n' "$2"); }
# Every line present in $1 but not $2, i.e. what was removed.
snapshot_removed() { comm -23 <(printf '%s\n' "$1") <(printf '%s\n' "$2"); }

# --------------------------------------------------------------------------
# Tests: install
# --------------------------------------------------------------------------

test_fresh_install_creates_the_cli_and_the_iterm2_component() {
  pretend_iterm2_is_installed
  install_sh
  assert_status 0 "install.sh exits 0 on a clean system"
  assert_symlink_to "$(cli_path)" "$REPO_ROOT/bin/claude-usage" \
    "CLI symlink points at the repo's bin/claude-usage"
  assert_file "$(component_path)" "iTerm2 AutoLaunch component installed"
  assert_same_file "$(component_path)" "$REPO_ROOT/iterm2/ClaudeUsage.py" \
    "installed component is a verbatim copy of iterm2/ClaudeUsage.py"
  assert_file_contains "$(component_path)" "$MARKER" \
    "installed component carries the ownership marker"
  assert_output_contains "CLI:" "reports where the CLI went"
  assert_output_contains "iTerm2:" "reports where the component went"
}

test_fresh_install_touches_only_the_two_documented_paths() {
  pretend_iterm2_is_installed
  # Unrelated things that must survive untouched.
  mkdir -p "$HOME/.local/bin" "$HOME/.config/fish"
  printf 'not ours\n' >"$HOME/.local/bin/some-other-tool"
  printf 'hello\n' >"$HOME/notes.txt"

  local before after added removed
  before="$(snapshot)"
  install_sh
  after="$(snapshot)"
  assert_status 0 "install.sh exits 0"

  removed="$(snapshot_removed "$before" "$after")"
  if [ -z "$removed" ]; then
    pass "install.sh removed nothing that was already there"
  else
    fail "install.sh removed pre-existing paths: $removed"
  fi

  # Only the CLI symlink, the component, and the directories leading to them.
  added="$(snapshot_added "$before" "$after" | grep -v '^dir ' || true)"
  local expected
  expected="$(printf 'file ./Library/Application Support/iTerm2/Scripts/AutoLaunch/ClaudeUsage.py CKSUM\nlink ./.local/bin/claude-usage -> %s/bin/claude-usage\n' "$REPO_ROOT" | LC_ALL=C sort)"
  # Normalise the checksum out — we assert identity separately.
  added="$(printf '%s\n' "$added" | sed -E 's/^(file .*) [0-9]+$/\1 CKSUM/')"
  if [ "$added" = "$expected" ]; then
    pass "install.sh created exactly the CLI symlink and the iTerm2 component"
  else
    fail "install.sh created unexpected paths:"
    diff <(printf '%s\n' "$expected") <(printf '%s\n' "$added") >&2
  fi
}

test_installed_cli_runs_demo_without_network_or_credentials() {
  pretend_iterm2_is_installed
  install_sh
  assert_status 0 "install.sh exits 0"

  local before after out status
  before="$(snapshot)"

  out="$("$(cli_path)" --demo 2>&1)"
  status=$?
  if [ "$status" -eq 0 ]; then
    pass "installed CLI exits 0 for --demo"
  else
    fail "installed CLI exited $status for --demo: $out"
  fi
  case "$out" in
    *Usage*) pass "--demo renders a usage line: $out" ;;
    *) fail "--demo produced unexpected output: $out" ;;
  esac

  out="$("$(cli_path)" --demo --format json 2>&1)"
  if printf '%s' "$out" | python3 -c 'import json,sys; d=json.load(sys.stdin); sys.exit(0 if d.get("buckets") else 1)'; then
    pass "--demo --format json parses and carries buckets"
  else
    fail "--demo --format json did not parse: $out"
  fi

  # --demo short-circuits before get_usage(), so it must not write a cache.
  after="$(snapshot)"
  assert_snapshots_equal "$before" "$after" "--demo writes no files at all"
}

test_install_is_idempotent() {
  pretend_iterm2_is_installed
  install_sh
  assert_status 0 "first install.sh exits 0"
  local after_first after_second
  after_first="$(snapshot)"

  install_sh
  assert_status 0 "second install.sh exits 0"
  after_second="$(snapshot)"

  assert_snapshots_equal "$after_first" "$after_second" \
    "a second install.sh leaves the tree byte-identical"
  assert_symlink_to "$(cli_path)" "$REPO_ROOT/bin/claude-usage" \
    "the CLI symlink survives a second run"

  # And a third, because ln -sfn and cp are the operations most likely to
  # behave differently once the destination exists.
  install_sh
  assert_status 0 "third install.sh exits 0"
  assert_snapshots_equal "$after_first" "$(snapshot)" \
    "a third install.sh leaves the tree byte-identical"
}

# --- anti-clobber guard 1: a real file at the CLI path ----------------------

test_install_refuses_to_clobber_a_real_file_at_the_cli_path() {
  pretend_iterm2_is_installed
  mkdir -p "$HOME/.local/bin"
  printf 'a real binary the user put here\n' >"$(cli_path)"

  install_sh
  assert_status_nonzero "install.sh aborts rather than overwriting a real file"
  assert_output_contains "not a symlink" "the error names the actual problem"
  assert_file_contains "$(cli_path)" "a real binary the user put here" \
    "the user's file is left byte-for-byte intact"
  if [ -L "$(cli_path)" ]; then
    fail "install.sh replaced the user's file with a symlink"
  else
    pass "the path is still a regular file, not a symlink"
  fi
  # Aborting before the iTerm2 step is intentional: set -e means the guard
  # stops the whole install, so nothing else was written either.
  assert_absent "$(component_path)" "the aborted install wrote nothing else"
}

# --- anti-clobber guard 2: an iTerm2 component this project does not own ----

test_install_leaves_a_foreign_iterm2_component_alone() {
  pretend_iterm2_is_installed
  mkdir -p "$(autolaunch_dir)"
  printf '# somebody else ClaudeUsage.py\n' >"$(component_path)"

  install_sh
  assert_status 0 "install.sh still exits 0 (the CLI half must succeed)"
  assert_file_contains "$(component_path)" "somebody else" \
    "the foreign component is left byte-for-byte intact"
  assert_output_contains "skipped iTerm2 component" \
    "install.sh says out loud that it skipped the component"
  assert_symlink_to "$(cli_path)" "$REPO_ROOT/bin/claude-usage" \
    "the CLI is still installed despite the skipped component"
}

test_install_replaces_a_component_it_installed_itself() {
  # The mirror of the guard above: the marker is what makes overwriting safe,
  # so an outdated copy of *our own* component must be refreshed.
  pretend_iterm2_is_installed
  mkdir -p "$(autolaunch_dir)"
  printf '# stale copy\n# identifier="%s"\n' "$MARKER" >"$(component_path)"

  install_sh
  assert_status 0 "install.sh exits 0"
  assert_same_file "$(component_path)" "$REPO_ROOT/iterm2/ClaudeUsage.py" \
    "a marked component is refreshed from the repo"
  assert_output_contains "iTerm2:" "install.sh reports the component install"
}

test_install_without_iterm2_still_installs_the_cli() {
  if [ -d "/Applications/iTerm.app" ]; then
    skip "iTerm2 is installed on this machine; install.sh keys off /Applications/iTerm.app, which the sandbox cannot hide"
    return
  fi
  # Deliberately do NOT create ~/Library/Application Support/iTerm2.
  install_sh
  assert_status 0 "install.sh exits 0 with no iTerm2 present"
  assert_symlink_to "$(cli_path)" "$REPO_ROOT/bin/claude-usage" \
    "the CLI is installed anyway"
  assert_absent "$(component_path)" "no iTerm2 component is created"
  assert_output_contains "iTerm2 not found" "install.sh explains the skip"
}

# --------------------------------------------------------------------------
# Tests: uninstall
# --------------------------------------------------------------------------

test_uninstall_removes_exactly_what_install_created_and_nothing_else() {
  pretend_iterm2_is_installed
  # Pre-existing, unrelated state that must survive the round trip.
  mkdir -p "$HOME/.local/bin" "$XDG_CACHE_HOME/other-tool"
  printf 'not ours\n' >"$HOME/.local/bin/some-other-tool"
  printf 'keep me\n' >"$XDG_CACHE_HOME/other-tool/data"
  printf 'hello\n' >"$HOME/notes.txt"

  local before after_install after_uninstall added removed
  before="$(snapshot)"

  install_sh
  assert_status 0 "install.sh exits 0"
  after_install="$(snapshot)"

  uninstall_sh
  assert_status 0 "uninstall.sh exits 0"
  after_uninstall="$(snapshot)"

  # Nothing that existed before the install may be missing afterwards.
  removed="$(snapshot_removed "$before" "$after_uninstall")"
  if [ -z "$removed" ]; then
    pass "uninstall.sh removed nothing it did not install"
  else
    fail "uninstall.sh removed pre-existing paths: $removed"
  fi

  # Everything the install created is gone, except the directories it made
  # along the way — uninstall.sh deliberately removes files, not directories.
  added="$(snapshot_added "$before" "$after_uninstall" | grep -v '^dir ' || true)"
  if [ -z "$added" ]; then
    pass "every file and symlink install.sh created is gone"
  else
    fail "uninstall.sh left install artifacts behind: $added"
  fi

  assert_absent "$(cli_path)" "the CLI symlink is gone"
  assert_absent "$(component_path)" "the iTerm2 component is gone"
  assert_file "$HOME/.local/bin/some-other-tool" "the unrelated tool survives"
  assert_file "$XDG_CACHE_HOME/other-tool/data" "an unrelated cache survives"
  assert_file "$HOME/notes.txt" "an unrelated home file survives"

  # Sanity: the install really did create something, so the assertions above
  # are not passing vacuously.
  if [ "$before" = "$after_install" ]; then
    fail "install.sh created nothing — the round-trip assertions are vacuous"
  else
    pass "the round trip was not vacuous (install.sh did create artifacts)"
  fi
}

test_uninstall_leaves_a_foreign_cli_and_component_alone() {
  pretend_iterm2_is_installed
  mkdir -p "$HOME/.local/bin" "$(autolaunch_dir)"
  printf 'a real binary the user put here\n' >"$(cli_path)"
  printf '# somebody else ClaudeUsage.py\n' >"$(component_path)"

  uninstall_sh
  assert_status 0 "uninstall.sh exits 0"
  assert_file_contains "$(cli_path)" "a real binary the user put here" \
    "a non-symlink at the CLI path is left alone"
  assert_file_contains "$(component_path)" "somebody else" \
    "an unmarked component is left alone"
  assert_output_contains "not a symlink installed by this project" \
    "uninstall.sh explains why it left the CLI"
  assert_output_contains "not installed by this project" \
    "uninstall.sh explains why it left the component"
}

test_uninstall_leaves_a_symlink_that_points_somewhere_else() {
  mkdir -p "$HOME/.local/bin" "$HOME/elsewhere"
  printf 'other project\n' >"$HOME/elsewhere/claude-usage"
  ln -sfn "$HOME/elsewhere/claude-usage" "$(cli_path)"

  uninstall_sh
  assert_status 0 "uninstall.sh exits 0"
  assert_symlink_to "$(cli_path)" "$HOME/elsewhere/claude-usage" \
    "a symlink to another target is preserved"
  assert_output_contains "symlink points somewhere else" \
    "uninstall.sh explains why it left the symlink"
}

test_uninstall_removes_only_its_own_cache_directory() {
  # uninstall.sh:30 is `rm -rf "${XDG_CACHE_HOME:-$HOME/.cache}/claude-usage"`.
  # This is the single most destructive line in the repo, so it gets its own
  # test with a neighbour directory that must survive.
  mkdir -p "$XDG_CACHE_HOME/claude-usage" "$XDG_CACHE_HOME/other-tool"
  printf '{"cached": true}\n' >"$XDG_CACHE_HOME/claude-usage/usage.json"
  printf 'keep me\n' >"$XDG_CACHE_HOME/other-tool/data"

  uninstall_sh
  assert_status 0 "uninstall.sh exits 0"
  assert_absent "$XDG_CACHE_HOME/claude-usage" "the project's cache directory is removed"
  assert_file "$XDG_CACHE_HOME/other-tool/data" "a neighbouring cache directory survives"
  assert_file_contains "$HOME/.cache/other-tool/data" "keep me" \
    "the neighbour's contents are untouched"
  assert_output_contains "removed cache" "uninstall.sh reports the cache removal"
}

test_uninstall_on_a_never_installed_system_is_a_noop() {
  pretend_iterm2_is_installed
  printf 'hello\n' >"$HOME/notes.txt"

  local before after
  before="$(snapshot)"
  uninstall_sh
  after="$(snapshot)"

  assert_status 0 "uninstall.sh exits 0 with nothing installed"
  assert_snapshots_equal "$before" "$after" \
    "uninstall.sh changes nothing when nothing is installed"
  case "$LAST_OUT" in
    *"x "*|*"✗"*) fail "uninstall.sh printed an error on a clean system: $LAST_OUT" ;;
    *) pass "uninstall.sh printed no error on a clean system" ;;
  esac
  # Documenting current behaviour: the `rm -rf` succeeds against a path that
  # was never there, so the cache line prints unconditionally. Harmless, but
  # asserted here so that changing it becomes a deliberate decision.
  assert_output_contains "removed cache" \
    "the cache line prints even with no cache (known cosmetic wart)"
}

test_uninstall_is_idempotent() {
  pretend_iterm2_is_installed
  install_sh
  assert_status 0 "install.sh exits 0"

  uninstall_sh
  assert_status 0 "first uninstall.sh exits 0"
  local after_first
  after_first="$(snapshot)"

  uninstall_sh
  assert_status 0 "second uninstall.sh exits 0"
  assert_snapshots_equal "$after_first" "$(snapshot)" \
    "a second uninstall.sh changes nothing"
}

# --------------------------------------------------------------------------
# Tests: the repository checkout itself
# --------------------------------------------------------------------------

test_install_and_uninstall_do_not_modify_the_repo_checkout() {
  # install.sh runs `chmod +x "$REPO/bin/claude-usage"`. That is a no-op on a
  # fresh clone (the file is mode 755 in git), but it is the one write these
  # scripts make outside $HOME, so it is worth pinning down.
  pretend_iterm2_is_installed

  local before after
  before="$(cd "$REPO_ROOT" && find . -path ./.git -prune -o -print | LC_ALL=C sort)"
  local mode_before mode_after
  mode_before="$(file_mode "$REPO_ROOT/bin/claude-usage")"

  install_sh
  assert_status 0 "install.sh exits 0"
  uninstall_sh
  assert_status 0 "uninstall.sh exits 0"

  after="$(cd "$REPO_ROOT" && find . -path ./.git -prune -o -print | LC_ALL=C sort)"
  mode_after="$(file_mode "$REPO_ROOT/bin/claude-usage")"

  if [ "$before" = "$after" ]; then
    pass "the repo checkout gained and lost no files"
  else
    fail "the repo checkout changed:"
    diff <(printf '%s\n' "$before") <(printf '%s\n' "$after") >&2
  fi
  if [ "$mode_before" = "$mode_after" ]; then
    pass "bin/claude-usage keeps its mode ($mode_after)"
  else
    fail "bin/claude-usage mode changed: $mode_before -> $mode_after"
  fi
}

# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

run_test() {
  local name="$1"
  TESTS_RUN=$((TESTS_RUN + 1))
  CURRENT_FAILURES=0
  SKIP_REASON=""

  sandbox_up
  "$name"
  sandbox_down

  if [ -n "$SKIP_REASON" ]; then
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
    printf '  skip %s\n         (%s)\n' "$name" "$SKIP_REASON"
  elif [ "$CURRENT_FAILURES" -eq 0 ]; then
    TESTS_PASSED=$((TESTS_PASSED + 1))
    printf '  ok   %s\n' "$name"
  else
    TESTS_FAILED=$((TESTS_FAILED + 1))
    printf '  FAIL %s (%d assertion(s))\n' "$name" "$CURRENT_FAILURES"
  fi
}

main() {
  if [ ! -x "$REPO_ROOT/install.sh" ] || [ ! -x "$REPO_ROOT/uninstall.sh" ]; then
    printf 'FATAL: install.sh / uninstall.sh not found or not executable under %s\n' \
      "$REPO_ROOT" >&2
    exit 2
  fi

  printf 'install.sh / uninstall.sh test suite\n'
  printf '  repo:      %s\n' "$REPO_ROOT"
  printf '  real HOME: %s (never written to — see the SAFETY note at the top)\n\n' "$REAL_HOME"

  run_test test_fresh_install_creates_the_cli_and_the_iterm2_component
  run_test test_fresh_install_touches_only_the_two_documented_paths
  run_test test_installed_cli_runs_demo_without_network_or_credentials
  run_test test_install_is_idempotent
  run_test test_install_refuses_to_clobber_a_real_file_at_the_cli_path
  run_test test_install_leaves_a_foreign_iterm2_component_alone
  run_test test_install_replaces_a_component_it_installed_itself
  run_test test_install_without_iterm2_still_installs_the_cli
  run_test test_uninstall_removes_exactly_what_install_created_and_nothing_else
  run_test test_uninstall_leaves_a_foreign_cli_and_component_alone
  run_test test_uninstall_leaves_a_symlink_that_points_somewhere_else
  run_test test_uninstall_removes_only_its_own_cache_directory
  run_test test_uninstall_on_a_never_installed_system_is_a_noop
  run_test test_uninstall_is_idempotent
  run_test test_install_and_uninstall_do_not_modify_the_repo_checkout

  printf '\n----------------------------------------------------------------------\n'
  printf 'Ran %d tests: %d passed, %d failed, %d skipped\n' \
    "$TESTS_RUN" "$TESTS_PASSED" "$TESTS_FAILED" "$TESTS_SKIPPED"
  if [ "$TESTS_FAILED" -eq 0 ]; then
    printf '\nOK\n'
    exit 0
  fi
  printf '\nFAILED\n'
  exit 1
}

main "$@"
