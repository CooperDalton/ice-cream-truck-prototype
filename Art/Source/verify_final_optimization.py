"""Audit geometry, placement, materials, skinning, anchors, and road seams."""
import bpy,bmesh,json,math,hashlib,array,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
def models():return {o.name:o for c in bpy.context.scene.collection.children if not c.name.startswith('Z') for o in c.all_objects}
def meshhash(me):
    a=array.array('f',[0])*len(me.vertices)*3;me.vertices.foreach_get('co',a);b=array.array('i',[0])*len(me.loops);me.loops.foreach_get('vertex_index',b);return hashlib.sha256(a.tobytes()+b.tobytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/BeforeFinalOptimization.blend'));bpy.context.view_layer.update();before={};original_meshes={}
for n,o in models().items():
    d={'matrix':o.matrix_world.copy(),'parent':o.parent.name if o.parent else None,'hidden':o.hide_get(),'render_hidden':o.hide_render}
    if o.type=='MESH':
        d['mesh']=o.data.name;d['skin']=any(m.type=='ARMATURE' for m in o.modifiers)
        if o.data.name not in original_meshes:
            me=o.data;me.calc_loop_triangles();original_meshes[me.name]={'verts':[v.co.copy() for v in me.vertices],'faces':[tuple(p.vertices) for p in me.polygons],'tris':len(me.loop_triangles),'hash':meshhash(me)}
    before[n]=d
target=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend' if '--saved-master' in sys.argv else R/'Art/Source/OptimizedWorkshop.blend'
bpy.ops.wm.open_mainfile(filepath=str(target));bpy.context.view_layer.update();after=models();assert set(before)==set(after)
report={'objects_checked':len(after),'meshes':{},'road_edges_checked':0,'floating_hands':[]};checked=set()
for n,o in after.items():
    d=before[n];assert (o.parent.name if o.parent else None)==d['parent'];assert o.hide_get()==d['hidden'] and o.hide_render==d['render_hidden'],n
    assert max(abs(o.matrix_world[i][j]-d['matrix'][i][j]) for i in range(4) for j in range(4))<1e-5,n
    if o.type!='MESH':continue
    assert all(m is not None for m in o.data.materials),n
    assert all(math.isfinite(c) for v in o.data.vertices for c in v.co),n
    me=o.data;me.calc_loop_triangles();orig=original_meshes[d['mesh']];assert len(me.loop_triangles)<=orig['tris'],n
    if d['skin']:assert meshhash(me)==orig['hash'],n
    if me in checked:continue
    checked.add(me);bm=bmesh.new();bm.from_mesh(me)
    defects={'zero_area_faces':sum(f.calc_area()<1e-14 for f in bm.faces),'loose_vertices':sum(not v.link_faces for v in bm.verts),'edges_with_over_two_faces':sum(len(e.link_faces)>2 for e in bm.edges)}
    assert not any(defects.values()),(n,defects);bm.free()
    # Surface distance measures actual geometric change, independently of vertex numbering.
    a=BVHTree.FromPolygons(orig['verts'],orig['faces']);b=BVHTree.FromPolygons([v.co for v in me.vertices],[tuple(p.vertices) for p in me.polygons])
    distances=[b.find_nearest(v)[3] for v in orig['verts']]+[a.find_nearest(v.co)[3] for v in me.vertices]
    scale=max(o.matrix_world.to_scale());error=max(distances)*scale
    assert error<.035,(n,error)
    report['meshes'][n]={'before_triangles':orig['tris'],'after_triangles':len(me.loop_triangles),'max_surface_distance_m':round(error,6),**defects}
for rig_name in ['Crew_Rig','FirstPersonHands_Rig']:
    rig=bpy.data.objects[rig_name];body=next(o for o in rig.children if o.type=='MESH')
    def coords():
        bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return out
    for side in ['L','R']:
        bone=rig.data.bones['Hand_'+side];assert bone.parent.name=='Root' and not bone.use_connect
        pb=rig.pose.bones[bone.name];neutral=coords();pb.location.x=.2;posed=coords();index=body.vertex_groups[bone.name].index
        expected={v.index for v in body.data.vertices if any(g.group==index and g.weight>.99 for g in v.groups)};moved={i for i,(p,q) in enumerate(zip(neutral,posed)) if (p-q).length>1e-4};assert moved==expected
        pb.location.x=0;report['floating_hands'].append({'rig':rig_name,'hand':side,'vertices_moved':len(moved)})
for r in [o for o in after.values() if o.get('road_ports')]:
    ob=next(o for o in r.children if o.type=='MESH')
    for port in r['road_ports']:
        for x in [-3.75,-2.25,-1.75,-.25,.25,1.75,2.25,3.75]:
            p=(x,3.99,2) if port=='N' else (x,-3.99,2) if port=='S' else (3.99,x,2) if port=='E' else (-3.99,x,2)
            hit,point,_,_=ob.ray_cast(ob.matrix_world.inverted() @ r.matrix_world @ Vector(p),Vector((0,0,-1)));assert hit
            h=(r.matrix_world.inverted() @ ob.matrix_world @ point).z;expected=0 if abs(x)<2 else .12 if abs(x)<2.5 else .06;assert abs(h-expected)<.0001
        report['road_edges_checked']+=1
for name,count in [('FinishedCone_ROOT',1),('Cone_2Scoops_ROOT',2),('Cone_3Scoops_ROOT',3)]:
    r=bpy.data.objects[name];scoops=[o for o in r.children_recursive if o.type=='MESH' and 'IceCreamScoop' in o.name];assert len(scoops)==count,(name,len(scoops))
cone=bpy.data.objects['EmptyCone_ROOT_Mesh'].data;assert len(cone.vertices)==80
assert any(i.packed_file for i in bpy.data.images if 'WaffleCone' in i.name or 'Waffle' in i.name)
for rig in [o for o in after.values() if o.type=='ARMATURE']:
    for o in rig.children:
        if o.type=='MESH':assert all(abs(sum(g.weight for g in v.groups)-1)<.001 for v in o.data.vertices)
assert bpy.data.objects['Adult_Mesh'].data==bpy.data.objects['AdultVariant_Mesh'].data
assert bpy.data.objects['Child_Mesh'].data==bpy.data.objects['ChildVariant_Mesh'].data
truck=bpy.data.objects['IceCreamTruck_ROOT'];assert (truck.matrix_world.inverted() @ bpy.data.objects['SteeringWheel_ROOT'].matrix_world.translation).y<0
for ob in bpy.data.collections['F • Trees'].all_objects:
    if ob.type=='MESH':
        assert not any(p.use_smooth for p in ob.data.polygons),ob.name
        assert all(ob.data.corner_normals[i].vector.dot(p.normal)>.999 for p in ob.data.polygons for i in p.loop_indices),ob.name
report['checks']={'object_hierarchy_transforms_visibility_preserved':True,'all_six_skinned_meshes_unchanged':True,'normalized_skin_weights':True,'shared_customer_meshes':True,'one_two_three_scoop_models_preserved':True,'flat_cone_texture_preserved':True,'left_hand_drive_preserved':True,'faceted_tree_normals_preserved':True,'all_inspected_meshes_finite_and_without_degenerate_faces_or_multi_face_edges':True}
(R/'Art/Source/final-optimization-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'checks':report['checks'],'mesh_count':len(report['meshes']),'road_edges_checked':report['road_edges_checked'],'max_surface_distance_m':max(x['max_surface_distance_m'] for x in report['meshes'].values())},indent=2))
