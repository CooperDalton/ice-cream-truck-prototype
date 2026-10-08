"""Style G: Claymation. Aardman-like plasticine puppets: hand-pinched lumpy clay over thin wire limbs,
wide toothy grins, ping-pong eyes under heavy brows, bulbous noses, fingerprints everywhere."""
from common import *
from mathutils import noise as mnoise

KEY = "G"
LABEL = "Claymation"
SHADER = 'clay'
WORLD = "#d8cbb8"
FLOOR = "#b7a58c"

SKIN, SHIRT, TROUSER, SHOE = "#f0b48a", "#4f86c6", "#5a4a3f", "#c0392b"
Z_SKIN, Z_SHIRT, Z_TROUSER = "#88b04b", "#c97b3c", "#4a5a7a"
GUN_G, GUN_R = "#6ab187", "#c0392b"
BLOOD, PINK, MINT, VANILLA, CHOC = "#b3242c", "#f39ab2", "#9fdcbf", "#f7ecd0", "#6b3e26"
SPRINKLES = ["#e74c3c", "#f1c40f", "#3498db", "#ffffff", "#9b59b6", "#2ecc71", "#ff8fb3"]

# Scoop Pistol grip axis (gun-local), shared by the gun and the player's hand
GRIP_A, GRIP_B = Vector((0, 0.045, -0.03)), Vector((0, 0.088, -0.13))


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


# ------------------------------------------------------------------ materials

def clay(kit, name, hx, fp=1.0, rough=0.5, mottle=1.0):
    """Plasticine: waxy sheen, slight subsurface, colour mottling, fingerprint whorls and soft lumps (bump)."""
    key = ('Gclay', name, hx, fp)
    if key in kit._mats:
        return kit._mats[key]
    m = bpy.data.materials.new(f"G {name}")
    nt = v1.node_tree(m)
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    p = N("ShaderNodeBsdfPrincipled")
    L(p.outputs[0], out.inputs[0])
    col = hexc(hx)
    m.diffuse_color = col
    for k, v in {"Roughness": rough, "Specular IOR Level": 0.32, "Sheen Weight": 0.3, "Sheen Roughness": 0.35,
                 "Subsurface Weight": 0.12, "Subsurface Scale": 0.01, "Coat Weight": 0.08,
                 "Coat Roughness": 0.35}.items():
        p.inputs[k].default_value = v
    tc = N("ShaderNodeTexCoord")
    # colour mottling: kneaded plasticine is never one flat colour
    nz = N("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 3.5
    nz.inputs["Detail"].default_value = 3.0
    L(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = N("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[1].position = 0.3, 0.72
    e[0].color = tuple(c * (1 - 0.16 * mottle) for c in col[:3]) + (1,)
    e[1].color = tuple(min(1, c * (1 + 0.1 * mottle)) for c in col[:3]) + (1,)
    L(nz.outputs["Fac"], ramp.inputs[0])
    L(ramp.outputs[0], p.inputs["Base Color"])
    # fingerprints: concentric distorted rings around random voronoi cell centres, only in some cells
    vor = N("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 8.0
    L(tc.outputs["Object"], vor.inputs["Vector"])
    sub = N("ShaderNodeVectorMath")
    sub.operation = 'SUBTRACT'
    L(tc.outputs["Object"], sub.inputs[0])
    L(vor.outputs["Position"], sub.inputs[1])
    wave = N("ShaderNodeTexWave")
    wave.wave_type = 'RINGS'
    wave.inputs["Scale"].default_value = 30.0
    wave.inputs["Distortion"].default_value = 2.0
    wave.inputs["Detail"].default_value = 1.0
    L(sub.outputs[0], wave.inputs["Vector"])
    mask = N("ShaderNodeMapRange")
    mask.inputs["From Min"].default_value = 0.18
    mask.inputs["From Max"].default_value = 0.34
    mask.inputs["To Min"].default_value = 1.0
    mask.inputs["To Max"].default_value = 0.0
    L(vor.outputs["Distance"], mask.inputs["Value"])
    pick = N("ShaderNodeMath")
    pick.operation = 'GREATER_THAN'
    pick.inputs[1].default_value = 0.3
    L(vor.outputs["Color"], pick.inputs[0])
    m1 = N("ShaderNodeMath")
    m1.operation = 'MULTIPLY'
    L(mask.outputs[0], m1.inputs[0])
    L(pick.outputs[0], m1.inputs[1])
    m2 = N("ShaderNodeMath")
    m2.operation = 'MULTIPLY'
    L(m1.outputs[0], m2.inputs[0])
    L(wave.outputs["Fac"], m2.inputs[1])
    b1 = N("ShaderNodeBump")
    b1.inputs["Strength"].default_value = min(1.0, 0.6 * fp)
    b1.inputs["Distance"].default_value = 0.002
    L(m2.outputs[0], b1.inputs["Height"])
    # soft thumb-pressed dents
    nz2 = N("ShaderNodeTexNoise")
    nz2.inputs["Scale"].default_value = 14.0
    nz2.inputs["Detail"].default_value = 2.0
    L(tc.outputs["Object"], nz2.inputs["Vector"])
    b2 = N("ShaderNodeBump")
    b2.inputs["Strength"].default_value = 0.3
    b2.inputs["Distance"].default_value = 0.01
    L(nz2.outputs["Fac"], b2.inputs["Height"])
    L(b1.outputs["Normal"], b2.inputs["Normal"])
    L(b2.outputs["Normal"], p.inputs["Normal"])
    kit._mats[key] = m
    return m


def waffle(kit):
    """Waffle cone clay: criss-cross grooves pressed in with a modelling tool, around the -Y axis."""
    key = ('Gwaffle',)
    if key in kit._mats:
        return kit._mats[key]
    m = bpy.data.materials.new("G waffle")
    nt = v1.node_tree(m)
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    p = N("ShaderNodeBsdfPrincipled")
    L(p.outputs[0], out.inputs[0])
    p.inputs["Roughness"].default_value = 0.6
    p.inputs["Sheen Weight"].default_value = 0.3
    m.diffuse_color = hexc("#d9a35f")
    tc = N("ShaderNodeTexCoord")
    sep = N("ShaderNodeSeparateXYZ")
    L(tc.outputs["Object"], sep.inputs[0])
    ang = N("ShaderNodeMath")
    ang.operation = 'ARCTAN2'
    L(sep.outputs["X"], ang.inputs[0])
    L(sep.outputs["Z"], ang.inputs[1])
    wob = N("ShaderNodeTexNoise")
    wob.inputs["Scale"].default_value = 9.0
    L(tc.outputs["Object"], wob.inputs["Vector"])
    lines = []
    for sgn in (1, -1):
        a = N("ShaderNodeMath")
        a.operation = 'MULTIPLY'
        a.inputs[1].default_value = 7.0
        L(ang.outputs[0], a.inputs[0])
        b = N("ShaderNodeMath")
        b.operation = 'MULTIPLY_ADD'
        L(sep.outputs["Y"], b.inputs[0])
        b.inputs[1].default_value = 95.0 * sgn
        L(a.outputs[0], b.inputs[2])
        bw = N("ShaderNodeMath")
        bw.operation = 'MULTIPLY_ADD'
        L(wob.outputs["Fac"], bw.inputs[0])
        bw.inputs[1].default_value = 1.1 * sgn
        L(b.outputs[0], bw.inputs[2])
        s = N("ShaderNodeMath")
        s.operation = 'SINE'
        L(bw.outputs[0], s.inputs[0])
        ab = N("ShaderNodeMath")
        ab.operation = 'ABSOLUTE'
        L(s.outputs[0], ab.inputs[0])
        lines.append(ab)
    mn = N("ShaderNodeMath")
    mn.operation = 'MINIMUM'
    L(lines[0].outputs[0], mn.inputs[0])
    L(lines[1].outputs[0], mn.inputs[1])
    ramp = N("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position, e[1].position = 0.12, 0.34
    e[0].color = hexc("#9c5f28")
    e[1].color = hexc("#dcaa66")
    L(mn.outputs[0], ramp.inputs[0])
    L(ramp.outputs[0], p.inputs["Base Color"])
    hm = N("ShaderNodeMapRange")
    hm.inputs["From Min"].default_value = 0.05
    hm.inputs["From Max"].default_value = 0.4
    L(mn.outputs[0], hm.inputs["Value"])
    bump = N("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.7
    bump.inputs["Distance"].default_value = 0.004
    L(hm.outputs[0], bump.inputs["Height"])
    L(bump.outputs["Normal"], p.inputs["Normal"])
    kit._mats[key] = m
    return m


# ------------------------------------------------------------------ modelling helpers

def _tex(name, size):
    t = bpy.data.textures.get("G " + name)
    if t is None:
        t = bpy.data.textures.new("G " + name, 'CLOUDS')
        t.noise_scale = size
        t.noise_depth = 2
    return t


def lumps(ob, amp=0.012, size=0.09, fine=0.0035):
    """Hand-pinched irregularity: a broad lumpy displace plus a fine dent layer."""
    d = ob.modifiers.new("Lumps", 'DISPLACE')
    d.texture = _tex(f"lumps {size}", size)
    d.texture_coords = 'LOCAL'
    d.strength = amp
    if fine:
        d2 = ob.modifiers.new("Dents", 'DISPLACE')
        d2.texture = _tex("dents", 0.025)
        d2.texture_coords = 'LOCAL'
        d2.strength = fine
    return ob


def _cr(a, b, c, d, t):
    return 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t ** 3)


def resample(prof, k=3):
    out, n = [], len(prof)
    for i in range(n - 1):
        p0, p1, p2, p3 = prof[max(i - 1, 0)], prof[i], prof[i + 1], prof[min(i + 2, n - 1)]
        for s in range(k):
            out.append(tuple(_cr(a, b, c, d, s / k) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(prof[-1])
    return out


def rings(kit, name, prof, mat, parent, segs=16, k=2, warp=None, axis='z', sub=1, amp=0.014, size=0.09, fine=0.004,
          shape=None):
    """Lathe-style clay cage: profile of (h, rx, ry, offset) rings along local Z (or -Y with axis='y'), smoothed
    with a Catmull-Rom resample, capped, subdivided and displaced. Returns (object, dense profile)."""
    d = resample(prof, k)
    bm = bmesh.new()
    rows = []
    for h, rx, ry, off in d:
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            u, w = shape(a) if shape else (math.cos(a), math.sin(a))
            v = Vector((rx * u, off + ry * w, h))
            if axis == 'y':
                v = Vector((v.x, -v.z, v.y))
            if warp:
                v = warp(v)
            row.append(bm.verts.new(v))
        rows.append(row)
    for i in range(len(rows) - 1):
        for j in range(segs):
            bm.faces.new((rows[i][j], rows[i][(j + 1) % segs], rows[i + 1][(j + 1) % segs], rows[i + 1][j]))
    for row in (rows[0], rows[-1]):
        c = sum((v.co for v in row), Vector()) / segs
        pole = bm.verts.new(c)
        for j in range(segs):
            bm.faces.new((row[j], row[(j + 1) % segs], pole))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if sub:
        s = ob.modifiers.new("Subdivision", 'SUBSURF')
        s.levels = s.render_levels = sub
    if amp:
        lumps(ob, amp, size, fine)
    return ob, d


def surf(d, x, h, out=0.0):
    """Point on the front (-Y) of a z-axis rings profile, pushed `out` along the surface normal."""
    h = min(max(h, d[0][0]), d[-1][0])
    for i in range(len(d) - 1):
        if d[i][0] <= h <= d[i + 1][0]:
            t = (h - d[i][0]) / max(1e-6, d[i + 1][0] - d[i][0])
            rx, ry, off = (d[i][j] + (d[i + 1][j] - d[i][j]) * t for j in (1, 2, 3))
            break
    y = off - ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2))
    n = Vector((x / rx ** 2, (y - off) / ry ** 2, 0)).normalized()
    return Vector((x, y, h)) + n * out, n


def sausage(kit, name, pts, r, mat, parent, sub=1, amp=0.0):
    """Rolled clay snake along a polyline."""
    radii = r if isinstance(r, (list, tuple)) else [r] * len(pts)
    ob = kit.skin(name, [tuple(p) for p in pts], [(i, i + 1) for i in range(len(pts) - 1)], radii, mat, parent,
                  subsurf=sub)
    if amp:
        lumps(ob, amp, 0.06, 0.0)
    return ob


def _rotm(rot):
    if rot is None:
        return Matrix.Identity(3)
    if isinstance(rot, (Matrix,)):
        return rot
    return Euler([math.radians(a) for a in rot]).to_matrix()


def blob(kit, name, c, radii, mat, parent, rot=None, wob=0.08, segs=14, rings_=8, floor=None, amp=0.0,
         outline=None, flat=None):
    """Pinched clay lump: noisy UV sphere. outline(theta) scales the XY silhouette; flat(z) reshapes height
    (both in the unit sphere frame) before radii, rotation and translation are applied."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segs, v_segments=rings_, radius=1)
    o = Vector((kit.rand.uniform(-60, 60), kit.rand.uniform(-60, 60), kit.rand.uniform(-60, 60)))
    R = _rotm(rot)
    for v in bm.verts:
        n = v.co.copy()
        if outline:
            f = outline(math.atan2(n.y, n.x))
            n.x *= f
            n.y *= f
        if flat:
            n.z = flat(n.z, math.hypot(n.x, n.y))
        n *= 1 + wob * mnoise.noise(v.co * 1.4 + o)
        n = Vector((n.x * radii[0], n.y * radii[1], n.z * radii[2]))
        n = R @ n + Vector(c)
        if floor is not None:
            n.z = max(n.z, floor)
        v.co = n
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if amp:
        lumps(ob, amp, 0.05, 0.0)
    return ob


def drop(kit, name, pos, tail, r, length, mat, parent):
    """Flying clay teardrop; the tail points along `tail`."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1)
    o = Vector((kit.rand.uniform(-60, 60), 0, kit.rand.uniform(-60, 60)))
    for v in bm.verts:
        n = v.co * (1 + 0.1 * mnoise.noise(v.co * 1.5 + o))
        if n.z > 0:
            t = n.z
            n.z = n.z + (length / r - 1) * t * t
            n.x *= 1 - 0.55 * t
            n.y *= 1 - 0.55 * t
        v.co = n * r
    q = Vector(tail).normalized().to_track_quat('Z', 'Y')
    bmesh.ops.rotate(bm, matrix=q.to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(pos), verts=bm.verts)
    return kit.mesh_from_bmesh(name, bm, mat, parent)


def pancake(kit, name, c, R, H, mat, parent, normal=None, spikes=0, floor=True, wob=0.08):
    """Squashed clay splat: lobed (or spiky) outline, flat bottom and a plateau top."""
    rnd = kit.rand
    lob = [(rnd.uniform(0, 6.28), rnd.uniform(0.05, 0.14), rnd.randint(2, 5)) for _ in range(3)]
    sp = [(rnd.uniform(0, 6.28), rnd.uniform(0.35, 0.9)) for _ in range(spikes)]

    def outline(th):
        f = 1 + sum(a * math.sin(n * th + ph) for ph, a, n in lob)
        for a0, ln in sp:
            f += ln * max(0.0, math.cos(th - a0)) ** 60
        return f

    def flat(z, rr):
        s = abs(z) ** 0.45
        z2 = s if z > 0 else (-s if not floor else 0.0)
        return z2 / max(1.0, rr ** 1.5)
    rot = None if normal is None else Vector(normal).normalized().to_track_quat('Z', 'Y').to_matrix()
    return blob(kit, name, c, (R, R, H), mat, parent, rot=rot, wob=wob, segs=48 if spikes else 24, rings_=8,
                outline=outline, flat=flat)


def chunk(kit, name, c, r, mat, parent):
    """Torn-off clay chunk with fingerprints."""
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1)
    o = Vector((kit.rand.uniform(-60, 60), kit.rand.uniform(-60, 60), kit.rand.uniform(-60, 60)))
    sc = Vector((kit.rand.uniform(0.8, 1.3), kit.rand.uniform(0.7, 1.1), kit.rand.uniform(0.6, 1.0)))
    for v in bm.verts:
        n = v.co * (1 + 0.32 * mnoise.noise(v.co * 1.1 + o))
        v.co = Vector((n.x * sc.x, n.y * sc.y, n.z * sc.z)) * r
    bmesh.ops.rotate(bm, matrix=Euler([kit.rand.uniform(0, 6.28) for _ in range(3)]).to_matrix(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    return kit.mesh_from_bmesh(name, bm, mat, parent)


def sprinkle(kit, name, c, mat, parent, length=0.024, r=0.0055):
    d = Euler([kit.rand.uniform(0, 6.28) for _ in range(3)]).to_matrix() @ Vector((0, 0, length / 2))
    return sausage(kit, name, [Vector(c) - d, Vector(c) + d], r, mat, parent, sub=1)


def mtx(loc, rot=(0, 0, 0)):
    return Matrix.Translation(Vector(loc)) @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()


def pivot(kit, name, parent, M):
    p = kit.empty(name, parent)
    p.matrix_basis = M
    return p


def open_hand(kit, name, wrist, d, a, n, mat, parent, size=1.0, curl=0.35, spread=1.0):
    """Mitten palm plus four sausage fingers and a thumb. d: finger direction, a: across palm, n: palm normal."""
    d, a, n = Vector(d).normalized(), Vector(a).normalized(), Vector(n).normalized()
    wrist = Vector(wrist)
    pc = wrist + d * 0.04 * size
    M = Matrix((a, n, d)).transposed()
    blob(kit, f"{name} palm", pc, (0.04 * size, 0.022 * size, 0.042 * size), mat, parent, rot=M, wob=0.1)
    for i in range(4):
        u = (i - 1.5) / 1.5
        base = pc + d * 0.03 * size + a * u * 0.028 * size
        dd = (d + a * u * 0.18 * spread).normalized()
        p1 = base + dd * 0.032 * size
        p2 = p1 + (dd * (1 - curl) + n * curl).normalized() * 0.028 * size
        ln = 1.0 - abs(u - 0.2) * 0.12
        sausage(kit, f"{name} finger{i}", [base, p1, base + (p2 - base) * ln], [0.013 * size, 0.012 * size,
                                                                             0.011 * size], mat, parent, sub=1)
    t0 = pc + a * 0.035 * size
    sausage(kit, f"{name} thumb", [t0, t0 + (a * 0.6 + d * 0.5 + n * 0.3).normalized() * 0.04 * size],
            [0.014 * size, 0.012 * size], mat, parent, sub=1)


# ------------------------------------------------------------------ gun

def build_gun(kit, root):
    green = clay(kit, "gun green", GUN_G)
    dgreen = clay(kit, "gun green dark", hex_scale(GUN_G, 0.72))
    red = clay(kit, "gun red", GUN_R)
    cream = clay(kit, "tub", "#f6efe0")
    choc = clay(kit, "chocolate", CHOC)
    waf = waffle(kit)
    # chunky bean body along -Y
    rings(kit, "gun body", [(-0.098, 0.012, 0.012, 0.0), (-0.088, 0.036, 0.042, 0.0), (-0.055, 0.046, 0.053, 0.0),
                            (-0.005, 0.044, 0.05, 0.0), (0.04, 0.036, 0.04, 0.004), (0.07, 0.026, 0.028, 0.006),
                            (0.1, 0.022, 0.022, 0.006), (0.104, 0.008, 0.008, 0.006)],
          green, root, segs=14, k=1, axis='y', sub=1, amp=0.01, size=0.035, fine=0.002)
    # waffle cone muzzle (cup: outer wall, rolled lip, inner wall)
    rings(kit, "gun cone", [(0.085, 0.02, 0.02, 0.006), (0.11, 0.03, 0.03, 0.006), (0.15, 0.048, 0.048, 0.006),
                            (0.182, 0.068, 0.068, 0.006), (0.192, 0.072, 0.072, 0.006), (0.19, 0.06, 0.06, 0.006),
                            (0.165, 0.046, 0.046, 0.006), (0.135, 0.026, 0.026, 0.006), (0.12, 0.006, 0.006, 0.006)],
          waf, root, segs=14, k=1, axis='y', sub=1, amp=0.003, size=0.03, fine=0.0)
    ring_pts = [(0.069 * math.cos(a), -0.19, 0.006 + 0.069 * math.sin(a))
                for a in [i * 2 * math.pi / 11 for i in range(13)]]
    sausage(kit, "gun cone rim", ring_pts, 0.008, clay(kit, "cone rim", "#b8783a"), root, sub=1)
    blob(kit, "gun ammo scoop", (0, -0.165, 0.008), (0.042, 0.03, 0.04), clay(kit, "strawberry", PINK), root,
         wob=0.18)
    # pint-tub magazine on top with a chocolate scoop and sprinkles
    rings(kit, "gun pint tub", [(0.03, 0.026, 0.026, 0), (0.036, 0.03, 0.03, 0), (0.07, 0.034, 0.034, 0),
                                         (0.1, 0.038, 0.038, 0), (0.104, 0.036, 0.036, 0), (0.106, 0.03, 0.03, 0)],
                   cream, root, segs=12, k=1, sub=1, amp=0.002, size=0.03, fine=0.0)
    band = [(0.036 * math.cos(a), 0.036 * math.sin(a), 0.072) for a in [i * 2 * math.pi / 9 for i in range(11)]]
    sausage(kit, "gun tub band", band, 0.009, red, root, sub=1)
    collar = [(0.033 * math.cos(a), 0.033 * math.sin(a), 0.036) for a in [i * 2 * math.pi / 9 for i in range(11)]]
    sausage(kit, "gun tub collar", collar, 0.008, dgreen, root, sub=1)
    blob(kit, "gun scoop", (0, 0, 0.122), (0.043, 0.043, 0.033), choc, root, wob=0.2, segs=18, amp=0.006)
    for i in range(7):
        a = i * 0.9 + 0.3
        blob(kit, "gun scoop ruffle", (0.04 * math.cos(a), 0.04 * math.sin(a), 0.107), (0.022, 0.02, 0.01),
             choc, root, wob=0.2, segs=10, rings_=7)
    for i in range(12):
        a = i * 2.39996 + 0.4
        el = math.radians(25 + (i % 4) * 16)
        p = Vector((0.041 * math.cos(a) * math.cos(el), 0.041 * math.sin(a) * math.cos(el),
                    0.122 + 0.033 * math.sin(el)))
        sprinkle(kit, f"gun sprinkle{i}", p, clay(kit, f"sprinkle{i % 7}", SPRINKLES[i % 7]), root, 0.018, 0.0045)
    # grip, guard and trigger
    mid = (GRIP_A + GRIP_B) / 2
    sausage(kit, "gun grip", [GRIP_A + Vector((0, 0, 0.02)), mid, GRIP_B], [0.026, 0.026, 0.028], red, root, sub=1,
            amp=0.003)
    blob(kit, "gun pommel", GRIP_B + Vector((0, 0.003, -0.01)), (0.03, 0.034, 0.018), red, root, rot=(-22, 0, 0))
    sausage(kit, "gun guard", [(0, -0.03, -0.035), (0, -0.036, -0.068), (0, -0.018, -0.094), (0, 0.018, -0.1),
                               (0, 0.05, -0.088)], 0.0075, dgreen, root, sub=1)
    sausage(kit, "gun trigger", [(0, -0.002, -0.04), (0, -0.012, -0.062), (0, -0.004, -0.078)], [0.008, 0.007, 0.006],
            red, root, sub=1)
    # details: back hammer, front sight, side stripes and rivets
    blob(kit, "gun hammer", (0, 0.1, 0.03), (0.014, 0.02, 0.016), dgreen, root, rot=(-30, 0, 0))
    blob(kit, "gun sight", (0, -0.062, 0.035), (0.01, 0.016, 0.014), red, root)
    for s in (1, -1):
        sausage(kit, "gun stripe", [(s * 0.043, 0.07, 0.004), (s * 0.047, 0.02, 0.0), (s * 0.042, -0.035, -0.002),
                                    (s * 0.033, -0.07, 0.0)], [0.006, 0.008, 0.007, 0.005], red, root, sub=1)
        for j, y in enumerate((0.055, -0.02)):
            blob(kit, f"gun rivet{j}", (s * 0.046, y, -0.025), (0.004, 0.009, 0.009), cream, root, rot=(0, 0, 0),
                 wob=0.1, segs=10, rings_=6)


# ------------------------------------------------------------------ player

def build_player(kit, root):
    skin = clay(kit, "skin", SKIN)
    cheek = clay(kit, "skin cheek", "#f09d7c")
    shirt = clay(kit, "shirt", SHIRT)
    trou = clay(kit, "trousers", TROUSER)
    shoe = clay(kit, "shoes", SHOE)
    apron = clay(kit, "apron", "#f4ecdc")
    dark = clay(kit, "mouth", "#3a1717", fp=0.3)
    tooth = clay(kit, "teeth", "#fcf8ec", fp=0.3)
    eye = clay(kit, "eye", "#fbfaf4", fp=0.2, mottle=0.2)
    pupil = clay(kit, "pupil", "#151111", fp=0.0)
    brow = clay(kit, "brow", "#6b4630")
    hat = clay(kit, "hat", "#fbf8f0", mottle=0.4)
    navy = clay(kit, "strap", "#2f3e5c")
    lid = clay(kit, "cooler lid", "#8fc3e0")

    # legs: thin wire limbs in trouser clay, big red shoes
    for s, fy in ((1, -0.09), (-1, 0.05)):
        x = 0.1 * s
        sausage(kit, "leg", [(x, 0.0, 0.58), (x + 0.01 * s, fy * 0.5 - 0.03, 0.31), (x + 0.012 * s, fy, 0.09)],
                [0.045, 0.036, 0.034], trou, root, amp=0.004)
        blob(kit, "trouser cuff", (x + 0.012 * s, fy, 0.105), (0.047, 0.047, 0.026), trou, root, wob=0.12)
        blob(kit, "shoe", (x + 0.014 * s, fy - 0.045, 0.045), (0.07, 0.125, 0.06), shoe, root, wob=0.1, floor=0.0,
             amp=0.006)
    # chunky pear body
    rings(kit, "trousers", [(0.48, 0.1, 0.085, 0), (0.52, 0.16, 0.13, 0), (0.6, 0.19, 0.155, -0.01),
                            (0.68, 0.2, 0.165, -0.015), (0.72, 0.12, 0.1, -0.01)], trou, root, amp=0.012)
    shirt_p = [(0.6, 0.1, 0.08, 0), (0.64, 0.18, 0.145, -0.01), (0.76, 0.215, 0.18, -0.025),
               (0.88, 0.205, 0.165, -0.015), (0.98, 0.18, 0.14, 0), (1.05, 0.13, 0.105, 0.005),
               (1.1, 0.05, 0.05, 0.01)]
    _, ds = rings(kit, "shirt", shirt_p, shirt, root, segs=20, amp=0.014)
    dt = resample([(0.48, 0.1, 0.085, 0), (0.52, 0.16, 0.13, 0), (0.6, 0.19, 0.155, -0.01),
                   (0.68, 0.2, 0.165, -0.015), (0.72, 0.12, 0.1, -0.01)])

    # apron: a clay slab pressed onto the belly
    bm = bmesh.new()
    nx, nz = 8, 12
    grid = []
    for iz in range(nz + 1):
        z = 0.4 + (1.0 - 0.4) * iz / nz
        w = 0.095 if z > 0.82 else (0.19 if z < 0.72 else 0.19 - (z - 0.72) / 0.1 * 0.095)
        row = []
        for ix in range(nx + 1):
            x = -w + 2 * w * ix / nx
            ys = surf(ds, x, z)[0].y if z >= 0.62 else 1.0
            yt = surf(dt, x, z)[0].y if 0.5 <= z <= 0.72 else 1.0
            y = min(ys, yt)
            if z < 0.5:
                y = min(surf(dt, x, 0.5)[0].y, -0.1) - (0.5 - z) * 0.08
            if z < 0.42:
                z += 0.012 * math.sin(ix * 2.1)
            row.append(bm.verts.new((x, y - 0.012, z)))
        grid.append(row)
    for iz in range(nz):
        for ix in range(nx):
            bm.faces.new((grid[iz][ix], grid[iz][ix + 1], grid[iz + 1][ix + 1], grid[iz + 1][ix]))
    ap = kit.mesh_from_bmesh("apron", bm, apron, root)
    so = ap.modifiers.new("Thickness", 'SOLIDIFY')
    so.thickness = 0.016
    so.offset = 0
    s = ap.modifiers.new("Subdivision", 'SUBSURF')
    s.levels = s.render_levels = 1
    lumps(ap, 0.006, 0.06, 0.002)
    for s_ in (1, -1):
        p0 = surf(ds, 0.085 * s_, 0.99, 0.01)[0]
        sausage(kit, "apron strap", [p0, surf(ds, 0.075 * s_, 1.05, 0.008)[0], (0.06 * s_, -0.05, 1.1)], 0.011,
                apron, root, sub=1)
        sausage(kit, "apron tie", [surf(dt, 0.18 * s_, 0.7, 0.008)[0], (0.205 * s_, 0.0, 0.7),
                                   (0.17 * s_, 0.13, 0.7)], 0.011, apron, root, sub=1)
    pk = surf(ds, 0.0, 0.66, 0.02)[0]
    blob(kit, "apron pocket", pk, (0.08, 0.012, 0.045), apron, root, wob=0.05)
    # cooler backpack with spare pints
    cool = kit.prim("cooler", 'box', (0.3, 0.17, 0.28), clay(kit, "cooler", "#eef0ee", mottle=0.5), root,
                    offset=(0, 0.25, 0.83), bevel=0.05, bevel_segments=2)
    s = cool.modifiers.new("Subdivision", 'SUBSURF')
    s.levels = s.render_levels = 1
    lumps(cool, 0.01, 0.08)
    cl = kit.prim("cooler lid", 'box', (0.32, 0.19, 0.06), lid, root, offset=(0, 0.25, 0.985), bevel=0.025,
                  bevel_segments=2)
    s = cl.modifiers.new("Subdivision", 'SUBSURF')
    s.levels = s.render_levels = 1
    lumps(cl, 0.006, 0.06)
    for i, (px, col) in enumerate(((-0.085, PINK), (0.0, CHOC), (0.085, MINT))):
        rings(kit, "spare pint", [(1.01, 0.03, 0.03, 0), (1.015, 0.036, 0.036, 0), (1.08, 0.041, 0.041, 0),
                                  (1.088, 0.04, 0.04, 0), (1.09, 0.02, 0.02, 0)],
              clay(kit, f"pint{i}", col), root, segs=12, amp=0.004, size=0.03, fine=0.0)[0].location = (px, 0.26, 0)
        blob(kit, "pint lid", (px, 0.26, 1.093), (0.043, 0.043, 0.012), hat, root, wob=0.06)
    sausage(kit, "bungee", [(-0.14, 0.24, 1.05), (-0.04, 0.215, 1.06), (0.04, 0.215, 1.06), (0.14, 0.24, 1.05)],
            0.009, clay(kit, "bungee", "#f1c40f"), root, sub=1)
    for s_ in (1, -1):
        sausage(kit, "backpack strap", [(s_ * 0.11, 0.17, 0.96), (s_ * 0.115, 0.1, 1.06), (s_ * 0.12, -0.02, 1.07),
                                        (s_ * 0.135, -0.12, 0.99), (s_ * 0.16, -0.155, 0.86)], 0.014, navy, root,
                sub=1)
    # sleeves and thin wire arms
    for s_ in (1, -1):
        blob(kit, "sleeve", (s_ * 0.205, 0.0, 0.985), (0.07, 0.072, 0.075), shirt, root, rot=(0, s_ * 25, 0),
             wob=0.12, amp=0.006)
    G = Vector((-0.16, -0.44, 1.075))
    gp = kit.empty("held gun", root, G)
    build_gun(kit, gp)
    wrist = Vector((-0.032, 0.11, -0.09))
    sausage(kit, "right arm", [(-0.21, 0.0, 0.98), (-0.255, -0.17, 0.905), G + wrist], [0.032, 0.027, 0.026],
            skin, root, amp=0.003)
    # right hand wrapped around the grip (built in gun space)
    ax = (GRIP_B - GRIP_A).normalized()
    f = Vector((0, -ax.z, ax.y)) * -1
    f = Vector((0, -abs(f.y), -abs(f.z)))
    for i, t in enumerate((0.12, 0.37, 0.62, 0.86)):
        c = GRIP_A + (GRIP_B - GRIP_A) * t
        pts = []
        for j, phi in enumerate((5, 60, 115, 165)):
            r = 0.039 if j < 3 else 0.034
            ph = math.radians(phi)
            pts.append(c + (Vector((-1, 0, 0)) * math.cos(ph) + f * math.sin(ph)) * r)
        sausage(kit, f"grip finger{i}", pts, [0.014, 0.0135, 0.013, 0.012], skin, gp, sub=1)
    blob(kit, "grip palm", GRIP_A + (GRIP_B - GRIP_A) * 0.5 + Vector((-0.036, 0.012, 0)), (0.026, 0.05, 0.06),
         skin, gp, rot=(-22, 0, 0), wob=0.1)
    sausage(kit, "grip thumb", [(-0.034, 0.05, -0.03), (-0.01, 0.045, -0.006), (0.03, 0.03, -0.01),
                                (0.046, 0.005, -0.012)], [0.016, 0.015, 0.014, 0.012], skin, gp, sub=1)
    # left arm hangs loose with an open mitten hand
    lw = Vector((0.3, -0.05, 0.64))
    sausage(kit, "left arm", [(0.21, 0.0, 0.98), (0.29, 0.03, 0.8), lw], [0.032, 0.027, 0.026], skin, root,
            amp=0.003)
    open_hand(kit, "left hand", lw, (0.05, -0.15, -1), (0, -1, 0.1), (-1, 0, 0), skin, root, curl=0.45)

    # head: wide-jawed egg with a big grin
    hp = [(1.06, 0.04, 0.04, -0.01), (1.09, 0.12, 0.1, -0.025), (1.15, 0.165, 0.14, -0.03),
          (1.22, 0.168, 0.145, -0.022), (1.30, 0.158, 0.142, -0.01), (1.38, 0.14, 0.13, 0.0),
          (1.45, 0.1, 0.1, 0.005), (1.49, 0.03, 0.03, 0.01)]
    _, dh = rings(kit, "head", hp, skin, root, segs=20, k=3, amp=0.009, size=0.08)
    # grin
    mz = lambda x: 1.168 + 2.6 * x * x
    xs = [-0.11 + 0.22 * i / 6 for i in range(7)]
    sausage(kit, "mouth", [surf(dh, x, mz(x), -0.012)[0] for x in xs],
            [0.012 + 0.016 * math.sin(math.pi * i / 6) for i in range(7)], dark, root, sub=1)
    sausage(kit, "upper lip", [surf(dh, x * 1.03, mz(x) + 0.03 + 0.004 * math.cos(x * 20), 0.0)[0] for x in xs],
            [0.009 + 0.006 * math.sin(math.pi * i / 6) for i in range(7)], skin, root, sub=1)
    sausage(kit, "lower lip", [surf(dh, x * 1.03, mz(x) - 0.03 - 0.01 * math.cos(x * 14), 0.0)[0] for x in xs],
            [0.009 + 0.009 * math.sin(math.pi * i / 6) for i in range(7)], skin, root, sub=1)
    for i in range(6):
        x = -0.0725 + 0.029 * i
        p, n = surf(dh, x, mz(x) + 0.008, 0.008)
        kit.prim("tooth", 'box', (0.027, 0.012, 0.03), tooth, root, offset=p,
                 rot=(0, -math.degrees(math.atan(5.2 * x)), math.degrees(math.atan2(n.x, -n.y))),
                 bevel=0.005, bevel_segments=2)
    for s_ in (1, -1):
        blob(kit, "cheek", surf(dh, 0.115 * s_, 1.215, -0.01)[0], (0.045, 0.035, 0.04), cheek, root, wob=0.1)
    blob(kit, "nose", surf(dh, 0.0, 1.25, 0.012)[0], (0.046, 0.042, 0.044), cheek, root, wob=0.08)
    # ping-pong eyes under heavy brows
    for s_ in (1, -1):
        c, n = surf(dh, 0.046 * s_, 1.335, -0.004)
        blob(kit, "eye", c, (0.047, 0.047, 0.047), eye, root, wob=0.03, segs=18)
        look = Vector((-0.12 * s_ - 0.08, -1, -0.05)).normalized()
        blob(kit, "pupil", c + look * 0.045, (0.013, 0.013, 0.006), pupil, root,
             rot=look.to_track_quat('Z', 'Y').to_matrix(), wob=0.03, segs=10, rings_=6)
        bpts = [surf(dh, x * s_, z, 0.03)[0] for x, z in ((0.006, 1.392), (0.05, 1.408), (0.096, 1.386))]
        sausage(kit, "brow", bpts, [0.017, 0.024, 0.015], brow, root, sub=1)
        blob(kit, "ear", (0.163 * s_, 0.005, 1.27), (0.022, 0.038, 0.048), skin, root, wob=0.1)
        blob(kit, "sideburn", (0.135 * s_, 0.035, 1.39), (0.035, 0.06, 0.045), brow, root, wob=0.15)
    # paper soda-jerk cap: a boat of clay pinched to a ridge
    def capshape(a):
        sa = math.sin(a)
        return math.cos(a) * (1 - 0.93 * max(0.0, sa)) ** 1.6, (sa if sa > 0 else 0.12 * sa)
    cap = kit.empty("cap pivot", root, (0, 0.0, 1.442), (0, 6, 0))
    rings(kit, "cap", [(-0.15, 0.06, 0.07, 0.0), (-0.13, 0.1, 0.1, 0.0), (0.0, 0.13, 0.12, 0.0),
                       (0.13, 0.1, 0.1, 0.0), (0.15, 0.06, 0.07, 0.0)], hat, cap, segs=20, axis='y',
          shape=capshape, amp=0.004, size=0.05)
    stripe = clay(kit, "cap stripe", "#c0392b")
    for s_ in (1, -1):
        pts = []
        for y in (-0.125, -0.07, 0.0, 0.07, 0.125):
            q = (abs(y) / 0.13) ** 2
            rx, ry = 0.13 - 0.03 * q, 0.12 - 0.02 * q
            sa = 0.018 / ry
            pts.append((s_ * (rx * math.sqrt(1 - sa * sa) * (1 - 0.93 * sa) ** 1.6 + 0.002), y, 0.018))
        sausage(kit, "cap stripe", pts, 0.009, stripe, cap, sub=1)


# ------------------------------------------------------------------ zombie

def build_zombie(kit, root, hit=False):
    zs = clay(kit, "zombie skin", Z_SKIN)
    zd = clay(kit, "zombie skin dark", hex_scale(Z_SKIN, 0.72))
    shirt = clay(kit, "zombie shirt", Z_SHIRT)
    trou = clay(kit, "zombie trousers", Z_TROUSER)
    dark = clay(kit, "zombie mouth", "#2a1414", fp=0.3)
    tooth = clay(kit, "zombie teeth", "#e9dfae", fp=0.3)
    eye = clay(kit, "zombie eye", "#f1ead0", fp=0.2, mottle=0.3)
    pupil = clay(kit, "pupil", "#151111", fp=0.0)
    brain = clay(kit, "brain", "#e58aa0")
    shoe = clay(kit, "zombie shoe", "#5b3a29")
    blood = clay(kit, "blood", BLOOD)
    pink = clay(kit, "strawberry", PINK)
    rz = root.rotation_euler.z

    def wdir(v):
        return Matrix.Rotation(-rz, 3, 'Z') @ Vector(v)

    # ---- legs (own pivots), feet planted
    for s, name in ((-1, "R"), (1, "L")):
        lp = kit.empty(f"zombie leg {name}", root, (0.1 * s, 0, 0.56))
        if s < 0:
            knee, ankle = Vector((-0.01, -0.12, -0.25)), Vector((-0.02, -0.13, -0.5))
            sausage(kit, "thigh", [(0, 0, 0), knee], [0.05, 0.042], trou, lp, amp=0.004)
            sausage(kit, "shin", [knee, ankle], [0.033, 0.03], zs, lp, amp=0.003)

            def rag(v, c=knee):
                a = math.atan2(v.y - c.y, v.x - c.x)
                return v + Vector((0, 0, -0.02 * abs(math.sin(a * 3.5)) - 0.012 * math.sin(a * 7)))
            rings(kit, "torn cuff", [(-0.05, 0.048, 0.048, 0), (-0.035, 0.056, 0.056, 0), (0.03, 0.05, 0.05, 0),
                                     (0.04, 0.03, 0.03, 0)], trou, kit.empty("cuff", lp, knee), segs=14, warp=rag,
                  amp=0.004)
            foot = ankle + Vector((0, -0.05, -0.035))
            blob(kit, "bare foot", foot, (0.055, 0.095, 0.04), zs, lp, wob=0.12, floor=-0.56)
            for t in range(3):
                blob(kit, "toe", foot + Vector((-0.03 + 0.03 * t, -0.085 + 0.006 * abs(t - 1), -0.012)),
                     (0.017, 0.02, 0.016), zs, lp, wob=0.1, segs=10, rings_=6)
        else:
            knee, ankle = Vector((0.01, 0.03, -0.26)), Vector((0.02, 0.1, -0.5))
            sausage(kit, "leg", [(0, 0, 0), knee, ankle], [0.05, 0.04, 0.036], trou, lp, amp=0.004)
            blob(kit, "cuff", ankle + Vector((0, 0, 0.02)), (0.048, 0.048, 0.03), trou, lp, wob=0.2)
            foot = ankle + Vector((0, -0.05, -0.02))
            blob(kit, "shoe", foot, (0.065, 0.115, 0.05), shoe, lp, wob=0.12, floor=-0.56, amp=0.005)
            blob(kit, "toe poking out", foot + Vector((0.01, -0.115, 0.0)), (0.022, 0.025, 0.02), zs, lp, wob=0.1,
                 segs=10, rings_=6)
    rings(kit, "zombie pelvis", [(0.42, 0.1, 0.09, 0), (0.46, 0.15, 0.12, 0), (0.55, 0.17, 0.14, 0),
                                 (0.61, 0.165, 0.135, -0.005), (0.65, 0.1, 0.09, 0)], trou, root, amp=0.012)

    # ---- torso: slumped forward (recoils back when hit)
    T = mtx((0, 0, 0.58), (-12, -14, -10) if hit else (28, 0, 0))
    torso = pivot(kit, "zombie torso", root, T)
    rings(kit, "belly", [(-0.02, 0.12, 0.1, 0), (0.04, 0.17, 0.145, -0.02), (0.12, 0.18, 0.155, -0.03),
                         (0.18, 0.15, 0.12, -0.01)], zs, torso, amp=0.012)

    def hem(v):
        if v.z < 0.2:
            a = math.atan2(v.y, v.x)
            t = (0.2 - v.z) / 0.08
            v = v + Vector((0, 0, t * (0.045 * abs(math.sin(a * 4.5 + 0.7)) - 0.02 * math.sin(a * 9))))
        return v
    zp = [(0.12, 0.13, 0.11, 0.0), (0.15, 0.19, 0.155, -0.012), (0.24, 0.2, 0.165, -0.02), (0.34, 0.19, 0.155, -0.005),
          (0.42, 0.165, 0.14, 0.02), (0.48, 0.12, 0.11, 0.03), (0.52, 0.05, 0.05, 0.03)]
    _, dz = rings(kit, "zombie shirt", zp, shirt, torso, segs=22, warp=hem, amp=0.014)
    # torn hole showing skin, buttons, ice cream splat
    hc, hn = surf(dz, 0.075, 0.27, 0.004)
    blob(kit, "shirt hole", hc, (0.045, 0.012, 0.038), zs, torso, wob=0.25)
    hole_pts = [surf(dz, 0.075 + 0.05 * math.cos(a), 0.27 + 0.043 * math.sin(a), 0.006)[0]
                for a in [i * 2 * math.pi / 12 + 0.3 for i in range(12)]]
    sausage(kit, "hole rim", hole_pts, [0.008, 0.011, 0.007, 0.012, 0.009, 0.01, 0.007, 0.012, 0.009, 0.011,
                                        0.008, 0.01], clay(kit, "rim", hex_scale(Z_SHIRT, 0.8)), torso, sub=1)
    for i, z in enumerate((0.42, 0.33)):
        blob(kit, "button", surf(dz, -0.005, z, 0.006)[0], (0.014, 0.008, 0.014), clay(kit, "button", "#3c2a1e"),
             torso, wob=0.05, segs=10, rings_=6)
    sp = surf(dz, -0.08, 0.36, 0.005)[0]
    blob(kit, "ice cream splat", sp, (0.075, 0.025, 0.06), pink, torso, wob=0.25)
    for i, (dx, ln) in enumerate(((-0.04, 0.09), (0.0, 0.13), (0.035, 0.07))):
        top = surf(dz, -0.08 + dx, 0.33, 0.006)[0]
        bot = surf(dz, -0.08 + dx, 0.33 - ln, 0.004)[0]
        sausage(kit, "splat drip", [top, (top + bot) / 2, bot], [0.016, 0.012, 0.014], pink, torso, sub=1)
    blob(kit, "mint chip", sp + Vector((0.02, -0.02, 0.02)), (0.018, 0.012, 0.014), clay(kit, "mint", MINT), torso,
         wob=0.2, segs=10, rings_=6)

    # ---- head (own pivot): droopy, melted, brain out
    H = T @ mtx((0, -0.01, 0.48), (-28, 10, 6) if hit else (6, -8, 12))
    head = pivot(kit, "zombie head", root, H)
    hp = [(-0.03, 0.05, 0.05, -0.04), (0.0, 0.14, 0.11, -0.06), (0.05, 0.172, 0.138, -0.062),
          (0.11, 0.162, 0.135, -0.045), (0.18, 0.135, 0.125, -0.02), (0.25, 0.12, 0.115, -0.005),
          (0.30, 0.105, 0.105, 0.0), (0.33, 0.06, 0.06, 0.005), (0.35, 0.02, 0.02, 0.005)]

    def melt(v):
        if v.z < 0.17:
            k = (0.17 - v.z) / 0.17 * abs(v.x) / 0.17
            v = v + Vector((0.012 * v.x / 0.17, 0, -(0.085 if v.x > 0 else 0.03) * k))
        return v
    _, dh = rings(kit, "zombie head", hp, zs, head, segs=20, k=3, warp=melt, amp=0.01, size=0.08)

    def fp(x, z, out=0.0):
        p, n = surf(dh, x, z, out)
        return melt(p), n
    # sagging mouth with big crooked teeth
    mz = lambda x: 0.04 - 1.4 * x * x - 0.15 * x
    xs = [-0.1 + 0.2 * i / 6 for i in range(7)]
    sausage(kit, "zombie mouth", [fp(x, mz(x), -0.012)[0] for x in xs],
            [0.012 + 0.02 * math.sin(math.pi * i / 6) for i in range(7)], dark, head, sub=1)
    sausage(kit, "zombie upper lip", [fp(x * 1.03, mz(x) + 0.036, 0.0)[0] for x in xs],
            [0.009 + 0.006 * math.sin(math.pi * i / 6) for i in range(7)], zd, head, sub=1)
    sausage(kit, "zombie lower lip", [fp(x * 1.03, mz(x) - 0.036, 0.0)[0] for x in xs],
            [0.01 + 0.014 * math.sin(math.pi * i / 6) for i in range(7)], zd, head, sub=1)
    for x, up, tilt in ((-0.062, 1, 8), (-0.03, 1, -6), (0.04, 1, 14), (-0.012, -1, -10), (0.03, -1, 6)):
        p, n = fp(x, mz(x) + 0.013 * up, 0.008)
        kit.prim("zombie tooth", 'box', (0.027, 0.012, 0.03 if up > 0 else 0.022), tooth, head, offset=p,
                 rot=(0, tilt, math.degrees(math.atan2(n.x, -n.y))), bevel=0.005, bevel_segments=2)
    # melted cheeks hanging past the jaw
    for s_, ln in ((-1, 0.075), (1, 0.12)):
        c = fp(0.12 * s_, 0.035, -0.035)[0]
        drop(kit, "melted cheek", c, (0.08 * s_, -0.12, -1), 0.055, ln, zs, head)
    blob(kit, "zombie nose", fp(-0.01, 0.115, 0.014)[0], (0.036, 0.036, 0.054), zd, head, rot=(-25, 0, 8), wob=0.1)
    # mismatched ping-pong eyes
    for x, z, r, look in ((-0.048, 0.2, 0.033, (0.3, -1, 0.35)), (0.058, 0.13, 0.05, (0.35, -1, -0.45))):
        c, n = fp(x, z, -0.006)
        blob(kit, "zombie eye", c, (r, r, r), eye, head, wob=0.04, segs=18)
        lk = Vector(look).normalized()
        pr = 0.011 if r < 0.04 else 0.008
        blob(kit, "zombie pupil", c + lk * r * 0.97, (pr, pr, 0.005), pupil, head,
             rot=lk.to_track_quat('Z', 'Y').to_matrix(), wob=0.03, segs=10, rings_=6)
    lid = [fp(x, z, 0.032)[0] for x, z in ((0.01, 0.16), (0.058, 0.172), (0.106, 0.15))]
    sausage(kit, "droopy eyelid", lid, [0.015, 0.024, 0.015], zs, head, sub=1)
    sag = [fp(x, z, 0.022)[0] for x, z in ((0.024, 0.097), (0.058, 0.084), (0.092, 0.097))]
    sausage(kit, "sagging lower lid", sag, [0.006, 0.009, 0.006], clay(kit, "inner lid", "#c4505a"), head, sub=1)
    sausage(kit, "zombie brow R", [fp(x, z, 0.03)[0] for x, z in ((-0.012, 0.25), (-0.05, 0.262), (-0.09, 0.236))],
            [0.016, 0.022, 0.013], zd, head, sub=1)
    sausage(kit, "zombie brow L", [fp(x, z, 0.04)[0] for x, z in ((0.015, 0.222), (0.062, 0.215), (0.11, 0.185))],
            [0.015, 0.02, 0.013], zd, head, sub=1)
    blob(kit, "zombie ear", melt(Vector((-0.135, 0.01, 0.16))), (0.022, 0.036, 0.046), zs, head, wob=0.15)
    blob(kit, "ear stub", melt(Vector((0.125, 0.01, 0.18))), (0.02, 0.025, 0.022), blood, head, wob=0.2)
    # exposed brain: pink clay snakes coiled in the open skull
    blob(kit, "brain", (0.0, 0.01, 0.29), (0.1, 0.095, 0.062), brain, head, wob=0.1)
    rim = [(0.108 * math.cos(a), 0.008 + 0.104 * math.sin(a), 0.275 + 0.012 * math.sin(a * 5))
           for a in [i * 2 * math.pi / 16 for i in range(18)]]
    sausage(kit, "skull rim", rim, [0.014 + 0.006 * math.sin(i * 1.7) for i in range(18)], zs, head, sub=1)
    for i in range(6):
        a0 = i * math.pi / 3 + 0.3
        pts = []
        for j in range(7):
            u = -0.8 + 1.6 * j / 6
            r0 = 0.062 * (1 - 0.3 * abs(u))
            ang = a0 + 0.5 * u
            rr = r0 + 0.012 * math.sin(j * 2.2 + i)
            z = 0.29 + 0.062 * math.sqrt(max(0, 1 - (rr / 0.1) ** 2)) + 0.004
            pts.append((rr * math.cos(ang), 0.01 + rr * math.sin(ang), z))
        sausage(kit, "brain fold", pts, 0.014, brain, head, sub=1)
    sausage(kit, "brain fold top", [(-0.045, 0.0, 0.346), (-0.015, 0.025, 0.352), (0.015, -0.005, 0.353),
                                    (0.045, 0.02, 0.345)], 0.014, brain, head, sub=1)

    # ---- arms (own pivots), reaching forward
    def arm(piv, s, name):
        if s < 0:
            elbow, wrist = Vector((-0.02, -0.2, -0.03)), Vector((-0.01, -0.38, -0.02))
        else:
            elbow, wrist = Vector((0.03, -0.18, -0.08)), Vector((0.04, -0.36, -0.1))

        def rag(v):
            a = math.atan2(v.z, v.x)
            if v.y < -0.06:
                v = v + Vector((0, -0.03 * abs(math.sin(a * 3 + s)) + 0.01 * math.sin(a * 7), 0))
            return v
        rings(kit, f"{name} sleeve", [(-0.04, 0.04, 0.04, 0), (-0.02, 0.068, 0.068, 0), (0.06, 0.064, 0.06, -0.01),
                                      (0.1, 0.062, 0.058, -0.012), (0.11, 0.04, 0.04, -0.012)], shirt, piv, segs=14,
              axis='y', warp=rag, amp=0.006)
        sausage(kit, f"{name} arm", [(0, 0, 0), elbow, wrist], [0.034, 0.028, 0.026], zs, piv, amp=0.003)
        dv = (wrist - elbow).normalized()
        open_hand(kit, f"{name} hand", wrist, dv + Vector((0, 0, -0.3)), (1, 0, 0), (0, 0, -1), zs, piv, curl=0.6,
                  size=1.05)
    arm(pivot(kit, "zombie arm R", root, T @ mtx((-0.2, 0.03, 0.42), (-60, 0, 0) if hit else (-18, 0, -6))), -1,
        "zombie R")
    sh = T @ Vector((0.2, 0.03, 0.42))
    if not hit:
        arm(pivot(kit, "zombie arm L", root, T @ mtx((0.2, 0.03, 0.42), (-30, 0, 8))), 1, "zombie L")
        return

    # ---- hit: left arm flies off spinning, clay burst
    q = wdir((0.8, 0.1, 0.6)).normalized().to_track_quat('-Y', 'Z') @ Euler((0, math.radians(70), 0)).to_quaternion()
    fly = pivot(kit, "zombie arm L (flying)", root, Matrix.Translation(sh + wdir((0.5, -0.3, 0.3))) @
                q.to_matrix().to_4x4())
    arm(fly, 1, "zombie L")
    blob(kit, "arm stump blob", (0, 0.0, 0), (0.05, 0.05, 0.05), blood, fly, wob=0.25)
    for i in range(5):
        a = i * 1.26
        drop(kit, "arm stump drip", (0.04 * math.cos(a), 0.035, 0.04 * math.sin(a)),
             (math.cos(a), 0.6, math.sin(a)), 0.016, 0.05, blood, fly)
    # wound on the torso shoulder
    blob(kit, "shoulder wound", (0.17, 0.03, 0.42), (0.06, 0.065, 0.065), blood, torso, wob=0.25)
    pancake(kit, "shoulder splat", (0.2, 0.03, 0.43), 0.08, 0.02, blood, torso, normal=(1, 0, 0.2), spikes=7,
            floor=False)

    out = wdir((1, -0.3, 0.55)).normalized()
    burst = sh + out * 0.24
    # big starburst splat in mid-air facing the camera: blood, strawberry, vanilla layers
    nrm = wdir((0.4, -1, 0.15))
    for i, (col, R, sk) in enumerate(((blood, 0.16, 9), (pink, 0.1, 7), (clay(kit, "vanilla", VANILLA), 0.05, 5))):
        pancake(kit, f"burst splat{i}", burst + nrm.normalized() * (0.014 * i), R, 0.024, col, root, normal=nrm,
                spikes=sk, floor=False, wob=0.15)
    # flying teardrops and fingerprinted chunks
    cols = [blood] * 6 + [pink] * 3 + [clay(kit, "mint", MINT), clay(kit, "vanilla", VANILLA),
                                       clay(kit, "chocolate", CHOC)]
    rnd = kit.rand
    for i in range(18):
        v = (out + wdir((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.5, 0.4), rnd.uniform(-0.6, 0.7)))).normalized()
        dist = rnd.uniform(0.35, 1.0)
        r = rnd.uniform(0.016, 0.042)
        drop(kit, f"fx drop{i}", sh + v * dist + Vector((0, 0, -0.25 * dist * dist)), -v, r,
             r * rnd.uniform(2.2, 4.0), cols[i % len(cols)], root)
    for i, (col, d0, rr) in enumerate(((pink, (0.5, -0.5, 0.75), 0.07), (blood, (0.9, -0.2, -0.1), 0.06),
                                       (clay(kit, "mint", MINT), (0.25, -0.7, 0.2), 0.05))):
        v = wdir(d0)
        pancake(kit, f"fx flying pancake{i}", sh + v, rr, 0.016, col, root,
                normal=wdir((rnd.uniform(-1, 1), -1, rnd.uniform(-1, 1))), spikes=3, floor=False, wob=0.15)
    for i in range(11):
        v = (out + wdir((rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(-0.4, 0.8)))).normalized()
        chunk(kit, f"fx chunk{i}", sh + v * rnd.uniform(0.3, 0.8), rnd.uniform(0.03, 0.06),
              clay(kit, "chunk" + str(i % 4), [BLOOD, PINK, CHOC, VANILLA][i % 4], fp=1.6), root)
    for i in range(4):
        v = (out + wdir((rnd.uniform(-0.3, 0.6), rnd.uniform(-0.6, 0.3), rnd.uniform(0.0, 0.6)))).normalized()
        blob(kit, f"fx cone shard{i}", sh + v * rnd.uniform(0.3, 0.7), (0.03, 0.022, 0.006), waffle(kit), root,
             rot=(rnd.uniform(0, 360), rnd.uniform(0, 360), 0), wob=0.25, outline=lambda th: 1 + 0.3 * math.cos(3 * th))
    for i in range(26):
        v = (out + wdir((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(-0.6, 0.8)))).normalized()
        sprinkle(kit, f"fx sprinkle{i}", sh + v * rnd.uniform(0.15, 0.9),
                 clay(kit, f"sprinkle{i % 7}", SPRINKLES[i % 7]), root)
    # thick splats squashed on the floor
    for i, (wx, wy, R, col) in enumerate(((0.45, -0.2, 0.17, blood), (0.75, -0.45, 0.12, blood),
                                          (0.2, -0.55, 0.1, pink), (0.95, -0.1, 0.09, blood),
                                          (0.5, 0.2, 0.08, pink), (0.62, -0.25, 0.08, pink),
                                          (1.05, -0.6, 0.06, blood), (0.3, -0.3, 0.05, clay(kit, "mint", MINT)))):
        c = wdir((wx, wy, 0)) + Vector((0, 0, 0.0))
        pancake(kit, f"floor splat{i}", c, R, 0.022 if R > 0.1 else 0.017, col, root, spikes=4 if R > 0.09 else 2)
        for j in range(3):
            a = rnd.uniform(0, 6.28)
            dd = R * rnd.uniform(1.3, 1.8)
            pancake(kit, f"floor droplet{i}.{j}", c + Vector((dd * math.cos(a), dd * math.sin(a), 0)),
                    R * rnd.uniform(0.12, 0.22), 0.012, col, root)
    for i in range(10):
        c = wdir((rnd.uniform(0.2, 1.0), rnd.uniform(-0.6, 0.1), 0)) + Vector((0, 0, 0.006))
        sprinkle(kit, f"floor sprinkle{i}", c, clay(kit, f"sprinkle{i % 7}", SPRINKLES[i % 7]), root)


# ------------------------------------------------------------------ scene

def setup(scene, stage_collection):
    ld = bpy.data.lights.new("G warm fill", 'AREA')
    ld.energy = 260
    ld.size = 5
    ld.color = (1.0, 0.92, 0.82)
    ob = bpy.data.objects.new("G warm fill", ld)
    stage_collection.objects.link(ob)
    ob.location = (-3.0, -4.0, 5.5)
    ob.rotation_euler = (Vector((0.3, 1.5, 0.8)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
