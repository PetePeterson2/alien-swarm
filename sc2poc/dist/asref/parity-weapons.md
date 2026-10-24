# Weapons and items audit: Alien Swarm (2010) vs the SC2 port (working tree, 2026-10-24)

(Returned by the weapons agent as text; saved here verbatim.)

Correction to combat-sdk-notes: the grenade launcher's script fire_rate 1.8 is dead data; shared/swarm/asw_weapon_grenade_launcher.h:34 overrides GetFireRate() to 0.4. The port's rateAS=0.4 is right.

## Summary table (regular slot, port values from State.galaxy:297-373)

| # | Item | AS clip/reserve | Port | AS reload / Port | AS dmg (+skill) / Port | AS interval / Port rate,rateAS | Pellets | Flinch | Unlock | Class | Delta |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Assault Rifle | 98/490 (+5 of 8 gren.) | 98/490, alt 13 | 2.0/2.0 | 5+1 Acc / same | 0.07 / 0.07 | 1 | 0.20 | 1/1 | any | none |
| 2 | Prototype Rifle | 98/490 | 98/490, alt 13 | 2.0/2.0 | 5+1 Acc | 0.07 / 0.07 | 1 | 0.20 | 1/1 | Tech | none |
| 3 | Autogun | 250/250 | 250/250 | 2.0/2.0 | 7+1 Autogun | 0.1 / 0.1 | 1 | 0.20 | 1/1 | SW unique | none |
| 4 | Vindicator | 14/70 (+5/8 incend.) | 14/70, alt 13 | 2.0/2.0 | 15+2 Vind | 0.65 / 0.625,0.65 | 7 | 0.20 | 1/1 | Officer | 1/16, dmg x0.962 |
| 5 | Twin Pistols | 24/240 | 24/240 | 1.0/1.0 | 14+2 Acc | 0.5 held, click-rate / 0.5 semi | 1 | 0.10 | 1/1 | any | none |
| 6 | Sentry Gun | 1 | 1 | – | 10 x difficulty / 10x1.28 (Weapons.galaxy:834) | 0.1 (code) / 0.0625 | – | – | 1/1 | any | 2x dps |
| 7 | Heal Beacon | 4+1 Healing | same | – | pool 50+10/pt | – | – | – | 1/1 | Medic | none |
| 8 | Ammo Satchel | 3 | 3 | – | 100 units | – | – | – | 1/1 | any | none |
| 9 | Shotgun | 4/32 | 4/32 | 1.3/1.3 | 25+2 Acc | 1.0 / 1.0 | 7 | 0.20 | 3/3 | any | none |
| 10 | Tesla Cannon | 20/260 | 20/260 | 2.2/2.2 | 1+0.25 Acc | 0.25 / 0.25 | arcs 2 | 0 | 5/5 | any | none |
| 11 | Rail Rifle | 1/72 | 1/72 | 1.3/1.3 | 75+10 Acc | 0 (clip 1) | 1 | 0.20 | 7/7 | any | n/a |
| 12 | Medical Gun | 40+10 Healing (code) | 40+10 | never | heals 5+1 Healing | 0.33 / 0.3125,0.33 | – | 0 | 9/9 | Medic unique | 1/16; heal not rescaled |
| 13 | PDW | 80/400 | 80/400 | 1.0/1.0 | 7+1 Acc | 0.035 / 0.035 | 1 | 0.10 | 11/11 | any | none |
| 14 | Flamer | 40/200 | 40/200 | 2.2/2.2 | 2+0.5 Acc, burn x3 | 0.1 / 0.1 | 1 proj | 1.0 | 13/13 | any | model differs |
| 15 | Freeze Sentry | 1 | 1 | – | freeze 0.4/hit, 25 scaled / 0 dmg, 0.6 s freeze | – / 0.125 | – | – | 15/15 | any | dmg |
| 16 | Minigun | 250/250, 0.5 round/shot | same | 2.0/2.0 | 7+1 Autogun | 0.04/spin / 0.04 | 1 | 0.10 | 17/17 | SW unique | none |
| 17 | Marksman | 12/60 | 12/60 | 2.0/2.0 | 65+10 Acc | 1.2 / 1.2 | 1 | 0.20 | 19/19 | any | none |
| 18 | Incendiary Sentry | 1 | 1 | – | 4/proj | 0.1 / 0.125 | – | – | 21/21 | any | 1/16 |
| 19 | Chainsaw | inf | 1, no reload | – | 0.5x(1+Melee 30+6/pt) per 0.1 s / x1.25 per 0.125 s | 0.1 / 0.125 | – | 0.20 | 23/23 | any | compensated |
| 20 | Sentry Cannon | 1 | 1 | – | gren dmg x0.5, r x0.5 | 1.75 / 1.75 | – | – | 25/25 | any | none |
| 21 | Grenade Launcher | 6/18 | 6/18 | 3.2/3.2 | Grenades 80+10, r 280+20 | 0.4 (code) / 0.375,0.4 | – | – | 27/27 | any | 1/16, dmg not rescaled |

Extra slot (17): all unlock levels and class locks match. Deltas: Flares assist cone x3 vs AS radius x2; Laser Mines spread 30 deg total vs 15 deg steps, arm 0.3 vs 1 s; Damage Amp radius padded +32 u; Hornet yaw +-60/r 64 u vs AS +-35/r 50; Adrenaline fallback 5.0 vs 6.0; Electric Armor claws x0.25 vs AS fully absorbed; Incendiary Mines spacing 38 x1.6. Medkit, Welder, Heavy Armor, Freeze Grenades, Tesla Coil, Flashlight, Power Fist, Hand Grenades, Nightvision, Smart Bomb match.

XP table Progress.galaxy:37-40 = g_iLevelExperience; promo scale matches.

## Shared behaviour rules
- Hitscan, no falloff: port resolves hits at fire time, damage lands with the tracer. OK.
- Spread: AS triangular, port uniform (Weapons.galaxy:403); cone sizes right.
- Move x0.5 firing/reloading OK; shotgun/vindicator/railgun slow 0.15 s vs AS 0.1; pistols 0.9 for 0.15 s vs 0.5 for 0.03 s.
- Turn-rate limit: ABSENT (AS_Face instant, Marine.galaxy:465-468).
- Weapon switch 0.3 s vs 0.5 (Weapons.galaxy:63). Low-ammo click missing.
- Reload discards clip OK; auto-reload OK; fast reload exact (Weapons.galaxy:80-83,95-101). Roll does not cancel reload (Marine.galaxy:455-462).
- Piercing SW-only OK; leadership crit OK; amp OK.
- FF: AS full dmg x difficulty x absorption-squared ramp; port flat 50% x FFScale, bullet continues (Weapons.galaxy:315-327, Marine.galaxy:559-561).

## Per weapon
- Rifle grenade: AS straight at 1000 u/s, bursts on touch; port lobs an arc to the cursor at 14 cells/s (Weapons.galaxy:519-520,630-634).
- Prifle stun OK. Autogun OK. Vindicator incendiary OK but no child grenades for extra Grenades points; port adds early pop within 0.6 cell.
- Shotgun: port adds camera shake (AS none on bullet guns). Pistols OK. Minigun OK except no x3 spin-down while reloading.
- Marksman OK. Flamer: AS one 2-dmg hit per projectile then 5 s burn x3; port two puffs/round + contact ticks (Fx.galaxy:235) + ignite; extinguisher alt correct.
- Tesla OK (no shake). Railgun pierce 10 OK (+shake,+push). Launcher OK. Chainsaw reach ~56 u vs AS 30 u box.
- Ammo model: reserves OK; satchel OK; dropped weapon keeps clip+clips+alt OK; no shared pools (rifle/prifle, autogun/minigun); level crates refill both guns.

## AS-COMBAT proposals status
| # | Item | Status | Where |
|---|---|---|---|
| 1 | Laser flat at gun height to first hit, 7.5/4.5/3.5 cells | yes | Marine.galaxy:479-485,505-515 |
| 2 | Laser follows aim assist | yes | Weapons.galaxy:150-166, Marine.galaxy:497 |
| 3 | Laser x0.06 firing, off reload/melee/switch/use | yes | Marine.galaxy:522-525 |
| 4 | Squadmate stubs 1.25 cell at 0.46 | yes | Marine.galaxy:500-502,526 |
| 5 | AS fire rates | yes | State.galaxy:300,303,307,343,347,358 |
| 6 | Hurt-slow x0.5/0.5 s, drop push | no | Aliens.galaxy:159-187 no slow; Weapons.galaxy:211-217,416-421 still push; AS_Flinch uses 0.1+0.012*dmg, 0.22 s, not FlinchChance x HP%, 0.4-0.8 s |
| 7 | 600/300 deg/s turn | no | Marine.galaxy:465-468; Weapons.galaxy:372 |
| 8 | Sideways assist only prifle/autogun/flares | no | default autoaim=4.0 (State.galaxy:290); AS_AssistAim snaps all but flamer/launcher/tesla |
| 9 | Clip-ring reticle | no | nothing in HUD.galaxy |

## Items
- Sentries (Weapons.galaxy:736-849): AS health 300 + 150-dmg r 400 death blast; port none, aliens never target sentries. Ammo/arc/turn/ranges OK. MG 2x dps, no difficulty scale. Icer: AS 25 dmg + freeze; port 0 dmg. Setup OK. Pickup: AS hold-E dismantles into weapon with ammo, quick-E rotates: missing.
- Healing: beacon low-health multiplier 1+(1-hp%) vs AS 1+3(1-hp%) (Weapons.galaxy:941); heal gun cures a full Xenowounds share per tick vs AS spread over clip.
- Welder identical. Night vision OK. Electric armour x0.25 vs AS full absorb (Marine.galaxy:565).

## Skills
All applied except Hacking (absent; port has no Hacking skill, wire charge fixed 2/3 per s Use.galaxy:366) and the Accuracy muzzle-flash scale (1+0.2/pt).

## Prioritised deltas
High: (1) hurt-slow + drop bullet push + FlinchChance x HP% staggers; (2) turn-rate limit 600/300 with rounds and laser on turned facing; (3) horizontal assist only prifle/autogun/flare-lit, flare x2 radius; (4) sentries 300 HP, targetable, death blast, MG 0.1 s at 10 x difficulty; (5) sentry dismantle/rotate on E.
Medium: (6) FF absorption ramp; (7) clip-ring reticle; (8) rifle grenade straight at 1000 u/s; (9) electric armour full absorb; (10) beacon x4 low-health and heal-gun cure over clip; (11) roll cancels reload, switch 0.5 s, per-gun slow times; (12) rescale medical gun and launcher; (13) Hacking skill.
Low: triangular spread; no shake on shotgun/railgun; low-ammo click; minigun x3 spin-down reloading; chainsaw reach 30 u; hornet +-35/r 50; mine spacing 38; laser mines 30 deg total; stim fallback 6.0; vindicator cluster children; muzzle flash 1+0.2 Acc; amp radius pad; shared ammo pools; per-type crates.
