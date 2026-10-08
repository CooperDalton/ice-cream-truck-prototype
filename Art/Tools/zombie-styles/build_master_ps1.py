"""Add the PS1 (style H) game asset library to the master .blend, one collection per asset."""
import bpy, sys, math, importlib
sys.path.insert(0, "/tmp/artstyle/v2")
import common
import style_H as H

ROOT = "T • PS1 game assets"
BATCHES = [("h_core", "Zombies"), ("h_characters", "Characters"), ("h_weapons", "Weapons"), ("h_items", "Items"),
           ("h_truck", "Truck and kitchen"), ("h_fx", "FX"), ("h_road", "Road and town"), ("h_stops", "Supply stops and depot")]
MAIN = bpy.data.scenes["Ice cream truck workshop"]
if ROOT in bpy.data.collections:
    raise SystemExit("already built")
root = bpy.data.collections.new(ROOT)
MAIN.collection.children.link(root)
scene = bpy.data.scenes.new("PS1 game assets")
scene.collection.children.link(root)
scene.render.engine = 'BLENDER_EEVEE'
scene.view_settings.view_transform = 'Standard'
world = bpy.data.worlds.new("PS1 game assets world")
scene.world = world
bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
bg.inputs[0].default_value = common.hexc(H.WORLD)
stage = bpy.data.collections.new("T • PS1 review lights")
scene.collection.children.link(stage)
for name, rot, energy, color in (("PS1 key", (52, 0, -38), 3.2, "#fff4e2"), ("PS1 rim", (60, 0, 150), 1.4, "#d8e6ff")):
    ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]
    ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
H.setup(scene, stage)

y = 0.0
for b, (modname, title) in enumerate(BATCHES):
    mod = importlib.import_module(modname)
    spacing = getattr(mod, "SPACING", 12)
    batch = bpy.data.collections.new(f"T{b + 1} {title}")
    root.children.link(batch)
    for i, (name, fn) in enumerate(mod.ASSETS):
        col = bpy.data.collections.new(f"T{b + 1} {title} / {name}")
        batch.children.link(col)
        kit = H.make_kit(col, seed=100 + i)
        fn(kit, kit.empty(f"{name} root", None, (700 + i * spacing, y, 0)))
    print("BUILT", title, len(mod.ASSETS), len(batch.all_objects))
    y -= max(spacing, 10) + 15
bpy.ops.wm.save_mainfile()
