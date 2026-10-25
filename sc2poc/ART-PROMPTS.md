# Halcyon Drift — UI art prompts for Nano Banana

Ten images (some are sets) to replace the drawn-in-code art on the character select, weapon select,
mission select and in-game HUD. Each section says where the image goes, the size it is shown at,
the background to use, the file name to save it under, and the prompt to paste.

Save every result as PNG in `sc2poc/assets/ui-gen/` under the file name given, so they can be keyed,
resized and packed into the map.

---

## Read this first (for Gemini)

You are making UI art for an original top-down sci-fi squad shooter called **Halcyon Drift**:
four space marines fighting an insectoid alien swarm through derelict colony facilities.
Every image in this file belongs to one set and must look like it.

**Style bible — apply to every prompt below:**

- Gritty military sci-fi, 2000s–2010s PC game UI. Worn painted metal, scuffs, stencils, hazard paint.
  Not cartoon, not anime, not photoreal live action: a painted 3D game-art render.
- Palette: deep navy-black `#0C141E`, gunmetal and steel-blue panels, a cool cyan-blue accent
  `#5AB4F0` for lights and edges, white for line icons, amber `#F0A030` and hazard orange for warnings,
  alien green-yellow ichor only on alien things.
- Lighting: a cold key light from the top left, cyan rim light, deep shadows.
- **No text, letters, numbers, logos or watermarks** anywhere in the image unless a prompt asks for it.
  The game draws all text itself.
- Original designs only. Do not imitate any existing game's characters, logos or UI.

**Backgrounds (the game needs to cut every image out):**

Nano Banana cannot output true transparency, and asking for "transparent" makes it paint a fake grey
checkerboard into the image. Instead each prompt asks for one of two flat backgrounds, which are
removed afterwards:

- **KEY = MAGENTA** — the subject sits on a perfectly flat, uniform pure magenta `#FF00FF` background,
  no gradient, no floor, no cast shadow, no vignette, no reflections of the magenta on the subject.
  The subject itself must contain no magenta or pink.
- **KEY = BLACK** — for glowing, holographic or light-only elements: a perfectly flat pure black
  `#000000` background. These are blended additively in game, so black disappears.

**Consistency:** when a section is a set (the 8 marines, the guns, the items), generate the first one,
then generate the rest one at a time in the same conversation saying "same style, framing, lighting,
scale and background as the previous image" so the set matches.

---

## 1. Marine portraits (character select) — set of 8

**Where:** the roster's portrait cards and the briefing's squad rows (shown in a circle ~150 px),
and the in-game HUD portrait (~110 px). **Aspect:** 1:1, generate at 1024×1024. **KEY = MAGENTA.**
**Files:** `portrait_<name>.png` (e.g. `portrait_sarge.png`).

Template — replace the bracketed part with the marine's line below:

```
A head-and-shoulders portrait of a space marine for a sci-fi game's character select screen,
painted 3D game-art render. The marine faces the camera turned slightly to their right, centred,
filling the frame from mid-chest to just above the helmet. Bulky armoured shoulder pads and chest
plate, a high armoured collar. The helmet's visor is raised so the face is visible.
[MARINE DESCRIPTION]
Cold key light from the top left, a cyan-blue rim light on the right edge, dramatic but readable,
face clearly lit. Worn, scuffed painted armour with small stencil markings (no readable text).
Background: perfectly flat uniform pure magenta #FF00FF, no gradient, no shadow, no floor, nothing
behind the marine. No magenta or pink on the marine. No text, no logo, no frame, no border.
```

Marine lines (the helmet colours match the current in-game portraits, keep them):

- **sarge** — Officer. A gruff, hard-faced man in his late forties, grey stubble, a scar through one
  eyebrow. Olive-drab helmet with a yellow stripe down the centre, orange visor glass. Officer's
  chevrons painted on the shoulder pad.
- **wildcat** — Special Weapons. A fierce young woman, mid-twenties, sharp features, a defiant glare,
  dark hair tied back. Rust-brown helmet with a blue centre stripe, red-orange visor glass. Heavy
  ammo-feed harness over the shoulder.
- **faith** — Medic. A warm, steady woman in her thirties, calm eyes, a faint smile. White helmet with
  a red centre stripe, ice-blue visor glass. A white medical cross patch on the shoulder pad.
- **crash** — Tech. A cocky nineteen-year-old hacker, a smirk, slightly nervous eyes, a headset mic.
  Gold helmet with a gold visor glass. A small data-pad and cabling clipped at the collar.
- **jaeger** — Officer. A loud, brash, fearless young soldier with a square jaw and a buzz cut, a grin.
  Steel-blue helmet with a yellow centre stripe, cyan visor glass. Officer's chevrons on the shoulder.
- **wolfe** — Special Weapons. A hard, terse ex-convict in his forties, shaved head, prison tattoo on the
  neck, a cold stare. Gunmetal-grey helmet with a blue centre stripe, orange visor glass.
- **bastille** — Medic. A calm, wary combat medic in his thirties, neat beard, watchful eyes. Silver
  helmet with a red centre stripe, orange visor glass. A medical cross patch on the shoulder pad.
- **vegas** — Tech. A smooth-talking gambler in his thirties, slicked-back hair, a knowing half-smile,
  a playing card tucked in the helmet strap. Sand-gold helmet with an orange visor glass.

---

## 2. Class emblems (character select) — set of 4

**Where:** the small round badge on each portrait's lower right (~40 px) and the class name on the
roster. **Aspect:** 1:1, 1024×1024. **KEY = MAGENTA.** **Files:** `class_<name>.png`.

```
A round military insignia medallion for a sci-fi game, a painted 3D game-art render seen straight
on. A thick bevelled gunmetal rim with small rivets, a dark navy enamel centre, and in the centre a
bold, simple embossed white symbol: [SYMBOL]. The symbol must read clearly when the medallion is
shrunk to 40 pixels: thick shapes, no fine detail. A thin cyan-blue light along the rim's inner edge.
Background: perfectly flat uniform pure magenta #FF00FF, no shadow. No text, no letters, no numbers.
```

- **officer** — three stacked chevrons above a small star.
- **sw** (Special Weapons) — a heavy gun barrel cluster seen end-on, three barrels in a triangle.
- **medic** — a bold medical cross.
- **tech** — a circuit trace splitting into three branches ending in dots.

---

## 3. Weapon renders (weapon select) — set of 15

**Where:** the briefing's loadout slots and the equipment picker (slot ~180×110 px), and the large
weapon shown when one is selected. **Aspect:** 16:9, generate at 1344×768. **KEY = MAGENTA.**
**Files:** `gun_<name>.png`.

```
A single sci-fi military firearm for a game's weapon select screen, painted 3D game-art render,
shown in exact side profile facing right, the whole weapon in frame, centred, filling about 85% of
the width. [WEAPON DESCRIPTION]
Worn gunmetal and dark painted polymer with scuffed edges, small stencil markings (no readable text),
a thin cyan-blue status light. Cold key light from the top left, cyan rim light along the top edge.
Background: perfectly flat uniform pure magenta #FF00FF, no shadow, no floor, no reflection.
No magenta or pink on the weapon. No text, no hands, no person.
```

- **rifle** — 22A3-1 Assault Rifle: a chunky bullpup-style assault rifle with a box magazine, a
  folding stock and an under-barrel grenade tube.
- **prifle** — 22A7-Z Prototype Rifle: a sleeker, experimental version of the assault rifle with a
  glowing cyan targeting module on top and exposed cooling fins.
- **autogun** — S23A Autogun: a heavy squad support gun carried at the hip, a large drum feed, a
  support arm and a stabilising gimbal mount.
- **vindicator** — M42 Vindicator: a massive automatic combat shotgun with a long rectangular barrel
  shroud and a rotary drum magazine.
- **pistols** — M73 Twin Pistols: two identical heavy semi-automatic pistols, one above the other,
  both facing right.
- **shotgun** — Model 35 Pump-action Shotgun: a rugged pump-action shotgun with a tube magazine and
  a heat-shielded barrel.
- **tesla** — Tesla Cannon: a two-handed energy weapon with copper coils along the barrel, a glowing
  blue capacitor and a forked emitter tip.
- **railrifle** — Precision Rail Rifle: a long sniper rail gun with twin parallel rails, a long
  scope and a heavy battery pack.
- **marksman** — AVK-36 Marksman Rifle: a semi-automatic marksman rifle with a mid-length scope, a
  bipod folded under the barrel and a slim magazine.
- **minigun** — IAF Minigun: a six-barrel rotary minigun with a carry handle, a large ammunition box
  and a feed belt.
- **flamer** — M868 Flamer Unit: a flamethrower with a fuel canister under the body, a pilot-light
  nozzle and a heat-blackened muzzle.
- **pdw** — K80 Personal Defense Weapon: a compact submachine gun with a top-mounted magazine and a
  stubby barrel.
- **grenadelauncher** — Grenade Launcher: a six-round revolving-cylinder grenade launcher with a wide
  barrel.
- **chainsaw** — Chainsaw: a heavy two-handed military chainsaw with a long serrated bar and a
  reinforced engine housing.
- **medgun** — IAF Medical Gun: a white-and-red medical spray gun with a glass canister of glowing
  green-blue fluid.

---

## 4. Equipment renders (weapon select, offhand slot) — set of 23

**Where:** the briefing's third loadout slot and the equipment picker (~110×110 px).
**Aspect:** 1:1, 1024×1024. **KEY = MAGENTA.** **Files:** `item_<name>.png`.

```
A single piece of sci-fi military field equipment for a game's loadout screen, painted 3D game-art
render, seen at a three-quarter angle from slightly above, centred, filling about 75% of the frame.
[ITEM DESCRIPTION]
Worn gunmetal, olive and dark polymer, scuffed edges, small stencil markings (no readable text), a
small cyan-blue status light. Cold key light from the top left, cyan rim light.
Background: perfectly flat uniform pure magenta #FF00FF, no shadow, no floor.
No magenta or pink on the object. No text, no hands, no person.
```

- **sentry** — IAF Advanced Sentry Gun: a tripod-mounted automatic turret with a twin-barrel gun.
- **sentryfreeze** — Freeze Sentry: the same tripod turret with a frosted icy-blue emitter.
- **sentryfire** — Incendiary Sentry: the same tripod turret with a flame nozzle and an orange fuel tank.
- **sentrycannon** — Sentry Cannon: the same tripod with a single long high-velocity cannon barrel.
- **teslacoil** — Tesla Sentry Coil: a squat tripod with a copper coil tower crackling with blue arcs.
- **healbeacon** — IAF Heal Beacon: a small cylindrical beacon on a base with a glowing green-white
  medical light on top.
- **ammosatchel** — IAF Ammo Satchel: a rugged canvas-and-metal ammunition bag with buckles and
  magazines poking out.
- **medkit** — IAF Personal Healing Kit: a compact white hard-case medkit with a red cross.
- **welder** — Hand Welder: a pistol-grip industrial welding torch with a bright tip and a gas cell.
- **flares** — SM75 Combat Flares: three red-orange cylindrical combat flares bundled with a band.
- **grenades** — Hand Grenades: two military frag grenades with pins.
- **freezegrenades** — Freeze Grenades: two pale-blue cryo grenades with frost on them.
- **lasermines** — ML30 Laser Trip Mine: a flat wedge-shaped mine with a red laser emitter.
- **incmines** — M478 Proximity Incendiary Mines: a round disc mine with an orange warning ring.
- **smartbomb** — MTD6 Smart Bomb: a spherical bomb with blue sensor eyes around its equator.
- **hornet** — Hornet Barrage: a shoulder-mounted mini-rocket pod with six small tubes.
- **adrenaline** — Adrenaline: a combat auto-injector syringe with a glowing amber vial.
- **damageamp** — X33 Damage Amplifier: a compact wrist-mounted device with a glowing red-orange core.
- **nightvision** — MNV34 Nightvision Goggles: tactical goggles with twin lenses glowing faint green.
- **flashlight** — Flashlight Attachment: a rugged weapon-mounted tactical flashlight with a rail clamp.
- **powerfist** — IAF Power Fist Attachment: a heavy armoured gauntlet with pistons on the knuckles.
- **heavyarmor** — l3a Tactical Heavy Armor: a thick armoured chest plate with layered plates.
- **electricarmor** — v45 Electric Charged Armor: an armoured chest plate with blue electric arcs
  across it.

---

## 5. Mission location art (mission select and briefing) — set of 6

**Where:** the picture panel at the top left of MISSION PREP (480×480 px), which changes with the
mission arrows; the level's minimap moves to the panel's corner. **Aspect:** 1:1, 1024×1024.
**Background:** a full scene (this one is a picture, not a cut-out), with its
edges fading softly into flat navy-black `#0C141E` so it blends into the panel.
**Files:** `mission_<id>.png`.

```
Concept art for a mission briefing in a top-down sci-fi squad shooter: [LOCATION]
Seen from high above at a steep three-quarter angle, like the game's own camera, so the floor plan
reads clearly. Moody, dark, cinematic: pools of cold blue and white light, emergency red and amber
lamps, haze, deep shadows. Painted 3D game-art render. No people, no marines, no aliens visible,
only signs of them. The outer 10% of the image fades softly into flat dark navy #0C141E on every side.
No text, no labels, no UI, no logos.
```

- **landingbay** — Vereon XII, SynTek Landing Bay 7: a cavernous starport hangar with a parked
  dropship, escape pods in recessed bays, cargo containers, landing lights and yellow-black hazard
  lines, a security checkpoint gate.
- **cargo** — Vereon XII, Cargo Elevator: a huge open freight lift platform in a deep square shaft,
  guard rails, crates strapped down, warning beacons, the shaft walls dropping into darkness.
- **deima** — Deima, colony surface, night side: a long metal bridge over a dark chasm, an industrial
  pipeline running alongside it oozing alien biomass, a stormy night sky, distant colony lights.
- **rydberg** — Deima, Rydberg Power Plant: a reactor hall with a large dormant fusion core in the
  centre, catwalks, coolant pipes, consoles, some panels sparking.
- **residential** — Deima, SynTek Residential Block: colony apartment corridors and a mess hall,
  overturned furniture, alien eggs and fleshy biomass growing over the walls.
- **sewer** — Deima, Sewer Junction B5: a flooded sewer junction with grated walkways, big pipes,
  murky water, a collapsed tunnel mouth glowing with alien growth.

---

## 6. Star chart (mission select backdrop)

**Where:** behind the whole MISSION PREP screen, dimmed. **Aspect:** 16:9, 1920×1080 if
offered. **KEY = BLACK** (additive). **File:** `starchart.png`.

```
A holographic tactical star chart for a sci-fi game's mission select screen, drawn entirely in
glowing cyan-blue light lines on a perfectly flat pure black #000000 background. On the left a
large wireframe planet with latitude rings (a rocky world, Vereon XII), with a small orbiting
station; on the right a smaller wireframe moon-like planet (Deima) with a thin orbit ellipse and a
pulsing marker dot on its surface. A dashed flight path arcs from the left planet to the right one.
Faint range rings, tick marks and a sparse grid around them. Thin, crisp, glowing lines, a soft
bloom, everything else pure black. No text, no numbers, no labels, no filled surfaces.
```

---

## 7. Panel and button frame kit (all menus)

**Where:** every menu panel and button (MISSION PREP, SELECT MARINE, the equipment picker, debrief).
The game will cut it into a nine-slice (four corners, four edges, centre) and stretch it to any
size. **Aspect:** 1:1, 1024×1024. **KEY = MAGENTA.** **Files:** `frame_panel.png`, `frame_button.png`,
`frame_button_hover.png`.

```
A single empty rectangular UI panel frame for a gritty military sci-fi game, seen straight on, flat
and orthographic, filling the image with a 6% margin. A bevelled gunmetal border about 6% of the
image's width thick, with small chamfered (cut) corners, tiny rivets and a short cyan-blue light
strip at each corner. The four sides must be plain and uniform along their length (so they can be
stretched), all decoration only at the corners. The inside of the frame is perfectly flat uniform
dark navy #0C141E with a very faint fine grid. Outside the frame: perfectly flat uniform pure magenta
#FF00FF. No text, no icons, no shadow outside the frame.
```

- **frame_button** — same prompt, but "a wide, short button frame (4:1 proportions centred in the
  square), thinner border, the inside a slightly lighter steel-navy `#1A2A3C`".
- **frame_button_hover** — the button again, "the border's light strips and inner edge glowing bright
  cyan-blue, the inside a lighter blue `#24445E`".

---

## 8. HUD portrait bezel (in-game, bottom left)

**Where:** around the player's portrait and health ring at the bottom left (~170 px). The game draws
the portrait and the 270° health ring inside it; this is the metal housing round them.
**Aspect:** 1:1, 1024×1024. **KEY = MAGENTA.** **File:** `hud_bezel.png`.

```
A circular HUD housing for a sci-fi game, seen straight on, flat and orthographic. A thick
gunmetal ring with bevelled edges, small vents and rivets, and a thin cyan-blue light line along
its inner edge. The ring is a full circle except at the lower right, where it squares off into a
short flat horizontal bracket pointing right (where an ammo bar attaches). The centre of the ring,
about 65% of the diameter, is an empty hole of perfectly flat uniform pure magenta #FF00FF. Outside
the ring is also perfectly flat uniform pure magenta #FF00FF. No text, no numbers, no portrait,
no shadow.
```

---

## 9. HUD plates (in-game, bottom bar)

**Where:** the backplates behind the player's ammo and equipment strip (bottom left, ~330×70 px) and
behind each squadmate's card (bottom centre, ~170×60 px). **Aspect:** 21:9. **KEY = MAGENTA.**
**Files:** `hud_plate_player.png`, `hud_plate_squad.png`.

```
A horizontal HUD backplate for a gritty sci-fi game, seen straight on, flat and orthographic,
centred, filling 90% of the width. A low, wide, dark translucent-looking navy panel #0C141E at 85%
darkness, with a bevelled gunmetal edge along the top and bottom, angled (chamfered) ends, a thin
cyan-blue light line along the top edge, and faint stencilled tick marks along the bottom edge.
[VARIANT] The panel's face is plain and empty: no icons, no text, no numbers, no bars.
Outside the panel: perfectly flat uniform pure magenta #FF00FF, no shadow.
```

- **hud_plate_player** — "The panel is long, about 5 times as wide as it is tall, with the left end
  cut at a 45° angle and three faint recessed slots on the right half for equipment icons."
- **hud_plate_squad** — "The panel is about 3 times as wide as it is tall, with a round recessed
  socket on the left end for a small portrait."

---

## 10. Objective and alert icons (in-game) — one sheet of 12

**Where:** objective list ticks, world markers, the use prompt and warning flashes (~32–64 px).
**Aspect:** 4:3, one sheet in a 4×3 grid. **KEY = BLACK** (they glow and are tinted by the game).
**File:** `icons_objectives.png` (cut into cells afterwards).

```
A sheet of 12 game HUD icons for a sci-fi squad shooter, arranged in an even 4 columns by 3 rows grid
with generous equal spacing, each icon centred in its cell and the same size. Each icon is a bold,
simple glowing white line-art symbol with a soft white glow, thick strokes that stay readable at
32 pixels, on a perfectly flat pure black #000000 background. No boxes, no frames, no grid lines, no
text, no numbers. The icons, left to right, top to bottom:
1 objective complete: a bold check mark;
2 objective target: a downward chevron with a small diamond above it;
3 door: a sliding blast door with two panels;
4 weld: a welding torch with a spark;
5 hack: a terminal screen with a cursor bracket;
6 power: a lightning bolt inside a circle;
7 alien eggs: a cluster of three rounded egg shapes;
8 biomass: an organic blob with tendrils;
9 extraction: a dropship seen from above;
10 warning: a triangle with a heavy exclamation bar and dot;
11 low ammo: a single bullet with a slash beside it;
12 infested: a marine helmet with a small parasite shape on it.
```

---

## After generating

Save the PNGs in `sc2poc/assets/ui-gen/` under the names above, then check them:

```bash
py tools/genart.py
```

It keys out the backgrounds and writes two pictures to look at: `dist/genart-sheet.png` (every cut-out over
the game's navy and over a checker, with any warnings at the top) and `dist/genart-hud.png` (the HUD's
portrait corner with the bezel, plate, squad card and ticked box in place). A warning about a grey
checkerboard means Nano Banana painted fake transparency: generate that one again asking for flat magenta.

`py build.py` then packs them into the map. Any image that is missing keeps the game's drawn art.
Where each image goes:

| Image | Where it shows |
| --- | --- |
| `portrait_<name>` | briefing rows, SELECT MARINE, the HUD portrait |
| `class_<name>` | the class badge on every portrait, HUD and briefing |
| `gun_<name>`, `item_<name>` | the briefing's loadout slots and the equipment picker (the HUD keeps its line icons) |
| `mission_<id>` | MISSION PREP's picture panel |
| `starchart` | behind MISSION PREP |
| `frame_panel`, `frame_button`, `frame_button_hover` | every menu panel and button (a dimmed copy of `frame_button` for disabled buttons) |
| `hud_bezel` | round the health ring |
| `hud_plate_player`, `hud_plate_squad` | behind the ammo strip, behind each squadmate's card |
| `icons_objectives` | the ticked objective box, the minimap objective blip, the use panel (door, weld, hack, power, eggs, biomass, lift), low/no ammo, infested |
