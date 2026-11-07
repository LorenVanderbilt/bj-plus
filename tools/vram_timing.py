#!/usr/bin/env python3
"""Find VRAM accesses made faster than the real console allows: replay the recorded tests and list who makes them.

    python3 tools/vram_timing.py                 build, then replay every test in tests/clips.txt
    python3 tools/vram_timing.py shop_flippers   just those tests
    python3 tools/vram_timing.py --no-build      use the build that's there

The LSPC needs time between VRAM accesses (SNK's minimums, from the NeoGeo Dev Wiki's VRAM page): about 16 CPU
cycles from setting REG_VRAMADDR (0x3C0000) to reading REG_VRAMRW (0x3C0002), 16 from a data write to setting a new
address, and 12 between data writes. Faster, and the console reads stale data or drops the access - glitches that
come and go. MAME and FBNeo don't enforce it.

The gaps are measured in MAME, so they're approximate. The original game works on the console, so its own shortest
gaps are listed too: a patch's gap no shorter than the game's is likely fine.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import palette_timing as pt  # noqa: E402

OUT = pt.ROOT / "build" / "vram_timing"


def play(name, save):
    out = OUT / (name + ".txt")
    out.unlink(missing_ok=True)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", VRAM_TIMING_OUT=str(out))
    subprocess.run(["mame", "aes", "-hash", "build/aes", "-rompath", "build/aes", "-cart", "bjourney", "-state", save,
                    "-window", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-noautosave",
                    "-cfg_directory", str(OUT / "cfg"), "-nvram_directory", str(OUT / "nvram"),
                    "-input_directory", "tests/clips", "-playback", name + ".inp", "-exit_after_playback",
                    "-autoboot_script", "tools/vram_timing.lua"], cwd=pt.ROOT, env=env, capture_output=True)
    return name, out.read_text().splitlines() if out.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="tests' names (default: all of them)")
    ap.add_argument("--no-build", action="store_true", help="don't rebuild first")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    args = ap.parse_args()

    tests = {}
    for line in (pt.ROOT / "tests" / "clips.txt").read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, save = line.split()[:2]
            if (pt.ROOT / "tests" / "clips" / (name + ".inp")).exists():
                tests[name] = save
    names = args.names or sorted(tests)
    missing = [n for n in names if n not in tests]
    if missing:
        sys.exit("no such test: " + ", ".join(missing))
    OUT.mkdir(parents=True, exist_ok=True)
    pt.OUT.mkdir(parents=True, exist_ok=True)
    if not args.no_build or not (pt.OUT / "build.log").exists():
        pt.build()
    blocks = pt.code_blocks()

    found, failed = {}, []           # (kind, pc) -> [count, shortest gap, tests]
    with ThreadPoolExecutor(args.jobs) as pool:
        for name, lines in pool.map(lambda n: play(n, tests[n]), names):
            if lines is None:
                failed.append(name)
                continue
            for line in lines:
                kind, pc, n, least = line.split()
                f = found.setdefault((kind, int(pc, 16)), [0, 999.0, set()])
                f[0] += int(n)
                f[1] = min(f[1], float(least))
                f[2].add(name)

    game = {}
    for (kind, pc), (n, least, where) in found.items():
        if pc < pt.ORIGINAL_END:
            game[kind] = min(game.get(kind, 999.0), least)
    print("the game's own shortest gaps (cycles): " + ", ".join("%s %.0f" % kv for kv in sorted(game.items())))
    ours = sorted(((kind, pc), v) for (kind, pc), v in found.items() if pc >= pt.ORIGINAL_END)
    for (kind, pc), (n, least, where) in ours:
        what = next((why for at, size, why in blocks if at <= pc < at + size), "?")
        flag = "" if least >= game.get(kind, 0) else "  SHORTER THAN THE GAME'S"
        print("%06X  %-18s %7d times, shortest %3.0f cycles%s  %s" % (pc, kind, n, least, flag, what))
        print("        in: " + ", ".join(sorted(where)[:8]) + (" ..." if len(where) > 8 else ""))
    print("%d tests, %d of our places too fast%s" % (
        len(names) - len(failed), len(ours), "; no log from: " + ", ".join(failed) if failed else ""))
    return 1 if ours or failed else 0


if __name__ == "__main__":
    sys.exit(main())
