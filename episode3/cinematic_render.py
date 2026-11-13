"""Cinematic four-person cutout film, based on the updated Episode 01 rig.

Unlike the earlier lesson-card video, this is staged as a continuous family
conversation with facing partners, reverse compositions, room changes, walking
gait cycles, reactions, environment props and Rhubarb-directed lip movements.
Everything runs locally using Pillow, the existing articulated puppet and
FFmpeg. No video-generation plugin or paid API is required to rerender it.
"""
from bisect import bisect_right
from functools import lru_cache
from pathlib import Path
import json
import math
import subprocess

from PIL import Image,ImageDraw,ImageFilter,ImageFont,ImageOps

import render_episode as art

ROOT=Path(__file__).resolve().parent
STORY=json.loads((ROOT/'story.json').read_text())
TIMES=json.loads((ROOT/'timings.json').read_text())
W,H,FPS=1280,720,24
OUT=ROOT/'output'
OUT.mkdir(exist_ok=True)

PLAN=[
    ('drawing_room','Gather in the living room',None,1.00),
    ('drawing_room','A rose on the table','rose',1.36),
    ('drawing_room','The sunflower by the window','sunflower',1.33),
    ('kitchen','Walk into the kitchen','tulip',1.00),
    ('kitchen','The daisy on the counter','daisy',1.36),
    ('kitchen','Give Mom a lily','lily',1.39),
    ('balcony','Open the balcony door','marigold',1.00),
    ('balcony','The lotus in the water bowl','lotus',1.38),
    ('balcony','Is that a biscuit?','hibiscus',1.43),
    ('outside','Walk into the garden','orchid',1.00),
    ('outside','Follow the smell of jasmine','jasmine',1.39),
    ('outside','Family quiz and snack time',None,1.00),
]

POSITIONS=[
    {'dad':240,'mom':976,'boy':574,'girl':752},
    {'dad':320,'mom':960,'boy':600,'girl':771},
    {'dad':274,'mom':995,'boy':626,'girl':809},
    {'dad':230,'mom':985,'boy':606,'girl':800},
    {'dad':272,'mom':958,'boy':615,'girl':784},
    {'dad':240,'mom':870,'boy':528,'girl':1035},
    {'dad':245,'mom':945,'boy':573,'girl':770},
    {'dad':245,'mom':970,'boy':575,'girl':768},
    {'dad':258,'mom':952,'boy':580,'girl':792},
    {'dad':270,'mom':1000,'boy':596,'girl':789},
    {'dad':235,'mom':1000,'boy':565,'girl':786},
    {'dad':230,'mom':1000,'boy':575,'girl':800},
]

CHARACTERS=('dad','mom','boy','girl')
NAMES={'dad':'RAHUL','mom':'PRIYA','boy':'AARAV','girl':'ANAYA'}
COLOURS={'dad':'#8bc5d2','mom':'#efbb9b','boy':'#b4d6bc','girl':'#e8a8be'}
SPEECH_STARTS=[x['start'] for x in TIMES]
CUES=json.loads((ROOT/'audio/rhubarb_cues.json').read_text())['mouthCues'] if (ROOT/'audio/rhubarb_cues.json').exists() else []
CUE_STARTS=[c['start'] for c in CUES]


def clamp(v,a=0,b=1):return max(a,min(b,v))
def ease(v):v=clamp(v);return v*v*(3-2*v)


def speaker_line(t):
    i=bisect_right(SPEECH_STARTS,t)-1
    if i>=0 and t<=TIMES[i]['end']:
        return TIMES[i]
    return None


def mouth_shape(t):
    if not CUES:return 'D' if int(t*7)%3 else 'X'
    i=bisect_right(CUE_STARTS,t)-1
    if i<0 or t>=CUES[i]['end']:return 'X'
    value=CUES[i]['value']
    if value in ('X','A'):return 'X'
    if value in ('B','G'):return 'B'
    if value in ('F','H'):return 'F'
    return 'D'


def soft_shadow(im,box,radius=22,opacity=65):
    layer=Image.new('RGBA',im.size)
    ImageDraw.Draw(layer).ellipse(box,fill=(73,55,34,opacity))
    im.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius)))


def drawing_room():
    im=art.original.bg('routine_bedroom').copy().resize((W,H),Image.Resampling.LANCZOS)
    # Painted sofa and coffee table replace the bed's silhouette. The wall,
    # window, sunlight, art and texture remain the actual source painting.
    soft_shadow(im,(54,510,845,667),28,98)
    d=ImageDraw.Draw(im)
    d.rounded_rectangle((78,321,805,617),radius=60,fill='#8a9e8b',outline='#647865',width=11)
    d.rounded_rectangle((101,350,779,529),radius=40,fill='#bacbb2',outline='#7e9880',width=6)
    for x1,x2 in ((124,322),(333,534),(545,748)):
        d.rounded_rectangle((x1,396,x2,568),radius=29,fill='#c9d7ba',outline='#91a38a',width=5)
        d.arc((x1+20,418,x2-14,547),5,176,fill='#a4b69c',width=3)
    d.rounded_rectangle((62,437,147,615),radius=34,fill='#a6b79f',outline='#637867',width=8)
    d.rounded_rectangle((735,438,836,616),radius=38,fill='#a6b79f',outline='#637867',width=8)
    for x,y,c in ((152,402,'#dbbcb3'),(656,411,'#e7d7a7')):
        d.rounded_rectangle((x,y,x+95,y+78),radius=25,fill=c,outline='#aa9482',width=3)
    soft_shadow(im,(790,606,1198,670),13,80)
    d.rounded_rectangle((809,555,1181,602),radius=24,fill='#c29b72',outline='#936a46',width=6)
    for x in (855,1125):
        d.line((x,605,x-12,653),fill='#846347',width=13)
    d.rounded_rectangle((886,565,1080,574),radius=4,fill='#e7c397')
    return im


def kitchen():
    return art.original.bg('kitchen').resize((W,H),Image.Resampling.LANCZOS).copy()


def balcony():
    garden=art.original.bg('garden').resize((W,H),Image.Resampling.LANCZOS).copy()
    # Balcony stone floor and open countryside behind the family.
    d=ImageDraw.Draw(garden)
    d.polygon([(0,520),(1280,500),(1280,720),(0,720)],fill=(202,180,139,228))
    for y in (571,626,688):
        d.line((0,y,1280,y-11),fill='#b69a74',width=4)
    for x in range(70,1330,230):
        d.line((x,522,x+70,720),fill='#c3aa84',width=3)
    return garden


@lru_cache(maxsize=1)
def balcony_front():
    im=Image.new('RGBA',(W,H));d=ImageDraw.Draw(im)
    # A separate foreground rail hides the lower legs during conversations.
    d.rounded_rectangle((0,557,1280,576),radius=9,fill='#f6e5c9',outline='#ae8c67',width=3)
    for x in range(20,1280,132):
        d.rounded_rectangle((x,573,x+21,688),radius=6,fill='#e6d3b2',outline='#ab8a64',width=3)
        d.ellipse((x-3,561,x+24,587),fill='#f7e7cc',outline='#aa8b6d',width=2)
    d.rounded_rectangle((0,675,1280,695),radius=6,fill='#e4cfb1',outline='#9e7855',width=3)
    return im


@lru_cache(maxsize=4)
def room_image(name):
    return {'drawing_room':drawing_room,'kitchen':kitchen,
            'balcony':balcony,'outside':lambda:art.original.bg('garden').resize((W,H),Image.Resampling.LANCZOS)}[name]()


def draw_flower(im,name,room,t):
    if not name:return
    position={'drawing_room':(982,555,132),'kitchen':(1098,552,138),
              'balcony':(1075,553,144),'outside':(1094,573,162)}[room]
    cx,base,size=position
    flower=art.flower_art(name,size)
    delta=round(3*math.sin(t*1.2))
    im.alpha_composite(flower,(cx-size//2,base-flower.height-11+delta))
    d=ImageDraw.Draw(im)
    pw=size*.56
    d.ellipse((cx-pw/2-12,base-40,cx+pw/2+12,base-20),fill='#cf9b72',outline='#a47b58',width=3)
    d.polygon([(cx-pw/2,base-35),(cx+pw/2,base-35),
               (cx+pw*.37,base+13),(cx-pw*.37,base+13)],fill='#b88061')
    d.ellipse((cx-pw*.38,base+3,cx+pw*.38,base+16),fill='#a76f52')


def flower_word(im,name,local):
    if not name or local>4.8:return
    alpha=round(255*ease(local/.7)*(1-ease((local-4.0)/.8)))
    label=Image.new('RGBA',(310,80));d=ImageDraw.Draw(label)
    d.rounded_rectangle((2,3,306,72),radius=23,fill=(255,246,224,round(alpha*.88)),outline=(187,144,95,alpha),width=3)
    text=name.upper();f=art.font(34,True)
    tw=d.textbbox((0,0),text,font=f)[2]
    d.text(((310-tw)/2,17),text,font=f,fill=(83,62,41,alpha))
    im.alpha_composite(label,(866,110))


def make_actor_sprites():
    """An animation bank shared by all four characters and every scene."""
    bank={}
    mouths=(False,'B','D','F')
    for role in CHARACTERS:
        print(f'  Preparing {NAMES[role]}: face, gestures, walk cycle',flush=True)
        for pose in ('idle','listen','nod','talk','point','laugh','wave'):
            for mouth in mouths:
                pic=art.make_sprite(role,pose,mouth)
                bank[(role,pose,mouth,'right')]=pic
                bank[(role,pose,mouth,'left')]=ImageOps.mirror(pic)
        pic=art.make_sprite(role,'blink',False)
        bank[(role,'blink',False,'right')]=pic
        bank[(role,'blink',False,'left')]=ImageOps.mirror(pic)
        for phase in range(8):
            for mouth in (False,'D'):
                pose=f'walk_{phase}'
                pic=art.make_sprite(role,'walk',mouth,walk_phase=phase/8)
                bank[(role,pose,mouth,'right')]=pic
                bank[(role,pose,mouth,'left')]=ImageOps.mirror(pic)
    return bank


def actor_x(scene,role,local):
    dest=POSITIONS[scene][role]
    if scene in (3,6,9):
        delay={'dad':0.0,'boy':.20,'girl':.40,'mom':.65}[role]
        travel=ease((local-delay)/2.7)
        dest -= 580*(1-travel)
    elif scene==1 and role=='dad':
        dest+=35*ease((local-1.2)/2.4)
    elif scene==5 and role=='girl':
        dest-=35*ease((local-2)/2.5)
    elif scene==10 and role=='boy':
        dest+=42*ease((local-.5)/2)
    if scene==11 and local>8 and role in ('boy','girl'):
        dest+=(-20 if role=='boy' else 20)*ease((local-8)/2)
    return dest


def choose_pose(scene,role,local,t,line):
    if scene in (3,6,9) and local < ({'dad':2.6,'boy':2.9,'girl':3.1,'mom':3.4}[role]):
        return 'walk'
    if scene==11 and local>9.1:
        return 'wave'
    active=line is not None and line['speaker']==role
    if active:
        words=line['text'].lower()
        if any(x in words for x in ('biscuit','socks','rich','coffee','tomorrow','famous','style','snacks')):
            return 'laugh' if local%4>2.0 else 'talk'
        if any(x in words for x in ('rose','sunflower','tulip','daisy','lily','marigold',
                                    'lotus','hibiscus','orchid','jasmine')):
            return 'point' if local%5>1.0 else 'talk'
        return 'talk'
    # Reactions: children grin at their own or each other's jokes, parents laugh
    # immediately after a child's punchline rather than standing motionless.
    i=bisect_right(SPEECH_STARTS,t)-1
    if i>=0:
        last=TIMES[i]
        if last['speaker'] in ('boy','girl') and role in ('mom','dad'):
            if 0 <= t-last['end'] < .7:
                return 'laugh'
    if (t+{'dad':0,'mom':1.1,'boy':2.4,'girl':3.2}[role])%4.8<.12:
        return 'blink'
    return 'listen' if line else 'idle'


def look_direction(scene,role,line,local):
    if scene in (3,6,9) and local<3.4:return 'right'
    me=POSITIONS[scene][role]
    if line:
        talking=line['speaker']
        if role!=talking:
            target=POSITIONS[scene][talking]
        else:
            sequence=STORY['scenes'][scene]['lines']
            index=next((i for i,(who,txt) in enumerate(sequence)
                        if who==role and txt==line['text']),0)
            partner=sequence[index+1][0] if index<2 else sequence[index-1][0]
            target=POSITIONS[scene][partner]
    else:
        target=640
    return 'left' if target<me else 'right'


def draw_names(im,scene,local,bank,line):
    # Character identification appears only during the opening establishing
    # shot and the final ensemble; speech subtitles identify everyone later.
    if not (scene==0 and local<5.1):return
    d=ImageDraw.Draw(im)
    for role in CHARACTERS:
        x=actor_x(scene,role,local)
        y=240 if role in ('dad','mom') else 329
        f=art.font(16,True);tw=d.textbbox((0,0),NAMES[role],font=f)[2]
        d.rounded_rectangle((x-tw/2-13,y-5,x+tw/2+13,y+25),radius=11,
                            fill='#fff5e3',outline=COLOURS[role],width=3)
        d.text((x-tw/2,y),NAMES[role],font=f,fill='#564534')


def film_camera(im,scene,local,line):
    room,title,name,z=PLAN[scene]
    if z<=1.001:return im
    # A gentle reverse-shot camera follows whoever speaks, without cutting
    # the speaking partner out of frame.
    if line:
        sequence=STORY['scenes'][scene]['lines']
        i=next((i for i,(who,words) in enumerate(sequence)
                if who==line['speaker'] and words==line['text']),0)
        partner=sequence[i+1][0] if i<2 else sequence[i-1][0]
        target_x=.68*POSITIONS[scene][line['speaker']]+.32*POSITIONS[scene][partner]
    else:
        target_x=640
    dest=640+(target_x-640)*.72
    if line:
        i=bisect_right(SPEECH_STARTS,line['start'])-1
        before=TIMES[max(i-1,0)]['speaker']
        old=640+(POSITIONS[scene].get(before,640)-640)*.50
        x=old+(dest-old)*ease((local+scene*10-line['start'])/.6)
    else:x=dest
    cw=W/z;ch=H/z
    x0=max(0,min(W-cw,x-cw/2))
    y0=max(0,min(H-ch,(H-ch)/2-5))
    return im.crop((int(x0),int(y0),int(x0+cw),int(y0+ch))).resize((W,H),Image.Resampling.BICUBIC)


def subtitle(im,line):
    if line is None:return
    d=ImageDraw.Draw(im)
    words=line['text']
    f=art.font(26,True)
    while d.textbbox((0,0),words,font=f)[2]>1060 and f.size>18:
        f=art.font(f.size-1,True)
    width=d.textbbox((0,0),words,font=f)[2]
    x=(W-width)/2
    d.rounded_rectangle((max(25,x-40),646,min(W-25,x+width+40),699),
                        radius=17,fill=(29,24,22,208))
    d.text((x+2,656+2),words,font=f,fill=(0,0,0,155))
    d.text((x,656),words,font=f,fill='#fff6e5')
    role=line['speaker']
    f2=art.font(13,True)
    tag=f'{NAMES[role]} SPEAKS'
    tw=d.textbbox((0,0),tag,font=f2)[2]
    d.rounded_rectangle(((W-tw)/2-10,623,(W+tw)/2+10,646),radius=9,
                        fill='#322e28',outline=COLOURS[role],width=2)
    d.text(((W-tw)/2,626),tag,font=f2,fill=COLOURS[role])


def frame_at(t,sprites):
    scene=min(11,int(t/10))
    local=t-scene*10
    room,shot_name,flower,z=PLAN[scene]
    im=room_image(room).copy()
    draw_flower(im,flower,room,t)
    line=speaker_line(t)
    for role in CHARACTERS:
        pose=choose_pose(scene,role,local,t,line)
        if pose=='walk':
            p=f'walk_{int(t*8)%8}'
            mouth=('D' if line and line['speaker']==role and mouth_shape(t)!='X' else False)
        else:
            p=pose
            mouth=(mouth_shape(t) if line and line['speaker']==role else 'X')
            if mouth=='X':mouth=False
        direction=look_direction(scene,role,line,local)
        sprite=sprites[(role,p,mouth,direction)]
        x=actor_x(scene,role,local)
        ground={'drawing_room':635,'kitchen':631,'balcony':632,'outside':642}[room]
        y=ground
        if role in ('boy','girl'):
            y-=round(2.5*abs(math.sin(t*2.2)))
        elif pose=='walk':
            y-=round(3.5*abs(math.sin(t*5)))
        xx=int(x-sprite.width/2)
        yy=int(y-sprite.height)
        # alpha_composite can clip negative coordinates for an entrance.
        im.alpha_composite(sprite,(xx,yy))
    if room=='balcony':
        im.alpha_composite(balcony_front())
    draw_names(im,scene,local,sprites,line)
    im=film_camera(im,scene,local,line)
    flower_word(im,flower,local)
    # Small scene slate and room changes replace the old giant school card.
    if local<3:
        slate=Image.new('RGBA',(550,68));d=ImageDraw.Draw(slate)
        opacity=int(230*ease(local/.3)*(1-ease((local-2.3)/.7)))
        d.rounded_rectangle((8,7,540,59),radius=13,fill=(36,33,30,opacity))
        txt=f'{scene+1:02}  {shot_name.upper()}'
        f=art.font(19,True)
        while d.textbbox((0,0),txt,font=f)[2]>505 and f.size>15:
            f=art.font(f.size-1,True)
        d.text((25,23),txt,font=f,fill=(255,250,238,opacity))
        im.alpha_composite(slate,(24,33))
    subtitle(im,line)
    return im.convert('RGB')


def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',action='store_true')
    args=parser.parse_args()
    sprites=make_actor_sprites()
    print('Generating four-room contact sheet...',flush=True)
    contact=Image.new('RGB',(W*2,H*2),'white')
    for i,sec in enumerate((12,43,75,103)):
        contact.paste(frame_at(sec,sprites),((i%2)*W,(i//2)*H))
    contact.save(OUT/'cinematic_contact_sheet.jpg',quality=88,optimize=True)
    if args.preview:
        print('Preview complete.',flush=True)
        return
    target=OUT/'Ten_Funny_Flowers_Cinematic_120s.mp4'
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y',
         '-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}',
         '-pix_fmt','rgb24','-r',str(FPS),'-i','pipe:0',
         '-i',str(ROOT/'audio/narration_master.flac'),
         '-i',str(ROOT/'captions.srt'),
         '-filter:v','scale=1920:1080:flags=lanczos,format=yuv420p',
         '-c:v','libx264','-crf','21','-preset','veryfast',
         '-c:a','aac','-b:a','192k','-c:s','mov_text',
         '-map','0:v:0','-map','1:a:0','-map','2:s:0',
         '-metadata','title=Ten Funny Flowers - Family Movie Cut',
         '-t','120','-movflags','+faststart',str(target)]
    print('Rendering 120 seconds of cinematic 2D scenes...',flush=True)
    with subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE) as process:
        try:
            for i in range(120*FPS):
                process.stdin.write(frame_at((i+.5)/FPS,sprites).tobytes())
                if i%(10*FPS)==0:
                    print(f'  Movie frame {i:04}/{120*FPS} — {i//FPS} seconds',flush=True)
            process.stdin.close()
            errors=process.stderr.read()
            status=process.wait()
            if status:
                raise RuntimeError(f'FFmpeg returned {status}: {errors.decode(errors="replace")}')
        except (Exception,KeyboardInterrupt):
            process.kill()
            raise
    print(target,flush=True)


if __name__=='__main__':main()

