# Alien Swarm → StarCraft II Arcade: Feasibility Assessment

*2026-10-19. Source: [NicolasDe/AlienSwarm](https://github.com/NicolasDe/AlienSwarm), cloned to `AlienSwarm/`. Reference projects: Saboteur, PUBG: Battle Royale (`sc2map/doodad-royale`), GameNight, Seven Wonders, EatTheMap, Heist League, and the UAC fork in `uac_test`.*

## Verdict

**Feasible as a re-creation "in the spirit of" Alien Swarm. Not feasible as a port.**

- **Rules and numbers carry over cleanly.** Classes, skills, weapon stats, alien stats, the director, doors and objectives all map onto SC2 data and Galaxy.
- **The art fit is unusually good.** StarCraft's Zerg and Terran asset library is nearly a ready-made Alien Swarm cast.
- **Your PUBG map has already solved the hardest engine problems.** It has WASD movement, scripted hit detection, lag compensation, pooled tracers and staggered AI updates.
- **The real risk is feel.** Cursor aim and WASD under SC2's lockstep input delay, and darkness/flashlights, need a 2–3 day technical spike before you commit.

**Confidence:** high on systems and content, medium on control feel, low-to-medium on flashlight visuals until prototyped.

---

## 1. What the source repo and the retail install give you

*Updated 2026-10-20: the retail game is now installed from Steam (app 630, build 5587483) at `C:\Program Files (x86)\Steam\steamapps\common\Alien Swarm\swarm`. Most art is packed in `pak01_*.vpk` (6,728 files); data files are loose or in the VPK.*

| Item | Where | Status |
|---|---|---|
| Game-specific C++ (server, client, shared, map generator) | Repo | about 351K lines; about 260K is gameplay excluding menus and the generator |
| Weapon scripts (`asw_weapon_*.txt`) | Repo and retail `scripts/` | 48 files, **identical** in both. Clip, damage, fire rate and reload: **directly usable as design data** |
| Alien stats, director, skills table | Repo (code) | Readable: **directly usable as design data**. Retail `cfg/marine_skills.cfg` holds no skill data |
| Ammo limits (`sk_max_*`) | Retail `cfg/skill.cfg` | ✅ **Now available.** See 1a |
| Marine profiles | Retail VPK `resource/profiles.res` | ✅ **Now available.** See 1b |
| Equipment list | Retail VPK `resource/equipment.res` | ✅ **Now available.** See 1c |
| Campaign | Retail `resource/campaigns/jacob.txt` | ✅ **Now available.** See 1d. (`missions/campaign*.txt` are leftover Left 4 Dead 2 stubs; ignore them) |
| Difficulty scaling | Retail `cfg/difficulty.cfg` | ✅ **Now available.** See 1e |
| Maps | Retail `maps/` | 8 compiled BSPs (7 missions plus practice) and the lobby. **Not convertible** to SC2 terrain. Use as layout references (1f) |
| Procedural generator content | Retail `tilegen/` | 54 room templates and 55 VMF rooms, dev and example themes only. Reference for the Phase 2 stretch generator |
| Models, textures, sounds | Retail VPK and `sound/` | 730 models, 2,000 textures (about 475 MB), 2,443 WAVs (445 MB). Readable and convertible, but **Valve IP: reference only, never ship** (see IP note) |
| Engine source | — | Absent (prebuilt libraries only) |

### 1a. Ammo limits (`cfg/skill.cfg`)

| Weapon | Max reserve ammo | Weapon | Max reserve ammo |
|---|---|---|---|
| Rifle | 490 (5 clips × 98) | Railgun | 72 |
| Rifle grenades | 8 | Pistol | 240 (comment says 10 clips × 32) |
| Autogun | 250 | Mining laser | 250 |
| Shotgun | 32 (8 clips × 4) | Tesla cannon | 260 |
| Vindicator | 70 (5 clips × 14) | Chainsaw | 111 |
| Flamer | 200 | PDW | 400 (5 clips × 80) |
| Grenade launcher | 18 | Sniper rifle | 60 |

**Damage caveat:** `skill.cfg` also has `sk_plr_dmg_*` values that disagree with the weapon scripts (rifle 7 versus script `base_damage` 5). Per-shot damage comes from the script: `CASW_Weapon::GetWeaponDamage` (`src/game/shared/swarm/asw_weapon_shared.cpp:1236`) adds the accuracy skill bonus to `base_damage`. The `sk_plr_dmg_*` values only feed the ammo definitions in `asw_gamerules.cpp`. **Use the scripts for damage and `skill.cfg` only for ammo caps.**

### 1b. Marines (`resource/profiles.res`)

Eight marines in four classes. Points are the fixed skill levels for each of the five skill slots.

| Marine | Class | Default loadout | Skills (points) |
|---|---|---|---|
| Sarge | Officer | Rifle, Vindicator, Flares | Leadership 5, Vindicator 2, Grenades 2, Health 4, Accuracy 3 |
| Jaeger | Officer | Vindicator, Sentry, Medkit | Leadership 3, Vindicator 5, Grenades 4, Health 3, Melee 2 |
| Wildcat | Special Weapons | Autogun, Rifle, Flares | Autogun 4, Piercing 2, Accuracy 4, Reloading 3, Agility 4 |
| Wolfe | Special Weapons | Autogun, Sentry, Medkit | Autogun 5, Piercing 3, Accuracy 2, Reloading 2, Health 3 |
| Faith | Medic | Rifle, Heal beacon, Flares | Healing 5, Xenowounds 3, Accuracy 1, Reloading 2, Agility 3 |
| Bastille | Medic | Rifle, Heal beacon, Flares | Healing 4, Xenowounds 1, Accuracy 3, Reloading 3, Drugs 3 |
| Crash | Tech | Prototype rifle, Ammo satchel, Welder | Scanner 3, Engineering 1, Accuracy 3, Reloading 4, Grenades 2 |
| Vegas | Tech | Prototype rifle, Pistol, Medkit | Scanner 3, Engineering 3, Health 3, Reloading 2, Melee 4 |

### 1c. Equipment (`resource/equipment.res`)

- **Primary ("Regular"), 21:** rifle, prototype rifle, autogun, Vindicator, pistol, sentry, heal beacon, ammo satchel; then shotgun, tesla cannon, railgun, heal gun, PDW, flamer, freeze sentry, minigun, sniper rifle, flamer sentry, chainsaw, cannon sentry, grenade launcher.
- **Offhand ("Extra"), 17:** medkit, welder, flares, laser mines; then heavy armor, damage amp, hornet barrage, freeze grenades, stim, tesla trap, electric armor, incendiary mines, flashlight, fist, hand grenades, night vision, smart bomb.
- **Hidden ("Other"), 5:** fire extinguisher, mining laser, T75, blink, jump jet. These are map pickups or special cases, not loadout picks.
- Valve's comments rate most unlocks 1–10 on four axes: makes the game easier, fun to use, easy to use, not harmful to the team. **Useful for balancing a cut-down Phase 1 list.**
- Ricochet, flechette, stun grenades, hack tool and bait are commented out. This confirms they were cut (see section 6).

### 1d. Campaign: Jacob's Rest (`resource/campaigns/jacob.txt`)

A linear chain. Each mission links to the one before and after. Timor Station is revealed last.

| # | Mission | Map | Difficulty modifier | Threat |
|---|---|---|---|---|
| 1 | Landing Bay | `asi-jac1-landingbay_01` | −2 | 1 |
| 2 | Cargo Elevator | `asi-jac1-landingbay_02` | −2 | 1 |
| 3 | Deima Surface Bridge | `asi-jac2-deima` | −1 | 2 |
| 4 | Rydberg Reactor | `asi-jac3-rydberg` | 0 | 3 |
| 5 | SynTek Residential | `asi-jac4-residential` | 0 | 3 |
| 6 | Sewer Junction B5 | `asi-jac6-sewerjunction` | +2 | 5 |
| 7 | Timor Station | `asi-jac7-timorstation` | +2 | 6 |

The file also has each mission's short briefing text and campaign-map coordinates.

### 1e. Difficulty (`cfg/difficulty.cfg`)

- **Base level:** Easy 3, Normal 5, Hard 7, Insane 10, plus the mission modifier from 1d.
- **Aliens:** +20% health and +20% damage for each step above 5. This confirms the `1 + 0.2 × (difficulty − 5)` formula in section 5. Check `asw_gamerules.cpp` for how levels below 5 are clamped before porting.
- **Speed scale:**

| | Easy | Normal | Hard | Insane |
|---|---|---|---|---|
| Marines | 0.96 | 1.0 | 1.024 | 1.048 |
| Aliens | 0.7 | 1.0 | 1.1 | 1.2 |

### 1f. Map references

- **Overview images:** `resource/overviews/<map>.txt` names each mission's top-down overview texture (`materials/vgui/swarm/overviews/`) and gives `pos_x`, `pos_y` and `scale`. That maps the image onto world coordinates, so a layout can be traced onto an SC2 grid to scale.
- **BSP entity data:** each BSP stores its entities (spawners, doors, objectives) as plain text. Parsing it for placement data should be possible but hasn't been tried.
- **AI node graphs** (`maps/graphs/*.ain`): same as the repo.

**Implication:** nothing compiles or translates over. The repo plus the retail data files are a **spec**: an authoritative source of numbers and rules. With the retail files, the only data gaps left are the level layouts themselves. Code size isn't the obstacle, because SC2's engine already provides most of what that C++ does (units, pathing, AI, behaviors, networking).

**IP note (not legal advice):** don't use the "Alien Swarm" name, Valve assets or the marine names in a published map. Ship under your own title and use SC2 models.

---

## 2. System-by-system feasibility

| System | Alien Swarm | SC2 approach | Rating | Precedent in your projects |
|---|---|---|---|---|
| Players | 4 co-op (cap 6) | 4 humans plus AI-filled marines; well under the 16-slot limit | ✅ Easy | Saboteur and PUBG bot fill |
| Camera | 60° pitch, north-up, mouse lookahead | SC2's native camera is already about 56° top-down. Follow the marine each tick; lookahead is optional (it would lag) | ✅ Easy | Heist League `CAMERA_LAB.md` "Tactical overhead" |
| WASD movement | Client-predicted, 290 u/s | `UnitSetPosition` per 16 Hz tick plus wall sweep; first step on the key event (`BG_MoveNow`) | 🟡 Proven but laggy online | PUBG `World.galaxy`, EatTheMap |
| Cursor aim | Ray from the cursor, autoaim, turns 600°/s | `TriggerAddEventMouseMoved` world point (about 20 Hz, synced) plus a generous autoaim cone plus lag rewind | 🟠 **Main risk** | GameNight mouse-to-world; PUBG `BG_REWIND` |
| Hitscan guns | 0.035–0.1 s fire intervals | One trace per 16 Hz tick; scale damage per tick to keep DPS | ✅ Feasible | PUBG `Combat.galaxy` `BG_Trace` |
| Tracers and visual effects | Particles | Ring buffer of pooled units with tinted, additive meshes | ✅ Proven | PUBG `BG_RailUnit` (160 pool) |
| Projectiles (grenades, mortar, flamer, ranger spit) | Physics projectiles | Native `CEffectLaunchMissile` for AI and arcs; script-stepped for player shells | ✅ Proven | UAC (346 missile effects), PUBG `BG_LaunchShell` |
| Aliens (about 15 types) | Custom AI and behavior modules | Native units with attack orders plus Galaxy for special cases | ✅ Easy | UAC hordes (supply cap 170–350), PUBG `BG_ZergPulse` |
| Director (intensity, hordes, wanderers) | about 1.8K lines C++ | Galaxy timers plus spawn regions; logic ports almost line-for-line | ✅ Easy | UAC `SpawnUndead.galaxy` |
| Classes and skills (17 skills) | Profile and skill tables | Behaviors and upgrades, or Galaxy tables | ✅ Easy | UAC per-class MOS libraries |
| Status effects (burn, freeze, stun, infest, poison) | Custom | `CBehaviorBuff` with periodic effects: native strengths of SC2 | ✅ Easy | UAC (1,858 buffs) |
| Friendly fire | 3 modes | Your own traces already know who they hit; just allow marine targets | ✅ Easy | — |
| Shieldbug frontal shield | Hitbox-based | Facing-angle check in the trace | ✅ Easy | — |
| Doors (HP, dents, weld, bash) | Entity | Door units (Terran gate models) plus SCV-style weld channel; pathing blocker toggled | ✅ Easy | — |
| Hacking minigames (tumbler, wire puzzle) | Custom VGUI | Galaxy dialogs. **Real-time precision minigames suffer under lag**, so make them turn-based puzzles or progress bars | 🟡 Laborious | Saboteur and GameNight dialog UIs; TUNNEL RUN lag lesson |
| Briefing, lobby, loadout, HUD, minimap | about 25K lines UI | Dialog-driven; SC2 minimap is free; scanner blips are minimap pings | 🟡 Laborious but routine | Saboteur's UI, PUBG HUD |
| Darkness and flashlights | Dynamic lights, shadows | `PlayerSetLighting`/`GameSetLighting` dark presets plus fog-of-war line of sight. **Flashlight cone is unproven** | 🟠 **Needs prototype** | UAC night vision (`PlayerSetLighting`), PUBG blackout preset; *Haunted Forest* precedent noted in `SC2_Arcade_Recommendations.md` |
| Slow-mo (stim, death cam) | Global time scale | Behavior time scale or game speed; uncertain | 🟡 Minor | Not verified |
| Physics, ragdolls, frozen statues | Physics props | SC2 death animations and ragdoll-style death models; drop prop physics | ⚪ Cut or fake | — |
| Persistent XP, unlocks, medals | Steam stats | Banks (watch the about-37-file and declaration gotchas) | ✅ Proven | Saboteur, PUBG banks |
| Campaign and mission voting | Campaign save | One map with mission select, or one map per mission | ✅ Easy | — |
| Level design (7 missions) | BSPs (not in repo) | Rebuild from scratch: hand-made or Python-generated terrain and doodads | 🟠 **Biggest content cost** | `tools/basemap.py`, PUBG city kit |
| Procedural map generator | 24K lines | Optional stretch; your Python pipeline could generate corridor layouts at build time | ⚪ Stretch | — |

---

## 3. The art fit (the strongest argument for doing this)

Alien Swarm and StarCraft draw on the same *Aliens* lineage. Stock SC2 models cover almost the entire cast without imports:

| Alien Swarm | SC2 stand-in |
|---|---|
| Drone / jumper / uber drone | Zergling / Raptor zergling / Primal zergling |
| Parasite (latches on, infests, bursts) | Broodling, with an infest buff and spawn on death |
| Buzzer | Scourge- or Mutalisk-style flyer, scaled down |
| Shieldbug | Ultralisk (frontal plating) |
| Harvester (spits out parasites) | Swarm Host to Locusts |
| Mortarbug (arcing shells) | Ravager with Corrosive Bile |
| Boomer (bursts into blobs) | Baneling, scaled up |
| Ranger (ranged spit) | Hydralisk or Roach |
| Shaman (heals aliens) | Small Queen with Transfuse |
| Queen | Brood Mother or giant Queen |
| Eggs / biomass | Zerg eggs / creep and biomass doodads |
| Marines, Medic, Tech | Marine, Marauder, Medic, Firebat, SCV-style models from Wings of Liberty campaign assets |
| Sentry guns | Raven auto-turret |
| Mines, stim, welder, flares | Widow or spider mine, Stimpack, SCV repair beam, flare effects |
| Colony and station tilesets | Space Platform, Char, Korhal and Terran base doodads |

This avoids the 48–150 MB asset mods that PUBG and UAC needed, and the provenance problems that come with them.

---

## 4. The two real risks

### 4a. Control feel under lockstep (highest risk)

**The problem:** Alien Swarm relies on client-side prediction: aim and movement respond instantly. SC2 has none. Your own measurements:

- **Offline:** about 48 ms from key to movement and about 67 ms from click to tracer (PUBG). Fine.
- **Battle.net:** 5–9 loops of input delay. Strafing targets dodged 92–96% of perfectly aimed shots before `BG_REWIND`. Real players called PUBG 1.4's aiming "horrible".
- **Mouse-move:** events are synced network traffic at about 20 Hz (GameNight).

**Why it's less bad here than in PUBG:**

- It's **PvE**. Aliens charge straight in rather than strafing like human opponents.
- Alien Swarm **already has autoaim** toward the cursor (`asw_weapon_shared`), so a generous aim-assist cone toward the cursor is faithful, not a compromise.
- A **top-down cursor** is more forgiving than third-person mouse-look. You're pointing at a region, not tracking with yaw.

**Mitigations, all from your playbook:**

- Rewind traces (`BG_REWIND`).
- Take the first step on key-down (`BG_MoveNow`).
- Clear held keys on chat or menus (`BG_ChatRelease`).
- Snap the cone to the nearest alien within about 15° of the cursor direction.
- Hold-to-fire, so the click itself isn't timing-critical.

**Unverified:** your multiplayer gap. Almost nothing in your portfolio has been played by 2+ humans online. This project would need it early.

### 4b. Darkness and flashlights (atmosphere risk)

**The problem:** Alien Swarm's mood comes from per-marine flashlights casting shadows in dark corridors. SC2 options, roughly from most to least certain:

1. **Dark lighting preset** (`PlayerSetLighting`) plus **fog of war with line-of-sight blockers.** Proven by UAC and PUBG. Gives "can't see around corners" for free.
2. **Point lights attached to marines** (light actor or model with an embedded light). Your PUBG city runs about 40 point lights; performance on Low settings is unverified.
3. **True cone or spot flashlight:** a custom `.m3` with a spot light, or a projected decal or cone mesh in front of the marine. **Unproven.** The *Haunted Forest* precedent reportedly needs high shader settings, and Low-settings players may see nothing.

**Fallback if 3 fails:** options 1 and 2 still give a convincingly dark, claustrophobic map.

---

## 5. Recommended scope

### Phase 0: Technical spike (2–3 days). Go/no-go gate.

Built on `doodad-royale`'s build pipeline, not Saboteur's.

1. **Top-down controller:** 4 marines with WASD and cursor-aim hitscan rifles against 60 native zerglings pathing at them. Test `launch.ps1 -Lag 6` and **a real 2-player Battle.net session.** Kill criterion: hitting a charging drone feels reliable with aim assist at 6–9 loops of delay.
2. **Darkness:** dark preset, fog-of-war line of sight, marine point light, cone attempt. Test on the Low preset. Kill criterion: none. Pick the best option that renders on Low.
3. **Perf soak:** 4 marines × 16 Hz traces, 25 awake drones plus 20 wanderers, flamer burn buffs, 160-unit tracer pool, for 10 minutes. Watch frame rate and `ScriptError` logs.

### Phase 1: Vertical slice (about 1–2 weeks at your demonstrated pace)

- **Mission:** one, Landing Bay-style: corridors, a weld door, a hack, a horde finale, an escape.
- **Classes:** 4, with core skills.
- **Weapons:** about 8 (rifle, autogun, shotgun, flamer, grenade launcher, pistol, sentry, welder) plus about 4 offhands (medkit, flares, mines, stim).
- **Aliens:** 6 (drone, parasite, shieldbug, boomer, harvester, buzzer).
- **Director:** full, ported from `asw_director.cpp` and `asw_spawn_manager.cpp`.
- **UI:** briefing with loadout, HUD, debrief.
- **Players:** AI marines fill empty slots.

### Phase 2: Full game (about 3–5 more weeks)

- Remaining weapons (about 25 total) and aliens, including the Queen.
- 5–7 missions.
- Bank progression: XP, levels, unlocks and medals.
- Difficulty levels using the source formula `1 + 0.2 × (difficulty − 5)`.
- Optional: build-time procedural corridor generator.

**Basis for the estimates:** PUBG went from nothing to about 10K lines of combat and AI code, four arenas and 8 releases in about 8 days. Saboteur reached 74K lines and about 30 releases in about 4 weeks.

**Where to spend effort:** level design and online feel-tuning are the long poles, not code volume. Keep the script under the "code jump out of bounds" ceiling (about 40K data statements) by storing level data as strings, as PUBG does.

---

## 6. What to cut or simplify

| Cut or simplify | Why |
|---|---|
| Physics props, ragdolls, freeze-statue physics | Not worth emulating |
| Active-reload timing window | Online lag makes precise timing windows unfair (Saboteur TUNNEL RUN lesson). Use a plain reload with a skill-scaled time |
| Real-time tumbler and wire hacks | Make them untimed puzzles or channelled progress bars |
| Camera lookahead from the mouse | Would lag; use a fixed follow |
| Procedural map generator | Phase 2+ stretch only |
| Ricochet, flechette and other prototype weapons | Never localized in the source, so probably unshipped |

---

## 7. Key source files to mine for numbers

- `game/mod_swarm/scripts/asw_weapon_*.txt`: weapon stats
- `src/game/shared/swarm/asw_marine_skills.cpp`: skill base and per-point table
- `src/game/server/swarm/asw_director.cpp`, `asw_spawn_manager.cpp`, `asw_director_intensity.cpp`: pacing
- `src/game/server/swarm/asw_alien.cpp` and `asw_drone_advanced.cpp`, `asw_parasite.cpp`, `asw_shieldbug.cpp`, `asw_boomer.cpp`, `asw_queen.cpp`: alien stats and behavior
- `src/game/server/swarm/asw_door.cpp`: door HP and weld rules
- `src/game/server/swarm/asw_player_experience.cpp`: XP curve and unlock order
- `src/game/shared/swarm/asw_weapon_shared.cpp`: autoaim and fire logic
