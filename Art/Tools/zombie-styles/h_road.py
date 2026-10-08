"""Road batch (style H): tiling road chunks, roadside town buildings and roadside props.

Chunk contract (every chunk): 20 x 20 m, origin at the chunk center on the ground, travel toward -Y (entry edge y=+10,
exit edge y=-10). Asphalt |x| <= 4 with its top at z=0, a 0.15 m step at |x| = 4 (curb or dirt bank), roadside top at
z=0.15 out to |x| = 10, slab bottom at z=-0.25. Paint: white edge lines at |x| = 3.7, yellow center dashes 2 m long
centered at y = 0, +-4, +-8. Ground UVs are planar in chunk coordinates with periods that divide 20 m, so textures
tile across seams too. Curve Right = Curve Left mirrored across X (root scale x = -1).
Sockets: '<Chunk> socket entry' / 'socket exit' (local -Y = travel direction), buildings 'socket door'."""
from style_H import *

SPACING = 50
HALF, ROAD, SIDE, BOT = 10.0, 4.0, 0.15, -0.25
CURB_W, WALK_X, SHOULDER_X = 0.3, 7.0, 5.5
LINE_X, LINE_W, PAINT_Z = 3.7, 0.15, 0.006
DASHES = (8, 4, 0, -4, -8)
CUT = "#010203"   # texels of this color become transparent in cut_mat

GLYPHS = dict(FONT)
GLYPHS.update({'0': ("###", "#.#", "#.#", "#.#", "###"), '2': ("##.", "..#", ".#.", "#..", "###"),
               '5': ("###", "#..", "##.", "..#", "##.")})


def text2(c, s, x, y, col, k=1, shadow=None):
    """style_H.text with extra digit glyphs."""
    if shadow:
        text2(c, s, x + k, y - k, shadow, k)
    for ch in s:
        for r, row in enumerate(GLYPHS.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)
        x += 4 * k


# ---------------------------------------------------------------- materials
def tm(kit, name, make, emit=0.32, ext='EXTEND'):
    cache = kit.__dict__.setdefault("_road_tex", {})
    key = (name, emit, ext)
    if key not in cache:
        cache[key] = tex_mat(name, make(), emit, ext=ext)
    return cache[key]


def cut_mat(kit, name, make, emit=0.32):
    """Repeating pixel texture whose CUT texels are transparent (chain-link, scalloped valance)."""
    cache = kit.__dict__.setdefault("_road_tex", {})
    if name not in cache:
        cv = make()
        m = tex_mat(name, cv, emit, ext='REPEAT')
        key = rgb(CUT)
        img = bpy.data.images.new(f"H {name} cut", cv.w, cv.h, alpha=True)
        flat = []
        for col in cv.p:
            flat.extend((col[0], col[1], col[2], 0.0 if col == key else 1.0))
        img.pixels.foreach_set(flat)
        img.update()
        img.pack()
        nt = m.node_tree
        tx = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')
        tx.image = img
        nt.links.new(tx.outputs["Alpha"], next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED').inputs["Alpha"])
        cache[name] = m
    return cache[name]


# ---------------------------------------------------------------- 2D helpers and the mesh builder
def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def area2(poly):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))


def ccw(poly):
    poly = [(p[0], p[1]) for p in poly]
    return poly if area2(poly) > 0 else poly[::-1]


def arc(c, r, a0, a1, n):
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def resample(path, step=1.0):
    out = [tuple(path[0])]
    for a, b in zip(path, path[1:]):
        n = max(1, round(math.dist(a, b) / step))
        out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(1, n + 1)]
    return out


def offset(path, d):
    """Offset an open 2D polyline sideways by d (+ = left of travel), mitered."""
    P = [Vector((p[0], p[1])) for p in path]
    out = []
    for i in range(len(P)):
        ts = [(P[j + 1] - P[j]).normalized() for j in (i - 1, i) if 0 <= j < len(P) - 1]
        t = (ts[0] + ts[-1]).normalized()
        n = Vector((-t.y, t.x))
        out.append(tuple(P[i] + n * d / max(n.dot(Vector((-ts[0].y, ts[0].x))), 0.3)))
    return out


class MB:
    """Accumulates flat-shaded faces with UVs and material indices, then becomes one object."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")

    def face(self, pts, uvs, mi=0):
        f = self.bm.faces.new([self.bm.verts.new(Vector(p)) for p in pts])
        f.material_index = mi
        for lp, c in zip(f.loops, uvs):
            lp[self.uv].uv = c

    def up(self, pts, mi, s):
        """Horizontal face (any winding) turned to face +Z, planar UVs."""
        pts = [tuple(p) for p in pts]
        if area2(pts) < 0:
            pts = pts[::-1]
        self.face(pts, [(p[0] * s, p[1] * s) for p in pts], mi)

    def prism(self, poly, z0, z1, mi, s=0.25, side=None, top=True):
        poly = ccw(poly)
        if top:
            self.face([(x, y, z1) for x, y in poly], [(x * s, y * s) for x, y in poly], mi)
        L = 0.0
        for a, b in zip(poly, poly[1:] + poly[:1]):
            l = math.dist(a, b)
            self.face([(*a, z0), (*b, z0), (*b, z1), (*a, z1)],
                      [(L * s, z0 * s), ((L + l) * s, z0 * s), ((L + l) * s, z1 * s), (L * s, z1 * s)], mi if side is None else side)
            L += l

    def ribbon(self, pts, w, z, mi, s=0.5):
        a, b = offset(pts, -w / 2), offset(pts, w / 2)
        L = 0.0
        for i in range(len(pts) - 1):
            l = math.dist(pts[i], pts[i + 1])
            q = [(*a[i], z), (*a[i + 1], z), (*b[i + 1], z), (*b[i], z)]
            uv = [(L * s, 0), ((L + l) * s, 0), ((L + l) * s, 1), (L * s, 1)]
            if area2(q) < 0:
                q, uv = q[::-1], uv[::-1]
            self.face(q, uv, mi)
            L += l

    def obj(self, kit, name, mats, parent, loc=(0, 0, 0), rot=(0, 0, 0)):
        return kit.mesh_from_bmesh(name, self.bm, list(mats), parent, loc, rot, smooth=False)


def disc_face(mb, c, r, n, e1, e2, mi, a0=0.0):
    """n-gon facing e1 x e2 with polar UVs (texture center = disc center)."""
    pts, uvs = [], []
    for k in range(n):
        a = a0 + 2 * math.pi * k / n
        pts.append(Vector(c) + (Vector(e1) * math.cos(a) + Vector(e2) * math.sin(a)) * r)
        uvs.append((0.5 + 0.5 * math.cos(a), 0.5 + 0.5 * math.sin(a)))
    mb.face(pts, uvs, mi)


def plate(mb, c, r, n, depth, mi_front, mi_back, a0=0.0):
    """Round/polygonal sign plate facing -Y: textured front, back and rim."""
    c = Vector(c)
    h = Vector((0, depth / 2, 0))
    disc_face(mb, c - h, r, n, (1, 0, 0), (0, 0, 1), mi_front, a0)
    disc_face(mb, c + h, r, n, (-1, 0, 0), (0, 0, 1), mi_back, math.pi - a0)
    ring = [c + Vector((math.cos(a0 + 2 * math.pi * k / n), 0, math.sin(a0 + 2 * math.pi * k / n))) * r for k in range(n)]
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        mb.face([b - h, a - h, a + h, b + h], [(0, 0)] * 4, mi_back)


def extrude_y(mb, prof, y0, y1, mi, origin=(0, 0, 0), mi_cap=None):
    """Extrude a CCW (x, z) profile from y0 (front cap, faces -Y) to y1."""
    o = Vector(origin)
    F = [o + Vector((x, y0, z)) for x, z in prof]
    B = [o + Vector((x, y1, z)) for x, z in prof]
    mc = mi if mi_cap is None else mi_cap
    mb.face(F, [(0.5 + x, 0.5 + z) for x, z in prof], mc)
    mb.face(B[::-1], [(0.5 + x, 0.5 + z) for x, z in prof[::-1]], mc)
    for k in range(len(prof)):
        k2 = (k + 1) % len(prof)
        mb.face([F[k2], F[k], B[k], B[k2]], [(0, 0), (1, 0), (1, 1), (0, 1)], mi)


def place(kit, fn, parent, name, loc, rz=0.0, rot=None, scale=1.0):
    piv = kit.empty(name, parent, loc, rot or (0, 0, rz), (scale, scale, scale))
    fn(kit, piv, name)
    return piv


# ---------------------------------------------------------------- textures: ground
def tex_road(rand):
    c = Canvas(64, 64, ASPH)
    c.speckle(rand, ["#4a4068", "#2f2745", "#55497a"], 800)
    for _ in range(4):
        x, y = rand.randrange(64), rand.randrange(64)
        for _ in range(rand.randint(8, 18)):
            c.set(x, y, "#231c36")
            x += rand.choice((-1, 0, 1))
            y = (y + 1) % 64
    return c


def tex_sidewalk(rand):
    c = Canvas(32, 32, "#cfc6f0")
    c.speckle(rand, ["#c1b6e8", "#ddd6fa", "#b8acdf"], 180)
    for k in (0, 16):
        c.rect(0, k, 31, k, "#9d90cc")
        c.rect(k, 0, k, 31, "#9d90cc")
    c.dots([(5, 9), (6, 8), (7, 8), (8, 7)], "#a99bd6")
    return c


def tex_grass(rand):
    c = Canvas(32, 32, "#36a46a")
    c.speckle(rand, ["#2c8c5a", "#43bd78", "#4fd68a", "#2f9662"], 330)
    for _ in range(6):
        c.set(rand.randrange(32), rand.randrange(32), rand.choice((PINK, YEL, WHITE)))
    return c


def tex_puddle(rand):
    c = Canvas(16, 16, "#2a2f6b")
    c.speckle(rand, ["#353c80", "#232860"], 40)
    c.dots([(4, 11), (5, 11), (6, 10), (9, 6), (10, 6)], "#8fa4ff")
    return c


# ---------------------------------------------------------------- road chunks
G_ASPH, G_WALK, G_GRASS, G_DIRT, G_SOIL, G_CURB, G_HOLE, G_MUD, G_CRACK = 0, 1, 2, 3, 4, (5, 6), 7, 8, 9
S_ASPH, S_WALK, S_GRASS, S_DIRT = 0.2, 0.5, 0.25, 0.25


def ground_mats(kit):
    R = kit.rand
    return [tm(kit, "road asphalt", lambda: tex_road(R), 0.15, 'REPEAT'),
            tm(kit, "sidewalk", lambda: tex_sidewalk(R), 0.22, 'REPEAT'),
            tm(kit, "grass", lambda: tex_grass(R), 0.2, 'REPEAT'),
            tm(kit, "dirt", lambda: tex_dirt(R), 0.15, 'REPEAT'),
            solid(kit, "soil", "#4a2c48", 0.12),
            solid(kit, "curb pink", PINK, 0.35), solid(kit, "curb white", WHITE, 0.35),
            solid(kit, "pothole", "#2a2140", 0.08),
            tm(kit, "puddle", lambda: tex_puddle(R), 0.45),
            solid(kit, "crack", "#1d1630", 0.05)]


def walk(mb, poly):
    mb.prism(poly, BOT, SIDE, G_WALK, S_WALK, G_SOIL)


def lawn(mb, poly):
    mb.prism(poly, BOT, SIDE, G_GRASS, S_GRASS, G_SOIL)


def shoulder(mb, poly):
    mb.prism(poly, BOT, SIDE, G_DIRT, S_DIRT)


def curbs(mb, path, d, f=lambda poly: poly, skip=()):
    """Candy-striped curb blocks between a path and its offset by d (+ = left of travel)."""
    q = offset(path, d)
    for i in range(len(path) - 1):
        if i not in skip:
            mb.prism(f([path[i], path[i + 1], q[i + 1], q[i]]), BOT, SIDE, G_CURB[i % 2], 0.5)


def town_side(mb, sx, skip=()):
    curbs(mb, resample([(sx * ROAD, HALF), (sx * ROAD, -HALF)]), sx * CURB_W, skip=skip)
    walk(mb, rect(sx * (ROAD + CURB_W), -HALF, sx * WALK_X, HALF))
    lawn(mb, rect(sx * WALK_X, -HALF, sx * HALF, HALF))


def rural_side(mb, sx):
    shoulder(mb, rect(sx * ROAD, -HALF, sx * SHOULDER_X, HALF))
    lawn(mb, rect(sx * SHOULDER_X, -HALF, sx * HALF, HALF))


def paint(kit, root, p, white=(), yellow=(), bars=()):
    mb = MB()
    for pts in white:
        mb.ribbon(pts, LINE_W, PAINT_Z, 1)
    for pts in yellow:
        mb.ribbon(pts, LINE_W, PAINT_Z, 0)
    for pts, w in bars:
        mb.ribbon(pts, w, PAINT_Z, 1)
    return mb.obj(kit, f"{p} paint", [solid(kit, "lane yellow", YEL, 0.5), solid(kit, "lane white", WHITE, 0.4)], root)


def straight_lines():
    return [[(sx * LINE_X, HALF), (sx * LINE_X, -HALF)] for sx in (1, -1)], [[(0, y + 1), (0, y - 1)] for y in DASHES]


def sockets(kit, root, p, exits):
    kit.empty(f"{p} socket entry", root, (0, HALF, 0))
    for nm, loc, rz in exits:
        kit.empty(f"{p} socket {nm}", root, loc, (0, 0, rz))


def town_straight(kit, root, p):
    mb = MB()
    mb.prism(rect(-ROAD, -HALF, ROAD, HALF), BOT, 0.0, G_ASPH, S_ASPH)
    for sx in (1, -1):
        town_side(mb, sx)
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white, yellow = straight_lines()
    paint(kit, root, p, white, yellow)
    sockets(kit, root, p, [("exit", (0, -HALF, 0), 0)])
    d = kit.empty(f"{p} dressing", root)
    place(kit, street_lamp, d, f"{p} lamp 0", (-4.7, 4.0, SIDE), 90)
    place(kit, street_lamp, d, f"{p} lamp 1", (4.7, -6.0, SIDE), -90)
    place(kit, fire_hydrant, d, f"{p} hydrant", (4.75, 3.2, SIDE), -90)
    place(kit, trash_can, d, f"{p} trash can", (-5.3, -5.5, SIDE), 20)
    place(kit, bush, d, f"{p} bush 0", (8.6, 7.6, SIDE), 30)
    place(kit, bush, d, f"{p} bush 1", (-8.7, -7.8, SIDE), 200)


def rural_straight(kit, root, p):
    mb = MB()
    mb.prism(rect(-ROAD, -HALF, ROAD, HALF), BOT, 0.0, G_ASPH, S_ASPH)
    for sx in (1, -1):
        rural_side(mb, sx)
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white, yellow = straight_lines()
    paint(kit, root, p, white, yellow)
    sockets(kit, root, p, [("exit", (0, -HALF, 0), 0)])
    d = kit.empty(f"{p} dressing", root)
    pole = place(kit, lambda k, r, n: power_pole(k, r, n, stubs=False), d, f"{p} power pole", (-6.4, 0.0, SIDE), 0)
    for i, x in enumerate(POLE_WIRES):
        for sy in (1, -1):
            wire(kit, f"{p} wire {i} {sy}", pole, x, sy, 10.0)
    place(kit, hay_bale, d, f"{p} hay bale 0", (7.4, 3.6, SIDE), 18)
    place(kit, hay_bale, d, f"{p} hay bale 1", (8.7, 1.3, SIDE), -12)
    place(kit, round_tree, d, f"{p} round tree", (8.2, -6.2, SIDE), 40)
    place(kit, pine_tree, d, f"{p} pine tree", (-8.4, 6.6, SIDE), 0)
    place(kit, bush, d, f"{p} bush", (-8.8, -8.6, SIDE), 70)
    place(kit, mailbox, d, f"{p} mailbox", (5.0, -2.2, SIDE), -90)


def corner_block(mb, sy):
    """+X roadside block of the T-junction, between the main road (x = 4) and the side road edge (y = sy * 4)."""
    f = (lambda poly: poly) if sy > 0 else (lambda poly: [(x, -y) for x, y in poly])
    path = resample([(ROAD, HALF), (ROAD, 6.0)]) + arc((6.0, 6.0), 2.0, 180, 270, 6)[1:] + resample([(6.0, ROAD), (HALF, ROAD)])[1:]
    curbs(mb, path, CURB_W, f)
    walk(mb, f(offset(path, CURB_W) + [(HALF, WALK_X), (WALK_X, WALK_X), (WALK_X, HALF)]))
    lawn(mb, f(rect(WALK_X, WALK_X, HALF, HALF)))


def t_junction(kit, root, p):
    mb = MB()
    mb.prism([(-ROAD, -HALF), (ROAD, -HALF), (ROAD, -ROAD), (HALF, -ROAD), (HALF, ROAD), (ROAD, ROAD), (ROAD, HALF), (-ROAD, HALF)],
             BOT, 0.0, G_ASPH, S_ASPH)
    town_side(mb, -1)
    for sy in (1, -1):
        corner_block(mb, sy)
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white = [[(-LINE_X, HALF), (-LINE_X, -HALF)], [(LINE_X, HALF), (LINE_X, 6.0)], [(LINE_X, -6.0), (LINE_X, -HALF)],
             [(6.0, LINE_X), (HALF, LINE_X)], [(6.0, -LINE_X), (HALF, -LINE_X)]]
    yellow = [[(0, y + 1), (0, y - 1)] for y in DASHES] + [[(7.0, 0), (9.0, 0)]]
    bars = [([(4.9, 0.25), (4.9, 3.55)], 0.45)] + [([(-3.25 + i * 0.93, 6.9), (-3.25 + i * 0.93, 5.1)], 0.5) for i in range(8)]
    paint(kit, root, p, white, yellow, bars)
    sockets(kit, root, p, [("exit", (0, -HALF, 0), 0), ("exit side", (HALF, 0, 0), 90)])
    d = kit.empty(f"{p} dressing", root)
    place(kit, stop_sign, d, f"{p} stop sign", (5.7, 5.3, SIDE), 90)
    place(kit, street_lamp, d, f"{p} lamp 0", (-4.7, 7.5, SIDE), 90)
    place(kit, street_lamp, d, f"{p} lamp 1", (4.7, -7.4, SIDE), -90)
    place(kit, fire_hydrant, d, f"{p} hydrant", (-4.75, -2.5, SIDE), 90)
    place(kit, trash_can, d, f"{p} trash can", (8.3, -4.9, SIDE), 0)
    place(kit, bush, d, f"{p} bush 0", (8.6, 8.6, SIDE), 0)
    place(kit, bush, d, f"{p} bush 1", (8.7, -8.5, SIDE), 120)


CURVE_C, CURVE_N = (HALF, HALF), 12


def ring(r0, r1, n=CURVE_N):
    return arc(CURVE_C, r1, 180, 270, n) + arc(CURVE_C, r0, 270, 180, n)


def curve_left(kit, root, p):
    """90 degree left turn: enters at y=+10 heading -Y, exits at x=+10 heading +X. Mirror on X for a right turn."""
    mb = MB()
    mb.prism(ring(10 - ROAD, 10 + ROAD), BOT, 0.0, G_ASPH, S_ASPH)
    shoulder(mb, ring(10 - SHOULDER_X, 10 - ROAD))
    lawn(mb, [CURVE_C] + arc(CURVE_C, 10 - SHOULDER_X, 180, 270, CURVE_N))
    shoulder(mb, ring(10 + ROAD, 10 + SHOULDER_X))
    lawn(mb, arc(CURVE_C, 10 + SHOULDER_X, 180, 270, CURVE_N) + [(HALF, -HALF), (-HALF, -HALF), (-HALF, HALF)])
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white = [arc(CURVE_C, 10 - LINE_X, 180, 270, 24), arc(CURVE_C, 10 + LINE_X, 180, 270, 24)]
    yellow = [arc(CURVE_C, 10, 180 + math.degrees(s / 10), 180 + math.degrees((s + 2) / 10), 4) for s in (1.0, 4.9, 8.8, 12.7)]
    paint(kit, root, p, white, yellow)
    sockets(kit, root, p, [("exit", (HALF, 0, 0), 90)])
    d = kit.empty(f"{p} dressing", root)
    for i, a in enumerate((200, 225, 250)):
        r = 10 + ROAD + 1.0
        place(kit, chevron_sign, d, f"{p} chevron {i}",
              (CURVE_C[0] + r * math.cos(math.radians(a)), CURVE_C[1] + r * math.sin(math.radians(a)), SIDE), a)
    place(kit, speed_sign, d, f"{p} speed sign", (-5.0, 8.0, SIDE), 180)
    place(kit, pine_tree, d, f"{p} pine 0", (-6.0, -6.5, SIDE), 0, scale=1.1)
    place(kit, pine_tree, d, f"{p} pine 1", (-2.0, -7.9, SIDE), 40, scale=0.85)
    place(kit, round_tree, d, f"{p} round tree", (-8.0, 2.0, SIDE), 10)
    place(kit, bush, d, f"{p} bush 0", (8.6, 8.4, SIDE), 0)
    place(kit, bush, d, f"{p} bush 1", (7.6, -8.6, SIDE), 50, scale=0.8)
    place(kit, hay_bale, d, f"{p} hay bale", (6.9, 7.6, SIDE), -40)


HOLE_C = (2, -2)


def broken_road(kit, root, p):
    """Town straight with a pothole, cracks, a heaved slab, a loose curb block and debris."""
    R = kit.rand
    mb = MB()
    H = {(x, y): 0.0 if abs(x) == 4 or abs(y) == 10 else R.uniform(-0.02, 0.012) - 0.04 * max(0.0, 2.0 - math.dist((x, y), HOLE_C))
         for x in range(-4, 5) for y in range(-10, 11)}
    hole_cells = {(1, -3), (2, -3), (1, -2), (2, -2)}
    for x in range(-4, 4):
        for y in range(-10, 10):
            if (x, y) not in hole_cells:
                mb.up([(x, y, H[x, y]), (x + 1, y, H[x + 1, y]), (x + 1, y + 1, H[x + 1, y + 1]), (x, y + 1, H[x, y + 1])], G_ASPH, S_ASPH)
    mb.prism(rect(-ROAD, -HALF, ROAD, HALF), BOT, 0.0, G_ASPH, S_ASPH, top=False)
    # pothole: jagged rim ring from the 2x2 m square to a 16-point broken edge, walls, mud floor, puddle
    hx, hy = HOLE_C
    sq = [(hx - 1, hy - 1), (hx, hy - 1), (hx + 1, hy - 1), (hx + 1, hy), (hx + 1, hy + 1), (hx, hy + 1), (hx - 1, hy + 1), (hx - 1, hy)]
    inner = []
    for k in range(16):
        a = math.radians(225 + 22.5 * k + R.uniform(-6, 6))
        r = (0.78 if k % 2 == 0 else 0.62) + R.uniform(-0.12, 0.12)
        inner.append((hx + r * math.cos(a), hy + r * math.sin(a), R.uniform(-0.05, 0.0)))
    for i in range(8):
        a, b = sq[i], sq[(i + 1) % 8]
        mb.up([(*a, H[a]), (*b, H[b]), inner[(2 * i + 2) % 16], inner[2 * i + 1], inner[2 * i]], G_ASPH, S_ASPH)
    depth = -0.32
    floor = [(hx + (x - hx) * 0.8, hy + (y - hy) * 0.8, depth) for x, y, _ in inner]
    for k in range(16):
        k2 = (k + 1) % 16
        mb.face([floor[k2], floor[k], inner[k], inner[k2]], [(0, 0), (1, 0), (1, 1), (0, 1)], G_HOLE)
    mb.up(floor, G_MUD, 0.5)
    mb.up([(hx + 0.1 + 0.45 * math.cos(a), hy - 0.05 + 0.38 * math.sin(a), depth + 0.07) for a in
           (2 * math.pi * k / 7 for k in range(7))], G_MUD, 0.5)
    for sx in (1, -1):
        town_side(mb, sx, skip={13} if sx > 0 else ())
    # cracks: zigzags out of the pothole and along the lane, plus one across the sidewalk
    for k in range(5):
        a = math.radians(R.uniform(0, 360))
        x, y = hx + 0.8 * math.cos(a), hy + 0.8 * math.sin(a)
        pts = [(x, y)]
        for _ in range(R.randint(3, 6)):
            a += math.radians(R.uniform(-45, 45))
            x, y = max(-3.9, min(3.9, x + 0.6 * math.cos(a))), max(-9.9, min(9.9, y + 0.6 * math.sin(a)))
            pts.append((x, y))
        mb.ribbon(pts, 0.05, 0.004, G_CRACK)
    pts = [(-1.8, 9.6)]
    while pts[-1][1] > -6:
        pts.append((pts[-1][0] + R.uniform(-0.35, 0.35), pts[-1][1] - R.uniform(0.6, 1.1)))
    mb.ribbon(pts, 0.06, 0.004, G_CRACK)
    for x0, y0 in ((4.4, 6.0), (-6.8, -2.0)):
        mb.ribbon([(x0, y0), (x0 + 0.6, y0 - 0.5), (x0 + 1.0, y0 - 0.3), (x0 + 1.7, y0 - 0.9), (x0 + 2.2, y0 - 0.8)], 0.05,
                  SIDE + 0.004, G_CRACK)
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white, yellow = straight_lines()
    paint(kit, root, p, white, yellow)
    sockets(kit, root, p, [("exit", (0, -HALF, 0), 0)])
    d = kit.empty(f"{p} dressing", root)
    asph = tm(kit, "road asphalt", lambda: tex_road(R), 0.15, 'REPEAT')
    tbox(kit, f"{p} heaved slab", (0, 0, 0), (1.6, 1.2, 0.16), asph, d, loc=(-2.1, 4.6, 0.06), rot=(9, -12, 23))
    for i in range(9):
        a = 2 * math.pi * i / 9 + R.uniform(-0.3, 0.3)
        r = R.uniform(1.0, 1.9)
        s = R.uniform(0.12, 0.32)
        tbox(kit, f"{p} rubble {i}", (0, 0, 0), (s, s * 0.8, 0.08), asph, d,
             loc=(hx + r * math.cos(a), hy + r * math.sin(a), 0.03), rot=(R.uniform(-15, 15), R.uniform(-15, 15), R.uniform(0, 180)))
    brick = solid(kit, "brick", "#c95a7a", shade="#9e3d5c")
    for i in range(6):
        tbox(kit, f"{p} brick {i}", (0, 0, 0), (0.22, 0.11, 0.07), brick, d,
             loc=(R.uniform(-3.2, -0.5), R.uniform(-8.5, -4.0), 0.035), rot=(0, R.uniform(-10, 10), R.uniform(0, 180)))
    tbox(kit, f"{p} loose curb", (0, 0, 0), (0.3, 1.0, 0.4), solid(kit, "curb white", WHITE, 0.35), d,
         loc=(3.2, -3.7, 0.16), rot=(8, 72, 18))
    tire = kit.empty(f"{p} tire", d, (-1.4, -6.6, 0.11), (90, 0, 20))
    pts = [(0.3 * math.cos(a), 0.3 * math.sin(a), 0) for a in (2 * math.pi * k / 10 for k in range(11))]
    tube(kit, f"{p} tire", pts, 0.1, solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050"), tire, sides=6, front=(0, 0, 1),
         caps=(False, False))
    place(kit, traffic_cone, d, f"{p} cone 0", (3.3, -0.5, 0.0), 10)
    place(kit, traffic_cone, d, f"{p} cone 1", (0.6, -3.4, 0.17), rot=(80, 0, 35))
    place(kit, barricade, d, f"{p} barricade", (2.0, 1.2, 0.0), 180)
    place(kit, street_lamp, d, f"{p} lamp", (-4.7, 6.0, SIDE), rot=(14, 0, 90))
    place(kit, trash_can, d, f"{p} trash can", (-5.4, -6.2, SIDE + 0.27), rot=(90, 0, 140))


# ---------------------------------------------------------------- textures: props
def tex_stop(rand):
    c = Canvas(64, 64, INK)
    ap = math.cos(math.radians(22.5))
    for y in range(64):
        for x in range(64):
            u, v = (x + 0.5) / 32 - 1, (y + 0.5) / 32 - 1
            dd = max(abs(u), abs(v), (abs(u) + abs(v)) / math.sqrt(2))
            if dd <= ap:
                c.set(x, y, WHITE if dd > ap * 0.84 else RED)
    text2(c, "STOP", 9, 39, WHITE, 3)
    for x, y in ((44, 46), (17, 20), (40, 18)):
        disc(c, x, y, 1, "#3a2a40")
        c.set(x + 1, y + 1, "#d9d4ff")
    return c


def tex_speed(rand):
    c = Canvas(24, 32, WHITE)
    c.rect(0, 0, 23, 0, INK); c.rect(0, 31, 23, 31, INK); c.rect(0, 0, 0, 31, INK); c.rect(23, 0, 23, 31, INK)
    text2(c, "SPEED", 2, 28, INK)
    text2(c, "LIMIT", 2, 22, INK)
    text2(c, "25", 5, 14, INK, 2)
    for x, y in ((18, 6), (4, 15)):
        c.set(x, y, "#3a2a40"); c.set(x + 1, y, "#9a94c8")
    return c


def tex_zombie_sign(rand):
    c = tex_sign()
    for k in range(3):
        for i in range(7):
            c.set(22 + k * 2 + i // 2, 9 - i, DRED)
    return c


def tex_chevron():
    c = Canvas(16, 16, YEL)
    for y in range(16):
        x0 = 4 + int(abs(y - 7.5) * 0.75)
        c.rect(x0, y, x0 + 3, y, INK)
    c.rect(0, 0, 15, 0, INK); c.rect(0, 15, 15, 15, INK)
    return c


def tex_can():
    c = Canvas(16, 16, "#b9b2e6")
    for y in (1, 2, 7, 8, 13, 14):
        c.rect(0, y, 15, y, "#8f86c8" if y % 2 else "#d4cff5")
    c.rect(11, 0, 11, 15, "#9d95d4")
    c.dots([(3, 5), (4, 5), (4, 4)], "#7a72b4")
    return c


def tex_barricade():
    c = Canvas(16, 8, WHITE)
    for y in range(8):
        for x in range(16):
            if ((x + y) // 4) % 2:
                c.set(x, y, ORNG)
    return c


def tex_cone():
    c = Canvas(4, 16, ORNG)
    c.rect(0, 6, 3, 8, WHITE)
    c.rect(0, 11, 3, 12, WHITE)
    c.rect(0, 0, 3, 0, "#d96a20")
    return c


def tex_chain():
    c = Canvas(8, 8, CUT)
    for i in range(8):
        c.set(i, i, "#d4cff5")
        c.set(i, 7 - i, "#b9b2e6")
    return c


def tex_sedan(rand):
    c = tex_car(rand)
    c.dots([(40, 20), (41, 21), (42, 21), (43, 20), (41, 19), (42, 19), (42, 18), (41, 18), (43, 22), (40, 22)], RED)
    c.dots([(44, 17), (45, 16), (46, 15)], DRED)
    return c


def tex_burnt(rand):
    """64x64: bottom half charred body panels, top half cab side with an empty window hole."""
    c = Canvas(64, 64, "#3b2b44")
    c.speckle(rand, ["#2a1f33", "#4a3854", "#231a2c"], 1200)
    for _ in range(14):
        disc(c, rand.randrange(64), rand.randrange(64), rand.choice((1, 2, 3)), rand.choice(("#a4512f", "#7e3f34")))
    for _ in range(6):
        disc(c, rand.randrange(64), rand.randrange(32), 2, "#b8395a")
    c.rect(5, 42, 58, 60, "#120b1c")
    c.rect(5, 42, 58, 42, "#5a3a4a")
    for _ in range(14):
        c.set(rand.randrange(64), rand.randrange(64), ORNG)
    return c


def tex_leaf(rand, base):
    c = Canvas(8, 8, base)
    c.speckle(rand, [hex_scale(base, 0.82), hex_scale(base, 1.12)], 14)
    return c


def tex_hay(rand):
    c = Canvas(16, 16, "#ffd86a")
    c.speckle(rand, ["#e0b84a", "#fff1b0", "#d9a83a"], 110)
    return c


def tex_hay_end(rand):
    c = Canvas(32, 32, "#f4cd5e")
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - 15.5, y - 15.5)
            a = math.atan2(y - 15.5, x - 15.5) / (2 * math.pi)
            if int(d / 2.2 + a) % 2 == 0:
                c.set(x, y, "#d9a83a")
    c.speckle(rand, ["#fff1b0", "#c99a3a"], 60)
    return c


def tex_pole(rand):
    c = Canvas(8, 32, "#8a5a5a")
    c.speckle(rand, ["#7a4a4c", "#9a6a66", "#6e4044"], 70)
    for x in (2, 5):
        for y in range(0, 32, 2):
            c.set(x, y, "#6e4044")
    c.rect(0, 6, 7, 7, YEL)
    return c


def tex_swirl_disc():
    c = Canvas(32, 32, WHITE)
    for y in range(32):
        for x in range(32):
            d = math.hypot(x - 15.5, y - 15.5)
            a = math.atan2(y - 15.5, x - 15.5) / (2 * math.pi)
            if int(d / 2.6 + a * 3) % 2 == 0:
                c.set(x, y, PINK)
    return c


# ---------------------------------------------------------------- props
def street_lamp(kit, root, p):
    pole = solid(kit, "lamp pole", "#5b5fc0", shade="#474aa0")
    tube(kit, f"{p} base", [(0, 0, 0), (0, 0, 0.4)], [0.17, 0.12], pole, root, sides=6)
    tube(kit, f"{p} pole", [(0, 0, 0.35), (0, 0, 3.9), (0, -0.3, 4.2), (0, -1.1, 4.25)], [0.08, 0.06, 0.05, 0.045], pole, root,
         sides=6, side=(1, 0, 0))
    tube(kit, f"{p} band", [(0, 0, 1.0), (0, 0, 1.25)], 0.09, solid(kit, "lamp band", PINK), root, sides=6)
    tbox(kit, f"{p} head", (0, -1.25, 4.2), (0.26, 0.55, 0.12), pole, root)
    tbox(kit, f"{p} glow", (0, -1.25, 4.135), (0.2, 0.45, 0.02), solid(kit, "lamp glow", "#fff1a0", 3.0), root)
    kit.empty(f"{p} socket light", root, (0, -1.25, 4.1))
    point_light(kit, root, f"{p} light", (0, -1.25, 3.9), "#ffe6a0", 450, 9.0, 0.4)


def sign_pole(kit, root, p, h, x=0.0):
    tube(kit, f"{p} pole", [(x, 0.05, 0), (x, 0.05, h)], 0.035, solid(kit, "sign pole", STEEL, shade="#a9a2e0"), root, sides=6)


def stop_sign(kit, root, p):
    sign_pole(kit, root, p, 2.1)
    mb = MB()
    plate(mb, (0, 0, 2.15), 0.42, 8, 0.03, 0, 1, math.radians(22.5))
    mb.obj(kit, f"{p} plate", [tm(kit, "stop sign", lambda: tex_stop(kit.rand)), solid(kit, "sign back", "#9a94c8")], root)


def speed_sign(kit, root, p):
    sign_pole(kit, root, p, 2.3)
    tbox(kit, f"{p} plate", (0, 0, 2.0), (0.6, 0.03, 0.8), tm(kit, "speed sign", lambda: tex_speed(kit.rand)), root,
         uv={'all': (0.1, 0.4, 0.12, 0.42), 'ny': (0, 0, 1, 1)})
    for z in (1.75, 2.25):
        tbox(kit, f"{p} bracket {z}", (0, 0.035, z), (0.12, 0.03, 0.05), solid(kit, "sign pole", STEEL, shade="#a9a2e0"), root)
    tube(kit, f"{p} cap", [(0, 0.05, 2.3), (0, 0.05, 2.36)], [0.045, 0.02], solid(kit, "sign pole", STEEL, shade="#a9a2e0"), root,
         sides=6)


def zombies_sign(kit, root, p):
    lean = kit.empty(f"{p} lean", root, (0, 0, 0), (3, -5, 4))
    for i, x in enumerate((-0.45, 0.45)):
        sign_pole(kit, lean, f"{p} {i}", 2.2, x)
    tbox(kit, f"{p} plate", (0, 0, 1.85), (1.3, 0.03, 0.98), tm(kit, "zombies sign", lambda: tex_zombie_sign(kit.rand)), lean,
         uv={'all': (0.05, 0.3, 0.07, 0.32), 'ny': (0, 0, 1, 1)})


def chevron_sign(kit, root, p):
    sign_pole(kit, root, p, 1.6)
    tbox(kit, f"{p} plate", (0, 0, 1.3), (0.45, 0.03, 0.6), tm(kit, "chevron", tex_chevron), root,
         uv={'all': (0.0, 0.3, 0.05, 0.35), 'ny': (0, 0, 1, 1)})


def mailbox(kit, root, p):
    wood = solid(kit, "post wood", "#9a6a56", shade="#7a4a4c")
    blue, red, white = solid(kit, "mailbox blue", BLUE), solid(kit, "mailbox flag", RED), solid(kit, "mailbox white", WHITE)
    tbox(kit, f"{p} post", (0, 0.08, 0.52), (0.1, 0.1, 1.05), wood, root)
    tbox(kit, f"{p} shelf", (0, 0.0, 1.06), (0.22, 0.52, 0.04), wood, root)
    prof = [(-0.13, 0), (0.13, 0)] + [(0.13 * math.cos(a), 0.12 + 0.13 * math.sin(a)) for a in
                                      (math.pi * k / 6 for k in range(7))]
    mb = MB()
    extrude_y(mb, prof, -0.24, 0.26, 0, (0, 0, 1.08))
    mb.obj(kit, f"{p} box", [blue], root)
    door = kit.empty(f"{p} door", root, (0, -0.24, 1.08))
    mb = MB()
    extrude_y(mb, [(x * 1.06, z * 1.04) for x, z in prof], -0.025, 0.0, 0)
    mb.obj(kit, f"{p} door", [white], door)
    flag = kit.empty(f"{p} flag", root, (0.14, 0.12, 1.14))
    tbox(kit, f"{p} flag arm", (0.0, 0, 0.16), (0.015, 0.025, 0.32), red, flag)
    tbox(kit, f"{p} flag plate", (0.0, -0.07, 0.27), (0.015, 0.14, 0.09), red, flag)


def fire_hydrant(kit, root, p):
    red, yel, white = solid(kit, "hydrant red", RED, 0.38, shade=DRED), solid(kit, "hydrant yellow", YEL), \
        solid(kit, "hydrant cap", WHITE)
    tube(kit, f"{p} flange", [(0, 0, 0), (0, 0, 0.07)], [0.17, 0.16], red, root, sides=8)
    tube(kit, f"{p} barrel", [(0, 0, 0.06), (0, 0, 0.5), (0, 0, 0.56)], [0.12, 0.115, 0.135], red, root, sides=8)
    tube(kit, f"{p} bonnet", [(0, 0, 0.55), (0, 0, 0.6), (0, 0, 0.7), (0, 0, 0.75)], [0.15, 0.14, 0.09, 0.035], yel, root, sides=8)
    tube(kit, f"{p} nut", [(0, 0, 0.74), (0, 0, 0.8)], 0.035, yel, root, sides=5)
    for sx in (1, -1):
        tube(kit, f"{p} nozzle {sx}", [(sx * 0.1, 0, 0.42), (sx * 0.19, 0, 0.42)], 0.045, red, root, sides=6, front=(0, 0, 1))
        tube(kit, f"{p} nozzle cap {sx}", [(sx * 0.19, 0, 0.42), (sx * 0.23, 0, 0.42)], 0.055, white, root, sides=6, front=(0, 0, 1))
    tube(kit, f"{p} pumper", [(0, -0.1, 0.34), (0, -0.2, 0.34)], 0.06, red, root, sides=6, side=(1, 0, 0))
    tube(kit, f"{p} pumper cap", [(0, -0.2, 0.34), (0, -0.25, 0.34)], 0.072, white, root, sides=6, side=(1, 0, 0))


def trash_can(kit, root, p):
    R = kit.rand
    can = tm(kit, "trash can", tex_can)
    steel = solid(kit, "can steel", "#b9b2e6", shade="#9d95d4")
    tube(kit, f"{p} body", [(0, 0, 0), (0, 0, 0.78)], [0.25, 0.28], can, root, sides=10)
    for sx in (1, -1):
        tbox(kit, f"{p} handle {sx}", (sx * 0.29, 0, 0.62), (0.04, 0.16, 0.05), steel, root)
    tube(kit, f"{p} cone", [(0.08, 0.02, 0.72), (0.12, 0.03, 0.95)], [0.01, 0.07], tm(kit, "waffle", tex_waffle), root, sides=6)
    lowball(kit, f"{p} paper", (-0.1, -0.05, 0.83), (0.09, 0.08, 0.07), solid(kit, "paper", WHITE), root, smooth=False)
    lowball(kit, f"{p} wrapper", (-0.02, 0.12, 0.81), (0.07, 0.06, 0.05), solid(kit, "wrapper", PINK), root, smooth=False)
    lid = kit.empty(f"{p} lid", root, (-0.06, 0.0, 0.84), (0, -14, 0))
    tube(kit, f"{p} lid", [(0, 0, 0), (0, 0, 0.04), (0, 0, 0.11)], [0.31, 0.3, 0.07], steel, lid, sides=10)
    tbox(kit, f"{p} lid handle", (0, 0, 0.14), (0.18, 0.03, 0.04), steel, lid)


def picket_fence(kit, root, p):
    """2 m segment along X with its post at x=-1 (the next segment supplies the post at x=+1)."""
    fw = solid(kit, "fence", WHITE, 0.35)
    tbox(kit, f"{p} post", (-1.0, 0.0, 0.55), (0.1, 0.1, 1.1), fw, root)
    tube(kit, f"{p} post cap", [(-1.0, 0, 1.1), (-1.0, 0, 1.18)], 0.075, fw, root, sides=4, bulge=(0, 0.06), smooth=False)
    for i in range(5):
        x = -0.8 + i * 0.4
        tube(kit, f"{p} picket {i}", [(x, 0, 0.02), (x, 0, 0.92)], [(0.055, 0.02)] * 2, fw, root, sides=4, side=(1, 0, 0),
             bulge=(0, 0.09), smooth=False)
    for z in (0.3, 0.7):
        tbox(kit, f"{p} rail {z}", (0.0, 0.035, z), (2.0, 0.035, 0.08), solid(kit, "fence rail", MINT, 0.35), root)


def chainlink_fence(kit, root, p):
    """2.5 m segment along X with its post at x=-1.25."""
    steel = solid(kit, "chain steel", "#c9c2f0", shade="#a9a2e0")
    tube(kit, f"{p} post", [(-1.25, 0, 0), (-1.25, 0, 1.95)], 0.045, steel, root, sides=6, bulge=(0, 0.03))
    tube(kit, f"{p} top rail", [(-1.25, 0, 1.82), (1.25, 0, 1.82)], 0.025, steel, root, sides=6, front=(0, 0, 1))
    tube(kit, f"{p} arm", [(-1.25, 0, 1.9), (-1.25, -0.28, 2.18)], 0.02, steel, root, sides=4, side=(1, 0, 0))
    for i, (y, z) in enumerate(((-0.1, 2.0), (-0.2, 2.1))):
        pts = [(-1.25 + 2.5 * k / 8, y + (0.012 if k % 2 else -0.012), z - 0.06 * math.sin(math.pi * k / 8)) for k in range(9)]
        tube(kit, f"{p} barbed {i}", pts, 0.012, solid(kit, "barbed", "#8f86c8"), root, sides=4, front=(0, 0, 1))
    mb = MB()
    t = 0.3
    mb.face([(-1.25, 0, 0.05), (1.25, 0, 0.05), (1.25, 0, 1.8), (-1.25, 0, 1.8)],
            [(0, 0.05 / t), (2.5 / t, 0.05 / t), (2.5 / t, 1.8 / t), (0, 1.8 / t)], 0)
    mb.obj(kit, f"{p} mesh", [cut_mat(kit, "chain link", tex_chain)], root)


def barricade(kit, root, p):
    wood = solid(kit, "barricade leg", WHITE, 0.3, shade="#d4cff5")
    for sx in (1, -1):
        for sy in (1, -1):
            tbox(kit, f"{p} leg {sx} {sy}", (sx * 0.66, sy * 0.15, 0.52), (0.07, 0.05, 1.1), wood, root, rot=(sy * 16, 0, 0))
    stripes = tm(kit, "barricade", tex_barricade, ext='REPEAT')
    for i, (z, h) in enumerate(((0.95, 0.24), (0.55, 0.18))):
        tbox(kit, f"{p} board {i}", (0, -0.06 if i == 0 else -0.16, z), (1.75, 0.04, h), stripes, root,
             uv={'all': (0, 0, 0.1, 0.1), 'ny': (0, 0, 4.4, h / 0.2), 'py': (0, 0, 4.4, h / 0.2)})
    tbox(kit, f"{p} lamp box", (0.7, -0.06, 1.12), (0.12, 0.08, 0.1), solid(kit, "car dark", INK, 0.1), root)
    tube(kit, f"{p} lamp lens", [(0.7, -0.06, 1.17), (0.7, -0.06, 1.27)], [0.075, 0.065], solid(kit, "blinker", "#ffb13d", 2.2), root,
         sides=6)
    kit.empty(f"{p} socket light", root, (0.7, -0.06, 1.24))


def traffic_cone(kit, root, p):
    tbox(kit, f"{p} base", (0, 0, 0.02), (0.42, 0.42, 0.04), solid(kit, "cone base", "#d96a20"), root)
    tube(kit, f"{p} lip", [(0, 0, 0.04), (0, 0, 0.07)], 0.19, solid(kit, "cone base", "#d96a20"), root, sides=10)
    tube(kit, f"{p} cone", [(0, 0, 0.06), (0, 0, 0.74)], [0.17, 0.03], tm(kit, "cone", tex_cone), root, sides=10, caps=(False, True))


def wrecked_sedan(kit, root, p):
    R = kit.rand
    paint_m = tm(kit, "sedan paint", lambda: tex_sedan(R))
    glass = tm(kit, "sedan glass", lambda: tex_car_glass(R))
    dark, chrome = solid(kit, "car dark", INK, 0.1), solid(kit, "chrome", STEEL, shade="#a9a2e0")
    tire, cap = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050"), solid(kit, "car cap", PINK)
    body = kit.empty(f"{p} body", root)
    tbox(kit, f"{p} hull", (0, 0, 0.63), (1.8, 4.3, 0.54), paint_m, body)
    tbox(kit, f"{p} cabin", (0, 0.25, 1.15), (1.62, 2.1, 0.5), glass, body, taper=(0.86, 0.7))
    tbox(kit, f"{p} engine", (0, -1.5, 0.94), (1.1, 0.9, 0.1), dark, body)
    hood = kit.empty(f"{p} hood", body, (0, -0.85, 0.91), (-34, 0, 5))
    tbox(kit, f"{p} hood", (0, -0.66, 0.02), (1.72, 1.32, 0.05), paint_m, hood)
    trunk = kit.empty(f"{p} trunk lid", body, (0, 1.35, 0.91))
    tbox(kit, f"{p} trunk lid", (0, 0.4, 0.02), (1.72, 0.8, 0.05), paint_m, trunk)
    for nm, sx, y0, ang in (("front L", -1, -0.75, 0), ("front R", 1, -0.75, 58), ("rear L", -1, 0.4, 0), ("rear R", 1, 0.4, 0)):
        door = kit.empty(f"{p} door {nm}", body, (sx * 0.92, y0, 0.37), (0, 0, -sx * ang))
        tbox(kit, f"{p} door {nm}", (0, 0.56, 0.26), (0.05, 1.12, 0.52), paint_m, door, uv={'all': (0.1, 0.3, 0.5, 0.9)})
    tbox(kit, f"{p} front bumper", (0, -2.2, 0.4), (1.86, 0.12, 0.16), chrome, body, rot=(0, 9, 0))
    tbox(kit, f"{p} rear bumper", (0, 2.2, 0.42), (1.86, 0.12, 0.16), chrome, body)
    for sx, m in ((1, solid(kit, "headlight", "#fff1a0", 1.2)), (-1, dark)):
        tbox(kit, f"{p} headlight {sx}", (sx * 0.6, -2.16, 0.74), (0.32, 0.04, 0.14), m, body)
        tbox(kit, f"{p} taillight {sx}", (sx * 0.65, 2.16, 0.74), (0.3, 0.04, 0.12), solid(kit, "taillight", RED, 0.6), body)
    for nm, x, y in (("FL", -0.9, -1.35), ("FR", 0.9, -1.35), ("RL", -0.9, 1.35)):
        wheel(kit, f"{p} wheel {nm}", body, (x, y, 0.32), 1 if x > 0 else -1, tire, chrome, cap).scale = (0.7, 0.7, 0.7)
    tbox(kit, f"{p} cinder block", (0.85, 1.35, 0.11), (0.24, 0.4, 0.22), solid(kit, "cinder", "#9a94c8", shade="#7a74a8"), body)
    tbox(kit, f"{p} axle stub", (0.9, 1.35, 0.3), (0.14, 0.14, 0.14), dark, body)
    loose = wheel(kit, f"{p} wheel RR", root, (1.8, 2.7, 0.105), 1, tire, chrome, cap)
    loose.scale = (0.7, 0.7, 0.7)
    loose.rotation_euler = (0, math.radians(90), math.radians(25))
    shard = solid(kit, "glass shard", "#c7d4ff", 0.6)
    for i in range(6):
        tbox(kit, f"{p} shard {i}", (0, 0, 0), (0.09, 0.06, 0.01), shard, root,
             loc=(R.uniform(1.1, 1.6), R.uniform(-1.2, 0.4), 0.005), rot=(0, 0, R.uniform(0, 180)))


def rim(kit, name, parent, loc, side):
    piv = kit.empty(name, parent, loc)
    steel = solid(kit, "burnt rim", "#5a4f70", shade="#463c5a")
    tube(kit, name + " rim", [(-0.12, 0, 0), (0.12, 0, 0)], 0.3, steel, piv, sides=10, front=(0, 0, 1))
    tube(kit, name + " hub", [(side * 0.11, 0, 0), (side * 0.16, 0, 0)], [0.12, 0.06], steel, piv, sides=6, front=(0, 0, 1))
    return piv


def burnt_pickup(kit, root, p):
    R = kit.rand
    burnt = tm(kit, "burnt", lambda: tex_burnt(R))
    low, cab_uv = {'all': (0, 0, 1, 0.5)}, {'all': (0, 0, 1, 0.5), 'px': (0, 0.5, 1, 1), 'nx': (0, 0.5, 1, 1), 'ny': (0, 0.5, 1, 1)}
    dark = solid(kit, "car dark", INK, 0.1)
    body = kit.empty(f"{p} body", root, (0, 0, 0), (0, 1.5, 0))
    tbox(kit, f"{p} chassis", (0, 0, 0.4), (1.6, 4.9, 0.16), dark, body)
    tbox(kit, f"{p} engine bay", (0, -1.85, 0.85), (1.9, 1.45, 0.7), burnt, body, uv=low)
    hood = kit.empty(f"{p} hood", body, (0, -1.12, 1.2), (-13, 0, -5))
    tbox(kit, f"{p} hood", (0, -0.74, 0.02), (1.94, 1.48, 0.05), burnt, hood, uv=low)
    tbox(kit, f"{p} cab", (0, -0.37, 1.15), (1.9, 1.5, 1.3), burnt, body, taper=(0.94, 0.8), uv=cab_uv)
    tbox(kit, f"{p} bed floor", (0, 1.57, 0.54), (1.9, 2.3, 0.08), burnt, body, uv=low)
    for sx in (1, -1):
        tbox(kit, f"{p} bed side {sx}", (sx * 0.915, 1.57, 0.83), (0.07, 2.3, 0.5), burnt, body, uv=low)
    tbox(kit, f"{p} bed front", (0, 0.42, 0.83), (1.9, 0.07, 0.5), burnt, body, uv=low)
    gate = kit.empty(f"{p} tailgate", body, (0, 2.72, 0.54), (-100, 0, 0))
    tbox(kit, f"{p} tailgate", (0, 0.03, 0.25), (1.9, 0.06, 0.5), burnt, gate, uv=low)
    for nm, sx, ang in (("L", -1, 0), ("R", 1, 38)):
        door = kit.empty(f"{p} door {nm}", body, (sx * 0.97, -1.1, 0.55), (0, 0, -sx * ang))
        tbox(kit, f"{p} door {nm}", (0, 0.55, 0.37), (0.05, 1.1, 0.74), burnt, door, uv=low)
    tbox(kit, f"{p} bumper", (0, -2.64, 0.5), (1.96, 0.14, 0.18), burnt, body, rot=(0, -14, 0), uv=low)
    for nm, x, y in (("FL", -0.85, -1.85), ("FR", 0.85, -1.85), ("RL", -0.85, 1.6), ("RR", 0.85, 1.6)):
        rim(kit, f"{p} wheel {nm}", body, (x, y, 0.3), 1 if x > 0 else -1)
    ember = solid(kit, "ember", ORNG, 2.4, shade=YEL)
    for i, (x, y, z) in enumerate(((0.3, -1.9, 1.24), (-0.4, -1.5, 1.23), (0.2, -0.2, 0.62), (-0.5, 1.2, 0.6), (0.4, 1.9, 0.6),
                                   (-0.2, -2.2, 1.24))):
        tbox(kit, f"{p} ember {i}", (0, 0, 0), (0.1, 0.07, 0.05), ember, body, loc=(x, y, z), rot=(0, 0, R.uniform(0, 90)))
    point_light(kit, body, f"{p} ember light", (0, -0.4, 1.0), "#ff8a3d", 60, 3.0, 0.3)
    puff = [solid(kit, "smoke " + c, c, 0.45) for c in ("#8a7fae", "#b3a6d9", "#6e6494")]
    for i in range(5):
        r = 0.22 + i * 0.1
        lowball(kit, f"{p} smoke {i}", (0.08 * math.sin(i * 1.7), -0.4 + 0.25 * i, 2.0 + i * 0.5), (r, r, r * 0.9),
                puff[i % 3], body, smooth=False)
    kit.empty(f"{p} socket smoke", body, (0, -0.4, 1.85))


LEAF = ("#2fae66", "#3fcf7a", "#26995a")


def round_tree(kit, root, p):
    R = kit.rand
    bark = solid(kit, "bark", "#7a4a5a", shade="#5e3646")
    tube(kit, f"{p} trunk", [(0, 0, -0.05), (0.05, 0, 1.3), (0.12, 0.05, 2.5)], [0.25, 0.17, 0.12], bark, root, sides=6)
    tube(kit, f"{p} branch", [(0.06, 0, 1.6), (0.6, 0.1, 2.5)], [0.09, 0.05], bark, root, sides=5)
    leaves = [tm(kit, "leaf " + c, lambda c=c: tex_leaf(R, c), 0.3) for c in LEAF]
    for i, (c, r) in enumerate((((0.1, 0, 3.4), (1.55, 1.45, 1.25)), ((1.0, 0.3, 2.9), (1.0, 1.0, 0.85)),
                                ((-0.8, 0.2, 3.0), (1.1, 1.0, 0.9)), ((0.2, -0.7, 2.8), (1.0, 0.9, 0.8)),
                                ((0.1, 0.4, 4.25), (0.95, 0.9, 0.7)))):
        lowball(kit, f"{p} canopy {i}", c, r, leaves[i % 3], root)
    pink = solid(kit, "blossom", "#ff8fc8", 0.5)
    for i in range(6):
        a = R.uniform(0, 2 * math.pi)
        lowball(kit, f"{p} blossom {i}", (1.45 * math.cos(a), 1.35 * math.sin(a), R.uniform(2.9, 3.9)), (0.13, 0.13, 0.11), pink,
                root, smooth=False)


def pine_tree(kit, root, p):
    bark = solid(kit, "bark", "#7a4a5a", shade="#5e3646")
    tube(kit, f"{p} trunk", [(0, 0, -0.05), (0, 0, 1.3)], [0.18, 0.14], bark, root, sides=6)
    mats = [solid(kit, "pine dark", "#1f9e7a", 0.3, shade="#178060"), solid(kit, "pine light", "#2bbf8f", 0.3, shade="#1f9e7a")]
    for i, (z0, z1, r) in enumerate(((0.9, 2.9, 1.65), (2.0, 3.8, 1.3), (3.0, 4.7, 0.98), (4.0, 5.8, 0.66))):
        tube(kit, f"{p} tier {i}", [(0, 0, z0), (0, 0, z0 + 0.22), (0, 0, z1)], [r * 0.82, r, 0.03], mats[i % 2], root, sides=7)


def bush(kit, root, p):
    R = kit.rand
    leaves = [tm(kit, "leaf " + c, lambda c=c: tex_leaf(R, c), 0.3) for c in LEAF]
    for i, (c, r) in enumerate((((0, 0, 0.45), (0.75, 0.7, 0.55)), ((0.55, 0.2, 0.35), (0.5, 0.5, 0.4)),
                                ((-0.55, 0.1, 0.35), (0.55, 0.5, 0.42)), ((0.1, -0.4, 0.3), (0.5, 0.45, 0.35)))):
        lowball(kit, f"{p} clump {i}", c, r, leaves[i % 3], root)
    for i in range(7):
        a = R.uniform(0, 2 * math.pi)
        tbox(kit, f"{p} flower {i}", (0, 0, 0), (0.09, 0.09, 0.05), solid(kit, "flower " + str(i % 3), (PINK, YEL, WHITE)[i % 3], 0.5),
             root, loc=(0.7 * math.cos(a), 0.55 * math.sin(a), R.uniform(0.45, 0.85)), rot=(0, 0, R.uniform(0, 90)))


def hay_bale(kit, root, p):
    R = kit.rand
    r, hx = 0.72, 0.6
    tube(kit, f"{p} roll", [(-hx, 0, r), (hx, 0, r)], r, tm(kit, "hay", lambda: tex_hay(R)), root, sides=12, front=(0, 0, 1),
         caps=(False, False))
    mb = MB()
    disc_face(mb, (hx, 0, r), r, 12, (0, 1, 0), (0, 0, 1), 0)
    disc_face(mb, (-hx, 0, r), r, 12, (0, -1, 0), (0, 0, 1), 0)
    mb.obj(kit, f"{p} ends", [tm(kit, "hay end", lambda: tex_hay_end(R))], root)
    for x in (-0.3, 0.3):
        tube(kit, f"{p} twine {x}", [(x - 0.025, 0, r), (x + 0.025, 0, r)], r + 0.012, solid(kit, "twine", PINK), root, sides=12,
             front=(0, 0, 1), caps=(False, False))


POLE_WIRES, POLE_Z = (-1.05, -0.4, 1.05), 8.86


def wire(kit, name, parent, x, sy, ext, span=10.0, sag=0.9):
    """Power line from an insulator to y = sy * ext, sagging so its lowest point is mid-span (y = +-span)."""
    pts = [(x, -0.08 + sy * ext * k / 6, POLE_Z - sag * (ext * k / 6 / span) ** 2) for k in range(7)]
    tube(kit, name, pts, 0.018, solid(kit, "wire", INK, 0.1), parent, sides=4, front=(0, 0, 1), caps=(False, False))


def power_pole(kit, root, p, stubs=True):
    R = kit.rand
    wood = tm(kit, "pole wood", lambda: tex_pole(R))
    tube(kit, f"{p} pole", [(0, 0, -0.05), (0, 0, 9.2)], [0.17, 0.12], wood, root, sides=6)
    arm = solid(kit, "crossarm", "#9a6a66", shade="#7a4a4c")
    tbox(kit, f"{p} crossarm", (0, -0.08, 8.7), (2.5, 0.12, 0.14), arm, root)
    for sx in (1, -1):
        tbox(kit, f"{p} brace {sx}", (sx * 0.35, -0.08, 8.45), (0.05, 0.05, 0.6), arm, root, rot=(0, sx * 50, 0))
    glass = solid(kit, "insulator", MINT, 0.5, shade="#22c79c")
    for i, x in enumerate(POLE_WIRES):
        tube(kit, f"{p} insulator {i}", [(x, -0.08, 8.77), (x, -0.08, 8.86), (x, -0.08, 8.9)], [0.07, 0.05, 0.03], glass, root, sides=6)
        kit.empty(f"{p} socket wire {i}", root, (x, -0.08, POLE_Z))
    steel = solid(kit, "transformer", STEEL, shade="#a9a2e0")
    tube(kit, f"{p} transformer", [(0, 0.38, 6.9), (0, 0.38, 7.75)], 0.27, steel, root, sides=8)
    tube(kit, f"{p} transformer lid", [(0, 0.38, 7.75), (0, 0.38, 7.85)], [0.29, 0.2], steel, root, sides=8)
    tube(kit, f"{p} bushing", [(0.12, 0.38, 7.85), (0.12, 0.38, 8.05)], 0.03, glass, root, sides=5)
    tube(kit, f"{p} drop", [(0.12, 0.38, 8.05), (0.6, 0.2, 8.5), (1.05, -0.08, 8.86)], 0.012, solid(kit, "wire", INK, 0.1), root,
         sides=4, front=(0, 0, 1), caps=(False, False))
    tbox(kit, f"{p} bracket", (0, 0.2, 7.3), (0.12, 0.2, 0.3), steel, root)
    for i in range(7):
        sx = 1 if i % 2 else -1
        tbox(kit, f"{p} step {i}", (sx * 0.2, 0, 2.6 + i * 0.55), (0.26, 0.035, 0.035), steel, root)
    tbox(kit, f"{p} tag", (0, -0.15, 1.9), (0.18, 0.02, 0.24), solid(kit, "pole tag", YEL), root)
    if stubs:
        for i, x in enumerate(POLE_WIRES):
            for sy in (1, -1):
                wire(kit, f"{p} wire stub {i} {sy}", root, x, sy, 2.4)


# ---------------------------------------------------------------- buildings: shared bits
def bricks(c, rand, x0, y0, x1, y1, base, mortar, hi, bw=6, bh=3):
    c.rect(x0, y0, x1, y1, base)
    for y in range(y0, y1 + 1):
        row = (y - y0) // bh
        if (y - y0) % bh == bh - 1:
            c.rect(x0, y, x1, y, mortar)
        else:
            for x in range(x0 + (row % 2) * (bw // 2), x1 + 1, bw):
                c.set(x, y, mortar)
    for _ in range((x1 - x0) * (y1 - y0) // 12):
        c.set(rand.randint(x0, x1), rand.randint(y0, y1), hi)


def window_px(c, x0, y0, w, h, lit):
    c.rect(x0, y0, x0 + w - 1, y0 + h - 1, WHITE)
    c.rect(x0 + 2, y0 + 2, x0 + w - 3, y0 + h - 3, "#ffd36b" if lit else GLASS)
    if lit:
        for r in range(h - 6):
            ww = max(0, 4 - r // 3)
            c.rect(x0 + 2, y0 + h - 3 - r, x0 + 2 + ww, y0 + h - 3 - r, PINK)
            c.rect(x0 + w - 3 - ww, y0 + h - 3 - r, x0 + w - 3, y0 + h - 3 - r, PINK)
    else:
        for i in range(4):
            c.set(x0 + 4 + i, y0 + h - 6 - i, "#6f8cff")
    c.rect(x0 + w // 2, y0 + 2, x0 + w // 2, y0 + h - 3, WHITE)
    c.rect(x0 + 2, y0 + h // 2, x0 + w - 3, y0 + h // 2, WHITE)


def transpose(c):
    t = Canvas(c.h, c.w, WHITE)
    for y in range(c.h):
        for x in range(c.w):
            t.p[x * t.w + y] = c.p[y * c.w + x]
    return t


def tex_shingles(rand, base, dark):
    """Shingle rows run along U (transposed), so on a tbox 'pz' face they run along the tbox's local Y (the ridge)."""
    c = Canvas(32, 32, base)
    for y in range(0, 32, 4):
        c.rect(0, y, 31, y, dark)
        for x in range((y // 4 % 2) * 3, 32, 6):
            c.rect(x, y, x, y + 3, dark)
    c.speckle(rand, [hex_scale(base, 1.12), hex_scale(base, 0.9)], 60)
    return transpose(c)


# ---------------------------------------------------------------- house (front faces +X)
SIDING, SIDING_D = "#9ff0d8", "#6fd2b8"
HX0, HX1, HY, HF, HT, HRX, HRZ = -2.2, 3.8, 4.0, 0.3, 3.3, 0.8, 5.4


def tex_house(rand):
    """128x128 atlas: rows 0-47 front (8 x 3 m), rows 48-95 side (x 0-95, 6 x 3 m) + plain siding (x 96-127),
    rows 96-127 chimney brick (x 0-31)."""
    c = Canvas(128, 128, SIDING)
    for y in range(0, 96, 3):
        c.rect(0, y, 127, y, SIDING_D)
    c.speckle(rand, ["#b5f6e4", "#8ae6cc"], 220, 0, 95)
    for x0, x1, y0, y1 in ((0, 1, 0, 47), (126, 127, 0, 47), (0, 1, 48, 95), (94, 95, 48, 95)):
        c.rect(x0, y0, x1, y1, WHITE)
    c.rect(0, 0, 127, 1, "#5fbfa5")
    c.rect(0, 48, 95, 49, "#5fbfa5")
    window_px(c, 14, 16, 20, 23, True)
    window_px(c, 94, 16, 20, 23, False)
    c.rect(54, 0, 73, 37, WHITE)
    c.rect(56, 0, 71, 34, INK)
    window_px(c, 38, 64, 20, 23, False)
    disc(c, 111, 78, 5, WHITE)
    disc(c, 111, 78, 3, GLASS)
    bricks(c, rand, 0, 96, 31, 127, "#c95a7a", "#9e3d5c", "#d9708e")
    return c


def tex_house_door():
    c = Canvas(16, 32, PINK)
    c.rect(0, 0, 15, 0, "#d93a85"); c.rect(0, 31, 15, 31, "#d93a85")
    c.rect(3, 4, 12, 13, "#e8458f"); c.rect(3, 17, 12, 22, "#e8458f")
    c.rect(4, 24, 11, 29, GLASS); c.rect(5, 28, 6, 28, "#6f8cff")
    c.rect(12, 15, 13, 16, YEL)
    return c


def roof_plane(kit, name, parent, x_eave, z_eave, x_ridge, z_ridge, width, mat, th=0.12, tile=1.6):
    """Slab whose underside runs from the eave line to the ridge line (both along Y)."""
    dx, dz = x_ridge - x_eave, z_ridge - z_eave
    L = math.hypot(dx, dz)
    a = math.degrees(math.atan2(dz, abs(dx)))
    sgn = 1 if dx > 0 else -1
    n = Vector((-sgn * dz / L * 1, 0, abs(dx) / L))
    c = Vector(((x_eave + x_ridge) / 2, 0, (z_eave + z_ridge) / 2)) + n * th / 2
    return tbox(kit, name, tuple(c), (L, width, th), mat, parent, rot=(0, -sgn * a, 0),
                uv={'all': (0, 0, 0.2, 0.2), 'pz': (0, 0, L / tile, width / tile)})


def house(kit, root, p):
    root = kit.empty(f"{p} body", root, (0, 0, 0), (0, 0, 180))   # modeled facing -X, turned to face +X
    R = kit.rand
    atlas = tm(kit, "house", lambda: tex_house(R))
    shing = tm(kit, "house shingles", lambda: tex_shingles(R, "#5b6cff", "#3d47c8"), ext='REPEAT')
    white, blue, pink = solid(kit, "trim", WHITE, 0.35), solid(kit, "shutter", BLUE), solid(kit, "flower box", PINK)
    found = solid(kit, "foundation", "#9a8fc8", shade="#857ab5")
    deck = solid(kit, "porch deck", "#e6e0ff", shade="#cfc6f0")
    side_uv = (0, 48 / 128, 96 / 128, 96 / 128)
    tbox(kit, f"{p} foundation", ((HX0 + HX1) / 2, 0, 0.05), (HX1 - HX0 + 0.1, 2 * HY + 0.1, 0.5), found, root)
    tbox(kit, f"{p} walls", ((HX0 + HX1) / 2, 0, HF + 1.5), (HX1 - HX0, 2 * HY, 3.0), atlas, root,
         uv={'all': (0.9, 0.5, 0.95, 0.55), 'nx': (0, 0, 1, 48 / 128), 'px': side_uv, 'ny': side_uv, 'py': side_uv})
    mb = MB()
    u = lambda x, z: ((96 + (x - HX0) / (HX1 - HX0) * 31) / 128, (48 + (z - HT) / (HRZ - HT) * 47) / 128)
    for sy in (1, -1):
        tri = [(HX1, sy * HY, HT), (HX0, sy * HY, HT), (HRX, sy * HY, HRZ)]
        tri = tri if sy > 0 else [tri[1], tri[0], tri[2]]
        mb.face(tri, [u(x, z) for x, _, z in tri], 0)
    mb.obj(kit, f"{p} gables", [atlas], root)
    k = (HRZ - HT) / (HRX - HX0)
    for nm, xe in (("front", HX0 - 0.45), ("back", HX1 + 0.45)):
        roof_plane(kit, f"{p} roof {nm}", root, xe, HT - 0.45 * k, HRX, HRZ, 2 * HY + 0.8, shing)
        tbox(kit, f"{p} gutter {nm}", (xe, 0, HT - 0.45 * k - 0.02), (0.12, 2 * HY + 0.8, 0.1), white, root)
    tbox(kit, f"{p} ridge", (HRX, 0, HRZ + 0.1), (0.3, 2 * HY + 0.9, 0.12), solid(kit, "ridge", "#3d47c8"), root)
    tbox(kit, f"{p} chimney", (2.6, 2.6, 4.9), (0.7, 0.7, 2.6), atlas, root, uv={'all': (0, 0.75, 0.25, 1.0)})
    tbox(kit, f"{p} chimney cap", (2.6, 2.6, 6.24), (0.86, 0.86, 0.1), white, root)
    # porch
    px = HX0 - 0.75
    tbox(kit, f"{p} porch", (px, 0, 0.15), (1.5, 6.6, 0.3), deck, root)
    tbox(kit, f"{p} step", (HX0 - 1.7, 0, 0.1), (0.4, 1.6, 0.2), deck, root)
    for i, y in enumerate((-3.2, -0.9, 0.9, 3.2)):
        tbox(kit, f"{p} post {i}", (HX0 - 1.4, y, 1.5), (0.14, 0.14, 2.4), white, root)
    roof_plane(kit, f"{p} porch roof", root, HX0 - 1.7, 2.68, HX0, 3.0, 6.9, shing, th=0.1)
    for sy in (1, -1):
        ys = [sy * (0.9 + 2.3 * k / 6) for k in range(7)]
        tbox(kit, f"{p} rail top {sy}", (HX0 - 1.4, sy * 2.05, 1.2), (0.08, 2.3, 0.08), white, root)
        tbox(kit, f"{p} rail low {sy}", (HX0 - 1.4, sy * 2.05, 0.42), (0.06, 2.3, 0.06), white, root)
        for i, y in enumerate(ys[1:-1]):
            tbox(kit, f"{p} baluster {sy} {i}", (HX0 - 1.4, y, 0.8), (0.05, 0.05, 0.78), white, root)
    door = kit.empty(f"{p} door", root, (HX0 - 0.035, -0.5, HF))
    tbox(kit, f"{p} door", (0, 0.5, 1.08), (0.06, 1.0, 2.16), tm(kit, "house door", tex_house_door), door,
         uv={'all': (0.1, 0.1, 0.15, 0.15), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})
    kit.empty(f"{p} socket door", root, (HX0 - 1.2, 0, HF))
    tbox(kit, f"{p} porch lamp", (HX0 - 0.06, 0.85, 2.3), (0.08, 0.14, 0.2), solid(kit, "porch lamp", "#fff1a0", 1.6), root)
    # windows: shutters, sills, flower boxes
    for i, yw in enumerate((2.53, -2.47)):
        for s in (1, -1):
            tbox(kit, f"{p} shutter {i} {s}", (HX0 - 0.03, yw + s * 0.88, HF + 1.72), (0.05, 0.42, 1.45), blue, root)
        tbox(kit, f"{p} sill {i}", (HX0 - 0.08, yw, HF + 0.98), (0.16, 1.45, 0.07), white, root)
        tbox(kit, f"{p} flower box {i}", (HX0 - 0.16, yw, HF + 0.84), (0.24, 1.2, 0.2), pink, root)
        for j in range(4):
            tbox(kit, f"{p} flower {i} {j}", (HX0 - 0.16, yw - 0.45 + j * 0.3, HF + 0.98), (0.14, 0.14, 0.1),
                 solid(kit, "flower " + str(j % 2), (YEL, WHITE)[j % 2], 0.5), root, rot=(0, 0, 45))
    for i, yw in enumerate((2.53, -2.47)):
        for j, (dy, dz, sy_, sz) in enumerate(((0, 0.98 + 1.48, 1.45, 0.08), (0.66, 1.72, 0.08, 1.5), (-0.66, 1.72, 0.08, 1.5))):
            tbox(kit, f"{p} window trim {i} {j}", (HX0 - 0.04, yw + dy, HF + dz), (0.06, sy_, sz), white, root)
    for j, (dy, dz, sy_, sz) in enumerate(((0, 2.26, 1.3, 0.12), (0.6, 1.1, 0.1, 2.25), (-0.6, 1.1, 0.1, 2.25))):
        tbox(kit, f"{p} door trim {j}", (HX0 - 0.04, dy, HF + dz), (0.06, sy_, sz), white, root)
    for s in (1, -1):
        tbox(kit, f"{p} back shutter {s}", (HX1 + 0.03, s * 1.15, HF + 1.72), (0.05, 0.42, 1.45), blue, root)
    tbox(kit, f"{p} back sill", (HX1 + 0.08, 0, HF + 0.98), (0.16, 1.9, 0.07), white, root)
    dx = HX0 + 0.9
    dz = HT - 0.45 * k + (dx - (HX0 - 0.45)) * k
    tbox(kit, f"{p} dormer", (dx + 0.4, 0, dz + 0.45), (1.4, 1.5, 1.3), atlas, root,
         uv={'all': (0.76, 0.4, 0.99, 0.74), 'nx': (38 / 128, 64 / 128, 58 / 128, 87 / 128)})
    for s in (1, -1):
        tbox(kit, f"{p} dormer roof {s}", (dx + 0.35, s * 0.4, dz + 1.33), (1.75, 0.98, 0.08), shing, root, rot=(-s * 32, 0, 0),
             uv={'all': (0, 0, 1, 0.6)})
    for sy in (1, -1):
        for s in (1, -1):
            tbox(kit, f"{p} side shutter {sy} {s}", (HRX + s * 0.88, sy * (HY + 0.03), HF + 1.72), (0.42, 0.05, 1.45), blue, root)
        tbox(kit, f"{p} side sill {sy}", (HRX, sy * (HY + 0.08), HF + 0.98), (1.45, 0.16, 0.07), white, root)


# ---------------------------------------------------------------- candy shop (front faces +X)
PLASTER, PLASTER_D = "#ffc2dc", "#f2a6c8"
SX0, SX1, SY, SF, SH = -3.0, 3.5, 4.8, 0.2, 3.8


def tex_shop(rand):
    """128x128 atlas: rows 0-50 front (9.6 x 3.8 m), rows 52-102 side (x 0-86, 6.5 m) and back (x 88-127)."""
    c = Canvas(128, 128, PLASTER)
    c.speckle(rand, [PLASTER_D, "#ffd6e8"], 400)
    bricks(c, rand, 0, 0, 127, 8, "#c95a7a", "#9e3d5c", "#d9708e")
    jar_cols = (PINK, MINT, YEL, BLUE, ORNG, PURP, "#ff8fc8", WHITE)
    for x0, x1 in ((5, 52), (75, 122)):
        c.rect(x0, 9, x1, 35, MINT)
        c.rect(x0 + 1, 10, x1 - 1, 34, "#3a3f8f")
        for yb in (10, 18, 26):
            c.rect(x0 + 1, yb, x1 - 1, yb, WHITE)
            for j, x in enumerate(range(x0 + 3, x1 - 4, 6)):
                col = jar_cols[(x // 6 + yb) % len(jar_cols)]
                if (j + yb) % 4 == 3:
                    disc(c, x + 2, yb + 5, 2, col)
                    c.rect(x + 2, yb + 1, x + 2, yb + 2, WHITE)
                else:
                    c.rect(x, yb + 1, x + 4, yb + 6, "#c7d4ff")
                    c.rect(x + 1, yb + 1, x + 3, yb + 4, col)
                    c.rect(x, yb + 7, x + 4, yb + 7, PINK)
        for i in range(4):
            c.set(x0 + 6 + i, 32 - i, "#8fa4ff")
    c.rect(56, 0, 71, 31, MINT)
    c.rect(57, 0, 70, 29, INK)
    c.rect(0, 37, 127, 38, WHITE)
    # side: mural with a big cone and a little window; back: plain
    bricks(c, rand, 0, 52, 86, 58, "#c95a7a", "#9e3d5c", "#d9708e")
    cone_icon(c, 22, 62, 18, MINT)
    text2(c, "SCOOP", 44, 92, PINK, 2, shadow=BLUE)
    window_px(c, 52, 62, 22, 20, False)
    bricks(c, rand, 88, 52, 127, 58, "#c95a7a", "#9e3d5c", "#d9708e")
    return c


def tex_shop_sign(rand):
    c = Canvas(64, 24, WHITE)
    for x in range(64):
        col = PINK if (x // 3) % 2 else MINT
        for y in (0, 1, 22, 23):
            c.set(x, y, col)
    for y in range(24):
        for x in (0, 1, 62, 63):
            c.set(x, y, PINK if (y // 3) % 2 else MINT)
    text2(c, "CANDY", 4, 18, BLUE, 3)
    text2(c, "CANDY", 3, 19, PINK, 3)
    for _ in range(18):
        x, y = rand.randrange(3, 61), rand.choice((2, 3, 20, 21))
        c.set(x, y, rand.choice((YEL, BLUE, PURP)))
    return c


def tex_shop_door():
    c = Canvas(16, 32, MINT)
    c.rect(2, 2, 13, 29, "#3a3f8f")
    c.rect(2, 14, 13, 14, MINT)
    c.rect(1, 17, 14, 23, INK)
    text2(c, "OPEN", 0, 22, PINK)
    c.rect(12, 12, 13, 13, YEL)
    for i in range(4):
        c.set(4 + i, 27 - i, "#8fa4ff")
    return c


def tex_awning_rows():
    c = Canvas(8, 8, PINK)
    c.rect(0, 4, 7, 7, WHITE)
    return c


def tex_valance():
    c = Canvas(16, 8, CUT)
    for x in range(16):
        cx, col = (3.5, PINK) if x < 8 else (11.5, WHITE)
        for y in range(8):
            if y >= 4 or (x - cx) ** 2 + (y - 4.5) ** 2 <= 4.4 ** 2:
                c.set(x, y, col)
    return c


def tex_gumballs(rand):
    c = Canvas(16, 8, "#d8e2ff")
    for _ in range(26):
        c.set(rand.randrange(16), rand.randrange(1, 7), rand.choice((PINK, MINT, YEL, BLUE, RED, PURP)))
    return c


def tex_board(rand):
    c = Canvas(16, 24, "#2a2140")
    c.rect(0, 0, 15, 0, CHOC); c.rect(0, 23, 15, 23, CHOC); c.rect(0, 0, 0, 23, CHOC); c.rect(15, 0, 15, 23, CHOC)
    text2(c, "SALE", 1, 21, WHITE)
    cone_icon(c, 8, 3, 8, PINK)
    return c


def candy_shop(kit, root, p):
    root = kit.empty(f"{p} body", root, (0, 0, 0), (0, 0, 180))   # modeled facing -X, turned to face +X
    R = kit.rand
    atlas = tm(kit, "candy shop", lambda: tex_shop(R))
    pink, white, mint, yel = solid(kit, "shop pink", PINK), solid(kit, "trim", WHITE, 0.35), solid(kit, "shop mint", MINT), \
        solid(kit, "shop yellow", YEL)
    plaster = solid(kit, "parapet", "#ffb3d4", shade=PLASTER_D)
    cx = (SX0 + SX1) / 2
    tbox(kit, f"{p} foundation", (cx, 0, 0.05), (SX1 - SX0 + 0.2, 2 * SY + 0.2, 0.3), solid(kit, "foundation", "#9a8fc8"), root)
    tbox(kit, f"{p} walls", (cx, 0, SF + SH / 2), (SX1 - SX0, 2 * SY, SH), atlas, root,
         uv={'all': (0.9, 0.9, 0.95, 0.95), 'nx': (0, 0, 1, 51 / 128), 'ny': (0, 52 / 128, 87 / 128, 103 / 128),
             'py': (0, 52 / 128, 87 / 128, 103 / 128), 'px': (88 / 128, 52 / 128, 1, 103 / 128)})
    top = SF + SH
    tbox(kit, f"{p} roof", (cx, 0, top + 0.05), (SX1 - SX0 + 0.2, 2 * SY + 0.2, 0.1), solid(kit, "tar roof", "#6a5fa0"), root)
    tbox(kit, f"{p} parapet front", (SX0, 0, top + 0.3), (0.25, 2 * SY + 0.2, 0.6), plaster, root)
    for sy in (1, -1):
        tbox(kit, f"{p} parapet side {sy}", (cx, sy * SY, top + 0.2), (SX1 - SX0 + 0.2, 0.2, 0.4), plaster, root)
    tbox(kit, f"{p} sign", (SX0 - 0.16, 0, top + 0.85), (0.14, 6.4, 1.7), tm(kit, "shop sign", lambda: tex_shop_sign(R)), root,
         uv={'all': (0.3, 0.4, 0.32, 0.42), 'nx': (0, 0, 1, 1)})
    for i, (y, col, r) in enumerate(((-2.4, PINK, 0.3), (0.0, MINT, 0.24), (2.4, YEL, 0.28))):
        lowball(kit, f"{p} gumdrop {i}", (SX0 - 0.16, y, top + 1.75 + r * 0.6), (r, r, r * 0.9), solid(kit, "gumdrop " + col, col, 0.45),
                root)
    lolly = kit.empty(f"{p} lollipop", root, (-1.4, -3.4, top))
    tube(kit, f"{p} lollipop stick", [(0, 0, 0), (0, 0, 2.5)], 0.07, white, lolly, sides=6)
    mb = MB()
    plate(mb, (0, 0, 0), 0.85, 12, 0.16, 0, 1)
    mb.obj(kit, f"{p} lollipop candy", [tm(kit, "lolly swirl", tex_swirl_disc), pink], lolly, (0, 0, 3.15), (0, 0, -90))
    tbox(kit, f"{p} ac unit", (2.0, 2.2, top + 0.45), (1.2, 0.9, 0.7), solid(kit, "ac", STEEL, shade="#a9a2e0"), root)
    tbox(kit, f"{p} ac fan", (2.0, 2.2, top + 0.81), (0.7, 0.7, 0.03), solid(kit, "car dark", INK, 0.1), root)
    # awning with a scalloped valance and string lights
    tbox(kit, f"{p} awning", (SX0 - 0.5, 0, 3.025), (1.14, 2 * SY, 0.05), tm(kit, "awning rows", tex_awning_rows, ext='REPEAT'),
         root, rot=(0, -28.8, 0), uv={'all': (0, 0, 1, 16), 'pz': (0, 0, 1, 16)})
    tbox(kit, f"{p} valance", (SX0 - 1.0, 0, 2.62), (0.02, 2 * SY, 0.26), cut_mat(kit, "valance", tex_valance), root,
         uv={'all': (0, 0, 16, 1)})
    for i, y in enumerate((-4.4, 0.0, 4.4)):
        tube(kit, f"{p} awning arm {i}", [(SX0, y, 2.3), (SX0 - 0.95, y, 2.74)], 0.025, white, root, sides=4, side=(0, 1, 0))
    for i in range(12):
        y = -SY + 0.4 + i * (2 * SY - 0.8) / 11
        col = (PINK, YEL, MINT, BLUE)[i % 4]
        tbox(kit, f"{p} bulb {i}", (SX0 - 1.0, y, 2.44), (0.07, 0.07, 0.09), solid(kit, "bulb " + col, col, 1.8), root)
    door = kit.empty(f"{p} door", root, (SX0 - 0.035, -0.53, SF))
    tbox(kit, f"{p} door", (0, 0.53, 1.1), (0.06, 1.06, 2.2), tm(kit, "shop door", tex_shop_door), door,
         uv={'all': (0, 0.5, 0.1, 0.55), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})
    kit.empty(f"{p} socket door", root, (SX0 - 0.9, 0, 0))
    for i, yw in enumerate((2.66, -2.59)):
        tbox(kit, f"{p} sill {i}", (SX0 - 0.08, yw, SF + 0.64), (0.18, 3.6, 0.08), white, root)
        tbox(kit, f"{p} planter {i}", (SX0 - 0.25, yw, 0.18), (0.4, 1.6, 0.36), mint, root)
        for j in range(4):
            lowball(kit, f"{p} planter flower {i} {j}", (SX0 - 0.25, yw - 0.6 + j * 0.4, 0.42), (0.17, 0.17, 0.13),
                    solid(kit, "flower " + str(j % 3), (PINK, YEL, WHITE)[j % 3], 0.5), root, smooth=False)
    gm = kit.empty(f"{p} gumball machine", root, (SX0 - 0.5, 1.15, 0))
    tube(kit, f"{p} gumball stand", [(0, 0, 0), (0, 0, 0.05), (0, 0, 0.75)], [0.2, 0.09, 0.07], solid(kit, "gumball red", RED), gm,
         sides=8)
    tbox(kit, f"{p} gumball box", (0, 0, 0.85), (0.3, 0.3, 0.22), solid(kit, "gumball red", RED), gm)
    tbox(kit, f"{p} gumball coin", (0, -0.155, 0.85), (0.1, 0.02, 0.1), solid(kit, "chrome", STEEL), gm)
    tube(kit, f"{p} gumball globe", [(0, 0, 0.96), (0, 0, 1.1), (0, 0, 1.3), (0, 0, 1.42)], [0.17, 0.25, 0.22, 0.1],
         tm(kit, "gumballs", lambda: tex_gumballs(R)), gm, sides=8)
    tube(kit, f"{p} gumball cap", [(0, 0, 1.41), (0, 0, 1.48)], [0.12, 0.05], solid(kit, "gumball red", RED), gm, sides=8)
    board = kit.empty(f"{p} sandwich board", root, (SX0 - 1.55, -2.6, 0), (0, 0, 10))
    t_board = tm(kit, "sale board", lambda: tex_board(R))
    for s in (1, -1):
        tbox(kit, f"{p} board {s}", (s * 0.13, 0, 0.45), (0.03, 0.6, 0.9), t_board, board, rot=(0, -s * 13, 0),
             uv={'all': (0, 0, 0.05, 0.05), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})


# ---------------------------------------------------------------- boarded-up building (front faces +X)
BRICK, MORTAR, BRICK_HI = "#c95a7a", "#9e3d5c", "#d9708e"
BX0, BX1, BY, BF, BH = -3.0, 3.0, 4.5, 0.1, 6.4
GAPE = "#140c22"


def front_px(px, row):
    """Front texture (128 x 96) texel -> (y, z) on the front wall."""
    return BY - px * (2 * BY / 128), BF + row * (BH / 96)


def tex_boarded_front(rand):
    c = Canvas(128, 96, BRICK)
    bricks(c, rand, 0, 0, 127, 95, BRICK, MORTAR, BRICK_HI)
    for x0, y0, x1, y1 in ((8, 10, 58, 38), (102, 12, 120, 36), (14, 56, 34, 82), (54, 56, 74, 82), (94, 56, 114, 82)):
        c.rect(x0 - 1, y0 - 2, x1 + 1, y0 - 1, "#e6c7d8")
        c.rect(x0 - 1, y1 + 1, x1 + 1, y1 + 2, "#e6c7d8")
        c.rect(x0, y0, x1, y1, GAPE)
        for i in range(4):
            c.rect(x0, y1 - i, x0 + 3 - i, y1 - i, "#8fa4ff")
            c.rect(x1 - 3 + i, y0 + i, x1, y0 + i, "#6f8cff")
    c.dots([(62, 72), (66, 72)], ZG)
    c.dots([(62, 71), (66, 71)], "#4fd68a")
    c.rect(73, 0, 91, 34, "#e6c7d8")
    c.rect(74, 0, 90, 32, GAPE)
    c.rect(0, 40, 127, 41, "#7a2f4c")
    text2(c, "KEEP OUT", 33, 53, ZG, 2)
    for i in range(9):
        c.set(98 + i, 44 + i, RED); c.set(106 - i, 44 + i, RED)
    c.speckle(rand, ["#3a2a40", "#8a4a64"], 90)
    return c


def tex_boarded_side(rand):
    c = Canvas(96, 96, BRICK)
    bricks(c, rand, 0, 0, 95, 95, BRICK, MORTAR, BRICK_HI)
    for x0, y0, x1, y1 in ((16, 14, 34, 36), (60, 14, 78, 36), (16, 56, 34, 78), (60, 56, 78, 78)):
        c.rect(x0 - 1, y1 + 1, x1 + 1, y1 + 2, "#e6c7d8")
        c.rect(x0, y0, x1, y1, GAPE)
    c.rect(36, 82, 58, 93, "#e9a9c0")
    text2(c, "ICE", 38, 92, "#fff0f6")
    text2(c, "COLD", 39, 86, "#fff0f6")
    c.speckle(rand, ["#3a2a40", "#8a4a64"], 60)
    return c


def tex_plank(rand):
    c = Canvas(16, 4, "#c98a52")
    c.speckle(rand, ["#b07440", "#dca06a"], 16)
    c.rect(0, 0, 15, 0, "#8a5226")
    c.dots([(1, 2), (14, 2)], INK)
    return c


def tex_hardware():
    c = Canvas(40, 10, "#f2e3c8")
    c.rect(0, 0, 39, 0, CHOC); c.rect(0, 9, 39, 9, CHOC)
    text2(c, "HARDWARE", 4, 7, CHOC)
    c.dots([(10, 2), (11, 3), (30, 6), (31, 6)], "#b8a890")
    return c


def boards(kit, root, p, yc, zc, w, h, n, wood, x=BX0 - 0.04):
    R = kit.rand
    for i in range(n):
        z = zc - h / 2 + h * (i + 0.5) / n
        tbox(kit, f"{p} {i}", (0, 0, 0), (0.05, w + 0.35, 0.2), wood, root, loc=(x - 0.01 * i, yc + R.uniform(-0.08, 0.08), z),
             rot=(R.uniform(-14, 14), 0, 0), uv={'all': (0, 0, 1, 1)})


def boarded_building(kit, root, p):
    root = kit.empty(f"{p} body", root, (0, 0, 0), (0, 0, 180))   # modeled facing -X, turned to face +X
    R = kit.rand
    front = tm(kit, "boarded front", lambda: tex_boarded_front(R))
    side = tm(kit, "boarded side", lambda: tex_boarded_side(R))
    wood = tm(kit, "plank", lambda: tex_plank(R))
    stone = solid(kit, "stone trim", "#e6c7d8", shade="#cfaec0")
    iron = solid(kit, "fire escape", "#4a4680", shade="#3a3666")
    tbox(kit, f"{p} foundation", (0, 0, 0.0), (BX1 - BX0 + 0.1, 2 * BY + 0.1, 0.3), solid(kit, "foundation", "#9a8fc8"), root)
    tbox(kit, f"{p} walls", (0, 0, BF + BH / 2), (BX1 - BX0, 2 * BY, BH), front, root,
         uv={'all': (0.9, 0.5, 0.92, 0.52), 'nx': (0, 0, 1, 1)})
    for sy in (1, -1):
        mb = MB()
        y = sy * (BY + 0.002)
        q = [(BX0, y, BF), (BX1, y, BF), (BX1, y, BF + BH), (BX0, y, BF + BH)]
        uv = [(0, 0), (1, 0), (1, 1), (0, 1)] if sy < 0 else [(1, 0), (0, 0), (0, 1), (1, 1)]
        if sy > 0:
            q = [q[1], q[0], q[3], q[2]]
            uv = [(0, 0), (1, 0), (1, 1), (0, 1)]
        mb.face(q, uv, 0)
        mb.obj(kit, f"{p} side {sy}", [side], root)
    top = BF + BH
    tbox(kit, f"{p} roof", (0, 0, top + 0.05), (BX1 - BX0 + 0.1, 2 * BY + 0.1, 0.1), solid(kit, "tar roof", "#6a5fa0"), root)
    tbox(kit, f"{p} cornice", (BX0 - 0.1, 0, top + 0.1), (0.45, 2 * BY + 0.5, 0.35), stone, root)
    tbox(kit, f"{p} parapet", (BX0 + 0.05, 0, top + 0.45), (0.25, 2 * BY + 0.2, 0.5), solid(kit, "brick", BRICK, shade=MORTAR), root)
    for sy in (1, -1):
        tbox(kit, f"{p} side cornice {sy}", (0, sy * (BY + 0.05), top + 0.1), (BX1 - BX0 + 0.3, 0.35, 0.3), stone, root)
    tbox(kit, f"{p} belt", (BX0 - 0.06, 0, BF + 3.2), (0.12, 2 * BY + 0.1, 0.18), stone, root)
    tbox(kit, f"{p} roof hatch", (1.4, -2.0, top + 0.45), (1.2, 1.2, 0.8), solid(kit, "hatch", "#8f86c8"), root)
    # boarded windows (texture texels -> wall coordinates), the middle upper window stays open (zombie eyes)
    for i, (x0, y0, x1, y1, n) in enumerate(((8, 10, 58, 38, 4), (102, 12, 120, 36, 3), (14, 56, 34, 82, 3), (94, 56, 114, 82, 2))):
        ya, za = front_px(x0, y0)
        yb, zb = front_px(x1 + 1, y1 + 1)
        boards(kit, root, f"{p} window {i} plank", (ya + yb) / 2, (za + zb) / 2, abs(yb - ya), zb - za, n, wood)
    for sy in (1, -1):
        for i, (x0, x1) in enumerate(((16, 35), (60, 79))):
            xa, xb = BX1 - x0 / 16, BX1 - x1 / 16
            if sy < 0:
                xa, xb = -xa, -xb
            for j in range(2):
                tbox(kit, f"{p} side plank {sy} {i} {j}", (0, 0, 0), (abs(xb - xa) + 0.35, 0.05, 0.2), wood, root,
                     loc=((xa + xb) / 2, sy * (BY + 0.04), 1.4 + j * 0.6 + 0.0), rot=(0, R.uniform(-14, 14), 0))
    ya, za = front_px(74, 0)
    yb, zb = front_px(91, 33)
    door = kit.empty(f"{p} door", root, (BX0 - 0.035, ya, BF))
    tbox(kit, f"{p} door", (0, (yb - ya) / 2, (zb - za) / 2), (0.06, abs(yb - ya), zb - za), solid(kit, "door wood", "#5e3a4a"), door)
    for s in (1, -1):
        tbox(kit, f"{p} door plank {s}", (0, 0, 0), (0.05, 1.9, 0.2), wood, root, loc=(BX0 - 0.09 - (s > 0) * 0.02, (ya + yb) / 2,
                                                                                         BF + 1.1), rot=(s * 52, 0, 0))
    kit.empty(f"{p} socket door", root, (BX0 - 0.9, (ya + yb) / 2, 0))
    tbox(kit, f"{p} step", (BX0 - 0.35, (ya + yb) / 2, 0.08), (0.7, 1.6, 0.16), stone, root)
    # hardware sign hanging from one bolt
    sign = kit.empty(f"{p} sign", root, (BX0 - 0.12, 0.45, 2.88), (-14, 0, 0))
    tbox(kit, f"{p} sign", (0, 1.75, -0.28), (0.08, 3.5, 0.56), tm(kit, "hardware sign", tex_hardware), sign,
         uv={'all': (0.4, 0.4, 0.42, 0.42), 'nx': (0, 0, 1, 1)})
    # fire escape on the +Y side with a drop ladder
    fy = BY + 0.55
    for z in (3.35, 5.45):
        tbox(kit, f"{p} escape deck {z}", (0, fy, z), (4.4, 1.0, 0.05), iron, root)
        tube(kit, f"{p} escape rail {z}", [(-2.2, fy + 0.5, z + 0.9), (2.2, fy + 0.5, z + 0.9)], 0.03, iron, root, sides=4,
             front=(0, 0, 1))
        for x in (-2.2, -0.7, 0.7, 2.2):
            tbox(kit, f"{p} escape post {z} {x}", (x, fy + 0.5, z + 0.45), (0.04, 0.04, 0.9), iron, root)
        for x in (-2.2, 2.2):
            tbox(kit, f"{p} escape bracket {z} {x}", (x, BY + 0.25, z - 0.25), (0.05, 0.6, 0.05), iron, root, rot=(-40, 0, 0))
    for x in (1.35, 1.85):
        tube(kit, f"{p} escape stair {x}", [(x, fy + 0.25, 3.38), (x - 1.6, fy + 0.25, 5.45)], 0.03, iron, root, sides=4,
             side=(0, 1, 0))
    for i in range(6):
        t = (i + 0.5) / 6
        tbox(kit, f"{p} escape tread {i}", (1.6 - 1.6 * t, fy + 0.25, 3.38 + 2.07 * t), (0.22, 0.5, 0.03), iron, root)
    drop = kit.empty(f"{p} drop ladder", root, (-1.6, fy + 0.3, 3.3))
    for x in (-0.22, 0.22):
        tbox(kit, f"{p} drop rail {x}", (x, 0, -0.9), (0.04, 0.04, 1.8), iron, drop)
    for i in range(6):
        tbox(kit, f"{p} drop rung {i}", (0, 0, -0.2 - i * 0.3), (0.44, 0.03, 0.03), iron, drop)
    # downpipe and trash bags
    tube(kit, f"{p} downpipe", [(BX0 - 0.1, -BY + 0.2, top), (BX0 - 0.1, -BY + 0.2, 2.2), (BX0 - 0.35, -BY + 0.25, 1.6)], 0.06,
         solid(kit, "pipe", "#8f86c8"), root, sides=6, side=(0, 1, 0))
    bag = solid(kit, "trash bag", "#3c2f5a", shade="#2e2448")
    for i, (x, y, r) in enumerate(((BX0 - 0.5, -3.4, 0.38), (BX0 - 0.6, -2.8, 0.32), (BX0 - 0.4, -2.3, 0.3))):
        lowball(kit, f"{p} trash bag {i}", (x, y, r * 0.8), (r, r, r * 0.85), bag, root)


# ---------------------------------------------------------------- scene
def road_strip(kit, root):
    """Town straight -> T-junction -> rural straight, dressed, seen like the truck sees it from above-behind."""
    for fn, y, nm in ((town_straight, 20, "Town Straight"), (t_junction, 0, "T Junction"), (rural_straight, -20, "Rural Straight")):
        fn(kit, kit.empty(f"strip {nm}", root, (0, y, 0)), f"strip {nm}")
    mb = MB()
    for poly in (rect(10, 4, 22, 32), rect(10, -32, 22, -4), rect(-22, -32, -10, 32)):
        lawn(mb, poly)
    mb.prism(rect(10, -4, 22, 4), BOT, 0.0, G_ASPH, S_ASPH)
    for sy in (1, -1):
        mb.prism(rect(10, sy * ROAD, 22, sy * (ROAD + CURB_W)), BOT, SIDE, G_CURB[0], 0.5)
    mb.obj(kit, "backlot", ground_mats(kit), root)
    paint(kit, root, "backlot", [[(10, sy * LINE_X), (22, sy * LINE_X)] for sy in (1, -1)], [[(11, 0), (13, 0)], [(15, 0), (17, 0)]])
    place(kit, house, root, "house", (-11.8, 23.0, SIDE), 0)
    place(kit, boarded_building, root, "boarded", (10.3, 20.0, SIDE), 180)
    place(kit, candy_shop, root, "candy shop", (-10.0, -0.5, SIDE), 0)
    for i, y in enumerate((19.0, 21.0, 25.0, 27.0)):
        place(kit, picket_fence, root, f"picket {i}", (-7.2, y, SIDE), 90)
    place(kit, mailbox, root, "house mailbox", (-6.6, 24.4, SIDE), 90)
    for i, y in enumerate((11.4, 13.9)):
        place(kit, chainlink_fence, root, f"chainlink {i}", (7.2, y, SIDE), 90)
    place(kit, wrecked_sedan, root, "sedan", (2.1, 27.0, 0.0), 166)
    place(kit, barricade, root, "barricade", (8.6, 1.6, 0.0), -90)
    for i, (x, y) in enumerate(((6.4, -1.8), (6.9, 2.4), (9.0, -2.6))):
        place(kit, traffic_cone, root, f"cone {i}", (x, y, 0.0), i * 30)
    place(kit, zombies_sign, root, "zombies sign", (-5.0, -12.5, SIDE), 180)
    place(kit, burnt_pickup, root, "pickup", (-6.6, -25.5, SIDE), 196)
    place(kit, trash_can, root, "shop can", (-6.4, 5.4, SIDE), 0)
    for i, (x, y, fn) in enumerate(((-15.5, -14.0, round_tree), (14.5, -24.0, pine_tree), (15.5, 8.5, round_tree),
                                    (-16.0, -27.0, pine_tree), (17.0, -12.0, pine_tree), (-16.5, 10.0, pine_tree))):
        place(kit, fn, root, f"backlot tree {i}", (x, y, SIDE), i * 50)
    for i, (x, y, rz) in enumerate(((-1.7, 4.5, 172), (1.4, -4.0, 196), (-5.6, 13.5, 140))):
        build_zombie(kit, kit.empty(f"walker {i}", root, (x, y, 0.0 if abs(x) < 4 else SIDE), (0, 0, rz)))
    build_sprinter(kit, kit.empty("sprinter", root, (0.6, 11.0, 0.0), (0, 0, 186)))


ASSET_FNS = [
    ("Town Straight", town_straight), ("Rural Straight", rural_straight), ("Curve Left", curve_left),
    ("T Junction", t_junction), ("Broken Road", broken_road),
    ("House", house), ("Candy Shop", candy_shop), ("Boarded Building", boarded_building),
    ("Street Lamp", street_lamp), ("Stop Sign", stop_sign), ("Speed Sign", speed_sign), ("Zombies Ahead Sign", zombies_sign),
    ("Mailbox", mailbox), ("Fire Hydrant", fire_hydrant), ("Trash Can", trash_can), ("Picket Fence", picket_fence),
    ("Chainlink Fence", chainlink_fence), ("Barricade", barricade), ("Traffic Cone", traffic_cone),
    ("Wrecked Sedan", wrecked_sedan), ("Burnt Pickup", burnt_pickup), ("Round Tree", round_tree), ("Pine Tree", pine_tree),
    ("Bush", bush), ("Hay Bale", hay_bale), ("Power Pole", power_pole),
]
ASSETS = [(n, (lambda f, n: lambda kit, root: f(kit, root, n))(f, n)) for n, f in ASSET_FNS]
def pothole_close(kit, root):
    broken_road(kit, kit.empty("pothole Broken Road", root), "pothole Broken Road")


def curve_seams(kit, root):
    """Rural straight -> curve left -> rural straight turned onto +X, plus a mirrored (right) curve, to show tiling."""
    rural_straight(kit, kit.empty("seams A", root, (0, 20, 0)), "seams A")
    curve_left(kit, kit.empty("seams B", root, (0, 0, 0)), "seams B")
    rural_straight(kit, kit.empty("seams C", root, (20, 0, 0), (0, 0, 90)), "seams C")
    curve_left(kit, kit.empty("seams D", root, (40, 0, 0), (0, 0, 90), (-1, 1, 1)), "seams D")


SCENES = [dict(name="road strip", build=road_strip, cam=((-1.5, 36.0, 7.5), (0.3, 6.0, 0.0), 24), res=(1600, 900)),
          dict(name="pothole close", build=pothole_close, cam=((0.2, -8.0, 3.2), (2.0, -1.0, 0.0), 30), res=(1600, 900)),
          dict(name="curve seams", build=curve_seams, cam=((-30.0, 58.0, 50.0), (13.0, 10.0, 0.0), 30), res=(1600, 900))]
