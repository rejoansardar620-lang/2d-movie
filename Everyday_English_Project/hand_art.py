"""Pose-specific hand artwork: dorsal rest, open palm, side press and grip.

The pose describes the visible surface; mirroring only assigns the other hand.
The third return value is the thumb layer to composite after a held object.
"""
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
SKIN = '#f5b77c'
LIGHT = '#fac38e'
SHADOW = '#dea16e'
EDGE = '#b77c52'
CREASE = '#cf9161'
AA = 4


def _curve(points, steps=12):
    """One cubic Bezier, in artwork coordinates."""
    a, b, c, d = points
    result = []
    for i in range(steps + 1):
        t = i / steps
        result.append(tuple((1-t)**3*a[k] + 3*(1-t)**2*t*b[k]
                            + 3*(1-t)*t*t*c[k] + t**3*d[k] for k in (0, 1)))
    return result


def _path(segments):
    return [p for segment in segments for p in _curve(segment)]


def _line(draw, points, fill, width=1):
    draw.line([(round(x*AA), round(y*AA)) for x, y in points],
              fill=fill, width=max(1, round(width*AA)), joint='curve')


def _paint(draw, segments, fill=SKIN, outline=EDGE, width=.7):
    points = _path(segments)
    draw.polygon([(round(x*AA), round(y*AA)) for x, y in points], fill=fill)
    if outline:
        _line(draw, points + points[:1], outline, width)


def _palm():
    # The supplied sprite shows the back of the hand. Supination reverses the
    # projected thumb side before anatomical left/right mirroring is applied.
    source = ImageOps.mirror(Image.open(ROOT/'action_rig/hand.png').convert('RGBA'))
    pic = source.resize((source.width*AA, source.height*AA), Image.Resampling.BICUBIC)
    d = ImageDraw.Draw(pic)
    # Palm creases, thenar fold and wrist crease distinguish the exposed palm.
    for points, width in [
        (((20, 32), (28, 32), (34, 40), (31, 48)), .65),
        (((16, 46), (24, 43), (31, 44), (36, 48)), .6),
        (((14, 53), (23, 50), (30, 51), (37, 55)), .55),
        (((25, 16), (29, 17), (34, 17), (38, 16)), .45),
    ]:
        _line(d, _curve(points), CREASE, width)
    # Preserve the source alpha exactly: creases cannot extend the silhouette.
    pic = pic.resize(source.size, Image.Resampling.LANCZOS)
    pic.putalpha(source.getchannel('A'))
    return pic, (source.width-1-16, 8)


def _grip():
    pic = Image.new('RGBA', (48*AA, 64*AA))
    front = Image.new('RGBA', pic.size)
    d = ImageDraw.Draw(pic)
    # Wrist flows into a palm with four softly staggered curled knuckles.
    _paint(d, [
        ((7, 0), (12, 0), (23, 0), (27, 1)),
        ((27, 1), (27, 11), (26, 17), (30, 21)),
        ((30, 21), (36, 20), (43, 25), (43, 32)),
        ((43, 32), (43, 38), (40, 42), (38, 45)),
        ((38, 45), (35, 54), (30, 58), (25, 57)),
        ((25, 57), (20, 59), (15, 56), (12, 54)),
        ((12, 54), (6, 51), (5, 46), (5, 40)),
        ((5, 40), (4, 32), (7, 24), (8, 18)),
        ((8, 18), (8, 12), (7, 5), (7, 0)),
    ])
    # Side planes give the grip volume without drawing a rectangular fist.
    _paint(d, [
        ((7, 29), (6, 41), (8, 49), (16, 53)),
        ((16, 53), (21, 56), (30, 57), (35, 49)),
        ((35, 49), (26, 54), (16, 46), (14, 38)),
        ((14, 38), (12, 34), (11, 29), (7, 29)),
    ], fill=SHADOW, outline=None)
    for x, end_y in [(13, 47), (20, 51), (27, 50), (34, 45)]:
        _line(d, _curve(((x-2, 34), (x+3, 38), (x+2, 43), (x, end_y))), CREASE, .65)
    _line(d, _curve(((10, 19), (14, 21), (21, 21), (25, 19))), CREASE, .45)
    # The thumb crosses the grip at (22,35); the object is sandwiched between
    # this layer and the curled fingers, rather than painted over the whole hand.
    thumb = [
        ((34, 23), (38, 24), (39, 28), (36, 31)),
        ((36, 31), (32, 34), (27, 38), (23, 39)),
        ((23, 39), (18, 39), (16, 36), (18, 33)),
        ((18, 33), (22, 30), (27, 29), (29, 26)),
        ((29, 26), (30, 24), (32, 23), (34, 23)),
    ]
    f = ImageDraw.Draw(front)
    _paint(f, thumb, fill=LIGHT)
    _line(f, _curve(((21, 33), (23, 31), (26, 31), (28, 32))), '#e4a676', .6)
    # Include the thumb in an unoccluded hand; return the same thumb separately
    # so the renderer can restore it on top of the object.
    pic.alpha_composite(front)
    return (pic.resize((48, 64), Image.Resampling.LANCZOS), (16, 8),
            front.resize((48, 64), Image.Resampling.LANCZOS))


def _press():
    pic = Image.new('RGBA', (46*AA, 93*AA))
    d = ImageDraw.Draw(pic)
    # Side view: four aligned fingers are nearly superimposed. The middle
    # fingertip remains (20,88), matching the alarm contact geometry.
    _paint(d, [
        ((8, 0), (12, 0), (21, 0), (25, 1)),
        ((25, 1), (24, 15), (25, 27), (28, 35)),
        ((28, 35), (32, 41), (34, 49), (31, 56)),
        ((31, 56), (29, 60), (25, 56), (24, 50)),
        ((24, 50), (25, 63), (25, 77), (23, 85)),
        ((23, 85), (22, 88), (20, 89), (18, 87)),
        ((18, 87), (12, 86), (10, 82), (10, 76)),
        ((10, 76), (9, 66), (9, 53), (8, 45)),
        ((8, 45), (6, 35), (8, 25), (9, 17)),
        ((9, 17), (9, 10), (8, 4), (8, 0)),
    ])
    _line(d, _curve(((17, 51), (17, 63), (17, 78), (18, 85))), CREASE, .7)
    _line(d, _curve(((23, 34), (21, 39), (22, 46), (25, 50))), CREASE, .6)
    return pic.resize((46, 93), Image.Resampling.LANCZOS), (16, 8)


@lru_cache(maxsize=8)
def draw_hand(side, pose='relaxed'):
    """Return (base RGBA, wrist pivot, foreground thumb RGBA)."""
    if side not in ('near', 'far'):
        raise ValueError('side must be near or far')
    if pose == 'grip':
        pic, pivot, foreground = _grip()
    else:
        if pose == 'palm':
            pic, pivot = _palm()
        elif pose == 'press':
            pic, pivot = _press()
        elif pose == 'relaxed':
            pic = Image.open(ROOT/'action_rig/hand.png').convert('RGBA')
            pivot = (16, 8)
        else:
            raise ValueError(f'Unknown hand pose: {pose}')
        foreground = Image.new('RGBA', pic.size)
    if side == 'far':
        pic = ImageOps.mirror(pic)
        foreground = ImageOps.mirror(foreground)
        pivot = (pic.width-1-pivot[0], pivot[1])
    return pic, pivot, foreground
