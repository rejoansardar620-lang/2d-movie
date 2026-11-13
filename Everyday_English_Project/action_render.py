"""Articulated 2D morning routine; independent joints, props and occlusion layers."""
from pathlib import Path
from functools import lru_cache
import argparse,bisect,hashlib,json,math,subprocess,time
import numpy as np
from hand_art import draw_hand
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageOps,ImageEnhance
ROOT=Path(__file__).resolve().parent
W,H,FPS=1920,1080,24
spec=json.loads((ROOT/'lesson.json').read_text());scenes=spec['scenes'];lines=spec['sentences'];N=len(scenes)
starts=[x['start'] for x in lines]
cues=json.loads((ROOT/'audio/mouth_cues.json').read_text())['mouthCues'];cue_starts=[x['start'] for x in cues]
parts={p.stem:Image.open(p).convert('RGBA') for p in (ROOT/'action_rig').glob('*.png')}
dark={k:ImageEnhance.Brightness(v).enhance(.91) for k,v in parts.items()}
INK='#493b31';CREAM='#fff5e5';ACCENT='#93704f'
def ease(u):u=max(0,min(1,u));return u*u*u*(u*(6*u-15)+10)
def mix(a,b,u):return np.asarray(a)+(np.asarray(b)-a)*u
def rot(p,a):
 r=math.radians(a);c,s=math.cos(r),math.sin(r);x,y=p;return np.array([c*x-s*y,s*x+c*y])
def angle(p):return math.degrees(math.atan2(p[1],p[0]))-90
def wrist_angle(forearm_angle,desired=None):
 if desired is None:return forearm_angle
 delta=(desired-forearm_angle+180)%360-180
 return forearm_angle+float(np.clip(delta,-40,40))
@lru_cache(maxsize=16)
def hand_sprite(side,grip=False,pose=None):
 image,pivot,_=draw_hand(side,pose or ('grip' if grip else 'relaxed'))
 return image,pivot
def limb_sprite(im,side,name,start,end,source_start,source_end):
 # Depth changes the outline/occlusion, not the character's skin colour.
 pic=parts[name]
 a=np.array(source_start,dtype=float);b=np.array(source_end,dtype=float)
 if side=='far':
  pic=ImageOps.mirror(pic);a[0]=pic.width-1-a[0];b[0]=pic.width-1-b[0]
 vector=np.asarray(end)-start
 place(im,pic,a,start,angle(vector)-angle(b-a),np.linalg.norm(vector)/np.linalg.norm(b-a))
def place(im,pic,pivot,target,deg=0,scale=1):
 a=math.radians(deg);c,s=math.cos(a),math.sin(a);target=np.asarray(target);pivot=np.asarray(pivot)
 corners=np.array([[0,0],[pic.width,0],[0,pic.height],[pic.width,pic.height]],float)
 R=np.array([[c,-s],[s,c]]);out=(corners-pivot)@R.T*scale+target
 lo=np.floor(out.min(0)).astype(int)-2;hi=np.ceil(out.max(0)).astype(int)+2;dx,dy=lo-target
 coeff=(c/scale,s/scale,pivot[0]+(c*dx+s*dy)/scale,-s/scale,c/scale,pivot[1]+(-s*dx+c*dy)/scale)
 p=pic.transform(tuple(hi-lo),Image.Transform.AFFINE,coeff,Image.Resampling.BICUBIC);im.alpha_composite(p,tuple(lo))
def ik(a,b,l1,l2,bend=-1):
 # Project unreachable targets onto the reach circle before solving either bone.
 a=np.asarray(a,dtype=float);b=np.asarray(b,dtype=float);v=b-a;length=float(np.linalg.norm(v))
 direction=v/length if length>1e-8 else np.array([0.,1.])
 dist=float(np.clip(length,abs(l1-l2)+1e-5,l1+l2-1e-5));b=a+direction*dist;v=b-a
 th=math.atan2(v[1],v[0])+bend*math.acos(np.clip((l1*l1+dist*dist-l2*l2)/(2*l1*dist),-1,1));el=a+np.array([math.cos(th),math.sin(th)])*l1
 return el,b
@lru_cache(maxsize=40)
def font(size,bold=False):return ImageFont.truetype(str(ROOT/'assets/fonts'/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),size)
@lru_cache(maxsize=8)
def bg(name):return Image.open(ROOT/'assets/backgrounds'/f'{name}.png').convert('RGBA').resize((W,H),Image.Resampling.LANCZOS)
def shape_at(t):
 j=bisect.bisect_right(cue_starts,t)-1
 return cues[j]['value'] if j>=0 and t<cues[j]['end'] else 'X'
@lru_cache(maxsize=60)
def face(shape,blink):
 h=parts['head'].copy()
 def cover(box,fill):
  mask=Image.new('L',h.size);ImageDraw.Draw(mask).ellipse(box,fill=255);p=Image.new('RGBA',h.size,fill);p.putalpha(mask.filter(ImageFilter.GaussianBlur(1.2)));h.alpha_composite(p)
 if blink:
  for x,y,w in [(131,101,17),(177,101,10)]:
   cover((x-w-3,y-12,x+w+3,y+12),(250,183,126));ImageDraw.Draw(h).arc((x-w,y-6,x+w,y+6),0,180,fill='#6d422c',width=2)
 if shape=='BRUSH':
  # Open jaw with separate upper/lower teeth; action takes priority over speech.
  cover((131,128,185,163),(252,181,125));d=ImageDraw.Draw(h)
  d.ellipse((141,135,181,157),fill='#683429',outline='#b66f54',width=2)
  d.rounded_rectangle((145,137,177,143),radius=2,fill='#fff9e9')
  d.rounded_rectangle((148,151,175,154),radius=2,fill='#f5e8d5')
  d.arc((142,134,181,160),5,160,fill='#d38c6b',width=2)
 elif shape not in ('A','X'):
  cover((131,128,185,163),(252,181,125));d=ImageDraw.Draw(h);mw,mh={'B':(13,3),'C':(12,7),'D':(11,10),'E':(7,8),'F':(6,8),'G':(12,3),'H':(10,6)}.get(shape,(11,6))
  d.ellipse((163-mw,142-mh/2,163+mw,143+mh),fill='#7a3a30',outline='#b97755',width=1)
  if shape in 'BCDGH':d.line((165-mw,142,161+mw,142),fill='#fff6e6',width=2)
 return h
def geom(c):
 root=np.array([c['x'],c['y']],float);s=c['s'];lean=c.get('lean',0)
 if c.get('walk'):root[1]-=2*s*(1-math.cos(gait_phase(c)*math.tau*2))
 elif not c.get('lying'):root[1]+=1.1*s*math.sin(c.get('time',0)*math.tau/3.6)
 def p(v):return root+rot(np.array(v)*s,lean)
 neck=p((14,-208));ha=lean+c.get('nod',0);mouth=neck+rot(np.array([-51 if c.get('head_flip') else 51,-69])*s,ha)
 return root,p,neck,ha,mouth
def gait_phase(c):
 # Travel-driven phase keeps the stance foot stationary as the body eases.
 return c['x']*.62/c.get('stride',96)
def grip_point(c,side,wrist):
 p=geom(c)[1];s=c['s'];shoulder=p((52,-183) if side=='far' else (-55,-184))
 elbow,solved=ik(shoulder,wrist,143*s,138*s,c.get('bend_'+side,1 if side=='near' else -1))
 direction=wrist_angle(angle(solved-elbow),c.get('hand_'+side))
 return solved+rot(np.array([-6 if side=='far' else 6,27])*s*.83,direction)
def grip_foreground(im,c,targets):
 """Put the thumb back in front of a held handle, using the same wrist pose."""
 p=geom(c)[1];s=c['s']
 for side in ('near','far'):
  if not c.get('grip_'+side) or side not in targets:continue
  sh=p((52,-183) if side=='far' else (-55,-184))
  elbow,wrist=ik(sh,targets[side],143*s,138*s,c.get('bend_'+side,1 if side=='near' else -1))
  _,pivot,front=draw_hand(side,'grip')
  place(im,front,pivot,wrist,wrist_angle(angle(wrist-elbow),c.get('hand_'+side)),s*.83)
def brush_pose(c,local):
 """Attach the bristles to the teeth and derive the handle/hand from that point."""
 _,p,_,ha,mouth=geom(c)
 lift=ease((local-.4)/1.5)*(1-ease((local-8.6)/1.0))
 scrub=ease((local-1.9)/.35)*(1-ease((local-8.3)/.3))
 deg=ha-7;size=.55;pivot=(155,90)
 # Short, horizontal strokes across the teeth, rather than moving the whole arm.
 tip=mouth+rot((4*math.sin(local*math.tau*2.4)*scrub,2),ha)
 contact=tip-rot(np.array([28,81])-pivot,deg)*size
 rest=p((68,45))
 handle=mix(rest,contact,lift);wrist=handle.copy()
 # The brush passes through the curled fingers, not through the wrist joint.
 for _ in range(8):wrist+=handle-grip_point(c,'near',wrist)
 return wrist,('brush',handle,pivot,deg,size),lift
def wake_pose(local):
 """Wake, lean slightly, reach around the face, tap the top, then withdraw."""
 button=np.array([113.,622.]);reach_start=5.25;press_start=7.25;press_end=7.65;return_end=9.55
 approach=ease((local-reach_start)/(press_start-reach_start))
 withdraw=ease((local-press_end)/(return_end-press_end))
 lean_in=ease((local-4.65)/1.5)*(1-ease((local-8.0)/1.55))
 c=base(t=local);c.update(x=540-32*lean_in,y=652,s=.75,lean=-78+13*lean_in,
     lying=True,eyes_closed=local<3.7,nod=0,head_flip=True,bend_near=-1,bend_far=1,hand_pose_near='press')
 rest=np.array([474.,686.]);contact_wrist=button-rot(np.array([4.,80.])*.75*.83,90)
 # Quadratic arc goes below the face and reaches above the clock before contact.
 control=np.array([326.,729.])
 u=approach*(1-withdraw)
 wrist=(1-u)**2*rest+2*u*(1-u)*control+u*u*contact_wrist
 _,p,_,_,_=geom(c);shoulder=p((-55,-184))
 elbow,solved=ik(shoulder,wrist,143*.75,138*.75,-1)
 forearm=angle(solved-elbow);turn=(90-forearm+180)%360-180;c['hand_near']=forearm+turn*ease(u)
 actual_angle=wrist_angle(forearm,c['hand_near'])
 fingertip=solved+rot(np.array([4.,80.])*.75*.83,actual_angle)
 phase='sleep' if local<3.7 else 'look' if local<reach_start else 'reach' if local<press_start else 'press' if local<=press_end else 'return' if local<return_end else 'rest'
 state={'phase':phase,'contact':press_start<=local<=press_end,'fingertip':fingertip,'button':button}
 return c,{'near':wrist,'far':p((50,65))},state
def puppet(im,t,c,targets=None):
 if c.get('flip'):
  cc=dict(c);cc['flip']=False;layer=Image.new('RGBA',(W,H));tt={k:(2*c['x']-v[0],v[1]) for k,v in (targets or {}).items()};r=puppet(layer,t,cc,tt);im.alpha_composite(ImageOps.mirror(layer),(round(2*c['x']-W),0));return {k:np.array([2*c['x']-v[0],v[1]]) for k,v in r.items()}
 root,p,neck,ha,mouth=geom(c);s=c['s'];targets=targets or {}
 pelvis_angle=0 if c.get('lying') else np.clip(c.get('lean',0)*.22,-14,14)
 for side in ['far','near']:
  off=-35 if side=='far' else 36;hip=root+rot(np.array([off,70])*s,pelvis_angle);ps=dark if side=='far' else parts
  if c.get('lying'):knee=hip+rot((0,200*s),-85);ankle=knee+rot((0,195*s),-88)
  else:
   if 'feet' in c:ankle=np.array(c['feet'][0 if side=='far' else 1])-np.array([0,38*s])
   elif c.get('walk',False):
    q=(gait_phase(c)+(0 if side=='near' else .5))%1;stride=c.get('stride',96)
    if q<.62:dx=stride*(.5-q/.62);lift=0
    else:u=(q-.62)/.38;dx=stride*(-.5+ease(u));lift=35*math.sin(math.pi*u)**2
    ankle=np.array([root[0]+off*s+dx,920-38*s-lift])
   else:ankle=np.array([root[0]+off*s+16*s,920-38*s])
   knee,ankle=ik(hip,ankle,200*s,195*s,-1)
  aa=angle(knee-hip);bb=angle(ankle-knee)
  # Use the painted trouser layers instead of flat polygon legs.
  d=ImageDraw.Draw(im);r=29*s
  d.ellipse((knee[0]-r,knee[1]-r,knee[0]+r,knee[1]+r),fill='#d5b28b' if side=='far' else '#e6c49d')
  place(im,ps['thigh'],(44,15),hip,aa,s)
  place(im,ps['shin'],(38,14),knee,bb,s)
  place(im,ps['foot'],(34,40),ankle,-80 if c.get('lying') else min(12,max(-12,bb*.25)),s)
 place(im,parts['pelvis'],(95,8),root,pelvis_angle,s)
 def arm(side):
  ps=dark if side=='far' else parts;sh=p((52,-183) if side=='far' else (-55,-184))
  if side in targets:wrist=np.array(targets[side])
  else:
   swing=25*math.sin(gait_phase(c)*math.tau)*(1 if side=='near' else -1) if c.get('walk') else 0;wrist=sh+rot((0,260*s),c.get('arm_'+side,swing)+c.get('lean',0))
  el,wrist=ik(sh,wrist,143*s,138*s,c.get('bend_'+side,1 if side=='near' else -1));aa=angle(el-sh);bb=angle(wrist-el)
  d=ImageDraw.Draw(im);r=22*s;d.ellipse((el[0]-r,el[1]-r,el[0]+r,el[1]+r),fill='#f5b77c')
  limb_sprite(im,side,'forearm',el,wrist,(25,10),(31,148))
  if side=='near':
   d=ImageDraw.Draw(im);r=26*s;d.ellipse((sh[0]-r,sh[1]-r,sh[0]+r,sh[1]+r),fill='#f9ede1')
  limb_sprite(im,side,'upper_arm',sh,el,(37,12),(27,155))
  hand,pivot=hand_sprite(side,c.get('grip_'+side,False),c.get('hand_pose_'+side))
  place(im,hand,pivot,wrist,wrist_angle(bb,c.get('hand_'+side)),s*.83)
  return wrist
 far=arm('far');place(im,parts['torso'],(100,225),p((0,-2)),c.get('lean',0),s)
 blink=c.get('eyes_closed',False) or ((t+1.4)%4.1)<.12;shape=c.get('mouth_shape') or ('X' if c.get('silent_mouth') else shape_at(t))
 head=face(shape,blink);head_pivot=(112,212)
 if c.get('head_flip'):head=ImageOps.mirror(head);head_pivot=(head.width-1-112,212)
 place(im,head,head_pivot,neck,ha,s);near=arm('near')
 return {'near':near,'far':far,'mouth':mouth,'neck':neck}
def shadow(im,x,y=925,w=160):ImageDraw.Draw(im).ellipse((x-w/2,y-11,x+w/2,y+10),fill=(82,57,31,45))
def base(x=800,s=.75,t=0):return {'x':x,'y':920-495*s,'s':s,'lean':0,'nod':0,'time':t}
def beats(si):return [l.get('speech_start',l['start'])-si*10 for l in lines if l['scene']==si]
def curtain(im,a,t):
 x0=1110;x1=max(x0+55,1484-325*a);y0=84;y1=574;d=ImageDraw.Draw(im);d.polygon([(x0,y0),(x1,y0),(x1+8*math.sin(t*2),y1),(x0,y1)],fill='#ead4af',outline='#b49064')
 for j in range(1,9):x=x0+(x1-x0)*j/9;d.line((x,y0+10,x-4+5*math.sin(t+j),y1-7),fill='#d4b68d',width=4)
 d.line((x0,y0,x1,y0),fill='#faf0d8',width=7);return (x1-12,470)
def window_pane(im,a):
 hinge=1230;edge=1483-200*a;top=108+32*a;bottom=534-18*a;pts=[(hinge,108),(edge,top),(edge,bottom),(hinge,534)]
 layer=Image.new('RGBA',im.size);d=ImageDraw.Draw(layer);d.polygon(pts,fill=(221,239,235,40));d.line(pts+[pts[0]],fill='#976a3c',width=10);d.line((hinge,321,edge,(top+bottom)/2),fill='#b58a50',width=7);d.line((edge-11,(top+bottom)/2-14,edge-11,(top+bottom)/2+15),fill='#6b583a',width=6);im.alpha_composite(layer)
 return (edge-11,(top+bottom)/2+55)
def blanket(im,level=1,shift=0):
 if level<=0:return
 x=425+shift;y=610;ww=735;hh=242;tex=bg('routine_bedroom').crop((405,681,1140,889)).resize((ww,hh),Image.Resampling.BICUBIC);mask=Image.new('L',(ww,hh));d=ImageDraw.Draw(mask);d.polygon([(0,40),(35,7),(ww-20,15),(ww,65),(ww,hh),(0,hh)],fill=round(255*level));tex.putalpha(mask);im.alpha_composite(tex,(int(x),y));ImageDraw.Draw(im).line((x+36,y+11,x+ww-25,y+18),fill='#c5a780',width=3)
def water(im,t,on=True):
 if not on:return
 d=ImageDraw.Draw(im)
 for k in range(4):x=1405+3*math.sin(t*8+k);d.line((x+k,496,x+k+1,567),fill=(155,208,219,185),width=3)
 for k in range(8):
  ph=(t*2+k/8)%1;x=1405+math.sin(k*4)*28*ph;y=566-18*math.sin(ph*math.pi);d.ellipse((x-2,y-2,x+2,y+3),fill='#b8e5eb')
def mirror(im,t,c,targets,held_props):
 layer=Image.new('RGBA',(W,H));puppet(layer,t,c,targets)
 for name,target,pivot,deg,size in held_props:place(layer,prop(name),pivot,target,deg,size)
 grip_foreground(layer,c,targets)
 reflected=ImageOps.mirror(layer.crop((1030,150,1530,770))).resize((480,595),Image.Resampling.BICUBIC)
 overlay=Image.new('RGBA',(W,H));overlay.alpha_composite(reflected,(1380,70));mask=Image.new('L',(W,H));ImageDraw.Draw(mask).ellipse((1355,-23,1865,437),fill=210)
 alpha=np.asarray(overlay.getchannel('A')).astype(float)*np.asarray(mask)/255;overlay.putalpha(Image.fromarray(alpha.astype('uint8')));im.alpha_composite(overlay)
@lru_cache(maxsize=8)
def prop(name):
 im=Image.new('RGBA',(180,180));d=ImageDraw.Draw(im)
 if name=='brush':
  d.rounded_rectangle((18,84,150,98),radius=6,fill='#69b3be',outline='#3b747b',width=2);d.rounded_rectangle((137,69,166,98),radius=5,fill='#ebeee2',outline='#5b878a',width=2)
  for y in range(73,95,4):d.line((140,y,164,y),fill='#b3cbd0',width=2)
 elif name=='comb':
  d.rounded_rectangle((35,35,75,150),radius=9,fill='#b97643',outline='#6c492d',width=3)
  for y in range(45,145,10):d.line((71,y,108,y),fill='#89522e',width=5)
 elif name=='towel':
  d.rounded_rectangle((20,20,150,163),radius=16,fill='#f5ccae',outline='#c38e68',width=3)
  for x in range(30,150,9):d.line((x,24,x-5,159),fill='#edbd9b',width=2)
  d.line((25,145,145,145),fill='#fff0d5',width=8)
 elif name=='cup':
  d.ellipse((105,58,159,118),fill='#a7c8b4',outline='#547c6c',width=5);d.ellipse((117,70,146,105),fill=(0,0,0,0));d.rounded_rectangle((35,47,122,142),radius=18,fill='#b8d4c0',outline='#547c6c',width=3);d.ellipse((35,41,122,62),fill='#eef2da',outline='#547c6c',width=3);d.ellipse((44,46,113,56),fill='#8fb8be')
 elif name=='bag':d.arc((42,18,136,119),180,360,fill='#78593d',width=12);d.rounded_rectangle((24,64,154,168),radius=15,fill='#c69758',outline='#805e3c',width=4);d.line((32,85,145,85),fill='#eac58b',width=5)
 if name=='brush':im=ImageOps.mirror(im)
 return im
def action_stage(si,t):
 local=t-si*10;b=beats(si);scene=scenes[si];im=bg(scene['background']).copy();targets={};after=[];c=base(t=t);a=scene['action']
 if a=='wake':
  c,targets,state=wake_pose(local)
  # The visible button is on top of the painted clock; motion stops after the press.
  d=ImageDraw.Draw(im);bx,by=state['button'];depress=2 if state['contact'] else 0
  d.rounded_rectangle((bx-8,by-4+depress,bx+8,by+1+depress),radius=2,fill='#e7c879',outline='#7b7841')
  if local<7.25:
   pulse=round(2*math.sin(local*math.tau*4))
   for x in (75,150):d.arc((x-6-pulse,628,x+6+pulse,648),100 if x<100 else -80,260 if x<100 else 80,fill='#8c7c48',width=2)
  puppet(im,t,c,targets);blanket(im,1,0)
 elif a=='stretch':
  up=ease(local/2);c.update(hand_pose_near='palm',hand_pose_far='palm',bend_near=-1,bend_far=1,x=540+130*up,y=652+8*up,s=.75,lean=-78*(1-up),lying=up<.85,feet=[(820,920),(868,920)],nod=-3*math.sin(local));p=geom(c)[1];st=ease((local-b[1])/.8)*(1-ease((local-8.6)/.7));targets['near']=mix(p((-55,75)),p((-155,-340)),st);targets['far']=mix(p((55,75)),p((155,-340)),st);puppet(im,t,c,targets);blanket(im,1,80*up)
 elif a=='stand':
  st=ease((local-b[2])/max(.6,9-b[2]));c.update(x=670+170*st,y=660+(920-495*.75-660)*st,s=.75,lean=10*math.sin(st*math.pi),feet=[(820,920),(868,920)]);p=geom(c)[1];pull=ease((local-b[0])/max(.8,b[1]-b[0]));targets['near']=p((75,55));puppet(im,t,c,targets)
  if local<b[1]+.4:blanket(im,1-ease((local-b[1])/.4),80+120*pull)
 elif a=='window':
  w=ease(local/max(1,b[1]-.25));c=base(960+430*w,.75,t);c.update(walk=w<.998,phase=local*1.35,nod=2*math.sin(local*2));op=ease((local-b[1])/max(.5,b[2]-b[1]-.3));cur=curtain(im,op,t);win=ease((local-b[2])/1.5);handle=window_pane(im,win)
  if local>=b[1]-.2:targets['near']=cur if local<b[2] else handle
  shadow(im,c['x']);puppet(im,t,c,targets)
 elif a=='make_bed':
  c=base(1050,.75,t);c.update(lean=50+3*math.sin(local*1.2),nod=6,flip=True);sweep=ease((local-b[1])/max(.5,9-b[1]));targets={'near':(950-50*sweep,650+7*math.sin(local*3)),'far':(1010-55*sweep,648)};shadow(im,c['x']);blanket(im,1,70-70*sweep);puppet(im,t,c,targets)
 elif a in ['bathroom','wash','brush','dry','comb']:
  c=base(1230,.8,t);c.update(lean=14,nod=1.5*math.sin(t*1.5))
  if a=='bathroom':
   w=ease(local/max(1,b[1]-.25));c.update(x=250+980*w,walk=w<.998,phase=local*1.5,stride=110,lean=14*w)
   if local>b[2]-.3:targets['far']=(1510,520);c['lean']=22
  p=geom(c)[1];mouth=geom(c)[4]
  if a=='wash':
   c['lean']=18-10*ease((local-b[1])/1.4);p=geom(c)[1];mouth=geom(c)[4];lift=ease((local-b[1])/.9)*(1-ease((local-8.3)/.7));targets['near']=mix((1390,575),mouth+(-24,20),lift);targets['far']=mix((1425,577),mouth+(4,24),lift);c.update(eyes_closed=lift>.7,hand_near=-100,hand_far=-60)
  elif a=='brush':
   targets['near'],brush_item,opening=brush_pose(c,local);c.update(grip_near=True,mouth_shape='BRUSH' if opening>.25 else 'X');after.append(brush_item)
  elif a=='dry':
   if local<b[1]:targets['far']=(1505,520);c['lean']=22
   else:
    lift=ease((local-b[2])/.8);pos=mix((1350,600),mouth+(-20,15),lift);targets['near']=pos;targets['far']=pos+(-70,18);c.update(eyes_closed=lift>.7,hand_near=-120);after.append(('towel',pos,(105,70),-8+4*math.sin(t*2),.8))
  elif a=='comb':
   c['bend_near']=-1;c['lean']=4;p=geom(c)[1];mouth=geom(c)[4];cycle=(local-b[1])%2.2/2.2;stroke=ease(cycle/.72) if cycle<.72 else 1-ease((cycle-.72)/.28);on=ease((local-b[1])/.4)*(1-ease((local-8.8)/.7));pos=mix(p((-55,70)),p((-85,-335+120*stroke)),on);targets['near']=pos;c['hand_near']=-135
   if on>.02:after.append(('comb',pos+(-6,-12),(55,135),-15,.62))
  if a!='bathroom' or local>b[1]:mirror(im,t,c,targets,after)
  on=a in ['wash','brush'] or (a=='bathroom' and local>b[2]+.4) or (a=='dry' and local<b[0]+.8);water(im,t,on);shadow(im,c['x']);puppet(im,t,c,targets)
  im.alpha_composite(bg('bathroom').crop((1181,650,1920,949)),(1181,650))
  if a=='wash' and lift>.7:
   d=ImageDraw.Draw(im)
   for k in range(6):f=(t*1.5+k/6)%1;x=mouth[0]-25+k*8;y=mouth[1]+15+40*f;d.ellipse((x-2,y-2,x+2,y+4),fill='#bbdfdd')
 elif a=='drink':
  w=ease(local/max(1,b[1]-.3));c=base(490+550*w,.8,t);c.update(walk=w<.998,phase=local*1.5,lean=4);mouth=geom(c)[4];lift=ease((local-b[2])/.8)*(1-ease((local-9)/.6));pick=ease((local-b[1])/1.1);hold=mix((1280,405),(1160,535),pick);pos=mix(hold,mouth+(0,25),lift)
  if local>b[1]-.3:targets['near']=pos+(-20,20)
  shadow(im,c['x']);puppet(im,t,c,targets);after.append(('cup',pos,(90,100),-18*lift,.75))
 elif a=='leave':
  w=ease((local-b[1])/max(1,b[2]-b[1]));c=base(640+440*w,.75,t);c.update(walk=local>=b[1] and local<b[2],phase=local*1.35);pick=ease(local/1.6);c['lean']=24*(1-pick);p=geom(c)[1];targets['far']=mix((c['x']+100,755),p((75,85)),pick);c['grip_far']=True;c['bend_near']=-1
  if local>b[2]:
   c['hand_pose_near']='palm';wave=ease((local-b[2])/.7);targets['near']=mix(p((-55,76)),p((-105,-270+14*math.sin(t*5))),wave);c['hand_near']=180*wave+12*math.sin(t*5)*wave
  shadow(im,c['x']);joints=puppet(im,t,c,targets);after.append(('bag',grip_point(c,'far',joints['far']),(90,24),4*math.sin(t*3),.8))
 for name,target,pivot,deg,s in after:place(im,prop(name),pivot,target,deg,s)
 grip_foreground(im,c,targets)
 return im
CAMERAS=[(1.37,670,590),(1.24,750,535),(1,960,540),(1.08,1340,500),(1.16,930,520),(1,960,540),(1.24,1300,420),(1.24,1300,420),(1.24,1300,420),(1.24,1300,420),(1.06,1050,520),(1,960,540)]
def camera(im,si,local):
 zoom,cx,cy=CAMERAS[si];zoom+=.012*ease(local/10);cw=W/zoom;ch=H/zoom;l=max(0,min(W-cw,cx-cw/2));top=max(0,min(H-ch,cy-ch/2));return im.crop((round(l),round(top),round(l+cw),round(top+ch))).resize((W,H),Image.Resampling.BICUBIC)
def frame(t):
 si=min(N-1,int(t//10));local=t-si*10;im=camera(action_stage(si,t),si,local);d=ImageDraw.Draw(im);d.rounded_rectangle((47,35,356,82),radius=16,fill=(255,246,229,235));d.text((69,57),'MORNING ENGLISH',font=font(23,True),fill=INK,anchor='lm')
 d.rectangle((0,930,W,H),fill=CREAM);d.line((0,930,W,930),fill='#d4b694',width=3);d.text((65,961),f'{si+1:02} / 12  ·  '+scenes[si]['word'].upper(),font=font(22,True),fill=ACCENT,anchor='lm');d.text((1855,961),'LEARN BY DOING',font=font(22),fill=ACCENT,anchor='rm')
 idx=max(0,min(len(lines)-1,bisect.bisect_right(starts,t)-1));text=lines[idx]['text'];size=52
 while d.textlength(text,font=font(size,True))>1790:size-=2
 d.text((960,1018),text,font=font(size,True),fill=INK,anchor='mm');d.rounded_rectangle((65,1060,1855,1066),radius=3,fill='#e6d4b9');d.rounded_rectangle((65,1060,65+max(3,1790*t/120),1066),radius=3,fill='#a68655');return im.convert('RGB')
@lru_cache(maxsize=1)
def render_fingerprint():
 """Invalidate rendered frames when code, artwork, timing or mouth cues change."""
 digest=hashlib.sha256()
 files=[Path(__file__),ROOT/'hand_art.py',ROOT/'lesson.json',ROOT/'audio/mouth_cues.json']
 files+=sorted((ROOT/'action_rig').glob('*.png'))
 files+=sorted(p for p in (ROOT/'assets').rglob('*') if p.is_file())
 for path in files:
  digest.update(str(path.relative_to(ROOT)).encode());digest.update(path.read_bytes())
 return digest.hexdigest()
def segment_current(index):
 out=ROOT/'output/segments';video=out/f'{index:02}.mp4';stamp=out/f'{index:02}.json'
 if not video.exists() or not stamp.exists():return False
 try:
  data=json.loads(stamp.read_text())
  return data.get('inputs')==render_fingerprint() and data.get('video')==hashlib.sha256(video.read_bytes()).hexdigest()
 except (ValueError,OSError):return False
def render_segment(index):
 out=ROOT/'output/segments';out.mkdir(parents=True,exist_ok=True);result=out/f'{index:02}.mp4';partial=out/f'{index:02}.partial.mp4'
 if segment_current(index):return index
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p','-frames:v',str(FPS*10),str(partial)];proc=subprocess.Popen(cmd,stdin=subprocess.PIPE);start=time.monotonic()
 try:
  for n in range(FPS*10):proc.stdin.write(frame(index*10+n/FPS).tobytes())
  proc.stdin.close()
  if proc.wait()!=0:raise RuntimeError(f'FFmpeg failed while rendering scene {index}')
  partial.replace(result)
  (out/f'{index:02}.json').write_text(json.dumps({'inputs':render_fingerprint(),'video':hashlib.sha256(result.read_bytes()).hexdigest()}))
 except BaseException:proc.kill();raise
 print(f'Rendered {index+1:02}/{N} in {time.monotonic()-start:.1f}s',flush=True);return index
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--scene',type=int);p.add_argument('--time',type=float);args=p.parse_args();(ROOT/'output').mkdir(exist_ok=True)
 if args.preview:
  sheet=Image.new('RGB',(1920,1440),'white')
  for i in range(N):pic=frame(i*10+5);pic.save(ROOT/'output'/f'preview_{i:02}.jpg',quality=92);sheet.paste(pic.resize((640,360),Image.Resampling.LANCZOS),((i%3)*640,(i//3)*360))
  sheet.save(ROOT/'output/Preview_Contact_Sheet.jpg',quality=93)
 elif args.time is not None:frame(args.time).save(ROOT/'output/pose.jpg',quality=94)
 elif args.scene is not None:render_segment(args.scene)
