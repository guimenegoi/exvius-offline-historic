"""Offline tests of native-Global unit names and rarity candidate matching."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_historical_unit_candidates import (
    build_candidates, original_global_index, requested_rarity
)


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.mst = [
            {"3HriTp6B": "100", "woghJa61": "100", "9fW0TePj": "3"},
            {"3HriTp6B": "101", "woghJa61": "100", "9fW0TePj": "4"},
            {"3HriTp6B": "102", "woghJa61": "100", "9fW0TePj": "5"},
            {"3HriTp6B": "200", "woghJa61": "200", "9fW0TePj": "3"},
            {"3HriTp6B": "207", "woghJa61": "207", "9fW0TePj": "7"},
            {"3HriTp6B": "307", "woghJa61": "307", "9fW0TePj": "7"},
            {"3HriTp6B": "317", "woghJa61": "317", "9fW0TePj": "7"},
        ]
        self.text = [
            {"key": "MST_UNIT_NAME_100", "v": ["Kefka", "Kefka"]},
            {"key": "MST_UNIT_NAME_101", "v": ["Kefka", "Kefka"]},
            {"key": "MST_UNIT_NAME_102", "v": ["Kefka", "Kefka"]},
            {"key": "MST_UNIT_NAME_200", "v": ["Amarant", "Amarant"]},
            {"key": "MST_UNIT_NAME_207", "v": ["Amarant", "Amarant"]},
            {"key": "MST_UNIT_NAME_307", "v": ["NV Hero", "NV Hero"]},
            {"key": "MST_UNIT_NAME_317", "v": ["NV Hero", "NV Hero"]},
        ]
        self.history = {"source": {"sha256": "a" * 64}, "debuts": [
            {"name": "Kefka", "release": "2016-07-08", "rarity": "3~5★", "note_line": 1},
            {"name": "Amarant", "release": "2016-08-19", "rarity": "3~5★", "note_line": 2},
            {"name": "NV Hero", "release": "2021-08-19", "rarity": "NV", "note_line": 3},
            {"name": "Unknown", "release": "2016-09-01", "rarity": "4★", "note_line": 4},
        ]}

    def test_native_name_and_rarity_filter(self):
        result = build_candidates(self.history, self.mst, self.text)
        self.assertEqual(result["counts"], {
            "missing_original_global_name": 1,
            "multiple_original_families": 1,
            "unique_rarity_candidate": 2,
        })
        first = result["units"][0]
        self.assertEqual(first["candidate_families"],
                         [{"base_unit_id": "100", "base_rarity": "3",
                           "matching_initial_rarity": True,
                           "form_ids": ["100", "101", "102"]}])
        amarant = result["units"][1]
        self.assertEqual([c["base_unit_id"] for c in amarant["candidate_families"]
                          if c["matching_initial_rarity"]], ["200"])
        self.assertEqual(result["units"][2]["status"], "multiple_original_families")
        self.assertEqual(result["version"], 2)
        self.assertTrue(result["usage"].startswith("AUDIT"))

    def test_repeated_and_conditional_are_not_approved(self):
        self.history["debuts"].append(
            {"name": "Kefka", "release": "2021-01-01", "rarity": "NV", "note_line": 5})
        self.history["debuts"][1]["access"] = "conditional"
        result = build_candidates(self.history, self.mst, self.text)
        self.assertEqual(result["units"][0]["status"], "repeated_name_different_dates")
        self.assertEqual(result["units"][-1]["status"], "repeated_name_different_dates")
        self.assertEqual(result["units"][1]["status"], "conditional_availability")

    def test_unknown_rarity_fails_closed(self):
        self.history["debuts"][0]["rarity"] = None
        result = build_candidates(self.history, self.mst, self.text)
        self.assertEqual(result["units"][0]["status"], "unverified_initial_rarity")
        self.assertIsNone(requested_rarity(None))
        self.assertEqual(requested_rarity("NV"), "7")

    def test_banner_conflicts_reported_not_rewritten(self):
        source = {"banners": [
            {"id": "9", "community": {"units": ["Kefka", "Amarant", "Missing"],
                                    "unit_ids": ["200", "200", "999"]}}]}
        report = build_candidates(self.history, self.mst, self.text, source)
        audit = report["community_id_audit"]
        self.assertEqual(audit["references_checked"], 3)
        self.assertEqual(audit["references_with_different_global_name"], 1)
        self.assertEqual(audit["references_absent_from_original_text"], 1)
        self.assertEqual(report["units"][0]["candidate_families"][0]["base_unit_id"], "100")


if __name__ == "__main__":
    unittest.main()
