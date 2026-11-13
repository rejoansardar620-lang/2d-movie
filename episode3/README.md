# Episode 03 — Ten Funny Flowers (2 minutes)

**Latest cinematic movie cut:** [`output/Ten_Funny_Flowers_Cinematic_120s.mp4`](output/Ten_Funny_Flowers_Cinematic_120s.mp4)

**Legacy classroom/card cut:** [`output/Ten_Funny_Flowers_120s.mp4`](output/Ten_Funny_Flowers_120s.mp4)

Four consistent 2D characters visit four locations; the parents teach their
children ten flowers through funny English dialogue. The latest film is
**120.000 seconds, 1920 × 1080, 24 fps, H.264/AAC**, with a selectable subtitle
track and speaker-tagged burned-in dialogue captions. It is rendered in code
and can be reproduced offline; no browser, animation plugin or paid video
generation API is required.

### What changed since the card-based first version

- Real acted dialogue: whichever family member speaks faces the next/previous
  speaker; listeners face the speaker, tilt their heads and react to jokes.
- Three walk-in entrances at the new rooms, an eight-frame gait cycle, a
  goodbye wave, a blink and gesture bank, nods, pointing and laughing.
- Different camera compositions, close-ups, scene titles, ten animated flower
  props placed within the scene, and room-specific lighting/backgrounds.
- Lip movement based on 575 audio-aligned mouth cues from the open-source
  **Rhubarb Lip Sync CLI**, in place of an arbitrary open/close oscillator.
- A **Godot 4.6** project with reusable skeletal actors and bone controls for
  `walk`, `talk`, `point`, `wave`, `laugh`, `sit` and `listen`. The Python
  movie renderer produces the delivered MP4; the Godot scene is an editable
  rig foundation, not the generator of the delivered MP4.

These are reusable cutout puppets built from the existing source illustration,
not hand-drawn frame-by-frame motion or finished profile/back-facing art.

## Family

| Character | Family role | Appearance | Voice source |
|---|---|---|---|
| Rahul | Father | Short dark hair, blue shirt, blue trousers | Roger: warm male |
| Priya | Mother | Original brown hair and original white shirt | Piper Amy: clear female |
| Aarav | Son | Short dark hair, green shirt, blue trousers | Liam: energetic male |
| Anaya | Daughter | Brown hair with pink ribbon, pink shirt, purple trousers | Jessica: playful female |

The mother uses Episode 01's original illustrated layers. The other characters
are reusable modifications of the **same layered rig**, with the same IK arms,
painted leg layers, body proportions, and original hand sprites. These family
members are deliberately recognizable as the same 2D animation series.

## Storyboard

| Time | Topic | Comedy beat |
|---|---|---|
| 00:00–00:10 | Introduction | Does learning flowers include snacks? |
| 00:10–00:20 | Rose | Can a rose bite? |
| 00:20–00:30 | Sunflower | Taller than Dad! |
| 00:30–00:40 | Tulip | Fairy teacup |
| 00:40–00:50 | Daisy | Will Daisy play with me? |
| 00:50–01:00 | Lily | Lily is a friend's name |
| 01:00–01:10 | Marigold | Is it really made of gold? |
| 01:10–01:20 | Lotus | Swimming lessons for a flower |
| 01:20–01:30 | Hibiscus | “Hi, biscuit!” |
| 01:30–01:40 | Orchid | Fancy like Mom |
| 01:40–01:50 | Jasmine | Dad's old socks |
| 01:50–02:00 | Review | Recap all ten + request snacks |

## Locations and directing

| Time | Place | Action |
|---|---|---|
| 00:00–00:30 | Drawing room | Family gathers around the sofa; dad introduces the rose and sunflower. |
| 00:30–01:00 | Kitchen | Family walks in, turns toward each other, and discusses tulip, daisy and lily. |
| 01:00–01:30 | Balcony | Family enters a balcony with foreground railing; marigold, lotus, hibiscus. |
| 01:30–02:00 | Outside | They enter the garden, discuss orchid and jasmine, and wave goodbye. |

## Files

| File | Purpose |
|---|---|
| `story.json` | 12 scenes, 36 dialogue lines, cast, words, order |
| `render_episode.py` | Renders rigged family sprites, poses, painted garden, flowers, cards, captions and MP4 |
| `cinematic_render.py` | New 12-shot/4-location movie director, face-to-face blocking, cuts, character acting and finished MP4 |
| `prepare_lipsync.py` | Invokes the open-source Rhubarb CLI on the mixed dialogue recording |
| `audio/rhubarb_cues.json` | 575 sound-aligned mouth cues, reusable by the Python film and Godot |
| `export_godot_assets.py` | Exports painted, layered family sprites and locations for Godot |
| `../godot_movie/` | Editable Godot Skeleton2D family rig and timed dialogue scene |
| `produce_audio.py` | Creates synchronized dialogue and light original music, with separately timed voices |
| `audio/raw/*.mp3` | Three original voice tracks, one per character, in script order |
| `audio/narration.wav` | Complete 120s narration + original music, enough to re-render without TTS |
| `audio_sources.json` | The corresponding source-recording URLs |
| `timings.json` | Exact caption and speaker timing |
| `captions.srt` | Timed subtitles, also embedded in MP4 |
| `output/contact_sheet.jpg` | Four representative storyboard frames |
| `output/Ten_Funny_Flowers_120s.mp4` | Final video |
| `output/Ten_Funny_Flowers_Cinematic_120s.mp4` | Latest cinematic finished video |
| `output/cinematic_contact_sheet.jpg` | Four representative movie frames |

The **source art** remains in `../Everyday_English_Project/assets/` and
`../Everyday_English_Project/action_rig/`, with no duplicated backgrounds or
new third-party image dependencies. The original renderer is imported from
`../Everyday_English_Project/action_render.py` and used for the body articulation.

## Render immediately

You need Python 3.11/3.12, Pillow, NumPy, SciPy, FFmpeg and the original repo.
The rendered narration is checked in, so you do **not** need TTS or any model
download to rebuild the same video.

```bash
python -m pip install pillow numpy scipy
python episode3/cinematic_render.py
```

The renderer creates **24 unique frames per second** at 720p working resolution,
then uses Lanczos scaling to deliver the 1080p MP4. Mouth visemes are selected
from Rhubarb audio timings by active speaker. The original
`master_audio.py` from Episode 01 measures and masters the mixed track at
**−16 LUFS with a −1.5 dBTP ceiling** before embedding it into the video.

## Regenerate audio from the original dialogue

1. Install `piper-tts` and use the provided three MP3s for Rahul, Aarav and
   Anaya. Each voice track has lines in script order, with cut points in
   `produce_audio.py` determined from the natural silences between lines.
2. Download the two Piper Amy voice files to `episode3/models/`:

   - [`en_US-amy-medium.onnx`](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx)
   - [`en_US-amy-medium.onnx.json`](https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json)

3. Generate and render:

```bash
python -m pip install pillow numpy scipy piper-tts
python episode3/produce_audio.py
python episode3/cinematic_render.py
```

The Piper model is ignored in git because it is a downloadable 61 MB binary.
The video contains **four separately voiced characters**, with Priya generated
locally after the online voice-generation credit balance ran out. Three MP3s
are already included. You can later replace any actor's MP3 with your preferred
recording or Kokoro voice by updating the cuts in `produce_audio.py`.

## Quality checks and limitations

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate \
  -of json episode3/output/Ten_Funny_Flowers_Cinematic_120s.mp4
```

Check the MP4 after re-rendering for voice-sentence boundaries, mouth cues,
proper overlap of the four characters and the full ten-name recap. Because
the other family members are modified from the original one-view illustration,
they use arm and upper-body gestures plus gentle motion, **not new full-body
turnaround artwork**. Flowers are hand-drawn shapes made in Pillow, rather
than stock photographs. No reference video footage is included. Review the
voice providers' terms before any commercial distribution. Audio dialogue and
the licensed/source recordings are checked into this repo; the Rhubarb
phoneme tool is optional for rerenders because the cues are already generated.
