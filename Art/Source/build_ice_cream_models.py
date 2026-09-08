import bpy, math, random, json
from mathutils import Vector, Quaternion
from pathlib import Path
from math import sin, cos, pi, sqrt

ROOT = Path('/Users/cooperdalton/Ice Cream Truck Prototype')
OUT = ROOT / 'Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend'
random.seed(19)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if not c.objects and not c.children: bpy.data.collections.remove(c)
scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1

# Colors are shared materials, so variants need no texture editing.
def mat(name, hexcode, rough=.45, metal=0):
    h=hexcode.lstrip('#'); rgb=[int(h[i:i+2],16)/255 for i in (0,2,4)]
    rgb=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*rgb,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    return m
cream=mat('Enamel • warm cream','FFF0CE'); pink=mat('Enamel • strawberry','E76D91')
mint=mat('Enamel • mint','70C7B5'); plum=mat('Rubber • deep plum','373248',.62)
graphite=mat('Cooking plates • charcoal','333742',.7); silver=mat('Metal • soft steel','BCC9D0',.28,.6)
gold=mat('Waffle • toasted edges','C27A32',.73); waffle=mat('Waffle • golden center','E5AE55',.72)
batter=mat('Batter • vanilla','F8DDA3',.52); white=mat('Label • ivory','FFF8E7',.7)
red=mat('Light • coral','F17F63'); green=mat('Light • pistachio','A6D76C')
flavors=[mat('Flavor • '+n,c,.65) for n,c in [('Strawberry','F39AB6'),('Vanilla','FFEAC0'),('Chocolate','815343'),('Mint','9BD9BE'),('Blueberry','A99AD9'),('Mango','FFC566'),('Cherry','D97594'),('Cookie cream','E9D5B6'),('Coffee','B6917D'),('Pistachio','B9D39A'),('Blue moon','88CBEB'),('Peach','F3B894')]]
sprinkle_mats=[pink,mint,cream,mat('Sprinkle • lemon','FFE574'),mat('Sprinkle • violet','A08CD8')]

current=None
def collection(name):
    global current
    current=bpy.data.collections.new(name); scene.collection.children.link(current); return current

def put(o,name,material=None):
    o.name=name
    for c in list(o.users_collection): c.objects.unlink(o)
    current.objects.link(o)
    if material: o.data.materials.append(material)
    return o

def empty(name,loc=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None); current.objects.link(o); o.location=loc
    o.empty_display_type='PLAIN_AXES'; o.empty_display_size=.065
    if parent: o.parent=parent
    return o

def finish(o,bevel=0,smooth=True):
    if bevel:
        b=o.modifiers.new('Soft manufactured edges','BEVEL'); b.width=bevel; b.segments=3
    if smooth:
        for p in o.data.polygons: p.use_smooth=True
        if bevel:
            n=o.modifiers.new('Weighted face normals','WEIGHTED_NORMAL'); n.keep_sharp=True; n.weight=40
    return o

def cube(name,loc,dims,material,bevel=.015,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc); o=put(bpy.context.object,name,material)
    o.dimensions=dims; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    finish(o,bevel)
    if parent:o.parent=parent
    return o

def cyl(name,loc,r,depth,material,vertices=32,parent=None,bevel=.006):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc)
    o=put(bpy.context.object,name,material); finish(o,bevel)
    if parent:o.parent=parent
    return o

def sphere(name,loc,scale,material,sub=2,parent=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc)
    o=put(bpy.context.object,name,material); o.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    if parent:o.parent=parent
    return o

def mesh(name,verts,faces,material,parent=None):
    m=bpy.data.meshes.new(name); m.from_pydata(verts,[],faces); m.update()
    o=bpy.data.objects.new(name,m); current.objects.link(o)
    if material:m.materials.append(material)
    if parent:o.parent=parent
    return o

def path(name,points,radius,material,parent=None,closed=False):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=1; c.bevel_depth=radius; c.bevel_resolution=2
    s=c.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points):p.co=(*co,1)
    s.use_cyclic_u=closed
    o=bpy.data.objects.new(name,c); current.objects.link(o); c.materials.append(material)
    if parent:o.parent=parent
    return o

def ring(name,loc,r,t,material,parent=None):
    bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=8,location=loc,major_radius=r,minor_radius=t)
    o=put(bpy.context.object,name,material)
    for p in o.data.polygons:p.use_smooth=True
    if parent:o.parent=parent
    return o

def label(name,text,loc,size,material,parent=None,rot=(pi/2,0,0)):
    c=bpy.data.curves.new(name,'FONT'); c.body=text; c.align_x='CENTER'; c.align_y='CENTER'; c.size=size; c.extrude=.0003
    o=bpy.data.objects.new(name,c);current.objects.link(o); c.materials.append(material);o.location=loc;o.rotation_euler=rot
    if parent:o.parent=parent
    return o

def rounded_points(w,d,r,z,n=5):
    pts=[]
    for cx,cy,start in [(w/2-r,d/2-r,0),(-w/2+r,d/2-r,pi/2),(-w/2+r,-d/2+r,pi),(w/2-r,-d/2+r,3*pi/2)]:
        for j in range(n+1):
            a=start+j*pi/2/n;pts.append((cx+r*cos(a),cy+r*sin(a),z))
    return pts

def vessel(name,profiles,material,parent):
    verts=[]
    for w,d,r,z in profiles:verts+=rounded_points(w,d,r,z)
    n=len(verts)//len(profiles);faces=[]
    for layer in range(len(profiles)-1):
        for i in range(n):
            a=layer*n+i;b=layer*n+(i+1)%n;faces.append((a,b,b+n,a+n))
    faces.append(tuple(reversed(range(n))));faces.append(tuple((len(profiles)-1)*n+i for i in range(n)))
    o=mesh(name,verts,faces,material,parent);finish(o,.002)
    return o

# The cabinet leaves an actual cavity beneath the removable pans.
collection('01 • Prep counter')
counter=empty('PrepCounter_ROOT')
counter['dimensions_m']='2.60 wide × 1.02 deep × 0.96 working height'
for x in [-1.13,1.13]:
    for y in [-.35,.35]:
        cube('Rubber foot',(x,y,.055),(.13,.13,.10),plum,.025,counter)
        cyl('Leg',(x,y,.18),.039,.21,silver,parent=counter)
cube('Cabinet body',(0,.05,.50),(2.51,.85,.58),mint,.05,counter)
cube('Cream fascia',(0,-.39,.69),(2.48,.045,.22),cream,.012,counter)
cube('Pink toe stripe',(0,-.388,.265),(2.39,.02,.055),pink,.008,counter)
for x in [-.82,0,.82]:
    cube('Inset front panel',(x,-.392,.445),(.75,.025,.245),mint,.022,counter)
    cube('Panel handle',(x,-.425,.535),(.19,.036,.035),plum,.013,counter)
# Top surface built around the grid, without a solid slab crossing the ice cream.
cube('Front preparation ledge',(0,-.385,.927),(2.60,.32,.066),cream,.025,counter)
cube('Rear counter rim',(0,.479,.927),(2.60,.06,.066),cream,.012,counter)
for x in [-1.27,1.27]:cube('Side counter rim',(x,.10,.927),(.06,.72,.066),cream,.012,counter)
for i in range(5):cube('Tub grid divider',(-.82+i*.41,.112,.922),(.035,.66,.042),silver,.009,counter)
cube('Tub row divider',(0,.115,.922),(2.48,.036,.042),silver,.009,counter)
cube('Rear splash lip',(0,.506,.99),(2.55,.035,.09),mint,.012,counter)
label('Front badge','SCOOP SHOP',(0,-.419,.688),.065,plum,counter)
for x in [-.48,.48]:sphere('Badge dot',(x,-.425,.688),(.014,.005,.014),pink,parent=counter)

collection('02 • Twelve removable flavor tubs')
for row,y in enumerate([-.052,.285]):
    for col in range(6):
        idx=row*6+col;x=-1.025+col*.41
        root=empty(f'Tub_{row+1}_{col+1}_{flavors[idx].name.split(" • ")[1]}',(x,y,.93))
        root['flavor_material']=flavors[idx].name
        vessel('Removable tub',[(.32,.25,.035,-.21),(.39,.32,.045,0),(.39,.32,.045,.016),(.356,.286,.038,.016),(.295,.222,.03,-.19)],silver,root)
        # A triangulated rounded mound keeps the ice cream stylized and distinct from its tub.
        verts=[(0,0,-.015)];rings=8;steps=32
        for j in range(1,rings+1):
            rr=j/rings
            for k in range(steps):
                a=2*pi*k/steps
                xx=math.copysign(abs(cos(a))**.48,cos(a))*.166*rr
                yy=math.copysign(abs(sin(a))**.48,sin(a))*.130*rr
                zz=-.032+.027*(1-rr**2)+.008*sin(xx*73+idx)*cos(yy*67+idx)+random.uniform(-.003,.003)
                verts.append((xx,yy,zz))
        faces=[]
        for k in range(steps):faces.append((0,1+k,1+(k+1)%steps))
        for j in range(rings-1):
            for k in range(steps):
                a=1+j*steps+k;b=1+j*steps+(k+1)%steps;c=a+steps;d=b+steps
                faces.extend([(a,c,d),(a,d,b)])
        o=mesh('IceCream_Fill • '+str(idx+1),verts,faces,flavors[idx],root)
        for p in o.data.polygons:p.use_smooth=True
        if idx in [2,3,7]:
            for k in range(14):
                xx=random.uniform(-.14,.14);yy=random.uniform(-.10,.10)
                chip=cube('Chocolate fleck',(xx,yy,-.008),(.010,.007,.005),gold if idx==7 else plum,.001,root)
                chip.rotation_euler.z=random.uniform(0,pi)

collection('03 • Six cone holders')
for i in range(6):
    root=empty('ConeHolder_'+str(i+1),(-1.025+i*.41,-.392,.96))
    cube('Holder foot',(0,0,.012),(.135,.12,.024),pink,.026,root)
    for yy in [-.042,.042]:
        path('Support',[(0,yy,.018),(0,yy,.16)],.005,silver,root)
    ring('Open upper ring',(0,0,.157),.055,.007,silver,root)
    ring('Open lower ring',(0,0,.055),.025,.005,silver,root)
    empty('ConePlacement_SOCKET',(0,0,.036),root)

collection('04 • Waffle station')
station=empty('WaffleStation_ROOT',(-1.73,-.025,0))
for x in [-.27,.27]:
    for y in [-.32,.32]:cube('Station leg',(x,y,.46),(.065,.065,.84),mint,.016,station)
cube('Station shelf',(0,0,.30),(.65,.78,.045),pink,.013,station)
cube('Station worktop',(0,0,.927),(.74,.97,.066),cream,.025,station)
maker=empty('WaffleMaker_ROOT',(0,0,.96),station)
for x in [-.15,.15]:
    for y in [-.12,.12]:cube('Appliance foot',(x,y,.012),(.08,.065,.024),plum,.012,maker)
cyl('Lower pink housing',(0,0,.055),.232,.075,pink,parent=maker,bevel=.014)
cyl('Lower dark rim',(0,0,.089),.221,.025,plum,parent=maker)
cyl('Lower cooking plate',(0,0,.106),.199,.015,graphite,parent=maker,bevel=.002)

def waffle_grid(name,r,z,material,parent,thick=.009):
    for direction in [0,1]:
        for i in range(-4,5):
            a=i*.04
            if abs(a)>r:continue
            length=2*sqrt(r*r-a*a)
            loc=(a,0,z) if direction==0 else (0,a,z)
            dims=(thick,length,.010) if direction==0 else (length,thick,.010)
            cube(name,loc,dims,material,.002,parent)
waffle_grid('Lower iron grid',.192,.118,graphite,maker)
# Every upper component belongs to a hinge at the rear edge of the appliance.
hinge=empty('Lid_HINGE • rotate local X',(0,.19,.18),maker)
hinge.rotation_euler.x=math.radians(-108)
hinge['closed_angle_degrees']=0;hinge['open_angle_degrees']=-108
cyl('Lid pink shell',(0,-.19,.04),.232,.066,pink,parent=hinge,bevel=.014)
cyl('Lid cream accent',(0,-.19,.078),.210,.018,cream,parent=hinge)
cyl('Lid gasket',(0,-.19,.001),.218,.018,plum,parent=hinge)
cyl('Upper cooking plate',(0,-.19,-.012),.198,.012,graphite,parent=hinge,bevel=.002)
upper=empty('Upper plate grid',(0,-.19,-.022),hinge)
waffle_grid('Upper iron grid',.192,0,graphite,upper)
for x in [-.115,.115]:cube('Handle bracket',(x,-.392,.06),(.032,.075,.044),plum,.009,hinge)
cube('Lid handle',(0,-.433,.065),(.29,.05,.055),plum,.018,hinge)
bar=cyl('Hinge pin',(0,.19,.18),.025,.29,silver,parent=maker);bar.rotation_euler.y=pi/2
cube('Status panel',(0,-.221,.056),(.17,.025,.044),plum,.009,maker)
for x,m in [(-.040,red),(.040,green)]:sphere('Status lamp',(x,-.237,.06),(.011,.006,.011),m,parent=maker)

for x in [-.11,.11]:cube('Rear hinge support',(x,.19,.13),(.04,.05,.10),plum,.01,maker)

collection('05 • Batter and cooked waffle')
waffle_root=empty('CookedWaffle_ROOT',(-1.73,-.025,1.091))
cyl('Cooked waffle disc',(0,0,0),.170,.014,waffle,parent=waffle_root,bevel=.003)
waffle_grid('Golden waffle lattice',.166,.012,gold,waffle_root,.008)
ring('Waffle outer edge',(0,0,.009),.166,.004,gold,waffle_root)
# Raw batter is an alternate state, kept hidden in the presentation.
raw=empty('RawBatter_ROOT',(-1.73,-.025,1.09))
o=sphere('Raw batter portion',(0,0,0),(.15,.15,.008),batter,sub=3,parent=raw);o.hide_render=True;o.hide_set(True)
raw['usage']='Alternate state to the cooked waffle. Enable for pouring stage.'

collection('06 • Batter bottle')
bottle=empty('BatterBottle_ROOT',(-1.83,-.35,.96))
def lathe(name,profile,material,parent,n=32):
    verts=[]
    for r,z in profile:
        for i in range(n):a=2*pi*i/n;verts.append((r*cos(a),r*sin(a),z))
    faces=[]
    for j in range(len(profile)-1):
        for i in range(n):a=j*n+i;b=j*n+(i+1)%n;faces.append((a,b,b+n,a+n))
    faces.extend([tuple(reversed(range(n))),tuple((len(profile)-1)*n+i for i in range(n))])
    o=mesh(name,verts,faces,material,parent)
    for p in o.data.polygons:p.use_smooth=True
    return o
lathe('Squeeze bottle body',[(.046,0),(.055,.012),(.058,.04),(.058,.175),(.052,.193),(.030,.207),(.030,.225)],pink,bottle)
cyl('Bottle label band',(0,0,.115),.0585,.105,cream,parent=bottle,bevel=.002)
cyl('Bottle collar',(0,0,.222),.035,.024,pink,parent=bottle)
lathe('Pour nozzle',[(.017,.234),(.014,.25),(.006,.283),(.004,.287)],pink,bottle)
label('Batter label','BATTER',(0,-.0595,.126),.022,plum,bottle)
label('Batter sublabel','WAFFLE MIX',(0,-.0595,.097),.009,plum,bottle)
empty('Pour_SOCKET',(0,0,.287),bottle)

collection('07 • Waffle cones and ice cream')
def cone(name,loc):
    root=empty(name,loc)
    import runpy
    helper=runpy.run_path(str(ROOT/'Art/Source/flat_waffle_cone.py'))
    o=bpy.data.objects.new('Hollow waffle cone',helper['build_cone_mesh']())
    current.objects.link(o);o.parent=root
    empty('Scoop_SOCKET',(0,0,.204),root)
    return root

def scoop(parent,loc,material,name='IceCreamScoop'):
    root=empty(name,loc,parent)
    core=sphere('Scoop body',(0,0,.018),(.079,.076,.075),material,sub=3,parent=root)
    for v in core.data.vertices:
        co=v.co;co*=1+.027*sin(co.x*130+co.y*82)*cos(co.z*140)
    for i in range(9):
        a=2*pi*i/9;sphere('Scalloped scoop edge',(.055*cos(a),.055*sin(a),-.017),(.028,.027,.022),material,parent=root)
    return root
plain=cone('EmptyCone_ROOT',(-.615,-.392,.996))
served=cone('FinishedCone_ROOT',(-.205,-.392,.996))
scoop_root=scoop(served,(0,0,.201),flavors[0])
for i in range(40):
    theta=random.uniform(.12,1.5);a=random.uniform(0,2*pi)
    p=(.080*sin(theta)*cos(a),.077*sin(theta)*sin(a),.018+.077*cos(theta))
    o=cube('Sprinkle on scoop',p,(.010,.003,.003),sprinkle_mats[i%5],.0012,scoop_root)
    normal=Vector((sin(theta)*cos(a),sin(theta)*sin(a),cos(theta)))
    o.rotation_euler=normal.to_track_quat('Z','Y').to_euler();o.rotation_euler.rotate_axis('Z',random.uniform(0,2*pi))

collection('08 • Ice cream scooper')
scooper=empty('Scooper_ROOT',(.57,-.50,.991))
scooper.rotation_euler.z=math.radians(0)
cube('Scooper grip',(-.075,0,0),(.18,.043,.039),plum,.018,scooper)
cube('Grip accent',(-.147,0,0),(.028,.046,.041),pink,.012,scooper)
cube('Metal shaft',(.043,0,.002),(.11,.017,.018),silver,.006,scooper)
# An open hemispherical bowl, with thickness, can visibly contain a scoop.
verts=[];n=32;bands=10
for r in [.056,.051]:
    for j in range(bands+1):
        t=.025+(pi/2-.025)*j/bands
        for k in range(n):a=2*pi*k/n;verts.append((.136+r*sin(t)*cos(a),r*sin(t)*sin(a),.027-r*cos(t)))
faces=[];layer=(bands+1)*n
for side in range(2):
    for j in range(bands):
        for k in range(n):
            a=side*layer+j*n+k;b=side*layer+j*n+(k+1)%n
            face=(a,b,b+n,a+n);faces.append(face if side==0 else tuple(reversed(face)))
for k in range(n):a=bands*n+k;b=bands*n+(k+1)%n;faces.append((a,b,b+layer,a+layer))
o=mesh('Open steel scoop bowl',verts,faces,silver,scooper)
for p in o.data.polygons:p.use_smooth=True
ring('Scoop bowl lip',(.136,0,.027),.0535,.0025,silver,scooper)
empty('HeldScoop_SOCKET',(.136,0,.027),scooper)

collection('09 • Sprinkle shaker')
shaker=empty('SprinkleShaker_ROOT',(1.19,-.35,.96))
lathe('Shaker body',[(.041,0),(.05,.01),(.05,.132),(.043,.151),(.038,.157)],cream,shaker)
cyl('Pink shaker cap',(0,0,.16),.048,.033,pink,parent=shaker,bevel=.005)
for k in range(6):
    a=2*pi*k/6;cyl('Cap opening',(.025*cos(a),.025*sin(a),.177),.0035,.001,plum,vertices=12,parent=shaker,bevel=0)
label('Sprinkles label','SPRINKLES',(0,-.0505,.10),.014,plum,shaker)
for i in range(18):
    a=random.uniform(-2.7,-.45);z=random.uniform(.025,.077)
    p=(.0505*cos(a),.0505*sin(a),z)
    o=cube('Label sprinkle',p,(.004,.002,.012),sprinkle_mats[i%5],.001,shaker);o.rotation_euler.z=a-pi/2;o.rotation_euler.y=random.uniform(-.6,.6)
empty('SprinkleEmission_SOCKET',(0,0,.18),shaker)

# Consolidate decorative mesh parts under each interaction root to keep the Outliner usable.
# Moving roots, sockets, materials, and removable items remain separate.
for c in list(scene.collection.children):
    for o in list(c.objects):
        if o.type in {'CURVE','FONT'}:
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')

assets=[o for c in scene.collection.children for o in c.objects]
for o in assets:
    if o.type=='MESH':
        bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
# Join mesh parts sharing a parent, except ice cream fills, which must remain independently editable.
for c in list(scene.collection.children):
    parents={o.parent for o in c.objects if o.type=='MESH'}
    for p in parents:
        group=[o for o in c.objects if o.type=='MESH' and o.parent==p and not o.name.startswith('IceCream_Fill') and not o.hide_render]
        if len(group)>1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:o.select_set(True)
            bpy.context.view_layer.objects.active=group[0]
            bpy.ops.object.join();group[0].name=(p.name.split(' • ')[0] if p else c.name)+'_Mesh'

import runpy
runpy.run_path(str(ROOT/'Art/Source/add_scoop_variants.py'))['add_variants']()

collection('99 • Studio presentation • exclude from game export')
stage=current
floor=mat('Studio • muted blueberry','777D9B',.82)
cube('Studio floor',(0,0,-.06),(200,200,.10),floor,.01)
world=scene.world or bpy.data.worlds.new('Studio world');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.38,.5,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.35

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size,target):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);current.objects.link(o);o.location=loc;aim(o,target)
area('Key softbox',(-3,-4,6),700,(1,.86,.72),4,(0,0,.6))
area('Fill softbox',(4,-1,4),500,(.76,.86,1),3,(0,0,.8))
area('Rim softbox',(0,3,5),850,(1,.79,.68),3,(0,0,.8))
d=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',d);current.objects.link(cam);scene.camera=cam
cam.location=(-3.5,-4.8,3.6);aim(cam,(-.38,0,.74));d.type='ORTHO';d.ortho_scale=4.65;d.lens=50
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1700;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
# Material color mode makes the saved scene readable immediately without shader compilation.
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='SOLID';a.spaces.active.shading.color_type='MATERIAL'
            a.spaces.active.shading.light='STUDIO';a.spaces.active.shading.show_shadows=True
            a.spaces.active.region_3d.view_perspective='CAMERA'
# Hide studio clutter in the working viewport only.
for o in stage.objects:
    if o.type!='CAMERA':o.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
bpy.context.view_layer.objects.active=None
scene['asset_notes']='First modeling pass. Separate roots for pickup props, tubs, cone holders and hinged lid. Material colors are editable. No gameplay code.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
# Export only the models, preserving their node hierarchy and material colors.
bpy.ops.object.select_all(action='DESELECT')
for c in scene.collection.children:
    if c!=stage:
        for o in c.objects:
            if not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Art/Exports/IceCreamPreparation.glb'),use_selection=True,export_format='GLB',export_yup=True)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(ROOT/'Art/Previews/01_Preparation_Set.png')
bpy.ops.render.render(write_still=True)
cam.location=(-2.6,-2.6,2.9);aim(cam,(-1.35,-.08,1.02));cam.data.ortho_scale=1.75
scene.render.resolution_x=1400;scene.render.resolution_y=1200
scene.render.filepath=str(ROOT/'Art/Previews/02_Waffle_and_Props.png');bpy.ops.render.render(write_still=True)
cam.location=(1.6,-2.6,3.6);aim(cam,(0,0,1));cam.data.ortho_scale=2.95
scene.render.resolution_x=1600;scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'Art/Previews/03_Counter_Detail.png');bpy.ops.render.render(write_still=True)
hinge.rotation_euler.x=0
cam.location=(-2.65,-2.65,2.55);aim(cam,(-1.7,-.03,1.10));cam.data.ortho_scale=.95
scene.render.resolution_x=1000;scene.render.resolution_y=1000
scene.render.filepath=str(ROOT/'Art/Previews/04_Closed_Waffle_Maker.png');bpy.ops.render.render(write_still=True)
print('ASSET_BUILD_COMPLETE',str(OUT))
