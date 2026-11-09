"""Cross-check the 2016 Global banner evidence; never authorize summons."""
from collections import Counter, defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def audit(banners, debuts, events):
    first = defaultdict(list)
    for unit in debuts:
        if unit.get("name") and unit.get("release"):
            first[unit["name"]].append(unit["release"])
    anomalies = []
    totals = Counter()
    for banner in banners:
        release = banner.get("release", "")
        if not release.startswith("2016"):
            continue
        totals["banners"] += 1
        community = banner.get("community") or {}
        names = community.get("units") or []
        ids = community.get("unit_ids") or []
        if len(names) != len(ids):
            anomalies.append({
                "type": "featured_name_id_count_mismatch",
                "banner_id": str(banner["id"]),
                "release": release,
                "names": names,
                "unit_ids": ids,
                "note": "Do not assume names and IDs are positional matches.",
            })
        for name in names:
            totals["featured_name_mentions"] += 1
            dates = first.get(name, [])
            if not dates:
                anomalies.append({
                    "type": "no_matching_editorial_debut",
                    "banner_id": str(banner["id"]),
                    "release": release,
                    "name": name,
                    "note": "An absent debut row is NOT proof that the unit was unreleased.",
                })
            elif min(dates) > release:
                anomalies.append({
                    "type": "debut_after_banner",
                    "banner_id": str(banner["id"]),
                    "release": release,
                    "name": name,
                    "earliest_debut": min(dates),
                    "note": "Requires independent GL provenance review.",
                })
    totals["event_areas_2016"] = sum(str(e.get("release") or "").startswith("2016") for e in events)
    totals["event_areas_undated"] = sum(not e.get("release") for e in events)
    totals["anomalies"] = len(anomalies)
    return {
        "schema": 1,
        "region": "GL",
        "status": "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE",
        "summary": dict(sorted(totals.items())),
        "anomalies": sorted(anomalies, key=lambda a: (a["release"], a["banner_id"], a["type"], a.get("name", ""))),
    }


def main():
    root = ROOT / "source/server"
    banners = json.loads((root / "gacha_community.json").read_text())["banners"]
    debuts = json.loads((root / "content/historical_unit_debuts.json").read_text())["debuts"]
    events = json.loads((root / "event_archive.json").read_text())["events"]
    result = audit(banners, debuts, events)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
