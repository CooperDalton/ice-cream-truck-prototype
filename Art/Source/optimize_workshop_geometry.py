"""Conservative mesh cleanup and targeted reductions for the final model audit."""
import bpy,bmesh,math,json,hashlib,runpy
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
def tris(me):
    me.calc_loop_triangles();return len(me.loop_triangles)
def optimize():
    scene=bpy.context.scene;models=[o for c in scene.collection.children if not c.name.startswith(('Z','99')) for o in c.all_objects if o.type=='MESH'];seen=set();report=[];visibility={o:o.hide_get() for o in models}
    for ob in models:
        original=ob.data
        if original in seen:continue
        seen.add(original);users=[o for o in models if o.data==original];before=tris(original);vbefore=len(original.vertices)
        # Keep skinned characters and the already minimal UV-mapped cone shell intact.
        if any(m.type=='ARMATURE' for m in ob.modifiers) or original.name.startswith('Shared flat-textured waffle cone'):
            report.append({'object':ob.name,'instances':len(users),'before':before,'after':before,'action':'preserved rig or textured cone'});continue
        ob.data=original.copy();me=ob.data
        # Weld only coincident bevel vertices. This removes collapsed bevel faces.
        bm=bmesh.new();bm.from_mesh(me)
        remaining=set(bm.verts);components=[]
        while remaining:
            seed=remaining.pop();group=[seed];queue=[seed]
            while queue:
                v=queue.pop()
                for e in v.link_edges:
                    other=e.other_vert(v)
                    if other in remaining:remaining.remove(other);group.append(other);queue.append(other)
            components.append(group)
        for group in components:bmesh.ops.remove_doubles(bm,verts=group,dist=1e-7)
        bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
        # Separate the pre-existing edge where several shaker-label faces met.
        junctions=[e for e in bm.edges if len(e.link_faces)>2]
        if junctions:bmesh.ops.split_edges(bm,edges=junctions)
        zero=[f for f in bm.faces if f.calc_area()<1e-14]
        if zero:bmesh.ops.delete(bm,geom=zero,context='FACES_ONLY')
        loose=[v for v in bm.verts if not v.link_faces]
        if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
        bm.to_mesh(me);bm.free();me.update()
        bpy.ops.object.select_all(action='DESELECT');ob.hide_set(False);ob.select_set(True);bpy.context.view_layer.objects.active=ob
        # Merge coplanar triangles without crossing material boundaries or UV seams.
        dec=ob.modifiers.new('Dissolve flat subdivisions','DECIMATE');dec.decimate_type='DISSOLVE';dec.angle_limit=math.radians(.5);dec.delimit={'MATERIAL','SEAM','UV','NORMAL'};dec.use_dissolve_boundaries=False;bpy.ops.object.modifier_apply(modifier=dec.name)
        target=None
        if 'IceCreamScoop' in ob.name:target=650
        elif ob.name.startswith('ConeHolder_'):target=360
        elif ob.name.startswith('Tub_'):target=1000
        elif '_Wheel_AXLE_Mesh' in ob.name and ob.name.startswith(('Front','Rear')):target=1050
        elif ob.name.startswith('SteeringWheel_ROOT_Mesh'):target=550
        # Keep small isolated decorations from disappearing during collapse.
        if target and tris(ob.data)>target:
            dec=ob.modifiers.new('Reduce repeated curved detail','DECIMATE');dec.ratio=target/tris(ob.data);dec.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=dec.name)
        # Transfer the authored split normals so broad surfaces keep their shading.
        if original.has_custom_normals:
            source=ob.copy();source.data=original;source.name='Temporary original normals';bpy.context.scene.collection.objects.link(source)
            for m in list(source.modifiers):source.modifiers.remove(m)
            source.hide_render=True
            mod=ob.modifiers.new('Preserve authored normals','DATA_TRANSFER');mod.object=source;mod.use_loop_data=True;mod.data_types_loops={'CUSTOM_NORMAL'};mod.loop_mapping='POLYINTERP_NEAREST'
            bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(source,do_unlink=True)
        runpy.run_path(str(R/'Art/Source/restore_authored_flat_faces.py'))['restore_flat_faces'](ob.data,[v.co for v in original.vertices],[tuple(p.vertices) for p in original.polygons],[p.use_smooth for p in original.polygons])
        # Remove unused slots while retaining each instance's material overrides.
        used=sorted(set(p.material_index for p in ob.data.polygons));slots={o:[(s.link,s.material) for s in o.material_slots] for o in users};polymats=[used.index(p.material_index) for p in ob.data.polygons]
        mats=[ob.data.materials[i] for i in used];assert all(m is not None for m in mats),(ob.name,used)
        ob.data.materials.clear()
        for m in mats:ob.data.materials.append(m)
        for p,i in zip(ob.data.polygons,polymats):p.material_index=i
        for o in users:
            o.data=ob.data
            for new,old in enumerate(used):
                kind,material=slots[o][old];o.material_slots[new].link=kind;o.material_slots[new].material=material
        seen.add(ob.data)
        after=tris(ob.data);assert after<=before,(ob.name,before,after)
        report.append({'object':ob.name,'instances':len(users),'before':before,'after':after,'vertices_before':vbefore,'vertices_after':len(ob.data.vertices),'action':'cleanup and targeted collapse' if target else 'coplanar and degenerate cleanup'})
        ob.select_set(False)
    for o,hidden in visibility.items():o.hide_set(hidden)
    bpy.context.view_layer.objects.active=None;bpy.context.view_layer.update()
    return report
if __name__=='__main__':
    report=optimize();(R/'Art/Source/final-optimization-changes.json').write_text(json.dumps(report,indent=2)+'\n')
    bpy.ops.wm.save_as_mainfile(filepath=str(R/'Art/Source/OptimizedWorkshop.blend'))
    a=sum(r['before']*r['instances'] for r in report);b=sum(r['after']*r['instances'] for r in report)
    print('OPTIMIZED',a,b,round(100*(a-b)/a,1))
    for r in sorted(report,key=lambda r:(r['before']-r['after'])*r['instances'],reverse=True)[:20]:print(r)
