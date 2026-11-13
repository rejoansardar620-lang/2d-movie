"""Separate the generated puppet sheet into reusable articulated PNG layers."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
from scipy import ndimage
ROOT=Path(__file__).resolve().parent
im=Image.open(ROOT/'assets/action_puppet_sheet.png').convert('RGBA');a=np.array(im)
regions={
 'head':(100,0,430,363),'torso':(610,20,920,342),'pelvis':(1080,60,1400,338),
 'upper_arm':(210,360,365,660),'forearm':(690,365,825,660),'hand':(1155,390,1330,655),
 'thigh':(175,670,370,1024),'shin':(690,670,830,1024),'foot':(1110,760,1390,962)}
target={'head':(200,274),'torso':(190,235),'pelvis':(190,135),'upper_arm':(66,166),'forearm':(49,152),'hand':(46,93),'thigh':(88,227),'shin':(76,217),'foot':(120,77)}
out=ROOT/'action_rig';out.mkdir(exist_ok=True);config={}
for name,r in regions.items():
 x1,y1,x2,y2=r;b=a[y1:y2,x1:x2].copy();core=b[:,:,3]>200
 labels,n=ndimage.label(core);count=np.bincount(labels.ravel());count[0]=0;mask=labels==count.argmax()
 mask=ndimage.binary_fill_holes(mask);mask=ndimage.binary_closing(mask,iterations=1)
 yy,xx=np.where(mask);box=(max(0,xx.min()-2),max(0,yy.min()-2),min(b.shape[1],xx.max()+3),min(b.shape[0],yy.max()+3))
 # Low-alpha generation haze is outside the connected artwork, not part of it.
 alpha=Image.fromarray((mask*255).astype('uint8')).filter(ImageFilter.GaussianBlur(.45));b[:,:,3]=np.asarray(alpha)
 p=Image.fromarray(b).crop(box);source_box=[box[0]+x1,box[1]+y1,box[2]+x1,box[3]+y1]
 p=p.resize(target[name],Image.Resampling.LANCZOS)
 if name=='torso':
  alpha=p.getchannel('A');ImageDraw.Draw(alpha).polygon([(0,0),(55,0),(73,38),(65,100),(44,124),(0,124)],fill=0);p.putalpha(alpha)
  under=Image.new('RGBA',p.size);ImageDraw.Draw(under).polygon([(46,41),(92,43),(88,126),(45,125)],fill='#f5e9de');under.alpha_composite(p);p=under
 fades={'pelvis':(0,48),'thigh':(12,30),'shin':(26,0),'upper_arm':(0,24),'forearm':(22,0)}
 if name in fades:
  top,bottom=fades[name];arr=np.array(p);fade=np.ones(p.height)
  if top:fade[:top]=np.linspace(0,1,top)
  if bottom:fade[-bottom:]=np.linspace(1,0,bottom)
  arr[:,:,3]=(arr[:,:,3]*fade[:,None]).astype('uint8');p=Image.fromarray(arr)
 p.save(out/f'{name}.png')
 config[name]={'file':f'{name}.png','size':target[name],'source_box':list(map(int,source_box))}
(out/'rig.json').write_text(json.dumps(config,indent=2));print(config)
