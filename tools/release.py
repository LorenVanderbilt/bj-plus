#!/usr/bin/env python3
"""Make the release files from the last build: xdelta patches, and ready-to-copy packages for each setup.

    python3 tools/release.py [--name bjplus-beta1]

Run tools/hackbuild.py first. Everything goes in dist/<name>/ (git-ignored):

    <name>_xdelta.zip     patches for the MAME set's files (022-p1.p1.xdelta ...), and for a Darksoft-style set's
                          (prom.xdelta ...), with how to apply them. No game data: this is the one to share.
    private/              ready-patched files, for testing on your own devices only - they hold game data:
        fbneo/            RetroArch Final Burn Neo (AES): fbneo/patched/bjourney.zip
        mame_aes/         MAME: bjourney.zip, for `mame aes -cart bjourney`
        mister_pocket/    MiSTer and Analogue Pocket: a Darksoft-style bjourney/ folder
        backbit/          BackBit Platinum MVS: a folder of the game's files, the sound ROMs named as the cart wants

The Darksoft layout was checked against the published Darksoft checksums for the original game: prom, srom and
m1rom are the MAME files as they are, crom0 is each C ROM pair interleaved a word at a time (c1 / c2, then c3 / c4),
vroma0 is v11 with zeros up to 2 MB and then v22 (the ADPCM-B ROM, at MiSTer's vromb_offset 0x200000), and fpga is
the text "13".
"""
import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(ROOT, "roms", "bjourney.zip")
BUILT = os.path.join(ROOT, "build", "aes", "bjourney.zip")
GAME_FILES = ["022-p1.p1", "022-s1.s1", "022-m1.m1", "022-v11.v11", "022-v22.v22",
              "022-c1.c1", "022-c2.c2", "022-c3.c3", "022-c4.c4"]
ORIGINAL_SHA1 = {   # the files the patches apply to, as listed in README.md
    "022-p1.p1": "b8ca548e56f1c7abcdce415ba7329e0cf698ee13",
    "022-s1.s1": "dbdf86c193b7c1d795f8c21f2c103c1d3e18abbe",
    "022-m1.m1": "deabc11ab81e7e68a3e041c03a127ae28d0d7264",
    "022-c1.c1": "6e282285be72583d828e7765b1c1695ecdc44777",
    "022-c2.c2": "c468d2556b3de095aaa05edd1bc16d71303e9478",
    "022-c3.c3": "974b823fc62236fbc23e727f25b61a805a707a9e",
    "022-c4.c4": "47288be69e6992d09ebef108b4de9ffab6293dc8",
}
DARKSOFT_SHA1 = {   # Darksoft's checksums for the original game's folder
    "prom": "b8ca548e56f1c7abcdce415ba7329e0cf698ee13",
    "srom": "dbdf86c193b7c1d795f8c21f2c103c1d3e18abbe",
    "m1rom": "deabc11ab81e7e68a3e041c03a127ae28d0d7264",
    "crom0": "8065f86a92a5b498fbe45d5b65eb8e199a756115",
    "vroma0": "d50f5bdc2b83232298e96059c380b41879506bdf",
    "fpga": "bd307a3ec329e10a2cff8fb87480823da114f8f4",
}
VROMB_OFFSET = 0x200000
BACKBIT_NAMES = {"022-v11.v11": "022-v1.v1", "022-v22.v22": "022-v2.v2"}
                                    # the cart's developer's names for Blue's Journey's sound ROMs: with MAME's, the
                                    # music is missing a channel (checked on the user's cart, 2026-11-06)
BACKBIT_FOLDER = "Blues Journey Plus"   # the cart's menu shows the folder's name

XDELTA_README = """Blue's Journey Plus - patches

You need the MAME ROM set bjourney (Blue's Journey / Raguy). Check your files match the checksums in
CHECKSUMS.txt before patching.

MAME set (MAME, RetroArch, most emulators)
  1. Unzip bjourney.zip into a folder.
  2. Apply each file in mame/ to the ROM file it's named after, with an xdelta patcher (Delta Patcher, or
     xdelta3 -d -s 022-p1.p1 022-p1.p1.xdelta 022-p1.p1.new and then replace the original with the .new file).
  3. Zip the files back up as bjourney.zip and play it as the Neo Geo AES (home console).

Darksoft-style set (MiSTer, Analogue Pocket)
  If you have the game as a Darksoft-style folder (prom, srom, m1rom, crom0, vroma0, fpga), apply the files in
  darksoft/ the same way. vroma0 and fpga don't change.

BackBit Platinum MVS
  Patch the MAME set's files as above, then rename 022-v11.v11 to 022-v1.v1 and 022-v22.v22 to 022-v2.v2 (with
  MAME's names the cart drops a sound channel). Put the game's files (no zip, no BIOS files) in a folder of their
  own inside NeoGeo/ on the card, and set the cart's Arcade Mode to AES.
"""

PRIVATE_README = """Ready-patched files for testing on your own devices. They contain game data: don't share them.

fbneo/ - RetroArch, Final Burn Neo core
  Keep the original bjourney.zip in your ROMs folder. Copy fbneo/patched/bjourney.zip to
  <RetroArch system folder>/fbneo/patched/bjourney.zip. In the core options, turn on "Allow patched romsets"
  and set the Neo Geo mode to AES. Then load the original bjourney.zip.

mame_aes/ - MAME
  Put bjourney.zip in your roms folder (with neogeo.zip, and an AES BIOS) and run: mame aes -cart bjourney

backbit/ - BackBit Platinum MVS
  Copy the "Blues Journey Plus" folder into NeoGeo/ on the card (any genre folder inside it is fine) and set the
  cart's Arcade Mode to AES (D in its menu). Leave the Menu Hotkey on: with it off the cart crashes on Start at the
  title, the unpatched game too.

mister_pocket/ - MiSTer and Analogue Pocket
  MiSTer: copy the bjourney folder into games/NeoGeo/ (the core's Darksoft romsets.xml lists bjourney) and
  pick AES in the core's menu.
  Analogue Pocket (Mazamars312's Neo Geo core): copy the bjourney folder into assets/ng/common/, then choose
  AES under Core Settings.
"""


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def darksoft(files):
    """The Darksoft-style folder's files from a MAME set's: {name: bytes}."""
    def interleave(a, b):
        return b"".join(a[i:i + 2] + b[i:i + 2] for i in range(0, len(a), 2))
    v11 = files["022-v11.v11"]
    return {
        "prom": files["022-p1.p1"],
        "srom": files["022-s1.s1"],
        "m1rom": files["022-m1.m1"],
        "crom0": interleave(files["022-c1.c1"], files["022-c2.c2"]) + interleave(files["022-c3.c3"], files["022-c4.c4"]),
        "vroma0": v11 + bytes(VROMB_OFFSET - len(v11)) + files["022-v22.v22"],
        "fpga": b"13",
    }


def xdelta(old, new, out, work):
    """Write an xdelta patch from old to new (bytes) at out, and check it applies."""
    a, b, back = (os.path.join(work, n) for n in ("old", "new", "back"))
    open(a, "wb").write(old)
    open(b, "wb").write(new)
    subprocess.run(["xdelta3", "-e", "-9", "-f", "-s", a, b, out], check=True)
    subprocess.run(["xdelta3", "-d", "-f", "-s", a, out, back], check=True)
    assert open(back, "rb").read() == new, "%s doesn't apply" % out


def write_zip(path, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", default="bjplus-beta1")
    args = ap.parse_args()
    if not shutil.which("xdelta3"):
        sys.exit("xdelta3 not found (brew install xdelta)")
    original = {n: zipfile.ZipFile(ORIGINAL).read(n) for n in GAME_FILES}
    built = {n: zipfile.ZipFile(BUILT).read(n) for n in GAME_FILES}
    for name, want in ORIGINAL_SHA1.items():
        if sha1(original[name]) != want:
            sys.exit("roms/bjourney.zip: %s isn't the expected file" % name)
    dark_original, dark_built = darksoft(original), darksoft(built)
    for name, want in DARKSOFT_SHA1.items():
        assert sha1(dark_original[name]) == want, "Darksoft %s doesn't match its checksum" % name

    out = os.path.join(ROOT, "dist", args.name)
    shutil.rmtree(out, ignore_errors=True)
    work = os.path.join(out, "_work")
    os.makedirs(work)

    patches, checksums = {}, ["MAME set (bjourney.zip):"]
    for sets, folder in ((zip(GAME_FILES, (original[n] for n in GAME_FILES), (built[n] for n in GAME_FILES)), "mame"),
                         (((n, dark_original[n], dark_built[n]) for n in dark_original), "darksoft")):
        if folder == "darksoft":
            checksums.append("\nDarksoft-style folder:")
        for name, old, new in sets:
            checksums.append("  %-12s %8d bytes  sha1 %s" % (name, len(old), sha1(old)))
            if old != new:
                path = os.path.join(work, "patch")
                xdelta(old, new, path, work)
                patches["%s/%s.xdelta" % (folder, name)] = open(path, "rb").read()
    patches["README.txt"] = XDELTA_README
    patches["CHECKSUMS.txt"] = "\n".join(checksums) + "\n"
    write_zip(os.path.join(out, "%s_xdelta.zip" % args.name), patches)

    private = os.path.join(out, "private")
    os.makedirs(os.path.join(private, "fbneo", "patched"))
    write_zip(os.path.join(private, "fbneo", "patched", "bjourney.zip"), built)
    os.makedirs(os.path.join(private, "mame_aes"))
    write_zip(os.path.join(private, "mame_aes", "bjourney.zip"), built)
    folder = os.path.join(private, "mister_pocket", "bjourney")
    os.makedirs(folder)
    for name, data in dark_built.items():
        open(os.path.join(folder, name), "wb").write(data)
    folder = os.path.join(private, "backbit", BACKBIT_FOLDER)
    os.makedirs(folder)
    for name in GAME_FILES:
        open(os.path.join(folder, BACKBIT_NAMES.get(name, name)), "wb").write(built[name])
    open(os.path.join(private, "README.txt"), "w").write(PRIVATE_README)
    shutil.rmtree(work)

    for path, _, names in sorted(os.walk(out)):
        for n in sorted(names):
            p = os.path.join(path, n)
            print("%9d  %s" % (os.path.getsize(p), os.path.relpath(p, ROOT)))


if __name__ == "__main__":
    main()
