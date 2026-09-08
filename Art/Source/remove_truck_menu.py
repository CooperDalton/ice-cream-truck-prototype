"""Remove the three-cone menu panel, including a separated copy in the live master."""
import bpy,bmesh,json,shutil
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend';report=[]
for file in [master,R/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend',R/'Art/Source/RoomierTruck.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.view_layer.update()
    shutil.copy2(file,R/'Art/Source'/('BeforeMenuRemoval_'+file.stem+'.blend'))
    truck=bpy.data.objects['IceCreamTruck_ROOT'];parts=0;removed=0
    for ob in list(truck.children_recursive):
        if ob.type!='MESH':continue
        t=truck.matrix_world.inverted() @ ob.matrix_world;bm=bmesh.new();bm.from_mesh(ob.data);remaining=set(bm.verts);matches=[]
        while remaining:
            seed=remaining.pop();group={seed};todo=[seed]
            while todo:
                v=todo.pop()
                for e in v.link_edges:
                    w=e.other_vert(v)
                    if w in remaining:remaining.remove(w);group.add(w);todo.append(w)
            if all(3.06<(t@v.co).x<3.44 and -2.10<(t@v.co).y<-1.99 and 1.99<(t@v.co).z<2.77 for v in group):matches.append(group)
        if matches:
            verts=set().union(*matches);parts+=len(matches);removed+=len(verts)
            if len(verts)==len(bm.verts):bpy.data.objects.remove(ob,do_unlink=True)
            else:
                bmesh.ops.delete(bm,geom=list(verts),context='VERTS');bm.to_mesh(ob.data);ob.data.update()
        bm.free()
    assert parts==11 and removed==255,(file,parts,removed)
    report.append({'file':str(file),'panel_components_removed':parts,'vertices_removed':removed})
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
for filename,cols in [('IceCreamTruck',[bpy.data.collections['B • Ice cream truck']]),('WorkshopModels',[c for c in scene.collection.children if not c.name.startswith('Z')])]:
    bpy.ops.object.select_all(action='DESELECT')
    for c in cols:
        for o in c.all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{filename}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
(R/'Art/Source/menu-removal-verification.json').write_text(json.dumps(report,indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
for c in scene.collection.children:c.hide_render=not c.name.startswith(('B •','Z •'))
cam=scene.camera;truck=bpy.data.objects['IceCreamTruck_ROOT'];cam.location=truck.matrix_world@Vector((7,-10,4.5));target=truck.matrix_world@Vector((2.4,-1.8,2.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.5
scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.filepath=str(R/'Art/Previews/Truck_Menu_Removed.png');bpy.ops.render.render(write_still=True)
print('MENU_REMOVED',json.dumps(report))
