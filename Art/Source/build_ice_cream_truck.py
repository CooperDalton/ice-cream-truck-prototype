"""Model the truck and fit the existing preparation assets inside it."""
from pathlib import Path
ROOT=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
# Reuse the modeling helpers and palette from the approved preparation set.
helper=(ROOT/'Art/Source/build_ice_cream_models.py').read_text().split('# The cabinet leaves an actual cavity')[0]
exec(compile(helper,'prep_model_helpers','exec'))
OUT=ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruck.blend'
blue=mat('Windows • blue tint','A2D9E0',.18,.05)
p=blue.node_tree.nodes.get('Principled BSDF');p.inputs['Transmission Weight'].default_value=.65;p.inputs['IOR'].default_value=1.45
inside=mat('Interior • light sage','D8E7D6',.65)
floormat=mat('Floor • warm graphite','67616E',.8)
amber=mat('Lights • amber','FFBF53',.35)
headlight=mat('Lights • warm white','FFF3D0',.25)
cloth=mat('Seats • muted plum','655870',.8)
chrome=mat('Trim • ivory metal','D9DFD7',.3,.4)

def bar(name,a,b,width,material,parent=None):
    mid=(Vector(a)+Vector(b))/2
    o=cyl(name,mid,width,(Vector(a)-Vector(b)).length,material,vertices=16,parent=parent,bevel=width*.3)
    o.rotation_euler=(Vector(b)-Vector(a)).to_track_quat('Z','Y').to_euler()
    return o

def wheel_cut(o,x,y):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=.565,depth=.7,location=(x,y,.5),rotation=(pi/2,0,0))
    cutter=bpy.context.object
    bpy.context.view_layer.objects.active=o
    for modifier in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    b=o.modifiers.new('Wheel opening','BOOLEAN');b.operation='DIFFERENCE';b.object=cutter
    bpy.ops.object.modifier_apply(modifier=b.name)
    bpy.data.objects.remove(cutter,do_unlink=True)
    finish(o,.008)

def axis_y_cyl(name,loc,r,depth,material,parent=None,vertices=32):
    o=cyl(name,loc,r,depth,material,vertices,parent,bevel=.008);o.rotation_euler.x=pi/2
    return o

collection('10 • Truck chassis')
truck=empty('IceCreamTruck_ROOT')
truck['dimensions_m']='6.45 long × 2.90 wide × 3.90 tall including roof sign'
truck['forward_axis']='-X in Blender, +Y is driver side'
truck['floor_height_m']=.55
chassis=empty('Chassis_ROOT',parent=truck)
cube('Floor deck',(0,0,.51),(6.24,2.68,.10),floormat,.025,chassis)
for y in [-.80,.80]:cube('Chassis rail',(0,y,.34),(5.8,.13,.20),plum,.025,chassis)
for x in [-2.10,1.68]:bar('Axle',(x,-1.35,.49),(x,1.35,.49),.055,plum,chassis)
for y in [-1.10,1.10]:
    for x in [-2.10,1.68]:cube('Interior wheel box',(x,y,.74),(1.09,.43,.39),inside,.08,chassis)

collection('11 • Body shell')
body=empty('BodyShell_ROOT',parent=truck)
# Lower side panels have cut wheel openings, not tires buried in solid bodywork.
for sign in [-1,1]:
    y=sign*1.36
    lower=cube('Cargo lower side',(1.25,y,1.08),(3.82,.12,1.10),cream,.04,body)
    wheel_cut(lower,1.68,y)
    stripe=cube('Pink belt stripe',(1.25,y+sign*.069,.91),(3.82,.014,.32),pink,.012,body)
    wheel_cut(stripe,1.68,y)
    trim=cube('Lower mint trim',(1.25,y+sign*.066,.58),(3.82,.019,.10),mint,.015,body)
    wheel_cut(trim,1.68,y)
    # Rear pillar and cab junction frame the side opening.
    cube('Rear corner pillar',(2.92,y,2.21),(.46,.12,1.33),cream,.045,body)
    cube('Cab junction pillar',(-.54,y,2.21),(.30,.12,1.33),cream,.03,body)
    cube('Upper body rail',(1.15,y,2.72),(3.08,.12,.34),cream,.025,body)
    cube('Pink header inset',(1.05,y+sign*.069,2.72),(2.52,.016,.23),pink,.02,body)
    if sign==1:
        cube('Driver side solid wall',(1.13,y,2.11),(3.02,.12,1.10),cream,.025,body)
    for x in [-2.1,1.68]:
        pts=[(x+.586*cos(a*pi/32),y+sign*.082,.5+.586*sin(a*pi/32)) for a in range(33)]
        path('Wheel arch trim',pts,.027,chrome,body)
    for x in [-.25,2.91]:
        sphere('Side reflector',(x,y+sign*.075,.70),(.068,.012,.026),amber if x<0 else red,parent=body)
# Rear wall leaves a full-height entry opening.
for y in [-.975,.975]:cube('Rear wall side',(3.12,y,1.71),(.12,.81,2.32),cream,.035,body)
cube('Rear door header',(3.12,0,2.78),(.12,1.15,.19),cream,.018,body)
cube('Rear bumper',(3.24,0,.43),(.20,2.78,.17),plum,.045,body)
for y in [-1.18,1.18]:
    cube('Tail light bezel',(3.191,y,1.13),(.025,.17,.40),plum,.025,body)
    cube('Brake light',(3.211,y,1.22),(.025,.125,.15),red,.02,body)
    cube('Turn light',(3.211,y,1.035),(.025,.125,.11),amber,.015,body)
cube('Rear plate',(3.258,0,.48),(.016,.47,.12),cream,.014,body)
label('Rear plate lettering','SCOOPS',(3.272,0,.48),.065,plum,body,rot=(pi/2,0,pi/2))
# Step-van nose and slanted windshield.
cube('Rounded nose',(-2.825,0,1.16),(.67,2.70,1.23),cream,.15,body)
cube('Pink nose stripe',(-3.165,0,.90),(.02,2.48,.28),pink,.018,body)
cube('Front bumper',(-3.235,0,.48),(.21,2.84,.20),plum,.06,body)
cube('Front grille surround',(-3.177,0,1.17),(.048,1.04,.38),plum,.09,body)
for z in [1.07,1.16,1.25]:cube('Grille slat',(-3.207,0,z),(.029,.84,.025),chrome,.011,body)
for y in [-.96,.96]:
    lamp=cyl('Headlight bezel',(-3.149,y,1.31),.185,.056,mint,parent=body);lamp.rotation_euler.y=pi/2
    lamp=cyl('Headlight lens',(-3.190,y,1.31),.142,.036,headlight,parent=body);lamp.rotation_euler.y=pi/2
    cube('Front turn indicator',(-3.161,y,.99),(.025,.20,.068),amber,.023,body)
# Two windshield panes bordered with thick readable rubber and cream pillars.
for sign in [-1,1]:
    ya,yb=sorted([sign*.025,sign*1.25])
    verts=[(-3.04,ya,1.72),(-3.04,yb,1.72),(-2.66,yb,2.72),(-2.66,ya,2.72)]
    mesh('Windshield glass',verts,[(0,1,2,3)],blue,body)
    path('Windshield seal',verts,.037,plum,body,True)
for sign in [-1,1]:
    pts=[(-3.01,sign*1.32,1.71),(-2.65,sign*1.366,1.71),(-2.59,sign*1.366,2.71)]
    mesh('Cab quarter glass',pts,[(0,1,2)],blue,body)
for y in [-1.31,1.31]:bar('Windshield outer pillar',(-3.07,y,1.67),(-2.65,y,2.78),.063,cream,body)
bar('Windshield center pillar',(-3.05,0,1.70),(-2.65,0,2.77),.027,cream,body)
cube('Windshield brow',(-2.66,0,2.785),(.21,2.75,.13),cream,.05,body)
# Front roof fills the slanted cab silhouette; the cargo roof remains removable.
verts=[(-2.72,-1.39,2.76),(-2.72,1.39,2.76),(-.66,1.39,2.76),(-.66,-1.39,2.76),(-2.61,-1.39,2.96),(-2.61,1.39,2.96),(-.66,1.39,2.96),(-.66,-1.39,2.96)]
o=mesh('Cab roof',verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],cream,body);finish(o,.035)
for y in [-.98,0,.98]:sphere('Cab roof marker',(-2.726,y,2.82),(.03,.067,.037),amber,parent=body)

collection('12 • Cab doors and mirrors')
doors=[]
for sign,side in [(-1,'Passenger'),(1,'Driver')]:
    # Build at truck coordinates, then move the root to the forward hinge.
    door=empty(side+'Door_HINGE',parent=truck);doors.append(door)
    lower=cube(side+' lower door',(-1.655,sign*1.36,1.10),(1.88,.105,1.10),cream,.025,door)
    wheel_cut(lower,-2.1,sign*1.36)
    stripe=cube('Door belt stripe',(-1.655,sign*1.42,.91),(1.88,.014,.32),pink,.008,door);wheel_cut(stripe,-2.1,sign*1.42)
    # Side glazing follows the windshield slope at its front edge.
    pts=[(-2.64,sign*1.366,1.70),(-.75,sign*1.366,1.70),(-.75,sign*1.366,2.70),(-2.57,sign*1.366,2.70)]
    mesh(side+' door glass',pts,[(0,1,2,3)],blue,door)
    path('Door window frame',pts,.038,cream,door,True)
    path('Door window seal',[(x,sign*1.394,z) for x,y,z in pts],.016,plum,door,True)
    cube('Exterior door handle',(-.91,sign*1.435,1.50),(.20,.048,.045),plum,.017,door)
    cube('Interior door handle',(-.91,sign*1.29,1.48),(.18,.037,.037),plum,.012,door)
    hinge_pos=Vector((-2.60,sign*1.36,.56))
    for child in list(door.children):child.location-=hinge_pos
    door.location=hinge_pos;door['open_rotation_z_degrees']=sign*68
    # Mirrors mount on the body and remain separate from the doors.
    bar(side+' mirror stalk',(-2.59,sign*1.39,1.82),(-2.63,sign*1.70,1.95),.022,plum,truck)
    cube(side+' mirror housing',(-2.64,sign*1.77,2.04),(.075,.23,.32),plum,.035,truck)
    cube(side+' mirror face',(-2.593,sign*1.77,2.04),(.008,.17,.25),silver,.015,truck)
    cube(side+' cab step',(-1.1,sign*1.45,.40),(.64,.25,.10),silver,.024,truck)

collection('13 • Serving hatch')
hatch=empty('ServingHatch_HINGE',(.99,-1.439,2.55),truck)
hatch['closed_rotation_x_degrees']=0;hatch['open_rotation_x_degrees']=-98
cube('Serving hatch panel',(0,0,-.465),(2.84,.065,.93),pink,.025,hatch)
cube('Awning cream underside',(0,.038,-.465),(2.75,.014,.83),cream,.015,hatch)
for i in range(7):cube('Awning cream stripe',(-1.20+i*.40,-.038,-.465),(.18,.014,.88),cream,.006,hatch)
bar('Hatch hinge barrel',(-1.42,0,0),(1.42,0,0),.034,silver,hatch)
hatch.rotation_euler.x=math.radians(-98)
ledge=empty('ServiceLedge_ROOT',parent=truck)
cube('Outside serving ledge',(.99,-1.51,1.55),(2.91,.43,.075),cream,.029,ledge)
cube('Serving ledge pink trim',(.99,-1.731,1.55),(2.82,.018,.040),pink,.008,ledge)
# Branding on the service header and the opposite side.
label('Service side wordmark','SCOOP SHOP',(1.05,-1.441,2.73),.188,white,body)
label('Driver side wordmark','SCOOP SHOP',(1.10,1.442,2.20),.27,pink,body,rot=(pi/2,0,pi))
label('Driver side subline','ICE CREAM',(1.10,1.443,1.92),.115,plum,body,rot=(pi/2,0,pi))
collection('14 • Rear entry door')
rear=empty('RearEntryDoor_HINGE',(3.19,-.56,.55),truck)
rear['open_rotation_z_degrees']=-95
# Geometry is local to the rear left hinge; the clear doorway is 1.12 meters wide.
cube('Rear door lower panel',(0,.56,.72),(.065,1.09,1.44),mint,.027,rear)
cube('Rear door upper rail',(0,.56,2.08),(.065,1.09,.10),cream,.018,rear)
for y in [.04,1.08]:cube('Rear door side rail',(0,y,1.77),(.065,.085,.58),cream,.012,rear)
cube('Rear door glass',(0,.56,1.77),(.026,.94,.55),blue,.01,rear)
cube('Rear door handle',(.058,.98,1.02),(.055,.035,.18),plum,.012,rear)
for z,x,w in [(.20,3.45,1.24),(.38,3.27,1.18)]:
    cube('Rear entry step',(x,0,z),(.38,w,.08),silver,.025,truck)
    for y in [-.42,-.21,0,.21,.42]:cube('Step grip',(x,y,z+.046),(.27,.014,.007),plum,.002,truck)

collection('15 • Four wheels')
for x,axle_name in [(-2.1,'Front'),(1.68,'Rear')]:
    for sign,side in [(-1,'Right'),(1,'Left')]:
        steer=empty(f'{axle_name}{side}_Steering',(x,sign*1.36,.50),truck)
        wheel=empty(f'{axle_name}{side}_Wheel_AXLE',parent=steer)
        wheel['spin_axis']='local Y';steer['steering_axis']='local Z'
        profiles=[(.285,-.15),(.405,-.15),(.475,-.10),(.492,-.055),(.492,.055),(.475,.10),(.405,.15),(.285,.15)]
        verts=[];n=40
        for radius,y in profiles:
            for k in range(n):a=2*pi*k/n;verts.append((radius*cos(a),y,radius*sin(a)))
        faces=[]
        for j in range(len(profiles)):
            for k in range(n):a=j*n+k;b=j*n+(k+1)%n;c=((j+1)%len(profiles))*n;faces.append((a,b,c+(k+1)%n,c+k))
        o=mesh('Rounded tire',verts,faces,plum,wheel)
        for p in o.data.polygons:p.use_smooth=True
        axis_y_cyl('Wheel steel rim',(0,sign*.12,0),.293,.11,silver,wheel)
        axis_y_cyl('Mint hubcap',(0,sign*.19,0),.219,.049,mint,wheel)
        axis_y_cyl('Cream center cap',(0,sign*.221,0),.092,.025,cream,wheel)
        for k in range(5):
            a=2*pi*k/5
            axis_y_cyl('Wheel lug',(sin(a)*.146,sign*.225,cos(a)*.146),.022,.025,chrome,wheel,12)
        for k in range(30):
            a=2*pi*k/30
            # Subtle tread blocks retain the broad tire silhouette.
            o=cube('Tire tread',(.491*cos(a),0,.491*sin(a)),(.019,.11,.026),plum,.004,wheel)
            o.rotation_euler.y=-a

collection('16 • Driver cabin')
cabin=empty('Cabin_ROOT',parent=truck)
cube('Dashboard',(-2.59,0,1.58),(.60,2.54,.23),plum,.07,cabin)
cube('Dashboard top',(-2.59,0,1.707),(.58,2.46,.04),mint,.017,cabin)
for y in [-.80,.80]:
    cube('Seat pedestal',(-1.48,y,.77),(.37,.39,.43),silver,.03,cabin)
    cube('Seat cushion',(-1.48,y,1.025),(.61,.59,.17),cloth,.09,cabin)
    seat=cube('Seat back',(-1.17,y,1.39),(.15,.60,.68),cloth,.075,cabin);seat.rotation_euler.y=math.radians(-8)
    cube('Seat headrest',(-1.10,y,1.81),(.15,.40,.24),cloth,.067,cabin)
    cube('Seat mint insert',(-1.25,y,1.4),(.02,.43,.42),mint,.025,cabin)
steering=empty('SteeringWheel_ROOT',(-2.11,.80,1.60),cabin)
steering.rotation_euler.y=math.radians(63)
ring('Steering rim',(0,0,0),.229,.024,plum,steering)
cyl('Steering hub',(0,0,-.008),.073,.055,mint,parent=steering)
for a in [pi/2,7*pi/6,11*pi/6]:bar('Steering spoke',(0,0,-.01),(.207*cos(a),.207*sin(a),0),.016,silver,steering)
bar('Steering column',(-2.11,.80,1.58),(-2.45,.80,1.44),.04,plum,cabin)
# Dash instruments face the driver, toward positive X.
for y,r in [(.69,.092),(.92,.065)]:
    g=cyl('Gauge bezel',(-2.279,y,1.62),r,.018,silver,parent=cabin);g.rotation_euler.y=pi/2
    g=cyl('Gauge face',(-2.266,y,1.62),r*.83,.009,plum,parent=cabin);g.rotation_euler.y=pi/2
    bar('Gauge needle',(-2.258,y,1.62),(-2.258,y-.028,1.65),.003,cream,cabin)
for y in [-.42,-.18,.06]:cube('Dashboard switch',(-2.266,y,1.60),(.024,.087,.041),pink if y<0 else mint,.012,cabin)
bar('Gear lever',(-1.98,.36,.79),(-1.90,.36,1.26),.018,silver,cabin)
sphere('Gear knob',(-1.90,.36,1.28),(.05,.044,.055),plum,parent=cabin)
for y in [.69,.91]:cube('Pedal',(-2.29,y,.69),(.18,.11,.035),plum,.012,cabin)
empty('DriverSeat_SOCKET',(-1.48,.80,1.16),cabin)
empty('DriverView_SOCKET',(-1.44,.80,1.98),cabin)

# Append the saved preparation set without changing its source file.
with bpy.data.libraries.load(str(ROOT/'Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend'),link=False) as (src,dst):
    dst.collections=[name for name in src.collections if name[:2] in ['01','02','03','04','05','06','07','08','09']]
collection('17 • Interior preparation equipment')
equipment_collection=current
equipment=empty('InteriorEquipment_ROOT',(.95,-.79,.56),truck);equipment.rotation_euler.z=pi
for loaded in dst.collections:
    equipment_collection.children.link(loaded)
    for o in loaded.objects:
        if o.parent is None:o.parent=equipment
        if o.name.startswith('Raw batter portion'):
            o.hide_render=True;o.hide_set(True)

collection('18 • Removable roof and roof sign')
roof=empty('Roof_ROOT • hide for interior view',parent=truck)
cube('Cargo roof',(1.22,0,2.94),(3.94,2.84,.17),cream,.07,roof)
for y in [-1.36,1.36]:cube('Roof pink seam',(1.2,y,2.858),(3.84,.06,.037),pink,.013,roof)
for x in [.10,2.0]:
    cube('Ceiling light frame',(x,.45,2.84),(.67,.19,.04),mint,.024,roof)
    cube('Ceiling light diffuser',(x,.45,2.816),(.58,.13,.009),headlight,.018,roof)
# Roof vents and speaker pods are simple separate meshes.
for x in [2.55,-.16]:
    cube('Roof vent',(x,.67,3.065),(.49,.42,.10),mint,.035,roof)
    for j in range(4):cube('Vent slot',(x-.15+j*.1,.67,3.12),(.032,.29,.006),plum,.008,roof)
for y in [-1.0,1.0]:
    cube('Speaker pod',(-.42,y,3.12),(.42,.30,.20),cream,.065,roof)
    cube('Speaker grille',(-.42,y+(-.154 if y<0 else .154),3.12),(.29,.013,.105),plum,.031,roof)
# Reuse the actual cone and scoop as the oversized roof ornament.
signroot=empty('RoofIceCreamSign_ROOT',(.99,-.03,3.12),roof)
signroot.rotation_euler.y=math.radians(-65);signroot.scale=(4.2,4.2,4.2)
source=bpy.data.objects['FinishedCone_ROOT']
def clone_sign(src,parent):
    o=src.copy();o.name='RoofSign_'+src.name;current.objects.link(o);o.parent=parent
    for child in src.children:
        if 'SOCKET' not in child.name:clone_sign(child,o)
    return o
for child in source.children:
    if 'SOCKET' not in child.name:clone_sign(child,signroot)
for x in [.25,.95]:cube('Sign support',(x,-.03,3.14),(.13,.31,.22),plum,.024,roof)

# Convert curves and apply edge modifiers before exporting.
asset_collections=[c for c in scene.collection.children]
asset_objects=set(o for c in asset_collections for o in c.all_objects)
for o in list(asset_objects):
    if o.type in {'CURVE','FONT'}:
        bpy.ops.object.select_all(action='DESELECT');o.hide_set(False);o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
for o in list(asset_objects):
    if o.type=='MESH':
        bpy.context.view_layer.objects.active=o
        for mod in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
# Consolidate static pieces by parent, leaving doors, wheels, fills and pickup props separate.
for col in asset_collections:
    if col==equipment_collection:continue
    parents={o.parent for o in col.objects if o.type=='MESH'}
    for parent in parents:
        group=[o for o in col.objects if o.type=='MESH' and o.parent==parent]
        if len(group)>1:
            bpy.ops.object.select_all(action='DESELECT')
            for o in group:o.select_set(True)
            bpy.context.view_layer.objects.active=group[0];bpy.ops.object.join()
            group[0].name=parent.name.split(' • ')[0]+'_Mesh' if parent else col.name+'_Mesh'

# Set the final cabin and side labels to left-hand drive.
import runpy
runpy.run_path(str(ROOT/'Art/Source/left_hand_drive.py'))['move_driver_left']()

collection('99 • Truck studio • exclude from game export')
stage=current
floor=mat('Truck studio • lavender','8187A3',.85)
cube('Studio floor',(0,0,-.04),(200,200,.06),floor,.005)
world=scene.world or bpy.data.worlds.new('Truck studio world');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.34,.39,.5,1);world.node_tree.nodes['Background'].inputs[1].default_value=.3

def aim(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def area(name,loc,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);current.objects.link(o);o.location=loc;aim(o,(0,0,1.3))
area('Warm key',(-5,-6,8),1500,(1,.87,.74),6)
area('Cool fill',(1,4,7),1250,(.78,.87,1),5)
area('Rear rim',(6,-1,7),1350,(1,.84,.72),4)
area('Interior ceiling fill',(.9,.40,2.76),90,(1,.94,.85),2)
d=bpy.data.cameras.new('Truck review camera');cam=bpy.data.objects.new('Truck review camera',d);current.objects.link(cam);scene.camera=cam
cam.location=(-8.5,-10.5,6.3);aim(cam,(0,-.05,1.75));d.type='ORTHO';d.ortho_scale=9.0
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1300;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
for o in stage.objects:
    if o.type!='CAMERA':o.hide_set(True)
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            a.spaces.active.shading.type='MATERIAL';a.spaces.active.overlay.show_overlays=False
            a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.region_3d.view_camera_zoom=12
bpy.ops.object.select_all(action='DESELECT')
scene['asset_notes']='Ice cream truck art pass. Interior equipment appended from the separate preparation model. Separate local pivots for doors, hatch, steering wheel and road wheels. No gameplay code.'
bpy.context.view_layer.update()
assert len([o for o in bpy.data.objects if o.name.endswith('_Wheel_AXLE')])==4
assert all(n in bpy.data.objects for n in ['ServingHatch_HINGE','RearEntryDoor_HINGE','DriverDoor_HINGE','PassengerDoor_HINGE','DriverView_SOCKET','InteriorEquipment_ROOT'])
assert len([o for o in equipment.children_recursive if o.type=='EMPTY' and o.name.startswith('Tub_')])==12
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
# Export the vehicle together with its fitted equipment, without studio objects.
for col in scene.collection.children:
    if col!=stage:
        for o in col.all_objects:
            if not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'Art/Exports/IceCreamTruck.glb'),use_selection=True,export_format='GLB',export_yup=True,export_extras=True)
bpy.ops.object.select_all(action='DESELECT')
scene.render.filepath=str(ROOT/'Art/Previews/Truck_01_Exterior.png');bpy.ops.render.render(write_still=True)
# Cutaway uses the same model, with roof and opposite side removed from the view.
for o in roof.children_recursive:
    if o.type=='MESH':o.hide_render=True
for o in hatch.children_recursive:
    if o.type=='MESH':o.hide_render=True
for o in bpy.data.collections['12 • Cab doors and mirrors'].objects:
    if o.type=='MESH':o.hide_render=True
# Hide body shell for an honest view of the floorplan, while retaining cabin equipment.
for o in body.children_recursive:
    if o.type=='MESH':o.hide_render=True
for door in doors:
    for o in door.children_recursive:
        if o.type=='MESH':o.hide_render=True
rear.rotation_euler.z=math.radians(-95)
cam.location=(5.6,7.2,7.4);aim(cam,(.20,-.05,1.06));d.ortho_scale=8.2
scene.render.resolution_x=1800;scene.render.resolution_y=1300
scene.render.filepath=str(ROOT/'Art/Previews/Truck_02_Interior_Cutaway.png');bpy.ops.render.render(write_still=True)
# Restore shell for a rear view, keeping the access door open.
for o in hatch.children_recursive:
    if o.type=='MESH':o.hide_render=False
for o in bpy.data.collections['12 • Cab doors and mirrors'].objects:
    if o.type=='MESH':o.hide_render=False
for o in list(roof.children_recursive)+list(body.children_recursive):
    if o.type=='MESH':o.hide_render=False
for door in doors:
    for o in door.children_recursive:
        if o.type=='MESH':o.hide_render=False
cam.location=(8,-8,5);aim(cam,(.40,-.03,1.6));d.ortho_scale=8.1
scene.render.filepath=str(ROOT/'Art/Previews/Truck_03_Rear_Entry.png');bpy.ops.render.render(write_still=True)
rear.rotation_euler.z=0
cam.location=(1.35,1.12,2.16);aim(cam,(1.1,-.80,1.47));d.type='PERSP';d.lens=20;d.clip_start=.03
scene.render.resolution_x=1700;scene.render.resolution_y=1100
scene.render.filepath=str(ROOT/'Art/Previews/Truck_04_FirstPerson_Prep.png');bpy.ops.render.render(write_still=True)
print('TRUCK_COMPLETE',str(OUT))
