"""Paid Global Shop offers unlock by introduction only; story towns keep upstream logic."""
import importlib
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "source/server"))
sys.path.insert(0, str(ROOT / "source/exvius"))

import ffbe_player
from exvius_actions_shops import item_buy
from ffbe_state import State
from historical_progression import (historical_commerce_catalogue,
                                    historical_premium_bundle_ids)


def preview(month="2016-06"):
    return {"meta": {"historical_preview": True, "historical_month": month}}


BUNDLE = {
    "id": "990000101",
    "name": "Evidence-backed Bundle",
    "available_from": "2016-07-08",
    "status": "approved",
    "source": "https://example.org/global-shop-source",
    "currency": "USD",
    "original_price": "1.99",
    "contents": ["50:1:5000"],
}


class HistoricalCommerceTests(TestCase):
    def test_catalogue_is_about_paid_shop_not_town_stores(self):
        catalogue = historical_commerce_catalogue()
        self.assertEqual(catalogue["schema"], 1)
        self.assertEqual(catalogue["region"], "GL")
        self.assertEqual(catalogue["unlock_policy"], "available_from_only_permanent")
        self.assertNotIn("town_stock", catalogue)
        self.assertEqual(catalogue["premium_bundles"], [])
        for row in catalogue["premium_bundles"]:
            self.assertNotIn("until", row)
            self.assertNotIn("expires", row)
            self.assertNotIn("end_date", row)

    def test_premium_bundles_only_unlock_forward_and_never_expire(self):
        catalogue = {"schema": 1, "region": "GL", "premium_bundles": [
            BUNDLE,
            {**BUNDLE, "id": "missing-source", "source": ""},
            {**BUNDLE, "id": "draft", "status": "candidate"},
            {**BUNDLE, "id": "future", "available_from": "2023-04-10"},
        ]}
        with patch("historical_progression.historical_commerce_catalogue",
                   return_value=catalogue):
            self.assertEqual(historical_premium_bundle_ids(preview("2016-06")), set())
            self.assertEqual(historical_premium_bundle_ids(preview("2016-07")),
                             {BUNDLE["id"]})
            self.assertEqual(historical_premium_bundle_ids(preview("2024-10")),
                             {BUNDLE["id"], "future"})
            self.assertIsNone(historical_premium_bundle_ids({"meta": {}}))
            with self.assertRaises(ValueError):
                historical_premium_bundle_ids(preview("bad month"))

    def test_historical_shop_only_lists_unlocked_cash_bundles(self):
        original_player = State.player
        State.player = SimpleNamespace(data=preview("2016-07"), dirty=False)
        source = [
            {"id": BUNDLE["id"], "name": "Evidence-backed Bundle",
             "usd": "1.99", "contents": ["50:1:5000"], "limit": "once"},
            {"id": "990000102", "name": "Not yet verified",
             "usd": "0.99", "contents": ["50:1:100"], "limit": "once"},
        ]
        try:
            with patch("historical_progression.historical_commerce_catalogue",
                       return_value={"schema": 1, "region": "GL",
                                     "premium_bundles": [BUNDLE]}), patch.object(
                    ffbe_player, "_global_bundles", return_value=source), patch.object(
                    __import__("player_state"), "_load_ndjson",
                    return_value={"100": {"FBjo93gK": "120",
                                          "AOHRcCC2": "0.99"}}), patch.object(
                    State, "replies", {}):
                out = ffbe_player.serve_lapis_shop(
                    {"3VS1Bhmf": [{"id": "2024-future-shop"}],
                     "fMohhKK8": [{"EzXXHtTY": "2024-bundle"}],
                     "pcjqhOI8": [{"EzXXHtTY": "2024-bundle"}]},
                    "uLXAMvCT")
                self.assertEqual(out["3VS1Bhmf"], [])
                self.assertEqual([row["EzXXHtTY"] for row in out["fMohhKK8"]],
                                 [BUNDLE["id"]])
                self.assertEqual([row["EzXXHtTY"] for row in out["pcjqhOI8"]],
                                 [BUNDLE["id"]])
                self.assertFalse(State.player.dirty)
        finally:
            State.player = original_player

    def test_original_town_shop_does_not_need_bespoke_release_date(self):
        original_player = State.player
        State.player = SimpleNamespace(data=preview(), mode="live", dirty=False)
        selection = {"2aciVI9Y": [{"Gh92V3Tx": 1101,
                                   "j9NS0H15": "20:101000100:2",
                                   "U1uaXph4": 200}]}

        def rows(name):
            if name == "F_TOWN_STORE_MST":
                return [{"Gh92V3Tx": "1101", "Z20mNDvL": "5001", "kaG4xf3I": "1"}]
            return [{"YWF08vZS": "20", "6uIYE15X": "101000100",
                     "Z20mNDvL": "5001"}]
        try:
            with patch("exvius_actions_shops._rows", side_effect=rows), patch(
                    "exvius_actions_shops._product",
                    return_value={"E61qF5Lp": "100"}), patch(
                    "exvius_actions_shops._reply", return_value={"success": True}), patch(
                    "exvius_actions_shops._rewards"), patch(
                    "exvius_actions_shops._pay") as pay, patch(
                    "exvius_actions_shops._grant") as grant:
                self.assertEqual(item_buy({}, selection), {"success": True})
                pay.assert_called_once_with(gil=200)
                grant.assert_called_once_with([{"kind": 20, "id": 101000100, "count": 2}])
        finally:
            State.player = original_player

    def test_catalogue_is_bundled_inside_android_zip(self):
        from build_historical_preview_apk import RESOURCE_FILES
        self.assertEqual(RESOURCE_FILES["content/historical_commerce.json"],
                         "source/server/content/historical_commerce.json")
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "app.imy"
            with ZipFile(archive, "w") as output:
                output.writestr("historical_commerce_ziptest.py",
                                (ROOT / "source/server/historical_progression.py").read_bytes())
                output.writestr("content/historical_commerce.json",
                                (ROOT / RESOURCE_FILES["content/historical_commerce.json"]).read_bytes())
            sys.path.insert(0, str(archive))
            try:
                module = importlib.import_module("historical_commerce_ziptest")
                self.assertEqual(module.historical_premium_bundle_ids(preview()), set())
            finally:
                sys.path.remove(str(archive))
                sys.modules.pop("historical_commerce_ziptest", None)
