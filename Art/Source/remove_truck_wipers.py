"""Remove only the four disconnected wiper parts from the joined truck shell."""
import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
report=[]
for file in [master,R/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend',R/'Art/Source/RoomierTruck.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.view_layer.update()
    truck=bpy.data.objects['IceCreamTruck_ROOT'];body=bpy.data.objects['BodyShell_ROOT_Mesh']
    transform=truck.matrix_world.inverted() @ body.matrix_world
    bm=bmesh.new();bm.from_mesh(body.data);remaining=set(bm.verts);matches=[]
    while remaining:
        seed=remaining.pop();group={seed};todo=[seed]
        while todo:
            v=todo.pop()
            for e in v.link_edges:
                other=e.other_vert(v)
                if other in remaining:remaining.remove(other);group.add(other);todo.append(other)
        p=[transform @ v.co for v in group]
        if all(-3.51<v.x<-3.23 and .50<abs(v.y)<1.35 and 1.90<v.z<2.55 for v in p):matches.append(group)
    assert len(matches)==4,(str(file),len(matches))
    verts=set().union(*matches);before=len(bm.verts)
    bmesh.ops.delete(bm,geom=list(verts),context='VERTS');bm.to_mesh(body.data);bm.free()
    assert before-len(body.data.vertices)==len(verts)
    report.append({'file':str(file),'wiper_parts_removed':4,'vertices_removed':len(verts)})
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
# Export from the preserved live master, including its other current edits.
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
for file,groups in [('IceCreamTruck',['B • Ice cream truck']),('WorkshopModels',[c.name for c in scene.collection.children if not c.name.startswith('Z')])]:
    bpy.ops.object.select_all(action='DESELECT')
    for name in groups:
        for o in bpy.data.collections[name].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/(file+'.glb')),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
for c in scene.collection.children:c.hide_render=not c.name.startswith(('B •','Z •'))
cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=10.5;cam.location=(-8,-11,6.9)
cam.rotation_euler=(Vector((1.7,1.3,1.85))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1800;scene.render.resolution_y=1200
scene.render.filepath=str(R/'Art/Previews/Truck_05_Roomier_Exterior.png');bpy.ops.render.render(write_still=True)
(R/'Art/Source/wiper-removal-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('WIPERS_REMOVED',json.dumps(report))
