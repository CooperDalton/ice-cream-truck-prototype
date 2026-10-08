"""Check exported FBX files against manifest.json.

    blender -b --factory-startup --python check_unity_export.py -- "Walker,Ice Cream Truck,..."   (no names = all)

unity - reads the FBX node transforms and vertices directly and applies Unity's conversion for a Y-up file (mirror X,
        T_unity = F T F). Checks the single top-level node is identity, then triangles, bounds and every empty's
        position/forward/up against the manifest.
back  - fresh Blender, default FBX import: geometry must land where it was built (front along -Y) and every material
        must resolve its PNG on disk.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix, Euler
from io_scene_fbx import parse_fbx

HERE = os.path.dirname(os.path.abspath(__file__))
UNITY_PROJECT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "Zombie Ice Cream Truck"))
manifest = json.load(open(os.path.join(UNITY_PROJECT, "Assets/Art/PS1/manifest.json")))["assets"]
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
names = args[0].split(",") if args else list(manifest)
TOL = 2e-3
F = Matrix.Diagonal((-1, 1, 1, 1))


def elems(e, key):
    return [c for c in e.elems if c.id == key]


def props70(e):
    block = elems(e, b"Properties70")
    return {p.props[0].decode(): p.props[4:] for p in elems(block[0], b"P")} if block else {}


def unity_view(path):
    """(top-level node names, top local matrix, {node name: Unity world matrix}, Unity-space vertices, triangles)."""
    root, _ = parse_fbx.parse(path)
    objs = elems(root, b"Objects")[0]
    models = {m.props[0]: m for m in elems(objs, b"Model")}
    geoms = {g.props[0]: g for g in elems(objs, b"Geometry")}
    parent, geom_of = {}, {}
    for c in elems(elems(root, b"Connections")[0], b"C"):
        if c.props[0] == b"OO" and c.props[1] in models:
            parent[c.props[1]] = c.props[2]
        if c.props[0] == b"OO" and c.props[1] in geoms and c.props[2] in models:
            geom_of[c.props[2]] = c.props[1]

    def local(mid):
        p = props70(models[mid])
        extra = set(p) & {"PreRotation", "PostRotation", "RotationPivot", "ScalingPivot", "RotationOffset",
                          "ScalingOffset", "GeometricTranslation", "GeometricRotation", "GeometricScaling"}
        assert not extra, f"unhandled FBX transform properties {extra}"
        rot = Euler([math.radians(a) for a in p.get("Lcl Rotation", (0, 0, 0))], 'XYZ').to_matrix().to_4x4()
        return (Matrix.Translation(p.get("Lcl Translation", (0, 0, 0))) @ rot
                @ Matrix.Diagonal((*p.get("Lcl Scaling", (1, 1, 1)), 1)))

    def world(mid):
        w = local(mid)
        while parent.get(mid, 0) != 0:
            mid = parent[mid]
            w = local(mid) @ w
        return F @ w @ F

    label = lambda mid: models[mid].props[1].split(b"\x00")[0].decode()
    tops = [mid for mid in models if parent.get(mid, 0) == 0]
    pts, tris = [], 0
    for mid, gid in geom_of.items():
        w = np.array(world(mid))
        v = np.array(elems(geoms[gid], b"Vertices")[0].props[0]).reshape(-1, 3) * (-1, 1, 1)
        tris += int((np.array(elems(geoms[gid], b"PolygonVertexIndex")[0].props[0]) < 0).sum())
        pts.append(v @ w[:3, :3].T + w[:3, 3])
    return [label(m) for m in tops], local(tops[0]), {label(m): world(m) for m in models}, np.concatenate(pts), tris


def blender_bounds(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    bpy.context.view_layer.update()
    pts, missing = [], []
    for ob in bpy.context.scene.objects:
        if ob.type == 'MESH':
            pts += [ob.matrix_world @ v.co for v in ob.data.vertices]
            for slot in ob.material_slots:
                img = next(n.image for n in slot.material.node_tree.nodes if n.type == 'TEX_IMAGE')
                if not os.path.exists(bpy.path.abspath(img.filepath)):
                    missing.append(img.filepath)
    pts = np.array([(-p.x, p.z, -p.y) for p in pts])
    return pts.min(axis=0), pts.max(axis=0), sorted(set(missing))


def off(a, b):
    return float(np.abs(np.asarray(a) - np.asarray(b)).max())


failures = 0
for name in names:
    entry = manifest[name]
    path = os.path.join(UNITY_PROJECT, entry["fbx"])
    problems = []
    tops, top_local, worlds, pts, tris = unity_view(path)
    if tops != [f"{name} root"]:
        problems.append(f"top-level nodes {tops}")
    if off(top_local, Matrix.Identity(4)) > 1e-5:
        problems.append(f"root transform is not identity: {top_local}")
    if tris != entry["triangles"]:
        problems.append(f"triangles {tris} != {entry['triangles']}")
    if off(pts.min(axis=0), entry["boundsMin"]) > TOL or off(pts.max(axis=0), entry["boundsMax"]) > TOL:
        problems.append(f"unity bounds {pts.min(axis=0).round(3)} {pts.max(axis=0).round(3)}")
    worst = 0.0
    for e in entry["empties"]:
        w = worlds[e["name"]]
        rot = w.to_3x3()
        worst = max(worst, off(w.translation, e["position"]), off((rot @ Vector((0, 0, 1))).normalized(), e["forward"]),
                    off((rot @ Vector((0, 1, 0))).normalized(), e["up"]))
    if worst > 5e-3:
        problems.append(f"empties off by up to {worst:.4f}")
    lo, hi, missing = blender_bounds(path)
    if off(lo, entry["boundsMin"]) > TOL or off(hi, entry["boundsMax"]) > TOL:
        problems.append(f"blender round-trip bounds {lo.round(3)} {hi.round(3)}")
    if missing:
        problems.append(f"missing textures {missing[:3]}")
    failures += bool(problems)
    size = np.subtract(entry["boundsMax"], entry["boundsMin"])
    print(f"CHECK {name}: {'OK' if not problems else 'FAIL'} | {len(worlds)} nodes, {tris} tris, "
          f"{len(entry['empties'])} empties, size x{size[0]:.2f} y{size[1]:.2f} z{size[2]:.2f} m")
    for p in problems:
        print("   ", p)
print(f"CHECK_DONE {len(names) - failures}/{len(names)} ok")
