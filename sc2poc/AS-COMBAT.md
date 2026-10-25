# Alien Swarm combat reference, recorded 2026-10-24

The user played Landing Bay (`asi-jac1-landingbay_01`) as Sarge with the 22A3-1 Assault Rifle, with Wildcat, Faith and Crash as the AI squad: about 3.7 minutes, four fights. These notes record how the shooting looks and feels, for tuning the port. Screen observations come from the recording; numbers marked *SDK* come from `../AlienSwarm/src` (full detail in `dist/asref/combat-sdk-notes.md`).

**Captures** (`dist/asref/`, reference only):
- `combat-rifle-fight.webp`: a 6 s close fight at 20 fps (centre crop).
- `combat-swarm-fight.webp`: the 10 s squad fight in the blue yard.
- Stills `combat-01` to `combat-09`.
- Demo `combat1.dem` in the game's `swarm/` folder (`playdemo combat1`, `demo_timescale 0.25` for slow motion).

## What the player does

- **Bursts, not a held trigger.** There were 38 bursts in 3.7 minutes, a median of 0.7 s each (0.15 to 2.7 s), about 34 s of fire in all. Between bursts the player re-aims and steps back.
- **Shooting on the move.** Almost every burst is fired while backing off or strafing (WASD held through it), with the gun aimed at the drones independently of the movement.
- **Melee** with the right button, in quick taps (6 in 3 s), when drones are on top of the marine.
- **One manual reload** (R at 82 s). The others came when the clip ran dry. "RELOADING" in red floats over the marine, a bar sits by the portrait, and the reload took about 2.5 s.

## Rate of fire (measured)

Read off the HUD's ammo counter during held bursts: 84 → 72 in 0.98 s, 59 → 38 in 1.75 s, 23 → 5 in 1.55 s. That is **about 12 rounds a second**, so a 98-round clip lasts about 8 s of fire.

## The laser sight

- A thin, saturated red line from the muzzle. It **does not stop at the cursor**: it runs on through the reticle to the wall or alien behind it (`combat-05`, `combat-09`). So it shows where the bullets will go, not where the mouse is.
- It is faint against lit floors and vivid in the dark and in smoke. Where it crosses haze it breaks into bright dashes as the motes catch it (`combat-06`).
- When the rifle is firing, the tracers and flash swamp it. It is most visible between bursts.

## The reticle

- AS draws its own cursor: a small grey ring with gaps, tick marks and a centre dot. The ring is the clip gauge (see the SDK notes below).
- **A red cross-hatched mark appears on a drone under the reticle** (`combat-03`). It is the laser's impact mark where the autoaimed beam lands on the body, not the cursor changing. It tells the player the shot will connect before they fire.

## Rifle fire

- **Muzzle flash:** a white-hot star with an orange fringe, about half a cell across, on most frames while firing. It **lights the floor round the marine** warm yellow (a dynamic light), so a firing marine glows in a dark room.
- **Tracers:** long, thin yellow-orange streaks, 1.5 to 2 cells long, crossing the screen in 2 or 3 frames. Visible spread: some streaks fan a few degrees off the line, and some skip off at angles past the target. With four marines firing, the screen is criss-crossed by tracers.
- **Friendly fire:** "Don't Hurt Squad Mates" warnings come up whenever the line crosses a squadmate.

## Hitting and killing drones

- **A hit** shows a small green spurt at the impact point. No damage numbers. The drone keeps coming: it doesn't stop for most hits.
- **The kill is the payoff:** a big lime-green acid flare about 1.5 to 2 cells across, made of wispy streaks, bursts from the body and hangs for 0.5 to 1 s while it thins to a green mist. The corpse stays (rooms fill with bodies) along with dark green-brown splats.
- In a group fight, kills chain: a burst sweeping a clump pops two or three flares in a second.

## Getting hit

- Drones close fast and wrap round the marine. Each claw hit throws a **bright red spray of streaks** off the marine (`combat-04`).
- One drone lunging in reads as a dark mass on top of the marine. The red spray is the main signal.

## The camera while fighting

- The lean toward the cursor is constant and big: aiming at drones to one side slides the whole view that way, and the marine rides well off-centre during fights.

## What the SDK says (checked by hand)

- **Laser sight** (`client/swarm/c_asw_weapon.cpp` `SimulateLaserPointer`, 704–810):
  - It is traced from the muzzle along the **autoaimed** shot direction (`GetAutoaimVectorForMarine`) for `GetLaserPointerRange()` and ends on whatever it hits first.
  - Ranges: 600 units (7.5 cells) for most guns, 360 for the Vindicator (`asw_weapon_assault_shotgun_shared.h:46`), 280 for the flamer, 240 for the extinguisher.
  - The cursor plays no part in where it ends. The particle's end point is oriented to the surface it hits, which draws the red mark on a drone.
  - Opacity is 0.65, cut to **0.065 while firing** (`alpha *= 0.06`). It is **hidden** while reloading, meleeing, switching weapons, using something, or in slow motion.
  - Over a squadmate a second friendly-fire channel lights up (`alphaFF` 0.65).
  - **Other marines' lasers are 100 units long (1.25 cells) at opacity 0.3**: short stubs. Only your own laser reaches across the room.
- **The reticle's ring is the clip** (`client/swarm/vgui/asw_hud_crosshair.cpp` 408–470):
  - A circular progress bar round the cursor shows the clip draining.
  - During a reload it fills and flashes between yellow (215,205,80) and red (175,80,80) five times a second, with the fast-reload window drawn on the ring.
- **Rate of fire**: `swarm/scripts/asw_weapon_*.txt` `fire_rate`, and `CASW_Weapon::PrimaryAttack` keeps time by adding the rate to the next shot time, so the average is exact. (The script's 14.3 a second is more than the 12 a second measured above; the source and the game disagree here.)

  | Weapon | AS fire_rate | Port's rate |
  |---|---|---|
  | Rifle / Prototype | 0.07 | 0.0625 |
  | Autogun | 0.1 | 0.125 |
  | PDW | 0.035 | 0.03125 |
  | Flamer | 0.1 | 0.125 |
  | Marksman | 1.2 | 1.1875 |
  | Minigun | 0.04 | 0.04 |
  | Pistols | 0.5 | 0.5 |
  | Shotgun | 1.0 | 1.0 |

- **Firing and reloading halve the marine's speed** (`asw_weapon_shared.cpp:1231` `GetMovementScale`: 0.5 while `IsFiring() || IsReloading()`; autogun 0.5/0.8, minigun 0.4/0.95). The port already does this.

- **Hits slow drones instead of shoving them** (SDK agent, `server/swarm/asw_alien.cpp:944-949`): any hit sets the alien to `asw_alien_hurt_speed` 0.5 for 0.5 s, refreshed by every hit. A held trigger keeps a charging drone at about half speed. Each hit also has a chance to stagger (20% for the rifle, scaled by the health left) for 0.4-0.8 s. Bullets do no knockback.
- **Turning is limited** (`asw_marine_linear_turn_rate` 600 deg/s, half that while firing, `GetTurnRateModifier`), and bullets leave along the marine's actual facing. The gun sweeps onto a target instead of snapping.
- **Sideways aim assist is only for some guns** (`client/swarm/asw_input.cpp:634-636`): the plain rifle's assist only fixes the shot's height (flat at a drone's body instead of down at the floor point). Sideways snapping happens only for weapons with an autoaim radius scale (prototype rifle, autogun) or near a flare. That is also why the laser lands on a drone's body: it runs flat at gun height.
- Full SDK reference: `dist/asref/combat-sdk-notes.md` (drone health per difficulty, melee timings, every weapon's spread and slowdown).

## Changes made to the port (2026-10-24)

- **The laser shows where the bullets go** (`src/Marine.galaxy` `AS_Attachments`, `AS_LaserRange`):
  - It runs flat at gun height to the first bulkhead or alien, out to 7.5 cells (4.5 for the shotguns, 3.5 for the flamer), instead of down to the deck under the cursor.
  - The dot shows only where it hits something.
- **The laser follows the shot's aim assist** (`src/Weapons.galaxy` `AS_AssistAim`, `AS_ShotAimPulse`):
  - The assisted line is worked out every step, and the beam is drawn along it.
  - When the assist will take a drone, the beam is on that drone. The marine still faces the cursor.
- **The laser gets out of the way:** 6% opacity within 0.15 s of a shot. It is off while reloading, for 0.5 s after a melee swing, for 0.3 s after changing guns, and while using a panel.
- **AI squadmates' lasers** are 1.25-cell stubs at 46% opacity (AS's 0.3 against 0.65). The autopilot's player 1 keeps a full one.
- **Fire rates are AS's script values** (rifle and prototype 0.07, autogun 0.1, PDW 0.035, flamer 0.1, marksman 1.2). With `rate` equal to `rateAS`, the damage-per-second correction no longer scales anything.

## Still proposed

In order of how much each should change the feel:

1. **Hits slow drones; they don't shove them.**
   - Every bullet hit halves the alien's speed for 0.5 s, refreshed by each hit, so holding the trigger on a charging drone visibly brakes it.
   - Drop the per-bullet `push` from rifle-class rounds and keep `AS_Flinch` as the stagger.
   - The port has no hurt-slow today.
2. **The marine turns at 600 deg/s, 300 deg/s while firing,** instead of facing the cursor instantly (`AS_Face`, `AS_AimUpdate`). Rounds and the laser follow the turned facing, so a burst sweeps across a pack.
3. **Sideways aim assist only where AS has it:** the prototype rifle, the autogun and near flares. Use cone 0 for the plain rifle and the other guns. For the plain rifle, AS's assist only fixes the shot's height.
4. **A reticle with the clip on it.** A ring at the cursor's point on the deck that drains as the clip empties. During a reload it fills, flashing yellow and red, with the fast-reload window marked. It needs a new ring mesh (`tools/fx.py`).

Already matching AS, so no change: the halved speed while firing, the drone acid flare, the red spray on a clawed marine, the flinch, the camera lean, tracers on every round, casings and the friendly-fire share.
