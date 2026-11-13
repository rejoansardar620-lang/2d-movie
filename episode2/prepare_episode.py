"""Build Episode 02 from the original project without replacing its art, rig or renderer.

Usage:
    python episode2/prepare_episode.py

Run from a checkout containing the extracted 'Everyday_English_Project' folder.
This creates build/episode02/Everyday_English_Project/.
"""
from pathlib import Path
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Everyday_English_Project"
DEST = ROOT / "build" / "episode02"
PROJECT = DEST / "Everyday_English_Project"

# Original scenes/backgrounds/artwork remain unchanged. Each item is a new
# 10-second vignette, with 3 short, clear first-person English sentences.
SHOTS = [
    ("Let in the sunshine", "routine_bedroom", "window",
     ["I walk over to my window.", "I pull the curtains apart.", "I welcome the morning sunshine."]),
    ("Tidy my bedroom", "routine_bedroom", "make_bed",
     ["I straighten my bed.", "I pull the blanket into place.", "My room looks neat and tidy."]),
    ("Wash my hands", "bathroom", "wash",
     ["I turn on the water.", "I gently wash my hands.", "Now my hands feel clean."]),
    ("Comb my hair", "bathroom", "comb",
     ["I look into the mirror.", "I slowly comb my hair.", "I am almost ready now."]),
    ("Walk into the kitchen", "kitchen", "enter_kitchen",
     ["I walk into the kitchen.", "I look around the room.", "It is time for breakfast."]),
    ("Pick a fresh apple", "kitchen", "wash_apple",
     ["I pick up a red apple.", "I wash the apple carefully.", "It is fresh and ready."]),
    ("Prepare my breakfast", "kitchen", "make_breakfast",
     ["I take out a small bowl.", "I stir my breakfast gently.", "It smells really nice."]),
    ("Enjoy my breakfast", "kitchen", "eat_breakfast",
     ["I sit down to eat.", "I take a small bite.", "My breakfast tastes delicious."]),
    ("Drink some water", "kitchen", "drink",
     ["I pick up a glass of water.", "I take a slow sip.", "I feel fresh and happy."]),
    ("Pack my bag", "kitchen", "pack_bag",
     ["I put my things away.", "I close my small bag.", "I check that I have everything."]),
    ("Go outside", "garden", "leave",
     ["I carry my bag outside.", "I walk into the garden.", "The air feels lovely today."]),
    ("Water the flowers", "garden", "water_plants",
     ["I fill my watering can.", "I water the little flowers.", "Now I am ready to go."]),
]

# New actions use the exact same articulated puppet, 2D compositing, backgrounds,
# camera transforms, palette and caption renderer as Episode 01.
ACTION_EXTENSION = """
 elif a=='enter_kitchen':
  u=ease(local/max(1,b[1]-.25));c=base(270+760*u,.8)
  c.update(walk=u<.998,phase=local*1.5,lean=3*math.sin(local*.65),nod=2*math.sin(local))
  if local>b[2]-.5:
   p=geom(c)[1];targets['near']=p((-110,-225))
  shadow(im,c['x']);puppet(im,t,c,targets)
 elif a=='wash_apple':
  c=base(1020,.79);c.update(lean=10,nod=2*math.sin(local))
  p=geom(c)[1];reach=ease((local-.5)/1.2);wash=ease((local-b[1])/.9)
  target=mix(p((-70,95)),(1220,590),reach)
  if wash>.05:target=target+np.array([12*math.sin(local*6)*wash,5*math.sin(local*5)*wash])
  targets['near']=target;targets['far']=(1200,565)
  shadow(im,c['x']);puppet(im,t,c,targets)
  after.append(('apple',target,(78,88),-10+4*math.sin(t*2),.64))
  if wash>.1:
   d=ImageDraw.Draw(im)
   for k in range(8):
    xx=1190+4*k;yy=495+((t*70+k*17)%90)
    d.ellipse((xx-2,yy-2,xx+2,yy+3),fill='#c0e4e3')
 elif a=='make_breakfast':
  c=base(1010,.79);c.update(lean=16,nod=1.8*math.sin(local*1.7))
  stir=ease((local-b[1])/.6);pos=(1170+19*math.sin(local*5)*stir,568+8*math.cos(local*5)*stir)
  targets['near']=pos;targets['far']=(1152,637)
  shadow(im,c['x']);puppet(im,t,c,targets)
  after.extend([('bowl',(1180,675),(90,120),0,.80),('spoon',pos,(48,145),-16+18*math.sin(local*5)*stir,.62)])
 elif a=='eat_breakfast':
  c=base(1010,.79);c.update(lean=5,nod=1.6*math.sin(local*2))
  mouth=geom(c)[4];lift=ease((local-b[1])/.7)*(1-ease((local-8.6)/.9))
  pos=mix((1170,625),mouth+(-37,16),lift);pos+=np.array([1.5*math.sin(local*10),2*math.cos(local*7)])
  targets['near']=pos;targets['far']=(1118,682)
  shadow(im,c['x']);puppet(im,t,c,targets)
  after.extend([('bowl',(1180,702),(90,120),0,.76),('spoon',pos,(48,145),-7-28*lift,.6)])
 elif a=='pack_bag':
  c=base(1060,.8);c.update(lean=28-20*ease((local-b[2])/.9),nod=3*math.sin(t*.8))
  p=geom(c)[1];pick=ease((local-b[1])/1.2);x=1190-100*pick;y=765-80*pick
  targets['near']=(x-15,y-65);targets['far']=(x+35,y-65)
  shadow(im,c['x']);puppet(im,t,c,targets)
  after.append(('bag',(x,y),(90,105),4*math.sin(t*1.1),.9))
 elif a=='water_plants':
  c=base(720,.76);c.update(lean=12,nod=2*math.sin(local),walk=False)
  p=geom(c)[1];pour=ease((local-b[1])/.8)*(1-ease((local-9.0)/.8))
  pos=mix(p((-100,45)),(1030,615),pour);targets['near']=pos;targets['far']=p((85,75))
  shadow(im,c['x']);puppet(im,t,c,targets)
  after.append(('watering_can',pos,(68,70),-38*pour,.85))
  if pour>.03:
   d=ImageDraw.Draw(im)
   for k in range(10):
    phase=(t*.75+k/10)%1;x=1090+110*phase;y=642+140*phase*phase+7*math.sin(k*3)
    d.ellipse((x-3,y-2,x+3,y+5),fill='#b5dbe5')
"""

PROP_EXTENSION = """
 elif name=='apple':
  d.ellipse((32,55,132,150),fill='#c85343',outline='#8c3a2f',width=4)
  d.ellipse((53,68,80,104),fill='#ee8c79')
  d.line((83,61,89,30),fill='#674a2f',width=6)
  d.ellipse((89,27,120,43),fill='#6f995d',outline='#506e48',width=2)
 elif name=='bowl':
  d.ellipse((21,83,156,130),fill='#edcfac',outline='#a77e5c',width=5)
  d.pieslice((22,74,158,161),0,180,fill='#c9a77d',outline='#966f50',width=3)
  d.ellipse((33,85,146,112),fill='#ead4a2',outline='#987b5e',width=2)
  for xx,yy in [(60,96),(86,102),(111,94)]:d.ellipse((xx-6,yy-5,xx+6,yy+3),fill='#a87949')
 elif name=='spoon':
  d.line((49,142,84,55),fill='#abb8b5',width=10)
  d.ellipse((67,25,106,69),fill='#b9c8c6',outline='#7a9694',width=4)
 elif name=='watering_can':
  d.ellipse((112,58,168,115),fill='#9dbca6',outline='#60866c',width=5)
  d.polygon([(104,60),(160,79),(166,94),(117,89)],fill='#9dbca6')
  d.arc((32,32,110,117),185,350,fill='#60866c',width=9)
  d.rounded_rectangle((35,68,130,151),radius=20,fill='#a7c4ad',outline='#60866c',width=4)
"""

# Reframe new shots within existing painted rooms, preserving the camera system.
CAMERAS = [
    (1.08, 1340, 500), (1.16, 930, 520),
    (1.24, 1300, 420), (1.24, 1300, 420),
    (1.00, 960, 540), (1.10, 1150, 520),
    (1.14, 1130, 530), (1.18, 1120, 510),
    (1.06, 1050, 520), (1.13, 1110, 510),
    (1.00, 960, 540), (1.10, 970, 540),
]


def patch_renderer(path: Path) -> None:
    source = path.read_text()
    action_anchor = " elif a=='drink':"
    prop_anchor = " return im\ndef action_stage(si,t):"
    if source.count(action_anchor) != 1 or source.count(prop_anchor) != 1:
        raise RuntimeError("The original renderer changed; patch locations not unique")
    source = source.replace(action_anchor, ACTION_EXTENSION + action_anchor, 1)
    source = source.replace(prop_anchor, PROP_EXTENSION + " return im\ndef action_stage(si,t):", 1)
    # Original camera implementation reads CAMERAS[scene_index].
    source, count = re.subn(r"^CAMERAS=.*$", "CAMERAS="+repr(CAMERAS), source, count=1, flags=re.M)
    if count != 1:
        raise RuntimeError("Could not update camera list")
    source = source.replace("'MORNING ENGLISH'", "'MORNING ENGLISH'", 1)
    source = source.replace("'LEARN BY DOING'", "'LEARN BY DOING'", 1)
    path.write_text(source)


def main() -> None:
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    if DEST.exists():
        shutil.rmtree(DEST)
    DEST.mkdir(parents=True)
    shutil.copytree(SOURCE, PROJECT, ignore=shutil.ignore_patterns('__pycache__', 'segments'))
    if not PROJECT.is_dir():
        raise RuntimeError("Expected original project folder missing")
    spec = {
        "title": "Morning English — Breakfast and Garden (Episode 02)",
        "duration": 120, "fps": 24, "voice": "af_heart",
        "scenes": [], "sentences": [], "reference_footage_used": False,
    }
    for i, (title, background, action, sentences) in enumerate(SHOTS):
        spec["scenes"].append({
            "id": i, "start": 10*i, "end": 10*i+10, "word": title,
            "chapter": "Breakfast and garden", "background": background, "action": action,
        })
        for j, line in enumerate(sentences):
            spec["sentences"].append({
                "scene": i, "start": 10*i+10*j/3, "end": 10*i+10*(j+1)/3,
                "text": line, "action": action
            })
    (PROJECT/"lesson.json").write_text(json.dumps(spec, indent=2))
    (PROJECT/"Lesson_Script.txt").write_text("\n\n".join(
        f"{i*10:03}–{i*10+10:03}s | {s[0]}\n" + "\n".join(s[3])
        for i,s in enumerate(SHOTS)
    ))
    patch_renderer(PROJECT/"action_render.py")
    # Prevent old audio leaking into Episode 02: make_voice.py must regenerate
    # narration, Rhubarb mouth cues, dialogue, timings and caption file.
    for name in ("narration.flac", "narration.wav", "narration_raw.wav",
                 "timings.json", "mouth_cues.json", "dialogue.txt"):
        (PROJECT/"audio"/name).unlink(missing_ok=True)
    (PROJECT/"captions.srt").unlink(missing_ok=True)
    (PROJECT/"output").mkdir(exist_ok=True)
    compile((PROJECT/"action_render.py").read_text(), str(PROJECT/"action_render.py"), "exec")
    assert len(spec["scenes"])==12 and len(spec["sentences"])==36
    print(f"Prepared {PROJECT}: 12 scenes, 36 lines, same original art and character", flush=True)


if __name__ == "__main__":
    main()
