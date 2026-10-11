"""Add the hot spots, Kevin's shop and the new gear (cones, guns, ingredients, flavors, fuel parts) to the PS1 game assets
in the master .blend as batch T10, and rebuild the master's Ice Cream Truck in place so it carries the fuel intake.
    blender -b "Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend" --python add_gameplay_master.py"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_H as H
import h_hotspots, h_shop, h_weapons, h_items, h_truck

ROOT = "T • PS1 game assets"
TITLE = "T10 Hot spots, shop and new gear"
NEW_GEAR = {
    h_weapons: ["Plain Cone", "Waffle Cone", "Double Dip", "Soft Serve Hose", "Sundae Bazooka", "Jackpot Blaster"],
    h_items: ["Coffee Sack", "Nut Bag"] + [f"{kind} {flavor}{suffix}" for kind, suffix in (("Pint", " Full"), ("Scoop Grenade", ""), ("Flavor Tub", ""))
                                           for flavor in ("Coffee", "Rocky Road", "Neapolitan")],
    h_truck: ["Fuel Intake", "Upgrade Sundae Tank"],
}


def entries(module):
    """(seed index, name, builder) for every asset of a module, numbered the way export_unity.py seeds them."""
    return [(i, name, fn) for i, (name, fn) in enumerate(module.ASSETS)]


def build(index, name, fn, col, location):
    kit = H.make_kit(col, seed=100 + index)
    fn(kit, kit.empty(f"{name} root", None, location))


root = bpy.data.collections[ROOT]
if TITLE in bpy.data.collections:
    raise SystemExit("already added")

# Rebuild the truck where it stands.
truck_col = next(c for c in root.children_recursive if c.name.endswith("/ Ice Cream Truck"))
truck_root = bpy.data.objects["Ice Cream Truck root"]
location = truck_root.matrix_world.translation.copy()
for ob in list(truck_col.all_objects):
    bpy.data.objects.remove(ob, do_unlink=True)
index, name, fn = next(e for e in entries(h_truck) if e[1] == "Ice Cream Truck")
build(index, name, fn, truck_col, location)
print("REBUILT", name, len(truck_col.all_objects))

y = min(ob.matrix_world.translation.y for ob in root.all_objects) - 40
batch = bpy.data.collections.new(TITLE)
root.children.link(batch)
x = 700
for module in (h_hotspots, h_shop):
    for index, name, fn in entries(module):
        col = bpy.data.collections.new(f"{TITLE} / {name}")
        batch.children.link(col)
        build(index, name, fn, col, (x, y, 0))
        x += module.SPACING
for module, names in NEW_GEAR.items():
    for index, name, fn in entries(module):
        if name not in names:
            continue
        col = bpy.data.collections.new(f"{TITLE} / {name}")
        batch.children.link(col)
        build(index, name, fn, col, (x, y, 0))
        x += 2.5
print("BUILT", TITLE, len(batch.all_objects), "at y", round(y, 1))
bpy.ops.wm.save_mainfile()
