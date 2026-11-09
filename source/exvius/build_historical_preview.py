"""Build an explicitly UNVERIFIED 2016-06 to 2016-07 gameplay preview.

The preview is test-only. Never promote this file to the verified catalogue.
Only native base rarity is allowed; date and rarity ceiling still need audit.
"""
from __future__ import annotations

import json
from pprint import pformat
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "source/server/content/historical_unit_releases_preview.json"
MODULE = ROOT / "source/server/historical_preview_data.py"
CUTOFF = "2016-07"


def build_preview(launch: dict, debuts: dict) -> dict:
    if launch["status"] != "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE":
        raise ValueError("Launch evidence status changed.")
    units = {}
    launch_count = 0
    for record in launch["units"]:
        channel = record.get("catalogue_acquisition")
        candidates = record["candidates"]
        if channel not in ("rare", "friend") or len(candidates) != 1:
            continue
        unit_id = candidates[0]["base_unit_id"]
        rarity = str(record["base_rarity"])
        if unit_id in units:
            raise ValueError("Repeated base unit in launch roster.")
        units[unit_id] = {
            "base_rarity": rarity, "channels": [channel],
            "rarities": {rarity: "2016-06-30"},
        }
        launch_count += 1

    july = {"Kefka", "Golbez", "Chizuru", "Hayate", "Locke", "Artemios"}
    included = set()
    for record in debuts["units"]:
        if record["name"] not in july or record["release"][:7] != CUTOFF:
            continue
        if record["status"] != "unique_rarity_candidate":
            raise ValueError("July historical debut identity remains ambiguous.")
        matching = [unit for unit in record["candidate_families"]
                    if unit["matching_initial_rarity"]]
        if len(matching) != 1:
            raise ValueError("July debut does not have one original Global root.")
        unit_id = matching[0]["base_unit_id"]
        if unit_id in units:
            raise ValueError("July debut already in launch roster.")
        rarity = matching[0]["base_rarity"]
        units[unit_id] = {
            "base_rarity": rarity, "channels": ["rare"],
            "rarities": {rarity: record["release"]},
        }
        included.add(record["name"])
    if included != july or launch_count != 63 or len(units) != 69:
        raise ValueError(f"Incomplete experimental launch/July coverage: {len(units)}, {included}")
    return {
        "schema": 1, "status": "preview", "latest_month": CUTOFF,
        "warnings": [
            "UNVERIFIED TEST ONLY: June 30 debut assumption for launch roster",
            "Only original base rarity available, not historically reconstructed rarity ceilings",
            "Preview gates dated summons and selected routes/rewards; it does NOT reconstruct all historical story, quest, shop or event inventories",
            "Rates are authored by upstream, not authenticated historical 2016 odds",
        ],
        "sources": [
            launch["source_url"],
            launch.get("catalogue_source_url", ""),
            "https://exvius.fandom.com/wiki/Update_Schedule",
            "Original Global F_UNIT_MST and F_TEXT_UNITS_NAME",
        ],
        "units": dict(sorted(units.items())),
    }


def main():
    launch = json.loads((ROOT / "source/server/content/historical_launch_candidates.json").read_text())
    debuts = json.loads((ROOT / "source/server/content/historical_unit_candidates.json").read_text())
    report = build_preview(launch, debuts)
    DEST.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # Chaquopy imports modules from app.imy; ordinary sibling Path.read_text
    # does not work inside a zipped .pyc bundle. Ship a compiled data module.
    MODULE.write_text('"""Audited *candidate* preview, not verified historic releases."""\n'
                      + "DOCUMENT = " + pformat(report, sort_dicts=True, width=100) + "\n")
    print("Preview units", len(report["units"]), "launch", 63, "July new", 6)


if __name__ == "__main__":
    main()
