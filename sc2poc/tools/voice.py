"""The commander's voice: every level's LINES (tools/<level>.py), spoken by Microsoft's Edge neural voices
(edge-tts, online) and put through a radio filter, cached in assets/vo/ for build.py to pack.

    py tools/voice.py            voice the lines that are new or changed since the last run
    py tools/voice.py --all      voice every line again (after changing VOICE, RATE, PITCH or the filter)
    py tools/voice.py --raw K    also keep the unfiltered take of line K beside the clip, to compare
    py tools/voice.py --import D take recorded takes instead: D/<key>.wav (any rate, mono or stereo), through the
                                 radio filter (add --clean to keep them as recorded, only trimmed and levelled);
                                 an imported clip is kept until imported again (assets/vo/AI-STUDIO.md lists the takes)

assets/vo/manifest.json holds each clip's text, voice and length; build.py reads only that and the clips,
so a build never goes online. A line with no clip (or whose text changed) stays a subtitle until voiced.
"""
from pathlib import Path
import argparse, ast, asyncio, io, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'vo'
MANIFEST = OUT / 'manifest.json'
VOICE, RATE, PITCH = 'en-US-ChristopherNeural', '+6%', '-6Hz'   # Microsoft's "reliable, authority" newsreader
RATE_HZ = 24000                                                 # edge-tts speaks at 24 kHz mono
FILTER = 2                                                      # bump to re-voice every line after changing radio()


def lines():
    """Every top-level LINES dict in tools/*.py, read without importing the level modules."""
    found = {}
    for path in sorted((ROOT / 'tools').glob('*.py')):
        tree = ast.parse(path.read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'LINES' for t in node.targets):
                for key, text in ast.literal_eval(node.value).items():
                    assert key not in found, 'line %s in two levels' % key
                    found[key] = text
    return found


def speak(text):
    """The line as Edge says it: float mono samples at RATE_HZ."""
    import edge_tts, soundfile as sf

    async def fetch():
        audio = bytearray()
        async for chunk in edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH).stream():
            if chunk['type'] == 'audio':
                audio += chunk['data']
        return bytes(audio)

    data, rate = sf.read(io.BytesIO(asyncio.run(fetch())), dtype='float64')
    if data.ndim > 1:
        data = data.mean(axis=1)
    assert rate == RATE_HZ, rate
    return data


def band(x, lo, hi, soft=1.0):
    """Zero-phase band-pass by FFT with smooth (soft octaves wide) edges."""
    n = len(x)
    f = np.fft.rfftfreq(n, 1.0 / RATE_HZ)
    f[0] = 1e-3
    g = 1.0 / (1.0 + (lo / f) ** (4 / soft)) / (1.0 + (f / hi) ** (4 / soft))
    return np.fft.irfft(np.fft.rfft(x) * g, n)


def radio(voice, seed):
    """A field radio: a squelch click and a breath of static, the voice thinned to the telephone band and driven
    a little into the clip, a hiss under it, and the carrier dropping off with a click at the end."""
    rng = np.random.default_rng(seed)
    t = np.flatnonzero(np.abs(voice) > 0.01)
    voice = voice[max(t[0] - RATE_HZ // 50, 0):t[-1] + RATE_HZ // 10] if len(t) else voice
    voice = voice / (np.abs(voice).max() + 1e-9)
    lead, tail = int(0.16 * RATE_HZ), int(0.22 * RATE_HZ)
    x = np.concatenate([np.zeros(lead), voice, np.zeros(tail)])
    x = band(x, 320.0, 3300.0)
    x = np.tanh(2.6 * x / (np.abs(x).max() + 1e-9)) / np.tanh(2.6)
    # A faint ring on the voice: a short comb, as off a cheap speaker grille.
    d = int(0.0021 * RATE_HZ)
    x[d:] += 0.18 * x[:-d]
    n = len(x)
    hiss = band(rng.standard_normal(n), 900.0, 5200.0)
    hiss *= 0.035 / (hiss.std() + 1e-9)
    # The carrier: static swells in over the lead, sits under the voice, and cuts at the end.
    env = np.ones(n)
    env[:lead] = np.linspace(0.0, 1.0, lead) ** 0.5
    env[-tail // 2:] = 0.0
    x = x + hiss * env * (1.0 + 0.6 * (np.arange(n) < lead))
    for at, strength in ((int(0.02 * RATE_HZ), 0.55), (n - tail // 2, 0.4)):
        k = int(0.012 * RATE_HZ)
        click = band(rng.standard_normal(k), 600.0, 4500.0) * np.exp(-np.arange(k) / (0.0025 * RATE_HZ))
        x[at:at + k] += strength * click / (np.abs(click).max() + 1e-9)
    return 0.89 * x / (np.abs(x).max() + 1e-9)


def take(path):
    """A recorded take as float mono samples at RATE_HZ (linear resampling: the radio band is far below either rate)."""
    import soundfile as sf
    data, rate = sf.read(str(path), dtype='float64')
    if data.ndim > 1:
        data = data.mean(axis=1)
    if rate != RATE_HZ:
        n = int(round(len(data) * RATE_HZ / rate))
        data = np.interp(np.arange(n) * (rate / RATE_HZ), np.arange(len(data)), data)
    return data


def levelled(voice):
    """A take kept as recorded: trimmed to the speech with a short lead and tail, peak at -1 dB."""
    t = np.flatnonzero(np.abs(voice) > 0.01 * np.abs(voice).max())
    voice = voice[max(t[0] - RATE_HZ // 20, 0):t[-1] + RATE_HZ // 5] if len(t) else voice
    return 0.89 * voice / (np.abs(voice).max() + 1e-9)


def import_takes(folder, want, have, clean):
    import soundfile as sf
    found = {p.stem: p for p in Path(folder).glob('*.wav')}
    for key in sorted(set(found) - set(want)):
        print('no such line, skipped:', found[key].name)
    for n, key in enumerate(sorted(set(found) & set(want))):
        raw = take(found[key])
        clip = levelled(raw) if clean else radio(raw, n + 1)
        sf.write(OUT / (key + '.ogg'), clip.astype(np.float32), RATE_HZ, format='OGG', subtype='VORBIS')
        have[key] = {'text': want[key], 'voice': 'take:' + found[key].name, 'filter': 'clean' if clean else FILTER,
                     'seconds': round(len(clip) / RATE_HZ, 2)}
        print('%-20s %5.2f s  from %s' % (key, have[key]['seconds'], found[key].name))
    missing = sorted(set(want) - set(found))
    if missing:
        print('no take for: %s' % ', '.join(missing))


def main():
    import soundfile as sf
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--raw', action='append', default=[])
    ap.add_argument('--import', dest='folder')
    ap.add_argument('--clean', action='store_true')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    have = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    want = lines()
    if args.folder:
        import_takes(args.folder, want, have, args.clean)
        MANIFEST.write_text(json.dumps(have, indent=1, sort_keys=True) + '\n', encoding='utf-8')
        return
    made = 0
    for n, (key, text) in enumerate(sorted(want.items())):
        entry = have.get(key)
        # A recorded take stands until its line's text changes.
        if entry and entry.get('voice', '').startswith('take:') and entry['text'] == text and not args.all:
            continue
        stamp = {'text': text, 'voice': VOICE, 'rate': RATE, 'pitch': PITCH, 'filter': FILTER}
        if not args.all and key not in args.raw and entry and {k: entry.get(k) for k in stamp} == stamp and (OUT / (key + '.ogg')).exists():
            continue
        raw = speak(text)
        if key in args.raw:
            sf.write(OUT / (key + '.raw.wav'), raw, RATE_HZ)
        clip = radio(raw, n + 1)
        sf.write(OUT / (key + '.ogg'), clip.astype(np.float32), RATE_HZ, format='OGG', subtype='VORBIS')
        have[key] = dict(stamp, seconds=round(len(clip) / RATE_HZ, 2))
        made += 1
        print('%-20s %5.2f s  %s' % (key, have[key]['seconds'], text[:60]))
    for key in sorted(set(have) - set(want)):
        print('dropped', key)
        have.pop(key)
        (OUT / (key + '.ogg')).unlink(missing_ok=True)
    MANIFEST.write_text(json.dumps(have, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    print('%d voiced, %d lines in all' % (made, len(have)))


if __name__ == '__main__':
    sys.exit(main())
