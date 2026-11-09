"""2016 UI capabilities and server-side transaction/award gate regression."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "source/server"))

from historical_progression import FEATURE_INTRODUCED, historical_features, feature_available
from offline_menu import status


def preview(month="2016-06"):
    return {"meta": {"historical_preview": True, "historical_month": month},
            "identity": {"handle_name": "Rain"}, "rank": {"level": 1}}


class HistoricCapabilities(TestCase):
    def test_single_authoritative_period_matrix(self):
        june = historical_features(preview())
        self.assertTrue(june["world"])
        self.assertTrue(june["colosseum"])
        for name in ("arena", "expedition", "equipment_enhancement", "panel_quest",
                     "sp_challenge", "modern_login_calendar", "anniversary_ticket",
                     "catchup_rewards"):
            self.assertFalse(june[name], name)
        self.assertFalse(historical_features(preview("2016-07"))["expedition"])
        self.assertFalse(historical_features(preview("2016-09"))["arena"])
        self.assertTrue(historical_features(preview("2016-09"))["ability_awakening"])
        self.assertTrue(historical_features(preview("2016-11"))["arena"])
        self.assertFalse(historical_features(preview("2016-11"))["expedition"])
        # VC inventory arrived in 2020, but the decorative Home button and
        # attached BGM belong to the GL UI update on September 22, 2022.
        self.assertFalse(historical_features(preview("2020-07"))["vision_cards"])
        self.assertTrue(historical_features(preview("2020-08"))["vision_cards"])
        self.assertFalse(historical_features(preview("2020-08"))["home_vision_card_ornament"])
        self.assertTrue(historical_features(preview("2022-08"))["vision_cards"])
        self.assertFalse(historical_features(preview("2022-08"))["home_vision_card_ornament"])
        self.assertTrue(historical_features(preview("2022-09"))["home_vision_card_ornament"])
        self.assertTrue(historical_features(preview("2017-06"))["expedition"])
        self.assertFalse(historical_features(preview("2017-06"))["panel_quest"])
        self.assertTrue(feature_available("not-in-matrix", {"meta": {}}))
        self.assertFalse(feature_available("not-in-matrix", preview()))

    def test_entries_have_evidence_or_are_explicitly_unverified(self):
        for name, (month, url) in FEATURE_INTRODUCED.items():
            self.assertEqual(month is None, url is None, name)
            if month is not None:
                self.assertTrue(url.startswith("https://"), name)

    def test_corrupted_month_does_not_unblock(self):
        with self.assertRaises(ValueError):
            historical_features(preview("2030-any"))
        self.assertIsNone(historical_features({"meta": {}}))

    def test_status_is_projection_from_same_policy(self):
        player = SimpleNamespace(data=preview())
        info = status(SimpleNamespace(player=player), "/not/a/real/save")
        self.assertEqual(info["historical_features"], historical_features(player.data))
        self.assertTrue(info["historical_preview"])
        player.data["meta"].clear()
        self.assertIsNone(status(SimpleNamespace(player=player),
                                 "/not/a/real/save")["historical_features"])


class HistoricServerGates(TestCase):
    def setUp(self):
        import ffbe_state
        self.state = ffbe_state.State

    def test_expedition_and_panel_claim_cannot_mutate_preview(self):
        import exvius_actions
        # Use a handler that would mutate the player if allowed. The direct
        # request must be intercepted before invoking it.
        for request in ("hW0804Q9", "I8uq68c3", "2pe3Xa8b",
                        "r4A791RF", "AOY6npa3", "egJpaGtk"):
            with self.subTest(request=request):
                called = Mock(side_effect=lambda spec, req: {"mutated": True})
                player = SimpleNamespace(data=preview(), mode="live")
                with patch.object(self.state, "player", player), patch.object(
                        exvius_actions, "_all_handlers", return_value={request: called}), patch(
                        "exvius_colosseum.project", side_effect=lambda spec: spec):
                    self.assertEqual(exvius_actions.serve_actions(
                        {"original": []}, request, "{}"), {})
                    called.assert_not_called()
        # Unmarked saves are not changed by this preview-only safety gate.
        called = Mock(return_value={"legacy": True})
        with patch.object(self.state, "player", SimpleNamespace(
                data={"meta": {}}, mode="live")), patch.object(
                exvius_actions, "_all_handlers", return_value={"I8uq68c3": called}), patch(
                "exvius_colosseum.project", side_effect=lambda spec: spec):
            self.assertEqual(exvius_actions.serve_actions(
                {}, "I8uq68c3", "{}"), {"legacy": True})
            called.assert_called_once()

    def test_arena_refused_but_colosseum_kept_in_2016(self):
        import exvius_actions
        arena_ids = ("f8kXGWy0", "DgG4Cy0F", "eHY7X8Nn", "os4k7C0b",
                     "6ZNY3zAm", "kcW85SfU", "hqzU9Qc5")
        colosseum_ids = ("5g0vWZFq", "4uCSA3ko", "3zgbapQ7", "Un16HuNI")
        for request in (*arena_ids, *colosseum_ids):
            with self.subTest(request=request):
                handler = Mock(return_value={"would_mutate": True})
                player = SimpleNamespace(data=preview("2016-06"), mode="live")
                with patch.object(self.state, "player", player), patch.object(
                        exvius_actions, "_all_handlers", return_value={request: handler}), patch(
                        "exvius_colosseum.project", side_effect=lambda spec: spec):
                    result = exvius_actions.serve_actions({}, request, "{}")
                    if request in arena_ids:
                        self.assertEqual(result, {})
                        handler.assert_not_called()
                    else:
                        self.assertEqual(result, {"would_mutate": True})
                        handler.assert_called_once()
        # Transition: Arena is introduced in November 2016; older saves and
        # the original Colosseum request path remain unchanged.
        handler = Mock(return_value={"allowed": True})
        with patch.object(self.state, "player", SimpleNamespace(
                data=preview("2016-11"), mode="live")), patch.object(
                exvius_actions, "_all_handlers", return_value={arena_ids[0]: handler}), patch(
                "exvius_colosseum.project", side_effect=lambda spec: spec):
            self.assertEqual(exvius_actions.serve_actions(
                {}, arena_ids[0], "{}"), {"allowed": True})
            handler.assert_called_once()

    def test_colosseum_encounters_load_without_filesystem_specific_paths(self):
        from exvius_colosseum import _encounters
        source = _encounters()
        self.assertIsInstance(source, dict)
        self.assertTrue(source, 'Original Colosseum encounters must be available')

    def test_future_calendar_and_anniversary_do_not_award_2016(self):
        import ffbe_player
        player = SimpleNamespace(data=preview(), mode="live",
                                 advance_login_bonus=Mock(return_value=1),
                                 mark_anniversary_issued=Mock(),
                                 deliver_mail=Mock())
        with patch.object(self.state, "player", player):
            original = {"test": [], "f5bA4wFx": [{"from": "2021"}]}
            out = ffbe_player.serve_login_bonus(original, "vw9RP3i4")
            self.assertEqual(len(out["f5bA4wFx"]), 28)
            self.assertEqual(out["f5bA4wFx"][0]["YWF08vZS"], "30")
            self.assertEqual(out["f5bA4wFx"][0]["5GNDIwPX"], "500")
            self.assertEqual(out["DM63p52N"], [
                {"lO28ROQ0": "daily_login_banner_dailylogin_00.png"}])
            self.assertEqual(original["f5bA4wFx"], [{"from": "2021"}])
            ffbe_player.deliver_login_mail({"f5bA4wFx": []}, "vw9RP3i4")
            route = ffbe_player.ANNIVERSARY_TICKET_CARRIER.split(",")[0]
            ffbe_player.deliver_anniversary_ticket({}, route)
            self.assertEqual(ffbe_player._catchup_plan(), {})
            player.advance_login_bonus.assert_called_once()
            player.mark_anniversary_issued.assert_not_called()
            player.deliver_mail.assert_not_called()

    def test_future_panel_screens_are_empty_not_paid(self):
        import ffbe_player
        player = SimpleNamespace(data=preview())
        with patch.object(self.state, "player", player):
            pq = ffbe_player.serve_panel_quest(None, ffbe_player.PANEL_QUEST_REQUEST)
            self.assertEqual(pq[ffbe_player.PANEL_QUEST_SCHEDULE_TAG], [])
            self.assertEqual(pq[ffbe_player.PANEL_QUEST_INFO_TAG], [])
            sp = ffbe_player.serve_sp_challenge(None, ffbe_player.SP_CHALLENGE_REQUEST)
            self.assertEqual(sp[ffbe_player.SP_CHALLENGE_STATUS_TAG], [])
            self.assertEqual(sp[ffbe_player.SP_CHALLENGE_TICKER_TAG], [])
