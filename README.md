# Slack-SOTA-Spots

Keeps the HamAlert SOTA trigger's callsign list in sync with SOTA-NA Slack members, so
spots for every member reach #spots without hand-maintaining the list. HamAlert still
delivers the spots, and nothing here calls the SOTA API.

## One-time setup
1. The HamAlert CLI with `set-callsigns` is installed at `~/.cargo/bin/hamalert-cli`, built from
   `~/devel/personal/hamalert-cli` (branch `set-callsigns`). To rebuild it, put Homebrew's keg-only
   rustup on PATH first:
   `export PATH=/opt/homebrew/opt/rustup/bin:$PATH && cargo install --path ~/devel/personal/hamalert-cli`
2. `~/.cargo/bin/hamalert-cli auth login`: prompts once and stores the password in the macOS Keychain.
3. `~/.cargo/bin/hamalert-cli backup --output current.json`, then find your SOTA trigger's `_id` in the file.

## Each sync
1. Export the member list from Slack: Workspace settings → Manage members → Export member list (CSV).
2. `./sync.sh ~/Downloads/<export>.csv <trigger-id>`: dry run. Prints members without a
   recognizable callsign and the `+added` / `-removed` diff against HamAlert.
3. `./sync.sh ~/Downloads/<export>.csv <trigger-id> --apply`: backs up all triggers to `backups/`, then updates.
   If more than 10% of the list (minimum 5) would be removed, the update is refused. Review the `-`
   lines, then either add callsigns that should stay to `extra.txt` or allow the removals with
   `--apply --max-removals N`. `./sync.sh --help` lists all options.

## Overrides
- `extra.txt`: callsigns to always include (members whose Slack name has no callsign).
- `exclude.txt`: callsigns to always drop (false matches).

Both are one callsign per line; `#` starts a comment.

## Tests
`python3 -m unittest`
