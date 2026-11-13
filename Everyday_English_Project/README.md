# Morning English — Learn by Doing

A two-minute original 2D morning routine: wake up, sit up, stretch, get out of bed, open the curtains and window, make the bed, walk to the bathroom, wash, brush teeth, dry the face, comb hair, drink water and walk outside. Twelve ten-second shots contain 36 first-person sentences with synchronized captions. The setting changes when the routine moves rooms; camera framing changes between shots.

This version uses an articulated cutout puppet with separate head, torso, pelvis, upper arms, forearms, hands, legs and shoes. Arm and leg inverse kinematics, head tilt, blinks, approximate mouth shapes, prop movements, a mirror reflection and foreground blanket/counter layers produce the actions. It is economical 2D cutout animation, not a 3D simulation or frame-by-frame feature animation.

No footage, frames or recorded narration from the supplied reference video are used. The reference informed the everyday action sequence. All final visuals are original artwork or project-drawn props. Voice is locally generated Kokoro-82M af_heart, with Rhubarb mouth cues.

## Render the included video

Install Python 3.11/3.12 and FFmpeg, then:

```sh
pip install pillow numpy
python action_render.py --preview
python render_all.py --workers 2
```

Use one worker on a small laptop. The final file is `output/Everyday_English_2_Minute_Preview.mp4`, 1920 × 1080, 24 fps, exactly 120 seconds, H.264 video and AAC stereo audio. The supplied narration is lossless FLAC. The subtitle track and `captions.srt` accompany the burned-in sentence captions. Rendered segments are checked against the renderer, artwork, lesson, and mouth-cue content; changed inputs rebuild automatically. `--join-only` rejects stale segments.

## Edit the routine

- `build_routine.py`: the twelve actions and 36 sentences. Run it only when changing the lesson, then regenerate narration.
- `action_render.py`: the rig, joint motion, hand targets, scene interactions, camera framing and captions.
- `lesson.json`: synchronized active timeline.
- `action_rig/`: prepared transparent body-part layers.
- `assets/action_puppet_sheet.png`: original generated source sheet.
- `prepare_action_rig.py`: reproducible layer extraction and preparation; requires scipy.
- `audio/narration.flac`, `timings.json`, `mouth_cues.json`: narration and timing data.
- `assets/backgrounds/`: bedroom, bathroom, kitchen and garden.

## Generate a new voice track

```sh
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install kokoro==0.9.4 'transformers<5' soundfile espeakng-loader phonemizer
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

Download the official Kokoro files into `models/`: `config.json`, `kokoro-v1_0.pth` and `voices/af_heart.pt` (save the last as `af_heart.pt`) from https://huggingface.co/hexgrad/Kokoro-82M/tree/main . Download Rhubarb 1.14.0 for your operating system from https://github.com/DanielSWolf/rhubarb-lip-sync/releases/tag/v1.14.0 . Then run:

```sh
python make_voice.py --model-dir models --rhubarb /path/to/rhubarb --workers 2
python render_all.py --workers 2
```

The speech generator uses local PyTorch inference. It does not load ONNX Runtime. Optional Hugging Face telemetry is disabled. Model weights and executable runtimes are not included in this ZIP. The included narration makes them unnecessary for rendering this lesson.

## Tools and assets

Python/Pillow animate and composite; Kokoro/PyTorch generate speech; Rhubarb supplies approximate phoneme mouth cues; FFmpeg encodes. Blender is not used. The character and backgrounds were generated for this project, then separated into animation layers. Small props and effects are drawn in code. Kokoro model: Apache 2.0, https://huggingface.co/hexgrad/Kokoro-82M . DejaVu font license is included. No external vocabulary icons are used in this version.

## Animation and sound improvements

The character uses painted leg layers, fixed elbow bend directions, a reach-clamped two-bone rig, smooth acceleration, subtle breathing, and a walking phase driven by distance. Brushing has an explicit open jaw with teeth; the toothbrush handle and hand are derived from the bristle contact point. Combing returns smoothly between strokes, and the bag attaches to the solved hand position.

`render_all.py` automatically runs `master_audio.py`: gentle speech EQ, measured two-pass normalization to −16 LUFS with a −1.5 dBTP ceiling, and 256 kb/s AAC. The source recording, timing, and pitch remain unchanged. Measured mastering reports are saved under `output/audio/`.

To regenerate speech, `make_voice.py` now defaults to `--speed 0.85` (use `--speed 0.65` for the previous slower delivery). It saves 24-bit source audio; final mastering runs at render time. Regeneration still requires the optional Kokoro and Rhubarb dependencies above. The included improved preview uses the existing narration with the new mastering; a newly synthesized performance has not been validated here.

Run the geometry, brushing-contact, and cache regression checks with:

```sh
python -m unittest discover -s . -p 'test_*.py' -v
```

The artwork remains a single-view cutout rig. Full turns, detailed fingers, and more expressive acting would require additional painted poses or a deformable mesh rig.
