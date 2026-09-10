"""Compare the saved master with the live-session backup from before the append."""
import ast
import bpy
import hashlib
import json
from pathlib import Path

project=Path(__file__).resolve().parents[2]
source=ast.parse((project/'Art/Source/build_art_style_review.py').read_text())
node=next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='fingerprint')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
bpy.ops.wm.open_mainfile(filepath=str(project/'Art/Source/BeforeArtStyleRound2_Append.blend'))
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene
    bpy.context.view_layer.update()
before={o.name:fingerprint(o) for o in bpy.data.objects}
bpy.ops.wm.open_mainfile(filepath=str(project/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene
    bpy.context.view_layer.update()
changed=[name for name,value in before.items() if name not in bpy.data.objects or fingerprint(bpy.data.objects[name])!=value]
assert not changed, changed
gallery=bpy.data.collections['M - Soft and Cel shop props']
assert len(gallery.children)==8
scene=bpy.data.scenes['Art style review 2']
assert sum(o.instance_type=='COLLECTION' for o in scene.objects)==8
assert scene.camera.data.ortho_scale==19
result={'saved_master_verified':True,'existing_objects_preserved':len(before),'new_variants':8,'display_instances':8}
(project/'Art/Previews/ArtStyleRound2/saved-master-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
