#!/usr/bin/env bash
# Sync SOTA-NA Slack member callsigns into the HamAlert SOTA trigger.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./sync.sh <slack-members.csv> <trigger-id> [--apply] [set-callsigns options]

Builds callsigns.txt from the Slack member export, then compares it with the
HamAlert trigger. Without --apply it only shows the diff (dry run).

Options:
  --apply              Back up all triggers to backups/, then update the trigger
  --max-removals N     Allow up to N callsigns to be removed in one run
                       (default: 10% of the current list, minimum 5)
  -h, --help           Show this help

Examples:
  ./sync.sh ~/Downloads/members.csv 5f1c...           # dry run
  ./sync.sh ~/Downloads/members.csv 5f1c... --apply   # apply
  ./sync.sh ~/Downloads/members.csv 5f1c... --apply --max-removals 50

Before raising --max-removals, check the "-" lines in the dry run: callsigns
that should stay can go in extra.txt instead.
USAGE
}

for arg in "$@"; do
  [[ "$arg" == "-h" || "$arg" == "--help" ]] && { usage; exit 0; }
done
if [[ $# -lt 2 ]]; then
  usage >&2
  exit 1
fi

csv="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
trigger_id="$2"
shift 2

apply=false
passthrough=()
for arg in "$@"; do
  if [[ "$arg" == "--apply" ]]; then
    apply=true
  else
    passthrough+=("$arg")
  fi
done

cd "$(dirname "$0")"
export PATH="$HOME/.cargo/bin:$PATH"

args=()
[[ -f extra.txt ]] && args+=(--extra extra.txt)
[[ -f exclude.txt ]] && args+=(--exclude exclude.txt)
python3 slack_callsigns.py "$csv" -o callsigns.txt ${args[@]+"${args[@]}"}

set_args=(--trigger-id "$trigger_id" --file callsigns.txt ${passthrough[@]+"${passthrough[@]}"})
if $apply; then
  mkdir -p backups
  hamalert-cli backup --output "backups/hamalert-$(date +%Y%m%d-%H%M%S).json"
  hamalert-cli set-callsigns "${set_args[@]}" --no-dry-run
else
  hamalert-cli set-callsigns "${set_args[@]}"
fi
