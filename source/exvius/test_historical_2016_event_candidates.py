"""Original Global event dates are not approval to reuse 2017 rerun missions."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


class Historical2016EventCandidatesTests(unittest.TestCase):
    def test_every_candidate_is_research_only_and_is_a_later_archive(self):
        root = ROOT / 'source/server'
        candidates = json.loads((root / 'content/historical_2016_event_candidates.json').read_text())
        events = {str(e['area']): e for e in json.loads((root / 'event_archive.json').read_text())['events']}
        self.assertEqual(candidates['region'], 'GL')
        self.assertEqual(candidates['purpose'], 'research_only_not_imported_by_runtime')
        self.assertEqual(len(candidates['candidates']), 5)
        for entry in candidates['candidates']:
            self.assertEqual(entry['status'], 'original_identity_unverified_do_not_unlock')
            self.assertTrue(entry['source'].startswith('https://'))
            self.assertTrue(entry['global_first_release'].startswith('2016-'))
            self.assertTrue(entry['blocking_evidence'])
            for candidate in entry['archived_area_candidates']:
                original = events[candidate['area']]
                self.assertEqual(original['release'], candidate['archive_release'])
                self.assertGreater(original['release'], entry['global_first_release'])
                self.assertEqual(original['name'], entry['event'])
                self.assertEqual(original['missions'], candidate['archive_missions'])
                self.assertTrue(original['release'].startswith('2017'))

    def test_archive_still_does_not_unlock_2016_reruns(self):
        root = ROOT / 'source/server'
        events = json.loads((root / 'event_archive.json').read_text())['events']
        self.assertFalse(any(str(e.get('release') or '').startswith('2016') for e in events))


if __name__ == '__main__':
    unittest.main()
