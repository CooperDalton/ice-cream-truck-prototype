"""Batch 'stops' (style H): dairy farm, gas station and garden supply stops, the depot, and the gun crate wreck.
Every set piece sits on the +X side of a road chunk: root at the road edge, buildings within x 0..20, y -10..10,
entrances facing the road (-X)."""
from style_H import *

SPACING = 60

# ---------------------------------------------------------------- pixel font with digits
FONT2 = dict(FONT)
FONT2.update({
    '0': ("###", "#.#", "#.#", "#.#", "###"), '2': ("##.", "..#", ".#.", "#..", "###"),
    '4': ("#.#", "#.#", "###", "..#", "..#"), '5': ("###", "#..", "##.", "..#", "##."),
    '6': (".##", "#..", "###", "#.#", "###"), '7': ("###", "..#", ".#.", ".#.", ".#."),
    '8': ("###", "#.#", "###", "#.#", "###"), '9': ("###", "#.#", "###", "..#", "##."),
    '.': ("...", "...", "...", "...", ".#."), '-': ("...", "...", "###", "...", "..."),
    '+': ("...", ".#.", "###", ".#.", "..."), 'J': ("..#", "..#", "..#", "#.#", ".#."),
    'Q': (".#.", "#.#", "#.#", "##.", ".##"), '$': (".##", "##.", ".#.", ".##", "##."),
})


def txt(c, s, x, y, col, k=1, shadow=None):
    """3x5 pixel font with digits. (x, y) is the top-left texel (y counts up from the bottom)."""
    if shadow:
        txt(c, s, x + k, y - k, shadow, k)
    for ch in s:
        for r, row in enumerate(FONT2.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)
        x += 4 * k


def txt_c(c, s, cx, y, col, k=1, shadow=None):
    txt(c, s, cx - text_w(s, k) // 2, y, col, k, shadow)


# ---------------------------------------------------------------- naming, sockets
def asset_name(root):
    return root.name[:-5] if root.name.endswith(" root") else root.name


def socket(kit, root, purpose, loc, rot=(0, 0, 0)):
    s = kit.empty(f"{asset_name(root)} socket {purpose}", root, loc, rot)
    s.empty_display_size = 0.4
    return s


def prefixed(fn):
    """Build, then prefix every descendant name with the asset name."""
    def build(kit, root):
        fn(kit, root)
        P = asset_name(root)
        stack = list(root.children)
        while stack:
            ob = stack.pop()
            stack.extend(ob.children)
            if not ob.name.startswith(P):
                ob.name = f"{P} {ob.name}"
    return build


# ---------------------------------------------------------------- geometry helpers
def block(kit, name, parent, x0, x1, y0, y1, z0, z1, mat, tile=2.0, rot=(0, 0, 0)):
    """Axis-aligned box from extents with world-scaled UVs (use REPEAT textures)."""
    t = tile
    yz, xz, xy = (y0 / t, z0 / t, y1 / t, z1 / t), (x0 / t, z0 / t, x1 / t, z1 / t), (x0 / t, y0 / t, x1 / t, y1 / t)
    return tbox(kit, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat, parent,
                rot=rot, uv={'px': yz, 'nx': yz, 'py': xz, 'ny': xz, 'pz': xy, 'nz': xy})


def pad(kit, name, parent, x0, x1, y0, y1, mat, tile=2.0, z=0.0, th=0.06):
    return tbox(kit, name, ((x0 + x1) / 2, (y0 + y1) / 2, z - th / 2), (x1 - x0, y1 - y0, th), mat, parent,
                uv={'all': (x0 / tile, y0 / tile, x1 / tile, y1 / tile)})


def holey_wall(kit, name, parent, x0, x1, y0, y1, z0, z1, holes, mat, tile=2.0):
    """Wall running along Y split into boxes around rectangular holes (ya, yb, za, zb)."""
    ys = sorted({y0, y1} | {h[0] for h in holes} | {h[1] for h in holes})
    for i in range(len(ys) - 1):
        ya, yb = ys[i], ys[i + 1]
        ym = (ya + yb) / 2
        z = z0
        for za, zb in sorted((h[2], h[3]) for h in holes if h[0] <= ym <= h[1]) + [(z1, z1)]:
            if za > z + 1e-4:
                block(kit, f"{name} {i}", parent, x0, x1, ya, yb, z, za, mat, tile)
            z = max(z, zb)


def frame(kit, name, parent, x, ya, yb, za, zb, mat, w=0.1, d=0.14):
    """Four trim boxes around a rectangular opening in a wall facing -X."""
    for i, (y0, y1, z0, z1) in enumerate(((ya - w, yb + w, za - w, za), (ya - w, yb + w, zb, zb + w),
                                          (ya - w, ya, za, zb), (yb, yb + w, za, zb))):
        block(kit, f"{name} {i}", parent, x - d, x, y0, y1, z0, z1, mat)


def prism(kit, name, prof, x0, x1, mat, parent, tile=(2.0, 2.0), caps=True):
    """Extrude a convex YZ profile along X. Sides: u along x, v along z; caps: planar (y, z)."""
    tu, tv = tile
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    A = [bm.verts.new((x0, y, z)) for y, z in prof]
    B = [bm.verts.new((x1, y, z)) for y, z in prof]

    def face(vs, uvs):
        f = bm.faces.new(vs)
        for lp, c in zip(f.loops, uvs):
            lp[uvl].uv = c

    n = len(prof)
    for i in range(n):
        j = (i + 1) % n
        (ya, za), (yb, zb) = prof[i], prof[j]
        va, vb = (za / tv, zb / tv) if abs(zb - za) > 1e-6 else (ya / tv, yb / tv)
        face((A[i], A[j], B[j], B[i]), ((x0 / tu, va), (x0 / tu, vb), (x1 / tu, vb), (x1 / tu, va)))
    if caps:
        face(A, [(y / tu, z / tv) for y, z in prof])
        face(B[::-1], [(y / tu, z / tv) for y, z in prof[::-1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def slab(kit, name, a, b, x0, x1, th, mat, parent, ov=0.35, ext=(0.3, 0.06), tile=2.0):
    """Roof slab resting on the profile edge a->b (YZ points, a.y < b.y), extruded along X with overhang."""
    dy, dz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dy, dz)
    ang = math.atan2(dz, dy)
    d = (math.cos(ang), math.sin(ang))
    n = (-math.sin(ang), math.cos(ang))
    sh = (ext[1] - ext[0]) / 2
    cy = (a[0] + b[0]) / 2 + n[0] * th / 2 + d[0] * sh
    cz = (a[1] + b[1]) / 2 + n[1] * th / 2 + d[1] * sh
    lx, ly = x1 - x0 + 2 * ov, L + ext[0] + ext[1]
    return tbox(kit, name, ((x0 + x1) / 2, cy, cz), (lx, ly, th), mat, parent, rot=(math.degrees(ang), 0, 0),
                uv={'all': (0, 0, lx / tile, ly / tile)})


def face_uv(face, rect=(0, 0, 1, 1), rest=(0.0, 0.0, 0.04, 0.04)):
    """UV dict: one face gets the full texture, the rest sample a corner."""
    return {'all': rest, face: rect}


def pickup_ring(kit, parent, loc, r=1.2):
    m = solid(kit, "pickup ring", YEL, 0.9)
    ring_mesh(kit, "pickup ring", r, r + 0.16, m, parent, (loc[0], loc[1], 0.025), segs=16)


# ---------------------------------------------------------------- shared textures
def tex_grass(rand):
    c = Canvas(32, 32, "#2f9e5e")
    c.speckle(rand, ["#38b46c", "#278a50", "#3fc47a"], 260)
    for _ in range(7):
        c.set(rand.randrange(32), rand.randrange(32), rand.choice((PINK, YEL, WHITE)))
    return c


def tex_gravel(rand):
    c = Canvas(32, 32, "#8a7090")
    c.speckle(rand, ["#a08aa8", "#6e5878", "#b8a4bc"], 300)
    return c


def tex_concrete(rand):
    c = Canvas(32, 32, "#77709e")
    c.speckle(rand, ["#6c6592", "#837cab", "#8c86b4"], 200)
    c.rect(0, 0, 31, 0, "#5a5482"); c.rect(0, 0, 0, 31, "#5a5482")
    disc(c, 20, 12, 3, "#5e5888"); disc(c, 9, 23, 2, "#5e5888")
    return c


def tex_wood(rand):
    c = Canvas(32, 32, "#d9924a")
    for y in (0, 8, 16, 24):
        c.rect(0, y, 31, y, "#8a5226")
    c.speckle(rand, ["#c47f3a", "#e8a862"], 60)
    return c


def tex_ribbed(rand, base, line, step=4):
    c = Canvas(32, 32, base)
    for x in range(0, 32, step):
        c.rect(x, 0, x, 31, line)
    c.speckle(rand, [hex_scale(base, 0.9)], 40)
    return c


def tex_stucco(rand, base):
    c = Canvas(32, 32, base)
    c.speckle(rand, [hex_scale(base, 0.88), hex_scale(base, 1.08)], 160)
    return c


def tex_hay(rand):
    c = Canvas(16, 16, "#ffd75a")
    c.speckle(rand, ["#e8b83a", "#fff0a0", "#d9a020"], 80)
    for x in range(16):
        c.set(x, rand.randrange(16), "#c98a1a")
    c.rect(0, 4, 15, 4, PINK); c.rect(0, 11, 15, 11, PINK)
    return c


def tex_sign_board(lines, w=64, h=32, bg=WHITE, border=RED):
    """lines: (text, cx, top_y, col, k, shadow)."""
    c = Canvas(w, h, bg)
    c.rect(0, 0, w - 1, 1, border); c.rect(0, h - 2, w - 1, h - 1, border)
    c.rect(0, 0, 1, h - 1, border); c.rect(w - 2, 0, w - 1, h - 1, border)
    for s, cx, y, col, k, sh in lines:
        txt_c(c, s, cx, y, col, k, sh)
    return c


# ================================================================ 1. dairy farm
def tex_barn(rand):
    c = Canvas(32, 32, "#e8304a")
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 31, "#b81838")
    c.speckle(rand, ["#ff4a62", "#c82040"], 70)
    return c


def tex_barn_door():
    c = Canvas(32, 64, "#e8304a")
    for x in range(2, 32, 4):
        c.rect(x, 0, x, 63, "#b81838")
    c.rect(0, 0, 31, 2, WHITE); c.rect(0, 61, 31, 63, WHITE); c.rect(0, 0, 2, 63, WHITE); c.rect(29, 0, 31, 63, WHITE)
    c.rect(0, 31, 31, 32, WHITE)
    for y0 in (3, 33):
        for i in range(28):
            x = 3 + i * 24 // 27
            c.rect(x, y0 + i, x + 1, y0 + i, WHITE); c.rect(30 - x - 1, y0 + i, 30 - x, y0 + i, WHITE)
    return c


def tex_milk_tank(rand):
    c = Canvas(128, 64, "#e9e4ff")
    for x in range(0, 128, 16):
        c.rect(x, 0, x, 63, "#cfc8f0")
    c.rect(0, 20, 127, 41, BLUE); c.rect(0, 19, 127, 19, WHITE); c.rect(0, 42, 127, 42, WHITE)
    for cx in (64, 0, 128):
        txt_c(c, "MILK", cx, 36, WHITE, 2, shadow=PINK)
    c.rect(0, 52, 127, 63, WHITE)  # milk drips over the top
    x = 0
    while x < 128:
        w = rand.choice((2, 3, 3, 4))
        ln = rand.randint(0, 7)
        c.rect(x, 52 - ln, x + w - 1, 52, WHITE)
        x += w + rand.choice((1, 2, 3))
    c.speckle(rand, ["#d8d2f4"], 40, 0, 18)
    return c


def tex_cow(rand, zombie):
    base, spot = (WHITE, INK) if not zombie else ("#b8f08a", "#6d42d6")
    c = Canvas(32, 32, base)
    for _ in range(8):
        cx, cy, r = rand.randrange(32), rand.randrange(3, 29), rand.randint(2, 4)
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r - 1, cx + r + 2):
                if ((x - cx) / (r + 1.5)) ** 2 + ((y - cy) / (r + 0.5)) ** 2 < 1:
                    c.set(x, y, spot)
    if zombie:  # rib wound on the +X flank (u ~ 0.25)
        c.rect(4, 11, 12, 21, DRED)
        for y in (13, 16, 19):
            c.rect(5, y, 11, y, WHITE)
        c.rect(3, 10, 13, 10, RED); c.rect(3, 22, 13, 22, RED)
        c.speckle(rand, ["#9cd870"], 50)
    return c


def tex_cow_face(zombie):
    base = WHITE if not zombie else "#b8f08a"
    c = Canvas(16, 16, base)
    if not zombie:
        c.rect(0, 11, 6, 15, INK); c.rect(0, 9, 3, 10, INK)
        for x0 in (1, 10):  # wide scared eyes, pinprick pupils
            c.rect(x0, 5, x0 + 4, 10, INK); c.rect(x0 + 1, 6, x0 + 3, 9, WHITE)
            c.set(x0 + 2, 7, INK)
        c.rect(2, 12, 5, 12, INK); c.rect(10, 12, 13, 12, INK)  # raised brows
    else:
        c.rect(9, 10, 15, 15, "#6d42d6")
        for x0 in (1, 10):
            c.rect(x0, 5, x0 + 4, 10, "#2a0f2e")
        c.rect(2, 7, 4, 8, RED); c.set(3, 8, YEL)
        c.rect(11, 6, 13, 9, RED)
        c.rect(5, 2, 6, 6, RED); c.set(5, 1, DRED)  # blood streak
        for x in range(11, 15):
            c.set(x, 12, INK)
    return c


def tex_muzzle(zombie):
    c = Canvas(16, 8, "#ffb0c8" if not zombie else "#d08aa8")
    c.rect(3, 4, 5, 6, "#8a1f3d"); c.rect(10, 4, 12, 6, "#8a1f3d")
    if zombie:
        c.rect(3, 0, 12, 2, "#2a0f2e")
        for x in range(4, 12, 2):
            c.set(x, 2, "#fff1c7")
    else:
        c.rect(6, 0, 9, 2, "#8a1f3d")  # mouth open "moo!"
    return c


def cow(kit, parent, name, loc, rz, zombie=False):
    R = kit.rand
    cw = kit.empty(name, parent, loc, (0, 0, rz))
    t_hide = tex_mat(f"{name} hide", tex_cow(R, zombie))
    hide = solid(kit, "cow zombie skin" if zombie else "cow white", "#b8f08a" if zombie else WHITE)
    t_face = tex_mat(f"{name} face", tex_cow_face(zombie))
    t_muz = tex_mat(f"{name} muzzle", tex_muzzle(zombie))
    pinkm = solid(kit, "cow pink", "#ffb0c8")
    hoof = solid(kit, "hoof", "#3a2a40", 0.15)
    horn = solid(kit, "horn", "#fff1c7")
    tube(kit, f"{name} body", [(0, -0.95, 1.12), (0, -0.8, 1.16), (0, 0.0, 1.13), (0, 0.75, 1.14), (0, 0.95, 1.08)],
         [(0.28, 0.28), (0.36, 0.37), (0.4, 0.39), (0.39, 0.37), (0.28, 0.28)], t_hide, cw, sides=8, front=(0, 0, 1),
         bulge=(0.05, 0.08))
    head = kit.empty(f"{name} head", cw, (0, -0.95, 1.32), (34, 0, 14) if zombie else (-22, 0, -12))
    tbox(kit, f"{name} head", (0, -0.25, 0), (0.44, 0.5, 0.46), t_face, head, taper=(0.86, 0.9), uv=face_uv('ny'))
    tbox(kit, f"{name} muzzle", (0, -0.53, -0.12), (0.42, 0.16, 0.26), t_muz, head, uv=face_uv('ny', rest=(0, 0.9, 0.05, 1)))
    for sx in (1, -1):
        tip = (sx * 0.3, -0.1, 0.36) if not (zombie and sx < 0) else (sx * 0.22, -0.11, 0.25)
        tube(kit, f"{name} horn {sx}", [(sx * 0.17, -0.12, 0.2), tip], [0.05, 0.016], horn, head, sides=4)
        tbox(kit, f"{name} ear {sx}", (sx * 0.3, -0.12, 0.08), (0.2, 0.05, 0.11), pinkm, head, rot=(0, sx * 20, 0))
    # legs on hip/shoulder pivots so they can fly off
    poses = {(1, -1): (-14, 0, 4), (-1, -1): (-10, 0, -4), (1, 1): (12, 0, 0), (-1, 1): (8, 0, 0)} if not zombie else \
        {(1, -1): (10, 0, 0), (-1, -1): (-6, 0, -6), (1, 1): (-4, 0, 4), (-1, 1): (14, 0, 0)}
    for (sx, sy), rot in poses.items():
        leg = kit.empty(f"{name} leg {sx} {sy}", cw, (sx * 0.22, sy * 0.62, 0.84), rot)
        if zombie and (sx, sy) == (1, -1):
            tube(kit, f"{name} leg stump", [(0, 0, 0.05), (0, 0, -0.32)], [0.11, 0.09], hide, leg, sides=6)
            tube(kit, f"{name} leg wound", [(0, 0, -0.32), (0, 0, -0.36)], [0.09, 0.07], solid(kit, "cow wound", DRED, 0.4), leg,
                 sides=6)
            tube(kit, f"{name} leg bone", [(0, 0, -0.34), (0, 0.01, -0.62), (0, 0, -0.72)], [0.035, 0.03, 0.05],
                 solid(kit, "bone", "#fff1c7"), leg, sides=4)
        else:
            tube(kit, f"{name} leg", [(0, 0, 0.05), (0, 0, -0.4), (0, 0, -0.7)], [0.11, 0.082, 0.07], hide, leg, sides=6)
        tbox(kit, f"{name} hoof", (0, 0, -0.78), (0.15, 0.17, 0.12), hoof, leg)
    lowball(kit, f"{name} udder", (0, 0.5, 0.74), (0.17, 0.16, 0.11), pinkm, cw)
    tail = kit.empty(f"{name} tail", cw, (0, 0.99, 1.2), (24, 0, 10))
    tube(kit, f"{name} tail", [(0, 0, 0), (0, 0.04, -0.3), (0, 0.02, -0.55)], [0.03, 0.025, 0.02], hide, tail, sides=4)
    lowball(kit, f"{name} tail tuft", (0, 0.02, -0.6), (0.05, 0.05, 0.08), solid(kit, "tuft", INK, 0.15), tail, smooth=False)
    if zombie:
        goo = solid(kit, "goo", ZG, 0.9, shade="#6fd83a")
        tube(kit, f"{name} drool", [(0.08, -0.6, -0.24), (0.09, -0.62, -0.4), (0.08, -0.6, -0.5)], [0.025, 0.018, 0.03], goo,
             head, sides=4, bulge=(0, 0.02))
    return cw


def round_bale(kit, parent, name, loc, rz, mat):
    b = kit.empty(name, parent, loc, (0, 0, rz))
    tube(kit, name, [(0, -0.6, 0.72), (0, 0.6, 0.72)], 0.74, mat, b, sides=8, front=(0, 0, 1), bulge=(0.04, 0.04))
    return b


def square_bale(kit, parent, name, loc, rz, mat):
    return tbox(kit, name, (loc[0], loc[1], loc[2] + 0.21), (1.0, 0.5, 0.42), mat, parent, rot=(0, 0, rz))


def fence_run(kit, name, parent, a, b, post, rail, every=2.2, rails=(0.5, 0.95)):
    a, b = Vector((a[0], a[1], 0)), Vector((b[0], b[1], 0))
    L = (b - a).length
    n = max(2, math.ceil(L / every) + 1)
    for i in range(n):
        p = a.lerp(b, i / (n - 1))
        tbox(kit, f"{name} post {i}", (p.x, p.y, 0.62), (0.14, 0.14, 1.24), post, parent)
    ang = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    m = (a + b) / 2
    for z in rails:
        tbox(kit, f"{name} rail {z}", (m.x, m.y, z), (L, 0.06, 0.14), rail, parent, rot=(0, 0, ang))


def barn(kit, root, loc):
    R = kit.rand
    b = kit.empty("barn", root, loc)
    t_wall = tex_mat("barn wall", tex_barn(R), ext='REPEAT')
    t_roof = tex_mat("barn roof", tex_ribbed(R, STEEL, "#a9a2e0", 4), ext='REPEAT')
    t_door = tex_mat("barn door", tex_barn_door())
    t_hay = tex_mat("barn hay", tex_hay(R), ext='REPEAT')
    white, ink = solid(kit, "trim", WHITE), solid(kit, "barn dark", INK, 0.1)
    glow = solid(kit, "barn window glow", "#ffd36b", 0.9)
    D = 10.0
    prof = [(-4, 0), (4, 0), (4, 4), (3, 6.1), (0, 7.4), (-3, 6.1), (-4, 4)]
    prism(kit, "barn walls", prof, 0, D, t_wall, b)
    roof = [(-4, 4), (-3, 6.1), (0, 7.4), (3, 6.1), (4, 4)]
    for i in range(4):
        slab(kit, f"barn roof {i}", roof[i], roof[i + 1], 0, D, 0.14, t_roof, b,
             ext=(0.4 if i == 0 else 0.08, 0.4 if i == 3 else 0.08))
    for x in (0.0, D):
        for y in (-4, 4):
            tbox(kit, "corner trim", (x, y, 2.0), (0.18, 0.18, 4.0), white, b)
    # big door: dark opening, header, two hinged leaves (pivots at the jambs)
    tbox(kit, "door opening", (-0.02, 0, 1.85), (0.04, 3.9, 3.7), ink, b)
    tbox(kit, "door header", (-0.1, 0, 3.82), (0.2, 4.5, 0.22), white, b)
    for sy, rz in ((-1, 68), (1, -16)):
        leaf = kit.empty(f"barn door {sy}", b, (-0.14, sy * 1.95, 0), (0, 0, rz))
        tbox(kit, f"barn door {sy}", (0, -sy * 0.975, 1.8), (0.1, 1.95, 3.6), t_door, leaf,
             uv=face_uv('nx', rest=(0, 0, 0.04, 1)) | {'px': (0, 0, 1, 1)})
    for i in range(3):
        tbox(kit, f"spilled hay {i}", (-0.4 - 0.5 * i, -0.6 + 0.7 * i, 0.06), (0.5, 0.35, 0.12), t_hay, b, rot=(0, 0, 25 * i))
    # hay loft with hay spilling out, pulley beam
    tbox(kit, "loft opening", (-0.02, 0, 5.15), (0.04, 1.5, 1.3), ink, b)
    frame(kit, "loft frame", b, 0.0, -0.75, 0.75, 4.5, 5.8, white, w=0.12, d=0.12)
    tbox(kit, "loft hay", (-0.16, 0, 4.72), (0.36, 1.3, 0.4), t_hay, b)
    tbox(kit, "loft hay top", (-0.1, 0.2, 5.0), (0.24, 0.8, 0.25), t_hay, b, rot=(14, 0, 8))
    tbox(kit, "pulley beam", (-0.55, 0, 6.35), (1.3, 0.2, 0.2), white, b)
    tube(kit, "pulley rope", [(-1.1, 0, 6.25), (-1.1, 0, 5.4)], 0.02, solid(kit, "rope", "#ffe58a"), b, sides=4)
    tube(kit, "pulley hook", [(-1.1, 0, 5.42), (-1.1, 0, 5.3), (-1.04, 0, 5.24)], 0.03, solid(kit, "hook", STEEL), b, sides=4)
    # lit windows on both long sides
    for sy in (-1, 1):
        for x in (2.6, 7.4):
            tbox(kit, "window frame", (x, sy * 4.02, 2.5), (1.1, 0.06, 1.1), white, b)
            tbox(kit, "window", (x, sy * 4.05, 2.5), (0.86, 0.06, 0.86), glow, b)
            tbox(kit, "window bar", (x, sy * 4.08, 2.5), (0.08, 0.04, 0.86), white, b)
    # cupola + weather vane on the ridge
    tbox(kit, "cupola", (5, 0, 7.55), (1.1, 1.1, 1.0), white, b)
    tbox(kit, "cupola louvre", (5, 0, 7.6), (1.14, 0.8, 0.5), ink, b)
    tbox(kit, "cupola roof", (5, 0, 8.3), (1.5, 1.5, 0.55), t_roof, b, taper=(0.06, 0.06))
    tube(kit, "vane rod", [(5, 0, 8.5), (5, 0, 9.3)], 0.025, solid(kit, "vane", YEL), b, sides=4)
    tbox(kit, "vane arrow", (5, 0, 9.15), (0.9, 0.04, 0.08), solid(kit, "vane", YEL), b)
    tbox(kit, "vane tail", (5.38, 0, 9.15), (0.18, 0.03, 0.22), solid(kit, "vane pink", PINK), b)
    return b


def milk_tank(kit, root, loc):
    R = kit.rand
    t = kit.empty("milk tank", root, loc)
    steel = solid(kit, "tank steel", STEEL, shade="#a9a2e0")
    tube(kit, "tank", [(0, 0, 0.8), (0, 0, 1.05), (0, 0, 3.3), (0, 0, 3.62), (0, 0, 3.78)], [0.3, 1.1, 1.1, 0.8, 0.26],
         tex_mat("milk tank", tex_milk_tank(R)), t, sides=10, bulge=(0.04, 0.03))
    for i in range(4):
        a = math.radians(45 + 90 * i)
        tube(kit, f"tank leg {i}", [(math.cos(a) * 0.95, math.sin(a) * 0.95, 0), (math.cos(a) * 0.82, math.sin(a) * 0.82, 1.3)],
             0.06, steel, t, sides=4)
    tube(kit, "tank band", [(0, 0, 1.25), (0, 0, 1.38)], 1.14, solid(kit, "tank pink", PINK), t, sides=10, caps=(False, False))
    # outlet pipe and valve wheel
    tube(kit, "outlet", [(0, 0, 0.82), (0, -0.2, 0.62), (0, -1.0, 0.62)], 0.07, steel, t, sides=6)
    valve = kit.empty("valve wheel", t, (0, -0.75, 0.62))
    ring_mesh(kit, "valve wheel", 0.1, 0.17, solid(kit, "valve", YEL), valve, (0, 0, 0), segs=8)
    valve.rotation_euler = (math.radians(90), 0, 0)
    # ladder up the +X side and a hinged hatch lid
    yel = solid(kit, "ladder", YEL)
    for sy in (-0.24, 0.24):
        tbox(kit, "ladder rail", (1.2, sy, 1.9), (0.05, 0.05, 3.8), yel, t)
    for i in range(10):
        tbox(kit, f"ladder rung {i}", (1.2, 0, 0.4 + i * 0.36), (0.04, 0.48, 0.04), yel, t)
    tube(kit, "hatch ring", [(0, 0, 3.78), (0, 0, 3.92)], 0.3, steel, t, sides=8)
    lid = kit.empty("hatch lid", t, (0, 0.3, 3.92), (-60, 0, 0))
    tube(kit, "hatch lid", [(0, -0.3, 0), (0, -0.3, 0.05)], 0.32, solid(kit, "lid", PINK), lid, sides=8)
    return t


def milk_pickup(kit, root, loc):
    p = kit.empty("milk crates", root, loc)
    t_crate = tex_mat("milk crate", tex_crate())
    t_bottle = tex_mat("milk bottle", tex_bottle())
    uv = {'pz': (0.0, 0.92, 0.05, 1.0)}
    crates = [(-0.24, -0.19, 0.0, 3), (0.24, -0.2, 0.0, -4), (-0.22, 0.19, 0.0, 6), (0.25, 0.18, 0.0, -2),
              (-0.2, 0.0, 0.3, 8), (0.24, 0.02, 0.3, -6), (0.02, 0.04, 0.6, 14)]
    for i, (x, y, z, r) in enumerate(crates):
        tbox(kit, f"crate {i}", (x, y, z + 0.15), (0.44, 0.34, 0.3), t_crate, p, rot=(0, 0, r), uv=uv)
    for i, (x, y, z) in enumerate(((-0.08, -0.04, 0.65), (0.12, -0.04, 0.65), (-0.08, 0.12, 0.65), (0.12, 0.12, 0.65),
                                   (-0.3, -0.06, 0.35), (-0.1, 0.06, 0.35), (0.6, -0.5, 0.0))):
        tube(kit, f"bottle {i}", [(0, 0, 0), (0, 0, 0.22), (0, 0, 0.3), (0, 0, 0.36)], [0.055, 0.055, 0.028, 0.03],
             t_bottle, p, sides=6, loc=(x, y, z))
    lying = kit.empty("tipped bottle", p, (0.55, 0.45, 0.055), (90, 0, 60))
    tube(kit, "tipped bottle", [(0, 0, -0.18), (0, 0, 0.04), (0, 0, 0.12), (0, 0, 0.18)], [0.055, 0.055, 0.028, 0.03],
         t_bottle, lying, sides=6)
    splat(kit, "milk puddle", (0.85, 0.75), 0.3, solid(kit, "milk", WHITE, 0.5), p, z=0.012)
    pickup_ring(kit, p, (0, 0), 1.15)
    return p


@prefixed
def build_dairy(kit, root):
    R = kit.rand
    t_grass = tex_mat("grass", tex_grass(R), 0.15, ext='REPEAT')
    t_gravel = tex_mat("gravel", tex_gravel(R), 0.15, ext='REPEAT')
    t_hay = tex_mat("hay", tex_hay(R), ext='REPEAT')
    pad(kit, "ground", root, 0, 20, -10, 10, t_grass, tile=4)
    pad(kit, "driveway", root, 0, 8.7, 1.4, 5.6, t_gravel, tile=3, z=0.012, th=0.04)
    pad(kit, "pickup apron", root, 0, 4.4, -2.6, 1.4, t_gravel, tile=3, z=0.012, th=0.04)
    barn(kit, root, (8.6, 3.5, 0))
    milk_tank(kit, root, (11.8, -2.7, 0))
    milk_pickup(kit, root, (2.3, -0.7, 0))
    socket(kit, root, "pickup", (2.3, -0.7, 0), (0, 0, 90))

    # roadside sign
    sign = kit.empty("farm sign", root, (0.7, -4.6, 0))
    wood = tex_mat("wood", tex_wood(R), ext='REPEAT')
    for sy in (-1.05, 1.05):
        tbox(kit, "sign post", (0, sy, 0.95), (0.13, 0.13, 1.9), wood, sign)
    board = tex_sign_board([("FRESH", 32, 28, RED, 2, None), ("MILK", 32, 14, BLUE, 2, None)])
    for x0 in (5, 56):  # little milk bottles
        board.rect(x0, 6, x0 + 3, 14, WHITE); board.rect(x0, 6, x0 + 3, 8, BLUE); board.rect(x0 + 1, 15, x0 + 2, 18, PINK)
        board.rect(x0 - 1, 5, x0 + 4, 5, INK)
    tbox(kit, "sign board", (0, 0, 1.5), (0.08, 2.6, 1.3), tex_mat("farm sign", board), sign,
         uv={'all': (0.0, 0.0, 0.03, 0.03), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})

    # paddock: fence with a broken -X section where the zombie cow is pushing out
    post, rail = solid(kit, "fence post", WHITE, 0.35), solid(kit, "fence rail", WHITE, 0.35)
    x0, x1, y0, y1 = 5.4, 18.2, -9.5, -4.6
    fence_run(kit, "fence S", root, (x0, y0), (x1, y0), post, rail)
    fence_run(kit, "fence N", root, (x0, y1), (x1, y1), post, rail)
    fence_run(kit, "fence E", root, (x1, y0), (x1, y1), post, rail)
    fence_run(kit, "fence W a", root, (x0, y0), (x0, -8.4), post, rail, every=3)
    fence_run(kit, "fence W b", root, (x0, -6.2), (x0, y1), post, rail, every=3)
    for i, (y, rot) in enumerate(((-7.6, (70, 10, 30)), (-7.0, (10, 64, -20)))):
        tbox(kit, f"broken rail {i}", (x0 - 0.5 - 0.3 * i, y, 0.2 + 0.25 * i), (0.06, 1.6, 0.14), rail, root, rot=rot)
    cow(kit, root, "scared cow A", (10.3, -7.2, 0), 206)
    cow(kit, root, "scared cow B", (14.6, -6.6, 0), 146)
    cow(kit, root, "zombie cow", (4.1, -7.3, 0), -96, zombie=True)

    # hay: round bales by the barn, square bales by the crates and in the paddock
    round_bale(kit, root, "round bale A", (6.6, 7.0, 0), 12, t_hay)
    round_bale(kit, root, "round bale B", (6.5, 8.9, 0), -8, t_hay)
    round_bale(kit, root, "round bale C", (16.4, -7.3, 0), 80, t_hay)
    for i, (x, y, z, r) in enumerate(((3.6, 0.6, 0, 8), (3.7, 1.15, 0, -4), (3.65, 0.85, 0.42, 92))):
        square_bale(kit, root, f"square bale {i}", (x, y, z), r, t_hay)
    for i, (x, y, z, r) in enumerate(((8.0, 9.2, 0, 4), (9.05, 9.25, 0, -3), (8.5, 9.2, 0.42, 2))):
        square_bale(kit, root, f"barn bale {i}", (x, y, z), r, t_hay)


# ================================================================ 2. gas station
def tex_fascia():
    c = Canvas(128, 16, WHITE)
    c.rect(0, 0, 127, 2, PINK); c.rect(0, 3, 127, 3, BLUE); c.rect(0, 14, 127, 15, PINK)
    txt_c(c, "GAS N SNAX", 64, 12, PINK, 2, shadow=BLUE)
    for cx in (10, 117):
        cone_icon(c, cx, 4, 6, MINT)
    return c


def tex_pump_face():
    c = Canvas(32, 64, WHITE)
    c.rect(0, 0, 31, 5, INK)
    c.rect(0, 6, 31, 29, MINT); c.rect(0, 29, 31, 30, "#22c79c")
    for y in range(9, 27, 4):
        c.rect(4, y, 27, y, "#22c79c")
    c.rect(3, 32, 28, 44, INK)
    txt(c, "9.99", 8, 42, YEL); txt(c, "GAL", 10, 36, "#7fd8ff")
    c.rect(0, 46, 31, 63, PINK)
    txt_c(c, "GAS", 16, 60, WHITE, 2, shadow="#d63a86")
    c.rect(0, 46, 31, 47, YEL)
    return c


def tex_price_sign():
    c = Canvas(48, 64, PINK)
    c.rect(0, 0, 47, 0, WHITE); c.rect(0, 63, 47, 63, WHITE); c.rect(0, 0, 0, 63, WHITE); c.rect(47, 0, 47, 63, WHITE)
    txt_c(c, "GAS", 24, 61, WHITE, 3, shadow=BLUE)
    c.rect(4, 44, 43, 44, YEL)
    c.rect(2, 2, 45, 41, INK)
    for i, (name, price, col) in enumerate((("GAS", "9.99", YEL), ("SUGAR", "1.29", WHITE), ("COCOA", "2.49", MINT),
                                            ("SNAX", "0.99", PINK))):
        y = 38 - i * 9
        txt(c, name, 4, y, col); txt(c, price, 29, y, col)
    return c


def tex_mart_sign():
    c = Canvas(96, 16, INK)
    c.rect(0, 0, 95, 0, PINK); c.rect(0, 15, 95, 15, PINK)
    txt_c(c, "MINI MART", 48, 13, YEL, 2, shadow=PINK)
    return c


def tex_candy_shelf(rand):
    """4 shelf bands of colorful candy boxes and bags (one band per 16 rows)."""
    c = Canvas(64, 64, "#3a2340")
    cols = [PINK, YEL, MINT, BLUE, ORNG, PURP, RED, WHITE, ZG]
    for band in range(4):
        x = 0
        while x < 64:
            w = rand.choice((3, 4, 5))
            h = rand.randint(9, 14)
            col = rand.choice(cols)
            c.rect(x, band * 16 + 1, x + w - 1, band * 16 + h, col)
            c.rect(x, band * 16 + h - 2, x + w - 1, band * 16 + h - 2, rand.choice((WHITE, INK, YEL)))
            c.set(x + w // 2, band * 16 + 4, WHITE)
            x += w + 1
        c.rect(0, band * 16, 63, band * 16, "#e9e4ff")
    return c


def tex_baking_shelf(rand):
    c = Canvas(64, 64, "#3a2340")
    for band in range(4):
        x = 0
        while x < 64:
            kind = rand.random()
            if kind < 0.45:  # sugar sack
                w = 8
                c.rect(x, band * 16 + 1, x + w - 1, band * 16 + 12, "#e8c48a")
                c.rect(x + 1, band * 16 + 13, x + w - 2, band * 16 + 13, "#e8c48a")
                c.rect(x, band * 16 + 3, x + w - 1, band * 16 + 3, BLUE)
                txt(c, "S", x + 2, band * 16 + 10, BLUE)
            elif kind < 0.8:  # cocoa box
                w = 5
                c.rect(x, band * 16 + 1, x + w - 1, band * 16 + 11, "#8a4a2a")
                c.rect(x, band * 16 + 8, x + w - 1, band * 16 + 9, PINK)
            else:  # syrup bottle
                w = 3
                c.rect(x, band * 16 + 1, x + w - 1, band * 16 + 9, CHOC); c.rect(x + 1, band * 16 + 10, x + 1, band * 16 + 12, RED)
            x += w + 1
        c.rect(0, band * 16, 63, band * 16, "#e9e4ff")
    return c


def tex_cooler_doors(rand):
    c = Canvas(64, 32, STEEL)
    for x0 in range(0, 64, 16):
        c.rect(x0 + 2, 2, x0 + 13, 29, "#7fd8ff")
        for y in (6, 14, 22):
            c.rect(x0 + 2, y, x0 + 13, y, "#c7c0e8")
            for bx in range(x0 + 3, x0 + 13, 2):
                c.rect(bx, y + 1, bx, y + 5, rand.choice((PINK, YEL, MINT, RED, BLUE, ORNG)))
        c.rect(x0 + 12, 12, x0 + 12, 18, INK)
    return c


def tex_checker():
    c = Canvas(16, 16, "#e8e0ff")
    c.rect(0, 0, 7, 7, "#8f66e6"); c.rect(8, 8, 15, 15, "#8f66e6")
    return c


def tex_aisle(word, bg):
    c = Canvas(32, 8, bg)
    txt_c(c, word, 16, 6, WHITE)
    return c


def tex_ice():
    c = Canvas(32, 16, WHITE)
    c.rect(0, 0, 31, 3, BLUE)
    txt_c(c, "ICE", 16, 13, BLUE, 2)
    return c


def sugar_sack(kit, parent, name, loc, rot, t_sack, tie, s=1.0):
    p = kit.empty(name, parent, loc, rot, (s, s, s))
    tube(kit, name, [(0, 0, 0), (0, 0, 0.14), (0.01, 0, 0.4), (0.03, 0.01, 0.55), (0.04, 0.01, 0.62), (0.04, 0.01, 0.66),
                     (0.05, 0.01, 0.73)], [(0.24, 0.18), (0.27, 0.2), (0.24, 0.18), (0.13, 0.1), (0.04, 0.04),
                                           (0.035, 0.035), (0.08, 0.06)], t_sack, p, sides=8)
    tube(kit, name + " tie", [(0.04, 0.01, 0.6), (0.04, 0.01, 0.635)], 0.05, tie, p, sides=6)
    return p


def cocoa_bag(kit, parent, name, loc, rz, t_cocoa):
    b = kit.empty(name, parent, loc, (0, 0, rz), (1.4, 1.4, 1.4))
    tbox(kit, name, (0, 0, 0.17), (0.2, 0.12, 0.34), t_cocoa, b, taper=(1.0, 0.7), uv={'pz': (0, 0, 0.1, 0.1), 'nz': (0, 0, 0.1, 0.1)})
    tbox(kit, name + " fold", (0, 0, 0.35), (0.2, 0.06, 0.04), solid(kit, "cocoa fold", CHOC), b)
    return b


def pump(kit, parent, name, loc, t_face):
    p = kit.empty(name, parent, loc)
    tbox(kit, name + " body", (0, 0, 0.85), (0.6, 0.95, 1.7), t_face, p,
         uv={'all': (0.02, 0.0, 0.08, 1.0), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})
    tbox(kit, name + " cap", (0, 0, 1.74), (0.7, 1.05, 0.08), solid(kit, "pump cap", YEL), p)
    holster = solid(kit, "holster", INK, 0.1)
    tbox(kit, name + " holster", (-0.34, 0.3, 0.95), (0.08, 0.16, 0.22), holster, p)
    tube(kit, name + " hose", [(-0.3, 0.42, 1.45), (-0.45, 0.48, 1.2), (-0.55, 0.5, 0.6), (-0.48, 0.42, 0.38),
                               (-0.42, 0.34, 0.75)], 0.035, holster, p, sides=4, front=(1, 0, 0))
    noz = kit.empty(name + " nozzle", p, (-0.4, 0.3, 0.98), (0, -20, 0))
    tbox(kit, name + " nozzle grip", (0, 0, -0.1), (0.08, 0.07, 0.22), solid(kit, "nozzle", BLUE), noz)
    tube(kit, name + " nozzle spout", [(0, 0, 0.0), (-0.02, 0, 0.12), (-0.12, 0, 0.16)], 0.022, solid(kit, "spout", STEEL), noz,
         sides=4, front=(1, 0, 0))
    return p


@prefixed
def build_gas(kit, root):
    R = kit.rand
    t_conc = tex_mat("concrete", tex_concrete(R), 0.15, ext='REPEAT')
    pad(kit, "ground", root, 0, 20, -10, 10, t_conc, tile=4)
    white, pink, yel, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "yellow", YEL), solid(kit, "dark", INK, 0.1)
    lamp = solid(kit, "light panel", "#fff6d8", 2.4)

    # canopy over the pump island
    t_fascia = tex_mat("fascia", tex_fascia())
    tbox(kit, "canopy", (5.5, -2.1, 5.05), (6.6, 10.0, 0.7), t_fascia, root,
         uv={'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1), 'ny': (0.96, 0, 1, 1), 'py': (0.96, 0, 1, 1),
             'pz': (0.975, 0.4, 0.99, 0.55), 'nz': (0.975, 0.4, 0.99, 0.55)})
    for x in (3.9, 7.1):
        for y in (-5.4, -0.6):
            tbox(kit, "canopy light", (x, y, 4.68), (1.3, 2.0, 0.04), lamp, root)
    for y in (-5.0, 0.8):
        point_light(kit, root, "canopy light", (5.5, y, 4.3), "#fff1d0", 380, 9.0, 0.6)
    t_swirl = tex_mat("column swirl", tex_swirl(), ext='REPEAT')
    for y in (-6.4, 2.2):
        tbox(kit, "canopy column", (5.5, y, 2.45), (0.42, 0.42, 4.5), t_swirl, root, uv={'all': (0, 0, 0.6, 4)})
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    tbox(kit, "pump island", (5.5, -2.1, 0.11), (1.3, 9.8, 0.22), t_haz, root,
         uv={'all': (0, 0, 8, 0.6), 'pz': (0.02, 0.02, 0.08, 0.08)})
    t_pump = tex_mat("pump face", tex_pump_face())
    pump(kit, root, "pump A", (5.5, -4.1, 0.22), t_pump)
    pump(kit, root, "pump B", (5.5, -0.1, 0.22), t_pump)
    for y in (-6.75, 2.55):
        tube(kit, "bollard", [(4.95, y, 0.22), (4.95, y, 1.1)], 0.1, yel, root, sides=6, bulge=(0, 0.05))

    # mini-mart: front wall with window openings so the candy aisle shows through
    t_wall = tex_mat("mart wall", tex_stucco(R, MINT), ext='REPEAT')
    t_roof = tex_mat("mart roof", tex_ribbed(R, "#5b5fc0", "#474aa0", 4), ext='REPEAT')
    mx0, mx1, my0, my1, H = 12.0, 19.0, -8.5, 2.5, 3.8
    holes = [(-7.9, -4.3, 0.7, 2.6), (-3.7, -0.9, 0.7, 2.6), (0.2, 1.8, 0.0, 2.6)]
    holey_wall(kit, "mart front", root, mx0, mx0 + 0.25, my0, my1, 0, H, holes, t_wall)
    block(kit, "mart side S", root, mx0, mx1, my0, my0 + 0.25, 0, H, t_wall)
    block(kit, "mart side N", root, mx0, mx1, my1 - 0.25, my1, 0, H, t_wall)
    block(kit, "mart back", root, mx1 - 0.25, mx1, my0, my1, 0, H, t_wall)
    block(kit, "mart roof", root, mx0 - 0.2, mx1 + 0.2, my0 - 0.2, my1 + 0.2, H, H + 0.25, t_roof)
    block(kit, "mart fascia", root, mx0 - 0.3, mx0 - 0.05, my0 - 0.2, my1 + 0.2, 2.9, H + 0.3, pink)
    block(kit, "mart kick", root, mx0 - 0.08, mx0, my0, my1, 0, 0.3, pink)
    tbox(kit, "mart sign", (mx0 - 0.36, -3.4, 3.42), (0.1, 6.4, 0.95), tex_mat("mart sign", tex_mart_sign(), 1.1), root,
         uv=face_uv('nx'))
    for i, (ya, yb, za, zb) in enumerate(holes):
        frame(kit, f"mart frame {i}", root, mx0 + 0.02, ya, yb, za if za > 0 else 0.0, zb, white, w=0.08, d=0.12)
        if i < 2:
            block(kit, f"mart mullion {i}", root, mx0 - 0.08, mx0 + 0.04, (ya + yb) / 2 - 0.04, (ya + yb) / 2 + 0.04, za, zb, white)
    door = kit.empty("mart door", root, (mx0 - 0.04, 1.8, 0), (0, 0, -48))
    for i, (y0, y1, z0, z1) in enumerate(((-1.6, -1.5, 0, 2.6), (-0.1, 0, 0, 2.6), (-1.6, 0, 0, 0.12), (-1.6, 0, 2.48, 2.6),
                                          (-1.5, -0.1, 1.1, 1.2))):
        block(kit, f"mart door {i}", door, -0.04, 0.04, y0, y1, z0, z1, pink if i < 4 else yel)
    # interior: checker floor, candy and baking shelves, cooler wall, counter, lights
    block(kit, "mart floor", root, mx0 + 0.25, mx1 - 0.25, my0 + 0.25, my1 - 0.25, 0, 0.03,
          tex_mat("checker floor", tex_checker(), 0.3, ext='REPEAT'), tile=1.2)
    for name, y0, y1, t_items, word, col in (
            ("candy shelf", -7.7, -4.5, tex_mat("candy shelf", tex_candy_shelf(R), 0.5), "CANDY", PINK),
            ("sugar shelf", -3.5, -1.1, tex_mat("baking shelf", tex_baking_shelf(R), 0.5), "SUGAR", BLUE)):
        sx = 14.3
        block(kit, name + " back", root, sx + 0.35, sx + 0.45, y0, y1, 0, 1.95, pink)
        for lv in range(4):
            z = 0.1 + lv * 0.46
            block(kit, f"{name} board {lv}", root, sx, sx + 0.45, y0, y1, z - 0.04, z, white)
            tbox(kit, f"{name} items {lv}", (sx + 0.2, (y0 + y1) / 2, z + 0.19), (0.3, y1 - y0 - 0.1, 0.38), t_items, root,
                 uv={'all': (0.0, lv / 4 + 0.01, 0.05, lv / 4 + 0.05), 'nx': (0, lv / 4, 1, (lv + 1) / 4)})
        tbox(kit, name + " aisle sign", (sx - 0.1, (y0 + y1) / 2, 2.85), (0.05, 1.8, 0.45),
             tex_mat(f"{name} aisle sign", tex_aisle(word, col), 0.8), root, uv=face_uv('nx'))
        tube(kit, name + " sign wire", [(sx - 0.1, (y0 + y1) / 2, 3.07), (sx - 0.1, (y0 + y1) / 2, H)], 0.012, ink, root, sides=3)
    tbox(kit, "cooler wall", (mx1 - 0.35, -3.0, 1.25), (0.2, 6.5, 2.3), tex_mat("cooler doors", tex_cooler_doors(R), 0.9), root,
         uv={'all': (0, 0, 0.05, 0.05), 'nx': (0, 0, 1, 1)})
    block(kit, "counter", root, 15.6, 17.8, 1.35, 2.2, 0, 1.0, pink)
    tbox(kit, "register", (16.2, 1.75, 1.15), (0.4, 0.35, 0.3), solid(kit, "register", BLUE), root, rot=(0, -20, 0))
    for x in (14.0, 16.8):
        for y in (-6.0, -1.0):
            tbox(kit, "ceiling light", (x, y, H - 0.03), (0.4, 2.2, 0.04), lamp, root)
    point_light(kit, root, "mart light", (15.2, -3.0, 3.3), "#fff1d0", 520, 9.0, 0.8)

    block(kit, "ac unit", root, 16.0, 17.6, -6.5, -5.0, H + 0.25, H + 1.0, solid(kit, "ac unit", STEEL, shade="#a9a2e0"))
    tube(kit, "ac fan", [(16.8, -5.75, H + 1.0), (16.8, -5.75, H + 1.04)], 0.5, ink, root, sides=8)
    block(kit, "back door", root, mx1, mx1 + 0.06, -1.5, -0.4, 0, 2.2, pink)
    # ice chest by the mart
    tbox(kit, "ice chest", (12.9, 3.25, 0.5), (1.2, 0.8, 1.0), tex_mat("ice chest", tex_ice()), root,
         uv={'all': (0.02, 0.0, 0.06, 0.05), 'nx': (0, 0, 1, 1), 'ny': (0, 0, 1, 1)})

    # pickup: pallet of sugar sacks and cocoa bags in front of the mart door
    pk = kit.empty("sugar pallet", root, (10.2, 3.7, 0))
    t_sack, t_cocoa = tex_mat("sugar sack", tex_sack(R)), tex_mat("cocoa", tex_cocoa())
    tie = solid(kit, "sack tie", PINK)
    tbox(kit, "pallet", (0, 0, 0.07), (1.5, 1.2, 0.14), tex_mat("pallet wood", tex_wood(R), ext='REPEAT'), pk,
         uv={'all': (0, 0, 1, 1)})
    sugar_sack(kit, pk, "sack lying A", (-0.35, -0.3, 0.38), (90, 0, 10), t_sack, tie, 1.25)
    sugar_sack(kit, pk, "sack lying B", (-0.3, 0.32, 0.38), (90, 0, -6), t_sack, tie, 1.25)
    sugar_sack(kit, pk, "sack standing", (0.42, 0.25, 0.14), (0, 0, -30), t_sack, tie, 1.3)
    for i, (x, y, rz) in enumerate(((0.45, -0.3, 10), (0.18, -0.38, -14), (0.0, 0.0, 30))):
        cocoa_bag(kit, pk, f"cocoa bag {i}", (x, y, 0.14 if i < 2 else 0.62), rz, t_cocoa)
    pickup_ring(kit, pk, (0, 0), 1.25)
    socket(kit, root, "pickup", (10.2, 3.7, 0), (0, 0, 90))

    # price pylon facing the road traffic (both ±Y faces)
    pyl = kit.empty("price sign", root, (1.4, 7.8, 0))
    pole = solid(kit, "pole", "#5b5fc0", shade="#474aa0")
    for x in (-0.7, 0.7):
        tube(kit, "pylon pole", [(x, 0, 0), (x, 0, 3.5)], 0.11, pole, pyl, sides=6)
    tbox(kit, "pylon sign", (0, 0, 5.05), (2.4, 0.36, 3.2), tex_mat("price sign", tex_price_sign(), 0.9), pyl,
         uv={'all': (0.02, 0.5, 0.04, 0.52), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    tbox(kit, "pylon cap", (0, 0, 6.72), (2.6, 0.5, 0.14), yel, pyl)
    t_waffle, t_sw = tex_mat("sign waffle", tex_waffle()), tex_mat("sign swirl", tex_swirl())
    tube(kit, "pylon cone", [(0, 0, 6.8), (0, 0, 7.5)], [0.04, 0.38], t_waffle, pyl, sides=8)
    tube(kit, "pylon swirl", [(0, 0, 7.46), (0, 0, 7.6), (0.02, 0, 7.72), (0, 0, 7.9), (0, 0, 8.08)],
         [0.42, 0.4, 0.3, 0.18, 0.03], t_sw, pyl, sides=8)
    lowball(kit, "pylon cherry", (0, 0, 8.14), (0.08, 0.08, 0.08), solid(kit, "cherry", RED, 0.6), pyl)

    # parking stripes and an oil drum trash can
    for i in range(4):
        block(kit, f"parking line {i}", root, 9.6, 11.6, -8.2 + i * 2.6, -8.08 + i * 2.6, 0.0, 0.012, white)
    tube(kit, "trash drum", [(11.3, -9.3, 0), (11.3, -9.3, 0.9)], 0.3, solid(kit, "drum", BLUE), root, sides=8)
    tube(kit, "trash drum band", [(11.3, -9.3, 0.55), (11.3, -9.3, 0.62)], 0.31, pink, root, sides=8, caps=(False, False))


# ================================================================ 3. garden
def tex_glass(rand):
    """2 m x 4 m tile: cyan glass, white glazing bars every metre, plants pressed against the lower panes."""
    c = Canvas(32, 64, "#8fe8f0")
    c.speckle(rand, ["#7fd8ec", "#a8f2f6"], 120)
    for _ in range(26):
        x, y = rand.randrange(32), rand.randint(2, 18)
        disc(c, x, y, rand.randint(2, 3), rand.choice(("#3fbf6a", "#2f9e5e", "#56d67e")))
    for _ in range(10):
        c.set(rand.randrange(32), rand.randint(4, 20), rand.choice((RED, PINK, YEL)))
    for i in range(10):  # glare streaks
        c.set(20 + i // 2, 40 + i, WHITE); c.set(21 + i // 2, 40 + i, WHITE); c.set(6 + i // 2, 44 + i, WHITE)
    c.rect(0, 0, 0, 63, WHITE); c.rect(15, 0, 16, 63, WHITE)
    for y in (0, 16, 37):
        c.rect(0, y, 31, y, WHITE)
    return c


def tex_berry():
    c = Canvas(16, 16, RED)
    for y in range(0, 16, 3):
        for x in range((y // 3) % 2 * 2, 16, 4):
            c.set(x, y, YEL)
    c.rect(0, 14, 15, 15, "#3fbf6a")
    return c


def tex_berry_pile(rand):
    c = Canvas(16, 16, RED)
    for _ in range(12):
        x, y = rand.randrange(16), rand.randrange(16)
        c.set(x, y, DRED); c.set(x + 1, y + 1, YEL)
    c.speckle(rand, ["#3fbf6a"], 10)
    return c


def tex_mint_leaf(rand):
    c = Canvas(16, 16, "#3fd88e")
    c.speckle(rand, ["#2fb070", "#6ff0b0", "#22a060"], 90)
    return c


def tex_weave():
    c = Canvas(16, 16, "#e8b070")
    for y in range(16):
        for x in range(16):
            if (x + y) % 4 == 0 or (x - y) % 4 == 0:
                c.set(x, y, "#b87a3a")
    c.rect(0, 14, 15, 15, PINK)
    return c


def tex_soil(rand):
    c = Canvas(32, 32, "#6b3f4a")
    c.speckle(rand, ["#5a3340", "#7d4d58"], 160)
    for _ in range(40):  # straw mulch
        x, y = rand.randrange(32), rand.randrange(32)
        c.set(x, y, "#ffe58a"); c.set(x + 1, y, "#e0b84a")
    return c


def tex_awning_rows():
    c = Canvas(8, 16, WHITE)
    c.rect(0, 0, 7, 7, RED)
    return c


def strawberry(kit, parent, name, loc, s, t_berry, leaf):
    b = kit.empty(name, parent, loc, scale=(s, s, s))
    tube(kit, name, [(0, 0, -0.42), (0, 0, -0.3), (0, 0, -0.05), (0, 0, 0.12), (0, 0, 0.2)], [0.03, 0.22, 0.36, 0.3, 0.1],
         t_berry, b, sides=8, v=(0.0, 0.9))
    for i in range(5):
        a = 72 * i
        tbox(kit, f"{name} leaf {i}", (0.17 * math.cos(math.radians(a)), 0.17 * math.sin(math.radians(a)), 0.18), (0.28, 0.12, 0.03),
             leaf, b, rot=(0, -18, a))
    tube(kit, name + " stem", [(0, 0, 0.18), (0.02, 0, 0.34)], 0.035, leaf, b, sides=4)
    return b


def berry_basket(kit, parent, name, loc, t_weave, t_fill, r=0.24):
    b = kit.empty(name, parent, loc)
    tube(kit, name, [(0, 0, 0), (0, 0, 0.2)], [r * 0.75, r], t_weave, b, sides=8, caps=(True, False))
    tube(kit, name + " fill", [(0, 0, 0.12), (0, 0, 0.19)], [r * 0.96, r * 0.9], t_fill, b, sides=8, bulge=(0, 0.07))
    return b


@prefixed
def build_garden(kit, root):
    R = kit.rand
    t_grass = tex_mat("grass", tex_grass(R), 0.15, ext='REPEAT')
    t_gravel = tex_mat("gravel", tex_gravel(R), 0.15, ext='REPEAT')
    t_soil = tex_mat("soil", tex_soil(R), 0.2, ext='REPEAT')
    wood = tex_mat("wood", tex_wood(R), ext='REPEAT')
    t_berry = tex_mat("strawberry", tex_berry())
    t_pile = tex_mat("berry pile", tex_berry_pile(R), 0.4)
    t_mint = tex_mat("mint leaves", tex_mint_leaf(R), 0.35)
    t_weave = tex_mat("basket weave", tex_weave())
    leaf = solid(kit, "leaf", "#3fbf6a", shade="#2f9e5e")
    white, pink, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "dark", INK, 0.1)
    pad(kit, "ground", root, 0, 20, -10, 10, t_grass, tile=4)
    pad(kit, "path", root, 0, 11.2, 4.3, 5.5, t_gravel, tile=3, z=0.012, th=0.04)
    pad(kit, "stand apron", root, 0, 4.6, -2.4, 2.4, t_gravel, tile=3, z=0.012, th=0.04)

    # farm stand facing the road, baskets on the counter = pickup
    st = kit.empty("farm stand", root, (0, 0, 0))
    for x, h in ((1.75, 2.55), (3.9, 2.3)):
        for y in (-1.75, 1.75):
            block(kit, "stand post", st, x - 0.07, x + 0.07, y - 0.07, y + 0.07, 0, h, wood)
    block(kit, "stand counter", st, 1.7, 2.45, -1.8, 1.8, 0, 1.0, wood)
    board = tex_sign_board([("FRESH BERRIES", 32, 13, RED, 1, None), ("MINT", 32, 6, "#22a060", 1, None)], 64, 16, WHITE, PINK)
    tbox(kit, "stand front board", (1.66, 0, 0.6), (0.04, 3.3, 0.66), tex_mat("stand board", board), st, uv=face_uv('nx'))
    block(kit, "stand back", st, 3.85, 3.95, -1.8, 1.8, 0, 2.25, wood)
    block(kit, "stand shelf", st, 3.3, 3.85, -1.7, 1.7, 0.9, 0.96, wood)
    t_awn = tex_mat("stand awning", tex_awning_rows(), ext='REPEAT')
    tbox(kit, "stand roof", (2.8, 0, 2.46), (2.9, 4.1, 0.06), t_awn, st, rot=(0, 5, 0), uv={'all': (0, 0, 1, 4.1)})
    for i in range(9):
        y = -1.8 + i * 0.45
        lowball(kit, f"stand scallop {i}", (1.33, y, 2.46), (0.03, 0.23, 0.12), solid(kit, "red", RED) if i % 2 == 0 else white,
                st, smooth=False)
    head = tex_sign_board([("U-PICK", 32, 13, WHITE, 2, RED)], 64, 16, PINK, WHITE)
    tbox(kit, "stand header", (1.5, 0, 2.95), (0.08, 2.4, 0.62), tex_mat("stand header", head, 0.6), st, uv=face_uv('nx'))
    strawberry(kit, st, "giant strawberry", (3.0, 0, 3.05), 1.0, t_berry, leaf)
    tw, tm = t_weave, t_mint
    for i, (y, fill) in enumerate(((-1.25, t_pile), (-0.45, t_pile), (0.4, tm), (1.2, t_pile))):
        berry_basket(kit, st, f"counter basket {i}", (2.05, y, 1.0), tw, fill)
    for i, (y, fill) in enumerate(((-1.2, t_pile), (-0.4, tm), (0.6, t_pile))):
        berry_basket(kit, st, f"shelf basket {i}", (3.55, y, 0.96), tw, fill, 0.2)
    for i, (x, y, z, rz) in enumerate(((1.2, -1.2, 0, 8), (1.15, 1.25, 0, -12), (1.2, 1.2, 0.3, 4))):
        c = kit.empty(f"berry crate {i}", st, (x, y, z), (0, 0, rz))
        tbox(kit, f"berry crate {i}", (0, 0, 0.15), (0.6, 0.42, 0.3), wood, c, uv={'all': (0, 0, 0.3, 0.15)})
        tbox(kit, f"berry crate fill {i}", (0, 0, 0.29), (0.54, 0.36, 0.04), t_pile, c)
    pickup_ring(kit, st, (0.85, 0.0), 1.0)
    socket(kit, root, "pickup", (0.85, 0.0, 0), (0, 0, 90))

    # strawberry rows
    for r, y in enumerate((-4.3, -6.3, -8.3)):
        tbox(kit, f"berry row {r}", (11.5, y, 0.17), (12.0, 1.2, 0.34), t_soil, root, taper=(1.0, 0.6),
             uv={'all': (0, 0, 6, 0.6)})
        for i in range(7):
            x = 6.3 + i * 1.75 + R.uniform(-0.2, 0.2)
            lowball(kit, f"berry plant {r} {i}", (x, y, 0.46), (0.36, 0.32, 0.2), leaf, root, smooth=False)
            for j in range(2):
                a = R.uniform(0, 2 * math.pi)
                tbox(kit, f"berry {r} {i} {j}", (x + 0.3 * math.cos(a), y + 0.3 * math.sin(a), 0.38), (0.11, 0.11, 0.13),
                     solid(kit, "berry", RED, 0.45), root, rot=(R.uniform(0, 30), 0, R.uniform(0, 90)))
    sgn = kit.empty("row sign", root, (5.3, -3.2, 0))
    tube(kit, "row sign stake", [(0, 0, 0), (0, 0, 1.0)], 0.04, wood, sgn, sides=4)
    tbox(kit, "row sign", (0, 0, 1.05), (0.06, 0.9, 0.4),
         tex_mat("row sign", tex_sign_board([("BERRY", 16, 6, RED, 1, None)], 32, 8, WHITE, RED)), sgn, uv=face_uv('nx'))

    # mint planters with label stakes
    for i, (x, y, rz) in enumerate(((6.5, 2.9, 0), (9.0, 2.9, 0), (7.8, 7.2, 0))):
        p = kit.empty(f"mint planter {i}", root, (x, y, 0), (0, 0, rz))
        block(kit, f"planter {i}", p, -0.9, 0.9, -0.35, 0.35, 0, 0.5, wood)
        block(kit, f"planter soil {i}", p, -0.84, 0.84, -0.29, 0.29, 0.5, 0.52, t_soil)
        for j in range(3):
            lowball(kit, f"mint bush {i} {j}", (-0.55 + 0.55 * j, R.uniform(-0.05, 0.05), 0.7),
                    (0.32, 0.26, 0.26 + 0.05 * (j % 2)), solid(kit, "mint bush", "#3fd88e", shade="#22a060"), p, smooth=False)
        tube(kit, f"mint stake {i}", [(-0.95, -0.36, 0.2), (-0.95, -0.36, 1.0)], 0.025, wood, p, sides=4)
        tbox(kit, f"mint label {i}", (-0.95, -0.38, 1.0), (0.4, 0.04, 0.2),
             tex_mat(f"mint label {i}", tex_sign_board([("MINT", 16, 6, "#22a060", 1, None)], 32, 8, WHITE, MINT)), p,
             uv=face_uv('ny'))

    # greenhouse: glass prism, kick wall, hinged door and roof vent
    gh = kit.empty("greenhouse", root, (11.2, 4.9, 0))
    t_glass = tex_mat("greenhouse glass", tex_glass(R), 0.5, ext='REPEAT')
    prism(kit, "greenhouse glass", [(-2.6, 0), (2.6, 0), (2.6, 2.3), (0, 3.5), (-2.6, 2.3)], 0, 6.0, t_glass, gh, tile=(2.0, 4.0))
    block(kit, "greenhouse kick", gh, -0.06, 6.06, -2.66, 2.66, 0, 0.32, wood)
    tbox(kit, "ridge cap", (3.0, 0, 3.52), (6.3, 0.16, 0.1), white, gh)
    for sy in (-1, 1):
        tbox(kit, f"eave beam {sy}", (3.0, sy * 2.62, 2.3), (6.2, 0.1, 0.1), white, gh)
    tbox(kit, "door opening", (-0.02, 0, 1.05), (0.04, 1.2, 2.1), solid(kit, "greenhouse dark", "#1f5a4a", 0.2), gh)
    dr = kit.empty("greenhouse door", gh, (-0.06, -0.6, 0), (0, 0, 64))
    tbox(kit, "greenhouse door", (0, 0.6, 1.05), (0.06, 1.2, 2.1), t_glass, dr, uv={'all': (0.05, 0.05, 0.45, 0.5)})
    for z in (0.05, 2.05):
        tbox(kit, "door rail", (0, 0.6, z), (0.08, 1.2, 0.1), white, dr)
    vent = kit.empty("roof vent", gh, (4.0, 0, 3.5), (-28, 0, 0))
    tbox(kit, "roof vent", (0, -0.6, 0.0), (1.4, 1.2, 0.05), t_glass, vent, rot=(-24.8, 0, 0), uv={'all': (0.1, 0.6, 0.6, 0.9)})
    for i, y in enumerate((-1.2, 1.4)):
        pot = kit.empty(f"pot {i}", gh, (-0.6, y, 0))
        tube(kit, f"pot {i}", [(0, 0, 0), (0, 0, 0.35)], [0.16, 0.22], solid(kit, "pot", ORNG), pot, sides=6)
        lowball(kit, f"pot plant {i}", (0, 0, 0.55), (0.28, 0.28, 0.3), leaf, pot, smooth=False)
    # watering can
    can = kit.empty("watering can", root, (10.4, 6.6, 0), (0, 0, 30))
    tube(kit, "can", [(0, 0, 0), (0, 0, 0.3)], 0.15, solid(kit, "can", BLUE), can, sides=8)
    tube(kit, "can spout", [(0, -0.1, 0.1), (0, -0.4, 0.38)], [0.04, 0.025], solid(kit, "can", BLUE), can, sides=4)
    tube(kit, "can handle", [(0, 0.12, 0.25), (0, 0.06, 0.42), (0, -0.06, 0.42), (0, -0.1, 0.3)], 0.02, solid(kit, "yellow", YEL), can,
         sides=4, front=(1, 0, 0))


# ================================================================ 4. depot
def tex_door_slats():
    c = Canvas(16, 32, WHITE)
    for y in range(0, 32, 4):
        c.rect(0, y, 15, y, "#c7c0e8")
    c.rect(0, 0, 15, 2, PINK)
    return c


def tex_neon(rand):
    c = Canvas(112, 20, INK)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        txt_c(c, "SCOOP DEPOT", 56 + dx, 15 + dy, "#a02a6a", 2)
    txt_c(c, "SCOOP DEPOT", 56, 15, "#ffb3d9", 2)
    for cx in (7, 104):
        cone_icon(c, cx, 3, 8, MINT)
    c.rect(0, 0, 111, 0, MINT); c.rect(0, 19, 111, 19, MINT)
    return c


def tex_open():
    c = Canvas(24, 10, INK)
    c.rect(0, 0, 23, 0, RED); c.rect(0, 9, 23, 9, RED); c.rect(0, 0, 0, 9, RED); c.rect(23, 0, 23, 9, RED)
    txt_c(c, "OPEN", 12, 7, "#9ff7ff")
    return c


def tex_upgrades():
    c = Canvas(128, 40, INK)
    c.rect(0, 0, 127, 0, PINK); c.rect(0, 39, 127, 39, PINK); c.rect(0, 0, 0, 39, PINK); c.rect(127, 0, 127, 39, PINK)
    txt_c(c, "UPGRADES", 64, 37, YEL, 1)
    prices = ("90", "70", "60", "50", "40", "80", "200", "30")
    for i in range(8):
        x0 = i * 16
        cx = x0 + 8
        c.rect(x0 + 1, 9, x0 + 14, 30, "#2a1f4f")
        if i == 0:  # minigun
            for y in (17, 19, 21):
                c.rect(x0 + 2, y, x0 + 10, y, STEEL)
            c.rect(x0 + 9, 15, x0 + 13, 23, MINT); c.rect(x0 + 10, 24, x0 + 12, 27, PINK)
        elif i == 1:  # sundae shotgun
            c.rect(x0 + 2, 19, x0 + 13, 20, STEEL); c.rect(x0 + 10, 16, x0 + 13, 20, PINK)
            c.rect(x0 + 1, 20, x0 + 4, 22, WHITE); disc(c, x0 + 3, 24, 1, RED)
        elif i == 2:  # plow
            for y in range(14, 24):
                for x in range(x0 + 2 + (23 - y) // 3, x0 + 14 - (23 - y) // 3):
                    c.set(x, y, YEL if ((x + y) // 2) % 2 else INK)
            for x in range(x0 + 3, x0 + 13, 3):
                c.set(x, 13, YEL); c.set(x, 12, YEL)
        elif i == 3:  # armor plate
            c.rect(x0 + 4, 15, x0 + 11, 27, BLUE); c.rect(x0 + 5, 13, x0 + 10, 14, BLUE); c.rect(x0 + 6, 12, x0 + 9, 12, BLUE)
            c.rect(x0 + 7, 16, x0 + 8, 25, WHITE); c.rect(x0 + 5, 21, x0 + 10, 22, WHITE)
        elif i == 4:  # tires
            disc(c, cx, 20, 6, "#4a4060"); disc(c, cx, 20, 3, STEEL); disc(c, cx, 20, 1, PINK)
        elif i == 5:  # freezer: snowflake
            for k in range(-5, 6):
                c.set(cx + k, 20, MINT); c.set(cx, 20 + k, MINT); c.set(cx + k, 20 + k, WHITE); c.set(cx + k, 20 - k, WHITE)
        elif i == 6:  # Second Scoop: cone with a halo
            cone_icon(c, cx, 11, 8, PINK)
            c.rect(cx - 3, 28, cx + 3, 28, YEL); c.set(cx - 4, 27, YEL); c.set(cx + 4, 27, YEL)
        else:  # pint mags
            c.rect(cx - 4, 12, cx + 4, 25, WHITE); c.rect(cx - 4, 15, cx + 4, 21, MINT); c.rect(cx - 5, 25, cx + 5, 26, "#22c79c")
            c.rect(cx + 2, 11, cx + 4, 13, YEL)
        txt_c(c, prices[i], cx, 7, PINK if i == 6 else YEL)
    return c


def tex_terminal():
    c = Canvas(32, 24, BLUE)
    c.rect(0, 18, 31, 23, PINK)
    txt_c(c, "SHOP", 16, 22, WHITE)
    for i, w in enumerate((20, 14, 24, 10)):
        y = 14 - i * 4
        c.rect(3, y, 3 + w, y + 1, YEL if i == 1 else WHITE)
    c.rect(1, 9, 1, 11, YEL)
    return c


def tex_pegboard(rand):
    c = Canvas(64, 32, "#d9924a")
    for y in range(1, 32, 3):
        for x in range(1, 64, 3):
            c.set(x, y, "#8a5226")
    c.rect(4, 6, 5, 24, STEEL); c.rect(2, 24, 7, 27, STEEL)  # wrench
    c.rect(12, 6, 13, 22, PINK); c.rect(9, 22, 16, 26, STEEL)  # hammer
    c.rect(22, 8, 34, 14, STEEL); c.rect(34, 8, 38, 16, YEL)  # saw
    c.rect(44, 6, 45, 20, YEL); disc(c, 44, 23, 3, STEEL)  # scoop
    c.rect(52, 5, 59, 26, RED); c.rect(53, 22, 58, 24, INK)  # extinguisher
    return c


def flood_pole(kit, parent, name, loc, rz, pole, glow, h=6.0):
    p = kit.empty(name, parent, loc, (0, 0, rz))
    tube(kit, name + " pole", [(0, 0, 0), (0, 0, h), (0.5, 0, h + 0.2)], [0.1, 0.07, 0.06], pole, p, sides=6)
    tbox(kit, name + " head", (0.65, 0, h + 0.15), (0.6, 0.45, 0.16), pole, p, rot=(0, 18, 0))
    tbox(kit, name + " glow", (0.65, 0, h + 0.06), (0.5, 0.36, 0.03), glow, p, rot=(0, 18, 0))
    point_light(kit, p, name + " light", (0.9, 0, h - 0.4), "#ffe6a0", 900, 16.0, 0.5)
    return p


@prefixed
def build_depot(kit, root):
    R = kit.rand
    t_asph = tex_mat("asphalt", tex_asphalt(R), emit=0.15, ext='REPEAT')
    t_conc = tex_mat("concrete", tex_concrete(R), 0.18, ext='REPEAT')
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    t_wall = tex_mat("garage wall", tex_ribbed(R, LAV, LAV_D, 3), ext='REPEAT')
    t_roof = tex_mat("garage roof", tex_ribbed(R, "#5b5fc0", "#474aa0", 4), ext='REPEAT')
    white, pink, yel, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "yellow", YEL), solid(kit, "dark", INK, 0.1)
    lamp = solid(kit, "lamp glow", "#fff1a0", 3.0)
    pole = solid(kit, "pole", "#5b5fc0", shade="#474aa0")
    pad(kit, "ground", root, 0, 20, -10, 10, t_asph, tile=4)

    # parking pad with painted bay lines and arrows into the garage
    pad(kit, "parking pad", root, 0.4, 7.9, -2.9, 2.9, t_conc, tile=4, z=0.012, th=0.04)
    for y in (-2.75, 2.75):
        block(kit, "bay line", root, 0.4, 7.9, y - 0.08, y + 0.08, 0.0, 0.03, yel)
    for i, x in enumerate((2.0, 5.0)):
        bm = bmesh.new()
        pts = [(x - 0.9, -0.2), (x, -0.2), (x, -0.55), (x + 0.8, 0), (x, 0.55), (x, 0.2), (x - 0.9, 0.2)]
        bm.faces.new([bm.verts.new((px, py, 0.03)) for px, py in pts])
        kit.mesh_from_bmesh(f"pad arrow {i}", bm, yel, root, smooth=False)

    # garage: front wall with a 4.4 x 4.2 m door, tilt-up door hinged at the header
    g = kit.empty("garage", root, (8.0, 0, 0))
    D, W, H = 10.0, 4.5, 5.4
    holey_wall(kit, "garage front", g, 0, 0.3, -W, W, 0, H, [(-2.2, 2.2, 0, 4.2)], t_wall)
    block(kit, "garage side S", g, 0, D, -W, -W + 0.3, 0, H, t_wall)
    block(kit, "garage side N", g, 0, D, W - 0.3, W, 0, H, t_wall)
    block(kit, "garage back", g, D - 0.3, D, -W, W, 0, H, t_wall)
    block(kit, "garage roof", g, -0.3, D + 0.2, -W - 0.2, W + 0.2, H, H + 0.25, t_roof)
    block(kit, "garage roof trim", g, -0.36, -0.2, -W - 0.2, W + 0.2, H - 0.3, H + 0.3, pink)
    for (y0, y1, z0, z1) in ((-2.45, -2.2, 0, 4.2), (2.2, 2.45, 0, 4.2), (-2.45, 2.45, 4.2, 4.45)):
        block(kit, "door hazard", g, -0.06, 0.02, y0, y1, z0, z1, t_haz, tile=0.5)
    door = kit.empty("garage door", g, (0.4, 0, 4.15), (0, -88, 0))
    tbox(kit, "garage door", (0, 0, -2.08), (0.08, 4.3, 4.1), tex_mat("door slats", tex_door_slats(), ext='REPEAT'), door,
         uv={'all': (0, 0, 4, 4)})
    tbox(kit, "door handle", (-0.06, 0, -3.9), (0.06, 0.8, 0.06), yel, door)
    # interior: floor, threshold, tool wall, bench, tires, drums, lights
    block(kit, "garage floor", g, 0.3, D - 0.3, -W + 0.3, W - 0.3, 0, 0.03, t_conc, tile=4)
    block(kit, "threshold", g, 0.3, 0.7, -2.2, 2.2, 0, 0.04, t_haz, tile=0.5)
    for y in (-1.5, 1.5):
        block(kit, "guide line", g, 0.8, D - 1.0, y - 0.06, y + 0.06, 0.03, 0.045, yel)
    tbox(kit, "tool wall", (D - 0.33, 0, 2.0), (0.04, 5.0, 2.4), tex_mat("pegboard", tex_pegboard(R)), g, uv=face_uv('nx'))
    block(kit, "workbench", g, 6.0, 9.2, W - 1.0, W - 0.3, 0.9, 1.0, solid(kit, "bench", ORNG))
    for x in (6.1, 9.1):
        block(kit, "bench leg", g, x - 0.05, x + 0.05, W - 0.95, W - 0.35, 0, 0.9, ink)
    tbox(kit, "toolbox", (7.0, W - 0.65, 1.2), (0.7, 0.4, 0.4), solid(kit, "toolbox", RED), g)
    tire = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050")
    for i in range(3):
        tube(kit, f"spare tire {i}", [(1.2, -W + 1.0, i * 0.3), (1.2, -W + 1.0, i * 0.3 + 0.28)], 0.45, tire, g, sides=10)
    for i, (x, y, col) in enumerate(((2.3, -W + 0.75, BLUE), (2.95, -W + 0.8, PINK))):
        tube(kit, f"oil drum {i}", [(x, y, 0), (x, y, 0.95)], 0.3, solid(kit, f"drum {col}", col), g, sides=8)
    for x in (2.5, 6.5):
        tbox(kit, "shop light", (x, 0, H - 0.08), (0.3, 3.0, 0.06), lamp, g)
    point_light(kit, g, "garage light", (4.5, 0, 4.2), "#fff1d0", 700, 11.0, 0.8)
    for y in (-3.2, 3.2):
        tbox(kit, "wall pack", (-0.1, y, 4.6), (0.2, 0.5, 0.25), ink, g)
        tbox(kit, "wall pack glow", (-0.21, y, 4.55), (0.02, 0.4, 0.14), lamp, g)
        point_light(kit, g, "wall pack light", (-0.6, y, 4.3), "#ffe6a0", 240, 8.0, 0.3)
    # side windows glowing from inside
    for x in (2.5, 7.5):
        tbox(kit, "side window", (x, -W - 0.02, 3.0), (1.6, 0.06, 0.9), white, g)
        tbox(kit, "side window glow", (x, -W - 0.05, 3.0), (1.4, 0.04, 0.7), solid(kit, "window glow", "#ffd36b", 0.9), g)
    block(kit, "rear door", g, D, D + 0.06, 1.5, 2.6, 0, 2.2, solid(kit, "rear door", BLUE))
    tbox(kit, "rear lamp", (D + 0.12, 2.05, 2.45), (0.12, 0.3, 0.15), lamp, g)
    block(kit, "dumpster", g, D + 0.4, D + 1.5, -3.0, -1.0, 0, 1.3, solid(kit, "dumpster", MINT))
    block(kit, "dumpster lid", g, D + 0.35, D + 1.55, -3.05, -0.95, 1.3, 1.4, solid(kit, "dumpster lid", "#22c79c"))
    socket(kit, root, "truck park", (8.0 + 5.0, 0, 0), (0, 0, 90))

    # neon sign on the roof
    ns = kit.empty("neon sign", g, (0.3, 0, H + 0.25))
    for y in (-3.2, 3.2):
        tbox(kit, "neon post", (0.3, y, 0.5), (0.1, 0.1, 1.0), ink, ns)
    tbox(kit, "neon board", (0.25, 0, 1.55), (0.12, 7.6, 1.36), tex_mat("neon", tex_neon(R), 1.6), ns,
         uv={'all': (0.0, 0.0, 0.004, 0.004), 'nx': (0, 0, 1, 1)})
    point_light(kit, ns, "neon glow", (-1.2, 0, 1.4), PINK, 500, 9.0, 1.5)

    # shop annex: walk-up counter, upgrade board, terminal, Second Scoop on display
    s = kit.empty("shop", root, (9.0, 0, 0))
    t_shop = tex_mat("shop wall", tex_stucco(R, PINK), ext='REPEAT')
    y0, y1, SH = -9.8, -5.0, 4.3
    holey_wall(kit, "shop front", s, 0, 0.25, y0, y1, 0, SH, [(-9.2, -5.6, 1.1, 2.6)], t_shop)
    block(kit, "shop side S", s, 0, 5, y0, y0 + 0.25, 0, SH, t_shop)
    block(kit, "shop side N", s, 0, 5, y1 - 0.25, y1, 0, SH, t_shop)
    block(kit, "shop back", s, 4.75, 5, y0, y1, 0, SH, t_shop)
    block(kit, "shop roof", s, -0.2, 5.2, y0 - 0.2, y1 + 0.2, SH, SH + 0.2, t_roof)
    block(kit, "shop floor", s, 0.25, 4.75, y0 + 0.25, y1 - 0.25, 0, 0.03, tex_mat("checker floor", tex_checker(), 0.3, ext='REPEAT'),
          tile=1.2)
    frame(kit, "shop window frame", s, 0.02, -9.2, -5.6, 1.1, 2.6, white, w=0.08, d=0.12)
    block(kit, "shop counter", s, -0.6, 0.35, -9.3, -5.5, 1.02, 1.1, solid(kit, "counter", MINT))
    t_awn = tex_mat("awning", tex_awning(), ext='REPEAT')
    tbox(kit, "shop awning", (-0.45, -7.4, 2.85), (1.0, 4.0, 0.05), t_awn, s, rot=(0, -22, 0), uv={'all': (0, 0, 4, 1)})
    for i in range(9):
        lowball(kit, f"awning scallop {i}", (-0.95, -9.2 + i * 0.45, 2.63), (0.03, 0.23, 0.11), pink if i % 2 else white, s,
                smooth=False)
    tbox(kit, "upgrade board", (-0.05, -7.4, 3.6), (0.1, 4.4, 1.2), tex_mat("upgrade board", tex_upgrades(), 1.0), s,
         uv={'all': (0.0, 0.0, 0.004, 0.004), 'nx': (0, 0, 1, 1)})
    tbox(kit, "open sign", (0.2, -8.6, 2.2), (0.04, 0.9, 0.38), tex_mat("open sign", tex_open(), 1.8), s, uv=face_uv('nx'))
    # terminal on the counter, facing the customer
    term = kit.empty("terminal", s, (-0.25, -8.75, 1.1))
    tbox(kit, "terminal stand", (0.05, 0, 0.12), (0.12, 0.12, 0.24), ink, term)
    tbox(kit, "terminal monitor", (0.05, 0, 0.45), (0.16, 0.62, 0.46), solid(kit, "terminal case", STEEL), term, rot=(0, -10, 0))
    tbox(kit, "terminal screen", (-0.04, 0, 0.45), (0.02, 0.54, 0.38), tex_mat("terminal screen", tex_terminal(), 1.4), term,
         rot=(0, -10, 0), uv=face_uv('nx'))
    tbox(kit, "terminal keys", (-0.22, 0, 0.02), (0.22, 0.5, 0.03), ink, term)
    # Second Scoop (revival item) on a pedestal with a halo
    ss = kit.empty("second scoop", s, (-0.2, -6.2, 1.1), scale=(1.4, 1.4, 1.4))
    tube(kit, "pedestal", [(0, 0, 0), (0, 0, 0.18)], [0.14, 0.11], solid(kit, "pedestal", PURP), ss, sides=6)
    tube(kit, "ss cone", [(0, 0, 0.18), (0, 0, 0.42)], [0.01, 0.075], tex_mat("ss waffle", tex_waffle()), ss, sides=8)
    lowball(kit, "ss scoop", (0, 0, 0.47), (0.085, 0.085, 0.075), solid(kit, "ss cream", "#ff8fc8", 0.7), ss)
    lowball(kit, "ss scoop 2", (0, 0, 0.58), (0.07, 0.07, 0.06), solid(kit, "ss mint", MINT, 0.7), ss)
    ring_mesh(kit, "ss halo", 0.09, 0.16, solid(kit, "halo", YEL, 2.2), ss, (0, 0, 0.74), segs=10)
    point_light(kit, ss, "ss glow", (-0.2, 0, 0.6), YEL, 30, 2.0, 0.1)
    # shelves of parts behind the counter
    for lv in range(3):
        block(kit, f"parts shelf {lv}", s, 4.2, 4.75, -9.4, -5.4, 0.6 + lv * 0.6, 0.65 + lv * 0.6, white)
        for i in range(5):
            col = (MINT, PINK, YEL, BLUE, ORNG)[(i + lv) % 5]
            tube(kit, f"shelf pint {lv} {i}", [(4.45, -5.8 - i * 0.75, 0.65 + lv * 0.6), (4.45, -5.8 - i * 0.75, 0.9 + lv * 0.6)],
                 [0.1, 0.12], tex_mat(f"shelf pint {col}", tex_pint(col)), s, sides=6)
    point_light(kit, s, "shop light", (2.0, -7.4, 3.4), "#fff1d0", 380, 7.0, 0.6)
    socket(kit, root, "shop counter", (9.0 - 1.1, -7.4, 0), (0, 0, 90))

    # flood light poles and a tire stack by the road
    glow = solid(kit, "flood glow", "#fff6d0", 3.0)
    flood_pole(kit, root, "flood pole A", (0.8, -4.0, 0), 0, pole, glow)
    flood_pole(kit, root, "flood pole B", (0.8, 6.5, 0), 0, pole, glow)
    for i in range(4):
        tube(kit, f"stack tire {i}", [(5.0, 8.6, i * 0.28), (5.0, 8.6, i * 0.28 + 0.26)], 0.42, tire, root, sides=10)
    for i, (x, y) in enumerate(((3.0, 8.0), (3.7, 8.8))):
        tube(kit, f"yard drum {i}", [(x, y, 0), (x, y, 0.95)], 0.3, solid(kit, "drum pink", PINK), root, sides=8)


# ================================================================ 5. gun crate wreck
def tex_van_side(rand):
    """128x128 atlas: top half = +X side, bottom half = -X side (road side, with graffiti)."""
    c = Canvas(128, 128, WHITE)
    for half in (0, 64):
        sub = Canvas(128, 64, WHITE)
        sub.speckle(rand, ["#ece4ef"], 60)
        sub.rect(0, 0, 127, 8, BLUE); sub.rect(0, 9, 127, 9, YEL)
        sub.rect(0, 58, 127, 63, PINK)
        for _ in range(26):  # sprinkle confetti
            x, y = rand.randrange(128), rand.randint(12, 55)
            sub.rect(x, y, x + 1, y, rand.choice((PINK, YEL, MINT, BLUE, PURP)))
        txt_c(sub, "SPRINKLE", 64, 50, PINK, 2, shadow=BLUE)
        txt_c(sub, "EXPRESS", 64, 34, BLUE, 2)
        for _ in range(5):  # rust and dents
            disc(sub, rand.randrange(128), rand.randint(10, 56), rand.randint(1, 3), "#c96f3a")
        for hx, hy in ((20, 26), (96, 20), (110, 40)):  # zombie handprints
            sub.rect(hx, hy, hx + 3, hy + 3, ZG)
            for f in range(4):
                sub.rect(hx + f, hy + 4, hx + f, hy + 6 + (f % 2), ZG)
        sub.rect(60, 12, 62, 24, RED); sub.rect(61, 10, 61, 12, DRED)
        if half == 0:  # road side: graffiti arrow to the crate behind the van
            sub.rect(38, 12, 86, 29, "#2a1f4f")
            txt(sub, "GUNS", 56, 26, ORNG, 2, shadow=INK)
            for i in range(7):
                sub.rect(40 + i, 20 - i, 40 + i, 20 + i, YEL)
            sub.rect(47, 19, 53, 21, YEL)
        for y in range(64):
            for x in range(128):
                c.p[(y + half) * 128 + x] = sub.p[y * 128 + x]
    return c


def tex_van_cab(rand):
    c = Canvas(64, 64, WHITE)
    c.rect(0, 0, 63, 24, BLUE); c.rect(0, 25, 63, 26, YEL)
    c.rect(6, 32, 57, 58, GLASS)
    x, y = 30, 46  # cracked windshield
    for _ in range(4):
        dx, dy = rand.choice((-1, 1)), rand.choice((-1, 1))
        px, py = x, y
        for i in range(9):
            c.set(px, py, "#c7d4ff"); px += dx; py += dy * rand.choice((0, 1))
    disc(c, 30, 46, 2, "#c7d4ff")
    c.rect(14, 8, 49, 16, INK)
    for yy in range(9, 16, 2):
        c.rect(15, yy, 48, yy, STEEL)
    disc(c, 6, 12, 4, "#fff6b0"); disc(c, 57, 12, 4, "#4a3f7a")  # one headlight smashed
    return c


def tex_van_door():
    c = Canvas(16, 32, WHITE)
    c.rect(0, 0, 15, 5, BLUE); c.rect(0, 6, 15, 6, YEL); c.rect(0, 29, 15, 31, PINK)
    c.rect(3, 19, 12, 26, GLASS); c.dots([(5, 24), (6, 23), (7, 22), (8, 22)], "#c7d4ff")
    c.rect(1, 12, 2, 14, INK)
    c.rect(9, 9, 12, 12, ZG); c.rect(9, 13, 9, 15, ZG); c.rect(11, 13, 11, 16, ZG)
    return c


def tex_cardboard():
    c = Canvas(16, 16, "#d8a868")
    c.rect(0, 7, 15, 8, "#f0d8a0")
    disc(c, 11, 3, 2, PINK); c.set(10, 3, WHITE)
    c.rect(0, 0, 15, 0, "#a87a40")
    return c


def gun_crate(kit, parent, loc, rz):
    R = kit.rand
    gc = kit.empty("gun crate", parent, loc, (0, 0, rz))
    t_plank = tex_mat("planks", tex_planks())
    tbox(kit, "gun crate", (0, 0, 0.11), (0.62, 0.36, 0.22), t_plank, gc, uv={'pz': (0.0, 0.0, 0.1, 0.1)})
    tbox(kit, "crate inside", (0, 0, 0.2), (0.56, 0.3, 0.04), solid(kit, "crate dark", "#3a2340", 0.1), gc)
    straw = solid(kit, "straw", "#ffe58a", 0.45, shade="#e0b84a")
    for i in range(14):
        tbox(kit, f"straw {i}", (0, 0, 0), (0.008, 0.07, 0.008), straw, gc,
             loc=(R.uniform(-0.26, 0.26), R.uniform(-0.12, 0.12), 0.225), rot=(R.uniform(-20, 20), 0, R.uniform(0, 180)))
    lid = kit.empty("crate lid", gc, (0, 0.18, 0.22), (-105, 0, 0))
    tbox(kit, "crate lid", (0, -0.18, 0.015), (0.62, 0.36, 0.03), t_plank, lid)
    held = kit.empty("crate pistol", gc, (-0.05, -0.02, 0.27), (0, -90, -90))
    build_gun(kit, held)
    for i, col in enumerate((MINT, YEL)):
        p = kit.empty(f"crate pint {i}", gc, (0.2, -0.07 + i * 0.13, 0.24), (90, 0, 15 * i))
        tube(kit, f"crate pint {i}", [(0, 0, -0.045), (0, 0, 0.045)], [0.04, 0.045], tex_mat(f"crate pint {i}", tex_pint(col)),
             p, sides=8)
    return gc


@prefixed
def build_wreck(kit, root):
    R = kit.rand
    t_dirt = tex_mat("dirt", tex_dirt(R), emit=0.15, ext='REPEAT')
    pad(kit, "shoulder", root, 0, 8, -6.5, 6.5, t_dirt, tile=2)
    for i, (x0, x1, yy) in enumerate(((0.3, 3.4, -6.5), (1.1, 4.2, -6.9))):
        tbox(kit, f"skid mark {i}", ((x0 + x1) / 2, yy + 1.5, 0.008), (0.25, 5.0, 0.01), solid(kit, "skid", "#231c36", 0.1), root,
             rot=(0, 0, -28))
    white, ink, pink = solid(kit, "white", WHITE), solid(kit, "dark", INK, 0.1), solid(kit, "pink", PINK)
    tire = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050")

    # crashed delivery van, nose in the ditch against a snapped pole
    van = kit.empty("van", root, (3.4, 0.2, 0.05), (5, -12, 24))
    t_side = tex_mat("van side", tex_van_side(R))
    tbox(kit, "van box", (0, 0.65, 1.55), (2.1, 3.7, 2.3), t_side, van,
         uv={'px': (0, 0.5, 1, 1), 'nx': (0, 0, 1, 0.5), 'py': (0.02, 0.2, 0.05, 0.25), 'ny': (0.02, 0.2, 0.05, 0.25),
             'pz': (0.01, 0.2, 0.03, 0.22), 'nz': (0.01, 0.01, 0.03, 0.03)})
    tbox(kit, "van cab", (0, -1.75, 1.2), (2.0, 1.1, 1.7), tex_mat("van cab", tex_van_cab(R)), van, taper=(0.96, 0.8),
         uv={'ny': (0.0, 0.4, 1.0, 1.0), 'all': (0.02, 0.0, 0.06, 0.3), 'pz': (0.02, 0.6, 0.04, 0.62)})
    hood = kit.empty("van hood", van, (0, -2.3, 0.95), (-24, 6, 4))
    tbox(kit, "van hood", (0, -0.35, 0), (1.9, 0.75, 0.7), tex_mat("van grille", tex_van_cab(R)), hood, taper=(0.98, 0.9),
         uv={'ny': (0.0, 0.0, 1.0, 0.4), 'all': (0.02, 0.0, 0.06, 0.3)})
    tbox(kit, "van chassis", (0, 0, 0.42), (1.9, 5.0, 0.22), ink, van)
    tbox(kit, "van bumper", (0, 2.5, 0.5), (2.1, 0.14, 0.16), white, van)
    tbox(kit, "rear opening", (0, 2.51, 1.55), (1.9, 0.04, 2.1), solid(kit, "van dark", "#3a2350", 0.15), van)
    t_door = tex_mat("van door", tex_van_door())
    for sx, rz in ((-1, 70), (1, -96)):
        leaf = kit.empty(f"rear door {sx}", van, (sx * 1.03, 2.55, 0.5), (0, 0, rz))
        tbox(kit, f"rear door {sx}", (-sx * 0.5, 0, 1.05), (1.0, 0.06, 2.1), t_door, leaf,
             uv={'all': (0.0, 0.3, 0.1, 0.4), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    for nm, x, y, sx in (("front L", -1.0, -1.9, -1), ("rear L", -1.0, 1.7, -1), ("rear R", 1.0, 1.7, 1)):
        wheel(kit, f"van wheel {nm}", van, (x, y, 0.4), sx, tire, solid(kit, "hub", STEEL), pink).scale = (0.85, 0.85, 0.85)
    tbox(kit, "van axle stub", (1.0, -1.9, 0.32), (0.14, 0.14, 0.14), ink, van)
    loose = wheel(kit, "loose wheel", root, (6.6, -2.4, 0.13), 1, tire, solid(kit, "hub", STEEL), pink)
    loose.rotation_euler = (0, math.radians(84), math.radians(30))
    loose.scale = (0.85, 0.85, 0.85)
    puff = [solid(kit, "smoke " + c, c, 0.45) for c in ("#8a7fae", "#b3a6d9", "#6e6494")]
    for i in range(5):
        r = 0.16 + i * 0.07
        lowball(kit, f"van smoke {i}", (0.15 * math.sin(i * 1.7), -2.6 + 0.12 * i, 1.4 + i * 0.4), (r, r, r * 0.9), puff[i % 3], van,
                smooth=False)

    # snapped pole the van hit
    wood = tex_mat("pole wood", tex_wood(R), ext='REPEAT')
    tube(kit, "pole stump", [(5.4, -3.2, 0), (5.4, -3.2, 1.1), (5.45, -3.2, 1.25)], [0.16, 0.15, 0.1], wood, root, sides=6)
    fallen = kit.empty("fallen pole", root, (5.5, -3.3, 1.05), (0, 72, 12))
    tube(kit, "fallen pole", [(0, 0, 0), (0, 0, 6.0)], [0.15, 0.12], wood, fallen, sides=6)
    tbox(kit, "pole crossbar", (0, 0, 5.6), (0.1, 1.6, 0.12), wood, fallen)
    tube(kit, "dangling wire", [(0, 0.75, 5.6), (-1.5, 1.5, 4.0), (-3.0, 2.4, 3.6)], 0.02, ink, fallen, sides=3, caps=(False, False))

    # spilled boxes and the gun crate behind the open doors, a red flare marks the spot
    t_box = tex_mat("cardboard", tex_cardboard())
    for i, (x, y, s, r) in enumerate(((-0.5, 0.7, 0.5, (0, 0, 10)), (0.3, 0.6, 0.45, (0, 0, -8)))):
        tbox(kit, f"cargo box {i}", (x, 2.6, 0.45 + s / 2 + (0.5 if i else 0)), (s, s * 0.8, s), t_box, van, rot=r)
    for i, (x, y, z, s, r) in enumerate(((3.0, 4.6, 0, 0.5, (0, 0, 20)), (3.9, 5.1, 0, 0.42, (12, 8, -15)),
                                         (2.3, 5.4, 0, 0.36, (0, 0, 50)), (3.05, 4.62, 0.5, 0.34, (0, 0, -10)))):
        tbox(kit, f"spilled box {i}", (x, y, z + s / 2), (s, s * 0.8, s), t_box, root, rot=r)
    spr = [solid(kit, "sprinkle " + c, c, 0.7) for c in (PINK, BLUE, YEL, MINT, WHITE)]
    for i in range(18):
        tbox(kit, f"spilled sprinkle {i}", (0, 0, 0), (0.03, 0.1, 0.03), spr[i % 5], root,
             loc=(2.9 + R.uniform(-0.8, 0.8), 4.4 + R.uniform(-0.6, 0.6), 0.02), rot=(0, 0, R.uniform(0, 180)))
    crate = gun_crate(kit, root, (0.0, 0.0, 0.0), -15)
    crate.location = (1.3, 3.5, 0)
    crate.scale = (1.6, 1.6, 1.6)
    socket(kit, root, "gun crate", (1.3, 3.5, 0), (0, 0, -15))
    flare = kit.empty("flare", root, (1.9, 4.4, 0.04), (0, 74, 20))
    tube(kit, "flare stick", [(0, 0, 0), (0, 0, 0.26)], 0.03, solid(kit, "flare", RED), flare, sides=4)
    tube(kit, "flare flame", [(0, 0, 0.26), (0, 0, 0.36)], [0.04, 0.01], solid(kit, "flare flame", "#ff6a7a", 4.0), flare, sides=4)
    point_light(kit, root, "flare light", (1.8, 4.2, 0.4), RED, 160, 6.0, 0.2)
    for i in range(4):
        r = 0.07 + i * 0.04
        lowball(kit, f"flare smoke {i}", (2.1 + 0.22 * i, 4.4 - 0.12 * i, 0.3 + i * 0.3), (r, r, r * 0.9),
                solid(kit, "flare smoke", "#ff8fc8", 0.6), root, smooth=False)


# ================================================================ scenes
def build_truck_bare(kit, root):
    """build_truck without the crew and road: body, wheels, plow, serving window, roof dressing and turret."""
    R = kit.rand
    t_side = tex_mat("truck side", tex_truck_side(R))
    t_cab = tex_mat("cab", tex_cab(R))
    t_grille = tex_mat("grille", tex_grille())
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    t_waffle = tex_mat("sign waffle", tex_waffle())
    t_swirl = tex_mat("swirl", tex_swirl())
    t_awn = tex_mat("awning", tex_awning(), ext='REPEAT')
    pink, yel, white, ink = solid(kit, "truck pink", PINK), solid(kit, "truck yellow", YEL), solid(kit, "truck white", WHITE), \
        solid(kit, "truck dark", INK, 0.1)
    mint = solid(kit, "truck mint", MINT)
    tire = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050")
    truck = kit.empty("truck", root)
    tbox(kit, "cargo box", (0, 0.925, 1.575), (2.3, 3.65, 1.95), t_side, truck,
         uv={'px': (0, 0.5, 1, 1), 'nx': (0, 0, 1, 0.5), 'py': (0.02, 0.08, 0.3, 0.42), 'ny': (0.02, 0.08, 0.3, 0.42),
             'pz': (0.01, 0.2, 0.03, 0.22), 'nz': (0.01, 0.01, 0.03, 0.03)})
    tbox(kit, "cab", (0, -1.5, 1.42), (2.2, 1.2, 1.64), t_cab, truck, taper=(0.96, 0.84),
         uv={'ny': (0.3, 0.0, 0.97, 1.0), 'pz': (0.0, 0.7, 0.1, 0.8), 'py': (0.0, 0.7, 0.1, 0.8)})
    tbox(kit, "hood", (0, -2.42, 0.98), (2.14, 0.66, 0.76), t_grille, truck, taper=(0.98, 0.9),
         uv={'px': (0.0, 0.5, 0.05, 0.6), 'nx': (0.0, 0.5, 0.05, 0.6), 'pz': (0.0, 0.5, 0.05, 0.6)})
    tbox(kit, "chassis", (0, -0.1, 0.5), (2.0, 5.2, 0.24), ink, truck)
    for sx in (1, -1):
        for y, nm in ((-2.0, "front"), (1.85, "rear")):
            wheel(kit, f"wheel {nm} {sx}", truck, (sx * 1.02, y, 0.45), sx, tire, white, pink)
        tbox(kit, f"mirror arm {sx}", (sx * 1.18, -2.0, 1.75), (0.18, 0.04, 0.04), ink, truck)
        tbox(kit, f"mirror {sx}", (sx * 1.3, -2.0, 1.72), (0.06, 0.12, 0.24), pink, truck)
        tbox(kit, f"fender {sx}", (sx * 1.05, -2.0, 0.98), (0.3, 1.05, 0.08), pink, truck)
    plow = kit.empty("plow", truck, (0, -3.05, 0.55), (16, 0, 0))
    tbox(kit, "plow blade", (0, 0, 0), (2.5, 0.1, 0.72), t_haz, plow, uv={'all': (0, 0, 3, 1)})
    for i in range(7):
        x = -1.08 + i * 0.36
        tube(kit, f"plow tooth {i}", [(x, -0.04, -0.36), (x, -0.2, -0.36)], [(0.07, 0.03), 0.004], yel, plow, sides=4,
             side=(1, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"plow strut {sx}", (sx * 0.7, -2.88, 0.62), (0.1, 0.3, 0.1), ink, truck)
    tbox(kit, "rear bumper", (0, 2.83, 0.62), (2.2, 0.14, 0.16), white, truck)
    for (cy, cz, sy, sz) in ((0.2, 2.06, 1.62, 0.07), (0.2, 1.24, 1.62, 0.07), (-0.58, 1.65, 0.07, 0.86), (0.98, 1.65, 0.07, 0.86)):
        tbox(kit, "window frame", (1.165, cy, cz), (0.05, sy, sz), mint, truck)
    tbox(kit, "awning", (1.36, 0.2, 2.2), (0.42, 1.8, 0.04), t_awn, truck, rot=(0, 20, 0),
         uv={'pz': (0, 0, 6, 1), 'nz': (0, 0, 6, 1), 'px': (0, 0, 6, 1)})
    for i in range(9):
        y = -0.6 + i * 0.2
        lowball(kit, f"scallop {i}", (1.56, y + 0.1, 2.11), (0.02, 0.1, 0.05), pink if i % 2 else white, truck, smooth=False)
    tbox(kit, "counter", (1.27, 0.2, 1.23), (0.24, 1.6, 0.05), pink, truck)
    tbox(kit, "hatch frame", (-0.45, 1.9, 2.585), (0.78, 0.78, 0.07), pink, truck)
    tbox(kit, "hatch hole", (-0.45, 1.9, 2.6), (0.62, 0.62, 0.06), ink, truck)
    lid = kit.empty("hatch lid", truck, (-0.45, 2.29, 2.63), (-112, 0, 0))
    tbox(kit, "hatch lid", (0, -0.38, 0.02), (0.74, 0.74, 0.05), mint, lid)
    for sx in (0.42, 0.88):
        tbox(kit, f"ladder rail {sx}", (sx, 2.8, 1.65), (0.05, 0.05, 2.3), yel, truck)
    for i in range(7):
        tbox(kit, f"ladder rung {i}", (0.65, 2.8, 0.75 + i * 0.3), (0.46, 0.04, 0.04), yel, truck)
    tube(kit, "speaker", [(0.75, -0.6, 2.75), (0.75, -0.75, 2.75), (0.75, -0.95, 2.78)], [0.04, 0.07, 0.15], yel, truck,
         sides=8, side=(1, 0, 0), caps=(True, False))
    sign = kit.empty("cone sign", truck, (-0.45, -1.45, 2.24))
    tube(kit, "sign post", [(0, 0, 0), (0, 0, 0.1)], 0.05, pink, sign, sides=6)
    tube(kit, "sign cone", [(0, 0, 0.08), (0, 0, 0.5)], [0.02, 0.24], t_waffle, sign, sides=8, bulge=(0.02, 0))
    tube(kit, "sign swirl", [(0, 0, 0.48), (0, 0, 0.56), (0.01, 0, 0.6), (0.01, 0, 0.67), (-0.01, 0, 0.7), (-0.01, 0, 0.77),
                             (0, 0, 0.84)], [0.27, 0.26, 0.2, 0.19, 0.13, 0.11, 0.025], t_swirl, sign, sides=8)
    lowball(kit, "sign cherry", (0, 0, 0.88), (0.05, 0.05, 0.05), solid(kit, "cherry", RED, 0.6), sign)
    turret = kit.empty("turret", truck, (0.35, 0.25, 2.55), scale=(1.2, 1.2, 1.2))
    build_minigun(kit, turret)
    return truck


def road_strip(kit, root, y0=-22, y1=22):
    """Simple 8 m road along Y at x -8..0 (the stop's road edge is x = 0)."""
    R = kit.rand
    road = kit.empty("road strip", root)
    t_asph = tex_mat("asphalt", tex_asphalt(R), emit=0.15, ext='REPEAT')
    t_dirt = tex_mat("dirt", tex_dirt(R), emit=0.15, ext='REPEAT')
    pad(kit, "asphalt", road, -8, 0, y0, y1, t_asph, tile=2)
    pad(kit, "dirt", road, -16, 26, y0, y1, t_dirt, tile=2, z=-0.02)
    yel, white = solid(kit, "lane yellow", YEL, 0.5), solid(kit, "lane white", WHITE, 0.4)
    n = int((y1 - y0) / 2.8)
    for i in range(n):
        y = y0 + 1 + i * 2.8
        block(kit, f"lane dash {i}", road, -4.07, -3.93, y, y + 1.4, 0, 0.012, yel)
    for x in (-7.7, -0.3):
        block(kit, "edge line", road, x - 0.06, x + 0.06, y0, y1, 0, 0.012, white)
    return road


def stop_scene(builder, name, truck=((-2.1, -1.5, 0), 0)):
    def build(kit, root):
        road_strip(kit, root)
        builder(kit, kit.empty(f"{name} root", root))
        build_truck_bare(kit, kit.empty("parked truck", root, truck[0], (0, 0, truck[1])))
    return build


ASSETS = [
    ("Dairy Farm Stop", build_dairy),
    ("Gas Station Stop", build_gas),
    ("Garden Stop", build_garden),
    ("Depot", build_depot),
    ("Gun Crate Wreck", build_wreck),
]

CAM = ((-8, -17, 10), (8, 1, 1.5), 30)
AWAY = ((-2.1, -19, 0), 0)


def scene(name, builder, asset, cam, truck=((-2.1, -1.5, 0), 0)):
    return dict(name=name, build=stop_scene(builder, asset, truck), cam=cam, res=(1600, 900))


SCENES = [
    scene("dairy farm scene", build_dairy, "Dairy Farm Stop", CAM),
    scene("gas station scene", build_gas, "Gas Station Stop", ((-4, -20, 9), (8, 0, 2), 26), ((-2.1, 1.5, 0), 0)),
    scene("garden scene", build_garden, "Garden Stop", CAM),
    scene("depot scene", build_depot, "Depot", CAM, ((4.2, 0, 0), 90)),
    scene("wreck scene", build_wreck, "Gun Crate Wreck", ((-8, 9.5, 5.5), (3, 0.5, 1), 30), ((-2.1, -7, 0), 0)),
    scene("dairy pickup detail", build_dairy, "Dairy Farm Stop", ((-3, -9.5, 2.6), (3.5, -3.8, 0.8), 30), AWAY),
    scene("gas mart detail", build_gas, "Gas Station Stop", ((7.4, -5.6, 1.7), (14, -3.6, 1.3), 28), AWAY),
    scene("garden stand detail", build_garden, "Garden Stop", ((-3, -4.5, 2.3), (2.5, 0.4, 1.3), 30), AWAY),
    scene("depot counter detail", build_depot, "Depot", ((4.6, -11, 2.4), (8.6, -7.3, 2.1), 28), AWAY),
    scene("wreck crate detail", build_wreck, "Gun Crate Wreck", ((-1.6, 7.0, 2.2), (1.8, 3.3, 0.5), 30), AWAY),
]
