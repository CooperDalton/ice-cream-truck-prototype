"""Build three art studies beside the original assets, then render matching views.

Run with Blender --background <original workshop backup> --python this-file.
The candidate stays outside Assets until its renders and preservation audit pass.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / 'Art/Previews/ArtStyleReview'
OUTPUT.mkdir(parents=True, exist_ok=True)
original_scene = bpy.context.scene
original_names = set(bpy.data.objects.keys())


def fingerprint(obj):
    state = [obj.name, obj.parent.name if obj.parent else None,
             list(map(list, obj.matrix_world))]
    if obj.type == 'MESH':
        state += [[list(v.co) for v in obj.data.vertices],
                  [list(p.vertices) + [p.material_index] for p in obj.data.polygons],
                  [m.name for m in obj.data.materials]]
    return hashlib.sha256(json.dumps(state).encode()).hexdigest()


before = {name: fingerprint(bpy.data.objects[name]) for name in original_names}
review = bpy.data.scenes.new('Art style review')
bpy.context.window.scene = review
review.render.engine = 'CYCLES'
review.cycles.samples = 24
review.cycles.use_denoising = True
review.render.resolution_x = 960
review.render.resolution_y = 800
review.render.resolution_percentage = 100
review.render.image_settings.file_format = 'PNG'
review.view_settings.view_transform = 'Standard'
review.view_settings.look = 'None'
review.world = bpy.data.worlds.new('Art review warm studio')
review.world.use_nodes = True
review.world.node_tree.nodes['Background'].inputs[0].default_value = (.32, .37, .48, 1)
review.world.node_tree.nodes['Background'].inputs[1].default_value = .35
gallery = bpy.data.collections.new('L - Art style alternatives')
review.collection.children.link(gallery)
original_scene.collection.children.link(gallery)
current = None
root = None
style = ''
materials = {}


def color(hexcode):
    rgb = [int(hexcode[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in rgb)


def material(name, hexcode, rough=.7):
    key = (style, name)
    if key in materials:
        return materials[key]
    m = bpy.data.materials.new(f'ArtReview {style} {name}')
    m.use_nodes = True
    rgb = color(hexcode)
    m.diffuse_color = (*rgb, 1)
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = rough
    if style == 'Painted':
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 3.0
        noise.inputs['Detail'].default_value = .5
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = .23
        ramp.color_ramp.elements[0].color = (*(c * .82 for c in rgb), 1)
        ramp.color_ramp.elements[1].position = .8
        ramp.color_ramp.elements[1].color = (*(min(1, c * 1.1 + .02) for c in rgb), 1)
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs[0], p.inputs['Base Color'])
        p.inputs['Roughness'].default_value = .95
    if style == 'Cel':
        geometry = nodes.new('ShaderNodeNewGeometry')
        light_dot = nodes.new('ShaderNodeVectorMath')
        light_dot.operation = 'DOT_PRODUCT'
        light_dot.inputs[1].default_value = Vector((-5, -7, 10)).normalized()
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.interpolation = 'CONSTANT'
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
        for i, (position, factor) in enumerate([(0, .43), (.30, .76), (.72, 1.08)]):
            e = ramp.color_ramp.elements[0] if i == 0 else ramp.color_ramp.elements.new(position)
            e.position = position
            e.color = (*(min(1, c * factor) for c in rgb), 1)
        emission = nodes.new('ShaderNodeEmission')
        links.new(geometry.outputs['Normal'], light_dot.inputs[0])
        links.new(light_dot.outputs['Value'], ramp.inputs[0])
        links.new(ramp.outputs[0], emission.inputs[0])
        links.new(emission.outputs[0], nodes['Material Output'].inputs[0])
    materials[key] = m
    return m


def start(name, pos):
    global current, root
    current = bpy.data.collections.new(f'{style} - {name}')
    gallery.children.link(current)
    root = bpy.data.objects.new(f'ArtReview_{style}_{name}_ROOT', None)
    current.objects.link(root)
    root.location = pos
    root['review_only'] = True
    root['style'] = style
    root['asset_type'] = name
    return root


def mesh(name, verts, faces, mat, bevel=0, smooth=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(data)
    bm.free()
    obj = bpy.data.objects.new(f'{root.name[:-5]} {name}', data)
    current.objects.link(obj)
    obj.parent = root
    data.materials.append(mat)
    for p in data.polygons:
        p.use_smooth = smooth
    if bevel:
        mod = obj.modifiers.new('Rounded edges', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
        mod = obj.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
        mod.keep_sharp = True
    return obj


def box(name, pos, dims, mat, bevel=.06, tilt=0):
    verts = [(x * dims[0] / 2, y * dims[1] / 2, z * dims[2] / 2)
             for x, y, z in [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
                             (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)]]
    obj = mesh(name, verts, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                            (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat, bevel)
    obj.location = pos
    obj.rotation_euler.y = tilt
    return obj


def blob(name, pos, dims, mat, detail=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=detail, radius=1)
    obj = bpy.context.object
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    current.objects.link(obj)
    obj.parent = root
    obj.name = f'{root.name[:-5]} {name}'
    obj.location = pos
    for v in obj.data.vertices:
        v.co = Vector((v.co.x * dims[0], v.co.y * dims[1], v.co.z * dims[2]))
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def branch(name, a, b, r1, r2, mat):
    delta = Vector(b) - Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r1, radius2=r2, depth=delta.length)
    obj = bpy.context.object
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    current.objects.link(obj)
    obj.parent = root
    obj.name = f'{root.name[:-5]} {name}'
    obj.location = (Vector(a) + Vector(b)) / 2
    obj.rotation_euler = delta.to_track_quat('Z', 'Y').to_euler()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def cottage():
    trim = material('Vanilla trim', 'FFF0D4')
    wall = material('Peach plaster', 'EDAD8F')
    roof = material('Berry roof', 'A875A9' if style != 'Cel' else '9874C5')
    accent = material('Mint wood', '79BCAA')
    glass = material('Blue window', '548A9E', .38)
    glint = material('Window highlight', 'C0EBE7')
    base = material('Foundation', 'CDB9A8')
    gold = material('Brass handle', 'EDBB62')
    box('Foundation', (0, 0, .14), (5.25, 4.65, .28), base, .13)
    wall_height = 2.6 if style == 'Painted' else 2.94
    box('Soft plaster shell', (0, 0, .12 + wall_height / 2), (5, 4.4, wall_height), wall, .23 if style == 'Soft' else .1)
    # Curved eaves and a thick rim change the roof silhouette at street distance.
    xs = [-3.22 + i * 6.44 / 24 for i in range(25)]
    profile = [(x, 3.02 + 1.8 * (1 + math.cos(math.pi * x / 3.22)) / 2) for x in xs]
    if style == 'Cel':
        profile = [(-3.25, 2.96), (-2.65, 3.12), (.18, 5.0), (2.65, 3.12), (3.25, 2.96)]
    if style == 'Painted':
        profile = [(x + .28 * (z - 3), z + .1 * x) for x, z in profile]
    for part, dz, depth, mat in [('Vanilla roof edge', -.10, 5.7, trim), ('Roof', .03, 5.62, roof)]:
        n = len(profile)
        cross = profile + [(x, z - .24) for x, z in reversed(profile)]
        verts = [(x, y, z + dz) for y in [-depth / 2, depth / 2] for x, z in cross]
        nn = 2 * n
        faces = [tuple(reversed(range(nn))), tuple(range(nn, nn * 2))]
        faces += [(i, (i + 1) % nn, (i + 1) % nn + nn, i + nn) for i in range(nn)]
        mesh(part, verts, faces, mat, .065)
    # Follow the underside of the curved roof so the gable cannot poke through it.
    gable = [(x, z) for x, z in profile if abs(x) < 2.6]
    verts = [(x, -2.18, height) for x, z in gable for height in (2.65, z - .24)]
    faces = [(i*2, i*2+2, i*2+3, i*2+1) for i in range(len(gable)-1)]
    mesh('Front gable', verts, faces, wall, smooth=False)
    box('Door surround', (-1.35, -2.24, 1.28), (1.33, .28, 2.34), trim, .23)
    box('Mint door', (-1.35, -2.40, 1.25), (1.08, .12, 2.1), accent, .18)
    box('Door pane', (-1.35, -2.48, 1.76), (.69, .025, .65), glass, .12)
    blob('Round door handle', (-1.0, -2.52, 1.05), (.077, .06, .077), gold)
    box('Doorstep', (-1.35, -2.58, .12), (1.65, .85, .24), base, .11)

    def window(x, y, z, w, h, side=False):
        parts = [box('Window surround', (x, y, z), (w + .26, .24, h + .25), trim, .18),
                 box('Blue pane', (x, y - .14, z), (w, .05, h), glass, .12),
                 box('Mullion', (x, y - .18, z), (.09, .08, h), trim, .035),
                 box('Crossbar', (x, y - .18, z), (w, .08, .09), trim, .035),
                 box('Deep sill', (x, y - .08, z - h / 2 - .12), (w + .45, .44, .16), trim, .065)]
        for xx in [-.25, .25]:
            parts.append(box('Broad glass glint', (x + xx * w, y - .172, z + h * .23),
                             (.1, .014, h * .26), glint, .005, -.35))
        if side:
            for obj in parts:
                ox, oy, oz = obj.location
                obj.location = (-oy, ox, oz)
                obj.rotation_euler.z = math.pi / 2
        elif w > 1:
            for sign in [-1, 1]:
                box('Shutter', (x + sign * (w / 2 + .33), y + .01, z), (.33, .16, h + .08), accent, .09,
                    sign * .05 if style == 'Painted' else 0)
        return parts

    window(.9, -2.23, 1.68, 1.28, 1.26)
    window(0, -2.53, 1.68, 1.16, 1.26, True)
    window(.1 if style == 'Painted' else 0, -2.30, 3.80, .55, .55)
    box('Chimney', (1.65, .9, 4.13), (.64, .70, 1.42), roof, .1, -.1 if style == 'Painted' else 0)
    box('Chimney cap', (1.6, .9, 4.86), (.88, .92, .23), trim, .095)
    box('Chimney opening', (1.6, .9, 4.985), (.45, .48, .025), material('Plum recess', '534456'), .06)


def tree():
    bark = material('Honey bark', '9C6B4F')
    leaf = material('Mint foliage', '86BB79' if style != 'Cel' else '71B889')
    light = material('Sunlit foliage', 'B2D58F' if style != 'Cel' else '97D193')
    branch('Curving trunk lower', (0, 0, .04), (-.16, .03, 1.3), .28, .21, bark)
    branch('Curving trunk upper', (-.16, .03, 1.3), (.18, .04, 2.65), .21, .09, bark)
    for i, (x, y, z, dims) in enumerate([(-.82, .02, 2.8, (1.1, 1.02, 1.06)),
                                        (.86, .1, 2.94, (1.08, .99, 1.05)),
                                        (.08, .1, 3.64, (1.14, 1.04, 1.02)),
                                        (-.03, -.58, 2.95, (.96, .85, .89))]):
        if style == 'Painted':
            x += .18 * (z - 2)
        branch('Branch', (-.13, 0, 1.45), (x, y, z), .12, .04, bark)
        crown = blob('Canopy', (x, y, z), dims, leaf if i % 2 == 0 else light, 4 if style == 'Soft' else 3)
        if style == 'Painted':
            for v in crown.data.vertices:
                v.co *= 1 + .055 * math.sin(v.co.x * 7 + v.co.z * 4)
    for a in [0, 2.1, 4.2]:
        branch('Root flare', (math.cos(a) * .43, math.sin(a) * .43, .045), (0, 0, .55), .08, .16, bark)


def rounded_points(w, d, r, z):
    points = []
    for cx, cy, start in [(w/2-r, d/2-r, 0), (-w/2+r, d/2-r, math.pi/2),
                          (-w/2+r, -d/2+r, math.pi), (w/2-r, -d/2+r, 3*math.pi/2)]:
        for i in range(7):
            a = start + i * math.pi / 12
            points.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
    return points


def tub():
    enamel = material('Cream enamel', 'F9E7D6', .4)
    pink = material('Strawberry badge', 'DA7590')
    cream = material('Strawberry ice cream', 'F3A6BA', .67)
    profiles = [(.31, .24, .045, 0), (.386, .316, .055, .196), (.39, .32, .056, .211),
                (.385, .315, .056, .221), (.345, .275, .043, .221), (.335, .265, .041, .201),
                (.286, .216, .035, .018)]
    verts = [p for profile in profiles for p in rounded_points(*profile)]
    n = 28
    faces = [(j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i)
             for j in range(len(profiles)-1) for i in range(n)]
    faces += [tuple(reversed(range(n))), tuple(range((len(profiles)-1)*n, len(profiles)*n))]
    mesh('Rounded reusable tub', verts, faces, enamel, .0018, smooth=style != 'Cel')
    verts = [(0, 0, .208)]
    rings, steps = 12, 48
    for j in range(1, rings + 1):
        rr = j / rings
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x = math.copysign(abs(math.cos(a)) ** .43, math.cos(a)) * .164 * rr
            y = math.copysign(abs(math.sin(a)) ** .43, math.sin(a)) * .129 * rr
            wave = .006 * math.sin(y * 110 + math.sin(x * 25) * .8)
            z = .204 + .012 * (1 - rr ** 2) + wave * (1 - rr ** 5)
            verts.append((x, y, z))
    faces = [(0, 1+k, 1+(k+1)%steps) for k in range(steps)]
    for j in range(rings - 1):
        for k in range(steps):
            a, b = 1+j*steps+k, 1+j*steps+(k+1)%steps
            faces.append((a, a+steps, b+steps, b))
    fill = mesh('Ice cream fill', verts, faces, cream)
    fill['fill_fraction'] = 1.0
    fill['separate_mesh_for_later_depletion'] = True
    box('Flavor badge', (0, -.148, .12), (.17, .018, .057), pink, .016)
    seed = material('Fruit accent', 'BC506E')
    for x, y in [(-.095, .01), (.07, .065), (.034, -.085), (-.058, -.083), (.105, -.034)]:
        blob('Strawberry piece', (x, y, .217), (.007, .005, .003), seed, 1)
    for x in [-.042, 0, .042]:
        box('Badge mark', (x, -.159, .122), (.021, .002, .01), enamel, .003)


assets = []
source_names = ['House_Cottage_ROOT', 'Tree_Roundmaple_ROOT', 'Tub_1_1_Strawberry']
for column, style_name in enumerate(['Original', 'Soft', 'Cel', 'Painted']):
    style = style_name
    for row, (kind, builder, source_name) in enumerate(zip(['Cottage', 'Tree', 'Tub'], [cottage, tree, tub], source_names)):
        pos = (48 + column * 10, row * -11, 0)
        r = start(kind, pos)
        if style == 'Original':
            source = bpy.data.objects[source_name]
            copies = {source: r}
            for obj in source.children_recursive:
                copy = obj.copy()
                copy.name = f'ArtReview_Original {obj.name}'
                current.objects.link(copy)
                copies[obj] = copy
            for obj, copy in copies.items():
                if obj != source:
                    copy.parent = copies[obj.parent]
            if kind == 'Tub':
                r.location.z = .21
        else:
            builder()
        assets.append((style, kind, current, r))

# Colored silhouette shells keep the cel study readable without outlining every face.
style = 'Cel'
ink = material('Plum outline', '493A57')
ink.use_backface_culling = True
ink.use_backface_culling_shadow = True
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
for asset_style, kind, col, asset_root in assets:
    if asset_style != 'Cel':
        continue
    for obj in list(col.objects):
        if obj.type != 'MESH' or len(obj.data.polygons) < 5:
            continue
        data = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        width = .00085 if kind == 'Tub' else .017
        for vertex in data.vertices:
            vertex.co += vertex.normal * width
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
        bm.to_mesh(data)
        bm.free()
        data.materials.clear()
        data.materials.append(ink)
        for p in data.polygons:
            p.material_index = 0
        outline = bpy.data.objects.new(obj.name + ' outline', data)
        col.objects.link(outline)
        outline.parent = asset_root
        outline.matrix_basis = obj.matrix_basis.copy()
        outline['review_outline'] = True

# Only the review scene owns this stage and its camera.
stage = bpy.data.collections.new('Art review stage')
review.collection.children.link(stage)
data = bpy.data.cameras.new('Art review camera')
camera = bpy.data.objects.new('Art review camera', data)
stage.objects.link(camera)
review.camera = camera
camera.data.type = 'ORTHO'
lights = []
for name, pos, energy, size in [('Key', (-5, -7, 10), 1400, 5), ('Fill', (6, -3, 6), 650, 6)]:
    data = bpy.data.lights.new('Art review ' + name, 'AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    obj = bpy.data.objects.new(data.name, data)
    stage.objects.link(obj)
    lights.append((obj, Vector(pos), energy, size))
floor_data = bpy.data.meshes.new('Art review floor')
floor_data.from_pydata([(-200, -200, -.015), (200, -200, -.015), (200, 200, -.015), (-200, 200, -.015)], [], [(0, 1, 2, 3)])
floor = bpy.data.objects.new('Art review floor', floor_data)
stage.objects.link(floor)
style = 'Studio'
floor_data.materials.append(material('Warm background', 'EAE4D9'))


def frame(kind, asset_root):
    origin = Vector((asset_root.location.x, asset_root.location.y, 0))
    scale = .082 if kind == 'Tub' else 1
    target = origin + Vector((0, 0, .125 if kind == 'Tub' else 2.3))
    camera.location = target + Vector((7, -12, 7.8)) * scale
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.data.ortho_scale = .61 if kind == 'Tub' else 8.9 if kind == 'Cottage' else 6.3
    camera.data.clip_start = .001
    for obj, offset, energy, size in lights:
        obj.location = origin + offset * scale
        obj.data.energy = energy * scale ** 2
        obj.data.size = size * scale
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()


report = {'original_object_count': len(original_names), 'variants': []}
for style_name, kind, col, r in assets:
    for other_style, other_kind, other, other_root in assets:
        other.hide_render = other != col
    frame(kind, r)
    # All views use the same renderer, framing, and studio lighting.
    review.render.engine = 'BLENDER_EEVEE'
    review.eevee.taa_render_samples = 128
    review.render.filepath = str(OUTPUT / f'{style_name}_{kind}.png')
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    tris = 0
    for obj in col.all_objects:
        if obj.type == 'MESH':
            evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
            evaluated.data.calc_loop_triangles()
            tris += len(evaluated.data.loop_triangles)
    report['variants'].append({'style': style_name, 'asset': kind, 'triangles': tris})

for _, _, col, _ in assets:
    col.hide_render = False
camera.location = (65, -50, 40)
camera.rotation_euler = (Vector((63, -9, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.ortho_scale = 46
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.overlay.show_overlays = False
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[name]) == before[name] for name in original_names), 'Original asset changed'
assert len([a for a in assets if a[0] != 'Original']) == 9
report['original_objects_preserved'] = True
report['shading_note'] = 'Blender EEVEE studies. Custom shading is not yet installed in Unity.'
(OUTPUT / 'audit.json').write_text(json.dumps(report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / 'Art/Source/ArtStyleReview_Candidate.blend'))
print('ART_REVIEW_COMPLETE ' + json.dumps(report))
