"""The marines' chatter (asw_marine_speech.cpp): every line a marine barks over its head, spoken in each of the
eight marines' own voices by Google's Gemini TTS (online), cut apart at its pauses, checked by a blind Gemini transcription,
trimmed and levelled, and cached in assets/barks/ for build.py to pack.

    py tools/barks.py                voice the clips that are new, changed or heard wrong last time
    py tools/barks.py --all          voice every clip again
    py tools/barks.py --only sarge   one marine (or a line kind: --only pain); with --all to redo just those
    py tools/barks.py --list         the clips and how each was heard, without going online

The API key is KEY in the repository's .env (a Google AI Studio key). The free tier allows only a few requests a
day a model, so each marine's lines are said in one take, a long pause between lines, and cut apart at the pauses;
one transcription request a marine checks the cut clips. A clip heard wrong is taken again on the next run
(with the others that failed).

assets/barks/manifest.json holds each clip's text, voice, direction and length; build.py reads only that and the
clips, so a build never goes online. A line with no clip (or whose text changed) stays text only until voiced.
"""
from pathlib import Path
import argparse, base64, difflib, io, json, re, sys, time, urllib.error, urllib.request
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'assets' / 'barks'
MANIFEST = OUT / 'manifest.json'
ENV = ROOT.parent / '.env'
API = 'https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent'
# Each model has its own daily quota on the free tier: the next is used when one runs out (same prebuilt voices).
# 3.1 refuses some whole takes (SAFETY: the infested and dying lines); 3.8-flash-lite-tts is left out, since it
# barely pauses between callouts and its takes do not cut.
TTS_MODELS = ['gemini-3.8-flash-tts', 'gemini-3.1-flash-tts-preview']
EAR_MODEL = 'gemini-3.5-flash'
RATE_HZ = 24000

# The lines by kind, in src/State.galaxy's AS_CH_* order (the index is the constant): key, the take's audio tag
# for it, and its lines.
BARKS = [
    ('ff', '[angry]', ["Watch your fire!", "Hey! Same side!", "Check your targets!"]),
    ('pain', '[pained]', ["Ugh!", "I'm hit!", "Argh!"]),
    ('painbig', '[shouting in pain]', ["I'm hit bad!", "Aagh! That hurt!"]),
    ('firing', '[shouting]', ["Contact! Engaging!", "Eat this!", "Take that, bug!"]),
    ('idle', '[uneasy, quiet]', ["Quiet. Too quiet.", "Anyone else hear that?", "Let's keep moving."]),
    ('down', '[shouting, alarmed]', ["Marine down!", "Man down!", "We lost one!"]),
    ('infested', '[panicked]', ["I'm infested! Medic!", "Something's inside me!"]),
    ('die', '[dying]', ["Aaargh...", "No...!"]),
    ('reload', '[urgent]', ["Reloading!", "Changing mags!", "Cover me, reloading!"]),
    ('close', '[panicked]', ["They're too close!", "Get it off me!"]),
    ('shieldbug', '[shouting]', ["Shieldbug! Hit it from behind!", "Big one! Shieldbug!"]),
    ('parasite', '[shouting]', ["Parasites! Don't let them latch on!", "Parasite!"]),
    ('eggs', '[tense, quiet]', ["Eggs. Careful.", "Alien eggs up ahead."]),
    ('noammo', '[frustrated]', ["I'm out of ammo!", "Dry! Need ammo!"]),
    ('hold', '[calm]', ["Holding here.", "Holding position."]),
    ('healing', '[reassuring]', ["Hold still, patching you up.", "Healing!"]),
]

# The eight marines in profile order (src/State.galaxy AS_ProfileSet; the key is the profile's face key):
# a Gemini prebuilt voice each, and who they are.
MARINES = [
    ('sarge', 'Rasalgethi', 'a gruff, gravel-voiced veteran master sergeant in his late forties, hard and commanding'),
    ('wildcat', 'Kore', 'a fierce, fiery young woman, a special weapons marine with a hard edge'),
    ('faith', 'Sulafat', 'a warm, steady woman in her thirties, a devoted field medic'),
    ('crash', 'Puck', 'a cocky nineteen-year-old hacker, quick and a little nervous'),
    ('jaeger', 'Fenrir', 'a loud, brash, fearless soldier from a long line of soldiers'),
    ('wolfe', 'Zubenelgenubi', 'a hard, terse ex-convict, a heavy weapons marine of few words'),
    ('bastille', 'Iapetus', 'a calm, wary combat medic with a faint French accent'),
    ('vegas', 'Sadachbia', 'a smooth-talking gambler with an Italian-American accent'),
]


def clips():
    """{clip key: (marine, kind, n, text, voice, tag)} for every marine and line."""
    voices = {face: voice for face, voice, _ in MARINES}
    return {'%s_%s_%d' % (face, kind, n): (face, kind, n, text, voices[face], tag)
            for face, _, _ in MARINES for kind, tag, texts in BARKS for n, text in enumerate(texts)}


def api_key():
    for line in ENV.read_text(encoding='utf-8').splitlines():
        if line.startswith('KEY='):
            return line[4:].strip()
    sys.exit('no KEY= in %s' % ENV)


class OutOfQuota(Exception):
    pass


class NoAudio(Exception):
    """The model answered with no audio: a long take some models will not finish."""


def call(model, body, key):
    """One generateContent call. Busy (503) and per-minute limits are waited out; the day's quota is not."""
    for attempt in range(6):
        req = urllib.request.Request(API % model, data=json.dumps(body).encode(),
                                     headers={'x-goog-api-key': key, 'Content-Type': 'application/json'})
        try:
            return json.load(urllib.request.urlopen(req, timeout=300))
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', 'replace')
            if e.code == 429 and 'PerDay' in err:
                raise OutOfQuota('%s: the free tier\'s requests for today are used up' % model)
            if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise RuntimeError('%s %d: %s' % (model, e.code, err[:300]))
            wait = re.search(r'"retryDelay": "(\d+)', err)
            time.sleep(min(int(wait.group(1)) + 1, 90) if wait else 10 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            if attempt == 5:
                raise
            time.sleep(10 * (attempt + 1))


def decode(part):
    """An inlineData audio part as float mono samples at RATE_HZ."""
    import soundfile as sf
    raw = base64.b64decode(part['data'])
    if part['mimeType'].startswith('audio/wav'):
        data, rate = sf.read(io.BytesIO(raw), dtype='float64')
    else:  # audio/l16; rate=24000: raw 16-bit little-endian PCM
        rate = int(re.search(r'rate=(\d+)', part['mimeType']).group(1))
        data = np.frombuffer(raw, '<i2').astype(np.float64) / 32768.0
    if data.ndim > 1:
        data = data.mean(axis=1)
    if rate != RATE_HZ:
        n = int(round(len(data) * RATE_HZ / rate))
        data = np.interp(np.arange(n) * (rate / RATE_HZ), np.arange(len(data)), data)
    return data


def prompt(who, lines):
    """A take's prompt in Gemini's director's-notes layout: everything above the transcript is direction, never read
    out. The lines (tag, text) a long pause apart."""
    script = '\n[long pause]\n'.join('%s %s' % (tag, text) for tag, text in lines)
    return ('# AUDIO PROFILE\n%s, a space marine.\n\n'
              '## THE SCENE\nThe dark corridors of a derelict colony, fighting an alien swarm.\n\n'
              '### DIRECTOR\'S NOTES\nEach line of the transcript is a separate callout in the heat of a fight, in the '
              'mood its bracketed tag gives. A long silence between callouts.\n\n'
            '#### TRANSCRIPT\n%s' % (who[0].upper() + who[1:], script))


def take(model, who, voice, lines, key):
    """One take of a marine's lines (tag, text), a long pause between each."""
    body = {'contents': [{'parts': [{'text': prompt(who, lines)}]}],
            'generationConfig': {'responseModalities': ['AUDIO'],
                                 'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': voice}}}}}
    reply = call(model, body, key)['candidates'][0]
    if 'content' not in reply:
        raise NoAudio('%s gave no audio for %d lines (%s)' % (model, len(lines), reply.get('finishReason')))
    return decode(reply['content']['parts'][0]['inlineData'])


def islands(audio):
    """The take's stretches of speech as (start, end) seconds, split at pauses of 0.55 s or more. A 10 ms frame is
    speech above half the geometric mean of the take's silence (its quietest fifth) and its speech (its loudest tenth),
    so a soft-spoken marine's cries count as well as a loud one's. A take's pauses between callouts run 0.6 to 2 s,
    the breaks inside one under half a second."""
    hop = RATE_HZ // 100
    rms = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, 'same')[::hop])
    loud = np.concatenate([[False], rms > 0.5 * np.sqrt(np.percentile(rms, 20) * np.percentile(rms, 90)), [False]])
    flips = np.flatnonzero(np.diff(loud.astype(int)))
    out = []
    for on, off in zip(flips[::2], flips[1::2]):
        if out and on / 100.0 - out[-1][1] < 0.55:
            out[-1] = (out[-1][0], off / 100.0)
        elif off - on >= 6:                     # a click or breath shorter than 60 ms is not a callout
            out.append((on / 100.0, off / 100.0))
    return out


def breaks(text):
    return len(re.findall(r'[.!?,] ', text.strip()))


def assign(spans, texts):
    """The stretches handed to the lines in order, each line one or more stretches in a row (more only where the line
    has a sentence break to pause at), by least squared log error against a length fitted to the lines' letters.
    [(start, end)] a line, or None when the take has fewer stretches than lines (two callouts run together) or more
    than a few extra (words said that are not in the script, such as a tag read out)."""
    n, m = len(texts), len(spans)
    if m < n or m > n + max(2, n // 10):
        return None
    size = np.array([len(re.sub(r'[^A-Za-z]', '', t)) for t in texts], float)
    rate = sum(b - a for a, b in spans) / size.sum()
    lo = 0.0
    for _ in range(3):
        want = np.maximum(lo + rate * size, 0.25)
        best = {(0, 0): (0.0, None)}
        for i in range(1, n + 1):
            for j in range(i, m - (n - i) + 1):
                for k in range(1, min(breaks(texts[i - 1]) + 1, j) + 1):
                    prev = best.get((i - 1, j - k))
                    if prev is None:
                        continue
                    dur = spans[j - 1][1] - spans[j - k][0]
                    cost = prev[0] + np.log(dur / want[i - 1]) ** 2 + 0.05 * (k - 1)
                    if (i, j) not in best or cost < best[(i, j)][0]:
                        best[(i, j)] = (cost, k)
        if (n, m) not in best:
            return None
        out, j = [], m
        for i in range(n, 0, -1):
            k = best[(i, j)][1]
            out.append((spans[j - k][0], spans[j - 1][1]))
            j -= k
        out.reverse()
        dur = np.array([b - a for a, b in out])
        rate, lo = np.polyfit(size, dur, 1)
    return out


def piece(audio, cuts, i):
    """Line i's clip: its stretch widened into the pauses either side (up to their middles) so a soft start or a
    trailing breath is not lost, then trimmed to 2% of its own peak, so a quiet line keeps its quiet words."""
    a, b = cuts[i]
    lo = (cuts[i - 1][1] + a) / 2 if i else 0.0
    hi = (b + cuts[i + 1][0]) / 2 if i + 1 < len(cuts) else len(audio) / RATE_HZ
    x = audio[int(max(a - 0.25, lo) * RATE_HZ):int(min(b + 0.45, hi) * RATE_HZ)]
    hop = RATE_HZ // 100
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same'))
    on = np.flatnonzero(rms > 0.02 * rms.max())
    return levelled(x[on[0]:on[-1] + 1] if len(on) else x)


def levelled(voice):
    """A short lead and tail around the speech, faded at both ends, peak at -1 dB."""
    lead, tail = RATE_HZ // 40, RATE_HZ // 8
    voice = np.concatenate([np.zeros(lead), voice, np.zeros(tail)])
    k = RATE_HZ // 200
    voice[:lead + k] *= np.clip(np.arange(lead + k) / (lead + k), 0, 1)
    voice[-tail:] *= np.linspace(1.0, 0.0, tail) ** 2
    return 0.89 * voice / (np.abs(voice).max() + 1e-9)


def hear(pieces, key):
    """What Gemini hears in each clip, blind (no script given), in one request: the clips one after another with two
    seconds of silence between them, transcribed as one string a clip."""
    import soundfile as sf
    gap = np.zeros(2 * RATE_HZ)
    buf = io.BytesIO()
    sf.write(buf, np.concatenate([x for p in pieces for x in (p, gap)]).astype(np.float32), RATE_HZ, format='WAV', subtype='PCM_16')
    ask = ('This recording holds %d short shouted callouts, one after another, with two seconds of silence between '
           'them. Transcribe each callout word for word, writing a cry or groan as a word (Ugh, Argh). Reply with a JSON '
           'array of %d strings, one a callout in order.' % (len(pieces), len(pieces)))
    body = {'contents': [{'parts': [{'inlineData': {'mimeType': 'audio/wav', 'data': base64.b64encode(buf.getvalue()).decode()}},
                                    {'text': ask}]}],
            'generationConfig': {'temperature': 0.0, 'responseMimeType': 'application/json'}}
    reply = call(EAR_MODEL, body, key)['candidates'][0]['content']['parts']
    heard = [str(h) for h in json.loads(''.join(p.get('text', '') for p in reply))]
    return heard if len(heard) == len(pieces) else None


def words(s):
    """The words, with every spelling of a cry (Aagh, Argh, Ugh, Gah) as one word."""
    out = re.sub(r'[^a-z ]', '', s.lower().replace("'", '').replace('-', ' ')).split()
    return ['(cry)' if re.fullmatch(r'a+r*g+h*|u+g+h+|g+a+h+|a+h+|a+r+g+h+|o+w+', w) else w for w in out]


def matches(text, heard):
    """A clip passes when the transcription has the line's words. A bare cry ("Ugh!", "Aaargh...") passes on being
    short, since a transcriber spells a cry any way it likes."""
    want, got = words(text), words(heard)
    if len(want) <= 1 and len(text) <= 10:
        return 1 <= len(got) <= 2 or (not got and heard.strip() != '')
    return difflib.SequenceMatcher(None, want, got).ratio() >= 0.8


def load(path):
    """A saved or hand-recorded take as float mono samples at RATE_HZ."""
    import soundfile as sf
    data, rate = sf.read(str(path), dtype='float64')
    if data.ndim > 1:
        data = data.mean(axis=1)
    if rate != RATE_HZ:
        n = int(round(len(data) * RATE_HZ / rate))
        data = np.interp(np.arange(n) * (rate / RATE_HZ), np.arange(len(data)), data)
    return data


def write_script():
    """The takes to record by hand in Google AI Studio, one a marine, the marines still to voice first."""
    have = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    todo = [face for face, _, _ in MARINES if not all(have.get(k, {}).get('ok') for k in clips() if k.startswith(face + '_'))]
    out = ['# Marine chatter for Google AI Studio', '',
           'Where: AI Studio, **Generate speech**, model **Gemini 3.8 Flash TTS** (or the newest Flash TTS), single speaker.',
           'For each marine: pick the voice named below, paste the whole prompt block into the text box, run it, and',
           'download the take as **`<marine>.wav`**, all in one folder. One take holds all 38 lines; `tools/barks.py`',
           'cuts it at the pauses and checks every clip with a transcription. Then:', '',
           '    py tools/barks.py --import <that folder>', '',
           'A take that skips a line, reads a tag out loud or runs two lines together fails the check for those clips',
           '(the run lists them): record that marine again. Marines still to voice: **%s**.' % (', '.join(todo) or 'none'), '']
    lines = [(tag, text) for _, tag, texts in BARKS for text in texts]
    for face, voice, who in sorted(MARINES, key=lambda m: m[0] not in todo):
        out += ['## %s%s (voice: %s)' % (face, '' if face in todo else ', done', voice), '', '```', prompt(who, lines), '```', '']
    (OUT / 'AI-STUDIO.md').write_text('\n'.join(out), encoding='utf-8')
    print('wrote', OUT / 'AI-STUDIO.md', '- to voice:', ', '.join(todo) or 'none')


def main():
    import soundfile as sf
    ap = argparse.ArgumentParser()
    ap.add_argument('--all', action='store_true')
    ap.add_argument('--only', action='append', default=[])
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--keep', help='also save each raw take to this folder as <marine>.wav')
    ap.add_argument('--take', action='append', default=[], help='MARINE=PATH: cut a saved take instead of a new one')
    ap.add_argument('--import', dest='folder', help='cut the takes recorded by hand in this folder (<marine>.wav, AI-STUDIO.md)')
    ap.add_argument('--script', action='store_true', help='write assets/barks/AI-STUDIO.md, the takes to record by hand')
    args = ap.parse_args()
    if args.script:
        return write_script()
    takes = {f: load(path) for f, path in (t.split('=', 1) for t in args.take)}
    if args.folder:
        for face, _, _ in MARINES:
            if (Path(args.folder) / (face + '.wav')).exists():
                takes[face] = load(Path(args.folder) / (face + '.wav'))
        args.only, args.all = args.only or sorted(takes), True
    OUT.mkdir(parents=True, exist_ok=True)
    have = json.loads(MANIFEST.read_text(encoding='utf-8')) if MANIFEST.exists() else {}
    want = clips()
    if args.list:
        for name in sorted(want):
            e = have.get(name)
            print('%-24s %s' % (name, '%5.2f s  %s  heard "%s"' % (e['seconds'], 'ok ' if e['ok'] else 'OFF', e['heard']) if e else '-'))
        return
    for name in sorted(set(have) - set(want)):
        print('dropped', name)
        have.pop(name)
        (OUT / (name + '.ogg')).unlink(missing_ok=True)
    who = {face: (voice, desc) for face, voice, desc in MARINES}
    todo = {}
    for name, spec in sorted(want.items(), key=lambda kv: (kv[1][0], [b[0] for b in BARKS].index(kv[1][1]), kv[1][2])):
        face, kind, n, text, voice, tag = spec
        if args.only and face not in args.only and kind not in args.only:
            continue
        stamp = {'text': text, 'voice': voice, 'tag': tag}
        entry = have.get(name)
        if not args.all and entry and entry['ok'] and {k: entry.get(k) for k in stamp} == stamp and (OUT / (name + '.ogg')).exists():
            continue
        todo.setdefault(face, []).append((name, spec, stamp))
    key = api_key()
    made = 0
    models = list(TTS_MODELS)
    queue = list(todo.items())
    try:
        while queue:
            face, jobs = queue.pop(0)
            voice, desc = who[face]
            texts = [spec[3] for _, spec, _ in jobs]
            if face in takes:
                audio = takes[face]
            else:
                try:
                    audio = take(models[0], desc, voice, [(spec[5], spec[3]) for _, spec, _ in jobs], key)
                except OutOfQuota as e:
                    if len(models) == 1:
                        raise
                    print(e, '- on to', models[1])
                    models.pop(0)
                    queue.insert(0, (face, jobs))
                    continue
                except NoAudio as e:
                    if len(jobs) == 1:
                        print(e)
                        continue
                    # Half the lines a take, as many times as it takes.
                    print(e, '- halves')
                    queue[:0] = [(face, jobs[:len(jobs) // 2]), (face, jobs[len(jobs) // 2:])]
                    continue
                if args.keep:
                    sf.write(Path(args.keep) / ('%s-%s.wav' % (face, jobs[0][0].split('_', 1)[1])), audio.astype(np.float32), RATE_HZ)
            cuts = assign(islands(audio), texts)
            if cuts is None:
                print('%s: the take does not cut into its callouts (%d stretches for %d lines); run again for a new take'
                      % (face, len(islands(audio)), len(texts)))
                continue
            pieces = [piece(audio, cuts, i) for i in range(len(cuts))]
            heard = hear(pieces, key) or [''] * len(pieces)
            for (name, spec, stamp), clip, h in zip(jobs, pieces, heard):
                secs = len(clip) / RATE_HZ
                ok = matches(spec[3], h) and secs <= 1.5 + 0.15 * len(spec[3])
                # A clip that fails the check is kept only when there was none before, to listen to; build.py
                # packs only the ones that passed.
                if ok or name not in have or not (OUT / (name + '.ogg')).exists():
                    sf.write(OUT / (name + '.ogg'), clip.astype(np.float32), RATE_HZ, format='OGG', subtype='VORBIS')
                    have[name] = dict(stamp, model=models[0] if face not in takes else 'take', seconds=round(secs, 2), heard=h, ok=ok)
                    made += 1
                print('%-24s %5.2f s  %s  "%s" heard "%s"' % (name, secs, 'ok ' if ok else 'OFF', spec[3], h))
            MANIFEST.write_text(json.dumps(have, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    except OutOfQuota as e:
        print(e, '- every TTS model is out of quota; run again tomorrow for the rest')
    MANIFEST.write_text(json.dumps(have, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    off = sorted(n for n, e in have.items() if not e['ok'])
    print('%d voiced, %d of %d clips in all%s' % (made, len(have), len(want), '; heard off: ' + ', '.join(off) if off else ''))


if __name__ == '__main__':
    sys.exit(main())
