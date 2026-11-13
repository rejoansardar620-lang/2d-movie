"""Editable two-minute morning routine; twelve shots and 36 action sentences."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parent
shots=[
 ('Wake up','routine_bedroom','wake',['I wake up in the morning.','I open my eyes.','I turn off my alarm.']),
 ('Sit up and stretch','routine_bedroom','stretch',['I sit up in bed.','I stretch my arms.','I am ready to get up.']),
 ('Get out of bed','routine_bedroom','stand',['I move the blanket.','I put my feet on the floor.','I get out of bed.']),
 ('Open the window','routine_bedroom','window',['I walk to the window.','I open the curtains.','I open the window.']),
 ('Make the bed','routine_bedroom','make_bed',['I make my bed.','I pull the blanket straight.','I smooth it with my hands.']),
 ('Go to the bathroom','bathroom','bathroom',['I walk to the bathroom.','I stop beside the sink.','I turn on the tap.']),
 ('Wash up','bathroom','wash',['I wash my hands.','I wash my face.','The cool water wakes me up.']),
 ('Brush my teeth','bathroom','brush',['I pick up my toothbrush.','I brush my teeth.','I keep my teeth clean.']),
 ('Dry my face','bathroom','dry',['I turn off the tap.','I take a soft towel.','I dry my face.']),
 ('Comb my hair','bathroom','comb',['I look in the mirror.','I comb my hair.','Now my hair is neat.']),
 ('Drink some water','kitchen','drink',['I walk to the kitchen.','I pick up my cup.','I drink some water.']),
 ('Start the day','garden','leave',['I pick up my bag.','I walk outside.','I am ready for the day.']),
]
spec={'title':'Morning English — Learn by Doing','duration':120,'fps':24,'voice':'af_heart','scenes':[],'sentences':[],'reference_footage_used':False}
for i,(title,bg,action,texts) in enumerate(shots):
 spec['scenes'].append({'id':i,'start':i*10,'end':i*10+10,'word':title,'chapter':'Morning routine','background':bg,'action':action})
 for j,text in enumerate(texts):spec['sentences'].append({'scene':i,'start':i*10+j*10/3,'end':i*10+(j+1)*10/3,'text':text,'action':action})
(ROOT/'lesson.json').write_text(json.dumps(spec,indent=2))
(ROOT/'Lesson_Script.txt').write_text('\n\n'.join(f'{i*10:03}–{i*10+10:03}s | {s[0]}\n'+'\n'.join(s[3]) for i,s in enumerate(shots)))
print('12 shots / 36 sentences / 120 seconds')
