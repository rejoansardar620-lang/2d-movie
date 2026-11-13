"""Local PyTorch/Kokoro speech and per-scene Rhubarb lip sync."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from multiprocessing import get_context
import argparse,json,subprocess,hashlib,os,time
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
import numpy as np
import soundfile as sf
ROOT=Path(__file__).resolve().parent;SR=24000
ENGINE=None;VOICE=None;RHUBARB=None

def stamp(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def initialize(model_dir,rhubarb):
 global ENGINE,VOICE,RHUBARB
 import torch
 from kokoro import KModel,KPipeline
 torch.set_num_threads(2);torch.set_num_interop_threads(1)
 path=Path(model_dir)
 model=KModel(repo_id='hexgrad/Kokoro-82M',config=str(path/'config.json'),model=str(path/'kokoro-v1_0.pth')).eval()
 ENGINE=KPipeline(lang_code='a',repo_id='hexgrad/Kokoro-82M',model=model,device='cpu')
 VOICE=torch.load(path/'af_heart.pt',map_location='cpu',weights_only=True);RHUBARB=rhubarb

def generate_scene(job):
 scene,lines,voice_id=job;t0=time.monotonic();out=ROOT/'audio';index=scene['id']
 tag=hashlib.sha256(json.dumps([scene['word'],[x['text'] for x in lines],voice_id,'torch2-picture-lesson']).encode()).hexdigest()
 checkpoint=out/'scenes'/f'{index:02}.json';wav=checkpoint.with_suffix('.wav')
 if checkpoint.exists() and wav.exists():
  r=json.loads(checkpoint.read_text())
  if r.get('tag')==tag:return r
 speed=.65
 for attempt in range(4):
  clips=[]
  for line in lines:
   digest=hashlib.sha256(('torch-misaki-v1'+line['text']+voice_id+str(round(speed,4))).encode()).hexdigest()[:16]
   cached=out/'lines'/f'{digest}.wav'
   if cached.exists():a,sr=sf.read(cached,dtype='float32')
   else:
    pieces=list(ENGINE(line['text'],voice=VOICE,speed=speed,split_pattern=None))
    a=np.concatenate([p.audio.numpy() for p in pieces]);sr=SR
    nz=np.flatnonzero(np.abs(a)>.003)
    if len(nz):a=a[max(0,nz[0]-int(.055*sr)):min(len(a),nz[-1]+int(.10*sr))]
    a=np.asarray(a,np.float32);fade=min(int(.006*sr),len(a)//3)
    a[:fade]*=np.linspace(0,1,fade);a[-fade:]*=np.linspace(1,0,fade);sf.write(cached,a,sr)
   assert sr==SR;clips.append(a)
  total=sum(len(a)/SR for a in clips)
  if total<=8.95:break
  speed*=total/8.95*1.015
 assert total<=9.12,(scene['word'],total,speed)
 gap=(9.82-total)/3;cursor=.12;mix=np.zeros(SR*10,np.float32);timings=[]
 for j,(line,a) in enumerate(zip(lines,clips)):
  end=cursor+len(a)/SR;offset=round(cursor*SR);mix[offset:offset+len(a)]=a
  line['start']=round(scene['start'] if j==0 else scene['start']+cursor-.07,4)
  line['end']=round(scene['start']+end+gap-.07,4) if j<2 else scene['end']
  line['speech_start']=round(scene['start']+cursor,4);line['speech_end']=round(scene['start']+end,4);line['speed']=round(speed,4)
  timings.append({'start':line['speech_start'],'end':line['speech_end'],'text':line['text'],'scene':index});cursor=end+gap
 sf.write(wav,mix,SR)
 dialogue=checkpoint.with_suffix('.txt');dialogue.write_text('\n'.join(l['text'] for l in lines));cuefile=checkpoint.with_suffix('.cues.json')
 subprocess.run([RHUBARB,'-r','pocketSphinx','-f','json','--threads','1','-q','-d',str(dialogue),'-o',str(cuefile),str(wav)],check=True)
 cues=json.loads(cuefile.read_text())['mouthCues']
 for c in cues:c['start']=round(c['start']+scene['start'],3);c['end']=round(c['end']+scene['start'],3)
 result={'tag':tag,'scene':index,'word':scene['word'],'lines':lines,'timings':timings,'cues':cues,'speech_duration':total,'speed':speed,'elapsed':time.monotonic()-t0}
 checkpoint.write_text(json.dumps(result,indent=2));return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--model-dir',type=Path,required=True);p.add_argument('--rhubarb',type=Path,required=True);p.add_argument('--workers',type=int,default=3);args=p.parse_args()
 spec=json.loads((ROOT/'lesson.json').read_text());out=ROOT/'audio'
 for folder in ['scenes','lines']:(out/folder).mkdir(exist_ok=True,parents=True)
 jobs=[(s,[x.copy() for x in spec['sentences'] if x['scene']==s['id']],spec['voice']) for s in spec['scenes']];results={}
 with ProcessPoolExecutor(max_workers=args.workers,mp_context=get_context('spawn'),initializer=initialize,initargs=(str(args.model_dir.resolve()),str(args.rhubarb.resolve()))) as pool:
  for fut in as_completed([pool.submit(generate_scene,j) for j in jobs]):
   r=fut.result();results[r['scene']]=r;print(f"Voice + lip sync {len(results):02}/{len(jobs)}: {r['word']} ({r['elapsed']:.1f}s)",flush=True)
 mix=np.zeros(spec['duration']*SR,np.float32);timings=[];lines=[];cues=[]
 for i in range(len(spec['scenes'])):
  a,sr=sf.read(out/'scenes'/f'{i:02}.wav',dtype='float32');assert sr==SR and len(a)==10*SR
  mix[i*10*SR:(i+1)*10*SR]=a;lines.extend(results[i]['lines']);timings.extend(results[i]['timings']);cues.extend(results[i]['cues'])
 spec['sentences']=lines;(ROOT/'lesson.json').write_text(json.dumps(spec,indent=2));sf.write(out/'narration_raw.wav',mix,SR)
 (out/'timings.json').write_text(json.dumps(timings,indent=2));(out/'dialogue.txt').write_text('\n'.join(x['text'] for x in lines));(out/'mouth_cues.json').write_text(json.dumps({'mouthCues':cues},indent=2))
 (ROOT/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(r["start"])} --> {stamp(r["end"])}\n{r["text"]}' for i,r in enumerate(timings))+'\n')
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y','-i',str(out/'narration_raw.wav'),'-af','highpass=f=65,loudnorm=I=-18:TP=-2:LRA=7','-ar','48000','-ac','2',str(out/'narration.wav')],check=True)
 print('Narration, lip sync and captions complete.',flush=True)
if __name__=='__main__':main()
