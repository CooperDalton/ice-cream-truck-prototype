"""Batch "truck": the playable ice cream truck (separate moving parts, full walk-in interior, roof deck), the kitchen
stations as standalone placeable assets, and the bolt-on upgrades. Truck faces -Y, root at ground level, Z up."""
from style_H import *

# ---------------------------------------------------------------- truck layout (meters, truck root space)
FL, CE, RT = 0.75, 2.86, 2.92        # interior floor top, ceiling, roof top (2.11 m headroom)
W, WT = 1.15, 0.06                   # outer half width, wall thickness
IW = W - WT                          # inner half width
YF, YB, YR = -2.35, -0.95, 2.95      # cab front wall, cab/kitchen bulkhead, rear wall (outer faces)
ZB = 0.55                            # bottom edge of the body walls
WIN = (0.1, 1.5, 1.72, 2.55)         # serving window opening on +X: y0, y1, z0, z1
DOOR = (-2.05, -1.1, 0.8, 2.6)       # cab door openings (both sides): y0, y1, z0, z1
RDOOR = (-0.45, 0.45, 0.8, 2.65)     # rear door opening: x0, x1, z0, z1
HATCH = (-1.03, -0.45, 2.12, 2.72)   # roof hatch opening: x0, x1, y0, y1
WSH = (-1.0, 1.0, 1.55, 2.5)         # windshield opening: x0, x1, z0, z1
WHEEL_Y = (-2.65, 2.0)
ARCH = (1.45, 2.55, ZB, 1.0)         # rear wheel arch hole in the side walls
TURRET = (0.0, 0.45)
UPGRADE = dict(plow=(0, -3.35, 0.55), spikes=(0, 0.25, 1.0), armor=(0, 0, 0), turret2=(0.3, 1.95, RT),
               hopper=(IW - 0.35, -0.6, RT), engine=(0, -2.7, 1.4), tank=(-(W + 0.22), 0.05, 0.52))
CREAM = "#fff1c7"; BERRY = "#ff8fc8"; DECK = "#8a7fd0"
FUEL_INTAKE = (-IW + 0.25, -1.45, FL)  # cab, passenger side (left-hand drive: driver on +X); the station faces +X


# ---------------------------------------------------------------- helpers
def slab(kit, name, parent, n, pos, thick, ar, br, holes, mats, uv_out, uv_in, out_sign=1, loc=(0, 0, 0), rot=(0, 0, 0)):
    """Axis-aligned wall/roof slab with rectangular holes. n = normal axis ('x', 'y', 'z'); (a, b) are the other two
    axes in order (x: y,z / y: x,z / z: x,y). holes = [(a0, a1, b0, b1)]. mats = [outer, inner]; outer-boundary rims use
    the outer material, hole rims the inner one. uv_out / uv_in map (a, b) -> (u, v)."""
    acut = sorted({ar[0], ar[1]} | {min(max(h[k], ar[0]), ar[1]) for h in holes for k in (0, 1)})
    bcut = sorted({br[0], br[1]} | {min(max(h[k], br[0]), br[1]) for h in holes for k in (2, 3)})
    na, nb = len(acut) - 1, len(bcut) - 1
    cells = set()
    for i in range(na):
        for j in range(nb):
            ca, cb = (acut[i] + acut[i + 1]) / 2, (bcut[j] + bcut[j + 1]) / 2
            if not any(h[0] < ca < h[1] and h[2] < cb < h[3] for h in holes):
                cells.add((i, j))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    cache = {}

    def vert(i, j, s):
        if (i, j, s) not in cache:
            d = pos + s * thick / 2
            a, b = acut[i], bcut[j]
            cache[(i, j, s)] = bm.verts.new((d, a, b) if n == 'x' else (a, d, b) if n == 'y' else (a, b, d))
        return cache[(i, j, s)]

    def face(keys, mi, uvf):
        f = bm.faces.new([vert(*k) for k in keys])
        f.material_index = mi
        for lp, k in zip(f.loops, keys):
            lp[uvl].uv = uvf(acut[k[0]], bcut[k[1]])

    o = out_sign
    for (i, j) in cells:
        q = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
        face([(a, b, o) for a, b in q], 0, uv_out)
        face([(a, b, -o) for a, b in reversed(q)], 1, uv_in)
        for (di, dj), e0, e1 in (((0, -1), q[0], q[1]), ((1, 0), q[1], q[2]), ((0, 1), q[2], q[3]), ((-1, 0), q[3], q[0])):
            ni, nj = i + di, j + dj
            if (ni, nj) not in cells:
                outside = not (0 <= ni < na and 0 <= nj < nb)
                face([(*e0, o), (*e1, o), (*e1, -o), (*e0, -o)], 0 if outside else 1, uv_out if outside else uv_in)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mats, parent, loc, rot, smooth=False)


def dial(kit, name, parent, loc, r, mat, sides=12):
    """Flat round face with planar UVs, facing -Y (u = +X, v = +Z)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new((r * math.cos(2 * math.pi * k / sides), r * math.sin(2 * math.pi * k / sides), 0))
                      for k in range(sides)])
    for lp in f.loops:
        lp[uvl].uv = (0.5 + lp.vert.co.x / (2 * r), 0.5 + lp.vert.co.y / (2 * r))
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, (90, 0, 0), smooth=False)


def glass(kit):
    cache = kit.__dict__.setdefault("_hmats", {})
    if "glass" not in cache:
        c = Canvas(16, 16, "#3a4a9a")
        for x0 in (3, 9):
            for i in range(7):
                c.set(x0 + i, 3 + i, "#9fb4ff"); c.set(x0 + i + 1, 3 + i, "#9fb4ff")
        m = tex_mat("truck glass", c, emit=0.3, rough=0.2)
        p = next(nd for nd in m.node_tree.nodes if nd.type == 'BSDF_PRINCIPLED')
        p.inputs["Alpha"].default_value = 0.42
        cache["glass"] = m
    return cache["glass"]


def socket(kit, parent, name, loc, rot=(0, 0, 0)):
    ob = kit.empty(name, parent, loc, rot)
    ob.empty_display_type = 'ARROWS'
    ob.empty_display_size = 0.15
    return ob


def tile(s=0.6):
    return lambda a, b: (a / s, b / s)


def pint(kit, name, parent, loc, col, scoop=True):
    p = kit.empty(name, parent, loc)
    tube(kit, name + " cup", [(0, 0, 0), (0, 0, 0.12)], [0.05, 0.058], tex_mat(name, tex_pint(col)), p, sides=8)
    if scoop:
        lowball(kit, name + " scoop", (0, 0, 0.125), (0.055, 0.055, 0.04), solid(kit, "scoop " + col, hex_scale(col, 1.1), 0.45), p)
    return p


# ---------------------------------------------------------------- textures
def tex_body_side(rand, plus):
    """128x64 side livery. u runs front -> rear on +X, rear -> front on -X (so text reads left to right)."""
    c = Canvas(128, 64, WHITE)
    c.speckle(rand, ["#f4ebe2"], 70, 11, 52)
    c.rect(0, 0, 127, 9, PINK); c.rect(0, 10, 127, 10, BLUE)
    frosting(c, rand, 56, 47)
    if plus:
        c.rect(56, 29, 96, 55, MINT); c.rect(58, 31, 94, 53, INK)
        text(c, "ICE CREAM", 44, 27, PINK, 2, shadow=BLUE)
        cone_icon(c, 111, 31, 10, MINT)
        cone_icon(c, 45, 33, 9, PINK)
    else:
        text(c, "ICE", 8, 45, PINK, 3, shadow=BLUE)
        text(c, "CREAM", 8, 28, BLUE, 3, shadow=PINK)
        cone_icon(c, 82, 16, 15, MINT)
    return c


def tex_front(rand):
    c = Canvas(64, 64, WHITE)
    c.speckle(rand, ["#f4ebe2"], 30, 24, 55)
    c.rect(0, 0, 63, 22, PINK); c.rect(0, 23, 63, 23, BLUE)
    c.rect(2, 25, 61, 53, MINT)
    frosting(c, rand, 58, 54)
    return c


def tex_rear(rand):
    c = Canvas(64, 64, WHITE)
    c.speckle(rand, ["#f4ebe2"], 30, 11, 55)
    c.rect(0, 0, 63, 9, PINK); c.rect(0, 10, 63, 10, BLUE)
    for y in range(0, 6):
        for x in range(64):
            if ((x + y) // 3) % 2:
                c.set(x, y, YEL)
    c.rect(17, 5, 47, 58, MINT)
    cone_icon(c, 9, 24, 10, PINK); cone_icon(c, 55, 24, 10, MINT)
    frosting(c, rand, 58, 52)
    return c


def tex_cab_door(rand, plus):
    c = Canvas(32, 64, WHITE)
    c.speckle(rand, ["#f4ebe2"], 20, 7, 58)
    c.rect(0, 0, 31, 4, PINK); c.rect(0, 5, 31, 5, BLUE)
    c.rect(2, 28, 30, 60, MINT)
    c.rect(0, 62, 31, 63, MINT)
    hx = 25 if plus else 3
    c.rect(hx, 25, hx + 3, 26, INK)
    cone_icon(c, 16, 9, 8, YEL)
    return c


def tex_rear_door(rand):
    c = Canvas(32, 64, WHITE)
    c.speckle(rand, ["#f4ebe2"], 20, 8, 58)
    for y in range(0, 7):
        for x in range(32):
            c.set(x, y, INK if ((x + y) // 3) % 2 else YEL)
    c.rect(4, 34, 28, 58, MINT)
    c.rect(1, 28, 3, 30, INK)
    text(c, "YUM!", 8, 22, PINK, shadow=BLUE)
    return c


def tex_tiles(rand):
    c = Canvas(16, 16, WHITE)
    for k in (0, 8):
        c.rect(0, k, 15, k, "#bff5e6"); c.rect(k, 0, k, 15, "#bff5e6")
    c.rect(9, 1, 15, 7, "#ffd0e6")
    c.speckle(rand, ["#f4ebe2"], 8)
    return c


def tex_checker():
    c = Canvas(16, 16, WHITE)
    c.rect(0, 0, 7, 7, BERRY); c.rect(8, 8, 15, 15, BERRY)
    c.dots([(3, 12), (12, 4)], "#f4ebe2")
    return c


def tex_ceiling():
    c = Canvas(16, 16, LAV)
    c.rect(0, 0, 15, 0, LAV_D)
    c.dots([(2, 3), (10, 3), (6, 11), (14, 11)], "#e6dcff")
    return c


def tex_deck():
    c = Canvas(16, 16, DECK)
    for x0, y0 in ((2, 2), (10, 2), (6, 10), (14, 10)):
        c.dots([(x0, y0), (x0 + 1, y0 + 1), (x0 + 2, y0 + 2)], "#6f63b0")
        c.dots([(x0 + 1, y0), (x0 + 2, y0 + 1)], "#b3a9ee")
    return c


def tex_dash():
    c = Canvas(64, 16, "#5b4a8a")
    c.rect(0, 13, 63, 15, PINK); c.rect(0, 12, 63, 12, "#ff8fc8")
    c.rect(4, 2, 24, 9, "#4a3b78"); c.rect(13, 6, 15, 6, YEL)
    c.rect(28, 3, 36, 9, INK); c.rect(29, 7, 35, 8, MINT); c.dots([(30, 4), (32, 4), (34, 4)], PINK)
    for x in (40, 58):
        c.rect(x, 4, x + 3, 9, INK)
        for y in (5, 7):
            c.rect(x, y, x + 3, y, "#7a6aa8")
    return c


def tex_gauges():
    """Instrument binnacle face: speedometer (left) and fuel gauge (right)."""
    c = Canvas(32, 16, INK)
    c.rect(0, 15, 31, 15, PINK)
    disc(c, 10, 7, 6, "#8f66e6"); disc(c, 10, 7, 5, WHITE)
    for k in range(7):
        a = math.radians(210 - k * 40)
        c.set(round(10 + 4.4 * math.cos(a)), round(7 + 4.4 * math.sin(a)), RED if k > 4 else INK)
    for t in range(4):
        c.set(round(10 + t * math.cos(math.radians(60))), round(7 + t * math.sin(math.radians(60))), RED)
    disc(c, 24, 8, 4, "#8f66e6"); disc(c, 24, 8, 3, WHITE)
    for t in range(3):
        c.set(round(24 + t * math.cos(math.radians(150))), round(8 + t * math.sin(math.radians(150))), RED)
    text(c, "E", 18, 3, RED); text(c, "F", 27, 3, ZG)
    return c


def tex_seat():
    c = Canvas(16, 16, PINK)
    for x in (3, 7, 11, 15):
        c.rect(x, 0, x, 15, "#d63a86")
    c.rect(0, 14, 15, 15, "#ff8fc8")
    return c


def tex_churn():
    c = Canvas(64, 32, PINK)
    for x in range(0, 64, 5):
        c.rect(x, 0, x, 31, "#e63d8f")
    for y in (3, 27):
        c.rect(0, y - 1, 63, y + 1, YEL); c.rect(0, y + 1, 63, y + 1, "#fff6b0")
    c.rect(19, 10, 44, 21, WHITE); c.rect(19, 10, 44, 10, BLUE)
    text(c, "CHURN", 23, 18, BLUE)
    c.dots([(22, 12), (32, 12), (42, 12)], PINK)
    return c


def tex_flavor_tub(name, col, txt):
    c = Canvas(64, 32, WHITE)
    c.rect(0, 6, 63, 20, col); c.rect(0, 5, 63, 5, hex_scale(col, 0.75)); c.rect(0, 21, 63, 21, hex_scale(col, 0.75))
    for x0 in (32 - text_w(txt) // 2, 64 - text_w(txt) // 2):
        text(c, txt, x0 % 64, 16, WHITE, 1, shadow=hex_scale(col, 0.7))
    c.rect(0, 0, 63, 2, PINK); c.rect(0, 28, 63, 31, PINK)
    return c


FLAVORS = [("vanilla", CREAM, "#f5d98a", "VAN"), ("chocolate", CHOC, "#4e2812", "CHOC"), ("strawberry", BERRY, PINK, "BERRY"),
           ("mint", "#a8ffd9", "#22c79c", "MINT")]


def tex_freezer(rand):
    c = Canvas(64, 32, WHITE)
    c.speckle(rand, ["#dff4ff"], 40)
    c.rect(0, 0, 63, 3, MINT); c.rect(0, 26, 63, 27, PINK)
    for cx in (11, 52):
        for i in range(-3, 4):
            c.set(cx + i, 15, BLUE); c.set(cx, 15 + i, BLUE); c.set(cx + i, 15 + i, BLUE); c.set(cx + i, 15 - i, BLUE)
    text(c, "FREEZER", 18, 18, PINK, shadow=BLUE)
    c.rect(56, 30, 63, 31, "#2a3f7a")
    return c


def tex_counter():
    c = Canvas(64, 32, "#ffcf5a")
    for y in range(32):
        for x in range(64):
            if (x + y) % 5 == 0 or (x - y) % 5 == 0:
                c.set(x, y, "#d9862a")
    c.rect(0, 0, 63, 3, PINK); c.rect(0, 0, 1, 31, PINK); c.rect(62, 0, 63, 31, PINK); c.rect(0, 27, 63, 31, PINK)
    c.rect(19, 11, 44, 21, WHITE); c.rect(19, 11, 44, 11, MINT)
    text(c, "SCOOP", 23, 19, PINK, shadow=BLUE)
    return c


def tex_countertop(rand):
    c = Canvas(16, 16, WHITE)
    c.speckle(rand, [PINK, BLUE, YEL, MINT, PURP], 14)
    return c


def tex_pegboard():
    c = Canvas(32, 32, LAV)
    for y in range(1, 26, 3):
        for x in range(1, 32, 3):
            c.set(x, y, LAV_D)
    c.rect(0, 26, 31, 31, PINK)
    text(c, "GUNS", 9, 30, WHITE, shadow=DRED)
    return c


def tex_drawers():
    c = Canvas(32, 16, PINK)
    for y0 in (1, 8):
        c.rect(1, y0, 30, y0 + 5, "#ff8fc8"); c.rect(13, y0 + 2, 18, y0 + 3, YEL)
    return c


def tex_bin(label, col):
    c = Canvas(32, 32, WHITE)
    c.rect(0, 0, 31, 3, col); c.rect(0, 27, 31, 31, col)
    text(c, label, 16 - text_w(label) // 2, 22, col, shadow=INK if col == YEL else None)
    if label == "MILK":
        disc(c, 16, 10, 4, "#cfe4ff"); disc(c, 16, 10, 3, WHITE); c.rect(15, 14, 17, 16, "#cfe4ff")
    elif label == "SUGAR":
        c.rect(11, 6, 20, 14, "#e6e0ff"); c.rect(12, 7, 19, 13, WHITE); c.rect(12, 13, 19, 13, "#f4ebe2")
    else:
        for i, fc in enumerate((CREAM, CHOC, BERRY, MINT)):
            disc(c, 7 + i * 6, 10, 2, fc)
    c.rect(28, 30, 31, 31, "#2a2240")
    return c


def tex_gauge_dial():
    c = Canvas(32, 32, WHITE)
    for k in range(13):
        a = math.radians(210 - k * 20)
        col = RED if k < 3 else YEL if k < 6 else ZG
        for r in (11, 12):
            c.set(round(15.5 + r * math.cos(a)), round(15.5 + r * math.sin(a)), col)
        c.set(round(15.5 + 13 * math.cos(a)), round(15.5 + 13 * math.sin(a)), INK)
    text(c, "AMMO", 9, 10, BLUE)
    return c


def tex_gauge_plate():
    c = Canvas(32, 64, MINT)
    c.rect(0, 52, 31, 63, PINK)
    text(c, "AMMO", 9, 60, WHITE, shadow=DRED)
    for x, y in ((2, 2), (29, 2), (2, 49), (29, 49)):
        c.rect(x, y, x + 1, y + 1, "#1fbf95")
    c.rect(0, 0, 31, 0, "#1fbf95")
    return c


def tex_label(s, fg, bg, w=None):
    c = Canvas(w or text_w(s) + 4, 9, bg)
    text(c, s, 2, 7, fg)
    return c


def tex_hopper(big):
    c = Canvas(64, 32, WHITE)
    c.rect(0, 0, 63, 3, PINK); c.rect(0, 28, 63, 31, PINK); c.rect(0, 4, 63, 4, "#d63a86")
    c.rect(0, 9, 63, 22, MINT); c.rect(0, 8, 63, 8, "#22c79c"); c.rect(0, 23, 63, 23, "#22c79c")
    if big:
        text(c, "AMMO", 2, 19, WHITE, 2, shadow="#22c79c")
        c.rect(38, 6, 50, 25, INK); c.rect(39, 7, 49, 24, GLASS)
        for i, fc in enumerate((BERRY, CREAM, MINT, CHOC, YEL, BERRY)):
            disc(c, 41 + (i % 2) * 5, 9 + i * 3, 2, fc)
    else:
        text(c, "AMMO", 32 - text_w("AMMO", 2) // 2, 19, WHITE, 2, shadow="#22c79c")
    return c


def tex_armor():
    c = Canvas(32, 32, "#a99fd6")
    c.rect(0, 0, 31, 1, "#6f66a8"); c.rect(0, 30, 31, 31, "#cfc6f2")
    for x in range(2, 31, 6):
        for y in (4, 27):
            c.set(x, y, "#ece6ff"); c.set(x + 1, y - 1, "#6f66a8")
    c.speckle(random.Random(9), ["#9a90cc", "#b6adde"], 40, 6, 24)
    return c


def tex_heat():
    c = Canvas(8, 16, STEEL)
    c.rect(0, 10, 7, 12, "#c7a0ff"); c.rect(0, 13, 7, 14, ORNG); c.rect(0, 15, 7, 15, YEL)
    return c


def tex_perf():
    c = Canvas(16, 16, PINK)
    for y in range(1, 16, 3):
        for x in range((y // 3) % 2 * 2, 16, 4):
            c.set(x, y, "#b0306f")
    return c


# ---------------------------------------------------------------- shared parts
def turret_mount(kit, root, tag=""):
    """Roof turret mount: hazard-banded plate, bolts and a bearing ring. The turret sits on `socket turret`."""
    deck, haz = solid(kit, "mount plate", "#b8b0e0", shade="#9a90cc"), tex_mat("mount hazard", tex_hazard(), ext='REPEAT')
    tube(kit, "mount plate", [(0, 0, 0.0), (0, 0, 0.05)], 0.48, deck, root, sides=10)
    tube(kit, "mount hazard band", [(0, 0, 0.0), (0, 0, 0.06)], 0.5, haz, root, sides=10, caps=(False, False))
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        tbox(kit, f"mount bolt {k}", (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.065), (0.04, 0.04, 0.03),
             solid(kit, "bolt", YEL), root)
    tube(kit, "mount bearing", [(0, 0, 0.05), (0, 0, 0.12)], [0.4, 0.37], solid(kit, "turret blue", BLUE), root, sides=10)
    socket(kit, root, f"socket turret{tag}", (0, 0, 0.12))


def hopper(kit, root, big, tag=""):
    """Turret ammo hopper on the roof deck; the feed pipe drops through the roof to the kitchen hopper gauge."""
    steel, pink, mint = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "hopper pink", PINK), \
        solid(kit, "hopper mint", "#22c79c")
    r, z0, z1 = (0.27, 0.22, 1.05) if big else (0.2, 0.16, 0.58)
    tube(kit, "hopper feed pipe", [(0, 0, -0.08), (0, 0, z0)], 0.07, steel, root, sides=8)
    tube(kit, "hopper funnel", [(0, 0, z0 - 0.08), (0, 0, z0)], [0.08, r * 0.95], steel, root, sides=10)
    tube(kit, "hopper drum", [(0, 0, z0), (0, 0, z1)], [r * 0.95, r], tex_mat("hopper drum", tex_hopper(big)), root, sides=10)
    legs = 4 if big else 3
    for k in range(legs):
        a = 2 * math.pi * (k + 0.5) / legs
        tube(kit, f"hopper leg {k}", [(math.cos(a) * r * 1.25, math.sin(a) * r * 1.25, 0.0),
                                      (math.cos(a) * r * 0.9, math.sin(a) * r * 0.9, z0 + 0.12)], 0.022, pink, root,
             sides=4)
    if big:
        for z in (z0 + 0.06, z1 - 0.05):
            tube(kit, f"hopper band {z:.2f}", [(0, 0, z - 0.025), (0, 0, z + 0.025)], r + 0.02, pink, root, sides=10,
                 caps=(False, False))
        tbox(kit, "hopper sight", (0, -r - 0.02, (z0 + z1) / 2), (0.05, 0.03, z1 - z0 - 0.2), steel, root)
    lid = kit.empty("hopper lid", root, (0, r, z1), (-20 if big else 0, 0, 0))
    tube(kit, "hopper lid", [(0, -r, 0.0), (0, -r, 0.04)], r + 0.03, mint, lid, sides=10)
    tube(kit, "hopper lid knob", [(0, -r, 0.04), (0, -r, 0.08)], [0.04, 0.03], pink, lid, sides=6)
    socket(kit, root, f"socket hopper load{tag}", (0, 0, z1 + 0.05))


# ---------------------------------------------------------------- kitchen stations (front = -Y, root on the floor)
def build_churn(kit, root, tag=""):
    R = kit.rand
    steel, yel, pink = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "churn yellow", YEL), solid(kit, "churn pink", PINK)
    for i, (x, y) in enumerate(((0.17, 0.17), (-0.17, 0.17), (0.17, -0.17), (-0.17, -0.17))):
        tbox(kit, f"churn leg {i}", (x, y, 0.2), (0.05, 0.05, 0.4), steel, root, rot=(0, 0, 45))
    tube(kit, "churn base ring", [(0, 0, 0.36), (0, 0, 0.42)], 0.29, yel, root, sides=10)
    tube(kit, "churn drum", [(0, 0, 0.42), (0, 0, 1.06)], [0.25, 0.28], tex_mat("churn", tex_churn()), root, sides=10)
    tube(kit, "churn shoulder", [(0, 0, 1.06), (0, 0, 1.12)], [0.29, 0.2], steel, root, sides=10)
    # top hopper: milk + sugar + flavoring go in here
    tube(kit, "churn hopper", [(0, 0, 1.1), (0, 0, 1.18), (0, 0, 1.42)], [0.1, 0.14, 0.31], pink, root, sides=10,
         caps=(True, False))
    tube(kit, "churn hopper rim", [(0, 0, 1.41), (0, 0, 1.45)], 0.33, solid(kit, "churn mint", MINT), root, sides=10,
         caps=(False, False))
    lowball(kit, "churn mix", (0, 0, 1.32), (0.25, 0.25, 0.03), solid(kit, "churn mix", CREAM, 0.45), root, smooth=False)
    for i, (x, y, col) in enumerate(((0.08, -0.06, BERRY), (-0.1, 0.04, WHITE), (0.02, 0.1, CHOC))):
        lowball(kit, f"churn swirl {i}", (x, y, 1.345), (0.07, 0.05, 0.015), solid(kit, "swirl " + col, col, 0.45), root,
                smooth=False)
    # big crank on the +X side: gearbox, axle, crank pivot (spins about local X)
    tbox(kit, "churn gearbox", (0.31, 0, 0.86), (0.1, 0.24, 0.24), pink, root)
    tube(kit, "churn axle", [(0.36, 0, 0.86), (0.44, 0, 0.86)], 0.035, steel, root, sides=6)
    crank = kit.empty("churn crank", root, (0.44, 0, 0.86), (25, 0, 0))
    tube(kit, "churn gear", [(0, 0, 0), (0.035, 0, 0)], 0.17, tex_mat("churn gear", tex_hazard(), ext='REPEAT'), crank,
         sides=12)
    tbox(kit, "churn crank arm", (0.05, 0, 0.17), (0.035, 0.06, 0.42), yel, crank)
    tube(kit, "churn crank handle", [(0.05, 0, 0.36), (0.24, 0, 0.36)], 0.028, pink, crank, sides=6)
    lowball(kit, "churn crank knob", (0.25, 0, 0.36), (0.045, 0.045, 0.045), yel, crank)
    # spout and the tub slot it fills
    tube(kit, "churn spout", [(0, -0.24, 0.5), (0, -0.33, 0.48), (0, -0.37, 0.42)], [0.045, 0.04, 0.04], steel, root,
         sides=6, side=(1, 0, 0))
    spv = kit.empty("churn spout valve", root, (0, -0.33, 0.53))
    tbox(kit, "churn spout valve", (0.05, 0, 0.02), (0.12, 0.025, 0.025), yel, spv)
    lowball(kit, "churn drip", (0, -0.37, 0.38), (0.02, 0.02, 0.03), solid(kit, "drip", BERRY, 0.5), root, smooth=False)
    tbox(kit, "churn tub tray", (0, -0.38, 0.025), (0.34, 0.3, 0.05), steel, root)
    tub = kit.empty("churn tub", root, (0, -0.38, 0.05))
    tube(kit, "churn tub", [(0, 0, 0), (0, 0, 0.26)], [0.1, 0.115], tex_mat("churn tub", tex_flavor_tub("s", BERRY, "BERRY")),
         tub, sides=10, caps=(True, False))
    tube(kit, "churn tub fill", [(0, 0, 0.18), (0, 0, 0.2)], 0.108, solid(kit, "fill berry", BERRY, 0.45), tub, sides=10,
         bulge=(0, 0.02))
    socket(kit, root, f"socket use point{tag}", (0, -0.85, 0))
    socket(kit, root, f"socket hopper{tag}", (0, 0, 1.42))
    socket(kit, root, f"socket tub{tag}", (0, -0.38, 0.05))


def tub_in(kit, parent, name, loc, flavor, top):
    nm, col, dark, txt = flavor
    t = kit.empty(name, parent, loc)
    tube(kit, name, [(0, 0, -top), (0, 0, 0)], [0.105, 0.115], tex_mat(name, tex_flavor_tub(nm, col if nm != "vanilla" else "#f5d98a", txt)),
         t, sides=10, caps=(False, False))
    tube(kit, name + " cream", [(0, 0, -0.02), (0, 0, -0.005)], 0.108, solid(kit, "cream " + nm, col, 0.45, shade=dark), t,
         sides=10, bulge=(0, 0.02))
    return t


def build_freezer(kit, root, tag=""):
    R = kit.rand
    t = tex_mat("freezer", tex_freezer(R))
    side = (0.0, 0.05, 0.08, 0.8)
    tbox(kit, "freezer plinth", (0, 0, 0.04), (1.16, 0.6, 0.08), solid(kit, "plinth", INK, 0.1), root)
    tbox(kit, "freezer body", (0, 0, 0.46), (1.2, 0.65, 0.76), t, root,
         uv={'px': side, 'nx': side, 'py': side, 'pz': (0.89, 0.945, 0.98, 0.99), 'nz': side})
    xs = (-0.45, -0.15, 0.15, 0.45)
    white, well = solid(kit, "freezer white", WHITE), solid(kit, "freezer well", "#2a3f7a", 0.2)
    slab(kit, "freezer deck", root, 'z', 0.87, 0.06, (-0.6, 0.6), (-0.325, 0.325),
         [(x - 0.125, x + 0.125, -0.125, 0.125) for x in xs], [white, well], tile(), tile())
    for i, x in enumerate(xs[:3]):
        tub_in(kit, root, f"freezer tub {i + 1}", (x, 0, 0.92), FLAVORS[i], 0.2)
    mint = solid(kit, "freezer mint", MINT)
    for y in (-0.305, 0.305):
        tbox(kit, f"freezer rail {y}", (0, y, 0.915), (1.2, 0.04, 0.03), mint, root)
    # The freezer is open-topped (it had sliding glass lids); their handle material is still made here so the shared
    # random sequence, and with it every later texture of the truck, stays the same.
    solid(kit, "handle pink", PINK)
    socket(kit, root, f"socket use point{tag}", (0, -0.75, 0))
    for i, x in enumerate(xs):
        socket(kit, root, f"socket slot {i + 1}{tag}", (x, 0, 0.72))


def build_scoop_counter(kit, root, tag=""):
    R = kit.rand
    t = tex_mat("counter", tex_counter())
    side = (0.0, 0.2, 0.03, 0.8)
    tbox(kit, "counter plinth", (0, 0.02, 0.04), (1.36, 0.54, 0.08), solid(kit, "plinth", INK, 0.1), root)
    tbox(kit, "counter cabinet", (0, 0.02, 0.49), (1.36, 0.56, 0.82), t, root, uv={'px': side, 'nx': side, 'py': side, 'pz': side})
    top = tbox(kit, "counter top", (0, -0.0, 0.925), (1.44, 0.62, 0.05), tex_mat("countertop", tex_countertop(R), ext='REPEAT'),
               root, uv={'all': (0, 0, 2.4, 1)})
    mint, steel = solid(kit, "holder mint", MINT), solid(kit, "steel", STEEL, shade="#a9a2e0")
    xs = (-0.6, -0.43, -0.26, -0.09)
    for i, x in enumerate(xs):
        tube(kit, f"pint holder {i + 1}", [(x, -0.14, 0.95), (x, -0.14, 1.0)], [0.068, 0.072], mint, root, sides=8,
             caps=(True, False))
    for i, col in ((0, PINK), (2, MINT)):
        pint(kit, f"counter pint {i + 1}", root, (xs[i], -0.14, 0.955), col)
    # tub well with a chocolate tub and a dipper well holding the scoop
    tube(kit, "tub well rim", [(0.42, 0.04, 0.95), (0.42, 0.04, 0.98)], [0.14, 0.15], steel, root, sides=10, caps=(False, False))
    tub_in(kit, root, "counter tub", (0.42, 0.04, 0.985), FLAVORS[1], 0.06)
    lowball(kit, "tub divot", (0.38, -0.0, 0.975), (0.05, 0.04, 0.01), solid(kit, "divot", "#4e2812", 0.2), root, smooth=False)
    tbox(kit, "dipper well", (0.12, -0.08, 0.97), (0.14, 0.2, 0.05), steel, root)
    tbox(kit, "dipper water", (0.12, -0.08, 0.996), (0.11, 0.17, 0.004), solid(kit, "water", "#8fd8ff", 0.5), root)
    sc = kit.empty("counter scoop", root, (0.12, -0.12, 1.0), (-40, 0, 15))
    tube(kit, "scoop handle", [(0, 0, 0.03), (0, 0, 0.2)], 0.017, solid(kit, "scoop yellow", YEL), sc, sides=6)
    lowball(kit, "scoop bowl", (0, 0, 0.0), (0.04, 0.04, 0.03), steel, sc)
    tbox(kit, "counter napkins", (-0.5, 0.2, 1.0), (0.14, 0.1, 0.1), solid(kit, "napkin box", BLUE), root)
    socket(kit, root, f"socket use point{tag}", (0, -0.75, 0))
    socket(kit, root, f"socket scoop{tag}", (0.12, -0.12, 1.0))
    socket(kit, root, f"socket tub{tag}", (0.42, 0.04, 0.78))
    for i, x in enumerate(xs):
        socket(kit, root, f"socket pint {i + 1}{tag}", (x, -0.14, 0.955))


def build_gun_rack(kit, root, tag=""):
    t_cab = tex_mat("rack drawers", tex_drawers())
    side = (0.0, 0.0, 0.1, 1.0)
    tbox(kit, "rack cabinet", (0, 0, 0.3), (0.9, 0.35, 0.6), t_cab, root, uv={'px': side, 'nx': side, 'py': side, 'pz': side})
    tbox(kit, "rack board", (0, 0.15, 1.22), (0.9, 0.05, 1.24), tex_mat("pegboard", tex_pegboard()), root,
         uv={'px': (0, 0, 0.05, 0.8), 'nx': (0, 0, 0.05, 0.8), 'pz': (0, 0.9, 1, 1)})
    yel, pink, ink = solid(kit, "rack yellow", YEL), solid(kit, "rack pink", PINK), solid(kit, "rack dark", INK, 0.1)
    tbox(kit, "rack cradle", (0, 0.0, 0.64), (0.9, 0.24, 0.08), yel, root)
    tbox(kit, "rack clip bar", (0, 0.09, 1.34), (0.9, 0.06, 0.06), pink, root)
    xs = (-0.33, -0.11, 0.11, 0.33)
    rot = (-90, 0, -90)
    for i, x in enumerate(xs):
        tbox(kit, f"rack notch {i + 1}", (x, -0.02, 0.681), (0.07, 0.16, 0.004), ink, root)
        clip = kit.empty(f"rack clip {i + 1}", root, (x, 0.06, 1.34))
        tube(kit, f"rack clip {i + 1}", [(-0.05, 0, 0), (-0.05, -0.08, 0), (0.05, -0.08, 0), (0.05, 0, 0)], 0.012, yel, clip,
             sides=4, side=(0, 0, 1), caps=(False, False))
        socket(kit, root, f"socket gun {i + 1}{tag}", (x, -0.02, 1.03), rot)
    build_shotgun(kit, kit.empty("rack shotgun", root, (xs[0], -0.02, 1.03), rot))
    build_gun(kit, kit.empty("rack pistol", root, (xs[2], -0.02, 1.04), rot))
    socket(kit, root, f"socket use point{tag}", (0, -0.7, 0))


def build_bins(kit, root, tag=""):
    R = kit.rand
    tbox(kit, "bins plinth", (0, 0, 0.03), (0.98, 0.42, 0.06), solid(kit, "plinth", INK, 0.1), root)
    side = (0.0, 0.3, 0.1, 0.7)
    for i, (label, col, nm) in enumerate((("MILK", BLUE, "milk"), ("SUGAR", PINK, "sugar"), ("FLAVOR", PURP, "flavoring"))):
        x = -0.33 + i * 0.33
        tbox(kit, f"bin {nm}", (x, 0, 0.42), (0.31, 0.44, 0.72), tex_mat(f"bin {nm}", tex_bin(label, col)), root,
             uv={'px': side, 'nx': side, 'py': side, 'pz': (0.89, 0.95, 0.97, 0.99)})
        lid = kit.empty(f"bin {nm} lid", root, (x, 0.22, 0.78), ((-100, -72, -88)[i], 0, 0))
        tbox(kit, f"bin {nm} lid", (0, -0.22, 0.015), (0.31, 0.45, 0.03), solid(kit, "lid " + col, col), lid)
        tbox(kit, f"bin {nm} lid handle", (0, -0.43, 0.04), (0.1, 0.03, 0.025), solid(kit, "bin yellow", YEL), lid)
        socket(kit, root, f"socket {nm}{tag}", (x, 0, 0.8))
    t_bottle = tex_mat("bin milk bottle", tex_bottle())
    for k, (x, y) in enumerate(((-0.4, -0.08), (-0.27, -0.06), (-0.37, 0.09))):
        tube(kit, f"bin milk bottle {k}", [(x, y, 0.6), (x, y, 0.82), (x, y, 0.88), (x, y, 0.94), (x, y, 0.96)],
             [0.05, 0.05, 0.028, 0.024, 0.026], t_bottle, root, sides=8)
    lowball(kit, "bin sugar mound", (0, 0, 0.78), (0.13, 0.19, 0.07), solid(kit, "sugar", WHITE, 0.5, shade="#e6e0ff"), root)
    sc = kit.empty("bin sugar scoop", root, (0.04, -0.05, 0.84), (0, 35, 30))
    tube(kit, "sugar scoop", [(0, 0, 0), (0, 0, 0.14)], [0.035, 0.03], solid(kit, "steel", STEEL, shade="#a9a2e0"), sc, sides=6,
         caps=(True, False))
    for k, (fc, cap) in enumerate(((CREAM, "#f5d98a"), (CHOC, "#4e2812"), (BERRY, PINK), (MINT, "#22c79c"))):
        x, y = 0.26 + (k % 2) * 0.12, -0.07 + (k // 2) * 0.13
        tube(kit, f"flavor bottle {k}", [(x, y, 0.6), (x, y, 0.84), (x, y, 0.88)], [0.04, 0.04, 0.02],
             solid(kit, "syrup " + fc, fc, 0.45), root, sides=6)
        tube(kit, f"flavor nozzle {k}", [(x, y, 0.88), (x, y, 0.94)], [0.02, 0.005], solid(kit, "nozzle " + cap, cap), root, sides=4)
    socket(kit, root, f"socket use point{tag}", (0, -0.7, 0))


def build_hopper_gauge(kit, root, tag=""):
    """Wall-mounted (back plane at y = 0). Dial reads the roof turret hopper; pints go up the pneumatic pipe."""
    steel, pink, yel = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "gauge pink", PINK), solid(kit, "gauge yellow", YEL)
    tbox(kit, "gauge plate", (-0.05, -0.015, 1.5), (0.62, 0.03, 0.9), tex_mat("gauge plate", tex_gauge_plate()), root,
         uv={'px': (0, 0, 0.05, 0.05), 'nx': (0, 0, 0.05, 0.05), 'pz': (0, 0, 0.05, 0.05), 'nz': (0, 0, 0.05, 0.05)})
    dx, dz = -0.12, 1.55
    tube(kit, "gauge bezel", [(dx, -0.03, dz), (dx, -0.08, dz)], 0.21, pink, root, sides=12, front=(0, 0, 1))
    dial(kit, "gauge face", root, (dx, -0.082, dz), 0.185, tex_mat("gauge dial", tex_gauge_dial()))
    needle = kit.empty("gauge needle", root, (dx, -0.088, dz), (0, 52, 0))
    tbox(kit, "gauge needle", (0, 0, 0.07), (0.018, 0.006, 0.16), solid(kit, "needle", RED, 0.6), needle)
    lowball(kit, "gauge hub", (dx, -0.09, dz), (0.02, 0.012, 0.02), yel, root, smooth=False)
    lowball(kit, "gauge lamp", (dx, -0.05, 1.86), (0.035, 0.035, 0.035), solid(kit, "lamp red", RED, 1.2), root)
    # pneumatic feed pipe up through the ceiling to the roof hopper, with a front loading mouth and flap
    # the pipe hugs the wall, then doglegs out at the ceiling so the roof hopper clears the railing
    px, py, top = 0.2, -0.1, -0.35
    tube(kit, "gauge pipe", [(px, py, 1.12), (px, py, 1.18), (px, py, 1.8), (px, (py + top) / 2, 1.96), (px, top, 2.0),
                             (px, top, 2.14)], [0.05, 0.06, 0.06, 0.06, 0.06, 0.06], steel, root, sides=8, side=(1, 0, 0))
    for z in (1.45, 1.7):
        tube(kit, f"gauge pipe band {z}", [(px, py, z - 0.03), (px, py, z + 0.03)], 0.068, pink, root, sides=8)
        tbox(kit, f"gauge pipe bracket {z}", (px, -0.03, z), (0.04, 0.06, 0.03), steel, root)
    tube(kit, "gauge mouth", [(px, py, 1.3), (px, py - 0.1, 1.3), (px, py - 0.14, 1.3)], [0.07, 0.08, 0.1], pink, root,
         sides=8, side=(1, 0, 0), caps=(False, False))
    flap = kit.empty("gauge flap", root, (px, py - 0.145, 1.4), (-70, 0, 0))
    tbox(kit, "gauge flap", (0, 0, -0.09), (0.18, 0.015, 0.18), yel, flap)
    tbox(kit, "gauge load label", (px - 0.02, -0.04, 1.13), (0.2, 0.01, 0.075), tex_mat("load label", tex_label("LOAD", INK, YEL)), root,
         uv={'px': (0, 0, 0.05, 0.05), 'nx': (0, 0, 0.05, 0.05)})
    socket(kit, root, f"socket use point{tag}", (0, -0.85, 0))
    socket(kit, root, f"socket load{tag}", (px, py - 0.14, 1.3))


def build_roof_bell(kit, root, tag=""):
    """Bell on a speaking pipe that drops into the kitchen. The gunner whacks it with the hanging mallet."""
    steel, pink, yel = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "bell pink", PINK), solid(kit, "bell gold", YEL,
                                                                                                        shade="#e0b020")
    tbox(kit, "bell flange", (0, 0, 0.02), (0.24, 0.24, 0.04), steel, root)
    tube(kit, "bell pipe", [(0, 0, 0.04), (0, 0, 0.9), (0, -0.05, 1.0), (0, -0.14, 1.06), (0, -0.24, 1.07)],
         [0.04, 0.035, 0.035, 0.035, 0.03], pink, root, sides=6, side=(1, 0, 0))
    for z in (0.15, 0.6):
        tube(kit, f"bell band {z}", [(0, 0, z - 0.025), (0, 0, z + 0.025)], 0.045, yel, root, sides=6)
    tbox(kit, "bell sign", (0, -0.045, 0.42), (0.2, 0.012, 0.08), tex_mat("bang label", tex_label("BANG", WHITE, RED)), root,
         uv={'px': (0, 0, 0.05, 0.05), 'nx': (0, 0, 0.05, 0.05), 'pz': (0, 0, 0.05, 0.05)})
    bell = kit.empty("bell", root, (0, -0.25, 1.05))
    tube(kit, "bell body", [(0, 0, 0.0), (0, 0, -0.05), (0, 0, -0.14), (0, 0, -0.2)], [0.03, 0.08, 0.11, 0.155], yel, bell,
         sides=10, caps=(True, False))
    tube(kit, "bell lip", [(0, 0, -0.2), (0, 0, -0.22)], [0.16, 0.16], solid(kit, "bell lip", "#e0b020"), bell, sides=10,
         caps=(False, False))
    tube(kit, "bell clapper", [(0, 0, -0.03), (0, 0, -0.19)], 0.01, steel, bell, sides=4)
    lowball(kit, "bell clapper ball", (0, 0, -0.2), (0.03, 0.03, 0.03), steel, bell)
    mallet = kit.empty("bell mallet", root, (0.06, 0, 0.78), (0, 0, 0))
    tube(kit, "mallet hook", [(-0.02, 0, 0.0), (0.0, 0, 0.02), (0.02, 0, 0.0)], 0.008, steel, mallet, sides=4, side=(0, 1, 0))
    tube(kit, "mallet handle", [(0.02, 0, 0.0), (0.02, 0, -0.34)], 0.014, yel, mallet, sides=6)
    tube(kit, "mallet head", [(0.02, -0.08, -0.37), (0.02, 0.08, -0.37)], 0.05, pink, mallet, sides=8, side=(1, 0, 0))
    socket(kit, root, f"socket use point{tag}", (0, -0.6, 0))
    socket(kit, root, f"socket strike{tag}", (0, -0.25, 0.85))


# ---------------------------------------------------------------- the truck
def wheel_spin(kit, name, parent, loc, side, steer, mats):
    """Axle pivot (spins about X). Front wheels get a steer pivot (yaws about Z) above the axle pivot."""
    if steer:
        parent = kit.empty(name + " steer", parent, loc)
        loc = (0, 0, 0)
    return wheel(kit, name, parent, loc, side, *mats)


def base_plow(kit, root):
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    yel = solid(kit, "truck yellow", YEL)
    plow = kit.empty("plow", root, (0, 0, 0), (16, 0, 0))
    tbox(kit, "plow blade", (0, 0, 0), (2.5, 0.1, 0.72), t_haz, plow, uv={'all': (0, 0, 3, 1)})
    for i in range(7):
        x = -1.08 + i * 0.36
        tube(kit, f"plow tooth {i}", [(x, -0.04, -0.36), (x, -0.2, -0.36)], [(0.07, 0.03), 0.004], yel, plow, sides=4,
             side=(1, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"plow strut {sx}", (sx * 0.7, 0.18, 0.05), (0.1, 0.36, 0.1), solid(kit, "truck dark", INK, 0.1), plow)
    return plow


def build_ice_cream_truck(kit, root):
    """Returns dict(roof=, side=, plow=, hopper=) pivots so scenes can cut away or swap parts."""
    R = kit.rand
    pink, yel, white, ink = solid(kit, "truck pink", PINK), solid(kit, "truck yellow", YEL), solid(kit, "truck white", WHITE), \
        solid(kit, "truck dark", INK, 0.1)
    mint, steel = solid(kit, "truck mint", MINT), solid(kit, "steel", STEEL, shade="#a9a2e0")
    t_tile = tex_mat("kitchen tiles", tex_tiles(R), ext='REPEAT')
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    vinyl = solid(kit, "door vinyl", "#ff8fc8", shade="#e676b0")
    truck = kit.empty("truck", root)
    side = kit.empty("side +X", truck)     # everything on the serving-window wall (hidden in the cutaway)
    roof = kit.empty("roof deck", truck)   # roof slab and everything on it
    L, H = YR - YF, RT - ZB

    # ---- shell: floor, side walls, front, rear, bulkhead, roof
    tbox(kit, "chassis", (0, -0.05, 0.46), (1.9, 6.0, 0.18), ink, truck)
    tbox(kit, "floor", (0, (YF + YR) / 2, FL - 0.06), (2 * IW, L - 2 * WT, 0.12), tex_mat("floor", tex_checker(), ext='REPEAT'),
         truck, uv={'all': (0, 0, 2 * IW / 0.6, (L - 2 * WT) / 0.6)})
    for sx in (1, -1):
        holes = [(YF, -2.2, ZB, 0.85), DOOR[:2] + DOOR[2:], ARCH] + ([WIN] if sx > 0 else [])
        uvo = (lambda a, b: ((a - YF) / L, (b - ZB) / H)) if sx > 0 else (lambda a, b: ((YR - a) / L, (b - ZB) / H))
        slab(kit, f"wall {'+X' if sx > 0 else '-X'}", side if sx > 0 else truck, 'x', sx * (W - WT / 2), WT, (YF, YR), (ZB, RT),
             holes, [tex_mat(f"body side {sx}", tex_body_side(R, sx > 0)), t_tile], uvo, tile(), out_sign=sx)
        tbox(kit, f"wheel well {sx}", (sx * (IW - 0.15), sum(ARCH[:2]) / 2, FL + 0.13), (0.3, ARCH[1] - ARCH[0], 0.26), steel, truck)
    slab(kit, "wall front", truck, 'y', YF + WT / 2, WT, (-IW, IW), (ZB, RT), [WSH],
         [tex_mat("body front", tex_front(R)), t_tile], lambda a, b: ((a + IW) / (2 * IW), (b - ZB) / H), tile(), out_sign=-1)
    slab(kit, "wall rear", truck, 'y', YR - WT / 2, WT, (-IW, IW), (ZB, RT), [RDOOR],
         [tex_mat("body rear", tex_rear(R)), t_tile], lambda a, b: ((IW - a) / (2 * IW), (b - ZB) / H), tile(), out_sign=1)
    slab(kit, "bulkhead", truck, 'y', YB, 0.05, (-IW, IW), (FL, CE), [(-0.5, 0.5, FL, 2.5)], [t_tile, t_tile], tile(), tile())
    slab(kit, "roof", roof, 'z', (CE + RT) / 2, RT - CE, (-IW, IW), (YF + WT, YR - WT), [HATCH],
         [tex_mat("deck", tex_deck(), ext='REPEAT'), tex_mat("ceiling", tex_ceiling(), ext='REPEAT')], tile(0.5), tile(0.5))
    tbox(kit, "windshield post", (0, YF - 0.005, sum(WSH[2:]) / 2), (0.06, 0.07, WSH[3] - WSH[2]), ink, truck)
    tbox(kit, "windshield glass", (0, YF + WT / 2, sum(WSH[2:]) / 2), (WSH[1] - WSH[0], 0.015, WSH[3] - WSH[2]), glass(kit), truck)
    tbox(kit, "ceiling light", (0, 1.0, CE - 0.02), (0.22, 2.4, 0.04), solid(kit, "light", "#fff6d0", 2.2), roof)
    tbox(kit, "cab dome light", (0, -1.5, CE - 0.02), (0.25, 0.25, 0.04), solid(kit, "light", "#fff6d0", 2.2), roof)

    # ---- hood, bumpers, fenders, wheels, mirrors, lights, steps
    tbox(kit, "hood", (0, -2.7, 0.975), (2.14, 0.7, 0.85), tex_mat("grille", tex_grille()), truck, taper=(0.98, 0.9),
         uv={'px': (0.0, 0.5, 0.05, 0.6), 'nx': (0.0, 0.5, 0.05, 0.6), 'pz': (0.0, 0.5, 0.05, 0.6), 'py': (0.0, 0.5, 0.05, 0.6)})
    tbox(kit, "front bumper", (0, -3.08, 0.6), (2.24, 0.12, 0.16), steel, truck)
    tbox(kit, "rear bumper", (0, YR + 0.1, 0.55), (2.24, 0.18, 0.14), white, truck)
    tbox(kit, "rear step", (0, YR + 0.25, 0.42), (0.95, 0.3, 0.05), t_haz, truck, uv={'pz': (0, 0, 3, 1)})
    tire = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050")
    for sx in (1, -1):
        for k, (y, nm) in enumerate(zip(WHEEL_Y, ("front", "rear"))):
            wheel_spin(kit, f"wheel {nm} {'+X' if sx > 0 else '-X'}", truck, (sx * 1.0, y, 0.45), sx, k == 0, (tire, white, pink))
        tbox(kit, f"fender {sx}", (sx * 1.04, -2.65, 0.95), (0.3, 1.0, 0.08), pink, truck)
        tbox(kit, f"mirror arm {sx}", (sx * 1.24, -2.32, 2.15), (0.2, 0.04, 0.04), ink, truck)
        tbox(kit, f"mirror {sx}", (sx * 1.36, -2.32, 2.1), (0.06, 0.12, 0.26), pink, truck)
        tbox(kit, f"door step {sx}", (sx * 1.21, sum(DOOR[:2]) / 2, 0.42), (0.16, 0.8, 0.05), t_haz, truck, uv={'pz': (0, 0, 3, 1)})
        tbox(kit, f"tail light {sx}", (sx * 0.82, YR + 0.005, 1.05), (0.22, 0.03, 0.3), solid(kit, "tail light", RED, 1.0), truck)
        tbox(kit, f"marker light {sx}", (sx * 0.9, YF - 0.005, 2.78), (0.14, 0.02, 0.06), solid(kit, "marker", ORNG, 1.2), truck)
    plow = base_plow(kit, kit.empty("plow mount", truck, UPGRADE['plow']))

    # ---- cab doors (hinge at the front edge, swing about Z) with windows
    dw, dh = DOOR[1] - DOOR[0] - 0.01, DOOR[3] - DOOR[2] - 0.01
    for sx in (1, -1):
        nm = '+X' if sx > 0 else '-X'
        door = kit.empty(f"cab door {nm}", side if sx > 0 else truck, (sx * (W - 0.03), DOOR[0] + 0.005, DOOR[2]))
        uvo = (lambda a, b: (a / dw, b / dh)) if sx > 0 else (lambda a, b: (1 - a / dw, b / dh))
        slab(kit, f"cab door {nm}", door, 'x', 0, 0.05, (0, dw), (0, dh), [(0.1, dw - 0.1, 0.85, 1.65)],
             [tex_mat(f"cab door {nm}", tex_cab_door(R, sx > 0)), vinyl], uvo, tile(), out_sign=sx)
        tbox(kit, f"cab door {nm} glass", (0, dw / 2, 1.25), (0.015, dw - 0.2, 0.8), glass(kit), door)
        tbox(kit, f"cab door {nm} handle", (sx * 0.035, dw - 0.1, 0.75), (0.03, 0.12, 0.035), steel, door)
        tbox(kit, f"cab door {nm} inner handle", (-sx * 0.035, dw - 0.1, 0.75), (0.03, 0.1, 0.03), steel, door)

    # ---- rear door (hinge on the -X edge, swings about Z)
    rw, rh = RDOOR[1] - RDOOR[0] - 0.01, RDOOR[3] - RDOOR[2] - 0.01
    rdoor = kit.empty("rear door", truck, (RDOOR[0] + 0.005, YR - WT / 2, RDOOR[2]))
    slab(kit, "rear door", rdoor, 'y', 0, 0.05, (0, rw), (0, rh), [(0.2, rw - 0.2, 1.05, 1.6)],
         [tex_mat("rear door", tex_rear_door(R)), vinyl], lambda a, b: (1 - a / rw, b / rh), tile(), out_sign=1)
    tbox(kit, "rear door glass", (rw / 2, 0, 1.325), (rw - 0.4, 0.015, 0.55), glass(kit), rdoor)
    tbox(kit, "rear door handle", (rw - 0.08, 0.035, 0.75), (0.12, 0.03, 0.035), steel, rdoor)

    # ---- serving window (+X): frame, outside ledge, shutter that flips up into an awning
    wy, wz = (WIN[0] + WIN[1]) / 2, (WIN[2] + WIN[3]) / 2
    for nm, cy, cz, sy, sz in (("top", wy, WIN[3], WIN[1] - WIN[0] + 0.1, 0.06), ("bottom", wy, WIN[2], WIN[1] - WIN[0] + 0.1, 0.06),
                               ("front", WIN[0], wz, 0.06, WIN[3] - WIN[2]), ("rear", WIN[1], wz, 0.06, WIN[3] - WIN[2])):
        tbox(kit, f"window frame {nm}", (W + 0.015, cy, cz), (0.04, sy, sz), mint, side)
    tbox(kit, "window ledge", (W + 0.12, wy, WIN[2] - 0.02), (0.26, WIN[1] - WIN[0], 0.05), pink, side)
    for y in (WIN[0] + 0.2, WIN[1] - 0.2):
        tbox(kit, f"window ledge bracket {y:.1f}", (W + 0.06, y, WIN[2] - 0.12), (0.12, 0.04, 0.16), pink, side, rot=(0, 40, 0))
    shut = kit.empty("serving shutter", side, (W + 0.04, wy, WIN[3] + 0.03), (0, -72, 0))
    sl = WIN[1] - WIN[0] + 0.06
    tbox(kit, "serving shutter", (0.02, 0, -(WIN[3] - WIN[2] + 0.06) / 2), (0.04, sl, WIN[3] - WIN[2] + 0.06),
         tex_mat("awning", tex_awning(), ext='REPEAT'), shut, uv={'all': (0, 0, 6, 1)})
    for i in range(7):
        y = -sl / 2 + (i + 0.5) * sl / 7
        lowball(kit, f"shutter scallop {i}", (0.02, y, -(WIN[3] - WIN[2] + 0.06) - 0.03), (0.03, 0.1, 0.05),
                pink if i % 2 else white, shut, smooth=False)
    tbox(kit, "shutter handle", (0.06, 0, -(WIN[3] - WIN[2]) + 0.02), (0.03, 0.2, 0.03), steel, shut)

    # ---- cab interior: dashboard, instruments, steering wheel, pedals, seat, gear stick
    t_dash = tex_mat("dash", tex_dash())
    tbox(kit, "dashboard", (0, YF + WT + 0.17, 1.33), (2 * IW, 0.34, 0.36), t_dash, truck, taper=(1.0, 0.75),
         uv={'px': (0, 0, 0.05, 0.1), 'nx': (0, 0, 0.05, 0.1), 'pz': (0, 0.0, 0.05, 0.1)})
    tbox(kit, "dash console", (0, YF + WT + 0.2, (FL + 1.15) / 2), (0.34, 0.4, 1.15 - FL), solid(kit, "console", "#5b4a8a"), truck)
    tbox(kit, "instruments", (0.55, -2.03, 1.6), (0.46, 0.1, 0.2), tex_mat("gauges", tex_gauges()), truck, rot=(-25, 0, 0),
         uv={'px': (0, 0, 0.05, 0.05), 'nx': (0, 0, 0.05, 0.05), 'pz': (0, 0, 0.05, 0.05), 'ny': (0, 0, 0.05, 0.05)})
    tube(kit, "steering column", [(0.55, -2.1, 1.2), (0.55, -1.9, 1.38)], 0.035, ink, truck, sides=6)
    wheel_piv = kit.empty("steering wheel", truck, (0.55, -1.88, 1.4), (-35, 0, 0))
    ring = [(0.2 * math.cos(2 * math.pi * k / 10), 0.2 * math.sin(2 * math.pi * k / 10), 0) for k in range(11)]
    tube(kit, "steering wheel rim", ring, 0.022, pink, wheel_piv, sides=5, side=(0, 0, 1), caps=(False, False))
    for k, a in enumerate((90, 210, 330)):
        tbox(kit, f"steering wheel spoke {k}", (0.09 * math.cos(math.radians(a)), 0.09 * math.sin(math.radians(a)), 0),
             (0.18, 0.03, 0.015), steel, wheel_piv, rot=(0, 0, a))
    tube(kit, "steering wheel hub", [(0, 0, -0.02), (0, 0, 0.03)], 0.05, yel, wheel_piv, sides=8)
    for nm, x in (("brake", 0.65), ("gas", 0.43)):
        ped = kit.empty(f"pedal {nm}", truck, (x, -2.12, FL + 0.02), (38, 0, 0))
        tbox(kit, f"pedal {nm}", (0, 0, 0.11), (0.08 if nm == "gas" else 0.12, 0.02, 0.2), steel if nm == "gas" else pink, ped)
    seat = kit.empty("driver seat", truck, (0.55, -1.4, FL))
    t_seat = tex_mat("seat", tex_seat())
    tube(kit, "seat pedestal", [(0, 0, 0), (0, 0, 0.33)], 0.08, ink, seat, sides=6)
    tbox(kit, "seat cushion", (0, 0, 0.4), (0.56, 0.52, 0.14), t_seat, seat)
    tbox(kit, "seat back", (0, 0.25, 0.82), (0.56, 0.13, 0.7), t_seat, seat, rot=(-10, 0, 0))
    tbox(kit, "seat headrest", (0, 0.31, 1.27), (0.32, 0.1, 0.18), t_seat, seat, rot=(-10, 0, 0))
    tube(kit, "gear stick", [(0.02, -1.95, 1.15), (0.0, -1.85, 1.42)], 0.015, steel, truck, sides=4)
    lowball(kit, "gear knob", (0.0, -1.85, 1.44), (0.04, 0.04, 0.04), solid(kit, "knob cherry", RED, 0.6), truck)
    socket(kit, truck, "socket seat", (0.55, -1.4, FL + 0.47))

    # ---- kitchen stations
    def station(fn, nm, loc, rz):
        fn(kit, kit.empty(f"station {nm}", truck, loc, (0, 0, rz)), tag=" " + nm)
    station(build_churn, "churn", (-IW + 0.36, -0.55, FL), 90)
    station(build_bins, "ingredient bins", (-IW + 0.23, 0.48, FL), 90)
    station(build_gun_rack, "gun rack", (-IW + 0.18, 1.6, FL), 90)
    station(build_scoop_counter, "scoop counter", (IW - 0.31, sum(WIN[:2]) / 2, FL), -90)
    station(build_freezer, "freezer rack", (IW - 0.33, 2.22, FL), -90)
    station(build_hopper_gauge, "hopper gauge", (IW, -0.4, FL), -90)

    # ---- ladder to the roof hatch (player climbs facing -X)
    lx, ly0, ly1 = -0.98, HATCH[2] + 0.08, HATCH[3] - 0.08
    for y in (ly0, ly1):
        tbox(kit, f"ladder rail {y:.2f}", (lx, y, (FL + CE) / 2), (0.05, 0.05, CE - FL), yel, truck)
        tube(kit, f"ladder hoop {y:.2f}", [(lx, y, CE), (lx, y, RT + 0.75), (lx + 0.12, y, RT + 0.9), (lx + 0.36, y, RT + 0.9),
                                           (lx + 0.46, y, RT + 0.6), (lx + 0.46, y, RT)], 0.025, yel, roof, sides=4,
             side=(0, 1, 0), caps=(False, False))
    for i in range(7):
        tbox(kit, f"ladder rung {i}", (lx, (ly0 + ly1) / 2, FL + 0.3 + i * 0.29), (0.04, ly1 - ly0, 0.04), yel, truck)
    socket(kit, truck, "socket ladder", (lx + 0.45, (ly0 + ly1) / 2, FL), (0, 0, -90))

    # ---- roof deck: hatch, railing, turret mount, hopper, bell, cone sign, speaker
    hx, hy = (HATCH[0] + HATCH[1]) / 2, (HATCH[2] + HATCH[3]) / 2
    hw, hd = HATCH[1] - HATCH[0], HATCH[3] - HATCH[2]
    for nm, c, s in (("front", (hx, HATCH[2] - 0.04, RT + 0.03), (hw + 0.16, 0.08, 0.06)),
                     ("rear", (hx, HATCH[3] + 0.04, RT + 0.03), (hw + 0.16, 0.08, 0.06)),
                     ("left", (HATCH[0] - 0.04, hy, RT + 0.03), (0.08, hd, 0.06)),
                     ("right", (HATCH[1] + 0.04, hy, RT + 0.03), (0.08, hd, 0.06))):
        tbox(kit, f"hatch frame {nm}", c, s, pink, roof)
    lid = kit.empty("hatch lid", roof, (hx, HATCH[3] + 0.02, RT + 0.07), (-112, 0, 0))
    tbox(kit, "hatch lid", (0, -hd / 2 - 0.02, 0.0), (hw + 0.1, hd + 0.06, 0.05), mint, lid)
    tbox(kit, "hatch lid handle", (0, -hd + 0.02, 0.04), (0.2, 0.04, 0.04), yel, lid)
    socket(kit, roof, "socket hatch", (hx, hy, RT))
    rx, ry0, ry1 = IW - 0.02, YB + 0.03, YR - 0.06
    loop = [(rx, ry0), (rx, ry1), (-rx, ry1), (-rx, ry0), (rx, ry0)]
    for z, nm in ((0.55, "mid"), (1.0, "top")):
        tube(kit, f"railing {nm}", [(x, y, RT + z) for x, y in loop], 0.025, yel, roof, sides=4, side=(0, 0, 1),
             caps=(False, False))
    posts = [(rx, ry0), (rx, ry1), (-rx, ry1), (-rx, ry0), (rx, 1.0), (-rx, 1.0), (0.4, ry1), (-0.1, ry0)]
    for i, (x, y) in enumerate(posts):
        tube(kit, f"railing post {i}", [(x, y, RT), (x, y, RT + 1.02)], 0.03, pink, roof, sides=4)
    turret_mount(kit, kit.empty("turret mount", roof, (TURRET[0], TURRET[1], RT)))
    hop = kit.empty("hopper", roof, UPGRADE['hopper'])
    hopper(kit, hop, big=False)
    build_roof_bell(kit, kit.empty("station roof bell", roof, (-0.85, 1.25, RT), (0, 0, 90)), tag=" roof bell")
    t_waffle, t_swirl = tex_mat("sign waffle", tex_waffle()), tex_mat("swirl", tex_swirl())
    sign = kit.empty("cone sign", roof, (-0.45, -1.65, RT))
    tube(kit, "sign post", [(0, 0, 0), (0, 0, 0.1)], 0.05, pink, sign, sides=6)
    tube(kit, "sign cone", [(0, 0, 0.08), (0, 0, 0.5)], [0.02, 0.24], t_waffle, sign, sides=8, bulge=(0.02, 0))
    tube(kit, "sign swirl", [(0, 0, 0.48), (0, 0, 0.56), (0.01, 0, 0.6), (0.01, 0, 0.67), (-0.01, 0, 0.7), (-0.01, 0, 0.77),
                             (0, 0, 0.84)], [0.27, 0.26, 0.2, 0.19, 0.13, 0.11, 0.025], t_swirl, sign, sides=8)
    lowball(kit, "sign cherry", (0, 0, 0.88), (0.05, 0.05, 0.05), solid(kit, "cherry", RED, 0.6), sign)
    tube(kit, "speaker", [(0.65, -1.7, RT + 0.2), (0.65, -1.85, RT + 0.2), (0.65, -2.05, RT + 0.23)], [0.04, 0.07, 0.15], yel,
         roof, sides=8, side=(1, 0, 0), caps=(True, False))
    tbox(kit, "speaker post", (0.65, -1.7, RT + 0.09), (0.05, 0.05, 0.18), ink, roof)

    # ---- sockets
    socket(kit, side, "socket serving window", (W, wy, wz), (0, 0, 90))
    socket(kit, truck, "socket rear door", (0, YR - WT / 2, FL), (0, 0, 180))
    for nm, p in UPGRADE.items():
        socket(kit, truck, f"socket upgrade {nm}", p)
    # ---- fuel intake in the cab, passenger side (+X) between the dashboard and the bulkhead; built last on purpose
    station(build_fuel_intake, "fuel intake", FUEL_INTAKE, 90)
    return dict(roof=roof, side=side, plow=plow, hopper=hop)


# ---------------------------------------------------------------- upgrades (root = matching truck upgrade socket)
def build_plow2(kit, root):
    t_haz = tex_mat("hazard", tex_hazard(), ext='REPEAT')
    yel, pink, steel, ink = solid(kit, "plow yellow", YEL), solid(kit, "plow pink", PINK), \
        solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "truck dark", INK, 0.1)
    plow = kit.empty("plow", root, (0, 0, 0), (10, 0, 0))
    tip_y, ang, half = -0.3, 24, 1.48
    ends = []
    for sx in (1, -1):
        blade = kit.empty(f"plow wing {sx}", plow, (0, tip_y, 0), (0, 0, sx * ang))
        tbox(kit, f"plow wing {sx}", (sx * half / 2, 0, 0.05), (half, 0.12, 1.1), t_haz, blade, uv={'all': (0, 0, 3, 1.4)})
        tbox(kit, f"plow edge {sx}", (sx * half / 2, -0.03, -0.53), (half, 0.1, 0.08), steel, blade)
        for k in range(4):
            x = sx * (0.2 + k * 0.36)
            tube(kit, f"plow tooth {sx} {k}", [(x, -0.04, -0.52), (x, -0.36, -0.6)], [(0.09, 0.04), 0.004], yel, blade, sides=4,
                 side=(1, 0, 0))
        for k in range(3):
            x = sx * (0.35 + k * 0.45)
            tube(kit, f"plow spike {sx} {k}", [(x, 0.0, 0.58), (x, -0.18, 0.86)], [0.05, 0.003], steel, blade, sides=5)
            tbox(kit, f"plow rib {sx} {k}", (x, 0.12, 0.0), (0.06, 0.14, 1.0), ink, blade)
        ends.append((sx * half * math.cos(math.radians(ang)), tip_y + half * math.sin(math.radians(ang))))
    tube(kit, "plow top bar", [(ends[1][0], ends[1][1], 0.6), (0, tip_y - 0.02, 0.6), (ends[0][0], ends[0][1], 0.6)], 0.06, pink,
         plow, sides=6, side=(0, 0, 1))
    tube(kit, "plow ram", [(0, tip_y - 0.05, 0.05), (0, tip_y - 0.7, 0.0)], [0.14, 0.006], yel, plow, sides=6, side=(0, 0, 1))
    tube(kit, "plow ram collar", [(0, tip_y - 0.02, 0.05), (0, tip_y - 0.1, 0.05)], 0.16, pink, plow, sides=6, side=(0, 0, 1))
    for sx in (1, -1):
        tbox(kit, f"plow arm {sx}", (sx * 0.6, 0.15, 0.0), (0.12, 0.62, 0.14), ink, plow)
    for i, (x, z) in enumerate(((0.5, 0.2), (-0.9, -0.1), (0.95, -0.25))):
        lowball(kit, f"plow goo {i}", (x, tip_y + abs(x) * 0.45 - 0.08, z), (0.14, 0.03, 0.1),
                solid(kit, "goo", ZG, 0.9, shade="#6fd83a"), plow, smooth=False)


def build_spikes(kit, root):
    steel, pink, ink = solid(kit, "steel", STEEL, shade="#a9a2e0"), solid(kit, "spike pink", PINK), solid(kit, "truck dark", INK, 0.1)
    y0, y1 = -0.8 - UPGRADE['spikes'][1], 1.4 - UPGRADE['spikes'][1]
    for sx in (1, -1):
        tbox(kit, f"spike rail {sx}", (sx * (W + 0.04), (y0 + y1) / 2, 0), (0.08, y1 - y0, 0.12), ink, root)
        for k in range(3):
            tbox(kit, f"spike bracket {sx} {k}", (sx * (W + 0.03), y0 + 0.2 + k * (y1 - y0 - 0.4) / 2, -0.12), (0.06, 0.08, 0.16),
                 ink, root)
        n = 8
        for k in range(n):
            y = y0 + 0.15 + k * (y1 - y0 - 0.3) / (n - 1)
            tilt = (k % 2) * 0.08 - 0.04
            tube(kit, f"spike collar {sx} {k}", [(sx * (W + 0.08), y, 0), (sx * (W + 0.13), y, 0)], 0.055, pink, root, sides=6)
            tube(kit, f"spike {sx} {k}", [(sx * (W + 0.13), y, 0), (sx * (W + 0.5), y - 0.06, tilt)], [0.045, 0.003], steel, root,
                 sides=4)


def build_armor(kit, root):
    t = tex_mat("armor", tex_armor())
    bolt, haz = solid(kit, "armor bolt", YEL), tex_mat("hazard", tex_hazard(), ext='REPEAT')
    ws = kit.empty("armor windshield", root, (0, YF - 0.06, 0))
    for k, z in enumerate((1.68, 2.0, 2.32)):
        tbox(kit, f"armor slat {k}", (0, 0, z), (2.12, 0.05, 0.22), t, ws)
    tbox(kit, "armor top band", (0, 0, 2.56), (2.12, 0.06, 0.1), haz, ws, uv={'all': (0, 0, 6, 1)})
    for sx in (1, -1):
        tbox(kit, f"armor strap {sx}", (sx * 1.0, -0.02, 2.05), (0.1, 0.05, 1.05), t, ws)
        for z in (1.62, 2.0, 2.4):
            tbox(kit, f"armor bolt {sx} {z}", (sx * 1.0, -0.05, z), (0.04, 0.02, 0.04), bolt, ws)
    # door plates: pivots sit exactly on the truck door hinges (parent them to the door pivots)
    dw = DOOR[1] - DOOR[0] - 0.01
    for sx in (1, -1):
        nm = '+X' if sx > 0 else '-X'
        p = kit.empty(f"armor cab door {nm}", root, (sx * (W - 0.03), DOOR[0] + 0.005, DOOR[2]))
        tbox(kit, f"armor cab door {nm}", (sx * 0.045, dw / 2, 1.25), (0.03, dw - 0.08, 0.9), t, p)
        tbox(kit, f"armor cab door {nm} slit", (sx * 0.06, dw / 2, 1.38), (0.01, dw - 0.3, 0.05), solid(kit, "slit", INK, 0.05), p)
    rw = RDOOR[1] - RDOOR[0] - 0.01
    p = kit.empty("armor rear door", root, (RDOOR[0] + 0.005, YR - WT / 2, RDOOR[2]))
    tbox(kit, "armor rear door", (rw / 2, 0.045, 1.325), (rw - 0.24, 0.03, 0.66), t, p)
    tbox(kit, "armor rear door slit", (rw / 2, 0.062, 1.42), (rw - 0.44, 0.01, 0.05), solid(kit, "slit", INK, 0.05), p)


def build_turret2(kit, root):
    turret_mount(kit, root)
    steel = solid(kit, "steel", STEEL, shade="#a9a2e0")
    for sx in (1, -1):
        tbox(kit, f"mount brace {sx}", (sx * 0.52, 0, 0.04), (0.12, 0.7, 0.06), steel, root)


def build_big_hopper(kit, root):
    hopper(kit, root, big=True)


def build_engine(kit, root):
    """Engine upgrade: twin exhaust stacks behind the cab doors and a blower poking through the hood."""
    chrome = solid(kit, "chrome", STEEL, shade="#ffffff")
    heat, perf = tex_mat("stack tip", tex_heat()), tex_mat("heat shield", tex_perf())
    ink, pink = solid(kit, "truck dark", INK, 0.1), solid(kit, "blower pink", PINK)
    sy = -1.02 - UPGRADE['engine'][1]
    for sx in (1, -1):
        x = sx * 1.25
        tube(kit, f"stack {sx}", [(sx * 1.0, sy, -0.75), (x, sy, -0.62), (x, sy, 1.9)], 0.075, chrome, root, sides=8,
             caps=(True, False))
        tube(kit, f"stack tip {sx}", [(x, sy, 1.9), (x, sy + 0.02, 2.06), (x + sx * 0.04, sy + 0.1, 2.14)], [0.075, 0.085, 0.095],
             heat, root, sides=8, caps=(False, False), v=(0.6, 1.0))
        tube(kit, f"stack shield {sx}", [(x, sy, 0.2), (x, sy, 1.15)], 0.095, perf, root, sides=8)
        for z in (0.0, 1.35):
            tbox(kit, f"stack bracket {sx} {z}", (sx * 1.18, sy, z), (0.1, 0.05, 0.05), ink, root)
    tbox(kit, "blower base", (0, 0.02, 0.05), (0.5, 0.42, 0.1), ink, root)
    tbox(kit, "blower body", (0, 0.02, 0.2), (0.42, 0.36, 0.22), chrome, root)
    for k in range(5):
        tbox(kit, f"blower fin {k}", (-0.16 + k * 0.08, 0.02, 0.33), (0.02, 0.36, 0.04), chrome, root)
    tbox(kit, "blower scoop", (0, -0.02, 0.42), (0.36, 0.3, 0.14), pink, root, taper=(0.9, 0.8))
    tbox(kit, "blower mouth", (0, -0.17, 0.42), (0.3, 0.01, 0.1), ink, root)
    pul = kit.empty("blower pulley", root, (0, -0.2, 0.15))
    tube(kit, "blower pulley", [(0, 0, 0), (0, -0.04, 0)], 0.08, solid(kit, "pulley yellow", YEL), pul, sides=8, side=(1, 0, 0))


# ---------------------------------------------------------------- fuel intake (the truck runs on ice cream) and tank
FUEL_GLYPHS = dict(FONT, **{':': ("...", ".#.", "...", ".#.", "...")})


def fixed_mat(kit, name, col, emit=0.32, shade=None):
    """solid() look-alike that never touches kit.rand, so adding it to the truck leaves older textures unchanged."""
    cache = kit.__dict__.setdefault("_hmats", {})
    key = ("fixed", name, col, emit)
    if key not in cache:
        cv = Canvas(8, 8, col)
        cv.speckle(random.Random(name), [shade or hex_scale(col, 0.86)], 9)
        cache[key] = tex_mat(name, cv, emit)
    return cache[key]


def fuel_text(c, s, cx, y, col):
    x = cx - text_w(s) // 2
    for ch in s:
        for r, row in enumerate(FUEL_GLYPHS.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.set(x + q, y - r, col)
        x += 4


def tex_fuel_sign():
    c = Canvas(64, 16, RED)
    c.rect(0, 0, 63, 0, DRED); c.rect(0, 15, 63, 15, DRED); c.rect(0, 0, 0, 15, DRED); c.rect(63, 0, 63, 15, DRED)
    fuel_text(c, "FUEL:", 32, 13, YEL)
    fuel_text(c, "ICE CREAM ONLY", 32, 6, WHITE)
    return c


def tex_fuel_dial():
    c = Canvas(32, 32, WHITE)
    for k in range(13):
        a = math.radians(160 - k * 140 / 12 + 0)
        col = RED if k < 3 else YEL if k < 7 else ZG
        for r in (11, 12):
            c.set(round(15.5 + r * math.cos(a + math.radians(-50))), round(15.5 + r * math.sin(a + math.radians(-50))), col)
    for k in range(13):
        a = math.radians(160 - k * 140 / 12)
        c.set(round(15.5 + 13 * math.cos(a)), round(15.5 + 13 * math.sin(a)), INK)
    fuel_text(c, "E", 6, 20, RED)
    fuel_text(c, "F", 26, 20, "#22a04a")
    cone_icon(c, 16, 6, 6, PINK)
    return c


def build_fuel_intake(kit, root, tag=""):
    """Kitchen-style station (front -Y, root on the floor): waffle-cone funnel feeding a chrome pipe into the floor,
    a fuel gauge whose needle pivot points straight up at rest (rotates about the dial normal) and a warning sign.
    Uses no kit.rand: it is installed last in the truck and must not shift any older random texture."""
    chrome = fixed_mat(kit, "intake chrome", STEEL, shade="#ffffff")
    pink, yel, ink = fixed_mat(kit, "intake pink", PINK), fixed_mat(kit, "intake yellow", YEL), fixed_mat(kit, "intake dark", INK, 0.1)
    choc = fixed_mat(kit, "intake fudge", CHOC, 0.28, shade="#4e2812")
    py = 0.04
    tube(kit, "intake floor flange", [(0, py, 0.0), (0, py, 0.035)], [0.13, 0.11], ink, root, sides=8)
    tube(kit, "intake pipe", [(0, py, 0.02), (0, py, 0.82)], 0.052, chrome, root, sides=8)
    tube(kit, "intake pipe band", [(0, py, 0.095), (0, py, 0.145)], 0.06, pink, root, sides=8, caps=(False, False))
    # waffle cone funnel, chocolate-dipped rim, a puddle of melted ice cream inside
    tube(kit, "intake funnel", [(0, py, 0.76), (0, py, 0.95), (0, py, 1.16)], [0.05, 0.13, 0.215],
         tex_mat("intake waffle", tex_waffle(), ext='REPEAT'), root, sides=8, caps=(True, False), v=(0.0, 2.0))
    tube(kit, "intake funnel rim", [(0, py, 1.12), (0, py, 1.165), (0, py, 1.19)], [0.208, 0.226, 0.222], choc, root, sides=8,
         caps=(False, False))
    for k in range(3):
        a = 2 * math.pi * (k + 0.3) / 3
        r0, r1 = 0.212, 0.19
        tube(kit, f"intake fudge drip {k}", [(math.cos(a) * r0, py + math.sin(a) * r0, 1.13),
                                             (math.cos(a) * r1, py + math.sin(a) * r1, 1.09 - 0.03 * (k % 2))],
             [0.016, 0.01], choc, root, sides=4, bulge=(0, 0.008))
    tube(kit, "intake melt", [(0, py, 1.08), (0, py, 1.11), (0, py, 1.13)], [0.18, 0.16, 0.06],
         tex_mat("intake swirl", tex_swirl(), 0.45, ext='REPEAT'), root, sides=8, caps=(False, True))
    # tripod legs from the floor up under the cone
    for k, a in enumerate((215, 325, 90)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tube(kit, f"intake leg {k}", [(ca * 0.22, py + sa * 0.17, 0.0), (ca * 0.12, py + sa * 0.1, 0.96)], 0.018, pink, root, sides=4)
    tube(kit, "intake collar", [(0, py, 0.93), (0, py, 0.98)], 0.14, yel, root, sides=8, caps=(False, False))
    # fuel gauge on a bracket in front of the pipe, dial facing -Y
    gz, gy = 0.6, -0.085
    tbox(kit, "intake gauge bracket", (0, (py + gy) / 2, gz), (0.05, py - gy, 0.05), chrome, root)
    tube(kit, "intake gauge bezel", [(0, gy + 0.03, gz), (0, gy - 0.01, gz)], 0.115, pink, root, sides=10, front=(0, 0, 1))
    dial(kit, "intake gauge face", root, (0, gy - 0.012, gz), 0.098, tex_mat("fuel dial", tex_fuel_dial()), sides=10)
    needle = kit.empty("fuel needle", root, (0, gy - 0.018, gz))
    tbox(kit, "intake needle", (0, 0, 0.04), (0.012, 0.005, 0.09), fixed_mat(kit, "intake needle red", RED, 0.6), needle)
    tbox(kit, "intake gauge hub", (0, gy - 0.022, gz), (0.022, 0.008, 0.022), yel, root)
    # warning sign hung on the pipe
    tbox(kit, "intake sign", (0, py - 0.065, 0.36), (0.34, 0.012, 0.085), tex_mat("fuel sign", tex_fuel_sign()), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.02, 0.02)})
    tbox(kit, "intake sign strap", (0, py - 0.03, 0.36), (0.12, 0.06, 0.02), chrome, root)
    socket(kit, root, f"socket use point{tag}", (0, -0.7, 0))
    socket(kit, root, f"socket load{tag}", (0, py, 1.16))


def tex_tank():
    """64x32 pint-carton wrap for the lying tank: u runs around (u 0.5 faces out), v along the tank."""
    c = Canvas(64, 32, WHITE)
    c.rect(0, 0, 63, 2, PINK); c.rect(0, 29, 63, 31, PINK)
    c.rect(0, 7, 63, 24, MINT); c.rect(0, 7, 63, 7, "#1fbf95"); c.rect(0, 24, 63, 24, "#1fbf95")
    c.rect(16, 10, 47, 21, WHITE)
    fuel_text(c, "SUNDAE", 32, 19, PINK)
    fuel_text(c, "FUEL", 32, 13, "#119a76")
    for cy in (4, 27):
        for x in range(2, 64, 6):
            c.set(x, cy, (YEL, BLUE, PINK, PURP)[(x // 6) % 4])
    return c


def build_sundae_tank(kit, root):
    """Bolt-on auxiliary tank: a giant pint lying along Y on the -X side, chrome straps, saddle brackets to the chassis
    and a cherry fill cap. Root = `socket upgrade tank` at the tank's center."""
    chrome = solid(kit, "chrome", STEEL, shade="#ffffff")
    pink, ink = solid(kit, "tank pink", PINK), solid(kit, "truck dark", INK, 0.1)
    L, r = 0.75, 0.22
    tube(kit, "tank body", [(0, -L, 0), (0, L, 0)], r, tex_mat("tank wrap", tex_tank(), ext='REPEAT'), root, sides=10,
         front=(-1, 0, 0), caps=(False, False))
    for s in (-1, 1):
        tube(kit, f"tank lid {s}", [(0, s * (L - 0.03), 0), (0, s * (L + 0.02), 0), (0, s * (L + 0.035), 0)],
             [r + 0.016, r + 0.012, r * 0.7], pink, root, sides=10, front=(-1, 0, 0), caps=(False, True))
        y = s * 0.42
        tube(kit, f"tank strap {s}", [(0, y - 0.04, 0), (0, y + 0.04, 0)], r + 0.014, chrome, root, sides=10, front=(-1, 0, 0),
             caps=(False, False))
        tbox(kit, f"tank saddle {s}", (0.2, y, -0.18), (0.44, 0.12, 0.05), ink, root)
        tbox(kit, f"tank saddle upright {s}", (0.42, y, -0.09), (0.05, 0.12, 0.2), ink, root)
        tube(kit, f"tank strap bolt {s}", [(0.12, y, -0.2), (0.12, y, -0.15)], 0.022, chrome, root, sides=6)
    tube(kit, "tank filler neck", [(-0.04, 0.3, r - 0.02), (-0.04, 0.3, r + 0.05)], 0.05, chrome, root, sides=8)
    tube(kit, "tank fill cap", [(-0.04, 0.3, r + 0.05), (-0.04, 0.3, r + 0.075)], [0.065, 0.06], pink, root, sides=8)
    lowball(kit, "tank cap cherry", (-0.04, 0.3, r + 0.1), (0.032, 0.032, 0.03), solid(kit, "cherry", RED, 0.6), root)
    tube(kit, "tank fuel line", [(0.15, -0.6, -0.12), (0.3, -0.62, -0.17), (0.42, -0.62, -0.17)], 0.018, chrome, root, sides=5)


# ---------------------------------------------------------------- scenes
def ground(kit, root, size=(9, 13)):
    tbox(kit, "ground", (0, 0, -0.03), (size[0], size[1], 0.06), tex_mat("asphalt", tex_asphalt(kit.rand), emit=0.15, ext='REPEAT'),
         root, uv={'all': (0, 0, size[0] / 2, size[1] / 2)})
    for i in range(4):
        tbox(kit, f"lane dash {i}", (-3.2, -5 + i * 3.2, 0.004), (0.14, 1.4, 0.01), solid(kit, "lane yellow", YEL, 0.5), root)


def hide_tree(ob):
    ob.hide_render = True
    for c in ob.children_recursive:
        c.hide_render = True


def scene_cutaway(kit, root):
    ground(kit, root)
    parts = build_ice_cream_truck(kit, kit.empty("truck", root))
    hide_tree(parts['roof'])
    hide_tree(parts['side'])
    for nm, p, e in (("kitchen glow", (0, 1.0, 2.5), 25), ("cab glow", (0.1, -1.6, 2.4), 15)):
        point_light(kit, root, nm, p, "#fff0dc", e, 5.0, 0.5)


def scene_upgraded(kit, root):
    ground(kit, root)
    t = kit.empty("truck", root)
    parts = build_ice_cream_truck(kit, t)
    hide_tree(parts['plow'])
    hide_tree(parts['hopper'])
    for nm, fn in (("plow", build_plow2), ("spikes", build_spikes), ("armor", build_armor), ("turret2", build_turret2),
                   ("hopper", build_big_hopper), ("engine", build_engine), ("tank", build_sundae_tank)):
        fn(kit, kit.empty(f"upgrade {nm}", t, UPGRADE[nm]))
    for nm, p in (("turret gun", (TURRET[0], TURRET[1], RT + 0.12)), ("turret 2 gun", (UPGRADE['turret2'][0], UPGRADE['turret2'][1], RT + 0.12))):
        build_minigun(kit, kit.empty(nm, t, p, (0, 0, 135 if "2" in nm else -45), (1.2, 1.2, 1.2)))


# ---------------------------------------------------------------- module interface
def named(name, fn):
    def build(kit, root):
        fn(kit, root)
        for ob in kit.col.objects:
            if not ob.name.startswith(name):
                ob.name = f"{name} {ob.name}"
    return (name, build)


ASSETS = [
    named("Ice Cream Truck", build_ice_cream_truck),
    named("Churn", build_churn),
    named("Freezer Rack", build_freezer),
    named("Scoop Counter", build_scoop_counter),
    named("Gun Rack", build_gun_rack),
    named("Ingredient Bins", build_bins),
    named("Hopper Gauge", build_hopper_gauge),
    named("Roof Bell", build_roof_bell),
    named("Upgrade Plow", build_plow2),
    named("Upgrade Side Spikes", build_spikes),
    named("Upgrade Window Armor", build_armor),
    named("Upgrade Second Turret Mount", build_turret2),
    named("Upgrade Big Hopper", build_big_hopper),
    named("Upgrade Exhaust Stacks", build_engine),
    named("Fuel Intake", build_fuel_intake),
    named("Upgrade Sundae Tank", build_sundae_tank),
]
SPACING = 9
SCENES = [
    dict(name="truck cutaway", build=scene_cutaway, cam=((5.6, -2.9, 6.6), (-0.2, 0.15, 0.9), 30), res=(1600, 900)),
    dict(name="truck all upgrades", build=scene_upgraded, cam=((7.0, -7.0, 6.0), (0, -0.1, 1.5), 32), res=(1600, 900)),
]
