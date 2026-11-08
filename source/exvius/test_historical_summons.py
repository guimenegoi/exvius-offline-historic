"""Fail-closed historical summon tests without extracted Android assets."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "source/server"))

from historical_progression import UnavailableContent
from historical_summons import load_verified_unit_releases, prepare_historical_summon


class HistoricalSummonTests(unittest.TestCase):
    RELEASES = {
        "101": {"base_rarity": "3", "rarities": {
            "3": "2016-07-08", "6": "2016-09-01"}},
        "102": {"base_rarity": "3", "rarities": {"3": "2016-08-05"}},
    }

    def prepare(self, **kw):
        defaults = {
            "month": "2016-07", "releases": self.RELEASES,
            "pool": [{"unit_id": "101", "rarity": 3, "rate": 0.4},
                     {"unit_id": "102", "rarity": 3, "rate": 0.4},
                     {"unit_id": "999", "rarity": 3, "rate": 0.2}],
            "guaranteed_pool": [], "extra_slots": [], "guarantee": {},
            "bonus_rewards": [], "bonus_choices": [],
        }
        defaults.update(kw)
        return prepare_historical_summon(**defaults)

    def test_all_draws_exclude_future_and_unknown_ids(self):
        pool, _, _, _ = self.prepare()
        self.assertEqual([r["unit_id"] for r in pool], ["101"])
        self.assertAlmostEqual(pool[0]["rate"], 1.0)
        self.assertEqual(self.RELEASES["102"]["rarities"]["3"], "2016-08-05")

    def test_future_awakening_rarity_does_not_unlock_with_unit(self):
        pool, _, _, _ = self.prepare(pool=[
            {"unit_id": "101", "rarity": 6, "rate": 0.8},
            {"unit_id": "101", "rarity": 3, "rate": 0.2}])
        self.assertEqual([(r["unit_id"], r["rarity"]) for r in pool], [("101", 3)])
        self.assertAlmostEqual(pool[0]["rate"], 1.0)

    def test_future_fixed_guarantee_refuses_before_purchase(self):
        with self.assertRaises(UnavailableContent):
            self.prepare(guarantee={"unit_id": "102"},
                         guaranteed_pool=[{"unit_id": "101", "rarity": 3, "rate": 1}])

    def test_guarantee_choices_and_separate_pool_are_filtered(self):
        pool, special, _, guarantee = self.prepare(
            guarantee={"any_of": ["101", "102"], "rarity": 3},
            guaranteed_pool=[{"unit_id": "101", "rarity": 3, "rate": 0.3},
                             {"unit_id": "102", "rarity": 3, "rate": 0.7}])
        self.assertEqual(guarantee["any_of"], ["101"])
        self.assertEqual([r["unit_id"] for r in special], ["101"])
        self.assertAlmostEqual(sum(r["rate"] for r in special), 1.0)

    def test_future_extra_guarantee_slots_cannot_leak(self):
        _, _, slots, _ = self.prepare(extra_slots=[(1, [
            {"unit_id": "101", "rarity": 3, "rate": 1},
            {"unit_id": "102", "rarity": 3, "rate": 1}])])
        self.assertEqual([r["unit_id"] for r in slots[0][1]], ["101"])
        with self.assertRaises(UnavailableContent):
            self.prepare(extra_slots=[(1, [{"unit_id": "102", "rarity": 3, "rate": 1}])])

    def test_bonus_and_mixed_rewards_are_not_unconditionally_credited(self):
        for extras in (
            {"bonus_rewards": [{"kind": 10, "id": "102", "count": 1}]},
            {"bonus_choices": [{"rate": 0.1, "rewards": [
                {"kind": 10, "id": "102", "count": 1}]}]},
            {"bonus_rewards": [{"kind": 21, "id": 9999, "count": 1}]},
            {"pool": [{"kind": 21, "id": 123, "count": 1, "rate": 1}]},
        ):
            with self.subTest(extras=extras), self.assertRaises(UnavailableContent):
                self.prepare(**extras)

    def test_verified_index_must_be_explicitly_approved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "unit_releases.json"
            with self.assertRaises(UnavailableContent):
                load_verified_unit_releases(path)
            path.write_text("[]")
            with self.assertRaises(UnavailableContent):
                load_verified_unit_releases(path)
            for status, units in (
                ("draft", {"101": self.RELEASES["101"]}),
                ("verified", {}),
                ("verified", {"unknown": self.RELEASES["101"]}),
                ("verified", {"101": {"base_rarity": "3", "rarities": {"3": "unverified"}}}),
                ("verified", {"101": {"base_rarity": "3", "rarities": {"6": "2016-09-01"}}}),
                ("verified", {"101": {"base_rarity": "3", "rarities": {
                    "3": "2016-07-08", "12": "2016-07-08"}}}),
            ):
                path.write_text(json.dumps({"schema": 1, "status": status,
                                            "sources": ["Global chronology"], "units": units}))
                with self.subTest(status=status, units=units), self.assertRaises(UnavailableContent):
                    load_verified_unit_releases(path)
            path.write_text(json.dumps({"schema": 1, "status": "verified",
                                        "sources": ["Global chronology"],
                                        "units": {"101": self.RELEASES["101"]}}))
            self.assertEqual(load_verified_unit_releases(path), {"101": self.RELEASES["101"]})

    def test_unapproved_release_index_rejects_player_summon_before_spending(self):
        from player_state import PlayerState

        class MinimalPlayer:
            mode = "live"
            dirty = False
            data = {"meta": {"historical_month": "2016-07"},
                    "gacha": {"user_banners": {}, "daily": {}}}

            def gacha_step(self, _banner):
                return 0

            def spend_currency(self, *_args):
                raise AssertionError("Historical rejection must occur before charging.")

            roll_gacha = PlayerState.roll_gacha

        player = MinimalPlayer()
        banner = {"id": "9800101", "name": "Historical gate test", "draws": 1,
                  "cost": {"kind": "lapis", "amount": 500},
                  "pool": [{"unit_id": "101", "rarity": 3, "rate": 1}]}
        before = copy.deepcopy(player.data)
        with patch("player_state.expand_pool", return_value=banner["pool"]), patch(
                "historical_summons.load_verified_unit_releases",
                side_effect=UnavailableContent("No approved release data")):
            self.assertIsNone(player.roll_gacha(banner))
        self.assertEqual(player.data, before)
        self.assertFalse(player.dirty)

    def test_approved_pool_charges_only_for_historical_award(self):
        from player_state import PlayerState

        class MinimalPlayer:
            mode = "live"
            dirty = False

            def __init__(self):
                self.data = {
                    "meta": {"historical_month": "2016-07"},
                    "gacha": {"user_banners": {}, "daily": {}, "step": {},
                              "completed_laps": {}},
                    "currencies": {"lapis_free": 2000},
                    "roster": [],
                }
                self.spend_count = 0

            def gacha_step(self, _banner):
                return 0

            def spend_currency(self, kind, amount):
                self.spend_count += 1
                self.data["currencies"]["lapis_free"] -= amount
                return True

            def grant_unit(self, master_id, granted_rarity=None):
                new_unit = {"master_id": str(master_id),
                            "instance_id": str(len(self.data["roster"]) + 1),
                            "level": 1}
                self.data["roster"].append(new_unit)
                return new_unit

            def _apply_unit_reward_metadata(self, _unit, _reward):
                pass

            banner_state = PlayerState.banner_state
            roll_gacha = PlayerState.roll_gacha

        def banner(guarantee=None):
            return {"id": "9800102", "name": "Historical test",
                    "cost": {"kind": "lapis", "amount": 500},
                    "draws": 1, "guarantee": guarantee or {},
                    "pool": [{"unit_id": "101", "rarity": 3, "rate": 0.5},
                             {"unit_id": "102", "rarity": 3, "rate": 0.5}]}

        player = MinimalPlayer()
        original = banner()
        with patch("player_state.expand_pool", return_value=original["pool"]), patch(
                "historical_summons.load_verified_unit_releases",
                return_value=self.RELEASES), patch(
                "player_state.unit_mst", return_value={"9fW0TePj": 3}), patch(
                "player_state.effect_pattern_for", return_value=1):
            outcome = player.roll_gacha(original)
            self.assertEqual([row["unit_id"] for row in outcome["awards"]], ["101"])
            self.assertEqual(player.spend_count, 1)
            self.assertEqual(player.data["currencies"]["lapis_free"], 1500)
            self.assertEqual(len(player.data["roster"]), 1)
            before = copy.deepcopy(player.data)
            denied = player.roll_gacha(banner({"unit_id": "102"}))
            self.assertIsNone(denied)
            self.assertEqual(player.data, before)
            self.assertEqual(player.spend_count, 1)


if __name__ == "__main__":
    unittest.main()
