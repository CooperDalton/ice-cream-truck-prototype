"""Generates the PS1 pixel-art FX sprites for the Unity project (white shapes with grey shading, tinted at runtime).

python3 fx_sprites.py  ->  Zombie Ice Cream Truck/Assets/Art/Sprites/
  fx_atlas.png       128x128, 8x8 cells of 16 px. Rows (top to bottom): blobs, stars, smoke puffs, sprinkles, sparks,
                     drops, rings, ice shards. Unity's texture sheet animation counts rows from the top.
  screen_splat_N.png 64x64 big gore splats for the screen overlay (4 variants)
  vignette.png       128x128 white radial edge mask (alpha), tinted at runtime
  hitmarker.png      16x16 cross hit marker
"""
import math
import os
import random
import struct
import zlib

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../Zombie Ice Cream Truck/Assets/Art/Sprites")


def write_png(path, width, height, pixels):
    """pixels: list of rows of (r, g, b, a) 0..255, top row first."""
    raw = b"".join(b"\x00" + b"".join(struct.pack("BBBB", *p) for p in row) for row in pixels)

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def blank(size):
    return [[(0, 0, 0, 0) for _ in range(size)] for _ in range(size)]


def shade(value):
    v = max(0, min(255, int(value)))
    return (v, v, v, 255)


def blob(rand, size, lobes, spikiness, drips=0):
    """Irregular goo splat with a lighter core and 1 px darker rim."""
    img = blank(size)
    c = (size - 1) / 2
    radius = size * 0.32
    phases = [rand.uniform(0, math.tau) for _ in range(3)]
    amps = [rand.uniform(0.1, 0.25) * spikiness for _ in range(3)]

    def edge(a):
        return radius * (1 + sum(amp * math.sin(k * lobes * a / 3 + ph) for k, (amp, ph) in enumerate(zip(amps, phases), 1)))
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            d = math.hypot(dx, dy)
            r = edge(math.atan2(dy, dx))
            if d <= r:
                img[y][x] = shade(255 if d < r * 0.55 else 225 if d < r - 1.2 else 170)
    for _ in range(drips):
        x = int(c + rand.uniform(-radius, radius) * 0.7)
        top = int(c + radius * 0.5)
        for y in range(top, min(size, top + rand.randint(2, int(size * 0.35)))):
            img[y][x] = shade(200)
        for y in range(top, min(size, top + 2)):
            img[y][min(size - 1, x + 1)] = shade(200)
    for _ in range(int(size * 0.4)):
        a = rand.uniform(0, math.tau)
        d = radius * rand.uniform(1.15, 1.6)
        x, y = int(c + math.cos(a) * d), int(c + math.sin(a) * d)
        if 0 <= x < size and 0 <= y < size:
            img[y][x] = shade(210)
    return img


def star(size, points, inner, rot):
    img = blank(size)
    c = (size - 1) / 2
    outer = size * 0.48
    for y in range(size):
        for x in range(size):
            dx, dy = x - c, y - c
            a = math.atan2(dy, dx) + rot
            sector = (a % (math.tau / points)) / (math.tau / points)
            r = outer * (inner + (1 - inner) * abs(1 - 2 * sector) ** 1.6)
            d = math.hypot(dx, dy)
            if d <= r:
                img[y][x] = shade(255 if d < r * 0.5 else 215)
    return img


def puff(rand, size, density):
    img = blank(size)
    c = (size - 1) / 2
    bayer = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    blobs = [(c + rand.uniform(-2, 2), c + rand.uniform(-2, 2), size * rand.uniform(0.22, 0.32)) for _ in range(4)]
    for y in range(size):
        for x in range(size):
            v = max(1 - math.hypot(x - bx, y - by) / br for bx, by, br in blobs)
            if v <= 0:
                continue
            if v * 16 * density > bayer[y % 4][x % 4]:
                img[y][x] = shade(235 if v > 0.5 else 190)
    return img


def sprinkle(size, angle):
    img = blank(size)
    c = (size - 1) / 2
    for t in range(-4, 5):
        x = c + math.cos(angle) * t * 0.8
        y = c + math.sin(angle) * t * 0.8
        for ox in (0, 1):
            for oy in (0, 1):
                xi, yi = int(x + ox - 0.5), int(y + oy - 0.5)
                if 0 <= xi < size and 0 <= yi < size:
                    img[yi][xi] = shade(255 if abs(t) < 3 else 200)
    return img


def spark(size, arms, length):
    img = blank(size)
    c = size // 2
    for k in range(arms):
        a = k * math.tau / arms
        for t in range(int(size * length)):
            x, y = int(round(c + math.cos(a) * t)), int(round(c + math.sin(a) * t))
            if 0 <= x < size and 0 <= y < size:
                img[y][x] = shade(255 - t * 10)
    img[c][c] = shade(255)
    return img


def drop(size, stretch):
    img = blank(size)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            dy = (y - c - 2) / (size * 0.22)
            width = size * 0.22 * (1 - max(0, -dy) / stretch) if dy < 0 else size * 0.22 * math.sqrt(max(0, 1 - dy * dy))
            if abs(x - c) <= width and -stretch < dy <= 1:
                img[y][x] = shade(255 if abs(x - c) < width * 0.5 else 200)
    return img


def ring(size, radius, thickness):
    img = blank(size)
    c = (size - 1) / 2
    for y in range(size):
        for x in range(size):
            d = math.hypot(x - c, y - c)
            if abs(d - radius) <= thickness:
                img[y][x] = shade(255 if abs(d - radius) < thickness * 0.5 else 210)
    return img


def shard(rand, size):
    img = blank(size)
    pts = [(rand.uniform(0.3, 0.7) * size, rand.uniform(0, 0.15) * size), (rand.uniform(0.75, 1) * size, rand.uniform(0.4, 0.7) * size),
           (rand.uniform(0.4, 0.6) * size, rand.uniform(0.85, 1) * size), (rand.uniform(0, 0.25) * size, rand.uniform(0.3, 0.6) * size)]
    for y in range(size):
        for x in range(size):
            inside = True
            for i in range(4):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % 4]
                if (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0) < 0:
                    inside = False
            if inside:
                img[y][x] = shade(255 if (x + y) % 5 else 205)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    rand = random.Random(7)
    cell = 16
    rows = [
        [blob(rand, cell, rand.randint(3, 7), rand.uniform(0.8, 1.6), drips=rand.randint(0, 2)) for _ in range(8)],
        [star(cell, p, i, rand.uniform(0, 1)) for p, i in [(4, 0.25), (5, 0.4), (6, 0.35), (8, 0.45), (4, 0.15), (5, 0.25), (6, 0.5), (8, 0.3)]],
        [puff(rand, cell, d) for d in (1.4, 1.2, 1.0, 0.9, 1.3, 1.1, 0.8, 1.0)],
        [sprinkle(cell, k * math.pi / 8) for k in range(8)],
        [spark(cell, a, l) for a, l in [(4, 0.45), (6, 0.45), (8, 0.45), (4, 0.3), (6, 0.35), (8, 0.3), (5, 0.45), (3, 0.45)]],
        [drop(cell, s) for s in (1.5, 2.0, 2.5, 3.0, 1.5, 2.0, 2.5, 3.0)],
        [ring(cell, r, t) for r, t in [(3, 1), (4, 1), (5, 1.2), (6, 1.2), (7, 1.3), (5, 2), (6, 2), (7, 2)]],
        [shard(rand, cell) for _ in range(8)],
    ]
    atlas = blank(cell * 8)
    for r, row in enumerate(rows):
        for c, img in enumerate(row):
            for y in range(cell):
                for x in range(cell):
                    atlas[r * cell + y][c * cell + x] = img[y][x]
    write_png(os.path.join(OUT, "fx_atlas.png"), 128, 128, atlas)
    for i in range(4):
        write_png(os.path.join(OUT, f"screen_splat_{i + 1}.png"), 64, 64, blob(rand, 64, rand.randint(4, 8), 1.6, drips=rand.randint(3, 6)))
    vignette = [[(255, 255, 255, int(255 * min(1, max(0, (math.hypot(x - 63.5, y - 63.5) / 90 - 0.45) / 0.55) ** 1.5))) for x in range(128)] for y in range(128)]
    write_png(os.path.join(OUT, "vignette.png"), 128, 128, vignette)
    marker = blank(16)
    for t in range(3, 7):
        for x, y in ((t, t), (15 - t, t), (t, 15 - t), (15 - t, 15 - t)):
            marker[y][x] = shade(255)
    write_png(os.path.join(OUT, "hitmarker.png"), 16, 16, marker)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
