"""Render the extra-model shots for one style: blender -b --factory-startup --python render_more.py -- <KEY> [shots]
Shots: lineup, pop, truck, arsenal, props. Writes out/<KEY>_more_<shot>.png and out/<KEY>_more_sheet.png."""
import bpy, sys, os, math, importlib, subprocess
sys.path.insert(0, "/tmp/artstyle/v2")
from mathutils import Vector
import common
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
KEY = args[0]
ALL = ["lineup", "pop", "truck", "arsenal", "props"]
SHOTS = args[1].split(",") if len(args) > 1 else ALL
OUT = os.environ.get("ART_OUT", "/tmp/artstyle/v2/out")
mod = importlib.import_module(f"style_{KEY}")

scene = bpy.context.scene
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
scene.eevee.taa_render_samples = 48
scene.eevee.use_raytracing = True
world = bpy.data.worlds.new("more world")
scene.world = world
bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs[0].default_value = common.hexc(mod.WORLD)
bg.inputs[1].default_value = 0.9


def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
cols = {k: collection(f"{KEY} {k}") for k in ALL + ["stage"]}
stage = cols["stage"]


def sun(name, rot, energy, color):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]; ld.angle = math.radians(6)
    ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
sun("key", (52, 0, -38), 3.2, "#fff4e2")
sun("rim", (60, 0, 150), 1.4, "#d8e6ff")


def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens; cd.clip_end = 300
    ob = bpy.data.objects.new(name, cd); stage.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob
cams = {
    "lineup": (camera("cam lineup", (0.3, -7.4, 1.7), (0.05, 0, 0.92), 38), (1600, 900)),
    "pop": (camera("cam pop", (12.9, -5.2, 1.9), (12.0, 0.2, 1.0), 35), (1400, 1000)),
    "truck": (camera("cam truck", (37.0, -8.2, 3.6), (30.0, 0.6, 1.4), 32), (1600, 900)),
    "arsenal": (camera("cam arsenal", (51.75, -0.3, 1.2), (50.0, -0.08, 1.07), 45), (1400, 1000)),
    "props": (camera("cam props", (61.4, -2.7, 1.45), (60.0, 0.0, 0.35), 40), (1400, 1000)),
}
fk = common.Kit(stage, getattr(mod, "SHADER", "candy"))
fm = fk.mat("floor", mod.FLOOR)
floors = {
    "lineup": fk.prim("floor lineup", 'cyl', (4.2, 4.2, 0.02), fm, offset=(0.05, 0.6, -0.01), segments=64),
    "pop": fk.prim("floor pop", 'cyl', (3.2, 3.2, 0.02), fm, offset=(12.0, 0.4, -0.01), segments=64),
    "props": fk.prim("floor props", 'cyl', (2.4, 2.4, 0.02), fm, offset=(60.0, 0.2, -0.01), segments=64),
}
if hasattr(mod, "setup"):
    mod.setup(scene, stage)


def kit_for(shot, seed):
    return mod.make_kit(cols[shot], seed=seed)

if "lineup" in SHOTS:
    k = kit_for("lineup", 11)
    mod.build_player(k, k.empty("lineup player", None, (-2.25, 0, 0), (0, 0, -6)))
    mod.build_zombie(k, k.empty("lineup walker", None, (-0.75, 0, 0), (0, 0, 10)), hit=False)
    mod.build_sprinter(k, k.empty("lineup sprinter", None, (0.75, 0, 0), (0, 0, 14)), hit=False)
    mod.build_bloater(k, k.empty("lineup bloater", None, (2.35, 0.25, 0), (0, 0, 12)), pop=False)
if "pop" in SHOTS:
    k = kit_for("pop", 12)
    mod.build_bloater(k, k.empty("pop bloater", None, (12.0, 0.4, 0), (0, 0, 8)), pop=True)
    mod.build_zombie(k, k.empty("pop walker A", None, (10.85, 0.1, 0), (0, 0, -40)), hit=True)
    mod.build_sprinter(k, k.empty("pop sprinter B", None, (13.15, 0.0, 0), (0, 0, 48)), hit=True)
if "truck" in SHOTS:
    k = kit_for("truck", 13)
    mod.build_truck(k, k.empty("truck root", None, (30.0, 0, 0)))
if "arsenal" in SHOTS:
    k = kit_for("arsenal", 14)
    mod.build_gun(k, k.empty("arsenal pistol", None, (50.0, -0.2, 1.33)))
    mod.build_shotgun(k, k.empty("arsenal shotgun", None, (50.0, 0.0, 0.95)))
if "props" in SHOTS:
    k = kit_for("props", 15)
    mod.build_props(k, k.empty("props root", None, (60.0, 0, 0)))

for shot in SHOTS:
    for name, c in cols.items():
        if name != "stage":
            c.hide_render = name != shot
    for name, f in floors.items():
        f.hide_render = name != shot
    cam, res = cams[shot]
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    path = f"{OUT}/{KEY}_more_{shot}.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if hasattr(mod, "post"):
        mod.post(path)
if SHOTS == ALL:
    p = lambda s: f"{OUT}/{KEY}_more_{s}.png"
    subprocess.run(["magick", "(", p("lineup"), p("truck"), "+append", ")",
                    "(", p("pop"), p("arsenal"), p("props"), "-resize", "x900", "+append", ")",
                    "-resize", "3200x", "-append", "-resize", "2400x", f"{OUT}/{KEY}_more_sheet.png"], check=True)
print("RENDER_DONE", KEY)
