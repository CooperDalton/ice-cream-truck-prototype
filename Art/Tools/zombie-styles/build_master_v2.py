"""Replace the v1 art style mockups in the master .blend with the v2 per-style designs."""
import bpy, sys, math, importlib
sys.path.insert(0, "/tmp/artstyle/v2")
sys.path.insert(0, "/tmp/artstyle")
from mathutils import Vector
import common
import build_styles as v1

KEYS = "ABCDEFGHIJ"
ROOT = "S • Zombie demo art styles v2"
MAIN = bpy.data.scenes["Ice cream truck workshop"]

v1.cleanup()
old = bpy.data.collections.get(ROOT)
if old:
    raise SystemExit("v2 already present")
for sc in [s for s in bpy.data.scenes if s.name.startswith("Zombie demo v2 - ")]:
    bpy.data.scenes.remove(sc)

root = bpy.data.collections.new(ROOT)
MAIN.collection.children.link(root)


def collection(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


for i, key in enumerate(KEYS):
    mod = importlib.import_module(f"style_{key}")
    base = Vector((500 + i * 8, 0, 0))
    style = collection(f"S{i + 1} {mod.LABEL}", root)
    cols = {k: collection(f"S{i + 1} {mod.LABEL} / {k.title()}", style) for k in ("characters", "gun", "impact")}
    scene = bpy.data.scenes.new(f"Zombie demo v2 - {mod.LABEL}")
    scene.collection.children.link(style)
    stage = collection(f"S{i + 1} {mod.LABEL} / Review stage", scene.collection)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.view_settings.view_transform = 'Standard'
    scene.eevee.taa_render_samples = 48
    scene.eevee.use_raytracing = True
    world = bpy.data.worlds.new(f"Zombie demo v2 world {key}")
    scene.world = world
    bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = common.hexc(mod.WORLD)
    bg.inputs[1].default_value = 0.9

    def sun(name, rot, energy, color):
        ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]; ld.angle = math.radians(6)
        ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
    sun(f"{key} key", (52, 0, -38), 3.2, "#fff4e2")
    sun(f"{key} rim", (60, 0, 150), 1.4, "#d8e6ff")

    def camera(name, loc, target, lens):
        cd = bpy.data.cameras.new(name); cd.lens = lens
        ob = bpy.data.objects.new(name, cd); stage.objects.link(ob); ob.location = loc
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    camera(f"CAM {key} characters", (1.9, -4.4, 1.45), (0.05, 0, 0.8), 42)
    camera(f"CAM {key} gun", (2.92, -0.7, 1.3), (2.3, -0.445, 1.11), 50)
    camera(f"CAM {key} impact", (1.7, -0.5, 1.3), (0.6, 3.4, 1.0), 42)
    fk = common.Kit(stage, getattr(mod, "SHADER", "candy"))
    fm = fk.mat(f"{key} floor", mod.FLOOR)
    fk.prim(f"{key} floor characters", 'cyl', (2.3, 2.3, 0.02), fm, offset=(0.05, 0, -0.01), segments=64)
    fk.prim(f"{key} floor impact", 'cyl', (1.6, 1.6, 0.02), fm, offset=(0.4, 3.4, -0.01), segments=64)
    if hasattr(mod, "setup"):
        mod.setup(scene, stage)
    scene.camera = bpy.data.objects[f"CAM {key} characters"]

    kit = mod.make_kit(cols["characters"], seed=1)
    mod.build_player(kit, kit.empty(f"{key} player root", None, (-0.7, 0, 0), (0, 0, -8)))
    mod.build_zombie(kit, kit.empty(f"{key} zombie root", None, (0.8, 0, 0), (0, 0, 22)), hit=False)
    kit = mod.make_kit(cols["gun"], seed=2)
    mod.build_gun(kit, kit.empty(f"{key} gun root", None, (2.3, -0.4, 1.1)))
    kit = mod.make_kit(cols["impact"], seed=3)
    mod.build_zombie(kit, kit.empty(f"{key} impact zombie root", None, (0.2, 3.4, 0), (0, 0, 30)), hit=True)

    anchor = bpy.data.objects.new(f"{key} style anchor", None)
    style.objects.link(anchor)
    anchor.location = base
    for c in list(cols.values()) + [stage]:
        for ob in c.all_objects:
            if ob.parent is None and ob is not anchor:
                ob.parent = anchor
    print("BUILT", key, mod.LABEL, len(style.all_objects))

bpy.ops.wm.save_mainfile()
