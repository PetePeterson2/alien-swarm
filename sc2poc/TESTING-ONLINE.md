# Cargo Elevator: 4-player online test

The mission plays solo too: AI marines fill any empty slots. These steps are for the real test, four people on Battle.net.

## 1. Build

```
py build.py
```

This writes `dist/AlienPOC.SC2Map` (the archive) and `editor/AlienPOC.SC2Map` (the same map as a folder the Editor opens).

## 2. Publish it privately (the host does this once per build)

1. Open the StarCraft II Editor, then **File → Open** `sc2poc/editor/AlienPOC.SC2Map`.
2. **File → Publish**. Choose your region and **Private**. Name: `Halcyon Drift: Cargo Elevator`.
3. Republish after every rebuild; the name stays the same, so friends get the update.

Private maps don't show in the Arcade search, but anyone in your lobby can play them.

## 3. Host

1. In the client: **Arcade → My Published → Halcyon Drift: Cargo Elevator → Create Lobby**.
2. Invite three friends. All four slots are on one co-op team; empty slots become AI marines.
3. Start.

## 4. What to check, in order

| Beat | Look for |
|---|---|
| Landing bay | All four marines spawn together. WASD and mouse aim feel responsive on Battle.net (input delay is the big unknown). |
| Observation gallery | Four windows burst inward one after another, and drones pour through. |
| Security door | Standing at the console fills the override bar (a second marine speeds it up). A swarm comes while you hold it. The door slides open. |
| Crew quarters, north passage | The vent blows (fire, shake, parasites). |
| Upper concourse | Swarms start arriving every 45-70 s. |
| Elevator lobby | The objective says to board. The platform ringed in black, with tall shaft walls, should look like a drop. |
| Boarding | The lift won't start until every living marine stands on the platform. A 5 s countdown starts; it cancels if anyone steps off. |
| **The ride (about 75 s)** | The bridge retracts and the gates close. The shaft walls scroll upward, so the platform reads as descending. Lamps sweep up past you, red lights circle, and the alarm beacons turn. Aliens crawl head-down along the walls and leap onto the platform; buzzers rise out of the drop. A power surge blacks everything out for 2 s at about 40 s. The lift brakes, the exit lintel rises into place, the gates part and the bridge runs out. |
| Lower level | The infested freight junction, then the service shaft, the colony concourse and the transit station. |
| Extraction | Every living marine inside the green platform ends the mission. The debrief shows kills, accuracy, damage and deaths, then the game ends after 30 s. |

Deaths: a downed marine comes back beside a living teammate after 10 s. If the whole squad dies, everyone redeploys at the last checkpoint.

## 5. Report back

- Did everyone stay in sync (no desync drop)? How did aiming feel at real latency?
- Frame rate during the ride with four marines and a full wave.
- Anything that looked wrong in the shaft: pieces popping, walls facing the wrong way, gaps.
- Too hard or too easy for four (alien counts scale with squad size).

## Solo QA builds

- `.\launch.ps1 -QA` shows script errors on screen. **Ctrl+L** jumps the squad to the next beat (door, lobby, platform, near the bottom of the ride, extraction). Ctrl+G god mode, Ctrl+K kill all aliens.
- `.\launch.ps1 -Auto` plays the mission by itself (marine 1 follows the route, AI marines follow) and logs every beat to `Documents/StarCraft II/Accounts/<id>/<id>/Banks/ASAuto.SC2Bank`.
