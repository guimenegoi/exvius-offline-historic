"""Asset-free tests for the fork's isolated historical policy."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "server"))
import historical_progression as history


class FakePlayer:
    def __init__(self, meta=None):
        self.data = {"meta": meta or {}}
        self.dirty = False


class HistoricalProgressionTests(unittest.TestCase):
    def test_launch_and_month_boundaries(self):
        self.assertEqual(str(history.month_cutoff("2016-06")), "2016-06-30")
        self.assertEqual(history.next_month("2016-12"), "2017-01")
        self.assertEqual(str(history.month_cutoff("2020-02")), "2020-02-29")
        for invalid in ("2016-05", "2016-13", "2016-6", "all", "2016-06-30"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                history.month_cutoff(invalid)

    def test_progression_is_explicit_and_monotonic(self):
        player = FakePlayer()
        self.assertEqual(history.current_month(player.data), "2016-06")
        self.assertEqual(history.advance_month(player, "2016-07"), "2016-07")
        self.assertTrue(player.dirty)
        self.assertEqual(history.current_month(player.data), "2016-07")
        with self.assertRaises(ValueError):
            history.advance_month(player, "2016-07")
        self.assertEqual(player.data["meta"]["historical_month"], "2016-07")

    def test_corrupt_save_never_disables_gate(self):
        with self.assertRaises(ValueError):
            history.current_month({"meta": {"historical_month": "all"}})

    def test_unknown_and_future_dates_are_not_released(self):
        self.assertTrue(history.is_released("2016-06-30", "2016-06"))
        self.assertFalse(history.is_released("2016-07-01", "2016-06"))
        self.assertTrue(history.is_released("2016-07", "2016-07"))
        for value in (None, "", "unknown", "2016-99-01", "2020-01-01"):
            self.assertFalse(history.is_released(value, "2016-06"))

    def test_banner_selection_excludes_undated_and_future(self):
        banners = [
            {"id": "a", "community": {"release": "2016-07-14"}},
            {"id": "b", "release": "2016-08-03"},
            {"id": "c"},
        ]
        self.assertEqual(history.available_banners(banners, "2016-07"), banners[:1])

    def test_pool_filters_all_future_units_including_standard(self):
        rows = [{"unit_id": "old", "rate": 0.2, "rarity": 3},
                {"unit_id": "future", "rate": 0.7, "rarity": 5},
                {"unit_id": "unknown", "rate": 0.1, "rarity": 4}]
        releases = {"old": "2016-06-30", "future": "2019-01-01"}
        selected = history.eligible_pool(rows, releases, "2016-06")
        self.assertEqual([r["unit_id"] for r in selected], ["old"])
        self.assertAlmostEqual(selected[0]["rate"], 1.0)
        self.assertEqual(rows[0]["rate"], 0.2)  # upstream rows untouched
        with self.assertRaises(history.UnavailableContent):
            history.eligible_pool(rows[1:], releases, "2016-06")


if __name__ == "__main__":
    unittest.main()
