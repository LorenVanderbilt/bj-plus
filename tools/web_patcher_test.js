// Test the web patcher's engine (tools/web_patcher/patcher.js) under Node, against release.py's output:
//     node tools/web_patcher_test.js [bjplus-beta1]
// Run tools/release.py first. It patches roms/bjourney.zip the patcher's way and checks the result against
// build/aes/bjourney.zip, then builds every package and checks each file against dist/<name>/private/<system>/
// (README.txt aside: the private copy's first lines differ; a zip inside a package by its contents). Also: a
// Darksoft-style folder as input, a wrong program ROM, and something that isn't the game.
"use strict";
var fs = require("fs"), path = require("path");
var ROOT = path.dirname(__dirname), name = process.argv[2] || "bjplus-beta1";
var D = require(path.join(ROOT, "dist", name, "patcher", "patchdata.js"));
var P = require(path.join(ROOT, "tools", "web_patcher", "patcher.js"));
var failures = 0;

function check(ok, what) {
  console.log((ok ? "ok    " : "FAIL  ") + what);
  if (!ok) failures++;
}
function same(a, b) {
  return a.length === b.length && Buffer.compare(Buffer.from(a), Buffer.from(b)) === 0;
}
async function zipMap(data) {
  var m = {};
  (await P.readZip(data)).forEach(function (f) { m[f.name] = f.data; });
  return m;
}

(async function () {
  var original = new Uint8Array(fs.readFileSync(path.join(ROOT, "roms", "bjourney.zip")));
  var id = await P.identify(D, [{ name: "bjourney.zip", data: original }]);
  check(id.ok, "the MAME set's bjourney.zip is recognised");

  var t = Date.now(), built = await P.patch(D, id.files);
  var expect = await zipMap(new Uint8Array(fs.readFileSync(path.join(ROOT, "build", "aes", "bjourney.zip"))));
  check(D.order.every(function (n) { return same(built[n], expect[n]); }),
        "patched files match the build (" + (Date.now() - t) + " ms)");

  for (var i = 0; i < D.packages.length; i++) {
    var pkg = D.packages[i], files = await P.packageFiles(D, pkg, built), bad = [];
    for (var j = 0; j < files.length; j++) {
      var f = files[j], disk = path.join(ROOT, "dist", name, "private", pkg.id, f.name);
      if (f.name === "README.txt") { if (!fs.existsSync(disk)) bad.push(f.name); continue; }
      if (!fs.existsSync(disk)) { bad.push(f.name + " (not in private/)"); continue; }
      var want = new Uint8Array(fs.readFileSync(disk));
      if (/\.zip$/.test(f.name)) {
        var a = await zipMap(f.data), b = await zipMap(want);
        if (Object.keys(a).sort().join() !== Object.keys(b).sort().join() ||
            Object.keys(a).some(function (k) { return !same(a[k], b[k]); })) bad.push(f.name);
      } else if (!same(f.data, want)) bad.push(f.name);
    }
    var zipped = await P.buildPackage(D, pkg, built), back = await zipMap(zipped);
    if (Object.keys(back).length !== files.length) bad.push("(its zip)");
    check(bad.length === 0, pkg.label + ": " + files.length + " files, " + Math.round(zipped.length / 1024) +
          " KB" + (bad.length ? " - wrong: " + bad.join(", ") : ""));
  }

  var orig = await zipMap(original), dark = P.darksoft(D, orig);
  var fromDark = await P.identify(D, Object.keys(dark).map(function (n) { return { name: "bjourney/" + n, data: dark[n] }; }));
  check(fromDark.ok && D.order.every(function (n) { return same(fromDark.files[n], orig[n]); }),
        "a Darksoft-style folder is recognised and turned back into the MAME files");

  var wrong = Object.keys(orig).map(function (n) {
    var d = orig[n].slice(); if (n === "022-p1.p1") d[100] ^= 1; return { name: n, data: d };
  });
  var w = await P.identify(D, wrong);
  check(!w.ok && w.status.filter(function (s) { return s.state === "other"; }).map(function (s) { return s.name; }).join() === "022-p1.p1",
        "a changed program ROM is reported as a different version, by name");
  var none = await P.identify(D, [{ name: "readme.txt", data: new TextEncoder().encode("hello") }]);
  check(!none.ok && none.status.every(function (s) { return s.state === "missing"; }), "something else: every file missing");

  console.log(failures ? failures + " failed" : "all passed");
  process.exit(failures ? 1 : 0);
})().catch(function (e) { console.error(e); process.exit(1); });
