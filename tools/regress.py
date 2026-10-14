#!/usr/bin/env python3
"""Regression run: build the hack, play every AES save for 5 seconds with the same input, and compare what's on
screen with the last accepted run.

    python3 tools/regress.py                  build, run every save in sta/aes, compare with the baseline
    python3 tools/regress.py lava quick       just those saves
    python3 tools/regress.py --accept         make this run the new baseline (after checking what changed)
    python3 tools/regress.py --no-build       use the build that's there

Each save is played headless (tools/regress.lua: idle, walk right, jump twice, attack) with snapshots at frames 30,
150 and 300. A save fails when the game faults, stops looping, errors in Lua or never finishes; it has changed when a
snapshot differs from the baseline's. Changed saves get a side-by-side picture (baseline | now | the differing pixels
in red) in build/regress/diff/, and build/regress/index.html shows the run: problems and changes first, then every
save's snapshots. MAME's settings for these runs live in build/regress/cfg, apart from yours.

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
OUT = ROOT / "build" / "regress"
FRAMES = (30, 150, 300)          # (as tools/regress.lua takes them)
TIMEOUT = 120                    # seconds a save may take (they take ~10)


def build():
    """Build the hack; the lines that aren't the usual patch log (warnings) come back."""
    run = subprocess.run([sys.executable, "tools/hackbuild.py"], cwd=ROOT, capture_output=True, text=True)
    log = (run.stdout + run.stderr).splitlines()
    if run.returncode or not any(line.startswith("Built build/aes/") for line in log):
        print("\n".join(log[-20:]))
        sys.exit("build failed")
    return [line for line in log if not line.startswith(("  ", "* ", "Applying ", "Built "))]


def play(name, now):
    """Play one save; its snapshots and report go to now/name."""
    out = now / name
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    env = dict(os.environ, SDL_VIDEODRIVER="dummy", SDL_AUDIODRIVER="dummy", REGRESS_REPORT=str(out / "report.txt"))
    cmd = ["mame", "aes", "-hash", "build/aes", "-rompath", "build/aes", "-cart", "bjourney", "-state", name,
           "-window", "-video", "none", "-sound", "none", "-nothrottle", "-skip_gameinfo", "-noautosave",
           "-cfg_directory", str(OUT / "cfg"), "-nvram_directory", str(OUT / "nvram"),
           "-snapshot_directory", str(out), "-snapname", "%i", "-autoboot_script", "tools/regress.lua"]
    try:
        subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, timeout=TIMEOUT)
    except subprocess.TimeoutExpired:
        return name, ["never finished (%d s)" % TIMEOUT]
    report = out / "report.txt"
    if not report.exists():
        return name, ["no report (the save didn't load?)"]
    fields = dict(line.split(" ", 1) for line in report.read_text().splitlines())
    problems = []
    if "error" in fields:
        problems.append("Lua error: " + fields["error"])
    if int(fields["frames"]) < FRAMES[-1]:
        problems.append("stopped at frame " + fields["frames"])
    if int(fields["faults"]):
        problems.append("faulted (%s frames in the exception handlers)" % fields["faults"])
    if int(fields["stuck"]):
        problems.append("stuck at 0x" + fields["last_pc"])
    if int(fields["bios"]) > 30:
        problems.append("in the BIOS for %s frames (a reset?)" % fields["bios"])
    for i, f in enumerate(FRAMES):
        snap = out / ("%04d.png" % i)
        if snap.exists():
            snap.rename(out / ("f%03d.png" % f))
        else:
            problems.append("no snapshot at frame %d" % f)
    return name, problems


def compare(name, now, base, diffs):
    """The frames whose snapshot differs from the baseline's (a picture of each into diffs), or None if new."""
    if not (base / name).exists():
        return None
    changed = []
    for f in FRAMES:
        a, b = base / name / ("f%03d.png" % f), now / name / ("f%03d.png" % f)
        if not (a.exists() and b.exists()):
            continue
        if a.read_bytes() == b.read_bytes():
            continue
        old, new = read_rgba(a), read_rgba(b)
        marks = [[o != n for (o, _), (n, _) in zip(ro, rn)] for ro, rn in zip(old, new)]
        count = sum(map(sum, marks))
        if count:
            changed.append((f, count))
            write_rgb(diffs / ("%s_f%03d.png" % (name, f)),
                      [[o for o, _ in ro] + [n for n, _ in rn] +
                       [(255, 0, 0) if m else tuple(v // 3 for v in n) for (n, _), m in zip(rn, rm)]
                       for ro, rn, rm in zip(old, new, marks)])
    return changed


def page(names, results, diffs):
    """build/regress/index.html: the saves with problems or changes first, then the rest, three snapshots each."""
    def row(name):
        problems, diff = results[name], diffs[name]
        notes = list(problems) + (["new"] if diff is None else ["frame %d changed: %d px" % d for d in diff])
        pics = "".join('<img src="now/%s/f%03d.png" title="frame %d">' % (name, f, f) for f in FRAMES)
        pics += "".join('<br><img src="diff/%s_f%03d.png" title="baseline | now | changed">' % (name, f)
                        for f, _ in diff or [])
        return '<section class="%s"><h2>%s</h2><p>%s</p>%s</section>' % (
            "bad" if problems else "changed" if diff else "", html.escape(name),
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
    ap.add_argument("saves", nargs="*", help="save names (default: every save in sta/aes)")
    ap.add_argument("--accept", action="store_true", help="make this run the new baseline")
    ap.add_argument("--no-build", action="store_true", help="don't rebuild first")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    args = ap.parse_args()

    names = args.saves or sorted(p.stem for p in SAVES.glob("*.sta"))
    missing = [n for n in names if not (SAVES / (n + ".sta")).exists()]
    if missing:
        sys.exit("no such save: " + ", ".join(missing))
    warnings = [] if args.no_build else build()

    now, base, diffs = OUT / "now", OUT / "baseline", OUT / "diff"
    shutil.rmtree(diffs, ignore_errors=True)
    diffs.mkdir(parents=True)
    with ThreadPoolExecutor(args.jobs) as pool:
        results = dict(pool.map(lambda n: play(n, now), names))

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
            lines.append("changed  %-24s %s" % (name, ", ".join("frame %d: %d px" % d for d in diff)))
    if new:
        lines.append("new      " + ", ".join(new))
    for w in warnings:
        lines.insert(0, "build    " + w)
    lines.append("%d saves: %d failed, %d changed, %d new, %d the same" %
                 (len(names), failed, changed, len(new), len(names) - changed - len(new)))
    print("\n".join(lines))
    (OUT / "report.txt").write_text("\n".join(lines) + "\n")
    page(names, results, compared)
    print("the run, to look through: " + str((OUT / "index.html").relative_to(ROOT)))

    if args.accept:
        for name in names:
            shutil.rmtree(base / name, ignore_errors=True)
            shutil.copytree(now / name, base / name)
        print("accepted as the baseline")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
