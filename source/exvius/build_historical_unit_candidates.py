"""Audit the historical unit debuts against ORIGINAL preserved Global master rows.

Uses F_UNIT_MST + F_TEXT_UNITS_NAME fetched from the official data-001 pack.
The output is AUDIT ONLY, not a playable unit-ID allowlist. Base rarity can
identify a candidate family but does not prove historical awakening availability.

    python3 source/exvius/build_historical_unit_candidates.py
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
MASTER_FIELD = "3HriTp6B"
ROOT_FIELD = "woghJa61"
RARITY_FIELD = "9fW0TePj"
TEXT_PREFIX = "MST_UNIT_NAME_"


def load_ndjson(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def original_global_index(mst: list[dict], texts: list[dict]) -> tuple[dict, dict, dict]:
    english = {
        row["key"][len(TEXT_PREFIX):]: row["v"][0]
        for row in texts if row.get("key", "").startswith(TEXT_PREFIX) and row.get("v")
    }
    by_name = defaultdict(lambda: defaultdict(set))
    by_id = defaultdict(set)
    base_rarity = {}
    for row in mst:
        unit_id = str(row[MASTER_FIELD])
        name = english.get(unit_id)
        root = str(row[ROOT_FIELD])
        if not name or not root:
            continue
        by_name[name][root].add(unit_id)
        by_id[unit_id].add(name)
        if unit_id == root:
            base_rarity[root] = str(row[RARITY_FIELD])
    return by_name, by_id, base_rarity


def requested_rarity(text: str | None) -> str | None:
    if not text:
        return None
    if text.startswith("NV"):
        return "7"  # In the preserved master the NV starting rarity code is 7.
    match = re.match(r"^[1-9]", text)
    return match.group() if match else None


def build_candidates(history: dict, mst: list[dict], texts: list[dict],
                     community: dict | None = None) -> dict:
    by_name, by_id, base_rarity = original_global_index(mst, texts)
    name_dates = defaultdict(set)
    for row in history["debuts"]:
        name_dates[row["name"]].add(row["release"])
    output, counts = [], Counter()
    for row in history["debuts"]:
        families = by_name.get(row["name"], {})
        minimum = requested_rarity(row.get("rarity"))
        matching = {
            root for root in families
            if minimum is not None and base_rarity.get(root) == minimum
        }
        if not families:
            status = "missing_original_global_name"
        elif len(name_dates[row["name"]]) > 1:
            status = "repeated_name_different_dates"
        elif row.get("access") == "conditional":
            status = "conditional_availability"
        elif minimum is None:
            status = "unverified_initial_rarity"
        elif len(matching) == 1:
            status = "unique_rarity_candidate"
        elif not matching:
            status = "rarity_mismatch"
        else:
            status = "multiple_original_families"
        counts[status] += 1
        output.append({
            "name": row["name"],
            "release": row["release"],
            "rarity": row.get("rarity"),
            "status": status,
            "candidate_families": [
                {"base_unit_id": root, "base_rarity": base_rarity.get(root),
                 "matching_initial_rarity": root in matching,
                 "form_ids": sorted(forms)}
                for root, forms in sorted(families.items())
            ],
            "note_line": row["note_line"],
        })
    report = {
        "version": 2,
        "usage": "AUDIT ONLY - not authoritative for live summon or reward gating",
        "source": {"master": "Elvlin/exvius-offline official data-001 static/mst_decoded/F_UNIT_MST.ndjson",
                   "names": "Elvlin/exvius-offline official data-001 static/text_decoded/F_TEXT_UNITS_NAME.ndjson",
                   "history_sha256": history["source"]["sha256"]},
        "counts": dict(sorted(counts.items())),
        "units": output,
    }
    if community is not None:
        examined, mismatch, missing = 0, 0, 0
        examples = []
        for banner in community.get("banners", []):
            info = banner.get("community") or {}
            for name, unit_id in zip(info.get("units") or [], info.get("unit_ids") or []):
                examined += 1
                known = by_id.get(str(unit_id), set())
                if not known:
                    missing += 1
                elif name not in known:
                    mismatch += 1
                    if len(examples) < 20:
                        examples.append({"banner_id": str(banner["id"]),
                                         "unit_id": str(unit_id),
                                         "banner_name": name,
                                         "original_global_name": sorted(known)})
        report["community_id_audit"] = {
            "references_checked": examined,
            "references_with_different_global_name": mismatch,
            "references_absent_from_original_text": missing,
            "examples": examples,
            "usage": "Diagnostic only. Do not rewrite upstream banner data from this report."
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, default=ROOT / "source/server/content/historical_unit_debuts.json")
    parser.add_argument("--mst", type=Path, default=ROOT / "data/mst_decoded/F_UNIT_MST.ndjson")
    parser.add_argument("--names", type=Path, default=ROOT / "data/text_decoded/F_TEXT_UNITS_NAME.ndjson")
    parser.add_argument("--community", type=Path, default=ROOT / "source/server/gacha_community.json")
    parser.add_argument("--output", type=Path, default=ROOT / "source/server/content/historical_unit_candidates.json")
    args = parser.parse_args()
    history = json.loads(args.history.read_text(encoding="utf-8"))
    mst, texts = load_ndjson(args.mst), load_ndjson(args.names)
    community = json.loads(args.community.read_text(encoding="utf-8"))
    report = build_candidates(history, mst, texts, community)
    for name, source in (("master_sha256", args.mst), ("names_sha256", args.names)):
        report["source"][name] = hashlib.sha256(source.read_bytes()).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"counts": report["counts"],
                      "community_id_audit": {k: v for k, v in report["community_id_audit"].items()
                                             if k != "examples"}}))


if __name__ == "__main__":
    main()
