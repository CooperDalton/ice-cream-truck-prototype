"""Give the street bin a closed wall section, rim and recessed interior; update its FBX."""
import math
from pathlib import Path
import bpy
from mathutils import Matrix

repo = Path(__file__).resolve().parents[2]
scene = bpy.data.scenes['Ice cream truck workshop']
bpy.context.window.scene = scene
collection = bpy.data.collections['Town / Street_bin']
root = bpy.data.objects['Town_Street_bin_ROOT']
body = next(o for o in collection.objects if o.name.endswith('Bin body'))
opening = next(o for o in collection.objects if o.name.endswith('Dark opening'))
# Traverse the outer wall upward, across the lip and down its inner face.
profile = [(.27, 0), (.31, .85), (.34, .87), (.34, .95), (.28, 1.03),
           (.255, 1.01), (.31, .94), (.31, .89), (.285, .87), (.245, .05)]
n = 20
vertices = [(r * math.cos(i * math.tau / n), r * math.sin(i * math.tau / n), z)
            for r, z in profile for i in range(n)]
faces = [(j*n+i, j*n+(i+1)%n, ((j+1)%len(profile))*n+(i+1)%n, ((j+1)%len(profile))*n+i)
         for j in range(len(profile)) for i in range(n)]
body.data.clear_geometry()
body.data.from_pydata(vertices, [], faces)
body.data.update()
# Flat faces retain the town's faceted style without smearing normals across the lip.
for p in body.data.polygons:
    p.use_smooth = False
opening.data.clear_geometry()
opening.data.from_pydata([(0, 0, .10)] + [(.25*math.cos(i*math.tau/n), .25*math.sin(i*math.tau/n), .10) for i in range(n)], [],
                        [(0, 1+i, 1+(i+1)%n) for i in range(n)])
opening.data.update()
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(repo/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
export = bpy.data.scenes.new('Bin export')
wrapper = bpy.data.objects.new('Town model', None)
export.collection.objects.link(wrapper)
deps = bpy.context.evaluated_depsgraph_get()
for obj in collection.objects:
    if obj.type != 'MESH':
        continue
    data = bpy.data.meshes.new_from_object(obj.evaluated_get(deps), depsgraph=deps)
    copy = bpy.data.objects.new(obj.name, data)
    export.collection.objects.link(copy)
    copy.parent = wrapper
    copy.matrix_world = Matrix.Translation(-root.matrix_world.translation) @ obj.matrix_world
bpy.context.window.scene = export
bpy.ops.object.select_all(action='SELECT')
bpy.context.view_layer.objects.active = wrapper
bpy.ops.export_scene.fbx(filepath=str(repo/'Ice Cream Truck Prototype/Assets/Art/Tycoon/Town/Street_bin.fbx'),
                        use_selection=True, object_types={'MESH', 'EMPTY'}, axis_forward='-Z', axis_up='Y', bake_anim=False, add_leaf_bones=False)
print('BIN_FIXED: outer faces, inner faces, closed rim, recessed interior; master and FBX saved.')
