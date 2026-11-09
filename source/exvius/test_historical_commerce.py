"""The original Global shop route must not charge unverified future stock."""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile
import importlib
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch, Mock
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / "source/server"))

from historical_progression import (historical_commerce_catalogue,
                                    historical_town_purchase_allowed)
from exvius_actions_shops import item_buy
from ffbe_state import State


def preview(month="2016-06"):
    return {"meta": {"historical_preview": True, "historical_month": month}}


class HistoricalCommerceTests(TestCase):
    def test_inventory_is_global_and_provenanced(self):
        catalogue = historical_commerce_catalogue()
        self.assertEqual(catalogue["schema"], 1)
        self.assertEqual(catalogue["region"], "GL")
        self.assertEqual(len(catalogue["town_stock"]), 1)
        self.assertEqual(catalogue["limited_bundles"], [])
        self.assertEqual(catalogue["unit_awakening_steps"], [])
        for entry in catalogue["town_stock"]:
            self.assertTrue(entry["source"].startswith("https://"))
            self.assertGreater(entry["price_gil"], 0)

    def test_period_town_and_price_filter(self):
        potion = {"kind": 20, "id": "101000100", "price_gil": 100}
        self.assertTrue(historical_town_purchase_allowed(preview(), 1101, [potion]))
        self.assertTrue(historical_town_purchase_allowed(preview("2016-07"), 1101, [potion]))
        for town, basket in (
            (1102, [potion]),
            (1101, [{"kind": 20, "id": "999999", "price_gil": 100}]),
            (1101, [{"kind": 20, "id": "101000100", "price_gil": 101}]),
            (1101, [potion, {"kind": 21, "id": "999999", "price_gil": 1}]),
            (1101, []),
        ):
            with self.subTest(town=town, basket=basket):
                self.assertFalse(historical_town_purchase_allowed(preview(), town, basket))
        self.assertTrue(historical_town_purchase_allowed({"meta": {}}, 1101,
                                                          [{"kind": 20, "id": "999", "price_gil": 1}]))
        with self.assertRaises(ValueError):
            historical_town_purchase_allowed(preview("not-a-month"), 1101, [potion])

    def test_resource_loader_and_apk_overlay_contract(self):
        # APK embeds resources inside app.imy, not the server filesystem.
        sys.path.insert(0, str(ROOT / "source/exvius"))
        from build_historical_preview_apk import RESOURCE_FILES
        self.assertEqual(RESOURCE_FILES["content/historical_commerce.json"],
                         "source/server/content/historical_commerce.json")
        with TemporaryDirectory() as directory:
            archive = Path(directory) / "app.imy"
            with ZipFile(archive, "w") as output:
                output.writestr("historical_economy_ziptest.py",
                                (ROOT / "source/server/historical_progression.py").read_bytes())
                output.writestr("content/historical_commerce.json",
                                (ROOT / RESOURCE_FILES["content/historical_commerce.json"]).read_bytes())
            sys.path.insert(0, str(archive))
            try:
                module = importlib.import_module("historical_economy_ziptest")
                self.assertTrue(module.historical_town_purchase_allowed(
                    preview(), 1101, [{"kind": 20, "id": "101000100", "price_gil": 100}]))
            finally:
                sys.path.remove(str(archive))
                sys.modules.pop("historical_economy_ziptest", None)

    def test_original_item_buy_rejects_unknown_basket_before_payment(self):
        original_player = State.player
        player = SimpleNamespace(data=preview(), mode="live", dirty=False)
        State.player = player
        buy = {"2aciVI9Y": [{"Gh92V3Tx": 1101, "j9NS0H15": "20:999999999:1",
                              "U1uaXph4": 100}]}
        def rows(name):
            return ([{"Gh92V3Tx": "1101", "Z20mNDvL": "5001", "kaG4xf3I": "1"}]
                    if name == "F_TOWN_STORE_MST" else
                    [{"YWF08vZS": "20", "6uIYE15X": "999999999", "Z20mNDvL": "5001"}])
        try:
            with patch("exvius_actions_shops._rows", side_effect=rows), patch(
                    "exvius_actions_shops._product", return_value={"E61qF5Lp": "100"}), patch(
                    "exvius_actions_shops._reply", return_value={}), patch(
                    "exvius_actions_shops._pay") as pay, patch(
                    "exvius_actions_shops._grant") as grant:
                self.assertEqual(item_buy({}, buy), {})
                pay.assert_not_called()
                grant.assert_not_called()
                self.assertEqual(player.data, preview())
                self.assertFalse(player.dirty)
        finally:
            State.player = original_player

    def test_original_item_buy_allows_audited_potion_with_upstream_route(self):
        original_player = State.player
        player = SimpleNamespace(data=preview(), mode="live", dirty=False)
        State.player = player
        buy = {"2aciVI9Y": [{"Gh92V3Tx": 1101, "j9NS0H15": "20:101000100:2",
                              "U1uaXph4": 200}]}
        def rows(name):
            return ([{"Gh92V3Tx": "1101", "Z20mNDvL": "5001", "kaG4xf3I": "1"}]
                    if name == "F_TOWN_STORE_MST" else
                    [{"YWF08vZS": "20", "6uIYE15X": "101000100", "Z20mNDvL": "5001"}])
        try:
            with patch("exvius_actions_shops._rows", side_effect=rows), patch(
                    "exvius_actions_shops._product", return_value={"E61qF5Lp": "100"}), patch(
                    "exvius_actions_shops._reply", return_value={"done": True}), patch(
                    "exvius_actions_shops._rewards"), patch(
                    "exvius_actions_shops._pay") as pay, patch(
                    "exvius_actions_shops._grant") as grant:
                self.assertEqual(item_buy({}, buy), {"done": True})
                pay.assert_called_once_with(gil=200)
                grant.assert_called_once_with([{"kind": 20, "id": 101000100, "count": 2}])
        finally:
            State.player = original_player
