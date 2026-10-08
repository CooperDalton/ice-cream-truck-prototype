"""Render one style module: blender -b --factory-startup --python render_v2.py -- <KEY> [shots]
Writes /tmp/artstyle/v2/out/<KEY>_characters.png, <KEY>_gun.png, <KEY>_impact.png and <KEY>_sheet.png."""
import bpy, sys, os, math, importlib, subprocess
sys.path.insert(0, "/tmp/artstyle/v2")
from mathutils import Vector
import common
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
KEY = args[0]
SHOTS = args[1].split(",") if len(args) > 1 else ["characters", "gun", "impact"]
OUT = os.environ.get("ART_OUT", "/tmp/artstyle/v2/out")
mod = importlib.import_module(f"style_{KEY}")

scene = bpy.context.scene
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
scene.eevee.taa_render_samples = 48
if hasattr(scene.eevee, "use_raytracing"):
    scene.eevee.use_raytracing = True
world = bpy.data.worlds.new("v2 world")
scene.world = world
bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs[0].default_value = common.hexc(mod.WORLD)
bg.inputs[1].default_value = 0.9

def collection(name):
    c = bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c
cols = {k: collection(f"{KEY} {k}") for k in ("characters", "gun", "impact", "stage")}
stage = cols["stage"]

def sun(name, rot, energy, color):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]; ld.angle = math.radians(6)
    ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
sun("key", (52, 0, -38), 3.2, "#fff4e2")
sun("rim", (60, 0, 150), 1.4, "#d8e6ff")

def camera(name, loc, target, lens):
    cd = bpy.data.cameras.new(name); cd.lens = lens
    ob = bpy.data.objects.new(name, cd); stage.objects.link(ob); ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return ob
cams = {
    "characters": camera("cam characters", (1.9, -4.4, 1.45), (0.05, 0, 0.8), 42),
    "gun": camera("cam gun", (2.92, -0.7, 1.3), (2.3, -0.445, 1.11), 50),
    "impact": camera("cam impact", (1.7, -0.5, 1.3), (0.6, 3.4, 1.0), 42),
}
floor_kit = common.Kit(stage, getattr(mod, "SHADER", "candy"))
floor_mat = floor_kit.mat("floor", mod.FLOOR)
floors = {
    "characters": floor_kit.prim("floor characters", 'cyl', (2.3, 2.3, 0.02), floor_mat, offset=(0.05, 0, -0.01), segments=64),
    "impact": floor_kit.prim("floor impact", 'cyl', (1.6, 1.6, 0.02), floor_mat, offset=(0.4, 3.4, -0.01), segments=64),
}
if hasattr(mod, "setup"):
    mod.setup(scene, stage)

kit = mod.make_kit(cols["characters"], seed=1)
mod.build_player(kit, kit.empty("player root", None, (-0.7, 0, 0), (0, 0, -8)))
mod.build_zombie(kit, kit.empty("zombie root", None, (0.8, 0, 0), (0, 0, 22)), hit=False)
kit = mod.make_kit(cols["gun"], seed=2)
mod.build_gun(kit, kit.empty("gun root", None, (2.3, -0.4, 1.1)))
kit = mod.make_kit(cols["impact"], seed=3)
mod.build_zombie(kit, kit.empty("impact zombie root", None, (0.2, 3.4, 0), (0, 0, 30)), hit=True)

for shot in SHOTS:
    for name, c in cols.items():
        if name != "stage":
            c.hide_render = name != shot
    for name, f in floors.items():
        f.hide_render = name != shot
    scene.camera = cams[shot]
    scene.render.resolution_x, scene.render.resolution_y = (1000, 1000) if shot == "gun" else (1400, 1000)
    path = f"{OUT}/{KEY}_{shot}.png"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if hasattr(mod, "post"):
        mod.post(path)
if SHOTS == ["characters", "gun", "impact"]:
    subprocess.run(["magick", f"{OUT}/{KEY}_characters.png", f"{OUT}/{KEY}_impact.png", "(", f"{OUT}/{KEY}_gun.png",
                    "-resize", "x1000", ")", "+append", "-resize", "2400x", f"{OUT}/{KEY}_sheet.png"], check=True)
print("RENDER_DONE", KEY)
