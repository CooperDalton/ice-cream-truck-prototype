"""Style H item batch: pints, scoop grenades, flavor tubs, bulky ingredients, gun crates, Second Scoop, sprinkles,
tip jar and the chocolate tip coin. Every asset root sits on the ground (origin at the bottom center, front -Y).
Hand-held things get `<Asset> socket hand`; two-handed things get `socket hand L` (+X) and `socket hand R` (-X).
Lids, flaps, wings and spinners are their own objects under pivots at their hinge or axis."""
from style_H import *

FL = {
    "vanilla": dict(label="VANILLA", cream="#fff1c7", shade="#f0d590", hi="#fffbea", kind="bean", chip=None,
                    tint=YEL, tint_d="#e0a81c", ink="#b0661a"),
    "chocolate": dict(label="CHOC", cream="#8a4a26", shade="#6a3418", hi="#a8643a", kind="fudge", chip="#2e140a",
                      tint="#b0602e", tint_d="#6e3a1e", ink="#6e3a1e"),
    "strawberry": dict(label="BERRY", cream="#ff9fcf", shade="#ff7dbb", hi="#ffd6ea", kind="berry", chip=RED,
                       tint=PINK, tint_d="#d63a86", ink="#d63a86"),
    "mint": dict(label="MINT", cream="#a8ffd9", shade="#7fe8bf", hi="#e0fff2", kind="chips", chip=CHOC,
                 tint=MINT, tint_d="#22c79c", ink="#119a76"),
}
FLAVORS = ("vanilla", "chocolate", "strawberry", "mint")
PAPER = "#f4ebe2"
WOOD = "#e8a85a"; WOOD_D = "#a8642a"
GOLD = "#ffd23a"; GOLD_D = "#d9901a"
LEAF = "#3fdc6e"; LEAF_D = "#1f9e4a"
SPRINKLES = (PINK, BLUE, YEL, MINT, WHITE, PURP, ORNG)

GLYPHS = {
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    '+': ("...", ".#.", "###", ".#.", "..."),
    'h': ("#.#.#", ".###.", "#####", ".###.", "#.#.#"),
}


def glyph(c, g, x, y, col, k=1):
    """Draw a GLYPHS entry; (x, y) is the top-left texel, y counts up."""
    for r, row in enumerate(GLYPHS[g]):
        for q, b in enumerate(row):
            if b == '#':
                c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)


# ---------------------------------------------------------------- builders
def lathe(kit, name, prof, mat, parent=None, sides=8, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, jit=0.0,
          half=True):
    """Surface of revolution around local Z. prof = [(r, z, v)]; r == 0 makes a pole. u = 0.5 faces -Y; with half=True
    a face (not an edge) is centered on -Y, so labels painted at u = 0.5 read flat (use ext='REPEAT' textures)."""
    R = kit.rand
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    off = 0.5 if half else 0.0
    angs = [-math.pi + 2 * math.pi * (k + off) / sides for k in range(sides)]
    rings = []
    for r, z, _ in prof:
        if r == 0:
            rings.append(bm.verts.new((0, 0, z)))
            continue
        ring = []
        for a in angs:
            rr = r + (R.uniform(-jit, jit) if jit else 0.0)
            zz = z + (R.uniform(-jit, jit) * 0.6 if jit else 0.0)
            ring.append(bm.verts.new((math.sin(a) * rr, -math.cos(a) * rr, zz)))
        rings.append(ring)
    V = [min(0.995, max(0.005, p[2])) for p in prof]
    for i in range(len(prof) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(sides):
            k2 = (k + 1) % sides
            u0, u1 = (k + off) / sides, (k + 1 + off) / sides
            if isinstance(A, list) and isinstance(B, list):
                vs, uvs = (A[k], A[k2], B[k2], B[k]), ((u0, V[i]), (u1, V[i]), (u1, V[i + 1]), (u0, V[i + 1]))
            elif isinstance(B, list):
                vs, uvs = (A, B[k2], B[k]), (((u0 + u1) / 2, V[i]), (u1, V[i + 1]), (u0, V[i + 1]))
            else:
                vs, uvs = (A[k], A[k2], B), ((u0, V[i]), (u1, V[i]), ((u0 + u1) / 2, V[i + 1]))
            fc = bm.faces.new(vs)
            for lp, c in zip(fc.loops, uvs):
                lp[uvl].uv = c
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth)


def pillow(kit, name, W, Hh, D, mat, parent, nx=6, nz=7, loc=(0, 0, 0), rot=(0, 0, 0), jit=0.0, slump=0.12):
    """Stuffed sack: front and back grids pinched together along the sides and top, flat-ish bottom. Front face uses
    the left half of the texture, back the right half."""
    R = kit.rand
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    F, B = {}, {}
    for j in range(nz):
        for i in range(nx):
            u, v = i / (nx - 1), j / (nz - 1)
            g = math.sin(math.pi * u) ** 0.55 * math.cos(0.5 * math.pi * v) ** 0.55
            x = (u - 0.5) * W * (1 + 0.08 * math.sin(math.pi * v) - slump * v * v)
            z = v * Hh - 0.035 * Hh * math.sin(math.pi * u) * v ** 4
            dj = (R.uniform(-jit, jit) if jit and 0 < i < nx - 1 and 0 < j < nz - 1 else 0.0)
            if g < 1e-6:
                F[i, j] = B[i, j] = bm.verts.new((x, 0, z))
            else:
                F[i, j] = bm.verts.new((x, -D / 2 * g - dj, z + dj * 0.5))
                B[i, j] = bm.verts.new((x, D / 2 * g + dj, z + dj * 0.5))

    def face(vs, uvs):
        keep = [(a, b) for n, (a, b) in enumerate(zip(vs, uvs)) if a not in vs[:n]]
        fc = bm.faces.new([a for a, _ in keep])
        for lp, (_, c) in zip(fc.loops, keep):
            lp[uvl].uv = c

    for j in range(nz - 1):
        for i in range(nx - 1):
            u0, u1, v0, v1_ = i / (nx - 1), (i + 1) / (nx - 1), j / (nz - 1), (j + 1) / (nz - 1)
            f = lambda u, v: (0.005 + 0.49 * u, 0.005 + 0.99 * v)
            face((F[i, j], F[i + 1, j], F[i + 1, j + 1], F[i, j + 1]), (f(u0, v0), f(u1, v0), f(u1, v1_), f(u0, v1_)))
            b = lambda u, v: (0.995 - 0.49 * u, 0.005 + 0.99 * v)
            if F[i, j + 1] is B[i, j + 1] and F[i + 1, j + 1] is B[i + 1, j + 1] and F[i, j] is B[i, j] \
                    and F[i + 1, j] is B[i + 1, j]:
                continue
            face((B[i + 1, j], B[i, j], B[i, j + 1], B[i + 1, j + 1]), (b(u1, v0), b(u0, v0), b(u0, v1_), b(u1, v1_)))
    for i in range(nx - 1):
        face((B[i, 0], B[i + 1, 0], F[i + 1, 0], F[i, 0]), ((0.5, 0.01), (0.51, 0.01), (0.51, 0.02), (0.5, 0.02)))
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth=True)


def coin_mesh(kit, name, r, t, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), sides=10):
    """Upright disc (axis along Y). Front face samples the left half of the texture, back the right half, the rim a
    thin strip at u 0..0.04."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    angs = [2 * math.pi * (k + 0.5) / sides for k in range(sides)]
    fr = [bm.verts.new((math.sin(a) * r, -t / 2, math.cos(a) * r)) for a in angs]
    bk = [bm.verts.new((math.sin(a) * r, t / 2, math.cos(a) * r)) for a in angs]

    def face(vs, uvs):
        fc = bm.faces.new(vs)
        for lp, c in zip(fc.loops, uvs):
            lp[uvl].uv = c
    face(fr[::-1], [(0.25 + 0.245 * math.sin(a), 0.5 + 0.49 * math.cos(a)) for a in angs[::-1]])
    face(bk, [(0.75 - 0.245 * math.sin(a), 0.5 + 0.49 * math.cos(a)) for a in angs])
    for k in range(sides):
        k2 = (k + 1) % sides
        face((fr[k], fr[k2], bk[k2], bk[k]), ((0.01, k / sides), (0.01, (k + 1) / sides), (0.03, (k + 1) / sides),
                                              (0.03, k / sides)))
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth=False)


def flat_poly(kit, name, pts, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Flat polygon in the local XZ plane (faces -Y) with planar UVs over its bounds."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    xs, zs = [p[0] for p in pts], [p[1] for p in pts]
    vs = [bm.verts.new((x, 0, z)) for x, z in pts]
    fc = bm.faces.new(vs)
    for lp, (x, z) in zip(fc.loops, pts):
        lp[uvl].uv = (0.02 + 0.96 * (x - min(xs)) / (max(xs) - min(xs)), 0.02 + 0.96 * (z - min(zs)) / (max(zs) - min(zs)))
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth=False)


def glass_mat(name):
    cv = Canvas(32, 16, "#cfe8ff")
    for x in (9, 10, 13, 25):
        cv.rect(x, 2, x, 14, WHITE)
    cv.rect(0, 15, 31, 15, WHITE)
    m = tex_mat(name, cv, emit=0.35, rough=0.15, ext='REPEAT')
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs["Alpha"].default_value = 0.34
    return m


def socket(kit, A, purpose, parent, loc, rot=(0, 0, 0)):
    ob = kit.empty(f"{A} socket {purpose}", parent, loc, rot)
    ob.empty_display_type = 'ARROWS'
    return ob


def sprinkle_mats(kit):
    return [solid(kit, "item sprinkle " + c, c, 0.65) for c in SPRINKLES]


# ---------------------------------------------------------------- flavor textures
def tex_scoop(f, rand, sparkle=False):
    c = Canvas(32, 16, f["cream"])
    c.speckle(rand, [f["shade"]], 60)
    c.rect(0, 0, 31, 1, f["shade"])
    c.speckle(rand, [f["hi"]], 30, 8, 15)
    k = f["kind"]
    if k == "bean":
        c.speckle(rand, ["#3a2414", "#6a4a24"], 18, 2, 15)
    elif k == "fudge":
        for _ in range(5):
            x, y = rand.randrange(32), rand.randint(2, 13)
            for s in range(5):
                c.set(x + s, y + (s % 3 == 1), "#c47a44")
        for _ in range(12):
            x, y = rand.randrange(32), rand.randint(2, 14)
            c.rect(x, y, x + 1, y, f["chip"])
    elif k == "berry":
        for _ in range(9):
            x, y = rand.randrange(32), rand.randint(2, 13)
            c.rect(x, y, x + 1, y + 1, RED); c.set(x + 1, y + 1, "#ff6a8a")
        c.speckle(rand, [YEL, "#ffd0e6"], 18, 2, 15)
    elif k == "chips":
        for _ in range(16):
            x, y = rand.randrange(32), rand.randint(2, 14)
            c.rect(x, y, x + 1, y, rand.choice((CHOC, "#3a1c0c")))
    if sparkle:
        c.speckle(rand, [YEL, WHITE, "#ffe98a"], 22, 3, 15)
    return c


def tex_pint_h(f, rand, empty):
    """64x32: rows 0-19 outer wall, 20-21 rim, 22-31 inside."""
    c = Canvas(64, 32, WHITE)
    c.speckle(rand, [PAPER], 50, 0, 19)
    c.rect(0, 0, 63, 1, "#e6dcd2")
    c.rect(0, 4, 63, 15, f["tint"])
    c.rect(0, 4, 63, 4, f["tint_d"]); c.rect(0, 15, 63, 15, f["tint_d"])
    w = text_w(f["label"])
    x0 = 40 - (w + 1) // 2
    c.rect(x0 - 2, 6, x0 + w + 1, 13, WHITE)
    text(c, f["label"], x0, 11, f["ink"])
    for cx in (16 if w > 20 else 20, 64 if w > 20 else 60):
        if cx:
            disc(c, cx, 10, 2, WHITE); disc(c, cx, 10, 1, f["cream"] if f["kind"] != "bean" else "#fff8dc")
    cone_icon(c, 0, 5, 5, scoop=f["cream"])
    for i in range(18):
        c.set(rand.randrange(64), rand.choice((17, 18, 2)), SPRINKLES[i % 6])
    c.rect(0, 20, 63, 21, f["tint_d"])
    c.rect(0, 22, 63, 31, PAPER); c.rect(0, 27, 63, 30, "#e2d8ec"); c.rect(0, 31, 63, 31, "#d0c4de")
    if empty:
        for _ in range(10):
            x = rand.randrange(64)
            c.rect(x, 22 + rand.randint(4, 7), x + rand.randint(0, 1), 31, f["cream"])
        c.speckle(rand, [f["cream"], f["shade"]], 50, 29, 31)
    return c


def tex_pint_lid(f, rand):
    c = Canvas(32, 8, f["tint"])
    c.rect(0, 0, 31, 2, f["tint_d"])
    c.rect(0, 3, 31, 3, WHITE)
    c.speckle(rand, [WHITE, YEL if f["tint"] != YEL else PINK], 12, 4, 6)
    c.rect(0, 7, 31, 7, f["cream"] if f["kind"] != "bean" else WHITE)
    return c


def tex_tub_h(f, rand, fill):
    """96x48: rows 0-25 outer wall, 26-28 bead, 29 rim, 30-47 inside. fill = scoops left out of 8."""
    c = Canvas(96, 48, WHITE)
    c.speckle(rand, [PAPER], 90, 0, 25)
    c.rect(0, 0, 95, 2, f["tint_d"])
    c.rect(0, 5, 95, 23, f["tint"])
    c.rect(0, 5, 95, 5, f["tint_d"]); c.rect(0, 23, 95, 23, f["tint_d"])
    for x in range(0, 96, 6):  # candy stripes between the bands
        c.rect(x, 3, x + 2, 4, PINK if f["tint"] != PINK else BLUE)
        c.rect(x + 3, 24, x + 5, 25, PINK if f["tint"] != PINK else BLUE)
    # front sticker: flavor name and the 8-scoop gauge
    w = text_w(f["label"])
    c.rect(56 - 19, 7, 56 + 18, 21, WHITE)
    c.rect(56 - 19, 7, 56 + 18, 7, "#e6dcd2")
    text(c, f["label"], 56 - (w + 1) // 2, 19, f["ink"])
    for i in range(8):
        x = 56 - 16 + i * 4
        if i < fill:
            c.rect(x, 9, x + 2, 11, f["tint_d"]); c.set(x, 11, WHITE)
        else:
            c.rect(x, 9, x + 2, 11, "#ddd2e6"); c.set(x + 1, 10, WHITE)
    # back: big scoop + cone icon
    cone_icon(c, 0, 7, 9, scoop=f["cream"] if f["kind"] != "bean" else "#fff8dc")
    for cx in (24, 82):
        disc(c, cx, 14, 4, WHITE); disc(c, cx, 14, 3, f["cream"] if f["kind"] != "bean" else "#fff8dc")
        c.dots([(cx - 1, 15), (cx + 1, 13)], f["chip"] or "#3a2414")
    c.rect(0, 26, 95, 28, f["tint"]); c.rect(0, 26, 95, 26, f["tint_d"])
    c.rect(0, 29, 95, 29, WHITE)
    c.rect(0, 30, 95, 47, PAPER); c.rect(0, 40, 95, 45, "#e6dcec"); c.rect(0, 46, 95, 47, "#d0c4de")
    if fill < 8:
        top = 30 + int(round(16 * (1 - fill / 8)))
        for _ in range(26):
            x = rand.randrange(96)
            c.rect(x, 31 + rand.randint(0, 5), x + rand.randint(0, 2), top + 1, f["cream"])
        c.speckle(rand, [f["shade"]], 30, 31, top)
    return c


def tex_tub_lid(f, rand):
    c = Canvas(96, 16, f["tint"])
    c.rect(0, 0, 95, 4, f["tint_d"])
    c.rect(0, 5, 95, 6, WHITE)
    for x in range(0, 96, 4):
        c.set(x, 2, WHITE)
    c.speckle(rand, [WHITE, YEL if f["tint"] != YEL else PINK, BLUE], 40, 7, 12)
    c.rect(0, 13, 95, 15, WHITE)
    c.rect(0, 15, 95, 15, f["cream"] if f["kind"] != "bean" else "#fff8dc")
    return c


# ---------------------------------------------------------------- scoop
SCOOP_Z = (0.0, 0.12, 0.22, 0.6, 1.05, 1.42, 1.66)
SCOOP_R = (0.62, 1.04, 0.86, 1.04, 0.98, 0.7, 0.3)


def scoop(kit, name, parent, loc, r, mat, f=None, chips=7, drips=0, chip_mat=None):
    """Hand-scooped ball: frilly lip at the bottom, lumpy dome, flavor bits pressed into the surface."""
    R = kit.rand
    ob = tube(kit, name, [(0, 0, z * r) for z in SCOOP_Z], [x * r for x in SCOOP_R], mat, parent, sides=8,
              bulge=(0, 0.08 * r), loc=loc)
    for i, vtx in enumerate(ob.data.vertices):
        ring, k = divmod(i, 8)
        if ring == 1:
            s = 1.1 if k % 2 else 0.95
            vtx.co.x *= s; vtx.co.y *= s; vtx.co.z += 0.05 * r if k % 2 else -0.03 * r
        elif 2 <= ring <= 6 or i == 57:
            vtx.co += Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * 0.06 * r
    if f and f["chip"] and chips:
        cm = chip_mat or solid(kit, f"{name} bits", f["chip"], 0.3)
        big = f["kind"] == "berry"
        for i in range(chips):
            t = R.uniform(0.0, 1.0)
            z = (0.55 + 0.95 * t) * r
            rr = (1.02 - 0.62 * t * t) * r
            a = 2 * math.pi * (i + R.uniform(-0.3, 0.3)) / chips
            s = r * (0.24 if big else 0.18)
            tbox(kit, f"{name} bit {i}", (0, 0, 0), (s, s * 0.8, s * (0.8 if big else 0.5)), cm, parent,
                 loc=(loc[0] + math.cos(a) * rr, loc[1] + math.sin(a) * rr, loc[2] + z),
                 rot=(R.uniform(0, 90), R.uniform(-30, 30), R.uniform(0, 180)))
    for i in range(drips):
        a = 2 * math.pi * (i + 0.3) / max(drips, 1) + R.uniform(-0.3, 0.3)
        ca, sa = math.cos(a), math.sin(a)
        tube(kit, f"{name} drip {i}", [(ca * 1.0 * r, sa * 1.0 * r, 0.75 * r), (ca * 1.07 * r, sa * 1.07 * r, 0.4 * r),
                                       (ca * 1.14 * r, sa * 1.14 * r, (0.05 + 0.12 * (i % 2)) * r)],
             [0.16 * r, 0.12 * r, 0.1 * r], mat, parent, sides=5, loc=loc, bulge=(0, 0.08 * r))
    return ob


# ---------------------------------------------------------------- 1. pints
PINT_H, PINT_RB, PINT_RT, PINT_W = 0.12, 0.044, 0.052, 0.0045


def build_pint(kit, root, A, fl, full):
    f, R = FL[fl], kit.rand
    H, rb, rt, w = PINT_H, PINT_RB, PINT_RT, PINT_W
    carton = tex_mat(f"{A} carton", tex_pint_h(f, R, not full), ext='REPEAT')
    lathe(kit, f"{A} carton", [(0, 0, 0.005), (rb - 0.004, 0, 0.012), (rb, 0.005, 0.03), (rt, H, 0.6),
                               (rt - 0.0008, H + 0.003, 0.65), (rt - w, H, 0.69), (rb - w, 0.008, 0.95),
                               (0, 0.008, 0.99)], carton, root, sides=8)
    socket(kit, A, "hand", root, (0, 0, H * 0.5))
    if full:
        cream = tex_mat(f"{A} cream", tex_scoop(f, R), 0.4, ext='REPEAT')
        scoop(kit, f"{A} scoop", root, (0, 0, H - 0.034), 0.047, cream, f, chips=6)
        hinge = kit.empty(f"{A} lid hinge", root, (0, rt + 0.003, H), (-118, 0, 0))
        lid = tex_mat(f"{A} lid", tex_pint_lid(f, R), ext='REPEAT')
        lathe(kit, f"{A} lid", [(rt + 0.003, -0.011, 0.05), (rt + 0.004, 0.003, 0.3), (rt * 0.9, 0.008, 0.6),
                                (0, 0.01, 0.95)], lid, hinge, sides=8, loc=(0, -(rt + 0.003), 0))
    else:
        cream = solid(kit, f"{A} leftover", f["cream"], 0.4, shade=f["shade"])
        lathe(kit, f"{A} leftover", [(rb - w - 0.002, 0.009, 0.1), (0.022, 0.015, 0.5), (0, 0.017, 0.9)], cream, root,
              sides=8, jit=0.002)


# ---------------------------------------------------------------- 2. scoop grenades
def build_grenade(kit, root, A, fl):
    f, R = FL[fl], kit.rand
    cream = tex_mat(f"{A} cream", tex_scoop(f, R), 0.42, ext='REPEAT')
    r = 0.05
    scoop(kit, f"{A} scoop", root, (0, 0, 0), r, cream, f, chips=9)
    socket(kit, A, "hand", root, (0, 0, 0.8 * r))


# ---------------------------------------------------------------- 3. flavor tubs
TUB_H, TUB_RB, TUB_RT, TUB_W = 0.24, 0.128, 0.145, 0.006


def tub_inner_r(z):
    return TUB_RB - TUB_W + (TUB_RT - TUB_RB) * (z - 0.012) / (TUB_H - 0.012)


def build_tub(kit, root, A, fl, fill):
    f, R = FL[fl], kit.rand
    H, rb, rt, w = TUB_H, TUB_RB, TUB_RT, TUB_W
    body = tex_mat(f"{A} tub", tex_tub_h(f, R, fill), ext='REPEAT')
    lathe(kit, f"{A} tub", [(0, 0, 0.004), (rb - 0.008, 0, 0.012), (rb, 0.008, 0.025), (rt, H - 0.022, 0.54),
                            (rt + 0.006, H - 0.018, 0.56), (rt + 0.006, H, 0.6), (rt - w, H, 0.625),
                            (rb - w, 0.012, 0.95), (0, 0.012, 0.99)], body, root, sides=12)
    cream = tex_mat(f"{A} cream", tex_scoop(f, R), 0.4, ext='REPEAT')
    chip = solid(kit, f"{A} bits", f["chip"], 0.3) if f["chip"] else None
    if fill == 8:
        zf = H - 0.014
        ri = tub_inner_r(zf)
        lathe(kit, f"{A} ice cream", [(ri - 0.001, zf - 0.03, 0.05), (ri - 0.002, zf, 0.2), (ri * 0.78, zf + 0.026, 0.45),
                                      (ri * 0.42, zf + 0.04, 0.75), (0, zf + 0.046, 0.98)], cream, root, sides=12,
              jit=0.006)
        # scoop-shaped ridge where the churn poured the last of it
        scoop(kit, f"{A} swirl", root, (0.03, -0.02, zf + 0.022), 0.05, cream, f, chips=0)
        top = [(ri * 0.6, zf + 0.03), (ri * 0.35, zf + 0.04)]
    else:
        zf = H * 0.5
        ri = tub_inner_r(zf)
        lathe(kit, f"{A} ice cream", [(ri - 0.001, zf + 0.012, 0.2), (ri * 0.82, zf + 0.004, 0.42),
                                      (ri * 0.5, zf - 0.016, 0.7), (0, zf - 0.024, 0.98)], cream, root, sides=12,
              jit=0.007)
        # leftover curls from the scooper and the scooper itself, leaning on the rim
        for i, (x, y, rr) in enumerate(((0.05, 0.03, 0.03), (-0.045, 0.04, 0.026))):
            scoop(kit, f"{A} curl {i}", root, (x, y, zf - 0.012), rr, cream, None)
        tool = kit.empty(f"{A} scooper", root, (0.02, 0.02, zf - 0.004), (0, -34, 30))
        tube(kit, f"{A} scooper handle", [(0, 0, 0.03), (0, 0, 0.13), (0, 0, 0.25)], [0.012, 0.015, 0.016],
             solid(kit, f"{A} scooper handle", PINK), tool, sides=6)
        lowball(kit, f"{A} scooper bowl", (0, 0, 0.012), (0.034, 0.034, 0.024), solid(kit, "steel", STEEL, shade="#a9a2e0"),
                tool)
        top = [(ri * 0.55, zf - 0.006), (ri * 0.3, zf - 0.016)]
    if chip:
        for i in range(10):
            rr, z = top[i % 2]
            a = 2 * math.pi * i / 10 + R.uniform(-0.2, 0.2)
            s = 0.012 if f["kind"] == "berry" else 0.009
            tbox(kit, f"{A} bit {i}", (0, 0, 0), (s, s * 0.8, s * 0.6), chip, root,
                 loc=(math.cos(a) * rr, math.sin(a) * rr, z + 0.002), rot=(R.uniform(0, 60), 0, R.uniform(0, 180)))
    hinge = kit.empty(f"{A} lid hinge", root, (0, rt + 0.008, H), (-112, 0, 0))
    lid = tex_mat(f"{A} lid", tex_tub_lid(f, R), ext='REPEAT')
    lathe(kit, f"{A} lid", [(rt + 0.01, -0.02, 0.03), (rt + 0.012, 0.004, 0.25), (rt * 0.92, 0.012, 0.5),
                            (rt * 0.35, 0.017, 0.82), (0, 0.017, 0.98)], lid, hinge, sides=12, loc=(0, -(rt + 0.008), 0))
    tbox(kit, f"{A} lid tab", (0, -(2 * rt + 0.02), -0.004), (0.05, 0.022, 0.008), solid(kit, f"{A} tab", f["tint_d"]),
         hinge)
    socket(kit, A, "hand L", root, (rt + 0.01, 0, H * 0.55))
    socket(kit, A, "hand R", root, (-(rt + 0.01), 0, H * 0.55))


# ---------------------------------------------------------------- 4. bulky ingredients
def tex_milk_crate():
    c = Canvas(64, 24, BLUE)
    for half, x0 in ((0, 0), (1, 32)):
        c.rect(x0, 0, x0 + 31, 1, "#1f5fd0")
        c.rect(x0, 18, x0 + 31, 23, "#5aa0ff"); c.rect(x0, 23, x0 + 31, 23, "#9cc4ff")
        for y in (3, 10):
            for x in range(x0 + 2, x0 + 31, 6):
                c.rect(x, y, x + 3, y + 5, "#173f9e"); c.rect(x, y + 5, x + 3, y + 5, "#0f2c78")
    text(c, "MILK", 9, 22, WHITE)
    c.rect(32 + 9, 14, 32 + 22, 17, "#0f2c78")  # end-wall hand hole (cuts into the top slats)
    c.rect(32 + 10, 18, 32 + 21, 19, "#0f2c78")
    return c


def tex_milk_bottle():
    c = Canvas(32, 32, WHITE)
    c.rect(0, 0, 31, 1, "#e6eef8")
    c.rect(0, 7, 31, 17, PINK); c.rect(0, 7, 31, 7, "#d63a86"); c.rect(0, 17, 31, 17, "#d63a86")
    text(c, "MILK", 16 - 8, 15, WHITE)
    c.rect(0, 22, 31, 27, "#e8f3ff")
    for x in (6, 7, 22):
        c.rect(x, 3, x, 21, "#ffffff" if x != 22 else "#e6eef8")
    c.rect(0, 28, 31, 31, PINK)
    for x in range(0, 32, 4):
        c.set(x + 1, 29, WHITE)
    return c


def build_milk_crate(kit, root, A):
    R = kit.rand
    W, D, Hc, t = 0.46, 0.34, 0.27, 0.022
    m = tex_mat(f"{A} plastic", tex_milk_crate())
    rim = {'pz': (0.1, 0.9, 0.2, 0.98), 'nz': (0.1, 0.0, 0.2, 0.05)}
    tbox(kit, f"{A} floor", (0, 0, t / 2), (W - 0.01, D - 0.01, t), solid(kit, f"{A} floor", "#1f5fd0", 0.25), root)
    for s in (-1, 1):
        tbox(kit, f"{A} side {s}", (0, s * (D - t) / 2, Hc / 2), (W, t, Hc), m, root,
             uv=dict(rim, ny=(0, 0, 0.5, 1), py=(0, 0, 0.5, 1), nx=(0.1, 0.1, 0.12, 0.9), px=(0.1, 0.1, 0.12, 0.9)))
        tbox(kit, f"{A} end {s}", (s * (W - t) / 2, 0, Hc / 2), (t, D - 2 * t, Hc), m, root,
             uv=dict(rim, nx=(0.5, 0, 1, 1), px=(0.5, 0, 1, 1), ny=(0.6, 0.1, 0.62, 0.9), py=(0.6, 0.1, 0.62, 0.9)))
    glass = tex_mat(f"{A} bottle", tex_milk_bottle(), ext='REPEAT')
    for i, (x, y, tilt) in enumerate(((-0.105, -0.075, (0, 3, 0)), (0.105, -0.075, (-3, 0, 0)), (-0.105, 0.075, (3, 0, 4)),
                                      (0.105, 0.075, (0, -4, 0)))):
        b = kit.empty(f"{A} bottle {i}", root, (x, y, t), tilt)
        lathe(kit, f"{A} bottle {i}", [(0, 0, 0.0), (0.042, 0, 0.02), (0.047, 0.012, 0.08), (0.047, 0.17, 0.6),
                                       (0.031, 0.22, 0.74), (0.022, 0.26, 0.84), (0.026, 0.268, 0.88),
                                       (0.026, 0.29, 0.96), (0, 0.293, 0.99)], glass, b, sides=8)
    socket(kit, A, "hand L", root, (W / 2, 0, Hc * 0.85))
    socket(kit, A, "hand R", root, (-W / 2, 0, Hc * 0.85))


def tex_sugar(rand):
    c = Canvas(128, 64, "#fff4e0")
    for y in range(64):
        for x in range(128):
            if (x * 3 + y * 5) % 11 == 0:
                c.set(x, y, "#f0e2c6")
    for x0 in (0, 64):
        c.rect(x0, 3, x0 + 63, 7, BLUE); c.rect(x0, 9, x0 + 63, 10, PINK)
        c.rect(x0, 54, x0 + 63, 55, PINK)
        for x in range(x0 + 2, x0 + 63, 4):  # stitched top seam
            c.rect(x, 60, x + 1, 60, "#c9a066")
    c.rect(32 - 22, 29, 32 + 21, 44, WHITE)
    text(c, "SUGAR", 32 - 19, 41, BLUE, 2)
    for i, (cx, cy) in enumerate(((24, 19), (32, 19), (40, 19), (28, 26), (36, 26))):  # sugar cubes
        c.rect(cx - 3, cy - 3, cx + 3, cy + 3, "#9cc4ff"); c.rect(cx - 2, cy - 2, cx + 2, cy + 2, WHITE)
        c.set(cx - 1, cy + 1, "#e6eef8")
    text(c, "SWEET", 96 - 19, 41, PINK, 2)
    cone_icon(c, 96, 14, 9, PINK)
    c.speckle(rand, ["#f0e2c6", "#e6d4b0"], 120)
    return c


def build_sugar_sack(kit, root, A):
    W, Hh, D = 0.46, 0.6, 0.3
    m = tex_mat(f"{A} sack", tex_sugar(kit.rand))
    pillow(kit, f"{A} sack", W, Hh, D, m, root, nx=7, nz=7, jit=0.012)
    ear = solid(kit, f"{A} ear", "#fff4e0", shade="#e6d4b0")
    for s in (-1, 1):
        x = s * W * 0.5 * (1 - 0.12 + 0.0)
        tube(kit, f"{A} ear {s}", [(x * 0.97, 0, Hh - 0.02), (x * 1.04, 0, Hh + 0.025), (x * 1.1, 0, Hh + 0.05)],
             [(0.022, 0.012), (0.018, 0.009), (0.008, 0.004)], ear, root, sides=5)
    tbox(kit, f"{A} seam", (0, 0, Hh - 0.012), (W * 0.84, 0.02, 0.022), solid(kit, f"{A} seam", PINK), root)
    socket(kit, A, "hand L", root, (W * 0.48, 0, Hh * 0.45))
    socket(kit, A, "hand R", root, (-W * 0.48, 0, Hh * 0.45))


def tex_cocoa_bag():
    c = Canvas(64, 48, "#8a4a2a")
    for y in range(48):
        for x in range(64):
            if (x * 7 + y * 3) % 13 == 0:
                c.set(x, y, "#7a3e22")
    # front (x 0-31)
    c.rect(0, 0, 31, 2, "#5e2e18")
    c.rect(0, 30, 31, 37, PINK); c.rect(0, 30, 31, 30, "#d63a86")
    text(c, "COCOA", 16 - 10, 36, WHITE)
    for cx, cy in ((10, 18), (21, 18), (16, 10)):  # cocoa beans
        disc(c, cx, cy, 4, "#5e2e18"); disc(c, cx, cy, 3, "#a85a30")
        c.rect(cx, cy - 2, cx, cy + 2, "#5e2e18"); c.set(cx - 1, cy + 1, "#d08a50")
    c.rect(4, 3, 27, 4, YEL)
    # back (x 32-47)
    c.rect(32, 30, 47, 37, PINK)
    disc(c, 40, 18, 4, "#5e2e18"); disc(c, 40, 18, 3, "#a85a30")
    # side gusset (x 48-63): darker with a fold line
    c.rect(48, 0, 63, 47, "#7a3e22"); c.rect(55, 0, 56, 47, "#5e2e18")
    c.rect(48, 30, 63, 37, "#d63a86")
    return c


def build_cocoa_bag(kit, root, A):
    W, D, Hh = 0.32, 0.2, 0.46
    m = tex_mat(f"{A} bag", tex_cocoa_bag())
    tbox(kit, f"{A} bag", (0, 0, Hh / 2), (W, D, Hh), m, root, taper=(1.0, 0.45),
         uv={'ny': (0, 0, 0.5, 1), 'py': (0.5, 0, 0.75, 1), 'nx': (0.75, 0, 1, 1), 'px': (0.75, 0, 1, 1),
             'pz': (0.8, 0.0, 0.85, 0.05), 'nz': (0.8, 0.0, 0.85, 0.05)})
    fold = solid(kit, f"{A} fold", "#6e3a1e", shade="#5e2e18")
    tube(kit, f"{A} fold", [(-W / 2 - 0.006, 0, Hh + 0.012), (W / 2 + 0.006, 0, Hh + 0.012)], [(0.03, 0.026)] * 2, fold,
         root, sides=6, side=(0, 0, 1))
    tbox(kit, f"{A} clip", (0, -0.004, Hh + 0.012), (0.07, 0.07, 0.03), solid(kit, f"{A} clip", PINK), root)
    tbox(kit, f"{A} clip tab", (0, -0.04, Hh - 0.012), (0.05, 0.008, 0.03), solid(kit, f"{A} clip", PINK), root)
    # a spill of cocoa dust on top of the fold
    lathe(kit, f"{A} dust", [(0.03, Hh + 0.034, 0.1), (0, Hh + 0.045, 0.9)], solid(kit, f"{A} dust", "#5e2e18"), root,
          sides=6, loc=(0.09, 0.0, 0.0), jit=0.004)
    socket(kit, A, "hand L", root, (W / 2, 0, Hh * 0.45))
    socket(kit, A, "hand R", root, (-W / 2, 0, Hh * 0.45))


def tex_berry_flat():
    c = Canvas(64, 32, WOOD)
    for y in (0, 8, 16, 24):
        c.rect(0, y, 63, y, WOOD_D)
    c.speckle(random.Random(7), ["#d99446", "#f2bc72"], 80)
    # long side (x 0-47): stamped label
    c.rect(4, 3, 43, 13, WHITE); c.rect(4, 3, 43, 3, "#e6dcd2")
    text(c, "BERRIES", 24 - 13, 11, RED)
    for cx in (7, 41):
        disc(c, cx, 8, 2, RED); c.set(cx, 11, LEAF)
    # end (x 48-63): hand hole
    c.rect(51, 9, 60, 13, "#3a2340"); c.rect(52, 14, 59, 14, "#3a2340")
    c.rect(0, 30, 63, 31, "#f2bc72")
    return c


def tex_berry_bed(rand):
    c = Canvas(32, 32, "#d01a40")
    for _ in range(40):
        x, y = rand.randrange(32), rand.randrange(32)
        disc(c, x, y, 2, rand.choice((RED, "#ff4060", DRED)))
    c.speckle(rand, [YEL], 50)
    c.speckle(rand, [LEAF, LEAF_D], 30)
    return c


def tex_berry():
    c = Canvas(12, 8, RED)
    for y in range(0, 7, 2):
        for x in range(y % 4 // 2, 12, 3):
            c.set(x, y, YEL)
    c.rect(0, 0, 11, 0, DRED)
    c.rect(0, 7, 11, 7, "#ff6a8a")
    return c


def build_strawberry_basket(kit, root, A):
    R = kit.rand
    W, D, Hb, t = 0.46, 0.32, 0.15, 0.018
    m = tex_mat(f"{A} wood", tex_berry_flat())
    plain = {'pz': (0.9, 0.95, 1.0, 1.0), 'nz': (0.9, 0.95, 1.0, 1.0)}
    tbox(kit, f"{A} floor", (0, 0, t / 2), (W, D, t), m, root, uv={'all': (0.0, 0.5, 0.7, 1.0)})
    for s in (-1, 1):
        tbox(kit, f"{A} side {s}", (0, s * (D - t) / 2, Hb / 2), (W, t, Hb), m, root,
             uv=dict(plain, ny=(0, 0, 0.75, 0.5), py=(0, 0, 0.75, 0.5), nx=(0.7, 0.6, 0.72, 0.9),
                     px=(0.7, 0.6, 0.72, 0.9)))
        tbox(kit, f"{A} end {s}", (s * (W - t) / 2, 0, Hb * 0.6), (t, D - 2 * t, Hb * 1.2), m, root,
             uv=dict(plain, nx=(0.75, 0, 1, 0.55), px=(0.75, 0, 1, 0.55), ny=(0.7, 0.6, 0.72, 0.9),
                     py=(0.7, 0.6, 0.72, 0.9)))
    tbox(kit, f"{A} berry bed", (0, 0, Hb - 0.02), (W - 2 * t, D - 2 * t, 0.03), tex_mat(f"{A} berry bed", tex_berry_bed(R)),
         root, uv={'pz': (0, 0, 1, 1)}, taper=(1.0, 1.0))
    berry = tex_mat(f"{A} berry", tex_berry(), 0.42, ext='REPEAT')
    leaf = solid(kit, f"{A} leaf", LEAF, 0.4, shade=LEAF_D)
    spots = [(-0.17, -0.09), (-0.09, -0.1), (0.0, -0.08), (0.09, -0.1), (0.17, -0.08), (-0.14, 0.0), (-0.05, 0.01),
             (0.05, -0.01), (0.15, 0.02), (-0.16, 0.09), (-0.03, 0.09), (0.08, 0.08), (0.18, 0.1)]
    for i, (x, y) in enumerate(spots):
        b = kit.empty(f"{A} berry {i}", root, (x, y, Hb - 0.002), (R.uniform(70, 110), 0, R.uniform(0, 360)))
        lathe(kit, f"{A} berry {i}", [(0, 0.0, 0.02), (0.018, 0.016, 0.4), (0.021, 0.034, 0.75), (0, 0.046, 0.98)],
              berry, b, sides=6, loc=(0, 0, -0.024))
        cap = kit.link(f"{A} leaf {i}", star_mesh(f"{A} leaf {i}", 5, 0.022, 0.009), b, (0, 0, 0.022), (90, 0, 0))
        cap.data.materials.append(leaf)
    socket(kit, A, "hand L", root, (W / 2, 0, Hb * 0.85))
    socket(kit, A, "hand R", root, (-W / 2, 0, Hb * 0.85))


def tex_burlap(rand):
    c = Canvas(64, 32, "#d9b07a")
    for y in range(32):
        for x in range(64):
            if (x + 2 * y) % 4 == 0:
                c.set(x, y, "#c49660")
            elif (x * 5 + y) % 7 == 0:
                c.set(x, y, "#e8c48e")
    c.rect(0, 15, 63, 17, PINK); c.rect(0, 16, 63, 16, "#ff8fc8")
    c.rect(34, 4, 45, 12, "#c49660")
    text(c, "MINT", 40 - 8, 11, "#119a76")
    for x in range(0, 64, 3):  # rolled rim edge
        c.set(x, 26, "#a87a48")
    return c


def tex_leaf(rand):
    c = Canvas(16, 8, LEAF)
    c.rect(0, 3, 15, 4, "#8affb0")
    for x in range(2, 15, 3):
        c.set(x, 2, "#2fbf5a"); c.set(x, 5, "#2fbf5a")
    c.rect(0, 0, 15, 0, LEAF_D); c.rect(0, 7, 15, 7, LEAF_D)
    return c


def sprig(kit, name, parent, base, d, L, leaf_mat, stem_mat, rand):
    """Mint sprig: a 4-sided stem with pairs of diamond leaves (one bmesh) at three nodes plus a top tuft."""
    d = Vector(d).normalized()
    pts = [Vector(base), Vector(base) + d * L * 0.5 + Vector((rand.uniform(-1, 1), rand.uniform(-1, 1), 0)) * 0.01,
           Vector(base) + d * L]
    tube(kit, f"{name} stem", [tuple(p) for p in pts], [0.004, 0.0035, 0.003], stem_mat, parent, sides=4,
         caps=(False, False))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    side0 = d.cross(Vector((0, 0, 1)) if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
    for n, t in enumerate((0.3, 0.56, 0.8, 1.0)):
        p = pts[0].lerp(pts[2], t)
        s = Matrix.Rotation(math.radians(90 * n + rand.uniform(-20, 20)), 3, d) @ side0
        size = (0.075, 0.068, 0.058, 0.045)[n]
        for sg in ((1, -1) if n < 3 else (1, -1, 0)):
            dirv = (s * sg if sg else d).normalized()
            dirv = (dirv + d * 0.45).normalized()
            n_ = dirv.cross(d).normalized() if sg else s
            tip = p + dirv * size
            mid = p + dirv * size * 0.45
            vs = [bm.verts.new(p), bm.verts.new(mid + n_ * size * 0.3 + d * 0.004), bm.verts.new(tip + d * 0.008),
                  bm.verts.new(mid - n_ * size * 0.3 + d * 0.004)]
            fc = bm.faces.new(vs)
            for lp, c in zip(fc.loops, ((0.02, 0.5), (0.5, 0.98), (0.98, 0.5), (0.5, 0.02))):
                lp[uvl].uv = c
    kit.mesh_from_bmesh(f"{name} leaves", bm, leaf_mat, parent, smooth=False)


def build_mint_bundle(kit, root, A):
    R = kit.rand
    m = tex_mat(f"{A} burlap", tex_burlap(R), ext='REPEAT')
    lathe(kit, f"{A} sack", [(0, 0, 0.01), (0.13, 0, 0.05), (0.168, 0.04, 0.14), (0.178, 0.17, 0.45),
                             (0.158, 0.25, 0.62), (0.172, 0.282, 0.72), (0.188, 0.302, 0.8), (0.17, 0.322, 0.88),
                             (0.148, 0.305, 0.95)], m, root, sides=8, jit=0.006)
    leaf = tex_mat(f"{A} leaf", tex_leaf(R), 0.42)
    stem = solid(kit, f"{A} stem", LEAF_D)
    mound = Canvas(16, 16, LEAF)
    mound.speckle(R, ["#8affb0", LEAF_D, MINT], 70)
    lathe(kit, f"{A} leaves bed", [(0.155, 0.29, 0.1), (0.15, 0.33, 0.3), (0.11, 0.37, 0.55), (0.06, 0.395, 0.75),
                                   (0, 0.4, 0.95)], tex_mat(f"{A} leaves bed", mound, 0.4), root, sides=8, jit=0.02)
    for i in range(13):
        a = 2 * math.pi * i / 13 * 2.0 + R.uniform(-0.25, 0.25)
        rr = 0.03 + 0.1 * ((i * 5) % 13) / 12
        base = (math.cos(a) * rr, math.sin(a) * rr, 0.33 + 0.05 * (1 - rr / 0.13))
        d = (math.cos(a) * 0.8 * rr / 0.13, math.sin(a) * 0.8 * rr / 0.13, 1.0)
        sprig(kit, f"{A} sprig {i}", root, base, d, R.uniform(0.09, 0.15), leaf, stem, R)
    tube(kit, f"{A} twine", [(0, 0, 0.245), (0, 0, 0.262)], 0.162, solid(kit, f"{A} twine", PINK), root, sides=8,
         caps=(False, False))
    socket(kit, A, "hand L", root, (0.18, 0, 0.28))
    socket(kit, A, "hand R", root, (-0.18, 0, 0.28))


def tex_vanilla_box(rand):
    c = Canvas(64, 48, WOOD)
    for y in (0, 9, 18, 28, 38):
        c.rect(0, y, 63, y, WOOD_D)
    c.speckle(rand, ["#d99446", "#f2bc72"], 120)
    # front (rows 0-27): yellow label with a vanilla flower
    c.rect(6, 4, 57, 23, YEL); c.rect(6, 4, 57, 4, "#d9b21a"); c.rect(7, 22, 56, 22, WHITE)
    text(c, "VANILLA", 32 - 13 + 6, 19, "#7a3a1c")
    cx, cy = 13, 13
    for dx, dy in ((0, 3), (3, 1), (2, -3), (-2, -3), (-3, 1)):
        disc(c, cx + dx, cy + dy, 2, WHITE)
    disc(c, cx, cy, 1, YEL); c.set(cx, cy, ORNG)
    for x in range(22, 52, 2):
        c.set(x, 8, "#3a1c0c"); c.set(x + 1, 9, "#3a1c0c")
    # lid top (rows 28-47): stamped flower and stripes
    c.rect(4, 31, 59, 44, "#f2bc72")
    text(c, "VANILLA", 32 - 13, 40, "#7a3a1c")
    c.rect(4, 32, 59, 32, YEL); c.rect(4, 43, 59, 43, YEL)
    return c


def build_vanilla_box(kit, root, A):
    R = kit.rand
    W, D, Hb, t = 0.42, 0.28, 0.17, 0.016
    m = tex_mat(f"{A} wood", tex_vanilla_box(R))
    plank = {'all': (0.0, 0.62, 0.08, 0.7)}
    tbox(kit, f"{A} floor", (0, 0, t / 2), (W, D, t), m, root, uv=plank)
    tbox(kit, f"{A} front", (0, -(D - t) / 2, Hb / 2), (W, t, Hb), m, root, uv=dict(plank, ny=(0, 0, 1, 0.58)))
    tbox(kit, f"{A} back", (0, (D - t) / 2, Hb / 2), (W, t, Hb), m, root, uv=dict(plank, py=(0.6, 0.62, 1, 0.8)))
    for s in (-1, 1):
        tbox(kit, f"{A} end {s}", (s * (W - t) / 2, 0, Hb / 2), (t, D - 2 * t, Hb), m, root,
             uv=dict(plank, nx=(0.0, 0.62, 0.4, 0.8), px=(0.0, 0.62, 0.4, 0.8)))
    tbox(kit, f"{A} tissue", (0, 0, Hb - 0.05), (W - 2 * t, D - 2 * t, 0.02), solid(kit, f"{A} tissue", "#fff1c7"), root)
    pod = solid(kit, f"{A} pod", "#3a1c0c", 0.28, shade="#5a3418")
    ribbon = solid(kit, f"{A} ribbon", YEL, 0.45)
    for b, (x, y, yaw) in enumerate(((-0.1, -0.05, 8), (0.02, -0.04, -6), (0.12, 0.04, 14))):
        bund = kit.empty(f"{A} bundle {b}", root, (x, y, Hb - 0.032), (0, 0, yaw))
        for i in range(6):
            ox, oz = (i % 3 - 1) * 0.011, (i // 3) * 0.009
            bend = R.uniform(-0.012, 0.012)
            tube(kit, f"{A} pod {b}.{i}", [(ox * 1.6 + bend, -0.11, oz + 0.004), (ox, 0.0, oz + 0.008),
                                           (ox * 1.6 - bend, 0.11, oz + 0.002)],
                 [(0.006, 0.004), (0.0065, 0.0045), (0.003, 0.002)], pod, bund, sides=4, side=(1, 0, 0))
        tube(kit, f"{A} ribbon {b}", [(0, -0.008, 0.008), (0, 0.008, 0.008)], [(0.024, 0.016)] * 2, ribbon, bund, sides=6,
             side=(1, 0, 0), caps=(False, False))
    hinge = kit.empty(f"{A} lid hinge", root, (0, D / 2, Hb), (-104, 0, 0))
    tbox(kit, f"{A} lid", (0, -D / 2, 0.008), (W + 0.01, D + 0.004, 0.016), m, hinge,
         uv=dict(plank, pz=(0, 0.6, 1, 1)))
    tbox(kit, f"{A} latch", (0, -(D - t) / 2 - 0.012, Hb - 0.02), (0.04, 0.008, 0.03), solid(kit, f"{A} brass", GOLD), root)
    socket(kit, A, "hand L", root, (W / 2, 0, Hb * 0.6))
    socket(kit, A, "hand R", root, (-W / 2, 0, Hb * 0.6))


# ---------------------------------------------------------------- 5. gun crate
def tex_gun_crate(rand):
    """128x64 atlas: front (0-63, 0-31), side (64-95, 0-31), plain plank (96-127, 0-31), lid top (0-63, 32-63),
    straw (64-127, 32-63)."""
    c = Canvas(128, 64, "#d9924a")
    c.speckle(rand, ["#c47f3a", "#e8a862"], 500, 0, 31)
    for x0, x1 in ((0, 63), (64, 95), (96, 127)):
        for y in (0, 10, 21, 31):
            c.rect(x0, y, x1, y, "#8a5226")
    for x0, x1 in ((0, 63),):
        for y in (32, 43, 53, 63):
            c.rect(x0, y, x1, y, "#8a5226")
    c.speckle(rand, ["#c47f3a", "#e8a862"], 250, 33, 62)
    for (x, y) in ((2, 5), (61, 5), (2, 15), (61, 15), (2, 26), (61, 26), (66, 5), (93, 5), (66, 26), (93, 26)):
        c.set(x, y, INK)
    # front stencil: SCOOP + FRAGILE
    text(c, "SCOOP", 32 - 19, 27, PINK, 2)
    for x in range(32 - 19, 32 + 19, 4):  # stencil bridges
        c.rect(x + 1, 21, x + 1, 21, "#8a5226")
    text(c, "FRAGILE", 32 - 13, 11, RED)
    c.rect(32 - 15, 4, 32 + 14, 4, RED)
    # side: cone stencil
    cone_icon(c, 80, 5, 13, PINK)
    # lid top: GUNS, arrows and THIS SIDE UP
    text(c, "GUNS", 32 - 15, 58, PINK, 2)
    text(c, "THIS SIDE UP", 32 - 23, 42, INK)
    for ax in (6, 57):
        for row in range(4):
            c.rect(ax - row, 52 - row, ax + row, 52 - row, INK)
        c.rect(ax, 44, ax, 48, INK)
    # straw
    c.rect(64, 32, 127, 63, "#ffe58a")
    for _ in range(140):
        x, y = rand.randrange(64, 128), rand.randrange(32, 64)
        c.rect(x, y, x + rand.randint(1, 4), y, rand.choice(("#e0b84a", "#fff2b0", "#d9a83a")))
    return c


def build_gun_crate(kit, root, A, opened):
    R = kit.rand
    W, D, H, t = 0.74, 0.42, 0.3, 0.028
    m = tex_mat(f"{A} planks", tex_gun_crate(R))
    plain = (0.76, 0.02, 0.99, 0.48)
    pu = {'all': plain}
    tbox(kit, f"{A} floor", (0, 0, t / 2), (W, D, t), m, root, uv=pu)
    for s in (-1, 1):
        tbox(kit, f"{A} wall {s}", (0, s * (D - t) / 2, H / 2), (W, t, H), m, root,
             uv=dict(pu, ny=(0, 0, 0.5, 0.5), py=(0, 0, 0.5, 0.5) if s > 0 else plain))
        tbox(kit, f"{A} end {s}", (s * (W - t) / 2, 0, H / 2), (t, D - 2 * t, H), m, root,
             uv=dict(pu, nx=(0.5, 0, 0.75, 0.5) if s < 0 else plain, px=(0.5, 0, 0.75, 0.5) if s > 0 else plain))
    steel = solid(kit, f"{A} steel", STEEL, shade="#a9a2e0")
    for sx in (-1, 1):
        for sy in (-1, 1):
            tbox(kit, f"{A} corner {sx}{sy}", (sx * (W / 2 - 0.012), sy * (D / 2 - 0.012), H / 2), (0.034, 0.034, H + 0.004),
                 steel, root)
    rope = solid(kit, f"{A} rope", "#ffd36b", shade="#d9a83a")
    for s in (-1, 1):
        x = s * (W / 2 + 0.004)
        tube(kit, f"{A} handle {s}", [(x, -0.08, 0.2), (x + s * 0.035, -0.07, 0.17), (x + s * 0.04, 0, 0.16),
                                      (x + s * 0.035, 0.07, 0.17), (x, 0.08, 0.2)], 0.011, rope, root, sides=5)
    yel = solid(kit, f"{A} latch", YEL)
    tbox(kit, f"{A} hasp", (0, -D / 2 - 0.008, H - 0.04), (0.06, 0.014, 0.05), yel, root)
    hinge = kit.empty(f"{A} lid hinge", root, (0, D / 2, H), (-108 if opened else 0, 0, 0))
    tbox(kit, f"{A} lid", (0, -D / 2, 0.018), (W + 0.012, D + 0.012, 0.036), m, hinge,
         uv=dict(pu, pz=(0, 0.5, 0.5, 1.0)))
    tbox(kit, f"{A} lid latch", (0, -D - 0.01, 0.0), (0.05, 0.012, 0.04), yel, hinge)
    for sx in (-1, 1):
        tbox(kit, f"{A} lid band {sx}", (sx * (W / 2 - 0.06), -D / 2, 0.038), (0.04, D + 0.016, 0.008), steel, hinge)
    socket(kit, A, "hand L", root, (W / 2 + 0.04, 0, 0.17))
    socket(kit, A, "hand R", root, (-W / 2 - 0.04, 0, 0.17))
    socket(kit, A, "contents", root, (0, 0, H - 0.06))
    if not opened:
        return
    tbox(kit, f"{A} straw bed", (0, 0, H - 0.09), (W - 2 * t, D - 2 * t, 0.04), m, root,
         uv={'all': (0.52, 0.52, 0.98, 0.98)})
    straw = solid(kit, f"{A} straw", "#ffe58a", 0.45, shade="#e0b84a")
    for i in range(7):
        tbox(kit, f"{A} straw {i}", (0, 0, 0), (0.008, 0.08, 0.008), straw, root,
             loc=(R.uniform(-0.32, 0.32), R.uniform(-0.17, 0.17), H - 0.066),
             rot=(R.uniform(-25, 25), R.uniform(-10, 10), R.uniform(0, 180)))
    held = kit.empty(f"{A} pistol", root, (-0.06, -0.03, H - 0.04), (0, 90, 78))
    build_gun(kit, held)
    for i, (x, y, col) in enumerate(((0.22, 0.04, MINT),)):
        p = kit.empty(f"{A} spare pint {i}", root, (x, y, H - 0.04), (90, 0, 20 + 50 * i))
        tube(kit, f"{A} spare pint {i}", [(0, 0, -0.06), (0, 0, 0.06)], [0.044, 0.05],
             tex_mat(f"{A} spare pint {i}", tex_pint(col)), p, sides=8)


# ---------------------------------------------------------------- 6. Second Scoop
def tex_wing():
    c = Canvas(16, 16, WHITE)
    for x in range(2, 16, 4):
        c.rect(x, 0, x, 9, "#d9ccff")
    c.rect(0, 0, 15, 2, LAV)
    c.rect(0, 13, 15, 15, "#fff8e0")
    return c


def build_second_scoop(kit, root, A):
    R = kit.rand
    float_p = kit.empty(f"{A} float", root, (0, 0, 0.11))
    waffle = tex_mat(f"{A} waffle", tex_waffle(), 0.6)
    tube(kit, f"{A} cone", [(0, 0, 0.0), (0, 0, 0.08), (0, 0, 0.16)], [0.006, 0.03, 0.052], waffle, float_p, sides=8,
         caps=(True, False))
    tube(kit, f"{A} cone rim", [(0, 0, 0.152), (0, 0, 0.17)], [0.057, 0.057], solid(kit, f"{A} rim", GOLD, 0.7, shade=GOLD_D),
         float_p, sides=8)
    van = dict(FL["vanilla"], cream="#fff6d8", hi=WHITE)
    s1 = tex_mat(f"{A} scoop gold", tex_scoop(van, R, sparkle=True), 0.95, ext='REPEAT')
    s2 = tex_mat(f"{A} scoop pink", tex_scoop(FL["strawberry"], R, sparkle=True), 0.95, ext='REPEAT')
    scoop(kit, f"{A} scoop 1", float_p, (0, 0, 0.15), 0.054, s1, None, drips=3)
    scoop(kit, f"{A} scoop 2", float_p, (0, 0, 0.222), 0.047, s2, None, drips=2)
    lowball(kit, f"{A} cherry", (0, 0, 0.312), (0.016, 0.016, 0.015), solid(kit, f"{A} cherry", RED, 0.9), float_p)
    tube(kit, f"{A} stem", [(0, 0, 0.322), (0.006, 0, 0.34), (0.016, 0, 0.352)], 0.0025, solid(kit, f"{A} stem", LEAF_D),
         float_p, sides=4)
    # halo on its own pivot so it can spin
    halo_p = kit.empty(f"{A} halo", float_p, (0, 0.004, 0.385), (12, 0, 0))
    ring = [(0.07 + 0.011 * math.cos(2 * math.pi * k / 6), 0.011 * math.sin(2 * math.pi * k / 6), k / 6) for k in range(7)]
    lathe(kit, f"{A} halo", ring, solid(kit, f"{A} halo", YEL, 2.2, shade="#ffe98a"), halo_p, sides=12)
    # wings on hinge pivots at the back of the scoop
    wing_m = tex_mat(f"{A} wing", tex_wing(), 0.9)
    outline = [(0, 0.03), (0.04, 0.07), (0.09, 0.095), (0.14, 0.088), (0.165, 0.07), (0.15, 0.052), (0.128, 0.05),
               (0.135, 0.03), (0.11, 0.03), (0.112, 0.01), (0.085, 0.012), (0.083, -0.01), (0.058, -0.005),
               (0.05, -0.025), (0.028, -0.016), (0.0, -0.01)]
    for s, nm in ((1, "L"), (-1, "R")):
        wp = kit.empty(f"{A} wing {nm}", float_p, (s * 0.03, 0.035, 0.18), (0, 0, s * -28))
        pts = [(s * x, z) for x, z in outline]
        flat_poly(kit, f"{A} wing {nm}", pts if s > 0 else pts[::-1], wing_m, wp)
    for i, (p, size, col) in enumerate((((0.1, -0.03, 0.3), 0.03, YEL), ((-0.11, -0.02, 0.22), 0.024, WHITE),
                                        ((0.085, -0.04, 0.12), 0.018, PINK), ((-0.07, -0.05, 0.36), 0.02, MINT),
                                        ((0.04, -0.07, 0.42), 0.016, WHITE), ((-0.1, -0.04, 0.06), 0.016, YEL))):
        fx_star(kit, float_p, f"{A} sparkle {i}", p, 4, size, size * 0.3, col, 2.0, rot=(0, R.uniform(0, 30), 0))
    point_light(kit, float_p, f"{A} glow", (0, -0.06, 0.25), "#ffd36b", 6, 1.2, 0.05)
    ring_mesh(kit, f"{A} pickup ring", 0.1, 0.14, solid(kit, f"{A} pickup ring", PINK, 1.6), root, (0, 0, 0.003), segs=16)
    ring_mesh(kit, f"{A} pickup ring inner", 0.06, 0.075, solid(kit, f"{A} pickup ring inner", YEL, 1.6), root,
              (0, 0, 0.004), segs=12)
    socket(kit, A, "hand", float_p, (0, 0, 0.07))


# ---------------------------------------------------------------- 7. sprinkles refill
def tex_sprinkle_box(rand):
    """96x48: front (0-39), back (40-79), side (80-95)."""
    c = Canvas(96, 48, PINK)
    for i in range(260):
        x, y = rand.randrange(80), rand.randrange(48)
        col = SPRINKLES[i % 7]
        if col == PINK:
            col = BLUE
        if rand.random() < 0.5:
            c.rect(x, y, x + 1, y, col)
        else:
            c.rect(x, y, x, y + 1, col)
    for x0 in (0, 40):
        c.rect(x0, 40, x0 + 39, 47, BLUE)
        c.rect(x0, 0, x0 + 39, 3, YEL)
        c.rect(x0 + 1, 18, x0 + 38, 30, WHITE); c.rect(x0 + 1, 18, x0 + 38, 18, "#e6dcd2")
    text(c, "REFILL", 20 - 11, 46, WHITE)
    text(c, "SPRINKLES", 20 - 17, 27, BLUE, shadow="#9cc4ff")
    for x in range(4, 37, 3):
        c.rect(x, 20, x + 1, 20, SPRINKLES[x % 7] if SPRINKLES[x % 7] != WHITE else PURP)
    cone_icon(c, 20, 5, 8, PINK)
    text(c, "TOPPING", 60 - 13, 27, PINK)
    text(c, "1", 60 - 1, 46, WHITE)
    c.rect(80, 0, 95, 47, WHITE)
    for x in range(80, 96, 4):
        c.rect(x, 0, x + 1, 47, PINK)
    c.rect(80, 40, 95, 47, BLUE)
    return c


def build_sprinkles(kit, root, A):
    R = kit.rand
    W, D, Hh = 0.1, 0.065, 0.17
    m = tex_mat(f"{A} box", tex_sprinkle_box(R))
    tbox(kit, f"{A} box", (0, 0, Hh / 2), (W, D, Hh), m, root,
         uv={'ny': (0, 0, 40 / 96, 1), 'py': (40 / 96, 0, 80 / 96, 1), 'nx': (80 / 96, 0, 1, 1), 'px': (80 / 96, 0, 1, 1),
             'pz': (82 / 96, 0.86, 0.99, 0.99), 'nz': (0.1, 0.0, 0.2, 0.05)})
    tbox(kit, f"{A} spout hole", (0, -D / 2 + 0.012, Hh + 0.0008), (0.044, 0.02, 0.0016), solid(kit, f"{A} hole", INK, 0.1),
         root)
    hinge = kit.empty(f"{A} spout hinge", root, (0, -D / 2, Hh + 0.001), (125, 0, 0))
    tbox(kit, f"{A} spout", (0, 0.012, 0.0015), (0.046, 0.024, 0.003), solid(kit, f"{A} spout", STEEL, shade="#a9a2e0"),
         hinge)
    spr = sprinkle_mats(kit)
    for i in range(12):  # stream falling out of the spout plus a little pile
        f = i / 11
        p = (R.uniform(-0.012, 0.012) + 0.02 * f, -D / 2 - 0.012 - 0.05 * f, Hh - 0.005 - 0.15 * f * f)
        tbox(kit, f"{A} falling {i}", (0, 0, 0), (0.005, 0.005, 0.016), spr[i % 7], root, loc=p,
             rot=(R.uniform(0, 180), R.uniform(0, 180), 0))
    for i in range(10):
        a, rr = R.uniform(0, 2 * math.pi), R.uniform(0, 0.03)
        tbox(kit, f"{A} pile {i}", (0, 0, 0), (0.005, 0.016, 0.005), spr[i % 7], root,
             loc=(0.02 + math.cos(a) * rr, -D / 2 - 0.07 + math.sin(a) * rr, 0.003 + 0.003 * (i % 3)),
             rot=(0, R.uniform(-20, 20), R.uniform(0, 180)))
    socket(kit, A, "hand", root, (0, 0, Hh * 0.45))


# ---------------------------------------------------------------- 8. money
def tex_coin(face=True):
    c = Canvas(32, 16, GOLD_D)
    for y in range(16):
        c.set(0, y, GOLD if y % 2 else GOLD_D); c.set(1, y, GOLD_D if y % 2 else GOLD)
    for x0 in (8, 24):
        disc(c, x0, 8, 7, GOLD_D)
        disc(c, x0, 8, 6, GOLD)
        disc(c, x0, 8, 5, "#ffe46a")
    glyph(c, '$', 8 - 2, 11, "#c27a10")
    c.dots([(5, 12), (4, 11), (12, 5)], WHITE)
    # back: foil peeled off with a bite of chocolate showing
    disc(c, 26, 10, 4, CHOC); disc(c, 26, 10, 3, "#8a4a26")
    for x, y in ((29, 13), (30, 11), (29, 8), (23, 14)):
        c.set(x, y, "#c27a10")
    c.dots([(20, 5), (21, 6)], WHITE)
    return c


def tex_bill():
    c = Canvas(16, 32, "#5fd38a")
    c.rect(0, 0, 15, 1, "#2f9e5a"); c.rect(0, 30, 15, 31, "#2f9e5a")
    c.rect(0, 0, 0, 31, "#2f9e5a"); c.rect(15, 0, 15, 31, "#2f9e5a")
    disc(c, 8, 16, 5, "#9cf0b8")
    glyph(c, '$', 6, 19, "#1f7a44")
    c.dots([(3, 4), (12, 27), (3, 27), (12, 4)], "#1f7a44")
    return c


def tex_jar_band():
    c = Canvas(80, 16, PINK)
    c.rect(0, 0, 79, 1, "#d63a86"); c.rect(0, 14, 79, 15, "#d63a86")
    c.rect(0, 2, 79, 2, WHITE); c.rect(0, 13, 79, 13, WHITE)
    for x0 in (50, 10):
        text(c, "TIPS", x0 - 7, 10, WHITE, shadow="#a8206a")
    for cx in (30, 70):
        glyph(c, 'h', cx - 2, 10, YEL)
    return c


def build_tip_jar(kit, root, A):
    R = kit.rand
    gold = tex_mat(f"{A} coins", tex_coin(), 0.5, ext='REPEAT')
    glass = glass_mat(f"{A} glass")
    lathe(kit, f"{A} jar", [(0, 0, 0.01), (0.068, 0, 0.05), (0.078, 0.012, 0.15), (0.08, 0.15, 0.6), (0.068, 0.172, 0.7),
                            (0.06, 0.18, 0.75), (0.065, 0.186, 0.82), (0.066, 0.2, 0.9), (0.058, 0.2, 0.95),
                            (0.056, 0.184, 0.99)], glass, root, sides=10)
    lathe(kit, f"{A} coin pile", [(0.074, 0.006, 0.1), (0.076, 0.09, 0.4), (0.05, 0.118, 0.7), (0, 0.126, 0.95)], gold,
          root, sides=10, jit=0.004)
    lathe(kit, f"{A} label", [(0.0815, 0.062, 0.03), (0.0815, 0.118, 0.97)], tex_mat(f"{A} label", tex_jar_band(),
                                                                                       ext='REPEAT'),
          root, sides=10, smooth=False)
    coin_m = tex_mat(f"{A} coin", tex_coin(), 0.6)
    for i in range(6):
        a, rr = 2 * math.pi * i / 6, 0.03 + 0.012 * (i % 2)
        coin_mesh(kit, f"{A} coin {i}", 0.02, 0.005, coin_m, root,
                  loc=(math.cos(a) * rr, math.sin(a) * rr, 0.13 + 0.01 * (i % 3)),
                  rot=(R.uniform(50, 85), R.uniform(-20, 20), math.degrees(a) + 90), sides=8)
    bill = tex_mat(f"{A} bill", tex_bill(), 0.45)
    for i, (x, y, rz, tilt) in enumerate(((-0.02, 0.015, 20, -14), (0.025, -0.01, -35, 18))):
        bp = kit.empty(f"{A} bill {i}", root, (x, y, 0.12), (tilt, 0, rz))
        tbox(kit, f"{A} bill {i} low", (0, 0, 0.04), (0.05, 0.003, 0.08), bill, bp,
             uv={'all': (0.0, 0.0, 1.0, 0.6)})
        tbox(kit, f"{A} bill {i} fold", (0, -0.008, 0.095), (0.05, 0.003, 0.04), bill, bp, rot=(-28, 0, 0),
             uv={'all': (0.0, 0.6, 1.0, 1.0)})
    socket(kit, A, "coin drop", root, (0, 0, 0.2))


def build_tip_coin(kit, root, A):
    R = kit.rand
    spin = kit.empty(f"{A} spin", root, (0, 0, 0.075))
    coin_mesh(kit, f"{A} coin", 0.045, 0.014, tex_mat(f"{A} coin", tex_coin(), 0.75), spin, sides=10)
    tube(kit, f"{A} rim", [(0, -0.0075, 0), (0, 0.0075, 0)], 0.0462, solid(kit, f"{A} rim", GOLD_D, 0.6), spin, sides=10,
         side=(0, 0, 1), caps=(False, False))
    # "+$" popup in pixel voxels, yellow over a pink drop shadow
    pop = kit.empty(f"{A} popup", root, (0, 0, 0.17))
    yel, pink = solid(kit, f"{A} pop yellow", YEL, 1.3), solid(kit, f"{A} pop back", ORNG, 0.9)
    cells = {}
    for gx, g in ((0, '+'), (4, '$')):
        rows = GLYPHS[g]
        off = (len(GLYPHS['$']) - len(rows)) // 2
        for r, row in enumerate(rows):
            for q, b in enumerate(row):
                if b == '#':
                    cells[(gx + q, 0, 6 - r - off)] = yel
                    cells[(gx + q, 1, 6 - r - off)] = pink
    kit.voxels(f"{A} popup", cells, 0.009, pop, loc=(-0.045, 0, -0.03))
    for i, (p, s, col) in enumerate((((0.06, -0.01, 0.12), 0.018, YEL), ((-0.062, -0.01, 0.06), 0.014, WHITE),
                                     ((0.05, -0.01, 0.03), 0.01, PINK))):
        fx_star(kit, root, f"{A} sparkle {i}", p, 4, s, s * 0.3, col, 2.0, rot=(0, R.uniform(0, 40), 0))


# ---------------------------------------------------------------- assembly
def run(kit, root, A, fn, *a):
    fn(kit, root, A, *a)
    for ob in root.children_recursive:
        if not ob.name.startswith(A):
            ob.name = f"{A} {ob.name}"


def entry(A, fn, *a):
    return (A, lambda kit, root: run(kit, root, A, fn, *a))


CAP = {"vanilla": "Vanilla", "chocolate": "Chocolate", "strawberry": "Strawberry", "mint": "Mint"}
ITEMS = []
for fl in FLAVORS:
    ITEMS.append((f"Pint {CAP[fl]} Full", build_pint, (fl, True)))
for fl in FLAVORS:
    ITEMS.append((f"Pint {CAP[fl]} Empty", build_pint, (fl, False)))
for fl in FLAVORS:
    ITEMS.append((f"Scoop Grenade {CAP[fl]}", build_grenade, (fl,)))
for fl in FLAVORS:
    ITEMS.append((f"Flavor Tub {CAP[fl]}", build_tub, (fl, 8)))
ITEMS += [
    ("Flavor Tub Mint Half", build_tub, ("mint", 4)),
    ("Milk Crate", build_milk_crate, ()),
    ("Sugar Sack", build_sugar_sack, ()),
    ("Cocoa Bag", build_cocoa_bag, ()),
    ("Strawberry Basket", build_strawberry_basket, ()),
    ("Mint Bundle", build_mint_bundle, ()),
    ("Vanilla Bean Box", build_vanilla_box, ()),
    ("Gun Crate Closed", build_gun_crate, (False,)),
    ("Gun Crate Open", build_gun_crate, (True,)),
    ("Second Scoop", build_second_scoop, ()),
    ("Sprinkles Refill", build_sprinkles, ()),
    ("Tip Jar", build_tip_jar, ()),
    ("Tip Coin", build_tip_coin, ()),
]
ASSETS = [entry(A, fn, *a) for A, fn, a in ITEMS]
SPACING = 4


# ---------------------------------------------------------------- scene: everything on a kitchen counter
def tex_counter_top(rand):
    c = Canvas(16, 16, "#e4dcff")
    c.speckle(rand, ["#d2c6ff", "#f2eeff", "#c8f5e6", "#ffd0e6"], 40)
    return c


def tex_cabinet():
    c = Canvas(32, 32, PINK)
    c.rect(2, 3, 29, 29, "#ff7dbb"); c.rect(3, 4, 28, 28, PINK)
    c.rect(0, 0, 31, 1, "#d63a86"); c.rect(15, 0, 16, 31, "#d63a86")
    c.rect(12, 16, 13, 21, YEL); c.rect(18, 16, 19, 21, YEL)
    return c


def tex_tile():
    c = Canvas(16, 16, "#f2eaff")
    c.rect(0, 0, 15, 0, LAV); c.rect(0, 0, 0, 15, LAV)
    c.rect(8, 8, 15, 15, "#c8f5e6"); c.rect(8, 8, 15, 8, LAV); c.rect(8, 8, 8, 15, LAV)
    return c


def tex_floor():
    c = Canvas(16, 16, "#5b3fa0")
    c.rect(0, 0, 7, 7, "#7a5ac8"); c.rect(8, 8, 15, 15, "#7a5ac8")
    return c


COUNTER_Z = 0.92


def build_counter_scene(kit, root):
    R = kit.rand
    L = 4.9
    tbox(kit, "counter floor", (0, -0.6, -0.01), (8.0, 4.0, 0.02), tex_mat("counter floor", tex_floor(), 0.25, ext='REPEAT'),
         root, uv={'pz': (0, 0, 20, 10)})
    tbox(kit, "counter body", (0, 0.02, 0.44), (L - 0.06, 0.96, 0.88), tex_mat("cabinet", tex_cabinet(), ext='REPEAT'), root,
         uv={'ny': (0, 0, 8, 1), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})
    tbox(kit, "counter kick", (0, -0.45, 0.04), (L - 0.04, 0.06, 0.08), solid(kit, "kick", INK, 0.1), root)
    tbox(kit, "counter top", (0, 0.0, COUNTER_Z - 0.02), (L, 1.04, 0.04), tex_mat("counter top", tex_counter_top(R),
                                                                                    ext='REPEAT'),
         root, uv={'pz': (0, 0, 12, 2), 'ny': (0, 0, 12, 0.1)})
    tbox(kit, "counter edge", (0, -0.522, COUNTER_Z - 0.02), (L + 0.01, 0.012, 0.044), solid(kit, "edge", MINT), root)
    tbox(kit, "backsplash", (0, 0.56, COUNTER_Z + 0.75), (L + 0.2, 0.08, 1.5), tex_mat("tile", tex_tile(), 0.12, ext='REPEAT'),
         root, uv={'ny': (0, 0, 24, 7)})
    tbox(kit, "shelf", (0, 0.46, COUNTER_Z + 1.05), (L - 0.4, 0.14, 0.03), solid(kit, "shelf", MINT), root)
    # the cook, for scale
    cook = kit.empty("cook", root, (-2.78, -0.05, 0), (0, 0, -12))
    build_player(kit, cook)
    z = COUNTER_Z
    back = [("Gun Crate Closed", -2.06, 0.2), ("Gun Crate Open", -1.24, 0.16), ("Strawberry Basket", -0.6, 0.25),
            ("Vanilla Bean Box", -0.1, 0.22), ("Milk Crate", 0.4, 0.26), ("Sugar Sack", 0.9, 0.27),
            ("Cocoa Bag", 1.35, 0.28), ("Mint Bundle", 1.78, 0.27), ("Second Scoop", 2.22, 0.2)]
    front, x = [], -2.2
    for fl in FLAVORS:
        front.append((f"Pint {CAP[fl]} Full", x)); x += 0.12
    for fl in FLAVORS:
        front.append((f"Pint {CAP[fl]} Empty", x)); x += 0.12
    x += 0.03
    for fl in FLAVORS:
        front.append((f"Scoop Grenade {CAP[fl]}", x)); x += 0.13
    front += [("Sprinkles Refill", x + 0.06), ("Tip Jar", x + 0.26), ("Tip Coin", x + 0.46)]
    front += [(f"Flavor Tub {n}", 0.08 + 0.34 * i) for i, n in enumerate(("Vanilla", "Chocolate", "Strawberry", "Mint",
                                                                          "Mint Half"))]
    table = {A: (fn, a) for A, fn, a in ITEMS}
    for A, px, py in back:
        sub = kit.empty(f"{A} (counter)", root, (px, py, z), (0, 0, R.uniform(-4, 4)))
        run(kit, sub, A, table[A][0], *table[A][1])
    for A, px in front:
        py = -0.24 if A.startswith("Flavor") else -0.3
        sub = kit.empty(f"{A} (counter)", root, (px, py, z), (0, 0, R.uniform(-6, 6)))
        run(kit, sub, A, table[A][0], *table[A][1])


SCENES = [
    dict(name="kitchen counter", build=build_counter_scene, cam=((-0.35, -4.9, 3.1), (-0.35, 0.05, 0.95), 28), res=(1600, 900)),
    dict(name="kitchen counter close", build=build_counter_scene, cam=((-1.3, -1.6, 1.62), (-1.3, -0.12, 1.0), 32),
         res=(1600, 900)),
]
