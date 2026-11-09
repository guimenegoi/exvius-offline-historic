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

    def test_single_original_global_softlaunch_video_supports_all_four_surfaces(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        epoch = doc["eras"][0]
        times = {"home": 10, "units": 35, "summons": 80, "vortex": 245}
        original_video = None
        for surface, second in times.items():
            rec = epoch["screens"][surface]
            self.assertEqual(rec["status"], "reference-collected")
            self.assertFalse(rec["layout_verified"])
            ref_id = f"ushi-2016-05-22-{surface}-{second:03d}"
            linked = [rec["reference"]] + rec.get("secondary_references", [])
            self.assertIn(ref_id, linked)
            source = doc["references"][ref_id]
            self.assertEqual(source["surface"], surface)
            self.assertEqual(source["region"], "GL")
            self.assertEqual(source["type"], "dated-video-frame")
            self.assertEqual(source["video_upload_date"], "2016-05-22")
            self.assertIsNone(source["capture_date"])
            self.assertEqual(source["frame_second"], second)
            self.assertTrue(source["source"].endswith(f"&t={second}s"))
            self.assertTrue(source["local_path"].startswith(
                "data/ui-snapshots/references/video-global-2016-05-22/"))
            self.assertEqual(len(source["sha256"]), 64)
            self.assertGreater(len(source["visible_controls"]), 3)
            if original_video is None:
                original_video = source["video_full_sha256"]
            else:
                self.assertEqual(original_video, source["video_full_sha256"])
            file = ROOT / source["local_path"]
            if file.is_file():
                self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),
                                 source["sha256"])
        self.assertEqual(
            {"Forge", "Abilities", "Synthesize"},
            set(doc["references"]["ushi-2016-05-22-home-010"]["visible_controls"])
            & {"Forge", "Abilities", "Synthesize"})
        self.assertIn(
            "Chamber of Creation",
            doc["references"]["ushi-2016-05-22-vortex-245"]["visible_controls"])

    def test_2022_global_home_update_is_separate_from_vision_card_items(self):
        doc = json.loads(INDEX.read_text(encoding="utf-8"))
        milestone = next(item for item in doc["transition_sources"]
                         if item.get("date") == "2022-09-22")
        self.assertEqual(milestone["region"], "GL")
        self.assertEqual(milestone["month"], "2022-09")
        self.assertTrue(milestone["source"].startswith("https://"))
        self.assertIn("Unit Enhance/Awaken", milestone["proves"])
        self.assertFalse(next(era for era in doc["eras"]
                         if era["id"] == "global-2022-ui")["screens"]["home"]
                         .get("layout_verified", False))

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

    def test_original_ui_atlas_provenance_is_pinned_per_client(self):
        clients = json.loads(INDEX.read_text(encoding="utf-8"))["client_builds"]
        early = clients[:2]
        for client in clients:
            packs = client["cpk_evidence"]
            self.assertEqual(len(packs), 3 if client["bundled_common_cpk"] else 1)
            for pack in packs:
                self.assertTrue(pack["path"].startswith("assets/cpk/"))
                self.assertEqual(len(pack["sha256"]), 64)
                self.assertGreater(pack["entry_count"], 0)
                for asset, checksum in pack["asset_sha256"].items():
                    self.assertFalse(asset.startswith("/"))
                    self.assertNotIn("..", asset.split("/"))
                    self.assertEqual(len(checksum), 64)
            self.assertFalse(client["layout_verified"])
        self.assertEqual(early[0]["cpk_evidence"], early[1]["cpk_evidence"])
        original = early[0]["cpk_evidence"][0]
        self.assertEqual(original["entry_count"], 148)
        self.assertEqual(original["sprite_frame_counts"],
                         {"image/ui/common/common.plist": 119,
                          "image/ui/header/header.plist": 8,
                          "image/ui/footer/footer.plist": 14})
        self.assertEqual(len(original["asset_sha256"]), 6)
        pretutorial = early[0]["cpk_evidence"][1]
        self.assertEqual(pretutorial["entry_count"], 105)
        self.assertTrue(pretutorial["path"].endswith("resources_common_pretutorial.cpk"))
        self.assertNotEqual(pretutorial["asset_sha256"]["layout/header/layout_header.csv"],
                            original.get("asset_sha256", {}).get("layout/header/layout_header.csv"))
        self.assertEqual(early[0]["cpk_evidence"][1], early[1]["cpk_evidence"][1])
        rebuilt = clients[2]["cpk_evidence"]
        self.assertFalse(any(p["path"] == original["path"] for p in rebuilt))
        self.assertNotEqual(early[1]["cpk_evidence"][-1]["sha256"], rebuilt[0]["sha256"])
        self.assertEqual(rebuilt[0]["entry_count"], 292)

    def test_dated_2016_global_home_reference_is_not_assumed_capture_date(self):
        ref = json.loads(INDEX.read_text(encoding="utf-8"))["references"]["moby-4036609"]
        self.assertEqual(ref["archive_date"], "2016-07-12")
        self.assertIsNone(ref["capture_date"])
        self.assertTrue(ref["source"].endswith("/android/851459/"))

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
