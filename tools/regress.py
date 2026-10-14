#!/usr/bin/env python3
"""Regression run: build the hack, play every AES save and every recorded test, and compare what's on screen with
the last accepted run.

    python3 tools/regress.py                  build, run every save in sta/aes and every test in tests/clips.txt
    python3 tools/regress.py lava round_clear just those (a save's name or a test's)
    python3 tools/regress.py --accept         make this run the new baseline (after checking what changed)
    python3 tools/regress.py --no-build       use the build that's there

Each save is played headless (tools/regress.lua: idle, walk right, jump twice, attack) with snapshots at frames 30,
150 and 300 - a crash check where it was saved. Each test (tests/clips.txt) replays its recorded clip from its save,
with a snapshot every half second until the clip ends - the thing it was recorded to show. A run fails when the game
faults, stops looping, errors in Lua or never finishes; it has changed when a snapshot differs from the baseline's.
Changed ones get a side-by-side picture (baseline | now | the differing pixels in red) in build/regress/diff/, and
build/regress/index.html shows the run: problems and changes first, then everything's snapshots. MAME's settings for
these runs live in build/regress/cfg, apart from yours.

A save made with an older build can fault under a newer one without anything being wrong: it holds return addresses
and code pointers into the patches' new code, which moves when an earlier patch's code grows. Run such a save on the
build it was made with (a git worktree of that day's commit) before calling it a bug, and make it again if so.
"""
import argparse
import html
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from png_tiles import read_rgba, write_rgb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SAVES = ROOT / "sta" / "aes"
CLIPS, RECORDINGS = ROOT / "tests" / "clips.txt", ROOT / "tests" / "clips"
OUT = ROOT / "build" / "regress"
FRAMES = 300                     # (a save alone: as tools/regress.lua plays it)
TIMEOUT = 300                    # seconds a run may take (a save alone ~10, a clip about its length / 10)


def clips():
    """The recorded tests: {name: (save, what it shows)}."""
    tests = {}
    for line in CLIPS.read_text().splitlines():
        if line.strip() and not line.startswith("#"):
            name, save, what = line.split(None, 2)
            tests[name] = (save, what)
    return tests


def build():
    """Build the hack; the lines that aren't the usual patch log (warnings) come back."""
    run = subprocess.run([sys.executable, "tools/hackbuild.py"], cwd=ROOT, capture_output=True, text=True)
    log = (run.stdout + run.stderr).splitlines()
    if run.returncode or not any(line.startswith("Built build/aes/") for line in log):
        print("\n".join(log[-20:]))
        sys.exit("build failed")
    return [line for line in log if not line.startswith(("  ", "* ", "Applying ", "Built "))]


def play(name, save, clip, now):
    """Play a save (and a clip, if it's a test); its snapshots and report go to now/name."""
    out = now / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    if clip and not (RECORDINGS / (clip + ".inp")).exists():
        return name, ["no recording (tests/clips/%s.inp)" % clip]
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", REGRESS_REPORT=str(out / "report.txt"),
               REGRESS_CLIP="1" if clip else "0")
    cmd = ["mame", "aes", "-hash", "build/aes", "-rompath", "build/aes", "-cart", "bjourney", "-state", save,
           "-window", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-noautosave",
           "-cfg_directory", str(OUT / "cfg"), "-nvram_directory", str(OUT / "nvram"),
           "-snapshot_directory", str(out), "-snapname", "%i", "-autoboot_script", "tools/regress.lua"]
    if clip:
        cmd += ["-input_directory", str(RECORDINGS), "-playback", clip + ".inp", "-exit_after_playback"]
    try:
        subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return name, ["never finished (%d s)" % TIMEOUT]
    report = out / "report.txt"
    if not report.exists():
        return name, ["no report (the save didn't load?)"]
    fields = dict((line + " ").split(" ", 1) for line in report.read_text().splitlines())
    problems = []
    if "error" in fields:
        problems.append("Lua error: " + fields["error"])
    if not clip and int(fields["frames"]) < FRAMES:
        problems.append("stopped at frame " + fields["frames"].strip())
    if int(fields["faults"]):
        problems.append("faulted (%s frames in the exception handlers)" % fields["faults"].strip())
    if int(fields["stuck"]):
        problems.append("stuck at 0x" + fields["last_pc"].strip())
    if int(fields["bios"]) > 30:
        problems.append("in the BIOS for %s frames (a reset?)" % fields["bios"].strip())
    for i, f in enumerate(fields["snaps"].split()):
        snap = out / ("%04d.png" % i)
        if snap.exists():
            snap.rename(out / ("f%04d.png" % int(f)))
        else:
            problems.append("no snapshot at frame %s" % f)
    return name, problems


def snapshots(folder):
    return sorted(p.name for p in folder.glob("f*.png"))


def compare(name, now, base, diffs):
    """The snapshots that differ from the baseline's, as (frame, pixels; -1: only in one of them), each pictured into
    diffs; None if there's no baseline."""
    if not (base / name).exists():
        return None
    changed = []
    for snap in sorted(set(snapshots(base / name)) | set(snapshots(now / name))):
        a, b, f = base / name / snap, now / name / snap, int(snap[1:-4])
        if not (a.exists() and b.exists()):
            changed.append((f, -1))
            continue
        if a.read_bytes() == b.read_bytes():
            continue
        old, new = read_rgba(a), read_rgba(b)
        marks = [[o != n for (o, _), (n, _) in zip(ro, rn)] for ro, rn in zip(old, new)]
        count = sum(map(sum, marks))
        if count:
            changed.append((f, count))
            write_rgb(diffs / ("%s_f%04d.png" % (name, f)),
                      [[o for o, _ in ro] + [n for n, _ in rn] +
                       [(255, 0, 0) if m else tuple(v // 3 for v in n) for (n, _), m in zip(rn, rm)]
                       for ro, rn, rm in zip(old, new, marks)])
    return changed


def describe(diff):
    return ["frame %d %s" % (f, "only in one run" if n < 0 else "changed: %d px" % n) for f, n in diff]


def page(names, results, diffs, tests):
    """build/regress/index.html: the runs with problems or changes first, then the rest, with their snapshots."""
    def row(name):
        problems, diff = results[name], diffs[name]
        notes = list(problems) + (["new"] if diff is None else describe(diff))
        pics = "".join('<img src="now/%s/%s">' % (name, snap) for snap in snapshots(OUT / "now" / name))
        pics += "".join('<br><img src="diff/%s_f%04d.png" title="baseline | now | changed">' % (name, f)
                        for f, n in diff or [] if n > 0)
        title = name + (" - test from %s: %s" % tests[name] if name in tests else "")
        return '<section class="%s"><h2>%s</h2><p>%s</p>%s</section>' % (
            "bad" if problems else "changed" if diff else "", html.escape(title),
            html.escape("; ".join(notes) or "the same"), pics)
    first = [n for n in names if results[n] or diffs[n]]
    body = "".join(row(n) for n in first + [n for n in names if n not in first])
    (OUT / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Regression run</title><style>'
        "body{font:14px sans-serif;background:#222;color:#ddd;margin:16px} img{margin:2px;image-rendering:pixelated}"
        "section{margin-bottom:20px} h2{margin:0;font-size:16px} p{margin:2px 0}"
        ".bad h2{color:#f66} .changed h2{color:#fc6}</style>" + body)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("names", nargs="*", help="saves' or tests' names (default: all of them)")
    ap.add_argument("--accept", action="store_true", help="make this run the new baseline")
    ap.add_argument("--no-build", action="store_true", help="don't rebuild first")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    args = ap.parse_args()

    tests = clips()
    saves = sorted(p.stem for p in SAVES.glob("*.sta"))
    names = args.names or saves + sorted(tests)
    missing = [n for n in names if n not in tests and n not in saves]
    if missing:
        sys.exit("no such save or test: " + ", ".join(missing))
    runs = [(n,) + ((tests[n][0], n) if n in tests else (n, None)) for n in names]
    warnings = [] if args.no_build else build()

    now, base, diffs = OUT / "now", OUT / "baseline", OUT / "diff"
    shutil.rmtree(diffs, ignore_errors=True)
    diffs.mkdir(parents=True)
    with ThreadPoolExecutor(args.jobs) as pool:
        results = dict(pool.map(lambda run: play(*run, now), runs))

    lines, failed, changed, new, compared = [], 0, 0, [], {}
    for name in names:
        problems = results[name]
        diff = compared[name] = compare(name, now, base, diffs)
        if problems:
            failed += 1
            lines.append("FAIL     %-24s %s" % (name, "; ".join(problems)))
        if diff is None:
            new.append(name)
        elif diff:
            changed += 1
            lines.append("changed  %-24s %s" % (name, ", ".join(describe(diff))))
    if new:
        lines.append("new      " + ", ".join(new))
    for w in warnings:
        lines.insert(0, "build    " + w)
    lines.append("%d runs: %d failed, %d changed, %d new, %d the same" %
                 (len(names), failed, changed, len(new), len(names) - changed - len(new)))
    print("\n".join(lines))
    (OUT / "report.txt").write_text("\n".join(lines) + "\n")
    page(names, results, compared, tests)
    print("the run, to look through: " + str((OUT / "index.html").relative_to(ROOT)))

    if args.accept:
        for name in names:
            shutil.rmtree(base / name, ignore_errors=True)
            shutil.copytree(now / name, base / name)
        print("accepted as the baseline")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
