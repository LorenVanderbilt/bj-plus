#!/usr/bin/env python3
"""Make the release files from the last build: the web patcher, xdelta patches, and ready-to-copy packages.

    python3 tools/release.py [--name bjplus-beta1] [--version "Beta 1"]

Run tools/hackbuild.py first. Everything goes in dist/<name>/ (git-ignored):

    patcher/              the web patcher (tools/web_patcher/ plus this release's patchdata.js): a player drops in
                          their own bjourney.zip (or Darksoft-style folder), picks a system and downloads a ready
                          package with its README. Patching happens in their browser; nothing is uploaded.
    <name>_itch_html.zip  patcher/ zipped for itch.io's "HTML" upload (index.html at its root)
    <name>_xdelta.zip     patches for the MAME set's files (022-p1.p1.xdelta ...), and for a Darksoft-style set's
                          (prom.xdelta ...), with how to apply them by hand. No game data: shareable.
    private/<system>/     each package the patcher makes, ready-patched, for testing on your own devices only -
                          they hold game data. The same layout and README the patcher's download has.

The packages are defined once, in PACKAGES: release.py builds private/ from that list and writes the same list into
patchdata.js for the patcher, so the two can't drift apart.

The Darksoft layout was checked against the published Darksoft checksums for the original game: prom, srom and
m1rom are the MAME files as they are, crom0 is each C ROM pair interleaved a word at a time (c1 / c2, then c3 / c4),
vroma0 is v11 with zeros up to 2 MB and then v22 (the ADPCM-B ROM, at MiSTer's vromb_offset 0x200000), and fpga is
the text "13".

Final Burn Neo reads each file at the size its game list gives (c3 / c4 512 KB), so the added sprite tiles
(hackbuild's AES_C34_SIZE) never load through its "patched romsets" folder. A RomData file (FBNeo's own format,
src/burner/romdata.cpp) declares the files' real sizes: bjplus.zip next to bjplus.dat runs as bjourney with them.
"""
import argparse
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGINAL = os.path.join(ROOT, "roms", "bjourney.zip")
BUILT = os.path.join(ROOT, "build", "aes", "bjourney.zip")
BUILT_LIST = os.path.join(ROOT, "build", "aes", "neogeo.xml")
                                    # MAME's software list entry for the built files: its own list has c3 / c4 at
                                    # the original 512 KB and refuses the grown ones
WEB_PATCHER = os.path.join(ROOT, "tools", "web_patcher")
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
FBNEO_NAME = "bjplus"               # the RomData set's zip and .dat
FBNEO_TYPES = {"022-p1.p1": "1, BRF_ESS, BRF_PRG", "022-s1.s1": "2, BRF_GRA", "022-c1.c1": "3, BRF_GRA",
               "022-c2.c2": "3, BRF_GRA", "022-c3.c3": "3, BRF_GRA", "022-c4.c4": "3, BRF_GRA",
               "022-m1.m1": "4, BRF_ESS, BRF_PRG", "022-v11.v11": "5, BRF_SND", "022-v22.v22": "5, BRF_SND"}
                                    # each file's ROM type, as FBNeo's bjourney entry (d_neogeo.cpp). Written out:
                                    # the RetroArch core's RomData parser (src/burner/libretro/romdata.cpp) has no
                                    # [section] defaults and drops a line without a type - with none it ran as an
                                    # unknown "bjplus" (the user's Retroid, 2026-11-09)
POCKET_FOLDER = "bjplus"            # in Assets/ng/common/: its own name, so the original bjourney folder stays
POCKET_JSON = {                     # Mazamars312's Neo Geo core: a copy of its Blue's Journey instance file (from
    "instance": {                   # the core's dist/Assets/ng/Mazamars312.NeoGeo/) pointed at POCKET_FOLDER. The
        "magic": "APF_VER_1",       # memory writes set up the sound ROMs (PCM, V2OFFSET, V2MASK, C1WAIT in its
        "variant_select": {"id": 777, "select": False},     # neogeojsonmaker.py), not the sprite ROM's size
        "data_path": POCKET_FOLDER,
        "data_slots": [{"id": 3, "filename": "srom"}, {"id": 4, "filename": "prom"}, {"id": 5, "filename": "crom0"},
                       {"id": 6, "filename": "m1rom"}, {"id": 7, "filename": "vroma0"}],
        "memory_writes": [{"address": "0xF000030c", "data": "0xFFFFFFFF"},
                          {"address": "0xF0000310", "data": "0x00200000"},
                          {"address": "0xF0000314", "data": "0x000FFFFF"},
                          {"address": "0xF0000400", "data": "0x00000001"}],
    }
}
MERGE_GAP = 32                      # patch runs closer than this are stored as one


def readme(system, version, contents, steps, trouble, private=False):
    """A package's README.txt: what it is, what's in it, where it goes, what to do if it doesn't work."""
    rule = "=" * 70
    lines = ["Blue's Journey Plus - %s - %s" % (version, system), rule, "",
             "Blue's Journey Plus is a fan update of Blue's Journey (Alpha Denshi, 1990) for the Neo Geo home",
             "console (AES): a bigger, redrawn Blue, a new HUD, a pause menu, a retranslated script and many fixes.",
             "",
             ("These files were patched for testing on your own devices. They contain the game's data: don't share"
              " them." if private else
              "This package was made from your own copy of the game, in your browser. It contains the game's data:"
              " please don't share it - point people to the patcher instead."), "",
             "WHAT'S IN IT", ""]
    lines += ["  %s" % c for c in contents]
    lines += ["", "HOW TO PLAY IT", ""]
    for i, step in enumerate(steps):                    # (a step's later lines: a command, a note, under it)
        first, *more = step.split("\n")
        lines += ["  %d. %s" % (i + 1, first)] + ["     " + m for m in more]
    lines += ["", "IF SOMETHING'S WRONG", ""]
    lines += ["  - %s" % t for t in trouble]
    lines += ["", "Found a problem or a glitch? Please report it on the Blue's Journey Plus page, with where it"
              " happened and a screenshot if you can.", "",
              "Blue's Journey (c) 1990 Alpha Denshi / SNK. Blue's Journey Plus is an unofficial fan project by"
              " Loren Vanderbilt III, not affiliated with or endorsed by them.", ""]
    return "\n".join(_wrap(l) for l in lines)


def _wrap(line, width=100):
    """Hard-wrap one README line, keeping its indent on the continuation lines."""
    if len(line) <= width:
        return line
    body = line.lstrip()
    indent = " " * (len(line) - len(body))
    lead = indent + ("   " if body[:2] in ("- ",) or body[:1].isdigit() else "")
    out, cur = [], indent
    for word in body.split(" "):
        if len(cur) + len(word) + 1 > width and cur.strip():
            out.append(cur.rstrip())
            cur = lead
        cur += word + " "
    out.append(cur.rstrip())
    return "\n".join(out)


def packages(version, private=False):
    """Every system's package: {id, label, note, download, entries: [[path, kind, arg]], next: [steps]}.
    kind "file": a MAME file (by its name); "darksoft": a Darksoft-style file (prom, crom0 ...); "zip": a zip of
    the MAME files named in arg; "text": arg itself; "list": MAME's software list entry; "dat": the FBNeo RomData file."""
    def pkg(id_, label, note, download, entries, system, contents, steps, trouble):
        entries = entries + [["README.txt", "text", readme(system, version, contents, steps, trouble, private)]]
        return {"id": id_, "label": label, "note": note, "download": download, "entries": entries, "next": steps}

    dark = ["prom", "srom", "m1rom", "crom0", "vroma0", "fpga"]
    return [
        pkg("retroarch", "RetroArch", "FinalBurn Neo core: Android, PC, Mac, handhelds",
            "BluesJourneyPlus-RetroArch.zip",
            [["bjplus.zip", "zip", GAME_FILES], ["bjplus.dat", "dat", None]],
            "RetroArch (FinalBurn Neo)",
            ["bjplus.zip  the patched game",
             "bjplus.dat  tells FinalBurn Neo the game's file sizes (its graphics files are bigger than the",
             "            original's) - keep it next to bjplus.zip",
             "README.txt  this file"],
            ["Copy bjplus.zip and bjplus.dat into the folder with your other Neo Geo games, side by side. The Neo Geo"
             " BIOS, neogeo.zip, needs to be in that folder or in RetroArch's system folder.",
             "In RetroArch, choose Load Content, pick bjplus.zip and the core \"Arcade (FinalBurn Neo)\".",
             "Open Quick Menu > Core Options and set the Neo-Geo mode to an AES (home console) setting, such as"
             " \"AES Asia\". Then Quick Menu > Restart."],
            ["\"Romset is unknown\": bjplus.dat isn't in the same folder as bjplus.zip, or the FinalBurn Neo core is"
             " older than mid-2024. Update it with Online Updater > Update Installed Cores.",
             "INSERT COIN on the title, and no NEW GAME / OPTIONS menu: the core is in arcade (MVS) mode. Set the"
             " Neo-Geo mode to AES and restart.",
             "Use FinalBurn Neo, not RetroArch's MAME cores: those only run the arcade version, without the newest"
             " graphics. FinalBurn Neo's \"patched romsets\" folder doesn't work for this game either.",
             "Tested on a Retroid Pocket with RetroArch 1.22 and FinalBurn Neo 1.0.0.03."]),
        pkg("mame", "MAME", "On a computer: Windows, Mac, Linux",
            "BluesJourneyPlus-MAME.zip",
            [["bjplus/bjourney.zip", "zip", GAME_FILES], ["bjplus/neogeo.xml", "list", None]],
            "MAME",
            ["bjplus/bjourney.zip  the patched game",
             "bjplus/neogeo.xml    MAME's list entry for it: the game's graphics files are bigger than the",
             "                     original's, and MAME refuses them without this",
             "README.txt           this file"],
            ["Put the bjplus folder somewhere handy, for example next to your MAME roms folder.",
             "Open a terminal (Command Prompt on Windows) in the folder that holds bjplus, and run MAME as the Neo"
             " Geo home console, giving the path of your roms folder (the one with your Neo Geo BIOS files: neogeo.zip, and"
             " aes.zip for the home console):\n"
             "  mame aes -hash bjplus -rompath \"bjplus;C:\\path\\to\\your\\roms\" -cart bjourney\n"
             "On a Mac or Linux the path looks like \"bjplus;/Users/you/mame/roms\"."],
            ["\"WRONG LENGTH\" or \"not found\": MAME isn't reading bjplus/neogeo.xml. Check -hash points at the"
             " bjplus folder.",
             "Don't run it with \"mame bjourney\": that's the arcade machine, which loads only part of the graphics"
             " and has no title menu.",
             "Tested with MAME 0.289."]),
        pkg("backbit", "BackBit Platinum", "A real Neo Geo, with the BackBit flash cart",
            "BluesJourneyPlus-BackBit.zip",
            [["%s/%s" % (BACKBIT_FOLDER, BACKBIT_NAMES.get(n, n)), "file", n] for n in GAME_FILES],
            "BackBit Platinum MVS",
            ["%s/  the game's files, ready for the cart. The two sound files are named" % BACKBIT_FOLDER,
             "    022-v1.v1 and 022-v2.v2, the names the cart's developer gives for this game (with MAME's",
             "    names the music crackles)",
             "README.txt  this file"],
            ["Copy the \"%s\" folder into the NeoGeo folder on the cart's SD card. Putting it inside a genre"
             " folder is fine." % BACKBIT_FOLDER,
             "In the cart's menu, set Arcade Mode to AES.",
             "Choose %s from the cart's menu." % BACKBIT_FOLDER],
            ["Keep the cart's Menu Hotkey turned on: with it off, the cart can crash when Start is pressed on the"
             " title screen (the original game does this too).",
             "Copying from a Mac adds hidden \"._\" files the cart can pick up by mistake. Eject the card properly,"
             " or run dot_clean on the folder first.",
             "Tested on a BackBit Platinum in a Neo Geo, on a CRT TV."]),
        pkg("mister", "MiSTer", "The NeoGeo core, Darksoft-style folder",
            "BluesJourneyPlus-MiSTer.zip",
            [["bjourney/%s" % n, "darksoft", n] for n in dark],
            "MiSTer (NeoGeo core)",
            ["bjourney/   the patched game in the Darksoft-style layout the NeoGeo core reads",
             "README.txt  this file"],
            ["If you already have Blue's Journey in games/NeoGeo/bjourney, move it somewhere else first: this"
             " folder takes its place.",
             "Copy the bjourney folder into games/NeoGeo/ on the MiSTer's SD card.",
             "Load it in the NeoGeo core and set the system type to AES in the core's menu."],
            ["Not tested on a MiSTer yet: it should work (the core reads the bigger graphics file whole), but"
             " please report how it goes."]),
        pkg("pocket", "Analogue Pocket", "Mazamars312's Neo Geo core",
            "BluesJourneyPlus-AnaloguePocket.zip",
            [["Assets/ng/common/%s/%s" % (POCKET_FOLDER, n), "darksoft", n] for n in dark if n != "fpga"]
            + [["Assets/ng/Mazamars312.NeoGeo/Blue's Journey Plus.json", "text",
                json.dumps(POCKET_JSON, indent=4) + "\n"]],
            "Analogue Pocket (Mazamars312's Neo Geo core)",
            ["Assets/ng/common/%s/  the patched game (Darksoft-style files)" % POCKET_FOLDER,
             "Assets/ng/Mazamars312.NeoGeo/Blue's Journey Plus.json  tells the core where the game is",
             "README.txt  this file",
             "Your original Blue's Journey (Assets/ng/common/bjourney) is left as it is."],
            ["Set up Mazamars312's Neo Geo core first if you haven't: its BIOS files go in Assets/ng/common/.",
             "Copy the Assets folder onto the root of the Pocket's SD card. It merges with the Assets folder"
             " already there.",
             "On the Pocket, open the Neo Geo core and choose Blue's Journey Plus.",
             "Press the Home button, then Core Settings > MVS/AES, and choose AES. The core restarts."],
            ["The game doesn't appear: check the .json file is in Assets/ng/Mazamars312.NeoGeo/ and the game's"
             " files in Assets/ng/common/%s/." % POCKET_FOLDER,
             "INSERT COIN on the title: the core is in MVS mode. Set MVS/AES to AES under Core Settings."]),
    ]


def sha1(data):
    return hashlib.sha1(data).hexdigest()


def crc(data):
    return "%08x" % (zlib.crc32(data) & 0xFFFFFFFF)


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


def zip_bytes(files):
    path = os.path.join(ROOT, "dist", ".zip_tmp")
    write_zip(path, files)
    data = open(path, "rb").read()
    os.remove(path)
    return data


def fbneo_dat(files):
    """FBNeo's RomData file for the built files: run as bjourney, from bjplus.zip, at the files' own sizes."""
    lines = ["// Blue's Journey Plus: Final Burn Neo RomData (load %s.zip, this file next to it)" % FBNEO_NAME,
             "ZipName:  " + FBNEO_NAME, "DrvName:  bjourney", "FullName: \"Blue's Journey Plus\""]
    lines.append("")
    lines += ["%-12s 0x%06x, 0x%08x, %s" % (n + ",", len(files[n]), zlib.crc32(files[n]), FBNEO_TYPES[n])
              for n in FBNEO_TYPES]           # (in the driver's order)
    return "\n".join(lines) + "\n"


def runs(old, new):
    """Where new differs from old (or runs past its end), as [offset, length] runs merged across small gaps."""
    def same(a, b):
        return b <= len(old) and old[a:b] == new[a:b]
    out, i, n, step = [], 0, len(new), 64
    while i < n:
        j = min(i + step, n)
        if same(i, j):
            i = j
            continue
        s = i
        while s < len(old) and old[s] == new[s]:
            s += 1
        e = j
        while e < n and not same(e, min(e + step, n)):
            e = min(e + step, n)
        while e > s and e <= len(old) and old[e - 1] == new[e - 1]:
            e -= 1
        if out and s - (out[-1][0] + out[-1][1]) < MERGE_GAP:
            out[-1][1] = e - out[-1][0]
        else:
            out.append([s, e - s])
        i = max(e, j)
    return out


def patch_data(original, built, version, packages_list):
    """patchdata.js for the web patcher: the original files' checksums (MAME and Darksoft names), each patched
    file's runs (their bytes deflated together, from the file's "at" in that blob), the texts the packages need,
    and the packages."""
    blob, files = bytearray(), {}
    for name in GAME_FILES:
        new, rs = built[name], runs(original[name], built[name])
        files[name] = {"size": len(new), "crc32": crc(new), "runs": rs, "at": len(blob)}
        for off, length in rs:
            blob += new[off:off + length]
        back = bytearray(original[name][:len(new)].ljust(len(new), b"\0"))     # (rebuilt the patcher's way)
        at = files[name]["at"]
        for off, length in rs:
            back[off:off + length] = blob[at:at + length]
            at += length
        assert bytes(back) == new, "runs of %s don't rebuild it" % name
    comp = zlib.compressobj(9, zlib.DEFLATED, -15)
    packed = comp.compress(bytes(blob)) + comp.flush()
    data = {
        "version": version,
        "order": GAME_FILES,
        "source": {n: {"size": len(original[n]), "crc32": crc(original[n])} for n in GAME_FILES},
        "darksource": {n: {"size": len(d), "crc32": crc(d)} for n, d in darksoft(original).items()},
        "vrombOffset": VROMB_OFFSET,
        "target": files,
        "blobSize": len(blob),
        "texts": {"dat": fbneo_dat(built), "list": open(BUILT_LIST).read()},
        "packages": packages_list,
        "blob": base64.b64encode(packed).decode(),
    }
    return ("// Generated by tools/release.py for %s - don't edit.\nvar BJPLUS = %s;\n"
            "if (typeof module !== \"undefined\") module.exports = BJPLUS;\n" % (version, json.dumps(data)))


def build_package(pkg, built, dark_built, texts):
    """The files a package holds: {path: bytes} (the same thing the web patcher builds)."""
    out = {}
    for path, kind, arg in pkg["entries"]:
        if kind == "file":
            out[path] = built[arg]
        elif kind == "darksoft":
            out[path] = dark_built[arg]
        elif kind == "zip":
            out[path] = zip_bytes({n: built[n] for n in arg})
        elif kind in ("dat", "list"):
            out[path] = texts[kind].encode()
        else:
            out[path] = arg.encode()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", default="bjplus-beta1")
    ap.add_argument("--version", default="Beta 1")
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
    texts = {"dat": fbneo_dat(built), "list": open(BUILT_LIST).read()}

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
    patches["fbneo/%s.dat" % FBNEO_NAME] = texts["dat"]
    patches["mame/neogeo.xml"] = texts["list"]
    patches["README.txt"] = XDELTA_README % {"version": args.version}
    patches["CHECKSUMS.txt"] = "\n".join(checksums) + "\n"
    write_zip(os.path.join(out, "%s_xdelta.zip" % args.name), patches)

    for pkg in packages(args.version, private=True):       # private/<system>/: unpacked, ready to copy
        for path, data in build_package(pkg, built, dark_built, texts).items():
            dest = os.path.join(out, "private", pkg["id"], path)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            open(dest, "wb").write(data)

    web = os.path.join(out, "patcher")
    shutil.copytree(WEB_PATCHER, web)
    open(os.path.join(web, "patchdata.js"), "w").write(patch_data(original, built, args.version, packages(args.version)))
    with zipfile.ZipFile(os.path.join(out, "%s_itch_html.zip" % args.name), "w", zipfile.ZIP_DEFLATED) as z:
        for n in sorted(os.listdir(web)):
            z.write(os.path.join(web, n), n)
    shutil.rmtree(work)

    for path, _, names in sorted(os.walk(out)):
        for n in sorted(names):
            p = os.path.join(path, n)
            print("%9d  %s" % (os.path.getsize(p), os.path.relpath(p, ROOT)))


XDELTA_README = """Blue's Journey Plus - %(version)s - patches
======================================================================

The easy way: use the Blue's Journey Plus patcher on its page. Drop in your bjourney.zip, pick your system and
download a ready package. These patches are for doing it by hand.

You need the MAME ROM set bjourney (Blue's Journey / Raguy). Check your files match the checksums in
CHECKSUMS.txt before patching.

MAME set (MAME, RetroArch, most emulators)
  1. Unzip bjourney.zip into a folder.
  2. Apply each file in mame/ to the ROM file it's named after, with an xdelta patcher (Delta Patcher, or
     xdelta3 -d -s 022-p1.p1 022-p1.p1.xdelta 022-p1.p1.new and then replace the original with the .new file).
  3. Zip the files back up as bjourney.zip and play it as the Neo Geo AES (home console).
  MAME: its own list of Neo Geo carts expects the original file sizes and refuses the patched set. Put the patched
  bjourney.zip in a folder of its own with mame/neogeo.xml from this zip, and run (with the folder's path):
      mame aes -hash bjplus -rompath "bjplus;roms" -cart bjourney
  (roms being where your neogeo.zip / aes.zip BIOS files are).

RetroArch, Final Burn Neo core
  Patch the MAME set's files as above, but zip them as bjplus.zip instead, and put it in your ROMs folder with
  fbneo/bjplus.dat from this zip next to it (and neogeo.zip). Load bjplus.zip, with the core's Neo Geo mode set
  to AES. (FBNeo's "patched romsets" folder doesn't work for this hack: it cuts the bigger graphics files short.)

Darksoft-style set (MiSTer, Analogue Pocket)
  If you have the game as a Darksoft-style folder (prom, srom, m1rom, crom0, vroma0, fpga), apply the files in
  darksoft/ the same way. vroma0 and fpga don't change.

BackBit Platinum MVS
  Patch the MAME set's files as above, then rename 022-v11.v11 to 022-v1.v1 and 022-v22.v22 to 022-v2.v2 (with
  MAME's names the music crackles). Put the game's files (no zip, no BIOS files) in a folder of their own inside
  NeoGeo/ on the card, and set the cart's Arcade Mode to AES.
"""


if __name__ == "__main__":
    main()
