"""Build eight additional Soft/Cel studies as an appendable Blender library."""
import ast
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Previews/ArtStyleRound2'
OUT.mkdir(parents=True, exist_ok=True)

# Reuse the exact materials and mesh helpers from the first comparison.
source = ast.parse((ROOT / 'Art/Source/build_art_style_review.py').read_text())
helpers = {'color', 'material', 'mesh', 'box', 'blob', 'branch', 'rounded_points', 'tub'}
exec(compile(ast.Module(body=[n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in helpers], type_ignores=[]), '<round-one-helpers>', 'exec'))
materials = {}
style = ''
current = root = None
scene = bpy.data.scenes.new('Art style review 2')
bpy.context.window.scene = scene
gallery = bpy.data.collections.new('M - Soft and Cel shop props')
scene.collection.children.link(gallery)


def start(kind, position):
    global current, root
    current = bpy.data.collections.new(f'Round2 {style} - {kind}')
    gallery.children.link(current)
    root = bpy.data.objects.new(f'ArtReview2_{style}_{kind}_ROOT', None)
    current.objects.link(root)
    root.location = position
    root['style'] = style
    root['asset_type'] = kind
    root['review_only'] = True


def lathe(name, profile, mat, location=(0, 0, 0), segments=48):
    vertices = [(r*math.cos(i*math.tau/segments), r*math.sin(i*math.tau/segments), z)
                for r, z in profile for i in range(segments)]
    faces = [(j*segments+i, j*segments+(i+1)%segments, (j+1)*segments+(i+1)%segments, (j+1)*segments+i)
             for j in range(len(profile)-1) for i in range(segments)]
    obj = mesh(name, vertices, faces, mat)
    obj.location = location
    return obj


def text_label(name, text, position, size, mat, rotation=(math.pi/2, 0, 0)):
    data = bpy.data.curves.new(name, 'FONT')
    data.body = text
    data.align_x = 'CENTER'
    data.align_y = 'CENTER'
    data.size = size
    data.extrude = size * .017
    data.bevel_depth = size * .005
    obj = bpy.data.objects.new(name, data)
    current.objects.link(obj)
    obj.parent = root
    obj.location = position
    obj.rotation_euler = rotation
    data.materials.append(mat)
    return obj


def palette():
    return [material('Warm vanilla', 'FFF0D4', .47), material('Strawberry pink', 'E681A5', .46),
            material('Mint enamel', '79BCAA', .43), material('Plum rubber', '51415C', .8),
            material('Brushed steel', 'BDCED7', .3)]


def stand():
    global root
    vanilla, pink, mint, plum, steel = palette()
    box('Rounded cabinet', (0, 0, .5), (2.0, .90, .9), mint, .13 if style == 'Soft' else .07)
    box('Cream front panel', (0, -.459, .52), (1.73, .055, .65), vanilla, .11)
    box('Pink nameplate', (0, -.501, .57), (1.22, .065, .34), pink, .10)
    text_label('SCOOP shop sign', 'SCOOP', (0, -.540, .57), .215, vanilla)
    for x in [-.70, .70]:
        blob('Badge dot', (x, -.499, .57), (.04, .016, .04), pink, 3)
    box('Plum toe rail', (0, -.005, .12), (1.9, .92, .14), plum, .06)
    for x in [-.83, .83]:
        for y in [-.3, .3]:
            box('Rubber foot', (x, y, .055), (.18, .18, .11), plum, .04)
    # The top is built around the two open tubs.
    box('Front serving ledge', (0, -.415, 1.00), (2.26, .40, .15), vanilla, .065)
    box('Rear rim', (0, .485, 1.00), (2.26, .15, .15), vanilla, .05)
    for x, width in [(-.985, .29), (0, .28), (.985, .29)]:
        box('Counter divider', (x, .105, 1.0), (width, .73, .15), vanilla, .035)
    for x in [-.95, .95]:
        branch('Canopy post', (x, .34, 1.02), (x, .34, 2.26), .047, .047, mint)
        blob('Post cap', (x, .34, 2.28), (.072, .072, .072), vanilla, 3)
    for i in range(8):
        x1 = -1.2 + .3*i
        ys = [-.70 + 1.40*j/20 for j in range(21)]
        profile = [(y, 2.19 + .37*math.sin(math.pi*(y+.7)/1.4)) for y in ys]
        if style == 'Cel':
            profile = [(-.7, 2.19), (0, 2.58), (.7, 2.19)]
        vertices = [(x, y, z) for x in [x1, x1+.3] for y, z in profile]
        n = len(profile)
        o = mesh('Canopy stripe', vertices, [(j, j+1, n+j+1, n+j) for j in range(n-1)], pink if i%2==0 else vanilla)
        mod = o.modifiers.new('Cloth thickness', 'SOLIDIFY')
        mod.thickness = .024
        # Rounded scallops read clearly against the open serving space.
        points = [(x1, -.708, 2.20), (x1+.3, -.708, 2.20)]
        points += [(x1+.3-k*.3/16, -.708, 2.12-.08*math.sin(math.pi*k/16)) for k in range(17)]
        flap = mesh('Scalloped valance', points, [tuple(range(len(points)))], pink if i%2==0 else vanilla, smooth=False)
        mod = flap.modifiers.new('Valance thickness', 'SOLIDIFY')
        mod.thickness = .021
    stand_root = root
    for i, x in enumerate([-.49, .49]):
        root = bpy.data.objects.new(f'ArtReview2_{style}_Stand flavor {i}', None)
        current.objects.link(root)
        root.parent = stand_root
        root.location = (x, .10, .733)
        root.scale = (1.65, 1.95, 1.4)
        tub()
        if i == 1:
            flavor = material('Vanilla ice cream', 'FFE5B2', .65)
            for obj in root.children:
                if 'Ice cream fill' in obj.name:
                    obj.data.materials[0] = flavor
        root = stand_root


def waffle_iron():
    global root
    vanilla, pink, mint, plum, steel = palette()
    charcoal = material('Cooking plate', '454151', .88)
    rib = material('Cooking ribs', '635A6D', .72)
    for x in [-.14, .14]:
        for y in [-.13, .13]:
            box('Foot', (x, y, .018), (.07, .075, .035), plum, .013)
    lathe('Rounded pink housing', [(0,.033),(.19,.033),(.233,.056),(.237,.096),(.22,.12),(0,.12)], pink)
    lathe('Cream gasket', [(0,.112),(.222,.112),(.225,.13),(.218,.141),(0,.141)], vanilla)

    def plate(center_z, underside=False):
        lathe('Cooking plate', [(0,center_z-.007),(.2,center_z-.007),(.203,center_z+.002),(.2,center_z+.009),(0,center_z+.009)], charcoal)
        z = center_z-.009 if underside else center_z+.011
        for axis in range(2):
            for i in range(-4,5):
                a = i*.039
                length = 2*math.sqrt(.187**2-a*a)
                dims = (.009,length,.007) if axis==0 else (length,.009,.007)
                loc = (a,0,z) if axis==0 else (0,a,z)
                box('Waffle grid', loc, dims, rib, .002)
    plate(.15)
    box('Control panel', (0,-.225,.095), (.21,.035,.05), plum,.014)
    for x,mat in [(-.051,pink),(.051,material('Ready light','AED56F'))]:
        blob('Indicator light',(x,-.247,.098),(.013,.005,.013),mat,3)
    appliance = root
    root = bpy.data.objects.new(f'ArtReview2_{style}_WaffleIron_Lid_HINGE',None)
    current.objects.link(root)
    root.parent = appliance
    root.location=(0,.19,.17)
    root.rotation_euler.x=math.radians(-108)
    root['closed_angle_degrees']=0
    root['open_angle_degrees']=-108
    lid = root
    lathe('Top rounded housing',[(0,.0),(.20,.0),(.227,.023),(.235,.06),(.20,.085),(0,.085)],pink)
    plate(-.007,True)
    for obj in list(lid.children):
        obj.location.y-=.19
    for x in [-.11,.11]:
        box('Handle mount',(x,-.40,.046),(.043,.1,.049),steel,.012)
    box('Chunky insulated handle',(0,-.459,.046),(.32,.069,.065),mint,.028 if style=='Soft' else .018)
    root=appliance
    branch('Rear hinge pin',(-.14,.19,.17),(.14,.19,.17),.025,.025,steel)


def serving_bowl():
    vanilla,pink,mint,plum,steel=palette()
    lathe('Paper bowl',[(0,0),(.052,0),(.058,.008),(.079,.063),(.082,.066),(.083,.072),(.078,.075),(.073,.068),(.051,.009),(0,.009)],pink)
    lathe('Cream band',[(.065,.025),(.0704,.039)],vanilla)
    lathe('Rolled rim',[(.078,.066),(.083,.068),(.083,.073),(.08,.076),(.076,.073),(.076,.069),(.078,.066)],vanilla)
    scoops=[]
    for flavor,x,y,z,mat in [('Vanilla',-.032,.006,.103,material('Vanilla ice cream','FFE5B2')),
                            ('Strawberry',.033,-.012,.109,material('Strawberry ice cream','F3A6BA'))]:
        scoop=blob(flavor+' scoop',(x,y,z),(.051,.049,.048),mat,4)
        for v in scoop.data.vertices:
            v.co*=1+.035*math.sin(v.co.x*240+v.co.y*170)*math.cos(v.co.z*210)
        scoop.data.update()
        scoops.append(scoop)
        for i in range(9):
            a=i*math.tau/9
            blob('Scoop ruffle',(x+.041*math.cos(a),y+.039*math.sin(a),z-.023),(.013,.012,.011),mat,2)
    bpy.context.view_layer.update()
    for i in range(15):
        a=i*2.4
        scoop=scoops[i%2]
        hit,point,normal,_=scoop.ray_cast((.027*math.cos(a),.024*math.sin(a),.09),(0,0,-1))
        assert hit
        position=scoop.location+point+normal*.001
        o=box('Sprinkle',position,(.008,.0025,.0024),[mint,pink,vanilla][i%3],.0009)
        o.rotation_euler=normal.to_track_quat('Z','Y').to_euler()
        o.rotation_euler.z+=a


def scooper():
    vanilla,pink,mint,plum,steel=palette()
    box('Rounded mint grip',(0,-.077,.047),(.046,.145,.046),mint,.02 if style=='Soft' else .014)
    box('Soft thumb pad',(0,-.028,.070),(.030,.054,.010),pink,.009)
    for y in [-.104,-.084,-.064]:
        box('Grip groove',(0,y,.0704),(.031,.0025,.002),vanilla,.001)
    branch('Steel neck',(0,-.004,.047),(0,.071,.056),.010,.010,steel)
    lathe('Open scoop head',[(0,-.033),(.022,-.028),(.039,-.016),(.047,0),(.045,.004),(.041,.003),(.034,-.015),(.017,-.025),(0,-.026)],steel,(0,.111,.071),64)
    branch('Thumb lever',(.02,-.019,.048),(.028,.060,.047),.004,.004,steel)
    box('Thumb lever end',(.032,-.009,.048),(.017,.03,.007),pink,.005)
    for obj in root.children:
        obj.location.z-=.024


assets=[]
builders=[('Stand',stand,1.0),('Waffle iron',waffle_iron,4.2),('Serving bowl',serving_bowl,13),('Scooper',scooper,10)]
for column,style_name in enumerate(['Soft','Cel']):
    style=style_name
    for row,(kind,builder,display_scale) in enumerate(builders):
        start(kind,(96+column*6,-row*4,0))
        builder()
        assets.append((style,kind,current,root,display_scale))

# Outline shells belong only to the cel study.
style='Cel'
ink=material('Plum outline','493A57')
ink.use_backface_culling=True
ink.use_backface_culling_shadow=True
bpy.context.view_layer.update()
depsgraph=bpy.context.evaluated_depsgraph_get()
for st,kind,col,r,scale in assets:
    if st!='Cel':
        continue
    for obj in list(col.objects):
        if obj.type!='MESH' or 'Ice cream fill' in obj.name or (len(obj.data.polygons)<5 and not obj.modifiers):
            continue
        data=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        for v in data.vertices:
            v.co+=v.normal*(.006 if kind=='Stand' else .0006 if kind=='Waffle iron' else .00025)
        bm=bmesh.new();bm.from_mesh(data)
        bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        data.materials.clear();data.materials.append(ink)
        for p in data.polygons:p.material_index=0
        obj_copy=bpy.data.objects.new(obj.name+' outline',data)
        col.objects.link(obj_copy)
        obj_copy.parent=obj.parent
        obj_copy.matrix_basis=obj.matrix_basis.copy()
        obj_copy['review_outline']=True

# Display instances enlarge the tools without changing the modeled dimensions.
display=bpy.data.collections.new('Round2 display copies and labels')
scene.collection.children.link(display)
instances=[]
for st,kind,col,r,scale in assets:
    col.instance_offset=r.location
    o=bpy.data.objects.new(f'{st} / {kind} / display',None)
    display.objects.link(o)
    o.instance_type='COLLECTION';o.instance_collection=col
    o.location=(-2.2 if st=='Soft' else 2.2,-builders.index(next(b for b in builders if b[0]==kind))*4.7,0)
    o.scale=(scale,)*3
    instances.append(o)
scene.collection.children.unlink(gallery)
scene.render.engine='BLENDER_EEVEE'
scene.eevee.taa_render_samples=128
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.world=bpy.data.worlds.new('Round2 studio world')
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.37,.48,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
stage=bpy.data.collections.new('Round2 studio')
scene.collection.children.link(stage)
current=stage
root=bpy.data.objects.new('Round2 stage root',None);stage.objects.link(root)
style='Studio'
floor=box('Review floor',(0,-4,-.09),(60,60,.14),material('Warm background','EAE4D9'),0)
cam_data=bpy.data.cameras.new('Round2 camera')
cam=bpy.data.objects.new(cam_data.name,cam_data);stage.objects.link(cam);scene.camera=cam
cam.data.type='ORTHO';cam.data.clip_start=.001
lights=[]
for name,loc,energy,size in [('Key',(-5,-7,10),1400,5),('Fill',(6,-3,6),650,6)]:
    data=bpy.data.lights.new('Round2 '+name,'AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);stage.objects.link(obj)
    lights.append((obj,Vector(loc)))


def frame(target,ortho):
    cam.location=target+Vector((7,-12,7.8))
    cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=ortho
    for obj,offset in lights:
        obj.location=target+offset
        obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()


report=[]
for i,(st,kind,col,r,scale) in enumerate(assets):
    for j,o in enumerate(instances):o.hide_render=j!=i
    bpy.context.view_layer.update()
    points=[instances[i].location+(obj.matrix_world@Vector(corner)-r.location)*scale
            for obj in col.objects if obj.type in {'MESH','FONT'} for corner in obj.bound_box]
    minimum=Vector(tuple(min(p[axis] for p in points) for axis in range(3)))
    maximum=Vector(tuple(max(p[axis] for p in points) for axis in range(3)))
    target=(minimum+maximum)/2
    frame(target,1)
    inverse_rotation=cam.rotation_euler.to_matrix().transposed()
    projected=[inverse_rotation@(p-target) for p in points]
    width=max(p.x for p in projected)-min(p.x for p in projected)
    height=max(p.y for p in projected)-min(p.y for p in projected)
    cam.data.ortho_scale=max(width,height*1.25)*1.15
    scene.render.filepath=str(OUT/f'{st}_{kind.replace(" ","_")}.png')
    bpy.ops.render.render(write_still=True)
    report.append({'style':st,'asset':kind,'root':r.name,'display_scale':scale})
for o in instances:o.hide_render=False
frame(Vector((0,-7,.6)),19)
cam.location=(2,-30,27)
cam.rotation_euler=(Vector((0,-7,.6))-cam.location).to_track_quat('-Z','Y').to_euler()
for obj,offset in lights:
    obj.location=Vector((0,-4,0))+offset*1.5
    obj.data.energy*=2.25
    obj.data.size*=1.5
    obj.rotation_euler=(Vector((0,-4,0))-obj.location).to_track_quat('-Z','Y').to_euler()

current=display
root=bpy.data.objects.new('Round2 labels',None);display.objects.link(root)
label_mat=material('Label ink','51415C')
for st,x in [('SOFT TOY TOWN',-2.2),('CEL CARTOON',2.2)]:
    text_label(st,st,(x,0,3.25),.3,label_mat)
for row,(kind,_,scale) in enumerate(builders):
    for x in [-2.2,2.2]:
        label=kind.upper()+(' / DISPLAY x'+str(scale) if scale!=1 else '')
        text_label(label,label,(x,-row*4.7-1.7,.012),.17,label_mat,rotation=(0,0,0))
scene['review_note']='Soft left, Cel right. Tools enlarged for inspection; source models stay at real scale in collection M.'
bpy.context.preferences.filepaths.save_version=0
bpy.data.libraries.write(str(ROOT/'Art/Source/ArtStyleRound2_Additions.blend'),{scene,gallery},fake_user=True,compress=True)
(OUT/'audit.json').write_text(json.dumps(report,indent=2))
print('ROUND2_COMPLETE: eight models, render comparisons, and an appendable review scene.')
