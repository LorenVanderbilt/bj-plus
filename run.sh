#!/bin/sh
# Build the patched ROM set and play it in MAME - as the AES home console by default.
#   ./run.sh                          AES (home console) mode, all patches
#   ./run.sh --mvs                    arcade (MVS) mode instead (coin = 5, start = 1)
#   ./run.sh --bios unibios40         use a different BIOS: AES machine: asia (default), japan, devel, unibios40, unibios33 ...
#                                     arcade machine (--mvs): euro (default), us, japan, unibios40 ...
#   ./run.sh --only anim-speed        just that patch
#   ./run.sh --skip anim-speed        everything except that patch (--skip every patch = the original game)
#   ./run.sh --difficulty 1           start at that difficulty (LEVEL 1-8; AES only - as if picked in OPTIONS)
#   ./run.sh --original               the ORIGINAL game plus a stage select on the title (Up / Down) - for
#                                     before-and-after footage (build/original/; its saves go in sta_original/)
#   ./run.sh [options] -- [MAME options]     anything after -- goes to MAME
# Personal defaults go in local.cfg (not committed), a shell file, e.g.:  DIFFICULTY=1
# To record a play session so it can be replayed exactly later (saved to recordings/NAME.inp):
#   ./run.sh --mvs --skip anim-speed hero-big-art -- -record NAME.inp     (recordings are mode-specific)
# Controls: 1 = Start, 5 = Select (AES) / insert coin (MVS), arrows = move, Z/X/C/V = A/B/C/D (the shared
# ../neogeo-notes/tools/mame/neogeo-keys.cfg: macOS takes Ctrl+arrows), Tab = MAME menu, Esc = quit.
# M = save for Claude (sta/aes/new_01.sta, new_02 ... - ../neogeo-notes/tools/mame/savekey.lua), Shift+F7 = MAME's own save.
# A remap saved from MAME's Tab menu (cfg/aes.cfg) overrides neogeo-keys.cfg.
cd "$(dirname "$0")" || exit 1
mode=aes
bios=""
build_args=""
DIFFICULTY=""
ORIGINAL=""
[ -f local.cfg ] && . ./local.cfg
while [ $# -gt 0 ] && [ "$1" != "--" ]; do
    case "$1" in
        --mvs) mode=mvs ;;
        --aes) mode=aes ;;
        --bios) shift; bios="-bios $1" ;;
        --difficulty) shift; DIFFICULTY="$1" ;;
        --original) build_args="$build_args --original"; ORIGINAL=1 ;;
        *) build_args="$build_args $1" ;;
    esac
    shift
done
[ "$1" = "--" ] && shift
# MAME runs only one -autoboot_script: the save key, --difficulty's and any given after -- all go through run_scripts
scripts="../neogeo-notes/tools/mame/savekey.lua"
n=$#
while [ $n -gt 0 ]; do
    if [ "$1" = "-autoboot_script" ] && [ $n -gt 1 ]; then
        scripts="$scripts;$2"; shift 2; n=$((n - 2))
    else
        set -- "$@" "$1"; shift; n=$((n - 1))
    fi
done
python3 tools/hackbuild.py $build_args || exit 1
out=build
states=""
[ -n "$ORIGINAL" ] && { out=build/original; states="-state_directory sta_original"; }   # (its saves apart from the hack's)
mkdir -p recordings
keys="-ctrlrpath ../neogeo-notes/tools/mame -ctrlr neogeo-keys -autoboot_script tools/run_scripts.lua"
if [ "$mode" = aes ]; then
    [ -f $out/aes/neogeo.xml ] || { echo "No AES build (need roms/aes.zip) - use --mvs, or see tools/hackbuild.py"; exit 1; }
    [ -n "$DIFFICULTY" ] && { export HACK_DIFFICULTY="$DIFFICULTY"; scripts="$scripts;tools/difficulty.lua"; }
    export RUN_SCRIPTS="$scripts"
    exec mame aes -hash $out/aes -rompath $out/aes -cart bjourney $states $bios $keys -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
fi
export RUN_SCRIPTS="$scripts"
exec mame bjourney -rompath $out/roms $states $bios $keys -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
