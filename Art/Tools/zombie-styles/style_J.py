"""Style J: Voxel. Hand-authored MagicaVoxel / Crossy Road look: every part is a deliberately placed voxel model."""
from common import *

KEY = "J"
LABEL = "Voxel"
SHADER = 'facet'
WORLD = "#bfe3ff"
FLOOR = "#9ccc65"

S = 0.04    # character voxel
G = 0.01    # gun voxel


def make_kit(col, seed):
    return Kit(col, SHADER, seed)

COLORS = {
    'sky': "#4fc3f7", 'indigo': "#3949ab", 'strap': "#283593", 'skin': "#ffcc99", 'cheek': "#ff8a80",
    'white': "#f7f7f2", 'orange': "#ffb74d", 'orange_dk': "#f57c00", 'hair': "#6d4c41", 'eye': "#212121",
    'lip': "#9c3d3d", 'sole': "#eceff1", 'shoe': "#455a64", 'pink': "#f48fb1", 'pink_dk': "#ec407a",
    'cone': "#e3b26a", 'cone_dk': "#b97a34", 'mint': "#a5d6a7", 'yellow': "#fff176", 'cream': "#fff3e0",
    'choc': "#6d4c41", 'choc_dk': "#4e342e",
    'zskin': "#7cb342", 'zskin_dk': "#558b2f", 'zskin_lt': "#9ccc65", 'teal': "#26a69a", 'teal_dk': "#00796b",
    'pants': "#5d4037", 'pants_dk': "#3e2723", 'brain': "#f48fb1", 'brain_dk': "#c2185b", 'blood': "#e53935",
    'blood_dk': "#b71c1c", 'blood_hi': "#ff5252", 'mouth': "#3a0b14", 'tooth': "#fffde7", 'red_eye': "#ff1744",
    'bone': "#fff8e1", 'zhair': "#4e342e",
    'gun': "#ff7043", 'gun_dk': "#e64a19", 'gblue': "#4fc3f7", 'gblue_dk': "#0288d1", 'cherry': "#e53935",
    'stem': "#33691e", 'smoke': "#ffffff", 'smoke_dk': "#e3eef7", 'spark': "#fff59d",
}


class Pal:
    """Material lookup. pal['x'] is the flat color, pal.j('x') a randomly jittered shade (hand-painted voxel noise)."""

    def __init__(self, kit):
        self.kit = kit

    def __getitem__(self, name):
        return self.kit.mat(name, COLORS[name])

    def j(self, name):
        f = self.kit.rand.choice((0.93, 1.0, 1.0, 1.0, 1.05))
        return self.kit.mat(f"{name} {f}", hex_scale(COLORS[name], f))


def fill(c, xs, ys, zs, m):
    """Fill an inclusive voxel box. m: material or zero-arg callable (per-voxel jitter)."""
    for i in range(xs[0], xs[1] + 1):
        for j in range(ys[0], ys[1] + 1):
            for k in range(zs[0], zs[1] + 1):
                c[(i, j, k)] = m() if callable(m) else m


def paint(c, xs, ys, zs, m):
    """Recolor existing voxels inside an inclusive box."""
    for i in range(xs[0], xs[1] + 1):
        for j in range(ys[0], ys[1] + 1):
            for k in range(zs[0], zs[1] + 1):
                if (i, j, k) in c:
                    c[(i, j, k)] = m() if callable(m) else m


def pixels(c, rows, i0, j, ktop, pal):
    """ASCII pixel art onto the XZ plane at depth j. rows run top to bottom; chars missing from pal are skipped,
    '-' removes the voxel."""
    for r, row in enumerate(rows):
        for n, ch in enumerate(row):
            key = (i0 + n, j, ktop - r)
            if ch == '-':
                c.pop(key, None)
            elif ch in pal:
                c[key] = pal[ch]


def part(kit, name, cells, parent, pivot, ppivot=(0, 0, 0), rot=(0, 0, 0), size=S):
    """One voxel part on its own pivot. Cells live in one shared grid; pivot/ppivot are grid coordinates."""
    e = kit.empty(name, parent, tuple((a - b) * size for a, b in zip(pivot, ppivot)), rot)
    kit.voxels(name, cells, size, e, tuple(-a * size for a in pivot))
    return e


def rotm(rot):
    return Euler([math.radians(a) for a in rot]).to_matrix()


# ------------------------------------------------------------------------------------------------ player
def build_player(kit, root):
    P = Pal(kit)

    # legs: stubby indigo trousers, white-soled sneakers
    for side, i0, rot in (('R', -4, (-6, 0, 0)), ('L', 1, (5, 0, 0))):
        c = {}
        fill(c, (i0, i0 + 2), (-2, 1), (3, 9), lambda: P.j('indigo'))
        fill(c, (i0, i0 + 2), (-2, 1), (3, 3), P['strap'])
        fill(c, (i0, i0 + 2), (-3, 1), (1, 2), P['shoe'])
        fill(c, (i0, i0 + 2), (-3, 1), (0, 0), P['sole'])
        paint(c, (i0 + 1, i0 + 1), (-3, -3), (2, 2), P['sole'])
        part(kit, f"leg {side}", c, root, (i0 + 1.5, 0, 10), rot=rot)

    # torso: shirt, apron color blocks, cooler straps
    body = kit.empty("body", root, (0, 0, 10 * S))
    c = {}
    fill(c, (-5, 4), (-3, 2), (10, 11), P['indigo'])
    fill(c, (-5, 4), (-3, 2), (12, 22), lambda: P.j('sky'))
    paint(c, (-4, 3), (-3, -3), (10, 15), P['white'])          # apron waist
    paint(c, (-3, 2), (-3, -3), (16, 21), P['white'])          # bib
    fill(c, (-4, 3), (-3, -3), (5, 9), P['white'])             # apron skirt in front of the legs
    fill(c, (-4, 3), (-3, -3), (4, 4), P['sky'])               # hem trim
    paint(c, (-5, -5), (-2, 2), (14, 14), P['white'])          # apron strings around the waist
    paint(c, (4, 4), (-2, 2), (14, 14), P['white'])
    fill(c, (-5, -6), (2, 3), (13, 14), P['white'])            # bow knot at the back
    paint(c, (-2, -2), (-3, 2), (22, 22), P['white'])          # neck strap
    paint(c, (1, 1), (-3, 2), (22, 22), P['white'])
    paint(c, (-4, -4), (-3, 2), (16, 22), P['strap'])          # cooler straps
    paint(c, (3, 3), (-3, 2), (16, 22), P['strap'])
    paint(c, (-4, -4), (-2, 2), (22, 22), P['strap'])
    paint(c, (3, 3), (-2, 2), (22, 22), P['strap'])
    fill(c, (-2, 1), (-4, -4), (10, 12), P['white'])           # pocket
    fill(c, (-2, 1), (-4, -4), (12, 12), P['sky'])
    pixels(c, ["-pp-", "pppp", "-cc-", "-cc-"], -2, -4, 20,     # ice cream badge on the bib, raised one voxel
           {'p': P['pink'], 'c': P['cone']})
    part(kit, "torso", c, body, (0, 0, 10), (0, 0, 10))

    # cooler backpack with spare pints in the side pockets
    c = {}
    fill(c, (-4, 3), (3, 4), (14, 21), P['strap'])
    fill(c, (-5, 4), (5, 10), (12, 25), lambda: P.j('orange'))
    fill(c, (-5, 4), (5, 10), (12, 12), P['white'])
    fill(c, (-6, 5), (4, 11), (26, 27), P['white'])
    fill(c, (-2, 1), (7, 8), (28, 29), P['shoe'])
    for i in range(-1, 1):
        for j in range(7, 9):
            c.pop((i, j, 28), None)
    flake = ["s.s.s", ".sss.", "sssss", ".sss.", "s.s.s"]
    for r, row in enumerate(flake):
        for n, ch in enumerate(row):
            if ch == 's':
                c[(4, 6 + n, 24 - r)] = P['sky']
                c[(-5, 6 + n, 24 - r)] = P['sky']
    for i0, band, lid in ((5, 'pink', 'pink_dk'), (-8, 'mint', 'choc')):
        fill(c, (i0, i0 + 2), (5, 7), (13, 17), P['white'])
        fill(c, (i0, i0 + 2), (5, 7), (15, 15), P[band])
        fill(c, (i0, i0 + 2), (5, 7), (18, 18), P[lid])
        fill(c, (i0, i0 + 2), (4, 8), (13, 14), P['strap'])
    part(kit, "cooler", c, body, (0, 0, 10), (0, 0, 10))

    # head: big Crossy Road cube with a pixel-art face
    head = kit.empty("head pivot", body, (0, -0.5 * S, 13 * S), (0, 0, 4))
    h = {}
    fill(h, (-5, 4), (-5, 4), (23, 33), lambda: P.j('skin'))
    fill(h, (-5, 4), (-4, 4), (33, 33), P['hair'])
    fill(h, (-5, 4), (4, 4), (25, 33), P['hair'])
    fill(h, (-5, -5), (-2, 4), (29, 33), P['hair'])
    fill(h, (4, 4), (-2, 4), (29, 33), P['hair'])
    fill(h, (-5, -5), (-2, -1), (27, 28), P['hair'])
    fill(h, (4, 4), (-2, -1), (27, 28), P['hair'])
    pixels(h, [
        "HHHHHHHHHH",
        "HHH.HH.HHH",
        "H........H",
        "..bb..bb..",
        "..........",
        "..WE..WE..",
        "..EE..EE..",
        "..........",
        "rrm....mrr",
        "...mmmm...",
        "..........",
    ], -5, -5, 33, {'H': P['hair'], 'b': P['hair'], 'W': P['white'], 'E': P['eye'], 'r': P['cheek'], 'm': P['lip']})
    fill(h, (-6, -6), (-1, 0), (26, 28), P['skin'])
    fill(h, (5, 5), (-1, 0), (26, 28), P['skin'])
    part(kit, "head", h, head, (0, -0.5, 23), (0, -0.5, 23))

    # paper soda-jerk hat, tilted
    c = {}
    fill(c, (-5, 4), (-5, 4), (34, 34), P['sky'])
    fill(c, (-5, 4), (-5, 4), (35, 35), P['white'])
    fill(c, (-4, 3), (-5, 4), (36, 36), P['white'])
    fill(c, (-3, 2), (-4, 3), (37, 37), P['white'])
    fill(c, (-1, 0), (-3, 2), (38, 38), P['white'])
    pixels(c, ["pp", "cc"], -1, -6, 36, {'p': P['pink'], 'c': P['cone']})
    part(kit, "hat", c, head, (0, 0, 34), (0, -0.5, 23), rot=(-4, 7, 0))

    # arms. Right arm (-X) raised, aiming the Scoop Pistol forward.
    for side, i0, rot in (('R', -8, (-86, 0, 4)), ('L', 5, (8, -12, 0))):
        c = {}
        fill(c, (i0, i0 + 2), (-2, 0), (13, 18), lambda: P.j('skin'))
        fill(c, (i0, i0 + 2), (-2, 0), (19, 22), lambda: P.j('sky'))
        fill(c, (i0, i0 + 2), (-2, 0), (19, 19), P['indigo'])
        arm = part(kit, f"arm {side}", c, body, (i0 + 1.5, -0.5, 22), (0, 0, 10), rot=rot)
        if side == 'R':
            sc = 1.25
            grip = Vector((0, 0.072, -0.075)) * sc
            hand = Vector((0, 0, -8 * S))
            ginv = rotm(rot).inverted()
            gun = kit.empty("held gun", arm, hand - ginv @ grip, (0, 0, 0), (sc, sc, sc))
            gun.rotation_euler = ginv.to_euler()
            build_gun(kit, gun)


# ------------------------------------------------------------------------------------------------ zombie
def build_zombie(kit, root, hit=False):
    P = Pal(kit)
    R = kit.rand

    # legs: one shoe, one bare foot, ragged trouser hems
    for side, i0, pants_low, rot in (('R', -4, 4, (-12, 0, 3)), ('L', 1, 6, (10, 4, -4))):
        c = {}
        fill(c, (i0, i0 + 2), (-2, 0), (0, 10), lambda: P.j('zskin'))
        for i in range(i0, i0 + 3):
            for j in range(-2, 1):
                low = pants_low - R.choice((0, 0, 1, 2))
                for k in range(low, 11):
                    c[(i, j, k)] = P.j('pants')
        fill(c, (i0, i0 + 2), (-2, 0), (10, 10), P['pants_dk'])
        if side == 'R':
            fill(c, (i0, i0 + 2), (-3, 0), (0, 1), P['shoe'])
            paint(c, (i0 + 1, i0 + 1), (-2, -2), (6, 7), P['zskin_dk'])   # torn knee
        else:
            c[(i0, -3, 0)] = P['zskin_dk']
            c[(i0 + 2, -3, 0)] = P['zskin_dk']
            c[(i0 + 1, -3, 0)] = P['zskin']
        part(kit, f"leg {side}", c, root, (i0 + 1.5, -0.5, 10.5), rot=rot)

    # torso: torn teal shirt, ribs peeking out, ice cream splat on the chest
    trot = (-16, 10, 12) if hit else (24, 0, -6)
    body = kit.empty("torso pivot", root, (0, -0.5 * S, 11 * S), trot)
    c = {}
    fill(c, (-5, 4), (-3, 2), (11, 12), P['pants'])
    fill(c, (-5, 4), (-3, 2), (12, 12), P['pants_dk'])
    fill(c, (-5, 4), (-3, 2), (13, 22), lambda: P.j('teal'))
    for i in range(-5, 5):                                  # ragged hem with belly showing through
        for j in range(-3, 3):
            if R.random() < 0.4:
                c[(i, j, 13)] = P.j('zskin')
                if R.random() < 0.4:
                    c[(i, j, 14)] = P['zskin']
    pixels(c, ["dddd", "dGGd", "dBBd", "dGGd", "dBBd", "-dd-"], -5, -3, 18,
           {'d': P['teal_dk'], 'G': P['zskin_dk'], 'B': P['bone']})
    pixels(c, ["dd", "Gd"], 2, -3, 14, {'d': P['teal_dk'], 'G': P['zskin']})
    paint(c, (-2, 1), (-3, -3), (22, 22), P['teal_dk'])
    paint(c, (-1, 0), (-3, 2), (22, 22), P['zskin_dk'])
    for (i, k), ch in {(0, 21): 'p', (1, 21): 'p', (2, 21): 'w', (-1, 20): 'p', (0, 20): 'w', (1, 20): 'p',
                       (2, 20): 'p', (3, 20): 'p', (-1, 19): 'p', (0, 19): 'p', (1, 19): 'p', (2, 19): 'w',
                       (3, 19): 'p', (0, 18): 'p', (1, 18): 'p', (2, 18): 'p', (0, 17): 'p', (2, 17): 'p',
                       (0, 16): 'p', (2, 15): 'p'}.items():
        c[(i, -4, k)] = P['pink'] if ch == 'p' else P['cream']
    c[(1, -5, 20)] = P['cherry']
    for (i, k) in ((-2, 21), (4, 18), (-1, 17), (3, 16)):
        if (i, -3, k) in c:
            c[(i, -3, k)] = P['pink']
    if hit:                                                  # shoulder stump where the left arm was
        paint(c, (4, 4), (-2, 0), (18, 22), P['blood_dk'])
        fill(c, (5, 5), (-2, 0), (19, 21), P['blood'])
        c[(6, -1, 20)] = P['bone']
        c[(5, -1, 18)] = P['blood']
        c[(5, -1, 17)] = P['blood']
        for (j, k) in ((-4, 21), (-4, 20), (-4, 19), (-4, 17), (-3, 22), (-3, 23)):   # ice cream that hit him
            c[(3, j, k)] = P['pink']
        c[(2, -4, 20)] = P['cream']
    part(kit, "torso", c, body, (0, -0.5, 11), (0, -0.5, 11))

    # head: gaping block mouth, mismatched eyes, exposed brain, voxel blood drips
    hrot = (-20, -14, -24) if hit else (-18, 8, 12)
    head = kit.empty("head pivot", body, (-0.5 * S, -0.5 * S, 12 * S), hrot)
    h = {}
    fill(h, (-5, 4), (-5, 3), (23, 34), lambda: P.j('zskin'))
    pixels(h, [
        "GgggggGGGg",
        "GGGgggGGGG",
        "gwwwggGGGg",
        "gwwwggGrGg",
        "gwkwggGGGg",
        "ggggnngggg",
        "gtmtmmtmtg",
        "gmmmmmmmmg",
        "gmmmmmmmmg",
        "gmmtmmtmmg",
        "bggggggggb",
        "Gggggggggg",
    ], -5, -5, 34, {'g': P['zskin'], 'G': P['zskin_dk'], 'w': P['white'], 'k': P['eye'], 'r': P['red_eye'],
                    'n': P['mouth'], 't': P['tooth'], 'm': P['mouth'], 'b': P['blood']})
    for i in range(-4, 4):                                   # carve the mouth two voxels deep
        for k in range(25, 29):
            if h[(i, -5, k)] is P['mouth']:
                del h[(i, -5, k)]
                del h[(i, -4, k)]
                h[(i, -3, k)] = P['mouth']
    fill(h, (-1, 0), (-4, -4), (25, 25), P['blood_hi'])      # tongue
    fill(h, (-4, -2), (-6, -6), (30, 32), P['white'])        # bulging big eye
    h[(-3, -7, 30)] = P['eye']
    for (i, k) in ((-4, 22), (-4, 21), (-4, 20), (3, 22), (3, 21), (0, 22)):   # drool of blood off the chin
        h[(i, -5, k)] = P['blood']
    # exposed brain on top: the skull is open, one-voxel bumps, fold lines, blood dripping off the rim
    for i in range(-2, 5):
        for j in range(-4, 3):
            if ((i - 1.2) / 3.6) ** 2 + ((j + 0.8) / 3.4) ** 2 > 1:
                continue
            for k in (33, 34):
                h[(i, j, k)] = P['brain_dk'] if (i - j + k) % 3 == 0 and k == 34 else P['brain']
            if (i + j) % 2 == 0:
                h[(i, j, 35)] = P['brain']
                if R.random() < 0.25:
                    h[(i, j, 36)] = P['brain']
            elif R.random() < 0.3:
                h[(i, j, 35)] = P['brain_dk']
    for (j, kl) in ((-3, 30), (-1, 28), (1, 31)):
        for k in range(kl, 35):
            h[(5, j, k)] = P['blood'] if k > kl else P['blood_dk']
    for (i, kl) in ((1, 31), (3, 32)):
        for k in range(kl, 35):
            h[(i, -6, k)] = P['blood']
    fill(h, (-5, -3), (-1, 2), (35, 35), P['zhair'])
    h[(-4, 1, 36)] = P['zhair']
    h[(-5, -3, 35)] = P['zhair']
    fill(h, (-6, -6), (-1, 0), (28, 30), P['zskin'])        # one ear, the other is gone
    paint(h, (4, 4), (-1, 0), (28, 29), P['blood_dk'])
    part(kit, "head", h, head, (-0.5, -1, 23), (0, -0.5, 11 + 12))

    # arms: uneven lengths, torn sleeves, claw fingers
    for side, i0, top_skin, sleeve, rot in (('R', -8, 10, 18, (-30, 75, 10) if hit else (-104, 0, 8)),
                                            ('L', 5, 14, 19, (-76, 0, -10))):
        c = {}
        fill(c, (i0, i0 + 2), (-2, 0), (top_skin, 22), lambda: P.j('zskin'))
        for i in range(i0, i0 + 3):
            for j in range(-2, 1):
                low = sleeve - R.choice((0, 0, 1, 2))
                for k in range(low, 23):
                    c[(i, j, k)] = P.j('teal')
        for i, ln in ((i0, 2), (i0 + 1, 1), (i0 + 2, 2)):
            for d in range(1, ln + 1):
                c[(i, -2, top_skin - d)] = P['zskin_dk']
        c[(i0 + 1, 0, top_skin - 1)] = P['zskin_dk']
        if side == 'R':
            paint(c, (i0, i0), (-1, -1), (13, 14), P['blood_dk'])
            c[(i0 - 1, -1, 14)] = P['bone']
        if side == 'L' and hit:
            paint(c, (i0, i0 + 2), (-2, 0), (22, 22), P['blood'])
            c[(i0 + 1, -1, 22)] = P['blood_dk']
            c[(i0 + 1, -1, 23)] = P['bone']
            c[(i0 + 1, -1, 24)] = P['bone']
            c[(i0 + 1, -2, 23)] = P['blood']
        pivot = (i0 + 1.5, -0.5, 22)
        if side == 'L' and hit:
            # detached arm: flies to world +X, -Y, +Z from the shoulder, spinning
            tm = rotm(trot)
            shoulder = Vector((0, -0.5, 11)) * S + tm @ (Vector(pivot) - Vector((0, -0.5, 11))) * S
            rinv = root.rotation_euler.to_matrix().inverted()
            fly = shoulder + rinv @ Vector((0.52, -0.3, 0.42))
            e = kit.empty("arm L (detached)", root, fly, (-40, 65, 140))
            kit.voxels("arm L", c, S, e, tuple(-a * S for a in pivot))
            fx_burst(kit, P, root, shoulder, fly, rinv)
        else:
            part(kit, f"arm {side}", c, body, pivot, (0, -0.5, 11), rot=rot)


# ------------------------------------------------------------------------------------------------ hit FX
def blob(R, n):
    """Chunky voxel blob: a 2^3 cube with bites taken out, or a 3^3 cube with most corners knocked off."""
    if n == 2:
        cells = [(i, j, k) for i in range(2) for j in range(2) for k in range(2)]
        for _ in range(R.randint(1, 3)):
            cells.remove(R.choice(cells[1:]))
        return cells
    return [(i, j, k) for i in range(3) for j in range(3) for k in range(3)
            if abs(i - 1) + abs(j - 1) + abs(k - 1) <= 2 or R.random() < 0.2]


def chunk(kit, name, parent, center, cells, size, mat):
    """Axis-aligned debris chunk centered on center (root space)."""
    c = {key: (mat() if callable(mat) else mat) for key in cells}
    ext = Vector([max(k[a] for k in cells) + 1 for a in range(3)]) * size * 0.5
    kit.voxels(name, c, size, parent, tuple(Vector(center) - ext))


def fx_burst(kit, P, root, shoulder, fly, rinv):
    R = kit.rand
    d = (fly - shoulder).normalized()
    blood = lambda: P[R.choice(('blood', 'blood', 'blood_dk', 'blood_hi'))]

    # blood trail of cubes following the flying arm, shrinking with distance
    for n in range(30):
        t = R.uniform(0.05, 1.0)
        spread = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1))) * 0.07 * (0.3 + t)
        p = shoulder + (fly - shoulder) * t + spread + Vector((0, 0, 0.1 * math.sin(t * math.pi)))
        size = 0.05 - 0.032 * t + R.uniform(-0.006, 0.006)
        if R.random() < 0.35:
            chunk(kit, "blood chunk", root, p, blob(R, 2), size * 0.6, blood)
        else:
            chunk(kit, "blood cube", root, p, [(0, 0, 0)], size, blood)

    # radial burst of blood cubes and ice cream scoop chunks around the stump
    for n in range(18):
        v = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1) + 0.6)).normalized()
        v = (v + d * 0.6).normalized()
        p = shoulder + v * R.uniform(0.2, 0.6)
        chunk(kit, "blood cube", root, p, [(0, 0, 0)], R.uniform(0.018, 0.04), blood)
    for n in range(5):
        v = Vector((R.gauss(0, 1) + 0.8, R.gauss(0, 1) - 0.5, R.gauss(0, 1) + 0.8)).normalized()
        chunk(kit, "blood blob", root, shoulder + v * R.uniform(0.25, 0.5), blob(R, 3), 0.026, blood)
    flavors = ('pink', 'pink', 'cream', 'choc', 'mint')
    for n in range(12):
        v = Vector((R.gauss(0, 1), R.gauss(0, 1) - 0.5, R.gauss(0, 1) + 0.8)).normalized()
        p = shoulder + v * R.uniform(0.18, 0.6)
        fl = flavors[n % len(flavors)]
        chunk(kit, "scoop chunk", root, p, blob(R, 3), R.uniform(0.026, 0.038), lambda: P.j(fl))
    for n in range(60):                                       # sprinkle confetti, tiny voxels
        v = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 1) + 0.5)).normalized()
        p = shoulder + v * R.uniform(0.1, 0.7)
        cells = [(0, 0, 0), (1, 0, 0)] if R.random() < 0.5 else [(0, 0, 0), (0, 0, 1)]
        chunk(kit, "sprinkle", root, p, cells, 0.011,
              P[R.choice(('pink_dk', 'yellow', 'sky', 'mint', 'white', 'orange'))])

    # waffle cone shards: two-tone chunks of cone with a cap of pink
    for n in range(5):
        v = Vector((R.gauss(0, 1) + 0.6, R.gauss(0, 1) - 0.6, R.gauss(0, 1) + 0.9)).normalized()
        p = shoulder + v * R.uniform(0.25, 0.55)
        cells = [(i, j, k) for i in range(3) for j in range(2) for k in range(2)]
        c = {key: P['cone_dk'] if (key[0] + key[2]) % 2 else P['cone'] for key in cells}
        for i in range(3):
            c[(i, 0, 2)] = P['pink']
            c[(i, 1, 2)] = P['pink']
        kit.voxels("cone shard", c, 0.022, root, tuple(p))

    # drip column falling from the stump
    for n in range(6):
        p = shoulder + Vector((0.02, 0, -0.08 - n * 0.09)) + Vector((R.uniform(-0.02, 0.02), R.uniform(-0.02, 0.02), 0))
        chunk(kit, "blood drip", root, p, [(0, 0, 0), (0, 0, 1)] if n % 2 else [(0, 0, 0)], 0.022 - n * 0.002, blood)

    # floor splat: a stepped voxel puddle of blood and melted ice cream, plus scattered droplets
    g = 0.025
    splat = {}
    cx, cy = (shoulder.x + 0.12) / g, (shoulder.y - 0.12) / g
    lobes = [(cx, cy, 7.5)] + [(cx + R.uniform(-9, 9), cy + R.uniform(-9, 9), R.uniform(2.5, 5)) for _ in range(6)]
    pink_lobes = [(cx + 6, cy - 4, 5.0), (cx + 9, cy - 1, 3.0), (cx + 1, cy - 9, 2.5)]
    for i in range(int(cx) - 22, int(cx) + 23):
        for j in range(int(cy) - 22, int(cy) + 23):
            inb = min((((i + 0.5 - a) ** 2 + (j + 0.5 - b) ** 2) ** 0.5 - r) for a, b, r in lobes)
            inp = min((((i + 0.5 - a) ** 2 + (j + 0.5 - b) ** 2) ** 0.5 - r) for a, b, r in pink_lobes)
            if inp < 0:
                splat[(i, j, 0)] = P['pink'] if inp < -1 else P['pink_dk']
                if inp < -2.5:
                    splat[(i, j, 1)] = P['cream'] if (i + j) % 5 == 0 else P['pink']
            elif inb < 0:
                splat[(i, j, 0)] = P['blood_dk'] if inb > -1 else P['blood']
                if inb < -3:
                    splat[(i, j, 1)] = P['blood']
            elif inb < 4 and R.random() < 0.05:
                splat[(i, j, 0)] = P['blood']
    kit.voxels("floor splat", splat, g, root, (0, 0, 0))
    # landing splat under the flying arm
    land = {}
    lx, ly = fly.x / g, fly.y / g
    for i in range(int(lx) - 6, int(lx) + 7):
        for j in range(int(ly) - 6, int(ly) + 7):
            r = ((i + 0.5 - lx) ** 2 + (j + 0.5 - ly) ** 2) ** 0.5
            if r < 3.2 + R.uniform(0, 1.6):
                land[(i, j, 0)] = P['blood']
    kit.voxels("arm splat", land, g, root, (0, 0, 0))


# ------------------------------------------------------------------------------------------------ gun
def build_gun(kit, root):
    """Scoop Pistol at 1 cm voxels. Grid origin is the receiver center; barrel along -j, grip down."""
    P = Pal(kit)
    R = kit.rand
    c = {}

    # waffle-cone muzzle with a pink scoop loaded in its mouth
    for j in range(-22, -13):
        r = 2.6 + (-14 - j) * 0.45
        for i in range(-8, 8):
            for k in range(-7, 9):
                d = math.hypot(i + 0.5, k + 0.5 - 1)
                if d <= r and (d > r - 1.6 or j >= -20):
                    dark = (j + i + k) % 4 == 0 or (j - i - k) % 4 == 0
                    c[(i, j, k)] = P['cone_dk'] if dark and j > -22 else P['cone']
    for i in range(-6, 6):
        for j in range(-24, -17):
            for k in range(-5, 7):
                if math.hypot(math.hypot(i + 0.5, k + 0.5 - 1), (j + 0.5 + 18.6) * 1.1) <= 4.4:
                    c.setdefault((i, j, k), P['pink'])

    # barrel with collar rings
    fill(c, (-2, 1), (-13, -6), (-1, 2), lambda: P.j('gblue'))
    fill(c, (-3, 2), (-13, -13), (-2, 3), P['gun'])
    fill(c, (-3, 2), (-9, -9), (-2, 3), P['gun'])
    fill(c, (-1, 0), (-11, -11), (3, 4), P['gun'])

    # receiver
    fill(c, (-3, 2), (-6, 8), (-3, 5), lambda: P.j('gun'))
    for key in [(j, k) for j in (-6, 8) for k in (5, -3)] + [(7, 5), (8, 4)]:
        for i in range(-3, 3):
            c.pop((i, key[0], key[1]), None)
    paint(c, (-3, 2), (-5, 8), (1, 1), P['gblue'])
    paint(c, (-3, 2), (-5, 7), (-3, -3), P['gun_dk'])
    fill(c, (-2, 1), (9, 9), (-1, 4), P['gblue'])
    fill(c, (-1, 0), (10, 10), (4, 6), P['gblue_dk'])
    for (j, k) in ((5, 3), (6, 3), (5, 2), (6, 2)):         # side vent pixels
        c[(2, j, k)] = P['gun_dk']
        c[(-3, j, k)] = P['gun_dk']

    # pint-tub magazine
    for k in range(6, 15):
        r = 4.3 + (k - 6) * 0.08 + (0.7 if k == 14 else 0)
        if k == 6:
            r = 3.4
        for i in range(-6, 6):
            for j in range(-5, 7):
                if math.hypot(i + 0.5, j + 0.5 - 1) <= r:
                    if k == 6:
                        m = P['gblue_dk']
                    elif 8 <= k <= 11:
                        m = P['pink'] if (k == 10 and (i + j) % 3 == 0) else P['gblue']
                    else:
                        m = P['white']
                    c[(i, j, k)] = m

    # chocolate scoop with sprinkles, overhanging lumps and a cherry
    scoop = []
    for i in range(-7, 7):
        for j in range(-6, 8):
            for k in range(15, 21):
                if math.hypot(math.hypot(i + 0.5, j + 0.5 - 1), (k + 0.5 - 14.6) * 1.05) <= 5.1:
                    c[(i, j, k)] = P['choc'] if R.random() < 0.8 else P['choc_dk']
                    scoop.append((i, j, k))
    for a in range(0, 360, 30):
        x, y = 5.4 * math.cos(math.radians(a)), 5.4 * math.sin(math.radians(a)) + 1
        key = (math.floor(x), math.floor(y))
        c[(key[0], key[1], 15)] = P['choc']
        if a % 90 == 30:
            c[(key[0], key[1], 14)] = P['choc']
            c[(key[0], key[1], 13)] = P['choc_dk']
    for key in scoop:
        up = (key[0], key[1], key[2] + 1)
        if up not in c and R.random() < 0.3:
            c[up] = P[R.choice(('pink_dk', 'yellow', 'sky', 'mint', 'white'))]
    fill(c, (-1, 0), (0, 1), (20, 21), P['cherry'])
    c[(0, 1, 22)] = P['stem']
    c[(0, 2, 23)] = P['stem']

    # grip: raked back, finger grooves, knurled sides, orange butt cap
    for k in range(-15, -3):
        s = (-4 - k) // 3
        for j in range(4 + s, 9 + s):
            if j == 4 + s and k % 3 == 0:
                continue
            for i in range(-2, 2):
                knurl = i in (-2, 1) and 5 + s <= j <= 7 + s and -13 <= k <= -6 and (j + k) % 2 == 0
                c[(i, j, k)] = P['gblue_dk'] if knurl else P.j('gblue')
    fill(c, (-2, 1), (8, 12), (-16, -16), P['gun'])

    # trigger guard and trigger
    fill(c, (-1, 0), (-3, -3), (-9, -4), P['gun'])
    fill(c, (-1, 0), (-3, 4), (-9, -9), P['gun'])
    for (j, k) in ((0, -4), (0, -5), (-1, -6), (-1, -7)):
        c[(-1, j, k)] = P['sole']
        c[(0, j, k)] = P['sole']

    kit.voxels("scoop pistol", c, G, root, (0, 0, 0))
