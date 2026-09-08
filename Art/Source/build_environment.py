"""Add four houses and four trees to the preserved Blender workshop."""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
assert 'E • Houses' not in bpy.data.collections
rng=random.Random(28)
def collection(name, parent=None):
    c=bpy.data.collections.new(name)
    (parent or scene.collection).children.link(c)
    return c
houses=collection('E • Houses');trees=collection('F • Trees')
current=None;root=None

def material(name,color,rough=.7):
    m=bpy.data.materials.new('Environment • '+name);m.use_nodes=True
    rgb=[int(color[i:i+2],16)/255 for i in (0,2,4)]
    rgb=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m.diffuse_color=(*rgb,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*rgb,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=rough
    return m
cream=material('Ivory trim','FFF1D3');base=material('Foundation','ADABB3')
glass=material('Blue window glass','477B93',.3);glint=material('Window reflection','AADFE6',.32)
metal=material('Door hardware','DAB46B',.35);dark=material('Deep recess','3D4054')
wood=material('Warm bark','966444');woodlight=material('Birch bark','DBCCA3')
leaves=[material('Oak leaf green','82AE48'),material('Oak sunlit leaves','A0C658'),material('Poplar leaves','71AA62'),material('Poplar light leaves','8ABD70'),material('Pine needles','388875'),material('Pine light needles','519C79'),material('Maple leaves','A8BB51'),material('Maple light leaves','C3CD62')]

def link(o,name,mat=None,parent=None):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    current.objects.link(o);o.parent=parent or root
    if mat:o.data.materials.append(mat)
    return o

def empty(name,pos=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);current.objects.link(o);o.location=pos;o.parent=parent
    o.empty_display_size=.22
    return o

def bevel(o,width=.06):
    b=o.modifiers.new('Soft corners','BEVEL');b.width=width;b.segments=2
    n=o.modifiers.new('Face normals','WEIGHTED_NORMAL');n.keep_sharp=True;n.weight=40
    return o

def cube(name,pos,size,mat,parent=None,soft=.04):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=link(bpy.context.object,name,mat,parent);o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if soft:bevel(o,soft)
    return o

def mesh(name,verts,faces,mat,parent=None,soft=0):
    d=bpy.data.meshes.new(name);d.from_pydata(verts,[],faces);d.update()
    o=bpy.data.objects.new(name,d);current.objects.link(o);o.parent=parent or root;o.data.materials.append(mat)
    if soft:bevel(o,soft)
    return o

def cylinder(name,a,b,r1,r2,mat,parent=None,n=10):
    mid=(Vector(a)+Vector(b))/2;delta=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r1,radius2=r2,depth=delta.length,location=mid)
    o=link(bpy.context.object,name,mat,parent);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    bevel(o,.025)
    return o

def blob(name,pos,size,mat,parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1,location=pos)
    o=link(bpy.context.object,name,mat,parent)
    for v in o.data.vertices:v.co*=rng.uniform(.96,1.045)
    o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return o

def roof(name,x,y,w,d,z,rise,mat):
    # Solid gable volume, with beveled roof planes and cream fascia below.
    for suffix,extra,zz,mm in [(' fascia',.03,z-.08,cream),(' roof',0,z,mat)]:
        a=w/2+extra;b=d/2+extra;t=.18
        v=[(x-a,y-b,zz),(x+a,y-b,zz),(x,y-b,zz+rise),(x-a,y+b,zz),(x+a,y+b,zz),(x,y+b,zz+rise)]
        o=mesh(name+suffix,v,[(0,2,1),(3,4,5),(0,3,5,2),(1,2,5,4),(0,1,4,3)],mm,soft=.055)
    cylinder(name+' ridge cap',(x,y-d/2-.03,z+rise),(x,y+d/2+.03,z+rise),.095,.095,mat,n=8)

def window(name,x,y,z,w=1,h=1.25,angle=0,shutters=None):
    p=empty(name,(x,y,z),root);p.rotation_euler.z=angle
    cube(name+' frame',(0,0,0),(w+.2,.16,h+.2),cream,p)
    cube(name+' glass',(0,-.097,0),(w,.055,h),glass,p,.015)
    cube(name+' mullion',(0,-.14,0),(.065,.065,h),cream,p,.012)
    cube(name+' transom',(0,-.14,.05),(w,.065,.065),cream,p,.012)
    cube(name+' sill',(0,-.085,-h/2-.09),(w+.32,.34,.12),cream,p,.025)
    for xx in [-w*.26,w*.25]:
        o=cube(name+' reflection',(xx,-.131,h*.25),(.06,.009,h*.30),glint,p,.005);o.rotation_euler.y=-.35
    if shutters:
        for sign in [-1,1]:
            sx=sign*(w/2+.26)
            cube(name+' shutter',(sx,.015,0),(.25,.12,h+.08),shutters,p,.025)
            for zz in [-.35,0,.35]:cube(name+' shutter rail',(sx,-.055,zz*h),(.22,.025,.04),cream,p,.005)
    return p

def door(name,x,y,mat):
    p=empty(name,(x,y,1.22),root)
    cube(name+' surround',(0,0,0),(1.13,.2,2.2),cream,p)
    cube(name+' leaf',(0,-.125,0),(.9,.12,2.02),mat,p)
    cube(name+' inset panel',(0,-.2,-.45),(.66,.055,.72),cream,p,.035)
    cube(name+' window',(0,-.2,.45),(.62,.055,.62),glass,p,.045)
    cylinder(name+' knob',(.32,-.2,-.04),(.32,-.31,-.04),.06,.06,metal,p,n=12)
    cube(name+' step',(x,y-.30,.09),(1.48,.70,.18),base)
    return p

def wallblock(x,y,w,d,h,mat):
    cube('Foundation',(x,y,.12),(w+.14,d+.14,.24),base,soft=.07)
    cube('Wall shell',(x,y,h/2+.12),(w,d,h),mat,soft=.055)
    for xx in [x-w/2+.045,x+w/2-.045]:
        for yy in [y-d/2+.045,y+d/2-.045]:cube('Corner trim',(xx,yy,h/2+.12),(.15,.15,h),cream,soft=.025)
    cube('Eave band',(x,y,h+.05),(w+.10,d+.10,.17),cream)

def chimney(x,y,z,roofmat):
    cube('Chimney',(x,y,z),(.58,.65,1.35),roofmat)
    cube('Chimney cap',(x,y,z+.70),(.74,.81,.15),cream)
    cube('Chimney dark opening',(x,y,z+.785),(.42,.48,.035),dark,soft=.01)

house_roots=[]
# 1. Compact cottage with a large front gable.
current=collection('01 Peach cottage',houses);root=empty('House_Cottage_ROOT',(-12,8,0));house_roots.append(root)
wall=material('Cottage walls','F0AE91');rmat=material('Cottage roof','936D98');accent=material('Cottage door and shutters','73A99B')
wallblock(0,0,5.2,4.5,2.9,wall);roof('Cottage gable',0,0,5.8,5.15,3.04,1.70,rmat)
door('Cottage front door',-1.45,-2.31,accent);window('Cottage front window',.78,-2.29,1.63,1.35,1.35,shutters=accent)
window('Cottage side window',2.63,.15,1.63,1.2,1.3,math.pi/2)
window('Cottage left window',-2.63,.15,1.63,1.2,1.3,-math.pi/2)
window('Cottage attic window',0,-2.607,3.7,.56,.55)
chimney(1.55,1.10,4.0,rmat)
# 2. Narrow two-story house with a covered entry.
current=collection('02 Mint townhouse',houses);root=empty('House_Townhouse_ROOT',(-4,8,0));house_roots.append(root)
wall=material('Townhouse walls','9DCCB6');rmat=material('Townhouse roof','4F8094');accent=material('Townhouse door','E99999')
wallblock(0,0,4.45,4.6,5.30,wall);roof('Townhouse gable',0,0,5.05,5.25,5.45,1.65,rmat)
cube('Story band',(0,0,2.87),(4.56,4.7,.14),cream)
door('Townhouse front door',-1.05,-2.36,accent)
window('Townhouse ground window',1.03,-2.35,1.65,1.02,1.3)
for xx in [-1.05,1.05]:window('Townhouse upper window',xx,-2.35,4.05,1.04,1.48,shutters=rmat)
for zz in [1.65,4.05]:
    for sign in [-1,1]:window('Townhouse side window',sign*2.26,.4,zz,1.1,1.3,sign*math.pi/2)
cube('Porch canopy',(-1.05,-2.85,2.62),(1.85,1.25,.16),rmat,soft=.055)
for xx in [-1.83,-.28]:cube('Porch post',(xx,-3.29,1.40),(.12,.12,2.3),cream)
window('Townhouse attic window',0,-2.657,6.03,.48,.5)
# 3. Wide bungalow with a hip roof and full-width veranda.
current=collection('03 Butter bungalow',houses);root=empty('House_Bungalow_ROOT',(4,8,0));house_roots.append(root)
wall=material('Bungalow walls','F1D78F');rmat=material('Bungalow roof','CF817C');accent=material('Bungalow door','669EA8')
wallblock(0,0,6.0,4.6,2.80,wall)
a=3.35;b=2.66;z=2.94;peak=4.40
v=[(-a,-b,z),(a,-b,z),(a,b,z),(-a,b,z),(-1.15,0,peak),(1.15,0,peak)]
mesh('Bungalow hip roof',v,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4),(3,2,1,0)],rmat,soft=.065)
cube('Veranda deck',(0,-2.93,.12),(6.28,1.42,.24),base)
door('Bungalow front door',0,-2.36,accent)
for xx in [-1.88,1.88]:window('Bungalow front window',xx,-2.35,1.66,1.12,1.20,shutters=accent)
canopy=cube('Veranda roof',(0,-2.91,2.70),(6.55,1.8,.18),rmat,soft=.045);canopy.rotation_euler.x=.10
for xx in [-2.87,2.87]:
    cube('Veranda column',(xx,-3.53,1.44),(.17,.17,2.45),cream)
    cube('Veranda column foot',(xx,-3.53,.44),(.30,.3,.50),cream)
for sign in [-1,1]:window('Bungalow side window',sign*3.04,.25,1.65,1.5,1.22,sign*math.pi/2)
chimney(1.4,1.0,4.03,rmat)
# 4. Two-story main volume with a lower attached garage.
current=collection('04 Lilac family house',houses);root=empty('House_Family_ROOT',(12,8,0));house_roots.append(root)
wall=material('Family house walls','B9ABCF');rmat=material('Family house roof','637C9C');accent=material('Family house door','E7AD7D')
wallblock(-1.10,.1,3.9,4.7,5.1,wall);roof('Family main gable',-1.1,.1,4.5,5.3,5.24,1.36,rmat)
wallblock(2.15,.30,2.65,4.3,2.64,wall);roof('Garage gable',2.15,.30,3.08,4.85,2.78,.92,rmat)
door('Family front door',-1.70,-2.31,accent)
window('Family ground window',-.2,-2.29,1.62,.83,1.18)
for xx in [-2.18,-.20]:window('Family upper window',xx,-2.29,3.96,1.04,1.30)
for zz in [1.65,3.96]:window('Family left window',-3.08,.5,zz,1.1,1.3,-math.pi/2)
cube('Garage door surround',(2.15,-1.92,1.31),(2.30,.18,2.33),cream)
cube('Garage door',(2.15,-2.04,1.31),(2.07,.09,2.1),accent)
for zz in [.56,1.01,1.46,1.91]:cube('Garage horizontal seam',(2.15,-2.10,zz),(1.94,.025,.035),cream,soft=.008)
for xx in [1.63,2.16,2.69]:cube('Garage window',(xx,-2.104,2.03),(.39,.025,.30),glass,soft=.025)
roof('Entry awning',-1.7,-2.63,1.52,.88,2.51,.38,rmat)
# Rear windows complete each exterior for viewing from any street direction.
for idx,r in enumerate(house_roots):
    root=r;current=r.users_collection[0]
    yy=[2.28,2.34,2.34,2.50][idx]
    for xx in ([-1.1,1.1] if idx!=3 else [-2.1,-.1]):window('Rear window',xx,yy,1.65,1.08,1.22,math.pi)
    root['asset_type']='House exterior';root['front_axis']='-Y';root['units']='meters';root['lot_size_m']=8.0
    root['customization']='Separate wall, roof, trim, door and window materials.'
# Trees use faceted crowns, tapered branches, and ground-level origins.
tree_roots=[]
def tree_start(name,pos):
    global current,root
    current=collection(name,trees);root=empty('Tree_'+name.split(' ',1)[1].replace(' ','')+'_ROOT',pos);tree_roots.append(root)
    root['asset_type']='Tree';root['units']='meters';root['customization']='Change foliage and bark materials independently.'

def trunk(height,radius,mat):
    cylinder('Tapered trunk',(0,0,.04),(.06,.025,height),radius,radius*.36,mat,n=9)
    for a in [0,1.9,3.8]:cylinder('Root flare',(math.cos(a)*radius*1.9,math.sin(a)*radius*1.9,.06),(0,0,.6),radius*.28,radius*.5,mat,n=7)

tree_start('01 Broad oak',(-12,.2,0));trunk(3.30,.28,wood)
for i,(x,y,z,sx,sy,sz) in enumerate([(-1.0,-.1,3.25,1.3,1.22,1.25),(.98,.05,3.4,1.24,1.24,1.2),(0,.6,3.95,1.45,1.3,1.35),(0,-.62,4.10,1.30,1.3,1.22),(-.6,.25,4.60,1.06,1.04,1.08)]):
    cylinder('Oak branch',(0,0,1.75),(x,y,z),.15,.06,wood)
    blob('Oak crown '+str(i+1),(x,y,z),(sx,sy,sz),leaves[i%2])
tree_start('02 Slender poplar',(-8,.2,0));trunk(4.2,.19,woodlight)
for i,(x,y,z,ss) in enumerate([(0,0,3.7,(.98,.91,1.95)),(-.48,.05,3.10,(.62,.72,1.22)),(.43,.12,3.70,(.64,.67,1.40)),(.05,-.1,4.85,(.65,.63,1.20))]):
    blob('Poplar crown '+str(i+1),(x,y,z),ss,leaves[2+i%2])
for i in range(7):
    z=.42+i*.35
    cube('Birch bark dash',(-.02 if i%2 else .06,-.18+z*.02,z),(.10+(i%3)*.025,.025,.035),wood,soft=.008)
tree_start('03 Tiered pine',(8,.2,0));trunk(4.9,.19,wood)
for idx,(z,rad,h) in enumerate([(1.25,1.47,1.80),(2.15,1.21,1.70),(3.04,.94,1.55),(3.85,.66,1.42)]):
    n=10;v=[]
    for zz,rr in [(z,rad*.84),(z+.23,rad),(z+h*.60,rad*.46)]:
        for j in range(n):
            a=2*math.pi*j/n+.11*idx;v.append((math.cos(a)*rr,math.sin(a)*rr,zz+rng.uniform(-.06,.06)))
    v.append((0,0,z+h));faces=[tuple(reversed(range(n)))]
    for level in range(2):
        for j in range(n):faces.append((level*n+j,level*n+(j+1)%n,(level+1)*n+(j+1)%n,(level+1)*n+j))
    for j in range(n):faces.append((2*n+j,2*n+(j+1)%n,3*n))
    mesh('Pine tier '+str(idx+1),v,faces,leaves[4+idx%2],soft=.025)
tree_start('04 Round maple',(12,.2,0));trunk(2.5,.23,wood)
for i,(x,y,z,ss) in enumerate([(-.78,0,2.75,(1.10,1.1,1.1)),(.85,.10,2.87,(1.12,1.1,1.15)),(0,.18,3.51,(1.25,1.22,1.10)),(0,-.55,2.87,(1.05,.92,1.0))]):
    cylinder('Maple branch',(0,0,1.45),(x,y,z),.12,.05,wood)
    blob('Maple crown '+str(i+1),(x,y,z),ss,leaves[6+i%2])
# Review lighting covers the expanded scene. Original assets remain in place.
studio=bpy.data.collections['Z • Review lighting and camera']
for o in studio.objects:
    if o.type=='LIGHT':
        if 'Key' in o.name:o.location=(-12,-9,17);o.data.energy=5500;o.data.size=11
        elif 'Fill' in o.name:o.location=(12,-2,14);o.data.energy=4500;o.data.size=10
        else:o.location=(1,15,16);o.data.energy=6000;o.data.size=10
        o.rotation_euler=(Vector((0,4,2))-o.location).to_track_quat('-Z','Y').to_euler()
sun_data=bpy.data.lights.new('Neighborhood soft sunlight','SUN');sun_data.energy=1.5;sun_data.angle=.24
sun=bpy.data.objects.new('Neighborhood soft sunlight',sun_data);studio.objects.link(sun);sun.rotation_euler=(.45,-.5,-.4)
cam=scene.camera

def camera(pos,target,scale,w,h):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=scale;scene.render.resolution_x=w;scene.render.resolution_y=h

def render(name):
    scene.render.filepath=str(ROOT/'Art/Previews'/name);bpy.ops.render.render(write_still=True)

camera((16,-31,25),(.7,3.0,2.0),39.0,2400,1500)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_percentage=100
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL';area.spaces.active.overlay.show_overlays=False
            area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.region_3d.view_camera_zoom=4
scene['environment_models']='Four house exteriors and four tree variants. All asset roots at ground level; houses face -Y.'
bpy.context.view_layer.update()
bpy.ops.object.select_all(action='DESELECT')
assert len(house_roots)==4 and len(tree_roots)==4
for r in house_roots+tree_roots:
    assert len([o for o in r.children_recursive if o.type=='MESH'])>3
    assert all(o.data.materials for o in r.children_recursive if o.type=='MESH')
for col in [houses,trees]:
    for obj in col.all_objects:
        if obj.type=='MESH':
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
            bm.to_mesh(obj.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for c in [houses,trees]:
    for o in c.all_objects:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Art/Exports/Neighborhood.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
render('Workshop_All_Models.png')
for c in scene.collection.children:
    if c not in [houses,trees,studio]:c.hide_render=True
trees.hide_render=True
camera((8,-23,18),(.5,8,2.9),35,2400,1100);render('Environment_01_Houses.png')
houses.hide_render=True;trees.hide_render=False
for r,x in zip(tree_roots,[-6,-2,2,6]):r.location=(x,0,0)
camera((9,-22,11),(0,0,2.5),17,2000,1100);render('Environment_02_Trees.png')
# A closer view shows window construction and the porch at character scale.
houses.hide_render=False;trees.hide_render=True
for r in house_roots[2:]:
    for o in r.children_recursive:o.hide_render=True
camera((-5,-5,8.5),(-8,8,2.8),14.0,1600,1300);render('Environment_03_House_Detail.png')
print('ENVIRONMENT_COMPLETE: four houses, four trees, selected asset export, shared scene saved.')
