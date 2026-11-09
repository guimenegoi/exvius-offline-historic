"""Verify binary Android version upgrades preserve the rest of the manifest."""
from pathlib import Path
import sys
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/exvius'))
from build_historical_preview_apk import REPLACED, update_manifest_version_code


class ManifestVersionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ROOT / 'release/exvius-offline-v0.1.24.apk') as archive:
            cls.manifest = archive.read('AndroidManifest.xml')

    def test_version_can_increment_without_touching_package_or_application(self):
        new_manifest, old_code = update_manifest_version_code(self.manifest, 9066)
        self.assertEqual(old_code, 9064)
        self.assertEqual(len(new_manifest), len(self.manifest))
        self.assertEqual(sum(a != b for a, b in zip(new_manifest, self.manifest)), 1)
        # Only 9064 -> 9066 changes one byte in this particular manifest.
        _, new_code = update_manifest_version_code(new_manifest, 9067)
        self.assertEqual(new_code, 9066)

    def test_native_competition_action_gate_is_bundled(self):
        self.assertEqual(REPLACED.get("exvius_actions.pyc"),
                         "source/server/exvius_actions.py")
        self.assertEqual(REPLACED.get("exvius_colosseum.pyc"),
                         "source/server/exvius_colosseum.py")
        self.assertEqual(REPLACED.get("capture_server.pyc"),
                         "source/server/capture_server.py")

    def test_event_battle_transaction_guards_are_included_in_preview_apk(self):
        # A source-only historical gate is not effective if the original
        # app.imy still imports its older exvius_repeat/actions_modes bytecode.
        for module in ("event_archive", "exvius_repeat", "exvius_actions_modes"):
            self.assertEqual(REPLACED.get(module + ".pyc"),
                             "source/server/" + module + ".py")
        with ZipFile(ROOT / 'release/exvius-offline-v0.1.24.apk') as source:
            from io import BytesIO
            with ZipFile(BytesIO(source.read('assets/chaquopy/app.imy'))) as python:
                self.assertTrue(all(module + ".pyc" in python.namelist()
                                    for module in ("event_archive", "exvius_repeat",
                                                   "exvius_actions_modes")))

    def test_invalid_versions_fail_closed(self):
        for code in (0, 9064, 9000, -1, 2 ** 31):
            with self.subTest(code=code), self.assertRaises(ValueError):
                update_manifest_version_code(self.manifest, code)
        with self.assertRaises(ValueError):
            update_manifest_version_code(b'not Android XML', 9066)


if __name__ == '__main__':
    unittest.main()
