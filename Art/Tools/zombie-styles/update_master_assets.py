"""Rebuild assets that are already in the master .blend where they stand, after their builder changed.
    blender -b "Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend" --python update_master_assets.py -- "Ice Cream Truck,Fuel Intake"
Each asset lives in a collection named "<batch> / <asset name>" with its root empty "<asset name> root"; it is rebuilt with
the same seed export_unity.py uses (100 + its index in its module's ASSETS)."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib
import style_H as H

MODULES = ["h_core", "h_characters", "h_weapons", "h_items", "h_truck", "h_road", "h_stops", "h_fx", "h_scenery", "h_hotspots", "h_shop"]
names = sys.argv[sys.argv.index("--") + 1].split(",")
root = bpy.data.collections["T • PS1 game assets"]
for name in names:
    module, index, fn = next((m, i, f) for m in map(importlib.import_module, MODULES) for i, (n, f) in enumerate(m.ASSETS) if n == name)
    collection = next(c for c in root.children_recursive if c.name.endswith(f"/ {name}"))
    location = bpy.data.objects[f"{name} root"].matrix_world.translation.copy()
    for ob in list(collection.all_objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    kit = H.make_kit(collection, seed=100 + index)
    fn(kit, kit.empty(f"{name} root", None, location))
    print("REBUILT", name, "from", module.__name__, len(collection.all_objects), "objects")
bpy.ops.wm.save_mainfile()
