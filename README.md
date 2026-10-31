# Blue's Journey Plus

Blue's Journey (Alpha Denshi, 1990) is one of the Neo Geo's most charming platformers - and one of its roughest:
a stiff little hero, a translation that loses the story's warmth, countdowns everywhere, and a few bugs. Blue's
Journey Plus is a romhack that keeps the game you remember and smooths out the rougher details: a bigger, redrawn Blue, a pause
menu, a cleaner HUD, a retranslated script, smoother scenery and a few new secrets.

It's an update to the **home (AES) experience** - that's the version it's made and tested for. (The build also writes
an arcade (MVS) set with the gameplay changes, but it isn't a supported way to play.)

**Status: beta.** Feedback welcome, please submit via the Issues tab of this repo.

## What's changed

**Blue**
- Blue is drawn with his big, detailed artwork all the time - redrawn throws, idle, ocarina, swimming, climbing,
  carrying.
- Shrunk (mini) Blue can run while holding A.

**Controls and pause**
- Pressing Start opens the in-game pause menu: RESUME, RESTART LEVEL, QUIT TO TITLE. Select hides it for a clean pause screen.
- D switches between the weapons you've collected.

**Weapons**
- Boomerang: level 2 throws two at once, level 3 throws three, with every third one bigger, and it always comes back to Blue.
- Acorn bomb level 3: a quick second throw. 
- Leaf level 2 and 3 have updated animations.
- Points pop up for enemies killed while invincible, and for collecting 1UPs and snacks.

**Screens and HUD**
- Boots straight to the title; a title menu with NEW GAME and OPTIONS.
- A redesigned HUD during gameplay is more organized and minimal so you can focus on the game.
- Screen transitions have been cleaned to not show brief graphic cycling, and iris transitions added to start of level.

**Text**
- The script retranslated with the Japanese as a guide, typos fixed - fan favorites like LEAF DUMP kept.

**Rules and timers**
- No countdowns in the shop, the houses, the card game or the lottery.
- Losing a life keeps your flowers and items. A continue restarts the level from its beginning (boss fights
  excepted).
- Three hearts to start on the easiest three difficulty levels; boss hits scale with the difficulty.
- Shop prices charged now match the prices shown.

**Levels**
- Smoother wheels, conveyors and elevators; a faster zipline; drowning and lava shown in front of the water line;
  the goal's bells rock and sparkle.
- A few new secrets.

## Playing it

You need the MAME ROM set **bjourney** (Blue's Journey / Raguy) and the patch files. The patches change these
files of the set; check yours match before patching:

| File | Size | CRC32 | SHA-1 |
|---|---|---|---|
| 022-p1.p1 | 1048576 | 6a2f6d4a | b8ca548e56f1c7abcdce415ba7329e0cf698ee13 |
| 022-s1.s1 | 131072 | 843c3624 | dbdf86c193b7c1d795f8c21f2c103c1d3e18abbe |
| 022-m1.m1 | 131072 | 8e1d4ab6 | deabc11ab81e7e68a3e041c03a127ae28d0d7264 |
| 022-c1.c1 | 1048576 | 4d47a48c | 6e282285be72583d828e7765b1c1695ecdc44777 |
| 022-c2.c2 | 1048576 | e8c1491a | c468d2556b3de095aaa05edd1bc16d71303e9478 |
| 022-c3.c3 | 524288 | 66e69753 | 974b823fc62236fbc23e727f25b61a805a707a9e |
| 022-c4.c4 | 524288 | 71bfd48a | 47288be69e6992d09ebef108b4de9ffab6293dc8 |

1. Unzip `bjourney.zip` into a folder.
2. Apply each patch file to the ROM file it's named after (with an xdelta patcher, e.g. Delta Patcher or `xdelta3`).
3. Zip the files back up as `bjourney.zip` and play it as the Neo Geo **AES** (home console) - e.g. in MAME,
   `mame aes -cart bjourney`, or set your emulator's Neo Geo BIOS to AES / home.

**Tested on:** MAME on macOS (where it was developed), and RetroArch on Android (Retroid Pocket Nova). Real hardware
testing on a CRT is next.

## Building from source

You need Python 3, [ngdevkit](https://github.com/dciabrin/ngdevkit)'s `m68k-neogeo-elf` toolchain, and MAME.

1. Put the MAME set `bjourney.zip` and the BIOS `neogeo.zip` in `roms/` (and `aes.zip`, ngdevkit's open AES BIOS,
   for the home version).
2. `./run.sh` builds `build/` from `patches/*.py` and plays it in MAME as the AES. `python3 tools/hackbuild.py` just
   builds.

- `patches/` - one file per change, applied in name order; each starts with what it does and how (the game's
  addresses, what was found). `patches/pins.json` keeps each patch's code at a fixed address.
- `tools/hackbuild.py` - the build. `tools/regress.py` plays every test clip and save headless and compares the
  screens with the last accepted run (`tests/clips.txt`).
- `art/` - redrawn graphics the patches read. `docs/` - notes on the game's internals.

`TODO.md` is the working list: what's done, what's next, and what was tried and dropped.

## Credits

Blue's Journey Plus by Loren Vanderbilt III. Blue's Journey © 1990 Alpha Denshi / SNK - no game data is included;
you need your own copy.
