"""Historical Global availability policy.

Pure selection helpers; no gameplay hooks are enabled until the unit release
index is audited. Unknown release dates fail closed rather than leaking future
content. The existing PlayerState owns save persistence.
"""
from __future__ import annotations

import calendar
from datetime import date
from functools import lru_cache
import json
import pkgutil
import re

LAUNCH_MONTH = "2016-06"
_MONTH = re.compile(r"\d{4}-\d{2}\Z")
_DAY = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


class UnavailableContent(ValueError):
    """A catalogue entry has no eligible historical result."""


def _month_parts(month: str) -> tuple[int, int]:
    if not isinstance(month, str) or not _MONTH.fullmatch(month):
        raise ValueError("Historical month must be YYYY-MM.")
    year, number = map(int, month.split("-"))
    if not 1 <= number <= 12 or month < LAUNCH_MONTH:
        raise ValueError("Historical month precedes Global launch or is invalid.")
    return year, number


def month_cutoff(month: str) -> date:
    year, number = _month_parts(month)
    return date(year, number, calendar.monthrange(year, number)[1])


def next_month(month: str) -> str:
    year, number = _month_parts(month)
    return f"{year + (number == 12):04d}-{number % 12 + 1:02d}"


def current_month(player_data: dict) -> str:
    # Older saves have no historical marker and begin at Global launch.
    month = (player_data.get("meta") or {}).get("historical_month", LAUNCH_MONTH)
    _month_parts(month)  # Corrupt data must never unlock the whole catalogue.
    return month


def advance_to_month(player, target: str, latest_month: str) -> str:
    """Select a later available month, never reversing historical progression.

    Supports a quick next-update button or a jump-forward month selector. The
    caller confirms the choice in the UI and persists PlayerState atomically.
    """
    current = current_month(player.data)
    _month_parts(target)
    _month_parts(latest_month)
    if target <= current or target > latest_month:
        raise ValueError("Choose a future month within the audited historical timeline.")
    player.data.setdefault("meta", {})["historical_month"] = target
    player.dirty = True
    return target


def advance_month(player, latest_month: str) -> str:
    """Advance exactly one month using the same validated progression policy."""
    return advance_to_month(player, next_month(current_month(player.data)), latest_month)


def is_released(release: str | None, month: str) -> bool:
    """Accept only explicit Global YYYY-MM or YYYY-MM-DD release metadata."""
    cutoff = month_cutoff(month)
    if not isinstance(release, str):
        return False
    try:
        if _MONTH.fullmatch(release):
            year, number = map(int, release.split("-"))
            released = date(year, number, 1)
        elif _DAY.fullmatch(release):
            released = date.fromisoformat(release)
        else:
            return False
    except ValueError:
        return False
    return released <= cutoff


# First Global availability for systems, not the final client's F_FUNCTION_MST flags.
# Sources refer to the Global release (not Japanese version) and are retained
# here for every introduced date. None = no audited launch date; fail closed.
FEATURE_INTRODUCED = {
    "world": ("2016-06", "https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/"),
    "vortex": ("2016-06", "https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/"),
    "craft": ("2016-06", "https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/"),
    "espers": ("2016-06", "https://www.mobygames.com/game/79645/final-fantasy-brave-exvius/screenshots/"),
    "colosseum": ("2016-06", "https://finalfantasy.fandom.com/wiki/Colosseum_(Brave_Exvius)"),
    "colosseum_beginner": ("2016-06", "https://exvius.fandom.com/wiki/Colosseum"),
    # Earliest directly attested Global completion (July 9), not a proved
    # launch date. Fail closed in June pending contemporary launch evidence.
    "colosseum_intermediate": ("2016-07", "https://www.neogaf.com/threads/final-fantasy-brave-exvius-ot-classic-sprite-based-jrpg-goodness-up-global-launch.1219944/page-89"),
    "colosseum_advanced": ("2016-09", "https://exvius.fandom.com/wiki/News/Archives/2016_-_2021"),
    "arena": ("2016-11", "https://exvius.fandom.com/wiki/News/Archives/2016_-_2021"),
    "ability_awakening": ("2016-09", "https://exvius.fandom.com/wiki/Update_Schedule"),
    "expedition": ("2017-06", "https://exvius.fandom.com/wiki/News/Archives/2016_-_2021"),
    # Unlike unit awakening (launch-era), these systems have no approved
    # Global intro date in this audit. Do not infer dates from the 2024 MST.
    "equipment_enhancement": (None, None),
    "panel_quest": (None, None),
    "sp_challenge": (None, None),
    "modern_login_calendar": (None, None),
    "anniversary_ticket": (None, None),
    "catchup_rewards": (None, None),
    # Square Enix's Global debut notice, 20 August 2020:
    # https://na.finalfantasy.com/news/1462
    "neo_vision": ("2020-08", "https://na.finalfantasy.com/news/1462"),
    "vision_cards": ("2020-08", "https://na.finalfantasy.com/news/1462"),
    # Global v7.5.0 home redesign (not the 2020 inventory VC release).
    # https://exvius.fandom.com/wiki/Update_Schedule (22-Sept-2022 feature)
    "home_vision_card_ornament": ("2022-09", "https://exvius.fandom.com/wiki/Update_Schedule"),
    # Steel Castle Melfikya was introduced after 2016; exact first Global
    # date remains to be verified before its UI is enabled.
    "item_world": (None, None),
    "modern_event_modes": (None, None),
    "modern_gacha_selection": (None, None),
    "modern_exchange": (None, None),
    "modern_unit_growth": (None, None),
    "modern_quest_rewards": (None, None),
    "world_season_selector": (None, None),
    "historic_awakening_index": (None, None),
    "emblem_event": (None, None),
    "comeback_quest": (None, None),
    "modern_lapis_bundles": (None, None),
    "late_shop_magic_key": (None, None),
    "unverified_exchange_catalogue": (None, None),
    "unverified_party_presets": (None, None),
}


def historical_features(player_data: dict) -> dict[str, bool] | None:
    """One server-authoritative feature projection for a historical save.

    Unmarked legacy saves return None and retain upstream behavior.
    Historical saves validate the marker before deriving any permissions.
    A missing/uncorroborated Global release is never enabled implicitly.
    """
    if not (player_data.get("meta") or {}).get("historical_preview"):
        return None
    month = current_month(player_data)
    return {key: is_released(introduced, month) for key, (introduced, _source) in
            FEATURE_INTRODUCED.items()}


def feature_available(feature: str, player_data: dict) -> bool:
    """Use the same period policy in server routes and native UI status."""
    features = historical_features(player_data)
    return features is None or features.get(feature, False)


# These three native Global roots appear in the early roster as *story*
# acquisition, not as Rare or Friend Point summons. Preserve the original
# campaign grants. Nothing else is admitted without a dated preview entry.
STORY_ROOTS = frozenset({"100000102", "100000202", "100000302"})


def historical_unit_reward_allowed(master_id, player_data: dict) -> bool:
    """Fail closed for undated grants outside the preview summon catalogue."""
    if not (player_data.get("meta") or {}).get("historical_preview"):
        return True
    from historical_preview_data import DOCUMENT
    unit_id = str(master_id)
    if unit_id in STORY_ROOTS:
        return True
    record = DOCUMENT["units"].get(unit_id)
    if not record:
        return False
    return any(is_released(release, current_month(player_data))
               for release in (record.get("rarities") or {}).values())


def historical_reward_allowed(row: dict, player_data: dict) -> bool:
    """Common grant gate for mail, quest, boss, shop and direct reward paths."""
    if not (player_data.get("meta") or {}).get("historical_preview"):
        return True
    kind = int(row.get("kind", 0) or 0)
    if kind == 10:
        return historical_unit_reward_allowed(row.get("id"), player_data)
    if kind == 26:  # late player emblems
        return False
    if kind == 27:  # Vision Cards only from Global 2020-08
        return feature_available("vision_cards", player_data)
    if kind == 28:  # later unit series points
        return feature_available("modern_unit_growth", player_data)
    return True



@lru_cache(maxsize=1)
def historical_commerce_catalogue() -> dict:
    """One evidence-backed Global economic index, both on disk and in app.imy.

    The APK builder embeds this JSON in the Chaquopy archive. A missing
    resource must fail closed, never fall through to the final-client shop.
    """
    raw = pkgutil.get_data(__name__, "content/historical_commerce.json")
    if not raw:
        raise UnavailableContent("The historical Global commerce index is missing.")
    catalogue = json.loads(raw.decode("utf-8"))
    if catalogue.get("schema") != 1 or catalogue.get("region") != "GL":
        raise UnavailableContent("Wrong historical commerce catalogue.")
    return catalogue



def historical_premium_bundle_ids(player_data: dict) -> set[str] | None:
    """Paid Shop offers unlock permanently at their first evidenced Global release.

    None retains the ordinary nonhistorical offline catalogue. Historical
    offers require explicit approval; a later month never removes a bundle.
    Frequency and purchase limits are still handled by the original Shop.
    """
    if not (player_data.get("meta") or {}).get("historical_preview"):
        return None
    month = current_month(player_data)
    catalogue = historical_commerce_catalogue()
    return {str(row["id"]) for row in catalogue["premium_bundles"]
            if row.get("status") == "approved" and row.get("source")
            and row.get("currency") and row.get("original_price") is not None
            and isinstance(row.get("contents"), list) and row["contents"]
            and is_released(row.get("available_from"), month)}


def historical_colosseum_orb_cap(player_data: dict) -> int | None:
    """Global launch cap 3; Arena debut in November 2016 raised it to 5.

    Returns None for unmarked saves, retaining upstream's runtime cap.
    This is the last sourced historical cap; a later rise to ten is not
    presumed without a separate dated Global announcement.
    """
    if not (player_data.get("meta") or {}).get("historical_preview"):
        return None
    month = current_month(player_data)
    return 5 if is_released("2016-11-10", month) else 3


def eligible_pool(rows: list[dict], global_unit_release: dict[str, str], month: str) -> list[dict]:
    """Filter explicit, expanded summon rows; preserve their relative rates.

    The pool must already be expanded with player_state.expand_pool. No unknown
    unit or zero-weight pool may produce a reward. This does not yet cover
    authored bonus awards or non-summon rewards.
    """
    month_cutoff(month)

    def release_of(row: dict):
        entry = global_unit_release.get(str(row.get("unit_id")))
        if isinstance(entry, dict):
            # Verified catalogues gate the exact grant rarity, not just the
            # character's initial release. An awakening cannot arrive early.
            return (entry.get("rarities") or {}).get(str(row.get("rarity")))
        return entry  # Kept for the earlier audit-only, ID/date tests.

    eligible = [dict(row) for row in rows if is_released(release_of(row), month)]
    original_weight = sum(max(0.0, float(row.get("rate", 0))) for row in rows)
    kept_weight = sum(max(0.0, float(row.get("rate", 0))) for row in eligible)
    if not eligible or kept_weight <= 0:
        raise UnavailableContent("No historically eligible summon rewards.")
    factor = original_weight / kept_weight
    for row in eligible:
        row["rate"] = max(0.0, float(row.get("rate", 0))) * factor
    return eligible
