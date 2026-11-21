"""Add the heist pitch models (kids and crew poses, cops and NPCs, police car and harbor, diamond and town line props)
to the PS1 game assets in the master .blend as batch T11.
    blender -b "Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend" --python add_pitch_master.py"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_H as H
import h_kids, h_cops, h_vehicles, h_heist

ROOT = "T • PS1 game assets"
TITLE = "T11 Heist pitch"

root = bpy.data.collections[ROOT]
if TITLE in bpy.data.collections:
    raise SystemExit("already added")

y = min(ob.matrix_world.translation.y for ob in root.all_objects) - 40
batch = bpy.data.collections.new(TITLE)
root.children.link(batch)
x = 700
for module in (h_kids, h_cops, h_vehicles, h_heist):
    for index, (name, fn) in enumerate(module.ASSETS):
        col = bpy.data.collections.new(f"{TITLE} / {name}")
        batch.children.link(col)
        kit = H.make_kit(col, seed=100 + index)
        fn(kit, kit.empty(f"{name} root", None, (x, y, 0)))
        x += module.SPACING
print("BUILT", TITLE, len(batch.all_objects), "at y", round(y, 1))
bpy.ops.wm.save_mainfile()
