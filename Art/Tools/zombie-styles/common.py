"""Shared toolkit for the v2 art style mockups. Style modules import this."""
import bpy, bmesh, math, random, sys
from mathutils import Vector, Matrix, Euler
sys.path.insert(0, "/tmp/artstyle/v2")
import v1_styles as v1

hexc = v1.hexc            # '#rrggbb' -> linear RGBA tuple
hex_scale = v1.hex_scale  # darken/lighten a hex string
star_mesh = v1.star_mesh  # (name, points, r_out, r_in) -> flat star mesh in the XZ plane

SHADERS = {
    'candy': v1.candy_material,       # soft principled, light coat
    'facet': v1.facet_material,       # rough matte principled
    'ink': v1.ink_material,           # 3-band toon ramp (emission)
    'vinyl': v1.vinyl_material,       # glossy plastic
    'halftone': v1.halftone_material, # screen-space halftone dots (emission)
    'gummy': v1.gummy_material,       # translucent candy (transmission + SSS)
    'clay': v1.clay_material,         # matte clay with fingerprint bump
    'ps1': v1.ps1_material,           # pixel-noise matte
    'paper': v1.paper_material,       # matte paper fiber bump
}


class Kit:
    """Builds objects into one collection. All helpers return the created object."""

    def __init__(self, col, shader, seed=1):
        self.col = col
        self.shader = shader
        self.rand = random.Random(seed)
        self._mats = {}

    # ---------------------------------------------------------- materials
    def mat(self, name, hex_color, shader=None):
        """Cached material. shader defaults to the style's shader. Custom node materials: build your own
        bpy.data.materials entry and pass it anywhere a material is expected."""
        shader = shader or self.shader
        key = (name, hex_color, shader)
        if key not in self._mats:
            m = bpy.data.materials.new(f"ZD2 {name}")
            SHADERS[shader](m, hexc(hex_color))
            self._mats[key] = m
        return self._mats[key]

    # ---------------------------------------------------------- objects
    def link(self, name, data, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        ob = bpy.data.objects.new(name, data)
        self.col.objects.link(ob)
        ob.parent = parent
        ob.location = loc
        ob.rotation_euler = [math.radians(a) for a in rot]
        ob.scale = scale
        return ob

    def empty(self, name, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1)):
        """Pivot. Children use parent-local coordinates (matrix_parent_inverse stays identity)."""
        ob = self.link(name, None, parent, loc, rot, scale)
        ob.empty_display_size = 0.06
        return ob

    def mesh_from_bmesh(self, name, bm, mat, parent=None, loc=(0, 0, 0), rot=(0, 0, 0), smooth=True):
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        mats = mat if isinstance(mat, (list, tuple)) else [mat]
        for m in mats:
            me.materials.append(m)
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        return self.link(name, me, parent, loc, rot)

    def prim(self, name, kind, size, mat, parent=None, offset=(0, 0, 0), rot=(0, 0, 0), segments=16, rings=10,
             taper=1.0, smooth=True, bevel=0.0, bevel_segments=3):
        """kind: 'sphere' (size = radii), 'box' (size = dimensions), 'cyl'/'cone' (size = (rx, ry, length), along Z,
        taper = top radius factor), 'ico' (size = radii, segments = subdivisions). Geometry is baked
        (scaled/rotated/offset) into the mesh; the object sits at the parent pivot."""
        bm = bmesh.new()
        if kind == 'sphere':
            bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=1)
        elif kind == 'ico':
            bmesh.ops.create_icosphere(bm, subdivisions=segments, radius=1)
        elif kind == 'box':
            bmesh.ops.create_cube(bm, size=1)
        else:
            bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=1, radius2=taper, depth=1)
        bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
        bmesh.ops.rotate(bm, matrix=Euler([math.radians(a) for a in rot]).to_matrix(), verts=bm.verts)
        bmesh.ops.translate(bm, vec=Vector(offset), verts=bm.verts)
        ob = self.mesh_from_bmesh(name, bm, mat, parent, smooth=smooth)
        if bevel:
            mod = ob.modifiers.new("Bevel", 'BEVEL')
            mod.width = bevel
            mod.segments = bevel_segments
            mod.limit_method = 'ANGLE'
            mod.harden_normals = smooth
        return ob

    def skin(self, name, points, edges, radii, mat, parent=None, subsurf=2, smooth=True, root=0):
        """Continuous organic body from a stick skeleton (Skin modifier + Subdivision).
        points: list of (x,y,z) in parent space; edges: list of (i, j); radii: per point (rx, ry) or float.
        Great for limbs/torsos that flow into each other instead of stacked primitives."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([Vector(p) for p in points], edges, [])
        me.materials.append(mat)
        ob = self.link(name, me, parent)
        mod = ob.modifiers.new("Skin", 'SKIN')
        mod.use_smooth_shade = smooth
        sv = me.skin_vertices[0].data
        for i, r in enumerate(radii):
            sv[i].radius = (r, r) if isinstance(r, (int, float)) else r
            sv[i].use_root = i == root
        if subsurf:
            sub = ob.modifiers.new("Subdivision", 'SUBSURF')
            sub.levels = sub.render_levels = subsurf
        return ob

    def cage(self, name, verts, faces, mat, parent=None, subsurf=2, smooth=True, creases=None):
        """Hand-placed low-poly cage (box modeling). With subsurf=0 and smooth=False it is a faceted low-poly mesh.
        creases: optional list of (edge vertex pair, crease 0..1)."""
        me = bpy.data.meshes.new(name)
        me.from_pydata([Vector(v) for v in verts], [], faces)
        me.validate()
        me.materials.append(mat)
        if smooth:
            me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
        ob = self.link(name, me, parent)
        if subsurf:
            sub = ob.modifiers.new("Subdivision", 'SUBSURF')
            sub.levels = sub.render_levels = subsurf
        return ob

    def mirror(self, ob, axis_x=True):
        """Mirror a half-modeled object across its local X axis (model the +X side, get the -X side)."""
        mod = ob.modifiers.new("Mirror", 'MIRROR')
        mod.use_axis = (axis_x, False, False)
        mod.use_clip = True
        ob.modifiers.move(len(ob.modifiers) - 1, 0)
        return ob

    def outline(self, ob, width, color="#1a1424"):
        """Inverted-hull outline (works in EEVEE). Adds the outline material as an extra slot."""
        ob.data.materials.append(v1.outline_material(color))
        sol = ob.modifiers.new("Outline", 'SOLIDIFY')
        sol.thickness = width
        sol.offset = 1
        sol.use_flip_normals = True
        sol.use_rim = False
        sol.material_offset = len(ob.data.materials) - 1
        return ob

    def voxels(self, name, cells, size, parent=None, loc=(0, 0, 0)):
        """Hand-authored voxel model. cells: {(i, j, k): material}. Only exposed faces are built, one object per
        material. Voxel (i,j,k) occupies [i,i+1]*size etc. in parent space offset by loc. Returns list of objects."""
        by_mat = {}
        for key, m in cells.items():
            by_mat.setdefault(m, []).append(key)
        out = []
        for m, keys in by_mat.items():
            bm = bmesh.new()
            cache = {}

            def vert(p):
                v = cache.get(p)
                if v is None:
                    v = bm.verts.new(Vector(p) * size)
                    cache[p] = v
                return v
            for key in keys:
                for a in range(3):
                    u, w = (a + 1) % 3, (a + 2) % 3
                    for sgn in (1, -1):
                        n = list(key); n[a] += sgn
                        if tuple(n) in cells:
                            continue
                        c = list(key)
                        if sgn > 0:
                            c[a] += 1
                        cu = list(c); cu[u] += 1
                        cuw = list(cu); cuw[w] += 1
                        cw = list(c); cw[w] += 1
                        quad = [tuple(c), tuple(cu), tuple(cuw), tuple(cw)]
                        if sgn < 0:
                            quad.reverse()
                        bm.faces.new([vert(p) for p in quad])
            out.append(self.mesh_from_bmesh(f"{name} {m.name}", bm, m, parent, loc, smooth=False))
        return out
