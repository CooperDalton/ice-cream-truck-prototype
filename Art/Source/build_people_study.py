"""Four new toon character silhouettes, each dressed as staff and a customer."""
import ast
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Art/Previews/PeopleStudy';OUT.mkdir(parents=True,exist_ok=True)
for filename,names in [('build_art_style_review.py',{'color','material','mesh','box','blob','branch'}),('build_art_style_round2.py',{'lathe','text_label'}),('build_toon_kit.py',{'tube'})]:
    tree=ast.parse((ROOT/'Art/Source'/filename).read_text())
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))
style='Cel';materials={};current=root=None
cream=material('People warm cream','FFF0D4');mint=material('People mint','79BCAA');pink=material('People strawberry','E681A5')
plum=material('People plum','51415C');skin=material('People warm skin','E5AD83');hair=material('People cocoa hair','704D48')
cheek=material('People cheek','D9877E');white=material('People eye white','FFF8E5');sole=material('People sole','D8C9B4')
scene=bpy.data.scenes.new('People - compare silhouettes');bpy.context.window.scene=scene
gallery=bpy.data.collections.new('O - Toon people alternatives');gallery.use_fake_user=True;scene.collection.children.link(gallery)
assets=[];parts={}


def tag(o,bone):
    parts[o]=bone
    return o


def orb(name,pos,dims,mat,bone,detail=3):
    return tag(blob(name,pos,dims,mat,detail),bone)


def cube(name,pos,dims,mat,bone,bevel=.04):
    return tag(box(name,pos,dims,mat,bevel),bone)


def rod(name,a,b,r1,r2,mat,bone):
    return tag(branch(name,a,b,r1,r2,mat),bone)


def stroke(name,coords,radius,mat,bone):
    return tag(tube(name,coords,[radius]*len(coords),mat),bone)


def torso(levels,mat,bone='Spine'):
    n=32;vertices=[];faces=[]
    for z,w,d in levels:
        for j in range(n):
            a=j*math.tau/n;vertices.append((w*math.cos(a),d*math.sin(a),z))
    for i in range(len(levels)-1):
        for j in range(n):faces.append((i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j))
    faces.extend([tuple(reversed(range(n))),tuple((len(levels)-1)*n+j for j in range(n))])
    return tag(mesh('Tailored torso',vertices,faces,mat),'Spine')


def hand(pos,sign,size):
    bone='Hand_'+('L' if sign<0 else 'R');x,y,z=pos
    orb('Mitten palm',pos,(.07*size,.048*size,.077*size),skin,bone)
    for j in range(3):orb('Rounded fingertip',(x+(j-1)*.035*size,y-.002,z-.047*size),(.026*size,.041*size,.036*size),skin,bone,2)
    orb('Thumb',(x-sign*.065*size,y-.02,z+.012*size),(.032*size,.036*size,.046*size),skin,bone,2)


def face(kind,hz,depth,width,staff):
    if kind=='Chunky comic':
        eyex=.105;eyez=hz+.025;fy=-depth-.004
        for sign in [-1,1]:
            orb('Eye white',(sign*eyex,fy,eyez),(.057,.016,.071),white,'Head')
            orb('Pupil',(sign*eyex+.004,fy-.017,eyez),(.026,.010,.041),plum,'Head')
            brow=cube('Strong eyebrow',(sign*eyex,fy,eyez+.102),(.115,.023,.031),hair,'Head',.010)
            brow.rotation_euler.y=sign*-.12
        cube('Chunky nose',(0,fy-.035,hz-.055),(.082,.083,.090),skin,'Head',.032)
        coords=[(x,fy-.006,hz-.139+.045*(x/.10)**2) for x in [-.10,-.075,-.05,-.025,0,.025,.05,.075,.10]]
        stroke('Grin',coords,.008,plum,'Head')
    else:
        eyex=.105 if kind!='Pocket people' else .115
        fy=-depth*math.sqrt(1-(eyex/width)**2)-.012
        for sign in [-1,1]:
            eye_dims=(.027,.018,.044) if kind=='Pocket people' else (.035,.022,.052)
            orb('Simple oval eye',(sign*eyex,fy,hz+.025),eye_dims,plum,'Head')
            orb('Eye glint',(sign*eyex-.007,fy-.018,hz+.041),(.008,.005,.011),white,'Head',2)
            if kind!='Pocket people':
                coords=[(sign*eyex-.043+i*.0215,fy+.019,hz+.102+.014*math.sin(i*math.pi/4)) for i in range(5)]
                stroke('Friendly eyebrow',coords,.009,hair,'Head')
            orb('Cheek',(sign*(eyex+.068),fy+.036,hz-.065),(.031,.010,.017),cheek,'Head',2)
        orb('Small nose',(0,-depth-.027,hz-.04),(.033,.039,.034),skin,'Head')
        coords=[(x,-depth*math.sqrt(max(.1,1-(x/width)**2))-.012,hz-.116+.032*(x/.077)**2) for x in [-.077,-.058,-.038,-.019,0,.019,.038,.058,.077]]
        stroke('Smile',coords,.0065,plum,'Head')


def headwear(kind,hz,hw,hd,hh,staff):
    if staff:
        orb('Hair at nape',(0,.054,hz+hh*.51),(hw*.97,hd*.91,hh*.46),hair,'Head')
        if kind=='Chunky comic':
            cube('Cap crown',(0,.018,hz+hh+.035),(hw*2.15,hd*2.2,.16),pink,'Head',.078)
            orb('Cap visor',(0,-hd*.83,hz+hh-.017),(hw*.99,hd*.73,.036),pink,'Head')
            orb('Cap button',(0,.018,hz+hh+.121),(.025,.025,.016),cream,'Head',2)
        else:
            orb('Cap crown',(0,.018,hz+hh*.79),(hw*1.04,hd*1.05,hh*.35),pink,'Head')
            orb('Cap visor',(0,-hd*.78,hz+hh*.69),(hw*.82,hd*.63,.037),pink,'Head')
            orb('Cap button',(0,.018,hz+hh*1.14),(.025,.025,.016),cream,'Head',2)
        # A small scoop badge keeps the uniform free of text and numbers.
        orb('Hat scoop badge',(0,-hd*.91,hz+hh*.88),(.030,.008,.029),cream,'Head',2)
    elif kind=='Pocket people':
        orb('Bob back',(0,.085,hz+.075),(hw*1.06,hd*.87,hh*.94),hair,'Head')
        for sign in [-1,1]:orb('Bob side',(sign*hw*.82,.018,hz-.035),(hw*.24,hd*.91,hh*.73),hair,'Head')
        for i in range(4):orb('Rounded fringe',((i-1.5)*hw*.41,-hd*.62,hz+hh*.67),(hw*.31,hd*.46,hh*.22),hair,'Head')
    elif kind=='Chunky comic':
        cube('Swept hair',(0,.018,hz+hh*.91),(hw*2.06,hd*1.92,.19),hair,'Head',.07)
        q=cube('Side swept quiff',(-hw*.18,-hd*.57,hz+hh*1.14),(hw*1.64,hd*.97,.17),hair,'Head',.065);q.rotation_euler.y=-.15
    else:
        orb('Hair cap',(0,.07,hz+hh*.58),(hw*1.02,hd*.97,hh*.53),hair,'Head')
        for i in range(3):orb('Swept fringe',(-hw*.55+i*hw*.45,-hd*.57,hz+hh*(.81-i*.09)),(hw*.44,hd*.49,hh*.29),hair,'Head')


def build_character(kind,staff):
    global current,root,parts
    role='Staff' if staff else 'Customer'
    current=bpy.data.collections.new('People / '+kind+' / '+role);gallery.children.link(current)
    root=bpy.data.objects.new('People_'+kind.replace(' ','_')+'_'+role+'_ROOT',None);current.objects.link(root)
    root.location=(300+len(assets)*3,0,0);root['style']='Cel cartoon';root['study']=kind;root['role']=role
    parts={};floating=kind=='Floating crew';short=kind=='Pocket people';angular=kind=='Chunky comic'
    hz,hw,hd,hh=(1.56,.255,.205,.30) if angular else (1.14,.375,.27,.33) if short else (1.43,.30,.225,.32) if floating else (1.44,.31,.235,.34)
    hip=.69 if angular else .44 if short else .27 if floating else .58
    shoulder=1.20 if angular else .82 if short else 1.03 if floating else 1.10
    tw=.27 if angular else .235 if short else .245 if floating else .26
    td=.165 if angular else .165 if short else .17 if floating else .17
    cloth=cream if staff else material(kind+' customer clothes',{'Rounded crew':'8CA6CA','Chunky comic':'B593C5','Pocket people':'E8B55D','Floating crew':'88B5A2'}[kind])
    torso([(hip,tw*.70,td*.87),(hip+.08,tw*.94,td),(shoulder-.20,tw,td),(shoulder-.055,tw*.98,td*.88),(shoulder+.03,tw*.62,td*.69)],cloth)
    orb('Neck',(0,0,shoulder+.087),(.09,.09,.13),skin,'Spine')
    if angular:
        cube('Rounded square head',(0,0,hz),(hw*2,hd*2,hh*2),skin,'Head',.115)
    else:
        orb('Cheek shaped head',(0,0,hz),(hw,hd,hh),skin,'Head',4)
    for sign in [-1,1]:orb('Ear',(sign*hw*.96,.015,hz-.025),(.047,.049,.069),skin,'Head',2)
    face(kind,hz,hd,hw,staff);headwear(kind,hz,hw,hd,hh,staff)
    if staff:
        # Curved apron follows the front of the torso without a floating oval panel.
        z0=hip+.07;z1=shoulder-.055;vertices=[];faces=[];n=16
        for z,r in [(z0,tw*.88),(z0+.08,tw*.97),(z1-.12,tw),(z1,tw*.91)]:
            for i in range(n+1):
                a=-math.pi*.80+i*math.pi*.60/n
                vertices.append((r*math.cos(a),td*math.sin(a)-.014,z))
        for j in range(3):
            for i in range(n):a=j*(n+1)+i;faces.append((a,a+1,a+n+2,a+n+1))
        apron=tag(mesh('Wrap apron',vertices,faces,mint),'Spine');apron.modifiers.new('Apron thickness','SOLIDIFY').thickness=.008
        for x in [-.11,.11]:rod('Apron strap',(x,-td*.78,shoulder+.015),(x,-td-.018,z1-.13),.016,.016,mint,'Spine')
        cube('Apron pocket',(0,-td-.022,hip+.21),(tw*.98,.02,.12),mint,'Spine',.025)
        stroke('Pocket seam',[(-tw*.45,-td-.037,hip+.252),(0,-td-.037,hip+.246),(tw*.45,-td-.037,hip+.252)],.0045,cream,'Spine')
    else:
        cube('Shirt collar',(0,-td*.72,shoulder+.014),(.15,.045,.055),cream,'Spine',.018)
        if kind=='Chunky comic':
            for x in [-.16,.16]:cube('Jacket pocket',(x,-td-.012,shoulder-.18),(.11,.024,.12),cloth,'Spine',.022)
    bones=[('Root',(0,0,0),(0,0,.15),None),('Spine',(0,0,hip),(0,0,shoulder),'Root'),('Head',(0,0,shoulder+.08),(0,0,hz+.15),'Spine')]
    for sign,side in [(-1,'L'),(1,'R')]:
        sh=(sign*tw*.92,0,shoulder-.025);el=(sign*(tw+.09),-.015,shoulder-.23);wr=(sign*(tw+.12),-.05,shoulder-.38)
        if short:el=(sign*(tw+.06),-.012,shoulder-.12);wr=(sign*(tw+.10),-.04,shoulder-.23)
        if floating:wr=(sign*.43,-.018,.84)
        if not floating:
            direction=Vector(el)-Vector(sh);length=direction.length
            sleeve=tag(lathe('Rounded short sleeve',[(0,-.070),(.044,-.052),(.071,-.027),(.084,0),(.079,length-.025),(.073,length),(0,length)],cloth,sh,32),'UpperArm_'+side)
            sleeve.rotation_euler=direction.to_track_quat('Z','Y').to_euler()
            orb('Elbow',el,(.059,.06,.06),skin,'Forearm_'+side,2)
            rod('Forearm',el,wr,.060,.052,skin,'Forearm_'+side)
            bones.extend([('UpperArm_'+side,sh,el,'Spine'),('Forearm_'+side,el,wr,'UpperArm_'+side)])
        hand((wr[0],wr[1],wr[2]-.055),sign,.86 if short else .94)
        bones.append(('Hand_'+side,wr,(wr[0],wr[1],wr[2]-.12),'Spine' if floating else 'Forearm_'+side))
        if not floating:
            x=sign*(.125 if not short else .115);knee=(x,0,hip*.54);ankle=(x,-.005,.15)
            rod('Trouser thigh',(x,0,hip+.015),knee,.103 if angular else .096,.087,plum,'Thigh_'+side)
            rod('Trouser shin',knee,ankle,.087,.082,plum,'Shin_'+side)
            cube('Chunky shoe',(x,-.060,.085),(.195,.33,.16),mint if staff else pink,'Foot_'+side,.057)
            cube('Cream shoe sole',(x,-.061,.022),(.199,.333,.043),sole,'Foot_'+side,.018)
            cube('Shoe strap',(x,-.155,.15),(.13,.052,.028),cream,'Foot_'+side,.011)
            bones.extend([('Thigh_'+side,(x,0,hip+.015),knee,'Root'),('Shin_'+side,knee,ankle,'Thigh_'+side),('Foot_'+side,ankle,(x,-.18,.08),'Shin_'+side)])
    data=bpy.data.armatures.new(root.name[:-5]+' rig');rig=bpy.data.objects.new(data.name,data);current.objects.link(rig);rig.parent=root
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for name,a,b,parent in bones:
        bone=data.edit_bones.new(name);bone.head=a;bone.tail=b
        if parent:bone.parent=data.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj,bone in parts.items():
        group=obj.vertex_groups.new(name=bone);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
        mod=obj.modifiers.new('Study rig','ARMATURE');mod.object=rig
    for side in ['L','R']:
        socket=bpy.data.objects.new(root.name[:-5]+' Grip_'+side,None);current.objects.link(socket);socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Hand_'+side;socket.empty_display_size=.035
    root['rig_note']='Rigid bone weights for silhouette review; no animation clips.'
    assets.append({'name':kind,'role':role,'root':root,'collection':current,'rig':rig})


for kind in ['Rounded crew','Chunky comic','Pocket people','Floating crew']:
    for staff in [True,False]:build_character(kind,staff)
bpy.context.view_layer.update()
display=bpy.data.collections.new('People comparison display');scene.collection.children.link(display)
for i,e in enumerate(assets):
    e['collection'].instance_offset=e['root'].location
    o=bpy.data.objects.new(e['name']+' / '+e['role']+' display',None);display.objects.link(o);o.instance_type='COLLECTION';o.instance_collection=e['collection']
    o.location=((i//2)*2.0,-(i%2)*3.0,0);e['instance']=o
scene.collection.children.unlink(gallery)
studio=bpy.data.collections.new('People review studio');scene.collection.children.link(studio)
current=studio;root=bpy.data.objects.new('People studio root',None);studio.objects.link(root)
style='Studio';floor=box('People floor',(3,-1,-.055),(40,40,.1),material('People studio floor','EAE4D9'),0)
scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=64
scene.render.resolution_x=760;scene.render.resolution_y=920;scene.render.resolution_percentage=100
scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.world=bpy.data.worlds.new('People world');scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.37,.48,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
data=bpy.data.cameras.new('People camera');camera=bpy.data.objects.new(data.name,data);studio.objects.link(camera);scene.camera=camera;data.type='ORTHO';data.clip_start=.001
lights=[]
for name,offset,energy in [('Key',(-4,-6,9),1100),('Fill',(5,-2,6),600)]:
    d=bpy.data.lights.new('People '+name,'AREA');d.energy=energy;d.shape='DISK';d.size=5
    o=bpy.data.objects.new(d.name,d);studio.objects.link(o);lights.append((o,Vector(offset)))
report=[]
for i,e in enumerate(assets):
    for j,a in enumerate(assets):a['instance'].hide_render=j!=i
    points=[e['instance'].location+(o.matrix_world@Vector(c)-e['root'].location) for o in e['collection'].objects if o.type=='MESH' for c in o.bound_box]
    target=Vector(tuple((min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)))
    camera.location=target+Vector((3,-11,3.3));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    rot=camera.rotation_euler.to_matrix().transposed();projected=[rot@(p-target) for p in points]
    data.ortho_scale=max((max(p.x for p in projected)-min(p.x for p in projected))*920/760,max(p.y for p in projected)-min(p.y for p in projected))*1.13
    for light,offset in lights:light.location=target+offset;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
    file=e['name'].replace(' ','_')+'_'+e['role']+'.png';scene.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
    report.append({'direction':e['name'],'role':e['role'],'root':e['root'].name,'collection':e['collection'].name,'preview':file,'bones':len(e['rig'].data.bones)})
for e in assets:e['instance'].hide_render=False
current=display;root=bpy.data.objects.new('People comparison labels',None);display.objects.link(root)
style='Cel';label=material('People label ink','51415C')
for i,name in enumerate(['Rounded crew','Chunky comic','Pocket people','Floating crew']):
    text_label('Direction',name.upper(),(i*2,-.6,.015),.115,label,rotation=(0,0,0))
    text_label('Customer label','CUSTOMER',(i*2,-3.65,.015),.105,label,rotation=(0,0,0))
target=Vector((3,-1.4,.8));camera.location=target+Vector((.3,-14,10));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();data.ortho_scale=8.7
for light,offset in lights:light.location=target+offset;light.data.energy*=1.6;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.filepath=str(OUT/'BlenderPeopleReview.png');bpy.ops.render.render(write_still=True)
bpy.context.view_layer.update();bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/PeopleStudy_Additions.blend'),compress=True)
(OUT/'inventory.json').write_text(json.dumps(report,indent=2))
print('PEOPLE_STUDY_COMPLETE',len(assets))
