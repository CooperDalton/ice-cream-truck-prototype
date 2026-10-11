"""Scenery batch (style H): extra buildings, props and nature for the land around the road, the 20 x 20 m scenery
blocks the game drops into the empty grid cells beside the road, and extra roadside dressing for the plain road chunks.

Props follow the usual rules: root at ground level, front facing -Y, moving parts on pivots.
Blocks: origin at the cell center on the ground, ground slab from z = -0.25 up to z = 0.15 like the chunk roadside,
the road-facing edge at y = -10 (local -Y, which becomes Unity forward, points at the road).
Dressing sets use the road chunk's own coordinates (see h_road) and only add props outside the asphalt.
Blocks and dressing sets are baked into one mesh each (they never move and need no sockets)."""
from style_H import *
import h_road as road
import h_stops as stops
from h_road import MB, rect, tm, place, SIDE, BOT, HALF
from h_stops import txt, txt_c, prism, slab, face_uv, fence_run

SPACING = 28

STONE, STONE_D = "#b3a6d9", "#8f82bd"
DEAD_BARK = "#6e5a7a"
CORN_YEL = "#ffd84a"


# ---------------------------------------------------------------- shared materials and helpers
def stone(kit):
    return tm(kit, "scenery stone", lambda: tex_stone(kit.rand), 0.3, 'REPEAT')


def wood(kit):
    return tm(kit, "scenery wood", lambda: stops.tex_wood(kit.rand), 0.3, 'REPEAT')


def tex_stone(rand):
    c = Canvas(16, 16, STONE)
    c.speckle(rand, [STONE_D, "#c4b8e6", "#a194cc"], 70)
    return c


def tex_rock(rand):
    c = Canvas(16, 16, "#8a82b0")
    c.speckle(rand, ["#7a72a0", "#9d96c4", "#6c6494", "#38b46c"], 80)
    return c


def tex_soil(rand):
    c = Canvas(16, 16, "#5a3a4c")
    c.speckle(rand, ["#6b4a5a", "#4a2c40", "#7d5a6a"], 90)
    return c


def bake(kit, root, p):
    """Join every mesh below root into '<p> mesh' (a direct child of root) and drop everything else below root."""
    bpy.context.view_layer.update()
    below = list(root.children_recursive)
    meshes = [o for o in below if o.type == 'MESH']
    me = bpy.data.meshes.new(f"{p} mesh")
    me.uv_layers.new(name="UVMap")   # without it the joined UVs do not become the render UV map
    target = kit.link(f"{p} mesh", me, root)
    with bpy.context.temp_override(active_object=target, selected_editable_objects=[target] + meshes):
        bpy.ops.object.join()
    for o in root.children_recursive:
        if o is not target:
            bpy.data.objects.remove(o)
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get("material_index", idx)
    used = sorted(set(idx))
    mats = [me.materials[i] for i in used]
    me.materials.clear()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", [used.index(i) for i in idx])
    return target


# ---------------------------------------------------------------- small props
def bench(kit, root, p):
    w = solid(kit, "bench wood", "#e8a862", shade="#c47f3a")
    iron = solid(kit, "bench iron", PINK, shade="#d93a85")
    for sx in (1, -1):
        x = sx * 0.78
        tbox(kit, f"{p} leg front {sx}", (x, -0.2, 0.22), (0.07, 0.07, 0.44), iron, root)
        tbox(kit, f"{p} leg back {sx}", (x, 0.2, 0.45), (0.07, 0.07, 0.9), iron, root, rot=(-8, 0, 0))
        tbox(kit, f"{p} arm {sx}", (x, -0.04, 0.64), (0.08, 0.5, 0.06), iron, root)
        tbox(kit, f"{p} seat rail {sx}", (x, 0.0, 0.42), (0.07, 0.52, 0.05), iron, root)
    for i in range(3):
        tbox(kit, f"{p} slat {i}", (0, -0.18 + i * 0.14, 0.47), (1.8, 0.11, 0.04), w, root)
    for i in range(2):
        tbox(kit, f"{p} back slat {i}", (0, 0.22 + i * 0.025, 0.66 + i * 0.17), (1.8, 0.04, 0.12), w, root, rot=(-8, 0, 0))


def picnic_table(kit, root, p):
    w = solid(kit, "picnic wood", "#ff8fc8", shade="#e870a8")
    leg = solid(kit, "picnic legs", "#c75a9a", shade="#a8487e")
    for i in range(4):
        tbox(kit, f"{p} top {i}", (0, -0.33 + i * 0.22, 0.76), (1.9, 0.2, 0.05), w, root)
    for sy in (1, -1):
        for i in range(2):
            tbox(kit, f"{p} seat {sy} {i}", (0, sy * (0.62 + i * 0.13), 0.45), (1.9, 0.12, 0.045), w, root)
    for sx in (1, -1):
        for sy in (1, -1):
            tbox(kit, f"{p} leg {sx} {sy}", (sx * 0.7, sy * 0.36, 0.38), (0.08, 0.08, 0.86), leg, root, rot=(sy * -38, 0, 0))
        tbox(kit, f"{p} brace {sx}", (sx * 0.7, 0, 0.42), (0.08, 1.6, 0.06), leg, root)


def tex_booth():
    c = Canvas(32, 64, PINK)
    c.rect(4, 5, 27, 49, GLASS)
    for x in (15, 16):
        c.rect(x, 5, x, 49, PINK)
    for y in (20, 35):
        c.rect(4, y, 27, y, PINK)
    for i in range(6):
        c.set(7 + i, 44 - i, "#6f8cff"); c.set(19 + i, 30 - i, "#6f8cff")
    c.rect(2, 52, 29, 61, WHITE)
    txt_c(c, "PHONE", 16, 59, PINK)
    c.rect(0, 0, 31, 1, "#d93a85")
    return c


def phone_booth(kit, root, p):
    t = tm(kit, "phone booth", tex_booth)
    pink = solid(kit, "booth pink", PINK)
    tbox(kit, f"{p} base", (0, 0, 0.05), (1.0, 1.0, 0.1), solid(kit, "booth base", "#9a8fc8"), root)
    tbox(kit, f"{p} body", (0, 0, 1.2), (0.9, 0.9, 2.2), t, root, uv={'all': (0, 0, 1, 1), 'pz': (0, 0, 0.03, 0.03),
                                                                            'nz': (0, 0, 0.03, 0.03)})
    tbox(kit, f"{p} roof", (0, 0, 2.36), (1.02, 1.02, 0.12), pink, root, taper=(0.8, 0.8))
    tbox(kit, f"{p} lamp", (0, 0, 2.5), (0.3, 0.3, 0.16), solid(kit, "booth lamp", "#fff1a0", 1.6), root)
    tbox(kit, f"{p} phone", (0, 0.36, 1.35), (0.24, 0.12, 0.34), solid(kit, "phone steel", STEEL), root)
    tube(kit, f"{p} cord", [(0.08, 0.3, 1.25), (0.2, 0.0, 0.9), (0.15, -0.2, 0.6)], 0.015, solid(kit, "cord", INK, 0.1), root,
         sides=4, front=(0, 0, 1))
    tbox(kit, f"{p} receiver", (0.15, -0.22, 0.56), (0.08, 0.22, 0.06), solid(kit, "receiver", INK, 0.1), root, rot=(0, 0, 25))


def tex_dumpster(rand):
    c = Canvas(32, 16, BLUE)
    c.speckle(rand, ["#2470d8", "#4a9aff"], 40)
    for _ in range(5):
        disc(c, rand.randrange(32), rand.randrange(2, 14), 1, "#c96f3a")
    txt_c(c, "TRASH", 16, 11, WHITE)
    c.rect(0, 0, 31, 1, "#1d5ab0")
    for f in range(4):
        c.rect(24 + f, 3, 24 + f, 5 + f % 2, ZG)
    c.rect(24, 1, 27, 2, ZG)
    return c


def dumpster(kit, root, p):
    R = kit.rand
    t = tm(kit, "dumpster", lambda: tex_dumpster(R))
    blue = solid(kit, "dumpster blue", BLUE, shade="#2470d8")
    lid_m = solid(kit, "dumpster lid", "#3c3fb8", shade="#2c2f98")
    dark = solid(kit, "dumpster dark", INK, 0.1)
    tbox(kit, f"{p} body", (0, 0, 0.68), (1.9, 1.15, 1.0), t, root,
         uv={'all': (0.4, 0.3, 0.45, 0.35), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)}, taper=(1.04, 1.08))
    tbox(kit, f"{p} rim", (0, 0, 1.2), (2.0, 1.27, 0.06), blue, root)
    for sx in (1, -1):
        tbox(kit, f"{p} pocket {sx}", (sx * 1.0, 0, 0.75), (0.1, 0.5, 0.18), blue, root)
        for sy in (1, -1):
            tbox(kit, f"{p} caster {sx} {sy}", (sx * 0.8, sy * 0.45, 0.1), (0.12, 0.12, 0.2), dark, root)
    for i, (x, ang) in enumerate(((-0.48, 0), (0.48, 112))):
        lid = kit.empty(f"{p} lid {i}", root, (x, 0.63, 1.23), (ang, 0, 0))
        tbox(kit, f"{p} lid {i}", (0, -0.63, 0.03), (0.94, 1.26, 0.05), lid_m, lid)
    bags = [solid(kit, "bag " + c, c, 0.25) for c in ("#3b2a63", "#2a1f4f", "#4a3a7a")]
    for i, (x, y, z, r) in enumerate(((0.3, -0.15, 1.25, 0.33), (0.62, 0.2, 1.2, 0.28), (0.1, 0.25, 1.32, 0.25))):
        lowball(kit, f"{p} bag {i}", (x, y, z), (r, r * 0.9, r * 0.8), bags[i], root, smooth=False)
    lowball(kit, f"{p} spilled bag", (-0.6, -0.95, 0.2), (0.32, 0.28, 0.22), bags[0], root, smooth=False)
    tbox(kit, f"{p} pizza box", (-1.05, -0.7, 0.03), (0.42, 0.42, 0.05), solid(kit, "cardboard", "#e8b878"), root, rot=(0, 0, 20))


def tire(kit, name, parent, loc, rot=(0, 0, 0)):
    piv = kit.empty(name, parent, loc, rot)
    rubber = solid(kit, "tire rubber", "#463a60", 0.2, shade="#382e50")
    tube(kit, name, [(0, 0, -0.11), (0, 0, 0.11)], 0.36, rubber, piv, sides=10, caps=(False, False))
    for z in (-0.11, 0.11):
        ring_mesh(kit, f"{name} wall {z}", 0.17, 0.37, solid(kit, "tire wall", "#5a4c78", 0.2), piv, (0, 0, z), segs=10)
    return piv


def tire_pile(kit, root, p):
    R = kit.rand
    for i in range(4):
        tire(kit, f"{p} stack {i}", root, (R.uniform(-0.04, 0.04), R.uniform(-0.04, 0.04), 0.11 + i * 0.22), (0, 0, R.uniform(0, 30)))
    tire(kit, f"{p} stack b", root, (0.75, 0.15, 0.11))
    tire(kit, f"{p} stack b2", root, (0.78, 0.12, 0.33), (6, 4, 0))
    tire(kit, f"{p} leaning", root, (-0.62, -0.3, 0.34), (80, 0, 30))
    tire(kit, f"{p} rolled", root, (0.5, -0.85, 0.36), (90, 0, -60))


def tex_drum(rand, base):
    c = Canvas(32, 16, base)
    c.speckle(rand, [hex_scale(base, 0.88)], 30)
    for y in (3, 12):
        c.rect(0, y, 31, y, hex_scale(base, 0.7))
    c.rect(12, 6, 19, 9, YEL)
    c.dots([(15, 7), (16, 7), (15, 8), (16, 8)], INK)
    for _ in range(3):
        disc(c, rand.randrange(32), rand.randrange(16), 1, "#c96f3a")
    return c


def drum(kit, name, parent, loc, rot, mat):
    piv = kit.empty(name, parent, loc, rot)
    tube(kit, name, [(0, 0, 0), (0, 0, 0.88)], 0.3, mat, piv, sides=10)
    tube(kit, f"{name} lid", [(0, 0, 0.88), (0, 0, 0.9)], [0.3, 0.27], mat, piv, sides=10)
    return piv


def barrel_stack(kit, root, p):
    R = kit.rand
    mats = [tm(kit, f"drum {c}", lambda c=c: tex_drum(R, c)) for c in (MINT, PURP, ORNG)]
    for i, (x, y) in enumerate(((0, 0), (0.62, 0.05), (0.3, 0.55))):
        drum(kit, f"{p} drum {i}", root, (x, y, 0), (0, 0, R.uniform(0, 360)), mats[i % 3])
    drum(kit, f"{p} drum top", root, (0.3, 0.2, 0.9), (0, 0, 40), mats[2])
    drum(kit, f"{p} drum tipped", root, (-0.55, -0.7, 0.3), (90, 0, 70), mats[1])
    splat(kit, f"{p} goo", (-0.15, -1.15, 0.006), 0.55, solid(kit, "toxic goo", ZG, 0.9, shade="#6fd83a"), root)


# ---------------------------------------------------------------- nature
def dead_tree(kit, root, p):
    R = kit.rand
    bark = solid(kit, "dead bark", DEAD_BARK, shade="#54445e")
    tube(kit, f"{p} trunk", [(0, 0, -0.05), (0.12, 0, 1.4), (0.0, 0.18, 2.9), (0.3, 0.1, 4.3)], [0.32, 0.2, 0.13, 0.04], bark, root,
         sides=6)
    for i, (a, b, c, r) in enumerate((((0.08, 0.06, 1.9), (0.9, -0.2, 2.6), (1.5, -0.1, 3.4), 0.09),
                                      ((0.04, 0.12, 2.4), (-0.7, 0.4, 3.0), (-1.3, 0.2, 3.9), 0.08),
                                      ((0.1, 0.16, 3.1), (0.4, 0.9, 3.7), (0.2, 1.4, 4.4), 0.06),
                                      ((0.12, 0.0, 1.2), (-0.6, -0.5, 1.6), (-1.0, -0.6, 2.2), 0.07),
                                      ((0.2, 0.12, 3.6), (0.8, 0.3, 4.1), (1.0, 0.6, 4.6), 0.05))):
        tube(kit, f"{p} branch {i}", [a, b, c], [r, r * 0.6, 0.015], bark, root, sides=5)
        twig = Vector(c) + Vector((R.uniform(-0.4, 0.4), R.uniform(-0.4, 0.4), 0.45))
        tube(kit, f"{p} twig {i}", [b, twig], [r * 0.5, 0.01], bark, root, sides=4)
    for i in range(3):
        a = i * 2.1
        tube(kit, f"{p} root {i}", [(0, 0, 0.2), (0.6 * math.cos(a), 0.6 * math.sin(a), 0.02)], [0.14, 0.04], bark, root, sides=5)
    crow = kit.empty(f"{p} crow", root, (1.2, -0.15, 3.05), (0, 0, 30))
    blk = solid(kit, "crow", "#241a3a", 0.12)
    lowball(kit, f"{p} crow body", (0, 0, 0.1), (0.07, 0.13, 0.08), blk, crow, smooth=False)
    lowball(kit, f"{p} crow head", (0, -0.12, 0.2), (0.05, 0.05, 0.05), blk, crow, smooth=False)
    tbox(kit, f"{p} crow beak", (0, -0.18, 0.19), (0.02, 0.06, 0.02), solid(kit, "beak", YEL), crow)
    tbox(kit, f"{p} crow eye", (0.035, -0.14, 0.22), (0.015, 0.015, 0.015), solid(kit, "crow eye", RED, 1.5), crow)


def boulders(kit, root, p):
    R = kit.rand
    rock = tm(kit, "rock", lambda: tex_rock(R))
    for i, (x, y, rx, ry, rz) in enumerate(((0, 0, 0.9, 0.75, 0.6), (0.95, 0.3, 0.55, 0.5, 0.42), (-0.6, 0.6, 0.45, 0.4, 0.3),
                                           (0.4, -0.75, 0.3, 0.28, 0.2))):
        ob = lowball(kit, f"{p} rock {i}", (x, y, rz * 0.55), (rx, ry, rz), rock, root, smooth=False)
        ob.rotation_euler = (R.uniform(-0.2, 0.2), R.uniform(-0.2, 0.2), R.uniform(0, 3))


def tall_grass(kit, root, p):
    R = kit.rand
    blades = [solid(kit, "grass blade " + c, c, 0.3) for c in ("#3fcf7a", "#2fae66", "#7ed957")]
    for i in range(12):
        a = R.uniform(0, 2 * math.pi)
        d = R.uniform(0, 0.45)
        h = R.uniform(0.45, 0.85)
        tbox(kit, f"{p} blade {i}", (d * math.cos(a), d * math.sin(a), h / 2), (0.09, 0.012, h), blades[i % 3], root,
             rot=(R.uniform(-18, 18), R.uniform(-18, 18), R.uniform(0, 180)), taper=(0.15, 1))
    for i in range(3):
        a = R.uniform(0, 2 * math.pi)
        x, y, h = 0.3 * math.cos(a), 0.3 * math.sin(a), R.uniform(0.7, 0.95)
        tube(kit, f"{p} stem {i}", [(x, y, 0), (x, y, h)], 0.012, blades[0], root, sides=4)
        tbox(kit, f"{p} flower {i}", (x, y, h), (0.12, 0.12, 0.06), solid(kit, "wild " + str(i), (PINK, YEL, WHITE)[i], 0.6), root,
             rot=(0, 0, 45))


def tex_cob():
    c = Canvas(8, 16, CORN_YEL)
    for y in range(0, 16, 2):
        for x in range(y // 2 % 2, 8, 2):
            c.set(x, y, "#f0b830")
    return c


def corn_patch(kit, root, p):
    """4 x 4 m: four tilled rows of corn along Y."""
    R = kit.rand
    stalk = solid(kit, "corn stalk", "#7ed957", shade="#5cb83a")
    leaf = solid(kit, "corn leaf", "#4fc860", shade="#3fa040")
    cob = tm(kit, "corn cob", tex_cob)
    tassel = solid(kit, "corn tassel", "#ffe58a")
    soil = tm(kit, "tilled soil", lambda: tex_soil(R), 0.2, 'REPEAT')
    for row in range(4):
        x = -1.5 + row
        tbox(kit, f"{p} mound {row}", (x, 0, 0.05), (0.55, 4.0, 0.1), soil, root, taper=(0.6, 1.0),
             uv={'all': (0, 0, 0.5, 4)})
        for k in range(4):
            y = -1.5 + k + R.uniform(-0.2, 0.2)
            h = R.uniform(1.9, 2.5)
            s = kit.empty(f"{p} stalk {row} {k}", root, (x + R.uniform(-0.1, 0.1), y, 0.08),
                          (R.uniform(-5, 5), R.uniform(-5, 5), R.uniform(0, 360)))
            tube(kit, f"{p} stalk {row} {k}", [(0, 0, 0), (0, 0, h)], [0.045, 0.02], stalk, s, sides=4)
            for j, (z, a) in enumerate(((h * 0.35, 0), (h * 0.6, 150))):
                lp = kit.empty(f"{p} leaf piv {row} {k} {j}", s, (0, 0, z), (0, 0, a))
                tbox(kit, f"{p} leaf {row} {k} {j}", (0, -0.34, 0.05), (0.09, 0.7, 0.012), leaf, lp, rot=(-22, 0, 0),
                     taper=(0.3, 1.0))
            tube(kit, f"{p} cob {row} {k}", [(0.04, 0, h * 0.48), (0.13, -0.03, h * 0.48 + 0.28)], [0.055, 0.03], cob, s, sides=5)
            tbox(kit, f"{p} tassel {row} {k}", (0, 0, h + 0.1), (0.12, 0.12, 0.2), tassel, s, taper=(0.2, 0.2))


def split_rail(kit, root, p):
    """3 m segment along X with its post at x = -1.5 (the next segment supplies the post at x = +1.5)."""
    w = solid(kit, "rail wood", "#a87a66", shade="#7a4a4c")
    tbox(kit, f"{p} post", (-1.5, 0, 0.6), (0.14, 0.14, 1.2), w, root)
    tbox(kit, f"{p} post cap", (-1.5, 0, 1.22), (0.16, 0.16, 0.06), solid(kit, "rail cap", WHITE), root)
    for i, (z, dz) in enumerate(((0.45, 0.04), (0.92, -0.05))):
        tbox(kit, f"{p} rail {i}", (0, 0.05, z), (3.1, 0.07, 0.13), w, root, rot=(0, math.degrees(dz / 3.0) * 4, 0))


def scarecrow(kit, root, p):
    w = wood(kit)
    flannel = tm(kit, "flannel", tex_flannel)
    straw = solid(kit, "straw", "#ffd86a", shade="#e0b84a")
    denim = solid(kit, "scarecrow denim", PANTS)
    tbox(kit, f"{p} post", (0, 0.1, 1.2), (0.12, 0.12, 2.4), w, root, uv={'all': (0, 0, 0.1, 1.2)})
    tbox(kit, f"{p} bar", (0, 0.1, 1.78), (1.7, 0.09, 0.09), w, root, uv={'all': (0, 0, 0.85, 0.1)})
    tbox(kit, f"{p} shirt", (0, 0, 1.45), (0.62, 0.3, 0.78), flannel, root, taper=(1.1, 1.0))
    for sx in (1, -1):
        tube(kit, f"{p} sleeve {sx}", [(sx * 0.28, 0.02, 1.72), (sx * 0.62, 0.04, 1.74), (sx * 0.8, 0.04, 1.66)], [0.13, 0.11, 0.1],
             flannel, root, sides=6, front=(0, 0, 1))
        for k in range(3):
            tbox(kit, f"{p} straw hand {sx} {k}", (sx * 0.9, 0.04 + (k - 1) * 0.04, 1.62 - k * 0.04), (0.2, 0.025, 0.025), straw, root,
                 rot=(0, sx * (20 + k * 18), (k - 1) * 20))
        tube(kit, f"{p} leg {sx}", [(sx * 0.14, 0, 1.1), (sx * 0.16, -0.02, 0.62)], [0.11, 0.1], denim, root, sides=6)
        for k in range(3):
            tbox(kit, f"{p} straw foot {sx} {k}", (sx * 0.16 + (k - 1) * 0.03, -0.02, 0.52), (0.025, 0.025, 0.2), straw, root,
                 rot=(0, (k - 1) * 18, 0))
    tbox(kit, f"{p} patch", (0.13, -0.11, 0.85), (0.1, 0.02, 0.1), solid(kit, "patch", YEL), root)
    head = kit.empty(f"{p} head", root, (0, 0.0, 2.08), (0, 8, -6))
    tbox(kit, f"{p} head", (0, 0, 0.0), (0.42, 0.36, 0.42), tm(kit, "sack face", tex_sack_face), head, taper=(0.82, 0.86),
         uv=face_uv('ny', rest=(0, 0, 0.1, 0.1)))
    tbox(kit, f"{p} neck tie", (0, 0, -0.2), (0.26, 0.24, 0.05), solid(kit, "twine", PINK), head)
    tube(kit, f"{p} brim", [(0, 0, 0.18), (0, 0, 0.2)], 0.4, straw, head, sides=10)
    tube(kit, f"{p} crown", [(0, 0, 0.2), (0, 0, 0.42)], [0.2, 0.15], straw, head, sides=8)
    tube(kit, f"{p} band", [(0, 0, 0.22), (0, 0, 0.27)], 0.205, solid(kit, "hat band", PINK), head, sides=8)


def tex_flannel():
    c = Canvas(16, 16, "#ff4f6a")
    for k in (2, 3, 10, 11):
        c.rect(k, 0, k, 15, "#b0103a")
        c.rect(0, k, 15, k, "#b0103a")
    for k in (6, 14):
        c.rect(k, 0, k, 15, YEL)
        c.rect(0, k, 15, k, YEL)
    return c


def tex_sack_face():
    c = Canvas(16, 16, "#e8c88a")
    c.speckle(random.Random(3), ["#d4b070", "#f0d8a0"], 40)
    for d in range(3):   # X eyes
        for cx in (4, 11):
            c.set(cx - 1 + d, 10 - 1 + d, INK); c.set(cx + 1 - d, 10 - 1 + d, INK)
    for x in range(3, 13):  # stitched grin
        c.set(x, 4 + (1 if x in (3, 12) else 0), INK)
        if x % 2:
            c.set(x, 3 + (1 if x in (3, 12) else 0), INK); c.set(x, 5 + (1 if x in (3, 12) else 0), INK)
    c.rect(7, 7, 8, 7, ORNG)
    return c


# ---------------------------------------------------------------- town pieces
def tex_plaque():
    c = Canvas(32, 16, "#ffd36b")
    c.rect(0, 0, 31, 0, "#c99a2a"); c.rect(0, 15, 31, 15, "#c99a2a")
    txt_c(c, "OUR", 16, 13, CHOC)
    txt_c(c, "TOWN", 16, 6, CHOC)
    return c


def cone_statue(kit, root, p):
    st = stone(kit)
    tbox(kit, f"{p} step", (0, 0, 0.12), (2.0, 2.0, 0.24), st, root, uv={'all': (0, 0, 2, 0.5)})
    tbox(kit, f"{p} plinth", (0, 0, 0.8), (1.3, 1.3, 1.12), st, root, uv={'all': (0, 0, 1.3, 1.1)})
    tbox(kit, f"{p} cap", (0, 0, 1.42), (1.5, 1.5, 0.12), st, root, uv={'all': (0, 0, 1.5, 0.2)})
    tbox(kit, f"{p} plaque", (0, -0.66, 0.85), (0.8, 0.03, 0.42), tm(kit, "statue plaque", tex_plaque), root,
         uv=face_uv('ny', rest=(0.5, 0.5, 0.52, 0.52)))
    tube(kit, f"{p} cone", [(0, 0, 1.48), (0, 0, 3.4)], [0.06, 0.78], tm(kit, "waffle", tex_waffle), root, sides=10)
    lowball(kit, f"{p} scoop low", (0, 0, 3.62), (0.86, 0.86, 0.62), solid(kit, "statue pink", PINK), root)
    lowball(kit, f"{p} scoop high", (0.05, 0, 4.25), (0.66, 0.66, 0.5), solid(kit, "statue mint", MINT), root)
    lowball(kit, f"{p} cherry", (0.1, -0.05, 4.82), (0.17, 0.17, 0.17), solid(kit, "cherry", RED, 0.45), root)
    tube(kit, f"{p} stem", [(0.1, -0.05, 4.95), (0.2, 0.0, 5.25)], 0.025, solid(kit, "stem", "#2fae66"), root, sides=4)
    drip = solid(kit, "statue pink", PINK)
    for i in range(7):
        a = i * 2 * math.pi / 7 + 0.3
        ln = 0.18 + 0.2 * ((i * 37) % 5) / 4
        tbox(kit, f"{p} drip {i}", (0.8 * math.cos(a), 0.8 * math.sin(a), 3.33 - ln / 2), (0.14, 0.14, ln), drip, root,
             rot=(0, 0, math.degrees(a)))
    for i in range(14):
        a = i * 2.4
        z = 3.95 + 0.25 * math.sin(i)
        tbox(kit, f"{p} sprinkle {i}", (0.85 * math.cos(a) * 0.9, 0.85 * math.sin(a) * 0.9, z), (0.1, 0.03, 0.03),
             solid(kit, "sprinkle " + str(i % 4), (YEL, BLUE, WHITE, PURP)[i % 4], 0.6), root, rot=(0, 30, math.degrees(a) + 60))


def tex_bus_sign():
    c = Canvas(16, 16, BLUE)
    disc(c, 8, 8, 7, WHITE)
    disc(c, 8, 8, 6, BLUE)
    txt_c(c, "BUS", 8, 10, WHITE)
    return c


def tex_poster(rand):
    c = Canvas(16, 24, "#ffe14a")
    cone_icon(c, 8, 3, 9, PINK)
    txt_c(c, "YUM", 8, 22, PINK)
    for _ in range(10):
        c.set(rand.randrange(16), rand.randrange(16, 24), rand.choice((BLUE, MINT, WHITE)))
    return c


def tex_glass(rand):
    c = Canvas(16, 16, GLASS)
    for i in range(5):
        c.set(3 + i, 12 - i, "#6f8cff"); c.set(9 + i, 9 - i, "#6f8cff")
    x, y = 11, 4
    for _ in range(7):
        c.set(x, y, "#c7d4ff"); x += rand.choice((-1, 0, 1)); y += rand.choice((-1, 1))
    return c


def bus_stop(kit, root, p):
    R = kit.rand
    steel = solid(kit, "shelter steel", "#5b5fc0", shade="#474aa0")
    glass = tm(kit, "shelter glass", lambda: tex_glass(R))
    for sx in (1, -1):
        for sy in (1, -1):
            tube(kit, f"{p} post {sx} {sy}", [(sx * 1.5, sy * 0.65, 0), (sx * 1.5, sy * 0.65, 2.4)], 0.05, steel, root, sides=6)
    tbox(kit, f"{p} roof", (0, 0.05, 2.47), (3.3, 1.65, 0.1), steel, root, rot=(-4, 0, 0))
    tbox(kit, f"{p} roof trim", (0, -0.78, 2.4), (3.3, 0.06, 0.16), solid(kit, "shelter trim", PINK), root)
    tbox(kit, f"{p} back glass", (0, 0.65, 1.3), (2.95, 0.04, 1.8), glass, root, uv={'all': (0, 0, 3, 1.8)})
    tbox(kit, f"{p} ad panel", (1.5, 0.0, 1.3), (0.06, 1.25, 1.8), tm(kit, "bus poster", lambda: tex_poster(R)), root)
    tbox(kit, f"{p} side glass", (-1.5, 0.15, 1.3), (0.04, 0.95, 1.8), glass, root, uv={'all': (0, 0, 1, 1.8)})
    tbox(kit, f"{p} bench", (0, 0.35, 0.46), (2.4, 0.4, 0.06), solid(kit, "bench wood", "#e8a862", shade="#c47f3a"), root)
    for sx in (1, -1):
        tbox(kit, f"{p} bench leg {sx}", (sx * 1.0, 0.35, 0.22), (0.06, 0.34, 0.44), steel, root)
    tube(kit, f"{p} sign pole", [(-2.0, -0.4, 0), (-2.0, -0.4, 2.6)], 0.035, solid(kit, "sign pole", STEEL, shade="#a9a2e0"), root,
         sides=6)
    mb = MB()
    road.plate(mb, (-2.0, -0.42, 2.45), 0.28, 10, 0.03, 0, 1)
    mb.obj(kit, f"{p} sign", [tm(kit, "bus sign", tex_bus_sign), solid(kit, "sign back", "#9a94c8")], root)
    tbox(kit, f"{p} litter", (0.6, -0.4, 0.02), (0.2, 0.14, 0.03), solid(kit, "litter", WHITE), root, rot=(0, 0, 30))
    lowball(kit, f"{p} cup", (-0.9, -0.5, 0.07), (0.06, 0.06, 0.07), solid(kit, "cup", PINK), root, smooth=False)


def tex_billboard(rand):
    c = Canvas(96, 48, "#ff8fc8")
    for y in range(24, 48):
        c.rect(0, y, 95, y, "#ff8fc8" if y < 34 else "#ffb0d8" if y < 42 else "#ffd0e8")
    c.rect(0, 0, 95, 9, MINT)
    for x in range(0, 96, 6):
        c.rect(x, 9, x + 2, 9, WHITE)
    cone_icon(c, 16, 7, 22, PINK)
    disc(c, 16, 41, 6, "#9cff57")
    c.set(16, 48, RED)
    txt(c, "SCOOPS", 36, 44, WHITE, 2, shadow=PINK)
    txt(c, "ICE CREAM", 38, 30, BLUE, 1)
    txt(c, "NEXT EXIT", 38, 22, INK, 1)
    for i, (x, y) in enumerate(((60, 15), (63, 13), (66, 15), (69, 12), (72, 14))):   # graffiti scribble
        c.rect(x, y, x + 2, y + 1, RED)
    txt(c, "RUN", 76, 18, RED, 2)
    for hx, hy in ((8, 20), (86, 34)):   # zombie handprints
        c.rect(hx, hy, hx + 3, hy + 3, ZG)
        for f in range(4):
            c.rect(hx + f, hy + 4, hx + f, hy + 6 + (f % 2), ZG)
    c.rect(0, 0, 95, 0, WHITE); c.rect(0, 47, 95, 47, WHITE); c.rect(0, 0, 0, 47, WHITE); c.rect(95, 0, 95, 47, WHITE)
    return c


def billboard(kit, root, p):
    R = kit.rand
    w = wood(kit)
    steel = solid(kit, "billboard steel", "#5b5fc0", shade="#474aa0")
    for sx in (1, -1):
        tbox(kit, f"{p} leg {sx}", (sx * 2.2, 0.15, 3.0), (0.28, 0.28, 6.0), w, root, uv={'all': (0, 0, 0.25, 3)})
        tbox(kit, f"{p} brace {sx}", (sx * 2.2, 0.75, 2.5), (0.12, 0.12, 3.6), w, root, rot=(-24, 0, 0), uv={'all': (0, 0, 0.1, 2)})
    tbox(kit, f"{p} board", (0, 0, 6.2), (6.6, 0.24, 3.3), tm(kit, "billboard ad", lambda: tex_billboard(R)), root,
         uv=face_uv('ny', rest=(0, 0.95, 0.02, 0.97)))
    tbox(kit, f"{p} back", (0, 0.13, 6.2), (6.6, 0.02, 3.3), w, root, uv={'all': (0, 0, 3.3, 1.6)})
    tbox(kit, f"{p} catwalk", (0, -0.45, 4.48), (6.8, 0.7, 0.06), solid(kit, "grate", "#3c3fb8"), root)
    tbox(kit, f"{p} rail", (0, -0.78, 5.0), (6.8, 0.04, 0.04), steel, root)
    for i in range(5):
        tbox(kit, f"{p} rail post {i}", (-3.3 + i * 1.65, -0.78, 4.75), (0.04, 0.04, 0.5), steel, root)
    for i, x in enumerate((-2.0, 2.0)):
        tube(kit, f"{p} lamp arm {i}", [(x, 0.0, 7.85), (x, -0.5, 8.2), (x, -0.9, 8.15)], 0.03, steel, root, sides=4, side=(1, 0, 0))
        tbox(kit, f"{p} lamp {i}", (x, -0.95, 8.1), (0.4, 0.2, 0.1), steel, root)
        tbox(kit, f"{p} lamp glow {i}", (x, -0.95, 8.04), (0.32, 0.14, 0.02), solid(kit, "lamp glow", "#fff1a0", 3.0), root)


# ---------------------------------------------------------------- town buildings
def tex_diner_windows():
    """One 1.5 m bay: lit pane with a pink stool and a booth silhouette."""
    c = Canvas(16, 12, STEEL)
    c.rect(1, 1, 14, 10, "#ffd36b")
    c.rect(1, 1, 14, 3, "#ff8fc8")
    c.rect(6, 4, 9, 5, PINK); c.rect(7, 1, 8, 3, "#c75a9a")
    c.rect(2, 8, 4, 9, "#fff1a0")
    return c


def tex_neon(word, w, h, col):
    c = Canvas(w, h, INK)
    c.rect(0, 0, w - 1, 0, col); c.rect(0, h - 1, w - 1, h - 1, col)
    c.rect(0, 0, 0, h - 1, col); c.rect(w - 1, 0, w - 1, h - 1, col)
    txt_c(c, word, w // 2, h - 4, col, 2, shadow=hex_scale(col, 0.45))
    return c


def tex_diner_skirt(rand):
    c = Canvas(16, 16, "#c9c2f0")
    for x in range(0, 16, 2):
        c.rect(x, 0, x, 15, "#a9a2e0")
    c.speckle(rand, ["#e6e0ff"], 12)
    return c


def tex_door_glass():
    c = Canvas(16, 32, PINK)
    c.rect(2, 3, 13, 27, "#ffd36b")
    c.rect(7, 3, 8, 27, PINK)
    txt_c(c, "OPEN", 8, 20, RED)
    return c


def diner(kit, root, p):
    """50s chrome diner, 11 x 5 m, front (door) facing -Y."""
    R = kit.rand
    L, D = 5.5, 2.5
    body = tm(kit, "diner body", lambda: stops.tex_stucco(R, WHITE), 0.32, 'REPEAT')
    skirt = tm(kit, "diner skirt", lambda: tex_diner_skirt(R), 0.3, 'REPEAT')
    win = tm(kit, "diner windows", tex_diner_windows, 0.55, 'REPEAT')
    pink, chrome = solid(kit, "diner pink", PINK), solid(kit, "diner chrome", "#e6e0ff", 0.4, shade="#c9c2f0")
    neon_m = solid(kit, "neon mint", MINT, 1.6)
    tbox(kit, f"{p} skirt", (0, 0, 0.35), (2 * L + 0.1, 2 * D + 0.1, 0.7), skirt, root, uv={'all': (0, 0, 11, 1)})
    prof = [(-D, 0.7), (D, 0.7), (D, 3.3), (D - 0.35, 3.85), (D - 1.25, 4.2), (0, 4.3), (-D + 1.25, 4.2), (-D + 0.35, 3.85),
            (-D, 3.3)]
    prism(kit, f"{p} body", prof, -L, L, body, root)
    for sy in (-1, 1):
        y = sy * (D + 0.03)
        tbox(kit, f"{p} stripe {sy}", (0, y, 1.05), (2 * L, 0.06, 0.55), pink, root)
        tbox(kit, f"{p} chrome band {sy}", (0, y, 1.42), (2 * L, 0.07, 0.12), chrome, root)
        tbox(kit, f"{p} windows {sy}", (0, y, 2.25), (2 * L - 0.6, 0.06, 1.25), win, root,
             uv={'all': (0, 0, (2 * L - 0.6) / 1.5, 1)})
        tbox(kit, f"{p} sill chrome {sy}", (0, y * 1.01, 3.0), (2 * L, 0.07, 0.1), chrome, root)
        tbox(kit, f"{p} neon {sy}", (0, y * 1.02, 3.32), (2 * L, 0.05, 0.06), neon_m, root)
    for sx in (-1, 1):
        tbox(kit, f"{p} end window {sx}", (sx * (L + 0.03), 0, 2.25), (0.06, 2 * D - 1.2, 1.25), win, root,
             uv={'all': (0, 0, 2.5, 1)})
        tbox(kit, f"{p} end stripe {sx}", (sx * (L + 0.03), 0, 1.05), (0.06, 2 * D, 0.55), pink, root)
    # vestibule with the door
    tbox(kit, f"{p} vestibule", (0, -D - 0.55, 1.95), (2.0, 1.1, 2.5), body, root, uv={'all': (0, 0, 1, 1.2)})
    tbox(kit, f"{p} vestibule roof", (0, -D - 0.6, 3.27), (2.3, 1.35, 0.14), pink, root)
    tbox(kit, f"{p} door", (0, -D - 1.12, 1.75), (1.0, 0.05, 2.1), tm(kit, "diner door", tex_door_glass), root,
         uv=face_uv('ny', rest=(0, 0, 0.05, 0.05)))
    tbox(kit, f"{p} step", (0, -D - 1.45, 0.35), (1.8, 0.7, 0.7), skirt, root, uv={'all': (0, 0, 2, 1)})
    kit.empty(f"{p} socket door", root, (0, -D - 2.0, 0))
    # roof sign on two poles
    for sx in (-1, 1):
        tube(kit, f"{p} sign pole {sx}", [(sx * 1.5, 0, 4.2), (sx * 1.5, 0, 5.0)], 0.06, chrome, root, sides=6)
    tbox(kit, f"{p} sign", (0, 0, 5.65), (4.4, 0.22, 1.35), tm(kit, "diner neon", lambda: tex_neon("DINER", 48, 16, PINK), 1.2),
         root, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    tbox(kit, f"{p} sign cap", (0, 0, 6.38), (4.6, 0.3, 0.1), pink, root)
    # a big soft serve cone on the roof end
    tube(kit, f"{p} cone", [(L - 1.3, 0.0, 4.0), (L - 1.3, 0.0, 5.3)], [0.05, 0.5], tm(kit, "waffle", tex_waffle), root, sides=8)
    for i, (z, r) in enumerate(((5.45, 0.55), (5.8, 0.42), (6.1, 0.26))):
        lowball(kit, f"{p} swirl {i}", (L - 1.3, 0, z), (r, r, r * 0.6), solid(kit, "soft serve", "#fff1dc", 0.45), root)
    tube(kit, f"{p} swirl tip", [(L - 1.3, 0, 6.2), (L - 1.25, 0, 6.45)], [0.12, 0.02], solid(kit, "soft serve", "#fff1dc", 0.45),
         root, sides=6)
    tbox(kit, f"{p} ac unit", (-3.2, 1.0, 4.35), (1.1, 0.9, 0.6), solid(kit, "ac steel", "#9a94c8"), root)


def tex_apartment(rand):
    """160 x 80 atlas at 8 px/m: x 0-95 front (12 x 10 m), x 96-159 side (8 x 10 m)."""
    c = Canvas(160, 80, "#c95a7a")
    road.bricks(c, rand, 0, 24, 159, 76, "#c95a7a", "#9e3d5c", "#d9708e")
    c.rect(0, 77, 159, 79, WHITE)
    c.rect(0, 0, 95, 23, "#ffc2dc")
    c.rect(0, 0, 95, 1, "#d93a85")
    c.rect(0, 18, 95, 23, BLUE)
    txt_c(c, "LAUNDRY", 48, 22, WHITE, 1, shadow=INK)
    for x0 in (4, 56):
        c.rect(x0, 3, x0 + 35, 15, WHITE)
        c.rect(x0 + 2, 4, x0 + 33, 14, "#ffd36b")
        for k in range(4):
            disc(c, x0 + 6 + k * 8, 8, 2, STEEL)
            disc(c, x0 + 6 + k * 8, 8, 1, GLASS)
    c.rect(42, 0, 53, 15, WHITE)
    c.rect(44, 0, 51, 14, INK)
    c.rect(96, 0, 159, 23, "#c95a7a")
    road.bricks(c, rand, 96, 0, 159, 23, "#c95a7a", "#9e3d5c", "#d9708e")

    def win(x, y, state):
        if state == "lit":
            road.window_px(c, x, y, 10, 13, True)
        elif state == "dark":
            road.window_px(c, x, y, 10, 13, False)
        elif state == "boarded":
            c.rect(x, y, x + 9, y + 12, WHITE)
            c.rect(x + 1, y + 1, x + 8, y + 11, "#2a1f4f")
            for k in range(3):
                c.rect(x - 1, y + 2 + k * 4, x + 10, y + 3 + k * 4, "#d9924a")
        else:   # broken
            road.window_px(c, x, y, 10, 13, False)
            c.rect(x + 2, y + 2, x + 7, y + 10, INK)
            c.dots([(x + 3, y + 9), (x + 6, y + 4), (x + 4, y + 6)], "#c7d4ff")
        c.rect(x - 1, y - 1, x + 10, y - 1, WHITE)
    states = ["lit", "dark", "dark", "boarded", "broken", "lit", "dark"]
    for f, y in enumerate((29, 55)):
        for k, x in enumerate((7, 31, 55, 79)):
            win(x, y, states[(f * 4 + k * 3 + rand.randrange(3)) % len(states)])
        for k, x in enumerate((110, 140)):
            win(x, y, states[(f + k * 2 + rand.randrange(3)) % len(states)])
    for k, x in enumerate((110, 140)):
        win(x, 6, "dark")
    for _ in range(3):   # graffiti and goo
        x, y = rand.randrange(0, 90), rand.randint(26, 50)
        c.rect(x, y, x + 5, y + 1, ZG)
    return c


def apartment(kit, root, p):
    """Three storey brick block, 12 x 8 x 10 m, laundromat at street level, front facing -Y."""
    R = kit.rand
    W, D, H = 6.0, 4.0, 10.0
    atlas = tm(kit, "apartment", lambda: tex_apartment(R))
    front, side = (0, 0, 96 / 160, 1), (96 / 160, 0, 1, 1)
    tbox(kit, f"{p} walls", (0, 0, H / 2), (2 * W, 2 * D, H), atlas, root,
         uv={'ny': front, 'py': front, 'px': side, 'nx': side, 'pz': (0.62, 0.1, 0.63, 0.11), 'nz': (0.62, 0.1, 0.63, 0.11)})
    white, ink = solid(kit, "trim", WHITE, 0.35), solid(kit, "fire escape", "#2a1f4f", 0.12)
    tbox(kit, f"{p} cornice", (0, 0, H + 0.12), (2 * W + 0.3, 2 * D + 0.3, 0.24), white, root)
    tbox(kit, f"{p} roof", (0, 0, H + 0.02), (2 * W - 0.3, 2 * D - 0.3, 0.06), solid(kit, "tar roof", "#3d3358"), root)
    awning = tm(kit, "laundry awning", tex_awning, 0.35, 'REPEAT')
    for i, x in enumerate((-3.6, 3.0)):
        tbox(kit, f"{p} awning {i}", (x, -D - 0.45, 2.05), (4.6, 1.0, 0.08), awning, root, rot=(20, 0, 0),
             uv={'all': (0, 0, 4, 1)})
    # fire escape: two landings joined by a ladder in front of the left windows
    for f, z in enumerate((3.2, 6.4)):
        tbox(kit, f"{p} landing {f}", (-2.4, -D - 0.6, z), (4.4, 1.2, 0.06), ink, root)
        tbox(kit, f"{p} landing rail {f}", (-2.4, -D - 1.18, z + 0.5), (4.4, 0.04, 0.05), ink, root)
        for k in range(5):
            tbox(kit, f"{p} baluster {f} {k}", (-4.6 + k * 1.1, -D - 1.18, z + 0.25), (0.04, 0.04, 0.5), ink, root)
    tbox(kit, f"{p} ladder", (-2.4, -D - 0.6, 4.8), (0.5, 0.06, 3.5), ink, root, rot=(0, 35, 0))
    # rooftop water tank and vents
    for sx in (1, -1):
        for sy in (1, -1):
            tube(kit, f"{p} tank leg {sx} {sy}", [(3 + sx * 0.6, 1.5 + sy * 0.6, H), (3 + sx * 0.6, 1.5 + sy * 0.6, H + 1.2)], 0.05,
                 ink, root, sides=4)
    tube(kit, f"{p} tank", [(3, 1.5, H + 1.2), (3, 1.5, H + 2.7)], 0.95, wood(kit), root, sides=10, v=(0, 0.8))
    tube(kit, f"{p} tank roof", [(3, 1.5, H + 2.7), (3, 1.5, H + 3.2)], [1.02, 0.05], solid(kit, "tank roof", PURP), root, sides=10)
    for i, (x, y) in enumerate(((-3.5, 1.0), (-1.5, 2.2))):
        tbox(kit, f"{p} vent {i}", (x, y, H + 0.35), (0.9, 0.7, 0.6), solid(kit, "ac steel", "#9a94c8"), root)
    kit.empty(f"{p} socket door", root, (0, -D - 0.6, 0))


def tex_silo(rand):
    c = Canvas(16, 64, WHITE)
    for y in range(0, 64, 8):
        c.rect(0, y, 15, y + 3, MINT)
    c.speckle(rand, ["#e6e0ff", "#22c79c"], 40)
    for _ in range(4):
        disc(c, rand.randrange(16), rand.randrange(64), 1, "#c96f3a")
    return c


def silo(kit, root, p):
    R = kit.rand
    tube(kit, f"{p} body", [(0, 0, 0), (0, 0, 10.0)], 1.7, tm(kit, "silo", lambda: tex_silo(R)), root, sides=12)
    lowball(kit, f"{p} dome", (0, 0, 10.0), (1.75, 1.75, 1.3), solid(kit, "silo dome", PINK), root)
    tube(kit, f"{p} vent", [(0, 0, 11.1), (0, 0, 11.6)], [0.25, 0.1], solid(kit, "silo vent", STEEL), root, sides=6)
    steel = solid(kit, "ladder steel", "#5b5fc0", shade="#474aa0")
    for sx in (1, -1):
        tbox(kit, f"{p} ladder rail {sx}", (sx * 0.25, -1.8, 5.2), (0.05, 0.05, 10.0), steel, root)
    for i in range(24):
        tbox(kit, f"{p} rung {i}", (0, -1.8, 0.5 + i * 0.4), (0.5, 0.04, 0.04), steel, root)
    for i in range(8):
        tbox(kit, f"{p} cage {i}", (0, -2.05, 3.0 + i * 0.9), (0.7, 0.04, 0.04), steel, root)
    tube(kit, f"{p} chute", [(1.5, 0.6, 9.4), (2.4, 1.0, 8.0), (2.8, 1.2, 1.5)], 0.18, solid(kit, "chute", "#c9c2f0"), root, sides=6)
    tbox(kit, f"{p} hopper", (2.8, 1.2, 0.75), (0.9, 0.9, 1.5), solid(kit, "hopper", PURP), root, taper=(1.3, 1.3))
    tbox(kit, f"{p} base", (0, 0, 0.12), (3.8, 3.8, 0.24), stone(kit), root, uv={'all': (0, 0, 3, 0.3)})


def tex_tower(rand):
    c = Canvas(96, 32, PINK)
    frosting(c, rand, 22, 14)
    c.rect(0, 0, 95, 1, "#d93a85")
    txt_c(c, "SPRINKLE", 48, 11, WHITE, 1, shadow="#b0306f")
    for _ in range(20):
        x, y = rand.randrange(96), rand.randint(2, 12)
        if not (30 < x < 66):
            c.rect(x, y, x + 1, y, rand.choice((YEL, MINT, BLUE, WHITE)))
    return c


def water_tower(kit, root, p):
    R = kit.rand
    steel = solid(kit, "tower steel", "#5b5fc0", shade="#474aa0")
    zt = 9.4
    for i, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, -1), (-1, 1))):
        tube(kit, f"{p} leg {i}", [(sx * 2.3, sy * 2.3, 0), (sx * 1.55, sy * 1.55, zt)], [0.16, 0.12], steel, root, sides=6)
        tbox(kit, f"{p} foot {i}", (sx * 2.3, sy * 2.3, 0.15), (0.6, 0.6, 0.3), stone(kit), root, uv={'all': (0, 0, 0.6, 0.3)})
    for lvl, (z0, z1) in enumerate(((0.6, 4.6), (4.6, 8.6))):
        f0, f1 = 2.3 - 0.75 * z0 / zt, 2.3 - 0.75 * z1 / zt
        for k, ((ax, ay), (bx, by)) in enumerate((((1, 1), (1, -1)), ((1, -1), (-1, -1)), ((-1, -1), (-1, 1)), ((-1, 1), (1, 1)))):
            tube(kit, f"{p} brace {lvl} {k} a", [(ax * f0, ay * f0, z0), (bx * f1, by * f1, z1)], 0.04, steel, root, sides=4)
            tube(kit, f"{p} brace {lvl} {k} b", [(bx * f0, by * f0, z0), (ax * f1, ay * f1, z1)], 0.04, steel, root, sides=4)
    tube(kit, f"{p} tank", [(0, 0, zt), (0, 0, zt + 0.3), (0, 0, zt + 3.4)], [1.8, 2.7, 2.7],
         tm(kit, "tower tank", lambda: tex_tower(R)), root, sides=12, v=(0, 1))
    tube(kit, f"{p} roof", [(0, 0, zt + 3.4), (0, 0, zt + 3.5), (0, 0, zt + 4.9)], [2.85, 2.85, 0.1],
         solid(kit, "tower roof", MINT, shade="#22c79c"), root, sides=12)
    lowball(kit, f"{p} cherry", (0, 0, zt + 5.15), (0.32, 0.32, 0.32), solid(kit, "cherry", RED, 0.45), root)
    ring_mesh(kit, f"{p} catwalk", 2.7, 3.4, solid(kit, "grate", "#3c3fb8"), root, (0, 0, zt + 0.32), segs=12)
    rail = [(3.35 * math.cos(2 * math.pi * k / 12), 3.35 * math.sin(2 * math.pi * k / 12), zt + 1.25) for k in range(13)]
    tube(kit, f"{p} rail", rail, 0.035, steel, root, sides=4, front=(0, 0, 1), caps=(False, False))
    for k in range(12):
        a = 2 * math.pi * k / 12
        tbox(kit, f"{p} rail post {k}", (3.35 * math.cos(a), 3.35 * math.sin(a), zt + 0.8), (0.05, 0.05, 0.9), steel, root)
    for sx in (1, -1):
        tbox(kit, f"{p} ladder rail {sx}", (sx * 0.22, -2.6, zt / 2 + 0.3), (0.05, 0.05, zt + 0.4), steel, root, rot=(-4.5, 0, 0))
    for i in range(int(zt / 0.45)):
        z = 0.4 + i * 0.45
        tbox(kit, f"{p} rung {i}", (0, -2.6 + 0.08 * (z - zt / 2) / zt * 9.4, z), (0.44, 0.04, 0.04), steel, root)


def tool_shed(kit, root, p):
    R = kit.rand
    w = wood(kit)
    roof = tm(kit, "shed roof", lambda: stops.tex_ribbed(R, "#5b6cff", "#3d47c8", 4), 0.32, 'REPEAT')
    prof = [(-1.3, 0), (1.3, 0), (1.3, 2.1), (0, 2.8), (-1.3, 2.1)]
    tbox(kit, f"{p} floor", (0, 0, 0.08), (3.2, 2.8, 0.16), stone(kit), root, uv={'all': (0, 0, 3, 0.2)})
    piv = kit.empty(f"{p} body", root, (0, 0, 0.16), (0, 0, 90))
    prism(kit, f"{p} walls", prof, -1.5, 1.5, w, piv)
    for i, (a, b) in enumerate(((prof[4], prof[3]), (prof[3], prof[2]))):
        slab(kit, f"{p} roof {i}", a, b, -1.5, 1.5, 0.1, roof, piv, ext=(0.3, 0.05) if i == 0 else (0.05, 0.3))
    door = kit.empty(f"{p} door", root, (-0.5, -1.33, 0.16), (0, 0, -35))
    tbox(kit, f"{p} door", (0.5, -0.03, 0.95), (1.0, 0.06, 1.9), solid(kit, "shed door", PINK), door)
    tbox(kit, f"{p} door dark", (0, -1.32, 1.11), (1.0, 0.02, 1.9), solid(kit, "shed dark", INK, 0.08), root)
    tbox(kit, f"{p} window", (1.52, 0, 1.4), (0.04, 0.8, 0.6), solid(kit, "shed window", "#ffd36b", 0.9), root)
    tbox(kit, f"{p} shovel handle", (1.0, -1.4, 0.75), (0.04, 0.04, 1.3), w, root, rot=(12, 0, 0))
    tbox(kit, f"{p} shovel blade", (1.0, -1.25, 0.12), (0.22, 0.03, 0.3), solid(kit, "shovel", STEEL), root, rot=(12, 0, 0))


# ---------------------------------------------------------------- wrecks
def tex_bus_side(rand):
    c = Canvas(128, 40, "#ffc93a")
    c.speckle(rand, ["#f0b830", "#ffd85a"], 120)
    for y in (6, 12):
        c.rect(0, y, 127, y + 1, INK)
    x = 4
    while x < 124:
        broken = rand.random() < 0.35
        c.rect(x, 16, x + 9, 29, GLASS if not broken else INK)
        if broken:
            for k in range(4):
                c.set(x + rand.randrange(10), 16 + rand.randrange(14), "#c7d4ff")
        else:
            c.dots([(x + 2, 26), (x + 3, 25), (x + 4, 24)], "#6f8cff")
        x += 12
    txt_c(c, "SCHOOL BUS", 64, 37, INK)
    for hx, hy in ((20, 2), (70, 3), (102, 2)):
        c.rect(hx, hy, hx + 3, hy + 2, RED)
        for f in range(4):
            c.rect(hx + f, hy + 3, hx + f, hy + 4 + (f % 2), RED)
    for _ in range(8):
        disc(c, rand.randrange(128), rand.randrange(1, 14), rand.choice((1, 2)), "#c96f3a")
    return c


def school_bus(kit, root, p):
    """Crashed school bus, 11 m long, nose (-Y) down in a ditch."""
    R = kit.rand
    side = tm(kit, "bus side", lambda: tex_bus_side(R))
    yel = solid(kit, "bus yellow", "#ffc93a", shade="#f0b830")
    ink = solid(kit, "bus black", INK, 0.1)
    glass = tm(kit, "bus glass", lambda: tex_car_glass(R))
    body = kit.empty(f"{p} body", root, (0, 0, 0.12), (-3, 4, 0))
    tbox(kit, f"{p} hull", (0, 1.0, 1.7), (2.5, 8.6, 2.5), side, body,
         uv={'all': (0.5, 0.2, 0.52, 0.22), 'px': (0, 0, 1, 1), 'nx': (0, 0, 1, 1)})
    tbox(kit, f"{p} roof", (0, 1.0, 3.02), (2.4, 8.5, 0.16), solid(kit, "bus roof", WHITE), body, taper=(0.92, 0.99))
    tbox(kit, f"{p} hood", (0, -4.1, 1.0), (2.3, 1.6, 1.1), yel, body, taper=(0.95, 0.9))
    hood = kit.empty(f"{p} hood lid", body, (0, -3.3, 1.58), (-25, 0, 0))
    tbox(kit, f"{p} hood lid", (0, -0.8, 0.02), (2.2, 1.6, 0.05), yel, hood)
    tbox(kit, f"{p} windshield", (0, -3.32, 2.3), (2.3, 0.05, 1.0), glass, body)
    tbox(kit, f"{p} grille", (0, -4.92, 0.95), (1.6, 0.05, 0.7), solid(kit, "grille", STEEL), body)
    tbox(kit, f"{p} bumper", (0, -5.0, 0.48), (2.5, 0.2, 0.24), ink, body, rot=(0, 8, 0))
    tbox(kit, f"{p} rear bumper", (0, 5.35, 0.55), (2.5, 0.2, 0.24), ink, body)
    for sx in (1, -1):
        tbox(kit, f"{p} flasher {sx}", (sx * 0.9, -3.25, 3.0), (0.2, 0.1, 0.16), solid(kit, "flasher", RED, 1.4), body)
    arm = kit.empty(f"{p} stop arm", body, (1.27, -2.6, 2.0), (0, 0, -80))
    mb = MB()
    road.plate(mb, (0, -0.45, 0), 0.25, 8, 0.03, 0, 1, math.radians(22.5))
    mb.obj(kit, f"{p} stop arm", [tm(kit, "stop sign", lambda: road.tex_stop(R)), solid(kit, "sign back", "#9a94c8")], arm)
    door = kit.empty(f"{p} door", body, (-1.27, -2.7, 0.5), (0, 0, 60))
    tbox(kit, f"{p} door", (0, 0.4, 1.0), (0.05, 0.8, 2.0), glass, door)
    tire_m, hub = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050"), solid(kit, "bus hub", STEEL)
    for nm, x, y in (("FL", -1.1, -3.9), ("FR", 1.1, -3.9), ("RL", -1.1, 3.0), ("RR", 1.1, 3.0)):
        wheel(kit, f"{p} wheel {nm}", body, (x, y, 0.42), 1 if x > 0 else -1, tire_m, hub, ink)
    shard = solid(kit, "glass shard", "#c7d4ff", 0.6)
    for i in range(8):
        tbox(kit, f"{p} shard {i}", (0, 0, 0), (0.1, 0.07, 0.01), shard, root,
             loc=(R.uniform(-2.2, -1.4), R.uniform(-3.0, 3.5), 0.01), rot=(0, 0, R.uniform(0, 180)))
    lowball(kit, f"{p} backpack", (-1.9, -1.6, 0.15), (0.2, 0.14, 0.18), solid(kit, "backpack", PURP), root, smooth=False)


# ---------------------------------------------------------------- cemetery
def tex_grave(rand, word):
    c = Canvas(16, 24, STONE)
    c.speckle(rand, [STONE_D, "#c4b8e6"], 30)
    txt_c(c, word, 8, 18, "#5e4f8a")
    c.rect(4, 9, 11, 9, "#5e4f8a")
    for _ in range(2):
        x = rand.randrange(16)
        c.rect(x, 0, x, rand.randint(2, 6), "#4fd68a")
    return c


def gravestone(kit, root, p, kind=0, word="RIP"):
    R = kit.rand
    st = stone(kit)
    face = tm(kit, f"grave {word}", lambda: tex_grave(R, word))
    lean = kit.empty(f"{p} lean", root, (0, 0, 0), (R.uniform(-8, 8), R.uniform(-6, 6), R.uniform(-8, 8)))
    if kind == 0:
        tbox(kit, f"{p} slab", (0, 0, 0.4), (0.62, 0.16, 0.8), face, lean, uv=face_uv('ny', rest=(0, 0, 0.1, 0.1)))
        tube(kit, f"{p} top", [(0, -0.08, 0.8), (0, 0.08, 0.8)], 0.31, st, lean, sides=10, front=(0, 0, 1))
    elif kind == 1:
        tbox(kit, f"{p} upright", (0, 0, 0.6), (0.18, 0.16, 1.2), st, lean, uv={'all': (0, 0, 0.2, 1.2)})
        tbox(kit, f"{p} arm", (0, 0, 0.88), (0.7, 0.16, 0.18), st, lean, uv={'all': (0, 0, 0.7, 0.2)})
        tbox(kit, f"{p} plinth", (0, 0, 0.1), (0.5, 0.35, 0.2), st, lean, uv={'all': (0, 0, 0.5, 0.2)})
    else:
        tbox(kit, f"{p} block", (0, 0, 0.3), (0.8, 0.3, 0.6), face, lean, uv=face_uv('ny', rest=(0, 0, 0.1, 0.1)), taper=(0.9, 0.8))
    tbox(kit, f"{p} mound", (0, -0.85, 0.06), (0.7, 1.4, 0.14), tm(kit, "grave soil", lambda: tex_soil(R), 0.2, 'REPEAT'), root,
         taper=(0.75, 0.85), uv={'all': (0, 0, 0.7, 1.4)})


def open_grave(kit, root, p):
    R = kit.rand
    soil = tm(kit, "grave soil", lambda: tex_soil(R), 0.2, 'REPEAT')
    tbox(kit, f"{p} hole", (0, -0.9, 0.006), (0.95, 1.9, 0.012), solid(kit, "grave hole", "#120a24", 0.0), root)
    for i, (x, y, rx, ry, rz) in enumerate(((0.95, -0.6, 0.5, 0.7, 0.35), (0.85, -1.4, 0.4, 0.45, 0.28), (-0.7, -1.7, 0.3, 0.3, 0.16))):
        lowball(kit, f"{p} dirt {i}", (x, y, 0), (rx, ry, rz), soil, root, smooth=False)
    gravestone(kit, kit.empty(f"{p} stone", root, (0.1, 0.25, 0), (-14, 0, 9)), f"{p} stone", 0, "RIP")
    hand = kit.empty(f"{p} hand", root, (-0.25, -1.75, 0), (10, -15, 20))
    skin = solid(kit, "zombie skin", "#9cff57", shade="#6fd83a")
    tube(kit, f"{p} forearm", [(0, 0, -0.1), (0, 0, 0.42)], [0.06, 0.05], skin, hand, sides=6)
    tbox(kit, f"{p} palm", (0, 0, 0.5), (0.13, 0.05, 0.14), skin, hand)
    for f in range(4):
        tbox(kit, f"{p} finger {f}", (-0.045 + f * 0.03, 0, 0.62 + 0.02 * (f % 2)), (0.022, 0.03, 0.12), skin, hand,
             rot=(0, -8 + f * 5, 0))
    tbox(kit, f"{p} sleeve", (0, 0, 0.08), (0.14, 0.14, 0.12), solid(kit, "sleeve", "#5b4a8a"), hand)
    sh = kit.empty(f"{p} shovel", root, (1.0, -0.8, 0.3), (0, -28, 0))
    tbox(kit, f"{p} shovel handle", (0, 0, 0.55), (0.04, 0.04, 1.1), wood(kit), sh, uv={'all': (0, 0, 0.05, 1)})
    tbox(kit, f"{p} shovel blade", (0, 0, -0.05), (0.24, 0.03, 0.3), solid(kit, "shovel", STEEL), sh)


def tex_crypt():
    c = Canvas(32, 8, STONE)
    c.rect(0, 0, 31, 0, STONE_D); c.rect(0, 7, 31, 7, STONE_D)
    txt_c(c, "REST", 16, 6, "#5e4f8a")
    return c


def mausoleum(kit, root, p):
    st = stone(kit)
    tbox(kit, f"{p} step", (0, -0.2, 0.15), (3.8, 4.6, 0.3), st, root, uv={'all': (0, 0, 3.8, 0.3)})
    tbox(kit, f"{p} walls", (0, 0.4, 1.85), (3.0, 3.2, 3.1), st, root, uv={'all': (0, 0, 3, 3)})
    for sx in (1, -1):
        tube(kit, f"{p} column {sx}", [(sx * 1.25, -1.6, 0.3), (sx * 1.25, -1.6, 3.4)], [0.2, 0.17], st, root, sides=8)
        tbox(kit, f"{p} column cap {sx}", (sx * 1.25, -1.6, 3.42), (0.5, 0.5, 0.12), st, root, uv={'all': (0, 0, 0.5, 0.1)})
    tbox(kit, f"{p} lintel", (0, -0.8, 3.6), (3.4, 2.0, 0.3), tm(kit, "crypt lintel", tex_crypt), root,
         uv=face_uv('ny', rest=(0.5, 0.5, 0.52, 0.52)))
    mb = MB()
    road.extrude_y(mb, [(-1.8, 0), (1.8, 0), (0, 1.0)], -1.85, 2.05, 0, (0, 0, 3.75))
    mb.obj(kit, f"{p} pediment", [st], root)
    tbox(kit, f"{p} doorway", (0, -1.21, 1.45), (1.3, 0.02, 2.3), solid(kit, "crypt dark", "#120a24", 0.0), root)
    door = kit.empty(f"{p} door", root, (0.65, -1.22, 0.3), (0, 0, 38))
    tbox(kit, f"{p} door", (-0.32, -0.04, 1.15), (0.64, 0.08, 2.3), solid(kit, "crypt door", "#4a3a6e"), door)
    goo = solid(kit, "goo", ZG, 0.9, shade="#6fd83a")
    for i, (x, ln) in enumerate(((-0.6, 0.6), (0.2, 0.35), (0.5, 0.8))):
        tbox(kit, f"{p} goo drip {i}", (x, -1.82, 3.45 - ln / 2), (0.1, 0.04, ln), goo, root)
    splat(kit, f"{p} goo pool", (0, -2.2, 0.31), 0.5, goo, root)


def iron_fence(kit, root, p):
    """2.5 m segment along X with its post at x = -1.25."""
    iron = solid(kit, "wrought iron", "#4a3a6e", 0.25, shade="#3a2a5a")
    tbox(kit, f"{p} post", (-1.25, 0, 0.85), (0.12, 0.12, 1.7), iron, root)
    lowball(kit, f"{p} post ball", (-1.25, 0, 1.78), (0.09, 0.09, 0.09), iron, root, smooth=False)
    for z in (0.2, 1.35):
        tbox(kit, f"{p} rail {z}", (0, 0, z), (2.5, 0.04, 0.05), iron, root)
    for i in range(9):
        x = -1.0 + i * 0.25
        tbox(kit, f"{p} bar {i}", (x, 0, 0.78), (0.025, 0.025, 1.5), iron, root)
        tbox(kit, f"{p} spike {i}", (x, 0, 1.58), (0.06, 0.025, 0.12), iron, root, taper=(0.1, 1.0))


# ---------------------------------------------------------------- scenery blocks (20 x 20 m, road beyond y = -10)
def asphalt(kit):
    return tm(kit, "road asphalt", lambda: road.tex_road(kit.rand), 0.15, 'REPEAT')


def sidewalk(kit):
    return tm(kit, "sidewalk", lambda: road.tex_sidewalk(kit.rand), 0.22, 'REPEAT')


def dirt(kit):
    return tm(kit, "dirt", lambda: tex_dirt(kit.rand), 0.15, 'REPEAT')


def ground(kit, root, p):
    mb = MB()
    road.lawn(mb, rect(-HALF, -HALF, HALF, HALF))
    mb.obj(kit, f"{p} ground", road.ground_mats(kit), root)


def pad(kit, root, name, x0, y0, x1, y1, mat, tile=2.0, z=0.012):
    tbox(kit, name, ((x0 + x1) / 2, (y0 + y1) / 2, SIDE + z / 2), (x1 - x0, y1 - y0, z), mat, root,
         uv={'all': (x0 / tile, y0 / tile, x1 / tile, y1 / tile)})


def at(kit, d, fn, name, x, y, rz=0.0, scale=1.0, z=SIDE):
    return place(kit, fn, d, name, (x, y, z), rz, scale=scale)


def fence_line(kit, d, fn, name, a, b, seg, post):
    """Fence segments (each with its post at local x = -seg / 2) from a to b, closed by a post at b (post = (material,
    width, height))."""
    a, b = Vector(a), Vector(b)
    n = max(1, round((b - a).length / seg))
    rz = math.degrees(math.atan2(b.y - a.y, b.x - a.x))
    k = (b - a) / n
    for i in range(n):
        c = a + k * (i + 0.5)
        sc = k.length / seg
        piv = kit.empty(f"{name} {i}", d, (c.x, c.y, SIDE), (0, 0, rz), (sc, 1, 1))
        fn(kit, piv, f"{name} {i}")
    end = kit.empty(f"{name} end", d, (b.x, b.y, SIDE), (0, 0, rz))
    tbox(kit, f"{name} end post", (0, 0, post[2] / 2), (post[1], post[1], post[2]), post[0], end)


def rail_post(kit):
    return solid(kit, "rail wood", "#a87a66", shade="#7a4a4c"), 0.14, 1.2


def iron_post(kit):
    return solid(kit, "wrought iron", "#4a3a6e", 0.25, shade="#3a2a5a"), 0.12, 1.7


def scatter(R, n, x0, x1, y0, y1, gap, taken):
    pts = []
    for _ in range(600):
        if len(pts) == n:
            break
        q = (R.uniform(x0, x1), R.uniform(y0, y1))
        if all(math.dist(q, t[:2]) >= max(gap, t[2]) for t in taken + [(*p, gap) for p in pts]):
            pts.append(q)
    taken += [(*q, gap) for q in pts]
    return pts


def grass_tufts(kit, d, p, spots):
    for i, (x, y) in enumerate(spots):
        at(kit, d, tall_grass, f"{p} grass {i}", x, y, i * 47, 0.9 + 0.1 * (i % 3))


def block_houses(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    for i, x in enumerate((-5.0, 5.2)):
        pad(kit, root, f"{p} path {i}", x - 0.6, -HALF, x + 0.6, -2.4, sidewalk(kit))
    at(kit, d, road.house, f"{p} house 0", -5.0, 1.6, -90)
    at(kit, d, road.house, f"{p} house 1", 5.2, 2.0, -90)
    for i, cx in enumerate((-8.6, -6.6, -3.4, -1.4, 0.6, 2.6, 7.2)):
        at(kit, d, road.picket_fence, f"{p} picket {i}", cx, -8.8)
    at(kit, d, road.mailbox, f"{p} mailbox 0", -6.2, -9.4)
    at(kit, d, road.mailbox, f"{p} mailbox 1", 4.0, -9.4)
    at(kit, d, road.round_tree, f"{p} tree 0", -0.4, -5.6, 30)
    at(kit, d, road.pine_tree, f"{p} pine 0", -8.6, 8.4)
    at(kit, d, road.pine_tree, f"{p} pine 1", 8.9, 8.6, 40, 0.9)
    at(kit, d, road.bush, f"{p} bush 0", -2.4, -7.0)
    at(kit, d, road.bush, f"{p} bush 1", 8.4, -6.4, 70)
    at(kit, d, road.trash_can, f"{p} trash", 3.2, -8.0)
    at(kit, d, picnic_table, f"{p} picnic", 0.2, 8.3, 8)
    grass_tufts(kit, d, p, [(-9.3, -6.5), (9.2, -1.0), (-1.0, 4.5)])
    bake(kit, root, p)


def block_diner(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} lot", -9.6, -9.6, 9.6, -2.2, asphalt(kit))
    white = solid(kit, "lane white", WHITE, 0.4)
    for i in range(7):
        tbox(kit, f"{p} stall {i}", (-7.5 + i * 2.5, -4.0, SIDE + 0.014), (0.12, 3.0, 0.01), white, root)
    at(kit, d, diner, f"{p} diner", 0, 2.6)
    at(kit, d, road.wrecked_sedan, f"{p} sedan", -4.3, -4.3, 8, z=SIDE + 0.012)
    at(kit, d, road.traffic_cone, f"{p} cone 0", 2.0, -7.5, 20, z=SIDE + 0.012)
    at(kit, d, road.traffic_cone, f"{p} cone 1", 3.1, -6.9, 0, z=SIDE + 0.012)
    at(kit, d, road.street_lamp, f"{p} lamp", 9.0, -9.0, 180, z=SIDE + 0.012)
    at(kit, d, phone_booth, f"{p} phone", 8.6, -0.9)
    at(kit, d, dumpster, f"{p} dumpster", -7.8, 7.8)
    at(kit, d, barrel_stack, f"{p} barrels", 8.0, 7.6, 160)
    at(kit, d, road.round_tree, f"{p} tree", -8.0, 3.4, 80)
    at(kit, d, road.pine_tree, f"{p} pine", 8.4, 3.6)
    grass_tufts(kit, d, p, [(-9.2, -1.2), (5.5, 8.8), (-4.0, 8.9)])
    bake(kit, root, p)


def block_candy(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} walk", -9.6, -4.0, 1.2, -2.4, sidewalk(kit))
    pad(kit, root, f"{p} path", -5.2, -HALF, -3.8, -4.0, sidewalk(kit))
    at(kit, d, road.candy_shop, f"{p} shop", -4.6, 2.2, -90)
    at(kit, d, tool_shed, f"{p} shed", 6.2, 6.4)
    at(kit, d, picnic_table, f"{p} picnic", 4.6, 0.8, 10)
    at(kit, d, bench, f"{p} bench", -7.4, -5.2)
    at(kit, d, phone_booth, f"{p} phone", 1.8, -3.2)
    at(kit, d, road.burnt_pickup, f"{p} pickup", 6.6, -5.2, 15)
    at(kit, d, road.round_tree, f"{p} tree", 8.4, 1.6, 20)
    at(kit, d, road.bush, f"{p} bush 0", 2.2, 7.8)
    at(kit, d, road.bush, f"{p} bush 1", -1.4, -7.6, 100)
    grass_tufts(kit, d, p, [(-9.0, -8.6), (9.0, -9.0), (3.0, 4.6)])
    bake(kit, root, p)


def block_apartments(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} walk", -9.6, -3.8, 9.6, -1.0, sidewalk(kit))
    pad(kit, root, f"{p} path", -0.8, -HALF, 0.8, -3.8, sidewalk(kit))
    at(kit, d, apartment, f"{p} apartment", 0, 3.0)
    at(kit, d, dumpster, f"{p} dumpster", 8.0, 4.6, -90)
    at(kit, d, barrel_stack, f"{p} barrels", -8.4, 5.4, 30)
    at(kit, d, tire_pile, f"{p} tires", 8.2, -6.6, 20)
    at(kit, d, bench, f"{p} bench", -4.0, -3.0, 0, z=SIDE + 0.012)
    at(kit, d, road.trash_can, f"{p} trash", 2.4, -3.2, 0, z=SIDE + 0.012)
    at(kit, d, road.street_lamp, f"{p} lamp", -7.4, -1.6, 0, z=SIDE + 0.012)
    at(kit, d, road.round_tree, f"{p} tree", -7.6, -7.2, 50)
    at(kit, d, road.pine_tree, f"{p} pine", 8.6, 8.8)
    at(kit, d, road.bush, f"{p} bush", 3.4, -7.4)
    grass_tufts(kit, d, p, [(-3.4, -8.2), (6.0, -9.2), (-9.0, 9.0)])
    bake(kit, root, p)


def block_ruins(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} rubble lot", -2.0, -9.0, 9.4, 1.0, dirt(kit))
    at(kit, d, road.boarded_building, f"{p} building", -4.2, 2.5, -90)
    at(kit, d, school_bus, f"{p} bus", 5.4, 0.8, 12)
    at(kit, d, road.barricade, f"{p} barricade 0", -1.2, -6.8, 10)
    at(kit, d, road.barricade, f"{p} barricade 1", 1.6, -7.9, -15)
    for i, (x, y) in enumerate(((-3.4, -7.6), (3.8, -8.6), (0.2, -5.2))):
        at(kit, d, road.traffic_cone, f"{p} cone {i}", x, y, i * 40)
    at(kit, d, barrel_stack, f"{p} barrels", -7.8, -6.2, 200)
    at(kit, d, tire_pile, f"{p} tires", -1.6, 8.0, 60)
    at(kit, d, dead_tree, f"{p} dead tree", 8.4, 8.0, 120)
    at(kit, d, boulders, f"{p} rubble", 1.4, -2.6, 30, 0.6)
    grass_tufts(kit, d, p, [(-9.2, -9.0), (-6.0, 8.8), (9.0, -6.5)])
    bake(kit, root, p)


def block_park(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    walk = sidewalk(kit)
    pad(kit, root, f"{p} path front", -0.9, -HALF, 0.9, -2.0, walk)
    pad(kit, root, f"{p} plaza", -2.8, -2.0, 2.8, 4.2, walk)
    pad(kit, root, f"{p} path side", -HALF, 0.4, -2.8, 1.8, walk)
    at(kit, d, cone_statue, f"{p} statue", 0, 1.1)
    at(kit, d, bench, f"{p} bench 0", -2.2, 1.1, 90, z=SIDE + 0.012)
    at(kit, d, bench, f"{p} bench 1", 2.2, 1.1, -90, z=SIDE + 0.012)
    at(kit, d, bench, f"{p} bench 2", 0, 3.6, 180, z=SIDE + 0.012)
    at(kit, d, picnic_table, f"{p} picnic 0", -6.4, 6.6, 15)
    at(kit, d, picnic_table, f"{p} picnic 1", 6.2, 6.8, -10)
    at(kit, d, road.round_tree, f"{p} tree 0", -7.4, -6.4, 0)
    at(kit, d, road.round_tree, f"{p} tree 1", 7.6, -4.4, 120)
    at(kit, d, road.round_tree, f"{p} tree 2", 7.4, 2.4, 200)
    at(kit, d, road.pine_tree, f"{p} pine", -3.6, 8.4)
    at(kit, d, road.bush, f"{p} bush 0", -3.2, -6.4)
    at(kit, d, road.bush, f"{p} bush 1", 3.4, -7.6, 80)
    at(kit, d, road.trash_can, f"{p} trash", 1.6, -3.4)
    at(kit, d, road.street_lamp, f"{p} lamp", -1.6, -6.0, 180)
    grass_tufts(kit, d, p, [(-8.8, -1.6), (9.0, 9.0), (4.4, -0.6), (-6.4, 3.4)])
    bake(kit, root, p)


def block_cemetery(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} path", -0.9, -HALF, 0.9, 4.2, dirt(kit))
    for a, b in (((-9.6, -9.2), (-2.4, -9.2)), ((2.4, -9.2), (9.6, -9.2)), ((-9.6, -9.2), (-9.6, 9.4)), ((9.6, -9.2), (9.6, 9.4))):
        fence_line(kit, d, iron_fence, f"{p} fence {a[0]} {b[1]}", a, b, 2.5, iron_post(kit))
    st = stone(kit)
    for sx in (1, -1):
        tbox(kit, f"{p} gate pillar {sx}", (sx * 2.2, -9.2, SIDE + 1.0), (0.5, 0.5, 2.0), st, d, uv={'all': (0, 0, 0.5, 2)})
        lowball(kit, f"{p} gate ball {sx}", (sx * 2.2, -9.2, SIDE + 2.2), (0.24, 0.24, 0.24), st, d, smooth=False)
    words = ("RIP", "MOM", "DAD", "BOB", "SAL", "RIP")
    open_slots = {(5.0, -1.6), (-5.0, 1.8)}
    for j, y in enumerate((-5.2, -1.6, 1.8)):
        for i, x in enumerate((-7.6, -5.0, -2.6, 2.6, 5.0, 7.6)):
            name = f"{p} grave {i} {j}"
            if (x, y) in open_slots:
                at(kit, d, open_grave, name, x, y, R.uniform(-8, 8))
            else:
                kind = (i + 2 * j) % 3
                at(kit, d, lambda k, r, n, kind=kind, w=words[(i * 3 + j) % 6]: gravestone(k, r, n, kind, w), name,
                   x + R.uniform(-0.2, 0.2), y + 0.7 + R.uniform(-0.2, 0.2), R.uniform(-10, 10))
    at(kit, d, mausoleum, f"{p} mausoleum", 0, 6.4)
    at(kit, d, dead_tree, f"{p} dead tree 0", -7.6, 6.6, 40)
    at(kit, d, dead_tree, f"{p} dead tree 1", 7.4, 7.2, 200, 0.85)
    grass_tufts(kit, d, p, [(-4.4, 8.6), (4.6, 8.8), (8.8, -7.0)])
    bake(kit, root, p)


def block_barn(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} drive", -4.4, -HALF, 0.8, -0.4, dirt(kit))
    stops.barn(kit, kit.empty(f"{p} barn", d, (-1.5, -0.5, SIDE), (0, 0, 90)), (0, 0, 0))
    at(kit, d, silo, f"{p} silo", 6.4, 5.0)
    at(kit, d, road.hay_bale, f"{p} hay 0", 5.0, -3.0, 20)
    at(kit, d, road.hay_bale, f"{p} hay 1", 6.8, -1.0, -10)
    hay = tm(kit, "square hay", lambda: stops.tex_hay(R), 0.32, 'REPEAT')
    for i, (x, y, z, rz) in enumerate(((-7.6, 1.6, 0, 0), (-7.6, 2.2, 0, 0), (-7.6, 1.9, 0.42, 4), (-6.5, 1.9, 0, 90))):
        stops.square_bale(kit, d, f"{p} bale {i}", (x, y, SIDE + z), rz, hay)
    fence_line(kit, d, split_rail, f"{p} fence left", (-9.6, -9.2), (-5.0, -9.2), 3.0, rail_post(kit))
    fence_line(kit, d, split_rail, f"{p} fence right", (1.4, -9.2), (9.6, -9.2), 3.0, rail_post(kit))
    stops.cow(kit, d, f"{p} cow 0", (6.8, -6.4, SIDE), 30, zombie=True)
    stops.cow(kit, d, f"{p} cow 1", (3.6, -7.0, SIDE), -70)
    at(kit, d, tool_shed, f"{p} shed", -7.8, 7.6, 90)
    grass_tufts(kit, d, p, [(-9.0, -6.2), (2.6, -4.4), (9.0, 1.6), (3.6, 8.8)])
    bake(kit, root, p)


def block_cornfield(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    for i, x in enumerate((-7.5, -3.3, 3.3, 7.5)):
        for j, y in enumerate((-0.6, 3.8)):
            at(kit, d, corn_patch, f"{p} corn {i} {j}", x, y)
    pad(kit, root, f"{p} lane", -1.1, -HALF, 1.1, 6.0, dirt(kit))
    at(kit, d, scarecrow, f"{p} scarecrow", 0, 1.6, 10)
    fence_line(kit, d, split_rail, f"{p} fence left", (-9.6, -8.8), (-1.6, -8.8), 3.0, rail_post(kit))
    fence_line(kit, d, split_rail, f"{p} fence right", (1.6, -8.8), (9.6, -8.8), 3.0, rail_post(kit))
    at(kit, d, road.hay_bale, f"{p} hay 0", -6.0, 8.2, 80)
    at(kit, d, road.hay_bale, f"{p} hay 1", -3.4, 8.6, 95)
    at(kit, d, dead_tree, f"{p} dead tree", 6.4, 8.0, 10)
    at(kit, d, boulders, f"{p} rocks", 6.8, -6.0, 40, 0.7)
    grass_tufts(kit, d, p, [(-8.6, -5.4), (-4.6, -6.6), (3.6, -5.8), (9.0, -3.6), (1.6, 8.6)])
    bake(kit, root, p)


def block_water_tower(kit, root, p):
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    pad(kit, root, f"{p} gravel", -1.6, -0.6, 4.6, 5.6, dirt(kit))
    pad(kit, root, f"{p} track", 0.4, -HALF, 2.6, -0.6, dirt(kit))
    at(kit, d, water_tower, f"{p} tower", 1.5, 2.5)
    at(kit, d, tool_shed, f"{p} shed", -6.6, 5.4)
    fence_line(kit, d, split_rail, f"{p} fence left", (-9.6, -9.0), (-0.4, -9.0), 3.0, rail_post(kit))
    fence_line(kit, d, split_rail, f"{p} fence right", (3.6, -9.0), (9.6, -9.0), 3.0, rail_post(kit))
    at(kit, d, boulders, f"{p} rocks 0", -6.8, -4.4, 0)
    at(kit, d, boulders, f"{p} rocks 1", 7.6, -1.4, 120, 0.8)
    at(kit, d, tire_pile, f"{p} tires", 7.0, 7.6, 200)
    at(kit, d, barrel_stack, f"{p} barrels", -2.8, 8.0, 90)
    at(kit, d, dead_tree, f"{p} dead tree", -7.8, -0.2, 300)
    at(kit, d, road.bush, f"{p} bush", 5.6, -6.0)
    grass_tufts(kit, d, p, [(-4.0, -6.0), (-1.4, -3.0), (6.6, 3.0), (-8.8, 8.6), (8.8, -8.2), (4.4, -3.6)])
    bake(kit, root, p)


def block_forest(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    taken = []
    for i, (x, y) in enumerate(scatter(R, 10, -8.8, 8.8, -8.8, 8.8, 3.2, taken)):
        at(kit, d, road.pine_tree, f"{p} pine {i}", x, y, R.uniform(0, 360), R.uniform(0.8, 1.35))
    for i, (x, y) in enumerate(scatter(R, 3, -8.6, 8.6, -8.6, 8.6, 3.4, taken)):
        at(kit, d, road.round_tree, f"{p} tree {i}", x, y, R.uniform(0, 360), R.uniform(0.85, 1.1))
    for i, (x, y) in enumerate(scatter(R, 2, -8.6, 8.6, -8.6, 8.6, 2.0, taken)):
        at(kit, d, dead_tree, f"{p} dead {i}", x, y, R.uniform(0, 360), R.uniform(0.8, 1.0))
    for i, (x, y) in enumerate(scatter(R, 3, -9, 9, -9, 9, 1.6, taken)):
        at(kit, d, boulders, f"{p} rocks {i}", x, y, R.uniform(0, 360), R.uniform(0.5, 0.9))
    for i, (x, y) in enumerate(scatter(R, 5, -9, 9, -9, 9, 1.2, taken)):
        at(kit, d, road.bush, f"{p} bush {i}", x, y, R.uniform(0, 360), R.uniform(0.8, 1.1))
    grass_tufts(kit, d, p, scatter(R, 8, -9.3, 9.3, -9.3, 9.3, 0.8, taken))
    bake(kit, root, p)


def block_meadow(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    d = kit.empty(f"{p} props", root)
    at(kit, d, billboard, f"{p} billboard", 0.4, -4.2)
    at(kit, d, road.wrecked_sedan, f"{p} sedan", 6.6, 0.8, 70)
    for i, (x, y, rz) in enumerate(((-6.0, 3.0, 20), (-4.2, 5.4, -30), (-7.4, 6.4, 80))):
        at(kit, d, road.hay_bale, f"{p} hay {i}", x, y, rz)
    stops.cow(kit, d, f"{p} cow 0", (2.8, 5.4, SIDE), 120, zombie=True)
    stops.cow(kit, d, f"{p} cow 1", (-1.6, 8.2, SIDE), 200)
    at(kit, d, boulders, f"{p} rocks", 7.4, -6.8, 60)
    at(kit, d, dead_tree, f"{p} dead tree", -7.6, -6.6, 140)
    at(kit, d, road.pine_tree, f"{p} pine", 8.2, 8.0, 0, 1.1)
    taken = [(0.4, -4.2, 4.0), (6.6, 0.8, 3.0), (-6.0, 4.6, 2.6), (2.8, 5.4, 1.8), (-1.6, 8.2, 1.8), (7.4, -6.8, 1.6),
             (-7.6, -6.6, 1.4), (8.2, 8.0, 2.0)]
    grass_tufts(kit, d, p, scatter(R, 12, -9.3, 9.3, -9.3, 9.3, 1.0, taken))
    bake(kit, root, p)


def block_side_street(kit, root, p):
    """The road leaving a T junction: enters at y = -10 (asphalt |x| <= 4, like the chunk) and dead-ends at a barricade."""
    mb = MB()
    mb.prism(rect(-road.ROAD, -HALF, road.ROAD, 5.0), BOT, 0.0, road.G_ASPH, road.S_ASPH)
    for sx in (1, -1):
        road.town_side(mb, sx)
    road.lawn(mb, rect(-road.ROAD, 5.0, road.ROAD, HALF))
    mb.obj(kit, f"{p} ground", road.ground_mats(kit), root)
    road.paint(kit, root, p, [[(sx * road.LINE_X, -HALF), (sx * road.LINE_X, 5.0)] for sx in (1, -1)],
               [[(0, y + 1), (0, y - 1)] for y in (-8, -4, 0)])
    d = kit.empty(f"{p} props", root)
    for i, x in enumerate((-2.7, 0.0, 2.7)):
        at(kit, d, road.barricade, f"{p} barricade {i}", x, 3.6, 0, z=0.0)
    for i, (x, y) in enumerate(((-1.6, 2.0), (1.2, 1.4), (3.2, 2.4))):
        at(kit, d, road.traffic_cone, f"{p} cone {i}", x, y, i * 50, z=0.0)
    at(kit, d, road.wrecked_sedan, f"{p} sedan", -1.6, -3.2, 160, z=0.0)
    fence_line(kit, d, road.chainlink_fence, f"{p} chainlink", (-5.0, 5.2), (5.0, 5.2), 2.5,
               (solid(kit, "chain steel", "#c9c2f0", shade="#a9a2e0"), 0.09, 1.95))
    at(kit, d, road.burnt_pickup, f"{p} pickup", 1.4, 7.6, 80)
    at(kit, d, road.zombies_sign, f"{p} sign", -5.6, -6.0)
    at(kit, d, road.street_lamp, f"{p} lamp 0", 4.7, -1.0, -90)
    at(kit, d, road.street_lamp, f"{p} lamp 1", -4.7, 6.0, 90)
    at(kit, d, road.fire_hydrant, f"{p} hydrant", 4.75, -7.0, -90)
    at(kit, d, road.trash_can, f"{p} trash", -5.3, 2.0, 30)
    at(kit, d, road.pine_tree, f"{p} pine 0", -2.6, 8.6)
    at(kit, d, road.round_tree, f"{p} tree", 8.4, 6.4, 60)
    at(kit, d, road.bush, f"{p} bush 0", -8.6, -8.0)
    at(kit, d, road.bush, f"{p} bush 1", 8.6, -4.0, 40)
    bake(kit, root, p)


# ---------------------------------------------------------------- extra dressing for the plain road chunks (chunk coordinates)
def town_dressing(kit, root, p):
    d = kit.empty(f"{p} props", root)
    at(kit, d, bus_stop, f"{p} bus stop", 6.0, -1.0, -90)
    at(kit, d, bench, f"{p} bench", -5.7, 1.2, 90)
    at(kit, d, phone_booth, f"{p} phone", -6.2, 7.4, 90)
    at(kit, d, dumpster, f"{p} dumpster", -8.7, -1.6, 90)
    at(kit, d, road.round_tree, f"{p} tree", 8.6, -4.4, 10)
    at(kit, d, road.pine_tree, f"{p} pine", -8.8, 4.6, 0, 0.9)
    grass_tufts(kit, d, p, [(8.2, 2.6), (-8.2, -4.6), (9.0, 9.2)])
    bake(kit, root, p)


def rural_dressing(kit, root, p):
    d = kit.empty(f"{p} props", root)
    for sx in (1, -1):
        fence_line(kit, d, split_rail, f"{p} fence {sx}", (sx * 9.5, -9.8), (sx * 9.5, 9.8), 3.0, rail_post(kit))
    at(kit, d, boulders, f"{p} rocks", -7.6, -4.4, 30, 0.7)
    at(kit, d, dead_tree, f"{p} dead tree", 7.2, 8.0, 200)
    at(kit, d, tire_pile, f"{p} tires", -5.9, -8.0, 40)
    grass_tufts(kit, d, p, [(6.4, -3.6), (-5.8, 3.4), (7.6, 6.0), (-7.4, 9.0), (5.8, 0.4)])
    bake(kit, root, p)


def curve_dressing(kit, root, p):
    """Curve Left coordinates; the game mirrors it with the road for right turns, so nothing here carries text."""
    d = kit.empty(f"{p} props", root)
    at(kit, d, dead_tree, f"{p} dead tree", -8.6, -4.2, 70)
    at(kit, d, boulders, f"{p} rocks 0", 2.6, -8.4, 10)
    at(kit, d, boulders, f"{p} rocks 1", -4.0, -2.4, 160, 0.6)
    at(kit, d, tire_pile, f"{p} tires", -8.4, 7.6, 0)
    at(kit, d, barrel_stack, f"{p} barrels", -7.6, -7.4, 30)
    at(kit, d, road.pine_tree, f"{p} pine", 4.4, -4.6, 0, 0.8)
    grass_tufts(kit, d, p, [(0.4, -6.0), (-6.0, 0.4), (-2.4, -5.2), (8.4, 9.0), (6.4, -8.8)])
    bake(kit, root, p)


def junction_dressing(kit, root, p):
    d = kit.empty(f"{p} props", root)
    at(kit, d, bench, f"{p} bench", -5.7, 3.0, 90)
    at(kit, d, phone_booth, f"{p} phone", -6.3, -6.6, 90)
    at(kit, d, dumpster, f"{p} dumpster", -8.7, 4.4, 90)
    at(kit, d, road.round_tree, f"{p} tree", -8.6, -1.8, 140)
    grass_tufts(kit, d, p, [(-8.6, -8.8), (-8.8, 8.8), (9.0, 9.0)])
    bake(kit, root, p)


def broken_dressing(kit, root, p):
    d = kit.empty(f"{p} props", root)
    at(kit, d, road.wrecked_sedan, f"{p} sedan", 7.9, -4.0, 10)
    at(kit, d, barrel_stack, f"{p} barrels", 6.0, 3.4, 250)
    at(kit, d, tire_pile, f"{p} tires", -8.2, 2.0, 80)
    at(kit, d, dead_tree, f"{p} dead tree", -8.6, -3.0, 20)
    at(kit, d, phone_booth, f"{p} phone", 6.2, 8.2, -90)
    grass_tufts(kit, d, p, [(8.6, 7.4), (-8.6, -8.6), (-8.0, 8.4)])
    bake(kit, root, p)


BLOCKS = [("Block Houses", block_houses), ("Block Diner", block_diner), ("Block Candy Shop", block_candy),
          ("Block Apartments", block_apartments), ("Block Ruins", block_ruins), ("Block Park", block_park),
          ("Block Cemetery", block_cemetery), ("Block Barn", block_barn), ("Block Cornfield", block_cornfield),
          ("Block Water Tower", block_water_tower), ("Block Forest", block_forest), ("Block Meadow", block_meadow),
          ("Block Side Street", block_side_street)]
DRESSING = [("Town Straight Dressing", town_dressing), ("Rural Straight Dressing", rural_dressing),
            ("Curve Dressing", curve_dressing), ("Junction Dressing", junction_dressing), ("Broken Road Dressing", broken_dressing)]


ASSET_FNS = [
    ("Diner", diner), ("Brick Apartment", apartment), ("Water Tower", water_tower), ("Silo", silo), ("Tool Shed", tool_shed),
    ("Billboard", billboard), ("Bus Stop", bus_stop), ("Bench", bench), ("Picnic Table", picnic_table),
    ("Phone Booth", phone_booth), ("Dumpster", dumpster), ("Tire Pile", tire_pile), ("Barrel Stack", barrel_stack),
    ("School Bus Wreck", school_bus), ("Dead Tree", dead_tree), ("Boulders", boulders), ("Tall Grass", tall_grass),
    ("Corn Patch", corn_patch), ("Split Rail Fence", split_rail), ("Scarecrow", scarecrow), ("Cone Statue", cone_statue),
    ("Gravestone", lambda k, r, n: gravestone(k, r, n, 0, "RIP")), ("Gravestone Cross", lambda k, r, n: gravestone(k, r, n, 1)),
    ("Open Grave", open_grave), ("Mausoleum", mausoleum), ("Iron Fence", iron_fence),
] + BLOCKS + DRESSING
ASSETS = [(n, (lambda f, n: lambda kit, root: f(kit, root, n))(f, n)) for n, f in ASSET_FNS]


def dressed_chunks(kit, root):
    for i, (chunk, dress) in enumerate(((road.town_straight, town_dressing), (road.rural_straight, rural_dressing),
                                        (road.curve_left, curve_dressing), (road.t_junction, junction_dressing),
                                        (road.broken_road, broken_dressing))):
        c = kit.empty(f"dressed {i}", root, (i * 22, 0, 0))
        chunk(kit, kit.empty(f"dressed {i} road", c), f"dressed {i} road")
        dress(kit, kit.empty(f"dressed {i} extra", c), f"dressed {i} extra")


def neighborhood(kit, root):
    """Town straight, T junction, town straight with blocks on both sides and the side street off the junction."""
    for y, chunk, dress, nm in ((-20, road.town_straight, town_dressing, "a"), (0, road.t_junction, junction_dressing, "b"),
                                (20, road.town_straight, town_dressing, "c")):
        c = kit.empty(f"hood {nm}", root, (0, y, 0))
        chunk(kit, kit.empty(f"hood {nm} road", c), f"hood {nm} road")
        dress(kit, kit.empty(f"hood {nm} extra", c), f"hood {nm} extra")
    for x, y, rz, fn in ((20, -20, -90, block_houses), (20, 0, -90, block_side_street), (20, 20, -90, block_diner),
                         (-20, -20, 90, block_apartments), (-20, 0, 90, block_park), (-20, 20, 90, block_candy),
                         (40, -20, -90, block_cemetery), (40, 0, -90, block_forest), (40, 20, -90, block_ruins),
                         (-40, -20, 90, block_forest), (-40, 0, 90, block_houses), (-40, 20, 90, block_cornfield)):
        fn(kit, kit.empty(f"hood block {x} {y}", root, (x, y, 0), (0, 0, rz)), f"hood block {x} {y}")


SCENES = [dict(name="dressed chunks", build=dressed_chunks, cam=((44, -40, 38), (44, 0, 0), 30), res=(1800, 900)),
          dict(name="neighborhood", build=neighborhood, cam=((0, -38, 9), (0, 14, 1), 28), res=(1600, 900)),
          dict(name="neighborhood above", build=neighborhood, cam=((-6, -60, 70), (5, 2, 0), 30), res=(1600, 1000))]
