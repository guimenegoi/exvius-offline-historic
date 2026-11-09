"""Date/reward/action coverage for the June/July historical test slice.

This file inventories ALL current mutation dispatch endpoints; calendar
gates are opt-in and may not alter classic crafting or friend services.
"""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'source/server'))
from historical_progression import (
    feature_available, historical_unit_reward_allowed, historical_reward_allowed,
)
from historical_preview_data import DOCUMENT
import exvius_actions
import ffbe_player
import ffbe_state
from player_state import PlayerState


def preview(month="2016-06"):
    return {"meta": {"historical_preview": True, "historical_month": month}}


class HistoricDispatcherInventory(TestCase):
    def test_all_2024_endpoints_are_inventory_checked(self):
        handlers = exvius_actions._all_handlers()
        gates = exvius_actions.HISTORICAL_ACTION_FEATURES
        self.assertGreaterEqual(len(handlers), 116)
        self.assertEqual(set(gates) - set(handlers), set(),
                         "A gate references a nonexistent handler: possible typo.")
        self.assertGreaterEqual(len(gates), 81)
        self.assertTrue(all(feature_available(feature, preview()) is False
                            for feature in set(gates.values())))
        # The early release had the core gameplay paths; those must work.
        originals = ("5g0vWZFq", "4uCSA3ko", "3zgbapQ7", "Un16HuNI",
                     "QkN1Sp64", "Gr9zxXk5", "kx13SLUY", "j0A5vQd8",
                     "RQ5BjDE0", "sxK2HG6T")
        self.assertFalse(set(originals).intersection(gates))
        self.assertTrue(all(route in handlers for route in originals))

    def test_missing_handler_still_cannot_bypass_calendar_gate(self):
        player = SimpleNamespace(data=preview(), mode="live", dirty=False)
        with patch.object(ffbe_state.State, "player", player), patch.object(
                exvius_actions, "_all_handlers", return_value={}), patch(
                "exvius_colosseum.project", side_effect=lambda spec: spec):
            self.assertEqual(exvius_actions.serve_actions(
                {"modern": True}, "f8kXGWy0", "{}"), {})
            self.assertFalse(player.dirty)

    def test_blocked_endpoints_are_refused_before_handler_or_save(self):
        for route, feature in exvius_actions.HISTORICAL_ACTION_FEATURES.items():
            with self.subTest(route=route, feature=feature):
                called = Mock(return_value={"charged": 100})
                player = SimpleNamespace(data=preview(), mode="live", dirty=False)
                with patch.object(ffbe_state.State, "player", player), patch.object(
                        exvius_actions, "_all_handlers", return_value={route: called}), patch(
                        "exvius_colosseum.project", side_effect=lambda spec: spec):
                    self.assertEqual(exvius_actions.serve_actions({}, route, "{}"), {})
                    called.assert_not_called()
                    self.assertFalse(player.dirty)
        with patch.object(ffbe_state.State, "player", SimpleNamespace(
                data={"meta": {}}, mode="live")), patch.object(
                exvius_actions, "_all_handlers",
                return_value={"Pf5C8xjJ": lambda *_: {"original": True}}), patch(
                "exvius_colosseum.project", side_effect=lambda spec: spec):
            self.assertEqual(exvius_actions.serve_actions({}, "Pf5C8xjJ", "{}"),
                             {"original": True})


class HistoricBundledFriends(TestCase):
    def test_missing_pyyaml_falls_back_to_no_friends(self):
        import ffbe_friends
        with patch.object(ffbe_friends, "yaml", None):
            self.assertEqual(ffbe_friends.load_friends("friends.yaml"), [])


class HistoricRewardGates(TestCase):
    def test_original_story_units_and_dated_preview_ids_only(self):
        self.assertTrue(historical_unit_reward_allowed("100000102", preview()))
        self.assertTrue(historical_unit_reward_allowed("100000202", preview()))
        self.assertTrue(historical_unit_reward_allowed("100000302", preview()))
        self.assertFalse(historical_unit_reward_allowed("100000999", preview()))
        july = [unit_id for unit_id, spec in DOCUMENT["units"].items()
                if any(r.startswith("2016-07") for r in spec["rarities"].values())]
        self.assertEqual(len(july), 6)
        for unit_id in july:
            self.assertFalse(historical_unit_reward_allowed(unit_id, preview()))
            self.assertTrue(historical_unit_reward_allowed(unit_id, preview("2016-07")))
        self.assertTrue(historical_unit_reward_allowed("100000999", {"meta": {}}))

    def test_direct_reward_paths_cannot_credit_future_unit_card_or_emblem(self):
        state = preview()
        p = PlayerState({**state, "roster": [], "vision_cards": []})
        before = json.dumps(p.data, sort_keys=True)
        for row in ({"kind": 10, "id": 999999999, "count": 1},
                    {"kind": 26, "id": 5, "count": 1},
                    {"kind": 27, "id": 300, "count": 1},
                    {"kind": 28, "id": 9, "count": 1}):
            with self.subTest(row=row):
                self.assertFalse(historical_reward_allowed(row, state))
                self.assertFalse(p._can_credit(row))
                self.assertEqual(p._grant_items([row]), [])
                self.assertEqual(json.dumps(p.data, sort_keys=True), before)
                self.assertFalse(p.dirty)
        self.assertIsNone(p.grant_unit("999999999"))
        self.assertFalse(p.dirty)
        self.assertTrue(historical_reward_allowed(
            {"kind": 50, "id": 1, "count": 100}, state))


class HistoricShopAndEmblem(TestCase):
    def test_uncatalogued_modern_bundle_purchase_never_charges(self):
        for reply in ("uLXAMvCT", "w6Z9a6tD", "X07iYtp5"):
            player = SimpleNamespace(data=preview(), dirty=False)
            with self.subTest(reply=reply), patch.object(ffbe_state.State,
                    "player", player), patch.object(ffbe_player,
                    "_global_bundles", side_effect=AssertionError("must not load final bundles")):
                original = {"fMohhKK8": [{"id": "2024"}],
                            "pcjqhOI8": [{"id": "2024"}],
                            "3VS1Bhmf": [{"id": "2024"}]}
                result = ffbe_player.serve_lapis_shop(original, reply)
                if reply == "w6Z9a6tD":
                    self.assertEqual(result, {})
                else:
                    for key in original:
                        self.assertEqual(result[key], [])
                self.assertFalse(player.dirty)
                self.assertTrue(original["fMohhKK8"])

    def test_emblem_campaign_does_not_send_future_mail_or_credit(self):
        player = SimpleNamespace(data=preview(), dirty=False)
        with patch.object(ffbe_state.State, "player", player):
            self.assertEqual(ffbe_player.deliver_emblem_tier_mail(), [])
            result = ffbe_player.serve_emblem_event(
                {}, ffbe_player.EMBLEM_EVENT_REQUEST)
            for tag in (ffbe_player.EMBLEM_MONTHLY_GROUP,
                        ffbe_player.EMBLEM_WEEKLY_GROUP,
                        ffbe_player.EMBLEM_MILESTONE_GROUP):
                self.assertEqual(result[tag], [])
            self.assertEqual(ffbe_player.credit_emblem_objectives(
                "{}", {}, "x5Unqg2d"), {})
            self.assertFalse(player.dirty)

    def test_native_features_have_a_client_side_unavailable_path(self):
        source = (ROOT / 'source/exvius/android_test.js').read_text()
        for key in ('FUNCTION_PANEL_QUEST', 'FUNCTION_EMBLEM_EVENT',
                    'FUNCTION_COMEBACK_QUEST', 'FUNCTION_REEL_EXPEDITION',
                    'FUNCTION_SELECT_WORLD_DIVISION',
                    'FUNCTION_THIRDWORLD_CHANGE', 'FUNCTION_WORLD_CHANGE'):
            self.assertIn(key, source)
