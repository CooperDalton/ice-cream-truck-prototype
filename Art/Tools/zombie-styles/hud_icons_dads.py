"""Render the Divorced Dads HUD item icons from the PS1 (style H) models, the same way hud_icons.py does for the zombie
mode: blender -b --factory-startup --python hud_icons_dads.py -- [name,name]

Each icon is the real model (built like export_unity.py, seed 100 + its index in the module's ASSETS) shot with an
orthographic camera on a transparent background at 64 x 64, then given hard alpha and a 1 px ink outline with
ImageMagick. Output: Zombie Ice Cream Truck/Assets/Art/Sprites/DadsIcons/<icon>.png."""
import bpy, sys, os, math, importlib, subprocess
from mathutils import Vector, Quaternion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import common
import style_H as H

OUT = os.path.join(HERE, "../../../Zombie Ice Cream Truck/Assets/Art/Sprites/DadsIcons")
SIZE = 64
SIDE = (1.0, -0.38, 0.32)       # guns: side profile from +X, barrel to the left
LONG = (1.0, -0.38, 0.32, 32)  # long guns: same view rolled so the barrel runs corner to corner
THREE_Q = (0.62, -0.72, 0.5)   # everything else: front-right, from above

# icon file name -> (module, asset name, view direction (x, y, z[, camera roll in degrees]))
ICONS = {
    "Cone": ("h_dads_items", "Cone", THREE_Q),
    "WaffleCone": ("h_dads_items", "Waffle Cone", THREE_Q),
    "DoubleWaffleCone": ("h_dads_items", "Double Waffle Cone", THREE_Q),
    "ScoopPistol": ("h_weapons", "Scoop Pistol", SIDE),
    "SundaeShotgun": ("h_weapons", "Sundae Shotgun", LONG),
    "Minigun": ("h_weapons", "Soft Serve Minigun", SIDE),
    "MudBucket": ("h_dads_items", "Mud Bucket", THREE_Q),
    "StrawberryBasket": ("h_items", "Strawberry Basket", THREE_Q),
    "IcedCoffee": ("h_dads_items", "Iced Coffee", THREE_Q),
    "NutSack": ("h_dads_items", "Nut Sack", THREE_Q),
    "GoldLeaf": ("h_dads_items", "Gold Leaf", THREE_Q),
    "LunchMoney": ("h_dads_items", "Lunch Money", (0.3, -1.0, 0.6)),
}
for flavor in ("Mud", "Strawberry", "Coffee", "Rocky Road", "Gold Leaf"):
    key = flavor.replace(" ", "")
    ICONS[f"Scoop{key}"] = ("h_dads_items", f"Scoop {flavor}", THREE_Q)
    ICONS[f"Tub{key}"] = ("h_dads_items", f"Flavor Tub {flavor}", THREE_Q)

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = set(args[0].split(",")) if args else None


def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.view_settings.view_transform = 'Standard'
    scene.eevee.taa_render_samples = 16
    scene.render.film_transparent = True
    scene.render.filter_size = 0.6
    scene.render.resolution_x = scene.render.resolution_y = SIZE
    scene.render.image_settings.color_mode = 'RGBA'
    world = bpy.data.worlds.new("icons")
    scene.world = world
    bg = world.node_tree.nodes.get("Background") or world.node_tree.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = common.hexc(H.WORLD)
    bg.inputs[1].default_value = 0.9
    stage = bpy.data.collections.new("stage")
    scene.collection.children.link(stage)
    for name, rot, energy, color in (("key", (52, 0, -38), 3.2, "#fff4e2"), ("rim", (60, 0, 150), 1.4, "#d8e6ff")):
        ld = bpy.data.lights.new(name, 'SUN'); ld.energy = energy; ld.color = common.hexc(color)[:3]
        ob = bpy.data.objects.new(name, ld); stage.objects.link(ob); ob.rotation_euler = [math.radians(a) for a in rot]
    cam_data = bpy.data.cameras.new("cam")
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new("cam", cam_data)
    stage.objects.link(cam)
    scene.camera = cam
    return scene, cam


def render_icon(scene, cam, icon, module, asset, view):
    mod = importlib.import_module(module)
    index, fn = next((i, f) for i, (n, f) in enumerate(mod.ASSETS) if n == asset)
    col = bpy.data.collections.new(f"icon {icon}")
    scene.collection.children.link(col)
    kit = H.make_kit(col, seed=100 + index)
    fn(kit, kit.empty(f"{asset} root", None, (0, 0, 0)))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts = [ob.matrix_world @ Vector(c) for ob in col.all_objects if ob.type in {'MESH', 'CURVE', 'FONT', 'META'}
           for c in ob.evaluated_get(dg).bound_box]
    center = sum(pts, Vector()) / len(pts)
    d = Vector(view[:3]).normalized()
    roll = math.radians(view[3]) if len(view) > 3 else 0.0
    cam.location = center + d * 10
    cam.rotation_euler = ((-d).to_track_quat('-Z', 'Y') @ Quaternion((0, 0, 1), roll)).to_euler()
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    local = [inv @ p for p in pts]
    w = max(p.x for p in local) - min(p.x for p in local)
    h = max(p.y for p in local) - min(p.y for p in local)
    mid = Vector(((max(p.x for p in local) + min(p.x for p in local)) / 2, (max(p.y for p in local) + min(p.y for p in local)) / 2, 0))
    cam.location = cam.matrix_world @ mid
    cam.data.ortho_scale = max(w, h) * 1.12
    cam.data.clip_end = 100
    path = os.path.join(OUT, f"{icon}.png")
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    # Hard pixel edges and a 1 px ink outline so icons read on any background.
    subprocess.run(["magick", path, "-channel", "A", "-threshold", "45%", "+channel",
                    "(", "+clone", "-alpha", "extract", "-morphology", "Dilate", "Square:1",
                    "-background", H.INK, "-alpha", "shape", ")", "+swap", "-background", "none", "-flatten", path], check=True)
    bpy.data.collections.remove(col)
    for ob in list(bpy.data.objects):
        if ob.users_collection == () or not ob.users_collection:
            bpy.data.objects.remove(ob)
    print("ICON", icon)


def main():
    os.makedirs(OUT, exist_ok=True)
    scene, cam = setup_scene()
    for icon, (module, asset, view) in ICONS.items():
        if ONLY and icon not in ONLY:
            continue
        render_icon(scene, cam, icon, module, asset, view)
    print("ICONS_DONE")


main()
