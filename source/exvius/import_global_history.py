"""Import FFBE Global unit debut evidence from an Obsidian chronology note.

This is a SOURCE CATALOGUE, not a playable release-ID allowlist: repeated unit
names and regenerated community banner IDs require client-master verification.
Usage: python3 source/exvius/import_global_history.py --note PATH --output PATH
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import re

LINE = re.compile(r"^- \*\*(\d{4}-\d{2}-\d{2})\*\*.*?:LiSparkles: Unidades lançadas — (.+)$")
RARITY = re.compile(r"^(?P<name>.+?)\s+(?P<rarity>[1-9](?:\s*[~-]\s*[1-9])?★|NV\+?)(?P<tail>.*)$")
LATER_RARITY = re.compile(r"\s+[1-9](?:\s*[~-]\s*[1-9])?★|\s+NV(?:\s|$)")
SOURCE_URL = "https://exvius.fandom.com/wiki/Update_Schedule"


def split_outside_parentheses(text: str) -> list[str]:
    """Split a release list, never splitting commas inside editorial notes."""
    items, part, depth = [], [], 0
    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            items.append("".join(part).strip())
            part = []
        else:
            part.append(char)
    if part:
        items.append("".join(part).strip())
    return [part for part in items if part]


def parse_debuts(note: str) -> dict:
    rows, warnings = [], []
    for line_number, line in enumerate(note.splitlines(), 1):
        match = LINE.match(line)
        if not match:
            continue
        released, units = match.groups()
        date.fromisoformat(released)
        for item in split_outside_parentheses(units):
            parsed = RARITY.match(item)
            if parsed:
                name = parsed["name"].strip()
                rarity = parsed["rarity"]
                tail = parsed["tail"].strip()
                # Some source lines accidentally omit the comma between units.
                if LATER_RARITY.search(tail):
                    warnings.append({"line": line_number, "release": released,
                                     "text": item, "reason": "multiple-units-in-entry"})
                    continue
                if tail and not (tail.startswith("(") or tail.startswith("*")):
                    warnings.append({"line": line_number, "release": released,
                                     "text": item, "reason": "unexpected-trailing-text"})
                    continue
                access = "conditional" if tail else "unqualified"
            else:
                # Valid sources occasionally omit rarity (e.g. Reberta / Zyrus).
                # Do not infer IDs for these name-only records.
                name, rarity, access = item.strip(), None, "unqualified"
                if "(" in name or "★" in name or "," in name:
                    warnings.append({"line": line_number, "release": released,
                                     "text": item, "reason": "unparsed-rarity"})
                    continue
            if not name:
                warnings.append({"line": line_number, "release": released,
                                 "text": item, "reason": "empty-name"})
                continue
            rows.append({"name": name, "release": released, "rarity": rarity,
                         "access": access, "note_line": line_number,
                         **({"annotation": tail} if parsed and tail else {})})
    unique = {(row["name"], row["release"], row["rarity"]): row for row in rows}
    records = sorted(unique.values(), key=lambda row: (row["release"], row["name"], row["rarity"] or ""))
    by_name = defaultdict(set)
    for row in records:
        by_name[row["name"]].add(row["release"])
    ambiguous = [{"name": name, "dates": sorted(dates)} for name, dates in sorted(by_name.items())
                 if len(dates) > 1]
    return {"debuts": records, "ambiguous_names": ambiguous, "parse_warnings": warnings}


def audit_community_banners(debuts: list, community: dict) -> dict:
    """Collect diagnostic collisions only. Never authorize a unit ID here."""
    dates_by_name = defaultdict(set)
    for row in debuts:
        dates_by_name[row["name"]].add(row["release"])
    names_by_id = defaultdict(set)
    exact = set()
    for banner in community.get("banners", []):
        info = banner.get("community") or {}
        names, ids = info.get("units") or [], info.get("unit_ids") or []
        for name, unit_id in zip(names, ids):
            names_by_id[str(unit_id)].add(name)
            if info.get("release") in dates_by_name.get(name, ()):
                exact.add((str(unit_id), name, info["release"]))
    collisions = [{"unit_id": unit_id, "names": sorted(names)}
                  for unit_id, names in names_by_id.items() if len(names) > 1]
    return {
        "banner_count": len(community.get("banners", [])),
        "matched_name_date_pairs": len(exact),
        "matched_distinct_unit_ids": len({row[0] for row in exact}),
        "colliding_unit_ids": sorted(collisions, key=lambda row: row["unit_id"]),
        "warning": "Community banner unit IDs are not authoritative: verify against original Global F_UNIT_MST and English text tables."
    }


def import_note(note_bytes: bytes, community: dict | None = None) -> dict:
    parsed = parse_debuts(note_bytes.decode("utf-8-sig"))
    result = {"version": 1, "source": {
        "kind": "user-curated-global-chronology",
        "reference": SOURCE_URL,
        "sha256": hashlib.sha256(note_bytes).hexdigest(),
        "scope": "reported Global unit debut names, not client unit-ID unlocks"
    }, **parsed}
    if community is not None:
        result["community_audit"] = audit_community_banners(parsed["debuts"], community)
    return result


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--note", required=True, type=Path)
    cli.add_argument("--output", required=True, type=Path)
    cli.add_argument("--community", type=Path, help="Optional upstream gacha_community.json for collision audit")
    args = cli.parse_args()
    community = json.loads(args.community.read_text(encoding="utf-8")) if args.community else None
    result = import_note(args.note.read_bytes(), community)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "unit_debuts": len(result["debuts"]),
        "ambiguous_names": len(result["ambiguous_names"]),
        "parse_warnings": len(result["parse_warnings"]),
        "community_id_collisions": len((result.get("community_audit") or {}).get("colliding_unit_ids", []))
    }))


if __name__ == "__main__":
    main()
