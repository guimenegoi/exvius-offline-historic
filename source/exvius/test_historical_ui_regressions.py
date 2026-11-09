"""Regressions from the first two on-device FFBE Global historic APK sessions."""
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'source/server'))
import ffbe_gacha
import ffbe_player
import ffbe_state
import historical_login_preview
from historical_summons import visible_banners
from player_state import PlayerState


def marked(month='2016-06'):
    return {'meta': {'historical_preview': True, 'historical_month': month}}


class HistoricalSummonUi(TestCase):
    def test_periods_and_native_tab_types(self):
        catalogue = json.loads((ROOT / 'source/server/gacha_catalogue.json').read_text())['banners']
        community = json.loads((ROOT / 'source/server/gacha_community.json').read_text())['banners']
        authored = json.loads((ROOT / 'source/server/gacha_authored.json').read_text())['banners']
        first = [b for b in catalogue if str(b['id']) in ('12', '18')]
        duplicates = [b for b in community if str(b['id']) in ('9100000', '9100001')]
        permanent = [b for b in authored if str(b['id']) in ('1', '9')]
        self.assertEqual(len(first), 2)
        self.assertEqual(len(duplicates), 2)
        self.assertEqual(len(permanent), 2)
        State = ffbe_state.State
        with patch.object(State, 'player', SimpleNamespace(data=marked('2016-06'))):
            june = visible_banners(first + duplicates + permanent, State.player)
            self.assertEqual({str(b['id']) for b in june}, {'1', '9'})
            self.assertEqual({b['id']: ffbe_gacha.gacha_type_code(b) for b in june},
                             {'1': 0, '9': 1})
            State.player.data['meta']['historical_month'] = '2016-07'
            july = visible_banners(first + duplicates + permanent, State.player)
            self.assertEqual({str(b['id']) for b in july}, {'1', '9', '12', '18'})
            self.assertEqual({b['id']: ffbe_gacha.gacha_type_code(b) for b in july},
                             {'1': 0, '9': 1, '12': 50, '18': 50})
            with patch.dict(os.environ, {'EXVIUS_SUMMON_ARCHIVE': '0'}):
                self.assertEqual(ffbe_gacha.gacha_type_code(first[0]), 50)

    def test_embedded_json_loader_does_not_need_real_filesystem(self):
        with patch.object(ffbe_gacha.os.path, 'isfile', return_value=False):
            authored = ffbe_gacha.authored_banners()
            self.assertTrue(any(str(b['id']) == '1' for b in authored))
            standard = ffbe_gacha.standard_banners()
            # Standard may be switched off by configured source mode.
            self.assertIsInstance(standard, list)


class HistoricalVortexUi(TestCase):
    def test_captured_2024_event_tiles_cannot_survive_empty_2016_archive(self):
        rows = [
            {'uv60hgDW': '226', 'U9iHsau3': '21104', 'qo3PECw6': '2110401'},
            {'uv60hgDW': '899', 'U9iHsau3': '89601', 'qo3PECw6': '8960101'},
            {'uv60hgDW': '990999', 'U9iHsau3': '99901', 'qo3PECw6': '9990101'},
        ]
        player = SimpleNamespace(data=marked(), dirty=False)
        with patch.object(ffbe_state.State, 'player', player), patch.object(
                ffbe_player, 'load_policy', return_value={
                    'version': 1, 'areas': [], 'permanent': True}):
            reply = ffbe_player.serve_event_gate(
                {'0xkoNP8U': rows}, ffbe_player.EVENT_GATE_CARRIERS[0])
        self.assertEqual([r['uv60hgDW'] for r in reply['0xkoNP8U']], ['226'])
        self.assertEqual([r['uv60hgDW'] for r in rows], ['226', '899', '990999'])
        self.assertFalse(player.dirty)

    def test_persisted_endgame_policy_cannot_readd_unreleased_tiles(self):
        rows = [
            {'uv60hgDW': '226', 'U9iHsau3': '21104', 'qo3PECw6': '2110401'},
            {'uv60hgDW': '899', 'U9iHsau3': '89601', 'qo3PECw6': '8960101'},
        ]
        player = SimpleNamespace(data=marked(), dirty=False)
        with patch.object(ffbe_state.State, 'player', player), patch.object(
                ffbe_player, 'load_policy', return_value={
                    'version': 1, 'areas': ['899', '970'], 'permanent': True}), patch.object(
                ffbe_player, '_event_area_facts', return_value=[]) as lookup:
            out = ffbe_player.serve_event_gate(
                {'0xkoNP8U': rows}, ffbe_player.EVENT_GATE_CARRIERS[0])
        lookup.assert_called_once_with([])
        self.assertEqual([r['uv60hgDW'] for r in out['0xkoNP8U']], ['226'])
        self.assertFalse(player.dirty)

    def test_late_survival_mode_does_not_add_2016_event_tiles(self):
        player = SimpleNamespace(data=marked(), dirty=False)
        with patch.object(ffbe_state.State, 'player', player):
            original = {'NsC8t4Qr': [{'future': True}]}
            result = ffbe_player.serve_survival(
                original, ffbe_player.SURVIVAL_CARRIERS[0])
            self.assertEqual(result['NsC8t4Qr'], [])
            self.assertEqual(original['NsC8t4Qr'], [{'future': True}])


class Original2016DailyLogin(TestCase):
    def test_28_historical_cells_and_currency_values(self):
        months = historical_login_preview.MONTHS
        self.assertEqual(set(months), {'2016-Jun', '2016-Jul'})
        for month in months.values():
            self.assertEqual(set(map(int, month['days'])), set(range(1, 29)))
        june = months['2016-Jun']['days']
        july = months['2016-Jul']['days']
        self.assertEqual((june['1']['type'], june['1']['count']), (30, 500))
        self.assertEqual((june['3']['type'], june['3']['count']), (51, 200))
        self.assertEqual((june['7']['type'], june['7']['count']), (50, 100))
        self.assertEqual((july['1']['type'], july['1']['count']), (50, 125))
        self.assertEqual((july['3']['type'], july['3']['count']), (30, 3000))
        self.assertEqual(july['2']['id'], 50)

    def test_calendar_and_mail_awarded_once_per_historical_month(self):
        p = PlayerState({
            **marked(), 'currencies': {'gil': 0, 'lapis_free': 0, 'lapis_paid': 0},
            'mailbox': [], 'login_bonus': {'month': '', 'day': 0, 'last_advance': ''},
        }, mode='live')
        with patch.object(ffbe_state.State, 'player', p), patch.object(
                ffbe_player.time, 'strftime', return_value='2026-11-09'), patch.object(
                p, 'record_archive', return_value=None):
            june = ffbe_player.serve_login_bonus({}, 'vw9RP3i4')
            self.assertEqual(len(june['f5bA4wFx']), 28)
            ffbe_player.deliver_login_mail(june, 'vw9RP3i4')
            ffbe_player.deliver_login_mail(june, 'vw9RP3i4')
            self.assertEqual(len(p.mailbox), 1)
            first = p.mailbox[0]['mail_id']
            self.assertEqual(p.receive_mail(first)[0]['kind'], 30)
            self.assertEqual(p.data['currencies']['gil'], 500)
            p.data['meta']['historical_month'] = '2016-07'
            july = ffbe_player.serve_login_bonus({}, 'vw9RP3i4')
            self.assertEqual(len(july['f5bA4wFx']), 28)
            ffbe_player.deliver_login_mail(july, 'vw9RP3i4')
            ffbe_player.deliver_login_mail(july, 'vw9RP3i4')
            self.assertEqual(len(p.mailbox), 2)
            second = p.mailbox[1]['mail_id']
            self.assertNotEqual(first, second)
            self.assertEqual(p.receive_mail(second)[0]['kind'], 50)
            self.assertEqual(p.data['currencies']['lapis_free'], 125)
            self.assertEqual(p.receive_mail(second), [])
