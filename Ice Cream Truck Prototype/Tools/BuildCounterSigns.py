"""Author the service signs in the master workshop and export their game meshes."""
import math
from pathlib import Path
import shutil
import bpy

project = Path(__file__).resolve().parents[1]
master = project / 'Assets/IceCreamTruckWorkshop.blend'
backup = Path('/tmp/IceCreamTruckWorkshop-before-signs.blend')
if not backup.exists():
    shutil.copy2(master, backup)
bpy.ops.wm.open_mainfile(filepath=str(master))
previous = bpy.data.collections.get('Q - Counter service signs')
if previous:
    for obj in list(previous.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(previous)
original_objects = set(bpy.data.objects.keys())
collection = bpy.data.collections.new('Q - Counter service signs')
bpy.context.scene.collection.children.link(collection)
folder = project / 'Assets/Art/Tycoon/Signs'
folder.mkdir(exist_ok=True)

def material(name, color):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*color, 1)
    mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .8
    return mat

cream = material('SignCream', (.94, .87, .69))
mint = material('SignMint', (.22, .56, .46))
ink = material('SignInk', (.16, .12, .20))

def adopt(obj, name, parent, mat):
    obj.name = name
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

def box(name, position, size, parent, mat, bevel):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = adopt(bpy.context.object, name, parent, mat)
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new('Soft edges', 'BEVEL')
    modifier.width = bevel
    modifier.segments = 3
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj

for index, label in enumerate(('ORDER', 'PICKUP')):
    root = bpy.data.objects.new(label + ' counter sign', None)
    collection.objects.link(root)
    box('Mint foot', (0, 0, .018), (.52, .19, .036), root, mint, .012)
    for x in (-.21, .21):
        box('Support', (x, 0, .068), (.035, .046, .085), root, mint, .008)
    box('Mint frame', (0, 0, .20), (.76, .07, .25), root, mint, .032)
    for side in (-1, 1):
        box('Cream face', (0, side * .036, .20), (.714, .012, .204), root, cream, .024)
        bpy.ops.object.text_add(location=(0, side * .044, .20))
        text = bpy.context.object
        text.data.body = label
        text.data.align_x = 'CENTER'
        text.data.align_y = 'CENTER'
        text.data.size = .125
        text.data.extrude = .0012
        text.data.bevel_depth = .0004
        text.data.bevel_resolution = 1
        text.data.resolution_u = 5
        text.rotation_euler = (math.pi / 2, 0, 0 if side == -1 else math.pi)
        bpy.ops.object.convert(target='MESH')
        adopt(bpy.context.object, label + (' front letters' if side == -1 else ' back letters'), root, ink)
    bpy.ops.object.select_all(action='DESELECT')
    root.select_set(True)
    for obj in root.children:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = root
    bpy.ops.export_scene.fbx(filepath=str(folder / (label.title() + 'Sign.fbx')), use_selection=True,
        object_types={'EMPTY','MESH'}, bake_anim=False, add_leaf_bones=False,
        axis_forward='-Z', axis_up='Y', apply_unit_scale=True, mesh_smooth_type='FACE')
    root.location = (380 + index * 1.4, 0, 0)

assert original_objects.issubset(bpy.data.objects.keys())
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(master), compress=True)
print('Preserved', len(original_objects), 'original objects; added', len(bpy.data.objects)-len(original_objects), 'sign objects')
