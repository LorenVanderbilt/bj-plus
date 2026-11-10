// Blue's Journey Plus web patcher: everything but the page - reading the player's files, checking them, patching,
// and building each system's package. index.html drives it; tools/web_patcher_test.js runs it under Node against
// release.py's own packages. The data (checksums, patch runs, packages) is patchdata.js, written by release.py.
(function (root) {
  "use strict";

  var CRC_TABLE = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(data) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < data.length; i++) c = CRC_TABLE[(c ^ data[i]) & 255] ^ (c >>> 8);
    return ("0000000" + ((c ^ 0xFFFFFFFF) >>> 0).toString(16)).slice(-8);
  }

  // Raw deflate: the browser's own CompressionStream, or Node's zlib (for the test).
  function through(stream, data) {
    var piped = new Blob([data]).stream().pipeThrough(stream);
    return new Response(piped).arrayBuffer().then(function (b) { return new Uint8Array(b); });
  }
  function inflateRaw(data) {
    if (typeof DecompressionStream !== "undefined") return through(new DecompressionStream("deflate-raw"), data);
    return Promise.resolve(new Uint8Array(require("zlib").inflateRawSync(data)));
  }
  function deflateRaw(data) {
    if (typeof CompressionStream !== "undefined") return through(new CompressionStream("deflate-raw"), data);
    return Promise.resolve(new Uint8Array(require("zlib").deflateRawSync(data)));
  }

  function fromBase64(text) {
    if (typeof atob === "undefined") return new Uint8Array(Buffer.from(text, "base64"));
    var bin = atob(text), out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }

  // A zip's files as [{name, data}] (stored or deflated entries; folders skipped).
  async function readZip(buf) {
    var dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength), end = -1;
    for (var i = buf.length - 22; i >= Math.max(0, buf.length - 65557); i--) {
      if (dv.getUint32(i, true) === 0x06054b50) { end = i; break; }
    }
    if (end < 0) throw new Error("This isn't a zip file.");
    var count = dv.getUint16(end + 10, true), p = dv.getUint32(end + 16, true), out = [];
    var names = new TextDecoder();
    for (var k = 0; k < count; k++) {
      if (dv.getUint32(p, true) !== 0x02014b50) throw new Error("This zip file is damaged.");
      var method = dv.getUint16(p + 10, true), packed = dv.getUint32(p + 20, true), size = dv.getUint32(p + 24, true);
      var nameLen = dv.getUint16(p + 28, true), extra = dv.getUint16(p + 30, true), note = dv.getUint16(p + 32, true);
      var local = dv.getUint32(p + 42, true);
      var name = names.decode(buf.subarray(p + 46, p + 46 + nameLen));
      p += 46 + nameLen + extra + note;
      if (name.slice(-1) === "/") continue;
      var at = local + 30 + dv.getUint16(local + 26, true) + dv.getUint16(local + 28, true);
      var raw = buf.subarray(at, at + packed), data;
      if (method === 0) data = raw.slice();
      else if (method === 8) data = await inflateRaw(raw);
      else throw new Error(name + " uses a kind of compression this page can't read. Re-zip it normally.");
      if (data.length !== size) throw new Error(name + " didn't unpack whole: the zip may be damaged.");
      out.push({ name: name, data: data });
    }
    return out;
  }

  // A zip of [{name, data}], deflated where that's smaller.
  async function writeZip(files) {
    var enc = new TextEncoder(), parts = [], central = [], offset = 0, now = new Date();
    var time = (now.getHours() << 11) | (now.getMinutes() << 5) | (now.getSeconds() >> 1);
    var date = ((now.getFullYear() - 1980) << 9) | ((now.getMonth() + 1) << 5) | now.getDate();
    for (var i = 0; i < files.length; i++) {
      var f = files[i], name = enc.encode(f.name), crc = parseInt(crc32(f.data), 16);
      var body = await deflateRaw(f.data), method = 8;
      if (body.length >= f.data.length) { body = f.data; method = 0; }
      var head = new Uint8Array(30 + name.length), h = new DataView(head.buffer);
      h.setUint32(0, 0x04034b50, true); h.setUint16(4, 20, true); h.setUint16(6, 0x0800, true);
      h.setUint16(8, method, true); h.setUint16(10, time, true); h.setUint16(12, date, true);
      h.setUint32(14, crc, true); h.setUint32(18, body.length, true); h.setUint32(22, f.data.length, true);
      h.setUint16(26, name.length, true); head.set(name, 30);
      var dir = new Uint8Array(46 + name.length), d = new DataView(dir.buffer);
      d.setUint32(0, 0x02014b50, true); d.setUint16(4, 20, true); d.setUint16(6, 20, true); d.setUint16(8, 0x0800, true);
      d.setUint16(10, method, true); d.setUint16(12, time, true); d.setUint16(14, date, true);
      d.setUint32(16, crc, true); d.setUint32(20, body.length, true); d.setUint32(24, f.data.length, true);
      d.setUint16(28, name.length, true); d.setUint32(42, offset, true); dir.set(name, 46);
      parts.push(head, body);
      central.push(dir);
      offset += head.length + body.length;
    }
    var dirSize = central.reduce(function (n, c) { return n + c.length; }, 0);
    var tail = new Uint8Array(22), t = new DataView(tail.buffer);
    t.setUint32(0, 0x06054b50, true); t.setUint16(8, files.length, true); t.setUint16(10, files.length, true);
    t.setUint32(12, dirSize, true); t.setUint32(16, offset, true);
    var all = parts.concat(central, [tail]), out = new Uint8Array(offset + dirSize + 22), pos = 0;
    all.forEach(function (a) { out.set(a, pos); pos += a.length; });
    return out;
  }

  // The player's files ([{name, data}]: loose files, the contents of zips, a zip inside a zip) -> the original
  // MAME set's files by checksum, read straight or made from a Darksoft-style folder. Returns {files, status}:
  // status lists each needed file as found, from a Darksoft folder, a different version (same name, other
  // checksum) or missing.
  async function identify(D, given) {
    var all = [];
    for (var i = 0; i < given.length; i++) {
      var g = given[i];
      if (/\.zip$/i.test(g.name)) {
        try { (await readZip(g.data)).forEach(function (f) { all.push(f); }); } catch (e) { all.push(g); }
      } else all.push(g);
    }
    var byCrc = {}, byName = {};
    all.forEach(function (f) {
      var c = crc32(f.data);
      if (!byCrc[c]) byCrc[c] = f.data;
      byName[f.name.split("/").pop().toLowerCase()] = c;
    });
    var files = {}, status = [];
    D.order.forEach(function (n) {
      var want = D.source[n];
      if (byCrc[want.crc32]) files[n] = byCrc[want.crc32];
    });
    var missing = D.order.filter(function (n) { return !files[n]; });
    var dark = {}, darkFound = Object.keys(D.darksource).filter(function (n) {
      var c = D.darksource[n].crc32;
      if (byCrc[c]) dark[n] = byCrc[c];
      return !!byCrc[c];
    });
    if (missing.length && dark.crom0 && dark.vroma0) {        // a Darksoft-style folder: back to the MAME files
      var made = fromDarksoft(D, dark);
      missing.forEach(function (n) {
        if (made[n] && crc32(made[n]) === D.source[n].crc32) files[n] = made[n];
      });
    }
    D.order.forEach(function (n) {
      var state = files[n] ? "ok" : byName[n] && byName[n] !== D.source[n].crc32 ? "other" : "missing";
      status.push({ name: n, state: state });
    });
    var ok = status.every(function (s) { return s.state === "ok"; });
    return { files: files, status: status, ok: ok, empty: all.length === 0, darksoft: darkFound.length > 0 };
  }

  function fromDarksoft(D, dark) {
    var out = {}, c = dark.crom0, v = dark.vroma0;
    if (dark.prom) out["022-p1.p1"] = dark.prom;
    if (dark.srom) out["022-s1.s1"] = dark.srom;
    if (dark.m1rom) out["022-m1.m1"] = dark.m1rom;
    var c12 = D.source["022-c1.c1"].size * 2, pairs = [["022-c1.c1", "022-c2.c2", 0, c12],
      ["022-c3.c3", "022-c4.c4", c12, c12 + D.source["022-c3.c3"].size * 2]];
    pairs.forEach(function (p) {
      var a = new Uint8Array((p[3] - p[2]) / 2), b = new Uint8Array(a.length);
      for (var i = p[2], j = 0; i < p[3]; i += 4, j += 2) {
        a[j] = c[i]; a[j + 1] = c[i + 1]; b[j] = c[i + 2]; b[j + 1] = c[i + 3];
      }
      out[p[0]] = a; out[p[1]] = b;
    });
    out["022-v11.v11"] = v.slice(0, D.source["022-v11.v11"].size);
    out["022-v22.v22"] = v.slice(D.vrombOffset, D.vrombOffset + D.source["022-v22.v22"].size);
    return out;
  }

  // The original MAME files -> Blue's Journey Plus's, each checked against its checksum.
  async function patch(D, src) {
    var blob = await inflateRaw(fromBase64(D.blob)), out = {};
    if (blob.length !== D.blobSize) throw new Error("The patch data didn't unpack whole. Reload the page and try again.");
    D.order.forEach(function (n) {
      var t = D.target[n], s = src[n], b = new Uint8Array(t.size), at = t.at;
      b.set(s.subarray(0, Math.min(s.length, t.size)));
      t.runs.forEach(function (r) { b.set(blob.subarray(at, at + r[1]), r[0]); at += r[1]; });
      if (crc32(b) !== t.crc32) throw new Error(n + " came out wrong after patching. Please report this.");
      out[n] = b;
    });
    return out;
  }

  function darksoft(D, f) {
    function interleave(a, b) {
      var o = new Uint8Array(a.length * 2);
      for (var i = 0, j = 0; i < a.length; i += 2, j += 4) { o[j] = a[i]; o[j + 1] = a[i + 1]; o[j + 2] = b[i]; o[j + 3] = b[i + 1]; }
      return o;
    }
    var lo = interleave(f["022-c1.c1"], f["022-c2.c2"]), hi = interleave(f["022-c3.c3"], f["022-c4.c4"]);
    var crom = new Uint8Array(lo.length + hi.length); crom.set(lo); crom.set(hi, lo.length);
    var v22 = f["022-v22.v22"], vrom = new Uint8Array(D.vrombOffset + v22.length);
    vrom.set(f["022-v11.v11"]); vrom.set(v22, D.vrombOffset);
    return { prom: f["022-p1.p1"], srom: f["022-s1.s1"], m1rom: f["022-m1.m1"], crom0: crom, vroma0: vrom,
             fpga: new TextEncoder().encode("13") };
  }

  // One system's package as [{name, data}] (release.py's PACKAGES, the same entries its private/ folders get).
  async function packageFiles(D, pkg, built) {
    var enc = new TextEncoder(), dark = null, out = [];
    for (var i = 0; i < pkg.entries.length; i++) {
      var e = pkg.entries[i], path = e[0], kind = e[1], arg = e[2], data;
      if (kind === "file") data = built[arg];
      else if (kind === "darksoft") data = (dark = dark || darksoft(D, built))[arg];
      else if (kind === "zip") data = await writeZip(arg.map(function (n) { return { name: n, data: built[n] }; }));
      else if (kind === "dat" || kind === "list") data = enc.encode(D.texts[kind]);
      else data = enc.encode(arg);
      out.push({ name: path, data: data });
    }
    return out;
  }

  var api = { crc32: crc32, readZip: readZip, writeZip: writeZip, identify: identify, patch: patch,
              darksoft: darksoft, packageFiles: packageFiles,
              buildPackage: async function (D, pkg, built) { return writeZip(await packageFiles(D, pkg, built)); } };
  if (typeof module !== "undefined") module.exports = api;
  else root.BJPatcher = api;
})(this);
