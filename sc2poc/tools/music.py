"""The score: long Flow takes cut to short seamless loops and packed small, into assets/music/ for build.py.

    py tools/music.py <folder>          cut every take in TRACKS found in <folder> (<file>.wav)
    py tools/music.py <folder> --check  only report the loops it would cut and their seams

Each take is a few minutes with an intro and an ending; the map wants a loop of a fraction of that. The
loop is found, not guessed: the tempo from the take's onsets, then every start in its steady stretch and
every whole number of bars in LOOP_SECS is scored by how alike the music is just before and just after
the start and the end (log-spectra over half a second each side); the best pair is nudged to the sample
where the waveforms line up, and the end is crossfaded into the start so the loop has no seam. Then
32 kHz stereo Vorbis at QUALITY: the takes have under 0.03 % of their energy above 11 kHz, so 32 kHz
loses nothing; stereo stays (the aftermath pads are wide), Vorbis codes the two channels jointly.

assets/music/manifest.json keeps each loop's length and where in its take it came from.
"""
from pathlib import Path
import argparse, json, sys
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'music'
MANIFEST = OUT / 'manifest.json'
# id: (take file, loop seconds wanted (min, max)). Briefing and aftermath sit under menus for a minute or two;
# combat under a fight, so it loops more and gets a little more length to wear better.
TRACKS = {
    'briefing': ('music_briefing.wav', (36.0, 52.0)),
    'combat': ('music_combat_loop.wav', (40.0, 56.0)),
    'aftermath': ('music_aftermath_loop.wav', (36.0, 52.0)),
}
RATE = 32000
QUALITY = 0.15          # Vorbis quality 0..1 (soundfile compression_level is the inverse): about 60 kbit/s at 32 kHz
FADE = 0.35             # the crossfade over the seam, seconds
N, HOP = 2048, 512


def spec(x, r):
    w = np.hanning(N)
    frames = np.lib.stride_tricks.sliding_window_view(x, N)[::HOP] * w
    S = np.abs(np.fft.rfft(frames, axis=1))
    f = np.fft.rfftfreq(N, 1 / r)
    edges = np.geomspace(40, 12000, 49)
    bands = np.stack([S[:, (f >= a) & (f < b)].sum(axis=1) for a, b in zip(edges[:-1], edges[1:])], axis=1)
    return np.log(bands + 1e-6)


def tempo(L, r):
    """Beats per minute from the onset envelope's autocorrelation, folded into 70..150."""
    flux = np.maximum(np.diff(L, axis=0), 0).sum(axis=1)
    flux -= flux.mean()
    ac = np.correlate(flux, flux, 'full')[len(flux) - 1:]
    dt = HOP / r
    lags = np.arange(len(ac)) * dt
    ok = (lags > 60 / 150) & (lags < 60 / 70)
    k = np.argmax(np.where(ok, ac, -np.inf))
    # refine the peak by a parabola through its neighbours
    a, b, c = ac[k - 1], ac[k], ac[k + 1]
    k = k + 0.5 * (a - c) / (a - 2 * b + c)
    return 60 / (k * dt), ac[int(round(k))] / ac[0]


def find_loop(x, r, secs):
    mono = x.mean(axis=1)
    L = spec(mono, r)
    bpm, conf = tempo(L, r)
    beat = 60 / bpm
    energy = L.max(axis=1)
    loud = energy > np.median(energy) - 2.0
    # the steady stretch: from the first second the take is loud to the last (no intro, no ending)
    on = np.flatnonzero(np.convolve(loud, np.ones(40) / 40, 'same') > 0.9)
    lo, hi = on[0] + 20, on[-1] - 20
    W = int(0.5 * r / HOP)
    Z = (L - L.mean(axis=0)) / (L.std(axis=0) + 1e-6)
    sq = np.concatenate([[0.0], np.cumsum((Z * Z).sum(axis=1))])
    best = None
    # Whole phrases (bars a multiple of 4), the length free by a few frames round the tempo's guess: a tempo
    # off by a fraction of a percent is a tenth of a second over a loop this long.
    for bars in range(4, int(secs[1] / (4 * beat)) + 1, 4):
        n0 = int(round(bars * 4 * beat * r / HOP))
        if n0 * HOP / r < secs[0]:
            continue
        for n in range(n0 - 12, n0 + 13):
            dot = np.concatenate([[0.0], np.cumsum((Z[:-n] * Z[n:]).sum(axis=1))])
            a = np.arange(max(lo, W), min(hi - n, len(Z) - n - W))
            if not len(a):
                continue
            num = dot[a + W] - dot[a - W]
            den = np.sqrt((sq[a + W] - sq[a - W]) * (sq[a + n + W] - sq[a + n - W])) + 1e-9
            s = num / den
            k = int(np.argmax(s))
            if best is None or s[k] > best[0]:
                best = (float(s[k]), int(a[k]), n, bars)
    s, a, n, bars = best
    # to the sample: the lag around the frame guess where the two waveforms agree best
    A, E = a * HOP, (a + n) * HOP
    span, w = int(0.02 * r), int(0.05 * r)
    ref = mono[A:A + w]
    lags = range(-span, span + 1)
    corr = [float(ref @ mono[E + k:E + k + w]) for k in lags]
    E += list(lags)[int(np.argmax(corr))]
    return {'bpm': round(bpm, 2), 'pulse': round(float(conf), 2), 'bars': bars, 'start': A / r, 'end': E / r,
            'seconds': round((E - A) / r, 3), 'match': round(s, 3)}, A, E


def splice(x, A, E, r):
    """x[A:E] with the music after E faded in over its first FADE seconds: playing it end to start is
    then what the take plays at E (equal-power crossfade)."""
    f = int(FADE * r)
    loop = x[A:E].copy()
    t = np.linspace(0, np.pi / 2, f)[:, None]
    loop[:f] = x[A:A + f] * np.sin(t) + x[E:E + f] * np.cos(t)
    return loop


def resample(x, r):
    if r == RATE:
        return x
    n = int(round(len(x) * RATE / r))
    pos = np.arange(n) * (r / RATE)
    return np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(x.shape[1])], axis=1)


def main():
    import soundfile as sf
    ap = argparse.ArgumentParser()
    ap.add_argument('folder')
    ap.add_argument('--check', action='store_true')
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    have = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    for key, (name, secs) in TRACKS.items():
        src = Path(args.folder) / name
        if not src.exists():
            print('%-10s no %s' % (key, name))
            continue
        x, r = sf.read(str(src), dtype='float64', always_2d=True)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, axis=1)
        x = resample(x[:, :2], r)
        info, A, E = find_loop(x, RATE, secs)
        print('%-10s %s: %.1f bpm (pulse %.2f), %d bars = %.2f s from %.2f s, seam match %.3f'
              % (key, name, info['bpm'], info['pulse'], info['bars'], info['seconds'], info['start'], info['match']))
        if args.check:
            continue
        loop = splice(x, A, E, RATE)
        loop *= 0.95 / max(np.abs(loop).max(), 1e-9)
        path = OUT / (key + '.ogg')
        # In blocks: libsndfile's Vorbis encoder crashes the process on one big write.
        with sf.SoundFile(str(path), 'w', RATE, 2, format='OGG', subtype='VORBIS', compression_level=1.0 - QUALITY) as f:
            for i in range(0, len(loop), 1 << 15):
                f.write(loop[i:i + (1 << 15)].astype(np.float32))
        info.update(take=name, bytes=path.stat().st_size)
        have[key] = info
        print('%-10s -> %s, %d KB' % ('', path.name, path.stat().st_size // 1024))
    if not args.check:
        MANIFEST.write_text(json.dumps(have, indent=1, sort_keys=True) + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
