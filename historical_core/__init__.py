"""Version-independent research policy for the FFBE Global historical timeline.

Not wired to Android, NativeRules, inventory, rewards, or transactions.
"""
from .policy import HistoricalPolicy, Decision

__all__ = ["HistoricalPolicy", "Decision"]
