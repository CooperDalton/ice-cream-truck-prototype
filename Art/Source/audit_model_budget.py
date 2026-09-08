"""Measure saved geometry and exported vertices, including normal/material splits."""
import bpy,json,struct
from pathlib import Path
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
def totals(objects):
    out={'vertices':0,'triangles':0,'mesh_objects':0,'material_sections':0};d=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type!='MESH' or o.hide_render:continue
        ev=o.evaluated_get(d);me=ev.to_mesh();me.calc_loop_triangles()
        out['vertices']+=len(me.vertices);out['triangles']+=len(me.loop_triangles);out['mesh_objects']+=1;out['material_sections']+=len(set(p.material_index for p in me.polygons));ev.to_mesh_clear()
    return out
report={}
for label,path in [('before',R/'Art/Source/BeforeTruckCharacterRevision_Disk.blend'),('after',R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(path))
    report[label]={c.name:totals(c.all_objects) for c in bpy.context.scene.collection.children if not c.name.startswith('Z')}
    if label=='after':
        report['assets']={o.name:totals([o]+list(o.children_recursive)) for c in bpy.context.scene.collection.children if not c.name.startswith('Z') for o in c.all_objects if o.parent is None}
        report['props']={o.name:totals([o]+list(o.children_recursive)) for o in bpy.data.collections['A • Preparation models'].all_objects if o.type=='EMPTY' and (o.name.startswith(('FinishedCone','Cone_2Scoops','Cone_3Scoops','Scooper_ROOT','BatterBottle_ROOT','SprinkleShaker_ROOT','IceCreamScoop')) and o.name.endswith('ROOT') or o.name=='IceCreamScoop')}
# glTF counts are closer to runtime vertices than Blender's welded source vertices.
report['exports']={}
for name in ['Characters','IceCreamTruck','IceCreamPreparation','Neighborhood','RoadAndParkKit','RemainingProps','WorkshopModels']:
    data=(R/'Art/Exports'/(name+'.glb')).read_bytes();length=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+length]);nodes=j['nodes'];acc=j['accessors']
    def count(index):
        node=nodes[index];out={'vertices':0,'triangles':0,'mesh_nodes':0,'material_sections':0}
        if 'mesh' in node:
            ps=j['meshes'][node['mesh']]['primitives'];out['mesh_nodes']=1;out['material_sections']=len(ps)
            for p in ps:out['vertices']+=acc[p['attributes']['POSITION']]['count'];out['triangles']+=acc[p['indices']]['count']//3
        for child in node.get('children',[]):
            c=count(child)
            for k in out:out[k]+=c[k]
        return out
    report['exports'][name]={nodes[i]['name']:count(i) for i in j['scenes'][0]['nodes']}
    if name=='Characters':
        assert len(j['skins'])==6
        for n in nodes:
            if 'mesh' in n:
                assert 'skin' in n
                for p in j['meshes'][n['mesh']]['primitives']:assert 'JOINTS_0' in p['attributes'] and 'WEIGHTS_0' in p['attributes']
# Exercise a hand gesture on the saved rig without writing the pose to disk.
rig=bpy.data.objects['Adult_Rig'];ob=next(o for o in rig.children if o.type=='MESH')
def coords():
    bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=[x.co.copy() for x in me.vertices];ev.to_mesh_clear();return v
before=coords();pb=rig.pose.bones['Hand_L'];pb.rotation_mode='XYZ';pb.rotation_euler.y=.55;after=coords();delta=max((a-b).length for a,b in zip(before,after));assert delta>.04;pb.rotation_euler.y=0
assert bpy.data.objects['Adult_Mesh'].data==bpy.data.objects['AdultVariant_Mesh'].data
assert bpy.data.objects['Child_Mesh'].data==bpy.data.objects['ChildVariant_Mesh'].data
for rig in [o for o in bpy.context.scene.objects if o.type=='ARMATURE']:
    for o in rig.children:
        if o.type=='MESH':
            for v in o.data.vertices:assert abs(sum(g.weight for g in v.groups)-1)<.001
report['checks']={'hand_pose_vertex_movement_m':round(delta,4),'skin_weights_normalized':True,'shared_customer_meshes':True}
(R/'Art/Source/model-budget.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
