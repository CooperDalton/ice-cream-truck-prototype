"""Fit the workshop canopy over an 8 x 6 m shop, with posts outside the plot."""
import json
from pathlib import Path

import bpy
from mathutils import Matrix

repo = Path(__file__).resolve().parents[2]
entry = next(e for e in json.loads((repo / 'Art/Previews/ToonKit/inventory.json').read_text())
             if e['name'] == 'Pop up canopy')
root = bpy.data.objects[entry['root']]
collection = bpy.data.collections[entry['collection']]
bpy.context.window.scene = bpy.data.scenes['Ice cream truck workshop']
bpy.context.view_layer.update()
canvas = [o for o in collection.objects if 'Striped canvas' in o.name and 'outline' not in o.name]
points = [o.matrix_local @ v.co for o in canvas for v in o.data.vertices]
width = max(p.x for p in points) - min(p.x for p in points)
depth = max(p.y for p in points) - min(p.y for p in points)
lift = 2.5 - min(p.z for p in points)
posts = [o for o in collection.objects if 'Canopy upright' in o.name and 'outline' not in o.name]
post_height = max((o.matrix_local @ v.co).z for o in posts for v in o.data.vertices)
extend_posts = Matrix.Diagonal((1, 1, 2.55 / post_height, 1))
stretch = Matrix.Diagonal((8.2 / width, 6.2 / depth, 1, 1))
for obj in collection.objects:
    if obj.type != 'MESH':
        continue
    if 'Canopy upright' in obj.name:
        obj.location.x = 4.05 if obj.location.x > 0 else -4.05
        obj.location.y = 3.05 if obj.location.y > 0 else -3.05
        local = obj.matrix_local.copy()
        obj.data = obj.data.copy()
        obj.data.transform(local.inverted() @ extend_posts @ local)
        obj.data.update()
    elif 'Striped canvas' in obj.name or 'Soft valance' in obj.name:
        local = obj.matrix_local.copy()
        obj.data = obj.data.copy()
        if 'Soft valance' in obj.name:
            # Stretch the trim along the eave without thickening it.
            obj.location.x *= 8.2 / width
            obj.location.y = -3.1
            obj.data.transform(Matrix.Diagonal((8.2 / width, 1, 1, 1)))
        else:
            obj.data.transform(local.inverted() @ stretch @ local)
        obj.data.update()
        obj.location.z += lift
root['shop_plot_size_m'] = [8.0, 6.0]
root['roof_size_m'] = [8.2, 6.2]
root['roof_eave_height_m'] = 2.5
bpy.context.view_layer.update()
points = [o.matrix_local @ v.co for o in canvas for v in o.data.vertices]
assert abs(max(p.x for p in points) - min(p.x for p in points) - 8.2) < .001
assert abs(max(p.y for p in points) - min(p.y for p in points) - 6.2) < .001
assert abs(min(p.z for p in points) - 2.5) < .001
assert abs(max(p.z for p in points) - 2.95) < .001
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(repo / 'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
print('CANOPY_RESIZED: roof 8.2 x 6.2 m; eaves 2.5 m; peak 2.95 m; posts reach 2.55 m with feet on the ground.')
