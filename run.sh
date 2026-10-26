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
# Controls (MAME defaults): 1 = Start, 5 = Select (AES) / insert coin (MVS), arrows = move,
# Left Ctrl/Alt/Space/Shift = A/B/C/D, Tab = MAME menu, Esc = quit.
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
python3 tools/hackbuild.py $build_args || exit 1
out=build
states=""
[ -n "$ORIGINAL" ] && { out=build/original; states="-state_directory sta_original"; }   # (its saves apart from the hack's)
mkdir -p recordings
if [ "$mode" = aes ]; then
    [ -f $out/aes/neogeo.xml ] || { echo "No AES build (need roms/aes.zip) - use --mvs, or see tools/hackbuild.py"; exit 1; }
    script=""
    [ -n "$DIFFICULTY" ] && { export HACK_DIFFICULTY="$DIFFICULTY"; script="-autoboot_script tools/difficulty.lua"; }
    exec mame aes -hash $out/aes -rompath $out/aes -cart bjourney $states $bios $script -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
fi
exec mame bjourney -rompath $out/roms $states $bios -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
