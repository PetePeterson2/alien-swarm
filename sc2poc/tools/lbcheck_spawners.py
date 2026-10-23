"""Landing Bay's spawners against the original map's entity lump.

Every asw_spawner in asi-jac1-landingbay_01 (dumped with the scratch BSP reader to
<ents.txt>) should be a row of tools/landingbay.py SPAWNERS with the same alien,
counts, interval, skill gating and spawn rule. Positions are not compared: the
level is traced at a coarser grid and some spawners were nudged into rooms.

    py tools/lbcheck_spawners.py <asi-jac1-landingbay_01.ents.txt>
"""
from collections import Counter
from pathlib import Path
import re, sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import landingbay as L

# AlienClass is an index into the SDK's spawnable list (asw_spawner.cpp), in this order.
KIND = ['AS_DRONE', 'AS_BUZZER', 'AS_PARASITE', 'AS_SHIELDBUG', 'AS_GRUB', 'AS_JUMPER', 'AS_HARVESTER', 'AS_XENOMITE',
        'AS_QUEEN', 'AS_BOOMER', 'AS_RANGER', 'AS_MORTAR', 'AS_SHAMAN']


def num(e, k, dflt):
    # Instanced spawners carry '???' where the instance fills a value in: the default stands.
    try:
        return float(e.get(k, dflt))
    except ValueError:
        return float(dflt)


def entities(text):
    for block in re.findall(r'\{(.*?)\}', text, re.S):
        yield dict(re.findall(r'"([^"]*)" "([^"]*)"', block))


def key(name, alien, num, live, interval, infinite, smin, smax, near, burrow):
    return (name, alien, int(num), int(live), round(float(interval), 2), int(infinite), int(smin), int(smax), int(near))


def main():
    text = Path(sys.argv[1]).read_text(encoding='utf-8', errors='replace')
    every = list(entities(text))
    # Output targets: the text before the first separator of every On* value (an entity repeats its On* keys).
    targets = {re.split(r'[,]', v)[0] for k, v in re.findall(r'"(On\w+)" "([^"]*)"', text)}
    ents, dead = [], []
    for e in every:
        if e.get('classname') != 'asw_spawner':
            continue
        # SpawnerState 1 waits for an input (asw_spawner.h SST_WaitForInputs): one nothing targets never spawns.
        if num(e, 'SpawnerState', 0) == 1 and e.get('targetname', '') not in targets:
            dead.append(e.get('targetname', ''))
            continue
        ents.append(e)
    print('never started in the original (left out): %d (%s)' % (len(dead), ', '.join(sorted(set(dead)))))
    want = Counter()
    for e in ents:
        cls = e.get('AlienClass', '0')
        want[key(e.get('targetname', ''), KIND[int(cls)] if cls.isdigit() else 'AS_DRONE',
                 num(e, 'NumAliens', 0), num(e, 'MaxLiveAliens', 0), num(e, 'SpawnInterval', 0),
                 num(e, 'InfiniteAliens', 0), num(e, 'MinSkillLevel', 0), num(e, 'MaxSkillLevel', 0),
                 num(e, 'SpawnIfMarinesAreNear', 0), 0)] += 1
    have = Counter(key(*((r[0], r[3]) + tuple(r[4:12]))) for r in L.SPAWNERS)
    missing, extra = want - have, have - want
    for k, n in sorted(missing.items()):
        print('in the map, not in landingbay.py: %d x %s' % (n, k))
    for k, n in sorted(extra.items()):
        print('in landingbay.py, not in the map: %d x %s' % (n, k))
    print('%d spawners in the map, %d rows, %d differ' % (sum(want.values()), len(L.SPAWNERS), sum(missing.values()) + sum(extra.values())))
    sys.exit(1 if missing or extra else 0)


if __name__ == '__main__':
    main()
