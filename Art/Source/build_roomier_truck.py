"""Build the larger unbranded truck source for the shared workshop."""
from pathlib import Path
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
s=(R/'Art/Source/build_ice_cream_truck.py').read_text()
s=s[:s.index("collection('99 • Truck studio")]
s=s.replace("Ice Cream Truck Prototype/Assets/IceCreamTruckSimulatorModels.blend","Art/Source/PreparationBeforeRevision.blend")
# Reduce the resolution of small manufactured details at construction time.
s=s.replace("exec(compile(helper,'prep_model_helpers','exec'))", "helper=helper.replace('b.segments=3','b.segments=1').replace('c.bevel_resolution=2','c.bevel_resolution=1').replace('major_segments=40','major_segments=24').replace('vertices=32','vertices=20')\nexec(compile(helper,'prep_model_helpers','exec'))")
s=s.replace("vertices=48,radius=.565", "vertices=24,radius=.565").replace('range(33)','range(17)').replace('a*pi/32','a*pi/16').replace('verts=[];n=40','verts=[];n=24')
start=s.index('        for k in range(30):');end=s.index("\ncollection('16",start);s=s[:start]+s[end:]
s=s.replace("(1.25,y,1.08),(3.82,.12,1.10)", "(1.25,y,.925 if sign==-1 else 1.08),(3.82,.12,.73 if sign==-1 else 1.10)")
s=s.replace("(2.92,y,2.21),(.46,.12,1.33)","(2.92,y,2.025),(.46,.12,1.70)").replace("(-.54,y,2.21),(.30,.12,1.33)","(-.54,y,2.025),(.30,.12,1.70)")
s=s.replace("(0,0,-.465),(2.84,.065,.93)","(0,0,-.63),(2.99,.065,1.26)").replace("(0,.038,-.465),(2.75,.014,.83)","(0,.038,-.63),(2.9,.014,1.16)").replace("(-1.20+i*.40,-.038,-.465),(.18,.014,.88)","(-1.20+i*.40,-.038,-.63),(.18,.014,1.20)")
s=s.replace("(.99,-1.51,1.55),(2.91,.43,.075)","(.99,-1.55,1.29),(3.05,.60,.075)").replace("(.99,-1.731,1.55),(2.82,.018,.040)","(.99,-1.856,1.29),(2.96,.018,.040)")
# None of the truck lettering is retained.
s='\n'.join(line for line in s.splitlines() if not line.startswith('label('))+'\n'
insert="""
import runpy
cone_mesh=runpy.run_path(str(ROOT/'Art/Source/flat_waffle_cone.py'))['build_cone_mesh']()
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and any(n in ob.name for n in ['FinishedCone_ROOT_Mesh','EmptyCone_ROOT_Mesh']):
        ob.data=cone_mesh;ob.material_slots[0].link='DATA'
# Widen and lengthen the shell, while keeping the equipment at working scale.
from mathutils import Matrix
hatch.rotation_euler.x=0
bpy.context.view_layer.update()
scale=Matrix.Diagonal((1.12,1.40,1.18,1.0))
scale.translation=(0,0,-.56*.18)
skip=set([equipment]+list(equipment.children_recursive))
objs=[o for o in truck.children_recursive if o not in skip]
old={o:o.matrix_world.copy() for o in objs}
def depth(o):
    n=0
    while o.parent:n+=1;o=o.parent
    return n
for o in sorted(objs,key=depth):
    o.matrix_world=scale @ old[o]
    bpy.context.view_layer.update()
hatch.rotation_euler.x=math.radians(-98)
equipment.location=(1.35,1.22,.56);equipment.rotation_euler.z=0
truck['dimensions_m']='7.26 long x 3.98 body width; interior ceiling 2.71 m above floor'
truck['clear_work_aisle_m']=2.55
truck['serving_window_width_m']=3.45
truck['serving_window_height_m']=1.49
truck['layout']='Preparation counter on the opposite wall from the open serving window.'
# A contrasting frame makes the empty serving opening visible from either side.
current=bpy.data.collections['13 • Serving hatch']
for xx in [-.40,2.68]:cube('Serving window vertical frame',(xx*1.12,-1.94,2.20),(.075,.08,1.48),mint,.02,truck)
for zz in [1.42,2.91]:cube('Serving window horizontal frame',(1.14,-1.94,zz),(3.52,.08,.085),mint,.02,truck)
empty('ServeCustomer_SOCKET',(1.14,-2.21,1.49),truck)
empty('ServingView_SOCKET',(1.14,-.50,2.18),truck)
"""
s=s.replace('# Convert curves and apply edge modifiers before exporting.',insert+'\n# Convert curves and apply edge modifiers before exporting.')
s+="\nbpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Art/Source/RoomierTruck.blend'))\nprint('ROOMIER_TRUCK_BUILT')\n"
exec(compile(s,'roomier_truck','exec'))
