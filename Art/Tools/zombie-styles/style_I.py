"""Style I: Paper cutout. Flat construction-paper pieces, layered with small depth gaps, jointed with brass brads,
white sticker border and darker cardboard edges. Characters are cards in the XZ plane facing -Y."""
from common import *

KEY = "I"
LABEL = "Paper cutout"
SHADER = 'paper'
WORLD = "#c9a77c"
FLOOR = "#e8d5b5"

TOMATO, BLUE, SKIN, CREAM = "#e85d4a", "#3a6ea5", "#f6c8a0", "#fffaf0"
ZSKIN, LAVENDER, ZPANTS = "#9ccc65", "#b388eb", "#5d8a7a"
MUSTARD = "#f2b134"
WHITE, EDGE, INK = "#fdfaf2", "#a7845a", "#2b2230"
PINK, MINT, CHOC, WAFFLE = "#f48fb1", "#8fd9b6", "#6b3e26", "#d4914a"
BLOOD = "#d8324a"

T = 0.004      # card thickness
G = 0.01       # layer step for characters


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


# ------------------------------------------------------------------ 2D shape helpers (u = X, v = Z)
def chaikin(pts, it):
    for _ in range(it):
        out = []
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            out.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            out.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        pts = out
    return pts


def ellipse(cx, cz, rx, rz, n=20, a0=0.0):
    return [(cx + rx * math.cos(a0 + 2 * math.pi * i / n), cz + rz * math.sin(a0 + 2 * math.pi * i / n)) for i in range(n)]


def capsule(p1, p2, r1, r2, n=7):
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    pts = []
    for k in range(n + 1):
        a = ang - math.pi / 2 + math.pi * k / n
        pts.append((p2[0] + r2 * math.cos(a), p2[1] + r2 * math.sin(a)))
    for k in range(n + 1):
        a = ang + math.pi / 2 + math.pi * k / n
        pts.append((p1[0] + r1 * math.cos(a), p1[1] + r1 * math.sin(a)))
    return pts


def band(path, w0, w1=None):
    """Strip polygon along a polyline, width tapering from w0 to w1."""
    w1 = w0 if w1 is None else w1
    left, right = [], []
    n = len(path)
    for i, p in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, n - 1)]
        dx, dz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dz)
        nx, nz = -dz / ln, dx / ln
        w = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((p[0] + nx * w, p[1] + nz * w))
        right.append((p[0] - nx * w, p[1] - nz * w))
    return left + right[::-1]


def area(pts):
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                     for i in range(len(pts)))


def ccw(pts):
    return pts if area(pts) > 0 else pts[::-1]


def offset(pts, d):
    pts = ccw(pts)
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        e0 = Vector((p1[0] - p0[0], p1[1] - p0[1])).normalized()
        e1 = Vector((p2[0] - p1[0], p2[1] - p1[1])).normalized()
        n0 = Vector((e0.y, -e0.x))
        n1 = Vector((e1.y, -e1.x))
        m = (n0 + n1)
        m = m.normalized() if m.length > 1e-6 else n0
        k = d / max(0.4, m.dot(n0))
        out.append((p1[0] + m.x * k, p1[1] + m.y * k))
    return out


def ragged(pts, amp, rand, sub=2):
    """Torn edge: subdivide each edge and push points in and out."""
    out = []
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        for k in range(sub):
            t = k / sub
            out.append((a[0] + (b[0] - a[0]) * t + rand.uniform(-amp, amp),
                        a[1] + (b[1] - a[1]) * t + rand.uniform(-amp, amp)))
    return out


def star(cx, cz, points, r_out, r_in, rand, wob=0.18, a0=0.0):
    pts = []
    for i in range(points * 2):
        a = a0 + math.pi * i / points
        r = (r_out if i % 2 == 0 else r_in) * (1 + rand.uniform(-wob, wob))
        pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return pts


def blob(cx, cz, r, rand, n=14, wob=0.25, sq=1.0):
    return chaikin([(cx + r * (1 + rand.uniform(-wob, wob)) * math.cos(2 * math.pi * i / n),
                     cz + r * sq * (1 + rand.uniform(-wob, wob)) * math.sin(2 * math.pi * i / n)) for i in range(n)], 1)


def scoop(rad, rand):
    """Ice cream scoop silhouette: lumpy dome with a scalloped bottom edge."""
    pts = [(rad * math.cos(math.pi * i / 11) * (1 + rand.uniform(-0.06, 0.06)),
            rad * 0.85 * math.sin(math.pi * i / 11) * (1 + rand.uniform(-0.06, 0.06))) for i in range(12)]
    # melting bottom edge with drip tongues
    for i in range(1, 12):
        x = -rad + 2 * rad * i / 12
        z = -rad * 0.12
        if i in (3, 4):
            z = -rad * (0.75 + rand.uniform(0, 0.4)) if i == 3 else -rad * 0.75
        if i in (8, 9):
            z = -rad * (0.5 + rand.uniform(0, 0.3)) if i == 8 else -rad * 0.5
        pts.append((x, z))
    return chaikin(pts, 2)


def drop(cx, cz, r, ang, stretch=2.2):
    """Teardrop pointing along ang (degrees)."""
    a = math.radians(ang)
    pts = []
    for i in range(14):
        t = 2 * math.pi * i / 14
        x, z = math.cos(t) * r, math.sin(t) * r
        if x < 0:
            x *= stretch * (1 - 0.35 * abs(math.sin(t)))
        pts.append((x, z))
    pts = [(-x, z) for x, z in pts]
    return [(cx + x * math.cos(a) - z * math.sin(a), cz + x * math.sin(a) + z * math.cos(a)) for x, z in pts]


# ------------------------------------------------------------------ paper construction
def M(kit, c):
    return c if isinstance(c, bpy.types.Material) else kit.mat(c, c)


def slab(kit, name, pts, mats, y, t):
    pts = ccw(pts)
    bm = bmesh.new()
    front = [bm.verts.new((u, y, v)) for u, v in pts]
    back = [bm.verts.new((u, y + t, v)) for u, v in pts]
    bm.faces.new(front)
    bm.faces.new(back[::-1])
    n = len(pts)
    for i in range(n):
        f = bm.faces.new((front[i], back[i], back[(i + 1) % n], front[(i + 1) % n]))
        f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    return me


def piece(kit, name, pts, color, parent, y=0.0, t=T, border=0.0, loc=(0, 0, 0), rot=(0, 0, 0), smooth=0,
          jit=0.0012, edge=EDGE):
    """One cut paper shape in the parent's XZ plane, front face at y (facing -Y). border > 0 adds a white sticker
    backing behind it."""
    pts = chaikin(pts, smooth)
    if jit:
        pts = [(u + kit.rand.uniform(-jit, jit), v + kit.rand.uniform(-jit, jit)) for u, v in pts]
    ob = kit.link(name, slab(kit, name, pts, [M(kit, color), M(kit, edge)], y, t), parent, loc, rot)
    if border:
        bp = offset(pts, border)
        b = kit.link(name + " border", slab(kit, name + " border", bp, [M(kit, WHITE), M(kit, edge)],
                                              y + t + 0.0007, t * 0.5), ob)
    return ob


def brad(kit, parent, x, y, z, r=0.013, rot=(90, 0, 0)):
    m = kit.mat("brass", "#d9ad3c", 'vinyl')
    kit.prim("brad", 'cyl', (r, r, 0.003), m, parent, offset=(x, y - 0.0015, z), rot=rot, segments=12, taper=0.8)
    kit.prim("brad dome", 'sphere', (r * 0.55, 0.0025, r * 0.55), m, parent, offset=(x, y - 0.003, z), segments=10,
             rings=5)


def easel(kit, root, h):
    """Folded cardboard stand behind the card."""
    piece(kit, "stand", [(0.0, 0.0), (0.0, h), (h * 0.42, 0.0)], "#b8915f", root, y=-0.003, t=0.004,
          loc=(0.0, 0.035, 0.0), rot=(0, 0, 90), jit=0)


# ------------------------------------------------------------------ gun
def build_gun(kit, root):
    """Scoop Pistol as a paper cutout in the YZ plane (profile faces +X). 2D coords: s forward (-Y), z up."""
    g = kit.empty("gun card", root, rot=(0, 0, 90))
    L = 0.005
    t = 0.0025
    r = kit.rand

    def P(name, sz, color, layer, border=0.0, smooth=0, jit=0.0006):
        return piece(kit, name, [(-s, z) for s, z in sz], color, g, y=-layer * L, t=t, border=border, smooth=smooth,
                     jit=jit)
    dark_mustard = hex_scale(MUSTARD, 0.82)
    # grip and guard (back layer)
    P("grip", [(-0.022, -0.015), (-0.088, -0.015), (-0.118, -0.128), (-0.108, -0.142), (-0.062, -0.14),
               (-0.05, -0.12)], CHOC, 0, border=0.006, smooth=1)
    for i in range(3):
        z = -0.06 - 0.022 * i
        s0 = -0.075 - 0.006 * i - (0.012 + 0.01 * i) * 0.25
        P(f"grip groove {i}", band([(s0 - 0.005 - 0.01 * i * 0.3, z), (s0 + 0.03, z + 0.004)], 0.007),
          hex_scale(CHOC, 0.7), 1, jit=0.0003)
    P("trigger guard", band([(-0.028, -0.03), (-0.026, -0.058), (-0.012, -0.074), (0.012, -0.078), (0.032, -0.066),
                             (0.042, -0.045), (0.044, -0.03)], 0.01),
      dark_mustard, 0, border=0.005)
    P("trigger", [(-0.002, -0.03), (0.012, -0.03), (0.006, -0.052), (-0.01, -0.062), (-0.006, -0.046)], TOMATO, 0,
      smooth=1)
    # barrel and scoop in the muzzle (behind the cone)
    P("barrel", [(0.06, -0.022), (0.13, -0.02), (0.13, 0.02), (0.06, 0.022)], hex_scale(MUSTARD, 0.7), 0)
    P("muzzle scoop", ellipse(0.218, 0.0, 0.034, 0.05, 18), PINK, 0, border=0.005)
    # body
    P("body", [(-0.105, -0.032), (0.075, -0.036), (0.095, -0.012), (0.09, 0.03), (0.06, 0.04), (-0.07, 0.042),
               (-0.105, 0.03), (-0.115, 0.0)], MUSTARD, 1, border=0.007, smooth=1)
    P("hammer", [(-0.1, 0.015), (-0.122, 0.04), (-0.112, 0.05), (-0.088, 0.035)], dark_mustard, 0, border=0.005)
    P("sight", [(0.06, 0.035), (0.075, 0.035), (0.072, 0.055), (0.064, 0.055)], dark_mustard, 0, border=0.004)
    P("body stripe", band([(-0.1, -0.014), (0.088, -0.018)], 0.012), TOMATO, 2)
    P("star decal", star(-0.075, 0.012, 5, 0.018, 0.008, r, wob=0.05, a0=math.pi / 2), CREAM, 3)
    # waffle cone muzzle
    cone = [(0.105, -0.024), (0.205, -0.06), (0.205, 0.06), (0.105, 0.024)]
    P("cone", cone, WAFFLE, 1, border=0.007)
    for i in range(-3, 6):
        for j in range(-4, 5):
            cs = 0.125 + 0.016 * i + 0.008 * (j % 2)
            cz = 0.013 * j
            half = 0.024 + (cs - 0.105) / 0.1 * 0.036
            if 0.115 < cs < 0.19 and abs(cz) < half - 0.011:
                P("waffle", [(cs - 0.0065, cz), (cs, cz - 0.0055), (cs + 0.0065, cz), (cs, cz + 0.0055)],
                  "#e9b673", 2, jit=0.0004)
    P("cone rim", [(0.198, -0.066), (0.216, -0.064), (0.216, 0.064), (0.198, 0.066)], "#e9b673", 2, border=0.004)
    # pint tub magazine with chocolate scoop and sprinkles
    P("scoop", [(-0.075, 0.098), (-0.07, 0.135), (-0.05, 0.158), (-0.03, 0.155), (-0.012, 0.172), (0.012, 0.165),
                (0.03, 0.172), (0.05, 0.152), (0.068, 0.13), (0.07, 0.098)], CHOC, 1, border=0.006, smooth=1)
    P("pint tub", [(-0.055, 0.036), (0.045, 0.036), (0.058, 0.112), (-0.068, 0.112)], CREAM, 2, border=0.006)
    P("pint label", [(-0.06, 0.06), (0.05, 0.06), (0.053, 0.083), (-0.063, 0.083)], TOMATO, 3)
    P("pint label dot", ellipse(-0.005, 0.0715, 0.013, 0.009, 12), CREAM, 4)
    P("pint lip", [(-0.074, 0.106), (0.064, 0.106), (0.064, 0.119), (-0.074, 0.119)], hex_scale(CREAM, 0.9), 3)
    for k, (s0, w, ln) in enumerate([(-0.045, 0.013, 0.028), (0.012, 0.012, 0.034), (0.045, 0.011, 0.022)]):
        P(f"choc drip {k}", capsule((s0, 0.12), (s0, 0.12 - ln), w / 2, w / 2 * 1.15, 5) +
          [(s0 + w / 2, 0.122), (s0 - w / 2, 0.122)], CHOC, 4, smooth=0)
    cols = [PINK, MINT, "#7ec4e0", CREAM, TOMATO, "#ffd54a"]
    for k in range(11):
        cs = -0.055 + 0.011 * k + r.uniform(-0.004, 0.004)
        top = 0.13 + 0.03 * math.sin(math.pi * (k + 0.5) / 11)
        cz = r.uniform(0.128, top)
        a = r.uniform(0, math.pi)
        d = (math.cos(a) * 0.006, math.sin(a) * 0.006)
        P(f"sprinkle {k}", capsule((cs - d[0], cz - d[1]), (cs + d[0], cz + d[1]), 0.0028, 0.0028, 4),
          cols[k % len(cols)], 2, jit=0)
    # brads
    for s, z in ((-0.05, -0.005), (0.005, -0.035)):
        brad(kit, g, -s, -5 * L, z, r=0.0065)
    brad(kit, g, -0.135, -3 * L, 0.0, r=0.006)


# ------------------------------------------------------------------ player
def build_player(kit, root):
    r = kit.rand
    y = lambda n: -n * G
    easel(kit, root, 0.9)
    # cooler backpack with pints peeking out
    for k, (x, c) in enumerate(((-0.17, PINK), (0.0, CHOC), (0.17, MINT))):
        p = piece(kit, f"pint {k}", [(x - 0.06, 1.12), (x + 0.06, 1.12), (x + 0.07, 1.32), (x - 0.07, 1.32)], CREAM,
                  root, y(-5), border=0.012)
        piece(kit, f"pint {k} lid", [(x - 0.075, 1.31), (x + 0.075, 1.31), (x + 0.07, 1.345), (x - 0.07, 1.345)], c,
              root, y(-6))
        piece(kit, f"pint {k} label", [(x - 0.064, 1.2), (x + 0.064, 1.2), (x + 0.066, 1.24), (x - 0.066, 1.24)], c,
              root, y(-6))
    piece(kit, "cooler", [(-0.26, 0.72), (0.26, 0.72), (0.27, 1.18), (-0.27, 1.18)], "#7ec4e0", root, y(-4),
          border=0.014, smooth=1)
    piece(kit, "cooler lid", [(-0.29, 1.12), (0.29, 1.12), (0.28, 1.2), (-0.28, 1.2)], WHITE, root, y(-3.2),
          border=0.01, smooth=1)
    # legs on hip brads
    for side in (-1, 1):
        hip = kit.empty(f"hip {side}", root, (side * 0.085, y(-1), 0.66), (0, side * -3, 0))
        piece(kit, "leg", [(-0.075, 0.05), (0.075, 0.05), (0.062, -0.57), (-0.058, -0.57)], BLUE, hip, 0,
              border=0.012)
        piece(kit, "cuff", [(-0.066, -0.52), (0.068, -0.52), (0.07, -0.575), (-0.068, -0.575)],
              hex_scale(BLUE, 1.35), hip, -G)
        piece(kit, "shoe", [(-0.075 + side * 0.03, -0.66), (0.075 + side * 0.03, -0.66), (0.09 * side + 0.03, -0.625),
                            (0.07 * side + 0.02, -0.585), (-0.06 * side + 0.0, -0.575), (-0.07 * side, -0.62)][::side],
              "#5a3d2b", hip, -2 * G, border=0.012, smooth=2)
        piece(kit, "shoe lace", [(-0.02, -0.598), (0.025, -0.598), (0.022, -0.608), (-0.02, -0.608)], WHITE, hip,
              -3 * G)
        brad(kit, hip, 0.0, -G * 0.6, 0.0)
    # torso
    shirt = [(-0.15, 0.6), (0.15, 0.6), (0.165, 0.85), (0.205, 1.06), (0.14, 1.125), (0.05, 1.135), (-0.05, 1.135),
             (-0.14, 1.125), (-0.205, 1.06), (-0.165, 0.85)]
    piece(kit, "shirt", shirt, TOMATO, root, y(0), border=0.014, smooth=1)
    piece(kit, "neck", [(-0.045, 1.08), (0.045, 1.08), (0.045, 1.18), (-0.045, 1.18)], hex_scale(SKIN, 0.88), root,
          y(0.6))
    piece(kit, "collar L", [(0.0, 1.07), (0.075, 1.14), (0.025, 1.14)], WHITE, root, y(1.2))
    piece(kit, "collar R", [(0.0, 1.07), (-0.025, 1.14), (-0.075, 1.14)], WHITE, root, y(1.2))
    apron = [(-0.1, 0.98), (0.1, 0.98), (0.1, 0.83), (0.175, 0.79), (0.19, 0.47), (0.0, 0.455), (-0.19, 0.47),
             (-0.175, 0.79), (-0.1, 0.83)]
    piece(kit, "apron", apron, CREAM, root, y(1), border=0.008)
    piece(kit, "apron pocket", [(-0.08, 0.58), (0.08, 0.58), (0.075, 0.69), (-0.075, 0.69)], TOMATO, root, y(2),
          smooth=0)
    piece(kit, "pocket stitch", band([(-0.07, 0.67), (0.07, 0.67)], 0.006), CREAM, root, y(3), jit=0.0004)
    piece(kit, "logo cone", [(-0.022, 0.905), (0.022, 0.905), (0.0, 0.85)], WAFFLE, root, y(2))
    piece(kit, "logo scoop", ellipse(0.0, 0.917, 0.027, 0.022, 14), PINK, root, y(3))
    piece(kit, "apron tie", band([(-0.19, 0.79), (-0.24, 0.75), (-0.235, 0.7)], 0.025, 0.018), CREAM, root, y(0.4))
    for side in (-1, 1):
        piece(kit, f"strap {side}", band([(side * 0.115, 1.14), (side * 0.13, 0.98), (side * 0.15, 0.82)], 0.038),
              hex_scale(BLUE, 0.8), root, y(2.2))
        piece(kit, f"strap buckle {side}", [(side * 0.125 - 0.024, 0.9), (side * 0.125 + 0.03, 0.905),
                                            (side * 0.13 + 0.03, 0.93), (side * 0.13 - 0.024, 0.925)], MUSTARD,
              root, y(3.2))
    # head
    head = kit.empty("head", root, (0, y(3), 1.29), (0, 3, 0))
    for side in (-1, 1):
        piece(kit, "ear", ellipse(side * 0.165, -0.015, 0.04, 0.05, 14), SKIN, head, G * 0.5, border=0.01)
        piece(kit, "ear inner", ellipse(side * 0.168, -0.015, 0.018, 0.028, 10), hex_scale(SKIN, 0.85), head,
              G * 0.5 - 0.0045)
    piece(kit, "hair back", [(-0.18, -0.04), (-0.17, 0.12), (0.0, 0.2), (0.17, 0.12), (0.18, -0.04), (0.12, 0.08),
                             (-0.12, 0.08)], "#6b4226", head, G * 1.5, border=0.012, smooth=1)
    face = [(-0.16, 0.02), (-0.15, -0.09), (-0.09, -0.155), (0.0, -0.172), (0.09, -0.155), (0.15, -0.09),
            (0.16, 0.02), (0.14, 0.11), (0.07, 0.165), (-0.07, 0.165), (-0.14, 0.11)]
    piece(kit, "face", face, SKIN, head, 0, border=0.012, smooth=2)
    piece(kit, "fringe", [(-0.16, 0.06), (-0.12, 0.17), (0.12, 0.17), (0.16, 0.06), (0.1, 0.1), (0.06, 0.05),
                          (0.02, 0.1), (-0.04, 0.06), (-0.08, 0.1)], "#6b4226", head, -G)
    for side in (-1, 1):
        piece(kit, "eye", ellipse(side * 0.058, 0.0, 0.022, 0.034, 16), INK, head, -G)
        piece(kit, "eye shine", ellipse(side * 0.058 + 0.008, 0.012, 0.007, 0.009, 8), WHITE, head, -2 * G, jit=0)
        piece(kit, "brow", band([(side * 0.03, 0.05), (side * 0.085, 0.065)], 0.013, 0.009), "#6b4226", head, -G)
        piece(kit, "cheek", ellipse(side * 0.105, -0.06, 0.028, 0.02, 12), "#f29a8a", head, -G)
    piece(kit, "nose", [(-0.016, -0.045), (0.016, -0.045), (0.012, -0.02), (0.0, -0.012), (-0.012, -0.02)],
          hex_scale(SKIN, 0.86), head, -G, smooth=1)
    piece(kit, "mouth", [(-0.055, -0.085), (0.055, -0.085), (0.045, -0.11), (0.02, -0.125), (-0.02, -0.125),
                         (-0.045, -0.11)], "#7a2a2a", head, -G, smooth=1)
    piece(kit, "teeth", [(-0.045, -0.088), (0.045, -0.088), (0.04, -0.1), (-0.04, -0.1)], WHITE, head, -2 * G)
    # soda-jerk paper hat
    hat = kit.empty("hat", head, (0, -2.5 * G, 0.115), (0, -7, 0))
    piece(kit, "hat", [(-0.2, -0.005), (0.2, -0.005), (0.175, 0.1), (0.07, 0.145), (-0.07, 0.145), (-0.175, 0.1)],
          WHITE, hat, 0, border=0.01, smooth=1)
    piece(kit, "hat stripe", band([(-0.19, 0.03), (0.19, 0.03)], 0.028), TOMATO, hat, -G)
    piece(kit, "hat fold", band([(-0.17, 0.085), (0.0, 0.11), (0.17, 0.085)], 0.006), hex_scale(WHITE, 0.86), hat, -G)
    piece(kit, "hat badge", star(0.0, 0.07, 5, 0.026, 0.012, r, wob=0.05, a0=math.pi / 2), MUSTARD, hat, -2 * G)
    # right arm (-X): raised, swung forward so the gun reads; elbow on a brad
    sh = kit.empty("R shoulder", root, (-0.17, y(5), 1.06), (0, 96, 42))
    piece(kit, "R upper arm", capsule((0, 0), (0, -0.22), 0.045, 0.04), SKIN, sh, 0, border=0.01)
    piece(kit, "R sleeve", capsule((0, 0.01), (0, -0.09), 0.062, 0.056), TOMATO, sh, -G, border=0.008)
    brad(kit, sh, 0, -2 * G, 0)
    el = kit.empty("R elbow", sh, (0, -3 * G, -0.21), (0, -4, 0))
    piece(kit, "R forearm", capsule((0, 0), (0, -0.2), 0.04, 0.036), SKIN, el, 0, border=0.01)
    brad(kit, el, 0, -G, 0)
    sc = 1.25
    gp = kit.empty("R gun", el, (-0.08 * sc, -2 * G, -0.24 - 0.07 * sc), scale=(sc, sc, sc))
    gp.rotation_euler = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0))).to_euler()
    build_gun(kit, gp)
    piece(kit, "R fist", [(-0.04, -0.2), (0.045, -0.2), (0.05, -0.27), (0.03, -0.3), (-0.035, -0.3),
                          (-0.048, -0.25)], SKIN, el, -6.5 * G, border=0.008, smooth=1)
    piece(kit, "R thumb", capsule((0.04, -0.215), (0.0, -0.24), 0.014, 0.013, 5), hex_scale(SKIN, 0.93), el,
          -7.5 * G)
    # left arm (+X): holding a spare cone
    sh = kit.empty("L shoulder", root, (0.17, y(5), 1.06), (0, -26, 0))
    piece(kit, "L upper arm", capsule((0, 0), (0, -0.22), 0.045, 0.04), SKIN, sh, 0, border=0.01)
    piece(kit, "L sleeve", capsule((0, 0.01), (0, -0.09), 0.062, 0.056), TOMATO, sh, -G, border=0.008)
    brad(kit, sh, 0, -2 * G, 0)
    el = kit.empty("L elbow", sh, (0, -3 * G, -0.21), (0, -150, 0))
    piece(kit, "L forearm", capsule((0, 0), (0, -0.19), 0.04, 0.036), SKIN, el, 0, border=0.01)
    brad(kit, el, 0, -G, 0)
    piece(kit, "cone", [(-0.035, -0.3), (0.035, -0.3), (0.0, -0.19)], WAFFLE, el, G * 0.5, border=0.008)
    piece(kit, "cone scoop", blob(0.0, -0.33, 0.042, r, wob=0.12), MINT, el, G * 1.5, border=0.008)
    piece(kit, "L fist", ellipse(0.0, -0.21, 0.045, 0.04, 16), SKIN, el, -G, border=0.008)


# ------------------------------------------------------------------ zombie
def zombie_arm(kit, parent, name, sleeve_col, torn):
    """Arm hanging along -Z from its shoulder brad. Returns (shoulder, elbow, wrist) pivots' children built."""
    r = kit.rand
    piece(kit, name + " upper arm", capsule((0, 0), (0, -0.23), 0.04, 0.034), ZSKIN, parent, 0, border=0.01)
    sl = [(-0.06, 0.03), (0.06, 0.03), (0.06, -0.08), (0.04, -0.12), (0.02, -0.09), (0.0, -0.13), (-0.025, -0.095),
          (-0.045, -0.12), (-0.062, -0.07)]
    piece(kit, name + " sleeve", sl, sleeve_col, parent, -G, border=0.008)
    brad(kit, parent, 0, -2 * G, 0)
    el = kit.empty(name + " elbow", parent, (0, -3 * G, -0.22))
    piece(kit, name + " forearm", capsule((0, 0), (0, -0.21), 0.035, 0.03), ZSKIN, el, 0, border=0.01)
    piece(kit, name + " scrape", band([(-0.012, -0.08), (0.006, -0.12)], 0.014, 0.006), "#7aa84a", el, -G, jit=0.0004)
    brad(kit, el, 0, -G, 0)
    wr = kit.empty(name + " wrist", el, (0, -2 * G, -0.21))
    hand = [(-0.04, 0.02), (0.04, 0.02), (0.045, -0.04), (0.035, -0.1), (0.022, -0.1), (0.018, -0.055),
            (0.008, -0.11), (-0.006, -0.11), (-0.008, -0.06), (-0.02, -0.1), (-0.034, -0.098), (-0.03, -0.05),
            (-0.05, -0.04)]
    piece(kit, name + " hand", hand, ZSKIN, wr, 0, border=0.009)
    for x in (-0.027, 0.0, 0.028):
        piece(kit, name + " nail", [(x - 0.006, -0.095), (x + 0.006, -0.095), (x, -0.112)], "#e8e2c8", wr, -G, jit=0)
    return el, wr


def build_zombie(kit, root, hit=False):
    r = kit.rand
    y = lambda n: -n * G
    easel(kit, root, 0.8)
    # legs: thigh and shin on brads, knock-kneed
    for side, th, sh_rot, shoe in ((-1, -9, 17, True), (1, 11, -24, False)):
        hip = kit.empty(f"hip {side}", root, (side * 0.085, y(-1), 0.62), (0, th, 0))
        thigh = [(-0.07, 0.04), (0.07, 0.04), (0.06, -0.3), (-0.06, -0.3)]
        piece(kit, "thigh", thigh, ZPANTS, hip, 0, border=0.012)
        piece(kit, "patch", [(-0.03, -0.12), (0.03, -0.11), (0.032, -0.17), (-0.028, -0.175)], "#c9a06a", hip, -G)
        brad(kit, hip, 0, -G * 1.2, 0)
        knee = kit.empty(f"knee {side}", hip, (0, -2 * G, -0.28), (0, sh_rot, 0))
        piece(kit, "shin", capsule((0, 0.0), (0, -0.27), 0.04, 0.034), ZSKIN, knee, 0, border=0.01)
        torn = [(-0.062, 0.03), (0.062, 0.03), (0.06, -0.12), (0.04, -0.15), (0.025, -0.12), (0.005, -0.17),
                (-0.012, -0.13), (-0.03, -0.16), (-0.045, -0.12), (-0.06, -0.14)]
        piece(kit, "pant leg", torn, ZPANTS, knee, -G, border=0.01)
        brad(kit, knee, 0, -2 * G, 0)
        if shoe:
            piece(kit, "shoe", [(-0.1, -0.32), (0.06, -0.32), (0.06, -0.27), (0.02, -0.25), (-0.05, -0.25),
                                (-0.1, -0.285)], "#4a3a32", knee, -G, border=0.01, smooth=1)
            piece(kit, "shoe hole", ellipse(-0.07, -0.3, 0.012, 0.009, 8), ZSKIN, knee, -2 * G)
        else:
            foot = [(-0.03, -0.25), (0.04, -0.25), (0.08, -0.29), (0.09, -0.325), (0.07, -0.33), (0.065, -0.315),
                    (0.05, -0.33), (0.04, -0.315), (0.025, -0.33), (0.015, -0.315), (-0.04, -0.325)]
            piece(kit, "bare foot", foot, ZSKIN, knee, -G * 0.5, border=0.01)
    piece(kit, "hips", [(-0.165, 0.5), (0.165, 0.5), (0.17, 0.665), (-0.17, 0.665)], ZPANTS, root, y(-0.5),
          border=0.012)
    piece(kit, "belt", band([(-0.17, 0.645), (0.17, 0.64)], 0.035), "#4a3a32", root, y(0.5))
    piece(kit, "belt buckle", [(-0.025, 0.625), (0.025, 0.625), (0.025, 0.66), (-0.025, 0.66)], MUSTARD, root, y(1.5))
    # torso: hunched forward, slumped to one side
    torso = kit.empty("torso", root, (0, 0, 0.6), (-8, -4, 0) if hit else (14, 5, 0))
    shirt = [(-0.16, -0.05), (-0.12, -0.02), (-0.09, -0.07), (-0.05, -0.03), (-0.01, -0.08), (0.03, -0.03),
             (0.07, -0.075), (0.1, -0.03), (0.16, -0.06), (0.165, 0.2), (0.215, 0.4), (0.17, 0.455), (0.06, 0.47),
             (-0.06, 0.5), (-0.17, 0.5), (-0.225, 0.45), (-0.18, 0.2)]
    piece(kit, "shirt", shirt, LAVENDER, torso, 0, border=0.014)
    piece(kit, "rip", [(0.04, 0.08), (0.09, 0.12), (0.11, 0.2), (0.08, 0.25), (0.06, 0.18), (0.03, 0.2),
                       (0.05, 0.13)], ZSKIN, torso, -G)
    for k in range(3):
        piece(kit, "rib", band([(0.055, 0.14 + 0.03 * k), (0.095, 0.15 + 0.03 * k)], 0.01), "#f3ecd8", torso,
              -2 * G, jit=0.0004)
    piece(kit, "collar", [(-0.09, 0.47), (0.05, 0.455), (0.0, 0.4), (-0.03, 0.42)], hex_scale(LAVENDER, 0.75), torso,
          -G)
    piece(kit, "tie", [(-0.03, 0.43), (0.0, 0.43), (0.012, 0.25), (-0.008, 0.22), (-0.03, 0.26)], TOMATO, torso,
          -2 * G, border=0.006)
    # ice cream splat on the shirt
    piece(kit, "shirt splat", [(-0.16, 0.3), (-0.12, 0.36), (-0.06, 0.34), (-0.04, 0.29), (-0.06, 0.24),
                               (-0.07, 0.15), (-0.085, 0.15), (-0.09, 0.23), (-0.11, 0.2), (-0.12, 0.12),
                               (-0.135, 0.12), (-0.14, 0.24), (-0.17, 0.26)], PINK, torso, -G, border=0.007, smooth=1)
    piece(kit, "splat cherry", ellipse(-0.1, 0.33, 0.022, 0.022, 12), BLOOD, torso, -2 * G)
    # head: sunk low, tilted
    head = kit.empty("head", torso, (-0.03, -3 * G, 0.54), (0, -22, 0) if hit else (0, 17, 0))
    skull = [(-0.15, -0.02), (-0.13, -0.12), (-0.07, -0.17), (0.02, -0.18), (0.1, -0.15), (0.155, -0.06),
             (0.16, 0.05), (0.13, 0.08), (0.11, 0.06), (0.085, 0.1), (0.05, 0.075), (0.02, 0.11), (-0.02, 0.08),
             (-0.05, 0.115), (-0.08, 0.085), (-0.12, 0.1), (-0.15, 0.07)]
    piece(kit, "brain", [(-0.13, 0.04), (-0.14, 0.11), (-0.1, 0.16), (-0.04, 0.17), (0.02, 0.18), (0.08, 0.16),
                         (0.13, 0.12), (0.14, 0.04)], "#f7a1b8", head, G, border=0.012, smooth=2)
    for path in ([(-0.11, 0.1), (-0.07, 0.14), (-0.03, 0.12)], [(-0.01, 0.15), (0.03, 0.12), (0.07, 0.15)],
                 [(0.06, 0.12), (0.1, 0.13), (0.12, 0.09)], [(-0.06, 0.1), (-0.02, 0.135)]):
        piece(kit, "brain fold", band(path, 0.009, 0.006), "#d9708e", head, 0.5 * G, jit=0.0003)
    piece(kit, "skull", skull, ZSKIN, head, 0, border=0.012)
    piece(kit, "ear", ellipse(-0.155, -0.04, 0.035, 0.05, 12), ZSKIN, head, G * 0.5, border=0.01)
    piece(kit, "eye bag", ellipse(-0.06, -0.03, 0.06, 0.06, 18), "#7da84f", head, -G)
    piece(kit, "big eye", ellipse(-0.06, -0.02, 0.05, 0.05, 20), "#fff6d8", head, -2 * G)
    piece(kit, "big pupil", ellipse(-0.045, -0.035, 0.014, 0.014, 10), INK, head, -3 * G)
    piece(kit, "small eye", ellipse(0.075, -0.015, 0.024, 0.022, 14), "#fff6d8", head, -G)
    piece(kit, "small pupil", ellipse(0.07, -0.022, 0.009, 0.009, 8), "#c0392b", head, -2 * G)
    piece(kit, "droopy lid", [(0.045, -0.005), (0.105, -0.005), (0.1, 0.01), (0.075, 0.016), (0.05, 0.01)], "#7da84f",
          head, -3 * G, smooth=1)
    mouth = ([(-0.06, -0.1), (0.06, -0.085), (0.07, -0.12), (0.03, -0.165), (-0.03, -0.165), (-0.065, -0.135)] if hit
             else [(-0.06, -0.1), (0.065, -0.09), (0.06, -0.125), (0.0, -0.14), (-0.055, -0.125)])
    piece(kit, "mouth", mouth, "#3a1a2a", head, -G, smooth=1)
    for k, x in enumerate((-0.04, -0.012, 0.04)):
        piece(kit, "tooth", [(x - 0.012, -0.096 + 0.0015 * k), (x + 0.012, -0.093 + 0.0015 * k), (x, -0.118)],
              "#f3ecd8", head, -2 * G, jit=0)
    piece(kit, "scar", band([(0.06, -0.06), (0.12, -0.11)], 0.007), INK, head, -G, jit=0.0003)
    for k in range(3):
        cx, cz = 0.07 + 0.02 * k, -0.068 - 0.017 * k
        piece(kit, "stitch", band([(cx - 0.012, cz - 0.012), (cx + 0.012, cz + 0.012)], 0.005), INK, head, -G,
              jit=0.0002)
    # right arm (-X): reaching forward, swung out of the card plane
    sh = kit.empty("R shoulder", torso, (-0.185, -2 * G, 0.43), (0, 80, 38) if not hit else (0, 120, 30))
    el, wr = zombie_arm(kit, sh, "R", LAVENDER, True)
    el.rotation_euler[1] = math.radians(-12)
    wr.rotation_euler[1] = math.radians(-55)
    # left arm (+X): dangling limp, or flying away when hit
    if not hit:
        sh = kit.empty("L shoulder", torso, (0.175, -2 * G, 0.4), (0, -12, 0))
        el, wr = zombie_arm(kit, sh, "L", LAVENDER, True)
        el.rotation_euler[1] = math.radians(-20)
        wr.rotation_euler[1] = math.radians(15)
    else:
        sh = kit.empty("L arm flying", root, (0.62, -0.38, 1.28), (25, -150, -30))
        el, wr = zombie_arm(kit, sh, "L", LAVENDER, True)
        el.rotation_euler[1] = math.radians(-35)
        wr.rotation_euler[1] = math.radians(25)
        piece(kit, "arm stump rip", ragged(ellipse(0, 0.0, 0.05, 0.035, 10), 0.012, r, 2), BLOOD, sh, G,
              border=0.008, jit=0)
        build_hit_fx(kit, root, torso)


def build_hit_fx(kit, root, torso):
    r = kit.rand
    # wound on the shoulder
    piece(kit, "shoulder wound", ragged(ellipse(0.17, 0.4, 0.06, 0.05, 10), 0.014, r, 2), BLOOD, torso, -4 * G,
          border=0.008, jit=0)
    piece(kit, "bone", capsule((0.15, 0.4), (0.21, 0.42), 0.012, 0.012, 5) + [], "#f3ecd8", torso, -5 * G, jit=0)
    for x, z in ((0.212, 0.432), (0.212, 0.408)):
        piece(kit, "bone knob", ellipse(x, z, 0.014, 0.014, 10), "#f3ecd8", torso, -5 * G, jit=0)
    # cut-paper starburst at the hit point
    fx = kit.empty("burst", root, (0.36, -0.12, 1.02), (0, 0, 0))
    piece(kit, "burst outer", star(0, 0, 13, 0.27, 0.14, r, wob=0.22), "#ffd54a", fx, 0, border=0.014, jit=0)
    piece(kit, "burst mid", star(0, 0, 11, 0.18, 0.1, r, wob=0.2, a0=0.2), WHITE, fx, -G, jit=0)
    piece(kit, "burst inner", star(0, 0, 9, 0.1, 0.055, r, wob=0.18, a0=0.1), TOMATO, fx, -2 * G, jit=0)
    # torn red paper blood and drops flying out
    o = Vector((0.3, -0.2, 1.05))
    for k in range(16):
        a = r.uniform(-60, 80)
        d = Vector((math.cos(math.radians(a)), r.uniform(-1.2, -0.2), math.sin(math.radians(a)))).normalized()
        p = o + d * r.uniform(0.18, 0.6)
        size = r.uniform(0.018, 0.045)
        sp = kit.empty("blood", root, tuple(p), (r.uniform(-30, 30), 0, r.uniform(-35, 35)))
        if k % 2:
            pts = drop(0, 0, size, a + 180, 2.4)
        else:
            pts = ragged(ellipse(0, 0, size * 1.3, size, 8), size * 0.3, r, 2)
        piece(kit, "blood piece", pts, BLOOD if k % 3 else hex_scale(BLOOD, 0.8), sp, 0, border=0.006, jit=0)
    # ice cream chunks with drips
    for k, (c, p) in enumerate(((PINK, (0.55, -0.42, 0.95)), (MINT, (0.14, -0.38, 1.33)), ("#fff1c9", (0.72, -0.2, 1.12)),
                                (PINK, (0.4, -0.5, 1.45)), (CHOC, (0.62, -0.3, 0.72)))):
        sp = kit.empty("ice cream", root, p, (r.uniform(-15, 15), 0, r.uniform(-20, 20)))
        rad = r.uniform(0.065, 0.085)
        piece(kit, "scoop chunk", scoop(rad, r), c, sp, 0, border=0.01, jit=0)
        piece(kit, "scoop shine", ellipse(-rad * 0.35, rad * 0.45, rad * 0.18, rad * 0.1, 10), WHITE, sp, -G * 0.6,
              jit=0)
    # confetti and paper scraps
    cols = ["#ffd54a", PINK, MINT, "#7ec4e0", TOMATO, CREAM, LAVENDER]
    for k in range(70):
        a = r.uniform(-80, 100)
        d = Vector((math.cos(math.radians(a)), r.uniform(-1.4, 0.2), math.sin(math.radians(a)))).normalized()
        p = o + d * r.uniform(0.2, 0.75)
        if p.z < 0.15:
            p.z = 0.15 + r.uniform(0, 0.2)
        sp = kit.empty("confetti", root, tuple(p), (r.uniform(0, 360), r.uniform(0, 360), r.uniform(0, 360)))
        w, h = r.uniform(0.012, 0.022), r.uniform(0.006, 0.012)
        pts = [(-w, -h), (w, -h), (w, h), (-w, h)] if k % 3 else [(-w, -h), (w, -h), (0, h * 1.6)]
        piece(kit, "confetti piece", pts, cols[k % len(cols)], sp, 0, t=0.0015, jit=0)
    # brass brad popping out
    bp = kit.empty("popped brad", root, (0.45, -0.3, 1.38), (30, 40, 0))
    brad(kit, bp, 0, 0, 0, r=0.016)
    # torn splats on the floor
    for k, (x, yy, rad, c) in enumerate(((0.45, -0.25, 0.13, BLOOD), (0.7, -0.05, 0.08, PINK),
                                         (-0.2, -0.3, 0.07, BLOOD), (0.3, -0.55, 0.06, MINT))):
        sp = kit.empty("floor splat", root, (x, yy, 0.002), (-90, 0, r.uniform(0, 360)))
        pts = ragged(blob(0, 0, rad, r, n=10, wob=0.3, sq=0.8), rad * 0.12, r, 2)
        piece(kit, "splat", pts, c, sp, 0, t=0.002, border=0.008, jit=0)
