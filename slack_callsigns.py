#!/usr/bin/env python3
"""Extract amateur radio callsigns from a Slack member-list CSV export.

Usage:
    python3 slack_callsigns.py members.csv [-o callsigns.txt]
        [--extra extra.txt] [--exclude exclude.txt]

The first callsign in the Slack display name wins; if the display name has
none, the full name is checked. Only active members are included
(billing-active = 1, when the export has that column). Members with no callsign in either are
skipped. Writes a sorted, de-duplicated list of base callsigns (one per line)
to stdout or -o. A summary and the members with no recognizable callsign are
printed to stderr.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

# Prefix: 1-2 chars with at least one letter (W, KD, VE, 4X, E7), then a
# digit, then a 1-4 letter suffix. Optional portable prefix/suffix around it.
CALLSIGN_RE = re.compile(
    r"^(?:[A-Z0-9]{1,4}/)?"
    r"((?:[A-Z]{1,2}|[0-9][A-Z]|[A-Z][0-9])[0-9][A-Z]{1,4})"
    r"(?:/[A-Z0-9]{1,4})?$"
)
TOKEN_SPLIT_RE = re.compile(r"[\s\-–—|()\[\],:;]+")

DISPLAY_HEADERS = {"displayname", "display name", "display_name"}
FULL_HEADERS = {"fullname", "full name", "full_name", "real name", "realname"}
STATUS_HEADERS = {"status", "account type", "account_type"}
SKIP_STATUS_WORDS = ("deactivated", "bot")
ACTIVE_HEADERS = {"billing-active"}


def extract_callsign(name):
    """Return the first base callsign found in name, or None."""
    if not name:
        return None
    for token in TOKEN_SPLIT_RE.split(name.upper()):
        match = CALLSIGN_RE.match(token.strip(".'\"!?"))
        if match:
            return match.group(1)
    return None


def base_callsign(call):
    """Strip portable prefixes/suffixes: VE7/W1ABC/P -> W1ABC."""
    match = CALLSIGN_RE.match(call.strip().upper())
    return match.group(1) if match else None


def read_list_file(path):
    """Read one callsign per line; blank lines and # comments are ignored."""
    if path is None:
        return set()
    calls = set()
    for line in Path(path).read_text().splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            calls.add(base_callsign(line) or line.upper())
    return calls


def find_column(headers, wanted):
    for header in headers:
        if header.strip().lower() in wanted:
            return header
    return None


def parse_members(rows, headers):
    """Return (callsigns, names_without_callsign, member_count)."""
    display_col = find_column(headers, DISPLAY_HEADERS)
    full_col = find_column(headers, FULL_HEADERS)
    status_col = find_column(headers, STATUS_HEADERS)
    active_col = find_column(headers, ACTIVE_HEADERS)
    if not display_col and not full_col:
        raise ValueError(
            "No display name or full name column found. Headers: " + ", ".join(headers)
        )

    callsigns = set()
    missing = []
    members = 0
    for row in rows:
        status = (row.get(status_col) or "").lower() if status_col else ""
        if any(word in status for word in SKIP_STATUS_WORDS):
            continue
        if active_col and (row.get(active_col) or "").strip() != "1":
            continue
        members += 1
        display = (row.get(display_col) or "").strip() if display_col else ""
        full = (row.get(full_col) or "").strip() if full_col else ""
        call = extract_callsign(display) or extract_callsign(full)
        if call:
            callsigns.add(call)
        else:
            missing.append(display or full or "(no name)")
    return callsigns, missing, members


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("csv", help="Slack member list export (CSV)")
    parser.add_argument("-o", "--output", help="write callsigns here instead of stdout")
    parser.add_argument("--extra", help="callsigns to always include")
    parser.add_argument("--exclude", help="callsigns to always remove")
    args = parser.parse_args(argv)

    with open(args.csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        try:
            callsigns, missing, members = parse_members(reader, reader.fieldnames or [])
        except ValueError as e:
            sys.exit(f"error: {e}")

    parsed = len(callsigns)
    callsigns |= read_list_file(args.extra)
    callsigns -= read_list_file(args.exclude)

    output = "\n".join(sorted(callsigns)) + "\n"
    if args.output:
        Path(args.output).write_text(output)
    else:
        sys.stdout.write(output)

    print(
        f"{members} members, {parsed} callsigns parsed, {len(callsigns)} after overrides",
        file=sys.stderr,
    )
    if missing:
        print(f"{len(missing)} members with no recognizable callsign:", file=sys.stderr)
        for name in sorted(missing, key=str.lower):
            print(f"  {name}", file=sys.stderr)


if __name__ == "__main__":
    main()
