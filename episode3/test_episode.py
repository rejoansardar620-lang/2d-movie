"""Quick invariants for the new educational episode."""
from pathlib import Path
import json
import subprocess
import unittest

HERE=Path(__file__).resolve().parent
STORY=json.loads((HERE/'story.json').read_text())


class FlowerLessonTests(unittest.TestCase):
    def test_exactly_ten_flower_names(self):
        flowers=[scene['flower'] for scene in STORY['scenes'] if scene['flower']]
        self.assertEqual(flowers,['rose','sunflower','tulip','daisy','lily',
                                  'marigold','lotus','hibiscus','orchid','jasmine'])

    def test_four_characters_12_scenes_36_lines(self):
        self.assertEqual(len(STORY['characters']),4)
        self.assertEqual(len(STORY['scenes']),12)
        lines=[line for scene in STORY['scenes'] for line in scene['lines']]
        self.assertEqual(len(lines),36)
        self.assertEqual({who for who,_ in lines},set(STORY['characters']))

    def test_audio_and_captions_cover_two_minutes(self):
        timeline=json.loads((HERE/'timings.json').read_text())
        self.assertEqual(len(timeline),36)
        self.assertTrue((HERE/'captions.srt').exists())
        for line in timeline:
            i=line['scene']
            self.assertGreaterEqual(line['start'],i*10)
            self.assertLessEqual(line['end'],(i+1)*10)
            self.assertLess(line['start'],line['end'])
        self.assertEqual(STORY['duration'],120)

    def test_final_video_when_present(self):
        mp4=HERE/'output/Ten_Funny_Flowers_120s.mp4'
        if not mp4.is_file():
            self.skipTest('Video not rendered yet')
        p=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                          '-of','default=noprint_wrappers=1:nokey=1',str(mp4)],
                         capture_output=True,text=True,check=True)
        self.assertAlmostEqual(float(p.stdout.strip()),120.0,places=1)


if __name__=='__main__':
    unittest.main()
