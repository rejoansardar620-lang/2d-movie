# Episode 03 — Ten Funny Flowers: Premium 2D Family Film

## Deliverables

| Asset | Description |
|---|---|
| `output/Ten_Funny_Flowers_Premium_120s.mp4` | Complete 120-second, Full HD, 24 fps H.264/AAC storybook film |
| `output/premium_contact_sheet.jpg` | 12-scene camera and art preview |
| `output/premium_qc_36_frames.jpg` | First, middle, last frames of all 12 scenes |
| `premium_render.py` | Reproducible video director with animated characters, flower inserts, pond, camera and typography |
| `premium_foley.py` | Original synthesized walking, garden, water, chirp and chime sounds |
| `assets_premium/source/` | Four-family-character style/pose source atlases and botanical flower atlas |
| `extract_premium_assets.py` | Splits the original full-body atlas illustrations into intact acting sprites |
| `test_premium.py` | Automated anatomy/continuity, flower, timing and video validation |

## The anatomy correction

The earlier film reused a single woman's illustrated head with cropped hair
and attached it to a programmatically drawn male torso. The resulting father
and son looked too similar and sometimes appeared to have severed necks.

For this revision we regenerated the entire family as a **coherent original
model sheet**, preserving the same clothing colours and storybook style while
distinguishing a 38-year-old father, a mother, a 9-year-old son, and a 7-year-
old daughter. We also generated separate **walking** and **speaking/gesture**
keyframes. Faces, necks, arms, torso, trousers, hands, knees and shoes are
part of one continuous body in every frame; no independently floating heads.

The alpha-mask regression tests require the largest contiguous painted body
component in each of 12 sprites to exceed **99.5%** of all painted pixels.
`extract_premium_assets.py` removes stray pixels from neighboring atlas
figures before delivery. Actor height is age-appropriate; figure contact
shadows are independently animated to ground their feet.

This approach prioritizes **anatomical continuity and consistent identity**.
It is still a small-pose 2D animation system: three principal keyframes per
actor plus camera movement, whole-sprite facing direction, idle breathing,
walking translations, gestures and lip overlays. It is not an industry-complete
bone-rigged turnaround with 360-degree turns, custom hand poses, or manually
drawn 24-frame-per-second in-between animation. Future production work can add
additional natural pose frames without reintroducing cutout neck seams.

## Reproduction (no paid runtime API)

The story and all original four-character audio recordings remain in `episode3/`.
Use the generated source PNG atlases already shipped with the project. The
full-body actor artwork was generated for this film using an AI image-generation
tool, then cropped into reproducible film assets using local scripts.

Requirements: Python 3.11+, Pillow, NumPy, SciPy, FFmpeg.

```bash
python3 -m pip install pillow numpy scipy
python3 episode3/extract_premium_assets.py
python3 episode3/premium_foley.py
python3 episode3/premium_render.py --preview
python3 episode3/premium_render.py
python3 -m unittest discover -s episode3 -p 'test_premium.py' -v
```

The renderer operates at 1280×720 with 24 unique frames each second, then
uses FFmpeg Lanczos scaling for Full HD and H.264/AAC encoding. It retains the
episode's four-voice, 120-second, previously mastered FLAC soundtrack and
mixes only low-level **original synthesized** environmental effects. No
external TTS call is necessary to reproduce the audio, and no animation
plugin is necessary to reproduce the movie.

## Exact shot plan

| Seconds | Location | Featured element | Physical / cinematic action |
|---|---|---|---|
| 0–10 | Drawing room | Family | Wide introduction; speaker- and listener-facing exchanges |
| 10–20 | Drawing room | Rose | Bloom/thorn insert, child's playful question, mother's warning |
| 20–30 | Drawing room | Sunflower | Plant taller than Dad; playful child and parent reactions |
| 30–40 | Kitchen | Tulip | Walking entrance, cup-shaped bloom, fantasy tea-cup glimmer |
| 40–50 | Kitchen | Daisy | White petal/gold disc insert, child addressing the flower |
| 50–60 | Kitchen | Lily | Distinctive stamen/large petals, child's gentle high-five gesture |
| 60–70 | Balcony | Marigold | Family walks in; gold-coin imagination gag |
| 70–80 | Pond beside balcony | Lotus | Explicit water, floating green leaf and moving ripples; no pot |
| 80–90 | Balcony | Hibiscus | Red flower with protruding stamen; biscuit-language joke |
| 90–100 | Outside | Orchid | Walk into garden; orchid close-up and mother's elegant reaction |
| 100–110 | Outside | Jasmine | White flower cluster; aroma curl and father's socks joke |
| 110–120 | Outside | Ten species | Accurate ten-flower recap board and family happy ending |

## Art source and visual consistency

The atlas under `assets_premium/source/` is the **source of truth** for all
character and botanical illustrations. The `actors/` and `flowers/` PNGs are
derived exports, regenerated in one command; edit the source sheets and rerun
the extractor if the wardrobe/appearance changes. The source sheets were
generated for this production using the following art direction:

> Family-friendly premium hand-painted storybook 2D, warm outlines and soft
> shading. Rahul: mature father with short dark hair, light stubble, blue shirt
> and jeans. Priya: adult woman, brown hair, white blouse, beige trousers.
> Aarav: clearly 9-year-old child, short dark hair, teal shirt, blue jeans.
> Anaya: clearly 7-year-old child, pink bow and top, purple trousers. Four
> aligned full-body figures with proportionate anatomy, connected shoulders,
> wrists, knees and feet. Additional whole-body walk and conversation poses.
> Botanical atlas: species-accurate rose, sunflower, tulip, daisy, lily,
> marigold, aquatic lotus, hibiscus, orchid and jasmine; transparent backdrop.

`premium_render.py` uses the **same artwork** for every scene to prevent
identity morphing or wardrobe changes. The film uses the original painterly
backgrounds from `Everyday_English_Project` with a dedicated pond composited
into the lotus section.

## QA procedure

1. Render all 36 first/middle/last frames and review `premium_qc_36_frames.jpg`.
2. Inspect all four identities and the distinct adult/child proportions.
3. Verify uninterrupted full-body silhouette masks and no neighboring limbs.
4. Verify flower spelling/order, the distinct bloom shapes and lotus water.
5. Play the MP4 from start to finish and check 120 seconds, Full HD, 24 fps,
   audible four-voice dialogue, correct subtitle text and safe peak levels.
6. Inspect room-entry movements around seconds 30, 60 and 90.
7. Run `test_premium.py` and a full FFmpeg decode on the exported video.

### Honest remaining limitations

The film now has cohesive full-body people, modern minimal captions, accurate
flower reference art and story-specific camera shots. **It still uses a
limited number of illustrated poses and simulated mouth overlays**, so highly
nuanced eye animation, complex finger contact, seamless turnarounds and
fluid hand-drawn secondary motion are not yet equivalent to a professional
frame-by-frame studio animation. The 36-frame strip is a sampled review,
not a human inspection of all 2,880 images; continuous-playback verification
is required for final release sign-off.
