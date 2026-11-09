"""Contracts for the early Global Home shell: source assets are NOT a UI snapshot."""
import os
import tempfile
import unittest
from pathlib import Path

from preview_historical_home_shell import frame_rectangle, parse_layout, render_common_shell


class HistoricalHomeShellTests(unittest.TestCase):
    def test_original_footer_csv_coordinates_and_order(self):
        original = (
            b'0,841,640,44,0,ticker_area,mypage_under_ticker.png,\r\n'
            b'0,884,640,104,0,footer_bg,mypage_under_bg.png,\r\n'
            b'-5,868,120,120,0,footer_home,mypage_btn_home1.png,\r\n'
            b'101,868,120,120,0,footer_unit,mypage_btn_unit1.png,\r\n'
            b'207,868,120,120,0,footer_item,mypage_btn_item1.png,\r\n'
            b'313,868,120,120,0,footer_shop,mypage_btn_shop1.png,\r\n'
            b'419,868,120,120,0,footer_gacha,mypage_btn_gacha1.png,\r\n'
            b'525,868,120,120,0,footer_friend,mypage_btn_friend1.png,\r\n'
        )
        rows = parse_layout(original)
        self.assertEqual(len(rows), 8)
        self.assertEqual(rows[2].x, -5)
        self.assertEqual([r.label for r in rows[2:]], [
            "footer_home", "footer_unit", "footer_item", "footer_shop",
            "footer_gacha", "footer_friend",
        ])
        self.assertEqual([r.x for r in rows[2:]], [-5, 101, 207, 313, 419, 525])

    def test_rejects_duplicate_original_controls_and_invalid_geometry(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            parse_layout(b'0,1,10,10,0,footer_home,x.png,\n'
                         b'1,1,10,10,0,footer_home,y.png,\n')
        with self.assertRaisesRegex(ValueError, "Invalid"):
            parse_layout(b'0,1,-10,10,0,footer_home,x.png,\n')

    def test_both_original_plist_notations(self):
        self.assertEqual(frame_rectangle({
            "frame": "{{2,154},{120,120}}", "rotated": False}), (2,154,120,120))
        self.assertEqual(frame_rectangle({
            "textureRect": "{{562,888},{32,32}}",
            "textureRotated": False}), (562,888,32,32))
        with self.assertRaisesRegex(ValueError, "Rotated"):
            frame_rectangle({"frame": "{{0,0},{10,12}}", "rotated": True})

    def test_refuses_unverified_or_unsupported_client_before_rendering(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "GL-2.0.0-2017-02.apk"
            file.write_bytes(b"test")
            with self.assertRaisesRegex(ValueError, "Only verified"):
                render_common_shell(file, 1024, Path(directory) / "output.png")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                render_common_shell(file, 1080, Path(directory) / "output.png")

    @unittest.skipUnless(os.environ.get("FFBE_HISTORIC_APK"), "Original signed APK integration")
    def test_actual_2016_era_atlas_and_layout_are_verified(self):
        # Run with PYTHONPATH=<test-only CriCodecs/Pillow> and FFBE_HISTORIC_APK.
        apk = Path(os.environ["FFBE_HISTORIC_APK"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "shell.png"
            report = render_common_shell(apk, 1024, output)
            from PIL import Image
            with Image.open(output) as image:
                self.assertEqual(image.size, (640, 1024))
                self.assertEqual(image.getpixel((320, 420))[3], 0)
                self.assertNotEqual(image.getpixel((320, 20))[3], 0)
                self.assertNotEqual(image.getpixel((320, 960))[3], 0)
            controls = {row["control"]: row["rect"]
                        for row in report["rendered_controls"]}
            self.assertEqual(controls["footer_shop"], [313,868,120,120])
            self.assertEqual(controls["footer_friend"], [525,868,120,120])
            self.assertEqual(len(controls), 17)
            self.assertFalse(report["layout_verified"])
            self.assertFalse(report["global_english_localization_verified"])
            self.assertFalse(report["header_variant_runtime_verified"])
            self.assertIsNone(report["header_variant_selected_by_original_client"])
            self.assertEqual(report["header_variant_used_for_static_preview"], "common")
            comparisons = report["header_layout_candidate_comparison"]
            self.assertEqual(len(comparisons), 2)
            self.assertEqual(
                [row["control"] for row in comparisons[0]["differences"]],
                ["header_stamina_info", "header_stamina_time"])
            self.assertEqual(comparisons[0]["differences"][0]["common"], [61, 79, 92, 19])
            self.assertEqual(comparisons[0]["differences"][0]["pretutorial"], [19, 79, 145, 19])
            self.assertEqual(
                [row["control"] for row in comparisons[1]["differences"]],
                ["sub_header_label"])
            self.assertEqual(report["source_version"], "1.2.0")
            with self.assertRaises(FileExistsError):
                render_common_shell(apk, 1024, output)


if __name__ == "__main__":
    unittest.main()
