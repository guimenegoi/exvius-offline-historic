"""Standalone contract tests, no game data download or Android dependency."""
import json
from pathlib import Path
import unittest

from historical_core.policy import HistoricalPolicy


class HistoricalPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = HistoricalPolicy.from_file()
        cls.data = json.loads(Path(__file__).with_name("catalogue_2016.json").read_text())

    def test_catalogue_has_only_evidenced_2016_entries(self):
        entries = self.data["entries"]
        self.assertEqual(len(entries), 35)
        self.assertEqual(sum(x["kind"] == "event" for x in entries), 14)
        self.assertEqual(sum(x["kind"] == "banner" for x in entries), 21)
        self.assertEqual(len({x["key"] for x in entries}), 35)
        self.assertTrue(all(x["release"].startswith("2016-") for x in entries))
        self.assertTrue(all(x["source"] for x in entries))

    def test_2016_banner_catalogue_matches_original_source(self):
        source = json.loads(Path("source/server/gacha_community.json").read_text())["banners"]
        expected = {str(b["id"]): (b["name"], b["release"])
                    for b in source if b.get("release", "").startswith("2016-")}
        actual = {b["native_id"]: (b["name"], b["release"])
                  for b in self.data["entries"] if b["kind"] == "banner"}
        self.assertEqual(actual, expected)

    def test_original_events_are_not_relabelled_2017_reruns(self):
        source = json.loads(Path("source/server/event_archive.json").read_text())["events"]
        dated_2016 = {str(e["area"]) for e in source
                      if str(e.get("release", "")).startswith("2016-")}
        self.assertFalse(dated_2016)
        events = [e for e in self.data["entries"] if e["kind"] == "event"]
        self.assertTrue(all(e["native_id"] is None and
                            e["status"] == "identity_unresolved" for e in events))

    def test_banner_unlocks_on_debut_and_stays_available(self):
        key = "banner:9100000"
        self.assertEqual(self.policy.check(key, "2016-07-07").reason, "not_yet_released")
        self.assertTrue(self.policy.check(key, "2016-07-08").allowed)
        self.assertTrue(self.policy.check(key, "2024-10-30").allowed)

    def test_unknown_content_denied(self):
        self.assertEqual(self.policy.check("banner:999999", "2019-01-01").reason, "unknown_content")

    def test_original_events_without_native_ids_stay_blocked(self):
        key = "event:The Giant of Babel"
        self.assertEqual(self.policy.check(key, "2016-10-13").reason, "not_yet_released")
        self.assertEqual(self.policy.check(key, "2016-10-14").reason, "identity_or_pool_unverified")
        self.assertFalse(self.policy.check(key, "2024-10-30").allowed)

    def test_inconsistent_banner_pool_stays_blocked(self):
        self.assertEqual(self.policy.check("banner:9100016", "2016-11-25").reason,
                         "identity_or_pool_unverified")

    def test_outside_global_period(self):
        self.assertEqual(self.policy.check("banner:9100000", "2016-06-29").reason,
                         "outside_global_period")
        self.assertEqual(self.policy.check("banner:9100000", "2024-10-31").reason,
                         "outside_global_period")

    def test_account_conditions_are_additional_and_nonmutating(self):
        row = dict(key="banner:test", kind="banner", native_id="42",
                   release="2016-07-01", confidence="B",
                   status="catalogue_candidate", minimum_rank=10,
                   required_flags=["story:1"])
        policy = HistoricalPolicy([row])
        account = {"rank": 9, "flags": ["story:1"]}
        before = json.dumps(account, sort_keys=True)
        self.assertEqual(policy.check("banner:test", "2016-07-01", account).reason,
                         "rank_requirement")
        self.assertEqual(policy.check("banner:test", "2016-07-01",
                                      {"rank": 10, "flags": []}).reason, "story_requirement")
        self.assertTrue(policy.check("banner:test", "2016-07-01",
                                     {"rank": 10, "flags": ["story:1"]}).allowed)
        self.assertEqual(json.dumps(account, sort_keys=True), before)

    def test_duplicate_keys_and_invalid_dates_rejected(self):
        row = dict(key="x", release="2016-07-01", confidence="B")
        with self.assertRaises(ValueError):
            HistoricalPolicy([row, row])
        with self.assertRaises(ValueError):
            HistoricalPolicy([dict(row, release="2016-13-01")])

    def test_store_content_is_out_of_scope(self):
        row = dict(key="shop:bundle", kind="shop", native_id="123",
                   release="2016-07-01", confidence="A",
                   status="catalogue_candidate")
        with self.assertRaisesRegex(ValueError, "unsupported historical content kind"):
            HistoricalPolicy([row])
        self.assertEqual(self.policy.check("shop:bundle", "2016-07-08").reason,
                         "unknown_content")

    def test_invalid_selected_date_rejected(self):
        with self.assertRaises(ValueError):
            self.policy.check("banner:9100000", "July 2016")


if __name__ == "__main__":
    unittest.main()
