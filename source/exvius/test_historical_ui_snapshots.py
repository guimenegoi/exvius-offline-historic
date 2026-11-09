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

    def test_archived_global_clients_are_evidence_not_active_layouts(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        clients = doc["client_builds"]
        self.assertEqual([item["version"] for item in clients],
                         ["1.2.0", "1.4.1", "2.0.0"])
        self.assertEqual([item["archive_release_month"] for item in clients],
                         ["2016-11", "2017-01", "2017-02"])
        self.assertEqual(len({item["apk_sha256"] for item in clients}), 3)
        self.assertEqual(len({item["x86_libgame_sha256"] for item in clients}), 3)
        self.assertEqual(len({item["signing_cert_sha1"] for item in clients}), 1)
        for item in clients:
            self.assertEqual(item["region"], "GL")
            self.assertFalse(item["layout_verified"])
            self.assertEqual(len(item["apk_sha256"]), 64)
            self.assertEqual(len(item["x86_libgame_sha256"]), 64)
            self.assertEqual(len(item["signing_cert_sha1"]), 40)
            self.assertTrue(item["source"].startswith("https://appchive.net/apk/"))
            self.assertTrue(item["native_evidence"]["gate_list_layout"])

    def test_binary_proves_native_home_transition_without_claiming_ui_snapshot(self):
        clients = json.loads(INDEX.read_text(encoding="utf-8"))["client_builds"]
        for item in clients[:2]:
            self.assertTrue(item["native_evidence"]["home_draw_craft"])
            self.assertFalse(item["native_evidence"]["home_rotate_menu_list"])
            self.assertEqual(item["native_evidence"]["scene_export_counts"]["HomeRotateMenuList"], 0)
            self.assertTrue(item["bundled_common_cpk"])
        update = clients[2]
        self.assertFalse(update["native_evidence"]["home_draw_craft"])
        self.assertTrue(update["native_evidence"]["home_rotate_menu_list"])
        self.assertTrue(update["native_evidence"]["home_rotate_colosseum_orbs"])
        self.assertEqual(update["native_evidence"]["scene_export_counts"]["HomeRotateMenuList"], 27)
        self.assertFalse(update["bundled_common_cpk"])

    def test_verified_vortex_reference_is_still_unrendered(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        vortex = doc["eras"][0]["screens"]["vortex"]
        self.assertEqual(vortex["status"], "reference-collected")
        self.assertFalse(vortex["layout_verified"])
        ref = doc["references"][vortex["reference"]]
        self.assertEqual(ref["surface"], "vortex")
        self.assertEqual(ref["region"], "GL")
        self.assertTrue(ref["original_image"].endswith("vortex-dimensionnel-002.jpg"))

    def test_archived_client_checksum_validation_fails_closed(self):
        from tempfile import TemporaryDirectory
        from audit_historical_client_apks import audit
        client = json.loads(INDEX.read_text(encoding="utf-8"))["client_builds"][0]
        with TemporaryDirectory() as directory:
            path = Path(directory) / "untrusted.apk"
            path.write_bytes(b"not a verified signed FFBE Global package")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                audit(path, client)

    def test_no_unverified_era_is_active_layout(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        self.assertFalse(any(record.get("layout_verified") is True
                             for era in doc["eras"] for record in era["screens"].values()))
        self.assertEqual(doc["eras"][0]["from"], "2016-06")
        self.assertTrue(any(era["from"] == "2022-09" for era in doc["eras"]))
