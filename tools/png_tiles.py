"""Minimal PNG read / write (no PIL): an indexed picture out, and any 8-bit PNG back in as palette indices.

write_indexed(path, rows, palette): rows = [[index, ...], ...], palette = [(r, g, b), ...] (index 0 transparent).
read_indices(path, palette): the picture's pixels as indices into palette - each pixel's colour matched to the
nearest palette colour (so an editor that reorders the palette or saves RGB(A) still round-trips); fully
transparent pixels are index 0.
"""
import struct
import zlib


def _chunk(kind, data):
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def write_indexed(path, rows, palette):
    h, w = len(rows), len(rows[0])
    raw = b"".join(b"\0" + bytes(r) for r in rows)
    png = b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 3, 0, 0, 0))
    png += _chunk(b"PLTE", b"".join(bytes(c) for c in palette))
    png += _chunk(b"tRNS", b"\0") + _chunk(b"IDAT", zlib.compress(raw, 9)) + _chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    return a if pa <= pb and pa <= pc else b if pb <= pc else c


def read_indices(path, palette):
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise SystemExit("%s: not a PNG" % path)
    pos, idat, plte, trns = 8, b"", [], b""
    while pos < len(data):
        n, kind = struct.unpack(">I4s", data[pos:pos + 8])
        body = data[pos + 8:pos + 8 + n]
        if kind == b"IHDR":
            w, h, depth, ctype, _, _, interlace = struct.unpack(">IIBBBBB", body)
        elif kind == b"PLTE":
            plte = [tuple(body[i:i + 3]) for i in range(0, n, 3)]
        elif kind == b"tRNS":
            trns = body
        elif kind == b"IDAT":
            idat += body
        pos += 12 + n
    if interlace:
        raise SystemExit("%s: interlaced PNGs aren't supported" % path)
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    if depth != 8 and not (ctype == 3 and depth in (1, 2, 4)) or depth == 16:
        raise SystemExit("%s: use an 8-bit (or indexed) PNG" % path)
    bpp = max(1, channels * depth // 8)
    stride = (w * channels * depth + 7) // 8
    raw, out, prev = zlib.decompress(idat), [], bytearray(stride)
    for y in range(h):
        f, line = raw[y * (stride + 1)], bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            a = line[i - bpp] if i >= bpp else 0
            b, c = prev[i], prev[i - bpp] if i >= bpp else 0
            line[i] = (line[i] + (0, a, b, (a + b) // 2, _paeth(a, b, c))[f]) & 255
        prev = line
        row = []
        for x in range(w):
            if ctype == 3:
                v = (line[x * depth // 8] >> (8 - depth - (x * depth) % 8)) & ((1 << depth) - 1)
                alpha = trns[v] if v < len(trns) else 255
                rgb = plte[v]
            else:
                px = line[x * channels:(x + 1) * channels]
                rgb = tuple(px[:3]) if channels >= 3 else (px[0],) * 3
                alpha = px[-1] if ctype in (4, 6) else 255
            if alpha == 0:
                row.append(0)
            else:
                row.append(min(range(1, len(palette)), key=lambda i: sum((rgb[k] - palette[i][k]) ** 2 for k in range(3))))
        out.append(row)
    return out
