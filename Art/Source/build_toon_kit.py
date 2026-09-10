"""Author the selected toon model kit in a separate appendable Blender library."""
import ast
import bpy
import bmesh
import json
import math
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Art/Previews/ToonKit'
OUT.mkdir(parents=True, exist_ok=True)
for filename, names in [
    ('build_art_style_review.py', {'color','material','mesh','box','blob','branch','rounded_points','tub','cottage','tree'}),
    ('build_art_style_round2.py', {'lathe','text_label','palette','stand','waffle_iron','serving_bowl','scooper'})]:
    parsed=ast.parse((ROOT/'Art/Source'/filename).read_text())
    exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),filename,'exec'))

source_scene=bpy.data.scenes['Ice cream truck workshop']
bpy.context.window.scene=source_scene
bpy.context.view_layer.update()
scene=bpy.data.scenes.new('Toon kit - all models')
bpy.context.window.scene=scene
gallery=bpy.data.collections.new('N - Toon tycoon model kit')
gallery.use_fake_user=True
scene.collection.children.link(gallery)
style='Cel'
materials={}
assets=[]
current=root=None
cream,pink,mint,plum,steel=palette()
gold=material('Baked waffle','DDA463')
white=material('Whipped cream','FFF6DF')
flavors=[('Vanilla','FFEAC0'),('Chocolate','815343'),('Strawberry','F39AB6'),('Mint','9BD9BE'),
         ('Cookie cream','E9D5B6'),('Cherry','D97594'),('Coffee','B6917D'),('Mango','FFC566'),
         ('Blueberry','A99AD9'),('Peach','F3B894'),('Pistachio','B9D39A'),('Blue moon','88CBEB')]
toppings=[('Sprinkles','E681A5','dry'),('Chocolate sauce','815343','sauce'),('Cookie crumbs','B6917D','dry'),
          ('Caramel sauce','D99C53','sauce'),('Chopped nuts','C3A471','dry'),('Whipped cream','FFF6DF','cream')]


def start(name, group, footprint=None):
    global current,root
    current=bpy.data.collections.new('Toon / '+name)
    gallery.children.link(current)
    root=bpy.data.objects.new('Toon_'+name.replace(' ','_')+'_ROOT',None)
    current.objects.link(root)
    root.location=(180+(len(assets)%10)*9,-(len(assets)//10)*9,0)
    root['style']='Cel cartoon';root['units']='meters';root['front']='-Y'
    root['asset_type']=name
    if footprint:root['grid_footprint_m']=footprint
    assets.append({'name':name,'group':group,'collection':current,'root':root})


def anchor(name, pos, parent=None):
    o=bpy.data.objects.new(root.name[:-5]+'_'+name,None)
    current.objects.link(o);o.parent=parent or root;o.location=pos
    o.empty_display_type='ARROWS';o.empty_display_size=.05
    return o


def ring(name, pos, radius, thickness, mat):
    profile=[(radius+thickness*math.cos(i*math.tau/12),thickness*math.sin(i*math.tau/12)) for i in range(13)]
    return lathe(name,profile,mat,pos,32)


def bowl(offset=(0,0,0)):
    lathe('Paper bowl',[(0,0),(.052,0),(.058,.008),(.079,.063),(.082,.066),(.083,.072),(.078,.075),(.073,.068),(.051,.009),(0,.009)],pink,offset)
    lathe('Cream band',[(.065,.025),(.0704,.039)],cream,offset)
    lathe('Rolled paper rim',[(.078,.066),(.083,.068),(.083,.073),(.08,.076),(.076,.073),(.076,.069),(.078,.066)],cream,offset)


def scoop_piece(name,h,pos=(0,0,.05),scale=1):
    mat=material(name+' flavor',h)
    o=blob(name+' scoop',pos,(.052*scale,.05*scale,.048*scale),mat,3)
    for v in o.data.vertices:
        v.co*=1+.035*math.sin(v.co.x*240/scale+v.co.y*170/scale)*math.cos(v.co.z*210/scale)
    for i in range(9):
        a=i*math.tau/9
        blob('Ruffled scoop edge',(pos[0]+.042*scale*math.cos(a),pos[1]+.04*scale*math.sin(a),pos[2]-.026*scale),(.012*scale,.011*scale,.009*scale),mat,2)
    return o


def tube(name,coords,radii,mat):
    coords=list(map(Vector,coords));verts=[];faces=[];segments=12
    for i,p in enumerate(coords):
        tangent=(coords[min(i+1,len(coords)-1)]-coords[max(i-1,0)]).normalized()
        side=tangent.cross(Vector((0,0,1))).normalized()
        up=side.cross(tangent).normalized()
        for j in range(segments):
            a=j*math.tau/segments
            verts.append(p+(side*math.cos(a)+up*math.sin(a))*radii[i])
    for i in range(len(coords)-1):
        for j in range(segments):faces.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    faces.extend([tuple(reversed(range(segments))),tuple((len(coords)-1)*segments+j for j in range(segments))])
    return mesh(name,verts,faces,mat)


def cone():
    lathe('Waffle cone',[(0,0),(.007,.012),(.055,.16),(.056,.166),(.051,.167),(.003,.017),(0,.017)],gold,segments=40)
    dark=material('Waffle grooves','BD814B')
    # A raised diagonal lattice follows the conical wall, with no floating crossbars.
    for direction in [-1,1]:
        for j in range(10):
            coords=[]
            for k in range(16):
                z=.015+k*.0096;r=.055*z/.16+.0007;a=j*math.tau/10+direction*z*30
                coords.append((r*math.cos(a),r*math.sin(a),z))
            for a,b in zip(coords,coords[1:]):branch('Baked lattice',a,b,.0008,.0008,dark)
    ring('Cone lip',(0,0,.164),.054,.002,gold)


def package(label,count,mat,dims=(.32,.24,.29)):
    box('Rounded refill package',(0,0,dims[2]/2),dims,mat,.025)
    box('Cream paper label',(0,-dims[1]/2-.002,dims[2]*.5),(dims[0]*.84,.005,dims[2]*.62),cream,.016)
    text_label('Package contents',label.upper(),(0,-dims[1]/2-.006,dims[2]*.59),dims[0]*.086,plum)
    box('Folded seal',(0,0,dims[2]+.012),(dims[0]*.7,.038,.024),cream,.007)
    root['capacity_portions']=count
    anchor('CARRY_GRIP',(0,0,dims[2]*.6))


def container(label,h,kind,capacity):
    mat=material(label+' contents',h)
    if kind=='dry':
        lathe('Shaker jar',[(0,0),(.043,0),(.052,.018),(.052,.145),(.045,.16),(0,.16)],cream,segments=32)
        lathe('Colored lid',[(0,.159),(.054,.159),(.056,.177),(.048,.189),(0,.189)],mat,segments=32)
        for x,y in [(-.022,0),(0,0),(.022,0),(0,.022),(0,-.022)]:
            blob('Shaker opening',(x,y,.19),(.004,.004,.001),plum,2)
        # Front window is a separate content strip with an empty shape key.
        fill=box('Contents window',(0,-.052,.139),(.054,.005,.026),mat,.004)
    else:
        profile=[(0,0),(.034,0),(.044,.015),(.044,.15),(.036,.18),(.018,.19),(0,.19)]
        lathe('Working bottle',profile,mat,segments=32)
        lathe('Cap',[(0,.185),(.022,.185),(.024,.203),(.022,.21),(0,.21)],cream,segments=24)
        branch('Pour nozzle',(0,0,.208),(0,0,.26),.012,.003,cream)
        if kind=='cream':
            box('Whipped cream trigger',(.015,0,.228),(.037,.034,.02),pink,.009)
        fill=None
    box('Bottle label',(0,-.044,.09),(.067,.014,.055),cream,.014)
    short={'Chocolate sauce':'CHOCO','Caramel sauce':'CARAMEL','Whipped cream':'WHIP','Cookie crumbs':'COOKIE','Chopped nuts':'NUTS','Sprinkles':'SPRINKLES','Batter':'BATTER'}[label]
    text_label('Bottle name',short,(0,-.052,.097),.011,plum)
    anchor('GRIP',(0,0,.09));anchor('POUR',(0,0,.19 if kind=='dry' else .26))
    root['capacity_portions']=capacity


def locker(slots):
    global root
    rows=slots//2;h=.20+rows*.30
    box('Locker rear',(0,.232,h/2),(1,.036,h),mint,.024)
    for x in [-.479,0,.479]:box('Locker upright',(x,0,h/2),(.04,.50,h),mint,.014)
    for i in range(rows+1):box('Compartment shelf',(0,0,.14+i*.30),(1,.50,.032),cream,.012)
    box('Rounded locker crown',(0,0,h+.005),(1,.50,.075),mint,.025)
    for x in [-.4,.4]:box('Locker foot',(x,0,.045),(.12,.37,.09),plum,.025)
    owner=root
    for i in range(slots):
        column=i%2;row=i//2;x=-.24+column*.48;z=.155+row*.30
        anchor('STOCK_'+str(i+1),(x,.015,z+.04))
        hinge=anchor('DOOR_'+str(i+1)+'_HINGE',(x-.217,-.242,z+.137))
        hinge['open_axis']='Z';hinge['closed_angle_degrees']=0;hinge['open_angle_degrees']=-105
        root=hinge
        box('Compartment door',(.218,0,0),(.432,.035,.27),pink if row%2==0 else mint,.02)
        box('Inset label',(.12,-.021,.048),(.115,.006,.058),cream,.012)
        branch('Door handle',(.365,-.049,-.025),(.365,-.049,.053),.011,.011,cream)
        for dz in [-.055,-.083]:box('Air vent',(.19,-.02,dz),(.19,.006,.006),plum,.002)
        anchor('HAND_TARGET',(.365,-.055,.01))
        root=owner
    root['inventory_slots']=slots
    anchor('WORKER_ACCESS',(0,-.75,0))


def table(counter=False):
    box('Countertop',(0,0,.96),(2,1,.08),cream,.035)
    if counter:
        box('Counter cabinet',(0,0,.48),(1.92,.92,.88),mint,.055)
        box('Front inset',(0,-.468,.52),(1.68,.018,.62),pink,.025)
        for x in [-.47,.47]:box('Raised cream trim',(x,-.482,.52),(.79,.018,.53),cream,.025)
    else:
        for x in [-.86,.86]:
            for y in [-.36,.36]:
                box('Mint table leg',(x,y,.47),(.10,.10,.90),mint,.018)
                box('Rubber foot',(x,y,.035),(.11,.11,.07),plum,.012)
        box('Lower shelf',(0,0,.20),(1.82,.80,.055),mint,.02)
    root['surface_height_m']=1.0
    anchor('SURFACE_ORIGIN',(-1,-.5,1));anchor('WORKER_ACCESS',(0,-.95,0))


def cooled(wells):
    w=wells*.5
    for y in [-.225,.225]:box('Cooler wall',(0,y,.79),(w-.015,.035,.22),mint,.012)
    for x in [-w/2+.0225,w/2-.0225]:box('Cooler side',(x,0,.79),(.030,.42,.22),mint,.009)
    for x in [-w/2+.06,w/2-.06]:
        for y in [-.18,.18]:box('Removable leg',(x,y,.34),(.042,.042,.68),steel,.008)
    for i in range(wells):
        x=-w/2+.25+i*.5
        for y in [-.209,.209]:box('Well rim',(x,y,.916),(.49,.068,.07),cream,.019)
        for xx in [x-.22,x+.22]:box('Well side',(xx,0,.916),(.05,.36,.07),cream,.016)
        box('Cold well bottom',(x,0,.710),(.385,.316,.025),steel,.012)
        anchor('TUB_'+str(i+1),(x,0,.722))
    root['surface_supported_origin_z']=.68;root['tub_wells']=wells
    anchor('WORKER_ACCESS',(0,-.7,0))


def storage(slots,cold=True):
    rows=slots//2;h=rows*.36+.2
    for x in [-.48,.48]:
        for y in [-.23,.23]:box('Rack upright',(x,y,h/2),(.045,.045,h),mint,.014)
    for j in range(rows+1):box('Rack shelf',(0,0,.14+j*.36),(1,.5,.04),cream,.012)
    box('Rack header',(0,-.255,h+.04),(1,.055,.16),mint,.02)
    text_label('Rack name','COLD STOCK' if cold else 'PICKUP',(0,-.286,h+.04),.075,cream)
    for i in range(slots):
        x=-.24+(i%2)*.48;z=.165+(i//2)*.36
        anchor('PACKAGE_'+str(i+1),(x,0,z))
    root['cargo_slots']=slots
    anchor('WORKER_ACCESS',(0,-.75,0))


def canopy():
    for x in [-1.45,1.45]:
        for y in [-.95,.95]:branch('Canopy upright',(x,y,0),(x,y,2.25),.035,.035,mint)
    for i in range(10):
        x=-1.5+i*.3
        o=mesh('Striped canvas',[(x,-1,2.2),(x+.3,-1,2.2),(x+.3,0,2.65),(x,0,2.65),(x,1,2.2),(x+.3,1,2.2)],[(0,1,2,3),(3,2,5,4)],pink if i%2 else cream,smooth=False)
        o.modifiers.new('Canvas thickness','SOLIDIFY').thickness=.018
        box('Soft valance',(x+.15,-1,2.13),(.3,.03,.18),pink if i%2 else cream,.035)


def kiosk():
    box('Kiosk floor',(0,0,.08),(4,3,.16),cream,.03)
    box('Kiosk back wall',(0,1.45,1.37),(4,.1,2.58),mint,.035)
    for x in [-1.95,1.95]:
        box('Side lower wall',(x,0,.6),(.1,2.9,1.05),mint,.02)
        for y in [-1.4,1.4]:box('Corner post',(x,y,1.40),(.14,.14,2.55),cream,.025)
    box('Serving ledge',(0,-1.42,1.04),(4,.37,.12),cream,.03)
    box('Front low wall',(0,-1.46,.53),(4,.09,.89),mint,.025)
    box('Front shop badge',(0,-1.52,.59),(1.45,.055,.40),pink,.07)
    text_label('Kiosk logo','SCOOP',(0,-1.552,.59),.28,cream)
    for i in range(12):
        x=-2.16+i*.36
        mesh('Kiosk roof stripe',[(x,-1.7,2.65),(x+.36,-1.7,2.65),(x+.36,0,3.13),(x,0,3.13),(x,1.7,2.65),(x+.36,1.7,2.65)],[(0,1,2,3),(3,2,5,4)],pink if i%2 else cream,smooth=False).modifiers.new('Roof thickness','SOLIDIFY').thickness=.04
    # Side entry stays open behind the serving ledge.
    for o in list(current.objects):
        if 'Side lower wall' in o.name and o.location.x>0:o.scale.y=.56;o.location.y=-.63
    anchor('ENTRY',(2.25,.8,.16));anchor('SERVICE',(0,-1.9,1.1))


def supplier():
    box('Warehouse slab',(0,0,.10),(6,4,.20),cream,.05)
    box('Rear wall',(0,1.94,1.75),(6,.12,3.30),mint,.035)
    for x in [-2.94,2.94]:box('Warehouse side',(x,0,1.75),(.12,4,3.30),mint,.025)
    for x,w in [(-2.54,.80),(0,.8),(2.58,.72)]:box('Front pier',(x,-1.94,1.75),(w,.12,3.30),mint,.025)
    box('Front lintel',(0,-1.94,3.0),(6,.15,.8),mint,.025)
    box('Roof',(0,0,3.47),(6.25,4.25,.20),plum,.065)
    box('Supplier sign',(0,-2.035,2.98),(4.8,.12,.56),cream,.07)
    text_label('Supplier name','SCOOP SUPPLY',(0,-2.102,2.98),.36,plum)
    for x in [-1.34,1.37]:
        box('Door frame',(x,-1.99,1.30),(1.69,.10,2.42),cream,.018)
        box('Door opening',(x,-2.052,1.30),(1.50,.022,2.25),plum,.018)
        for j in range(4):box('Raised shutter slat',(x,-2.075,2.19+j*.095),(1.49,.04,.065),steel,.01)
    text_label('Pickup entrance','COLLECT',(1.37,-2.086,1.67),.17,cream)
    text_label('Supplier entrance','ORDER',(-1.34,-2.086,1.67),.17,cream)
    for x in [-2.65,2.65]:
        branch('Safety bollard',(x,-2.5,.1),(x,-2.5,.74),.075,.075,pink)
        ring('Bollard band',(x,-2.5,.5),.076,.007,cream)
    anchor('ORDER_ACCESS',(-1.34,-2.8,0));anchor('PICKUP_ACCESS',(1.37,-2.8,0))


def clone_source(name):
    source=bpy.data.objects[name]
    objects=[source]+list(source.children_recursive)
    mapping={}
    for old in objects:
        new=old.copy()
        if old.data:new.data=old.data.copy()
        new.name=root.name[:-5]+' '+old.name
        current.objects.link(new);mapping[old]=new
        if new.type=='MESH':
            for i,slot in enumerate(old.material_slots):
                m=slot.material
                rgb=m.diffuse_color[:3]
                p=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
                if p:rgb=p.inputs['Base Color'].default_value[:3]
                hexcode=''.join(f'{round(max(0,min(1,(12.92*c if c<=.0031308 else 1.055*c**(1/2.4)-.055)))*255):02X}' for c in rgb)
                new.material_slots[i].link='DATA'
                new.material_slots[i].material=material('Adapted '+m.name,hexcode)
    for old,new in mapping.items():
        if old==source:
            new.parent=root;new.matrix_parent_inverse=Matrix.Identity(4)
            new.location=(0,0,0)
        else:new.parent=mapping[old.parent]
        for mod in new.modifiers:
            if mod.type=='ARMATURE':mod.object=mapping[mod.object]
        for constraint in new.constraints:
            if hasattr(constraint,'target') and constraint.target in mapping:constraint.target=mapping[constraint.target]
    root['adapted_from']=name
    return mapping


# Serving pieces and preparation equipment.
start('Empty bowl','Serving');bowl();anchor('GRIP',(0,0,.03))
start('Bowl stack 12','Serving')
for i in range(12):bowl((0,0,i*.013))
root['stack_count']=12
start('One scoop bowl','Serving');bowl();scoop_piece('Vanilla','FFEAC0',(0,0,.062))
start('Two scoop bowl','Serving');serving_bowl()
start('Empty waffle cone','Serving');cone()
start('One scoop cone','Serving');cone();scoop_piece('Strawberry','F39AB6',(0,0,.186),1.22)
start('Two scoop cone','Serving');cone();scoop_piece('Chocolate','815343',(0,0,.186),1.22);scoop_piece('Mint','9BD9BE',(.009,0,.266),1.1)
start('Flat baked waffle','Serving')
lathe('Waffle disc',[(0,0),(.185,0),(.189,.009),(.18,.013),(0,.013)],gold,segments=48)
for axis in range(2):
    for i in range(-5,6):
        a=i*.029;length=2*math.sqrt(.176**2-a*a)
        box('Baked grid',(a,0,.015) if axis==0 else (0,a,.015),(.005,length,.004) if axis==0 else (length,.005,.004),material('Waffle grooves','BD814B'),.001)
start('Cone holder','Serving',(.25,.25))
box('Stable holder base',(0,0,.015),(.22,.22,.03),mint,.025)
for x in [-.06,.06]:branch('Holder upright',(x,0,.027),(x,0,.18),.009,.009,steel)
ring('Cone support',(0,0,.18),.055,.009,pink);anchor('CONE',(0,0,.04));anchor('GRIP',(0,0,.08))
start('Three cone rack','Serving',(.5,.25))
box('Rack base',(0,0,.015),(.48,.23,.03),mint,.025)
for x in [-.15,0,.15]:
    branch('Rack post',(x,.06,.03),(x,.06,.19),.007,.007,steel)
    ring('Cone rack ring',(x,0,.19),.058,.007,pink);anchor('CONE_'+str(x),(x,0,.04))
start('Bowl prep mat','Serving',(.5,.5))
box('Prep mat',(0,0,.006),(.47,.47,.012),mint,.035);ring('Bowl placement mark',(0,0,.013),.092,.003,cream);anchor('BOWL',(0,0,.015))
start('Tool rest','Serving',(.25,.25))
box('Tool tray',(0,0,.015),(.24,.24,.03),cream,.026)
for x in [-.085,.085]:box('Tray side',(x,0,.034),(.026,.21,.045),mint,.012)
anchor('SCOOPER',(0,0,.032));anchor('BOTTLE',(0,0,.032))
start('Bowl dispenser 30','Serving',(.25,.25))
box('Dispenser foot',(0,0,.025),(.24,.24,.05),mint,.025)
for x in [-.10,.10]:branch('Stack guide',(x,.02,.05),(x,.02,.47),.008,.008,steel)
for i in range(30):bowl((0,0,.05+i*.0105))
root['capacity_bowls']=30;anchor('TAKE',(0,-.12,.15))
start('Basic scooper','Serving');scooper()
for o in current.objects:
    if o.type=='MESH' and ('grip' in o.name.lower() or 'pad' in o.name.lower()):o.data.materials[0]=cream
root['strokes_per_portion']=3;anchor('GRIP',(0,-.065,.025))
start('One swipe scooper','Serving');scooper();root['strokes_per_portion']=1
ring('Upgrade collar',(0,.025,.024),.013,.003,gold).rotation_euler.x=math.pi/2
anchor('GRIP',(0,-.065,.025))
start('Waffle iron','Serving',(.5,.75));waffle_iron();anchor('POUR',(0,0,.17));anchor('WORKER_ACCESS',(0,-.7,0))

# The twelve tub surfaces have matching empty shape keys and independent shells.
for name,h in flavors:
    start(name+' tub','Flavors');tub()
    fill=next(o for o in current.objects if 'Ice cream fill' in o.name)
    fill.data.materials[0]=material(name+' flavor',h)
    for o in list(current.objects):
        if 'Strawberry piece' in o.name or 'Badge mark' in o.name:bpy.data.objects.remove(o,do_unlink=True)
        elif 'Flavor badge' in o.name:o.data.materials[0]=material(name+' flavor',h)
    fill.shape_key_add(name='Full')
    empty=fill.shape_key_add(name='Empty')
    for v in empty.data:v.co.z=.022;v.co.x*=.86;v.co.y*=.84
    empty.value=0.0
    fill['capacity_portions']=24;fill['empty_shape_key']='Empty';fill['full_value']=0.;fill['empty_value']=1.
    text_label('Flavor name',name.upper(),(0,-.161,.123),.017,plum)
    root['capacity_portions']=24;anchor('GRIP',(0,0,.12));anchor('SCOOP',(0,0,.215))
for name,h in flavors:
    start(name+' scoop','Flavors');scoop_piece(name,h)
start('Tub transport lid','Supplies')
box('Tub lid',(0,0,.012),(.40,.33,.025),mint,.04);box('Lid inset',(0,0,.027),(.32,.25,.012),cream,.033)
anchor('GRIP',(0,0,.03))
for name,h,kind in toppings:
    start(name+' dispenser','Toppings');container(name,h,kind,15)
    start(name+' refill','Toppings');package(name,30,material(name+' contents',h))
    start(name+' serving layer','Toppings')
    if kind=='dry':
        for i in range(28):
            a=i*2.399;r=.046*math.sqrt((i+.5)/28);z=.038*math.sqrt(max(0,1-(r/.052)**2))
            mat=[pink,mint,gold,white][i%4] if name=='Sprinkles' else material(name+' contents',h)
            o=box('Sprinkle' if name=='Sprinkles' else 'Crumb',(r*math.cos(a),r*math.sin(a),z),(.009,.0025,.0025) if name=='Sprinkles' else (.005,.004,.004),mat,.001)
            o.rotation_euler.z=a
    elif kind=='sauce':
        for j in range(-2,3):
            x=j*.016;coords=[]
            for k in range(14):
                y=-.038+k*.076/13;xx=x+.004*math.sin(k*.9);z=.042*math.sqrt(max(.05,1-(xx/.058)**2-(y/.058)**2))
                coords.append((xx,y,z))
            tube('Sauce drizzle',coords,[.0024]*len(coords),material(name+' contents',h))
    else:
        coords=[]
        for i in range(90):
            t=i/89;a=t*math.tau*3.2;r=.032*(1-t)
            coords.append((r*math.cos(a),r*math.sin(a),.018+.075*t))
        tube('Cream swirl',coords,[.010*(1-i/96) for i in range(len(coords))],white)
start('Batter bottle','Supplies');container('Batter','F0D596','sauce',10)
start('Batter refill carton','Supplies');package('Batter',20,gold)
start('Bowl supply pack','Supplies');package('Bowls + spoons',30,pink,(.34,.28,.38));root['capacity_bowls']=30

# Furniture obeys the planned floor and tabletop dimensions.
for slots in [4,8,12]:start(str(slots)+' slot locker','Furniture',(1,.5));locker(slots)
start('Prep table','Furniture',(2,1));table()
start('Service counter','Furniture',(2,1));table(True)
for wells in [1,2]:start(str(wells)+' well cooled module','Furniture',(.5*wells,.5));cooled(wells)
for slots in [4,8]:start(str(slots)+' slot cold rack','Furniture',(1,.5));storage(slots)
start('Floor expansion tile','Buildings',(1,1))
box('Floor tile',(0,0,.045),(1,1,.09),cream,.018)
for axis in range(2):box('Tile seam',(0,0,.091),(.005,.95,.002) if axis==0 else (.95,.005,.002),pink,.001)
start('Pop up canopy','Buildings',(3,2));canopy()
start('Pop up stand','Buildings',(2.5,1.5));stand();anchor('SERVICE',(0,-.9,1));anchor('WORKER_ACCESS',(0,.9,0))
start('Expanded kiosk shell','Buildings',(4,3));kiosk()
start('Open closed sign','Furniture',(.5,.5))
for y in [-.18,.18]:
    o=box('A frame board',(0,y,.40),(.43,.04,.76),mint,.025);o.rotation_euler.x=math.radians(-15 if y<0 else 15)
box('Sign face',(0,-.25,.43),(.36,.022,.44),cream,.022)
text_label('Open face','OPEN',(0,-.268,.48),.085,plum)
text_label('Open subline','COME SCOOP',(0,-.268,.36),.032,plum)
text_label('Closed reverse','CLOSED',(0,.25,.45),.07,cream,rotation=(math.pi/2,0,math.pi))
start('Supplier storefront','Buildings',(6,4));supplier()
start('Supplier terminal','Furniture',(.5,.5))
box('Terminal foot',(0,0,.035),(.45,.43,.07),plum,.03)
box('Terminal pedestal',(0,.035,.52),(.18,.18,.98),mint,.032)
box('Terminal housing',(0,0,1.10),(.46,.17,.34),pink,.035)
box('Screen',(0,-.093,1.11),(.38,.02,.255),plum,.02)
text_label('Screen title','SUPPLIES',(0,-.106,1.17),.044,cream)
for i in range(3):box('Screen category',(-.115+i*.115,-.107,1.065),(.082,.006,.077),[mint,cream,pink][i],.009)
anchor('HAND_TARGET',(0,-.11,1.10));anchor('PLAYER_ACCESS',(0,-.65,0))
start('Pickup shelf','Furniture',(1,.5));storage(8,False)
start('Loading pad','Buildings',(2,2))
box('Loading mat',(0,0,.009),(2,2,.018),plum,.03)
for x in [-.94,.94]:box('Loading border',(x,0,.02),(.05,1.95,.005),gold,.002)
for y in [-.94,.94]:box('Loading border',(0,y,.02),(1.95,.05,.005),gold,.002)
text_label('Loading label','PICKUP',(0,0,.025),.23,cream,rotation=(0,0,0));anchor('DELIVERY',(0,0,.025))

# Existing vehicle proportions, hinges and rigs survive as separate toon copies.
for slots in [4,8]:
    start('Delivery bike '+str(slots)+' cargo','Vehicles');clone_source('Delivery_Bicycle_ROOT')
    # Replace the old cooler with open, visible package sockets.
    for o in list(current.objects):
        if 'Cooler' in o.name and o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
    w=.82 if slots==4 else 1.12;d=.68
    box('Cargo tray',(0,.64,.895),(w,d,.055),cream,.018)
    for x in [-w/2,w/2]:box('Cargo side',(x,.64,1.03),(.035,d,.26),mint,.017)
    for y in [.30,.98]:box('Cargo end',(0,y,1.03),(w,.035,.26),mint,.017)
    cols=2
    if slots==8:
        box('Upper cargo tray',(0,.64,1.225),(w,d,.045),cream,.018)
        for x in [-w/2,w/2]:
            for y in [.30,.98]:box('Upper tray support',(x,y,1.12),(.033,.033,.44),mint,.01)
        for x in [-w/2,w/2]:box('Upper cargo side',(x,.64,1.37),(.035,d,.26),mint,.017)
        for y in [.30,.98]:box('Upper cargo end',(0,y,1.37),(w,.035,.26),mint,.017)
    for i in range(slots):
        x=-w/2+w*(i%cols+.5)/cols;y=.30+d*((i%4)//cols+.5)/2;z=.924+(i//4)*.325
        anchor('CARGO_'+str(i+1),(x,y,z))
        box('Slot pad',(x,y,z+.003),(w/cols-.025,d/2-.025,.008),pink,.008)
    root['cargo_slots']=slots
start('Delivery cooler','Vehicles');clone_source('Delivery_Cooler_ROOT')
start('Ice cream truck','Vehicles');clone_source('IceCreamTruck_ROOT')
for i,(label,shirt,apron,hat) in enumerate([('Rookie','FFF0D4','79BCAA','E681A5'),('Experienced','FFE4B8','9884BC','79BCAA'),('Expert','E5DBF2','51415C','E0B86F')]):
    start(label+' employee','Staff')
    mapping=clone_source('Crew_ROOT')
    for o in mapping.values():
        if o.type=='MESH':
            for slot in o.material_slots:
                name=slot.material.name.lower()
                for term,h in [('clothes',shirt),('apron',apron),('hair',hat)]:
                    if term in name:slot.material=material(label+' '+term,h)
    rig=next(o for o in mapping.values() if o.type=='ARMATURE')
    root['rig_bones']=len(rig.data.bones)
    # Staff rank pin follows the body bone, ready for later animation.
    pin=blob('Apron badge',(0,-.324,.79),(.047,.013,.047),cream,3)
    bpy.context.view_layer.update();world=pin.matrix_world.copy()
    pin.parent=rig;pin.parent_type='BONE';pin.parent_bone='Body'
    bpy.context.view_layer.update();pin.matrix_world=world
start('First person hands','Staff');clone_source('FirstPersonHands_ROOT')
for variant in [1,2]:
    start('Neighborhood cottage '+str(variant),'Buildings');cottage()
    if variant==2:
        for o in current.objects:
            if o.type=='MESH':
                for slot in o.material_slots:
                    if 'Peach plaster' in slot.material.name:slot.material=material('Lilac plaster','B3A2D1')
                    elif 'Berry roof' in slot.material.name:slot.material=material('Mint cottage roof','79BCAA')
start('Round maple','Buildings');tree()

# Keep a complete checkpoint before rendering or building review scenes.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Working.blend'),compress=True)
# Add thin colored silhouettes to static closed parts only.
bpy.context.view_layer.update()
depsgraph=bpy.context.evaluated_depsgraph_get()
ink=material('Toon kit outline','493A57');ink.use_backface_culling=True;ink.use_backface_culling_shadow=True
for entry in assets:
    col=entry['collection']
    for obj in list(col.objects):
        if obj.type!='MESH' or obj.data.shape_keys or any(m.type=='ARMATURE' for m in obj.modifiers):continue
        if len(obj.data.polygons)<5 and not obj.modifiers:continue
        data=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        thickness=min(.004,max(.00022,max(obj.dimensions)*.0018))
        for v in data.vertices:v.co+=v.normal*thickness
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        data.materials.clear();data.materials.append(ink)
        for face in data.polygons:face.material_index=0
        shell=bpy.data.objects.new(obj.name+' outline',data);col.objects.link(shell)
        shell.parent=obj.parent;shell.parent_type=obj.parent_type;shell.parent_bone=obj.parent_bone
        shell.matrix_parent_inverse=obj.matrix_parent_inverse.copy();shell.matrix_basis=obj.matrix_basis.copy()
        shell['toon_outline']=True

# Source collection positions stay at modeling scale. Display copies are normalized for review.
display=bpy.data.collections.new('Toon kit display copies')
scene.collection.children.link(display)
bpy.context.view_layer.update()
for i,entry in enumerate(assets):
    col,r=entry['collection'],entry['root']
    points=[obj.matrix_world@Vector(c)-r.location for obj in col.objects if obj.type in {'MESH','FONT'} for c in obj.bound_box]
    low=Vector(tuple(min(p[a] for p in points) for a in range(3)))
    high=Vector(tuple(max(p[a] for p in points) for a in range(3)))
    size=high-low;scale=2.1/max(size)
    col.instance_offset=r.location+Vector((0,0,low.z))
    o=bpy.data.objects.new('Display / '+entry['name'],None);display.objects.link(o)
    o.instance_type='COLLECTION';o.instance_collection=col;o.scale=(scale,)*3
    o.location=((i%10)*3.4,-(i//10)*3.5,0)
    entry.update(instance=o,scale=scale,bounds=[list(low),list(high)])
scene.collection.children.unlink(gallery)
stage=bpy.data.collections.new('Toon kit studio');scene.collection.children.link(stage)
current=stage;root=bpy.data.objects.new('Toon kit studio root',None);stage.objects.link(root)
style='Studio'
box('Studio floor',(15,-15,-.065),(100,100,.12),material('Toon review floor','EAE4D9'),0)
scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=64
scene.render.resolution_x=720;scene.render.resolution_y=600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
scene.world=bpy.data.worlds.new('Toon kit studio world')
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.32,.37,.48,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
data=bpy.data.cameras.new('Toon kit camera');cam=bpy.data.objects.new(data.name,data);stage.objects.link(cam)
scene.camera=cam;cam.data.type='ORTHO';cam.data.clip_start=.001
lights=[]
for name,offset,energy in [('Key',(-5,-7,10),1400),('Fill',(6,-3,6),650)]:
    data=bpy.data.lights.new('Toon studio '+name,'AREA');data.energy=energy;data.shape='DISK';data.size=5
    o=bpy.data.objects.new(data.name,data);stage.objects.link(o);lights.append((o,Vector(offset)))


def frame_asset(entry):
    inst=entry['instance'];col=entry['collection'];scale=entry['scale']
    points=[inst.location+(o.matrix_world@Vector(c)-col.instance_offset)*scale for o in col.objects if o.type in {'MESH','FONT'} for c in o.bound_box]
    target=Vector(tuple((min(p[a] for p in points)+max(p[a] for p in points))/2 for a in range(3)))
    cam.location=target+Vector((6,-10,7));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    rotation=cam.rotation_euler.to_matrix().transposed();projected=[rotation@(p-target) for p in points]
    cam.data.ortho_scale=max(max(p.x for p in projected)-min(p.x for p in projected),(max(p.y for p in projected)-min(p.y for p in projected))*1.2)*1.16
    for light,offset in lights:light.location=target+offset;light.rotation_euler=(target-light.location).to_track_quat('-Z','Y').to_euler()


report=[]
for i,entry in enumerate(assets):
    for j,e in enumerate(assets):e['instance'].hide_render=j!=i
    bpy.context.view_layer.update();frame_asset(entry)
    filename=f'{i+1:02d}_{entry["name"].replace(" ","_")}.png'
    scene.render.filepath=str(OUT/filename);bpy.ops.render.render(write_still=True)
    report.append({'name':entry['name'],'group':entry['group'],'root':entry['root'].name,'collection':entry['collection'].name,'display_scale':entry['scale'],'bounds_m':entry['bounds'],'preview':filename})
    print('TOON_ASSET_RENDERED',i+1,entry['name'],flush=True)
for entry in assets:entry['instance'].hide_render=False
current=display;root=bpy.data.objects.new('Toon gallery labels',None);display.objects.link(root)
labelmat=material('Gallery text','51415C')
for entry in assets:
    p=entry['instance'].location
    text_label('Label / '+entry['name'],entry['name'].upper(),(p.x,p.y-1.20,.015),.12,labelmat,rotation=(0,0,0))
target=Vector((15.3,-14,0));cam.location=target+Vector((0,-32,43));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=39
scene['note']='Selected cel cartoon style. Display copies enlarged independently; source models in collection N retain meter scale. Modeling only, no gameplay integration.'
# Save a compact first-page scene so opening the kit starts with readable shop equipment.
review=bpy.data.scenes.new('Toon kit - start here')
for col in [stage,display]:review.collection.children.link(col)
review.camera=cam;review.world=scene.world
review.render.engine='BLENDER_EEVEE';review.view_settings.view_transform='Standard';review.view_settings.look='None'
# The overview scene is retained; a dedicated camera frames the first sixteen serving models.
cd=cam.data.copy();cc=bpy.data.objects.new('Toon serving camera',cd);review.collection.objects.link(cc)
review.camera=cc;cc.location=(11.5,-17,22);cc.rotation_euler=(Vector((11.5,-2.5,.3))-cc.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=29
bpy.context.preferences.filepaths.save_version=0
for saved_scene in [scene,review]:
    bpy.context.window.scene=saved_scene
    bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonKit_Additions.blend'),compress=True)
(OUT/'inventory.json').write_text(json.dumps(report,indent=2))
print('TOON_KIT_COMPLETE',len(assets),flush=True)
