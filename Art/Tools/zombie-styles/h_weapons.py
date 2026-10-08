from style_H import *
# Style H weapons batch: the full gun set, the roof turret, the scooper tool, the sprinkle jar and a gun-rack scene.
# Guns: barrel along -Y, grip down, root at the receiver. Sockets are empties named '<Asset> socket <purpose>';
# moving parts are empties named '<Asset> <part>' placed on their hinge or axis.

SPR = (PINK, BLUE, YEL, MINT, WHITE, ORNG, PURP)
VAN = "#fff1c7"; BERRY = "#ff8fc8"


# ---------------------------------------------------------------- helpers
def sock(kit, asset, purpose, parent, loc, rot=(0, 0, 0)):
    e = kit.empty(f"{asset} socket {purpose}", parent, loc, rot)
    e.empty_display_size = 0.03
    return e


def gun_mats(kit):
    return dict(steel=solid(kit, "steel", STEEL, shade="#a9a2e0"), pink=solid(kit, "gun pink", PINK),
                yel=solid(kit, "gun yellow", YEL), ink=solid(kit, "gun dark", INK, 0.1),
                grip=tex_mat("weapons grip", tex_grip()),
                cream={c: solid(kit, f"cream {c}", c, 0.45 if c != CHOC else 0.25, shade="#4e2812" if c == CHOC else None)
                       for c in (VAN, BERRY, CHOC, "#9ff5d8")})


def grip_trigger(kit, N, root, y, zb, m, angle=16):
    """Pistol grip centered at y under a receiver whose bottom is zb, trigger on a pivot, guard. Adds the grip socket."""
    tbox(kit, f"{N} grip", (0, y, zb - 0.037), (0.04, 0.045, 0.1), m['grip'], root, rot=(angle, 0, 0), taper=(1.0, 1.12))
    trig = kit.empty(f"{N} trigger", root, (0, y - 0.058, zb))
    tbox(kit, f"{N} trigger blade", (0, 0.002, -0.014), (0.008, 0.01, 0.028), m['yel'], trig, rot=(-18, 0, 0))
    tube(kit, f"{N} guard", [(0, y - 0.09, zb), (0, y - 0.092, zb - 0.032), (0, y - 0.07, zb - 0.047),
                             (0, y - 0.028, zb - 0.046)], 0.0065, m['yel'], root, sides=4, side=(1, 0, 0))
    sock(kit, N, "grip", root, (0, y, zb - 0.037), (angle, 0, 0))


def sprinkle_bits(kit, N, parent, n, center, rx, ry, z, size=0.012):
    mats = [solid(kit, "gun sprinkle " + c, c, 0.6) for c in SPR[:5]]
    R = kit.rand
    for i in range(n):
        tbox(kit, f"{N} sprinkle {i}", (0, 0, 0), (size * 0.35, size, size * 0.35), mats[i % 5], parent,
             loc=(center[0] + R.uniform(-rx, rx), center[1] + R.uniform(-ry, ry), z),
             rot=(R.uniform(-15, 15), 0, R.uniform(0, 180)))


def tex_body(base, dark, light, stripe, mark=YEL):
    """tex_gun_body recolored: dark base row, stripe band, light top, little cone mark."""
    c = Canvas(32, 16, base)
    c.rect(0, 0, 31, 1, dark)
    c.rect(0, 6, 31, 8, stripe)
    c.rect(0, 14, 31, 15, light)
    for x in range(2, 31, 4):
        c.set(x, 3, dark); c.set(x, 11, dark)
    for row in range(5):
        c.rect(22 - row // 2, 9 + row, 22 + row // 2, 9 + row, mark)
    return c


def tex_smg_body(rand):
    c = Canvas(32, 16, BLUE)
    c.rect(0, 0, 31, 1, "#1d5fcc")
    c.rect(0, 14, 31, 15, "#8cc0ff")
    c.rect(0, 5, 31, 9, WHITE)
    for x in range(0, 32, 2):
        col = SPR[(x // 2) % 6]
        if rand.random() < 0.5:
            c.rect(x, 6 + rand.randint(0, 2), x + 1, 6 + rand.randint(0, 2), col)
        else:
            y = rand.randint(5, 8)
            c.rect(x, y, x, y + 1, col)
    for x in range(1, 31, 4):
        c.set(x, 3, "#1d5fcc"); c.set(x + 2, 11, "#1d5fcc")
    return c


def tex_candy(a, b, period=6):
    c = Canvas(16, 32, a)
    for y in range(32):
        for x in range(16):
            if (x + y) % period < period // 2:
                c.set(x, y, b)
    return c


def tex_shroud():
    c = Canvas(16, 16, STEEL)
    for y in range(1, 16, 4):
        for x in range(0, 16, 3):
            c.set(x + (y // 4) % 2, y, INK); c.set(x + (y // 4) % 2, y + 1, "#6a5fb0")
    c.rect(0, 0, 15, 0, "#a9a2e0"); c.rect(0, 15, 15, 15, "#a9a2e0")
    return c


def tex_jar(rand):
    """Sprinkle jar (64 px around, square texels on the jar): rainbow sprinkles to the shoulder, label, glass glint."""
    c = Canvas(64, 32, "#cfe9ff")
    for y in range(1, 24):
        for x in range(64):
            c.set(x, y, rand.choice(SPR[:4] + (ORNG, PURP, WHITE)))
    c.rect(0, 9, 63, 17, WHITE)
    c.rect(0, 9, 63, 9, PINK); c.rect(0, 17, 63, 17, PINK)
    text(c, "SPRINKLES", 21, 15, PINK)
    c.rect(22, 2, 23, 7, "#ffffff"); c.rect(22, 19, 23, 22, "#ffffff")
    c.rect(0, 0, 63, 0, "#9cc8f0")
    return c


def tex_banana(rand):
    c = Canvas(12, 32, YEL)
    for x in range(0, 12, 2):
        c.rect(x, 0, x, 31, "#f5c832")
    c.rect(0, 0, 11, 2, CHOC); c.rect(0, 3, 11, 4, "#b8d84a")
    c.rect(0, 29, 11, 31, "#3a2010")
    c.speckle(rand, ["#c9952a", CHOC], 14, 6, 27)
    return c


def tex_licorice():
    c = Canvas(8, 32, RED)
    for y in range(32):
        for x in range(8):
            if (x + y) % 4 < 1:
                c.set(x, y, DRED)
            elif (x + y) % 4 == 2:
                c.set(x, y, "#ff6a7e")
    return c


def tex_plate():
    c = Canvas(32, 32, STEEL)
    for y in range(32):
        for x in range(32):
            if x < 3 or x > 28 or y < 3 or y > 28:
                c.set(x, y, INK if ((x + y) // 3) % 2 else YEL)
    c.speckle(random.Random(3), ["#a9a2e0"], 40, 4, 27)
    return c


def tex_scoop_grip():
    c = Canvas(16, 16, PINK)
    for y in range(1, 13, 3):
        for x in range(0, 16, 2):
            c.set(x + (y // 3) % 2, y, "#d63a86")
    c.rect(0, 13, 15, 15, YEL); c.rect(0, 0, 15, 0, YEL)
    return c


# ---------------------------------------------------------------- existing guns, wrapped with sockets and pivots
def adopt(kit, root, asset, parts):
    """Move build_gun / build_shotgun parts onto hinge pivots and prefix every name with the asset name."""
    obs = {o.name.split('.')[0]: o for o in root.children}
    for base, (pname, hinge) in parts.items():
        p = kit.empty(f"{asset} {pname}", root, hinge)
        o = obs[base]
        o.parent = p
        o.location = Vector(o.location) - Vector(hinge)
    for o in root.children_recursive:
        if not o.name.startswith(asset):
            o.name = f"{asset} {o.name}"


def build_scoop_pistol(kit, root):
    N = "Scoop Pistol"
    build_gun(kit, root)
    adopt(kit, root, N, {"trigger": ("trigger", (0, -0.006, -0.03)), "hammer": ("hammer", (0, 0.094, 0.02))})
    sock(kit, N, "muzzle", root, (0, -0.208, 0.004))
    sock(kit, N, "grip", root, (0, 0.05, -0.065), (16, 0, 0))


def build_sundae_shotgun(kit, root):
    N = "Sundae Shotgun"
    build_shotgun(kit, root)
    adopt(kit, root, N, {"trigger": ("trigger", (0, 0.047, -0.026)), "pump": ("pump", (0, -0.18, -0.032))})
    sock(kit, N, "muzzle", root, (0, -0.4, 0.03))
    sock(kit, N, "grip", root, (0, 0.1, -0.06), (18, 0, 0))


# ---------------------------------------------------------------- sprinkle jar (item, and the SMG magazine)
def sprinkle_jar(kit, N, parent, cap_open=-14):
    """Jar along +Z from its base at the parent origin, 0.17 m tall. Flip cap on a hinge at the back edge."""
    pink = solid(kit, "gun pink", PINK)
    tube(kit, f"{N} jar", [(0, 0, 0), (0, 0, 0.012), (0, 0, 0.11), (0, 0, 0.128), (0, 0, 0.135)],
         [0.036, 0.042, 0.042, 0.032, 0.03], tex_mat(f"{N} jar", tex_jar(kit.rand)), parent, sides=8)
    tube(kit, f"{N} lid", [(0, 0, 0.128), (0, 0, 0.16)], [0.038, 0.036], pink, parent, sides=8)
    tube(kit, f"{N} lid band", [(0, 0, 0.134), (0, 0, 0.142)], 0.04, solid(kit, "gun yellow", YEL), parent, sides=8,
         caps=(False, False))
    ink = solid(kit, "gun dark", INK, 0.1)
    for i, (x, y) in enumerate(((0, 0.012), (-0.012, 0.002), (0.012, 0.002), (-0.007, 0.018), (0.007, 0.018))):
        tbox(kit, f"{N} shaker hole {i}", (x, y, 0.1605), (0.006, 0.006, 0.002), ink, parent)
    cap = kit.empty(f"{N} flip cap", parent, (0, 0.034, 0.161), (cap_open, 0, 0))
    tbox(kit, f"{N} flip cap", (0, -0.034, 0.004), (0.066, 0.068, 0.008), solid(kit, "jar cap mint", MINT), cap)
    tbox(kit, f"{N} cap hinge", (0, 0.038, 0.158), (0.024, 0.01, 0.012), solid(kit, "jar cap mint", MINT), parent)
    tbox(kit, f"{N} cap tab", (0, -0.072, 0.004), (0.018, 0.01, 0.006), solid(kit, "jar cap mint", MINT), cap)


def build_sprinkle_jar(kit, root):
    N = "Sprinkle Jar"
    sprinkle_jar(kit, N, root)
    sprinkle_bits(kit, N, root, 6, (0.0, -0.02), 0.012, 0.01, 0.168)
    sock(kit, N, "hand", root, (0, 0, 0.07))


# ---------------------------------------------------------------- Sprinkle SMG
def build_smg(kit, root):
    N = "Sprinkle SMG"
    m = gun_mats(kit)
    t_body = tex_mat("smg body", tex_smg_body(kit.rand))
    tbox(kit, f"{N} receiver", (0, 0.01, 0), (0.05, 0.2, 0.064), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tbox(kit, f"{N} top cover", (0, 0.0, 0.038), (0.034, 0.17, 0.012), m['pink'], root)
    tbox(kit, f"{N} rear cap", (0, 0.115, 0.002), (0.046, 0.016, 0.058), m['pink'], root)
    tbox(kit, f"{N} rear sight", (0, 0.085, 0.05), (0.022, 0.012, 0.016), m['yel'], root)
    tube(kit, f"{N} shroud", [(0, -0.085, 0.006), (0, -0.2, 0.006)], 0.022, tex_mat("smg shroud", tex_shroud()), root,
         sides=8, side=(1, 0, 0))
    tbox(kit, f"{N} front sight", (0, -0.185, 0.032), (0.008, 0.012, 0.016), m['yel'], root)
    tube(kit, f"{N} barrel", [(0, -0.195, 0.006), (0, -0.228, 0.006)], 0.011, m['steel'], root, sides=6, side=(1, 0, 0))
    tube(kit, f"{N} flash hider", [(0, -0.222, 0.006), (0, -0.25, 0.006)], [0.014, 0.021], m['pink'], root, sides=8,
         side=(1, 0, 0), caps=(True, False))
    tube(kit, f"{N} flash hider ring", [(0, -0.245, 0.006), (0, -0.252, 0.006)], 0.022, m['yel'], root, sides=8,
         side=(1, 0, 0), caps=(False, False))
    # magazine well and the sprinkle jar magazine (lid up into the gun)
    tbox(kit, f"{N} mag well", (0, -0.03, -0.044), (0.07, 0.072, 0.04), m['pink'], root, taper=(1.0, 0.9))
    mag = kit.empty(f"{N} magazine", root, (0, -0.03, -0.152), (0, 0, 0), (0.72, 0.72, 0.72))
    sprinkle_jar(kit, f"{N} mag", mag, 0)
    grip_trigger(kit, N, root, 0.07, -0.032, m, angle=12)
    # charging bolt on the right side
    bolt = kit.empty(f"{N} bolt", root, (0.026, 0.03, 0.016))
    tbox(kit, f"{N} bolt slot", (0, 0.0, 0), (0.004, 0.08, 0.01), m['ink'], bolt)
    tbox(kit, f"{N} bolt knob", (0.012, -0.03, 0), (0.022, 0.014, 0.014), m['yel'], bolt)
    # folding wire stock on its hinge
    stock = kit.empty(f"{N} stock", root, (0, 0.12, -0.012))
    for sx in (1, -1):
        tube(kit, f"{N} stock rod {sx}", [(sx * 0.016, 0, 0.02), (sx * 0.016, 0.15, -0.0)], 0.0055, m['yel'], stock,
             sides=4, side=(0, 0, 1))
        tube(kit, f"{N} stock low rod {sx}", [(sx * 0.016, 0, -0.012), (sx * 0.016, 0.15, -0.04)], 0.0055, m['yel'],
             stock, sides=4, side=(0, 0, 1))
    tbox(kit, f"{N} butt pad", (0, 0.158, -0.018), (0.05, 0.018, 0.075), m['pink'], stock)
    sprinkle_bits(kit, N, root, 7, (0, 0.0), 0.012, 0.07, 0.0455, 0.012)
    sock(kit, N, "muzzle", root, (0, -0.252, 0.006))


# ---------------------------------------------------------------- Long Spoon sniper
def build_long_spoon(kit, root):
    N = "Long Spoon"
    m = gun_mats(kit)
    t_body = tex_mat("spoon body", tex_body(LAV, LAV_D, "#dccbff", PINK))
    purp, glass = solid(kit, "scope purple", PURP, shade="#6a3fd0"), solid(kit, "lens", GLASS, 0.6, shade="#3f48a0")
    tbox(kit, f"{N} receiver", (0, 0.03, 0), (0.05, 0.27, 0.066), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tbox(kit, f"{N} rail", (0, 0.03, 0.038), (0.026, 0.22, 0.01), m['ink'], root)
    tube(kit, f"{N} stock", [(0, 0.16, 0.0), (0, 0.3, -0.03), (0, 0.46, -0.055)],
         [(0.026, 0.034), (0.026, 0.05), (0.028, 0.07)], tex_mat("spoon stock", tex_stock()), root, sides=6,
         side=(1, 0, 0), bulge=(0, 0.004))
    tbox(kit, f"{N} cheek rest", (0, 0.3, 0.012), (0.04, 0.12, 0.02), m['pink'], root, rot=(-8, 0, 0))
    tbox(kit, f"{N} butt pad", (0, 0.47, -0.056), (0.058, 0.02, 0.15), m['ink'], root, rot=(-8, 0, 0))
    # the barrel is a long sundae spoon: candy-striped handle, steel neck, oval bowl at the muzzle
    tube(kit, f"{N} spoon handle", [(0, -0.1, 0.004), (0, -0.46, 0.004)], [(0.021, 0.015), (0.019, 0.013)],
         tex_mat("spoon handle", tex_candy(PINK, WHITE)), root, sides=8, side=(1, 0, 0))
    tube(kit, f"{N} spoon neck", [(0, -0.455, 0.004), (0, -0.62, 0.004), (0, -0.66, 0.008)], [(0.014, 0.009), 0.011, 0.013],
         m['steel'], root, sides=6, side=(1, 0, 0))
    tube(kit, f"{N} spoon bowl", [(0, -0.655, 0.01), (0, -0.675, 0.012), (0, -0.72, 0.014), (0, -0.77, 0.014),
                                  (0, -0.8, 0.012)], [(0.018, 0.009), (0.04, 0.015), (0.05, 0.018), (0.042, 0.015),
                                                       (0.014, 0.007)], m['steel'], root, sides=8, front=(0, 0, 1))
    tube(kit, f"{N} spoon dish", [(0, -0.68, 0.029), (0, -0.72, 0.032), (0, -0.765, 0.029)],
         [(0.03, 0.002), (0.04, 0.003), (0.03, 0.002)], solid(kit, "spoon dish", "#a9a2e0", shade="#8f87cc"), root,
         sides=8, front=(0, 0, 1))
    for y in (-0.12, -0.3):
        tbox(kit, f"{N} barrel band {y}", (0, y, 0.004), (0.04, 0.016, 0.03), m['yel'], root)
    tbox(kit, f"{N} handguard", (0, -0.17, -0.016), (0.044, 0.12, 0.03), t_body, root, taper=(1.0, 1.0))
    # scope on two rings
    tube(kit, f"{N} scope", [(0, 0.15, 0.088), (0, 0.12, 0.088), (0, 0.09, 0.084), (0, -0.07, 0.084), (0, -0.1, 0.088),
                             (0, -0.13, 0.088)], [0.024, 0.024, 0.017, 0.017, 0.028, 0.028], purp, root, sides=8,
         side=(1, 0, 0), caps=(False, False))
    for y, r in ((0.15, 0.022), (-0.13, 0.026)):
        tube(kit, f"{N} lens {y}", [(0, y - 0.004 * (1 if y < 0 else -1), 0.088), (0, y, 0.088)], r, glass, root, sides=8,
             side=(1, 0, 0))
    tube(kit, f"{N} scope sunshade", [(0, -0.128, 0.088), (0, -0.16, 0.088)], 0.03, m['pink'], root, sides=8,
         side=(1, 0, 0), caps=(False, False))
    tbox(kit, f"{N} lens glint", (0.008, -0.161, 0.098), (0.008, 0.002, 0.01), solid(kit, "glint", WHITE, 0.9), root)
    for y in (0.07, -0.05):
        tbox(kit, f"{N} scope ring {y}", (0, y, 0.062), (0.03, 0.018, 0.05), m['yel'], root)
    tube(kit, f"{N} turret top", [(0, 0.01, 0.1), (0, 0.01, 0.118)], 0.012, m['yel'], root, sides=6)
    tube(kit, f"{N} turret side", [(0.016, 0.01, 0.084), (0.034, 0.01, 0.084)], 0.012, m['yel'], root, sides=6,
         front=(0, 0, 1))
    # bolt with a cherry knob, rotates about the bore axis then slides
    bolt = kit.empty(f"{N} bolt", root, (0, 0.11, 0.016))
    tube(kit, f"{N} bolt arm", [(0.024, 0, 0), (0.05, 0.0, -0.006), (0.058, 0.012, -0.024)], 0.006, m['steel'], bolt,
         sides=4, front=(0, -1, 0))
    lowball(kit, f"{N} bolt cherry", (0.06, 0.014, -0.034), (0.014, 0.014, 0.014), solid(kit, "cherry", RED, 0.6), bolt)
    tube(kit, f"{N} cherry stem", [(0.06, 0.014, -0.022), (0.062, 0.02, -0.006)], 0.002,
         solid(kit, "cherry stem", "#3fae4a"), bolt, sides=4, caps=(False, False))
    # pint magazine
    mag = kit.empty(f"{N} magazine", root, (0, -0.04, -0.033), (-8, 0, 0))
    tube(kit, f"{N} pint", [(0, 0, -0.1), (0, 0, -0.012)], [0.03, 0.036], tex_mat("spoon pint", tex_pint(BLUE)), mag, sides=8)
    tube(kit, f"{N} pint lid", [(0, 0, -0.014), (0, 0, 0.0)], 0.04, solid(kit, "pint lid blue", "#1d5fcc"), mag, sides=8)
    grip_trigger(kit, N, root, 0.1, -0.033, m, angle=14)
    sock(kit, N, "muzzle", root, (0, -0.805, 0.012))
    sock(kit, N, "scope eye", root, (0, 0.2, 0.088))


# ---------------------------------------------------------------- Cone Launcher
def build_cone_launcher(kit, root):
    N = "Cone Launcher"
    m = gun_mats(kit)
    R = kit.rand
    t_body = tex_mat("launcher body", tex_body(PINK, "#d63a86", BERRY, MINT))
    t_waffle = tex_mat("launcher waffle", tex_waffle())
    t_drum = tex_mat("launcher drum", tex_candy(LAV, LAV_D, 8))
    tbox(kit, f"{N} receiver", (0, 0.08, 0.0), (0.06, 0.15, 0.09), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tube(kit, f"{N} stock", [(0, 0.15, -0.0), (0, 0.24, -0.025), (0, 0.32, -0.045)],
         [(0.03, 0.036), (0.03, 0.05), (0.032, 0.064)], tex_mat("launcher stock", tex_stock()), root, sides=6,
         side=(1, 0, 0), bulge=(0, 0.004))
    # frame: top strap and axle carry the drum between receiver and barrel block
    tbox(kit, f"{N} top strap", (0, -0.06, 0.088), (0.03, 0.2, 0.014), m['steel'], root)
    tbox(kit, f"{N} front block", (0, -0.165, 0.03), (0.07, 0.03, 0.13), m['pink'], root)
    tube(kit, f"{N} axle", [(0, 0.01, -0.03), (0, -0.17, -0.03)], 0.012, m['steel'], root, sides=6, side=(1, 0, 0))
    drum = kit.empty(f"{N} drum", root, (0, -0.07, -0.03))
    tube(kit, f"{N} drum shell", [(0, 0.075, 0), (0, -0.075, 0)], 0.078, t_drum, drum, sides=6, side=(1, 0, 0))
    for y in (0.078, -0.078):
        tube(kit, f"{N} drum cap {y}", [(0, y * 0.97, 0), (0, y, 0)], 0.06, m['yel'], drum, sides=6, side=(1, 0, 0))
    flav = [m['cream'][c] for c in (BERRY, VAN, CHOC, "#9ff5d8", BERRY, VAN)]
    for i in range(6):
        a = math.radians(90 + 60 * i)
        lowball(kit, f"{N} drum scoop {i}", (math.cos(a) * 0.078, 0, math.sin(a) * 0.078), (0.04, 0.056, 0.04), flav[i], drum)
    # waffle-cone barrel on a break-open hinge, aligned with the top chamber
    brl = kit.empty(f"{N} barrel", root, (0, -0.18, -0.03))
    tube(kit, f"{N} barrel collar", [(0, 0.0, 0.072), (0, -0.04, 0.072)], 0.04, m['pink'], brl, sides=8, side=(1, 0, 0))
    tube(kit, f"{N} waffle cone", [(0, -0.03, 0.072), (0, -0.2, 0.072), (0, -0.33, 0.072)], [0.036, 0.06, 0.082],
         t_waffle, brl, sides=8, side=(1, 0, 0), caps=(True, False))
    tube(kit, f"{N} cone rim", [(0, -0.325, 0.072), (0, -0.342, 0.072)], [0.088, 0.086],
         solid(kit, "rim", "#ffcf5a", shade="#d9862a"), brl, sides=8, side=(1, 0, 0), caps=(False, False))
    lowball(kit, f"{N} loaded scoop", (0, -0.31, 0.072), (0.07, 0.05, 0.068), m['cream']["#9ff5d8"], brl)
    sprinkle_bits(kit, N, brl, 5, (0, -0.32), 0.03, 0.01, 0.142, 0.016)
    tbox(kit, f"{N} hinge", (0, 0.0, -0.002), (0.05, 0.02, 0.02), m['steel'], brl)
    # foregrip under the cone, flip-up ladder sight
    tbox(kit, f"{N} foregrip", (0, -0.13, -0.025), (0.036, 0.04, 0.09), m['grip'], brl, rot=(-6, 0, 0))
    tbox(kit, f"{N} foregrip clamp", (0, -0.13, 0.024), (0.05, 0.05, 0.024), m['pink'], brl)
    sight = kit.empty(f"{N} sight", brl, (0, -0.02, 0.112), (-70, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"{N} sight rail {sx}", (sx * 0.01, 0, 0.025), (0.004, 0.004, 0.05), m['yel'], sight)
    tbox(kit, f"{N} sight top", (0, 0, 0.05), (0.024, 0.004, 0.006), m['yel'], sight)
    grip_trigger(kit, N, root, 0.1, -0.045, m, angle=16)
    sock(kit, N, "muzzle", root, (0, -0.52, 0.042))


# ---------------------------------------------------------------- Banana Split Harpoon
def build_harpoon(kit, root):
    N = "Banana Split Harpoon"
    m = gun_mats(kit)
    R = kit.rand
    t_body = tex_mat("harpoon body", tex_body(YEL, "#d9b21a", "#fff3a0", PINK, PINK))
    t_lic = tex_mat("licorice", tex_licorice())
    tbox(kit, f"{N} receiver", (0, 0.04, 0), (0.05, 0.2, 0.06), t_body, root, taper=(0.86, 1.0),
         uv={'pz': (0.0, 0.9, 1.0, 1.0), 'nz': (0.0, 0.0, 1.0, 0.1)})
    tube(kit, f"{N} stock", [(0, 0.13, -0.004), (0, 0.22, -0.02), (0, 0.28, -0.03)], [(0.022, 0.03), (0.024, 0.04),
                                                                                       (0.026, 0.05)],
         tex_mat("harpoon stock", tex_candy(PINK, WHITE, 8)), root, sides=6, side=(1, 0, 0), bulge=(0, 0.004))
    tube(kit, f"{N} barrel", [(0, -0.06, 0.0), (0, -0.6, 0.0)], 0.019, m['pink'], root, sides=8, side=(1, 0, 0))
    tbox(kit, f"{N} shaft rail", (0, -0.33, 0.022), (0.014, 0.54, 0.008), m['steel'], root)
    tbox(kit, f"{N} muzzle head", (0, -0.61, 0.012), (0.06, 0.036, 0.06), t_body, root,
         uv={'all': (0.6, 0.0, 0.9, 0.6)})
    tbox(kit, f"{N} line slot", (0, -0.63, -0.028), (0.02, 0.012, 0.024), m['yel'], root)
    # banana harpoon: separate projectile pivot, peel split open into fins at the tail, steel barbed tip
    hp = kit.empty(f"{N} harpoon", root, (0, -0.34, 0.046))
    tube(kit, f"{N} banana", [(0, 0.27, 0.004), (0, 0.2, -0.002), (0, 0.0, -0.006), (0, -0.2, -0.002), (0, -0.25, 0.004)],
         [0.012, 0.018, 0.021, 0.017, 0.01], tex_mat("banana", tex_banana(R)), hp, sides=6, side=(1, 0, 0), smooth=False)
    peel_out, peel_in = solid(kit, "peel", YEL, shade="#f5c832"), solid(kit, "peel inside", VAN, 0.4)
    for i, a in enumerate((-62, 0, 62)):
        fin = kit.empty(f"{N} peel {i}", hp, (0, 0.17, -0.002), (0, a, 0))
        tbox(kit, f"{N} peel {i}", (0.0, 0.07, 0.034), (0.006, 0.13, 0.04), peel_out, fin, rot=(22, 0, 0), taper=(1.0, 0.6))
        tbox(kit, f"{N} peel {i} inner", (0.0035, 0.07, 0.034), (0.002, 0.12, 0.032), peel_in, fin, rot=(22, 0, 0),
             taper=(1.0, 0.6))
    tube(kit, f"{N} tip", [(0, -0.24, 0.002), (0, -0.27, 0.002), (0, -0.33, 0.002)], [0.012, 0.012, 0.001], m['steel'], hp,
         sides=6, side=(1, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"{N} barb {sx}", (sx * 0.014, -0.28, 0.002), (0.004, 0.034, 0.012), m['steel'], hp, rot=(0, 0, -sx * 28))
    lowball(kit, f"{N} cherry", (0, 0.02, 0.025), (0.012, 0.012, 0.012), solid(kit, "cherry", RED, 0.6), hp)
    tube(kit, f"{N} whip", [(0, 0.02, 0.012), (0, 0.02, 0.02)], [0.016, 0.01], solid(kit, "whip", WHITE, 0.5), hp, sides=6)
    sock(kit, N, "harpoon line", hp, (0, 0.275, 0.004))
    # licorice line: harpoon tail, along the side to the muzzle slot, back under the barrel to the reel
    tube(kit, f"{N} licorice line", [(0, -0.065, 0.05), (0.02, -0.09, 0.035), (0.034, -0.2, 0.006), (0.036, -0.42, -0.012),
                                     (0.02, -0.6, -0.028), (0, -0.635, -0.03), (-0.004, -0.6, -0.036),
                                     (0, -0.42, -0.046), (0.0, -0.25, -0.05), (0, -0.16, -0.054)],
         0.0045, t_lic, root, sides=5, side=(1, 0, 0), caps=(False, False))
    # reel under the barrel with a crank on the right
    reel = kit.empty(f"{N} reel", root, (0, -0.12, -0.06))
    tube(kit, f"{N} spool", [(-0.024, 0, 0), (0.024, 0, 0)], 0.034, m['pink'], reel, sides=8, front=(0, 0, 1))
    tube(kit, f"{N} spool line", [(-0.018, 0, 0), (0.018, 0, 0)], 0.038, t_lic, reel, sides=8, front=(0, 0, 1),
         caps=(False, False))
    tube(kit, f"{N} spool hub", [(-0.03, 0, 0), (0.03, 0, 0)], 0.012, m['yel'], reel, sides=6, front=(0, 0, 1))
    tbox(kit, f"{N} reel bracket", (0, 0.0, 0.04), (0.02, 0.03, 0.04), m['steel'], root, loc=(0, -0.12, -0.06))
    crank = kit.empty(f"{N} crank", reel, (0.03, 0, 0), (-35, 0, 0))
    tbox(kit, f"{N} crank arm", (0.004, 0, -0.022), (0.008, 0.012, 0.05), m['yel'], crank)
    tube(kit, f"{N} crank knob", [(0.008, 0, -0.044), (0.032, 0, -0.044)], 0.008, m['pink'], crank, sides=6, front=(0, 0, 1))
    grip_trigger(kit, N, root, 0.08, -0.03, m, angle=14)
    sock(kit, N, "line anchor", root, (0, -0.12, -0.022))
    sock(kit, N, "muzzle", root, (0, -0.63, 0.048))


# ---------------------------------------------------------------- Soft Serve Minigun turret
def build_turret(kit, root):
    N = "Soft Serve Minigun"
    m = gun_mats(kit)
    t_body = tex_mat("minigun body", tex_gun_body())
    t_hop = tex_mat("hopper", tex_pint(MINT))
    blue = solid(kit, "turret blue", BLUE)
    tbox(kit, f"{N} mount plate", (0, 0, 0.015), (0.8, 0.8, 0.03), tex_mat("mount plate", tex_plate()), root,
         uv={'all': (0.0, 0.0, 0.1, 0.1), 'pz': (0.0, 0.0, 1.0, 1.0)})
    for i, (x, y) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        tube(kit, f"{N} bolt {i}", [(x * 0.33, y * 0.33, 0.03), (x * 0.33, y * 0.33, 0.045)], 0.022, m['ink'], root, sides=6)
    sock(kit, N, "turret base", root, (0, 0, 0))
    yaw = kit.empty(f"{N} yaw", root, (0, 0, 0.03))
    tube(kit, f"{N} turret ring", [(0, 0, 0.0), (0, 0, 0.1), (0, 0, 0.13)], [0.42, 0.4, 0.34], blue, yaw, sides=10)
    tube(kit, f"{N} ring band", [(0, 0, 0.03), (0, 0, 0.06)], 0.422, m['pink'], yaw, sides=10, caps=(False, False))
    tube(kit, f"{N} post", [(0, 0, 0.12), (0, 0, 0.24)], 0.08, m['steel'], yaw, sides=6)
    tbox(kit, f"{N} yoke", (0, 0, 0.25), (0.4, 0.16, 0.05), m['pink'], yaw)
    for sx in (1, -1):
        tbox(kit, f"{N} yoke arm {sx}", (sx * 0.18, 0, 0.33), (0.04, 0.16, 0.18), m['pink'], yaw)
    pitch = kit.empty(f"{N} pitch", yaw, (0, 0, 0.36))
    for sx in (1, -1):
        tube(kit, f"{N} trunnion {sx}", [(sx * 0.125, 0, 0), (sx * 0.215, 0, 0)], 0.05, m['yel'], pitch, sides=8,
             front=(0, 0, 1))
    tbox(kit, f"{N} housing", (0, 0.06, 0), (0.25, 0.42, 0.22), t_body, pitch, uv={'pz': (0, 0.9, 1, 1), 'nz': (0, 0, 1, 0.1)})
    tube(kit, f"{N} motor", [(0, 0.27, 0), (0, 0.33, 0)], [0.09, 0.07], m['pink'], pitch, sides=8, side=(1, 0, 0))
    tbox(kit, f"{N} sight post", (0, -0.12, 0.13), (0.012, 0.012, 0.05), m['yel'], pitch)
    tube(kit, f"{N} sight ring", [(0, -0.122, 0.17), (0, -0.112, 0.17)], 0.03, m['yel'], pitch, sides=8, side=(1, 0, 0),
         caps=(False, False))
    # pint hopper with a soft serve swirl standing in it
    tube(kit, f"{N} hopper", [(0, 0.04, 0.1), (0, 0.04, 0.32)], [0.12, 0.15], t_hop, pitch, sides=8)
    tube(kit, f"{N} hopper rim", [(0, 0.04, 0.31), (0, 0.04, 0.34)], 0.16, solid(kit, "hopper rim", "#22c79c"), pitch, sides=8)
    zs = [0.32, 0.37, 0.41, 0.45, 0.49, 0.53, 0.57, 0.6, 0.64]
    rs = [0.14, 0.145, 0.11, 0.115, 0.08, 0.085, 0.05, 0.045, 0.004]
    tube(kit, f"{N} soft serve", [(0.004 * (i % 2), 0.04, z) for i, z in enumerate(zs)], rs,
         tex_mat("soft serve", tex_swirl()), pitch, sides=8)
    tube(kit, f"{N} soft serve curl", [(0, 0.04, 0.635), (0.015, 0.035, 0.66), (0.03, 0.04, 0.665)], [0.014, 0.01, 0.003],
         m['cream'][VAN], pitch, sides=6)
    # barrel cluster spins about Y
    brl = kit.empty(f"{N} barrels", pitch, (0, -0.15, 0))
    for i in range(6):
        a = 2 * math.pi * i / 6
        o = (math.cos(a) * 0.062, math.sin(a) * 0.062)
        tube(kit, f"{N} barrel {i}", [(o[0], 0.0, o[1]), (o[0], -0.8, o[1])], 0.021, m['steel'], brl, sides=6, side=(1, 0, 0))
    for y0, y1, r, mt in ((0.01, -0.09, 0.105, m['pink']), (-0.43, -0.48, 0.098, m['yel']), (-0.75, -0.81, 0.1, m['pink'])):
        tube(kit, f"{N} clamp {y0}", [(0, y0, 0), (0, y1, 0)], r, mt, brl, sides=8, side=(1, 0, 0))
    tube(kit, f"{N} spindle", [(0, -0.05, 0), (0, -0.85, 0)], 0.025, m['yel'], brl, sides=6, side=(1, 0, 0))
    # spade grips and butterfly trigger for the gunner
    for sx in (1, -1):
        tube(kit, f"{N} grip arm {sx}", [(sx * 0.09, 0.26, 0.04), (sx * 0.12, 0.38, 0.04), (sx * 0.12, 0.42, 0.02)], 0.014,
             m['steel'], pitch, sides=4, side=(1, 0, 0))
        tube(kit, f"{N} grip low arm {sx}", [(sx * 0.09, 0.26, -0.07), (sx * 0.12, 0.38, -0.08), (sx * 0.12, 0.42, -0.07)],
             0.014, m['steel'], pitch, sides=4, side=(1, 0, 0))
        tube(kit, f"{N} handle {sx}", [(sx * 0.12, 0.425, 0.04), (sx * 0.12, 0.425, -0.09)], 0.026,
             tex_mat("turret grip", tex_scoop_grip()), pitch, sides=6)
    trig = kit.empty(f"{N} trigger", pitch, (0, 0.4, 0.035))
    tbox(kit, f"{N} butterfly trigger", (0, 0.01, -0.03), (0.13, 0.012, 0.05), m['yel'], trig, rot=(15, 0, 0))
    sock(kit, N, "gunner hands", pitch, (0, 0.425, -0.025))
    sock(kit, N, "muzzle", pitch, (0, -0.96, 0))
    sock(kit, N, "hopper", pitch, (0, 0.04, 0.34))


# ---------------------------------------------------------------- ice cream scooper tool
def build_scooper(kit, root):
    N = "Scooper"
    m = gun_mats(kit)
    steel = m['steel']
    tube(kit, f"{N} handle", [(0, 0.17, 0.0), (0, 0.16, 0.0), (0, 0.1, 0.0), (0, 0.03, 0.002), (0, 0.01, 0.004)],
         [0.018, 0.026, 0.028, 0.024, 0.02], tex_mat("scooper grip", tex_scoop_grip()), root, sides=8, side=(1, 0, 0),
         bulge=(0.01, 0), v=(1.0, 0.0))
    tube(kit, f"{N} end cap", [(0, 0.175, 0.0), (0, 0.19, 0.0)], [0.02, 0.012], m['yel'], root, sides=8, side=(1, 0, 0))
    tube(kit, f"{N} ferrule", [(0, 0.016, 0.004), (0, -0.01, 0.005)], 0.021, steel, root, sides=8, side=(1, 0, 0))
    tube(kit, f"{N} neck", [(0, -0.008, 0.005), (0, -0.05, 0.008), (0, -0.075, 0.016)], [0.013, 0.01, 0.011], steel, root,
         sides=6, side=(1, 0, 0))
    c = Vector((0, -0.112, 0.03))
    r = 0.045
    a = [math.radians(d) for d in (0, 30, 60, 84)]
    tube(kit, f"{N} bowl", [c - Vector((0, 0, r * math.sin(t))) for t in a], [r * math.cos(t) for t in a], steel, root,
         sides=8, caps=(False, True))
    tube(kit, f"{N} bowl lip", [c - Vector((0, 0, 0.004)), c + Vector((0, 0, 0.002))], r + 0.003, steel, root, sides=8,
         caps=(False, False))
    scr = kit.empty(f"{N} scraper", root, tuple(c))
    tube(kit, f"{N} scraper band", [(-0.04, 0, 0.0), (-0.03, 0, -0.03), (0, 0, -0.042), (0.03, 0, -0.03), (0.04, 0, 0.0)],
         0.003, m['ink'], scr, sides=4, front=(0, -1, 0), caps=(False, False))
    lever = kit.empty(f"{N} thumb lever", root, (0, 0.02, 0.026), (12, 0, 0))
    tbox(kit, f"{N} thumb lever", (0, 0.03, 0.006), (0.018, 0.07, 0.008), m['yel'], lever)
    tbox(kit, f"{N} lever pad", (0, 0.06, 0.012), (0.024, 0.02, 0.006), m['pink'], lever)
    tbox(kit, f"{N} lever arm", (0, -0.035, -0.002), (0.006, 0.05, 0.006), steel, lever, rot=(-14, 0, 0))
    load = kit.empty(f"{N} loaded scoop", root, tuple(c))
    lowball(kit, f"{N} scoop", (0, 0, 0.004), (0.043, 0.043, 0.036), m['cream'][BERRY], load)
    sprinkle_bits(kit, N, load, 5, (0, 0), 0.011, 0.011, 0.038, 0.012)
    sock(kit, N, "hand", root, (0, 0.1, 0))
    sock(kit, N, "scoop tip", root, tuple(c))


ASSETS = [
    ("Scoop Pistol", build_scoop_pistol),
    ("Sundae Shotgun", build_sundae_shotgun),
    ("Sprinkle SMG", build_smg),
    ("Long Spoon", build_long_spoon),
    ("Cone Launcher", build_cone_launcher),
    ("Banana Split Harpoon", build_harpoon),
    ("Soft Serve Minigun", build_turret),
    ("Scooper", build_scooper),
    ("Sprinkle Jar", build_sprinkle_jar),
]
SPACING = 3


# ---------------------------------------------------------------- scene: weapon select pegboard
def tex_pegboard():
    c = Canvas(128, 64, LAV)
    for y in range(1, 64, 4):
        for x in range(1, 128, 4):
            c.set(x, y, "#5a3fa8")
            c.set(x + 1, y, "#7d5ad6")
    return c


def tex_header(rand):
    c = Canvas(68, 16, PINK)
    frosting(c, rand, 12, 9)
    text(c, "PICK YOUR SCOOP!", 3, 8, WHITE, shadow=DRED)
    return c


def hang(kit, root, fn, name, slot, board_y):
    """Build a gun in side profile (barrel to -X, right side facing the camera) centered on slot, with two pegs."""
    p = kit.empty(f"rack {name}", root, (0, 0, 0), (0, 0, -90))
    fn(kit, p)
    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    pts = [inv @ (o.matrix_world @ Vector(b)) for o in p.children_recursive if o.type == 'MESH' for b in o.bound_box]
    lo = Vector([min(q[k] for q in pts) for k in range(3)])
    hi = Vector([max(q[k] for q in pts) for k in range(3)])
    ctr = (lo + hi) / 2
    p.location = Vector((slot[0] - ctr.x, -ctr.y + board_y - 0.06, slot[1] - ctr.z))
    steel = solid(kit, "steel", STEEL, shade="#a9a2e0")
    w = hi.x - lo.x
    for i, f in enumerate((-0.28, 0.22)):
        x, z = slot[0] + f * w, slot[1] - (hi.z - lo.z) / 2 - 0.012
        tube(kit, f"rack peg {name} {i}", [(x, board_y, z), (x, board_y - 0.1, z), (x, board_y - 0.12, z + 0.03)], 0.008,
             steel, root, sides=4, front=(0, 0, 1))
    return p


def build_rack(kit, root):
    R = kit.rand
    by, bx = 0.0, -0.65
    tbox(kit, "rack wall", (0, 0.3, 1.8), (8.0, 0.1, 4.0), solid(kit, "rack wall", "#2c1c4f", 0.2), root)
    tbox(kit, "rack floor", (0, -1.0, -0.02), (8.0, 3.0, 0.04), solid(kit, "rack floor", FLOOR, 0.2), root)
    tbox(kit, "pegboard", (bx, by + 0.02, 1.35), (3.1, 0.04, 1.7), tex_mat("pegboard", tex_pegboard()), root)
    pink = solid(kit, "gun pink", PINK)
    for x in (bx - 1.58, bx + 1.58):
        tbox(kit, f"pegboard frame {x}", (x, by - 0.005, 1.35), (0.06, 0.06, 1.76), pink, root)
    for z in (0.5, 2.2):
        tbox(kit, f"pegboard frame {z}", (bx, by - 0.005, z), (3.22, 0.06, 0.06), pink, root)
    tbox(kit, "header sign", (bx, by - 0.02, 2.47), (2.0, 0.06, 0.47), tex_mat("rack header", tex_header(R)), root,
         uv={'all': (0, 0, 0.02, 0.02), 'ny': (0, 0, 1, 1)})
    slots = [(build_long_spoon, "Long Spoon", (-1.45, 1.93)), (build_harpoon, "Banana Split Harpoon", (0.15, 1.93)),
             (build_sundae_shotgun, "Sundae Shotgun", (-1.65, 1.4)), (build_cone_launcher, "Cone Launcher", (-0.7, 1.4)),
             (build_smg, "Sprinkle SMG", (0.38, 1.4)), (build_scoop_pistol, "Scoop Pistol", (-1.7, 0.88)),
             (build_scooper, "Scooper", (-0.95, 0.88))]
    for fn, name, slot in slots:
        hang(kit, root, fn, name, slot, by)
    # little shelf with sprinkle jars
    tbox(kit, "jar shelf", (0.1, by - 0.1, 0.72), (0.65, 0.2, 0.03), pink, root)
    for i, x in enumerate((-0.12, 0.1, 0.32)):
        j = kit.empty(f"rack jar {i}", root, (x, by - 0.1, 0.735), (0, 0, -15 + 15 * i))
        sprinkle_jar(kit, f"rack jar {i}", j, 0)
    # the roof turret stands on the floor beside the board, side on
    t = kit.empty("rack turret", root, (1.3, -0.7, 0), (0, 0, 90))
    build_turret(kit, t)


SCENES = [dict(name="Weapon Rack", build=build_rack, cam=((0.15, -7.9, 1.3), (0.15, 0, 1.22), 50), res=(1600, 900))]
