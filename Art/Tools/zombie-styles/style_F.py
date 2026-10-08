"""Style F: Gummy. Everyone is molded gummy candy.

Bodies are metaball-molded gummy shapes baked to meshes (one continuous molded body per part), with two-tone
color regions and shallow embossing (apron, hat, cooler, torn shirt) painted and displaced onto the baked surface.
"""
from common import *
import numpy as np

KEY = "F"
LABEL = "Gummy"
SHADER = 'gummy'
WORLD = "#ffe3ef"
FLOOR = "#ffd1e3"

# palette
P_ORANGE, P_BLUE, P_PURPLE = "#ffb36b", "#3fa9ff", "#7c4dff"
Z_LIME, Z_PINK, Z_YELLOW = "#7ed957", "#ff5c8a", "#ffd23f"
G_ORANGE, G_GRAPE = "#ff8c42", "#9b5de5"
CHOC = "#6b2f12"
SYRUP = "#8c0014"

THRESH = 0.6
_counter = [0]


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


# ------------------------------------------------------------------ materials
def _nt(m):
    return v1.node_tree(m)


def _gummy_core(nt, rough=0.1, sss_scale=0.12, trans=0.22, glow=0.14, edge=0.75):
    """Shared gummy node core reading the 'Col' attribute. Returns (principled, attr, base_socket)."""
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    # thick edges read deeper and more saturated (light travels farther through the candy)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    deep = nt.nodes.new("ShaderNodeMix")
    deep.data_type = 'RGBA'
    deep.blend_type = 'MULTIPLY'
    deep.inputs[0].default_value = 1.0
    nt.links.new(attr.outputs["Color"], deep.inputs[6])
    nt.links.new(attr.outputs["Color"], deep.inputs[7])
    edgef = nt.nodes.new("ShaderNodeMath")
    edgef.operation = 'MULTIPLY'
    edgef.inputs[1].default_value = edge
    nt.links.new(lw.outputs["Facing"], edgef.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    nt.links.new(edgef.outputs[0], mix.inputs[0])
    nt.links.new(attr.outputs["Color"], mix.inputs[6])
    nt.links.new(deep.outputs[2], mix.inputs[7])
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])
    nt.links.new(attr.outputs["Color"], p.inputs["Subsurface Radius"])
    nt.links.new(attr.outputs["Color"], p.inputs["Emission Color"])
    for k, v in {"Roughness": rough, "IOR": 1.42, "Transmission Weight": trans, "Subsurface Weight": 1.0,
                 "Subsurface Scale": sss_scale, "Coat Weight": 1.0, "Coat Roughness": 0.03, "Coat IOR": 1.5,
                 "Emission Strength": glow, "Specular IOR Level": 0.7}.items():
        p.inputs[k].default_value = v
    nt.links.new(p.outputs[0], out.inputs[0])
    return p, attr, mix.outputs[2]


def gum_mat(name="gum"):
    m = bpy.data.materials.get("ZD2F " + name)
    if m:
        return m
    m = bpy.data.materials.new("ZD2F " + name)
    nt = _nt(m)
    _gummy_core(nt)
    m.diffuse_color = (1, 0.6, 0.3, 1)
    return m


def sour_mat(name="sour"):
    """Sugar-coated sour gummy. Col alpha = sugar amount (0 inside bites)."""
    m = bpy.data.materials.get("ZD2F " + name)
    if m:
        return m
    m = bpy.data.materials.new("ZD2F " + name)
    nt = _nt(m)
    p, attr, base = _gummy_core(nt, rough=0.12, glow=0.1)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 140
    nt.links.new(coord.outputs["Object"], vor.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9
    nt.links.new(coord.outputs["Object"], noise.inputs["Vector"])
    cover = nt.nodes.new("ShaderNodeMapRange")
    cover.inputs[1].default_value = 0.35
    cover.inputs[2].default_value = 0.6
    cover.inputs[3].default_value = 0.55
    cover.inputs[4].default_value = 1.0
    nt.links.new(noise.outputs["Fac"], cover.inputs[0])
    sugar = nt.nodes.new("ShaderNodeMath")
    sugar.operation = 'MULTIPLY'
    nt.links.new(attr.outputs["Alpha"], sugar.inputs[0])
    nt.links.new(cover.outputs[0], sugar.inputs[1])
    # frosted tint
    frost = nt.nodes.new("ShaderNodeMix")
    frost.data_type = 'RGBA'
    frost.inputs[7].default_value = (0.95, 0.97, 0.9, 1)
    fs = nt.nodes.new("ShaderNodeMath")
    fs.operation = 'MULTIPLY'
    fs.inputs[1].default_value = 0.42
    nt.links.new(sugar.outputs[0], fs.inputs[0])
    nt.links.new(fs.outputs[0], frost.inputs[0])
    nt.links.new(base, frost.inputs[6])
    nt.links.new(frost.outputs[2], p.inputs["Base Color"])
    rough = nt.nodes.new("ShaderNodeMapRange")
    rough.inputs[3].default_value = 0.12
    rough.inputs[4].default_value = 0.55
    nt.links.new(sugar.outputs[0], rough.inputs[0])
    nt.links.new(rough.outputs[0], p.inputs["Roughness"])
    coat = nt.nodes.new("ShaderNodeMapRange")
    coat.inputs[3].default_value = 1.0
    coat.inputs[4].default_value = 0.15
    nt.links.new(sugar.outputs[0], coat.inputs[0])
    nt.links.new(coat.outputs[0], p.inputs["Coat Weight"])
    # faceted crystals: random height per voronoi cell
    h = nt.nodes.new("ShaderNodeMath")
    h.operation = 'MULTIPLY'
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(vor.outputs["Color"], sep.inputs[0])
    nt.links.new(sep.outputs[0], h.inputs[0])
    nt.links.new(sugar.outputs[0], h.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.002
    nt.links.new(h.outputs[0], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
    m.diffuse_color = (0.4, 0.8, 0.3, 1)
    return m


def syrup_mat():
    m = bpy.data.materials.get("ZD2F syrup")
    if m:
        return m
    m = bpy.data.materials.new("ZD2F syrup")
    nt, p = v1.principled(m, hexc(SYRUP), **{"Roughness": 0.03, "Coat Weight": 1.0, "Coat Roughness": 0.0,
                                             "Transmission Weight": 0.45, "Subsurface Weight": 0.6,
                                             "Subsurface Radius": (1.0, 0.08, 0.08), "Subsurface Scale": 0.05,
                                             "IOR": 1.45, "Specular IOR Level": 0.9,
                                             "Emission Color": hexc("#ff1030"), "Emission Strength": 0.08})
    return m


def cream_mat():
    m = bpy.data.materials.get("ZD2F cream")
    if m:
        return m
    m = bpy.data.materials.new("ZD2F cream")
    nt = _nt(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    nt.links.new(attr.outputs["Color"], p.inputs["Base Color"])
    for k, v in {"Roughness": 0.38, "Subsurface Weight": 0.4, "Subsurface Scale": 0.03, "Coat Weight": 0.3,
                 "Coat Roughness": 0.2}.items():
        p.inputs[k].default_value = v
    nt.links.new(p.outputs[0], out.inputs[0])
    return m


def crystal_mat():
    m = bpy.data.materials.get("ZD2F crystal")
    if m:
        return m
    m = bpy.data.materials.new("ZD2F crystal")
    v1.principled(m, (1, 1, 1, 1), **{"Roughness": 0.04, "Transmission Weight": 0.75, "IOR": 1.55,
                                      "Coat Weight": 1.0, "Emission Color": (1, 1, 1, 1),
                                      "Emission Strength": 0.35})
    return m


# ------------------------------------------------------------------ painting helpers
_lin = {}


def lin(hx):
    if hx not in _lin:
        _lin[hx] = hexc(hx)[:3]
    return _lin[hx]


def paint_uniform(ob, hx, sugar=1.0):
    me = ob.data
    ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    c = lin(hx)
    ca.data.foreach_set("color", (list(c) + [sugar]) * len(me.vertices))
    return ob


def smoothstep(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def inside(sd, w=0.006):
    """signed distance (negative inside) -> soft 0..1 mask"""
    return 1.0 - smoothstep(-w, w, sd)


def sd_box2(px, py, cx, cy, hx, hy, r=0.0):
    qx, qy = abs(px - cx) - hx + r, abs(py - cy) - hy + r
    return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - r


# ------------------------------------------------------------------ metaball molding
def _kf(s):
    return math.sqrt(1 - (THRESH / s) ** (1 / 3))


class Blob:
    """Collects metaball elements (in visible units) and color/emboss painters, then bakes one molded mesh."""

    def __init__(self, base, sugar=0.0):
        self.els = []
        self.paints = []  # (fn(p, n) -> mask, hex or None, height, sugar or None)
        self.base = base
        self.sugar = sugar

    def _add(self, typ, c, R, size, rot, s, col, neg):
        q = Euler([math.radians(a) for a in rot]).to_quaternion()
        self.els.append(dict(t=typ, c=Vector(c), R=R, size=Vector(size), q=q, qi=q.inverted(), s=s, col=col,
                             neg=neg))

    def ball(self, c, r, col=None, s=2.0, neg=False):
        self._add('BALL', c, r / _kf(s), (1, 1, 1), (0, 0, 0), s, col, neg)

    def ell(self, c, h, rot=(0, 0, 0), col=None, s=2.0, neg=False):
        self._add('ELLIPSOID', c, 1 / _kf(s), h, rot, s, col, neg)

    def box(self, c, h, r, rot=(0, 0, 0), col=None, s=2.0):
        self._add('CUBE', c, r / _kf(s), [max(0.001, x - r) for x in h], rot, s, col, False)

    def chain(self, pts, radii, col=None, s=2.0, spacing=0.75, neg=False):
        """Beads along a polyline. col may be a hex, None, or a list cycled per bead (stripes)."""
        pts = [Vector(p) for p in pts]
        out = []
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            ra, rb = radii[i], radii[i + 1]
            n = max(1, int((b - a).length / (spacing * min(ra, rb))))
            for k in range(n + (1 if i == len(pts) - 2 else 0)):
                t = k / n
                out.append((a.lerp(b, t), ra + (rb - ra) * t))
        for j, (p, r) in enumerate(out):
            c = col[j % len(col)] if isinstance(col, list) else col
            self.ball(p, r, c, s, neg)
        return [p for p, _ in out]

    def paint(self, fn, hx=None, height=0.0, sugar=None):
        self.paints.append((fn, hx, height, sugar))

    @staticmethod
    def dens(e, P):
        """Metaball density of element e at points P (n, 3), matching Blender's falloff."""
        d = (P - np.array(e['c'])) @ np.array(e['qi'].to_matrix()).T
        sz = np.array(e['size'])
        if e['t'] == 'CUBE':
            d = np.sign(d) * np.maximum(np.abs(d) - sz, 0)
        elif e['t'] == 'ELLIPSOID':
            d = d / sz
        v = np.maximum(1 - (d * d).sum(1) / (e['R'] * e['R']), 0)
        return e['s'] * v * v * v

    def build(self, kit, name, mat, parent=None, res=0.016, tris=None, loc=(0, 0, 0), rot=(0, 0, 0)):
        _counter[0] += 1
        nm = f"gumF{_counter[0]}x"
        mb = bpy.data.metaballs.new(nm)
        mb.resolution = mb.render_resolution = res
        mb.threshold = THRESH
        mob = bpy.data.objects.new(nm, mb)
        kit.col.objects.link(mob)
        for e in self.els:
            el = mb.elements.new(type=e['t'])
            el.co = e['c']
            el.radius = e['R']
            el.stiffness = e['s']
            el.rotation = e['q']
            el.use_negative = e['neg']
            if e['t'] != 'BALL':
                el.size_x, el.size_y, el.size_z = e['size']
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        me = bpy.data.meshes.new_from_object(mob.evaluated_get(dg))
        me.name = name
        bpy.data.objects.remove(mob)
        bpy.data.metaballs.remove(mb)
        self._paint_mesh(me)
        me.materials.append(mat)
        me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = kit.link(name, me, parent, loc, rot)
        ntri = sum(len(p.vertices) - 2 for p in me.polygons)
        if tris and ntri > tris:
            dec = ob.modifiers.new("Decimate", 'DECIMATE')
            dec.ratio = tris / ntri
        return ob

    def _paint_mesh(self, me):
        n = len(me.vertices)
        co = [0.0] * (3 * n)
        no = [0.0] * (3 * n)
        me.vertices.foreach_get("co", co)
        me.vertices.foreach_get("normal", no)
        pos = [e for e in self.els if not e['neg']]
        neg = [e for e in self.els if e['neg']]
        P = np.array(co).reshape(-1, 3)
        Dp = np.array([self.dens(e, P) for e in pos])
        best_i, total = Dp.argmax(0), Dp.sum(0)
        if neg:
            Dn = np.array([self.dens(e, P) for e in neg])
            nb_i, nb_d = Dn.argmax(0), Dn.max(0)
        cols = []
        for i in range(n):
            p = Vector(co[3 * i:3 * i + 3])
            nv = Vector(no[3 * i:3 * i + 3])
            c = Vector(lin(pos[best_i[i]]['col'] or self.base))
            sugar = self.sugar
            if neg and total[i] > THRESH * 1.2 and nb_d[i] > 0.05:  # carved by a negative element: glossy, no sugar
                sugar = 0.0
                if neg[nb_i[i]]['col']:
                    c = Vector(lin(neg[nb_i[i]]['col']))
            disp = 0.0
            for fn, phx, h, psug in self.paints:
                m = fn(p, nv)
                if m <= 0:
                    continue
                if phx:
                    c = c.lerp(Vector(lin(phx)), m)
                if psug is not None:
                    sugar = sugar + (psug - sugar) * m
                disp += h * m
            if disp:
                p2 = p + nv * disp
                co[3 * i:3 * i + 3] = p2[:]
            cols.extend((c[0], c[1], c[2], sugar))
        me.vertices.foreach_set("co", co)
        ca = me.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
        ca.data.foreach_set("color", cols)
        me.update()


def ground(ob, z_target=0.0):
    """Shift ob (in its parent space) so its lowest vertex sits at z_target in parent space."""
    zs = [(ob.matrix_basis @ v.co).z for v in ob.data.vertices]
    ob.location.z += z_target - min(zs)


# ------------------------------------------------------------------ gun
def _torus(kit, name, parent, center, axis, R, r, hx, nmaj=24, nmin=6):
    """Smooth gummy ring (rims, lips). axis 'Y' or 'Z' is the ring's normal."""
    bm = bmesh.new()
    rings = []
    for i in range(nmaj):
        a = 2 * math.pi * i / nmaj
        ring = []
        for j in range(nmin):
            b = 2 * math.pi * j / nmin
            rad, h = R + r * math.cos(b), r * math.sin(b)
            x, w = rad * math.cos(a), rad * math.sin(a)
            ring.append(bm.verts.new((x, h, w) if axis == 'Y' else (x, w, h)))
        rings.append(ring)
    for i in range(nmaj):
        for j in range(nmin):
            a, b = rings[i][j], rings[(i + 1) % nmaj][j]
            bm.faces.new((a, b, rings[(i + 1) % nmaj][(j + 1) % nmin], rings[i][(j + 1) % nmin]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.translate(bm, vec=Vector(center), verts=bm.verts)
    return paint_uniform(kit.mesh_from_bmesh(name, bm, gum_mat(), parent), hx, 0)


def _waffle_cone(kit, name, parent, y0, y1, r0, r1, nseg=40, nlen=10):
    bm = bmesh.new()
    rings = []
    cols = []
    for j in range(nlen + 1):
        t = j / nlen
        y = y0 + (y1 - y0) * t
        r = r0 + (r1 - r0) * (t ** 1.7)
        ring = []
        for i in range(nseg):
            a = 2 * math.pi * i / nseg
            u, v = i / nseg * 10, t * 2.5
            f1, f2 = (u + v) % 1, (u - v) % 1
            ridge = max(1 - min(f1, 1 - f1) * 7, 1 - min(f2, 1 - f2) * 7, 0)
            rr = r + 0.0028 * ridge
            ring.append(bm.verts.new((rr * math.cos(a), y, rr * math.sin(a))))
            cols.append(ridge)
        rings.append(ring)
    for j in range(nlen):
        for i in range(nseg):
            a, b = rings[j][i], rings[j][(i + 1) % nseg]
            c, d = rings[j + 1][(i + 1) % nseg], rings[j + 1][i]
            bm.faces.new((a, b, c, d))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, gum_mat(), parent)
    ca = ob.data.color_attributes.new("Col", 'FLOAT_COLOR', 'POINT')
    lo, hi = Vector(lin("#e8641c")), Vector(lin("#ffc06a"))
    data = []
    for r in cols:
        c = lo.lerp(hi, r)
        data.extend((c[0], c[1], c[2], 0))
    ca.data.foreach_set("color", data)
    return ob


def build_gun(kit, root):
    gm = gum_mat()
    # molded grape body + grip + trigger guard, one piece
    b = Blob(G_GRAPE)
    b.ell((0, 0.0, 0.0), (0.034, 0.095, 0.036), s=3)
    b.ball((0, 0.085, 0.006), 0.04, s=3)
    b.ell((0, -0.088, 0.0), (0.03, 0.022, 0.03), s=3)                           # barrel collar
    b.chain([(0, 0.068, -0.02), (0, 0.085, -0.07), (0, 0.1, -0.115)], [0.027, 0.026, 0.028], s=3)  # grip
    for k in range(3):                                                         # molded finger ridges
        b.ball((0, 0.06 + 0.012 * k, -0.06 - 0.02 * k), 0.016, s=4)
    guard = [(0, -0.01, -0.03), (0, -0.012, -0.06), (0, 0.01, -0.082), (0, 0.04, -0.082), (0, 0.065, -0.07)]
    b.chain(guard, [0.008] * 5, s=4, spacing=0.6)
    b.ell((0, 0.022, -0.05), (0.007, 0.009, 0.02), rot=(-20, 0, 0), col=G_ORANGE, s=4)  # trigger
    b.chain([(0.0, -0.06, 0.036), (0.0, 0.06, 0.036)], [0.009, 0.009], col=G_ORANGE, s=4)  # top rib
    # embossed scoop badge on both sides + side stripe
    b.paint(lambda p, n: inside(math.hypot(p.y + 0.01, p.z - 0.002) - 0.017, 0.003) * smoothstep(0.3, 0.6, abs(n.x)),
            G_ORANGE, 0.003)
    b.paint(lambda p, n: inside(abs(p.z + 0.016) - 0.004, 0.002) * smoothstep(0.3, 0.6, abs(n.x)) *
            (1 if -0.08 < p.y < 0.05 else 0), "#c79bff", 0.0015)
    b.build(kit, "gun body", gm, root, res=0.0045, tris=1400)
    # waffle-cone flared muzzle
    _waffle_cone(kit, "gun waffle muzzle", root, -0.095, -0.175, 0.024, 0.056)
    _torus(kit, "gun muzzle rim", root, (0, -0.176, 0), 'Y', 0.0585, 0.0065, "#ffc06a")
    # pint tub magazine, chocolate scoop, sprinkles
    tub = kit.prim("gun pint tub", 'cyl', (0.034, 0.034, 0.055), gm, root, offset=(0, 0.02, 0.064), taper=1.13,
                   segments=20, bevel=0.006)
    paint_uniform(tub, "#ffb36b", 0)
    _torus(kit, "gun tub top rim", root, (0, 0.02, 0.091), 'Z', 0.0385, 0.0065, G_GRAPE)
    _torus(kit, "gun tub base rim", root, (0, 0.02, 0.04), 'Z', 0.0345, 0.0055, G_GRAPE)
    sc = Blob(CHOC)
    sc.ball((0, 0.02, 0.112), 0.034, s=2.5)
    for i in range(9):
        a = 2 * math.pi * i / 9 + 0.3
        sc.ball((0.03 * math.cos(a), 0.02 + 0.03 * math.sin(a), 0.098 + 0.004 * (i % 2)), 0.013, s=3)
    sc.build(kit, "gun chocolate scoop", gm, root, res=0.004, tris=900)
    cols = [P_BLUE, Z_PINK, Z_YELLOW, Z_LIME, "#ffffff", G_GRAPE]
    for i in range(16):
        u = kit.rand.uniform(0, 2 * math.pi)
        v = kit.rand.uniform(0.15, 1.2)
        d = Vector((math.cos(u) * math.sin(v), math.sin(u) * math.sin(v), math.cos(v)))
        pos = Vector((0, 0.02, 0.112)) + d * 0.035
        s = kit.prim(f"gun sprinkle {i}", 'cyl', (0.0028, 0.0028, 0.013), gm, root, offset=(0, 0, 0), segments=6)
        paint_uniform(s, cols[i % len(cols)], 0)
        tang = d.cross(Vector((kit.rand.uniform(-1, 1), kit.rand.uniform(-1, 1), 0.3))).normalized()
        s.location = pos
        s.rotation_euler = tang.to_track_quat('Z', 'Y').to_euler()


# ------------------------------------------------------------------ player
def build_player(kit, root):
    body_piv = kit.empty("player body", root)
    b = Blob(P_ORANGE)
    # head: big round gummy-bear head with ears and muzzle
    b.ell((0, 0, 1.12), (0.25, 0.22, 0.23))
    for sx in (1, -1):
        b.ball((sx * 0.19, 0.01, 1.3), 0.075, s=2.5)
        b.ball((sx * 0.19, -0.035, 1.3), 0.04, col="#ff9a45", s=4)                # inner ear
        b.ball((sx * 0.085, -0.19, 1.19), 0.03, col="#2a1650", s=5)                 # embossed eyes
        b.ball((sx * 0.072, -0.213, 1.205), 0.009, col="#ffffff", s=6)              # eye shine
    b.ell((0, -0.19, 1.05), (0.11, 0.085, 0.075))                                  # muzzle
    b.ell((0, -0.27, 1.09), (0.04, 0.025, 0.028), col="#2a1650", s=4)              # nose
    # soda-jerk paper hat molded on as a blue boat cap with purple band
    b.ell((0, 0.0, 1.335), (0.12, 0.27, 0.06), rot=(-5, 0, 0), col=P_BLUE, s=4)
    b.ell((0, 0.0, 1.38), (0.075, 0.24, 0.075), rot=(-5, 0, 0), col=P_BLUE, s=4)
    b.ell((0, 0.0, 1.43), (0.035, 0.18, 0.055), rot=(-5, 0, 0), col=P_BLUE, s=5)
    b.ell((0, 0.0, 1.47), (0.016, 0.1, 0.03), rot=(-5, 0, 0), col=P_BLUE, s=6)
    b.ell((0, 0.0, 1.325), (0.125, 0.275, 0.022), rot=(-5, 0, 0), col=P_PURPLE, s=6)
    # body: pear torso with round belly
    b.ell((0, 0.0, 0.6), (0.25, 0.21, 0.29))
    b.ball((0, -0.04, 0.5), 0.22)
    # legs: thick stumps merging into the body, rounded feet
    for sx in (1, -1):
        b.chain([(sx * 0.13, 0, 0.36), (sx * 0.14, -0.02, 0.16)], [0.11, 0.105])
        b.ell((sx * 0.14, -0.06, 0.075), (0.1, 0.135, 0.075))
    # arms: left (+X) resting on the belly, right (-X) raised and aiming forward
    b.chain([(0.22, 0.0, 0.8), (0.3, -0.06, 0.64), (0.25, -0.17, 0.53)], [0.08, 0.072, 0.07])
    b.ell((0.24, -0.2, 0.52), (0.07, 0.06, 0.07))
    paw = Vector((-0.2, -0.47, 0.93))
    b.chain([(-0.21, 0.0, 0.82), (-0.25, -0.24, 0.88), paw], [0.082, 0.072, 0.07])
    b.ell(paw + Vector((0, -0.02, 0)), (0.07, 0.07, 0.065))
    # cooler backpack molded onto the back: purple box, blue lid, spare pints poking up
    b.box((0, 0.27, 0.64), (0.2, 0.1, 0.2), 0.05, col=P_PURPLE, s=4)
    b.box((0, 0.275, 0.83), (0.21, 0.11, 0.035), 0.03, col=P_BLUE, s=4)
    b.chain([(-0.09, 0.3, 0.86), (-0.06, 0.3, 0.9), (0.06, 0.3, 0.9), (0.09, 0.3, 0.86)], [0.018] * 4,
            col=P_BLUE, s=4)
    for sx, hx in ((1, "#fff1d6"), (-1, "#ff9ec1")):
        b.box((sx * 0.13, 0.25, 0.9), (0.05, 0.05, 0.06), 0.025, col=hx, s=4)
        b.ell((sx * 0.13, 0.25, 0.965), (0.055, 0.055, 0.016), col=P_BLUE, s=5)
    # shoulder straps
    for sx in (1, -1):
        b.chain([(sx * 0.12, -0.17, 0.8), (sx * 0.13, -0.09, 0.88), (sx * 0.13, 0.06, 0.9), (sx * 0.12, 0.2, 0.82)],
                [0.022] * 4, col=P_PURPLE, s=4)

    # apron: embossed blue bib + skirt on the front, with a purple scoop pocket
    def apron_sd(p):
        bib = sd_box2(p.x, p.z, 0, 0.72, 0.12 - (p.z - 0.62) * 0.15, 0.12, 0.03)
        skirt = sd_box2(p.x, p.z, 0, 0.44, 0.24, 0.17, 0.05)
        return min(bib, skirt)

    def apron(p, n):
        return inside(apron_sd(p), 0.006) * smoothstep(-0.05, -0.35, n.y)

    b.paint(apron, P_BLUE, 0.012)
    b.paint(lambda p, n: inside(abs(apron_sd(p) + 0.016) - 0.005, 0.004) * smoothstep(-0.05, -0.35, n.y),
            "#7fc6ff", 0.005)                                                           # stitched rim ridge
    b.paint(lambda p, n: inside(math.hypot(p.x - 0.0, p.z - 0.47) - 0.06, 0.005) * smoothstep(-0.1, -0.5, n.y),
            P_PURPLE, 0.006)                                                            # scoop pocket
    b.paint(lambda p, n: inside(math.hypot(p.x - 0.0, p.z - 0.52) - 0.032, 0.004) * smoothstep(-0.1, -0.5, n.y),
            "#fff1d6", 0.006)                                                           # scoop on pocket
    body = b.build(kit, "player gummy body", gum_mat(), body_piv, res=0.012, tris=9500)
    ground(body)
    gun = kit.empty("held gun", body, paw + Vector((0, -0.09, 0.075)), (6, 0, 0), (1.15, 1.15, 1.15))
    build_gun(kit, gun)


# ------------------------------------------------------------------ zombie
def _limb(kit, name, parent, pts, radii, paw, paw_h, tris=1500, drip=None):
    stripes = [Z_PINK, Z_PINK, Z_YELLOW, Z_YELLOW]
    b = Blob(Z_PINK, sugar=1.0)
    b.chain(pts, radii, col=stripes, s=2.4, spacing=0.55)
    b.ell(paw, paw_h, col=Z_YELLOW, s=2.4)
    if drip:
        b.chain(drip, [0.022, 0.014, 0.02], col=Z_YELLOW, s=3)
    return b.build(kit, name, sour_mat(), parent, res=0.012, tris=tris)


def build_zombie(kit, root, hit=False):
    rz = root.rotation_euler.z
    to_local = Matrix.Rotation(-rz, 3, 'Z')
    hips = kit.empty("zombie hips", root, (0, 0, 0.42), (-16, -12, 0) if hit else (0, 0, 0))

    # torso: lime sour gummy, hunched, with a bite and a torn yellow shirt
    t = Blob(Z_LIME, sugar=1.0)
    t.ball((0, 0.02, 0.04), 0.19)
    t.ell((0, -0.05, 0.2), (0.24, 0.2, 0.22))
    t.ell((0, -0.14, 0.4), (0.22, 0.17, 0.15), rot=(20, 0, 0))
    t.ball((0, 0.03, 0.38), 0.15)                                                    # hunch
    nrm = Vector((0.97, -0.25, 0)).normalized()
    tan = Vector((0.25, 0.97, 0)).normalized()
    C = Vector((0.235, -0.1, 0.16))                                                  # on the left flank surface
    t.ball(C + nrm * 0.01, 0.1, s=6, neg=True, col="#4cc22a")
    for i in range(9):
        a = 2 * math.pi * i / 9
        t.ball(C + nrm * 0.012 + (tan * math.cos(a) + Vector((0, 0, 1)) * math.sin(a)) * 0.1, 0.04, s=6,
               neg=True, col="#4cc22a")
    if hit:  # torn shoulder stump
        t.ball((0.25, -0.15, 0.42), 0.075, s=5, neg=True, col="#c4142e")

    def hem(x):
        return 0.3 + 0.05 * abs(((x * 8) % 1) - 0.5) * 2 + (0.06 if x > 0.05 else 0)

    def shirt(p, n):
        if p.z < hem(p.x) or p.z > 0.47 or abs(p.x) > 0.17:
            return 0
        hole = math.hypot(p.x + 0.08, p.z - 0.27) - 0.045
        hole2 = math.hypot(p.x - 0.1, (p.z - 0.4) * 1.5) - 0.035
        return inside(-min(hole, hole2), 0.004) * smoothstep(-0.0, -0.3, n.y)

    t.paint(shirt, "#ff8fb0", 0.01, 0.2)
    t.paint(lambda p, n: inside(abs(p.z - hem(p.x)) - 0.004, 0.004) * smoothstep(0.0, -0.3, n.y) *
            (1 if p.z < 0.47 and abs(p.x) < 0.17 else 0), Z_PINK, 0.004)
    t.build(kit, "zombie torso", sour_mat(), hips, res=0.013, tris=3800)

    # head: drooping melted gummy bear head with exposed brain
    neck = kit.empty("zombie neck", hips, (0, -0.2, 0.5), (-12, -6, 24) if hit else (10, 0, -10))
    h = Blob(Z_LIME, sugar=1.0)
    h.ell((0, -0.1, 0.1), (0.22, 0.19, 0.19))
    h.ball((0.17, -0.06, 0.26), 0.06)                                               # ear
    h.ell((-0.21, -0.08, 0.02), (0.05, 0.05, 0.1), rot=(0, 20, 0))                 # melted ear, sagging
    h.chain([(-0.22, -0.08, -0.06), (-0.225, -0.08, -0.13)], [0.035, 0.03])
    h.ell((0.0, -0.26, -0.03), (0.11, 0.08, 0.08), rot=(15, 0, 0))                 # sagging snout
    h.ell((0.0, -0.33, -0.06), (0.07, 0.04, 0.03), s=6, neg=True, col="#5c0a26")   # mouth
    h.ball((0.03, -0.3, -0.03), 0.014, col="#fff6d8", s=5)                         # tooth
    h.ball((-0.035, -0.3, -0.035), 0.012, col="#fff6d8", s=5)
    h.ball((0.09, -0.26, 0.13), 0.065, col="#fffbe8", s=4)                         # big bulging eye
    h.ball((0.1, -0.322, 0.125), 0.024, col="#2b0f1a", s=6)                        # pupil
    h.ell((-0.095, -0.285, 0.045), (0.034, 0.024, 0.055), rot=(0, -15, 0), col="#2b0f1a", s=5)  # small droopy eye
    h.ell((-0.095, -0.282, 0.105), (0.05, 0.03, 0.022), rot=(0, -25, 0), col="#4fa832", s=5)  # heavy lid
    # exposed brain: pink wrinkled lobes bulging through the top of the head
    lc, lh = Vector((0.07, -0.1, 0.245)), Vector((0.095, 0.15, 0.09))
    for sx in (1, -1):
        c = Vector((sx * lc.x, lc.y, lc.z))
        h.ell(c, lh, col="#e8336b", s=3)
        for row in range(3):                       # squiggly wrinkle ridges over each lobe
            pts = []
            for k in range(9):
                u = -0.85 + 1.7 * k / 8
                dx = (-0.45 + 0.45 * row) + 0.18 * math.sin(k * 1.9 + row * 2 + sx)
                dz = math.sqrt(max(0.0, 1 - dx * dx - u * u))
                nrmv = Vector((sx * dx / lh.x, u / lh.y, dz / lh.z)).normalized()
                pts.append(c + Vector((sx * dx * lh.x, u * lh.y, dz * lh.z)) + nrmv * 0.004)
            h.chain(pts, [0.019] * len(pts), col="#ffa3c2", s=6, spacing=0.8)
    h.ell((0, -0.1, 0.33), (0.014, 0.17, 0.06), s=6, neg=True, col="#c8204f")      # brain groove
    for i in range(10):                            # cracked skull rim shards
        a = 2 * math.pi * i / 10
        h.ell((0.16 * math.cos(a), -0.1 + 0.19 * math.sin(a), 0.235 + 0.02 * (i % 2)), (0.03, 0.03, 0.03 + 0.02 * (i % 3)),
              rot=(30 * math.sin(a), -30 * math.cos(a), 0), s=4)
    # melted drips off the chin and cheek
    h.chain([(0.05, -0.27, -0.09), (0.055, -0.27, -0.16), (0.055, -0.27, -0.2)], [0.025, 0.014, 0.022], s=3)
    h.chain([(-0.12, -0.22, -0.03), (-0.125, -0.22, -0.1), (-0.125, -0.22, -0.13)], [0.02, 0.012, 0.017], s=3)
    head = h.build(kit, "zombie head", sour_mat(), neck, res=0.01, tris=4200)

    # ice cream splat: vanilla blob on the right shoulder/chest, dripping
    ic = Blob("#fff3d6")
    ic.ell((-0.15, -0.24, 0.42), (0.09, 0.03, 0.07), rot=(25, 0, 0))
    ic.ball((-0.2, -0.24, 0.47), 0.04)
    ic.ball((-0.1, -0.27, 0.45), 0.03)
    ic.chain([(-0.12, -0.27, 0.38), (-0.125, -0.27, 0.3), (-0.125, -0.27, 0.27)], [0.025, 0.014, 0.02], s=3)
    ic.chain([(-0.2, -0.24, 0.39), (-0.205, -0.24, 0.34)], [0.02, 0.016], s=3)
    ic.ball((-0.15, -0.28, 0.44), 0.022, col="#ff9ec1")
    ic.build(kit, "zombie ice cream splat", cream_mat(), hips, res=0.008, tris=800)

    # arms: two-tone sour-worm limbs on shoulder pivots
    arm_r = kit.empty("zombie arm R", hips, (-0.24, -0.15, 0.42), (20, 0, -6) if hit else (0, 0, 0))
    _limb(kit, "zombie arm R mesh", arm_r, [(0, 0, 0), (-0.05, -0.2, -0.06), (-0.03, -0.38, -0.1)],
          [0.068, 0.06, 0.056], (-0.03, -0.43, -0.12), (0.06, 0.07, 0.055),
          drip=[(-0.03, -0.45, -0.16), (-0.03, -0.45, -0.21), (-0.03, -0.45, -0.24)])
    if hit:
        sh_world = hips.matrix_basis @ Vector((0.24, -0.15, 0.42))
        fly = sh_world + to_local @ Vector((0.72, -0.28, 0.42))
        arm_l = kit.empty("zombie arm L (flying)", root, fly, (60, -40, 130))
    else:
        arm_l = kit.empty("zombie arm L", hips, (0.24, -0.15, 0.42))
    _limb(kit, "zombie arm L mesh", arm_l, [(0, 0, 0), (0.05, -0.21, 0.02), (0.04, -0.42, 0.04)],
          [0.068, 0.06, 0.056], (0.04, -0.47, 0.04), (0.06, 0.07, 0.055))

    # legs
    for sx, rot in ((1, (0, 0, 12)), (-1, (6, 0, -16))):
        leg = kit.empty(f"zombie leg {'L' if sx > 0 else 'R'}", root, (sx * 0.12, 0.02, 0.42), rot)
        ob = _limb(kit, leg.name + " mesh", leg, [(0, 0, 0.02), (sx * 0.01, -0.02, -0.15), (0, -0.02, -0.28)],
                   [0.095, 0.09, 0.088], (0, -0.06, -0.355), (0.1, 0.135, 0.07), tris=1500)
        ground(ob, -0.42)

    if hit:
        _hit_fx(kit, root, to_local, sh_world, fly)


# ------------------------------------------------------------------ hit FX
def _drop_mesh(name, r, tail):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r)
    for v in bm.verts:
        if v.co.z > 0:
            f = v.co.z / r
            v.co.z *= 1 + tail * f
            v.co.x *= 1 - 0.8 * f * f
            v.co.y *= 1 - 0.8 * f * f
    return bm


def _hit_fx(kit, root, to_local, sh, fly):
    R = kit.rand
    fx = kit.empty("hit fx", root)
    syrup = syrup_mat()
    up = Vector((0, 0, 1))
    burst_dir = (to_local @ Vector((1.0, -0.55, 0.6))).normalized()

    def spray_dir(spread):
        d = burst_dir + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-0.6, 1))) * spread
        return d.normalized()

    # syrup stump cap and the gooey strand stretching to the flying arm
    st = Blob(SYRUP)
    st.ball(sh + Vector((0.02, 0, 0)), 0.06, s=3)
    a, b = sh + Vector((0.04, -0.01, 0)), fly
    n = 10
    for i in range(n + 1):
        u = i / n
        p = a.lerp(b, u) + up * (-0.06 * math.sin(math.pi * u))
        st.ball(p, 0.035 * (1 - 0.75 * math.sin(math.pi * u)) + 0.006, s=3)
    st.chain([sh + Vector((0.05, -0.06, -0.04)), sh + Vector((0.06, -0.07, -0.14)), sh + Vector((0.06, -0.07, -0.19))],
             [0.025, 0.014, 0.022], s=3)
    # syrup ribbons arcing out of the wound, thinning into beads with a fat drop at the end
    for k in range(8):
        d = spray_dir(0.55)
        L = R.uniform(0.35, 0.75)
        n = int(L / 0.01)
        for i in range(n + 1):
            u = i / n
            p = sh + d * L * u + up * (-0.35 * (L * u) ** 2)
            r = 0.032 * (1 - u) + 0.01 + (0.014 if i == n else 0)
            st.ball(p, r, s=3)
    stob = st.build(kit, "fx syrup stump + strand", gum_mat(), fx, res=0.008, tris=3000)
    stob.data.materials[0] = syrup

    # flying syrup drops (teardrops trailing back toward the wound)
    for i in range(40):
        d = spray_dir(1.0)
        dist = R.uniform(0.3, 1.1)
        p = sh + d * dist + up * (-0.25 * dist * dist)
        r = R.uniform(0.012, 0.045) * (1.2 - dist * 0.5)
        ob = kit.mesh_from_bmesh(f"fx syrup drop {i}", _drop_mesh("drop", r, R.uniform(1.0, 2.6)), syrup, fx)
        ob.location = p
        ob.rotation_euler = (-d).to_track_quat('Z', 'Y').to_euler()

    # glossy syrup puddles and splats on the floor
    pud = Blob(SYRUP)
    centers = [(0.45, -0.25), (0.75, -0.05), (0.3, -0.55), (0.95, -0.4), (-0.15, -0.35)]
    for k, (cx, cy) in enumerate(centers):
        c = to_local @ Vector((cx, cy, 0))
        rr = R.uniform(0.07, 0.14)
        pud.ell((c.x, c.y, 0.0), (rr, rr * R.uniform(0.7, 1.0), 0.012), rot=(0, 0, R.uniform(0, 180)), s=3)
        for j in range(5):
            a = R.uniform(0, 2 * math.pi)
            dd = rr * R.uniform(1.0, 1.6)
            pud.ell((c.x + math.cos(a) * dd, c.y + math.sin(a) * dd, 0.0), (rr * 0.25, rr * 0.25, 0.01), s=3)
    pob = pud.build(kit, "fx syrup puddles", gum_mat(), fx, res=0.01, tris=4000)
    pob.data.materials[0] = syrup

    # jelly chunks: sugared lime cubes and torn worm bits
    for i in range(20):
        d = spray_dir(0.9)
        dist = R.uniform(0.2, 0.85)
        p = sh + d * dist + up * (-0.2 * dist * dist)
        s = R.uniform(0.03, 0.065)
        hx = [Z_LIME, Z_LIME, Z_PINK, Z_YELLOW][i % 4]
        ob = kit.prim(f"fx jelly chunk {i}", 'box', (s, s * R.uniform(0.7, 1.2), s * R.uniform(0.7, 1.1)), sour_mat(),
                      fx)
        bev = ob.modifiers.new("Bevel", 'BEVEL')
        bev.width = s * 0.3
        bev.segments = 3
        paint_uniform(ob, hx, 1.0)
        ob.location = p
        ob.rotation_euler = (R.uniform(0, 6), R.uniform(0, 6), R.uniform(0, 6))
    for i, (cx, cy) in enumerate([(0.6, -0.35), (0.85, 0.15), (0.2, -0.7)]):
        c = to_local @ Vector((cx, cy, 0))
        ob = kit.prim(f"fx floor chunk {i}", 'box', (0.05, 0.045, 0.04), sour_mat(), fx, bevel=0.012)
        paint_uniform(ob, [Z_LIME, Z_PINK, Z_YELLOW][i], 1.0)
        ob.location = (c.x, c.y, 0.02)
        ob.rotation_euler = (0, 0, R.uniform(0, 3))

    # sugar crystals: glinting little cubes in the burst and scattered on the floor
    cm = crystal_mat()
    for i in range(120):
        if i < 85:
            d = spray_dir(1.0)
            dist = R.uniform(0.1, 0.9)
            p = sh + d * dist + up * (-0.15 * dist * dist)
        else:
            c = to_local @ Vector((R.uniform(-0.2, 1.1), R.uniform(-0.8, 0.3), 0))
            p = Vector((c.x, c.y, 0.006))
        s = R.uniform(0.01, 0.024)
        ob = kit.prim(f"fx sugar {i}", 'box', (s, s, s), cm, fx, smooth=False)
        ob.location = p
        ob.rotation_euler = (R.uniform(0, 6), R.uniform(0, 6), R.uniform(0, 6))

    # ice cream: vanilla and strawberry globs flying, plus a floor splat
    for i in range(7):
        d = spray_dir(1.0)
        dist = R.uniform(0.35, 1.0)
        p = sh + d * dist + up * (-0.2 * dist * dist)
        g = Blob(["#fff3d6", "#ff9ec1"][i % 2])
        rr = R.uniform(0.03, 0.05)
        g.ball((0, 0, 0), rr)
        for j in range(5):
            o = Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))).normalized() * rr * 0.8
            g.ball(o, rr * R.uniform(0.4, 0.6), s=2.5)
        g.chain([-d * rr * 1.2, -d * rr * 2.4, -d * rr * 3.0], [rr * 0.45, rr * 0.2, rr * 0.25], s=3)
        g.build(kit, f"fx ice cream glob {i}", cream_mat(), fx, res=0.007, tris=1200, loc=p)
    sp = Blob("#fff3d6")
    c = to_local @ Vector((0.55, -0.6, 0))
    sp.ell((c.x, c.y, 0.0), (0.12, 0.1, 0.03), s=3)
    sp.ball((c.x, c.y, 0.03), 0.05, col="#ff9ec1", s=3)
    for j in range(7):
        a = j * 0.9
        sp.ell((c.x + math.cos(a) * 0.15, c.y + math.sin(a) * 0.13, 0.0), (0.03, 0.03, 0.018), s=3)
    sp.build(kit, "fx ice cream floor splat", cream_mat(), fx, res=0.008, tris=2500)


# ------------------------------------------------------------------ lights
def setup(scene, stage):
    def light(name, kind, loc, rot, energy, color, **kw):
        ld = bpy.data.lights.new(name, kind)
        ld.energy = energy
        ld.color = hexc(color)[:3]
        for k, v in kw.items():
            setattr(ld, k, v)
        ob = bpy.data.objects.new(name, ld)
        stage.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = rot
        return ob

    # strong warm backlight from behind the characters so the candy glows through
    light("gummy backlight", 'SUN', (0, 0, 0), Euler((math.radians(-68), 0, math.radians(10))), 3.0, "#fff0dc", angle=math.radians(4), specular_factor=0.25)
    # gun: a spot behind the gun (from -X) for translucent rims
    gl = Vector((1.72, -0.25, 1.32))
    light("gummy gun back", 'SPOT', gl, (Vector((2.3, -0.42, 1.1)) - gl).to_track_quat('-Z', 'Y').to_euler(), 25, "#fff0dc", spot_size=math.radians(35))
