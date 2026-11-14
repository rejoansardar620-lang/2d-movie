# Ten Funny Flowers — Premium Rebuild QC Report

## Release under review

`output/Ten_Funny_Flowers_Premium_120s.mp4`

| Check | Result |
|---|---|
| Running time | **120.000 seconds** |
| Image | **1920 × 1080, 24 fps, H.264** |
| Frame count | **2,880** |
| Sound | **AAC, four-character original dialogue plus original synthesized ambience** |
| Loudness | **−16.0 LUFS integrated**, approximately **−3.9 dBFS true peak** |
| Entire-file FFmpeg video/audio decode | **Pass; no decoder errors** |
| Automated checks | **8/8 pass** (`python3 -m unittest discover -s episode3 -p 'test_premium.py' -v`) |
| Visual spot checks | **36 sampled frames**: opening/middle/closing frames of each ten-second scene |

## Creative corrections verified in samples

- Rahul and Aarav are independently illustrated as an adult father and young son; their heads, shoulders, torsos and limbs are part of intact body silhouettes. All 12 full-body keyframe exports pass the connected-alpha-component test (>99.5% contiguous paint).
- Priya and Anaya retain consistent clothing and physical ages in the same treatment.
- Flower sequence is rose, sunflower, tulip, daisy, lily, marigold, lotus, hibiscus, orchid and jasmine; the atlas uses distinct botanical features for each.
- Lotus occurs in a water pond with floating foliage and ripples, not in a pot. Characters remain outside the pond area.
- The story moves through drawing room, kitchen, balcony/pond and exterior garden. Room entrances, two-shots, closeups and punchline reactions were reviewed.
- The ten-flower recap uses readable flower labels. Captions use lower-profile styling and no persistent speaker banners.

## Scope and outstanding quality limitations

This is a **substantial reconstruction**, but the 2D system is not yet a full, individually articulated studio character rig. Each actor currently has three whole-body poses (idle, walk, talk), translated and blended with restrained breathing and facial overlays. The mouth animation is simplified and does not provide meticulously hand-corrected visemes for every phoneme. Complex turns, independent hand poses, and truly natural limb interpolation need additional artwork and a more advanced rig; passing the connected-silhouette test does not prove that each anatomical joint is correct in motion.

The 36-frame contact sheet is a representative inspection rather than a manual examination of all 2,880 frames. The exported media decoded end-to-end and automated checks passed, but a subjective professional sign-off after a complete real-time screening is still recommended. No claim is made that the remaining animation limitations are solved.

## Reproduce tests and media

```bash
python3 episode3/extract_premium_assets.py
python3 episode3/premium_foley.py
python3 episode3/premium_render.py
python3 -m unittest discover -s episode3 -p 'test_premium.py' -v
ffmpeg -v error -i episode3/output/Ten_Funny_Flowers_Premium_120s.mp4 -f null -
```

For the complete editorial and art guide, see `PREMIUM_RELEASE.md`.
