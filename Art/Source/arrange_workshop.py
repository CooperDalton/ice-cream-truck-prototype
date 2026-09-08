"""Keep the full model set close together and visible in the master workshop."""
import bpy
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');scene=bpy.context.scene
positions={
'IceCreamTruck_ROOT':(1.5,1.1,0),'PreparationSet_ROOT':(-4.2,-2.1,0),
'Crew_ROOT':(-4.4,-4.0,0),'Adult_ROOT':(-2.35,-4.0,0),'AdultVariant_ROOT':(-.3,-4.0,0),
'Child_ROOT':(1.55,-4.0,0),'ChildVariant_ROOT':(3.20,-4.0,0),'FirstPersonHands_ROOT':(4.65,-4.0,.15),
'House_Cottage_ROOT':(-10.5,7.2,0),'House_Townhouse_ROOT':(-3.5,7.2,0),
'House_Bungalow_ROOT':(3.5,7.2,0),'House_Family_ROOT':(10.5,7.2,0),
'Tree_Broadoak_ROOT':(-8.4,.45,0),'Tree_Slenderpoplar_ROOT':(-5.5,1.5,0),
'Tree_Tieredpine_ROOT':(7.0,-.3,0),'Tree_Roundmaple_ROOT':(9.9,1.0,0)}
for name,p in positions.items():bpy.data.objects[name].location=p
for c in scene.collection.children:c.hide_viewport=False;c.hide_render=False
# Reveal every asset collection in the working view.
def reveal(layer):
    layer.exclude=False;layer.hide_viewport=False
    for c in layer.children:reveal(c)
reveal(bpy.context.view_layer.layer_collection)
for c in scene.collection.children:
    if c.name.startswith('Z'):continue
    for o in c.all_objects:
        if not o.name.startswith('Raw batter'):o.hide_set(False);o.hide_render=False
studio=bpy.data.collections['Z • Review lighting and camera']
for o in studio.objects:
    if o.type!='CAMERA':o.hide_set(True)
bpy.data.objects['Truck interior review fill'].location=(2.85,2.0,3.12)
cam=scene.camera;cam.location=(12,-26,19);target=Vector((.6,2.4,2.15))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=33.5
scene.render.resolution_x=2400;scene.render.resolution_y=1450;scene.render.resolution_percentage=100
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False
            sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=25
            sp.region_3d.view_location=target;sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.region_3d.view_distance=28
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
scene['workflow']='All assets belong in this master scene, grouped closely beside the truck. Save the overview so the full set is visible on opening.'
bpy.context.view_layer.update()
assert all(name in scene.objects for name in positions)
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for c in scene.collection.children:
    if c!=studio:
        for o in c.all_objects:
            if not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports/WorkshopModels.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
print('ALL_16_ASSET_ROOTS_VISIBLE_IN_SHARED_SCENE')
