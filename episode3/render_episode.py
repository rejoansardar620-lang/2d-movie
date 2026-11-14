"""Render a 120-second family flower lesson with the original articulated rig.

Built from Episode 01's painted garden, actual rig sprites, joint solver and
proportions. Extra family members reuse the hand-animated cutout technique.
The fully composited 1280x720 frames are encoded to 1920x1080 / 24fps H.264.
"""
from pathlib import Path
import importlib.util
import io
import json
import math
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent / "Everyday_English_Project"
STORY = json.loads((HERE / "story.json").read_text())
TIMES = json.loads((HERE / "timings.json").read_text())
W, H, FPS = 1280, 720, 24
OUT = HERE / "output"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT))
import action_render as original
from master_audio import master

FONTFILE = PROJECT / "assets" / "fonts" / "DejaVuSans.ttf"
BOLDFILE = PROJECT / "assets" / "fonts" / "DejaVuSans-Bold.ttf"
def font(n, bold=False):
    return ImageFont.truetype(str(BOLDFILE if bold else FONTFILE), n)


def tint_part(img, kind, color):
    """Preserve the parent puppet's ink, folds and painted highlights."""
    im = img.copy()
    a = np.asarray(im).copy().astype(np.float32)
    rgb = a[:, :, :3]
    color_rgb = np.asarray(tuple(bytes.fromhex(color.lstrip('#'))), np.float32)
    mx, mn = rgb.max(2), rgb.min(2)
    brightness = rgb.mean(2)
    if kind == "torso":
        mask = (brightness > 95) & ((mx - mn) < 70)
        strength = .68
    else:
        mask = (rgb[:, :, 0] > rgb[:, :, 2] + 10) & (brightness > 55)
        strength = .79
    shades = .62 + .55 * (brightness / 255)
    recolor = np.clip(color_rgb[None, None, :] * shades[:, :, None], 0, 255)
    rgb[mask] = rgb[mask] * (1-strength) + recolor[mask] * strength
    a[:, :, :3] = rgb
    return Image.fromarray(np.uint8(np.clip(a, 0, 255)), "RGBA")


def head_for(role):
    h = original.parts['head'].copy()
    if role in ('dad','boy'):
        # Retain the same face and skin rendering but remove the long-hair
        # silhouette below the cheek. Finish with short painted locks.
        m = Image.new('L', h.size)
        d = ImageDraw.Draw(m)
        d.polygon([(32,72),(42,43),(80,12),(146,5),(195,31),
                   (197,111),(184,143),(174,166),(149,186),
                   (113,191),(83,170),(59,136),(35,108)], fill=255)
        # Multiply in floating point: multiplying uint8 alpha channels would
        # wrap 255*255 to 1 and accidentally erase the entire face.
        h.putalpha(Image.fromarray((np.asarray(h.getchannel('A'),dtype=np.float32) *
                                   np.asarray(m,dtype=np.float32) / 255).astype('uint8')))
        arr=np.asarray(h).copy()
        yy,xx=np.ogrid[:h.height,:h.width]
        hair=(yy>154)&(arr[:,:,0]<155)&(arr[:,:,1]<115)&(arr[:,:,2]<105)
        # Keep the face/neck and remove the original long hairstyle's tails.
        hair &= ((xx<112) | (xx>160))
        arr[:,:,3][hair]=0
        h=Image.fromarray(arr,'RGBA')
        top = Image.new('RGBA', h.size)
        d = ImageDraw.Draw(top)
        hair = '#3d2c2a' if role == 'dad' else '#4f302a'
        d.pieslice((36,-2,196,120), 176, 349, fill=hair, outline='#302322', width=3)
        d.polygon([(41,66),(60,28),(112,14),(160,24),(166,49),
                   (149,43),(134,55),(108,43),(78,64),(50,84)],fill=hair)
        for xx in (76,98,122):
            d.arc((xx,15,xx+48,65), 192, 290, fill='#87604a',width=3)
        h.alpha_composite(top)
        if role == 'dad':
            d = ImageDraw.Draw(h)
            d.arc((139,136,180,156), 185, 355, fill='#533b32', width=3)
            d.arc((126,151,178,184), 5, 115, fill='#91614b', width=2)
    elif role == 'girl':
        d = ImageDraw.Draw(h)
        for x,y in ((48,32),(171,33)):
            d.ellipse((x-15,y-9,x+15,y+9),fill='#ed889b',outline='#a84c61',width=2)
            d.polygon([(x,y),(x-23,y-18),(x-20,y+10)],fill='#f0a4b4')
    return h


BASE_PARTS = {k: v.copy() for k,v in original.parts.items()}
CHAR_CONFIG = {
    'dad': {'shirt':'#6a9cba','pants':'#5c7892'},
    'mom': {'shirt':'#f7eee4','pants':'#c9b08c'},
    'boy': {'shirt':'#79bd9e','pants':'#60799d'},
    'girl': {'shirt':'#eda5ba','pants':'#9a7db9'},
}


def masculine_torso(shirt):
    """Paint a straight-cut T-shirt over the same shoulder/waist rig anchors."""
    pic=Image.new('RGBA',(190,235))
    d=ImageDraw.Draw(pic)
    points=[(18,30),(65,7),(131,7),(177,31),(167,106),(148,105),
            (143,218),(48,218),(39,106),(20,110)]
    d.polygon(points,fill=shirt)
    d.line(points+[points[0]],fill='#796451',width=4,joint='curve')
    d.pieslice((64,-6,135,34),0,180,fill='#deb58c',outline='#8d7255',width=3)
    d.arc((72,-4,126,25),0,180,fill='#e7f4e8',width=5)
    d.line((35,99,56,104),fill='#476b70',width=3)
    d.line((148,102,164,97),fill='#476b70',width=3)
    d.line((51,193,142,195),fill='#496d77',width=3)
    d.arc((71,100,129,154),10,162,fill='#8ab9c4',width=2)
    return pic


def parts_for(role):
    parts = {k:v.copy() for k,v in BASE_PARTS.items()}
    if role != 'mom':
        parts['torso'] = (masculine_torso(CHAR_CONFIG[role]['shirt'])
                          if role in ('dad','boy') else
                          tint_part(parts['torso'], 'torso', CHAR_CONFIG[role]['shirt']))
        parts['pelvis'] = tint_part(parts['pelvis'], 'pants', CHAR_CONFIG[role]['pants'])
        for name in ('thigh','shin'):
            parts[name] = tint_part(parts[name], 'pants', CHAR_CONFIG[role]['pants'])
    parts['head'] = head_for(role)
    return parts


VARIANTS = {role:parts_for(role) for role in CHAR_CONFIG}


def make_sprite(role,pose,open_mouth=False,walk_phase=0.0):
    original.parts = VARIANTS[role]
    original.dark = {k:ImageEnhance.Brightness(v).enhance(.91) for k,v in original.parts.items()}
    def face(shape,blink):
        head = original.parts['head'].copy()
        if open_mouth:
            d = ImageDraw.Draw(head)
            # Four viseme groups: rounded, narrow, open and closed. A bool
            # remains supported by the original Episode 03 renderer.
            shape=open_mouth if isinstance(open_mouth,str) else 'D'
            bounds={'B':(151,142,173,150),'D':(146,137,176,158),
                    'F':(154,137,169,159)}.get(shape,(146,139,174,154))
            d.ellipse(bounds,fill='#7f3b36',outline='#c48765',width=2)
            if shape!='F':
                d.arc((bounds[0]+2,bounds[1]+1,bounds[2]-2,bounds[1]+7),0,180,
                      fill='#fff6dc',width=2)
        if blink:
            d = ImageDraw.Draw(head)
            d.arc((92,97,141,111),2,177,fill='#76523b',width=3)
        return head
    original.face = face
    im = Image.new('RGBA',(1920,1080))
    c = original.base(x=960,s=.79,t=1)
    c['nod'] = (-7 if pose == 'laugh' else 7 if pose=='listen' else
                -4 if pose=='nod' else 2 if pose=='talk' else 0)
    if pose=='blink':
        c['eyes_closed']=True
    c['lean'] = (5 if pose in ('talk','point') else -7 if pose=='laugh' else 0)
    p = original.geom(c)[1]
    targets = {}
    if pose == 'talk':
        targets['near'] = p((120,-120))
    elif pose == 'point':
        targets['near'] = p((180,-235))
        targets['far'] = p((50,65))
    elif pose == 'laugh':
        targets['near'] = p((6,-205))
    elif pose == 'wave':
        targets['near'] = p((140,-345))
        c['hand_pose_near']='palm'
    elif pose == 'walk':
        c['walk']=True
        c['stride']=96
        c['x'] = 960 + walk_phase * 155
        c['lean'] = 7
    original.puppet(im,1,c,targets)
    box = im.getbbox()
    if not box:
        raise RuntimeError(f"Failed to draw {role} / {pose}")
    cropped = im.crop(box)
    # Parent and child characters use the same illustrated DNA, scaled to
    # naturally different heights. Keep a consistent foot baseline.
    height = {'dad':355,'mom':348,'boy':257,'girl':254}[role]
    width = max(1, round(cropped.width*height/cropped.height))
    return cropped.resize((width,height),Image.Resampling.LANCZOS)


def build_sprites():
    sprites={}
    for role in CHAR_CONFIG:
        for pose in ('idle','talk','point','laugh','wave','walk'):
            for mouth in (False,True):
                sprites[(role,pose,mouth)] = make_sprite(role,pose,mouth)
    return sprites


FLOWER_COLORS = {'rose':'#d95d68','sunflower':'#eebd3b','tulip':'#e98a93',
                 'daisy':'#f9f6e7','lily':'#f7c8cf','marigold':'#ef9e30',
                 'lotus':'#e9aac9','hibiscus':'#cf455a','orchid':'#a881c8',
                 'jasmine':'#f9f7de'}
FLOWER_FACTS = {'rose':'A rose may have prickles!','sunflower':'Big, bright and yellow.',
                'tulip':'Cup-shaped petals.','daisy':'White petals, yellow center.',
                'lily':'Large, graceful petals.','marigold':'Fluffy orange bloom.',
                'lotus':'A flower of ponds.','hibiscus':'Five striking petals.',
                'orchid':'An elegant, colorful bloom.','jasmine':'Small, sweet-smelling flowers.'}


def petal(d,cx,cy,direction,length,width,color,outline='#9d815d'):
    a=math.radians(direction)
    ux,uy=math.cos(a),math.sin(a)
    nx,ny=-uy,ux
    points=[(cx-ux*12,cy-uy*12),
            (cx+ux*length*.52+nx*width,cy+uy*length*.52+ny*width),
            (cx+ux*length,cy+uy*length),
            (cx+ux*length*.52-nx*width,cy+uy*length*.52-ny*width)]
    d.polygon(points,fill=color)
    d.line(points+[points[0]],fill=outline,width=2,joint='curve')
    d.line([(cx+ux*15,cy+uy*15),(cx+ux*length*.7,cy+uy*length*.7)],
           fill=ImageColorShade(color),width=2)


def ImageColorShade(hx):
    v=tuple(bytes.fromhex(hx.lstrip('#')))
    return tuple(max(0,int(n*.87)) for n in v)


def flower_art(name, size=300):
    im=Image.new('RGBA',(360,400))
    d=ImageDraw.Draw(im)
    cx,cy=180,154
    d.line((180,165,173,350),fill='#648a51',width=12)
    d.line((180,165,173,350),fill='#91ae72',width=4)
    for x,y,flip in ((176,274,-1),(179,326,1)):
        d.ellipse((x-105 if flip<0 else x,y-18,x if flip<0 else x+96,y+19),
                  fill='#83ad66',outline='#648954',width=2)
        d.line((x,y,x+(-66 if flip<0 else 65),y),fill='#658c59',width=2)
    if name in ('sunflower','daisy','marigold'):
        count={'sunflower':18,'daisy':14,'marigold':33}[name]
        for i in range(count):
            angle=i*360/count
            col={'sunflower':'#f9c94b','daisy':'#fffaf2','marigold':('#f4a329' if i%3 else '#f9c64a')}[name]
            petal(d,cx,cy,angle,108 if name!='marigold' else 83,
                  17 if name!='marigold' else 17,col)
        center={'sunflower':'#714827','daisy':'#edbf43','marigold':'#d97725'}[name]
        r={'sunflower':60,'daisy':37,'marigold':44}[name]
        d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=center,outline='#8b683e',width=4)
        if name=='sunflower':
            for y in range(cy-r+12,cy+r-10,12):
                for x in range(cx-r+13,cx+r-10,12):
                    if (x-cx)**2+(y-cy)**2<(r-8)**2:
                        d.ellipse((x,y,x+4,y+5),fill='#b68b4c')
    elif name=='rose':
        for ring in range(3):
            count=8-ring*2
            for i in range(count):
                a=i*360/count+ring*13
                r=73-ring*24
                x=cx+r*math.cos(math.radians(a));y=cy+r*math.sin(math.radians(a))
                d.ellipse((x-47+ring*3,y-43+ring*3,x+47-ring*3,y+43-ring*3),
                          fill=['#d65666','#eb8996','#f7adb3'][ring],outline='#b54f61',width=3)
        d.arc((cx-31,cy-31,cx+35,cy+35),0,315,fill='#9d4059',width=8)
        d.arc((cx-10,cy-8,cx+17,cy+18),0,290,fill='#f5c2bf',width=6)
    elif name=='tulip':
        d.ellipse((90,95,270,239),fill='#e58596',outline='#a85b6d',width=4)
        d.polygon([(90,135),(88,76),(142,116),(174,63),(211,118),(276,68),(269,162),
                   (238,217),(126,217)],fill='#e8848c',outline='#b76070',width=4)
        d.polygon([(139,119),(174,65),(209,122),(210,212),(145,212)],fill='#f2a2ad',outline='#be7282',width=3)
    elif name in ('lily','lotus'):
        for i,a in enumerate((210,240,270,300,330,30,150)):
            petal(d,cx,cy,a,118 if name=='lily' else 116,36,
                  '#f6d6de' if name=='lily' else ('#f2c3d4' if i%2 else '#e8a1c4'))
        d.ellipse((164,140,196,172),fill='#eec48b',outline='#b98871',width=3)
        if name=='lily':
            for a in (35,85,140,205,275):
                xx=180+83*math.cos(math.radians(a));yy=148+65*math.sin(math.radians(a))
                d.line((180,157,xx,yy),fill='#a5825c',width=3)
                d.ellipse((xx-5,yy-6,xx+6,yy+5),fill='#bf7f45')
        else:
            d.ellipse((84,333,298,378),fill='#72ae85',outline='#457c61',width=4)
            d.line((184,357,257,333),fill='#a8cd8a',width=3)
    elif name=='hibiscus':
        for a in (270,342,54,126,198):
            petal(d,cx,cy,a,117,52,'#d94c65',outline='#a8324a')
        d.ellipse((155,127,205,177),fill='#9a394d')
        d.line((177,153,248,86),fill='#e9c770',width=7)
        for z in range(5):
            x=228+z*5;y=103-z*5
            d.ellipse((x-5,y-5,x+5,y+5),fill='#f6d87f')
    elif name=='orchid':
        for a in (210,270,330,20,160):
            petal(d,cx,cy,a,112,45,'#b794d8',outline='#7f5fa7')
        d.ellipse((140,133,217,205),fill='#e9c3dc',outline='#9565af',width=4)
        d.ellipse((164,154,198,185),fill='#9c4f90')
        for x,y in ((138,112),(238,116),(170,81)):
            d.ellipse((x-6,y-6,x+6,y+6),fill='#805aa0')
    elif name=='jasmine':
        for a in (270,342,54,126,198):
            petal(d,cx,cy,a,91,34,'#fffaf0',outline='#b4bca6')
        d.ellipse((160,135,201,176),fill='#f2cb6b',outline='#b9a055',width=3)
        for i in range(5):
            a=math.radians(i*72)
            x=cx+10*math.cos(a);y=cy+10*math.sin(a)
            d.ellipse((x-3,y-3,x+3,y+3),fill='#dbaa56')
    return im.resize((size,round(size*400/360)),Image.Resampling.LANCZOS)


def rounded(im,box,r,fill,outline=None,width=2):
    ImageDraw.Draw(im).rounded_rectangle(box,radius=r,fill=fill,outline=outline,width=width)


def flower_card(scene):
    # Persistent visual teaching aid, matching the source's warm drawn palette.
    card=Image.new('RGBA',(364,462))
    rounded(card,(0,0,362,458),26,(255,250,235,238),outline='#d6aa78',width=5)
    d=ImageDraw.Draw(card)
    name=scene['flower']
    if name:
        art=flower_art(name,300)
        card.alpha_composite(art,((364-art.width)//2,42))
        width=d.textbbox((0,0),name.upper(),font=font(36,True))[2]
        d.text(((364-width)/2,353),name.upper(),font=font(36,True),fill='#684b34')
        fact=FLOWER_FACTS[name]
        tw=d.textbbox((0,0),fact,font=font(16))[2]
        d.text(((364-tw)/2,408),fact,font=font(16),fill='#876c58')
    else:
        names=list(FLOWER_COLORS)
        for i,nam in enumerate(names):
            x=8+(i%5)*71;y=48+(i//5)*152
            art=flower_art(nam,80)
            card.alpha_composite(art,(x,y))
            short=nam.capitalize()
            tw=d.textbbox((0,0),short,font=font(9,True))[2]
            d.text((x+40-tw/2,y+101),short,font=font(9,True),fill='#70523d')
        ttl='TEN FLOWERS!' if scene['topic'] != 'Ten-flower recap' else 'YOU DID IT!'
        tw=d.textbbox((0,0),ttl,font=font(28,True))[2]
        d.text(((364-tw)/2,374),ttl,font=font(28,True),fill='#6b563a')
    return card


def draw_label(d,x,y,name):
    colors={'dad':'#4a8396','mom':'#b37365','boy':'#4e9981','girl':'#b66883'}
    label=STORY['characters'][name]['name']
    f=font(13,True);tw=d.textbbox((0,0),label,font=f)[2]
    d.rounded_rectangle((x-tw/2-11,y,x+tw/2+11,y+26),radius=12,fill='#fff6e8',outline=colors[name],width=2)
    d.text((x-tw/2,y+4),label,fill=colors[name],font=f)


def current_line(t):
    for row in TIMES:
        if row['start'] <= t <= row['end']:
            return row
    return None


def paint_frame(t,sprites,flower_cards,background):
    idx=min(11,int(t//10));local=t-idx*10;scene=STORY['scenes'][idx]
    im=background.copy();d=ImageDraw.Draw(im)
    # Pale translucent title bands keep lettering readable above busy foliage.
    rounded(im,(35,24,765,102),23,(255,249,232,224),outline='#c99a69',width=3)
    d=ImageDraw.Draw(im)
    d.text((56,33),'FAMILY FLOWER ADVENTURE',font=font(28,True),fill='#594631')
    d.text((60,75),f"{idx+1:02}/12  •  {scene['topic']}",font=font(15),fill='#80634a')
    rounded(im,(876,124,1263,610),26,(99,65,39,47))
    card=flower_cards[idx]
    if local < .38:
        card=card.copy().point(lambda p: p)  # keep RGBA, then fade in on scene changes
        alpha=card.getchannel('A').point(lambda a:int(a*max(.05,local/.38)))
        card.putalpha(alpha)
    im.alpha_composite(card,(889,130))
    who=current_line(t)
    positions={'dad':(176,615),'mom':(389,615),'boy':(590,615),'girl':(782,615)}
    for role in ('dad','mom','boy','girl'):
        active=who is not None and role==who['speaker']
        if active:
            pose='talk' if (t*2.0)%3<2 else 'point'
        elif local<1.0 and idx==0:
            pose='walk'
        elif role in ('boy','girl') and int(t*1.7)%9==0:
            pose='wave'
        elif role=='dad' and idx==2:
            pose='laugh'
        else:
            pose='idle'
        mouth=active and int(t*7)%3 != 0
        sprite=sprites[(role,pose,mouth)]
        x,basey=positions[role]
        bounce=(5*abs(math.sin(local*4.6)) if role in ('boy','girl') else 2*math.sin(local*2.4))
        shift=(-230*(1-local) if local<1 and idx==0 else 0) if role=='boy' else 0
        offset=(x-sprite.width//2+round(shift),basey-sprite.height-round(bounce))
        im.alpha_composite(sprite,offset)
        draw_label(ImageDraw.Draw(im),x,basey-sprite.height-25,role)
    # Caption strip is drawn last, like the original Episode 01 subtitle treatment.
    rounded(im,(28,617,1252,712),25,(255,249,235,245),outline='#ad815a',width=3)
    d=ImageDraw.Draw(im)
    if who:
        name=STORY['characters'][who['speaker']]['name']
        d.rounded_rectangle((48,635,179,691),radius=17,fill=STORY['characters'][who['speaker']]['color'])
        f=font(20,True);tw=d.textbbox((0,0),name,font=f)[2]
        d.text((113-tw/2,651),name,font=f,fill='#fffdf5')
        sentence=who['text'];max_width=1030
        f=font(27,True)
        while d.textbbox((0,0),sentence,font=f)[2]>max_width and f.size>19:
            f=font(f.size-1,True)
        d.text((203,649),sentence,font=f,fill='#533e31')
    else:
        msg='Can you remember all ten flower names?'
        d.text((87,649),msg,font=font(27,True),fill='#67503b')
    return im.convert('RGB')


def main():
    print('Preparing the four original-style articulated characters...',flush=True)
    sprites=build_sprites()
    bg=Image.open(PROJECT/'assets/backgrounds'/'garden.png').convert('RGBA')
    background=bg.resize((W,H),Image.Resampling.LANCZOS)
    cards=[flower_card(s) for s in STORY['scenes']]
    # Contact sheet preview is saved before spending time on final encode.
    contact=Image.new('RGB',(W*2,H*2),'white')
    for i,scene_i in enumerate((0,2,7,11)):
        frame=paint_frame(scene_i*10+4.2,sprites,cards,background)
        contact.paste(frame,((i%2)*W,(i//2)*H))
    contact.save(OUT/'contact_sheet.jpg',quality=88,optimize=True)
    print('Rendering 120 seconds of family animation...',flush=True)
    mastered = master(HERE / 'audio/narration.wav', HERE / 'audio/narration_master.flac')
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-vcodec','rawvideo',
         '-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','pipe:0',
         '-i',str(mastered),'-i',str(HERE/'captions.srt'),
         '-filter:v','scale=1920:1080:flags=lanczos,fps=24,format=yuv420p',
         '-c:v','libx264','-preset','veryfast','-crf','21',
         '-c:a','aac','-b:a','192k',
         '-c:s','mov_text','-map','0:v:0','-map','1:a:0','-map','2:s:0',
         '-t','120','-movflags','+faststart',
         '-metadata','title=Ten Funny Flowers — Family Garden Adventure',
         str(OUT/'Ten_Funny_Flowers_120s.mp4')]
    with subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as proc:
        try:
            for i in range(120*FPS):
                frame=paint_frame((i+.5)/FPS,sprites,cards,background)
                proc.stdin.write(frame.tobytes())
                if i%(10*FPS)==0:
                    print(f'  Composited {i//FPS:03}/120 seconds',flush=True)
            proc.stdin.close()
            err=proc.stderr.read()
            rc=proc.wait()
            if rc:
                raise RuntimeError(f'ffmpeg failed ({rc}): {err.decode(errors="replace")}')
        except (Exception,KeyboardInterrupt):
            proc.kill()
            raise
    print(OUT/'Ten_Funny_Flowers_120s.mp4',flush=True)


if __name__=='__main__':
    main()
