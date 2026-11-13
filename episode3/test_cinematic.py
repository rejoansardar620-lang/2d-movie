"""Fast, entirely offline checks for the two-minute four-room family movie."""
from pathlib import Path
import json
import subprocess
import unittest

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


class CinematicFilmChecks(unittest.TestCase):
    def test_four_locations_in_strict_order(self):
        import cinematic_render as movie
        self.assertEqual([scene[0] for scene in movie.PLAN],
                         ['drawing_room'] * 3 + ['kitchen'] * 3 +
                         ['balcony'] * 3 + ['outside'] * 3)
        self.assertEqual(len(movie.PLAN), 12)

    def test_four_speakers_ten_unique_flowers(self):
        story = json.loads((ROOT / 'story.json').read_text())
        self.assertEqual(set(story['characters']), {'dad', 'mom', 'boy', 'girl'})
        flower_names = [scene['flower'] for scene in story['scenes'] if scene['flower']]
        self.assertEqual(len(flower_names), 10)
        self.assertEqual(len(set(flower_names)), 10)
        self.assertEqual(len(story['scenes']), 12)
        self.assertEqual(sum(len(scene['lines']) for scene in story['scenes']), 36)

    def test_aligned_speech_and_phonemes(self):
        lines = json.loads((ROOT / 'timings.json').read_text())
        cues = json.loads((ROOT / 'audio/rhubarb_cues.json').read_text())['mouthCues']
        self.assertEqual(len(lines), 36)
        self.assertGreater(len(cues), 500)
        self.assertTrue(all(0 <= line['start'] < line['end'] <= 120 for line in lines))
        self.assertTrue(all(0 <= cue['start'] < cue['end'] <= 120 for cue in cues))

    def test_exported_godot_rig_assets(self):
        parts = {'head', 'torso', 'pelvis', 'thigh', 'shin', 'foot',
                 'upper_arm', 'forearm', 'hand'}
        for actor in ('dad', 'mom', 'boy', 'girl'):
            for part in parts:
                self.assertTrue((REPO / 'godot_movie/assets/characters' / actor /
                                 f'{part}.png').is_file())
        for room in ('drawing_room', 'kitchen', 'balcony', 'outside'):
            self.assertTrue((REPO / 'godot_movie/assets/backgrounds' /
                             f'{room}.png').is_file())

    def test_final_movie_container(self):
        mp4 = ROOT / 'output/Ten_Funny_Flowers_Cinematic_120s.mp4'
        self.assertTrue(mp4.is_file())
        result = subprocess.check_output(['ffprobe', '-v', 'error',
              '-show_entries', 'stream=codec_name,width,height,avg_frame_rate:format=duration',
              '-of', 'json', str(mp4)])
        info = json.loads(result)
        self.assertAlmostEqual(float(info['format']['duration']), 120.0, places=1)
        self.assertTrue(any(s.get('codec_name') == 'h264' and
                            s.get('width') == 1920 and s.get('height') == 1080 and
                            s.get('avg_frame_rate') == '24/1'
                            for s in info['streams']))
        self.assertTrue(any(s.get('codec_name') == 'aac' for s in info['streams']))


if __name__ == '__main__':
    unittest.main()
