"""Add the remaining prototype model kit to the preserved shared workshop."""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector, Matrix
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
assert 'G • Modular ground' not in bpy.data.collections, 'This additive builder has already run.'
old={o.name:(o.matrix_world.copy(),o.data.name if o.data else None) for o in scene.objects if o.type not in {'LIGHT','CAMERA'}}

def col(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
roads=col('G • Modular ground');park=col('H • Park and street props');props=col('I • Supplies and handheld props');delivery=col('J • Delivery bike and stand')
current=props;root=None;assets=[]
def mat(name,hex,rough=.6,metal=0):
    m=bpy.data.materials.new('Town kit • '+name);m.use_nodes=True
    rgb=[int(hex[i:i+2],16)/255 for i in (0,2,4)];rgb=[v/12.92 if v<.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    m.diffuse_color=(*rgb,1);bs=m.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal;return m
cream=mat('Cream','FFF0D5');pink=mat('Strawberry','E98CA6');mint=mat('Mint','77BFB0');purple=mat('Plum','716185');dark=mat('Charcoal','343745');silver=mat('Brushed metal','B0BCC2',.36,.45);yellow=mat('Butter yellow','F2CF73');wood=mat('Warm wood','BE8960');grass=mat('Grass','98B962');leaf=mat('Shrub','659C6A');asphalt=mat('Road','666979');pavement=mat('Sidewalk','D7C8B6');white=mat('Road paint','F8EDD5');red=mat('Coral','D97575');blue=mat('Blue','72ADCB');cardboard=mat('Cardboard','BC976E');brown=mat('Soil','81624F')

def empty(name,pos=(0,0,0),parent=None):
    o=bpy.data.objects.new(name,None);current.objects.link(o);o.location=pos;o.parent=parent;o.empty_display_size=.12;return o

def start(name,pos,c):
    global current,root
    current=c;root=empty(name+'_ROOT',pos);root['units']='meters';root['front']='local -Y';assets.append(root);return root

def link(o,name,m,parent=None):
    o.name=name
    for c in list(o.users_collection):c.objects.unlink(o)
    current.objects.link(o);o.parent=parent or root
    if m:o.data.materials.append(m)
    return o

def finish(o,bevel=0,smooth=True):
    if smooth:
        for p in o.data.polygons:p.use_smooth=True
    if bevel:
        b=o.modifiers.new('Rounded edges','BEVEL');b.width=bevel;b.segments=1
        n=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');n.keep_sharp=True
    return o

def box(name,pos,size,m,parent=None,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos);o=link(bpy.context.object,name,m,parent);o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,bevel)

def cyl(name,a,b,r,m,parent=None,n=12,r2=None):
    v=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=n,radius1=r,radius2=r if r2 is None else r2,depth=v.length,location=(Vector(a)+Vector(b))/2)
    o=link(bpy.context.object,name,m,parent);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return finish(o)

def blob(name,pos,size,m,parent=None):
    if name in {'Petal','Flower center'}:bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=pos)
    else:bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=pos)
    o=link(bpy.context.object,name,m,parent);o.scale=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o)

def torus(name,pos,r,t,m,parent=None,rotation=(0,0,0),n=20):
    bpy.ops.mesh.primitive_torus_add(major_segments=n,minor_segments=6,location=pos,major_radius=r,minor_radius=t,rotation=rotation)
    return finish(link(bpy.context.object,name,m,parent))

def custom(name,v,f,mats,indices=None):
    me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);current.objects.link(o);o.parent=root
    for m in mats:me.materials.append(m)
    if indices:
        for p,i in zip(me.polygons,indices):p.material_index=i
    return o

def socket(name,pos,parent=None):
    o=empty(name,pos,parent or root);o['purpose']='Attachment anchor for future interaction setup';return o

def handle(name,z,w,d,m,parent=None,x=0,y=0):
    for s in [-1,1]:box(name+' upright',(x+s*w/2,y,z-d/2),(.065,.075,d),m,parent,.025)
    box(name+' grip',(x,y,z),(w+.065,.075,.075),m,parent,.03)

def hollow_container(name,z0,z1,r0,r1,m,n=16):
    v=[];f=[]
    for r,z in [(r0,z0),(r1,z1),(r1-.025,z1),(r0-.025,z0+.03)]:
        for i in range(n):
            a=i*math.tau/n;v.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(3):
        for i in range(n):f.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    f.extend([tuple(reversed(range(n))),tuple(range(3*n,4*n))])
    return finish(custom(name,v,f,[m]))

# Ground tiles have identical 8 m bounds and matching road edge sections.
ports={'N':(0,4,0),'E':(4,0,0),'S':(0,-4,0),'W':(-4,0,0)}
tile_specs=[('Road_Straight','NS',(-12,-22,0)),('Road_Corner','NE',(-4,-22,0)),('Road_TJunction','NES',(4,-22,0)),('Road_Crossroads','NESW',(12,-22,0)),('Road_DeadEnd','S',(-12,-14,0)),('Road_Crosswalk','NS',(-4,-14,0)),('Grass_Cell','',(4,-14,0))]
for name,exits,pos in tile_specs:
    start(name,pos,roads);root['grid_size_m']=8.;root['road_width_m']=4.;root['road_ports']=exits;root['edge_profile']='4 m road, 0.5 m sidewalk each side, grass to tile boundary'
    if not exits:
        box('Grass ground',(0,0,-.05),(8,8,.22),grass,bevel=0)
        continue
    n=16;step=.5
    def isroad(x,y):
        return bool(exits) and ((abs(x)<2 and abs(y)<2) or ('N' in exits and abs(x)<2 and y>0) or ('S' in exits and abs(x)<2 and y<0) or ('E' in exits and abs(y)<2 and x>0) or ('W' in exits and abs(y)<2 and x<0))
    cells={}
    for ix in range(n):
        for iy in range(n):
            x=-4+(ix+.5)*step;y=-4+(iy+.5)*step
            kind=0 if isroad(x,y) else 1 if any(isroad(x+dx*step,y+dy*step) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]) else 2
            cells[ix,iy]=kind
    v=[];f=[];mi=[];lookup={};heights=[0,.12,.06]
    def vid(p):
        if p not in lookup:lookup[p]=len(v);v.append(p)
        return lookup[p]
    def face(points,index):f.append(tuple(vid(p) for p in points));mi.append(index)
    for (ix,iy),kind in cells.items():
        x=-4+ix*step;y=-4+iy*step;z=heights[kind]
        face([(x,y,z),(x+step,y,z),(x+step,y+step,z),(x,y+step,z)],kind)
        for dx,dy,a,b in [(0,-1,(x,y),(x+step,y)),(1,0,(x+step,y),(x+step,y+step)),(0,1,(x+step,y+step),(x,y+step)),(-1,0,(x,y+step),(x,y))]:
            other=cells.get((ix+dx,iy+dy));zz=heights[other] if other is not None else -.16
            if z>zz:face([(*a,zz),(*b,zz),(*b,z),(*a,z)],kind)
    face([(-4,4,-.16),(4,4,-.16),(4,-4,-.16),(-4,-4,-.16)],2)
    custom(name+'_Surface',v,f,[asphalt,pavement,grass],mi)
    for p in exits:socket(name+'_RoadPort_'+p,ports[p])
    if name!='Road_Corner':
        for p in exits:
            for a in [2.65,3.55]:
                vertical=p in 'NS';sgn=1 if p in 'NE' else -1
                box('Center dash',(0,sgn*a,.008) if vertical else (sgn*a,0,.008),(.075,.45,.012) if vertical else (.45,.075,.012),yellow,bevel=0)
    if name=='Road_Crosswalk':
        for x in [-1.55,-1.05,-.55,-.05,.45,.95,1.45]:box('Crosswalk paint',(x,0,.009),(.28,1.1,.015),white,bevel=0)
    if name=='Road_DeadEnd':box('End marking',(0,1.5,.009),(2.8,.10,.015),yellow,bevel=0)
# Loose pieces support manual layout between cells.
start('Sidewalk_Straight',(18,-22,0),roads);box('Paving',(0,0,.055),(1,8,.11),pavement,bevel=.015)
for y in [-3,-2,-1,0,1,2,3]:box('Joint',(0,y,.112),(.94,.012,.006),cardboard,bevel=0)
start('Sidewalk_Corner',(18,-16,0),roads);box('Paving horizontal',(0,0,.055),(2,1,.11),pavement,bevel=.015);box('Paving vertical',(-.5,1,.055),(1,1,.11),pavement,bevel=.015)
start('Curb_Ramp',(18,-13.5,0),roads);custom('Sloped curb',[(-.6,-.5,0),(.6,-.5,0),(.6,.5,0),(-.6,.5,0),(-.6,-.5,.015),(.6,-.5,.015),(.6,.5,.12),(-.6,.5,.12)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],[pavement])
# Park furniture uses broad shapes and a few shared material slots.
start('Park_Bench',(10,-8,0),park)
for x in [-.68,.68]:
    for y in [-.22,.22]:cyl('Bench leg',(x,y,0),(x,y,.51),.055,purple)
    cyl('Back upright',(x,.24,.25),(x,.33,1.05),.045,purple)
for y in [-.22,0,.22]:box('Seat plank',(0,y,.49),(1.7,.20,.10),wood)
for z in [.74,.94]:box('Back plank',(0,.31,z),(1.7,.09,.16),wood)
for x in [-.78,.78]:box('Armrest',(x,0,.73),(.10,.65,.10),purple)
bench=root
start('Picnic_Table',(13,-7.7,0),park)
for x in [-.6,.6]:
    for s in [-1,1]:cyl('Splayed table leg',(x,s*.57,0),(x,s*.23,.77),.06,mint)
    box('Bench support',(x,0,.36),(.12,1.75,.12),mint)
for y in [-.3,-.1,.1,.3]:box('Table plank',(0,y,.78),(1.8,.18,.09),wood)
for y in [-.73,.73]:box('Picnic seat',(0,y,.43),(1.85,.30,.10),wood)
picnic=root
start('Park_TrashBin',(15,-7.6,0),park);hollow_container('Bin body',.08,.80,.30,.34,mint);torus('Top rim',(0,0,.81),.315,.035,purple,n=16)
box('Foot',(0,0,.04),(.62,.62,.08),purple)
trashbin=root
start('Street_Lamp',(16.7,-7.8,0),park);cyl('Lamp base',(0,0,0),(0,0,.24),.20,purple);cyl('Lamp post',(0,0,.2),(0,0,3.0),.065,purple)
box('Lantern base',(0,0,3.02),(.46,.46,.12),purple);box('Lantern glass',(0,0,3.28),(.34,.34,.42),yellow)
for x in [-.19,.19]:
    for y in [-.19,.19]:box('Lantern frame',(x,y,3.27),(.04,.04,.44),purple,None,.008)
cyl('Lantern cap',(0,0,3.49),(0,0,3.68),.34,purple,n=4,r2=.06)
lamp=root
start('Picket_Fence',(11,-10,0),park)
for z in [.38,.78]:box('Fence rail',(0,.04,z),(2.4,.08,.10),cream)
for x in [-1.1,-.73,-.36,0,.36,.73,1.1]:
    box('Picket',(x,0,.53),(.19,.12,.98),cream,None,.025);cyl('Picket top',(x,0,1.01),(x,0,1.14),.12,cream,n=4,r2=0)
fence=root
start('Shrub_Round',(14,-10,0),park)
for x,y,z,s in [(-.28,0,.42,.47),(.29,.06,.40,.44),(0,-.04,.66,.43)]:blob('Shrub foliage',(x,y,z),(s,s,s),leaf)
shrub=root
start('Flower_Patch',(15.5,-10,0),park)
for j,(x,y) in enumerate([(-.3,0),(.05,.15),(.28,-.13)]):
    z=.30+.08*(j%2);cyl('Stem',(x,y,0),(x,y,z),.014,leaf,n=6)
    for i in range(5):
        a=i*math.tau/5;blob('Petal',(x+.07*math.cos(a),y+.07*math.sin(a),z),(.072,.05,.028),pink if j%2 else cream)
    blob('Flower center',(x,y,z+.02),(.04,.04,.025),yellow)
flowers=root
start('Mailbox',(17.4,-10,0),park);box('Mailbox post',(0,0,.6),(.12,.12,1.2),wood);box('Mailbox shell',(0,-.04,1.25),(.43,.56,.37),blue,bevel=.09);box('Mailbox door',(0,-.335,1.25),(.37,.03,.31),cream,bevel=.07);box('Mail slot',(0,-.354,1.28),(.25,.01,.025),dark,bevel=.005)
flag=empty('Mailbox_Flag_PIVOT',(.24,.09,1.21),root);box('Flag staff',(0,0,.15),(.025,.035,.3),red,flag,.007);box('Flag pennant',(0,-.065,.28),(.025,.16,.10),red,flag,.01)
start('Fire_Hydrant',(19,-10,0),park);cyl('Hydrant barrel',(0,0,.05),(0,0,.58),.14,red);blob('Hydrant crown',(0,0,.59),(.17,.17,.12),red)
for s in [-1,1]:cyl('Outlet',(s*.1,0,.37),(s*.25,0,.37),.09,red);cyl('Outlet cap',(s*.24,0,.37),(s*.29,0,.37),.11,cream)
cyl('Hydrant foot',(0,0,0),(0,0,.08),.21,purple)
start('Street_Sign',(19,-7.6,0),park);cyl('Sign pole',(0,0,0),(0,0,2.3),.045,silver);cyl('Octagonal sign border',(0,-.035,2.02),(0,.035,2.02),.34,cream,n=8);cyl('Octagonal sign face',(0,-.049,2.02),(0,-.037,2.02),.295,red,n=8)
# Simple cross symbol is editable geometry, with no shop wordmarks.
box('Sign symbol',(0,-.057,2.02),(.29,.012,.055),cream,bevel=.01)
# Additional handheld and supply models, displayed on a shallow review plinth.
start('Boombox',(-5.1,-7.2,0),props);box('Radio case',(0,0,.26),(.82,.27,.46),cream,bevel=.07)
for x in [-.245,.245]:
    cyl('Speaker trim',(x,-.15,.26),(x,-.16,.26),.167,pink,n=20);cyl('Speaker cone',(x,-.165,.26),(x,-.176,.26),.137,dark,n=20);blob('Speaker dust cap',(x,-.185,.26),(.057,.017,.057),purple)
box('Cassette frame',(0,-.15,.22),(.17,.035,.12),pink);box('Cassette window',(0,-.174,.22),(.105,.012,.048),dark,bevel=.005)
for x in [-.13,-.043,.043,.13]:box('Radio button',(x,0,.51),(.066,.085,.035),pink,bevel=.012)
handle('Carry handle',.65,.52,.15,purple);socket('Boombox_Grip_SOCKET',(0,0,.65));cyl('Antenna',(.30,.07,.49),(.38,.07,.85),.01,silver,n=8)
start('Baseball_Bat',(-3.8,-7.2,0),props)
# A single lathed mesh keeps the bat inexpensive.
v=[];f=[]
for z,rad in [(0,.035),(.025,.045),(.055,.027),(.27,.030),(.48,.054),(.70,.065),(.81,.052),(.83,.01)]:
    for i in range(12):a=i*math.tau/12;v.append((rad*math.cos(a),rad*math.sin(a),z))
for j in range(7):
    for i in range(12):f.append((j*12+i,j*12+(i+1)%12,(j+1)*12+(i+1)%12,(j+1)*12+i))
f.extend([tuple(reversed(range(12))),tuple(range(84,96))]);finish(custom('Bat',v,f,[wood]));socket('Bat_Grip_SOCKET',(0,0,.17))
start('Delivery_Cooler',(-2.7,-7.2,0),props);box('Cooler floor',(0,0,.04),(.65,.44,.08),mint,bevel=.018)
for x in [-.3,.3]:box('Cooler side',(x,0,.25),(.05,.44,.42),mint,bevel=.015)
for y in [-.195,.195]:box('Cooler wall',(0,y,.25),(.55,.05,.42),mint,bevel=.015)
lid=empty('Cooler_Lid_HINGE',(0,.215,.47),root);box('Cooler lid',(0,-.215,.015),(.69,.48,.085),cream,lid,.035);lid['open_local_x_degrees']=-100
handle('Cooler handle',.17,.34,.12,purple,lid,y=-.215);box('Cooler latch',(0,-.24,.42),(.10,.03,.14),purple);socket('Cooler_Grip_SOCKET',(0,0,.64));cooler=root
start('Supply_Crate',(-1.4,-7.2,0),props)
box('Crate floor',(0,0,.04),(.55,.43,.08),wood)
for x in [-.24,.24]:
    for y in [-.18,.18]:box('Corner post',(x,y,.20),(.065,.065,.36),wood)
for z in [.15,.31]:
    for y in [-.205,.205]:box('Crate long slat',(0,y,z),(.55,.045,.10),wood)
    for x in [-.26,.26]:box('Crate end slat',(x,0,z),(.045,.43,.10),wood)
socket('Crate_Grip_SOCKET',(0,0,.30))
start('Ingredient_Carton',(-.45,-7.2,0),props);box('Carton',(0,0,.17),(.23,.17,.34),cream);box('Carton flavor band',(0,-.087,.16),(.21,.012,.11),pink,None,.008)
custom('Carton folded top',[(-.115,-.085,.34),(.115,-.085,.34),(.115,.085,.34),(-.115,.085,.34),(-.115,0,.43),(.115,0,.43)],[(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5),(0,3,2,1)],[pink]);socket('Carton_Grip_SOCKET',(0,0,.2))
start('Restock_Box',(.45,-7.2,0),props);box('Supply box',(0,0,.22),(.55,.4,.44),cardboard);box('Packing tape',(0,0,.447),(.07,.41,.012),cream,bevel=0);socket('Box_Grip_SOCKET',(0,0,.22))
start('Serving_Cup',(1.35,-7.2,0),props)
# Hollow cup with a flat interior bottom, no unnecessary subdivision.
v=[];f=[]
for rad,z in [(.048,0),(.077,.12),(.072,.12),(.044,.012)]:
    for i in range(16):a=i*math.tau/16;v.append((rad*math.cos(a),rad*math.sin(a),z))
for j in range(3):
    for i in range(16):f.append((16*j+i,16*j+(i+1)%16,16*(j+1)+(i+1)%16,16*(j+1)+i))
f.extend([tuple(reversed(range(16))),tuple(range(48,64))]);finish(custom('Cup shell',v,f,[pink]));socket('Cup_Scoop_SOCKET',(0,0,.125))
start('Tasting_Spoon',(1.85,-7.2,0),props);box('Spoon handle',(0,0,.07),(.022,.012,.14),yellow,bevel=.01);blob('Spoon bowl',(0,0,.16),(.037,.009,.048),yellow);socket('Spoon_Grip_SOCKET',(0,0,.065))
start('Napkin_Dispenser',(2.45,-7.2,0),props);box('Dispenser',(0,0,.13),(.25,.18,.25),silver,bevel=.035);box('Napkin slot',(0,-.096,.17),(.16,.015,.09),dark);box('Folded napkin',(0,-.108,.17),(.13,.018,.075),cream)
start('Topping_Jar',(3.25,-7.2,0),props);cyl('Topping jar',(0,0,.02),(0,0,.23),.075,cream,n=16);cyl('Jar lid',(0,0,.23),(0,0,.27),.082,purple,n=16);box('Flavor label',(0,-.074,.14),(.105,.015,.085),pink,bevel=.01);socket('Jar_Grip_SOCKET',(0,0,.13))
start('Serving_Tray',(4.25,-7.2,0),props);box('Tray floor',(0,0,.025),(.52,.32,.035),mint)
for y in [-.15,.15]:box('Tray lip',(0,y,.055),(.52,.025,.065),mint,bevel=.012)
for x in [-.25,.25]:box('Tray lip',(x,0,.055),(.025,.30,.065),mint,bevel=.012)
for i,x in enumerate([-.16,0,.16]):socket('Tray_Cup_'+str(i+1)+'_SOCKET',(x,0,.045))
start('Cleaning_Bucket',(-5.1,-9.2,0),props);hollow_container('Bucket',.02,.32,.14,.18,blue)
handle('Bucket handle',.49,.32,.20,silver);socket('Bucket_Grip_SOCKET',(0,0,.49))
start('Cleaning_Rag',(-4.2,-9.2,0),props);box('Folded cloth',(0,0,.018),(.28,.20,.035),pink,bevel=.012);box('Cloth fold',(0,-.012,.039),(.26,.175,.013),pink,bevel=.006);socket('Rag_Grip_SOCKET',(0,0,.03))
for name,pos,mop in [('Broom',(-3.45,-9.2,0),False),('Mop',(-2.65,-9.2,0),True)]:
    start(name,pos,props);cyl('Tool handle',(0,0,.14),(0,0,1.22),.022,wood,n=10);cyl('Grip',(0,0,1.0),(0,0,1.24),.03,purple,n=10);socket(name+'_Grip_SOCKET',(0,0,.75))
    if mop:
        for x in [-.10,-.05,0,.05,.10]:box('Mop cloth',(x,0,.055),(.05,.22,.10),cream,bevel=.02)
        box('Mop head',(0,0,.12),(.25,.12,.07),mint)
    else:
        box('Broom head',(0,0,.18),(.35,.10,.09),mint);box('Bristle block',(0,0,.07),(.33,.085,.14),yellow,bevel=.01)
        for x in [-.12,-.06,0,.06,.12]:box('Bristle groove',(x,-.046,.06),(.008,.005,.1),wood,bevel=0)
start('Dustpan',(-1.8,-9.2,0),props);box('Dustpan base',(0,0,.012),(.27,.25,.025),pink,bevel=.008)
for x in [-.13,.13]:box('Dustpan edge',(x,0,.04),(.02,.25,.075),pink,bevel=.008)
cyl('Dustpan handle',(0,.10,.05),(0,.3,.14),.023,purple,n=10);socket('Dustpan_Grip_SOCKET',(0,.25,.12))
start('Trash_Bag',(-.85,-9.2,0),props);blob('Tied bag',(0,0,.25),(.21,.18,.25),purple);cyl('Bag neck',(0,0,.45),(0,0,.52),.06,purple,n=8,r2=.027);blob('Bag knot',(0,0,.52),(.08,.045,.04),purple);socket('Bag_Grip_SOCKET',(0,0,.52))
start('Toolbox',(.25,-9.2,0),props);box('Toolbox case',(0,0,.13),(.42,.24,.25),red,bevel=.03);box('Toolbox lid',(0,0,.27),(.44,.26,.06),cream);handle('Toolbox handle',.38,.22,.07,purple);socket('Toolbox_Grip_SOCKET',(0,0,.38))
start('Wrench',(1.2,-9.2,0),props);box('Wrench shaft',(0,0,.12),(.042,.025,.24),silver,bevel=.015)
box('Wrench jaw base',(0,0,.25),(.10,.03,.045),silver,bevel=.01)
for x in [-.045,.045]:box('Open jaw',(x,0,.283),(.025,.03,.07),silver,bevel=.008)
socket('Wrench_Grip_SOCKET',(0,0,.12))
start('Traffic_Cone',(2.1,-9.2,0),props);box('Safety cone base',(0,0,.035),(.32,.32,.07),purple);cyl('Safety cone',(0,0,.07),(0,0,.5),.12,red,n=12,r2=.023);cyl('Reflective band',(0,0,.29),(0,0,.37),.073,cream,n=12,r2=.055)
start('Spare_Tire',(3.25,-9.2,0),props);torus('Spare tire',(0,0,.38),.285,.095,dark,rotation=(math.pi/2,0,0),n=24);cyl('Wheel hub',(0,-.06,.38),(0,.06,.38),.20,silver,n=16);cyl('Hub recess',(0,-.075,.38),(0,-.06,.38),.10,purple,n=12)
# Bike faces -Y. Wheels and steering remain separate articulated roots.
start('Delivery_Bicycle',(-9,-7.0,0),delivery)
rear=empty('Bike_RearWheel_AXLE',(0,.63,.34),root)
def wheel(p,name):
    torus(name+' tire',(0,0,0),.292,.038,dark,p,(0,math.pi/2,0),24);torus(name+' rim',(0,0,0),.26,.015,cream,p,(0,math.pi/2,0),20)
    cyl(name+' hub',(-.08,0,0),(.08,0,0),.042,silver,p,n=12)
    for i in range(8):
        a=i*math.tau/8;cyl(name+' spoke',(0,0,0),(0,.255*math.cos(a),.255*math.sin(a)),.006,silver,p,n=6)
wheel(rear,'Rear')
steer=empty('Bike_Steering_PIVOT',(0,-.62,.85),root);front=empty('Bike_FrontWheel_AXLE',(0,-.05,-.51),steer);wheel(front,'Front')
for x in [-.07,.07]:cyl('Fork',(x,0,-.07),(x,-.05,-.51),.025,mint,steer)
cyl('Steering stem',(0,0,0),(0,-.06,.25),.022,silver,steer);cyl('Handlebar',(-.30,-.06,.25),(.30,-.06,.25),.022,silver,steer)
for s in [-1,1]:cyl('Bike handgrip',(s*.2,-.06,.25),(s*.34,-.06,.25),.03,purple,steer);socket('Bike_Hand_'+str(s)+'_SOCKET',(s*.27,-.06,.25),steer)
A=(0,.63,.34);B=(0,.07,.34);C=(0,.26,.85);D=(0,-.60,.87);E=(0,-.5,.59)
for a,b in [(A,B),(A,C),(B,C),(C,D),(D,E),(E,B)]:cyl('Bike frame',a,b,.035,mint)
cyl('Seatpost',C,(0,.30,1.0),.025,silver);box('Saddle',(0,.32,1.035),(.25,.30,.08),purple,bevel=.04);socket('Bike_Rider_SOCKET',(0,.32,1.10))
crank=empty('Bike_Pedals_AXLE',B,root);cyl('Crank axle',(-.13,0,0),(.13,0,0),.045,silver,crank)
for s in [-1,1]:cyl('Crank arm',(s*.13,0,0),(s*.13,0,s*.13),.018,silver,crank);box('Pedal',(s*.20,0,s*.13),(.16,.09,.04),purple,crank,.012)
box('Chain guard',(.055,.34,.34),(.04,.60,.12),cream,bevel=.04)
for x in [-.15,.15]:cyl('Rack support',(x,.63,.35),(x,.70,.83),.018,silver)
box('Rear carrier',(0,.62,.84),(.40,.46,.045),silver);socket('Bike_Cooler_SOCKET',(0,.64,.87));cyl('Kickstand',(.05,.15,.35),(.28,.20,0),.018,silver)
bike=root
# Copies of the same cooler mesh will be added after static joining.
start('PopUp_Stand',(-13.4,-6.7,0),delivery);box('Stand cabinet',(0,0,.48),(1.9,.88,.94),mint,bevel=.06);box('Stand front panel',(0,-.454,.5),(1.60,.035,.66),cream,bevel=.04);box('Stand counter',(0,-.04,.99),(2.08,1.06,.13),cream,bevel=.04)
for x in [-.91,.91]:cyl('Canopy pole',(x,.34,1.02),(x,.34,2.24),.045,purple)
# A pitched canopy is split into broad alternating stripes.
for i in range(8):
    x=-1.12+i*.28;v=[(x,-.66,2.20),(x+.28,-.66,2.20),(x+.28,0,2.52),(x,0,2.52),(x,.60,2.20),(x+.28,.60,2.20)]
    custom('Canopy stripe',v,[(0,1,2,3),(3,2,5,4)],[pink if i%2 else cream]);box('Canopy valance',(x+.14,-.66,2.13),(.28,.04,.18),pink if i%2 else cream,bevel=.025)
for x in [-.58,0,.58]:
    box('Counter tub rim',(x,.12,1.07),(.48,.50,.04),silver,bevel=.035);box('Ice cream display',(x,.12,1.093),(.39,.41,.025),pink if x<0 else cream if x==0 else mint,bevel=.055)
for x in [-.65,-.3,.05]:torus('Stand cone ring',(x,-.38,1.10),.062,.012,purple,n=16);socket('Stand_Cone_'+str(x)+'_SOCKET',(x,-.38,1.10))
socket('Stand_Service_SOCKET',(0,-.75,1.05));stand=root
# Apply bevels and consolidate fixed pieces per parent, leaving hinges and sockets intact.
for c in [roads,park,props,delivery]:
    for o in list(c.all_objects):
        if o.type=='MESH':
            bpy.context.view_layer.objects.active=o;o.select_set(True)
            for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
            o.select_set(False)
    parents={o.parent for o in list(c.all_objects) if o.type=='MESH'}
    for p in parents:
        meshes=[o for o in list(c.all_objects) if o.type=='MESH' and o.parent==p]
        bpy.ops.object.select_all(action='DESELECT')
        for o in meshes:o.select_set(True)
        bpy.context.view_layer.objects.active=meshes[0]
        if len(meshes)>1:bpy.ops.object.join()
        o=bpy.context.object;o.name=p.name.replace('_ROOT','').replace('_PIVOT','')+'_Mesh'
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
        o.select_set(False)

def duplicate_hierarchy(source,name,parent,pos):
    mapping={}
    for original in [source]+list(source.children_recursive):
        obj=original.copy();current.objects.link(obj);mapping[original]=obj
        obj.name=name+'_'+original.name
        obj.parent=mapping.get(original.parent,parent);obj.matrix_parent_inverse=original.matrix_parent_inverse.copy();obj.matrix_basis=original.matrix_basis.copy()
    dup=mapping[source];dup.location=pos;return dup
current=delivery;duplicate_hierarchy(cooler,'BikeCarrier',bike,(0,.64,.87))
# One populated 8 m park cell; furniture uses linked meshes from the kit.
start('Park_Cell',(12,-14,0),roads);root['grid_size_m']=8.;root['pedestrian_ports']='NESW'
box('Park lawn',(0,0,-.05),(8,8,.22),grass,bevel=0)
import runpy
runpy.run_path(str(R/'Art/Source/park_path_mesh.py'))['create_park_path'](root, roads, pavement, 8, 1.4)
parkroot=root
for p in 'NESW':socket('Park_PathPort_'+p,ports[p])
for src,name,pos in [(bench,'ParkBench',(-2,1.2,.06)),(picnic,'ParkPicnic',(2,2,.06)),(trashbin,'ParkBin',(1,-1,.06)),(lamp,'ParkLamp',(-1.1,-1.2,.06)),(shrub,'ParkShrubA',(-2.6,-2.5,.06)),(shrub,'ParkShrubB',(2.4,-2.5,.06)),(flowers,'ParkFlowers',(-2.1,-2.7,.06)),(fence,'ParkFenceA',(-2.4,3.7,.06)),(fence,'ParkFenceB',(2.4,3.7,.06))]:duplicate_hierarchy(src,name,parkroot,pos)
# Add existing tree data without duplicating its geometry resource.
source=bpy.data.objects['Tree_Roundmaple_ROOT'];duplicate_hierarchy(source,'ParkMaple',parkroot,(-2.3,2.5,.06))
# Separate sample tiles slightly for review; their geometry remains exactly 8 m wide.
for r in assets:
    if r.get('grid_size_m'):
        r.location.x*=1.045
        if r.location.y < -20:r.location.y-=.36
# Expand the completed base cells for the truck's driving scale.
import runpy
runpy.run_path(str(R/'Art/Source/enlarge_road_tiles.py'))['enlarge_tiles']()
# Two low display platforms make tiny props legible together without entering exports.
studio=bpy.data.collections['Z • Review lighting and camera'];current=studio;root=None
for y in [-7.2,-9.2]:
    o=box('Small prop review shelf',(0,y,.37),(11.8,.86,.74),pavement,bevel=.06);o['review_only']=True
for r in assets:
    if r.users_collection[0]==props:r.location.z=.75
# Expand studio ground if it is smaller than this review arrangement.
for o in studio.objects:
    if o.type=='MESH' and not o.get('review_only') and max(o.dimensions.x,o.dimensions.y)>20:o.scale.x*=2;o.scale.y*=2
cam=scene.camera;target=Vector((1,-5.2,1.4));cam.location=(26,-48,39);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=48
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=2400;scene.render.resolution_y=1900;scene.render.resolution_percentage=100
def fit_camera(objects,margin=1.07):
    bpy.context.view_layer.update()
    q=cam.rotation_euler.to_quaternion();inv=q.inverted()
    points=[inv @ (o.matrix_world @ Vector(v)) for o in objects if o.type=='MESH' and not o.hide_render for v in o.bound_box]
    low=Vector(tuple(min(p[i] for p in points) for i in range(3)));high=Vector(tuple(max(p[i] for p in points) for i in range(3)))
    center=(low+high)/2;cam.location=q @ Vector((center.x,center.y,high.z+60))
    cam.data.ortho_scale=max(high.x-low.x,(high.y-low.y)*scene.render.resolution_x/scene.render.resolution_y)*margin
fit_camera([o for c in scene.collection.children if c!=studio for o in c.all_objects])
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_overlays=False;sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=0
            sp.region_3d.view_location=target;sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.region_3d.view_distance=40
bpy.context.view_layer.update()
# Existing model geometry and poses must survive this additive pass.
for name,(matrix,data) in old.items():
    o=bpy.data.objects[name]
    if any(c.name.startswith('Z') for c in o.users_collection):continue
    assert max(abs(o.matrix_world[i][j]-matrix[i][j]) for i in range(4) for j in range(4))<.00001,name
    assert (o.data.name if o.data else None)==data,name
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
scene['remaining_model_kit']='8 m modular road and park cells, park furniture, handheld and supply props, delivery bicycle and pop-up stand. No gameplay code.'
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for filename,collections in [('RoadAndParkKit',[roads,park]),('RemainingProps',[props,delivery]),('WorkshopModels',[c for c in scene.collection.children if c!=studio])]:
    bpy.ops.object.select_all(action='DESELECT')
    for c in collections:
        for o in c.all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/f'{filename}.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(R/'Art/Previews/Workshop_All_Models.png');bpy.ops.render.render(write_still=True)
# Detail renders only change the temporary background session after the saved overview.
def camera(pos,target,scale,w=2100,h=1200):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.resolution_x=w;scene.render.resolution_y=h
for c in scene.collection.children:c.hide_render=c not in [props,delivery,studio]
camera((2,-18,11),(-4,-7.5,1),23);scene.render.filepath=str(R/'Art/Previews/Remaining_Props.png');bpy.ops.render.render(write_still=True)
for c in scene.collection.children:c.hide_render=c not in [roads,park,studio]
camera((26,-37,27),(2,-16,0),38,2300,1400)
for o in studio.objects:
    if o.get('review_only'):o.hide_render=True
fit_camera([o for c in [roads,park] for o in c.all_objects])
scene.render.filepath=str(R/'Art/Previews/Road_And_Park_Kit.png');bpy.ops.render.render(write_still=True)
print('REMAINING_MODELS_COMPLETE',len(assets),'new asset roots; old models preserved')
