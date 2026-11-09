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

    def test_released_event_can_still_require_account_maturity(self):
        original = event_archive._DOCUMENT
        late = {
            'area': '9001', 'release': '2016-07-08',
            'account_requirements': {
                'source': 'https://example.org/verified-original-event-rank',
                'minimum_rank': 10, 'cleared_missions': ['1110101']}}
        try:
            event_archive._DOCUMENT = {'events': [
                {'area': '9000', 'release': '2016-06-30'},
                late, {'area': '9002', 'release': None}]}
            player = self.make_player('2016-06')
            player.data['rank'] = {'level': 1}
            player.data['progress'] = {'cleared_missions': []}
            self.assertEqual(event_archive.area_ids(player), ['9000'])
            player.data['meta']['historical_month'] = '2016-07'
            self.assertEqual(event_archive.area_ids(player), ['9000'])
            player.data['rank']['level'] = 10
            self.assertEqual(event_archive.area_ids(player), ['9000'])
            player.data['progress']['cleared_missions'].append('1110101')
            self.assertEqual(event_archive.area_ids(player), ['9000', '9001'])
            player.data['meta']['historical_month'] = '2016-08'
            self.assertEqual(event_archive.area_ids(player), ['9000', '9001'])
            self.assertFalse(player.dirty)
            self.assertEqual(player.data['rank']['level'], 10)
            legacy = self.make_player(preview=False)
            self.assertEqual(event_archive.area_ids(legacy), ['9000', '9001', '9002'])
        finally:
            event_archive._DOCUMENT = original

    def test_battle_attempt_and_event_list_share_original_release_policy(self):
        from copy import deepcopy
        from exvius_repeat import begin_attempt, claim_mission_rewards, complete_attempt
        player = self.make_player('2016-06')
        player.mode = 'live'
        future = '2220101'  # area 222: Global May 12, 2017
        initial = deepcopy(player.data)
        self.assertFalse(event_archive.mission_available(player, future))
        self.assertFalse(begin_attempt(player, future))
        self.assertFalse(claim_mission_rewards(player, future))
        self.assertEqual(complete_attempt(player, future, True, [], {}, {})['reason'],
                         'no pending mission load')
        self.assertEqual(player.data, initial)
        self.assertFalse(player.dirty)
        # Known, authentic 2016 chambers and ordinary story missions are not
        # collateral damage from the event-only archive check.
        self.assertTrue(event_archive.mission_available(player, '2111001'))
        self.assertTrue(event_archive.mission_available(player, '1110101'))
        self.assertTrue(begin_attempt(player, '2111001'))
        self.assertTrue(player.dirty)
        # Introduction alone is enough for catalogue availability when no
        # extra, sourced original-account requirement is declared.
        player.data['meta']['historical_month'] = '2017-05'
        self.assertTrue(event_archive.mission_available(player, future))
        self.assertTrue(begin_attempt(player, future))
        player.data['meta']['historical_month'] = '2024-10'
        self.assertTrue(event_archive.mission_available(player, future))
        # Ordinary offline saves never inherit the historical date denial.
        legacy = self.make_player(preview=False)
        legacy.mode = 'live'
        self.assertTrue(begin_attempt(legacy, future))

    def test_maturity_blocks_both_direct_load_and_mode_precharge(self):
        from copy import deepcopy
        from exvius_repeat import begin_attempt
        from exvius_actions_modes import _begin, _Refused
        from ffbe_state import State
        original_document = event_archive._DOCUMENT
        original_player = State.player
        player = self.make_player('2016-07')
        player.mode = 'live'
        player.data['rank'] = {'level': 1, 'nrg': 100}
        player.data['progress'] = {'cleared_missions': []}
        condition = {'source': 'https://example.org/audited-global-event-requirement',
                     'minimum_rank': 10, 'cleared_missions': ['1110101']}
        try:
            event_archive._DOCUMENT = {'events': [{
                'area': '9991', 'missions': ['99910101'],
                'release': '2016-07-08', 'account_requirements': condition}]}
            State.player = player
            snapshot = deepcopy(player.data)
            self.assertFalse(begin_attempt(player, '99910101'))
            # Special native modes charge NRG/orbs before their attempt is
            # registered. The shared guard must refuse before that charge.
            with patch('exvius_actions_modes._cost',
                       side_effect=AssertionError('A locked event must not charge NRG')):
                with self.assertRaises(_Refused):
                    _begin('tower', {}, {'qo3PECw6': '99910101'}, {})
            self.assertEqual(player.data, snapshot)
            self.assertFalse(player.dirty)
            player.data['rank']['level'] = 10
            self.assertFalse(begin_attempt(player, '99910101'))
            player.data['progress']['cleared_missions'] = ['1110101']
            self.assertTrue(begin_attempt(player, '99910101'))
        finally:
            event_archive._DOCUMENT = original_document
            State.player = original_player

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
