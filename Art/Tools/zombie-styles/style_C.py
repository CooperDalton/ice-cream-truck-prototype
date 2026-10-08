"""Style C: Ink comic. Saturday-morning cartoon / Borderlands-lite.
Exaggerated cartoon anatomy built from lofted tubes (bmesh cages + subsurf), inverted-hull ink outlines on every
visible part (thick on silhouettes, thin on details), faces drawn as flat shapes conformed onto the head."""
from common import *

KEY = "C"
LABEL = "Ink comic"
SHADER = 'ink'
WORLD = "#fff4d8"
FLOOR = "#ffe9b8"

INK = "#1a1024"
W_SIL = 0.014   # silhouette outline width (characters)
W_MID = 0.009
W_IN = 0.0055   # inner detail outline
X = Vector((1, 0, 0))
Z = Vector((0, 0, 1))
IMPACT_CAM = Vector((1.7, -0.5, 1.3))

SKIN = "#ffcf9e"; SHIRT = "#e8443a"; PANTS = "#2f5bd3"; WHITE = "#fffaf0"; COOLER = "#3ec7c1"
BOOT = "#6b3f2a"; SOLE = "#2b1d2b"; HAIR = "#6b3f1f"; STRAP = "#1f7c78"
ZSKIN = "#8bd14e"; ZSHIRT = "#7a4bd1"; ZPANTS = "#2aa39a"; BRAIN = "#ff8fb0"; MOUTH = "#5a1630"
ORANGE = "#ffb627"; TEAL = "#3ec7c1"; CONE = "#e0a458"; CHOC = "#7a4425"; PINK = "#ff8fc0"; VANILLA = "#fff1cf"
BLOOD = "#e3262f"; STAR = "#ffe14d"


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


def setup(scene, stage_collection):
    scene.render.filter_size = 1.0
    scene.eevee.use_raytracing = False


# ------------------------------------------------------------------ helpers
def flat(kit, name, hx):
    """Unlit flat color: drawn face features, FX fills, ink strokes."""
    key = (name, hx, 'flatC')
    if key not in kit._mats:
        m = bpy.data.materials.new(f"ZD2 C flat {name}")
        nt = v1.node_tree(m)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = hexc(hx)
        nt.links.new(em.outputs[0], out.inputs[0])
        m.diffuse_color = hexc(hx)
        kit._mats[key] = m
    return kit._mats[key]


def mk(kit, name, verts, faces, mat, parent, subsurf=1, ow=None, smooth=True):
    bm = bmesh.new()
    vs = [bm.verts.new(Vector(v)) for v in verts]
    for f in faces:
        bm.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent, smooth=smooth)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    if ow:
        kit.outline(ob, ow, INK)
    return ob


def tube(kit, name, pts, radii, mat, parent=None, n=10, subsurf=1, ow=None, ref=None, dome=0.6, caps=(True, True)):
    """Lofted tube through pts. radii: float or (ra, rb); ra lies along ref (default X) projected off the tangent."""
    pts = [Vector(p) for p in pts]
    m = len(pts)
    if ref is None:
        d = (pts[-1] - pts[0]).normalized()
        ref = X if abs(d.x) < 0.8 else Z
    ref = Vector(ref)
    verts, faces, tans = [], [], []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]).normalized()
        u = (ref - t * ref.dot(t)).normalized()
        w = t.cross(u)
        r = radii[i]
        ra, rb = (r, r) if isinstance(r, (int, float)) else r
        for k in range(n):
            a = 2 * math.pi * k / n
            verts.append(p + u * math.cos(a) * ra + w * math.sin(a) * rb)
        tans.append((t, min(ra, rb)))
    for i in range(m - 1):
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((i * n + k, i * n + k2, (i + 1) * n + k2, (i + 1) * n + k))
    if caps[0]:
        c = len(verts)
        verts.append(pts[0] - tans[0][0] * tans[0][1] * dome)
        faces += [(c, (k + 1) % n, k) for k in range(n)]
    if caps[1]:
        c = len(verts)
        verts.append(pts[-1] + tans[-1][0] * tans[-1][1] * dome)
        b = (m - 1) * n
        faces += [(c, b + k, b + (k + 1) % n) for k in range(n)]
    return mk(kit, name, verts, faces, mat, parent, subsurf, ow)


def lathe(kit, name, prof, mat, parent=None, axis='Z', center=(0, 0, 0), n=16, subsurf=1, ow=None, closed=False,
          sx=1.0, sy=1.0):
    """Surface of revolution. prof: list of (r, h). Open profiles cap to the axis where r == 0."""
    c = Vector(center)

    def P(r, a, h):
        x, y = r * math.cos(a) * sx, r * math.sin(a) * sy
        return c + (Vector((x, y, h)) if axis == 'Z' else Vector((x, h, y)))
    verts, faces, rings = [], [], []
    for r, h in prof:
        if r == 0:
            verts.append(c + (Vector((0, 0, h)) if axis == 'Z' else Vector((0, h, 0))))
            rings.append(len(verts) - 1)
        else:
            rings.append([len(verts) + k for k in range(n)])
            verts += [P(r, 2 * math.pi * k / n, h) for k in range(n)]
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for k in range(n):
            k2 = (k + 1) % n
            if isinstance(a, int):
                faces.append((a, b[k], b[k2]))
            elif isinstance(b, int):
                faces.append((a[k], a[k2], b))
            else:
                faces.append((a[k], a[k2], b[k2], b[k]))
    return mk(kit, name, verts, faces, mat, parent, subsurf, ow)


def surf_r(d, rad, fn):
    r = 1 / math.sqrt((d.x / rad[0]) ** 2 + (d.y / rad[1]) ** 2 + (d.z / rad[2]) ** 2)
    return r * (fn(d) if fn else 1)


def dirf(u, v):
    return Vector((math.sin(u) * math.cos(v), -math.cos(u) * math.cos(v), math.sin(v)))


def surf(c, rad, fn, u, v, lift=0.0):
    d = dirf(u, v)
    return Vector(c) + d * (surf_r(d, rad, fn) + lift)


def blob(kit, name, c, rad, mat, parent=None, fn=None, seg=24, rings=14, ow=None, subsurf=0):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=rings, radius=1)
    for v in bm.verts:
        d = v.co.normalized()
        v.co = Vector(c) + d * surf_r(d, rad, fn)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    if ow:
        kit.outline(ob, ow, INK)
    return ob


def offset_poly(poly, d):
    n = len(poly)
    area = sum(poly[i][0] * poly[(i + 1) % n][1] - poly[(i + 1) % n][0] * poly[i][1] for i in range(n))
    s = 1 if area > 0 else -1

    def nrm(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        return s * dy / L, -s * dx / L
    out = []
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        n1, n2 = nrm(p0, p1), nrm(p1, p2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        L = math.hypot(bx, by)
        bx, by = (bx / L, by / L) if L > 1e-6 else n1
        k = max(0.4, bx * n1[0] + by * n1[1])
        out.append((p1[0] + bx * d / k, p1[1] + by * d / k))
    return out


def ell(cu, cv, ru, rv, n=20, rot=0.0):
    cr, sr = math.cos(rot), math.sin(rot)
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a) * ru, math.sin(a) * rv
        out.append((cu + x * cr - y * sr, cv + x * sr + y * cr))
    return out


def stroke_poly(center, widths):
    """Closed polygon around a 2D centerline with per-point half-widths (tapered brush stroke)."""
    left, right = [], []
    n = len(center)
    for i, (p, w) in enumerate(zip(center, widths)):
        a, b = center[max(i - 1, 0)], center[min(i + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((p[0] + nx * w, p[1] + ny * w))
        right.append((p[0] - nx * w, p[1] - ny * w))
    return left + right[::-1]


def decal(kit, name, c, rad, fn, poly, mat, parent, lift=0.004, ow=0.0, cuts=2):
    """Flat drawn shape conformed onto an ellipsoid surface; poly in (yaw, pitch) radians around -Y.
    ow (radians) adds an ink border drawn just beneath."""
    def build(pl, lift, m, nm):
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new((u, v, 0)) for u, v in pl])
        bmesh.ops.triangulate(bm, faces=[f], ngon_method='EAR_CLIP')
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=cuts, use_grid_fill=True)
        for vt in bm.verts:
            vt.co = surf(c, rad, fn, vt.co.x, vt.co.y, lift)
        return kit.mesh_from_bmesh(nm, bm, m, parent, smooth=False)
    if ow:
        build(offset_poly(poly, ow), lift * 0.5, flat(kit, "ink", INK), name + " ink")
    return build(poly, lift, mat, name)


def flat_poly(kit, name, poly, mat, parent=None, ow=0.0, z=0.0, ink_z=-0.002):
    """Flat 2D shape in the local XY plane (normal +Z) with an optional ink border underneath."""
    def build(pl, zz, m, nm):
        bm = bmesh.new()
        f = bm.faces.new([bm.verts.new((u, v, zz)) for u, v in pl])
        bmesh.ops.triangulate(bm, faces=[f], ngon_method='EAR_CLIP')
        return kit.mesh_from_bmesh(nm, bm, m, parent, smooth=False)
    ob = build(poly, z, mat, name)
    if ow:
        ink = build(offset_poly(poly, ow), z + ink_z, flat(kit, "ink", INK), name + " ink")
        ink.parent = ob
    return ob


def stroke(kit, name, pts, mat, parent=None, bevel=0.002, radii=None):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = bevel
    cu.bevel_resolution = 2
    cu.use_fill_caps = True
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for i, (pt, p) in enumerate(zip(sp.points, pts)):
        pt.co = (p[0], p[1], p[2], 1)
        pt.radius = radii[i] if radii else 1.0
    cu.materials.append(mat)
    return kit.link(name, cu, parent)


def jag_band(kit, name, c, axis, rw, rd, length, mat, parent, n=14, up=False, ow=W_IN, thick=0.008, flare=1.06):
    """Torn cloth hem / broken skull rim: a ring with ragged triangular teeth, given thickness by Solidify."""
    c, a = Vector(c), Vector(axis).normalized()
    u = (X - a * X.dot(a)).normalized() if abs(a.x) < 0.8 else (Z - a * Z.dot(a)).normalized()
    w = a.cross(u)
    sgn = 1 if up else -1
    verts, faces = [], []
    for k in range(n):
        ang = 2 * math.pi * k / n
        verts.append(c + u * math.cos(ang) * rw + w * math.sin(ang) * rd)
    for k in range(n):
        ang = 2 * math.pi * (k + 0.5) / n
        L = length * (kit.rand.uniform(0.6, 1.25) if k % 2 == 0 else kit.rand.uniform(0.15, 0.35))
        verts.append(c + a * sgn * L + (u * math.cos(ang) * rw + w * math.sin(ang) * rd) * flare)
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((k, k2, n + k))
        faces.append((k2, n + k2, n + k))
    ob = mk(kit, name, verts, faces, mat, parent, 0, None)
    sol = ob.modifiers.new("Thick", 'SOLIDIFY')
    sol.thickness = thick
    sol.offset = 0
    if ow:
        kit.outline(ob, ow, INK)
    return ob


def oprim(kit, w, *a, **k):
    ob = kit.prim(*a, **k)
    kit.outline(ob, w, INK)
    return ob


def piv(kit, name, parent, absp, pabs=(0, 0, 0)):
    return kit.empty(name, parent, tuple(Vector(absp) - Vector(pabs)))


def rel(pts, o):
    return [Vector(p) - Vector(o) for p in pts]


def lerp(a, b, t):
    return Vector(a).lerp(Vector(b), t)


def aim_matrix(loc, fwd, up=Z):
    """Pivot matrix whose local -Z points along fwd (used for hands hanging off forearms)."""
    q = (-Vector(fwd)).to_track_quat('Z', 'Y')
    return Matrix.Translation(Vector(loc)) @ q.to_matrix().to_4x4()


# ------------------------------------------------------------------ player
def player_fist(kit, parent, thumb_up):
    """Huge cartoon fist in hand-local space (origin = fist center, fingers rolled toward -Y)."""
    sk = kit.mat("skin", SKIN)
    blob(kit, "fist", (0, 0, 0), (0.05, 0.058, 0.056), sk, parent, ow=W_MID)
    for i, z in enumerate((0.03, 0.0, -0.03)):
        tube(kit, f"finger roll {i}", [(-0.036, -0.045, z), (0.036, -0.048, z)], [0.019, 0.019], sk, parent, n=8,
             dome=0.9, ow=W_IN)
    if thumb_up:
        tube(kit, "thumb", [(0.0, -0.02, 0.04), (0.0, -0.025, 0.085), (0.004, -0.028, 0.115)], [0.024, 0.021, 0.019],
             sk, parent, n=8, ow=W_IN)
    else:
        tube(kit, "thumb", [(0.045, 0.01, 0.03), (0.05, -0.03, 0.045), (0.045, -0.06, 0.05)], [0.022, 0.02, 0.017], sk,
             parent, n=8, ow=W_IN)


def player_head(kit, hp):
    sk = kit.mat("skin", SKIN)
    hc, hr = (0, -0.01, 0.13), (0.155, 0.145, 0.16)

    def hfn(d):
        low = max(0.0, -d.z)
        return 1 + 0.16 * low * (1 - low) + 0.06 * low * max(0.0, -d.y)
    blob(kit, "head", hc, hr, sk, hp, fn=hfn, seg=32, rings=18, ow=W_SIL)
    ink, white = flat(kit, "ink", INK), flat(kit, "white", "#ffffff")
    R = 0.15
    o = 0.006 / R
    # eyes: big ovals touching, pupils looking toward the aim (character right = -u)
    for s in (1, -1):
        eu = 0.2 * s
        decal(kit, f"eye white {s}", hc, hr, hfn, ell(eu, 0.12, 0.155, 0.24, 24), white, hp, 0.004, o)
        pu = eu - 0.055
        decal(kit, f"pupil {s}", hc, hr, hfn, ell(pu, 0.09, 0.07, 0.115, 18), ink, hp, 0.006)
        decal(kit, f"eye shine {s}", hc, hr, hfn, ell(pu + 0.025, 0.14, 0.024, 0.032, 10), white, hp, 0.008)
    # brows: right one low and determined, left one cocked high
    decal(kit, "brow R", hc, hr, hfn, stroke_poly([(-0.42, 0.41), (-0.27, 0.43), (-0.08, 0.38)], [0.035, 0.06, 0.05]),
          ink, hp, 0.006)
    decal(kit, "brow L", hc, hr, hfn, stroke_poly([(0.07, 0.47), (0.22, 0.56), (0.4, 0.52)], [0.05, 0.06, 0.03]),
          ink, hp, 0.006)
    # cocky lopsided grin with a row of teeth
    def top(t):
        return -0.38 + 0.84 * t, -0.27 + 0.11 * t + 0.04 * math.sin(math.pi * t)
    N = 14
    top_e = [top(i / N) for i in range(N + 1)]
    bot = []
    for i in range(N - 1, 0, -1):
        u, v = top(i / N)
        bot.append((u, v - 0.27 * math.sin(math.pi * i / N) ** 0.75))
    mouth = top_e + bot
    decal(kit, "grin", hc, hr, hfn, mouth, flat(kit, "mouth", "#6e1626"), hp, 0.005, o)
    teeth = [(u, v - 0.015) for u, v in top_e[1:-1]]
    teeth += [(u, v - 0.015 - min(0.085, 0.27 * math.sin(math.pi * i / N) ** 0.75 * 0.55))
              for i, (u, v) in reversed(list(enumerate(top_e[1:-1], 1)))]
    decal(kit, "teeth", hc, hr, hfn, teeth, white, hp, 0.007)
    tongue = ell(0.07, -0.47, 0.13, 0.06, 14)
    decal(kit, "tongue", hc, hr, hfn, tongue, flat(kit, "tongue", "#ff6f7d"), hp, 0.0065)
    # nose, ears, hair
    blob(kit, "nose", surf(hc, hr, hfn, 0.02, -0.06, 0.012), (0.036, 0.03, 0.03), sk, hp, ow=W_IN)
    for s in (1, -1):
        blob(kit, f"ear {s}", surf(hc, hr, hfn, 1.5 * s, 0.0, -0.01), (0.022, 0.036, 0.046), sk, hp, ow=W_MID)
        decal(kit, f"sideburn {s}", hc, hr, hfn, [(1.2 * s, 0.32), (1.38 * s, 0.32), (1.32 * s, 0.05), (1.22 * s, 0.1)],
              flat(kit, "hair", HAIR), hp, 0.004)
    hair = kit.mat("hair", HAIR)
    for i, (u0, du, dz) in enumerate(((-0.25, -0.12, 0.02), (0.05, 0.06, 0.04), (0.3, 0.14, 0.0))):
        a = surf(hc, hr, None, u0, 0.62, -0.01)
        b = surf(hc, hr, None, u0 + du, 0.5, 0.025)
        tube(kit, f"hair tuft {i}", [a, b, b + Vector((du * 0.25, -0.02, -0.035 + dz))], [0.03, 0.022, 0.006], hair, hp,
             n=8, ow=W_IN)
    # paper soda-jerk cap, garrison shape, cocked to the side
    cap = kit.empty("cap", hp, (0, -0.005, 0.215), (4, -11, 0))
    paper = kit.mat("paper", WHITE)
    n = 16
    verts, faces = [], []
    for rx, ry, z0, peak in ((0.14, 0.142, 0.0, 0.0), (0.132, 0.168, 0.05, 0.012), (0.02, 0.172, 0.125, 0.045)):
        for k in range(n):
            a = 2 * math.pi * k / n
            verts.append((rx * math.cos(a), ry * math.sin(a), z0 + peak * abs(math.sin(a)) ** 2))
    for i in range(2):
        for k in range(n):
            faces.append((i * n + k, i * n + (k + 1) % n, (i + 1) * n + (k + 1) % n, (i + 1) * n + k))
    verts.append((0, 0, 0.12))
    faces += [(3 * n, 2 * n + k, 2 * n + (k + 1) % n) for k in range(n)]
    verts.append((0, 0, 0.0))
    faces += [(3 * n + 1, (k + 1) % n, k) for k in range(n)]
    mk(kit, "paper cap", verts, faces, paper, cap, 1, W_SIL)
    lathe(kit, "cap band", [(1.0, 0.0), (1.035, 0.0), (1.04, 0.026), (1.005, 0.026)], kit.mat("shirt", SHIRT), cap,
          n=24, closed=True, sx=0.142, sy=0.144, ow=W_IN)


def build_player(kit, root):
    sk, shirt, pants = kit.mat("skin", SKIN), kit.mat("shirt", SHIRT), kit.mat("pants", PANTS)
    boot, sole, white = kit.mat("boot", BOOT), kit.mat("sole", SOLE), kit.mat("apron", WHITE)
    # chunky boots and tapered legs
    for s in (1, -1):
        x = 0.19 * s
        tube(kit, f"boot {s}", [(x, 0.012, 0.25), (x, 0.016, 0.13), (x, -0.06, 0.08), (x, -0.2, 0.08)],
             [0.066, 0.078, (0.09, 0.075), (0.092, 0.07)], boot, root, n=12, ref=X, ow=W_SIL)
        tube(kit, f"sole {s}", [(x, 0.085, 0.024), (x, -0.06, 0.024), (x, -0.235, 0.026)], [(0.082, 0.024), (0.094, 0.025),
             (0.096, 0.026)], sole, root, n=10, ref=X, dome=0.9, ow=W_MID)
        tube(kit, f"leg {s}", [(0.095 * s, 0, 0.84), (0.15 * s, -0.025, 0.5), (0.185 * s, 0.01, 0.29),
                               (0.19 * s, 0.012, 0.22)], [0.1, 0.072, 0.07, 0.078], pants, root, ow=W_SIL)
    tube(kit, "hips", [(0, 0.0, 0.68), (0, 0, 0.8), (0, 0, 0.92)], [(0.15, 0.115), (0.158, 0.12), (0.142, 0.11)],
         pants, root, n=12, ow=W_SIL)
    # V-shaped torso: broad shoulders, pinched waist
    TOR = [(0.86, 0.14, 0.105), (0.95, 0.118, 0.095), (1.06, 0.185, 0.12), (1.16, 0.255, 0.132), (1.24, 0.262, 0.125),
           (1.305, 0.16, 0.095)]
    tube(kit, "torso", [(0, 0, z) for z, _, _ in TOR], [(w, d) for _, w, d in TOR], shirt, root, n=12, subsurf=2,
         dome=0.35, ow=W_SIL)

    def prof(z):
        for (z0, w0, d0), (z1, w1, d1) in zip(TOR, TOR[1:]):
            if z <= z1:
                t = max(0.0, (z - z0) / (z1 - z0))
                return w0 + (w1 - w0) * t, d0 + (d1 - d0) * t
        return TOR[-1][1], TOR[-1][2]

    def front(x, z, pad):
        w, d = prof(z)
        return Vector((x, -d * math.sqrt(max(0.05, 1 - (x / w) ** 2)) - pad, z))
    tube(kit, "neck", [(0, 0, 1.22), (0, -0.01, 1.37)], [0.062, 0.058], sk, root, ow=W_MID)
    # apron: two-layer slab hugging the bib, flaring over the hips
    rows = [(1.13, 0.215, 0.13, 32), (1.0, 0.152, 0.11, 36), (0.93, 0.13, 0.1, 82), (0.86, 0.148, 0.118, 82),
            (0.72, 0.172, 0.135, 80), (0.56, 0.2, 0.15, 76)]
    cols = 9
    verts, faces = [], []
    for layer, k in ((0, 1.1), (1, 1.03)):
        for z, w, d, ang in rows:
            for j in range(cols):
                a = math.radians(-ang + 2 * ang * j / (cols - 1))
                verts.append((math.sin(a) * w * k, -math.cos(a) * d * k - (0.012 if layer == 0 else 0.0), z))
    R, C = len(rows), cols
    for layer in (0, 1):
        o = layer * R * C
        for i in range(R - 1):
            for j in range(C - 1):
                faces.append((o + i * C + j, o + i * C + j + 1, o + (i + 1) * C + j + 1, o + (i + 1) * C + j))
    for i in range(R - 1):
        for j in (0, C - 1):
            faces.append((i * C + j, (i + 1) * C + j, R * C + (i + 1) * C + j, R * C + i * C + j))
    for i in (0, R - 1):
        for j in range(C - 1):
            faces.append((i * C + j, i * C + j + 1, R * C + i * C + j + 1, R * C + i * C + j))
    mk(kit, "apron", verts, faces, white, root, 1, W_MID)
    tie = kit.mat("strap", STRAP)
    for s in (1, -1):
        pts = [front(0.072 * s, 1.11, 0.006), front(0.07 * s, 1.21, 0.012), (0.062 * s, -0.1, 1.29),
               (0.056 * s, -0.052, 1.35)]
        tube(kit, f"apron neck strap {s}", pts, [(0.016, 0.006)] * 4, white, root, n=8, ref=X, ow=W_IN)
    # pocket with an ice cream cone emblem
    pk = front(0.0, 0.76, 0.02)
    pocket = kit.empty("apron pocket", root, pk)
    oprim(kit, W_IN, "pocket", 'box', (0.17, 0.02, 0.1), white, pocket, offset=(0, -0.012, 0), bevel=0.006)
    emblem = kit.empty("emblem", pocket, (0.0, -0.023, 0.0), (90, 0, 0))
    flat_poly(kit, "emblem cone", [(-0.022, 0.012), (0.022, 0.012), (0.0, -0.035)], flat(kit, "cone", CONE), emblem,
              0.004, 0.003, -0.001)
    flat_poly(kit, "emblem scoop", ell(0, 0.022, 0.025, 0.02, 14), flat(kit, "pink", PINK), emblem, 0.004, 0.004,
              -0.001)
    # cooler backpack with spare pints poking out of the lid
    cool = kit.empty("cooler", root, (0, 0.255, 1.06))
    oprim(kit, W_SIL, "cooler box", 'box', (0.36, 0.22, 0.34), kit.mat("cooler", COOLER), cool, bevel=0.035)
    oprim(kit, W_IN, "cooler stripe", 'box', (0.37, 0.23, 0.05), white, cool, offset=(0, 0, -0.07), bevel=0.02)
    lid = kit.empty("cooler lid", cool, (0, 0.115, 0.17), (-24, 0, 0))
    oprim(kit, W_SIL, "lid", 'box', (0.38, 0.24, 0.055), white, lid, offset=(0, -0.115, 0.025), bevel=0.02)
    for i, (x, tilt, col) in enumerate(((-0.08, -14, PINK), (0.07, 10, CHOC), (0.0, 3, "#9be36a"))):
        pint = kit.empty(f"spare pint {i}", cool, (x, -0.03 + 0.02 * i, 0.12 + 0.02 * (i % 2)), (tilt, -tilt, 0))
        lathe(kit, "pint tub", [(0, 0), (0.042, 0), (0.05, 0.1), (0, 0.1)], white, pint, n=14, ow=W_IN)
        lathe(kit, "pint lid", [(0, 0.095), (0.054, 0.095), (0.054, 0.12), (0, 0.12)], kit.mat(f"lid{i}", col), pint,
              n=14, ow=W_IN)
        lathe(kit, "pint label", [(0.047, 0.035), (0.0485, 0.035), (0.0495, 0.065), (0.0475, 0.065)],
              kit.mat(f"lid{i}", col), pint, n=14, closed=True)
    for s in (1, -1):
        x = 0.135 * s
        pts = [(0.11 * s, 0.14, 1.24), (x, 0.06, 1.325), (x, -0.03, 1.305), front(x, 1.2, 0.012),
               front(0.13 * s, 1.08, 0.012), front(0.12 * s, 1.0, 0.012)]
        tube(kit, f"backpack strap {s}", pts, [(0.024, 0.008)] * len(pts), tie, root, n=8, ref=X, ow=W_IN)
    # right arm (-X) up and aiming, sleeve puffed
    S, E, Wr = Vector((-0.25, 0, 1.21)), Vector((-0.32, -0.22, 1.18)), Vector((-0.27, -0.44, 1.23))
    tube(kit, "sleeve R", [(-0.19, 0, 1.24), S, lerp(S, E, 0.45)], [0.07, 0.088, 0.084], shirt, root, ow=W_SIL)
    tube(kit, "arm R", [S, lerp(S, E, 0.5), E, lerp(E, Wr, 0.5), Wr], [0.072, 0.066, 0.054, 0.046, 0.04], sk, root,
         ow=W_SIL)
    fc = Wr + Vector((0.0, -0.045, -0.01))
    fist = kit.empty("fist R", root, fc)
    player_fist(kit, fist, False)
    gun = kit.empty("held gun", root, fc + Vector((0.0, -0.085, 0.096)), (0, 0, 2), (1.3, 1.3, 1.3))
    build_gun(kit, gun)
    # left arm (+X): thumbs up
    S, E, Wr = Vector((0.25, 0, 1.21)), Vector((0.43, 0.04, 1.0)), Vector((0.45, -0.03, 1.22))
    tube(kit, "sleeve L", [(0.19, 0, 1.24), S, lerp(S, E, 0.42)], [0.07, 0.088, 0.084], shirt, root, ow=W_SIL)
    tube(kit, "arm L", [S, lerp(S, E, 0.5), E, lerp(E, Wr, 0.5), Wr], [0.072, 0.066, 0.054, 0.046, 0.04], sk, root,
         ow=W_SIL)
    fist = kit.empty("fist L", root, Wr + Vector((0, -0.01, 0.055)), (0, 0, 12))
    player_fist(kit, fist, True)
    hp = kit.empty("head pivot", root, (0, -0.01, 1.36), (4, 0, 20))
    player_head(kit, hp)


# ------------------------------------------------------------------ zombie
def zombie_hand(kit, parent, side):
    """Long knuckly hand, local space: wrist at origin, fingers hanging toward -Z, front is -Y."""
    sk = kit.mat("zskin", ZSKIN)
    blob(kit, "palm", (0, 0, -0.05), (0.024, 0.045, 0.056), sk, parent, ow=W_MID)
    for i, y in enumerate((-0.03, 0.0, 0.03)):
        k = Vector((0.004 * side, y, -0.098))
        blob(kit, f"knuckle {i}", k, (0.019, 0.017, 0.017), sk, parent, seg=12, rings=8, ow=W_IN)
        L = 0.075 + 0.015 * (i == 1)
        curl = 0.02 + 0.01 * i
        tube(kit, f"finger {i}", [k, k + Vector((0, -0.005, -L * 0.55)), k + Vector((-curl * side, -0.015, -L))],
             [0.012, 0.011, 0.008], sk, parent, n=8, ow=W_IN)
    tube(kit, "thumb", [(0.0, -0.035, -0.035), (-0.012 * side, -0.06, -0.06), (-0.02 * side, -0.065, -0.085)],
         [0.013, 0.012, 0.009], sk, parent, n=8, ow=W_IN)


def zombie_arm(kit, parent, side, S, E, Wr, pabs, name):
    """Overlong noodle arm with torn sleeve. Built on a shoulder pivot; returns the pivot."""
    sk, shirt = kit.mat("zskin", ZSKIN), kit.mat("zshirt", ZSHIRT)
    sp = piv(kit, name, parent, S, pabs)
    S, E, Wr = Vector(S), Vector(E), Vector(Wr)
    tube(kit, "arm", rel([S, lerp(S, E, 0.5), E, lerp(E, Wr, 0.5), Wr], S), [0.05, 0.04, 0.043, 0.032, 0.028],
         sk, sp, ow=W_SIL)
    tube(kit, "sleeve", rel([S - Vector((0.04 * side, 0, -0.02)), S, lerp(S, E, 0.3)], S), [0.062, 0.07, 0.066],
         shirt, sp, ow=W_MID)
    jag_band(kit, "sleeve rag", lerp(S, E, 0.3) - S, (E - S), 0.066, 0.066, 0.07, shirt, sp, n=10)
    hand = kit.empty("hand", sp)
    hand.matrix_basis = aim_matrix(Wr - S, (Wr - E).normalized())
    zombie_hand(kit, hand, side)
    return sp


def zombie_head(kit, hp, hit):
    sk = kit.mat("zskin", ZSKIN)
    hc, hr = Vector((0, -0.08, 0.06)), (0.125, 0.13, 0.142)

    def hfn(d):
        return 1 + 0.035 * math.sin(6 * d.x + 2) * math.cos(5 * d.y) + 0.06 * max(0.0, -d.z) * max(0.0, -d.y)
    blob(kit, "head", hc, hr, sk, hp, fn=hfn, seg=28, rings=16, ow=W_SIL)
    ink, white = flat(kit, "ink", INK), flat(kit, "white", "#ffffff")
    R = 0.13
    o = 0.006 / R
    # exposed brain popping out of a cracked skull
    bc, br = hc + Vector((0.01, 0.025, 0.095)), (0.098, 0.105, 0.062)

    def bfn(d):
        return 1 + 0.06 * math.sin(13 * d.x) * math.sin(11 * d.y + 1)
    blob(kit, "brain", bc, br, kit.mat("brain", BRAIN), hp, fn=bfn, ow=W_MID)
    bink = kit.mat("brain line", "#c4456f")
    for j in range(5):
        x0 = -0.6 + 0.3 * j
        pts = []
        for i in range(12):
            t = -0.75 + 1.5 * i / 11
            d = Vector((x0 + 0.08 * math.sin(t * 9 + j * 2), t, 1.0)).normalized()
            pts.append(bc + d * (surf_r(d, br, bfn) + 0.001))
        stroke(kit, f"brain fold {j}", pts, bink, hp, 0.0028)
    jag_band(kit, "skull crack", hc + Vector((0.01, 0.025, 0.088)), Z, 0.104, 0.112, 0.04, sk, hp, n=16, up=True,
             ow=W_MID, thick=0.01, flare=0.93)
    # bulging eye (+X side) and a tiny droopy one
    eu, ev = 0.38, 0.1
    ec = surf(hc, hr, hfn, eu, ev, 0.01)
    er = 0.056 if not hit else 0.064
    eye = blob(kit, "bulge eye", ec, (er, er, er), kit.mat("eyeball", "#fffbe8"), hp, ow=W_MID)
    look = -0.25 if not hit else 0.35
    decal(kit, "bulge pupil", ec, (er, er, er), None, ell(0.18 + look * 0.3, 0.05, 0.13, 0.13, 14), ink, hp, 0.002)
    vein = kit.mat("vein", "#e3262f")
    for i in range(3):
        a = 2.0 + i * 1.1
        pts = [ec + Vector((math.cos(a) * er * 0.9, -math.sin(a) * 0.1 * er, math.sin(a) * er * 0.9)) * 1.0]
        mid = Vector((math.cos(a) * 0.55, -0.85, math.sin(a) * 0.55)).normalized()
        pts.append(ec + mid * er * 1.01)
        stroke(kit, f"vein {i}", pts, vein, hp, 0.0018)
    decal(kit, "small eye ink", hc, hr, hfn, ell(-0.32, 0.12, 0.095, 0.07, 16), ink, hp, 0.004)
    decal(kit, "small eye", hc, hr, hfn, ell(-0.32, 0.11, 0.07, 0.045, 16), flat(kit, "yellow eye", "#fff59a"), hp,
          0.006)
    decal(kit, "small pupil", hc, hr, hfn, ell(-0.33, 0.1, 0.022, 0.022, 8), ink, hp, 0.008)
    decal(kit, "droopy lid", hc, hr, hfn, stroke_poly([(-0.44, 0.19), (-0.32, 0.17), (-0.2, 0.12)],
                                                      [0.025, 0.035, 0.02]), ink, hp, 0.009)
    decal(kit, "brow", hc, hr, hfn, stroke_poly([(-0.48, 0.28), (-0.3, 0.32), (-0.12, 0.27)], [0.03, 0.05, 0.035]),
          ink, hp, 0.006)
    decal(kit, "eye bag", hc, hr, hfn, stroke_poly([(-0.4, 0.0), (-0.32, -0.03), (-0.24, 0.0)], [0.01, 0.015, 0.01]),
          flat(kit, "bag", "#4f8a2c"), hp, 0.005)
    # stitches across the forehead
    st = [(-0.15 + 0.06 * i, 0.42 - 0.02 * i) for i in range(6)]
    decal(kit, "scar", hc, hr, hfn, stroke_poly(st, [0.012] * len(st)), ink, hp, 0.005)
    for i in range(1, 5):
        u, v = st[i]
        decal(kit, f"stitch {i}", hc, hr, hfn, stroke_poly([(u - 0.01, v + 0.05), (u + 0.01, v - 0.05)], [0.01, 0.01]),
              ink, hp, 0.006)
    # nostrils
    for s in (1, -1):
        decal(kit, f"nostril {s}", hc, hr, hfn, ell(0.05 * s, -0.12, 0.022, 0.03, 8), ink, hp, 0.005)
    # gaping mouth: dark cavity, crooked upper teeth, hanging jaw
    mc = surf(hc, hr, hfn, 0.04, -0.42, -0.03)
    blob(kit, "mouth cavity", mc, (0.07, 0.04, 0.045), kit.mat("mouth", MOUTH), hp, ow=W_IN)
    tw = kit.mat("teeth", "#fff6d0")
    for i, (u, tilt, h) in enumerate(((-0.25, 8, 0.026), (-0.08, -6, 0.032), (0.19, 14, 0.022))):
        p = surf(hc, hr, hfn, u, -0.3, -0.006)
        oprim(kit, 0.004, f"top tooth {i}", 'box', (0.02, 0.014, h), tw, hp, offset=p - Vector((0, 0, h * 0.4)), rot=(0, tilt, 0),
                 bevel=0.004, bevel_segments=2)
    jaw = kit.empty("jaw", hp, hc + Vector((0, 0.01, -0.06)), (28 if not hit else 42, 0, 0), )
    jaw.rotation_euler.y = math.radians(-14)
    jaw.rotation_euler.z = math.radians(8)
    jc = Vector((0, -0.105, -0.06))
    blob(kit, "jaw", jc, (0.08, 0.07, 0.036), sk, jaw, fn=lambda d: 1 + 0.15 * max(0.0, d.z), ow=W_MID)
    blob(kit, "tongue", jc + Vector((0.01, -0.005, 0.026)), (0.05, 0.045, 0.014), kit.mat("tongue", "#d9466b"), jaw,
         ow=W_IN)
    for i, (x, h) in enumerate(((-0.045, 0.024), (0.02, 0.03), (0.05, 0.02))):
        oprim(kit, 0.004, f"low tooth {i}", 'box', (0.018, 0.013, h), tw, jaw, offset=jc + Vector((x, -0.05, 0.03)),
                 rot=(0, (-1) ** i * 10, 0), bevel=0.004, bevel_segments=2)
    # one chewed ear
    blob(kit, "ear", surf(hc, hr, hfn, 1.45, 0.05, -0.012), (0.02, 0.03, 0.04), sk, hp, ow=W_MID)
    blob(kit, "ear stub", surf(hc, hr, hfn, -1.45, 0.0, -0.01), (0.015, 0.02, 0.022), sk, hp, ow=W_MID)


def ice_splat(kit, name, parent, c, normal, size, col=PINK):
    """Cartoon ice cream splat stuck to a surface: lumpy flattened glob, drips running down."""
    sp = kit.empty(name, parent, c)
    sp.matrix_basis = Matrix.Translation(Vector(c)) @ Vector(normal).to_track_quat('-Y', 'Z').to_matrix().to_4x4()
    m = kit.mat(name, col)
    blob(kit, "glob", (0, 0, 0), (size, size * 0.35, size * 0.85), m, sp,
         fn=lambda d: 1 + 0.18 * math.sin(7 * math.atan2(d.z, d.x)), seg=24, rings=12, ow=W_MID)
    for i, (x, L) in enumerate(((-0.45, 1.3), (0.2, 1.8), (0.6, 1.0))):
        top = Vector((x * size, -0.1 * size, -0.4 * size))
        tube(kit, f"drip {i}", [top, top + Vector((0, 0.05 * size, -L * size))], [0.22 * size, 0.18 * size], m, sp, n=8,
             dome=1.0, ow=W_IN)
    blob(kit, "shine", (-0.3 * size, -0.36 * size, 0.3 * size), (0.18 * size, 0.04 * size, 0.12 * size),
         flat(kit, "white", "#ffffff"), sp, seg=10, rings=6)
    return sp


def build_zombie(kit, root, hit=False):
    sk, shirt, pants = kit.mat("zskin", ZSKIN), kit.mat("zshirt", ZSHIRT), kit.mat("zpants", ZPANTS)
    # legs: lanky, knock-kneed, torn at the shin, bare splayed feet
    legs = (("leg R", -1, (-0.1, 0.04, 0.88), (-0.085, -0.1, 0.47), (-0.17, 0.0, 0.09), -18),
            ("leg L", 1, (0.1, 0.04, 0.88), (0.035, -0.07, 0.48), (0.19, 0.07, 0.09), 26))
    for name, s, H, K, A, yaw in legs:
        lp = piv(kit, name, root, H)
        H, K, A = Vector(H), Vector(K), Vector(A)
        cuff = lerp(K, A, 0.3)
        tube(kit, "thigh", rel([H, lerp(H, K, 0.5), K, cuff], H), [0.078, 0.066, 0.058, 0.062], pants, lp, ow=W_SIL)
        jag_band(kit, "pant rag", cuff - H, A - K, 0.062, 0.062, 0.065, pants, lp, n=12)
        tube(kit, "shin", rel([K, A + Vector((0, 0, 0.0))], H), [0.04, 0.03], sk, lp, ow=W_SIL)
        foot = kit.empty("foot", lp, A - H, (0, 0, yaw))
        blob(kit, "foot", (0, -0.06, -0.045), (0.05, 0.11, 0.042), sk, foot,
             fn=lambda d: 1 + 0.1 * max(0.0, -d.y), ow=W_SIL)
        for i, x in enumerate((-0.03, 0.0, 0.03)):
            blob(kit, f"toe {i}", (x, -0.165, -0.06), (0.017, 0.022, 0.02), sk, foot, seg=10, rings=6, ow=W_IN)
    # question-mark spine
    hips = piv(kit, "hips", root, (0, 0.03, 0.9))
    tube(kit, "pants hips", rel([(0, 0.03, 0.76), (0, 0.03, 0.88), (0, 0.05, 0.98)], (0, 0.03, 0.9)),
         [(0.14, 0.11), (0.148, 0.118), (0.142, 0.122)], pants, hips, ow=W_SIL, n=12)
    spine = piv(kit, "spine", hips, (0, 0.03, 0.92), (0, 0.03, 0.9))
    SP = [(0, 0.03, 0.88), (0, 0.09, 1.04), (0, 0.125, 1.2), (0, 0.085, 1.35), (0, -0.03, 1.42)]
    RAD = [(0.13, 0.105), (0.125, 0.115), (0.16, 0.13), (0.19, 0.12), (0.11, 0.085)]
    so = (0, 0.03, 0.92)
    tube(kit, "belly", rel(SP[:3], so), RAD[:3], sk, spine, n=12, ow=W_SIL)
    tube(kit, "shirt", rel([(0, 0.06, 1.03)] + SP[2:], so), [(0.138, 0.125)] + [(a * 1.06, b * 1.06) for a, b in RAD[2:]],
         shirt, spine, n=12, subsurf=2, dome=0.35, ow=W_SIL)
    jag_band(kit, "shirt hem", Vector((0, 0.085, 1.05)) - Vector(so), (0, 0.3, 1), 0.142, 0.13, 0.08, shirt, spine,
             n=18, ow=W_MID)
    tube(kit, "neck", rel([(0, 0.0, 1.37), (0, -0.11, 1.39)], so), [0.054, 0.048], sk, spine, ow=W_MID)
    ice_splat(kit, "chest splat", spine, Vector((-0.075, -0.005, 1.22)) - Vector(so), (0.25, -1, 0.1), 0.06, PINK)
    # hanging head and dragging arms
    hp = piv(kit, "head pivot", spine, (0, -0.11, 1.39), so)
    hp.rotation_euler = [math.radians(a) for a in ((-6, 14, 10) if not hit else (-16, -12, 20))]
    zombie_head(kit, hp, hit)
    SR, SL = (-0.19, 0.06, 1.34), (0.19, 0.06, 1.34)
    arm_r = zombie_arm(kit, spine, -1, SR, (-0.26, 0.02, 0.98), (-0.24, -0.06, 0.6), so, "arm R")
    if not hit:
        arm_l = zombie_arm(kit, spine, 1, SL, (0.27, -0.1, 1.02), (0.26, -0.28, 0.7), so, "arm L")
        spine.rotation_euler = [math.radians(a) for a in (17, 0, 0)]
        arm_r.rotation_euler = [math.radians(a) for a in (-17, 0, 0)]
        arm_l.rotation_euler = [math.radians(a) for a in (-12, 0, 4)]
        return
    # ---- hit pose: recoil, flailing right arm, left arm blown off
    spine.rotation_euler = [math.radians(a) for a in (-14, 6, 16)]
    hips.rotation_euler = [math.radians(a) for a in (-4, 0, 6)]
    arm_r.rotation_euler = [math.radians(a) for a in (0, 96, -12)]
    stump_local = Vector(SL) - Vector(so)
    stump = kit.empty("stump", spine, stump_local)
    bpy.context.view_layer.update()
    H = stump.matrix_world.translation.copy()
    L = root.matrix_world.inverted()
    blood, flatw = kit.mat("blood", BLOOD), flat(kit, "white", "#ffffff")
    # stump: ragged red cap and a cartoon bone nub
    blob(kit, "stump gore", (0.03, 0, 0), (0.06, 0.07, 0.07), blood, stump,
         fn=lambda d: 1 + 0.25 * math.sin(6 * math.atan2(d.z, d.y)) * max(0.0, d.x), ow=W_MID)
    bone = kit.mat("bone", "#fff8e8")
    tube(kit, "stump bone", [(0.04, 0, 0), (0.1, -0.01, 0.01)], [0.018, 0.016], bone, stump, n=8, ow=W_IN)
    for s in (1, -1):
        blob(kit, f"bone knob {s}", (0.11, -0.01, 0.01 + 0.014 * s), (0.017, 0.017, 0.017), bone, stump, seg=12,
             rings=8, ow=W_IN)
    cam = IMPACT_CAM
    T = (cam - H).normalized()
    Rv = T.cross(Z).normalized() * -1
    if Rv.x < 0:
        Rv = -Rv
    U = Rv.cross(T).normalized() * -1
    if U.z < 0:
        U = -U

    def place(ob, mw):
        ob.matrix_basis = L @ mw

    def bill(p, track='Z', up='Y'):
        return Matrix.Translation(p) @ (cam - p).to_track_quat(track, up).to_matrix().to_4x4()
    # flying arm, tumbling, 0.5 m out toward camera-right and up
    F = H + Vector((0.34, -0.17, 0.33))
    fly = kit.empty("flying arm pivot", root)
    place(fly, Matrix.Translation(F) @ Euler((math.radians(25), math.radians(-128), math.radians(35))).to_matrix().to_4x4())
    S0 = Vector((0.19, 0.02, 1.36))
    zombie_arm(kit, fly, 1, S0, (0.27, -0.12, 1.02), (0.22, -0.2, 0.66), S0, "arm L (flying)")
    blob(kit, "arm gore", (0, 0, 0.0), (0.055, 0.055, 0.05), blood, fly,
         fn=lambda d: 1 + 0.25 * math.sin(6 * math.atan2(d.y, d.x)) * max(0.0, d.z), ow=W_MID)
    tube(kit, "arm bone", [(0, 0, -0.01), (0, -0.005, 0.06)], [0.016, 0.015], bone, fly, n=8, ow=W_IN)
    for s in (1, -1):
        blob(kit, f"arm bone knob {s}", (0.013 * s, -0.005, 0.07), (0.016, 0.016, 0.016), bone, fly, seg=12, rings=8,
             ow=W_IN)
    # comic starburst behind the hit point with SPLAT! lettering
    sc = H - T * 0.45 + Rv * 0.12 + U * 0.05
    burst = kit.empty("burst", root)
    place(burst, bill(sc, '-Y', 'Z'))
    for nm, pts, ro, ri, col, dy, sca, rot in (("burst ink", 13, 0.78, 0.46, INK, 0.012, 1.0, 0),
                                               ("burst", 13, 0.72, 0.42, STAR, 0.0, 1.0, 0),
                                               ("burst inner ink", 11, 0.47, 0.3, INK, -0.006, 1.0, 9),
                                               ("burst inner", 11, 0.44, 0.27, "#ffffff", -0.012, 1.0, 9)):
        me = star_mesh(nm, pts, ro, ri)
        me.materials.append(flat(kit, nm, col))
        kit.link(nm, me, burst, (0, dy, 0), (0, rot, 0))
    font = bpy.data.fonts.load("/usr/share/fonts/noto/NotoSans-BlackItalic.ttf", check_existing=True)
    tp = kit.empty("splat text", root)
    place(tp, bill(H + U * 0.62 - Rv * 0.42 + T * 0.15) @ Matrix.Rotation(math.radians(8), 4, 'Z'))
    for nm, col, off, dz in (("txt ink", INK, 0.022, -0.006), ("txt", "#ff4fa0", 0.0, 0.0)):
        cu = bpy.data.curves.new(nm, 'FONT')
        cu.body = "SPLAT!"
        cu.font = font
        cu.size = 0.27
        cu.align_x = 'CENTER'
        cu.align_y = 'CENTER'
        cu.offset = off
        cu.materials.append(flat(kit, nm, col))
        kit.link(nm, cu, tp, (0, 0, dz))
    # speed lines radiating from the hit and spin arcs around the flying arm
    inkm = flat(kit, "ink", INK)
    for i in range(9):
        a = math.radians(-40 + 22 * i + kit.rand.uniform(-6, 6))
        dv = (Rv * math.cos(a) + U * math.sin(a)).normalized()
        r0, r1 = kit.rand.uniform(0.32, 0.42), kit.rand.uniform(0.62, 0.8)
        stroke(kit, f"speed line {i}", [L @ (H + dv * r0 + T * 0.1), L @ (H + dv * r1 + T * 0.1)], inkm, root, 0.009,
               [1.0, 0.15])
    ac = F + Vector((0.08, -0.05, -0.06))
    for j, (r, a0, a1) in enumerate(((0.3, 100, 200), (0.36, 115, 185), (0.3, 280, 350))):
        pts = [L @ (ac + (Rv * math.cos(math.radians(a)) + U * math.sin(math.radians(a))) * r + T * 0.05)
               for a in [a0 + (a1 - a0) * k / 10 for k in range(11)]]
        stroke(kit, f"spin arc {j}", pts, inkm, root, 0.008, [0.2 + 0.8 * math.sin(math.pi * k / 10) for k in range(11)])
    # big outlined blood blobs and ice cream chunks with white highlight drops
    D0 = (Rv * 0.75 + U * 0.55 + T * 0.25).normalized()
    hl = (T * 0.8 + U * 0.5 - Rv * 0.3).normalized()
    chunks = [(BLOOD, 16), (PINK, 6), (VANILLA, 5), (CHOC, 4)]
    for col, count in chunks:
        m = kit.mat("fx " + col, col)
        for i in range(count):
            dv = (D0 + Vector((kit.rand.uniform(-1, 1), kit.rand.uniform(-0.6, 0.6), kit.rand.uniform(-0.7, 0.9))) * 0.75).normalized()
            dist = kit.rand.uniform(0.2, 0.85)
            p = H + dv * dist - Z * 0.25 * dist * dist + T * 0.08
            r = kit.rand.uniform(0.022, 0.05) if col == BLOOD else kit.rand.uniform(0.03, 0.05)
            fx = kit.empty(f"fx {col} {i}", root)
            place(fx, Matrix.Translation(p))
            if col == BLOOD:
                q = (L.to_3x3() @ dv).normalized()
                tube(kit, "drop", [-q * r * 2.4, Vector((0, 0, 0))], [r * 0.22, r], m, fx, n=10, ow=0.0075)
            else:
                fn = (lambda d: 1 + 0.16 * math.sin(8 * math.atan2(d.y, d.x)) * max(0.0, -d.z) + 0.05)
                blob(kit, "scoop chunk", (0, 0, 0), (r, r, r * 0.85), m, fx, fn=fn, seg=18, rings=10, ow=0.0075)
            blob(kit, "highlight", (L.to_3x3() @ (hl * r * 0.62 + U * r * 0.15)), (r * 0.26, r * 0.26, r * 0.36), flatw,
                 fx, seg=10, rings=6)
    spr = ["#ff5fa2", "#ffe14d", "#4fc3ff", "#ffffff", "#7be36a"]
    for i in range(18):
        dv = (D0 + Vector((kit.rand.uniform(-1, 1), kit.rand.uniform(-0.5, 0.5), kit.rand.uniform(-0.8, 1))) * 0.9).normalized()
        p = H + dv * kit.rand.uniform(0.2, 0.75) + T * 0.1
        a = Vector((kit.rand.uniform(-1, 1), kit.rand.uniform(-1, 1), kit.rand.uniform(-1, 1))).normalized() * 0.018
        lp = L @ p
        la = L.to_3x3() @ a
        tube(kit, f"sprinkle {i}", [lp - la, lp + la], [0.008, 0.008], kit.mat("spr" + spr[i % 5], spr[i % 5]), root,
             n=6, dome=1.0, ow=0.004)
    # splats on the floor
    floor = kit.empty("floor splats", root)
    place(floor, Matrix.Translation(Vector((H.x, H.y, 0.003))))
    for i, (dx, dy, r, col) in enumerate(((0.25, -0.15, 0.24, BLOOD), (0.55, -0.35, 0.14, PINK), (-0.1, -0.35, 0.12, BLOOD),
                                          (0.45, 0.1, 0.1, VANILLA), (0.75, -0.1, 0.06, BLOOD), (0.1, -0.55, 0.05, BLOOD))):
        n = 22
        pts = []
        for k in range(n):
            a = 2 * math.pi * k / n
            rr = r * (1 + (0.32 if k % 3 == 0 else 0.0) * kit.rand.uniform(0.4, 1.0) + kit.rand.uniform(-0.06, 0.06))
            pts.append((dx + math.cos(a) * rr, dy + math.sin(a) * rr * 0.85))
        flat_poly(kit, f"floor splat {i}", pts, kit.mat("fx " + col, col), floor, 0.012, 0.002 * (i + 1), -0.0015)
        flat_poly(kit, f"floor shine {i}", ell(dx - r * 0.3, dy + r * 0.25, r * 0.22, r * 0.1, 10, 0.4), flatw, floor,
                  0.0, 0.002 * (i + 1) + 0.001)


# ------------------------------------------------------------------ gun
def build_gun(kit, root):
    orange, teal = kit.mat("gun orange", ORANGE), kit.mat("gun teal", TEAL)
    choc, white = kit.mat("choc", CHOC), kit.mat("tub", WHITE)
    inkm = flat(kit, "ink", INK)
    # fat bulbous body, rear heavier than nose
    tube(kit, "gun body", [(0, 0.105, 0.002), (0, 0.075, 0.004), (0, 0.03, 0.0), (0, -0.03, -0.002), (0, -0.078, 0.0)],
         [(0.032, 0.034), (0.042, 0.048), (0.038, 0.043), (0.031, 0.035), (0.028, 0.031)], orange, root, n=12,
         subsurf=2, ref=X, dome=0.7, ow=0.005)
    tube(kit, "gun collar", [(0, -0.066, 0), (0, -0.096, 0)], [0.037, 0.037], teal, root, n=14, dome=0.15, ow=0.004)
    tube(kit, "rear knob", [(0, 0.11, 0.002), (0, 0.13, 0.002)], [0.022, 0.022], teal, root, n=12, dome=0.3, ow=0.004)
    stroke(kit, "body shine", [(0.02, 0.1, 0.03), (0.026, 0.085, 0.038), (0.027, 0.064, 0.038)],
           flat(kit, "white", "#ffffff"), root, 0.004, [0.4, 1.0, 0.5])
    stroke(kit, "nose shine", [(0.019, -0.025, 0.028), (0.019, -0.055, 0.025)], flat(kit, "white", "#ffffff"), root,
           0.0035, [1.0, 0.4])
    for i, y in enumerate((0.075, 0.055, 0.035)):
        blob(kit, f"vent {i}", (0.037, y, -0.012), (0.004, 0.006, 0.012), inkm, root, seg=8, rings=6)
    # flared waffle-cone muzzle with diamond grid and a loaded scoop inside
    prof = [(0.026, -0.088), (0.034, -0.11), (0.05, -0.15), (0.068, -0.197), (0.072, -0.203), (0.066, -0.209),
            (0.058, -0.2), (0.024, -0.115)]
    lathe(kit, "waffle cone", prof, cone, root, axis='Y', n=20, closed=True, ow=0.005)

    def cone_r(y):
        for (r0, y0), (r1, y1) in zip(prof, prof[1:4]):
            if y1 <= y <= y0:
                return r0 + (r1 - r0) * (y - y0) / (y1 - y0)
        return prof[3][0]
    line = kit.mat("waffle line", "#9c5a23")
    for k in range(8):
        for sgn in (1, -1):
            pts = []
            for i in range(9):
                t = i / 8
                y = -0.1 - 0.094 * t
                a = 2 * math.pi * k / 8 + sgn * t * 1.3
                r = cone_r(y) + 0.0012
                pts.append((r * math.cos(a), y, r * math.sin(a)))
            stroke(kit, f"waffle {k} {sgn}", pts, line, root, 0.0014)
    blob(kit, "muzzle scoop", (0, -0.19, 0.0), (0.05, 0.03, 0.05), kit.mat("pink scoop", PINK), root,
         fn=lambda d: 1 + 0.08 * math.sin(6 * math.atan2(d.z, d.x)), ow=0.004)
    # pint-tub magazine with a chocolate scoop and sprinkles
    tc = Vector((0, 0.018, 0.034))
    tube(kit, "tub mount", [(0, 0.018, 0.02), (0, 0.018, 0.045)], [0.024, 0.024], orange, root, n=12, ow=0.003)
    lathe(kit, "pint tub", [(0, 0), (0.027, 0), (0.03, 0.004), (0.035, 0.05), (0.037, 0.053), (0.037, 0.057), (0, 0.057)],
          white, root, center=tc, n=18, ow=0.004)
    lathe(kit, "tub label", [(0.0315, 0.016), (0.0338, 0.016), (0.0353, 0.036), (0.0328, 0.036)], teal, root,
          center=tc, n=18, closed=True)
    scc, scr = tc + Vector((0, 0, 0.062)), (0.037, 0.037, 0.031)

    def sfn(d):
        return 1 + 0.08 * math.sin(7 * math.atan2(d.y, d.x)) * max(0.0, 0.4 - d.z)
    blob(kit, "choc scoop", scc, scr, choc, root, fn=sfn, ow=0.004)
    for i, a in enumerate((0.6, 2.4)):
        top = scc + Vector((math.cos(a) * 0.039, math.sin(a) * 0.039, -0.018))
        tube(kit, f"choc drip {i}", [top, top + Vector((math.cos(a) * -0.002, math.sin(a) * -0.002, -0.016 - 0.008 * i))],
             [0.0065, 0.0075], choc, root, n=8, dome=1.0, ow=0.0025)
    spr = ["#ff5fa2", "#ffe14d", "#4fc3ff", "#ffffff", "#7be36a"]
    for i in range(16):
        u = kit.rand.uniform(0, 2 * math.pi)
        v = kit.rand.uniform(0.25, 1.35)
        d = Vector((math.cos(u) * math.cos(v), math.sin(u) * math.cos(v), math.sin(v)))
        p = scc + d * (surf_r(d, scr, sfn) + 0.001)
        t = d.cross(Vector((kit.rand.uniform(-1, 1), kit.rand.uniform(-1, 1), kit.rand.uniform(-1, 1)))).normalized()
        tube(kit, f"sprinkle {i}", [p - t * 0.005, p + t * 0.005], [0.0022, 0.0022],
             kit.mat("spr" + spr[i % 5], spr[i % 5]), root, n=6, dome=1.0, subsurf=0)
    # chunky raked grip, trigger guard, trigger
    tube(kit, "grip", [(0, 0.058, -0.015), (0, 0.072, -0.07), (0, 0.088, -0.118), (0, 0.092, -0.132)],
         [(0.019, 0.027), (0.02, 0.028), (0.023, 0.031), (0.021, 0.029)], teal, root, n=12, ref=X, dome=0.4, ow=0.005)
    tube(kit, "trigger guard", [(0, -0.03, -0.022), (0, -0.036, -0.058), (0, -0.012, -0.078), (0, 0.025, -0.077),
                                (0, 0.055, -0.06)], [0.0058] * 5, orange, root, n=8, ow=0.003)
    tube(kit, "trigger", [(0, 0.0, -0.025), (0, -0.01, -0.045), (0, -0.004, -0.06)], [0.006, 0.0055, 0.005],
         kit.mat("trigger", SHIRT), root, n=8, ow=0.003)
    tube(kit, "front sight", [(0, -0.06, 0.025), (0, -0.07, 0.042)], [(0.006, 0.01), (0.005, 0.008)], teal, root, n=8,
         ow=0.003)
