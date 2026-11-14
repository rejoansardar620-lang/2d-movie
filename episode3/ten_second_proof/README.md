# Four-character, 10-second 2D animation proof

This is **only the first ten seconds** of the family's flower-learning film,
pending visual approval. It uses the same painted, articulated **nine-part
2D rig** as the two-minute girl reference included in this repository. We
are not making the next 110 seconds until the user approves the motion.

## Reference and exactly what is reused

The reference `Everyday_English_2_Minute_Preview (2).mp4` was made with
`Everyday_English_Project/action_render.py`, `hand_art.py`, and the sprite
parts in `Everyday_English_Project/action_rig/`. Those source files are the
ground truth for style and movement. The family renderer **directly imports**
the original's `rot`, `place`, `angle`, `ik`, `geom`, `gait_phase`, `ease`,
and hand-pose functions. Elbows and knees have two-bone inverse kinematics,
walking has independent step phases, and the head attaches at the neck pivot.

This version replaces the previous experimental whole-body OpenCV mesh
approach. We leave `render.py` and `face_rig.py` in place for comparison,
but they are **not** the production path for this reference-style version.

## Reusable character rigs

| Character | Design | Animated parts |
|---|---|---|
| Rahul | Adult father, dark hair and stubble, blue collared shirt, blue jeans | Head, torso, pelvis, upper arms, forearms, hands, thighs, shins, shoes |
| Priya | Exact reference girl's original illustrated head and white torso, beige trousers | Same nine-part arrangement |
| Aarav | Childlike dark-haired boy, green raglan top and blue jeans | Same arrangement, child-scaled |
| Anaya | Brown-haired girl with pink bow, pink top, purple trousers | Same arrangement, child-scaled |

`matched_rig/source_generated/` contains the newly illustrated transparent
father, son and daughter's **head and torso** sprites. The mother retains
the reference girl's original head/torso. `prepare_matched_rigs.py`
constructs four compatible 9-part rig folders under `matched_rig/roles/`,
recoloring the reference painted trouser and sleeve components appropriately.
The references are copied as body-part paintings, **not as video frames**.

**Asset availability:** The GitHub pull request includes the **36 ready-to-use
character-part PNGs** and the editable text renderer. Its companion full
source ZIP also includes the six original high-resolution generated paintings
used to construct the parts, the reference assets, audio masters, and rendered
MP4. The full ZIP is the recommended self-contained handoff.

Each head has separately located eye and mouth anchors. `rigged_render.py`
blinks the eyelids, shifts the pupil position, rotates the neck, and generates
distinct mouth configurations from the existing Rhubarb audio cues. The
four characters speak at their assigned times, look toward each other, and
take independent steps/gestures. `narration_master.flac` retains the original
four voices; `premium_foley.wav` supplies background ambience.

## Shot list (exactly 10 seconds)

| Time | Action |
|---|---|
| 00:00–01:55 | Garden establishing shot. Dad walks in, son runs in, mother and daughter watch. |
| 01:55–03:58 | Dad's greeting; medium shot and open-palm acting. |
| 03:58–04:35 | Family reaction; mother approaches. |
| 04:35–07:32 | Mom says not to eat flowers; her speaking shot and hand movement. |
| 07:32–07:97 | Family anticipates Aarav's reply. |
| 07:97–09:55 | Aarav asks whether flowers are snacks; speaking gesture and animated eyes. |
| 09:55–10:00 | Return to the family; no unapproved next scene. |

The educational dialogue is unchanged. Clean subtitles appear only during
spoken lines. Background is the exact painterly reference garden scene.

## Run and inspect

From the repository root, with Python 3, Pillow, NumPy, and FFmpeg installed:

```bash
python3 -m pip install numpy pillow
python3 episode3/ten_second_proof/rigged_render.py --preview
python3 episode3/ten_second_proof/rigged_render.py
python3 -m unittest episode3/ten_second_proof/test_articulated.py -v
```

`matched_rig/roles/` already contains the render-ready body parts; no art
generation is necessary to run the GitHub branch. To **regenerate** every part
from its high-resolution source, first extract the complete source ZIP and run
`python3 episode3/ten_second_proof/prepare_matched_rigs.py`.

The editable runtime needs the included `Everyday_English_Project` reference
sources, all six generated transparent head/torso PNGs, and the two episode3
audio files. Video rendering creates exactly 240 frames, 1920×1080, 24 fps
H.264, AAC; always validate the final MP4 with FFprobe and visual playback.

Result files:

- `output/Ten_Second_Family_Articulated_Reference_Style.mp4`
- `output/Ten_Second_Rigged_Contact_Sheet.jpg`
- `rigged_render.py` and `prepare_matched_rigs.py`
- `matched_rig/roles/{dad,mom,boy,girl}/*.png` (36 character layers)
- `test_articulated.py`

## Boundaries and QA

This proof has **real two-bone joint articulation and eight speech viseme
states**, unlike sliding static cutouts. It is still a limited three-quarter
storybook puppet. We do not claim complete hand-drawn Disney animation,
full profile turns, or individual finger deformation. Some high-bend or
cross-body poses may require new role-specific limb drawings and touchups.
Inspect every gesture frame-by-frame before expanding the film.
