"""Evidence-contract tests: historical UI snapshots must not be invented."""
import hashlib
import json
from pathlib import Path
from unittest import TestCase

ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT / "source/server/content/historical_ui_snapshots.json"


class HistoricalUiSnapshotEvidence(TestCase):
    def test_evidence_index_is_explicitly_non_rendering(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], 1)
        self.assertEqual(doc["region"], "GL")
        self.assertEqual(doc["status"], "evidence-inventory-not-a-renderer")
        self.assertEqual(len({era["id"] for era in doc["eras"]}), len(doc["eras"]))
        for era in doc["eras"]:
            self.assertIn(era["confidence"], ("partial", "transition-only", "client-baseline"))
            self.assertTrue(era["screens"])
            for surface, record in era["screens"].items():
                self.assertIn(surface, ("home", "summons", "vortex", "units"))
                self.assertIn(record["status"], ("missing", "reference-collected", "local-baseline"))
                if record["status"] == "reference-collected":
                    self.assertFalse(record["layout_verified"])
                    self.assertIn(record["reference"], doc["references"])

    def test_local_reference_hash_when_present(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        for ref in doc["references"].values():
            self.assertTrue(ref["source"].startswith("https://"))
            path = ROOT / ref["local_path"]
            if path.is_file() and "sha256" in ref:
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), ref["sha256"])

    def test_no_unverified_era_is_active_layout(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertFalse(any(record.get("layout_verified") is True
                             for era in doc["eras"] for record in era["screens"].values()))
        self.assertEqual(doc["eras"][0]["from"], "2016-06")
        self.assertTrue(any(era["from"] == "2022-09" for era in doc["eras"]))
