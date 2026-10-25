# Alien Swarm combat feel: notes from the SDK source

Sources:
- `SRC` = `C:\Users\drink\OneDrive\Desktop\alien\AlienSwarm\src`
- `GAME` = `C:\Program Files (x86)\Steam\steamapps\common\Alien Swarm\swarm`
- `VPK` = files read out of `GAME\pak01_dir.vpk`: `resource/profiles.res`, the particle files (`particles/*.pcf`, decoded from binary DMX v5), and `models/aliens/drone/drone.mdl` (v49 sequence and animation headers).

Units are Source units (1 u ≈ 1 inch); times are in seconds. Anything I worked out rather than read straight from code or data is marked **(inferred)**. Unless noted, a cvar value is the default in code.

Caveat: the SDK is the 2010 "Swarm SDK" source, while the installed game runs Valve's compiled DLLs. Game data (scripts, cfg, VPK) comes from the install. Code and data agree everywhere I checked them against each other, but the shipped DLLs could differ in places.

---

## 0. Global rules that shape every gun

| Rule | Value | Where |
|---|---|---|
| Hit registration | **Hitscan** traces (`MASK_SHOT`, hits hitboxes) for every bullet gun. Lag-compensated for player marines. Flamer, grenades and rifle grenades are projectiles. | `game/shared/swarm/asw_marine_shared.cpp:689-976` (FireRegularBullets), `asw_weapon_shared.cpp:613-618` |
| Max bullet range | `asw_weapon_max_shooting_distance` **1500**. The PDW uses this too: `asw_pdw_max_shooting_distance 400` is defined but not used in PDW fire. | `asw_weapon_shared.cpp:42`, `asw_weapon_pdw_shared.cpp:52,211` |
| Damage falloff | **None.** Damage is constant out to 1500. | FireRegularBullets (no distance term) |
| Damage source | `base_damage` in the weapon .txt plus a skill bonus. The `sk_plr_dmg_asw_*` values in `cfg/skill.cfg` only apply when `info.m_flDamage == 0`, which is never the case for these guns, so treat them as legacy. | `asw_weapon_shared.cpp:1236-1248`, `asw_marine_shared.cpp:880-883` |
| Fire timing | Hold to fire. `m_flNextPrimaryAttack += fire_rate` in a while-loop, so several bullets can go out in one frame and the fire rate does not depend on framerate. | `asw_weapon_shared.cpp:637-645` |
| Tracer frequency | 1 tracer per bullet (`m_iTracerFreq = 1`), on every hitscan gun | `asw_weapon_shared.cpp:674` |
| Spread model | Static cone. It **does not grow** with sustained fire or movement, and nothing in the code reads `m_fFireDuration` for spread. `CShotManipulator::ApplySpread`: x,y = 0.5·U(-1,1) + 0.5·U(-1,1) (a triangular distribution, rejected outside the unit circle) × cone, added to forward along the right/up axes. | `game/shared/shot_manipulator.h:60-93`, `ai_shot_bias_min/max` -1/1 → flatness 0.5 (`baseentity_shared.cpp:62-63`) |
| Cone constants | 3° = 0.02618, 7° = 0.06105, 15° = 0.13053, 20° = 0.17365 (sin of the half-angle) | `game/shared/basecombatweapon_shared.h:109-118` |
| Move slow while firing | Base weapon: `GetMovementScale` = **0.5** while firing or reloading, 1.0 otherwise. Several guns override this (see the table). | `asw_weapon_shared.cpp:1018-1021,1231-1234` |
| Turn slow while firing | `GetTurnRateModifier` = **0.5** while firing | `asw_weapon_shared.cpp:1203-1209` |
| Weapon switch | **0.5 s** before the next attack | `asw_weapon_shared.cpp:1115-1130` |
| Low-ammo click | `ASW_Weapon.LowAmmoClick` while clip ≤ 6 (default `AmmoClickPoint`) | `asw_weapon_shared.cpp:599-602,1438-1441` |
| Reload discards clip | `FinishReload` sets `m_iClip1 = 0` before refilling. **The rounds left in the clip are lost.** | `asw_weapon_shared.cpp:1065-1066` |
| Auto-reload | Firing on an empty clip calls `Reload()`. With no buttons held and clip 0, it auto-reloads (respecting `ShouldAutoReload`). | `asw_weapon_shared.cpp:584-588,513-550` |
| Piercing | Only Special Weapons class marines (Wildcat, Wolfe) pierce. Chance = 0.20 × piercing skill points (Wildcat 2 → 40%, Wolfe 3 → 60%). Each bullet passes through **1** extra alien at most (`iMaxPenetrate = 1`), and never through shieldbugs. The pierced shot is flattened to z = 0 when shooter and target are within 70 u of height. The bonus applies to **any** hitscan gun those marines fire. | `asw_marine_shared.cpp:668-687,1268-1374`, `asw_marine_skills.cpp:28,74,219-221` |
| Leadership "crit" | Each shot rolls for double damage, with chance = 0.03 × the highest Leadership points within `asw_leadership_radius` **600** (Sarge 5 → 15%, Jaeger 3 → 9%). Damage-amp powerup ×2. | `asw_marine_resource.cpp:305-330` (server), `asw_marine_skills.cpp:22,68` |
| Gib threshold | Damage > 200 sets `DMG_ALWAYSGIB` | `asw_marine_shared.cpp:59,886` |

### Marine skill values (static per profile)

Skill points come from `resource/profiles.res` (VPK). Values are base + step × points, from `game/shared/swarm/asw_marine_skills.cpp:22-139` (cvars) and `:194-345` (formulas). A marine without a skill counts as 0 points.

| Marine | Accuracy (rifle dmg +1/pt, pistol/shotgun +2, PDW +1, prifle +1, sniper/railgun +10, flamer +0.5, tesla +0.25) | Reloading (time scale 1.4 − 0.14/pt; fast window ×(1 + 0.05/pt)) | Agility (move speed 290 + 10/pt) | Other |
|---|---|---|---|---|
| Sarge | 3 | – (×1.4) | – (290) | Leadership 5, Vindicator 2, Grenades 2, Health 4 |
| Wildcat | 4 | 3 (×0.98) | 4 (330) | Autogun 4, Piercing 2 |
| Faith | 1 | 2 (×1.12) | 3 (320) | Healing 5 |
| Crash | 3 | 4 (×0.84) | – | Grenades 2 |
| Jaeger | – | – | – | Leadership 3, Vindicator 5, Grenades 4, Melee 2 |
| Wolfe | 2 | 2 (×1.12) | – | Autogun 5, Piercing 3 |
| Bastille | 3 | 3 (×0.98) | – | Healing 4, Drugs 3 |
| Vegas | – | 2 (×1.12) | – | Melee 4 |

Reload time = `reload_time` × scale (`asw_weapon_shared.cpp:710-723`). The rifle's 2.0 s therefore becomes **2.8 s** for a marine with no Reloading skill, which matches the code comment "assuming 2.8 base reload time" at `:873`. The best case is 1.68 s (Crash).

---

## 1. Weapons

Numbers come from the installed `GAME/scripts/asw_weapon_*.txt` (`clip_size`, `reload_time`, `base_damage`, `fire_rate`, `num_pellets`, `FlinchChance`, `StoppingPowerFlinchBonus`), plus the code listed in each row. RPM = 60 / fire_rate.

| Weapon (script) | Interval / RPM | Damage per hit (+skill) | Pellets | Clip | Reload (script) | Spread | Laser range | Move scale | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Assault rifle (`rifle`) | 0.07 / 857 | 5 (+1 per Accuracy pt) | 1 | 98 (+8 grenades, 5 default) | 2.0 | 3° (`server/swarm/asw_weapon_rifle.h:33-37`) | 600 | 0.5 firing/reloading, else 1.0 | Flinch 0.20. Alt fire: rifle grenade (below). |
| Prototype rifle (`prifle`) | 0.07 / 857 | 5 (+1 per Accuracy pt) | 1 | 98 / 8 | 2.0 | 3° (inherits rifle) | 600 | 0.5 / 1.0 | **Autoaim radius ×1.5** with horizontal snap (`asw_weapon_prifle_shared.h:25-26`). Alt: stun grenade (`asw_stun_grenade_time` 6.0, `server/swarm/asw_grenade_prifle.cpp:21`). Blue tracer. |
| Autogun (`autogun`) | 0.1 / 600 | 7 (+1 per Autogun pt) | 1 | 250 | 2.0 | **7°** (`asw_weapon_autogun_shared.cpp:194-197`) | 600 | **0.5 firing, 0.8 always otherwise** (`:177-180`) | Autoaim radius ×1.5 with horizontal snap (`.h:28-29`). Special Weapons class only. Spin-down sound on release. Flinch 0.20, bonus 0.30. |
| Minigun (`minigun`) | 0.04 / 1500 at full spin; interval = 0.04 / max(spin, 0.75) → 0.053 at the threshold | 7 (+1 per Autogun pt) | 1 | 250 shown; **each shot uses 0.5 round** (500 shots per clip) (`asw_weapon_minigun.cpp:211-219`) | 2.0 | **15° horizontal, 0.02 vertical** (`:389-393`) | 600 | **0.4 while firing, alt-held or spin ≥ 0.99; else 0.95** (`:361-372`) | Spin-up: `asw_minigun_spin_up_rate` 1.0 per s, so **0.75 s before the first shot** (`asw_minigun_spin_rate_threshold` 0.75) and 1.0 s to full. Spin-down 0.4 per s, ×3 while reloading or meleeing. Alt-fire or walking also spins it (`:285-303`). Spin sound pitch 50→150. Flinch 0.10, bonus 0.30. |
| Shotgun (`shotgun`) | 1.0 / 60 | **25** per pellet (+2 per Accuracy pt) | **7** | 4 | 1.3 | Uniform **±11° yaw and pitch** (`GetAngularBulletSpread` (22,22,22) with `FIRE_BULLETS_ANGULAR_SPREAD`, `asw_weapon_shotgun_shared.h:53-57`, `shot_manipulator.h:95-107`). Each pellet is a **6×6×6 hull trace** (`asw_marine_shared.cpp:801-805`). | 360 | Slow only for **0.1 s** after each shot (`asw_weapon_shotgun_shared.cpp:239,258-261`) | Prefers flat aiming. The shot origin is hull-traced from the marine's centre so it can't start over an alien's head (`:129-136`). Shell eject is delayed `asw_shotgun_shell_delay` 0.8. |
| Vindicator / assault shotgun (`vindicator`) | 0.65 / 92 | **15** per pellet (+2 per Vindicator pt) | 7 (`asw_skill_vindicator_pellets_base` 7, step 0) | 14 (+8 incendiary grenades) | 2.0 | Same as shotgun (inherits) | 360 | Slow for 0.1 s after a shot **and while reloading** (`asw_weapon_assault_shotgun_shared.cpp:86-89`) | Alt: incendiary grenade (`asw_vindicator_grenade_velocity` 3.0, fuse 3). |
| Pistols (`pistol`) | 0.5 while held; **refires as fast as you click** (the button-release path sets next attack to now − 0.1, `asw_weapon_pistol_shared.cpp:294-297`) | 14 (+2 per Accuracy pt) | 1 | 24 | 1.0 | **0 (perfectly accurate)** (`.h:49-54`) | 600 | Slow for 0.03 s after a shot (`:254,276-279`) | Dual: alternates left and right muzzles and tracers (`:256-263,402-410`). |
| PDW (`pdw`) | 0.035 / 1714 | 7 (+1 per Accuracy pt) | 1 | 80 | 1.0 | 3° (`asw_weapon_pdw_shared.h:29-32`) | 600 | 0.5 / 1.0 (base) | Dual-wield muzzles. Flinch 0.10. |
| Sniper rifle (`sniper_rifle`) | 1.2 / 50 | **65** (+10 per Accuracy pt) | 1 | 12 | 2.0 | 0 | 600 | Slow for 0.03 s after a shot, **and the whole time zoomed** (`asw_weapon_sniper_rifle.cpp:209,222-225`) | Penetrates up to **2** aliens (chance 3.5, max 1; 4 under damage amp) (`:189-194`). Alt toggles zoom. |
| Flamer (`flamer`) | 0.1 | 2 (+0.5 per Accuracy pt) per projectile hit, DMG_BURN | 1 projectile per tick | 40 | 2.2 | 0 (no spread) | 280 | 0.5 / 1.0 | Projectile at **600 u/s ±10%**, life **1.0 s** (so about 600 u reach) (`asw_weapon_flamer_shared.h:80`, `.cpp:260-266`, `server/swarm/asw_flamer_projectile.cpp:81`). Ignite radius `asw_flamer_size` 40. Ignites for `asw_alien_burn_duration` **5 s** at 2.5 dps in 0.4 s ticks (`server/swarm/asw_alien.cpp:2376`), and burn damage is ×`asw_fire_alien_damage_scale` **3.0** (`:49,912-917`), so **7.5 dps, 37.5 total**. Flinch 1.0. |
| Grenade launcher (`grenade_launcher`) | 1.8 | Grenades skill: 80 (+10/pt), radius 280 (+20/pt) | – | 6 | 3.2 | – | – | – | Lobbed to the **cursor's ground point** (`UTIL_LaunchVector`, gravity ×`asw_grenade_launcher_gravity` 2.4, ×28 velocity). Explodes on world contact (`asw_weapon_grenade_launcher.cpp:70-121`). |
| Rifle grenade (rifle alt) | Primary can fire again 0.5 s later; alt 1.0 s later | Grenades skill: 80 (+10/pt), radius 280 (+20/pt) | – | 8 (5 default) | – | – | – | – | Straight shot at **1000 u/s** along the aim vector (`server/swarm/asw_weapon_rifle.cpp:132-181`). Not allowed while reloading. |
| Chainsaw (`chainsaw`) | Damage pulse every **0.1 s** | 0.5 × 1 + Melee dmg (30 + 6/pt) per pulse, so **about 300 dps** (inferred) | – | ∞ (111 shown) | – | Reach **30 u**, box −5..5 × −5..25 | (no laser) | Slow while running (`:629-632`) | Camera shake while biting: amp 12.5, freq 100, 1.0 s (`asw_weapon_chainsaw_shared.cpp:43-45,305-338,678-683`). |
| Tesla gun (`tesla_gun`) | 0.25 per shock | 1 (+0.25 per Accuracy pt), DMG_SHOCK. The primary target takes base + leftover arc damage (up to 2×). | Arcs to **2** more aliens within 160 u (range/1.5) | 20 | 2.2 | – | 240 (range 240) | Slow while reloading or after a shot | Shock **electrostuns for 6 s** (alien speed ×0.3) and forces a flinch (`asw_weapon_tesla_gun_shared.cpp:42,269-345`, `asw_alien.cpp:938-943`). Screen shake 1.0 amp × proximity within 300 u, 80 Hz, 0.5 s (`client/swarm/c_asw_fx.cpp:3598-3613`). Flinch 0. |
| Railgun (`railgun`) | No delay but **clip 1**, so effectively one shot per reload | 75 (+10 per Accuracy pt), DMG_SONIC | 1 | 1 | 1.3 | 0 | 600 | Slow for 0.1 s | **Pierces up to 10 targets** (chance 1.0) (`asw_weapon_railgun_shared.cpp:346,366`). |

Not in the core list: mining laser 50 dmg / 0.5 s, flechette 0.125 s, ricochet rifle 0.07 s (scripts present).

### Fast reload (active reload)
Code: `asw_weapon_shared.cpp:148-273` (press handling), `:872-895` (window). `asw_fast_reload_enabled` 1.
- The window opens at **29–35%** of the reload time (random).
- Width as a fraction of reload time: Easy/Normal **0.10**; Hard 0.08–0.12; Insane 0.06–0.10; Imba 0.055–0.09. Multiply by (1.0 + 0.05 × Reloading pts).
- **Hit:** the weapon can fire **0.5 s after the press**. Plays the `fast_reload` particle at the muzzle and the `FastReload.Success` sound (owner only). The laser is hidden for 2.5 s.
- **Miss** (pressing outside the window): next attack = max(now + 2.0, current end + 1.0), which is a jam. Plays the `reload_fail` particle, `FastReload.Miss`, and pain chatter.
- A UI progress bar runs from reload start to the next-attack time (client, `:276-292`).

### Reload interruption
- A diving roll cancels the reload (`OnStartedRoll`, `asw_weapon_shared.cpp:1506-1515`) unless a fast reload has already succeeded.
- Holstering also clears `m_bInReload` (`game/shared/basecombatweapon_shared.cpp:1383-1388`).
- You cannot fire during a reload; the next attack time is the reload end.

---

## 2. Aiming, autoaim, turning, laser

### Cursor to world (client, `game/client/swarm/asw_input.cpp`)
- `HUDToWorld` (`:347-675`) casts a ray from the camera through the cursor. If it hits nothing, the aim point is where the ray crosses the plane **z = marine origin + 34** (`ASW_MARINE_GUN_OFFSET_Z`, gun height; `game/shared/swarm/asw_shareddefs.h:63-65` X 25 / Y 4 / Z 34).
- **Autoaim (aim assist), screen-space:**
  1. If the cursor is directly over an aim target with line of sight, that target wins (`:427-474`).
  2. Otherwise every target within **1600 u** (`ASW_MAX_AUTO_AIM_RANGE` 2,560,000 squared, `asw_input.h:41`) gets a screen-space circle of radius `GetRadius()` = **23 u** for aliens (`c_asw_alien.h:66`). The radius is ×2 in controller mode, × the weapon's `GetAutoAimRadiusScale` (prifle and autogun 1.5), and ×2 for targets inside a flare's 250 u radius (`asw_flare_autoaim_radius`, `asw_gamerules.cpp:288`).
  3. A target qualifies if its circle intersects the **screen line from the marine through the cursor**. The **closest** qualifying target along that line wins, and LOS is required (`:476-585`).
  4. Targets more than 250 u above with dir.z > 0.85 are skipped.
- **What autoaim changes:**
  - Normally only the aim **height**. The aim plane z becomes the target's aim z (`:596`), smoothed by `SmoothAimingFloorZ`: z moves |Δ|/10 × 100 × dt per frame, roughly exponential with 0.1 s (`client/swarm/c_asw_player.cpp:2412-2430`).
  - A **horizontal snap** to the target's x,y happens only with radius-scale weapons (prifle, autogun) or flare autoaim (`:632-658`, `asw_horizontal_autoaim` 1).
  - Controller mode aims straight at the target (`:601-614`).
- **Drone aim height:** `C_ASW_Drone_Advanced::GetAimTargetPos` = drone origin + 34 (`client/swarm/c_asw_drone_advanced.cpp:329-335`). In practice the marine shoots **flat at gun height** at drones, and the comment says this lets shotguns hit several drones at once.
- Server and client `GetAutoaimVectorForMarine` both just return `EyeAngles()` forward (`server/swarm/asw_player.cpp:2190-2198` with `ASW_NO_SERVERSIDE_AUTOAIM`; `client/swarm/c_asw_player.cpp:935-941`). The per-weapon `GetAutoAimAmount` values (rifle 2°×0.3, shotgun 0.26, and so on) are therefore **unused for bullets**. All assist lives in the client cursor code above.

### Facing and turn rate
- `ComputeNewMarineFacing` (`asw_input.cpp:809-932`) solves the yaw so that a gun offset 4 u to the marine's right points through the aim point. Targets nearer than **300 u** are pushed out to 300 for the yaw solve, which avoids twitching (`:858-875`). Pitch comes from the gun position to the aim point.
- `SmoothTurningYaw` (`:714-775`): linear turn **`asw_marine_linear_turn_rate` 600°/s**, × weapon `GetTurnRateModifier` (**0.5 while firing**, so 300°/s). dt is capped at 0.2. The fractional mode is off (`asw_marine_fraction_turn_scale` 0).
- The marine does not turn if the mouse hasn't moved and the marine is still (`:967-985`).
- Bullets fire along the **smoothed EyeAngles** (`asw_weapon_shared.cpp:621-625`), so a fast cursor flick **sweeps** the stream at 300°/s instead of snapping. **(inferred feel consequence)**
- Shot origin is `Weapon_ShootPosition` = origin + up·34 + fwd·25 + right·4, using yaw only (`asw_marine_shared.cpp:253-282`).

### Laser sight (`client/swarm/c_asw_weapon.cpp:662-850`, particles in VPK `particles/asw_weapon_fx.pcf`)
- **Path:** from the weapon's **muzzle attachment** along the **same `vecDirShooting` the bullets use** (EyeAngles forward, before spread), traced with `MASK_SHOT` out to `GetLaserPointerRange()`:
  - 600 by default (`c_asw_weapon.h:196`); shotgun and vindicator 360; flamer 280; tesla, heal gun and extinguisher 240.
  - It stops on the first wall or alien.
  - The "exact cursor" correction applies only if the laser is longer than `asw_laser_sight_min_distance` **9999**, which is effectively never.
- **It follows the marine's actual (turn-limited) facing, not the cursor.**
- **Local player's laser:** particle `weapon_laser_sight`, a `render_rope` of 32 nodes using `particle\beam_laser_soft_01.vmt`:
  - Color **pure red (255,0,0)**, particle radius **12**, alpha 30–32 of 255.
  - Slow alpha oscillation (frequency 0.75–2.5).
  - Fades in over the first 8 u from the muzzle and fades out over the last **52 u** before the hit point.
  - Overall alpha is driven by CP3.x (→ alpha2, max 0.4): code sets 0.65 normally, **×0.06 while firing** (nearly invisible while shooting), and 0 while reloading, meleeing, switching, during slow-mo, while using an object, or for 2.5 s after a fast reload (`:754-783`).
- When the laser touches a **marine**, a child `weapon_laser_sight_FF` (dotted line, `beam_dotted_line_1.vmt`, red, radius 2, alpha 38) shows at CP3.y = 0.65, ×1.5 while firing. This is the friendly-fire warning.
- **Other players' lasers:** `weapon_laser_sight_other`, **orange-red (217–224, 66–84, 0)**, radius 9, alpha 24–28, only **100 u** long, code alpha 0.3 (`:758-763`).
- No separate dot particle exists in these systems. The rope just ends at the hit point (CP2 is oriented to the surface normal).
- Weapons with `OrientToLaser` (default 1) are rotated to align with the laser (`:680-702`).
- `asw_laser_sight` 1 (archive).

---

## 3. Shooting feedback

**Muzzle flash**
- Particle per weapon (`muzzle_rifle`, `muzzle_autogun`, `muzzle_shotgun`, `muzzle_pdw`, `muzzle_vindicator`, `muzzle_pistol`, `muzzle_proto_rifle`, `muzzle_railgun`) in `particles/asw_muzzle_fx.pcf`.
- `muzzle_rifle` is a flame sprite plus an additive glow, emitted for 0.01 s at 1100/s. Particle life is **0.011–0.021 s**, so it lasts one or two frames. Children: `muzzle_sparks_short`, `muzzle_rifle_glow`. Colors are warm white/yellow (255,251,218) and glow (255,210–235,102–139).
- Scale (CP10) = 1.0 + 0.2 × Accuracy pts (`c_asw_weapon.cpp:294-306`, `asw_marine_skills.cpp:134-135`). The vindicator uses 1.5 × that with the Vindicator skill; the minigun uses 2 × that with the Autogun skill.
- The flash turns **red tint (1, 0.55, 0.55)** at scale ≥ 1.9 (minigun: ≥ 1.15 after halving). With these profiles, only Wildcat and Wolfe's minigun goes red. **(inferred)**
- Dynamic light: radius 50–100 (`asw_muzzle_light_radius_min/max`), color `asw_muzzle_light` "255 192 64 6", life **0.05 s** (`c_asw_weapon.cpp:92-95,358-380`).

**Tracers** (`client/swarm/c_asw_fx.cpp:1926-2052`, `particles/asw_tracer_fx.pcf`)
- One per bullet, a particle from muzzle to hit point. `render_sprite_trail` with `particle\tracers\asw_bullet_tracer_1.vmt`.
- Speed **3000 u/s** for every weapon.
- Trail length 0.1–0.3 s × speed, capped by `max length`, so in practice a **90–140 u streak**.
- Per weapon (color, radius, max length):

  | Tracer | Color | Radius | Max length |
  |---|---|---|---|
  | `tracer_rifle` | 255,176,92 → 255,212,173 (orange) | 10–12 | 120 |
  | `tracer_default` | 255,250,218 | 10 | 120 |
  | `tracer_autogun` | 255,208–223,106–127 | 16 | 90, plus trail child |
  | `tracer_minigun` | 255,165–175,196–203 (pinkish) | 14 | 140, plus trail |
  | `tracer_shotgun` / `tracer_vindicator` | 255,250,218 | 9 / 10 | 120 / 90, vindicator adds smoke |
  | `tracer_pistol` | 255,177–194,76–87 | 14 | 120 |
  | `tracer_pdw` | 255,228,100–135 | 10 | 120 |
  | `tracer_proto_rifle` | **blue** 108–183,111–185,255 | 10–13 | 110 |

- A red-tint variant (CP10 = 1, 0.65, 0.65) is used when the muzzle is red.
- The old line tracer (`asw_tracer_style` 1, `asw_use_particle_tracers` 1) is 64–128 u long at 3000 u/s.
- The local player's tracers are spawned client-side. The server sends them only to other players (`asw_marine_shared.cpp:1827-1855`).

**Impacts**
- **On aliens:** particle `drone_shot` (`particles/infested_blood.pcf`), spawned at the hit point facing back toward the shooter (`game/shared/swarm/asw_fx_shared.cpp:57-71`, `asw_alien_shared.cpp:93-98`):
  - 3–4 green goop sprites (146–174, 215–229, 105–109), radius 6–10 growing ×4, life 0.2–0.4 s.
  - Child bursts of 4–16 trail streaks at 100–200 u/s, life about 0.1–0.13 s.
  - A spark child and `drone_blood_goop`.
  - **Green blood decals** on surfaces behind the alien: 1 trace under 10 dmg, 2 under 25, 4 at 25 or more, out to 172 u (`asw_alien_shared.cpp:100-169`).
- **On walls:** the standard Source `UTIL_ImpactTrace(DMG_BULLET)` surface impact (decal, particles and sound by surface type) at the tracer end (`c_asw_fx.cpp:2037-2045`).
- **Damage numbers: off by default** (`asw_floating_number_type` 0; 1 = vgui, 2 = particles) (`asw_util_shared.cpp:1065-1113`).

**Sounds**
- Weapon `single_shot` (local marine, e.g. `ASW_Weapon_Rifle.SingleFP`) or `single_shot_npc` for others, played on every `PrimaryAttack` call (one per frame-batch of bullets).
- Drone pain `ASW_Drone.Pain` at most once every **0.5 s** (`server/swarm/asw_drone_advanced.cpp:268-275`).
- Bullet-hit-flesh sound comes from the surface property **(inferred: no explicit hit-confirm sound in code)**.
- The game's comment says bullet whiz sounds are skipped because "the camera is too high up to hear them" (`c_asw_fx.cpp:1921`).

**Camera shake**
- **No shake on firing** for any bullet gun; only the chainsaw (bite) and tesla (zap) shake.
- On the **marine being hit**: with no inflictor, amp 2, 40 Hz, 0.2 s; otherwise a **directional punch, amp 20, freq 1, 0.3 s** toward the attacker (`server/swarm/asw_marine.cpp:1355-1364`).
- Explosions: 25 / 150 Hz / 1 s within 750 u (grenades, barrels).

**Shell ejection:** particle brass `weapon_shell_casing_rifle` for the autogun, minigun and sniper, and `..._shotgun` for the shotgun (delay 0.8 s). The plain rifle has no code-side ejection **(it may come from model anim events, not checked)**.

**Marine fire animation:** `PLAYERANIMEVENT_FIRE_GUN_PRIMARY` restarts a fire gesture layer on each tracer (`c_asw_fx.cpp:2047`, `asw_playeranimstate.cpp:275-282`). There is no code recoil, view punch or aim kick.

---

## 4. Alien hit reactions (drone)

| Property | Value | Where |
|---|---|---|
| Drone HP | `asw_drone_health` **40** × difficulty factor, minimum 25 | `server/swarm/asw_drone_advanced.cpp:54,2322-2330` |
| Difficulty factor | 1 + (missionDifficulty − 5) × 0.2. Mission difficulty: Easy 3, Normal 5, Hard 7, Insane 10, Imba 13, then −1 with 3 marines and −2 with 2 or fewer, plus the campaign map modifier, minimum 2. | `asw_gamerules.cpp:122-123,5154-5215,5325-5341`, `GAME/cfg/difficulty.cfg:13-16` |
| → HP | Easy **25**, Normal **40**, Hard **56**, Insane **80**, Imba **104** (4 marines, no campaign modifier) | – |
| Hurt slow | **Any** non-shock damage sets alien speed ×`asw_alien_hurt_speed` **0.5** for **0.5 s**, refreshed by every hit. Root-motion moves are also scaled ×0.05. While slowed, yaw speed is halved. | `server/swarm/asw_alien.cpp:54,944-949,2510-2552`, `asw_drone_advanced.cpp:328-341` |
| Electrostun (shock) | ×0.3 speed for `asw_stun_grenade_time` 6 s, plus a forced big flinch | `asw_alien.cpp:55,938-943`, `asw_ai_behavior_flinch`/`ForceFlinch` `:2604` |
| Light flinch | Every damaging hit sets COND_LIGHT_DAMAGE and plays the **`Flinch_Gesture` overlay (0.4 s)**, at most once per random 0.3–1.0 s | `asw_drone_advanced.cpp:2127-2151`, `game/server/ai_basenpc.cpp:959-962` |
| Heavy flinch (stagger) | Chance = weapon `FlinchChance` × (HP before the hit / max HP); the Special Weapons stopping-power bonus is 0 because no profile has the skill. Rifle 20% at full HP. On success the drone runs SCHED_BIG_FLINCH with a random anim: Small 30% (**0.4 s**), Medium 36% (0.8 s), Big 34% (0.8 s). Explosions and shock always flinch; kicks pick by Melee skill. | `server/swarm/asw_weapon.cpp:199-231`, `asw_drone_advanced.cpp:2046-2096,2153-2177`, drone.mdl `Flinch_*` 13/25 frames @30 |
| Knockback (alive) | **None from bullets.** `CASW_Alien::Knockback` (adds velocity, lifts off ground) is only called by melee knockback and the jump-jet stumble (`asw_stumble_knockback` 300, `asw_stumble_lift` 300). | `asw_alien.cpp:2395-2412`, `asw_marine_shared.cpp:1981-2006`, `asw_gamerules.cpp:4553-4658` |
| Death force | For non-explosive kills: normalized direction (attacker → alien) × `asw_drone_death_force` 5 × 10000, mass-scaled to drone 90; pitch tilted `asw_drone_death_force_pitch` −10° (upward). Explosive and burn kills use a random horizontal ¼ force. | `asw_alien.cpp:1940-1996`, `asw_drone_advanced.cpp:1272-1306` |
| Death style | At spawn, 7.5% are pre-rolled to instagib (`asw_drone_gib_chance` 0.075). On death: blast/sonic damage > 8 → instagib; any hit > 20 → instagib 95% of the time (so rifle kills never instagib from damage; sniper and shotgun-pellet sums can **(inferred)**). Otherwise `fancy` death (anim `Death01`, 1.33 s with goo fountains, then ragdoll) when `m_fFancyDeathChance ≤ 0.5`, else breaks into ragdoll pieces at 50%, else ragdoll-fade. Fire and electric kills have special death anims (1.3–2.3 s). Explosives may hurl a body at the camera (chance 0.667, at most every 10 s). A green "GreenBloodBig" decal goes under the body. | `asw_drone_advanced.cpp:69,189,1257-1306`, `asw_alien.cpp:58-61,2100-2190` |
| Gibs | `g_drone_maxgibs` 16; gib bleed time 1.5 s | `client/swarm/c_asw_fx.cpp:48,415` |

**Rifle bullets per drone** (ceil(HP / dmg), no leadership crits; at 0.07 s per bullet, time to kill = (n − 1) × 0.07):

| Rifle dmg (who) | Easy 25 | Normal 40 | Hard 56 | Insane 80 | Imba 104 |
|---|---|---|---|---|---|
| 5 (Jaeger, Vegas) | 5 | 8 | 12 | 16 | 21 |
| 6 (Faith) | 5 | 7 | 10 | 14 | 18 |
| 7 (Wolfe) | 4 | 6 | 8 | 12 | 15 |
| 8 (Sarge, Crash, Bastille) | 4 | 5 | 7 | 10 | 13 |
| 9 (Wildcat) | 3 | 5 | 7 | 9 | 12 |

So on Normal a drone dies in about **0.3–0.5 s** of rifle fire. **(inferred arithmetic)**

**Drone speed** (`asw_drone_advanced.cpp:299-326,1249-1253`, `GAME/cfg/difficulty.cfg:27-30`, drone.mdl):
- The ACT_RUN sequence `Run_Idle_01` blends `Run_01`: 360 u over 40 frames at 30 fps, so a ground speed of **270 u/s**.
- The code sets playback **1.25** for ACT_RUN, ACT_DRONE_RUN_ATTACKING and ACT_MELEE_ATTACK1, and GetIdealSpeed multiplies by playback rate, `asw_drone_speedboost` 1.0, and difficulty `asw_alien_speed_scale_*`: Easy 0.7, Normal 1.0, Hard 1.1, Insane and Imba 1.2 (the code defaults are 0; cfg sets them).
- Result: **Easy 236, Normal ≈ 338, Hard 371, Insane/Imba 405 u/s**, and half that while hurt. **(inferred from the model plus the code chain; the blend pose `idle_move` = 0 is assumed to be the full-run end)**
- Acceleration = ideal speed × `asw_drone_acceleration` 5 per second.
- Yaw speed: `asw_drone_yaw_speed` 32 ×10 = 320°/s; 640°/s while preparing an attack; 80°/s mid-swipe (`ai_motor.cpp:777` ×10).
- Hull: 34 × 34 × 69 (−17..17, 0..69) (`:222-225`).

**Drone melee:**
- Starts at `asw_drone_start_melee_range` **100**, requires the marine in its front half-plane (dot > 0), and hits within `asw_drone_melee_range` **60** using a 32 × 32 × 64 hull trace (`:38-39,721-787,910-935`).
- Damage `sk_asw_drone_damage` **15** × the alien damage factor (0.6 / 1 / 1.4 / 2.0 / 2.6), minimum 3; force `asw_drone_melee_force` 1.67. Shove vectors −250 / −350 and view punch (20, 0, −12) (`:48,78,830-842`).
- Timing from drone.mdl `Lunge_Attack01/02/03` (ACT_MELEE_ATTACK1, weights 2/2/1): 31 frames at 30 fps = 1.0 s at 1.0 playback, **0.8 s at 1.25**. Hit event at cycle **0.733** (01, 02) → about **0.59 s** after the swing starts, or 0.40 (03) → about 0.32 s; swipe sound at cycle 0.3–0.5. **(timings inferred = cycle × 1.0 s / 1.25)**
- Drones keep moving during the lunge (the moving blend `Attack0x_N` is 270.9 u over 1 s).
- Touch damage `asw_drone_touch_damage` 0, except climbing drones, which do 20 and a 200 u/s shove.

---

## 5. Marine movement

| Property | Value | Where |
|---|---|---|
| Base run speed | Agility 290 + 10/pt: Wildcat 330, Faith 320, everyone else **290** (300 if there is no marine resource) | `asw_marine_shared.cpp:284-291`, `asw_marine_skills.cpp:65,111,341-343` |
| Difficulty scale | Easy 0.96, Normal 1.0, Hard 1.024, Insane and Imba 1.048 (cfg overrides the code defaults of 1.0) | `asw_marine_shared.cpp:67-70,297-304`, `GAME/cfg/difficulty.cfg:22-25` |
| While firing or reloading | × weapon movement scale: 0.5 base; autogun 0.8 idle / 0.5; minigun 0.95 / 0.4; shotguns, pistol and sniper only for 0.03–0.1 s after a shot | see weapon table |
| Walk key | Wish speed clamped to **180** | `asw_marine_gamemovement.cpp:731-746` |
| Acceleration | Quake-style `sv_accelerate` **10**: accelspeed = 10 × wishspeed × dt, so full speed in **about 0.1 s** **(inferred)** | `game/shared/movevars_shared.cpp:37`, `asw_marine_gamemovement.cpp:1744` |
| Friction | `asw_marine_friction` **10**, `sv_stopspeed` 100: drop = max(speed, 100) × 10 × dt, stopping in about 0.1–0.2 s **(inferred)** | `asw_marine_gamemovement.cpp:67,1416-1425`, `movevars_shared.cpp:24` |
| Gravity / max | `asw_marine_gravity` 800, `asw_sv_maxspeed` 500 cap | `asw_marine_gamemovement.cpp:66-68,926` |
| Movement axes | **Camera-relative** (`GetTopDownMovementAxis` when `asw_controls` 1), independent of facing, so **full-speed strafing and backpedalling** (no direction penalty found in code) | `asw_marine_gamemovement.cpp:1689-1692` |
| Anim | `asw_feetyawrate` 300°/s, `asw_max_body_yaw` 30° before the feet snap, `asw_facefronttime` 2.0; walk/run anim speeds 175/380 | `game/shared/swarm/asw_playeranimstate.cpp:65-82` |
| On being hit | Short stumble on non-burn damage (`asw_marine_stumble_on_damage` 1, interval 2.0), flinch gesture, pain chatter (large above 35 dmg) | `server/swarm/asw_marine.cpp:357-359,1459-1476` |
| Camera (context) | Pitch 60°, distance 412, yaw 90. Pans toward the cursor: up to 300 east/west, 200 north, 380 south, deadspace 64. Spring constant 0.75, damping 3.0, max velocity 35. | `client/swarm/asw_in_camera.cpp:15-45` |

---

## 6. Other feel-defining rules

- **Friendly fire:**
  - Bullets **do hit marines**: `SetSkipMarines(false)`, but marines mid-roll are skipped (`asw_marine_shared.cpp:755-757`).
  - `asw_marine_ff` 1: FF damage scale = 1.0 + 0.2 × (missionDifficulty − 5), i.e. Easy 0.6, Normal 1.0, Hard 1.4, Insane 2.0 (`server/swarm/asw_marine.cpp:373-378,4185-4210`).
  - `asw_marine_ff_absorption` 1 ("ramp up"): FF damage × absorption², where absorption builds at 0.25 per s while being shot and decays at 0.33 per s once 2 s have passed without FF (`:1056-1072,1977-1981,4508-4514`). The first stray bullets do nearly nothing.
  - FF melee does 0.
  - FF-guard mode (0) stops the shooter firing for 5 s.
  - The laser shows a dotted FF warning line when aimed at a marine.
- **Marine death protection:** one hit can't kill a marine unless they are on 1 HP (`asw_marine_death_protection` 1, `asw_marine.cpp:364`).
- **Alien soft collision:** aliens push each other apart within `asw_springcol_radius` 50, cap 33, force ×3 (`asw_alien.cpp:67-71`).
- **Fire:** burning damage to aliens ×3. The flamer's flinch chance is 1.0, so it nearly always staggers healthy drones **(inferred: chance scales with remaining HP fraction)**.
- **Death cam:** on marine death, time slows to 0.035 for 0.4 s, holds for 1.75 s (`asw_gamerules.cpp:157-163`). Stim slow-mo is 0.35.
- **Hit registration summary:** hitscan along the smoothed facing, applied instantly at 1500 u range, no falloff, lag-compensated. Shotgun pellets use small hull traces. Tracers are cosmetic and travel at 3000 u/s, so they **lag** the actual hit by up to 0.5 s at long range **(inferred)**.

---

## Tuning takeaways for the SC2 port (inferred)

1. The rifle is a laser-straight hose: 857 RPM, ±1.5° triangular spread, 5–9 dmg. A drone dies in 5–8 bullets on Normal, about 0.3–0.5 s. The marine slows to **half speed** and turns at **300°/s** while firing.
2. The big stopping-power effect is the **0.5 s, 50% hurt-slow on every hit**, not knockback. Continuous fire keeps drones at about 170 u/s, against about 338 u/s unhurt on Normal and a marine at 145 u/s while firing. Add a 20%-scaled-by-HP chance of a 0.4–0.8 s stagger, plus a 0.4 s flinch overlay at most every 0.3–1.0 s.
3. Aim assist moves the shot **height** (to gun height, flat) and picks the nearest alien along the cursor line. It does not bend yaw except on the prifle, autogun and inside flare radius.
4. The laser is a faint pure-red rope (particle alpha 30/255, further scaled by about 0.26 through CP3) from the muzzle out to 600 u or the first hit, and nearly vanishes while firing (×0.06). Tracers are short (about 120 u) warm-orange streaks at 3000 u/s, one per bullet. The muzzle flash lasts 1–2 frames with a 50 ms orange point light.
5. Reload is 2.8 s for most marines. The fast-reload window is about 0.28 s wide, starts at about 32%, and unlocks fire 0.5 s after the press; a miss jams for 2 s or more. The remaining clip is discarded.
