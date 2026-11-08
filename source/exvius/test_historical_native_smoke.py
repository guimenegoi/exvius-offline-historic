"""Integration smoke test against optional, locally extracted original Global tables.

Skipped when official game data is unavailable (CI and fresh checkouts).
"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
HAS_NATIVE = (
    (DATA / "mst_decoded/F_UNIT_MST.ndjson").is_file()
    and (DATA / "text_decoded/F_TEXT_UNITS_NAME.ndjson").is_file()
)
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "source/server"))


@unittest.skipUnless(HAS_NATIVE, "Original Global tables not locally extracted.")
class NativeGlobalSmokeTests(unittest.TestCase):
    def test_july_2016_kefka_banner_pool_excludes_future_units(self):
        # Keep data_paths' import-time binding isolated to this test method.
        original = os.environ.get("FFBE_DATA")
        try:
            os.environ["FFBE_DATA"] = str(DATA)
            from player_state import expand_pool
            from historical_progression import eligible_pool
            banners = json.loads((ROOT / "source/server/gacha_community.json").read_text())["banners"]
            catalogue = json.loads((ROOT / "source/server/content/historical_unit_candidates.json").read_text())
            index = {
                next(f["base_unit_id"] for f in unit["candidate_families"]
                     if f["matching_initial_rarity"]): unit["release"]
                for unit in catalogue["units"] if unit["status"] == "unique_rarity_candidate"
            }
            selected = eligible_pool(expand_pool(banners[0]), index, "2016-07")
            self.assertEqual({entry["unit_id"] for entry in selected},
                             {"100004604", "204001403", "206001703"})
            self.assertAlmostEqual(sum(entry["rate"] for entry in selected), 1.0)
            self.assertTrue(all(index[entry["unit_id"]] <= "2016-07-31"
                                for entry in selected))
        finally:
            if original is None:
                os.environ.pop("FFBE_DATA", None)
            else:
                os.environ["FFBE_DATA"] = original


if __name__ == "__main__":
    unittest.main()
