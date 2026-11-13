"""Split production-approved generated artwork into non-deforming film sprites.

Each animation keyframe is an intact, continuous full-body painting. We do not
cut heads or hands away from shoulders: the main defect in the old film was a
severed neck caused by mixing independently painted source parts. Preserving
complete silhouettes is a deliberate film-quality trade-off: fewer in-betweens,
but coherent identity and anatomy on every rendered frame.
"""
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import binary_dilation, label

ROOT = Path(__file__).resolve().parent / 'assets_premium'
SOURCE = ROOT / 'source'
ACTORS = ROOT / 'actors'
FLOWERS = ROOT / 'flowers'
ROLES = ('dad', 'mom', 'boy', 'girl')
NAMES = ('rose', 'sunflower', 'tulip', 'daisy', 'lily',
         'marigold', 'lotus', 'hibiscus', 'orchid', 'jasmine')

# Boundaries are per-pose because the arms extend differently when speaking.
# Determined by inspecting the alpha channels of the four-character canvases.
SPLITS = {
    'idle': (0, 486, 831, 1167, 1536),
    'walk': (0, 462, 854, 1187, 1536),
    'talk': (0, 505, 881, 1188, 1536),
}


def bounded_rgba(picture, pad=3, role=None, mode=None):
    # Some multi-figure model sheets place the next actor's shoe or elbow
    # inside an adjacent rectangular tile. Keep the actor's single largest
    # connected silhouette and zero all stray neighboring anatomy.
    pixels=np.asarray(picture.getchannel('A')).copy()
    if role=='mom' and mode=='talk':
        # The neighboring boy's hand and sneaker enter the far-right strip of
        # this sheet tile. The mother's own raised hand is entirely above it.
        pixels[300:,300:]=0
    labels,count=label(pixels>16)
    if count:
        areas=np.bincount(labels.ravel())
        areas[0]=0
        primary=labels==areas.argmax()
        keep=binary_dilation(primary,iterations=3)
        pixels[~keep]=0
        picture.putalpha(Image.fromarray(pixels,'L'))
    alpha = picture.getchannel('A')
    box = alpha.point(lambda v: 255 if v > 10 else 0).getbbox()
    if box is None:
        raise ValueError('Transparent sprite: missing actor/flower artwork')
    l, t, r, b = box
    return picture.crop((max(0,l-pad),max(0,t-pad),
                         min(picture.width,r+pad),min(picture.height,b+pad)))


def main():
    ACTORS.mkdir(parents=True, exist_ok=True)
    FLOWERS.mkdir(parents=True, exist_ok=True)
    for mode, splits in SPLITS.items():
        atlas = Image.open(SOURCE / f'family_{mode}.png').convert('RGBA')
        assert atlas.size == (1536, 1024)
        for i, role in enumerate(ROLES):
            part = bounded_rgba(atlas.crop((splits[i],0,splits[i+1],1024)),
                                role=role,mode=mode)
            part.save(ACTORS / f'{role}_{mode}.png')
            print(f'Actor {role:4} {mode:4} {part.size}')
    atlas = Image.open(SOURCE / 'botanical_atlas.png').convert('RGBA')
    width, height = atlas.size
    for index, name in enumerate(NAMES):
        x = index % 5
        y = index // 5
        bounds = (round(x*width/5),round(y*height/2),
                  round((x+1)*width/5),round((y+1)*height/2))
        part = bounded_rgba(atlas.crop(bounds))
        part.save(FLOWERS / f'{name}.png')
        print(f'Flower {name:10} {part.size}')


if __name__ == '__main__':
    main()
