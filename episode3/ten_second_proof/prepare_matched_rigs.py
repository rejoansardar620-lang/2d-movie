"""Produce four compatible cutout rigs from the 120s girl's real rig.

The female reference parts are not approximated with geometric stick limbs:
we reuse their painted limb shading, contact pivots and 2-bone dimensions.
New transparent art supplies the individual father/son/daughter HEADS and
TORSOS, all in the same established film style.  Recoloring painted trouser
layers yields reusable outfit-specific joint components.
"""

from pathlib import Path
import json
import numpy as np
from PIL import Image


HERE=Path(__file__).resolve().parent
REF=HERE.parents[1]/"Everyday_English_Project"/"action_rig"
SRC=HERE/"matched_rig"/"source_generated"
DEST=HERE/"matched_rig"/"roles"
SIZES={"head":(200,274),"torso":(190,235),"pelvis":(190,135),
       "upper_arm":(66,166),"forearm":(49,152),"hand":(46,93),
       "thigh":(88,227),"shin":(76,217),"foot":(120,77)}
PANTS={"dad":(76,110,148),"mom":None,"boy":(70,105,150),"girl":(151,110,178)}
SLEEVE={"dad":(104,155,208),"mom":None,"boy":None,"girl":(245,142,166)}


def crop_generated(path:Path,size:tuple[int,int])->Image.Image:
    original=Image.open(path).convert("RGBA")
    alpha=np.asarray(original.getchannel("A"))
    yy,xx=np.where(alpha>36)
    if not len(xx):
        raise ValueError(f"No alpha cutout: {path}")
    im=original.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)))
    # The target slot has fixed joint/pivot coordinates shared with reference.
    # Fit the entire painted cutout without exposing a black matte.
    w,h=size
    factor=min(w/im.width,h/im.height)
    im=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.LANCZOS)
    canvas=Image.new("RGBA",size)
    canvas.alpha_composite(im,((w-im.width)//2,h-im.height))
    return canvas


def recolor_pants(original:Image.Image,tone:tuple[int,int,int])->Image.Image:
    arr=np.asarray(original.convert("RGBA")).copy()
    rgb=arr[:,:,:3].astype(np.float32)
    luminance=rgb[:,:,0]*.30+rgb[:,:,1]*.59+rgb[:,:,2]*.11
    shade=np.clip((luminance/187.0)**.87,.42,1.52)
    tinted=np.asarray(tone,dtype=np.float32)[None,None,:]*shade[:,:,None]
    # A little of the original pigment variation keeps watercolour folds.
    blue=np.clip(.90*tinted+.10*rgb,0,255).astype(np.uint8)
    arr[:,:,:3]=blue
    return Image.fromarray(arr)


def recolor_sleeve(original:Image.Image,tone:tuple[int,int,int])->Image.Image:
    arr=np.asarray(original.convert("RGBA")).copy()
    h,w=arr.shape[:2]
    yy=np.mgrid[0:h,0:w][0]
    rgb=arr[:,:,:3].astype(np.float32)
    pale=(rgb[:,:,0]>200)&(rgb[:,:,1]>193)&(rgb[:,:,2]>185)
    mask=pale&(yy<round(h*.41))&(arr[:,:,3]>28)
    lum=(rgb[:,:,0]*.30+rgb[:,:,1]*.59+rgb[:,:,2]*.11)/225
    new=np.asarray(tone)[None,None,:]*np.clip(lum[:,:,None],.55,1.22)
    arr[mask,:3]=np.clip(new[mask],0,255).astype('uint8')
    return Image.fromarray(arr)


def main():
    manifest={}
    for role in ("dad","mom","boy","girl"):
        target=DEST/role
        target.mkdir(parents=True,exist_ok=True)
        for part,size in SIZES.items():
            if role!="mom" and part in ("head","torso"):
                image=crop_generated(SRC/f"{part}_{role}.png",size)
            else:
                image=Image.open(REF/f"{part}.png").convert("RGBA")
            if PANTS[role] and part in ("pelvis","thigh","shin"):
                image=recolor_pants(image,PANTS[role])
            if SLEEVE[role] and part=="upper_arm":
                image=recolor_sleeve(image,SLEEVE[role])
            image.save(target/f"{part}.png")
        manifest[role]={"name":{"dad":"Rahul","mom":"Priya","boy":"Aarav","girl":"Anaya"}[role],
                        "layers":list(SIZES),"head_size":SIZES["head"],"pants_color":PANTS[role],
                        "body_pivot":[100,225],"head_pivot":[112,212]}
    (DEST/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print(f"Prepared {len(manifest)} full nine-part illustrated rigs in {DEST}")


if __name__=="__main__":main()
