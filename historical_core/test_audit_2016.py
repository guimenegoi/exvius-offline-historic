"""Contract tests preventing retroactive release of reconstructed reruns."""
import json
import unittest
from historical_core.audit_2016 import OUT, build
from historical_core.policy import HistoricalPolicy


class HistoricalAuditTests(unittest.TestCase):
    def test_reproducible_audit_and_counts(self):
        data = build()
        self.assertEqual(data, json.loads(OUT.read_text(encoding="utf-8")))
        self.assertEqual(data["counts"], {
            "original_events": 14,
            "events_with_archived_name_matches": 6,
            "archived_variants": 8,
            "banners": 21,
            "banners_with_featured_mismatch": 1,
            "cash_shop_bundles_in_offline_index": 13,
        })

    def test_all_name_matches_are_later_variants_not_original_ids(self):
        for event in build()["events"]:
            self.assertIsNone(event["original_native_id"])
            self.assertFalse(event["original_mission_and_reward_identity_verified"])
            self.assertEqual(event["decision"], "original_content_not_identified")
            for variant in event["archive_name_matches"]:
                self.assertTrue(variant["later_than_original_debut"])
                self.assertTrue(variant["missions"])

    def test_2016_events_remain_blocked_even_with_archived_variants(self):
        policy = HistoricalPolicy.from_file()
        for event in build()["events"]:
            decision = policy.check("event:" + event["name"], "2024-10-30")
            self.assertFalse(decision.allowed)

    def test_banner_pool_inconsistency_is_explicit(self):
        rows = [x for x in build()["banners"] if x["featured_count_mismatch"]]
        self.assertEqual([x["catalogue_id"] for x in rows], ["9100016"])
        self.assertEqual(len(rows[0]["community_featured_names"]), 4)
        self.assertEqual(len(rows[0]["community_featured_ids"]), 3)
        self.assertFalse(rows[0]["original_global_id_verified"])

    def test_offline_early_bird_is_not_2016_offer(self):
        warning = build()["cash_shop_warning"]
        self.assertEqual(warning["original_2016_early_bird_usd"], "3.99")
        self.assertEqual(warning["offline_early_bird_usd"], "1.99")
        self.assertEqual(warning["equivalence"], "not_established")


if __name__ == "__main__":
    unittest.main()
