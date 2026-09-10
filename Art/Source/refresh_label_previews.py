import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Art/Previews/ToonKit'
audit=json.loads((ROOT/'Art/Previews/PeopleStudy/append-audit.json').read_text())
changed={e['collection'] for e in audit['cleared_numeric_model_labels']}
inventory=json.loads((OUT/'inventory.json').read_text())
for scene in bpy.data.scenes:bpy.context.window.scene=scene;bpy.context.view_layer.update()
scene=bpy.data.scenes['Toon kit - all models'];bpy.context.window.scene=scene
scene.render.resolution_x=720;scene.render.resolution_y=600;scene.render.resolution_percentage=100
display=bpy.data.collections['Toon kit display copies'];stage=bpy.data.collections['Toon kit studio'];cam=scene.camera
rendered=[]
for entry in inventory:
    if entry['collection'] not in changed:continue
    col=bpy.data.collections[entry['collection']];inst=bpy.data.objects['Display / '+entry['name']]
    for obj in display.objects:obj.hide_render=obj!=inst
    bpy.context.view_layer.update()
    points=[inst.location+(obj.matrix_world@Vector(c)-col.instance_offset)*entry['display_scale'] for obj in col.objects if obj.type in {'MESH','FONT'} and (obj.type!='FONT' or obj.data.body) for c in obj.bound_box]
    target=Vector(tuple((min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)))
    cam.location=target+Vector((6,-10,7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    rot=cam.rotation_euler.to_matrix().transposed();p=[rot@(v-target) for v in points]
    cam.data.ortho_scale=max(max(v.x for v in p)-min(v.x for v in p),(max(v.y for v in p)-min(v.y for v in p))*1.2)*1.16
    for light in stage.objects:
        if light.type=='LIGHT':
            light.location=target+Vector((-5,-7,10) if 'Key' in light.name else (6,-3,6));light.data.energy=1400 if 'Key' in light.name else 650;light.data.size=5
            light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/entry['preview']);bpy.ops.render.render(write_still=True);rendered.append(entry['name'])
for obj in display.objects:obj.hide_render=False
for light in stage.objects:
    if light.type=='LIGHT':
        light.location=(-1,-5,12) if 'Key' in light.name else (12,-10,10);light.data.energy=3800 if 'Key' in light.name else 2600;light.data.size=10
        light.rotation_euler=(Vector((5,-5,0))-light.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.data.scenes['Toon kit - start here'];bpy.context.window.scene=scene;scene.render.filepath=str(OUT/'BlenderReview.png');bpy.ops.render.render(write_still=True)
(ROOT/'Art/Previews/PeopleStudy/refreshed-label-previews.json').write_text(json.dumps(rendered,indent=2));print('LABEL_PREVIEWS_REFRESHED',len(rendered))
