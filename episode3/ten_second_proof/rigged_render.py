"""10-second family-film proof using the reference girl's *actual* joint rig.

Each character is assembled from nine painted layers and animated with
two-bone IK elbows/knees, planted-foot walk cycles, a rotating neck joint,
independent eye motion, blinks, and audio-directed mouth visemes.  The
original single-girl routine remains untouched and is the rigging reference.

    python3 episode3/ten_second_proof/rigged_render.py --preview
    python3 episode3/ten_second_proof/rigged_render.py
"""

from __future__ import annotations

import argparse
import bisect
from functools import lru_cache
import json
import math
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

HERE = Path(__file__).resolve().parent
EPISODE = HERE.parent
PROJECT = HERE.parents[1]
REFERENCE = PROJECT / "Everyday_English_Project"
sys.path.insert(0, str(REFERENCE))
import action_render as ref  # noqa: E402 - reuse exact original two-bone geometry

W, H, FPS = 1920, 1080, 24
OUT = HERE / "output"
RIG = HERE / "matched_rig" / "roles"
TIMINGS = json.loads((EPISODE / "timings.json").read_text())[:3]
CUES = json.loads((EPISODE / "audio" / "rhubarb_cues.json").read_text())["mouthCues"]
CUE_STARTS = [c["start"] for c in CUES]
GROUND = 920
SKIN = {"dad": (237, 174, 127), "mom": (251, 184, 129),
        "boy": (249, 188, 145), "girl": (250, 187, 143)}
PANTS = {"dad":(83,112,151),"mom":(201,178,155),
         "boy":(82,107,146),"girl":(155,115,176)}
FACE = {
    "dad": dict(mouth=(147, 164), eyes=((119, 118), (171, 114)), pivot=(112, 247)),
    "mom": dict(mouth=(163, 142), eyes=((132, 101), (176, 101)), pivot=(112, 212)),
    "boy": dict(mouth=(145, 204), eyes=((118, 166), (169, 163)), pivot=(112, 260)),
    "girl": dict(mouth=(149, 203), eyes=((118, 163), (170, 160)), pivot=(112, 255)),
}
SCALE = {"dad": .92, "mom": .84, "boy": .63, "girl": .57}


def smooth(u: float) -> float:
    u = max(0., min(1., u))
    return u*u*(3-2*u)


def active_line(t: float):
    return next((v for v in TIMINGS if v["start"] <= t < v["end"]), None)


def viseme_at(t: float, role: str) -> str:
    line = active_line(t)
    if line is None or line["speaker"] != role:
        return "X"
    idx = bisect.bisect_right(CUE_STARTS, t) - 1
    if idx >= 0 and CUES[idx]["start"] <= t < CUES[idx]["end"]:
        return CUES[idx]["value"]
    return "A"


@lru_cache(maxsize=4)
def parts_for(role: str):
    return {p.stem: Image.open(p).convert("RGBA") for p in (RIG / role).glob("*.png")}


@lru_cache(maxsize=4)
def dark_for(role: str):
    return {k: ImageEnhance.Brightness(v).enhance(.89) for k, v in parts_for(role).items()}


def mouth_on_head(im: Image.Image, role: str, shape: str):
    if shape in ("X", "A"):
        return
    x, y = FACE[role]["mouth"]
    skin = SKIN[role]
    # Cover the existing illustrated resting smile, blending with its paint.
    veil = Image.new("RGBA", im.size)
    mask = Image.new("L", im.size)
    ImageDraw.Draw(mask).ellipse((x-30,y-17,x+30,y+17), fill=255)
    veil.paste(skin + (255,), (0,0,im.width,im.height))
    veil.putalpha(mask.filter(ImageFilter.GaussianBlur(3.5)))
    im.alpha_composite(veil)
    d = ImageDraw.Draw(im)
    radii = {"B":(16,3), "C":(14,8), "D":(13,12), "E":(8,13),
             "F":(6,12), "G":(18,5), "H":(11,7)}
    rx, ry = radii.get(shape, (11,6))
    d.ellipse((x-rx,y-ry,x+rx,y+ry), fill="#783729",outline="#ae6045",width=2)
    if shape in ("B","C","D","G","H"):
        d.arc((x-rx+3,y-ry+2,x+rx-3,y+2),180,360,fill="#fff2da",width=3)
    if shape in ("D","E","F"):
        d.ellipse((x-6,y+ry-6,x+7,y+ry),fill="#c76f72")


@lru_cache(maxsize=512)
def face_sprite(role: str, shape: str, blink: bool, gaze_tenths: int):
    head = parts_for(role)["head"].copy()
    gaze = gaze_tenths / 10.0
    # Colored pupil overlays and painted eyelids use precisely located
    # landmarks; the eye positions are *independent* of neck/head movement.
    d = ImageDraw.Draw(head)
    for eye_x, eye_y in FACE[role]["eyes"]:
        if blink:
            color = SKIN[role]
            d.ellipse((eye_x-13,eye_y-8,eye_x+13,eye_y+8),fill=color)
            d.arc((eye_x-12,eye_y-5,eye_x+12,eye_y+6),5,176,fill="#654331",width=3)
        else:
            # Redraw only the painted iris zone. The surrounding original
            # eyelid geometry and expressive eyebrows remain intact.
            offset = gaze*2.8
            if abs(offset) > .2:
                d.ellipse((eye_x-7,eye_y-7,eye_x+7,eye_y+7),fill="#fff5e9")
                d.ellipse((eye_x-5+offset,eye_y-6,eye_x+5+offset,eye_y+6),fill="#79472d")
                d.ellipse((eye_x-3+offset,eye_y-4,eye_x+3+offset,eye_y+4),fill="#322822")
                d.ellipse((eye_x-2+offset,eye_y-4,eye_x+offset,eye_y-2),fill="#ffffff")
    mouth_on_head(head,role,shape)
    return head


def footfall(role: str, t: float):
    if role == "dad":
        u = smooth(t/1.55)
        return 345 + 190*u, (t < 1.55)
    if role == "boy":
        u = smooth(t/1.48)
        return 1380 - 412*u, (t < 1.48)
    if role == "mom":
        u = smooth((t-3.0)/1.35)
        return 1370 - 78*u, 3.0 < t < 4.35
    u = smooth((t-7.10)/1.20)
    return 1640 - 95*u, 7.10 < t < 8.30


def pose(role: str, t: float):
    x, walking = footfall(role,t)
    scale = SCALE[role]
    c = ref.base(x=x,s=scale,t=t)
    c.update(walk=walking, stride=85 if role in ("boy","girl") else 106,
             silent_mouth=False, lean=0.0, nod=0.0, bend_near=1, bend_far=-1)
    targets = {}
    ground_phase = ref.gait_phase(c) * math.tau
    c["lean"] = 2.1 * math.sin(t*1.45 + (0 if role=="dad" else 1.1))
    if walking:
        c["lean"] += 5 * (1 if role=="dad" else -1)
    if role == "dad":
        c["nod"] = -3.0*math.sin(t*1.6) if t<3.4 else 5*math.sin(t*.8)
        if 1.0 < t < 3.36:
            u = smooth((t-1.0)/.35)*(1-smooth((t-3.0)/.36))
            p = ref.geom(c)[1]
            targets["near"] = p((-170,-90)) * u + p((-95,80))*(1-u)
            c["bend_near"] = -1
            c["hand_pose_near"] = "palm"
        if t>8.7: c["nod"] += 8*math.sin((t-8.7)*4)
    elif role == "mom":
        c["nod"] = -4*math.sin(t*1.4)
        if 4.0<t<7.3:
            u=smooth((t-4.0)/.6)*(1-smooth((t-6.7)/.5))
            p = ref.geom(c)[1]
            targets["near"] = p((-155,-82))*u + p((-85,58))*(1-u)
            c["bend_near"] = -1
            c["hand_pose_near"] = "palm"
        if t>8.6:c["nod"]=-4
    elif role == "boy":
        c["nod"] = 4*math.sin(t*3) if walking else 3*math.sin(t*1.1)
        if t>7.9:
            u=smooth((t-7.9)/.36)
            p=ref.geom(c)[1]
            targets["near"] = p((-125,-58))*u+p((-78,65))*(1-u)
            c["bend_near"] = -1
            c["nod"] += 6*math.sin((t-8)*3)
            c["hand_pose_near"]="palm"
    elif role == "girl":
        c["nod"] = 2.5*math.sin(t*1.5)
        if t>8.2:
            p=ref.geom(c)[1]
            u=smooth((t-8.2)/.4)
            targets["near"] = p((-145,-92))*u + p((-85,65))*(1-u)
            c["bend_near"]=-1
            c["hand_pose_near"]="palm"
    # Exact scene audio drives eight different mouth configurations.
    c["mouth_shape"] = viseme_at(t,role)
    offsets={"dad":.0,"mom":1.05,"boy":1.98,"girl":2.55}
    c["eyes_closed"] = ((t+offsets[role])%3.85)<.11
    c["gaze"] = ({"dad":.6,"mom":-.4,"boy":-.5,"girl":-.7}[role]
                 + .30*math.sin(1.7*t+offsets[role]))
    return c,targets


def puppet(im: Image.Image, t: float, role: str):
    """Reference film's joint system, unchanged mathematically, role-aware art."""
    c, targets = pose(role,t)
    all_parts = parts_for(role)
    darker = dark_for(role)
    root,p,neck,head_angle,_ = ref.geom(c)
    scale = c["s"]
    angle=ref.angle
    place=ref.place
    for side in ("far","near"):
        hip_offset=-35 if side=="far" else 36
        hip=root+ref.rot(np.array([hip_offset,70])*scale,0)
        pictures=darker if side=="far" else all_parts
        if c.get("walk"):
            q=(ref.gait_phase(c)+(0 if side=="near" else .5))%1
            stride=c["stride"]
            if q<.62:
                dx=stride*(.5-q/.62);lift=0
            else:
                u=(q-.62)/.38
                dx=stride*(-.5+ref.ease(u))
                lift=35*math.sin(math.pi*u)**2
            ankle=np.array([root[0]+hip_offset*scale+dx, GROUND-38*scale-lift])
        else:
            ankle=np.array([root[0]+hip_offset*scale+16*scale,GROUND-38*scale])
        knee,ankle=ref.ik(hip,ankle,200*scale,195*scale,-1)
        # Painted trouser layers hide the joint; no detached segment edges.
        knee_fill = PANTS[role]
        ImageDraw.Draw(im).ellipse((knee[0]-28*scale,knee[1]-29*scale,
                                    knee[0]+28*scale,knee[1]+29*scale),
                                   fill=knee_fill+(255,))
        place(im,pictures["thigh"],(44,15),hip,angle(knee-hip),scale)
        place(im,pictures["shin"],(38,14),knee,angle(ankle-knee),scale)
        place(im,pictures["foot"],(34,40),ankle,0,scale)
    place(im,all_parts["pelvis"],(95,8),root,0,scale)

    def arm(side):
        pictures=darker if side=="far" else all_parts
        shoulder=p((52,-183) if side=="far" else (-55,-184))
        if side in targets:
            wrist=np.asarray(targets[side])
        else:
            swing=26*math.sin(ref.gait_phase(c)*math.tau)*(1 if side=="near" else -1) if c["walk"] else 0
            wrist=shoulder+ref.rot((0,260*scale),c.get("arm_"+side,swing)+c["lean"])
        elbow,wrist=ref.ik(shoulder,wrist,143*scale,138*scale,
                           c.get("bend_"+side,1 if side=="near" else -1))
        ink=SKIN[role]
        ImageDraw.Draw(im).ellipse((elbow[0]-19*scale,elbow[1]-20*scale,
                                    elbow[0]+19*scale,elbow[1]+20*scale),
                                   fill=ink+(255,))
        # Reuse the reference's bone anchoring points and mirrored far limb.
        def bone(name, start, end, source_a,source_b):
            pic=pictures[name]
            pa=np.asarray(source_a,float);pb=np.asarray(source_b,float)
            if side=="far":
                pic=ImageOps.mirror(pic)
                pa[0]=pic.width-1-pa[0];pb[0]=pic.width-1-pb[0]
            vector=end-start
            place(im,pic,pa,start,angle(vector)-angle(pb-pa),
                  np.linalg.norm(vector)/np.linalg.norm(pb-pa))
        bone("forearm",elbow,wrist,(25,10),(31,148))
        bone("upper_arm",shoulder,elbow,(37,12),(27,155))
        hand,pivot=ref.hand_sprite(side,False,c.get("hand_pose_"+side))
        place(im,hand,pivot,wrist,ref.wrist_angle(angle(wrist-elbow)),scale*.83)

    arm("far")
    place(im,all_parts["torso"],(100,225),p((0,-2)),c["lean"],scale)
    face=face_sprite(role,c["mouth_shape"],c["eyes_closed"],round(c["gaze"]*10))
    place(im,face,FACE[role]["pivot"],neck,head_angle,scale)
    arm("near")


@lru_cache(maxsize=1)
def garden():
    return Image.open(REFERENCE/"assets"/"backgrounds"/"garden.png").convert("RGBA").resize((W,H))


@lru_cache(maxsize=4)
def font(size,bold=False):
    style="DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(str(REFERENCE/"assets"/"fonts"/style),size)


def crop_camera(im,t):
    # A small directed shot sequence, with reaction cuts rather than static
    # wide compositions; cuts are aligned to dialogue and gesture beats.
    if t<1.55:
        zoom,cx,cy=1.0,960,525
    elif t<3.58:
        zoom,cx,cy=1.46,565,315
    elif t<4.35:
        zoom,cx,cy=1.12,970,560
    elif t<7.32:
        zoom,cx,cy=1.72,1370,345
    elif t<7.97:
        zoom,cx,cy=1.05,1030,560
    elif t<9.55:
        zoom,cx,cy=2.0,1250,365
    else:
        zoom,cx,cy=1.0,960,540
    zoom+=.016*math.sin(t*.6)
    width,height=W/zoom,H/zoom
    left=max(0,min(W-width,cx-width/2))
    top=max(0,min(H-height,cy-height/2))
    return im.crop((round(left),round(top),round(left+width),round(top+height))).resize((W,H),Image.Resampling.BICUBIC)


def frame(t):
    stage=garden().copy()
    shadow_layer=Image.new("RGBA",(W,H))
    for role in ("dad","mom","boy","girl"):
        c,_=pose(role,t)
        radius=75*c["s"]/.75
        ImageDraw.Draw(shadow_layer).ellipse((c["x"]-radius,GROUND-5,
                                             c["x"]+radius,GROUND+11),
                                            fill=(82,57,31,72))
    shadow_layer=shadow_layer.filter(ImageFilter.GaussianBlur(12))
    stage.alpha_composite(shadow_layer)
    # Scene-depth order by feet, independent of who speaks.
    for role in ("dad","mom","boy","girl"):
        puppet(stage,t,role)
    stage=crop_camera(stage,t)
    # Captions retain the original speaker's words, no clunky black box.
    line=active_line(t)
    if line:
        d=ImageDraw.Draw(stage)
        subtitle=line["text"]
        size=44
        while d.textlength(subtitle,font=font(size,True))>W-240:size-=2
        bbox=d.textbbox((W//2,985),subtitle,font=font(size,True),anchor="mm",stroke_width=3)
        d.rounded_rectangle((bbox[0]-23,bbox[1]-11,bbox[2]+23,bbox[3]+12),
                            radius=21,fill=(255,249,238,224))
        d.text((W//2,985),subtitle,font=font(size,True),anchor="mm",
               fill="#493b31",stroke_width=0)
    return stage.convert("RGB")


def render_preview():
    OUT.mkdir(parents=True,exist_ok=True)
    sample_times=(0.0,.55,1.2,2.1,3.1,4.8,5.9,7.3,8.35,9.0,9.9)
    sheet=Image.new("RGB",(1440,4*270),"white")
    for i,t in enumerate(sample_times):
        pic=frame(t)
        pic.save(OUT/f"rigged_{t:04.1f}.jpg",quality=91)
        x=(i%3)*480;y=(i//3)*270
        sheet.paste(pic.resize((480,270),Image.Resampling.BICUBIC),(x,y))
    sheet.save(OUT/"Ten_Second_Rigged_Contact_Sheet.jpg",quality=92)
    return OUT/"Ten_Second_Rigged_Contact_Sheet.jpg"


def render_video():
    OUT.mkdir(parents=True,exist_ok=True)
    silent=OUT/"rigged_silent.mp4"
    result=OUT/"Ten_Second_Family_Articulated_Reference_Style.mp4"
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}",
         "-r",str(FPS),"-i","pipe:0","-an","-c:v","libx264",
         "-preset","veryfast","-crf","20","-threads","2",
         "-pix_fmt","yuv420p","-frames:v",str(FPS*10),str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    begin=time.monotonic()
    try:
        for i in range(FPS*10):
            proc.stdin.write(frame(i/FPS).tobytes())
            if (i+1)%48==0:
                print(f"  articulated {i+1}/240 frames ({time.monotonic()-begin:.0f}s)",flush=True)
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError("H264 render failed")
    except BaseException:
        proc.kill()
        raise
    # Original four-voice 120s master provides authentic dialogue timing.
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-i",str(silent),"-i",str(EPISODE/"audio"/"narration_master.flac"),
         "-i",str(EPISODE/"audio"/"premium_foley.wav"),
         "-filter_complex","[1:a]atrim=0:10,asetpts=PTS-STARTPTS[voice];"
                           "[2:a]atrim=0:10,asetpts=PTS-STARTPTS,volume=0.18[fx];"
                           "[voice][fx]amix=inputs=2:duration=first:dropout_transition=0,"
                           "alimiter=limit=0.94[a]",
         "-map","0:v:0","-map","[a]","-c:v","copy","-c:a","aac",
         "-b:a","192k","-ar","48000","-t","10","-movflags","+faststart",str(result)]
    subprocess.run(cmd,check=True)
    print(f"Render completed in {time.monotonic()-begin:.1f}s: {result}")
    return result


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--preview",action="store_true")
    ap.add_argument("--still",type=float)
    args=ap.parse_args()
    if args.preview:
        print(render_preview())
    elif args.still is not None:
        OUT.mkdir(parents=True,exist_ok=True)
        image=OUT/"rigged_still.png"
        frame(args.still).save(image)
        print(image)
    else:
        render_video()
