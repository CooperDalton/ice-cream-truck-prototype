"""Preserve the live edits, restore compatible optimized meshes, and enlarge the road kit."""
import bpy,json,runpy,hashlib,array,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
def fingerprint(me):
    a=array.array('f',[0])*len(me.vertices)*3;me.vertices.foreach_get('co',a);b=array.array('i',[0])*len(me.loops);me.loops.foreach_get('vertex_index',b)
    return hashlib.sha256(a.tobytes()+b.tobytes()+bytes(p.use_smooth for p in me.polygons)).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/BeforeFinalOptimization.blend'))
baseline={o.name:fingerprint(o.data) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/BeforeLargerRoads_Disk.blend'))
optimized={o.name:{'hash':fingerprint(o.data),'materials':[m.name if m else None for m in o.data.materials],'slots':[(s.link,s.material.name if s.material else None) for s in o.material_slots]} for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/BeforeLargerRoads_Live.blend'))
original_objects=set(bpy.data.objects);materials={m.name:m for m in bpy.data.materials};live={o.name:o for o in bpy.context.scene.objects};transforms={o.name:o.matrix_world.copy() for o in bpy.context.scene.objects}
names=[n for n,o in live.items() if o.type=='MESH' and n in baseline and n in optimized and fingerprint(o.data)==baseline[n] and optimized[n]['hash']!=baseline[n]]
with bpy.data.libraries.load(str(R/'Art/Source/BeforeLargerRoads_Disk.blend'),link=False) as (src,dst):dst.objects=list(names)
for n,source in zip(names,dst.objects):
    ob=live[n];ob.data=source.data;meta=optimized[n]
    for i,name in enumerate(meta['materials']):ob.data.materials[i]=materials[name] if name else None
    for i,(kind,name) in enumerate(meta['slots']):ob.material_slots[i].link=kind;ob.material_slots[i].material=materials[name] if name else None
for ob in list(bpy.data.objects):
    if ob not in original_objects:bpy.data.objects.remove(ob,do_unlink=True)
scene=bpy.context.scene;scene['geometry_audit']='Retained compatible meshes from final optimization while preserving live edits.'
report={'optimized_mesh_instances_restored':len(names),'resized_tiles':runpy.run_path(str(R/'Art/Source/enlarge_road_tiles.py'))['enlarge_tiles']()}
# Confirm all other model transforms survive the resize and layout adjustment.
roadroots=set(o.name for o in bpy.data.collections['G • Modular ground'].objects if o.parent is None)
for n,matrix in transforms.items():
    ob=bpy.data.objects[n];parent=ob
    while parent.parent:parent=parent.parent
    if parent.name in roadroots:continue
    assert max(abs(ob.matrix_world[i][j]-matrix[i][j]) for i in range(4) for j in range(4))<1e-5,n
# Frame the full-size library, keeping every asset in the master scene.
cam=scene.camera;cam.location=(42,-92,76);cam.rotation_euler=(Vector((4,-19,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO'
scene.render.resolution_x=2800;scene.render.resolution_y=1700;scene.render.resolution_percentage=100;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
bpy.context.view_layer.update();q=cam.rotation_euler.to_quaternion();inv=q.inverted();points=[inv @ (o.matrix_world @ Vector(v)) for c in scene.collection.children if not c.name.startswith('Z') for o in c.all_objects if o.type=='MESH' and not o.hide_render for v in o.bound_box]
low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)));center=(low+high)/2;cam.location=q @ Vector((center.x,center.y,high.z+100));cam.data.ortho_scale=max(high.x-low.x,(high.y-low.y)*2800/1700)*1.07
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=8;sp.overlay.show_overlays=False
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
bpy.ops.wm.save_as_mainfile(filepath=str(master))
exports={'IceCreamPreparation':['A • Preparation models'],'IceCreamTruck':['B • Ice cream truck'],'Characters':['C • Characters','D • First-person hands'],'Neighborhood':['E • Houses','F • Trees'],'RoadAndParkKit':['G • Modular ground','H • Park and street props'],'RemainingProps':['I • Supplies and handheld props','J • Delivery bike and stand'],'WorkshopModels':[c.name for c in scene.collection.children if not c.name.startswith('Z')]}
for name,groups in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for g in groups:
        for o in bpy.data.collections[g].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{name}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
(R/'Art/Source/larger-road-tiles.json').write_text(json.dumps(report,indent=2)+'\n')
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
# Temporary driving-scale view. Keep the saved truck arrangement unchanged.
for c in scene.collection.children:c.hide_render=not c.name.startswith(('B •','G •','Z •'))
for o in bpy.data.collections['Z • Review lighting and camera'].objects:
    if o.get('review_only'):o.hide_render=True
truck=bpy.data.objects['IceCreamTruck_ROOT'];road=bpy.data.objects['Road_Straight_ROOT'];truck.location=road.location+Vector((-3,0,0));truck.rotation_euler.z=math.pi/2
for n in ['ServingHatch_HINGE','DriverDoor_HINGE','PassengerDoor_HINGE','RearEntryDoor_HINGE']:bpy.data.objects[n].rotation_euler=(0,0,0)
bpy.context.view_layer.update()
cam.location=road.location+Vector((21,-28,24));target=road.location+Vector((2,0,1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=31;scene.render.resolution_x=1800;scene.render.resolution_y=1400;scene.render.filepath=str(R/'Art/Previews/Road_Truck_Scale.png');bpy.ops.render.render(write_still=True)
print('LARGER_ROADS_SAVED',json.dumps(report))
