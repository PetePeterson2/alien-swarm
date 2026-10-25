# Music for Google Flow, after Alien Swarm's score

Three tracks in all: the briefing (you're making it) and **two loops** that do every other job.
Alien Swarm's other long cues (the elevator ride, the reactor finale, the holdout battle, the stims rush,
the two debriefs) all fold into these two. The short stings stay optional; the port already plays stock
SC2 sounds for them.

The house sound, measured from the game's `sound/music/*.wav`: dark industrial sci-fi, heavy sub-bass
(60–90 % of every track's energy is below 120 Hz), synths and processed percussion rather than an orchestra,
little high air, built around **D minor**, military tension rather than horror. Both loops are in D minor so
either can follow the briefing or the other.

## What each loop covers

| Loop | Replaces (original cue, length) | Where the port plays it |
|---|---|---|
| **A, Combat** `music_combat_loop.wav` | elevator ride (2:51, 108 bpm), reactor finale (1:24, 117 bpm), holdout battle (2:20, 130 half-time), stims rush (0:30) | the cargo lift's ride, Rydberg's last push, any holdout; while a stim's slow-motion lasts, the same loop muffled and quieter |
| **B, Aftermath** `music_aftermath_loop.wav` | debrief after a win (1:47, 62/124 bpm), debrief after a loss (3:37, slow), the briefing's tail | the stats screen after every mission, won or lost; the quiet between missions |

The originals' tempos sit at 108–130 bpm for action and 62–80 for the debriefs, so Loop A takes **120 bpm** and
Loop B **80 bpm**: whole bars then come out to round seconds.

## Making a loop that loops

Flow writes songs with an intro and an ending; a loop has neither. The prompts ask for that, but expect to
help it:
- Ask for **exactly the bar count** given. At 120 bpm, 32 bars is 64 s; at 80 bpm, 32 bars is 96 s.
- No intro, no fade, no ending. It starts mid-groove and ends on the bar before that same downbeat.
- If the take has an intro or an ending anyway, keep it. **I cut it to the bar grid, splice the end into
  the start with a short crossfade, and check the seam**, so a near-miss is fine. Just say which take you like.
- WAV is best. One file per loop, at the file name given.

---

## Loop A, Combat — `music_combat_loop.wav` (64 s: 32 bars at 120 bpm)

> Seamless looping dark electronic combat music for a sci-fi squad shooter, instrumental, no vocals.
> 120 BPM, D minor, exactly 32 bars (64 seconds), steady high intensity from the first beat to the last:
> no intro, no build-up, no ending, no fade. It must loop seamlessly: the last bar leads straight back
> into the first. A relentless driving groove: punchy industrial drums with metallic hits, a pounding
> distorted sub-bass line, sixteenth-note sequenced staccato synth arpeggios, a wide dark analog pad,
> and a grim, heroic lead motif (an analog lead doubled by low strings) that states a four-bar phrase
> over bars 9–16 and answers it over bars 25–32. Bars 17–24 thin the drums and add mechanical
> texture and alarms without dropping the energy. Gritty, urgent, mechanical: marines holding a
> corridor against an endless alien swarm. Heavy low end, little high air, punchy and clean.

What it takes from where: the arpeggio drive and bass from the elevator ride, the lead line over driving
percussion from the reactor finale, the metallic hits and half-time weight from the holdout. Bars 17–24
are the thinner stretch, so the loop doesn't wear out over a long fight.

## Loop B, Aftermath — `music_aftermath_loop.wav` (96 s: 32 bars at 80 bpm)

> Seamless looping dark ambient after-action music for a sci-fi military game, instrumental, no vocals.
> 80 BPM, D minor, exactly 32 bars (96 seconds), even intensity throughout: no intro, no ending, no fade.
> It must loop seamlessly: the last bar leads straight back into the first. Slowly shifting warm synth
> pads like a distant choir and low strings, a deep muffled boom on the first beat of every second bar,
> a soft steady ticking pulse like a clock or a heart monitor, sustained sub-bass notes, and a calm, slow
> synth motif that rises toward the major over bars 9–16 and settles back into the minor over bars
> 25–32. Bittersweet, tired, reflective: the squad back on the ship reviewing the mission, whether they
> won or lost. Muted and spacious, deep low end, almost no high frequencies.

What it takes from where: the deep booms and pitch-dropping low end from the winning debrief, the
choir-like pads and ticking pulse from the losing one. The motif leaning major then back to minor lets the
one loop sit under a win or a loss.

---

## Optional: short stings (each a few seconds, small)

Skip these to keep the file count down; the port already plays stock SC2 sounds for each moment. If you
want them anyway, one each:

- `music_sting.wav`, horde breaks through (the original's three 17 s stings, cut to one short one):
  > Horror-action shock sting, instrumental, no vocals, 6 seconds, D minor. A fast reversed swell into a
  > massive impact with a deep boom and crunching metal, then a short dissonant sub drone decaying to
  > silence by 0:06.
- `music_objective.wav`, objective done or mission won (original 8 s, F major):
  > Short victorious sci-fi sting, instrumental, no vocals, 5 seconds, F major. A quick swell into a warm,
  > wide low synth-brass chord with a bright bell-like synth tone above it, then a decay to silence by 0:05.
- `music_failed.wav`, squad wiped out (original 4.6 s, D minor):
  > Short grim mission-failed sting, instrumental, no vocals, 5 seconds, D minor. A heavy dark distorted
  > low chord with a thin high electronic whine like a flatlining monitor and a deep sub boom, decaying to
  > silence by 0:05.

## The briefing (yours), for reference

The original under the briefing: 119 s, about 76 bpm, D minor. Very dark and low (87 % sub-bass): a soft
15 s swell, slow pulsing low booms with sparse high ticks over a held pad, two waves of intensity (about
0:30 and 1:10), and a long pad tail fading out. Keep it in D minor and it will hand over cleanly to either loop.
