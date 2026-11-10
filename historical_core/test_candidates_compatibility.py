"""Research indexing and read-only release-compatibility contracts."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from historical_core.build_candidates import OUT, ROOT, build
from historical_core.compatibility import apk_fingerprint, compare_sources
from historical_core.policy import HistoricalPolicy


class CandidateTests(unittest.TestCase):
    def test_deterministic_catalogue_and_no_promotion(self):
        expected = build()
        actual = json.loads(OUT.read_text(encoding="utf-8"))
        self.assertEqual(actual, expected)
        self.assertEqual(actual["counts"]["banner"], 348)
        self.assertEqual(actual["counts"]["community_event"], 637)
        self.assertEqual(len(actual["rejected_invalid_dates"]), 4)
        self.assertTrue(all(x["raw_date"] == "2022-06-31"
                            for x in actual["rejected_invalid_dates"]))
        self.assertTrue(all(x["status"] == "unverified_historical_candidate"
                            for x in actual["entries"]))

    def test_candidates_not_automatically_eligible(self):
        candidates = build()["entries"]
        policy = HistoricalPolicy.from_file()
        self.assertEqual(policy.check(candidates[0]["key"], "2024-10-30").reason,
                         "unknown_content")
        policy_with_candidates = HistoricalPolicy(candidates)
        self.assertFalse(policy_with_candidates.check(candidates[0]["key"], "2024-10-30").allowed)

    def test_community_index_only_uses_global_region(self):
        raw = json.loads((ROOT / "source/server/community_events.json").read_text())["events"]
        source = {(x["url"], x["start"]) for x in raw if x.get("region") == "global"}
        for item in build()["entries"]:
            if item["kind"] == "community_event":
                self.assertIn((item["source"], item["release"]), source)


class CompatibilityTests(unittest.TestCase):
    def test_same_source_ref_has_no_changes(self):
        report = compare_sources(ROOT, "upstream/main", "upstream/main")
        self.assertFalse(report["runtime_changed"])
        self.assertEqual(report["changes"], [])
        self.assertEqual(report["binary_engine_compatibility"], "not_established")

    def test_current_historic_branch_only_adds_docs_and_core(self):
        report = compare_sources(ROOT, "upstream/main", "HEAD")
        self.assertFalse(report["runtime_changed"])
        self.assertTrue(all(x["category"] in ("other", "documentation")
                            for x in report["changes"]))

    def test_fork_does_not_modify_upstream_gameplay_or_store(self):
        report = compare_sources(ROOT, "upstream/main", "HEAD")
        self.assertFalse(report["runtime_changed"])
        self.assertFalse(any(x["path"].startswith(("source/server/", "source/exvius/",
                                                   "source/memorial/", "release/"))
                             for x in report["changes"]))

    def test_apk_fingerprint_detects_assets_without_claiming_compatibility(self):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / "synthetic.apk"
            with zipfile.ZipFile(apk, "w") as f:
                f.writestr("lib/arm64-v8a/libgame.so", b"native-test")
                f.writestr("assets/rules/native_content.zip", b"rules-test")
            result = apk_fingerprint(apk)
            self.assertEqual(result["rules_asset_count"], 1)
            self.assertEqual(result["chaquopy_asset_count"], 0)
            self.assertEqual(result["binary_engine_compatibility"], "not_established")
            self.assertEqual(len(result["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
