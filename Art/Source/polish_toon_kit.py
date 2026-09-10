"""Finish the cream swirl and light the saved review pages."""
import ast,bpy,bmesh,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Art/Previews/ToonKit'
entries=json.loads((OUT/'inventory.json').read_text())
scene=bpy.data.scenes['Toon kit - all models'];bpy.context.window.scene=scene
gallery=bpy.data.collections['N - Toon tycoon model kit'];scene.collection.children.link(gallery)
for filename,names in [('build_art_style_review.py',{'color','material','mesh'}),('build_art_style_round2.py',{'lathe'}),('build_toon_kit.py',{'tube'})]:
    tree=ast.parse((ROOT/'Art/Source'/filename).read_text())
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))
style='Cel';materials={}
entry=next(e for e in entries if e['name']=='Whipped cream serving layer')
current=bpy.data.collections[entry['collection']];root=bpy.data.objects[entry['root']]
for o in list(current.objects):
    if o!=root:bpy.data.objects.remove(o,do_unlink=True)
white=material('Whipped cream final','FFF6DF')
lathe('Soft cream center',[(0,.004),(.023,.007),(.024,.018),(.019,.032),(.008,.052),(0,.066)],white,segments=40)
coords=[]
for i in range(110):
    t=i/109;a=t*math.tau*3.1;r=.029*(1-t)
    coords.append((r*math.cos(a),r*math.sin(a),.015+.052*t))
tube('Piped cream spiral',coords,[.012*(1-.82*i/109) for i in range(110)],white)
bpy.context.view_layer.update()
points=[o.matrix_world@Vector(c)-root.location for o in current.objects if o.type=='MESH' for c in o.bound_box]
lo=Vector(tuple(min(p[a] for p in points) for a in range(3)));hi=Vector(tuple(max(p[a] for p in points) for a in range(3)))
entry['bounds_m']=[list(lo),list(hi)];entry['display_scale']=2.1/max(hi-lo)
current.instance_offset=root.location+Vector((0,0,lo.z))
for o in bpy.data.objects:
    if o.instance_type=='COLLECTION' and o.instance_collection==current:o.scale=(entry['display_scale'],)*3
scene.collection.children.unlink(gallery)
inst=bpy.data.objects['Display / '+entry['name']]
for o in bpy.data.collections['Toon kit display copies'].objects:o.hide_render=o!=inst
target=inst.location+(lo+hi)/2*entry['display_scale'];target.z-=lo.z*entry['display_scale']
cam=scene.camera;cam.location=target+Vector((6,-10,7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.65
for o in bpy.data.collections['Toon kit studio'].objects:
    if o.type=='LIGHT':
        o.location=target+Vector((-5,-7,10) if 'Key' in o.name else (6,-3,6))
        o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/entry['preview']);bpy.ops.render.render(write_still=True)
for o in bpy.data.collections['Toon kit display copies'].objects:o.hide_render=False
target=Vector((15.3,-14,0));cam.location=target+Vector((0,-32,43));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=39
for o in bpy.data.collections['Toon kit studio'].objects:
    if o.type=='LIGHT':
        o.location=(-1,-5,12) if 'Key' in o.name else (12,-10,10)
        o.data.energy=3800 if 'Key' in o.name else 2600;o.data.size=10
        o.rotation_euler=(Vector((5,-5,0))-o.location).to_track_quat('-Z','Y').to_euler()
for s in bpy.data.scenes:
    if not s.name.startswith('Toon kit - ') or s==scene:continue
    bpy.context.window.scene=s;bpy.context.view_layer.update()
    for o in s.objects:
        if o.type=='FONT':o.data.size=.16
    camera=s.camera
    center=Vector((camera.location.x-2,camera.location.y+14,camera.location.z-21))
    camera.location=center+Vector((3,-17,19));camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.ortho_scale*=1.04
page=bpy.data.scenes['Toon kit - start here'];bpy.context.window.scene=page;bpy.context.view_layer.update()
page.render.filepath=str(OUT/'BlenderReview.png');bpy.ops.render.render(write_still=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Additions.blend'),compress=True)
(OUT/'inventory.json').write_text(json.dumps(entries,indent=2))
print('TOON_REVIEW_POLISHED')
