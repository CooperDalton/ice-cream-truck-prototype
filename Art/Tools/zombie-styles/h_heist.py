"""Batch 'heist' (style H): the stolen Hope Diamond, the rocky road tub it hides in, Kevin's Bait Shack at the town line,
the Leaving Maplewood sign and a police roadblock. Standing assets: root on the floor at the footprint center, front -Y
(the diamond's root is its bottom point). Sockets are empties named '<Asset> socket <purpose>'."""
import random
from style_H import *
import h_items
from h_items import FL
from h_shop import txt3, FONT3, build_kevin, prefixed as shop_prefixed
from h_road import traffic_cone, tex_road, tex_grass

# 5x7 pixel font (variable width) for the big sign lettering
FONT5 = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."),
    'D': ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'G': (".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"),
    'I': ("###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    '&': (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "'": ("#", "#", ".", ".", ".", ".", "."),
    ' ': ("..", "..", "..", "..", "..", "..", ".."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
}


FONT35 = dict(FONT3)
FONT35.update({'&': (".#..", "#.#.", ".#..", "#.##", ".#.#"), ' ': (".", ".", ".", ".", ".")})


def txt5(c, s, x, y, col, kx=1, ky=None, shadow=None, center=False, font=FONT5):
    """Variable-width pixel font (5x7 by default, FONT35 = 3x5). (x, y) = top-left texel (top-center with center=True),
    y counts up; kx/ky = pixel scale."""
    ky = ky or kx
    if center:
        x -= (sum(len(font[ch][0]) + 1 for ch in s) - 1) * kx // 2
    if shadow:
        txt5(c, s, x + kx, y - ky, shadow, kx, ky, font=font)
    for ch in s:
        rows = font[ch]
        for r, row in enumerate(rows):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * kx, y - (r + 1) * ky + 1, x + q * kx + kx - 1, y - r * ky, col)
        x += (len(rows[0]) + 1) * kx


FISH = (".....fffff........",
        "...##########...##",
        ".###e#########.###",
        "##############.##.",
        ".#bbbbbbbbbbbb###.",
        "...bbbbbbbbbb..###",
        ".....bbbbb......##")


def fish_px(c, x0, y0, body, belly, fin, flip=False):
    """18x7 pixel fish, (x0, y0) = top-left texel, y counts up. flip faces it right."""
    cols = {'#': body, 'b': belly, 'f': fin, 'e': INK}
    for r, row in enumerate(FISH):
        for q, ch in enumerate(row):
            if ch in cols:
                c.set(x0 + (17 - q if flip else q), y0 - r, cols[ch])


def socket(kit, A, purpose, parent, loc, rot=(0, 0, 0)):
    s = kit.empty(f"{A} socket {purpose}", parent, loc, rot)
    s.empty_display_type = 'ARROWS'
    s.empty_display_size = 0.2
    return s


def named(A, fn):
    """Build, then prefix every descendant name with the asset name exactly once."""
    def build(kit, root):
        fn(kit, root, A)
        for ob in root.children_recursive:
            if not ob.name.startswith(A):
                ob.name = f"{A} {ob.name}"
    return build


def wall_box(kit, name, center, size, mat, parent, rot=(0, 0, 0), per=1.0):
    """Box with world-scale UVs (one texture repeat per `per` meters) on every face."""
    sx, sy, sz = (v / per for v in size)
    return tbox(kit, name, center, size, mat, parent, rot=rot,
                uv={'ny': (0, 0, sx, sz), 'py': (0, 0, sx, sz), 'px': (0, 0, sy, sz), 'nx': (0, 0, sy, sz),
                    'pz': (0, 0, sx, sy), 'nz': (0, 0, sx, sy)})


def prism_x(kit, name, poly, x0, x1, mat, parent, per=1.0):
    """Polygon in the YZ plane extruded from x0 to x1, planar UVs (u = y, v = z, one repeat per `per` meters)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    a = [bm.verts.new((x0, y, z)) for y, z in poly]
    b = [bm.verts.new((x1, y, z)) for y, z in poly]
    for ring in (a, b):
        f = bm.faces.new(ring)
        for lp in f.loops:
            lp[uvl].uv = (lp.vert.co.y / per, lp.vert.co.z / per)
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        f = bm.faces.new((a[i], a[j], b[j], b[i]))
        for lp in f.loops:
            lp[uvl].uv = ((lp.vert.co.y + lp.vert.co.z) / per, lp.vert.co.x / per)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


# ================================================================ 1. Hope Diamond
D_R, D_GIRDLE, D_BAND, D_CROWN = 0.12, 0.1, 0.008, 0.052
ICE, ICE_W, ICE_L, ICE_D = "#6ccaff", "#eef9ff", "#a98cff", "#3f8fe8"


def build_diamond(kit, parent, A, sparkles=True):
    """Brilliant cut: octagonal table, star and upper girdle facets, 16-sided girdle, pavilion to a point at the root."""
    R, zg, zt = D_R, D_GIRDLE, D_GIRDLE + D_BAND + D_CROWN
    pts = [(0, 0, 0)]
    for k in range(16):
        a = math.radians(k * 22.5)
        pts += [(math.cos(a) * R, math.sin(a) * R, zg), (math.cos(a) * R, math.sin(a) * R, zg + D_BAND)]
    for k in range(8):
        a = math.radians(k * 45 + 22.5)
        pts.append((math.cos(a) * R * 0.66, math.sin(a) * R * 0.66, zg * 0.52))           # pavilion break
        pts.append((math.cos(a) * R * 0.58, math.sin(a) * R * 0.58, zt))                   # table corners
        b = math.radians(k * 45)
        pts.append((math.cos(b) * R * 0.86, math.sin(b) * R * 0.86, zg + D_BAND + D_CROWN * 0.55))  # star points
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in pts]
    res = bmesh.ops.convex_hull(bm, input=vs)
    bmesh.ops.delete(bm, geom=[g for g in res["geom_interior"] + res["geom_unused"] if isinstance(g, bmesh.types.BMVert)],
                     context='VERTS')
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(1.0), verts=bm.verts, edges=bm.edges)
    mats = [solid(kit, "diamond ice", ICE, 0.75, shade="#a8e2ff"), solid(kit, "diamond white", ICE_W, 0.85, shade="#c8ecff"),
            solid(kit, "diamond lavender", ICE_L, 0.75, shade="#c8b8ff"), solid(kit, "diamond deep", ICE_D, 0.7, shade="#6cb0f4")]
    for f in bm.faces:
        n = f.normal
        sector = int(round(math.degrees(math.atan2(n.y, n.x)) / 22.5)) % 16
        if n.z > 0.97:
            f.material_index = 1                                  # table
        elif n.z > 0.2:
            f.material_index = (0, 2, 0, 1)[sector % 4]           # crown
        elif n.z > -0.2:
            f.material_index = (1, 0)[sector % 2]                 # girdle
        else:
            f.material_index = (3, 2, 0, 2)[sector % 4]           # pavilion
    gem_ob = kit.mesh_from_bmesh(f"{A} gem", bm, mats, parent, smooth=False)
    if sparkles:
        for i, (p, s) in enumerate((((-0.15, -0.06, 0.2), 0.05), ((0.16, 0.02, 0.15), 0.038), ((0.06, -0.1, 0.26), 0.03),
                                    ((0.13, -0.11, 0.05), 0.028))):
            for j, rz in enumerate((0, 90)):
                fx_star(kit, parent, f"{A} sparkle {i} {j}", p, 4, s, s * 0.2, WHITE, 3.0, (0, 0, rz + 20 * i))
    return gem_ob


# ================================================================ 2. Flavor Tub Rocky Road Diamond
TUB_SEED = 100 + [n for n, _ in h_items.ASSETS].index("Flavor Tub Rocky Road")


def build_diamond_tub(kit, root, A):
    keep = kit.rand
    kit.rand = random.Random(TUB_SEED)    # same seed as "Flavor Tub Rocky Road", so the tub matches it texel for texel
    h_items.build_tub(kit, root, A, "rockyroad", 8)
    kit.rand = keep
    hinge = next(o for o in root.children if o.name == f"{A} lid hinge")   # lid off
    for ob in list(hinge.children_recursive) + [hinge]:
        bpy.data.objects.remove(ob)
    piv = kit.empty(f"{A} diamond", root, (0.0, 0.08, 0.235), (60, 0, 12))
    gem_ob = build_diamond(kit, piv, A, sparkles=False)
    # the swirl and rocky road bits that would poke through the buried gem go (they sit inside it anyway)
    bpy.context.view_layer.update()
    mw = gem_ob.matrix_world
    planes = [(mw @ f.center, (mw.to_3x3() @ f.normal).normalized()) for f in gem_ob.data.polygons]
    for ob in list(root.children):
        if ob.type == 'MESH' and (" bit" in ob.name or " swirl" in ob.name) and any(
                all((ob.matrix_world @ v.co - c).dot(n) < 0 for c, n in planes) for v in ob.data.vertices):
            bpy.data.objects.remove(ob)
    for i, (p, s) in enumerate((((-0.17, -0.1, 0.42), 0.045), ((0.13, -0.08, 0.38), 0.034), ((0.02, 0.12, 0.47), 0.03),
                                ((-0.2, 0.06, 0.3), 0.026))):
        for j, rz in enumerate((0, 90)):
            fx_star(kit, root, f"{A} sparkle {i} {j}", p, 4, s, s * 0.2, WHITE, 3.0, (0, 0, rz + 25 * i))
    socket(kit, A, "diamond", piv, (0, 0, D_GIRDLE))


# ================================================================ 3. Bait Shack
SH_X, SH_YF, SH_YB = 2.15, -1.3, 1.4          # wall faces
ROOF_YF, ROOF_YB, ROOF_ZF, ROOF_ZB = -1.45, 1.6, 2.66, 2.36
FLOOR_Z, COUNTER_Z = 0.1, 1.0
WOOD_G, WOOD_GD = "#a39488", "#7a6c66"


def roof_z(y):
    return ROOF_ZF + (ROOF_ZB - ROOF_ZF) * (y - ROOF_YF) / (ROOF_YB - ROOF_YF)


def tex_peel_planks(rand, paint, shade, hi):
    """64x64 = 2 m: horizontal clapboards (8 px), paint peeling to grey wood in a few patches."""
    c = Canvas(64, 64, paint)
    for b in range(8):
        y0 = b * 8
        c.rect(0, y0, 63, y0, shade)
        c.rect(0, y0 + 7, 63, y0 + 7, hi)
        if b % 3 != 1:
            x, w, h = rand.randrange(64), rand.randint(5, 14), rand.randint(3, 5)
            yy = y0 + 1
            for k in range(w):
                top = yy + h - 1 - (1 if k in (0, w - 1) else 0)
                c.rect(x + k, yy, x + k, top, WOOD_G)
            c.rect(x + 1, yy, x + w - 2, yy, WOOD_GD)
    c.speckle(rand, [shade], 60)
    return c


def tex_grey_planks(rand):
    c = Canvas(32, 32, WOOD_G)
    for x in range(0, 32, 6):
        c.rect(x, 0, x, 31, WOOD_GD)
    c.speckle(rand, ["#8f8178", "#b5a89c"], 90)
    return c


def tex_tin(rand):
    """16x16 = 0.5 m: corrugated ridges along v, rust blooms."""
    c = Canvas(16, 16, "#c9c4dc")
    for x in range(16):
        c.rect(x, 0, x, 15, ("#e8e4f6", "#c9c4dc", "#a6a0c0", "#b7b2d0")[x % 4])
    for _ in range(3):
        x, y = rand.randrange(16), rand.randrange(16)
        for _ in range(7):
            c.set(x, y, rand.choice(("#d0783a", "#b05a2a", "#e89a5a")))
            x += rand.choice((-1, 0, 1)); y += rand.choice((-1, 0, 1))
    return c


def tex_shack_sign(rand):
    """128x40 over 4.2 x 1.28 m."""
    c = Canvas(128, 40, "#fff1c7")
    c.speckle(rand, ["#f0dca8", "#fff8e0"], 160)
    for _ in range(10):   # weathered gaps in the paint
        x, y = rand.randrange(4, 124), rand.randrange(3, 37)
        c.rect(x, y, x + rand.randint(1, 3), y, "#d8c08a")
    c.rect(0, 0, 127, 1, MINT); c.rect(0, 38, 127, 39, MINT); c.rect(0, 0, 1, 39, MINT); c.rect(126, 0, 127, 39, MINT)
    txt5(c, "KEVIN'S", 64, 36, PINK, 2, 3, shadow=INK, center=True)
    txt5(c, "BAIT & DOCUMENTS", 64, 13, "#2e5ad0", 2, center=True, font=FONT35)
    fish_px(c, 5, 29, "#5f9ee8", WHITE, "#2e5ad0")
    fish_px(c, 105, 29, "#5f9ee8", WHITE, "#2e5ad0", flip=True)
    return c


def tex_pegboard():
    c = Canvas(16, 16, "#c89a62")
    for y in range(1, 16, 4):
        for x in range(1, 16, 4):
            c.set(x, y, "#6a4422")
    return c


PLATE_COLS = [("#ffe14a", "#2e5ad0", "#2e5ad0"), (WHITE, RED, "#2e5ad0"), ("#2e86ff", WHITE, WHITE), (ORNG, INK, INK),
              (MINT, "#1f6a8a", "#1f6a8a"), ("#ffb3d9", "#a02a6a", "#a02a6a"), (WHITE, "#2e9e5a", "#2e9e5a"),
              ("#b48cff", WHITE, YEL)]


def tex_plate(rand, base, ink, band):
    c = Canvas(32, 16, base)
    c.rect(0, 0, 31, 0, ink); c.rect(0, 15, 31, 15, ink); c.rect(0, 0, 0, 15, ink); c.rect(31, 0, 31, 15, ink)
    c.rect(2, 12, 29, 13, band)
    s = "".join(rand.choice("ABCDEFGHKLMNPRSTUVWXYZ") for _ in range(3)) + " " + \
        "".join(rand.choice("0123456789") for _ in range(3))
    txt3(c, s, 3, 9, ink)
    c.dots([(4, 3), (27, 3)], "#8f86a8")
    return c


def tex_notary():
    c = Canvas(48, 16, "#24306e")
    c.rect(0, 0, 47, 0, YEL); c.rect(0, 15, 47, 15, YEL); c.rect(0, 0, 0, 15, YEL); c.rect(47, 0, 47, 15, YEL)
    disc(c, 7, 8, 4, YEL); disc(c, 7, 8, 2, "#d9901a"); c.set(7, 8, YEL)
    c.dots([(5, 3), (9, 3), (4, 2), (10, 2)], RED)
    txt5(c, "NOTARY", 14, 11, WHITE)
    return c


def tex_passport(col):
    """16x16: cover (u 0-0.7) with a gold crest, white page edges (u 0.75-1)."""
    c = Canvas(16, 16, col)
    c.rect(12, 0, 15, 15, "#f4ebe2")
    for y in range(0, 16, 2):
        c.rect(12, y, 15, y, "#d8cfc6")
    disc(c, 6, 9, 2, "#ffd23a"); c.set(6, 9, col)
    c.rect(3, 4, 9, 4, "#ffd23a")
    return c


def tex_form(rand):
    c = Canvas(16, 24, "#fbf7f0")
    c.rect(0, 20, 15, 23, "#2e5ad0")
    for y in range(3, 18, 2):
        c.rect(2, y, 2 + rand.randint(6, 12), y, "#b8b0c8")
    disc(c, 11, 5, 2, RED); c.set(11, 5, "#fbf7f0")
    return c


def tex_newspaper(rand):
    c = Canvas(32, 24, "#e8e4dc")
    c.rect(2, 19, 29, 21, INK)
    c.rect(2, 9, 13, 16, "#8f8a9a")
    for col0 in (16, 2):
        for y in range(2 if col0 == 2 else 9, 17 if col0 == 16 else 8, 2):
            c.rect(col0, y, col0 + 12 - rand.randint(0, 3), y, "#9a96a8")
    c.rect(16, 2, 28, 2, "#9a96a8"); c.rect(16, 4, 26, 4, "#9a96a8")
    return c


def tex_cooler_front():
    c = Canvas(32, 24, WHITE)
    c.rect(0, 0, 31, 2, "#2e86ff"); c.rect(0, 3, 31, 3, "#1f5fd0")
    c.rect(0, 23, 31, 23, "#d8d2e8")
    txt5(c, "LIVE", 16, 21, "#2e5ad0", center=True)
    txt5(c, "BAIT", 16, 12, RED, center=True)
    return c


def tex_worm_crate():
    c = Canvas(40, 32, "#e8a85a")
    for y in (0, 10, 21, 31):
        c.rect(0, y, 39, y, "#a8642a")
    c.rect(0, 0, 1, 31, "#a8642a"); c.rect(38, 0, 39, 31, "#a8642a")
    c.rect(3, 11, 36, 20, "#f2c88a")
    txt5(c, "WORMS", 20, 19, "#7a3a1c", center=True)
    return c


def build_shack(kit, root, A):
    R = kit.rand
    mint = tex_mat("shack mint planks", tex_peel_planks(R, "#8ff0cf", "#5fd0aa", "#c4fbe6"), ext='REPEAT')
    pink = tex_mat("shack pink planks", tex_peel_planks(R, "#ffaed2", "#e888b4", "#ffd6ea"), ext='REPEAT')
    grey = tex_mat("shack grey planks", tex_grey_planks(R), 0.28, ext='REPEAT')
    tin = tex_mat("shack tin roof", tex_tin(R), 0.3, ext='REPEAT')
    post = solid(kit, "shack post", WOOD_G, shade=WOOD_GD)
    trim_pink, ink = solid(kit, "shack trim pink", "#ff7dbb", shade="#d63a86"), solid(kit, "shack dark", INK, 0.1)
    x0, x1, yf, yb = -SH_X, SH_X, SH_YF, SH_YB
    t = 0.08
    # floor deck, walls, front counter
    wall_box(kit, f"{A} floor", (0, (yf + yb) / 2, FLOOR_Z / 2), (2 * SH_X, yb - yf, FLOOR_Z), grey, root)
    wall_box(kit, f"{A} back wall", (0, yb - t / 2, roof_z(yb) / 2), (2 * SH_X, t, roof_z(yb) - 0.02), mint, root, per=2)
    for sx, nm in ((-1, "left"), (1, "right")):
        xa = sx * SH_X
        prism_x(kit, f"{A} {nm} wall", [(yf, 0), (yb, 0), (yb, roof_z(yb) - 0.02), (yf, roof_z(yf) - 0.02)],
                min(xa, xa - sx * t), max(xa, xa - sx * t), mint, root, per=2)
    wall_box(kit, f"{A} front wall", (0, yf + t / 2, (COUNTER_Z - 0.06) / 2), (2 * SH_X, t, COUNTER_Z - 0.06), pink, root, per=2)
    wall_box(kit, f"{A} counter", (0, yf - 0.02, COUNTER_Z - 0.03), (2 * SH_X + 0.1, 0.62, 0.06), grey, root)
    tbox(kit, f"{A} counter edge", (0, yf - 0.33, COUNTER_Z - 0.03), (2 * SH_X + 0.1, 0.03, 0.08), trim_pink, root)
    for sx in (-1, 1):
        tbox(kit, f"{A} counter bracket {sx}", (sx * 1.4, yf - 0.16, COUNTER_Z - 0.2), (0.05, 0.3, 0.05), post, root,
             rot=(-40, 0, 0))
    # front posts, header beam under the roof, side window
    for sx in (-1, 1):
        tbox(kit, f"{A} corner post {sx}", (sx * (SH_X - 0.05), yf - 0.03, roof_z(yf) / 2), (0.12, 0.12, roof_z(yf)), post, root)
        tbox(kit, f"{A} back post {sx}", (sx * (SH_X - 0.05), yb - 0.03, roof_z(yb) / 2), (0.12, 0.12, roof_z(yb)), post, root)
    wall_box(kit, f"{A} header", (0, yf + 0.04, (2.15 + roof_z(yf)) / 2), (2 * SH_X, 0.1, roof_z(yf) - 2.15), pink, root, per=2)
    tbox(kit, f"{A} header trim", (0, yf - 0.02, 2.17), (2 * SH_X + 0.06, 0.06, 0.06), trim_pink, root)
    tbox(kit, f"{A} window", (-SH_X - 0.01, 0.35, 1.55), (0.04, 0.8, 0.6), solid(kit, "shack glass", GLASS, 0.2), root)
    for dz, h in ((-0.33, 0.06), (0.33, 0.06)):
        tbox(kit, f"{A} window frame {dz}", (-SH_X - 0.03, 0.35, 1.55 + dz), (0.04, 0.92, h), trim_pink, root)
    for dy in (-0.43, 0.0, 0.43):
        tbox(kit, f"{A} window mullion {dy}", (-SH_X - 0.03, 0.35 + dy, 1.55), (0.04, 0.06, 0.6), trim_pink, root)
    # slanted tin roof (high at the front) and its fascia
    L = math.hypot(ROOF_YB - ROOF_YF, ROOF_ZF - ROOF_ZB)
    tilt = -math.degrees(math.atan2(ROOF_ZF - ROOF_ZB, ROOF_YB - ROOF_YF))
    tbox(kit, f"{A} roof", (0, (ROOF_YF + ROOF_YB) / 2, (ROOF_ZF + ROOF_ZB) / 2 + 0.02), (2 * SH_X + 0.35, L, 0.04), tin, root,
         rot=(tilt, 0, 0), uv={'all': (0, 0, (2 * SH_X + 0.35) * 2, L * 2)})
    for i, x in enumerate((-1.6, -0.55, 0.55, 1.6)):   # roof ribs
        tbox(kit, f"{A} roof rib {i}", (x, (ROOF_YF + ROOF_YB) / 2, (ROOF_ZF + ROOF_ZB) / 2 + 0.05), (0.05, L, 0.03),
             solid(kit, "tin rib", "#a6a0c0"), root, rot=(tilt, 0, 0))
    # the big sign over the front on two posts
    sz0, sz1, sy = 2.12, 3.4, ROOF_YF - 0.08
    for sx in (-1, 1):
        tbox(kit, f"{A} sign post {sx}", (sx * 1.5, sy + 0.07, (2.2 + sz1 - 0.08) / 2), (0.1, 0.06, sz1 - 0.08 - 2.2), post, root)
    tbox(kit, f"{A} sign", (0, sy, (sz0 + sz1) / 2), (4.2, 0.06, sz1 - sz0), tex_mat("bait sign", tex_shack_sign(R), 0.75), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.4, 0.95, 0.42, 0.97)})
    tbox(kit, f"{A} sign cap", (0, sy, sz1 - 0.01), (4.3, 0.1, 0.04), trim_pink, root)

    # interior: pegboard of license plates, NOTARY sign, fishing rods
    yw = yb - t
    wall_box(kit, f"{A} pegboard", (-0.45, yw - 0.015, 1.65), (2.3, 0.03, 1.0), tex_mat("pegboard", tex_pegboard(), ext='REPEAT'),
             root)
    for i in range(8):
        col, row = i % 4, i // 4
        base, ink_c, band = PLATE_COLS[i]
        tbox(kit, f"{A} plate {i}", (-1.3 + col * 0.56, yw - 0.04, 1.92 - row * 0.42), (0.42, 0.015, 0.21),
             tex_mat(f"plate {i}", tex_plate(R, base, ink_c, band)), root, rot=(0, R.uniform(-6, 6), 0),
             uv={'ny': (0, 0, 1, 1), 'all': (0.4, 0.4, 0.42, 0.42)})
        tbox(kit, f"{A} plate hook {i}", (-1.3 + col * 0.56, yw - 0.04, 2.04 - row * 0.42), (0.03, 0.06, 0.03), ink, root)
    tbox(kit, f"{A} notary sign", (1.35, yw - 0.02, 2.0), (0.96, 0.03, 0.32), tex_mat("notary sign", tex_notary(), 0.6), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.02, 0.02)})
    rod, cork, reel = solid(kit, "rod", "#2a2238", 0.15), solid(kit, "rod cork", "#e8b878"), solid(kit, "rod reel", STEEL)
    for i, (x, lean) in enumerate(((1.0, 6), (1.3, -4), (1.65, 9))):
        rp = kit.empty(f"{A} rod {i}", root, (x, yw - 0.12, FLOOR_Z), (-6, lean, 0))
        tube(kit, f"{A} rod {i} handle", [(0, 0, 0), (0, 0, 0.4)], [0.022, 0.018], cork, rp, sides=5)
        tube(kit, f"{A} rod {i} blank", [(0, 0, 0.4), (0, 0, 1.75)], [0.012, 0.005], rod, rp, sides=4)
        tube(kit, f"{A} rod {i} reel", [(-0.04, -0.04, 0.32), (0.04, -0.04, 0.32)], 0.04, reel, rp, sides=6)
    socket(kit, A, "shopkeeper", root, (0, -0.65, FLOOR_Z))

    # counter clutter: passports, stamp and ink pad, forms, a fish on newspaper
    cz = COUNTER_Z
    for s, (x, y, n, rz) in enumerate(((-1.55, -1.35, 7, 8), (-1.3, -1.25, 5, -12), (-1.45, -1.05, 4, 22))):
        for k in range(n):
            col = ("#24306e", "#7a1830", "#24306e", "#1f5a3a")[(k + s) % 4]
            tbox(kit, f"{A} passport {s} {k}", (x + R.uniform(-0.01, 0.01), y + R.uniform(-0.01, 0.01), cz + 0.006 + k * 0.012),
                 (0.13, 0.18, 0.011), tex_mat(f"passport {col}", tex_passport(col)), root, rot=(0, 0, rz + R.uniform(-7, 7)),
                 uv={'pz': (0, 0, 0.7, 1), 'nz': (0, 0, 0.7, 1), 'all': (0.78, 0.1, 1.0, 0.9)})
    ip = kit.empty(f"{A} ink pad", root, (-0.55, -1.2, cz), (0, 0, -8))
    tbox(kit, f"{A} ink pad tin", (0, 0, 0.012), (0.18, 0.12, 0.024), solid(kit, "ink tin", "#2e5ad0"), ip)
    tbox(kit, f"{A} ink pad felt", (0, 0, 0.025), (0.15, 0.09, 0.004), solid(kit, "ink felt", DRED, 0.3), ip)
    st = kit.empty(f"{A} stamp", root, (-0.3, -1.3, cz), (0, 0, 14))
    tbox(kit, f"{A} stamp base", (0, 0, 0.025), (0.1, 0.06, 0.03), solid(kit, "stamp wood", "#c47a3a"), st)
    tbox(kit, f"{A} stamp rubber", (0, 0, 0.006), (0.1, 0.06, 0.012), solid(kit, "stamp rubber", RED), st)
    tube(kit, f"{A} stamp handle", [(0, 0, 0.04), (0, 0, 0.1)], [0.016, 0.012], solid(kit, "stamp wood", "#c47a3a"), st, sides=6)
    lowball(kit, f"{A} stamp knob", (0, 0, 0.12), (0.03, 0.03, 0.026), solid(kit, "stamp knob", INK, 0.2), st)
    form = tex_mat("form", tex_form(R))
    for k in range(6):
        tbox(kit, f"{A} form {k}", (0.25 + R.uniform(-0.03, 0.03), -1.2 + R.uniform(-0.03, 0.03), cz + 0.003 + k * 0.004),
             (0.21, 0.28, 0.003), form, root, rot=(0, 0, R.uniform(-18, 18)), uv={'pz': (0, 0, 1, 1), 'all': (0, 0, 0.1, 0.1)})
    news = kit.empty(f"{A} newspaper", root, (1.3, -1.22, cz + 0.002), (0, 0, 6))
    tbox(kit, f"{A} newspaper sheet", (0, 0, 0.002), (0.62, 0.44, 0.004), tex_mat("newspaper", tex_newspaper(R)), news,
         uv={'pz': (0, 0, 1, 1), 'all': (0, 0, 0.05, 0.05)})
    fish_m, fin_m = solid(kit, "fish", "#8fb4ec", shade="#c8dcff"), solid(kit, "fish fin", "#4f78c8")
    fp = kit.empty(f"{A} fish", root, (1.3, -1.22, cz + 0.03), (0, 0, -12))
    tube(kit, f"{A} fish body", [(-0.22, 0, 0), (-0.17, 0, 0.002), (-0.05, 0, 0.005), (0.08, 0, 0.003), (0.16, 0, 0)],
         [(0.012, 0.004), (0.05, 0.022), (0.065, 0.028), (0.042, 0.02), (0.016, 0.008)], fish_m, fp, sides=6, front=(0, 0, 1))
    bm = bmesh.new()
    for tri in (((0.15, 0, 0), (0.25, 0.08, 0.004), (0.22, 0, 0.002)), ((0.15, 0, 0), (0.22, 0, 0.002), (0.25, -0.08, 0.004))):
        bm.faces.new([bm.verts.new(p) for p in tri])
    kit.mesh_from_bmesh(f"{A} fish tail", bm, fin_m, fp, smooth=False)
    tbox(kit, f"{A} fish fin", (-0.03, 0.06, 0.004), (0.1, 0.03, 0.006), fin_m, fp, rot=(0, 0, -10))
    tbox(kit, f"{A} fish eye", (-0.165, -0.012, 0.024), (0.016, 0.016, 0.006), solid(kit, "fish eye", INK, 0.1), fp)
    tbox(kit, f"{A} fish eye shine", (-0.168, -0.014, 0.0275), (0.006, 0.006, 0.002), solid(kit, "shine", WHITE, 1.2), fp)

    # LIVE BAIT cooler and WORMS crate beside the shack
    cool = kit.empty(f"{A} cooler", root, (SH_X + 0.55, -0.95, 0), (0, 0, -8))
    tbox(kit, f"{A} cooler body", (0, 0, 0.23), (0.62, 0.46, 0.46), tex_mat("bait cooler", tex_cooler_front()), cool,
         uv={'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1), 'all': (0.0, 0.7, 0.03, 0.75)})
    tbox(kit, f"{A} cooler lid", (0, 0, 0.49), (0.66, 0.5, 0.06), solid(kit, "cooler lid", "#2e86ff", shade="#1f5fd0"), cool)
    tbox(kit, f"{A} cooler handle", (0, 0, 0.535), (0.3, 0.05, 0.03), solid(kit, "cooler handle", WHITE), cool)
    crate = kit.empty(f"{A} worm crate", root, (SH_X + 0.5, -0.1, 0), (0, 0, 12))
    tbox(kit, f"{A} worm crate box", (0, 0, 0.17), (0.5, 0.4, 0.34), tex_mat("worm crate", tex_worm_crate()), crate,
         uv={'all': (0, 0, 1, 1), 'pz': (0.1, 0.05, 0.2, 0.08)})
    tbox(kit, f"{A} worm dirt", (0, 0, 0.33), (0.44, 0.34, 0.03), solid(kit, "dirt", "#5a3418", shade="#3e2210"), crate)
    worm = solid(kit, "worm", "#ff8fae", shade="#e0607e")
    for k in range(4):
        a = R.uniform(0, 6.28)
        x, y = R.uniform(-0.14, 0.12), R.uniform(-0.1, 0.1)
        tube(kit, f"{A} worm {k}", [(x, y, 0.345), (x + 0.04 * math.cos(a), y + 0.04 * math.sin(a), 0.37),
                                    (x + 0.09 * math.cos(a + 0.6), y + 0.09 * math.sin(a + 0.6), 0.35)], 0.01, worm, crate, sides=4)


# ================================================================ 4. Town Line Sign
HWY_GREEN = "#1e9e5a"


def tex_town_sign():
    c = Canvas(128, 64, HWY_GREEN)
    for y in range(64):
        for x in range(128):
            if (x * 3 + y * 5) % 23 == 0:
                c.set(x, y, "#1a8e50")
    c.rect(3, 3, 124, 4, WHITE); c.rect(3, 59, 124, 60, WHITE); c.rect(3, 3, 4, 60, WHITE); c.rect(123, 3, 124, 60, WHITE)
    c.dots([(3, 3), (124, 3), (3, 60), (124, 60)], HWY_GREEN)
    txt5(c, "LEAVING", 64, 54, WHITE, 2, center=True)
    txt5(c, "MAPLEWOOD", 64, 33, WHITE, 2, 3, center=True)
    return c


def tex_come_back():
    c = Canvas(84, 13, "#1f5fd0")
    c.rect(1, 1, 82, 1, WHITE); c.rect(1, 11, 82, 11, WHITE); c.rect(1, 1, 1, 11, WHITE); c.rect(82, 1, 82, 11, WHITE)
    txt5(c, "COME BACK SOON", 42, 9, WHITE, center=True)
    return c


def build_town_sign(kit, root, A):
    steel, back = solid(kit, "sign post", "#b9b4d4", shade="#9a94c0"), solid(kit, "sign back", "#a7a3b8", shade="#8f8aa6")
    top, h, w = 3.0, 1.3, 2.6
    for sx in (-1, 1):
        tbox(kit, f"{A} post {sx}", (sx * 0.85, 0.07, (top - 0.05) / 2), (0.1, 0.1, top - 0.05), steel, root)
        tbox(kit, f"{A} post foot {sx}", (sx * 0.85, 0.07, 0.04), (0.2, 0.2, 0.08), back, root)
    tbox(kit, f"{A} board", (0, 0, top - h / 2), (w, 0.03, h), tex_mat("town line sign", tex_town_sign(), 0.45), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.5, 0.45, 0.52, 0.47)})
    tbox(kit, f"{A} board back", (0, 0.02, top - h / 2), (w, 0.01, h), back, root)
    for z in (top - 0.3, top - h + 0.3):
        tbox(kit, f"{A} rail {z:.2f}", (0, 0.045, z), (w - 0.2, 0.04, 0.08), back, root)
    zb = 1.42
    tbox(kit, f"{A} small board", (0, -0.005, zb), (2.0, 0.03, 0.31), tex_mat("come back soon", tex_come_back(), 0.45), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.3, 0.5, 0.32, 0.52)})
    tbox(kit, f"{A} small board back", (0, 0.015, zb), (2.0, 0.01, 0.31), back, root)


# ================================================================ 5. Police Roadblock
def tex_stripes():
    c = Canvas(16, 8, WHITE)
    for y in range(8):
        for x in range(16):
            if ((x + y) // 4) % 2:
                c.set(x, y, RED)
    return c


def tex_police_board():
    """70x22 over a 2.0 x 0.63 m board: POLICE LINE / DO NOT CROSS filling the face."""
    c = Canvas(70, 22, YEL)
    c.rect(0, 0, 69, 0, INK); c.rect(0, 21, 69, 21, INK); c.rect(0, 0, 0, 21, INK); c.rect(69, 0, 69, 21, INK)
    txt5(c, "POLICE LINE", 35, 19, INK, center=True)
    txt5(c, "DO NOT CROSS", 35, 9, INK, center=True)
    return c


def sawhorse(kit, A, tag, parent, loc, rz, top_mat, top_uv, top_h, stripes, lamp=None, low_z=0.55):
    p = kit.empty(f"{A} {tag}", parent, loc, (0, 0, rz))
    leg = solid(kit, "barricade leg", WHITE, shade="#d4cff5")
    for sx in (1, -1):
        for sy in (1, -1):
            tbox(kit, f"{A} {tag} leg {sx} {sy}", (sx * 0.78, sy * 0.16, 0.54), (0.07, 0.05, 1.12), leg, p, rot=(sy * 16, 0, 0))
        tbox(kit, f"{A} {tag} foot {sx}", (sx * 0.78, 0, 0.03), (0.12, 0.7, 0.06), solid(kit, "barricade foot", "#3a3050"), p)
    front = lambda z: -0.16 + (z - 0.54) * math.tan(math.radians(16)) - 0.05   # just in front of the front legs at z
    tbox(kit, f"{A} {tag} top board", (0, front(1.12 - top_h), 1.12 - top_h / 2), (2.0, 0.04, top_h), top_mat, p, uv=top_uv)
    tbox(kit, f"{A} {tag} low board", (0, front(low_z - 0.1), low_z), (2.0, 0.04, 0.2), stripes, p,
         uv={'all': (0, 0, 0.1, 0.1), 'ny': (0, 0, 5.0, 1.0), 'py': (0, 0, 5.0, 1.0)})
    if lamp:
        x = lamp * 0.8
        tbox(kit, f"{A} {tag} lamp box", (x, -0.08, 1.17), (0.16, 0.1, 0.1), solid(kit, "lamp housing", INK, 0.1), p)
        tube(kit, f"{A} {tag} lamp lens", [(x, -0.08, 1.22), (x, -0.08, 1.4)], [0.12, 0.1],
             solid(kit, "amber lamp", "#ff9a1a", 2.6, shade="#ffc060"), p, sides=8)
        socket(kit, A, f"lamp {'L' if lamp > 0 else 'R'}", p, (x, -0.08, 1.3))


def build_roadblock(kit, root, A):
    stripes = tex_mat("roadblock stripes", tex_stripes(), ext='REPEAT')
    plain_uv = {'all': (0, 0, 0.1, 0.1), 'ny': (0, 0, 5.0, 1.2), 'py': (0, 0, 5.0, 1.2)}
    sawhorse(kit, A, "barricade L", root, (2.05, 0.15, 0), 3, stripes, plain_uv, 0.24, stripes, lamp=1)
    sawhorse(kit, A, "barricade C", root, (0, -0.1, 0), -2, tex_mat("police line board", tex_police_board(), 0.5),
             {'all': (0.5, 0.5, 0.52, 0.52), 'ny': (0, 0, 1, 1)}, 0.63, stripes, low_z=0.3)
    sawhorse(kit, A, "barricade R", root, (-2.05, 0.15, 0), -4, stripes, plain_uv, 0.24, stripes, lamp=-1)
    for i, (x, y, r) in enumerate(((2.85, -1.0, 10), (1.0, -1.05, 40), (-1.0, -1.0, 70), (-2.85, -0.95, 20))):
        traffic_cone(kit, kit.empty(f"{A} cone {i}", root, (x, y, 0), (0, 0, r)), f"{A} cone {i}")


ASSETS = [
    ("Hope Diamond", named("Hope Diamond", build_diamond)),
    ("Flavor Tub Rocky Road Diamond", named("Flavor Tub Rocky Road Diamond", build_diamond_tub)),
    ("Bait Shack", named("Bait Shack", build_shack)),
    ("Town Line Sign", named("Town Line Sign", build_town_sign)),
    ("Police Roadblock", named("Police Roadblock", build_roadblock)),
]
SPACING = 10


# ================================================================ scenes
def build_town_line(kit, root):
    R = kit.rand
    grass = tex_mat("scene grass", tex_grass(R), 0.3, ext='REPEAT')
    asph = tex_mat("scene asphalt", tex_road(R), 0.3, ext='REPEAT')
    tbox(kit, "ground", (0, -10, -0.05), (60, 80, 0.1), grass, root, uv={'all': (0, 0, 15, 20)})
    tbox(kit, "road", (0, -10, 0.0), (8, 80, 0.02), asph, root, uv={'all': (0, 0, 2, 20)})
    white, yel = solid(kit, "paint white", WHITE), solid(kit, "paint yellow", YEL)
    for sx in (-1, 1):
        tbox(kit, f"edge line {sx}", (sx * 3.7, -10, 0.012), (0.15, 80, 0.01), white, root)
    for i in range(16):
        tbox(kit, f"dash {i}", (0, 28 - i * 5, 0.012), (0.15, 2.0, 0.01), yel, root)
    for nm, fn, loc, rz in (("Bait Shack", build_shack, (-8.0, 1.5, 0), 90), ("Town Line Sign", build_town_sign, (5.6, -3.0, 0), 180),
                            ("Police Roadblock", build_roadblock, (0, -17.0, 0), 180)):
        named(nm, fn)(kit, kit.empty(f"scene {nm}", root, loc, (0, 0, rz)))
    kv = kit.empty("scene kevin", root, (-8.0 + 0.65, 1.5, FLOOR_Z), (0, 0, 90))
    shop_prefixed("Shopkeeper Kevin", build_kevin)(kit, kv)


def build_freezer(kit, root):
    tbox(kit, "freezer floor", (0, 0, -0.02), (1.4, 1.0, 0.04), solid(kit, "freezer floor", "#9fb4e8", shade="#8aa0dc"), root)
    named("Flavor Tub Rocky Road Diamond", build_diamond_tub)(kit, kit.empty("scene tub", root))


SCENES = [
    dict(name="town line", build=build_town_line, cam=((2.5, 13.0, 4.2), (-3.0, -6.0, 1.4), 30), res=(1600, 900)),
    dict(name="bait counter", build=build_town_line, cam=((-3.2, 0.2, 1.75), (-7.6, 1.5, 1.35), 32), res=(1600, 900)),
    dict(name="freezer diamond", build=build_freezer, cam=((0.0, -0.62, 0.92), (0.0, 0.0, 0.27), 45), res=(1200, 900)),
]
