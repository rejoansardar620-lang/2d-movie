"""Reproducible speech mastering without changing narration timing or pitch.

Uses only FFmpeg and the Python standard library. The source remains untouched;
the master and its measured loudness report are disposable render outputs.
"""
from pathlib import Path
import argparse
import hashlib
import json
import math
import subprocess

ROOT = Path(__file__).resolve().parent
TARGET_I = -16
TARGET_TP = -1.5
TARGET_LRA = 7
# Light cleanup and presence, without gating quiet consonants or adding reverb.
TONE = 'highpass=f=65,equalizer=f=240:t=q:w=0.8:g=-1.2,equalizer=f=2800:t=q:w=0.8:g=1.0'


def measure(source, filters=''):
    """Return EBU R128 measurements; fail on silence or an FFmpeg error."""
    norm = f'loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}:print_format=json'
    result = subprocess.run(
        ['ffmpeg', '-hide_banner', '-nostdin', '-i', str(source), '-af',
         ','.join(x for x in (filters, norm) if x), '-f', 'null', '-'],
        capture_output=True, text=True, check=True,
    )
    start = result.stderr.rfind('{')
    end = result.stderr.rfind('}')
    if start < 0 or end < start:
        raise RuntimeError('FFmpeg did not return loudness measurements')
    data = json.loads(result.stderr[start:end + 1])
    for key in ('input_i', 'input_tp', 'input_lra', 'input_thresh', 'target_offset'):
        if not math.isfinite(float(data[key])):
            raise ValueError(f'Unusable loudness measurement {key}; check for silent narration')
    return data


def master(source, destination):
    source, destination = Path(source), Path(destination)
    if source.resolve() == destination.resolve():
        raise ValueError('The mastered output must not overwrite the source')
    destination.parent.mkdir(parents=True, exist_ok=True)
    report_path = destination.with_suffix('.json')
    identity = hashlib.sha256(source.read_bytes() + Path(__file__).read_bytes()).hexdigest()
    if destination.exists() and report_path.exists():
        try:
            previous = json.loads(report_path.read_text())
            if previous.get('source_and_settings_sha256') == identity and previous.get('output_sha256') == hashlib.sha256(destination.read_bytes()).hexdigest():
                return destination
        except (ValueError, OSError):
            pass
    before = measure(source)
    shaped = measure(source, TONE)
    normalization = (
        f'loudnorm=I={TARGET_I}:TP={TARGET_TP}:LRA={TARGET_LRA}'
        f':measured_I={shaped["input_i"]}:measured_TP={shaped["input_tp"]}'
        f':measured_LRA={shaped["input_lra"]}:measured_thresh={shaped["input_thresh"]}'
        f':offset={shaped["target_offset"]}:linear=true'
    )
    partial = destination.with_name(destination.stem + '.partial' + destination.suffix)
    try:
        subprocess.run(
            ['ffmpeg', '-hide_banner', '-nostdin', '-loglevel', 'error', '-y',
             '-i', str(source), '-af', f'{TONE},{normalization}',
             '-ar', '48000', '-ac', '2', '-c:a', 'flac', '-sample_fmt', 's32', str(partial)],
            check=True,
        )
        after = measure(partial)
        if float(after['input_tp']) > TARGET_TP + 0.2:
            raise RuntimeError('Mastered audio exceeded the true-peak ceiling')
        if abs(float(after['input_i']) - TARGET_I) > 0.5:
            raise RuntimeError('Mastered audio missed the loudness target')
        partial.replace(destination)
        report = {
            'source_and_settings_sha256': identity,
            'output_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'source': source.name, 'filters': TONE,
            'target_lufs': TARGET_I, 'true_peak_ceiling_dbtp': TARGET_TP,
            'before': {k: before[k] for k in ('input_i', 'input_tp', 'input_lra')},
            'after': {k: after[k] for k in ('input_i', 'input_tp', 'input_lra')},
        }
        report_path.write_text(json.dumps(report, indent=2) + '\n')
        print(f'Voice master: {before["input_i"]} → {after["input_i"]} LUFS; '
              f'true peak {after["input_tp"]} dBTP', flush=True)
        return destination
    finally:
        partial.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'audio/narration.flac')
    parser.add_argument('--output', type=Path, default=ROOT / 'output/audio/narration_master.flac')
    args = parser.parse_args()
    print(master(args.source, args.output))
