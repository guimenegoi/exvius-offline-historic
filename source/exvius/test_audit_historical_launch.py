"""Unit tests for the reported early-Global roster audit."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_historical_launch import audit_snapshot


class LaunchAuditTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = {
            "schema": 1, "status": "unverified_launch_snapshot",
            "source_url": "https://example.invalid/report",
            "source_period": "Before first July banner, date uncertain",
            "units": [
                {"source_name": "Paladin Cecil", "master_name": "Cecil",
                 "base_rarity": "3", "acquisition": "unknown"},
                {"source_name": "Rain", "base_rarity": "2", "acquisition": "story"},
                {"source_name": "Magitek Armor Terra", "base_rarity": "3",
                 "acquisition": "pre_registration"},
            ],
        }
        self.master = [
            {"3HriTp6B": "101", "woghJa61": "101", "9fW0TePj": "3"},
            {"3HriTp6B": "102", "woghJa61": "101", "9fW0TePj": "5"},
            {"3HriTp6B": "201", "woghJa61": "201", "9fW0TePj": "2"},
            {"3HriTp6B": "301", "woghJa61": "301", "9fW0TePj": "3"},
        ]
        self.text = [
            {"key": "MST_UNIT_NAME_101", "v": ["Cecil", "Cecil"]},
            {"key": "MST_UNIT_NAME_102", "v": ["Cecil", "Cecil"]},
            {"key": "MST_UNIT_NAME_201", "v": ["Rain", "Rain"]},
            {"key": "MST_UNIT_NAME_301", "v": ["Magitek Armor Terra", "Magitek Armor Terra"]},
        ]

    def test_native_id_match_does_not_authorize_summon(self):
        audit = audit_snapshot(self.snapshot, self.master, self.text)
        self.assertEqual(audit["summary"], {
            "native_identity_match_acquisition_unknown": 1,
            "registration_candidate_not_rare": 1,
            "story_candidate_not_rare": 1,
        })
        self.assertEqual(audit["units"][0]["candidates"],
                         [{"base_unit_id": "101", "form_ids": ["101", "102"]}])
        self.assertEqual(audit["status"], "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE")
        self.assertNotIn("release", audit["units"][0])

    def test_second_source_is_corrobating_evidence_not_a_rare_summon_flag(self):
        self.snapshot["draw_source_url"] = "https://example.invalid/second"
        self.snapshot["draw_reported_names"] = ["Cecil", "Klein"]
        report = audit_snapshot(self.snapshot, self.master, self.text)
        self.assertEqual(report["units"][0]["status"],
                         "reported_drawable_acquisition_unverified")
        self.assertEqual(report["draw_names_not_matched"], ["Klein"])
        self.assertEqual(report["units"][1]["status"], "story_candidate_not_rare")
        self.assertNotIn("historical_month", report)
        self.assertEqual(report["status"], "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE")

    def test_wrong_base_rarity_is_not_accepted(self):
        self.snapshot["units"][0]["base_rarity"] = "5"
        report = audit_snapshot(self.snapshot, self.master, self.text)
        self.assertEqual(report["units"][0]["status"], "missing_or_rarity_conflict")

    def test_invalid_snapshot_refuses(self):
        self.snapshot["status"] = "verified"
        with self.assertRaises(ValueError):
            audit_snapshot(self.snapshot, self.master, self.text)


if __name__ == "__main__":
    unittest.main()
