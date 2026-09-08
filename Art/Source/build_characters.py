"""Add customizable cartoon characters to the shared Blender workshop."""
import bpy, math, random, json
from mathutils import Vector
from pathlib import Path
from math import sin, cos, pi, sqrt
ROOT=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
assert 'C • Characters' not in bpy.data.collections, 'Characters already exist; edit the existing models instead of rebuilding over them.'
random.seed(82)
charcol=bpy.data.collections.new('C • Characters');scene.collection.children.link(charcol)
current=charcol

def material(name,h,rough=.62):
    h=h.lstrip('#');rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    rgb=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m=bpy.data.materials.new('Character • '+name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=rough
    return m
base={key:material(key,h) for key,h in {'Skin':'D99C70','Hand':'F4C64F','Shirt':'FFF0D9','Pants':'4B546E','Shoe':'6E586F','Sole':'F6EAD1','Accent':'E9799C','Hair':'503630','EyeWhite':'FFFBEF','Pupil':'302B3B','Iris':'6B4B35','Mouth':'743F44','Blush':'D88178','Tongue':'E9A19D','Metal':'B9C5CB','Apron':'75BBA8'}.items()}
character_roots=[]
body_templates={}

def link(o,name,matkey=None):
    o.name=name
    for col in list(o.users_collection):col.objects.unlink(o)
    current.objects.link(o)
    if matkey:o.data.materials.append(base[matkey])
    return o

def root(name,location):
    o=bpy.data.objects.new(name,None);current.objects.link(o);o.location=location;o.empty_display_size=.1
    return o

def weights(o,spec):
    for name in sorted({k for item in spec for k in item}):o.vertex_groups.new(name=name)
    for i,item in enumerate(spec):
        for name,w in item.items():
            if w>0:o.vertex_groups[name].add([i],w,'REPLACE')

def rigid(o,bone):
    g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')

def mesh(name,verts,faces,matkey,bone=None,ws=None):
    m=bpy.data.meshes.new(name);m.from_pydata(verts,[],faces);m.update()
    o=bpy.data.objects.new(name,m);current.objects.link(o);m.materials.append(base[matkey])
    for p in m.polygons:p.use_smooth=True
    if ws:weights(o,ws)
    elif bone:rigid(o,bone)
    return o

def ellipsoid(name,loc,scale,key,bone,segments=20,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=loc)
    o=link(bpy.context.object,name,key);o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    if bone:rigid(o,bone)
    return o

def box(name,loc,dims,key,bone,bevel=.015):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=link(bpy.context.object,name,key);o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    b=o.modifiers.new('Rounded edges','BEVEL');b.width=bevel;b.segments=2
    bpy.ops.object.modifier_apply(modifier=b.name)
    for p in o.data.polygons:p.use_smooth=True
    n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');bpy.ops.object.modifier_apply(modifier=n.name)
    if bone:rigid(o,bone)
    return o

def tube(name,points,radii,key,bone_names,depth_ratio=1,segments=10):
    verts=[];ws=[];faces=[]
    for j,co in enumerate(points):
        co=Vector(co)
        tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
        tangent.normalize();ref=Vector((0,1,0));u=tangent.cross(ref).normalized();v=tangent.cross(u).normalized()
        for k in range(segments):
            a=2*pi*k/segments;verts.append(co+u*(cos(a)*radii[j])+v*(sin(a)*radii[j]*depth_ratio));ws.append(bone_names[j])
    for j in range(len(points)-1):
        for k in range(segments):a=j*segments+k;b=j*segments+(k+1)%segments;faces.append((a,b,b+segments,a+segments))
    faces.extend([tuple(reversed(range(segments))),tuple((len(points)-1)*segments+i for i in range(segments))])
    return mesh(name,verts,faces,key,ws=ws)

def curve_mesh(name,pts,r,key,bone):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=1
    s=d.splines.new('POLY');s.points.add(len(pts)-1)
    for p,co in zip(s.points,pts):p.co=(*co,1)
    o=bpy.data.objects.new(name,d);current.objects.link(o);d.materials.append(base[key])
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
    rigid(o,bone)
    return o

def torso(name,levels,key,bones):
    verts=[];ws=[];n=16
    for (z,w,d),weight in zip(levels,bones):
        for k in range(n):
            a=2*pi*k/n
            # Rounded rectangular cross-sections keep shirts broad and readable.
            x=math.copysign(abs(cos(a))**.75,cos(a))*w;y=math.copysign(abs(sin(a))**.75,sin(a))*d
            verts.append((x,y,z));ws.append(weight)
    faces=[]
    for j in range(len(levels)-1):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((len(levels)-1)*n+i for i in range(n))])
    return mesh(name,verts,faces,key,ws=ws)

def join(parts,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join();o=parts[0];o.name=name
    return o

def make_rig(name,root_obj,bones):
    d=bpy.data.armatures.new(name);rig=bpy.data.objects.new(name,d);current.objects.link(rig)
    rig.parent=root_obj;rig.show_in_front=True
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    bpy.ops.object.mode_set(mode='EDIT')
    for name,head,tail,parent in bones:
        b=d.edit_bones.new(name);b.head=head;b.tail=tail
        if parent:b.parent=d.edit_bones[parent]
    bpy.ops.object.mode_set(mode='OBJECT');rig.data.display_type='OCTAHEDRAL'
    return rig

def bind(o,rig):
    o.parent=rig;m=o.modifiers.new('Character skin','ARMATURE');m.object=rig;m.use_vertex_groups=True


def palette(o,pal):
    for slot in o.material_slots:
        key=slot.material.name.split(' • ')[-1]
        if key in pal:slot.link='OBJECT';slot.material=pal[key]


def hand(name,center,sign,scale,hand_bone,bones,up=False):
    parts=[];c=Vector(center);s=scale;direction=1 if up else -1
    parts.append(ellipsoid(name+' palm',c,(.048*s,.032*s,.064*s),'Hand',hand_bone,16,10))
    for i,(offset,length) in enumerate([(-.032,.057),(-.010,.077),(.013,.071),(.034,.054)]):
        digit=['Index','Middle','Ring','Little'][i];a=c+Vector((sign*offset*s,0,direction*.035*s))
        b=a+Vector((sign*.004*s,-.006*s,direction*length*.53*s));end=a+Vector((sign*.007*s,-.014*s,direction*length*s))
        n1=f'{name}_{digit}01';n2=f'{name}_{digit}02'
        bones.extend([(n1,a,b,hand_bone),(n2,b,end,n1)])
        pts=[a,a.lerp(b,.5),b,b.lerp(end,.65),end]
        rs=[.014*s,.014*s,.0125*s,.011*s,.006*s]
        parts.append(tube(digit,pts,rs,'Hand',[{n1:1},{n1:1},{n1:.5,n2:.5},{n2:1},{n2:1}],segments=8))
    a=c+Vector((-sign*.031*s,0,.015*s));b=c+Vector((-sign*.065*s,-.004*s,-.008*s));end=c+Vector((-sign*.081*s,-.016*s,-.039*s))
    n1=f'{name}_Thumb01';n2=f'{name}_Thumb02';bones.extend([(n1,a,b,hand_bone),(n2,b,end,n1)])
    parts.append(tube('Thumb',[a,a.lerp(b,.5),b,b.lerp(end,.65),end],[.022*s,.021*s,.018*s,.014*s,.008*s],'Hand',[{n1:1},{n1:1},{n1:.5,n2:.5},{n2:1},{n2:1}],segments=10))
    return parts


def hair(head_center,hr,style):
    hz=head_center;rx,ry,rz=hr;parts=[];verts=[];faces=[];n=28;bands=9
    for j in range(bands+1):
        for k in range(n):
            a=2*pi*k/n
            maxtheta=(1.55+.40*sin(a)) if style!='bob' else (1.60+.60*sin(a))
            t=.015+maxtheta*j/bands
            verts.append((rx*1.035*sin(t)*cos(a),ry*1.05*sin(t)*sin(a),hz+rz*1.035*cos(t)))
    for j in range(bands):
        for k in range(n):a=j*n+k;b=j*n+(k+1)%n;faces.append((a,b,b+n,a+n))
    parts.append(mesh('Hair cap',verts,faces,'Hair','Head'))
    if style=='curly':
        for i in range(13):
            a=-pi+pi*i/12
            x=rx*.91*cos(a);y=ry*.80*sin(a);z=hz+rz*.58+.055*sin(i*1.7)
            parts.append(ellipsoid('Rounded curls',(x,y,z),(.082,.075,.072),'Hair','Head',12,8))
        for x,y,z in [(-.11,.02,.31),(.04,-.03,.33),(.14,.03,.28)]:
            parts.append(ellipsoid('Crown curl',(x,y,hz+z*(rz/.32)),(.10,.095,.08),'Hair','Head',12,8))
    elif style!='hat':
        for i,(x,z,angle) in enumerate([(-.13,.22,-25),(0,.245,-25),(.12,.23,-32)]):
            o=ellipsoid('Swept fringe',(x*(rx/.29),-.15*(ry/.235),hz+z*(rz/.32)),(.135*(rx/.29),.105*(ry/.235),.075*(rz/.32)),'Hair','Head',16,10)
            o.rotation_euler.y=math.radians(angle);parts.append(o)
    if style=='bob':
        for sign in [-1,1]:parts.append(ellipsoid('Bob side',(sign*rx*.83,.05,hz-.025),(.095,.145,.19*(rz/.32)),'Hair','Head',16,10))
    return parts


def make_character(name,loc,child,palhex,style='swoop',crew=False,cap=False):
    global current
    current=bpy.data.collections.new(name);charcol.children.link(current)
    char_root=root(name+'_ROOT',loc);character_roots.append(char_root)
    if child:
        hip,knee,ankle,shoulder,elbow,wrist,hz=.47,.28,.13,.77,.61,.48,1.06
        hr=(.267,.224,.28);shx=.20;elx=.29;wx=.365;legx=.094;s=.79
    else:
        hip,knee,ankle,shoulder,elbow,wrist,hz=.77,.45,.15,1.20,1.02,.83,1.54
        hr=(.29,.235,.32);shx=.235;elx=.365;wx=.48;legx=.125;s=1
    bones=[('Root',(0,0,0),(0,0,.16),None),('Hips',(0,0,hip-.04),(0,0,hip+.10),'Root'),('Spine',(0,0,hip+.10),(0,0,shoulder-.10),'Hips'),('Chest',(0,0,shoulder-.10),(0,0,shoulder),'Spine'),('Neck',(0,0,shoulder),(0,0,hz-hr[2]+.12),'Chest'),('Head',(0,0,hz-hr[2]+.12),(0,0,hz+hr[2]),'Neck')]
    pieces=[];face=[];access=[]
    pieces.append(torso('Shirt',[(hip-.04,.213*s,.151*s),(hip+.055,.213*s,.151*s),(shoulder-.12,.24*s,.149*s),(shoulder-.025,.238*s,.137*s),(shoulder+.01,.216*s,.113*s)],'Shirt',[{'Hips':1},{'Hips':.3,'Spine':.7},{'Spine':.35,'Chest':.65},{'Chest':1},{'Chest':1}]))
    pieces.append(torso('Pants waist',[(hip-.13*s,.19*s,.123*s),(hip-.075*s,.208*s,.13*s),(hip+.005,.205*s,.129*s)],'Pants',[{'Hips':1}]*3))
    pieces.append(tube('Neck',[(0,0,shoulder-.01),(0,0,hz-hr[2]+.13)],[.074*s,.068*s],'Skin',[{'Neck':1},{'Head':1}],segments=12))
    pieces.append(ellipsoid('Head',(0,0,hz),hr,'Skin','Head',28,18))
    for sign,side in [(1,'L'),(-1,'R')]:
        upper='UpperArm_'+side;lower='LowerArm_'+side;hb='Hand_'+side
        shoulderp=Vector((sign*shx,0,shoulder-.055));ep=Vector((sign*elx,-.004,elbow));wp=Vector((sign*wx,-.014,wrist));hp=wp+Vector((sign*.025,-.005,-.047*s))
        bones.extend([(upper,shoulderp,ep,'Chest'),(lower,ep,wp,upper),(hb,wp,hp+Vector((0,0,-.055*s)),lower)])
        end=shoulderp.lerp(ep,.68)
        sleeve_start=shoulderp-Vector((sign*.065*s,0,0))
        pieces.append(tube('Short sleeve',[sleeve_start,sleeve_start.lerp(end,.45),end],[.088*s,.096*s,.080*s],'Shirt',[{upper:1}]*3,segments=12))
        pieces.append(tube('Sleeve hem',[end-Vector((0,0,.005)),end+Vector((0,0,.018*s))],[.081*s,.081*s],'Accent',[{upper:1}]*2,segments=12))
        pieces.append(tube('Arm',[shoulderp.lerp(ep,.60),ep.lerp(shoulderp,.13),ep,ep.lerp(wp,.18),ep.lerp(wp,.75),wp],[.069*s,.062*s,.062*s,.064*s,.049*s,.039*s],'Skin',[{upper:1},{upper:1},{upper:.5,lower:.5},{lower:1},{lower:1},{lower:1}],segments=12))
        pieces.append(tube('Wrist cuff',[wp-Vector((0,0,.008*s)),wp+Vector((0,0,.028*s))],[.044*s,.047*s],'Accent',[{hb:1}]*2,segments=12))
        pieces += hand(side,hp,sign,s,hb,bones)
        uleg='UpperLeg_'+side;lleg='LowerLeg_'+side;foot='Foot_'+side
        a=Vector((sign*legx,0,hip));b=Vector((sign*(legx+.01),-.006,knee));c=Vector((sign*(legx+.02),0,ankle));toe=c+Vector((0,-.14*s,-.055*s))
        bones.extend([(uleg,a,b,'Hips'),(lleg,b,c,uleg),(foot,c,toe,lleg)])
        if child:
            end=a.lerp(b,.84)
            pieces.append(tube('Shorts',[a,a.lerp(end,.45),end],[.089*s,.096*s,.087*s],'Pants',[{uleg:1}]*3,segments=12))
            pieces.append(tube('Lower leg',[a.lerp(b,.75),b,b.lerp(c,.3),c],[.058*s,.060*s,.055*s,.044*s],'Skin',[{uleg:1},{uleg:.5,lleg:.5},{lleg:1},{lleg:1}],segments=12))
        else:
            pieces.append(tube('Trouser leg',[a,a.lerp(b,.55),b,b.lerp(c,.2),b.lerp(c,.85),c],[.089,.085,.075,.076,.066,.064],'Pants',[{uleg:1},{uleg:1},{uleg:.5,lleg:.5},{lleg:1},{lleg:1},{lleg:1}],segments=12))
        pieces.append(tube('Sock',[c-Vector((0,0,.02)),c+Vector((0,0,.055*s))],[.047*s,.047*s],'Sole',[{lleg:1}]*2,segments=12))
        pieces.append(box('Sneaker sole',(c.x,-.055*s,.032*s),(.185*s,.294*s,.05*s),'Sole',foot,.02*s))
        pieces.append(box('Sneaker upper',(c.x,-.055*s,.095*s),(.178*s,.281*s,.116*s),'Shoe',foot,.046*s))
        pieces.append(box('Sneaker toe',(c.x,-.176*s,.079*s),(.164*s,.060*s,.064*s),'Sole',foot,.023*s))
        for zoff in [0,.028]:pieces.append(box('Sneaker strap',(c.x,-.055*s+zoff*s,.15*s),(.13*s,.020*s,.015*s),'Accent',foot,.006*s))
        # Face features are rigidly weighted to the head bone.
        face.append(ellipsoid('Ear',(sign*hr[0]*.98,0,hz-.015),(.05*s,.041*s,.075*s),'Skin','Head',16,10))
        face.append(ellipsoid('Inner ear',(sign*hr[0]*1.04,-.031*s,hz-.017),(.025*s,.012*s,.041*s),'Blush','Head',12,8))
        ex=sign*hr[0]*.38;ez=hz+.025
        eye_scale=.96 if child else 1
        face.append(ellipsoid('Eye white',(ex,-hr[1]*.92,ez),(.087*eye_scale,.040,.104*eye_scale),'EyeWhite','Head',20,14))
        face.append(ellipsoid('Iris',(ex,-hr[1]*.92-.036,ez),(.052*eye_scale,.018,.064*eye_scale),'Iris','Head',18,12))
        face.append(ellipsoid('Pupil',(ex,-hr[1]*.92-.049,ez),(.039*eye_scale,.010,.051*eye_scale),'Pupil','Head',18,12))
        face.append(ellipsoid('Eye sparkle',(ex-.012,-hr[1]*.92-.059,ez+.024),(.014,.005,.018),'EyeWhite','Head',12,8))
        face.append(ellipsoid('Small eye sparkle',(ex+.017,-hr[1]*.92-.058,ez-.020),(.006,.003,.007),'EyeWhite','Head',10,6))
        pts=[(ex+u*.079,-hr[1]*.87,hz+.152+.013*(1-u*u)) for u in [-1,-.5,0,.5,1]]
        face.append(curve_mesh('Eyebrow',pts,.011,'Hair','Head'))
        face.append(ellipsoid('Rosy cheek',(sign*hr[0]*.62,-hr[1]*.85,hz-.071),(.039,.011,.023),'Blush','Head',16,8))
    face.append(ellipsoid('Nose',(0,-hr[1]*1.10,hz-.057),(.042*s,.047*s,.035*s),'Skin','Head',16,10))
    if child:
        face.append(mesh('Happy smile',[(x,-hr[1]*.95,hz+z) for x,z in [(-.073,-.106),(-.04,-.116),(0,-.118),(.04,-.116),(.073,-.106),(.062,-.146),(.035,-.17),(0,-.177),(-.035,-.17),(-.062,-.146)]],[tuple(range(10))],'Mouth','Head'))
        face.append(box('Top teeth',(0,-hr[1]*.95-.005,hz-.126),(.083,.008,.015),'EyeWhite','Head',.005))
        face.append(ellipsoid('Tongue',(0,-hr[1]*.95-.005,hz-.160),(.033,.005,.014),'Tongue','Head',12,8))
    else:
        pts=[(u*.073,-hr[1]*.91,hz-.126-.022*(1-u*u)) for u in [-1,-.75,-.5,-.25,0,.25,.5,.75,1]]
        face.append(curve_mesh('Smile',pts,.0075,'Mouth','Head'))
    hairparts=hair(hz,hr,'hat' if crew or cap else style)
    if crew or cap:
        # Soft cap is a separate accessory, so the character also works bareheaded.
        access.append(ellipsoid('Cap crown',(0,.014,hz+hr[2]*.79),(hr[0]*1.00,hr[1]*.97,.13*s),'Accent','Head',24,14))
        access.append(ellipsoid('Cap brim',(0,-.217*s,hz+hr[2]*.70),(.265*s,.162*s,.032*s),'Accent','Head',24,10))
        access.append(ellipsoid('Cap button',(0,.014,hz+hr[2]*.79+.132*s),(.023*s,.023*s,.014*s),'Sole','Head',12,8))
    if crew:
        av=[];aw=[];af=[]
        for z,w,weight in [(.735,.217,{'Spine':1}),(.87,.204,{'Spine':1}),(1.02,.16,{'Spine':.3,'Chest':.7}),(1.145,.12,{'Chest':1})]:
            for i in range(5):
                t=-1+i*.5;av.append((w*t,-.161-.009*(1-t*t),z));aw.append(weight)
        for j in range(3):
            for i in range(4):a=j*5+i;af.append((a,a+1,a+6,a+5))
        access.append(mesh('Apron bib',av,af,'Apron',ws=aw))
        for sign in [-1,1]:access.append(curve_mesh('Apron strap',[(sign*.10,-.167,1.13),(sign*.115,-.135,1.225),(sign*.115,.07,1.19)],.010,'Apron','Chest'))
        access.append(box('Apron pocket',(0,-.179,.90),(.18,.014,.092),'Sole','Spine',.015))
        access.append(ellipsoid('Uniform cone scoop',(0,-.179,1.045),(.026,.009,.026),'Accent','Chest',14,8))
        access.append(mesh('Uniform cone badge',[(-.021,-.188,1.026),(.021,-.188,1.026),(0,-.188,.985)],[(0,1,2)],'Hand','Chest'))
    rig=make_rig(name+'_Rig',char_root,bones)
    body=join(pieces,name+'_Body');bind(body,rig)
    facemesh=join(face,name+'_Face');bind(facemesh,rig)
    hairmesh=join(hairparts,name+'_Hair');bind(hairmesh,rig)
    accessories=None
    if access:accessories=join(access,name+'_Accessories');bind(accessories,rig)
    # Reuse the exact same adult or child body mesh across variants.
    kind='Child' if child else 'Adult'
    if kind in body_templates:
        prototype=body_templates[kind]
        assert len(body.data.vertices)==len(prototype.data.vertices)
        assert [g.name for g in body.vertex_groups]==[g.name for g in prototype.vertex_groups]
        assert all((a.co-b.co).length<.0001 for a,b in zip(body.data.vertices,prototype.data.vertices))
        body.data=prototype.data
    else:
        body.data.name=kind+'_SharedBody';body_templates[kind]=body
    pal={key:material(name+' / '+key,h) for key,h in palhex.items()}
    for o in [body,facemesh,hairmesh]+([accessories] if accessories else []):palette(o,pal)
    char_root['character_type']=kind;char_root['palette_materials']=', '.join(pal.keys());char_root['body_mesh']=body.data.name
    char_root['rig_note']='A-pose. Separate fingers, bone-weighted body, head accessories. No animations.'
    return char_root,rig

crew={'Skin':'DCA477','Hand':'F3C94E','Shirt':'FFF0DA','Pants':'4B536C','Shoe':'5C4866','Sole':'FFF0D5','Accent':'E87FA0','Hair':'51332B','Apron':'72B9A5','Blush':'D88D7D'}
adulta={'Skin':'B97A57','Hand':'B97A57','Shirt':'E88D65','Pants':'4C6380','Shoe':'656079','Sole':'F7E8CA','Accent':'F4D080','Hair':'392D2D','Iris':'6C4938','Blush':'AD665E'}
adultb={'Skin':'825840','Hand':'825840','Shirt':'81C3B7','Pants':'685477','Shoe':'DE997D','Sole':'F7E8CA','Accent':'F5D68A','Hair':'342B2D','Iris':'5D4238','Blush':'985B58'}
childa={'Skin':'F0BD96','Hand':'F0BD96','Shirt':'A497CB','Pants':'6583A5','Shoe':'E4B84F','Sole':'FFF0D3','Accent':'E986AF','Hair':'B46E3D','Iris':'706347','Blush':'E39B90'}
childb={'Skin':'C88F67','Hand':'C88F67','Shirt':'D6CE76','Pants':'6CA99D','Shoe':'D880A2','Sole':'FFF0D3','Accent':'E99BC0','Hair':'503335','Iris':'64453E','Blush':'C87977'}
make_character('01 Crew player',(-3.85,-4.5,0),False,crew,crew=True)
make_character('02 Adult NPC',(-2.20,-4.5,0),False,adulta)
make_character('03 Adult NPC color variant',(-.55,-4.5,0),False,adultb,style='curly')
make_character('04 Child NPC',(1.05,-4.5,0),True,childa,cap=True)
make_character('05 Child NPC color variant',(2.45,-4.5,0),True,childb,style='bob')

# First-person arms use the same articulated hand design at adult scale.
current=bpy.data.collections.new('D • First-person hands');scene.collection.children.link(current)
fp=root('FirstPersonHands_ROOT',(4.05,-4.5,.25))
fpbones=[('Root',(0,0,0),(0,0,.1),None)];fpparts=[]
for sign,side in [(1,'L'),(-1,'R')]:
    x=sign*.19;a=(x,0,.05);w=(x,0,.44);h=(x,-.012,.50)
    fore='Forearm_'+side;hb='Hand_'+side
    fpbones.extend([(fore,a,w,'Root'),(hb,w,(x,-.012,.59),fore)])
    fpparts.append(tube('Uniform forearm',[(x,0,.05),(x,0,.23),(x,0,.40)],[.084,.070,.050],'Shirt',[{fore:1}]*3,segments=16))
    fpparts.append(tube('Glove cuff',[(x,0,.38),(x,0,.45)],[.056,.050],'Accent',[{fore:1},{hb:1}],segments=14))
    fpparts+=hand(side,h,sign,1,hb,fpbones,up=True)
fprig=make_rig('FirstPersonHands_Rig',fp,fpbones)
fpm=join(fpparts,'FirstPersonHands_Mesh');bind(fpm,fprig)
fp['usage']='Articulated left and right first-person hands; five fingers per hand.'
# Use actual palette slots for the gloves and sleeves.

bpy.ops.object.select_all(action='DESELECT')
scene['characters']='Crew player, two adult NPC palettes, two child NPC palettes, articulated first-person hands.'
cam=scene.camera
cam.location=(-9.8,-18.8,10.8);cam.rotation_euler=(Vector((-.6,-.6,1.45))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=14.3
scene.render.resolution_x=2000;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.region_3d.view_camera_zoom=8
bpy.context.view_layer.update()
# Confirm complete weight coverage and shared geometry before saving.
for rig in [o for o in charcol.all_objects if o.type=='ARMATURE']+[fprig]:
    bone_names=set(rig.data.bones.keys())
    for ob in rig.children:
        if ob.type!='MESH':continue
        names=[g.name for g in ob.vertex_groups]
        for v in ob.data.vertices:
            total=sum(g.weight for g in v.groups if names[g.group] in bone_names)
            assert abs(total-1)<.001,(ob.name,v.index,total)
assert len(character_roots)==5
assert len([o for o in bpy.data.objects if o.type=='ARMATURE' and o.name.endswith('_Rig')])==6
print('CHARACTERS_VERIFIED: five full-body characters, two shared body meshes, six rigs; every mesh vertex weighted.')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
# Export only the character set. No cameras or review geometry are included.
for col in [charcol,current]:
    for o in col.all_objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Art/Exports/Characters.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(ROOT/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
# Character-only views use the same saved geometry and studio lighting.
for col in scene.collection.children:
    if col not in [charcol,current] and not col.name.startswith('Z'):col.hide_render=True
for light in [o for o in scene.objects if o.type=='LIGHT']:
    if 'Key' in light.name:light.location=(-5,-9,6);light.data.energy=850;light.data.size=5
    elif 'Fill' in light.name:light.location=(6,-6,5);light.data.energy=700;light.data.size=4
    else:light.location=(0,-1,6);light.data.energy=1000;light.data.size=4
    light.rotation_euler=(Vector((0,-4.5,1))-light.location).to_track_quat('-Z','Y').to_euler()
cam.location=(.0,-15,3.0);cam.rotation_euler=(Vector((0,-4.5,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=9.35
scene.render.resolution_x=2100;scene.render.resolution_y=1000
scene.render.filepath=str(ROOT/'Art/Previews/Characters_01_Lineup.png');bpy.ops.render.render(write_still=True)
# Close portrait of the three distinct roles.
for r in character_roots:
    if r.name.startswith(('03','05')):
        for o in r.children_recursive:
            if o.type=='MESH':o.hide_render=True
character_roots[0].location.x=-1.55;character_roots[1].location.x=0;character_roots[3].location.x=1.5
for o in fp.children_recursive:
    if o.type=='MESH':o.hide_render=True
cam.location=(.1,-12,2.5);cam.rotation_euler=(Vector((0,-4.5,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.85
scene.render.resolution_x=1700;scene.render.resolution_y=1200
scene.render.filepath=str(ROOT/'Art/Previews/Characters_02_Main_Models.png');bpy.ops.render.render(write_still=True)
# Verify the finger rigs with a posed first-person hand render.
for r in character_roots:
    for o in r.children_recursive:
        if o.type=='MESH':o.hide_render=True
for o in fp.children_recursive:
    if o.type=='MESH':o.hide_render=False
for digit in ['Index','Middle','Ring','Little']:
    for seg in ['01','02']:
        b=fprig.pose.bones['R_'+digit+seg];b.rotation_mode='XYZ';b.rotation_euler.x=math.radians(-35 if seg=='01' else -48)
cam.location=(4.05,-8.0,1.7);cam.rotation_euler=(Vector((4.05,-4.5,.69))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.1
scene.render.resolution_x=1200;scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'Art/Previews/Characters_03_FirstPerson_Hands.png');bpy.ops.render.render(write_still=True)
print('CHARACTERS_COMPLETE')
