from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from multiprocessing import get_context
import json,subprocess,argparse
from master_audio import master
ROOT=Path(__file__).resolve().parent

def run_scene(i):
 from action_render import render_segment
 return render_segment(i)
def main():
 p=argparse.ArgumentParser();p.add_argument('--workers',type=int,default=3);p.add_argument('--join-only',action='store_true');args=p.parse_args()
 spec=json.loads((ROOT/'lesson.json').read_text());N=len(spec['scenes']);out=ROOT/'output';segments=out/'segments'
 if not args.join_only:
  with ProcessPoolExecutor(max_workers=args.workers,mp_context=get_context('spawn')) as pool:
   for count,f in enumerate(as_completed([pool.submit(run_scene,i) for i in range(N)]),1):f.result();print(f'Completed {count}/{N}',flush=True)
 from action_render import segment_current
 for i in range(N):
  if not segment_current(i):raise RuntimeError(f'Scene {i} is missing or stale; rerun without --join-only')
 listing=segments/'concat.txt';listing.write_text(''.join(f"file '{i:02}.mp4'\n" for i in range(N)))
 audio=ROOT/'audio/narration.wav'
 if not audio.exists():audio=audio.with_suffix('.flac')
 audio=master(audio,out/'audio/narration_master.flac')
 result=out/('Everyday_English_2_Minute_Preview.mp4' if N==12 else 'Everyday_English_10_Minutes.mp4')
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','warning','-y','-f','concat','-safe','0','-i',str(listing),'-i',str(audio),'-i',str(ROOT/'captions.srt'),'-map','0:v:0','-map','1:a:0','-map','2:s:0','-c:v','copy','-c:a','aac','-b:a','256k','-c:s','mov_text','-metadata:s:s:0','language=eng','-metadata','title=Morning English — Learn by Doing','-metadata','comment=Original 2D morning-routine animation, generated narration and captions.','-t',str(spec['duration']),'-movflags','+faststart',str(result)],check=True)
 print(result,flush=True)
if __name__=='__main__':main()
