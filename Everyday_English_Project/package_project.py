"""Package the reusable morning-routine project without model weights or caches."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parent
names=['action_render.py','render_all.py','build_routine.py','prepare_action_rig.py','make_voice.py','master_audio.py','test_animation.py','package_project.py','README.md','requirements.txt','lesson.json','Lesson_Script.txt','captions.srt','artwork_prompts.md','QA_Report.json']
paths=[ROOT/n for n in names if (ROOT/n).exists()]
for folder in ['action_rig','assets/fonts']:paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
paths.extend(ROOT/'assets/backgrounds'/f'{n}.png' for n in ['routine_bedroom','bathroom','kitchen','garden'])
paths.extend(ROOT/'assets'/n for n in ['action_puppet_sheet.png','character_master.png'])
paths.extend(ROOT/'audio'/n for n in ['narration.flac','timings.json','mouth_cues.json','dialogue.txt'])
paths.append(ROOT/'output/Preview_Contact_Sheet.jpg')
out=ROOT/'output/Everyday_English_2_Minute_Project.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=5) as z:
 for p in paths:
  if p.is_file():z.write(p,'Everyday_English_Project/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(out) as z:assert z.testzip() is None
print(out, out.stat().st_size, 'bytes')
