#!/bin/sh
# Build the patched ROM set and play it in MAME. Usage: ./run.sh [hackbuild.py options]
#   ./run.sh                   all patches
#   ./run.sh --only anim-speed just that patch
#   ./run.sh --skip anim-speed everything except that patch
# Controls: 5 = insert coin, 1 = 1P start, arrows = move, Left Ctrl/Alt/Space/Shift = A/B/C/D,
# Tab = MAME menu, Esc = quit.
cd "$(dirname "$0")" || exit 1
python3 tools/hackbuild.py "$@" || exit 1
exec mame bjourney -rompath build/roms -window -skip_gameinfo -nowaitvsync
