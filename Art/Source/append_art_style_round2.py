"""Run inside the live Blender session to preserve edits and append round two."""
import ast
import bpy
import hashlib
import json
from pathlib import Path
from mathutils import Vector

project = Path('C:/Users/wizdr/ice-cream-truck-prototype')
source = ast.parse((project/'Art/Source/build_art_style_review.py').read_text())
node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'fingerprint')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
bpy.context.view_layer.update()
before = {o.name:fingerprint(o) for o in bpy.data.objects}
assert 'M - Soft and Cel shop props' not in bpy.data.collections
bpy.ops.wm.save_as_mainfile(filepath=str(project/'Art/Source/BeforeArtStyleRound2_Append.blend'),copy=True)
with bpy.data.libraries.load(str(project/'Art/Source/ArtStyleRound2_Additions.blend'),link=False) as (available, loaded):
    loaded.collections=['M - Soft and Cel shop props']
    loaded.scenes=['Art style review 2']
gallery=loaded.collections[0]
review=loaded.scenes[0]
bpy.data.scenes['Ice cream truck workshop'].collection.children.link(gallery)
bpy.context.window.scene=review
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[name])==value for name,value in before.items())
assert len(gallery.children)==8
report={'existing_objects_preserved':len(before),'new_asset_collections':len(gallery.children),
        'live_edits_preserved':True,'scene':review.name}
(project/'Art/Previews/ArtStyleRound2/append-audit.json').write_text(json.dumps(report,indent=2))
area=bpy.context.area
area.type='VIEW_3D'
space=area.spaces.active
space.overlay.show_overlays=False
space.shading.type='MATERIAL'
space.shading.use_scene_world=True
space.shading.use_scene_lights=True
space.region_3d.view_perspective='CAMERA'
space.region_3d.view_camera_zoom=10
space.region_3d.view_camera_offset=(0,0)
# Save the master with the original scene active so its model importer keeps its root scene.
bpy.context.window.scene=bpy.data.scenes['Ice cream truck workshop']
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(project/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
bpy.context.window.scene=review
print('ROUND2_APPENDED '+json.dumps(report))
