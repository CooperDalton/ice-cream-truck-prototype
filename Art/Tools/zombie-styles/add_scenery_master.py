"""Add the scenery batch (h_scenery) to the PS1 game assets in the master .blend, below the existing batches.
    blender -b "Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend" --python add_scenery_master.py"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_H as H
import h_scenery

ROOT = "T • PS1 game assets"
TITLE = "T9 Scenery, blocks and road dressing"
root = bpy.data.collections[ROOT]
if TITLE in bpy.data.collections:
    raise SystemExit("already added")
y = min(ob.matrix_world.translation.y for ob in root.all_objects) - 40
batch = bpy.data.collections.new(TITLE)
root.children.link(batch)
for i, (name, fn) in enumerate(h_scenery.ASSETS):
    col = bpy.data.collections.new(f"{TITLE} / {name}")
    batch.children.link(col)
    kit = H.make_kit(col, seed=100 + i)
    fn(kit, kit.empty(f"{name} root", None, (700 + i * h_scenery.SPACING, y, 0)))
print("BUILT", TITLE, len(h_scenery.ASSETS), len(batch.all_objects), "at y", round(y, 1))
bpy.ops.wm.save_mainfile()
