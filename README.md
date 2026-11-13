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
