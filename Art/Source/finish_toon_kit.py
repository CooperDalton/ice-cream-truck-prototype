"""Fit the upgraded cargo rack and make separate, readable Blender review pages."""
import ast
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Art/Previews/ToonKit'
inventory=json.loads((OUT/'inventory.json').read_text())
gallery=bpy.data.collections.get('N - Toon tycoon model kit')
if gallery is None:
    gallery=bpy.data.collections.new('N - Toon tycoon model kit')
    for entry in inventory:gallery.children.link(bpy.data.collections[entry['collection']])
gallery.use_fake_user=True
scene=bpy.data.scenes['Toon kit - all models']
bpy.context.window.scene=scene
scene.collection.children.link(gallery)
for filename,names in [('build_art_style_review.py',{'color','material','mesh','box','blob','branch'}),('build_art_style_round2.py',{'text_label','lathe'}),('build_toon_kit.py',{'bowl','scoop_piece','tube','container','cooled','anchor','ring'})]:
    tree=ast.parse((ROOT/'Art/Source'/filename).read_text())
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))
style='Cel';materials={}
cream=material('Kit finish vanilla','FFF0D4');mint=material('Kit finish mint','79BCAA');pink=material('Kit finish pink','E681A5')
plum=material('Kit finish plum','51415C');steel=material('Kit finish steel','BDCED7');white=material('Kit finish whip','FFF6DF')
changed_names=[]


def rebuild(name):
    global current,root
    entry=next(e for e in inventory if e['name']==name)
    current=bpy.data.collections[entry['collection']];root=bpy.data.objects[entry['root']]
    for o in list(current.objects):
        if o!=root:bpy.data.objects.remove(o,do_unlink=True)
    changed_names.append(name)


for name,count in [('Empty bowl',1),('Bowl stack 12',12),('One scoop bowl',1),('Bowl dispenser 30',30)]:
    rebuild(name)
    if count==30:
        box('Dispenser foot',(0,0,.025),(.24,.24,.05),mint,.025)
        for x in [-.10,.10]:branch('Stack guide',(x,.02,.05),(x,.02,.47),.008,.008,steel)
    for i in range(count):bowl((0,0,(.05+i*.0105) if count==30 else i*.013))
    if name=='One scoop bowl':scoop_piece('Vanilla','FFEAC0',(0,0,.062))
    anchor('TAKE',(0,-.12,.15)) if count==30 else anchor('GRIP',(0,0,.03))
for name,h in [('Sprinkles','E681A5'),('Cookie crumbs','B6917D'),('Chopped nuts','C3A471')]:
    rebuild(name+' dispenser');container(name,h,'dry',15)
for wells in [1,2]:
    rebuild(str(wells)+' well cooled module');cooled(wells)
for name,h in [('Chocolate sauce','815343'),('Caramel sauce','D99C53'),('Whipped cream','FFF6DF')]:
    rebuild(name+' serving layer')
    if name=='Whipped cream':
        coords=[]
        for i in range(90):
            t=i/89;a=t*math.tau*3.2;r=.032*(1-t)
            coords.append((r*math.cos(a),r*math.sin(a),.018+.075*t))
        tube('Cream swirl',coords,[.010*(1-i/96) for i in range(90)],white)
    else:
        for j in range(-2,3):
            coords=[]
            for k in range(14):
                y=-.038+k*.076/13;x=j*.016+.004*math.sin(k*.9);z=.042*math.sqrt(max(.05,1-(x/.058)**2-(y/.058)**2))
                coords.append((x,y,z))
            tube('Sauce drizzle',coords,[.0024]*14,material(name+' contents',h))
rebuild('Cone holder')
box('Stable holder base',(0,0,.015),(.22,.22,.03),mint,.025)
for x in [-.06,.06]:branch('Holder upright',(x,0,.027),(x,0,.18),.009,.009,steel)
ring('Cone support',(0,0,.18),.055,.009,pink);anchor('CONE',(0,0,.04));anchor('GRIP',(0,0,.08))
rebuild('Three cone rack')
box('Rack base',(0,0,.015),(.48,.23,.03),mint,.025)
for x in [-.15,0,.15]:
    branch('Rack post',(x,.06,.03),(x,.06,.19),.007,.007,steel)
    ring('Cone rack ring',(x,0,.19),.058,.007,pink);anchor('CONE_'+str(x),(x,0,.04))
bpy.data.objects['Toon_Waffle_iron_ROOT']['grid_footprint_m']=(.5,.75)
entry=next(e for e in inventory if e['name']=='Delivery bike 8 cargo')
current=bpy.data.collections[entry['collection']];root=bpy.data.objects[entry['root']]
# This also makes the finishing pass safe to run on a freshly rebuilt library.
if not any('Upper cargo tray' in o.name for o in current.objects):
    for o in list(current.objects):
        if 'Slot pad' in o.name:bpy.data.objects.remove(o,do_unlink=True)
    w=1.12;d=.68
    box('Upper cargo tray',(0,.64,1.225),(w,d,.045),cream,.018)
    for x in [-w/2,w/2]:
        for y in [.30,.98]:box('Upper tray support',(x,y,1.12),(.033,.033,.44),mint,.01)
    for x in [-w/2,w/2]:box('Upper cargo side',(x,.64,1.37),(.035,d,.26),mint,.017)
    for y in [.30,.98]:box('Upper cargo end',(0,y,1.37),(w,.035,.26),mint,.017)
    for i in range(8):
        x=-w/2+w*(i%2+.5)/2;y=.30+d*((i%4)//2+.5)/2;z=.924+(i//4)*.325
        o=next(o for o in current.objects if o.name.endswith('_CARGO_'+str(i+1)))
        o.location=(x,y,z)
        box('Slot pad',(x,y,z+.003),(w/2-.025,d/2-.025,.008),pink,.008)
# Add missing dry-ingredient content keys to the separate window meshes.
for col in gallery.children:
    for obj in col.objects:
        if obj.type=='MESH' and 'Contents window' in obj.name and 'outline' not in obj.name and not obj.data.shape_keys:
            obj.shape_key_add(name='Full');empty=obj.shape_key_add(name='Empty')
            for v in empty.data:v.co.z=-.013
            empty.value=0.0
            obj['empty_shape_key']='Empty'

bpy.context.view_layer.update()
for changed_name in changed_names:
    entry=next(e for e in inventory if e['name']==changed_name)
    col=bpy.data.collections[entry['collection']];r=bpy.data.objects[entry['root']]
    points=[o.matrix_world@Vector(c)-r.location for o in col.objects if o.type in {'MESH','FONT'} for c in o.bound_box]
    low=Vector(tuple(min(p[a] for p in points) for a in range(3)));high=Vector(tuple(max(p[a] for p in points) for a in range(3)))
    entry['bounds_m']=[list(low),list(high)];entry['display_scale']=2.1/max(high-low)
    col.instance_offset=r.location+Vector((0,0,low.z))
    bpy.data.objects['Display / '+changed_name].scale=(entry['display_scale'],)*3
entry=next(e for e in inventory if e['name']=='Delivery bike 8 cargo')
current.instance_offset=root.location
points=[o.matrix_world@Vector(c)-root.location for o in current.objects if o.type in {'MESH','FONT'} for c in o.bound_box]
lo=Vector(tuple(min(p[a] for p in points) for a in range(3)));hi=Vector(tuple(max(p[a] for p in points) for a in range(3)))
entry['bounds_m']=[list(lo),list(hi)];entry['display_scale']=2.1/max(hi-lo)
inst=bpy.data.objects['Display / '+entry['name']];inst.scale=(entry['display_scale'],)*3
scene.collection.children.unlink(gallery)
# Replace the wide initial review with a short page of representative assets.
old=bpy.data.scenes['Toon kit - start here'];bpy.data.scenes.remove(old)
stage=bpy.data.collections['Toon kit studio']
pages=[]
representatives=['Pop up stand','Expanded kiosk shell','12 slot locker','Waffle iron','Two scoop bowl','One swipe scooper','Strawberry tub','Chocolate sauce dispenser','Delivery bike 8 cargo','Ice cream truck','Expert employee','Supplier storefront']
groups=list(dict.fromkeys(e['group'] for e in inventory))
for title,names in [('start here',representatives)]+[(g,[e['name'] for e in inventory if e['group']==g]) for g in groups]:
    page=bpy.data.scenes.new('Toon kit - '+title);pages.append(page)
    bpy.context.window.scene=page
    page.collection.children.link(stage)
    page.world=scene.world;page.render.engine='BLENDER_EEVEE';page.eevee.taa_render_samples=64
    page.view_settings.view_transform='Standard';page.view_settings.look='None'
    page.render.resolution_x=1600;page.render.resolution_y=1100;page.render.resolution_percentage=100
    current=bpy.data.collections.new('Toon page '+title);page.collection.children.link(current)
    root=bpy.data.objects.new('Toon '+title+' labels',None);current.objects.link(root)
    labelmat=material('Kit labels','51415C')
    columns=4 if len(names)>6 else 2
    for i,name in enumerate(names):
        entry=next(e for e in inventory if e['name']==name)
        o=bpy.data.objects.new('Toon page '+title+' / '+name,None);current.objects.link(o)
        o.instance_type='COLLECTION';o.instance_collection=bpy.data.collections[entry['collection']]
        o.scale=(entry['display_scale'],)*3;o.location=((i%columns)*3.4,-(i//columns)*3.6,0)
        text_label('Page label',name.upper(),(o.location.x,o.location.y-1.3,.012),.115,labelmat,rotation=(0,0,0))
    rows=math.ceil(len(names)/columns)
    target=Vector(((columns-1)*1.7,-(rows-1)*1.8,.5))
    data=bpy.data.cameras.new('Toon '+title+' camera');data.type='ORTHO';data.clip_start=.001
    cam=bpy.data.objects.new(data.name,data);page.collection.objects.link(cam);page.camera=cam
    cam.location=target+Vector((2,-14,21));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    corners=[Vector((x,y,z)) for x in [-1.65,(columns-1)*3.4+1.65] for y in [1.4,-(rows-1)*3.6-1.6] for z in [0,2.5]]
    rotation=cam.rotation_euler.to_matrix().transposed();projected=[rotation@(p-target) for p in corners]
    data.ortho_scale=max(max(p.x for p in projected)-min(p.x for p in projected),(max(p.y for p in projected)-min(p.y for p in projected))*1600/1100)*1.06
    page['note']='Display copies are enlarged individually. Source models retain real dimensions in collection N.'
    if title=='start here':
        page.render.filepath=str(OUT/'BlenderReview.png');bpy.ops.render.render(write_still=True)

# Render every corrected asset through its existing individual preview camera.
bpy.context.window.scene=scene
for changed_name in changed_names+['Delivery bike 8 cargo']:
    entry=next(e for e in inventory if e['name']==changed_name)
    inst=bpy.data.objects['Display / '+changed_name];col=bpy.data.collections[entry['collection']]
    for obj in bpy.data.collections['Toon kit display copies'].objects:obj.hide_render=obj!=inst
    bpy.context.view_layer.update()
    points=[inst.location+(o.matrix_world@Vector(c)-col.instance_offset)*entry['display_scale'] for o in col.objects if o.type in {'MESH','FONT'} for c in o.bound_box]
    target=Vector(tuple((min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)))
    cam=scene.camera;cam.location=target+Vector((6,-10,7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    rotation=cam.rotation_euler.to_matrix().transposed();p=[rotation@(v-target) for v in points]
    cam.data.ortho_scale=max(max(v.x for v in p)-min(v.x for v in p),(max(v.y for v in p)-min(v.y for v in p))*1.2)*1.16
    for o in stage.objects:
        if o.type=='LIGHT':
            o.location=target+Vector((-5,-7,10) if 'Key' in o.name else (6,-3,6))
            o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(OUT/entry['preview']);bpy.ops.render.render(write_still=True)
for obj in bpy.data.collections['Toon kit display copies'].objects:obj.hide_render=False
target=Vector((15.3,-14,0));cam.location=target+Vector((0,-32,43));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=39
for o in stage.objects:
    if o.type=='LIGHT':
        o.location=(-5,-7,10) if 'Key' in o.name else (6,-3,6)
        o.rotation_euler=(Vector((4,-4,0))-o.location).to_track_quat('-Z','Y').to_euler()
for saved_scene in [scene,*pages]:
    bpy.context.window.scene=saved_scene
    bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Additions.blend'),compress=True)
(OUT/'inventory.json').write_text(json.dumps(inventory,indent=2))
print('TOON_KIT_FINISHED',len(inventory),'assets;',len(pages),'review pages')
