#!/usr/bin/env bash
# TPM entry point: makes #{claude_usage} usable in tmux status-left/status-right.
#
#   set -g @plugin 'Tatendaz/claude-usage'
#   set -g status-right '#{claude_usage} | %H:%M '
#
# The placeholder expands to a colored segment like:  ✳ 5h 8% wk 10% fable 17%

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Encode the path as octal bytes: neither shell syntax nor tmux format/job
# delimiters from a checkout name may become executable status-line text.
encoded_path="$(printf '%s' "$CURRENT_DIR/bin/claude-usage" | od -An -v -to1 | awk '{for (i=1; i<=NF; i++) printf "\\%s", $i}')"
usage_cmd="#(exec \"\$(printf '$encoded_path')\" --format tmux)"

do_interpolation() {
  local content="$1"
  echo "${content//\#\{claude_usage\}/$usage_cmd}"
}

update_option() {
  local option="$1"
  local value new
  value="$(tmux show-option -gqv "$option")"
  new="$(do_interpolation "$value")"
  if [ "$new" != "$value" ]; then
    tmux set-option -gq "$option" "$new"
  fi
}

main() {
  update_option "status-right"
  update_option "status-left"
}
main
