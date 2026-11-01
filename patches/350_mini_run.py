NAME = "mini-run"
DESCRIPTION = "Mini Blue runs faster while A is held (he can't attack as mini; A just stopped him)"

# Mini Blue (form 0 at player block +0x01; 1 is normal, 2 big) can't attack, but pressing A still stopped him. While
# walking (state 1, 0x3EB44), 0x44B58 reports an attack and he takes the attack path at 0x3EC2E, which clears his
# speed and starts a throw a mini can't make.
#
# When mini with A held:
#   * the walk carries on instead (ATTACK_CHECK);
#   * his walking speed is RUN_SPEED instead of 200 (MINI_SPEED). Speeds come from 0x427F4 by form, in 1/128 px a
#     frame: mini 200, normal and big 160, with the fern's 1.25x on top.
# Otherwise everything is as before.
ATTACK_CHECK = 0x3EB8A       # jsr 0x44B58 (pc-relative) ; bne.w 0x3EC2E
WALK_ON, STOP = 0x3EB92, 0x3EC2E
ATTACK_PRESSED = 0x44B58
MINI_SPEED = 0x4280E
RUN_SPEED = 300              # 1.5x mini's walk
HEROES = [(0x104000, 0x107000, 0x10FD96), (0x104080, 0x107400, 0x10FD9C)]   # hero, player block, buttons (bit 4 = A)


def apply(rom):
    # d0 = 1 if this hero (a5) is mini with A held, else 0, with the flags set from it
    test = "".join("    cmpa.l #0x%X,%%a5\n    bne 1f\n    tst.b 0x%X\n    bne 8f\n    btst #4,0x%X\n    bne 7f\n"
                   "    bra 8f\n1:\n" % (hero, block + 1, buttons) for hero, block, buttons in HEROES)
    code = rom.place_code(r"""
    bra.w attack_check
    bra.w mini_speed

running:                                | d0 = 1: this hero (a5) is mini with A held
%(test)s8:  moveq #0,%%d0
    rts
7:  moveq #1,%%d0
    rts

attack_check:
    jsr 0x%(pressed)X
    beq 1f
    bsr running                         | an attack, unless a mini with A held runs on
    bne 1f
    jmp 0x%(stop)X
1:  jmp 0x%(walk_on)X

mini_speed:
    lea 0x4C7DA,%%a0
    bsr running
    beq 1f
    move.w #%(run)d,%%d0
    rts
1:  move.w #200,%%d0
    rts
""" % {"test": test, "pressed": ATTACK_PRESSED, "stop": STOP, "walk_on": WALK_ON, "run": RUN_SPEED},
        why="mini Blue: A held runs")
    rom.write(ATTACK_CHECK, bytes.fromhex("4EF9") + code.to_bytes(4, "big") + bytes.fromhex("4E71"),
              expect=bytes.fromhex("4EBA5FCC6600009E"), why="walking with A: a mini with A held walks on")
    rom.write(MINI_SPEED, bytes.fromhex("4EB9") + (code + 4).to_bytes(4, "big") + bytes.fromhex("4E714E71"),
              expect=bytes.fromhex("303C00C841F90004C7DA"), why="mini's walking speed: RUN_SPEED with A held")
