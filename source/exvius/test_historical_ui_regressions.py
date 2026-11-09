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
    def _serve_historical_chambers(self, source_rows, month="2016-06"):
        # Reproduce the original native reply (Experience + late Fallen) and
        # verify the full downstream response, including artwork and tab IDs.
        from event_archive import events
        player = SimpleNamespace(data=marked(month), dirty=False)
        historic = events(player)
        mission_rows = [{"uv60hgDW": r["area"],
                         "U9iHsau3": r["first_dungeon"],
                         "qo3PECw6": r["first_mission"]}
                        for r in historic]
        with patch.object(ffbe_state.State, 'player', player), patch.object(
                ffbe_player, 'load_policy',
                side_effect=AssertionError("Endgame saved policy must not be consulted")), patch.object(
                ffbe_player, '_event_area_facts',
                side_effect=AssertionError("Historical archive already supplies its own masters")), patch.object(
                ffbe_player, '_load_mst_rows', return_value={"__rows__": mission_rows}), patch(
                'exvius_raid_progress.personal_event', return_value=None), patch.object(
                ffbe_player, 'apply_availability', side_effect=lambda spec, *_a, **_kw: spec), patch.object(
                ffbe_player, 'serve_switches', side_effect=lambda spec: spec):
            reply = ffbe_player.serve_event_gate(
                {'0xkoNP8U': source_rows}, ffbe_player.EVENT_GATE_CARRIERS[0])
        self.assertFalse(player.dirty)
        return reply

    def test_only_four_original_enhancement_chambers_reach_client(self):
        rows = [
            {'uv60hgDW': '226', 'qnUhs32P': '2',
             'U9iHsau3': '21104', 'qo3PECw6': '2110401'},
            {'uv60hgDW': '899', 'qnUhs32P': '3',
             'U9iHsau3': '89601', 'qo3PECw6': '8960101'},
            {'uv60hgDW': '990999', 'qnUhs32P': '1',
             'U9iHsau3': '99901', 'qo3PECw6': '9990101'},
        ]
        reply = self._serve_historical_chambers(rows)
        areas = {str(row["uv60hgDW"]) for row in reply['0xkoNP8U']}
        self.assertEqual(areas, {'216', '224', '225', '226'})
        self.assertTrue(all(row['qnUhs32P'] == '2'
                            for row in reply['0xkoNP8U']))
        art = {row['uv60hgDW']: row['4yT7FUqj']
               for row in reply['0xkoNP8U']}
        self.assertEqual(art, {
            '216': 'global_spd_bn_list_00216.png',
            '224': 'global_spd_bn_list_00224.png',
            '225': 'global_spd_bn_list_00225.png',
            '226': 'global_spd_bn_list_00226.png',
        })
        self.assertEqual([r['uv60hgDW'] for r in rows],
                         ['226', '899', '990999'])

    def test_old_saved_endgame_policy_does_not_reintroduce_tiles(self):
        # The same four chambers are served regardless of a stale endgame
        # policy. The source-stage test above rejects any load_policy call.
        result = self._serve_historical_chambers([
            {'uv60hgDW': '899', 'U9iHsau3': '89601',
             'qo3PECw6': '8960101'}], month="2016-07")
        self.assertEqual({r['uv60hgDW'] for r in result['0xkoNP8U']},
                         {'216', '224', '225', '226'})

    def test_native_archive_rejects_empty_era_fallback_and_tab_mutation(self):
        js = (ROOT / 'source/exvius/summon_menu.js').read_text()
        self.assertIn('(!eventHistorical && !eventAreas.size)', js)
        self.assertIn('if (eventHistorical ||', js)
        self.assertIn('historical_preview === true', js)

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
        self.assertEqual(months['2016-Jun']['banner'],
                         'daily_login_banner_dailylogin_00.png')
        self.assertEqual(months['2016-Jul']['banner'],
                         'daily_login_banner_dailylogin_00.png')
        self.assertTrue((ROOT / 'source/server/assets/banner_art' /
                         months['2016-Jun']['banner']).is_file())
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
