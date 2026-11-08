"""Audit a reported early-Global roster without declaring summon eligibility.

The source post does not distinguish Rare Summon from Friend Point and story
rewards. This script resolves native GL base-unit IDs, but NEVER writes the
verified historical_unit_releases.json used by the transaction gate.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from build_historical_unit_candidates import load_ndjson, original_global_index

ROOT = Path(__file__).resolve().parents[2]


def audit_snapshot(snapshot: dict, mst: list[dict], texts: list[dict]) -> dict:
    if snapshot.get("schema") != 1 or snapshot.get("status") != "unverified_launch_snapshot":
        raise ValueError("Only a traceable unverified launch snapshot can be audited.")
    by_name, _by_id, base_rarities = original_global_index(mst, texts)
    corroborated = set(snapshot.get("draw_reported_names") or [])
    rows, summary, channels = [], Counter(), Counter()
    for source in snapshot["units"]:
        name = source["source_name"]
        master_name = source.get("master_name", name)
        rarity = str(source["base_rarity"])
        identities = by_name.get(master_name, {})
        matches = [(root, forms) for root, forms in sorted(identities.items())
                   if base_rarities.get(root) == rarity]
        if not matches:
            status = "missing_or_rarity_conflict"
        elif len(matches) != 1:
            status = "ambiguous_native_identity"
        elif source.get("acquisition") == "story":
            status = "story_candidate_not_rare"
        elif source.get("acquisition") == "pre_registration":
            status = "registration_candidate_not_rare"
        elif master_name in corroborated:
            status = "reported_drawable_acquisition_unverified"
        else:
            status = "native_identity_match_acquisition_unknown"
        summary[status] += 1
        acquisition = source.get("catalogue_acquisition", "unclassified")
        channels[acquisition] += 1
        rows.append({
            "source_name": name, "master_name": master_name,
            "base_rarity": rarity,
            "acquisition": source.get("acquisition", "unknown"),
            "catalogue_acquisition": acquisition,
            "status": status,
            "candidates": [
                {"base_unit_id": root, "form_ids": sorted(forms)}
                for root, forms in matches
            ],
        })
    return {
        "schema": 1,
        "status": "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE",
        "source_url": snapshot["source_url"],
        "source_period": snapshot["source_period"],
        "notes": "Unit presence near launch does not prove a Rare Summon, Friend Point, or June 30 release date.",
        "summary": dict(sorted(summary.items())),
        "catalogue_source_url": snapshot.get("catalogue_source_url"),
        "acquisition_summary": dict(sorted(channels.items())),
        "draw_source_url": snapshot.get("draw_source_url"),
        "draw_names_not_matched": sorted(
            corroborated - {row["master_name"] for row in rows}),
        "units": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path,
                        default=ROOT / "source/server/content/historical_launch_snapshot.json")
    parser.add_argument("--mst", type=Path, default=ROOT / "data/mst_decoded/F_UNIT_MST.ndjson")
    parser.add_argument("--names", type=Path,
                        default=ROOT / "data/text_decoded/F_TEXT_UNITS_NAME.ndjson")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "source/server/content/historical_launch_candidates.json")
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    report = audit_snapshot(snapshot, load_ndjson(args.mst), load_ndjson(args.names))
    report["sources_sha256"] = {
        "snapshot": hashlib.sha256(args.snapshot.read_bytes()).hexdigest(),
        "master": hashlib.sha256(args.mst.read_bytes()).hexdigest(),
        "names": hashlib.sha256(args.names.read_bytes()).hexdigest(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"units": len(report["units"]), "summary": report["summary"]}))


if __name__ == "__main__":
    main()
