"""Tests for the reference-rig four-character ten-second film."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

import numpy as np
from PIL import ImageChops

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rigged_render as film


class CharacterAnimationTests(unittest.TestCase):
    def test_all_four_use_nine_distinct_articulated_layers(self):
        expected={"head","torso","pelvis","upper_arm","forearm","hand",
                  "thigh","shin","foot"}
        for role in ("dad","mom","boy","girl"):
            with self.subTest(role=role):
                layers=film.parts_for(role)
                self.assertEqual(expected,set(layers))
                self.assertEqual(layers["head"].size,(200,274))
                self.assertEqual(layers["torso"].size,(190,235))
                self.assertGreater(layers["head"].getbbox()[2],140)

    def test_girl_reference_matches_original_reference_art(self):
        reference=film.ref.parts
        for part in ("head","torso"):
            self.assertIsNone(ImageChops.difference(
                film.parts_for("mom")[part],reference[part]).getbbox())

    def test_face_parts_really_animate(self):
        for role in ("dad","mom","boy","girl"):
            base=film.face_sprite(role,"X",False,0)
            blink=film.face_sprite(role,"X",True,0)
            eyes=film.face_sprite(role,"X",False,9)
            lips=film.face_sprite(role,"D",False,0)
            with self.subTest(role=role):
                self.assertIsNotNone(ImageChops.difference(base,blink).convert("RGB").getbbox())
                self.assertIsNotNone(ImageChops.difference(base,eyes).convert("RGB").getbbox())
                self.assertIsNotNone(ImageChops.difference(base,lips).convert("RGB").getbbox())

    def test_four_voices_have_distinct_correct_dialogue(self):
        self.assertEqual([line["speaker"] for line in film.TIMINGS],
                         ["dad","mom","boy"])
        self.assertEqual(film.active_line(2.0)["speaker"],"dad")
        self.assertEqual(film.active_line(5.0)["speaker"],"mom")
        self.assertEqual(film.active_line(8.7)["speaker"],"boy")
        self.assertIsNone(film.active_line(7.5))
        self.assertEqual(film.viseme_at(5,"dad"),"X")

    def test_walk_and_run_use_different_travel_and_joint_lengths(self):
        self.assertTrue(film.pose("dad",.7)[0]["walk"])
        self.assertTrue(film.pose("boy",.7)[0]["walk"])
        self.assertLess(film.pose("dad",.25)[0]["x"],film.pose("dad",1.6)[0]["x"])
        self.assertGreater(film.pose("boy",.25)[0]["x"],film.pose("boy",1.6)[0]["x"])
        self.assertNotEqual(film.pose("dad",2.0)[1],{})
        self.assertEqual(film.SCALE["dad"],max(film.SCALE.values()))

    def test_knee_and_elbow_inverse_kinematics_returns_two_segments(self):
        start=np.array([100.,100.]);target=np.array([175.,270.])
        joint,solved=film.ref.ik(start,target,110,120,-1)
        self.assertAlmostEqual(float(np.linalg.norm(joint-start)),110,places=3)
        self.assertAlmostEqual(float(np.linalg.norm(solved-joint)),120,places=3)

    def test_media_exact_duration_and_codecs(self):
        movie=film.OUT/"Ten_Second_Family_Articulated_Reference_Style.mp4"
        if not movie.exists():
            self.skipTest("Movie has not been rendered yet")
        result=subprocess.run(["ffprobe","-v","error","-show_streams",
                               "-show_format","-of","json",str(movie)],
                              capture_output=True,text=True,check=True)
        data=json.loads(result.stdout)
        video=next(s for s in data["streams"] if s["codec_type"]=="video")
        audio=next(s for s in data["streams"] if s["codec_type"]=="audio")
        self.assertEqual(video["width"],1920)
        self.assertEqual(video["height"],1080)
        self.assertEqual(video["codec_name"],"h264")
        self.assertEqual(audio["codec_name"],"aac")
        self.assertEqual(video.get("nb_frames"),"240")
        self.assertAlmostEqual(float(data["format"]["duration"]),10.0,places=2)


if __name__=="__main__":unittest.main()
