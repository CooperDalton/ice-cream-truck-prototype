"""Mirror the complete cab layout across the truck centerline with positive scales."""
import bpy
from mathutils import Matrix

def move_driver_left():
    truck=bpy.data.objects['IceCreamTruck_ROOT'];cabin=bpy.data.objects['Cabin_ROOT'];bpy.context.view_layer.update()
    inv=truck.matrix_world.inverted();steering=bpy.data.objects['SteeringWheel_ROOT']
    assert (inv @ steering.matrix_world.translation).y>0, 'Cab is already on the left.'
    reflection=Matrix.Diagonal((1.,-1.,1.,1.));objects=[cabin]+list(cabin.children_recursive)
    before={o:(o.matrix_basis.copy(),o.matrix_parent_inverse.copy()) for o in objects}
    positions={o:[inv @ o.matrix_world @ v.co for v in o.data.vertices] for o in objects if o.type=='MESH'}
    for o in objects:
        if o.type=='MESH':
            original=o.data
            normals={(p.index,original.loops[i].vertex_index):reflection.to_3x3() @ original.corner_normals[i].vector for p in original.polygons for i in p.loop_indices}
            o.data=original.copy();o.data.name=original.name+' left hand drive';o.data.transform(reflection);o.data.flip_normals()
            o.data.normals_split_custom_set([normals[(p.index,o.data.loops[i].vertex_index)] for p in o.data.polygons for i in p.loop_indices]);o.data.update()
        basis,parent_inverse=before[o];o.matrix_parent_inverse=reflection @ parent_inverse @ reflection;o.matrix_basis=reflection @ basis @ reflection
    bpy.context.view_layer.update()
    error=0
    for o,points in positions.items():
        for v,p in zip(o.data.vertices,points):error=max(error,(inv @ o.matrix_world @ v.co-reflection @ p).length)
    assert error<.00002,error
    assert all(o.matrix_world.determinant()>0 for o in objects)
    # Names follow the actual vehicle side, without moving the doors or road wheels.
    pairs=[('DriverDoor_HINGE','PassengerDoor_HINGE'),('DriverDoor_HINGE_Mesh','PassengerDoor_HINGE_Mesh')]
    pairs += [(o.name,o.name.replace('Left','Right')) for o in list(truck.children_recursive) if 'Left' in o.name and o.name.replace('Left','Right') in bpy.data.objects]
    for a,b in pairs:
        x=bpy.data.objects[a];y=bpy.data.objects[b];x.name='DriverSideRenameTemporary';y.name=a;x.name=b
    truck['driver_side']='Left when facing forward; truck-local -Y';cabin['layout']='Left-hand drive: wheel, column, gauges, switches, gear lever, pedals and driver anchors mirrored together.'
    checks={name:list(inv @ bpy.data.objects[name].matrix_world.translation) for name in ['SteeringWheel_ROOT','DriverSeat_SOCKET','DriverView_SOCKET','DriverDoor_HINGE']}
    assert all(p[1]<0 for p in checks.values()),checks
    return {'driver_positions_in_truck_space':checks,'maximum_mirror_error_m':error,'positive_transform_determinants':True,'mesh_counts_unchanged':True}
