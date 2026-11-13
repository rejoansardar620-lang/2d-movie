# Episode 02 — Breakfast and Garden (120 seconds)

This is a continuation of the original **Morning English — Learn by Doing** project, not an independent animation remake.

## Preserve the original style

- Character identity: the exact body-part PNG layers in `action_rig/`, taken from the original ZIP.
- Backgrounds: the original `routine_bedroom.png`, `bathroom.png`, `kitchen.png`, and `garden.png`.
- Animation: the original `action_render.py` articulated Pillow/NumPy renderer, IK arms and legs, blink/mouth cues, hand targets, and camera framing.
- Visual appearance: original painted artwork, caption strip and warm palette; new props are drawn in the same Pillow pipeline.
- Voice: original `Kokoro-82M` (PyTorch) with `af_heart` at an initial speed of `0.65`, regenerated for **all 36 Episode 02 lines**.
- Mouth animation: Rhubarb 1.14.0 aligned to the regenerated voice.
- Encoding: 1920×1080, 24 FPS, H.264 video + AAC audio, original `render_all.py`.
- Audio mastering: `highpass=f=65,loudnorm=I=-18:TP=-2:LRA=7` from original `make_voice.py`.

## Storyboard

| Time | Scene | Action |
|---|---|---|
| 00:00–00:10 | Let in the sunshine | Walk to and open curtains/window |
| 00:10–00:20 | Tidy my bedroom | Straighten the bed |
| 00:20–00:30 | Wash my hands | Water and hands at sink |
| 00:30–00:40 | Comb my hair | Comb with mirror |
| 00:40–00:50 | Walk into the kitchen | Walk into room |
| 00:50–01:00 | Pick a fresh apple | Reach, hold and wash apple |
| 01:00–01:10 | Prepare my breakfast | Stir in bowl |
| 01:10–01:20 | Enjoy my breakfast | Lift spoon toward mouth |
| 01:20–01:30 | Drink some water | Lift cup and drink |
| 01:30–01:40 | Pack my bag | Pick up bag and check belongings |
| 01:40–01:50 | Go outside | Walk through garden |
| 01:50–02:00 | Water the flowers | Tilt watering can over flowers |

Each scene contains three first-person English sentences, timed and spoken using the same voice. **The same drawing rig and original rooms are used throughout.**

## Run a full build without setting up your laptop

Open [GitHub Actions](https://github.com/rejoansardar620-lang/2d-movie/actions/workflows/render-episode2.yml), select **Render Episode 02 — same original 2D style**, click **Run workflow**, choose the `work/next-two-minute-episode` branch, and run it.

The workflow installs Python, FFmpeg, PyTorch, Kokoro and Rhubarb, extracts the original ZIP, prepares Episode 02, regenerates voice/lip-sync and renders the video.

If successful, the run's **Artifacts** section contains `Episode-02-Finished-Video-and-Project` with:

- `Episode_02_Breakfast_and_Garden_120s.mp4`
- `Episode_02_Complete_Project.zip`

These assets appear only after a successful run. They are not currently stored in the repository. GitHub's Actions artifact retention is set to 30 days.

## Run locally

Requirements: Python 3.11, FFmpeg, 16GB+ RAM recommended and sufficient disk space. Lower memory: use `--workers 1`.

1. Clone the repository and check out `work/next-two-minute-episode`.
2. Run `python episode2/prepare_episode.py`.
3. Enter `build/episode02/Everyday_English_Project`.
4. Follow the original README's Kokoro/PyTorch and Rhubarb installation steps.
5. Download the official Kokoro `config.json`, `kokoro-v1_0.pth`, and `voices/af_heart.pt` into `models/`. Save the last file as `models/af_heart.pt`.
6. Run `python make_voice.py --model-dir models --rhubarb /absolute/path/to/rhubarb --workers 1`.
7. Run `python action_render.py --preview`, then `python render_all.py --workers 1`.

Do **not** run `build_routine.py` from the original ZIP after preparing Episode 02: that would overwrite the new lesson timeline.

## Quality review

Before releasing, watch the full MP4 and check for hand-prop alignment, self-overlap, clipping at kitchen/garden scene boundaries, caption timing, audible dialogue, Rhubarb mouth alignment and flicker. The pre-render preview is useful for static staging but is not a substitute for full motion/audio QA.

## Source

The only Episode 02 modifications are `episode2/prepare_episode.py` and the automation workflow. The original ZIP and preview are left unchanged, so Episode 01 remains reproducible.
