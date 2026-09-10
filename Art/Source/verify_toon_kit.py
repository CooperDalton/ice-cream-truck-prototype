"""Verify actual saved models, including deformation, articulation and preservation."""
import ast
import bpy
import hashlib
import json
import math
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Art/Previews/ToonKit'
master='--master' in sys.argv
before={}
if master:
    tree=ast.parse((ROOT/'Art/Source/build_art_style_review.py').read_text())
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='fingerprint')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Art/Source/BeforeToonKit_Append.blend'))
    for scene in bpy.data.scenes:
        bpy.context.window.scene=scene;bpy.context.view_layer.update()
    before={o.name:fingerprint(o) for o in bpy.data.objects}
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
else:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Additions.blend'))
for scene in bpy.data.scenes:
    bpy.context.window.scene=scene;bpy.context.view_layer.update()
if master:
    changed=[name for name,value in before.items() if name not in bpy.data.objects or fingerprint(bpy.data.objects[name])!=value]
    assert not changed,changed
inventory=json.loads((OUT/'inventory.json').read_text())
gallery=bpy.data.collections['N - Toon tycoon model kit']
assert len(inventory)==len(gallery.children)==91
scene=bpy.data.scenes['Ice cream truck workshop']
bpy.context.window.scene=scene
if gallery.name not in scene.collection.children:scene.collection.children.link(gallery)
bpy.context.view_layer.update()
triangle_count=0;fill_checks=[];rig_checks=[];hinges=[]
for entry in inventory:
    col=bpy.data.collections[entry['collection']];root=bpy.data.objects[entry['root']]
    assert root in list(col.objects)
    for obj in col.objects:
        if obj.type=='MESH':
            assert all(math.isfinite(v) for vertex in obj.data.vertices for v in vertex.co)
            obj.data.calc_loop_triangles();triangle_count+=len(obj.data.loop_triangles)
            assert all(slot.material and any(n.type=='EMISSION' for n in slot.material.node_tree.nodes) for slot in obj.material_slots),obj.name
            for mod in obj.modifiers:
                if mod.type=='ARMATURE':
                    assert mod.object in list(col.objects),obj.name
                    rig_checks.append(obj.name)
        if 'DOOR_' in obj.name and obj.name.endswith('_HINGE'):
            old=obj.rotation_euler.copy()
            handle=next(c for c in obj.children if c.type=='EMPTY' and c.name.endswith('HAND_TARGET'))
            a=handle.matrix_world.translation.copy()
            obj.rotation_euler.z=math.radians(-105);bpy.context.view_layer.update()
            assert (a-handle.matrix_world.translation).length>.3
            obj.rotation_euler=old;bpy.context.view_layer.update();hinges.append(obj.name)
        if obj.type=='MESH' and 'Ice cream fill' in obj.name and obj.data.shape_keys:
            key=obj.data.shape_keys.key_blocks['Empty'];old=key.value
            assert old==0,obj.name
            heights=[]
            for value in [0,.5,1]:
                key.value=value;bpy.context.view_layer.update()
                evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
                heights.append(sum(v.co.z for v in evaluated.data.vertices)/len(evaluated.data.vertices))
            assert heights[0]>.20 and abs(heights[2]-.022)<.00001
            assert abs(heights[1]-(heights[0]+heights[2])/2)<.00001
            key.value=old;fill_checks.append({'object':obj.name,'full_half_empty_mean_z':heights})
assert len(fill_checks)==12
assert len(hinges)==24
for slots in [4,8,12]:
    root=bpy.data.objects[f'Toon_{slots}_slot_locker_ROOT']
    assert root['inventory_slots']==slots and tuple(root['grid_footprint_m'])==(1,.5)
    assert len([o for o in root.children if '_STOCK_' in o.name])==slots
for slots in [4,8]:
    root=bpy.data.objects[f'Toon_Delivery_bike_{slots}_cargo_ROOT']
    cargo=[o for o in root.children if '_CARGO_' in o.name]
    assert len(cargo)==slots
    assert len({round(o.location.z,3) for o in cargo})==(1 if slots==4 else 2)
for wells in [1,2]:
    root=bpy.data.objects[f'Toon_{wells}_well_cooled_module_ROOT']
    col=next(c for c in gallery.children if root in list(c.objects))
    position=root.location+Vector((0 if wells==1 else -.25,0,2))
    hits=[]
    for obj in col.objects:
        if obj.type!='MESH' or 'outline' in obj.name:continue
        inverse=obj.matrix_world.inverted()
        hit,point,normal,index=obj.ray_cast(inverse@position,inverse.to_3x3()@Vector((0,0,-1)))
        if hit:hits.append((obj.matrix_world@point-root.location).z)
    assert hits and max(hits)<.75,(wells,hits)
pages=[s.name for s in bpy.data.scenes if s.name.startswith('Toon kit - ')]
assert len(pages)==10
report={'saved_master_verified':master,'new_asset_collections':len(inventory),'existing_objects_preserved':len(before),'raw_mesh_triangles_including_outlines':triangle_count,'articulated_locker_doors_checked':len(hinges),'depleting_flavor_surfaces_checked':fill_checks,'skinned_meshes_with_local_rigs':len(rig_checks),'cooled_wells_are_open':True,'bike_capacity_levels_verified':True,'review_scenes':pages}
(OUT/('saved-master-audit.json' if master else 'candidate-audit.json')).write_text(json.dumps(report,indent=2))
print('TOON_VERIFIED',json.dumps({k:v for k,v in report.items() if k not in ['depleting_flavor_surfaces_checked','review_scenes']}))
