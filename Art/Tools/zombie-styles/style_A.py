"""Style A: Candy smooth. Soft-toy jellybean characters (Fall Guys / Gang Beasts look).
Bodies are one lathed bean (head and torso in one form) with color bands, clothing shells conformed to the bean,
skin-modifier noodle limbs, mitten hands, and metaball goo/puff FX."""
from common import *
import itertools

KEY = "A"
LABEL = "Candy smooth"
SHADER = 'candy'
WORLD = "#f3e9f2"
FLOOR = "#f6e3ef"

_ids = itertools.count(1)

DARK = "#2b2340"
SPRINKLE_COLS = ["#ff7fa8", "#8fc8ff", "#ffe08a", "#8fe3c9", "#c9a8ff", "#ffffff"]


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


def setup(scene, stage_collection):
    ld = bpy.data.lights.new("candy fill", 'AREA')
    ld.energy = 140
    ld.size = 4
    ld.color = hexc("#ffe6f2")[:3]
    ob = bpy.data.objects.new("candy fill", ld)
    stage_collection.objects.link(ob)
    ob.location = (-2.5, -4.0, 2.6)
    ob.rotation_euler = (Vector((0.4, 1.0, 0.9)) - ob.location).to_track_quat('-Z', 'Y').to_euler()


# ------------------------------------------------------------------ materials
def gloss(kit, name, hex_color, rough=0.12, coat=0.7, sss=0.15):
    key = ("gloss", name, hex_color)
    if key not in kit._mats:
        m = bpy.data.materials.new(f"ZD2 A {name}")
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes.get("Principled BSDF")
        p.inputs["Base Color"].default_value = hexc(hex_color)
        p.inputs["Roughness"].default_value = rough
        p.inputs["Coat Weight"].default_value = coat
        p.inputs["Coat Roughness"].default_value = 0.05
        p.inputs["Subsurface Weight"].default_value = sss
        m.diffuse_color = hexc(hex_color)
        kit._mats[key] = m
    return kit._mats[key]


def waffle_mat(kit):
    key = ("waffle",)
    if key not in kit._mats:
        m = bpy.data.materials.new("ZD2 A waffle")
        m.use_nodes = True
        nt = m.node_tree
        p = nt.nodes.get("Principled BSDF")
        p.inputs["Roughness"].default_value = 0.5
        p.inputs["Coat Weight"].default_value = 0.2
        tc = nt.nodes.new("ShaderNodeTexCoord")
        fac = None
        for ang in (45, -45):
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Rotation"].default_value = (math.radians(ang), 0, 0)
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            wv = nt.nodes.new("ShaderNodeTexWave")
            wv.bands_direction = 'Y'
            wv.inputs["Scale"].default_value = 17
            wv.inputs["Distortion"].default_value = 0
            nt.links.new(mp.outputs[0], wv.inputs["Vector"])
            if fac is None:
                fac = wv.outputs["Fac"]
            else:
                mul = nt.nodes.new("ShaderNodeMath")
                mul.operation = 'MINIMUM'
                nt.links.new(fac, mul.inputs[0])
                nt.links.new(wv.outputs["Fac"], mul.inputs[1])
                fac = mul.outputs[0]
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.12
        ramp.color_ramp.elements[0].color = hexc("#b9803f")
        ramp.color_ramp.elements[1].position = 0.3
        ramp.color_ramp.elements[1].color = hexc("#e9b872")
        nt.links.new(fac, ramp.inputs[0])
        nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.6
        bump.inputs["Distance"].default_value = 0.004
        nt.links.new(fac, bump.inputs["Height"])
        nt.links.new(bump.outputs[0], p.inputs["Normal"])
        m.diffuse_color = hexc("#e9b872")
        kit._mats[key] = m
    return kit._mats[key]


# ------------------------------------------------------------------ geometry helpers
def lathe(kit, name, prof, mats, parent, axis='Z', segs=32, ey=1.0, deform=None, mat_fn=None, subsurf=1):
    """Surface of revolution. prof: [(r, h)], r == 0 at an end makes a pole. axis 'Z': theta 0 faces -Y;
    axis 'Y': h runs along -Y... (h along Y, theta 0 faces +Z). deform(v, theta, h) -> v."""
    mats = mats if isinstance(mats, (list, tuple)) else [mats]
    bm = bmesh.new()
    rings = []
    for i, (r, h) in enumerate(prof):
        n = 1 if r < 1e-6 and i in (0, len(prof) - 1) else segs
        ring = []
        for j in range(n):
            th = 2 * math.pi * j / segs
            if axis == 'Z':
                v = Vector((r * math.sin(th), -ey * r * math.cos(th), h))
            else:
                v = Vector((r * math.sin(th), h, ey * r * math.cos(th)))
            if deform:
                v = deform(v, th, h)
            ring.append(bm.verts.new(v))
        rings.append(ring)
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        hm = (prof[i][1] + prof[i + 1][1]) / 2
        for j in range(segs):
            j2 = (j + 1) % segs
            if len(A) == 1:
                f = bm.faces.new((A[0], B[j], B[j2]))
            elif len(B) == 1:
                f = bm.faces.new((A[j], B[0], A[j2]))
            else:
                f = bm.faces.new((A[j], B[j], B[j2], A[j2]))
            if mat_fn:
                f.material_index = mat_fn(2 * math.pi * (j + 0.5) / segs, hm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, list(mats), parent)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    return ob


def grid(kit, name, rows, mat, parent, closed=False, subsurf=1, solid=0.0, skip=None):
    """Quad sheet from rows of points (equal length)."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in row] for row in rows]
    n = len(rows[0])
    for i in range(len(rows) - 1):
        for j in range(n if closed else n - 1):
            if skip and skip(i, j):
                continue
            j2 = (j + 1) % n
            bm.faces.new((vs[i][j], vs[i][j2], vs[i + 1][j2], vs[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if solid:
        so = ob.modifiers.new("Solidify", 'SOLIDIFY')
        so.thickness = solid
        so.offset = 0
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    return ob


def tube(kit, name, path, radius, mat, parent, closed=False, segs=8, subsurf=0, flat=1.0):
    """Swept round tube with rounded ends. radius: float or per-point list. flat squashes the cross-section."""
    path = [Vector(p) for p in path]
    radii = radius if isinstance(radius, (list, tuple)) else [radius] * len(path)
    n = len(path)
    tans = []
    for i in range(n):
        if closed:
            t = path[(i + 1) % n] - path[i - 1]
        else:
            t = path[min(i + 1, n - 1)] - path[max(i - 1, 0)]
        tans.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
    u = tans[0].cross(ref).normalized()
    frames = []
    for i in range(n):
        if i:
            u = (u - tans[i] * u.dot(tans[i])).normalized()
        w = tans[i].cross(u)
        frames.append((u, w))
    bm = bmesh.new()
    rings = []
    for i in range(n):
        u, w = frames[i]
        rings.append([bm.verts.new(path[i] + radii[i] * (math.cos(a) * u + flat * math.sin(a) * w))
                      for a in (2 * math.pi * k / segs for k in range(segs))])
    for i in range(n if closed else n - 1):
        A, B = rings[i], rings[(i + 1) % n]
        for k in range(segs):
            k2 = (k + 1) % segs
            bm.faces.new((A[k], A[k2], B[k2], B[k]))
    if not closed:
        for end, ring, sgn in ((path[0], rings[0], -1), (path[-1], rings[-1], 1)):
            t = tans[0] if sgn < 0 else tans[-1]
            r = radii[0] if sgn < 0 else radii[-1]
            pole = bm.verts.new(end + t * sgn * r * 0.9)
            for k in range(segs):
                bm.faces.new((ring[k], ring[(k + 1) % segs], pole))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    return ob


def meta(kit, name, elems, mat, parent, res=0.012, threshold=0.6):
    """Metaball blob cluster. elems: (co, radius) or (co, radius, (sx, sy, sz), direction)."""
    mb = bpy.data.metaballs.new(f"{name}{next(_ids)}")
    mb.resolution = mb.render_resolution = res
    mb.threshold = threshold
    for el in elems:
        e = mb.elements.new()
        e.co = el[0]
        e.radius = el[1]
        if len(el) > 2:
            e.type = 'ELLIPSOID'
            e.size_x, e.size_y, e.size_z = el[2]
            if len(el) > 3:
                e.rotation = Vector((1, 0, 0)).rotation_difference(Vector(el[3]).normalized())
    mb.materials.append(mat)
    return kit.link(f"{name.replace('.', '_')}{next(_ids)}", mb, parent)


def prim(kit, *a, **kw):
    """kit.prim with lighter default sphere tessellation (smooth shading hides it at this size)."""
    kw.setdefault('segments', 12)
    kw.setdefault('rings', 7)
    return kit.prim(*a, **kw)


def place(ob, p, n, spin=0.0):
    """Orient an object so local Z follows normal n (local Y toward world up)."""
    q = Vector(n).to_track_quat('Z', 'Y')
    if spin:
        q = q @ Euler((0, 0, math.radians(spin))).to_quaternion()
    ob.location = p
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = q
    return ob


def sprinkles(kit, name, items, parent, length=0.022, radius=0.0045):
    """items: (pos, dir, color index into SPRINKLE_COLS). One mesh, many capsule sprinkles."""
    bm = bmesh.new()
    for pos, d, ci in items:
        res = bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=4, radius=1)
        vs = res['verts']
        bmesh.ops.scale(bm, vec=Vector((radius, radius, length / 2)), verts=vs)
        q = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized())
        bmesh.ops.rotate(bm, matrix=q.to_matrix(), verts=vs)
        bmesh.ops.translate(bm, vec=Vector(pos), verts=vs)
        for f in {f for v in vs for f in v.link_faces}:
            f.material_index = ci
    mats = [kit.mat(f"sprinkle {c}", c) for c in SPRINKLE_COLS]
    return kit.mesh_from_bmesh(name, bm, mats, parent)


def catmull(pts, n=24):
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (Vector(P[k]) for k in (i - 1, i, i + 1, i + 2))
        for s in range(n):
            t = s / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(Vector(pts[-1]))
    return out


def smooth01(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


class Bean:
    """One continuous jellybean body (head + torso) defined by a (r, z) profile, with optional deformation.
    surf() returns points on the deformed surface so clothes and faces conform to it."""

    def __init__(self, ctrl, ey=0.86, deform=None, rings=34):
        self.dense = catmull(ctrl, 30)
        self.ey = ey
        self.deform = deform
        L = [0.0]
        for a, b in zip(self.dense, self.dense[1:]):
            L.append(L[-1] + (b - a).length)
        prof = []
        k = 0
        for i in range(rings + 1):
            s = L[-1] * i / rings
            while k < len(L) - 2 and L[k + 1] < s:
                k += 1
            t = (s - L[k]) / max(L[k + 1] - L[k], 1e-9)
            p = self.dense[k].lerp(self.dense[k + 1], t)
            prof.append((max(p.x, 0.0) if 0 < i < rings else 0.0, p.y))
        self.prof = prof

    def r_at(self, z):
        best = 0.0
        for a, b in zip(self.dense, self.dense[1:]):
            if min(a.y, b.y) <= z <= max(a.y, b.y) and a.y != b.y:
                best = max(best, a.x + (b.x - a.x) * (z - a.y) / (b.y - a.y))
        return best

    def top_z(self, rho):
        for p in reversed(self.dense):
            if p.x >= rho:
                return p.y
        return self.dense[0].y

    def _def(self, v, th, z):
        return self.deform(v, th, z) if self.deform else v

    def surf(self, th_deg, z, off=0.0):
        th = math.radians(th_deg)
        r = self.r_at(z)
        v = Vector(((r + off) * math.sin(th), -(self.ey * r + off) * math.cos(th), z))
        return self._def(v, th, z)

    def normal(self, th, z):
        dth = self.surf(th + 1.5, z) - self.surf(th - 1.5, z)
        dz = self.surf(th, z + 0.01) - self.surf(th, z - 0.01)
        return dth.cross(dz).normalized()

    def mesh(self, kit, name, mats, parent, mat_fn=None, segs=40):
        return lathe(kit, name, self.prof, mats, parent, 'Z', segs, self.ey,
                     (lambda v, th, h: self._def(v, th, h)) if self.deform else None, mat_fn, subsurf=0)

    def shell(self, kit, name, mat, parent, th0, th1, zb, zt, off, n_th=24, n_z=8, closed=False, solid=0.01,
              skip=None, subsurf=1):
        """Clothing sheet conformed to the body. zb/zt: functions of theta (deg) for bottom/top edges."""
        rows = []
        cnt = n_th if closed else n_th + 1
        ths = [th0 + (th1 - th0) * j / n_th for j in range(cnt)]
        for i in range(n_z + 1):
            t = i / n_z
            rows.append([self.surf(th, zb(th) + (zt(th) - zb(th)) * t, off) for th in ths])
        return grid(kit, name, rows, mat, parent, closed, subsurf, solid, skip)

    def feature(self, kit, name, kind, size, mat, parent, th, z, sink=0.0, spin=0.0, offset=(0, 0, 0)):
        """Small primitive stuck on the surface (eyes, cheeks), local Z = outward normal."""
        ob = prim(kit, name, kind, size, mat, parent, offset=offset, segments=16, rings=9)
        n = self.normal(th, z)
        return place(ob, self.surf(th, z) - n * sink, n, spin)


def mitten(kit, name, mat, parent, loc, rot, s=1.0):
    """Soft mitten: palm blob + thumb, built around its own pivot (fingers along local -Y)."""
    piv = kit.empty(name, parent, loc, rot)
    kit.skin(name + " palm", [(0, 0.02 * s, 0), (0, -0.03 * s, 0.0), (0, -0.05 * s, -0.005 * s)], [(0, 1), (1, 2)],
             [(0.04 * s, 0.032 * s), (0.05 * s, 0.036 * s), (0.04 * s, 0.03 * s)], mat, piv)
    kit.skin(name + " thumb", [(0.0, 0.0, 0.01 * s), (0.0, -0.03 * s, 0.05 * s)], [(0, 1)],
             [0.02 * s, 0.017 * s], mat, piv)
    return piv


# ------------------------------------------------------------------ gun
def scoop(kit, name, mat, parent, r=0.044, base=0.0, ruffle=8, seed=0.0):
    """Ice cream scoop with a ruffled skirt, axis Z, sitting on z=base."""
    prof = [(0, base - 0.002), (r * 0.98, base), (r * 1.14, base + 0.18 * r), (r * 1.08, base + 0.36 * r),
            (r * 1.03, base + 0.62 * r), (r * 0.9, base + 1.05 * r), (r * 0.62, base + 1.42 * r),
            (r * 0.3, base + 1.62 * r), (0, base + 1.68 * r)]

    def dfm(v, th, h):
        w = 1 + 0.07 * math.sin(ruffle * th + seed) * (1 - smooth01(base + 0.4 * r, base + 0.9 * r, h)) \
            + 0.03 * math.sin(3 * th + seed * 2) * smooth01(base + 0.5 * r, base + 1.5 * r, h)
        return Vector((v.x * w, v.y * w, v.z))
    return lathe(kit, name, prof, mat, parent, 'Z', 16, 1.0, dfm)


def build_gun(kit, root):
    mint = kit.mat("gun mint", "#8fe3c9")
    pink = kit.mat("gun pink", "#ff9cc4")
    white = kit.mat("gun white", "#ffffff")
    choc = kit.mat("choc", "#7a4a36")
    dark = kit.mat("gun dark", "#5b3d5e")

    # main body: a chunky soft bulb along Y, white racing band
    body_prof = [(0, 0.118), (0.026, 0.115), (0.04, 0.1), (0.048, 0.075), (0.05, 0.04), (0.049, 0.0),
                 (0.046, -0.04), (0.04, -0.07), (0.034, -0.088), (0.03, -0.1), (0, -0.104)]
    lathe(kit, "gun body", body_prof, [mint, white], root, 'Y', 16, 1.05,
          mat_fn=lambda th, h: 1 if -0.018 < h < 0.002 else 0)
    # rear pink cap
    prim(kit, "gun rear cap", 'sphere', (0.026, 0.02, 0.026), pink, root, offset=(0, 0.114, 0.004))
    # waffle cone muzzle with a vanilla rim
    cone_prof = [(0.03, -0.085), (0.034, -0.1), (0.045, -0.15), (0.062, -0.198), (0.064, -0.206),
                 (0.055, -0.208), (0.046, -0.196), (0, -0.17)]
    lathe(kit, "gun waffle cone", cone_prof, waffle_mat(kit), root, 'Y', 16, 1.0)
    rim = [Vector((0.063 * math.sin(a) * (1 + 0.06 * math.sin(7 * a)), -0.204, 0.063 * math.cos(a)))
           for a in (2 * math.pi * k / 28 for k in range(28))]
    tube(kit, "gun cone rim", rim, 0.011, white, root, closed=True)
    # strawberry ammo peeking out of the cone
    prim(kit, "gun cone ammo", 'sphere', (0.04, 0.03, 0.04), pink, root, offset=(0, -0.19, 0))
    # pint-tub magazine on top
    tub_prof = [(0, 0.03), (0.034, 0.03), (0.037, 0.05), (0.041, 0.085), (0.044, 0.096), (0.046, 0.099),
                (0.042, 0.101), (0, 0.1)]
    tub = lathe(kit, "gun pint tub", tub_prof, [white, pink], root, 'Z', 16, 1.0,
                mat_fn=lambda th, h: 1 if 0.052 < h < 0.08 else 0)
    tub.location = (0, 0.012, 0)
    tube(kit, "gun tub collar", [Vector((0.037 * math.sin(a), 0.012 + 0.037 * math.cos(a), 0.04))
                                 for a in (2 * math.pi * k / 20 for k in range(20))], 0.008, mint, root, closed=True)
    sc = scoop(kit, "gun choc scoop", choc, root, 0.042, 0.094, 8, 1.3)
    sc.location = (0, 0.012, 0)
    rnd = kit.rand
    items = []
    for i in range(13):
        th = rnd.uniform(0, 2 * math.pi)
        ph = rnd.uniform(0.15, 1.15)
        n = Vector((math.sin(ph) * math.cos(th), math.sin(ph) * math.sin(th), math.cos(ph)))
        pos = Vector((0, 0.012, 0.094 + 0.042 * 0.62)) + Vector((n.x * 0.045, n.y * 0.045, n.z * 0.044))
        tang = n.cross(Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))))
        items.append((pos, tang, i % len(SPRINKLE_COLS)))
    sprinkles(kit, "gun sprinkles", items, root, 0.016, 0.0036)
    # grip: pink soft paddle with finger bumps, raked back
    grip_prof = [(0, 0.012), (0.02, 0.008), (0.026, -0.01), (0.027, -0.05), (0.028, -0.09), (0.025, -0.11),
                 (0.016, -0.122), (0, -0.124)]

    def grip_dfm(v, th, h):
        bump = 0.0
        if v.y < 0:
            bump = 0.006 * max(0.0, math.sin((h + 0.02) / 0.1 * 3 * math.pi)) * (-v.y / 0.03)
        return Vector((v.x * 0.82, v.y * 1.2 - bump, v.z))
    grip = lathe(kit, "gun grip", grip_prof, pink, root, 'Z', 14, 1.0, grip_dfm)
    grip.location = (0, 0.058, -0.022)
    grip.rotation_euler = (math.radians(17), 0, 0)
    prim(kit, "gun grip cap", 'sphere', (0.022, 0.032, 0.012), mint, root,
             offset=(0, 0.058 + 0.12 * math.sin(math.radians(17)), -0.022 - 0.12 * math.cos(math.radians(17))),
             rot=(17, 0, 0))
    # trigger + guard
    tube(kit, "gun trigger", [(0, 0.012, -0.04), (0, 0.0, -0.058), (0, 0.006, -0.076)],
         [0.009, 0.0085, 0.008], pink, root, segs=8, subsurf=2)
    tube(kit, "gun guard", [(0, -0.03, -0.035), (0, -0.04, -0.07), (0, -0.026, -0.1), (0, 0.0, -0.11),
                            (0, 0.04, -0.104)], 0.008, mint, root, segs=8, subsurf=2)
    # front sight bead and a candy dial on the side
    prim(kit, "gun sight", 'sphere', (0.011, 0.011, 0.011), pink, root, offset=(0, -0.07, 0.042))
    for sx in (1, -1):
        prim(kit, f"gun dial {sx}", 'cyl', (0.016, 0.016, 0.01), white, root, offset=(sx * 0.047, 0.05, 0.004),
                 rot=(0, 90, 0), segments=20)
        prim(kit, f"gun dial dot {sx}", 'sphere', (0.007, 0.007, 0.007), pink, root, offset=(sx * 0.052, 0.05, 0.004))
    prim(kit, "gun muzzle ring", 'cyl', (0.034, 0.034, 0.012), pink, root, offset=(0, -0.088, 0), rot=(90, 0, 0),
             segments=24)


# ------------------------------------------------------------------ player
def build_player(kit, root):
    skin = kit.mat("skin", "#ffd0b0")
    shirt = kit.mat("shirt", "#8fc8ff")
    pants = kit.mat("pants", "#5e6fb0")
    pink = kit.mat("accent", "#ff7fa8")
    white = kit.mat("white", "#fdfbff")
    dark = kit.mat("eye dark", DARK)
    blush = kit.mat("blush", "#ff9fb8")

    bean = Bean([(0, 0.25), (0.16, 0.265), (0.27, 0.33), (0.31, 0.45), (0.315, 0.6), (0.298, 0.74),
                 (0.292, 0.82), (0.31, 0.95), (0.32, 1.08), (0.29, 1.22), (0.2, 1.33), (0, 1.37)], rings=44)
    bean.mesh(kit, "player bean", [pants, shirt, skin], root,
              mat_fn=lambda th, z: 0 if z < 0.42 else (1 if z < 0.8 else 2), segs=40)

    # face
    for sx in (1, -1):
        th = 21 * sx
        bean.feature(kit, f"eye white {sx}", 'sphere', (0.066, 0.082, 0.03), white, root, th, 1.09, 0.006)
        bean.feature(kit, f"pupil {sx}", 'sphere', (0.038, 0.05, 0.02), dark, root, th - 3 * sx, 1.085, -0.018)
        bean.feature(kit, f"eye shine {sx}", 'sphere', (0.012, 0.014, 0.01), white, root, th - 5 * sx, 1.105, -0.036)
        bean.feature(kit, f"cheek {sx}", 'sphere', (0.04, 0.026, 0.012), blush, root, 36 * sx, 0.99, 0.004)
        brow = [bean.surf(th + sx * a, 1.19 + 0.008 * a / 10 - 0.004 * (a / 10) ** 2, 0.008) for a in (-12, -4, 4, 12)]
        tube(kit, f"brow {sx}", brow, 0.009, dark, root, segs=8)
    smile = [bean.surf(a, 0.975 + 0.028 * (a / 13) ** 2, 0.004) for a in range(-13, 14, 2)]
    tube(kit, "smile", smile, 0.009, dark, root, segs=8)

    # soda-jerk paper hat: garrison boat shape conformed to the dome, pink band
    rows = []
    n = 16
    for k in range(5):
        t = k / 4
        row = []
        for j in range(n):
            a = 2 * math.pi * j / n
            ax, ay = 0.15 * (1 - 0.92 * t ** 1.3), 0.215 * (1 - 0.1 * t)
            x, y = ax * math.sin(a), -ay * math.cos(a)
            rho = math.sqrt(x * x + (y / bean.ey) ** 2)
            zb = bean.top_z(rho) - 0.02
            ridge = 0.16 - 0.035 * math.cos(a) ** 2 * 0 - 0.03 * (1 - abs(math.cos(a)))
            row.append(Vector((x, y, zb + ridge * t + 0.012 * t * (1 - t))))
        rows.append(row)
    hat = grid(kit, "paper hat", rows, white, root, closed=True, subsurf=1, solid=0.01)
    band = [Vector((r.x * 1.06, r.y * 1.04, r.z + 0.035)) for r in rows[0]]
    tube(kit, "hat band", band, 0.013, pink, root, closed=True)
    prim(kit, "hat scoop badge", 'sphere', (0.03, 0.012, 0.03), pink, root, offset=(0.0, -0.205, 1.35))

    # collar bow tie
    for sx in (1, -1):
        lobe = prim(kit, f"bow lobe {sx}", 'sphere', (0.05, 0.025, 0.034), pink, root, rot=(0, -12 * sx, 0))
        lobe.location = bean.surf(0, 0.8, 0.02) + Vector((0.045 * sx, 0, 0))
    prim(kit, "bow knot", 'sphere', (0.02, 0.02, 0.022), pink, root,
             offset=tuple(bean.surf(0, 0.8, 0.03)))

    # apron with scalloped hem, pocket, neck loop and back ties
    bean.shell(kit, "apron", white, root, -64, 64, lambda th: 0.33 + 0.015 * math.cos(math.radians(th) * 9),
               lambda th: 0.745 - 0.03 * (th / 64) ** 2, 0.012, 18, 5)
    bean.shell(kit, "apron pocket", pink, root, -20, 20, lambda th: 0.43, lambda th: 0.53, 0.028, 6, 2)
    neck = [bean.surf(th, 0.72 + 0.12 * smooth01(55, 120, abs(((th + 180) % 360) - 180)), 0.016)
            for th in range(55, 306, 10)]
    tube(kit, "apron neck loop", neck, 0.011, white, root)
    tie = [bean.surf(th, 0.4, 0.016) for th in range(60, 301, 10)]
    tube(kit, "apron waist tie", tie, 0.011, white, root)
    back = bean.surf(180, 0.4, 0.03)
    for sx in (1, -1):
        prim(kit, f"apron bow {sx}", 'sphere', (0.05, 0.02, 0.032), white, root,
                 offset=tuple(back + Vector((0.045 * sx, 0, 0))), rot=(0, 15 * sx, 0))

    # cooler backpack with spare pints + straps
    prim(kit, "cooler", 'box', (0.46, 0.22, 0.38), pink, root, offset=(0, 0.37, 0.66), bevel=0.05, bevel_segments=4)
    prim(kit, "cooler lid", 'box', (0.48, 0.24, 0.07), white, root, offset=(0, 0.37, 0.86), bevel=0.03,
             bevel_segments=3)
    tube(kit, "cooler handle", [(-0.1, 0.37, 0.89), (-0.08, 0.37, 0.95), (0.08, 0.37, 0.95), (0.1, 0.37, 0.89)],
         0.012, white, root)
    for i, (px, lid) in enumerate(((-0.17, "#ff9cc4"), (0.17, "#8fe3c9"))):
        prim(kit, f"spare pint {i}", 'cyl', (0.05, 0.05, 0.1), white, root, offset=(px, 0.37, 0.94), taper=1.12,
                 segments=20, bevel=0.008)
        prim(kit, f"spare pint lid {i}", 'cyl', (0.058, 0.058, 0.02), kit.mat(f"lid {lid}", lid), root,
                 offset=(px, 0.37, 0.995), segments=20, bevel=0.006)
    for sx in (1, -1):
        path = [bean.surf(sx * th, z, 0.018) for th, z in
                ((160, 0.56), (128, 0.76), (95, 0.84), (55, 0.8), (38, 0.64), (42, 0.5), (80, 0.47), (128, 0.5))]
        tube(kit, f"strap {sx}", path, 0.016, pink, root, flat=0.55)

    # legs and shoes (stubby)
    for sx in (1, -1):
        kit.skin(f"leg {sx}", [(0.13 * sx, 0, 0.34), (0.135 * sx, -0.01, 0.18), (0.14 * sx, -0.01, 0.08)],
                 [(0, 1), (1, 2)], [0.085, 0.07, 0.06], pants, root)
        prim(kit, f"shoe {sx}", 'sphere', (0.085, 0.12, 0.065), pink, root, offset=(0.14 * sx, -0.04, 0.062))
        prim(kit, f"shoe sole {sx}", 'sphere', (0.088, 0.124, 0.03), white, root, offset=(0.14 * sx, -0.04, 0.03))

    # right arm (-X) raised, aiming the gun
    sh = bean.surf(-88, 0.64, -0.05)
    hand = Vector((-0.33, -0.5, 0.82))
    kit.skin("arm right", [tuple(sh), (-0.36, -0.2, 0.74), (-0.34, -0.42, 0.8)], [(0, 1), (1, 2)],
             [0.06, 0.05, 0.045], skin, root)
    kit.skin("sleeve right", [tuple(sh), (-0.33, -0.08, 0.7)], [(0, 1)], [0.075, 0.07], shirt, root)
    gun = kit.empty("held gun", root, tuple(hand - Vector((0, 0.072, -0.074)) * 1.15), scale=(1.15, 1.15, 1.15))
    build_gun(kit, gun)
    mitten(kit, "mitten right", skin, root, tuple(hand + Vector((0, 0.01, 0.0))), (0, 0, 0))
    # left arm relaxed
    sh = bean.surf(88, 0.64, -0.05)
    kit.skin("arm left", [tuple(sh), (0.39, -0.03, 0.52), (0.42, -0.06, 0.42)], [(0, 1), (1, 2)],
             [0.06, 0.05, 0.045], skin, root)
    kit.skin("sleeve left", [tuple(sh), (0.35, -0.01, 0.6)], [(0, 1)], [0.075, 0.07], shirt, root)
    mitten(kit, "mitten left", skin, root, (0.43, -0.07, 0.39), (-80, 0, 10))


# ------------------------------------------------------------------ zombie
DENT = (32.0, 1.25)  # theta, z of the head dent


def zombie_deform(bean_ref):
    def dfm(v, th, z):
        v = Vector(v)
        # dent: push in around DENT point (computed on the undeformed bean)
        d0 = bean_ref['dent']
        if d0 is not None:
            d = (v - d0).length
            if d < 0.14:
                k = (1 - (d / 0.14) ** 2) ** 2
                radial = Vector((v.x, v.y, 0.4 * (v.z - 1.05)))
                v -= radial.normalized() * 0.065 * k
        # sagging droop on the -X side of the belly
        side = max(0.0, -math.sin(th))
        g = math.exp(-((z - 0.5) / 0.17) ** 2)
        v.x -= 0.075 * g * side ** 1.5
        v.z -= 0.035 * g * side
        # lopsided head leaning to +X, drooping on its -X side
        h = smooth01(0.8, 1.42, z)
        v.x += 0.05 * h
        v.z -= 0.045 * h * side
        return v
    return dfm


def zombie_arm(kit, name, parent, loc, direction, mats, torn=False, droop=0.0, twist=0.0):
    """Arm built along local -Y, oriented so it points along `direction` (parent space)."""
    skin, shirt, goo, bone = mats
    q = Vector((0, -1, 0)).rotation_difference(Vector(direction).normalized()) \
        @ Euler((0, math.radians(twist), 0)).to_quaternion()
    piv = kit.empty(name, parent, loc, [math.degrees(a) for a in q.to_euler()])
    kit.skin(name + " noodle", [(0, 0.02, 0), (0.01, -0.17, -0.03 - droop), (0.0, -0.33, -0.07 - droop * 1.6)],
             [(0, 1), (1, 2)], [0.058, 0.05, 0.045], skin, piv)

    def jag(v, th, h):
        k = 1 + 0.12 * math.sin(5 * th) * smooth01(-0.1, -0.13, h)
        return Vector((v.x * k, v.y + (0.02 * math.sin(4 * th + 1) if h < -0.1 else 0), v.z * k))
    lathe(kit, name + " sleeve", [(0.04, 0.03), (0.075, 0.0), (0.078, -0.06), (0.074, -0.12), (0.06, -0.125),
                                  (0.05, -0.1), (0.045, -0.04)], shirt, piv, 'Y', 14, 1.0, jag)
    mitten(kit, name + " mitten", skin, piv, (0.0, -0.37, -0.075 - droop * 1.6), (-15, 0, 0), 1.05)
    if torn:
        meta(kit, name + "goo", [((0, 0.03, 0), 0.12), ((0.01, 0.08, 0.01), 0.08), ((0.02, 0.13, -0.01), 0.055),
                                 ((-0.03, 0.05, 0.05), 0.06)], goo, piv, res=0.008)
        prim(kit, name + " bone", 'sphere', (0.024, 0.03, 0.024), bone, piv, offset=(0.014, 0.085, 0.025))
        prim(kit, name + " bone b", 'sphere', (0.024, 0.03, 0.024), bone, piv, offset=(-0.016, 0.088, 0.027))
    return piv


def build_zombie(kit, root, hit=False):
    skin = kit.mat("zskin", "#a9dc8e")
    skin_dk = kit.mat("zskin dark", "#86c070")
    shirt = kit.mat("zshirt", "#ffe08a")
    pants = kit.mat("zpants", "#9a86d6")
    white = kit.mat("white", "#fdfbff")
    dark = kit.mat("eye dark", DARK)
    mouth_m = kit.mat("zmouth", "#5a2f5e")
    brain = gloss(kit, "brain", "#ff8fb8", 0.25, 0.5, 0.2)
    goo = gloss(kit, "goo", "#ff4f7a")
    icecream = kit.mat("strawberry", "#ffb3cf")
    bone = kit.mat("bone", "#fff6e6")
    shoe_m = kit.mat("zshoe", "#6b5a9e")

    ref = {'dent': None}
    bean = Bean([(0, 0.23), (0.17, 0.245), (0.29, 0.32), (0.335, 0.45), (0.335, 0.6), (0.305, 0.75),
                 (0.292, 0.84), (0.31, 0.97), (0.312, 1.1), (0.275, 1.25), (0.17, 1.37), (0, 1.41)],
                deform=zombie_deform(ref), rings=48)
    # undeformed dent center
    th = math.radians(DENT[0])
    r = bean.r_at(DENT[1])
    ref['dent'] = Vector((r * math.sin(th), -bean.ey * r * math.cos(th), DENT[1]))

    # pose
    if hit:
        torso_rot, head_tw = (-16, -10, 14), 0
        arm_r_dir = (-0.6, -0.35, 0.85)
    else:
        torso_rot, head_tw = (17, 4, -6), 0
        arm_r_dir = (-0.3, -1, 0.12)
    torso = kit.empty("zombie torso", root, (0, 0, 0.3), torso_rot)
    space = kit.empty("zombie body space", torso, (0, 0, -0.3))
    bean.mesh(kit, "zombie bean", [pants, skin], space, mat_fn=lambda t, z: 0 if z < 0.4 else 1, segs=40)

    # torn shirt shell with jagged hem, ragged collar, and a hole
    def hem(thd):
        return 0.45 + 0.035 * abs(((thd * 7 / 360.0) % 1.0) - 0.5) * 2 + 0.02 * math.sin(math.radians(thd) * 3)

    def collar(thd):
        return 0.83 + 0.025 * abs(((thd * 9 / 360.0) % 1.0) - 0.5) * 2

    bean.shell(kit, "zombie shirt", shirt, space, -180, 180, hem, collar, 0.01, 48, 9, closed=True, solid=0.012,
               skip=lambda i, j: (i in (4, 5) and j in (18, 19)) or (i == 3 and j == 30), subsurf=0)

    # brain peeking from the dent
    c = bean.surf(DENT[0], DENT[1], -0.02)
    nrm = bean.normal(DENT[0], DENT[1])
    u = nrm.cross(Vector((0, 0, 1))).normalized()
    w = u.cross(nrm)
    els = [(c, 0.12)]
    for k in range(10):
        a = 2 * math.pi * k / 10
        els.append((c + (u * math.cos(a) + w * math.sin(a)) * 0.065 + nrm * 0.02, 0.07))
    for k in range(5):
        els.append((c + u * (k - 2) * 0.03 + nrm * 0.05 + w * 0.025 * (-1) ** k, 0.06))
    meta(kit, "zbrain", els, brain, space, res=0.015)
    groove = gloss(kit, "brain groove", "#e2588e", 0.3, 0.4, 0.1)

    def dome(x, y):
        return c + u * x + w * y + nrm * (0.02 + 0.062 * math.sqrt(max(0.0, 1 - (x * x + y * y) / 0.11 ** 2)))
    tube(kit, "brain midline", [dome(0, t / 10 * 0.085) for t in range(-10, 11, 2)], 0.006, groove, space, segs=6)
    for sx in (1, -1):
        for k, y0 in enumerate((-0.035, 0.03)):
            tube(kit, f"brain gyrus {sx} {k}",
                 [dome(sx * (0.025 + 0.012 * math.sin(t * 1.9 + k)), y0 + t * 0.011) for t in range(-3, 4)],
                 0.005, groove, space, segs=6)
    rim = [bean.surf(DENT[0] + math.degrees(0.12 * math.cos(a) / 0.3), DENT[1] + 0.11 * math.sin(a), 0.004)
           for a in (2 * math.pi * k / 16 for k in range(16))]
    tube(kit, "dent rim", rim, 0.012, skin_dk, space, closed=True)

    # face: swollen right eye, small droopy left eye, crooked mouth with a tooth
    bean.feature(kit, "swollen eye", 'sphere', (0.088, 0.1, 0.06), white, space, -22, 1.07, 0.0)
    bean.feature(kit, "swollen pupil", 'sphere', (0.022, 0.024, 0.012), dark, space, -17, 1.05, -0.058)
    bean.feature(kit, "swollen eye bag", 'sphere', (0.08, 0.035, 0.035), skin_dk, space, -22, 0.975, 0.0)
    bean.feature(kit, "small eye", 'sphere', (0.04, 0.042, 0.02), white, space, 22, 1.08, 0.004)
    bean.feature(kit, "small pupil", 'sphere', (0.02, 0.022, 0.012), dark, space, 21, 1.075, -0.016)
    bean.feature(kit, "small eye lid", 'sphere', (0.05, 0.03, 0.03), skin_dk, space, 22, 1.11, 0.004, spin=-14)
    bean.feature(kit, "mouth", 'sphere', (0.07, 0.03, 0.02), mouth_m, space, 3, 0.94, 0.006, spin=-9)
    bean.feature(kit, "tooth", 'box', (0.022, 0.024, 0.02), bone, space, -4, 0.955, -0.006, spin=-9)
    # band-aid on the cheek, stitches on the sagging side
    bean.feature(kit, "bandaid", 'box', (0.07, 0.03, 0.012), kit.mat("bandaid", "#ffc9a6"), space, 42, 0.98,
                 0.002, spin=30)
    for k in range(3):
        bean.feature(kit, f"stitch {k}", 'box', (0.008, 0.05, 0.008), dark, space, -50 - 9 * k, 1.2 - 0.03 * k,
                     -0.006, spin=-20)
    tube(kit, "stitch line", [bean.surf(-41 - 9 * k, 1.23 - 0.03 * k, 0.003) for k in range(0, 5)], 0.005,
         dark, space, segs=6)

    # strawberry ice cream splat on the chest with drips and a little waffle cone stuck in it
    sp_th, sp_z = 30, 0.66
    rows = [[bean.surf(sp_th, sp_z, 0.022)] * 18]
    for ring in (0.35, 0.7, 1.0):
        row = []
        for j in range(18):
            a = 2 * math.pi * j / 18
            R = 0.085 * ring * (1 + 0.28 * math.sin(5 * a + 0.7) + 0.1 * math.sin(3 * a))
            row.append(bean.surf(sp_th + math.degrees(R * math.cos(a) / 0.31), sp_z + R * math.sin(a),
                                 0.022 - 0.013 * ring ** 2))
        rows.append(row)
    grid(kit, "zombie splat", rows, icecream, space, closed=True, subsurf=1, solid=0.008)
    for k, (dt, L) in enumerate(((-6, 0.1), (5, 0.06))):
        drip = [bean.surf(sp_th + dt, sp_z - 0.06 - s * L, 0.014) for s in (0, 0.5, 1)]
        tube(kit, f"splat drip {k}", drip, [0.016, 0.013, 0.018], icecream, space, segs=8)
    cone = prim(kit, "splat cone", 'cone', (0.03, 0.03, 0.1), waffle_mat(kit), space, offset=(0, 0, 0.05),
                    taper=0.05, segments=16)
    place(cone, bean.surf(sp_th + 4, sp_z + 0.02, 0.0), bean.normal(sp_th + 4, sp_z + 0.02))
    cone.rotation_quaternion = cone.rotation_quaternion @ Euler((math.radians(25), 0, 0)).to_quaternion()

    # arms on their own pivots
    mats = (skin, shirt, goo, bone)
    sh_r = bean.surf(-90, 0.66, -0.03)
    sh_l = bean.surf(90, 0.68, -0.03)
    zombie_arm(kit, "zombie arm right", space, tuple(sh_r), arm_r_dir, mats, droop=0.02, twist=-10)
    if not hit:
        zombie_arm(kit, "zombie arm left", space, tuple(sh_l), (0.35, -1, 0.3), mats, twist=10)
    else:
        M = Matrix.Translation((0, 0, 0.3)) @ Euler([math.radians(a) for a in torso_rot]).to_matrix().to_4x4() \
            @ Matrix.Translation((0, 0, -0.3))
        sh_world = M @ sh_l
        fly = sh_world + Vector((0.4, -0.28, 0.4))
        zombie_arm(kit, "zombie arm left flying", root, tuple(fly), (0.75, -0.3, 0.55), mats, torn=True, twist=70)
        build_hit_fx(kit, root, space, bean, sh_l, sh_world, fly, goo, white)

    # legs on their own pivots: one stepping, one dragging and turned in
    if hit:
        legs = {1: ((-28, 0, 6), 0.3), -1: ((14, -6, -8), 0.31)}
    else:
        legs = {1: ((-18, 0, 4), 0.315), -1: ((16, 8, -14), 0.31)}
    for sx in (1, -1):
        rot, L = legs[sx]
        piv = kit.empty(f"zombie leg {sx}", root, (0.135 * sx, 0, 0.32), rot)
        kit.skin(f"zombie leg {sx} noodle", [(0, 0, 0.04), (0.005 * sx, 0, -0.14), (0, 0, -L + 0.07)],
                 [(0, 1), (1, 2)], [0.088, 0.075, 0.062], pants, piv)
        lathe(kit, f"zombie leg {sx} cuff", [(0.06, -L + 0.2), (0.078, -L + 0.17), (0.084, -L + 0.11),
                                              (0.07, -L + 0.1), (0.055, -L + 0.13)], pants, piv, 'Z', 14, 1.0,
              lambda v, th, h: Vector((v.x, v.y, v.z + (0.022 * math.sin(5 * th + sx) if h < -L + 0.12 else 0))))
        if sx == 1:
            prim(kit, f"zombie shoe {sx}", 'sphere', (0.085, 0.125, 0.06), shoe_m, piv, offset=(0, -0.04, -L + 0.04))
        else:
            prim(kit, f"zombie foot {sx}", 'sphere', (0.075, 0.11, 0.055), skin, piv, offset=(0, -0.03, -L + 0.045))
            for t in range(3):
                prim(kit, f"zombie toe {t}", 'sphere', (0.022, 0.024, 0.022), skin, piv,
                         offset=(-0.035 + 0.035 * t, -0.13, -L + 0.03))


# ------------------------------------------------------------------ hit FX
def teardrops(kit, name, items, mat, parent):
    """Glossy goo drops: items (pos, flight direction, radius). Round head leads, tail trails."""
    prof = [(0, -1.0), (0.62, -0.82), (0.95, -0.42), (1.0, 0.0), (0.82, 0.5), (0.5, 1.05), (0.2, 1.6), (0, 1.95)]
    bm = bmesh.new()
    for pos, d, r in items:
        rings = []
        for rr, h in prof:
            if rr == 0:
                rings.append([bm.verts.new((0, 0, h * r))])
            else:
                rings.append([bm.verts.new((rr * r * math.cos(a), rr * r * math.sin(a), h * r))
                              for a in (2 * math.pi * k / 12 for k in range(12))])
        for A, B in zip(rings, rings[1:]):
            for k in range(12):
                k2 = (k + 1) % 12
                if len(A) == 1:
                    bm.faces.new((A[0], B[k2], B[k]))
                elif len(B) == 1:
                    bm.faces.new((A[k], A[k2], B[0]))
                else:
                    bm.faces.new((A[k], A[k2], B[k2], B[k]))
        vs = [v for ring in rings for v in ring]
        q = Vector((0, 0, -1)).rotation_difference(Vector(d).normalized())
        bmesh.ops.rotate(bm, matrix=q.to_matrix(), verts=vs)
        bmesh.ops.translate(bm, vec=Vector(pos), verts=vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    sub = ob.modifiers.new("Subdivision", 'SUBSURF')
    sub.levels = sub.render_levels = 1
    return ob


def build_hit_fx(kit, root, space, bean, sh_local, sh, fly, goo, white):
    rnd = kit.rand
    vanilla = kit.mat("vanilla", "#fff3dc")
    flavors = [kit.mat("strawberry", "#ffb3cf"), kit.mat("mint ice", "#a8f0d8"), vanilla,
               kit.mat("choc", "#7a4a36")]
    goo_floor = gloss(kit, "goo floor", "#ff5a84", 0.08, 0.9, 0.1)
    puff = kit.mat("puff", "#ffffff")

    # stump goo on the body (in body space so it follows the torso)
    meta(kit, "stumpgoo", [(sh_local + Vector((0.03, 0, 0)), 0.16), (sh_local + Vector((0.09, -0.03, 0.05)), 0.1),
                           (sh_local + Vector((0.07, 0.04, -0.06)), 0.09),
                           (sh_local + Vector((0.06, -0.06, -0.14)), 0.06, (1, 1, 2.0))], goo, space, res=0.01)

    # gooey strand from stump to the flying arm, beading up
    els = []
    for k in range(11):
        t = (k + 1) / 12
        p = sh.lerp(fly, t) + Vector((0, 0, 0.08 * math.sin(math.pi * t)))
        els.append((p, (0.085 if k % 2 else 0.06) * (1 - 0.45 * t)))
    meta(kit, "goostrand", els, goo, root, res=0.008)

    # burst of goo drops flying out
    items = []
    for k in range(34):
        d = Vector((rnd.uniform(0.1, 1.0), rnd.uniform(-1.0, 0.3), rnd.uniform(-0.4, 1.0))).normalized()
        items.append((sh + d * rnd.uniform(0.18, 0.85), d, rnd.uniform(0.014, 0.034)))
    for k in range(8):  # drops raining down onto the floor splats
        p = Vector((rnd.uniform(0.3, 0.95), rnd.uniform(-0.6, 0.1), rnd.uniform(0.15, 0.6)))
        items.append((p, Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), -1)), rnd.uniform(0.016, 0.026)))
    teardrops(kit, "goo drops", items, goo, root)

    # ice cream chunks flying
    for k, (off, r) in enumerate((((0.55, -0.15, 0.25), 0.07), ((0.3, -0.5, 0.48), 0.06),
                                  ((0.78, 0.05, 0.62), 0.055), ((0.12, -0.32, 0.72), 0.05),
                                  ((0.66, -0.45, 0.02), 0.055), ((0.95, -0.25, 0.3), 0.045))):
        piv = kit.empty(f"chunk {k}", root, tuple(sh + Vector(off)),
                        (rnd.uniform(-60, 60), rnd.uniform(-60, 60), rnd.uniform(0, 360)))
        scoop(kit, f"chunk scoop {k}", flavors[k % 4], piv, r, -r * 0.8, 8, k * 1.7)

    # soft white puff clouds
    for k, (off, s) in enumerate((((0.18, 0.12, 0.2), 1.15), ((0.5, 0.08, 0.6), 0.9), ((0.8, 0.0, 0.2), 0.8),
                                  ((0.38, -0.3, -0.05), 0.7))):
        c = sh + Vector(off)
        els = [(c, 0.2 * s)]
        for j in range(7):
            a = 2 * math.pi * j / 7 + k
            els.append((c + Vector((math.cos(a) * 0.13 * s, math.sin(a) * 0.06 * s, math.sin(a * 1.3 + 0.5) * 0.1 * s)),
                        rnd.uniform(0.13, 0.17) * s))
        meta(kit, f"puff{k}", els, puff, root, res=0.016)

    # swoosh motion arcs around the spinning arm
    for k in range(2):
        arc = []
        for s in range(12):
            a = math.radians(-20 + 11 * s + 180 * k)
            arc.append(fly + Vector((0.3 * math.cos(a), 0.08 * math.sin(a), 0.3 * math.sin(a))))
        tube(kit, f"swoosh {k}", arc, [0.004 + 0.014 * math.sin(math.pi * s / 11) for s in range(12)], white, root,
             segs=8)

    # sprinkle confetti
    items = []
    for k in range(110):
        d = Vector((rnd.uniform(-0.2, 1.0), rnd.uniform(-1.0, 0.3), rnd.uniform(-0.4, 1.0))).normalized()
        p = sh + d * rnd.uniform(0.15, 1.0)
        items.append((p, Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))), k % 6))
    for k in range(40):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0.25, 1.0)
        items.append((Vector((math.cos(a) * rr + 0.2, math.sin(a) * rr - 0.2, 0.006)),
                      Vector((math.cos(a * 3), math.sin(a * 3), 0)), k % 6))
    sprinkles(kit, "confetti sprinkles", items, root, 0.034, 0.007)

    # glossy floor splats
    for k, (cx, cy, s) in enumerate(((0.6, -0.25, 1.0), (1.0, -0.6, 0.6), (0.3, -0.5, 0.5),
                                     (0.85, 0.2, 0.55), (0.55, -0.85, 0.4))):
        els = [(Vector((cx, cy, 0)), 0.32 * s, (1, 1, 0.1))]
        for j in range(8):
            a = 2 * math.pi * j / 8 + rnd.uniform(-0.3, 0.3)
            rr = rnd.uniform(0.14, 0.22) * s
            els.append((Vector((cx + math.cos(a) * rr, cy + math.sin(a) * rr, 0)), rnd.uniform(0.09, 0.13) * s,
                        (1, 1, 0.16)))
            els.append((Vector((cx + math.cos(a) * rr * 1.75, cy + math.sin(a) * rr * 1.75, 0)),
                        rnd.uniform(0.04, 0.06) * s, (1, 1, 0.3)))
        meta(kit, f"floorsplat{k}", els, goo_floor, root, res=0.01)
    # melted strawberry puddle with a dropped scoop and cone
    els = [(Vector((-0.45, -0.35, 0)), 0.3, (1.3, 1, 0.1)), (Vector((-0.28, -0.47, 0)), 0.16, (1, 1, 0.14)),
           (Vector((-0.62, -0.25, 0)), 0.14, (1, 1, 0.14))]
    meta(kit, "meltpuddle", els, flavors[0], root, res=0.01)
    scoop(kit, "dropped scoop", flavors[0], kit.empty("dropped scoop piv", root, (-0.42, -0.33, 0.0), (0, 18, 0)),
          0.07, -0.02, 8, 2.0)
    cone = prim(kit, "dropped cone", 'cone', (0.05, 0.05, 0.16), waffle_mat(kit), root, offset=(0, 0, 0.08),
                    taper=0.05, segments=18)
    cone.location = (-0.52, -0.5, 0.04)
    cone.rotation_euler = (math.radians(95), 0, math.radians(-50))


def post(path):
    import subprocess
    subprocess.run(["magick", path, "-sigmoidal-contrast", "3.2x42%", "-modulate", "100,108,100", path], check=True)
