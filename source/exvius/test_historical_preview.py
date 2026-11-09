"""Asset-free smoke tests for the restricted launch/July APK preview."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT / "source/exvius"))
sys.path.insert(0, str(PROJECT / "source/server"))
from build_historical_preview import build_preview
from historical_progression import current_month
from historical_summons import load_verified_unit_releases
from offline_menu import next_historical_update, status


class FakePlayer:
    def __init__(self, historical="2016-06"):
        self.data = {"meta": {"historical_month": historical, "historical_preview": True},
                     "identity": {"handle_name": "Rain"}, "rank": {"level": 1}}
        self.dirty = False
        self.fail_save = False

    def save(self, path, force=False):
        if self.fail_save:
            return False
        Path(path).write_text(json.dumps(self.data))
        self.dirty = False
        return True


class PreviewTests(unittest.TestCase):
    def test_catalogue_has_only_base_rarity_and_manual_preview_status(self):
        path = PROJECT / "source/server/content/historical_unit_releases_preview.json"
        document = json.loads(path.read_text())
        self.assertEqual(document["status"], "preview")
        self.assertEqual(document["latest_month"], "2016-07")
        self.assertEqual(len(document["units"]), 69)
        for unit in document["units"].values():
            self.assertEqual(list(unit["rarities"]), [unit["base_rarity"]])
            self.assertEqual(len(unit["channels"]), 1)
        self.assertEqual(document["units"],
                         load_verified_unit_releases(preview=True))

    def test_builder_matches_shipped_generated_evidence(self):
        base = PROJECT / "source/server/content"
        launch = json.loads((base / "historical_launch_candidates.json").read_text())
        debuts = json.loads((base / "historical_unit_candidates.json").read_text())
        self.assertEqual(build_preview(launch, debuts)["units"],
                         load_verified_unit_releases(preview=True))

    def test_advance_is_saved_exactly_once(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root) / "campaign.json"
            player = FakePlayer()
            self.assertTrue(player.save(save))
            state = SimpleNamespace(player=player, state_dirty=True)
            first = next_historical_update(state, save, "campaign")
            self.assertEqual(first["historical_month"], "2016-07")
            self.assertEqual(current_month(json.loads(save.read_text())), "2016-07")
            self.assertFalse(state.state_dirty)
            second = next_historical_update(state, save, "campaign")
            self.assertEqual(second["historical_month"], "2016-07")
            self.assertEqual(status(state, save)["latest_preview_month"], "2016-07")

    def test_save_failure_rolls_back_period(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root) / "campaign.json"
            player = FakePlayer()
            player.save(save)
            state = SimpleNamespace(player=player, state_dirty=True)
            player.fail_save = True
            with self.assertRaises(OSError):
                next_historical_update(state, save, "campaign")
            self.assertEqual(player.data["meta"]["historical_month"], "2016-06")
            self.assertEqual(json.loads(save.read_text())["meta"]["historical_month"], "2016-06")
            self.assertFalse(player.dirty)

    def test_existing_unmarked_save_uses_backup_new_game_path(self):
        with tempfile.TemporaryDirectory() as root:
            save = Path(root) / "campaign.json"
            save.write_text("{}")
            player = FakePlayer()
            player.data["meta"].clear()
            state = SimpleNamespace(player=player, state_dirty=False)
            with patch("offline_menu.new_game", return_value={"has_save": True}) as patched:
                self.assertEqual(next_historical_update(state, save, "campaign"), {"has_save": True})
                patched.assert_called_once()


if __name__ == "__main__":
    unittest.main()
