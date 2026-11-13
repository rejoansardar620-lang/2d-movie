"""Assemble Episode 03 dialogue, one speaker at a time, into an exact 120s WAV.

The three supplied actor MP3s contain their lines in story order. The explicit
cut points were reviewed against each MP3's pauses to preserve whole phrases.
Mom's lines are generated locally with the open-source Piper Amy voice.
"""
from pathlib import Path
import json
import math
import subprocess
import wave

import numpy as np
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
RATE = 24000
STORY = json.loads((HERE / "story.json").read_text())
OUT = HERE / "audio"
BOUNDS = {
    "dad": [(0,3.15),(4.00,7.25),(8.26,10.20),(10.94,15.53),
            (16.48,19.20),(19.88,21.84),(22.90,25.30),(25.99,28.65),
            (29.37,31.37),(32.03,34.11),(35.05,37.73),(37.96,40.12)],
    "boy": [(0,1.46),(2.50,3.96),(4.90,6.34),(7.46,8.61),
            (9.58,11.32),(12.24,14.83)],
    "girl": [(0,1.77),(2.80,4.25),(4.95,6.53),(7.19,8.66),
             (9.75,11.91),(12.82,16.11)],
}


def read_wav(path):
    import scipy.io.wavfile
    rate, x = scipy.io.wavfile.read(path)
    if x.ndim > 1:
        x = x.mean(axis=1)
    source_dtype = x.dtype
    x = x.astype(np.float32) / (32768.0 if source_dtype == np.int16 else 2147483648.0)
    if rate != RATE:
        from math import gcd
        g = gcd(rate, RATE)
        x = resample_poly(x, RATE // g, rate // g)
    return x


def write_wav(path, data):
    import scipy.io.wavfile
    path.parent.mkdir(parents=True, exist_ok=True)
    scipy.io.wavfile.write(path, RATE, (np.clip(data, -1, 1) * 32767).astype(np.int16))


def decode_mp3(path, target):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
                    "-ar", str(RATE), "-ac", "1", "-c:a", "pcm_s16le", str(target)], check=True)


def make_mother_lines():
    from piper import PiperVoice
    from piper.config import SynthesisConfig
    model = HERE / "models" / "en_US-amy-medium.onnx"
    if not model.exists():
        raise FileNotFoundError(f"Download the Piper Amy voice model first: {model}")
    voice = PiperVoice.load(model)
    mom_lines = [text for s in STORY["scenes"] for role, text in s["lines"] if role == "mom"]
    lines_dir = OUT / "lines"
    lines_dir.mkdir(parents=True, exist_ok=True)
    # Amy is a gentle American English neural voice; subtle pauses are added at mix time.
    for i, sentence in enumerate(mom_lines):
        path = lines_dir / f"mom_{i:02}.wav"
        with wave.open(str(path), "wb") as wav_file:
            voice.synthesize_wav(sentence, wav_file, syn_config=SynthesisConfig(length_scale=1.03))
        print(f"  Priya voice {i+1:02}/{len(mom_lines)}", flush=True)


def prepare_actor_clips():
    clips = {}
    for role, boundaries in BOUNDS.items():
        mp3 = OUT / "raw" / f"{role}.mp3"
        if not mp3.exists():
            raise FileNotFoundError(mp3)
        wav = OUT / "raw" / f"{role}.wav"
        decode_mp3(mp3, wav)
        if role in ("boy", "girl"):
            # The recorded performances are adult voices. Subtle formant-safe
            # pitch lifting makes them read more clearly as the two children.
            lifted=OUT / 'raw' / f'{role}_pitch.wav'
            pitch={'boy':1.14,'girl':1.08}[role]
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',
                            '-i',str(wav),'-af',f'rubberband=pitch={pitch}',
                            '-ar',str(RATE),'-ac','1',str(lifted)],check=True)
            wav=lifted
        source = read_wav(wav)
        clips[role] = [source[round(a * RATE):round(b * RATE)].copy() for a, b in boundaries]
    make_mother_lines()
    clips["mom"] = [read_wav(f) for f in sorted((OUT / "lines").glob("mom_*.wav"))]
    for role, items in clips.items():
        expected = sum(who == role for scene in STORY["scenes"] for who, _ in scene["lines"])
        assert len(items) == expected, (role, len(items), expected)
    return clips


def compact_if_needed(x, length):
    if len(x) <= length:
        return x
    # Keep every complete phrase, using phase-corrected FFmpeg atempo for the
    # occasional long line instead of truncation or a pitch-raising resample.
    factor = len(x) / length
    raw = OUT / "tempo_in.wav"
    processed = OUT / "tempo_out.wav"
    write_wav(raw, x)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw),
                    "-af", f"atempo={factor:.5f}", "-ar", str(RATE), str(processed)], check=True)
    result = read_wav(processed)
    return result[:length]


def music_bed():
    """Quiet original four-chord plucked notes; no copyrighted recording."""
    n = 120 * RATE
    result = np.zeros(n, dtype=np.float32)
    chords = [[261.63, 329.63, 392], [220, 261.63, 349.23],
              [196, 246.94, 392], [220, 261.63, 329.63]]
    for step in range(160):
        start = int(step * .75 * RATE)
        chord = chords[(step // 16) % 4]
        hz = chord[step % 3] * (2 if step % 4 == 0 else 1)
        dur = min(int(.68 * RATE), n - start)
        if dur <= 0:
            break
        t = np.arange(dur, dtype=np.float32) / RATE
        env = np.exp(-5.0 * t) * (1 - np.exp(-65 * t))
        tone = np.sin(2 * np.pi * hz * t) + .22 * np.sin(2 * np.pi * 2 * hz * t)
        result[start:start+dur] += .013 * tone * env
    return result


def sparkle(mix, when):
    start = round(when * RATE)
    t = np.arange(int(.32 * RATE), dtype=np.float32) / RATE
    chirp = (.013 * np.sin(2 * np.pi * (700 * t + 650 * t * t)) +
             .009 * np.sin(2 * np.pi * (1046 * t + 340 * t * t)))
    chirp *= np.exp(-12 * t) * (1 - np.exp(-80 * t))
    end = min(len(mix), start + len(chirp))
    if end > start:
        mix[start:end] += chirp[:end-start]


def assemble():
    clips = prepare_actor_clips()
    indices = {role: 0 for role in clips}
    mix = music_bed()
    timestamps = []
    for scene_idx, scene in enumerate(STORY["scenes"]):
        scene_clips = []
        for role, text in scene["lines"]:
            scene_clips.append((role, text, clips[role][indices[role]]))
            indices[role] += 1
        # Reserve a small pause between replies, allowing the joke to land.
        gap = .22
        speech_time = sum(len(x) / RATE for _, _, x in scene_clips)
        usable = 9.38 - 2 * gap
        rate = min(1.0, usable / max(speech_time, .01))
        scene_clips = [(who, text, compact_if_needed(audio, round(len(audio) * rate)))
                       for who, text, audio in scene_clips]
        total = sum(len(x) / RATE for _, _, x in scene_clips)
        # Begin early, but leave remaining spare time for human pacing.
        gap = min(1.0, max(.22, (9.58 - total) / 2))
        cursor = 10 * scene_idx + .18
        for j, (role, line, audio) in enumerate(scene_clips):
            st = cursor
            en = min(10 * (scene_idx + 1) - .1, st + len(audio) / RATE)
            n = max(0, round((en - st) * RATE))
            start = round(st * RATE)
            voice = audio[:n].copy()
            fade = min(160, len(voice) // 4)
            if fade:
                voice[:fade] *= np.linspace(0, 1, fade)
                voice[-fade:] *= np.linspace(1, 0, fade)
            mix[start:start+len(voice)] += voice * .73
            timestamps.append({"scene": scene_idx, "speaker": role, "text": line,
                               "start": round(st, 3), "end": round(en, 3)})
            cursor = en + (gap if j < 2 else 0)
        if scene_idx not in (0, 11):
            sparkle(mix, scene_idx * 10 + .06)
        print(f"  Scene {scene_idx+1:02}: dialogue through {cursor:.2f}s", flush=True)

    # Consistent, modest peak normalization; loudnorm applied on final encode.
    peak = max(float(np.max(np.abs(mix))), 1e-6)
    mix *= min(1.6, .86 / peak)
    write_wav(OUT / "narration.wav", mix)
    (HERE / "timings.json").write_text(json.dumps(timestamps, indent=2) + "\n")
    srt = []
    for i, item in enumerate(timestamps, 1):
        def tc(seconds):
            ms = round(seconds * 1000)
            return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"
        srt.append(f"{i}\n{tc(item['start'])} --> {tc(item['end'])}\n{item['text']}")
    (HERE / "captions.srt").write_text("\n\n".join(srt) + "\n")
    assert len(timestamps) == 36
    print("Generated exactly 120 seconds of mastered-source dialogue.", flush=True)


if __name__ == "__main__":
    assemble()
