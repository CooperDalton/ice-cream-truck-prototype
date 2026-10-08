"""Shared material builders and helpers for the zombie demo art style mockups."""
import bpy, bmesh, math


def hexc(h):
    h = h.lstrip('#')

    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(lin(int(h[i:i + 2], 16) / 255) for i in (0, 2, 4)) + (1,)


def hex_scale(h, f):
    h = h.lstrip('#')
    return '#' + ''.join('%02x' % min(255, int(int(h[i:i + 2], 16) * f)) for i in (0, 2, 4))


def scale_color(c, f):
    return tuple(min(1, x * f) for x in c[:3]) + (1,)


def node_tree(m):
    if hasattr(m, "use_nodes"):
        try:
            m.use_nodes = True
        except Exception:
            pass
    nt = m.node_tree
    nt.nodes.clear()
    return nt


def candy_material(m, color):
    nt = node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = 0.42
    p.inputs["Coat Weight"].default_value = 0.25
    p.inputs["Coat Roughness"].default_value = 0.2
    p.inputs["Subsurface Weight"].default_value = 0.08
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = color


def facet_material(m, color):
    nt = node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = color
    p.inputs["Roughness"].default_value = 0.88
    p.inputs["Specular IOR Level"].default_value = 0.2
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = color


def ink_material(m, color):
    nt = node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    diffuse = nt.nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    to_rgb = nt.nodes.new("ShaderNodeShaderToRGB")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    els[0].position = 0.0
    els[0].color = tuple(x * 0.42 for x in color[:3]) + (1,)
    els[1].position = 0.32
    els[1].color = color
    hi = els.new(0.92)
    hi.color = tuple(min(1, x * 1.25 + 0.06) for x in color[:3]) + (1,)
    emit = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(diffuse.outputs[0], to_rgb.inputs[0])
    nt.links.new(to_rgb.outputs[0], ramp.inputs[0])
    nt.links.new(ramp.outputs[0], emit.inputs[0])
    nt.links.new(emit.outputs[0], out.inputs[0])
    m.diffuse_color = color


def outline_material(color="#1a1424"):
    m = bpy.data.materials.get("ZD outline " + color)
    if m:
        return m
    m = bpy.data.materials.new("ZD outline " + color)
    nt = node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    emit.inputs[0].default_value = hexc(color)
    nt.links.new(emit.outputs[0], out.inputs[0])
    m.use_backface_culling = True
    m.diffuse_color = hexc(color)
    return m


def principled(m, color, **inputs):
    nt = node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    p.inputs["Base Color"].default_value = color
    for k, v in inputs.items():
        p.inputs[k].default_value = v
    nt.links.new(p.outputs[0], out.inputs[0])
    m.diffuse_color = color
    return nt, p


def bump_chain(nt, p, layers):
    coord = nt.nodes.new("ShaderNodeTexCoord")
    normal = None
    for kind, scale, strength, extra in layers:
        tex = nt.nodes.new(kind)
        tex.inputs["Scale"].default_value = scale
        for k, v in extra.items():
            if isinstance(v, str):
                setattr(tex, k, v)
            else:
                tex.inputs[k].default_value = v
        nt.links.new(coord.outputs["Object"], tex.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = strength
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        if normal:
            nt.links.new(normal, bump.inputs["Normal"])
        normal = bump.outputs["Normal"]
    nt.links.new(normal, p.inputs["Normal"])


def vinyl_material(m, color):
    principled(m, color, **{"Roughness": 0.2, "Coat Weight": 0.8, "Coat Roughness": 0.04, "Specular IOR Level": 0.6})


def gummy_material(m, color):
    principled(m, color, **{"Roughness": 0.18, "Transmission Weight": 0.65, "Subsurface Weight": 0.5,
                            "Subsurface Radius": (1.0, 0.4, 0.25), "Subsurface Scale": 0.08, "Coat Weight": 1.0,
                            "Coat Roughness": 0.03, "Emission Color": color, "Emission Strength": 0.18, "IOR": 1.35})
    if hasattr(m, "use_raytrace_refraction"):
        m.use_raytrace_refraction = True


def clay_material(m, color):
    nt, p = principled(m, color, **{"Roughness": 0.72, "Sheen Weight": 0.3, "Subsurface Weight": 0.08,
                                    "Specular IOR Level": 0.3})
    bump_chain(nt, p, [("ShaderNodeTexNoise", 30, 0.35, {"Detail": 6.0}),
                       ("ShaderNodeTexWave", 5, 0.25, {"wave_type": 'RINGS', "Distortion": 6.0})])


def paper_material(m, color):
    nt, p = principled(m, color, **{"Roughness": 1.0, "Specular IOR Level": 0.05})
    bump_chain(nt, p, [("ShaderNodeTexNoise", 140, 0.18, {"Detail": 8.0})])


def ps1_material(m, color):
    nt, p = principled(m, color, **{"Roughness": 1.0, "Specular IOR Level": 0.1})
    coord = nt.nodes.new("ShaderNodeTexCoord")
    snap = nt.nodes.new("ShaderNodeVectorMath")
    snap.operation = 'SNAP'
    snap.inputs[1].default_value = (0.035, 0.035, 0.035)
    noise = nt.nodes.new("ShaderNodeTexWhiteNoise")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs[6].default_value = color
    mix.inputs[7].default_value = tuple(x * 0.72 for x in color[:3]) + (1,)
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 0.7
    nt.links.new(coord.outputs["Object"], snap.inputs[0])
    nt.links.new(snap.outputs[0], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Value"], mul.inputs[0])
    nt.links.new(mul.outputs[0], mix.inputs[0])
    nt.links.new(mix.outputs[2], p.inputs["Base Color"])


def halftone_material(m, color):
    nt = node_tree(m)
    N = nt.nodes.new
    L = nt.links.new
    out = N("ShaderNodeOutputMaterial")
    diffuse = N("ShaderNodeBsdfDiffuse")
    to_rgb = N("ShaderNodeShaderToRGB")
    bw = N("ShaderNodeRGBToBW")
    L(diffuse.outputs[0], to_rgb.inputs[0])
    L(to_rgb.outputs[0], bw.inputs[0])
    coord = N("ShaderNodeTexCoord")
    sep = N("ShaderNodeSeparateXYZ")
    L(coord.outputs["Camera"], sep.inputs[0])

    def math_node(op, a, b=None, clamp=False, c=None):
        node = N("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                node.inputs[i].default_value = v
            else:
                L(v, node.inputs[i])
        return node.outputs[0]
    depth = math_node('MULTIPLY', sep.outputs[2], -1.0)
    sx = math_node('DIVIDE', sep.outputs[0], depth)
    sy = math_node('DIVIDE', sep.outputs[1], depth)
    freq = 150 * 0.7071
    u = math_node('MULTIPLY', math_node('ADD', sx, sy), freq)
    v = math_node('MULTIPLY', math_node('SUBTRACT', sx, sy), freq)
    cu = math_node('SUBTRACT', math_node('FRACT', u), 0.5)
    cv = math_node('SUBTRACT', math_node('FRACT', v), 0.5)
    comb = N("ShaderNodeCombineXYZ")
    L(cu, comb.inputs[0])
    L(cv, comb.inputs[1])
    length = N("ShaderNodeVectorMath")
    length.operation = 'LENGTH'
    L(comb.outputs[0], length.inputs[0])
    radius = math_node('MULTIPLY_ADD', bw.outputs[0], -0.8, clamp=True, c=0.8)
    dot = math_node('LESS_THAN', length.outputs["Value"], radius)
    mix = N("ShaderNodeMix")
    mix.data_type = 'RGBA'
    paper = tuple(c * 0.9 + w * 0.1 for c, w in zip(color[:3], hexc("#efe3c8")[:3])) + (1,)
    mix.inputs[6].default_value = paper
    mix.inputs[7].default_value = tuple(x * 0.38 for x in color[:3]) + (1,)
    L(dot, mix.inputs[0])
    emit = N("ShaderNodeEmission")
    L(mix.outputs[2], emit.inputs[0])
    L(emit.outputs[0], out.inputs[0])
    m.diffuse_color = color


def star_mesh(name, points, r_out, r_in):
    bm = bmesh.new()
    c = bm.verts.new((0, 0, 0))
    ring = []
    for i in range(points * 2):
        a = math.pi * i / points
        r = r_out if i % 2 == 0 else r_in
        ring.append(bm.verts.new((math.cos(a) * r * (0.85 + 0.3 * ((i * 7) % 5) / 4), 0, math.sin(a) * r)))
    for i in range(len(ring)):
        bm.faces.new((c, ring[i], ring[(i + 1) % len(ring)]))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me
