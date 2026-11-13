# Reusable 2D family actors — Godot 4.6, no animation plugin

This is an **editable Godot project** that uses Godot's built-in `Skeleton2D`
and `Bone2D` nodes, plus local GDScript, for four family members. It shares
the original `Everyday_English_Project` hand/body art and the four-voice
episode recording. It is an independent editing/animation starting point;
**the completed movie MP4 is rendered by `episode3/cinematic_render.py`, not
exported by Godot**.

## Start it

1. Install [Godot 4.6](https://godotengine.org/), the open-source engine.
2. From the repository root, regenerate the four character layer sets, rooms
   and flower props if needed:

   ```bash
   python3 episode3/export_godot_assets.py
   ```

3. Open the **repository root** (the folder containing `project.godot`) as a
   Godot project; press **F6/F5** to run the main scene. The source audio
   and `timings.json` drive who speaks, while `rhubarb_cues.json` drives the
   mouth shape. No proprietary plug-in or API key is required.

   Optional automated script check:

   ```bash
   godot --headless --path . --editor --quit
   godot --headless --path . --quit-after 15
   ```

## Layered character rig

Each of `dad`, `mom`, `boy`, and `girl` has a separate set of original-style
painted PNG layers in `assets/characters/<role>/`: head, body, pelvis, thighs,
shins, feet, upper arms, forearms, hands. `actor.gd` creates the hierarchy:

```text
Skeleton2D
  hip
    near/far thigh -> shin -> foot
    spine
      near/far arm -> forearm -> hand
      head -> VisemeMouth
```

The configurable `apply_action(time, mode, look_right, mouth)` supports:

| Motion | Animation |
|---|---|
| `walk` | Alternating knee, shin and arm swing with body bounce |
| `talk`, `point` | Speaker gestures toward the listening character |
| `listen` | Head tilts toward the active speaker |
| `laugh` | Head tilt and lifted arm |
| `wave` | Raised waving arm |
| `sit` | Hip/knee rotations, ready for a properly staged chair scene |
| any mode | Left/right look, subtle breath and rhythmic head motion |
| dialogue | Multiple phoneme mouth shapes (Rhubarb `A`–`H`, `X`) |

The `director.gd` controls room backgrounds, flower props, walking entrances,
positions, camera coverage, subtitles, and responsive dialogue. For a new
episode, change `ROOMS`, `TARGETS`, script/timings, and recordings.

## Update lip sync from the open-source CLI

Download the Rhubarb Lip Sync official CLI release from
[GitHub](https://github.com/DanielSWolf/rhubarb-lip-sync/releases), then run:

```bash
python3 episode3/prepare_lipsync.py --rhubarb /path/to/rhubarb
```

This recreates 575 cues in the current version from `audio/narration.wav`.
Each character uses only the cues during **their** timed lines. The audio
itself is reused rather than regenerated, so the original four-voice mix is
preserved.

## Honest limitations

The source project has one three-quarter/front-facing painted character
rig. The four family designs reuse it and add age, costume and hair changes.
They can **mirror left/right**, walk, talk and gesture, but mirroring does not
create an authentic profile/back view. Chair contact, hand-held props,
eye-pupil tracking, fully articulated fingers, and realistic long-distance
perspective still need new dedicated paintings and rigging. Godot supplies
editing tools for those improvements, not automatic actor-quality animation.

Other fully open-source options: [Blender Grease Pencil](https://docs.blender.org/manual/en/latest/grease_pencil/)
for additional hand-drawn angle/pose art; [OpenToonz](https://opentoonz.github.io/e/)
or [Synfig](https://www.synfig.org/) for more traditional shot animation.
