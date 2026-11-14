"""Original, generated sound effects for the animated film (no stock SFX).

These gentle effects sit below the already-mastered, licensed/source-verified
four-voice conversation and music. Rendered as deterministic PCM so a new
developer can reproduce it offline without cloud audio generation.
"""
from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter

ROOT=Path(__file__).resolve().parent
SR=48000
DURATION=120


def main():
    rng=np.random.default_rng(11013)
    out=np.zeros(SR*DURATION,dtype=np.float32)

    def insert(seconds,signal):
        begin=int(seconds*SR)
        if begin<0:return
        end=min(len(out),begin+len(signal))
        if end>begin:out[begin:end]+=signal[:end-begin]

    def chime(seconds,notes=(640,960),level=.010,duration=.48):
        t=np.arange(int(duration*SR))/SR
        env=(1-np.exp(-t*45))*np.exp(-t*7.5)
        wave=sum(np.sin(2*np.pi*n*t) for n in notes)/len(notes)
        insert(seconds,(wave*env*level).astype(np.float32))

    def footstep(seconds):
        t=np.arange(int(.18*SR))/SR
        body=np.sin(2*np.pi*(75+22*np.exp(-t*30))*t)
        grain=rng.standard_normal(len(t))*.22
        env=np.exp(-t*38)*(1-np.exp(-t*125))
        insert(seconds,((body+grain)*env*.023).astype(np.float32))

    def bird(seconds,base=1150):
        duration=.27
        t=np.arange(int(duration*SR))/SR
        f=base+620*np.sin(np.pi*t/duration)**2
        phase=np.cumsum(2*np.pi*f/SR)
        env=np.sin(np.pi*t/duration)**2
        insert(seconds,(np.sin(phase)*env*.013).astype(np.float32))

    # Footsteps approach each room entrance, staggered and volume-safe.
    for scene in (30,60,90):
        for step in range(11):
            footstep(scene+.16+.28*step)

    # Garden atmospheres and a warm, low-amplitude, filtered breeze.
    start=60*SR
    noise=rng.standard_normal(len(out)-start).astype(np.float32)
    air=lfilter([.004],[1,-.985],noise).astype(np.float32)
    out[start:]+=np.clip(air,-.012,.012)*.28
    for i,t in enumerate((63.2,65.4,69.6,73.1,77.2,89.4,93.0,97.4,102.7,109.4,114.9)):
        bird(t,base=1080+(i%4)*90)
        bird(t+.17,base=1460+(i%4)*110)

    # Water movement around the correctly placed pond lotus.
    for when in (70.55,72.18,74.8,76.4,78.3):
        t=np.arange(int(.45*SR))/SR
        env=np.exp(-t*8)
        ripple=np.sin(2*np.pi*(370-170*t)*t)*env*.008
        insert(when,ripple.astype(np.float32))

    # Tiny magical/comedic punctuations with original synthesised notes.
    for when,notes in ((15.4,(650,990)),(27.1,(490,720)),
                       (36.0,(940,1290)),(57.2,(720,980)),
                       (67.4,(880,1240)),(83.8,(580,920)),
                       (98.6,(740,1070)),(107.0,(460,690)),
                       (119.0,(830,1245,1660))):
        chime(when,notes)

    out=np.clip(out,-.14,.14)
    target=ROOT/'audio/premium_foley.wav'
    wavfile.write(target,SR,np.int16(out*32767))
    print(f'Wrote {target}: {DURATION}s at {SR}Hz, peak={float(abs(out).max()):.4f}')


if __name__=='__main__':main()
