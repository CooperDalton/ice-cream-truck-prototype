"""Build simple toy characters in the current shared Blender scene."""
import bpy, bmesh, math
from mathutils import Vector, Matrix
scene=bpy.context.scene
charcol=bpy.data.collections.new('C • Characters');scene.collection.children.link(charcol)
handcol=bpy.data.collections.new('D • First-person hands');scene.collection.children.link(handcol)
current=None;parts=[];mats={}
def material(name,h):
    rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)];rgb=[x/12.92 if x<.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
    m=bpy.data.materials.new('Toy • '+name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=.78
    return m
white=material('Eye whites','FFF7DE');dark=material('Pupils and eyebrows','343044');nose=material('Bubblegum nose','F287AD')
def setup(name,palette):
    global mats
    mats={k:material(name+' / '+k,h) for k,h in palette.items()};mats.update(Eyes=white,Dark=dark,Nose=nose)
def weight(o,bone):
    g=o.vertex_groups.new(name=bone);g.add(list(range(len(o.data.vertices))),1,'REPLACE')
def mesh(name,v,f,key,bone):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    o=bpy.data.objects.new(name,me);current.objects.link(o);me.materials.append(mats[key]);weight(o,bone)
    for p in me.polygons:p.use_smooth=True
    parts.append(o);return o

def orb(name,pos,size,key,bone,segments=16,rings=10):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=1,location=pos)
    o=bpy.context.object;o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    current.objects.link(o);o.scale=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mats[key]);weight(o,bone)
    for p in o.data.polygons:p.use_smooth=True
    parts.append(o);return o

def bean():
    n=24;v=[];f=[]
    levels=[(.06,.09,.09),(.10,.22,.18),(.24,.33,.26),(.52,.37,.29),(.83,.34,.27),(1.03,.27,.22),(1.09,.17,.16)]
    for z,w,d in levels:
        for j in range(n):a=2*math.pi*j/n;v.append((w*math.cos(a),d*math.sin(a),z))
    for i in range(len(levels)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f+=[tuple(reversed(range(n))),tuple((len(levels)-1)*n+j for j in range(n))]
    mesh('Rounded bean body',v,f,'Clothes','Body')

def mitten(name,pos,sign,key,bone,size=1):
    outline=[(-.10,0),(.08,0),(.12,.05),(.21,.12),(.235,.19),(.21,.23),(.17,.23),(.11,.18),(.13,.34),(.10,.38),(.055,.38),(.025,.35),(.02,.21),(-.005,.40),(-.04,.43),(-.08,.41),(-.09,.37),(-.06,.22),(-.14,.34),(-.19,.35),(-.22,.31),(-.21,.26),(-.14,.11),(-.13,.04)]
    # Smooth the silhouette while keeping the finger valleys readable.
    smooth=[]
    for i,p1 in enumerate(outline):
        p0=Vector(outline[(i-1)%len(outline)]);p1=Vector(p1);p2=Vector(outline[(i+1)%len(outline)]);p3=Vector(outline[(i+2)%len(outline)])
        for t in [0,.5]:smooth.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    v=[];f=[];n=len(smooth)
    for scale,yy in [(.82,.056),(.95,.044),(1,0),(.95,-.044),(.82,-.056)]:
        for x,z in smooth:v.append((pos[0]+sign*x*scale*size,pos[1]+yy*size,pos[2]+(.17+(z-.17)*scale)*size))
    for k in range(4):
        for j in range(n):a=k*n+j;b=k*n+(j+1)%n;f.append((a,b,b+n,a+n))
    f.extend([tuple(reversed(range(n))),tuple(4*n+j for j in range(n))])
    return mesh(name,v,f,key,bone)

def make_rig(name,root,child=False,fp=False):
    d=bpy.data.armatures.new(name);o=bpy.data.objects.new(name,d);current.objects.link(o);o.parent=root
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT')
    specs=[('Root',(0,0,0),(0,0,.15),None)]
    if not fp:specs += [('Body',(0,0,.15),(0,0,.95),'Root'),('Head',(0,0,1.05),(0,0,1.65),'Body')]
    for sign,side in [(-1,'L'),(1,'R')]:
        co=(sign*(.28 if fp else .64),-.03,.10 if fp else .92)
        specs.append(('Hand_'+side,co,(co[0],co[1],co[2]+.25),'Root' if fp or name=='Crew_Rig' else 'Body'))
    for n,a,b,p in specs:
        bone=d.edit_bones.new(n);bone.head=a;bone.tail=b
        if p:bone.parent=d.edit_bones[p]
    bpy.ops.object.mode_set(mode='OBJECT');o.show_in_front=True
    if fp or name=='Crew_Rig':
        root['easy_mode_hand_setup']='Floating hands with independent Root-parented controls and no arms.'
        for sign,side in [(-1,'L'),(1,'R')]:
            bone=d.bones['Hand_'+side]
            sock=bpy.data.objects.new(('FirstPerson' if fp else 'Crew')+'_Grip_'+side+'_SOCKET',None)
            current.objects.link(sock);sock.parent=o;sock.parent_type='BONE';sock.parent_bone=bone.name;sock.empty_display_size=.045
            palm=Vector((sign*(.28 if fp else .66),-.06 if fp else -.13,.2615 if fp else 1.1015))
            sock.matrix_basis=(bone.matrix_local @ Matrix.Translation((0,bone.length,0))).inverted() @ Matrix.Translation(palm)
    return o

def finish(name,rig):
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=parts[0];o.name=name
    # Bake object transforms to an origin at the rig root before parenting.
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    o.parent=rig;mod=o.modifiers.new('Simple character rig','ARMATURE');mod.object=rig
    return o

roots=[];templates={}
configs=[('Crew',(-4.8,-4.5,0),False,{'Skin':'C6CA7B','Clothes':'FFF0D6','Accent':'EF879E','Hair':'EF879E'},'cap'),('Adult',(-2.5,-4.5,0),False,{'Skin':'A7C785','Clothes':'63558D','Accent':'ECCC5A','Hair':'E8A260'},'helmet'),('AdultVariant',(-.2,-4.5,0),False,{'Skin':'E6C36D','Clothes':'559CA8','Accent':'EBCBAA','Hair':'866DB3'},'helmet'),('Child',(1.9,-4.5,0),True,{'Skin':'B2A5D6','Clothes':'EF9DA2','Accent':'F3DA82','Hair':'675984'},'cap'),('ChildVariant',(3.7,-4.5,0),True,{'Skin':'E9B78E','Clothes':'79B7A4','Accent':'E9C97B','Hair':'D6816C'},'cap')]
for idx,(name,pos,child,palette,hat) in enumerate(configs):
    current=bpy.data.collections.new('%02d %s'%(idx+1,name));charcol.children.link(current);parts=[];setup(name,palette)
    root=bpy.data.objects.new(name+'_ROOT',None);current.objects.link(root);root.location=pos;root.empty_display_size=.15;roots.append(root)
    bean();orb('Collar',(0,0,1.06),(.28,.23,.065),'Accent','Body',16,6)
    orb('Round head',(0,0,1.48),(.49,.39,.48),'Skin','Head',20,12)
    for sign in [-1,1]:
        orb('Big white eye',(sign*.217,-.338,1.51),(.208,.108,.251),'Eyes','Head',16,10)
        orb('Simple pupil',(sign*.217+.022,-.431,1.51),(.108,.045,.155),'Dark','Head',12,8)
        orb('Eye glint',(sign*.217-.010,-.469,1.574),(.029,.010,.035),'Eyes','Head',8,6)
        brow=orb('Soft eyebrow',(sign*.22,-.32,1.81),(.19,.077,.067),'Dark','Head',12,6);brow.rotation_euler.y=sign*.06
        mitten('Floating mitten '+str(sign),(sign*.66,-.07,.94),sign,'Skin','Hand_'+('L' if sign<0 else 'R'),.95)
    orb('Round pink nose',(0,-.404,1.30),(.103,.07,.071),'Nose','Head',12,8)
    if hat=='cap':
        orb('Cap crown',(0,.025,1.86),(.495,.385,.165),'Hair','Head',16,8)
        orb('Cap visor',(0,-.34,1.86),(.39,.25,.055),'Hair','Head',16,6)
        orb('Cap button',(0,.02,2.014),(.047,.045,.028),'Accent','Head',8,6)
    else:
        orb('Rounded hair cap',(0,.12,1.79),(.493,.32,.24),'Hair','Head',16,8)
        for sign in [-1,1]:orb('Simple side hair',(sign*.42,.05,1.57),(.11,.24,.31),'Hair','Head',12,8)
    if name=='Crew':
        # A single mint apron panel follows the bean rather than adding uniform detail.
        mats['Apron']=material('Crew / Apron','73B5A3')
        orb('Simple apron',(0,-.249,.61),(.245,.064,.34),'Apron','Body',16,8)
    else:
        orb('Shirt badge',(0,-.286,.72),(.072,.014,.071),'Accent','Body',10,6)
    rig=make_rig(name+'_Rig',root);body=finish(name+'_Mesh',rig)
    # Identical customer variants reuse one mesh with per-object palette slots.
    family='Child' if child else ('Adult' if name.startswith('Adult') else 'Crew')
    if family in templates:
        source=templates[family];palette_slots=[slot.material for slot in body.material_slots]
        body.data=source.data
        for i,m in enumerate(palette_slots):body.material_slots[i].link='OBJECT';body.material_slots[i].material=m
    else:templates[family]=body
    if child:root.scale=(.76,.76,.69)
    root['style']='Round toy head, bean body, floating four-digit mittens; no human limb anatomy.'
    root['customization']='Named material slots for skin, clothes, hat or hair, and accents. Adult and child appearance pairs share mesh data.'
# First-person pair uses the same silhouette at a larger visible scale.
current=handcol;parts=[];setup('First person',{'Skin':'F0CE68','Clothes':'FFF0D6','Accent':'ED92A8','Hair':'ED92A8'})
fp=bpy.data.objects.new('FirstPersonHands_ROOT',None);current.objects.link(fp);fp.location=(5.5,-4.5,.15)
for sign,side in [(-1,'L'),(1,'R')]:
    mitten('First-person '+side,(sign*.28,0,.1),sign,'Skin','Hand_'+side,.95)
    orb('Cuff '+side,(sign*.28,0,.11),(.107,.07,.060),'Accent','Hand_'+side,12,6)
rig=make_rig('FirstPersonHands_Rig',fp,fp=True);finish('FirstPersonMittens_Mesh',rig)
scene['characters']='Five simple bean characters and a pair of first-person mittens. Five-bone character rigs; three-bone hand rig.'
print('ROUND_CHARACTERS_BUILT')
