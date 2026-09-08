"""Check road dimensions, seams, park prop scale, and truck clearance."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype');bpy.context.view_layer.update();scene=bpy.context.scene
roads=bpy.data.collections['G • Modular ground'];tiles=[o for o in roads.objects if o.parent is None and 'grid_size_m' in o];assert len(tiles)==8
report={'tile_size_m':24,'road_width_m':12,'lane_width_m':6,'sidewalk_width_m':1.5,'tiles':{},'road_ports_checked':0}
for r in tiles:
    assert r['grid_size_m']==24
    points=[r.matrix_world.inverted() @ o.matrix_world @ Vector(p) for o in r.children if o.type=='MESH' for p in o.bound_box]
    extent=[max(p[i] for p in points)-min(p[i] for p in points) for i in range(2)];assert all(abs(n-24)<1e-4 for n in extent),(r.name,extent)
    report['tiles'][r.name]=extent
    if r.get('road_ports'):
        ob=next(o for o in r.children if o.type=='MESH');assert r['road_width_m']==12
        for port in r['road_ports']:
            for cross in [-11,-8,-6.75,-5,-1,1,5,6.75,8,11]:
                p=(cross,11.99,2) if port=='N' else (cross,-11.99,2) if port=='S' else (11.99,cross,2) if port=='E' else (-11.99,cross,2)
                hit,point,_,_=ob.ray_cast(ob.matrix_world.inverted() @ r.matrix_world @ Vector(p),Vector((0,0,-1)));assert hit
                h=(r.matrix_world.inverted() @ ob.matrix_world @ point).z;expected=0 if abs(cross)<6 else .12 if abs(cross)<7.5 else .06;assert abs(h-expected)<.0001,(r.name,port,cross,h)
            name=r.name.replace('_ROOT','')+'_RoadPort_'+port;socket=bpy.data.objects[name];local=r.matrix_world.inverted() @ socket.matrix_world.translation;assert abs(local.length-12)<1e-4
            report['road_ports_checked']+=1
# Linked park props keep their normal size. Their offsets are the only changes.
park=bpy.data.objects['Park_Cell_ROOT']
for ob in park.children:
    if ob.type=='EMPTY' and not ('Port' in ob.name):assert all(abs(v-1)<1e-5 for v in ob.scale),ob.name
# Measure the closed truck for driving; these temporary poses are not saved.
for name in ['ServingHatch_HINGE','DriverDoor_HINGE','PassengerDoor_HINGE','RearEntryDoor_HINGE']:bpy.data.objects[name].rotation_euler=(0,0,0)
bpy.context.view_layer.update();truck=bpy.data.objects['IceCreamTruck_ROOT'];inverse=truck.matrix_world.inverted();points=[inverse @ ob.matrix_world @ v.co for ob in truck.children_recursive if ob.type=='MESH' and not ob.hide_render for v in ob.data.vertices]
length=max(p.x for p in points)-min(p.x for p in points);width=max(p.y for p in points)-min(p.y for p in points)
assert width<6,(length,width)
# Sweep a conservative truck rectangle through the NE corner on a 12 m radius arc.
# Exits assume adjoining straight tiles, so the rectangle may extend beyond the cell boundary.
margin=99
for step in range(91):
    angle=math.pi+math.pi*.5*step/90;c=Vector((12+12*math.cos(angle),12+12*math.sin(angle)));forward=Vector((-math.sin(angle),math.cos(angle)));side=Vector((-forward.y,forward.x))
    for i in range(21):
        for j in range(7):
            p=c+forward*((i/20-.5)*length)+side*((j/6-.5)*width)
            # The corner consists of the north and east arms and their central square.
            inside=(abs(p.x)<=6 and p.y>=-6) or (abs(p.y)<=6 and p.x>=-6)
            assert inside,(step,list(p))
            margin=min(margin,max(6-abs(p.x),6-abs(p.y)))
report.update({'truck_closed_length_m':length,'truck_closed_width_including_mirrors_m':width,'lane_side_clearance_m':(6-width)/2,'corner_sweep_radius_m':12,'corner_sweep_sampled_clear':True,'park_prop_scale_preserved':True,'triangle_count_change_from_resize':sum(x['triangles_after']-x['triangles_before'] for x in json.loads((R/'Art/Source/larger-road-tiles.json').read_text())['resized_tiles'])})
(R/'Art/Source/larger-roads-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
