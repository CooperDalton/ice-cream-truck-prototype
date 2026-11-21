"""Batch 'cops' (style H): heist pitch NPCs. Police Officer (standing, climbing into the truck, running), the
plainclothes Detective, Forger Kevin holding up a fake plate, and the Diamond Buyer.
Standing assets: root on the floor at the footprint center, front -Y. Rig: hips > spine > head / arm R / arm L
(shoulder > forearm > hand pivots), hips > leg R / leg L (hip > shin > foot pivots). Sockets are empties named
'<Asset> socket <purpose>'."""
from style_H import *
from h_shop import prefixed, socket, txt3, txt3_c
from h_characters import named, build_team_player

UA, FA = 0.28, 0.26          # upper arm, forearm
TH, SH = 0.42, 0.43          # thigh, shin
SHOULDER = (0.2, 0.0, 0.49)  # spine-local
NECK = (0.0, -0.005, 0.55)

COP = "#3550c8"; COP_D = "#24379a"; COP_L = "#5a74e0"; COP_P = "#1e2462"; GOLD = "#ffd23a"; GOLD_D = "#c98a10"
BELT = "#221a2c"; BELT_L = "#3a3048"; MOUTH = "#2a0f2e"; LIPD = "#8a2a3a"; LINE = "#6a2a24"
TAN = "#dca85a"; TAN_D = "#a87a3a"; TAN_L = "#f0c47a"; HAT = "#7a4a2a"; HAT_D = "#3a2216"; DSKIN = "#f6c6a2"
KSKIN = "#ffb58e"; KHAIR = "#4a3326"; KHAKI = "#d2bb80"; KHAKI_D = "#a8915a"; PALM = "#2fd06a"; TRUNK = "#8a5a2a"
SUIT = "#f6f2fa"; SUIT_D = "#c9bfdc"; SHIRT_B = "#1c1628"; BSKIN = "#e0a070"; BHAIR = "#15101e"


# ---------------------------------------------------------------- rig helpers
class J:
    """A pivot plus its root-space position and rotation, so children can be placed in root space."""

    def __init__(self, ob, pos, M):
        self.ob, self.pos, self.M = ob, Vector(pos), M

    def at(self, p):
        return self.pos + self.M @ Vector(p)


def R(*deg):
    return Euler([math.radians(a) for a in deg]).to_matrix()


def joint(kit, name, parent, pos, M):
    Pi = parent.M.transposed()
    ob = kit.empty(name, parent.ob, Pi @ (Vector(pos) - parent.pos))
    ob.rotation_euler = (Pi @ M).to_euler()
    return J(ob, pos, M)


def frame(d, up):
    """Rotation whose local -Z runs along d and whose local +Y leans toward up."""
    z = -Vector(d).normalized()
    up = Vector(up).normalized()
    if abs(up.dot(z)) > 0.9:
        up = Vector((0, 0, 1)) if abs(z.z) < 0.9 else Vector((0, -1, 0))
    y = (up - z * up.dot(z)).normalized()
    return Matrix((y.cross(z), y, z)).transposed()


def foot_frame(toe):
    y = -Vector(toe).normalized()
    z = Vector((0, 0, 1))
    z = (z - y * z.dot(y)).normalized()
    return Matrix((y.cross(z), y, z)).transposed()


def ik(a, c, l1, l2, pole):
    """Two-bone IK: returns (elbow, end) for a chain from a toward c bending toward pole."""
    a, c, pole = Vector(a), Vector(c), Vector(pole)
    n = (c - a).normalized()
    L = min((c - a).length, (l1 + l2) * 0.998)
    x = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    p = (pole - n * pole.dot(n)).normalized()
    return a + n * x + p * h, a + n * L


def arm(kit, spine, nm, sx, P, t_arm, skin, k=1.0, cuff=None):
    """Shoulder > forearm > hand pivots posed by a root-space wrist target. P: wrist, pole, hand (direction),
    palm (direction the flat of the hand faces), grip ('flat', 'fist', 'open', 'point', 'pocket'), thumb (hint)."""
    S = spine.at((sx * SHOULDER[0], SHOULDER[1], SHOULDER[2]))
    E, W = ik(S, P['wrist'], UA, FA, P['pole'])
    out = Vector((sx, 0, 0.15))
    up = joint(kit, f"arm {nm}", spine, S, frame(E - S, out))
    tube(kit, f"upper arm {nm}", [(0, 0, 0.03), (0, 0, -0.14), (0, 0, -(UA + 0.025))], [0.066 * k, 0.06 * k, 0.052 * k],
         t_arm, up.ob, sides=6, front=(0, 1, 0), v=(0.0, 0.5), bulge=(0.02, 0.01))
    if cuff:
        tube(kit, f"sleeve hem {nm}", [(0, 0, -0.1), (0, 0, -0.15)], [0.07 * k, 0.074 * k], cuff, up.ob, sides=6,
             front=(0, 1, 0), caps=(False, False))
    fo = joint(kit, f"forearm {nm}", up, E, frame(W - E, out))
    tube(kit, f"forearm {nm}", [(0, 0, 0.02), (0, 0, -0.13), (0, 0, -FA)], [0.052 * k, 0.047 * k, 0.038 * k], t_arm, fo.ob,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    hdir = Vector(P.get('hand', W - E))
    hd = joint(kit, f"hand {nm}", fo, W, frame(hdir, P.get('palm', (-sx, 0, 0))))
    grip = P.get('grip', 'flat')
    ts = 1 if hd.M.col[0].dot(Vector(P.get('thumb', (0, -1, 0)))) >= 0 else -1
    if grip == 'pocket':
        tube(kit, f"hand {nm}", [(0, 0, 0.01), (0, 0, -0.05)], [(0.042, 0.026), (0.046, 0.026)], skin, hd.ob, sides=6,
             front=(0, 1, 0))
        return up, fo, hd
    L = 0.1 if grip in ('fist', 'point') else 0.13
    tube(kit, f"hand {nm}", [(0, 0, 0.01), (0, 0, -0.06), (0, 0, -L)],
         [(0.046, 0.028), (0.052, 0.03 if grip != 'fist' else 0.036), (0.042, 0.024 if grip != 'fist' else 0.03)],
         skin, hd.ob, sides=6, front=(0, 1, 0), bulge=(0, 0.015))
    tube(kit, f"thumb {nm}", [(ts * 0.035, 0.01, -0.03), (ts * 0.06, 0.016, -0.07), (ts * 0.064, 0.016, -0.1)],
         [0.015, 0.013, 0.01], skin, hd.ob, sides=4)
    if grip == 'open':
        for i, x in enumerate((-0.03, -0.01, 0.01, 0.03)):
            tube(kit, f"finger {nm} {i}", [(x * 0.9, 0, -0.12), (x * 1.5, 0, -0.18 + abs(x) * 0.6)], [0.012, 0.009], skin,
                 hd.ob, sides=4)
    elif grip == 'point':
        tube(kit, f"finger {nm}", [(ts * 0.022, 0.0, -0.09), (ts * 0.022, 0.0, -0.18)], [0.013, 0.01], skin, hd.ob, sides=4)
    return up, fo, hd


def leg(kit, hips, nm, sx, P, t_leg, foot_fn, k=1.0):
    H = hips.at((sx * 0.088, 0, 0))
    K, A = ik(H, P['ankle'], TH, SH, P.get('pole', (0, -1, 0.1)))
    fwd = (0, -1, 0)
    th = joint(kit, f"leg {nm}", hips, H, frame(K - H, fwd))
    tube(kit, f"thigh {nm}", [(0, 0, 0.04), (0, 0, -0.2), (0, 0, -(TH + 0.02))], [(0.086 * k, 0.09 * k), 0.072 * k, 0.06 * k],
         t_leg, th.ob, sides=6, front=(0, 1, 0), v=(0.0, 0.5))
    sh = joint(kit, f"shin {nm}", th, K, frame(A - K, fwd))
    tube(kit, f"shin {nm}", [(0, 0, 0.02), (0, -0.01, -0.2), (0, 0, -SH)], [0.06 * k, 0.053 * k, 0.045 * k], t_leg, sh.ob,
         sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    ft = joint(kit, f"foot {nm}", sh, A, foot_frame(P.get('toe', (0, -1, 0))))
    foot_fn(kit, ft.ob, nm)
    return th, sh, ft


TORSO_PTS = [(0, 0, -0.06), (0, 0, 0.04), (0, 0, 0.18), (0, -0.005, 0.34), (0, 0.005, 0.48), (0, 0.01, 0.57)]
TORSO_RAD = [(0.155, 0.105), (0.16, 0.11), (0.145, 0.104), (0.168, 0.115), (0.198, 0.118), (0.088, 0.07)]
HEAD_PTS = [(0, 0, 0), (0, 0, 0.05), (0, -0.005, 0.08), (0, -0.01, 0.13), (0, -0.005, 0.19), (0, 0, 0.25), (0, 0.005, 0.29),
            (0, 0.005, 0.31)]
HEAD_RAD = [0.048, 0.054, (0.08, 0.086), (0.101, 0.107), (0.106, 0.112), (0.098, 0.104), (0.07, 0.075), (0.03, 0.035)]


def on_front(pts, rad, x, z, side=-1, pad=0.01):
    """y of a tube surface (vertical loft) at lateral x and height z plus pad. side -1 = front."""
    i = max(0, min(len(pts) - 2, next((j for j in range(len(pts) - 1) if z <= pts[j + 1][2]), len(pts) - 2)))
    t = max(0.0, min(1.0, (z - pts[i][2]) / (pts[i + 1][2] - pts[i][2])))
    cy = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
    rx = rad[i][0] + (rad[i + 1][0] - rad[i][0]) * t
    ry = rad[i][1] + (rad[i + 1][1] - rad[i][1]) * t
    return cy + side * (ry + pad) * math.sqrt(max(0.0, 1 - (x / (rx + pad)) ** 2))


def body(kit, root, B):
    """Shared adult body. B: textures (torso, head, arm, leg, skin), foot builder, torso shape and the pose."""
    rootj = J(root, (0, 0, 0), Matrix.Identity(3))
    P = B['pose']
    hips = joint(kit, "hips", rootj, P.get('hips', (0, 0, 0.9)), Matrix.Identity(3))
    spine = joint(kit, "spine", hips, hips.pos, R(*P.get('spine', (0, 0, 0))))
    pts, rad = B.get('pts', TORSO_PTS), B.get('rad', TORSO_RAD)
    tube(kit, "torso", pts, rad, B['torso'], spine.ob, sides=10)
    tube(kit, "neck", [(0, -0.005, 0.47), (0, -0.005, 0.6)], [0.05, 0.047], B['skin'], spine.ob, sides=6)
    head = joint(kit, "head", spine, spine.at(NECK), spine.M @ R(*P.get('head', (0, 0, 0))))
    tube(kit, "head", HEAD_PTS, HEAD_RAD, B['head'], head.ob, bulge=(0, 0.01))
    lowball(kit, "nose", (0, -0.118, 0.142), (0.017, 0.02, 0.026), B['skin'], head.ob, smooth=False)
    for sx, nm in ((1, "L"), (-1, "R")):
        lowball(kit, f"ear {nm}", (sx * 0.104, 0.008, 0.16), (0.014, 0.024, 0.034), B['skin'], head.ob, smooth=False)
    J_ = dict(root=rootj, hips=hips, spine=spine, head=head)
    for sx, nm in ((-1, "R"), (1, "L")):
        J_['arm' + nm] = arm(kit, spine, nm, sx, P['arm' + nm], B['arm'], B['skin'], B.get('arm_k', 1.0), B.get('cuff'))
        J_['leg' + nm] = leg(kit, hips, nm, sx, P['leg' + nm], B['leg'], B['foot'], B.get('leg_k', 1.0))
    return J_


def shield_badge(kit, name, mat, parent, loc, rot=(0, 0, 0), s=1.0, depth=0.008):
    """Little extruded police shield, front facing -Y."""
    outline = [(-0.026, 0.03), (-0.012, 0.036), (0, 0.04), (0.012, 0.036), (0.026, 0.03), (0.024, -0.008), (0.012, -0.026),
               (0, -0.036), (-0.012, -0.026), (-0.024, -0.008)]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    fr = [bm.verts.new((x * s, -depth / 2, z * s)) for x, z in outline]
    bk = [bm.verts.new((x * s, depth / 2, z * s)) for x, z in outline]
    faces = [bm.faces.new(fr[::-1]), bm.faces.new(bk)]
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        faces.append(bm.faces.new((fr[i], fr[j], bk[j], bk[i])))
    for f in faces:
        for lp in f.loops:
            lp[uvl].uv = (0.5 + lp.vert.co.x / (0.06 * s), 0.5 + lp.vert.co.z / (0.08 * s))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth=False)


def tex_badge():
    c = Canvas(16, 16, GOLD)
    for y in range(16):
        c.set(0, y, GOLD_D); c.set(15, y, GOLD_D)
    c.rect(0, 0, 15, 1, GOLD_D); c.rect(0, 14, 15, 15, GOLD_D)
    disc(c, 8, 8, 3, "#fff2a0")
    c.rect(7, 7, 8, 9, BLUE)
    c.dots([(3, 12), (4, 12), (12, 4)], WHITE)
    return c


def dress_shoe(col, hi):
    def build(kit, ft, nm):
        m = solid(kit, f"shoe {col}", col, 0.3, shade=hi)
        tube(kit, f"shoe {nm}", [(0, 0.05, 0.0), (0, -0.04, 0.004), (0, -0.14, -0.012)],
             [(0.05, 0.044), (0.056, 0.046), (0.045, 0.028)], m, ft, sides=6, front=(0, 0, 1), bulge=(0.015, 0.03))
        tbox(kit, f"sole {nm}", (0, -0.045, -0.042), (0.1, 0.22, 0.016), solid(kit, "sole", "#120c1a", 0.1), ft)
    return build


def sunglasses(kit, name, head, z, y=-0.112, frame_col=INK, lens=INK, tilt=0.0, lift=0.0):
    """Two chunky lenses and a bridge hugging the face at height z, plus arms back to the ears."""
    g = kit.empty(f"{name}", head, (0, y, z), (tilt, 0, 0))
    lm = tex_mat(f"{name} lens", tex_lens(lens), 0.45)
    fm = solid(kit, f"{name} frame", frame_col, 0.4)
    for sx in (1, -1):
        tbox(kit, f"{name} lens {sx}", (sx * 0.042, -0.006 + abs(sx) * 0.0, lift), (0.062, 0.012, 0.042), lm, g,
             rot=(0, 0, -sx * 14), uv={'ny': (0, 0, 1, 1), 'all': (0, 0, 0.1, 0.1)})
        tube(kit, f"{name} arm {sx}", [(sx * 0.072, 0.0, lift + 0.012), (sx * 0.1, 0.06, lift + 0.01), (sx * 0.104, 0.11, lift)],
             0.006, fm, g, sides=4)
    tbox(kit, f"{name} bridge", (0, -0.012, lift + 0.01), (0.03, 0.01, 0.01), fm, g)
    return g


def tex_lens(col):
    c = Canvas(16, 8, col)
    c.rect(0, 7, 15, 7, hex_scale(col, 1.6) if col != INK else "#3a2f5a")
    for i in range(3):
        c.set(3 + i, 5 - i, WHITE); c.set(4 + i, 5 - i, "#c8c0ff")
    c.set(11, 2, "#c8c0ff")
    return c


def face_base(c, skin, hair, crown=46, back=True):
    shade = hex_scale(skin, 0.86)
    c.rect(0, crown, 63, 63, hair)
    if back:
        for x in range(64):
            if x < 17 or x > 47:
                c.rect(x, 18 + (x * 7) % 3, x, crown, hair)
    c.rect(17, 30, 19, crown, hair); c.rect(45, 30, 47, crown, hair)   # sideburns
    c.rect(20, 14, 44, 15, shade)                                     # jaw line shadow
    c.dots([(30, 28), (34, 28)], shade)
    return c


def brows(c, col, left, right):
    """left/right: lists of (x, y) pixels drawn 2 rows thick."""
    for x, y in left + right:
        c.rect(x, y, x, y + 1, col)


# ---------------------------------------------------------------- Police Officer
def tex_cop_head(rand, shout=False):
    c = face_base(Canvas(64, 64, SKIN), SKIN, "#3a2418", crown=44)
    # eyes: narrowed and hard
    for x0 in (24, 36):
        c.rect(x0, 34, x0 + 3, 36, WHITE)
        c.rect(x0 + 1, 34, x0 + 2, 36, INK)
        c.rect(x0 - 1, 37, x0 + 4, 37, "#5a2a1a")
    # brows angled down to the nose
    brows(c, "#3a2418", [(22, 40), (23, 40), (24, 40), (25, 39), (26, 39), (27, 38), (28, 38)],
          [(35, 38), (36, 38), (37, 39), (38, 39), (39, 40), (40, 40), (41, 40)])
    c.rect(31, 36, 32, 38, hex_scale(SKIN, 0.85))  # frown crease
    if shout:
        c.rect(26, 17, 37, 26, MOUTH)
        c.rect(27, 25, 36, 25, WHITE)
        c.rect(28, 17, 35, 19, "#ff5d7a")
        c.rect(25, 18, 25, 25, LIPD); c.rect(38, 18, 38, 25, LIPD); c.rect(26, 27, 37, 27, LIPD)
        c.rect(26, 16, 37, 16, LIPD)
    else:
        c.rect(26, 23, 37, 23, LINE)
        c.dots([(25, 22), (38, 22), (24, 21)], LINE)
        c.rect(28, 21, 35, 21, hex_scale(SKIN, 0.88))
    c.speckle(rand, ["#eab094"], 40, 12, 22)
    return c


def tex_cop_torso(rand):
    c = Canvas(64, 64, COP)
    c.rect(0, 0, 63, 7, COP_P)
    for y in range(10, 60):   # placket and buttons
        c.set(31, y, COP_D)
    for y in (18, 28, 38, 48):
        c.rect(32, y, 33, y + 1, "#e8ecff")
    for x0 in (20, 37):       # chest pockets with flaps
        c.rect(x0, 38, x0 + 7, 46, COP_D); c.rect(x0 + 1, 39, x0 + 6, 45, COP)
        c.rect(x0, 45, x0 + 7, 48, COP_D); c.rect(x0 + 3, 45, x0 + 4, 46, GOLD)
    c.rect(21, 50, 27, 51, "#e8ecff"); c.rect(22, 50, 26, 50, INK)   # name bar on the right chest
    c.rect(0, 62, 63, 63, COP_D)
    for y in range(52, 64):                                           # V collar, dark tie
        hw = (y - 52) * 0.5
        c.rect(int(32 - hw), y, int(31 + hw), y, SKIN)
        c.set(int(32 - hw) - 1, y, COP_D); c.set(int(31 + hw) + 1, y, COP_D)
    c.rect(31, 20, 32, 58, INK); c.rect(30, 56, 33, 58, INK); c.rect(31, 19, 32, 19, "#3a3048")
    c.rect(31, 40, 32, 40, GOLD)
    c.speckle(rand, [COP_L], 30, 10, 56)
    return c


def tex_cop_arm():
    c = Canvas(16, 32, SKIN)
    c.rect(0, 0, 15, 12, COP)
    c.rect(0, 12, 15, 12, COP_D)
    # shoulder patch facing out: gold rim, blue field, white star
    c.rect(4, 2, 11, 9, GOLD); c.rect(5, 3, 10, 8, COP_D)
    c.dots([(7, 6), (8, 6), (7, 5), (8, 5), (6, 5), (9, 5), (7, 7), (8, 7), (6, 4), (9, 4)], WHITE)
    c.rect(0, 26, 15, 26, "#f0a888")
    c.dots([(3, 18), (11, 22)], "#f0a888")
    return c


def tex_cop_leg():
    c = Canvas(16, 32, COP_P)
    for x in (4, 12):
        c.rect(x, 0, x, 31, "#5a74e0")
    c.rect(0, 0, 15, 1, "#151a48")
    return c


def tex_cop_cap():
    c = Canvas(64, 16, COP_D)
    c.rect(0, 0, 63, 5, BELT)
    c.rect(0, 6, 63, 6, GOLD)
    c.rect(0, 15, 63, 15, COP)
    return c


def tex_radio():
    c = Canvas(8, 16, BELT)
    c.rect(1, 9, 6, 13, "#55507a")
    c.dots([(2, 10), (4, 10), (2, 12), (4, 12)], INK)
    c.rect(1, 3, 6, 6, "#3a3a4a"); c.set(5, 5, RED)
    return c


COP_POSES = {
    'stand': dict(
        hips=(0, 0, 0.9), spine=(0, 0, 0), head=(-2, 0, 0),
        armR=dict(wrist=(-0.215, -0.07, 1.0), pole=(-1, 0.45, 0), hand=(0.35, -0.5, -0.8), palm=(1, 0.2, 0), grip='flat'),
        armL=dict(wrist=(0.215, -0.07, 1.0), pole=(1, 0.45, 0), hand=(-0.35, -0.5, -0.8), palm=(-1, 0.2, 0), grip='flat'),
        legR=dict(ankle=(-0.12, 0.0, 0.05), toe=(-0.2, -1, 0)), legL=dict(ankle=(0.12, 0.0, 0.05), toe=(0.2, -1, 0))),
    'climb': dict(
        hips=(0, -0.04, 0.88), spine=(27, 0, 0), head=(-34, 0, 0),
        armR=dict(wrist=(-0.6, -0.16, 1.32), pole=(-0.2, 0.6, -1), hand=(-0.05, 0, 1), palm=(-1, 0, 0), grip='fist',
                  thumb=(0, -1, 0)),
        armL=dict(wrist=(0.27, -0.78, 1.4), pole=(1, 0, -1), hand=(0, -0.8, 0.25), palm=(0, -0.2, -1), grip='open',
                  thumb=(-1, 0, 0)),
        legR=dict(ankle=(-0.1, -0.34, 0.445), pole=(0, -1, 0.2), toe=(0, -1, 0)),
        legL=dict(ankle=(0.1, 0.1, 0.075), pole=(0, -1, 0), toe=(0, -1, -0.45))),
    'run': dict(
        hips=(0, -0.02, 0.86), spine=(13, 0, 4), head=(-12, 0, 0),
        armR=dict(wrist=(-0.3, -0.6, 1.5), pole=(-1, 0, -1), hand=(-0.12, -1, 0.1), palm=(1, 0, 0), grip='point',
                  thumb=(0, 0, 1)),
        armL=dict(wrist=(0.22, 0.2, 1.0), pole=(0.3, 1, 0.2), hand=(0, -0.3, -1), palm=(-1, 0, 0), grip='fist'),
        legL=dict(ankle=(0.1, -0.4, 0.28), pole=(0, -1, 0.3), toe=(0, -1, 0.15)),
        legR=dict(ankle=(-0.1, 0.4, 0.13), pole=(0, -1, -0.2), toe=(0, -0.45, -1))),
}


def build_officer(kit, root, A, pose='stand'):
    Rn = kit.rand
    skin = solid(kit, "cop skin", SKIN)
    B = dict(torso=tex_mat("cop torso", tex_cop_torso(Rn)), head=tex_mat("cop head", tex_cop_head(Rn, pose == 'run')),
             arm=tex_mat("cop arm", tex_cop_arm()), leg=tex_mat("cop leg", tex_cop_leg()), skin=skin,
             cuff=solid(kit, "cop sleeve hem", COP_D), foot=dress_shoe(BELT, "#3a3048"), pose=COP_POSES[pose],
             rad=[(0.155, 0.108), (0.162, 0.112), (0.15, 0.106), (0.172, 0.118), (0.205, 0.12), (0.09, 0.072)])
    Jt = body(kit, root, B)
    spine, head = Jt['spine'], Jt['head']
    pts, rad = TORSO_PTS, B['rad']
    gold = tex_mat("badge", tex_badge(), 0.7)
    blk = solid(kit, "duty belt", BELT, 0.25, shade=BELT_L)
    steel = solid(kit, "cuff steel", STEEL, 0.45, shade="#a9a2e0")

    # gold badge on the left chest, mic on the right shoulder strap, epaulettes
    yb = on_front(pts, rad, 0.08, 0.43, pad=0.006)
    shield_badge(kit, "chest badge", gold, spine.ob, (0.08, yb, 0.43), (-6, 0, 10), s=1.15)
    tbox(kit, "shoulder mic", (-0.11, on_front(pts, rad, -0.11, 0.47, pad=0.015), 0.47), (0.045, 0.025, 0.06), blk, spine.ob,
         rot=(-20, 0, 0))
    for sx in (1, -1):
        tbox(kit, f"epaulette {sx}", (sx * 0.135, 0.0, 0.565), (0.13, 0.05, 0.016), solid(kit, "epaulette", COP_D), spine.ob,
             rot=(0, sx * 18, 0))
        tbox(kit, f"epaulette button {sx}", (sx * 0.085, -0.01, 0.585), (0.016, 0.016, 0.01), gold, spine.ob, rot=(0, sx * 18, 0))

    # duty belt: holster on the right hip, radio front left, cuffs at the back
    tube(kit, "duty belt", [(0, 0.0, 0.0), (0, 0.0, 0.07)], [(0.172, 0.122), (0.168, 0.12)], blk, spine.ob, sides=10,
         caps=(False, False))
    yf = on_front(pts, rad, 0, 0.035, pad=0.018)
    tbox(kit, "buckle", (0, yf, 0.035), (0.06, 0.012, 0.05), steel, spine.ob)
    tbox(kit, "buckle bar", (0, yf - 0.007, 0.035), (0.036, 0.006, 0.022), blk, spine.ob)
    hol = kit.empty("holster", spine.ob, (-0.185, 0.01, 0.0), (0, 8, 0))
    tbox(kit, "holster", (0, 0, -0.08), (0.055, 0.11, 0.17), blk, hol, taper=(1.0, 1.0))
    tbox(kit, "holster flap", (-0.006, 0, 0.0), (0.05, 0.1, 0.03), solid(kit, "holster flap", BELT_L), hol)
    tbox(kit, "pistol grip", (0, 0.025, 0.05), (0.035, 0.05, 0.085), solid(kit, "pistol grip", "#45405a", 0.2), hol,
         rot=(-14, 0, 0))
    rad_p = kit.empty("radio", spine.ob, (0.15, -0.08, 0.02), (0, 0, 28))
    tbox(kit, "radio", (0, 0, -0.02), (0.05, 0.036, 0.1), tex_mat("radio", tex_radio()), rad_p,
         uv={'ny': (0, 0, 1, 1), 'all': (0, 0, 0.1, 0.1)})
    tube(kit, "radio antenna", [(-0.012, 0, 0.03), (-0.012, 0, 0.1)], [0.007, 0.005], blk, rad_p, sides=4)
    for i, x in enumerate((0.03, 0.09)):
        tube(kit, f"handcuff {i}", [(x + 0.03 * math.cos(a), 0.14, 0.02 + 0.03 * math.sin(a)) for a in
                                    (math.radians(d) for d in range(0, 361, 60))], 0.007, steel, spine.ob, sides=4,
             caps=(False, False))
    tbox(kit, "baton", (-0.12, 0.1, -0.12), (0.03, 0.03, 0.32), blk, spine.ob, rot=(-10, -10, 0))

    # police cap: black band, gold cord, navy crown flaring to a flat top, glossy visor and the cap badge
    cap = kit.empty("cap", head.ob, (0, -0.005, 0.205), (-5, 0, 0))
    tube(kit, "cap crown", [(0, 0, 0.0), (0, 0, 0.045), (0, -0.01, 0.085), (0, -0.012, 0.1)],
         [(0.112, 0.12), (0.116, 0.124), (0.138, 0.15), (0.134, 0.146)], tex_mat("cop cap", tex_cop_cap()), cap,
         sides=10, caps=(False, True))
    vp = kit.empty("cap visor", cap, (0, -0.118, 0.004), (14, 0, 0))
    lowball(kit, "cap visor", (0, 0, 0), (0.098, 0.07, 0.012), solid(kit, "visor", INK, 0.35, shade="#3a2f5a"), vp, smooth=False)
    shield_badge(kit, "cap badge", gold, cap, (0, -0.152, 0.07), (-14, 0, 0), s=0.85)

    socket(kit, A, "hand R", Jt['armR'][2].ob, (0, 0, -0.08))
    socket(kit, A, "hand L", Jt['armL'][2].ob, (0, 0, -0.08))
    socket(kit, A, "head", head.ob, (0, -0.1, 0.17))


# ---------------------------------------------------------------- Detective
def tex_det_head(rand):
    c = face_base(Canvas(64, 64, DSKIN), DSKIN, "#5a3a22", crown=44)
    # eyes peeking over the low sunglasses: narrowed, side-eye
    for x0 in (24, 36):
        c.rect(x0, 35, x0 + 3, 37, WHITE)
        c.rect(x0 + 2, 35, x0 + 3, 37, INK)
        c.rect(x0 - 1, 38, x0 + 4, 38, "#4a2a1a")
        c.rect(x0, 34, x0 + 3, 34, hex_scale(DSKIN, 0.8))
    # one brow low and hard, one cocked up
    brows(c, "#4a2a1a", [(22, 40), (23, 40), (24, 40), (25, 40), (26, 39), (27, 39), (28, 39)],
          [(35, 42), (36, 43), (37, 43), (38, 43), (39, 43), (40, 42), (41, 41)])
    # pursed, pulled-aside mouth and stubble
    c.speckle(rand, ["#d9a888", "#c99a7e"], 90, 13, 26)
    c.rect(29, 23, 36, 24, LIPD)
    c.dots([(37, 25), (28, 22), (27, 22)], LIPD)
    return c


def tex_trench_torso(rand):
    c = Canvas(64, 64, TAN)
    c.rect(0, 0, 63, 5, TAN_D)
    # lapels: V opening with shirt and tie
    for y in range(36, 64):
        hw = 1 + (y - 36) * 0.26
        for x in range(64):
            d = abs(x + 0.5 - 32)
            if d <= hw:
                c.set(x, y, WHITE)
            elif d <= hw + 3:
                c.set(x, y, TAN_D if d > hw + 2 else TAN_L)
    for y in range(36, 60):
        c.rect(31, y, 32, y, "#a0203a")
    c.rect(30, 57, 33, 59, "#c02848"); c.rect(31, 40, 32, 40, "#7a1028")
    c.dots([(31, 52), (32, 48), (31, 44)], "#7a1028")
    # double-breasted buttons, belt with buckle
    for y in (22, 29):
        for x in (25, 38):
            c.rect(x, y, x + 1, y + 1, "#4a2c18")
    c.rect(0, 12, 63, 17, TAN_D); c.rect(28, 11, 35, 18, "#e8c060"); c.rect(30, 13, 33, 16, TAN_D)
    c.rect(0, 62, 63, 63, TAN_D)
    c.speckle(rand, [hex_scale(TAN, 0.92)], 50, 0, 60)
    return c


def tex_trench_skirt(rand):
    """32x32, row 0 at the waist (top), row 31 at the hem; front slit at x 16."""
    c = Canvas(32, 32, TAN)
    c.rect(15, 0, 16, 31, TAN_D); c.rect(17, 0, 17, 31, TAN_L)
    for x0 in (8, 21):
        c.rect(x0, 8, x0 + 3, 10, TAN_D)
    c.rect(0, 29, 31, 31, TAN_D)
    c.rect(19, 0, 20, 9, TAN_D); c.rect(19, 10, 20, 11, "#e8c060")   # belt tail
    c.speckle(rand, [hex_scale(TAN, 0.92)], 30)
    return c


def tex_trench_arm():
    c = Canvas(16, 32, TAN)
    c.rect(0, 22, 15, 24, TAN_D)
    c.rect(0, 28, 15, 31, WHITE)
    c.rect(0, 27, 15, 27, TAN_D)
    c.rect(6, 0, 9, 3, TAN_D)
    return c


def tex_slacks():
    c = Canvas(16, 32, "#4a3f5a")
    c.rect(7, 0, 8, 31, "#5a4f6e")
    return c


def tex_fedora():
    c = Canvas(32, 16, HAT)
    c.rect(0, 0, 31, 4, HAT_D)
    c.rect(0, 5, 31, 5, "#a0683a")
    c.rect(0, 13, 31, 15, hex_scale(HAT, 0.85))
    return c


def tex_notepad():
    c = Canvas(16, 16, "#8a5a2a")
    c.rect(1, 1, 14, 13, "#a8743a")
    c.rect(3, 9, 12, 10, WHITE)
    c.rect(0, 14, 15, 15, STEEL)
    for x in range(0, 16, 2):
        c.set(x, 15, "#8a86b0")
    return c


def tex_pages():
    c = Canvas(16, 16, WHITE)
    for y in (3, 6, 9, 12):
        c.rect(1, y, 14, y, "#9ab8ff")
    c.rect(2, 9, 9, 9, INK); c.rect(2, 6, 12, 6, INK); c.rect(2, 3, 6, 3, INK)
    c.rect(0, 14, 15, 15, STEEL)
    return c


def build_detective(kit, root, A):
    Rn = kit.rand
    skin = solid(kit, "det skin", DSKIN)
    # notepad (left hand) and pencil tip (right hand), in root space
    pad_c = Vector((0.04, -0.33, 1.2))
    pad_M = R(38, 0, -12)         # page side (local +Y) tilted up toward his face, cover faces the viewer
    n = pad_M @ Vector((0, 1, 0))
    tip = pad_c + n * 0.009 + pad_M @ Vector((-0.012, 0, 0.02))
    pose = dict(hips=(0, 0, 0.9), spine=(4, 0, 0), head=(10, 6, 3),
                armL=dict(wrist=pad_c + pad_M @ Vector((0.015, -0.03, -0.12)), pole=(1, 0.6, -1),
                          hand=pad_M @ Vector((0, 0, 1)), palm=pad_M @ Vector((0, 1, 0)), grip='fist', thumb=(-1, 0, 0)),
                armR=dict(wrist=tip + Vector((-0.11, 0.04, 0.08)), pole=(-1, 0.3, -1), hand=(0.75, -0.35, -0.5),
                          palm=(0.3, 0, -1), grip='fist', thumb=(0, -1, 0)),
                legR=dict(ankle=(-0.11, 0.0, 0.05), toe=(-0.15, -1, 0)), legL=dict(ankle=(0.11, 0.03, 0.05), toe=(0.25, -1, 0)))
    rad = [(0.162, 0.115), (0.168, 0.12), (0.158, 0.114), (0.175, 0.122), (0.208, 0.124), (0.09, 0.074)]
    B = dict(torso=tex_mat("trench torso", tex_trench_torso(Rn)), head=tex_mat("det head", tex_det_head(Rn)),
             arm=tex_mat("trench arm", tex_trench_arm()), leg=tex_mat("slacks", tex_slacks()), skin=skin, arm_k=1.12,
             foot=dress_shoe("#5a3418", "#7a4a28"), pose=pose, rad=rad)
    Jt = body(kit, root, B)
    spine, head, hips = Jt['spine'], Jt['head'], Jt['hips']
    tan = solid(kit, "trench", TAN, shade=TAN_D)

    # coat skirt from the waist to below the knees, popped collar, epaulettes
    tube(kit, "coat skirt", [(0, 0.0, 0.02), (0, 0.01, -0.2), (0, 0.02, -0.5)], [(0.172, 0.126), (0.205, 0.16), (0.245, 0.2)],
         tex_mat("trench skirt", tex_trench_skirt(Rn)), hips.ob, sides=10, caps=(False, False))
    cp = [(0.11 * math.sin(math.radians(a)), 0.09 * -math.cos(math.radians(a)) + 0.005, 0.56) for a in range(-120, 121, 30)]
    tube(kit, "collar", [(x * 0.95, y * 0.95, z - 0.01) for x, y, z in cp], [(0.04, 0.012)] * len(cp), tan, spine.ob, sides=4,
         side=(0, 0, 1), caps=(True, True))
    tube(kit, "collar top", [(x * 1.1, y * 1.1, z + 0.04) for x, y, z in cp], [(0.018, 0.01)] * len(cp), tan, spine.ob,
         sides=4, side=(0, 0, 1))
    for sx in (1, -1):
        tbox(kit, f"epaulette {sx}", (sx * 0.14, 0.0, 0.57), (0.13, 0.05, 0.016), solid(kit, "trench dark", TAN_D), spine.ob,
             rot=(0, sx * 18, 0))

    # fedora tipped forward, sunglasses slid down the nose
    hat = kit.empty("fedora", head.ob, (0, 0.0, 0.215), (-7, 0, 4))
    hm = tex_mat("fedora", tex_fedora())
    tube(kit, "fedora brim", [(0, 0, -0.006), (0, 0, 0.008)], [(0.19, 0.2), (0.18, 0.19)], solid(kit, "fedora brim", HAT, shade=HAT_D),
         hat, sides=10)
    tube(kit, "fedora crown", [(0, 0, 0.0), (0, 0, 0.05), (0, 0.004, 0.11), (0, 0.006, 0.13)],
         [(0.112, 0.122), (0.11, 0.12), (0.095, 0.11), (0.08, 0.094)], hm, hat, sides=8, caps=(False, True), bulge=(0, -0.025))
    sunglasses(kit, "sunglasses", head.ob, 0.152, y=-0.117, tilt=-6)

    # notepad and pencil
    pad = joint(kit, "notepad", Jt['armL'][2], pad_c, pad_M)
    tbox(kit, "notepad", (0, 0, 0), (0.1, 0.012, 0.14), tex_mat("notepad", tex_notepad()), pad.ob,
         uv={'ny': (0, 0, 1, 1), 'all': (0.1, 0.1, 0.2, 0.2)})
    tbox(kit, "notepad pages", (0, 0.0075, -0.004), (0.094, 0.004, 0.13), tex_mat("pages", tex_pages(), 0.5), pad.ob,
         uv={'py': (0, 0, 1, 1), 'all': (0, 0, 0.1, 0.1)})
    tube(kit, "notepad spiral", [(-0.05, 0, 0.071), (0.05, 0, 0.071)], 0.008, solid(kit, "spiral", STEEL), pad.ob, sides=4,
         side=(0, 0, 1))
    hand_c = Jt['armR'][2].at((0, 0, -0.06))
    d = (hand_c - tip).normalized()
    pen = joint(kit, "pencil", Jt['armR'][2], tip, frame(-d, (0, 0, 1)))
    tube(kit, "pencil", [(0, 0, -0.018), (0, 0, -0.15)], 0.0075, solid(kit, "pencil", YEL), pen.ob, sides=6)
    tube(kit, "pencil tip", [(0, 0, -0.018), (0, 0, 0.0)], [0.0075, 0.0015], solid(kit, "pencil wood", "#ffcf9a"), pen.ob,
         sides=6)
    tube(kit, "pencil eraser", [(0, 0, -0.15), (0, 0, -0.165)], 0.008, solid(kit, "eraser", PINK), pen.ob, sides=6)

    socket(kit, A, "hand R", Jt['armR'][2].ob, (0, 0, -0.08))
    socket(kit, A, "hand L", Jt['armL'][2].ob, (0, 0, -0.08))
    socket(kit, A, "head", head.ob, (0, -0.1, 0.17))


# ---------------------------------------------------------------- Forger Kevin
def palm_tree(c, x, y, trunk=TRUNK, leaf=PALM):
    for i in range(6):
        c.set(x + (1 if i > 3 else 0), y + i, trunk)
    top = (x + 1, y + 6)
    for dx, dy in ((-3, -1), (-2, 0), (-1, 1), (1, 1), (2, 0), (3, -1), (0, 1), (-2, -1), (2, -1), (4, -2), (-4, -2),
                   (-1, 0), (1, 0), (0, 2), (-3, 0), (3, 0), (-4, -3), (4, -3)):
        c.set(top[0] + dx, top[1] + dy, leaf)
    c.set(top[0], top[1] - 1, "#8a3a1a")


def hibiscus(c, x, y):
    for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        c.set(x + dx, y + dy, YEL)
    c.set(x, y, "#ff8a3d")


def hawaiian(c, rand, y0, y1, n_trees, n_flowers):
    for _ in range(n_trees):
        palm_tree(c, rand.randrange(c.w), rand.randint(y0, max(y0, y1 - 8)))
    for _ in range(n_flowers):
        hibiscus(c, rand.randrange(c.w), rand.randint(y0 + 1, y1 - 1))


def tex_kevin_head(rand):
    c = face_base(Canvas(64, 64, KSKIN), KSKIN, KHAIR, crown=45)
    # half-lidded sly eyes glancing at the buyer
    for x0 in (24, 36):
        c.rect(x0, 34, x0 + 3, 35, WHITE)
        c.rect(x0 + 2, 34, x0 + 3, 35, INK)
        c.rect(x0 - 1, 36, x0 + 4, 37, hex_scale(KSKIN, 0.82))
        c.rect(x0 - 1, 36, x0 + 4, 36, "#3a2014")
    brows(c, KHAIR, [(22, 39), (23, 39), (24, 39), (25, 39), (26, 39), (27, 39)],
          [(36, 41), (37, 42), (38, 42), (39, 42), (40, 41), (41, 40)])
    # lopsided grin under the mustache, teeth showing, right corner hiked up
    c.rect(26, 19, 38, 22, MOUTH)
    c.rect(27, 21, 38, 22, WHITE)
    c.rect(27, 19, 33, 19, "#ff6f8f")
    c.rect(39, 22, 40, 24, MOUTH); c.set(41, 25, MOUTH)
    c.rect(25, 18, 38, 18, LIPD); c.rect(25, 19, 25, 21, LIPD)
    c.rect(36, 25, 37, 25, hex_scale(KSKIN, 0.85))   # cheek dimple
    c.rect(21, 30, 24, 31, "#ff8f8f"); c.rect(39, 30, 42, 31, "#ff8f8f")   # sunburnt cheeks
    c.speckle(rand, [hex_scale(KSKIN, 0.9)], 30, 10, 18)
    return c


def tex_kevin_shirt(rand):
    c = Canvas(64, 64, PINK)
    hawaiian(c, rand, 2, 60, 26, 26)
    c.rect(0, 0, 63, 1, "#d63a86")
    # open collar V with a little chest hair, buttons down the front
    for y in range(50, 64):
        hw = (y - 50) * 0.36
        c.rect(int(32 - hw), y, int(31 + hw + 1), y, KSKIN)
        c.set(int(32 - hw) - 1, y, WHITE); c.set(int(31 + hw + 1) + 1, y, WHITE)
    c.dots([(31, 55), (33, 57), (30, 59), (32, 54)], KHAIR)
    for y in (8, 18, 28, 38):
        c.rect(32, y, 32, y + 1, WHITE)
    c.rect(37, 34, 44, 41, "#d63a86"); c.rect(38, 35, 43, 40, PINK)   # pocket with pens
    c.rect(39, 40, 39, 43, BLUE); c.rect(41, 40, 41, 44, RED)
    return c


def tex_kevin_arm(rand):
    c = Canvas(16, 32, KSKIN)
    c.rect(0, 0, 15, 11, PINK)
    hawaiian(c, rand, 0, 10, 2, 3)
    c.rect(0, 11, 15, 11, "#d63a86")
    c.dots([(3, 18), (11, 22), (6, 25), (9, 16)], hex_scale(KSKIN, 0.86))
    c.rect(0, 27, 15, 28, "#ffd23a")   # gold watch on both wrists, the forger's tell
    c.set(7, 27, WHITE)
    return c


def tex_cargo():
    c = Canvas(16, 32, KSKIN)
    c.rect(0, 0, 15, 12, KHAKI)
    c.rect(0, 12, 15, 13, KHAKI_D)
    c.rect(7, 0, 8, 12, hex_scale(KHAKI, 0.92))
    c.dots([(4, 20), (11, 24), (6, 27)], hex_scale(KSKIN, 0.86))
    return c


def tex_plate():
    """64x32 fake license plate: white plate, blue border and number, SEASIDE across the top."""
    c = Canvas(64, 32, WHITE)
    c.rect(0, 0, 63, 1, "#1f3fae"); c.rect(0, 30, 63, 31, "#1f3fae")
    c.rect(0, 0, 1, 31, "#1f3fae"); c.rect(62, 0, 63, 31, "#1f3fae")
    c.rect(3, 22, 60, 28, "#ffe8a0")
    txt3_c(c, "SEASIDE", 32, 27, RED)
    c.rect(4, 26, 6, 28, ORNG); c.rect(57, 26, 59, 28, ORNG)
    txt3(c, "7KE 8L2", 5, 19, "#1f3fae", k=2)
    c.rect(4, 4, 59, 5, "#d8e2ff")
    c.dots([(6, 3), (57, 3), (6, 24), (57, 24)], STEEL)
    return c


def sandal(kit, ft, nm):
    skin = solid(kit, "kevin skin", KSKIN)
    tube(kit, f"foot {nm}", [(0, 0.045, 0.0), (0, -0.04, -0.008), (0, -0.13, -0.02)], [(0.044, 0.036), (0.05, 0.03), (0.046, 0.02)],
         skin, ft, sides=6, front=(0, 0, 1), bulge=(0.01, 0.02))
    tbox(kit, f"sandal sole {nm}", (0, -0.045, -0.04), (0.11, 0.24, 0.022), solid(kit, "sandal sole", "#8a5a2a", shade="#6a4018"), ft)
    tube(kit, f"sandal strap {nm}", [(-0.05, -0.06, -0.035), (-0.03, -0.065, 0.004), (0.03, -0.065, 0.004), (0.05, -0.06, -0.035)],
         0.011, solid(kit, "sandal strap", MINT), ft, sides=4, side=(0, 1, 0))


def build_forger_kevin(kit, root, A):
    Rn = kit.rand
    skin = solid(kit, "kevin skin", KSKIN)
    plate_c = Vector((-0.44, -0.3, 1.43))
    pose = dict(hips=(0, 0, 0.9), spine=(5, 0, -3), head=(-4, -6, -7),
                armR=dict(wrist=(-0.27, -0.27, 1.34), pole=(-0.7, 0.3, -1), hand=(-0.15, 0, 1), palm=(-1, 0, 0), grip='fist',
                          thumb=(0, -1, 0)),
                armL=dict(wrist=(0.17, -0.37, 1.04), pole=(1, 0.4, -0.2), hand=(0.02, -1, -0.1), palm=(0, 0, -1), grip='open',
                          thumb=(-1, 0, 0)),
                legR=dict(ankle=(-0.12, 0.02, 0.05), toe=(-0.25, -1, 0)), legL=dict(ankle=(0.12, 0.02, 0.05), toe=(0.25, -1, 0)))
    pts = [(0, 0.0, -0.06), (0, -0.03, 0.04), (0, -0.045, 0.17), (0, -0.015, 0.33), (0, 0.005, 0.48), (0, 0.01, 0.57)]
    rad = [(0.165, 0.125), (0.178, 0.158), (0.172, 0.165), (0.172, 0.13), (0.2, 0.118), (0.088, 0.07)]
    B = dict(torso=tex_mat("kevin shirt", tex_kevin_shirt(Rn)), head=tex_mat("forger head", tex_kevin_head(Rn)),
             arm=tex_mat("kevin shirt arm", tex_kevin_arm(Rn)), leg=tex_mat("cargo shorts", tex_cargo()), skin=skin,
             cuff=solid(kit, "shirt hem", PINK, shade="#d63a86"), foot=sandal, pose=pose, pts=pts, rad=rad)
    Jt = body(kit, root, B)
    spine, head, hips = Jt['spine'], Jt['head'], Jt['hips']

    # shorts seat, cuffs and cargo pockets
    khaki = solid(kit, "khaki", KHAKI, shade=KHAKI_D)
    tube(kit, "shorts seat", [(0, -0.01, 0.02), (0, 0.0, -0.1)], [(0.17, 0.13), (0.18, 0.125)], khaki, hips.ob, sides=10,
         caps=(False, True))
    for nm, sx in (("R", -1), ("L", 1)):
        th = Jt['leg' + nm][0]
        tube(kit, f"shorts cuff {nm}", [(0, 0, -0.17), (0, 0, -0.23)], [(0.088, 0.09), (0.094, 0.096)], khaki, th.ob, sides=6,
             front=(0, 1, 0), caps=(False, False))
        tbox(kit, f"cargo pocket {nm}", (-sx * 0.085, 0.0, -0.13), (0.03, 0.09, 0.1), solid(kit, "cargo pocket", KHAKI_D), th.ob)

    # mint sun visor with the shades pushed up onto it, chunky mustache
    vis = kit.empty("sun visor", head.ob, (0, -0.002, 0.205), (-6, 0, 0))
    mint = solid(kit, "visor mint", MINT, 0.45, shade="#22c79c")
    tube(kit, "visor band", [(0, 0, 0.0), (0, 0, 0.04)], [(0.111, 0.118), (0.108, 0.115)], mint, vis, sides=10,
         caps=(False, False))
    vb = kit.empty("visor brim", vis, (0, -0.13, 0.008), (10, 0, 0))
    lowball(kit, "visor brim", (0, 0, 0), (0.11, 0.085, 0.012), mint, vb, smooth=False)
    sunglasses(kit, "shades", head.ob, 0.262, y=-0.1, tilt=-38, lens=INK, frame_col=YEL)
    tube(kit, "mustache", [(-0.05, -0.098, 0.112), (-0.028, -0.116, 0.124), (0, -0.124, 0.128), (0.028, -0.116, 0.124),
                           (0.05, -0.098, 0.112)], [0.009, 0.015, 0.016, 0.015, 0.009], solid(kit, "mustache", KHAIR, 0.2),
         head.ob, sides=6, side=(0, 0, 1))

    # the fake plate held up beside his head
    plate = joint(kit, "fake plate", Jt['armR'][2], plate_c, R(0, 4, 3))
    tbox(kit, "fake plate", (0, 0, 0), (0.3, 0.01, 0.15), tex_mat("fake plate", tex_plate(), 0.5), plate.ob,
         uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.03, 0.06)})

    socket(kit, A, "plate", plate.ob, (0, 0, 0))
    socket(kit, A, "hand L", Jt['armL'][2].ob, (0, 0, -0.08))
    socket(kit, A, "head", head.ob, (0, -0.1, 0.17))


# ---------------------------------------------------------------- Diamond Buyer
def tex_buyer_head(rand):
    c = Canvas(64, 64, BSKIN)
    c.rect(0, 44, 63, 63, BHAIR)
    for x in range(64):
        if x < 18 or x > 46:
            c.rect(x, 22 + (x * 5) % 3, x, 44, BHAIR)
    c.rect(18, 32, 19, 44, BHAIR); c.rect(45, 32, 46, 44, BHAIR)
    c.rect(30, 42, 33, 44, BHAIR); c.rect(31, 41, 32, 41, BHAIR)   # widow's peak
    for i in range(6):                                               # slick comb lines
        c.rect(6 + i * 10, 48 + i % 3, 10 + i * 10, 48 + i % 3, "#4a4a72")
        c.rect(3 + i * 10, 55 - i % 2, 8 + i * 10, 55 - i % 2, "#3a3a5a")
    c.rect(20, 14, 44, 15, hex_scale(BSKIN, 0.86))
    brows(c, BHAIR, [(23, 40), (24, 41), (25, 41), (26, 41), (27, 40)], [(36, 40), (37, 41), (38, 41), (39, 41), (40, 40)])
    # wide smug grin with a gold tooth
    c.rect(25, 21, 39, 24, MOUTH)
    c.rect(26, 23, 38, 24, WHITE)
    c.rect(34, 23, 35, 24, GOLD)
    c.dots([(24, 25), (40, 25), (23, 26), (41, 26)], MOUTH)
    c.rect(26, 20, 38, 20, LIPD)
    return c


def tex_buyer_torso(rand):
    c = Canvas(64, 64, SUIT)
    c.rect(0, 0, 63, 3, SUIT_D)
    for y in range(26, 64):
        hw = 1 + (y - 26) * 0.3
        for x in range(64):
            d = abs(x + 0.5 - 32)
            if d <= hw:
                c.set(x, y, SHIRT_B)
            elif d <= hw + 3:
                c.set(x, y, SUIT_D if d > hw + 2 else WHITE)
    c.rect(29, 56, 34, 63, BSKIN)                    # open shirt collar
    c.rect(27, 58, 28, 63, SHIRT_B); c.rect(35, 58, 36, 63, SHIRT_B)
    c.rect(31, 18, 32, 19, INK); c.rect(31, 10, 32, 11, INK)   # buttons
    c.rect(41, 8, 48, 9, SUIT_D); c.rect(16, 8, 23, 9, SUIT_D)  # hip pockets
    c.rect(39, 44, 44, 47, PINK); c.dots([(40, 48), (42, 48), (43, 49)], PINK)   # pocket square
    c.rect(38, 43, 45, 43, SUIT_D)
    c.speckle(rand, ["#ebe4f2"], 30, 4, 60)
    return c


def tex_suit_skirt():
    c = Canvas(32, 16, SUIT)
    c.rect(15, 0, 16, 15, SUIT_D)
    for x0 in (6, 22):
        c.rect(x0, 5, x0 + 4, 5, SUIT_D)
    c.rect(0, 15, 31, 15, SUIT_D)
    return c


def tex_suit_arm():
    c = Canvas(16, 32, SUIT)
    c.rect(0, 28, 15, 29, SHIRT_B)
    c.rect(6, 29, 9, 29, GOLD)
    c.rect(0, 0, 15, 0, SUIT_D)
    return c


def tex_suit_leg():
    c = Canvas(16, 32, SUIT)
    c.rect(7, 0, 8, 31, SUIT_D)
    return c


def build_buyer(kit, root, A):
    Rn = kit.rand
    skin = solid(kit, "buyer skin", BSKIN)
    pose = dict(hips=(0, 0, 0.9), spine=(-3, 0, -4), head=(-3, 4, 9),
                armR=dict(wrist=(-0.44, -0.08, 1.72), pole=(-1, 0.3, -0.7), hand=(-0.12, -0.05, 1), palm=(0, -1, 0),
                          grip='open', thumb=(1, 0, 0)),
                armL=dict(wrist=(0.155, -0.06, 0.92), pole=(1, 0.7, 0.1), hand=(-0.35, 0.25, -1), palm=(-1, 0, 0),
                          grip='pocket'),
                legR=dict(ankle=(-0.1, 0.02, 0.05), toe=(-0.3, -1, 0)), legL=dict(ankle=(0.16, -0.06, 0.05), toe=(0.4, -1, 0)))
    rad = [(0.16, 0.11), (0.165, 0.114), (0.152, 0.11), (0.176, 0.12), (0.212, 0.122), (0.09, 0.072)]
    B = dict(torso=tex_mat("buyer torso", tex_buyer_torso(Rn)), head=tex_mat("buyer head", tex_buyer_head(Rn)),
             arm=tex_mat("suit arm", tex_suit_arm()), leg=tex_mat("suit leg", tex_suit_leg()), skin=skin,
             foot=dress_shoe(INK, "#3a2f5a"), pose=pose, rad=rad, arm_k=1.06)
    Jt = body(kit, root, B)
    spine, head, hips = Jt['spine'], Jt['head'], Jt['hips']

    tube(kit, "jacket skirt", [(0, 0.0, 0.0), (0, 0.004, -0.2)], [(0.168, 0.118), (0.185, 0.13)],
         tex_mat("suit skirt", tex_suit_skirt()), hips.ob, sides=10, caps=(False, False))
    for sx in (1, -1):
        tbox(kit, f"shoulder pad {sx}", (sx * 0.15, 0.0, 0.555), (0.11, 0.12, 0.024), solid(kit, "suit", SUIT, shade=SUIT_D),
             spine.ob, rot=(0, sx * 16, 0))
    gold = solid(kit, "gold", GOLD, 0.65, shade=GOLD_D)
    cp = [(-0.075, 0.0, 0.57), (-0.065, -0.07, 0.52), (-0.04, -0.11, 0.47), (0, -0.124, 0.44), (0.04, -0.11, 0.47),
          (0.065, -0.07, 0.52), (0.075, 0.0, 0.57)]
    tube(kit, "gold chain", cp, 0.009, gold, spine.ob, sides=4, caps=(False, False))
    tube(kit, "medallion", [(0, -0.128, 0.42), (0, -0.142, 0.42)], 0.024, gold, spine.ob, sides=8)
    tube(kit, "pinky ring", [(0.03, 0.0, -0.1), (0.03, 0.0, -0.115)], 0.014, gold, Jt['armR'][2].ob, sides=6)

    # slicked-back pompadour and dark shades
    lowball(kit, "pompadour", (0, -0.035, 0.282), (0.092, 0.1, 0.045), solid(kit, "slick hair", BHAIR, 0.3, shade="#3a3a5a"),
            head.ob)
    sunglasses(kit, "sunglasses", head.ob, 0.178, y=-0.112, frame_col=GOLD)

    socket(kit, A, "hand R", Jt['armR'][2].ob, (0, 0, -0.08))
    socket(kit, A, "head", head.ob, (0, -0.1, 0.17))


# ---------------------------------------------------------------- module interface
def officer(pose):
    return lambda kit, root, A: build_officer(kit, root, A, pose)


ASSETS = [
    ("Police Officer", prefixed("Police Officer", officer('stand'))),
    ("Police Officer Climb", prefixed("Police Officer Climb", officer('climb'))),
    ("Police Officer Run", prefixed("Police Officer Run", officer('run'))),
    ("Detective", prefixed("Detective", build_detective)),
    ("Forger Kevin", prefixed("Forger Kevin", build_forger_kevin)),
    ("Diamond Buyer", prefixed("Diamond Buyer", build_buyer)),
]
SPACING = 6

LINEUP_X = 1.0


def build_lineup(kit, root):
    p = kit.empty("lineup crew", root, (-3 * LINEUP_X, 0, 0))
    named("Player Pink", build_team_player, team='pink')(kit, p)
    for i, (name, fn) in enumerate(ASSETS):
        a = kit.empty(f"lineup {name}", root, ((i - 2) * LINEUP_X, 0, 0))
        fn(kit, a)


SCENES = [
    dict(name="lineup", build=build_lineup, cam=((0, -7.6, 1.4), (0, 0, 0.95), 38), res=(1600, 900)),
    dict(name="lineup faces cops", build=build_lineup, cam=((-1.0, -4.2, 1.6), (-1.0, 0, 1.3), 45), res=(1600, 900)),
    dict(name="lineup faces civilians", build=build_lineup, cam=((2.0, -4.2, 1.6), (2.0, 0, 1.3), 45), res=(1600, 900)),
]
