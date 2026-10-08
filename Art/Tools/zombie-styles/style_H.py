"""Style H: PS1 bright. Late-90s PlayStation low poly with a bright candy palette.
Hand-built low-poly tubes and boxes (6-8 sided limbs, gouraud shading, no subdivision), with faces, clothing,
apron stripes, hat band and zombie wounds painted into tiny Closest-sampled pixel textures."""
import subprocess
from common import *

KEY = "H"
LABEL = "PS1 bright"
SHADER = 'ps1'
WORLD = "#1b1033"
FLOOR = "#3b2a63"

PINK = "#ff4fa3"; BLUE = "#2e86ff"; MINT = "#38f2c3"; YEL = "#ffe14a"; SKIN = "#ffc29e"
ZG = "#9cff57"; PURP = "#8f5bff"; ORNG = "#ff8a3d"
WHITE = "#fff7ee"; INK = "#1b1033"; RED = "#ff2448"; DRED = "#b0103a"
PANTS = "#3c3fb8"; HAIR = "#7a3a1c"; CHOC = "#6e3a1e"


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


# ---------------------------------------------------------------- pixel textures
def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


class Canvas:
    """Tiny pixel canvas. Origin bottom-left (matches UV space); x wraps around so cylinders paint seamlessly."""

    def __init__(self, w, h, fill):
        self.w, self.h = w, h
        self.p = [rgb(fill)] * (w * h)

    def set(self, x, y, col):
        if 0 <= y < self.h:
            self.p[y * self.w + x % self.w] = rgb(col)

    def rect(self, x0, y0, x1, y1, col):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, col)

    def dots(self, pts, col):
        for x, y in pts:
            self.set(x, y, col)

    def speckle(self, rand, cols, n, y0=0, y1=None):
        y1 = self.h - 1 if y1 is None else y1
        for _ in range(n):
            self.set(rand.randrange(self.w), rand.randint(y0, y1), rand.choice(cols))

    def image(self, name):
        img = bpy.data.images.new(name, self.w, self.h, alpha=False)
        flat = []
        for c in self.p:
            flat.extend((c[0], c[1], c[2], 1.0))
        img.pixels.foreach_set(flat)
        img.update()
        img.pack()
        return img


def tex_mat(name, cv, emit=0.32, rough=0.8, ext='EXTEND'):
    m = bpy.data.materials.new(f"ZD2 H {name}")
    nt = v1.node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = cv.image(f"H {name}")
    tx.interpolation = 'Closest'
    tx.extension = ext
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = 0.2
    p.inputs["Emission Strength"].default_value = emit
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"])
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = (*cv.p[len(cv.p) // 2], 1.0)
    return m


def solid(kit, name, col, emit=0.32, shade=None):
    """Flat-color pixel material with a few darker texels for that dithered vertex-lit look."""
    cache = kit.__dict__.setdefault("_hmats", {})
    key = (name, col, emit)
    if key not in cache:
        cv = Canvas(8, 8, col)
        cv.speckle(kit.rand, [shade or hex_scale(col, 0.86)], 9)
        cache[key] = tex_mat(name, cv, emit)
    return cache[key]


# ---------------------------------------------------------------- low-poly builders
def tube(kit, name, pts, radii, mat, parent=None, sides=8, front=(0, -1, 0), side=None, caps=(True, True),
         bulge=(0.0, 0.0), loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, v=(0.0, 1.0)):
    """Hand-placed low-poly loft: one ring of `sides` verts per point, cylindrical UVs (u=0.5 faces `front`,
    v runs along the path). radii are r or (r_side, r_front)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    P = [Vector(p) for p in pts]
    n = len(P)
    if isinstance(radii, (int, float)):
        radii = [radii] * n
    L = [0.0]
    for i in range(1, n):
        L.append(L[-1] + (P[i] - P[i - 1]).length)
    V = [min(0.995, max(0.005, v[0] + (v[1] - v[0]) * l / L[-1])) for l in L]
    rings, T = [], []
    for i in range(n):
        if i == 0:
            t = P[1] - P[0]
        elif i == n - 1:
            t = P[-1] - P[-2]
        else:
            t = (P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()
        t.normalize()
        T.append(t)
        if side:
            s = Vector(side)
            s = (s - t * s.dot(t)).normalized()
            f = s.cross(t)
        else:
            f = Vector(front)
            f = (f - t * f.dot(t)).normalized()
            s = t.cross(f)
        r = radii[i]
        rx, ry = (r, r) if isinstance(r, (int, float)) else r
        rings.append([bm.verts.new(P[i] + s * math.sin(a) * rx + f * math.cos(a) * ry)
                      for a in (-math.pi + 2 * math.pi * k / sides for k in range(sides))])

    def face(vs, uvs):
        fc = bm.faces.new(vs)
        for lp, c in zip(fc.loops, uvs):
            lp[uvl].uv = c

    for i in range(n - 1):
        for k in range(sides):
            k2 = (k + 1) % sides
            face((rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]),
                 [(k / sides, V[i]), ((k + 1) / sides, V[i]), ((k + 1) / sides, V[i + 1]), (k / sides, V[i + 1])])
    for end, (idx, sgn) in enumerate(((0, -1), (n - 1, 1))):
        if caps[end]:
            c = bm.verts.new(P[idx] + T[idx] * sgn * bulge[end])
            for k in range(sides):
                k2 = (k + 1) % sides
                face((rings[idx][k], rings[idx][k2], c),
                     [(k / sides, V[idx]), ((k + 1) / sides, V[idx]), ((k + 0.5) / sides, V[idx])])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth)


BOX_FACES = {
    'ny': ((0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)),
    'py': ((1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)),
    'px': ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)),
    'nx': ((0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)),
    'pz': ((0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)),
    'nz': ((0, 1, 0), (1, 1, 0), (1, 0, 0), (0, 0, 0)),
}


def tbox(kit, name, center, size, mat, parent=None, rot=(0, 0, 0), uv=None, taper=(1.0, 1.0), smooth=False,
         loc=(0, 0, 0)):
    """Box with per-face UV rectangles (uv = {face: (u0, v0, u1, v1)}, default full texture). taper scales the top."""
    uv = uv or {}
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    R = Euler([math.radians(a) for a in rot]).to_matrix()
    verts = {}
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                tx, ty = (taper[0], taper[1]) if iz else (1.0, 1.0)
                p = Vector(((ix - 0.5) * size[0] * tx, (iy - 0.5) * size[1] * ty, (iz - 0.5) * size[2]))
                verts[(ix, iy, iz)] = bm.verts.new(R @ p + Vector(center))
    for fname, corners in BOX_FACES.items():
        u0, v0, u1, v1_ = uv.get(fname, uv.get('all', (0.0, 0.0, 1.0, 1.0)))
        fc = bm.faces.new([verts[c] for c in corners])
        for lp, c in zip(fc.loops, ((u0, v0), (u1, v0), (u1, v1_), (u0, v1_))):
            lp[uvl].uv = c
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, smooth=smooth)


def lowball(kit, name, center, radii, mat, parent=None, smooth=True):
    return kit.prim(name, 'ico', radii, mat, parent, offset=center, segments=1, smooth=smooth)


def aim(ob, d):
    """Point the pivot's local -Z along d (local +Y stays as close to up as possible)."""
    ob.rotation_euler = Vector(d).to_track_quat('-Z', 'Y').to_euler()


def splat(kit, name, center, r, mat, parent, lobes=11, z=0.004):
    bm = bmesh.new()
    vs = []
    for i in range(lobes):
        a = 2 * math.pi * i / lobes
        rr = r * (0.55 + 0.6 * kit.rand.random()) if i % 2 else r * (0.8 + 0.25 * kit.rand.random())
        vs.append(bm.verts.new((center[0] + math.cos(a) * rr, center[1] + math.sin(a) * rr, z)))
    bm.faces.new(vs)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


# ---------------------------------------------------------------- textures: player
def tex_player_head():
    c = Canvas(64, 64, SKIN)
    # hair: crown, back of head and sideburns
    c.rect(0, 47, 63, 63, HAIR)
    for x in range(64):
        back = x < 17 or x > 47
        if back:
            c.rect(x, 16 + (x * 7) % 3, x, 47, HAIR)
    c.rect(17, 34, 19, 47, HAIR); c.rect(45, 34, 47, 47, HAIR)
    c.dots([(24, 46), (25, 45), (26, 46), (30, 45), (31, 44), (36, 45), (37, 46), (40, 45)], HAIR)
    # ears
    c.rect(16, 29, 17, 36, "#f2a37f"); c.rect(47, 29, 48, 36, "#f2a37f")
    # brows
    c.rect(25, 41, 28, 41, HAIR); c.rect(35, 41, 38, 41, HAIR)
    # eyes: white, dark pupil, highlight
    for x0 in (25, 35):
        c.rect(x0, 35, x0 + 3, 38, WHITE)
        c.rect(x0 + 1, 35, x0 + 2, 38, INK)
        c.set(x0 + 2, 38, WHITE)
    # nose
    c.dots([(31, 31), (32, 31), (32, 32)], "#f0a07c")
    # blush
    c.rect(23, 30, 25, 31, "#ff8fae"); c.rect(38, 30, 40, 31, "#ff8fae")
    # smile
    c.rect(28, 25, 35, 25, "#8a1f3d")
    c.rect(29, 24, 34, 24, "#ff6f8f")
    c.dots([(27, 26), (36, 26)], "#8a1f3d")
    c.rect(29, 25, 34, 25, WHITE)
    c.rect(28, 26, 35, 26, "#8a1f3d")
    return c


def tex_hat():
    c = Canvas(64, 32, WHITE)
    c.rect(0, 4, 63, 8, PINK)
    c.rect(0, 10, 63, 10, BLUE)
    c.rect(0, 0, 63, 1, "#e9ded6")
    for cx in (16, 48):  # little cone logo on each side
        for row in range(7):
            half = row // 2
            c.rect(cx - half, 12 + row, cx + half, 12 + row, "#f0a43a")
        c.rect(cx - 3, 19, cx + 3, 22, PINK)
        c.rect(cx - 2, 23, cx + 2, 23, PINK)
        c.dots([(cx - 1, 21), (cx + 2, 20)], WHITE)
    c.rect(30, 26, 33, 31, "#efe4da")
    return c


def tex_player_torso(rand):
    c = Canvas(64, 64, BLUE)
    c.rect(0, 0, 63, 8, PANTS)
    c.rect(0, 9, 63, 11, PINK)  # apron waist tie
    c.rect(56, 6, 58, 10, PINK); c.rect(59, 4, 60, 8, PINK)  # bow tails at the back
    # bib with candy stripes
    for y in range(12, 50):
        half = 9 if y < 40 else 7
        for x in range(32 - half, 32 + half):
            c.set(x, y, PINK if (x - 32) % 4 == 0 else WHITE)
        c.set(32 - half - 1, y, PINK); c.set(32 + half, y, PINK)
    c.rect(24, 49, 39, 50, PINK)
    c.rect(28, 20, 35, 26, PINK); c.rect(29, 21, 34, 25, "#ff7dbb")  # pocket
    c.dots([(30, 24), (33, 24)], WHITE)
    c.rect(34, 42, 38, 45, YEL); c.rect(35, 43, 37, 43, INK)  # name tag
    # straps over the shoulders, crossing on the back
    c.rect(25, 50, 26, 63, PINK); c.rect(37, 50, 38, 63, PINK)
    for i in range(46):
        y = 63 - i
        c.set(-10 + i // 2 + 64, y, PINK); c.set(10 - i // 2, y, PINK)
    # collar
    c.rect(28, 58, 35, 63, SKIN); c.dots([(28, 58), (35, 58)], BLUE)
    c.rect(26, 60, 27, 63, WHITE); c.rect(36, 60, 37, 63, WHITE)
    c.rect(0, 62, 63, 63, WHITE); c.rect(28, 62, 35, 63, SKIN)
    c.speckle(rand, ["#2a78ea"], 40, 12, 57)
    return c


def tex_player_arm():
    c = Canvas(16, 32, SKIN)
    c.rect(0, 0, 15, 8, BLUE)
    c.rect(0, 8, 15, 8, WHITE)
    c.rect(0, 27, 15, 29, MINT)
    c.dots([(3, 15), (11, 20)], "#f0a888")
    return c


def tex_player_leg():
    c = Canvas(16, 32, PANTS)
    c.rect(3, 0, 4, 31, MINT); c.rect(11, 0, 12, 31, MINT)
    c.rect(0, 29, 15, 31, "#5559d8")
    c.rect(0, 0, 15, 1, "#30329a")
    return c


def tex_shoe():
    c = Canvas(16, 16, PINK)
    c.rect(0, 0, 3, 15, WHITE); c.rect(12, 0, 15, 15, WHITE)
    for y in (5, 7, 9):
        c.rect(7, y, 8, y, WHITE)
    c.rect(4, 12, 11, 15, "#ff7dbb")
    c.rect(4, 0, 11, 2, "#d63a86")
    return c


def tex_apron():
    c = Canvas(32, 32, WHITE)
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 31, PINK)
    c.rect(0, 0, 31, 2, PINK)
    c.rect(0, 29, 31, 31, PINK)
    c.rect(10, 8, 21, 20, "#ff7dbb")
    c.rect(11, 9, 20, 19, WHITE)
    for row in range(6):
        c.rect(15 - row // 2, 10 + row, 16 + row // 2, 10 + row, "#f0a43a")
    c.rect(13, 16, 18, 18, MINT); c.rect(14, 19, 17, 19, MINT)
    c.set(15, 18, PINK)
    return c


def tex_cooler():
    c = Canvas(32, 32, MINT)
    c.rect(0, 0, 31, 1, "#22c79c")
    c.rect(0, 10, 31, 12, PINK)
    c.rect(0, 26, 31, 31, WHITE)
    c.rect(0, 25, 31, 25, "#22c79c")
    # snowflake badge
    for i in range(-3, 4):
        c.set(16 + i, 18, WHITE); c.set(16, 18 + i, WHITE); c.set(16 + i, 18 + i, WHITE); c.set(16 + i, 18 - i, WHITE)
    c.rect(29, 28, 31, 31, PINK)
    return c


def tex_pint(col):
    c = Canvas(32, 16, WHITE)
    c.rect(0, 3, 31, 10, col)
    c.rect(0, 13, 31, 15, hex_scale(col, 0.8))
    c.rect(0, 0, 31, 0, "#e6dcd2")
    for x in (8, 24):
        c.rect(x - 1, 5, x + 1, 8, WHITE); c.set(x, 6, YEL)
    return c


# ---------------------------------------------------------------- textures: zombie
def tex_zombie_head(rand):
    c = Canvas(64, 64, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d", "#86e64a"], 160)
    c.rect(0, 58, 63, 63, DRED)  # open scalp rim
    for x in range(64):
        c.rect(x, 55 + rand.randint(0, 3), x, 58, DRED)
    # purple tufts at the back and sides
    for x in list(range(0, 16)) + list(range(48, 64)):
        if rand.random() < 0.55:
            c.rect(x, 44 + rand.randint(0, 4), x, 54, PURP)
    # dark sockets
    c.rect(23, 33, 29, 40, "#5fb52e"); c.rect(34, 32, 41, 41, "#5fb52e")
    # right eye (-X): small, red, squinting
    c.rect(24, 36, 28, 37, INK); c.rect(25, 36, 27, 37, RED); c.set(26, 37, YEL)
    c.rect(23, 38, 29, 38, "#3f8a1f")
    # left eye (+X): huge bulging white with a pinprick pupil and veins
    c.rect(35, 33, 40, 40, WHITE)
    c.set(35, 33, "#5fb52e"); c.set(40, 40, "#5fb52e")
    c.dots([(38, 36), (37, 36)], INK)
    c.dots([(35, 38), (36, 39), (40, 35), (39, 34)], RED)
    # skull nose
    c.dots([(31, 30), (33, 30), (31, 29), (33, 29)], "#2a5a12")
    # grimace: clenched teeth, black gaps, gums, down-turned corners
    c.rect(24, 19, 40, 26, "#2a0f2e")
    c.rect(25, 25, 39, 25, "#ff5d7a")
    for x in range(25, 40):
        c.rect(x, 23, x, 24, "#fff1c7" if x % 2 else "#e8d27a")
        c.rect(x, 20, x, 21, "#fff1c7" if x % 2 == 0 else "#e8d27a")
    c.rect(25, 22, 39, 22, "#2a0f2e")
    c.dots([(23, 19), (22, 18), (41, 19), (42, 18)], "#2a0f2e")
    c.rect(29, 21, 30, 21, "#2a0f2e")  # missing tooth
    # stitches on the cheek
    for x in range(42, 49):
        c.set(x, 29, INK)
    for x in (43, 45, 47):
        c.set(x, 28, INK); c.set(x, 30, INK)
    # ears, wound
    c.rect(16, 28, 17, 35, "#6fcf35"); c.rect(47, 28, 48, 33, "#6fcf35")
    c.rect(18, 42, 21, 44, RED); c.set(19, 43, DRED)
    return c


def tex_brain(rand):
    c = Canvas(32, 16, "#ff8fc8")
    for _ in range(14):
        x, y = rand.randrange(32), rand.randrange(16)
        for _ in range(7):
            c.set(x, y, "#d8337a")
            x += rand.choice((-1, 0, 1)); y += rand.choice((-1, 0, 1))
    c.rect(15, 6, 16, 15, "#c02768"); c.rect(0, 6, 0, 15, "#c02768"); c.rect(31, 6, 31, 15, "#c02768")
    c.rect(0, 0, 31, 1, DRED)
    c.speckle(rand, ["#ffc0e0"], 18, 2, 15)
    return c


def tex_zombie_torso(rand):
    c = Canvas(64, 64, ORNG)
    c.rect(0, 0, 63, 9, PURP)
    c.rect(0, 9, 63, 10, "#5b34b8")  # belt
    c.rect(30, 9, 33, 10, YEL)
    # torn shirt hem showing green belly
    for x in range(64):
        c.rect(x, 11, x, 11 + rand.choice((1, 2, 3, 5, 6)), ZG)
    c.speckle(rand, ["#e8752b", "#ffa060"], 90, 18, 60)
    # faded logo (pale circle) and holes
    for (hx, hy, r) in ((22, 40, 3), (6, 30, 4), (54, 22, 3), (44, 52, 2)):
        for y in range(hy - r - 1, hy + r + 2):
            for x in range(hx - r - 1, hx + r + 2):
                d = (x - hx) ** 2 + (y - hy) ** 2
                if d <= r * r:
                    c.set(x, y, ZG)
                elif d <= (r + 1) ** 2:
                    c.set(x, y, "#b84a14")
    for y in (28, 30, 32):  # ribs through the side hole
        c.rect(4, y, 8, y, WHITE)
    # wound slash
    for i in range(7):
        c.set(25 + i, 24 + i, RED); c.set(26 + i, 24 + i, DRED)
    # ice cream splat on the chest with drips
    for y in range(38, 50):
        for x in range(30, 44):
            if (x - 37) ** 2 / 49 + (y - 44) ** 2 / 30 < 1:
                c.set(x, y, PINK if (x + y) % 7 else "#ff8fc8")
    c.rect(33, 44, 37, 47, WHITE); c.rect(38, 42, 40, 44, "#ffd0e6")
    for dx, ln in ((31, 6), (34, 9), (38, 4), (41, 7)):
        c.rect(dx, 38 - ln, dx, 38, PINK)
        c.set(dx, 37 - ln, "#ff8fc8")
    c.dots([(33, 46), (36, 48), (39, 47), (35, 44)], BLUE)
    c.dots([(31, 45), (38, 49)], YEL)
    # collar torn open
    c.rect(28, 58, 36, 63, ZG); c.rect(0, 62, 63, 63, "#d9631f"); c.rect(28, 62, 36, 63, ZG)
    return c


def tex_zombie_arm(rand):
    c = Canvas(16, 32, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 60)
    c.rect(0, 0, 15, 1, DRED)  # shoulder stump
    c.rect(0, 2, 15, 9, ORNG)
    for x in range(16):
        c.rect(x, 10, x, 10 + rand.choice((0, 1, 2, 3)), ORNG)
    c.rect(5, 17, 8, 19, RED); c.set(6, 18, DRED)
    c.rect(10, 24, 12, 25, PURP)
    c.dots([(2, 22), (3, 23), (13, 14)], "#5fb52e")
    return c


def tex_zombie_hand():
    c = Canvas(16, 16, ZG)
    for x in (2, 6, 10, 14):
        c.rect(x, 6, x, 15, "#5fb52e")
    c.rect(0, 13, 15, 15, "#e8d27a")
    c.rect(0, 0, 15, 1, "#7fe03f")
    return c


def tex_zombie_leg(rand, torn):
    c = Canvas(16, 32, PURP)
    c.speckle(rand, ["#7a48ea", "#a57bff"], 40)
    c.rect(3, 8, 6, 12, ORNG); c.dots([(3, 8), (6, 12), (3, 12), (6, 8)], "#b84a14")
    if torn:
        for x in range(16):
            c.rect(x, 20 + rand.choice((0, 1, 2, 3, 4)), x, 31, ZG)
        c.rect(9, 26, 11, 27, RED)
    else:
        c.rect(0, 29, 15, 31, "#6d42d6")
    return c


def tex_waffle():
    c = Canvas(32, 16, "#ffcf5a")
    for y in range(16):
        for x in range(32):
            if (x + y) % 5 == 0 or (x - y) % 5 == 0:
                c.set(x, y, "#d9862a")
    c.rect(0, 14, 31, 15, "#c96f1c")
    return c


def tex_gun_body():
    c = Canvas(32, 16, MINT)
    c.rect(0, 0, 31, 1, "#1fbf95")
    c.rect(0, 6, 31, 8, PINK)
    c.rect(0, 14, 31, 15, "#8ff9de")
    for x in range(2, 31, 4):
        c.set(x, 3, "#1fbf95"); c.set(x, 11, "#1fbf95")
    for row in range(5):
        c.rect(22 - row // 2, 9 + row, 22 + row // 2, 9 + row, YEL)
    return c


def tex_grip():
    c = Canvas(16, 16, PINK)
    for y in range(1, 16, 3):
        c.rect(0, y, 15, y, "#d63a86")
    c.rect(0, 14, 15, 15, "#ff8fc8")
    return c


# ---------------------------------------------------------------- player
def player_arm(kit, root, name, shoulder, target, tex_arm, skin, hand_extra=None):
    piv = kit.empty(name, root, shoulder)
    d = Vector(target) - Vector(shoulder)
    aim(piv, d)
    L = d.length
    tube(kit, name + " arm", [(0, 0, 0.02), (0, 0, -0.12), (0, 0, -0.27), (0, 0, -(L - 0.06))],
         [0.066, 0.058, 0.05, 0.038], tex_arm, piv, sides=6, front=(0, 1, 0), bulge=(0.03, 0))
    tube(kit, name + " hand", [(0, 0, -(L - 0.07)), (0, 0, -(L - 0.02)), (0, 0, -(L + 0.04))],
         [(0.042, 0.032), (0.048, 0.036), (0.036, 0.028)], skin, piv, sides=6, front=(0, 1, 0), bulge=(0, 0.02))
    return piv, L


def build_player(kit, root):
    t_head = tex_mat("player head", tex_player_head())
    t_hat = tex_mat("hat", tex_hat())
    t_torso = tex_mat("player torso", tex_player_torso(kit.rand))
    t_arm = tex_mat("player arm", tex_player_arm())
    t_leg = tex_mat("player leg", tex_player_leg())
    t_shoe = tex_mat("shoe", tex_shoe())
    t_apron = tex_mat("apron", tex_apron())
    t_cool = tex_mat("cooler", tex_cooler())
    skin = solid(kit, "skin", SKIN)

    # torso: one 8-sided loft, pants waistband to shoulders
    tube(kit, "torso", [(0, 0, 0.84), (0, 0, 0.94), (0, 0, 1.08), (0, -0.005, 1.24), (0, 0.005, 1.38), (0, 0.01, 1.47)],
         [(0.15, 0.1), (0.155, 0.105), (0.138, 0.098), (0.16, 0.11), (0.19, 0.112), (0.085, 0.068)], t_torso, root)

    # apron skirt: hand-built curved strip with planar UVs
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    cols, rows = 5, 3
    grid = []
    for j, (z, rx, ry) in enumerate(((0.95, 0.165, 0.118), (0.75, 0.19, 0.14), (0.55, 0.2, 0.15))):
        row = []
        for i in range(cols):
            a = math.radians(-62 + 124 * i / (cols - 1))
            row.append(bm.verts.new((math.sin(a) * rx, -math.cos(a) * ry - 0.004, z)))
        grid.append(row)
    for j in range(rows - 1):
        for i in range(cols - 1):
            fc = bm.faces.new((grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]))
            for lp, uv in zip(fc.loops, ((i / 4, 1 - (j + 1) / 2), ((i + 1) / 4, 1 - (j + 1) / 2),
                                         ((i + 1) / 4, 1 - j / 2), (i / 4, 1 - j / 2))):
                lp[uvl].uv = (min(0.995, max(0.005, uv[0])), min(0.995, max(0.005, uv[1])))
    kit.mesh_from_bmesh("apron", bm, t_apron, root)

    # head + paper soda-jerk hat
    head = kit.empty("head pivot", root, (0, -0.005, 1.45))
    tube(kit, "head", [(0, 0, 0), (0, 0, 0.05), (0, -0.005, 0.08), (0, -0.01, 0.13), (0, -0.005, 0.19), (0, 0, 0.25),
                       (0, 0.005, 0.29), (0, 0.005, 0.31)],
         [0.048, 0.054, (0.078, 0.085), (0.1, 0.106), (0.106, 0.112), (0.098, 0.104), (0.07, 0.075), (0.03, 0.035)],
         t_head, head, bulge=(0, 0.01))
    tube(kit, "hat", [(0, 0.004, 0.205), (0, 0.004, 0.245), (0, 0.004, 0.3), (0, 0.004, 0.345)],
         [(0.113, 0.121), (0.108, 0.13), (0.06, 0.134), (0.012, 0.126)], t_hat, head, caps=(False, True))

    # legs: one 6-sided loft each plus a sneaker
    for sx, name in ((1, "L"), (-1, "R")):
        leg = kit.empty(f"leg {name}", root, (sx * 0.085, 0, 0.9), (0, sx * -3, 0))
        tube(kit, f"leg {name}", [(0, 0, 0.04), (0, 0, -0.2), (0, -0.012, -0.43), (0, 0, -0.62), (0, 0, -0.82)],
             [(0.082, 0.088), 0.07, 0.056, 0.05, 0.043], t_leg, leg, sides=6, front=(0, 1, 0))
        tube(kit, f"shoe {name}", [(0, 0.05, -0.86), (0, -0.03, -0.855), (0, -0.12, -0.87)],
             [(0.048, 0.042), (0.054, 0.048), (0.042, 0.03)], t_shoe, leg, sides=6, front=(0, 0, 1),
             bulge=(0.015, 0.03))

    # arms: right arm straight out aiming, left hand cupping under the grip
    hand_r = Vector((-0.11, -0.6, 1.38))
    arm_r, L = player_arm(kit, root, "arm R", (-0.2, 0, 1.39), hand_r, t_arm, skin)
    gun = kit.empty("held gun", arm_r, (0, 0.062, -L - 0.052))
    gun.rotation_euler = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0))).to_euler()
    build_gun(kit, gun)
    player_arm(kit, root, "arm L", (0.2, 0, 1.39), hand_r + Vector((0.05, 0.05, -0.07)), t_arm, skin)

    # cooler backpack with straps and spare pints
    back = kit.empty("cooler pivot", root, (0, 0.2, 1.17))
    tbox(kit, "cooler", (0, 0, 0), (0.34, 0.2, 0.3), t_cool, back,
         uv={'pz': (0.9, 0.9, 1.0, 1.0), 'nz': (0.1, 0.0, 0.2, 0.05)})
    tbox(kit, "cooler lid", (0, 0, 0.165), (0.36, 0.22, 0.04), solid(kit, "lid", PINK), back)
    tube(kit, "handle", [(-0.1, 0, 0.185), (-0.08, 0, 0.215), (0.08, 0, 0.215), (0.1, 0, 0.185)], 0.01,
         solid(kit, "handle", YEL), back, sides=4, side=(0, 1, 0))
    for i, (x, col) in enumerate(((-0.105, PINK), (0.0, MINT), (0.105, YEL))):
        y = 0.035 if i != 1 else -0.03
        t_pint = tex_mat(f"pint {i}", tex_pint(col))
        tube(kit, f"pint {i}", [(x, y, 0.185), (x, y, 0.285)], [0.04, 0.046], t_pint, back, sides=8)
        tube(kit, f"pint lid {i}", [(x, y, 0.285), (x, y, 0.3)], [0.05, 0.05], solid(kit, f"pint lid {i}", hex_scale(col, 0.8)),
             back, sides=8)
    strap = solid(kit, "strap", YEL)
    for sx in (1, -1):
        tube(kit, f"strap {sx}", [(sx * 0.11, 0.1, 1.33), (sx * 0.115, 0.06, 1.455), (sx * 0.12, -0.06, 1.44),
                                  (sx * 0.125, -0.112, 1.33), (sx * 0.13, -0.114, 1.16)],
             [(0.024, 0.007)] * 5, strap, root, sides=4, side=(1, 0, 0), caps=(False, False))


# ---------------------------------------------------------------- zombie
def zombie_arm(kit, parent, name, loc, d, elbow, wrist, t_arm, t_hand):
    piv = kit.empty(f"arm {name}", parent, loc)
    aim(piv, d)
    tube(kit, f"upper arm {name}", [(0, 0, 0.03), (0, 0, -0.14), (0, 0, -0.28)], [0.062, 0.056, 0.048], t_arm, piv,
         sides=6, front=(0, 1, 0), v=(0.0, 0.5), bulge=(0.02, 0.0))
    fore = kit.empty(f"forearm {name}", piv, (0, 0, -0.28), elbow)
    tube(kit, f"forearm {name}", [(0, 0, 0.02), (0, 0, -0.13), (0, 0, -0.26)], [0.048, 0.045, 0.034], t_arm, fore,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    hand = kit.empty(f"hand {name}", fore, (0, 0, -0.26), wrist)
    tube(kit, f"hand {name}", [(0, 0, 0.01), (0, 0, -0.06), (0, 0, -0.13)], [(0.044, 0.026), (0.05, 0.026), (0.04, 0.02)],
         t_hand, hand, sides=6, front=(0, 1, 0), bulge=(0, 0.015))
    return piv


def zombie_leg(kit, parent, name, loc, thigh, knee, t_leg, foot_mat, bare):
    piv = kit.empty(f"leg {name}", parent, loc, thigh)
    tube(kit, f"thigh {name}", [(0, 0, 0.04), (0, 0, -0.2), (0, 0, -0.42)], [(0.08, 0.085), 0.068, 0.056], t_leg, piv,
         sides=6, front=(0, 1, 0), v=(0.0, 0.5))
    shin = kit.empty(f"shin {name}", piv, (0, 0, -0.42), knee)
    tube(kit, f"shin {name}", [(0, 0, 0.02), (0, -0.01, -0.2), (0, 0, -0.4)], [0.056, 0.05, 0.042], t_leg, shin,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    foot = kit.empty(f"foot {name}", shin, (0, 0, -0.43), (-(thigh[0] + knee[0]), 0, 0))
    if bare:
        tube(kit, f"foot {name}", [(0, 0.04, 0.0), (0, -0.05, -0.005), (0, -0.13, -0.015)],
             [(0.042, 0.036), (0.05, 0.03), (0.046, 0.018)], foot_mat, foot, sides=6, front=(0, 0, 1), bulge=(0.01, 0.02))
    else:
        tube(kit, f"foot {name}", [(0, 0.05, 0.0), (0, -0.04, 0.005), (0, -0.13, -0.01)],
             [(0.05, 0.044), (0.055, 0.048), (0.044, 0.03)], foot_mat, foot, sides=6, front=(0, 0, 1),
             bulge=(0.015, 0.03))
    return piv, foot


def build_zombie(kit, root, hit=False):
    t_head = tex_mat("zombie head", tex_zombie_head(kit.rand))
    t_brain = tex_mat("brain", tex_brain(kit.rand))
    t_torso = tex_mat("zombie torso", tex_zombie_torso(kit.rand))
    t_arm = tex_mat("zombie arm", tex_zombie_arm(kit.rand))
    t_hand = tex_mat("zombie hand", tex_zombie_hand())
    t_leg = tex_mat("zombie leg", tex_zombie_leg(kit.rand, False))
    t_leg_torn = tex_mat("zombie leg torn", tex_zombie_leg(kit.rand, True))
    shoe = tex_mat("zombie shoe", tex_shoe())
    bare = solid(kit, "bare foot", ZG)
    cream = solid(kit, "scoop", PINK, 0.4)

    hips = kit.empty("hips", root, (0, 0.02, 0.9), (0, 0, -4) if not hit else (0, 0, 10))
    spine_rot = (30, -6, 8) if not hit else (-16, 12, -14)
    spine = kit.empty("spine", hips, (0, 0, 0), spine_rot)
    tube(kit, "torso", [(0, 0, -0.08), (0, 0, 0.05), (0, 0.015, 0.2), (0, 0.045, 0.36), (0, 0.06, 0.5), (0, 0.05, 0.585)],
         [(0.15, 0.1), (0.152, 0.104), (0.135, 0.1), (0.158, 0.11), (0.185, 0.115), (0.085, 0.07)], t_torso, spine)
    # melting scoop stuck on the right shoulder
    lowball(kit, "shoulder scoop", (-0.13, -0.02, 0.56), (0.07, 0.065, 0.05), cream, spine)
    tube(kit, "scoop drip", [(-0.17, -0.06, 0.53), (-0.175, -0.075, 0.44), (-0.17, -0.08, 0.4)], [0.022, 0.018, 0.012],
         cream, spine, sides=5, bulge=(0, 0.012))

    head = kit.empty("head", spine, (0, 0.02, 0.57), (-26, 16, -10) if not hit else (-34, -12, 20), (1.12, 1.12, 1.12))
    tube(kit, "head", [(0, 0, 0), (0, -0.02, 0.05), (0, -0.035, 0.08), (0, -0.04, 0.13), (0, -0.035, 0.19),
                       (0, -0.03, 0.245), (0, -0.03, 0.26)],
         [0.046, 0.052, (0.088, 0.088), (0.1, 0.104), (0.104, 0.11), (0.096, 0.104), (0.084, 0.09)],
         t_head, head, caps=(True, False))
    tube(kit, "brain", [(0, -0.03, 0.235), (0, -0.03, 0.27), (0, -0.03, 0.305), (0, -0.03, 0.322)],
         [(0.088, 0.096), (0.09, 0.098), (0.068, 0.076), (0.03, 0.036)], t_brain, head, v=(0.0, 1.0), bulge=(0, 0.006))

    # arms
    if not hit:
        zombie_arm(kit, spine, "R", (-0.2, 0.05, 0.5), (0.02, -1, 0.62), (-10, 0, 0), (-40, 0, 0), t_arm, t_hand)
        zombie_arm(kit, spine, "L", (0.2, 0.05, 0.5), (0.06, -1, 0.45), (-14, 0, 6), (-34, 0, 0), t_arm, t_hand)
    else:
        zombie_arm(kit, spine, "R", (-0.2, 0.05, 0.5), (-0.7, 0.1, 0.9), (-30, 0, 0), (20, 0, 0), t_arm, t_hand)

    # legs: stiff shamble, one foot dragging
    if not hit:
        lp, lf = zombie_leg(kit, hips, "L", (0.095, 0, 0), (-16, 0, 4), (14, 0, 0), t_leg, shoe, False)
        rp, rf = zombie_leg(kit, hips, "R", (-0.095, 0, 0), (10, 0, -5), (6, 0, 0), t_leg_torn, bare, True)
    else:
        lp, lf = zombie_leg(kit, hips, "L", (0.095, 0, 0), (12, -4, 12), (10, 0, 0), t_leg, shoe, False)
        rp, rf = zombie_leg(kit, hips, "R", (-0.095, 0, 0), (-22, 0, -6), (30, 0, 0), t_leg_torn, bare, True)

    # drop the hips so the lower foot sits on the floor
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    low = min((inv @ f.matrix_world.translation).z for f in (lf, rf))
    hips.location.z -= low - 0.035

    if hit:
        build_hit_fx(kit, root, spine, t_arm, t_hand)


def build_hit_fx(kit, root, spine, t_arm, t_hand):
    """Left arm flies off toward the camera's right; chunky pixel cubes, sprinkles, hit stars and flat splats."""
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    rz = root.rotation_euler.z
    fx = kit.empty("fx (world aligned)", root, (0, 0, 0), (0, 0, -math.degrees(rz)))
    to_fx = Matrix.Rotation(rz, 3, 'Z')
    S = to_fx @ (inv @ (spine.matrix_world @ Vector((0.2, 0.05, 0.5))))
    D = Vector((0.75, -0.42, 0.52)).normalized()
    R = kit.rand

    # flying arm, spinning
    arm_end = S + Vector((0.5, -0.32, 0.38))
    arm = zombie_arm(kit, fx, "L (flying)", arm_end, (0.9, 0.1, -0.35), (-20, 0, 10), (-30, 0, 0), t_arm, t_hand)
    arm.rotation_euler.rotate_axis('Z', math.radians(70))

    red = solid(kit, "blood", RED, 0.55, shade=DRED)
    dred = solid(kit, "blood dark", DRED, 0.45)
    creams = [solid(kit, "fx " + c, c, 0.55) for c in (PINK, WHITE, MINT, YEL)]
    sprinkle_cols = [solid(kit, "sprinkle " + c, c, 0.7) for c in (PINK, BLUE, YEL, MINT, WHITE, PURP, ORNG)]

    def cube(name, p, s, m):
        return tbox(kit, name, (0, 0, 0), (s, s, s), m, fx, loc=p,
                    rot=(R.uniform(0, 90), R.uniform(0, 90), R.uniform(0, 90)))

    # stump gush
    cube("stump", S + Vector((0.01, -0.01, 0)), 0.075, red)
    for i in range(16):
        t = R.uniform(0.06, 0.75)
        p = S + D * t + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1.4, 0.8))) * (0.06 + 0.4 * t)
        cube(f"blood cube {i}", p, R.uniform(0.03, 0.065) * (1.25 - t), red if i % 4 else dred)
    # drips falling from the burst toward the floor splats
    for i in range(6):
        p = S + D * (0.15 + 0.1 * i) + Vector((0, 0, -0.25 - 0.13 * i))
        cube(f"drip {i}", p, 0.04 - 0.003 * i, red if i % 3 else creams[0])
    # trail between stump and the flying arm
    for i in range(7):
        f = (i + 1) / 8
        p = S.lerp(arm_end, f) + Vector((0, 0, 0.05 * math.sin(f * math.pi)))
        cube(f"trail {i}", p, 0.055 - 0.005 * i, red if i % 2 else creams[0])
    # ice cream chunks and blobs
    for i in range(14):
        t = R.uniform(0.1, 0.85)
        p = S + D * t + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-0.6, 1.2))) * (0.08 + 0.4 * t)
        cube(f"cream cube {i}", p, R.uniform(0.035, 0.07), creams[i % 4])
    for i, (off, rr) in enumerate(((Vector((0.18, -0.2, 0.22)), 0.06), (Vector((0.32, 0.05, 0.08)), 0.05),
                                   (Vector((0.05, -0.28, -0.05)), 0.045))):
        lowball(kit, f"cream blob {i}", S + off, (rr, rr, rr * 0.85), creams[i % 3], fx, smooth=False)
    # sprinkles
    for i in range(36):
        t = R.uniform(0.05, 0.7)
        p = S + D * t + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * (0.08 + 0.3 * t)
        tbox(kit, f"sprinkle {i}", (0, 0, 0), (0.009, 0.009, 0.034), sprinkle_cols[i % 7], fx, loc=p,
             rot=(R.uniform(0, 180), R.uniform(0, 180), R.uniform(0, 180)))
    # flat hit stars facing the camera
    face = (0, 0, 21)
    toward_cam = Vector((0.36, -0.93, 0)) * 0.12
    star_y = kit.link("hit star", star_mesh("hit star", 8, 0.26, 0.11), fx, S + D * 0.08 + toward_cam, face)
    star_y.data.materials.append(solid(kit, "star", YEL, 1.4))
    star_w = kit.link("hit star core", star_mesh("hit star core", 6, 0.1, 0.05), fx,
                      S + D * 0.08 + toward_cam * 1.15, (0, 12, 21))
    star_w.data.materials.append(solid(kit, "star core", WHITE, 1.6))
    star_p = kit.link("hit star pink", star_mesh("hit star pink", 5, 0.08, 0.035), fx,
                      arm_end + Vector((0.02, -0.06, 0.08)), (0, 30, 21))
    star_p.data.materials.append(solid(kit, "star pink", PINK, 1.2))
    # flat splats on the floor
    base = Vector((S.x, S.y, 0))
    for i, (dx, dy, r, m) in enumerate(((0.35, -0.2, 0.22, red), (0.62, -0.42, 0.13, red), (0.1, -0.35, 0.1, red),
                                        (0.5, 0.05, 0.16, creams[0]), (0.78, -0.15, 0.1, creams[1]),
                                        (0.2, 0.15, 0.09, creams[2]), (-0.25, -0.15, 0.07, red))):
        splat(kit, f"splat {i}", (base.x + dx, base.y + dy), r, m, fx, z=0.004 + 0.001 * i)
    for i in range(10):
        p = (base.x + R.uniform(0, 0.9), base.y + R.uniform(-0.6, 0.2))
        splat(kit, f"splat dot {i}", p, R.uniform(0.02, 0.045), red if i % 3 else creams[0], fx, lobes=6, z=0.012)


# ---------------------------------------------------------------- gun
def build_gun(kit, root):
    t_body = tex_mat("gun body", tex_gun_body())
    t_waffle = tex_mat("waffle", tex_waffle())
    t_grip = tex_mat("grip", tex_grip())
    t_tub = tex_mat("tub", tex_pint(PINK))
    pink = solid(kit, "gun pink", PINK)
    yel = solid(kit, "gun yellow", YEL)
    choc = solid(kit, "chocolate", CHOC, 0.25, shade="#4e2812")
    berry = solid(kit, "berry cream", "#ff8fc8", 0.45)

    tbox(kit, "body", (0, 0.0, 0.0), (0.05, 0.16, 0.056), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tbox(kit, "rear cap", (0, 0.088, 0.002), (0.046, 0.022, 0.05), pink, root)
    tbox(kit, "hammer", (0, 0.1, 0.03), (0.016, 0.02, 0.022), yel, root, rot=(-30, 0, 0))
    tbox(kit, "sight", (0, -0.07, 0.033), (0.01, 0.018, 0.014), yel, root)
    tube(kit, "barrel", [(0, -0.075, 0.004), (0, -0.115, 0.004)], [0.018, 0.016], pink, root, sides=8, side=(1, 0, 0))
    tube(kit, "waffle cone", [(0, -0.105, 0.004), (0, -0.15, 0.004), (0, -0.2, 0.004)], [0.02, 0.034, 0.054],
         t_waffle, root, sides=8, side=(1, 0, 0), caps=(True, False))
    tube(kit, "cone rim", [(0, -0.196, 0.004), (0, -0.208, 0.004)], [0.058, 0.056], solid(kit, "rim", "#ffcf5a", shade="#d9862a"),
         root, sides=8, side=(1, 0, 0), caps=(False, False))
    tube(kit, "loaded scoop", [(0, -0.17, 0.004), (0, -0.196, 0.004)], [0.044, 0.05], berry, root, sides=8,
         side=(1, 0, 0), bulge=(0, 0.012))
    # pint tub magazine with a chocolate scoop and sprinkles
    tube(kit, "pint tub", [(0, 0.012, 0.026), (0, 0.012, 0.088)], [0.026, 0.032], t_tub, root, sides=8)
    tube(kit, "tub rim", [(0, 0.012, 0.086), (0, 0.012, 0.094)], [0.035, 0.035], pink, root, sides=8)
    lowball(kit, "choc scoop", (0, 0.012, 0.104), (0.032, 0.032, 0.026), choc, root)
    R = kit.rand
    spr = [solid(kit, "gun sprinkle " + c, c, 0.6) for c in (PINK, BLUE, YEL, MINT, WHITE)]
    for i in range(9):
        a = 2 * math.pi * i / 9 + R.uniform(-0.2, 0.2)
        rr = 0.012 + 0.016 * (i % 3) / 2
        z = 0.104 + 0.026 * math.sqrt(max(0.0, 1 - (rr / 0.032) ** 2)) + 0.002
        tbox(kit, f"sprinkle {i}", (0, 0, 0), (0.005, 0.014, 0.005), spr[i % 5], root,
             loc=(math.cos(a) * rr, 0.012 + math.sin(a) * rr, z), rot=(R.uniform(-20, 20), 0, R.uniform(0, 180)))
    # grip, trigger, guard
    tbox(kit, "grip", (0, 0.05, -0.065), (0.04, 0.044, 0.1), t_grip, root, rot=(16, 0, 0), taper=(1.0, 1.12))
    tbox(kit, "trigger", (0, -0.008, -0.045), (0.008, 0.01, 0.028), yel, root, rot=(-18, 0, 0))
    tube(kit, "guard", [(0, -0.04, -0.028), (0, -0.042, -0.06), (0, -0.02, -0.075), (0, 0.022, -0.074)], 0.0065, yel,
         root, sides=4, side=(1, 0, 0))


# ================================================================ round 3: more models
LAV = "#b48cff"; LAV_D = "#8f66e6"; GLASS = "#2a2f6b"; ASPH = "#3d3358"; STEEL = "#d9d4ff"

FONT = {
    'A': (".#.", "#.#", "###", "#.#", "#.#"), 'B': ("##.", "#.#", "##.", "#.#", "##."),
    'C': (".##", "#..", "#..", "#..", ".##"), 'D': ("##.", "#.#", "#.#", "#.#", "##."),
    'E': ("###", "#..", "##.", "#..", "###"), 'F': ("###", "#..", "##.", "#..", "#.."),
    'G': (".##", "#..", "#.#", "#.#", ".##"), 'H': ("#.#", "#.#", "###", "#.#", "#.#"),
    'I': ("###", ".#.", ".#.", ".#.", "###"), 'K': ("#.#", "#.#", "##.", "#.#", "#.#"),
    'L': ("#..", "#..", "#..", "#..", "###"), 'M': ("#.#", "###", "###", "#.#", "#.#"),
    'N': ("##.", "#.#", "#.#", "#.#", "#.#"), 'O': (".#.", "#.#", "#.#", "#.#", ".#."),
    'P': ("##.", "#.#", "##.", "#..", "#.."), 'R': ("##.", "#.#", "##.", "#.#", "#.#"),
    'S': (".##", "#..", ".#.", "..#", "##."), 'T': ("###", ".#.", ".#.", ".#.", ".#."),
    'U': ("#.#", "#.#", "#.#", "#.#", "###"), 'V': ("#.#", "#.#", "#.#", "#.#", ".#."),
    'W': ("#.#", "#.#", "###", "###", "#.#"), 'X': ("#.#", "#.#", ".#.", "#.#", "#.#"),
    'Y': ("#.#", "#.#", ".#.", ".#.", ".#."), 'Z': ("###", "..#", ".#.", "#..", "###"),
    '1': (".#.", "##.", ".#.", ".#.", "###"), '3': ("##.", "..#", ".#.", "..#", "##."),
    '!': (".#.", ".#.", ".#.", "...", ".#."),
}


def text(c, s, x, y, col, k=1, shadow=None):
    """3x5 pixel font. (x, y) is the top-left texel (y counts up from the bottom); k = pixel scale."""
    if shadow:
        text(c, s, x + k, y - k, shadow, k)
    for ch in s:
        for r, row in enumerate(FONT.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)
        x += 4 * k


def text_w(s, k=1):
    return (4 * len(s) - 1) * k


def disc(c, cx, cy, r, col):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r + r:
                c.set(x, y, col)


def cone_icon(c, cx, y0, h, scoop=PINK):
    """Little pixel cone: waffle triangle with a scoop on top. y0 = cone tip row."""
    for row in range(h):
        half = row // 2
        c.rect(cx - half, y0 + row, cx + half, y0 + row, "#f0a43a" if (row % 3) else "#d9862a")
    disc(c, cx, y0 + h + h // 3, h // 2, scoop)
    c.set(cx - 1, y0 + h + h // 3 + 1, WHITE)


# ---------------------------------------------------------------- shared FX helpers
def fx_frame(kit, root, name):
    """Empty under root whose axes are world aligned (cancels the root's Z rotation)."""
    rz = root.rotation_euler.z
    return kit.empty(f"{name} (world aligned)", root, (0, 0, 0), (0, 0, -math.degrees(rz))), Matrix.Rotation(rz, 3, 'Z')


def root_pos(root, ob, pt=(0, 0, 0)):
    bpy.context.view_layer.update()
    return root.matrix_world.inverted() @ (ob.matrix_world @ Vector(pt))


def fling(root, items):
    """Detach pivots (keeping their pose) onto root, then push and spin them. items: (pivot, offset, spin_deg)."""
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    mats = [inv @ ob.matrix_world for ob, _, _ in items]
    for m, (ob, off, spin) in zip(mats, items):
        ob.parent = root
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = m
        ob.location += Vector(off)
        ob.rotation_euler.rotate(Euler([math.radians(a) for a in spin]))


def fx_palette(kit):
    return dict(red=solid(kit, "blood", RED, 0.55, shade=DRED), dred=solid(kit, "blood dark", DRED, 0.45),
                creams=[solid(kit, "fx " + c, c, 0.55) for c in (PINK, WHITE, MINT, YEL)],
                goo=solid(kit, "goo", ZG, 0.9, shade="#6fd83a"),
                spr=[solid(kit, "sprinkle " + c, c, 0.7) for c in (PINK, BLUE, YEL, MINT, WHITE, PURP, ORNG)])


def fx_cube(kit, fx, name, p, s, m):
    R = kit.rand
    return tbox(kit, name, (0, 0, 0), (s, s, s), m, fx, loc=p, rot=(R.uniform(0, 90), R.uniform(0, 90), R.uniform(0, 90)))


def fx_star(kit, fx, name, p, points, ro, ri, col, emit, rot=(0, 0, 0)):
    ob = kit.link(name, star_mesh(name, points, ro, ri), fx, p, rot)
    ob.data.materials.append(solid(kit, "star " + col, col, emit))
    return ob


def burst(kit, fx, S, D, tag, scale=1.0, blood=16, cream=14, sprinkles=30, blobs=3, goo=0, reach=0.8):
    """Chunky pixel-cube burst from S along D (fx frame): blood + ice cream cubes, sprinkles, blobs."""
    R = kit.rand
    pal = fx_palette(kit)

    def spot(t, up=0.8):
        return S + D * t + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1.2, up))) * (0.06 + 0.45 * t) * scale

    for i in range(blood):
        t = R.uniform(0.05, reach)
        fx_cube(kit, fx, f"{tag} blood {i}", spot(t), R.uniform(0.03, 0.065) * scale * (1.25 - 0.5 * t / reach),
                pal['red'] if i % 4 else pal['dred'])
    for i in range(cream):
        fx_cube(kit, fx, f"{tag} cream {i}", spot(R.uniform(0.1, reach * 1.1), 1.2), R.uniform(0.035, 0.07) * scale,
                pal['creams'][i % 4])
    for i in range(goo):
        fx_cube(kit, fx, f"{tag} goo {i}", spot(R.uniform(0.1, reach), 1.2), R.uniform(0.03, 0.07) * scale, pal['goo'])
    for i in range(blobs):
        r = R.uniform(0.04, 0.065) * scale
        lowball(kit, f"{tag} blob {i}", spot(R.uniform(0.15, reach), 1.0), (r, r, r * 0.85),
                pal['creams'][i % 3] if i % 4 != 3 else pal['goo'], fx, smooth=False)
    for i in range(sprinkles):
        tbox(kit, f"{tag} sprinkle {i}", (0, 0, 0), (0.009 * scale, 0.009 * scale, 0.034 * scale), pal['spr'][i % 7], fx,
             loc=spot(R.uniform(0.05, reach * 1.2)), rot=(R.uniform(0, 180), R.uniform(0, 180), R.uniform(0, 180)))
    return pal


def trail(kit, fx, a, b, tag, n=6, size=0.05):
    pal = fx_palette(kit)
    for i in range(n):
        f = (i + 1) / (n + 1)
        p = a.lerp(b, f) + Vector((0, 0, 0.06 * math.sin(f * math.pi)))
        fx_cube(kit, fx, f"{tag} trail {i}", p, size * (1 - 0.5 * f), pal['red'] if i % 2 else pal['creams'][0])


def floor_splats(kit, fx, base, spots, tag, dots=10, spread=(0.9, 0.6)):
    pal = fx_palette(kit)
    R = kit.rand
    for i, (dx, dy, r, kind) in enumerate(spots):
        m = pal[kind] if kind in pal else pal['creams'][kind]
        splat(kit, f"{tag} splat {i}", (base.x + dx, base.y + dy), r, m, fx, z=0.004 + 0.001 * i)
    for i in range(dots):
        p = (base.x + R.uniform(-spread[0], spread[0]), base.y + R.uniform(-spread[1], spread[1]))
        splat(kit, f"{tag} dot {i}", p, R.uniform(0.02, 0.05), pal['red'] if i % 3 else pal['creams'][0], fx, lobes=6,
              z=0.014)


def ring_mesh(kit, name, r0, r1, mat, parent, loc, segs=16, z=0.0):
    bm = bmesh.new()
    inner = [bm.verts.new((math.cos(2 * math.pi * i / segs) * r0, math.sin(2 * math.pi * i / segs) * r0, z)) for i in range(segs)]
    outer = [bm.verts.new((math.cos(2 * math.pi * (i + 0.5) / segs) * r1, math.sin(2 * math.pi * (i + 0.5) / segs) * r1, z))
             for i in range(segs)]
    for i in range(segs):
        bm.faces.new((inner[i], outer[i], inner[(i + 1) % segs]))
        bm.faces.new((inner[(i + 1) % segs], outer[i], outer[(i + 1) % segs]))
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, smooth=False)


def point_light(kit, parent, name, loc, col, energy, cutoff, radius=0.3):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = hexc(col)[:3]
    ld.shadow_soft_size = radius
    ld.use_custom_distance = True
    ld.cutoff_distance = cutoff
    return kit.link(name, ld, parent, loc)


# ---------------------------------------------------------------- textures: sprinter
def tex_sprinter_head(rand):
    c = Canvas(64, 64, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 120)
    c.speckle(rand, ["#4f9f22"], 40, 50, 63)  # shaved scalp stubble
    c.rect(0, 45, 63, 49, PINK); c.rect(0, 47, 63, 47, WHITE)  # sweatband
    c.rect(16, 28, 17, 36, "#6fcf35"); c.rect(47, 28, 48, 36, "#6fcf35")
    # angry slanted brows over glowing eyes
    c.dots([(24, 41), (25, 41), (26, 40), (27, 40), (28, 39)], "#2a5a12")
    c.dots([(39, 41), (38, 41), (37, 40), (36, 40), (35, 39)], "#2a5a12")
    for x0 in (25, 35):
        c.rect(x0, 34, x0 + 3, 37, YEL)
        c.set(x0 + 1 if x0 == 25 else x0 + 2, 35, RED)
        c.set(x0 + 2 if x0 == 25 else x0 + 1, 36, WHITE)
    c.rect(22, 29, 25, 31, "#5fb52e"); c.rect(38, 29, 41, 31, "#5fb52e")  # hollow cheeks
    c.dots([(31, 31), (33, 31)], "#2a5a12")
    # screaming mouth
    c.rect(27, 15, 37, 27, "#2a0f2e")
    c.dots([(27, 15), (37, 15), (27, 27), (37, 27)], ZG)
    for x in range(28, 37):
        c.set(x, 26, "#fff1c7" if x % 2 else "#e8d27a")
        c.set(x, 16, "#fff1c7" if x % 2 == 0 else "#e8d27a")
    c.rect(30, 17, 34, 19, "#ff5d7a")
    c.rect(39, 22, 44, 22, "#2a0f2e")  # torn cheek
    c.dots([(40, 21), (42, 21), (41, 23), (43, 23)], RED)
    return c


def tex_sprinter_torso(rand):
    c = Canvas(64, 64, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 60)
    c.rect(0, 0, 63, 11, PINK); c.rect(15, 0, 17, 11, WHITE); c.rect(47, 0, 49, 11, WHITE)
    c.rect(0, 11, 63, 12, WHITE)
    for y in range(13, 51):
        for x in range(64):
            pit = y > 38 and (12 <= x <= 20 or 44 <= x <= 52)
            if not pit:
                c.set(x, y, YEL)
    for x0 in (22, 37, 54, 5):
        c.rect(x0, 51, x0 + 5, 63, YEL)
    c.rect(28, 54, 36, 63, ZG)
    c.speckle(rand, ["#f2cf2e", "#fff07a"], 70, 13, 50)
    # race bib "13"
    c.rect(24, 23, 39, 39, WHITE)
    text(c, "13", 25, 36, BLUE, 2)
    c.dots([(24, 39), (39, 39), (24, 23), (39, 23)], "#9a9ab8")
    # rips and a claw slash
    for (hx, hy, r) in ((8, 30, 3), (58, 20, 2), (32, 17, 2)):
        disc(c, hx, hy, r + 1, "#c9a81a"); disc(c, hx, hy, r, ZG)
    for y in (28, 30, 32):
        c.rect(6, y, 10, y, WHITE)
    for k in range(3):
        for i in range(8):
            c.set(42 + k * 2 + i // 3, 22 + i, RED)
    return c


def tex_sprinter_arm(rand):
    c = Canvas(16, 32, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 50)
    c.rect(0, 0, 15, 1, DRED)
    for x in (3, 11):
        c.rect(x, 4, x, 14, "#5fb52e"); c.rect(x + 1, 18, x + 1, 29, "#5fb52e")
    c.rect(6, 9, 8, 11, RED); c.set(7, 10, DRED)
    c.rect(0, 24, 15, 25, PINK)  # wristband
    return c


def tex_claw_hand():
    c = Canvas(16, 16, ZG)
    for x in (2, 6, 10, 14):
        c.rect(x, 5, x, 11, "#5fb52e")
    c.rect(0, 11, 15, 15, YEL)
    for x in range(0, 16, 4):
        c.rect(x, 11, x, 15, "#d9b21a")
    return c


def tex_sprinter_leg(rand):
    c = Canvas(16, 32, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 50)
    c.rect(0, 0, 15, 7, PINK); c.rect(3, 0, 4, 7, WHITE); c.rect(11, 0, 12, 7, WHITE)
    for x in range(16):
        c.rect(x, 8, x, 8 + rand.choice((0, 0, 1, 2)), PINK)
    c.rect(6, 15, 9, 17, RED); c.dots([(7, 16)], DRED)
    c.rect(0, 27, 15, 31, WHITE); c.rect(0, 29, 15, 29, PINK)
    return c


def tex_runner_shoe():
    c = Canvas(16, 16, ORNG)
    c.rect(0, 0, 3, 15, WHITE); c.rect(12, 0, 15, 15, WHITE)
    for i in range(6):
        c.set(4 + i, 4 + i, YEL); c.set(11 - i, 4 + i, YEL)
    for y in (6, 8, 10):
        c.rect(7, y, 8, y, WHITE)
    c.rect(4, 13, 11, 15, "#ffb070")
    return c


# ---------------------------------------------------------------- sprinter
def sprinter_arm(kit, parent, name, loc, d, elbow, wrist, t_arm, t_hand):
    piv = kit.empty(f"arm {name}", parent, loc)
    aim(piv, d)
    tube(kit, f"upper arm {name}", [(0, 0, 0.025), (0, 0, -0.13), (0, 0, -0.26)], [0.046, 0.04, 0.033], t_arm, piv,
         sides=6, front=(0, 1, 0), v=(0.0, 0.5), bulge=(0.015, 0.0))
    fore = kit.empty(f"forearm {name}", piv, (0, 0, -0.26), elbow)
    tube(kit, f"forearm {name}", [(0, 0, 0.015), (0, 0, -0.12), (0, 0, -0.25)], [0.034, 0.033, 0.026], t_arm, fore,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    hand = kit.empty(f"hand {name}", fore, (0, 0, -0.25), wrist)
    tube(kit, f"hand {name}", [(0, 0, 0.01), (0, 0, -0.06), (0, 0, -0.15)], [(0.036, 0.02), (0.042, 0.02), (0.03, 0.008)],
         t_hand, hand, sides=6, front=(0, 1, 0), bulge=(0, 0.02))
    return piv


def sprinter_leg(kit, parent, name, loc, thigh, knee, foot_rot, t_leg, t_shoe):
    piv = kit.empty(f"leg {name}", parent, loc, thigh)
    tube(kit, f"thigh {name}", [(0, 0, 0.04), (0, 0, -0.2), (0, 0, -0.43)], [(0.064, 0.07), 0.055, 0.044], t_leg, piv,
         sides=6, front=(0, 1, 0), v=(0.0, 0.5))
    shin = kit.empty(f"shin {name}", piv, (0, 0, -0.43), knee)
    tube(kit, f"shin {name}", [(0, 0, 0.02), (0, -0.012, -0.2), (0, 0, -0.41)], [0.045, 0.04, 0.032], t_leg, shin,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    foot = kit.empty(f"foot {name}", shin, (0, 0, -0.43), (foot_rot, 0, 0))
    tube(kit, f"shoe {name}", [(0, 0.045, 0.0), (0, -0.04, 0.004), (0, -0.14, -0.012)],
         [(0.042, 0.04), (0.046, 0.044), (0.036, 0.026)], t_shoe, foot, sides=6, front=(0, 0, 1), bulge=(0.012, 0.03))
    ends = [kit.empty(f"{name} heel", foot, (0, 0.06, -0.04)), kit.empty(f"{name} toe", foot, (0, -0.17, -0.03))]
    return piv, ends


SPRINTER_POSES = {
    'run': dict(spine=(40, 0, -8), head=(-42, 0, 10), hips=(0, 0, 6),
                armR=((0.15, -0.8, -0.5), (80, 0, 0), (10, 0, 0)), armL=((-0.1, 0.75, -0.65), (70, 0, 0), (-10, 0, 0)),
                legL=((-62, 0, 3), (82, 0, 0), -20), legR=((30, 0, -3), (52, 0, 0), -24)),
    'climb': dict(spine=(10, 0, 0), head=(-42, 0, 8), hips=(0, 0, 0),
                  armR=((-0.18, -0.4, 1), (12, 0, 0), (-55, 0, 0)), armL=((0.16, -0.3, 1), (20, 0, 0), (-60, 0, 0)),
                  legL=((-82, 0, 8), (104, 0, 0), -15), legR=((4, 0, -5), (46, 0, 0), -30)),
}


def build_sprinter(kit, root, hit=False, climb=False):
    t_head = tex_mat("sprinter head", tex_sprinter_head(kit.rand))
    t_torso = tex_mat("sprinter torso", tex_sprinter_torso(kit.rand))
    t_arm = tex_mat("sprinter arm", tex_sprinter_arm(kit.rand))
    t_hand = tex_mat("claw hand", tex_claw_hand())
    t_leg = tex_mat("sprinter leg", tex_sprinter_leg(kit.rand))
    t_shoe = tex_mat("runner shoe", tex_runner_shoe())
    mohawk = solid(kit, "mohawk", PURP, 0.5, shade="#6a3fd6")
    P = SPRINTER_POSES['climb' if climb else 'run']

    hips = kit.empty("hips", root, (0, 0, 0.92), P['hips'])
    spine = kit.empty("spine", hips, (0, 0, 0), P['spine'])
    tube(kit, "torso", [(0, 0, -0.06), (0, 0, 0.06), (0, 0.01, 0.2), (0, 0.035, 0.36), (0, 0.045, 0.49), (0, 0.04, 0.56)],
         [(0.125, 0.085), (0.12, 0.082), (0.105, 0.078), (0.13, 0.088), (0.158, 0.094), (0.07, 0.058)], t_torso, spine)
    head = kit.empty("head", spine, (0, 0.035, 0.545), P['head'])
    tube(kit, "head", [(0, 0, 0), (0, -0.015, 0.05), (0, -0.03, 0.08), (0, -0.035, 0.13), (0, -0.03, 0.19),
                       (0, -0.02, 0.25), (0, -0.01, 0.29), (0, -0.005, 0.31)],
         [0.04, 0.045, (0.07, 0.082), (0.086, 0.098), (0.09, 0.102), (0.084, 0.094), (0.056, 0.064), (0.022, 0.028)],
         t_head, head, bulge=(0, 0.008))
    for i, (y, h) in enumerate(((-0.07, 0.07), (-0.02, 0.1), (0.03, 0.11), (0.08, 0.09))):
        z = 0.3 - abs(y + 0.01) * 0.6
        tube(kit, f"mohawk {i}", [(0, y, z - 0.03), (0, y + 0.06, z + h)], [(0.012, 0.03), 0.003], mohawk, head,
             sides=4, caps=(True, True))
    armR = sprinter_arm(kit, spine, "R", (-0.135, 0.045, 0.46), *P['armR'], t_arm, t_hand)
    armL = sprinter_arm(kit, spine, "L", (0.135, 0.045, 0.46), *P['armL'], t_arm, t_hand)
    legL, endsL = sprinter_leg(kit, hips, "L", (0.085, 0, 0), *P['legL'], t_leg, t_shoe)
    legR, endsR = sprinter_leg(kit, hips, "R", (-0.085, 0, 0), *P['legR'], t_leg, t_shoe)

    if not climb:
        low = min(root_pos(root, e).z for e in endsL + endsR)
        hips.location.z -= low - 0.012
    if hit:
        sprinter_hit_fx(kit, root, hips, spine, head, armR, armL, legL)


def sprinter_hit_fx(kit, root, hips, spine, head, armR, armL, legL):
    """One hit and it comes apart: head, arms, torso and a leg fly backward; the right leg stays standing."""
    fx, to_fx = fx_frame(kit, root, "sprinter fx")
    C = to_fx @ root_pos(root, spine, (0, 0.03, 0.28))
    parts = [(head, (0.2, 0.75, 0.7), (130, 40, 200)), (armR, (-0.62, 0.42, 0.35), (10, 85, -70)),
             (armL, (0.66, 0.3, 0.42), (50, -95, 30)), (spine, (0.06, 0.55, 0.32), (-55, 25, 15)),
             (legL, (0.5, 0.35, 0.42), (80, 35, 10))]
    old = {id(ob): to_fx @ root_pos(root, ob) for ob, _, _ in parts}
    fling(root, parts)
    pal = fx_palette(kit)
    stump = to_fx @ root_pos(root, hips, (-0.085, 0, 0.02))
    fx_cube(kit, fx, "leg stump", stump + Vector((0, 0, 0.03)), 0.07, pal['red'])
    D = (to_fx @ Vector((0, 0.7, 0.55))).normalized()
    burst(kit, fx, C, D, "sprinter", scale=1.1, blood=18, cream=14, sprinkles=34, blobs=4)
    for ob, off, _ in parts:
        a = old[id(ob)]
        trail(kit, fx, a, a + to_fx @ Vector(off), f"sprinter {ob.name}", n=4, size=0.045)
    fx_star(kit, fx, "sprinter star", C + Vector((0, -0.25, 0.05)), 7, 0.24, 0.1, YEL, 1.4, (0, 0, 0))
    fx_star(kit, fx, "sprinter star core", C + Vector((0, -0.28, 0.05)), 6, 0.12, 0.05, WHITE, 1.6, (0, 18, 0))
    base = Vector((C.x, C.y, 0))
    floor_splats(kit, fx, base, [(0.05, 0.25, 0.2, 'red'), (0.35, 0.55, 0.12, 'red'), (-0.3, 0.4, 0.1, 0),
                                 (0.2, -0.15, 0.09, 1), (-0.15, 0.75, 0.08, 'red')], "sprinter", dots=8)


# ---------------------------------------------------------------- textures: bloater
def tex_bloater_head(rand):
    c = Canvas(64, 64, LAV)
    c.speckle(rand, [LAV_D, "#c7a6ff"], 150)
    c.rect(16, 28, 17, 36, LAV_D); c.rect(47, 28, 48, 36, LAV_D)
    # right eye (-X): tiny glowing yellow; left eye (+X): swollen shut
    c.rect(22, 32, 29, 39, "#3a1f73"); c.rect(23, 33, 28, 38, YEL); c.rect(25, 35, 26, 36, RED); c.set(27, 37, WHITE)
    c.rect(34, 31, 43, 40, "#d4bcff"); c.rect(35, 35, 42, 36, "#3a1f73"); c.rect(36, 33, 41, 33, LAV_D)
    c.rect(22, 41, 29, 42, "#4a2a8a"); c.rect(34, 42, 43, 42, "#4a2a8a")
    c.dots([(30, 29), (31, 28), (33, 28), (34, 29)], "#3a1f73")
    # slack mouth with the tongue hanging out, drool, double chin
    c.rect(24, 17, 40, 25, "#2a0f2e")
    c.rect(25, 24, 39, 24, "#fff1c7"); c.rect(28, 24, 28, 24, "#2a0f2e"); c.rect(35, 24, 35, 24, "#2a0f2e")
    c.rect(28, 10, 35, 21, "#ff6f9a"); c.rect(31, 11, 32, 20, "#e0457a")
    c.rect(39, 9, 40, 18, ZG); c.rect(39, 8, 40, 8, "#c8ff9e")
    c.rect(22, 9, 42, 9, LAV_D)
    for x, y in ((20, 44), (44, 40), (40, 48), (22, 27)):
        disc(c, x, y, 1, ZG); c.set(x, y, YEL)
    for x in range(0, 64, 5):
        c.rect(x, 54, x, 58, "#4a2a8a")
    return c


def tex_bloater_body(rand):
    """Body loft z 0.5..1.72: blue shorts, bare swollen belly with glowing veins, a too-small orange tank top."""
    c = Canvas(64, 64, LAV)
    c.speckle(rand, [LAV_D, "#c7a6ff"], 220)
    c.rect(0, 0, 63, 11, BLUE); c.rect(0, 11, 63, 12, YEL); c.rect(30, 11, 33, 12, PINK)
    c.speckle(rand, ["#2470dd", "#5aa0ff"], 40, 0, 10)
    # stretch marks
    for x0 in (8, 14, 50, 56, 22, 42):
        for i in range(5):
            c.set(x0 + i // 2, 18 + i + (x0 % 3), "#d4bcff")
    # navel and glowing veins radiating from it
    c.rect(31, 25, 33, 27, "#3a1f73")
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1), (2, 0), (-2, 0)):
        x, y = 32, 26
        for i in range(9):
            x += dx + rand.choice((-1, 0, 0, 1)); y += dy + rand.choice((-1, 0, 1)) * (dy == 0)
            c.set(x, y, ZG if i % 3 else "#d8ff9e")
    # tank top riding up, ragged hem
    for x in range(64):
        c.rect(x, 39 + rand.choice((0, 1, 2, 3)), x, 63, ORNG)
    c.speckle(rand, ["#e8752b", "#ffa060"], 60, 42, 60)
    c.rect(27, 56, 37, 63, LAV)  # neck scoop
    for (hx, hy) in ((12, 50), (52, 47), (40, 58)):
        disc(c, hx, hy, 2, LAV); c.set(hx, hy, ZG)
    # strawberry ice cream drips down the chest
    for dx, ln in ((24, 7), (27, 11), (30, 5), (35, 9), (38, 6)):
        c.rect(dx, 52 - ln, dx + 1, 54, PINK)
        c.set(dx, 51 - ln, "#ff8fc8")
    c.rect(23, 53, 39, 55, PINK); c.dots([(26, 54), (33, 54), (36, 55)], WHITE)
    return c


def tex_bloater_limb(rand, shorts):
    c = Canvas(16, 32, LAV)
    c.speckle(rand, [LAV_D, "#c7a6ff"], 60)
    c.rect(0, 0, 15, 1, DRED)
    if shorts:
        c.rect(0, 2, 15, 9, BLUE)
        for x in range(16):
            c.set(x, 10 + rand.choice((0, 0, 1)), BLUE)
    for y in (14, 22, 27):
        x = rand.randrange(16)
        disc(c, x, y, 1, ZG); c.set(x, y, YEL)
    c.rect(4, 17, 5, 25, "#7a52d8")
    return c


def tex_fat_hand():
    c = Canvas(16, 16, LAV)
    for x in (3, 7, 11, 15):
        c.rect(x, 7, x, 15, LAV_D)
    c.rect(0, 14, 15, 15, "#d4bcff")
    return c


# ---------------------------------------------------------------- bloater
BLOAT_RINGS = [(0.5, 0.36, 0.3, 0.0), (0.68, 0.52, 0.48, -0.04), (0.92, 0.6, 0.6, -0.12), (1.18, 0.56, 0.52, -0.08),
               (1.42, 0.5, 0.42, 0.0), (1.6, 0.38, 0.3, 0.03), (1.72, 0.17, 0.15, 0.04)]


def bloat_point(z, a, push=0.0):
    """Point on the bloater belly surface at height z and angle a (0 = front, +pi/2 = +X)."""
    for (z0, rx0, ry0, c0), (z1, rx1, ry1, c1) in zip(BLOAT_RINGS, BLOAT_RINGS[1:]):
        if z0 <= z <= z1:
            f = (z - z0) / (z1 - z0)
            rx, ry, cy = rx0 + (rx1 - rx0) * f, ry0 + (ry1 - ry0) * f, c0 + (c1 - c0) * f
            return Vector((math.sin(a) * (rx + push), cy - math.cos(a) * (ry + push), z))
    raise ValueError(z)


def bloat_arm(kit, parent, name, loc, d, elbow, t_arm, t_hand, pus):
    piv = kit.empty(f"arm {name}", parent, loc)
    aim(piv, d)
    tube(kit, f"upper arm {name}", [(0, 0, 0.06), (0, 0, -0.16), (0, 0, -0.34)], [0.135, 0.125, 0.105], t_arm, piv,
         sides=8, front=(0, 1, 0), v=(0.0, 0.5), bulge=(0.03, 0))
    fore = kit.empty(f"forearm {name}", piv, (0, 0, -0.34), elbow)
    tube(kit, f"forearm {name}", [(0, 0, 0.03), (0, 0, -0.15), (0, 0, -0.3)], [0.108, 0.104, 0.084], t_arm, fore,
         sides=8, front=(0, 1, 0), v=(0.5, 1.0))
    tube(kit, f"hand {name}", [(0, 0, -0.29), (0, 0, -0.36), (0, 0, -0.45)], [(0.1, 0.06), (0.11, 0.064), (0.08, 0.05)],
         t_hand, fore, sides=6, front=(0, 1, 0), bulge=(0, 0.03))
    lowball(kit, f"arm pustule {name}", (0.0, -0.11, -0.12), (0.045, 0.04, 0.045), pus, piv)
    return piv


def bloat_leg(kit, parent, name, loc, thigh, knee, t_leg, foot_mat):
    piv = kit.empty(f"leg {name}", parent, loc, thigh)
    tube(kit, f"thigh {name}", [(0, 0, 0.05), (0, 0, -0.15), (0, 0, -0.3)], [(0.17, 0.18), 0.155, 0.125], t_leg, piv,
         sides=8, front=(0, 1, 0), v=(0.0, 0.5))
    shin = kit.empty(f"shin {name}", piv, (0, 0, -0.3), knee)
    tube(kit, f"shin {name}", [(0, 0, 0.03), (0, 0, -0.14), (0, 0, -0.27)], [0.125, 0.118, 0.105], t_leg, shin,
         sides=8, front=(0, 1, 0), v=(0.5, 1.0))
    foot = kit.empty(f"foot {name}", shin, (0, 0, -0.29), (-(thigh[0] + knee[0]), 0, 0))
    tube(kit, f"foot {name}", [(0, 0.07, 0.0), (0, -0.05, -0.005), (0, -0.19, -0.02)],
         [(0.1, 0.06), (0.11, 0.058), (0.095, 0.034)], foot_mat, foot, sides=6, front=(0, 0, 1), bulge=(0.02, 0.03))
    return piv, kit.empty(f"{name} sole", foot, (0, 0, -0.055))


def build_bloater(kit, root, pop=False):
    t_head = tex_mat("bloater head", tex_bloater_head(kit.rand))
    t_body = tex_mat("bloater body", tex_bloater_body(kit.rand))
    t_arm = tex_mat("bloater arm", tex_bloater_limb(kit.rand, False))
    t_leg = tex_mat("bloater leg", tex_bloater_limb(kit.rand, True))
    t_hand = tex_mat("fat hand", tex_fat_hand())
    pus = solid(kit, "pustule", ZG, 2.6, shade="#d8ff9e")
    pus_core = solid(kit, "pustule core", YEL, 3.0)
    foot = solid(kit, "bloater foot", LAV, shade=LAV_D)

    hips = kit.empty("hips", root, (0, 0, 0.66))
    legL, soleL = bloat_leg(kit, hips, "L", (0.24, 0, 0), (-6, -7, 0), (8, 0, 0), t_leg, foot)
    legR, soleR = bloat_leg(kit, hips, "R", (-0.24, 0.02, 0), (5, 8, 0), (6, 0, 0), t_leg, foot)
    low = min(root_pos(root, s).z for s in (soleL, soleR))
    hips.location.z -= low
    torso = kit.empty("torso", hips, (0, 0, -0.66))   # torso space == root space before the hips drop
    if not pop:
        tube(kit, "body", [(0, cy, z) for z, rx, ry, cy in BLOAT_RINGS], [(rx, ry) for z, rx, ry, cy in BLOAT_RINGS],
             t_body, torso, sides=10, bulge=(0.04, 0.02))
        R = kit.rand
        spots = [(0.85, 0.3), (0.95, -0.5), (1.05, 0.1), (0.75, -0.2), (1.2, 0.9), (1.25, -1.0), (0.9, 1.4),
                 (1.0, -1.5), (1.35, 0.4), (0.7, 0.8), (1.1, 2.4), (0.9, -2.6), (1.3, 3.1), (1.5, -0.7), (0.62, -0.9),
                 (1.45, 1.6)]
        for i, (z, a) in enumerate(spots):
            r = R.uniform(0.035, 0.07)
            p = bloat_point(z, a, -r * 0.3)
            lowball(kit, f"pustule {i}", p, (r, r, r), pus, torso)
            lowball(kit, f"pustule core {i}", bloat_point(z, a, r * 0.55), (r * 0.4, r * 0.4, r * 0.4), pus_core, torso)
    head = kit.empty("head", torso, (0, 0.0, 1.7), (4, 0, 5), (1.15, 1.15, 1.15))
    tube(kit, "head", [(0, 0, 0), (0, -0.03, 0.06), (0, -0.045, 0.13), (0, -0.04, 0.2), (0, -0.03, 0.25),
                       (0, -0.025, 0.285)],
         [(0.15, 0.13), (0.165, 0.15), (0.158, 0.152), (0.14, 0.135), (0.09, 0.09), (0.03, 0.03)], t_head, head,
         bulge=(0, 0.006))
    armR = bloat_arm(kit, torso, "R", (-0.37, 0.0, 1.37), (-0.36, -0.18, -1), (14, 0, 0), t_arm, t_hand, pus)
    armL = bloat_arm(kit, torso, "L", (0.37, 0.0, 1.37), (0.34, -0.08, -1), (20, 0, 0), t_arm, t_hand, pus)
    if pop:
        bloater_pop_fx(kit, root, torso, head, armR, armL, t_body, pus)


def shell_chunk(kit, name, parent, z0, z1, a0, a1, outer, inner):
    """Curved piece of the belly skin (2x2 quads) with goo on the inside, origin at its center."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    zs, As = (z0, (z0 + z1) / 2, z1), (a0, (a0 + a1) / 2, a1)
    P = [[bloat_point(z, a) for a in As] for z in zs]
    ctr = sum((p for row in P for p in row), Vector()) / 9
    layers = []
    for push in (0.0, -0.04):
        layers.append([[bm.verts.new(bloat_point(z, a, push) - ctr) for a in As] for z in zs])
    for li, L in enumerate(layers):
        for j in range(2):
            for i in range(2):
                vs = (L[j][i], L[j][i + 1], L[j + 1][i + 1], L[j + 1][i])
                fc = bm.faces.new(vs if li == 0 else vs[::-1])
                fc.material_index = li
                for lp, (jj, ii) in zip(fc.loops, ((j, i), (j, i + 1), (j + 1, i + 1), (j + 1, i)) if li == 0 else
                                        ((j + 1, i), (j + 1, i + 1), (j, i + 1), (j, i))):
                    u = (As[ii] / (2 * math.pi) + 0.5) % 1.0
                    lp[uvl].uv = (min(0.995, max(0.005, u)), (zs[jj] - 0.5) / 1.22)
    ob = kit.mesh_from_bmesh(name, bm, [outer, inner], parent, smooth=True)
    return ob, ctr


def bloater_pop_fx(kit, root, torso, head, armR, armL, t_body, pus):
    """The pop: belly bursts into skin chunks, head and arms launch, and a huge candy-goo blast."""
    R = kit.rand
    pal = fx_palette(kit)
    # what is left standing: a torn bowl of belly on the legs, full of goo
    bowl = tube(kit, "belly bowl", [(0, cy, z) for z, rx, ry, cy in BLOAT_RINGS[:3]],
                [(rx, ry) for z, rx, ry, cy in BLOAT_RINGS[:3]], t_body, torso, sides=10, caps=(True, False))
    vs = bowl.data.vertices
    for k in range(10):
        vs[20 + k].co.z += 0.09 if k % 2 else -0.05
    tube(kit, "bowl goo", [(0, -0.1, 0.78), (0, -0.1, 0.86)], [(0.5, 0.5), (0.46, 0.46)], pal['creams'][0], torso,
         sides=10, bulge=(0, 0.06))
    for i in range(5):
        a = 2 * math.pi * i / 5
        lowball(kit, f"bowl goo blob {i}", (math.sin(a) * 0.32, -0.1 - math.cos(a) * 0.3, 0.92), (0.11, 0.11, 0.08),
                pal['creams'][i % 4] if i != 2 else pal['goo'], torso, smooth=False)

    fx, to_fx = fx_frame(kit, root, "pop fx")
    C = to_fx @ root_pos(root, torso, (0, -0.05, 1.12))
    fling(root, [(head, (0.25, 0.3, 1.05), (160, 60, 220)), (armR, (-1.05, 0.25, 0.55), (30, 120, -40)),
                 (armL, (1.05, 0.15, 0.7), (60, -110, 40))])
    # belly skin chunks flying out in a ring
    for i in range(8):
        a0 = 2 * math.pi * i / 8 + R.uniform(-0.1, 0.1)
        z0 = R.choice((0.95, 1.1, 1.25))
        ob, ctr = shell_chunk(kit, f"belly chunk {i}", fx, z0, z0 + 0.32, a0, a0 + 0.62, t_body, pal['creams'][0])
        out = Vector((ctr.x, ctr.y, 0)).normalized()
        ob.location = C + to_fx @ (out * R.uniform(1.0, 1.6) + Vector((0, 0, R.uniform(-0.3, 0.9))))
        ob.rotation_euler = (R.uniform(-90, 90) * 0.0174, R.uniform(-90, 90) * 0.0174, R.uniform(0, 6.28))
        lowball(kit, f"chunk pustule {i}", ob.location + Vector((0, 0, 0.06)), (0.04, 0.04, 0.04), pus, fx)

    # flash: layered stars behind the body, facing the camera
    back = Vector((0, 0.45, 0))
    fx_star(kit, fx, "pop star pink", C + back * 1.4 + Vector((0, 0, 0.1)), 12, 1.55, 0.75, PINK, 1.5, (0, 8, 0))
    fx_star(kit, fx, "pop star yellow", C + back * 1.2 + Vector((0, 0, 0.1)), 10, 1.15, 0.55, YEL, 1.8, (0, -6, 0))
    fx_star(kit, fx, "pop star white", C + back + Vector((0, 0, 0.1)), 8, 0.62, 0.32, WHITE, 2.2, (0, 14, 0))
    # pixel smoke puffs ringing the blast
    puffs = [solid(kit, "puff " + c, c, 0.5) for c in ("#e3cfff", "#ffd0ea", "#cff7ff")]
    for i in range(9):
        a = math.pi * (i / 8) + R.uniform(-0.1, 0.1)
        r = R.uniform(0.15, 0.24)
        p = C + Vector((math.cos(a) * R.uniform(1.2, 1.6), 0.6 + math.sin(a) * 0.4, math.sin(a) * 0.9 + R.uniform(-0.2, 0.2)))
        lowball(kit, f"puff {i}", p, (r, r, r * 0.9), puffs[i % 3], fx, smooth=False)
    # the big burst: cubes, goo, sprinkles, blobs
    for i, D in enumerate((Vector((1, 0.1, 0.7)), Vector((-1, 0.1, 0.7)), Vector((0, 0.3, 1)), Vector((0.6, 0.6, 0.3)),
                           Vector((-0.6, 0.6, 0.3)))):
        burst(kit, fx, C + Vector((0, 0, 0.25)), D.normalized(), f"pop {i}", scale=1.4, blood=5, cream=5, sprinkles=14,
              blobs=2, goo=4, reach=1.6)
    # shockwave rings and floor splats
    ring_mesh(kit, "shock ring", 1.55, 1.75, solid(kit, "ring pink", PINK, 1.6), fx, Vector((C.x, C.y, 0.02)), 18)
    ring_mesh(kit, "shock ring 2", 2.25, 2.33, solid(kit, "ring mint", MINT, 1.6), fx, Vector((C.x, C.y, 0.025)), 22)
    base = Vector((C.x, C.y, 0))
    floor_splats(kit, fx, base, [(0, 0.1, 1.15, 0), (0.9, -0.5, 0.35, 'red'), (-1.0, -0.4, 0.3, 'goo'),
                                 (0.4, -1.1, 0.25, 'red'), (-0.5, -1.2, 0.22, 1), (1.4, 0.3, 0.2, 'goo'),
                                 (-1.5, 0.5, 0.25, 'red'), (0.0, -1.6, 0.15, 2)], "pop", dots=24, spread=(2.0, 1.6))
    point_light(kit, fx, "pop flash", C + Vector((0, 0.2, 0.6)), "#ffd36b", 220, 6.0, 0.6)


# ---------------------------------------------------------------- textures: truck and road
def frosting(c, rand, y0, y1):
    """Mint frosting band from row y0 to the top with rounded drips hanging down to y1."""
    c.rect(0, y0, c.w - 1, c.h - 1, MINT)
    x = 0
    while x < c.w:
        w = rand.choice((2, 3, 3, 4))
        ln = rand.randint(0, y0 - y1)
        c.rect(x, y0 - ln, x + w - 1, y0, MINT)
        c.set(x, y0 - ln, "#22c79c")
        x += w + rand.choice((1, 2, 3))
    c.rect(0, c.h - 2, c.w - 1, c.h - 1, "#8ff9de")
    for _ in range(c.w // 3):
        c.set(rand.randrange(c.w), rand.randint(y0 + 1, c.h - 3), rand.choice((PINK, YEL, BLUE, WHITE, PURP)))


def tex_truck_side(rand):
    """128x128 atlas: top half = +X side with the serving window, bottom half = -X side."""
    c = Canvas(128, 128, WHITE)
    for half in (0, 64):
        sub = Canvas(128, 64, WHITE)
        sub.rect(0, 0, 127, 9, PINK); sub.rect(0, 10, 127, 10, BLUE)
        sub.speckle(rand, ["#f4ebe2"], 60, 11, 52)
        frosting(sub, rand, 56, 47)
        if half == 64:
            sub.rect(12, 20, 64, 48, "#ffd0e6")
            sub.rect(14, 22, 62, 46, INK)
            sub.rect(16, 24, 30, 32, "#4a3f7a"); sub.rect(18, 33, 22, 40, "#c7c0e8"); sub.rect(19, 41, 21, 42, PINK)
            for x in range(34, 61, 6):
                cone_icon(sub, x, 28, 6, (PINK, MINT, YEL, "#ff8fc8", WHITE)[(x // 6) % 5])
            text(sub, "ICE", 72, 47, PINK, 3, shadow=BLUE)
            text(sub, "CREAM", 70, 29, BLUE, 2, shadow=PINK)
            cone_icon(sub, 116, 13, 10, PINK)
        else:
            text(sub, "ICE CREAM", 4, 47, PINK, 3, shadow=BLUE)
            text(sub, "SOFT SERVE", 8, 26, BLUE, 2)
            cone_icon(sub, 117, 15, 12, MINT)
        for y in range(64):
            for x in range(128):
                c.p[(y + half) * 128 + x] = sub.p[y * 128 + x]
    return c


def tex_cab(rand):
    c = Canvas(64, 64, WHITE)
    c.rect(0, 0, 63, 26, PINK); c.rect(0, 27, 63, 27, BLUE)
    c.rect(20, 34, 60, 58, GLASS)
    for i in range(10):
        c.set(26 + i, 40 + i, "#6f8cff"); c.set(27 + i, 40 + i, "#6f8cff")
    c.rect(20, 58, 60, 58, "#c7c0e8")
    c.rect(17, 3, 17, 60, INK); c.rect(22, 30, 25, 30, YEL)
    c.speckle(rand, ["#f4ebe2"], 30, 28, 63)
    frosting(c, rand, 60, 58)
    return c


def tex_grille():
    c = Canvas(64, 32, PINK)
    c.rect(0, 0, 63, 5, "#e6e0ff"); c.rect(0, 2, 63, 2, "#9a94c8")
    c.rect(18, 9, 45, 24, INK)
    for y in range(10, 24, 3):
        c.rect(19, y, 44, y, "#ff8fc8")
    for cx in (9, 54):
        disc(c, cx, 17, 5, "#e6e0ff"); disc(c, cx, 17, 4, "#fff6b0"); disc(c, cx, 17, 2, WHITE)
    c.rect(28, 26, 35, 29, YEL)
    return c


def tex_hazard():
    c = Canvas(32, 8, YEL)
    for y in range(8):
        for x in range(32):
            if ((x + y) // 4) % 2:
                c.set(x, y, INK)
    return c


def tex_asphalt(rand):
    c = Canvas(32, 32, ASPH)
    c.speckle(rand, ["#4a4068", "#2f2745", "#55497a"], 220)
    x, y = 4, 30
    for _ in range(14):
        c.set(x, y, "#231c36"); x += rand.choice((0, 1)); y -= 1
    return c


def tex_dirt(rand):
    c = Canvas(32, 32, "#6b4a5a")
    c.speckle(rand, ["#7d5a6a", "#5a3d4c", "#8a6575"], 200)
    for _ in range(14):
        x, y = rand.randrange(32), rand.randrange(32)
        c.dots([(x, y), (x + 1, y + 1), (x - 1, y + 1)], "#4fd68a")
    return c


def tex_swirl():
    c = Canvas(32, 16, PINK)
    for y in range(16):
        for x in range(32):
            if (x + 2 * y) % 8 < 3:
                c.set(x, y, WHITE)
    return c


def tex_awning():
    c = Canvas(32, 8, WHITE)
    for x in range(32):
        if (x // 4) % 2:
            c.rect(x, 0, x, 7, PINK)
    return c


def tex_sign():
    c = Canvas(32, 24, YEL)
    c.rect(0, 0, 31, 0, INK); c.rect(0, 23, 31, 23, INK); c.rect(0, 0, 0, 23, INK); c.rect(31, 0, 31, 23, INK)
    text(c, "ZOMBIES", 3, 20, INK)
    text(c, "AHEAD", 7, 13, INK)
    c.rect(14, 2, 17, 6, ZG); c.dots([(13, 7), (15, 7), (17, 7), (18, 6)], ZG)
    return c


def tex_car(rand):
    c = Canvas(64, 32, "#4fb5c8")
    c.speckle(rand, ["#3f9fb2", "#6cc8d8"], 80)
    for _ in range(9):
        disc(c, rand.randrange(64), rand.randrange(4, 28), rand.choice((1, 2)), "#c96f3a")
    c.rect(0, 0, 63, 3, "#2f6f80"); c.rect(0, 13, 63, 13, "#e6e0ff")
    return c


def tex_car_glass(rand):
    c = Canvas(16, 16, GLASS)
    for _ in range(4):
        x, y = rand.randrange(16), rand.randrange(16)
        for i in range(6):
            c.set(x, y, "#c7d4ff"); x += rand.choice((-1, 0, 1)); y += rand.choice((-1, 1))
    return c


# ---------------------------------------------------------------- truck
def wheel(kit, name, parent, loc, side, tire, hub, cap):
    piv = kit.empty(name, parent, loc)
    tube(kit, name + " tire", [(-0.15, 0, 0), (0.15, 0, 0)], 0.45, tire, piv, sides=10, front=(0, 0, 1))
    tube(kit, name + " hub", [(side * 0.14, 0, 0), (side * 0.165, 0, 0)], 0.25, hub, piv, sides=10, front=(0, 0, 1))
    tube(kit, name + " cap", [(side * 0.16, 0, 0), (side * 0.2, 0, 0)], [0.09, 0.05], cap, piv, sides=6, front=(0, 0, 1))
    return piv


def build_minigun(kit, parent):
    """Soft Serve Minigun on its turret ring: six barrels, mint housing, pint hopper on top."""
    t_body = tex_mat("minigun body", tex_gun_body())
    t_hop = tex_mat("hopper", tex_pint(MINT))
    steel, pink, yel = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "gun pink", PINK), solid(kit, "gun yellow", YEL)
    tube(kit, "turret ring", [(0, 0, 0.0), (0, 0, 0.1), (0, 0, 0.13)], [0.42, 0.4, 0.34], solid(kit, "turret blue", BLUE),
         parent, sides=10)
    tube(kit, "turret post", [(0, 0, 0.12), (0, 0, 0.22)], 0.08, steel, parent, sides=6)
    tbox(kit, "yoke", (0, 0, 0.23), (0.36, 0.14, 0.05), pink, parent)
    for sx in (1, -1):
        tbox(kit, f"yoke arm {sx}", (sx * 0.16, 0, 0.29), (0.04, 0.16, 0.14), pink, parent)
    gun = kit.empty("minigun", parent, (0, 0, 0.3), (-3, 0, 0))
    tbox(kit, "housing", (0, 0.06, 0), (0.25, 0.42, 0.22), t_body, gun, uv={'pz': (0, 0.9, 1, 1), 'nz': (0, 0, 1, 0.1)})
    tube(kit, "motor", [(0, 0.27, 0), (0, 0.34, 0)], [0.09, 0.07], pink, gun, sides=8, side=(1, 0, 0))
    for i in range(6):
        a = 2 * math.pi * i / 6
        o = (math.cos(a) * 0.062, math.sin(a) * 0.062)
        tube(kit, f"barrel {i}", [(o[0], -0.15, o[1]), (o[0], -0.95, o[1])], 0.021, steel, gun, sides=6, side=(1, 0, 0))
    for y0, y1, r, m in ((-0.14, -0.24, 0.105, pink), (-0.58, -0.63, 0.098, yel), (-0.9, -0.96, 0.1, pink)):
        tube(kit, f"clamp {y0}", [(0, y0, 0), (0, y1, 0)], r, m, gun, sides=8, side=(1, 0, 0))
    tube(kit, "spindle", [(0, -0.2, 0), (0, -1.0, 0)], 0.025, yel, gun, sides=6, side=(1, 0, 0))
    tube(kit, "hopper", [(0, 0.04, 0.1), (0, 0.04, 0.32)], [0.12, 0.15], t_hop, gun, sides=8)
    tube(kit, "hopper rim", [(0, 0.04, 0.31), (0, 0.04, 0.34)], 0.16, solid(kit, "hopper rim", "#22c79c"), gun, sides=8)
    lowball(kit, "hopper scoop", (0, 0.04, 0.35), (0.13, 0.13, 0.07), solid(kit, "hopper cream", "#ff8fc8", 0.45), gun)
    for sx in (1, -1):
        tube(kit, f"handle {sx}", [(sx * 0.09, 0.3, 0.0), (sx * 0.1, 0.42, 0.0), (sx * 0.1, 0.44, -0.1)], 0.02, yel, gun,
             sides=4, side=(1, 0, 0))
    return gun


def build_truck(kit, root):
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

    # body: cargo box, cab, hood
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
    # zombie plow with hazard stripes and teeth
    plow = kit.empty("plow", truck, (0, -3.05, 0.55), (16, 0, 0))
    tbox(kit, "plow blade", (0, 0, 0), (2.5, 0.1, 0.72), t_haz, plow, uv={'all': (0, 0, 3, 1)})
    for i in range(7):
        x = -1.08 + i * 0.36
        tube(kit, f"plow tooth {i}", [(x, -0.04, -0.36), (x, -0.2, -0.36)], [(0.07, 0.03), 0.004], yel, plow, sides=4,
             side=(1, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"plow strut {sx}", (sx * 0.7, -2.88, 0.62), (0.1, 0.3, 0.1), ink, truck)
    tbox(kit, "rear bumper", (0, 2.83, 0.62), (2.2, 0.14, 0.16), white, truck)

    # serving window on +X: frame, awning, counter with pints
    for (cy, cz, sy, sz) in ((0.2, 2.06, 1.62, 0.07), (0.2, 1.24, 1.62, 0.07), (-0.58, 1.65, 0.07, 0.86), (0.98, 1.65, 0.07, 0.86)):
        tbox(kit, "window frame", (1.165, cy, cz), (0.05, sy, sz), mint, truck)
    tbox(kit, "awning", (1.36, 0.2, 2.2), (0.42, 1.8, 0.04), t_awn, truck, rot=(0, 20, 0),
         uv={'pz': (0, 0, 6, 1), 'nz': (0, 0, 6, 1), 'px': (0, 0, 6, 1)})
    for i in range(9):
        y = -0.6 + i * 0.2
        lowball(kit, f"scallop {i}", (1.56, y + 0.1, 2.11), (0.02, 0.1, 0.05), pink if i % 2 else white, truck, smooth=False)
    tbox(kit, "counter", (1.27, 0.2, 1.23), (0.24, 1.6, 0.05), pink, truck)
    for i, (y, col) in enumerate(((-0.3, PINK), (0.0, MINT), (0.55, YEL))):
        tube(kit, f"counter pint {i}", [(1.3, y, 1.255), (1.3, y, 1.355)], [0.04, 0.046], tex_mat(f"counter pint {i}", tex_pint(col)),
             truck, sides=8)
    tube(kit, "counter cone", [(1.3, 0.3, 1.26), (1.3, 0.3, 1.38)], [0.004, 0.035], t_waffle, truck, sides=6)
    lowball(kit, "counter cone scoop", (1.3, 0.3, 1.4), (0.04, 0.04, 0.035), solid(kit, "cone scoop", "#ff8fc8", 0.45), truck)

    # roof: hatch with an open lid, rear ladder, loudspeaker, giant cone sign on the cab, turret
    tbox(kit, "hatch frame", (-0.45, 1.9, 2.585), (0.78, 0.78, 0.07), pink, truck)
    tbox(kit, "hatch hole", (-0.45, 1.9, 2.6), (0.62, 0.62, 0.06), ink, truck)
    lid = kit.empty("hatch lid", truck, (-0.45, 2.29, 2.63), (-112, 0, 0))
    tbox(kit, "hatch lid", (0, -0.38, 0.02), (0.74, 0.74, 0.05), mint, lid)
    for sx in (0.42, 0.88):
        tbox(kit, f"ladder rail {sx}", (sx, 2.8, 1.65), (0.05, 0.05, 2.3), yel, truck)
        tube(kit, f"ladder hoop {sx}", [(sx, 2.8, 2.78), (sx, 2.7, 2.9), (sx, 2.55, 2.9), (sx, 2.45, 2.58)], 0.025, yel, truck,
             sides=4, side=(1, 0, 0), caps=(False, False))
    for i in range(7):
        tbox(kit, f"ladder rung {i}", (0.65, 2.8, 0.75 + i * 0.3), (0.46, 0.04, 0.04), yel, truck)
    tube(kit, "speaker", [(0.75, -0.6, 2.75), (0.75, -0.75, 2.75), (0.75, -0.95, 2.78)], [0.04, 0.07, 0.15], yel, truck,
         sides=8, side=(1, 0, 0), caps=(True, False))
    tbox(kit, "speaker post", (0.75, -0.6, 2.64), (0.05, 0.05, 0.18), ink, truck)
    sign = kit.empty("cone sign", truck, (-0.45, -1.45, 2.24))
    tube(kit, "sign post", [(0, 0, 0), (0, 0, 0.1)], 0.05, pink, sign, sides=6)
    tube(kit, "sign cone", [(0, 0, 0.08), (0, 0, 0.5)], [0.02, 0.24], t_waffle, sign, sides=8, bulge=(0.02, 0))
    tube(kit, "sign swirl", [(0, 0, 0.48), (0, 0, 0.56), (0.01, 0, 0.6), (0.01, 0, 0.67), (-0.01, 0, 0.7), (-0.01, 0, 0.77),
                             (0, 0, 0.84)], [0.27, 0.26, 0.2, 0.19, 0.13, 0.11, 0.025], t_swirl, sign, sides=8)
    lowball(kit, "sign cherry", (0, 0, 0.88), (0.05, 0.05, 0.05), solid(kit, "cherry", RED, 0.6), sign)
    turret = kit.empty("turret", truck, (0.35, 0.25, 2.55), scale=(1.2, 1.2, 1.2))
    build_minigun(kit, turret)

    # crew: player at the turret, sprinter climbing the +X side, walkers on the road
    build_player(kit, kit.empty("roof player", truck, (0.3, 1.1, 2.55), (0, 0, -4)))
    build_sprinter(kit, kit.empty("climbing sprinter", truck, (1.38, -0.6, 0.76), (0, 0, -90)), climb=True)
    for i, (x, y, rz) in enumerate(((-1.4, -4.0, 168), (0.55, -4.3, 200), (2.3, -2.2, -118))):
        build_zombie(kit, kit.empty(f"road walker {i}", root, (x, y, 0), (0, 0, rz)), hit=False)

    build_road(kit, root)


def build_road(kit, root):
    R = kit.rand
    road = kit.empty("road", root)
    t_asph = tex_mat("asphalt", tex_asphalt(R), emit=0.15, ext='REPEAT')
    t_dirt = tex_mat("dirt", tex_dirt(R), emit=0.15, ext='REPEAT')
    tbox(kit, "asphalt", (-0.45, 0, -0.03), (7.3, 16, 0.06), t_asph, road, uv={'all': (0, 0, 3.6, 8)})
    for x0, x1 in ((3.2, 4.7), (-5.0, -4.1)):
        tbox(kit, "shoulder", ((x0 + x1) / 2, 0, 0.0), (x1 - x0, 16, 0.1 if x0 > 0 else 0.04), t_dirt, road,
             uv={'all': (0, 0, (x1 - x0) / 2, 8)})
    yel, white = solid(kit, "lane yellow", YEL, 0.5), solid(kit, "lane white", WHITE, 0.4)
    for i in range(6):
        tbox(kit, f"lane dash {i}", (-1.95, -7.0 + i * 2.8, 0.004), (0.14, 1.4, 0.01), yel, road)
    tbox(kit, "edge line", (2.95, 0, 0.004), (0.12, 16, 0.01), white, road)
    tbox(kit, "edge line L", (-3.85, 0, 0.004), (0.12, 16, 0.01), white, road)
    curb = [solid(kit, "curb pink", PINK, 0.35), solid(kit, "curb white", WHITE, 0.35)]
    for i in range(16):
        tbox(kit, f"curb {i}", (3.32, -7.5 + i, 0.08), (0.24, 1.0, 0.16), curb[i % 2], road)

    # street lamp
    lamp = kit.empty("street lamp", road, (4.15, 6.6, 0.1))
    pole = solid(kit, "pole", "#5b5fc0", shade="#474aa0")
    tube(kit, "lamp pole", [(0, 0, 0), (0, 0, 3.9), (-0.3, 0, 4.2), (-1.1, 0, 4.25)], [0.08, 0.06, 0.05, 0.045], pole, lamp, sides=6)
    tbox(kit, "lamp head", (-1.25, 0, 4.2), (0.55, 0.26, 0.12), pole, lamp)
    tbox(kit, "lamp glow", (-1.25, 0, 4.135), (0.45, 0.2, 0.02), solid(kit, "lamp glow", "#fff1a0", 3.0), lamp)
    point_light(kit, lamp, "lamp light", (-1.25, 0, 3.9), "#ffe6a0", 450, 9.0, 0.4)
    # warning sign
    sign = kit.empty("road sign", road, (4.05, 1.2, 0.1), (0, 0, 35))
    tube(kit, "sign pole", [(0, 0.03, 0), (0, 0.03, 1.9)], 0.035, solid(kit, "sign pole", STEEL), sign, sides=6)
    tbox(kit, "sign plate", (0, 0, 1.95), (0.96, 0.03, 0.72), tex_mat("road sign", tex_sign()), sign,
         uv={'py': (0.0, 0.0, 0.05, 0.05)})
    # picket fence, one picket knocked over
    fence = kit.empty("fence", road, (4.5, 3.0, 0.1))
    fw = solid(kit, "fence", WHITE, 0.35)
    for i in range(10):
        y = i * 0.42
        rot = (0, 0, 0) if i != 6 else (-62, 0, 10)
        pk = kit.empty(f"picket {i}", fence, (0, y, 0), rot)
        tube(kit, f"picket {i}", [(0, 0, 0), (0, 0, 0.9)], [(0.05, 0.02)] * 2, fw, pk, sides=4, side=(0, 1, 0), bulge=(0, 0.08),
             smooth=False)
    for z in (0.3, 0.7):
        tbox(kit, f"fence rail {z}", (-0.03, 1.9, z), (0.03, 4.0, 0.08), solid(kit, "fence rail", MINT, 0.35), fence)
    # wrecked car on the far shoulder, still smoking
    car = kit.empty("wrecked car", road, (1.3, 7.0, 0.02), (3, -5, -28))
    t_car = tex_mat("car", tex_car(R))
    t_glass = tex_mat("car glass", tex_car_glass(R))
    tbox(kit, "car body", (0, 0, 0.62), (1.8, 4.1, 0.62), t_car, car, uv={'pz': (0, 0, 0.3, 0.3)})
    tbox(kit, "car cabin", (0, 0.25, 1.17), (1.6, 2.0, 0.5), t_glass, car, taper=(0.86, 0.72))
    hood = kit.empty("car hood", car, (0, -1.0, 0.95), (-38, 0, 0))
    tbox(kit, "car hood", (0, -0.5, 0), (1.7, 1.0, 0.05), t_car, hood)
    for i, (x, y) in enumerate(((0.9, -1.3), (-0.9, -1.3), (0.9, 1.35))):
        wheel(kit, f"car wheel {i}", car, (x, y, 0.33), 1 if x > 0 else -1, solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050"),
              solid(kit, "car hub", STEEL), solid(kit, "car cap", PINK)).scale = (0.7, 0.7, 0.7)
    tbox(kit, "missing wheel axle", (-0.9, 1.35, 0.22), (0.1, 0.1, 0.1), solid(kit, "truck dark", INK, 0.1), car)
    puff = [solid(kit, "smoke " + c, c, 0.45) for c in ("#8a7fae", "#b3a6d9", "#6e6494")]
    for i in range(5):
        r = 0.14 + i * 0.06
        lowball(kit, f"car smoke {i}", (0.1 * math.sin(i * 1.7), -1.5 - 0.1 * i, 1.25 + i * 0.36), (r, r, r * 0.9),
                puff[i % 3], car, smooth=False)


# ---------------------------------------------------------------- textures: shotgun and props
def tex_stock():
    c = Canvas(32, 16, PINK)
    for y in range(16):
        for x in range(32):
            if (x + y) % 9 < 2:
                c.set(x, y, WHITE)
    c.rect(0, 14, 31, 15, INK)
    return c


def tex_pump():
    c = Canvas(16, 16, YEL)
    for y in range(1, 16, 3):
        c.rect(0, y, 15, y, "#d9b21a")
    return c


def tex_boat():
    c = Canvas(32, 16, "#d9f4ff")
    c.speckle(random.Random(5), ["#bfe8ff", "#ffffff"], 40)
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 11, "#a8d8f0")
    c.rect(0, 12, 31, 15, PINK)
    for x in range(0, 32, 4):
        c.set(x + 1, 11, PINK); c.set(x + 2, 11, PINK)
    return c


def tex_tub(rand):
    c = Canvas(64, 32, WHITE)
    c.rect(0, 6, 63, 20, MINT); c.rect(0, 5, 63, 5, "#22c79c"); c.rect(0, 21, 63, 21, "#22c79c")
    for x0 in (17, 49):
        text(c, "MINT", x0, 18, WHITE, 2, shadow="#22c79c")
    c.rect(0, 0, 63, 2, PINK); c.rect(0, 28, 63, 31, PINK)
    c.speckle(rand, [CHOC], 18, 23, 27)
    return c


def tex_mint_chip(rand):
    c = Canvas(16, 16, "#a8ffd9")
    c.speckle(rand, [CHOC, "#4e2812"], 30)
    return c


def tex_crate():
    c = Canvas(32, 32, BLUE)
    for y in (6, 16):
        for x in (3, 11, 19, 27):
            c.rect(x - 2, y, x + 2, y + 6, "#173f9e")
    c.rect(0, 28, 31, 31, "#5aa0ff"); c.rect(0, 0, 31, 2, "#1f5fd0")
    return c


def tex_bottle():
    c = Canvas(16, 32, WHITE)
    c.rect(0, 10, 15, 16, PINK); c.rect(0, 12, 15, 13, WHITE)
    c.rect(0, 22, 15, 26, "#cfe4ff")
    c.rect(0, 27, 15, 31, PINK)
    return c


def tex_sack(rand):
    c = Canvas(64, 32, "#e8c48a")
    for y in range(32):
        for x in range(64):
            if (x + y) % 3 == 0 and (x * 7 + y) % 5 == 0:
                c.set(x, y, "#c9a066")
    c.rect(0, 2, 63, 3, BLUE)
    text(c, "SUGAR", 13, 22, BLUE, 2)
    text(c, "SUGAR", 45, 22, BLUE, 1)
    c.rect(22, 6, 30, 8, PINK)
    return c


def tex_cocoa():
    c = Canvas(32, 32, "#8a4a2a")
    c.rect(0, 20, 31, 24, PINK)
    text(c, "COCOA", 6, 15, "#ffe3c0")
    c.rect(0, 0, 31, 2, "#5e2e18")
    disc(c, 16, 6, 2, "#5e2e18")
    return c


def tex_planks():
    c = Canvas(32, 32, "#d9924a")
    for y in (0, 10, 21):
        c.rect(0, y, 31, y, "#8a5226")
    c.speckle(random.Random(3), ["#c47f3a", "#e8a862"], 60)
    text(c, "SCOOP", 6, 17, PINK)
    c.rect(1, 1, 2, 2, INK); c.rect(29, 1, 30, 2, INK); c.rect(1, 29, 2, 30, INK); c.rect(29, 29, 30, 30, INK)
    return c


# ---------------------------------------------------------------- Sundae Shotgun
def build_shotgun(kit, root):
    t_body = tex_mat("shotgun body", tex_gun_body())
    t_grip = tex_mat("shotgun grip", tex_grip())
    t_stock = tex_mat("stock", tex_stock())
    t_pump = tex_mat("pump", tex_pump())
    t_boat = tex_mat("sundae boat", tex_boat())
    steel = solid(kit, "steel", STEEL, shade="#a9a2e0")
    pink, yel, ink = solid(kit, "gun pink", PINK), solid(kit, "gun yellow", YEL), solid(kit, "gun dark", INK, 0.1)
    R = kit.rand

    tube(kit, "stock", [(0, 0.13, 0.01), (0, 0.24, -0.02), (0, 0.35, -0.05)], [(0.026, 0.035), (0.027, 0.05), (0.029, 0.068)],
         t_stock, root, sides=6, side=(1, 0, 0), bulge=(0, 0.004))
    tbox(kit, "receiver", (0, 0.03, 0.02), (0.056, 0.22, 0.08), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tbox(kit, "grip", (0, 0.1, -0.06), (0.04, 0.045, 0.1), t_grip, root, rot=(18, 0, 0), taper=(1.0, 1.12))
    tbox(kit, "trigger", (0, 0.045, -0.04), (0.008, 0.01, 0.028), yel, root, rot=(-18, 0, 0))
    tube(kit, "guard", [(0, 0.01, -0.02), (0, 0.008, -0.055), (0, 0.035, -0.07), (0, 0.075, -0.064)], 0.0065, yel, root,
         sides=4, side=(1, 0, 0))
    # over-under barrels, pump and magazine tube
    for z in (0.045, 0.005):
        tube(kit, f"barrel {z}", [(0, -0.07, z), (0, -0.3, z)], 0.019, steel, root, sides=8, side=(1, 0, 0))
    for y in (-0.11, -0.27):
        tbox(kit, f"barrel band {y}", (0, y, 0.025), (0.046, 0.016, 0.07), pink, root)
    tube(kit, "mag tube", [(0, -0.07, -0.03), (0, -0.28, -0.03)], 0.012, steel, root, sides=6, side=(1, 0, 0))
    tube(kit, "pump", [(0, -0.12, -0.032), (0, -0.24, -0.032)], [(0.03, 0.026), (0.03, 0.026)], t_pump, root, sides=8,
         side=(1, 0, 0))
    # sundae-boat muzzle loaded with three scoops, cream and a cherry
    tube(kit, "sundae boat", [(0, -0.28, 0.025), (0, -0.31, 0.025), (0, -0.37, 0.028), (0, -0.4, 0.03)],
         [(0.03, 0.03), (0.062, 0.04), (0.076, 0.046), (0.07, 0.044)], t_boat, root, sides=8, side=(1, 0, 0),
         caps=(True, False))
    tube(kit, "boat cream", [(0, -0.36, 0.028), (0, -0.395, 0.03)], [(0.064, 0.038), (0.062, 0.036)],
         solid(kit, "vanilla", "#fff1c7", 0.45), root, sides=8, side=(1, 0, 0), bulge=(0, 0.01))
    scoops = [solid(kit, "berry cream", "#ff8fc8", 0.45), solid(kit, "vanilla", "#fff1c7", 0.45),
              solid(kit, "chocolate", CHOC, 0.25, shade="#4e2812")]
    for i, y in enumerate((-0.31, -0.345, -0.38)):
        lowball(kit, f"boat scoop {i}", (0, y, 0.072), (0.034, 0.03, 0.03), scoops[i], root)
    tube(kit, "whip", [(0, -0.345, 0.095), (0, -0.345, 0.14)], [0.022, 0.003], solid(kit, "whip", WHITE, 0.5), root, sides=6)
    lowball(kit, "cherry", (0, -0.345, 0.148), (0.012, 0.012, 0.012), solid(kit, "cherry", RED, 0.6), root)
    tbox(kit, "wafer", (0.015, -0.385, 0.1), (0.008, 0.015, 0.07), solid(kit, "wafer", "#ffcf5a", shade="#d9862a"), root,
         rot=(-25, 0, 0))
    spr = [solid(kit, "gun sprinkle " + c, c, 0.6) for c in (PINK, BLUE, YEL, MINT, WHITE)]
    for i in range(8):
        tbox(kit, f"boat sprinkle {i}", (0, 0, 0), (0.004, 0.012, 0.004), spr[i % 5], root,
             loc=(R.uniform(-0.02, 0.02), -0.31 - 0.07 * i / 7, 0.1 - 0.004 * (i % 3)), rot=(0, 0, R.uniform(0, 180)))
    # pint feed: hopper pint on top, a spare pint strapped to the stock
    tube(kit, "feed pint", [(0, 0.02, 0.06), (0, 0.02, 0.13)], [0.032, 0.038], tex_mat("feed pint", tex_pint(MINT)), root, sides=8)
    tube(kit, "feed pint lid", [(0, 0.02, 0.13), (0, 0.02, 0.142)], 0.042, solid(kit, "pint lid mint", "#22c79c"), root, sides=8)
    tube(kit, "spare pint", [(0.03, 0.2, -0.03), (0.03, 0.27, -0.03)], [0.026, 0.03], tex_mat("spare pint", tex_pint(YEL)),
         root, sides=8, side=(0, 0, 1))
    tbox(kit, "pint strap", (0.034, 0.235, -0.03), (0.064, 0.012, 0.068), pink, root)
    tbox(kit, "bead", (0, -0.29, 0.07), (0.008, 0.01, 0.012), yel, root)


# ---------------------------------------------------------------- props
def build_props(kit, root):
    R = kit.rand
    white, pink, yel = solid(kit, "prop white", WHITE), solid(kit, "prop pink", PINK), solid(kit, "prop yellow", YEL)
    # flavor tub (3 gallon) with the scoop tool stuck in it
    tub = kit.empty("flavor tub", root, (-0.78, -0.28, 0))
    tube(kit, "tub", [(0, 0, 0), (0, 0, 0.36)], [0.17, 0.19], tex_mat("flavor tub", tex_tub(R)), tub, sides=10, caps=(True, False))
    tube(kit, "tub ice cream", [(0, 0, 0.3), (0, 0, 0.35)], [0.18, 0.17], tex_mat("mint chip", tex_mint_chip(R)), tub,
         sides=10, bulge=(0, 0.04))
    lid = kit.empty("tub lid", tub, (-0.23, 0.06, 0.2), (0, -72, 20))
    tube(kit, "tub lid", [(0, 0, -0.015), (0, 0, 0.015)], 0.2, pink, lid, sides=10)
    tool = kit.empty("scooper", tub, (0.04, -0.02, 0.36), (0, 32, 20))
    tube(kit, "scooper handle", [(0, 0, 0.04), (0, 0, 0.22)], 0.016, yel, tool, sides=6)
    lowball(kit, "scooper bowl", (0, 0, 0.0), (0.04, 0.04, 0.03), solid(kit, "steel", STEEL, shade="#a9a2e0"), tool)
    # filled pint
    pint = kit.empty("filled pint", root, (-0.36, -0.42, 0))
    tube(kit, "pint", [(0, 0, 0), (0, 0, 0.12)], [0.05, 0.058], tex_mat("prop pint", tex_pint(PINK)), pint, sides=8)
    lowball(kit, "pint scoop", (0, 0, 0.13), (0.06, 0.06, 0.045), solid(kit, "berry cream", "#ff8fc8", 0.45), pint)
    spr = [solid(kit, "gun sprinkle " + c, c, 0.6) for c in (PINK, BLUE, YEL, MINT, WHITE)]
    for i in range(8):
        a = 2 * math.pi * i / 8
        tbox(kit, f"pint sprinkle {i}", (0, 0, 0), (0.006, 0.018, 0.006), spr[i % 5], pint,
             loc=(math.cos(a) * 0.035, math.sin(a) * 0.035, 0.168), rot=(0, 0, R.uniform(0, 180)))
    # milk crate with bottles
    crate = kit.empty("milk crate", root, (0.22, 0.34, 0), (0, 0, -8))
    tbox(kit, "crate", (0, 0, 0.15), (0.44, 0.34, 0.3), tex_mat("milk crate", tex_crate()), crate,
         uv={'pz': (0.0, 0.92, 0.05, 1.0)})
    t_bottle = tex_mat("milk bottle", tex_bottle())
    for i, (x, y, tilt) in enumerate(((-0.1, -0.08, 0), (0.1, -0.08, 4), (-0.1, 0.08, -3), (0.1, 0.08, 8))):
        b = kit.empty(f"bottle {i}", crate, (x, y, 0.05), (tilt, 0, 0))
        tube(kit, f"bottle {i}", [(0, 0, 0), (0, 0, 0.22), (0, 0, 0.28), (0, 0, 0.34), (0, 0, 0.36)],
             [0.055, 0.055, 0.03, 0.026, 0.028], t_bottle, b, sides=8)
    # sugar sack, slumped, tied at the top
    sack = kit.empty("sugar sack", root, (0.72, 0.25, 0), (0, 0, -20))
    tube(kit, "sack", [(0, 0, 0), (0, 0, 0.14), (0.01, 0, 0.4), (0.03, 0.01, 0.55), (0.04, 0.01, 0.62), (0.04, 0.01, 0.66),
                       (0.05, 0.01, 0.73)], [(0.24, 0.18), (0.27, 0.2), (0.24, 0.18), (0.13, 0.1), (0.04, 0.04), (0.035, 0.035),
                                             (0.08, 0.06)], tex_mat("sugar sack", tex_sack(R)), sack, sides=8)
    tube(kit, "sack tie", [(0.04, 0.01, 0.6), (0.04, 0.01, 0.635)], 0.05, pink, sack, sides=6)
    # cocoa bag with a folded top
    bag = kit.empty("cocoa bag", root, (0.3, -0.3, 0), (0, 0, 24))
    tbox(kit, "cocoa bag", (0, 0, 0.17), (0.2, 0.12, 0.34), tex_mat("cocoa", tex_cocoa()), bag, taper=(1.0, 0.7),
         uv={'pz': (0, 0, 0.1, 0.1), 'nz': (0, 0, 0.1, 0.1)})
    tbox(kit, "cocoa fold", (0, 0, 0.35), (0.2, 0.06, 0.04), solid(kit, "cocoa fold", "#6e3a1e"), bag)
    # gun crate, lid open, a Scoop Pistol and spare pints in the straw
    gc = kit.empty("gun crate", root, (-0.42, 0.3, 0), (0, 0, 8))
    t_plank = tex_mat("planks", tex_planks())
    tbox(kit, "gun crate", (0, 0, 0.11), (0.62, 0.36, 0.22), t_plank, gc, uv={'pz': (0.0, 0.0, 0.1, 0.1)})
    tbox(kit, "crate inside", (0, 0, 0.2), (0.56, 0.3, 0.04), solid(kit, "crate dark", "#3a2340", 0.1), gc)
    straw = solid(kit, "straw", "#ffe58a", 0.45, shade="#e0b84a")
    for i in range(22):
        tbox(kit, f"straw {i}", (0, 0, 0), (0.008, 0.07, 0.008), straw, gc,
             loc=(R.uniform(-0.26, 0.26), R.uniform(-0.12, 0.12), 0.225), rot=(R.uniform(-20, 20), 0, R.uniform(0, 180)))
    lid = kit.empty("crate lid", gc, (0, 0.18, 0.22), (-105, 0, 0))
    tbox(kit, "crate lid", (0, -0.18, 0.015), (0.62, 0.36, 0.03), t_plank, lid)
    held = kit.empty("crate pistol", gc, (-0.05, -0.02, 0.27), (0, -90, -90))
    build_gun(kit, held)
    for i, (x, col) in enumerate(((0.2, MINT), (0.2, YEL))):
        p = kit.empty(f"crate pint {i}", gc, (x, -0.07 + i * 0.13, 0.24), (90, 0, 15 * i))
        tube(kit, f"crate pint {i}", [(0, 0, -0.045), (0, 0, 0.045)], [0.04, 0.045], tex_mat(f"crate pint {i}", tex_pint(col)),
             p, sides=8)


# ---------------------------------------------------------------- scene / post
def setup(scene, stage):
    for name, loc, col, energy in (("pink fill", (-3, -2, 2.5), PINK, 260), ("blue rim", (3, 4, 3), BLUE, 380)):
        ld = bpy.data.lights.new(name, 'POINT')
        ld.energy = energy
        ld.color = hexc(col)[:3]
        ld.shadow_soft_size = 0.5
        ob = bpy.data.objects.new(name, ld)
        stage.objects.link(ob)
        ob.location = loc


def post(path):
    subprocess.run(["magick", path, "-filter", "point", "-resize", "25%", "-ordered-dither", "o4x4,6",
                    "-filter", "point", "-resize", "400%", path], check=True)
