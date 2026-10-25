# Halcyon Drift — UI art prompts, batch 2

The next ten images for Nano Banana, picked for how much of the game each one fixes:

| # | File | Why it's next |
| --- | --- | --- |
| 1 | `frame_button.png` | menu panels already use the painted frame; buttons still use the old flat art |
| 2 | `frame_button_hover.png` | the highlighted state of the same buttons |
| 3 | `hud_plate_squad.png` | the three squadmate cards along the HUD's bottom (the player plate is done) |
| 4 | `class_sw.png` | the Special Weapons badge, on every Wildcat/Wolfe portrait and HUD card |
| 5 | `class_medic.png` | the Medic badge (Faith, Bastille) |
| 6 | `class_tech.png` | the Tech badge (Crash, Vegas) |
| 7 | `portrait_crash.png` | the marine you play by default |
| 8 | `portrait_wildcat.png` | in the default squad |
| 9 | `portrait_faith.png` | in the default squad (with Sarge, the default four are then all painted) |
| 10 | `mission_cargo.png` | the second mission's picture on Mission Prep |

Every prompt below is complete: paste it as it is. Save each result into `sc2poc/assets/ui-gen/`
under its file name (PNG or JPG both work).

---

## Read this first (for Gemini)

You are making UI art for an original top-down sci-fi squad shooter called **Halcyon Drift**: four
space marines fighting an insectoid alien swarm through derelict colony facilities. These images
continue a set that already exists, and must match it.

- Gritty military sci-fi, 2000s–2010s PC game UI. Worn painted metal, scuffs, hazard paint. A painted
  3D game-art render: not cartoon, not anime, not photoreal live action.
- Palette: deep navy-black `#0C141E`, gunmetal and steel-blue, a cool cyan-blue accent `#5AB4F0` for
  lights and edges, white for symbols.
- Lighting: a cold key light from the top left, a cyan rim light, deep shadows.
- **No text, letters, numbers, logos or watermarks.**
- **Background:** a perfectly flat, uniform pure magenta `#FF00FF`, with no gradient, floor, shadow or
  vignette, unless a prompt says otherwise. Never draw a grey checkerboard "transparent" background.
  The subject itself must contain no magenta or pink.

**Use the existing images as references.** Attach the file named under each prompt (they are in
`sc2poc/assets/ui-gen/`) together with the prompt, so the new image matches the one already in the game.

---

## 1. `frame_button.png` — menu button

**Attach:** `frame_panel.jpg` (the panel frame these buttons sit in). **Aspect:** 1:1.

```
Using the attached panel frame as the style reference (same gunmetal, bevels, rivets and cyan light
strips), make a single empty rectangular menu button frame for the same game UI, seen straight on,
flat and orthographic. The button is wide and short, 4 times as wide as it is tall, centred in the
square image and filling 85% of its width. A bevelled gunmetal border about 8% of the button's height
thick, with small chamfered (cut) corners, and a short cyan-blue light strip at each end. The long top
and bottom sides must be plain and uniform along their length (they get stretched); all decoration
only at the corners and ends. The inside of the button is flat dark steel-navy #1A2A3C. Everything
outside the button: perfectly flat uniform pure magenta #FF00FF, no shadow. No text, no icons.
```

## 2. `frame_button_hover.png` — highlighted button

**Attach:** the `frame_button` you just made. **Aspect:** 1:1.

```
The exact same button as the attached image, same size, shape and position in the frame, but
highlighted: the border's light strips and the button's inner edge glow bright cyan-blue #5AB4F0 with
a soft bloom, and the inside is a lighter blue #24445E. Everything outside the button: perfectly flat
uniform pure magenta #FF00FF, no shadow. No text, no icons.
```

## 3. `hud_plate_squad.png` — squadmate card

**Attach:** `hud_plate_player.jpg` (the player's plate, already in the game). **Aspect:** 21:9.

```
Using the attached HUD plate as the style reference (same dark navy face, gunmetal edge, cyan line
along the top, stencilled tick marks), make a smaller horizontal HUD backplate for one squadmate,
seen straight on, flat and orthographic, centred, filling 70% of the image's width. The plate is about
3 times as wide as it is tall, with angled (chamfered) ends, and a round recessed socket at its left
end for a small circular badge. The rest of its face is plain and empty: no slots, no icons, no text,
no numbers, no bars. Outside the plate: perfectly flat uniform pure magenta #FF00FF, no shadow.
```

## 4–6. Class badges

**Attach:** `class_officer.jpg` (the Officer badge, already in the game). **Aspect:** 1:1. One image
each, in the same chat, attaching the officer badge every time.

**4. `class_sw.png` — Special Weapons**

```
The exact same round insignia medallion as the attached image (same thick bevelled gunmetal rim,
rivets, glowing cyan inner ring, dark navy enamel centre, same size and position, same lighting),
but the embossed white symbol in the centre is three heavy gun barrels seen end-on, arranged in a
triangle, thick simple shapes that read at 40 pixels. Background: perfectly flat uniform pure
magenta #FF00FF, no shadow. No text, no letters, no numbers.
```

**5. `class_medic.png` — Medic**

```
The exact same round insignia medallion as the attached image (same thick bevelled gunmetal rim,
rivets, glowing cyan inner ring, dark navy enamel centre, same size and position, same lighting),
but the embossed white symbol in the centre is a bold, thick medical cross with slightly rounded
ends. Background: perfectly flat uniform pure magenta #FF00FF, no shadow. No text, no letters, no
numbers.
```

**6. `class_tech.png` — Tech**

```
The exact same round insignia medallion as the attached image (same thick bevelled gunmetal rim,
rivets, glowing cyan inner ring, dark navy enamel centre, same size and position, same lighting),
but the embossed white symbol in the centre is a thick circuit trace rising from the bottom and
splitting into three branches, each ending in a round node, simple shapes that read at 40 pixels.
Background: perfectly flat uniform pure magenta #FF00FF, no shadow. No text, no letters, no numbers.
```

## 7–9. Marine portraits

**Attach:** `portrait_sarge.jpg` (Sarge, already in the game). **Aspect:** 1:1. One image each, in the
same chat, attaching Sarge every time. The game zooms in on the helmet and face, so keep the head the
same size and place in the frame as Sarge's.

**7. `portrait_crash.png` — Crash, Tech**

```
A portrait of a different space marine in exactly the same style, framing, pose, lighting, armour
design and painted 3D game-art render as the attached portrait: head and shoulders from mid-chest up,
facing the camera turned slightly to their right, the helmet and face in the same size and place as
in the attached image, goggle-visor pushed up on the helmet so the face is fully visible, cyan rim
light on the right edge. This marine is Crash, the squad's tech: a cocky nineteen-year-old hacker,
young clean-shaven face, a smirk, slightly nervous eyes, a headset microphone at the jaw. Gold-yellow
helmet and armour with a gold visor glass. A small data-pad and cabling clipped at the collar.
Background: perfectly flat uniform pure magenta #FF00FF, no gradient, no shadow. No magenta or pink on
the marine. No text, no logo, no frame, no border.
```

**8. `portrait_wildcat.png` — Wildcat, Special Weapons**

```
A portrait of a different space marine in exactly the same style, framing, pose, lighting, armour
design and painted 3D game-art render as the attached portrait: head and shoulders from mid-chest up,
facing the camera turned slightly to their right, the helmet and face in the same size and place as
in the attached image, goggle-visor pushed up on the helmet so the face is fully visible, cyan rim
light on the right edge. This marine is Wildcat, a special weapons marine: a fierce young woman in her
mid-twenties, sharp features, a defiant glare, dark hair tied back. Rust-brown helmet and armour with a
blue stripe down the centre of the helmet and a red-orange visor glass. A heavy ammunition-feed harness
over one shoulder. Background: perfectly flat uniform pure magenta #FF00FF, no gradient, no shadow. No
magenta or pink on the marine. No text, no logo, no frame, no border.
```

**9. `portrait_faith.png` — Faith, Medic**

```
A portrait of a different space marine in exactly the same style, framing, pose, lighting, armour
design and painted 3D game-art render as the attached portrait: head and shoulders from mid-chest up,
facing the camera turned slightly to their right, the helmet and face in the same size and place as
in the attached image, goggle-visor pushed up on the helmet so the face is fully visible, cyan rim
light on the right edge. This marine is Faith, the field medic: a warm, steady woman in her thirties,
calm eyes, a faint reassuring smile. White helmet and armour with a red stripe down the centre of the
helmet and an ice-blue visor glass. A white medical cross patch on the shoulder pad. Background:
perfectly flat uniform pure magenta #FF00FF, no gradient, no shadow. No magenta or pink on the marine.
No text, no logo, no frame, no border.
```

## 10. `mission_cargo.png` — Cargo Elevator

**Attach:** `mission_landingbay.jpg` (the first mission's picture, already in the game). **Aspect:** 1:1.
This one is a full picture, not a cut-out: no magenta.

```
Concept art for the next mission briefing in the same top-down sci-fi squad shooter, in exactly the
same style, colours, camera angle and painted 3D game-art render as the attached image: Vereon XII,
the cargo elevator. A huge open freight lift platform in a deep square shaft, seen from high above
at a steep three-quarter angle so the platform reads clearly: guard rails round its edge, cargo crates
strapped down on it, yellow-black hazard stripes, rotating amber warning beacons, the shaft's ribbed
metal walls dropping away into darkness below, a few cold blue work lights. Moody and dark, with haze.
No people, no marines, no aliens. The outer 10% of the image fades softly into flat dark navy #0C141E on
every side, as in the attached image. No text, no labels, no UI, no logos.
```

---

When they're saved, tell Claude: it runs `py tools/genart.py`, checks the cut-outs, and builds them in.
