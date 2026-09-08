import bpy,runpy
from pathlib import Path
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');fix=runpy.run_path(str(R/'Art/Source/restore_authored_flat_faces.py'))['restore_flat_faces']
master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
pairs=[(R/'Art/Source/BeforeFinalOptimization.blend',master),(R/'Art/Source/BeforeFinalOptimization.blend',R/'Art/Source/OptimizedWorkshop.blend')]
for name,path in [('IceCreamTruck',R/'Ice Cream Truck Prototype/Assets'),('IceCreamTruckSimulatorModels',R/'Ice Cream Truck Prototype/Assets'),('RoomierTruck',R/'Art/Source')]:pairs.append((R/'Art/Source'/f'BeforeFinalOptimization_{name}.blend',path/f'{name}.blend'))
for before,after in pairs:
    bpy.ops.wm.open_mainfile(filepath=str(before));original={o.name:([v.co.copy() for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[p.use_smooth for p in o.data.polygons]) for o in bpy.context.scene.objects if o.type=='MESH' and not any(m.type=='ARMATURE' for m in o.modifiers) and not o.data.name.startswith('Shared flat-textured waffle cone') and not all(p.use_smooth for p in o.data.polygons)}
    bpy.ops.wm.open_mainfile(filepath=str(after));seen=set()
    for name,data in original.items():
        ob=bpy.data.objects[name]
        if ob.data in seen:continue
        seen.add(ob.data);fix(ob.data,*data)
    bpy.ops.wm.save_as_mainfile(filepath=str(after))
bpy.ops.wm.open_mainfile(filepath=str(master));scene=bpy.context.scene
exports={'IceCreamPreparation':['A • Preparation models'],'IceCreamTruck':['B • Ice cream truck'],'Characters':['C • Characters','D • First-person hands'],'Neighborhood':['E • Houses','F • Trees'],'RoadAndParkKit':['G • Modular ground','H • Park and street props'],'RemainingProps':['I • Supplies and handheld props','J • Delivery bike and stand'],'WorkshopModels':[c.name for c in scene.collection.children if not c.name.startswith('Z')]}
for name,groups in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for group in groups:
        for ob in bpy.data.collections[group].all_objects:
            if not ob.hide_render:ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{name}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT');scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
print('AUTHORED_FLAT_FACES_RESTORED')
