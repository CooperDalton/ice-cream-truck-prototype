"""Divorced Dads town (style H): the Crossroads chunk, the Creek Fill cell, and the 40 x 40 m blocks between roads.

Road cells reuse h_road's Town Straight / T Junction / Curve Left. Crossroads follows the same chunk contract
(20 x 20 m, asphalt |x|, |y| <= 4 at z = 0, curbs, sidewalks out to 7 m, lawn at z = 0.15). Creek Fill is a 20 x 20 m
lawn cell (top z = 0.15) with a creek along X, a footbridge along Y and fences on the -Y and +Y edges.

Blocks: origin at the block center at road level (z = 0), ground slab from z = -0.25 to the roadside height z = 0.15 so
it meets the road cells' lawn strips flush. Front faces -Y. Every building is baked to one mesh ('<Block> <building>
mesh'), props to '<Block> props mesh', ground to '<Block> ground'. Buildings are solid from the slab up past 1.9 m;
yards, paths and lots stay below 0.4 m. Sockets: '<Block> socket <name> <i>' at ground level (z = 0.15)."""
from style_H import *
import h_road as road
import h_stops as stops
from h_road import (MB, rect, tm, place, SIDE, BOT, HALF, ROAD, CURB_W, WALK_X, LINE_X, DASHES, ground_mats, walk, lawn,
                    curbs, offset, resample, arc, paint, window_px, bricks, tex_shingles, roof_plane, cut_mat, tex_chain)
from h_stops import block as sblock, prism, slab
from h_dads_characters import lathe, torus, txt, txt_c, FONT2
from h_dads_items import FLV, acorn

SPACING = 60
B2 = 20.0   # block half size

GRASS_G, DIRT_G, SOIL_G = 2, 3, 4
LEAF = ("#2fae66", "#3fcf7a", "#26995a")
WATER = "#4fa8ff"


# ---------------------------------------------------------------- generic helpers
def asset(root):
    return root.name[:-5] if root.name.endswith(" root") else root.name


def socket(kit, root, purpose, loc, rz=0.0):
    s = kit.empty(f"{asset(root)} socket {purpose}", root, loc, (0, 0, rz))
    s.empty_display_size = 0.4
    return s


def bake(kit, root, p):
    """Join every mesh below root into '<p> mesh' (a direct child of root) and drop everything else below root."""
    bpy.context.view_layer.update()
    meshes = [o for o in root.children_recursive if o.type == 'MESH']
    me = bpy.data.meshes.new(f"{p} mesh")
    me.uv_layers.new(name="UVMap")
    target = kit.link(f"{p} mesh", me, root)
    with bpy.context.temp_override(active_object=target, selected_editable_objects=[target] + meshes):
        bpy.ops.object.join()
    for o in list(root.children_recursive):
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


def bake_props(kit, root, props, p):
    """Bake the props pivot and move the mesh straight under root (no leftover pivot)."""
    m = bake(kit, props, f"{p} props")
    bpy.context.view_layer.update()
    mw = m.matrix_world.copy()
    m.parent = root
    m.matrix_world = mw
    bpy.data.objects.remove(props)
    return m


def baked(kit, root, name, loc=(0, 0, 0), rz=0.0, build=None):
    """Build into a temporary pivot, bake it, then move the mesh directly under root (keeping its world transform)."""
    piv = kit.empty(name, root, loc, (0, 0, rz))
    build(piv)
    m = bake(kit, piv, name)
    bpy.context.view_layer.update()
    mw = m.matrix_world.copy()
    m.parent = root
    m.matrix_world = mw
    bpy.data.objects.remove(piv)
    return m


def pad(kit, parent, name, x0, y0, x1, y1, mat, tile=2.0, z=0.012):
    return tbox(kit, name, ((x0 + x1) / 2, (y0 + y1) / 2, SIDE + z / 2), (x1 - x0, y1 - y0, z), mat, parent,
                uv={'all': (x0 / tile, y0 / tile, x1 / tile, y1 / tile)})


def at(kit, d, fn, name, x, y, rz=0.0, scale=1.0, z=SIDE):
    return place(kit, fn, d, name, (x, y, z), rz, scale=scale)


def tex_picket_cut():
    c = Canvas(16, 32, road.CUT)
    c.rect(3, 0, 12, 27, WHITE); c.rect(4, 28, 11, 29, WHITE); c.rect(6, 30, 9, 31, WHITE)
    c.rect(11, 0, 12, 27, "#e6dcd2")
    c.rect(0, 8, 15, 10, MINT); c.rect(0, 20, 15, 22, MINT)
    c.rect(0, 8, 15, 8, "#22c79c"); c.rect(0, 20, 15, 20, "#22c79c")
    return c


def panel(kit, d, name, a, b, z0, z1, mat, u_len, v_len=None):
    """One vertical quad from a to b (two-sided cut-out material), u repeats every u_len meters."""
    mb = MB()
    L = (Vector(b) - Vector(a)).length
    v0, v1 = (0.01, 0.99) if v_len is None else (z0 / v_len, z1 / v_len)
    mb.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)],
            [(0, v0), (L / u_len, v0), (L / u_len, v1), (0, v1)], 0)
    return mb.obj(kit, name, [mat], d)


def fence_line(kit, d, fn, name, a, b, seg, post=None):
    """Cheap fence run from a to b: one cut-out panel plus posts (picket: every ~4 m, chain-link: every ~2.5 m)."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    if fn is road.chainlink_fence:
        steel = solid(kit, "chain steel", "#c9c2f0", shade="#a9a2e0")
        panel(kit, d, f"{name} mesh", a, b, SIDE + 0.05, SIDE + 1.8, cut_mat(kit, "chain link", tex_chain), 0.3, 0.3)
        n = max(1, round(L / 2.5))
        for i in range(n + 1):
            q = a.lerp(b, i / n)
            tube(kit, f"{name} post {i}", [(q.x, q.y, SIDE), (q.x, q.y, SIDE + 1.95)], 0.045, steel, d, sides=5, caps=(False, True))
        tube(kit, f"{name} top rail", [(a.x, a.y, SIDE + 1.82), (b.x, b.y, SIDE + 1.82)], 0.025, steel, d, sides=4,
             caps=(False, False))
    else:
        fw = solid(kit, "fence", WHITE, 0.35)
        panel(kit, d, f"{name} mesh", a, b, SIDE + 0.02, SIDE + 0.95, cut_mat(kit, "picket cut", tex_picket_cut), 0.4)
        n = max(1, round(L / 4.0))
        u = (b - a).normalized()
        rz = math.degrees(math.atan2(u.y, u.x))
        for i in range(n + 1):
            q = a.lerp(b, i / n)
            tbox(kit, f"{name} post {i}", (q.x, q.y, SIDE + 0.55), (0.1, 0.1, 1.1), fw, d, rot=(0, 0, rz))
    if post and fn is not road.chainlink_fence and fn is not road.picket_fence:
        tbox(kit, f"{name} end post", (b.x, b.y, SIDE + post[2] / 2), (post[1], post[1], post[2]), post[0], d)


def fence_gaps(kit, d, fn, name, a, b, seg, gaps, post=None):
    """fence_line from a to b leaving open gaps [(t0, t1)] given as distances along the line."""
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    u = (b - a) / L
    cuts, t = [], 0.0
    for g0, g1 in sorted(gaps):
        if g0 > t + 0.5:
            cuts.append((t, g0))
        t = g1
    if L > t + 0.5:
        cuts.append((t, L))
    for i, (t0, t1) in enumerate(cuts):
        fence_line(kit, d, fn, f"{name} {i}", tuple(a + u * t0), tuple(a + u * t1), seg, post)


def picket_post(kit):
    return solid(kit, "fence", WHITE, 0.35), 0.1, 1.1


def chain_post(kit):
    return solid(kit, "chain steel", "#c9c2f0", shade="#a9a2e0"), 0.09, 1.95


def leaf_mat(kit, i=0):
    return tm(kit, "leaf " + LEAF[i % 3], lambda: road.tex_leaf(kit.rand, LEAF[i % 3]), 0.3)


def ground(kit, root, p, kind=GRASS_G, half=B2, shift=2.0):
    """Lawn (or dirt) slab like the road chunk roadside. UVs use block coordinates shifted by 2 m so the 4 m grass tile
    lines up with the neighboring road cells (whose centers sit 30 m from the block center)."""
    mb = MB()
    mb.prism(rect(-half + shift, -half + shift, half + shift, half + shift), BOT, SIDE, kind, 0.25, SOIL_G)
    return mb.obj(kit, f"{p} ground", ground_mats(kit), root, loc=(-shift, -shift, 0))


def tex_front(rand, w, h, base, shade, draw):
    c = Canvas(w, h, base)
    c.speckle(rand, [shade], w * h // 14)
    draw(c)
    return c


def plate(kit, name, parent, center, size, mat, face='ny'):
    """Thin decal box; only `face` shows the full texture."""
    return tbox(kit, name, center, size, mat, parent, uv={'all': (0.0, 0.0, 0.02, 0.02), face: (0, 0, 1, 1)})


def sign_tex(text, w, h, bg, fg, k=2, border=None, shadow=None, lines=None):
    c = Canvas(w, h, bg)
    if border:
        c.rect(0, 0, w - 1, 1, border); c.rect(0, h - 2, w - 1, h - 1, border)
        c.rect(0, 0, 1, h - 1, border); c.rect(w - 2, 0, w - 1, h - 1, border)
    rows = lines or [text]
    total = len(rows) * 6 * k - k
    y = h // 2 + total // 2
    for row in rows:
        txt_c(c, row, w // 2, y, fg, k, shadow)
        y -= 6 * k
    return c


# ---------------------------------------------------------------- 1. Crossroads
def rot90(pts, k):
    out = []
    for p in pts:
        x, y = p[0], p[1]
        for _ in range(k % 4):
            x, y = -y, x
        out.append((x, y))
    return out


def corner(mb, sx, sy):
    f = lambda poly: [(sx * x, sy * y) for x, y in poly]
    path = resample([(ROAD, HALF), (ROAD, 6.0)]) + arc((6.0, 6.0), 2.0, 180, 270, 6)[1:] + resample([(6.0, ROAD), (HALF, ROAD)])[1:]
    curbs(mb, path, CURB_W, f)
    walk(mb, f(offset(path, CURB_W) + [(HALF, WALK_X), (WALK_X, WALK_X), (WALK_X, HALF)]))
    lawn(mb, f(rect(WALK_X, WALK_X, HALF, HALF)))


def crossroads(kit, root, p):
    mb = MB()
    plus = [(-ROAD, -HALF), (ROAD, -HALF), (ROAD, -ROAD), (HALF, -ROAD), (HALF, ROAD), (ROAD, ROAD), (ROAD, HALF), (-ROAD, HALF),
            (-ROAD, ROAD), (-HALF, ROAD), (-HALF, -ROAD), (-ROAD, -ROAD)]
    mb.prism(plus, BOT, 0.0, 0, 0.2)
    for sx in (1, -1):
        for sy in (1, -1):
            corner(mb, sx, sy)
    mb.obj(kit, f"{p} ground", ground_mats(kit), root)
    white, yellow, bars = [], [], []
    for k in range(4):
        white += [rot90([(LINE_X, 7.6), (LINE_X, HALF)], k), rot90([(-LINE_X, 7.6), (-LINE_X, HALF)], k)]
        yellow += [rot90([(0, 9.8), (0, 8.2)], k)]
        bars += [(rot90([(-3.25 + i * 0.93, 6.8), (-3.25 + i * 0.93, 5.2)], k), 0.5) for i in range(8)]
        bars += [(rot90([(-3.7, 7.35), (-0.25, 7.35)], k), 0.4)]
    paint(kit, root, p, white, yellow, bars)
    road.sockets(kit, root, p, [("exit", (0, -HALF, 0), 0), ("exit left", (HALF, 0, 0), 90), ("exit right", (-HALF, 0, 0), -90)])
    d = kit.empty(f"{p} dressing", root)
    for k in range(4):
        (x, y), = rot90([(-5.4, 7.6)], k)
        place(kit, road.stop_sign, d, f"{p} stop sign {k}", (x, y, SIDE), 180 + 90 * k)
    for k, (x, y, rz) in enumerate(((5.0, 8.3, -90), (-5.0, -8.3, 90))):
        place(kit, road.street_lamp, d, f"{p} lamp {k}", (x, y, SIDE), rz)
    place(kit, road.fire_hydrant, d, f"{p} hydrant", (8.0, -5.2, SIDE), 0)
    for k, (x, y) in enumerate(((8.7, 8.7), (-8.7, 8.7), (8.7, -8.7))):
        place(kit, road.bush, d, f"{p} bush {k}", (x, y, SIDE), 40 * k)
    place(kit, road.trash_can, d, f"{p} trash can", (-8.2, -8.0, SIDE), 10)


# ---------------------------------------------------------------- 2. Creek Fill
def tex_water(rand):
    c = Canvas(32, 32, WATER)
    c.speckle(rand, ["#6fbcff", "#3f90e8"], 120)
    for _ in range(8):
        x, y = rand.randrange(32), rand.randrange(32)
        c.rect(x, y, x + 3, y, WHITE)
    return c


def tex_bank(rand):
    c = Canvas(16, 16, "#8a6a4a")
    c.speckle(rand, ["#6e5238", "#a8865e", "#9a92b0"], 90)
    return c


def creek_fill(kit, root, p):
    R = kit.rand
    mats = ground_mats(kit) + [tm(kit, "creek water", lambda: tex_water(R), 0.5, 'REPEAT'),
                               tm(kit, "creek bank", lambda: tex_bank(R), 0.25, 'REPEAT')]
    WAT, BANK = len(mats) - 2, len(mats) - 1
    mb = MB()
    N = 20
    xs = [-HALF + 2 * HALF * i / N for i in range(N + 1)]
    cy = [1.2 * math.sin(x / 20 * 2 * math.pi) for x in xs]   # wiggles, but meets x = +-10 at y = 0
    w_top, w_bed = 2.6, 1.4
    north = [(x, c + w_top) for x, c in zip(xs, cy)]
    south = [(x, c - w_top) for x, c in zip(xs, cy)]
    mb.prism(north + [(HALF, HALF), (-HALF, HALF)], BOT, SIDE, GRASS_G, 0.25, SOIL_G)
    mb.prism([(-HALF, -HALF), (HALF, -HALF)] + south[::-1], BOT, SIDE, GRASS_G, 0.25, SOIL_G)
    for i in range(N):   # sloped banks and bed
        x0, x1 = xs[i], xs[i + 1]
        c0, c1 = cy[i], cy[i + 1]
        for sg in (1, -1):
            a0, a1 = (x0, c0 + sg * w_top, SIDE), (x1, c1 + sg * w_top, SIDE)
            b0, b1 = (x0, c0 + sg * w_bed, -0.2), (x1, c1 + sg * w_bed, -0.2)
            q = [b0, b1, a1, a0] if sg > 0 else [a0, a1, b1, b0]
            mb.face(q, [(x0 * 0.5, 0), (x1 * 0.5, 0), (x1 * 0.5, 0.6), (x0 * 0.5, 0.6)] if sg > 0 else
                    [(x0 * 0.5, 0.6), (x1 * 0.5, 0.6), (x1 * 0.5, 0), (x0 * 0.5, 0)], BANK)
        mb.face([(x0, c0 - w_bed, -0.2), (x1, c1 - w_bed, -0.2), (x1, c1 + w_bed, -0.2), (x0, c0 + w_bed, -0.2)],
                [(0, 0), (1, 0), (1, 1), (0, 1)], BANK)
        mb.face([(x0, c0 - 1.9, -0.05), (x1, c1 - 1.9, -0.05), (x1, c1 + 1.9, -0.05), (x0, c0 + 1.9, -0.05)],
                [(x0 * 0.25, (c0 - 1.9) * 0.25), (x1 * 0.25, (c1 - 1.9) * 0.25), (x1 * 0.25, (c1 + 1.9) * 0.25),
                 (x0 * 0.25, (c0 + 1.9) * 0.25)], WAT)
    for x0, x1 in ((-HALF, -1.0), (1.0, HALF)):   # end caps so the slab reads solid at the cell edges
        pass
    mb.obj(kit, f"{p} ground", mats, root)
    d = kit.empty(f"{p} props", root)
    # gravel path from the -Y edge to the +Y edge over the bridge
    gravel = tm(kit, "gravel", lambda: stops.tex_gravel(R), 0.25, 'REPEAT')
    pad(kit, d, f"{p} path south", -0.8, -HALF, 0.8, -w_top - 0.3, gravel)
    pad(kit, d, f"{p} path north", -0.8, w_top + 0.3, 0.8, HALF, gravel)
    wood = tm(kit, "bridge wood", lambda: stops.tex_wood(R), 0.3, 'REPEAT')
    bridge = kit.empty(f"{p} bridge", d, (0, 0, 0))
    L = 2 * w_top + 1.2
    k = 9
    for i in range(k):   # arched deck planks
        t = (i + 0.5) / k
        y = -L / 2 + L * t
        z = SIDE + 0.08 + 0.45 * math.sin(math.pi * t)
        tbox(kit, f"{p} plank {i}", (0, y, z), (1.9, L / k - 0.04, 0.08), wood, bridge,
             rot=(math.degrees(math.atan(0.45 * math.pi / L * math.cos(math.pi * t))), 0, 0))
    rail = solid(kit, "bridge rail", PINK, 0.38, shade="#e83a8f")
    for sx in (1, -1):
        pts = [(sx * 0.95, -L / 2 + L * t, SIDE + 0.95 + 0.45 * math.sin(math.pi * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)]
        tube(kit, f"{p} rail {sx}", pts, 0.05, rail, bridge, sides=6, caps=(True, True))
        for j, (x, y, z) in enumerate(pts):
            tbox(kit, f"{p} baluster {sx} {j}", (x, y, (z + SIDE) / 2 - 0.1), (0.1, 0.1, z - SIDE + 0.1), wood, bridge)
    # cattails and reeds along the banks
    stem, head = solid(kit, "reed", "#3f9e5a"), solid(kit, "cattail", "#7a4a2a", shade="#5e3418")
    for i in range(16):
        x = -9 + 18 * i / 15 + R.uniform(-0.4, 0.4)
        if abs(x) < 1.6:
            continue
        c = 1.2 * math.sin(x / 20 * 2 * math.pi)
        y = c + (1 if i % 2 else -1) * R.uniform(1.6, 2.4)
        for j in range(3):
            ox, oy = R.uniform(-0.2, 0.2), R.uniform(-0.2, 0.2)
            h = R.uniform(0.9, 1.4)
            tube(kit, f"{p} reed {i} {j}", [(x + ox, y + oy, 0.0), (x + ox * 1.4, y + oy * 1.4, h)], [0.02, 0.012], stem, d, sides=4)
            if j == 0:
                tube(kit, f"{p} cattail {i}", [(x + ox * 1.35, y + oy * 1.35, h - 0.25), (x + ox * 1.4, y + oy * 1.4, h - 0.02)],
                     0.04, head, d, sides=5)
    lily = solid(kit, "lily pad", "#3fcf7a", 0.35)
    for i, x in enumerate((-6.5, -4.0, 4.5, 7.2)):
        c = 1.2 * math.sin(x / 20 * 2 * math.pi)
        splat(kit, f"{p} lily {i}", (x, c + (0.5 if i % 2 else -0.6)), 0.35, lily, d, lobes=7, z=-0.04)
    rock = solid(kit, "creek rock", "#9a92b0", 0.28, shade="#7a72a0")
    for i, (x, dy) in enumerate(((-8, 1.9), (-2.5, -2.0), (3.2, 2.1), (8.5, -1.8), (6.0, 2.2))):
        c = 1.2 * math.sin(x / 20 * 2 * math.pi)
        lowball(kit, f"{p} rock {i}", (x, c + dy, 0.0), (0.45, 0.35, 0.3), rock, d, smooth=False)
    # trees and a bench
    at(kit, d, road.round_tree, f"{p} tree 0", -6.5, 6.5, 30)
    at(kit, d, road.round_tree, f"{p} tree 1", 6.8, -6.2, 200, 0.9)
    at(kit, d, road.pine_tree, f"{p} pine", 7.5, 7.0)
    at(kit, d, road.bush, f"{p} bush 0", -7.0, -6.5)
    at(kit, d, road.bush, f"{p} bush 1", 3.5, 6.8, 80)
    at(kit, d, bench, f"{p} bench", -3.2, -6.0)
    # fence along the road-facing edges (-Y and +Y), open at the path
    for sy in (1, -1):
        fence_gaps(kit, d, road.picket_fence, f"{p} fence {sy}", (-9.8, sy * 9.6), (9.8, sy * 9.6), 2.0, [(8.6, 11.2)],
                   picket_post(kit))
    bake_props(kit, root, d, p)


# ---------------------------------------------------------------- props shared by the blocks
def bench(kit, root, p):
    w = solid(kit, "bench wood", "#e8a862", shade="#c47f3a")
    iron = solid(kit, "bench iron", "#4a3a6e", 0.25)
    for i, z in enumerate((0.45, 0.5)):
        tbox(kit, f"{p} seat {i}", (0, -0.12 + 0.13 * i, z), (1.6, 0.12, 0.05), w, root)
    for i, z in enumerate((0.7, 0.85)):
        tbox(kit, f"{p} back {i}", (0, 0.18, z), (1.6, 0.04, 0.1), w, root)
    for sx in (1, -1):
        tbox(kit, f"{p} leg {sx}", (sx * 0.7, 0.0, 0.25), (0.06, 0.45, 0.5), iron, root)
        tbox(kit, f"{p} arm {sx}", (sx * 0.74, 0.03, 0.62), (0.05, 0.4, 0.05), iron, root)
        tbox(kit, f"{p} back post {sx}", (sx * 0.7, 0.2, 0.62), (0.05, 0.05, 0.5), iron, root)


def swing_set(kit, root, p, seats=3):
    frame = solid(kit, "swing frame", BLUE, 0.4, shade="#1f5fd0")
    chain = solid(kit, "swing chain", STEEL, 0.4)
    W = 1.1 * seats + 0.6
    for sx in (1, -1):
        for sy in (1, -1):
            tube(kit, f"{p} leg {sx} {sy}", [(sx * W / 2, sy * 0.9, 0.0), (sx * W / 2, 0, 2.3)], 0.05, frame, root, sides=6)
    tube(kit, f"{p} top bar", [(-W / 2 - 0.1, 0, 2.3), (W / 2 + 0.1, 0, 2.3)], 0.06, frame, root, sides=6, front=(0, 0, 1))
    cols = (PINK, YEL, MINT, ORNG)
    for i in range(seats):
        x = -W / 2 + 0.6 + 1.1 * i
        for sx in (1, -1):
            tube(kit, f"{p} chain {i} {sx}", [(x + sx * 0.2, 0, 2.28), (x + sx * 0.2, 0, 0.5)], 0.012, chain, root, sides=4)
        tbox(kit, f"{p} seat {i}", (x, 0, 0.48), (0.5, 0.22, 0.05), solid(kit, f"swing seat {i}", cols[i % 4], 0.45), root)


def slide(kit, root, p):
    frame = solid(kit, "slide frame", RED, 0.4, shade=DRED)
    chute = solid(kit, "slide chute", YEL, 0.45, shade="#e0b21a")
    deck = solid(kit, "slide deck", PURP, 0.4)
    for sx in (1, -1):
        for sy in (1, -1):
            tube(kit, f"{p} post {sx} {sy}", [(sx * 0.5, 1.0 + sy * 0.5, 0), (sx * 0.5, 1.0 + sy * 0.5, 2.6)], 0.05, frame, root,
                 sides=6)
    tbox(kit, f"{p} deck", (0, 1.0, 1.5), (1.1, 1.1, 0.08), deck, root)
    tbox(kit, f"{p} roof", (0, 1.0, 2.65), (1.3, 1.3, 0.1), deck, root, taper=(0.2, 0.2))
    for i in range(5):   # ladder rungs on +Y
        tbox(kit, f"{p} rung {i}", (0, 1.6, 0.3 + 0.25 * i), (0.8, 0.05, 0.05), frame, root)
    ang = math.degrees(math.atan2(1.45, 2.4))
    tbox(kit, f"{p} chute", (0, -0.75, 0.82), (0.7, 2.8, 0.06), chute, root, rot=(-ang, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"{p} chute side {sx}", (sx * 0.36, -0.75, 0.92), (0.06, 2.8, 0.2), chute, root, rot=(-ang, 0, 0))


def merry_go_round(kit, root, p):
    lathe(kit, f"{p} disc", [(0, 0.3), (1.2, 0.3), (1.2, 0.22), (0.2, 0.15), (0, 0.15)], tm(kit, "merry disc", tex_merry), root,
          sides=12)
    rail = solid(kit, "merry rail", STEEL, 0.4, shade="#a9a2e0")
    tube(kit, f"{p} hub", [(0, 0, 0.3), (0, 0, 1.0)], 0.06, rail, root, sides=6)
    for k in range(4):
        a = math.pi / 2 * k
        ca, sa = math.cos(a), math.sin(a)
        tube(kit, f"{p} bar {k}", [(ca * 1.05, sa * 1.05, 0.3), (ca * 1.0, sa * 1.0, 0.85), (ca * 0.1, sa * 0.1, 1.0)], 0.035, rail,
             root, sides=4, caps=(False, False))


def tex_merry():
    c = Canvas(32, 16, PINK)
    for x in range(0, 32, 8):
        c.rect(x, 0, x + 3, 15, YEL)
    return c


def sandbox(kit, root, p):
    wood = solid(kit, "sandbox wood", "#e8a862", shade="#c47f3a")
    for sy in (1, -1):
        tbox(kit, f"{p} side y {sy}", (0, sy * 1.2, 0.12), (2.6, 0.12, 0.24), wood, root)
        tbox(kit, f"{p} side x {sy}", (sy * 1.25, 0, 0.12), (0.12, 2.4, 0.24), wood, root)
    tbox(kit, f"{p} sand", (0, 0, 0.1), (2.4, 2.3, 0.08), solid(kit, "sand", "#ffe0a0", 0.35, shade="#f0c878"), root)
    lowball(kit, f"{p} castle", (0.4, 0.3, 0.17), (0.3, 0.3, 0.2), solid(kit, "sand castle", "#f0c878"), root, smooth=False)
    tube(kit, f"{p} pail", [(-0.5, -0.4, 0.14), (-0.5, -0.4, 0.34)], [0.1, 0.13], solid(kit, "sand pail", RED, 0.45), root, sides=8)
    tbox(kit, f"{p} shovel", (-0.2, -0.6, 0.16), (0.08, 0.35, 0.03), solid(kit, "sand shovel", BLUE, 0.45), root, rot=(0, 0, 30))


def tire(kit, p, parent, loc, rot=(0, 0, 0), r=0.36):
    torus(kit, f"{p}", r * 0.72, r * 0.3, solid(kit, "old tire", "#2a2238", 0.15, shade="#3a3050"), parent, loc=loc, rot=rot,
          seg=10, sides=5)


def tire_pile(kit, root, p):
    for i, (x, y, z, rx) in enumerate(((0, 0, 0.12, 0), (0.05, 0.02, 0.33, 0), (0.0, -0.03, 0.54, 0), (0.85, 0.3, 0.38, 75))):
        tire(kit, f"{p} tire {i}", root, (x, y, z), (rx, 0, 15 * i))


def lawn_chair(kit, root, p):
    frame = solid(kit, "chair frame", STEEL, 0.35)
    web = tm(kit, "chair web", tex_web)
    tbox(kit, f"{p} seat", (0, 0, 0.35), (0.55, 0.5, 0.03), web, root, rot=(-8, 0, 0))
    tbox(kit, f"{p} back", (0, 0.3, 0.68), (0.55, 0.03, 0.6), web, root, rot=(-15, 0, 0))
    for sx in (1, -1):
        tube(kit, f"{p} leg {sx}", [(sx * 0.28, -0.25, 0.0), (sx * 0.28, 0.2, 0.4), (sx * 0.28, 0.4, 0.98)], 0.018, frame, root,
             sides=4)
        tube(kit, f"{p} leg b {sx}", [(sx * 0.28, 0.3, 0.0), (sx * 0.28, -0.2, 0.36)], 0.018, frame, root, sides=4)
        tbox(kit, f"{p} arm {sx}", (sx * 0.3, 0.0, 0.58), (0.05, 0.55, 0.03), frame, root)


def tex_web():
    c = Canvas(16, 16, MINT)
    for i in range(0, 16, 4):
        c.rect(i, 0, i + 1, 15, WHITE)
        c.rect(0, i, 15, i + 1, "#22c79c")
    return c


def kiddie_pool(kit, root, p):
    lathe(kit, f"{p} pool", [(1.1, 0.0), (1.2, 0.12), (1.2, 0.3), (1.05, 0.32), (1.0, 0.1)], solid(kit, "kiddie pool", BLUE, 0.45,
                                                                                                shade="#1f5fd0"), root,
          sides=12, closed=True)
    lathe(kit, f"{p} water", [(1.02, 0.2), (0, 0.2)], tm(kit, "pool water", lambda: tex_water(kit.rand), 0.55, 'REPEAT'), root,
          sides=12)
    for i, (x, y) in enumerate(((0.3, 0.2), (-0.4, -0.2))):
        lowball(kit, f"{p} duck {i}", (x, y, 0.25), (0.08, 0.1, 0.07), solid(kit, "rubber duck", YEL, 0.6), root, smooth=False)


def laundry_line(kit, root, p, L=5.0):
    post = solid(kit, "line post", STEEL, 0.35, shade="#a9a2e0")
    for sx in (1, -1):
        tube(kit, f"{p} post {sx}", [(sx * L / 2, 0, 0), (sx * L / 2, 0, 1.9)], 0.04, post, root, sides=5)
        tbox(kit, f"{p} cross {sx}", (sx * L / 2, 0, 1.85), (0.06, 1.0, 0.06), post, root)
    for sy in (1, -1):
        tube(kit, f"{p} line {sy}", [(-L / 2, sy * 0.45, 1.85), (0, sy * 0.45, 1.75), (L / 2, sy * 0.45, 1.85)], 0.008,
             solid(kit, "line", WHITE), root, sides=3)
    cols = (PINK, YEL, WHITE, MINT, BLUE, ORNG)
    for i in range(7):
        x = -L / 2 + 0.5 + i * (L - 1) / 6
        sy = 1 if i % 2 else -1
        kind = i % 3
        size = ((0.5, 0.7), (0.35, 0.5), (0.7, 0.55))[kind]   # sheet, shirt, towel
        tbox(kit, f"{p} cloth {i}", (x, sy * 0.45, 1.77 - size[1] / 2), (size[0], 0.02, size[1]),
             solid(kit, f"cloth {i % 6}", cols[i % 6], 0.4), root)
    tbox(kit, f"{p} boxers", (0.2, -0.45, 1.6), (0.3, 0.02, 0.28), tm(kit, "boxers", tex_boxers), root,
         uv={'all': (0, 0, 1, 1)})


def tex_boxers():
    c = Canvas(16, 16, WHITE)
    for y in range(0, 16, 5):
        for x in range((y // 5) % 2 * 3, 16, 6):
            disc(c, x, y, 1, RED)
    return c


def mailbox_c(kit, root, p, col=BLUE):
    road.mailbox(kit, root, p)


def flower_bed(kit, root, p, w=2.0, d=0.6):
    tbox(kit, f"{p} soil", (0, 0, 0.06), (w, d, 0.12), solid(kit, "bed soil", "#5a3a4c", 0.15), root)
    for i in range(int(w / 0.3)):
        x = -w / 2 + 0.15 + i * 0.3
        tbox(kit, f"{p} flower {i}", (x, 0, 0.2), (0.16, 0.16, 0.12), solid(kit, "flower " + str(i % 3), (PINK, YEL, WHITE)[i % 3], 0.5),
             root, rot=(0, 0, 45))
        tbox(kit, f"{p} stem {i}", (x, 0.05, 0.12), (0.2, 0.2, 0.1), solid(kit, "flower leaf", "#3fcf7a"), root, rot=(0, 0, 20))


def car(kit, root, p, col=PINK):
    """Parked hatchback (4.2 m) facing -Y."""
    body = solid(kit, f"car {col}", col, 0.4, shade=hex_scale(col, 0.85))
    glass = solid(kit, "car glass", GLASS, 0.3, shade="#3a3f80")
    tbox(kit, f"{p} body", (0, 0, 0.6), (1.8, 4.2, 0.7), body, root, taper=(0.98, 0.98))
    tbox(kit, f"{p} cabin", (0, 0.3, 1.25), (1.6, 2.4, 0.65), body, root, taper=(0.85, 0.75))
    tbox(kit, f"{p} glass", (0, 0.3, 1.27), (1.64, 2.0, 0.5), glass, root, taper=(0.85, 0.72))
    tbox(kit, f"{p} bumper f", (0, -2.12, 0.42), (1.8, 0.1, 0.2), solid(kit, "bumper", STEEL), root)
    tbox(kit, f"{p} bumper b", (0, 2.12, 0.42), (1.8, 0.1, 0.2), solid(kit, "bumper", STEEL), root)
    for sx in (1, -1):
        tbox(kit, f"{p} light {sx}", (sx * 0.65, -2.11, 0.68), (0.3, 0.04, 0.15), solid(kit, "headlight", "#fff1a0", 1.2), root)
        for sy in (1, -1):
            tube(kit, f"{p} wheel {sx} {sy}", [(sx * 0.82, sy * 1.35, 0.33), (sx * 0.95, sy * 1.35, 0.33)], 0.33,
                 solid(kit, "tire", "#2a2238", 0.15), root, sides=8, front=(0, 0, 1))


# ---------------------------------------------------------------- houses (Maple Grove), copied from h_road.house with colors
HX0, HX1, HY, HF, HT, HRX, HRZ = road.HX0, road.HX1, road.HY, road.HF, road.HT, road.HRX, road.HRZ
HOUSE_COLORS = [
    dict(siding="#9ff0d8", siding_d="#6fd2b8", roof="#5b6cff", roof_d="#3d47c8", door=PINK, shutter=BLUE),
    dict(siding="#ffc2dc", siding_d="#f2a0c4", roof="#8f5bff", roof_d="#6a3fd6", door=MINT, shutter=PURP),
    dict(siding="#fff09a", siding_d="#f0d870", roof="#ff6f8f", roof_d="#d63a6a", door=BLUE, shutter=MINT),
    dict(siding="#c8d8ff", siding_d="#a4b8f0", roof="#3fae8a", roof_d="#2a8a6a", door=YEL, shutter=PINK),
    dict(siding="#ffd8b0", siding_d="#f0b888", roof="#6a5aa8", roof_d="#4a3a88", door=RED, shutter=BLUE),
    dict(siding="#d8ffc8", siding_d="#b0e8a0", roof="#e86a4a", roof_d="#c04a2a", door=PURP, shutter=ORNG),
]


def tex_house_c(rand, C):
    c = Canvas(128, 128, C['siding'])
    for y in range(0, 96, 3):
        c.rect(0, y, 127, y, C['siding_d'])
    c.speckle(rand, [hex_scale(C['siding'], 1.06), hex_scale(C['siding'], 0.94)], 220, 0, 95)
    for x0, x1, y0, y1 in ((0, 1, 0, 47), (126, 127, 0, 47), (0, 1, 48, 95), (94, 95, 48, 95)):
        c.rect(x0, y0, x1, y1, WHITE)
    c.rect(0, 0, 127, 1, hex_scale(C['siding_d'], 0.85))
    c.rect(0, 48, 95, 49, hex_scale(C['siding_d'], 0.85))
    window_px(c, 14, 16, 20, 23, rand.random() < 0.5)
    window_px(c, 94, 16, 20, 23, rand.random() < 0.5)
    c.rect(54, 0, 73, 37, WHITE)
    c.rect(56, 0, 71, 34, INK)
    window_px(c, 38, 64, 20, 23, False)
    disc(c, 111, 78, 5, WHITE)
    disc(c, 111, 78, 3, GLASS)
    bricks(c, rand, 0, 96, 31, 127, "#c95a7a", "#9e3d5c", "#d9708e")
    return c


def tex_door_c(col):
    c = Canvas(16, 32, col)
    d = hex_scale(col, 0.85)
    c.rect(0, 0, 15, 0, d); c.rect(0, 31, 15, 31, d)
    c.rect(3, 4, 12, 13, d); c.rect(3, 17, 12, 22, d)
    c.rect(4, 24, 11, 29, GLASS); c.rect(5, 28, 6, 28, "#6f8cff")
    c.rect(12, 15, 13, 16, YEL)
    return c


def house_c(kit, root, p, ci=0):
    """h_road.house recolored: modeled facing -X, turned to face +X (place with rz = -90 to face -Y)."""
    C = HOUSE_COLORS[ci % len(HOUSE_COLORS)]
    root = kit.empty(f"{p} body", root, (0, 0, 0), (0, 0, 180))
    R = kit.rand
    atlas = tm(kit, f"house {ci}", lambda: tex_house_c(R, C))
    shing = tm(kit, f"house shingles {ci}", lambda: tex_shingles(R, C['roof'], C['roof_d']), ext='REPEAT')
    white, blue, pink = solid(kit, "trim", WHITE, 0.35), solid(kit, f"shutter {C['shutter']}", C['shutter']), \
        solid(kit, f"flower box {C['door']}", C['door'])
    found = solid(kit, "foundation", "#9a8fc8", shade="#857ab5")
    deck = solid(kit, "porch deck", "#e6e0ff", shade="#cfc6f0")
    side_uv = (0, 48 / 128, 96 / 128, 96 / 128)
    tbox(kit, f"{p} foundation", ((HX0 + HX1) / 2, 0, 0.05), (HX1 - HX0 + 0.1, 2 * HY + 0.1, 0.5), found, root)
    tbox(kit, f"{p} walls", ((HX0 + HX1) / 2, 0, HF + 1.5), (HX1 - HX0, 2 * HY, 3.0), atlas, root,
         uv={'all': (0.9, 0.5, 0.95, 0.55), 'nx': (0, 0, 1, 48 / 128), 'px': side_uv, 'ny': side_uv, 'py': side_uv})
    mb = MB()
    u = lambda x, z: ((96 + (x - HX0) / (HX1 - HX0) * 31) / 128, (48 + (z - HT) / (HRZ - HT) * 47) / 128)
    for sy in (1, -1):
        tri = [(HX1, sy * HY, HT), (HX0, sy * HY, HT), (HRX, sy * HY, HRZ)]
        tri = tri if sy > 0 else [tri[1], tri[0], tri[2]]
        mb.face(tri, [u(x, z) for x, _, z in tri], 0)
    mb.obj(kit, f"{p} gables", [atlas], root)
    k = (HRZ - HT) / (HRX - HX0)
    for nm, xe in (("front", HX0 - 0.45), ("back", HX1 + 0.45)):
        roof_plane(kit, f"{p} roof {nm}", root, xe, HT - 0.45 * k, HRX, HRZ, 2 * HY + 0.8, shing)
        tbox(kit, f"{p} gutter {nm}", (xe, 0, HT - 0.45 * k - 0.02), (0.12, 2 * HY + 0.8, 0.1), white, root)
    tbox(kit, f"{p} ridge", (HRX, 0, HRZ + 0.1), (0.3, 2 * HY + 0.9, 0.12), solid(kit, f"ridge {ci}", C['roof_d']), root)
    tbox(kit, f"{p} chimney", (2.6, 2.6, 4.9), (0.7, 0.7, 2.6), atlas, root, uv={'all': (0, 0.75, 0.25, 1.0)})
    tbox(kit, f"{p} chimney cap", (2.6, 2.6, 6.24), (0.86, 0.86, 0.1), white, root)
    tbox(kit, f"{p} porch", (HX0 - 0.75, 0, 0.15), (1.5, 6.6, 0.3), deck, root)
    tbox(kit, f"{p} step", (HX0 - 1.7, 0, 0.1), (0.4, 1.6, 0.2), deck, root)
    for i, y in enumerate((-3.2, -0.9, 0.9, 3.2)):
        tbox(kit, f"{p} post {i}", (HX0 - 1.4, y, 1.5), (0.14, 0.14, 2.4), white, root)
    roof_plane(kit, f"{p} porch roof", root, HX0 - 1.7, 2.68, HX0, 3.0, 6.9, shing, th=0.1)
    for sy in (1, -1):
        ys = [sy * (0.9 + 2.3 * kk / 6) for kk in range(7)]
        tbox(kit, f"{p} rail top {sy}", (HX0 - 1.4, sy * 2.05, 1.2), (0.08, 2.3, 0.08), white, root)
        tbox(kit, f"{p} rail low {sy}", (HX0 - 1.4, sy * 2.05, 0.42), (0.06, 2.3, 0.06), white, root)
        for i, y in enumerate(ys[1:-1]):
            tbox(kit, f"{p} baluster {sy} {i}", (HX0 - 1.4, y, 0.8), (0.05, 0.05, 0.78), white, root)
    tbox(kit, f"{p} door", (HX0 - 0.035, 0.0, HF + 1.08), (0.06, 1.0, 2.16), tm(kit, f"house door {ci}", lambda: tex_door_c(C['door'])),
         root, uv={'all': (0.1, 0.1, 0.15, 0.15), 'nx': (0, 0, 1, 1), 'px': (0, 0, 1, 1)})
    tbox(kit, f"{p} porch lamp", (HX0 - 0.06, 0.85, 2.3), (0.08, 0.14, 0.2), solid(kit, "porch lamp", "#fff1a0", 1.6), root)
    for i, yw in enumerate((2.53, -2.47)):
        for s in (1, -1):
            tbox(kit, f"{p} shutter {i} {s}", (HX0 - 0.03, yw + s * 0.88, HF + 1.72), (0.05, 0.42, 1.45), blue, root)
        tbox(kit, f"{p} sill {i}", (HX0 - 0.08, yw, HF + 0.98), (0.16, 1.45, 0.07), white, root)
        tbox(kit, f"{p} flower box {i}", (HX0 - 0.16, yw, HF + 0.84), (0.24, 1.2, 0.2), pink, root)
    for s in (1, -1):
        tbox(kit, f"{p} back shutter {s}", (HX1 + 0.03, s * 1.15, HF + 1.72), (0.05, 0.42, 1.45), blue, root)
    dx = HX0 + 0.9
    dz = HT - 0.45 * k + (dx - (HX0 - 0.45)) * k
    tbox(kit, f"{p} dormer", (dx + 0.4, 0, dz + 0.45), (1.4, 1.5, 1.3), atlas, root,
         uv={'all': (0.76, 0.4, 0.99, 0.74), 'nx': (38 / 128, 64 / 128, 58 / 128, 87 / 128)})
    for s in (1, -1):
        tbox(kit, f"{p} dormer roof {s}", (dx + 0.35, s * 0.4, dz + 1.33), (1.75, 0.98, 0.08), shing, root, rot=(-s * 32, 0, 0),
             uv={'all': (0, 0, 1, 0.6)})


def treehouse(kit, root, p):
    road.round_tree(kit, root, p)
    wood = tm(kit, "treehouse wood", lambda: stops.tex_wood(kit.rand), 0.3, 'REPEAT')
    tbox(kit, f"{p} hut", (0.2, -0.3, 2.9), (1.6, 1.4, 1.2), wood, root, uv={'all': (0, 0, 1, 1)})
    tbox(kit, f"{p} hut roof", (0.2, -0.3, 3.65), (1.9, 1.7, 0.4), solid(kit, "hut roof", RED, 0.4), root, taper=(0.1, 1.0))
    tbox(kit, f"{p} sign", (0.2, -1.02, 3.0), (0.7, 0.04, 0.3), tm(kit, "no dads", lambda: sign_tex("NO DADS", 32, 12, WHITE, RED, 1)),
         root, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
    for i in range(6):
        tbox(kit, f"{p} rung {i}", (0.2, -0.3, 0.4 + 0.4 * i), (0.4, 0.05, 0.05), wood, root, loc=(0, -0.0, 0))


def suburb_block(kit, root, p, variant):
    R = kit.rand
    ground(kit, root, p)
    walkm = road.ground_mats(kit)[1]
    concrete = tm(kit, "driveway", lambda: stops.tex_concrete(R), 0.25, 'REPEAT')
    lots = [(-9.5, -1, 0), (9.5, -1, 1), (-9.5, 1, 2), (9.5, 1, 3)]   # (x, facing: -1 = faces -Y, +1 = faces +Y, color)
    props = kit.empty(f"{p} props", root)
    for i, (x, f, ci) in enumerate(lots):
        ci = (ci + 2 * variant) % len(HOUSE_COLORS)
        y = f * 9.0
        rz = -90 if f < 0 else 90
        baked(kit, root, f"{p} house {i}", (x, y, SIDE), rz, lambda piv, i=i, ci=ci: house_c(kit, piv, f"{p} house {i}", ci))
        # front path from the porch to the block edge, driveway beside the house
        pad(kit, props, f"{p} path {i}", x - 0.6, min(f * 13.4, f * B2), x + 0.6, max(f * 13.4, f * B2), walkm)
        dx = x + (4.9 if x < 0 else -4.9) * (1 if variant % 2 == 0 else -1)
        pad(kit, props, f"{p} drive {i}", dx - 1.3, min(f * 5.0, f * B2), dx + 1.3, max(f * 5.0, f * B2), concrete)
        at(kit, props, road.mailbox, f"{p} mailbox {i}", x + 1.3, f * 18.9, 0 if f < 0 else 180)
        at(kit, props, flower_bed, f"{p} bed {i}", x - 2.6, f * 13.9, 0)
    # picket fences along the front and back edges with gaps for paths and drives
    for sy in (1, -1):
        gaps = []
        for x, f, ci in lots:
            if f == sy:
                dx = x + (4.9 if x < 0 else -4.9) * (1 if variant % 2 == 0 else -1)
                gaps += [(x + 19.4 - 0.9, x + 19.4 + 0.9), (dx + 19.4 - 1.5, dx + 19.4 + 1.5)]
        fence_gaps(kit, props, road.picket_fence, f"{p} fence {sy}", (-19.4, sy * 19.4), (19.4, sy * 19.4), 2.0, gaps,
                   picket_post(kit))
    # side fences with a gate gap each, and a back-yard divider
    for sx in (1, -1):
        fence_gaps(kit, props, road.picket_fence, f"{p} side fence {sx}", (sx * 19.4, -19.4), (sx * 19.4, 19.4), 2.0,
                   [(18.0, 21.0)], picket_post(kit))
    fence_gaps(kit, props, road.picket_fence, f"{p} divider", (0, -4.0), (0, 4.0), 2.0, [(3.0, 5.0)], picket_post(kit))
    # trees and back-yard toys
    trees = [(-15.5, -15.5), (15.5, 15.0), (-2.5, -15.0), (3.0, 15.5)] if variant != 1 else \
        [(-16.0, 15.0), (16.0, -15.5), (2.5, -15.5), (-2.5, 15.5)]
    for i, (x, y) in enumerate(trees):
        at(kit, props, road.round_tree if i % 2 == 0 else road.pine_tree, f"{p} tree {i}", x, y, 40 * i, 0.9 + 0.1 * (i % 2))
    for i, (x, y) in enumerate(((-17.5, -2.0), (17.5, 2.5), (-1.6, 17.6), (1.6, -17.6))):
        at(kit, props, road.bush, f"{p} bush {i}", x, y, 70 * i, 0.8)
    kid_spots = [(-8.2, -16.0), (10.8, -15.8), (-10.8, 15.8), (8.0, 16.2), (-9.5, -13.6), (9.5, 13.6)]
    patch, mud = [], []
    if variant == 0:
        at(kit, props, swing_set, f"{p} swings", -8.0, 0.0, 0)
        at(kit, props, sandbox, f"{p} sandbox", 9.0, 1.5, 0)
        at(kit, props, kiddie_pool, f"{p} kiddie pool", 12.5, -1.5, 0)
        kid_spots += [(-8.0, -1.4), (9.0, 3.0), (12.0, -3.0)]
        patch, mud = [(-14.5, -16.0), (14.0, 16.0)], [(4.5, 1.0)]
    elif variant == 1:
        at(kit, props, treehouse, f"{p} treehouse", -9.0, 0.0, 30)
        at(kit, props, slide, f"{p} slide", 9.0, 0.5, 90)
        at(kit, props, lawn_chair, f"{p} chair", 13.0, -1.5, 160)
        kid_spots += [(-7.0, -1.8), (7.0, 0.5), (-12.0, 2.0)]
        patch, mud = [(15.0, -15.5)], []
    else:
        at(kit, props, swing_set, f"{p} swings", 9.0, 0.0, 0, 0.9)
        at(kit, props, merry_go_round, f"{p} merry", -9.5, 0.5, 0, 0.8)
        at(kit, props, laundry_line, f"{p} laundry", -14.0, 2.0, 90)
        at(kit, props, road.trash_can, f"{p} trash", 6.0, -4.2, 0)
        kid_spots += [(9.0, -1.4), (-9.5, -1.8), (-6.0, 2.5)]
        patch, mud = [(-15.0, 15.5), (13.5, -15.0)], [(-4.5, -1.5)]
    bake_props(kit, root, props, p)
    for i, (x, y) in enumerate(kid_spots):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)
    for i, (x, y) in enumerate(patch):
        socket(kit, root, f"patch {i}", (x, y, SIDE), 180 if y > 0 else 0)
    for i, (x, y) in enumerate(mud):
        socket(kit, root, f"mud {i}", (x, y, SIDE))


# ---------------------------------------------------------------- The Flats: trailer lots
def tex_trailer(rand, base, stripe):
    """128 x 64: rows 0-31 long side (12 m x 2.8 m), rows 32-63 end (x 0-39)."""
    c = Canvas(128, 64, base)
    for y in range(0, 32, 2):
        c.rect(0, y, 127, y, hex_scale(base, 0.92))
    c.speckle(rand, [hex_scale(base, 0.85), hex_scale(base, 1.06)], 260, 0, 31)
    c.rect(0, 9, 127, 11, stripe); c.rect(0, 12, 127, 12, hex_scale(stripe, 0.8))
    for x0 in (8, 30, 86, 108):
        c.rect(x0, 14, x0 + 12, 25, WHITE); c.rect(x0 + 1, 15, x0 + 11, 24, GLASS)
        c.dots([(x0 + 3, 21), (x0 + 4, 20), (x0 + 5, 19)], "#6f8cff")
        if rand.random() < 0.5:
            c.rect(x0 + 1, 19, x0 + 11, 24, "#ffd36b")
    c.rect(56, 2, 66, 27, WHITE); c.rect(57, 3, 65, 26, hex_scale(base, 0.75))
    c.rect(59, 18, 63, 24, GLASS); c.set(64, 13, YEL)
    for _ in range(14):   # rust streaks
        x = rand.randrange(128)
        c.rect(x, 26 - rand.randint(2, 8), x, 27, "#b8703a")
    c.rect(0, 32, 39, 63, base)
    for y in range(32, 64, 2):
        c.rect(0, y, 39, y, hex_scale(base, 0.92))
    c.rect(0, 41, 39, 43, stripe)
    c.rect(14, 46, 26, 56, WHITE); c.rect(15, 47, 25, 55, GLASS)
    return c


def trailer(kit, root, p, base=MINT, stripe=PINK, L=12.0, W=3.6):
    R = kit.rand
    t = tm(kit, f"trailer {base}", lambda: tex_trailer(R, base, stripe))
    side, end = (0, 0, 1, 0.5), (0, 0.5, 40 / 128, 1)
    tbox(kit, f"{p} body", (0, 0, 1.95), (L, W, 2.8), t, root,
         uv={'ny': side, 'py': side, 'nx': end, 'px': end, 'pz': (0.9, 0.9, 0.95, 0.95), 'nz': (0.9, 0.9, 0.95, 0.95)})
    tbox(kit, f"{p} roof", (0, 0, 3.42), (L + 0.1, W + 0.1, 0.15), solid(kit, "trailer roof", STEEL, 0.3, shade="#a9a2e0"), root,
         taper=(0.98, 0.8))
    tbox(kit, f"{p} skirt", (0, 0, 0.36), (L - 0.2, W - 0.2, 0.44), cut_mat(kit, "lattice", tex_lattice), root,
         uv={'all': (0, 0, L / 1.0, 0.44)})
    tbox(kit, f"{p} skirt back", (0, 0, 0.36), (L - 0.4, W - 0.4, 0.44), solid(kit, "crawlspace", INK, 0.05), root)
    wood = tm(kit, "steps wood", lambda: stops.tex_wood(R), 0.3, 'REPEAT')
    for i in range(3):
        tbox(kit, f"{p} step {i}", (-0.0, -W / 2 - 0.9 + 0.3 * i, 0.12 + 0.2 * i), (1.4, 0.6, 0.24 + 0.4 * i), wood, root,
             uv={'all': (0, 0, 1, 1)})
    tbox(kit, f"{p} ac unit", (L / 2 - 2.5, -W / 2 - 0.25, 2.3), (0.7, 0.5, 0.5), solid(kit, "ac unit", "#d9d4ff", 0.3), root)
    tube(kit, f"{p} propane", [(-L / 2 + 0.8, -W / 2 - 0.5, 0.15), (-L / 2 + 0.8, -W / 2 - 0.5, 1.1)], 0.3,
         solid(kit, "propane", WHITE, 0.35), root, sides=8, bulge=(0, 0.2))
    tbox(kit, f"{p} hitch", (L / 2 + 0.7, 0, 0.5), (1.4, 0.15, 0.15), solid(kit, "hitch", "#4a3a6e"), root)
    tbox(kit, f"{p} awning", (0, -W / 2 - 0.9, 2.7), (3.2, 1.8, 0.06), tm(kit, "trailer awning", tex_stripe_awning), root,
         rot=(-8, 0, 0), uv={'all': (0, 0, 1, 1)})
    for sx in (1, -1):
        tube(kit, f"{p} awning pole {sx}", [(sx * 1.5, -W / 2 - 1.7, 0.0), (sx * 1.5, -W / 2 - 1.7, 2.6)], 0.03,
             solid(kit, "pole", STEEL), root, sides=4)
    tube(kit, f"{p} antenna", [(L / 2 - 1.5, 0.5, 3.5), (L / 2 - 1.5, 0.5, 4.4)], 0.02, solid(kit, "antenna", STEEL), root, sides=4)
    tbox(kit, f"{p} antenna bar", (L / 2 - 1.5, 0.5, 4.3), (0.9, 0.03, 0.03), solid(kit, "antenna", STEEL), root, rot=(0, 0, 30))


def tex_lattice():
    c = Canvas(16, 16, road.CUT)
    for i in range(16):
        c.set(i, i, WHITE); c.set(15 - i, i, WHITE)
        c.set((i + 8) % 16, i, WHITE); c.set((23 - i) % 16, i, WHITE)
    return c


def tex_stripe_awning():
    c = Canvas(32, 16, WHITE)
    for x in range(0, 32, 8):
        c.rect(x, 0, x + 3, 15, YEL)
    return c


def tex_dirt_lot(rand):
    c = Canvas(32, 32, "#8a6a5a")
    c.speckle(rand, ["#7a5a4c", "#9a7a68", "#6e5040"], 260)
    for _ in range(10):
        x, y = rand.randrange(32), rand.randrange(32)
        c.dots([(x, y), (x + 1, y + 1)], "#4fd68a")
    return c


def trailer_lot(kit, root, p, variant):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    dirt = tm(kit, "lot dirt", lambda: tex_dirt_lot(R), 0.2, 'REPEAT')
    gravel = tm(kit, "gravel", lambda: stops.tex_gravel(R), 0.25, 'REPEAT')
    # big dirt yard with patchy grass islands left as lawn, gravel lane through the middle
    pad(kit, props, f"{p} dirt a", -19.5, -19.5, 19.5, -2.0, dirt, 4.0)
    pad(kit, props, f"{p} dirt b", -19.5, 2.0, 19.5, 19.5, dirt, 4.0)
    pad(kit, props, f"{p} lane", -2.2, -B2, 2.2, B2, gravel, 3.0, z=0.02)
    pad(kit, props, f"{p} lane x", -B2, -1.6, B2, 1.6, gravel, 3.0, z=0.018)
    cols = [(MINT, PINK), (YEL, BLUE), ("#ffc2dc", MINT), ("#c8d8ff", ORNG)]
    if variant == 0:
        spots = [(-10.5, -9.5, 0), (10.5, -9.0, 0), (-10.5, 10.0, 180), (11.0, 10.5, 180)]
    else:
        spots = [(-11.0, -8.0, 0), (11.0, -11.0, 0), (-9.5, 12.0, 180)]
    for i, (x, y, rz) in enumerate(spots):
        b, s = cols[(i + variant) % 4]
        baked(kit, root, f"{p} trailer {i}", (x, y, SIDE), rz, lambda piv, i=i, b=b, s=s: trailer(kit, piv, f"{p} trailer {i}", b, s))
    # chain-link fence around the lot with gaps at the lane and the side yards
    post = chain_post(kit)
    for sy in (1, -1):
        fence_gaps(kit, props, road.chainlink_fence, f"{p} fence {sy}", (-19.6, sy * 19.6), (19.6, sy * 19.6), 2.5,
                   [(16.8, 22.4), (4.0, 6.5)], post)
    for sx in (1, -1):
        fence_gaps(kit, props, road.chainlink_fence, f"{p} side {sx}", (sx * 19.6, -19.6), (sx * 19.6, 19.6), 2.5,
                   [(17.6, 21.6)], post)
    # junk
    if variant == 0:
        at(kit, props, tire_pile, f"{p} tires", -16.0, -2.8, 0)
        at(kit, props, lawn_chair, f"{p} chair 0", -7.0, -15.0, 200)
        at(kit, props, lawn_chair, f"{p} chair 1", -5.6, -15.4, 160)
        at(kit, props, kiddie_pool, f"{p} kiddie pool", 7.0, -15.0, 0)
        at(kit, props, laundry_line, f"{p} laundry", 12.0, 4.5, 0)
        at(kit, props, road.trash_can, f"{p} trash 0", 3.4, -5.0, 0)
        at(kit, props, road.trash_can, f"{p} trash 1", 3.6, 5.6, 40)
        at(kit, props, dead_car, f"{p} junk car", -15.0, 5.0, 80)
        at(kit, props, road.round_tree, f"{p} tree", 16.5, -16.0, 30, 0.85)
        kids = [(-6.3, -14.0), (7.0, -12.8), (-12.0, -4.4), (10.5, -3.6), (-10.0, 5.8), (12.0, 6.4), (5.0, 15.0), (-4.0, 16.5)]
        mud = [(0.0, -9.0), (-4.5, 8.0), (14.5, -3.8)]
    else:
        at(kit, props, tire_pile, f"{p} tires", 15.5, 4.0, 40)
        at(kit, props, lawn_chair, f"{p} chair", -15.5, -15.5, 210)
        at(kit, props, kiddie_pool, f"{p} kiddie pool", 7.5, 7.0, 0)
        at(kit, props, laundry_line, f"{p} laundry", -11.0, 4.6, 0)
        at(kit, props, dead_car, f"{p} junk car", 13.0, 14.5, 10)
        at(kit, props, road.trash_can, f"{p} trash", 3.4, -6.0, 0)
        at(kit, props, swing_set, f"{p} rusty swings", 10.5, -2.5, 0, 0.9)
        at(kit, props, road.pine_tree, f"{p} pine", -16.5, 16.5, 0, 0.9)
        kids = [(-11.0, -13.5), (11.0, -15.0), (10.5, -4.0), (7.0, 9.2), (-9.5, 7.2), (-4.5, 15.0), (14.0, 8.0)]
        mud = [(-5.0, -5.0), (6.0, 14.5)]
    bake_props(kit, root, props, p)
    for i, (x, y) in enumerate(kids):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)
    for i, (x, y) in enumerate(mud):
        socket(kit, root, f"mud {i}", (x, y, SIDE))


def dead_car(kit, root, p):
    car(kit, root, p, "#b48cff")
    for sx in (1, -1):
        for sy in (1, -1):
            tbox(kit, f"{p} block {sx} {sy}", (sx * 0.85, sy * 1.35, 0.15), (0.35, 0.35, 0.3), solid(kit, "cinder", "#9a92b0"), root)


# ---------------------------------------------------------------- Big Dairy Lot
def tex_carton(rand):
    """128 x 128: front face (10 m x 8 m) in rows 0-101, gable fin strip above."""
    c = Canvas(128, 128, WHITE)
    c.speckle(rand, ["#f0e8f8"], 200)
    c.rect(0, 0, 127, 5, BLUE)
    c.rect(0, 100, 127, 103, BLUE)
    for i, (x, y, r) in enumerate(((14, 70, 7), (108, 30, 6), (20, 25, 5), (110, 82, 5))):
        disc(c, x, y, r, "#241a30"); disc(c, x + r - 1, y + 2, r - 2, "#241a30")
    c.rect(18, 76, 109, 97, PINK); c.rect(18, 76, 109, 77, "#d63a86")
    txt_c(c, "BIG DAIRY", 64, 93, WHITE, 2, shadow="#a8206a")
    # milk drop logo
    disc(c, 64, 52, 12, BLUE); disc(c, 64, 52, 10, WHITE)
    for r in range(12):
        c.rect(64 - (11 - r) // 2, 62 + r, 64 + (11 - r) // 2, 62 + r, BLUE if r > 9 else WHITE)
    txt_c(c, "WE OWN YOU", 64, 36, BLUE)
    # payment window
    c.rect(44, 6, 84, 28, "#9d95d4"); c.rect(46, 8, 82, 26, GLASS)
    c.dots([(50, 22), (51, 21), (52, 20)], "#6f8cff")
    return c


def big_dairy_lot(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    asph = tm(kit, "road asphalt", lambda: road.tex_road(R), 0.15, 'REPEAT')
    pad(kit, props, f"{p} lot", -18.8, -B2, 18.8, 18.8, asph, 5.0)
    white = solid(kit, "lane white", WHITE, 0.4)
    yel = solid(kit, "lane yellow", YEL, 0.5)
    for i in range(8):   # shop pedestal squares along -X
        y = -13.0 + 3.0 * i
        for (a, b, w, h) in ((0, -0.8, 1.7, 0.1), (0, 0.8, 1.7, 0.1), (-0.8, 0, 0.1, 1.7), (0.8, 0, 0.1, 1.7)):
            tbox(kit, f"{p} pedestal mark {i} {a} {b}", (-15.0 + a, y + b, SIDE + 0.016), (w, h, 0.01), yel, props)
    for i in range(5):   # parking stripes along +X
        tbox(kit, f"{p} stall {i}", (15.5, -12 + 4 * i, SIDE + 0.016), (4.0, 0.12, 0.01), white, props)
    tbox(kit, f"{p} truck bay", (0, -4.0, SIDE + 0.016), (4.2, 8.0, 0.01), solid(kit, "bay", "#3d3358", 0.1), props)
    for sx in (1, -1):
        tbox(kit, f"{p} bay line {sx}", (sx * 2.1, -4.0, SIDE + 0.02), (0.15, 8.0, 0.01), yel, props)
    tbox(kit, f"{p} bay stop", (0, -8.0, SIDE + 0.02), (4.2, 0.3, 0.01), yel, props)
    # giant milk carton
    def carton(piv):
        t = tm(kit, "carton", lambda: tex_carton(R))
        W, D, H = 10.0, 9.0, 8.0
        tbox(kit, f"{p} carton walls", (0, 0, H / 2), (W, D, H), t, piv,
             uv={'ny': (0, 0, 1, 104 / 128), 'py': (0, 0, 1, 104 / 128), 'nx': (0.1, 0.05, 0.9, 104 / 128),
                 'px': (0.1, 0.05, 0.9, 104 / 128), 'pz': (0.4, 0.5, 0.5, 0.6), 'nz': (0.4, 0.5, 0.5, 0.6)})
        prof = [(-D / 2, H), (D / 2, H), (0.3, H + 3.4), (-0.3, H + 3.4)]
        prism(kit, f"{p} carton gable", [(y, z) for y, z in prof], -W / 2, W / 2, solid(kit, "carton top", WHITE, 0.35,
                                                                                        shade="#e6e0f4"), piv)
        tbox(kit, f"{p} carton fin", (0, 0, H + 3.75), (W + 0.2, 0.6, 0.8), solid(kit, "carton fin", BLUE, 0.4), piv)
        tbox(kit, f"{p} spout", (W / 2 - 1.6, -0.9, H + 2.6), (2.0, 0.5, 1.2), solid(kit, "carton spout", PINK, 0.4), piv,
             rot=(-40, 0, 0))
        # payment window counter and awning
        tbox(kit, f"{p} counter", (0, -D / 2 - 0.35, 1.05), (3.6, 0.7, 0.1), solid(kit, "counter", PINK, 0.4), piv)
        tbox(kit, f"{p} counter base", (0, -D / 2 - 0.15, 0.5), (3.6, 0.3, 1.0), solid(kit, "counter base", "#d63a86"), piv)
        tbox(kit, f"{p} awning", (0, -D / 2 - 0.9, 2.95), (4.6, 1.8, 0.08), tm(kit, "dairy awning", tex_stripe_awning), piv,
             rot=(-14, 0, 0), uv={'all': (0, 0, 1.5, 1)})
        tbox(kit, f"{p} pay sign", (0, -D / 2 - 0.05, 3.45), (2.6, 0.08, 0.5),
             tm(kit, "pay sign", lambda: sign_tex("PAY HERE", 48, 10, YEL, INK, 1, border=PINK)), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        tbox(kit, f"{p} cash box", (1.2, -D / 2 - 0.4, 1.25), (0.5, 0.4, 0.3), solid(kit, "cash box", GREEN_CASH, 0.45), piv)
        for sx in (1, -1):
            tube(kit, f"{p} flood {sx}", [(sx * 4.6, -D / 2, 7.4), (sx * 4.6, -D / 2 - 0.8, 7.6)], 0.08, solid(kit, "flood", STEEL), piv,
                 sides=5)
            tbox(kit, f"{p} flood lamp {sx}", (sx * 4.6, -D / 2 - 0.9, 7.5), (0.5, 0.2, 0.3), solid(kit, "flood glow", "#fff1a0", 1.6), piv)
    baked(kit, root, f"{p} carton", (0, 12.5, SIDE), 0, carton)
    # time clock post where the dads clock out
    def clock(piv):
        tube(kit, f"{p} clock post", [(0, 0, 0), (0, 0, 1.3)], 0.06, solid(kit, "clock post", STEEL), piv, sides=6)
        tbox(kit, f"{p} clock box", (0, 0, 1.45), (0.5, 0.3, 0.6), solid(kit, "clock box", BLUE, 0.4, shade="#1f5fd0"), piv)
        tbox(kit, f"{p} clock face", (0, -0.16, 1.55), (0.36, 0.02, 0.3), tm(kit, "clock face", tex_clock), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        tbox(kit, f"{p} card rack", (0.36, -0.05, 1.3), (0.2, 0.1, 0.5), solid(kit, "card rack", STEEL), piv)
        tbox(kit, f"{p} clock sign", (0, 0, 2.05), (0.9, 0.06, 0.35), tm(kit, "clock sign", lambda: sign_tex("CLOCK OUT", 40, 12, WHITE, PINK, 1)),
             piv, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        tube(kit, f"{p} sign post", [(0, 0.04, 1.75), (0, 0.04, 1.9)], 0.03, solid(kit, "clock post", STEEL), piv, sides=4)
    baked(kit, root, f"{p} time clock", (7.5, 6.0, SIDE + 0.012), 0, clock)
    # chain-link fence with the truck opening on the front
    post = chain_post(kit)
    fence_gaps(kit, props, road.chainlink_fence, f"{p} fence front", (-19.6, -19.6), (19.6, -19.6), 2.5, [(13.6, 25.6)], post)
    fence_line(kit, props, road.chainlink_fence, f"{p} fence back", (-19.6, 19.6), (19.6, 19.6), 2.5, post)
    for sx in (1, -1):
        fence_gaps(kit, props, road.chainlink_fence, f"{p} fence side {sx}", (sx * 19.6, -19.6), (sx * 19.6, 19.6), 2.5,
                   [(4.0, 6.5)], post)
    # big sign at the gate
    def gate_sign(piv):
        for sx in (1, -1):
            tube(kit, f"{p} sign leg {sx}", [(sx * 2.0, 0, 0), (sx * 2.0, 0, 4.0)], 0.1, solid(kit, "sign leg", STEEL), piv, sides=6)
        tbox(kit, f"{p} gate sign", (0, 0, 4.4), (5.0, 0.2, 1.4),
             tm(kit, "gate sign", lambda: sign_tex("", 64, 20, PINK, WHITE, 1, border=WHITE,
                                                   lines=["BIG DAIRY", "LOANS 24-7"])), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    baked(kit, root, f"{p} gate sign", (8.4, -18.4, SIDE), 0, gate_sign)
    for i, (x, y) in enumerate(((-17.5, 17.5), (17.5, 17.5))):
        at(kit, props, road.street_lamp, f"{p} lamp {i}", x, y, 180 + (40 if x < 0 else -40))
    for i, (x, y) in enumerate(((10.0, 17.8), (11.0, 17.6), (10.5, 18.4))):
        tube(kit, f"{p} drum {i}", [(x, y, SIDE), (x, y, SIDE + 0.9)], 0.3, solid(kit, "drum", BLUE if i % 2 else WHITE, 0.4),
             props, sides=8)
    at(kit, props, road.round_tree, f"{p} tree", -17.0, 10.0, 0, 0.8)
    def statue(piv):
        tbox(kit, f"{p} plinth", (0, 0, 0.5), (2.6, 1.6, 1.0), solid(kit, "plinth", PINK, 0.4, shade="#e83a8f"), piv)
        tbox(kit, f"{p} plinth plate", (0, -0.82, 0.55), (1.6, 0.04, 0.4),
             tm(kit, "plinth plate", lambda: sign_tex("BESSIE", 32, 8, GOLDC, INK, 1)), piv, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        cw = kit.empty(f"{p} cow", piv, (0, 0, 1.0), (0, 0, 0), (1.3, 1.3, 1.3))
        stops.cow(kit, cw, f"{p} cow", (0, 0, 0), 90)
    baked(kit, root, f"{p} cow statue", (-8.5, 9.5, SIDE + 0.012), 20, statue)
    def refunds(piv):
        tbox(kit, f"{p} refunds", (0, 0, 1.2), (2.4, 0.05, 0.8), tm(kit, "refunds sign", lambda: sign_tex("", 40, 14, WHITE, RED, 1,
                                                                                                       border=RED, lines=["NO", "REFUNDS"])),
             piv, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    baked(kit, root, f"{p} refunds sign", (-12.0, -19.75, SIDE), 0, refunds)
    for i, x in enumerate((-3.0, 3.0)):
        tube(kit, f"{p} bollard {i}", [(x, 7.0, SIDE), (x, 7.0, SIDE + 0.9)], 0.15, solid(kit, "bollard", YEL, 0.45), props, sides=8)
        lowball(kit, f"{p} bollard cap {i}", (x, 7.0, SIDE + 0.9), (0.15, 0.15, 0.1), solid(kit, "bollard", YEL, 0.45), props)
    bake_props(kit, root, props, p)
    socket(kit, root, "truck park", (0, -4.0, SIDE), 0)
    socket(kit, root, "collector", (0, 12.5 - 4.5 - 1.6, SIDE), 0)
    for i in range(8):
        socket(kit, root, f"shop {i}", (-15.0, -13.0 + 3.0 * i, SIDE), 90)
    socket(kit, root, "end day", (7.5, 5.3, SIDE), 0)
    for i, (x, y) in enumerate(((-12.0, -17.0), (12.5, -16.5), (-10.5, 14.0), (12.0, 10.0), (17.0, -6.0), (-6.0, 6.0))):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)


GREEN_CASH = "#5fd38a"


def tex_clock():
    c = Canvas(16, 16, "#2a2f3a")
    c.rect(1, 3, 14, 12, "#9cff57")
    txt(c, "5:00", 0, 10, "#1f5a12")
    return c


# ---------------------------------------------------------------- Park Block
def pond(kit, root, p, rx=5.5, ry=3.8):
    R = kit.rand
    rim = [(math.cos(2 * math.pi * k / 16) * rx * (1 + R.uniform(-0.08, 0.08)), math.sin(2 * math.pi * k / 16) * ry *
            (1 + R.uniform(-0.08, 0.08))) for k in range(16)]
    stone = solid(kit, "pond stone", "#b3a6d9", 0.3, shade="#8f82bd")
    for k, (x, y) in enumerate(rim):
        lowball(kit, f"{p} rim {k}", (x, y, 0.06), (0.55, 0.45, 0.22), stone, root, smooth=False)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    c = bm.verts.new((0, 0, 0.02))
    ring = [bm.verts.new((x * 0.97, y * 0.97, 0.02)) for x, y in rim]
    for k in range(16):
        f = bm.faces.new((c, ring[k], ring[(k + 1) % 16]))
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.x / 4, lp.vert.co.y / 4)
    kit.mesh_from_bmesh(f"{p} water", bm, tm(kit, "pond water", lambda: tex_water(R), 0.5, 'REPEAT'), root, smooth=False)
    lily = solid(kit, "lily pad", "#3fcf7a", 0.35)
    for i, (x, y) in enumerate(((1.5, 1.0), (-2.0, -0.8), (2.6, -1.4))):
        splat(kit, f"{p} lily {i}", (x, y), 0.45, lily, root, lobes=7, z=0.03)
    for i, (x, y) in enumerate(((-1.0, 0.6), (0.6, -0.4))):
        lowball(kit, f"{p} duck {i}", (x, y, 0.12), (0.14, 0.2, 0.12), solid(kit, "duck", WHITE, 0.5), root, smooth=False)
        lowball(kit, f"{p} duck head {i}", (x, y - 0.18, 0.28), (0.08, 0.08, 0.08), solid(kit, "duck", WHITE, 0.5), root, smooth=False)
        tbox(kit, f"{p} beak {i}", (x, y - 0.27, 0.27), (0.05, 0.06, 0.03), solid(kit, "beak", ORNG, 0.5), root)


def park_block(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    walkm = road.ground_mats(kit)[1]
    mulch = solid(kit, "mulch", "#a85a3a", 0.25, shade="#8a4a2a")
    rubber = tm(kit, "playground rubber", lambda: tex_rubber(R), 0.3, 'REPEAT')
    # paths: a cross plus a loop corner
    pad(kit, props, f"{p} path x", -B2, -1.0, B2, 1.0, walkm)
    pad(kit, props, f"{p} path y", -1.0, -B2, 1.0, B2, walkm)
    tube(kit, f"{p} plaza", [(0, 0, SIDE), (0, 0, SIDE + 0.02)], 3.4, walkm, props, sides=12)
    at(kit, props, fountain_small, f"{p} fountain", 0, 0, 0)
    # playground (-X, -Y quadrant)
    pad(kit, props, f"{p} play pad", -17.5, -17.5, -4.0, -4.0, rubber, 3.0)
    at(kit, props, slide, f"{p} slide", -14.0, -8.0, 0)
    at(kit, props, swing_set, f"{p} swings", -8.0, -14.5, 0)
    at(kit, props, merry_go_round, f"{p} merry", -7.5, -8.0, 0)
    at(kit, props, sandbox, f"{p} sandbox", -14.5, -14.5, 0)
    # pond (+X, +Y quadrant)
    pond_piv = kit.empty(f"{p} pond", props, (10.5, 10.5, SIDE))
    pond(kit, pond_piv, f"{p} pond")
    # nut tree spot (+X, -Y quadrant): mulch ring, keep 5 m clear
    tube(kit, f"{p} mulch", [(10.0, -10.0, SIDE), (10.0, -10.0, SIDE + 0.03)], 1.8, mulch, props, sides=12)
    # benches along the paths, trees (-X, +Y quadrant grove), flower beds, lamps
    for i, (x, y, rz) in enumerate(((-6.0, 2.2, 180), (6.0, -2.2, 0), (2.2, 6.0, -90), (-2.2, -6.0, 90), (4.0, 15.0, -90),
                                    (15.0, 4.0, 180))):
        at(kit, props, bench, f"{p} bench {i}", x, y, rz)
    for i, (x, y) in enumerate(((-15.0, 15.0), (-9.0, 16.5), (-15.5, 8.5), (-7.5, 9.5), (17.0, -17.5), (17.0, 17.0))):
        at(kit, props, road.round_tree if i % 3 else road.pine_tree, f"{p} tree {i}", x, y, 37 * i, 0.9 + 0.1 * (i % 2))
    for i, (x, y, rz) in enumerate(((3.5, 3.5, 45), (-3.5, 3.5, -45), (3.5, -3.5, -45), (-3.5, -3.5, 45))):
        at(kit, props, flower_bed, f"{p} bed {i}", x, y, rz)
    for i, (x, y) in enumerate(((1.6, 12.0), (-1.6, -12.0), (12.0, -1.6), (-12.0, 1.6))):
        at(kit, props, road.street_lamp, f"{p} lamp {i}", x, y, 0)
    for i, (x, y) in enumerate(((1.6, 18.5), (18.5, -1.6))):
        at(kit, props, road.trash_can, f"{p} trash {i}", x, y, 0)
    # little park sign at the front entrance
    def sign(piv):
        for sx in (1, -1):
            tbox(kit, f"{p} sign post {sx}", (sx * 1.0, 0, 0.6), (0.15, 0.15, 1.2), solid(kit, "park wood", "#a8642a"), piv)
        tbox(kit, f"{p} sign board", (0, 0, 1.3), (2.4, 0.12, 0.7), tm(kit, "park sign", lambda: sign_tex("", 48, 16, "#3f9e5a", WHITE, 1,
                                                                                                        border="#a8642a",
                                                                                                        lines=["MAPLE", "PARK"])),
             piv, uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    sp = kit.empty(f"{p} sign", props, (3.2, -18.5, SIDE))
    sign(sp)
    bake_props(kit, root, props, p)
    socket(kit, root, "nut tree", (10.0, -10.0, SIDE))
    kids = [(-14.0, -10.5), (-8.0, -13.2), (-6.0, -8.0), (-12.5, -14.5), (-10.0, -5.5), (0.0, -3.6), (-5.0, 1.8), (5.5, 7.0),
            (6.5, 12.0), (-12.0, 12.0), (14.0, 2.6), (2.2, -15.0)]
    for i, (x, y) in enumerate(kids):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)


def tex_rubber(rand):
    c = Canvas(16, 16, "#ff8a3d")
    c.speckle(rand, ["#e8752b", "#ffa060", PINK], 60)
    return c


def fountain_small(kit, root, p):
    stone = solid(kit, "fountain stone", "#d9d4ff", 0.35, shade="#b9b2e6")
    water = tm(kit, "fountain water", lambda: tex_water(kit.rand), 0.6, 'REPEAT')
    lathe(kit, f"{p} basin", [(0, 0.0), (1.6, 0.0), (1.6, 0.5), (1.4, 0.5), (1.4, 0.15), (0, 0.15)], stone, root, sides=12)
    lathe(kit, f"{p} pool", [(1.42, 0.38), (0, 0.38)], water, root, sides=12)
    tube(kit, f"{p} stem", [(0, 0, 0.3), (0, 0, 1.3)], [0.2, 0.15], stone, root, sides=8)
    lathe(kit, f"{p} bowl", [(0, 1.2), (0.7, 1.3), (0.75, 1.45), (0, 1.38)], stone, root, sides=10)
    tube(kit, f"{p} jet", [(0, 0, 1.4), (0, 0, 1.9)], [0.08, 0.03], solid(kit, "jet", "#c8f0ff", 0.9), root, sides=6)


# ---------------------------------------------------------------- School Block
def tex_school(rand, W, H):
    w, h = 128, 40
    c = Canvas(w, h, "#ff9a9a")
    bricks(c, rand, 0, 0, w - 1, h - 1, "#ff8f8f", "#e06a7a", "#ffb0b0", bw=6, bh=3)
    c.rect(0, 0, w - 1, 2, "#b8b0e8")
    c.rect(0, h - 3, w - 1, h - 1, WHITE)
    c.rect(0, 19, w - 1, 20, WHITE)
    for row, y0 in enumerate((5, 24)):
        for x0 in range(4, w - 8, 12):
            if row == 0 and 54 <= x0 <= 70:
                continue
            c.rect(x0, y0, x0 + 8, y0 + 10, WHITE); c.rect(x0 + 1, y0 + 1, x0 + 7, y0 + 9, GLASS)
            c.rect(x0 + 4, y0 + 1, x0 + 4, y0 + 9, WHITE)
            if rand.random() < 0.3:
                c.rect(x0 + 1, y0 + 1, x0 + 3, y0 + 4, rand.choice((YEL, PINK, MINT)))   # kid art in the window
    c.rect(56, 3, 72, 17, WHITE); c.rect(57, 3, 71, 16, "#3a6fd8"); c.rect(64, 3, 64, 16, WHITE)
    c.rect(58, 12, 63, 15, GLASS); c.rect(65, 12, 70, 15, GLASS)
    return c


def school_bus(kit, root, p):
    """Parked school bus, 10 m long, facing -Y."""
    R = kit.rand
    side = tm(kit, "bus side", lambda: tex_bus(R))
    yel = solid(kit, "bus yellow", "#ffc93a", 0.4, shade="#f0b830")
    ink = solid(kit, "bus black", INK, 0.1)
    tbox(kit, f"{p} hull", (0, 0.8, 1.75), (2.5, 8.4, 2.4), side, root,
         uv={'all': (0.5, 0.2, 0.52, 0.22), 'px': (0, 0, 1, 1), 'nx': (0, 0, 1, 1)})
    tbox(kit, f"{p} roof", (0, 0.8, 3.0), (2.4, 8.3, 0.16), solid(kit, "bus roof", WHITE), root, taper=(0.92, 0.99))
    tbox(kit, f"{p} hood", (0, -4.2, 1.05), (2.3, 1.6, 1.1), yel, root, taper=(0.95, 0.9))
    tbox(kit, f"{p} windshield", (0, -3.42, 2.3), (2.3, 0.05, 1.0), solid(kit, "bus glass", GLASS, 0.3), root)
    tbox(kit, f"{p} grille", (0, -5.02, 1.0), (1.6, 0.05, 0.7), solid(kit, "grille", STEEL), root)
    tbox(kit, f"{p} bumper", (0, -5.1, 0.5), (2.5, 0.2, 0.24), ink, root)
    tbox(kit, f"{p} rear bumper", (0, 5.05, 0.55), (2.5, 0.2, 0.24), ink, root)
    for sx in (1, -1):
        tbox(kit, f"{p} flasher {sx}", (sx * 0.9, -3.35, 2.98), (0.2, 0.1, 0.16), solid(kit, "flasher", RED, 1.4), root)
    for nm, x, y in (("FL", -1.1, -3.9), ("FR", 1.1, -3.9), ("RL", -1.1, 3.0), ("RR", 1.1, 3.0)):
        tube(kit, f"{p} wheel {nm}", [(x - 0.15, y, 0.45), (x + 0.15, y, 0.45)], 0.45, solid(kit, "tire", "#2a2238", 0.15), root,
             sides=10, front=(0, 0, 1))
    tbox(kit, f"{p} stop arm", (-1.35, -2.7, 2.0), (0.03, 0.5, 0.5), solid(kit, "stop red", RED, 0.5), root)


def tex_bus(rand):
    c = Canvas(128, 40, "#ffc93a")
    c.speckle(rand, ["#f0b830", "#ffd85a"], 120)
    for y in (6, 12):
        c.rect(0, y, 127, y + 1, INK)
    for x in range(4, 124, 12):
        c.rect(x, 16, x + 9, 29, GLASS); c.dots([(x + 2, 26), (x + 3, 25), (x + 4, 24)], "#6f8cff")
    txt_c(c, "SCHOOL BUS", 64, 37, INK)
    return c


def school_block(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    walkm = road.ground_mats(kit)[1]
    asph = tm(kit, "road asphalt", lambda: road.tex_road(R), 0.15, 'REPEAT')
    W, D, H = 30.0, 10.0, 7.0

    def school(piv):
        t = tm(kit, "school front", lambda: tex_school(R, W, H))
        wall = tm(kit, "school brick", lambda: tex_brick_tile(R), 0.3, 'REPEAT')
        sblock(kit, f"{p} walls", piv, -W / 2, W / 2, -D / 2, D / 2, 0, H, wall, 3.0)
        plate(kit, f"{p} facade", piv, (0, -D / 2 - 0.03, H / 2), (W, 0.06, H), t)
        plate(kit, f"{p} back facade", piv, (0, D / 2 + 0.03, H / 2), (W, 0.06, H), t, 'py')
        tbox(kit, f"{p} roof", (0, 0, H + 0.15), (W + 0.4, D + 0.4, 0.3), solid(kit, "school roof", "#9d95d4", 0.3), piv)
        tbox(kit, f"{p} parapet", (0, -D / 2 - 0.05, H + 0.45), (W + 0.4, 0.3, 0.3), solid(kit, "parapet", WHITE), piv)
        # entrance portico with the sign
        for sx in (1, -1):
            tube(kit, f"{p} column {sx}", [(sx * 2.4, -D / 2 - 2.6, 0), (sx * 2.4, -D / 2 - 2.6, 3.6)], 0.22,
                 solid(kit, "column", WHITE, 0.4), piv, sides=8)
        tbox(kit, f"{p} portico", (0, -D / 2 - 1.4, 3.8), (6.0, 2.9, 0.4), solid(kit, "portico", "#b8b0e8"), piv)
        tbox(kit, f"{p} name sign", (0, -D / 2 - 2.88, 3.8), (5.8, 0.06, 0.36),
             tm(kit, "school sign", lambda: sign_tex("MAPLE GROVE ELEMENTARY", 96, 8, "#3a6fd8", WHITE, 1)), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        tbox(kit, f"{p} big sign", (0, -D / 2 - 0.1, H - 0.9), (12.0, 0.12, 1.2),
             tm(kit, "school big sign", lambda: sign_tex("", 96, 24, WHITE, "#3a6fd8", 1, border=PINK,
                                                         lines=["MAPLE GROVE", "ELEMENTARY"])), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        for i in range(3):
            tbox(kit, f"{p} step {i}", (0, -D / 2 - 0.6 - 0.4 * i, 0.08 + 0.0), (5.0 - 0.0 * i, 1.4 - 0.4 * i, 0.15 + 0.05 * (2 - i)),
                 solid(kit, "steps", "#d9d4ff", 0.3), piv)
        tbox(kit, f"{p} bell", (W / 2 - 3.0, 0, H + 0.9), (1.2, 1.2, 1.2), solid(kit, "bell tower", WHITE), piv)
        tbox(kit, f"{p} bell roof", (W / 2 - 3.0, 0, H + 1.8), (1.5, 1.5, 0.8), solid(kit, "bell roof", RED, 0.4), piv,
             taper=(0.1, 0.1))
    baked(kit, root, f"{p} school", (-2.0, 12.5, SIDE), 0, school)
    # drop-off loop with the bus, walkway, flagpole
    pad(kit, props, f"{p} drop off", -19.5, -14.0, -4.0, -7.0, asph, 5.0)
    pad(kit, props, f"{p} drive in", -19.5, -B2, -15.5, -14.0, asph, 5.0)
    pad(kit, props, f"{p} drive out", -8.0, -B2, -4.0, -14.0, asph, 5.0)
    pad(kit, props, f"{p} walk", -4.0, -12.0, 1.0, 4.6, walkm)
    pad(kit, props, f"{p} front walk", -1.5, -B2, 1.0, -12.0, walkm)
    at(kit, props, school_bus, f"{p} bus", -11.0, -10.5, -90, z=SIDE + 0.012)
    def flagpole(kit_, piv, n):
        tube(kit, f"{n} pole", [(0, 0, 0), (0, 0, 8.0)], [0.08, 0.05], solid(kit, "flag pole", STEEL), piv, sides=6)
        lowball(kit, f"{n} ball", (0, 0, 8.05), (0.1, 0.1, 0.1), solid(kit, "gold", "#ffd23a", 0.7), piv)
        tbox(kit, f"{n} flag", (0.75, 0, 7.4), (1.4, 0.03, 0.9), tm(kit, "flag", tex_flag), piv,
             uv={'all': (0, 0, 1, 1)})
        tube(kit, f"{n} base", [(0, 0, 0), (0, 0, 0.3)], 0.5, solid(kit, "flag base", "#b8b0e8"), piv, sides=8)
    at(kit, props, flagpole, f"{p} flagpole", 3.0, -9.0, 0)
    # blacktop playground (+X)
    pad(kit, props, f"{p} blacktop", 4.0, -18.0, 18.5, 4.5, asph, 5.0)
    yel, white = solid(kit, "lane yellow", YEL, 0.5), solid(kit, "lane white", WHITE, 0.4)
    for i in range(8):   # hopscotch
        tbox(kit, f"{p} hop {i}", (6.5 + (0.45 if i in (3, 4, 6) else 0) * (1 if i % 2 else -1), -15.0 + 0.9 * i, SIDE + 0.016),
             (0.8, 0.8, 0.01), solid(kit, "hop " + str(i % 3), (PINK, MINT, YEL)[i % 3], 0.45), props)
    for i, (x, y) in enumerate(((11.0, -14.0), (13.5, -14.0), (11.0, -11.5), (13.5, -11.5))):
        tbox(kit, f"{p} four square {i}", (x, y, SIDE + 0.016), (2.4, 2.4, 0.01), white, props)
        tbox(kit, f"{p} four square in {i}", (x, y, SIDE + 0.018), (2.2, 2.2, 0.01), solid(kit, "court", "#3d6ad8", 0.25), props)
    at(kit, props, swing_set, f"{p} swings", 12.0, -3.0, 0)
    at(kit, props, slide, f"{p} slide", 16.0, 1.0, 180)
    tube(kit, f"{p} hoop pole", [(16.8, -8.0, SIDE), (16.8, -8.0, SIDE + 3.0)], 0.07, solid(kit, "hoop pole", STEEL), props, sides=6)
    tbox(kit, f"{p} backboard", (16.5, -8.0, SIDE + 3.2), (0.06, 1.6, 1.0), solid(kit, "backboard", WHITE), props)
    torus(kit, f"{p} hoop", 0.25, 0.02, solid(kit, "hoop", ORNG, 0.6), props, loc=(16.15, -8.0, SIDE + 3.0), seg=8, sides=4)
    post = chain_post(kit)
    fence_gaps(kit, props, road.chainlink_fence, f"{p} play fence front", (3.8, -18.6), (19.0, -18.6), 2.5, [(1.0, 3.5)], post)
    fence_line(kit, props, road.chainlink_fence, f"{p} play fence side", (19.0, -18.6), (19.0, 5.0), 2.5, post)
    for i, (x, y) in enumerate(((-17.0, 17.0), (17.0, 17.0), (-17.0, -2.0), (1.5, -16.0))):
        at(kit, props, road.round_tree, f"{p} tree {i}", x, y, 50 * i, 0.9)
    for i, x in enumerate((-12.0, -7.0, 3.5, 8.0)):
        at(kit, props, road.bush, f"{p} bush {i}", x, 6.2, 30 * i, 0.8)
    at(kit, props, bench, f"{p} bench", -3.0, -4.0, 90)
    bake_props(kit, root, props, p)
    kids = [(6.5, -12.0), (11.0, -14.0), (13.5, -11.5), (12.0, -4.4), (15.0, -1.5), (8.5, -6.0), (-2.5, -2.0), (0.0, 3.5),
            (-6.0, 4.0), (3.0, -7.0), (-14.0, -6.0), (9.0, 2.5)]
    for i, (x, y) in enumerate(kids):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)


def tex_brick_tile(rand):
    c = Canvas(32, 32, "#ff8f8f")
    bricks(c, rand, 0, 0, 31, 31, "#ff8f8f", "#e06a7a", "#ffb0b0", bw=8, bh=4)
    return c


def tex_flag():
    c = Canvas(24, 16, WHITE)
    for y in range(0, 16, 4):
        c.rect(0, y, 23, y + 1, RED)
    c.rect(0, 8, 10, 15, BLUE)
    c.dots([(2, 13), (5, 13), (8, 13), (3, 10), (6, 10)], WHITE)
    return c


# ---------------------------------------------------------------- Coffee Strip
def tex_shopfront(rand, name, base, trim, sign_bg, sign_fg, w=64, h=40, door=True, k=1, logo=None):
    c = Canvas(w, h, base)
    c.speckle(rand, [hex_scale(base, 0.92)], w * h // 14)
    c.rect(0, 0, w - 1, 2, trim)
    c.rect(0, h - 14, w - 1, h - 1, sign_bg); c.rect(0, h - 14, w - 1, h - 14, trim); c.rect(0, h - 1, w - 1, h - 1, trim)
    txt_c(c, name, w // 2 + (4 if logo else 0), h - 4, sign_fg, k)
    if logo:
        logo(c, 6, h - 12)
    c.rect(4, 4, w - 5, h - 18, WHITE)
    c.rect(6, 6, w - 7, h - 20, GLASS)
    for x in range(6, w - 7, 10):
        c.rect(x, 6, x, h - 20, WHITE)
    c.dots([(9, 16), (10, 15), (11, 14), (30, 18), (31, 17)], "#6f8cff")
    if door:
        c.rect(w // 2 - 5, 3, w // 2 + 5, h - 18, trim); c.rect(w // 2 - 4, 4, w // 2 + 4, h - 20, GLASS)
        c.set(w // 2 + 3, 12, YEL)
    return c


def cup_logo(c, x, y):
    c.rect(x, y, x + 5, y + 7, WHITE); c.rect(x + 6, y + 2, x + 7, y + 5, WHITE)
    c.rect(x + 1, y + 5, x + 4, y + 6, "#6e3a1e")
    c.dots([(x + 1, y + 9), (x + 3, y + 10), (x + 2, y + 11)], WHITE)


def patio_table(kit, root, p, col):
    steel = solid(kit, "patio steel", "#4a3a6e", 0.25)
    tube(kit, f"{p} leg", [(0, 0, 0), (0, 0, 0.74)], 0.04, steel, root, sides=5)
    tube(kit, f"{p} foot", [(0, 0, 0), (0, 0, 0.04)], 0.3, steel, root, sides=6)
    lathe(kit, f"{p} top", [(0, 0.72), (0.45, 0.72), (0.45, 0.76), (0, 0.76)], solid(kit, "table top", WHITE, 0.35), root, sides=8,
          closed=True)
    tube(kit, f"{p} pole", [(0, 0, 0.76), (0, 0, 2.3)], 0.025, steel, root, sides=4)
    lathe(kit, f"{p} umbrella", [(1.1, 1.95), (0.6, 2.2), (0, 2.38)], tm(kit, f"umbrella {col}", lambda: tex_umbrella(col)), root,
          sides=8)
    for i in range(2):
        a = math.pi * i + 0.6
        cp = kit.empty(f"{p} chair {i}", root, (math.cos(a) * 0.75, math.sin(a) * 0.75, 0), (0, 0, math.degrees(a) - 90))
        tbox(kit, f"{p} chair seat {i}", (0, 0, 0.45), (0.42, 0.42, 0.05), solid(kit, f"chair {col}", col, 0.4), cp)
        tbox(kit, f"{p} chair back {i}", (0, 0.2, 0.7), (0.42, 0.04, 0.45), solid(kit, f"chair {col}", col, 0.4), cp)
        for sx in (1, -1):
            tbox(kit, f"{p} chair leg {i} {sx}", (sx * 0.18, 0, 0.22), (0.04, 0.38, 0.44), steel, cp)


def tex_umbrella(col):
    c = Canvas(32, 8, WHITE)
    for x in range(0, 32, 8):
        c.rect(x, 0, x + 3, 7, col)
    c.rect(0, 0, 31, 0, hex_scale(col, 0.8))
    return c


def coffee_strip(kit, root, p):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    walkm = road.ground_mats(kit)[1]
    asph = tm(kit, "road asphalt", lambda: road.tex_road(R), 0.15, 'REPEAT')
    brick = tm(kit, "patio brick", lambda: tex_pavers(R), 0.3, 'REPEAT')
    pad(kit, props, f"{p} plaza", -B2, -B2, B2, 4.0, walkm, 2.0)
    pad(kit, props, f"{p} patio", -18.5, -18.5, -4.0, -6.0, brick, 2.0, z=0.02)
    pad(kit, props, f"{p} parking", 2.0, -19.5, 19.5, -2.0, asph, 5.0, z=0.02)
    for i in range(6):
        tbox(kit, f"{p} stall {i}", (4.0 + 3.0 * i, -14.0, SIDE + 0.026), (0.12, 5.0, 0.01), solid(kit, "lane white", WHITE, 0.4), props)
    shops = [("BEAN THERE", -12.0, 12.0, "#ffe0b0", "#6e3a1e", "#6e3a1e", WHITE, cup_logo),
             ("SUDS", 2.0, 10.0, "#c8f0ff", BLUE, BLUE, WHITE, None),
             ("VIDEO", 14.0, 10.0, "#e8d8ff", PURP, YEL, PURP, None)]
    for i, (nm, x, w, base, trim, sbg, sfg, logo) in enumerate(shops):
        def shop(piv, nm=nm, w=w, base=base, trim=trim, sbg=sbg, sfg=sfg, logo=logo, i=i):
            H, D = 5.0, 9.0
            t = tm(kit, f"shopfront {nm}", lambda: tex_shopfront(R, nm, base, trim, sbg, sfg, 64, 40, True, 1, logo))
            wall = tm(kit, f"shop wall {i}", lambda: stops.tex_stucco(R, base), 0.3, 'REPEAT')
            sblock(kit, f"{p} shop {i} walls", piv, -w / 2, w / 2, -D / 2, D / 2, 0, H, wall, 3.0)
            plate(kit, f"{p} shop {i} front", piv, (0, -D / 2 - 0.03, H / 2), (w, 0.06, H), t)
            tbox(kit, f"{p} shop {i} roof", (0, 0, H + 0.2), (w + 0.3, D + 0.3, 0.4), solid(kit, f"shop roof {i}", trim, 0.35), piv)
            tbox(kit, f"{p} shop {i} awning", (0, -D / 2 - 0.8, 3.0), (w - 0.6, 1.6, 0.08),
                 tm(kit, f"awning {i}", lambda: tex_umbrella(trim if trim != "#6e3a1e" else PINK)), piv, rot=(-16, 0, 0),
                 uv={'all': (0, 0, w / 2, 1)})
        baked(kit, root, f"{p} {('coffee shop', 'laundromat', 'video store')[i]}", (x, 9.0, SIDE + 0.012), 0, shop)
    # coffee shop extras: chalkboard, big cup on the roof
    def roof_cup(piv):
        lathe(kit, f"{p} big cup", [(0, 0), (0.9, 0), (1.3, 2.2), (1.4, 2.4), (0, 2.4)], tm(kit, "big cup", tex_big_cup), piv, sides=10)
        lathe(kit, f"{p} big lid", [(1.45, 2.4), (1.3, 2.7), (0, 2.75)], solid(kit, "lid", WHITE, 0.4), piv, sides=10)
        tube(kit, f"{p} big straw", [(0.3, 0, 2.6), (0.4, 0, 3.6)], 0.1, solid(kit, "straw", PINK, 0.5), piv, sides=6)
    baked(kit, root, f"{p} roof cup", (-12.0, 9.0, SIDE + 5.4), 0, roof_cup)
    cols = (PINK, MINT, YEL, BLUE)
    tables = [(-15.5, -9.0), (-10.0, -9.0), (-15.5, -14.5), (-10.0, -14.5)]
    for i, (x, y) in enumerate(tables):
        at(kit, props, lambda k, r, n, c=cols[i]: patio_table(k, r, n, c), f"{p} table {i}", x, y, 20 * i, z=SIDE + 0.02)
    for i, x in enumerate((-18.0, -6.0)):
        at(kit, props, flower_bed, f"{p} planter {i}", x, -5.3, 0, 0.8)
    at(kit, props, chalkboard, f"{p} chalkboard", -6.0, -2.8, 20)
    at(kit, props, road.trash_can, f"{p} trash", -3.0, -1.0, 0)
    at(kit, props, bench, f"{p} bench", 6.0, 2.6, 0)
    at(kit, props, lambda k, r, n: car(k, r, n, MINT), f"{p} car 0", 5.5, -14.0, 180, z=SIDE + 0.02)
    at(kit, props, lambda k, r, n: car(k, r, n, YEL), f"{p} car 1", 14.5, -14.0, 0, z=SIDE + 0.02)
    for i, (x, y) in enumerate(((-18.0, 17.5), (18.0, 17.5), (-2.0, 17.0))):
        at(kit, props, road.round_tree if i != 2 else road.bush, f"{p} tree {i}", x, y, 30 * i, 0.85)
    at(kit, props, dumpster, f"{p} dumpster", 8.0, 16.5, 0)
    for i, (x, y) in enumerate(((1.0, -18.5), (19.0, -1.0))):
        at(kit, props, road.street_lamp, f"{p} lamp {i}", x, y, 90 if i == 0 else 180)
    bake_props(kit, root, props, p)
    for i, (x, y) in enumerate(tables):
        a = 20 * i
        socket(kit, root, f"cup {i}", (x + 0.15, y - 0.12, SIDE + 0.02 + 0.76), 0)
    socket(kit, root, "cup 4", (-12.0 - 1.0, 9.0 - 4.5 - 0.6, SIDE + 1.0), 0)
    kids = [(-12.5, -3.5), (-3.0, -8.0), (-7.5, -17.5), (2.0, 1.8), (8.5, -3.6), (12.0, 2.5), (16.0, -6.0), (-1.0, -17.0)]
    for i, (x, y) in enumerate(kids):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)


def tex_pavers(rand):
    c = Canvas(32, 32, "#e8907a")
    bricks(c, rand, 0, 0, 31, 31, "#e8907a", "#c46a5a", "#f4a890", bw=8, bh=4)
    return c


def tex_big_cup():
    c = Canvas(32, 32, WHITE)
    c.rect(0, 8, 31, 22, "#d9a868")
    txt_c(c, "BEAN", 16, 20, "#6e3a1e")
    txt_c(c, "THERE", 8, 13, PINK); txt_c(c, "THERE", 24, 13, PINK)
    return c


def chalkboard(kit, root, p):
    wood = solid(kit, "board wood", "#a8642a")
    board = tm(kit, "chalkboard", lambda: sign_tex("", 24, 32, "#2a3a2a", WHITE, 1, lines=["ICED", "COFFEE", "$3"]))
    for s in (1, -1):
        tbox(kit, f"{p} board {s}", (0, s * 0.18, 0.55), (0.6, 0.04, 1.0), board, root, rot=(s * 12, 0, 0),
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
        tbox(kit, f"{p} frame {s}", (0, s * 0.2, 1.06), (0.64, 0.05, 0.05), wood, root, rot=(s * 12, 0, 0))


def dumpster(kit, root, p):
    tbox(kit, f"{p} bin", (0, 0, 0.7), (2.0, 1.3, 1.2), solid(kit, "dumpster", "#3fae8a", 0.3, shade="#2a8a6a"), root, taper=(1.05, 1.1))
    tbox(kit, f"{p} lid", (0, 0.05, 1.36), (2.1, 1.45, 0.08), solid(kit, "dumpster lid", INK, 0.15), root, rot=(-6, 0, 0))
    for sx in (1, -1):
        tube(kit, f"{p} wheel {sx}", [(sx * 0.8, -0.5, 0.1), (sx * 0.8, -0.4, 0.1)], 0.1, solid(kit, "tire", "#2a2238", 0.15), root,
             sides=6, side=(1, 0, 0))


# ---------------------------------------------------------------- Hillside Estates
CREAM = "#fff1dc"; CREAM_D = "#f0dcc0"; GOLDC = "#ffd23a"; HEDGE = "#2a9e5a"


def tex_mansion(rand, w=128, h=64):
    c = Canvas(w, h, CREAM)
    c.speckle(rand, [CREAM_D, "#fff8ec"], w * h // 10)
    c.rect(0, 0, w - 1, 3, "#d9c8b0")
    c.rect(0, 30, w - 1, 31, GOLDC)
    c.rect(0, h - 3, w - 1, h - 1, GOLDC)
    for row, y0 in enumerate((6, 35)):
        for x0 in range(5, w - 10, 13):
            if row == 0 and w // 2 - 12 <= x0 <= w // 2 + 4:
                continue
            c.rect(x0, y0, x0 + 8, y0 + 18, WHITE); c.rect(x0 + 1, y0 + 1, x0 + 7, y0 + 17, GLASS)
            c.rect(x0 + 4, y0 + 1, x0 + 4, y0 + 17, WHITE); c.rect(x0 + 1, y0 + 9, x0 + 7, y0 + 9, WHITE)
            c.rect(x0 - 1, y0 + 19, x0 + 9, y0 + 20, GOLDC)
            if rand.random() < 0.4:
                c.rect(x0 + 1, y0 + 1, x0 + 3, y0 + 8, "#ffd36b")
    c.rect(w // 2 - 8, 4, w // 2 + 8, 27, "#7a3a1c"); c.rect(w // 2 - 7, 5, w // 2 + 7, 26, "#a8642a")
    c.rect(w // 2, 5, w // 2, 26, "#7a3a1c"); c.dots([(w // 2 - 2, 15), (w // 2 + 2, 15)], GOLDC)
    disc(c, w // 2, 24, 5, "#7a3a1c")
    return c


def mansion(kit, piv, p, W=18.0, D=11.0, H=7.6, wings=True):
    R = kit.rand
    face = tm(kit, "mansion front", lambda: tex_mansion(R))
    wall = tm(kit, "mansion wall", lambda: stops.tex_stucco(R, CREAM), 0.32, 'REPEAT')
    roofm = tm(kit, "mansion roof", lambda: tex_shingles(R, "#6a5aa8", "#4a3a88"), ext='REPEAT')
    white, gold = solid(kit, "column", WHITE, 0.4, shade="#ece4f4"), solid(kit, "gold trim", GOLDC, 0.7, shade="#d9901a")
    tbox(kit, f"{p} plinth", (0, 0, 0.25), (W + 0.4, D + 0.4, 0.5), solid(kit, "plinth", "#d9d4ff", 0.3), piv)
    sblock(kit, f"{p} walls", piv, -W / 2, W / 2, -D / 2, D / 2, 0.5, H, wall, 3.0)
    plate(kit, f"{p} facade", piv, (0, -D / 2 - 0.03, (H + 0.5) / 2), (W, 0.06, H - 0.5), face)
    plate(kit, f"{p} back", piv, (0, D / 2 + 0.03, (H + 0.5) / 2), (W, 0.06, H - 0.5), face, 'py')
    tbox(kit, f"{p} cornice", (0, 0, H + 0.12), (W + 0.6, D + 0.6, 0.25), white, piv)
    tbox(kit, f"{p} roof", (0, 0, H + 1.6), (W + 0.5, D + 0.5, 2.8), roofm, piv, taper=(0.62, 0.25),
         uv={'all': (0, 0, W / 3, 1.0)})
    for sx in (1, -1):
        tbox(kit, f"{p} chimney {sx}", (sx * W * 0.32, 0.8, H + 2.6), (0.9, 0.9, 2.2), solid(kit, "chimney", CREAM_D), piv)
        lowball(kit, f"{p} finial {sx}", (sx * W * 0.31 * 0.62 + 0, 0, H + 3.15), (0.25, 0.25, 0.3), gold, piv, smooth=False)
    # portico with white columns and a gold-trimmed pediment
    for i, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
        tube(kit, f"{p} column {i}", [(x, -D / 2 - 2.4, 0.5), (x, -D / 2 - 2.4, H - 0.3)], 0.26, white, piv, sides=8)
        tbox(kit, f"{p} capital {i}", (x, -D / 2 - 2.4, H - 0.2), (0.7, 0.7, 0.2), gold, piv)
    tbox(kit, f"{p} entablature", (0, -D / 2 - 1.25, H), (7.6, 2.9, 0.6), white, piv)
    mb = MB()
    road.extrude_y(mb, [(-3.9, H + 0.3), (3.9, H + 0.3), (0, H + 2.0)], -D / 2 - 2.75, -D / 2 + 0.2, 0, (0, 0, 0))
    mb.obj(kit, f"{p} pediment", [white], piv)
    lowball(kit, f"{p} crest", (0, -D / 2 - 2.8, H + 0.95), (0.5, 0.08, 0.45), gold, piv, smooth=False)
    tbox(kit, f"{p} porch", (0, -D / 2 - 1.4, 0.4), (8.4, 3.2, 0.8), solid(kit, "marble", "#f4f0ff", 0.35, shade="#d9d4ff"), piv)
    for i in range(3):
        tbox(kit, f"{p} stair {i}", (0, -D / 2 - 3.2 - 0.4 * i, 0.12 + 0.13 * (2 - i)), (4.0, 0.5, 0.25 + 0.26 * (2 - i)),
             solid(kit, "marble", "#f4f0ff", 0.35, shade="#d9d4ff"), piv)
    for sx in (1, -1):
        lowball(kit, f"{p} lion {sx}", (sx * 2.4, -D / 2 - 3.3, 1.05), (0.35, 0.5, 0.45), gold, piv, smooth=False)
    if wings:
        for sx in (1, -1):
            x0 = W / 2 if sx > 0 else -W / 2 - 6.0
            sblock(kit, f"{p} wing {sx}", piv, x0, x0 + 6.0, -D / 2 + 1.5, D / 2 - 1.0, 0.0, 4.6, wall, 3.0)
            plate(kit, f"{p} wing face {sx}", piv, (x0 + 3.0, -D / 2 + 1.47, 2.4), (6.0, 0.06, 4.2), tm(kit, "wing face",
                                                                                                     lambda: tex_mansion(R, 48, 32)))
            tbox(kit, f"{p} wing roof {sx}", (x0 + 3.0, 0.25, 5.2), (6.4, D - 2.0, 1.2), roofm, piv, taper=(0.7, 0.4),
                 uv={'all': (0, 0, 2, 0.5)})
            for k in range(4):
                tbox(kit, f"{p} balustrade {sx} {k}", (x0 + 0.75 + 1.5 * k, -D / 2 + 1.3, 4.85), (0.2, 0.2, 0.5), gold, piv)


def hedge(kit, root, p, L=4.0, H=1.4, W=1.0):
    m = tm(kit, "hedge", lambda: road.tex_leaf(kit.rand, HEDGE), 0.3)
    tbox(kit, f"{p} hedge", (0, 0, H / 2), (L, W, H), m, root, taper=(0.95, 0.9), uv={'all': (0, 0, L / 1.5, H / 1.5)})


def hedge_line(kit, d, name, a, b, gaps=(), H=1.4):
    a, b = Vector(a), Vector(b)
    L = (b - a).length
    u = (b - a) / L
    rz = math.degrees(math.atan2(u.y, u.x))
    cuts, t = [], 0.0
    for g0, g1 in sorted(gaps):
        if g0 > t + 0.3:
            cuts.append((t, g0))
        t = g1
    if L > t + 0.3:
        cuts.append((t, L))
    for i, (t0, t1) in enumerate(cuts):
        c = a + u * (t0 + t1) / 2
        piv = kit.empty(f"{name} {i}", d, (c.x, c.y, SIDE), (0, 0, rz))
        hedge(kit, piv, f"{name} {i}", t1 - t0, H)


def topiary(kit, root, p, kind=0):
    pot = solid(kit, "topiary pot", WHITE, 0.4, shade="#ece4f4")
    lathe(kit, f"{p} pot", [(0.3, 0.0), (0.42, 0.55), (0.48, 0.6), (0, 0.58)], pot, root, sides=8)
    tbox(kit, f"{p} pot band", (0, 0, 0.5), (0.9, 0.9, 0.06), solid(kit, "gold trim", GOLDC, 0.7), root, taper=(1, 1))
    leaf = tm(kit, "hedge", lambda: road.tex_leaf(kit.rand, HEDGE), 0.3)
    tube(kit, f"{p} trunk", [(0, 0, 0.55), (0, 0, 1.1)], 0.05, solid(kit, "bark", "#7a4a5a"), root, sides=4)
    if kind == 0:
        lowball(kit, f"{p} ball", (0, 0, 1.45), (0.5, 0.5, 0.5), leaf, root)
        lowball(kit, f"{p} ball top", (0, 0, 2.15), (0.3, 0.3, 0.3), leaf, root)
    else:
        tube(kit, f"{p} cone", [(0, 0, 0.9), (0, 0, 2.6)], [0.55, 0.02], leaf, root, sides=7)


def fountain_big(kit, root, p):
    stone = solid(kit, "fountain stone", "#f4f0ff", 0.38, shade="#d9d4ff")
    gold = solid(kit, "gold trim", GOLDC, 0.7, shade="#d9901a")
    water = tm(kit, "fountain water", lambda: tex_water(kit.rand), 0.6, 'REPEAT')
    lathe(kit, f"{p} basin", [(0, 0.0), (2.6, 0.0), (2.6, 0.6), (2.35, 0.6), (2.35, 0.15), (0, 0.15)], stone, root, sides=14)
    lathe(kit, f"{p} pool", [(2.37, 0.45), (0, 0.45)], water, root, sides=14)
    tube(kit, f"{p} stem", [(0, 0, 0.3), (0, 0, 1.5)], [0.3, 0.2], stone, root, sides=8)
    lathe(kit, f"{p} bowl 1", [(0, 1.4), (1.2, 1.5), (1.25, 1.7), (0, 1.6)], stone, root, sides=12)
    lathe(kit, f"{p} pool 1", [(1.15, 1.66), (0, 1.66)], water, root, sides=12)
    tube(kit, f"{p} stem 2", [(0, 0, 1.6), (0, 0, 2.4)], [0.15, 0.1], stone, root, sides=8)
    lathe(kit, f"{p} bowl 2", [(0, 2.3), (0.6, 2.4), (0.62, 2.55), (0, 2.5)], gold, root, sides=10)
    lowball(kit, f"{p} cherub", (0, 0, 2.85), (0.22, 0.2, 0.3), gold, root, smooth=False)
    tube(kit, f"{p} jet", [(0, 0, 3.0), (0, 0, 3.6)], [0.07, 0.02], solid(kit, "jet", "#c8f0ff", 0.9), root, sides=6)
    for k in range(6):
        a = 2 * math.pi * k / 6
        tube(kit, f"{p} spout {k}", [(math.cos(a) * 0.5, math.sin(a) * 0.5, 2.45), (math.cos(a) * 1.0, math.sin(a) * 1.0, 2.0),
                                     (math.cos(a) * 1.15, math.sin(a) * 1.15, 1.75)], 0.035, solid(kit, "jet", "#c8f0ff", 0.9),
             root, sides=4)


def iron_gate(kit, root, p, W=6.0):
    """Gated driveway: brick pillars with gold balls and a closed double iron gate between them (along X)."""
    brick = tm(kit, "pillar brick", lambda: tex_brick_tile(kit.rand), 0.3, 'REPEAT')
    iron = solid(kit, "wrought iron", "#4a3a6e", 0.25, shade="#3a2a5a")
    gold = solid(kit, "gold trim", GOLDC, 0.7)
    for sx in (1, -1):
        sblock(kit, f"{p} pillar {sx}", root, sx * W / 2 - 0.4, sx * W / 2 + 0.4, -0.4, 0.4, 0, 2.4, brick, 1.0)
        tbox(kit, f"{p} cap {sx}", (sx * W / 2, 0, 2.5), (0.95, 0.95, 0.2), solid(kit, "cap stone", WHITE), root)
        lowball(kit, f"{p} ball {sx}", (sx * W / 2, 0, 2.85), (0.3, 0.3, 0.3), gold, root, smooth=False)
    n = 14
    for i in range(n):
        x = -W / 2 + 0.5 + (W - 1.0) * i / (n - 1)
        h = 1.8 + 0.35 * math.sin(math.pi * ((i % (n // 2)) / (n // 2 - 1)))
        tbox(kit, f"{p} bar {i}", (x, 0, h / 2), (0.05, 0.05, h), iron, root)
        lowball(kit, f"{p} tip {i}", (x, 0, h + 0.05), (0.05, 0.05, 0.08), gold, root, smooth=False)
    for z in (0.3, 1.6):
        tbox(kit, f"{p} rail {z}", (0, 0, z), (W - 0.8, 0.06, 0.06), iron, root)
    tbox(kit, f"{p} crest", (0, -0.03, 1.15), (0.6, 0.04, 0.5), gold, root)


def tennis_court(kit, root, p):
    court = solid(kit, "court", "#3fae8a", 0.3, shade="#2a8a6a")
    white = solid(kit, "lane white", WHITE, 0.4)
    tbox(kit, f"{p} surface", (0, 0, 0.01), (11.0, 22.0, 0.02), court, root)
    tbox(kit, f"{p} inner", (0, 0, 0.015), (8.2, 23.8 * 0.0 + 18.0, 0.02), solid(kit, "court inner", "#4a6fd8", 0.3), root)
    for (x, y, w, h) in ((0, 9.0, 8.2, 0.08), (0, -9.0, 8.2, 0.08), (4.1, 0, 0.08, 18.0), (-4.1, 0, 0.08, 18.0), (0, 0, 0.08, 9.0),
                         (0, 4.5, 8.2, 0.08), (0, -4.5, 8.2, 0.08)):
        tbox(kit, f"{p} line {x} {y} {w}", (x, y, 0.03), (w, h, 0.01), white, root)
    tbox(kit, f"{p} net", (0, 0, 0.5), (10.0, 0.04, 0.9), cut_mat(kit, "chain link", tex_chain), root, uv={'all': (0, 0, 30, 3)})
    tbox(kit, f"{p} net band", (0, 0, 0.95), (10.0, 0.06, 0.08), white, root)
    for sx in (1, -1):
        tube(kit, f"{p} net post {sx}", [(sx * 5.1, 0, 0), (sx * 5.1, 0, 1.05)], 0.05, solid(kit, "post", STEEL), root, sides=4)


def pool(kit, root, p):
    coping = solid(kit, "coping", WHITE, 0.4, shade="#ece4f4")
    water = tm(kit, "pool water", lambda: tex_water(kit.rand), 0.6, 'REPEAT')
    tbox(kit, f"{p} deck", (0, 0, 0.02), (12.0, 8.0, 0.04), tm(kit, "pool deck", lambda: tex_pavers(kit.rand), 0.3, 'REPEAT'), root,
         uv={'all': (0, 0, 6, 4)})
    for sy in (1, -1):
        tbox(kit, f"{p} coping y {sy}", (0, sy * 2.6, 0.08), (9.0, 0.4, 0.12), coping, root)
    for sx in (1, -1):
        tbox(kit, f"{p} coping x {sx}", (sx * 4.3, 0, 0.08), (0.4, 5.6, 0.12), coping, root)
    tbox(kit, f"{p} water", (0, 0, 0.05), (8.2, 4.8, 0.02), water, root, uv={'all': (0, 0, 3, 2)})
    tbox(kit, f"{p} board", (-4.0, 0, 0.45), (2.0, 0.5, 0.08), solid(kit, "diving board", PINK, 0.45), root)
    tbox(kit, f"{p} board stand", (-4.8, 0, 0.22), (0.4, 0.4, 0.44), coping, root)
    for i, x in enumerate((-2.0, 0.5, 3.0)):
        lc = kit.empty(f"{p} lounger {i}", root, (x, 3.5, 0.04), (0, 0, 180))
        tbox(kit, f"{p} lounger {i}", (0, 0, 0.35), (0.7, 1.8, 0.08), solid(kit, "lounger", (MINT, YEL, PINK)[i], 0.4), lc)
        tbox(kit, f"{p} lounger back {i}", (0, -0.75, 0.6), (0.7, 0.6, 0.08), solid(kit, "lounger", (MINT, YEL, PINK)[i], 0.4), lc,
             rot=(40, 0, 0))
        tbox(kit, f"{p} lounger legs {i}", (0, 0, 0.17), (0.6, 1.6, 0.3), solid(kit, "lounger frame", WHITE), lc)
    ring = solid(kit, "float", ORNG, 0.5)
    torus(kit, f"{p} float", 0.45, 0.14, ring, root, loc=(1.5, -0.5, 0.12), seg=10, sides=5)


def mansion_block(kit, root, p, variant):
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    gravel = tm(kit, "white gravel", lambda: tex_white_gravel(R), 0.3, 'REPEAT')
    walkm = road.ground_mats(kit)[1]
    mx = 0.0 if variant == 0 else 2.0
    baked(kit, root, f"{p} mansion", (mx, 8.0, SIDE), 0, lambda piv: mansion(kit, piv, f"{p} mansion"))
    # gated drive: curved approach as two straight pads around the fountain
    gx = -10.0 if variant == 0 else 12.0
    pad(kit, props, f"{p} drive in", gx - 1.8, -B2, gx + 1.8, -9.0, gravel, 3.0)
    pad(kit, props, f"{p} forecourt", -9.0 + mx, -9.0, 9.0 + mx, -3.6, gravel, 3.0)
    lo, hi = sorted((gx, mx))
    pad(kit, props, f"{p} drive link", lo - 1.8, -9.0, hi + 1.8, -5.5, gravel, 3.0)
    pad(kit, props, f"{p} foot path", mx - 1.0, -B2, mx + 1.0, -9.0, walkm)
    at(kit, props, fountain_big, f"{p} fountain", mx, -13.0, 0)
    at(kit, props, iron_gate, f"{p} gate", gx, -19.3, 0)
    # hedges around the estate with the gate and a pedestrian gap
    hedge_line(kit, props, f"{p} hedge front", (-19.4, -19.3), (19.4, -19.3),
               [(gx + 19.4 - 3.5, gx + 19.4 + 3.5), (mx + 19.4 - 1.2, mx + 19.4 + 1.2)])
    for sx in (1, -1):
        hedge_line(kit, props, f"{p} hedge side {sx}", (sx * 19.3, -18.6), (sx * 19.3, 19.3), [(17.0, 19.5)])
    hedge_line(kit, props, f"{p} hedge back", (-18.6, 19.3), (18.6, 19.3), [(17.4, 19.8)])
    for i, (x, y, k) in enumerate(((mx - 5.0, -4.6, 0), (mx + 5.0, -4.6, 0), (mx - 8.5, -8.0, 1), (mx + 8.5, -8.0, 1),
                                   (mx - 3.5, -16.0, 1), (mx + 3.5, -16.0, 1))):
        at(kit, props, lambda kk, r, n, k=k: topiary(kk, r, n, k), f"{p} topiary {i}", x, y, 0)
    if variant == 0:
        at(kit, props, tennis_court, f"{p} tennis", 13.0, -6.0, 0, z=SIDE + 0.01)
        post = chain_post(kit)
        fence_gaps(kit, props, road.chainlink_fence, f"{p} court fence", (7.0, -18.0), (7.0, 6.0), 2.5, [(10.0, 13.0)], post)
        kids = [(-14.0, -14.0), (-4.0, -11.0), (4.0, -11.0), (10.0, -2.0), (-15.0, 6.0), (15.5, 12.0)]
    else:
        at(kit, props, pool, f"{p} pool", -11.0, -6.0, 90, z=SIDE + 0.01)
        kids = [(-14.5, -14.0), (-8.0, -2.0), (-14.0, 1.5), (5.0, -11.0), (-3.0, -11.0), (16.0, 14.0)]
    for i, (x, y) in enumerate(((-16.5, 16.5), (16.5, 16.5), (-17.0, -16.0) if variant else (17.0, -16.5))):
        at(kit, props, road.round_tree, f"{p} tree {i}", x, y, 40 * i, 0.95)
    for i, (x, y) in enumerate(((mx - 9.0, 1.0), (mx + 9.0, 1.0))):
        at(kit, props, road.street_lamp, f"{p} lamp {i}", x, y, 0)
    bake_props(kit, root, props, p)
    for i, (x, y) in enumerate(kids):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 180 if y > 0 else 0)


def tex_white_gravel(rand):
    c = Canvas(32, 32, "#ece4f4")
    c.speckle(rand, ["#d9d0ea", "#fff8ff", "#c8bce0"], 300)
    return c


def vault_mansion(kit, root, p):
    """Mansion on +X, an open-front vault room (garage-like) on -X opening onto a paved courtyard that is reachable on
    foot from the street through a hedge gap. Vault socket against the vault room's back wall, plate socket 6 m in
    front of it."""
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    gravel = tm(kit, "white gravel", lambda: tex_white_gravel(R), 0.3, 'REPEAT')
    brick = tm(kit, "patio brick", lambda: tex_pavers(R), 0.3, 'REPEAT')
    walkm = road.ground_mats(kit)[1]
    baked(kit, root, f"{p} mansion", (6.5, 8.5, SIDE), 0, lambda piv: mansion(kit, piv, f"{p} mansion", W=14.0, D=10.0, wings=False))
    # vault room: back wall at y = 14, side walls, flat roof, open toward -Y
    vx, vback = -11.0, 14.0

    def vault_room(piv):
        wall = tm(kit, "mansion wall", lambda: stops.tex_stucco(R, CREAM), 0.32, 'REPEAT')
        gold = solid(kit, "gold trim", GOLDC, 0.7, shade="#d9901a")
        W, D, H = 9.0, 8.0, 4.0
        sblock(kit, f"{p} vault back wall", piv, -W / 2, W / 2, 0.0, 0.5, 0, H, wall, 3.0)
        for sx in (1, -1):
            sblock(kit, f"{p} vault side {sx}", piv, sx * W / 2 - (0.5 if sx > 0 else 0), sx * W / 2 + (0 if sx > 0 else 0.5),
                   -D, 0.5, 0, H, wall, 3.0)
        tbox(kit, f"{p} vault roof", (0, -D / 2 + 0.25, H + 0.15), (W + 0.6, D + 1.0, 0.3), solid(kit, "vault roof", "#6a5aa8"), piv)
        tbox(kit, f"{p} vault fascia", (0, -D - 0.2, H - 0.1), (W + 0.6, 0.3, 0.6), gold, piv)
        tbox(kit, f"{p} vault sign", (0, -D - 0.37, H - 0.1), (3.2, 0.04, 0.5),
             tm(kit, "private sign", lambda: sign_tex("PRIVATE", 40, 8, "#6a5aa8", GOLDC, 1)), piv,
             uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
        for sx in (1, -1):
            tube(kit, f"{p} vault column {sx}", [(sx * (W / 2 - 0.25), -D - 0.1, 0), (sx * (W / 2 - 0.25), -D - 0.1, H)], 0.28,
                 solid(kit, "column", WHITE, 0.4), piv, sides=8)
        tbox(kit, f"{p} vault floor", (0, -D / 2 + 0.25, 0.02), (W - 1.0, D, 0.04), solid(kit, "marble", "#f4f0ff", 0.35,
                                                                                         shade="#d9d4ff"), piv)
        tbox(kit, f"{p} red carpet", (0, -D / 2, 0.05), (1.6, D - 0.5, 0.02), solid(kit, "carpet", RED, 0.35), piv)
        for sx in (1, -1):   # velvet rope posts
            for k in range(2):
                tube(kit, f"{p} rope post {sx} {k}", [(sx * 1.4, -2.0 - 3.0 * k, 0), (sx * 1.4, -2.0 - 3.0 * k, 1.0)], 0.05, gold, piv,
                     sides=6)
            tube(kit, f"{p} rope {sx}", [(sx * 1.4, -2.0, 0.9), (sx * 1.4, -3.5, 0.7), (sx * 1.4, -5.0, 0.9)], 0.03,
                 solid(kit, "velvet rope", RED, 0.4), piv, sides=4)
    baked(kit, root, f"{p} vault room", (vx, vback, SIDE), 0, vault_room)
    # courtyard and approach
    pad(kit, props, f"{p} courtyard", -18.5, -6.0, -3.5, 14.0, brick, 2.0)
    pad(kit, props, f"{p} courtyard path", -12.0, -B2, -10.0, -6.0, walkm)
    pad(kit, props, f"{p} drive", 4.5, -B2, 8.5, 1.0, gravel, 3.0)
    at(kit, props, iron_gate, f"{p} gate", 6.5, -19.3, 0)
    at(kit, props, fountain_big, f"{p} fountain", -11.0, -12.0, 0)
    hedge_line(kit, props, f"{p} hedge front", (-19.4, -19.3), (19.4, -19.3), [(6.5 + 19.4 - 3.5, 6.5 + 19.4 + 3.5), (6.4, 10.4)])
    for sx in (1, -1):
        hedge_line(kit, props, f"{p} hedge side {sx}", (sx * 19.3, -18.6), (sx * 19.3, 19.3), [(17.0, 19.5)])
    hedge_line(kit, props, f"{p} hedge back", (-18.6, 19.3), (18.6, 19.3))
    hedge_line(kit, props, f"{p} hedge split", (-2.5, -17.0), (-2.5, 2.0), [(8.0, 10.0)])
    for i, (x, y, k) in enumerate(((-16.5, -4.0, 1), (-5.5, -4.0, 1), (2.5, -3.0, 0), (10.5, -3.0, 0))):
        at(kit, props, lambda kk, r, n, k=k: topiary(kk, r, n, k), f"{p} topiary {i}", x, y, 0)
    at(kit, props, road.round_tree, f"{p} tree 0", 16.5, -15.0, 0, 0.95)
    at(kit, props, road.round_tree, f"{p} tree 1", 16.5, 16.5, 90, 0.9)
    at(kit, props, lambda k, r, n: car(k, r, n, GOLDC), f"{p} gold car", 6.5, -6.0, 0, z=SIDE + 0.012)
    bake_props(kit, root, props, p)
    socket(kit, root, "vault", (vx, vback - 0.32, SIDE + 0.04), 0)
    socket(kit, root, "plate", (vx, vback - 0.32 - 6.0, SIDE + 0.04), 0)
    for i, (x, y) in enumerate(((-14.5, -9.0), (-7.5, -9.5), (12.0, -10.0), (0.5, -14.0))):
        socket(kit, root, f"kid {i}", (x, y, SIDE), 0)


# ---------------------------------------------------------------- Moving Day (the tutorial yard)
def tex_dad_box():
    c = sign_tex("DAD", 16, 16, "#d8a868", INK, 1)
    c.rect(0, 13, 15, 14, "#f0d8a0")
    c.rect(0, 0, 15, 0, "#a87a40")
    return c


def moving_pile(kit, root, p):
    """Dad's stuff, thrown out on the lawn: taped boxes, an armchair, a floor lamp and the TV."""
    box = tm(kit, "dad box", tex_dad_box)
    for i, (x, y, z, s, rz) in enumerate(((0.0, 0.0, 0.0, 0.6, 10), (0.7, 0.1, 0.0, 0.5, -15), (0.3, 0.05, 0.6, 0.45, 30),
                                          (-0.8, -0.5, 0.0, 0.55, 5), (1.4, -0.6, 0.0, 0.4, 40))):
        tbox(kit, f"{p} box {i}", (x, y, z + s / 2), (s, s, s), box, root, rot=(0, 0, rz), uv={'all': (0, 0, 1, 1)})
    seat = solid(kit, "armchair", "#8a6fd0", 0.35, shade="#6a4fb0")
    chair = kit.empty(f"{p} armchair", root, (-1.2, 1.4, 0), (0, 0, 160))
    tbox(kit, f"{p} chair seat", (0, 0, 0.25), (0.9, 0.8, 0.5), seat, chair)
    tbox(kit, f"{p} chair back", (0, 0.35, 0.75), (0.9, 0.2, 0.6), seat, chair)
    for sx in (1, -1):
        tbox(kit, f"{p} chair arm {sx}", (sx * 0.42, 0, 0.6), (0.16, 0.8, 0.25), seat, chair)
    tv = kit.empty(f"{p} tv", root, (0.9, 1.3, 0), (0, 0, -20))
    tbox(kit, f"{p} tv body", (0, 0, 0.3), (0.7, 0.55, 0.6), solid(kit, "tv", "#4a3a6e", 0.3), tv)
    tbox(kit, f"{p} tv screen", (0, -0.28, 0.32), (0.55, 0.02, 0.42), solid(kit, "tv screen", "#6f8cff", 0.8), tv)
    tube(kit, f"{p} lamp pole", [(-1.9, 0.6, 0.0), (-1.9, 0.6, 1.5)], 0.03, solid(kit, "lamp pole", STEEL), root, sides=4)
    tube(kit, f"{p} lamp shade", [(-1.9, 0.6, 1.4), (-1.9, 0.6, 1.75)], [0.28, 0.16], solid(kit, "lamp shade", YEL, 0.6), root,
         sides=8)


def yard_sign(kit, root, p, text, fg):
    tube(kit, f"{p} stake", [(0, 0, 0), (0, 0, 1.0)], 0.03, solid(kit, "sign stake", WHITE, 0.35), root, sides=4)
    plate(kit, f"{p} board", root, (0, 0, 1.1), (1.0, 0.04, 0.5), tm(kit, f"yard sign {text}", lambda: sign_tex(text, 32, 16, WHITE, fg, 2, border=fg)))


def moving_day(kit, root, p):
    """The tutorial yard, front (-Y) on the road where the truck is parked. Left: the ex's house behind a picket fence,
    with dad's stuff dumped on her lawn. Right: dad's trailer on a dirt lot with a mud puddle, a strawberry patch and a
    nut tree. The fronts stay open so the kid can walk straight from her porch to the serving window."""
    R = kit.rand
    ground(kit, root, p)
    props = kit.empty(f"{p} props", root)
    walkm = road.ground_mats(kit)[1]
    concrete = tm(kit, "driveway", lambda: stops.tex_concrete(R), 0.25, 'REPEAT')
    dirt = tm(kit, "lot dirt", lambda: tex_dirt_lot(R), 0.2, 'REPEAT')
    # hers
    baked(kit, root, f"{p} house", (-10.0, 5.0, SIDE), -90, lambda piv: house_c(kit, piv, f"{p} house", 1))
    pad(kit, props, f"{p} path", -10.6, -B2, -9.4, 0.8, walkm)
    pad(kit, props, f"{p} drive", -16.8, -B2, -14.2, 1.0, concrete)
    at(kit, props, lambda k, r, n: car(k, r, n, "#8f5bff"), f"{p} her car", -15.5, -8.0, 0, z=SIDE + 0.012)
    at(kit, props, flower_bed, f"{p} bed 0", -12.8, 0.4, 0)
    at(kit, props, flower_bed, f"{p} bed 1", -7.2, 0.4, 0)
    at(kit, props, road.mailbox, f"{p} her mailbox", -8.7, -18.9, 0)
    at(kit, props, lambda k, r, n: yard_sign(k, r, n, "HERS", PINK), f"{p} her sign", -12.5, -14.5, 0)
    at(kit, props, moving_pile, f"{p} dads stuff", -4.0, -5.5, 0)
    fence_line(kit, props, road.picket_fence, f"{p} her side fence", (-19.4, -19.4), (-19.4, 19.4), 2.0, picket_post(kit))
    fence_line(kit, props, road.picket_fence, f"{p} her back fence", (-19.4, 19.4), (-0.2, 19.4), 2.0, picket_post(kit))
    fence_line(kit, props, road.picket_fence, f"{p} divider", (-0.2, -11.0), (-0.2, 19.4), 2.0, picket_post(kit))
    at(kit, props, road.round_tree, f"{p} her tree", -16.0, 15.0, 30, 0.95)
    at(kit, props, road.bush, f"{p} her bush", -3.0, 12.0, 0, 0.8)
    # his
    pad(kit, props, f"{p} dirt", 0.3, -19.5, 19.5, 19.5, dirt, 4.0)
    baked(kit, root, f"{p} trailer", (11.0, 10.5, SIDE), 0, lambda piv: trailer(kit, piv, f"{p} trailer", "#c8d8ff", ORNG))
    at(kit, props, lawn_chair, f"{p} chair", 5.5, 6.0, 200)
    at(kit, props, road.trash_can, f"{p} trash", 3.0, 12.5, 20)
    at(kit, props, tire_pile, f"{p} tires", 17.0, 16.0, 40)
    at(kit, props, road.mailbox, f"{p} his mailbox", 8.7, -18.9, 0)
    at(kit, props, lambda k, r, n: yard_sign(k, r, n, "HIS", BLUE), f"{p} his sign", 7.0, 6.5, 0)
    post = chain_post(kit)
    fence_line(kit, props, road.chainlink_fence, f"{p} his side fence", (19.6, -19.6), (19.6, 19.6), 2.5, post)
    fence_line(kit, props, road.chainlink_fence, f"{p} his back fence", (0.2, 19.6), (19.6, 19.6), 2.5, post)
    bake_props(kit, root, props, p)
    socket(kit, root, "kid", (-10.0, -2.0, SIDE), 0)
    socket(kit, root, "dad", (10.0, 4.5, SIDE), 0)
    socket(kit, root, "mud 0", (4.0, -11.0, SIDE))
    socket(kit, root, "patch 0", (15.5, -7.0, SIDE), 0)
    socket(kit, root, "nut tree", (12.0, -15.5, SIDE))
    socket(kit, root, "tutorial park", (2.0, -28.0, SIDE), 90)


# ---------------------------------------------------------------- batch
ASSET_FNS = [
    ("Crossroads", crossroads),
    ("Creek Fill", creek_fill),
    ("Trailer Lot A", lambda k, r, n: trailer_lot(k, r, n, 0)),
    ("Trailer Lot B", lambda k, r, n: trailer_lot(k, r, n, 1)),
    ("Big Dairy Lot", big_dairy_lot),
    ("Suburb Block A", lambda k, r, n: suburb_block(k, r, n, 0)),
    ("Suburb Block B", lambda k, r, n: suburb_block(k, r, n, 1)),
    ("Suburb Block C", lambda k, r, n: suburb_block(k, r, n, 2)),
    ("Park Block", park_block),
    ("School Block", school_block),
    ("Coffee Strip", coffee_strip),
    ("Mansion Block A", lambda k, r, n: mansion_block(k, r, n, 0)),
    ("Mansion Block B", lambda k, r, n: mansion_block(k, r, n, 1)),
    ("Vault Mansion", vault_mansion),
    ("Moving Day", moving_day),
]
ASSETS = [(n, (lambda f, n: lambda kit, root: f(kit, root, n))(f, n)) for n, f in ASSET_FNS]


# ---------------------------------------------------------------- review scenes
def one(name):
    def build(kit, root):
        dict(ASSETS)[name](kit, kit.empty(f"{name} root", root))
    return build


def town_layout(kit, root):
    """Suburb Block A with its surrounding road ring: Crossroads at the corners, Town Straight between them."""
    lookup = dict(ASSETS)
    lookup["Suburb Block A"](kit, kit.empty("Suburb Block A root", root))
    lookup["Coffee Strip"](kit, kit.empty("Coffee Strip root", root, (60, 0, 0)))
    for x in (-30, 30, 90):
        for y in (-30, 30):
            lookup["Crossroads"](kit, kit.empty(f"Crossroads root {x} {y}", root, (x, y, 0)))
    for x in (-10, 10, 50, 70):
        for y in (-30, 30):
            road.town_straight(kit, kit.empty(f"Town Straight root {x} {y}", root, (x, y, 0), (0, 0, 90)), f"Town Straight {x} {y}")
    for x in (-30, 30, 90):
        for y in (-10, 10):
            road.town_straight(kit, kit.empty(f"Town Straight root {x} {y}", root, (x, y, 0)), f"Town Straight {x} {y}")


CLOSE = ((-16, -40, 14), (0, -2, 1.0), 30)
SCENES = [dict(name="town layout", build=town_layout, cam=((-38, -62, 34), (20, -2, 0), 30), res=(1800, 1000)),
          dict(name="street view", build=town_layout, cam=((-29.0, -24.0, 1.7), (10, -2, 1.5), 22), res=(1600, 900))]
for nm in ("Big Dairy Lot", "Trailer Lot A", "Suburb Block B", "Park Block", "School Block", "Coffee Strip", "Mansion Block A",
           "Vault Mansion", "Moving Day", "Creek Fill", "Crossroads"):
    cam = CLOSE if nm not in ("Creek Fill", "Crossroads") else ((-8, -20, 8), (0, 0, 0.5), 30)
    SCENES.append(dict(name=f"close {nm}", build=one(nm), cam=cam, res=(1600, 900)))
