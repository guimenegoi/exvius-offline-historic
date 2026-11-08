"""Tests for release-name candidates, not active game unlocks."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_historical_unit_candidates import build_candidates


class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.master = {"units": [
            {"original_id": "101", "identities": [
                {"server": "GL", "name": "Kefka", "source_unit_id": "100"}]},
            {"original_id": "102", "identities": [
                {"server": "GL", "name": "Kefka", "source_unit_id": "100"}]},
            {"original_id": "201", "identities": [
                {"server": "GL", "name": "Chizuru", "source_unit_id": "200"},
                {"server": "JP", "name": "Different JP Name", "source_unit_id": "200"}]},
            {"original_id": "301", "identities": [
                {"server": "GL", "name": "Amarant", "source_unit_id": "300"}]},
            {"original_id": "302", "identities": [
                {"server": "GL", "name": "Amarant", "source_unit_id": "302"}]},
        ]}
        self.history = {"source": {"sha256": "a" * 64}, "debuts": [
            {"name": "Kefka", "release": "2016-07-08",
             "rarity": "3~5★", "note_line": 1},
            {"name": "Amarant", "release": "2016-08-19",
             "rarity": "3~5★", "note_line": 2},
            {"name": "Unknown", "release": "2016-09-01",
             "rarity": "4★", "note_line": 3},
            {"name": "Chizuru", "release": "2016-07-08",
             "rarity": "4~5★", "access": "conditional", "note_line": 4},
        ]}

    def test_identity_statuses_and_explicit_source(self):
        result = build_candidates(self.history, self.master)
        self.assertEqual(result["counts"], {
            "conditional_availability": 1,
            "missing_global_identity": 1,
            "multiple_global_families": 1,
            "unique_name_candidate": 1,
        })
        self.assertEqual(result["usage"].split()[0], "AUDIT")
        self.assertEqual(result["units"][0]["candidate_families"],
                         [{"base_unit_id": "100", "form_ids": ["101", "102"]}])
        self.assertEqual(result["units"][1]["status"], "multiple_global_families")

    def test_community_ids_not_accepted_as_truth(self):
        community = {"banners": [
            {"id": "9", "community": {"units": ["Kefka", "Chizuru", "NoMatch"],
                                    "unit_ids": ["201", "201", "999"]}}]}
        result = build_candidates(self.history, self.master, community)
        audit = result["community_id_audit"]
        self.assertEqual(audit["references_checked"], 3)
        self.assertEqual(audit["references_with_different_global_name"], 1)
        self.assertEqual(audit["references_absent_from_gl_master"], 1)
        self.assertEqual(result["units"][0]["candidate_families"][0]["base_unit_id"], "100")

    def test_name_with_two_different_release_dates_requires_review(self):
        self.history["debuts"].append({
            "name": "Kefka", "release": "2021-01-01",
            "rarity": "NV", "note_line": 5})
        result = build_candidates(self.history, self.master)
        self.assertEqual(result["units"][0]["status"], "repeated_name_different_dates")
        self.assertEqual(result["units"][-1]["status"], "repeated_name_different_dates")


if __name__ == "__main__":
    unittest.main()
