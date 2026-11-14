"""Hand-calibrated animated facial layers for the premium 2D family artwork.

The previous proof warped arbitrary locations on each PNG.  Because talk,
idle, and walk artwork have different bounds, those warps missed the eyes and
mouth.  This module follows the proven, explicit-viseme + eyelid technique in
Everyday_English_Project/action_render.py, with independent gaze and more
accurate per-pose anchors.  There is no face-swap or generated-face flicker.
"""

from __future__ import annotations

import math

import cv2
import numpy as np


# All coordinates are measured in each ORIGINAL transparent PNG, not the
# rescaled on-screen sprite.  Source artwork changes framing by pose.
# Layout: eye_left, eye_right, mouth, mouth half-width in source pixels.
FEATURES = {
    "dad": {
        "idle": ((181, 82), (220, 82), (200, 121), 25),
        "walk": ((228, 86), (264, 85), (247, 126), 24),
        "talk": ((197, 91), (232, 84), (217, 130), 24),
    },
    "mom": {
        "idle": ((134, 91), (177, 86), (160, 124), 22),
        "walk": ((189, 86), (223, 85), (211, 119), 21),
        "talk": ((135, 91), (171, 81), (161, 119), 22),
    },
    "boy": {
        "idle": ((114, 83), (153, 82), (139, 117), 19),
        "walk": ((182, 102), (212, 100), (201, 126), 17),
        "talk": ((105, 102), (141, 90), (130, 120), 19),
    },
    "girl": {
        "idle": ((128, 86), (167, 83), (147, 116), 19),
        "walk": ((158, 89), (186, 86), (176, 126), 17),
        "talk": ((132, 89), (169, 84), (151, 125), 19),
    },
}

# The source art has large expressive eyes.  We keep the same proportions;
# iris and eyelid are independent layers, while the underlying face stays one
# uninterrupted illustration, preserving the neck and painted body.
FACE_PALETTE = {
    "dad": dict(iris=(42, 75, 103), lip=(70, 75, 134), edge=(53, 67, 91), skin=(151, 181, 242)),
    "mom": dict(iris=(61, 82, 118), lip=(82, 83, 157), edge=(75, 69, 105), skin=(152, 197, 248)),
    "boy": dict(iris=(57, 78, 110), lip=(74, 71, 135), edge=(63, 67, 92), skin=(156, 189, 250)),
    "girl": dict(iris=(67, 88, 125), lip=(85, 91, 163), edge=(80, 72, 115), skin=(159, 192, 251)),
}


class AnimatedFace:
    def __init__(self, role: str, mode: str, original_size: tuple[int, int], scale: float):
        self.role, self.mode, self.scale = role, mode, scale
        self.src_h, self.src_w = original_size
        self.eye_l, self.eye_r, self.mouth, self.mouth_width = FEATURES[role][mode]
        self.colors = FACE_PALETTE[role]

    def sanitized_source(self, source: np.ndarray) -> np.ndarray:
        """Remove the baked-in mouth; preserve the original expressive eyes."""
        mask = np.zeros(source.shape[:2], dtype=np.uint8)
        x, y = self.mouth
        cv2.ellipse(mask, (x, y), (self.mouth_width + 4, 15), 0, 0, 360, 255, -1)
        original = source.copy()
        # The painterly cheek colours are reconstructed from the surrounding
        # real source pixels, rather than hidden under opaque face stickers.
        original[:, :, :3] = cv2.inpaint(source[:, :, :3], mask, 5, cv2.INPAINT_TELEA)
        return original

    def landmarks(self):
        return {
            "eye_l": tuple(v * self.scale for v in self.eye_l),
            "eye_r": tuple(v * self.scale for v in self.eye_r),
            "mouth": tuple(v * self.scale for v in self.mouth),
            "brow_l": (self.eye_l[0] * self.scale, (self.eye_l[1] - 17) * self.scale),
            "brow_r": (self.eye_r[0] * self.scale, (self.eye_r[1] - 17) * self.scale),
        }

    def paint(self, sprite: np.ndarray, pose, time: float, viseme: str, displacement_x, displacement_y):
        """Render independent eyes, moving pupils, blink lids and speech mouths.

        Face details are drawn into a 4x supersampled region before downsample,
        so their fine features remain clean after a cinematic camera push-in.
        """
        h, w = sprite.shape[:2]
        coords = []
        for raw in (self.eye_l, self.eye_r, self.mouth):
            xx, yy = raw[0] * self.scale, raw[1] * self.scale
            ix, iy = int(np.clip(round(xx), 0, w - 1)), int(np.clip(round(yy), 0, h - 1))
            coords.append((xx + float(displacement_x[iy, ix]), yy + float(displacement_y[iy, ix])))

        x0 = max(0, int(min(p[0] for p in coords) - 24))
        x1 = min(w, int(max(p[0] for p in coords) + 25))
        y0 = max(0, int(min(p[1] for p in coords) - 22))
        y1 = min(h, int(max(p[1] for p in coords) + 27))
        if x1 <= x0 or y1 <= y0:
            return sprite
        S = 4
        patch = cv2.resize(sprite[y0:y1, x0:x1], ((x1 - x0) * S, (y1 - y0) * S),
                           interpolation=cv2.INTER_CUBIC)
        def point(p):
            return (round((p[0] - x0) * S), round((p[1] - y0) * S))
        def opaque(bgr):
            # cv2 drawing onto BGRA with a 3-tuple sets alpha to ZERO.  All
            # facial paint must be 4-channel, or the garden shines through!
            return (*bgr, 255)
        ecolor = self.colors["edge"]
        # Preserve the original artist-drawn eye shape, eyelashes, highlights
        # and iris (already gaze-shifted by the calibrated eye mesh in render).
        # During a blink we replace only the visible eye with a soft skin lid,
        # just as the proven 120-second girl's action_rig/face renderer does.
        for idx, xy in enumerate(coords[:2]):
            if pose.blink < .18:
                continue
            cx, cy = point(xy)
            rx, ry = (26, 20) if self.role in ("boy", "girl") else (24, 18)
            # Skin closes down over the eyeball. A narrow curved eyelid line
            # stays visible in the fully closed position.
            blend = min(1.0, (pose.blink - .18) / .35)
            skin = opaque(self.colors["skin"])
            face_cover = patch.copy()
            cv2.ellipse(face_cover, (cx,cy), (rx+2,ry), 0,0,360,skin,-1,cv2.LINE_AA)
            cv2.addWeighted(face_cover, blend,patch,1-blend,0,patch)
            if blend > .4:
                cv2.ellipse(patch,(cx,cy),(rx-2,6),0,9,169,opaque(ecolor),3,cv2.LINE_AA)

        mx, my = point(coords[2])
        # The reference girl uses subtle visemes: the opening must stay below
        # the nose/chin and read as a mouth rather than a second circular face.
        base_width = max(24, round(self.mouth_width * self.scale * S * .54))
        # Audio-driven viseme shapes from actual Rhubarb cue boundaries.
        mouth_shapes = {
            "X": (1.0, .0), "A": (1.0, .0), "B": (.74, .13),
            "C": (.84, .62), "D": (.90, 1.0), "E": (.65, .81),
            "F": (.52, .68), "G": (.92, .20), "H": (.73, .49),
        }
        width_factor, open_factor = mouth_shapes.get(viseme, (1, 0))
        if not pose.talk and viseme not in ("A", "X"):
            viseme = "X"
            width_factor, open_factor = mouth_shapes[viseme]
        mw = round(base_width * width_factor)
        if open_factor < .1:
            smile = np.array([(mx - mw, my - 4), (mx - mw // 2, my + 4),
                              (mx, my + 7), (mx + mw // 2, my + 4),
                              (mx + mw, my - 4)], dtype=np.int32)
            cv2.polylines(patch, [smile], False, opaque(self.colors["lip"]), 4, cv2.LINE_AA)
        else:
            mh = round(3 + 15 * open_factor)
            cv2.ellipse(patch, (mx, my), (mw, mh), 0, 0, 360,
                        opaque(self.colors["lip"]), -1, cv2.LINE_AA)
            cv2.ellipse(patch, (mx, my + 3), (max(1, mw-3), max(2, mh-4)), 0, 0, 360,
                        opaque((45, 45, 75)), -1, cv2.LINE_AA)
            if viseme in ("B", "C", "D", "G", "H"):
                cv2.ellipse(patch, (mx, my - max(0, mh//2)),
                            (max(5, mw-5), max(2, round(mh*.20))), 0, 180, 360,
                            opaque((235, 246, 252)), -1, cv2.LINE_AA)
            if viseme in ("D", "E"):
                cv2.ellipse(patch, (mx, my + round(mh*.48)),
                            (max(4, mw//2), max(2, mh//4)), 0, 180, 360,
                            opaque((111, 113, 195)), -1, cv2.LINE_AA)
            cv2.ellipse(patch, (mx, my), (mw, mh), 0, 0, 360,
                        opaque(self.colors["edge"]), 3, cv2.LINE_AA)

        sprite[y0:y1, x0:x1] = cv2.resize(patch, (x1-x0, y1-y0),
                                          interpolation=cv2.INTER_AREA)
        return sprite
