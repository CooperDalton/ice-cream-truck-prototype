"""Style D: Vinyl toy. Designer-vinyl / 90s action figure: molded segments, ball joints, cut lines, tampo-printed faces."""
from common import *

KEY = "D"
LABEL = "Vinyl toy"
SHADER = 'vinyl'
WORLD = "#dbe7f2"
FLOOR = "#ffffff"

PAL = {
    'shirt': "#ff6b4a", 'pants': "#3d5afe", 'skin': "#ffd2b0", 'white': "#fbfaf4", 'cooler': "#4dd0e1",
    'boot': "#2d3142", 'hair': "#7a4428", 'ink': "#1c1b26", 'blush': "#ff9a86",
    'zskin': "#9be15d", 'zshirt': "#ffca28", 'zpants': "#7e57c2", 'zhair': "#2e5a1c", 'shoe': "#8d6e63",
    'wear': "#f3f5ea", 'crack': "#1f2a16", 'chip': "#d8f5b8", 'brain': "#f48fb1", 'brain2': "#c2185b",
    'mouth': "#3a0f1e", 'zred': "#ff1744",
    'gun': "#29b6f6", 'gun2': "#0277bd", 'pink': "#ff4081", 'waffle': "#d99a52", 'waffle2': "#f2c98a",
    'choc': "#5e3721", 'goo': "#e3122b", 'straw': "#ff8fb8", 'vanilla': "#fff1cf", 'peg': "#e9edf2",
    'mint': "#8ef0c9", 'yellow': "#ffe14d", 'socket': "#20161c",
}
SPRINKLES = ['pink', 'yellow', 'mint', 'white', 'gun']


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


def M(kit, key, f=1.0):
    return kit.mat(key if f == 1.0 else f"{key} {f}", PAL[key] if f == 1.0 else hex_scale(PAL[key], f))


def deg_euler(rot):
    return Euler([math.radians(a) for a in rot])


# ------------------------------------------------------------------ modeling helpers

def loft(kit, name, rings, mats, parent, n=12, sub=1, caps=(True, True), loc=(0, 0, 0), rot=(0, 0, 0), grot=None,
         gloc=None, smooth=True):
    """Molded segment: a cage lofted through elliptical/superelliptical rings along local Z.
    Ring keys: z, rx, ry, cx, cy, p (superellipse), front/back (bulge toward -Y/+Y), fold/foldn/ph (molded ripples),
    rad (per-vertex radius factors), zig/rag (torn edges), fn(a, x, y)->(dx, dy, dz), m (material index)."""
    mats = list(mats) if isinstance(mats, (list, tuple)) else [mats]
    bm = bmesh.new()
    rows = []
    for r in rings:
        rx = r['rx']
        ry = r.get('ry', rx)
        p = r.get('p', 2.0)
        row = []
        for k in range(n):
            a = 2 * math.pi * k / n
            c, s = math.cos(a), math.sin(a)
            x = rx * math.copysign(abs(c) ** (2 / p), c)
            y = ry * math.copysign(abs(s) ** (2 / p), s)
            y += -r.get('front', 0) * s * s if s < 0 else r.get('back', 0) * s * s
            f = 1 + r.get('fold', 0) * math.sin(r.get('foldn', 5) * a + r.get('ph', 0))
            if 'rad' in r:
                f *= r['rad'][k]
            z = r['z'] + r.get('zig', 0) * (1 if k % 2 else -1)
            if r.get('rag'):
                z += r['rag'] * (kit.rand.random() * 2 - 1)
            x, y = x * f, y * f
            if 'fn' in r:
                dx, dy, dz = r['fn'](a, x, y)
                x, y, z = x + dx, y + dy, z + dz
            row.append(bm.verts.new((r.get('cx', 0) + x, r.get('cy', 0) + y, z)))
        rows.append(row)
    for i in range(len(rows) - 1):
        for k in range(n):
            f = bm.faces.new((rows[i][k], rows[i][(k + 1) % n], rows[i + 1][(k + 1) % n], rows[i + 1][k]))
            f.material_index = rings[i].get('m', 0)
    if caps[0]:
        bm.faces.new(rows[0]).material_index = rings[0].get('m', 0)
    if caps[1]:
        bm.faces.new(list(reversed(rows[-1]))).material_index = rings[-1].get('m', 0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if grot:
        bmesh.ops.rotate(bm, matrix=deg_euler(grot).to_matrix(), verts=bm.verts)
    if gloc:
        bmesh.ops.translate(bm, vec=Vector(gloc), verts=bm.verts)
    ob = kit.mesh_from_bmesh(name, bm, mats, parent, loc, rot, smooth=smooth)
    if sub:
        mod = ob.modifiers.new("Subdivision", 'SUBSURF')
        mod.levels = mod.render_levels = sub
    return ob


def ball(kit, name, parent, r, mat, loc=(0, 0, 0), seg=12):
    return kit.prim(name, 'sphere', (r, r, r), mat, parent, offset=loc, segments=seg, rings=seg // 2 + 2)


def torus(kit, name, R, r, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), N=20, Mn=8, sq=1.0):
    bm = bmesh.new()
    grid = []
    for i in range(N):
        a = 2 * math.pi * i / N
        row = []
        for j in range(Mn):
            b = 2 * math.pi * j / Mn
            rr = R + r * math.cos(b)
            row.append(bm.verts.new((rr * math.cos(a), rr * math.sin(a), r * sq * math.sin(b))))
        grid.append(row)
    for i in range(N):
        for j in range(Mn):
            bm.faces.new((grid[i][j], grid[(i + 1) % N][j], grid[(i + 1) % N][(j + 1) % Mn], grid[i][(j + 1) % Mn]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot)


def c_hand(kit, name, parent, mat, s, W=0.066, hole=0.022, th=0.019, gz=-0.07, sub=1):
    """Action-figure C-grip hand: back of hand + curled finger bar swept around a hole whose axis is local Y.
    s = +1 for a hand on the +X side, -1 for -X. The palm faces -s."""
    R = hole + th / 2
    path = [(0.0, -0.002, 0.036, 0.78), (s * 0.014, -0.028, 0.026, 0.9), (s * R, gz + 0.016, th, 1.0)]
    for deg in (0, 30, 60, 90, 120, 150, 180, 202):
        ph = math.radians(deg)
        path.append((s * R * math.cos(ph), gz - R * math.sin(ph), th * (0.92 if deg >= 180 else 1.0), 1.0))
    bm = bmesh.new()
    secs = []
    for i, (cx, cz, t, w) in enumerate(path):
        a = path[max(i - 1, 0)]
        b = path[min(i + 1, len(path) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, tz)
        nx, nz = tz / ln, -tx / ln
        sec = []
        for sn, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
            sec.append(bm.verts.new((cx + nx * sn * t / 2, sy * W * w / 2, cz + nz * sn * t / 2)))
        secs.append(sec)
    for i in range(len(secs) - 1):
        for j in range(4):
            bm.faces.new((secs[i][j], secs[i][(j + 1) % 4], secs[i + 1][(j + 1) % 4], secs[i + 1][j]))
    bm.faces.new(secs[0])
    bm.faces.new(list(reversed(secs[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    mod = ob.modifiers.new("Subdivision", 'SUBSURF')
    mod.levels = mod.render_levels = sub
    # thumb pressed along the palm side of the C opening
    kit.skin(name + " thumb", [(-s * 0.016, -W * 0.28, -0.026), (-s * (R + 0.006), -W * 0.36, -0.05),
                               (-s * (R + 0.004), -W * 0.34, -0.075)], [(0, 1), (1, 2)],
             [0.012, 0.0105, 0.009], mat, parent, subsurf=1)
    return ob


# ------------------------------------------------------------------ tampo-print decals (shrinkwrapped paint apps)

def bm_ellipse(rx, rz, cx=0.0, cz=0.0, seg=16, rings=2, rad=None, ang=0.0):
    bm = bmesh.new()
    c = bm.verts.new((cx, 0, cz))
    rows = []
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    for j in range(1, rings + 1):
        f = j / rings
        row = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            rr = f * (rad[k] if rad else 1.0)
            x, z = rx * rr * math.cos(a), rz * rr * math.sin(a)
            row.append(bm.verts.new((cx + x * ca - z * sa, 0, cz + x * sa + z * ca)))
        rows.append(row)
    for k in range(seg):
        bm.faces.new((c, rows[0][k], rows[0][(k + 1) % seg]))
    for j in range(rings - 1):
        for k in range(seg):
            bm.faces.new((rows[j][k], rows[j + 1][k], rows[j + 1][(k + 1) % seg], rows[j][(k + 1) % seg]))
    return bm


def bm_band(pts, width, bm=None):
    """Painted stroke along 2D points (x, z). width: float or per-point list."""
    bm = bm or bmesh.new()
    L, R = [], []
    for i, (x, z) in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, tz)
        nx, nz = -tz / ln, tx / ln
        w = (width[i] if isinstance(width, (list, tuple)) else width) / 2
        L.append(bm.verts.new((x + nx * w, 0, z + nz * w)))
        R.append(bm.verts.new((x - nx * w, 0, z - nz * w)))
    for i in range(len(pts) - 1):
        bm.faces.new((L[i], R[i], R[i + 1], L[i + 1]))
    return bm


def decal(kit, name, bm, mat, parent, target, loc=(0, 0, 0), rot=(0, 0, 0), off=0.0012, thick=0.0, sub=0):
    """Flat shape in local XZ projected along local Y onto target's evaluated surface (paint app / molded patch)."""
    for f in bm.faces:
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    ob = kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot)
    sw = ob.modifiers.new("Wrap", 'SHRINKWRAP')
    sw.target = target
    sw.wrap_method = 'PROJECT'
    sw.use_project_y = True
    sw.use_negative_direction = True
    sw.use_positive_direction = True
    sw.wrap_mode = 'ABOVE_SURFACE'
    sw.offset = off
    if thick:
        so = ob.modifiers.new("Solidify", 'SOLIDIFY')
        so.thickness = thick
        so.offset = 1
    if sub:
        mod = ob.modifiers.new("Subdivision", 'SUBSURF')
        mod.levels = mod.render_levels = sub
    return ob


def zigzag(x0, z0, x1, z1, n, amp, rnd):
    pts = []
    for i in range(n + 1):
        t = i / n
        j = 0 if i in (0, n) else amp * (1 if i % 2 else -1) * (0.6 + 0.8 * rnd.random())
        dx, dz = x1 - x0, z1 - z0
        ln = math.hypot(dx, dz)
        pts.append((x0 + dx * t - dz / ln * j, z0 + dz * t + dx / ln * j))
    return pts


def jag(kit, n, lo=0.7, hi=1.25):
    return [lo + (hi - lo) * kit.rand.random() for _ in range(n)]


# ------------------------------------------------------------------ figure (shared toy body, different paint/sculpt)

L_THIGH, L_SHIN, FOOT_H = 0.33, 0.335, 0.08


def leg_drop(hip_rot, knee):
    R = deg_euler(hip_rot).to_matrix()
    p = R @ (Vector((0, 0, -L_THIGH)) + Euler((math.radians(knee), 0, 0)).to_matrix() @ Vector((0, 0, -L_SHIN)))
    return -p.z + FOOT_H


def solve_knee(hip_rot, drop):
    lo, hi = 0.0, 150.0
    for _ in range(50):
        mid = (lo + hi) / 2
        if leg_drop(hip_rot, mid) > drop:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def torso_rings(z, back=0.0):
    rings = [
        dict(z=0.004, rx=.125, ry=.085, p=2.5),
        dict(z=0.016, rx=.126, ry=.086, p=2.5),
        dict(z=0.08, rx=.136, ry=.09, p=2.5),
        dict(z=0.17, rx=.165, ry=.1, p=2.6, front=.012, back=back * 0.6),
        dict(z=0.25, rx=.19, ry=.105, p=2.6, front=.024, back=back),
        dict(z=0.31, rx=.2, ry=.1, p=2.6, front=.012, back=back * 0.8),
        dict(z=0.35, rx=.16, ry=.085, p=2.4),
        dict(z=0.373, rx=.075, ry=.062),
        dict(z=0.38, rx=.05, ry=.045),
    ]
    return rings


def head_rings(zombie):
    def nose(a, x, y):
        return (0, -0.026 if abs(a - 1.5 * math.pi) < 1e-6 else 0, 0)
    if not zombie:
        return [
            dict(z=0.0, rx=.045, ry=.045),
            dict(z=0.005, rx=.06, ry=.06),
            dict(z=0.022, rx=.078, ry=.08, front=.014, cy=-.004, p=2.4),
            dict(z=0.05, rx=.09, ry=.09, front=.012, cy=-.004, p=2.3),
            dict(z=0.09, rx=.098, ry=.097, front=.006, fn=nose),
            dict(z=0.13, rx=.1, ry=.1),
            dict(z=0.165, rx=.097, ry=.1, front=.004),
            dict(z=0.2, rx=.08, ry=.088),
            dict(z=0.222, rx=.045, ry=.05),
            dict(z=0.228, rx=.01, ry=.01),
        ]
    return [
        dict(z=0.0, rx=.04, ry=.04),
        dict(z=0.005, rx=.055, ry=.058),
        dict(z=0.02, rx=.074, ry=.08, front=.024, cy=-.008, p=2.5),
        dict(z=0.05, rx=.08, ry=.085, front=.008, cy=-.004),
        dict(z=0.09, rx=.088, ry=.09, front=.004, fn=nose),
        dict(z=0.125, rx=.094, ry=.096),
        dict(z=0.15, rx=.094, ry=.098, front=.014),
        dict(z=0.168, rx=.09, ry=.094, zig=.014),
        dict(z=0.172, rx=.062, ry=.066, zig=.012),
    ]


def build_arm(kit, parent, s, S, loc, rot, sleeve, skin, ballmat, torn=False, pop=False):
    side = "L" if s > 0 else "R"
    pre = S['name']
    sh = kit.empty(f"{pre} shoulder {side}", parent, loc, rot)
    ball(kit, f"{pre} shoulder ball {side}", sh, 0.06, ballmat)
    if pop:  # popped: peg sticking out of the ball where it sat in the torso socket
        kit.prim(f"{pre} shoulder peg {side}", 'cyl', (0.02, 0.02, 0.06), M(kit, 'peg'), sh, offset=(0, 0, 0.075),
                 segments=12)
        ball(kit, f"{pre} shoulder peg knob {side}", sh, 0.027, M(kit, 'peg'), loc=(0, 0, 0.105), seg=12)
    hem = dict(z=-0.136, rx=.062, ry=.059, m=0, rag=0.012 if torn else 0, zig=0.008 if torn else 0)
    kit_rings = [
        dict(z=-0.02, rx=.05, m=0),
        dict(z=-0.05, rx=.058, ry=.056, m=0, fold=.04, foldn=3),
        dict(z=-0.095, rx=.06, ry=.057, m=0, fold=.05, foldn=4, ph=1),
        dict(z=-0.128, rx=.062, ry=.059, m=0),
        hem,
        dict(z=-0.142, rx=.047, m=1),
        dict(z=-0.175, rx=.05, ry=.046, m=1),
        dict(z=-0.21, rx=.043, ry=.041, m=1),
        dict(z=-0.226, rx=.04, m=1),
        dict(z=-0.232, rx=.035, m=1),
    ]
    ua = loft(kit, f"{pre} upper arm {side}", kit_rings, [sleeve, skin], sh, n=10, sub=1)
    el = kit.empty(f"{pre} elbow {side}", sh, (0, 0, -0.265), S['elbow'][side])
    ball(kit, f"{pre} elbow ball {side}", el, 0.041, M(kit, S['skin'], 0.93))
    loft(kit, f"{pre} forearm {side}", [
        dict(z=-0.026, rx=.036), dict(z=-0.034, rx=.038), dict(z=-0.075, rx=.046, ry=.042),
        dict(z=-0.15, rx=.037, ry=.034), dict(z=-0.19, rx=.031, ry=.029), dict(z=-0.198, rx=.031, ry=.029),
        dict(z=-0.2, rx=.026)], skin, el, n=10, sub=1)
    wr = kit.empty(f"{pre} wrist {side}", el, (0, 0, -0.212), S['wrist'][side])
    kit.prim(f"{pre} wrist peg {side}", 'cyl', (0.02, 0.02, 0.022), M(kit, S['skin'], 0.82), wr, offset=(0, 0, 0.006),
             segments=12)
    hand = c_hand(kit, f"{pre} hand {side}", wr, skin, s)
    return dict(sh=sh, el=el, wr=wr, hand=hand, ua=ua)


def build_leg(kit, hips, s, S, pants, skin, foot_kind):
    side = "L" if s > 0 else "R"
    pre = S['name']
    hp = kit.empty(f"{pre} hip {side}", hips, (s * 0.085, 0, -0.05), S['hip'][side])
    ball(kit, f"{pre} hip ball {side}", hp, 0.066, M(kit, S['pants'], 0.9))
    th = loft(kit, f"{pre} thigh {side}", [
        dict(z=-0.035, rx=.068, ry=.07), dict(z=-0.045, rx=.072, ry=.074),
        dict(z=-0.11, rx=.076, ry=.074, fold=.035, foldn=3, ph=0.5),
        dict(z=-0.2, rx=.066, ry=.064, fold=.05, foldn=5, ph=1.2),
        dict(z=-0.28, rx=.056, ry=.055), dict(z=-0.288, rx=.054), dict(z=-0.29, rx=.048)], pants, hp, n=10, sub=1)
    kn = kit.empty(f"{pre} knee {side}", hp, (0, 0, -L_THIGH), S['knee'][side])
    ball(kit, f"{pre} knee ball {side}", kn, 0.052, M(kit, S['pants'], 0.9))
    torn = S.get('torn_shin') == side
    rings = [dict(z=-0.035, rx=.05, m=0), dict(z=-0.043, rx=.053, m=0),
             dict(z=-0.11, rx=.056, ry=.06, back=.008, m=0, fold=.04, foldn=4),
             dict(z=-0.2, rx=.05, ry=.05, m=0, fold=.05, foldn=5, ph=2)]
    if torn:  # torn pant leg: ragged cuff, lime shin below
        rings += [dict(z=-0.215, rx=.054, m=0, rag=0.016, zig=0.012), dict(z=-0.222, rx=.04, m=1),
                  dict(z=-0.29, rx=.034, m=1), dict(z=-0.315, rx=.033, m=1), dict(z=-0.32, rx=.028, m=1)]
    else:
        rings += [dict(z=-0.27, rx=.05, ry=.05, m=0), dict(z=-0.29, rx=.056, m=0), dict(z=-0.305, rx=.056, m=0),
                  dict(z=-0.31, rx=.045, m=0), dict(z=-0.32, rx=.04, m=0)]
    sh = loft(kit, f"{pre} shin {side}", rings, [pants, skin], kn, n=10, sub=1)
    an = kit.empty(f"{pre} ankle {side}", kn, (0, 0, -L_SHIN), S['ankle'][side])
    if foot_kind == 'boot':
        loft(kit, f"{pre} boot {side}", [
            dict(z=0.012, rx=.05, ry=.05, m=0), dict(z=0.0, rx=.054, ry=.054, m=0),
            dict(z=-0.03, rx=.052, ry=.062, cy=-.012, m=0),
            dict(z=-0.055, rx=.057, ry=.098, cy=-.036, p=2.6, m=0),
            dict(z=-0.064, rx=.06, ry=.106, cy=-.04, p=2.8, m=1), dict(z=-0.08, rx=.06, ry=.106, cy=-.04, p=2.8, m=1)],
             [M(kit, S['boot']), M(kit, S['sole'])], an, n=12, sub=1)
    else:  # bare sculpted foot with toe nubs
        loft(kit, f"{pre} foot {side}", [
            dict(z=0.01, rx=.034), dict(z=-0.03, rx=.042, ry=.05, cy=-.01),
            dict(z=-0.06, rx=.05, ry=.092, cy=-.034, p=2.4), dict(z=-0.08, rx=.05, ry=.092, cy=-.034, p=2.4)],
             skin, an, n=12, sub=1)
        for i, tx in enumerate((-0.03, -0.01, 0.01, 0.028)):
            ball(kit, f"{pre} toe {side}{i}", an, 0.014 - 0.0015 * abs(i - 1.5), skin,
                 loc=(tx * -s, -0.118 + 0.006 * abs(i - 1.2), -0.066), seg=10)
    return dict(hp=hp, kn=kn, an=an, thigh=th, shin=sh)


def build_body(kit, root, S):
    z = S['zombie']
    pre = S['name']
    shirt, pants, skin = M(kit, S['shirt']), M(kit, S['pants']), M(kit, S['skin'])
    hips = kit.empty(f"{pre} hips", root, (0, 0, S['hip_z']), S.get('hips_rot', (0, 0, 0)))
    # pelvis: molded briefs block with the belt / apron string sculpted in
    pelvis = loft(kit, f"{pre} pelvis", [
        dict(z=-0.105, rx=.06, ry=.06, m=0), dict(z=-0.08, rx=.12, ry=.085, p=2.4, m=0),
        dict(z=0.0, rx=.142, ry=.098, p=2.7, m=0), dict(z=0.06, rx=.136, ry=.092, p=2.7, m=0),
        dict(z=0.068, rx=.142, ry=.098, p=2.7, m=1), dict(z=0.094, rx=.142, ry=.098, p=2.7, m=1),
        dict(z=0.1, rx=.125, ry=.085, p=2.6, m=1)], [pants, M(kit, S['belt'])], hips, n=16, sub=1)
    waist = kit.empty(f"{pre} waist", hips, (0, 0, 0.102), S['waist'])
    kit.prim(f"{pre} waist peg", 'cyl', (0.095, 0.07, 0.05), M(kit, S['pants'], 0.7), hips, offset=(0, 0, 0.1),
             segments=16)
    # torso: shirt sculpt; zombie gets a lime belly under a ragged shirt hem and a hunched back
    trings = torso_rings(z, back=0.03 if z else 0.0)
    if z:
        for r in trings[:2]:
            r['m'] = 1
        trings.insert(2, dict(z=0.05, rx=.13, ry=.088, p=2.5, m=1))
        trings.insert(3, dict(z=0.085, rx=.137, ry=.091, p=2.5, m=0, zig=0.016, rag=0.01))
    torso = loft(kit, f"{pre} torso", trings, [shirt, skin], waist, n=16, sub=1)
    neck = kit.empty(f"{pre} neck", waist, (0, 0, 0.38), S['neck'])
    kit.prim(f"{pre} neck peg", 'cyl', (0.036, 0.034, S['neck_len'] + 0.02), M(kit, S['skin'], 0.88), neck,
             offset=(0, 0, S['neck_len'] / 2), segments=14)
    head_p = kit.empty(f"{pre} head", neck, (0, 0, S['neck_len']), S['head'])
    head = loft(kit, f"{pre} head mold", head_rings(z), skin, head_p, n=16, sub=1)
    out = dict(hips=hips, pelvis=pelvis, waist=waist, torso=torso, neck=neck, head_p=head_p, head=head)
    # arms
    out['arms'] = {}
    for s in (-1, 1):
        side = "L" if s > 0 else "R"
        pop = z and S.get('pop') and s > 0
        parent, loc, rot = (root, S['pop_loc'], S['pop_rot']) if pop else (waist, (s * 0.205, 0, 0.3), S['shoulder'][side])
        out['arms'][side] = build_arm(kit, parent, s, S, loc, rot, shirt, skin, M(kit, S['shirt'], 0.92),
                                      torn=z, pop=pop)
    out['legs'] = {}
    for s in (-1, 1):
        side = "L" if s > 0 else "R"
        out['legs'][side] = build_leg(kit, hips, s, S, pants, skin, S['feet'][side])
    return out


# ------------------------------------------------------------------ player

def player_head(kit, b):
    hp, head = b['head_p'], b['head']
    ink, skin = M(kit, 'ink'), M(kit, 'skin')
    # molded hair: shell around the head that dips to the nape and stops at the brow, sculpted clumps
    def hairline(lift):
        return lambda a, x, y: (0, 0, lift * max(0.0, -math.sin(a)) ** 1.3 - 0.045 * max(0.0, math.sin(a)))
    loft(kit, "P hair", [
        dict(z=0.118, rx=.104, ry=.104, fn=hairline(0.052), fold=.035, foldn=9),
        dict(z=0.16, rx=.106, ry=.107, fn=hairline(0.02), fold=.03, foldn=9, ph=0.4),
        dict(z=0.2, rx=.088, ry=.096, fold=.02, foldn=7),
        dict(z=0.229, rx=.05, ry=.055), dict(z=0.24, rx=.012)], M(kit, 'hair'), hp, n=18, sub=1)
    for s in (-1, 1):  # ears
        kit.prim(f"P ear {s}", 'sphere', (0.014, 0.024, 0.03), skin, hp, offset=(s * 0.097, 0.008, 0.11), segments=12,
                 rings=8)
    # paper soda-jerk hat (garrison cap) molded as one piece, pink stripe band
    hat = kit.empty("P hat", hp, (0.004, 0.0, 0.168), (-6, 7, 0))
    bm = bmesh.new()
    secs = []
    ys = [-0.135, -0.115, -0.065, 0.0, 0.065, 0.115, 0.135]
    for y in ys:
        t = y / 0.13
        w = 0.106 * (1 - 0.72 * t ** 6) + 0.004
        h = 0.098 * (1 - 0.6 * t ** 4)
        prof = [(-w, -0.002), (-w * 1.01, 0.028), (-w * 0.8, 0.034), (-w * 0.42, h * 0.78), (-w * 0.1, h),
                (0, h * 0.86), (w * 0.1, h), (w * 0.42, h * 0.78), (w * 0.8, 0.034), (w * 1.01, 0.028), (w, -0.002)]
        secs.append([bm.verts.new((px, y, pz)) for px, pz in prof])
    for i in range(len(secs) - 1):
        for j in range(len(secs[0]) - 1):
            f = bm.faces.new((secs[i][j], secs[i][j + 1], secs[i + 1][j + 1], secs[i + 1][j]))
            f.material_index = 1 if j in (0, 9) else 0
    for sec in (secs[0], secs[-1]):
        bm.faces.new(sec)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    hob = kit.mesh_from_bmesh("P hat mold", bm, [M(kit, 'white'), M(kit, 'pink')], hat)
    so = hob.modifiers.new("Solidify", 'SOLIDIFY')
    so.thickness = 0.006
    sub = hob.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = sub.render_levels = 1
    ball(kit, "P hat button", hat, 0.012, M(kit, 'pink'), loc=(0.098, 0.0, 0.03), seg=12)
    # tampo-printed face
    for s in (-1, 1):
        decal(kit, f"P eye {s}", bm_ellipse(0.012, 0.018), ink, hp, head, loc=(s * 0.037, -0.2, 0.118))
        decal(kit, f"P eye shine {s}", bm_ellipse(0.0042, 0.0052), M(kit, 'white'), hp, head,
              loc=(s * 0.037 + 0.004, -0.2, 0.125), off=0.0024)
        decal(kit, f"P brow {s}", bm_band([(s * 0.02, 0.146), (s * 0.038, 0.153), (s * 0.058, 0.149)], 0.0075),
              M(kit, 'hair', 0.7), hp, head, loc=(0, -0.2, 0))
        decal(kit, f"P blush {s}", bm_ellipse(0.014, 0.008), M(kit, 'blush'), hp, head, loc=(s * 0.058, -0.2, 0.078))
    smile = [(x, 0.057 - 0.014 * (1 - (x / 0.032) ** 2)) for x in [i * 0.032 / 6 for i in range(-6, 7)]]
    decal(kit, "P smile", bm_band(smile, [0.004 + 0.002 * (1 - abs(i - 6) / 6) for i in range(13)]), M(kit, 'mouth'),
          hp, head, loc=(0, -0.2, 0))


def player_gear(kit, b):
    waist, torso, hips = b['waist'], b['torso'], b['hips']
    white, cyan = M(kit, 'white'), M(kit, 'cooler')
    # collar
    torus(kit, "P collar", 0.06, 0.013, white, waist, loc=(0, -0.004, 0.37), rot=(-8, 0, 0), sq=0.8)
    # apron bib: grid shrinkwrapped onto the chest, then thickened and smoothed (molded-on apron)
    bm = bmesh.new()
    grid = []
    for j in range(6):
        v = j / 5
        zz = 0.06 + 0.24 * v
        w = 0.09 - 0.02 * v
        grid.append([bm.verts.new((w * (i / 3 - 1), 0, zz)) for i in range(7)])
    for j in range(5):
        for i in range(6):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    bib = decal(kit, "P apron bib", bm, white, waist, torso, loc=(0, -0.3, 0), off=0.003, thick=0.008, sub=1)
    # little ice cream cone logo on the bib
    cone = bmesh.new()
    a, bb, c = cone.verts.new((-0.016, 0, 0.21)), cone.verts.new((0.016, 0, 0.21)), cone.verts.new((0, 0, 0.165))
    cone.faces.new((a, c, bb))
    decal(kit, "P logo cone", cone, M(kit, 'waffle'), waist, bib, loc=(0, -0.3, 0), off=0.001)
    decal(kit, "P logo scoop", bm_ellipse(0.019, 0.016, 0, 0.222), M(kit, 'pink'), waist, bib, loc=(0, -0.3, 0),
          off=0.0012)
    # neck strap of the apron
    for s in (-1, 1):
        kit.skin(f"P bib strap {s}", [(s * 0.062, -0.122, 0.29), (s * 0.07, -0.085, 0.355), (s * 0.06, -0.01, 0.39),
                                      (0, 0.05, 0.392)], [(0, 1), (1, 2), (2, 3)], [0.009] * 4, white, waist, subsurf=0)
    # apron skirt: rigid molded skirt with sculpted folds, hangs in front of the legs
    bm = bmesh.new()
    rows = []
    for j in range(6):
        v = j / 5
        zz = 0.085 - 0.42 * v
        rx, ry = 0.15 + 0.045 * v, 0.106 + 0.04 * v
        row = []
        for i in range(13):
            th = math.radians(-160 + 140 * i / 12)
            fold = 1 + 0.07 * v * math.sin(i * math.pi / 2 + 0.6)
            row.append(bm.verts.new((rx * fold * math.cos(th), ry * fold * math.sin(th), zz)))
        rows.append(row)
    for j in range(5):
        for i in range(12):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    sk = kit.mesh_from_bmesh("P apron skirt", bm, white, hips)
    so = sk.modifiers.new("Solidify", 'SOLIDIFY')
    so.thickness = 0.01
    so.offset = 1
    sub = sk.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = sub.render_levels = 1
    # pocket on the skirt
    decal(kit, "P apron pocket", bm_ellipse(0.05, 0.03, 0.04, -0.14, rad=[1.0] * 16), M(kit, 'white', 0.9), hips, sk,
          loc=(0, -0.4, 0), off=0.002)
    # cooler backpack
    pack = kit.empty("P cooler", waist, (0, 0.215, 0.205))
    kit.prim("P cooler body", 'box', (0.27, 0.17, 0.27), cyan, pack, bevel=0.034, bevel_segments=4)
    kit.prim("P cooler lid", 'box', (0.29, 0.19, 0.05), white, pack, offset=(0, 0, 0.155), bevel=0.02,
             bevel_segments=3)
    kit.prim("P cooler stripe", 'box', (0.275, 0.175, 0.03), M(kit, 'pink'), pack, offset=(0, 0, -0.06), bevel=0.012,
             bevel_segments=2)
    kit.skin("P cooler handle", [(-0.075, 0, 0.175), (-0.06, 0, 0.215), (0.06, 0, 0.215), (0.075, 0, 0.175)],
             [(0, 1), (1, 2), (2, 3)], [0.012] * 4, white, pack, subsurf=1)
    kit.prim("P pint shelf", 'box', (0.07, 0.17, 0.02), white, pack, offset=(0.168, 0, -0.1), bevel=0.008)
    for i, (lid, y) in enumerate((('pink', -0.045), ('choc', 0.045))):
        pt = kit.empty(f"P pint {i}", pack, (0.172, y, -0.09))
        loft(kit, f"P pint tub {i}", [dict(z=0.0, rx=.029, m=0), dict(z=0.02, rx=.03, m=1), dict(z=0.05, rx=.033, m=1),
                                       dict(z=0.068, rx=.034, m=0)], [white, M(kit, lid)], pt, n=12, sub=0)
        kit.prim(f"P pint lid {i}", 'cyl', (0.037, 0.037, 0.014), M(kit, lid), pt, offset=(0, 0, 0.074), segments=16,
                 bevel=0.004)
    kit.prim("P pint band", 'box', (0.075, 0.18, 0.016), cyan, pack, offset=(0.172, 0, -0.045), bevel=0.006)
    for s in (-1, 1):  # shoulder straps
        kit.skin(f"P strap {s}", [(s * 0.12, 0.12, 0.28), (s * 0.122, 0.04, 0.378), (s * 0.124, -0.106, 0.3),
                                  (s * 0.13, -0.122, 0.19), (s * 0.13, -0.11, 0.1)],
                 [(i, i + 1) for i in range(4)], [0.011] * 5, cyan, waist, subsurf=0)


def build_player(kit, root):
    S = dict(name="P", zombie=False, shirt='shirt', pants='pants', skin='skin', belt='white', boot='boot',
             sole='white', neck_len=0.032, feet={'L': 'boot', 'R': 'boot'})
    S['waist'] = (0, 0, -6)
    S['neck'] = (0, 0, 4)
    S['head'] = (-3, 0, 4)
    S['shoulder'] = {'R': (-86, 0, 10), 'L': (-28, -14, 0)}
    S['elbow'] = {'R': (-4, 0, 0), 'L': (-78, 0, 0)}
    S['wrist'] = {'R': (14, 0, 0), 'L': (0, 0, 0)}
    S['hip'] = {'R': (-10, 6, 0), 'L': (8, -6, 0)}
    S['knee'] = {'R': 12, 'L': 4}
    drops = [leg_drop(S['hip'][sd], S['knee'][sd]) for sd in "RL"]
    S['hip_z'] = min(drops) + 0.05
    S['knee'] = {sd: (S['knee'][sd], 0, 0) for sd in "RL"}
    S['ankle'] = {'R': (-2, -6, 0), 'L': (-12, 6, 0)}
    b = build_body(kit, root, S)
    player_head(kit, b)
    player_gear(kit, b)
    # Scoop Pistol in the right C-grip hand: grip axis aligned with the hand's hole axis (local Y)
    R = deg_euler((76, 0, 0)).to_matrix()
    grip = Vector((0, 0.0825, -0.07))
    loc = Vector((0, 0, -0.07)) - R @ grip
    gun = kit.empty("P held gun", b['arms']['R']['wr'], tuple(loc), (76, 0, 0))
    build_gun(kit, gun)


# ------------------------------------------------------------------ zombie

def zombie_head(kit, b, hit):
    hp, head = b['head_p'], b['head']
    ink, skin = M(kit, 'ink'), M(kit, 'zskin')
    # exposed brain popping out of the broken cranium cap
    brain_rings = [dict(z=0.135, rx=.064, ry=.07)]
    for i, (zz, rx, ry) in enumerate(((0.16, .074, .08), (0.18, .088, .096), (0.2, .092, .1), (0.22, .086, .094),
                                      (0.238, .07, .078))):
        brain_rings.append(dict(z=zz, rx=rx, ry=ry, fold=.09, foldn=7 + i % 3, ph=i * 1.3, rad=jag(kit, 20, 0.93, 1.07)))
    brain_rings += [dict(z=0.252, rx=.04, ry=.046), dict(z=0.258, rx=.01)]
    brain = loft(kit, "Z brain", brain_rings, M(kit, 'brain'), hp, n=20, sub=1, loc=(0.004, 0.006, 0))
    rnd = kit.rand
    for i, x0 in enumerate((-0.045, -0.015, 0.0, 0.03, 0.055)):  # squiggly gyri grooves seen from above
        if i == 2:
            pts = [(0.0, -0.06 + 0.12 * j / 10) for j in range(11)]
        else:
            pts = [(x0 * 0.8 + 0.007 * math.sin(j * 1.7 + i), -0.045 + 0.09 * j / 10) for j in range(11)]
        decal(kit, f"Z brain groove {i}", bm_band(pts, 0.005 if i == 2 else 0.0035), M(kit, 'brain2'), hp, brain,
              loc=(0.004, 0.006, 0.4), rot=(-90, 0, 0), off=0.0008)
    for i, (zz, w) in enumerate(((0.188, 0.07), (0.21, 0.065), (0.232, 0.045))):
        pts = [(-w + 2 * w * j / 12, zz + 0.006 * math.sin(j * 1.9 + i * 2)) for j in range(13)]
        decal(kit, f"Z brain front groove {i}", bm_band(pts, 0.004), M(kit, 'brain2'), hp, brain,
              loc=(0.004, -0.3, 0), off=0.0008)
    # molded hair clumps on the sides/back of the cracked cranium
    for i, (ang, zz) in enumerate(((155, 0.13), (125, 0.145), (55, 0.145), (25, 0.13), (90, 0.125), (195, 0.115),
                                   (-15, 0.115))):
        a = math.radians(ang)
        d = Vector((math.cos(a) * 0.7, math.sin(a) * 0.7, 0.7)).normalized()
        t = kit.prim(f"Z hair clump {i}", 'cone', (0.026, 0.02, 0.034), M(kit, 'zhair'), hp, offset=(0, 0, 0.012),
                     segments=8, taper=0.35)
        t.location = (0.08 * math.cos(a), 0.086 * math.sin(a), zz)
        t.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    kit.prim("Z ear", 'sphere', (0.014, 0.026, 0.032), skin, hp, offset=(-0.092, 0.01, 0.1), segments=12, rings=8)
    kit.prim("Z ear stub", 'cyl', (0.012, 0.012, 0.012), M(kit, 'zskin', 0.8), hp, offset=(0.093, 0.01, 0.1),
             rot=(0, 90, 0), segments=10)
    # mismatched eyes: big bulging white one, small red misprint
    decal(kit, "Z eye big", bm_ellipse(0.026, 0.026, seg=20), M(kit, 'white'), hp, head, loc=(-0.04, -0.3, 0.112),
          off=0.0015, thick=0.006, sub=1)
    decal(kit, "Z pupil", bm_ellipse(0.0075, 0.0075), ink, hp, head, loc=(-0.033, -0.3, 0.104), off=0.0085)
    decal(kit, "Z eye small ring", bm_ellipse(0.015, 0.013), M(kit, 'zred'), hp, head, loc=(0.043, -0.3, 0.1))
    decal(kit, "Z eye small dot", bm_ellipse(0.005, 0.005), ink, hp, head, loc=(0.046, -0.3, 0.101), off=0.0024)
    decal(kit, "Z brow", bm_band([(0.02, 0.128), (0.04, 0.124), (0.066, 0.13)], 0.008), M(kit, 'zhair'), hp, head,
          loc=(0, -0.3, 0))
    # jagged open grimace with teeth
    mouth_rad = [1.0, 1.1, 0.9, 1.15, 0.95, 1.1, 0.85, 1.0, 1.05, 0.9, 1.1, 0.95, 1.0, 1.05, 0.9, 1.0]
    oh = 0.016 if hit else 0.011
    decal(kit, "Z mouth", bm_ellipse(0.036, oh, rad=mouth_rad, ang=-7), M(kit, 'mouth'), hp, head,
          loc=(0.002, -0.3, 0.046))
    for i, tx in enumerate((-0.02, -0.004, 0.014)):
        sq = bmesh.new()
        v = [sq.verts.new(p) for p in ((tx - 0.006, 0, 0.0), (tx + 0.006, 0, 0.0), (tx + 0.005, 0, -0.012),
                                       (tx - 0.005, 0, -0.012))]
        sq.faces.new(v)
        decal(kit, f"Z tooth {i}", sq, M(kit, 'white'), hp, head, loc=(0, -0.3, 0.058 + 0.0015 * tx / 0.02),
              off=0.0024)
    # cracked plastic: dark crack lines with lighter stress-whitening halos, a chipped spot
    rnd = kit.rand
    cracks = [zigzag(0.026, 0.16, 0.05, 0.118, 6, 0.006, rnd), zigzag(-0.07, 0.09, -0.035, 0.052, 5, 0.005, rnd),
              zigzag(0.04, 0.148, 0.062, 0.136, 3, 0.004, rnd)]
    for i, pts in enumerate(cracks):
        decal(kit, f"Z crack halo {i}", bm_band(pts, 0.007), M(kit, 'chip'), hp, head, loc=(0, -0.3, 0), off=0.0012)
        decal(kit, f"Z crack {i}", bm_band(pts, 0.0028), M(kit, 'crack'), hp, head, loc=(0, -0.3, 0), off=0.002)
    decal(kit, "Z chip", bm_ellipse(0.012, 0.009, rad=jag(kit, 16, 0.6, 1.3)), M(kit, 'zskin', 0.7), hp, head,
          loc=(0.066, -0.3, 0.068), off=0.0014)
    decal(kit, "Z nose wear", bm_ellipse(0.009, 0.007, rad=jag(kit, 16)), M(kit, 'wear'), hp, head,
          loc=(0.003, -0.3, 0.088), off=0.0014)


def zombie_paint(kit, b, hit):
    torso, waist = b['torso'], b['waist']
    # torn holes in the shirt showing lime plastic, paint wear on edges
    decal(kit, "Z shirt hole", bm_ellipse(0.03, 0.026, rad=jag(kit, 16, 0.55, 1.35)), M(kit, 'zskin'), waist, torso,
          loc=(-0.06, -0.3, 0.2))
    decal(kit, "Z shirt hole 2", bm_ellipse(0.02, 0.03, rad=jag(kit, 16, 0.55, 1.35)), M(kit, 'zskin'), waist,
          torso, loc=(0.18, 0, 0.14), rot=(0, 0, 90))
    for i, (x, zz, r) in enumerate(((0.1, 0.3, 0.02), (-0.13, 0.27, 0.016), (0.03, 0.12, 0.012))):
        decal(kit, f"Z shirt wear {i}", bm_ellipse(r, r * 0.7, rad=jag(kit, 16, 0.5, 1.3)), M(kit, 'wear'), waist,
              torso, loc=(x, -0.3, zz))
    for sd, leg in b['legs'].items():
        decal(kit, f"Z knee wear {sd}", bm_ellipse(0.022, 0.016, rad=jag(kit, 16, 0.5, 1.3)), M(kit, 'wear'),
              leg['kn'], leg['shin'], loc=(0, -0.3, -0.06))
    # strawberry ice cream splat stuck on the right shoulder (molded, with drips)
    splat = bm_ellipse(0.06, 0.05, rad=[1.0, 1.35, 0.8, 1.1, 0.75, 1.3, 0.9, 1.05, 0.7, 1.25, 0.85, 1.0, 0.8, 1.4,
                                       0.9, 1.1], rings=3)
    bm_band([(-0.02, -0.03), (-0.024, -0.07), (-0.02, -0.1)], [0.016, 0.012, 0.014], splat)
    bm_band([(0.025, -0.03), (0.028, -0.055)], [0.014, 0.012], splat)
    decal(kit, "Z ice cream splat", splat, M(kit, 'straw'), waist, torso, loc=(-0.07, -0.3, 0.27),
          off=0.002, thick=0.012, sub=1)
    for i, (dx, dz, r) in enumerate(((-0.08, 0.285, 0.024), (-0.055, 0.265, 0.017), (-0.1, 0.262, 0.015))):
        ball(kit, f"Z splat lump {i}", waist, r, M(kit, 'vanilla' if i else 'straw'), loc=(dx, -0.135, dz), seg=12)
    if hit:  # empty shoulder socket where the arm popped off
        decal(kit, "Z socket hole", bm_ellipse(0.046, 0.046, seg=20), M(kit, 'socket'), waist, torso,
              loc=(0.36, -0.09, 0.3), rot=(0, 0, 70), off=0.002)
        torus(kit, "Z socket rim", 0.052, 0.013, M(kit, 'zshirt', 0.85), waist, loc=(0.192, -0.022, 0.3),
              rot=(0, 90, -20))
        decal(kit, "Z hit splat", bm_ellipse(0.07, 0.06, rad=[1.0, 1.4, 0.7, 1.2, 0.8, 1.45, 0.75, 1.1, 0.7, 1.3, 0.9,
                                                          1.15, 0.7, 1.35, 0.85, 1.2], rings=3),
              M(kit, 'goo'), waist, torso, loc=(0.07, -0.3, 0.2), off=0.002, thick=0.008, sub=1)


def build_zombie(kit, root, hit=False):
    S = dict(name="Z", zombie=True, shirt='zshirt', pants='zpants', skin='zskin', belt='shoe', boot='shoe',
             sole='zhair', neck_len=0.055, feet={'L': 'bare', 'R': 'boot'}, torn_shin='L')
    if not hit:
        S['waist'] = (34, -7, 8)
        S['neck'] = (-20, 0, -6)
        S['head'] = (-24, 14, 4)
        S['shoulder'] = {'R': (-112, 0, 10), 'L': (-58, -12, 0)}
        S['elbow'] = {'R': (-12, 0, 0), 'L': (-26, 34, 0)}
        S['wrist'] = {'R': (34, 0, 0), 'L': (38, 0, 12)}
        S['hip'] = {'R': (-24, 4, 0), 'L': (14, -5, -12)}
        kr = 38
    else:
        S['waist'] = (-14, 8, -36)
        S['neck'] = (-16, 0, 0)
        S['head'] = (-22, -14, -10)
        S['shoulder'] = {'R': (-10, 112, 0), 'L': (0, 0, 0)}
        S['elbow'] = {'R': (-55, 0, 0), 'L': (-30, 0, 0)}
        S['wrist'] = {'R': (20, 0, 0), 'L': (25, 0, 0)}
        S['hip'] = {'R': (-6, 4, 0), 'L': (-26, -8, -6)}
        kr = 20
    drop = leg_drop(S['hip']['R'], kr)
    kl = solve_knee(S['hip']['L'], drop)
    S['hip_z'] = drop + 0.05
    S['knee'] = {'R': (kr, 0, 0), 'L': (kl, 0, 0)}
    S['ankle'] = {'R': (-(S['hip']['R'][0] + kr), -S['hip']['R'][1], 0),
                  'L': (-(S['hip']['L'][0] + kl), -S['hip']['L'][1], 0)}
    if hit:
        W = deg_euler(S['waist']).to_matrix()
        shoulder = Vector((0, 0, S['hip_z'] + 0.102)) + W @ Vector((0.205, 0, 0.3))
        S['pop'] = True
        S['shoulder_world'] = shoulder
        S['pop_loc'] = tuple(shoulder + Vector((0.38, -0.36, 0.42)))
        S['pop_rot'] = tuple(math.degrees(a) for a in
                             Vector((0.5, -0.35, 0.8)).to_track_quat('Z', 'X').to_euler())
    b = build_body(kit, root, S)
    zombie_head(kit, b, hit)
    zombie_paint(kit, b, hit)
    if hit:
        impact_fx(kit, root, S, b)


# ------------------------------------------------------------------ hit FX: glossy goo, ice cream, plastic shards, pegs

def drop(kit, name, parent, pos, direction, size, mat):
    prof = [(0.0, 0.06), (0.25, 0.3), (0.55, 0.72), (0.85, 0.97), (1.1, 1.0), (1.35, 0.82), (1.5, 0.42), (1.55, 0.08)]
    ob = loft(kit, name, [dict(z=z * size, rx=r * size) for z, r in prof], mat, parent, n=10, sub=1, loc=pos)
    ob.rotation_euler = (-Vector(direction)).to_track_quat('Z', 'Y').to_euler()
    return ob


def blob(kit, name, parent, pos, r, mat, squash=1.0):
    rad = jag(kit, 12, 0.82, 1.15)
    rings = [dict(z=-r * squash, rx=r * 0.25, rad=rad), dict(z=-r * 0.6 * squash, rx=r * 0.85, rad=rad),
             dict(z=0, rx=r * 1.0, rad=rad), dict(z=r * 0.6 * squash, rx=r * 0.82, rad=rad),
             dict(z=r * squash, rx=r * 0.25, rad=rad)]
    ob = loft(kit, name, rings, mat, parent, n=12, sub=1, loc=pos)
    ob.rotation_euler = [kit.rand.uniform(0, 6.28) for _ in range(3)]
    return ob


def floor_splat(kit, name, parent, pos, r, mat, h=0.012, spikes=True):
    n = 16
    rad = [kit.rand.uniform(0.75, 1.1) * (kit.rand.choice((1.0, 1.0, 1.45)) if spikes else 1.0) for _ in range(n)]
    rings = [dict(z=0.0, rx=r, rad=rad), dict(z=h * 0.6, rx=r * 0.98, rad=rad), dict(z=h, rx=r * 0.8, rad=rad)]
    ob = loft(kit, name, rings, mat, parent, n=n, sub=1, loc=pos)
    ob.rotation_euler.z = kit.rand.uniform(0, 6.28)
    return ob


def shard(kit, name, parent, pos, size, mat):
    rnd = kit.rand
    bm = bmesh.new()
    k = rnd.randint(4, 6)
    angs = sorted(rnd.uniform(0, 2 * math.pi) for _ in range(k))
    bot = [bm.verts.new((size * rnd.uniform(0.5, 1.2) * math.cos(a), size * rnd.uniform(0.4, 1.0) * math.sin(a), 0))
           for a in angs]
    t = size * 0.22
    top = [bm.verts.new((v.co.x * 0.92, v.co.y * 0.92, t)) for v in bot]
    bm.faces.new(bot)
    bm.faces.new(list(reversed(top)))
    for i in range(k):
        bm.faces.new((bot[i], bot[(i + 1) % k], top[(i + 1) % k], top[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent, pos, smooth=False)
    ob.rotation_euler = [rnd.uniform(0, 6.28) for _ in range(3)]
    return ob


def peg(kit, name, parent, pos, rot, mat):
    p = kit.empty(name, parent, pos, rot)
    kit.prim(name + " shaft", 'cyl', (0.014, 0.014, 0.04), mat, p, segments=12)
    ball(kit, name + " knob", p, 0.019, mat, loc=(0, 0, 0.026), seg=12)
    kit.prim(name + " collar", 'cyl', (0.022, 0.022, 0.008), mat, p, offset=(0, 0, -0.02), segments=14, bevel=0.003)
    return p


def impact_fx(kit, root, S, b):
    rnd = kit.rand
    fx = kit.empty("Z fx", root)
    c = S['shoulder_world'] + Vector((0.06, -0.06, 0.0))
    goo, straw, van, choc = M(kit, 'goo'), M(kit, 'straw'), M(kit, 'vanilla'), M(kit, 'choc')
    body = [M(kit, 'zskin'), M(kit, 'zshirt'), M(kit, 'zpants'), M(kit, 'zshirt', 0.85)]

    def spray_dir():
        d = Vector((rnd.uniform(-0.15, 1.0), rnd.uniform(-1.0, 0.2), rnd.uniform(-0.3, 1.0)))
        return d.normalized()
    # flying arm trail of goo from the popped peg
    arm_loc = Vector(S['pop_loc'])
    for i in range(5):
        t = (i + 1) / 6
        p = c.lerp(arm_loc, t) + Vector((0, 0, 0.06 * math.sin(t * math.pi)))
        drop(kit, f"Z trail drop {i}", fx, tuple(p), arm_loc - c, 0.012 + 0.006 * (1 - t), goo)
    # big goo burst
    for i in range(28):
        d = spray_dir()
        dist = rnd.uniform(0.12, 0.75)
        drop(kit, f"Z goo drop {i}", fx, tuple(c + d * dist), d, rnd.uniform(0.014, 0.034), goo)
    for i in range(10):
        d = spray_dir()
        blob(kit, f"Z goo blob {i}", fx, tuple(c + d * rnd.uniform(0.08, 0.45)), rnd.uniform(0.022, 0.045), goo,
             squash=rnd.uniform(0.7, 1.1))
    blob(kit, "Z goo eruption", fx, tuple(c + Vector((0.02, -0.02, 0.0))), 0.055, goo, squash=0.8)
    # ice cream chunks (scoops) and sprinkles
    for i in range(11):
        d = spray_dir()
        mat = (straw, van, choc, straw, van, straw, choc)[i % 7]
        blob(kit, f"Z scoop chunk {i}", fx, tuple(c + d * rnd.uniform(0.15, 0.65)), rnd.uniform(0.03, 0.06), mat,
             squash=0.85)
    for i in range(44):
        d = spray_dir()
        p = c + d * rnd.uniform(0.1, 0.65)
        kit.prim(f"Z sprinkle {i}", 'cyl', (0.004, 0.004, 0.018), M(kit, SPRINKLES[i % len(SPRINKLES)]), fx,
                 offset=tuple(p), rot=(rnd.uniform(0, 180), rnd.uniform(0, 180), 0), segments=6, bevel=0.002,
                 bevel_segments=1)
    # plastic shards in body colors and popped pegs
    for i in range(24):
        d = spray_dir()
        shard(kit, f"Z shard {i}", fx, tuple(c + d * rnd.uniform(0.1, 0.7)), rnd.uniform(0.018, 0.045), body[i % 4])
    for i in range(4):
        d = spray_dir()
        peg(kit, f"Z popped peg {i}", fx, tuple(c + d * rnd.uniform(0.2, 0.45)),
            (rnd.uniform(0, 180), rnd.uniform(0, 180), 0), M(kit, 'peg'))
    # floor: puddles, melted scoop, shards and a peg lying on the floor
    fx_floor = [((0.45, -0.25), 0.15, goo), ((0.75, -0.55), 0.09, goo), ((0.25, -0.55), 0.06, goo),
                ((0.55, -0.05), 0.11, straw), ((0.95, -0.3), 0.06, van), ((0.15, -0.3), 0.05, straw)]
    for i, ((x, y), r, mat) in enumerate(fx_floor):
        floor_splat(kit, f"Z floor splat {i}", fx, (x, y, 0.0), r, mat)
        for j in range(3):
            a = rnd.uniform(0, 6.28)
            floor_splat(kit, f"Z floor dot {i}.{j}", fx, (x + math.cos(a) * r * 1.6, y + math.sin(a) * r * 1.6, 0),
                        r * rnd.uniform(0.12, 0.22), mat, h=0.008, spikes=False)
    blob(kit, "Z floor scoop", fx, (0.55, -0.05, 0.03), 0.04, straw, squash=0.7)
    for i in range(6):
        sh = shard(kit, f"Z floor shard {i}", fx, (rnd.uniform(0.2, 1.0), rnd.uniform(-0.7, 0.0), 0.004),
                   rnd.uniform(0.016, 0.03), body[i % 4])
        sh.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
    peg(kit, "Z floor peg", fx, (0.7, -0.15, 0.02), (90, 0, 35), M(kit, 'peg'))


# ------------------------------------------------------------------ gun: chunky molded toy blaster

def build_gun(kit, root):
    blue, blue2, pink = M(kit, 'gun'), M(kit, 'gun2'), M(kit, 'pink')
    waf, waf2, white = M(kit, 'waffle'), M(kit, 'waffle2'), M(kit, 'white')
    # main body, lofted front-to-back (geometry rotated so loft +Z points along -Y)
    loft(kit, "G body", [
        dict(z=-0.096, rx=.012, ry=.02, cy=.02), dict(z=-0.09, rx=.024, ry=.034, cy=.02),
        dict(z=-0.07, rx=.028, ry=.04, cy=.017, p=2.6), dict(z=-0.0, rx=.029, ry=.042, cy=.015, p=2.8),
        dict(z=0.055, rx=.028, ry=.038, cy=.016, p=2.7), dict(z=0.072, rx=.024, ry=.03, cy=.018),
        dict(z=0.078, rx=.014, ry=.018, cy=.018)], blue, root, n=12, sub=1, grot=(90, 0, 0))
    # pink side panels with molded screws (toy assembly detail on the camera side)
    for s in (-1, 1):
        kit.prim(f"G panel {s}", 'sphere', (0.006, 0.05, 0.022), pink, root, offset=(s * 0.027, 0.01, 0.012),
                 segments=16, rings=8)
        for i, (y, zz) in enumerate(((0.06, -0.012), (-0.045, 0.036), (0.07, 0.04))):
            kit.prim(f"G screw {s}{i}", 'cyl', (0.0045, 0.0045, 0.004), blue2, root, offset=(s * 0.0295, y, zz),
                     rot=(0, 90, 0), segments=10)
    # barrel and pink ring
    loft(kit, "G barrel", [dict(z=0.07, rx=.017, m=0), dict(z=0.1, rx=.017, m=0), dict(z=0.101, rx=.021, m=1),
                           dict(z=0.112, rx=.021, m=1), dict(z=0.113, rx=.017, m=0), dict(z=0.13, rx=.017, m=0)],
         [blue, pink], root, n=16, sub=0, grot=(90, 0, 0), loc=(0, 0, 0.018))
    # waffle-cone muzzle: checkerboard in/out offsets on the cage subdivide into a molded diamond waffle
    def cone_r(t):
        return 0.018 + 0.036 * t ** 1.3
    rings = [dict(z=0.118 + 0.1 * i / 6, rx=cone_r(i / 6)) for i in range(7)]
    loft(kit, "G waffle cone", rings, waf, root, n=16, sub=1, caps=(True, False), grot=(90, 0, 0), loc=(0, 0, 0.018))
    bm = bmesh.new()  # criss-cross waffle ridges: triangular-profile strips laid on the cone
    for d in (-1, 1):
        for j in range(8):
            rows = []
            for i in range(6):
                t = 0.12 + 0.88 * i / 5
                ph = 2 * math.pi * j / 8 + d * 1.5 * t
                r = cone_r(t) * 0.99
                p = Vector((r * math.cos(ph), -(0.118 + 0.1 * t), 0.018 + r * math.sin(ph)))
                nrm = Vector((math.cos(ph), 0, math.sin(ph)))
                tan = Vector((-math.sin(ph) * d * 1.5 * r, -0.1, math.cos(ph) * d * 1.5 * r))
                side = tan.cross(nrm).normalized() * 0.0035
                rows.append([bm.verts.new(p - side), bm.verts.new(p + nrm * 0.0035), bm.verts.new(p + side)])
            for i in range(5):
                for k in range(2):
                    bm.faces.new((rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    kit.mesh_from_bmesh("G waffle ridges", bm, waf2, root)
    torus(kit, "G cone rim", 0.055, 0.007, waf2, root, loc=(0, -0.219, 0.018), rot=(90, 0, 0), N=24, Mn=6)
    ball(kit, "G loaded scoop", root, 0.036, M(kit, 'straw'), loc=(0, -0.205, 0.018), seg=16)
    # tub magazine on top: pint with pink label, chocolate scoop with molded ruffle lip, sprinkles
    kit.prim("G tub mount", 'box', (0.04, 0.05, 0.02), blue2, root, offset=(0, -0.005, 0.057), bevel=0.006)
    tub = kit.empty("G tub", root, (0, -0.005, 0.062))
    loft(kit, "G pint tub", [dict(z=0.0, rx=.029, m=0), dict(z=0.006, rx=.03, m=0), dict(z=0.014, rx=.031, m=1),
                             dict(z=0.04, rx=.034, m=0), dict(z=0.052, rx=.035, m=0), dict(z=0.054, rx=.039, m=0),
                             dict(z=0.061, rx=.039, m=0), dict(z=0.062, rx=.033, m=0)], [white, pink], tub, n=18,
         sub=0)
    scoop = loft(kit, "G choc scoop", [
        dict(z=0.056, rx=.03), dict(z=0.064, rx=.039, fold=.07, foldn=9), dict(z=0.072, rx=.04, fold=.05, foldn=9,
                                                                               ph=0.5),
        dict(z=0.09, rx=.036), dict(z=0.105, rx=.026), dict(z=0.113, rx=.012), dict(z=0.115, rx=.003)],
        M(kit, 'choc'), tub, n=14, sub=1)
    rnd = kit.rand
    for i in range(16):
        az = rnd.uniform(0, 2 * math.pi)
        el = rnd.uniform(0.25, 1.35)
        cz = 0.07
        p = Vector((0.036 * math.cos(el) * math.cos(az), 0.036 * math.cos(el) * math.sin(az),
                    cz + 0.042 * math.sin(el)))
        kit.prim(f"G sprinkle {i}", 'cyl', (0.0028, 0.0028, 0.011), M(kit, SPRINKLES[i % len(SPRINKLES)]), tub,
                 offset=tuple(p), rot=(rnd.uniform(40, 140), 0, math.degrees(az) + 90), segments=6)
    # grip angled back with molded finger grooves
    grip_rings = []
    for i, (zz, rx, ry, fr) in enumerate(((-0.005, .017, .022, 0), (-0.03, .017, .022, .004), (-0.05, .0165, .021, -.002),
                                         (-0.07, .0165, .021, .004), (-0.09, .017, .022, -.002),
                                         (-0.11, .018, .023, .003), (-0.122, .021, .026, 0), (-0.132, .02, .025, 0))):
        grip_rings.append(dict(z=zz, rx=rx, ry=ry, cy=0.064 + (-zz) * 0.25, p=2.4, front=max(fr, 0)))
    loft(kit, "G grip", grip_rings, pink, root, n=10, sub=1)
    # trigger guard + trigger
    kit.skin("G trigger guard", [(0, -0.03, -0.018), (0, -0.036, -0.048), (0, -0.016, -0.066), (0, 0.022, -0.066),
                                 (0, 0.05, -0.05)], [(i, i + 1) for i in range(4)], [(0.0075, 0.0075)] * 5, blue, root,
             subsurf=1)
    kit.skin("G trigger", [(0, 0.004, -0.018), (0, -0.004, -0.034), (0, 0.004, -0.05)], [(0, 1), (1, 2)],
             [0.0065, 0.006, 0.0055], pink, root, subsurf=1)
    # sights and hammer knob
    kit.prim("G front sight", 'box', (0.008, 0.016, 0.014), pink, root, offset=(0, -0.07, 0.058), bevel=0.004)
    kit.prim("G rear sight", 'box', (0.02, 0.012, 0.014), pink, root, offset=(0, 0.075, 0.056), bevel=0.004)
    ball(kit, "G hammer", root, 0.014, pink, loc=(0, 0.098, 0.04), seg=12)


def setup(scene, stage):
    ld = bpy.data.lights.new("D softbox", 'AREA')
    ld.energy = 120
    ld.size = 2.5
    ld.color = hexc("#ffffff")[:3]
    ob = bpy.data.objects.new("D softbox", ld)
    stage.objects.link(ob)
    ob.location = (-1.5, -4.5, 3.5)
    ob.rotation_euler = (Vector((0.4, 0.5, 0.9)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
