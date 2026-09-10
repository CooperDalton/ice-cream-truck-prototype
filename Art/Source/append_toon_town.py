"""Append town models to the live Blender workshop, keeping existing edits."""
import bpy, json
from pathlib import Path
root=Path('C:/Users/wizdr/ice-cream-truck-prototype')
original_scene=bpy.context.window.scene
before={o.name:tuple(v for row in o.matrix_world for v in row) for o in bpy.data.objects}
assert 'P - Toon town scenery' not in bpy.data.collections
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Art/Source/BeforeTown_Live.blend'),copy=True)
with bpy.data.libraries.load(str(root/'Art/Source/ToonTown_Additions.blend'),link=False) as (available,loaded):
    loaded.collections=['P - Toon town scenery']
gallery=loaded.collections[0]
workshop=bpy.data.scenes['Ice cream truck workshop'];workshop.collection.children.link(gallery)
bpy.context.window.scene=workshop;bpy.context.view_layer.update()
assert all(name in bpy.data.objects and tuple(v for row in bpy.data.objects[name].matrix_world for v in row)==matrix for name,matrix in before.items())
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
bpy.context.window.scene=original_scene
(root/'Art/Source/ToonTown_append.json').write_text(json.dumps({'preserved_objects':len(before),'new_collections':len(gallery.children),'master_saved':True},indent=2))
print('TOWN_APPENDED',len(gallery.children))
