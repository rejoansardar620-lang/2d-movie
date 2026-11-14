"""Automated, objective acceptance checks for the 10-second motion pilot."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import render
from face_rig import FEATURES


class PilotChecks(unittest.TestCase):
    def test_exact_ten_second_fullhd_h264_aac(self):
        path=HERE/"output"/"Ten_Second_Animated_Family_Pilot.mp4"
        self.assertTrue(path.is_file())
        info=json.loads(subprocess.check_output([
            "ffprobe","-v","error","-show_entries","format=duration",
            "-show_entries","stream=codec_name,width,height,avg_frame_rate,nb_frames",
            "-of","json",str(path)],text=True))
        self.assertAlmostEqual(float(info["format"]["duration"]),10,places=3)
        video=next(s for s in info["streams"] if s["codec_name"]=="h264")
        self.assertEqual((video["width"],video["height"]),(1920,1080))
        self.assertEqual(video["avg_frame_rate"],"24/1")
        self.assertEqual(int(video["nb_frames"]),240)
        self.assertIn("aac",[s["codec_name"] for s in info["streams"]])

    def test_four_distinct_source_identities(self):
        self.assertEqual(set(render.ACTORS),{"dad","mom","boy","girl"})
        self.assertGreater(render.ACTORS["dad"]["idle"].h,render.ACTORS["boy"]["idle"].h)
        for role,modes in render.ACTORS.items():
            self.assertEqual(set(modes),{"walk","idle","talk"})

    def test_the_four_actor_motion_is_independently_keyed(self):
        dad=render.pose_for("dad",.85,render.speaker_at(.85))
        boy=render.pose_for("boy",.85,render.speaker_at(.85))
        mom=render.pose_for("mom",.85,render.speaker_at(.85))
        self.assertEqual((dad.activity,boy.activity,mom.activity),("walk","run","idle"))
        self.assertLess(render.pose_for("boy",.9,None).root_x,render.pose_for("boy",.2,None).root_x)
        self.assertGreater(render.pose_for("dad",1.1,None).root_x,render.pose_for("dad",.2,None).root_x)
        self.assertTrue(render.pose_for("mom",5.4,render.speaker_at(5.4)).point>.9)

    def test_facial_mouth_and_eye_mesh_is_independently_animated(self):
        actor=render.ACTORS["dad"]["talk"]
        base=render.Pose(0,0,gaze=0,talk=0,blink=0)
        active=render.Pose(0,0,gaze=1,talk=1,blink=1)
        a=actor.deform(2.0,base)
        b=actor.deform(2.0,active)
        eye=actor.joints["eye_r"];mouth=actor.joints["mouth"]
        for x,y in (eye,mouth):
            x,y=round(x),round(y)
            region_a=a[y-7:y+8,x-12:x+13,:3]
            region_b=b[y-7:y+8,x-12:x+13,:3]
            self.assertGreater(np.abs(region_a.astype(int)-region_b.astype(int)).mean(),.5)

    def test_facials_are_calibrated_to_each_art_pose(self):
        # Explicit per-pose anchors: the old normalized points silently landed
        # on cheeks or outside the face in this differently cropped art.
        for role,modes in render.ACTORS.items():
            for mode,actor in modes.items():
                eye_l,eye_r,mouth,_=FEATURES[role][mode]
                source=cv2.imread(str(render.ART/f"{role}_{mode}.png"),cv2.IMREAD_UNCHANGED)
                self.assertGreater(int(source[eye_l[1],eye_l[0],3]),200)
                self.assertGreater(int(source[eye_r[1],eye_r[0],3]),200)
                self.assertGreater(int(source[mouth[1],mouth[0],3]),200)
                self.assertNotEqual(actor.joints["eye_l"],actor.joints["eye_r"])

    def test_blink_and_visemes_keep_opaque_faces(self):
        actor=render.ACTORS["dad"]["talk"]
        closed=actor.deform(2.6,render.Pose(0,0,blink=1,talk=1,gaze=.5))
        opened=actor.deform(2.6,render.Pose(0,0,blink=0,talk=1,gaze=.5))
        x,y=map(round,actor.joints["eye_l"])
        blink_roi=closed[y-5:y+6,x-5:x+6]
        self.assertGreater(float(blink_roi[:,:,3].mean()),245)
        self.assertGreater(float(np.abs(closed[y-5:y+6,x-5:x+6,:3].astype(int)-
                                       opened[y-5:y+6,x-5:x+6,:3].astype(int)).mean()),2.0)

    def test_body_art_contiguity_no_separated_head_components(self):
        for role in render.ACTORS:
            for mode,actor in render.ACTORS[role].items():
                alpha=actor.image[:,:,3]
                count,mask,stats,centroids=cv2.connectedComponentsWithStats((alpha>90).astype(np.uint8))
                area=stats[1:,cv2.CC_STAT_AREA]
                self.assertGreater(area.max()/max(1,area.sum()),.987, f"{role}/{mode} disconnected art")

    def test_important_full_frames_are_not_empty(self):
        for t in (.0,.8,1.5,2.6,4.6,5.8,8.35,9.75):
            frame=render.render_frame(t)
            self.assertEqual(frame.shape,(720,1280,3))
            self.assertGreater(float(np.mean(frame)),75)
            self.assertGreater(float(np.std(frame)),18)


if __name__=="__main__":
    unittest.main()
