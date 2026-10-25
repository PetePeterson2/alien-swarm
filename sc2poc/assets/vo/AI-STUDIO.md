# Commander lines for Google AI Studio

Where: AI Studio → **Generate speech**, model **Gemini 3.1 Flash TTS**, single speaker.
Voices to try for him: **Algenib** (gravelly), **Alnilam** or **Orus** (firm), **Gacrux** (mature).

Record him **clean**, with no radio effect asked for. `tools/voice.py` adds the radio afterwards, and that way
every line gets the same radio. Save each take as **`<key>.wav`** (the key is in the table), all in one folder.
Then:

    py tools/voice.py --import <that folder>            radio filter on
    py tools/voice.py --import <that folder> --clean    as recorded, only trimmed and levelled

Tags are Gemini's square-bracket audio tags, placed in the text. `[short pause]`, `[long pause]`, `[sigh]`,
`[shouting]`, `[whispering]`, `[fast]` and `[slow]` are documented. The mood tags (`[serious]`, `[urgent]`,
`[relieved]`, `[grim]`, `[tired]`) are among its 200-odd tags but untested here: if one gets read out loud
as a word, delete it. Sparse tags work better than one on every phrase. The words outside the tags must stay
exactly as written, because the subtitles show those words.

## Style instructions (paste into the style / scene box)

> A veteran military mission commander in his fifties, speaking to a four-marine squad over a field radio
> from the bridge of a ship in orbit. Low, gravelly American voice. Clipped, controlled, economical: he has
> run a hundred of these drops and does not waste words. Calm on the surface, with tension under it; never
> theatrical, never shouting unless a line says so. Brisk pace, a beat at full stops.

## The lines

| Key | Mission | Say |
|---|---|---|
| `co_m1_ob1` | Landing Bay | [serious] Bloodhound has docked. [short pause] Sweep the landing bay and get through the security gate to the inner perimeter. You'll need your tech to bypass the door locks. |
| `co_m1_ob2` | Landing Bay | [relieved] Good work, we have the flight data. [short pause] The lift to the lower level is past flight control. Get your squad to the exit. |
| `co_m1_ob3` | Landing Bay | That's the cargo lift ahead. [short pause] Get everyone aboard. |
| `co_m1_ob7` | Cargo Elevator | The cargo elevator at the end of this section is your way down to the colony. [short pause] Move. |
| `co_m1_ob8` | Cargo Elevator | [sigh] You're down. Get to the exit, the colony is through there. |
| `co_m2_start` | Deima | [grim] This is Deima. The swarm is using the colony's main pipeline as a highway between the hives. [short pause] Find that pipe and shut it down. |
| `co_m2_ob1b` | Deima | Gate's open. Take the catwalks north to the pump station, [short pause] and watch the drop. |
| `co_m2_pipeline` | Deima | The miners wired the main pipe with charges before they were overrun. [short pause] Get to the detonator and finish the job. |
| `co_m2_powerout` | Deima | Power's gone on the bridge ahead. [short pause] It'll be dark out there. |
| `co_m2_stayinlight` | Deima | Bloodhound will run alongside and light the way. [short pause] [serious] Stay inside her lamps. |
| `co_m2_onback` | Deima | The last span is down. [short pause] She's bringing herself in over the gap: you'll cross on her back. |
| `co_m2_getaccross` | Deima | [urgent] [fast] She can't hold there long. [shouting] Get across, now! |
| `co_m3_ob1` | Rydberg Reactor | This is the Rydberg plant. Get to the reactor core and bring the power back up: [short pause] the colony's running on batteries. |
| `co_m3_ob2` | Rydberg Reactor | [relieved] Reactor's online, power is coming back across the colony. [fast] Don't stop now, keep moving. |
| `co_m3_ob3` | Rydberg Reactor | [tired] Squad, listen. [long pause] [sigh] We've lost the colony. [short pause] [grim] Command is drawing up a plan to nuke the site from orbit. [short pause] Get through the north doors and head for the residential sector. |
| `co_m5_ob1` | Residential | This is the SynTek residential block, eggs and biomass right through it. [short pause] Burn the growth, smash every egg, then get to the elevators. |
| `co_m5_parasite` | Residential | [serious] Careful round those eggs: [short pause] whatever hatches goes straight for a marine. |
| `co_m5_more_bio` | Residential | More biomass in the mall. [short pause] Bullets won't touch it: use the flamer. |
| `co_m5_almost` | Residential | Nearly there. A few eggs left, [short pause] keep looking. |
| `co_m5_elevator` | Residential | That's the lot. [short pause] Get to the elevators and call one down. |
| `co_sj_ob1` | Sewer Junction | [serious] Sewer Junction B5. [short pause] The swarm is coming up a tunnel on the east side: find it and bring it down. [short pause] Then clear the eggs. |
| `co_sj_ob3` | Sewer Junction | That's the tunnel. There are charges stacked at its mouth: [short pause] shoot them from a distance. |
| `co_sj_ob4` | Sewer Junction | [grim] Eggs all along these walkways. [short pause] Smash every one. |

`co_m2_getaccross` is spelled the way the game spells it, so name the file exactly that.
