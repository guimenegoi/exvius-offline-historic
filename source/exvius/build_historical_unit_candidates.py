"""Build an audit-only Global unit identity crosswalk.

Inputs: historical_unit_debuts.json and a local copy of the external
ffbe_asset_dump catalog/unit_master.json. Do not bundle the external master.
The resulting candidates are NOT the live game's unlock allowlist.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

MASTER_URL = ("https://github.com/DaddyRaegen/ffbe_asset_dump/"
              "blob/main/catalog/unit_master.json")


def gl_index(master: dict) -> tuple[dict, dict]:
    """Use only region-qualified source identities, never a global numeric ID guess."""
    by_name = defaultdict(lambda: defaultdict(set))
    by_form_id = defaultdict(set)
    for unit in master["units"]:
        form_id = str(unit["original_id"])
        for identity in unit.get("identities", []):
            if identity.get("server") != "GL":
                continue
            name = identity.get("name")
            root = identity.get("source_unit_id")
            if not name or not root:
                continue
            by_name[name][str(root)].add(form_id)
            by_form_id[form_id].add(name)
    return by_name, by_form_id


def build_candidates(history: dict, master: dict, community: dict | None = None) -> dict:
    by_name, by_form_id = gl_index(master)
    name_dates = defaultdict(set)
    for row in history["debuts"]:
        name_dates[row["name"]].add(row["release"])
    output, counts = [], Counter()
    for row in history["debuts"]:
        families = by_name.get(row["name"], {})
        if not families:
            status = "missing_global_identity"
        elif len(name_dates[row["name"]]) > 1:
            status = "repeated_name_different_dates"
        elif row.get("access") == "conditional":
            status = "conditional_availability"
        elif len(families) > 1:
            status = "multiple_global_families"
        else:
            status = "unique_name_candidate"
        counts[status] += 1
        output.append({
            "name": row["name"],
            "release": row["release"],
            "rarity": row.get("rarity"),
            "status": status,
            "candidate_families": [
                {"base_unit_id": root, "form_ids": sorted(forms)}
                for root, forms in sorted(families.items())
            ],
            "note_line": row["note_line"],
        })
    result = {
        "version": 1,
        "usage": "AUDIT ONLY - not authoritative for live summon or reward gating",
        "source": {"global_master": MASTER_URL,
                   "history_sha256": history["source"]["sha256"]},
        "counts": dict(sorted(counts.items())),
        "units": output,
    }
    if community is not None:
        examined, mismatch, missing = 0, 0, 0
        examples = []
        for banner in community.get("banners", []):
            info = banner.get("community") or {}
            for name, raw_id in zip(info.get("units") or [], info.get("unit_ids") or []):
                examined += 1
                known = by_form_id.get(str(raw_id), set())
                if not known:
                    missing += 1
                elif name not in known:
                    mismatch += 1
                    if len(examples) < 20:
                        examples.append({"banner_id": str(banner["id"]),
                                         "unit_id": str(raw_id),
                                         "banner_name": name,
                                         "global_master_name": sorted(known)})
        result["community_id_audit"] = {
            "references_checked": examined,
            "references_with_different_global_name": mismatch,
            "references_absent_from_gl_master": missing,
            "examples": examples,
            "usage": "Diagnostic only. Never patch the upstream banner data from this report."
        }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--community", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    history = json.loads(args.history.read_text("utf-8"))
    raw_master = args.master.read_bytes()
    master = json.loads(raw_master)
    community = json.loads(args.community.read_text("utf-8")) if args.community else None
    report = build_candidates(history, master, community)
    report["source"]["global_master_sha256"] = hashlib.sha256(raw_master).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(json.dumps({"counts": report["counts"],
                      "community_id_audit": {k: v for k, v in
                          report.get("community_id_audit", {}).items() if k != "examples"}}))


if __name__ == "__main__":
    main()
