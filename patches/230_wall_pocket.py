NAME = "wall-pocket"
DESCRIPTION = "Lower Earth Empire 2: the hero can't stand inside the brick wall at the secret tunnel's mouth (the shrunk hero still can)"

# Lower Earth Empire 2 (stage 4) has a secret: a one-cell-high tunnel through the brick wall beside the water,
# drawn as bricks, which the shrunk hero (C button) can walk through to a hidden spot about 250 px to the left.
# Its mouth is two cells tall, so the normal-size hero could get in too and stand inside the wall
# (sta/aes/brickwall.sta; the mouth is level cells (65, 23-24), the tunnel row 24 going left).
# He also gets there from the water: swimming, the game only probes a few pixels either side of his middle, so
# he can swim with his middle inside the brick column (x 534) and jumping out of the water carries him straight
# up into the mouth. Making those cells solid instead only got him stuck in the wall (the game then pushes him
# along it). So instead, each frame before the objects are drawn, a hero on this stage who isn't shrunk and is
# level with the mouth (level rows 20-30) is kept right of the wall's face (level x >= 1063, where he stands
# against an ordinary wall). Level coordinates: x = (x field - 0x4000) / 128 + the camera's x (0x10021A),
# y = -(y field / 128 + the camera's y (0x10020E)), 16-px cells. (0x10021A / 0x10020E, not the camera's 0x100216 /
# 0x10020A: those are the same until a respawn, which can move their origin - 1024 px over and up after dying by the
# wall - while these stay the level's own.) (Not the scroll values the collision lookup
# 0xD9B6 uses, 0x10022E / 0x100222: those are the camera within the 512-px window the level map wraps around
# in VRAM, so the same cell numbers come round again every 512 px - the first version used them and also
# clamped the hero at a cliff further on.)
ENABLED = False              # (switched off 2026-10-21, the user: it hid the secret too well - big Blue may stand in
                             # the mouths again. The code's still placed, so nothing after it moves; just not called.)
DRAW_FRONT_CALL = 0x11804    # jsr 0xA3A6 - the gameplay loop's front object group
DRAW_FRONT = 0xA3A6
HERO_CODE = 0x3BD10
STAGE = 4
ZONES = [   # (level rows top, bottom; x left, the face x)
    (20, 30, 1012, 1063),    # the tunnel's mouth (cells (65, 23-24))
    (38, 40, 1250, 1319),    # a second mouth over the water (cells (80-81, 37-38); the face at x 1312;
]                            # sta/aes/pocket_moss.sta)
ZONE_SRC = "    move.w (%a0),%d0                 | level with mouth ZI,\n    lsr.w #7,%d0\n    add.w 0x10020E,%d0\n    neg.w %d0\n    lsr.w #4,%d0\n    cmp.w #ROW_TOP,%d0\n    bcs 7ZIf\n    cmp.w #ROW_BOTTOM,%d0\n    bhi 7ZIf\n    move.w 2(%a0),%d0                | and left of the wall's face?\n    sub.w #0x4000,%d0\n    lsr.w #7,%d0\n    add.w 0x10021A,%d0\n    cmp.w #X_LEFT,%d0\n    bcs 7ZIf\n    cmp.w #X_FACE,%d0\n    bcc 7ZIf\n    move.w #X_FACE,%d0               | then at the face\n    sub.w 0x10021A,%d0\n    lsl.w #7,%d0\n    add.w #0x4000,%d0\n    move.w %d0,2(%a0)\n    rts\n7ZI:\n"


def apply(rom):
    src = r"""
clamp:
    cmp.b #STAGE,0x103005
    bne 9f
    movem.l %d0-%d1/%a0-%a1,-(%sp)
    lea 0x104000,%a0
    lea 0x107000,%a1
    bsr 1f
    lea 0x104080,%a0
    lea 0x107400,%a1
    bsr 1f
    movem.l (%sp)+,%d0-%d1/%a0-%a1
9:  jmp DRAW_FRONT

1:  cmp.l #HERO_CODE,4(%a0)          | a hero,
    bne 8f
    tst.b 1(%a1)                     | not shrunk (form 0 fits the tunnel),
    beq 8f
ZONES_CODE
8:  rts
"""
    zones = ""
    for i, (top, bottom, left, face) in enumerate(ZONES):
        z = ZONE_SRC
        for k, v in (("ROW_BOTTOM", bottom), ("ROW_TOP", top), ("X_LEFT", left), ("X_FACE", face), ("ZI", i)):
            z = z.replace(k, str(v))
        zones += z
    src = src.replace("ZONES_CODE", zones)
    for k, v in (("DRAW_FRONT", "0x%X" % DRAW_FRONT), ("HERO_CODE", "0x%X" % HERO_CODE), ("STAGE", str(STAGE))):
        src = src.replace(k, v)
    at = rom.place_code(src, why="Lower Earth Empire 2: keep the hero out of the wall at the tunnel's mouth")
    if not ENABLED:
        return
    rom.write(DRAW_FRONT_CALL, bytes.fromhex("4EB9") + at.to_bytes(4, "big"),
              expect=bytes.fromhex("4EB90000A3A6"), why="before drawing: keep the hero out of the wall pocket")
