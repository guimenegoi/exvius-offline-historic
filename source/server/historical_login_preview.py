"""2016 Global monthly login proof-of-concept from contemporary screenshots.

Source:
 https://finalfantasy.fandom.com/wiki/File:FFBE_June_2016_Daily_Rewards_(Global).png
 https://finalfantasy.fandom.com/wiki/File:FFBE_July_2016_Daily_Rewards_(Global).png

Gil, Lapis, Friend Points, Star Quartz and Rare Ticket amounts are transcribed
from the pictures. NRG points cannot be represented by the original mailbox
reward enum, so this preview grants equivalent NRG Restore 10 consumables.
June day 25 has an unidentified red icon: the safe temporary fallback is one
NRG Restore 10 rather than inventing a unit or premium ticket.
Those substitutions are explicitly NOT verified historical exact grants.
"""
from __future__ import annotations

_JUNE = [
    ("gil", 500), ("quartz", 1), ("fp", 200), ("ticket", 1),
    ("nrg", 20), ("gil", 1000), ("lapis", 100),
    ("gil", 1500), ("ticket", 1), ("fp", 400), ("lapis", 50),
    ("fp", 800), ("quartz", 3), ("lapis", 100),
    ("gil", 2000), ("quartz", 1), ("fp", 600), ("lapis", 50),
    ("ticket", 1), ("lapis", 25), ("lapis", 100),
    ("gil", 3000), ("nrg", 30), ("ticket", 1), ("unknown", 1),
    ("nrg", 35), ("lapis", 100), ("ticket", 1),
]
_JULY = [
    ("lapis", 125), ("ticket", 1), ("gil", 3000), ("nrg", 30),
    ("nrg", 5), ("gil", 3000), ("ticket", 1),
    ("nrg", 5), ("gil", 3000), ("lapis", 125), ("nrg", 30),
    ("gil", 3000), ("ticket", 1), ("ticket", 1),
    ("gil", 3000), ("ticket", 1), ("nrg", 30), ("lapis", 125),
    ("gil", 3000), ("nrg", 30), ("ticket", 1),
    ("ticket", 1), ("gil", 3000), ("lapis", 125), ("nrg", 5),
    ("nrg", 30), ("ticket", 1), ("ticket", 1),
]
_ITEMS = {
    "gil": (30, 1, "Gil"),
    "lapis": (50, 1, "Lapis"),
    "fp": (51, 1, "Friend Points"),
    "ticket": (23, 50, "Rare Summon Ticket"),
    "quartz": (20, 106200100, "Star Quartz"),
    "nrg": (23, 100, "NRG Restore 10"),
    "unknown": (23, 100, "NRG Restore 10 — tentative substitute"),
}


def build_calendar(rows: list[tuple[str, int]]) -> dict:
    if len(rows) != 28:
        raise ValueError("The June/July original login panels have 28 day cells")
    days = {}
    for day, (kind, raw_amount) in enumerate(rows, 1):
        item_type, item_id, name = _ITEMS[kind]
        amount = max(1, (raw_amount + 9) // 10) if kind == "nrg" else raw_amount
        days[str(day)] = {"type": item_type, "id": item_id, "count": amount,
                          "name": name, "how": "approximate-NRG" if kind in
                          ("nrg", "unknown") else "2016-Global-screenshot",
                          "screenshot_count": raw_amount}
    return {"days": days, "banner": ""}


MONTHS = {"2016-Jun": build_calendar(_JUNE), "2016-Jul": build_calendar(_JULY)}
