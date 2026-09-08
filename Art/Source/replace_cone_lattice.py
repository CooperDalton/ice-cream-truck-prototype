"""Replace raised cone lattice throughout current assets, preserving all roots."""
import bpy,json,runpy
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');helper=runpy.run_path(str(R/'Art/Source/flat_waffle_cone.py'));helper['write_texture']()
master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
paths=[master,R/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend',R/'Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend',R/'Art/Source/RoomierTruck.blend']
report=[]
for path in paths:
    bpy.ops.wm.open_mainfile(filepath=str(path));mesh=helper['build_cone_mesh']()
    cones=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(s in o.name for s in ['FinishedCone_ROOT_Mesh','EmptyCone_ROOT_Mesh'])]
    assert len(cones)==(9 if path==master else 4 if 'SimulatorModels' in path.name else 5)
    before=[]
    for o in cones:
        o.data.calc_loop_triangles();before.append({'object':o.name,'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles)})
        o.data=mesh;o.material_slots[0].link='DATA'
        assert not o.modifiers
    report.append({'file':str(path),'instances':len(cones),'before':before,'after_each':{'vertices':80,'triangles':156,'materials':1}})
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
exports={'IceCreamPreparation':['A • Preparation models'],'IceCreamTruck':['B • Ice cream truck'],'WorkshopModels':[c.name for c in scene.collection.children if not c.name.startswith('Z')]}
for file,groups in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for name in groups:
        for o in bpy.data.collections[name].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/(file+'.glb')),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT');scene.cycles.samples=24
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
# Show the empty cone and all three scoop counts using the saved geometry.
for col in scene.collection.children:
    col.hide_render=not col.name.startswith(('A •','Z •'))
prep=bpy.data.objects['PreparationSet_ROOT'];target=prep.matrix_world @ Vector((.10,-.39,1.20));cam=scene.camera
cam.location=target+Vector((.55,-2.0,.65));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=1.73
scene.render.resolution_x=1800;scene.render.resolution_y=1100
scene.render.filepath=str(R/'Art/Previews/Cones_Flat_Texture.png');bpy.ops.render.render(write_still=True)
(R/'Art/Source/cone-texture-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('FLAT_CONES_SAVED',json.dumps(report))
