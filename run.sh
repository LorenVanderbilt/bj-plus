#!/bin/sh
# Build the patched ROM set and play it in MAME.
#   ./run.sh                          all patches
#   ./run.sh --only anim-speed        just that patch
#   ./run.sh --skip anim-speed        everything except that patch (--skip every patch = the original game)
#   ./run.sh [patch options] -- [MAME options]     anything after -- goes to MAME
# To record a play session so it can be replayed exactly later (saved to recordings/NAME.inp):
#   ./run.sh --skip anim-speed -- -record NAME.inp
# Controls: 5 = insert coin, 1 = 1P start, arrows = move, Left Ctrl/Alt/Space/Shift = A/B/C/D,
# Tab = MAME menu, Esc = quit.
cd "$(dirname "$0")" || exit 1
build_args=""
while [ $# -gt 0 ] && [ "$1" != "--" ]; do build_args="$build_args $1"; shift; done
[ "$1" = "--" ] && shift
python3 tools/hackbuild.py $build_args || exit 1
mkdir -p recordings
exec mame bjourney -rompath build/roms -input_directory recordings -window -skip_gameinfo -nowaitvsync "$@"
