"""Add modular two- and three-scoop cones to the existing Blender scene."""
import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path('/Users/cooperdalton/Ice Cream Truck Prototype')


def add_variants():
    source = bpy.data.objects['FinishedCone_ROOT']
    target_collection = source.users_collection[0]
    first = next(o for o in source.children if o.type == 'EMPTY' and o.name.startswith('IceCreamScoop'))
    source['scoop_capacity'] = 3
    source['scoop_count'] = 1
    source['stack_spacing_m'] = .12
    # All cones use the same three local placement positions.
    first_socket = next(o for o in source.children if o.name.startswith('Scoop_SOCKET'))
    first_socket.location.z = .201
    for i in (2, 3):
        name = f'FinishedCone_Scoop{i:02}_SOCKET'
        slot = bpy.data.objects.get(name)
        if slot is None:
            slot = bpy.data.objects.new(name, None)
            target_collection.objects.link(slot)
        slot.parent = source
        slot.location = (0, 0, .201 + .12 * (i-1))
        slot.empty_display_size = .02

    def clone_tree(original, parent, prefix, flavor=None):
        copy = original.copy()
        copy.name = prefix + '_' + original.name
        target_collection.objects.link(copy)
        copy.parent = parent
        if copy.type == 'MESH' and flavor:
            for index, slot in enumerate(copy.material_slots):
                if slot.material and slot.material.name.startswith('Flavor • '):
                    slot.link = 'OBJECT'
                    slot.material = bpy.data.materials[flavor]
        for child in original.children:
            clone_tree(child, copy, prefix, flavor)
        return copy

    for count, x in [(2, .205), (3, .615)]:
        name = f'Cone_{count}Scoops_ROOT'
        if bpy.data.objects.get(name):
            continue
        root = source.copy()
        root.name = name
        target_collection.objects.link(root)
        root.location.x = x
        root['scoop_count'] = count
        for child in source.children:
            if child != first:
                clone_tree(child, root, f'Cone{count}')
        for i in range(count):
            flavor = ['Flavor • Strawberry', 'Flavor • Vanilla', 'Flavor • Chocolate'][i]
            part = clone_tree(first, root, f'Cone{count}_Scoop{i+1:02}', flavor)
            part.name = f'Cone{count}_Scoop{i+1:02}_ROOT'
            part.location = (0, 0, .201 + .12*i)
            part['stack_index'] = i + 1
    bpy.context.view_layer.update()
    for count, name in [(1,'FinishedCone_ROOT'),(2,'Cone_2Scoops_ROOT'),(3,'Cone_3Scoops_ROOT')]:
        root = bpy.data.objects[name]
        scoops = [o for o in root.children if o == first or o.name.endswith('_ROOT') and '_Scoop' in o.name]
        sockets = [o for o in root.children if 'SOCKET' in o.name]
        assert len(scoops) == count, (name, len(scoops))
        assert len(sockets) == 3, (name, len(sockets))
        assert all(abs(o.location.z - (.201 + .12*i)) < .00001 for i,o in enumerate(sorted(scoops,key=lambda o:o.location.z)))
        print('VERIFIED', name, count, 'separate scoops, 3 attachment sockets')


if __name__ == '__main__':
    add_variants()
    scene=bpy.context.scene
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    for collection in scene.collection.children:
        if not collection.name.startswith('99'):
            for o in collection.objects:
                if not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'Art/Exports/IceCreamPreparation.glb'),use_selection=True,export_format='GLB',export_yup=True)
    bpy.ops.object.select_all(action='DESELECT')
    cam=scene.camera
    # Refresh the overall render, then render the three stack heights together.
    scene.render.filepath=str(ROOT/'Art/Previews/01_Preparation_Set.png')
    bpy.ops.render.render(write_still=True)
    cam.location=(1.1,-3,2.0)
    cam.rotation_euler=(Vector((.19,-.39,1.25))-cam.location).to_track_quat('-Z','Y').to_euler()
    cam.data.type='ORTHO';cam.data.ortho_scale=1.43
    scene.render.resolution_x=1500;scene.render.resolution_y=1200
    scene.render.filepath=str(ROOT/'Art/Previews/05_One_Two_Three_Scoops.png')
    bpy.ops.render.render(write_still=True)
