"""Film-first, anatomically coherent 120-second family adventure (2026 revision).

The earlier cutout head/neck problem is solved at the ART level: every pose is
one connected, hand-painted full-body sprite. Only whole-figure pose keyframes
are swapped, never independently positioned heads, shoulders, wrists or hips.
Botanical species use individually illustrated transparent artwork. A shot
director stages real inserts, response shots, walk-ins, pond views and camera
movements rather than an all-cast classroom chart.

Run: python3 episode3/premium_render.py --preview
     python3 episode3/premium_render.py
Requires Pillow, numpy, ffmpeg; reuses this episode's saved narration/audio.
"""
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
import argparse
import json
import math
import subprocess

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

import cinematic_render as old
import render_episode as art

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / 'assets_premium'
OUTPUT = ROOT / 'output'
OUTPUT.mkdir(exist_ok=True)
STORY = json.loads((ROOT / 'story.json').read_text())
LINES = json.loads((ROOT / 'timings.json').read_text())
CUES = json.loads((ROOT / 'audio/rhubarb_cues.json').read_text())['mouthCues']
STARTS = [x['start'] for x in LINES]
CUE_STARTS = [x['start'] for x in CUES]
ROOMS = ('drawing_room',)*3 + ('kitchen',)*3 + ('balcony',)*3 + ('outside',)*3
WORDS = (None, 'rose', 'sunflower', 'tulip', 'daisy', 'lily', 'marigold',
         'lotus', 'hibiscus', 'orchid', 'jasmine', None)
W, H, FPS = 1280, 720, 24
ROLES = ('dad', 'mom', 'boy', 'girl')
SIZES = {'dad':427, 'mom':415, 'boy':315, 'girl':291}
COLORS = {'dad':'#638ea8','mom':'#bf8569','boy':'#4e9b90','girl':'#b777a0'}
PARTNERS = {'dad':'boy','mom':'girl','boy':'dad','girl':'mom'}

# Every room has deliberate floor/blocking marks. Wide shots hold the cast on
# distinct depths; dialogue shots favor two-shot eyelines instead of a roll call.
MARKS = [
    {'dad':238,'mom':1010,'boy':515,'girl':780},
    {'dad':230,'mom':990,'boy':485,'girl':768},
    {'dad':250,'mom':1010,'boy':610,'girl':815},
    {'dad':245,'mom':985,'boy':560,'girl':815},
    {'dad':270,'mom':945,'boy':590,'girl':786},
    {'dad':280,'mom':966,'boy':550,'girl':813},
    {'dad':238,'mom':950,'boy':575,'girl':785},
    {'dad':188,'mom':646,'boy':383,'girl':548},
    {'dad':238,'mom':956,'boy':545,'girl':799},
    {'dad':257,'mom':970,'boy':582,'girl':810},
    {'dad':241,'mom':964,'boy':558,'girl':800},
    {'dad':260,'mom':976,'boy':584,'girl':795},
]

def bound(v, a=0.0, b=1.0): return max(a,min(b,v))
def smooth(v):
    v=bound(v)
    return v*v*(3-2*v)
def ftext(n, bold=False): return art.font(n, bold)


def speaking(t):
    i=bisect_right(STARTS,t)-1
    return LINES[i] if i>=0 and t<LINES[i]['end'] else None


def viseme(t):
    i=bisect_right(CUE_STARTS,t)-1
    if i<0 or t>=CUES[i]['end']:
        return 'X'
    return CUES[i]['value']


@lru_cache(maxsize=80)
def pose_image(role, mode, direction):
    f=ASSETS/'actors'/f'{role}_{mode}.png'
    im=Image.open(f).convert('RGBA')
    scale=SIZES[role]/im.height
    size=(max(1,round(im.width*scale)),SIZES[role])
    im=im.resize(size,Image.Resampling.LANCZOS)
    if direction=='left': im=ImageOps.mirror(im)
    return im


@lru_cache(maxsize=30)
def botanical(name, height):
    im=Image.open(ASSETS/'flowers'/f'{name}.png').convert('RGBA')
    return im.resize((round(im.width*height/im.height),height),Image.Resampling.LANCZOS)


@lru_cache(maxsize=20)
def sway_plant(name, height, angle):
    # Animates an entire connected species illustration; no geometry morphs.
    im=botanical(name,height)
    if angle:
        im=im.rotate(angle,Image.Resampling.BICUBIC,expand=True)
    return im


@lru_cache(maxsize=4)
def back(room):
    im=old.room_image(room).copy()
    if room=='balcony':
        # The balustrade is separately rendered *in front* of the actors.
        return im
    return im


@lru_cache(maxsize=1)
def film_glow():
    # Warm premium storybook light and gentle atmospheric lift.
    gl=Image.new('RGBA',(W,H),(0,0,0,0))
    pix=gl.load()
    for y in range(H):
        for x in range(W):
            v=(1-x/W)**2 * (1-y/H)**2
            pix[x,y]=(254,211,144,int(24*v))
    return gl


@lru_cache(maxsize=80)
def cast_shadow(width):
    pic=Image.new('RGBA',(width+70,46),(0,0,0,0))
    ImageDraw.Draw(pic).ellipse((15,12,width+56,32),fill=(63,42,27,72))
    return pic.filter(ImageFilter.GaussianBlur(11))


def stage_position(scene, role, local):
    x=MARKS[scene][role]
    if scene in (3,6,9):
        priority=('mom','dad','girl','boy') if scene==6 else ('dad','boy','girl','mom')
        rank=priority.index(role)
        delay=(0.0,.16,.31,.48)[rank]
        progress=smooth((local-delay)/2.65)
        starting_x=130-rank*155
        x=starting_x+(x-starting_x)*progress
    # Each scene gets independent physical blocking, not a locked lineup.
    elif scene==1 and role=='dad': x+=50*smooth((local-1.1)/3.2)
    elif scene==2 and role=='boy': x+=38*smooth((local-3.4)/3.5)
    elif scene==5 and role=='girl': x-=36*smooth((local-3.2)/3.3)
    elif scene==9 and role=='mom': x-=44*smooth((local-3.4)/3.4)
    elif scene==10 and role=='boy': x+=53*smooth((local-.8)/3.8)
    return x


def direction_for(scene, role, line):
    me=MARKS[scene][role]
    if line is None:
        other=MARKS[scene][PARTNERS[role]]
    elif role!=line['speaker']:
        other=MARKS[scene][line['speaker']]
    else:
        scene_lines=STORY['scenes'][scene]['lines']
        j=next((j for j,(who,text) in enumerate(scene_lines)
                if who==role and text==line['text']),0)
        next_person=scene_lines[j+1][0] if j<2 else scene_lines[j-1][0]
        other=MARKS[scene][next_person]
    return 'left' if other<me else 'right'


def actor_mode(scene,role,local,line):
    if scene in (3,6,9) and local < (3.05+{'dad':0,'mom':.50,'boy':.25,'girl':.32}[role]):
        return 'walk'
    if scene==11 and local>8.9:return 'talk'  # celebratory hands up
    if line and role==line['speaker']:return 'talk'
    if line and line['speaker'] in ('boy','girl') and role in ('dad','mom'):
        if local%4.0>3.40:return 'talk'  # timed parental chuckle
    if scene==5 and role=='girl' and 5.0<local<7.6:return 'talk' # gentle high-five
    if scene==9 and role=='mom' and 7.0<local<9.8:return 'talk' # elegant pose
    return 'idle'


def actor_sprite(role,mode,direction,t,line,scene):
    im=pose_image(role,mode,direction)
    # Cast remains a single opaque silhouette. Mouth cues are tiny local
    # modifications (never different full heads); disable painted lips in idle.
    if mode=='talk' and line and line['speaker']==role:
        cue=viseme(t)
        if cue!='X' and cue!='A':
            # Source mouth center fractions were measured on the output sprites.
            fraction={'dad':(.62,.118),'mom':(.48,.125),
                      'boy':(.56,.129),'girl':(.53,.132)}[role]
            mx=round(im.width*(1-fraction[0] if direction=='left' else fraction[0]))
            my=round(im.height*fraction[1])
            im=im.copy()
            d=ImageDraw.Draw(im)
            r=3 if cue in ('B','G') else 5 if cue in ('F','H') else 4
            d.ellipse((mx-r,my-2,mx+r,my+(3 if cue in ('B','G') else 7)),
                      fill=(114,53,53,205))
    return im


def flower_placement(scene, name):
    if scene==2: return (474,631,490)  # towering sunflower beside Dad
    if scene==7: return (1031,627,332) # aquatic lotus, no pot
    if scene==10:return (1044,593,325)
    return {'drawing_room':(1080,596,310),'kitchen':(1088,586,310),
            'balcony':(1072,607,318),'outside':(1073,620,346)}[ROOMS[scene]]


def water_garden(im,t):
    """Actual garden pond for the lotus: water, leaf, ripples, reflections."""
    d=ImageDraw.Draw(im,'RGBA')
    d.ellipse((810,488,1275,704), fill=(64,141,155,239),outline=(49,98,105,255),width=7)
    for j in range(9):
        y=518+j*17
        d.arc((841,y,1220,y+58),200,345,fill=(196,244,240,90),width=3)
    d.ellipse((902,559,1128,654),fill=(74,133,78,235),outline=(47,100,56,255),width=4)
    d.pieslice((903,561,1127,654),318,350,fill=(66,147,162,245))
    for x in range(820,1240,160):
        phase=math.sin(t*2.8+x*.01)*8
        d.arc((x-54,605+phase,x+65,642+phase),5,174,fill=(230,252,246,130),width=2)


def decor_for_scene(im,scene,t):
    d=ImageDraw.Draw(im,'RGBA')
    local=t-scene*10
    if scene==3 and local>5.05:
        # Translucent imagined tea cup, a brief child's visual daydream.
        alpha=round(175*smooth((local-5.05)/.35)*(1-smooth((local-8.0)/1.0)))
        if alpha>0:
            d.rounded_rectangle((974,445,1077,508),radius=17,
                                fill=(242,225,252,alpha),outline=(183,138,197,alpha),width=4)
            d.arc((1062,444,1122,503),290,70,fill=(225,201,241,alpha),width=6)
            for x,y in ((968,422),(1118,413),(1021,389)):
                d.line((x-7,y,x+7,y),fill=(250,244,196,alpha),width=3)
                d.line((x,y-7,x,y+7),fill=(250,244,196,alpha),width=3)
    if scene==6 and local>5.6:
        alpha=round(182*smooth((local-5.6)/.5)*(1-smooth((local-8.6)/.7)))
        for i,(x,y) in enumerate(((975,407),(1055,365),(1150,405))):
            if alpha>0:
                d.ellipse((x-18,y-18+math.sin(t*3+i)*5,x+18,y+18),
                          fill=(250,201,80,alpha),outline=(190,138,46,alpha),width=4)
                d.arc((x-8,y-12,x+12,y+10),30,315,fill=(171,119,38,alpha),width=3)
    if scene==10:
        alpha=round(110*(1-smooth((local-6.1)/2.2)))
        for i in range(4):
            x=948+i*22+int(6*math.sin(t*2+i))
            d.arc((x,360+i*11,x+29,394+i*11),192,330,
                  fill=(247,251,240,alpha),width=2)


def compose_stage(t,line=None):
    scene=min(11,int(t//10))
    local=t-scene*10
    room=ROOMS[scene]
    im=back(room).copy()
    if scene==7:water_garden(im,t)
    name=WORDS[scene]
    if name:
        x,base,height=flower_placement(scene,name)
        angle=round(2*math.sin(t*1.4))
        asset=sway_plant(name,height,angle)
        px=round(x-asset.width/2)
        py=round(base-asset.height-12+2*math.sin(t*1.4))
        # A painted planter is scene dressing only where botanically correct.
        if scene not in (7,9,10):
            d=ImageDraw.Draw(im,'RGBA')
            d.ellipse((x-51,base-34,x+51,base-17),fill=(170,113,83,240))
            d.polygon((x-45,base-27,x+45,base-27,x+36,base+23,x-37,base+23),
                      fill=(190,119,86,246))
        im.alpha_composite(asset,(px,py))
    if line is None:line=speaking(t)
    # Draw far-to-near; each pose is an UNBROKEN original whole-body painting.
    for role in ('dad','boy','girl','mom'):
        mode=actor_mode(scene,role,local,line)
        look=direction_for(scene,role,line)
        if mode=='walk': look='right'
        sprite=actor_sprite(role,mode,look,t,line,scene)
        x=stage_position(scene,role,local)
        foot=round(639 if room!='outside' else 647)
        if mode=='walk':foot-=round(2*abs(math.sin(t*11)))
        else:foot-=round(1.4*math.sin(t*(1.35+ROLES.index(role)*.1)))
        xx=round(x-sprite.width/2)
        yy=foot-sprite.height
        shadow=cast_shadow(sprite.width)
        im.alpha_composite(shadow,(xx-35,foot-20))
        im.alpha_composite(sprite,(xx,yy))
    if room=='balcony' and scene!=7:
        rail=old.balcony_front().copy()
        # Keep the rail low, not a wall hiding the children's lower bodies.
        rail.putalpha(rail.getchannel('A').point(lambda p:round(p*.44)))
        im.alpha_composite(rail)
    decor_for_scene(im,scene,t)
    im.alpha_composite(film_glow())
    return im


def camera_target(scene,t,line):
    local=t-scene*10
    name=WORDS[scene]
    if scene in (3,6,9) and local<3.2:
        return (640.0,359.0,1.02)
    if name and local<1.9:
        x,base,height=flower_placement(scene,name)
        return (float(x),420.0,1.61 if scene!=2 else 1.38)
    if scene==0 and local<3.2:
        return (640.0,357.0,1.02)
    if line:
        x=stage_position(scene,line['speaker'],local)
        partner=stage_position(scene,PARTNERS[line['speaker']],local)
        if line['speaker'] in ('boy','girl'):
            return (bound(x*.74+partner*.26,355,935),418.0,1.38)
        return (bound(x*.59+partner*.41,340,942),395.0,1.31)
    return (640.0,357.0,1.10)


def cinematic_camera(im,scene,t,line):
    local=t-scene*10
    target=camera_target(scene,t,line)
    # Different shot setups with intentionally smooth ~0.55s pans at a
    # dialogue change, without mechanically tracking every letter.
    if line:
        pos=LINES.index(line)
        prev=camera_target(scene,max(scene*10+.05,line['start']-.2),
                           LINES[pos-1] if pos>0 and LINES[pos-1]['scene']==scene else None)
        move=smooth((t-line['start'])/.50)
        target=tuple(prev[i]*(1-move)+target[i]*move for i in range(3))
    if WORDS[scene] and scene not in (3,6,9) and local>1.9 and local<2.55:
        flower=camera_target(scene,scene*10+.7,None)
        k=smooth((local-1.9)/.65)
        target=tuple(flower[i]*(1-k)+target[i]*k for i in range(3))
    x,y,z=target
    crop_w=W/z
    crop_h=H/z
    cx=bound(x-crop_w/2,0,W-crop_w)
    cy=bound(y-crop_h/2,0,H-crop_h)
    return im.crop((int(cx),int(cy),int(cx+crop_w),int(cy+crop_h))).resize(
        (W,H),Image.Resampling.BICUBIC)


def flower_title(im,name,local):
    if name is None or local>4.0:return
    opacity=round(245*smooth(local/.45)*(1-smooth((local-3.45)/.52)))
    if opacity==0:return
    label=name.upper()
    d=ImageDraw.Draw(im,'RGBA')
    f=ftext(30,True)
    tw=d.textbbox((0,0),label,font=f)[2]
    left=1114-tw
    d.rounded_rectangle((left-18,35,1145,83),radius=15,
                        fill=(255,248,231,round(opacity*.90)),
                        outline=(175,139,103,round(opacity*.85)),width=2)
    d.text((left,45),label,font=f,fill=(89,66,48,opacity))


def modern_caption(im,line,t):
    if not line:return
    elapsed=t-line['start']; left=line['end']-t
    alpha=round(250*smooth(elapsed/.12)*smooth(left/.14))
    if alpha<2:return
    words=line['text']
    d=ImageDraw.Draw(im,'RGBA')
    f=ftext(26,True)
    while f.size>19 and d.textbbox((0,0),words,font=f)[2]>1110:
        f=ftext(f.size-1,True)
    tw=d.textbbox((0,0),words,font=f)[2]
    x=(W-tw)/2
    # Thin low-opacity backing and shadow; no large black boxes, speaker
    # labels, technical slate or unnecessary permanent furniture.
    d.rounded_rectangle((x-24,645,x+tw+24,698),radius=16,
                        fill=(32,31,36,round(alpha*.34)))
    d.text((x+1,658+2),words,font=f,fill=(42,35,35,round(alpha*.55)),stroke_width=2)
    d.text((x,658),words,font=f,fill=(255,251,242,alpha),
           stroke_width=1,stroke_fill=(48,40,40,round(alpha*.7)))


def review_finale(im,t):
    local=t-110
    if local<0:return
    d=ImageDraw.Draw(im,'RGBA')
    # Ten accurate thumbnails with names, not the previous giant classroom
    # graphic: appear gradually while parents recite the review.
    alpha=round(237*smooth((local-1.4)/1.3))
    if alpha<1:return
    d.rounded_rectangle((205,12,1075,194),radius=19,
                        fill=(255,249,232,round(alpha*.91)),
                        outline=(191,158,111,alpha),width=2)
    for i,name in enumerate(WORDS[1:11]):
        col=i%5;row=i//5
        x=268+col*167;y=12+row*86
        flower=botanical(name,62)
        im.alpha_composite(flower,(int(x-flower.width/2),int(y+5)))
        f=ftext(14,True)
        text=name.capitalize()
        tw=d.textbbox((0,0),text,font=f)[2]
        d.text((x-tw/2,y+68),text,font=f,fill=(89,63,41,alpha))


def render_frame(t):
    scene=min(11,int(t//10));local=t-scene*10
    line=speaking(t)
    frame=compose_stage(t,line)
    frame=cinematic_camera(frame,scene,t,line)
    flower_title(frame,WORDS[scene],local)
    if scene==11:review_finale(frame,t)
    modern_caption(frame,line,t)
    return frame.convert('RGB')


def previews():
    """Thirty-six first/mid/last shot checks + an easier 12-beat contact sheet."""
    sheet=Image.new('RGB',(4*384,3*216),'white')
    for i in range(12):
        sample=render_frame(i*10+4.7).resize((384,216),Image.Resampling.LANCZOS)
        sheet.paste(sample,((i%4)*384,(i//4)*216))
    sheet.save(OUTPUT/'premium_contact_sheet.jpg',quality=90,optimize=True)
    checks=Image.new('RGB',(4*320,9*180),'white')
    for i in range(12):
        for j,offset in enumerate((.35,4.98,9.63)):
            k=i*3+j
            checks.paste(render_frame(i*10+offset).resize((320,180),Image.Resampling.LANCZOS),
                         ((k%4)*320,(k//4)*180))
    checks.save(OUTPUT/'premium_qc_36_frames.jpg',quality=85,optimize=True)
    print('QC contact sheets created (12 scene shots + 36 first/middle/last frames).',flush=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--preview',action='store_true')
    args=ap.parse_args()
    previews()
    if args.preview:return
    video=OUTPUT/'Ten_Funny_Flowers_Premium_120s.mp4'
    soundtrack=ROOT/'audio/narration_master.flac'
    effects=ROOT/'audio/premium_foley.wav'
    inputs=['-i',str(soundtrack)]
    if effects.exists():inputs+=['-i',str(effects)]
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}',
         '-r',str(FPS),'-i','pipe:0']+inputs
    if effects.exists():
        cmd+=['-filter_complex','[1:a][2:a]amix=inputs=2:weights=1 0.32:normalize=0,alimiter=limit=0.96[a]',
              '-map','0:v','-map','[a]']
    else:cmd+=['-map','0:v','-map','1:a']
    cmd+=['-vf','scale=1920:1080:flags=lanczos,format=yuv420p',
          '-c:v','libx264','-preset','veryfast','-crf','20',
          '-c:a','aac','-b:a','192k','-t','120',
          '-metadata','title=Ten Funny Flowers - Storybook Family Film',
          '-movflags','+faststart',str(video)]
    print('Rendering 2,880 unique movie frames at 24fps...',flush=True)
    with subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
        try:
            for i in range(120*FPS):
                proc.stdin.write(render_frame((i+.5)/FPS).tobytes())
                if i%(10*FPS)==0:
                    print(f'Rendered {i//FPS:3d} / 120 seconds',flush=True)
            proc.stdin.close()
            err=proc.stderr.read()
            rc=proc.wait()
            if rc:
                raise RuntimeError(f'FFmpeg error {rc}: {err.decode(errors="replace")}')
        except (Exception,KeyboardInterrupt):
            proc.kill()
            raise
    print('Ready:',video,flush=True)


if __name__=='__main__':main()
