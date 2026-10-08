"""Style B: faceted low poly. Lanky hand-placed cage meshes, hard flat facets, grimy muted palette with ice cream pops."""
from common import *
import subprocess

KEY = "B"
LABEL = "Faceted low poly"
SHADER = 'facet'
WORLD = "#2a2f37"
FLOOR = "#3a4048"

C = dict(teal="#3f7f7c", denim="#2f3b4f", apron="#d9d1bc", skin="#c99a7a", red="#c94a3f",
         zskin="#7f9a5e", zshirt="#8e7f62", zpants="#4a3c33", metal="#7a838e", pink="#ff4f7b", tape="#d8b03a",
         boot="#4a3a2c", sole="#211e1c", hair="#33271f", dark="#17161a", mouth="#3a1418", bone="#d8cfb0",
         brain="#d98c9a", brain2="#b4606e", blood="#6e0f14", blood2="#9c1820", cream="#f2e6c8", choc="#5a3424",
         mint="#7fd8b8", waffle="#d29a55", waffle2="#9a6630", metal_d="#4a5058", dust="#b9b0a0", yeye="#e4da8a",
         strap="#2b2a2a", zrot="#5f7446", sprk_b="#5fb6ff")


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


def mt(kit, key):
    return kit.mat(key, C[key])


# ------------------------------------------------------------------ geometry helpers
def loft(rings, closed=True, cap0=True, cap1=True):
    """Connect rings of vertices with quads (or triangles to a single tip point). Returns (verts, faces, band)."""
    verts, faces, band, idx = [], [], [], []
    for r in rings:
        idx.append(list(range(len(verts), len(verts) + len(r))))
        verts.extend(tuple(p) for p in r)
    for s in range(len(rings) - 1):
        a, b = idx[s], idx[s + 1]
        if len(b) == 1:
            for i in range(len(a) if closed else len(a) - 1):
                faces.append([a[i], a[(i + 1) % len(a)], b[0]])
                band.append(s)
        elif len(a) == 1:
            for i in range(len(b) if closed else len(b) - 1):
                faces.append([a[0], b[(i + 1) % len(b)], b[i]])
                band.append(s)
        else:
            for i in range(len(a) if closed else len(a) - 1):
                j = (i + 1) % len(a)
                faces.append([a[i], a[j], b[j], b[i]])
                band.append(s)
    if cap0 and len(idx[0]) > 2:
        faces.append(list(reversed(idx[0])))
        band.append(-1)
    if cap1 and len(idx[-1]) > 2:
        faces.append(list(idx[-1]))
        band.append(len(rings) - 1)
    return verts, faces, band


def merge(*datas):
    verts, faces, band = [], [], []
    for v, f, b in datas:
        o = len(verts)
        verts += v
        faces += [[i + o for i in face] for face in f]
        band += b
    return verts, faces, band


def facet(kit, name, data, mats, parent, bandmat=None, mirror=False, loc=(0, 0, 0), rot=(0, 0, 0), solid=0.0):
    """Hand-placed faceted cage: kit.cage with no subdivision and flat shading, per-band materials."""
    verts, faces, band = data
    mats = mats if isinstance(mats, (list, tuple)) else [mats]
    ob = kit.cage(name, verts, faces, mats[0], parent, subsurf=0, smooth=False)
    me = ob.data
    assert len(me.polygons) == len(faces), name
    for m in mats[1:]:
        me.materials.append(m)
    if bandmat is not None:
        me.polygons.foreach_set("material_index", [bandmat(b) for b in band])
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    if mirror:
        kit.mirror(ob)
    if solid:
        sol = ob.modifiers.new("Solid", 'SOLIDIFY')
        sol.thickness = solid
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    return ob


def jit(kit, ring, amt):
    out = []
    for x, y, z in ring:
        dx = 0 if abs(x) < 1e-6 else kit.rand.uniform(-amt, amt)
        out.append((x + dx, y + kit.rand.uniform(-amt, amt), z + kit.rand.uniform(-amt, amt) * 0.6))
    return out


def limb(kit, secs, n=6, twist=0.5, jitter=0.07):
    """Rings along -Z. sec = (z, rx, ry[, cx, cy[, jag]]); rx == 0 makes a tip point."""
    rings = []
    for k, s in enumerate(secs):
        z, rx, ry = s[0], s[1], s[2]
        cx = s[3] if len(s) > 3 else 0.0
        cy = s[4] if len(s) > 4 else 0.0
        jag = s[5] if len(s) > 5 else 0.0
        if rx == 0:
            rings.append([(cx, cy, z)])
            continue
        ph = (k % 2) * math.pi / n * twist + kit.rand.uniform(-0.12, 0.12)
        ring = []
        for i in range(n):
            a = ph + 2 * math.pi * i / n
            f = 1 + kit.rand.uniform(-jitter, jitter)
            dz = (jag if i % 2 else -jag * 0.6) * kit.rand.uniform(0.5, 1.0) if jag else kit.rand.uniform(-0.003, 0.003)
            ring.append((cx + rx * f * math.cos(a), cy + ry * f * math.sin(a), z + dz))
        rings.append(ring)
    return rings


def torso_prof(w, df, db, yo=0.0, blade=0.0):
    return [(0, yo - df), (w * 0.6, yo - df * 0.93), (w, yo - df * 0.2), (w * 0.94, yo + db * 0.5),
            (w * 0.55, yo + db * 0.95 + blade), (0, yo + db)]


def hring(pts, z):
    return [(x, y, z) for x, y in pts]


def full_ring(half, z, grow=0.0):
    pts = half + [(-x, y) for x, y in reversed(half[1:-1])]
    cy = sum(p[1] for p in pts) / len(pts)
    out = []
    for x, y in pts:
        d = Vector((x, y - cy))
        d = d.normalized() * grow if d.length > 1e-6 else Vector((0, 0))
        out.append((x + d.x, y + d.y, z))
    return out


def slab(profile, hw, ch):
    """Profile polygon in YZ extruded to +X with a chamfer; mirror it for the other side."""
    cy = sum(p[0] for p in profile) / len(profile)
    cz = sum(p[1] for p in profile) / len(profile)
    a = [(0, y, z) for y, z in profile]
    b = [(hw - ch, y, z) for y, z in profile]
    c = []
    for y, z in profile:
        d = Vector((cy - y, cz - z))
        d = d.normalized() * min(ch, d.length * 0.5)
        c.append((hw, y + d.x, z + d.y))
    return loft([a, b, c], cap0=False, cap1=True)


def strip(path, w, t, side=(1, 0, 0)):
    rings = []
    n = len(path)
    sv = Vector(side)
    for i, p in enumerate(path):
        p = Vector(p)
        d = (Vector(path[min(i + 1, n - 1)]) - Vector(path[max(i - 1, 0)])).normalized()
        s = (sv - d * sv.dot(d)).normalized()
        nr = d.cross(s).normalized()
        rings.append([tuple(p + s * w / 2 + nr * t / 2), tuple(p - s * w / 2 + nr * t / 2),
                      tuple(p - s * w / 2 - nr * t / 2), tuple(p + s * w / 2 - nr * t / 2)])
    return loft(rings)


def surf_y(levels, x, z):
    """Front surface y of a mirrored half-ring head at (x, z), linear between hand-placed points."""
    def y_at(pts, ax):
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            if x0 <= ax <= x1 and x1 > x0:
                return y0 + (y1 - y0) * (ax - x0) / (x1 - x0)
        return pts[2][1]
    for k in range(len(levels) - 1):
        za, pa = levels[k]
        zb, pb = levels[k + 1]
        if za <= z <= zb:
            t = (z - za) / (zb - za)
            return y_at(pa, abs(x)) * (1 - t) + y_at(pb, abs(x)) * t
    return levels[-1][1][0][1]


def decal(levels, polys, off):
    verts, faces = [], []
    for poly in polys:
        o = len(verts)
        verts += [(x, surf_y(levels, x, z) - off, z) for x, z in poly]
        faces.append(list(range(o, o + len(poly))))
    return verts, faces, [0] * len(faces)


def blob(kit, name, mat, parent, pos, r, squash=(1, 1, 1), subdiv=1, rough=0.25, rot=None):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1)
    for v in bm.verts:
        f = 1 + kit.rand.uniform(-rough, rough)
        v.co = Vector((v.co.x * r * squash[0] * f, v.co.y * r * squash[1] * f, v.co.z * r * squash[2] * f))
    ob = kit.mesh_from_bmesh(name, bm, mat, parent, Vector(pos), smooth=False)
    ob.rotation_euler = rot if rot is not None else [kit.rand.uniform(0, 6.28) for _ in range(3)]
    return ob


def chunk(kit, name, mat, parent, pos, s):
    v = [(x * s * kit.rand.uniform(0.6, 1.3), y * s * kit.rand.uniform(0.6, 1.3), z * s * kit.rand.uniform(0.5, 1.2))
         for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    f = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    ob = facet(kit, name, (v, f, [0] * 6), mat, parent, loc=pos)
    ob.rotation_euler = [kit.rand.uniform(0, 6.28) for _ in range(3)]
    return ob


def shard(kit, name, mat, parent, pos, d, length, width):
    ring = []
    a0 = kit.rand.uniform(0, 1.5)
    for i in range(4):
        a = a0 + i * math.pi / 2
        r = width * kit.rand.uniform(0.6, 1.25)
        ring.append((r * math.cos(a), r * math.sin(a), length * kit.rand.uniform(0.2, 0.4)))
    data = loft([[(0, 0, -length * 0.15)], ring, [(0, 0, length)]])
    ob = facet(kit, name, data, mat, parent)
    q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
    ob.matrix_basis = Matrix.Translation(Vector(pos)) @ q.to_matrix().to_4x4()
    return ob


def splat(kit, name, mat, parent, pos, r, n=9, jag=0.5, z=0.003):
    pts = [(0, 0, z + 0.004)]
    for i in range(n):
        a = 2 * math.pi * i / n + kit.rand.uniform(-0.25, 0.25)
        rr = r * (kit.rand.uniform(0.8, 1.25) if i % 2 == 0 else 1 - jag * kit.rand.uniform(0.4, 1.0))
        pts.append((rr * math.cos(a), rr * math.sin(a), z))
    faces = [[0, 1 + i, 1 + (i + 1) % n] for i in range(n)]
    ob = facet(kit, name, (pts, faces, [0] * n), mat, parent, loc=(pos[0], pos[1], 0))
    ob.rotation_euler = (0, 0, kit.rand.uniform(0, 6.28))
    return ob


def chain(ob, root):
    m = Matrix.Identity(4)
    while ob is not root:
        m = ob.matrix_basis @ m
        ob = ob.parent
    return m


def foot(kit, name, parent, mats, h, L, w, bare=False):
    """Boxy faceted boot/foot (mirrored), ankle pivot at origin, sole at -h."""
    R = [(-h, [(0, -L), (w * 0.85, -L * 0.92), (w, -L * 0.18), (w * 0.92, L * 0.42), (0, L * 0.48)]),
         (-h + 0.028, [(0, -L * 1.03), (w * 0.9, -L * 0.95), (w * 1.05, -L * 0.18), (w * 0.97, L * 0.45), (0, L * 0.52)]),
         (-h + (0.05 if not bare else 0.04), [(0, -L * 0.9), (w * 0.86, -L * 0.8), (w * 0.98, -L * 0.12), (w * 0.92, L * 0.4), (0, L * 0.46)]),
         (-h + (0.1 if not bare else 0.075), [(0, -L * 0.4), (w * 0.85, -L * 0.36), (w * 0.95, 0.0), (w * 0.9, L * 0.36), (0, L * 0.42)]),
         (0.05, [(0, -w * 0.95), (w * 0.8, -w * 0.8), (w * 0.95, 0.0), (w * 0.8, w * 0.75), (0, w * 0.95)])]
    rings = [jit(kit, hring(p, z), 0.003) for z, p in R]
    return facet(kit, name, loft(rings, closed=False), mats, parent,
                 bandmat=lambda b: 1 if b in (-1, 0) else 0, mirror=True)


# ------------------------------------------------------------------ player
PH = [(-0.03, [(0, -0.04), (0.03, -0.035), (0.05, -0.01), (0.055, 0.02), (0.035, 0.045), (0, 0.05)]),
      (0.05, [(0, -0.05), (0.035, -0.04), (0.055, -0.01), (0.06, 0.03), (0.04, 0.06), (0, 0.065)]),
      (0.07, [(0, -0.108), (0.028, -0.1), (0.058, -0.05), (0.07, 0.02), (0.05, 0.07), (0, 0.08)]),
      (0.1, [(0, -0.112), (0.035, -0.103), (0.072, -0.042), (0.08, 0.03), (0.06, 0.085), (0, 0.095)]),
      (0.135, [(0, -0.136), (0.026, -0.106), (0.078, -0.062), (0.086, 0.02), (0.07, 0.09), (0, 0.105)]),
      (0.17, [(0, -0.112), (0.035, -0.098), (0.08, -0.064), (0.088, 0.02), (0.072, 0.095), (0, 0.11)]),
      (0.195, [(0, -0.11), (0.045, -0.106), (0.083, -0.07), (0.088, 0.02), (0.072, 0.095), (0, 0.11)]),
      (0.24, [(0, -0.096), (0.045, -0.089), (0.076, -0.055), (0.083, 0.02), (0.066, 0.086), (0, 0.096)]),
      (0.285, [(0, -0.05), (0.03, -0.045), (0.05, -0.02), (0.055, 0.02), (0.04, 0.05), (0, 0.055)])]


def player_arm(kit, name, parent, loc, rot, elbow_rot, wrist_rot, side):
    teal, skin = mt(kit, "teal"), mt(kit, "skin")
    sh = kit.empty(f"{name} shoulder", parent, loc, rot)
    up = limb(kit, [(0.05, 0.048, 0.046), (0.0, 0.064, 0.06), (-0.1, 0.057, 0.055), (-0.16, 0.06, 0.058, 0, 0, 0.006),
                    (-0.163, 0.043, 0.041), (-0.27, 0.039, 0.037), (-0.31, 0.035, 0.033)])
    facet(kit, f"{name} upper arm", loft(up), [teal, skin], sh, bandmat=lambda b: 0 if b in (-1, 0, 1, 2, 3) else 1)
    el = kit.empty(f"{name} elbow", sh, (0, 0, -0.29), elbow_rot)
    fo = limb(kit, [(0.02, 0.036, 0.034), (-0.06, 0.043, 0.038), (-0.18, 0.032, 0.028), (-0.25, 0.027, 0.023)])
    facet(kit, f"{name} forearm", loft(fo), skin, el)
    wr = kit.empty(f"{name} wrist", el, (0, 0, -0.245), wrist_rot)
    fist = limb(kit, [(0.01, 0.026, 0.022), (-0.03, 0.044, 0.034), (-0.075, 0.046, 0.043), (-0.1, 0.038, 0.034, 0, 0.004)],
                n=5, jitter=0.05)
    thumb = limb(kit, [(0.0, 0.012, 0.012), (-0.035, 0.011, 0.01), (-0.055, 0, 0)], n=4)
    thumb = [[(side * 0.03 + x * 0.7 + side * -z * 0.25, y - 0.03 + z * 0.15, -0.03 + z * 0.7) for x, y, z in r] for r in thumb]
    facet(kit, f"{name} hand", merge(loft(fist), loft(thumb)), skin, wr)
    return sh, el, wr


def build_player(kit, root):
    teal, denim, apron, skin, red = (mt(kit, k) for k in ("teal", "denim", "apron", "skin", "red"))
    hips = kit.empty("P hips", root, (0, 0, 0.95))
    spine = kit.empty("P spine", hips, (0, 0, 0.0), (9, 0, 0))

    secs = [(-0.1, 0.15, 0.1, 0.1), (0.0, 0.17, 0.11, 0.12), (0.1, 0.165, 0.115, 0.115), (0.24, 0.158, 0.13, 0.11),
            (0.38, 0.178, 0.12, 0.11, 0.0), (0.48, 0.19, 0.108, 0.115, 0.01), (0.55, 0.165, 0.085, 0.1, 0.02),
            (0.6, 0.066, 0.05, 0.05, 0.02)]
    rings = [jit(kit, hring(torso_prof(*s[1:]), s[0]), 0.004) for s in secs]
    facet(kit, "P torso", loft(rings, closed=False), [teal, denim], spine,
          bandmat=lambda b: 1 if b in (-1, 0, 1) else 0, mirror=True)
    # apron: bib, skirt, red hem stripe
    rows = [0.44, 0.3, 0.12, -0.05, -0.2, -0.29, -0.33, -0.38]
    D = {0.44: 0.125, 0.3: 0.142, 0.12: 0.133, -0.05: 0.128, -0.2: 0.15, -0.29: 0.158, -0.33: 0.162, -0.38: 0.166}
    arows = []
    for z in rows:
        xs = [-0.16, -0.08, 0.0, 0.08, 0.16]
        sc = 0.62 if z > 0.4 else (0.85 if z > 0.25 else 1.0)
        row = [(x * sc, -D[z] + 0.85 * (x * sc) ** 2, z) for x in xs]
        arows.append(jit(kit, row, 0.004))
    facet(kit, "P apron", loft(arows, closed=False, cap0=False, cap1=False), [apron, red], spine,
          bandmat=lambda b: 1 if b == 5 else 0, solid=0.006)
    for i, (x, z, r, col) in enumerate(((-0.07, 0.2, 0.035, "pink"), (0.06, -0.12, 0.028, "choc"), (-0.02, -0.26, 0.03, "pink"),
                                        (0.09, 0.32, 0.02, "mint"))):
        y = -min(D.items(), key=lambda kv: abs(kv[0] - z))[1] + 0.85 * x * x - 0.006
        st = kit.empty(f"P stain {i}", spine, (x, y, z), (90, 0, 0))
        splat(kit, f"P stain {i} mesh", mt(kit, col), st, (0, 0), r, n=9, jag=0.4, z=0.0)
    tie = [hring(torso_prof(0.172, 0.123, 0.122), z) for z in (0.09, 0.118)]
    facet(kit, "P apron tie", loft(tie, closed=False, cap0=False, cap1=False), apron, spine, mirror=True, solid=0.004)
    facet(kit, "P apron strap", strip([(0.098, -0.128, 0.44), (0.085, -0.1, 0.55), (0.07, -0.05, 0.615),
                                        (0.05, 0.02, 0.63), (0.0, 0.05, 0.625)], 0.018, 0.005, side=(0, 0, 1)),
          apron, spine, mirror=True)

    # cooler backpack with spare pints
    CR = [(0.12, [(0, 0.13), (0.14, 0.135), (0.16, 0.22), (0.14, 0.31), (0, 0.315)]),
          (0.15, [(0, 0.125), (0.155, 0.13), (0.172, 0.225), (0.155, 0.32), (0, 0.325)]),
          (0.27, [(0, 0.124), (0.157, 0.129), (0.174, 0.226), (0.157, 0.322), (0, 0.327)]),
          (0.32, [(0, 0.124), (0.158, 0.129), (0.175, 0.227), (0.158, 0.323), (0, 0.328)]),
          (0.44, [(0, 0.125), (0.16, 0.13), (0.178, 0.228), (0.16, 0.325), (0, 0.33)]),
          (0.45, [(0, 0.118), (0.172, 0.122), (0.192, 0.228), (0.172, 0.336), (0, 0.342)]),
          (0.5, [(0, 0.12), (0.168, 0.124), (0.188, 0.228), (0.168, 0.333), (0, 0.339)]),
          (0.525, [(0, 0.138), (0.148, 0.142), (0.164, 0.228), (0.148, 0.317), (0, 0.322)])]
    rings = [jit(kit, hring(p, z), 0.003) for z, p in CR]
    facet(kit, "P cooler", loft(rings, closed=False), [red, apron], spine,
          bandmat=lambda b: 1 if b in (2, 4, 5, 6, 7) else 0, mirror=True)
    for i, (x, lid) in enumerate(((-0.085, "pink"), (0.0, "choc"), (0.085, "mint"))):
        piv = kit.empty(f"P pint {i}", spine, (x, 0.23, 0.522), (kit.rand.uniform(-8, 8), kit.rand.uniform(-8, 8), 0))
        p = limb(kit, [(0.0, 0.036, 0.036), (0.07, 0.042, 0.042), (0.07, 0.046, 0.046), (0.088, 0.044, 0.044),
                       (0.092, 0.04, 0.04)], n=6, twist=0, jitter=0.02)
        facet(kit, f"P pint {i} tub", loft(p), [mt(kit, "cream"), mt(kit, lid)], piv,
              bandmat=lambda b: 0 if b in (-1, 0) else 1)
    facet(kit, "P cooler strap", strip([(0.1, 0.13, 0.455), (0.1, 0.105, 0.57), (0.1, 0.03, 0.635),
                                        (0.1, -0.06, 0.6), (0.11, -0.112, 0.5), (0.12, -0.132, 0.38),
                                        (0.125, -0.138, 0.28)], 0.032, 0.008), mt(kit, "strap"), spine, mirror=True)

    # head
    head = kit.empty("P head", spine, (0, -0.035, 0.585), (-8, 0, 0))
    rings = [hring(p, z) for z, p in PH]
    facet(kit, "P head", loft(rings, closed=False), skin, head, mirror=True)
    sock = kit.mat("socket", hex_scale(C["skin"], 0.62))
    facet(kit, "P eye sockets", decal(PH, [[(0.02, 0.165), (0.07, 0.158), (0.074, 0.172), (0.05, 0.183), (0.024, 0.178)]], 0.003),
          sock, head, mirror=True)
    facet(kit, "P eyes", decal(PH, [[(0.034, 0.168), (0.054, 0.166), (0.056, 0.172), (0.036, 0.174)]], 0.006),
          mt(kit, "dark"), head, mirror=True)
    facet(kit, "P brows", decal(PH, [[(0.016, 0.184), (0.072, 0.176), (0.078, 0.186), (0.02, 0.194)]], 0.007),
          mt(kit, "hair"), head, mirror=True)
    facet(kit, "P mouth", decal(PH, [[(0.0, 0.1), (0.03, 0.097), (0.031, 0.103), (0.0, 0.106)]], 0.004),
          kit.mat("lip", hex_scale(C["skin"], 0.5)), head, mirror=True)
    facet(kit, "P stubble", decal(PH, [[(0.0, 0.072), (0.04, 0.074), (0.062, 0.09), (0.05, 0.094), (0.032, 0.093), (0.0, 0.092)]], 0.002),
          kit.mat("stubble", hex_scale(C["skin"], 0.78)), head, mirror=True)
    ear = ([(0.083, -0.005, 0.12), (0.083, 0.035, 0.125), (0.083, 0.03, 0.185), (0.083, 0.0, 0.172),
            (0.1, 0.005, 0.128), (0.104, 0.038, 0.132), (0.1, 0.034, 0.18), (0.097, 0.004, 0.17)],
           [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]], [0] * 6)
    facet(kit, "P ears", ear, skin, head, mirror=True)
    hair = []
    for z, s in ((0.11, 1.03), (0.18, 1.06), (0.245, 1.07)):
        pts = dict(PH)[0.17] if z < 0.2 else dict(PH)[0.24]
        hair.append([(x * s, y * s + 0.004, z) for x, y in pts[3:]])
    facet(kit, "P hair", loft(hair, closed=False, cap0=False, cap1=False), kit.mat("phair", "#5a4232"), head, mirror=True,
          solid=0.004)
    # paper soda-jerk hat
    hv = [(0, -0.112, 0.228), (0.072, -0.088, 0.231), (0.096, 0.0, 0.234), (0.078, 0.086, 0.231), (0, 0.108, 0.228),
          (0, -0.126, 0.3), (0.014, -0.06, 0.315), (0.016, 0.0, 0.318), (0.014, 0.06, 0.315), (0, 0.122, 0.298),
          (0, -0.06, 0.321), (0, 0.0, 0.325), (0, 0.06, 0.321)]
    hf = [[0, 1, 6, 5], [1, 2, 7, 6], [2, 3, 8, 7], [3, 4, 9, 8], [5, 6, 10], [6, 7, 11, 10], [7, 8, 12, 11], [8, 9, 12]]
    hat = kit.empty("P hat", head, (0, 0.0, 0.0), (-4, 0, 0))
    facet(kit, "P hat paper", (hv, hf, [0] * len(hf)), apron, hat, mirror=True, solid=0.004)
    band = [[(x * 1.04, y * 1.04, z) for x, y, z in hv[:5]], [(x * 1.05, y * 1.05, z + 0.026) for x, y, z in hv[:5]]]
    facet(kit, "P hat stripe", loft(band, closed=False, cap0=False, cap1=False), red, hat, mirror=True, solid=0.004)

    # arms: right (-X) raised and aiming, left (+X) tugging the strap
    _, _, wr = player_arm(kit, "P R", spine, (-0.19, 0.0, 0.5), (-96, 0, 12), (-6, 0, 0), (0, 0, 0), 1)
    player_arm(kit, "P L", spine, (0.19, 0.0, 0.5), (-12, -10, 0), (-78, 0, -18), (10, 0, 0), -1)
    W = chain(wr, root)
    f = (W.to_3x3() @ Vector((0, 0, -1))).normalized()
    up = Vector((0, 0, 1))
    gz = (up - f * up.dot(f)).normalized()
    gy = -f
    gx = gy.cross(gz)
    R = Matrix((gx, gy, gz)).transposed()
    grip = Vector((0, 0.066, -0.07))
    center = W @ Vector((0, 0, -0.06))
    G = Matrix.Translation(center - R @ grip) @ R.to_4x4()
    gun = kit.empty("P held gun", wr)
    gun.matrix_basis = W.inverted() @ G
    build_gun(kit, gun)

    # legs
    for sx, name in ((-1, "R"), (1, "L")):
        hp = kit.empty(f"P {name} hip", hips, (sx * 0.095, 0.0, -0.04), (-6, sx * -3, 0))
        th = limb(kit, [(0.05, 0.085, 0.09), (-0.06, 0.088, 0.09), (-0.22, 0.07, 0.072), (-0.4, 0.052, 0.058),
                        (-0.44, 0.05, 0.055)])
        facet(kit, f"P {name} thigh", loft(th), denim, hp)
        kn = kit.empty(f"P {name} knee", hp, (0, 0, -0.43), (10, 0, 0))
        sh = limb(kit, [(0.03, 0.054, 0.058), (-0.1, 0.056, 0.062), (-0.26, 0.045, 0.048), (-0.33, 0.05, 0.052),
                        (-0.36, 0.06, 0.062)])
        facet(kit, f"P {name} shin", loft(sh), denim, kn)
        an = kit.empty(f"P {name} ankle", kn, (0, 0, -0.36), (-4, sx * 3, sx * -6))
        foot(kit, f"P {name} boot", an, [mt(kit, "boot"), mt(kit, "sole")], 0.12, 0.17, 0.056)


# ------------------------------------------------------------------ zombie
ZT = [(-0.1, 0.13, 0.09, 0.1, 0, 0), (0.0, 0.145, 0.095, 0.1, 0, 0), (0.07, 0.13, 0.085, 0.09, 0, 0),
      (0.15, 0.118, 0.065, 0.085, 0, 0), (0.21, 0.135, 0.095, 0.09, 0, 0), (0.245, 0.124, 0.082, 0.09, 0, 0),
      (0.285, 0.142, 0.1, 0.095, 0, 0.005), (0.32, 0.13, 0.087, 0.095, 0, 0.01), (0.36, 0.15, 0.105, 0.1, 0, 0.025),
      (0.395, 0.138, 0.094, 0.1, 0, 0.035), (0.44, 0.158, 0.1, 0.105, 0.0, 0.045), (0.5, 0.175, 0.085, 0.11, 0.02, 0.035),
      (0.55, 0.15, 0.065, 0.09, 0.03, 0.0), (0.585, 0.045, 0.035, 0.035, 0.01, 0)]
ZS = [(0.06, 0.152, 0.1, 0.105, 0, 0), (0.16, 0.148, 0.102, 0.1, 0, 0), (0.285, 0.153, 0.112, 0.105, 0, 0.012),
      (0.36, 0.163, 0.116, 0.11, 0, 0.032), (0.44, 0.171, 0.112, 0.114, 0, 0.048), (0.5, 0.18, 0.097, 0.122, 0.02, 0.04),
      (0.556, 0.14, 0.072, 0.098, 0.03, 0.0)]
ZH = [(0.09, [(0, -0.096), (0.03, -0.088), (0.058, -0.05), (0.07, 0.01), (0.055, 0.065), (0, 0.08)]),
      (0.12, [(0, -0.118), (0.022, -0.098), (0.052, -0.058), (0.072, 0.01), (0.062, 0.075), (0, 0.09)]),
      (0.155, [(0, -0.104), (0.035, -0.095), (0.078, -0.055), (0.082, 0.015), (0.07, 0.085), (0, 0.1)]),
      (0.185, [(0, -0.112), (0.05, -0.11), (0.084, -0.066), (0.087, 0.015), (0.072, 0.09), (0, 0.105)]),
      (0.22, [(0, -0.09), (0.045, -0.085), (0.075, -0.05), (0.08, 0.015), (0.068, 0.08), (0, 0.095)])]
ZJ = [(0.005, [(0, -0.102), (0.034, -0.093), (0.056, -0.05), (0.064, -0.005), (0.04, 0.012), (0, 0.012)]),
      (-0.04, [(0, -0.114), (0.028, -0.104), (0.05, -0.06), (0.056, -0.02), (0.035, 0.0), (0, 0.0)]),
      (-0.066, [(0, -0.104), (0.02, -0.099), (0.035, -0.07), (0.04, -0.042), (0.025, -0.03), (0, -0.03)])]


def zombie_hand(kit, name, wr, side):
    """Palm block plus long faceted wedge fingers curling toward +Y. side: +1 puts the thumb on +X."""
    parts = [loft(limb(kit, [(0.01, 0.026, 0.016), (-0.035, 0.037, 0.019), (-0.072, 0.039, 0.015)], n=5))]
    for i, (x, L) in enumerate(((-0.027, 0.095), (-0.009, 0.115), (0.009, 0.118), (0.027, 0.1))):
        x = x * side * -1
        L *= kit.rand.uniform(0.92, 1.05)
        parts.append(loft(limb(kit, [(-0.065, 0.0085, 0.007, x, 0.0), (-0.065 - L * 0.45, 0.0075, 0.0062, x * 1.08, 0.01),
                                     (-0.065 - L * 0.8, 0.005, 0.0045, x * 1.12, 0.03), (-0.065 - L, 0, 0, x * 1.12, 0.05)],
                               n=4, twist=1.0, jitter=0.1)))
    t = limb(kit, [(0.0, 0.009, 0.008), (-0.04, 0.007, 0.006), (-0.07, 0, 0)], n=4, twist=1.0)
    t = [[(side * (0.034 - z * 0.45) + x, y + 0.008 - z * 0.25, -0.02 + z * 0.75) for x, y, z in r] for r in t]
    parts.append(loft(t))
    facet(kit, f"{name} hand", merge(*parts), mt(kit, "zskin"), wr)


def zombie_arm(kit, name, parent, loc, rot, elbow_rot, wrist_rot, side, torn=False):
    shirt, skin = mt(kit, "zshirt"), mt(kit, "zskin")
    sh = kit.empty(f"{name} shoulder", parent, loc, rot)
    up = limb(kit, [(0.045, 0.048, 0.047), (0.0, 0.058, 0.055), (-0.1, 0.054, 0.052, 0, 0, 0.022), (-0.103, 0.034, 0.033),
                    (-0.2, 0.031, 0.029), (-0.275, 0.037, 0.034), (-0.31, 0.029, 0.028)])
    mats = [shirt, skin, mt(kit, "blood")]
    facet(kit, f"{name} upper arm", loft(up), mats, sh,
          bandmat=lambda b: (2 if torn else 0) if b == -1 else (0 if b in (0, 1, 2) else 1))
    el = kit.empty(f"{name} elbow", sh, (0, 0, -0.29), elbow_rot)
    fo = limb(kit, [(0.015, 0.03, 0.029), (-0.05, 0.034, 0.03), (-0.2, 0.025, 0.021), (-0.28, 0.02, 0.017)])
    facet(kit, f"{name} forearm", loft(fo), skin, el)
    wr = kit.empty(f"{name} wrist", el, (0, 0, -0.275), wrist_rot)
    zombie_hand(kit, name, wr, side)
    if torn:
        bone = limb(kit, [(0.03, 0.016, 0.016), (0.075, 0.014, 0.014), (0.088, 0.022, 0.02), (0.1, 0, 0)], n=5)
        facet(kit, f"{name} bone", loft(bone), mt(kit, "bone"), sh)
        blob(kit, f"{name} gore", mt(kit, "blood2"), sh, (0, 0, 0.05), 0.066, (1, 1, 0.4), rot=(0, 0, 0.4))
    return sh


def zombie_leg(kit, name, parent, sx, H, a, k, splay, torn, bare):
    pants, skin = mt(kit, "zpants"), mt(kit, "zskin")
    Lt, Ls, fh = 0.42, 0.37, 0.09
    drop = (Lt * math.cos(math.radians(a)) + Ls * math.cos(math.radians(a + k))) * math.cos(math.radians(splay))
    hz = fh + drop - H
    hp = kit.empty(f"{name} hip", parent, (sx * 0.085, 0.0, hz), (a, sx * -splay, 0))
    th = limb(kit, [(0.05, 0.075, 0.08), (-0.06, 0.073, 0.076), (-0.22, 0.058, 0.06), (-0.38, 0.046, 0.05),
                    (-0.425, 0.05, 0.053)])
    facet(kit, f"{name} thigh", loft(th), pants, hp)
    kn = kit.empty(f"{name} knee", hp, (0, 0, -Lt), (k, 0, 0))
    if torn:
        secs = [(0.03, 0.05, 0.054), (-0.08, 0.05, 0.054), (-0.16, 0.052, 0.054, 0, 0, 0.03), (-0.163, 0.034, 0.036),
                (-0.3, 0.028, 0.029), (-0.375, 0.031, 0.031)]
        bm = lambda b: 0 if b in (-1, 0, 1, 2) else 1
    else:
        secs = [(0.03, 0.05, 0.054), (-0.08, 0.049, 0.053), (-0.2, 0.041, 0.043), (-0.32, 0.04, 0.04, 0, 0, 0.015),
                (-0.375, 0.035, 0.035)]
        bm = lambda b: 0
    facet(kit, f"{name} shin", loft(limb(kit, secs)), [pants, skin], kn, bandmat=bm)
    an = kit.empty(f"{name} ankle", kn, (0, 0, -Ls), (-(a + k), 0, sx * -10))
    if bare:
        foot(kit, f"{name} foot", an, [skin, mt(kit, "zrot")], fh, 0.15, 0.045, bare=True)
    else:
        foot(kit, f"{name} shoe", an, [kit.mat("zshoe", "#3a302a"), mt(kit, "sole")], fh, 0.155, 0.05)


def build_zombie(kit, root, hit=False):
    skin, shirt, pants = mt(kit, "zskin"), mt(kit, "zshirt"), mt(kit, "zpants")
    H = 0.88
    legs = kit.empty("Z legs", root, (0, 0.03, H))
    hips = kit.empty("Z hips", root, (0, 0.03, H), (0, 0, 6) if not hit else (0, 0, -10))
    spine = kit.empty("Z spine", hips, (0, 0, 0), (34, 0, 4) if not hit else (-6, -12, -16))

    zombie_leg(kit, "Z L", legs, 1, H, -18 if not hit else -4, 26 if not hit else 14, 4, False, True)
    zombie_leg(kit, "Z R", legs, -1, H, 10 if not hit else 18, 14, 3, True, False)

    rings = [jit(kit, hring(torso_prof(*s[1:]), s[0]), 0.003) for s in ZT]
    facet(kit, "Z torso", loft(rings, closed=False), [skin, pants], spine,
          bandmat=lambda b: 1 if b in (-1, 0, 1) else 0, mirror=True)
    # torn shirt: full ring, jagged hem, holes
    srings = []
    for k, s in enumerate(ZS):
        r = full_ring(torso_prof(*s[1:]), s[0], 0.004)
        if k == 0:
            r = [(x, y, z + kit.rand.uniform(-0.06, 0.05) * (1 if i % 2 else 0.5)) for i, (x, y, z) in enumerate(r)]
        srings.append(r)
    v, f, b = loft(srings, cap0=False, cap1=False)
    holes = {(0, 0), (0, 1), (1, 0), (1, 1), (0, 9), (2, 5)}
    keep = [(face, bb) for i, (face, bb) in enumerate(zip(f, b)) if (bb, i % 10) not in holes]
    v = [(x + kit.rand.uniform(-0.006, 0.006), y + kit.rand.uniform(-0.006, 0.006), z + kit.rand.uniform(-0.012, 0.012))
         for x, y, z in v]
    facet(kit, "Z shirt", (v, [k[0] for k in keep], [k[1] for k in keep]), shirt, spine, solid=0.007)
    # ice cream splat on the shirt (right chest)
    sp = kit.empty("Z splat", spine, (-0.07, -0.126, 0.42), (-90 + 8, 0, 12))
    splat(kit, "Z splat pink", mt(kit, "pink"), sp, (0, 0), 0.07, n=11, jag=0.4, z=0.0)
    blob(kit, "Z splat scoop", mt(kit, "pink"), sp, (0.012, 0.0, -0.014), 0.032, (1, 1, 0.55))
    blob(kit, "Z splat cream", mt(kit, "cream"), sp, (-0.025, 0.02, -0.01), 0.018, (1, 1, 0.5))
    for i in range(3):
        d = kit.empty(f"Z drip {i}", sp, (-0.03 + i * 0.03, 0.04 + 0.01 * i, -0.004))
        facet(kit, f"Z drip {i} mesh", loft(limb(kit, [(0, 0.011, 0.004), (-0.05 - 0.025 * i, 0, 0)], n=4)),
              mt(kit, "pink"), d, rot=(90, 0, 0))

    # head with exposed brain and slack jaw
    head = kit.empty("Z head", spine, (0, -0.05, 0.6), (-44, 10, -6) if not hit else (24, -16, 22))
    neck = limb(kit, [(-0.1, 0.045, 0.045, 0, 0.02), (0.0, 0.036, 0.04, 0, 0.02), (0.1, 0.042, 0.045, 0, 0.03)], n=5)
    facet(kit, "Z neck", loft(neck), skin, head)
    top = [(x * 0.94, y * 0.94, 0.232 + kit.rand.uniform(0, 0.03) + (0.02 if y > 0 else 0)) for x, y in ZH[-1][1]]
    top = [(0 if i in (0, 5) else x, y, z) for i, (x, y, z) in enumerate(top)]
    rings = [hring(p, z) for z, p in ZH] + [top]
    facet(kit, "Z head", loft(rings, closed=False, cap1=False), [skin, mt(kit, "mouth"), mt(kit, "bone")], head,
          bandmat=lambda b: 1 if b == -1 else (2 if b == 4 else 0), mirror=True)
    jaw = kit.empty("Z jaw", head, (0, 0.005, 0.088), (24 if not hit else 38, 0, -4))
    facet(kit, "Z jaw", loft([hring(p, z) for z, p in ZJ], closed=False), [skin, mt(kit, "mouth")], jaw,
          bandmat=lambda b: 1 if b == -1 else 0, mirror=True)
    bone = mt(kit, "bone")
    for i, x in enumerate((-0.038, -0.018, 0.004, 0.044)):
        y = surf_y(ZH, x, 0.09) + 0.008
        facet(kit, f"Z tooth up {i}", loft([[(x - 0.007, y, 0.092), (x + 0.007, y, 0.092), (x, y + 0.008, 0.092)],
                                            [(x + kit.rand.uniform(-0.003, 0.003), y + 0.002, 0.07 - kit.rand.uniform(0, 0.008))]]),
              bone, head)
    for i, x in enumerate((-0.026, -0.006, 0.02)):
        y = -0.094 + abs(x) * 0.4
        facet(kit, f"Z tooth low {i}", loft([[(x - 0.007, y, 0.004), (x + 0.007, y, 0.004), (x, y + 0.008, 0.004)],
                                             [(x, y + 0.002, 0.022 + kit.rand.uniform(0, 0.006))]]), bone, jaw)
    # mismatched eyes: bulging pale left, sunken red pinprick right
    ey = surf_y(ZH, 0.044, 0.162)
    blob(kit, "Z eye big", mt(kit, "yeye"), head, (0.046, ey - 0.004, 0.163), 0.027, (1, 0.85, 1), rough=0.06)
    blob(kit, "Z pupil", mt(kit, "dark"), head, (0.05, ey - 0.027, 0.16), 0.006, rough=0.05)
    facet(kit, "Z socket", decal(ZH, [[(-0.022, 0.15), (-0.06, 0.146), (-0.07, 0.165), (-0.05, 0.18), (-0.025, 0.176)]], 0.003),
          mt(kit, "dark"), head)
    blob(kit, "Z pinprick", kit.mat("redeye", "#e0302a"), head, (-0.045, surf_y(ZH, -0.045, 0.164) - 0.006, 0.164), 0.0055,
         rough=0.05)
    facet(kit, "Z cheek rot", decal(ZH, [[(-0.03, 0.105), (-0.062, 0.1), (-0.068, 0.125), (-0.05, 0.14), (-0.034, 0.128)]], 0.003),
          mt(kit, "zrot"), head)
    facet(kit, "Z gash", decal(ZH, [[(0.03, 0.2), (0.07, 0.19), (0.072, 0.196), (0.034, 0.206)]], 0.004),
          mt(kit, "blood2"), head)
    for i, (x, y, z) in enumerate(((0.025, -0.03, 0.235), (-0.03, -0.025, 0.24), (0.028, 0.035, 0.25), (-0.026, 0.04, 0.252),
                                   (0.0, 0.0, 0.245))):
        blob(kit, f"Z brain {i}", mt(kit, "brain") if i % 2 == 0 else mt(kit, "brain2"), head, (x, y, z), 0.04,
             (0.85, 1.25, 0.6), subdiv=1, rough=0.12)
    ear = ([(0.074, -0.0, 0.12), (0.076, 0.035, 0.13), (0.076, 0.028, 0.188), (0.074, 0.002, 0.168),
            (0.094, 0.008, 0.124), (0.1, 0.042, 0.14), (0.096, 0.03, 0.186), (0.09, 0.004, 0.16)],
           [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]], [0] * 6)
    facet(kit, "Z ear", ear, skin, head)
    # arms: right (-X) always attached, left (+X) reaches or flies off
    if not hit:
        zombie_arm(kit, "Z R", spine, (-0.172, 0.02, 0.48), (-70, 6, 10), (18, 0, 0), (40, 0, 0), 1)
        zombie_arm(kit, "Z L", spine, (0.172, 0.02, 0.48), (-108, -4, -8), (12, 0, 0), (34, 0, 0), -1)
        return
    zombie_arm(kit, "Z R", spine, (-0.172, 0.02, 0.48), (-160, 24, 30), (40, 0, 0), (-30, 0, 10), 1)
    S = chain(spine, root) @ Vector((0.172, 0.02, 0.48))
    Rinv = root.matrix_basis.to_3x3().normalized().inverted()
    wdir = lambda x, y, z: Rinv @ Vector((x, y, z))
    fly = S + wdir(0.36, -0.22, 0.3)
    arm = zombie_arm(kit, "Z L flying", root, (0, 0, 0), (0, 0, 0), (28, 0, 0), (40, 0, 0), -1, torn=True)
    arm.matrix_basis = Matrix.Translation(fly) @ Euler((math.radians(-40), math.radians(70), math.radians(150))).to_matrix().to_4x4()
    # stump on the torso
    stump = kit.empty("Z stump", spine, (0.17, 0.02, 0.48), (0, 90, 0))
    blob(kit, "Z stump gore", mt(kit, "blood2"), stump, (0, 0, 0.0), 0.058, (1, 1, 0.45), rot=(0, 0, 0.3))
    facet(kit, "Z stump bone", loft(limb(kit, [(0.0, 0.016, 0.016), (0.04, 0.015, 0.014), (0.05, 0.022, 0.02), (0.06, 0, 0)], n=5)),
          bone, stump)
    impact_fx(kit, root, S, wdir)


def impact_fx(kit, root, S, wdir):
    blood, blood2 = mt(kit, "blood"), mt(kit, "blood2")
    creams = [mt(kit, "pink"), mt(kit, "cream"), mt(kit, "mint"), mt(kit, "choc")]
    base = wdir(1.0, -0.55, 0.75).normalized()
    rnd = kit.rand

    def spray(spread):
        d = base + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), rnd.uniform(-spread, spread)))
        return d.normalized()
    for i in range(30):
        d = spray(0.9)
        dist = rnd.uniform(0.08, 0.62)
        shard(kit, f"FX shard {i}", blood if i % 3 else blood2, root, S + d * dist, d, rnd.uniform(0.04, 0.11) * (1 - dist * 0.6),
              rnd.uniform(0.008, 0.018))
    for i in range(26):
        d = spray(1.1)
        dist = rnd.uniform(0.1, 0.7)
        blob(kit, f"FX cream {i}", creams[i % 4] if i % 5 else creams[0], root, S + d * dist, rnd.uniform(0.02, 0.05),
             (1, 1, rnd.uniform(0.6, 1.0)))
    for i in range(10):
        d = spray(1.0)
        chunk(kit, f"FX chunk {i}", mt(kit, "zskin") if i % 2 else mt(kit, "zshirt"), root,
              S + d * rnd.uniform(0.15, 0.55), rnd.uniform(0.012, 0.022))
    # sprinkles
    sprk = [mt(kit, "pink"), mt(kit, "tape"), mt(kit, "mint"), mt(kit, "sprk_b"), mt(kit, "cream")]
    for i in range(26):
        d = spray(1.3)
        p = S + d * rnd.uniform(0.1, 0.75)
        ob = kit.prim(f"FX sprinkle {i}", 'box', (0.005, 0.005, 0.02), sprk[i % 5], root, smooth=False)
        ob.location = p
        ob.rotation_euler = [rnd.uniform(0, 6.28) for _ in range(3)]
    # angular splash crown facing the camera
    cam = Vector((1.7, -0.5, 1.3))
    rootM = root.matrix_basis
    view = (rootM.inverted() @ cam - S).normalized()
    q = Vector((0, 0, 1)).rotation_difference(view)
    crown = kit.empty("FX crown", root)
    crown.matrix_basis = Matrix.Translation(S + view * 0.04) @ q.to_matrix().to_4x4()
    for layer, (mat, r0, r1, n) in enumerate(((blood2, 0.05, 0.34, 10), (mt(kit, "pink"), 0.035, 0.25, 9),
                                              (mt(kit, "cream"), 0.02, 0.13, 7))):
        v, f = [], []
        for i in range(n):
            a = 2 * math.pi * (i + 0.5 * layer + rnd.uniform(-0.2, 0.2)) / n
            w = rnd.uniform(0.18, 0.3)
            r = r1 * rnd.uniform(0.6, 1.15)
            o = len(v)
            v += [(r0 * math.cos(a - w), r0 * math.sin(a - w), layer * 0.01),
                  (r * math.cos(a), r * math.sin(a), layer * 0.01 + rnd.uniform(-0.02, 0.02)),
                  (r0 * math.cos(a + w), r0 * math.sin(a + w), layer * 0.01)]
            f.append([o, o + 1, o + 2])
        ring0 = [(r0 * 1.05 * math.cos(2 * math.pi * i / 7), r0 * 1.05 * math.sin(2 * math.pi * i / 7), layer * 0.01) for i in range(7)]
        o = len(v)
        v += ring0
        f.append(list(range(o, o + 7)))
        facet(kit, f"FX crown {layer}", (v, f, [0] * len(f)), mat, crown)
    # drip trail toward the flying arm
    for i in range(7):
        t = (i + 1) / 8
        p = S + wdir(0.36, -0.22, 0.3) * t + Vector((0, 0, 0.06 * math.sin(t * math.pi)))
        blob(kit, f"FX trail {i}", blood2 if i % 2 else mt(kit, "pink"), root, p, 0.018 * (1 - t * 0.5), (1, 1, 0.8))
    # floor splats and dust puffs
    for i in range(9):
        a = rnd.uniform(-1.4, 1.4)
        dist = rnd.uniform(0.15, 0.75)
        w = wdir(math.cos(a) * dist, -abs(math.sin(a)) * dist * 0.7 + rnd.uniform(-0.2, 0.25), 0)
        mat = blood if i % 3 == 0 else (blood2 if i % 3 == 1 else creams[i % 2])
        splat(kit, f"FX floor splat {i}", mat, root, (w.x, w.y), rnd.uniform(0.07, 0.2), n=rnd.choice((11, 13)),
              jag=0.32, z=0.002 + i * 0.0006)
        for j in range(3):
            o = Vector((w.x, w.y, 0)) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)).normalized() * rnd.uniform(0.2, 0.3)
            splat(kit, f"FX floor drop {i}.{j}", mat, root, (o.x, o.y), rnd.uniform(0.015, 0.03), n=5, jag=0.2,
                  z=0.002 + i * 0.0006)
    dust = kit.mat("dust puff", C["dust"])
    p = dust.node_tree.nodes["Principled BSDF"]
    p.inputs["Alpha"].default_value = 0.6
    for c in range(6):
        if c < 3:
            ctr = wdir((-0.32, 0.3, 0.05)[c], (0.12, 0.16, 0.3)[c], 0) + Vector((0, 0, 0.06))
        else:
            ctr = S + spray(0.35) * rnd.uniform(0.4, 0.6)
        view = (rootM.inverted() @ cam - ctr).normalized()
        piv = kit.empty(f"FX dust {c}", root)
        piv.matrix_basis = Matrix.Translation(ctr) @ Vector((0, 0, 1)).rotation_difference(view).to_matrix().to_4x4()
        for j in range(3):
            splat(kit, f"FX dust {c}.{j}", dust, piv, (rnd.uniform(-0.05, 0.05), rnd.uniform(-0.03, 0.05)),
                  rnd.uniform(0.05, 0.08) * (1.1 if c < 3 else 1.0), n=9, jag=0.25, z=j * 0.01)


# ------------------------------------------------------------------ gun
def build_gun(kit, root):
    metal, metal_d, pink, tape = mt(kit, "metal"), mt(kit, "metal_d"), mt(kit, "pink"), mt(kit, "tape")
    body = [(-0.065, 0.034), (0.06, 0.036), (0.088, 0.024), (0.1, -0.004), (0.094, -0.026), (0.03, -0.03), (-0.065, -0.028),
            (-0.078, 0.004)]
    facet(kit, "G body", slab(body, 0.024, 0.007), metal, root, mirror=True)
    grip = [(0.034, -0.026), (0.082, -0.026), (0.104, -0.128), (0.094, -0.14), (0.054, -0.14), (0.045, -0.128)]
    facet(kit, "G grip", slab(grip, 0.019, 0.006), metal_d, root, mirror=True)

    def gy(z, front):
        return (0.034 + (0.045 - 0.034) * (z + 0.026) / -0.102) if front else (0.082 + (0.104 - 0.082) * (z + 0.026) / -0.102)
    for i, (z0, z1) in enumerate(((-0.05, -0.068), (-0.074, -0.09), (-0.098, -0.112))):
        tp = [(gy(z0, True) - 0.004, z0), (gy(z0, False) + 0.004, z0 + 0.004 * (i - 1)), (gy(z1, False) + 0.004, z1 + 0.004 * (i - 1)),
              (gy(z1, True) - 0.004, z1)]
        facet(kit, f"G tape {i}", slab(tp, 0.0215, 0.003), tape, root, mirror=True)
    facet(kit, "G guard", strip([(0, -0.026, -0.026), (0, -0.031, -0.054), (0, -0.016, -0.073), (0, 0.02, -0.075),
                                 (0, 0.046, -0.066)], 0.012, 0.005), metal_d, root)
    facet(kit, "G trigger", slab([(0.008, -0.03), (0.02, -0.03), (0.014, -0.06), (0.004, -0.056)], 0.004, 0.0015), pink, root,
          mirror=True)
    # barrel and pink band
    barrel = kit.empty("G barrel", root, (0, -0.06, 0.006), (-90, 0, 0))
    facet(kit, "G barrel", loft(limb(kit, [(0.0, 0.018, 0.018), (-0.06, 0.016, 0.016), (-0.066, 0.02, 0.02),
                                           (-0.075, 0.02, 0.02)], n=8, twist=0, jitter=0.02)), metal, barrel)
    bandp = [(-0.05, 0.039), (-0.032, 0.041), (-0.03, -0.033), (-0.052, -0.031)]
    facet(kit, "G pink band", slab(bandp, 0.027, 0.004), pink, root, mirror=True)
    # waffle-cone flared muzzle, checkered facets
    cone = kit.empty("G cone", barrel, (0, 0, -0.07))
    rings = []
    for z, r in ((0.0, 0.02), (-0.025, 0.028), (-0.05, 0.037), (-0.075, 0.048), (-0.082, 0.052), (-0.085, 0.042), (-0.05, 0.022)):
        rings.append([(r * math.cos(2 * math.pi * i / 8 + (0.2 if len(rings) % 2 else 0)), r * math.sin(2 * math.pi * i / 8 + (0.2 if len(rings) % 2 else 0)), z)
                      for i in range(8)])
    v, f, b = loft(rings, cap0=False, cap1=True)
    w1, w2 = mt(kit, "waffle"), mt(kit, "waffle2")
    ob = facet(kit, "G waffle cone", (v, f, b), [w1, w2, mt(kit, "choc")], cone)
    ob.data.polygons.foreach_set("material_index",
                                 [(2 if bb >= 5 else (0 if bb == 4 else (i + bb) % 2)) for i, bb in enumerate(b)])
    # sights
    facet(kit, "G front sight", slab([(-0.058, 0.034), (-0.046, 0.034), (-0.05, 0.05), (-0.056, 0.05)], 0.004, 0.001), metal_d,
          root, mirror=True)
    facet(kit, "G rear sight", slab([(0.07, 0.033), (0.088, 0.024), (0.09, 0.046), (0.078, 0.048)], 0.012, 0.003), metal_d,
          root, mirror=True)
    # pint-tub magazine with chocolate scoop and sprinkles
    tub = kit.empty("G tub", root, (0, 0.012, 0.032), (-8, 0, 0))
    facet(kit, "G mag well", slab([(-0.03, 0.0), (0.03, 0.0), (0.024, 0.012), (-0.024, 0.012)], 0.02, 0.004), metal_d, tub,
          mirror=True)
    t = limb(kit, [(0.01, 0.028, 0.028), (0.03, 0.031, 0.031), (0.031, 0.033, 0.033), (0.055, 0.035, 0.035),
                   (0.056, 0.032, 0.032), (0.075, 0.035, 0.035), (0.077, 0.039, 0.039), (0.084, 0.038, 0.038)],
             n=8, twist=0, jitter=0.0)
    facet(kit, "G tub body", loft(t), [mt(kit, "cream"), pink], tub, bandmat=lambda b: 1 if b in (2, 3) else 0)
    blob(kit, "G scoop", mt(kit, "choc"), tub, (0, 0, 0.098), 0.043, (1, 1, 0.72), subdiv=1, rough=0.1, rot=(0.2, 0.3, 0.1))
    sprk = [pink, tape, mt(kit, "mint"), mt(kit, "sprk_b"), mt(kit, "cream")]
    for i in range(16):
        a = i * 2.4
        el = kit.rand.uniform(0.25, 1.2)
        n = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el) * 0.75 + 0.1)).normalized()
        p = Vector((0, 0, 0.098)) + Vector((n.x * 0.042, n.y * 0.042, n.z * 0.031))
        ob = kit.prim(f"G sprinkle {i}", 'box', (0.0035, 0.0035, 0.012), sprk[i % 5], tub, smooth=False)
        ob.location = p
        ob.rotation_euler = (kit.rand.uniform(0, 3), kit.rand.uniform(0, 3), a)


def setup(scene, stage):
    for name, loc, aim, energy, size, color in (("B warm key", (-2.4, -3.2, 3.0), (0.2, 0.5, 0.9), 700, 2.0, "#ffd2a0"),
                                                ("B cool rim", (2.2, 3.5, 2.6), (0.0, 0.5, 1.0), 500, 1.5, "#9fc4ff")):
        ld = bpy.data.lights.new(name, 'AREA')
        ld.energy = energy
        ld.size = size
        ld.color = hexc(color)[:3]
        ob = bpy.data.objects.new(name, ld)
        stage.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()


def post(path):
    subprocess.run(["magick", path, "(", "+clone", "-fill", "white", "-colorize", "100", "-background", "black",
                    "-vignette", "0x180-60-60", "+level", "55%,100%", ")", "-compose", "multiply", "-composite",
                    "-attenuate", "0.25", "+noise", "Gaussian", path], check=True)
