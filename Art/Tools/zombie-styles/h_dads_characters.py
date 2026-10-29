"""Divorced Dads characters (style H): the four player dads, dad first-person arms, the kids (four normal kids, Fat Kid,
Lactose Kid, Diabetic Kid, Rich Kid), the Cop and Big Dairy.

Rig (same as the zombie-mode players so WalkCycle works): '<Asset> leg L/R' pivots at the hips, '<Asset> arm L/R'
pivots at the shoulders (local axes aligned with the root, arms hanging down; WalkCycle swings them around local X),
'<Asset> head pivot' at the neck. Sockets: 'socket hand L/R' (palm center, axes aligned with the root in the rest pose),
dads 'socket camera' at eye height, kids / cop 'socket bubble' (about 0.35 m above the head, under the root) and
'socket mouth', Big Dairy 'socket bubble'. Everything faces -Y, feet at z = 0."""
from style_H import *
import re

SPACING = 3

# ---------------------------------------------------------------- palette
SKIN_D = "#f0a888"; SKIN_DD = "#e0906c"; SKIN_PALE = "#ffd9c4"
KHAKI = "#d9c08a"; KHAKI_D = "#b89a62"; KHAKI_L = "#ecd6a4"
DENIM = "#4a72d6"; DENIM_D = "#3456b0"; DENIM_L = "#6f92e8"
SWEAT = "#aaa6bf"; SWEAT_D = "#8c88a6"; SWEAT_L = "#c4c0d6"
NAVY = "#24307a"; NAVY_D = "#18205a"
GOLD = "#ffd23a"; GOLD_D = "#d9901a"
LEAF = "#3fdc6e"; LEAF_D = "#1f9e4a"
BELT = "#5a3418"; LEATHER = "#8a4a26"
COW_K = "#241a30"
TEE = "#ece6f4"; TEE_D = "#cfc6e0"
BLACK = "#20182c"; LENS = "#2a1f45"

DAD_TINT = {'pink': PINK, 'blue': BLUE, 'mint': MINT, 'yellow': YEL}


# ---------------------------------------------------------------- shared helpers
def named(asset, fn, **kw):
    """Build, then prefix every descendant name with the asset name."""
    def build(kit, root):
        fn(kit, root, **kw)
        for ob in root.children_recursive:
            ob.name = f"{asset} {re.sub(r'[.][0-9]{3}$', '', ob.name)}"
    return build


def set_root_matrix(root, ob, loc, rotm):
    bpy.context.view_layer.update()
    ob.matrix_world = root.matrix_world @ Matrix.Translation(Vector(loc)) @ rotm.to_4x4()


def surf_y(pts, rad, x, z, side=-1, pad=0.0):
    """y of a Z-running tube's surface at lateral x and height z (side -1 = front, +1 = back) plus pad."""
    i = max(0, min(len(pts) - 2, next((j for j in range(len(pts) - 1) if z <= pts[j + 1][2]), len(pts) - 2)))
    t = max(0.0, min(1.0, (z - pts[i][2]) / (pts[i + 1][2] - pts[i][2])))
    cy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
    r0 = rad[i] if not isinstance(rad[i], (int, float)) else (rad[i], rad[i])
    r1 = rad[i + 1] if not isinstance(rad[i + 1], (int, float)) else (rad[i + 1], rad[i + 1])
    rx = r0[0] + (r1[0] - r0[0]) * t
    ry = r0[1] + (r1[1] - r0[1]) * t
    return cy + side * (ry + pad) * math.sqrt(max(0.0, 1 - (x / (rx + pad)) ** 2))


def surf_r(pts, rad, z):
    """(rx, ry, cy) of a Z-running tube at height z."""
    i = max(0, min(len(pts) - 2, next((j for j in range(len(pts) - 1) if z <= pts[j + 1][2]), len(pts) - 2)))
    t = max(0.0, min(1.0, (z - pts[i][2]) / (pts[i + 1][2] - pts[i][2])))
    r0 = rad[i] if not isinstance(rad[i], (int, float)) else (rad[i], rad[i])
    r1 = rad[i + 1] if not isinstance(rad[i + 1], (int, float)) else (rad[i + 1], rad[i + 1])
    return (r0[0] + (r1[0] - r0[0]) * t, r0[1] + (r1[1] - r0[1]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t)


def lathe(kit, name, prof, mat, parent=None, sides=8, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True, closed=False,
          scale_y=1.0):
    """Surface of revolution around local Z. prof = [(r, z)] (r == 0 makes a pole). closed=True joins the last profile
    point back to the first (brims, rings) and recalculates normals outward."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    angs = [-math.pi + 2 * math.pi * (k + 0.5) / sides for k in range(sides)]
    rings = []
    for r, z in prof:
        if r == 0:
            rings.append(bm.verts.new((0, 0, z)))
        else:
            rings.append([bm.verts.new((math.sin(a) * r, -math.cos(a) * r * scale_y, z)) for a in angs])
    n = len(prof)
    V = [min(0.995, max(0.005, i / max(1, n - 1))) for i in range(n)]
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if closed else [])
    for i, j in pairs:
        A, B = rings[i], rings[j]
        if not isinstance(A, list) and not isinstance(B, list):
            continue
        for k in range(sides):
            k2 = (k + 1) % sides
            u0, u1 = k / sides, (k + 1) / sides
            if isinstance(A, list) and isinstance(B, list):
                vs, uvs = (A[k], A[k2], B[k2], B[k]), ((u0, V[i]), (u1, V[i]), (u1, V[j]), (u0, V[j]))
            elif isinstance(B, list):
                vs, uvs = (A, B[k2], B[k]), (((u0 + u1) / 2, V[i]), (u1, V[j]), (u0, V[j]))
            else:
                vs, uvs = (A[k], A[k2], B), ((u0, V[i]), (u1, V[i]), ((u0 + u1) / 2, V[j]))
            fc = bm.faces.new(vs)
            for lp, c in zip(fc.loops, uvs):
                lp[uvl].uv = c
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth)


def torus(kit, name, R, r, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), seg=10, sides=6, smooth=True):
    """Ring around local Z (donut, wristband): seg segments around, sides around the tube."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new(((R + r * math.cos(b)) * c, (R + r * math.cos(b)) * s, r * math.sin(b)))
                      for b in (2 * math.pi * k / sides for k in range(sides))])
    for i in range(seg):
        A, B = rings[i], rings[(i + 1) % seg]
        for k in range(sides):
            k2 = (k + 1) % sides
            fc = bm.faces.new((A[k], B[k], B[k2], A[k2]))
            for lp, c in zip(fc.loops, ((i / seg, k / sides), ((i + 1) / seg, k / sides), ((i + 1) / seg, (k + 1) / sides),
                                        (i / seg, (k + 1) / sides))):
                lp[uvl].uv = (min(0.995, max(0.005, c[0])), min(0.995, max(0.005, c[1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth)


FONT2 = dict(FONT)
FONT2.update({'0': ("###", "#.#", "#.#", "#.#", "###"), '2': ("##.", "..#", ".#.", "#..", "###"),
              '4': ("#.#", "#.#", "###", "..#", "..#"), '5': ("###", "#..", "##.", "..#", "##."),
              '6': (".##", "#..", "###", "#.#", "###"), '7': ("###", "..#", ".#.", ".#.", ".#."),
              '8': ("###", "#.#", "###", "#.#", "###"), '9': ("###", "#.#", "###", "..#", "##."),
              'J': ("..#", "..#", "..#", "#.#", ".#."), 'Q': (".#.", "#.#", "#.#", "##.", ".##"),
              '$': (".##", "##.", ".#.", ".##", "##."), '-': ("...", "...", "###", "...", "..."),
              '.': ("...", "...", "...", "...", ".#."), ':': ("...", ".#.", "...", ".#.", "...")})


def txt(c, s, x, y, col, k=1, shadow=None):
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


# ---------------------------------------------------------------- face textures
def tex_face(skin, hair=None, back=20, eyes='normal', brows=None, brow_tilt=0, mouth='smile', nose=None,
             blush="#ff8fae", stubble=None, bags=False, freckles=False, bangs=None, extra=None, ears=True):
    """64x64 head texture (x = 32 faces -Y). hair: crown + back down to row `back`; bangs: (row, color) fringe."""
    c = Canvas(64, 64, skin)
    shade = hex_scale(skin, 0.88)
    if hair:
        c.rect(0, 47, 63, 63, hair)
        for x in range(64):
            if x < 17 or x > 47:
                c.rect(x, back + (x * 7) % 3, x, 47, hair)
        c.rect(17, 36, 19, 47, hair); c.rect(45, 36, 47, 47, hair)
        c.dots([(24, 46), (25, 45), (30, 45), (31, 44), (36, 45), (37, 46), (40, 45)], hair)
        if bangs:
            row, col = bangs
            for x in range(20, 45):
                c.rect(x, row - (x % 3 == 0) - (x % 5 == 1), x, 47, col)
    if ears:
        c.rect(16, 29, 17, 36, hex_scale(skin, 0.86)); c.rect(47, 29, 48, 36, hex_scale(skin, 0.86))
    if stubble:
        for y in range(16, 31):
            for x in range(19, 46):
                if (x * 7 + y * 13) % 5 == 0 and not (27 <= x <= 36 and 23 <= y <= 27):
                    c.set(x, y, stubble)
    bc = brows or hair or HAIR
    if eyes != 'none':
        for i, x0 in enumerate((25, 35)):
            t = brow_tilt if i == 0 else -brow_tilt
            for q in range(4):
                c.set(x0 + q, 41 + (t * (q - 1.5) / 3 > 0.4) - (t * (q - 1.5) / 3 < -0.4), bc)
    for i, x0 in enumerate((25, 35)):
        if eyes == 'normal':
            c.rect(x0, 35, x0 + 3, 38, WHITE); c.rect(x0 + 1, 35, x0 + 2, 38, INK); c.set(x0 + 2, 38, WHITE)
        elif eyes == 'tired':
            c.rect(x0, 35, x0 + 3, 37, WHITE); c.rect(x0 + 1, 35, x0 + 2, 37, INK); c.set(x0 + 2, 37, WHITE)
            c.rect(x0, 38, x0 + 3, 38, hex_scale(skin, 0.74))
            c.rect(x0, 33, x0 + 3, 33, hex_scale(skin, 0.8)); c.rect(x0 + 1, 32, x0 + 2, 32, hex_scale(skin, 0.86))
        elif eyes == 'kid':
            c.rect(x0, 33, x0 + 3, 38, INK)
            for q in ((x0, 33), (x0 + 3, 33), (x0, 38), (x0 + 3, 38)):
                c.set(*q, skin)
            c.rect(x0 + 2, 36, x0 + 2, 37, WHITE); c.set(x0 + 1, 34, "#6a5aa8")
        elif eyes == 'smug':
            c.rect(x0, 35, x0 + 3, 37, WHITE); c.rect(x0 + 2, 35, x0 + 3, 36, INK)
            c.rect(x0 - 1, 37, x0 + 4, 38, hex_scale(skin, 0.7))
        elif eyes == 'sick':
            c.rect(x0, 35, x0 + 3, 38, WHITE); c.rect(x0 + 1, 35, x0 + 2, 37, INK)
            c.rect(x0 - 1, 33, x0 + 4, 33, hex_scale(skin, 0.78)); c.rect(x0 - 1, 39, x0 + 4, 39, hex_scale(skin, 0.8))
    if nose:
        c.rect(30, 30, 33, 32, nose)
    else:
        c.dots([(31, 31), (32, 31), (32, 32)], hex_scale(skin, 0.86))
    if blush:
        c.rect(22, 29, 24, 31, blush); c.rect(39, 29, 41, 31, blush)
    if freckles:
        c.dots([(23, 32), (25, 31), (39, 32), (41, 31), (24, 30), (40, 30)], hex_scale(skin, 0.72))
    lip, dark = "#ff6f8f", "#8a1f3d"
    if mouth == 'smile':
        c.rect(28, 25, 35, 25, dark); c.rect(29, 24, 34, 24, lip); c.dots([(27, 26), (36, 26)], dark)
        c.rect(29, 25, 34, 25, WHITE); c.rect(28, 26, 35, 26, dark)
    elif mouth == 'tired':
        c.rect(28, 25, 35, 25, dark); c.dots([(27, 24), (36, 24)], dark); c.rect(29, 24, 34, 24, hex_scale(skin, 0.8))
    elif mouth == 'grin':
        c.rect(27, 23, 36, 27, dark); c.rect(28, 26, 35, 27, WHITE); c.rect(29, 23, 34, 24, lip)
        c.dots([(26, 28), (37, 28)], dark)
    elif mouth == 'gap':
        c.rect(27, 23, 36, 27, dark); c.rect(28, 26, 35, 27, WHITE); c.rect(31, 26, 32, 27, dark)
        c.rect(29, 23, 34, 24, lip); c.dots([(26, 28), (37, 28)], dark)
    elif mouth == 'smirk':
        c.rect(28, 25, 33, 25, dark); c.rect(34, 26, 36, 26, dark); c.set(37, 27, dark)
    elif mouth == 'o':
        c.rect(29, 22, 34, 27, dark); c.rect(30, 23, 33, 26, "#c0305a"); c.rect(30, 22, 33, 22, lip)
    elif mouth == 'frown':
        c.rect(28, 24, 35, 24, dark); c.dots([(27, 23), (36, 23)], dark)
    elif mouth == 'flat':
        c.rect(28, 25, 35, 25, dark)
    if extra:
        extra(c)
    return c


def tex_hand(skin, tan=False, nails=True):
    """16x16 hand: v = 0 at the wrist. tan=True paints the pale ring tan line on the ring finger."""
    c = Canvas(16, 16, skin)
    for x in (2, 6, 10, 14):
        c.rect(x, 9, x, 15, hex_scale(skin, 0.86))
    c.rect(0, 0, 15, 1, hex_scale(skin, 0.92))
    if tan:
        c.rect(9, 10, 12, 11, "#fff4ea")
        c.rect(1, 10, 4, 11, "#fff4ea")
    return c


# ---------------------------------------------------------------- body builder
HEAD_PTS = [(0, 0, 0), (0, 0, 0.05), (0, -0.005, 0.08), (0, -0.01, 0.13), (0, -0.005, 0.19), (0, 0, 0.25),
            (0, 0.005, 0.29), (0, 0.005, 0.31)]
HEAD_RAD = [0.048, 0.054, (0.078, 0.085), (0.1, 0.106), (0.106, 0.112), (0.098, 0.104), (0.07, 0.075), (0.03, 0.035)]


def head_mesh(kit, piv, name, mat, s=1.0, w=1.0, jowl=0.0, neck=1.0):
    pts = [(x * s, y * s, z * s) for x, y, z in HEAD_PTS]
    rad = []
    for i, r in enumerate(HEAD_RAD):
        rx, ry = (r, r) if isinstance(r, (int, float)) else r
        k = s * (neck if i < 2 else w) * (1 + (jowl if i in (2, 3) else jowl * 0.4 if i == 4 else 0))
        rad.append((rx * k, ry * k))
    tube(kit, name, pts, rad, mat, piv, bulge=(0, 0.01 * s))
    return pts, rad


class Rig:
    pass


def arm(kit, parent, name, side, loc, L1, L2, radii, t_arm, t_hand, splay=6.0, bend=12.0, hand_s=1.0, sides=6,
        twist=0.0):
    """Shoulder pivot with axes aligned to the parent; the arm hangs along -Z, the elbow bends the forearm forward by
    `bend` degrees. Returns (pivot, wrist, forearm direction, palm socket position)."""
    piv = kit.empty(f"arm {name}", parent, loc, (0, -side * splay, twist))
    E = Vector((0, 0, -L1))
    b = math.radians(bend)
    d2 = Vector((0, -math.sin(b), -math.cos(b)))
    W = E + d2 * L2
    r0, r1, r2 = radii
    tube(kit, f"arm {name}", [(0, 0, r0 * 0.4), (0, 0, -L1 * 0.5), tuple(E), tuple(E + d2 * L2 * 0.5), tuple(W)],
         [r0, r0 * 0.9, r1, r1 * 0.92, r2], t_arm, piv, sides=sides, side=(1, 0, 0), bulge=(r0 * 0.4, 0))
    hs = hand_s
    fwd = Vector((0, -math.cos(b), math.sin(b)))
    tube(kit, f"hand {name}", [tuple(W - d2 * 0.012 * hs), tuple(W + d2 * 0.05 * hs), tuple(W + d2 * 0.1 * hs)],
         [(0.024 * hs, 0.036 * hs), (0.029 * hs, 0.045 * hs), (0.021 * hs, 0.033 * hs)], t_hand, piv, sides=6,
         side=(1, 0, 0), bulge=(0, 0.014 * hs))
    tube(kit, f"thumb {name}", [tuple(W + d2 * 0.015 * hs + fwd * 0.026 * hs - Vector((side * 0.006 * hs, 0, 0))),
                                tuple(W + d2 * 0.055 * hs + fwd * 0.045 * hs - Vector((side * 0.01 * hs, 0, 0)))],
         [0.0125 * hs, 0.0105 * hs], t_hand, piv, sides=5, bulge=(0, 0.008 * hs))
    palm = W + d2 * 0.055 * hs - Vector((side * 0.012 * hs, 0, 0))
    kit.empty(f"socket hand {name}", piv, tuple(palm), (0, side * splay, -twist))
    return piv, W, d2, palm


def leg(kit, parent, name, side, loc, radii, t_leg, shoe, splay=2.0):
    """Hip pivot; leg tube down to the ankle; shoe(kit, piv, name, ground_z) builds the foot (ground_z in pivot space)."""
    piv = kit.empty(f"leg {name}", parent, loc, (0, -side * splay, 0))
    g = -loc[2]
    L = -g - 0.09
    tube(kit, f"leg {name}", [(0, 0, 0.04), (0, 0, -L * 0.28), (0, -0.01, -L * 0.53), (0, 0, -L * 0.78), (0, 0, -L)],
         radii, t_leg, piv, sides=6)
    shoe(kit, piv, name, g)
    return piv


def sneaker(mat, s=1.0, sole=None, chunky=1.0):
    def build(kit, piv, name, g):
        ry = 0.046 * s * chunky
        tube(kit, f"shoe {name}", [(0, 0.05 * s, g + ry), (0, -0.03 * s, g + ry + 0.004), (0, -0.125 * s * chunky, g + ry * 0.72)],
             [(0.05 * s * chunky, ry * 0.9), (0.056 * s * chunky, ry), (0.044 * s * chunky, ry * 0.66)], mat, piv, sides=6,
             front=(0, 0, 1), bulge=(0.015 * s, 0.03 * s))
        if sole:
            tbox(kit, f"sole {name}", (0, -0.035 * s * chunky, g + 0.012 * chunky), (0.11 * s * chunky, 0.23 * s * chunky,
                                                                                      0.024 * chunky), sole, piv)
    return build


def body(kit, root, B, T):
    """B: proportions. T: materials (head, torso, armL, armR, handL, handR, legL, legR, shoeL, shoeR)."""
    rig = Rig()
    tube(kit, "torso", B['tp'], B['tr'], T['torso'], root, sides=B.get('torso_sides', 8))
    rig.tp, rig.tr = B['tp'], B['tr']
    rig.head = kit.empty("head pivot", root, B['head'])
    rig.hp, rig.hr = head_mesh(kit, rig.head, "head", T['head'], B['hs'], B.get('hw', 1.0), B.get('jowl', 0.0),
                               B.get('neck', 1.0))
    rig.hs = B['hs']
    rig.legs = {}
    for side, nm in ((1, "L"), (-1, "R")):
        rig.legs[nm] = leg(kit, root, nm, side, (side * B['hip_x'], 0, B['hip_z']), B['lr'], T['leg' + nm], T['shoe' + nm],
                           B.get('leg_splay', 2.0))
    rig.arms = {}
    sx, sy, sz = B['sh']
    for side, nm in ((1, "L"), (-1, "R")):
        rig.arms[nm] = arm(kit, root, nm, side, (side * sx, sy, sz), B['L1'], B['L2'], B['ar'], T['arm' + nm],
                           T['hand' + nm], B.get('splay', 6.0), B.get('bend' + nm, 12.0), B.get('hand_s', 1.0),
                           B.get('arm_sides', 6), B.get('twist' + nm, 0.0))
    return rig


def head_front(rig, z, x=0.0, pad=0.0):
    return surf_y(rig.hp, rig.hr, x, z, -1, pad)


def head_top(rig):
    return rig.hp[-1][2] + 0.01 * rig.hs


# ---------------------------------------------------------------- hats and face props
def cap(kit, rig, name, crown_mat, bill_mat, backwards=False, z0=0.2, tilt=-6, lift=1.0, band=None):
    s = rig.hs
    piv = kit.empty(name, rig.head, (0, -0.004 * s, z0 * s), (tilt if not backwards else -tilt, 0, 180 if backwards else 0))
    lathe(kit, f"{name} crown", [(0.113 * s, 0.0), (0.118 * s, 0.05 * s), (0.112 * s, 0.09 * s * lift),
                                 (0.08 * s, 0.13 * s * lift), (0.03 * s, 0.148 * s * lift), (0, 0.152 * s * lift)],
          crown_mat, piv, sides=8)
    lathe(kit, f"{name} bill", [(0.0, 0.006 * s), (0.1 * s, 0.006 * s), (0.1 * s, -0.004 * s), (0, -0.002 * s)], bill_mat,
          piv, sides=8, loc=(0, -0.112 * s, 0.006 * s), closed=True, scale_y=0.78)
    tube(kit, f"{name} button", [(0, 0, 0.148 * s * lift), (0, 0, 0.162 * s * lift)], 0.012 * s, bill_mat, piv, sides=4)
    if band:
        tube(kit, f"{name} snap", [(0, 0.11 * s, 0.012 * s), (0, 0.124 * s, 0.012 * s)], [(0.035 * s, 0.012 * s)] * 2, band,
             piv, sides=4, side=(1, 0, 0))
    return piv


def shades(kit, rig, name, frame, lens, z=0.178, aviator=False, w=1.0):
    s = rig.hs
    y = head_front(rig, z * s, 0.0, 0.0) - 0.006 * s
    piv = kit.empty(name, rig.head, (0, y, z * s))
    for sx in (1, -1):
        x = sx * 0.042 * s * w
        yy = head_front(rig, z * s, x, 0.0) - y - 0.01 * s
        if aviator:
            tbox(kit, f"{name} lens {sx}", (x, yy, -0.008 * s), (0.056 * s * w, 0.012 * s, 0.05 * s), lens, piv,
                 taper=(1.25, 1.0), rot=(0, 0, sx * -8))
        else:
            tbox(kit, f"{name} lens {sx}", (x, yy, 0), (0.058 * s * w, 0.014 * s, 0.036 * s), lens, piv, rot=(0, 0, sx * -8))
        tbox(kit, f"{name} arm {sx}", (sx * 0.1 * s * w, 0.04 * s, 0.006 * s), (0.008 * s, 0.11 * s, 0.008 * s), frame, piv)
    tbox(kit, f"{name} bridge", (0, -0.004 * s, 0.012 * s), (0.11 * s * w, 0.01 * s, 0.01 * s), frame, piv)
    return piv


def nose(kit, rig, mat, z=0.148, r=(0.02, 0.026, 0.024), dy=0.0):
    s = rig.hs
    y = head_front(rig, z * s)
    lowball(kit, "nose", (0, y - r[1] * s * 0.35 + dy * s, z * s), tuple(v * s for v in r), mat, rig.head)


def ears(kit, rig, mat, z=0.16, size=1.0):
    s = rig.hs
    for sx in (1, -1):
        rx, _, cy = surf_r(rig.hp, rig.hr, z * s)
        lowball(kit, f"ear {sx}", (sx * (rx - 0.004 * s), cy + 0.004 * s, z * s), (0.016 * s * size, 0.028 * s * size,
                                                                                   0.034 * s * size), mat, rig.head)


def mustache(kit, rig, mat, z=0.128, w=0.07, r=0.016, droop=0.022, jit=0.0):
    s = rig.hs
    pts = []
    for k in range(7):
        t = (k - 3) / 3
        x = t * w * s
        zz = z * s - droop * s * abs(t) ** 1.5 + 0.004 * s * (1 - abs(t))
        pts.append((x, head_front(rig, zz, x * 0.95) - r * s * 0.35, zz))
    rr = [(r * s * (0.55 + 0.45 * (1 - abs((k - 3) / 3) ** 2)), r * s * 0.8 * (0.6 + 0.4 * (1 - abs((k - 3) / 3))))
          for k in range(7)]
    return tube(kit, "mustache", pts, rr, mat, rig.head, sides=6)


def jaw_beard(kit, rig, mat, z=0.08, w=0.085, depth=0.03, jag=0.0):
    """Beard: a thick tube hugging the jaw from ear to ear, with the chin pushed down."""
    s = rig.hs
    pts, rr = [], []
    for k in range(9):
        t = (k - 4) / 4
        a = t * math.radians(80)
        x = math.sin(a) * w * s
        zz = z * s + (0.05 * s) * abs(t) ** 1.6
        y = head_front(rig, zz, x * 0.95) + depth * s * 0.25
        pts.append((x, y, zz - (0.012 * s if k == 4 else 0)))
        rr.append((depth * s * (0.9 - 0.3 * abs(t)), depth * s * (1.0 - 0.45 * abs(t))))
    ob = tube(kit, "beard", pts, rr, mat, rig.head, sides=6, front=(0, 0, -1))
    if jag:
        R = kit.rand
        for v in ob.data.vertices:
            v.co += Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 0.3))) * jag * s
    return ob


def hair_tuft(kit, rig, name, mat, pts, rad):
    s = rig.hs
    return tube(kit, name, [tuple(v * s for v in p) for p in pts], [r * s if isinstance(r, (int, float)) else (r[0] * s, r[1] * s)
                                                                  for r in rad], mat, rig.head, sides=5)


def sockets_npc(kit, root, rig, mouth=True, bubble=True):
    bpy.context.view_layer.update()
    top = (root.matrix_world.inverted() @ rig.head.matrix_world @ Vector((0, 0, head_top(rig)))).z
    if bubble:
        kit.empty("socket bubble", root, (0, 0, top + 0.35))
    if mouth:
        z = 0.12 * rig.hs
        kit.empty("socket mouth", rig.head, (0, head_front(rig, z) - 0.01, z))


# ---------------------------------------------------------------- dad proportions
DAD = dict(hip_z=0.87, hip_x=0.095,
           lr=[(0.088, 0.094), 0.078, 0.062, 0.055, 0.047],
           tp=[(0, 0.0, 0.8), (0, -0.022, 0.9), (0, -0.05, 1.02), (0, -0.04, 1.15), (0, -0.01, 1.26), (0, 0.012, 1.35),
               (0, 0.02, 1.44)],
           tr=[(0.168, 0.13), (0.186, 0.162), (0.194, 0.188), (0.184, 0.168), (0.186, 0.132), (0.205, 0.122),
               (0.088, 0.074)],
           head=(0, -0.012, 1.425), hs=1.14, hw=1.03, jowl=0.06,
           sh=(0.205, 0.016, 1.345), L1=0.29, L2=0.26, ar=(0.076, 0.062, 0.047), splay=7.0, bendL=14.0, bendR=14.0)


def dad_proportions(**kw):
    B = dict(DAD)
    B.update(kw)
    return B


def tex_dad_arm(sleeve, sleeve_row, skin, hair_col, trim=None, cuff=None, sun=None, rows=None):
    c = Canvas(16, 32, skin)
    if sun:
        c.rect(0, sleeve_row + 1, 15, 31, sun)
    c.rect(0, 0, 15, sleeve_row, sleeve)
    if trim:
        c.rect(0, sleeve_row, 15, sleeve_row, trim)
    for i, (x, y) in enumerate(((2, 15), (5, 18), (9, 16), (12, 20), (3, 22), (7, 24), (11, 26), (14, 23), (1, 27),
                                (6, 28), (10, 21), (13, 17))):
        if y > sleeve_row + 2:
            c.set(x, y, hair_col)
    if cuff:
        c.rect(0, 28, 15, 31, cuff)
    if rows:
        rows(c)
    return c


def tex_legs(base, shade, rows_fn):
    c = Canvas(16, 32, base)
    c.speckle(random.Random(3), [shade], 30)
    rows_fn(c)
    return c


def cuff_tube(kit, piv, name, z0, z1, r0, r1, mat):
    tube(kit, name, [(0, -0.004, z0), (0, -0.006, z1)], [r0, r1], mat, piv, sides=6, caps=(False, False))


def hem(kit, rig, root, name, z_top, z_bot, mat, flare=1.08, pad=0.01):
    rx0, ry0, cy0 = surf_r(rig.tp, rig.tr, z_top)
    rx1, ry1, cy1 = surf_r(rig.tp, rig.tr, z_bot)
    tube(kit, name, [(0, cy0, z_top), (0, cy1 - 0.004, z_bot)],
         [(rx0 + pad, ry0 + pad), (rx1 * flare + pad, ry1 * flare + pad)], mat, root, sides=8, caps=(False, False))


def belly_y(rig, z, x=0.0, pad=0.0):
    return surf_y(rig.tp, rig.tr, x, z, -1, pad)


# ---------------------------------------------------------------- Dad Pink: Hawaiian shirt, cargo shorts, socks + sandals
def tex_hawaii(rand, w=64, h=64, base=PINK):
    c = Canvas(w, h, base)
    c.speckle(rand, ["#ff6fb5"], w * h // 30)
    for _ in range(w * h // 110):
        x, y = rand.randrange(w), rand.randrange(h)
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1)):
            c.set(x + dx * 2, y + dy, LEAF if (dx + dy) % 2 else "#2fbf5a")
    for _ in range(w * h // 70):
        x, y = rand.randrange(w), rand.randrange(h)
        col = rand.choice((YEL, YEL, WHITE, ORNG))
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            c.set(x + dx, y + dy, col)
        c.set(x, y, ORNG if col != ORNG else YEL)
    return c


def tex_pink_torso(rand):
    c = tex_hawaii(rand)
    c.rect(0, 0, 63, 3, KHAKI); c.rect(0, 2, 63, 2, KHAKI_D)   # shorts waist peeking below the hem
    for y in range(4, 58, 6):
        c.set(32, y, WHITE)
    c.rect(31, 4, 31, 45, "#e83a8f")
    # open collar: V of skin with chest hair, lapels
    for y in range(46, 64):
        half = (y - 46) // 2 + 1
        c.rect(32 - half, y, 32 + half, y, SKIN)
        c.set(32 - half - 1, y, "#ffd0e8"); c.set(32 + half + 1, y, "#ffd0e8")
        c.set(32 - half - 2, y, "#ffd0e8"); c.set(32 + half + 2, y, "#ffd0e8")
    c.dots([(31, 52), (33, 54), (30, 55), (32, 57), (34, 56), (31, 59), (33, 50)], HAIR)
    c.rect(0, 62, 63, 63, "#ffd0e8"); c.rect(26, 62, 38, 63, SKIN)
    return c


def build_dad_pink(kit, root):
    R = kit.rand
    sun = "#ff9c8a"
    t_head = tex_mat("pink dad head", tex_face(SKIN, "#c08a5a", back=22, eyes='tired', mouth='grin', nose="#ff6a6a",
                                                blush="#ff8a8a", brow_tilt=1, freckles=True))
    t_shirt = tex_mat("hawaiian shirt", tex_pink_torso(R))
    t_arm = tex_mat("pink dad arm", tex_dad_arm("#ff4fa3", 9, SKIN, SKIN_D, trim="#ff8fc8", sun=None,
                                                rows=lambda c: [c.set(x, y, YEL) for x, y in ((3, 3), (10, 6), (7, 1), (13, 4))]))

    def leg_rows(c):
        c.rect(0, 0, 15, 12, KHAKI); c.rect(0, 12, 15, 12, KHAKI_D)
        c.rect(0, 20, 15, 31, WHITE); c.rect(0, 22, 15, 23, PINK); c.rect(0, 25, 15, 25, BLUE)
        c.rect(0, 20, 15, 20, "#e6dcd2")
    t_leg = tex_mat("pink dad leg", tex_legs(SKIN, SKIN_D, leg_rows))
    sock = solid(kit, "tube sock", WHITE, 0.35, shade="#e6dcd2")
    sandal = solid(kit, "sandal", LEATHER, 0.3, shade="#6e3a1e")

    def sandal_shoe(kit, piv, name, g):
        sneaker(sock, 0.95)(kit, piv, name, g + 0.02)
        tbox(kit, f"sandal sole {name}", (0, -0.03, g + 0.012), (0.12, 0.25, 0.024), sandal, piv)
        for i, y in enumerate((-0.09, -0.02)):
            tbox(kit, f"sandal strap {name} {i}", (0, y, g + 0.05), (0.118, 0.026, 0.02), sandal, piv, rot=(0, 0, 0))
    B = dad_proportions()
    T = dict(head=t_head, torso=t_shirt, armL=t_arm, armR=t_arm, handL=tex_mat("dad hand tan", tex_hand(SKIN, True)),
             handR=tex_mat("dad hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=sandal_shoe, shoeR=sandal_shoe)
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    nose(kit, rig, solid(kit, "sunburn nose", "#ff6a6a", 0.42), r=(0.022, 0.028, 0.026))
    ears(kit, rig, skin)
    kit.empty("socket camera", rig.head, (0, -0.1 * rig.hs, 0.18 * rig.hs))
    # untucked shirt hem, short sleeves flare
    hem(kit, rig, root, "shirt hem", 0.9, 0.78, tex_mat("hawaiian hem", tex_hawaii(R, 64, 16)), flare=1.06)
    for nm in ("L", "R"):
        piv = rig.arms[nm][0]
        tube(kit, f"sleeve {nm}", [(0, 0, 0.04), (0, 0, -0.16)], [(0.078, 0.078), (0.08, 0.078)],
             tex_mat("hawaiian sleeve", tex_hawaii(R, 32, 16)), piv, sides=6, caps=(True, False))
    # cargo shorts openings with side pockets
    shorts = solid(kit, "cargo shorts", KHAKI, shade=KHAKI_D)
    for side, nm in ((1, "L"), (-1, "R")):
        piv = rig.legs[nm]
        cuff_tube(kit, piv, f"shorts {nm}", 0.02, -0.36, (0.104, 0.108), (0.096, 0.1), shorts)
        tbox(kit, f"cargo pocket {nm}", (side * 0.1, -0.005, -0.22), (0.03, 0.11, 0.12), solid(kit, "cargo pocket", KHAKI_L,
                                                                                            shade=KHAKI), piv)
    # bucket hat
    hat = solid(kit, "bucket hat", "#f2e6c4", shade="#e0d0a8")
    s = rig.hs
    hp = kit.empty("bucket hat", rig.head, (0, 0.006 * s, 0.222 * s), (-8, 0, 0))
    lathe(kit, "bucket hat crown", [(0.118 * s, 0.0), (0.12 * s, 0.07 * s), (0.106 * s, 0.135 * s), (0.08 * s, 0.155 * s),
                                    (0, 0.16 * s)], hat, hp, sides=8)
    lathe(kit, "bucket hat band", [(0.122 * s, 0.006 * s), (0.123 * s, 0.03 * s)], solid(kit, "hat band", PINK), hp, sides=8)
    lathe(kit, "bucket hat brim", [(0.115 * s, 0.01 * s), (0.185 * s, -0.018 * s), (0.185 * s, -0.028 * s), (0.112 * s, -0.004 * s)],
          hat, hp, sides=10, closed=True)
    # fanny pack
    y = belly_y(rig, 0.86)
    fp = kit.empty("fanny pack", root, (0, y - 0.03, 0.86))
    tbox(kit, "fanny pack", (0, 0, 0), (0.2, 0.07, 0.1), solid(kit, "fanny pack", YEL), fp, taper=(0.9, 0.8))
    tbox(kit, "fanny zip", (0, -0.037, 0.02), (0.16, 0.008, 0.012), solid(kit, "fanny zip", MINT), fp)
    rx, ry, cy = surf_r(rig.tp, rig.tr, 0.86)
    tube(kit, "fanny strap", [(0, cy, 0.865), (0, cy, 0.885)], [(rx + 0.012, ry + 0.01)] * 2, solid(kit, "strap", INK, 0.2),
         root, sides=8, caps=(False, False))


# ---------------------------------------------------------------- Dad Blue: tucked polo, pleated khakis, dad sneakers
def tex_blue_torso(rand):
    c = Canvas(64, 64, BLUE)
    c.speckle(rand, ["#2a78ea"], 60, 12, 60)
    c.rect(0, 0, 63, 6, KHAKI); c.speckle(rand, [KHAKI_D], 12, 0, 5)
    for x in (24, 28, 36, 40):
        c.rect(x, 0, x, 5, KHAKI_D)
    c.rect(0, 7, 63, 10, BELT); c.rect(0, 10, 63, 10, "#3a2010")
    c.rect(29, 6, 35, 11, GOLD); c.rect(31, 7, 33, 10, BELT)
    for y in range(11, 14):   # polo blousing over the belt
        for x in range(0, 64, 3):
            c.set(x + (y % 2), y, "#1f5fd0")
    c.rect(30, 46, 34, 63, "#5aa0ff"); c.rect(32, 46, 32, 63, "#1f5fd0")
    c.dots([(31, 50), (31, 55), (31, 60)], WHITE)
    cone_icon(c, 40, 47, 5, PINK)
    c.rect(0, 62, 63, 63, "#1f5fd0")
    return c


def build_dad_blue(kit, root):
    R = kit.rand
    hair = "#5a3418"
    t_head = tex_mat("blue dad head", tex_face(SKIN, hair, back=18, eyes='tired', mouth='flat', brow_tilt=-1,
                                                stubble=None))
    t_torso = tex_mat("polo torso", tex_blue_torso(R))
    t_arm = tex_mat("polo arm", tex_dad_arm(BLUE, 8, SKIN, SKIN_D, trim=WHITE))

    def leg_rows(c):
        c.rect(0, 0, 15, 12, KHAKI)
        for x in (3, 8, 12):
            c.rect(x, 0, x, 11, KHAKI_D)
        c.rect(0, 12, 15, 12, KHAKI_D)
        c.rect(0, 26, 15, 31, WHITE); c.rect(0, 26, 15, 26, "#e6dcd2")
    t_leg = tex_mat("blue dad leg", tex_legs(SKIN_PALE, "#ffe6d8", leg_rows))
    shoe_m = tex_mat("dad sneaker", sneaker_tex(WHITE, BLUE, "#d9d4ff"))
    sole = solid(kit, "dad sneaker sole", "#e6e0ff", shade="#c9c2f0")
    shoe = sneaker(shoe_m, 1.0, sole, chunky=1.22)
    B = dad_proportions(hip_z=0.875, head=(0, -0.008, 1.43),
                        tr=[(0.17, 0.13), (0.19, 0.17), (0.198, 0.198), (0.186, 0.174), (0.188, 0.134), (0.21, 0.124),
                            (0.088, 0.074)])
    T = dict(head=t_head, torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("dad hand tan", tex_hand(SKIN, True)),
             handR=tex_mat("dad hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    nose(kit, rig, solid(kit, "nose", SKIN_D), r=(0.022, 0.03, 0.026))
    ears(kit, rig, skin)
    mustache(kit, rig, solid(kit, "mustache", hair, 0.3, shade="#3a2010"), w=0.072, r=0.022, droop=0.03)
    kit.empty("socket camera", rig.head, (0, -0.1 * rig.hs, 0.18 * rig.hs))
    s = rig.hs
    # polo collar and sleeves
    pol = solid(kit, "polo", BLUE, shade="#1f5fd0")
    rx, ry, cy = surf_r(rig.tp, rig.tr, 1.4)
    tube(kit, "polo collar", [(0, cy + 0.004, 1.385), (0, cy + 0.01, 1.445)], [(rx + 0.03, ry + 0.028), (0.085, 0.074)], pol,
         root, sides=8, caps=(False, False))
    for sx in (1, -1):
        tbox(kit, f"collar tip {sx}", (sx * 0.035, belly_y(rig, 1.39, sx * 0.035, 0.006), 1.395), (0.05, 0.012, 0.045), pol,
             root, rot=(-20, 0, sx * 28))
    for nm in ("L", "R"):
        tube(kit, f"sleeve {nm}", [(0, 0, 0.04), (0, 0, -0.15)], [(0.077, 0.077), (0.074, 0.074)], pol, rig.arms[nm][0], sides=6,
             caps=(True, False))
        tube(kit, f"sleeve band {nm}", [(0, 0, -0.14), (0, 0, -0.155)], 0.076, solid(kit, "polo band", WHITE), rig.arms[nm][0],
             sides=6, caps=(False, False))
    shorts = solid(kit, "khaki shorts", KHAKI, shade=KHAKI_D)
    for nm in ("L", "R"):
        cuff_tube(kit, rig.legs[nm], f"shorts {nm}", 0.02, -0.355, (0.1, 0.104), (0.098, 0.102), shorts)
    # ball cap with sunglasses pushed up on it
    cp = cap(kit, rig, "ball cap", tex_mat("blue cap", tex_cap(NAVY, WHITE)), solid(kit, "cap bill", NAVY), z0=0.2)
    gl = kit.empty("cap sunglasses", cp, (0, -0.122 * s, 0.07 * s), (-22, 0, 0))
    lens = solid(kit, "lens", LENS, 0.5, shade="#40306a")
    frame = solid(kit, "frame", BLACK, 0.2)
    for sx in (1, -1):
        tbox(kit, f"cap lens {sx}", (sx * 0.04 * s, 0, 0), (0.058 * s, 0.012 * s, 0.036 * s), lens, gl, rot=(0, 0, sx * -8))
        tbox(kit, f"cap glint {sx}", (sx * 0.05 * s, -0.007 * s, 0.008 * s), (0.014 * s, 0.003 * s, 0.008 * s),
             solid(kit, "glint", WHITE, 0.9), gl)
    tbox(kit, "cap bridge", (0, 0, 0.01 * s), (0.11 * s, 0.01 * s, 0.01 * s), frame, gl)
    # cell phone? no: a pen in the polo pocket would be too small; a lanyard whistle reads as coach dad
    tube(kit, "lanyard", [(-0.06, belly_y(rig, 1.36, -0.06, 0.004), 1.36), (-0.03, belly_y(rig, 1.24, -0.03, 0.01), 1.24),
                          (0.0, belly_y(rig, 1.18, 0, 0.012), 1.18), (0.03, belly_y(rig, 1.24, 0.03, 0.01), 1.24),
                          (0.06, belly_y(rig, 1.36, 0.06, 0.004), 1.36)], 0.006, solid(kit, "lanyard", YEL), root, sides=4,
         caps=(False, False))
    tube(kit, "whistle", [(0, belly_y(rig, 1.16, 0, 0.02), 1.16), (0, belly_y(rig, 1.16, 0, 0.02) - 0.05, 1.15)], 0.014,
         solid(kit, "whistle", STEEL, 0.45, shade="#a9a2e0"), root, sides=6)


def sneaker_tex(base, accent, sole):
    c = Canvas(16, 16, base)
    c.rect(4, 3, 11, 9, accent); c.rect(5, 4, 10, 8, base); c.rect(6, 5, 11, 6, accent)
    c.rect(0, 0, 15, 2, sole)
    for y in (11, 13):
        c.rect(6, y, 9, y, "#c9c2f0")
    return c


def tex_cap(base, front, letter=None, col=None):
    c = Canvas(32, 16, base)
    c.rect(10, 2, 21, 14, front)
    if letter:
        txt(c, letter, 14, 12, col or base, 2)
    c.rect(0, 0, 31, 1, hex_scale(base, 0.8))
    return c


# ---------------------------------------------------------------- Dad Mint: fleece vest, jeans, visor, goatee, holster
def tex_mint_torso(rand):
    c = Canvas(64, 64, TEE)
    c.speckle(rand, [TEE_D], 80)
    c.rect(0, 0, 63, 7, DENIM); c.speckle(rand, [DENIM_D], 20, 0, 7)
    c.rect(0, 8, 63, 10, BLACK); c.rect(30, 8, 34, 10, STEEL)
    c.rect(0, 56, 63, 63, TEE_D)
    return c


def tex_vest(rand):
    c = Canvas(64, 32, MINT)
    for y in range(32):
        for x in range(64):
            if (x * 5 + y * 3) % 7 == 0:
                c.set(x, y, "#22d8a8")
    c.rect(32, 0, 32, 31, "#d9d4ff"); c.rect(31, 0, 31, 31, "#12a883")
    c.rect(31, 29, 33, 31, STEEL)
    c.rect(38, 20, 44, 24, "#12a883"); c.rect(39, 21, 43, 23, WHITE)   # chest logo patch
    c.rect(21, 6, 27, 6, "#12a883"); c.rect(37, 6, 43, 6, "#12a883")   # pocket zips
    c.rect(0, 0, 63, 1, "#12a883")
    return c


def build_dad_mint(kit, root):
    R = kit.rand
    hair = "#b8b0c8"
    t_head = tex_mat("mint dad head", tex_face(SKIN, hair, back=20, eyes='tired', mouth='smirk', brows="#8a82a0",
                                                stubble="#d9a888", extra=lambda c: c.rect(27, 27, 36, 28, "#8a82a0")))
    t_torso = tex_mat("mint dad torso", tex_mint_torso(R))
    t_arm = tex_mat("long sleeve arm", tex_dad_arm(TEE, 27, SKIN, SKIN_D, trim=TEE_D,
                                                   rows=lambda c: c.speckle(random.Random(5), [TEE_D], 20, 0, 26)))

    def leg_rows(c):
        c.rect(4, 0, 4, 31, DENIM_D); c.rect(12, 0, 12, 31, DENIM_L)
        c.rect(0, 29, 15, 31, DENIM_D)
        c.rect(6, 12, 9, 15, DENIM_L)
    t_leg = tex_mat("jeans", tex_legs(DENIM, DENIM_D, leg_rows))
    shoe = sneaker(tex_mat("trail shoe", sneaker_tex("#8a82a8", MINT, "#5a5278")), 1.0,
                   solid(kit, "trail sole", "#4a4268", 0.25), 1.08)
    B = dad_proportions(hip_z=0.88, head=(0, -0.01, 1.435), hs=1.05,
                        lr=[(0.09, 0.096), 0.08, 0.066, 0.06, 0.056],
                        tr=[(0.166, 0.128), (0.18, 0.156), (0.186, 0.176), (0.178, 0.16), (0.184, 0.13), (0.2, 0.12),
                            (0.088, 0.074)])
    T = dict(head=t_head, torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("dad hand tan", tex_hand(SKIN, True)),
             handR=tex_mat("dad hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    nose(kit, rig, solid(kit, "nose", SKIN_D))
    ears(kit, rig, skin)
    s = rig.hs
    goatee = solid(kit, "goatee", "#8a82a0", 0.3, shade="#6e6688")
    zc = 0.035 * s
    lowball(kit, "goatee", (0, head_front(rig, 0.09 * s) - 0.004, 0.085 * s), (0.03 * s, 0.022 * s, 0.035 * s), goatee, rig.head)
    kit.empty("socket camera", rig.head, (0, -0.1 * rig.hs, 0.18 * rig.hs))
    # fleece vest shell over the tee with a stand-up collar
    vest = tex_mat("fleece vest", tex_vest(R))
    zs = [0.92, 1.02, 1.15, 1.26, 1.34, 1.4]
    pts, rr = [], []
    for z in zs:
        rx, ry, cy = surf_r(rig.tp, rig.tr, z)
        k = 0.86 if z > 1.3 else 1.0
        pts.append((0, cy, z)); rr.append((rx * k + 0.022, ry + 0.022))
    rr[-1] = (0.1, 0.088)
    tube(kit, "fleece vest", pts, rr, vest, root, sides=8, caps=(False, False))
    tube(kit, "vest collar", [(0, pts[-1][1], 1.4), (0, pts[-1][1] + 0.004, 1.46)], [(0.1, 0.088), (0.092, 0.08)],
         solid(kit, "vest collar", MINT, shade="#22d8a8"), root, sides=8, caps=(False, False))
    # phone holster on the right hip
    hol = kit.empty("phone holster", root, (-0.17, belly_y(rig, 0.83, -0.12, 0.0) + 0.05, 0.8), (0, 0, -35))
    tbox(kit, "holster", (0, 0, 0), (0.035, 0.08, 0.13), solid(kit, "holster", BLACK, 0.2), hol)
    tbox(kit, "phone", (0, 0, 0.07), (0.022, 0.07, 0.03), solid(kit, "phone", "#3a3050", 0.25), hol)
    tbox(kit, "holster clip", (0.02, 0, 0.04), (0.01, 0.03, 0.06), solid(kit, "clip", STEEL), hol)
    # visor
    vp = kit.empty("visor", rig.head, (0, -0.004 * s, 0.2 * s), (-6, 0, 0))
    vband = solid(kit, "visor band", MINT, shade="#22d8a8")
    lathe(kit, "visor band", [(0.114 * s, 0.0), (0.118 * s, 0.0), (0.116 * s, 0.045 * s), (0.11 * s, 0.045 * s)], vband, vp,
          sides=8, closed=True)
    lathe(kit, "visor bill", [(0.0, 0.006 * s), (0.105 * s, 0.006 * s), (0.105 * s, -0.004 * s), (0, -0.002 * s)],
          solid(kit, "visor bill", WHITE), vp, sides=8, loc=(0, -0.11 * s, 0.006 * s), closed=True, scale_y=0.8)
    hair_m = solid(kit, "grey hair", hair, 0.3, shade="#9a92b0")
    lowball(kit, "hair top", (0, 0.004 * s, 0.25 * s), (0.1 * s, 0.105 * s, 0.065 * s), hair_m, rig.head)


# ---------------------------------------------------------------- Dad Yellow: band tee, sweatpants, backwards cap, beard
def tex_yellow_torso(rand):
    F = "#f2d860"
    c = Canvas(64, 64, F)
    c.speckle(rand, ["#fff09a", "#e6c84a"], 160)
    c.rect(0, 0, 63, 3, SWEAT); c.dots([(30, 1), (34, 1), (30, 0), (34, 0)], WHITE)
    txt_c(c, "DAD", 32, 44, PURP, 1)
    txt_c(c, "ROCK", 32, 37, PURP, 1)
    for i, (x, y) in enumerate(((34, 31), (33, 30), (32, 29), (33, 28), (32, 27), (31, 26), (30, 25))):   # bolt
        c.rect(x - 1, y, x, y, RED)
    c.rect(24, 22, 40, 22, PURP)
    # coffee stain on the belly
    for (x, y, r) in ((26, 14, 3), (29, 12, 2), (23, 16, 1), (38, 20, 1)):
        disc(c, x, y, r, "#b8914a")
    c.dots([(27, 15), (25, 13), (30, 11)], "#9a7438")
    c.rect(0, 60, 63, 63, "#e6c84a"); c.rect(28, 60, 36, 63, SKIN)
    return c


def build_dad_yellow(kit, root):
    R = kit.rand
    hair = "#3a2414"
    t_head = tex_mat("yellow dad head", tex_face(SKIN, hair, back=16, eyes='tired', mouth='tired', brow_tilt=1,
                                                  stubble="#8a5a3a", bags=True))
    t_torso = tex_mat("band tee", tex_yellow_torso(R))
    t_arm = tex_mat("band tee arm", tex_dad_arm("#f2d860", 8, SKIN, SKIN_D, trim="#e6c84a"))

    def leg_rows(c):
        c.rect(0, 27, 15, 31, SWEAT_D); c.rect(0, 27, 15, 27, SWEAT_L)
        c.rect(5, 8, 7, 10, "#b8914a")
        c.rect(7, 0, 8, 26, SWEAT_L)
    t_leg = tex_mat("sweatpants", tex_legs(SWEAT, SWEAT_D, leg_rows))
    croc = tex_mat("croc", croc_tex())
    shoe = sneaker(croc, 1.0, None, 1.15)
    B = dad_proportions(hip_z=0.87, head=(0, -0.03, 1.415), hs=1.06, hw=1.04,
                        lr=[(0.096, 0.1), 0.088, 0.072, 0.066, 0.06],
                        tp=[(0, 0.0, 0.8), (0, -0.025, 0.9), (0, -0.055, 1.02), (0, -0.045, 1.15), (0, -0.015, 1.26),
                            (0, 0.01, 1.34), (0, 0.01, 1.43)],
                        tr=[(0.17, 0.13), (0.19, 0.168), (0.198, 0.196), (0.186, 0.174), (0.182, 0.13), (0.198, 0.12),
                            (0.088, 0.074)], sh=(0.2, 0.014, 1.33))
    T = dict(head=t_head, torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("dad hand tan", tex_hand(SKIN, True)),
             handR=tex_mat("dad hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    nose(kit, rig, solid(kit, "nose", SKIN_D), r=(0.024, 0.028, 0.028))
    ears(kit, rig, skin)
    beard_m = solid(kit, "beard", hair, 0.28, shade="#24160c")
    jaw_beard(kit, rig, beard_m, z=0.075, w=0.09, depth=0.032, jag=0.006)
    mustache(kit, rig, beard_m, z=0.128, w=0.05, r=0.014, droop=0.02)
    kit.empty("socket camera", rig.head, (0, -0.1 * rig.hs, 0.18 * rig.hs))
    hem(kit, rig, root, "tee hem", 0.86, 0.79, solid(kit, "tee hem", "#f2d860", shade="#e6c84a"), flare=1.05)
    for nm in ("L", "R"):
        tube(kit, f"sleeve {nm}", [(0, 0, 0.04), (0, 0, -0.14)], [(0.076, 0.076), (0.074, 0.074)],
             solid(kit, "tee sleeve", "#f2d860", shade="#e6c84a"), rig.arms[nm][0], sides=6, caps=(True, False))
    # backwards cap with the hair sticking out the front
    s = rig.hs
    cap(kit, rig, "backwards cap", tex_mat("purple cap", tex_cap(PURP, PURP)), solid(kit, "cap bill", "#6a3fd6"),
        backwards=True, z0=0.2, band=solid(kit, "snap", YEL))
    hm = solid(kit, "hair", hair, 0.28)
    for i, x in enumerate((-0.05, -0.015, 0.02, 0.055)):
        hair_tuft(kit, rig, f"hair tuft {i}", hm, [(x, -0.092, 0.235), (x * 1.1, -0.112, 0.215), (x * 1.2, -0.118, 0.198)],
                  [0.016, 0.012, 0.004])
    # coffee mug drip on the shoe? keep: a sweat stain is enough


def croc_tex():
    c = Canvas(16, 16, ORNG)
    for y in range(4, 15, 3):
        for x in range(1 + (y % 2), 16, 3):
            c.set(x, y, "#c45a1a")
    c.rect(0, 0, 15, 2, "#e0702a")
    return c


# ---------------------------------------------------------------- first-person arms
FP_GUN = (-0.13, -0.52, -0.045)
FP_GUN_ROT = (0, -6, 7)


def tex_dad_forearm():
    """v = 0 at the elbow: short polo sleeve, then hairy forearm skin."""
    c = Canvas(16, 32, SKIN)
    c.rect(0, 0, 15, 6, "#e8e0f4")
    c.speckle(random.Random(4), ["#d4cae6"], 10, 0, 5)
    for (x, y) in ((1, 10), (4, 12), (7, 11), (10, 13), (13, 10), (2, 15), (6, 16), (9, 17), (12, 15), (15, 18), (3, 19),
                   (8, 20), (11, 21), (14, 22), (5, 23), (1, 24), (10, 25), (7, 14), (12, 19), (4, 21)):
        c.set(x, y, "#8a4a26")
        c.set(x, y + 1, "#a8643a")
    c.dots([(3, 17), (11, 21), (6, 23), (13, 18)], "#f0a888")
    c.rect(0, 29, 15, 31, "#ffb994")
    return c


def tex_fist_dad(tan=False):
    c = Canvas(16, 16, SKIN)
    for y in (5, 10):
        c.rect(5, y, 13, y, "#e0906c")
    c.rect(12, 0, 13, 15, "#f2a37f")
    c.dots([(13, 2), (13, 7), (13, 12)], "#ffe0d4")
    c.dots([(5, 3), (5, 8), (5, 13)], "#ffd6bd")
    c.dots([(2, 6), (3, 9), (1, 12), (7, 2)], "#8a4a26")
    c.rect(0, 0, 15, 0, "#f0a888")
    return c


def tex_watch_face():
    c = Canvas(16, 8, "#2a2f3a")
    c.rect(1, 1, 14, 6, "#9cff57")
    txt(c, "12", 2, 6, "#1f5a12")
    c.rect(10, 2, 13, 3, "#1f5a12")
    return c


def build_dad_fp_arms(kit, root):
    """Same rig and placement as the zombie-mode First-Person Arms (camera = root, looking -Y): hairy forearms, short
    polo sleeves (own 'sleeve' material so it can be tinted per player), chunky digital watch on the left wrist and a
    pale ring tan line on the left ring finger."""
    t_fore = tex_mat("dad fp forearm", tex_dad_forearm())
    t_fist = tex_mat("dad fp fist", tex_fist_dad())
    skin = solid(kit, "skin", SKIN)
    sleeve = solid(kit, "fp sleeve", "#e8e0f4", shade="#d4cae6")
    kit.empty("socket camera", root, (0, 0, 0))
    G = Vector(FP_GUN)
    RG = Euler([math.radians(a) for a in FP_GUN_ROT]).to_matrix()

    def arm_(name, wrist_g, elbow_off):
        W = G + RG @ Vector(wrist_g)
        E = W + Vector(elbow_off)
        fore = kit.empty(f"forearm {name}", root, E)
        aim(fore, W - E)
        L = (W - E).length
        zs = [0.03, -0.1, -(L - 0.005)]
        tube(kit, f"forearm {name}", [(0, 0, z) for z in zs], [0.058, 0.05, 0.037], t_fore, fore, sides=8,
             front=(0, 1, 0), bulge=(0.02, 0))
        tube(kit, f"sleeve {name}", [(0, 0, 0.05), (0, 0, -0.035)], [0.074, 0.072], sleeve, fore, sides=8, caps=(True, False))
        tube(kit, f"sleeve band {name}", [(0, 0, -0.03), (0, 0, -0.045)], 0.074, solid(kit, "fp sleeve band", PINK),
             fore, sides=8, caps=(False, False))
        hand = kit.empty(f"hand {name}", fore, (0, 0, -L))
        set_root_matrix(root, hand, W, RG)
        wg = Vector(wrist_g)
        return fore, hand, L, (lambda pts: [tuple(Vector(p) - wg) for p in pts])

    fore_r, hand_r, Lr, gp = arm_("R", (-0.008, 0.112, -0.092), (-0.12, 0.2, -0.15))
    up = Vector((0, -math.sin(math.radians(16)), math.cos(math.radians(16))))
    front = Vector((0, -math.cos(math.radians(16)), -math.sin(math.radians(16))))
    gc = Vector((-0.006, 0.046, -0.065))
    tube(kit, "palm R", gp([(-0.008, 0.112, -0.092), (-0.01, 0.088, -0.078), gc + Vector((-0.008, 0.03, 0.004))]),
         [(0.034, 0.028), (0.04, 0.032), (0.038, 0.032)], skin, hand_r, sides=8, front=(1, 0, 0))
    tube(kit, "fist R", gp([gc - up * 0.05, gc - up * 0.012, gc + up * 0.026]), [(0.034, 0.038), (0.038, 0.044), (0.034, 0.039)],
         t_fist, hand_r, sides=8, front=tuple(front), bulge=(0.012, 0.008))
    tube(kit, "index finger R", gp([(-0.022, 0.014, -0.036), (-0.014, -0.01, -0.043), (-0.003, -0.02, -0.05),
                                    (0.004, -0.012, -0.058)]), [0.012, 0.0115, 0.011, 0.0095], skin, hand_r, sides=6,
         bulge=(0, 0.004))
    tube(kit, "thumb R", gp([(0.018, 0.075, -0.05), (0.029, 0.045, -0.034), (0.031, 0.016, -0.026), (0.029, -0.006, -0.024)]),
         [0.017, 0.014, 0.0115, 0.01], skin, hand_r, sides=6, bulge=(0, 0.005))
    kit.empty("socket hand R", hand_r, tuple(-Vector((-0.008, 0.112, -0.092))))

    fore_l, hand_l, Ll, gp = arm_("L", (0.072, 0.09, -0.15), (0.17, 0.19, -0.12))
    tube(kit, "palm L", gp([(0.072, 0.09, -0.15), (0.054, 0.062, -0.118), (0.045, 0.035, -0.098)]),
         [(0.036, 0.028), (0.042, 0.026), (0.038, 0.022)], skin, hand_l, sides=8, front=(1, 0, 0))
    tan = solid(kit, "tan line", "#fff1e6", 0.45)
    for i in range(4):
        z = -0.078 - 0.019 * i
        x0 = 0.044 - 0.002 * i
        pts = gp([(x0, 0.03, z), (0.03, 0.0, z), (0.004, -0.014, z + 0.002), (-0.024, -0.008, z + 0.003),
                  (-0.04, 0.012 + 0.004 * i, z + 0.003)])
        tube(kit, f"finger L {i}", pts, [0.011, 0.011, 0.011, 0.0102, 0.0092], skin, hand_l, sides=6, bulge=(0, 0.004))
        if i == 2:   # ring finger: pale band where the wedding ring used to be
            a, b = Vector(pts[0]), Vector(pts[1])
            tube(kit, "ring tan line", [tuple(a.lerp(b, 0.55)), tuple(a.lerp(b, 0.85))], 0.0122, tan, hand_l, sides=6,
                 caps=(False, False))
    tube(kit, "thumb L", gp([(0.058, 0.048, -0.084), (0.05, 0.016, -0.06), (0.042, -0.014, -0.046), (0.036, -0.036, -0.042)]),
         [0.017, 0.014, 0.012, 0.0102], skin, hand_l, sides=6, bulge=(0, 0.005))
    kit.empty("socket hand L", hand_l, tuple(Vector((0.045, 0.035, -0.098)) - Vector((0.072, 0.09, -0.15))))
    # chunky digital watch on the left wrist (forearm space, just above the wrist)
    wz = -(Ll - 0.045)
    tube(kit, "watch strap", [(0, 0, wz + 0.018), (0, 0, wz - 0.018)], [0.043, 0.041], solid(kit, "watch strap", BLACK, 0.2),
         fore_l, sides=8, caps=(False, False))
    wp = kit.empty("watch", fore_l, (0, 0, wz))
    tbox(kit, "watch case", (0.0, -0.046, 0), (0.05, 0.022, 0.044), solid(kit, "watch case", "#3a3050", 0.25), wp)
    tbox(kit, "watch face", (0.0, -0.058, 0), (0.038, 0.004, 0.03), tex_mat("watch face", tex_watch_face(), 0.9), wp,
         uv={'all': (0.1, 0.1, 0.2, 0.2), 'ny': (0, 0, 1, 1)})
    for sx in (1, -1):
        tbox(kit, f"watch button {sx}", (sx * 0.028, -0.046, 0), (0.008, 0.01, 0.01), solid(kit, "watch button", STEEL), wp)


# ---------------------------------------------------------------- kids
KID = dict(hip_z=0.47, hip_x=0.062,
           lr=[(0.062, 0.066), 0.054, 0.046, 0.043, 0.04],
           tp=[(0, 0.0, 0.44), (0, -0.012, 0.52), (0, -0.018, 0.6), (0, -0.008, 0.68), (0, 0.0, 0.74), (0, 0.004, 0.79)],
           tr=[(0.118, 0.09), (0.124, 0.1), (0.122, 0.1), (0.12, 0.088), (0.132, 0.084), (0.058, 0.05)],
           head=(0, -0.004, 0.775), hs=1.36, hw=1.04, jowl=0.04, neck=0.7,
           sh=(0.13, 0.004, 0.725), L1=0.17, L2=0.15, ar=(0.044, 0.036, 0.03), splay=8.0, bendL=10.0, bendR=10.0, hand_s=0.75,
           leg_splay=3.0)


def kid_props(**kw):
    B = dict(KID)
    B.update(kw)
    return B


def tex_kid_arm(sleeve, rows, skin, cuff=None, band=None):
    c = Canvas(16, 32, skin)
    c.rect(0, 0, 15, rows, sleeve)
    c.rect(0, rows, 15, rows, hex_scale(sleeve, 0.85))
    if cuff:
        c.rect(0, 28, 15, 31, cuff)
    if band:
        band(c)
    return c


def tex_kid_leg(pants, rows, skin, sock=WHITE, sock_rows=4, extra=None):
    c = Canvas(16, 32, skin)
    c.rect(0, 0, 15, rows, pants)
    c.rect(0, rows, 15, rows, hex_scale(pants, 0.85))
    if sock:
        c.rect(0, 31 - sock_rows, 15, 31, sock)
    if extra:
        extra(c)
    return c


def kid_shoe(kit, name, base, accent):
    return sneaker(tex_mat(name, sneaker_tex(base, accent, "#e6e0ff")), 0.8, solid(kit, "kid sole", WHITE, 0.35), 1.15)


def tex_kid_torso(base, top=None, rows=None, rand=None, waist=None):
    c = Canvas(64, 64, base)
    if waist:
        c.rect(0, 0, 63, 6, waist)
    if rows:
        rows(c)
    c.rect(0, 60, 63, 63, hex_scale(base, 0.85))
    c.rect(27, 59, 37, 63, SKIN if top is None else top)
    return c


def kid_base(kit, root, B, T, skin=SKIN):
    rig = body(kit, root, B, T)
    sm = solid(kit, "kid skin", skin)
    ears(kit, rig, sm, size=0.9)
    return rig


def shorts_cuffs(kit, rig, mat, r=(0.072, 0.076), z1=-0.16):
    for nm in ("L", "R"):
        cuff_tube(kit, rig.legs[nm], f"shorts {nm}", 0.03, z1, r, (r[0] * 0.98, r[1] * 0.98), mat)


def tee_sleeves(kit, rig, mat, ln=0.09, r=0.054):
    for nm in ("L", "R"):
        tube(kit, f"sleeve {nm}", [(0, 0, 0.03), (0, 0, -ln)], [r, r * 0.97], mat, rig.arms[nm][0], sides=6, caps=(True, False))


def kid_hair_cap(kit, rig, mat, z=0.17, back=0.12, tilt=0.0, scale=(1.06, 1.08, 1.0)):
    """Low dome of hair over the crown, a little bigger than the skull."""
    s = rig.hs
    return lathe(kit, "hair cap", [(0.108 * s * scale[0], z * s), (0.106 * s * scale[0], (z + 0.05) * s),
                                    (0.085 * s * scale[0], (z + 0.11) * s), (0.04 * s, (z + 0.145) * s), (0, (z + 0.152) * s)],
                 mat, rig.head, sides=8, loc=(0, 0.006 * s, 0), scale_y=scale[1])


def build_kid_stripes(kit, root):
    hair = "#7a3a1c"
    B = kid_props()

    def stripes(c):
        for y in range(8, 60, 6):
            c.rect(0, y, 63, y + 2, RED)
        c.rect(26, 40, 38, 52, WHITE)
        disc(c, 32, 46, 4, YEL); c.dots([(30, 47), (34, 47)], INK); c.rect(30, 44, 34, 44, INK)
    t_torso = tex_mat("stripe tee", tex_kid_torso(WHITE, rows=stripes, waist=BLUE))
    t_arm = tex_mat("stripe arm", tex_kid_arm(WHITE, 9, SKIN, band=lambda c: [c.rect(0, y, 15, y, RED) for y in (2, 6)]))
    t_leg = tex_mat("kid shorts leg", tex_kid_leg(BLUE, 11, SKIN, extra=lambda c: c.rect(0, 26, 15, 26, RED)))
    shoe = kid_shoe(kit, "kid sneaker red", RED, WHITE)
    T = dict(head=tex_mat("stripes kid head", tex_face(SKIN, hair, back=26, eyes='kid', mouth='gap', freckles=True,
                                                       bangs=(43, hair))),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = kid_base(kit, root, B, T)
    hm = solid(kit, "kid hair", hair, 0.32, shade="#5e2a12")
    kid_hair_cap(kit, rig, hm)
    for i, (x, a) in enumerate(((-0.04, -20), (0.0, 0), (0.04, 25))):   # spiky cowlick
        hair_tuft(kit, rig, f"spike {i}", hm, [(x, 0.01, 0.29), (x * 1.6, 0.03, 0.335)], [0.02, 0.003])
    shorts_cuffs(kit, rig, solid(kit, "kid shorts", BLUE, shade="#1f5fd0"))
    tee_sleeves(kit, rig, tex_mat("stripe sleeve", tex_kid_arm(WHITE, 31, WHITE,
                                                                band=lambda c: [c.rect(0, y, 15, y + 1, RED) for y in (4, 12, 20, 28)])))
    sockets_npc(kit, root, rig)


def build_kid_overalls(kit, root):
    hair = "#e8a050"

    def bib(c):
        c.rect(0, 0, 63, 38, DENIM)
        c.speckle(random.Random(2), [DENIM_D], 40, 0, 38)
        c.rect(22, 38, 42, 52, DENIM); c.rect(22, 52, 42, 52, DENIM_D)
        c.rect(26, 42, 38, 48, DENIM_L); c.rect(27, 43, 37, 47, DENIM)
        c.rect(24, 52, 26, 63, DENIM); c.rect(38, 52, 40, 63, DENIM)
        c.rect(24, 50, 26, 51, GOLD); c.rect(38, 50, 40, 51, GOLD)
        for y in range(52, 64):   # straps crossing on the back
            c.set(56 + (63 - y) // 3, y, DENIM); c.set(57 + (63 - y) // 3, y, DENIM)
            c.set(8 - (63 - y) // 3, y, DENIM); c.set(7 - (63 - y) // 3, y, DENIM)
        c.rect(0, 36, 21, 38, DENIM_D); c.rect(43, 36, 63, 38, DENIM_D)
        disc(c, 32, 30, 3, YEL); c.set(32, 30, PINK)
    t_torso = tex_mat("overalls", tex_kid_torso(PINK, rows=bib))
    t_arm = tex_mat("pink tee arm", tex_kid_arm(PINK, 8, SKIN))
    t_leg = tex_mat("overall leg", tex_kid_leg(DENIM, 24, SKIN, sock=YEL, sock_rows=3,
                                              extra=lambda c: (c.rect(0, 24, 15, 25, DENIM_L), c.rect(4, 0, 4, 23, DENIM_D))))
    shoe = kid_shoe(kit, "kid sneaker yellow", YEL, PINK)
    T = dict(head=tex_mat("overalls kid head", tex_face(SKIN, hair, back=24, eyes='kid', mouth='smile', bangs=(42, hair),
                                                        freckles=True)),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = kid_base(kit, root, kid_props(head=(0, -0.004, 0.77), hs=1.34), T)
    hm = solid(kit, "kid hair", hair, 0.34, shade="#d08a3a")
    kid_hair_cap(kit, rig, hm)
    s = rig.hs
    tie = solid(kit, "hair tie", PINK, 0.45)
    for sx in (1, -1):
        p = kit.empty(f"pigtail {'L' if sx > 0 else 'R'}", rig.head, (sx * 0.1 * s, 0.03 * s, 0.22 * s), (0, sx * 30, 0))
        lowball(kit, f"pigtail tie {sx}", (sx * 0.012, 0, 0), (0.022, 0.022, 0.022), tie, p)
        tube(kit, f"pigtail {sx}", [(sx * 0.02, 0, 0.0), (sx * 0.07, 0.0, -0.03), (sx * 0.1, 0.01, -0.1), (sx * 0.1, 0.02, -0.15)],
             [0.035, 0.04, 0.03, 0.008], hm, p, sides=6, side=(0, 1, 0))
    tee_sleeves(kit, rig, solid(kit, "pink tee", PINK, shade="#e83a8f"))
    for nm in ("L", "R"):
        cuff_tube(kit, rig.legs[nm], f"overall cuff {nm}", -0.2, -0.3, (0.06, 0.064), (0.064, 0.068),
                  solid(kit, "denim cuff", DENIM_L, shade=DENIM))
    sockets_npc(kit, root, rig)


def build_kid_hoodie(kit, root):
    hair = "#2a1a10"
    HOOD = "#8f5bff"

    def rows(c):
        c.rect(0, 0, 63, 5, HOOD); c.rect(0, 5, 63, 5, "#6a3fd6")
        c.rect(22, 10, 42, 22, "#7a48e8"); c.rect(22, 22, 42, 22, "#6a3fd6")   # kangaroo pocket
        c.rect(30, 46, 30, 58, WHITE); c.rect(34, 46, 34, 58, WHITE)          # drawstrings
        c.dots([(30, 45), (34, 45)], MINT)
        cone_icon(c, 32, 30, 7, MINT)
        c.rect(0, 59, 63, 63, "#7a48e8"); c.rect(28, 59, 36, 63, SKIN)
    t_torso = tex_mat("hoodie", tex_kid_torso(HOOD, rows=rows))
    t_arm = tex_mat("hoodie arm", tex_kid_arm(HOOD, 27, SKIN, band=lambda c: c.rect(0, 25, 15, 27, "#6a3fd6")))
    t_leg = tex_mat("kid jeans", tex_kid_leg(DENIM, 28, SKIN, sock=None, extra=lambda c: c.rect(0, 26, 15, 28, DENIM_D)))
    shoe = kid_shoe(kit, "kid sneaker mint", MINT, WHITE)
    T = dict(head=tex_mat("hoodie kid head", tex_face(SKIN, hair, back=26, eyes='kid', mouth='flat', bangs=(42, hair))),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    B = kid_props(hip_z=0.5, head=(0, -0.004, 0.805), sh=(0.132, 0.004, 0.755),
                  tp=[(0, 0.0, 0.46), (0, -0.012, 0.55), (0, -0.016, 0.63), (0, -0.006, 0.71), (0, 0.0, 0.77), (0, 0.004, 0.82)],
                  tr=[(0.126, 0.098), (0.13, 0.106), (0.128, 0.104), (0.126, 0.094), (0.136, 0.088), (0.062, 0.054)],
                  ar=(0.05, 0.042, 0.034))
    rig = kid_base(kit, root, B, T)
    hm = solid(kit, "kid hair", hair, 0.3)
    kid_hair_cap(kit, rig, hm)
    s = rig.hs
    hood_m = solid(kit, "hood", HOOD, shade="#7a48e8")
    lathe(kit, "hood", [(0.07, -0.02), (0.13, 0.02), (0.15, 0.08), (0.12, 0.13), (0.0, 0.15)], hood_m, root, sides=8,
          loc=(0, 0.075, 0.79), rot=(-60, 0, 0), scale_y=0.6)
    # backpack
    bp = kit.empty("backpack", root, (0, 0.17, 0.64))
    tbox(kit, "backpack", (0, 0, 0), (0.22, 0.1, 0.26), solid(kit, "backpack", ORNG, shade="#e8752b"), bp, taper=(0.9, 0.9))
    tbox(kit, "backpack pocket", (0, 0.06, -0.05), (0.16, 0.03, 0.1), solid(kit, "backpack pocket", YEL), bp)
    tbox(kit, "backpack flap", (0, 0.0, 0.14), (0.2, 0.11, 0.03), solid(kit, "backpack flap", "#e8752b"), bp)
    strap = solid(kit, "backpack strap", "#c45a1a")
    for sx in (1, -1):
        tube(kit, f"backpack strap {sx}", [(sx * 0.075, 0.13, 0.78), (sx * 0.08, 0.02, 0.81), (sx * 0.085, -0.095, 0.74),
                                           (sx * 0.09, -0.11, 0.6), (sx * 0.1, 0.1, 0.55)],
             [(0.018, 0.006)] * 5, strap, root, sides=4, side=(1, 0, 0), caps=(False, False))
    sockets_npc(kit, root, rig)


def build_kid_dress(kit, root):
    hair = "#5a2a14"
    DRESS = YEL

    def rows(c):
        for y in range(0, 60, 5):
            for x in range((y // 5) % 2 * 4, 64, 8):
                c.rect(x, y, x + 1, y + 1, WHITE); c.set(x, y + 2, PINK)
        c.rect(0, 52, 63, 63, SKIN)
        c.rect(20, 52, 24, 63, DRESS); c.rect(40, 52, 44, 63, DRESS)
        c.rect(52, 52, 56, 63, DRESS); c.rect(8, 52, 12, 63, DRESS)
        c.rect(24, 50, 40, 52, "#ffb21f")
    t_torso = tex_mat("sundress", tex_kid_torso(DRESS, top=SKIN, rows=rows))
    t_arm = tex_mat("bare arm", tex_kid_arm(SKIN, 0, SKIN))
    t_leg = tex_mat("bare leg", tex_kid_leg(SKIN, 0, SKIN, sock=WHITE, sock_rows=3))
    shoe = sneaker(solid(kit, "mary jane", RED, shade=DRED), 0.78, None, 1.0)
    T = dict(head=tex_mat("dress kid head", tex_face(SKIN, hair, back=14, eyes='kid', mouth='smile', bangs=(43, hair))),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = kid_base(kit, root, kid_props(hs=1.34), T)
    hm = solid(kit, "kid hair", hair, 0.3, shade="#401c0c")
    kid_hair_cap(kit, rig, hm)
    s = rig.hs
    # long hair down the back
    tube(kit, "long hair", [(0, 0.07 * s, 0.24 * s), (0, 0.11 * s, 0.12 * s), (0, 0.1 * s, 0.0), (0, 0.09 * s, -0.07 * s)],
         [(0.1 * s, 0.05 * s), (0.11 * s, 0.05 * s), (0.1 * s, 0.04 * s), (0.08 * s, 0.02 * s)], hm, rig.head, sides=6)
    bow = solid(kit, "hair bow", PINK, 0.45, shade="#e83a8f")
    bp = kit.empty("hair bow", rig.head, (0.06 * s, 0.0, 0.28 * s), (0, 25, 0))
    for sx in (1, -1):
        tbox(kit, f"bow loop {sx}", (sx * 0.04, 0, 0), (0.07, 0.03, 0.06), bow, bp, taper=(1.0, 1.0), rot=(0, sx * 15, 0))
    lowball(kit, "bow knot", (0, 0, 0), (0.018, 0.02, 0.022), bow, bp)
    skirt = tex_mat("sundress skirt", sundress_skirt())
    tube(kit, "skirt", [(0, -0.01, 0.54), (0, -0.014, 0.45), (0, -0.01, 0.36), (0, -0.004, 0.3)],
         [(0.13, 0.105), (0.16, 0.13), (0.2, 0.17), (0.215, 0.185)], skirt, root, sides=10, caps=(False, False))
    for nm in ("L", "R"):
        tbox(kit, f"strap {nm}", (0, 0, 0.01), (0.03, 0.08, 0.02), solid(kit, "dress strap", DRESS), rig.arms[nm][0])
    sockets_npc(kit, root, rig)


def sundress_skirt():
    c = Canvas(64, 16, YEL)
    for y in range(0, 16, 5):
        for x in range((y // 5) % 2 * 4, 64, 8):
            c.rect(x, y, x + 1, y + 1, WHITE); c.set(x, y + 2, PINK)
    c.rect(0, 0, 63, 1, "#ffb21f")
    return c


# ---------------------------------------------------------------- Fat Kid (mini-boss)
def build_fat_kid(kit, root):
    hair = "#c86a2a"
    TEEC = "#ff8a3d"

    def rows(c):
        c.rect(0, 0, 63, 8, "#3c3fb8"); c.rect(0, 8, 63, 8, "#2a2c90")
        c.speckle(random.Random(8), ["#ff9f5a"], 50, 9, 58)
        c.rect(0, 60, 63, 63, "#e8752b"); c.rect(26, 60, 38, 63, SKIN)
    t_torso = tex_mat("fat kid tee", tex_kid_torso(TEEC, rows=rows))
    t_arm = tex_mat("fat kid arm", tex_kid_arm(TEEC, 7, SKIN, band=lambda c: c.dots([(4, 20), (11, 24), (7, 15)], CHOC)))
    t_leg = tex_mat("fat kid leg", tex_kid_leg("#3c3fb8", 12, SKIN, sock=WHITE, sock_rows=5,
                                               extra=lambda c: c.rect(0, 27, 15, 27, RED)))
    shoe = sneaker(tex_mat("fat kid sneaker", sneaker_tex(WHITE, RED, "#e6e0ff")), 1.1, solid(kit, "kid sole", WHITE, 0.35), 1.2)

    def choc_mouth(c):
        for x, y in ((26, 26), (27, 27), (37, 26), (36, 22), (28, 21), (33, 21), (38, 25), (25, 24)):
            c.set(x, y, "#8a4a26")
        c.rect(27, 22, 28, 22, "#8a4a26"); c.rect(35, 27, 37, 27, "#8a4a26")
        c.rect(28, 23, 35, 26, "#3a1408"); c.rect(29, 25, 34, 26, WHITE); c.rect(30, 23, 33, 23, "#ff6f8f")
    T = dict(head=tex_mat("fat kid head", tex_face(SKIN, hair, back=26, eyes='kid', mouth='none', blush="#ff7a8f",
                                                   freckles=True, bangs=(44, hair), extra=choc_mouth)),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    B = dict(hip_z=0.5, hip_x=0.13, lr=[(0.13, 0.13), 0.12, 0.1, 0.092, 0.075],
             tp=[(0, 0.0, 0.42), (0, -0.04, 0.52), (0, -0.07, 0.66), (0, -0.06, 0.8), (0, -0.02, 0.92), (0, 0.0, 1.0),
                 (0, 0.0, 1.06)],
             tr=[(0.27, 0.22), (0.33, 0.29), (0.36, 0.32), (0.34, 0.3), (0.3, 0.24), (0.27, 0.2), (0.12, 0.11)],
             head=(0, -0.01, 1.02), hs=1.62, hw=1.12, jowl=0.16, neck=1.3,
             sh=(0.3, 0.0, 0.94), L1=0.22, L2=0.2, ar=(0.1, 0.085, 0.07), splay=18.0, bendL=16.0, bendR=16.0, hand_s=1.15,
             leg_splay=3.0, torso_sides=10)
    rig = body(kit, root, B, T)
    sm = solid(kit, "kid skin", SKIN)
    ears(kit, rig, sm, size=0.9)
    s = rig.hs
    hm = solid(kit, "kid hair", hair, 0.32, shade="#a8521a")
    kid_hair_cap(kit, rig, hm, scale=(1.1, 1.12, 1.0))
    # bib with a chocolate smear
    bib = tex_mat("bib", tex_bib())
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    zs = (0.98, 0.86, 0.74, 0.62)
    for j, z in enumerate(zs):
        row = []
        for i in range(5):
            a = math.radians(-50 + 100 * i / 4)
            rx, ry, cy = surf_r(rig.tp, rig.tr, z)
            row.append(bm.verts.new((math.sin(a) * (rx + 0.03), cy - math.cos(a) * (ry + 0.045), z)))
        grid.append(row)
    for j in range(len(zs) - 1):
        for i in range(4):
            fc = bm.faces.new((grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]))
            for lp, uv in zip(fc.loops, ((i / 4, 1 - (j + 1) / 3), ((i + 1) / 4, 1 - (j + 1) / 3), ((i + 1) / 4, 1 - j / 3),
                                         (i / 4, 1 - j / 3))):
                lp[uvl].uv = (min(0.995, max(0.005, uv[0])), min(0.995, max(0.005, uv[1])))
    kit.mesh_from_bmesh("bib", bm, bib, root)
    rx, ry, cy = surf_r(rig.tp, rig.tr, 1.02)
    tube(kit, "bib tie", [(0, cy, 1.0), (0, cy, 1.025)], [(rx + 0.01, ry + 0.01)] * 2, solid(kit, "bib tie", RED), root,
         sides=8, caps=(False, False))
    # sweatband
    lathe(kit, "sweatband", [(0.104 * s * 1.12, 0.215 * s), (0.104 * s * 1.12 + 0.014, 0.215 * s),
                             (0.096 * s * 1.12 + 0.014, 0.25 * s), (0.094 * s * 1.12, 0.25 * s)], tex_mat("sweatband", tex_sweatband()), rig.head, sides=8, closed=True,
          loc=(0, 0.002 * s, 0), scale_y=1.04)
    # tiny propeller beanie on top of the big head
    top = head_top(rig)
    bean = kit.empty("beanie", rig.head, (0.02 * s, 0.0, top - 0.035 * s), (0, 8, 0))
    lathe(kit, "beanie", [(0.05, 0.0), (0.052, 0.02), (0.04, 0.045), (0.0, 0.055)], tex_mat("beanie", tex_beanie()), bean,
          sides=8)
    tube(kit, "propeller stem", [(0, 0, 0.05), (0, 0, 0.085)], 0.006, solid(kit, "stem", YEL), bean, sides=4)
    prop = kit.empty("propeller", bean, (0, 0, 0.085))
    for k, col in enumerate((RED, BLUE, YEL)):
        tbox(kit, f"propeller blade {k}", (0.045, 0, 0), (0.08, 0.026, 0.006), solid(kit, f"blade {col}", col, 0.4), prop,
             rot=(10, 0, 0)).rotation_euler = (0, 0, math.radians(120 * k))
    lowball(kit, "propeller cap", (0, 0, 0.004), (0.01, 0.01, 0.01), solid(kit, "stem", YEL), prop)
    shorts_cuffs(kit, rig, solid(kit, "fat kid shorts", "#3c3fb8", shade="#2a2c90"), r=(0.145, 0.15), z1=-0.2)
    tee_sleeves(kit, rig, solid(kit, "fat kid sleeve", TEEC, shade="#e8752b"), ln=0.1, r=0.115)
    sockets_npc(kit, root, rig)


def tex_bib():
    c = Canvas(32, 32, WHITE)
    c.rect(0, 0, 31, 1, RED); c.rect(0, 0, 1, 31, RED); c.rect(30, 0, 31, 31, RED); c.rect(0, 30, 31, 31, RED)
    for x in range(3, 30, 4):
        c.set(x, 2, PINK)
    txt_c(c, "YUM", 16, 26, PINK)
    for x, y, r in ((12, 14, 4), (17, 11, 3), (20, 16, 2), (9, 9, 2), (22, 7, 1), (14, 6, 2)):
        disc(c, x, y, r, "#7a3e22")
    c.dots([(11, 15), (16, 12), (21, 17)], "#a8643a")
    for x in (8, 14, 19):
        c.rect(x, 3, x, 6, "#7a3e22")
    return c


def tex_sweatband():
    c = Canvas(16, 8, WHITE)
    c.rect(0, 3, 15, 4, RED)
    return c


def tex_beanie():
    c = Canvas(16, 8, BLUE)
    for x in range(0, 16, 4):
        c.rect(x, 0, x + 1, 7, RED)
    c.rect(0, 0, 15, 1, YEL)
    return c


# ---------------------------------------------------------------- Lactose Kid
def build_lactose_kid(kit, root):
    skin = "#e4f0c4"
    hair = "#b8a070"

    def rows(c):
        # crossed-out milk carton
        c.rect(27, 26, 36, 40, WHITE); c.rect(27, 40, 31, 44, WHITE); c.rect(32, 40, 36, 42, WHITE)
        c.rect(27, 30, 36, 33, BLUE); txt(c, "MLK", 26, 38, BLUE)
        for r in range(11, 13):
            for a in range(48):
                t = 2 * math.pi * a / 48
                c.set(int(32 + r * math.cos(t)), int(34 + r * math.sin(t)), RED)
        for i in range(-8, 9):
            c.rect(32 + i, 34 - i, 33 + i, 34 - i, RED)
    t_torso = tex_mat("lactose tee", tex_kid_torso(MINT, top=skin, rows=rows, waist="#8f5bff"))
    t_arm = tex_mat("lactose arm", tex_kid_arm(MINT, 8, skin))
    t_leg = tex_mat("lactose leg", tex_kid_leg("#8f5bff", 11, skin, sock=WHITE))
    shoe = kid_shoe(kit, "kid sneaker purple", PURP, WHITE)

    def queasy(c):
        c.rect(26, 23, 37, 23, "#5a7a3a"); c.dots([(25, 24), (38, 22), (28, 24), (34, 22)], "#5a7a3a")
    T = dict(head=tex_mat("lactose kid head", tex_face(skin, hair, back=26, eyes='sick', mouth='none', blush="#b8e08a",
                                                       bangs=(43, hair), extra=queasy)),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("lactose hand", tex_hand(skin)),
             handR=tex_mat("lactose hand", tex_hand(skin)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    B = kid_props(bendL=78.0, twistL=0.0, hs=1.33)
    rig = body(kit, root, B, T)
    sm = solid(kit, "lactose skin", skin)
    ears(kit, rig, sm, size=0.9)
    hm = solid(kit, "kid hair", hair, 0.32)
    kid_hair_cap(kit, rig, hm)
    tee_sleeves(kit, rig, solid(kit, "lactose sleeve", MINT, shade="#22d8a8"))
    shorts_cuffs(kit, rig, solid(kit, "lactose shorts", PURP, shade="#6a3fd6"))
    # soy-milk juice box in the left hand (part of the arm L hierarchy), straw toward the mouth
    armL, W, d2, palm = rig.arms["L"]
    jb = kit.empty("juice box", armL, tuple(palm + Vector((-0.012, 0, 0.012))))
    tbox(kit, "juice box", (0, 0, 0.0), (0.04, 0.05, 0.075), tex_mat("soy box", tex_soy_box()), jb,
         uv={'all': (0.0, 0.0, 0.1, 0.1), 'ny': (0, 0, 0.5, 1), 'py': (0.5, 0, 1, 1), 'nx': (0.5, 0, 1, 1),
             'px': (0.5, 0, 1, 1)})
    tube(kit, "juice straw", [(0.008, 0.01, 0.035), (0.008, 0.012, 0.075), (-0.004, 0.03, 0.095)], 0.0045,
         solid(kit, "straw", PINK, 0.45), jb, sides=4)
    sockets_npc(kit, root, rig)


def tex_soy_box():
    c = Canvas(32, 32, WHITE)
    c.rect(0, 0, 15, 12, ZG); c.rect(16, 0, 31, 31, "#c8f0a0")
    txt_c(c, "SOY", 8, 26, LEAF_D)
    disc(c, 8, 7, 3, "#fff1c7"); c.set(8, 8, LEAF_D)
    c.rect(18, 4, 29, 6, LEAF_D)
    return c


# ---------------------------------------------------------------- Diabetic Kid
def build_diabetic_kid(kit, root):
    hair = "#1f140c"
    skin = "#d9956a"
    TEEC = BLUE

    def rows(c):
        c.rect(0, 0, 63, 7, "#e6dcd2"); c.rect(0, 7, 63, 8, BELT)
        c.rect(30, 6, 34, 9, STEEL)
        for x in range(0, 64, 8):
            c.rect(x, 20, x + 3, 50, "#5aa0ff")
        disc(c, 32, 38, 6, YEL); c.dots([(30, 40), (34, 40)], INK); c.rect(29, 36, 35, 36, INK)
    t_torso = tex_mat("diabetic tee", tex_kid_torso(TEEC, top=skin, rows=rows))

    def bracelet(c):
        c.rect(0, 27, 15, 29, RED)
    t_armL = tex_mat("diabetic arm L", tex_kid_arm(TEEC, 8, skin))
    t_armR = tex_mat("diabetic arm R", tex_kid_arm(TEEC, 8, skin))
    t_leg = tex_mat("diabetic leg", tex_kid_leg("#e6dcd2", 12, skin, sock=WHITE, extra=lambda c: c.rect(0, 12, 15, 12, KHAKI_D)))
    shoe = kid_shoe(kit, "kid sneaker blue", BLUE, YEL)
    T = dict(head=tex_mat("diabetic kid head", tex_face(skin, hair, back=28, eyes='kid', mouth='smile', blush="#e87a7a")),
             torso=t_torso, armL=t_armL, armR=t_armR, handL=tex_mat("diabetic hand", tex_hand(skin)),
             handR=tex_mat("diabetic hand", tex_hand(skin)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    rig = body(kit, root, kid_props(), T)
    sm = solid(kit, "kid skin", skin)
    ears(kit, rig, sm, size=0.9)
    hm = solid(kit, "kid hair", hair, 0.28)
    kid_hair_cap(kit, rig, hm, scale=(1.08, 1.1, 1.0))
    for i, x in enumerate((-0.06, -0.02, 0.02, 0.06)):   # curly top
        lowball(kit, f"curl {i}", (x * rig.hs, 0.0, 0.29 * rig.hs + 0.01 * (i % 2)), (0.03, 0.03, 0.025), hm, rig.head)
    tee_sleeves(kit, rig, solid(kit, "diabetic sleeve", TEEC, shade="#1f5fd0"))
    shorts_cuffs(kit, rig, solid(kit, "khaki kid shorts", "#e6dcd2", shade="#cfc6e0"))
    # bright red insulin pump on the belt (right hip, front) with a little tube to the belly
    x = -0.085
    y = belly_y(rig, 0.47, x, 0.0)
    pump = kit.empty("insulin pump", root, (x, y - 0.018, 0.475), (0, 0, 20))
    red = solid(kit, "pump red", RED, 0.55, shade=DRED)
    tbox(kit, "insulin pump", (0, 0, 0), (0.07, 0.03, 0.085), red, pump)
    tbox(kit, "pump screen", (0, -0.016, 0.014), (0.05, 0.004, 0.032), tex_mat("pump screen", tex_pump_screen(), 0.9), pump,
         uv={'all': (0.1, 0.1, 0.2, 0.2), 'ny': (0, 0, 1, 1)})
    tbox(kit, "pump button", (0, -0.016, -0.025), (0.02, 0.004, 0.012), solid(kit, "pump button", WHITE, 0.6), pump)
    tbox(kit, "pump clip", (0, 0.017, 0.02), (0.03, 0.006, 0.05), solid(kit, "clip", STEEL), pump)
    site = Vector((0.04, belly_y(rig, 0.56, 0.04, 0.004), 0.56))
    tube(kit, "pump tube", [(x + 0.02, y - 0.02, 0.52), (x + 0.03, y - 0.04, 0.56), (0.0, belly_y(rig, 0.6, 0, 0.03), 0.6),
                            (site.x - 0.01, site.y - 0.012, site.z + 0.01), tuple(site)], 0.006,
         solid(kit, "pump tube", WHITE, 0.5), root, sides=4, caps=(False, False))
    tbox(kit, "infusion patch", tuple(site), (0.03, 0.006, 0.03), solid(kit, "patch", WHITE, 0.5), root)
    # medical bracelet on the left wrist
    armL, W, d2, palm = rig.arms["L"]
    tube(kit, "medical bracelet", [tuple(W - d2 * 0.02), tuple(W + d2 * 0.002)], 0.034, red, armL, sides=6, caps=(False, False))
    tbox(kit, "medical tag", tuple(W - d2 * 0.009 + Vector((0, -0.034, 0))), (0.026, 0.006, 0.02),
         tex_mat("medical tag", tex_med_tag()), armL, uv={'all': (0.1, 0.1, 0.2, 0.2), 'ny': (0, 0, 1, 1)})
    sockets_npc(kit, root, rig)


def tex_pump_screen():
    c = Canvas(16, 8, "#9cff57")
    txt(c, "120", 2, 6, "#1f5a12")
    return c


def tex_med_tag():
    c = Canvas(8, 8, WHITE)
    c.rect(3, 1, 4, 6, RED); c.rect(1, 3, 6, 4, RED)
    return c


# ---------------------------------------------------------------- Rich Kid
def build_rich_kid(kit, root):
    hair = "#e8c860"
    BLAZER = NAVY

    def rows(c):
        c.rect(0, 0, 63, 6, "#9a94b0")
        for y in range(6, 64):   # white shirt V under the blazer
            half = max(0, (y - 30) // 3)
            c.rect(32 - half, y, 32 + half, y, WHITE)
        c.rect(32, 7, 32, 30, "#101850")
        for y in (12, 20, 28):
            c.rect(31, y, 33, y + 1, GOLD)
        c.rect(38, 36, 44, 43, GOLD); c.rect(39, 37, 43, 42, RED); c.rect(41, 37, 41, 42, GOLD)   # crest
        c.rect(38, 44, 44, 44, GOLD)
        c.rect(20, 18, 27, 19, "#101850"); c.rect(37, 18, 44, 19, "#101850")
        c.rect(43, 47, 45, 50, WHITE); c.set(44, 51, RED)   # pocket square
    t_torso = tex_mat("blazer", tex_kid_torso(BLAZER, top=WHITE, rows=rows))
    t_arm = tex_mat("blazer arm", tex_kid_arm(BLAZER, 27, SKIN, band=lambda c: (c.rect(0, 26, 15, 27, WHITE),
                                                                               c.dots([(3, 24), (5, 24)], GOLD))))
    t_leg = tex_mat("slacks", tex_kid_leg("#9a94b0", 29, SKIN, sock=None, extra=lambda c: c.rect(8, 0, 8, 29, "#7a7494")))

    def loafer(kit, piv, name, g):
        sneaker(solid(kit, "loafer", "#7a3a1c", 0.35, shade="#5e2a12"), 0.82, None, 1.0)(kit, piv, name, g)
        tbox(kit, f"penny {name}", (0, -0.075, g + 0.065), (0.03, 0.03, 0.006), solid(kit, "penny", GOLD, 0.6), piv,
             rot=(-30, 0, 0))
    T = dict(head=tex_mat("rich kid head", tex_face(SKIN, hair, back=26, eyes='smug', mouth='smirk', blush=None,
                                                    brow_tilt=-1)),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("kid hand", tex_hand(SKIN)),
             handR=tex_mat("kid hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=loafer, shoeR=loafer)
    rig = kid_base(kit, root, kid_props(), T)
    s = rig.hs
    hm = solid(kit, "slick hair", hair, 0.45, shade="#fff09a")
    kid_hair_cap(kit, rig, hm, z=0.18)
    hair_tuft(kit, rig, "side swoop", hm, [(-0.07, -0.09, 0.27), (0.0, -0.105, 0.28), (0.06, -0.1, 0.25), (0.1, -0.06, 0.22)],
              [0.02, 0.03, 0.025, 0.01])
    tbox(kit, "hair part", (-0.035 * s, -0.01 * s, 0.31 * s), (0.008, 0.18 * s, 0.006), solid(kit, "part", SKIN), rig.head)
    for nm in ("L", "R"):
        tube(kit, f"blazer shoulder {nm}", [(0, 0, 0.035), (0, 0, -0.12)], [0.058, 0.052], solid(kit, "blazer", BLAZER,
                                                                                               shade="#18205a"),
             rig.arms[nm][0], sides=6, caps=(True, False))
    hem(kit, rig, root, "blazer hem", 0.5, 0.42, solid(kit, "blazer", BLAZER, shade="#18205a"), flare=1.08)
    bt = kit.empty("bow tie", root, (0, belly_y(rig, 0.76, 0, 0.006), 0.765))
    bow = solid(kit, "bow tie", RED, 0.4, shade=DRED)
    for sx in (1, -1):
        tbox(kit, f"bow tie {sx}", (sx * 0.026, 0, 0), (0.044, 0.016, 0.034), bow, bt, taper=(1.0, 1.0), rot=(0, sx * 10, 0))
    lowball(kit, "bow tie knot", (0, -0.006, 0), (0.012, 0.012, 0.014), bow, bt)
    sockets_npc(kit, root, rig)


# ---------------------------------------------------------------- Cop
def build_cop(kit, root):
    R = kit.rand
    hair = "#4a3326"
    SHIRT = "#5a7ef0"; SHIRT_D = "#3f5fd0"

    def rows(c):
        c.rect(0, 0, 63, 5, NAVY)
        c.rect(0, 5, 63, 10, BLACK); c.rect(29, 6, 35, 9, STEEL)
        c.rect(32, 11, 32, 58, SHIRT_D)
        for y in range(16, 58, 9):
            c.set(31, y, WHITE)
        for x0 in (19, 37):
            c.rect(x0, 40, x0 + 8, 46, SHIRT_D); c.rect(x0, 46, x0 + 8, 48, "#2f4fb8")
        c.rect(38, 50, 43, 55, GOLD); c.rect(39, 51, 42, 54, YEL); c.set(40, 52, GOLD_D)   # badge
        c.rect(20, 50, 26, 52, WHITE); c.rect(21, 51, 25, 51, INK)   # name tag
        c.rect(28, 58, 36, 63, SKIN)
        c.rect(0, 62, 63, 63, SHIRT_D)
    t_torso = tex_mat("cop shirt", tex_kid_torso(SHIRT, top=SKIN, rows=rows))
    t_arm = tex_mat("cop arm", tex_dad_arm(SHIRT, 9, SKIN, SKIN_D, trim=SHIRT_D,
                                           rows=lambda c: c.rect(5, 3, 10, 6, YEL)))
    t_leg = tex_mat("cop pants", tex_legs(NAVY, NAVY_D, lambda c: (c.rect(3, 0, 4, 31, YEL), c.rect(11, 0, 12, 31, YEL),
                                                                    c.rect(0, 29, 15, 31, NAVY_D))))
    shoe = sneaker(solid(kit, "cop shoe", BLACK, 0.3, shade="#3a3050"), 1.05, None, 1.05)
    T = dict(head=tex_mat("cop head", tex_face(SKIN, hair, back=18, eyes='none', mouth='flat', stubble="#e0a080")),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("dad hand", tex_hand(SKIN)),
             handR=tex_mat("dad hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    B = dad_proportions(hip_z=0.9, head=(0, -0.012, 1.475), hs=1.08, hw=1.06, jowl=0.1,
                        tp=[(0, 0.0, 0.82), (0, -0.04, 0.93), (0, -0.075, 1.06), (0, -0.06, 1.19), (0, -0.015, 1.3),
                            (0, 0.012, 1.39), (0, 0.02, 1.48)],
                        tr=[(0.19, 0.15), (0.225, 0.2), (0.235, 0.23), (0.22, 0.2), (0.21, 0.15), (0.225, 0.13),
                            (0.095, 0.08)],
                        sh=(0.225, 0.016, 1.385), L1=0.3, L2=0.27, ar=(0.072, 0.058, 0.045), bendL=75.0, twistL=-15.0,
                        splay=10.0, lr=[(0.095, 0.1), 0.085, 0.07, 0.062, 0.052])
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    s = rig.hs
    nose(kit, rig, solid(kit, "nose", "#ff9a8a"), r=(0.024, 0.03, 0.028))
    ears(kit, rig, skin)
    mustache(kit, rig, solid(kit, "mustache", hair, 0.3, shade="#2a1a10"), z=0.128, w=0.088, r=0.028, droop=0.04)
    shades(kit, rig, "aviators", solid(kit, "aviator frame", GOLD, 0.5), solid(kit, "aviator lens", "#3a2a6a", 0.6,
                                                                               shade="#ff8fc8"), aviator=True)
    # police cap
    cp = kit.empty("police cap", rig.head, (0, -0.004 * s, 0.205 * s), (-4, 0, 0))
    navy = solid(kit, "cap navy", NAVY, shade=NAVY_D)
    lathe(kit, "police cap", [(0.114 * s, 0.0), (0.118 * s, 0.045 * s), (0.142 * s, 0.1 * s), (0.142 * s, 0.112 * s), (0, 0.118 * s)],
          navy, cp, sides=10)
    lathe(kit, "cap band", [(0.119 * s, 0.006 * s), (0.122 * s, 0.04 * s)], solid(kit, "cap band", BLACK, 0.2), cp, sides=10)
    lathe(kit, "cap bill", [(0.0, 0.006 * s), (0.1 * s, 0.006 * s), (0.1 * s, -0.006 * s), (0, -0.004 * s)],
          solid(kit, "cap bill", BLACK, 0.25, shade="#3a3050"), cp, sides=8, loc=(0, -0.105 * s, 0.004 * s), closed=True,
          scale_y=0.7)
    tbox(kit, "cap badge", (0, -0.13 * s, 0.075 * s), (0.04 * s, 0.01, 0.045 * s), solid(kit, "badge", GOLD, 0.6), cp,
         rot=(-15, 0, 0), taper=(0.6, 1.0))
    # duty belt with a radio and cuffs pouch
    rx, ry, cy = surf_r(rig.tp, rig.tr, 0.86)
    tube(kit, "duty belt", [(0, cy, 0.84), (0, cy, 0.89)], [(rx + 0.012, ry + 0.012)] * 2, solid(kit, "duty belt", BLACK, 0.2),
         root, sides=8, caps=(False, False))
    rad = kit.empty("radio", root, (0.2, belly_y(rig, 0.86, 0.16, 0.0) + 0.03, 0.86), (0, 0, 35))
    tbox(kit, "radio", (0, 0, 0.02), (0.04, 0.06, 0.12), solid(kit, "radio", "#3a3050", 0.25), rad)
    tube(kit, "radio antenna", [(0, 0.01, 0.08), (0, 0.01, 0.2)], 0.007, solid(kit, "antenna", BLACK), rad, sides=4)
    tbox(kit, "radio light", (0, -0.031, 0.06), (0.01, 0.004, 0.01), solid(kit, "radio light", RED, 1.4), rad)
    tbox(kit, "cuff pouch", (0, 0, 0), (0.05, 0.12, 0.07), solid(kit, "pouch", BLACK, 0.2), root,
         loc=(-0.21, belly_y(rig, 0.86, -0.17, 0.0) + 0.05, 0.85))
    # donut in the left hand (arm L hierarchy), held up at belly height
    armL, W, d2, palm = rig.arms["L"]
    dn = kit.empty("donut", armL, tuple(palm + Vector((-0.01, -0.02, 0.05))), (75, 0, 0))
    torus(kit, "donut", 0.042, 0.022, solid(kit, "donut dough", "#e8a85a", shade="#c47f3a"), dn, seg=10, sides=6)
    torus(kit, "donut frosting", 0.042, 0.02, solid(kit, "frosting", PINK, 0.45, shade="#ff8fc8"), dn, loc=(0, 0, 0.006),
          seg=10, sides=6).scale = (1.0, 1.0, 0.7)
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.2
        tbox(kit, f"donut sprinkle {i}", (0, 0, 0), (0.006, 0.016, 0.005), solid(kit, f"sprinkle {i % 4}",
                                                                                 (YEL, WHITE, BLUE, MINT)[i % 4], 0.6),
             dn, loc=(math.cos(a) * 0.042, math.sin(a) * 0.042, 0.022), rot=(0, 0, math.degrees(a) + 40 * (i % 3)))
    hem(kit, rig, root, "shirt tuck", 0.92, 0.88, solid(kit, "cop shirt plain", SHIRT, shade=SHIRT_D), flare=1.02, pad=0.006)
    sockets_npc(kit, root, rig)


# ---------------------------------------------------------------- Big Dairy
def tex_cow_suit(rand, w, h, base=WHITE):
    c = Canvas(w, h, base)
    for _ in range(max(2, w * h // 300)):
        x, y = rand.randrange(w), rand.randrange(h)
        r = rand.choice((3, 4, 5))
        disc(c, x, y, r, COW_K)
        disc(c, x + r, y + 1, r - 1, COW_K)
        disc(c, x - 1, y - r + 1, r - 2, COW_K)
    c.speckle(rand, ["#ece4f4"], w * h // 25)
    return c


def build_big_dairy(kit, root):
    R = kit.rand
    hair = "#1b1033"

    def suit(c):
        for y in range(28, 64):
            half = max(0, (y - 28) // 2)
            c.rect(32 - half, y, 32 + half, y, BLACK)
        for y in range(48, 64):
            half = max(0, (y - 48) // 2)
            c.rect(32 - half, y, 32 + half, y, SKIN)
        c.rect(0, 0, 63, 3, COW_K)
        for y in (12, 20):
            c.rect(31, y, 33, y + 1, GOLD)
    cv = tex_cow_suit(R, 64, 64)
    suit(cv)
    t_torso = tex_mat("cow suit", cv)
    t_arm = tex_mat("cow suit arm", tex_cow_suit(R, 16, 32))
    cva = Canvas(16, 32, SKIN)
    t_leg = tex_mat("cow suit leg", tex_cow_suit(R, 16, 32))
    shoe = sneaker(solid(kit, "dress shoe", BLACK, 0.4, shade="#3a3050"), 1.15, None, 1.0)

    def face(c):
        c.rect(26, 19, 37, 19, hex_scale(SKIN, 0.82))
    T = dict(head=tex_mat("big dairy head", tex_face(SKIN, hair, back=22, eyes='none', mouth='smirk', blush="#ff9a8a",
                                                     stubble="#d9a080", extra=face)),
             torso=t_torso, armL=t_arm, armR=t_arm, handL=tex_mat("big hand", tex_hand(SKIN)),
             handR=tex_mat("big hand", tex_hand(SKIN)), legL=t_leg, legR=t_leg, shoeL=shoe, shoeR=shoe)
    B = dict(hip_z=0.92, hip_x=0.14, lr=[(0.13, 0.14), 0.12, 0.1, 0.09, 0.075],
             tp=[(0, 0.0, 0.84), (0, -0.04, 0.96), (0, -0.07, 1.1), (0, -0.05, 1.26), (0, -0.01, 1.4), (0, 0.01, 1.5),
                 (0, 0.02, 1.6)],
             tr=[(0.27, 0.2), (0.31, 0.26), (0.33, 0.29), (0.32, 0.26), (0.33, 0.2), (0.34, 0.18), (0.14, 0.12)],
             head=(0, -0.01, 1.585), hs=1.2, hw=1.12, jowl=0.18, neck=1.45,
             sh=(0.34, 0.01, 1.48), L1=0.33, L2=0.3, ar=(0.1, 0.085, 0.065), splay=12.0, bendL=16.0, bendR=16.0,
             hand_s=1.35, torso_sides=10)
    rig = body(kit, root, B, T)
    skin = solid(kit, "skin", SKIN)
    s = rig.hs
    nose(kit, rig, solid(kit, "nose", SKIN_D), r=(0.026, 0.032, 0.03))
    ears(kit, rig, skin)
    shades(kit, rig, "sunglasses", solid(kit, "shades frame", BLACK, 0.25), solid(kit, "shades lens", "#1b1033", 0.3,
                                                                                    shade="#3a2a6a"), w=1.12)
    # slicked-back hair
    hm = solid(kit, "slick hair", hair, 0.5, shade="#3a2a6a")
    lathe(kit, "slick hair", [(0.112 * s * 1.12, 0.17 * s), (0.11 * s * 1.12, 0.22 * s), (0.085 * s * 1.12, 0.29 * s),
                              (0.04 * s, 0.322 * s), (0, 0.326 * s)], hm, rig.head, sides=8, loc=(0, 0.012 * s, 0))
    # cigar with a glowing tip
    z = 0.118 * s
    cg = kit.empty("cigar", rig.head, (0.035 * s, head_front(rig, z, 0.035 * s) + 0.004, z), (0, 0, -18))
    tube(kit, "cigar", [(0, 0, 0), (0, -0.14, -0.02)], [0.019, 0.021], solid(kit, "cigar", "#8a4a26", shade="#6e3a1e"), cg,
         sides=6, side=(1, 0, 0))
    tube(kit, "cigar band", [(0, -0.03, -0.004), (0, -0.045, -0.006)], 0.022, solid(kit, "cigar band", GOLD, 0.5), cg, sides=6,
         side=(1, 0, 0), caps=(False, False))
    tube(kit, "cigar tip", [(0, -0.14, -0.02), (0, -0.16, -0.023)], [0.021, 0.02], solid(kit, "cigar ember", ORNG, 1.6,
                                                                                       shade=RED), cg,
         sides=6, side=(1, 0, 0))
    # gold chain with a milk-drop pendant
    gold = solid(kit, "gold", GOLD, 0.6, shade=GOLD_D)
    pts = []
    for k in range(9):
        t = (k - 4) / 4
        x = t * 0.11
        zz = 1.47 - 0.15 * (1 - t * t)
        pts.append((x, belly_y(rig, zz, x, 0.012), zz))
    tube(kit, "gold chain", pts, 0.012, gold, root, sides=4, caps=(False, False))
    pd = kit.empty("milk drop pendant", root, (0, belly_y(rig, 1.29, 0, 0.02), 1.27))
    lathe(kit, "milk drop", [(0, -0.05), (0.03, -0.035), (0.036, -0.015), (0.022, 0.012), (0.008, 0.03), (0, 0.04)],
          solid(kit, "milk white", WHITE, 0.7, shade="#e6eef8"), pd, sides=8, scale_y=0.45)
    lathe(kit, "drop rim", [(0.036, -0.016), (0.042, -0.016), (0.042, -0.008), (0.036, -0.008)], gold, pd, sides=8,
          closed=True, scale_y=0.5)
    # pinky ring on the right hand
    armR, W, d2, palm = rig.arms["R"]
    tube(kit, "pinky ring", [tuple(W + d2 * 0.1 + Vector((0, 0.04, 0))), tuple(W + d2 * 0.118 + Vector((0, 0.04, 0)))], 0.02,
         gold, armR, sides=6, caps=(False, False))
    lowball(kit, "ring stone", tuple(W + d2 * 0.11 + Vector((0.0, 0.05, 0.0))), (0.012, 0.012, 0.012),
            solid(kit, "diamond", "#c8f0ff", 1.2), armR, smooth=False)
    # suit lapels and cuffs
    hem(kit, rig, root, "jacket hem", 0.96, 0.82, tex_mat("cow hem", tex_cow_suit(R, 64, 16)), flare=1.06)
    for nm in ("L", "R"):
        armp, W, d2, palm = rig.arms[nm]
        tube(kit, f"shirt cuff {nm}", [tuple(W - d2 * 0.035), tuple(W - d2 * 0.005)], 0.07, solid(kit, "shirt cuff", WHITE),
             armp, sides=6, caps=(False, False))
        tube(kit, f"suit shoulder {nm}", [(0, 0, 0.06), (0, 0, -0.12)], [0.12, 0.11], tex_mat("cow shoulder",
                                                                                          tex_cow_suit(R, 16, 16)),
             armp, sides=6, caps=(True, False))
    sockets_npc(kit, root, rig, mouth=False)


# ---------------------------------------------------------------- batch
ASSETS = [
    ("Dad Pink", named("Dad Pink", build_dad_pink)),
    ("Dad Blue", named("Dad Blue", build_dad_blue)),
    ("Dad Mint", named("Dad Mint", build_dad_mint)),
    ("Dad Yellow", named("Dad Yellow", build_dad_yellow)),
    ("Dad First-Person Arms", named("Dad First-Person Arms", build_dad_fp_arms)),
    ("Kid Stripes", named("Kid Stripes", build_kid_stripes)),
    ("Kid Overalls", named("Kid Overalls", build_kid_overalls)),
    ("Kid Hoodie", named("Kid Hoodie", build_kid_hoodie)),
    ("Kid Dress", named("Kid Dress", build_kid_dress)),
    ("Fat Kid", named("Fat Kid", build_fat_kid)),
    ("Lactose Kid", named("Lactose Kid", build_lactose_kid)),
    ("Diabetic Kid", named("Diabetic Kid", build_diabetic_kid)),
    ("Rich Kid", named("Rich Kid", build_rich_kid)),
    ("Cop", named("Cop", build_cop)),
    ("Big Dairy", named("Big Dairy", build_big_dairy)),
]


def build_lineup(kit, root):
    for i, (nm, fn) in enumerate(ASSETS):
        if nm == "Dad First-Person Arms":
            continue
        k = i if i < 4 else i - 1
        p = kit.empty(f"lineup {nm}", root, ((k - 6.5) * 0.85, 0, 0), (0, 0, 0))
        fn(kit, p)


def build_row(names, dx):
    def build(kit, root):
        lookup = dict(ASSETS)
        for i, nm in enumerate(names):
            p = kit.empty(f"row {nm}", root, ((i - (len(names) - 1) / 2) * dx, 0, 0))
            lookup[nm](kit, p)
    return build


DADS = ["Dad Pink", "Dad Blue", "Dad Mint", "Dad Yellow"]
KIDS = ["Kid Stripes", "Kid Overalls", "Kid Hoodie", "Kid Dress", "Lactose Kid", "Diabetic Kid", "Rich Kid"]
SCENES = [dict(name="lineup", build=build_lineup, cam=((0.0, -17.5, 1.6), (0, 0, 0.95), 50), res=(1800, 520)),
          dict(name="dad faces", build=build_row(DADS, 0.62), cam=((0.0, -3.3, 1.6), (0, 0, 1.45), 50), res=(1600, 800)),
          dict(name="kid faces", build=build_row(KIDS, 0.46), cam=((0.0, -3.6, 1.0), (0, 0, 0.8), 50), res=(1600, 700)),
          dict(name="bosses", build=build_row(["Fat Kid", "Cop", "Big Dairy"], 1.0), cam=((0.0, -4.6, 1.4), (0, 0, 1.1), 50),
               res=(1600, 800))]
