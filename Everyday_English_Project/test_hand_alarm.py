"""Handedness, wrist anatomy, and alarm contact regression checks."""
import unittest

import numpy as np
from PIL import ImageOps

import action_render as renderer


class HandAnatomyTests(unittest.TestCase):
    def test_brush_handle_passes_through_gripping_fingers(self):
        for local in np.arange(240)/24:
            c=renderer.base(1230,.8,70+local)
            c.update(lean=14,nod=1.5*np.sin((70+local)*1.5))
            wrist,prop,_=renderer.brush_pose(c,float(local))
            np.testing.assert_allclose(renderer.grip_point(c,'near',wrist),prop[1],atol=.05)

    def test_left_and_right_hands_have_mirrored_silhouettes_and_pivots(self):
        for grip in (False, True):
            with self.subTest(grip=grip):
                near, near_pivot = renderer.hand_sprite('near', grip=grip)
                far, far_pivot = renderer.hand_sprite('far', grip=grip)
                self.assertEqual(near.size, far.size)
                np.testing.assert_array_equal(
                    np.asarray(ImageOps.mirror(near).getchannel('A')),
                    np.asarray(far.getchannel('A')),
                )
                self.assertAlmostEqual(far_pivot[0], near.width - 1 - near_pivot[0])
                self.assertAlmostEqual(far_pivot[1], near_pivot[1])
                # Distinct thumbs must not collapse into an identical silhouette.
                self.assertFalse(np.array_equal(
                    np.asarray(near.getchannel('A')),
                    np.asarray(far.getchannel('A')),
                ))

    def test_unposed_wrist_follows_forearm(self):
        for angle in (-350, -180, -20, 0, 110, 179, 350):
            self.assertAlmostEqual(renderer.wrist_angle(angle), angle)

    def test_wrist_limits_are_relative_and_wrap_at_180_degrees(self):
        for forearm in (-179, -120, 0, 120, 179):
            for desired in (-540, -179, -90, 0, 90, 179, 540):
                with self.subTest(forearm=forearm, desired=desired):
                    actual = renderer.wrist_angle(forearm, desired)
                    delta = (actual - forearm + 180) % 360 - 180
                    self.assertLessEqual(abs(delta), 40.000001)
        actual = renderer.wrist_angle(179, -179)
        self.assertAlmostEqual((actual - 179 + 180) % 360 - 180, 2)


class AlarmReachTests(unittest.TestCase):
    def test_wrist_turn_does_not_snap_across_angle_wrap(self):
        angles=[]
        for local in np.arange(240)/24:
            c,targets,_=renderer.wake_pose(float(local))
            shoulder=renderer.geom(c)[1]((-55,-184))
            elbow,wrist=renderer.ik(shoulder,targets['near'],143*c['s'],138*c['s'],-1)
            angles.append(renderer.wrist_angle(renderer.angle(wrist-elbow),c['hand_near']))
        continuous=np.rad2deg(np.unwrap(np.deg2rad(angles)))
        self.assertLess(float(np.max(np.abs(np.diff(continuous)))),12)

    def test_alarm_sequence_keeps_reach_and_fingertip_contact_plausible(self):
        roots = []
        contacts = 0
        phases = set()
        for local in np.arange(240) / 24:
            c, targets, state = renderer.wake_pose(float(local))
            roots.append([c['x'], c['y']])
            phases.add(state['phase'])
            to_world = renderer.geom(c)[1]
            for side, target in targets.items():
                if side not in ('near', 'far'):
                    continue
                shoulder = to_world((52, -183) if side == 'far' else (-55, -184))
                distance = np.linalg.norm(np.asarray(target) - shoulder)
                self.assertLessEqual(distance, (143 + 138) * c['s'] + 1e-5)
                self.assertGreaterEqual(distance, abs(143 - 138) * c['s'] - 1e-5)
            if state['contact']:
                contacts += 1
                self.assertLess(np.linalg.norm(np.asarray(state['fingertip']) - state['button']), 2)
        self.assertGreater(contacts, 0, 'The hand must actually press the alarm')
        self.assertGreaterEqual(len(phases), 3, 'Reach, press and return should be separate beats')
        self.assertLessEqual(float(np.ptp(np.asarray(roots)[:, 0])), 40)
        self.assertLessEqual(float(np.ptp(np.asarray(roots)[:, 1])), 40)
        self.assertFalse(renderer.wake_pose(9.99)[2]['contact'])


if __name__ == '__main__':
    unittest.main()
