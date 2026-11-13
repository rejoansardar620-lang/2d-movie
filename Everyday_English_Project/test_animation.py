"""Geometry regressions for the articulated character; run with unittest."""
import unittest
from unittest.mock import patch
import hashlib
import json
import tempfile
from pathlib import Path
from PIL import Image

import numpy as np

from action_render import ik
import action_render as renderer


class LimbGeometryTests(unittest.TestCase):
    def assert_limb(self, shoulder, target, upper, lower, bend):
        elbow, wrist = ik(shoulder, target, upper, lower, bend)
        self.assertTrue(np.isfinite(elbow).all())
        self.assertTrue(np.isfinite(wrist).all())
        self.assertAlmostEqual(float(np.linalg.norm(elbow - shoulder)), upper, places=5)
        self.assertAlmostEqual(float(np.linalg.norm(wrist - elbow)), lower, places=5)
        distance = float(np.linalg.norm(wrist - shoulder))
        self.assertGreaterEqual(distance + 1e-6, abs(upper - lower))
        self.assertLessEqual(distance, upper + lower + 1e-6)
        return elbow, wrist

    def test_reachable_hand_arrives_at_target(self):
        shoulder = np.array([50.0, 100.0])
        for offset in [(20, 60), (-100, 40), (130, -110), (0, 270)]:
            for bend in [-1, 1]:
                with self.subTest(offset=offset, bend=bend):
                    target = shoulder + offset
                    _, wrist = self.assert_limb(shoulder, target, 143, 138, bend)
                    np.testing.assert_allclose(wrist, target, atol=1e-6)

    def test_unreachable_targets_preserve_rigid_limb_lengths(self):
        shoulder = np.array([50.0, 100.0])
        for offset in [(0, 0), (1, 0), (0, -1000), (1000, 1000)]:
            for bend in [-1, 1]:
                with self.subTest(offset=offset, bend=bend):
                    self.assert_limb(shoulder, shoulder + offset, 143, 138, bend)

    def test_equal_bones_at_zero_distance_remain_finite(self):
        shoulder = np.array([50.0, 100.0])
        self.assert_limb(shoulder, shoulder, 100, 100, -1)

    def test_clamped_hand_stays_on_requested_reach_direction(self):
        shoulder = np.array([50.0, 100.0])
        for offset in [np.array([1000.0, 1000.0]), np.array([0.0, -1000.0]),
                       np.array([1.0, 1.0])]:
            with self.subTest(offset=offset):
                _, wrist = ik(shoulder, shoulder + offset, 143, 138, -1)
                direction = offset / np.linalg.norm(offset)
                reach = wrist - shoulder
                lateral_error = reach - np.dot(reach, direction) * direction
                self.assertLess(float(np.linalg.norm(lateral_error)), 1e-6)

    def test_fixed_bend_moves_continuously_across_shoulder_axis(self):
        shoulder = np.array([50.0, 100.0])
        for bend in [-1, 1]:
            elbows = [ik(shoulder, shoulder + [x, 180], 143, 138, bend)[0]
                      for x in np.linspace(-5, 5, 101)]
            steps = np.linalg.norm(np.diff(elbows, axis=0), axis=1)
            self.assertLess(float(steps.max()), 0.2)


class BrushingTests(unittest.TestCase):
    def test_hand_stays_reachable_through_pickup_scrub_and_lowering(self):
        for local in np.linspace(0, 9.99, 240):
            c = renderer.base(1230, .8, 70 + local)
            c.update(lean=14, nod=1.5*np.sin((70+local)*1.5))
            wrist, prop, opening = renderer.brush_pose(c, local)
            shoulder = renderer.geom(c)[1]((-55, -184))
            _, solved = renderer.ik(shoulder, wrist, 143*.8, 138*.8, 1)
            np.testing.assert_allclose(solved, wrist, atol=1e-6)
            if 2.3 < local < 8.3:
                _, target, pivot, angle, scale = prop
                bristles = target + renderer.rot(np.array([28,81])-pivot,angle)*scale
                self.assertLess(np.linalg.norm(bristles-renderer.geom(c)[4]), 5)
                self.assertGreater(opening, .99)

    def test_brushing_opens_mouth_even_during_speech(self):
        with patch.object(renderer, 'face', wraps=renderer.face) as face:
            renderer.action_stage(7, 75)
        self.assertTrue(face.call_args_list)
        self.assertTrue(all(call.args[0]=='BRUSH' for call in face.call_args_list))


class MotionTests(unittest.TestCase):
    def test_rendered_arm_does_not_flip_at_shoulder_axis(self):
        c=renderer.base()
        shoulder=renderer.geom(c)[1]((-55,-184))
        bends=[]
        for dx in (-1,1):
            with patch.object(renderer,'ik',wraps=renderer.ik) as solve:
                renderer.puppet(Image.new('RGBA',(1920,1080)),0,c,{'near':shoulder+[dx,180]})
            bends.append(solve.call_args_list[-1].args[4])
        self.assertEqual(bends[0],bends[1])

    def test_walking_stance_foot_remains_planted(self):
        ankles=[]
        for x in (1000,1001):
            c=renderer.base(x=x)
            c['walk']=True
            with patch.object(renderer,'ik',wraps=renderer.ik) as solve:
                renderer.puppet(Image.new('RGBA',(1920,1080)),0,c)
            ankles.append(solve.call_args_list[1].args[1])
        np.testing.assert_allclose(ankles[0],ankles[1],atol=1e-6)


class SegmentCacheTests(unittest.TestCase):
    def test_changed_inputs_or_damaged_video_are_not_reused(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(renderer, 'ROOT', Path(folder)), patch.object(renderer, 'render_fingerprint', return_value='new-inputs'):
            path=Path(folder)/'output/segments'
            path.mkdir(parents=True)
            (path/'00.mp4').write_bytes(b'generated video')
            stamp={'inputs':'old-inputs','video':hashlib.sha256(b'generated video').hexdigest()}
            (path/'00.json').write_text(json.dumps(stamp))
            self.assertFalse(renderer.segment_current(0))
            stamp['inputs']='new-inputs'
            (path/'00.json').write_text(json.dumps(stamp))
            self.assertTrue(renderer.segment_current(0))
            (path/'00.mp4').write_bytes(b'truncated')
            self.assertFalse(renderer.segment_current(0))


if __name__ == '__main__':
    unittest.main()
