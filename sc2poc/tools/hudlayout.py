"""Where the HUD goes, in SC2's 1200-high UI units: Alien Swarm's scripts/HudLayout.res (ASW_Hud_Master,
ASWHudMinimap) and the objective, use-area and overlay layouts of its HUD code, which work in 480-high
proportional units, times 2.5. build.py writes every upper-case name here into the map script as
`const int AS_HUD_<NAME>` (tints as `const color`), and tools/hudart.py's mockup places the art with them.
"""

# The bottom strip: one dialog anchored bottom left, STRIP_H tall; y counts down from its top.
STRIP_W, STRIP_H = 1360, 400
GUN_W, GUN_H = 200, 100                  # PrimaryWeapon / SecondaryWeapon at (18, r160) and (18, r130)
GUN1_Y, GUN2_Y = 0, 75
PX, PY = 45, 165                         # MarinePortrait (18, r94)
RING = 188                               # MarinePortrait_circle_bg 75
BEZEL = 264                              # the painted housing round the ring (tools/genart.py), centred on it
BAR_W = 362                              # MarinePortrait_bar_bg 75, run on under three item slots instead of one
FACE_X, FACE_Y, FACE_R = 95, 95, 68      # MarinePortrait_face 38, 38, radius 27
CLS_X, CLS_Y, CLS = 98, 125, 55          # MarinePortrait_class_icon 39, 50, 22
NAME_X, NAME_Y = 163, 96                 # MarinePortrait_weapon_name 65, 39
LOW_X, LOW_Y = 203, 66                   # MarinePortrait_low_ammo 81, 27
BUL_X, BUL_Y, ICON = 158, 120, 28        # MarinePortrait_bullets_icon 63, 48, 11
AMMO_X, AMMO_Y = 188, 112                # MarinePortrait_bullets 75, 45
GREN_X, GREN_TX = 245, 273               # MarinePortrait_grenades_icon 98, MarinePortrait_grenades 109
CLIP_X, CLIP_Y, CLIP, CLIP_GAP = 150, 150, 30, 20    # MarinePortrait_clips 60, 60, 12, spacing 8
ITEM_X, ITEM_Y, ITEM, ITEM_GAP = 288, 98, 88, 88     # ExtraItem 115, 39, 35 (hotkey top right, quantity bottom right)
RELOAD_X, RELOAD_Y, RELOAD_W, RELOAD_H = 248, 228, 210, 26   # FastReload 99, r69, 84, 11

# Squadmates: SquadMates_x 172 to the right of the marine (here past the marine's three item slots, where
# AS has one), then every SquadMates_spacing 100, at r55.
SQ_X, SQ_GAP, SQ_Y = 640, 250, 262
SQ_NAME_X, SQ_NAME_Y = 0, -4
SQ_BG_X, SQ_BG_Y, SQ_BG_W, SQ_BG_H = 0, 22, 212, 68
SQ_CLS_X, SQ_CLS_Y, SQ_CLS = 5, 27, 58
SQ_HP_X, SQ_HP_Y, SQ_HP_W, SQ_HP_H = 48, 28, 100, 20
SQ_AM_X, SQ_AM_Y, SQ_AM_H = 65, 52, 15
SQ_TICKS, SQ_TICK_GAP, SQ_TICK_W = 12, 7, 3
SQ_CLIP_X, SQ_CLIP_Y, SQ_CLIP, SQ_CLIP_GAP = 58, 70, 18, 13
SQ_ITEM_X, SQ_ITEM_Y, SQ_ITEM = 150, 25, 62

# Objectives, top left (CASWHudObjective::LayoutObjectives at asw_hud_scale 0.8): a black bar behind the
# header, a tick box per objective, "Objective complete!" typed out under the last one.
OBJ_X, OBJ_Y, OBJ_HEAD, OBJ_ROW, OBJ_TICK, OBJ_BAR_W, OBJ_W = 18, 18, 30, 28, 22, 444, 760

# The use panel, bottom centre (ASWHudUseArea at y 290..450): override and countdown progress.
USE_W, USE_H, USE_B, KEY = 470, 96, 144, 56

# The minimap, bottom right (ASWHudMinimap r171, 298, 160 wide at asw_hud_scale 0.8, map 0.7 of it).
MM, MM_R, MM_B, MM_BORDER, BLIP, BLIP_OBJ, BLIP_ALIENS = 224, 28, 55, 10, 12, 18, 24

# Overlay messages and notices (CASWHudOverlayMessages at YRES(80)), announcements across the middle.
MSG_W, MSG_H, MSG_Y = 900, 52, 200

# The commander's lines over the use panel: the subtitle box, and while he speaks his face on a comm screen
# at its left, standing taller than it (the SC2 campaign's transmission portrait). FACE is the screen's side;
# the two are centred together.
SUB_W, SUB_H, SUB_B, FACE, FACE_GAP = 1300, 110, 340, 200, 10

# Fonts, in style heights (DefaultSmall 8, Default 10, DefaultLarge 15, DefaultExtraLarge 20 of 480).
F_SMALL, F_DEFAULT, F_LARGE, F_XL = 18, 22, 30, 48

# Tints (r, g, b), multiplied over the grey-scale art.
HP_TINT = (106, 172, 205)                # sheet1 marine_health_circle_FG / team_health_bar_FG
HP_LOW = (106, 172, 205)                 # AS keeps the bars blue at low health; the ring's track pulses red
GHOST_TINT = (235, 235, 235)             # the health just lost, fading (m_colorDelay)
INFEST_TINT = (96, 220, 64)
BAR_TINT = (100, 190, 230)
INACTIVE = (66, 142, 192)                # weapons and items not in hand
GLOW = (35, 214, 250)                    # the glow of headers and "Objective complete!"
