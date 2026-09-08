"""Assemble the roomier truck, toy characters, and lighter meshes."""
import bpy,bmesh,runpy,math,json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');scene=bpy.context.scene
# The live session had the prep and truck. Preserve its prep edits, then restore
# the later environment collections from the disk snapshot.
def remove_collection(c):
    for o in list(c.all_objects):bpy.data.objects.remove(o,do_unlink=True)
    def remove(c):
        for ch in list(c.children):remove(ch)
        bpy.data.collections.remove(c)
    remove(c)
for c in list(scene.collection.children):
    if c.name.startswith(('B •','C •','D •')):remove_collection(c)
with bpy.data.libraries.load(str(R/'Art/Source/BeforeTruckCharacterRevision_Disk.blend'),link=False) as (src,dst):
    dst.collections=[n for n in src.collections if n.startswith(('E •','F •')) and n not in bpy.data.collections]
for c in dst.collections:scene.collection.children.link(c)
with bpy.data.libraries.load(str(R/'Art/Source/RoomierTruck.blend'),link=False) as (src,dst):
    dst.collections=[n for n in src.collections if n[:2] in ['10','11','12','13','14','15','16','17','18']]
truckcol=bpy.data.collections.new('B • Ice cream truck');scene.collection.children.link(truckcol)
for c in dst.collections:truckcol.children.link(c)
truck=bpy.data.objects['IceCreamTruck_ROOT'];truck.location=(1.7,1.3,0)
bpy.context.view_layer.update()
# Remove the baked counter wordmarks by their original local placement.
removed_wordmark_vertices=0
for col in [bpy.data.collections['A • Preparation models'],truckcol]:
    for o in col.all_objects:
        if o.type=='MESH' and o.name.startswith('PrepCounter_ROOT_Mesh'):
            o.data=o.data.copy();bm=bmesh.new();bm.from_mesh(o.data)
            local=o.parent.matrix_world.inverted() @ o.matrix_world
            letters=[v for v in bm.verts if abs((local @ v.co).x)<.40 and -.4205<(local @ v.co).y<-.418 and .64<(local @ v.co).z<.74]
            assert len(letters)>50,(o.name,len(letters))
            removed_wordmark_vertices+=len(letters)
            bmesh.ops.delete(bm,geom=letters,context='VERTS');bm.to_mesh(o.data);bm.free()
scene['removed_counter_wordmark_vertices']=removed_wordmark_vertices
# Simplify baked decorative geometry. Preserve shared mesh data and material slots.
processed={}
for col in [bpy.data.collections['A • Preparation models'],truckcol]:
    for o in col.all_objects:
        if o.type!='MESH':continue
        original=o.data
        if col==truckcol and o not in set(bpy.data.objects['InteriorEquipment_ROOT'].children_recursive) and not o.name.startswith('RoofSign_'):continue
        if original in processed:o.data=processed[original];continue
        original.calc_loop_triangles();n=len(original.loop_triangles)
        if n<450:continue
        ratio=min(1,1600/n) if n>4000 else .48
        # Keep the primary truck shell more detailed than the hand props.
        if o.name.startswith('BodyShell_ROOT_Mesh'):ratio=min(1,6500/n)
        old_slots=[(s.link,s.material) for s in o.material_slots]
        o.data=original.copy();processed[original]=o.data
        bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o
        mod=o.modifiers.new('Reduce decorative geometry','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        for i,(link,mat) in enumerate(old_slots):o.material_slots[i].link=link;o.material_slots[i].material=mat
        processed[original]=o.data
# Use the shared flat texture on cones after simplifying the preserved inputs.
cone_mesh=runpy.run_path(str(R/'Art/Source/flat_waffle_cone.py'))['build_cone_mesh']()
for o in scene.objects:
    if o.type=='MESH' and any(n in o.name for n in ['FinishedCone_ROOT_Mesh','EmptyCone_ROOT_Mesh']):
        o.data=cone_mesh;o.material_slots[0].link='DATA'
# Group static environment pieces into one mesh per asset, with editable materials.
for group in ['E • Houses','F • Trees']:
    col=bpy.data.collections[group]
    for root in [o for o in col.all_objects if o.parent is None]:
        meshes=[o for o in root.children_recursive if o.type=='MESH']
        for o in meshes:
            bpy.context.view_layer.objects.active=o
            for mod in list(o.modifiers):
                if mod.type=='BEVEL':mod.segments=1
                bpy.ops.object.modifier_apply(modifier=mod.name)
            # Flatten the hierarchy without changing placement.
            mw=o.matrix_world.copy();o.parent=root;o.matrix_world=mw
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join();meshes[0].name=root.name.replace('_ROOT','_Mesh')
        if group.startswith('E'):
            for p in meshes[0].data.polygons:p.use_smooth=True
            normal=meshes[0].modifiers.new('Weighted smooth house normals','WEIGHTED_NORMAL');normal.keep_sharp=True;normal.weight=50
            bpy.ops.object.modifier_apply(modifier=normal.name)
        for o in list(root.children_recursive):
            if o.type=='EMPTY':bpy.data.objects.remove(o,do_unlink=True)
runpy.run_path(str(R/'Art/Source/build_round_characters.py'))
# Restore all visible asset groups, retaining the alternate raw batter state hidden.
for c in scene.collection.children:
    c.hide_render=False;c.hide_viewport=False
for o in scene.objects:
    if o.type=='MESH' and not o.name.startswith(('Raw batter','Studio floor')):o.hide_set(False)
studio=bpy.data.collections['Z • Review lighting and camera']
for o in studio.all_objects:
    if o.type=='LIGHT' and o.data.type=='AREA':
        if 'Key' in o.name:o.location=(-12,-9,17);o.data.energy=5500;o.data.size=11
        elif 'Fill' in o.name:o.location=(12,-2,14);o.data.energy=4500;o.data.size=10
        else:o.location=(1,15,16);o.data.energy=6000;o.data.size=10
        o.rotation_euler=(Vector((0,4,2))-o.location).to_track_quat('-Z','Y').to_euler()
if not any(o.type=='LIGHT' and o.data.type=='SUN' for o in studio.objects):
    d=bpy.data.lights.new('Neighborhood soft sunlight','SUN');d.energy=1.5;d.angle=.24
    o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.rotation_euler=(.45,-.5,-.4)
d=bpy.data.lights.new('Truck interior review fill','AREA');d.energy=150;d.shape='DISK';d.size=2.0
o=bpy.data.objects.new(d.name,d);studio.objects.link(o);o.location=(3.05,2.2,3.12)
cam=scene.camera

def camera(pos,target,scale,w=2000,h=1300):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
    scene.render.resolution_x=w;scene.render.resolution_y=h

def render(name):
    scene.render.filepath=str(R/'Art/Previews'/name);bpy.ops.render.render(write_still=True)

def only(groups):
    for c in scene.collection.children:c.hide_render=c!=studio and c.name not in groups

scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_percentage=100
camera((16,-31,25),(.7,3,2),39,2400,1500)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL';a.spaces.active.overlay.show_overlays=False
            a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.region_3d.view_camera_zoom=4
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
# Export each family and the full set. Studio objects and hidden raw batter are excluded.
exports={'IceCreamPreparation':['A • Preparation models'],'IceCreamTruck':['B • Ice cream truck'],'Characters':['C • Characters','D • First-person hands'],'Neighborhood':['E • Houses','F • Trees'],'WorkshopModels':[c.name for c in scene.collection.children if c!=studio]}
for name,groups in exports.items():
    bpy.ops.object.select_all(action='DESELECT')
    for group in groups:
        for o in bpy.data.collections[group].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/(name+'.glb')),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
render('Workshop_All_Models.png')
only(['C • Characters','D • First-person hands']);camera((.4,-14,3.7),(.4,-4.5,1.02),12.4,2400,1000);render('Characters_04_Round_Lineup.png')
only(['B • Ice cream truck']);camera((-8,-11,6.9),(1.7,1.3,1.85),10.5,1800,1200);render('Truck_05_Roomier_Exterior.png')
# Look straight through the physical serving opening from customer height.
camera((2.9,-8,2.8),(2.9,2.1,1.95),5.9,1600,1200);render('Truck_06_Serving_Window.png')
# A roof-off view makes the aisle and the opposite-wall counter easy to inspect.
roof=bpy.data.objects['Roof_ROOT • hide for interior view']
for o in roof.children_recursive:o.hide_render=True
camera((8,-5,11),(2.2,1.4,1),9.4,1700,1300);render('Truck_07_Open_Floorplan.png')
# Interior eye-level view uses the actual roof and side walls.
for o in roof.children_recursive:o.hide_render=False
cam.data.type='PERSP';cam.data.lens=20;cam.location=(4.15,1.3,2.2);cam.rotation_euler=(Vector((1.1,1.0,1.95))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1600;scene.render.resolution_y=1100;render('Truck_08_Interior.png')
print('WORKSHOP_REVISION_COMPLETE')
