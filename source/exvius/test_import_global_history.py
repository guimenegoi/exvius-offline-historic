"""Asset-free tests for curated Global release evidence import."""
import sys
from pathlib import Path
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from import_global_history import (
    audit_community_banners, import_note, parse_debuts, split_outside_parentheses
)


class ImportGlobalHistoryTests(unittest.TestCase):
    def test_commas_in_annotations_do_not_create_units(self):
        items = split_outside_parentheses(
            "Kelsus 5~6★ (Shard summon, not immediately available), Zyrus")
        self.assertEqual(len(items), 2)

    def test_debuts_preserve_dates_and_special_access(self):
        note = ("- **2016-07-08** · :LiSparkles: Unidades lançadas — "
                "Kefka 3~5★, Golbez 3~5★\n"
                "- **2017-06-01** · :LiSparkles: Unidades lançadas — "
                "Kelsus 5~6★ (Shard summon, not immediately available), Zyrus\n")
        data = parse_debuts(note)
        self.assertEqual(len(data["debuts"]), 4)
        self.assertEqual(data["parse_warnings"], [])
        kelsus = next(r for r in data["debuts"] if r["name"] == "Kelsus")
        self.assertEqual(kelsus["release"], "2017-06-01")
        self.assertEqual(kelsus["access"], "conditional")
        self.assertIn("not immediately available", kelsus["annotation"])
        zyrus = next(r for r in data["debuts"] if r["name"] == "Zyrus")
        self.assertIsNone(zyrus["rarity"])

    def test_missing_separator_is_not_invented(self):
        note = ("- **2017-10-06** · :LiSparkles: Unidades lançadas — "
                "Yuri 3~5★ Cheerleader Fina 4~5★ (exclusive)\n")
        data = parse_debuts(note)
        self.assertEqual(data["debuts"], [])
        self.assertEqual(data["parse_warnings"][0]["reason"], "multiple-units-in-entry")

    def test_duplicate_name_on_different_dates_stays_ambiguous(self):
        note = ("- **2017-03-17** · :LiSparkles: Unidades lançadas — Y'shtola 5★\n"
                "- **2020-04-23** · :LiSparkles: Unidades lançadas — Y'shtola 6★\n")
        data = parse_debuts(note)
        self.assertEqual(data["ambiguous_names"],
                         [{"name": "Y'shtola", "dates": ["2017-03-17", "2020-04-23"]}])

    def test_reused_banner_ids_are_reported_not_accepted(self):
        source = {"banners": [
            {"community": {"release": "2016-07-08", "units": ["Kefka"], "unit_ids": ["1"]}},
            {"community": {"release": "2020-02-01", "units": ["Future Hero"], "unit_ids": ["1"]}}
        ]}
        debut = [{"name": "Kefka", "release": "2016-07-08"}]
        audit = audit_community_banners(debut, source)
        self.assertEqual(len(audit["colliding_unit_ids"]), 1)
        self.assertEqual(audit["matched_distinct_unit_ids"], 1)
        self.assertEqual(audit["colliding_unit_ids"][0]["unit_id"], "1")

    def test_generated_catalogue_has_traceable_source(self):
        doc = import_note(
            b"- **2016-07-08** \xc2\xb7 :LiSparkles: Unidades lan\xc3\xa7adas \xe2\x80\x94 Kefka 3~5\xe2\x98\x85\n")
        self.assertEqual(doc["version"], 1)
        self.assertEqual(len(doc["source"]["sha256"]), 64)
        self.assertEqual(doc["debuts"][0]["name"], "Kefka")
        self.assertNotIn("unit_id", doc["debuts"][0])


if __name__ == "__main__":
    unittest.main()
