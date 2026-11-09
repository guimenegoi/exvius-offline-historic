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


class HistoricHomeNative(TestCase):
    def test_vision_card_ornament_guard_uses_server_feature(self):
        js = (ROOT / 'source/exvius/home_carousel.js').read_text()
        self.assertIn("'_ZN9HomeScene21setOrnamentVisionCard", js)
        self.assertIn("'_ZN9HomeScene25setNoneOrnamentVisionCard", js)
        self.assertIn("features && features.vision_cards !== true", js)
        self.assertIn("Interceptor.replaceFast", js)

    def test_native_orb_vector_uses_owned_maximum_not_ten_slots(self):
        js = (ROOT / 'source/exvius/home_carousel.js').read_text()
        self.assertIn("Math.min(10, currentOrbs(card)?.maximum || 10)", js)
        self.assertIn("Array.from({length: maximum}", js)
        self.assertIn("data.add(maximum * Process.pointerSize)", js)
        self.assertIn('if (features && features.arena === false) visible(card.orbNodes[0], 0)', js)


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
            '216': 'event_216.png',
            '224': 'event_224.png',
            '225': 'event_225.png',
            '226': 'event_226.png',
        })
        self.assertEqual([r['uv60hgDW'] for r in rows],
                         ['226', '899', '990999'])

    def test_four_pinned_chamber_art_resources(self):
        import hashlib
        from PIL import Image
        from build_historical_preview_apk import RESOURCE_FILES
        records = json.loads((ROOT / 'source/server/event_art.json').read_text())['events']
        for area in ('216', '224', '225', '226'):
            entry = records[area]
            name = 'event_' + area + '.png'
            self.assertEqual(entry['filename'], name)
            self.assertEqual(entry['size'], [640, 240])
            self.assertTrue(entry['source_url'].startswith(
                'https://static.wikia.nocookie.net/exvius_gamepedia_en/'))
            self.assertEqual(RESOURCE_FILES['assets/area_art/' + name],
                             entry['runtime_file'])
            source, runtime = ROOT / entry['source_file'], ROOT / entry['runtime_file']
            if not source.is_file() or not runtime.is_file():
                continue  # licensed third-party source images are not tracked in Git
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),
                             entry['source_sha256'])
            self.assertEqual(hashlib.sha256(runtime.read_bytes()).hexdigest(),
                             entry['runtime_sha256'])
            with Image.open(source) as original, Image.open(runtime) as conversion:
                self.assertEqual(conversion.size, (640, 240))
                self.assertEqual(original.convert('RGBA').tobytes(),
                                 conversion.convert('RGBA').tobytes())

    def test_historical_native_cdn_fallback_for_bundled_original_art(self):
        import io
        import pkgutil
        import capture_server
        def attempt(state):
            output = io.BytesIO()
            handler = capture_server.Handler.__new__(capture_server.Handler)
            handler.command = 'GET'
            handler.path = '/en/sd/area/event_216.png'
            handler.request_version = 'HTTP/1.1'
            handler.requestline = 'GET /en/sd/area/event_216.png HTTP/1.1'
            handler.headers = {'Host': 'local-test'}
            handler.wfile = output
            handler.close_connection = True
            with patch.object(capture_server.State, 'player', state), patch.object(
                    capture_server.State, 'cdn_overlay', '/no-such-overlay'), patch.object(
                    capture_server.State, 'cdn_root', '/no-such-data'), patch.object(
                    capture_server, 'area_art_index', return_value={}), patch.object(
                    capture_server, 'banner_art_index', return_value={}), patch.object(
                    pkgutil, 'get_data', return_value=b'test-original-image') as embedded:
                handler._cdn_fetch()
            return output.getvalue(), embedded
        historical, lookup = attempt(SimpleNamespace(data=marked()))
        self.assertIn(b'200 OK', historical)
        self.assertTrue(historical.endswith(b'test-original-image'))
        lookup.assert_called_once_with('capture_server', 'assets/area_art/event_216.png')
        modern, lookup = attempt(SimpleNamespace(data={'meta': {}}))
        self.assertIn(b'404', modern)
        lookup.assert_not_called()

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
        self.assertIn('if (eventHistorical) {', js)
        self.assertIn("'void', ['pointer', 'long', 'bool']", js)
        # Frida requires a numeric native bool; passing JS true throws.
        self.assertIn('removeAreaAt(list, remove[i], 1)', js)
        self.assertIn('LOCAL_HISTORIC_GATE_LIST allowed=', js)
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
