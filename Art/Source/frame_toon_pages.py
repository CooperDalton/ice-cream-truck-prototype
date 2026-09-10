import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
for scene in bpy.data.scenes:
    if not scene.name.startswith('Toon kit - ') or scene.name.endswith('all models'):continue
    bpy.context.window.scene=scene
    instances=[o for o in scene.objects if o.instance_type=='COLLECTION']
    for o in instances:o.location.y*=1.25
    for o in scene.objects:
        if o.type=='FONT':o.location.y=(o.location.y+1.3)*1.25-1.5
    xmin=min(o.location.x for o in instances)-1.6;xmax=max(o.location.x for o in instances)+1.6
    ymin=min(o.location.y for o in instances)-1.8;ymax=max(o.location.y for o in instances)+1.4
    center=Vector(((xmin+xmax)/2,(ymin+ymax)/2,.55))
    cam=scene.camera;cam.location=center+Vector((1.5,-20,23));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
    rotation=cam.rotation_euler.to_matrix().transposed()
    points=[rotation@(Vector((x,y,z))-center) for x in [xmin,xmax] for y in [ymin,ymax] for z in [0,2.3]]
    cam.data.ortho_scale=max(max(v.x for v in points)-min(v.x for v in points),(max(v.y for v in points)-min(v.y for v in points))*1600/1100)*1.04
    bpy.context.view_layer.update()
scene=bpy.data.scenes['Toon kit - start here'];bpy.context.window.scene=scene
scene.render.filepath=str(ROOT/'Art/Previews/ToonKit/BlenderReview.png');bpy.ops.render.render(write_still=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Additions.blend'),compress=True)
