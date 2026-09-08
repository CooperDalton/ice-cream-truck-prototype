"""Replace overlapping park slabs while preserving the rest of the workshop."""
import bpy, bmesh, runpy, json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
root=bpy.data.objects['Park_Cell_ROOT']
old=[bpy.data.objects[n] for n in ('Park path north south','Park path east west')]
report={'before':[{ 'name':o.name,'top_z':max((o.matrix_local@v.co).z for v in o.data.vertices)} for o in old]}
unchanged={o.name:o.matrix_world.copy() for o in scene.objects if o not in old}
mat=old[0].data.materials[0]
obj=runpy.run_path(str(R/'Art/Source/park_path_mesh.py'))['create_park_path'](root,old[0].users_collection[0],mat,root['grid_size_m'],root['path_width_m'])
for o in old:bpy.data.objects.remove(o,do_unlink=True)
bpy.context.view_layer.update()
for name,matrix in unchanged.items():
    assert max(abs(bpy.data.objects[name].matrix_world[i][j]-matrix[i][j]) for i in range(4) for j in range(4))<1e-6,name
bm=bmesh.new();bm.from_mesh(obj.data)
assert all(e.is_manifold for e in bm.edges)
assert not obj.data.validate()
bm.free()
obj.data.calc_loop_triangles()
top=[t for t in obj.data.loop_triangles if all(abs(obj.data.vertices[i].co.z-.092)<1e-6 for i in t.vertices)]
area=sum(t.area for t in top)
expected=2*root['grid_size_m']*root['path_width_m']-root['path_width_m']**2
assert abs(area-expected)<1e-4,(area,expected)
report.update({'top_area_m2':area,'expected_union_area_m2':expected,'vertices':len(obj.data.vertices),'triangles':len(obj.data.loop_triangles),'manifold':True,'other_transforms_preserved':len(unchanged)})
master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(master))
# Reopen the saved artifact before checking and exporting it.
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
assert 'Park path north south' not in scene.objects
assert 'Park path east west' not in scene.objects
assert len(bpy.data.objects['Park continuous crossing'].data.polygons)==14
for name,groups in [('RoadAndParkKit',['G • Modular ground','H • Park and street props']),('WorkshopModels',[c.name for c in scene.collection.children if not c.name.startswith('Z')])]:
    bpy.ops.object.select_all(action='DESELECT')
    for g in groups:
        for o in bpy.data.collections[g].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{name}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
(R/'Art/Source/park-crossing-fix.json').write_text(json.dumps(report,indent=2)+'\n')
# Render a close view without altering the saved review layout.
root=bpy.data.objects['Park_Cell_ROOT'];keep={root,*root.children_recursive}
for o in scene.objects:
    if o.type=='MESH' and o not in keep:o.hide_render=True
cam=scene.camera;cam.location=root.location+Vector((19,-26,22));target=root.location+Vector((0,0,.1));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=32
scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.filepath=str(R/'Art/Previews/Park_Crossing_Fixed.png');bpy.ops.render.render(write_still=True)
print('PARK_CROSSING_FIXED',json.dumps(report))
