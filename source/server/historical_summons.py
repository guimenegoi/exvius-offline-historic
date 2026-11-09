"""Pre-charge historical gate for the existing PlayerState.roll_gacha pathway.

No candidate or release dates inferred from the final Global master are trusted
as historic unlocks. The live gate requires a separate, manually verified exact
unit ID -> rarity/date/channel mapping, not yet shipped with this fork.
"""
from __future__ import annotations

import json
from pathlib import Path

from historical_progression import UnavailableContent, eligible_pool, is_released, month_cutoff

VERIFIED_INDEX = Path(__file__).resolve().parent / "content/historical_unit_releases.json"
PREVIEW_INDEX = VERIFIED_INDEX.with_name("historical_unit_releases_preview.json")


def load_verified_unit_releases(path: Path = VERIFIED_INDEX, *, preview: bool = False) -> dict[str, dict]:
    """Preview is an explicit opt-in; verified mode never reads provisional IDs."""
    if preview and path == VERIFIED_INDEX:
        # In the Android build, Chaquopy imports .pyc from app.imy rather
        # than exposing neighbouring JSON files as filesystem Paths.
        from historical_preview_data import DOCUMENT
        document = DOCUMENT
    else:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise UnavailableContent("Verified Global unit release catalogue is not available.") from error
    if (not isinstance(document, dict) or document.get("schema") != 1 or
            document.get("status") != ("preview" if preview else "verified") or
            not document.get("sources") or not isinstance(document.get("units"), dict) or
            not document["units"]):
        raise UnavailableContent("Global unit release catalogue has not been approved.")
    for unit_id, spec in document["units"].items():
        if not isinstance(unit_id, str) or not unit_id.isascii() or not unit_id.isdecimal():
            raise UnavailableContent("Verified unit IDs must be numeric Global master IDs.")
        if not isinstance(spec, dict) or not isinstance(spec.get("rarities"), dict):
            raise UnavailableContent("Missing exact-rarity historical release data.")
        channels = spec.get("channels")
        if (not isinstance(channels, list) or not channels or
                not all(isinstance(item, str) and item in ("rare", "friend") for item in channels) or
                len(channels) != len(set(channels))):
            raise UnavailableContent("Verified units require explicit Rare/Friend channels.")
        base, rarities = str(spec.get("base_rarity", "")), spec["rarities"]
        if base not in rarities:
            raise UnavailableContent("Unit's original rarity is not dated.")
        for rarity, released in rarities.items():
            if (not isinstance(rarity, str) or len(rarity) != 1 or rarity not in "1234567" or
                    not isinstance(released, str) or
                    not is_released(released, "9999-12") or released < "2016-06"):
                raise UnavailableContent("Release catalogue contains an unverified rarity or date.")
    return document["units"]


def summon_channel(banner: dict, cost: dict) -> str:
    """Resolve the existing offer's summon channel before charging anything."""
    kind = str((cost or {}).get("kind") or "")
    friend_type = str(banner.get("type") or "").lower() == "friend" or \
        str(banner.get("exe_type") or "").lower() == "friend"
    if kind == "friend_point" and not banner.get("ticket_group_id"):
        return "friend"
    if friend_type:
        raise UnavailableContent("Friend summon with an unverified purchase method.")
    if kind in ("lapis", "ticket") or (not kind and banner.get("ticket_group_id")):
        return "rare"
    raise UnavailableContent("Summon purchase method is not historically classified.")


def banner_allowed(banner: dict, month: str) -> bool:
    """Only the 2016 permanent Rare/Friend entries or explicitly dated banners."""
    if str(banner.get("id")) in ("1", "9"):
        return True
    release = (banner.get("community") or {}).get("release") or banner.get("release")
    # Offline archive rule: once introduced in Global, a banner remains
    # accessible through the preserved Summons dropdown in all later months.
    # Its original live-service expiry is intentionally not simulated.
    return is_released(release, month)


def visible_banners(banners: list[dict], player) -> list[dict]:
    """Hide undated/future banners when a save explicitly opts into history."""
    meta = (player.data.get("meta") or {}) if player else {}
    if not meta.get("historical_preview"):
        return banners
    from historical_progression import current_month
    month = current_month(player.data)
    # Catalogue rows represent the shipped banner IDs. Community aliases
    # point to the SAME campaign; showing both created double banners.
    represented_aliases = {str(alias) for banner in banners
                           if banner_allowed(banner, month)
                           for alias in (banner.get("alias_ids") or [])}
    return [banner for banner in banners if
            banner_allowed(banner, month) and str(banner.get("id")) not in represented_aliases]


def _unit_allowed(unit_id, releases: dict, month: str, rarity=None) -> bool:
    spec = releases.get(str(unit_id))
    if not isinstance(spec, dict):
        return False
    granted_rarity = str(rarity if rarity is not None else spec.get("base_rarity"))
    return is_released((spec.get("rarities") or {}).get(granted_rarity), month)


def _check_rewards(rewards, releases: dict[str, dict], month: str) -> None:
    """Conservative until non-unit bonus rewards get their own date sources."""
    for row in rewards:
        if not isinstance(row, dict) or int(row.get("kind", -1)) != 10:
            raise UnavailableContent("Unverified non-unit summon reward or bonus.")
        if not _unit_allowed(row.get("id"), releases, month):
            raise UnavailableContent("A summon reward is not available in this period.")


def prepare_historical_summon(
    month: str,
    releases: dict[str, dict],
    pool: list[dict],
    guaranteed_pool: list[dict],
    extra_slots: list[tuple[int, list[dict]]],
    guarantee: dict,
    bonus_rewards: list[dict],
    bonus_choices: list[dict],
    channel: str,
    banner: dict | None = None,
) -> tuple[list[dict], list[dict], list[tuple[int, list[dict]]], dict]:
    """Restrict *every possible* unit grant before Lapis or tickets are spent.

    Reweights retained rows with historical_progression.eligible_pool.
    Guaranteed replacements and special slots are restricted separately; fixed
    future guarantees and unverified bonus paths fail before the purchase.
    """
    month_cutoff(month)
    if banner is not None and not banner_allowed(banner, month):
        raise UnavailableContent("The banner is from a later or undated period.")
    if channel not in ("rare", "friend"):
        raise UnavailableContent("Unknown historical summon channel.")
    releases = {unit_id: spec for unit_id, spec in releases.items()
                if isinstance(spec, dict) and channel in spec.get("channels", ())}
    if not releases:
        raise UnavailableContent("There are no verified Global summon units for this channel.")
    _check_rewards(bonus_rewards, releases, month)
    for choice in bonus_choices:
        _check_rewards(choice.get("rewards") or [], releases, month)

    # Other reward kinds may grant gear or resources from future seasons.
    for entry in pool:
        if int(entry.get("kind", 10)) != 10:
            raise UnavailableContent("Unverified mixed summon reward pool.")
    filtered_pool = eligible_pool(pool, releases, month)

    if guarantee.get("unit_id") is not None and not _unit_allowed(
            guarantee["unit_id"], releases, month):
        raise UnavailableContent("A fixed guaranteed unit has not been released.")
    normalized_guarantee = dict(guarantee)
    if guarantee.get("any_of"):
        allowed_choices = [u for u in guarantee["any_of"] if _unit_allowed(u, releases, month)]
        if not allowed_choices:
            raise UnavailableContent("Guaranteed unit choices are not available.")
        normalized_guarantee["any_of"] = allowed_choices

    # Both separate guaranteed pools and guarantee_slots can contain future
    # units that would bypass filtering only the regular draw pool.
    if guarantee:
        filtered_guaranteed = eligible_pool(guaranteed_pool, releases, month)
        if guarantee.get("rarity") is not None:
            threshold = int(guarantee["rarity"])
            if not any(int(e.get("rarity") or 0) >= threshold for e in filtered_guaranteed):
                raise UnavailableContent("Historical guaranteed rarity cannot be fulfilled.")
    else:
        filtered_guaranteed = filtered_pool

    filtered_slots = []
    for count, candidates in extra_slots:
        if count < 1:
            raise UnavailableContent("Invalid guaranteed slot count.")
        filtered_slots.append((count, eligible_pool(candidates, releases, month)))
    return filtered_pool, filtered_guaranteed, filtered_slots, normalized_guarantee
