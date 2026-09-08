"""Give the easy-mode player independent floating hands and grip anchors."""
import bpy,json
from pathlib import Path
from mathutils import Vector,Matrix
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
scene=bpy.context.scene
checks=[]
for name in ['Crew_Rig','FirstPersonHands_Rig']:
    rig=bpy.data.objects[name];body=next(o for o in rig.children if o.type=='MESH');fp=name.startswith('FirstPerson')
    def coordinates():
        bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
        out=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return out
    neutral=coordinates()
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for side in ['L','R']:
        b=rig.data.edit_bones['Hand_'+side];b.use_connect=False;b.parent=rig.data.edit_bones['Root']
    bpy.ops.object.mode_set(mode='OBJECT')
    assert max((a-b).length for a,b in zip(neutral,coordinates()))<1e-5
    rig.parent['easy_mode_hand_setup']='Floating left and right hands. Translate or rotate Hand_L and Hand_R independently; no arms or reach constraints.'
    rig['controls']='Hand_L and Hand_R are unconnected children of Root. Body motion does not pull the hands.'
    for sign,side in [(-1,'L'),(1,'R')]:
        bone=rig.data.bones['Hand_'+side];pb=rig.pose.bones[bone.name]
        sock_name=('FirstPerson' if fp else 'Crew')+'_Grip_'+side+'_SOCKET'
        sock=bpy.data.objects.get(sock_name)
        if sock is None:
            sock=bpy.data.objects.new(sock_name,None);rig.users_collection[0].objects.link(sock)
        sock.parent=rig;sock.parent_type='BONE';sock.parent_bone=bone.name;sock.empty_display_type='PLAIN_AXES';sock.empty_display_size=.045
        palm=Vector((sign*(.28 if fp else .66),-.06 if fp else -.13,.2615 if fp else 1.1015))
        parent_matrix=bone.matrix_local @ Matrix.Translation((0,bone.length,0))
        sock.matrix_parent_inverse=Matrix.Identity(4);sock.matrix_basis=parent_matrix.inverted() @ Matrix.Translation(palm)
        sock['usage']='Attach a held scooper, bottle, or cone here. This follows only its own hand control.'
        bpy.context.view_layer.update();start=sock.matrix_world.translation.copy()
        assert (start-rig.matrix_world @ palm).length<1e-5,(sock_name,start,rig.matrix_world @ palm)
        base=coordinates();pb.location.x=.3;posed=coordinates()
        moving=body.vertex_groups[bone.name].index
        expected={v.index for v in body.data.vertices if any(g.group==moving and g.weight>.99 for g in v.groups)}
        moved={i for i,(a,b) in enumerate(zip(base,posed)) if (a-b).length>1e-4}
        assert moved==expected,(name,side,len(moved),len(expected))
        delta=(sock.matrix_world.translation-start).length;assert abs(delta-.3)<1e-4
        checks.append({'rig':name,'hand':side,'independent_vertices':len(moved),'grip_socket_movement_m':round(delta,4)})
        pb.location.x=0
    if not fp:
        base=coordinates();rig.pose.bones['Body'].rotation_mode='XYZ';rig.pose.bones['Body'].rotation_euler.y=.25;posed=coordinates()
        handgroups={body.vertex_groups[n].index for n in ['Hand_L','Hand_R']}
        indices={v.index for v in body.data.vertices if any(g.group in handgroups for g in v.groups)}
        assert all((base[i]-posed[i]).length<1e-5 for i in indices)
        rig.pose.bones['Body'].rotation_euler.y=0
    bpy.context.view_layer.update();assert max((a-b).length for a,b in zip(neutral,coordinates()))<1e-5
bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=None
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
for name,groups in [('Characters',['C • Characters','D • First-person hands']),('WorkshopModels',[c.name for c in scene.collection.children if not c.name.startswith('Z')])]:
    bpy.ops.object.select_all(action='DESELECT')
    for group in groups:
        for o in bpy.data.collections[group].all_objects:
            if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(R/'Art/Exports'/(name+'.glb')),use_selection=True,export_format='GLB',export_yup=True,export_extras=True,export_animations=False)
(R/'Art/Source/floating-hands-verification.json').write_text(json.dumps(checks,indent=2)+'\n')
print('INDEPENDENT_HANDS_VERIFIED',json.dumps(checks))
