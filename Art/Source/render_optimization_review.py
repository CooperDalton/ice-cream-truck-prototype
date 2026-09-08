"""Render the same close-up before and after optimization."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
for label,path in [('Before',R/'Art/Source/BeforeFinalOptimization.blend'),('After',R/'Art/Source/OptimizedWorkshop.blend')]:
    if '--after-only' in sys.argv and label=='Before':continue
    bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene
    for c in scene.collection.children:c.hide_render=not c.name.startswith(('A •','Z •'))
    c=bpy.data.collections['Z • Review lighting and camera']
    for ob in c.objects:
        if ob.get('review_only'):ob.hide_render=True
    cam=scene.camera;r=bpy.data.objects['PreparationSet_ROOT'];cam.location=r.location+Vector((3.7,-6,4.2));target=r.location+Vector((.25,0,.95));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.2
    scene.render.resolution_x=1800;scene.render.resolution_y=1200;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True;scene.render.filepath=str(R/'Art/Previews'/f'Optimization_{label}.png');bpy.ops.render.render(write_still=True)
