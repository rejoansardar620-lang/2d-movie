"""Export paint layers into a reusable Godot 4.6 cutout rig (no proprietary plugin)."""
from pathlib import Path

import cinematic_render as movie
import render_episode as art

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'godot_movie'/'assets'


def main():
    for role,parts in art.VARIANTS.items():
        folder=DEST/'characters'/role
        folder.mkdir(parents=True,exist_ok=True)
        for name,pic in parts.items():
            pic.save(folder/f'{name}.png')
    backgrounds=DEST/'backgrounds'
    backgrounds.mkdir(parents=True,exist_ok=True)
    for room in ('drawing_room','kitchen','balcony','outside'):
        movie.room_image(room).save(backgrounds/f'{room}.png')
    flowers=DEST/'flowers'
    flowers.mkdir(parents=True,exist_ok=True)
    for name in art.FLOWER_COLORS:
        art.flower_art(name,190).save(flowers/f'{name}.png')
    print(f'Exported reusable painted family, rooms and flower assets to {DEST}')


if __name__=='__main__':main()
