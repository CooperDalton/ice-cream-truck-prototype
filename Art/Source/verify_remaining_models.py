"""Check saved models, tile connections, articulated parts, and GLB budgets."""
import bpy,json,hashlib,struct,array,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
def snapshot():
    out={}
    for o in bpy.context.scene.objects:
        if any(c.name.startswith('Z') for c in o.users_collection):continue
        state={'matrix':[round(v,6) for row in o.matrix_world for v in row], 'parent':o.parent.name if o.parent else None,'type':o.type}
        if o.type=='MESH':
            a=array.array('f',[0])*len(o.data.vertices)*3;o.data.vertices.foreach_get('co',a)
            b=array.array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',b)
            state['mesh']=hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest();state['materials']=[m.name if m else None for m in o.data.materials]
        out[o.name]=state
    return out
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/BeforeRemainingModels.blend'));before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'));after=snapshot()
assert all(after[name]==state for name,state in before.items())
newcols=[bpy.data.collections[name] for name in ['G • Modular ground','H • Park and street props','I • Supplies and handheld props','J • Delivery bike and stand']]
roots=[o for c in newcols for o in c.objects if o.parent is None];assert len(roots)==44
report={'existing_objects_preserved':len(before),'new_assets':len(roots),'tile_edges':{},'articulation':{},'exports':{}}
for r in roots:
    for o in [r]+list(r.children_recursive):
        if o.type=='MESH':assert len(o.data.materials)>0 and len(o.data.vertices)>0 and not o.hide_render
    if r.get('grid_size_m') and r.name!='Park_Cell_ROOT':
        pts=[r.matrix_world.inverted() @ o.matrix_world @ Vector(v) for o in r.children_recursive if o.type=='MESH' for v in o.bound_box]
        for i in [0,1]:assert abs(max(p[i] for p in pts)-min(p[i] for p in pts)-8)<.0001,r.name
    if r.get('road_ports'):
        ob=next(o for o in r.children if o.type=='MESH');edges={}
        for port in r['road_ports']:
            heights=[]
            for x in [-3.75,-2.75,-2.25,-1.75,-.25,.25,1.75,2.25,2.75,3.75]:
                p=(x,3.99,2) if port=='N' else (x,-3.99,2) if port=='S' else (3.99,x,2) if port=='E' else (-3.99,x,2)
                local=ob.matrix_world.inverted() @ r.matrix_world @ Vector(p)
                hit,point,normal,idx=ob.ray_cast(local,Vector((0,0,-1)))
                assert hit,(r.name,port,p)
                h=(r.matrix_world.inverted() @ ob.matrix_world @ point).z;expected=0 if abs(x)<2 else .12 if abs(x)<2.5 else .06
                assert abs(h-expected)<.0001,(r.name,port,x,h,expected)
                heights.append(round(h,4))
            edges[port]=heights
        report['tile_edges'][r.name]=edges
# Exercise the saved parent hierarchy without saving test poses.
for name,axis,angle in [('Cooler_Lid_HINGE',0,-100),('Bike_Steering_PIVOT',2,25),('Bike_FrontWheel_AXLE',0,45),('Bike_RearWheel_AXLE',0,45),('Bike_Pedals_AXLE',0,45),('Mailbox_Flag_PIVOT',0,70)]:
    o=bpy.data.objects[name];child=next(c for c in o.children if c.type=='MESH');v=child.data.vertices[0].co.copy();bpy.context.view_layer.update();p=child.matrix_world @ v
    old=o.rotation_euler.copy();o.rotation_euler[axis]+=math.radians(angle);bpy.context.view_layer.update();q=child.matrix_world @ v;delta=(q-p).length
    assert delta>.001,name;o.rotation_euler=old;report['articulation'][name]=round(delta,5)
bpy.context.view_layer.update()
for export in ['RoadAndParkKit','RemainingProps','WorkshopModels']:
    data=(R/'Art/Exports'/f'{export}.glb').read_bytes();length=struct.unpack_from('<I',data,12)[0];j=json.loads(data[20:20+length]);nodes=j['nodes'];acc=j['accessors']
    def counts(i):
        node=nodes[i];out={'vertices':0,'triangles':0,'mesh_nodes':0,'material_sections':0}
        if 'mesh' in node:
            out['mesh_nodes']=1
            for p in j['meshes'][node['mesh']]['primitives']:
                out['vertices']+=acc[p['attributes']['POSITION']]['count'];out['triangles']+=acc[p['indices']]['count']//3;out['material_sections']+=1
        for child in node.get('children',[]):
            for k,v in counts(child).items():out[k]+=v
        return out
    report['exports'][export]={nodes[i]['name']:counts(i) for i in j['scenes'][0]['nodes']}
    assert not any('review shelf' in n.get('name','') for n in nodes)
    if export!='WorkshopModels':
        for name,budget in report['exports'][export].items():assert budget['triangles']<7000,(name,budget)
    if export=='RemainingProps':
        exported={n.get('name') for n in nodes}
        for name in ['Cooler_Lid_HINGE','Bike_Steering_PIVOT','Bike_FrontWheel_AXLE','Bike_RearWheel_AXLE','Bike_Cooler_SOCKET','Boombox_Grip_SOCKET']:assert name in exported
report['checks']={'all_old_model_geometry_and_transforms_unchanged':True,'road_edges_match_in_all_port_directions':True,'eight_meter_tiles':True,'articulated_parts_move':True,'new_asset_budget_under_7000_triangles_each':True,'review_shelves_excluded_from_exports':True}
(R/'Art/Source/remaining-models-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':report['checks'],'new_assets':len(roots),'existing_objects_preserved':len(before),'new_totals':{k:sum(v[k] for export in ['RoadAndParkKit','RemainingProps'] for v in report['exports'][export].values()) for k in ['vertices','triangles','mesh_nodes','material_sections']}},indent=2))
