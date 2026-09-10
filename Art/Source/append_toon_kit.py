"""Append the verified toon asset library without replacing the live workshop."""
import ast
import bpy
import hashlib
import json
from pathlib import Path

project=Path('C:/Users/wizdr/ice-cream-truck-prototype')
source=ast.parse((project/'Art/Source/build_art_style_review.py').read_text())
node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='fingerprint')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
live_scene=bpy.context.scene
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene
    bpy.context.view_layer.update()
bpy.context.window.scene=live_scene
before={o.name:fingerprint(o) for o in bpy.data.objects}
assert 'N - Toon tycoon model kit' not in bpy.data.collections
bpy.ops.wm.save_as_mainfile(filepath=str(project/'Art/Source/BeforeToonKit_Append.blend'),copy=True)
with bpy.data.libraries.load(str(project/'Art/Source/ToonKit_Additions.blend'),link=False) as (available,loaded):
    loaded.collections=['N - Toon tycoon model kit']
    loaded.scenes=[n for n in available.scenes if n.startswith('Toon kit - ')]
gallery=loaded.collections[0]
workshop=bpy.data.scenes['Ice cream truck workshop']
workshop.collection.children.link(gallery)
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene
    bpy.context.view_layer.update()
changed=[name for name,value in before.items() if fingerprint(bpy.data.objects[name])!=value]
assert not changed,changed
inventory=json.loads((project/'Art/Previews/ToonKit/inventory.json').read_text())
assert len(gallery.children)==len(inventory)
report={'existing_objects_preserved':len(before),'new_asset_collections':len(gallery.children),'live_edits_preserved':True}
(project/'Art/Previews/ToonKit/append-audit.json').write_text(json.dumps(report,indent=2))
area=bpy.context.area;area.type='VIEW_3D'
space=area.spaces.active;space.overlay.show_overlays=False
space.shading.type='MATERIAL';space.shading.use_scene_world=True;space.shading.use_scene_lights=True
space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=0;space.region_3d.view_camera_offset=(0,0)
bpy.context.window.scene=workshop
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(project/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
bpy.context.window.scene=bpy.data.scenes['Toon kit - start here']
print('TOON_KIT_APPENDED',json.dumps(report))
