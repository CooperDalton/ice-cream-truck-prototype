"""Divorced Dads items (style H): scavenged ingredients (Mud Bucket, Iced Coffee, Nut Sack, Gold Leaf), cones, flavor
scoops and flavor tubs, Lunch Money, the Thought Bubble, and the world set pieces (Mud Puddle, Strawberry Patch, Nut
Tree, Vault, Pressure Plate, Gate, Loudspeaker).

Conventions as in h_items: root at the bottom center, front -Y. Two-handed bulky items have 'socket hand L' (+X) and
'socket hand R' (-X); small handheld items 'socket hand'. Cones: origin at the tip, 'socket scoop 1..3' stacked where
scoops sit. Scoops: origin at the bottom center of the frill. Moving parts sit on pivots at their hinge or axis."""
from style_H import *
import h_items as items
from h_items import coin_mesh, tex_coin, tex_bill, pillow, tex_tub_h, tex_tub_lid, tub_inner_r, TUB_H, TUB_RB, TUB_RT, TUB_W
from h_dads_characters import lathe, torus, txt, txt_c, FONT2

SPACING = 3

GOLD = "#ffd23a"; GOLD_D = "#d9901a"; GOLD_L = "#fff1a0"
LEAF = "#3fdc6e"; LEAF_D = "#1f9e4a"
MUD = "#7a5a3c"; MUD_D = "#5e4430"; MUD_L = "#9a7a58"
COFFEE = "#c69261"; COFFEE_D = "#a8743f"; BEAN = "#3a1c0c"
CARD = "#d9a868"; CARD_D = "#b8844a"
BARK = "#7a4a5a"; BARK_D = "#5e3646"

# flavor table (keys used by h_items tub textures: label, cream, shade, hi, kind, chip, tint, tint_d, ink)
FLV = {
    "Mud": dict(label="MUD", cream=MUD, shade=MUD_D, hi=MUD_L, kind="mud", chip="#9a92b0", tint="#9a6a42",
                tint_d="#6e4428", ink="#5e3418", emit=0.36),
    "Strawberry": dict(label="BERRY", cream="#ff9fcf", shade="#ff7dbb", hi="#ffd6ea", kind="berry", chip=RED, tint=PINK,
                       tint_d="#d63a86", ink="#d63a86", emit=0.4),
    "Coffee": dict(label="COFFEE", cream=COFFEE, shade=COFFEE_D, hi="#e0b080", kind="coffee", chip=BEAN, tint="#b07a48",
                   tint_d="#7a4a24", ink="#5a3014", emit=0.38),
    "Rocky Road": dict(label="ROCKY", cream="#8a4a26", shade="#6a3418", hi="#a8643a", kind="rocky", chip=WHITE,
                       tint=CHOC, tint_d="#4a2410", ink="#4a2410", emit=0.38),
    "Gold Leaf": dict(label="GOLD", cream="#fff1c7", shade="#f0d590", hi="#fffbea", kind="gold", chip=GOLD, tint=GOLD,
                      tint_d=GOLD_D, ink="#a8641a", emit=0.55),
}
FLAVORS = ("Mud", "Strawberry", "Coffee", "Rocky Road", "Gold Leaf")


def socket(kit, A, purpose, parent, loc, rot=(0, 0, 0)):
    ob = kit.empty(f"{A} socket {purpose}", parent, loc, rot)
    ob.empty_display_type = 'ARROWS'
    return ob


# ---------------------------------------------------------------- flavor scoops
def tex_scoop(f, rand):
    c = Canvas(32, 16, f["cream"])
    c.speckle(rand, [f["shade"]], 60)
    c.rect(0, 0, 31, 1, f["shade"])
    c.speckle(rand, [f["hi"]], 30, 8, 15)
    k = f["kind"]
    if k == "mud":
        c.speckle(rand, ["#9a92b0", "#6e6688", MUD_D], 40, 2, 15)
        for _ in range(4):
            x, y = rand.randrange(32), rand.randint(3, 13)
            c.rect(x, y, x + 2, y, "#5e4430")
    elif k == "berry":
        for _ in range(9):
            x, y = rand.randrange(32), rand.randint(2, 13)
            c.rect(x, y, x + 1, y + 1, RED); c.set(x + 1, y + 1, "#ff6a8a")
        c.speckle(rand, [YEL, "#ffd0e6"], 26, 2, 15)
    elif k == "coffee":
        for _ in range(7):
            x, y = rand.randrange(32), rand.randint(2, 13)
            for s in range(4):
                c.set(x + s, y + (s % 2), "#e8c090")
        c.speckle(rand, [BEAN, "#6a3a1a"], 26, 2, 15)
    elif k == "rocky":
        for _ in range(6):
            x, y = rand.randrange(32), rand.randint(2, 13)
            c.rect(x, y, x + 1, y + 1, WHITE)
        c.speckle(rand, ["#d9a868", "#3a1c0c"], 24, 2, 15)
    elif k == "gold":
        c.speckle(rand, [YEL, GOLD, GOLD_L, WHITE], 50, 2, 15)
    return c


SCOOP_Z = (0.0, 0.12, 0.22, 0.6, 1.05, 1.42, 1.66)
SCOOP_R = (0.62, 1.04, 0.86, 1.04, 0.98, 0.7, 0.3)


def scoop_ball(kit, name, parent, loc, r, mat):
    """Hand-scooped ball (h_items.scoop without the flavor bits): frilly lip at the bottom, lumpy dome."""
    R = kit.rand
    ob = tube(kit, name, [(0, 0, z * r) for z in SCOOP_Z], [x * r for x in SCOOP_R], mat, parent, sides=8,
              bulge=(0, 0.08 * r), loc=loc)
    for i, vtx in enumerate(ob.data.vertices):
        ring, k = divmod(i, 8)
        if ring == 1:
            s = 1.1 if k % 2 else 0.95
            vtx.co.x *= s; vtx.co.y *= s; vtx.co.z += 0.05 * r if k % 2 else -0.03 * r
        elif 2 <= ring <= 6 or i == 57:
            vtx.co += Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * 0.06 * r
    return ob


def on_ball(r, t, a):
    """Point on the scoop dome: t 0 (equator) .. 1 (top), angle a. Returns (x, y, z, normal)."""
    z = (0.6 + 0.95 * t) * r
    rr = (1.02 - 0.66 * t * t) * r
    n = Vector((math.cos(a), math.sin(a), 0.4 + 1.2 * t)).normalized()
    return Vector((math.cos(a) * rr, math.sin(a) * rr, z)), n


def gummy_worm(kit, name, parent, pts, r=0.006):
    c = Canvas(16, 8, "#ff6a3d")
    for x in range(0, 16, 4):
        c.rect(x, 0, x + 1, 7, "#ffe14a")
    c.rect(0, 0, 3, 7, "#ff4fa3")
    tube(kit, name, pts, [r * (0.7 if i == len(pts) - 1 else 1.0) for i in range(len(pts))],
         tex_mat(f"{name} gummy", c, 0.5, ext='REPEAT'), parent, sides=5, bulge=(r * 0.6, r * 0.6))


def coffee_bean(kit, name, parent, loc, s, rot):
    p = kit.empty(name, parent, loc, rot)
    lowball(kit, f"{name} bean", (0, 0, 0), (s, s * 0.7, s * 0.45), solid(kit, "coffee bean", "#4a2410", 0.3, shade=BEAN), p)
    tbox(kit, f"{name} groove", (0, 0, s * 0.42), (s * 1.5, s * 0.12, s * 0.06), solid(kit, "bean groove", BEAN, 0.2), p)
    return p


def flavor_bits(kit, A, parent, base, r, fl):
    """3D toppings pressed into a scoop of radius r whose bottom center is `base` (parent space)."""
    R = kit.rand
    B = Vector(base)
    k = FLV[fl]["kind"]
    if k == "mud":
        peb = solid(kit, "pebble", "#9a92b0", 0.3, shade="#6e6688")
        for i, (t, a) in enumerate(((0.2, 0.4), (0.5, 2.6), (0.1, 4.2), (0.7, 5.4))):
            p, n = on_ball(r, t, a)
            lowball(kit, f"{A} pebble {i}", tuple(B + p), (r * 0.16, r * 0.14, r * 0.12), peb, parent, smooth=False)
        p0, n0 = on_ball(r, 0.55, 1.2)
        gummy_worm(kit, f"{A} worm", parent, [tuple(B + p0 - n0 * r * 0.1), tuple(B + p0 + n0 * r * 0.35),
                                               tuple(B + p0 + n0 * r * 0.55 + Vector((0, 0, r * 0.35))),
                                               tuple(B + p0 + n0 * r * 0.4 + Vector((r * 0.25, -r * 0.1, r * 0.6)))],
                   r * 0.13)
    elif k == "berry":
        berry = solid(kit, "berry chunk", RED, 0.42, shade=DRED)
        for i, (t, a) in enumerate(((0.3, 0.6), (0.6, 3.0), (0.15, 4.6))):
            p, n = on_ball(r, t, a)
            tbox(kit, f"{A} berry {i}", (0, 0, 0), (r * 0.26, r * 0.22, r * 0.2), berry, parent, loc=tuple(B + p),
                 rot=(R.uniform(0, 60), R.uniform(0, 60), R.uniform(0, 90)))
    elif k == "coffee":
        for i, (t, a) in enumerate(((0.65, 0.9), (0.3, 3.6))):
            p, n = on_ball(r, t, a)
            coffee_bean(kit, f"{A} coffee bean {i}", parent, tuple(B + p + n * r * 0.05), r * 0.24,
                        tuple(math.degrees(v) for v in n.to_track_quat('Z', 'Y').to_euler()))
    elif k == "rocky":
        mm = solid(kit, "marshmallow", WHITE, 0.5, shade="#efe4da")
        nut = solid(kit, "nut bit", "#d9a868", 0.35, shade="#b8844a")
        for i, (t, a) in enumerate(((0.25, 0.3), (0.55, 2.2), (0.1, 3.7), (0.8, 4.9), (0.35, 5.6))):
            p, n = on_ball(r, t, a)
            tbox(kit, f"{A} marshmallow {i}", (0, 0, 0), (r * 0.28, r * 0.28, r * 0.24), mm, parent, loc=tuple(B + p),
                 rot=(R.uniform(0, 40), R.uniform(0, 40), R.uniform(0, 90)))
        for i, (t, a) in enumerate(((0.45, 1.2), (0.2, 2.9), (0.7, 3.4), (0.05, 5.0))):
            p, n = on_ball(r, t, a)
            tbox(kit, f"{A} nut {i}", (0, 0, 0), (r * 0.18, r * 0.12, r * 0.1), nut, parent, loc=tuple(B + p),
                 rot=(R.uniform(0, 90), R.uniform(0, 90), R.uniform(0, 90)))
    elif k == "gold":
        flake = solid(kit, "gold flake", GOLD, 1.3, shade=GOLD_L)
        for i in range(7):
            t, a = R.uniform(0.05, 0.85), 2 * math.pi * i / 7 + R.uniform(-0.3, 0.3)
            p, n = on_ball(r, t, a)
            q = n.to_track_quat('Z', 'Y').to_euler()
            tbox(kit, f"{A} gold flake {i}", (0, 0, 0), (r * 0.3, r * 0.22, r * 0.02), flake, parent,
                 loc=tuple(B + p + n * r * 0.02), rot=(math.degrees(q.x), math.degrees(q.y), R.uniform(0, 90)))


def build_scoop(kit, root, A, fl):
    f = FLV[fl]
    r = 0.045
    cream = tex_mat(f"{A} cream", tex_scoop(f, kit.rand), f["emit"], ext='REPEAT')
    scoop_ball(kit, f"{A} ball", root, (0, 0, 0), r, cream)
    flavor_bits(kit, A, root, (0, 0, 0), r, fl)
    socket(kit, A, "hand", root, (0, 0, 0.8 * r))


# ---------------------------------------------------------------- cones
def tex_sugar_cone():
    c = Canvas(32, 32, "#f0b860")
    for y in range(0, 32, 3):
        c.rect(0, y, 31, y, "#d9963f")
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 31, "#e0a24a")
    c.rect(0, 28, 31, 31, "#e8a850")
    return c


def tex_waffle_cone(dip=None):
    c = Canvas(32, 32, "#ffcf5a")
    for y in range(32):
        for x in range(32):
            if (x + y) % 6 == 0 or (x - y) % 6 == 0:
                c.set(x, y, "#d9862a")
    if dip:
        c.rect(0, 25, 31, 31, dip)
        for x in range(0, 32, 3):
            c.rect(x, 22 + (x * 7) % 4, x + 1, 25, dip)
        c.speckle(random.Random(5), [PINK, BLUE, YEL, MINT, WHITE], 30, 24, 31)
    return c


def build_cone(kit, root, A, kind):
    if kind == "sugar":
        H, rt = 0.18, 0.038
        body = tex_mat(f"{A} cone", tex_sugar_cone(), ext='REPEAT')
        lathe(kit, f"{A} cone", [(0.004, 0.0), (rt * 0.55, H * 0.55), (rt, H - 0.02), (rt * 1.06, H - 0.018),
                                 (rt * 1.06, H), (rt * 0.92, H + 0.004), (0, H - 0.006)], body, root, sides=8)
        lathe(kit, f"{A} rim", [(rt * 1.0, H - 0.034), (rt * 1.1, H - 0.032), (rt * 1.1, H - 0.02), (rt * 1.0, H - 0.018)],
              solid(kit, f"{A} rim", "#e0a24a", shade="#d9963f"), root, sides=8, closed=True)
        z1, step = H - 0.006, 0.066
    else:
        double = kind == "double"
        H, rt = (0.25, 0.05) if double else (0.2, 0.045)
        dip = "#6e3a1e" if not double else "#ff4fa3"
        body = tex_mat(f"{A} waffle", tex_waffle_cone(dip), ext='REPEAT')
        lathe(kit, f"{A} cone", [(0.004, 0.0), (rt * 0.5, H * 0.5), (rt, H - 0.01), (rt * 1.08, H), (rt * 0.9, H + 0.004),
                                 (0, H - 0.008)], body, root, sides=10)
        roll = solid(kit, f"{A} roll", "#e8a850", shade="#d9862a")
        torus(kit, f"{A} rolled rim", rt * 1.06, 0.007, roll, root, loc=(0, 0, H), seg=10, sides=5)
        if double:
            torus(kit, f"{A} dip ring", rt * 0.86, 0.008, solid(kit, f"{A} dip", "#6e3a1e", 0.35), root,
                  loc=(0, 0, H * 0.62), seg=10, sides=5)
            spr = [solid(kit, f"{A} sprinkle {c}", c, 0.6) for c in (YEL, BLUE, WHITE, MINT)]
            for i in range(10):
                a = 2 * math.pi * i / 10
                tbox(kit, f"{A} sprinkle {i}", (0, 0, 0), (0.004, 0.012, 0.004), spr[i % 4], root,
                     loc=(math.cos(a) * rt * 1.0, math.sin(a) * rt * 1.0, H - 0.018 - 0.008 * (i % 2)),
                     rot=(0, 30 * (i % 3), math.degrees(a) + 40))
        z1, step = H - 0.008, 0.07
    for i in range(3):
        socket(kit, A, f"scoop {i + 1}", root, (0, 0, z1 + step * i))
    socket(kit, A, "hand", root, (0, 0, H * 0.4))


# ---------------------------------------------------------------- flavor tubs (same layout as Flavor Tub Vanilla)
def build_tub(kit, root, A, fl):
    f, R = FLV[fl], kit.rand
    H, rb, rt, w = TUB_H, TUB_RB, TUB_RT, TUB_W
    body = tex_mat(f"{A} tub", tex_tub_h(f, R, 8), ext='REPEAT')
    items.lathe(kit, f"{A} tub", [(0, 0, 0.004), (rb - 0.008, 0, 0.012), (rb, 0.008, 0.025), (rt, H - 0.022, 0.54),
                                  (rt + 0.006, H - 0.018, 0.56), (rt + 0.006, H, 0.6), (rt - w, H, 0.625),
                                  (rb - w, 0.012, 0.95), (0, 0.012, 0.99)], body, root, sides=12)
    cream = tex_mat(f"{A} cream", tex_scoop(f, R), f["emit"], ext='REPEAT')
    zf = H - 0.014
    ri = tub_inner_r(zf)
    items.lathe(kit, f"{A} ice cream", [(ri - 0.001, zf - 0.03, 0.05), (ri - 0.002, zf, 0.2), (ri * 0.78, zf + 0.026, 0.45),
                                        (ri * 0.42, zf + 0.04, 0.75), (0, zf + 0.046, 0.98)], cream, root, sides=12, jit=0.006)
    scoop_ball(kit, f"{A} swirl", root, (0.03, -0.02, zf + 0.022), 0.05, cream)
    flavor_bits(kit, f"{A} top", root, (0.03, -0.02, zf + 0.022), 0.05, fl)
    hinge = kit.empty(f"{A} lid hinge", root, (0, rt + 0.008, H), (-112, 0, 0))
    lid = tex_mat(f"{A} lid", tex_tub_lid(f, R), ext='REPEAT')
    items.lathe(kit, f"{A} lid", [(rt + 0.01, -0.02, 0.03), (rt + 0.012, 0.004, 0.25), (rt * 0.92, 0.012, 0.5),
                                  (rt * 0.35, 0.017, 0.82), (0, 0.017, 0.98)], lid, hinge, sides=12, loc=(0, -(rt + 0.008), 0))
    tbox(kit, f"{A} lid tab", (0, -(2 * rt + 0.02), -0.004), (0.05, 0.022, 0.008), solid(kit, f"{A} tab", f["tint_d"]), hinge)
    socket(kit, A, "hand L", root, (rt + 0.01, 0, H * 0.55))
    socket(kit, A, "hand R", root, (-(rt + 0.01), 0, H * 0.55))


# ---------------------------------------------------------------- bulky ingredients
def tex_bucket(rand):
    c = Canvas(32, 32, "#c9c2f0")
    c.speckle(rand, ["#b4acdf", "#ddd6fa", "#a39bd0"], 120)
    for y in (6, 20):
        c.rect(0, y, 31, y + 1, "#9d95d4")
    for _ in range(9):   # mud drips down the outside from the rim
        x = rand.randrange(32)
        ln = rand.randint(4, 14)
        c.rect(x, 31 - ln, x + rand.randint(0, 1), 31, MUD)
    c.rect(0, 29, 31, 31, MUD)
    return c


def tex_mud(rand):
    c = Canvas(32, 32, MUD)
    c.speckle(rand, [MUD_D, MUD_L, "#6a4a30"], 220)
    c.speckle(rand, ["#9a92b0"], 18)
    for _ in range(6):
        x, y = rand.randrange(32), rand.randrange(32)
        c.dots([(x, y), (x + 1, y), (x + 2, y + 1)], "#b89a78")
    return c


def build_mud_bucket(kit, root, A):
    R = kit.rand
    H, rb, rt = 0.27, 0.12, 0.15
    pail = tex_mat(f"{A} pail", tex_bucket(R), ext='REPEAT')
    ob = lathe(kit, f"{A} pail", [(0, 0.005), (rb, 0.0), (rb + 0.004, 0.03), (rt - 0.004, H - 0.02), (rt + 0.008, H),
                                  (rt - 0.006, H + 0.004), (rb - 0.006, 0.02), (0, 0.02)], pail, root, sides=12, smooth=False)
    for v in ob.data.vertices:   # dents
        a = math.atan2(v.co.y, v.co.x)
        d = 0.018 * max(0.0, math.cos(a - 0.9)) ** 6 * min(1.0, v.co.z / H * 1.6) + 0.01 * max(0.0, math.cos(a + 2.4)) ** 8
        v.co.x -= math.cos(a) * d; v.co.y -= math.sin(a) * d
    mud = tex_mat(f"{A} mud", tex_mud(R), 0.36, ext='REPEAT')
    lathe(kit, f"{A} mud heap", [(rt - 0.004, H - 0.03), (rt + 0.012, H + 0.012), (rt * 0.8, H + 0.05), (rt * 0.45, H + 0.08),
                                 (0, H + 0.09)], mud, root, sides=10)
    for i, (a, ln) in enumerate(((0.4, 0.09), (2.0, 0.14), (3.3, 0.06), (4.6, 0.11), (5.5, 0.08))):
        ca, sa = math.cos(a), math.sin(a)
        tube(kit, f"{A} drip {i}", [(ca * (rt + 0.01), sa * (rt + 0.01), H + 0.01), (ca * (rt + 0.008), sa * (rt + 0.008), H - ln * 0.5),
                                    (ca * (rt - 0.002), sa * (rt - 0.002), H - ln)], [0.016, 0.012, 0.009], mud, root,
             sides=5, bulge=(0, 0.008))
    for i in range(3):   # bubbles on the heap
        a = R.uniform(0, 6.28)
        lowball(kit, f"{A} bubble {i}", (math.cos(a) * 0.06, math.sin(a) * 0.06, H + 0.07), (0.016, 0.016, 0.012),
                solid(kit, "mud bubble", MUD_L, 0.4), root)
    gummy_worm(kit, f"{A} worm", root, [(-0.03, -0.04, H + 0.06), (-0.04, -0.07, H + 0.11), (-0.02, -0.09, H + 0.15),
                                        (0.01, -0.085, H + 0.165)], 0.011)
    for sx in (1, -1):
        tbox(kit, f"{A} ear {sx}", (sx * (rt + 0.004), 0, H - 0.03), (0.012, 0.03, 0.03), solid(kit, "pail ear", "#9d95d4"), root)
    bail = kit.empty(f"{A} handle", root, (0, 0, H - 0.03), (0, 0, 0))
    tube(kit, f"{A} handle", [(rt + 0.01, 0, 0), (rt * 0.9, -0.02, 0.1), (0, -0.03, 0.15), (-rt * 0.9, -0.02, 0.1), (-(rt + 0.01), 0, 0)],
         0.006, solid(kit, "handle wire", STEEL, 0.4), bail, sides=4, caps=(False, False))
    socket(kit, A, "hand L", root, (rt + 0.01, 0, H * 0.6))
    socket(kit, A, "hand R", root, (-(rt + 0.01), 0, H * 0.6))


def tex_sleeve():
    c = Canvas(64, 16, "#d9a868")
    c.rect(0, 0, 63, 1, "#b8844a"); c.rect(0, 14, 63, 15, "#b8844a")
    c.rect(0, 3, 63, 12, WHITE)
    txt_c(c, "BEAN", 16, 11, "#6e3a1e")
    txt_c(c, "THERE", 16, 5 + 1, PINK)
    txt_c(c, "BEAN", 48, 11, "#6e3a1e")
    txt_c(c, "THERE", 48, 6, PINK)
    return c


def tex_iced(rand):
    c = Canvas(16, 32, COFFEE)
    c.speckle(rand, ["#d8a878", "#b07a48"], 50)
    c.rect(0, 0, 15, 4, "#8a5a2a")
    c.rect(0, 24, 15, 31, "#f0dcc0")   # creamy top layer
    c.speckle(rand, [WHITE], 10, 24, 31)
    return c


def build_iced_coffee(kit, root, A):
    R = kit.rand
    W = 0.28
    tray = tex_mat(f"{A} carrier", tex_carrier())
    tbox(kit, f"{A} carrier", (0, 0, 0.015), (W, W, 0.03), tray, root, uv={'all': (0, 0, 0.1, 0.1), 'pz': (0, 0, 1, 1)})
    for sx in (1, -1):
        tbox(kit, f"{A} wall {sx}", (sx * (W / 2 - 0.004), 0, 0.045), (0.008, W, 0.07), tray, root,
             uv={'all': (0.0, 0.0, 0.2, 0.2)})
        tbox(kit, f"{A} wall y {sx}", (0, sx * (W / 2 - 0.004), 0.045), (W, 0.008, 0.07), tray, root,
             uv={'all': (0.0, 0.0, 0.2, 0.2), 'ny': (0.0, 0.0, 1.0, 0.3), 'py': (0.0, 0.0, 1.0, 0.3)})
    # center divider with a carry handle
    tbox(kit, f"{A} divider", (0, 0, 0.1), (0.008, W - 0.02, 0.18), tray, root, uv={'all': (0, 0, 0.2, 0.2)})
    tbox(kit, f"{A} divider x", (0, 0, 0.06), (W - 0.02, 0.008, 0.1), tray, root, uv={'all': (0, 0, 0.2, 0.2)})
    plastic = items.glass_mat(f"{A} cup")
    coffee = tex_mat(f"{A} iced coffee", tex_iced(R), 0.4, ext='REPEAT')
    sleeve = tex_mat(f"{A} sleeve", tex_sleeve(), ext='REPEAT')
    lid = solid(kit, f"{A} lid", "#f4f0ff", 0.45, shade="#d9d4ff")
    ice = solid(kit, f"{A} ice", "#e0f4ff", 0.6, shade="#b8dcff")
    straws = (PINK, MINT, YEL, BLUE)
    for i, (x, y) in enumerate(((-0.07, -0.07), (0.07, -0.07), (-0.07, 0.07), (0.07, 0.07))):
        cp = kit.empty(f"{A} cup {i}", root, (x, y, 0.01), (0, 0, 45 + 90 * i))
        lathe(kit, f"{A} coffee {i}", [(0, 0.0), (0.034, 0.0), (0.045, 0.15), (0, 0.15)], coffee, cp, sides=8)
        lathe(kit, f"{A} cup {i}", [(0.036, -0.002), (0.048, 0.168), (0.05, 0.172)], plastic, cp, sides=8)
        lathe(kit, f"{A} cup sleeve {i}", [(0.0405, 0.05), (0.0455, 0.11)], sleeve, cp, sides=8)
        lathe(kit, f"{A} dome {i}", [(0.051, 0.168), (0.052, 0.176), (0.044, 0.19), (0.02, 0.2), (0, 0.202)], lid, cp, sides=8)
        for k in range(2):
            tbox(kit, f"{A} ice {i} {k}", (0, 0, 0), (0.022, 0.022, 0.022), ice, cp,
                 loc=(R.uniform(-0.015, 0.015), R.uniform(-0.015, 0.015), 0.13 + 0.02 * k), rot=(R.uniform(0, 40), 20, R.uniform(0, 90)))
        tube(kit, f"{A} straw {i}", [(0.008, 0.0, 0.05), (0.008, 0.0, 0.2), (0.012, -0.004, 0.25)], 0.0055,
             solid(kit, f"{A} straw {i}", straws[i], 0.5), cp, sides=5)
    socket(kit, A, "hand L", root, (W / 2, 0, 0.06))
    socket(kit, A, "hand R", root, (-W / 2, 0, 0.06))


def tex_carrier():
    c = Canvas(32, 32, CARD)
    c.speckle(random.Random(3), [CARD_D, "#e8bc80"], 90)
    for y in range(0, 32, 4):
        c.rect(0, y, 31, y, "#c8945a")
    txt_c(c, "BEAN", 16, 20, "#6e3a1e")
    return c


def tex_burlap_nuts(rand):
    c = Canvas(64, 32, "#d9b07a")
    for y in range(32):
        for x in range(64):
            if (x + 2 * y) % 4 == 0:
                c.set(x, y, "#c49660")
            elif (x * 5 + y) % 7 == 0:
                c.set(x, y, "#e8c48e")
    c.rect(6, 7, 25, 19, "#f4e6c4"); c.rect(6, 7, 25, 7, "#c49660")
    txt_c(c, "NUTS", 16, 17, "#7a3a1c")
    for x in (9, 22):
        disc(c, x, 10, 1, "#a8643a")
    txt_c(c, "NUTS", 48, 17, "#7a3a1c")
    return c


def acorn(kit, name, parent, loc, s, rot=(0, 0, 0), mats=None):
    nut, capm = mats
    p = kit.empty(name, parent, loc, rot)
    lathe(kit, f"{name} nut", [(0, -0.6 * s), (0.45 * s, -0.4 * s), (0.55 * s, 0.0), (0.5 * s, 0.25 * s), (0, 0.3 * s)], nut, p,
          sides=6)
    lathe(kit, f"{name} cap", [(0.5 * s, 0.15 * s), (0.6 * s, 0.3 * s), (0.4 * s, 0.5 * s), (0, 0.55 * s)], capm, p, sides=6)
    tube(kit, f"{name} stem", [(0, 0, 0.5 * s), (0, 0, 0.75 * s)], 0.08 * s, capm, p, sides=4)
    return p


def build_nut_sack(kit, root, A):
    R = kit.rand
    m = tex_mat(f"{A} burlap", tex_burlap_nuts(R))
    pillow(kit, f"{A} sack", 0.4, 0.42, 0.28, m, root, nx=6, nz=6, jit=0.012, slump=0.0)
    mats = (solid(kit, "acorn", "#c47f3a", 0.35, shade="#a8642a"), solid(kit, "acorn cap", "#7a4a2a", 0.3, shade="#5e3418"))
    for i in range(9):   # nuts piled in the open top
        a = 2 * math.pi * i / 9 + R.uniform(-0.2, 0.2)
        rr = 0.03 + 0.07 * (i % 3) / 2
        acorn(kit, f"{A} acorn {i}", root, (math.cos(a) * rr * 1.3, math.sin(a) * rr * 0.7, 0.4 + 0.035 * (2 - i % 3)), 0.032,
              (R.uniform(-40, 40), R.uniform(-40, 40), R.uniform(0, 360)), mats)
    tie = solid(kit, "twine", "#a8642a", 0.3)
    tube(kit, f"{A} twine", [(-0.17, -0.06, 0.36), (0.0, -0.11, 0.35), (0.17, -0.06, 0.36)], 0.01, tie, root, sides=4)
    tube(kit, f"{A} twine tail", [(0.0, -0.11, 0.35), (0.02, -0.13, 0.28), (-0.01, -0.13, 0.22)], 0.008, tie, root, sides=4)
    acorn(kit, f"{A} loose acorn", root, (0.12, -0.17, 0.02), 0.032, (80, 0, 30), mats)
    socket(kit, A, "hand L", root, (0.2, 0, 0.2))
    socket(kit, A, "hand R", root, (-0.2, 0, 0.2))


def tex_velvet(rand):
    c = Canvas(16, 16, "#8a1f5a")
    c.speckle(rand, ["#a8306e", "#6e1446"], 60)
    return c


def build_gold_leaf(kit, root, A):
    R = kit.rand
    W, D, H = 0.3, 0.2, 0.12
    vel = tex_mat(f"{A} velvet", tex_velvet(R), 0.35, ext='REPEAT')
    lining = solid(kit, f"{A} lining", "#ff8fc8", 0.4, shade="#ff6fb5")
    gold = solid(kit, f"{A} gold trim", GOLD, 0.7, shade=GOLD_D)
    tbox(kit, f"{A} box", (0, 0, H / 2), (W, D, H), vel, root)
    tbox(kit, f"{A} lining", (0, 0, H - 0.004), (W - 0.03, D - 0.03, 0.01), lining, root)
    for i, z in enumerate((0.012, H - 0.012)):
        tbox(kit, f"{A} band {i}", (0, 0, z), (W + 0.008, D + 0.008, 0.014), gold, root)
    for sx in (1, -1):
        for sy in (1, -1):
            lowball(kit, f"{A} foot {sx} {sy}", (sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), 0.0), (0.016, 0.016, 0.014), gold, root)
    # stack of gold sheets fanning out of the box
    sheet = tex_mat(f"{A} sheet", tex_gold_sheet(R), 1.25)
    for i in range(5):
        tbox(kit, f"{A} sheet {i}", (0, 0, 0), (0.2, 0.14, 0.004), sheet, root,
             loc=(R.uniform(-0.02, 0.02), R.uniform(-0.015, 0.015) - 0.01 * i, H + 0.004 + 0.006 * i),
             rot=(R.uniform(-8, 8) - 6 * i, R.uniform(-6, 6), R.uniform(-12, 12)))
    for i, (p, s) in enumerate((((0.12, -0.12, 0.24), 0.03), ((-0.13, -0.08, 0.2), 0.022), ((0.02, -0.14, 0.3), 0.018))):
        fx_star(kit, root, f"{A} sparkle {i}", p, 4, s, s * 0.3, WHITE if i % 2 else YEL, 2.2, rot=(0, R.uniform(0, 40), 0))
    hinge = kit.empty(f"{A} lid", root, (0, D / 2, H), (-105, 0, 0))
    tbox(kit, f"{A} lid", (0, -D / 2, 0.03), (W, D, 0.06), vel, hinge, taper=(1.0, 0.8))
    tbox(kit, f"{A} lid band", (0, -D / 2, 0.006), (W + 0.008, D + 0.008, 0.012), gold, hinge)
    tbox(kit, f"{A} lid lining", (0, -D / 2, -0.002), (W - 0.03, D - 0.03, 0.006), lining, hinge)
    tbox(kit, f"{A} clasp", (0, -D / 2 - 0.006, H - 0.03), (0.04, 0.012, 0.04), gold, root)
    socket(kit, A, "hand L", root, (W / 2, 0, H * 0.5))
    socket(kit, A, "hand R", root, (-W / 2, 0, H * 0.5))


def tex_gold_sheet(rand):
    c = Canvas(16, 16, GOLD)
    c.speckle(rand, [GOLD_L, "#ffe46a", GOLD_D], 70)
    c.rect(0, 0, 15, 0, GOLD_D)
    return c


# ---------------------------------------------------------------- lunch money and the thought bubble
def tex_dollar():
    c = Canvas(32, 16, "#7fe0a0")
    c.rect(0, 0, 31, 0, "#2f9e5a"); c.rect(0, 15, 31, 15, "#2f9e5a"); c.rect(0, 0, 0, 15, "#2f9e5a"); c.rect(31, 0, 31, 15, "#2f9e5a")
    c.rect(2, 2, 29, 13, "#9cf0b8")
    disc(c, 16, 8, 4, "#5fd38a")
    txt(c, "$", 15, 10, "#1f7a44")
    txt(c, "1", 3, 13, "#1f7a44"); txt(c, "1", 26, 6, "#1f7a44")
    return c


def build_lunch_money(kit, root, A):
    R = kit.rand
    spin = kit.empty(f"{A} spin", root, (0, 0, 0))
    bill = tex_mat(f"{A} bill", tex_dollar(), 0.55)
    # crumpled dollar: three bent panels
    for i, (x, rz, ry) in enumerate(((-0.035, 8, 18), (0.0, -6, -14), (0.035, 10, 22))):
        tbox(kit, f"{A} bill {i}", (0, 0, 0), (0.04, 0.06, 0.003), bill, spin, loc=(x, 0.005 * i, 0.03 + 0.008 * (i % 2)),
             rot=(R.uniform(-15, 15), ry, rz), uv={'all': (i / 3, 0, (i + 1) / 3, 1)})
    tbox(kit, f"{A} fold", (0, 0, 0), (0.05, 0.03, 0.003), bill, spin, loc=(0.01, -0.03, 0.045), rot=(50, 10, -20),
         uv={'all': (0.3, 0.5, 0.7, 1.0)})
    coin = tex_mat(f"{A} coin", tex_coin(), 0.7)
    rim = solid(kit, f"{A} coin rim", GOLD_D, 0.6)
    for i, (p, rot) in enumerate((((-0.03, -0.02, 0.012), (78, 0, 20)), ((0.035, -0.025, 0.02), (60, 0, -30)))):
        coin_mesh(kit, f"{A} coin {i}", 0.02, 0.006, coin, spin, loc=p, rot=rot, sides=8)
    tube(kit, f"{A} band", [(-0.012, 0.0, 0.03), (0.012, 0.0, 0.03)], [(0.028, 0.012)] * 2, solid(kit, f"{A} band", PINK, 0.5),
         spin, sides=6, side=(0, 0, 1), caps=(False, False))
    fx_star(kit, spin, f"{A} sparkle", (0.05, -0.02, 0.07), 4, 0.016, 0.005, WHITE, 2.0)
    socket(kit, A, "hand", root, (0, 0, 0.03))


def build_thought_bubble(kit, root, A):
    """Puffy cloud facing -Y centered on the root ('socket icon' at the center), two small puffs trailing down to the
    lower left toward the thinker's head."""
    white = solid(kit, f"{A} cloud", WHITE, 0.75, shade="#ece4f4")
    rim = solid(kit, f"{A} outline", "#8f5bff", 0.5)
    lobes = [(0, 0, 0.13), (-0.13, 0.0, 0.1), (0.13, 0.0, 0.1), (-0.07, 0.09, 0.1), (0.07, 0.09, 0.1), (-0.08, -0.08, 0.09),
             (0.08, -0.08, 0.09), (0.19, -0.02, 0.07), (-0.19, -0.02, 0.07), (0.0, 0.12, 0.08)]
    for i, (x, z, r) in enumerate(lobes):
        lowball(kit, f"{A} lobe {i}", (x, 0.0, z), (r, r * 0.45, r), white, root)
        lowball(kit, f"{A} lobe rim {i}", (x, 0.02, z), (r * 1.08, r * 0.4, r * 1.08), rim, root)
    for i, (x, z, r) in enumerate(((-0.17, -0.2, 0.04), (-0.23, -0.29, 0.025))):
        lowball(kit, f"{A} puff {i}", (x, 0.0, z), (r, r * 0.6, r), white, root)
        lowball(kit, f"{A} puff rim {i}", (x, 0.012, z), (r * 1.15, r * 0.5, r * 1.15), rim, root)
    socket(kit, A, "icon", root, (0, -0.07, 0.0))


# ---------------------------------------------------------------- world set pieces
def tex_puddle(rand):
    c = Canvas(64, 64, MUD)
    c.speckle(rand, [MUD_D, "#6a4a30", MUD_L], 600)
    for _ in range(10):
        x, y = rand.randrange(64), rand.randrange(64)
        c.dots([(x, y), (x + 1, y), (x + 2, y + 1), (x + 3, y + 1)], "#b89a78")
    for _ in range(5):
        x, y = rand.randrange(64), rand.randrange(64)
        c.rect(x, y, x + 1, y, "#c8b4ff")
    return c


def blob_poly(R, n, rx, ry, wob=0.18):
    return [(math.cos(2 * math.pi * k / n) * rx * (1 + R.uniform(-wob, wob)),
             math.sin(2 * math.pi * k / n) * ry * (1 + R.uniform(-wob, wob))) for k in range(n)]


def flat_disc(kit, name, poly, z, mat, parent, scale_uv=0.6, center_z=None):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    c = bm.verts.new((0, 0, z if center_z is None else center_z))
    ring = [bm.verts.new((x, y, z)) for x, y in poly]
    for k in range(len(ring)):
        fc = bm.faces.new((c, ring[k], ring[(k + 1) % len(ring)]))
        for lp in fc.loops:
            lp[uvl].uv = (lp.vert.co.x * scale_uv + 0.5, lp.vert.co.y * scale_uv + 0.5)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def build_mud_puddle(kit, root, A):
    R = kit.rand
    rim_poly = blob_poly(R, 14, 0.82, 0.66, 0.12)
    wet = blob_poly(R, 14, 0.7, 0.55, 0.1)
    flat_disc(kit, f"{A} rim", rim_poly, 0.02, solid(kit, f"{A} dried mud", "#9a7a58", 0.3, shade="#8a6a4a"), root,
              center_z=0.02)
    for k, (x, y) in enumerate(rim_poly):   # slumped edge skirt down to the ground
        x2, y2 = rim_poly[(k + 1) % len(rim_poly)]
        bm = bmesh.new()
        vs = [bm.verts.new((x * 1.08, y * 1.08, 0.0)), bm.verts.new((x2 * 1.08, y2 * 1.08, 0.0)), bm.verts.new((x2, y2, 0.02)),
              bm.verts.new((x, y, 0.02))]
        bm.faces.new(vs)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        kit.mesh_from_bmesh(f"{A} edge {k}", bm, solid(kit, f"{A} dried mud", "#9a7a58", 0.3, shade="#8a6a4a"), root, smooth=False)
    flat_disc(kit, f"{A} mud", wet, 0.035, tex_mat(f"{A} mud", tex_puddle(R), 0.4, ext='REPEAT'), root, center_z=0.03)
    # a heap of mud in the middle and a couple of lumps beside it, so the puddle reads from across the yard
    heap = tex_mat(f"{A} heap", tex_mud(R), 0.36, ext='REPEAT')
    for i, (x, y, r, h) in enumerate(((0.0, 0.0, 0.45, 0.4), (-0.4, 0.22, 0.22, 0.18), (0.32, 0.26, 0.18, 0.13), (0.12, -0.32, 0.16, 0.11))):
        lathe(kit, f"{A} heap {i}", [(r, 0.02), (r * 0.9, h * 0.35), (r * 0.65, h * 0.75), (r * 0.3, h * 0.97), (0, h)], heap, root,
              sides=10, loc=(x, y, 0.0))
    bub = kit.empty(f"{A} bubbles", root, (0, 0, 0.03))
    bm_mat = solid(kit, f"{A} bubble", MUD_L, 0.45, shade=MUD)
    for i, (x, y, r) in enumerate(((0.2, -0.1, 0.05), (-0.3, 0.15, 0.035), (0.05, 0.25, 0.03), (-0.1, -0.25, 0.04),
                                   (0.4, 0.2, 0.025))):
        lathe(kit, f"{A} bubble {i}", [(r, 0.0), (r * 0.8, r * 0.6), (r * 0.4, r * 0.9), (0, r)], bm_mat, bub, sides=6,
              loc=(x, y, 0.0))
        lowball(kit, f"{A} glint {i}", (x - r * 0.3, y - r * 0.3, r * 0.8), (r * 0.2, r * 0.2, r * 0.1),
                solid(kit, "glint", WHITE, 0.9), bub, smooth=False)
    stick = solid(kit, f"{A} stick", "#8a5a3a", 0.3, shade="#6a3a2a")
    tube(kit, f"{A} stick", [(0.35, -0.3, 0.02), (0.45, -0.32, 0.2), (0.5, -0.35, 0.34)], [0.018, 0.014, 0.01], stick, root,
         sides=5)
    tube(kit, f"{A} twig", [(0.46, -0.325, 0.24), (0.55, -0.3, 0.29)], [0.008, 0.005], stick, root, sides=4)
    lowball(kit, f"{A} leaf", (0.56, -0.3, 0.3), (0.03, 0.015, 0.012), solid(kit, "leaf", LEAF, 0.4), root, smooth=False)
    gummy_worm(kit, f"{A} worm", root, [(-0.5, -0.1, 0.03), (-0.56, -0.16, 0.05), (-0.62, -0.12, 0.04), (-0.66, -0.18, 0.03)],
               0.012)
    socket(kit, A, "use point", root, (0, 0, 0.03))


def tex_plank(rand):
    c = Canvas(32, 16, "#e8a862")
    c.speckle(rand, ["#c47f3a", "#f2bc72"], 60)
    c.rect(0, 0, 31, 0, "#a8642a"); c.rect(0, 15, 31, 15, "#a8642a")
    for x in range(0, 32, 9):
        c.rect(x, 6, x + 4, 6, "#c47f3a")
    return c


def tex_soil(rand):
    c = Canvas(32, 32, "#5a3a4c")
    c.speckle(rand, ["#6b4a5a", "#4a2c40", "#7d5a6a"], 260)
    return c


def strawberry(kit, name, parent, loc, s, t_berry, leaf, rot=(0, 0, 0)):
    p = kit.empty(name, parent, loc, rot)
    lathe(kit, f"{name} berry", [(0, -0.05 * s), (0.02 * s, -0.035 * s), (0.028 * s, -0.01 * s), (0.024 * s, 0.006 * s),
                                 (0, 0.01 * s)], t_berry, p, sides=6)
    cap = kit.link(f"{name} cap", star_mesh(f"{name} cap", 5, 0.026 * s, 0.01 * s), p, (0, 0, 0.011 * s), (90, 0, 0))
    cap.data.materials.append(leaf)
    return p


def leaf_cluster(kit, name, parent, loc, s, mat, R):
    """Strawberry plant: 5 trefoil leaves on short stems radiating from a crown (one mesh)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    base = Vector(loc)
    for k in range(5):
        a = 2 * math.pi * k / 5 + R.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), 0))
        tip = base + d * 0.16 * s + Vector((0, 0, 0.1 * s + R.uniform(0, 0.04) * s))
        side = Vector((-d.y, d.x, 0))
        for q, off in enumerate((-0.6, 0.0, 0.6)):
            dd = (d + side * off).normalized()
            c = tip + dd * 0.05 * s
            vs = [bm.verts.new(tip), bm.verts.new(c + Vector((-dd.y, dd.x, 0)) * 0.035 * s + Vector((0, 0, 0.01 * s))),
                  bm.verts.new(tip + dd * 0.1 * s - Vector((0, 0, 0.02 * s))),
                  bm.verts.new(c - Vector((-dd.y, dd.x, 0)) * 0.035 * s + Vector((0, 0, 0.01 * s)))]
            fc = bm.faces.new(vs)
            for lp, uv in zip(fc.loops, ((0.05, 0.5), (0.5, 0.95), (0.95, 0.5), (0.5, 0.05))):
                lp[uvl].uv = uv
        st = [bm.verts.new(base + side * 0.008 * s), bm.verts.new(base - side * 0.008 * s), bm.verts.new(tip)]
        fc = bm.faces.new(st)
        for lp in fc.loops:
            lp[uvl].uv = (0.5, 0.5)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def tex_leaf_h(rand):
    c = Canvas(16, 16, LEAF)
    c.rect(0, 7, 15, 8, "#8affb0")
    for x in range(2, 15, 3):
        c.set(x, 5, "#2fbf5a"); c.set(x, 10, "#2fbf5a")
    c.rect(0, 0, 15, 0, LEAF_D); c.rect(0, 15, 15, 15, LEAF_D)
    return c


def tex_berry():
    c = Canvas(12, 8, RED)
    for y in range(0, 7, 2):
        for x in range(y % 4 // 2, 12, 3):
            c.set(x, y, YEL)
    c.rect(0, 0, 11, 0, DRED)
    c.rect(0, 7, 11, 7, "#ff6a8a")
    return c


def build_strawberry_patch(kit, root, A):
    R = kit.rand
    W, D, H, t = 1.6, 0.8, 0.3, 0.06
    plank = tex_mat(f"{A} plank", tex_plank(R), ext='REPEAT')
    for sy in (1, -1):
        tbox(kit, f"{A} side {sy}", (0, sy * (D - t) / 2, H / 2), (W, t, H), plank, root, uv={'all': (0, 0, W / 0.8, 1.0)})
    for sx in (1, -1):
        tbox(kit, f"{A} end {sx}", (sx * (W - t) / 2, 0, H / 2), (t, D - 2 * t, H), plank, root, uv={'all': (0, 0, 1.0, 1.0)})
        for sy in (1, -1):
            tbox(kit, f"{A} post {sx} {sy}", (sx * (W / 2 - 0.02), sy * (D / 2 - 0.02), H / 2 + 0.03), (0.07, 0.07, H + 0.06),
                 solid(kit, "post", "#c47f3a", shade="#a8642a"), root)
    tbox(kit, f"{A} soil", (0, 0, H - 0.04), (W - 2 * t, D - 2 * t, 0.04), tex_mat(f"{A} soil", tex_soil(R), 0.2, ext='REPEAT'),
         root, uv={'all': (0, 0, 2, 1)})
    leaf = tex_mat(f"{A} leaves", tex_leaf_h(R), 0.4)
    spots = [(-0.55, -0.12), (-0.25, 0.12), (0.05, -0.1), (0.35, 0.12), (0.6, -0.08), (-0.6, 0.18), (0.25, -0.16)]
    for i, (x, y) in enumerate(spots):
        leaf_cluster(kit, f"{A} plant {i}", root, (x, y, H - 0.02), 1.0 + 0.2 * (i % 2), leaf, R)
    berries = kit.empty(f"{A} berries", root, (0, 0, H))
    t_berry = tex_mat(f"{A} berry", tex_berry(), 0.45, ext='REPEAT')
    lm = solid(kit, f"{A} berry leaf", LEAF, 0.4, shade=LEAF_D)
    for i in range(14):
        x, y = spots[i % len(spots)]
        a = R.uniform(0, 2 * math.pi)
        strawberry(kit, f"{A} berry {i}", berries, (x + math.cos(a) * 0.13, y + math.sin(a) * 0.1, 0.05 + R.uniform(0, 0.05)),
                   1.5, t_berry, lm, (R.uniform(-30, 30), R.uniform(-30, 30), R.uniform(0, 360)))
    # little seed-packet sign
    sp = kit.empty(f"{A} sign", root, (0.68, -D / 2 - 0.02, 0.0))
    tbox(kit, f"{A} sign stake", (0, 0, 0.25), (0.02, 0.02, 0.5), solid(kit, "stake", "#c47f3a"), sp)
    tbox(kit, f"{A} sign", (0, -0.015, 0.47), (0.16, 0.012, 0.11), tex_mat(f"{A} sign", tex_patch_sign()), sp,
         uv={'all': (0, 0, 0.05, 0.05), 'ny': (0, 0, 1, 1)})
    socket(kit, A, "use point", root, (0, -D / 2 - 0.4, 0))


def tex_patch_sign():
    c = Canvas(32, 24, WHITE)
    c.rect(0, 0, 31, 1, PINK); c.rect(0, 22, 31, 23, PINK)
    txt_c(c, "BERRY", 16, 19, RED)
    disc(c, 16, 8, 4, RED); c.dots([(15, 8), (17, 6), (14, 6)], YEL); c.rect(14, 12, 18, 13, LEAF)
    return c


def tex_bark(rand):
    c = Canvas(32, 32, BARK)
    for x in range(0, 32, 4):
        for y in range(32):
            if (y + x * 3) % 7 < 4:
                c.set(x + (y % 3 == 0), y, BARK_D)
    c.speckle(rand, ["#8a5a6a"], 60)
    return c


def tex_leaf_canopy(rand, base):
    c = Canvas(16, 16, base)
    c.speckle(rand, [hex_scale(base, 0.85), hex_scale(base, 1.15)], 70)
    return c


def build_nut_tree(kit, root, A):
    R = kit.rand
    bark = tex_mat(f"{A} bark", tex_bark(R), 0.28, ext='REPEAT')
    tube(kit, f"{A} trunk", [(0, 0, -0.05), (0, 0, 0.6), (0.05, 0.0, 2.2), (0.1, 0.04, 3.2), (0.12, 0.04, 3.9)],
         [0.55, 0.38, 0.35, 0.3, 0.24], bark, root, sides=8)
    for i, (a, ln) in enumerate(((0.3, 0.9), (2.4, 0.8), (4.4, 1.0))):   # root flare
        ca, sa = math.cos(a), math.sin(a)
        tube(kit, f"{A} root {i}", [(ca * 0.2, sa * 0.2, 0.35), (ca * 0.5, sa * 0.5, 0.08), (ca * ln, sa * ln, -0.02)],
             [0.16, 0.1, 0.04], bark, root, sides=5)
    canopy = kit.empty(f"{A} canopy", root, (0.12, 0.04, 3.7))
    for i, (d, z, ln, r) in enumerate((((1, 0.2, 0.5), 0.0, 2.0, 0.17), ((-1, 0.3, 0.55), 0.1, 2.0, 0.16),
                                        ((0.2, -1, 0.6), -0.1, 1.8, 0.15), ((-0.2, 1, 0.5), 0.0, 1.8, 0.15))):
        dv = Vector(d).normalized()
        tube(kit, f"{A} branch {i}", [(0, 0, z), tuple(dv * ln * 0.5 + Vector((0, 0, z))), tuple(dv * ln + Vector((0, 0, z)))],
             [r, r * 0.7, r * 0.35], bark, canopy, sides=6)
    leaves = [tex_mat(f"{A} leaves {k}", tex_leaf_canopy(R, c), 0.3) for k, c in enumerate(("#2fae66", "#3fcf7a", "#26995a"))]
    clumps = [((0, 0, 1.9), (3.0, 2.8, 2.0)), ((2.3, 0.4, 1.1), (1.9, 1.8, 1.5)), ((-2.3, 0.3, 1.2), (1.9, 1.9, 1.5)),
              ((0.3, -2.2, 1.1), (1.8, 1.7, 1.4)), ((-0.2, 2.3, 1.2), (1.9, 1.7, 1.4)), ((0.6, 0.2, 3.4), (2.0, 1.9, 1.3)),
              ((1.6, -1.5, 2.2), (1.4, 1.4, 1.2)), ((-1.6, -1.4, 2.3), (1.4, 1.3, 1.2))]
    for i, (c, r) in enumerate(clumps):
        lowball(kit, f"{A} clump {i}", c, r, leaves[i % 3], canopy)
    mats = (solid(kit, "acorn", "#c47f3a", 0.4, shade="#a8642a"), solid(kit, "acorn cap", "#7a4a2a", 0.32, shade="#5e3418"))
    for i in range(18):   # acorns hanging on the canopy surface
        c, r = clumps[i % len(clumps)]
        a = R.uniform(0, 2 * math.pi)
        e = R.uniform(-0.6, 0.15)
        n = Vector((math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e)))
        p = Vector(c) + Vector((n.x * r[0], n.y * r[1], n.z * r[2])) * 0.97
        acorn(kit, f"{A} acorn {i}", canopy, tuple(p), 0.26, (180 + R.uniform(-20, 20), R.uniform(-20, 20), 0), mats)
    socket(kit, A, "drop", root, (0.12, -3.2, 4.2))
    socket(kit, A, "shake point", root, (0, -0.65, 0))


def tex_steel(rand):
    c = Canvas(32, 32, "#c9c2f0")
    c.speckle(rand, ["#b4acdf", "#ddd6fa"], 120)
    for y in range(0, 32, 8):
        c.rect(0, y, 31, y, "#a39bd0")
    return c


def ring_plate(kit, name, W, H, r, cz, y0, y1, mat, parent, n=16):
    """Plate in the XZ plane (thickness y0..y1, bottom at z = 0) with a round hole of radius r centered at height cz."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    corner = [math.atan2(H - cz, W / 2), math.atan2(H - cz, -W / 2), math.atan2(-cz, -W / 2) + 2 * math.pi,
              math.atan2(-cz, W / 2) + 2 * math.pi]
    angs = sorted([2 * math.pi * k / n for k in range(n)] + corner)

    def outer(t):
        dx, dz = math.cos(t), math.sin(t)
        kx = (W / 2) / abs(dx) if abs(dx) > 1e-6 else 1e9
        kz = ((H - cz) if dz > 0 else cz) / abs(dz) if abs(dz) > 1e-6 else 1e9
        k = min(kx, kz)
        return dx * k, cz + dz * k
    m = len(angs)
    for side, y in (("f", y0), ("b", y1)):
        inner = [bm.verts.new((math.cos(t) * r, y, cz + math.sin(t) * r)) for t in angs]
        outv = [bm.verts.new((outer(t)[0], y, outer(t)[1])) for t in angs]
        for k in range(m):
            k2 = (k + 1) % m
            vs = [inner[k], inner[k2], outv[k2], outv[k]]
            fc = bm.faces.new(vs if side == "b" else vs[::-1])
            for lp in fc.loops:
                lp[uvl].uv = (lp.vert.co.x / 2 + 0.5, lp.vert.co.z / 2)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def build_vault(kit, root, A):
    """Wall vault 2 m wide, 2.4 m tall, 0.6 m deep. Front at y = -0.3, round door on 'Vault door' hinged at its left
    (-X) edge, rotating around Z. Interior shelf with gold bars, 'Vault socket loot' inside."""
    R = kit.rand
    W, H, D = 2.0, 2.4, 0.6
    steel = tex_mat(f"{A} steel", tex_steel(R), 0.3, ext='REPEAT')
    dark = solid(kit, f"{A} interior", "#3d3358", 0.15, shade="#2f2848")
    gold = solid(kit, f"{A} gold", GOLD, 0.7, shade=GOLD_D)
    cz, r = 1.15, 0.78
    # body: back, sides, top, bottom, front frame pieces around the round opening (simple: 4 boxes + corner wedges)
    tbox(kit, f"{A} back", (0, D / 2 - 0.05, H / 2), (W, 0.1, H), steel, root, uv={'all': (0, 0, 2, 2.4)})
    for sx in (1, -1):
        tbox(kit, f"{A} side {sx}", (sx * (W / 2 - 0.05), 0, H / 2), (0.1, D, H), steel, root, uv={'all': (0, 0, 0.6, 2.4)})
    tbox(kit, f"{A} top", (0, 0, H - 0.05), (W, D, 0.1), steel, root, uv={'all': (0, 0, 2, 0.6)})
    tbox(kit, f"{A} bottom", (0, 0, 0.05), (W, D, 0.1), steel, root, uv={'all': (0, 0, 2, 0.6)})
    ring_plate(kit, f"{A} front", W, H, r, cz, -D / 2, -D / 2 + 0.12, steel, root)
    tube(kit, f"{A} jamb", [(0, -D / 2 - 0.02, cz), (0, D / 2 - 0.1, cz)], r, dark, root, sides=16, side=(1, 0, 0),
         caps=(False, False))
    lathe(kit, f"{A} jamb ring", [(r, 0), (r + 0.1, 0), (r + 0.1, 0.05), (r, 0.05)], gold, root, sides=16, closed=True,
          loc=(0, -D / 2 - 0.02, cz), rot=(90, 0, 0))
    # interior shelf and gold bars
    tbox(kit, f"{A} shelf", (0, 0.05, cz - 0.15), (1.4, 0.4, 0.05), steel, root, uv={'all': (0, 0, 1, 0.3)})
    bar = solid(kit, f"{A} gold bar", GOLD, 0.9, shade=GOLD_L)
    k = 0
    for row in range(2):
        for i in range(4 - row):
            x = (i - (3 - row) / 2) * 0.17
            tbox(kit, f"{A} gold bar {k}", (x, 0.05, cz - 0.1 + row * 0.06), (0.15, 0.24, 0.06), bar, root, taper=(0.8, 0.85))
            k += 1
    for i, (x, z) in enumerate(((-0.3, cz + 0.25), (0.25, cz + 0.3))):
        lowball(kit, f"{A} coin pile {i}", (x, 0.1, cz - 0.12 + 0.06), (0.12, 0.1, 0.05), gold, root)
    kit.empty(f"{A} socket loot", root, (0, 0.0, cz - 0.1))
    # door on its hinge (left edge, -X)
    hinge = kit.empty(f"{A} door", root, (-r - 0.04, -D / 2 - 0.02, cz))
    door = tube(kit, f"{A} door slab", [(r + 0.04, -0.14, 0), (r + 0.04, 0.0, 0)], r + 0.03, steel, hinge, sides=16,
                side=(1, 0, 0))
    torus(kit, f"{A} door rim", r + 0.0, 0.04, gold, hinge, loc=(r + 0.04, -0.14, 0), rot=(90, 0, 0), seg=16, sides=5)
    wheel = kit.empty(f"{A} wheel", hinge, (r + 0.04, -0.2, 0))
    torus(kit, f"{A} wheel ring", 0.28, 0.025, gold, wheel, rot=(90, 0, 0), seg=12, sides=5)
    for i in range(3):
        a = 60 * i
        tbox(kit, f"{A} spoke {i}", (0, 0, 0), (0.56, 0.03, 0.03), gold, wheel, rot=(0, a, 0))
    lowball(kit, f"{A} hub", (0, 0, 0), (0.07, 0.05, 0.07), gold, wheel)
    for i in range(8):
        a = 2 * math.pi * i / 8
        lowball(kit, f"{A} bolt {i}", (r + 0.04 + math.cos(a) * (r - 0.08), -0.15, math.sin(a) * (r - 0.08)), (0.04, 0.03, 0.04),
                solid(kit, "bolt", "#e6e0ff", 0.4), hinge, smooth=False)
    for i, z in enumerate((0.4, -0.4)):
        tbox(kit, f"{A} hinge {i}", (0.02, -0.08, z), (0.12, 0.12, 0.22), gold, hinge)
    tbox(kit, f"{A} dial", (0, 0, 0), (0.14, 0.04, 0.14), solid(kit, "dial", "#3a3050", 0.3), hinge,
         loc=(r + 0.04 + 0.42, -0.17, 0.4), rot=(0, 45, 0))
    # skull? no: a big pixel "$" plate above the door
    tbox(kit, f"{A} plate", (0, -D / 2 - 0.03, H - 0.22), (0.7, 0.04, 0.22), tex_mat(f"{A} plate", tex_vault_plate()), root,
         uv={'all': (0, 0, 0.05, 0.05), 'ny': (0, 0, 1, 1)})
    socket(kit, A, "use point", root, (0, -D / 2 - 0.9, 0))


def tex_vault_plate():
    c = Canvas(48, 16, GOLD)
    c.rect(0, 0, 47, 0, GOLD_D); c.rect(0, 15, 47, 15, GOLD_D)
    txt_c(c, "VAULT", 24, 12, "#7a4a10", 2)
    return c


def tex_hazard_plate():
    c = Canvas(32, 32, "#3d3358")
    for i in range(-32, 64, 8):
        for t in range(4):
            for y in range(32):
                x = i + t + y
                if 0 <= x < 32 and (y < 4 or y > 27 or x < 4 or x > 27):
                    c.set(x, y, YEL)
    c.rect(6, 6, 25, 25, RED); c.rect(8, 8, 23, 23, "#ff4a68")
    disc(c, 16, 16, 4, WHITE); disc(c, 16, 16, 2, RED)
    return c


def build_pressure_plate(kit, root, A):
    W = 1.0
    frame = solid(kit, f"{A} frame", "#9d95d4", 0.3, shade="#8a82c0")
    for sy in (1, -1):
        tbox(kit, f"{A} frame y {sy}", (0, sy * (W / 2 - 0.04), 0.035), (W, 0.08, 0.07), frame, root)
    for sx in (1, -1):
        tbox(kit, f"{A} frame x {sx}", (sx * (W / 2 - 0.04), 0, 0.035), (0.08, W - 0.16, 0.07), frame, root)
    tbox(kit, f"{A} pit", (0, 0, 0.005), (W - 0.16, W - 0.16, 0.01), solid(kit, "pit", INK, 0.05), root)
    plate = kit.empty(f"{A} plate", root, (0, 0, 0.0))
    tbox(kit, f"{A} plate", (0, 0, 0.065), (W - 0.18, W - 0.18, 0.05), tex_mat(f"{A} hazard", tex_hazard_plate(), 0.45), plate,
         uv={'all': (0, 0, 0.1, 0.1), 'pz': (0, 0, 1, 1)})
    cable = solid(kit, f"{A} cable", "#2a2238", 0.2)
    tube(kit, f"{A} cable", [(W / 2, 0.2, 0.03), (W / 2 + 0.3, 0.25, 0.02), (W / 2 + 0.7, 0.1, 0.02), (W / 2 + 1.1, 0.3, 0.02),
                             (W / 2 + 1.6, 0.2, 0.02)], 0.02, cable, root, sides=5)
    tbox(kit, f"{A} junction box", (W / 2 + 1.7, 0.2, 0.06), (0.18, 0.14, 0.12), solid(kit, "junction", YEL), root)
    tbox(kit, f"{A} lamp", (W / 2 + 1.7, 0.2, 0.135), (0.05, 0.05, 0.03), solid(kit, "lamp", RED, 1.4), root)
    socket(kit, A, "stand point", root, (0, 0, 0.09))


def tex_boom(rand):
    c = Canvas(64, 8, WHITE)
    for x in range(0, 64, 16):
        c.rect(x, 0, x + 7, 7, RED)
    return c


def tex_permit():
    c = Canvas(64, 32, WHITE)
    c.rect(0, 0, 63, 2, RED); c.rect(0, 29, 63, 31, RED); c.rect(0, 0, 2, 31, RED); c.rect(61, 0, 63, 31, RED)
    txt_c(c, "PERMIT", 32, 25, RED, 2)
    txt_c(c, "ONLY", 32, 13, INK, 2)
    return c


def tex_booth(rand):
    c = Canvas(32, 32, "#b8b0e8")
    c.speckle(rand, ["#a8a0d8", "#c8c0f4"], 60)
    c.rect(0, 0, 31, 5, PINK)
    c.rect(4, 12, 27, 26, GLASS); c.rect(4, 12, 27, 12, WHITE); c.rect(15, 12, 16, 26, WHITE)
    c.dots([(7, 22), (8, 21), (9, 20)], "#6f8cff")
    return c


def build_gate(kit, root, A):
    """Boom gate across a 10 m road (road along Y). Origin on the road center line; guard post on +X, arm on 'Gate arm'
    pivoting around the Y axis at the post top (arm closed along -X)."""
    R = kit.rand
    px = 5.4
    steel = solid(kit, f"{A} steel", STEEL, 0.35, shade="#a9a2e0")
    post = tex_mat(f"{A} post", tex_boom(R), ext='REPEAT')
    # pedestal with the motor housing
    tbox(kit, f"{A} pedestal", (px, 0, 0.5), (0.4, 0.4, 1.0), solid(kit, f"{A} housing", YEL, 0.4, shade="#e0b21a"), root)
    tbox(kit, f"{A} housing top", (px, 0, 1.03), (0.46, 0.46, 0.06), steel, root)
    tbox(kit, f"{A} counterweight", (px + 0.55, 0, 1.15), (0.35, 0.2, 0.25), steel, root)
    arm = kit.empty(f"{A} arm", root, (px, -0.25, 1.15))
    arm_ob = tube(kit, f"{A} arm", [(0.55, 0, 0), (0.0, 0, 0), (-(px + 4.4) + 0.4, 0, 0), (-(px + 4.4), 0, 0)],
                  [0.07, 0.07, 0.06, 0.05], post, arm, sides=6, side=(0, 0, 1), v=(0.0, 1.0))
    me = arm_ob.data  # stripes repeat along the 9.8 m arm
    uv = me.uv_layers.active.data
    for i in range(len(uv)):
        uv[i].uv = (uv[i].uv[0], uv[i].uv[1] * 6.0)
    tube(kit, f"{A} hub", [(0, -0.06, 0), (0, 0.06, 0)], 0.12, steel, arm, sides=8, side=(1, 0, 0))
    for i, x in enumerate((-2.0, -5.0, -8.0)):
        tbox(kit, f"{A} reflector {i}", (x, -0.07, 0), (0.12, 0.01, 0.08), solid(kit, "reflector", ORNG, 1.2), arm)
    sign = kit.empty(f"{A} sign", arm, (-4.6, 0.0, -0.08))
    tbox(kit, f"{A} sign", (0, 0, -0.32), (1.2, 0.04, 0.6), tex_mat(f"{A} permit", tex_permit()), sign,
         uv={'all': (0, 0, 0.05, 0.05), 'ny': (0, 0, 1, 1), 'py': (0, 0, 1, 1)})
    for sx in (1, -1):
        tbox(kit, f"{A} sign hanger {sx}", (sx * 0.4, 0, 0.0), (0.03, 0.03, 0.1), steel, sign)
    tube(kit, f"{A} rest post", [(-4.1, -0.25, 0), (-4.1, -0.25, 1.05)], 0.05, steel, root, sides=6)
    tbox(kit, f"{A} rest fork", (-4.1, -0.25, 1.08), (0.18, 0.08, 0.06), steel, root)
    # guard booth beside the post
    booth = kit.empty(f"{A} booth", root, (px + 1.4, 1.2, 0))
    bt = tex_mat(f"{A} booth", tex_booth(R))
    tbox(kit, f"{A} booth", (0, 0, 1.2), (1.5, 1.5, 2.4), bt, booth,
         uv={'all': (0, 0, 1, 1), 'pz': (0.2, 0.2, 0.3, 0.3), 'nz': (0.2, 0.2, 0.3, 0.3)})
    tbox(kit, f"{A} booth roof", (0, 0, 2.48), (1.8, 1.8, 0.16), solid(kit, "booth roof", PINK, 0.4, shade="#e83a8f"), booth)
    tbox(kit, f"{A} booth light", (0, 0, 2.62), (0.2, 0.2, 0.14), solid(kit, "booth light", RED, 1.6), booth)
    socket(kit, A, "guard", root, (px + 1.4, 0.3, 0))


def tex_horn():
    c = Canvas(16, 16, WHITE)
    c.rect(0, 0, 15, 3, PINK)
    c.rect(0, 12, 15, 15, "#e6dcd2")
    return c


def build_loudspeaker(kit, root, A):
    steel = solid(kit, f"{A} steel", STEEL, 0.35, shade="#a9a2e0")
    tbox(kit, f"{A} base", (0, 0, 0.02), (0.36, 0.24, 0.04), steel, root)
    tube(kit, f"{A} post", [(0, 0, 0.04), (0, 0, 0.28)], 0.03, steel, root, sides=6)
    tbox(kit, f"{A} bar", (0, 0, 0.3), (0.42, 0.06, 0.05), steel, root)
    horn = tex_mat(f"{A} horn", tex_horn(), ext='REPEAT')
    for sx in (1, -1):
        h = kit.empty(f"{A} horn {'L' if sx > 0 else 'R'}", root, (sx * 0.15, 0.04, 0.36), (0, 0, sx * 38))
        lathe(kit, f"{A} horn {sx}", [(0.045, 0.0), (0.05, 0.05), (0.07, 0.14), (0.125, 0.26), (0.135, 0.27), (0.1, 0.26), (0, 0.21)],
              horn, h, sides=10, rot=(90, 0, 0))
        tube(kit, f"{A} driver {sx}", [(0, 0.08, 0), (0, 0.0, 0)], 0.065, solid(kit, f"{A} driver", PINK, 0.4), h, sides=8,
             side=(1, 0, 0))
        tbox(kit, f"{A} bracket {sx}", (0, 0.02, -0.06), (0.04, 0.06, 0.08), steel, h)
    tube(kit, f"{A} cable", [(0, 0.1, 0.04), (0.0, 0.2, 0.02), (0.1, 0.3, 0.01)], 0.012, solid(kit, "cable", INK, 0.2), root,
         sides=4)
    socket(kit, A, "mount", root, (0, 0, 0))


# ---------------------------------------------------------------- assembly
def run(kit, root, A, fn, *a):
    fn(kit, root, A, *a)
    for ob in root.children_recursive:
        if not ob.name.startswith(A):
            ob.name = f"{A} {ob.name}"


def entry(A, fn, *a):
    return (A, lambda kit, root: run(kit, root, A, fn, *a))


ITEMS = [
    ("Mud Bucket", build_mud_bucket, ()),
    ("Iced Coffee", build_iced_coffee, ()),
    ("Nut Sack", build_nut_sack, ()),
    ("Gold Leaf", build_gold_leaf, ()),
    ("Cone", build_cone, ("sugar",)),
    ("Waffle Cone", build_cone, ("waffle",)),
    ("Double Waffle Cone", build_cone, ("double",)),
]
ITEMS += [(f"Scoop {fl}", build_scoop, (fl,)) for fl in FLAVORS]
ITEMS += [(f"Flavor Tub {fl}", build_tub, (fl,)) for fl in FLAVORS]
ITEMS += [
    ("Lunch Money", build_lunch_money, ()),
    ("Thought Bubble", build_thought_bubble, ()),
    ("Mud Puddle", build_mud_puddle, ()),
    ("Strawberry Patch", build_strawberry_patch, ()),
    ("Nut Tree", build_nut_tree, ()),
    ("Vault", build_vault, ()),
    ("Pressure Plate", build_pressure_plate, ()),
    ("Gate", build_gate, ()),
    ("Loudspeaker", build_loudspeaker, ()),
]
ASSETS = [entry(A, fn, *a) for A, fn, a in ITEMS]


def build_cone_stack(kit, root):
    """Every cone with three scoops stacked on its sockets, plus a thought bubble with a scoop icon."""
    lookup = dict(ASSETS)
    for i, (cn, fls) in enumerate((("Cone", ("Mud", "Strawberry", "Coffee")),
                                   ("Waffle Cone", ("Rocky Road", "Gold Leaf", "Strawberry")),
                                   ("Double Waffle Cone", ("Coffee", "Rocky Road", "Gold Leaf")))):
        p = kit.empty(f"stack {i}", root, ((i - 1) * 0.22, 0, 0))
        lookup[cn](kit, p)
        bpy.context.view_layer.update()
        for k, fl in enumerate(fls):
            s = next(o for o in p.children_recursive if o.name.startswith(f"{cn} socket scoop {k + 1}"))
            sp = kit.empty(f"stack scoop {i} {k}", s)
            lookup[f"Scoop {fl}"](kit, sp)
    tb = kit.empty("bubble", root, (0.5, 0.05, 0.35))
    lookup["Thought Bubble"](kit, tb)
    bpy.context.view_layer.update()
    s = next(o for o in tb.children_recursive if o.name.startswith("Thought Bubble socket icon"))
    ic = kit.empty("bubble icon", s, (0, 0, -0.04), (0, 0, 0), (1.6, 1.6, 1.6))
    lookup["Scoop Strawberry"](kit, ic)


SCENES = [dict(name="cone stacks", build=build_cone_stack, cam=((0.15, -1.6, 0.45), (0.15, 0, 0.25), 50), res=(1600, 900))]
