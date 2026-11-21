"""Batch 'vehicles' (style H): the heist pitch's police car, the buyer's yacht and the harbor set (dock, water, lighthouse).
Police Car: root on the ground at the footprint center, front -Y, wheels on their own pivots, emissive light bar
(red half +X, blue half -X). Yacht: root at the waterline at the hull center, bow -Y, gangway on the +X side near the
stern ('Yacht socket gangway' at its outer end). Harbor Dock: root at the shore end center, deck top at z=0, the pier
runs along -Y, the water line is 1 m below the deck; 'Harbor Dock socket yacht' is where a yacht root goes (at the
water line, rotated so the yacht's bow points to shore and its +X gangway side faces the pier).
Harbor Water: 80 x 80 m plane, root at its center, texture repeats every 4 m. Lighthouse: root on the ground/water at the
center of its rock base."""
from style_H import *
from h_road import MB, rect
from h_stops import FONT2

SPACING = 30
CUT = "#010203"


def txt(c, s, x, y, col, k=1, ky=None):
    """3x5 pixel font with digits. (x, y) = top-left texel, y counts up; ky stretches the glyphs vertically."""
    ky = ky or k
    for ch in s:
        for r, row in enumerate(FONT2.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * k, y - (r + 1) * ky + 1, x + q * k + k - 1, y - r * ky, col)
        x += 4 * k


def txt_c(c, s, cx, y, col, k=1, ky=None):
    txt(c, s, cx - text_w(s, k) // 2, y, col, k, ky)


# ---------------------------------------------------------------- shared helpers
def tx(kit, name, make, emit=0.32, ext='EXTEND', rough=0.8):
    cache = kit.__dict__.setdefault("_veh_tex", {})
    key = (name, emit, ext)
    if key not in cache:
        cache[key] = tex_mat(name, make(), emit, rough=rough, ext=ext)
    return cache[key]


def see_through(kit, name, make, alpha, emit=0.3):
    """Tinted glass: constant alpha (exported as a __blend material)."""
    cache = kit.__dict__.setdefault("_veh_tex", {})
    if name not in cache:
        m = tex_mat(name, make(), emit, rough=0.2)
        p = next(nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
        p.inputs["Alpha"].default_value = alpha
        cache[name] = m
    return cache[name]


def prefixed(asset, fn):
    """Build, then prefix every descendant name with the asset name exactly once."""
    def build(kit, root):
        fn(kit, root, asset)
        for ob in root.children_recursive:
            if not ob.name.startswith(asset):
                ob.name = f"{asset} {ob.name}"
    return build


def socket(kit, A, purpose, parent, loc, rot=(0, 0, 0)):
    s = kit.empty(f"{A} socket {purpose}", parent, loc, rot)
    s.empty_display_type = 'ARROWS'
    s.empty_display_size = 0.4
    return s


def close(mb):
    """Weld a face soup into a closed solid and point every normal outward."""
    bmesh.ops.remove_doubles(mb.bm, verts=mb.bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(mb.bm, faces=mb.bm.faces)
    return mb


def beam(kit, name, a, b, w, d, mat, parent, up=(0, 0, 1)):
    """Box from point a to point b: w across (perpendicular to up), d along up."""
    a, b = Vector(a), Vector(b)
    t = (b - a).normalized()
    s = Vector(up).cross(t)
    s = s.normalized() if s.length > 1e-4 else Vector((1, 0, 0))
    u = t.cross(s).normalized()
    mb = MB()
    corners = {}
    for i, sx in enumerate((-1, 1)):
        for j, sy in enumerate((-1, 1)):
            for k, p in enumerate((a, b)):
                corners[(i, j, k)] = p + s * sx * w / 2 + u * sy * d / 2
    for q in (((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)), ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)),
              ((0, 0, 0), (0, 0, 1), (1, 0, 1), (1, 0, 0)), ((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),
              ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)), ((1, 0, 0), (1, 0, 1), (1, 1, 1), (1, 1, 0))):
        mb.face([corners[c] for c in q], [(0, 0), (1, 0), (1, 1), (0, 1)])
    close(mb)
    return mb.obj(kit, name, [mat], parent)


def ring_path(c, r, n, plane='xy'):
    pts = []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        ca, sa = math.cos(a) * r, math.sin(a) * r
        pts.append((c[0] + ca, c[1] + sa, c[2]) if plane == 'xy' else (c[0], c[1] + ca, c[2] + sa))
    return pts


def ring(kit, name, c, r, tr, mat, parent, n=12, plane='xy', sides=6):
    front = (0, 0, 1) if plane == 'xy' else (1, 0, 0)
    return tube(kit, name, ring_path(c, r, n, plane), tr, mat, parent, sides=sides, front=front, caps=(False, False))


def slant_box(kit, name, parent, xb, xt, yb, yt, z0, z1, mats, uv_side=(0, 0, 1, 1)):
    """Cabin block: bottom rectangle |x|<=xb, yb[0]..yb[1] at z0; top |x|<=xt, yt[0]..yt[1] at z1 (raked front).
    mats = [side, front, back, top]. Side UVs: u = 0 at the front on both sides (the -X side is mirrored)."""
    B = {(sx, e): Vector((sx * xb, yb[e], z0)) for sx in (-1, 1) for e in (0, 1)}
    T = {(sx, e): Vector((sx * xt, yt[e], z1)) for sx in (-1, 1) for e in (0, 1)}
    mb = MB()
    u0, v0, u1, v1_ = uv_side
    for sx in (1, -1):
        def uvs(p):
            f = (p.y - yb[0]) / (yb[1] - yb[0])
            return (u0 + (u1 - u0) * f, v0 + (v1_ - v0) * (p.z - z0) / (z1 - z0))
        q = [B[(sx, 0)], B[(sx, 1)], T[(sx, 1)], T[(sx, 0)]]
        mb.face(q, [uvs(p) for p in q], 0)
    mb.face([B[(1, 0)], B[(-1, 0)], T[(-1, 0)], T[(1, 0)]], [(1, 0), (0, 0), (0, 1), (1, 1)], 1)
    mb.face([B[(-1, 1)], B[(1, 1)], T[(1, 1)], T[(-1, 1)]], [(1, 0), (0, 0), (0, 1), (1, 1)], 2)
    mb.face([T[(1, 0)], T[(-1, 0)], T[(-1, 1)], T[(1, 1)]], [(0, 0), (1, 0), (1, 1), (0, 1)], 3)
    mb.face([B[(1, 0)], B[(1, 1)], B[(-1, 1)], B[(-1, 0)]], [(0, 0)] * 4, 3)
    close(mb)
    return mb.obj(kit, name, mats, parent)


# ================================================================ Police Car
CL, CW = 4.9, 0.95          # body length, half width
PXM = 128 / CL              # side texture texels per meter (both axes)
P_BLACK, P_WHITE = "#221d33", "#f6f3ff"
WB = 1.45                   # wheel center |y|
WR = 0.34                   # wheel radius


def tex_police_side():
    """128x64: rows 0-31 the +X side (front at u=0), rows 32-63 the -X side (front at u=1)."""
    c = Canvas(128, 64, P_BLACK)
    for r0, flip in ((0, False), (32, True)):
        X = (lambda y: int((CL / 2 - y) * PXM)) if flip else (lambda y: int((y + CL / 2) * PXM))
        R = lambda z: r0 + int((z - 0.25) * PXM)
        xa, xb = sorted((X(-0.95), X(1.35)))
        c.rect(xa, R(0.36), xb, r0 + 31, P_WHITE)                 # white doors (black rocker below)
        for y in (-0.95, 0.3, 1.35):                              # door seams
            c.rect(X(y), R(0.36), X(y), R(0.97), "#5d5880")
        c.rect(xa, R(0.36), xb, R(0.36), "#5d5880")
        for y in (0.12, 1.2):                                     # door handles
            hx = X(y)
            c.rect(min(hx, hx + (2 if flip else -2)), R(0.86), max(hx, hx + (2 if flip else -2)), R(0.86), "#4a4566")
        fc = (X(-0.95) + X(0.3)) // 2                             # front door center
        # blue pinstripe along the doors, broken by the lettering
        c.rect(xa + 1, R(0.52), xb - 1, R(0.53), "#3a6cff")
        txt_c(c, "POLICE", fc + 1, R(0.9), INK, k=1, ky=2)
        # badge on the rear door: gold star on a blue disc with a gold rim
        bc, by = (X(0.3) + X(1.35)) // 2, R(0.7)
        disc(c, bc, by, 5, "#c9922a")
        disc(c, bc, by, 4, "#2a3fb8")
        for dx, dy in ((0, 3), (-1, 2), (0, 2), (1, 2), (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1),
                       (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (-2, -1), (-1, -1), (1, -1), (2, -1), (-2, -2), (2, -2)):
            c.set(bc + dx, by + dy, "#ffd84a")
        # unit number on the rear quarter
        rq = X(1.95)
        txt_c(c, "13", rq, R(0.9), P_WHITE)
    return c


def tex_police_roof():
    c = Canvas(32, 32, P_WHITE)
    c.speckle(random.Random(7), ["#e4e0f4"], 20)
    txt_c(c, "13", 16, 27, INK, k=3)
    return c


def tex_grille():
    c = Canvas(16, 8, "#14101e")
    for y in (1, 3, 5):
        c.rect(0, y, 15, y, "#a9a2e0")
    c.rect(7, 0, 8, 7, "#a9a2e0")
    return c


def tex_lens(col):
    c = Canvas(16, 8, col)
    mix = '#' + ''.join('%02x' % ((int(col[i:i + 2], 16) + 255) // 2) for i in (1, 3, 5))
    c.rect(2, 2, 13, 5, mix)
    c.rect(5, 3, 10, 4, "#ffffff")
    c.rect(0, 0, 15, 0, hex_scale(col, 0.7))
    return c


def tex_plate():
    c = Canvas(16, 8, WHITE)
    c.rect(0, 7, 15, 7, BLUE)
    txt(c, "PD13", 0, 5, "#3a3fb8")
    return c


def tex_tint():
    c = Canvas(16, 16, "#1c2246")
    for x0 in (2, 9):
        for i in range(6):
            c.set(x0 + i, 4 + i, "#5a6cc0")
    return c


def tex_officer_face(mustache):
    c = Canvas(32, 32, SKIN)
    for x in range(32):
        if x < 9 or x > 23:
            c.rect(x, 12, x, 31, "#3a2418")
    c.rect(9, 27, 23, 31, "#3a2418")
    if mustache:
        c.rect(13, 21, 14, 22, INK); c.rect(18, 21, 19, 22, INK)
        c.rect(13, 14, 19, 15, "#3a2418")
    else:
        c.rect(11, 20, 21, 22, INK); c.rect(15, 21, 17, 21, "#555a80")   # sunglasses
        c.rect(14, 14, 18, 14, "#a8505a")
    c.dots([(16, 17), (16, 18)], "#e89a7a")
    return c


def police_wheel(kit, name, parent, loc, side, tire, steel, cap):
    piv = kit.empty(name, parent, loc)
    tube(kit, name + " tire", [(-0.12, 0, 0), (0.12, 0, 0)], [WR, WR], tire, piv, sides=12, front=(0, 0, 1))
    tube(kit, name + " rim", [(side * 0.115, 0, 0), (side * 0.128, 0, 0)], 0.22, steel, piv, sides=12, front=(0, 0, 1))
    tube(kit, name + " cap", [(side * 0.125, 0, 0), (side * 0.155, 0, 0)], [0.085, 0.06], cap, piv, sides=6, front=(0, 0, 1))
    return piv


def officer(kit, p, parent, nm, x, wheel_hands, mustache):
    navy = solid(kit, "uniform navy", "#2c3480", shade="#232a6a")
    black = solid(kit, "cap brim", INK, 0.15)
    skin = solid(kit, "skin", SKIN)
    face = tx(kit, f"officer face {nm}", lambda: tex_officer_face(mustache))
    hip = kit.empty(f"{p} officer {nm}", parent, (x, 0.1, 0.62))
    tube(kit, f"{p} officer {nm} torso", [(0, 0, 0), (0, 0, 0.22), (0, 0.01, 0.4), (0, 0.02, 0.47)],
         [(0.16, 0.11), (0.17, 0.11), (0.21, 0.12), (0.09, 0.07)], navy, hip, sides=6)
    tbox(kit, f"{p} officer {nm} chest badge", (0.09, -0.115, 0.36), (0.05, 0.01, 0.06), solid(kit, "badge gold", "#ffc83a", 0.8), hip)
    head = kit.empty(f"{p} officer {nm} head", hip, (0, 0.02, 0.46))
    tube(kit, f"{p} officer {nm} head", [(0, 0, 0), (0, 0, 0.05), (0, -0.005, 0.09), (0, -0.01, 0.16), (0, 0, 0.22), (0, 0, 0.25)],
         [0.048, 0.055, 0.088, 0.096, 0.088, 0.04], face, head, sides=8)
    tube(kit, f"{p} officer {nm} cap", [(0, 0.005, 0.18), (0, 0.005, 0.24), (0, 0.0, 0.29)], [(0.1, 0.105), (0.108, 0.115), (0.112, 0.12)],
         navy, head, sides=8)
    tbox(kit, f"{p} officer {nm} cap brim", (0, -0.11, 0.185), (0.17, 0.09, 0.02), black, head, rot=(-12, 0, 0))
    tbox(kit, f"{p} officer {nm} cap badge", (0, -0.112, 0.245), (0.045, 0.012, 0.045), solid(kit, "badge gold", "#ffc83a", 0.8), head)
    for sx, side in ((1, "L"), (-1, "R")):
        target = (sx * 0.13, -0.5, 0.4) if wheel_hands else (sx * 0.17, -0.3, 0.12)
        player_arm(kit, hip, f"{p} officer {nm} arm {side}", (sx * 0.19, 0.0, 0.42), target, navy, skin)


def build_police_car(kit, root, p):
    side = tx(kit, "police side", tex_police_side)
    black = solid(kit, "police black", P_BLACK, shade="#1a1628")
    white = solid(kit, "police white", P_WHITE, shade="#e2def2")
    under = solid(kit, "undercarriage", "#120e1c", 0.1)
    trim = solid(kit, "police trim", "#3a3550", shade="#2e2a42")
    chrome = solid(kit, "chrome", STEEL, shade="#a9a2e0")
    tint = see_through(kit, "police tint", tex_tint, 0.62)
    body = kit.empty(f"{p} body", root)

    # lower body: side profile extruded across X, arches cut for the wheels
    upper = [(-2.45, 0.36), (-2.45, 0.78), (-2.37, 0.87), (-1.0, 0.95), (-0.92, 0.97), (1.36, 0.97), (1.46, 0.95),
             (2.38, 0.92), (2.45, 0.84), (2.45, 0.36), (2.37, 0.3)]
    lower = []
    for yc in (WB, -WB):
        lower += [(yc + 0.44 * math.cos(math.radians(a)), 0.32 + 0.44 * math.sin(math.radians(a))) for a in range(0, 181, 30)]
    lower += [(-2.37, 0.3)]
    prof = upper + lower
    mb = MB()
    for sx in (1, -1):
        r0 = 0 if sx > 0 else 32
        mb.face([(sx * CW, y, z) for y, z in prof],
                [((y + CL / 2) / CL if sx > 0 else (CL / 2 - y) / CL, (r0 + (z - 0.25) * PXM) / 64) for y, z in prof], 0)
    n = len(prof)
    for k in range(n):
        a, b = prof[k], prof[(k + 1) % n]
        mi = 1 if k < len(upper) - 1 else 2
        mb.face([(CW, a[0], a[1]), (CW, b[0], b[1]), (-CW, b[0], b[1]), (-CW, a[0], a[1])],
                [(0, 0), (1, 0), (1, 1), (0, 1)], mi)
    close(mb)
    mb.obj(kit, f"{p} hull", [side, black, under], body)
    tbox(kit, f"{p} underbody", (0, 0, 0.42), (1.5, 4.4, 0.3), under, body)

    # greenhouse: tinted glass shell, white pillars, white roof with the unit number
    bf, br, tf, tr = (-0.92, 1.36, -0.22, 0.86)
    xb, xt, zb, zt = 0.86, 0.74, 0.97, 1.46
    mb = MB()
    Bf = lambda sx: (sx * xb, bf, zb); Br = lambda sx: (sx * xb, br, zb)
    Tf = lambda sx: (sx * xt, tf, zt); Tr = lambda sx: (sx * xt, tr, zt)
    full = [(0, 0), (1, 0), (1, 1), (0, 1)]
    mb.face([Bf(1), Bf(-1), Tf(-1), Tf(1)], full)
    mb.face([Br(-1), Br(1), Tr(1), Tr(-1)], full)
    for sx in (1, -1):
        mb.face([Bf(sx), Br(sx), Tr(sx), Tf(sx)], full)
    mb.face([Tf(1), Tf(-1), Tr(-1), Tr(1)], full)
    mb.face([Bf(1), Br(1), Br(-1), Bf(-1)], full)
    close(mb)
    mb.obj(kit, f"{p} windows", [tint], body)
    tbox(kit, f"{p} roof", (0, (tf + tr) / 2, zt + 0.025), (2 * xt + 0.06, tr - tf + 0.08, 0.05),
         tx(kit, "police roof", tex_police_roof), body, uv={'all': (0.0, 0.0, 0.05, 0.05), 'pz': (0, 0, 1, 1)})
    for sx in (1, -1):
        beam(kit, f"{p} pillar A {sx}", Bf(sx), (sx * xt, tf, zt + 0.01), 0.08, 0.08, white, body, up=(0, 1, 0))
        beam(kit, f"{p} pillar C {sx}", Br(sx), (sx * xt, tr, zt + 0.01), 0.08, 0.12, white, body, up=(0, 1, 0))
        beam(kit, f"{p} pillar B {sx}", (sx * (xb - 0.005), 0.32, zb), (sx * (xt - 0.005), 0.32, zt), 0.07, 0.1, white, body,
             up=(0, 1, 0))
        beam(kit, f"{p} belt trim {sx}", (sx * (CW - 0.06), bf - 0.05, zb + 0.01), (sx * (CW - 0.06), br + 0.05, zb + 0.01),
             0.1, 0.03, trim, body)
        tbox(kit, f"{p} mirror {sx}", (sx * 1.02, -0.8, 1.06), (0.1, 0.07, 0.11), black, body)
        tbox(kit, f"{p} mirror stalk {sx}", (sx * 0.95, -0.8, 1.02), (0.1, 0.03, 0.03), black, body)

    # interior: dash, steering wheel, seats and the two officers
    tbox(kit, f"{p} dash", (0, -0.72, 1.02), (1.66, 0.36, 0.12), solid(kit, "dash", "#2b2540", 0.2), body)
    ring(kit, f"{p} steering wheel", (0.42, -0.45, 1.06), 0.17, 0.02, black, body, n=10, sides=4).rotation_euler = (math.radians(62), 0, 0)
    seat = solid(kit, "seat", "#3a3352", shade="#2e2842")
    for sx in (1, -1):
        tbox(kit, f"{p} seat back {sx}", (sx * 0.42, 0.34, 1.0), (0.5, 0.14, 0.62), seat, body, rot=(-8, 0, 0))
        tbox(kit, f"{p} headrest {sx}", (sx * 0.42, 0.38, 1.36), (0.28, 0.12, 0.16), seat, body)
    officer(kit, p, body, "driver", 0.42, True, True)
    officer(kit, p, body, "partner", -0.42, False, False)
    cage = solid(kit, "cage", "#6d6890", 0.25)
    for i in range(7):
        x = -0.78 + i * 0.26
        tube(kit, f"{p} cage bar {i}", [(x, 0.62, 0.97), (x * 0.92, 0.62, 1.42)], 0.012, cage, body, sides=4)
    tube(kit, f"{p} cage top", [(-0.74, 0.62, 1.42), (0.74, 0.62, 1.42)], 0.015, cage, body, sides=4, front=(0, 0, 1))

    # light bar: red half +X, blue half -X
    lb = kit.empty(f"{p} light bar", body, (0, -0.02, zt + 0.05))
    tbox(kit, f"{p} light bar base", (0, 0, 0.03), (1.4, 0.34, 0.06), black, lb)
    for sx, col, nm in ((1, "#ff1030", "red"), (-1, "#1438ff", "blue")):
        tbox(kit, f"{p} light bar {nm}", (sx * 0.38, 0, 0.14), (0.6, 0.3, 0.17), tx(kit, f"bar {nm}", lambda col=col: tex_lens(col), 4.5),
             lb, taper=(0.94, 0.78))
        tbox(kit, f"{p} light bar {nm} cap", (sx * 0.69, 0, 0.12), (0.04, 0.3, 0.14), black, lb)
        point_light(kit, lb, f"{p} {nm} glow", (sx * 0.5, 0, 0.35), col, 160, 7.0, 0.3)
    tbox(kit, f"{p} light bar center", (0, 0, 0.12), (0.14, 0.26, 0.12), solid(kit, "bar white", "#fff4dc", 1.6), lb)
    tbox(kit, f"{p} light bar strap", (0, 0, 0.07), (0.16, 0.36, 0.04), black, lb)

    # front: bumper, grille, lights, push bar
    tbox(kit, f"{p} front bumper", (0, -2.49, 0.46), (1.94, 0.12, 0.2), trim, body)
    tbox(kit, f"{p} grille", (0, -2.455, 0.68), (0.66, 0.02, 0.16), tx(kit, "police grille", tex_grille), body)
    head = solid(kit, "headlight", "#fff4c8", 2.4)
    for sx in (1, -1):
        tbox(kit, f"{p} headlight {sx}", (sx * 0.64, -2.458, 0.69), (0.42, 0.02, 0.15), head, body)
        tbox(kit, f"{p} turn signal {sx}", (sx * 0.64, -2.458, 0.575), (0.3, 0.02, 0.06), solid(kit, "turn signal", ORNG, 1.2), body)
        tbox(kit, f"{p} taillight {sx}", (sx * 0.62, 2.458, 0.73), (0.48, 0.02, 0.16), solid(kit, "taillight", RED, 1.8), body)
        tbox(kit, f"{p} reverse light {sx}", (sx * 0.31, 2.458, 0.73), (0.12, 0.02, 0.16), solid(kit, "reverse light", WHITE, 0.6), body)
    plate = tx(kit, "police plate", tex_plate)
    tbox(kit, f"{p} rear bumper", (0, 2.49, 0.46), (1.94, 0.12, 0.2), trim, body)
    tbox(kit, f"{p} rear plate", (0, 2.462, 0.62), (0.34, 0.02, 0.17), plate, body, uv={'all': (0, 0, 0.05, 0.05), 'py': (1, 0, 0, 1)})
    pb = solid(kit, "push bar", "#14101e", 0.15, shade="#262040")
    for sx in (1, -1):
        tube(kit, f"{p} push bar post {sx}", [(sx * 0.33, -2.64, 0.3), (sx * 0.33, -2.64, 0.9)], 0.04, pb, body, sides=6)
        tbox(kit, f"{p} push bar pad {sx}", (sx * 0.33, -2.69, 0.62), (0.1, 0.05, 0.5), solid(kit, "rubber pad", "#2e2840", 0.12), body)
        tbox(kit, f"{p} push bar mount {sx}", (sx * 0.33, -2.58, 0.46), (0.08, 0.14, 0.08), pb, body)
    for z in (0.52, 0.86):
        tube(kit, f"{p} push bar rail {z}", [(-0.42, -2.64, z), (0.42, -2.64, z)], 0.035, pb, body, sides=6, front=(0, 0, 1))
    tbox(kit, f"{p} front plate", (0, -2.67, 0.36), (0.34, 0.02, 0.17), plate, body, uv={'all': (0, 0, 0.05, 0.05), 'ny': (0, 0, 1, 1)})
    # spotlight on the driver's A pillar, trunk antenna
    tube(kit, f"{p} spotlight", [(1.0, -0.78, 1.12), (1.0, -0.98, 1.12)], [0.065, 0.075], chrome, body, sides=8, side=(1, 0, 0))
    tube(kit, f"{p} spotlight stem", [(0.93, -0.84, 0.98), (1.0, -0.86, 1.08)], 0.015, chrome, body, sides=4)
    tube(kit, f"{p} antenna", [(-0.55, 2.15, 0.92), (-0.58, 2.3, 1.75)], [0.012, 0.005], black, body, sides=3)

    tire = solid(kit, "tire", "#1a1626", 0.12, shade="#2a2438")
    steel = solid(kit, "steel wheel", "#3a3550", 0.2)
    for nm, x, y in (("FL", 0.8, -WB), ("FR", -0.8, -WB), ("RL", 0.8, WB), ("RR", -0.8, WB)):
        police_wheel(kit, f"{p} wheel {nm}", root, (x, y, WR), 1 if x > 0 else -1, tire, steel, chrome)
    kit.empty(f"{p} socket light bar", lb, (0, 0, 0.3))


# ================================================================ Yacht
# stations: (y, half width, sheer z, knuckle z, chine z, keel z)
STATIONS = [(-7.0, 0.05, 1.60, 1.48, 1.40, 1.34), (-6.4, 0.78, 1.52, 0.80, 0.50, 0.25), (-5.4, 1.45, 1.42, 0.32, 0.0, -0.45),
            (-3.8, 1.9, 1.32, 0.15, -0.15, -0.85), (-1.5, 2.07, 1.24, 0.15, -0.22, -1.0), (2.5, 2.1, 1.2, 0.15, -0.25, -1.0),
            (6.3, 2.05, 1.2, 0.15, -0.2, -0.8)]
YV = lambda z: (z + 1.0) / 2.7                 # hull texture v (shared by the transom)


def hull_at(y):
    for a, b in zip(STATIONS, STATIONS[1:]):
        if a[0] <= y <= b[0]:
            f = (y - a[0]) / (b[0] - a[0])
            return a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f
    s = STATIONS[0] if y < STATIONS[0][0] else STATIONS[-1]
    return s[1], s[2]


def hull_rows(c, x, dz):
    """Paint one texel column of the hull bands; dz lifts the stripes toward the bow."""
    R = lambda z: int(YV(z) * 64)
    c.rect(x, 0, x, R(-0.02), "#3b3f9e")
    c.rect(x, R(-0.02), x, R(0.08), "#1b1033")
    c.rect(x, R(0.5 + dz), x, R(0.57 + dz), MINT)
    c.rect(x, R(0.66 + dz), x, R(0.9 + dz), PINK)


def tex_hull():
    c = Canvas(64, 64, WHITE)
    for x in range(64):
        y = -7 + 14 * (x + 0.5) / 64
        hull_rows(c, x, (hull_at(y)[1] - 1.2) * 0.85)
    R = lambda z: int(YV(z) * 64)
    for y0, y1 in ((-4.7, -2.6), (-2.1, 0.0), (0.6, 2.4)):         # long hull windows
        x0, x1 = int((y0 + 7) / 14 * 64), int((y1 + 7) / 14 * 64)
        c.rect(x0, R(0.26), x1, R(0.42), "#1e2450")
        c.rect(x0 + 1, R(0.38), x0 + 2, R(0.38), "#5a6cc0")
    return c


def tex_transom():
    c = Canvas(64, 64, WHITE)
    for x in range(64):
        hull_rows(c, x, 0.0)
    txt_c(c, "SOLITAIRE", 32, int(YV(1.14) * 64), "#2a2f6b")
    return c


def tex_teak():
    c = Canvas(32, 32, "#d9a066")
    R = random.Random(11)
    c.speckle(R, ["#c98f58", "#e4b07a"], 90)
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 31, "#7a4a2e")
    for x in range(2, 32, 4):
        c.set(x, R.randrange(32), "#7a4a2e")
    return c


def tex_cabin_side():
    """u = 0 at the cabin front on both sides; the window band is raked at the front."""
    c = Canvas(64, 32, WHITE)
    for r in range(9, 26):
        c.rect(3 + (r - 9) // 2, r, 61, r, "#1e2450")
    for x in (24, 25, 45, 46):
        c.rect(x, 9, x, 25, WHITE)
    for x0 in (12, 29, 50):
        for i in range(6):
            c.set(x0 + i, 13 + i, "#4a5aa8"); c.set(x0 + i + 1, 13 + i, "#4a5aa8")
    c.rect(0, 4, 63, 4, MINT)
    c.rect(0, 28, 63, 28, PINK)
    return c


def tex_cabin_front():
    c = Canvas(32, 32, WHITE)
    c.rect(2, 7, 29, 27, "#1e2450")
    c.rect(15, 7, 16, 27, WHITE)
    for x0 in (5, 19):
        for i in range(7):
            c.set(x0 + i, 10 + i, "#4a5aa8")
    c.rect(0, 3, 31, 3, MINT)
    return c


def tex_cabin_back():
    c = Canvas(32, 32, WHITE)
    c.rect(3, 2, 28, 26, "#1e2450")
    c.rect(15, 2, 16, 26, "#d9d4ff")
    c.rect(3, 26, 28, 26, "#d9d4ff")
    c.rect(13, 12, 13, 15, STEEL); c.rect(18, 12, 18, 15, STEEL)
    c.rect(0, 29, 31, 29, PINK)
    return c


def tex_cushion(col):
    c = Canvas(16, 16, col)
    c.rect(0, 0, 15, 0, hex_scale(col, 0.75)); c.rect(0, 15, 15, 15, WHITE)
    c.dots([(4, 5), (11, 5), (4, 10), (11, 10)], hex_scale(col, 0.7))
    return c


def build_yacht(kit, root, p):
    hull_m = tx(kit, "yacht hull", tex_hull)
    tran_m = tx(kit, "yacht transom", tex_transom)
    teak = tx(kit, "teak", tex_teak, ext='REPEAT')
    white = solid(kit, "yacht white", WHITE, shade="#ece4f0")
    steel = solid(kit, "rail steel", STEEL, 0.4, shade="#a9a2e0")
    dark = solid(kit, "yacht dark", "#1e2450", 0.2)
    side_m = tx(kit, "cabin side", tex_cabin_side)
    front_m = tx(kit, "cabin front", tex_cabin_front)
    back_m = tx(kit, "cabin back", tex_cabin_back)

    # hull: lofted stations, transom, deck
    secs = []
    for y, w, zs, zk_, zc, zk in STATIONS:
        secs.append([(w, y, zs), (0.99 * w, y, zk_), (0.85 * w, y, zc), (0, y, zk), (-0.85 * w, y, zc), (-0.99 * w, y, zk_),
                     (-w, y, zs)])
    huv = lambda q: ((q[1] + 7) / 14, YV(q[2]))
    mb = MB()
    for s0, s1 in zip(secs, secs[1:]):
        for j in range(6):
            q = [s0[j], s0[j + 1], s1[j + 1], s1[j]]
            mb.face(q, [huv(v) for v in q], 0)
        q = [s0[0], s0[6], s1[6], s1[0]]
        mb.face(q, [(v[0] / 1.5, v[1] / 1.5) for v in q], 2)
    mb.face(secs[0], [huv(v) for v in secs[0]], 0)
    mb.face(secs[-1], [((2.1 - v[0]) / 4.2, YV(v[2])) for v in secs[-1]], 1)
    close(mb)
    hull = mb.obj(kit, f"{p} hull", [hull_m, tran_m, teak], root)
    rub = solid(kit, "rub rail", "#d9d4ff", 0.35, shade="#b9b2e6")
    for sx in (1, -1):
        pts = [(sx * (s[1] + 0.03), s[0], s[2] - 0.03) for s in STATIONS[1:]]
        tube(kit, f"{p} rub rail {sx}", pts, 0.045, rub, root, sides=4, side=(0, 0, 1))
    # swim platform and ladder
    tbox(kit, f"{p} swim platform", (0, 6.68, 0.3), (3.9, 0.76, 0.12), teak, root, uv={'all': (0, 0, 2.6, 0.5)})
    tbox(kit, f"{p} swim platform base", (0, 6.6, 0.18), (3.7, 0.6, 0.14), white, root)
    for sx in (0.35, -0.35):
        tube(kit, f"{p} swim ladder {sx}", [(sx, 6.95, 0.36), (sx, 7.0, 0.1), (sx, 7.0, -0.5)], 0.02, steel, root, sides=4)
    for i, z in enumerate((-0.1, -0.35)):
        tube(kit, f"{p} swim ladder step {i}", [(-0.35, 7.0, z), (0.35, 7.0, z)], 0.02, steel, root, sides=4, front=(0, 0, 1))

    # level 1: salon with a raked windshield
    S1 = 2.85                       # salon roof underside
    F = S1 + 0.12                   # flybridge floor (salon roof top)
    slant_box(kit, f"{p} salon", root, 1.72, 1.58, (-3.7, 4.2), (-2.0, 4.2), 1.15, S1, [side_m, front_m, back_m, white])
    tbox(kit, f"{p} salon roof", (0, 1.5, S1 + 0.06), (3.6, 7.6, 0.12), white, root)
    tbox(kit, f"{p} salon roof trim", (0, 1.5, S1 - 0.02), (3.54, 7.54, 0.05), solid(kit, "trim pink", PINK, 0.4), root)
    for sx in (1, -1):
        tube(kit, f"{p} roof post {sx}", [(sx * 1.66, 5.1, 1.2), (sx * 1.66, 5.1, S1)], 0.05, steel, root, sides=6)
    # foredeck sunpad and anchor
    tbox(kit, f"{p} foredeck trunk", (0, -4.6, 1.45), (2.2, 1.6, 0.3), white, root)
    for i, (y, col) in enumerate(((-5.0, PINK), (-4.2, MINT))):
        tbox(kit, f"{p} sunpad {i}", (0, y, 1.67), (2.0, 0.74, 0.14), tx(kit, f"cushion {col}", lambda col=col: tex_cushion(col)), root,
             uv={'all': (0, 0, 1, 0.12), 'pz': (0, 0, 1, 1)})
    tbox(kit, f"{p} anchor", (0, -7.0, 1.12), (0.18, 0.12, 0.3), solid(kit, "anchor", "#5b5fc0"), root)
    tbox(kit, f"{p} windlass", (0, -6.1, 1.58), (0.3, 0.3, 0.16), steel, root)

    # level 2: sky lounge with a hardtop reaching back over the helm
    slant_box(kit, f"{p} upper cabin", root, 1.4, 1.22, (-1.4, 1.2), (-0.1, 1.2), F, F + 1.0, [side_m, front_m, back_m, white])
    tbox(kit, f"{p} upper roof", (0, 0.45, F + 1.05), (2.7, 3.9, 0.1), white, root)
    tbox(kit, f"{p} upper roof trim", (0, 0.45, F + 0.98), (2.64, 3.84, 0.05), solid(kit, "trim mint", MINT, 0.4), root)
    for sx in (1, -1):
        tube(kit, f"{p} hardtop post {sx}", [(sx * 1.2, 2.3, F), (sx * 1.2, 2.3, F + 1.0)], 0.04, steel, root, sides=6)
    for sx, col, nm in ((1, RED, "port"), (-1, "#3fff8a", "starboard")):
        tbox(kit, f"{p} nav light {nm}", (sx * 1.41, -0.9, F + 0.5), (0.05, 0.22, 0.12), solid(kit, f"nav {nm}", col, 2.4), root)

    # flybridge on the salon roof behind the sky lounge: helm, seats, railing
    pinkc = tx(kit, f"cushion {PINK}", lambda: tex_cushion(PINK))
    mintc = tx(kit, f"cushion {MINT}", lambda: tex_cushion(MINT))
    cush = {'all': (0, 0, 1, 0.12), 'pz': (0, 0, 1, 1)}
    tbox(kit, f"{p} fly bench", (0, 4.8, F + 0.22), (2.6, 0.55, 0.45), white, root)
    tbox(kit, f"{p} fly bench cushion", (0, 4.77, F + 0.49), (2.5, 0.5, 0.1), pinkc, root, uv=cush)
    tbox(kit, f"{p} fly bench back", (0, 5.07, F + 0.68), (2.5, 0.12, 0.45), pinkc, root, uv={'all': (0, 0, 1, 0.12), 'ny': (0, 0, 1, 1)})
    for sx in (1, -1):
        tbox(kit, f"{p} fly side seat {sx}", (sx * 1.3, 3.9, F + 0.22), (0.5, 1.3, 0.45), white, root)
        tbox(kit, f"{p} fly side cushion {sx}", (sx * 1.3, 3.9, F + 0.49), (0.46, 1.2, 0.1), mintc, root, uv=cush)
    tbox(kit, f"{p} fly table", (0, 3.9, F + 0.38), (1.0, 0.7, 0.06), teak, root, uv={'all': (0, 0, 0.6, 0.4)})
    tube(kit, f"{p} fly table leg", [(0, 3.9, F), (0, 3.9, F + 0.35)], 0.06, steel, root, sides=6)
    tbox(kit, f"{p} helm console", (0.6, 1.6, F + 0.4), (0.9, 0.5, 0.8), white, root, taper=(1.0, 0.6))
    tbox(kit, f"{p} helm screen", (0.6, 1.43, F + 0.75), (0.6, 0.04, 0.22), solid(kit, "helm screen", "#38f2c3", 1.2), root, rot=(-30, 0, 0))
    ring(kit, f"{p} helm wheel", (0.6, 1.95, F + 0.65), 0.18, 0.02, steel, root, n=10, sides=4).rotation_euler = (math.radians(70), 0, 0)
    tbox(kit, f"{p} helm seat", (0.6, 2.45, F + 0.3), (0.55, 0.5, 0.6), mintc, root, uv=cush)
    rail_h = 0.85
    for sx in (1, -1):
        tube(kit, f"{p} fly rail {sx}", [(sx * 1.75, 1.3, F + rail_h), (sx * 1.75, 5.25, F + rail_h), (0, 5.25, F + rail_h)],
             0.035, steel, root, sides=4)
        for y in (1.3, 2.6, 3.9, 5.25):
            tube(kit, f"{p} fly post {sx} {y}", [(sx * 1.75, y, F), (sx * 1.75, y, F + rail_h)], 0.025, steel, root, sides=4)

    # radar arch over the flybridge, raked aft
    arch = solid(kit, "arch", WHITE, shade="#ece4f0")
    A = F + 1.55
    for sx in (1, -1):
        beam(kit, f"{p} arch leg {sx}", (sx * 1.66, 2.7, F - 0.02), (sx * 1.3, 3.55, A), 0.14, 0.5, arch, root, up=(0, 1, 0))
        beam(kit, f"{p} arch stripe {sx}", (sx * 1.74, 2.75, F + 0.1), (sx * 1.38, 3.55, A - 0.1), 0.02, 0.18,
             solid(kit, "trim pink", PINK, 0.4), root, up=(0, 1, 0))
    tbox(kit, f"{p} arch top", (0, 3.6, A + 0.05), (2.95, 0.6, 0.2), arch, root)
    lowball(kit, f"{p} radar dome", (0, 3.6, A + 0.27), (0.36, 0.36, 0.16), white, root, smooth=False)
    for sx in (1, -1):
        tube(kit, f"{p} whip {sx}", [(sx * 1.25, 3.7, A + 0.15), (sx * 1.3, 3.9, A + 1.3)], [0.025, 0.008], white, root, sides=3)
    tbox(kit, f"{p} mast light", (0, 3.8, A + 0.25), (0.08, 0.08, 0.14), solid(kit, "mast light", "#fff4dc", 2.4), root)

    # deck railings along the sheer with a gate gap on +X near the stern
    gate = (4.05, 4.95)
    ys = [6.2, 5.0, 3.8, 2.6, 1.4, 0.2, -1.0, -2.2, -3.4, -4.6, -5.6, -6.3]
    rail = lambda sx, y: (sx * (hull_at(y)[0] - 0.12), y, hull_at(y)[1] + 0.8)
    post = lambda nm, sx, y: tube(kit, nm, [(sx * (hull_at(y)[0] - 0.12), y, hull_at(y)[1]), rail(sx, y)], 0.025, steel, root, sides=4)
    tip = (0, -6.75, hull_at(-6.75)[1] + 0.8)
    path = [rail(-1, y) for y in [6.25] + ys[1:]] + [tip] + [rail(1, y) for y in ys[:0:-1] if y < gate[0]] + [rail(1, gate[0])]
    tube(kit, f"{p} deck rail", path, 0.03, steel, root, sides=4)
    tube(kit, f"{p} deck rail stern", [rail(1, gate[1]), rail(1, 6.25), (0.5, 6.25, 2.0)], 0.03, steel, root, sides=4)
    tube(kit, f"{p} deck rail stern L", [rail(-1, 6.25), (-0.5, 6.25, 2.0)], 0.03, steel, root, sides=4)
    for sx in (1, -1):
        for y in ys:
            if sx > 0 and gate[0] - 0.1 < y < gate[1] + 0.1:
                continue
            post(f"{p} rail post {sx} {y}", sx, y)
    post(f"{p} gate post a", 1, gate[0]); post(f"{p} gate post b", 1, gate[1])
    tbox(kit, f"{p} side door step", (2.0, sum(gate) / 2, 1.24), (0.18, 0.86, 0.06), teak, root, uv={'all': (0, 0, 0.3, 0.3)})
    # gangway, hinged at the side door and folded out over the dock
    gw = kit.empty(f"{p} gangway", root, (2.06, sum(gate) / 2, 1.24), (0, 7, 0))
    tbox(kit, f"{p} gangway plank", (0.85, 0, 0.0), (1.7, 0.62, 0.06), teak, gw, uv={'all': (0, 0, 0.5, 1.2)})
    for sy in (1, -1):
        tube(kit, f"{p} gangway rail {sy}", [(0.05, sy * 0.3, 0.03), (0.05, sy * 0.3, 0.85), (1.6, sy * 0.3, 0.85), (1.6, sy * 0.3, 0.03)],
             0.022, steel, gw, sides=4)
    socket(kit, p, "gangway", gw, (1.7, 0, 0.03))
    # fenders hanging over the +X side
    fend = solid(kit, "fender", WHITE, 0.35, shade="#e8e0f0")
    for i, y in enumerate((-2.2, 0.6, 3.0)):
        x = hull_at(y)[0] + 0.14
        tube(kit, f"{p} fender {i}", [(x, y, 0.3), (x, y, 0.42), (x, y, 0.82), (x, y, 0.94)], [0.08, 0.14, 0.14, 0.08],
             fend, root, sides=8)
        tube(kit, f"{p} fender line {i}", [(x, y, 0.94), (x - 0.12, y, hull_at(y)[1] + 0.3)], 0.01, solid(kit, "rope", "#ffe9b8"), root, sides=3)


# ================================================================ Harbor Dock
DL, DW = 26.0, 2.0
WATER_Z = -1.0


def tex_planks():
    c = Canvas(32, 32, "#c48a5a")
    R = random.Random(21)
    c.speckle(R, ["#b37a4c", "#d39a6a", "#a86e44"], 110)
    for y in range(0, 32, 4):
        c.rect(0, y, 31, y, "#5e3a2e")
        c.set(R.randrange(32), y + 2, "#8a5a3a")
    for x in (5, 26):
        for y in range(2, 32, 4):
            c.set(x, y, "#3a2a2e")
    return c


def tex_piling():
    c = Canvas(16, 64, "#7a5240")
    R = random.Random(22)
    c.speckle(R, ["#6a4434", "#8a6048"], 120)
    for x in (3, 9, 13):
        c.rect(x, 0, x, 63, "#5e3a2e")
    wl = int((WATER_Z + 3) / 3.5 * 64)
    c.rect(0, 0, 15, wl - 3, "#3a3156")
    c.rect(0, wl - 4, 15, wl + 2, "#3fae8a")
    c.speckle(R, ["#2f8a6e", WHITE], 30, 0, wl)
    c.rect(0, 62, 15, 63, "#a58466")
    return c


def tex_crate():
    c = Canvas(32, 32, "#d9a05a")
    c.speckle(random.Random(23), ["#c98f4a", "#e8b06a"], 70)
    for y in (0, 1, 30, 31):
        c.rect(0, y, 31, y, "#8a5226")
    for x in (0, 1, 30, 31):
        c.rect(x, 0, x, 31, "#8a5226")
    for i in range(28):
        c.set(2 + i, 2 + i, "#8a5226"); c.set(3 + i, 2 + i, "#8a5226")
    txt_c(c, "FISH", 16, 20, "#3a3fb8")
    return c


def tex_box():
    c = Canvas(16, 16, "#e0b47a")
    c.rect(0, 7, 15, 8, "#c99a5e")
    c.rect(6, 0, 9, 15, "#f0d9a8")
    return c


def tex_life_ring():
    c = Canvas(8, 32, WHITE)
    for y0 in (0, 16):
        c.rect(0, y0, 7, y0 + 7, RED)
    c.rect(0, 0, 7, 0, "#c9c2e6")
    return c


def tex_pier_sign():
    c = Canvas(64, 24, "#2a5aa8")
    c.rect(0, 0, 63, 1, WHITE); c.rect(0, 22, 63, 23, WHITE); c.rect(0, 0, 1, 23, WHITE); c.rect(62, 0, 63, 23, WHITE)
    txt_c(c, "PIER 9", 32, 17, WHITE, k=2)
    c.rect(4, 4, 59, 4, YEL)
    return c


def tex_rock(rand):
    c = Canvas(16, 16, "#8a84b8")
    c.speckle(rand, ["#6e6898", "#a49ed0", "#5e5888"], 90)
    return c


def bollard(kit, p, parent, nm, loc, iron, rope):
    b = kit.empty(f"{p} bollard {nm}", parent, loc)
    tube(kit, f"{p} bollard {nm} base", [(0, 0, 0), (0, 0, 0.06)], 0.2, iron, b, sides=8)
    tube(kit, f"{p} bollard {nm} post", [(0, 0, 0.05), (0, 0, 0.3), (0, 0, 0.38), (0, 0, 0.44)], [0.11, 0.09, 0.15, 0.12], iron, b, sides=8)
    for i, (r, z) in enumerate(((0.26, 0.04), (0.2, 0.11), (0.13, 0.17))):
        ring(kit, f"{p} bollard {nm} rope coil {i}", (0.42, 0.05, z), r, 0.045, rope, b, n=10, sides=5)
    tube(kit, f"{p} bollard {nm} rope wrap", ring_path((0, 0, 0.2), 0.11, 8), 0.035, rope, b, sides=4, front=(0, 0, 1),
         caps=(False, False))
    tube(kit, f"{p} bollard {nm} rope lead", [(0.1, 0.03, 0.2), (0.25, 0.06, 0.06), (0.42 - 0.26, 0.05, 0.04)], 0.035, rope, b, sides=4)
    return b


def lamp_post(kit, p, parent, nm, loc):
    lp = kit.empty(f"{p} lamp {nm}", parent, loc)
    iron = solid(kit, "lamp iron", "#2f3a6e", shade="#262f5a")
    glow = solid(kit, "lamp glow", "#ffd98a", 3.2, shade="#ffe9b8")
    tube(kit, f"{p} lamp {nm} base", [(0, 0, 0), (0, 0, 0.35)], [0.16, 0.11], iron, lp, sides=8)
    tube(kit, f"{p} lamp {nm} pole", [(0, 0, 0.3), (0, 0, 3.0)], [0.07, 0.055], iron, lp, sides=6)
    tube(kit, f"{p} lamp {nm} collar", [(0, 0, 2.95), (0, 0, 3.05)], 0.11, iron, lp, sides=8)
    tbox(kit, f"{p} lamp {nm} lantern", (0, 0, 3.27), (0.3, 0.3, 0.42), glow, lp, taper=(1.25, 1.25))
    for sx in (1, -1):
        for sy in (1, -1):
            beam(kit, f"{p} lamp {nm} frame {sx} {sy}", (sx * 0.15, sy * 0.15, 3.06), (sx * 0.19, sy * 0.19, 3.48), 0.03, 0.03, iron, lp)
    tbox(kit, f"{p} lamp {nm} roof", (0, 0, 3.58), (0.5, 0.5, 0.2), iron, lp, taper=(0.15, 0.15))
    tube(kit, f"{p} lamp {nm} finial", [(0, 0, 3.66), (0, 0, 3.82)], [0.04, 0.01], iron, lp, sides=4)
    kit.empty(f"{p} socket lamp {nm}", lp, (0, 0, 3.27))
    point_light(kit, lp, f"{p} lamp {nm} light", (0, 0, 3.1), "#ffd98a", 320, 10.0, 0.3)
    return lp


def build_dock(kit, root, p):
    planks = tx(kit, "dock planks", tex_planks, ext='REPEAT')
    pile_m = tx(kit, "piling", tex_piling)
    wood = solid(kit, "dock beam", "#6a4434", shade="#5a3828")
    iron = solid(kit, "bollard iron", "#3a3560", shade="#2e2a4e")
    rope = solid(kit, "rope", "#ffe9b8", shade="#e0c890")
    pier = kit.empty(f"{p} pier", root)
    tbox(kit, f"{p} deck", (0, -DL / 2, -0.07), (2 * DW, DL, 0.14), planks, pier,
         uv={'all': (0, 0, 0.1, 0.1), 'pz': (0, 0, 2, DL / 2)})
    for sx in (1, -1):
        tbox(kit, f"{p} fascia {sx}", (sx * (DW + 0.04), -DL / 2, -0.12), (0.08, DL, 0.3), wood, pier)
        tbox(kit, f"{p} stringer {sx}", (sx * 1.3, -DL / 2, -0.29), (0.22, DL, 0.3), wood, pier)
    tbox(kit, f"{p} stringer mid", (0, -DL / 2, -0.29), (0.22, DL, 0.3), wood, pier)
    tbox(kit, f"{p} end board", (0, -DL - 0.04, -0.12), (2 * DW + 0.16, 0.08, 0.3), wood, pier)
    rows = [-0.3 - 3.2 * k for k in range(9)]
    for i, y in enumerate(rows):
        tbox(kit, f"{p} pile cap {i}", (0, y, -0.32), (2 * DW + 0.5, 0.26, 0.26), wood, pier)
        for sx in (1, -1):
            top = 0.45 if i % 2 == 0 else -0.2
            tube(kit, f"{p} piling {i} {sx}", [(sx * 2.15, y, -3.0), (sx * 2.15, y, top)], 0.17, pile_m, pier, sides=8,
                 v=(0.0, (top + 3.0) / 3.5))
        if i % 2:
            beam(kit, f"{p} brace {i}", (-2.1, y + 0.18, -0.45), (2.1, y + 0.18, -2.3), 0.12, 0.2, wood, pier, up=(0, 1, 0))
    for i, y in enumerate((-DL + 0.3,)):
        tube(kit, f"{p} piling end", [(0, y - 0.2, -3.0), (0, y - 0.2, -0.2)], 0.17, pile_m, pier, sides=8, v=(0.0, 2.8 / 3.5))

    # bollards with rope coils, the yacht mooring on the +X side at the far end
    for nm, x, y in (("1", 1.65, -6.0), ("2", -1.65, -12.5), ("3", 1.65, -13.0), ("4", 1.65, -24.5), ("5", -1.65, -24.5)):
        b = bollard(kit, p, pier, nm, (x, y, 0.0), iron, rope)
        if x < 0:
            b.rotation_euler.z = math.pi
    socket(kit, p, "yacht", root, (2.0 + 0.55 + 2.1, -19.0, WATER_Z), (0, 0, 180))
    # life ring on a post
    lr = kit.empty(f"{p} life ring post", pier, (-1.85, -10.0, 0.0))
    tbox(kit, f"{p} life ring post", (0, 0, 0.75), (0.14, 0.14, 1.5), wood, lr)
    tbox(kit, f"{p} life ring post cap", (0, 0, 1.53), (0.2, 0.2, 0.06), solid(kit, "post cap", WHITE), lr)
    tbox(kit, f"{p} life ring hook", (0.1, 0, 1.25), (0.08, 0.04, 0.04), iron, lr)
    ring(kit, f"{p} life ring", (0.12, 0, 0.93), 0.3, 0.075, tx(kit, "life ring", tex_life_ring), lr, n=16, plane='yz', sides=6)
    # lamps
    lamp_post(kit, p, pier, "near", (-1.8, -7.5, 0.0))
    lamp_post(kit, p, pier, "far", (1.8, -18.5, 0.0))
    # crates and a stacked pallet near the shore end
    crate = tx(kit, "fish crate", tex_crate)
    for i, (x, y, z, rz, s) in enumerate(((1.35, -2.4, 0.0, 8, 0.7), (1.3, -3.25, 0.0, -5, 0.7), (1.33, -2.8, 0.7, 20, 0.62),
                                          (-1.5, -20.5, 0.0, 15, 0.6))):
        tbox(kit, f"{p} crate {i}", (0, 0, s / 2), (s, s, s), crate, pier, loc=(x, y, z), rot=(0, 0, rz))
    pal = kit.empty(f"{p} pallet", pier, (-1.35, -4.1, 0.0), (0, 0, 6))
    slat = solid(kit, "pallet wood", "#e0b070", shade="#c99a5e")
    for i, x in enumerate((-0.5, 0.0, 0.5)):
        tbox(kit, f"{p} pallet block {i}", (x, 0, 0.05), (0.12, 1.1, 0.1), slat, pal)
    for i in range(5):
        tbox(kit, f"{p} pallet slat {i}", (0, -0.48 + 0.24 * i, 0.12), (1.2, 0.16, 0.04), slat, pal)
    box = tx(kit, "cargo box", tex_box)
    k = 0
    for layer, z in enumerate((0.14, 0.44, 0.74)):
        for bx, by in ((-0.3, -0.27), (0.3, -0.27), (-0.3, 0.27), (0.3, 0.27)):
            if layer == 2 and bx > 0 and by > 0:
                continue
            tbox(kit, f"{p} pallet box {k}", (bx, by, z + 0.15), (0.56, 0.5, 0.3), box, pal, rot=(0, 0, kit.rand.uniform(-4, 4)))
            k += 1
    tbox(kit, f"{p} pallet strap", (0, 0, 0.6), (1.18, 0.04, 0.95), solid(kit, "strap", PINK, 0.4), pal)
    # PIER 9 sign at the shore end, readable from both sides
    sg = kit.empty(f"{p} sign", root, (-1.82, -0.45, 0.0))
    tube(kit, f"{p} sign post", [(0, 0, 0.0), (0, 0, 2.1)], 0.06, solid(kit, "sign post", "#2f3a6e"), sg, sides=6)
    tbox(kit, f"{p} sign board", (0, 0, 1.85), (1.1, 0.06, 0.42), tx(kit, "pier sign", tex_pier_sign), sg,
         uv={'all': (0, 0, 0.03, 0.03), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})


# ================================================================ Harbor Water
def tex_water():
    c = Canvas(32, 32, "#4fb8d8")
    R = random.Random(31)
    c.speckle(R, ["#46aed0", "#5cc4e0"], 120)
    for (x, y, n) in ((2, 4, 7), (18, 9, 6), (8, 15, 8), (24, 21, 7), (3, 26, 6), (14, 29, 5)):
        for i in range(n):
            c.set(x + i, y + (1 if i in (0, n - 1) else 0), "#8fe4f0")
        c.set(x + n // 2, y + 1, "#d8fbff")
        for i in range(0, n, 2):
            c.set(x + i + 1, y - 1, "#6fd0e6")
    return c


def build_water(kit, root, p):
    m = tx(kit, "harbor water", tex_water, emit=0.25, ext='REPEAT', rough=0.35)
    n, half = 8, 40.0
    mb = MB()
    step = 2 * half / n
    for i in range(n):
        for j in range(n):
            x0, y0 = -half + i * step, -half + j * step
            q = [(x0, y0, 0), (x0 + step, y0, 0), (x0 + step, y0 + step, 0), (x0, y0 + step, 0)]
            mb.face(q, [(v[0] / 4, v[1] / 4) for v in q])
    # short skirt around the edge so the slab has a visible thickness where it meets a shore
    corners = [(-half, -half), (half, -half), (half, half), (-half, half)]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        L = math.dist(a, b) / 4
        mb.face([(*a, -0.3), (*b, -0.3), (*b, 0), (*a, 0)], [(0, -0.075), (L, -0.075), (L, 0), (0, 0)])
    mb.obj(kit, f"{p} surface", [m], root)


# ================================================================ Lighthouse
def tex_tower():
    c = Canvas(32, 64, WHITE)
    for b in range(0, 5, 2):
        c.rect(0, b * 13, 31, b * 13 + 12, RED)
    for y in range(64):
        c.set(y % 32, y, hex_scale(RED, 0.9) if (y // 13) % 2 == 0 else "#ece4f0")
    for y0 in (20, 46):
        c.rect(15, y0, 16, y0 + 3, "#1e2450")
    return c


def tex_lamp_room():
    c = Canvas(32, 16, "#ffe14a")
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 15, "#4a3a2a")
    c.rect(0, 0, 31, 1, "#4a3a2a"); c.rect(0, 14, 31, 15, "#4a3a2a")
    c.rect(1, 6, 31, 9, "#fff7cc")
    return c


def build_lighthouse(kit, root, p):
    R = kit.rand
    rock = tx(kit, "lighthouse rock", lambda: tex_rock(R))
    rock2 = solid(kit, "rock moss", "#5aa08a", shade="#4a8a76")
    for i in range(11):
        a = 2 * math.pi * i / 11 + R.uniform(-0.2, 0.2)
        d = R.uniform(1.6, 2.7) if i % 3 else R.uniform(0.8, 1.4)
        r = R.uniform(0.9, 1.5)
        lowball(kit, f"{p} rock {i}", (math.cos(a) * d, math.sin(a) * d, R.uniform(-0.1, 0.4)), (r * 1.2, r, r * 0.85),
                rock if i % 4 else rock2, root, smooth=False)
    tube(kit, f"{p} plinth", [(0, 0, 0.6), (0, 0, 1.5)], [1.75, 1.65], solid(kit, "plinth", "#d9d4ff", shade="#b9b2e6"), root, sides=10)
    tube(kit, f"{p} tower", [(0, 0, 1.45), (0, 0, 9.6)], [1.3, 0.86], tx(kit, "tower stripes", tex_tower), root, sides=10)
    tbox(kit, f"{p} door", (0, -1.27, 2.15), (0.62, 0.14, 1.2), solid(kit, "door", "#2a2f6b", 0.25), root, rot=(4, 0, 0))
    tbox(kit, f"{p} door hood", (0, -1.36, 2.85), (0.8, 0.3, 0.08), solid(kit, "lh red", RED), root)
    dark = solid(kit, "lh dark", INK, 0.2)
    tube(kit, f"{p} gallery", [(0, 0, 9.55), (0, 0, 9.75)], [1.45, 1.45], dark, root, sides=12)
    ring(kit, f"{p} gallery rail", (0, 0, 10.35), 1.4, 0.03, dark, root, n=12, sides=4)
    for i in range(12):
        a = 2 * math.pi * i / 12
        tube(kit, f"{p} rail post {i}", [(math.cos(a) * 1.4, math.sin(a) * 1.4, 9.75), (math.cos(a) * 1.4, math.sin(a) * 1.4, 10.35)],
             0.025, dark, root, sides=3)
    tube(kit, f"{p} lamp room", [(0, 0, 9.75), (0, 0, 10.95)], 0.74, tx(kit, "lamp room", tex_lamp_room, emit=3.5), root, sides=8)
    tube(kit, f"{p} lamp core", [(0, 0, 10.0), (0, 0, 10.7)], 0.3, solid(kit, "lamp core", "#fff7cc", 5.0), root, sides=6)
    tube(kit, f"{p} roof eave", [(0, 0, 10.95), (0, 0, 11.1)], 0.95, solid(kit, "lh red", RED), root, sides=8)
    tube(kit, f"{p} roof", [(0, 0, 11.1), (0, 0, 11.75)], [0.9, 0.08], solid(kit, "lh red", RED), root, sides=8, caps=(False, True))
    lowball(kit, f"{p} roof ball", (0, 0, 11.82), (0.12, 0.12, 0.12), dark, root)
    tube(kit, f"{p} spike", [(0, 0, 11.9), (0, 0, 12.2)], [0.025, 0.005], dark, root, sides=3)
    kit.empty(f"{p} socket lamp", root, (0, 0, 10.35))
    point_light(kit, root, f"{p} lamp light", (0, 0, 10.35), "#ffd36b", 900, 25.0, 0.5)


# ================================================================ scene
def harbor(kit, root):
    """Water, the dock off a quay, the yacht moored at the dock socket, a police car at the shore end, lighthouse far off."""
    build_water(kit, kit.empty("Harbor Water", root, (0, -25, 0)), "Harbor Water")
    quay = tex_mat("quay", tex_asphalt(kit.rand), emit=0.2, ext='REPEAT')
    tbox(kit, "quay", (0, 9.0, 0.0), (60, 18, 2.0), quay, root, uv={'all': (0, 0, 30, 9)})
    tbox(kit, "quay edge", (0, 0.1, 0.95), (60, 0.25, 0.12), solid(kit, "quay edge", YEL, 0.4), root)
    dock = kit.empty("Harbor Dock", root, (0, 0, 1.0))
    build_dock(kit, dock, "Harbor Dock")
    bpy.context.view_layer.update()
    sock = next(o for o in dock.children if o.name.startswith("Harbor Dock socket yacht"))
    m = root.matrix_world.inverted() @ sock.matrix_world
    yacht = kit.empty("Yacht", root, tuple(m.translation), tuple(math.degrees(a) for a in m.to_euler()))
    build_yacht(kit, yacht, "Yacht")
    build_lighthouse(kit, kit.empty("Lighthouse", root, (-22, -58, 0)), "Lighthouse")
    build_police_car(kit, kit.empty("Police Car", root, (-4.2, 2.6, 1.0), (0, 0, 112)), "Police Car")
    for i, (x, y) in enumerate(((7.0, 4.0), (-9.0, 3.0))):
        lamp_post(kit, "quay", root, str(i), (x, y, 1.0))


ASSETS = [
    ("Police Car", prefixed("Police Car", build_police_car)),
    ("Yacht", prefixed("Yacht", build_yacht)),
    ("Harbor Dock", prefixed("Harbor Dock", build_dock)),
    ("Harbor Water", prefixed("Harbor Water", build_water)),
    ("Lighthouse", prefixed("Lighthouse", build_lighthouse)),
]
SCENES = [dict(name="harbor", build=harbor, cam=((0.6, 9.5, 2.75), (-2.0, -16.0, 1.2), 24), res=(1600, 900))]
