"""Characters batch (style H): team-colored players + T-pose, first-person arms, three walker outfits (with hit
variants), a frozen walker in a mint ice block, and the spectator ghost."""
from style_H import *
import re


# ---------------------------------------------------------------- shared helpers
def named(asset, fn, **kw):
    """Build, then prefix every descendant name with the asset name."""
    def build(kit, root):
        fn(kit, root, **kw)
        for ob in root.children_recursive:
            ob.name = f"{asset} {re.sub(r'[.][0-9]{3}$', '', ob.name)}"
    return build


def set_root_matrix(root, ob, loc, rotm):
    """Place a parented pivot by its root-space location and rotation matrix."""
    bpy.context.view_layer.update()
    ob.matrix_world = root.matrix_world @ Matrix.Translation(Vector(loc)) @ rotm.to_4x4()


def alpha_mat(name, cv, av, emit=0.32):
    """tex_mat plus a Closest-sampled grayscale alpha canvas (dithered transparency)."""
    m = tex_mat(name, cv, emit, ext='REPEAT')
    nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = av.image(f"H {name} alpha")
    ta.image.colorspace_settings.name = 'Non-Color'
    ta.interpolation = 'Closest'
    ta.extension = 'REPEAT'
    nt.links.new(ta.outputs["Color"], p.inputs["Alpha"])
    m.surface_render_method = 'DITHERED'
    return m


def grey(v):
    return "#%02x%02x%02x" % ((int(v * 255),) * 3)


DIGITS = {'1': (".#.", "##.", ".#.", ".#.", "###"), '2': ("##.", "..#", ".#.", "#..", "###"),
          '3': ("##.", "..#", ".#.", "..#", "##."), '4': ("#.#", "#.#", "###", "..#", "..#")}


def digit(c, ch, x, y, col, k=1):
    for r, row in enumerate(DIGITS[ch]):
        for q, b in enumerate(row):
            if b == '#':
                c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)


# ---------------------------------------------------------------- team players
TEAMS = {
    'pink': dict(main=PINK, trim=PINK, dark="#d63a86", light="#ff8fc8", accent=MINT, num='1', ink=WHITE),
    'blue': dict(main=BLUE, trim=BLUE, dark="#1f5fd0", light="#8fbfff", accent=YEL, num='2', ink=WHITE),
    'mint': dict(main=MINT, trim="#14d6a4", dark="#12a883", light="#a6fbe6", accent=PINK, num='3', ink=INK),
    'yellow': dict(main=YEL, trim="#ffb21f", dark="#d99a0f", light="#fff09a", accent=BLUE, num='4', ink=INK),
}


def tex_team_hat(T):
    c = Canvas(64, 32, WHITE)
    c.rect(0, 4, 63, 8, T['trim'])
    c.rect(0, 10, 63, 10, T['accent'])
    c.rect(0, 0, 63, 1, "#e9ded6")
    for cx in (16, 48):
        for row in range(7):
            half = row // 2
            c.rect(cx - half, 12 + row, cx + half, 12 + row, "#f0a43a")
        c.rect(cx - 3, 19, cx + 3, 22, T['trim'])
        c.rect(cx - 2, 23, cx + 2, 23, T['trim'])
        c.dots([(cx - 1, 21), (cx + 2, 20)], WHITE)
    digit(c, T['num'], 31, 21, T['dark'])
    c.rect(30, 26, 33, 31, "#efe4da")
    return c


def tex_team_torso(rand, T):
    c = Canvas(64, 64, T['main'])
    c.rect(0, 0, 63, 8, PANTS)
    c.rect(0, 9, 63, 11, T['trim'])
    c.rect(56, 6, 58, 10, T['trim']); c.rect(59, 4, 60, 8, T['trim'])
    for y in range(12, 50):
        half = 9 if y < 40 else 7
        for x in range(32 - half, 32 + half):
            c.set(x, y, T['trim'] if (x - 32) % 4 == 0 else WHITE)
        c.set(32 - half - 1, y, T['trim']); c.set(32 + half, y, T['trim'])
    c.rect(24, 49, 39, 50, T['trim'])
    c.rect(28, 20, 35, 26, T['trim']); c.rect(29, 21, 34, 25, T['light'])
    c.dots([(30, 24), (33, 24)], WHITE)
    c.rect(34, 42, 38, 45, T['accent']); c.rect(35, 43, 37, 43, INK)
    c.rect(25, 50, 26, 63, T['trim']); c.rect(37, 50, 38, 63, T['trim'])
    for i in range(46):
        y = 63 - i
        c.set(-10 + i // 2 + 64, y, T['trim']); c.set(10 - i // 2, y, T['trim'])
    c.rect(28, 58, 35, 63, SKIN); c.dots([(28, 58), (35, 58)], T['main'])
    c.rect(26, 60, 27, 63, WHITE); c.rect(36, 60, 37, 63, WHITE)
    c.rect(0, 62, 63, 63, WHITE); c.rect(28, 62, 35, 63, SKIN)
    c.speckle(rand, [hex_scale(T['main'], 0.9)], 40, 12, 57)
    return c


def tex_team_arm(T):
    c = Canvas(16, 32, SKIN)
    c.rect(0, 0, 15, 8, T['main'])
    c.rect(0, 8, 15, 8, WHITE)
    c.rect(0, 27, 15, 29, T['accent'])
    c.dots([(3, 15), (11, 20)], "#f0a888")
    return c


def tex_team_apron(T):
    c = Canvas(32, 32, WHITE)
    for x in range(0, 32, 4):
        c.rect(x, 0, x, 31, T['trim'])
    c.rect(0, 0, 31, 2, T['trim'])
    c.rect(0, 29, 31, 31, T['trim'])
    c.rect(10, 8, 21, 20, T['light'])
    c.rect(11, 9, 20, 19, WHITE)
    for row in range(6):
        c.rect(15 - row // 2, 10 + row, 16 + row // 2, 10 + row, "#f0a43a")
    c.rect(13, 16, 18, 18, T['accent']); c.rect(14, 19, 17, 19, T['accent'])
    c.set(15, 18, WHITE)
    return c


def tex_team_shoe(T):
    c = Canvas(16, 16, T['trim'])
    c.rect(0, 0, 3, 15, WHITE); c.rect(12, 0, 15, 15, WHITE)
    for y in (5, 7, 9):
        c.rect(7, y, 8, y, WHITE)
    c.rect(4, 12, 11, 15, T['light'])
    c.rect(4, 0, 11, 2, T['dark'])
    return c


def tex_team_cooler(T):
    c = Canvas(32, 32, T['main'])
    c.rect(0, 0, 31, 1, T['dark'])
    c.rect(0, 10, 31, 12, T['accent'])
    c.rect(0, 26, 31, 31, WHITE)
    c.rect(0, 25, 31, 25, T['dark'])
    shadow = T['dark'] if T['ink'] == WHITE else WHITE
    digit(c, T['num'], 14, 24, shadow, 2)
    digit(c, T['num'], 13, 25, T['ink'], 2)
    c.rect(29, 28, 31, 31, T['accent'])
    return c


def build_team_player(kit, root, team='blue', tpose=False):
    """build_player recolored for a team (shirt, hat band, apron trim, shoes, cooler with the player number).
    tpose=True: arms straight out along X, no gun, for rigging."""
    T = TEAMS[team]
    t_head = tex_mat("player head", tex_player_head())
    t_hat = tex_mat(f"hat {team}", tex_team_hat(T))
    t_torso = tex_mat(f"torso {team}", tex_team_torso(kit.rand, T))
    t_arm = tex_mat(f"arm {team}", tex_team_arm(T))
    t_leg = tex_mat("player leg", tex_player_leg())
    t_shoe = tex_mat(f"shoe {team}", tex_team_shoe(T))
    t_apron = tex_mat(f"apron {team}", tex_team_apron(T))
    t_cool = tex_mat(f"cooler {team}", tex_team_cooler(T))
    skin = solid(kit, "skin", SKIN)

    tube(kit, "torso", [(0, 0, 0.84), (0, 0, 0.94), (0, 0, 1.08), (0, -0.005, 1.24), (0, 0.005, 1.38), (0, 0.01, 1.47)],
         [(0.15, 0.1), (0.155, 0.105), (0.138, 0.098), (0.16, 0.11), (0.19, 0.112), (0.085, 0.068)], t_torso, root)

    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    cols, rows = 5, 3
    grid = []
    for j, (z, rx, ry) in enumerate(((0.95, 0.165, 0.118), (0.75, 0.19, 0.14), (0.55, 0.2, 0.15))):
        row = []
        for i in range(cols):
            a = math.radians(-62 + 124 * i / (cols - 1))
            row.append(bm.verts.new((math.sin(a) * rx, -math.cos(a) * ry - 0.004, z)))
        grid.append(row)
    for j in range(rows - 1):
        for i in range(cols - 1):
            fc = bm.faces.new((grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]))
            for lp, uv in zip(fc.loops, ((i / 4, 1 - (j + 1) / 2), ((i + 1) / 4, 1 - (j + 1) / 2),
                                         ((i + 1) / 4, 1 - j / 2), (i / 4, 1 - j / 2))):
                lp[uvl].uv = (min(0.995, max(0.005, uv[0])), min(0.995, max(0.005, uv[1])))
    kit.mesh_from_bmesh("apron", bm, t_apron, root)

    head = kit.empty("head pivot", root, (0, -0.005, 1.45))
    tube(kit, "head", [(0, 0, 0), (0, 0, 0.05), (0, -0.005, 0.08), (0, -0.01, 0.13), (0, -0.005, 0.19), (0, 0, 0.25),
                       (0, 0.005, 0.29), (0, 0.005, 0.31)],
         [0.048, 0.054, (0.078, 0.085), (0.1, 0.106), (0.106, 0.112), (0.098, 0.104), (0.07, 0.075), (0.03, 0.035)],
         t_head, head, bulge=(0, 0.01))
    tube(kit, "hat", [(0, 0.004, 0.205), (0, 0.004, 0.245), (0, 0.004, 0.3), (0, 0.004, 0.345)],
         [(0.113, 0.121), (0.108, 0.13), (0.06, 0.134), (0.012, 0.126)], t_hat, head, caps=(False, True))
    kit.empty("socket camera", head, (0, -0.1, 0.17))

    for sx, name in ((1, "L"), (-1, "R")):
        leg = kit.empty(f"leg {name}", root, (sx * 0.085, 0, 0.9), (0, sx * -3, 0))
        tube(kit, f"leg {name}", [(0, 0, 0.04), (0, 0, -0.2), (0, -0.012, -0.43), (0, 0, -0.62), (0, 0, -0.82)],
             [(0.082, 0.088), 0.07, 0.056, 0.05, 0.043], t_leg, leg, sides=6, front=(0, 1, 0))
        tube(kit, f"shoe {name}", [(0, 0.05, -0.86), (0, -0.03, -0.855), (0, -0.12, -0.87)],
             [(0.048, 0.042), (0.054, 0.048), (0.042, 0.03)], t_shoe, leg, sides=6, front=(0, 0, 1),
             bulge=(0.015, 0.03))

    if tpose:
        arm_r, L = player_arm(kit, root, "arm R", (-0.2, 0, 1.39), (-0.8, 0, 1.39), t_arm, skin)
        kit.empty("socket hand R", arm_r, (0, 0, -L))
        arm_l, L = player_arm(kit, root, "arm L", (0.2, 0, 1.39), (0.8, 0, 1.39), t_arm, skin)
        kit.empty("socket hand L", arm_l, (0, 0, -L))
    else:
        hand_r = Vector((-0.11, -0.6, 1.38))
        arm_r, L = player_arm(kit, root, "arm R", (-0.2, 0, 1.39), hand_r, t_arm, skin)
        gun = kit.empty("socket hand R", arm_r, (0, 0.062, -L - 0.052))
        gun.rotation_euler = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0))).to_euler()
        build_gun(kit, gun)
        arm_l, L = player_arm(kit, root, "arm L", (0.2, 0, 1.39), hand_r + Vector((0.05, 0.05, -0.07)), t_arm, skin)
        kit.empty("socket hand L", arm_l, (0, 0, -L))

    back = kit.empty("cooler pivot", root, (0, 0.2, 1.17))
    tbox(kit, "cooler", (0, 0, 0), (0.34, 0.2, 0.3), t_cool, back,
         uv={'pz': (0.9, 0.9, 1.0, 1.0), 'nz': (0.1, 0.0, 0.2, 0.05)})
    tbox(kit, "cooler lid", (0, 0, 0.165), (0.36, 0.22, 0.04), solid(kit, f"lid {team}", T['accent']), back)
    tube(kit, "handle", [(-0.1, 0, 0.185), (-0.08, 0, 0.215), (0.08, 0, 0.215), (0.1, 0, 0.185)], 0.01,
         solid(kit, "handle", WHITE), back, sides=4, side=(0, 1, 0))
    for i, (x, col) in enumerate(((-0.105, PINK), (0.0, MINT), (0.105, YEL))):
        y = 0.035 if i != 1 else -0.03
        tube(kit, f"pint {i}", [(x, y, 0.185), (x, y, 0.285)], [0.04, 0.046], tex_mat(f"pint {i}", tex_pint(col)), back,
             sides=8)
        tube(kit, f"pint lid {i}", [(x, y, 0.285), (x, y, 0.3)], [0.05, 0.05], solid(kit, f"pint lid {i}", hex_scale(col, 0.8)),
             back, sides=8)
    strap = solid(kit, f"strap {team}", T['accent'])
    for sx in (1, -1):
        tube(kit, f"strap {sx}", [(sx * 0.11, 0.1, 1.33), (sx * 0.115, 0.06, 1.455), (sx * 0.12, -0.06, 1.44),
                                  (sx * 0.125, -0.112, 1.33), (sx * 0.13, -0.114, 1.16)],
             [(0.024, 0.007)] * 5, strap, root, sides=4, side=(1, 0, 0), caps=(False, False))


# ---------------------------------------------------------------- first-person arms
FP_GUN = (-0.13, -0.52, -0.045)   # Scoop Pistol origin relative to the camera (camera looks along -Y)
FP_GUN_ROT = (0, -6, 7)          # slight yaw so the barrel converges on the crosshair


def tex_fp_forearm(T):
    """v=0 at the elbow: rolled sleeve, white cuff, bare forearm, wristband at the wrist."""
    c = Canvas(16, 32, SKIN)
    c.rect(0, 0, 15, 12, T['main'])
    c.speckle(random.Random(4), [hex_scale(T['main'], 0.86)], 18, 0, 11)
    c.rect(0, 12, 15, 14, WHITE); c.rect(0, 12, 15, 12, "#e6dcd2")
    c.rect(0, 26, 15, 28, T['accent']); c.rect(0, 27, 15, 27, hex_scale(T['accent'], 0.85))
    c.dots([(3, 17), (11, 21), (6, 23), (13, 18)], "#f0a888")
    c.rect(0, 29, 15, 31, "#ffb994")
    return c


def tex_fist():
    """Wrapped fingers: u=0.5 faces the grip front, u=0.25 back of hand (-X), u=0.75 fingertips (+X)."""
    c = Canvas(16, 16, SKIN)
    for y in (5, 10):
        c.rect(5, y, 13, y, "#e0906c")
    c.rect(12, 0, 13, 15, "#f2a37f")
    c.dots([(13, 2), (13, 7), (13, 12)], "#ffe0d4")
    c.dots([(5, 3), (5, 8), (5, 13)], "#ffd6bd")
    c.rect(0, 0, 15, 0, "#f0a888")
    return c


def build_fp_arms(kit, root, team='blue'):
    """Forearms + hands from the player camera (root = camera, looking -Y). Right hand grips the pistol grip,
    left hand wraps under and around it. Pivots at elbows and wrists; hand pivots share the gun's frame."""
    T = TEAMS[team]
    t_fore = tex_mat(f"fp forearm {team}", tex_fp_forearm(T))
    t_fist = tex_mat("fp fist", tex_fist())
    skin = solid(kit, "skin", SKIN)
    cuff = solid(kit, "fp cuff", WHITE)
    kit.empty("socket camera", root, (0, 0, 0))
    G = Vector(FP_GUN)
    RG = Euler([math.radians(a) for a in FP_GUN_ROT]).to_matrix()

    def arm(name, wrist_g, elbow_off):
        W = G + RG @ Vector(wrist_g)
        E = W + Vector(elbow_off)
        fore = kit.empty(f"forearm {name}", root, E)
        aim(fore, W - E)
        L = (W - E).length
        zs = [0.03, -0.1, -(L - 0.005)]
        tube(kit, f"forearm {name}", [(0, 0, z) for z in zs], [0.054, 0.047, 0.034], t_fore, fore, sides=8,
             front=(0, 1, 0), bulge=(0.02, 0))
        zc = zs[0] - (13.5 / 32) * (zs[0] - zs[2])
        r = 0.054 + (0.047 - 0.054) * min(1.0, (zs[0] - zc) / 0.13)
        tube(kit, f"sleeve cuff {name}", [(0, 0, zc + 0.014), (0, 0, zc - 0.014)], r + 0.009, cuff, fore, sides=8,
             caps=(False, False))
        hand = kit.empty(f"hand {name}", fore, (0, 0, -L))
        set_root_matrix(root, hand, W, RG)
        wg = Vector(wrist_g)
        return hand, (lambda pts: [tuple(Vector(p) - wg) for p in pts])

    # right hand: fist around the tilted grip, index finger on the trigger, thumb along the frame
    hand_r, gp = arm("R", (-0.008, 0.112, -0.092), (-0.12, 0.2, -0.15))
    up = Vector((0, -math.sin(math.radians(16)), math.cos(math.radians(16))))
    front = Vector((0, -math.cos(math.radians(16)), -math.sin(math.radians(16))))
    gc = Vector((-0.006, 0.046, -0.065))
    tube(kit, "palm R", gp([(-0.008, 0.112, -0.092), (-0.01, 0.088, -0.078), gc + Vector((-0.008, 0.03, 0.004))]),
         [(0.032, 0.026), (0.038, 0.03), (0.036, 0.03)], skin, hand_r, sides=8, front=(1, 0, 0))
    tube(kit, "fist R", gp([gc - up * 0.05, gc - up * 0.012, gc + up * 0.026]), [(0.032, 0.036), (0.036, 0.042), (0.032, 0.037)],
         t_fist, hand_r, sides=8, front=tuple(front), bulge=(0.012, 0.008))
    tube(kit, "index finger R", gp([(-0.022, 0.014, -0.036), (-0.014, -0.01, -0.043), (-0.003, -0.02, -0.05),
                                    (0.004, -0.012, -0.058)]), [0.0115, 0.011, 0.0105, 0.009], skin, hand_r, sides=6,
         bulge=(0, 0.004))
    tube(kit, "thumb R", gp([(0.018, 0.075, -0.05), (0.029, 0.045, -0.034), (0.031, 0.016, -0.026), (0.029, -0.006, -0.024)]),
         [0.016, 0.013, 0.011, 0.0095], skin, hand_r, sides=6, bulge=(0, 0.005))
    kit.empty("socket hand R", hand_r, tuple(-Vector((-0.008, 0.112, -0.092))))

    # left hand: palm on the open left side of the grip, four fingers wrapped over the right fingers, thumb forward
    hand_l, gp = arm("L", (0.072, 0.09, -0.15), (0.17, 0.19, -0.12))
    tube(kit, "palm L", gp([(0.072, 0.09, -0.15), (0.054, 0.062, -0.118), (0.045, 0.035, -0.098)]),
         [(0.034, 0.026), (0.04, 0.024), (0.036, 0.021)], skin, hand_l, sides=8, front=(1, 0, 0))
    for i in range(4):
        z = -0.078 - 0.019 * i
        x0 = 0.044 - 0.002 * i
        tube(kit, f"finger L {i}", gp([(x0, 0.03, z), (0.03, 0.0, z), (0.004, -0.014, z + 0.002), (-0.024, -0.008, z + 0.003),
                                       (-0.04, 0.012 + 0.004 * i, z + 0.003)]), [0.0105, 0.0105, 0.0105, 0.0098, 0.0088],
             skin, hand_l, sides=6, bulge=(0, 0.004))
    tube(kit, "thumb L", gp([(0.058, 0.048, -0.084), (0.05, 0.016, -0.06), (0.042, -0.014, -0.046), (0.036, -0.036, -0.042)]),
         [0.016, 0.0135, 0.0115, 0.0098], skin, hand_l, sides=6, bulge=(0, 0.005))
    kit.empty("socket hand L", hand_l, tuple(Vector((0.045, 0.035, -0.098)) - Vector((0.072, 0.09, -0.15))))


FP_PITCH = 8.0


def tex_counter():
    c = Canvas(32, 32, LAV)
    c.speckle(random.Random(7), [LAV_D], 40)
    c.rect(0, 27, 31, 31, PINK)
    for x in range(0, 32, 4):
        c.rect(x, 28, x + 1, 31, WHITE)
    c.rect(0, 26, 31, 26, "#d63a86")
    c.rect(0, 0, 31, 2, LAV_D)
    return c


def tex_menu():
    c = Canvas(48, 24, INK)
    c.rect(0, 0, 47, 0, PINK); c.rect(0, 23, 47, 23, PINK); c.rect(0, 0, 0, 23, PINK); c.rect(47, 0, 47, 23, PINK)
    text(c, "MENU", 16, 21, YEL)
    for i, col in enumerate((WHITE, CHOC, PINK, MINT)):
        cone_icon(c, 7 + 11 * i, 3, 7, col)
    return c


def build_fp_scene(kit, root):
    eye = Vector((0, 0, 1.62))
    rig = kit.empty("fp rig", root, tuple(eye), (FP_PITCH, 0, 0))
    build_fp_arms(kit, rig)
    sock = next(o for o in rig.children_recursive if o.name.startswith("socket hand R"))
    gun = kit.empty("held pistol", sock)
    build_gun(kit, gun)

    R = kit.rand
    # counter
    counter = kit.empty("counter", root, (0, -0.95, 0))
    tbox(kit, "counter body", (0, 0, 0.5), (3.6, 0.7, 1.0), tex_mat("counter", tex_counter()), counter,
         uv={'pz': (0.1, 0.1, 0.2, 0.2)})
    tbox(kit, "counter top", (0, 0.02, 1.025), (3.64, 0.76, 0.05), solid(kit, "counter top", "#b9b2e6", shade="#a49cd8"),
         counter)
    # back wall with the serving window
    wall = solid(kit, "wall", LAV, shade=LAV_D)
    frame = solid(kit, "window frame", PINK)
    for i, (c, s) in enumerate((((-1.45, 0, 1.9), (1.0, 0.08, 1.8)), ((1.45, 0, 1.9), (1.0, 0.08, 1.8)),
                                ((0, 0, 1.15), (1.9, 0.08, 0.3)), ((0, 0, 2.5), (1.9, 0.08, 0.6)))):
        ob = tbox(kit, f"wall {i}", c, s, wall, root, loc=(0, -1.34, 0))
        ob.visible_shadow = False
    for i, (c, s) in enumerate((((-0.97, 0, 1.75), (0.06, 0.12, 0.92)), ((0.97, 0, 1.75), (0.06, 0.12, 0.92)),
                                ((0, 0, 2.2), (2.0, 0.12, 0.06)))):
        ob = tbox(kit, f"window frame {i}", c, s, frame, root, loc=(0, -1.34, 0))
        ob.visible_shadow = False
    tbox(kit, "serving ledge", (0, -1.42, 1.3), (1.95, 0.3, 0.05), solid(kit, "ledge", WHITE), root)
    menu = tbox(kit, "menu board", (-1.3, -1.29, 2.15), (0.6, 0.02, 0.3), tex_mat("menu", tex_menu()), root,
                uv={'all': (0.0, 0.0, 0.05, 0.05), 'py': (0.0, 0.0, 1.0, 1.0)})
    menu.visible_shadow = False
    # kitchen props on the counter
    tub = kit.empty("flavor tub", root, (0.62, -0.92, 1.05))
    tube(kit, "tub", [(0, 0, 0), (0, 0, 0.3)], [0.15, 0.17], tex_mat("flavor tub", tex_tub(R)), tub, sides=10, caps=(True, False))
    tube(kit, "tub ice cream", [(0, 0, 0.26), (0, 0, 0.3)], [0.16, 0.15], tex_mat("mint chip", tex_mint_chip(R)), tub,
         sides=10, bulge=(0, 0.04))
    tool = kit.empty("scooper", tub, (0.03, 0.02, 0.31), (0, 30, 150))
    tube(kit, "scooper handle", [(0, 0, 0.04), (0, 0, 0.2)], 0.015, solid(kit, "prop yellow", YEL), tool, sides=6)
    lowball(kit, "scooper bowl", (0, 0, 0.0), (0.038, 0.038, 0.028), solid(kit, "steel", STEEL, shade="#a9a2e0"), tool)
    for i, (x, y, col) in enumerate(((0.2, -0.98, PINK), (0.33, -1.08, MINT), (0.12, -1.1, YEL), (0.2, -0.98, WHITE))):
        z = 1.05 + (0.13 if i == 3 else 0)
        p = kit.empty(f"pint {i}", root, (x, y, z), (0, 0, R.uniform(0, 40)))
        tube(kit, f"pint {i}", [(0, 0, 0), (0, 0, 0.12)], [0.05, 0.058], tex_mat(f"pint {col}", tex_pint(col if col != WHITE else CHOC)),
             p, sides=8)
        tube(kit, f"pint lid {i}", [(0, 0, 0.12), (0, 0, 0.135)], 0.062, solid(kit, f"pint lid {col}", hex_scale(col, 0.85)), p,
             sides=8)
    t_waffle = tex_mat("waffle", tex_waffle())
    for i in range(3):
        cone = kit.empty(f"cone {i}", root, (-0.62 + 0.03 * i, -1.0, 1.05 + 0.06 * i), (180, 0, 0))
        tube(kit, f"cone {i}", [(0, 0, -0.16), (0, 0, 0.0)], [0.004, 0.05], t_waffle, cone, sides=8, caps=(False, False))
    # outside: road and a walker shuffling toward the window
    tbox(kit, "road", (0, -12, -0.65), (40, 22, 0.1), solid(kit, "asphalt", ASPH, 0.2, shade="#2f2848"), root)
    for i, x in enumerate((-3, 3)):
        tbox(kit, f"lane mark {i}", (x * 0.25, -6 - 3 * i, -0.595), (0.12, 1.2, 0.01), solid(kit, "lane", YEL, 0.5), root)
    z = kit.empty("outside walker", root, (0.55, -5.2, -0.6), (0, 0, 172))
    build_zombie(kit, z)
    point_light(kit, root, "kitchen light", (0, -0.5, 2.6), "#fff4e2", 50, 6, 0.6)
    point_light(kit, root, "fp fill", (0.3, 0.45, 2.0), "#fff4e2", 2.5, 2, 0.2)
    point_light(kit, root, "fp pink", (0.9, -0.2, 1.3), PINK, 10, 2.5, 0.3)
    point_light(kit, root, "window blue", (0.0, -2.5, 2.2), BLUE, 120, 8, 0.6)


FP_CAM = ((0, 0, 1.62), (0, -1, 1.62 - math.tan(math.radians(FP_PITCH))), 24)


# ---------------------------------------------------------------- walker variants
GREEN_D = "#5fb52e"


def tex_walker_head(rand, kind):
    skin = WALKER_SKIN[kind]
    c = Canvas(64, 64, skin)
    c.speckle(rand, [hex_scale(skin, 0.86), hex_scale(skin, 1.12)], 150)
    sock = hex_scale(skin, 0.68)
    c.rect(16, 28, 17, 35, hex_scale(skin, 0.8)); c.rect(47, 28, 48, 35, hex_scale(skin, 0.8))
    c.dots([(31, 30), (33, 30), (31, 29), (33, 29)], hex_scale(skin, 0.4))
    if kind == 'worker':
        c.rect(0, 40, 15, 63, "#4a3326"); c.rect(49, 40, 63, 63, "#4a3326"); c.rect(16, 45, 48, 63, "#4a3326")
        c.speckle(rand, [hex_scale(skin, 0.62)], 70, 10, 27)                  # stubble
        c.rect(23, 40, 29, 41, "#2a5a12"); c.rect(35, 40, 41, 41, "#2a5a12")   # heavy brow
        c.rect(23, 33, 29, 39, sock); c.rect(35, 33, 41, 39, sock)
        for x0 in (24, 36):
            c.rect(x0, 35, x0 + 4, 37, YEL); c.rect(x0 + 2, 35, x0 + 2, 37, RED)
        c.rect(24, 18, 40, 25, "#2a0f2e")
        for x in range(25, 40):
            c.rect(x, 22, x, 24, "#fff1c7" if x % 2 else "#e8d27a")
            c.rect(x, 19, x, 20, "#fff1c7" if x % 2 == 0 else "#e8d27a")
        c.rect(33, 22, 34, 24, "#2a0f2e")
        c.rect(40, 30, 44, 33, RED); c.dots([(41, 31), (43, 32)], DRED)       # gash
        c.rect(20, 41, 22, 44, "#ffc29e"); c.rect(19, 42, 23, 43, "#ffc29e")   # plaster
    elif kind == 'mail':
        c.rect(0, 30, 17, 63, HAIR); c.rect(47, 30, 63, 63, HAIR); c.rect(16, 48, 48, 63, HAIR)
        c.rect(23, 32, 29, 39, "#2a0f2e"); c.rect(24, 33, 28, 38, DRED); c.dots([(25, 36), (27, 34)], RED)  # empty socket
        c.rect(35, 33, 40, 39, WHITE); c.rect(37, 35, 38, 36, INK); c.dots([(35, 38), (40, 34)], RED)
        c.rect(23, 41, 29, 41, HAIR); c.rect(35, 42, 40, 42, HAIR)
        c.rect(25, 26, 39, 28, HAIR); c.dots([(24, 25), (40, 25), (23, 24), (41, 24)], HAIR)  # mustache
        c.rect(28, 14, 36, 24, "#2a0f2e")
        for x in range(28, 37):
            c.set(x, 24, "#fff1c7" if x % 2 else "#e8d27a")
        c.rect(30, 12, 34, 19, "#ff5d7a"); c.rect(32, 13, 32, 18, "#d8337a")  # lolling tongue
        c.rect(43, 18, 46, 21, RED)
    else:  # granny
        GH = "#ddd5f2"
        c.rect(0, 26, 17, 63, GH); c.rect(47, 26, 63, 63, GH); c.rect(16, 46, 48, 63, GH)
        for x in range(0, 64, 3):
            c.set(x, 47 + (x * 5) % 9, "#b4a8d8"); c.set(x + 1, 30 + (x * 7) % 26, "#b4a8d8")
        for x in range(18, 47):
            c.set(x, 45 + (x % 3 == 0), GH)
        c.rect(22, 41, 28, 41, hex_scale(skin, 0.75)); c.rect(36, 41, 42, 41, hex_scale(skin, 0.75))  # wrinkles
        for x0 in (23, 34):                                                    # glasses
            c.rect(x0, 32, x0 + 7, 39, INK)
            c.rect(x0 + 1, 33, x0 + 6, 38, "#e8f4ff")
            c.rect(x0 + 3, 35, x0 + 4, 36, INK)
            c.set(x0 + 5, 37, WHITE)
        c.rect(31, 37, 33, 37, INK); c.rect(17, 37, 22, 37, INK); c.rect(42, 37, 47, 37, INK)
        c.rect(22, 27, 24, 29, "#ff8fae"); c.rect(40, 27, 42, 29, "#ff8fae")
        c.rect(28, 18, 36, 23, "#2a0f2e"); c.rect(29, 19, 35, 19, "#ff5d7a")
        c.rect(33, 22, 33, 23, "#fff1c7")
        c.dots([(27, 22), (27, 19), (37, 21), (36, 24), (28, 24), (26, 20)], RED)  # lipstick smear
        c.set(38, 26, "#3f6a1f")                                                  # mole
        c.rect(44, 42, 46, 44, RED)
    return c


WALKER_SKIN = {'worker': ZG, 'mail': "#86f0a0", 'granny': "#c4f08c"}


def tex_worker_torso(rand):
    c = Canvas(64, 64, ORNG)
    c.speckle(rand, ["#e8752b", "#ffa060"], 70, 12, 60)
    c.rect(0, 0, 63, 8, "#3a6fd8"); c.speckle(rand, ["#2f5cc0"], 30, 0, 8)
    c.rect(0, 9, 63, 10, "#6e3a1e"); c.rect(30, 9, 33, 10, YEL)
    c.rect(28, 11, 36, 63, "#e8e4f0"); c.speckle(rand, ["#c8c0d8"], 20, 11, 56)
    for x in range(28, 37):
        c.rect(x, 11, x, 11 + rand.choice((1, 2, 3)), ZG)
    for y0 in (19, 33):
        for x in range(64):
            if not 27 <= x <= 37:
                c.rect(x, y0, x, y0 + 2, "#eef0ff"); c.set(x, y0 + 1, "#b9bfe0" if x % 3 else WHITE)
    for x in (23, 24, 40, 41, 8, 9, 55, 56):
        c.rect(x, 36, x, 63, "#eef0ff")
    c.rect(27, 11, 27, 63, "#c85a1a"); c.rect(37, 11, 37, 63, "#c85a1a")
    c.rect(41, 24, 46, 30, "#e0651f"); c.rect(43, 30, 43, 33, YEL); c.set(43, 34, PINK)  # pocket + pencil
    c.rect(28, 58, 36, 63, ZG); c.rect(0, 62, 63, 63, "#c85a1a"); c.rect(28, 62, 36, 63, ZG)
    text(c, "CREW", 57, 30, INK)
    for (hx, hy, r) in ((12, 26, 3), (50, 44, 2)):
        for y in range(hy - r - 1, hy + r + 2):
            for x in range(hx - r - 1, hx + r + 2):
                d = (x - hx) ** 2 + (y - hy) ** 2
                if d <= r * r:
                    c.set(x, y, ZG)
                elif d <= (r + 1) ** 2:
                    c.set(x, y, "#b84a14")
    for i in range(6):
        c.set(30 + i, 42 - i, RED); c.set(31 + i, 42 - i, DRED)
    for dx, ln in ((31, 6), (35, 9)):
        c.rect(dx, 36 - ln, dx, 36, RED)
    return c


def tex_worker_arm(rand):
    c = Canvas(16, 32, ZG)
    c.speckle(rand, ["#7fe03f", "#b6ff7d"], 50)
    c.rect(0, 0, 15, 15, "#e8324a")
    for y in range(0, 16, 4):
        c.rect(0, y, 15, y, "#a01830")
    for x in range(0, 16, 4):
        c.rect(x, 0, x, 15, "#a01830")
    for y in range(2, 16, 4):
        c.rect(0, y, 15, y, "#ff6a7a")
    c.rect(0, 14, 15, 16, "#ff8f9c"); c.rect(0, 16, 15, 16, "#c82a40")
    c.rect(0, 0, 15, 1, DRED)
    c.rect(5, 21, 8, 23, RED); c.set(6, 22, DRED)
    c.dots([(2, 26), (12, 19)], GREEN_D)
    return c


def tex_glove():
    c = Canvas(16, 16, "#f0b860")
    for x in (2, 6, 10, 14):
        c.rect(x, 6, x, 15, "#c98a3a")
    c.rect(0, 0, 15, 3, "#d99a48"); c.rect(0, 3, 15, 3, "#a86a28")
    c.rect(6, 13, 7, 15, ZG); c.set(7, 13, "#e8d27a")
    return c


def tex_worker_leg(rand):
    c = Canvas(16, 32, "#3a6fd8")
    c.speckle(rand, ["#2f5cc0", "#5a8af0"], 40)
    c.rect(4, 0, 4, 31, "#2a52b0")
    c.rect(1, 13, 7, 18, ZG); c.dots([(1, 15), (3, 16), (5, 15), (7, 14)], WHITE); c.rect(3, 14, 4, 15, RED)
    c.dots([(10, 24), (11, 25), (12, 9)], "#6e3a1e")
    c.rect(0, 29, 15, 31, "#2a52b0")
    return c


def tex_boot():
    c = Canvas(16, 16, "#9a5a2a")
    c.rect(0, 0, 2, 15, "#5a3014"); c.rect(13, 0, 15, 15, "#5a3014")
    for y in (4, 6, 8):
        c.rect(6, y, 9, y, YEL)
    c.rect(4, 13, 11, 15, "#c4bcef"); c.rect(4, 13, 11, 13, "#8f88c8")
    c.rect(3, 0, 12, 2, "#7a4420")
    return c


def tex_hardhat():
    c = Canvas(32, 16, YEL)
    c.rect(0, 0, 31, 1, "#e0b21a")
    c.rect(15, 2, 17, 15, "#ffd21a"); c.rect(0, 2, 1, 15, "#ffd21a"); c.rect(31, 2, 31, 15, "#ffd21a")
    disc(c, 8, 7, 2, PINK); c.set(8, 8, WHITE)
    c.dots([(22, 9), (23, 8), (24, 9)], "#d9a010")
    c.speckle(random.Random(11), ["#f5d23a"], 14, 2, 15)
    return c


SHIRT = "#8fc4ff"; NAVY = "#24307a"


def tex_mail_torso(rand):
    c = Canvas(64, 64, SHIRT)
    c.speckle(rand, ["#7ab2f0", "#a8d4ff"], 80, 11, 60)
    c.rect(0, 0, 63, 8, NAVY); c.rect(0, 9, 63, 10, INK); c.rect(30, 9, 33, 10, STEEL)
    for y in range(14, 58, 7):
        c.set(32, y, WHITE)
    c.rect(31, 11, 31, 57, "#7ab2f0")
    c.rect(30, 26, 33, 55, NAVY); c.rect(29, 54, 34, 58, NAVY); c.rect(31, 24, 32, 25, NAVY)
    for y in range(28, 54, 5):
        c.rect(30, y, 33, y, RED)
    for x0 in (20, 37):
        c.rect(x0, 38, x0 + 7, 46, "#7ab2f0"); c.rect(x0, 44, x0 + 7, 46, "#6aa0e0")
    c.rect(22, 44, 22, 48, RED)
    c.rect(26, 58, 37, 63, WHITE); c.rect(29, 59, 35, 63, "#86f0a0")
    text(c, "MAIL", 57, 52, NAVY)
    for (hx, hy, r) in ((7, 26, 4), (52, 34, 2)):
        for y in range(hy - r - 1, hy + r + 2):
            for x in range(hx - r - 1, hx + r + 2):
                d = (x - hx) ** 2 + (y - hy) ** 2
                if d <= r * r:
                    c.set(x, y, "#86f0a0")
                elif d <= (r + 1) ** 2:
                    c.set(x, y, RED)
    for y in (24, 26, 28):
        c.rect(5, y, 9, y, WHITE)
    for i in range(10):
        c.set(26 - i // 3, 57 - i, RED)
    return c


def tex_mail_arm(rand):
    c = Canvas(16, 32, "#86f0a0")
    c.speckle(rand, ["#6fd88a", "#a8ffbe"], 50)
    c.rect(0, 0, 15, 11, SHIRT); c.rect(0, 11, 15, 12, "#6aa0e0")
    c.rect(9, 4, 13, 8, WHITE); c.rect(10, 5, 12, 7, BLUE); c.set(11, 6, RED)
    c.rect(0, 0, 15, 1, DRED)
    c.rect(4, 20, 7, 22, RED); c.set(5, 21, DRED)
    return c


def tex_mail_leg(rand):
    c = Canvas(16, 32, "#86f0a0")
    c.speckle(rand, ["#6fd88a", "#a8ffbe"], 30)
    c.rect(0, 0, 15, 9, NAVY); c.rect(12, 0, 12, 9, RED)
    for x in range(16):
        c.rect(x, 9, x, 9 + rand.choice((0, 1)), NAVY)
    c.rect(4, 14, 6, 16, RED)
    c.rect(0, 20, 15, 31, WHITE); c.rect(0, 22, 15, 23, NAVY); c.rect(0, 24, 15, 24, RED)
    return c


def tex_mail_shoe():
    c = Canvas(16, 16, "#2b2340")
    c.rect(0, 0, 2, 15, WHITE); c.rect(13, 0, 15, 15, WHITE)
    c.rect(6, 4, 9, 9, "#3d3358")
    return c


def tex_mailbag():
    c = Canvas(32, 32, "#a85a2a")
    c.rect(0, 14, 31, 31, "#8a4520")
    for x in range(1, 31, 2):
        c.set(x, 15, "#e8c48a")
    c.rect(14, 12, 17, 18, YEL); c.rect(15, 13, 16, 17, "#8a4520")
    text(c, "MAIL", 9, 27, WHITE)
    return c


def tex_letter():
    c = Canvas(16, 8, WHITE)
    c.rect(11, 4, 14, 7, PINK); c.set(12, 5, WHITE)
    for y in (2, 4):
        c.rect(2, y, 8, y, "#b4a8d8")
    return c


ROBE = "#ff9ad5"; ROBE_D = "#e872b8"; ROBE_L = "#ffc4e8"; GOWN = "#c8b4ff"


def chenille(c, y0, y1):
    for y in range(y0, y1 + 1, 3):
        for x in range(y % 2, c.w, 3):
            c.set(x, y, ROBE_L)


def tex_granny_torso(rand):
    c = Canvas(64, 64, ROBE)
    chenille(c, 0, 63)
    c.speckle(rand, [ROBE_D], 50)
    for y in range(38, 64):
        half = (y - 38) // 3 + 1
        c.rect(32 - half, y, 32 + half, y, GOWN)
        c.set(32 - half - 1, y, ROBE_L); c.set(32 - half - 2, y, ROBE_L)
        c.set(32 + half + 1, y, ROBE_L); c.set(32 + half + 2, y, ROBE_L)
    c.dots([(31, 50), (33, 46), (30, 56), (34, 55), (32, 42)], WHITE); c.dots([(33, 52), (29, 59)], YEL)
    for y in range(16, 38):
        c.set(32 + (38 - y) // 5, y, ROBE_D)
    c.rect(0, 13, 63, 16, PURP); c.rect(0, 13, 63, 13, "#6a3fd6")
    c.rect(36, 11, 40, 18, PURP); c.rect(37, 12, 39, 17, "#a57bff")
    c.rect(41, 20, 48, 28, ROBE_D); c.rect(42, 21, 47, 27, ROBE); c.rect(43, 27, 46, 29, WHITE)
    c.rect(29, 60, 35, 63, "#c4f08c")
    c.rect(18, 52, 22, 56, RED); c.dots([(19, 53), (21, 55)], DRED)
    c.dots([(10, 30), (11, 29), (12, 30), (50, 40), (51, 41)], ZG)
    return c


def tex_robe_skirt(rand):
    c = Canvas(64, 16, ROBE)
    chenille(c, 2, 15)
    c.speckle(rand, [ROBE_D], 20)
    c.rect(0, 0, 63, 2, ROBE_L); c.rect(0, 3, 63, 3, ROBE_D)
    c.rect(35, 0, 35, 15, ROBE_D); c.rect(36, 0, 37, 15, ROBE_L)
    c.rect(38, 7, 39, 15, PURP); c.rect(40, 10, 41, 15, PURP); c.rect(38, 7, 39, 7, "#6a3fd6")
    for (x, y) in ((12, 8), (52, 5)):
        c.rect(x, y, x + 2, y + 1, ZG); c.set(x + 1, y - 1, ZG)
    c.rect(24, 4, 25, 6, RED)
    return c


def tex_granny_arm(rand):
    c = Canvas(16, 32, ROBE)
    chenille(c, 2, 21)
    c.rect(0, 21, 15, 23, ROBE_L)
    c.rect(0, 24, 15, 31, "#c4f08c"); c.dots([(3, 27), (11, 29)], "#9fc86a"); c.rect(7, 26, 7, 30, PURP)
    c.rect(0, 0, 15, 1, DRED)
    return c


def tex_granny_hand():
    c = Canvas(16, 16, "#c4f08c")
    for x in (2, 6, 10, 14):
        c.rect(x, 6, x, 12, "#9fc86a")
    c.rect(0, 13, 15, 15, RED); c.dots([(1, 15), (5, 15), (9, 15), (13, 15)], "#ff8fae")
    c.rect(4, 8, 5, 9, YEL)
    return c


def tex_granny_leg(rand):
    c = Canvas(16, 32, "#c4f08c")
    c.speckle(rand, ["#b0e07a", "#d8ffa8"], 30)
    for x0 in (3, 10):
        y = 8
        x = x0
        while y < 27:
            c.set(x, y, PURP); y += 1; x += rand.choice((-1, 0, 1))
    c.rect(0, 27, 15, 31, "#ffe0c8"); c.rect(0, 27, 15, 27, "#e8c0a0")
    return c


def tex_slipper(rand):
    c = Canvas(16, 16, "#8fc8ff")
    c.speckle(rand, ["#b8dcff", "#7ab2f0"], 50)
    c.rect(0, 0, 2, 15, WHITE); c.rect(13, 0, 15, 15, WHITE)
    return c


WALKERS = {
    'worker': dict(hips=(0, 0, -8), spine=(18, -4, 10), head=(-16, 20, -12), w=(1.16, 1.12), hip_x=0.11, k=1.15,
                   armR=((0.08, -1, 0.5), (-12, 0, 0), (-36, 0, 0)), armL=((0.22, -0.2, -1), (-28, 0, 0), (-8, 0, 0)),
                   legL=((-14, 0, 6), (12, 0, 0)), legR=((10, 0, -7), (6, 0, 0)),
                   hit=dict(hips=(0, 0, 10), spine=(-14, 12, -14), head=(-30, -12, 20),
                            armR=((-0.7, 0.1, 0.9), (-30, 0, 0), (20, 0, 0)), legL=((12, -4, 12), (10, 0, 0)),
                            legR=((-22, 0, -6), (30, 0, 0)))),
    'mail': dict(hips=(0, 0, 6), spine=(24, 5, -8), head=(-34, -16, 14), w=(1.0, 1.0), hip_x=0.095, k=1.0,
                 armR=((-0.02, -1, 0.78), (-8, 0, 0), (-30, 0, 0)), armL=((0.04, -1, 0.62), (-16, 0, -6), (-38, 0, 0)),
                 legL=((8, 0, 5), (8, 0, 0)), legR=((-18, 0, -3), (16, 0, 0)),
                 hit=dict(hips=(0, 0, 12), spine=(-16, 10, -12), head=(-36, 14, 22),
                          armR=((-0.75, 0.2, 0.85), (-26, 0, 0), (24, 0, 0)), legL=((14, -4, 10), (8, 0, 0)),
                          legR=((-24, 0, -6), (32, 0, 0)))),
    'granny': dict(hips=(0, 0, 4), spine=(36, 0, 6), head=(-50, 10, -8), w=(0.95, 1.06), hip_x=0.085, k=0.92,
                   armR=((-0.05, -0.75, 1), (-24, 0, 0), (-30, 0, 0)), armL=((0.18, -0.45, -1), (-34, 0, 0), (-14, 0, 0)),
                   legL=((-12, 0, 3), (18, 0, 0)), legR=((6, 0, -4), (16, 0, 0)),
                   hit=dict(hips=(0, 0, 10), spine=(6, 12, -14), head=(-40, -14, 20),
                            armR=((-0.7, 0.0, 1.0), (-30, 0, 0), (20, 0, 0)), legL=((10, -4, 10), (14, 0, 0)),
                            legR=((-20, 0, -6), (34, 0, 0)))),
}


def walker_arm(kit, parent, name, loc, d, elbow, wrist, t_arm, t_hand, k=1.0, bell=None):
    """zombie_arm with a thickness factor and an optional flared bell sleeve; returns (shoulder pivot, hand pivot)."""
    piv = kit.empty(f"arm {name}", parent, loc)
    aim(piv, d)
    tube(kit, f"upper arm {name}", [(0, 0, 0.03), (0, 0, -0.14), (0, 0, -0.28)], [0.062 * k, 0.056 * k, 0.048 * k], t_arm,
         piv, sides=6, front=(0, 1, 0), v=(0.0, 0.5), bulge=(0.02, 0.0))
    fore = kit.empty(f"forearm {name}", piv, (0, 0, -0.28), elbow)
    tube(kit, f"forearm {name}", [(0, 0, 0.02), (0, 0, -0.13), (0, 0, -0.26)], [0.048 * k, 0.045 * k, 0.034 * k], t_arm,
         fore, sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    if bell:
        tube(kit, f"sleeve {name}", [(0, 0, 0.0), (0, 0, -0.07), (0, 0, -0.13)], [0.058, 0.068, 0.082], bell, fore, sides=6,
             front=(0, 1, 0), caps=(False, False))
    hand = kit.empty(f"hand {name}", fore, (0, 0, -0.26), wrist)
    tube(kit, f"hand {name}", [(0, 0, 0.01), (0, 0, -0.06), (0, 0, -0.13)],
         [(0.044 * k, 0.026 * k), (0.05 * k, 0.026 * k), (0.04 * k, 0.02 * k)], t_hand, hand, sides=6, front=(0, 1, 0),
         bulge=(0, 0.015))
    return piv, hand


def walker_leg(kit, parent, name, loc, thigh, knee, t_leg, foot_mat, foot, k=1.0, pom=None):
    """zombie_leg with a thickness factor and boot / shoe / slipper feet."""
    piv = kit.empty(f"leg {name}", parent, loc, thigh)
    tube(kit, f"thigh {name}", [(0, 0, 0.04), (0, 0, -0.2), (0, 0, -0.42)], [(0.08 * k, 0.085 * k), 0.068 * k, 0.056 * k],
         t_leg, piv, sides=6, front=(0, 1, 0), v=(0.0, 0.5))
    shin = kit.empty(f"shin {name}", piv, (0, 0, -0.42), knee)
    tube(kit, f"shin {name}", [(0, 0, 0.02), (0, -0.01, -0.2), (0, 0, -0.4)], [0.056 * k, 0.05 * k, 0.042 * k], t_leg, shin,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    ft = kit.empty(f"foot {name}", shin, (0, 0, -0.43), (-(thigh[0] + knee[0]), 0, 0))
    if foot == 'boot':
        tube(kit, f"boot cuff {name}", [(0, 0.01, 0.1), (0, 0.01, 0.0)], [0.06, 0.062], foot_mat, ft, sides=6,
             front=(0, 0, 1), caps=(True, False))
        tube(kit, f"boot {name}", [(0, 0.06, 0.0), (0, -0.04, 0.008), (0, -0.15, -0.008)], [(0.062, 0.055), (0.066, 0.058),
                                                                                         (0.054, 0.036)],
             foot_mat, ft, sides=6, front=(0, 0, 1), bulge=(0.015, 0.035))
    elif foot == 'slipper':
        tube(kit, f"slipper {name}", [(0, 0.055, -0.01), (0, -0.04, -0.005), (0, -0.14, -0.018)],
             [(0.058, 0.04), (0.064, 0.044), (0.05, 0.026)], foot_mat, ft, sides=6, front=(0, 0, 1), bulge=(0.015, 0.03))
        lowball(kit, f"pom {name}", (0, -0.12, 0.02), (0.035, 0.035, 0.03), pom, ft, smooth=False)
    else:
        tube(kit, f"shoe {name}", [(0, 0.05, 0.0), (0, -0.04, 0.005), (0, -0.13, -0.01)],
             [(0.05, 0.044), (0.055, 0.048), (0.044, 0.03)], foot_mat, ft, sides=6, front=(0, 0, 1), bulge=(0.015, 0.03))
    return piv, ft


ZT_PTS = [(0, 0, -0.08), (0, 0, 0.05), (0, 0.015, 0.2), (0, 0.045, 0.36), (0, 0.06, 0.5), (0, 0.05, 0.585)]
ZT_RAD = [(0.15, 0.1), (0.152, 0.104), (0.135, 0.1), (0.158, 0.11), (0.185, 0.115), (0.085, 0.07)]


def on_torso(pts, rad, x, z, side=-1, pad=0.012):
    """y of the torso surface at lateral x and height z (side -1 = front, +1 = back) plus pad."""
    i = max(0, min(len(pts) - 2, next((j for j in range(len(pts) - 1) if z <= pts[j + 1][2]), len(pts) - 2)))
    t = max(0.0, min(1.0, (z - pts[i][2]) / (pts[i + 1][2] - pts[i][2])))
    cy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
    rx = rad[i][0] + (rad[i + 1][0] - rad[i][0]) * t
    ry = rad[i][1] + (rad[i + 1][1] - rad[i][1]) * t
    return cy + side * (ry + pad) * math.sqrt(max(0.0, 1 - (x / (rx + pad)) ** 2))


def build_walker(kit, root, kind='worker', hit=False):
    """Walker zombie in one of three outfits. Same rig as build_zombie: hips > spine > head / arms (shoulder,
    elbow, wrist pivots) and legs (hip, knee, ankle pivots); every limb detaches."""
    W = WALKERS[kind]
    P = W['hit'] if hit else W
    R = kit.rand
    t_head = tex_mat(f"{kind} head", tex_walker_head(R, kind))
    pts = [(x, y * W['w'][1], z) for x, y, z in ZT_PTS]
    rad = [(rx * W['w'][0], ry * W['w'][1]) for rx, ry in ZT_RAD]
    if kind == 'worker':
        t_torso, t_arm, t_hand = tex_mat("worker torso", tex_worker_torso(R)), tex_mat("worker arm", tex_worker_arm(R)), \
            tex_mat("work glove", tex_glove())
        t_leg = tex_mat("jeans", tex_worker_leg(R))
        foot_mat, foot, bell, pom = tex_mat("work boot", tex_boot()), 'boot', None, None
    elif kind == 'mail':
        t_torso, t_arm, t_hand = tex_mat("mail torso", tex_mail_torso(R)), tex_mat("mail arm", tex_mail_arm(R)), \
            tex_mat("zombie hand", tex_zombie_hand())
        t_leg = tex_mat("mail leg", tex_mail_leg(R))
        foot_mat, foot, bell, pom = tex_mat("mail shoe", tex_mail_shoe()), 'shoe', None, None
    else:
        t_torso, t_arm, t_hand = tex_mat("robe", tex_granny_torso(R)), tex_mat("robe arm", tex_granny_arm(R)), \
            tex_mat("granny hand", tex_granny_hand())
        t_leg = tex_mat("granny leg", tex_granny_leg(R))
        foot_mat, foot = tex_mat("slipper", tex_slipper(R)), 'slipper'
        bell, pom = solid(kit, "robe sleeve", ROBE, shade=ROBE_L), solid(kit, "pom", WHITE, 0.5)

    hips = kit.empty("hips", root, (0, 0.02, 0.9), P['hips'])
    spine = kit.empty("spine", hips, (0, 0, 0), P['spine'])
    tube(kit, "torso", pts, rad, t_torso, spine)
    head = kit.empty("head", spine, (0, 0.02 * W['w'][1], 0.57), P['head'], (1.12, 1.12, 1.12))
    tube(kit, "head", [(0, 0, 0), (0, -0.02, 0.05), (0, -0.035, 0.08), (0, -0.04, 0.13), (0, -0.035, 0.19),
                       (0, -0.03, 0.245), (0, -0.025, 0.285), (0, -0.02, 0.3)],
         [0.046, 0.052, (0.088, 0.088), (0.1, 0.104), (0.104, 0.11), (0.096, 0.104), (0.07, 0.078), (0.03, 0.035)],
         t_head, head, bulge=(0, 0.008))

    sx = 0.2 * W['w'][0]
    armR, handR = walker_arm(kit, spine, "R", (-sx, 0.05, 0.5), *P['armR'], t_arm, t_hand, W['k'], bell)
    armL, handL = walker_arm(kit, spine, "L", (sx, 0.05, 0.5), *W['armL'], t_arm, t_hand, W['k'], bell)
    hx = W['hip_x']
    lp, lf = walker_leg(kit, hips, "L", (hx, 0, 0), *P['legL'], t_leg, foot_mat, foot, W['k'] if kind == 'worker' else 1.0,
                        pom)
    rp, rf = walker_leg(kit, hips, "R", (-hx, 0, 0), *P['legR'], t_leg, foot_mat, foot, W['k'] if kind == 'worker' else 1.0,
                        pom)
    extra = []

    if kind == 'worker':
        hat = kit.empty("hard hat", head, (0, -0.033, 0.17), (-6, 0, 0))
        t_hat = tex_mat("hard hat", tex_hardhat())
        tube(kit, "hard hat", [(0, 0, 0.0), (0, 0, 0.06), (0, 0, 0.11), (0, 0, 0.14)],
             [(0.116, 0.126), (0.112, 0.122), (0.08, 0.09), (0.028, 0.032)], t_hat, hat, caps=(True, True), bulge=(0, 0.01))
        tube(kit, "hard hat brim", [(0, -0.018, -0.004), (0, -0.018, 0.012)], [(0.15, 0.172), (0.138, 0.16)],
             solid(kit, "hat brim", "#ffd21a", shade="#e0b21a"), hat, sides=8)
        tbox(kit, "hard hat ridge", (0, -0.005, 0.12), (0.03, 0.2, 0.04), solid(kit, "hat ridge", "#ffd21a"), hat, rot=(-8, 0, 0))
        extra.append((hat, (-0.12, 0.28, 0.6), (70, 25, 150)))
        wr = kit.empty("wrench", handL, (0, -0.03, -0.09), (0, 0, 0))
        steel = solid(kit, "wrench steel", STEEL, shade="#a9a2e0")
        tbox(kit, "wrench handle", (0, 0, -0.1), (0.026, 0.014, 0.3), steel, wr)
        tube(kit, "wrench jaw", [(-0.028, 0, -0.25), (-0.04, 0, -0.29), (0, 0, -0.315), (0.04, 0, -0.29), (0.028, 0, -0.25)],
             0.014, steel, wr, sides=4, side=(0, 1, 0))
        tube(kit, "wrench grip", [(0, 0, 0.0), (0, 0, 0.09)], 0.02, solid(kit, "wrench grip", RED), wr, sides=6)
    elif kind == 'mail':
        cap = kit.empty("mail cap", head, (0, -0.035, 0.19), (-8, 0, 0))
        tube(kit, "cap crown", [(0, 0, 0.0), (0, 0, 0.05), (0, 0, 0.08)], [(0.112, 0.12), (0.118, 0.128), (0.104, 0.112)],
             tex_mat("mail cap", tex_mail_cap()), cap, caps=(False, True), bulge=(0, 0.018))
        lowball(kit, "cap bill", (0, -0.13, 0.004), (0.095, 0.075, 0.012), solid(kit, "cap bill", NAVY), cap, smooth=False)
        extra.append((cap, (-0.18, 0.22, 0.5), (-60, 30, 100)))
        # satchel strap across the chest, bag on the left hip
        strap = solid(kit, "satchel strap", "#8a4520", shade="#6a3418")
        sp = [(-0.115, on_torso(pts, rad, -0.115, 0.585, 1, 0.01), 0.5), (-0.12, 0.05, 0.615)]
        for t in (0.0, 0.25, 0.5, 0.75, 1.0):
            x = -0.115 + 0.27 * t
            z = 0.53 - 0.52 * t
            sp.append((x, on_torso(pts, rad, x, z, -1, 0.012), z))
        tube(kit, "satchel strap", sp, [(0.022, 0.006)] * len(sp), strap, spine, sides=4, front=(0, -1, 0.3),
             caps=(False, False))
        bag = kit.empty("mailbag", spine, (0.2, -0.02, 0.0), (0, 0, -8))
        tbox(kit, "mailbag", (0, 0, -0.06), (0.09, 0.28, 0.22), tex_mat("mailbag", tex_mailbag()), bag,
             uv={'px': (0, 0, 1, 1), 'nx': (0, 0, 1, 1), 'all': (0, 0, 0.1, 0.1)})
        tbox(kit, "mailbag flap", (0.048, 0, 0.0), (0.012, 0.29, 0.12), tex_mat("mailbag", tex_mailbag()), bag,
             uv={'px': (0, 0.5, 1, 1), 'all': (0, 0.5, 0.1, 0.6)})
        t_let = tex_mat("letter", tex_letter())
        for i, (y, tilt) in enumerate(((-0.08, -12), (-0.02, 6), (0.05, -4), (0.1, 14))):
            tbox(kit, f"letter {i}", (0, y, 0.07 + 0.012 * (i % 2)), (0.012, 0.1, 0.06), t_let, bag, rot=(tilt, 0, 0))
    else:
        skirt = tex_mat("robe skirt", tex_robe_skirt(R))
        tube(kit, "robe skirt", [(0, 0.01, 0.06), (0, 0.0, -0.15), (0, -0.01, -0.35), (0, -0.01, -0.5)],
             [(0.155, 0.112), (0.19, 0.15), (0.22, 0.18), (0.235, 0.195)], skirt, hips, caps=(False, False))
        for i, (y, h) in enumerate(((0.03, 0.09), (0.06, 0.13))):
            tube(kit, f"sash tail {i}", [(0.065 + 0.03 * i, on_torso(pts, rad, 0.07, 0.0, -1, 0.01), 0.02),
                                         (0.07 + 0.035 * i, -0.13 - 0.01 * i, -h)], [(0.018, 0.005), (0.015, 0.004)],
                 solid(kit, "sash", PURP, shade="#6a3fd6"), spine, sides=4, front=(0, -1, 0))
        cols = [PINK, BLUE, YEL, MINT, PURP, PINK, BLUE]
        for i, (x, y, z, a) in enumerate(((-0.04, -0.105, 0.255, -40), (0.04, -0.105, 0.255, -40), (-0.045, -0.04, 0.3, -8),
                                          (0.045, -0.04, 0.3, -8), (-0.04, 0.03, 0.28, 30), (0.04, 0.03, 0.28, 30),
                                          (0.0, 0.08, 0.215, 60))):
            cp = kit.empty(f"curler {i}", head, (x, y, z), (a, 0, 0))
            tube(kit, f"curler {i}", [(-0.036, 0, 0), (0.036, 0, 0)], 0.024, solid(kit, f"curler {cols[i]}", cols[i], 0.45),
                 cp, sides=6, side=(0, 1, 0))
            tube(kit, f"curler pin {i}", [(-0.042, 0, 0), (0.042, 0, 0)], 0.006, solid(kit, "pin", WHITE), cp, sides=4,
                 side=(0, 1, 0))
            if i in (1, 3, 6):
                extra.append((cp, ((0.25, -0.3, 0.45), (0.35, 0.05, 0.55), (-0.2, 0.2, 0.6))[(i - 1) // 2 if i < 6 else 2],
                               (40 * i, 80, 30 * i)))
        lowball(kit, "hair bun", (0, 0.1, 0.17), (0.06, 0.05, 0.055), solid(kit, "grey hair", "#ddd5f2", shade="#b4a8d8"), head)

    bpy.context.view_layer.update()
    inv = root.matrix_world.inverted()
    low = min((inv @ f.matrix_world.translation).z for f in (lf, rf))
    hips.location.z -= low - (0.06 if foot == 'boot' else 0.035)

    if hit:
        walker_hit_fx(kit, root, kind, armL, extra, bag if kind == 'mail' else None)


def tex_mail_cap():
    c = Canvas(32, 16, "#2c4fd6")
    c.rect(0, 0, 31, 3, NAVY)
    c.rect(14, 5, 18, 10, WHITE); c.rect(15, 6, 17, 9, BLUE); c.set(16, 8, RED)
    c.rect(0, 12, 31, 15, "#3a5ee0")
    return c


def walker_hit_fx(kit, root, tag, armL, extra, bag):
    """Left arm flies off toward the camera's right (plus hat / curlers), stump burst, trails, star, splats."""
    fx, to_fx = fx_frame(kit, root, f"{tag} fx")
    S = to_fx @ root_pos(root, armL)
    parts = [(armL, (0.68, -0.44, 0.48), (40, -75, 65))] + extra
    old = {id(ob): to_fx @ root_pos(root, ob) for ob, _, _ in parts}
    fling(root, parts)
    pal = fx_palette(kit)
    fx_cube(kit, fx, f"{tag} stump", S + Vector((0.01, -0.01, 0)), 0.075, pal['red'])
    D = Vector((0.75, -0.42, 0.52)).normalized()
    burst(kit, fx, S, D, tag, blood=16, cream=12, sprinkles=28, blobs=3)
    for ob, off, _ in parts:
        a = old[id(ob)]
        trail(kit, fx, a, a + to_fx @ Vector(off), f"{tag} {ob.name}", n=5 if ob is armL else 3, size=0.05)
    fx_star(kit, fx, f"{tag} star", S + D * 0.08 + Vector((0.04, -0.11, 0)), 8, 0.26, 0.11, YEL, 1.4, (0, 0, 21))
    fx_star(kit, fx, f"{tag} star core", S + D * 0.08 + Vector((0.05, -0.13, 0)), 6, 0.1, 0.05, WHITE, 1.6, (0, 12, 21))
    if bag:
        t_let = tex_mat("letter", tex_letter())
        B = to_fx @ root_pos(root, bag)
        R = kit.rand
        for i in range(7):
            p = B + Vector((R.uniform(0.05, 0.55), R.uniform(-0.45, 0.05), R.uniform(0.05, 0.75)))
            tbox(kit, f"{tag} flying letter {i}", (0, 0, 0), (0.1, 0.004, 0.06), t_let, fx, loc=p,
                 rot=(R.uniform(-40, 40), R.uniform(-60, 60), R.uniform(0, 60)))
    base = Vector((S.x, S.y, 0))
    floor_splats(kit, fx, base, [(0.35, -0.2, 0.22, 'red'), (0.62, -0.42, 0.13, 'red'), (0.1, -0.35, 0.1, 'red'),
                                 (0.5, 0.05, 0.16, 0), (0.78, -0.15, 0.1, 1), (0.2, 0.15, 0.09, 2)], tag, dots=10)


# ---------------------------------------------------------------- frozen walker
def tex_ice(rand):
    c = Canvas(32, 32, "#7ff7d6")
    a = Canvas(32, 32, grey(0.4))
    for i in range(5):                                     # diagonal sheen streaks
        x0 = rand.randrange(32)
        for t in range(32):
            c.set(x0 + t // 2, t, "#b8fff0"); a.set(x0 + t // 2, t, grey(0.55))
    c.speckle(rand, ["#5ee8c4", "#a8fff0"], 60)
    for i in range(7):                                     # cracks: random walks, white with teal shadow
        x, y = rand.randrange(32), rand.randrange(32)
        for _ in range(rand.randint(8, 16)):
            c.set(x, y, WHITE); a.set(x, y, grey(0.95))
            c.set(x + 1, y - 1, "#1fbf95"); a.set(x + 1, y - 1, grey(0.75))
            x += rand.choice((-1, 0, 1)); y += rand.choice((-1, 1))
    c.rect(0, 0, 31, 0, "#c8fff4"); a.rect(0, 0, 31, 0, grey(0.8))
    return c, a


def build_frozen_walker(kit, root):
    """build_zombie inside a mint ice block. The block is 9 shell chunks (3 sectors x 3 tiers) plus crystal
    spikes, each its own object with its origin at its center so the game can shatter it."""
    body = kit.empty("walker", root)
    build_zombie(kit, body)
    R = kit.rand
    ice = alpha_mat("mint ice", *tex_ice(R), emit=0.55)
    ice_solid = solid(kit, "ice shard", "#a8fff0", 0.6, shade="#5ee8c4")
    N, TZ = 9, (0.0, 0.66, 1.3, 1.98)
    cx, cy, rx, ry = 0.0, -0.2, 0.5, 0.62
    A = [2 * math.pi * k / N + R.uniform(-0.12, 0.12) for k in range(N)]
    J = [[R.uniform(0.9, 1.1) for _ in range(4)] for _ in range(N)]
    Z = [[TZ[t] + (0 if t == 0 else R.uniform(-0.07, 0.07) if t < 3 else R.uniform(-0.12, 0.08)) for t in range(4)]
         for _ in range(N)]
    apex = Vector((cx + 0.04, cy + 0.03, 2.16))

    def P(k, t):
        k %= N
        s = 1 - 0.05 * t
        return Vector((cx + math.cos(A[k]) * rx * J[k][t] * s, cy + math.sin(A[k]) * ry * J[k][t] * s, Z[k][t]))

    blocks = kit.empty("ice block", root)
    for t in range(3):
        for s in range(3):
            ks = list(range(s * 3, s * 3 + 4))
            quads = [(P(k, t), P(k + 1, t), P(k + 1, t + 1), P(k, t + 1)) for k in ks[:-1]]
            tris = [(P(k, 3), P(k + 1, 3), apex) for k in ks[:-1]] if t == 2 else []
            allp = [p for q in quads + tris for p in q]
            ctr = sum(allp, Vector()) / len(allp)
            bm = bmesh.new()
            uvl = bm.loops.layers.uv.new("UVMap")
            for poly, kk in [(q, k) for q, k in zip(quads, ks)] + [(tr, k) for tr, k in zip(tris, ks)]:
                fc = bm.faces.new([bm.verts.new(p - ctr) for p in poly])
                for lp, p in zip(fc.loops, poly):
                    ang = (math.atan2((p.y - cy) / ry, (p.x - cx) / rx) / (2 * math.pi)) % 1.0
                    lp[uvl].uv = (ang * 3.0 + (0.0 if len(poly) == 4 else 0.0), p.z / 1.05)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            ob = kit.mesh_from_bmesh(f"ice chunk {t} {s}", bm, ice, blocks, tuple(ctr), smooth=False)
            ob.visible_shadow = False
    # crystal spikes on top and at the base
    for i, (p, d, ln, r) in enumerate((((0.12, -0.05, 2.0), (0.4, -0.2, 1), 0.34, 0.07), ((-0.2, -0.32, 1.95), (-0.5, -0.3, 1), 0.28, 0.06),
                                       ((0.0, 0.1, 2.02), (0.0, 0.5, 1), 0.22, 0.05), ((0.42, -0.5, 0.0), (0.7, -0.3, 0.6), 0.36, 0.08),
                                       ((-0.45, 0.05, 0.0), (-0.8, 0.2, 0.5), 0.3, 0.07), ((-0.1, -0.78, 0.0), (0.1, -0.9, 0.5), 0.26, 0.06))):
        sp = kit.empty(f"ice spike {i}", blocks, p)
        aim(sp, d)
        ob = tube(kit, f"ice spike {i}", [(0, 0, 0.04), (0, 0, -ln * 0.6), (0, 0, -ln)], [r, r * 0.8, 0.004], ice, sp, sides=6,
                  front=(0, 1, 0), smooth=False)
        ob.visible_shadow = False
    # frost on the floor and loose shards
    for i, (x, y, rr) in enumerate(((0.0, -0.2, 0.78), (0.55, -0.75, 0.22), (-0.6, -0.55, 0.16), (0.4, 0.4, 0.14))):
        splat(kit, f"frost {i}", (x, y), rr, solid(kit, "frost", "#c8fff4", 0.5, shade="#7ff7d6"), root, lobes=13, z=0.003 + 0.001 * i)
    for i in range(9):
        a = R.uniform(0, 2 * math.pi)
        d = R.uniform(0.62, 0.95)
        s = R.uniform(0.04, 0.09)
        tbox(kit, f"ice shard {i}", (0, 0, 0), (s, s * 0.8, s * 1.4), ice_solid, root,
             loc=(math.cos(a) * d * 0.9, -0.2 + math.sin(a) * d, s * 0.5), rot=(R.uniform(-30, 30), R.uniform(-30, 30), R.uniform(0, 90)))
    # the mint scoop that did it, melting down the top
    mint = tex_mat("mint chip", tex_mint_chip(R))
    lowball(kit, "mint scoop", (apex.x - 0.04, apex.y - 0.05, 2.17), (0.15, 0.15, 0.11), mint, blocks)
    for i, (x, y, ln) in enumerate(((-0.17, -0.2, 0.32), (0.06, -0.28, 0.45), (-0.02, -0.14, 0.2))):
        tube(kit, f"mint drip {i}", [(x, y - 0.06, 2.12), (x * 1.5, y * 1.9 - 0.08, 2.08 - ln * 0.4), (x * 1.7, y * 2.2 - 0.08, 2.08 - ln)],
             [0.035, 0.026, 0.018], mint, blocks, sides=5, bulge=(0, 0.015))
    for i, p in enumerate(((0.38, -0.7, 1.55), (-0.42, -0.6, 0.9), (0.3, -0.62, 0.45), (-0.1, -0.86, 1.82))):
        fx_star(kit, root, f"sparkle {i}", Vector(p), 4, 0.07, 0.016, WHITE, 1.8, (0, 0, 21))


# ---------------------------------------------------------------- spectator ghost
def tex_ghost():
    c = Canvas(32, 32, "#f4ecff")
    c.speckle(random.Random(9), ["#e4d8ff"], 40)
    c.rect(0, 0, 31, 3, "#c8b8ff"); c.rect(0, 4, 31, 4, "#d8ccff")
    for x0 in (11, 19):
        c.rect(x0, 17, x0 + 2, 23, INK); c.rect(x0 + 1, 16, x0 + 1, 24, INK)
        c.set(x0 + 1, 22, WHITE); c.set(x0 + 1, 21, WHITE)
    c.rect(15, 12, 17, 14, INK); c.set(16, 12, "#ff6f8f")
    c.rect(8, 14, 10, 15, "#ff8fae"); c.rect(22, 14, 24, 15, "#ff8fae")
    return c


def build_ghost(kit, root):
    """Floating ghost marker for a dead player: body pivot at 1.0 m (bob), little arm nubs (wave), paper hat."""
    body = kit.empty("ghost body", root, (0, 0, 1.0))
    t_ghost = tex_mat("ghost", tex_ghost(), emit=0.65)
    ob = tube(kit, "ghost", [(0, 0, 0), (0, 0, 0.08), (0, 0, 0.2), (0, 0, 0.32), (0, 0, 0.4), (0, 0, 0.45)],
              [(0.2, 0.19), (0.19, 0.18), (0.18, 0.17), (0.165, 0.158), (0.12, 0.114), (0.04, 0.038)], t_ghost, body,
              caps=(False, True), bulge=(0, 0.03))
    for i in range(8):
        v = ob.data.vertices[i]
        v.co.z += -0.06 if i % 2 else 0.02
        v.co.x *= 1.08; v.co.y *= 1.08
    glow = solid(kit, "ghost glow", "#f4ecff", 0.65, shade="#e4d8ff")
    for sx, name in ((1, "L"), (-1, "R")):
        arm = kit.empty(f"arm {name}", body, (sx * 0.16, -0.01, 0.2))
        aim(arm, (sx * 1, -0.3, 0.55 if sx > 0 else -0.2))
        tube(kit, f"arm {name}", [(0, 0, 0.02), (0, 0, -0.07), (0, 0, -0.12)], [0.045, 0.036, 0.024], glow, arm, sides=6,
             bulge=(0, 0.015))
    hat = kit.empty("paper hat", body, (0.01, 0.0, 0.36), (-6, 14, 0), (0.85, 0.85, 0.85))
    tube(kit, "paper hat", [(0, 0.004, 0.0), (0, 0.004, 0.04), (0, 0.004, 0.095), (0, 0.004, 0.14)],
         [(0.125, 0.133), (0.119, 0.143), (0.066, 0.147), (0.013, 0.139)], tex_mat("hat", tex_hat()), hat, caps=(False, True))
    splat(kit, "ground shadow", (0, 0), 0.2, solid(kit, "ghost shadow", "#120a24", 0.05), root, lobes=12, z=0.003)
    ring_mesh(kit, "marker ring", 0.26, 0.31, solid(kit, "marker ring", "#c8b8ff", 1.0), root, (0, 0, 0.006))


# ---------------------------------------------------------------- batch
ASSETS = [
    ("Player Pink", named("Player Pink", build_team_player, team='pink')),
    ("Player Blue", named("Player Blue", build_team_player, team='blue')),
    ("Player Mint", named("Player Mint", build_team_player, team='mint')),
    ("Player Yellow", named("Player Yellow", build_team_player, team='yellow')),
    ("Player T-Pose", named("Player T-Pose", build_team_player, team='blue', tpose=True)),
    ("First-Person Arms", named("First-Person Arms", build_fp_arms)),
    ("Walker Worker", named("Walker Worker", build_walker, kind='worker')),
    ("Walker Worker Hit", named("Walker Worker Hit", build_walker, kind='worker', hit=True)),
    ("Walker Mail Carrier", named("Walker Mail Carrier", build_walker, kind='mail')),
    ("Walker Mail Carrier Hit", named("Walker Mail Carrier Hit", build_walker, kind='mail', hit=True)),
    ("Walker Granny", named("Walker Granny", build_walker, kind='granny')),
    ("Walker Granny Hit", named("Walker Granny Hit", build_walker, kind='granny', hit=True)),
    ("Frozen Walker", named("Frozen Walker", build_frozen_walker)),
    ("Spectator Ghost", named("Spectator Ghost", build_ghost)),
]
SPACING = 12


def build_team_lineup(kit, root):
    for i, team in enumerate(('pink', 'blue', 'mint', 'yellow')):
        p = kit.empty(f"lineup {team}", root, ((i - 1.5) * 0.9, 0, 0), (0, 0, 200 if i % 2 else 20))
        named(f"Player {team.title()}", build_team_player, team=team)(kit, p)


SCENES = [
    dict(name="first-person view", build=build_fp_scene, cam=FP_CAM, res=(1600, 900)),
    dict(name="team lineup", build=build_team_lineup, cam=((0.3, -4.6, 1.6), (0, 0, 0.95), 40), res=(1600, 900)),
]
