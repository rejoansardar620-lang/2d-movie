# 2d-movie

The complete original animation project is extracted in [`Everyday_English_Project/`](Everyday_English_Project/README.md). The source ZIP has been removed; all 37 archived files are preserved in that folder.

To render Episode 01 with Python 3.11/3.12 and FFmpeg installed:

```sh
cd Everyday_English_Project
python -m pip install -r requirements.txt
python action_render.py --preview
python render_all.py --workers 2
```

See [Episode 02](episode2/README.md) for the continuation workflow. The original preview MP4 remains at the repository root.

## Improved character and audio

The root preview MP4 demonstrates the updated open-mouth brushing, stable arm joints, painted leg animation, smoother gestures, attached bag, and mastered narration. See the [animation and sound notes](Everyday_English_Project/README.md#animation-and-sound-improvements) for the changes, validation commands, and remaining rig limitations.

The [6–14 second hand review clip](Hand_Review_6-14s.mp4) isolates the alarm reach and sit-up/stretch transition, including the palm-facing poses and matching arm colours.

## Episode 03: Four-actor cinematic family conversation

**Current film revision:** [Premium 120-second storybook cut](episode3/PREMIUM_RELEASE.md).
It corrects the original cutout father/son head-body seams by using coherent,
full-body actor keyframes and swaps the geometric flowers for detailed botanical
illustrations. The lotus appears in a dedicated pond scene. Run it entirely
offline using the saved narration, generated art atlases and Python renderer.

The improved [two-minute movie cut](episode3/README.md) has Rahul, Priya,
Aarav and Anaya teach ten flower names in a funny conversation while moving
through a **drawing room → kitchen → balcony → garden**. It replaces the
static class-card presentation with staged exchanges, listening reactions,
shot changes, walking entrances, ten flower props, and audio-driven mouths.

- Final: [`episode3/output/Ten_Funny_Flowers_Cinematic_120s.mp4`](episode3/output/Ten_Funny_Flowers_Cinematic_120s.mp4)
- Python offline movie renderer: `python episode3/cinematic_render.py`
- Open-source speech mouth cues: `episode3/prepare_lipsync.py` + [Rhubarb Lip Sync](https://github.com/DanielSWolf/rhubarb-lip-sync)
- Reusable four-actor `Skeleton2D` cutout project for [Godot 4.6](godot_movie/README.md), no proprietary plugins.

The new family starts from the **latest updated Episode 01 character/rig**,
including the improved palm-facing hands; it is not new 360° turnaround art.
