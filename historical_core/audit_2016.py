"""Read-only provenance audit: original 2016 GL debuts versus Offline records."""
from collections import Counter
from datetime import date
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).with_name("audit_2016.json")


def read(path, key):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))[key]


def build():
    entries = read("historical_core/catalogue_2016.json", "entries")
    archived = read("source/server/event_archive.json", "events")
    banners = read("source/server/gacha_community.json", "banners")
    bundles = read("source/server/global_bundles.json", "bundles")
    events = []
    for entry in entries:
        if entry["kind"] != "event":
            continue
        matches = sorted((e for e in archived if e.get("name") == entry["name"]),
                         key=lambda x: (str(x.get("release")), str(x["area"])))
        variants = []
        for match in matches:
            d = match.get("release")
            later = bool(d and date.fromisoformat(d) > date.fromisoformat(entry["release"]))
            variants.append({
                "area": str(match["area"]),
                "archive_release": d,
                "missions": list(map(str, match.get("missions", []))),
                "kind": match.get("kind"),
                "source_page": match.get("source_page"),
                "later_than_original_debut": later,
            })
        events.append({
            "name": entry["name"], "original_global_debut": entry["release"],
            "contemporary_source": entry["source"], "confidence": entry["confidence"],
            "original_native_id": None,
            "original_mission_and_reward_identity_verified": False,
            "archive_name_matches": variants,
            "decision": "original_content_not_identified",
        })
    banner_rows = []
    by_id = {str(b["id"]): b for b in banners}
    for entry in entries:
        if entry["kind"] != "banner":
            continue
        b = by_id[entry["native_id"]]
        community = b.get("community", {})
        featured_names = community.get("units") or []
        featured_ids = community.get("unit_ids") or []
        pool = b.get("pool", {})
        # Early banners use flat weighted rows; later banners use tiers.
        # A flat pool has no separate 'featured' field to compare.
        tiered = isinstance(pool, dict)
        pool_featured = sorted({
            str(u)
            for tier in pool.get("tiers", []) if tiered
            for u in tier.get("featured", [])
        }) if tiered else None
        name_count = len(featured_names)
        id_count = len(featured_ids)
        inconsistent = name_count != id_count or (
            pool_featured is not None and set(featured_ids) != set(pool_featured)
        )
        banner_rows.append({
            "catalogue_id": str(b["id"]), "release": entry["release"],
            "name": entry["name"],
            "community_featured_names": featured_names,
            "community_featured_ids": featured_ids,
            "pool_featured_ids": pool_featured,
            "featured_count_mismatch": name_count != id_count,
            "featured_pool_mismatch": (set(featured_ids) != set(pool_featured))
            if pool_featured is not None else None,
            "original_global_id_verified": False,
            "original_rates_and_pool_verified": False,
            "decision": "requires_pool_review" if inconsistent else "community_index_only",
        })
    return {
        "schema_version": 1,
        "status": "research_only",
        "method": "Exact name matches and source fields; NOT original ID equivalence",
        "counts": {
            "original_events": len(events),
            "events_with_archived_name_matches": sum(bool(e["archive_name_matches"]) for e in events),
            "archived_variants": sum(len(e["archive_name_matches"]) for e in events),
            "banners": len(banner_rows),
            "banners_with_featured_mismatch": sum(b["featured_count_mismatch"] for b in banner_rows),
            "cash_shop_bundles_in_offline_index": len(bundles),
        },
        "events": events,
        "banners": banner_rows,
        "cash_shop_warning": {
            "original_2016_early_bird_usd": "3.99",
            "offline_early_bird_usd": next(
                (str(x.get("usd")) for x in bundles if x.get("name") == "Early Bird Offer"), None
            ),
            "equivalence": "not_established",
            "action": "do_not_backdate_or_enable_offline_bundle",
        },
    }


def main():
    data = build()
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data["counts"], indent=2))


if __name__ == "__main__":
    main()
