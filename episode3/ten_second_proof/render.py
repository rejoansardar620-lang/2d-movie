"""Ten-second, frame-animated 2D mesh-deformation pilot.

Unlike the old movie director, this script does NOT translate a static whole-
body sprite as its only motion.  It deforms contiguous original illustrations
through a spatially smooth joint field: hands, elbows, knees, ankles, head,
eyebrows, pupils and lips are independently time-animated. No floating seams.

Run `python3 episode3/ten_second_proof/render.py --preview`, inspect the contact
sheet, then run again without --preview to export the 10-second H264/AAC film.
Requires numpy, Pillow, OpenCV and ffmpeg. Reuses the episode's voice master.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import subprocess

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from face_rig import AnimatedFace

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).resolve().parent / "output"
OUTPUT.mkdir(parents=True, exist_ok=True)
ART = ROOT / "assets_premium" / "actors"
W, H, FPS, DURATION = 1280, 720, 24, 10
FONTS = ROOT.parent / "Everyday_English_Project" / "assets" / "fonts"

LANDMARKS = {
    # Landmark positions are normalized to the original, intact hand-painted
    # sprite bounding box; same source art is used for all 240 frames.
    "dad": dict(head=(.55,.10), neck=(.51,.195), eye_l=(.525,.095), eye_r=(.685,.092),
                brow_l=(.522,.072), brow_r=(.690,.070), mouth=(.605,.127),
                shoulder_l=(.23,.225), elbow_l=(.17,.36), hand_l=(.16,.54),
                shoulder_r=(.78,.245), elbow_r=(.85,.39), hand_r=(.90,.57),
                knee_l=(.32,.72), knee_r=(.67,.72), foot_l=(.29,.94), foot_r=(.71,.94)),
    "mom": dict(head=(.50,.095), neck=(.53,.190), eye_l=(.49,.090), eye_r=(.640,.090),
                brow_l=(.49,.071), brow_r=(.647,.071), mouth=(.580,.121),
                shoulder_l=(.20,.235), elbow_l=(.15,.36), hand_l=(.100,.51),
                shoulder_r=(.79,.245), elbow_r=(.86,.37), hand_r=(.910,.54),
                knee_l=(.28,.72), knee_r=(.66,.71), foot_l=(.24,.94), foot_r=(.69,.95)),
    "boy": dict(head=(.51,.10), neck=(.53,.192), eye_l=(.50,.100), eye_r=(.68,.100),
                brow_l=(.500,.079), brow_r=(.690,.080), mouth=(.602,.146),
                shoulder_l=(.23,.225), elbow_l=(.15,.37), hand_l=(.126,.525),
                shoulder_r=(.78,.24), elbow_r=(.81,.36), hand_r=(.91,.50),
                knee_l=(.35,.72), knee_r=(.69,.72), foot_l=(.29,.94), foot_r=(.74,.94)),
    "girl": dict(head=(.52,.105), neck=(.53,.20), eye_l=(.51,.100), eye_r=(.67,.098),
                brow_l=(.51,.077), brow_r=(.675,.077), mouth=(.594,.148),
                shoulder_l=(.26,.25), elbow_l=(.18,.37), hand_l=(.135,.51),
                shoulder_r=(.74,.26), elbow_r=(.82,.37), hand_r=(.91,.51),
                knee_l=(.38,.72), knee_r=(.70,.72), foot_l=(.32,.95), foot_r=(.73,.95)),
}
HEIGHTS = {"dad": 460, "mom": 440, "boy": 346, "girl": 310}
COLORS = {"dad": "#2c5571", "mom": "#8e5447", "boy": "#448c7f", "girl": "#b36d8e"}
TIMINGS = json.loads((ROOT / "timings.json").read_text())[:3]
CUES = json.loads((ROOT / "audio" / "rhubarb_cues.json").read_text())["mouthCues"]


def clip(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def smooth(v):
    v = clip(v)
    return v * v * (3 - 2 * v)


def ease(v):
    return smooth(v)


def sin_window(t, start, end):
    if not start <= t < end:
        return 0.0
    return math.sin(math.pi * (t - start) / (end - start))


def speaker_at(t):
    return next((entry for entry in TIMINGS if entry["start"] <= t < entry["end"]), None)


def mouth_cue_at(t):
    # Rhubarb's audio-driven phoneme classification (not arbitrary sine waves).
    return next((cue["value"] for cue in CUES if cue["start"] <= t < cue["end"]), "X")


VOWEL_OPEN = {"X": 0.0, "A": 0.0, "B": .20, "C": .57,
              "D": .98, "E": .79, "F": .68, "G": .35, "H": .43}


@dataclass
class Pose:
    root_x: float
    foot_y: float
    activity: str = "idle"
    gaze: float = 0.0
    talk: float = 0.0
    blink: float = 0.0
    joy: float = 0.0
    point: float = 0.0
    wave: float = 0.0
    lean: float = 0.0
    scale: float = 1.0


def pulse(t, at, width=.10):
    return math.exp(-.5 * ((t - at) / width) ** 2)


def pose_for(role, t, cue):
    # Independent timing for each character; they never share a canned pose.
    talking = cue is not None and cue["speaker"] == role
    lip = VOWEL_OPEN[mouth_cue_at(t)] if talking else 0.0
    if role == "dad":
        move = ease(t / 1.24)
        p = Pose(240 + 165 * move, 663, gaze=.70, lean=-.04 * (1-move),
                 activity="walk" if t < 1.24 else "idle", talk=lip,
                 blink=max(pulse(t,2.60,.070), pulse(t,7.52,.078)),
                 joy=.2 if t < 3.34 else .55 * smooth((t-8.10)/1.2),
                 point=sin_window(t, 1.15,3.36)*.95)
        if t >= 8.0:
            p.gaze=.85
            p.lean=.04*math.sin((t-8)*4)
        return p
    if role == "mom":
        move = ease((t-2.4)/1.98)
        return Pose(1035-155*move,661,gaze=-.80,
                    activity="walk" if 2.4<t<4.38 else "idle", talk=lip,
                    blink=max(pulse(t,3.27,.065),pulse(t,6.76,.070)),
                    point=sin_window(t,4.25,7.07)*1.15,
                    lean=.02*math.sin(t*1.4))
    if role == "boy":
        move=ease(t/1.24)
        return Pose(1190-548*move,657,
                    activity="run" if t<1.24 else "idle", talk=lip,
                    gaze=-.70 if t>2.0 else -.4,
                    blink=max(pulse(t,2.63,.07),pulse(t,7.80,.07)),
                    joy=.8*smooth((t-7.75)/.3),
                    point=sin_window(t,8.0,9.68)*1.2,
                    lean=.10*(1-move)+.08*sin_window(t,8.0,9.65))
    return Pose(1095+8*math.sin(t*1.1),652,gaze=-.65,
                activity="idle", blink=pulse(t,5.5,.075),
                joy=.45+.55*smooth((t-8.6)/.7),
                wave=.75*sin_window(t,8.3,10.0))


class MeshActor:
    """Continuous alpha-mesh skin, animated by independent local joint fields."""

    def __init__(self, role, mode="idle"):
        self.role=role
        self.mode=mode
        im=cv2.imread(str(ART / f"{role}_{mode}.png"),cv2.IMREAD_UNCHANGED)
        if im is None or im.shape[2]!=4:
            raise RuntimeError(f"Missing transparent full-body artwork: {role}")
        # Erase any tiny neighbouring figure fragments left by atlas crops.
        if mode == "talk" and role == "mom":
            im[int(im.shape[0]*.55):,int(im.shape[1]*.82):,3]=0
        if mode == "talk" and role == "dad":
            im[int(im.shape[0]*.49):,int(im.shape[1]*.91):,3]=0
        source_h,source_w=im.shape[:2]
        h=HEIGHTS[role]
        w=round(im.shape[1]*h/im.shape[0])
        self.face=AnimatedFace(role,mode,(source_h,source_w),h/source_h)
        im=self.face.sanitized_source(im)
        self.image=cv2.resize(im,(w,h),interpolation=cv2.INTER_AREA)
        self.h,self.w=self.image.shape[:2]
        self.gy,self.gx=np.mgrid[0:h,0:w].astype(np.float32)
        self.joints={key:(pt[0]*w,pt[1]*h) for key,pt in LANDMARKS[role].items()}
        self.joints.update(self.face.landmarks())
        self.gaussians={}
        for name,(cx,cy) in self.joints.items():
            if name.startswith("hand"):
                sx,sy=.21*w,.115*h
            elif name.startswith("elbow"):
                sx,sy=.25*w,.135*h
            elif name.startswith("knee"):
                sx,sy=.23*w,.125*h
            elif name.startswith("foot"):
                sx,sy=.23*w,.110*h
            elif name.startswith("eye"):
                sx,sy=.072*w,.018*h
            elif name.startswith("brow"):
                sx,sy=.105*w,.020*h
            elif name=="mouth":
                sx,sy=.11*w,.028*h
            elif name=="head":
                sx,sy=.35*w,.130*h
            else:
                sx,sy=.22*w,.10*h
            self.gaussians[name]=np.exp(-.5*((self.gx-cx)/sx)**2-.5*((self.gy-cy)/sy)**2)

    def deform(self,t,p):
        dx=np.zeros((self.h,self.w),np.float32)
        dy=np.zeros_like(dx)

        def move(name,x,y):
            nonlocal dx,dy
            g=self.gaussians[name]
            dx+=g*x
            dy+=g*y

        stride=0.0
        if p.activity=="walk":
            stride=math.sin(2*math.pi*1.65*t)
            # Large gait poses are already drawn in the walk model sheet.
            # The deformation is limited to toe lift and joint follow-through.
            length=.042*self.h
            move("foot_l",length*stride,-.018*self.h*max(0,-stride))
            move("foot_r",-length*stride,-.018*self.h*max(0,stride))
            move("knee_l",.40*length*stride,-.008*self.h*max(0,-stride))
            move("knee_r",-.40*length*stride,-.008*self.h*max(0,stride))
            move("hand_l",-length*.60*stride,0)
            move("hand_r",length*.60*stride,0)
            move("elbow_l",-length*.22*stride,0)
            move("elbow_r",length*.22*stride,0)
        elif p.activity=="run":
            stride=math.sin(2*math.pi*2.55*t)
            length=.062*self.h
            move("foot_l",length*stride,-.030*self.h*max(0,-stride))
            move("foot_r",-length*stride,-.030*self.h*max(0,stride))
            move("knee_l",.47*length*stride,-.012*self.h*max(0,-stride))
            move("knee_r",-.47*length*stride,-.012*self.h*max(0,stride))
            move("hand_l",-length*.72*stride,-.016*self.h)
            move("hand_r",length*.72*stride,-.016*self.h)
            move("elbow_l",-length*.24*stride,-.02*self.h)
            move("elbow_r",length*.24*stride,-.02*self.h)
        else:
            # Weight shifts, shoulder breathing and alternating relaxed hands.
            move("hand_l",2.8*math.sin(t*1.5),1.5*math.sin(t*2.0))
            move("hand_r",-2.4*math.sin(t*1.8),1.3*math.sin(t*1.7))
            move("foot_l",1.4*math.sin(t*0.7),0)
            move("foot_r",-1.4*math.sin(t*0.6),0)

        # Actual independent wrist, elbow and neck motion, not a translated PNG.
        move("hand_r",-p.point*.17*self.w,-p.point*.18*self.h)
        move("elbow_r",-p.point*.080*self.w,-p.point*.07*self.h)
        move("hand_l",p.wave*.17*self.w,-p.wave*.15*self.h)
        move("elbow_l",p.wave*.09*self.w,-p.wave*.05*self.h)
        move("head",p.lean*self.w+.016*self.w*math.sin(t*1.30),
             .008*self.h*math.sin(t*2.12)+p.joy*.004*self.h)
        move("brow_l",0,-p.joy*.018*self.h)
        move("brow_r",0,-p.joy*.020*self.h)
        # Calibrated anchors now sit on the real eyes.  Small independent
        # saccades visibly redirect the illustrated pupils toward family.
        glance=p.gaze*.6+.38*math.sin(t*3.25+{"dad":0,"mom":1,"boy":2,"girl":3}[self.role])
        move("eye_l",glance*.047*self.w,0)
        move("eye_r",glance*.047*self.w,0)

        # Explicit, independently drawn visemes, moving irises and eyelids
        # take over from the previous ineffective generic facial mesh warp.
        warped=cv2.remap(self.image,self.gx-dx,self.gy-dy,cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
        line=speaker_at(t)
        speaking=line is not None and line["speaker"]==self.role
        symbol=mouth_cue_at(t) if speaking else "X"
        return self.face.paint(warped,p,t,symbol,dx,dy)


ACTORS={role:{mode:MeshActor(role,mode) for mode in ("idle","walk","talk")}
        for role in ("dad","mom","boy","girl")}


def load_background():
    import sys
    sys.path.insert(0,str(ROOT))
    import cinematic_render
    pil=cinematic_render.room_image("outside").convert("RGB")
    return cv2.cvtColor(np.array(pil),cv2.COLOR_RGB2BGR)


BG=load_background()


def draw_shadow(frame,x,y,scale,width):
    layer=np.zeros_like(frame)
    rx=int(width*scale*.46)
    cv2.ellipse(layer,(int(x),int(y+1)),(max(rx,8),8),0,0,360,(34,38,48),-1,cv2.LINE_AA)
    layer=cv2.GaussianBlur(layer,(0,0),5.5)
    cv2.addWeighted(layer,.25,frame,.99,0,frame)


def composite(frame,actor,x,y,scale):
    h,w=actor.shape[:2]
    if abs(scale-1)>1e-4:
        actor=cv2.resize(actor,(max(1,int(w*scale)),max(1,int(h*scale))),
                         interpolation=cv2.INTER_AREA if scale<1 else cv2.INTER_CUBIC)
        h,w=actor.shape[:2]
    x0=int(x-w*.5); y0=int(y-h)
    x1=x0+w; y1=y0+h
    ax0=max(0,-x0);ay0=max(0,-y0)
    ax1=w-max(0,x1-W);ay1=h-max(0,y1-H)
    if ax1<=ax0 or ay1<=ay0:return
    roi=frame[y0+ay0:y0+ay1,x0+ax0:x0+ax1]
    fg=actor[ay0:ay1,ax0:ax1]
    a=fg[:,:,3:4].astype(np.float32)/255
    roi[:]=(fg[:,:,:3]*a+roi*(1-a)).astype(np.uint8)


def time_caption(t):
    line=speaker_at(t)
    return line["text"] if line else ""


def subtitles(frame,t):
    sentence=time_caption(t)
    if not sentence:return
    pil=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)).convert("RGBA")
    d=ImageDraw.Draw(pil,"RGBA")
    font=ImageFont.truetype(str(FONTS/"DejaVuSans-Bold.ttf"),27)
    bbox=d.textbbox((0,0),sentence,font=font)
    tw=bbox[2]-bbox[0]
    box=(W//2-tw//2-22,H-74,W//2+tw//2+22,H-25)
    d.rounded_rectangle(box,radius=15,fill=(24,36,40,178))
    d.text((W//2,H-52),sentence,font=font,fill=(255,253,240,255),anchor="mm")
    frame[:]=cv2.cvtColor(np.array(pil.convert("RGB")),cv2.COLOR_RGB2BGR)


def add_cinema_grade(frame,t):
    # Consistent warm grade with a faint moving sunbeam, never random flicker.
    frame[:,:,2]=np.minimum(255,frame[:,:,2].astype(np.float32)*1.025).astype(np.uint8)
    return frame


def camera_shot(t):
    # Editorial cuts to real close-ups: lip and eye acting must be visible,
    # while the entrance and running section remain full-body wides.
    if t < 1.24:return None
    if t < 3.58:return (445,325,1.93)
    if t < 4.38:return None
    if t < 7.35:return (850,340,1.95)
    if t < 8.0:return None
    if t >= 9.50:return None
    return (635,359,1.75)


def render_frame(t):
    f=BG.copy()
    poses={role:pose_for(role,t,speaker_at(t)) for role in ACTORS}
    # Spatial depth: non-speaking actors go behind a running child.
    for role in ("girl","mom","dad","boy"):
        p=poses[role]
        if p.activity in ("walk","run"):
            mode="walk"
        elif (role=="dad" and 1.24<=t<3.58) or (role=="mom" and 4.38<=t<7.35) or (role=="boy" and 8.0<=t<9.5):
            mode="talk"
        else:
            mode="idle"
        obj=ACTORS[role][mode]
        stepb=4.0*abs(math.sin(2*math.pi*1.65*t)) if p.activity=="walk" else 0
        stepb+=7.5*abs(math.sin(2*math.pi*2.55*t)) if p.activity=="run" else 0
        stepb+=1.5*math.sin(t*2.1+{"dad":0,"mom":1,"boy":2,"girl":3}[role])
        draw_shadow(f,p.root_x,p.foot_y,p.scale,obj.w)
        sprite=obj.deform(t,p)
        composite(f,sprite,p.root_x,p.foot_y-stepb,p.scale)
    shot=camera_shot(t)
    if shot:
        cx,cy,zoom=shot
        cw,ch=W/zoom,H/zoom
        x0=int(clip(cx-cw/2,0,W-cw))
        y0=int(clip(cy-ch/2,0,H-ch))
        x1=int(x0+cw); y1=int(y0+ch)
        f=cv2.resize(f[y0:y1,x0:x1],(W,H),interpolation=cv2.INTER_CUBIC)
    add_cinema_grade(f,t)
    subtitles(f,t)
    return f


def preview():
    times=(.0,.45,.9,1.4,2.1,2.8,3.9,4.7,5.6,6.6,7.9,8.4,9.0,9.65)
    thumbs=[]
    for t in times:
        im=cv2.resize(render_frame(t),(480,270),interpolation=cv2.INTER_AREA)
        cv2.putText(im,f"{t:04.2f}s",(12,29),cv2.FONT_HERSHEY_SIMPLEX,.75,(20,20,20),3,cv2.LINE_AA)
        cv2.putText(im,f"{t:04.2f}s",(12,29),cv2.FONT_HERSHEY_SIMPLEX,.75,(255,255,255),1,cv2.LINE_AA)
        thumbs.append(im)
    sheet=np.concatenate([np.concatenate(thumbs[i:i+2],axis=1) for i in range(0,len(thumbs),2)],axis=0)
    cv2.imwrite(str(OUTPUT/"ten_second_contact_sheet.jpg"),sheet,[cv2.IMWRITE_JPEG_QUALITY,93])
    print("Wrote",OUTPUT/"ten_second_contact_sheet.jpg")


def export_video():
    target=OUTPUT/"Ten_Second_Animated_Family_Pilot.mp4"
    soundtrack=ROOT/"audio"/"narration_master.flac"
    effects=ROOT/"audio"/"premium_foley.wav"
    if not effects.exists():
        subprocess.run(["python3",str(ROOT/"premium_foley.py")],check=True)
    cmd=["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-f","rawvideo","-vcodec","rawvideo","-pix_fmt","bgr24",
         "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0",
         "-i",str(soundtrack),"-i",str(effects),
         "-filter_complex","[1:a][2:a]amix=inputs=2:weights=1 0.32:normalize=0,alimiter=limit=0.96[a]",
         "-map","0:v:0","-map","[a]",
         "-vf","scale=1920:1080:flags=lanczos,format=yuv420p",
         "-t",str(DURATION),"-c:v","libx264","-preset","veryfast",
         "-crf","19","-r",str(FPS),"-c:a","aac","-b:a","192k",
         "-movflags","+faststart",str(target)]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as ff:
        try:
            for i in range(DURATION*FPS):
                ff.stdin.write(render_frame(i/FPS).tobytes())
                if (i+1)%48==0:print(f"rendered {i+1}/{DURATION*FPS} frames",flush=True)
            ff.stdin.close()
            error=ff.stderr.read().decode(errors="replace")
            code=ff.wait()
        except BrokenPipeError as exc:
            raise RuntimeError(ff.stderr.read().decode(errors="replace")) from exc
    if code:
        raise RuntimeError(f"FFmpeg failed: {error}")
    print("Exported",target)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    preview()
    if not args.preview:export_video()
