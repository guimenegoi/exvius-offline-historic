"""Pure, fail-closed historical availability checks; no game state mutation."""
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


class HistoricalPolicy:
    """Availability is a prerequisite, never an authorization to grant rewards.

    Account progression remains the original engine's responsibility. This
    standalone policy can enforce additional known rank/flag prerequisites
    but cannot substitute for native transaction and entitlement checks.
    """

    def __init__(self, entries):
        self._entries = {}
        for entry in entries:
            key = entry["key"]
            if key in self._entries:
                raise ValueError("duplicate historical key: " + key)
            if entry.get("confidence") not in ("A", "B", "C", "D"):
                raise ValueError("invalid confidence for " + key)
            date.fromisoformat(entry["release"])
            self._entries[key] = dict(entry)

    @classmethod
    def from_file(cls, path=None):
        path = Path(path) if path is not None else Path(__file__).with_name("catalogue_2016.json")
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("region") != "GL" or data.get("status") != "research_only":
            raise ValueError("unexpected catalogue region or provenance")
        return cls(data["entries"])

    def check(self, key: str, selected_date: str, account: Mapping | None = None) -> Decision:
        """Check a known content key without mutating the account or catalog.

        Unresolved native identities and inconsistent pools are intentionally
        blocked even after their documented debut dates.
        """
        day = date.fromisoformat(selected_date)
        if day < date(2016, 6, 30) or day > date(2024, 10, 30):
            return Decision(False, "outside_global_period")
        entry = self._entries.get(key)
        if entry is None:
            return Decision(False, "unknown_content")
        if day < date.fromisoformat(entry["release"]):
            return Decision(False, "not_yet_released")
        if entry.get("status") != "catalogue_candidate" or not entry.get("native_id"):
            return Decision(False, "identity_or_pool_unverified")
        if entry["confidence"] not in ("A", "B", "C"):
            return Decision(False, "source_unverified")
        account = account or {}
        if int(account.get("rank", 0)) < int(entry.get("minimum_rank", 0)):
            return Decision(False, "rank_requirement")
        if not set(entry.get("required_flags", ())).issubset(set(account.get("flags", ()))):
            return Decision(False, "story_requirement")
        return Decision(True, "historically_eligible_pending_native_checks")
