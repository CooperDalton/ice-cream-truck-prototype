"""Save the verified candidate, synchronize asset copies, and refresh all exports."""
import bpy,runpy,shutil,json,hashlib
from pathlib import Path
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
assert hashlib.sha256(master.read_bytes()).digest()==hashlib.sha256((R/'Art/Source/BeforeFinalOptimization.blend').read_bytes()).digest(), 'The saved master changed during the audit.'
optimize=runpy.run_path(str(R/'Art/Source/optimize_workshop_geometry.py'))['optimize'];copies=[]
for file in [R/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend',R/'Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend',R/'Art/Source/RoomierTruck.blend']:
    bpy.ops.wm.open_mainfile(filepath=str(file));shutil.copy2(file,R/'Art/Source'/('BeforeFinalOptimization_'+file.stem+'.blend'));changes=optimize();copies.append({'file':str(file),'changes':changes});bpy.ops.wm.save_as_mainfile(filepath=str(file))
bpy.ops.wm.open_mainfile(filepath=str(R/'Art/Source/OptimizedWorkshop.blend'));scene=bpy.context.scene
scene['geometry_audit']='Final optimization: degenerate and coplanar cleanup, lighter scoops, holders, tubs and wheels. Character rigs, anchors, flat cone texture and left-hand drive preserved.'
bpy.ops.wm.save_as_mainfile(filepath=str(master))
exports={'IceCreamPreparation':['A • Preparation models'],'IceCreamTruck':['B • Ice cream truck'],'Characters':['C • Characters','D • First-person hands'],'Neighborhood':['E • Houses','F • Trees'],'RoadAndParkKit':['G • Modular ground','H • Park and street props'],'RemainingProps':['I • Supplies and handheld props','J • Delivery bike and stand'],'WorkshopModels':[c.name for c in scene.collection.children if not c.name.startswith('Z')]}
for name,groups in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for group in groups:
        for ob in bpy.data.collections[group].all_objects:
            if not ob.hide_render:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{name}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
(R/'Art/Source/final-optimization-copy-sync.json').write_text(json.dumps(copies,indent=2)+'\n')
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
print('OPTIMIZED_MASTER_COPIES_AND_ALL_EXPORTS_SAVED')
