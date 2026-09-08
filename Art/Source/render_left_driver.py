import bpy,bmesh
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');scene=bpy.context.scene;t=bpy.data.objects['IceCreamTruck_ROOT'];bpy.context.view_layer.update()
o=bpy.data.objects['BodyShell_ROOT_Mesh'];transform=t.matrix_world.inverted()@o.matrix_world
bm=bmesh.new();bm.from_mesh(o.data);remaining=set(bm.verts);removed=[]
while remaining:
 v=remaining.pop();g={v};q=[v]
 while q:
  v=q.pop()
  for e in v.link_edges:
   w=e.other_vert(v)
   if w in remaining:remaining.remove(w);g.add(w);q.append(w)
 if all((transform@v.co).z>3.05 and (transform@v.co).x<-.60 for v in g):removed+=list(g)
print('TEMPORARY_ROOF_CUTAWAY',len(removed));assert removed
bmesh.ops.delete(bm,geom=removed,context='VERTS');bm.to_mesh(o.data);bm.free()
for c in scene.collection.children:c.hide_render=not c.name.startswith(('B •','Z •'))
for o in bpy.data.objects['Roof_ROOT • hide for interior view'].children_recursive:o.hide_render=True
cam=scene.camera;cam.location=t.matrix_world@Vector((.4,-.25,4.5));target=t.matrix_world@Vector((-1.9,0,1.3));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.8
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.filepath=str(R/'Art/Previews/Truck_Left_Hand_Drive.png');bpy.ops.render.render(write_still=True)
