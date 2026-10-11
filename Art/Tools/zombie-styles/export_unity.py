"""Export the PS1 (style H) asset library to the Zombie Ice Cream Truck Unity project.

    blender -b --factory-startup --python export_unity.py -- [filter]

filter: optional comma-separated asset names, slugs or module names (h_core, ...). Each asset is built alone at the
origin (seed 100 + its index in the module's ASSETS, like render_assets.py) and written as
Assets/Art/PS1/<Category>/<Asset Name>.fbx with its textures as PNGs in <Category>/Textures/. Assets/Art/PS1/manifest.json
gets bounds and every pivot/socket empty in Unity coordinates (entries for unfiltered assets are kept).

Axis mapping (Blender Z up, assets face -Y -> Unity Y up, +Z forward, left-handed):
    unity = (-blender.x, blender.z, -blender.y)
FBX settings: axis_forward -Z, axis_up Y, FBX_SCALE_UNITS (UnitScaleFactor 100 = meters, Unity file scale 1).
The exporter's bake_space_transform is not used: it computes wrong local matrices for children of rotated pivots
deeper than one level (fbx_utils.fbx_object_matrix). convert_space() does the same job correctly: every object's
local matrix L becomes G L G^-1 and mesh data G v (G = the exporter's axis conversion), and the root gets G^-1 so
the exporter's own G on top-level objects cancels. The FBX root node is then identity and every node's local +Z is
the Blender local -Y (Unity Transform.forward), local +Y is Blender local +Z (Transform.up).

Texture/material name tags read by PS1ArtPostprocessor.cs:
    texture "... __repeat.png"  sampled with REPEAT in Blender -> Wrap Repeat (otherwise Clamp)
    material "... __clip"       texture alpha is only 0/1 (sprites, decals, cut fences) -> alpha clip, two-sided
    material "... __blend"      texture alpha has partial values (glass, ghost, ice) -> transparent
Constant Principled alpha (glass) and separate grayscale alpha canvases (ghost, ice) are baked into the PNG alpha.
"""
import bpy, sys, os, re, json, importlib
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.io_utils import axis_conversion

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style_H as H

REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
UNITY_PROJECT = os.path.join(REPO, "Zombie Ice Cream Truck")
ART_REL = "Assets/Art/PS1"
ART = os.path.join(UNITY_PROJECT, ART_REL)

MODULES = ["h_core", "h_characters", "h_weapons", "h_items", "h_truck", "h_road", "h_stops", "h_fx", "h_scenery", "h_hotspots", "h_shop"]
CATEGORY = {"h_core": "Zombies", "h_characters": "Characters", "h_weapons": "Weapons", "h_items": "Items",
            "h_truck": "Truck", "h_road": "Road", "h_stops": "Stops", "h_fx": "FX", "h_scenery": "Scenery",
            "h_hotspots": "Stops", "h_shop": "Shop"}
ZOMBIE_CHARACTERS = {"Walker Worker", "Walker Mail Carrier", "Walker Granny", "Frozen Walker"}
SKIP = {"Walker Hit", "Sprinter Climb", "Sprinter Hit", "Bloater Pop", "Player T-Pose",
        "Walker Worker Hit", "Walker Mail Carrier Hit", "Walker Granny Hit"}

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ONLY = set(args[0].split(",")) if args else None
slug = lambda s: re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
safe = lambda s: re.sub(r"[^A-Za-z0-9 _-]+", "_", s).strip()


def prefixed(asset, raw, strip):
    """File-safe name that starts with the asset name exactly once."""
    name = safe(re.sub(strip, "", raw))
    return name if name.startswith(asset) else f"{asset} {name}"


def to_unity(v):
    return Vector((-v.x, v.z, -v.y))


def rounded(v):
    return [round(c, 4) + 0.0 for c in v]


def clear_data():
    for coll in (bpy.data.objects, bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights,
                 bpy.data.cameras, bpy.data.curves, bpy.data.metaballs, bpy.data.node_groups, bpy.data.collections):
        bpy.data.batch_remove(list(coll))


def reparent_children(ob):
    for child in ob.children:
        mw = child.matrix_world.copy()
        child.parent = ob.parent
        child.matrix_world = mw


def flatten_to_meshes(col, notes):
    """Curves, text and metaballs become meshes; lights, cameras and anything else non-exportable are dropped."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in list(col.all_objects):
        if ob.type in {'CURVE', 'FONT', 'META', 'SURFACE'}:
            name = ob.name
            me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            new = bpy.data.objects.new(name + " mesh", me)
            col.objects.link(new)
            new.parent = ob.parent
            new.matrix_parent_inverse = ob.matrix_parent_inverse
            new.matrix_basis = ob.matrix_basis
            for child in ob.children:
                child.parent = new
            notes.append(f"converted {ob.type.lower()} to mesh")
            bpy.data.objects.remove(ob)
            new.name = name
        elif ob.type in {'LIGHT', 'CAMERA', 'SPEAKER', 'LIGHT_PROBE'}:
            reparent_children(ob)
            notes.append(f"dropped {ob.type.lower()}")
            bpy.data.objects.remove(ob)
        elif ob.type == 'MESH' and ob.modifiers:
            ob.data = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
            ob.modifiers.clear()
            notes.append("applied modifiers")
    bad = [ob.name for ob in col.all_objects if ob.type not in {'MESH', 'EMPTY'}]
    assert not bad, f"unexpected object types: {bad}"


def convert_space(col, root):
    """Re-express every object in the exporter's target axes without moving anything in the world (see header)."""
    g = axis_conversion(to_forward='-Z', to_up='Y').to_4x4()
    g_inv = g.inverted()
    for me in {ob.data for ob in col.all_objects if ob.type == 'MESH'}:
        me.transform(g)
    for ob in col.all_objects:
        local = ob.matrix_parent_inverse @ ob.matrix_basis
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.matrix_basis = local @ g_inv if ob is root else g @ local @ g_inv
    bpy.context.view_layer.update()


def linked_from(socket):
    return socket.links[0].from_socket if socket.is_linked else None


def image_rgba(img):
    px = np.empty(img.size[0] * img.size[1] * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    return px.reshape(img.size[1], img.size[0], 4)


def bake_texture(mat):
    """RGBA pixels for the material's single color texture, with every alpha source folded into A."""
    p = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    color = linked_from(p.inputs["Base Color"])
    assert color is not None and color.node.type == 'TEX_IMAGE', f"{mat.name}: Base Color is not an image texture"
    tex = color.node
    rgba = image_rgba(tex.image).copy()
    alpha = linked_from(p.inputs["Alpha"])
    if alpha is None:
        rgba[..., 3] = p.inputs["Alpha"].default_value
        source = ("const", round(p.inputs["Alpha"].default_value, 4))
    else:
        assert alpha.node.type == 'TEX_IMAGE', f"{mat.name}: Alpha is not an image texture"
        a = image_rgba(alpha.node.image)
        assert a.shape == rgba.shape, f"{mat.name}: alpha texture size {a.shape} != color {rgba.shape}"
        rgba[..., 3] = a[..., 3] if alpha.name == "Alpha" else a[..., 0]
        source = (alpha.node.image.name, alpha.name)
    return tex, p, rgba, source


def alpha_mode(a):
    if a.min() >= 0.999:
        return ""
    if np.all((a <= 0.001) | (a >= 0.999)):
        return "__clip"
    return "__blend"


def export_materials(asset, col, tex_dir):
    """Write one PNG per distinct (image, alpha source, wrap) and rebuild each material around that file."""
    written, used_names = {}, set()
    mats = {slot.material for ob in col.all_objects if ob.type == 'MESH' for slot in ob.material_slots}
    for mat in sorted(mats, key=lambda m: m.name):
        tex, p, rgba, source = bake_texture(mat)
        mode = alpha_mode(rgba[..., 3])
        repeat = tex.extension == 'REPEAT'
        key = (tex.image.name, source, repeat)
        if key not in written:
            base = prefixed(asset, tex.image.name, r"^H ")
            name, n = base, 2
            while name in used_names:
                name, n = f"{base} {n}", n + 1
            used_names.add(name)
            path = os.path.join(tex_dir, name + ("__repeat" if repeat else "") + ".png")
            h, w = rgba.shape[:2]
            out = bpy.data.images.new(name, w, h, alpha=bool(mode))
            out.pixels.foreach_set(rgba.ravel())
            out.filepath_raw = path
            out.file_format = 'PNG'
            out.save()
            bpy.data.images.remove(out)
            written[key] = path
        emit = p.inputs["Emission Strength"].default_value
        rough = p.inputs["Roughness"].default_value
        nt = mat.node_tree
        nt.nodes.clear()
        out_node = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(written[key], check_existing=True)
        img.interpolation = 'Closest'
        img.extension = 'REPEAT' if repeat else 'EXTEND'
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Emission Strength"].default_value = emit
        nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
        if mode:
            nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
        nt.links.new(bsdf.outputs[0], out_node.inputs[0])
        mat.name = prefixed(asset, mat.name, r"^ZD2 H ") + mode
    return sorted(set(written.values()))


def hierarchy_path(ob, root):
    names = []
    while ob is not root:
        names.append(ob.name)
        ob = ob.parent
    return "/".join(reversed(names))


def describe(col, root):
    """Bounds, triangle count and empties in Unity coordinates, relative to the root (which sits at the origin)."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    pts, tris = [], 0
    for ob in col.all_objects:
        if ob.type != 'MESH':
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3, dtype=np.float64)
        me.vertices.foreach_get("co", co)
        me.calc_loop_triangles()
        tris += len(me.loop_triangles)
        m = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
        pts.append(np.stack([-co[:, 0], co[:, 2], -co[:, 1]], axis=1))
        ev.to_mesh_clear()
    pts = np.concatenate(pts)
    empties = []
    for ob in sorted((o for o in col.all_objects if o.type == 'EMPTY' and o is not root), key=lambda o: hierarchy_path(o, root)):
        mw = ob.matrix_world
        rot = mw.to_3x3()
        empties.append(dict(name=ob.name, kind="socket" if " socket " in ob.name else "pivot",
                            path=hierarchy_path(ob, root), position=rounded(to_unity(mw.translation)),
                            forward=rounded(to_unity(rot @ Vector((0, -1, 0))).normalized()),
                            up=rounded(to_unity(rot @ Vector((0, 0, 1))).normalized())))
    return dict(triangles=tris, boundsMin=rounded(pts.min(axis=0)), boundsMax=rounded(pts.max(axis=0)), empties=empties)


def export_asset(module, index, name, fn, category):
    clear_data()
    scene = bpy.context.scene
    col = bpy.data.collections.new(f"asset {name}")
    scene.collection.children.link(col)
    kit = H.make_kit(col, seed=100 + index)
    root = kit.empty(f"{name} root", None, (0, 0, 0))
    fn(kit, root)
    notes = []
    for ob in col.all_objects:
        if ob is not root and ob.parent is None:
            ob.parent = root
            notes.append(f"parented stray top-level object {ob.name} to the root")
    flatten_to_meshes(col, notes)
    for ob in scene.objects:
        assert ob.users_collection[0] is col, f"{ob.name} is outside the asset collection"
    cat_dir = os.path.join(ART, category)
    tex_dir = os.path.join(cat_dir, "Textures")
    os.makedirs(tex_dir, exist_ok=True)
    pngs = export_materials(name, col, tex_dir)
    info = describe(col, root)
    negative = sum(1 for ob in col.all_objects if ob.matrix_world.determinant() < 0)
    if negative:
        notes.append(f"{negative} objects with mirrored (negative) scale")
    convert_space(col, root)
    fbx = os.path.join(cat_dir, f"{name}.fbx")
    bpy.ops.export_scene.fbx(filepath=fbx, use_selection=False, object_types={'EMPTY', 'MESH'},
                             use_mesh_modifiers=True, use_mesh_modifiers_render=True, mesh_smooth_type='FACE',
                             use_triangles=True, colors_type='NONE', use_tspace=False, use_custom_props=False,
                             global_scale=1.0, apply_unit_scale=True, apply_scale_options='FBX_SCALE_UNITS',
                             axis_forward='-Z', axis_up='Y', use_space_transform=True, bake_space_transform=False,
                             bake_anim=False, add_leaf_bones=False, path_mode='RELATIVE', embed_textures=False)
    entry = dict(category=category, module=module, fbx=f"{ART_REL}/{category}/{name}.fbx",
                 textures=[f"{ART_REL}/{category}/Textures/{os.path.basename(p)}" for p in pngs], **info)
    if notes:
        entry["notes"] = sorted(set(notes))
    print(f"EXPORTED {category}/{name}: {info['triangles']} tris, {len(pngs)} png, {len(info['empties'])} empties"
          + (f" | {'; '.join(sorted(set(notes)))}" if notes else ""))
    return entry


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    manifest_path = os.path.join(ART, "manifest.json")
    assets = {}
    if ONLY and os.path.exists(manifest_path):
        assets = json.load(open(manifest_path))["assets"]
    for module in MODULES:
        mod = importlib.import_module(module)
        for i, (name, fn) in enumerate(mod.ASSETS):
            if name in SKIP:
                continue
            if ONLY and not ({name, slug(name), module} & ONLY):
                continue
            # Chunk dressing joins the road chunk prefabs, whose colliders are read from Road/ meshes.
            category = "Zombies" if name in ZOMBIE_CHARACTERS else "Road" if name.endswith(" Dressing") else CATEGORY[module]
            assets[name] = export_asset(module, i, name, fn, category)
    os.makedirs(ART, exist_ok=True)
    manifest = {
        "coordinateMapping": "Unity coordinates: unity = (-blender.x, blender.z, -blender.y). Meters. Positions are "
                             "relative to the imported model root (the Blender '<Asset> root' empty at the origin). "
                             "forward = the empty's Blender local -Y, up = its Blender local +Z; both equal the "
                             "imported Transform.forward / Transform.up. path is the Transform path below the model root.",
        "assets": dict(sorted(assets.items(), key=lambda kv: (kv[1]["category"], kv[0]))),
    }
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=1)
    print(f"EXPORT_DONE {len(assets)} assets in manifest")


main()
