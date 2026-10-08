import bpy, math
from mathutils import Vector
sc = bpy.data.scenes["PS1 game assets"]
cd = bpy.data.cameras.new("tmp overview"); cd.lens = 28; cd.clip_end = 2000
cam = bpy.data.objects.new("tmp overview", cd); sc.collection.objects.link(cam)
for name, loc, target in (("rows_small", (760, -150, 120), (760, -60, 0)), ("rows_env", (1000, -420, 260), (900, -230, 0))):
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = 1800, 1000
    sc.render.filepath = f"/tmp/artstyle/v2/out/assets/master_{name}.png"
    bpy.ops.render.render(write_still=True, scene=sc.name)
