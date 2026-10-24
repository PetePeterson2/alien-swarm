"""Game data catalogs: units, actors, models, lighting and font styles.

Every unit here is driven by the script (src/*.galaxy): none carries a native
weapon. Marines are placed each simulation step by the WASD controller; aliens
walk with native move orders and their claws, spit and bile are resolved by
the script, as PUBG: Battle Royale did with its zerg (proven pattern: unit
actors parented to GenericUnitMinimal with Stand/Walk baselines, death models
as one-shot actors created by the script).

Stock model ids were checked against the catalog dump in
../../Documents/sc2map/doodad-royale/reference/catalog/.
"""
import xml.etree.ElementTree as ET

from tools import alien, marine, level as L


def child(e, tag, **attrs):
    return ET.SubElement(e, tag, **{k: str(v) for k, v in attrs.items()})


# How big each alien's model is drawn. These are past Alien Swarm's own sizes (the drone was
# 1.25, the buzzer 0.42): at AS's camera distance the true sizes read small next to AS's
# chunkier models, so the swarm is drawn 15-65% larger. Collision radii stay AS-sized.
# The death, fire and gib one-shots use the same numbers so a corpse matches its body.
SIZE = {'drone': 1.45, 'uber': 1.6, 'parasite': 1.05, 'shieldbug': 0.72, 'boomer': 2.6, 'buzzer': 0.7,
        'ranger': 1.0, 'mortar': 0.9, 'harvester': 0.75, 'ripper': 0.9}
# Aliens: id, stock model, model scale, life, speed, radius, flying.
# Life values are Alien Swarm's normal-difficulty numbers (asw_*_health and the
# SetHealth calls in src/game/server/swarm/), except the boomer (800 there).
# The drone is the HotS raptor (Swarm campaign mod): spikier and longer-limbed than the
# zergling, nearer AS's drone, and it is the zergling that leaps, as AS's jumper does.
ALIENS = [
    ('ASDrone',      'HotSRaptor',    SIZE['drone'],     40,   3.4, 0.40, False),
    ('ASUberDrone',  'PrimalZergling', SIZE['uber'],     500,  2.9, 0.55, False),
    ('ASParasite',   'Broodling',     SIZE['parasite'],  25,   4.2, 0.22, False),
    ('ASShieldbug',  'Ultralisk',     SIZE['shieldbug'], 1000, 1.7, 0.95, False),
    ('ASBoomer',     'Baneling',      SIZE['boomer'],    400,  1.3, 0.75, False),
    ('ASBuzzer',     'Mutalisk',      SIZE['buzzer'],    30,   3.2, 0.30, True),
    ('ASRanger',     'Hydralisk',     SIZE['ranger'],    101,  2.5, 0.40, False),
    ('ASMortarbug',  'Ravager',       SIZE['mortar'],    350,  1.6, 0.55, False),
    ('ASHarvester',  'SwarmHostMP',   SIZE['harvester'], 200,  1.0, 0.70, False),
    ('ASRipper',     'ASRipperModel', SIZE['ripper'],    160,  3.6, 0.50, False),   # original mesh (tools/alien.py)
]
# Fixed things: id, model, scale, life.
STATICS = [
    ('ASEgg', 'Egg', 0.85, 30),
    ('ASBiomass', 'DestructibleZergInfestation3x3', 0.45, 600),
    ('ASSentry', 'SentryGun', 0.85, 300),
    ('ASAmmo', 'ASAmmoCaseModel', 1.0, 0),       # Alien Swarm's ammo case (tools/propart.py KPAmmo)
    ('ASMedkit', 'PickupHealth100', 0.9, 0),
    ('ASPickup', 'PickupPlasmaGun', 0.8, 0),     # a weapon or item lying on the deck (src/Weapons.galaxy AS_DropAt)
    ('ASBarrel', 'ASBarrelModel', 1.0, 30),      # an explosive barrel, shot like an alien (AS_BARREL)
]
# Projectiles moved by the script.
PROJECTILES = [('ASGrenade', 'TossGrenadeWeapon', 0.9), ('ASBile', 'RavagerCorrosiveBileMissile', 0.8),
               ('ASSpit', 'InfestedAcidSpinesWeapon', 1.2), ('ASFlare', 'PickupGrenades', 0.4)]
# Lights: units carrying omni light models, hidden and shown by the script for flicker.
LIGHT_MODELS = {'white': 'LightOmniWhite', 'cold': 'LightOmniCyan', 'red': 'LightOmniRed', 'green': 'LightOmniGreen',
                'orange': 'LightOmniOrange', 'purple': 'LightOmniPurple', 'whitebig': 'LightOmniWhiteLarge',
                'redbig': 'LightOmniRedLarge', 'orangebig': 'LightOmniOrangeLarge', 'yellow': 'LightOmniYellow',
                'coldbig': 'LightOmniCyanLarge', 'greenbig': 'LightOmniGreenLarge', 'purplebig': 'LightOmniPurpleLarge',
                'yellowbig': 'LightOmniYellowLarge'}
# One-shot effects: id, model, scale, seconds before the safety removal.
ONESHOTS = [
    ('ASDieDrone', 'HotSRaptorDeath', SIZE['drone'], 6), ('ASDieUber', 'PrimalZerglingDeath', SIZE['uber'], 6),
    ('ASDieParasite', 'BroodlingDeath', SIZE['parasite'], 4), ('ASDieShieldbug', 'UltraliskDeath', SIZE['shieldbug'], 8),
    ('ASDieBoomer', 'BanelingDeath', SIZE['boomer'], 5), ('ASDieBuzzer', 'MutaliskDeath', SIZE['buzzer'], 6),
    ('ASDieRanger', 'HydraliskDeath', SIZE['ranger'], 6), ('ASDieMortar', 'RavagerDeath', SIZE['mortar'], 6),
    ('ASDieHarvester', 'SwarmHostMPDeath', SIZE['harvester'], 7), ('ASDieEgg', 'EggsplosionGeneric', 0.8, 4),
    ('ASDieBiomass', 'DestructibleZergInfestation3x3Death', 0.45, 5), 
    ('ASDieSentry', 'SentryGunDeath', 0.85, 5),
    ('ASFxBlood', 'BloodTargetImpact', 0.9, 2.5), ('ASFxSpark', 'MarineAttackImpact', 0.9, 2),
    ('ASFxAcid', 'HydraliskAttackImpact', 1.0, 2.5), ('ASFxBileHit', 'RavagerCorrosiveBileImpact', 0.7, 4),
    ('ASFxBoom', 'TossGrenadeImpact', 1.0, 5), ('ASFxBigBoom', 'BanelingCorrosiveExplosion', 1.4, 5),
    ('ASFxRail', 'RaynorSnipeBigBloodImpact', 0.8, 3), ('ASFxSentryShot', 'SentryGunAttackImpact', 0.8, 2),
    ('ASFxBurn', 'BroodlingDeathFire', 0.9, 4),
    # Gore: gib bursts for overkill and blasts, torn-apart and burning deaths.
    ('ASGibSmall', 'DefaultExplosionZergSmall', 0.8, 5), ('ASGibLarge', 'DefaultExplosionZergLarge', 0.6, 6),
    ('ASGibChunks', 'SplitterlingMediumCorrosiveExplosion', 0.9, 5),
    # The raptor has no torn, acid or burning death of its own: it falls with its plain one under
    # the gib bursts or the flames (AS_Gore layers those on top).
    ('ASEviscDrone', 'HotSRaptorDeath', SIZE['drone'], 7), ('ASEviscUber', 'ZerglingDeathEviscerate', SIZE['uber'], 7),
    ('ASAcidDrone', 'HotSRaptorDeath', SIZE['drone'], 7),
    ('ASFireDrone', 'HotSRaptorDeath', SIZE['drone'], 7), ('ASFireUber', 'ZerglingDeathFire', SIZE['uber'], 7),
    ('ASFireParasite', 'BroodlingDeathFire', SIZE['parasite'], 5), ('ASFireShieldbug', 'UltraliskDeathFire', SIZE['shieldbug'], 8),
    ('ASFireRanger', 'HydraliskDeathFire', SIZE['ranger'], 7), ('ASFireMortar', 'RavagerDeathFire', SIZE['mortar'], 7),
    ('ASFireHarvester', 'SwarmHostMPDeathFire', SIZE['harvester'], 7),
    ('ASAcidRanger', 'HydraliskDeathAcid', SIZE['ranger'], 7), ('ASAcidMortar', 'RavagerDeathAcid', SIZE['mortar'], 7),
    ('ASAcidShieldbug', 'UltraliskDeathAcid', SIZE['shieldbug'], 8), ('ASAcidHarvester', 'SwarmHostMPDeathAcid', SIZE['harvester'], 7),
    ('ASBloodGeyser', 'LurkerAttackDeathBloodGeyser', 0.5, 4),
]
FX_UNITS = ['Tracer', 'Arc', 'Flash', 'Burst', 'Flame', 'Smoke', 'Ring', 'Splat1', 'Splat2', 'SplatGlow1', 'SplatGlow2', 'Scorch', 'Anchor']


def build(files, hull_models, props, kit_models=(), runtime_props=(), mesh_units=()):
    """Write every catalog into ``files``. ``hull_models`` are the M3 chunk names, ``props`` the stock models placed.

    The kit build (build.py --kit) passes neither and instead ``kit_models``, the hull kit's pieces, and
    ``runtime_props``, the stock dressing, both as model actors the script creates (src/Kit.galaxy).
    """
    cat = {k: ET.Element('Catalog') for k in ('Unit', 'Actor', 'Model', 'Light')}

    def unit(ident, model, scale, life=100, speed=0.0, radius=0.0, mobile=False, flying=False, collide=False, height=0.0, turn=1080):
        u = child(cat['Unit'], 'CUnit', id=ident)
        child(u, 'FlagArray', index='Unselectable', value=1)
        child(u, 'FlagArray', index='Untargetable', value=1)
        child(u, 'FlagArray', index='NoPortraitTalk', value=1)
        if not life:
            child(u, 'FlagArray', index='Invulnerable', value=1)
        # Every unit turns: effect meshes (tracers, the laser sight) are aimed by facing.
        child(u, 'FlagArray', index='Turnable', value=1)
        for tag, val in [('LifeMax', max(1, life)), ('LifeStart', max(1, life)), ('LifeRegenRate', 0), ('Radius', radius),
                         ('SeparationRadius', radius * 0.8 if mobile else 0), ('InnerRadius', radius * 0.5), ('MinimapRadius', 0),
                         ('Height', height), ('Speed', speed), ('Acceleration', 1000 if mobile else 0),
                         ('Deceleration', 1000 if mobile else 0), ('LateralAcceleration', 46 if mobile else 0), ('TurningRate', turn if mobile else 0)]:
            child(u, tag, value=val)
        child(u, 'PlaneArray', index='Air' if flying else 'Ground', value=1)
        if flying:
            child(u, 'Mover', value='Fly')
            child(u, 'Collide', index='Flying', value=1)
        else:
            child(u, 'Collide', index='Ground', value=1 if collide else 0)
        if mobile:
            child(u, 'AbilArray', Link='move'); child(u, 'AbilArray', Link='stop')
        a = child(cat['Actor'], 'CActorUnit', id=ident, parent='GenericUnitMinimal')
        child(a, 'On', index=1, Terms='UnitBirth.' + ident, Send='Create')
        child(a, 'Model', value=model)
        child(a, 'On', index=2, Terms='ActorCreation', Send='SetScale %g' % scale)
        child(a, 'On', index=3, Terms='UnitDeath', Send='Destroy')
        child(a, 'Baselines', index='Stand', AnimProps='Stand')
        child(a, 'Baselines', index='Walk', AnimProps='Walk')
        child(a, 'FogVisibility', value='Visible')
        for who in ['Self', 'Ally', 'Enemy', 'Neutral']:
            child(a, 'VisibleTo', index=who, value=1)
        return a

    # The marines (tools/marine.py): one model per weapon family, swapped as the gun in hand changes (src/Marine.galaxy
    # AS_GunModel). Turned by unit facing, which the engine draws smoothly between steps; a turn rate high enough
    # that a flick of the mouse lands in one step.
    for gun, _, _ in marine.GUNS:
        m = child(cat['Model'], 'CModel', id='ASMarine' + gun, parent='Unit')
        child(m, 'Model', value='Derelict\\Marine%s.m3' % gun)
    unit('ASMarine', 'ASMarineRifle', 1.0, 100, 2.25, 0.36, mobile=True, collide=True, turn=7200)
    # The laser sight and its dot ride with each marine, turned the same way (tools/fx.py lays the beam along a model's -Y).
    for name in ('Laser', 'LaserDot'):
        m = child(cat['Model'], 'CModel', id='ASFx' + name + 'Model', parent='Doodad')
        child(m, 'Model', value='Derelict\\Fx\\' + name + '.m3')
        unit('ASFx' + name, 'ASFx' + name + 'Model', 1.0, 0, mobile=True, turn=7200)
    # A fallen marine: its own model (the script swaps in the gun it held and tints the suit), played through
    # Death and left lying on its last frame, as AS's dead marines stay where they fell.
    a = child(cat['Actor'], 'CActorModel', id='ASDieMarine')
    child(a, 'Model', value='ASMarineRifle')
    child(a, 'On', Terms='ActorCreation', Send='AnimPlay Death Death PlayForever')
    child(a, 'On', Terms='ActorCreation', Send='TimerSet 90 ASExpire')
    child(a, 'On', Terms='TimerExpired; TimerName ASExpire', Send='Destroy')
    child(a, 'FogVisibility', value='Visible')
    # The ripper's own animated mesh; its corpse is the same model held on the last frame of Death.
    m = child(cat['Model'], 'CModel', id='ASRipperModel', parent='Unit')
    child(m, 'Model', value='Derelict\\Ripper.m3')
    for ident, model, scale, life, speed, radius, flying in ALIENS:
        a = unit(ident, model, scale, life, speed, radius, mobile=True, flying=flying, collide=True, height=1.3 if flying else 0.0)
        if ident == 'ASRipper':
            child(a, 'WalkAnimMoveSpeed', value=alien.WALK_SPEED)
    a = child(cat['Actor'], 'CActorModel', id='ASDieRipper')
    child(a, 'Model', value='ASRipperModel'); child(a, 'Scale', value=SIZE['ripper'])
    child(a, 'On', Terms='ActorCreation', Send='AnimPlay Death Death PlayForever')
    child(a, 'On', Terms='ActorCreation', Send='TimerSet 8 ASExpire')
    child(a, 'On', Terms='TimerExpired; TimerName ASExpire', Send='Destroy')
    child(a, 'FogVisibility', value='Visible')
    m = child(cat['Model'], 'CModel', id='ASAmmoCaseModel', parent='Doodad')
    child(m, 'Model', value='Derelict\\KPAmmo.m3')
    m = child(cat['Model'], 'CModel', id='ASBarrelModel', parent='Doodad')
    child(m, 'Model', value='Derelict\\KPBarrel.m3')
    for ident, model, scale, life in STATICS:
        unit(ident, model, scale, life, radius=0.5 if life else 0.0, collide=ident in ('ASSentry',))
    for ident, model, scale in PROJECTILES:
        unit(ident, model, scale, 0)
    for kind, model in LIGHT_MODELS.items():
        unit('ASLight' + kind.capitalize(), model, 1.0, 0)
    unit('ASFlashlight', 'FlashlightModel', 1.0, 0)
    # Mission pieces moved by the script (tools/elevator.py): shaft panels, gates, bridges, platform, doors.
    for name in mesh_units:
        m = child(cat['Model'], 'CModel', id='AS' + name + 'Model', parent='Doodad')
        child(m, 'Model', value='Derelict\\' + name + '.m3')
        unit('AS' + name,'AS' + name + 'Model', 1.0, 0)
    # Aliens crawling down the shaft walls during the elevator ride: model actors, walking forever.
    for ident, model, scale in [('ASClimbDrone', 'HotSRaptor', SIZE['drone']), ('ASClimbParasite', 'Broodling', SIZE['parasite']),
                                ('ASClimbRipper', 'ASRipperModel', SIZE['ripper']), ('ASClimbUber', 'PrimalZergling', SIZE['uber'])]:
        a = child(cat['Actor'], 'CActorModel', id=ident)
        child(a, 'Model', value=model); child(a, 'Scale', value=scale)
        child(a, 'On', Terms='ActorCreation', Send='AnimPlay Walk Walk PlayForever')
        child(a, 'On', Terms='ActorCreation', Send='AnimSetTimeScale Walk 1.6')
        child(a, 'FogVisibility', value='Visible')
    # Mission markers: the turning alarm lamp on the lift, the objective beacon.
    unit('ASAlarmLamp', 'AlarmLight', 0.8, 0)
    unit('ASObjBeacon', 'Beacon_Terran', 0.9, 0)
    # The marines' own effect meshes (tools/fx.py).
    for name in FX_UNITS:
        m = child(cat['Model'], 'CModel', id='ASFx' + name + 'Model', parent='Doodad')
        child(m, 'Model', value='Derelict\\Fx\\' + name + '.m3')
        unit('ASFx' + name, 'ASFx' + name + 'Model', 1.0, 0)
    for ident, model, scale, life in ONESHOTS:
        a = child(cat['Actor'], 'CActorModel', id=ident, parent='ModelAnimationStyleOneShot')
        child(a, 'Model', value=model); child(a, 'Scale', value=scale)
        child(a, 'On', Terms='ActorCreation', Send='TimerSet %s ASExpire' % life)
        child(a, 'On', Terms='TimerExpired; TimerName ASExpire', Send='Destroy')
        child(a, 'FogVisibility', value='Visible')
    # The hull: one doodad per mesh chunk (tools/level.py, hull_meshes).
    for name in hull_models:
        m = child(cat['Model'], 'CModel', id='AS' + name, parent='Doodad')
        child(m, 'Model', value='Derelict\\' + name + '.m3')
        a = child(cat['Actor'], 'CActorDoodad', id='AS' + name)
        child(a, 'Model', value='AS' + name); child(a, 'Footprint', value='')
        child(a, 'DoodadFlags', index='DefaultToModelAABBBounds', value=1)
        child(a, 'RandomScaleRange', value='1,1')
    # Footprint-free copies of the stock dressing: collision comes from tools/level.py, not from the doodads.
    for model in sorted(props):
        a = child(cat['Actor'], 'CActorDoodad', id='ASP_' + model)
        child(a, 'Model', value=model); child(a, 'Footprint', value='')
        child(a, 'On', index=0, Terms='ActorCreation', Send='AnimPlay Stand Stand PlayForever')
        child(a, 'RandomScaleRange', value='1,1')
    for name in kit_models:
        m = child(cat['Model'], 'CModel', id='AS' + name, parent='Doodad')
        child(m, 'Model', value='Derelict\\' + name + '.m3')
        a = child(cat['Actor'], 'CActorModel', id='AS' + name)
        child(a, 'Model', value='AS' + name)
        child(a, 'FogVisibility', value='Visible')
    for model in sorted(runtime_props):
        a = child(cat['Actor'], 'CActorModel', id='ASR_' + model)
        child(a, 'Model', value=model)
        child(a, 'On', Terms='ActorCreation', Send='AnimPlay Stand Stand PlayForever')
        child(a, 'FogVisibility', value='Visible')
    # Lighting presets: L cycles them in game (src/Main.galaxy). Alien Swarm's look: a cool, readable
    # ambient (nothing is pitch black), a key light for the unit shadows, lamps doing the drama, bloom on
    # anything bright (lamps, screens, grates, muzzle flashes), and a saturated picture (Colorize would tint it all one hue: off).
    presets = [
        # id, parent, ambient, exposure, key colour, key strength, fill strength, bloom threshold
        ('ASDerelict', 'StarshipDark', '0.14,0.16,0.21', '1.30', '0.62,0.72,0.90', '0.36', '0.12', '0.85'),
        ('ASAlarm', 'StarshipDark', '0.20,0.09,0.08', '1.25', '0.90,0.40,0.34', '0.44', '0.10', '0.80'),
        ('ASPowered', 'Starship', '0.36,0.38,0.43', '1.30', '0.90,0.94,1.00', '0.85', '0.32', '1.00'),
        ('ASBlackout', 'StarshipDark', '0.05,0.05,0.07', '1.10', '0.30,0.35,0.45', '0.12', '0.03', '0.70'),
    ]
    for ident, parent, ambient, exposure, key, mult, fill, bloom in presets:
        light = child(cat['Light'], 'CLight', id=ident, parent=parent)
        tod = child(light, 'ToDInfoArray', index=0, Id=ident, AmbientColor=ambient, Colorize=0)
        for name, value in [('HDRExposure', exposure), ('HDRAmbientMultiplier', '1.0'), ('HDRDiffuseMultiplier', '1.0'),
                            ('HDRBloomThreshold', bloom), ('HDRWhitePoint', '1.6'), ('HDREmisMultiplier', '1.7'),
                            ('HDRSpecMultiplier', '1.0'), ('ColorizationBlend', '0')]:
            child(tod, 'Param', index=name, value=value)
        child(tod, 'DirectionalLight', index='Key', Color=key, ColorMultiplier=mult, Direction='-0.35,-0.45,0.82')
        child(tod, 'DirectionalLight', index='Fill', Color='0.45,0.55,0.70', ColorMultiplier=fill, Direction='0.5,0.5,0.70')
        child(tod, 'DirectionalLight', index='Back', Color='0.5,0.5,0.6', ColorMultiplier='0.05', Direction='0.0,0.80,0.60')
    # The camera follows the marine with a 0.08 s smoothing (Doodad Royale's values, proven
    # there). SC2's default follow is tuned for RTS panning and trailed a running marine by
    # about a unit, catching up only once it stopped: the screen felt like it dragged.
    cam = ET.Element('Catalog')
    for attrs in ({'default': '1'}, {'id': 'Dflt'}):
        c = child(cam, 'CCamera', **attrs)
        child(c, 'TargetSmooth', SmoothTimeMin='0.080000', SmoothTimeMax='0.080000', VelocityMax='100.000000')
        child(c, 'FollowScrollLimit', value='1000.000000')
        child(c, 'BorderSizeX', value=0); child(c, 'BorderSizeY', value=0)
    cat['Camera'] = cam
    for kind, tree in cat.items():
        ET.indent(tree, space='    ')
        files['Base.SC2Data/GameData/%sData.xml' % kind] = ET.tostring(tree, encoding='utf-8', xml_declaration=True)
    files['Base.SC2Data/UI/FontStyles.SC2Style'] = font_styles()


def font_styles():
    """The HUD's text after Alien Swarm's scheme (Neo Sans and Verdana there, Eurostile here): white, the
    quantities light blue, headers and prompts with the cyan glow of its *Blur fonts (35,214,250)."""
    root = ET.Element('StyleFile')
    reg = 'UI\\Fonts\\Eurostile-Reg.otf'; bold = 'UI\\Fonts\\Eurostile-Bol.otf'; ext = 'UI\\Fonts\\EurostileExt-Med.otf'
    white = '255,255,255,255'; light = '255,226,232,236'; pale = '255,169,213,255'; steel = '255,140,200,240'
    blue = '255,66,142,192'; red = '255,200,25,25'; dim = '255,128,128,128'; glow = '200,35,214,250'
    for name, font, size, align, color, lit in [
            ('ASSmall', reg, 18, 'Left', white, False), ('ASSmallR', reg, 15, 'Right', light, False),
            ('ASSmallDim', reg, 18, 'Left', dim, False), ('ASLarge', reg, 30, 'Left', white, False),
            ('ASLow', reg, 20, 'Left', red, False), ('ASKeyR', bold, 22, 'Right', white, False),
            ('ASKeyC', bold, 26, 'Center', white, False), ('ASQtyR', reg, 17, 'Right', blue, False),
            ('ASObjHead', reg, 22, 'Left', white, True), ('ASObj', reg, 20, 'Left', white, False),
            ('ASObjDone', reg, 20, 'Left', white, True), ('ASUse', reg, 22, 'Left', white, True),
            ('ASBig', ext, 48, 'Center', white, True), ('ASBigSub', reg, 22, 'Center', pale, False),
            ('ASNotice', reg, 21, 'Center', pale, False), ('ASHead', ext, 26, 'Left', white, True),
            ('ASHeadR', ext, 22, 'Right', pale, False), ('ASHeadC', ext, 26, 'Center', white, True),
            ('ASFrame', reg, 19, 'Left', steel, False), ('ASBody', reg, 19, 'Left', light, False),
            ('ASBodyR', reg, 19, 'Right', light, False), ('ASBodyC', reg, 19, 'Center', light, False),
            ('ASBtn', ext, 20, 'Center', '255,180,220,250', False), ('ASBtnOff', ext, 20, 'Center', '255,90,104,116', False),
            ('ASTagMe', reg, 17, 'Center', '255,255,255,0', False), ('ASTagMate', reg, 17, 'Center', '255,0,144,188', False),
            ('ASTagAI', reg, 17, 'Center', white, False), ('ASDebTitle', reg, 32, 'Left', steel, False),
            ('ASDebPlace', reg, 24, 'Right', steel, False), ('ASPanelHead', reg, 24, 'Center', white, False),
            ('ASSmallC', reg, 17, 'Center', steel, False), ('ASDebPlace2', reg, 24, 'Left', white, False),
            ('ASTab', reg, 17, 'Center', steel, False),
            # Hacking, the briefing, hints and toasts.
            ('ASHackTitle', reg, 22, 'Left', white, False), ('ASLogged', reg, 17, 'Right', '255,255,40,30', False),
            ('ASLoggedL', reg, 17, 'Left', '255,255,40,30', False), ('ASGranted', ext, 28, 'Center', '255,255,60,40', True),
            ('ASCompTitle', ext, 30, 'Center', white, True), ('ASCompSmall', reg, 17, 'Left', white, False),
            ('ASCompSmallC', reg, 15, 'Center', white, False), ('ASMail', reg, 20, 'Left', '255,200,230,255', False),
            ('ASTumb1', bold, 32, 'Center', white, True), ('ASTumb0', bold, 32, 'Center', '255,64,64,64', False),
            ('ASHint', reg, 23, 'Left', white, True), ('ASSubtitle', reg, 21, 'Left', '255,226,240,240', False),
            ('ASToastHead', ext, 18, 'Left', '255,240,200,80', True)]:
        child(root, 'Style', name=name, template='ModCenterSize20', font=font, height=size, vjustify='Middle', hjustify=align,
              styleflags='Shadow | Glow | InlineJustification' if lit else 'Shadow | InlineJustification',
              textcolor=color, highlightcolor=color, disabledcolor=color, glowcolor=glow if lit else '0,0,0,0',
              shadowoffset=1, outlinewidth=0)
    ET.indent(root, space='    ')
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)
