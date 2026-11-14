"""Regression checks for the human-body rebuild and film deliverables."""
from pathlib import Path
import json
import subprocess
import unittest

import numpy as np
from PIL import Image, ImageStat
from scipy.ndimage import label

ROOT=Path(__file__).resolve().parent
ASSETS=ROOT/'assets_premium'
CAST=('dad','mom','boy','girl')
FLOWERS=('rose','sunflower','tulip','daisy','lily',
         'marigold','lotus','hibiscus','orchid','jasmine')


class PremiumMovieChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import premium_render
        cls.movie=premium_render

    def test_four_actors_are_connected_full_body_silhouettes(self):
        """A detached head would create a large separate alpha component."""
        for role in CAST:
            for pose in ('idle','walk','talk'):
                f=ASSETS/'actors'/f'{role}_{pose}.png'
                self.assertTrue(f.is_file(), f)
                with Image.open(f) as image:
                    alpha=np.asarray(image.getchannel('A'))>20
                self.assertGreater(int(alpha.sum()), 20000, f)
                components,count=label(alpha)
                totals=np.bincount(components.ravel())[1:]
                coherence=totals.max()/max(1,int(alpha.sum()))
                self.assertGreater(coherence,.995,
                                   f'{f.name}: silhouette incoherent ({coherence:.2%})')

    def test_parent_child_height_relationship(self):
        dims=self.movie.SIZES
        self.assertGreater(dims['dad'],dims['boy']*1.27)
        self.assertGreater(dims['mom'],dims['girl']*1.35)

    def test_all_botanical_species_present(self):
        self.assertEqual(tuple(x for x in self.movie.WORDS if x),FLOWERS)
        for flower in FLOWERS:
            f=ASSETS/'flowers'/f'{flower}.png'
            self.assertTrue(f.exists(),f)
            with Image.open(f) as image:
                self.assertGreater(image.width,240)
                self.assertGreater(image.height,380)

    def test_lotus_pond_is_not_under_any_actor_feet(self):
        # The pond occupies the right garden area; humans stand to its left.
        self.assertEqual(self.movie.WORDS[7],'lotus')
        self.assertLess(max(self.movie.MARKS[7].values()),810)
        self.assertGreater(self.movie.flower_placement(7,'lotus')[0],810)

    def test_story_timing_and_room_journey(self):
        self.assertEqual(self.movie.ROOMS,
                ('drawing_room',)*3+('kitchen',)*3+('balcony',)*3+('outside',)*3)
        lines=self.movie.LINES
        self.assertEqual(len(lines),36)
        self.assertEqual(len(set(r['speaker'] for r in lines)),4)
        self.assertTrue(all(0<=r['start']<r['end']<=120 for r in lines))

    def test_contact_frames_are_nonblack(self):
        preview=ROOT/'output/premium_qc_36_frames.jpg'
        self.assertTrue(preview.exists())
        image=Image.open(preview).convert('RGB')
        self.assertGreater(ImageStat.Stat(image).mean[0],60)

    def test_original_sound_and_foley_are_full_length(self):
        for file in ('narration_master.flac','premium_foley.wav'):
            f=ROOT/'audio'/file
            self.assertTrue(f.exists())
            raw=subprocess.check_output(['ffprobe','-v','error','-of','json',
                            '-show_entries','format=duration',str(f)])
            duration=float(json.loads(raw)['format']['duration'])
            self.assertAlmostEqual(duration,120.0,places=1)

    def test_rendered_video_is_120_sec_1080p_24_fps(self):
        p=ROOT/'output/Ten_Funny_Flowers_Premium_120s.mp4'
        self.assertTrue(p.exists(),p)
        raw=subprocess.check_output(['ffprobe','-v','error',
             '-show_entries','format=duration:stream=codec_name,width,height,avg_frame_rate',
             '-of','json',str(p)])
        data=json.loads(raw)
        self.assertAlmostEqual(float(data['format']['duration']),120,places=1)
        self.assertTrue(any(s.get('codec_name')=='h264' and
                            s.get('width')==1920 and s.get('height')==1080 and
                            s.get('avg_frame_rate')=='24/1'
                            for s in data['streams']))
        self.assertTrue(any(s.get('codec_name')=='aac' for s in data['streams']))


if __name__=='__main__':unittest.main()
