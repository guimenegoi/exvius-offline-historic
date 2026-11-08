"""Offline tests of HTTP-range ZIP index and member checksums."""
from io import BytesIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_historical_tables import FILES, central_directory, extract_entry, fetch_selected


class ZipRangeTests(unittest.TestCase):
    def setUp(self):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(FILES[0], b'{"unit_id": "100004604"}\n')
            z.writestr(FILES[1], b'{"name": "Chizuru"}\n')
        self.content = buffer.getvalue()
        self.requests = []

    def part(self, start, end):
        self.requests.append((start, end))
        return self.content[start:end + 1]

    def test_range_index_reads_only_selected_members(self):
        idx = central_directory(len(self.content), self.part)
        self.assertEqual(set(idx), set(FILES))
        self.assertEqual(extract_entry(idx[FILES[0]], self.part),
                         b'{"unit_id": "100004604"}\n')

    def test_member_crc_detects_corruption(self):
        index = central_directory(len(self.content), self.part)
        header = dict(index[FILES[0]], crc=0)
        with self.assertRaisesRegex(ValueError, "CRC"):
            extract_entry(header, self.part)

    def test_extraction_is_reusable_and_local(self):
        manifest = {"packs": [{"id": "data-001", "url": "https://test.invalid/pack.zip",
                               "size": len(self.content)}]}
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            first = fetch_selected(manifest, root, lambda url, a, b: self.part(a, b))
            self.assertEqual(len(first), 2)
            self.assertFalse(first[FILES[0]]["reused"])
            second = fetch_selected(manifest, root, lambda url, a, b: self.part(a, b))
            self.assertTrue(second[FILES[0]]["reused"])
            self.assertEqual((root / FILES[1].removeprefix("static/")).read_bytes(),
                             b'{"name": "Chizuru"}\n')

    def test_missing_master_fails_closed(self):
        manifest = {"packs": [{"id": "data-001", "url": "https://test.invalid/pack.zip",
                               "size": len(self.content)}]}
        bad = dict(manifest)
        bad["packs"] = []
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "data-001"):
                fetch_selected(bad, Path(td))


if __name__ == "__main__":
    unittest.main()
