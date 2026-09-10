"""Create the town scenery library and export its game meshes."""
import ast, bpy, bmesh, json, math, random
from pathlib import Path
from mathutils import Vector, Matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Ice Cream Truck Prototype/Assets/Art/Tycoon/Town'
OUT.mkdir(parents=True,exist_ok=True)
for file,names in [('build_art_style_review.py',{'color','material','mesh','box','blob','branch'}),('build_art_style_round2.py',{'lathe'})]:
    tree=ast.parse((ROOT/'Art/Source'/file).read_text())
    exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),file,'exec'))
scene=bpy.data.scenes.new('Town - model library');bpy.context.window.scene=scene
gallery=bpy.data.collections.new('P - Toon town scenery');scene.collection.children.link(gallery)
style='Cel';materials={};assets=[];current=root=None
cream=material('Town ivory','FFF1D2');wood=material('Town cedar','BA815B');dark=material('Town ink','454053')
mint=material('Town teal','65AA99');pink=material('Town rose','D7829E');gold=material('Town gold','E8BA66')
glass=material('Town glass','6390A6');leaf=material('Town foliage','76A775');lightleaf=material('Town lime','A7C880')
soil=material('Town soil','70594C');stone=material('Town stone','B4B8AE');water=material('Town water','7DCAD2')
coral=material('Town clay','D79679');lavender=material('Town lilac','AAA2C7')

def start(name,footprint):
    global current,root
    current=bpy.data.collections.new('Town / '+name);gallery.children.link(current)
    root=bpy.data.objects.new('Town_'+name+'_ROOT',None);current.objects.link(root)
    root.location=(290+(len(assets)%6)*16,-(len(assets)//6)*16,0)
    root['style']='Cel cartoon';root['front']='-Y';root['footprint']=footprint
    assets.append(dict(name=name,collection=current.name,root=root.name,footprint=footprint))

def roof(w,d,z,h,mat):
    verts=[(-w/2,-d/2,z),(w/2,-d/2,z),(0,-d/2,z+h),(-w/2,d/2,z),(w/2,d/2,z),(0,d/2,z+h)]
    mesh('Gabled roof',verts,[(0,2,1),(3,4,5),(0,3,5,2),(2,5,4,1),(1,4,3,0)],mat,.065,False)
    for y in [-d/2-.025,d/2+.025]:
        branch('Roof fascia',(-w/2,y,z),(0,y,z+h),.085,.085,cream);branch('Roof fascia',(0,y,z+h),(w/2,y,z),.085,.085,cream)
    branch('Ridge cap',(0,-d/2,z+h),(0,d/2,z+h),.095,.095,mat)

def window(x,y,z,w=1,h=1.35,shutters=False):
    box('Window surround',(x,y,z),(w+.2,.13,h+.2),cream,.045)
    box('Window glass',(x,y-.075,z),(w,.025,h),glass,.025)
    box('Window mullion',(x,y-.10,z),(.055,.04,h),cream,.01)
    box('Window crossbar',(x,y-.10,z),(w,.04,.055),cream,.01)
    box('Window sill',(x,y-.11,z-h/2-.1),(w+.3,.3,.12),cream,.025)
    if shutters:
        for dx in [-w*.75,w*.75]:
            box('Shutter',(x+dx,y-.025,z),(w*.35,.08,h),mint,.03)
            for dz in [-.35,0,.35]:box('Shutter slat',(x+dx,y-.08,z+dz),(w*.3,.03,.07),cream,.012)

def flowerpot(x,y,z,size=.4):
    lathe('Terracotta pot',[(0,0),(.7*size,0),(size,size*1.3),(1.08*size,size*1.3),(1.08*size,size*1.5),(.85*size,size*1.5)],coral,(x,y,z),16)
    for i in range(5):
        a=i*math.tau/5;px=x+math.cos(a)*size*.7;py=y+math.sin(a)*size*.7
        branch('Flower stem',(px,py,z+size),(px,py,z+size*2.4),.02,.01,leaf)
        blob('Bloom',(px,py,z+size*2.4),(size*.28,size*.28,size*.22),pink if i%2 else gold,1)

for name,w,d,h,wall,roofmat in [('Porch_cottage',6,5,3.5,mint,coral),('Dormer_house',6,5.5,5.6,cream,lavender),('Brick_townhouse',5,5.5,6.2,coral,dark),('Lemon_house',6.5,5,4,gold,mint)]:
    start(name,[w,d]);box('Foundation',(0,0,.2),(w+.2,d+.2,.4),stone,.09)
    box('Plaster walls',(0,0,h/2+.3),(w,d,h),wall,.13);roof(w+.7,d+.7,h+.3,1.8,roofmat)
    box('Door frame',(0,-d/2-.04,1.45),(1.35,.15,2.5),cream,.07)
    box('Front door',(0,-d/2-.14,1.4),(1.08,.07,2.22),pink,.055)
    blob('Brass doorknob',(.38,-d/2-.23,1.4),(.075,.06,.075),gold,2)
    for x in [-w*.3,w*.3]:window(x,-d/2-.07,2,1.0,1.25,True)
    if h>5:
        for x in [-w*.29,0,w*.29]:window(x,-d/2-.07,4.5,.95,1.35)
    else:
        box('Porch deck',(0,-d/2-.9,.25),(3.8,1.8,.35),wood,.06)
        for x in [-1.7,1.7]:branch('Porch column',(x,-d/2-1.6,.4),(x,-d/2-1.6,2.9),.085,.085,cream)
        box('Porch awning',(0,-d/2-.85,3),(4.1,2,.18),roofmat,.09)
    for step in range(3):box('Entry steps',(0,-d/2-.3-step*.38,.08+(2-step)*.08),(1.65,.55,.16+(2-step)*.16),stone,.045)
    box('Chimney',(w*.26,d*.15,h+1.25),(.65,.65,2),coral,.045)
    for z in [.9,1.2,1.5]:box('Chimney brick band',(w*.26,d*.15,h+z),(.68,.68,.06),cream,.015)
    flowerpot(-w*.43,-d/2-.6,.1,.27);flowerpot(w*.43,-d/2-.6,.1,.27)

for name,wall,awning in [('Corner_bakery',coral,cream),('Garden_cafe',cream,mint),('Seaside_shop',lavender,pink)]:
    start(name,[7,5]);box('Shop walls',(0,0,3.1),(7,5,6.2),wall,.12)
    box('Shop cornice',(0,0,6.3),(7.4,5.4,.35),cream,.10);box('Roof inset',(0,0,6.5),(6.7,4.7,.15),dark,.04)
    for x in [-2.2,2.2]:
        window(x,-2.57,1.8,2.0,2.2);window(x,-2.57,4.8,1.35,1.55,True)
    box('Shop door',(0,-2.57,1.4),(1.1,.14,2.8),glass,.045)
    for x in [-.65,.65]:box('Door jamb',(x,-2.68,1.4),(.13,.15,2.8),cream,.02)
    box('Door handle',(.4,-2.77,1.25),(.07,.08,.5),gold,.015)
    for i in range(12):
        x=-3.3+i*.6
        box('Striped awning',(x,-3.15,3.1),(.6,1.4,.15),awning if i%2 else pink,.04,tilt=0)
        blob('Scalloped valance',(x,-3.85,2.96),(.31,.09,.19),awning if i%2 else pink,2)
    # The hanging sign uses a modeled symbol, never lettering.
    branch('Sign bracket',(3.3,-2.6,4.0),(3.3,-3.55,4.0),.06,.06,dark)
    box('Hanging plaque',(3.3,-3.5,3.57),(.75,.17,.65),mint,.18)
    if name=='Corner_bakery':
        for i in range(3):blob('Bread emblem',(3.3+(i-1)*.15,-3.61,3.57),(.12,.045,.22),gold,2)
    elif name=='Garden_cafe':
        box('Cup emblem',(3.3,-3.61,3.57),(.35,.06,.27),cream,.07)
    else:blob('Scoop emblem',(3.3,-3.62,3.65),(.2,.06,.18),pink,2)

start('Park_bench',[1.9,.75])
for x in [-.7,.7]:
    for y in [-.24,.24]:branch('Bench leg',(x,y,0),(x,y,.48),.065,.065,dark)
    branch('Back support',(x,.25,.3),(x,.35,1.05),.06,.06,dark)
for y in [-.24,0,.24]:box('Seat slat',(0,y,.48),(1.9,.18,.09),wood,.04)
for z in [.76,.99]:box('Backrest slat',(0,.32,z),(1.9,.09,.18),wood,.045)

start('Picnic_table',[2.3,1.9])
for x in [-.72,.72]:
    for side in [-1,1]:branch('A frame leg',(x,side*.7,0),(x,side*.18,.82),.07,.07,cream)
for y in [-.3,-.1,.1,.3]:box('Table board',(0,y,.83),(2.3,.185,.1),wood,.035)
for y in [-.83,.83]:box('Picnic bench',(0,y,.45),(2.4,.4,.1),wood,.04)

start('Street_lantern',[.6,.6])
lathe('Lamp base',[(0,0),(.25,0),(.25,.14),(.12,.4),(.085,3.3)],dark,segments=16)
box('Lantern glowing glass',(0,0,3.55),(.42,.42,.55),gold,.045)
for x in [-.22,.22]:
    for y in [-.22,.22]:branch('Lantern frame',(x,y,3.23),(x,y,3.87),.035,.035,dark)
lathe('Lantern roof',[(0,4.0),(.34,3.85),(.34,3.78)],dark,segments=4)

start('Flower_planter',[1.6,.7])
box('Planter box',(0,0,.35),(1.6,.7,.7),cream,.07);box('Soil',(0,0,.7),(1.45,.55,.035),soil,.02)
for i in range(7):
    x=-.6+i*.2;blob('Leaf clump',(x,0,.82),(.23,.25,.18),leaf,1)
    blob('Flower head',(x,-.04,1.03),(.11,.11,.10),pink if i%2 else gold,2)

start('Hedge_section',[3,.8])
for x in [-1,-.5,0,.5,1]:blob('Hedge foliage',(x,0,.7),(.62,.48,.7),leaf,2)

start('Picket_fence',[3,.2])
for z in [.35,.8]:box('Fence rail',(0,0,z),(3,.09,.1),cream,.025)
for i in range(8):
    x=-1.4+i*.4;box('Picket',(x,-.06,.55),(.21,.1,1.1),cream,.04)
    mesh('Picket point',[(x-.105,-.11,1.1),(x+.105,-.11,1.1),(x,-.11,1.26),(x-.105,-.01,1.1),(x+.105,-.01,1.1),(x,-.01,1.26)],[(0,1,2),(3,5,4),(0,3,4,1),(1,4,5,2),(2,5,3,0)],cream,.02)

start('Street_bin',[.65,.65])
lathe('Bin body',[(0,0),(.27,0),(.31,.85),(.34,.87),(.34,.95),(.28,1.03)],mint,segments=20)
lathe('Dark opening',[(0,1.04),(.20,1.04)],dark,segments=20)
for i in range(10):
    a=i*math.tau/10;branch('Bin rib',(.28*math.cos(a),.28*math.sin(a),.1),(.30*math.cos(a),.30*math.sin(a),.8),.015,.015,cream)

start('Bus_shelter',[3.8,1.8])
for x in [-1.8,1.8]:
    for y in [-.6,.6]:branch('Shelter post',(x,y,0),(x,y,2.5),.065,.065,mint)
box('Shelter roof',(0,0,2.55),(4,1.8,.22),mint,.15)
box('Back panel',(0,.65,1.35),(3.55,.07,2.1),glass,.04)
box('Waiting bench',(0,.25,.5),(3,.5,.12),wood,.05)
for x in [-1.15,1.15]:box('Bench foot',(x,.25,.25),(.12,.35,.5),dark,.035)

start('Park_gazebo',[5,5])
lathe('Gazebo deck',[(0,0),(2.7,0),(2.7,.25),(0,.25)],wood,segments=8)
for i in range(8):
    a=i*math.tau/8;branch('Gazebo post',(2.3*math.cos(a),2.3*math.sin(a),.25),(2.3*math.cos(a),2.3*math.sin(a),3),.10,.10,cream)
lathe('Gazebo roof',[(0,4.2),(2.9,3.0),(2.9,2.88)],mint,segments=8)
blob('Roof finial',(0,0,4.22),(.16,.16,.22),gold,2)

start('Plaza_fountain',[4,4])
lathe('Fountain basin',[(0,0),(2,0),(2,.3),(1.84,.45),(1.65,.45),(1.65,.2),(0,.2)],cream,segments=32)
lathe('Water surface',[(0,.29),(1.66,.29)],water,segments=32)
lathe('Center pedestal',[(0,.3),(.45,.3),(.3,1.25),(.85,1.3),(.85,1.45),(0,1.45)],stone,segments=24)
lathe('Upper water',[(0,1.46),(.7,1.46)],water,segments=24)
blob('Water spout',(0,0,1.67),(.11,.11,.35),water,2)

start('Playground_swing',[4.2,2.5])
for x in [-1.9,1.9]:
    for y in [-1.1,1.1]:branch('Swing A frame',(x,y,0),(x,0,2.8),.09,.09,coral)
branch('Swing crossbar',(-2.1,0,2.8),(2.1,0,2.8),.11,.11,mint)
for x in [-.85,.85]:
    for dx in [-.24,.24]:branch('Swing rope',(x+dx,0,2.73),(x+dx,-.12,.5),.025,.025,cream)
    box('Swing seat',(x,-.12,.5),(.68,.42,.1),mint,.08)

start('Playground_slide',[2.5,4])
box('Slide platform',(0,.9,1.5),(1.1,1.1,.16),wood,.05)
for x in [-.45,.45]:
    branch('Platform leg',(x,1.25,0),(x,1.25,1.6),.06,.06,mint)
    branch('Ladder rail',(x,1.95,0),(x,1.25,1.65),.05,.05,coral)
    branch('Slide edge',(x,.4,1.55),(x,-1.9,.2),.07,.07,pink)
for i in range(6):box('Ladder rung',(0,1.9-i*.115,.15+i*.25),(.9,.1,.07),cream,.025)
mesh('Slide chute',[(-.45,.4,1.52),(.45,.4,1.52),(.45,-1.9,.18),(-.45,-1.9,.18)],[(0,1,2,3)],gold)

start('Park_entry_arch',[3.8,.5])
for x in [-1.7,1.7]:box('Arch post',(x,0,1.4),(.22,.25,2.8),cream,.07)
branch('Arch lintel',(-1.8,0,2.65),(1.8,0,2.65),.16,.16,mint)
for x in [-1.4,-.7,0,.7,1.4]:blob('Arch greenery',(x,0,2.8),(.52,.3,.4),leaf,2)

for name,bodymat in [('Parked_hatchback',pink),('Parked_van',mint)]:
    start(name,[2,4]);box('Car body',(0,0,.72),(1.9,3.8,.65),bodymat,.23)
    box('Cabin',(0,.15,1.32),(1.6,2.0,.85),bodymat,.23)
    box('Windshield',(0,-.88,1.47),(1.35,.06,.56),glass,.09)
    box('Rear window',(0,1.18,1.45),(1.3,.06,.48),glass,.07)
    for x in [-.84,.84]:box('Side window',(x,.15,1.47),(.05,1.65,.52),glass,.08)
    for x in [-.98,.98]:
        for y in [-1.2,1.2]:
            wheel=lathe('Tire',[(0,-.13),(.39,-.13),(.41,0),(.39,.13),(0,.13)],dark,(x,y,.43),20);wheel.rotation_euler.y=math.pi/2
            blob('Wheel hub',(x*1.035,y,.43),(.045,.2,.2),cream,2)
    for x in [-.62,.62]:box('Headlamp',(x,-1.91,.8),(.4,.07,.23),cream,.07)
    box('Bumper',(0,-1.96,.49),(1.65,.13,.16),cream,.06)

start('Willow_tree',[4,4])
branch('Tree trunk',(0,0,0),(.12,0,3.4),.3,.12,wood)
for i in range(7):
    a=i*math.tau/7;x=math.cos(a)*1.3;y=math.sin(a)*1.3
    branch('Tree bough',(.1,0,2.3),(x,y,3.8),.12,.06,wood)
    blob('Drooping crown',(x,y,3.65),(1.25,1.2,1.55),leaf if i%2 else lightleaf,2)

start('Cypress_tree',[2.2,2.2])
branch('Cypress trunk',(0,0,0),(0,0,4.7),.2,.05,wood)
for i in range(4):blob('Cypress crown',(0,0,2+i*.8),(1.1-i*.2,1.1-i*.2,1.45),leaf,2)

start('Garden_rocks',[2,1.6])
for x,y,z,s in [(-.5,0,.35,.6),(.45,.2,.5,.7),(.2,-.5,.2,.35)]:blob('Soft rock',(x,y,z),(s,s*.8,s*.75),stone,1)

start('Sidewalk_slab',[4,2])
box('Pavement',(0,0,.07),(4,2,.14),cream,.025)
for x in [-1,0,1]:box('Paving seam',(x,0,.143),(.018,1.95,.004),stone,.002)
box('Center seam',(0,0,.143),(3.95,.018,.004),stone,.002)

start('Curb_section',[4,.2])
box('Rounded curb',(0,0,.10),(4,.22,.20),cream,.035)

scene.view_settings.view_transform='Standard'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/ToonTown_Additions.blend'))
export=bpy.data.scenes.new('Town export')
manifest=[];material_data={}
for entry in assets:
    bpy.context.window.scene=scene;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    source_root=bpy.data.objects[entry['root']];copies=[]
    wrapper=bpy.data.objects.new('Town model',None);export.collection.objects.link(wrapper)
    for obj in bpy.data.collections[entry['collection']].objects:
        if obj.type!='MESH':continue
        data=bpy.data.meshes.new_from_object(obj.evaluated_get(deps),depsgraph=deps)
        copy=bpy.data.objects.new(obj.name,data);export.collection.objects.link(copy);copy.parent=wrapper
        copy.matrix_world=Matrix.Translation(-source_root.matrix_world.translation)@obj.matrix_world
        copies.append(copy)
        for mat in data.materials:material_data[mat.name]=list(mat.diffuse_color)
    bpy.context.window.scene=export;bpy.ops.object.select_all(action='DESELECT');wrapper.select_set(True)
    for obj in copies:obj.select_set(True)
    bpy.context.view_layer.objects.active=wrapper
    bpy.ops.export_scene.fbx(filepath=str(OUT/(entry['name']+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
    manifest.append(entry)
    for obj in copies:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(wrapper,do_unlink=True)
(OUT/'TownModels.json').write_text(json.dumps(dict(models=manifest,materials=[dict(name=n,color=c) for n,c in material_data.items()]),indent=2))
print('TOWN_MODELS_EXPORTED',len(manifest))
