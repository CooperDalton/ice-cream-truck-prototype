import ast,bpy,hashlib,json,math,re
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Art/Previews/PeopleStudy'
tree=ast.parse((ROOT/'Art/Source/build_art_style_review.py').read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fingerprint')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Art/Source/BeforePeopleStudy_Append.blend'))
for scene in bpy.data.scenes:bpy.context.window.scene=scene;bpy.context.view_layer.update()
before={o.name:fingerprint(o) for o in bpy.data.objects}
fonts={o.name:o.data.body for o in bpy.data.objects if o.type=='FONT'}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for scene in bpy.data.scenes:bpy.context.window.scene=scene;bpy.context.view_layer.update()
changed=[n for n,value in before.items() if n not in bpy.data.objects or fingerprint(bpy.data.objects[n])!=value]
assert not changed,changed
audit=json.loads((OUT/'append-audit.json').read_text());cleared={e['object'] for e in audit['cleared_numeric_model_labels']}
assert all(bpy.data.objects[n].data.body==body for n,body in fonts.items() if n not in cleared)
for obj in bpy.data.collections['N - Toon tycoon model kit'].all_objects:
    if obj.type=='FONT':assert not re.search(r'\d',obj.data.body),(obj.name,obj.data.body)
gallery=bpy.data.collections['O - Toon people alternatives'];assert len(gallery.children)==8
bpy.context.window.scene=bpy.data.scenes['Ice cream truck workshop'];bpy.context.view_layer.update()
rig_tests=[]
for col in gallery.children:
    rig=next(o for o in col.objects if o.type=='ARMATURE')
    count=len(rig.data.bones);assert count in [5,15]
    for obj in col.objects:
        if obj.type!='MESH':continue
        assert all(math.isfinite(c) for v in obj.data.vertices for c in v.co)
        modifier=next(m for m in obj.modifiers if m.type=='ARMATURE');assert modifier.object==rig
        assert all(v.groups for v in obj.data.vertices),obj.name
    head=next(o for o in col.objects if o.type=='MESH' and ('Cheek shaped head' in o.name or 'Rounded square head' in o.name))
    p=[v.co.copy() for v in head.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
    bone=rig.pose.bones['Head'];bone.rotation_mode='XYZ';bone.rotation_euler.z=.3;bpy.context.view_layer.update()
    q=[v.co.copy() for v in head.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
    movement=max((b-a).length for a,b in zip(p,q))
    assert movement>.01,(col.name,movement)
    bone.rotation_euler.z=0;bpy.context.view_layer.update()
    rig_tests.append({'collection':col.name,'bones':count,'head_pose_moves_mesh':True})
result={'saved_master_verified':True,'existing_objects_preserved':len(before),'numeric_model_labels_cleared':len(cleared),'other_model_text_preserved':True,'new_people':len(gallery.children),'rig_checks':rig_tests}
(OUT/'saved-master-audit.json').write_text(json.dumps(result,indent=2));print('PEOPLE_VERIFIED',json.dumps(result))
