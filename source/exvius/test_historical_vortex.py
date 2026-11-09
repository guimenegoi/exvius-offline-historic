"""The historical Vortex menu must work in the zipped Android Python runtime."""
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'source/server'))
import event_archive


class HistoricalVortexTests(unittest.TestCase):
    def make_player(self, historical='2016-06', preview=True):
        return SimpleNamespace(data={
            'meta': {'historical_month': historical,
                     'historical_preview': preview},
        }, dirty=False)

    def test_archive_payload_loads_from_package_without_filesystem_assumptions(self):
        self.assertEqual(len(event_archive.document()['events']), 757)

    def test_first_two_months_do_not_expose_future_or_undated_archive(self):
        player = self.make_player('2016-06')
        self.assertEqual(set(event_archive.area_ids(player)), {'216', '224', '225', '226'})
        player.data['meta']['historical_month'] = '2016-07'
        self.assertEqual(set(event_archive.area_ids(player)), {'216', '224', '225', '226'})
        self.assertEqual(len(event_archive.events(self.make_player(preview=False))), 757)

    def test_date_selection_fails_closed_for_undated_and_later_rows(self):
        original = event_archive._DOCUMENT
        try:
            event_archive._DOCUMENT = {
                'events': [
                    {'area': '1', 'release': '2016-06-30'},
                    {'area': '2', 'release': '2016-07-08'},
                    {'area': '3', 'release': '2016-08-01'},
                    {'area': '4', 'release': None},
                ],
            }
            self.assertEqual(event_archive.area_ids(self.make_player('2016-06')), ['1'])
            self.assertEqual(event_archive.area_ids(self.make_player('2016-07')), ['1', '2'])
        finally:
            event_archive._DOCUMENT = original

    def test_empty_historical_menu_shows_filter_without_loading_clash(self):
        player = self.make_player()
        with patch('player_state._load_ndjson', return_value={}), patch(
                'exvius_fortuna.level_rewards',
                side_effect=AssertionError('Never load future Clash rewards in 2016')):
            menu = event_archive.menu(player)
        self.assertEqual(menu['selected']['id'], 'season1')
        self.assertEqual(set(menu['area_ids']), {'216', '224', '225', '226'})
        self.assertTrue(menu['historical_preview'])
        self.assertEqual(set(menu['selected']['ids']), {'216', '224', '225', '226'})
        self.assertEqual(menu['native_modes'], {})
        self.assertEqual(menu['selected']['count'], 0)
        self.assertEqual(len(menu['groups']), len(event_archive.GROUPS))
        self.assertFalse(player.dirty)


if __name__ == '__main__':
    unittest.main()
