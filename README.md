# Blue's Journey Plus

Blue's Journey (Alpha Denshi, 1990) is one of the Neo Geo's most charming platformers - and one of its roughest:
a stiff little hero, a translation that loses the story's warmth, countdowns everywhere, and a few bugs. Blue's
Journey Plus is a romhack that keeps the game you remember and smooths out the rougher details: a bigger, redrawn Blue, a pause
menu, a cleaner HUD, a retranslated script, smoother scenery and a few new secrets.

It's an update to the **home console (AES) experience** - that's the version it's made and tested for. Started in
arcade (MVS) mode, it shows a message asking for AES mode instead of running.

**Status: Beta 1.** Get it from the [itch.io page](https://powerwindows.itch.io/blues-journey-plus). Feedback welcome: open an issue here, or leave a
comment on the itch.io page.

## What's changed

**Blue**
- Blue is drawn with his big, detailed artwork all the time - redrawn throws, idle, ocarina, swimming, climbing,
  carrying.
- Shrunk (mini) Blue can run while holding A.

**Controls and pause**
- Start opens the in-game pause menu: RESUME, RESTART LEVEL, QUIT TO TITLE. Select hides it for a clean pause screen.
- D switches between the weapons you've collected.

**Weapons**
- Boomerang: level 2 throws two at once, level 3 throws three, with every third one bigger, and it always comes back to Blue.
- Acorn bomb level 3: a quick second throw. 
- Leaf level 2 and 3 have updated animations.
- Points pop up for enemies killed while invincible, and for collecting 1UPs and snacks.

**Screens and HUD**
- Boots straight to the title; a title menu with NEW GAME and OPTIONS (level select, difficulty, a sound test with
  named tracks).
- A redesigned HUD during gameplay is more organized and minimal so you can focus on the game, and stays inside a
  real TV's picture.
- Screen transitions have been cleaned to not show brief graphic cycling, and iris transitions added to start of level.
- In two-player games, the CONTINUE? prompt sits cleanly over the HUD.

**Text**
- The script retranslated with the Japanese as a guide, typos fixed - fan favorites like LEAF DUMP kept; NPCs'
  personalities restored, item descriptions fixed.

**Rules and timers**
- No countdowns in the shop, the houses, the card game or the lottery.
- Losing a life keeps your flowers and items. A continue restarts the level from its beginning (boss fights
  excepted).
- Three hearts to start on the easiest three difficulty levels; boss hits scale with the difficulty.
- Shop prices charged now match the prices shown.

**Levels**
- Smoother wheels, conveyors and elevators; a faster zipline; drowning and lava shown in front of the water line;
  the goal's bells rock and sparkle.
- Water reflections (the sunken Ferris wheels too); drifting clouds and a PLUS banner on the title; baddies watching
  the final fight from the balcony.
- A few new secrets.

## Playing it

You need your own copy of the MAME ROM set **bjourney** (Blue's Journey / Raguy). No game data is included here.

**The easy way:** the patcher on the [itch.io page](https://powerwindows.itch.io/blues-journey-plus) runs in your browser (your files are never uploaded).
Drop in `bjourney.zip` or a Darksoft-style `bjourney` folder, pick RetroArch, MAME, BackBit Platinum, MiSTer or
Analogue Pocket, and download a zip laid out for that system, with a README of where it goes and which settings to
use.

**By hand:** the xdelta download (on the itch.io page) has a patch per file, the original files' checksums and the
same per-system steps. The patches change these files of the set; check yours match before patching:

| File | Size | CRC32 | SHA-1 |
|---|---|---|---|
| 022-p1.p1 | 1048576 | 6a2f6d4a | b8ca548e56f1c7abcdce415ba7329e0cf698ee13 |
| 022-s1.s1 | 131072 | 843c3624 | dbdf86c193b7c1d795f8c21f2c103c1d3e18abbe |
| 022-m1.m1 | 131072 | 8e1d4ab6 | deabc11ab81e7e68a3e041c03a127ae28d0d7264 |
| 022-c1.c1 | 1048576 | 4d47a48c | 6e282285be72583d828e7765b1c1695ecdc44777 |
| 022-c2.c2 | 1048576 | e8c1491a | c468d2556b3de095aaa05edd1bc16d71303e9478 |
| 022-c3.c3 | 524288 | 66e69753 | 974b823fc62236fbc23e727f25b61a805a707a9e |
| 022-c4.c4 | 524288 | 71bfd48a | 47288be69e6992d09ebef108b4de9ffab6293dc8 |

Play it as the Neo Geo **AES** (home console): in MAME, `mame aes -cart bjourney`; elsewhere, set the emulator's or
cart's Neo Geo mode / BIOS to AES.

**Tested on:** a real Neo Geo on a CRT (BackBit Platinum), RetroArch FinalBurn Neo on a Retroid Pocket, the Analogue
Pocket, and MAME on macOS. MiSTer should work but is untested - reports welcome.

## Building from source

You need Python 3, [ngdevkit](https://github.com/dciabrin/ngdevkit)'s `m68k-neogeo-elf` toolchain, and MAME.

1. Put the MAME set `bjourney.zip` and the BIOS `neogeo.zip` in `roms/` (and `aes.zip`, ngdevkit's open AES BIOS,
   for the home version).
2. `./run.sh` builds `build/` from `patches/*.py` and plays it in MAME as the AES. `python3 tools/hackbuild.py` just
   builds.

- `patches/` - one file per change, applied in name order; each starts with what it does and how (the game's
  addresses, what was found). `patches/pins.json` keeps each patch's code at a fixed address.
- `tools/hackbuild.py` - the build. `tools/regress.py` plays every test clip and save headless and compares the
  screens with the last accepted run (`tests/clips.txt`). `tools/release.py` makes the release files: the web
  patcher (`tools/web_patcher/`), the xdelta patches and each system's package.
- `art/` - redrawn graphics the patches read. `docs/` - notes on the game's internals.

## Credits

Blue's Journey Plus by Loren Vanderbilt III. Blue's Journey © 1990 Alpha Denshi / SNK - no game data is included;
you need your own copy.
