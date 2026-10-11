"""Batch 'hot spots' (style H): dense roadside set pieces where a big horde pours out and loot lies around.
Same contract as the stops (h_stops): root at the road edge on the ground, lot x 0..20, y -10..10, entrances facing
the road (-X), an open walkable yard between the road and the buildings.
Sockets (all at ground level): 'socket loot 1..7' (ingredient pickups, >= 1.3 m from anything solid at body height),
'socket crate 1..2' (gun crates, same clearance) and 'socket horde 1..6' (where zombies pour out)."""
from style_H import *
from h_stops import (socket, prefixed, block, pad, holey_wall, frame, prism, face_uv, txt, txt_c, tex_sign_board,
                     tex_grass, tex_concrete, tex_wood, tex_ribbed, tex_stucco, tex_weave, tex_checker, stop_scene)
import h_road as road
from h_road import MB, CUT, cut_mat, place, chainlink_fence

SPACING = 30

BARK = "#7a4a5a"
POLE = "#5b5fc0"


# ================================================================ shared helpers
def ngon(c, r, n, a0=0.0, ry=None):
    return [(c[0] + r * math.cos(a0 + 2 * math.pi * k / n), c[1] + (ry or r) * math.sin(a0 + 2 * math.pi * k / n))
            for k in range(n)]


def ngon_prism(kit, name, parent, poly, z0, z1, mat, s=0.5, top=True):
    mb = MB()
    mb.prism(poly, z0, z1, 0, s, top=top)
    return mb.obj(kit, name, [mat], parent)


def flat(kit, name, parent, poly, z, mat, s=0.5):
    mb = MB()
    mb.up([(x, y, z) for x, y in poly], 0, s)
    return mb.obj(kit, name, [mat], parent)


def hoop(kit, name, parent, c, R, r, mat, segs=16, sides=4, axis='x'):
    """Closed tube loop of radius R around center c, in the plane normal to axis ('x': YZ plane, 'z': XY plane)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    c = Vector(c)
    n1 = Vector((1, 0, 0)) if axis == 'x' else Vector((0, 0, 1))
    rings = []
    for i in range(segs):
        a = 2 * math.pi * i / segs
        p = Vector((0, math.cos(a), math.sin(a))) if axis == 'x' else Vector((math.cos(a), math.sin(a), 0))
        rings.append([bm.verts.new(c + p * R + (p * math.cos(b) + n1 * math.sin(b)) * r)
                      for b in (2 * math.pi * k / sides for k in range(sides))])
    for i in range(segs):
        i2 = (i + 1) % segs
        for k in range(sides):
            k2 = (k + 1) % sides
            f = bm.faces.new((rings[i][k], rings[i][k2], rings[i2][k2], rings[i2][k]))
            for lp, uv in zip(f.loops, ((i / segs, k / sides), (i / segs, k2 / sides), ((i + 1) / segs, k2 / sides),
                                        ((i + 1) / segs, k / sides))):
                lp[uvl].uv = uv
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def string_lights(kit, parent, name, a, b, sag, n, wire, bulbs):
    a, b = Vector(a), Vector(b)
    drop = lambda t: Vector((0, 0, sag * 4 * t * (1 - t)))
    tube(kit, name + " wire", [a.lerp(b, k / 8) - drop(k / 8) for k in range(9)], 0.015, wire, parent, sides=3,
         front=(0, 0, 1), caps=(False, False))
    for i in range(n):
        t = (i + 0.5) / n
        tbox(kit, f"{name} bulb {i}", a.lerp(b, t) - drop(t) - Vector((0, 0, 0.07)), (0.1, 0.1, 0.12),
             bulbs[i % len(bulbs)], parent)


def tex_stripes(c1, c2, w=32, h=8, step=4):
    c = Canvas(w, h, c1)
    for x in range(w):
        if (x // step) % 2:
            c.rect(x, 0, x, h - 1, c2)
    return c


def tex_drips(rand, base, cream, h=16):
    """Base color with a cream band on top that drips down (frosting cornice)."""
    c = Canvas(64, h, base)
    c.speckle(rand, [hex_scale(base, 0.9)], 40)
    top = h * 5 // 8
    c.rect(0, top, 63, h - 1, cream)
    x = 0
    while x < 64:
        w = rand.choice((2, 3, 3, 4))
        ln = rand.randint(0, top - 2)
        c.rect(x, top - ln, x + w - 1, top, cream)
        x += w + rand.choice((1, 2, 3))
    c.rect(0, h - 2, 63, h - 1, hex_scale(cream, 1.08))
    for _ in range(14):
        c.set(rand.randrange(64), rand.randint(top + 1, h - 3), rand.choice((PINK, YEL, BLUE, MINT, PURP)))
    return c


def tex_glowbulbs(bg, cols, w=32, h=8):
    c = Canvas(w, h, bg)
    for i, x in enumerate(range(1, w, 4)):
        c.rect(x, 3, x + 1, 4, cols[i % len(cols)])
    return c


def lamp_post(kit, parent, name, loc, glow, pole, h=3.6, light=True):
    p = kit.empty(name, parent, loc)
    tube(kit, name + " pole", [(0, 0, 0), (0, 0, 0.3), (0, 0, h)], [0.12, 0.07, 0.06], pole, p, sides=6)
    tube(kit, name + " cap", [(0, 0, h + 0.42), (0, 0, h + 0.56)], [0.22, 0.02], pole, p, sides=6)
    lowball(kit, name + " globe", (0, 0, h + 0.22), (0.22, 0.22, 0.24), glow, p)
    if light:
        point_light(kit, p, name + " light", (0, 0, h + 0.1), "#ffe6a0", 260, 9.0, 0.3)
    return p


def bench(kit, parent, name, loc, rz):
    """Park bench, seat facing local -Y."""
    b = kit.empty(name, parent, loc, (0, 0, rz))
    w = solid(kit, "bench wood", "#e8a862", shade="#c47f3a")
    iron = solid(kit, "bench iron", PINK, shade="#d93a85")
    for sx in (1, -1):
        x = sx * 0.78
        tbox(kit, f"{name} leg front {sx}", (x, -0.2, 0.22), (0.07, 0.07, 0.44), iron, b)
        tbox(kit, f"{name} leg back {sx}", (x, 0.2, 0.45), (0.07, 0.07, 0.9), iron, b, rot=(-8, 0, 0))
        tbox(kit, f"{name} arm {sx}", (x, -0.04, 0.64), (0.08, 0.5, 0.06), iron, b)
    for i in range(3):
        tbox(kit, f"{name} slat {i}", (0, -0.18 + i * 0.14, 0.47), (1.8, 0.11, 0.04), w, b)
    for i in range(2):
        tbox(kit, f"{name} back slat {i}", (0, 0.22 + i * 0.025, 0.66 + i * 0.17), (1.8, 0.04, 0.12), w, b, rot=(-8, 0, 0))
    return b


def slide(kit, parent, name, loc, rz, frame_col, chute_col, roof_col):
    """Playground slide: platform with a little roof at the origin, ladder at +Y, chute running down toward local -Y."""
    s = kit.empty(name, parent, loc, (0, 0, rz))
    fr, ch, rf = solid(kit, "slide frame", frame_col), solid(kit, "slide chute", chute_col), solid(kit, "slide roof", roof_col)
    P = 1.6
    for sx in (-0.45, 0.45):
        for sy in (-0.45, 0.45):
            tube(kit, f"{name} post {sx} {sy}", [(sx, sy, 0), (sx, sy, 2.7)], 0.05, fr, s, sides=4)
    tbox(kit, f"{name} deck", (0, 0, P), (1.0, 1.0, 0.08), ch, s)
    tbox(kit, f"{name} roof", (0, 0, 3.0), (1.3, 1.3, 0.6), rf, s, taper=(0.05, 0.05))
    for sx in (-0.5, 0.5):
        tbox(kit, f"{name} guard {sx}", (sx, 0, P + 0.45), (0.05, 0.9, 0.05), fr, s)
        tube(kit, f"{name} ladder rail {sx}", [(sx * 0.8, 0.5, P + 0.6), (sx * 0.8, 1.4, 0)], 0.035, fr, s, sides=4)
    for i in range(4):
        t = (i + 1) / 5
        tbox(kit, f"{name} rung {i}", (0, 0.5 + 0.9 * t, (P + 0.6) * (1 - t)), (0.8, 0.05, 0.05), fr, s)
    L = 2.9
    ang = math.degrees(math.atan2(P - 0.25, L))
    ch_piv = kit.empty(f"{name} chute", s, (0, -0.5, P), (-ang, 0, 0))
    tbox(kit, f"{name} chute bed", (0, -L / 2 - 0.15, -0.02), (0.6, L + 0.3, 0.05), ch, ch_piv)
    for sx in (-0.32, 0.32):
        tbox(kit, f"{name} chute lip {sx}", (sx, -L / 2 - 0.15, 0.1), (0.05, L + 0.3, 0.22), ch, ch_piv)
    return s


def tree(kit, parent, name, loc, kind, h, mats):
    """Low-poly park tree. kind 'blossom' = lumpy pink cherry blossom, 'lolly' = round lollipop crown with cherries."""
    R = kit.rand
    t = kit.empty(name, parent, loc, (0, 0, R.uniform(0, 360)))
    bark, blossom, leafy, cherry = mats
    lean = R.uniform(-0.25, 0.25)
    tube(kit, name + " trunk", [(0, 0, 0), (lean * 0.4, 0, h * 0.35), (lean, 0.1, h * 0.62)], [0.2, 0.14, 0.1], bark, t, sides=6)
    if kind == 'blossom':
        tube(kit, name + " branch", [(lean * 0.4, 0, h * 0.4), (lean + 0.7, 0.2, h * 0.7)], [0.08, 0.05], bark, t, sides=4)
        for i, (dx, dy, dz, r) in enumerate(((lean, 0.1, 0.78, 1.25), (lean + 0.8, 0.3, 0.72, 0.9), (lean - 0.6, -0.4, 0.7, 0.85),
                                             (lean + 0.1, -0.2, 0.95, 0.8))):
            lowball(kit, f"{name} crown {i}", (dx, dy, h * dz), (r, r * 0.95, r * 0.8), blossom, t)
    else:
        lowball(kit, name + " crown", (lean, 0.1, h * 0.8), (1.25, 1.25, 1.2), leafy, t)
        for i in range(5):
            a = R.uniform(0, 2 * math.pi)
            z = h * 0.8 + R.uniform(-0.5, 0.6)
            rr = 1.2 * math.sqrt(max(0.15, 1 - ((z - h * 0.8) / 1.2) ** 2))
            tbox(kit, f"{name} cherry {i}", (lean + rr * math.cos(a), 0.1 + rr * math.sin(a), z), (0.14, 0.14, 0.14), cherry, t)
    return t


# ================================================================ 1. school hot spot
def tex_yard(rand):
    c = Canvas(32, 32, "#54487a")
    c.speckle(rand, ["#5e5288", "#4a3f6c", "#665a90"], 220)
    x, y = 3, 31
    for _ in range(18):
        c.set(x, y, "#3a3058"); x += rand.choice((0, 1)); y -= 1
    return c


def tex_brick(rand):
    c = Canvas(32, 32, "#ffc2dc")
    for row in range(8):
        off = 4 if row % 2 else 0
        for col in range(-1, 4):
            x0 = col * 8 + off
            shade = rand.choice(("#f06a9a", "#f27aa8", "#e85a8e", "#f68ab4"))
            c.rect(max(0, x0 + 1), row * 4 + 1, min(31, x0 + 7), row * 4 + 3, shade)
    c.speckle(rand, ["#d9558a"], 30)
    return c


def tex_window(rand, broken=False):
    c = Canvas(32, 32, WHITE)
    lit = "#ffd36b"
    for x0, x1 in ((2, 14), (17, 29)):
        for y0, y1 in ((2, 13), (16, 29)):
            c.rect(x0, y0, x1, y1, lit if not broken else "#2a1f4a")
    if broken:
        for x0, y0 in ((4, 20), (22, 5), (8, 8)):
            for i in range(6):
                c.set(x0 + i, y0 + (i * 3) % 5, "#c7d4ff")
        c.rect(1, 12, 30, 15, "#d9924a"); c.rect(1, 13, 30, 13, "#8a5226")  # board nailed across
    else:
        cone_icon(c, 7, 4, 6, PINK)
        disc(c, 23, 24, 3, RED); c.set(23, 28, "#3fbf6a"); c.set(24, 28, "#3fbf6a")  # paper apple
        for x, y in ((19, 5), (20, 7), (22, 6), (25, 8), (26, 5)):  # crayon sun
            c.set(x, y, ORNG)
        disc(c, 23, 6, 2, YEL)
        c.rect(4, 19, 12, 26, "#7fd8ff"); c.rect(6, 21, 10, 24, BLUE)  # drawing
    c.rect(0, 0, 31, 1, "#c7c0e8")
    return c


def tex_school_door():
    c = Canvas(16, 32, BLUE)
    c.rect(3, 16, 12, 28, "#ffd36b"); c.rect(3, 22, 12, 22, WHITE)
    c.rect(11, 12, 13, 13, YEL)
    c.rect(0, 0, 15, 0, INK); c.rect(0, 31, 15, 31, WHITE)
    return c


def tex_plaque():
    c = Canvas(128, 28, WHITE)
    c.rect(0, 0, 127, 1, PINK); c.rect(0, 26, 127, 27, PINK)
    txt_c(c, "SPRINKLE HILLS", 64, 24, PINK, 2, shadow=BLUE)
    txt_c(c, "ELEMENTARY", 64, 12, BLUE, 2)
    for cx in (6, 121):
        disc(c, cx, 14, 3, RED); c.set(cx, 18, "#3fbf6a"); c.set(cx + 1, 18, "#3fbf6a")
    return c


def tex_marquee():
    c = Canvas(64, 32, WHITE)
    c.rect(0, 22, 63, 31, PINK)
    txt_c(c, "SPRINKLE HILLS", 32, 29, WHITE)
    c.rect(0, 0, 63, 0, INK); c.rect(0, 0, 0, 31, INK); c.rect(63, 0, 63, 31, INK)
    txt_c(c, "NO SCHOOL", 32, 19, INK)
    txt(c, "TODAY", 10, 11, RED); txt(c, "!!", 32, 11, RED)
    for x in range(4, 60, 9):
        c.rect(x, 2, x + 4, 3, ZG)
    return c


def tex_clock():
    c = Canvas(16, 16, INK)
    disc(c, 8, 8, 7, WHITE)
    for a in range(12):
        c.set(8 + round(6 * math.cos(a * math.pi / 6)), 8 + round(6 * math.sin(a * math.pi / 6)), PINK)
    c.rect(8, 8, 8, 13, INK); c.rect(8, 8, 11, 8, INK)
    return c


def tex_flag():
    c = Canvas(24, 16, PINK)
    c.rect(0, 0, 23, 2, MINT); c.rect(0, 13, 23, 15, MINT)
    cone_icon(c, 12, 3, 6, WHITE)
    return c


def tex_lockers():
    """Locker bank lying on its back: three doors whose long axis runs along u."""
    c = Canvas(32, 24, "#4f7bff")
    for y0 in (0, 8, 16):
        c.rect(0, y0, 31, y0, "#2a3f9e")
        for x in range(2, 7):
            c.rect(x, y0 + 2, x, y0 + 6, "#2a3f9e")  # vents
        c.rect(22, y0 + 3, 24, y0 + 4, STEEL)
        c.set(28, y0 + 4, YEL)
    c.rect(0, 23, 31, 23, "#2a3f9e")
    return c


def tex_tray(rand):
    c = Canvas(16, 12, "#ff8fc8")
    for x0, y0, x1, y1, col in ((1, 6, 9, 10, "#8a4a2a"), (11, 6, 14, 10, "#56d67e"), (1, 1, 5, 4, YEL), (7, 1, 14, 4, RED)):
        c.rect(x0, y0, x1, y1, col)
    c.speckle(rand, [WHITE], 6)
    return c


def tex_hopscotch():
    c = Canvas(20, 64, "#54487a")
    cols = (PINK, YEL, MINT, "#7fd8ff", PINK, YEL, MINT)
    rows = [(0, (5, 14), "1"), (10, (5, 14), "2"), (20, (5, 14), "3"), (30, (0, 9), "4"), (30, (10, 19), "5"),
            (40, (5, 14), "6"), (50, (0, 9), "7"), (50, (10, 19), "8")]
    for i, (y0, (x0, x1), num) in enumerate(rows):
        col = cols[i % len(cols)]
        c.rect(x0, y0, x1, y0, col); c.rect(x0, y0 + 9, x1, y0 + 9, col)
        c.rect(x0, y0, x0, y0 + 9, col); c.rect(x1, y0, x1, y0 + 9, col)
        txt(c, num, (x0 + x1) // 2 - 1, y0 + 7, WHITE)
    for dx in range(-5, 6):  # home arc
        c.set(10 + dx, 60 + round(3 * math.sqrt(max(0, 1 - (dx / 5.5) ** 2))), ORNG)
    return c


def tex_bus(rand):
    c = Canvas(128, 40, "#ffc93a")
    c.speckle(rand, ["#f0b830", "#ffd85a"], 120)
    for y in (6, 12):
        c.rect(0, y, 127, y + 1, INK)
    x = 4
    while x < 124:
        broken = rand.random() < 0.4
        c.rect(x, 16, x + 9, 29, GLASS if not broken else INK)
        if broken:
            for k in range(4):
                c.set(x + rand.randrange(10), 16 + rand.randrange(14), "#c7d4ff")
        else:
            c.dots([(x + 2, 26), (x + 3, 25), (x + 4, 24)], "#6f8cff")
        x += 12
    txt_c(c, "SCHOOL BUS", 64, 37, INK)
    for _ in range(10):
        disc(c, rand.randrange(128), rand.randrange(1, 14), rand.choice((1, 2)), "#c96f3a")
    for hx in (30, 84):  # handprints
        c.rect(hx, 18, hx + 3, 21, ZG); c.dots([(hx, 22), (hx + 1, 23), (hx + 2, 23), (hx + 3, 22)], ZG)
    return c


def tex_cafe_sign():
    return tex_sign_board([("CAFETERIA", 40, 12, PINK, 2, None)], 80, 16, WHITE, MINT)


def backpack(kit, parent, name, loc, rz, col):
    b = kit.empty(name, parent, loc, (0, 0, rz))
    m = solid(kit, f"backpack {col}", col)
    lowball(kit, name, (0, 0, 0.17), (0.17, 0.12, 0.19), m, b, smooth=False)
    tbox(kit, name + " pocket", (0, -0.12, 0.12), (0.22, 0.06, 0.14), solid(kit, "pocket", hex_scale(col, 0.8)), b)
    tbox(kit, name + " zip", (0, -0.155, 0.16), (0.16, 0.012, 0.02), solid(kit, "zip", YEL), b)
    return b


def tray(kit, parent, name, loc, rz, t_tray, flipped=False):
    m = t_tray if not flipped else solid(kit, "tray back", "#ff8fc8")
    tbox(kit, name, (loc[0], loc[1], 0.025), (0.46, 0.34, 0.03), m, parent, rot=(0, 0, rz), uv={'all': (0, 0, 0.1, 0.1), 'pz': (0, 0, 1, 1)})


def flipped_bus(kit, root, loc, rz):
    """School bus upside down on its roof, wheels in the air. Built upright (nose -X) inside a pivot rolled 180 deg."""
    R = kit.rand
    side = tex_mat("bus side", tex_bus(R))
    yel = solid(kit, "bus yellow", "#ffc93a", shade="#f0b830")
    ink = solid(kit, "bus black", INK, 0.1)
    glass = tex_mat("bus glass", tex_car_glass(R))
    bus = kit.empty("school bus", root, (loc[0], loc[1], 3.15), (180, 0, rz))
    tbox(kit, "bus hull", (0.6, 0, 1.75), (8.4, 2.5, 2.5), side, bus,
         uv={'all': (0.5, 0.2, 0.52, 0.22), 'py': (0, 0, 1, 1), 'ny': (0, 0, 1, 1)})
    tbox(kit, "bus roof", (0.6, 0, 3.07), (8.3, 2.3, 0.16), solid(kit, "bus roof", WHITE), bus, taper=(0.98, 0.92))
    under = solid(kit, "bus underside", "#4a4068", shade="#3a3050")
    tbox(kit, "bus chassis", (0.6, 0, 0.42), (8.0, 2.1, 0.2), under, bus)
    tube(kit, "bus drive shaft", [(-3.9, 0, 0.3), (3.4, 0, 0.3)], 0.07, solid(kit, "shaft", STEEL), bus, sides=4, front=(0, 0, 1))
    tbox(kit, "bus fuel tank", (0.4, -0.65, 0.22), (1.3, 0.55, 0.36), solid(kit, "fuel tank", STEEL, shade="#a9a2e0"), bus)
    hood = kit.empty("bus hood", bus, (-3.6, 0, 1.55), (0, 14, 0))
    tbox(kit, "bus hood", (-0.8, 0, -0.5), (1.6, 2.3, 1.1), yel, hood, taper=(0.95, 0.9))
    tbox(kit, "bus windshield", (-3.62, 0, 2.3), (0.05, 2.3, 1.0), glass, bus)
    tbox(kit, "bus grille", (-5.15, 0, 0.75), (0.05, 1.6, 0.7), solid(kit, "grille", STEEL), bus, rot=(0, 18, 6))
    tbox(kit, "bus bumper", (-5.2, 0, 0.45), (0.2, 2.5, 0.24), ink, bus, rot=(0, 0, 9))
    for sy in (1, -1):
        tbox(kit, f"bus flasher {sy}", (-3.5, sy * 0.9, 3.1), (0.1, 0.2, 0.16), solid(kit, "flasher", RED, 1.4), bus)
    tire, hub = solid(kit, "tire", "#2a2238", 0.15, shade="#3a3050"), solid(kit, "bus hub", STEEL)
    for nm, x, y in (("FL", -3.9, -1.05), ("FR", -3.9, 1.05), ("RL", 3.4, -1.05), ("RR", 3.4, 1.05)):
        w = kit.empty(f"bus wheel {nm}", bus, (x, y, 0.45))
        tube(kit, f"bus wheel {nm} tire", [(0, -0.16, 0), (0, 0.16, 0)], 0.45, tire, w, sides=10, front=(0, 0, 1))
        tube(kit, f"bus wheel {nm} hub", [(0, math.copysign(0.15, y), 0), (0, math.copysign(0.18, y), 0)], 0.24, hub, w,
             sides=8, front=(0, 0, 1))
    tube(kit, "bus axle", [(-3.9, -1.0, 0.45), (-3.9, 1.0, 0.45)], 0.07, ink, bus, sides=4, front=(0, 0, 1))
    tube(kit, "bus axle rear", [(3.4, -1.0, 0.45), (3.4, 1.0, 0.45)], 0.07, ink, bus, sides=4, front=(0, 0, 1))
    tube(kit, "bus exhaust", [(4.9, 0.7, 0.4), (3.0, 0.7, 0.4)], 0.06, solid(kit, "exhaust", STEEL), bus, sides=4, front=(0, 0, 1))
    arm = kit.empty("bus stop arm", bus, (-2.8, -1.27, 2.0), (0, 0, 75))
    mb = MB()
    road.plate(mb, (0, -0.45, 0), 0.25, 8, 0.03, 0, 1, math.radians(22.5))
    mb.obj(kit, "bus stop arm", [tex_mat("stop sign", road.tex_stop(R)), solid(kit, "sign back", "#9a94c8")], arm)
    door = kit.empty("bus rear door", bus, (4.82, -0.5, 0.6), (0, 0, -70))
    tbox(kit, "bus rear door", (0, 0.5, 1.1), (0.05, 1.0, 2.0), glass, door)
    return bus


@prefixed
def build_school(kit, root):
    R = kit.rand
    t_yard = tex_mat("schoolyard", tex_yard(R), 0.15, ext='REPEAT')
    t_conc = tex_mat("concrete", tex_concrete(R), 0.18, ext='REPEAT')
    t_brick = tex_mat("pink brick", tex_brick(R), ext='REPEAT')
    t_roof = tex_mat("school roof", tex_ribbed(R, POLE, "#474aa0", 4), ext='REPEAT')
    t_cornice = tex_mat("cornice", tex_drips(R, "#f06a9a", WHITE), ext='REPEAT')
    white, pink, yel, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "yellow", YEL), solid(kit, "dark", INK, 0.1)
    chalk = solid(kit, "paint white", WHITE, 0.45)
    wins = [tex_mat("window", tex_window(R)), tex_mat("window broken", tex_window(R, True))]
    pad(kit, "ground", root, 0, 20, -10, 10, t_yard, tile=4)
    pad(kit, "walkway", root, 0, 10.8, -1.9, 0.1, t_conc, tile=2, z=0.012, th=0.04)

    # painted yard: four-square court, hopscotch, skid marks where the bus left the road
    for i, (x0, x1, y0, y1) in enumerate(((4.6, 7.6, -5.6, -5.5), (4.6, 7.6, -2.65, -2.55), (4.6, 4.7, -5.6, -2.55),
                                          (7.5, 7.6, -5.6, -2.55), (6.05, 6.15, -5.6, -2.55), (4.6, 7.6, -4.12, -4.02))):
        block(kit, f"court line {i}", root, x0, x1, y0, y1, 0.0, 0.016, chalk)
    tbox(kit, "hopscotch", (4.1, 3.2, 0.008), (3.84, 1.2, 0.012), tex_mat("hopscotch", tex_hopscotch(), 0.4), root,
         uv={'all': (0, 0, 0.05, 0.05), 'pz': (0, 0, 1, 1)}, rot=(0, 0, 0))
    skid = solid(kit, "skid", "#2a2140", 0.1)
    for i, (a, b) in enumerate((((0.2, -6.6), (5.4, -7.7)), ((0.2, -8.4), (5.6, -9.1)))):
        L = math.dist(a, b)
        tbox(kit, f"skid mark {i}", ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, 0.006), (L, 0.28, 0.01), skid, root,
             rot=(0, 0, math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))))

    # main building: two storeys of pink brick, frosting cornice, lit classroom windows
    X0, X1, Y0, Y1, H = 12.0, 19.6, -5.4, 3.6, 5.6
    block(kit, "school", root, X0, X1, Y0, Y1, 0, H, t_brick)
    block(kit, "school roof", root, X0 - 0.1, X1 + 0.1, Y0 - 0.1, Y1 + 0.1, H, H + 0.12, t_roof)
    tbox(kit, "cornice front", (X0 - 0.13, (Y0 + Y1) / 2, H - 0.25), (0.26, Y1 - Y0 + 0.5, 0.7), t_cornice, root,
         uv={'all': (0, 0.9, 0.1, 1.0), 'nx': (0, 0, (Y1 - Y0 + 0.5) / 3, 1)})
    for sy, y in ((-1, Y0 - 0.13), (1, Y1 + 0.13)):
        tbox(kit, f"cornice side {sy}", ((X0 + X1) / 2, y, H - 0.25), (X1 - X0, 0.26, 0.7), t_cornice, root,
             uv={'all': (0, 0.9, 0.1, 1.0), 'ny': (0, 0, (X1 - X0) / 3, 1), 'py': (0, 0, (X1 - X0) / 3, 1)})
    block(kit, "plinth", root, X0 - 0.06, X1, Y0 - 0.06, Y1 + 0.06, 0, 0.45, solid(kit, "plinth", "#c7c0e8"))
    for row, (z0, ys) in enumerate(((1.0, (-4.3, -2.9, 1.3, 2.7)), (3.2, (-4.3, -2.9, 1.3, 2.7)))):
        for i, y in enumerate(ys):
            tbox(kit, f"window {row} {i}", (X0 - 0.03, y, z0 + 0.7), (0.06, 1.25, 1.4), wins[(row * 3 + i) % 4 == 2], root,
                 uv=face_uv('nx'))
            tbox(kit, f"window sill {row} {i}", (X0 - 0.08, y, z0 - 0.04), (0.16, 1.4, 0.08), white, root)
    # side windows facing the yard over the bus
    for i, x in enumerate((13.6, 16.0, 18.3)):
        for z0 in (1.0, 3.2):
            tbox(kit, f"side window {i} {z0}", (x, Y0 - 0.03, z0 + 0.7), (1.25, 0.06, 1.4), wins[i == 1], root, uv=face_uv('ny'))
    # entrance: dark doorway, doors swung open (one hanging off its hinge), steps, portico with the name plaque
    tbox(kit, "doorway", (X0 - 0.02, -0.9, 1.25), (0.04, 2.0, 2.5), ink, root)
    frame(kit, "door frame", root, X0, -1.9, 0.1, 0.0, 2.5, white, w=0.12, d=0.1)
    t_door = tex_mat("school door", tex_school_door())
    for nm, y, rz, tilt in (("door L", -1.9, 74, 0), ("door R", 0.1, -112, 9)):
        leaf = kit.empty(f"school {nm}", root, (X0 - 0.06, y, 0.3 if tilt == 0 else 0.22), (tilt, 0, rz))
        tbox(kit, f"school {nm}", (0, 0.5, 1.15), (0.06, 1.0, 2.3), t_door, leaf)
    block(kit, "step 0", root, X0 - 1.3, X0, -2.6, 0.8, 0, 0.15, t_conc)
    block(kit, "step 1", root, X0 - 0.8, X0, -2.6, 0.8, 0.15, 0.3, t_conc)
    for y in (-2.4, 0.6):
        tube(kit, "portico column", [(X0 - 1.1, y, 0.15), (X0 - 1.1, y, 3.0)], 0.17, white, root, sides=8)
    block(kit, "portico", root, X0 - 1.45, X0, -2.85, 1.05, 3.0, 3.7, white)
    tbox(kit, "plaque", (X0 - 1.48, -0.9, 3.35), (0.04, 3.9, 0.7), tex_mat("plaque", tex_plaque(), 0.6), root, uv=face_uv('nx'))
    prism(kit, "pediment", [(-2.85, 3.7), (1.05, 3.7), (-0.9, 4.55)], X0 - 1.45, X0, white, root)
    # SCHOOL sign on the roof edge and the bell tower with a clock behind it
    sign = tex_mat("school sign", tex_sign_board([("SCHOOL", 48, 20, BLUE, 3, PINK)], 96, 24, WHITE, BLUE), 0.8)
    for y in (-2.4, 0.6):
        tbox(kit, "sign post", (X0 + 0.3, y, H + 0.4), (0.1, 0.1, 0.8), ink, root)
    tbox(kit, "school sign", (X0 + 0.22, -0.9, H + 0.75), (0.1, 4.8, 1.2), sign, root, uv=face_uv('nx', rest=(0, 0, 0.02, 0.02)))
    T0, T1 = 14.6, 16.4
    block(kit, "bell tower", root, T0, T1, -1.8, 0.0, H, H + 2.3, t_brick)
    tbox(kit, "clock", (T0 - 0.02, -0.9, H + 1.7), (0.04, 0.95, 0.95), tex_mat("clock", tex_clock(), 0.7), root, uv=face_uv('nx'))
    for x in (T0 + 0.1, T1 - 0.1):
        for y in (-1.7, -0.1):
            tbox(kit, "belfry post", (x, y, H + 2.75), (0.18, 0.18, 0.9), white, root)
    tube(kit, "bell", [(15.5, -0.9, H + 3.05), (15.5, -0.9, H + 2.55)], [0.12, 0.38], solid(kit, "bell", YEL, 0.6), root,
         sides=8)
    tbox(kit, "belfry roof", (15.5, -0.9, H + 3.75), (2.3, 2.3, 1.1), solid(kit, "belfry roof", RED), root, taper=(0.04, 0.04))
    lowball(kit, "roof apple", (15.5, -0.9, H + 4.42), (0.2, 0.2, 0.18), solid(kit, "apple", RED, 0.6), root)
    tube(kit, "apple stem", [(15.5, -0.9, H + 4.55), (15.55, -0.9, H + 4.7)], 0.025, solid(kit, "stem", "#3fbf6a"), root, sides=4)
    block(kit, "ac unit", root, 17.6, 19.0, 1.2, 2.6, H + 0.12, H + 0.8, solid(kit, "ac", STEEL, shade="#a9a2e0"))

    # cafeteria wing: mint stucco, wide doorway with the double doors flung open, lunch tables inside
    CX, CY0, CY1, CH = 12.6, 4.4, 9.6, 3.8
    t_caf = tex_mat("cafeteria wall", tex_stucco(R, MINT), ext='REPEAT')
    DY0, DY1 = 5.8, 8.2
    holey_wall(kit, "cafeteria front", root, CX, CX + 0.25, CY0, CY1, 0, CH, [(DY0, DY1, 0, 2.6)], t_caf)
    block(kit, "cafeteria side S", root, CX, X1, CY0, CY0 + 0.25, 0, CH, t_caf)
    block(kit, "cafeteria side N", root, CX, X1, CY1 - 0.25, CY1, 0, CH, t_caf)
    block(kit, "cafeteria back", root, X1 - 0.25, X1, CY0, CY1, 0, CH, t_caf)
    block(kit, "cafeteria roof", root, CX - 0.15, X1 + 0.1, CY0 - 0.1, CY1 + 0.1, CH, CH + 0.2, t_roof)
    tbox(kit, "cafeteria cornice", (CX - 0.1, (CY0 + CY1) / 2, CH - 0.1), (0.2, CY1 - CY0 + 0.3, 0.5),
         tex_mat("cafe cornice", tex_drips(R, MINT, "#ff8fc8"), ext='REPEAT'), root,
         uv={'all': (0, 0.9, 0.1, 1.0), 'nx': (0, 0, (CY1 - CY0) / 3, 1)})
    block(kit, "cafeteria floor", root, CX + 0.25, X1 - 0.25, CY0 + 0.25, CY1 - 0.25, 0, 0.03,
          tex_mat("checker floor", tex_checker(), 0.3, ext='REPEAT'), tile=1.2)
    frame(kit, "cafeteria door frame", root, CX + 0.02, DY0, DY1, 0.0, 2.6, white, w=0.12, d=0.12)
    tbox(kit, "cafeteria sign", (CX - 0.06, 7.0, 3.12), (0.08, 3.4, 0.68), tex_mat("cafeteria sign", tex_cafe_sign(), 0.7), root,
         uv=face_uv('nx'))
    for nm, y, rz in (("L", DY0, 98), ("R", DY1, -104)):
        leaf = kit.empty(f"cafeteria door {nm}", root, (CX - 0.04, y, 0), (0, 0, rz))
        tbox(kit, f"cafeteria door {nm}", (0, 0.6 if nm == "L" else -0.6, 1.25), (0.06, 1.2, 2.5), t_door, leaf)
    lunch = solid(kit, "lunch table", "#ff8fc8", shade="#e870a8")
    for i, y in enumerate((5.7, 8.3)):
        block(kit, f"lunch table {i}", root, 14.2, 18.6, y - 0.45, y + 0.45, 0.72, 0.78, lunch)
        for sy in (-0.75, 0.75):
            block(kit, f"lunch bench {i} {sy}", root, 14.2, 18.6, y + sy - 0.15, y + sy + 0.15, 0.42, 0.46, lunch)
        for x in (14.5, 18.3):
            block(kit, f"lunch leg {i} {x}", root, x - 0.05, x + 0.05, y - 0.8, y + 0.8, 0.0, 0.72, ink)
    block(kit, "serving counter", root, 18.4, 19.35, 4.9, 9.1, 0, 1.0, solid(kit, "counter", STEEL, shade="#a9a2e0"))
    t_tray = tex_mat("lunch tray", tex_tray(R))
    for i, (x, y, rz) in enumerate(((15.0, 5.6, 10), (16.6, 5.9, -20), (17.4, 8.2, 35), (18.8, 6.0, 0), (18.8, 7.4, 5))):
        tbox(kit, f"table tray {i}", (x, y, 0.8 if x < 18.5 else 1.02), (0.46, 0.34, 0.03), t_tray, root, rot=(0, 0, rz),
             uv={'all': (0, 0, 0.1, 0.1), 'pz': (0, 0, 1, 1)})
    point_light(kit, root, "cafeteria light", (16.2, 7.0, 3.3), "#fff1d0", 380, 8.0, 0.6)
    point_light(kit, root, "cafeteria door glow", (11.4, 7.0, 2.4), "#ffd36b", 260, 7.0, 0.4)
    point_light(kit, root, "entrance light", (10.3, -0.9, 2.8), "#ffe6a0", 320, 8.0, 0.4)
    for y in (-2.1, 0.3):
        lowball(kit, "porch lamp", (X0 - 0.3, y, 2.6), (0.12, 0.12, 0.16), solid(kit, "porch lamp", "#fff1a0", 2.4), root)

    # spilled lunch: trays, food splats, a lunchbox, papers between the cafeteria and the yard
    for i, (x, y, rz, fl) in enumerate(((10.6, 5.2, 20, False), (9.6, 7.9, -35, True), (11.7, 9.0, 60, False),
                                        (8.4, 6.0, 5, False), (10.9, 4.3, -70, True))):
        tray(kit, root, f"spilled tray {i}", (x, y), rz, t_tray, fl)
    for i, (x, y, col) in enumerate(((10.2, 5.6, "#56d67e"), (9.2, 8.3, ORNG), (8.1, 6.4, "#8a4a2a"))):
        splat(kit, f"food splat {i}", (x, y), 0.22, solid(kit, f"food {col}", col, 0.4), root, z=0.012)
    paper = solid(kit, "paper", WHITE, 0.5)
    for i in range(12):
        x, y = R.uniform(2.5, 11.0), R.uniform(-6.0, 9.0)
        tbox(kit, f"paper {i}", (x, y, 0.006), (0.21, 0.3, 0.006), paper, root, rot=(0, 0, R.uniform(0, 180)))
    for i, (x, y, rz, col) in enumerate(((7.6, 2.0, 30, PURP), (4.2, -0.9, -60, BLUE), (11.2, -3.6, 120, MINT),
                                         (2.4, 6.2, 10, ORNG), (8.6, -5.8, 70, PINK))):
        backpack(kit, root, f"backpack {i}", (x, y, 0), rz, col)
    lb = kit.empty("lunchbox", root, (6.3, 0.9, 0), (0, 0, 25))
    tbox(kit, "lunchbox", (0, 0, 0.12), (0.34, 0.14, 0.24), solid(kit, "lunchbox", RED), lb)
    tube(kit, "lunchbox handle", [(-0.08, 0, 0.24), (-0.06, 0, 0.3), (0.06, 0, 0.3), (0.08, 0, 0.24)], 0.015, yel, lb, sides=4,
         front=(0, 0, 1))
    # lockers dragged out and knocked over
    t_lock = tex_mat("lockers", tex_lockers())
    tbox(kit, "locker bank 0", (9.5, 2.4, 0.225), (1.9, 1.2, 0.45), t_lock, root, rot=(0, 0, 18),
         uv={'all': (0, 0, 1, 0.12), 'pz': (0, 0, 1, 1)})
    tbox(kit, "locker bank 1", (11.55, 2.0, 0.98), (1.9, 1.2, 0.45), t_lock, root, rot=(0, -78, 0),
         uv={'all': (0, 0, 1, 0.12), 'pz': (0, 0, 1, 1)})
    lk = kit.empty("locker door", root, (9.5 + 0.2, 2.4 - 0.2, 0.45), (0, 0, 18))
    tbox(kit, "locker door", (0.0, 0.0, 0.2), (0.85, 0.36, 0.03), solid(kit, "locker door", "#4f7bff"), lk, rot=(-70, 0, 0))

    # crashed bus flipped onto its roof, the exposed engine burning
    flipped_bus(kit, root, (11.2, -7.95), -5)
    fire, core = solid(kit, "fire", ORNG, 2.0), solid(kit, "fire core", YEL, 2.4)
    for i, (x, y, h) in enumerate(((6.6, -8.3, 0.9), (7.1, -7.6, 0.7), (6.3, -7.5, 0.6), (7.0, -8.6, 0.5))):
        tbox(kit, f"flame {i}", (x, y, 2.7 + h / 2), (0.4, 0.4, h), fire, root, taper=(0.08, 0.08), rot=(0, 0, 45 + 20 * i))
        tbox(kit, f"flame core {i}", (x, y, 2.7 + h * 0.3), (0.22, 0.22, h * 0.6), core, root, taper=(0.1, 0.1), rot=(0, 0, 20 * i))
    smoke = solid(kit, "smoke", "#5a4a78", 0.2)
    for i, (x, y, z, r) in enumerate(((6.8, -8.0, 4.1, 0.32), (6.5, -7.8, 4.8, 0.42), (6.9, -7.5, 5.6, 0.5))):
        lowball(kit, f"smoke {i}", (x, y, z), (r, r, r * 0.85), smoke, root, smooth=False)
    point_light(kit, root, "bus fire", (5.8, -8.0, 3.4), ORNG, 420, 9.0, 0.5)

    # flagpole by the walkway
    tbox(kit, "flag plinth", (8.9, -3.3, 0.15), (0.8, 0.8, 0.3), t_conc, root)
    tube(kit, "flagpole", [(8.9, -3.3, 0.3), (8.9, -3.3, 8.0)], [0.07, 0.045], solid(kit, "pole steel", STEEL), root, sides=6)
    lowball(kit, "flagpole ball", (8.9, -3.3, 8.08), (0.1, 0.1, 0.1), yel, root)
    fl = kit.empty("flag", root, (8.9, -3.3, 7.8), (0, 0, -8))
    t_flag = tex_mat("flag", tex_flag(), 0.5)
    tbox(kit, "flag a", (0, 0.45, -0.45), (0.03, 0.9, 0.9), t_flag, fl, rot=(0, 0, 8), uv={'all': (0, 0, 0.5, 1)})
    tbox(kit, "flag b", (0.12, 1.32, -0.48), (0.03, 0.9, 0.86), t_flag, fl, rot=(0, 0, -6), uv={'all': (0.5, 0, 1, 1)})

    # marquee sign at the road
    mq = kit.empty("marquee", root, (0.9, -4.2, 0))
    block(kit, "marquee base", mq, -0.3, 0.3, -1.6, 1.6, 0, 0.6, t_brick)
    tbox(kit, "marquee board", (0, 0, 1.4), (0.18, 3.0, 1.5), tex_mat("marquee", tex_marquee(), 0.8), mq,
         uv=face_uv('nx', rest=(0.5, 0.5, 0.52, 0.52)) | {'px': (0, 0, 1, 1)})
    tbox(kit, "marquee cap", (0, 0, 2.2), (0.3, 3.2, 0.12), pink, mq)
    point_light(kit, mq, "marquee light", (-1.2, 0, 2.6), "#fff1d0", 160, 6.0, 0.3)

    # chain-link fences: south edge (flattened where the bus went through) and behind the playground
    for i, x in enumerate((1.85, 4.35)):
        place(kit, chainlink_fence, root, f"fence S {i}", (x, -9.65, 0), 0)
    place(kit, chainlink_fence, root, "fence S flat", (6.9, -9.1, 0.05), rot=(-86, 0, -18))
    for i, x in enumerate((1.85, 4.35, 6.85, 9.35)):
        place(kit, chainlink_fence, root, f"fence N {i}", (x, 9.65, 0), 180)

    # playground corner: slide, rainbow jungle gym
    slide(kit, root, "slide", (3.6, 8.3, 0), -90, PURP, YEL, PINK)
    jg = kit.empty("jungle gym", root, (7.0, 8.4, 0))
    bars = [solid(kit, f"gym {c}", c) for c in (RED, ORNG, YEL, ZG, BLUE, PURP)]
    S = 1.1
    for i, (sx, sy) in enumerate(((-S, -S), (S, -S), (S, S), (-S, S))):
        tube(kit, f"gym post {i}", [(sx, sy, 0), (sx, sy, 2.2)], 0.05, bars[4], jg, sides=4)
    k = 0
    for z in (1.1, 2.2):
        for (ax, ay), (bx, by) in (((-S, -S), (S, -S)), ((S, -S), (S, S)), ((S, S), (-S, S)), ((-S, S), (-S, -S))):
            tube(kit, f"gym bar {k}", [(ax, ay, z), (bx, by, z)], 0.04, bars[k % 6], jg, sides=4, front=(0, 0, 1))
            k += 1
    for i in range(5):
        y = -S + (i + 0.5) * 2 * S / 5
        tube(kit, f"gym rung {i}", [(-S, y, 2.2), (S, y, 2.2)], 0.03, bars[i], jg, sides=4, front=(0, 0, 1))
    lowball(kit, "kickball", (6.9, 5.6, 0.14), (0.14, 0.14, 0.14), solid(kit, "kickball", RED, 0.45), root)
    point_light(kit, root, "yard light", (5.5, 0.0, 5.5), "#c8b4ff", 500, 14.0, 1.0)

    # sockets
    for i, p in enumerate(((10.2, 7.0), (9.3, -1.2), (4.6, 5.4), (3.3, 2.0), (6.6, -3.6), (3.6, -7.0), (10.0, -4.6)), 1):
        socket(kit, root, f"loot {i}", (p[0], p[1], 0))
    socket(kit, root, "crate 1", (2.4, -1.6, 0), (0, 0, 90))
    socket(kit, root, "crate 2", (7.2, 3.8, 0), (0, 0, 70))
    for i, p in enumerate(((15.6, -0.9), (16.2, 7.0), (13.0, -9.7), (5.6, 9.5), (19.2, -7.6), (12.6, 4.0)), 1):
        socket(kit, root, f"horde {i}", (p[0], p[1], 0))


# ================================================================ 2. park hot spot
def tex_path(rand):
    c = Canvas(32, 32, "#d9a6b8")
    c.speckle(rand, ["#c8909f", "#e8bccb", "#bf8496"], 220)
    return c


def tex_water(rand):
    c = Canvas(32, 32, "#3f8cff")
    c.speckle(rand, ["#3580f0", "#4f9cff"], 120)
    for _ in range(10):
        x, y = rand.randrange(32), rand.randrange(32)
        c.rect(x, y, x + rand.randint(2, 4), y, "#8fd0ff")
    for _ in range(5):
        c.set(rand.randrange(32), rand.randrange(32), WHITE)
    return c


def tex_blossom(rand):
    c = Canvas(16, 16, "#ff9fd0")
    c.speckle(rand, ["#ff7fbf", "#ffd0e8", "#fff0f8", "#e8609f"], 110)
    return c


def tex_leafy(rand):
    c = Canvas(16, 16, "#3fcf7e")
    c.speckle(rand, ["#2fae66", "#5fe89a", "#27945a"], 100)
    return c


def tex_bark(rand):
    c = Canvas(8, 16, BARK)
    c.speckle(rand, ["#6a3e4e", "#8a5868"], 30)
    return c


def tex_park_sign():
    c = Canvas(112, 32, WHITE)
    c.rect(0, 0, 111, 1, "#3fbf6a"); c.rect(0, 30, 111, 31, "#3fbf6a")
    c.rect(0, 0, 1, 31, "#3fbf6a"); c.rect(110, 0, 111, 31, "#3fbf6a")
    txt_c(c, "CHERRY SWIRL", 56, 27, RED, 2, shadow=PINK)
    txt_c(c, "PARK", 56, 15, "#22a060", 2)
    for cx in (12, 99):
        disc(c, cx - 3, 6, 3, RED); disc(c, cx + 3, 7, 3, RED)
        c.dots([(cx - 2, 10), (cx - 1, 11), (cx, 12), (cx + 1, 11), (cx + 2, 10)], "#22a060")
    return c


def tex_cart(rand):
    c = Canvas(80, 32, WHITE)
    for x in range(80):
        if (x // 5) % 2:
            c.rect(x, 0, x, 5, "#7fd8ff")
    c.rect(0, 6, 79, 7, PINK)
    frosting(c, rand, 26, 22)
    for i, cx in enumerate((6, 74)):
        cone_icon(c, cx, 9, 6, (PINK, MINT)[i])
    txt_c(c, "ICE CREAM", 40, 21, PINK, 2, shadow=BLUE)
    return c


def tex_cloth():
    c = Canvas(8, 8, WHITE)
    for y in range(8):
        for x in range(8):
            if (x // 2 + y // 2) % 2:
                c.set(x, y, RED)
    return c


def tex_lattice():
    c = Canvas(16, 8, "#3a2340")
    for x in range(16):
        c.set(x, x % 8, WHITE); c.set(x, 7 - x % 8, WHITE)
    c.rect(0, 7, 15, 7, WHITE)
    return c


def tex_rail():
    c = Canvas(16, 8, CUT)
    c.rect(0, 0, 15, 0, WHITE); c.rect(0, 7, 15, 7, WHITE)
    for x in range(0, 16, 4):
        c.rect(x, 0, x, 7, WHITE); c.set(x + 1, 3, WHITE); c.set(x + 1, 4, WHITE)
    return c


def picnic_table(kit, parent, name, loc, rz, t_cloth):
    p = kit.empty(name, parent, loc, (0, 0, rz))
    w = solid(kit, "picnic wood", "#e8a862", shade="#c47f3a")
    leg = solid(kit, "picnic legs", "#c47f3a", shade="#a8662e")
    for i in range(4):
        tbox(kit, f"{name} top {i}", (0, -0.33 + i * 0.22, 0.76), (1.9, 0.2, 0.05), w, p)
    for sy in (1, -1):
        tbox(kit, f"{name} seat {sy}", (0, sy * 0.68, 0.45), (1.9, 0.3, 0.05), w, p)
    for sx in (1, -1):
        for sy in (1, -1):
            tbox(kit, f"{name} leg {sx} {sy}", (sx * 0.7, sy * 0.36, 0.38), (0.08, 0.08, 0.86), leg, p, rot=(sy * -38, 0, 0))
        tbox(kit, f"{name} brace {sx}", (sx * 0.7, 0, 0.42), (0.08, 1.6, 0.06), leg, p)
    tbox(kit, f"{name} cloth", (0.1, 0.0, 0.795), (1.3, 1.0, 0.02), t_cloth, p, rot=(0, 0, 8), uv={'all': (0, 0, 3, 2.4)})
    tbox(kit, f"{name} cloth drape", (0.1, -0.53, 0.66), (1.2, 0.02, 0.28), t_cloth, p, rot=(0, 0, 8), uv={'all': (0, 0, 3, 0.6)})
    return p


def picnic_spill(kit, parent, name, loc, rz, t_weave, food):
    """Overturned basket on the ground with lunch spilling out toward local -Y."""
    s = kit.empty(name, parent, loc, (0, 0, rz))
    bk = kit.empty(f"{name} basket", s, (0, 0, 0.24), (100, 0, 0))
    tube(kit, f"{name} basket", [(0, 0, -0.18), (0, 0, 0.18)], [(0.3, 0.22), (0.34, 0.25)], t_weave, bk, sides=8, caps=(True, False))
    lid = kit.empty(f"{name} lid", s, (0, 0.2, 0.04), (0, 0, 10))
    tbox(kit, f"{name} lid", (0, 0, 0.02), (0.66, 0.48, 0.04), t_weave, lid)
    bread, apple, melon, rind = food
    for i, (x, y, r) in enumerate(((-0.1, -0.45, 20), (0.25, -0.6, -40))):
        tbox(kit, f"{name} sandwich {i}", (x, y, 0.06), (0.22, 0.22, 0.1), bread, s, rot=(0, 0, r), taper=(0.1, 1.0))
    for i, (x, y) in enumerate(((-0.4, -0.7), (0.5, -0.3), (0.1, -0.95))):
        lowball(kit, f"{name} apple {i}", (x, y, 0.08), (0.08, 0.08, 0.08), apple, s)
    prism(kit, f"{name} melon", [(-0.2, 0), (0.2, 0), (0, 0.2)], -0.04, 0.04, melon, s)
    s2 = kit.empty(f"{name} melon slice", s, (0.6, -0.75, 0.0), (0, 0, 70))
    prism(kit, f"{name} melon slice", [(-0.18, 0.0), (0.18, 0.0), (0, 0.18)], -0.03, 0.03, melon, s2)
    tbox(kit, f"{name} rind", (0, 0, 0.01), (0.06, 0.38, 0.03), rind, s2)
    return s


@prefixed
def build_park(kit, root):
    R = kit.rand
    t_grass = tex_mat("grass", tex_grass(R), 0.15, ext='REPEAT')
    t_path = tex_mat("path", tex_path(R), 0.2, ext='REPEAT')
    t_water = tex_mat("pond water", tex_water(R), 0.6, ext='REPEAT')
    t_stone = tex_mat("stone", tex_stucco(R, "#b3a6d9"), ext='REPEAT')
    wood = tex_mat("wood", tex_wood(R), ext='REPEAT')
    white, pink, yel, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "yellow", YEL), solid(kit, "dark", INK, 0.1)
    pole = solid(kit, "lamp pole", POLE, shade="#474aa0")
    glow = solid(kit, "lamp glow", "#fff1a0", 2.4)
    tmats = (tex_mat("bark", tex_bark(R)), tex_mat("blossom", tex_blossom(R), 0.4), tex_mat("leafy", tex_leafy(R), 0.3),
             solid(kit, "cherry", RED, 0.6))
    pad(kit, "ground", root, 0, 20, -10, 10, t_grass, tile=4)

    # paths: entrance walk to the fountain plaza, branches to the gazebo, the bridge and the playground
    mb = MB()
    for pts, w in (([(0.0, 0.0), (4.6, 0.0)], 2.2), ([(8.4, 1.2), (10.6, 2.6), (12.2, 3.2)], 1.6),
                   ([(8.6, -1.4), (10.6, -3.0), (13.4, -3.0)], 1.6), ([(6.6, 2.6), (6.0, 4.6), (5.2, 6.4)], 1.4),
                   ([(11.4, -8.8), (13.2, -9.0), (14.6, -8.8)], 1.4)):
        mb.ribbon(pts, w, 0.014, 0, 0.5)
    mb.up([(x, y, 0.012) for x, y in ngon((7.0, 0.0), 2.9, 12)], 0, 0.5)
    mb.obj(kit, "paths", [t_path], root)

    # fountain: octagonal basin, tiered column topped with a soft-serve swirl, falling water curtain
    F = (7.0, 0.0)
    mbf = MB()
    out, inn = ngon(F, 1.5, 8, math.pi / 8), ngon(F, 1.25, 8, math.pi / 8)
    mbf.prism(out, 0, 0.5, 0, 0.5, top=False)
    for k in range(8):
        k2 = (k + 1) % 8
        mbf.face([(*out[k], 0.5), (*out[k2], 0.5), (*inn[k2], 0.5), (*inn[k], 0.5)], [(0, 0), (1, 0), (1, 0.2), (0, 0.2)], 0)
        mbf.face([(*inn[k], 0.5), (*inn[k2], 0.5), (*inn[k2], 0.32), (*inn[k], 0.32)], [(0, 0), (1, 0), (1, 0.1), (0, 0.1)], 0)
    mbf.up([(x, y, 0.32) for x, y in inn], 1, 0.5)
    mbf.obj(kit, "fountain basin", [t_stone, t_water], root)
    tube(kit, "fountain column", [(F[0], F[1], 0.32), (F[0], F[1], 1.4)], [0.22, 0.16], t_stone, root, sides=8)
    tube(kit, "fountain bowl", [(F[0], F[1], 1.25), (F[0], F[1], 1.45), (F[0], F[1], 1.55)], [0.2, 0.8, 0.85], t_stone, root,
         sides=8, caps=(True, False))
    curtain = solid(kit, "falling water", "#8fe0ff", 0.9)
    tube(kit, "water curtain", [(F[0], F[1], 1.52), (F[0], F[1], 0.9), (F[0], F[1], 0.34)], [0.86, 1.0, 1.12], curtain, root,
         sides=8, caps=(False, False))
    tube(kit, "fountain swirl", [(F[0], F[1], 1.45), (F[0], F[1], 1.65), (F[0], F[1], 1.9), (F[0], F[1], 2.15),
                                 (F[0], F[1], 2.4)], [0.42, 0.4, 0.3, 0.16, 0.03], tex_mat("swirl", tex_swirl()), root, sides=8)
    lowball(kit, "fountain cherry", (F[0], F[1], 2.5), (0.1, 0.1, 0.1), tmats[3], root)
    point_light(kit, root, "fountain glow", (F[0], F[1], 0.9), MINT, 220, 6.0, 0.5)

    # gazebo / bandstand: octagon platform with lattice skirt, white posts and rails, striped roof with drips
    G = (14.9, 3.4)
    ga = kit.empty("gazebo", root, (G[0], G[1], 0))
    poly = ngon((0, 0), 2.8, 8, math.pi / 8)
    ngon_prism(kit, "gazebo platform", ga, poly, 0, 0.36, tex_mat("lattice", tex_lattice(), ext='REPEAT'), s=0.6, top=False)
    flat(kit, "gazebo floor", ga, poly, 0.36, wood, 0.5)
    t_rail = cut_mat(kit, "gazebo rail", tex_rail)
    for k in range(8):
        a = math.pi / 8 + 2 * math.pi * k / 8
        px, py = 2.65 * math.cos(a), 2.65 * math.sin(a)
        tube(kit, f"gazebo post {k}", [(px, py, 0.36), (px, py, 3.0)], 0.08, white, ga, sides=6)
        a2 = a + 2 * math.pi / 8
        qx, qy = 2.65 * math.cos(a2), 2.65 * math.sin(a2)
        if abs(math.atan2((py + qy) / 2, (px + qx) / 2)) > math.radians(150):
            continue  # entrance faces -X
        L = math.dist((px, py), (qx, qy))
        tbox(kit, f"gazebo rail {k}", ((px + qx) / 2, (py + qy) / 2, 0.82), (L, 0.04, 0.8), t_rail, ga,
             rot=(0, 0, math.degrees(math.atan2(qy - py, qx - px))), uv={'all': (0, 0, L / 0.8, 1)})
    roof = tex_mat("gazebo roof", tex_stripes(PINK, WHITE, 32, 8, 2))
    tube(kit, "gazebo roof", [(0, 0, 2.95), (0, 0, 4.7)], [3.25, 0.12], roof, ga, sides=8, smooth=False)
    tube(kit, "gazebo eave", [(0, 0, 2.8), (0, 0, 3.0)], 3.28, white, ga, sides=8, smooth=False, caps=(True, False))
    for k in range(16):
        a = 2 * math.pi * k / 16
        lowball(kit, f"gazebo drip {k}", (3.2 * math.cos(a), 3.2 * math.sin(a), 2.72), (0.18, 0.18, 0.2 + 0.08 * (k % 3)),
                white, ga, smooth=False)
    lowball(kit, "gazebo cherry", (0, 0, 4.95), (0.3, 0.3, 0.28), tmats[3], ga)
    tube(kit, "gazebo stem", [(0, 0, 5.15), (0.15, 0, 5.55)], 0.04, solid(kit, "stem", "#3fbf6a"), ga, sides=4)
    block(kit, "gazebo step", ga, -3.2, -2.5, -1.0, 1.0, 0, 0.18, wood)
    tube(kit, "bass drum", [(0.6, -0.9, 0.86), (0.6, -0.5, 0.86)], 0.5, tex_mat("drum", tex_stripes(RED, WHITE, 16, 4, 2)), ga,
         sides=10, front=(0, 0, 1))
    tube(kit, "music stand", [(-0.4, 0.8, 0.36), (-0.4, 0.8, 1.4)], 0.02, ink, ga, sides=4)
    tbox(kit, "music sheet", (-0.45, 0.8, 1.45), (0.02, 0.4, 0.3), white, ga, rot=(0, -20, 0))
    point_light(kit, ga, "gazebo light", (0, 0, 2.6), "#ffe6a0", 380, 8.0, 0.5)

    # pond with a red arched bridge, rocks, lily pads and a rubber duck
    PC, PRX, PRY = (14.6, -5.9), 3.6, 2.5
    flat(kit, "pond", root, ngon(PC, PRX, 14, 0.1, PRY), 0.02, t_water, 0.25)
    rock = solid(kit, "rock", "#9a8ec4", shade="#7a6ea8")
    for k in range(16):
        a = 2 * math.pi * k / 16 + R.uniform(-0.1, 0.1)
        if abs(math.cos(a)) < 0.25:
            continue  # gaps where the bridge lands
        r = R.uniform(0.22, 0.34)
        lowball(kit, f"pond rock {k}", (PC[0] + (PRX + 0.1) * math.cos(a), PC[1] + (PRY + 0.1) * math.sin(a), r * 0.45),
                (r, r * 0.9, r * 0.6), rock, root, smooth=False)
    pad_m = solid(kit, "lily pad", "#3fbf6a", 0.35)
    for i, (dx, dy) in enumerate(((-2.0, 0.6), (1.6, 1.2), (2.2, -0.8), (-1.4, -1.2))):
        tube(kit, f"lily pad {i}", [(PC[0] + dx, PC[1] + dy, 0.03), (PC[0] + dx, PC[1] + dy, 0.04)], 0.32, pad_m, root, sides=6)
        lowball(kit, f"lily flower {i}", (PC[0] + dx + 0.1, PC[1] + dy, 0.09), (0.08, 0.08, 0.06), pink, root, smooth=False)
    duck = kit.empty("rubber duck", root, (PC[0] - 1.8, PC[1] - 0.6, 0.02), (0, 0, 40))
    lowball(kit, "duck body", (0, 0, 0.14), (0.24, 0.32, 0.17), solid(kit, "duck", YEL, 0.5), duck)
    lowball(kit, "duck head", (0, -0.22, 0.38), (0.14, 0.14, 0.14), solid(kit, "duck", YEL, 0.5), duck)
    tbox(kit, "duck beak", (0, -0.38, 0.36), (0.1, 0.1, 0.04), solid(kit, "beak", ORNG), duck)
    red = solid(kit, "bridge red", RED, shade=DRED)
    BX, N = PC[0], 8
    yb0, yb1 = PC[1] - PRY - 0.6, PC[1] + PRY + 0.9
    arc_pts = [(yb0 + (yb1 - yb0) * k / N, 0.1 + 0.85 * math.sin(math.pi * k / N)) for k in range(N + 1)]
    for k in range(N):
        (ya, za), (yb, zb) = arc_pts[k], arc_pts[k + 1]
        L = math.dist((ya, za), (yb, zb))
        tbox(kit, f"bridge deck {k}", (BX, (ya + yb) / 2, (za + zb) / 2), (1.5, L + 0.02, 0.1), wood, root,
             rot=(math.degrees(math.atan2(zb - za, yb - ya)), 0, 0), uv={'all': (0, 0, 0.75, L / 2)})
    for sx in (-0.72, 0.72):
        tube(kit, f"bridge rail {sx}", [(BX + sx, y, z + 0.85) for y, z in arc_pts[1:-1]], 0.05, red, root, sides=4,
             front=(0, 0, 1))
        for k in range(1, N, 2):
            y, z = arc_pts[k]
            tube(kit, f"bridge post {sx} {k}", [(BX + sx, y, z), (BX + sx, y, z + 0.92)], 0.06, red, root, sides=4)
    for sy, y in ((-1, yb0 + 0.3), (1, yb1 - 0.3)):
        for sx in (-0.72, 0.72):
            tube(kit, f"bridge end post {sy} {sx}", [(BX + sx, y, 0), (BX + sx, y, 1.1)], 0.09, red, root, sides=6)
            lowball(kit, f"bridge knob {sy} {sx}", (BX + sx, y, 1.18), (0.1, 0.1, 0.1), yel, root, smooth=False)

    # cherry blossom and lollipop trees around the edges, petals on the grass
    petals = solid(kit, "petals", "#ff9fd0", 0.35)
    for i, (x, y, kind, h) in enumerate(((2.2, -7.9, 'blossom', 5.0), (7.2, -8.6, 'lolly', 4.6), (17.8, -8.0, 'blossom', 5.4),
                                         (18.2, -0.6, 'lolly', 4.8), (17.6, 7.8, 'blossom', 5.6), (12.4, 8.5, 'lolly', 4.4),
                                         (2.1, 8.0, 'blossom', 4.8))):
        tree(kit, root, f"tree {i}", (x, y, 0), kind, h, tmats)
        if kind == 'blossom':
            splat(kit, f"petals {i}", (x + 0.3, y + 0.2), 1.5, petals, root, lobes=9, z=0.01)

    # playground: swing set and a slide
    sw = kit.empty("swing set", root, (3.6, 6.8, 0))
    frame_m = solid(kit, "swing frame", MINT, shade="#22c79c")
    for sy in (-1.7, 1.7):
        for sx in (-0.9, 0.9):
            tube(kit, f"swing leg {sy} {sx}", [(sx, sy, 0), (0, sy, 2.45)], 0.06, frame_m, sw, sides=4)
    tube(kit, "swing bar", [(0, -1.8, 2.45), (0, 1.8, 2.45)], 0.07, frame_m, sw, sides=6, front=(0, 0, 1))
    chain = solid(kit, "chain", STEEL)
    for i, (y, rx) in enumerate(((-0.8, 0), (0.8, 24))):
        piv = kit.empty(f"swing {i}", sw, (0, y, 2.4), (rx, 0, 0) if i else (0, 18, 0))
        for cy in (-0.22, 0.22):
            tube(kit, f"swing chain {i} {cy}", [(0, cy, 0), (0, cy, -1.9)], 0.015, chain, piv, sides=3)
        tbox(kit, f"swing seat {i}", (0, 0, -1.92), (0.24, 0.52, 0.05), pink, piv)
    slide(kit, root, "slide", (9.2, 8.4, 0), -90, BLUE, YEL, ORNG)

    # picnic tables with overturned baskets and spilled lunch
    t_cloth, t_weave = tex_mat("tablecloth", tex_cloth(), ext='REPEAT'), tex_mat("basket weave", tex_weave())
    food = (solid(kit, "bread", "#ffe0a0"), solid(kit, "apple", RED, 0.5), solid(kit, "melon", "#ff4f6a"), solid(kit, "rind", "#3fbf6a"))
    picnic_table(kit, root, "picnic table A", (4.4, -5.8, 0), 8, t_cloth)
    picnic_spill(kit, root, "spill A", (2.6, -4.7, 0), 120, t_weave, food)
    picnic_table(kit, root, "picnic table B", (10.0, -6.6, 0), -16, t_cloth)
    picnic_spill(kit, root, "spill B", (9.0, -8.6, 0), 220, t_weave, food)
    bench(kit, root, "bench A", (3.6, 2.5, 0), 180)
    bench(kit, root, "bench B", (11.0, 0.6, 0), -150)
    bench(kit, root, "bench C", (16.4, -1.3, 0), 0)

    # abandoned ice-cream cart: lid open, umbrella knocked over, scoops melting on the path
    ct = kit.empty("ice cream cart", root, (10.6, -1.5, 0), (0, 0, 24))
    t_cart = tex_mat("cart side", tex_cart(R))
    tbox(kit, "cart body", (0, 0, 0.85), (1.6, 0.9, 1.0), t_cart, ct,
         uv={'all': (0.0, 0.0, 0.05, 0.05), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1), 'nx': (0, 0, 0.4, 1), 'px': (0.6, 0, 1, 1)})
    lid = kit.empty("cart lid", ct, (0, 0.45, 1.35), (-110, 0, 0))
    tbox(kit, "cart lid", (0, -0.45, 0.03), (1.5, 0.9, 0.06), white, lid)
    for sx in (-0.55, 0.55):
        tube(kit, f"cart wheel {sx}", [(sx, -0.5, 0.32), (sx, -0.42, 0.32)], 0.32, ink, ct, sides=10, front=(0, 0, 1))
    tube(kit, "cart handle", [(0.8, 0.0, 1.0), (1.25, 0.0, 1.15)], 0.03, solid(kit, "steel", STEEL), ct, sides=4)
    tbox(kit, "cart grip", (1.25, 0, 1.15), (0.06, 0.8, 0.06), pink, ct)
    tube(kit, "cart leg", [(0.6, 0.3, 0.35), (0.6, 0.3, 0.0)], 0.04, ink, ct, sides=4)
    tub_cols = (PINK, CHOC, MINT, YEL)
    for i, col in enumerate(tub_cols):
        lowball(kit, f"cart scoop {i}", (-0.55 + i * 0.37, 0.0, 1.38), (0.16, 0.16, 0.12), solid(kit, f"scoop {col}", col, 0.55), ct)
    um = kit.empty("cart umbrella", ct, (-0.6, 0.3, 1.35), (12, -16, 0))
    tube(kit, "umbrella pole", [(0, 0, -0.3), (0, 0, 2.4)], 0.03, white, um, sides=4)
    tube(kit, "umbrella", [(0, 0, 1.95), (0, 0, 2.45)], [1.3, 0.04], tex_mat("umbrella", tex_stripes(PINK, WHITE, 32, 8, 4)), um,
         sides=8, smooth=False)
    for i, (x, y, col) in enumerate(((9.6, -2.6, PINK), (9.2, -1.8, MINT), (11.2, -2.9, CHOC))):
        splat(kit, f"melt {i}", (x, y), 0.32, solid(kit, f"melt {col}", col, 0.5), root, z=0.02)
        lowball(kit, f"dropped scoop {i}", (x + 0.05, y, 0.08), (0.13, 0.13, 0.09), solid(kit, f"scoop {col}", col, 0.55), root)
    point_light(kit, ct, "cart glow", (0, -1.0, 1.4), PINK, 120, 5.0, 0.3)

    # lamp posts along the paths, park sign at the road, hedges along the road edge
    for i, (x, y) in enumerate(((3.4, -1.9), (3.0, 1.7), (12.0, 6.2), (12.2, -4.0))):
        lamp_post(kit, root, f"lamp {i}", (x, y, 0), glow, pole)
    sg = kit.empty("park sign", root, (0.9, -4.4, 0))
    block(kit, "sign base", sg, -0.35, 0.35, -1.9, 1.9, 0, 0.55, t_stone)
    for y in (-1.6, 1.6):
        tbox(kit, "sign post", (0, y, 1.2), (0.14, 0.14, 1.4), wood, sg)
    tbox(kit, "sign board", (0, 0, 1.35), (0.12, 3.6, 1.1), tex_mat("park sign", tex_park_sign(), 0.7), sg,
         uv=face_uv('nx', rest=(0.5, 0.5, 0.51, 0.51)) | {'px': (0, 0, 1, 1)})
    for i, dy in enumerate((-0.25, 0.25)):
        lowball(kit, f"sign cherry {i}", (0, dy, 2.15 + 0.05 * i), (0.24, 0.24, 0.24), tmats[3], sg)
        tube(kit, f"sign cherry stem {i}", [(0, dy, 2.35), (0, dy * 0.3, 2.75)], 0.03, solid(kit, "stem", "#3fbf6a"), sg, sides=4)
    point_light(kit, sg, "sign light", (-1.2, 0, 2.4), "#fff1d0", 150, 6.0, 0.3)
    hedge = solid(kit, "hedge", "#2fae66", shade="#27945a")
    for i, (y0, y1) in enumerate(((-9.8, -6.8), (5.4, 7.6))):
        tbox(kit, f"hedge {i}", (0.7, (y0 + y1) / 2, 0.4), (0.8, y1 - y0, 0.8), hedge, root, taper=(0.85, 0.95))
    tube(kit, "trash can", [(5.6, -1.6, 0), (5.6, -1.6, 0.85)], 0.28, solid(kit, "trash can", "#3fbf6a"), root, sides=8)

    # sockets
    for i, p in enumerate(((8.6, -3.4), (4.6, -3.4), (12.2, -8.6), (6.8, 3.4), (10.6, 3.6), (6.2, 6.4), (17.9, -2.8)), 1):
        socket(kit, root, f"loot {i}", (p[0], p[1], 0))
    socket(kit, root, "crate 1", (1.9, -1.0, 0), (0, 0, 90))
    socket(kit, root, "crate 2", (13.4, -0.8, 0), (0, 0, 60))
    for i, p in enumerate(((14.9, 3.4), (2.2, -7.9), (18.2, -0.6), (17.6, 7.8), (12.4, 8.5), (18.6, -5.6)), 1):
        socket(kit, root, f"horde {i}", (p[0], p[1], 0))


# ================================================================ 3. fairground hot spot
def tex_fair_dirt(rand):
    c = Canvas(32, 32, "#b98a74")
    c.speckle(rand, ["#a87a66", "#c99a82", "#9a6c5a"], 240)
    for _ in range(14):
        c.set(rand.randrange(32), rand.randrange(32), rand.choice((PINK, YEL, MINT, "#7fd8ff", WHITE)))
    return c


def tex_arch_sign():
    c = Canvas(128, 40, PINK)
    c.rect(0, 0, 127, 2, PURP); c.rect(0, 37, 127, 39, PURP); c.rect(0, 0, 2, 39, PURP); c.rect(125, 0, 127, 39, PURP)
    for i, x in enumerate(range(4, 124, 6)):
        col = YEL if i % 2 else WHITE
        c.rect(x, 1, x + 1, 1, col); c.rect(x, 38, x + 1, 38, col)
    txt_c(c, "SUNDAE FUNDAY", 64, 34, WHITE, 2, shadow=BLUE)
    txt_c(c, "FAIR", 64, 21, YEL, 3, shadow=PURP)
    for cx in (16, 111):
        cone_icon(c, cx, 5, 8, MINT)
    return c


def tex_ticket():
    c = Canvas(32, 48, WHITE)
    for x in range(32):
        if (x // 4) % 2:
            c.rect(x, 0, x, 13, RED)
    c.rect(0, 14, 31, 15, YEL)
    c.rect(4, 18, 27, 36, INK)
    c.rect(9, 22, 22, 27, WHITE); c.rect(10, 23, 21, 26, RED)
    c.rect(4, 37, 27, 38, YEL)
    c.rect(0, 40, 31, 47, RED)
    txt_c(c, "TICKETS", 16, 46, WHITE)
    return c


def tex_booth_sign(word, bg, fg):
    c = Canvas(80, 16, bg)
    c.rect(0, 0, 79, 1, YEL); c.rect(0, 14, 79, 15, YEL)
    txt_c(c, word, 40, 12, fg, 2, shadow=INK)
    return c


def tex_board(rand):
    """Rounding board around the carousel canopy: pink band, bulbs and little mirrors."""
    c = Canvas(64, 8, PINK)
    c.rect(0, 0, 63, 0, YEL); c.rect(0, 7, 63, 7, YEL)
    for x in range(2, 64, 8):
        c.rect(x, 2, x + 3, 5, "#c7f0ff"); c.set(x + 1, 4, WHITE)
        c.rect(x + 5, 3, x + 6, 4, YEL)
    return c


def tex_hub():
    c = Canvas(16, 16, PINK)
    disc(c, 8, 8, 6, YEL); disc(c, 8, 8, 3, WHITE)
    for a in range(8):
        c.set(8 + round(7 * math.cos(a * math.pi / 4)), 8 + round(7 * math.sin(a * math.pi / 4)), WHITE)
    return c


def booth_tent(kit, parent, name, loc, rz, cols, word, prize):
    """Striped game booth, open front (local -Y) with a counter; prize kind 'bears', 'bottles' or 'ducks'."""
    R = kit.rand
    c1, c2 = cols
    b = kit.empty(name, parent, loc, (0, 0, rz))
    t_wall = tex_mat(f"{name} stripes", tex_stripes(c1, WHITE, 32, 8, 4), ext='REPEAT')
    W, D, H = 2.8, 2.2, 2.3
    block(kit, f"{name} back", b, -W / 2, W / 2, D / 2 - 0.08, D / 2, 0, H, t_wall, tile=2)
    for sx in (-1, 1):
        block(kit, f"{name} side {sx}", b, sx * W / 2 - 0.04, sx * W / 2 + 0.04, -D / 2, D / 2, 0, H, t_wall, tile=2)
    block(kit, f"{name} counter", b, -W / 2, W / 2, -D / 2, -D / 2 + 0.4, 0, 1.0, t_wall, tile=2)
    block(kit, f"{name} counter top", b, -W / 2 - 0.05, W / 2 + 0.05, -D / 2 - 0.05, -D / 2 + 0.45, 1.0, 1.06, solid(kit, "counter top", c2))
    tbox(kit, f"{name} roof", (0, 0, H + 0.6), (W + 0.4, D + 0.4, 1.2), tex_mat(f"{name} roof", tex_stripes(c1, WHITE, 32, 8, 4)), b,
         taper=(0.04, 0.04))
    lowball(kit, f"{name} pennant ball", (0, 0, H + 1.28), (0.12, 0.12, 0.12), solid(kit, "gold", YEL, 0.7), b, smooth=False)
    tbox(kit, f"{name} pennant", (0.25, 0, H + 1.6), (0.5, 0.02, 0.3), solid(kit, f"pennant {c2}", c2), b, taper=(0.1, 1))
    tube(kit, f"{name} pennant pole", [(0, 0, H + 1.2), (0, 0, H + 1.8)], 0.02, solid(kit, "gold", YEL, 0.7), b, sides=3)
    for i in range(9):
        x = -W / 2 - 0.1 + i * (W + 0.2) / 8
        tbox(kit, f"{name} scallop {i}", (x, -D / 2 - 0.2, H - 0.1), (0.34, 0.04, 0.3), solid(kit, f"scallop {c1}", c1) if i % 2
             else solid(kit, "white", WHITE), b, rot=(0, 180, 0), taper=(0.25, 1.0))
    tbox(kit, f"{name} sign", (0, -D / 2 - 0.26, H + 0.45), (2.4, 0.06, 0.48), tex_mat(f"{name} sign", tex_booth_sign(word, c2, WHITE), 0.8),
         b, uv=face_uv('ny'))
    bulb = solid(kit, "bulb", "#fff1a0", 2.4)
    for i in range(6):
        tbox(kit, f"{name} bulb {i}", (-W / 2 + 0.2 + i * (W - 0.4) / 5, -D / 2 - 0.24, H + 0.12), (0.08, 0.08, 0.1), bulb, b)
    if prize == 'bears':
        for i in range(5):
            col = (PINK, MINT, "#7fd8ff", YEL, PURP)[i]
            m = solid(kit, f"bear {col}", col)
            x, z = -1.1 + i * 0.55, 1.65 + 0.15 * (i % 2)
            lowball(kit, f"{name} bear {i}", (x, D / 2 - 0.25, z), (0.18, 0.12, 0.22), m, b)
            lowball(kit, f"{name} bear head {i}", (x, D / 2 - 0.28, z + 0.3), (0.13, 0.11, 0.12), m, b)
    elif prize == 'bottles':
        block(kit, f"{name} shelf", b, -1.0, 1.0, 0.1, 0.6, 0.0, 0.9, solid(kit, "shelf", WHITE))
        for i in range(12):
            x, y = -0.85 + (i % 6) * 0.34, 0.22 + (i // 6) * 0.26
            tube(kit, f"{name} bottle {i}", [(x, y, 0.9), (x, y, 1.12), (x, y, 1.2)], [0.06, 0.06, 0.025],
                 solid(kit, "bottle", (MINT, "#7fd8ff")[i % 2], 0.6), b, sides=4)
        for i in range(3):
            ring_mesh(kit, f"{name} ring {i}", 0.08, 0.12, solid(kit, "toss ring", (YEL, PINK, ZG)[i], 0.8), b,
                      (-0.6 + i * 0.5, -0.9, 1.07), segs=8)
    else:
        block(kit, f"{name} pool", b, -1.2, 1.2, -0.6, 0.6, 0.0, 0.85, solid(kit, "pool", BLUE))
        block(kit, f"{name} pool water", b, -1.1, 1.1, -0.5, 0.5, 0.85, 0.87, solid(kit, "pool water", "#7fd8ff", 0.7))
        for i in range(6):
            x, y = -0.85 + i * 0.34, R.uniform(-0.3, 0.3)
            lowball(kit, f"{name} duck {i}", (x, y, 0.95), (0.09, 0.12, 0.08), solid(kit, "duck", YEL, 0.5), b, smooth=False)
            lowball(kit, f"{name} duck head {i}", (x, y - 0.08, 1.06), (0.06, 0.06, 0.06), solid(kit, "duck", YEL, 0.5), b,
                    smooth=False)
    point_light(kit, b, f"{name} light", (0, -0.4, 2.0), "#ffe6a0", 160, 5.0, 0.3)
    return b


def horse(kit, parent, name, loc, rz, col, dz):
    h = kit.empty(name, parent, loc, (0, 0, rz))
    m = solid(kit, f"horse {col}", col)
    dark = solid(kit, f"horse mane {col}", hex_scale(col, 0.7))
    z = 1.15 + dz
    tbox(kit, name + " body", (0, 0, z), (0.26, 0.8, 0.32), m, h, taper=(0.9, 1.0))
    tbox(kit, name + " neck", (0, -0.42, z + 0.25), (0.2, 0.22, 0.45), m, h, rot=(-28, 0, 0))
    tbox(kit, name + " head", (0, -0.6, z + 0.45), (0.18, 0.38, 0.2), m, h, rot=(18, 0, 0))
    tbox(kit, name + " mane", (0, -0.36, z + 0.38), (0.06, 0.2, 0.42), dark, h, rot=(-28, 0, 0))
    for sx in (-0.08, 0.08):
        tbox(kit, f"{name} front leg {sx}", (sx, -0.42, z - 0.22), (0.07, 0.07, 0.42), m, h, rot=(-55, 0, 0))
        tbox(kit, f"{name} back leg {sx}", (sx, 0.36, z - 0.3), (0.07, 0.07, 0.45), m, h, rot=(22, 0, 0))
    tube(kit, name + " tail", [(0, 0.4, z + 0.05), (0, 0.6, z - 0.15), (0, 0.62, z - 0.4)], [0.05, 0.06, 0.03], dark, h, sides=4)
    tbox(kit, name + " saddle", (0, 0.02, z + 0.18), (0.32, 0.32, 0.06), solid(kit, "saddle", YEL, 0.5), h)
    return h


@prefixed
def build_fair(kit, root):
    R = kit.rand
    t_dirt = tex_mat("fair dirt", tex_fair_dirt(R), 0.18, ext='REPEAT')
    wood = tex_mat("boardwalk", tex_wood(R), ext='REPEAT')
    white, pink, yel, ink = solid(kit, "white", WHITE), solid(kit, "pink", PINK), solid(kit, "yellow", YEL), solid(kit, "dark", INK, 0.1)
    gold = solid(kit, "gold", YEL, 0.7)
    steel = solid(kit, "steel", STEEL, shade="#a9a2e0")
    bulbs = [solid(kit, f"bulb {c}", c, 2.4) for c in ("#fff1a0", "#ff8fc8", "#8ff9de", "#9fd0ff")]
    wire = solid(kit, "wire", INK, 0.1)
    t_swirl = tex_mat("swirl", tex_swirl(), ext='REPEAT')
    t_waffle = tex_mat("waffle", tex_waffle())
    pad(kit, "ground", root, 0, 20, -10, 10, t_dirt, tile=4)
    pad(kit, "midway", root, 0, 14.0, -1.7, 1.7, wood, tile=2, z=0.02, th=0.06)

    # entrance arch over the midway
    for sy in (-1, 1):
        y = sy * 3.3
        tube(kit, f"arch column {sy}", [(1.2, y, 0), (1.2, y, 5.0)], 0.32, t_swirl, root, sides=8)
        tube(kit, f"arch cone {sy}", [(1.2, y, 5.0), (1.2, y, 6.0)], [0.08, 0.5], t_waffle, root, sides=8)
        lowball(kit, f"arch scoop {sy}", (1.2, y, 6.25), (0.55, 0.55, 0.45), solid(kit, f"arch scoop {sy}", PINK if sy > 0 else MINT, 0.6), root)
        lowball(kit, f"arch cherry {sy}", (1.2, y, 6.8), (0.14, 0.14, 0.14), solid(kit, "cherry", RED, 0.6), root)
    tbox(kit, "arch sign", (1.2, 0, 5.1), (0.24, 6.0, 1.9), tex_mat("arch sign", tex_arch_sign(), 1.0), root,
         uv=face_uv('nx', rest=(0.5, 0.0, 0.52, 0.02)) | {'px': (0, 0, 1, 1)})
    string_lights(kit, root, "arch lights", (1.0, -3.0, 6.0), (1.0, 3.0, 6.0), -0.9, 13, wire, bulbs)
    point_light(kit, root, "arch glow", (-0.6, 0, 5.0), PINK, 500, 11.0, 1.0)

    # ticket booth beside the arch
    tk = kit.empty("ticket booth", root, (2.8, -6.0, 0))
    tbox(kit, "ticket booth", (0, 0, 1.15), (1.6, 1.6, 2.3), tex_mat("ticket booth", tex_ticket()), tk,
         uv={'all': (0, 0, 1, 0.28), 'nx': (0, 0, 1, 1)})
    tbox(kit, "ticket roof", (0, 0, 2.75), (2.1, 2.1, 0.9), tex_mat("ticket roof", tex_stripes(RED, WHITE, 32, 8, 4)), tk, taper=(0.05, 0.05))
    lowball(kit, "ticket ball", (0, 0, 3.3), (0.15, 0.15, 0.15), gold, tk, smooth=False)
    tbox(kit, "ticket ledge", (-0.88, 0, 1.0), (0.2, 1.2, 0.06), yel, tk)
    tkt = solid(kit, "ticket", "#ff8fc8", 0.5)
    for i in range(10):
        tbox(kit, f"ticket {i}", (R.uniform(-1.6, -0.6), R.uniform(-1.4, 1.4), 0.03), (0.16, 0.08, 0.005), tkt, tk,
             rot=(0, 0, R.uniform(0, 180)))
    tube(kit, "ticket roll", [(-1.0, 0.9, 0.08), (-1.0, 1.15, 0.08)], 0.08, tkt, tk, sides=6, front=(0, 0, 1))

    # carousel: rotor with horses on brass poles, striped canopy and mirrored rounding board
    C = (8.6, -5.8)
    car = kit.empty("carousel", root, (C[0], C[1], 0))
    ngon_prism(kit, "carousel base", car, ngon((0, 0), 3.0, 12), 0, 0.32, tex_mat("carousel base", tex_stripes(PURP, LAV, 32, 8, 2), ext='REPEAT'),
               s=0.5, top=False)
    rot = kit.empty("carousel rotor", car, (0, 0, 0), (0, 0, 15))
    flat(kit, "carousel floor", rot, ngon((0, 0), 2.95, 12), 0.32, wood, 0.5)
    tube(kit, "carousel column", [(0, 0, 0.32), (0, 0, 3.2)], 0.5, tex_mat("carousel column", tex_board(R), ext='REPEAT'), rot,
         sides=8)
    tube(kit, "carousel canopy", [(0, 0, 3.15), (0, 0, 4.6)], [3.3, 0.25], tex_mat("carousel canopy", tex_stripes(PINK, WHITE, 24, 8, 2)),
         rot, sides=12, smooth=False)
    tube(kit, "carousel board", [(0, 0, 2.75), (0, 0, 3.2)], 3.3, tex_mat("carousel board", tex_board(R), 0.7, ext='REPEAT'), rot,
         sides=12, smooth=False, caps=(True, False))
    for k in range(12):
        a = 2 * math.pi * (k + 0.5) / 12
        lowball(kit, f"carousel scallop {k}", (3.2 * math.cos(a), 3.2 * math.sin(a), 2.62), (0.42, 0.42, 0.2),
                pink if k % 2 else white, rot, smooth=False)
    lowball(kit, "carousel top scoop", (0, 0, 4.75), (0.5, 0.5, 0.4), solid(kit, "top scoop", MINT, 0.6), rot)
    lowball(kit, "carousel top cherry", (0, 0, 5.2), (0.16, 0.16, 0.16), solid(kit, "cherry", RED, 0.6), rot)
    for k in range(6):
        a = 2 * math.pi * k / 6
        px, py = 2.2 * math.cos(a), 2.2 * math.sin(a)
        tube(kit, f"carousel pole {k}", [(px, py, 0.32), (px, py, 2.75)], 0.035, gold, rot, sides=4)
        horse(kit, rot, f"horse {k}", (px, py, 0), math.degrees(a) + 180, (WHITE, PINK, MINT, "#7fd8ff", YEL, LAV)[k],
              0.18 if k % 2 else -0.08)
    point_light(kit, car, "carousel light", (0, 0, 2.4), "#ffe6a0", 450, 9.0, 0.8)

    # game booths along the north side of the midway
    booth_tent(kit, root, "booth ring toss", (3.4, 7.6, 0), 0, (RED, RED), "RING TOSS", 'bottles')
    booth_tent(kit, root, "booth scoop shot", (6.9, 7.8, 0), 0, (BLUE, BLUE), "SCOOP SHOT", 'bears')
    booth_tent(kit, root, "booth duck pond", (10.4, 7.6, 0), 0, ("#22c79c", PURP), "DUCK POND", 'ducks')

    # giant inflatable cone, tethered, sagging to one side
    ic = kit.empty("inflatable cone", root, (13.4, 8.2, 0), (0, -7, 0))
    tube(kit, "inflatable waffle", [(0, 0, 0.0), (0, 0, 0.3), (0, 0, 3.0)], [0.25, 0.32, 1.15], t_waffle, ic, sides=10, bulge=(0, 0))
    lowball(kit, "inflatable scoop 1", (0, 0, 3.55), (1.3, 1.3, 0.95), solid(kit, "inflatable pink", "#ff8fc8", 0.55), ic)
    lowball(kit, "inflatable scoop 2", (0.1, 0, 4.85), (1.0, 1.0, 0.8), solid(kit, "inflatable mint", MINT, 0.55), ic)
    lowball(kit, "inflatable cherry", (0.1, 0, 5.85), (0.32, 0.32, 0.32), solid(kit, "cherry", RED, 0.6), ic)
    rope = solid(kit, "rope", "#ffe58a")
    for i, (dx, dy) in enumerate(((-1.6, -1.2), (1.4, -1.4), (0.2, 1.6))):
        tube(kit, f"tether {i}", [(dx * 0.6, dy * 0.6, 3.3), (dx, dy, 0.0)], 0.02, rope, ic, sides=3)

    # ferris wheel: the landmark. Rotor (axis X) carries the rims, spokes and eight sundae-cup gondolas on pivots.
    FW = (16.9, 3.6)
    Rw, Hh = 5.0, 6.7
    fw = kit.empty("ferris wheel", root, (FW[0], FW[1], 0))
    frame_m = solid(kit, "wheel frame", WHITE, shade="#d0c8f0")
    leg = solid(kit, "wheel leg", PINK, shade="#d93a85")
    for sx in (-1.15, 1.15):
        for sy in (-1, 1):
            tube(kit, f"wheel leg {sx} {sy}", [(sx, sy * 3.4, 0), (sx * 0.85, 0, Hh)], 0.15, leg, fw, sides=6)
        tube(kit, f"wheel brace {sx}", [(sx, -1.7, Hh / 2), (sx, 1.7, Hh / 2)], 0.08, leg, fw, sides=4, front=(0, 0, 1))
    block(kit, "wheel platform", fw, -1.8, 1.8, -1.9, 1.9, 0, 0.3, wood)
    block(kit, "wheel step", fw, -2.5, -1.8, -1.0, 1.0, 0, 0.15, wood)
    tube(kit, "wheel axle", [(-1.25, 0, Hh), (1.25, 0, Hh)], 0.22, steel, fw, sides=8, front=(0, 0, 1))
    wr = kit.empty("ferris wheel rotor", fw, (0, 0, Hh), (12, 0, 0))
    for sx in (-0.6, 0.6):
        hoop(kit, f"wheel rim {sx}", wr, (sx, 0, 0), Rw, 0.09, frame_m, segs=16, sides=4)
        hoop(kit, f"wheel inner rim {sx}", wr, (sx, 0, 0), Rw * 0.45, 0.06, pink, segs=12, sides=4)
        for k in range(8):
            a = 2 * math.pi * k / 8
            tube(kit, f"wheel spoke {sx} {k}", [(sx, 0, 0), (sx, Rw * math.cos(a), Rw * math.sin(a))], 0.045, frame_m, wr, sides=4)
    tube(kit, "wheel hub", [(-0.75, 0, 0), (0.75, 0, 0)], 0.55, pink, wr, sides=8, front=(0, 0, 1))
    tube(kit, "wheel hub face", [(-0.8, 0, 0), (-0.75, 0, 0)], 0.6, tex_mat("wheel hub", tex_hub(), 0.9), wr, sides=8,
         front=(0, 0, 1))
    for k in range(16):
        a = 2 * math.pi * (k + 0.5) / 16
        tbox(kit, f"rim bulb {k}", (-0.72, Rw * math.cos(a), Rw * math.sin(a)), (0.1, 0.16, 0.16), bulbs[k % 4], wr)
    cups = [tex_mat(f"cup {c}", tex_pint(c)) for c in (PINK, MINT, YEL, "#7fd8ff")]
    for k in range(8):
        a = 2 * math.pi * k / 8 + math.radians(-12)
        gy, gz = Rw * math.cos(a), Rw * math.sin(a)
        tube(kit, f"gondola bar {k}", [(-0.6, gy, gz), (0.6, gy, gz)], 0.04, steel, wr, sides=4, front=(0, 0, 1))
        g = kit.empty(f"gondola {k}", wr, (0, gy, gz), (-12, 0, 0))
        tube(kit, f"gondola {k} hanger", [(0, 0, 0), (0, 0, -0.62)], 0.035, steel, g, sides=4)
        tube(kit, f"gondola {k} cup", [(0, 0, -1.3), (0, 0, -1.25), (0, 0, -0.62)], [0.3, 0.42, 0.6], cups[k % 4], g, sides=8,
             caps=(True, False), v=(0.0, 0.62))
        lowball(kit, f"gondola {k} cherry", (0, 0, 0.12), (0.1, 0.1, 0.1), solid(kit, "cherry", RED, 0.6), g, smooth=False)
    point_light(kit, fw, "wheel glow", (-1.6, 0, Hh), PINK, 700, 14.0, 1.0)
    point_light(kit, fw, "wheel base light", (-2.2, 0, 1.6), "#ffe6a0", 260, 7.0, 0.4)

    # helter-skelter: striped tower, cone roof, spiral slide wound around it
    HS = (16.6, -6.7)
    hs = kit.empty("helter skelter", root, (HS[0], HS[1], 0))
    tube(kit, "helter tower", [(0, 0, 0), (0, 0, 7.0)], [1.15, 0.95], tex_mat("helter stripes", tex_stripes(YEL, RED, 32, 8, 4)), hs,
         sides=8, smooth=False, caps=(False, False))
    tube(kit, "helter hut", [(0, 0, 7.0), (0, 0, 8.0)], 1.2, tex_mat("helter hut", tex_stripes(WHITE, PINK, 32, 8, 4)), hs, sides=8,
         smooth=False)
    tube(kit, "helter roof", [(0, 0, 8.0), (0, 0, 9.8)], [1.55, 0.05], tex_mat("helter roof", tex_stripes(RED, WHITE, 32, 8, 2)), hs,
         sides=8, smooth=False)
    tbox(kit, "helter flag", (0.3, 0, 10.05), (0.6, 0.02, 0.35), pink, hs, taper=(0.1, 1))
    tube(kit, "helter flag pole", [(0, 0, 9.7), (0, 0, 10.3)], 0.02, gold, hs, sides=3)
    tbox(kit, "helter door", (-1.12, 0, 0.95), (0.06, 0.8, 1.9), ink, hs, rot=(0, 0, 0))
    tbox(kit, "helter window", (-1.18, 0, 7.5), (0.06, 1.0, 0.6), ink, hs)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    turns, steps, z0, z1, r0, r1 = 2.25, 40, 7.0, 0.35, 1.05, 2.0
    rows = []
    for i in range(steps + 1):
        t = i / steps
        a = math.pi + 2 * math.pi * turns * t
        z = z0 + (z1 - z0) * t
        ca, sa = math.cos(a), math.sin(a)
        rows.append([bm.verts.new((r * ca, r * sa, z + dz)) for r, dz in ((r0, 0), (r1, 0), (r1 + 0.04, 0.3))])
    for i in range(steps):
        A, B = rows[i], rows[i + 1]
        for j, quad in enumerate(((A[0], A[1], B[1], B[0]), (A[1], B[1], B[2], A[2]))):
            f = bm.faces.new(quad)
            for lp, uv in zip(f.loops, ((i / 8, j * 0.5), (i / 8, j * 0.5 + 0.5), ((i + 1) / 8, j * 0.5 + 0.5), ((i + 1) / 8, j * 0.5))):
                lp[uvl].uv = uv
    kit.mesh_from_bmesh("helter slide", bm, tex_mat("helter slide", tex_stripes(MINT, "#22c79c", 16, 8, 2), ext='REPEAT'), hs,
                        smooth=False)
    tube(kit, "helter mat", [(-2.1, 0.2, 0.0), (-2.1, 0.2, 0.08)], 0.6, solid(kit, "mat", PURP), hs, sides=8)
    point_light(kit, hs, "helter light", (-1.8, 0, 7.6), "#ffe6a0", 260, 8.0, 0.4)

    # string lights criss-crossing the midway between poles
    poles = [(4.6, -2.3), (4.6, 2.3), (9.2, -2.3), (9.2, 2.3), (13.4, -2.3), (13.4, 2.3)]
    for i, (x, y) in enumerate(poles):
        tube(kit, f"light pole {i}", [(x, y, 0), (x, y, 4.2)], 0.07, solid(kit, "light pole", POLE, shade="#474aa0"), root, sides=6)
        lowball(kit, f"light pole top {i}", (x, y, 4.28), (0.1, 0.1, 0.1), gold, root, smooth=False)
    chains = [((1.2, -3.0, 4.9), (4.6, 2.3, 4.15)), ((1.2, 3.0, 4.9), (4.6, -2.3, 4.15)), ((4.6, -2.3, 4.15), (9.2, 2.3, 4.15)),
              ((4.6, 2.3, 4.15), (9.2, -2.3, 4.15)), ((9.2, -2.3, 4.15), (13.4, 2.3, 4.15)), ((9.2, 2.3, 4.15), (13.4, -2.3, 4.15)),
              ((13.4, 2.3, 4.15), (FW[0] - 1.2, FW[1] - 1.8, 3.4))]
    for i, (a, b) in enumerate(chains):
        string_lights(kit, root, f"string {i}", a, b, 0.5, 9, wire, bulbs)
    point_light(kit, root, "midway glow", (7.0, 0, 3.6), "#fff1a0", 420, 10.0, 1.0)

    # litter: popcorn boxes, a dropped cotton candy, balloons
    pop = tex_mat("popcorn box", tex_stripes(RED, WHITE, 16, 8, 2))
    for i, (x, y, rz, tip) in enumerate(((6.2, -1.1, 20, 90), (11.6, 1.2, -40, 0), (3.6, 1.0, 70, 90))):
        p = kit.empty(f"popcorn {i}", root, (x, y, 0.1 if tip else 0.04), (tip, 0, rz))
        tbox(kit, f"popcorn box {i}", (0, 0, 0.1), (0.16, 0.16, 0.22), pop, p, taper=(1.3, 1.3))
        lowball(kit, f"popcorn top {i}", (0, 0, 0.23), (0.11, 0.11, 0.06), solid(kit, "popcorn", "#fff1c7"), p, smooth=False)
    for i in range(14):
        tbox(kit, f"popcorn {i}", (R.uniform(2.5, 13.0), R.uniform(-1.4, 1.4), 0.1), (0.07, 0.07, 0.06),
             solid(kit, "popcorn", "#fff1c7"), root, rot=(R.uniform(0, 90), 0, R.uniform(0, 90)))
    cc = kit.empty("cotton candy", root, (8.0, 1.0, 0.08), (90, 0, 30))
    tube(kit, "cotton candy stick", [(0, 0, -0.25), (0, 0, 0.1)], 0.015, white, cc, sides=3)
    lowball(kit, "cotton candy", (0, 0, 0.2), (0.16, 0.16, 0.18), solid(kit, "cotton candy", "#ff9fd0", 0.6), cc)
    for i, (x, y, z, col) in enumerate(((5.1, 6.4, 3.2, RED), (5.3, 6.6, 3.5, YEL), (12.2, 6.1, 3.0, MINT))):
        lowball(kit, f"balloon {i}", (x, y, z), (0.22, 0.22, 0.27), solid(kit, f"balloon {col}", col, 0.6), root)
        tube(kit, f"balloon string {i}", [(x, y, z - 0.27), (x - 0.1, y + 0.2, 1.6)], 0.008, white, root, sides=3)

    # sockets
    for i, p in enumerate(((6.4, 0.0), (3.4, 4.4), (10.4, 4.4), (2.9, -2.6), (4.6, -9.0), (12.6, 4.6), (13.0, -6.2)), 1):
        socket(kit, root, f"loot {i}", (p[0], p[1], 0))
    socket(kit, root, "crate 1", (11.4, -0.4, 0), (0, 0, 90))
    socket(kit, root, "crate 2", (12.2, -3.8, 0), (0, 0, 30))
    for i, p in enumerate(((3.4, 9.6), (6.9, 9.7), (10.4, 9.6), (19.5, 3.6), (18.8, -9.4), (8.6, -5.8)), 1):
        socket(kit, root, f"horde {i}", (p[0], p[1], 0))


ASSETS = [
    ("School Hot Spot", build_school),
    ("Park Hot Spot", build_park),
    ("Fairground Hot Spot", build_fair),
]

CAM = ((-9, -21, 12), (9, 1, 2.5), 28)
AWAY = ((-2.1, -19, 0), 0)
SCENES = [
    dict(name="school scene", build=stop_scene(build_school, "School Hot Spot"), cam=CAM, res=(1600, 900)),
    dict(name="park scene", build=stop_scene(build_park, "Park Hot Spot"), cam=CAM, res=(1600, 900)),
    dict(name="fair scene", build=stop_scene(build_fair, "Fairground Hot Spot"), cam=CAM, res=(1600, 900)),
    dict(name="school road view", build=stop_scene(build_school, "School Hot Spot", AWAY), cam=((-6, -14, 2.2), (10, 0, 2.5), 24),
         res=(1600, 900)),
    dict(name="park road view", build=stop_scene(build_park, "Park Hot Spot", AWAY), cam=((-6, -14, 2.2), (10, 0, 2.5), 24),
         res=(1600, 900)),
    dict(name="fair road view", build=stop_scene(build_fair, "Fairground Hot Spot", AWAY), cam=((-6, -14, 2.2), (10, 0, 3.5), 24),
         res=(1600, 900)),
]
