"""Combine the preserved live prep scene and truck into one review scene."""
import bpy, runpy
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
scene.name='Ice cream truck workshop'
assert 'PreparationSet_ROOT' not in bpy.data.objects, 'Workshop is already combined.'
runpy.run_path(str(ROOT/'Art/Source/add_scoop_variants.py'))['add_variants']()
prep_collections=[c for c in scene.collection.children if c.name[:2] in ['01','02','03','04','05','06','07','08','09']]
prep_group=bpy.data.collections.new('A • Preparation models');scene.collection.children.link(prep_group)
prep_root=bpy.data.objects.new('PreparationSet_ROOT',None);prep_group.objects.link(prep_root)
prep_root.location=(-4.5,-1.1,0)
prep_root.empty_display_size=.2
for c in prep_collections:
    prep_group.children.link(c);scene.collection.children.unlink(c)
    c.hide_viewport=False;c.hide_render=False
    for o in list(c.all_objects):
        if o.parent is None:o.parent=prep_root
        if not o.name.startswith('Raw batter portion'):
            o.hide_set(False);o.hide_viewport=False;o.hide_render=False
with bpy.data.libraries.load(str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend'),link=False) as (src,dst):
    dst.collections=[name for name in src.collections if name[:2] in ['10','11','12','13','14','15','16','17','18']]
truck_group=bpy.data.collections.new('B • Ice cream truck');scene.collection.children.link(truck_group)
for c in dst.collections:
    truck_group.children.link(c)
truck=bpy.data.objects['IceCreamTruck_ROOT']
truck.location=(1.7,1.3,0)
# Shared studio for both full-scale sets.
studio=next(c for c in scene.collection.children if c.name.startswith('99'))
studio.name='Z • Review lighting and camera'
for o in studio.objects:
    if o.type=='LIGHT':
        if 'Key' in o.name:o.location=(-7,-7,10);o.data.energy=2400;o.data.size=7
        elif 'Fill' in o.name:o.location=(6,-2,9);o.data.energy=2000;o.data.size=6
        else:o.location=(1,7,10);o.data.energy=2400;o.data.size=6
        o.rotation_euler=(Vector((-.5,.3,1.2))-o.location).to_track_quat('-Z','Y').to_euler()
cam=scene.camera
cam.location=(-10.5,-15.8,10.5)
cam.rotation_euler=(Vector((-.8,.10,1.55))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=13.7
scene.render.resolution_x=1900;scene.render.resolution_y=1100
scene.render.resolution_percentage=100;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.filepath=str(ROOT/'Art/Previews/Workshop_All_Models.png')
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL';a.spaces.active.overlay.show_overlays=False
            a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.region_3d.view_camera_zoom=8
        elif a.type=='OUTLINER':a.spaces.active.display_mode='VIEW_LAYER'
# Ensure previously collapsed or hidden collections can be inspected in the combined view.
def reveal(layer):
    layer.exclude=False;layer.hide_viewport=False
    for child in layer.children:reveal(child)
reveal(bpy.context.view_layer.layer_collection)
bpy.ops.object.select_all(action='DESELECT')
scene['master_model_scene']=True
scene['workflow']='Keep new models in this scene, organized by collection and displayed side by side.'
bpy.context.view_layer.update()
assert truck.name in scene.objects and prep_root.name in scene.objects
assert len([o for o in prep_root.children_recursive if o.type=='EMPTY' and o.name.startswith('Tub_')])==12
assert all(n in scene.objects for n in ['Cone_2Scoops_ROOT','Cone_3Scoops_ROOT','IceCreamTruck_ROOT'])
print('VERIFIED one scene: full truck and standalone prep set with all three scoop counts')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
bpy.ops.render.render(write_still=True)
