# Artwork and production notes

The original front-view character, garden and kitchen are reused from this project. The uploaded reference video is consulted only for everyday actions and staging; no extracted frame is used in the finished animation.

Three additional original assets were generated using the built-in image generation tool:

1. **Puppet part sheet** — Preserve the original adult woman's chestnut wavy hair, warm complexion, hazel eyes, white short-sleeve shirt, beige trousers and tan shoes. Draw a spacious transparent 3 × 3 sheet of disconnected three-quarter right-facing head, shirt torso, pelvis, upper arm, forearm, hand, thigh, shin and side-view foot. Fine warm brown outlines and soft storybook cel shading. No text or labels.
2. **Bedroom** — Warm 16:9 storybook cel-animation bedroom with a horizontal side-on single bed across the lower left, headboard and pillow at left, smooth oatmeal blanket, wood bedside table and alarm clock, large window on upper right, cream curtains, plants and clear floor. No people or text; crisp bed and window contours for puppet interaction.
3. **Bathroom** — Matching warm 16:9 storybook bathroom, cream and sage tile, open floor at left, doorway and hallway, wooden vanity on right, white basin, visible chrome faucet, oval mirror, towel, soap and toothbrush cup. No people, reflected people, text or watermark.

`prepare_action_rig.py` crops and separates connected alpha artwork, removes generation haze, resizes reusable parts and feathers joint overlaps. Legs use a continuous drawn contour across knee bends to avoid visible cutout seams. The other body layers retain the generated artwork. Props (toothbrush, comb, towel, cup, bag), window pane, curtain, water, caption band and foot shadows are drawn in code. The original blanket texture is composited as a foreground layer so the sleeping body is covered. The mirror uses a horizontally reflected rendering of the animated upper body.

This is an economical reusable 2D cutout system. It supports the demonstrated poses and interactions; arbitrary new complex actions still require staging and animation work.
