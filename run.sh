#!/bin/sh
# Build the patched ROM set and play it in MAME - as the AES home console by default.
#   ./run.sh                          AES (home console) mode, all patches
#   ./run.sh --mvs                    arcade (MVS) mode instead (coin = 5, start = 1)
#   ./run.sh --only anim-speed        just that patch
#   ./run.sh --skip anim-speed        everything except that patch (--skip every patch = the original game)
#   ./run.sh [options] -- [MAME options]     anything after -- goes to MAME
# To record a play session so it can be replayed exactly later (saved to recordings/NAME.inp):
#   ./run.sh --mvs --skip anim-speed hero-big-art -- -record NAME.inp     (recordings are mode-specific)
# Controls (MAME defaults): 1 = Start, 5 = Select (AES) / insert coin (MVS), arrows = move,
# Left Ctrl/Alt/Space/Shift = A/B/C/D, Tab = MAME menu, Esc = quit.
cd "$(dirname "$0")" || exit 1
mode=aes
build_args=""
while [ $# -gt 0 ] && [ "$1" != "--" ]; do
    case "$1" in
        --mvs) mode=mvs ;;
        --aes) mode=aes ;;
        *) build_args="$build_args $1" ;;
    esac
    shift
done
[ "$1" = "--" ] && shift
python3 tools/hackbuild.py $build_args || exit 1
mkdir -p recordings
if [ "$mode" = aes ]; then
    [ -f build/aes/neogeo.xml ] || { echo "No AES build (need roms/aes.zip) - use --mvs, or see tools/hackbuild.py"; exit 1; }
    exec mame aes -hash build/aes -rompath build/aes -cart bjourney -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
fi
exec mame bjourney -rompath build/roms -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
