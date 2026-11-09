"""2016 Global cross-index audit is diagnostic, never an unlock source."""
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_historical_2016 import audit, ROOT


class Audit2016Tests(unittest.TestCase):
    def test_missing_editorial_debut_is_not_a_release_verdict(self):
        banners = [{"id": "1", "release": "2016-07-08",
                    "community": {"units": ["Known", "Unknown"],
                                  "unit_ids": ["10", "11"]}}]
        result = audit(banners, [{"name": "Known", "release": "2016-07-08"}], [])
        self.assertEqual(result["status"], "AUDIT_ONLY_NOT_AN_UNLOCK_CATALOGUE")
        self.assertEqual(result["summary"]["featured_name_mentions"], 2)
        self.assertEqual([a["name"] for a in result["anomalies"]], ["Unknown"])
        self.assertNotIn("approved", result)

    def test_mismatched_featured_id_count_is_detected(self):
        result = audit([{"id": "9100016", "release": "2016-11-25",
                         "community": {"units": ["A", "B"], "unit_ids": ["1"]}}],
                       [{"name": "A", "release": "2016-11-25"},
                        {"name": "B", "release": "2016-11-25"}], [])
        self.assertEqual(result["anomalies"][0]["type"], "featured_name_id_count_mismatch")

    def test_earlier_release_is_a_review_flag_only(self):
        result = audit([{"id": "1", "release": "2016-07-08",
                         "community": {"units": ["Future"], "unit_ids": ["1"]}}],
                       [{"name": "Future", "release": "2016-08-01"}], [])
        self.assertEqual(result["anomalies"][0]["type"], "debut_after_banner")

    def test_actual_2016_baseline(self):
        root = ROOT / "source/server"
        b = json.loads((root / "gacha_community.json").read_text())["banners"]
        d = json.loads((root / "content/historical_unit_debuts.json").read_text())["debuts"]
        e = json.loads((root / "event_archive.json").read_text())["events"]
        result = audit(b, d, e)
        self.assertEqual(result["summary"]["banners"], 21)
        self.assertEqual(result["summary"]["event_areas_2016"], 0)
        self.assertEqual(result["summary"]["event_areas_undated"], 131)
        self.assertEqual([a["banner_id"] for a in result["anomalies"]
                          if a["type"] == "featured_name_id_count_mismatch"], ["9100016"])
        self.assertTrue(any(a["name"] == "Gilgamesh" for a in result["anomalies"]
                            if a["type"] == "no_matching_editorial_debut"))


if __name__ == "__main__":
    unittest.main()
