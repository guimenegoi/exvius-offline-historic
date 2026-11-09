"""Audit-only tests for original Global Colosseum capacity, dates and grants."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "source/server"))

import ffbe_state
import exvius_colosseum as colosseum
import player_state
from historical_progression import feature_available, historical_colosseum_orb_cap


def historical(month="2016-06"):
    return {"meta": {"historical_preview": True, "historical_month": month}}


def player_at(month="2016-06"):
    return player_state.PlayerState({
        **historical(month),
        "rank": {"level": 1, "exp": 0, "nrg": 10},
        "orbs": {"clsm": {"point": 10, "anchor_utc": None}},
        "currencies": {"lapis_free": 1000, "lapis_paid": 0},
    })


class HistoricalOrbTests(TestCase):
    def test_capacity_changes_only_in_historic_saves(self):
        self.assertEqual(historical_colosseum_orb_cap(historical("2016-06")), 3)
        self.assertEqual(historical_colosseum_orb_cap(historical("2016-07")), 3)
        self.assertEqual(historical_colosseum_orb_cap(historical("2016-10")), 3)
        self.assertEqual(historical_colosseum_orb_cap(historical("2016-11")), 5)
        self.assertIsNone(historical_colosseum_orb_cap({"meta": {}}))
        for month, cap in (("2016-06", 3), ("2016-07", 3), ("2016-11", 5)):
            player = player_at(month)
            self.assertEqual(player.orb_view("clsm"), (cap, cap, 0))
            self.assertEqual(player.orb_capacity("clsm"), cap)
        legacy = player_state.PlayerState({"meta": {}, "orbs": {}})
        self.assertEqual(legacy.orb_capacity("clsm"),
                         player_state.ORB_FAMILIES["clsm"]["cap"])
        self.assertEqual(legacy.orb_view("clsm")[0], legacy.orb_capacity("clsm"))

    def test_consumption_and_hourly_recovery_never_exceed_historical_cap(self):
        p = player_at()
        start = 1731000000
        self.assertTrue(p.spend_orbs("clsm", 1, now=start))
        self.assertEqual(p.orb_view("clsm", now=start), (2, 3, 3600))
        self.assertEqual(p.orb_view("clsm", now=start + 1800), (2, 3, 1800))
        self.assertEqual(p.orb_view("clsm", now=start + 3600), (3, 3, 0))
        self.assertFalse(p.spend_orbs("clsm", 4, now=start + 1800))
        self.assertEqual(p.orb_view("clsm", now=start + 1800), (2, 3, 1800))
        self.assertEqual(p.orb_view("clsm", now=start + 86400), (3, 3, 0))
        p.data["meta"]["historical_month"] = "2016-11"
        self.assertEqual(p.orb_view("clsm", now=start + 86400), (5, 5, 0))
        self.assertEqual(p.orb_capacity("event"), player_state.ORB_FAMILIES["event"]["cap"])

    def test_refill_shop_uses_derived_cap_not_final_2024_cap(self):
        p = player_at("2016-06")
        with patch.object(player_state, "shop_mst", return_value={
                player_state.SHOP_USE_DIA_TOKEN: "100",
                player_state.SHOP_NAME_TOKEN: "Colosseum Orb Recovery"}):
            result = p.recharge_orb_with_shop("21")
            self.assertEqual(result["point"], 3)
            self.assertEqual(p.data["orbs"]["clsm"]["point"], 3)
            self.assertEqual(p.orb_view("clsm")[1], 3)
            p.data["meta"]["historical_month"] = "2016-11"
            result = p.recharge_orb_with_shop("21")
            self.assertEqual(result["point"], 5)
            self.assertEqual(p.orb_view("clsm")[1], 5)

    def test_rank_up_refills_only_historical_colosseum_orbs(self):
        p = player_at()
        p.data["orbs"]["clsm"] = {"point": 0, "anchor_utc": "2025-01-01T00:00:00Z"}
        with patch.object(player_state, "need_exp", side_effect=lambda lv: 20 if lv == 2 else 0), patch.object(
                player_state, "nrg_cap", return_value=30):
            p.add_rank_exp(20)
        self.assertEqual(p.data["rank"]["level"], 2)
        self.assertEqual(p.data["orbs"]["clsm"]["point"], 3)
        self.assertEqual(p.orb_view("clsm")[0], 3)
        legacy = player_at()
        legacy.data["meta"].clear()
        legacy.data["orbs"]["clsm"] = {"point": 0, "anchor_utc": "2025-01-01T00:00:00Z"}
        with patch.object(player_state, "need_exp", side_effect=lambda lv: 20 if lv == 2 else 0), patch.object(
                player_state, "nrg_cap", return_value=30):
            legacy.add_rank_exp(20)
        self.assertEqual(legacy.data["orbs"]["clsm"]["point"], 0)


class HistoricalGradeTests(TestCase):
    def test_beginner_intermediate_advanced_by_month(self):
        self.assertTrue(feature_available("colosseum_beginner", historical("2016-06")))
        self.assertFalse(feature_available("colosseum_intermediate", historical("2016-06")))
        self.assertTrue(feature_available("colosseum_intermediate", historical("2016-07")))
        self.assertFalse(feature_available("colosseum_advanced", historical("2016-07")))
        self.assertTrue(feature_available("colosseum_advanced", historical("2016-09")))
        self.assertTrue(feature_available("colosseum_advanced", {"meta": {}}))

    def test_future_grade_direct_request_refused_without_spending(self):
        p = player_at("2016-07")
        p.data["exvius_colosseum"] = {
            "highest": "30101", "unlocked": ["30101"], "rounds": {},
            "sequence": 0, "active": None}
        before = deepcopy(p.data)
        with patch.object(ffbe_state.State, "player", p), patch.object(
                colosseum, "_masters", return_value=(
                    {"3JuUWi4x": "3"}, {"sCd0L6Ka": "1000"})):
            result = colosseum.lottery({"unchanged": True}, {
                "wPBq3it9": [{"i5pd8xr3": "30101"}]})
        self.assertEqual(result, {"unchanged": True})
        self.assertEqual(p.data, before)
        self.assertFalse(p.dirty)

    def test_original_beginner_d1_reward_100_lapis_once(self):
        # Official Global F_CLSM_ROUND_MST row 10101:
        # first boss reward "50:1:100", repeat "20:101000100:1:100".
        p = player_at("2016-06")
        p.data["exvius_colosseum"] = {
            "highest": "10101", "unlocked": ["10101"],
            "sequence": 1, "active": {
                "id": 1, "progress": "10101", "boss": True,
                "group_id": "recovered", "before": 1000,
                "win_points": 1000, "lose_points": 1000},
            "rounds": {"10101": {
                "points": 1000, "battles": 10, "wins": 10,
                "boss_wins": 0,
                "selection": {"boss": True, "group_id": "recovered"}}}}
        row = {"3JuUWi4x": "1", "ewPqs8h6": "10102"}
        reward = {"1x4bG2J8": "50:1:100",
                  "dX6cor8j": "20:101000100:1:100"}
        p.record_archive = lambda *_args: None
        request = {"wPBq3it9": [{"i5pd8xr3": "10101", "VR3DuS2M": "2"}]}
        with patch.object(ffbe_state.State, "player", p), patch.object(
                colosseum, "_masters", return_value=(row, reward)), patch.object(
                colosseum, "_mst", return_value={"10101": row, "10102": {
                    "3JuUWi4x": "1"}}), patch.object(
                colosseum, "_available", return_value=True), patch.object(
                colosseum, "_reply", side_effect=lambda spec, model, **kw: {
                    "highest": model["highest"]}):
            first = colosseum.end({}, request)
            self.assertEqual(first["highest"], "10102")
            self.assertEqual(p.data["currencies"]["lapis_free"], 1100)
            self.assertEqual(p.data["exvius_colosseum"]["rounds"]["10101"]["boss_wins"], 1)
            repeat = colosseum.end({}, request)
            self.assertEqual(repeat["highest"], "10102")
            self.assertEqual(p.data["currencies"]["lapis_free"], 1100)

    def test_boss_grant_kept_but_next_unreleased_grade_not_unlocked(self):
        # First Intermediate rank promotion remains blocked in June.
        for month, unlocked in (("2016-06", False), ("2016-07", True)):
            with self.subTest(month=month):
                p = player_at(month)
                p.data["exvius_colosseum"] = {
                    "highest": "10505", "unlocked": ["10505"],
                    "sequence": 1, "active": {
                        "id": 1, "progress": "10505", "boss": True,
                        "group_id": "recovered", "before": 1000,
                        "win_points": 1000, "lose_points": 1000},
                    "rounds": {"10505": {
                        "points": 1000, "battles": 10, "wins": 10,
                        "boss_wins": 0, "selection": {"boss": True, "group_id": "recovered"}}}}
                row = {"3JuUWi4x": "1", "ewPqs8h6": "20101"}
                roundrow = {"1x4bG2J8": "20:1:1:100", "dX6cor8j": "20:1:1:100"}
                p.record_archive = lambda *_a: None
                p._can_credit = lambda *_a: True
                p._grant_items = lambda items: items
                def lookup(table, key):
                    if table == "F_CLSM_PROGRESS_MST.ndjson":
                        return {"10505": row, "20101": {"3JuUWi4x": "2"}}
                    return {}
                with patch.object(ffbe_state.State, "player", p), patch.object(
                        colosseum, "_masters", return_value=(row, roundrow)), patch.object(
                        colosseum, "_mst", side_effect=lookup), patch.object(
                        colosseum, "_available", return_value=True), patch.object(
                        colosseum, "_reply", side_effect=lambda spec, model, **kw: {
                            "unlocked": model["unlocked"]}):
                    answer = colosseum.end({}, {"wPBq3it9": [
                        {"i5pd8xr3": "10505", "VR3DuS2M": "2"}]})
                self.assertEqual("20101" in answer["unlocked"], unlocked)
                self.assertEqual(p.data["exvius_colosseum"]["rounds"]["10505"]["boss_wins"], 1)
                self.assertIsNone(p.data["exvius_colosseum"]["active"])
                if month == "2016-06":
                    # Unlock at the next authorised calendar month; never
                    # demand another boss defeat or pay a second prize.
                    p.data["meta"]["historical_month"] = "2016-07"
                    p.dirty = False
                    with patch.object(ffbe_state.State, "player", p), patch.object(
                            colosseum, "_mst", side_effect=lookup), patch.object(
                            colosseum, "_available", return_value=True), patch.object(
                            colosseum, "_reply", side_effect=lambda spec, model, **kw: {
                                "unlocked": model["unlocked"]}):
                        resumed = colosseum.entry({}, {})
                    self.assertIn("20101", resumed["unlocked"])
                    self.assertEqual(p.data["exvius_colosseum"]["highest"], "20101")
                    self.assertEqual(p.data["exvius_colosseum"]["rounds"]["10505"]["boss_wins"], 1)
                    self.assertTrue(p.dirty)
                    p.dirty = False
                    with patch.object(ffbe_state.State, "player", p), patch.object(
                            colosseum, "_mst", side_effect=lookup), patch.object(
                            colosseum, "_reply", side_effect=lambda spec, model, **kw: {
                                "unlocked": model["unlocked"]}):
                        colosseum.entry({}, {})
                    self.assertFalse(p.dirty, 'Second entry must not mutate the save')
