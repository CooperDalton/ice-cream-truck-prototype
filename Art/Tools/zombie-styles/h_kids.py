"""Kids and crew poses batch (style H, heist pitch): five chunky kid customers (coins, waves, a cone) and three
gunless crew poses built on the team player (throwing a cone, carrying the rocky road tub)."""
from style_H import *
from h_characters import named, set_root_matrix, TEAMS, build_team_player, tex_team_arm, tex_team_shoe

GOLD = "#ffd23a"; GOLD_D = "#e09a1a"; DENIM = "#4a7fd6"; DENIM_D = "#34609f"


# ---------------------------------------------------------------- kid textures
def tex_kid_head(K):
    """64x64 cylinder face canvas (u=0.5 faces -Y). Rows map linearly to head height: row = z / 0.38 * 64."""
    c = Canvas(64, 64, K['skin'])
    hair, sk_d = K['hair'], hex_scale(K['skin'], 0.86)
    # crown and back of the head
    c.rect(0, 44, 63, 63, hair)
    for x in range(64):
        if x < 15 or x > 48:
            c.rect(x, K.get('nape', 16) + (x * 5) % 3, x, 44, hair)
    # fringe
    bangs = K['bangs']
    if bangs == 'fringe':
        for x in range(15, 49):
            c.rect(x, 39 - (x % 3 == 0) - (x % 5 == 1), x, 44, hair)
    elif bangs == 'side':
        for x in range(15, 49):
            c.rect(x, 37 + (x - 15) // 6, x, 44, hair)
    elif bangs == 'spiky':
        for x in range(15, 49):
            c.rect(x, 38 + (2 if x % 4 < 2 else 0), x, 44, hair)
    else:
        c.rect(15, 41, 48, 44, hair)
    # ears
    c.rect(14, 22, 15, 30, sk_d); c.rect(48, 22, 49, 30, sk_d)
    # brows
    c.rect(23, 34, 27, 35, hair); c.rect(36, 34, 40, 35, hair)
    # eyes: big dark ovals with an iris band and a highlight
    for x0 in (23, 36):
        if K.get('eyes') == 'happy':
            c.rect(x0, 27, x0 + 4, 28, INK); c.rect(x0 - 1, 26, x0 - 1, 26, INK); c.rect(x0 + 5, 26, x0 + 5, 26, INK)
        else:
            c.rect(x0, 25, x0 + 4, 31, INK)
            c.rect(x0 + 1, 25, x0 + 3, 27, K['iris'])
            c.rect(x0 + 1, 29, x0 + 2, 30, WHITE)
            c.set(x0 + 3, 26, WHITE)
    if K.get('glasses'):
        g = K['glasses']
        for cx in (25, 38):
            for y in range(20, 36):
                for x in range(cx - 7, cx + 8):
                    d = (x - cx) ** 2 + ((y - 28) * 0.95) ** 2
                    if 26 <= d <= 52:
                        c.set(x, y, g)
        c.rect(31, 29, 32, 30, g)
        c.rect(14, 29, 17, 30, g); c.rect(46, 29, 49, 30, g)
    # nose, blush, freckles
    c.rect(31, 22, 32, 22, sk_d); c.set(32, 23, sk_d)
    c.rect(19, 20, 22, 22, "#ff8fae"); c.rect(41, 20, 44, 22, "#ff8fae")
    if K.get('freckles'):
        c.dots([(20, 23), (22, 24), (21, 22), (42, 23), (44, 24), (43, 22)], "#c4682e")
    # mouth
    m, lip = K['mouth'], "#8a1f3d"
    if m == 'grin':
        c.rect(26, 19, 37, 19, lip)
        c.rect(27, 15, 36, 18, lip)
        c.rect(28, 18, 35, 18, WHITE)
        c.rect(29, 15, 34, 16, "#ff6f8f")
        c.rect(28, 14, 35, 14, lip)
    elif m == 'ooh':
        c.rect(29, 14, 34, 19, lip)
        c.rect(30, 15, 33, 17, "#ff6f8f")
        c.rect(28, 15, 28, 18, lip); c.rect(35, 15, 35, 18, lip)
    elif m == 'lick':
        c.rect(27, 18, 36, 18, lip)
        c.rect(28, 16, 35, 17, lip)
        c.rect(30, 14, 33, 17, "#ff6f8f")
        c.rect(31, 15, 32, 15, "#e04f78")
    else:
        c.rect(27, 17, 36, 17, lip); c.dots([(26, 18), (37, 18)], lip)
        c.rect(28, 16, 35, 16, lip)
    return c


def tex_kid_torso(K):
    """64x32 shirt canvas; rows map to z 0.38-0.72 (row = (z-0.38)/0.34*32)."""
    shirt, top = K['shirt'], K['top']
    c = Canvas(64, 32, shirt)
    if top == 'stripes':
        for y in range(9, 30):
            if (y // 3) % 2:
                c.rect(0, y, 63, y, K['shirt2'])
    if top == 'hoodie':
        c.rect(0, 0, 63, 2, hex_scale(shirt, 0.78))
        for y in range(5, 15):
            half = 10 - (y - 5) // 3
            c.rect(32 - half, y, 31 + half, y, hex_scale(shirt, 0.86))
        c.rect(32 - 10, 5, 31 + 10, 5, hex_scale(shirt, 0.7))
        c.rect(31, 15, 32, 29, hex_scale(shirt, 0.7))
        c.rect(29, 18, 34, 22, WHITE); c.rect(30, 19, 33, 21, K['print'])
    else:
        c.rect(0, 0, 63, 8, K['bottom'])
        c.rect(0, 9, 63, 9, hex_scale(K['bottom'], 0.75))
        if top == 'dress':
            c.rect(0, 0, 63, 9, shirt)
            c.rect(0, 9, 63, 10, WHITE)
            for i, (x, y) in enumerate(((10, 14), (22, 20), (44, 15), (54, 22), (4, 23), (34, 12))):
                c.rect(x, y, x + 1, y + 1, WHITE)
            for x in range(22, 42):
                c.rect(x, 26 - int(abs(x - 31.5) // 4), x, 29, WHITE)
            c.rect(30, 22, 33, 24, K['print']); c.set(31, 23, WHITE)
    # neckline
    c.rect(26, 29, 37, 31, K['skin'])
    c.rect(25, 28, 38, 28, hex_scale(shirt, 0.8))
    p = K['print']
    if top == 'heart':
        rows = ["..##...##..", ".####.####.", "###########", "###########", ".#########.", "..#######..",
                "...#####...", "....###....", ".....#....."]
        for r, row in enumerate(rows):
            for q, ch in enumerate(row):
                if ch == '#':
                    c.set(27 + q, 24 - r, p)
        c.dots([(29, 23), (30, 23), (29, 22)], WHITE)
    if top == 'star':
        rows = ["....#....", "...###...", "#########", ".#######.", "..#####..", ".###.###.", ".##...##."]
        for r, row in enumerate(rows):
            for q, ch in enumerate(row):
                if ch == '#':
                    c.set(28 + q, 24 - r, p)
        c.rect(27, 25, 37, 25, hex_scale(shirt, 0.8)); c.rect(27, 16, 37, 16, hex_scale(shirt, 0.8))
    return c


def tex_kid_arm(K):
    c = Canvas(16, 32, K['skin'])
    n = K.get('sleeve', 8)
    c.rect(0, 0, 15, n, K['shirt'])
    c.rect(0, n, 15, n, hex_scale(K['shirt'], 0.8))
    if n > 20:
        c.rect(0, n - 3, 15, n - 1, hex_scale(K['shirt'], 0.82))
    return c


def tex_kid_leg(K):
    c = Canvas(16, 32, K['skin'])
    low = K['legwear']
    if low == 'jeans':
        c.rect(0, 0, 15, 31, K['bottom'])
        c.rect(0, 0, 15, 2, K['shirt'])
        c.rect(0, 28, 15, 31, hex_scale(K['bottom'], 1.25))
        c.rect(7, 3, 7, 27, hex_scale(K['bottom'], 0.85))
    else:
        if low == 'shorts':
            c.rect(0, 0, 15, 10, K['bottom'])
            c.rect(0, 10, 15, 10, hex_scale(K['bottom'], 0.75))
        sock = 22 if low == 'kneesocks' else 27
        c.rect(0, sock, 15, 31, WHITE)
        c.rect(0, sock + 1, 15, sock + 1, K['sock'])
    return c


# ---------------------------------------------------------------- kids
KIDS = {
    'pigtails': dict(h=0.97, skin=SKIN, hair=HAIR, iris="#6a3b1a", bangs='fringe', mouth='grin', nape=14,
                     shirt="#ff6fb4", top='heart', print=RED, bottom=DENIM, legwear='shorts', sock=PINK,
                     shoe=dict(trim=WHITE, light=PINK, dark="#d63a86")),
    'cap': dict(h=1.0, skin="#c98a5f", hair="#2a1a12", iris="#2a1a12", bangs='none', mouth='grin', nape=22,
                shirt=MINT, top='star', print=YEL, bottom=ORNG, legwear='shorts', sock=MINT,
                shoe=dict(trim=RED, light="#ff8a9a", dark=DRED)),
    'glasses': dict(h=0.93, skin="#f7d2b6", hair="#e0702a", iris=BLUE, bangs='side', mouth='lick', nape=20,
                    freckles=True, glasses=INK, shirt=YEL, shirt2=WHITE, top='stripes', print=YEL, bottom=PURP,
                    legwear='shorts', sock=YEL, shoe=dict(trim=BLUE, light="#8fbfff", dark="#1f5fd0")),
    'curly': dict(h=1.03, skin="#a8673f", hair="#2b160e", iris="#2b160e", bangs='fringe', mouth='ooh', nape=14,
                  shirt=LAV, top='dress', print=PINK, bottom=LAV, legwear='kneesocks', sock=LAV,
                  shoe=dict(trim=YEL, light="#fff09a", dark="#d99a0f")),
    'hoodie': dict(h=1.02, skin="#e0a27a", hair="#1d1720", iris="#3a2414", bangs='spiky', mouth='grin', nape=20,
                   shirt=BLUE, top='hoodie', print=YEL, bottom="#2b3a8f", legwear='jeans', sleeve=27, sock=WHITE,
                   shoe=dict(trim=ORNG, light="#ffc08a", dark="#c9601c")),
}

# arm poses in 1.0-scale root space: (elbow, wrist, hand kind) per side; shoulders at (+-0.155, 0, 0.655)
KID_POSES = {
    'pigtails': {'R': ((-0.25, -0.05, 0.8), (-0.27, -0.09, 0.96), 'coin up'),
                 'L': ((0.25, -0.03, 0.79), (0.33, -0.07, 0.93), 'open')},
    'cap': {'R': ((-0.2, -0.13, 0.55), (-0.13, -0.29, 0.62), 'coin forward'),
            'L': ((0.29, -0.02, 0.79), (0.3, -0.04, 0.96), 'open')},
    'glasses': {'R': ((-0.19, -0.11, 0.5), (-0.07, -0.2, 0.62), 'cone'),
                'L': ((0.18, -0.03, 0.49), (0.12, -0.15, 0.45), 'fist')},
    'curly': {'R': ((-0.21, -0.11, 0.76), (-0.25, -0.22, 0.95), 'open'),
              'L': ((0.21, -0.11, 0.76), (0.25, -0.22, 0.95), 'open')},
    'hoodie': {'R': ((-0.2, -0.1, 0.79), (-0.25, -0.18, 0.95), 'point'),
               'L': ((0.19, -0.1, 0.5), (0.11, -0.22, 0.57), 'coin forward')},
}


def coin(kit, parent, name, center, root):
    """Gold coin facing -Y, parented to the hand that holds it."""
    p = kit.empty(f"{name} pivot", parent)
    set_root_matrix(root, p, center, Matrix.Identity(3))
    tube(kit, name, [(0, 0.006, 0), (0, -0.006, 0)], 0.043, solid(kit, "coin", GOLD, 0.75, shade=GOLD_D), p, sides=10,
         front=(0, 0, 1), smooth=False)
    tube(kit, f"{name} face", [(0, 0.0, 0), (0, -0.009, 0)], 0.027, solid(kit, "coin face", "#ffe98a", 0.8, shade=GOLD),
         p, sides=8, front=(0, 0, 1), smooth=False)
    return p


def waffle_cone(kit, parent, name, tip, d, root, k=1.0, scoop=PINK):
    """Waffle cone with one scoop: tip at `tip`, opening along d (root space)."""
    p = kit.empty(f"{name} pivot", parent)
    set_root_matrix(root, p, tip, Vector(d).to_track_quat('Z', 'Y').to_matrix())
    tube(kit, name, [(0, 0, 0), (0, 0, 0.12 * k), (0, 0, 0.13 * k)], [0.006 * k, 0.04 * k, 0.044 * k],
         tex_mat("waffle", tex_waffle()), p, sides=8, front=(0, -1, 0), caps=(True, False))
    sc = solid(kit, f"scoop {scoop}", scoop, 0.42)
    lowball(kit, f"{name} scoop", (0, 0, 0.16 * k), (0.052 * k, 0.052 * k, 0.048 * k), sc, p)
    tube(kit, f"{name} drip", [(0, 0, 0.128 * k), (0, 0, 0.145 * k)], [0.05 * k, 0.054 * k], sc, p, sides=8)
    lowball(kit, f"{name} cherry", (0.01 * k, -0.01 * k, 0.212 * k), (0.014 * k,) * 3, solid(kit, "cherry", RED, 0.5), p)
    return p


def arm2(kit, parent, name, S, E, W, t_arm, joint, r=(0.044, 0.04, 0.036, 0.033), v=(0.0, 0.5, 1.0)):
    """Two-segment arm: upper pivot at the shoulder S aimed at the elbow E, forearm pivot aimed at the wrist W,
    wrist pivot at W (local -Z continues along the forearm). Coordinates in parent space."""
    S, E, W = Vector(S), Vector(E), Vector(W)
    q1 = (E - S).to_track_quat('-Z', 'Y')
    q2 = (W - E).to_track_quat('-Z', 'Y')
    a, b = (E - S).length, (W - E).length
    up = kit.empty(name, parent, S)
    up.rotation_euler = q1.to_euler()
    tube(kit, f"{name} upper", [(0, 0, 0.02), (0, 0, -a * 0.5), (0, 0, -a)], [r[0], r[1] * 1.02, r[1]], t_arm, up,
         sides=6, front=(0, 1, 0), bulge=(0.02, 0), v=(v[0], v[1]))
    lowball(kit, f"{name} elbow", (0, 0, -a), (r[1] * 0.98,) * 3, joint, up)
    fore = kit.empty(f"{name} forearm", up, (0, 0, -a))
    fore.rotation_euler = (q1.inverted() @ q2).to_euler()
    tube(kit, f"{name} forearm", [(0, 0, 0.0), (0, 0, -b * 0.5), (0, 0, -b)], [r[2], r[2] * 0.98, r[3]], t_arm, fore,
         sides=6, front=(0, 1, 0), v=(v[1], v[2]))
    wrist = kit.empty(f"{name} wrist", fore, (0, 0, -b))
    return wrist


def kid_hand(kit, wrist, name, skin, kind, sx, s):
    """Chunky mitten hand on the wrist pivot. kind: open, fist, point, coin..., cone. sx = +1 left, -1 right."""
    k = s
    if kind == 'open':
        tube(kit, f"{name} hand", [(0, 0, 0.01), (0, 0, -0.03 * k), (0, 0, -0.07 * k), (0, 0, -0.085 * k)],
             [(0.03 * k, 0.022 * k), (0.044 * k, 0.022 * k), (0.042 * k, 0.02 * k), (0.026 * k, 0.016 * k)], skin, wrist,
             sides=6, front=(0, 1, 0))
        tube(kit, f"{name} thumb", [(-sx * 0.03 * k, 0, -0.02 * k), (-sx * 0.06 * k, 0, -0.045 * k)], [0.014 * k, 0.011 * k],
             skin, wrist, sides=5)
    else:
        tube(kit, f"{name} hand", [(0, 0, 0.01), (0, 0, -0.03 * k), (0, 0, -0.065 * k)],
             [(0.032 * k, 0.028 * k), (0.04 * k, 0.034 * k), (0.03 * k, 0.026 * k)], skin, wrist, sides=6,
             front=(0, 1, 0), bulge=(0, 0.012 * k))
        if kind == 'point':
            tube(kit, f"{name} finger", [(0, -0.01 * k, -0.055 * k), (0, -0.01 * k, -0.115 * k)], [0.013 * k, 0.011 * k],
                 skin, wrist, sides=5, bulge=(0, 0.006 * k))
    kit.empty(f"socket hand {'L' if sx > 0 else 'R'}", wrist, (0, 0, -0.045 * k))


def kid_hair(kit, head, name, K, s):
    hm = solid(kit, f"{name} hair", K['hair'], 0.3)
    kind = K['bangs']
    if kind == 'none':     # under the backwards cap
        return hm
    kit.prim(f"{name} hair cap", 'ico', (0.158 * s, 0.155 * s, 0.13 * s), hm, head, offset=(0, 0.035 * s, 0.265 * s),
             segments=2, smooth=False)
    return hm


def build_kid(kit, root, kind):
    K = KIDS[kind]
    s = K['h']
    P = lambda x, y, z: Vector((x * s, y * s, z * s))
    t_head = tex_mat(f"kid head {kind}", tex_kid_head(K))
    t_torso = tex_mat(f"kid torso {kind}", tex_kid_torso(K))
    t_arm = tex_mat(f"kid arm {kind}", tex_kid_arm(K))
    t_leg = tex_mat(f"kid leg {kind}", tex_kid_leg(K))
    t_shoe = tex_mat(f"kid shoe {kind}", tex_team_shoe(K['shoe']))
    skin = solid(kit, f"skin {kind}", K['skin'])
    top = K['top']

    # legs
    for sx, nm in ((1, "L"), (-1, "R")):
        leg = kit.empty(f"leg {nm}", root, P(sx * 0.068, 0, 0.44), (0, sx * -3, 0))
        r0 = 0.066 if K['legwear'] in ('shorts', 'jeans') else 0.056
        tube(kit, f"leg {nm}", [P(0, 0, 0.04), P(0, 0, -0.12), P(0, -0.008, -0.24), P(0, 0, -0.37)],
             [r0 * s, 0.058 * s, 0.05 * s, 0.045 * s], t_leg, leg, sides=6, front=(0, 1, 0))
        tube(kit, f"shoe {nm}", [P(0, 0.045, -0.395), P(0, -0.03, -0.392), P(0, -0.105, -0.405)],
             [(0.05 * s, 0.045 * s), (0.058 * s, 0.05 * s), (0.048 * s, 0.035 * s)], t_shoe, leg, sides=6,
             front=(0, 0, 1), bulge=(0.012 * s, 0.025 * s))

    # torso (chunky barrel) plus the per-outfit extras
    tube(kit, "torso", [P(0, 0, 0.37), P(0, 0, 0.41), P(0, -0.004, 0.5), P(0, -0.004, 0.6), P(0, 0, 0.68), P(0, 0, 0.72)],
         [(0.128 * s, 0.098 * s), (0.134 * s, 0.102 * s), (0.126 * s, 0.098 * s), (0.136 * s, 0.1 * s),
          (0.142 * s, 0.094 * s), (0.06 * s, 0.05 * s)], t_torso, root, sides=10, v=(0.0, 1.0))
    if top == 'dress':
        cv = Canvas(32, 8, K['shirt'])
        cv.rect(0, 0, 31, 1, WHITE)
        for x in range(1, 32, 4):
            cv.rect(x, 4, x + 1, 5, WHITE)
        tube(kit, "skirt", [P(0, 0.0, 0.49), P(0, 0.004, 0.4), P(0, 0.01, 0.3)],
             [(0.132 * s, 0.1 * s), (0.17 * s, 0.14 * s), (0.215 * s, 0.185 * s)], tex_mat(f"skirt {kind}", cv), root,
             sides=10, caps=(False, False), v=(1.0, 0.0))
        bow = solid(kit, "dress bow", PINK, 0.45)
        for sx in (1, -1):
            tbox(kit, f"bow wing {sx}", P(sx * 0.03, -0.105, 0.66), (0.05 * s, 0.02 * s, 0.04 * s), bow, root,
                 rot=(-15, 0, sx * 10))
    if top == 'hoodie':
        hood = solid(kit, "hood", hex_scale(K['shirt'], 0.9))
        tube(kit, "hood", [P(-0.12, -0.02, 0.69), P(-0.1, 0.08, 0.73), P(0, 0.13, 0.75), P(0.1, 0.08, 0.73),
                           P(0.12, -0.02, 0.69)], [0.04 * s, 0.055 * s, 0.065 * s, 0.055 * s, 0.04 * s], hood, root,
             sides=6, side=(0, 0, 1))
        cord = solid(kit, "drawstring", WHITE, 0.4)
        for sx in (1, -1):
            tube(kit, f"drawstring {sx}", [P(sx * 0.035, -0.088, 0.69), P(sx * 0.04, -0.104, 0.6)], 0.007 * s, cord,
                 root, sides=4)
            tbox(kit, f"drawstring tip {sx}", P(sx * 0.04, -0.105, 0.592), (0.014 * s, 0.014 * s, 0.022 * s), cord, root)

    # head
    head = kit.empty("head pivot", root, P(0, 0, 0.7))
    hz = [0.0, 0.04, 0.07, 0.12, 0.19, 0.26, 0.32, 0.36, 0.38]
    hr = [0.05, 0.06, (0.112, 0.115), (0.142, 0.146), (0.152, 0.157), (0.147, 0.15), (0.118, 0.12), (0.066, 0.068),
          (0.02, 0.02)]
    tube(kit, "head", [P(0, -0.006 if 0.05 < z < 0.3 else 0.0, z) for z in hz],
         [(r * s, r * s) if isinstance(r, float) else (r[0] * s, r[1] * s) for r in hr], t_head, head, sides=10,
         bulge=(0, 0.004))
    for sx in (1, -1):
        lowball(kit, f"ear {sx}", P(sx * 0.152, 0.01, 0.17), (0.022 * s, 0.03 * s, 0.038 * s), skin, head)
    hm = kid_hair(kit, head, "hair", K, s)
    if kind == 'pigtails':
        tie = solid(kit, "hair tie", PINK, 0.5)
        for sx in (1, -1):
            pt = kit.empty(f"pigtail {'L' if sx > 0 else 'R'}", head, P(sx * 0.15, 0.04, 0.27))
            lowball(kit, f"pigtail tie {sx}", P(sx * 0.012, 0, 0), (0.03 * s, 0.034 * s, 0.034 * s), tie, pt)
            tube(kit, f"pigtail {sx}", [P(sx * 0.03, 0, 0.005), P(sx * 0.08, 0.01, -0.02), P(sx * 0.11, 0.02, -0.08),
                                        P(sx * 0.115, 0.025, -0.15)],
                 [0.04 * s, 0.05 * s, 0.042 * s, 0.018 * s], hm, pt, sides=6, side=(0, 1, 0), smooth=False)
    if kind == 'curly':
        for i, (x, y, z, r) in enumerate(((0.0, 0.0, 0.37, 0.08), (0.1, 0.0, 0.34, 0.075), (-0.1, 0.0, 0.34, 0.075),
                                          (0.15, 0.03, 0.26, 0.07), (-0.15, 0.03, 0.26, 0.07), (0.16, 0.07, 0.17, 0.065),
                                          (-0.16, 0.07, 0.17, 0.065), (0.06, 0.1, 0.36, 0.075), (-0.06, 0.1, 0.36, 0.075),
                                          (0.0, 0.14, 0.27, 0.08), (0.11, 0.12, 0.22, 0.07), (-0.11, 0.12, 0.22, 0.07),
                                          (0.0, 0.14, 0.15, 0.07), (0.05, -0.08, 0.3, 0.05), (-0.06, -0.08, 0.3, 0.05))):
            lowball(kit, f"curl {i}", P(x, y, z), (r * s, r * s, r * s * 0.92), hm, head, smooth=False)
        clip = solid(kit, "hair clip", YEL, 0.55)
        tbox(kit, "hair clip", P(0.11, -0.09, 0.29), (0.05 * s, 0.02 * s, 0.024 * s), clip, head, rot=(0, -30, 0))
    if kind == 'cap':
        cv = Canvas(32, 16, MINT)
        cv.rect(0, 0, 31, 2, "#14d6a4")
        cv.rect(14, 0, 17, 4, K['hair']); cv.rect(13, 3, 18, 3, WHITE)
        cv.rect(0, 9, 31, 9, "#14d6a4")
        t_cap = tex_mat("kid cap", cv)
        tube(kit, "cap", [P(0, 0.006, 0.225), P(0, 0.006, 0.29), P(0, 0.006, 0.35), P(0, 0.006, 0.385), P(0, 0.006, 0.4)],
             [(0.155 * s, 0.16 * s), (0.151 * s, 0.156 * s), (0.122 * s, 0.126 * s), (0.075 * s, 0.078 * s),
              (0.02 * s, 0.02 * s)], t_cap, head,
             sides=10, caps=(False, True), front=(0, -1, 0))
        tbox(kit, "cap brim", P(0, 0.2, 0.235), (0.2 * s, 0.14 * s, 0.018 * s), solid(kit, "cap brim", "#14d6a4"), head,
             rot=(-8, 0, 0), taper=(0.9, 0.9))
        lowball(kit, "cap button", P(0, 0.006, 0.402), (0.02 * s,) * 3, solid(kit, "cap button", WHITE), head)
        tube(kit, "hair tuft", [P(-0.1, -0.12, 0.23), P(0, -0.15, 0.245), P(0.1, -0.12, 0.23)], 0.022 * s, hm, head,
             sides=5, side=(0, 0, 1))
    if kind == 'hoodie':
        for i, (x, z) in enumerate(((-0.08, 0.35), (0.0, 0.38), (0.08, 0.35), (-0.04, 0.37), (0.05, 0.37))):
            tube(kit, f"spike {i}", [P(x, 0.0, z - 0.03), P(x * 1.4, 0.03, z + 0.06)], [0.04 * s, 0.004 * s], hm, head,
                 sides=5, smooth=False)
    if kind == 'glasses':
        frame = solid(kit, "glasses frame", INK, 0.1)
        tube(kit, "glasses bridge", [P(-0.022, -0.158, 0.172), P(0.022, -0.158, 0.172)], 0.006 * s, frame, head,
             sides=4)

    # arms
    joint_sleeve = top == 'hoodie'
    for sx, nm in ((1, "L"), (-1, "R")):
        E, W, hand = KID_POSES[kind][nm]
        joint = solid(kit, f"elbow {kind}", K['shirt']) if joint_sleeve else skin
        wrist = arm2(kit, root, f"arm {nm}", P(sx * 0.155, 0, 0.655), P(*E), P(*W), t_arm, joint,
                     r=(0.046 * s, 0.04 * s, 0.038 * s, 0.033 * s))
        kid_hand(kit, wrist, f"arm {nm}", skin, hand.split()[0] if hand.startswith(('open', 'point')) else 'fist', sx, s)
        Wv, d = P(*W), (P(*W) - P(*E)).normalized()
        tip = Wv + d * 0.06 * s
        if hand == 'coin up':
            coin(kit, wrist, f"coin {nm}", tip + Vector((0, -0.012, 0.035)) * s, root)
        elif hand == 'coin forward':
            coin(kit, wrist, f"coin {nm}", tip + Vector((0, -0.03, 0.03)) * s, root)
        elif hand == 'cone':
            waffle_cone(kit, wrist, "cone", Wv + d * 0.035 * s + Vector((0, 0, -0.07)) * s, (0.05, -0.15, 1.0), root, k=s)


# ---------------------------------------------------------------- crew poses
def team_body(kit, root, team, drop=0.0):
    """Team player without the gun (T-pose build) with its arms removed, under a body pivot. Returns body, T."""
    body = kit.empty("body", root, (0, 0, -drop))
    build_team_player(kit, body, team=team, tpose=True)
    for ob in list(body.children):
        if ob.type == 'EMPTY' and ob.name.startswith(("arm R", "arm L")):
            for sub in list(ob.children_recursive) + [ob]:
                data = sub.data
                bpy.data.objects.remove(sub, do_unlink=True)
                if data is not None and data.users == 0:
                    bpy.data.meshes.remove(data)
    return body, TEAMS[team]


def legs(body):
    return {ob.name[:5]: ob for ob in body.children if ob.type == 'EMPTY' and ob.name.startswith("leg ")}


def build_crew_throw(kit, root):
    body, T = team_body(kit, root, 'blue', drop=0.024)
    body.rotation_euler.z = math.radians(-14)
    fwd = Matrix.Rotation(math.radians(14), 3, 'Z')     # root-space points into the twisted body space
    lg = legs(body)
    lg["leg L"].rotation_euler = (math.radians(-14), math.radians(-6), 0)
    lg["leg R"].rotation_euler = (math.radians(14), math.radians(6), 0)
    t_arm = tex_mat("arm blue", tex_team_arm(T))
    skin = solid(kit, "skin", SKIN)
    # right arm cocked back above the shoulder, cone in the fist
    E, W = Vector((-0.43, 0.17, 1.46)), Vector((-0.38, 0.36, 1.66))
    wrist = arm2(kit, body, "arm R", (-0.2, 0, 1.39), E, W, t_arm, skin,
                 r=(0.066, 0.056, 0.05, 0.04))
    tube(kit, "arm R hand", [(0, 0, 0.01), (0, 0, -0.05), (0, 0, -0.1)], [(0.042, 0.036), (0.05, 0.042), (0.038, 0.03)],
         skin, wrist, sides=6, front=(0, 1, 0), bulge=(0, 0.02))
    kit.empty("socket hand R", wrist, (0, 0, -0.06))
    d = (W - E).normalized()
    waffle_cone(kit, wrist, "cone", W + d * 0.03 + Vector((0, 0.01, -0.03)), (-0.15, 0.6, 1.0), body, k=1.35)
    # left arm points forward at the target
    S, H = Vector((0.2, 0, 1.39)), fwd @ Vector((0.1, -0.62, 1.52))
    arm_l, L = player_arm(kit, body, "arm L", S, H, t_arm, skin)
    tube(kit, "arm L finger", [(0, -0.01, -(L + 0.03)), (0, -0.01, -(L + 0.1))], [0.016, 0.013], skin, arm_l, sides=5,
         bulge=(0, 0.008))
    kit.empty("socket hand L", arm_l, (0, 0, -L))
    head = next(ob for ob in body.children if ob.name.startswith("head pivot"))
    head.rotation_euler = (math.radians(-4), 0, math.radians(12))


def build_crew_carry(kit, root, team):
    body, T = team_body(kit, root, team)
    t_arm = tex_mat(f"arm {team}", tex_team_arm(T))
    skin = solid(kit, "skin", SKIN)
    carry = Vector((0, -0.42, 0.98))
    for sx, nm in ((1, "L"), (-1, "R")):
        S = Vector((sx * 0.2, 0, 1.39))
        E = Vector((sx * 0.29, -0.16, 1.17))
        W = carry + Vector((sx * 0.225, 0.02, 0.02))
        wrist = arm2(kit, body, f"arm {nm}", S, E, W, t_arm, skin, r=(0.066, 0.056, 0.05, 0.04))
        tube(kit, f"arm {nm} hand", [(0, 0, 0.01), (0, 0, -0.05), (0, 0, -0.1)],
             [(0.042, 0.03), (0.05, 0.034), (0.04, 0.026)], skin, wrist, sides=6, front=(sx, 0, 0), bulge=(0, 0.02))
        kit.empty(f"socket hand {nm}", wrist, (0, 0, -0.06))
    kit.empty("socket carry", body, carry)


# ---------------------------------------------------------------- batch
KID_NAMES = [("Kid Pigtails", 'pigtails'), ("Kid Cap", 'cap'), ("Kid Glasses", 'glasses'), ("Kid Curly", 'curly'),
             ("Kid Hoodie", 'hoodie')]
ASSETS = [(n, named(n, build_kid, kind=k)) for n, k in KID_NAMES] + [
    ("Crew Throw", named("Crew Throw", build_crew_throw)),
    ("Crew Carry Pink", named("Crew Carry Pink", build_crew_carry, team='pink')),
    ("Crew Carry Mint", named("Crew Carry Mint", build_crew_carry, team='mint')),
]
SPACING = 4


def build_kid_crowd(kit, root):
    spots = [(-0.65, 0.55, 8), (-0.3, -0.1, 6), (-1.15, -0.25, 35), (0.5, 0.05, -8), (0.98, 0.65, -14)]
    for (n, k), (x, y, rz) in zip(KID_NAMES, spots):
        p = kit.empty(f"crowd {k}", root, (x, y, 0), (0, 0, rz))
        named(n, build_kid, kind=k)(kit, p)


SCENES = [
    dict(name="kid crowd", build=build_kid_crowd, cam=((0.0, -2.9, 2.1), (-0.05, 0.25, 0.55), 30), res=(1600, 900)),
]

