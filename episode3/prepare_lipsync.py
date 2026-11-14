"""Align the supplied four-actor recording with open-source Rhubarb Lip Sync.

No paid service or plugin is needed. This CLI emits mouth shape A-H/X cues;
the film director assigns each cue to the actor speaking at that timestamp.
"""
from pathlib import Path
import argparse
import json
import subprocess

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rhubarb',required=True,type=Path)
    args=parser.parse_args()
    story=json.loads((ROOT/'story.json').read_text())
    dialogue='\n'.join(line for shot in story['scenes'] for _,line in shot['lines'])
    transcript=ROOT/'audio/dialogue_for_rhubarb.txt'
    transcript.write_text(dialogue+'\n')
    output=ROOT/'audio/rhubarb_cues.json'
    subprocess.run([str(args.rhubarb.resolve()),'-r','pocketSphinx','-f','json',
                    '--threads','2','-q','-d',str(transcript),'-o',str(output),
                    str(ROOT/'audio/narration.wav')],check=True)
    data=json.loads(output.read_text())
    cues=data.get('mouthCues',[])
    assert len(cues)>100, f'Unexpectedly few mouth cues: {len(cues)}'
    assert all(c['value'] in 'ABCDEFGHX' for c in cues)
    print(f'Saved {len(cues)} phoneme cues using open-source Rhubarb: {output}')


if __name__=='__main__':
    main()
