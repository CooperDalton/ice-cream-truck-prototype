"""Space the review displays for easy browsing in the open Blender session."""
import bpy
from mathutils import Vector
scene=bpy.data.scenes['Art style review 2']
bpy.context.window.scene=scene
display=bpy.data.collections['Round2 display copies and labels']
rows={'Stand':0,'Waffle iron':1,'Serving bowl':2,'Scooper':3}
for obj in display.objects:
    if obj.instance_type=='COLLECTION':
        kind=obj.name.split(' / ')[1]
        obj.location.y=-rows[kind]*4.7
    elif obj.type=='FONT':
        if obj.data.body in {'SOFT TOY TOWN','CEL CARTOON'}:
            obj.location.y=0
            obj.location.z=3.25
            obj.rotation_euler.x=1.57079632679
        else:
            kind=next(kind for kind in rows if obj.data.body.startswith(kind.upper()))
            obj.location.y=-rows[kind]*4.7-1.7
scene.camera.location=(2,-30,27)
scene.camera.rotation_euler=(Vector((0,-7,.6))-scene.camera.location).to_track_quat('-Z','Y').to_euler()
scene.camera.data.ortho_scale=19
area=bpy.context.area
area.type='VIEW_3D'
area.spaces.active.region_3d.view_perspective='CAMERA'
area.spaces.active.region_3d.view_camera_zoom=10
bpy.context.window.scene=bpy.data.scenes['Ice cream truck workshop']
bpy.ops.wm.save_as_mainfile(filepath='C:/Users/wizdr/ice-cream-truck-prototype/Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend')
bpy.context.window.scene=scene
