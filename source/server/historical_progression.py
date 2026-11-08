"""Historical Global availability policy.

Pure selection helpers; no gameplay hooks are enabled until the unit release
index is audited. Unknown release dates fail closed rather than leaking future
content. The existing PlayerState owns save persistence.
"""
from __future__ import annotations

import calendar
from datetime import date
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


def advance_month(player, latest_month: str) -> str:
    """Advance exactly one month. The caller persists PlayerState atomically."""
    current = current_month(player.data)
    _month_parts(latest_month)
    target = next_month(current)
    if target > latest_month:
        raise ValueError("No further audited historical month is available.")
    player.data.setdefault("meta", {})["historical_month"] = target
    player.dirty = True
    return target


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


def available_banners(banners: list[dict], month: str) -> list[dict]:
    """Exclude undated and future campaigns; permanent banners need a separately audited allowlist."""
    month_cutoff(month)
    return [banner for banner in banners if is_released(
        (banner.get("community") or {}).get("release") or banner.get("release"), month)]


def eligible_pool(rows: list[dict], global_unit_release: dict[str, str], month: str) -> list[dict]:
    """Filter explicit, expanded summon rows; preserve their relative rates.

    The pool must already be expanded with player_state.expand_pool. No unknown
    unit or zero-weight pool may produce a reward. This does not yet cover
    authored bonus awards or non-summon rewards.
    """
    month_cutoff(month)
    eligible = [dict(row) for row in rows if
                is_released(global_unit_release.get(str(row.get("unit_id"))), month)]
    original_weight = sum(max(0.0, float(row.get("rate", 0))) for row in rows)
    kept_weight = sum(max(0.0, float(row.get("rate", 0))) for row in eligible)
    if not eligible or kept_weight <= 0:
        raise UnavailableContent("No historically eligible summon rewards.")
    factor = original_weight / kept_weight
    for row in eligible:
        row["rate"] = max(0.0, float(row.get("rate", 0))) * factor
    return eligible
