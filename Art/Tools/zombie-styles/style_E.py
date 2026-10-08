"""Style E: 1950s B-movie halftone. Square-jawed soda jerk vs. a letterman-jacket ghoul, pulp-comic inked."""
import os
import sys
from common import *
from mathutils import Quaternion

KEY = "E"
LABEL = "1950s B-movie halftone"
SHADER = 'halftone'
WORLD = "#efe3c8"
FLOOR = "#e6d3ad"

INK = "#2a2320"
CREAM = "#efe3c8"
SHIRT = "#f7efdc"
TEAL = "#2f8f8a"
CHERRY = "#c8323c"
MUSTARD = "#d9a441"
NAVY = "#2b3a55"
SKIN = "#f2c79b"
ZSKIN = "#8fae6a"
HAIR = "#3b2a22"
CHOC = "#6b3f2a"
WAFFLE = "#cf9447"
ORANGE = "#e8772e"
SMOKE = "#d6c8aa"
BRAIN = "#e3868c"
TROUSER = "#5e5246"
SHOE = "#4a3528"
VANILLA = "#fbf3df"

FONT_BOLD = "/usr/share/fonts/gsfonts/NimbusSansNarrow-Bold.otf"
FONT_SERIF = "/usr/share/fonts/gsfonts/NimbusRoman-Bold.otf"

GUN_LINE = [0.0028]  # ink width for the gun; the held gun uses a thinner line


def e_halftone(m, color):
    """Halftone tuned for this style: lit faces stay clean flat ink colors, dots only grow into the shade."""
    nt = v1.node_tree(m)
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    diffuse = N("ShaderNodeBsdfDiffuse")
    to_rgb = N("ShaderNodeShaderToRGB")
    bw = N("ShaderNodeRGBToBW")
    L(diffuse.outputs[0], to_rgb.inputs[0])
    L(to_rgb.outputs[0], bw.inputs[0])
    sep = N("ShaderNodeSeparateXYZ")
    L(N("ShaderNodeTexCoord").outputs["Camera"], sep.inputs[0])

    def op(kind, a, b=None, clamp=False, c=None):
        node = N("ShaderNodeMath")
        node.operation = kind
        node.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                L(v, node.inputs[i])
        return node.outputs[0]
    depth = op('MULTIPLY', sep.outputs[2], -1.0)
    sx = op('DIVIDE', sep.outputs[0], depth)
    sy = op('DIVIDE', sep.outputs[1], depth)
    freq = 185 * 0.7071
    cu = op('SUBTRACT', op('FRACT', op('MULTIPLY', op('ADD', sx, sy), freq)), 0.5)
    cv = op('SUBTRACT', op('FRACT', op('MULTIPLY', op('SUBTRACT', sx, sy), freq)), 0.5)
    comb = N("ShaderNodeCombineXYZ")
    L(cu, comb.inputs[0])
    L(cv, comb.inputs[1])
    length = N("ShaderNodeVectorMath")
    length.operation = 'LENGTH'
    L(comb.outputs[0], length.inputs[0])
    radius = op('MINIMUM', op('MULTIPLY', op('SUBTRACT', 1.15, bw.outputs[0]), 0.9, clamp=True), 0.48)
    dot = op('LESS_THAN', length.outputs["Value"], radius)
    mix = N("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = color
    mix.inputs[7].default_value = tuple(x * 0.4 for x in color[:3]) + (1,)
    L(dot, mix.inputs[0])
    emit = N("ShaderNodeEmission")
    L(mix.outputs[2], emit.inputs[0])
    L(emit.outputs[0], out.inputs[0])
    m.diffuse_color = color


v1 = sys.modules["v1_styles"]
SHADERS['halftone'] = e_halftone


class EKit(Kit):
    """Kit with lighter defaults so the inked (outline-doubled) meshes stay inside the triangle budget."""

    def prim(self, name, kind, size, mat, parent=None, offset=(0, 0, 0), rot=(0, 0, 0), segments=None, rings=7, **kw):
        if segments is None:
            segments = 2 if kind == 'ico' else 12
        kw.setdefault('bevel_segments', 1)
        return super().prim(name, kind, size, mat, parent, offset, rot, segments, rings, **kw)

    def skin(self, name, points, edges, radii, mat, parent=None, subsurf=1, smooth=True, root=0):
        return super().skin(name, points, edges, radii, mat, parent, subsurf, smooth, root)


def make_kit(col, seed):
    return EKit(col, SHADER, seed)


# ------------------------------------------------------------------ helpers
def rot_matrix(rot):
    if isinstance(rot, (tuple, list)):
        return Euler([math.radians(a) for a in rot]).to_matrix()
    if isinstance(rot, Quaternion):
        return rot.to_matrix()
    return rot


def pose_matrix(loc, rot):
    return Matrix.Translation(Vector(loc)) @ rot_matrix(rot).to_4x4()


def loft(kit, name, secs, mats, parent=None, n=12, subsurf=1, mat_fn=None, rot=(0, 0, 0), offset=(0, 0, 0),
         line=None, smooth=True, even=False):
    """Superellipse cross-sections stacked along local Z. sec = (z, rx, ry, cx, cy, p, jag): p=2 ellipse,
    p>3 boxy; jag zigzags the ring for torn hems. Rotated/offset into parent space."""
    bm = bmesh.new()
    rings = []
    for s in secs:
        z, rx, ry, cx, cy, p, jag = (list(s) + [0, 0, 2, 0][len(s) - 3:])[:7]
        ring = []
        ts = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
        if even:
            ts = even_angles(rx, ry, p, n)
        for i, t in enumerate(ts):
            c, sn = math.cos(t), math.sin(t)
            x = cx + rx * math.copysign(abs(c) ** (2 / p), c)
            y = cy + ry * math.copysign(abs(sn) ** (2 / p), sn)
            zz = z + (jag if i % 2 else -jag * 0.6) * (0.6 + 0.8 * ((i * 37) % 7) / 6)
            ring.append(bm.verts.new((x, y, zz)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if mat_fn:
        for f in bm.faces:
            f.material_index = mat_fn(f.calc_center_median())
    bmesh.ops.transform(bm, matrix=rot_matrix(rot).to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)
    ob = kit.mesh_from_bmesh(name, bm, mats, parent, smooth=smooth)
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    if line:
        kit.outline(ob, line, INK)
    return ob


def even_angles(rx, ry, p, n, samples=720):
    """Superellipse parameters spaced by equal arc length, so boxy sections get even vertex spacing."""
    def pt(t):
        c, sn = math.cos(t), math.sin(t)
        return Vector((rx * math.copysign(abs(c) ** (2 / p), c), ry * math.copysign(abs(sn) ** (2 / p), sn)))
    ts = [-math.pi / 2 + 2 * math.pi * k / samples for k in range(samples + 1)]
    acc = [0.0]
    for a, b in zip(ts, ts[1:]):
        acc.append(acc[-1] + (pt(b) - pt(a)).length)
    out, j = [], 0
    for i in range(n):
        target = acc[-1] * i / n
        while acc[j + 1] < target:
            j += 1
        f = (target - acc[j]) / (acc[j + 1] - acc[j])
        out.append(ts[j] + (ts[j + 1] - ts[j]) * f)
    return out


def inked(kit, ob, w):
    kit.outline(ob, w, INK)
    return ob


def torus(kit, name, R, r, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), seg=12, rs=4, line=None):
    bm = bmesh.new()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(rs):
            b = 2 * math.pi * j / rs
            d = R + r * math.cos(b)
            ring.append(bm.verts.new((d * math.cos(a), d * math.sin(a), r * math.sin(b))))
        rings.append(ring)
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for j in range(rs):
            bm.faces.new((a[j], b[j], b[(j + 1) % rs], a[(j + 1) % rs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.transform(bm, matrix=rot_matrix(rot).to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    if line:
        inked(kit, ob, line)
    return ob


def sheet(kit, name, rows, cols, mat, parent, thick, line, subsurf=1):
    """Cloth/paper panel: rows = [(z, half_width, y_center, curve_depth)] across x, solidified."""
    bm = bmesh.new()
    grid = []
    for z, hw, yc, d in rows:
        row = []
        for j in range(cols):
            u = -1 + 2 * j / (cols - 1)
            row.append(bm.verts.new((u * hw, yc + d * u * u, z)))
        grid.append(row)
    for a, b in zip(grid, grid[1:]):
        for j in range(cols - 1):
            bm.faces.new((a[j], a[j + 1], b[j + 1], b[j]))
    ob = kit.mesh_from_bmesh(name, bm, mat, parent)
    sol = ob.modifiers.new("Thick", 'SOLIDIFY')
    sol.thickness = thick
    sol.offset = 0
    if subsurf:
        sub = ob.modifiers.new("Subdivision", 'SUBSURF')
        sub.levels = sub.render_levels = subsurf
    return inked(kit, ob, line)


def text_mesh(kit, name, body, size, extrude, font, mat, parent, loc, rot, bevel=0.0, resolution=3):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = bevel
    cu.align_x = 'CENTER'
    cu.align_y = 'CENTER'
    cu.resolution_u = resolution
    cu.font = bpy.data.fonts.load(font, check_existing=True)
    tmp = bpy.data.objects.new(name + " tmp", cu)
    kit.col.objects.link(tmp)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    me.materials.clear()
    me.materials.append(mat)
    return kit.link(name, me, parent, loc, rot)


def offset_poly(pts, w):
    """Grow a CCW 2D polygon outward by w (miter, clamped)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e1, e2 = (p1 - p0).normalized(), (p2 - p1).normalized()
        n1, n2 = Vector((e1.y, -e1.x)), Vector((e2.y, -e2.x))
        bis = (n1 + n2)
        bis = bis.normalized() if bis.length > 1e-6 else n1
        k = w / max(0.35, bis.dot(n1))
        out.append(tuple(p1 + bis * k))
    return out


def ccw(pts):
    area = sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts)))
    return pts if area > 0 else list(reversed(pts))


def flat_poly(kit, name, pts, mat, parent, line=0.012, loc=(0, 0, 0), rot=(0, 0, 0), plane='XZ'):
    """Flat 2D comic shape (CCW pts) with an ink border polygon tucked behind it.
    plane 'XZ' faces -Y (camera-facing pivots), 'XY' lies on the floor facing +Z."""
    pts = ccw(pts)
    piv = kit.empty(name, parent, loc, rot)

    def build(nm, poly, m, back):
        bm = bmesh.new()
        if plane == 'XZ':
            vs = [bm.verts.new((x, back, z)) for x, z in poly]
        else:
            vs = [bm.verts.new((x, z, -back)) for x, z in poly]
        bm.faces.new(vs)
        return kit.mesh_from_bmesh(nm, bm, m, piv, smooth=False)
    build(name + " fill", pts, mat, 0.0)
    if line:
        build(name + " ink", offset_poly(pts, line), kit.mat("ink", INK), 0.004 if plane == 'XZ' else 0.0015)
    return piv


def blob_pts(rand, r, n=18, jitter=0.15, spikes=0, spike_len=0.7):
    pts = []
    spike_at = set(rand.sample(range(n), spikes)) if spikes else set()
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (1 + rand.uniform(-jitter, jitter))
        if i in spike_at:
            rr = r * (1 + spike_len * rand.uniform(0.6, 1.2))
        pts.append((rr * math.cos(a), rr * math.sin(a)))
    return pts


def star_pts(points, r_out, r_in, rand, wobble=0.25):
    pts = []
    for i in range(points * 2):
        a = math.pi * i / points
        r = (r_out if i % 2 == 0 else r_in) * (1 + rand.uniform(-wobble, wobble))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


def flame_pts(scale, angle):
    """Flat cartoon flame with three licking tongues, pointing along +Z then rotated in-plane by angle (deg)."""
    raw = [(-0.5, 0.0), (-0.35, -0.28), (0.0, -0.38), (0.35, -0.28), (0.5, 0.0), (0.45, 0.45), (0.3, 0.3),
           (0.22, 0.95), (0.05, 0.5), (-0.08, 1.35), (-0.2, 0.55), (-0.32, 0.8), (-0.42, 0.3)]
    a = math.radians(angle)
    ca, sa = math.cos(a), math.sin(a)
    return [((x * ca - z * sa) * scale, (x * sa + z * ca) * scale) for x, z in raw]


def drop(kit, name, size, vel, mat, parent, loc, line=0.006, stretch=1.0):
    """Comic teardrop, tail trailing behind its velocity."""
    secs = [(-0.9, 0.3, 0.3), (-0.65, 0.78, 0.78), (-0.2, 1.0, 1.0), (0.35, 0.72, 0.72), (0.9, 0.3, 0.3),
            (1.2 + 0.6 * stretch, 0.04, 0.04)]
    secs = [(z * size, rx * size, ry * size) for z, rx, ry in secs]
    q = Vector((0, 0, 1)).rotation_difference(-Vector(vel).normalized())
    return loft(kit, name, secs, [mat], parent, n=10, subsurf=1, rot=q, offset=loc, line=line)


# ------------------------------------------------------------------ gun
def waffle_cone(kit, name, r0, r1, length, parent, rot, loc, line):
    """Waffle-cone flare: tan cone with a diamond lattice wireframe wrapped around it."""
    cone = loft(kit, name, [(0, r0, r0), (length * 0.85, r1 * 0.92, r1 * 0.92), (length, r1, r1)],
                [kit.mat("waffle", WAFFLE)], parent, n=20, subsurf=0, rot=rot, offset=loc, line=line)
    rings, seg = 6, 10
    bm = bmesh.new()
    vs = []
    for i in range(rings + 1):
        t = i / rings
        r = r0 + (r1 - r0) * t + 0.0012
        off = 0.5 * (i % 2)
        vs.append([bm.verts.new((r * math.cos(2 * math.pi * (j + off) / seg), r * math.sin(2 * math.pi * (j + off) / seg),
                                 length * t)) for j in range(seg)])
    for i in range(rings - 1):
        for j in range(seg):
            par = i % 2
            bm.faces.new((vs[i][j], vs[i + 1][(j + par) % seg], vs[i + 2][j], vs[i + 1][(j - 1 + par) % seg]))
    bmesh.ops.transform(bm, matrix=rot_matrix(rot).to_4x4(), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(loc), verts=bm.verts)
    lat = kit.mesh_from_bmesh(name + " lattice", bm, kit.mat("waffle line", "#8a5524"), parent, smooth=False)
    wf = lat.modifiers.new("Wire", 'WIREFRAME')
    wf.thickness = max(0.0018, (r1 - r0) * 0.06)
    wf.use_even_offset = True
    return cone


def build_gun(kit, root):
    w = GUN_LINE[0]
    teal = kit.mat("gun teal", TEAL)
    cherry = kit.mat("cherry", CHERRY)
    mustard = kit.mat("mustard", MUSTARD)
    cream = kit.mat("cream", CREAM)
    ink = kit.mat("ink", INK)
    along = (90, 0, 0)  # loft +Z -> barrel -Y, loft ry -> +Z
    # rocket fuselage: fat bulb at the back, tapering into the barrel
    body = [(-0.115, 0.012, 0.012), (-0.1, 0.028, 0.028), (-0.065, 0.044, 0.046), (-0.02, 0.047, 0.049),
            (0.03, 0.04, 0.042), (0.075, 0.029, 0.03), (0.105, 0.021, 0.021)]
    loft(kit, "gun fuselage", body, [teal], root, n=10, subsurf=1, rot=along, line=w)
    # chrome-ish stripe along the side (cream racing stripe)
    loft(kit, "gun stripe", [(-0.07, 0.0465, 0.012, 0, 0.0), (-0.01, 0.0495, 0.012), (0.05, 0.037, 0.01)],
         [cream], root, n=12, subsurf=1, rot=along)
    # banded barrel
    loft(kit, "gun barrel", [(0.09, 0.016, 0.016), (0.18, 0.015, 0.015)], [kit.mat("gun dark", "#22625f")], root,
         n=14, subsurf=0, rot=along, line=w)
    for i, y in enumerate((-0.115, -0.138, -0.161)):
        loft(kit, f"gun band {i}", [(0, 0.024, 0.024, 0, 0, 2.6), (0.011, 0.024, 0.024, 0, 0, 2.6)], [mustard], root,
             n=10, subsurf=0, rot=along, offset=(0, y + 0.0055, 0), line=w)
    # gyro rings around the fuselage
    torus(kit, "gun gyro ring", 0.05, 0.0055, mustard, root, (0, -0.075, 0), (90, 0, 0), line=w)
    torus(kit, "gun collar", 0.049, 0.006, cherry, root, (0, 0.035, 0), (90, 0, 0), seg=14, rs=5, line=w)
    # waffle-cone muzzle with a vanilla lip and a dark bore
    waffle_cone(kit, "gun waffle muzzle", 0.019, 0.05, 0.072, root, along, (0, -0.172, 0), w)
    torus(kit, "gun vanilla lip", 0.046, 0.009, kit.mat("vanilla", VANILLA), root, (0, -0.244, 0), (90, 0, 0),
          seg=20, line=w)
    kit.prim("gun bore", 'cyl', (0.037, 0.037, 0.004), ink, root, offset=(0, -0.238, 0), rot=(90, 0, 0), segments=20)
    # fins: tall swept tail fin plus two lower side fins
    fin = [(0.03, 0.03), (0.125, 0.022), (0.175, 0.11), (0.148, 0.118), (0.075, 0.055), (0.035, 0.045)]
    for i, spin in enumerate((0, 112, -112)):
        bm = bmesh.new()
        bm.faces.new([bm.verts.new((0, y, z)) for y, z in fin])
        bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(spin), 4, 'Y'), verts=bm.verts)
        ob = kit.mesh_from_bmesh(f"gun fin {i}", bm, cherry, root, smooth=False)
        sol = ob.modifiers.new("Thick", 'SOLIDIFY')
        sol.thickness = 0.007
        sol.offset = 0
        inked(kit, ob, w)
    # bakelite grip with a mustard pommel
    gv = [(-0.014, 0.0, -0.02), (0.014, 0.0, -0.02), (0.014, 0.05, -0.02), (-0.014, 0.05, -0.02),
          (-0.016, 0.027, -0.118), (0.016, 0.027, -0.118), (0.016, 0.079, -0.112), (-0.016, 0.079, -0.112)]
    gf = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    inked(kit, kit.cage("gun grip", gv, gf, cherry, root, subsurf=2), w)
    for i in range(3):
        kit.prim(f"gun grip groove {i}", 'box', (0.034, 0.006, 0.003), ink, root,
                 offset=(0, 0.037 + i * 0.006, -0.05 - i * 0.02), rot=(-28, 0, 0))
    kit.prim("gun pommel", 'sphere', (0.02, 0.03, 0.012), mustard, root, offset=(0, 0.054, -0.118), rot=(-12, 0, 0))
    # trigger and guard
    kit.skin("gun trigger guard", [(0, -0.035, -0.035), (0, -0.04, -0.07), (0, -0.01, -0.088), (0, 0.022, -0.082)],
             [(0, 1), (1, 2), (2, 3)], [0.0045] * 4, mustard, root, subsurf=0)
    kit.prim("gun trigger", 'cone', (0.005, 0.008, 0.03), ink, root, offset=(0, -0.012, -0.055), rot=(-20, 0, 0), taper=0.5)
    # pint-tub magazine with a chocolate scoop and sprinkles
    loft(kit, "gun pint mount", [(0.03, 0.012, 0.03, 0, 0, 4), (0.052, 0.012, 0.03, 0, 0, 4)], [kit.mat("navy", NAVY)],
         root, n=8, subsurf=0, offset=(0, -0.005, 0), line=w)
    pint = loft(kit, "gun pint tub", [(0.048, 0.03, 0.03), (0.11, 0.036, 0.036)], [cream, teal, cherry], root, n=20,
                subsurf=0, offset=(0, -0.005, 0), line=w,
                mat_fn=lambda c: 1 if 0.07 < c.z < 0.084 else 0)
    kit.prim("gun pint label stripe", 'cyl', (0.0345, 0.0345, 0.005), cherry, root, offset=(0, -0.005, 0.062), segments=20)
    torus(kit, "gun pint rim", 0.036, 0.0035, cream, root, (0, -0.005, 0.11), seg=20, line=w)
    choc = kit.mat("chocolate", CHOC)
    scoop = loft(kit, "gun choc scoop", [(0.104, 0.036, 0.036, 0, 0, 2, 0.006), (0.115, 0.04, 0.04), (0.13, 0.036, 0.036),
                                         (0.148, 0.022, 0.022), (0.156, 0.004, 0.004)], [choc], root, n=10, subsurf=1,
                 offset=(0, -0.005, 0), line=w)
    for i, (a, l) in enumerate(((40, 0.02), (160, 0.03), (250, 0.016))):
        x, y = 0.037 * math.cos(math.radians(a)), -0.005 + 0.037 * math.sin(math.radians(a))
        kit.skin(f"gun choc drip {i}", [(x, y, 0.108), (x * 1.02, y * 1.02 + 0.0002, 0.108 - l)], [(0, 1)],
                 [0.006, 0.0065], choc, root, subsurf=1)
    cols = [CHERRY, TEAL, MUSTARD, VANILLA, NAVY]
    for i in range(16):
        u = kit.rand.uniform(0, 2 * math.pi)
        v = kit.rand.uniform(0.2, 1.1)
        p = Vector((0.033 * math.cos(u) * math.cos(v), -0.005 + 0.033 * math.sin(u) * math.cos(v),
                    0.12 + 0.03 * math.sin(v)))
        kit.prim(f"gun sprinkle {i}", 'cyl', (0.003, 0.003, 0.012), kit.mat("sprinkle " + cols[i % 5], cols[i % 5]),
                 root, offset=tuple(p), rot=(kit.rand.uniform(0, 180), kit.rand.uniform(0, 180), 0), segments=6)
    # rear antenna ball
    kit.skin("gun antenna", [(0, 0.075, 0.035), (0, 0.105, 0.075)], [(0, 1)], [0.003, 0.003], ink, root, subsurf=0)
    kit.prim("gun antenna ball", 'sphere', (0.009, 0.009, 0.009), cherry, root, offset=(0, 0.107, 0.079))


# ------------------------------------------------------------------ player
def build_player(kit, root):
    W = 0.009
    ink = kit.mat("ink", INK)
    skin = kit.mat("skin", SKIN)
    shirt = kit.mat("shirt", SHIRT)
    navy = kit.mat("navy", NAVY)
    teal = kit.mat("teal", TEAL)
    cherry = kit.mat("cherry", CHERRY)
    cream = kit.mat("cream", CREAM)
    hair = kit.mat("hair", HAIR)
    mustard = kit.mat("mustard", MUSTARD)

    # legs: pleated high-waist slacks, cuffs, saddle shoes; heroic wide stance
    for s, nm in ((-1, "R"), (1, "L")):
        inked(kit, kit.skin(f"player leg {nm}", [(s * 0.085, 0, 0.93), (s * 0.11, -0.025, 0.5), (s * 0.13, 0.0, 0.12)],
                            [(0, 1), (1, 2)], [0.09, 0.066, 0.058], navy, root), W)
        loft(kit, f"player cuff {nm}", [(0.09, 0.064, 0.064, s * 0.13, 0.0), (0.135, 0.064, 0.064, s * 0.13, 0.0)],
             [kit.mat("navy dark", "#22304a")], root, n=14, subsurf=1, line=W * 0.7)
        inked(kit, kit.prim(f"player shoe {nm}", 'box', (0.1, 0.25, 0.085), cream, root, offset=(s * 0.135, -0.05, 0.045),
                            bevel=0.03), W * 0.8)
        kit.prim(f"player shoe saddle {nm}", 'box', (0.104, 0.09, 0.075), ink, root, offset=(s * 0.135, -0.03, 0.05),
                 bevel=0.02)
        kit.prim(f"player sole {nm}", 'box', (0.106, 0.256, 0.018), ink, root, offset=(s * 0.135, -0.05, 0.008), bevel=0.006)

    # torso: V-shaped heroic chest, navy trousers up to a high waist
    torso = [(0.86, 0.15, 0.1), (0.95, 0.145, 0.098), (1.05, 0.15, 0.1, 0, 0, 2.4), (1.18, 0.178, 0.112, 0, -0.005, 2.6),
             (1.30, 0.205, 0.118, 0, -0.008, 3), (1.375, 0.218, 0.108, 0, 0, 3.6), (1.43, 0.16, 0.085, 0, 0, 3),
             (1.46, 0.06, 0.055)]
    loft(kit, "player torso", torso, [shirt, navy], root, n=12, line=W, mat_fn=lambda c: 1 if c.z < 0.99 else 0)
    kit.prim("player belt", 'cyl', (0.152, 0.104, 0.022), ink, root, offset=(0, 0, 0.985), segments=20)
    kit.prim("player buckle", 'box', (0.04, 0.012, 0.028), mustard, root, offset=(0, -0.106, 0.985), bevel=0.004)

    # apron: bib and skirt in teal with cherry pocket, straps over the shoulders
    sheet(kit, "player apron", [(1.31, 0.095, -0.136, 0.008), (1.16, 0.105, -0.128, 0.01), (1.0, 0.125, -0.12, 0.014),
                                (0.965, 0.17, -0.118, 0.05), (0.75, 0.19, -0.13, 0.065), (0.53, 0.205, -0.15, 0.07)],
          7, teal, root, 0.008, W)
    sheet(kit, "player apron pocket", [(0.9, 0.09, -0.134, 0.006), (0.8, 0.095, -0.136, 0.008)], 5, cherry, root,
          0.006, W * 0.6, subsurf=0)
    for s in (-1, 1):
        inked(kit, kit.skin(f"player apron strap {s}", [(s * 0.085, -0.136, 1.3), (s * 0.1, -0.1, 1.42), (s * 0.08, 0.0, 1.46)],
                            [(0, 1), (1, 2)], [0.012] * 3, teal, root, subsurf=0), W * 0.5)

    # collar and bowtie
    for s in (-1, 1):
        cv = [(0.0, -0.07, 1.455), (s * 0.075, -0.05, 1.47), (s * 0.04, -0.1, 1.39)]
        ob = kit.cage(f"player collar {s}", cv, [(0, 1, 2)], shirt, root, subsurf=0)
        ob.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.008
        inked(kit, ob, W * 0.5)
        inked(kit, kit.prim(f"player bowtie wing {s}", 'cone', (0.03, 0.012, 0.045), cherry, root,
                            offset=(s * 0.026, -0.1, 1.415), rot=(0, -90 * s, 0), taper=0.3, segments=4), W * 0.5)
    kit.prim("player bowtie knot", 'sphere', (0.014, 0.012, 0.014), cherry, root, offset=(0, -0.108, 1.415))

    # neck and head: square jaw, pompadour, jaunty paper hat
    inked(kit, kit.skin("player neck", [(0, 0.0, 1.42), (0, -0.005, 1.55)], [(0, 1)], [0.055, 0.052], skin, root), W)
    head = kit.empty("player head pivot", root, (0, -0.01, 1.47), (-3, 0, 4))
    hsecs = [(0.0, 0.05, 0.035, 0, -0.045, 3), (0.025, 0.077, 0.07, 0, -0.025, 3.6), (0.06, 0.087, 0.085, 0, -0.01, 3.2),
             (0.11, 0.091, 0.095, 0, 0, 2.8), (0.16, 0.092, 0.098, 0, 0.005, 2.5), (0.205, 0.08, 0.088, 0, 0.005, 2.3),
             (0.235, 0.045, 0.05, 0, 0.005, 2)]
    loft(kit, "player head", hsecs, [skin, hair], head, n=12, line=W,
         mat_fn=lambda c: 1 if (c.z > 0.175 or (c.y > 0.035 and c.z > 0.07)) else 0)
    kit.prim("player pompadour", 'sphere', (0.08, 0.075, 0.05), hair, head, offset=(0, -0.045, 0.21), rot=(-25, 0, 0))
    inked(kit, kit.prim("player pompadour curl", 'sphere', (0.07, 0.05, 0.042), hair, head, offset=(0.008, -0.085, 0.228),
                        rot=(-40, 0, -6)), W * 0.7)
    for s in (-1, 1):
        inked(kit, kit.prim(f"player ear {s}", 'sphere', (0.016, 0.028, 0.034), skin, head, offset=(s * 0.09, 0.012, 0.11)),
              W * 0.5)
        kit.prim(f"player eye {s}", 'sphere', (0.011, 0.007, 0.015), ink, head, offset=(s * 0.034, -0.092, 0.122))
        kit.prim(f"player brow {s}", 'box', (0.036, 0.012, 0.011), ink, head, offset=(s * 0.036, -0.094, 0.15),
                 rot=(0, -12 * s, 0), bevel=0.003)
        kit.prim(f"player jaw line {s}", 'box', (0.003, 0.006, 0.03), kit.mat("skin shade", hex_scale(SKIN, 0.75)), head,
                 offset=(s * 0.074, -0.06, 0.03), rot=(0, 0, 0))
    kit.prim("player nose", 'cone', (0.016, 0.012, 0.042), skin, head, offset=(0, -0.103, 0.088), rot=(80, 0, 0), taper=0.35)
    kit.prim("player smirk", 'box', (0.042, 0.008, 0.007), ink, head, offset=(-0.006, -0.083, 0.045), rot=(0, -9, 0), bevel=0.002)
    kit.prim("player chin cleft", 'box', (0.003, 0.004, 0.018), ink, head, offset=(0, -0.08, 0.012))
    # paper soda-jerk hat (garrison fold), cream with cherry band, tipped back and to the side
    hat = kit.empty("player hat pivot", head, (0.004, 0.025, 0.2), (-8, 12, 0), (1.12, 1.1, 1.25))
    hv = [(0, -0.11, 0), (0.088, -0.05, 0), (0.088, 0.05, 0), (0, 0.11, 0), (-0.088, 0.05, 0), (-0.088, -0.05, 0),
          (0, -0.1, 0.085), (0, 0.0, 0.07), (0, 0.1, 0.085)]
    hf = [(0, 1, 2, 3, 8, 7, 6), (3, 4, 5, 0, 6, 7, 8)]
    ob = kit.cage("player hat", hv, hf, cream, hat, subsurf=0, smooth=False)
    ob.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.006
    inked(kit, ob, W * 0.7)
    band = [(0, -0.112, 0.0), (0.09, -0.051, 0.0), (0.09, 0.051, 0.0), (0, 0.112, 0.0), (-0.09, 0.051, 0.0), (-0.09, -0.051, 0.0)]
    bv = band + [(x * 0.93, y * 0.95, 0.024) for x, y, _ in band]
    bf = [(i, (i + 1) % 6, 6 + (i + 1) % 6, 6 + i) for i in range(6)]
    kit.cage("player hat band", bv, bf, cherry, hat, subsurf=0, smooth=False).modifiers.new("Thick", 'SOLIDIFY').thickness = 0.007

    # right arm (-X): short sleeve, raised and aiming the Scoop Pistol
    inked(kit, kit.skin("player sleeve R", [(-0.19, 0.0, 1.37), (-0.215, -0.1, 1.335)], [(0, 1)], [0.072, 0.064], shirt, root), W)
    inked(kit, kit.skin("player arm R", [(-0.2, -0.03, 1.36), (-0.22, -0.25, 1.31), (-0.2, -0.45, 1.335)], [(0, 1), (1, 2)],
                        [0.05, 0.048, 0.04], skin, root), W)
    inked(kit, kit.prim("player fist R", 'sphere', (0.045, 0.05, 0.046), skin, root, offset=(-0.2, -0.5, 1.33)), W * 0.7)
    GUN_LINE[0] = 0.004
    build_gun(kit, kit.empty("player held gun", root, (-0.2, -0.55, 1.4)))
    GUN_LINE[0] = 0.0028
    # left arm (+X): fist planted on the hip
    inked(kit, kit.skin("player sleeve L", [(0.19, 0.0, 1.37), (0.245, 0.03, 1.29)], [(0, 1)], [0.072, 0.064], shirt, root), W)
    inked(kit, kit.skin("player arm L", [(0.2, 0.0, 1.36), (0.31, 0.05, 1.14), (0.19, 0.0, 1.0)], [(0, 1), (1, 2)],
                        [0.05, 0.046, 0.04], skin, root), W)
    inked(kit, kit.prim("player fist L", 'sphere', (0.045, 0.05, 0.046), skin, root, offset=(0.175, -0.01, 0.98)), W * 0.7)

    # cooler backpack: cherry cooler, cream lid and stripe, three spare pints on top
    inked(kit, kit.prim("player cooler", 'box', (0.3, 0.17, 0.32), cherry, root, offset=(0, 0.215, 1.18), bevel=0.035), W)
    kit.prim("player cooler stripe", 'box', (0.306, 0.176, 0.04), cream, root, offset=(0, 0.215, 1.12), bevel=0.012)
    inked(kit, kit.prim("player cooler lid", 'box', (0.315, 0.185, 0.05), cream, root, offset=(0, 0.215, 1.355), bevel=0.016), W)
    for i, (x, c) in enumerate(((-0.095, TEAL), (0.0, CHERRY), (0.095, MUSTARD))):
        loft(kit, f"player pint {i}", [(1.38, 0.036, 0.036, x, 0.215), (1.465, 0.042, 0.042, x, 0.215)],
             [cream, kit.mat(f"pint {c}", c)], root, n=16, subsurf=0, line=W * 0.6,
             mat_fn=lambda cc: 1 if (1.405 < cc.z < 1.44) else 0)
        inked(kit, kit.prim(f"player pint lid {i}", 'cyl', (0.044, 0.044, 0.012), kit.mat(f"pint {c}", c), root,
                            offset=(x, 0.215, 1.47), segments=16), W * 0.5)
    for s in (-1, 1):
        inked(kit, kit.skin(f"player cooler strap {s}", [(s * 0.11, 0.13, 1.33), (s * 0.13, 0.02, 1.45),
                                                         (s * 0.16, -0.09, 1.36), (s * 0.155, -0.11, 1.22)],
                            [(0, 1), (1, 2), (2, 3)], [0.015] * 4, navy, root, subsurf=0), W * 0.5)


# ------------------------------------------------------------------ zombie
def build_zombie(kit, root, hit=False):
    W = 0.009
    ink = kit.mat("ink", INK)
    zs = kit.mat("zombie skin", ZSKIN)
    zdark = kit.mat("zombie shade", hex_scale(ZSKIN, 0.72))
    navy = kit.mat("navy", NAVY)
    mustard = kit.mat("mustard", MUSTARD)
    cherry = kit.mat("cherry", CHERRY)
    cream = kit.mat("cream", CREAM)
    trouser = kit.mat("trouser", TROUSER)
    shoe = kit.mat("shoe", SHOE)
    vanilla = kit.mat("vanilla", VANILLA)
    choc = kit.mat("chocolate", CHOC)

    if hit:
        hips_loc, torso_rot, head_rot = (0, 0.06, 0.9), (-16, -8, 16), (-22, -16, -22)
        leg_rot = {1: (14, -7, 0), -1: (-40, 16, 0)}
    else:
        hips_loc, torso_rot, head_rot = (0, 0.02, 0.89), (24, -12, -8), (-26, 22, 14)
        leg_rot = {1: (12, -4, -3), -1: (-12, 5, 4)}

    hips = kit.empty("zombie hips pivot", root, hips_loc)
    loft(kit, "zombie hips", [(-0.1, 0.15, 0.1), (0.0, 0.155, 0.105), (0.08, 0.145, 0.1)], [trouser], hips, n=14, line=W)
    kit.prim("zombie belt", 'cyl', (0.157, 0.107, 0.02), ink, hips, offset=(0, 0, 0.0), segments=20)

    # legs (each its own pivot): one trouser leg torn open at the shin
    for s, nm in ((1, "L"), (-1, "R")):
        leg = kit.empty(f"zombie leg {nm} pivot", hips, (s * 0.09, 0, -0.03), leg_rot[s])
        if s == 1:
            inked(kit, kit.skin("zombie leg L", [(0, 0, 0), (0, -0.04, -0.42), (0, 0.01, -0.8)], [(0, 1), (1, 2)],
                                [0.08, 0.063, 0.052], trouser, leg), W)
            loft(kit, "zombie hem L", [(-0.8, 0.058, 0.058, 0, 0.01), (-0.74, 0.056, 0.056, 0, 0.005, 2, 0.015)],
                 [trouser], leg, n=12, subsurf=1, line=W * 0.7)
        else:
            inked(kit, kit.skin("zombie leg R", [(0, 0, 0), (0, -0.04, -0.42), (0, -0.02, -0.56)], [(0, 1), (1, 2)],
                                [0.08, 0.063, 0.06], trouser, leg), W)
            loft(kit, "zombie hem R", [(-0.6, 0.07, 0.07, 0, -0.022, 2, 0.025), (-0.52, 0.064, 0.064, 0, -0.025)],
                 [trouser], leg, n=12, subsurf=1, line=W * 0.7)
            inked(kit, kit.skin("zombie shin R", [(0, -0.03, -0.5), (0, 0.0, -0.8)], [(0, 1)], [0.04, 0.034], zs, leg), W)
            kit.prim("zombie shin bruise", 'sphere', (0.02, 0.01, 0.03), zdark, leg, offset=(0.0, -0.045, -0.66))
        inked(kit, kit.prim(f"zombie shoe {nm}", 'box', (0.1, 0.24, 0.08), shoe, leg, offset=(0, -0.055, -0.825),
                            bevel=0.03), W * 0.8)
        kit.prim(f"zombie sole {nm}", 'box', (0.104, 0.244, 0.016), ink, leg, offset=(0, -0.055, -0.86), bevel=0.005)

    # torso: navy letterman jacket, padded square shoulders, ragged cherry waistband
    torso = kit.empty("zombie torso pivot", hips, (0, 0, 0.03), torso_rot)
    tsecs = [(-0.07, 0.158, 0.112, 0, 0, 2.4, 0.022), (-0.015, 0.152, 0.108), (0.05, 0.15, 0.105), (0.2, 0.172, 0.11, 0, -0.005, 2.6),
             (0.33, 0.212, 0.115, 0, 0, 3.6), (0.42, 0.235, 0.105, 0, 0, 4.6), (0.47, 0.2, 0.09, 0, 0, 4), (0.5, 0.075, 0.062, 0, 0.005)]
    loft(kit, "zombie jacket", tsecs, [navy, cherry], torso, n=12, line=W, mat_fn=lambda c: 1 if c.z < -0.015 else 0)
    torus(kit, "zombie collar", 0.072, 0.02, cherry, torso, (0, 0.0, 0.475), (8, 0, 0), seg=18, line=W * 0.6)
    # letterman chenille letter on a cream patch
    kit.prim("zombie letter patch", 'cyl', (0.062, 0.062, 0.008), cream, torso, offset=(0.085, -0.117, 0.28), rot=(92, 0, 0),
             segments=20)
    text_mesh(kit, "zombie letter Z", "Z", 0.11, 0.006, FONT_SERIF, cherry, torso, (0.085, -0.125, 0.28), (92, 0, 0))
    # snaps
    for i in range(4):
        kit.prim(f"zombie snap {i}", 'sphere', (0.009, 0.006, 0.009), cream, torso, offset=(-0.012, -0.113, 0.03 + i * 0.1))
    # torn holes showing green skin, and a dangling flap
    for i, (x, z) in enumerate(((-0.1, 0.12), (0.12, 0.06))):
        kit.prim(f"zombie tear {i}", 'sphere', (0.035, 0.008, 0.028), zs, torso, offset=(x, -0.106, z), rot=(0, 25 * i - 10, 0))
        kit.prim(f"zombie tear rim {i}", 'sphere', (0.04, 0.007, 0.033), ink, torso, offset=(x, -0.103, z), rot=(0, 25 * i - 10, 0))
    # vanilla splat with chocolate swirl and a cherry on the right shoulder
    sp = kit.empty("zombie splat pivot", torso, (-0.12, -0.03, 0.47), (-8, 6, 0))
    flat_poly(kit, "zombie splat", blob_pts(kit.rand, 0.052, 16, 0.15, spikes=3, spike_len=0.35), vanilla, sp, line=0.006,
              plane='XY')
    loft(kit, "zombie splat scoop", [(0.0, 0.05, 0.048, 0, 0, 2, 0.008), (0.022, 0.052, 0.05), (0.045, 0.035, 0.034),
                                     (0.06, 0.004, 0.004)], [vanilla], sp, n=10, line=W * 0.6)
    loft(kit, "zombie splat choc", [(0.03, 0.032, 0.03, 0.01, -0.01, 2, 0.006), (0.05, 0.026, 0.024, 0.01, -0.01),
                                    (0.062, 0.004, 0.004, 0.01, -0.01)], [choc], sp, n=12, line=W * 0.5)
    inked(kit, kit.prim("zombie splat cherry", 'sphere', (0.02, 0.02, 0.02), cherry, sp, offset=(0.005, -0.01, 0.075)), W * 0.5)
    kit.skin("zombie cherry stem", [(0.005, -0.01, 0.09), (0.015, 0.0, 0.125)], [(0, 1)], [0.003, 0.002], ink, sp, subsurf=0)
    for i, (x, l) in enumerate(((-0.155, 0.12), (-0.105, 0.17), (-0.07, 0.09))):
        inked(kit, kit.skin(f"zombie drip {i}", [(x, -0.095, 0.455), (x, -0.118, 0.4), (x, -0.12, 0.42 - l)],
                            [(0, 1), (1, 2)], [0.013, 0.012, 0.017], vanilla, torso), W * 0.5)

    # neck and head: sunken cheeks, pointy chin/nose/ears, exposed brain, mismatched eyes
    inked(kit, kit.skin("zombie neck", [(0, 0.0, 0.44), (0, -0.03, 0.56)], [(0, 1)], [0.045, 0.04], zs, torso), W)
    head = kit.empty("zombie head pivot", torso, (0, -0.035, 0.52), head_rot)
    hsecs = [(0.0, 0.018, 0.02, 0, -0.072), (0.03, 0.048, 0.048, 0, -0.045, 2.2), (0.07, 0.054, 0.07, 0, -0.016),
             (0.105, 0.058, 0.08, 0, 0, 2), (0.145, 0.086, 0.088, 0, 0, 2.7), (0.19, 0.088, 0.09, 0, 0.005, 2.8),
             (0.235, 0.078, 0.083, 0, 0.01, 2.6), (0.258, 0.04, 0.045, 0, 0.01)]
    loft(kit, "zombie head", hsecs, [zs, kit.mat("zombie hair", "#2f3a2c")], head, n=12, line=W,
         mat_fn=lambda c: 1 if (c.y > 0.03 and c.z > 0.1) or (c.z > 0.2 and c.x > 0.01) else 0)
    # exposed brain bulging out of a cracked skull
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1)
    bmesh.ops.scale(bm, vec=Vector((0.058, 0.075, 0.042)), verts=bm.verts)
    brain = kit.mesh_from_bmesh("zombie brain", bm, kit.mat("brain", BRAIN), head, loc=(-0.03, 0.0, 0.245), rot=(0, 0, 0))
    tex = bpy.data.textures.new("ZD2 brain folds", 'MARBLE')
    tex.marble_type = 'SHARPER'
    tex.noise_scale = 0.06
    tex.turbulence = 9
    disp = brain.modifiers.new("Folds", 'DISPLACE')
    disp.texture = tex
    disp.strength = 0.012
    disp.texture_coords = 'GLOBAL'
    inked(kit, brain, W * 0.6)
    kit.prim("zombie brain groove", 'box', (0.003, 0.13, 0.01), kit.mat("brain dark", hex_scale(BRAIN, 0.6)), head,
             offset=(-0.03, 0.0, 0.285))
    for i in range(6):
        a = math.radians(-30 + i * 45)
        p = (-0.03 + 0.06 * math.cos(a), 0.075 * math.sin(a), 0.235)
        kit.prim(f"zombie skull shard {i}", 'cone', (0.012, 0.008, 0.03), cream, head, offset=p,
                 rot=(kit.rand.uniform(-20, 20), kit.rand.uniform(-20, 20), math.degrees(a)), taper=0.0, segments=4)
    # mismatched eyes: a big bulging one and a sunken glowing socket
    inked(kit, kit.prim("zombie eye big", 'sphere', (0.03, 0.025, 0.03), cream, head, offset=(0.036, -0.075, 0.16)), W * 0.5)
    kit.prim("zombie pupil", 'sphere', (0.008, 0.006, 0.008), ink, head, offset=(0.047, -0.1, 0.166))
    kit.prim("zombie eye vein", 'box', (0.02, 0.004, 0.002), cherry, head, offset=(0.028, -0.098, 0.15), rot=(0, 30, 0))
    kit.prim("zombie socket", 'sphere', (0.022, 0.01, 0.017), ink, head, offset=(-0.035, -0.082, 0.158))
    kit.prim("zombie socket glow", 'sphere', (0.006, 0.005, 0.006), cherry, head, offset=(-0.035, -0.092, 0.158))
    for s in (-1, 1):
        kit.prim(f"zombie brow {s}", 'box', (0.04, 0.012, 0.012), ink, head, offset=(s * 0.036, -0.088, 0.19),
                 rot=(0, 16 * s, 0), bevel=0.003)
        kit.prim(f"zombie cheek hollow {s}", 'sphere', (0.014, 0.01, 0.03), zdark, head, offset=(s * 0.048, -0.05, 0.098),
                 rot=(0, -12 * s, 0))
        inked(kit, kit.prim(f"zombie ear {s}", 'cone', (0.018, 0.008, 0.06), zs, head, offset=(s * 0.1, 0.01, 0.16),
                            rot=(0, 60 * s, 0), taper=0.0, segments=8), W * 0.5)
    inked(kit, kit.prim("zombie nose", 'cone', (0.014, 0.011, 0.058), zs, head, offset=(0, -0.105, 0.12), rot=(70, 0, 0),
                        taper=0.0, segments=8), W * 0.5)
    kit.prim("zombie mouth", 'sphere', (0.034, 0.012, 0.02), ink, head, offset=(0.004, -0.068, 0.058), rot=(0, 8, 0))
    for i, x in enumerate((-0.02, -0.006, 0.012, 0.025)):
        kit.prim(f"zombie tooth {i}", 'box', (0.009, 0.006, 0.012 + 0.004 * (i % 2)), cream, head,
                 offset=(x, -0.079, 0.068 - 0.002 * (i % 2)))

    # arms (each its own pivot), outstretched; left arm flies off when hit
    shoulder = {s: Vector((s * 0.2, 0.0, 0.41)) for s in (1, -1)}
    if hit:
        arm_rot = {-1: (-128, -30, 10)}
    else:
        arm_rot = {1: (-torso_rot[0] + 38, 14, 34), -1: (-torso_rot[0] - 38, -8, -14)}
    for s, nm in ((1, "L"), (-1, "R")):
        if hit and s == 1:
            continue
        build_zombie_arm(kit, kit.empty(f"zombie arm {nm} pivot", torso, tuple(shoulder[s]), arm_rot[s]), s, nm, W)

    if hit:
        M = pose_matrix(hips_loc, (0, 0, 0)) @ pose_matrix((0, 0, 0.03), torso_rot)
        sh = M @ shoulder[1]
        Rinv = root.rotation_euler.to_matrix().inverted()
        wv = lambda v: Rinv @ Vector(v)
        arm = kit.empty("zombie arm L pivot", root, tuple(sh + wv((0.42, -0.16, 0.3))), (-25, 35, 55))
        build_zombie_arm(kit, arm, 1, "L", W)
        # stumps
        inked(kit, kit.prim("zombie arm stump", 'sphere', (0.06, 0.06, 0.03), cherry, arm, rot=(90, 0, 0)), W * 0.6)
        kit.prim("zombie arm bone", 'cyl', (0.016, 0.016, 0.05), cream, arm, offset=(0, 0.02, 0), rot=(90, 0, 0))
        inked(kit, kit.prim("zombie shoulder stump", 'sphere', (0.035, 0.07, 0.07), cherry, torso,
                            offset=(0.215, 0.0, 0.40)), W * 0.6)
        build_hit_fx(kit, root, sh, wv, W)


def build_zombie_arm(kit, piv, s, nm, W):
    zs = kit.mat("zombie skin", ZSKIN)
    inked(kit, kit.skin(f"zombie sleeve {nm}", [(0, 0, 0), (s * 0.03, -0.25, -0.06), (s * 0.01, -0.46, -0.06)],
                        [(0, 1), (1, 2)], [0.066, 0.056, 0.05], kit.mat("mustard", MUSTARD), piv), W)
    for i in range(2):
        kit.prim(f"zombie sleeve stripe {nm} {i}", 'cyl', (0.054 - i * 0.002, 0.054 - i * 0.002, 0.012),
                 kit.mat("cherry", CHERRY), piv, offset=(s * 0.012, -0.36 - i * 0.03, -0.06), rot=(90, 0, 0), segments=16)
    loft(kit, f"zombie cuff {nm}", [(0, 0.052, 0.052), (0.05, 0.06, 0.058, 0, 0, 2, 0.014)], [kit.mat("cream", CREAM)], piv,
         n=12, subsurf=1, rot=(90, 0, 0), offset=(s * 0.01, -0.44, -0.062), line=W * 0.6)
    inked(kit, kit.skin(f"zombie wrist {nm}", [(s * 0.01, -0.45, -0.062), (s * 0.01, -0.52, -0.068)], [(0, 1)],
                        [0.032, 0.03], zs, piv), W * 0.7)
    inked(kit, kit.prim(f"zombie palm {nm}", 'sphere', (0.044, 0.05, 0.02), zs, piv, offset=(s * 0.01, -0.54, -0.07)), W * 0.6)
    for i, (x, l) in enumerate(((-0.027, 0.85), (-0.009, 1.0), (0.009, 1.05), (0.027, 0.8))):
        x += s * 0.01
        inked(kit, kit.skin(f"zombie finger {nm} {i}", [(x, -0.575, -0.07), (x, -0.575 - 0.045 * l, -0.082),
                                                      (x * 1.05, -0.575 - 0.07 * l, -0.115)], [(0, 1), (1, 2)],
                            [0.011, 0.0095, 0.0065], zs, piv, subsurf=0), W * 0.45)
    inked(kit, kit.skin(f"zombie thumb {nm}", [(-s * 0.03, -0.53, -0.068), (-s * 0.055, -0.565, -0.085)], [(0, 1)],
                        [0.011, 0.008], zs, piv, subsurf=0), W * 0.45)


# ------------------------------------------------------------------ hit FX
def build_hit_fx(kit, root, sh, wv, W):
    rand = kit.rand
    cam_local = root.matrix_basis.inverted() @ Vector((1.7, -0.5, 1.3))
    cherry = kit.mat("cherry", CHERRY)
    vanilla = kit.mat("vanilla", VANILLA)
    choc = kit.mat("chocolate", CHOC)
    orange = kit.mat("flame", ORANGE)
    mustard = kit.mat("mustard", MUSTARD)
    smoke = kit.mat("smoke", SMOKE)
    smoke_dark = kit.mat("smoke shade", hex_scale(SMOKE, 0.82))

    def facing(name, pos, spin=0.0):
        d = (cam_local - Vector(pos)).normalized()
        q = (-d).to_track_quat('Y', 'Z')
        q = q @ Quaternion((0, 1, 0), math.radians(spin))
        piv = kit.empty(name, root, tuple(pos))
        piv.rotation_euler = q.to_euler()
        return piv

    def at(v):
        return sh + wv(v)

    # explosion: orange starburst with a mustard core and licking flames, behind the stump
    burst = facing("fx burst", at((0.12, 0.15, 0.02)), 8)
    flat_poly(kit, "fx burst outer", star_pts(11, 0.3, 0.17, rand), orange, burst, line=0.014)
    flat_poly(kit, "fx burst inner", star_pts(9, 0.18, 0.11, rand), mustard, burst, line=0.01, loc=(0.02, -0.03, 0.0))
    flat_poly(kit, "fx burst core", blob_pts(rand, 0.07, 12, 0.1), vanilla, burst, line=0.008, loc=(0.02, -0.05, 0.0))
    for i, (ang, sc, dist) in enumerate(((-70, 0.2, 0.3), (-20, 0.24, 0.34), (35, 0.18, 0.3), (120, 0.16, 0.28))):
        a = math.radians(ang + 90)
        flat_poly(kit, f"fx flame {i}", flame_pts(sc, ang), orange, burst, line=0.01,
                  loc=(dist * math.cos(a) * -1, -0.015, dist * math.sin(a) * 0.8))
        flat_poly(kit, f"fx flame core {i}", flame_pts(sc * 0.55, ang), mustard, burst, line=0.0,
                  loc=(dist * math.cos(a) * -1, -0.025, dist * math.sin(a) * 0.8 - 0.01))

    # billowing flat smoke clouds: overlapping inked disks, front ones overlapping back ones
    def cloud(name, pos, r, count, spin=0):
        piv = facing(name, pos, spin)
        for i in range(count):
            a = 2 * math.pi * i / count + rand.uniform(-0.3, 0.3)
            rr = r * rand.uniform(0.45, 0.7)
            off = (math.cos(a) * r * 0.62, -0.012 * (i % 3), math.sin(a) * r * 0.45 + r * 0.1)
            flat_poly(kit, f"{name} puff {i}", blob_pts(rand, rr, 16, 0.06), smoke, piv, line=0.011, loc=off)
            flat_poly(kit, f"{name} puff shade {i}", [(x * 0.75 + rr * 0.12, z * 0.55 - rr * 0.38) for x, z in
                                                      blob_pts(rand, rr, 12, 0.04)], smoke_dark, piv, line=0.0,
                      loc=(off[0], off[1] - 0.003, off[2]))
        flat_poly(kit, f"{name} puff core", blob_pts(rand, r * 0.6, 16, 0.06), smoke, piv, line=0.011,
                  loc=(0, -0.05, 0))
        return piv
    cloud("fx smoke high", at((0.62, 0.25, 0.62)), 0.14, 5, 0)
    cloud("fx smoke low", at((0.38, 0.1, -0.34)), 0.16, 5, 0)
    arm_pos = at((0.42, -0.16, 0.3))
    for i, t in enumerate((0.3, 0.55, 0.8)):
        p = sh.lerp(arm_pos, t) + wv((0, 0.2, 0.1 + 0.05 * math.sin(t * 3)))
        cloud(f"fx trail {i}", p, 0.05 + 0.03 * t, 4)

    # blood: cherry teardrops spraying from the stump, a stream after the arm
    for i in range(16):
        d = wv((rand.uniform(0.2, 1.0), rand.uniform(-0.8, 0.3), rand.uniform(-0.2, 1.0))).normalized()
        dist = rand.uniform(0.12, 0.6)
        drop(kit, f"fx blood {i}", rand.uniform(0.012, 0.03), d, cherry, root, tuple(sh + d * dist), line=0.006)
    stream = [sh + wv((0.05, -0.02, 0.06)), sh + wv((0.14, -0.08, 0.2)), sh + wv((0.24, -0.16, 0.3)),
              arm_pos - wv((0.03, -0.02, 0.02))]
    inked(kit, kit.skin("fx blood stream", [tuple(p) for p in stream], [(0, 1), (1, 2), (2, 3)],
                        [0.03, 0.022, 0.016, 0.026], cherry, root), 0.006)
    # ice cream chunks, a flying cone, cherries and sprinkles
    for i in range(7):
        d = wv((rand.uniform(-0.3, 1.0), rand.uniform(-0.9, 0.2), rand.uniform(-0.1, 1.0))).normalized()
        p = sh + d * rand.uniform(0.25, 0.6)
        r = rand.uniform(0.03, 0.055)
        m = vanilla if i % 3 else choc
        loft(kit, f"fx scoop {i}", [(-r * 0.6, r * 0.8, r * 0.8, 0, 0, 2, r * 0.18), (-r * 0.3, r * 1.0, r * 1.0),
                                     (r * 0.3, r * 0.9, r * 0.9), (r * 0.8, r * 0.3, r * 0.3)], [m], root, n=12,
             rot=(rand.uniform(0, 360), rand.uniform(0, 360), 0), offset=tuple(p), line=0.007)
    cone_p = at((0.62, -0.1, 0.55))
    waffle_cone(kit, "fx flying cone", 0.004, 0.045, 0.13, root, (150, 40, 0), tuple(cone_p), 0.006)
    for i, v in enumerate(((-0.25, -0.2, 0.55), (0.55, -0.35, 0.05))):
        p = at(v)
        inked(kit, kit.prim(f"fx cherry {i}", 'sphere', (0.025, 0.025, 0.025), cherry, root, offset=tuple(p)), 0.006)
        kit.skin(f"fx cherry stem {i}", [tuple(p + Vector((0, 0, 0.02))), tuple(p + Vector((0.015, 0.01, 0.06)))],
                 [(0, 1)], [0.003, 0.002], kit.mat("ink", INK), root, subsurf=0)
    cols = [CHERRY, TEAL, MUSTARD, NAVY, VANILLA]
    for i in range(40):
        d = wv((rand.uniform(-0.6, 1.0), rand.uniform(-1.0, 0.4), rand.uniform(-0.6, 1.0))).normalized()
        p = sh + d * rand.uniform(0.15, 0.75)
        kit.prim(f"fx sprinkle {i}", 'cyl', (0.006, 0.006, 0.026), kit.mat("sprinkle " + cols[i % 5], cols[i % 5]), root,
                 offset=tuple(p), rot=(rand.uniform(0, 180), rand.uniform(0, 180), 0), segments=6)
    # floor splats: cherry and vanilla puddles with ink rims, sprinkles on the floor
    for i, (x, y, r, m) in enumerate(((0.45, -0.2, 0.2, cherry), (0.15, -0.45, 0.12, vanilla), (0.75, 0.1, 0.1, cherry),
                                      (-0.25, -0.35, 0.09, choc), (0.55, -0.6, 0.08, cherry))):
        p = wv((x, y, 0))
        flat_poly(kit, f"fx floor splat {i}", blob_pts(rand, r, 26, 0.1, spikes=3, spike_len=0.3), m, root, line=0.012,
                  loc=(p.x, p.y, 0.004 + 0.001 * i), plane='XY', rot=(0, 0, rand.uniform(0, 360)))
        for j in range(3):
            a = rand.uniform(0, 2 * math.pi)
            q = p + wv((math.cos(a) * r * 1.9, math.sin(a) * r * 1.9, 0))
            flat_poly(kit, f"fx floor droplet {i} {j}", blob_pts(rand, r * 0.16, 10, 0.1), m, root, line=0.008,
                      loc=(q.x, q.y, 0.004), plane='XY')
    for i in range(18):
        p = wv((rand.uniform(-0.3, 0.9), rand.uniform(-0.8, 0.2), 0))
        kit.prim(f"fx floor sprinkle {i}", 'cyl', (0.006, 0.006, 0.026), kit.mat("sprinkle " + cols[i % 5], cols[i % 5]),
                 root, offset=(p.x, p.y, 0.008), rot=(90, 0, rand.uniform(0, 180)), segments=6)
    # pulp lettering
    txt_p = at((-0.95, 0.0, 0.62))
    tp = facing("fx splat text pivot", txt_p, -12)
    inked(kit, text_mesh(kit, "fx SPLAT text", "SPLAT!", 0.3, 0.03, FONT_BOLD, cherry, tp, (0, 0, 0), (90, 0, 0)), 0.014)


# ------------------------------------------------------------------ render hooks
# ================================================================== round 3: more models
JEANS = "#4d6d93"
GOO = "#a9dcb0"
GLOW = "#e4f7b8"
ASPHALT = "#6a6460"
STEEL = "#8c8a86"


def glow_mat(kit, name, hex_color, strength=1.0):
    """Flat emissive ink (no halftone) for glowing pustules and lamps."""
    key = ("glow " + name, hex_color, "emit")
    if key not in kit._mats:
        m = bpy.data.materials.new(f"ZD2 glow {name}")
        nt = v1.node_tree(m)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs[0].default_value = hexc(hex_color)
        em.inputs[1].default_value = strength
        nt.links.new(em.outputs[0], out.inputs[0])
        m.diffuse_color = hexc(hex_color)
        kit._mats[key] = m
    return kit._mats[key]


def fx_cam(root, default_offset):
    """Root-local camera position for camera-facing flat FX: the nearest scene camera within 9 m, else an offset."""
    best = None
    for ob in bpy.context.scene.objects:
        if ob.type == 'CAMERA':
            d = (ob.location - root.location).length
            if d < 9 and (best is None or d < best[0]):
                best = (d, ob.location.copy())
    world = best[1] if best else root.location + Vector(default_offset)
    return root.matrix_basis.inverted() @ world


def face_piv(kit, parent, name, pos, cam, spin=0.0, scale=1.0):
    d = (cam - Vector(pos)).normalized()
    q = (-d).to_track_quat('Y', 'Z') @ Quaternion((0, 1, 0), math.radians(spin))
    piv = kit.empty(name, parent, tuple(pos), scale=(scale, scale, scale))
    piv.rotation_euler = q.to_euler()
    return piv


def comic_cloud(kit, parent, name, pos, cam, r, count, line):
    rand = kit.rand
    smoke = kit.mat("smoke", SMOKE)
    shade = kit.mat("smoke shade", hex_scale(SMOKE, 0.82))
    piv = face_piv(kit, parent, name, pos, cam)
    for i in range(count):
        a = 2 * math.pi * i / count + rand.uniform(-0.3, 0.3)
        rr = r * rand.uniform(0.45, 0.7)
        off = (math.cos(a) * r * 0.62, -0.012 * r * (i % 3), math.sin(a) * r * 0.45 + r * 0.1)
        flat_poly(kit, f"{name} puff {i}", blob_pts(rand, rr, 16, 0.06), smoke, piv, line=line, loc=off)
        flat_poly(kit, f"{name} shade {i}", [(x * 0.75 + rr * 0.12, z * 0.55 - rr * 0.38) for x, z in blob_pts(rand, rr, 12, 0.04)],
                  shade, piv, line=0.0, loc=(off[0], off[1] - 0.003 * r * 10, off[2]))
    flat_poly(kit, f"{name} core", blob_pts(rand, r * 0.6, 16, 0.06), smoke, piv, line=line, loc=(0, -0.3 * r, 0))
    return piv


def comic_burst(kit, root, center, cam, size, text=None, goo=None, n_drops=16, n_scoops=6, n_sprinkles=30,
                clouds=3, floor=True, speed_lines=False, prefix="fx", text_at=(-0.9, -0.3, 1.25), text_size=0.55):
    """Generic pulp-comic explosion in root-local space: starburst + flames + flat smoke + cherry blood drops +
    ice cream chunks + sprinkles + floor splats + optional goo splashes, speed lines and lettering."""
    rand = kit.rand
    c = Vector(center)
    s = size
    L = 0.014 * max(1.0, s / 0.35) ** 0.6
    cherry = kit.mat("cherry", CHERRY)
    vanilla = kit.mat("vanilla", VANILLA)
    choc = kit.mat("chocolate", CHOC)
    orange = kit.mat("flame", ORANGE)
    mustard = kit.mat("mustard", MUSTARD)
    away = (c - cam).normalized()
    burst = face_piv(kit, root, f"{prefix} burst", c + away * 0.3 * s, cam, rand.uniform(-10, 10))
    flat_poly(kit, f"{prefix} burst outer", star_pts(12, s, s * 0.58, rand), orange, burst, line=L)
    flat_poly(kit, f"{prefix} burst inner", star_pts(10, s * 0.62, s * 0.38, rand), mustard, burst, line=L * 0.7,
              loc=(0, -0.03 * s, 0))
    flat_poly(kit, f"{prefix} burst core", blob_pts(rand, s * 0.24, 14, 0.12), vanilla, burst, line=L * 0.6,
              loc=(0, -0.06 * s, 0))
    for i in range(6):
        ang = -100 + i * 40 + rand.uniform(-10, 10)
        a = math.radians(ang + 90)
        d = s * rand.uniform(0.85, 1.05)
        sc = s * rand.uniform(0.5, 0.7)
        loc = (-d * math.cos(a), -0.02 * s, d * math.sin(a) * 0.85)
        flat_poly(kit, f"{prefix} flame {i}", flame_pts(sc, ang), orange, burst, line=L * 0.7, loc=loc)
        flat_poly(kit, f"{prefix} flame core {i}", flame_pts(sc * 0.55, ang), mustard, burst, line=0.0,
                  loc=(loc[0], loc[1] - 0.01 * s, loc[2] - 0.02 * s))
    if speed_lines:
        for i in range(22):
            a = 2 * math.pi * i / 22 + rand.uniform(-0.06, 0.06)
            r0, r1 = s * rand.uniform(1.25, 1.45), s * rand.uniform(1.9, 2.4)
            wdt = s * 0.022
            ca, sa = math.cos(a), math.sin(a)
            pts = [(ca * r0 - sa * 0.0, sa * r0), (ca * r1 - sa * wdt, sa * r1 + ca * wdt), (ca * r1 + sa * wdt, sa * r1 - ca * wdt)]
            flat_poly(kit, f"{prefix} speed line {i}", pts, kit.mat("ink", INK), burst, line=0.0, loc=(0, 0.05 * s, 0))
    for i in range(clouds):
        a = 2 * math.pi * i / clouds + rand.uniform(-0.4, 0.4)
        p = c + Vector((math.cos(a) * s * 1.1, 0.45 * s, math.sin(a) * s * 0.8 + 0.1 * s))
        comic_cloud(kit, root, f"{prefix} cloud {i}", p, cam, s * rand.uniform(0.4, 0.55), 5, L * 0.8)
    drop_mats = [cherry] + ([kit.mat("goo", goo)] if goo else [])
    for i in range(n_drops):
        d = Vector((rand.uniform(-1, 1), rand.uniform(-1, 0.6), rand.uniform(-0.3, 1.0))).normalized()
        drop(kit, f"{prefix} drop {i}", s * rand.uniform(0.035, 0.085), d, drop_mats[i % len(drop_mats)], root,
             tuple(c + d * s * rand.uniform(0.5, 1.6)), line=L * 0.45)
    for i in range(n_scoops):
        d = Vector((rand.uniform(-1, 1), rand.uniform(-1, 0.5), rand.uniform(-0.2, 1.0))).normalized()
        p = c + d * s * rand.uniform(0.7, 1.5)
        r = s * rand.uniform(0.08, 0.15)
        m = [vanilla, choc, kit.mat("goo", goo) if goo else cherry][i % 3]
        loft(kit, f"{prefix} scoop {i}", [(-r * 0.6, r * 0.8, r * 0.8, 0, 0, 2, r * 0.18), (-r * 0.3, r, r),
                                          (r * 0.3, r * 0.9, r * 0.9), (r * 0.8, r * 0.3, r * 0.3)], [m], root, n=10,
             rot=(rand.uniform(0, 360), rand.uniform(0, 360), 0), offset=tuple(p), line=L * 0.5)
    cols = [CHERRY, TEAL, MUSTARD, NAVY, VANILLA]
    for i in range(n_sprinkles):
        d = Vector((rand.uniform(-1, 1), rand.uniform(-1, 0.5), rand.uniform(-0.5, 1.0))).normalized()
        p = c + d * s * rand.uniform(0.4, 2.0)
        kit.prim(f"{prefix} sprinkle {i}", 'cyl', (0.006, 0.006, 0.026), kit.mat("sprinkle " + cols[i % 5], cols[i % 5]),
                 root, offset=tuple(p), rot=(rand.uniform(0, 180), rand.uniform(0, 180), 0), segments=6)
    if goo:
        gm = kit.mat("goo", goo)
        for i in range(5):
            a = math.radians(-60 + i * 30 + rand.uniform(-8, 8))
            p = c + Vector((math.sin(a) * s * 0.95, -0.2 * s, math.cos(a) * s * 0.75))
            piv = face_piv(kit, root, f"{prefix} goo splash {i}", p, cam, -math.degrees(a))
            pts = blob_pts(rand, s * 0.1, 14, 0.15, spikes=4, spike_len=1.0)
            flat_poly(kit, f"{prefix} goo splash {i} shape", pts, gm, piv, line=L * 0.7)
    if floor:
        mats = [cherry, vanilla, kit.mat("goo", goo) if goo else choc, cherry, choc]
        for i in range(5):
            a = rand.uniform(0, 2 * math.pi)
            dd = s * rand.uniform(0.2, 1.4)
            p = Vector((c.x + math.cos(a) * dd, c.y + math.sin(a) * dd * 0.7, 0))
            r = s * rand.uniform(0.18, 0.4)
            flat_poly(kit, f"{prefix} floor splat {i}", blob_pts(rand, r, 24, 0.1, spikes=3, spike_len=0.3), mats[i],
                      root, line=L * 0.8, loc=(p.x, p.y, 0.004 + 0.0012 * i), plane='XY', rot=(0, 0, rand.uniform(0, 360)))
            for j in range(3):
                b = rand.uniform(0, 2 * math.pi)
                q = p + Vector((math.cos(b) * r * 1.8, math.sin(b) * r * 1.8, 0))
                flat_poly(kit, f"{prefix} floor droplet {i} {j}", blob_pts(rand, r * 0.15, 10, 0.1), mats[i], root,
                          line=L * 0.5, loc=(q.x, q.y, 0.004), plane='XY')
    if text:
        tp = face_piv(kit, root, f"{prefix} text pivot", c + Vector(text_at) * s, cam, -10)
        t = text_mesh(kit, f"{prefix} text", text, s * text_size, s * 0.06, FONT_BOLD, cherry, tp, (0, 0, 0), (90, 0, 0))
        inked(kit, t, L * 1.1)
    return burst


def stump(kit, parent, name, loc, r, rot=(0, 0, 0), line=0.005):
    """Cherry-red wound cap with a cream bone nub for a severed joint."""
    inked(kit, kit.prim(name, 'sphere', (r, r, r * 0.45), kit.mat("cherry", CHERRY), parent, offset=loc, rot=rot), line)
    kit.prim(name + " bone", 'cyl', (r * 0.3, r * 0.3, r * 0.9), kit.mat("cream", CREAM), parent, offset=loc, rot=rot)


def surf_y(secs, z, x, inset=0.0):
    """Front (-Y) surface of a loft at height z and lateral x, for placing decals on bodies."""
    secs = [tuple(list(s) + [0, 0, 2, 0][len(s) - 3:])[:7] for s in secs]
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            rx, ry, cx, cy, p = [a[i] + (b[i] - a[i]) * t for i in (1, 2, 3, 4, 5)]
            u = min(0.98, abs(x - cx) / rx)
            return cy - ry * (1 - u ** p) ** (1 / p) * 0.97 + inset
    raise ValueError(z)


# ------------------------------------------------------------------ sprinter
def spr_hips(kit, piv, W):
    loft(kit, "sprinter hips", [(-0.08, 0.13, 0.09), (0.0, 0.135, 0.095), (0.06, 0.13, 0.09)], [kit.mat("jeans", JEANS)],
         piv, n=12, line=W)
    kit.prim("sprinter belt", 'cyl', (0.137, 0.097, 0.018), kit.mat("ink", INK), piv, offset=(0, 0, 0.02), segments=16)
    kit.prim("sprinter buckle", 'box', (0.03, 0.01, 0.024), kit.mat("mustard", MUSTARD), piv, offset=(0, -0.098, 0.02))


def spr_torso(kit, piv, W):
    zs = kit.mat("zombie skin", ZSKIN)
    ink = kit.mat("ink", INK)
    secs = [(-0.05, 0.13, 0.09, 0, 0, 2.2, 0.02), (0.05, 0.125, 0.085), (0.18, 0.14, 0.09), (0.32, 0.165, 0.095, 0, 0, 2.4),
            (0.4, 0.15, 0.08, 0, 0, 2.2), (0.44, 0.06, 0.05)]
    loft(kit, "sprinter tee", secs, [kit.mat("shirt", SHIRT)], piv, n=12, line=W)
    # ripped chest showing ribs
    y = surf_y(secs, 0.22, 0.04, -0.004)
    kit.prim("sprinter rib hole rim", 'sphere', (0.07, 0.012, 0.075), ink, piv, offset=(0.035, y + 0.006, 0.22), rot=(0, 15, 0))
    kit.prim("sprinter rib hole", 'sphere', (0.064, 0.012, 0.068), zs, piv, offset=(0.035, y + 0.002, 0.22), rot=(0, 15, 0))
    for i in range(3):
        kit.prim(f"sprinter rib {i}", 'box', (0.075 - i * 0.01, 0.006, 0.008), ink, piv,
                 offset=(0.035, y - 0.009, 0.25 - i * 0.03), rot=(0, 15, 8 * (i - 1)))
    kit.prim("sprinter tee stain", 'sphere', (0.04, 0.01, 0.03), kit.mat("cherry", CHERRY), piv,
             offset=(-0.07, surf_y(secs, 0.1, -0.07, -0.002), 0.1), rot=(0, -20, 0))
    torus(kit, "sprinter collar", 0.06, 0.012, kit.mat("shirt", SHIRT), piv, (0, 0, 0.425), (0, 0, 0), line=W * 0.5)
    inked(kit, kit.skin("sprinter neck", [(0, 0, 0.4), (0, -0.02, 0.52)], [(0, 1)], [0.036, 0.032], zs, piv), W)


def spr_head(kit, piv, W):
    zs = kit.mat("zombie skin", ZSKIN)
    ink = kit.mat("ink", INK)
    hair = kit.mat("hair", "#1f2420")
    secs = [(0.0, 0.035, 0.03, 0, -0.05), (0.04, 0.05, 0.055, 0, -0.03), (0.09, 0.056, 0.074, 0, -0.01),
            (0.14, 0.075, 0.085, 0, 0), (0.19, 0.078, 0.088, 0, 0.01), (0.23, 0.064, 0.075, 0, 0.015), (0.25, 0.03, 0.035, 0, 0.015)]
    loft(kit, "sprinter head", secs, [zs, hair], piv, n=12, line=W, mat_fn=lambda c: 1 if (c.z > 0.2 or (c.y > 0.03 and c.z > 0.1)) else 0)
    # greaser quiff swept back by the speed
    inked(kit, kit.prim("sprinter quiff", 'sphere', (0.065, 0.1, 0.045), hair, piv, offset=(0, -0.02, 0.235), rot=(-12, 0, 0)), W * 0.6)
    for i, x in enumerate((-0.04, 0.0, 0.04)):
        kit.prim(f"sprinter hair streak {i}", 'cone', (0.022, 0.016, 0.12), hair, piv, offset=(x, 0.1, 0.22 - 0.01 * abs(i - 1)),
                 rot=(-100, 0, 0), taper=0.0, segments=6)
    for s in (-1, 1):
        y = surf_y(secs, 0.15, s * 0.032)
        kit.prim(f"sprinter socket {s}", 'sphere', (0.02, 0.01, 0.015), ink, piv, offset=(s * 0.032, y, 0.15))
        kit.prim(f"sprinter eye glow {s}", 'sphere', (0.007, 0.005, 0.007), glow_mat(kit, "red eye", "#ff5a4a", 1.5), piv,
                 offset=(s * 0.032, y - 0.008, 0.152))
        kit.prim(f"sprinter brow {s}", 'box', (0.036, 0.01, 0.01), ink, piv, offset=(s * 0.034, y - 0.002, 0.178),
                 rot=(0, 20 * s, 0))
        inked(kit, kit.prim(f"sprinter ear {s}", 'cone', (0.014, 0.006, 0.05), zs, piv, offset=(s * 0.082, 0.02, 0.15),
                            rot=(0, 70 * s, 0), taper=0.0, segments=6), W * 0.4)
    inked(kit, kit.prim("sprinter nose", 'cone', (0.012, 0.01, 0.05), zs, piv, offset=(0, -0.098, 0.115), rot=(75, 0, 0),
                        taper=0.0, segments=6), W * 0.4)
    # screaming open jaw
    kit.prim("sprinter mouth", 'sphere', (0.03, 0.014, 0.038), ink, piv, offset=(0, -0.055, 0.045))
    for i, x in enumerate((-0.016, 0.0, 0.016)):
        kit.prim(f"sprinter fang top {i}", 'cone', (0.006, 0.004, 0.016), kit.mat("cream", CREAM), piv,
                 offset=(x, -0.066, 0.072), rot=(180, 0, 0), taper=0.0, segments=4)
        kit.prim(f"sprinter fang bottom {i}", 'cone', (0.005, 0.004, 0.012), kit.mat("cream", CREAM), piv,
                 offset=(x + 0.008, -0.066, 0.016), taper=0.0, segments=4)


def spr_arm(kit, piv, s, W):
    zs = kit.mat("zombie skin", ZSKIN)
    inked(kit, kit.skin(f"sprinter sleeve {s}", [(0, 0, 0), (s * 0.015, 0.06, -0.04)], [(0, 1)], [0.05, 0.047],
                        kit.mat("shirt", SHIRT), piv), W * 0.7)
    inked(kit, kit.skin(f"sprinter arm {s}", [(0, 0.0, 0.0), (s * 0.04, 0.2, -0.14), (s * 0.05, 0.41, -0.08)], [(0, 1), (1, 2)],
                        [0.04, 0.033, 0.028], zs, piv), W)
    kit.prim(f"sprinter elbow bone {s}", 'sphere', (0.016, 0.016, 0.016), kit.mat("cream", CREAM), piv,
             offset=(s * 0.048, 0.205, -0.17))
    inked(kit, kit.prim(f"sprinter hand {s}", 'sphere', (0.03, 0.04, 0.016), zs, piv, offset=(s * 0.05, 0.45, -0.075)), W * 0.5)
    for i, x in enumerate((-0.018, 0.0, 0.018)):
        x += s * 0.05
        inked(kit, kit.skin(f"sprinter finger {s} {i}", [(x, 0.47, -0.075), (x, 0.515, -0.08), (x * 1.03, 0.545, -0.1)],
                            [(0, 1), (1, 2)], [0.009, 0.008, 0.005], zs, piv, subsurf=0), W * 0.4)


def spr_leg(kit, piv, s, front, W):
    jeans = kit.mat("jeans", JEANS)
    zs = kit.mat("zombie skin", ZSKIN)
    if front:
        pts, shoe_c, shoe_r = [(0, 0, 0), (0, -0.39, -0.08), (0, -0.33, -0.47)], (0, -0.38, -0.53), (-20, 0, 0)
    else:
        pts, shoe_c, shoe_r = [(0, 0, 0), (0, 0.2, -0.4), (0, 0.44, -0.68)], (0, 0.42, -0.77), (55, 0, 0)
    inked(kit, kit.skin(f"sprinter leg {s}", pts, [(0, 1), (1, 2)], [0.07, 0.052, 0.045], jeans, piv), W)
    a = Vector(pts[2])
    d = (Vector(pts[2]) - Vector(pts[1])).normalized()
    q = Vector((0, 0, 1)).rotation_difference(d)
    loft(kit, f"sprinter cuff {s}", [(-0.03, 0.05, 0.05), (0.0, 0.056, 0.056)], [kit.mat("jeans cuff", hex_scale(JEANS, 1.25))],
         piv, n=10, rot=q, offset=tuple(a - d * 0.02), line=W * 0.5)
    inked(kit, kit.skin(f"sprinter ankle {s}", [tuple(a), tuple(a + d * 0.05)], [(0, 1)], [0.03, 0.03], zs, piv), W * 0.5)
    sp = kit.empty(f"sprinter shoe pivot {s}", piv, shoe_c, shoe_r)
    inked(kit, kit.prim(f"sprinter sneaker {s}", 'box', (0.09, 0.24, 0.08), kit.mat("cream", CREAM), sp, bevel=0.025), W * 0.7)
    kit.prim(f"sprinter sneaker toe {s}", 'sphere', (0.046, 0.05, 0.035), kit.mat("cherry", CHERRY), sp, offset=(0, -0.09, -0.005))
    kit.prim(f"sprinter sneaker sole {s}", 'box', (0.094, 0.244, 0.018), kit.mat("ink", INK), sp, offset=(0, 0, -0.04))
    if not front:
        kit.prim("sprinter knee hole", 'sphere', (0.04, 0.01, 0.035), zs, piv, offset=(0.0, 0.17, -0.42), rot=(30, 0, 0))


SPRINTER_RUN = dict(hips=((0, 0.05, 0.92), (0, 0, 40)), torso=((0, 0, 0.03), (50, 0, 8)), head=((0, -0.03, 0.45), (-66, 0, -10)),
                    arm={1: ((0.16, 0.0, 0.37), (-30, 0, -60)), -1: ((-0.16, 0.0, 0.37), (-42, 0, 50))},
                    leg={1: ((0.075, 0, -0.03), (0, 0, -3)), -1: ((-0.075, 0, -0.03), (0, 0, 4))})


def build_sprinter(kit, root, hit=False, pose=None):
    W = 0.008
    P = pose or SPRINTER_RUN
    if not hit:
        hips = kit.empty("sprinter hips pivot", root, *P['hips'])
        spr_hips(kit, hips, W)
        torso = kit.empty("sprinter torso pivot", hips, *P['torso'])
        spr_torso(kit, torso, W)
        spr_head(kit, kit.empty("sprinter head pivot", torso, *P['head']), W)
        for s in (1, -1):
            spr_arm(kit, kit.empty(f"sprinter arm pivot {s}", torso, *P['arm'][s]), s, W)
            spr_leg(kit, kit.empty(f"sprinter leg pivot {s}", hips, *P['leg'][s]), s, s == -1, W)
        return
    # blown apart by a single hit: every piece flies out of one comic explosion
    hips = kit.empty("sprinter hips pivot", root, (0.05, 0.1, 0.55), (-35, 25, 40))
    spr_hips(kit, hips, W)
    stump(kit, hips, "sprinter waist stump", (0, 0, 0.07), 0.12)
    torso = kit.empty("sprinter torso pivot", root, (-0.1, 0.15, 1.15), (-70, -30, 60))
    spr_torso(kit, torso, W)
    stump(kit, torso, "sprinter torso stump", (0, 0, -0.06), 0.12)
    head = kit.empty("sprinter head pivot", root, (0.25, -0.05, 1.95), (30, 40, -60))
    spr_head(kit, head, W)
    stump(kit, head, "sprinter neck stump", (0, -0.01, 0.0), 0.04)
    for s, loc, rot in ((1, (0.75, -0.2, 1.45), (40, -120, 30)), (-1, (-0.7, 0.05, 1.6), (-160, 30, -40))):
        a = kit.empty(f"sprinter arm pivot {s}", root, loc, rot)
        spr_arm(kit, a, s, W)
        stump(kit, a, f"sprinter shoulder stump {s}", (0, 0, 0), 0.045, rot=(90, 0, 0))
    for s, loc, rot in ((1, (0.6, -0.35, 0.55), (60, 30, 80)), (-1, (-0.55, -0.2, 0.75), (-40, -60, 20))):
        lg = kit.empty(f"sprinter leg pivot {s}", root, loc, rot)
        spr_leg(kit, lg, s, s == -1, W)
        stump(kit, lg, f"sprinter hip stump {s}", (0, 0, 0), 0.07)
    cam = fx_cam(root, (-0.25, -5.2, 1.9))
    comic_burst(kit, root, (0, 0, 1.1), cam, 0.42, text="SPLUT!", n_drops=14, n_scoops=5, n_sprinkles=24, clouds=3,
                prefix="sprinter fx")


# ------------------------------------------------------------------ bloater
BLOAT_BODY = [(0.42, 0.3, 0.26, 0, 0.0, 2.2), (0.55, 0.48, 0.42, 0, -0.04, 2.2), (0.75, 0.6, 0.56, 0, -0.1, 2.1),
              (0.98, 0.64, 0.6, 0, -0.12, 2.1), (1.22, 0.6, 0.54, 0, -0.07, 2.2), (1.45, 0.52, 0.44, 0, -0.02, 2.3),
              (1.62, 0.38, 0.32, 0, 0.0, 2.4), (1.72, 0.18, 0.16, 0, 0.0), (1.76, 0.1, 0.1)]


def bloat_pustule(kit, parent, name, loc, r, W):
    inked(kit, kit.prim(name, 'sphere', (r, r, r), glow_mat(kit, "pustule", GLOW, 1.15), parent, offset=loc, segments=10, rings=6),
          W * 0.6)
    kit.prim(name + " ring", 'sphere', (r * 1.25, r * 1.25, r * 1.25), kit.mat("pustule rim", "#7c9a52"), parent,
             offset=tuple(Vector(loc) + Vector((0, 0.35 * r, 0))), segments=8, rings=5)
    kit.prim(name + " shine", 'sphere', (r * 0.3, r * 0.2, r * 0.3), kit.mat("vanilla", VANILLA), parent,
             offset=tuple(Vector(loc) + Vector((r * 0.35, -r * 0.85, r * 0.35))), segments=6, rings=4)


def bloat_body(kit, piv, W, upto=None):
    """Milkman-uniform blimp of a body. upto: cut height for the burst stump."""
    zs = kit.mat("zombie skin", ZSKIN)
    shirt = kit.mat("shirt", SHIRT)
    navy = kit.mat("navy", NAVY)
    secs = BLOAT_BODY if upto is None else BLOAT_BODY[:2] + [(upto, 0.56, 0.52, 0, -0.08, 2.1, 0.05)]
    loft(kit, "bloater body", secs, [shirt, navy, zs], piv, n=16, line=W,
         mat_fn=lambda c: 1 if c.z < 0.62 else (2 if (c.z < 1.0 and c.y < 0.08) else 0))
    loft(kit, "bloater waistband", [(0.6, 0.545, 0.5, 0, -0.07, 2.2), (0.66, 0.565, 0.52, 0, -0.085, 2.2)], [navy], piv, n=20,
         line=W * 0.7)
    if upto is not None:
        loft(kit, "bloater goo stump", [(upto - 0.05, 0.5, 0.46, 0, -0.08, 2, 0.04), (upto + 0.08, 0.42, 0.38, 0, -0.06),
                                        (upto + 0.16, 0.2, 0.2, 0.05, -0.05), (upto + 0.2, 0.05, 0.05, 0.05, -0.05)],
             [kit.mat("goo", GOO)], piv, n=14, line=W)
        return
    # shirt hem riding up over the belly
    loft(kit, "bloater shirt hem", [(0.97, 0.655, 0.615, 0, -0.12, 2.1, 0.025), (1.04, 0.648, 0.605, 0, -0.115, 2.1)], [shirt],
         piv, n=20, line=W * 0.7)
    zd = kit.mat("zombie shade", hex_scale(ZSKIN, 0.72))
    kit.prim("bloater belly button", 'sphere', (0.03, 0.012, 0.02), kit.mat("ink", INK), piv,
             offset=(0.0, surf_y(secs, 0.8, 0.0, 0.004), 0.8))
    for i, (x, z, a) in enumerate(((-0.22, 0.85, 25), (-0.27, 0.72, -15), (0.24, 0.9, -30), (0.3, 0.76, 10))):
        kit.prim(f"bloater stretch mark {i}", 'box', (0.09, 0.008, 0.008), zd, piv, offset=(x, surf_y(secs, z, x, 0.002), z),
                 rot=(0, a, 0))
    for i, (x, z, r) in enumerate(((0.15, 0.88, 0.055), (-0.12, 0.7, 0.04), (0.35, 0.72, 0.035), (-0.38, 0.9, 0.05),
                                   (0.05, 0.68, 0.028))):
        bloat_pustule(kit, piv, f"bloater belly pustule {i}", (x, surf_y(secs, z, x, r * 0.4), z), r, W)
    for i, (x, z) in enumerate(((0.0, 1.45), (0.0, 1.3), (0.0, 1.15))):
        kit.prim(f"bloater button {i}", 'cyl', (0.025, 0.025, 0.012), kit.mat("cream", CREAM), piv,
                 offset=(x, surf_y(secs, z, x, -0.002), z), rot=(90, 0, 0), segments=10)
    for s in (-1, 1):
        pts = [(s * 0.2, 0.05, 1.72)] + [(s * (0.22 + 0.06 * (1.6 - z)), surf_y(secs, z, s * (0.22 + 0.06 * (1.6 - z)), -0.01), z)
                                         for z in (1.6, 1.4, 1.2)]
        pts.append((s * 0.29, surf_y(secs, 1.06, s * 0.29, -0.01), 1.06))
        inked(kit, kit.skin(f"bloater suspender {s}", pts, [(i, i + 1) for i in range(len(pts) - 1)], [0.022] * len(pts),
                            kit.mat("cherry", CHERRY), piv, subsurf=0), W * 0.5)
        bloat_pustule(kit, piv, f"bloater shoulder pustule {s}", (s * 0.4, -0.05, 1.56), 0.045, W)
        bloat_pustule(kit, piv, f"bloater back pustule {s}", (s * 0.42, 0.35, 1.2), 0.06, W)
    for s in (-1, 1):
        inked(kit, kit.prim(f"bloater bowtie {s}", 'cone', (0.04, 0.016, 0.06), kit.mat("teal", TEAL), piv,
                            offset=(s * 0.035, -0.16, 1.71), rot=(0, -90 * s, 0), taper=0.3, segments=4), W * 0.5)


def bloat_head(kit, piv, W, cap=True):
    zs = kit.mat("zombie skin", ZSKIN)
    ink = kit.mat("ink", INK)
    secs = [(0.0, 0.14, 0.12, 0, -0.03), (0.05, 0.155, 0.135, 0, -0.045), (0.1, 0.135, 0.125, 0, -0.03),
            (0.16, 0.12, 0.115, 0, -0.01), (0.22, 0.115, 0.11), (0.27, 0.09, 0.09), (0.3, 0.04, 0.04)]
    loft(kit, "bloater head", secs, [zs], piv, n=14, line=W)
    kit.prim("bloater chin crease", 'box', (0.16, 0.008, 0.008), kit.mat("zombie shade", hex_scale(ZSKIN, 0.72)), piv,
             offset=(0, surf_y(secs, 0.07, 0, 0.002), 0.07), rot=(0, 0, 0))
    yb = surf_y(secs, 0.17, 0.045)
    inked(kit, kit.prim("bloater pop eye", 'sphere', (0.024, 0.02, 0.024), kit.mat("cream", CREAM), piv,
                        offset=(0.045, yb + 0.004, 0.175)), W * 0.4)
    kit.prim("bloater pupil", 'sphere', (0.007, 0.005, 0.007), ink, piv, offset=(0.05, yb - 0.016, 0.172))
    kit.prim("bloater squint", 'box', (0.04, 0.008, 0.008), ink, piv, offset=(-0.045, yb + 0.002, 0.17), rot=(0, 12, 0))
    kit.prim("bloater nose", 'sphere', (0.03, 0.025, 0.022), zs, piv, offset=(0, surf_y(secs, 0.13, 0) - 0.01, 0.13))
    for s in (-1, 1):
        kit.prim(f"bloater nostril {s}", 'sphere', (0.006, 0.005, 0.005), ink, piv,
                 offset=(s * 0.01, surf_y(secs, 0.13, 0) - 0.034, 0.124))
        inked(kit, kit.prim(f"bloater ear {s}", 'sphere', (0.018, 0.03, 0.035), zs, piv, offset=(s * 0.12, 0.0, 0.16)), W * 0.4)
    ym = surf_y(secs, 0.085, 0)
    kit.prim("bloater mouth", 'sphere', (0.05, 0.012, 0.016), ink, piv, offset=(0, ym + 0.004, 0.085), rot=(0, -6, 0))
    inked(kit, kit.skin("bloater drool", [(0.02, ym - 0.004, 0.075), (0.024, ym - 0.012, 0.0), (0.024, ym - 0.016, -0.05)],
                        [(0, 1), (1, 2)], [0.01, 0.009, 0.015], kit.mat("goo", GOO), piv), W * 0.4)
    bloat_pustule(kit, piv, "bloater cheek pustule", (-0.09, surf_y(secs, 0.11, -0.09, 0.012), 0.11), 0.025, W)
    if cap:
        bloat_cap(kit, kit.empty("bloater cap pivot", piv, (0, 0.0, 0.24), (-6, 0, 8)), W)


def bloat_cap(kit, piv, W):
    loft(kit, "bloater milkman cap", [(0.0, 0.118, 0.115), (0.07, 0.122, 0.12), (0.09, 0.13, 0.13, 0, -0.01, 3)],
         [kit.mat("cream", CREAM)], piv, n=14, subsurf=0, line=W * 0.6)
    kit.prim("bloater cap band", 'cyl', (0.121, 0.118, 0.025), kit.mat("navy", NAVY), piv, offset=(0, 0, 0.02), segments=14)
    inked(kit, kit.prim("bloater cap brim", 'cyl', (0.1, 0.07, 0.01), kit.mat("ink", INK), piv, offset=(0, -0.12, 0.005),
                        rot=(-12, 0, 0), segments=12), W * 0.4)
    kit.prim("bloater cap badge", 'cyl', (0.02, 0.02, 0.006), kit.mat("mustard", MUSTARD), piv, offset=(0, -0.122, 0.05),
             rot=(90, 0, 0), segments=8)


def bloat_arm(kit, piv, s, W):
    zs = kit.mat("zombie skin", ZSKIN)
    inked(kit, kit.skin(f"bloater sleeve {s}", [(0, 0, 0), (s * 0.06, -0.03, -0.17)], [(0, 1)], [0.15, 0.135],
                        kit.mat("shirt", SHIRT), piv), W)
    inked(kit, kit.skin(f"bloater arm {s}", [(0, 0, -0.05), (s * 0.16, -0.05, -0.35), (s * 0.14, -0.15, -0.62)], [(0, 1), (1, 2)],
                        [0.12, 0.115, 0.09], zs, piv), W)
    inked(kit, kit.prim(f"bloater mitt {s}", 'sphere', (0.085, 0.075, 0.09), zs, piv, offset=(s * 0.145, -0.17, -0.72)), W * 0.7)
    for i in range(4):
        x = s * 0.145 + (i - 1.5) * 0.04
        inked(kit, kit.skin(f"bloater finger {s} {i}", [(x, -0.22, -0.74), (x, -0.235, -0.8)], [(0, 1)], [0.022, 0.018], zs, piv,
                            subsurf=0), W * 0.4)
    bloat_pustule(kit, piv, f"bloater arm pustule {s}", (s * 0.24, -0.1, -0.33), 0.035, W)


def bloat_leg(kit, piv, s, W):
    inked(kit, kit.skin(f"bloater leg {s}", [(0, 0, 0), (s * 0.03, -0.03, -0.22), (s * 0.04, 0, -0.4)], [(0, 1), (1, 2)],
                        [0.2, 0.16, 0.13], kit.mat("navy", NAVY), piv), W)
    inked(kit, kit.prim(f"bloater shoe {s}", 'box', (0.22, 0.36, 0.13), kit.mat("shoe", SHOE), piv, offset=(s * 0.04, -0.07, -0.43),
                        bevel=0.05), W * 0.7)
    kit.prim(f"bloater sole {s}", 'box', (0.226, 0.366, 0.03), kit.mat("ink", INK), piv, offset=(s * 0.04, -0.07, -0.485))


def build_bloater(kit, root, pop=False):
    W = 0.011
    legs = {s: kit.empty(f"bloater leg pivot {s}", root, (s * 0.27, -0.02, 0.5), (0, 0, s * 4)) for s in (-1, 1)}
    for s, p in legs.items():
        bloat_leg(kit, p, s, W)
    if not pop:
        body = kit.empty("bloater body pivot", root, (0, 0, 0), (-4, 0, 3))
        bloat_body(kit, body, W)
        bloat_head(kit, kit.empty("bloater head pivot", body, (0, -0.02, 1.7), (6, 0, -10)), W)
        for s in (-1, 1):
            bloat_arm(kit, kit.empty(f"bloater arm pivot {s}", body, (s * 0.6, -0.02, 1.42), (8, 0, -s * 4)), s, W)
        return
    # the moment it bursts: legs and a goo stump stay, everything else is thrown out of a huge explosion
    body = kit.empty("bloater body pivot", root, (0, 0, 0), (-4, 0, 3))
    bloat_body(kit, body, W, upto=0.72)
    head = kit.empty("bloater head pivot", root, (0.5, -0.6, 2.3), (25, 20, -35))
    bloat_head(kit, head, W, cap=False)
    stump(kit, head, "bloater neck stump", (0, -0.02, 0.0), 0.11)
    bloat_cap(kit, kit.empty("bloater cap pivot", root, (0.55, 0.3, 3.05), (-40, 30, -20)), W)
    for s, loc, rot in ((1, (1.45, -0.2, 1.75), (20, 75, 30)), (-1, (-1.5, 0.1, 1.55), (-30, 80, -40))):
        a = kit.empty(f"bloater arm pivot {s}", root, loc, rot)
        bloat_arm(kit, a, s, W)
        stump(kit, a, f"bloater shoulder stump {s}", (0, 0, 0.02), 0.13)
    rand = kit.rand
    zs = kit.mat("zombie skin", ZSKIN)
    shirt = kit.mat("shirt", SHIRT)
    cam = fx_cam(root, (0.9, -5.6, 1.9))
    for i in range(10):
        d = Vector((rand.uniform(-1, 1), rand.uniform(-0.8, 0.6), rand.uniform(-0.1, 1.0))).normalized()
        p = Vector((0, 0, 1.25)) + d * rand.uniform(0.9, 1.6)
        r = rand.uniform(0.09, 0.16)
        loft(kit, f"bloater chunk {i}", [(-r * 0.4, r * 0.9, r * 0.6, 0, 0, 2, r * 0.25), (0, r, r * 0.7),
                                         (r * 0.35, r * 0.7, r * 0.5, 0, 0, 2, r * 0.2)], [zs if i % 2 else shirt, kit.mat("cherry", CHERRY)],
             root, n=10, rot=(rand.uniform(0, 360), rand.uniform(0, 360), 0), offset=tuple(p), line=0.009,
             mat_fn=lambda c, r=r: 1 if c.z < -r * 0.3 else 0)
        if i < 4:
            bloat_pustule(kit, root, f"bloater flying pustule {i}", tuple(p + d * 0.2), 0.04, W)
    for i in range(4):
        d = Vector((rand.uniform(-1, 1), -0.5, rand.uniform(0.2, 1.0))).normalized()
        kit.prim(f"bloater flying button {i}", 'cyl', (0.025, 0.025, 0.012), kit.mat("cream", CREAM), root,
                 offset=tuple(Vector((0, 0, 1.3)) + d * rand.uniform(0.8, 1.4)), rot=(rand.uniform(0, 180), rand.uniform(0, 180), 0),
                 segments=10)
    for i in range(3):
        a = math.radians(rand.uniform(0, 360))
        p = Vector((math.cos(a) * 1.0, -0.3, 1.3 + math.sin(a) * 0.9))
        piv = face_piv(kit, root, f"bloater rag {i}", p, cam, rand.uniform(0, 360))
        flat_poly(kit, f"bloater rag {i} shape", blob_pts(rand, 0.12, 9, 0.45), shirt, piv, line=0.01)
    comic_burst(kit, root, (0, 0, 1.25), cam, 1.15, text="KA-BLOOEY!", goo=GOO, n_drops=26, n_scoops=8, n_sprinkles=60,
                clouds=6, speed_lines=True, prefix="bloater fx", text_at=(-0.75, -0.4, 0.95), text_size=0.4)


# ------------------------------------------------------------------ truck
SPRINTER_CLIMB = dict(hips=((0, 0.12, 1.05), (0, 0, 0)), torso=((0, 0, 0.03), (8, 0, -4)), head=((0, -0.03, 0.45), (-38, 0, 25)),
                      arm={1: ((0.16, 0.0, 0.37), (112, 0, -12)), -1: ((-0.16, 0.0, 0.37), (98, 0, 14))},
                      leg={1: ((0.075, 0, -0.03), (-38, 0, -4)), -1: ((-0.075, 0, -0.03), (6, 0, 6))})


def flat_quad(kit, name, corners, mat, parent, thick=0.0, line=None):
    bm = bmesh.new()
    bm.faces.new([bm.verts.new(c) for c in corners])
    ob = kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)
    if thick:
        sol = ob.modifiers.new("Thick", 'SOLIDIFY')
        sol.thickness = thick
        sol.offset = 0
    if line:
        inked(kit, ob, line)
    return ob


def minigun(kit, piv, W):
    teal = kit.mat("teal", TEAL)
    mustard = kit.mat("mustard", MUSTARD)
    cream = kit.mat("cream", CREAM)
    cherry = kit.mat("cherry", CHERRY)
    along = (90, 0, 0)
    loft(kit, "minigun housing", [(-0.45, 0.04, 0.04), (-0.4, 0.13, 0.13), (-0.2, 0.16, 0.16), (0.05, 0.15, 0.15), (0.12, 0.11, 0.11)],
         [teal], piv, n=12, rot=along, line=W)
    for i in range(6):
        a = 2 * math.pi * i / 6
        x, z = 0.075 * math.cos(a), 0.075 * math.sin(a)
        kit.prim(f"minigun barrel {i}", 'cyl', (0.026, 0.026, 0.62), kit.mat("gun dark", "#22625f"), piv, offset=(x, -0.42, z),
                 rot=(90, 0, 0), segments=8)
        kit.prim(f"minigun nozzle {i}", 'cone', (0.04, 0.04, 0.07), cream, piv, offset=(x * 1.15, -0.75, z * 1.15), rot=(90, 0, 0),
                 taper=0.55, segments=6)
    for i, y in enumerate((-0.2, -0.45, -0.68)):
        torus(kit, f"minigun band {i}", 0.11, 0.018, mustard, piv, (0, y, 0), (90, 0, 0), seg=14, rs=4, line=W * 0.7)
    for s in (-1, 1):
        inked(kit, kit.skin(f"minigun handle {s}", [(s * 0.08, 0.38, 0.0), (s * 0.2, 0.46, -0.02), (s * 0.2, 0.5, -0.12)],
                            [(0, 1), (1, 2)], [0.02] * 3, kit.mat("ink", INK), piv, subsurf=0), W * 0.4)
    # pint hopper with a soft-serve swirl, feeding the gun
    loft(kit, "minigun hopper", [(0.0, 0.17, 0.17), (0.12, 0.185, 0.185), (0.2, 0.195, 0.195), (0.34, 0.22, 0.22)], [cream, cherry],
         piv, n=16, subsurf=0,
         offset=(0.32, 0.05, 0.12), line=W, mat_fn=lambda c: 1 if 0.12 < c.z < 0.2 else 0)
    for i, (r, z) in enumerate(((0.19, 0.4), (0.15, 0.48), (0.1, 0.55), (0.05, 0.6))):
        torus(kit, f"minigun swirl {i}", r, 0.055 - i * 0.008, kit.mat("vanilla", VANILLA), piv, (0.32, 0.05, 0.12 + z),
              (0, 0, i * 30), seg=14, rs=6, line=W * 0.6)
    inked(kit, kit.prim("minigun swirl cherry", 'sphere', (0.05, 0.05, 0.05), cherry, piv, offset=(0.32, 0.05, 0.8)), W * 0.5)
    inked(kit, kit.skin("minigun feed chute", [(0.32, 0.05, 0.12), (0.25, 0.0, -0.05), (0.1, -0.05, -0.05)], [(0, 1), (1, 2)],
                        [0.06, 0.055, 0.05], mustard, piv), W * 0.6)
    # curved armour shield with rivets
    shield = [(-0.3, -0.2, -0.2), (0.3, -0.2, -0.2), (0.33, -0.23, 0.2), (0.0, -0.27, 0.28), (-0.33, -0.23, 0.2)]
    flat_quad(kit, "minigun shield", shield, kit.mat("cherry", CHERRY), piv, thick=0.025, line=W)
    for i, x in enumerate((-0.22, -0.07, 0.07, 0.22)):
        kit.prim(f"minigun rivet {i}", 'sphere', (0.016, 0.012, 0.016), mustard, piv, offset=(x, -0.235, 0.16))


def truck_body(kit, piv, W):
    teal = kit.mat("teal", TEAL)
    cream = kit.mat("cream", CREAM)
    cherry = kit.mat("cherry", CHERRY)
    navy = kit.mat("navy", NAVY)
    ink = kit.mat("ink", INK)
    glass = kit.mat("glass", "#33435f")
    secs = [(-2.78, 1.0, 0.95, 0, 1.52, 5), (-2.74, 1.12, 1.05, 0, 1.52, 6), (0.85, 1.12, 1.05, 0, 1.52, 6),
            (1.0, 1.12, 0.98, 0, 1.47, 5), (1.65, 1.1, 0.86, 0, 1.38, 4), (2.0, 1.08, 0.5, 0, 0.98, 4),
            (2.55, 1.02, 0.46, 0, 0.92, 3.5), (2.75, 0.85, 0.38, 0, 0.88, 3), (2.8, 0.5, 0.2, 0, 0.9, 2)]
    loft(kit, "truck body", secs, [cream, teal], piv, n=60, rot=(90, 0, 0), line=0.022, even=True,
         mat_fn=lambda c: 1 if c.y < 1.1 else 0)
    # cherry spear stripe hugging both flanks, dipping toward the hood
    for side in (-1, 1):
        bm = bmesh.new()
        rows = []
        steps = 56
        for k in range(steps + 1):
            z = -2.74 + (2.5 + 2.74) * k / steps
            a, b = [(sa, sb) for sa, sb in zip(secs, secs[1:]) if sa[0] <= z <= sb[0]][0]
            t = (z - a[0]) / (b[0] - a[0])
            rx, ry, cy, pp = [a[i] + (b[i] - a[i]) * t for i in (1, 2, 4, 5)]
            h = 1.12 - 0.1 * max(0.0, (z - 0.6) / 1.9)
            row = []
            for dh in (-0.09, 0.09):
                u = min(0.97, abs(h + dh - cy) / ry)
                x = rx * (1 - u ** pp) ** (1 / pp) + 0.012
                row.append(bm.verts.new((side * x, -z, h + dh)))
            rows.append(row)
        for r0, r1 in zip(rows, rows[1:]):
            bm.faces.new((r0[0], r1[0], r1[1], r0[1]) if side > 0 else (r0[1], r1[1], r1[0], r0[0]))
        ob = kit.mesh_from_bmesh(f"truck spear stripe {side}", bm, cherry, piv)
        ob.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.012
        inked(kit, ob, 0.008)
    # windshield, cab windows
    for s in (-1, 1):
        flat_quad(kit, f"truck windshield {s}", [(s * 0.06, -1.7, 2.2), (s * 0.92, -1.68, 2.12), (s * 0.95, -1.98, 1.56),
                                                 (s * 0.06, -2.0, 1.6)], glass, piv, thick=0.02, line=0.012)
        flat_quad(kit, f"truck windshield glint {s}", [(s * 0.3, -1.74, 2.12), (s * 0.4, -1.735, 2.12), (s * 0.28, -1.95, 1.66),
                                                       (s * 0.18, -1.955, 1.66)], cream, piv, thick=0.025)
        flat_quad(kit, f"truck side window {s}", [(s * 1.13, -1.0, 2.2), (s * 1.12, -1.6, 2.1), (s * 1.12, -1.6, 1.6),
                                                  (s * 1.13, -1.0, 1.6)], glass, piv, thick=0.03, line=0.012)
    # front: grille, headlights, chrome bumper
    inked(kit, kit.prim("truck grille", 'cyl', (0.5, 0.26, 0.05), cream, piv, offset=(0, -2.8, 0.92), rot=(90, 0, 0), segments=20), 0.012)
    for i in range(7):
        kit.prim(f"truck grille bar {i}", 'box', (0.035, 0.03, 0.4 - 0.025 * abs(i - 3) ** 2), ink, piv,
                 offset=(-0.33 + i * 0.11, -2.83, 0.92))
    for s in (-1, 1):
        inked(kit, kit.prim(f"truck headlight {s}", 'sphere', (0.16, 0.08, 0.16), glow_mat(kit, "lamp", "#fff3c4", 1.1), piv,
                            offset=(s * 0.75, -2.62, 1.2)), 0.012)
        torus(kit, f"truck headlight rim {s}", 0.16, 0.03, cream, piv, (s * 0.75, -2.6, 1.2), (90, 0, 0), seg=16, rs=4)
    inked(kit, kit.prim("truck bumper", 'box', (2.3, 0.2, 0.18), cream, piv, offset=(0, -2.86, 0.55), bevel=0.06), 0.014)
    inked(kit, kit.prim("truck rear bumper", 'box', (2.25, 0.18, 0.16), cream, piv, offset=(0, 2.82, 0.55), bevel=0.06), 0.014)
    # wedge plow with hazard stripes
    for s in (-1, 1):
        # plow blade: alternating mustard / ink hazard bands, raked back
        bm = bmesh.new()
        n = 8
        top = [bm.verts.new((s * 1.18 * k / n, -3.5 + 0.45 * k / n + 0.2, 0.78)) for k in range(n + 1)]
        bot = [bm.verts.new((s * 1.18 * k / n + s * 0.06, -3.5 + 0.45 * k / n - 0.02, 0.12)) for k in range(n + 1)]
        for k in range(n):
            f = bm.faces.new((bot[k], bot[k + 1], top[k + 1], top[k]))
            f.material_index = k % 2
        ob = kit.mesh_from_bmesh(f"truck plow {s}", bm, [kit.mat("mustard", MUSTARD), ink], piv, smooth=False)
        sol = ob.modifiers.new("Thick", 'SOLIDIFY')
        sol.thickness = 0.05
        sol.offset = 0
        inked(kit, ob, 0.016)
        inked(kit, kit.skin(f"truck plow arm {s}", [(s * 0.6, -2.9, 0.55), (s * 0.6, -3.18, 0.5)], [(0, 1)], [0.05, 0.05], ink, piv,
                            subsurf=0), 0.01)
    # wheels with whitewalls and hubcaps
    for x in (-1, 1):
        for y in (-1.9, 1.75):
            kit.prim(f"truck tire {x} {y}", 'cyl', (0.43, 0.43, 0.28), ink, piv, offset=(x * 0.97, y, 0.43), rot=(0, 90, 0), segments=18)
            kit.prim(f"truck whitewall {x} {y}", 'cyl', (0.3, 0.3, 0.03), cream, piv, offset=(x * 1.105, y, 0.43), rot=(0, 90, 0),
                     segments=18)
            kit.prim(f"truck hubcap {x} {y}", 'cyl', (0.18, 0.18, 0.04), kit.mat("steel", STEEL), piv, offset=(x * 1.12, y, 0.43),
                     rot=(0, 90, 0), segments=14)
            kit.prim(f"truck hub {x} {y}", 'sphere', (0.04, 0.06, 0.06), cherry, piv, offset=(x * 1.14, y, 0.43))
    # serving window (+X), counter, scalloped striped awning, menu board, lettering
    flat_quad(kit, "truck serving window", [(1.13, -0.45, 2.15), (1.13, 1.25, 2.15), (1.13, 1.25, 1.35), (1.13, -0.45, 1.35)],
              kit.mat("window dark", "#2a2a35"), piv, thick=0.03)
    for (a, b) in (((1.14, -0.5, 2.18), (0.06, 1.8, 0.07)), ((1.14, -0.5, 1.32), (0.06, 1.8, 0.07))):
        inked(kit, kit.prim("truck window frame", 'box', (b[0], b[1], b[2]), cream, piv, offset=(a[0], 0.4, a[2])), 0.008)
    for y in (-0.5, 1.3):
        inked(kit, kit.prim("truck window post", 'box', (0.06, 0.07, 0.9), cream, piv, offset=(1.14, y, 1.75)), 0.008)
    inked(kit, kit.prim("truck counter", 'box', (0.3, 1.9, 0.06), cream, piv, offset=(1.25, 0.4, 1.3), bevel=0.02), 0.01)
    for i in range(3):
        kit.prim(f"truck counter pint {i}", 'cyl', (0.06, 0.06, 0.12), kit.mat(f"pint {[TEAL, CHERRY, MUSTARD][i]}",
                 [TEAL, CHERRY, MUSTARD][i]), piv, offset=(1.25, -0.2 + i * 0.25, 1.39), segments=10)
    soft = [(0.95, 0.22), (1.05, 0.16), (1.12, 0.1), (1.18, 0.03)]
    for i, (z, r) in enumerate(soft):
        kit.prim(f"truck window soft serve {i}", 'sphere', (r, r, 0.06), kit.mat("vanilla", VANILLA), piv, offset=(0.95, 0.9, 1.0 + z))
    stripes = 8
    for i in range(stripes):
        y0, y1 = -0.6 + 2.0 * i / stripes, -0.6 + 2.0 * (i + 1) / stripes
        flat_quad(kit, f"truck awning {i}", [(1.12, y0, 2.36), (1.12, y1, 2.36), (1.72, y1, 2.12), (1.72, y0, 2.12)],
                  kit.mat("cherry", CHERRY) if i % 2 else cream, piv, thick=0.02)
        bm = bmesh.new()
        n = 6
        ring = [bm.verts.new((1.72, (y0 + y1) / 2 + 0.125 * math.cos(math.pi * k / n), 2.12 - 0.09 * math.sin(math.pi * k / n)))
                for k in range(n + 1)]
        bm.faces.new(ring)
        ob = kit.mesh_from_bmesh(f"truck awning scallop {i}", bm, kit.mat("cherry", CHERRY) if i % 2 else cream, piv, smooth=False)
        ob.modifiers.new("Thick", 'SOLIDIFY').thickness = 0.02
        inked(kit, ob, 0.008)
    kit.skin("truck awning edge", [(1.12, -0.6, 2.37), (1.12, 1.4, 2.37)], [(0, 1)], [0.025, 0.025], ink, piv, subsurf=0)
    for y in (-0.55, 1.35):
        kit.skin(f"truck awning strut {y}", [(1.13, y, 1.95), (1.72, y, 2.11)], [(0, 1)], [0.015, 0.015], ink, piv, subsurf=0)
    inked(kit, text_mesh(kit, "truck lettering", "ICE CREAM", 0.42, 0.03, FONT_BOLD, cream, piv, (1.14, 0.2, 0.74), (90, 0, 90),
                         resolution=1), 0.014)
    text_mesh(kit, "truck lettering small", "Scoops & Shooters", 0.16, 0.015, FONT_SERIF, cherry, piv, (1.14, -1.35, 0.78),
              (90, 0, 90), resolution=1)
    inked(kit, kit.prim("truck menu board", 'box', (0.04, 0.55, 0.65), navy, piv, offset=(1.14, 1.95, 1.75), bevel=0.02), 0.01)
    for i in range(4):
        kit.prim(f"truck menu line {i}", 'box', (0.05, 0.4 - 0.08 * (i % 2), 0.035), cream, piv, offset=(1.15, 1.95, 1.95 - i * 0.13))
    # roof: turret, open hatch, giant cone, loudspeaker horn
    roof = 2.57
    loft(kit, "truck turret ring", [(roof - 0.02, 0.42, 0.42), (roof + 0.12, 0.4, 0.4)], [navy], piv, n=16, subsurf=0,
         offset=(0, -0.35, 0), line=0.012)
    inked(kit, kit.skin("truck turret post", [(0, -0.35, roof + 0.1), (0, -0.35, roof + 0.32)], [(0, 1)], [0.09, 0.08], ink, piv,
                        subsurf=0), 0.01)
    minigun(kit, kit.empty("truck minigun pivot", piv, (0, -0.4, roof + 0.42), (4, 0, 8)), 0.012)
    inked(kit, kit.prim("truck hatch frame", 'box', (0.7, 0.7, 0.08), cream, piv, offset=(-0.45, 1.25, roof + 0.03), bevel=0.02), 0.01)
    kit.prim("truck hatch hole", 'box', (0.56, 0.56, 0.09), ink, piv, offset=(-0.45, 1.25, roof + 0.04))
    hp = kit.empty("truck hatch lid hinge", piv, (-0.45, 1.6, roof + 0.07), (-110, 0, 0))
    inked(kit, kit.prim("truck hatch lid", 'box', (0.66, 0.66, 0.05), navy, hp, offset=(0, -0.33, 0), bevel=0.015), 0.01)
    cone_p = kit.empty("truck giant cone pivot", piv, (0.35, 1.95, roof + 0.02))
    waffle_cone(kit, "truck giant cone", 0.03, 0.2, 0.32, cone_p, (0, 0, 0), (0, 0, 0), 0.012)
    loft(kit, "truck giant scoop", [(0.3, 0.2, 0.2, 0, 0, 2, 0.04), (0.38, 0.235, 0.235), (0.5, 0.2, 0.2), (0.6, 0.06, 0.06)],
         [kit.mat("vanilla", VANILLA)], cone_p, n=14, line=0.012)
    inked(kit, kit.prim("truck giant cherry", 'sphere', (0.07, 0.07, 0.07), cherry, cone_p, offset=(0, 0, 0.63)), 0.008)
    for i in range(10):
        a = 2 * math.pi * i / 10
        kit.prim(f"truck giant sprinkle {i}", 'cyl', (0.012, 0.012, 0.05), kit.mat("sprinkle " + [CHERRY, TEAL, MUSTARD, NAVY, CREAM][i % 5],
                 [CHERRY, TEAL, MUSTARD, NAVY, CREAM][i % 5]), cone_p, offset=(0.2 * math.cos(a), 0.2 * math.sin(a), 0.42 + 0.05 * (i % 2)),
                 rot=(70, 0, math.degrees(a) + 40), segments=5)
    inked(kit, kit.prim("truck horn", 'cone', (0.16, 0.16, 0.42), kit.mat("mustard", MUSTARD), piv, offset=(-0.6, -0.6, roof + 0.2),
                        rot=(-80, 0, -20), taper=0.15, segments=14), 0.01)
    kit.skin("truck horn post", [(-0.6, -0.6, roof), (-0.6, -0.6, roof + 0.18)], [(0, 1)], [0.03, 0.03], ink, piv, subsurf=0)
    # rear ladder up to the roof
    for x in (-0.85, -0.45):
        kit.skin(f"truck ladder rail {x}", [(x, 2.84, 0.55), (x, 2.84, roof + 0.25), (x, 2.6, roof + 0.3)], [(0, 1), (1, 2)],
                 [0.025] * 3, kit.mat("steel", STEEL), piv, subsurf=0)
    for i in range(7):
        kit.prim(f"truck ladder rung {i}", 'cyl', (0.02, 0.02, 0.4), kit.mat("steel", STEEL), piv, offset=(-0.65, 2.84, 0.75 + i * 0.28),
                 rot=(0, 90, 0), segments=6)


def road_chunk(kit, root):
    asphalt = kit.mat("asphalt", ASPHALT)
    ink = kit.mat("ink", INK)
    kit.prim("road asphalt", 'box', (8.0, 16.0, 0.1), asphalt, root, offset=(-0.3, 0, -0.05))
    kit.prim("road shoulder", 'box', (1.2, 16.0, 0.08), kit.mat("dirt", "#cdb38a"), root, offset=(-4.9, 0, -0.04))
    inked(kit, kit.prim("road curb", 'box', (0.25, 16.0, 0.18), kit.mat("concrete", "#d9d0bc"), root, offset=(3.82, 0, 0.04)), 0.015)
    kit.prim("road sidewalk", 'box', (1.2, 16.0, 0.14), kit.mat("sidewalk", "#e3dac6"), root, offset=(4.55, 0, 0.02))
    for i in range(8):
        kit.prim(f"road sidewalk seam {i}", 'box', (1.2, 0.03, 0.15), kit.mat("concrete dark", "#a49c8a"), root,
                 offset=(4.55, -7.0 + i * 2.0, 0.02))
    for i in range(6):
        kit.prim(f"road center dash {i}", 'box', (0.16, 1.4, 0.01), kit.mat("mustard", MUSTARD), root, offset=(-1.75, -6.8 + i * 2.8, 0.004))
    for x in (-4.1, 3.45):
        kit.prim(f"road edge line {x}", 'box', (0.12, 16.0, 0.01), kit.mat("cream", CREAM), root, offset=(x, 0, 0.004))
    rand = kit.rand
    for i in range(5):
        p = Vector((rand.uniform(-3.5, 3.0), rand.uniform(-7, 7), 0.006))
        pts = [tuple(p + Vector((rand.uniform(-0.2, 0.2) + k * 0.35, rand.uniform(-0.25, 0.25), 0))) for k in range(4)]
        kit.skin(f"road crack {i}", pts, [(k, k + 1) for k in range(3)], [0.015] * 4, ink, root, subsurf=0)
    for i in range(6):
        kit.prim(f"road weed {i}", 'cone', (0.08, 0.08, 0.25), kit.mat("weed", "#7f9a52"), root,
                 offset=(rand.uniform(-5.4, -4.4), rand.uniform(-7.5, 7.5), 0.1), taper=0.0, segments=5)


def street_lamp(kit, root, loc):
    p = kit.empty("lamp pivot", root, loc, (0, 0, 180))
    navy = kit.mat("navy", NAVY)
    inked(kit, kit.skin("lamp pole", [(0, 0, 0), (0, 0, 3.6), (0.15, 0, 4.1), (0.75, 0, 4.25)], [(0, 1), (1, 2), (2, 3)],
                        [0.07, 0.055, 0.045, 0.04], navy, p, subsurf=0), 0.014)
    inked(kit, kit.prim("lamp base", 'cyl', (0.16, 0.16, 0.4), navy, p, offset=(0, 0, 0.2), taper=0.7, segments=10), 0.012)
    inked(kit, kit.prim("lamp head", 'sphere', (0.32, 0.16, 0.09), navy, p, offset=(0.9, 0, 4.22), rot=(0, -6, 0)), 0.012)
    kit.prim("lamp glow", 'sphere', (0.25, 0.12, 0.04), glow_mat(kit, "lamp", "#fff3c4", 1.1), p, offset=(0.92, 0, 4.15))


def road_sign(kit, root, loc, rotz):
    p = kit.empty("sign pivot", root, loc, (0, 0, rotz))
    kit.skin("sign post", [(0, 0.02, 0), (0, 0.02, 2.3)], [(0, 1)], [0.035, 0.035], kit.mat("steel", STEEL), p, subsurf=0)
    inked(kit, kit.prim("sign diamond", 'box', (0.75, 0.04, 0.75), kit.mat("mustard", MUSTARD), p, offset=(0, 0, 2.2),
                        rot=(0, 45, 0), bevel=0.04), 0.014)
    inked(kit, text_mesh(kit, "sign text", "ZOMBIE\nX-ING", 0.17, 0.01, FONT_BOLD, kit.mat("ink", INK), p, (0, -0.035, 2.2),
                         (90, 0, 0)), 0.0)


def mailbox(kit, root, loc, rotz):
    p = kit.empty("mailbox pivot", root, loc, (0, 0, rotz))
    navy = kit.mat("navy", NAVY)
    for x in (-0.18, 0.18):
        kit.prim(f"mailbox leg {x}", 'box', (0.06, 0.06, 0.4), navy, p, offset=(x, 0, 0.2))
    loft(kit, "mailbox body", [(0.38, 0.24, 0.2, 0, 0, 6), (0.95, 0.24, 0.2, 0, 0, 6), (1.05, 0.2, 0.18, 0, 0, 3),
                               (1.12, 0.1, 0.18, 0, 0, 2)], [navy], p, n=12, line=0.012)
    inked(kit, text_mesh(kit, "mailbox text", "U.S. MAIL", 0.08, 0.005, FONT_BOLD, kit.mat("cream", CREAM), p, (0, -0.205, 0.8),
                         (90, 0, 0)), 0.0)
    kit.prim("mailbox stripe", 'box', (0.49, 0.41, 0.03), kit.mat("cherry", CHERRY), p, offset=(0, 0, 0.68))


def wrecked_car(kit, root, loc, rotz, cam):
    p = kit.empty("wreck pivot", root, loc, (3, -6, rotz))
    cherry = kit.mat("cherry", CHERRY)
    cream = kit.mat("cream", CREAM)
    secs = [(-2.4, 0.8, 0.28, 0, 0.62, 3), (-2.2, 0.92, 0.36, 0, 0.62, 4), (-0.8, 0.92, 0.38, 0, 0.64, 4), (-0.5, 0.88, 0.62, 0, 0.84, 3),
            (0.8, 0.88, 0.62, 0, 0.84, 3), (1.1, 0.92, 0.38, 0, 0.64, 4), (2.2, 0.9, 0.34, 0, 0.6, 4), (2.35, 0.7, 0.2, 0, 0.55, 2)]
    loft(kit, "wreck body", secs, [cherry, cream, kit.mat("glass", "#33435f")], p, n=24, rot=(90, 0, 0), line=0.016, even=True,
         mat_fn=lambda c: 2 if (c.y > 1.0 and -0.4 < c.z < 0.7) else (1 if c.y > 1.15 else 0))
    for s in (-1, 1):
        flat_quad(kit, f"wreck fin {s}", [(s * 0.8, 2.0, 0.9), (s * 0.85, 2.4, 1.18), (s * 0.85, 2.45, 0.85), (s * 0.82, 1.4, 0.88)],
                  cherry, p, thick=0.04, line=0.01)
    for x in (-0.85, 0.85):
        for y, z in ((-1.5, 0.32), (1.5, 0.3)):
            kit.prim(f"wreck tire {x} {y}", 'cyl', (0.32, 0.32, 0.2), kit.mat("ink", INK), p, offset=(x, y, z), rot=(0, 90, 0), segments=14)
            kit.prim(f"wreck whitewall {x} {y}", 'cyl', (0.2, 0.2, 0.02), cream, p, offset=(x * 1.11, y, z), rot=(0, 90, 0), segments=14)
    hp = kit.empty("wreck hood hinge", p, (0, -1.0, 1.0), (-38, 0, 8))
    inked(kit, kit.prim("wreck popped hood", 'box', (1.5, 1.2, 0.05), cherry, hp, offset=(0, -0.6, 0)), 0.01)
    inked(kit, kit.prim("wreck crumpled bumper", 'box', (1.9, 0.15, 0.14), kit.mat("steel", STEEL), p, offset=(0, -2.45, 0.42),
                        rot=(0, 8, 14)), 0.01)
    comic_cloud(kit, root, "wreck smoke", Vector(loc) + Vector((0.1, -1.2, 1.6)), cam, 0.55, 5, 0.018)
    comic_cloud(kit, root, "wreck smoke high", Vector(loc) + Vector((0.4, -0.9, 2.4)), cam, 0.38, 4, 0.016)


def build_truck(kit, root):
    cam = fx_cam(root, (7.0, -8.2, 3.6))
    road_chunk(kit, root)
    truck = kit.empty("truck pivot", root, (0.6, 0.0, 0.0))
    truck_body(kit, truck, 0.012)
    build_player(kit, kit.empty("truck player", truck, (0.55, 0.15, 2.57), (0, 0, -12)))
    build_sprinter(kit, kit.empty("truck sprinter", truck, (1.42, 2.1, 0.55), (0, 0, -90)), pose=SPRINTER_CLIMB)
    for i, (x, y, r) in enumerate(((-2.3, -3.3, 160), (-1.3, -4.9, 185), (2.5, 3.9, 245))):
        build_zombie(kit, kit.empty(f"truck walker {i}", root, (x, y, 0), (0, 0, r)), hit=False)
    street_lamp(kit, root, (4.4, 6.2, 0.09))
    road_sign(kit, root, (4.5, 3.0, 0.09), -40)
    mailbox(kit, root, (4.6, 0.4, 0.09), 60)
    wrecked_car(kit, root, (-3.4, -1.0, 0.0), -18, cam)


# ------------------------------------------------------------------ sundae shotgun
def build_shotgun(kit, root):
    w = 0.0035
    teal = kit.mat("gun teal", TEAL)
    cherry = kit.mat("cherry", CHERRY)
    mustard = kit.mat("mustard", MUSTARD)
    cream = kit.mat("cream", CREAM)
    vanilla = kit.mat("vanilla", VANILLA)
    ink = kit.mat("ink", INK)
    along = (90, 0, 0)
    root = kit.empty("shotgun scale pivot", root, (0, 0.06, 0.0), scale=(0.8, 0.8, 0.8))
    # cherry bakelite stock with a cream butt plate and fins
    loft(kit, "shotgun stock", [(-0.33, 0.024, 0.07, 0, -0.065, 3), (-0.31, 0.028, 0.078, 0, -0.065, 3),
                                (-0.16, 0.025, 0.045, 0, -0.025, 2.6), (-0.06, 0.024, 0.032, 0, -0.008)], [cherry], root, n=12,
         rot=along, line=w)
    kit.prim("shotgun butt plate", 'box', (0.05, 0.02, 0.15), cream, root, offset=(0, 0.335, -0.065), bevel=0.008)
    for s, z0 in ((1, 0.0), (-1, -0.13)):
        fin = [(0.18, z0), (0.3, z0), (0.36, z0 + s * 0.06), (0.32, z0 + s * 0.065), (0.24, z0 + s * 0.02)]
        flat_quad(kit, f"shotgun fin {s}", [(0, y, z) for y, z in fin], mustard, root, thick=0.006, line=w)
    # rocket receiver
    loft(kit, "shotgun receiver", [(-0.09, 0.02, 0.02), (-0.07, 0.04, 0.045), (0.02, 0.046, 0.05), (0.1, 0.042, 0.045),
                                   (0.13, 0.03, 0.032)], [teal], root, n=14, rot=along, line=w)
    loft(kit, "shotgun receiver stripe", [(-0.06, 0.0465, 0.01, 0, 0.0), (0.0, 0.05, 0.01), (0.09, 0.044, 0.009)], [cream], root,
         n=12, rot=along)
    torus(kit, "shotgun gyro ring", 0.06, 0.006, mustard, root, (0, 0.02, 0), (90, 0, 0), seg=16, rs=5, line=w)
    # over-under barrels with bands, pump slide under them
    for z in (0.02, -0.02):
        kit.prim(f"shotgun barrel {z}", 'cyl', (0.019, 0.019, 0.3), kit.mat("gun dark", "#22625f"), root, offset=(0, -0.26, z),
                 rot=(90, 0, 0), segments=12)
    for i, y in enumerate((-0.14, -0.33, -0.39)):
        loft(kit, f"shotgun band {i}", [(0, 0.026, 0.045, 0, 0, 3), (0.012, 0.026, 0.045, 0, 0, 3)], [mustard], root, n=12,
             subsurf=0, rot=along, offset=(0, y + 0.006, 0), line=w)
    loft(kit, "shotgun pump", [(0.17, 0.026, 0.026, 0, -0.06), (0.18, 0.03, 0.03, 0, -0.06), (0.29, 0.03, 0.03, 0, -0.06),
                               (0.3, 0.026, 0.026, 0, -0.06)], [cherry], root, n=12, rot=along, line=w)
    for i in range(4):
        kit.prim(f"shotgun pump ridge {i}", 'cyl', (0.032, 0.032, 0.005), ink, root, offset=(0, -0.2 - i * 0.025, -0.06),
                 rot=(90, 0, 0), segments=12)
    kit.prim("shotgun pump rod", 'cyl', (0.008, 0.008, 0.2), ink, root, offset=(0, -0.08, -0.05), rot=(90, 0, 0), segments=6)
    # sundae-boat muzzle: a long glass banana-split dish on a stem, three scoops, whipped cream and a cherry sight
    dish = kit.mat("glass dish", "#e8eef0")
    loft(kit, "shotgun sundae boat", [(-0.045, 0.022, 0.06, 0, 0, 2.2), (-0.03, 0.04, 0.085, 0, 0, 2.4),
                                      (0.0, 0.055, 0.105, 0, 0, 2.6), (0.025, 0.062, 0.115, 0, 0, 2.8, 0.004)], [dish], root,
         n=20, offset=(0, -0.48, 0.0), line=w)
    kit.prim("shotgun boat rim shade", 'cyl', (0.052, 0.104, 0.004), kit.mat("glass dish shade", "#b9c6cc"), root,
             offset=(0, -0.48, 0.026), segments=20)
    for z in (0.012, -0.018):
        kit.prim(f"shotgun bore {z}", 'cyl', (0.014, 0.011, 0.004), ink, root, offset=(0, -0.592, z), rot=(90, 0, 0), segments=10)
    for i, (y, m) in enumerate(((-0.42, VANILLA), (-0.48, CHOC), (-0.54, "#e9a0a8"))):
        inked(kit, kit.prim(f"shotgun boat scoop {i}", 'sphere', (0.04, 0.032, 0.03), kit.mat(f"scoop {m}", m), root,
                            offset=(0, y, 0.045)), w)
    for i, y in enumerate((-0.4, -0.56)):
        kit.prim(f"shotgun boat banana {i}", 'cyl', (0.012, 0.012, 0.05), kit.mat("banana", "#ecd27a"), root,
                 offset=(0.045, y, 0.03), rot=(70, 0, 0), segments=8)
    loft(kit, "shotgun whip", [(0.07, 0.026, 0.026, 0, 0, 2, 0.006), (0.09, 0.02, 0.02), (0.105, 0.011, 0.011), (0.118, 0.002, 0.002)],
         [vanilla], root, n=10, offset=(0, -0.48, 0.0), line=w)
    inked(kit, kit.prim("shotgun cherry sight", 'sphere', (0.014, 0.014, 0.014), cherry, root, offset=(0, -0.48, 0.13)), w)
    kit.skin("shotgun cherry stem", [(0, -0.48, 0.141), (0, -0.472, 0.168)], [(0, 1)], [0.002, 0.0015], ink, root, subsurf=0)
    # pistol grip, trigger, guard
    gv = [(-0.016, 0.03, -0.03), (0.016, 0.03, -0.03), (0.016, 0.08, -0.03), (-0.016, 0.08, -0.03),
          (-0.018, 0.06, -0.13), (0.018, 0.06, -0.13), (0.018, 0.11, -0.125), (-0.018, 0.11, -0.125)]
    gf = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    inked(kit, kit.cage("shotgun grip", gv, gf, cherry, root, subsurf=2), w)
    kit.skin("shotgun guard", [(0, -0.03, -0.04), (0, -0.035, -0.08), (0, 0.0, -0.095), (0, 0.035, -0.085)], [(0, 1), (1, 2), (2, 3)],
             [0.005] * 4, mustard, root, subsurf=0)
    kit.prim("shotgun trigger", 'cone', (0.005, 0.008, 0.03), ink, root, offset=(0, -0.008, -0.06), rot=(-20, 0, 0), taper=0.5)
    # fed by pints: a top-loading pint with a swirl, and a side saddle of spare pints on the +X flank
    loft(kit, "shotgun pint", [(0.045, 0.035, 0.035), (0.06, 0.037, 0.037), (0.08, 0.039, 0.039), (0.11, 0.041, 0.041)],
         [cream, teal], root, n=16, subsurf=0, offset=(0, 0.02, 0), line=w, mat_fn=lambda c: 1 if 0.06 < c.z < 0.08 else 0)
    torus(kit, "shotgun pint rim", 0.041, 0.004, cream, root, (0, 0.02, 0.11), seg=16, rs=4, line=w)
    for i, (r, z) in enumerate(((0.034, 0.12), (0.025, 0.138), (0.015, 0.152))):
        torus(kit, f"shotgun pint swirl {i}", r, 0.011, kit.mat("scoop #e9a0a8", "#e9a0a8"), root, (0, 0.02, z), (0, 0, i * 40),
              seg=12, rs=5, line=w)
    kit.prim("shotgun saddle plate", 'box', (0.006, 0.15, 0.05), mustard, root, offset=(0.05, -0.01, -0.005), bevel=0.003)
    for i in range(3):
        inked(kit, kit.prim(f"shotgun saddle pint {i}", 'cyl', (0.018, 0.018, 0.04), kit.mat(f"pint {[TEAL, CHERRY, MUSTARD][i]}",
              [TEAL, CHERRY, MUSTARD][i]), root, offset=(0.066, -0.06 + i * 0.045, -0.005), rot=(0, 90, 0), segments=12), w * 0.7)
        kit.prim(f"shotgun saddle pint lid {i}", 'cyl', (0.019, 0.019, 0.006), cream, root, offset=(0.088, -0.06 + i * 0.045, -0.005),
                 rot=(0, 90, 0), segments=12)


# ------------------------------------------------------------------ props
def label(kit, parent, text, size, mat, loc, rot, font=FONT_BOLD):
    return text_mesh(kit, f"label {text}", text, size, size * 0.06, font, mat, parent, loc, rot)


def build_props(kit, root):
    W = 0.007
    cream = kit.mat("cream", CREAM)
    cherry = kit.mat("cherry", CHERRY)
    teal = kit.mat("teal", TEAL)
    ink = kit.mat("ink", INK)
    vanilla = kit.mat("vanilla", VANILLA)
    wood = kit.mat("crate wood", "#b9854a")
    rand = kit.rand
    # gun crate: plank box, open lid propped back, straw and a Scoop Pistol inside
    crate = kit.empty("props gun crate", root, (-0.55, 0.2, 0), (0, 0, 8))
    for i, z in enumerate((0.05, 0.15, 0.25)):
        for s in (-1, 1):
            inked(kit, kit.prim(f"crate plank y {s} {i}", 'box', (0.8, 0.025, 0.095), wood, crate, offset=(0, s * 0.225, z)), W * 0.6)
            inked(kit, kit.prim(f"crate plank x {s} {i}", 'box', (0.025, 0.43, 0.095), wood, crate, offset=(s * 0.4, 0, z)), W * 0.6)
    kit.prim("crate floor", 'box', (0.8, 0.45, 0.02), kit.mat("crate dark", "#8a5d30"), crate, offset=(0, 0, 0.01))
    for s in (-1, 1):
        kit.prim(f"crate corner {s}", 'box', (0.05, 0.05, 0.31), kit.mat("crate dark", "#8a5d30"), crate, offset=(s * 0.39, -0.22, 0.155))
    kit.prim("crate straw", 'box', (0.76, 0.41, 0.03), kit.mat("straw", "#e2bf6a"), crate, offset=(0, 0, 0.2))
    for i in range(14):
        kit.prim(f"crate straw bit {i}", 'cyl', (0.004, 0.004, 0.1), kit.mat("straw", "#e2bf6a"), crate,
                 offset=(rand.uniform(-0.35, 0.35), rand.uniform(-0.19, 0.19), 0.22), rot=(rand.uniform(60, 120), 0, rand.uniform(0, 180)),
                 segments=4)
    lid = kit.empty("crate lid hinge", crate, (0, 0.24, 0.3), (-105, 0, 0))
    for i in range(4):
        inked(kit, kit.prim(f"crate lid plank {i}", 'box', (0.8, 0.11, 0.025), wood, lid, offset=(0, -0.06 - i * 0.112, 0)), W * 0.6)
    kit.prim("crate lid batten", 'box', (0.06, 0.44, 0.02), kit.mat("crate dark", "#8a5d30"), lid, offset=(0, -0.22, -0.02))
    label(kit, crate, "SCOOP Co.  HANDLE WITH CARE", 0.04, ink, (0, -0.24, 0.15), (90, 0, 0))
    GUN_LINE[0] = 0.0045
    build_gun(kit, kit.empty("crate pistol", crate, (0.0, 0.0, 0.3), (0, -90, 75)))
    GUN_LINE[0] = 0.0028
    # three-gallon flavor tub, lid leaning on it, scooper stuck in
    tub = kit.empty("props flavor tub", root, (0.25, 0.3, 0))
    loft(kit, "tub body", [(0.0, 0.16, 0.16), (0.1, 0.165, 0.165), (0.2, 0.17, 0.17), (0.32, 0.175, 0.175)], [cream, cherry], tub,
         n=20, subsurf=0, line=W, mat_fn=lambda c: 1 if 0.1 < c.z < 0.2 else 0)
    loft(kit, "tub ice cream", [(0.3, 0.17, 0.17, 0, 0, 2, 0.008), (0.33, 0.16, 0.16), (0.345, 0.1, 0.1, 0.04, 0.02)],
         [kit.mat("scoop #e9a0a8", "#e9a0a8")], tub, n=16, line=W * 0.6)
    label(kit, tub, "STRAWBERRY", 0.045, cream, (0, -0.178, 0.15), (90, 0, 0))
    lp = kit.empty("tub lid", tub, (0.2, -0.05, 0.0), (0, -72, -30))
    inked(kit, kit.prim("tub lid disk", 'cyl', (0.18, 0.18, 0.015), teal, lp, offset=(0, 0, 0.18), segments=20), W)
    sc = kit.empty("tub scooper", tub, (-0.05, 0.03, 0.36), (25, -20, 0))
    kit.prim("scooper bowl", 'sphere', (0.035, 0.035, 0.02), kit.mat("steel", STEEL), sc, offset=(0, 0, -0.02))
    inked(kit, kit.skin("scooper handle", [(0, 0, 0), (0, 0.0, 0.18)], [(0, 1)], [0.012, 0.014], cherry, sc, subsurf=0), W * 0.5)
    # filled pints
    for i, (x, y, c, nm) in enumerate(((0.05, -0.32, TEAL, "MINT"), (0.17, -0.38, CHERRY, "CHERRY"))):
        pp = kit.empty(f"props pint {i}", root, (x, y, 0), (0, 0, 20 + 15 * i))
        loft(kit, f"pint body {i}", [(0.0, 0.045, 0.045), (0.035, 0.047, 0.047), (0.075, 0.05, 0.05), (0.11, 0.052, 0.052)],
             [cream, kit.mat(f"pint {c}", c)], pp, n=16, subsurf=0, line=W * 0.7, mat_fn=lambda cc: 1 if 0.035 < cc.z < 0.075 else 0)
        inked(kit, kit.prim(f"pint lid {i}", 'cyl', (0.055, 0.055, 0.015), kit.mat(f"pint {c}", c), pp, offset=(0, 0, 0.115),
                            segments=16), W * 0.5)
        label(kit, pp, nm, 0.022, cream, (0, -0.05, 0.055), (90, 0, 0))
    # steel-wire milk crate with glass bottles
    mc = kit.empty("props milk crate", root, (0.78, -0.05, 0), (0, 0, -12))
    navy = kit.mat("navy", NAVY)
    kit.prim("milk crate floor", 'box', (0.34, 0.34, 0.015), navy, mc, offset=(0, 0, 0.008))
    for x in (-0.17, 0.17):
        for y in (-0.17, 0.17):
            kit.prim(f"milk crate post {x} {y}", 'box', (0.02, 0.02, 0.28), navy, mc, offset=(x, y, 0.14))
    for z in (0.12, 0.27):
        for s in (-1, 1):
            kit.prim(f"milk crate rail x {z} {s}", 'box', (0.36, 0.018, 0.02), navy, mc, offset=(0, s * 0.17, z))
            kit.prim(f"milk crate rail y {z} {s}", 'box', (0.018, 0.36, 0.02), navy, mc, offset=(s * 0.17, 0, z))
    for i in range(3):
        kit.prim(f"milk crate wire {i}", 'box', (0.008, 0.008, 0.26), navy, mc, offset=(-0.08 + i * 0.08, -0.17, 0.14))
    for i, (x, y) in enumerate(((-0.08, -0.08), (0.08, -0.08), (-0.08, 0.08), (0.08, 0.08))):
        loft(kit, f"milk bottle {i}", [(0.015, 0.06, 0.06), (0.2, 0.065, 0.065), (0.27, 0.04, 0.04), (0.33, 0.026, 0.026),
                                       (0.36, 0.028, 0.028)], [vanilla], mc, n=12, offset=(x, y, 0), line=W * 0.6)
        kit.prim(f"milk bottle cap {i}", 'cyl', (0.03, 0.03, 0.02), cherry, mc, offset=(x, y, 0.365), segments=10)
    # burlap sugar sack, slumped and tied
    sk = kit.empty("props sugar sack", root, (-0.25, -0.35, 0), (0, 0, 22))
    loft(kit, "sack body", [(0.0, 0.17, 0.12, 0, 0, 2.6), (0.06, 0.2, 0.15, 0, 0, 2.6), (0.22, 0.18, 0.13, 0.01, 0.0, 2.4, 0.01),
                            (0.34, 0.11, 0.08, 0.02, 0.01), (0.39, 0.035, 0.03, 0.03, 0.01), (0.46, 0.06, 0.04, 0.035, 0.01, 2, 0.015)],
         [kit.mat("burlap", "#dcc495")], sk, n=14, line=W)
    torus(kit, "sack tie", 0.04, 0.01, cherry, sk, (0.03, 0.01, 0.4), (0, 10, 0), seg=10, rs=4)
    label(kit, sk, "SUGAR", 0.07, navy, (0.0, -0.162, 0.15), (95, 0, 0))
    kit.prim("sack spill", 'cyl', (0.12, 0.08, 0.008), kit.mat("vanilla", VANILLA), root, offset=(-0.12, -0.55, 0.004), segments=12)
    # cocoa bag: folded paper sack
    cb = kit.empty("props cocoa bag", root, (0.55, -0.42, 0), (0, 0, 14))
    choc_paper = kit.mat("cocoa paper", "#8a5a3a")
    inked(kit, kit.prim("cocoa bag body", 'box', (0.17, 0.11, 0.24), choc_paper, cb, offset=(0, 0, 0.12), bevel=0.01), W)
    inked(kit, kit.prim("cocoa bag fold", 'box', (0.17, 0.04, 0.06), hex_and_mat(kit, "#9c6a46"), cb, offset=(0, 0.01, 0.27),
                        rot=(-12, 0, 0), bevel=0.008), W * 0.6)
    kit.prim("cocoa label", 'box', (0.13, 0.004, 0.08), cream, cb, offset=(0, -0.056, 0.12))
    label(kit, cb, "COCOA", 0.035, kit.mat("chocolate", CHOC), (0, -0.06, 0.12), (90, 0, 0))
    for i in range(10):
        kit.prim(f"props floor sprinkle {i}", 'cyl', (0.005, 0.005, 0.022), kit.mat("sprinkle " + [CHERRY, TEAL, MUSTARD, NAVY][i % 4],
                 [CHERRY, TEAL, MUSTARD, NAVY][i % 4]), root, offset=(rand.uniform(-0.2, 0.6), rand.uniform(-0.6, -0.2), 0.006),
                 rot=(90, 0, rand.uniform(0, 180)), segments=5)


def hex_and_mat(kit, h):
    return kit.mat("paper " + h, h)


def setup(scene, stage_collection):
    pass


def post(path):
    import subprocess
    subprocess.run(["magick", path, "-fill", "#5a4020", "-colorize", "6%", "-attenuate", "0.3", "+noise", "Gaussian",
                    "-background", "#7a6448", "-vignette", "0x160+-140+-140", path], check=True)
