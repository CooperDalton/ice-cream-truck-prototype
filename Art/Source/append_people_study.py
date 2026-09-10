"""Preserve live edits, remove model quantity text, and add the people studies."""
import ast,bpy,hashlib,json,re
from pathlib import Path
ROOT=Path('C:/Users/wizdr/ice-cream-truck-prototype');OUT=ROOT/'Art/Previews/PeopleStudy'
tree=ast.parse((ROOT/'Art/Source/build_art_style_review.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fingerprint')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
before={o.name:fingerprint(o) for o in bpy.data.objects}
font_before={o.name:o.data.body for o in bpy.data.objects if o.type=='FONT'}
assert 'O - Toon people alternatives' not in bpy.data.collections
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/BeforePeopleStudy_Append.blend'),copy=True)
cleared=[]
for col in bpy.data.collections['N - Toon tycoon model kit'].children:
    for obj in col.objects:
        if obj.type=='FONT' and re.search(r'\d',obj.data.body):
            cleared.append({'object':obj.name,'previous_text':obj.data.body,'collection':col.name})
            obj.data.body=''
with bpy.data.libraries.load(str(ROOT/'Art/Source/PeopleStudy_Additions.blend'),link=False) as (available,loaded):
    loaded.collections=['O - Toon people alternatives']
    loaded.scenes=['People - compare silhouettes']
gallery=loaded.collections[0]
workshop=bpy.data.scenes['Ice cream truck workshop'];workshop.collection.children.link(gallery)
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
changed=[name for name,hash in before.items() if fingerprint(bpy.data.objects[name])!=hash]
assert not changed,changed
allowed={e['object'] for e in cleared}
assert all(bpy.data.objects[name].data.body==value for name,value in font_before.items() if name not in allowed)
assert len(gallery.children)==8
report={'existing_objects_preserved':len(before),'cleared_numeric_model_labels':cleared,'new_people':8}
(OUT/'append-audit.json').write_text(json.dumps(report,indent=2))
area=bpy.context.area;area.type='VIEW_3D';space=area.spaces.active
space.overlay.show_overlays=False;space.shading.type='MATERIAL';space.shading.use_scene_world=True;space.shading.use_scene_lights=True
space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=15;space.region_3d.view_camera_offset=(0,0)
bpy.context.window.scene=workshop;bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
bpy.context.window.scene=loaded.scenes[0]
print('PEOPLE_APPENDED',len(cleared),'numeric labels cleared;',len(before),'existing objects preserved')
