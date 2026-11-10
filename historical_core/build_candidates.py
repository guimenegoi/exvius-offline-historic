"""Deterministic research-only index from checked-in Global community data.

Never assigns native IDs to community events or promotes candidates to
playable/eligible status. Reruns and JP-derived archive dates are excluded.
"""
from collections import Counter
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).with_name("candidates_2017_2024.json")


def build():
    banners = json.loads((ROOT / "source/server/gacha_community.json").read_text(encoding="utf-8"))["banners"]
    events = json.loads((ROOT / "source/server/community_events.json").read_text(encoding="utf-8"))["events"]
    rows = []
    rejected_dates = []
    for b in banners:
        day = str(b.get("release", ""))
        if not ("2017-01-01" <= day <= "2024-10-30"):
            continue
        try:
            date.fromisoformat(day)
        except ValueError:
            rejected_dates.append({"kind": "banner", "name": b.get("name"), "raw_date": day})
            continue
        rows.append({
            "key": "banner:" + str(b["id"]), "kind": "banner",
            "name": b["name"], "release": day, "confidence": "C",
            "source": "source/server/gacha_community.json",
            "native_id": str(b["id"]), "status": "unverified_historical_candidate",
        })
    for event in events:
        if event.get("region") != "global":
            continue
        day = str(event.get("start", ""))
        if not ("2017-01-01" <= day <= "2024-10-30"):
            continue
        try:
            date.fromisoformat(day)
        except ValueError:
            rejected_dates.append({"kind": "community_event", "name": event.get("name"), "raw_date": day})
            continue
        url = event.get("url")
        if not url:
            continue
        # The community event may be a rerun, and page dates can reflect
        # another instance. Preserve occurrence metadata, never infer debut.
        rows.append({
            "key": "community_event:" + url + ":" + day,
            "kind": "community_event", "name": event["name"],
            "release": day, "confidence": "C", "source": url,
            "native_id": None, "status": "unverified_historical_candidate",
            "occurrence": event.get("community", {}).get("occurrence", "unknown"),
            "date_basis": event.get("community", {}).get("date_basis", "unknown"),
        })
    rows.sort(key=lambda r: (r["release"], r["kind"], r["key"]))
    keys = [r["key"] for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate candidate keys")
    return {
        "schema_version": 1, "region": "GL", "status": "research_only",
        "description": "2017–2024 indexed community candidates, NOT validated original Global debuts or native entitlement IDs",
        "counts": dict(sorted(Counter(r["kind"] for r in rows).items())),
        "rejected_invalid_dates": rejected_dates,
        "entries": rows,
    }


def main():
    OUT.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Wrote", OUT, build()["counts"])


if __name__ == "__main__":
    main()
