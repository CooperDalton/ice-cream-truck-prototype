"""Render a PS1 (style H) asset batch: blender -b --factory-startup --python render_assets.py -- <module> [name,name]
The module defines ASSETS = [(name, build_fn)] (build_fn(kit, root)), optional SPACING (m between asset roots,
default 12) and optional SCENES = [dict(name=, build=fn(kit, root), cam=((x,y,z), (tx,ty,tz), lens), res=(w, h))]
with camera coordinates relative to the scene root. Each asset gets an auto-framed close-up; everything lands in
out/assets/<module>/ plus a labeled contact sheet <module>_sheet.png."""
import bpy, sys, os, math, importlib, subprocess, re
sys.path.insert(0, "/tmp/artstyle/v2")
from mathutils import Vector
import common
import style_H as H

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
MODNAME = args[0]
ONLY = set(args[1].split(",")) if len(args) > 1 else None
mod = importlib.import_module(MODNAME)
OUT = f"/tmp/artstyle/v2/out/assets/{MODNAME}"
os.makedirs(OUT, exist_ok=True)
slug = lambda s: re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")

scene = bpy.context.scene
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
scene.eevee.taa_render_samples = 32
scene.eevee.use_raytracing = True
world = bpy.data.worlds.new("assets world")
scene.world = world
bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs[0].default_value = common.hexc(H.WORLD)
bg.inputs[1].default_value = 0.9
stage = bpy.data.collections.new("stage")
scene.collection.children.link(stage)
for name, rot, energy, color in (("key", (52, 0, -38), 3.2, "#fff4e2"), ("rim", (60, 0, 150), 1.4, "#d8e6ff")):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]; ld.angle = math.radians(6)
    ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
H.setup(scene, stage)
fk = common.Kit(stage, H.SHADER)
floor_mat = fk.mat("floor", H.FLOOR)
cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
stage.objects.link(cam)
scene.camera = cam


def look(loc, target, lens):
    cam_data.lens = lens
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    cam_data.clip_end = max(200, (Vector(target) - Vector(loc)).length * 6)


jobs = []   # (label, collection, kind, data)
spacing = getattr(mod, "SPACING", 12)
for i, (name, fn) in enumerate(mod.ASSETS):
    if ONLY and slug(name) not in ONLY and name not in ONLY:
        continue
    col = bpy.data.collections.new(f"asset {name}")
    scene.collection.children.link(col)
    kit = H.make_kit(col, seed=100 + i)
    fn(kit, kit.empty(f"{name} root", None, (i * spacing, 0, 0)))
    jobs.append((f"{i:02d}_{slug(name)}", name, col, None))
for j, sc in enumerate(getattr(mod, "SCENES", [])):
    if ONLY and sc["name"] not in ONLY and slug(sc["name"]) not in ONLY:
        continue
    col = bpy.data.collections.new(f"scene {sc['name']}")
    scene.collection.children.link(col)
    kit = H.make_kit(col, seed=500 + j)
    base = Vector((0, -300 - j * 150, 0))
    sc["build"](kit, kit.empty(f"{sc['name']} root", None, tuple(base)))
    jobs.append((f"scene_{slug(sc['name'])}", sc["name"], col, (sc, base)))

bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()
floor = fk.prim("floor", 'cyl', (1, 1, 0.02), floor_mat, offset=(0, 0, -0.01), segments=48)
labels = []
for fname, label, col, scdata in jobs:
    for c in scene.collection.children:
        if c is not stage:
            c.hide_render = c is not col
    if scdata is None:
        pts = []
        for ob in col.all_objects:
            if ob.type in {'MESH', 'CURVE', 'FONT', 'META'}:
                ev = ob.evaluated_get(dg)
                pts += [ob.matrix_world @ Vector(c) for c in ev.bound_box]
        lo = Vector([min(p[k] for p in pts) for k in range(3)])
        hi = Vector([max(p[k] for p in pts) for k in range(3)])
        c = (lo + hi) / 2
        r = max((hi - lo).length / 2, 0.05)
        d = r / math.sin(math.atan(18 / 50)) * 1.08
        look(c + Vector((0.62, -0.72, 0.34)).normalized() * d, c, 50)
        floor.hide_render = lo.z > 0.15
        floor.location = (c.x, c.y, min(lo.z, 0))
        floor.scale = (r * 1.7, r * 1.7, 1)
        scene.render.resolution_x = scene.render.resolution_y = 900
        size = hi - lo
        tris = 0
        for ob in col.all_objects:
            if ob.type == 'MESH':
                me = ob.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); tris += len(me.loop_triangles)
                ob.evaluated_get(dg).to_mesh_clear()
        print(f"ASSET {label}: {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m, {tris} tris")
    else:
        sc, base = scdata
        loc, target, lens = sc["cam"]
        look(base + Vector(loc), base + Vector(target), lens)
        floor.hide_render = True
        scene.render.resolution_x, scene.render.resolution_y = sc.get("res", (1600, 900))
    path = f"{OUT}/{fname}.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    H.post(path)
    labels.append((path, label))
if labels and not ONLY:
    cmd = ["montage"]
    for path, label in labels:
        cmd += ["-label", label, path]
    cmd += ["-font", "Adwaita-Mono-Bold", "-pointsize", "28", "-fill", "#fff7ee", "-background", "#1b1033",
            "-tile", "4x", "-geometry", "560x560+8+8", f"/tmp/artstyle/v2/out/assets/{MODNAME}_sheet.png"]
    subprocess.run(cmd, check=True)
print("RENDER_DONE", MODNAME)
