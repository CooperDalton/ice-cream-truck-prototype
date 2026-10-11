"""Batch 'shop' (style H): Kevin's depot stall, the SCOOP SLOTS machine, its brain reel symbol and Shopkeeper Kevin.
Standing assets: root on the floor at the center, front -Y. Sockets are empties named '<Asset> socket <purpose>';
moving parts are empties on their hinge (lever, head, jaw, arms, legs)."""
from style_H import *
from h_stops import FONT2
from h_weapons import tex_candy, gem
from h_items import build_sugar_sack, build_milk_crate, build_cocoa_bag, run as item_run

FONT3 = dict(FONT2)
FONT3.update({"'": (".#.", ".#.", "...", "...", "..."), ':': ("...", ".#.", "...", ".#.", "...")})


def txt3(c, s, x, y, col, k=1):
    """3x5 pixel font with digits, J, Q, apostrophe and colon. (x, y) = top-left texel, y counts up."""
    for ch in s:
        for r, row in enumerate(FONT3.get(ch, ())):
            for q, b in enumerate(row):
                if b == '#':
                    c.rect(x + q * k, y - (r + 1) * k + 1, x + q * k + k - 1, y - r * k, col)
        x += 4 * k


def txt3_c(c, s, cx, y, col, k=1):
    txt3(c, s, cx - text_w(s, k) // 2, y, col, k)


def prefixed(asset, fn):
    """Build, then prefix every descendant name with the asset name exactly once."""
    def build(kit, root):
        fn(kit, root, asset)
        for ob in root.children_recursive:
            if not ob.name.startswith(asset):
                ob.name = f"{asset} {ob.name}"
    return build


def socket(kit, A, purpose, parent, loc, rot=(0, 0, 0)):
    s = kit.empty(f"{A} socket {purpose}", parent, loc, rot)
    s.empty_display_type = 'ARROWS'
    s.empty_display_size = 0.2
    return s


def flat_quad(kit, name, x0, x1, y0, y1, z, mat, parent, uv=(0, 0, 1, 1)):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    f = bm.faces.new([bm.verts.new(p) for p in ((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z))])
    for lp, c in zip(f.loops, ((uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3]))):
        lp[uvl].uv = c
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def catenary(a, b, sag, n):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, i / n) - Vector((0, 0, sag * 4 * (i / n) * (1 - i / n))) for i in range(n + 1)]


# ================================================================ Slot Brain (reel symbol)
def tex_slot_brain(rand):
    """32x16 wrap around the brain's long axis: bold meandering folds on pink, a darker groove along the top."""
    c = Canvas(32, 16, "#ff9fcf")
    for k in range(9):
        x, y = 1 + k * 3 + rand.randint(0, 1), rand.randint(2, 13)
        for _ in range(9):
            c.set(x, y, "#d63a86"); c.set(x + 1, y, "#e0559a")
            x += rand.choice((-1, 0, 1)); y = max(1, min(14, y + rand.choice((-1, 1))))
    c.speckle(rand, ["#ffd0e8"], 24, 0, 15)
    c.rect(15, 0, 16, 15, "#c02768")
    return c


def build_slot_brain(kit, root, A):
    """Cartoon brain in side profile facing -Y (the reel shows its front): domed top, cerebellum and stem at the back.
    Root at the center."""
    m = tex_mat(f"{A} brain", tex_slot_brain(kit.rand), 0.5, ext='REPEAT')
    xs = [-0.07, -0.06, -0.04, -0.01, 0.02, 0.045, 0.062, 0.07]
    zs = [-0.004, 0.0, 0.006, 0.01, 0.01, 0.004, -0.004, -0.008]
    hs = [0.016, 0.034, 0.046, 0.05, 0.05, 0.044, 0.032, 0.014]
    ds = [0.016, 0.03, 0.038, 0.042, 0.042, 0.038, 0.03, 0.014]
    tube(kit, f"{A} cerebrum", [(x, 0, z) for x, z in zip(xs, zs)], list(zip(hs, ds)), m, root, sides=8, front=(0, -1, 0))
    lowball(kit, f"{A} cerebellum", (0.04, 0.004, -0.036), (0.026, 0.028, 0.018), m, root)
    tube(kit, f"{A} stem", [(0.022, 0.004, -0.03), (0.026, 0.004, -0.05), (0.032, 0.004, -0.064)], [0.014, 0.012, 0.009],
         solid(kit, f"{A} stem", "#e0559a"), root, sides=6)
    tbox(kit, f"{A} shine", (-0.03, -0.04, 0.03), (0.018, 0.004, 0.008), solid(kit, f"{A} shine", WHITE, 1.2), root,
         rot=(0, -20, 0))


# ================================================================ Slot Machine
SM_W, SM_D, SM_H = 0.8, 0.6, 1.9
REELS = (-0.21, 0.0, 0.21)
REEL_Z = 1.25
WIN_W, WIN_H = 0.17, 0.22


def tex_slot_base():
    """Front of the base cabinet (32x48): candy stripes, gold trim, the payout chute label."""
    c = Canvas(32, 48, PINK)
    for y in range(48):
        for x in range(32):
            if (x + y) % 8 < 3:
                c.set(x, y, "#ff7dbb")
    c.rect(0, 0, 31, 2, "#d63a86"); c.rect(0, 45, 31, 47, YEL)
    c.rect(0, 0, 1, 47, YEL); c.rect(30, 0, 31, 47, YEL)
    c.rect(7, 22, 24, 32, WHITE); c.rect(8, 23, 23, 31, MINT)
    for i, col in enumerate((RED, YEL, BLUE)):
        disc(c, 11 + i * 5, 27, 2, col)
    return c


def tex_reel_panel():
    """Reel section front (64x48 over 0.76 x 0.52 m): gold frames around the three windows, stars."""
    c = Canvas(64, 48, "#ff8fc8")
    for y in range(48):
        for x in range(64):
            if (x // 4 + y // 4) % 2 == 0:
                c.set(x, y, "#ff9fd0")
    for rx in REELS:
        cx = int(round((rx + 0.38) / 0.76 * 64))
        x0, x1 = cx - 9, cx + 9
        y0, y1 = int((REEL_Z - WIN_H / 2 - 0.98) / 0.52 * 48) - 2, int((REEL_Z + WIN_H / 2 - 0.98) / 0.52 * 48) + 1
        c.rect(x0, y0, x1, y1, GOLD_S)
        c.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1, "#d9a01a")
    c.rect(0, 0, 63, 1, YEL); c.rect(0, 46, 63, 47, YEL)
    return c


GOLD_S = "#ffd23a"


def tex_marquee():
    c = Canvas(48, 12, INK)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        txt3_c(c, "SCOOP SLOTS", 24 + dx, 8 + dy, "#a02a6a")
    txt3_c(c, "SCOOP SLOTS", 24, 8, "#ffe14a")
    c.rect(0, 0, 47, 0, PINK); c.rect(0, 11, 47, 11, PINK)
    c.dots([(1, 2), (46, 2), (1, 9), (46, 9)], MINT)
    return c


def tex_whip_swirl():
    c = Canvas(32, 16, WHITE)
    for y in range(16):
        for x in range(32):
            if (x + 2 * y) % 8 < 2:
                c.set(x, y, "#e6dcf0")
    return c


def build_slot_machine(kit, root, A):
    R = kit.rand
    pink, yel, ink, steel = solid(kit, "slot pink", PINK), solid(kit, "slot gold", GOLD_S, shade="#d9a01a"), \
        solid(kit, "slot dark", INK, 0.08), solid(kit, "steel", STEEL, shade="#a9a2e0")
    mint = solid(kit, "slot mint", MINT)
    hw, hd = SM_W / 2, SM_D / 2
    # base cabinet with the striped front, payout chute and tray
    tbox(kit, f"{A} base", (0, 0, 0.47), (SM_W, SM_D, 0.94), tex_mat(f"{A} base front", tex_slot_base()), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.3, 0.1, 0.32, 0.12)})
    tbox(kit, f"{A} kick", (0, -hd + 0.02, 0.04), (SM_W + 0.02, 0.06, 0.08), ink, root)
    tbox(kit, f"{A} chute", (0, -hd - 0.004, 0.33), (0.36, 0.01, 0.14), ink, root)
    tbox(kit, f"{A} tray", (0, -hd - 0.05, 0.215), (0.42, 0.1, 0.03), steel, root)
    tbox(kit, f"{A} tray lip", (0, -hd - 0.1, 0.24), (0.42, 0.02, 0.05), yel, root)
    for i, (x, y) in enumerate(((-0.08, -0.33), (0.05, -0.36), (0.12, -0.32))):
        tube(kit, f"{A} coin {i}", [(x, y, 0.232), (x, y, 0.242)], 0.024, yel, root, sides=6)
    # control ledge: buttons and the coin slot
    tbox(kit, f"{A} ledge", (0, -hd - 0.05, 0.96), (SM_W, 0.16, 0.06), mint, root, rot=(-12, 0, 0))
    for i, (x, col) in enumerate(((-0.24, RED), (-0.12, YEL), (0.0, BLUE))):
        tube(kit, f"{A} button {i}", [(x, -hd - 0.06, 0.985), (x, -hd - 0.064, 1.0)], [0.03, 0.026],
             solid(kit, f"button {col}", col, 1.0), root, sides=6)
    tbox(kit, f"{A} coin plate", (0.22, -hd - 0.06, 0.99), (0.12, 0.08, 0.012), steel, root, rot=(-12, 0, 0))
    tbox(kit, f"{A} coin slot", (0.22, -hd - 0.061, 0.997), (0.05, 0.012, 0.006), ink, root, rot=(-12, 0, 0))
    # reel section: front panel with three recessed windows and dark backing
    fy = -hd + 0.04
    panel = tex_mat(f"{A} reel panel", tex_reel_panel())
    from h_truck import slab
    holes = [(x - WIN_W / 2, x + WIN_W / 2, REEL_Z - WIN_H / 2, REEL_Z + WIN_H / 2) for x in REELS]
    slab(kit, f"{A} reel panel", root, 'y', fy, 0.04, (-0.38, 0.38), (0.94, 1.5), holes, [panel, ink],
         lambda a, b: ((a + 0.38) / 0.76, (b - 0.98) / 0.52), lambda a, b: (0.5, 0.5), out_sign=-1)
    tbox(kit, f"{A} reel body", (0, fy + 0.065 + (hd - fy - 0.065) / 2, 1.22), (0.76, hd - fy - 0.065, 0.56), pink, root)
    tbox(kit, f"{A} reel backing", (0, fy + 0.06, REEL_Z), (0.68, 0.01, WIN_H + 0.08), ink, root)
    # chase lights around the reel section and the marquee
    bulbs = [solid(kit, "bulb " + c, c, 1.8) for c in (YEL, WHITE, "#ff8fc8")]
    k = 0
    for z in [0.98 + i * 0.085 for i in range(7)]:
        for sx in (1, -1):
            gem(kit, f"{A} bulb {k}", (sx * 0.355, fy - 0.035, z), 0.032, bulbs[k % 3], root); k += 1
    for x in [-0.27 + i * 0.09 for i in range(7)]:
        gem(kit, f"{A} bulb {k}", (x, fy - 0.035, 1.47), 0.032, bulbs[k % 3], root); k += 1
    # marquee
    tbox(kit, f"{A} marquee", (0, 0, 1.6), (SM_W, SM_D, 0.2), tex_mat(f"{A} marquee", tex_marquee(), 1.3), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.02, 0.02)})
    for z in (1.495, 1.705):
        tbox(kit, f"{A} marquee trim {z}", (0, 0, z), (SM_W + 0.03, SM_D + 0.03, 0.02), yel, root)
    # sundae top: dish, whipped cream dome, sprinkles and a cherry
    tube(kit, f"{A} dish", [(0, 0, 1.715), (0, 0, 1.74), (0, 0, 1.76)], [(0.36, 0.27), (0.4, 0.3), (0.41, 0.31)], pink, root,
         sides=10)
    zs = [1.75, 1.78, 1.8, 1.83, 1.85, 1.87, 1.885, 1.9]
    rs = [(0.37, 0.28), (0.36, 0.27), (0.28, 0.21), (0.27, 0.2), (0.18, 0.14), (0.17, 0.13), (0.08, 0.06), (0.01, 0.01)]
    tube(kit, f"{A} whipped cream", [(0.006 * (i % 2), 0, z) for i, z in enumerate(zs)], rs, tex_mat(f"{A} whip", tex_whip_swirl()),
         root, sides=10)
    for i, a in enumerate(range(0, 360, 45)):
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        tube(kit, f"{A} fudge drip {i}", [(ca * 0.33, sa * 0.25, 1.76), (ca * 0.41, sa * 0.31, 1.73),
                                          (ca * 0.41, sa * 0.31, 1.69 - 0.03 * (i % 2))], [0.026, 0.02, 0.014],
             solid(kit, "fudge", CHOC, 0.28, shade="#4e2812"), root, sides=4, bulge=(0, 0.01))
    spr = [solid(kit, f"sprinkle {c}", c, 0.7) for c in (BLUE, YEL, MINT, PINK, PURP)]
    for i in range(14):
        a = 2 * math.pi * i / 14 + R.uniform(-0.2, 0.2)
        t = R.uniform(0.15, 0.85)
        z = 1.76 + t * 0.12
        rx, ry = 0.36 * (1 - t * 0.75), 0.27 * (1 - t * 0.75)
        tbox(kit, f"{A} sprinkle {i}", (0, 0, 0), (0.012, 0.035, 0.012), spr[i % 5], root,
             loc=(math.cos(a) * rx, math.sin(a) * ry, z), rot=(R.uniform(-40, 40), 0, R.uniform(0, 180)))
    lowball(kit, f"{A} cherry", (0, 0, 1.935), (0.05, 0.05, 0.048), solid(kit, "cherry", RED, 0.7), root)
    tube(kit, f"{A} cherry stem", [(0, 0, 1.975), (0.02, 0.01, 2.02), (0.05, 0.02, 2.04)], 0.006,
         solid(kit, "cherry stem", "#3fae4a"), root, sides=4, caps=(False, False))
    # lever on the +X side: hub, arm and a big cherry knob; pulls forward/down about X
    tube(kit, f"{A} lever housing", [(hw, 0.0, 1.15), (hw + 0.05, 0.0, 1.15)], 0.07, yel, root, sides=8, front=(0, 0, 1))
    lever = kit.empty(f"{A} lever", root, (hw + 0.06, 0.0, 1.15))
    tube(kit, f"{A} lever hub", [(-0.01, 0, 0), (0.035, 0, 0)], 0.04, steel, lever, sides=8, front=(0, 0, 1))
    tube(kit, f"{A} lever arm", [(0.02, 0, 0), (0.02, 0, 0.38)], [0.016, 0.013], steel, lever, sides=6)
    lowball(kit, f"{A} lever knob", (0.02, 0, 0.42), (0.055, 0.055, 0.053), solid(kit, "cherry", RED, 0.7), lever)
    tbox(kit, f"{A} lever knob shine", (0.0, -0.04, 0.44), (0.02, 0.01, 0.014), solid(kit, "shine", WHITE, 1.2), lever)
    # sockets
    for i, x in enumerate(REELS):
        socket(kit, A, f"reel {i + 1}", root, (x, fy + 0.03, REEL_Z))
    socket(kit, A, "payout", root, (0, -hd - 0.05, 0.235))
    socket(kit, A, "use point", root, (0, -0.8, 0))


# ================================================================ Shopkeeper Kevin
KSKIN = SKIN; ZSKIN = "#a8c49a"; ZSKIN_D = "#86a678"; ZSKIN_L = "#c2d8b2"; KHAIR = "#4a3326"
TROUSER = "#3a2f5a"; LIP = "#c8506e"; BLUSH = "#ff8fae"


def tex_kevin_head(rand):
    """64x64 around the cranium (front at x 32; x < 32 = his right, the zombie side). Row 0 = upper lip line."""
    c = Canvas(64, 64, KSKIN)
    for y in range(64):
        edge = 30 + (y * 7 % 5) - 2
        for x in range(0, edge):
            c.set(x, y, ZSKIN)
    c.speckle(rand, [ZSKIN_D, ZSKIN_L], 120, 0, 63)
    for x in range(30, 64):   # restore the human side, then a few green patches creeping over
        for y in range(64):
            if x >= 30 + (y * 7 % 5) - 2:
                c.set(x, y, KSKIN)
    for cx, cy, r in ((44, 40, 3), (52, 18, 2), (40, 8, 2)):
        disc(c, cx, cy, r, ZSKIN)
        c.set(cx, cy, ZSKIN_D)
    c.speckle(rand, ["#f2b08e"], 30, 0, 40)
    # a few stitches where the halves meet: forehead and jaw line only
    for y in list(range(31, 41, 3)) + [7, 10]:
        x = 30 + (y * 7 % 5) - 2
        c.rect(x - 1, y, x + 1, y, "#3f5a36"); c.set(x, y + 1, "#3f5a36")
    # hair at the back and sides (the paper hat covers the top)
    c.rect(0, 46, 63, 63, KHAIR)
    for x in range(64):
        if x < 16 or x > 48:
            c.rect(x, 20 + (x * 5) % 4, x, 46, KHAIR)
    c.rect(16, 38, 18, 46, KHAIR); c.rect(46, 38, 48, 46, KHAIR)
    c.dots([(22, 45), (26, 44), (30, 45), (35, 44), (40, 45)], KHAIR)
    # human ear (+X) and the stitched seam where the borrowed ear sits (-X)
    c.rect(47, 22, 48, 30, "#f2a37f")
    for y in (21, 24, 27, 30):
        c.rect(14, y, 18, y, INK)
    # human eye: big, friendly, raised brow
    c.rect(35, 30, 38, 34, WHITE); c.rect(36, 30, 37, 33, INK); c.set(37, 33, WHITE)
    c.rect(34, 37, 38, 37, KHAIR); c.set(39, 36, KHAIR)
    # zombie eye: droopy, half-lidded, yellow sclera, little red pupil, dark bag under it
    c.rect(24, 27, 29, 32, ZSKIN_D)
    c.rect(25, 28, 28, 30, "#f4f0b0"); c.set(26, 28, RED); c.set(27, 28, INK)
    c.rect(24, 31, 29, 32, "#6f8f62"); c.set(23, 30, "#6f8f62")
    c.rect(25, 26, 28, 26, "#6f8f62")
    c.rect(24, 35, 28, 35, KHAIR)
    # nose and rosy cheeks on both sides
    c.dots([(31, 21), (32, 21), (32, 22), (33, 21)], "#e8967a")
    c.rect(37, 13, 42, 16, BLUSH); c.rect(38, 17, 41, 17, BLUSH)
    c.rect(21, 13, 26, 16, "#ff9fb8"); c.rect(22, 17, 25, 17, "#ff9fb8")
    # big grin: dark mouth with the top teeth (one missing) and upturned corners; the jaw carries the lower lip
    c.rect(25, 0, 39, 3, "#2a0f2e")
    for x in range(26, 39):
        c.rect(x, 2, x, 3, WHITE if x != 30 else "#2a0f2e")
    c.rect(25, 4, 39, 4, LIP)
    c.dots([(24, 3), (23, 4), (22, 5), (40, 3), (41, 4), (42, 5)], "#2a0f2e")
    return c


def tex_kevin_jaw(rand):
    """32x16 around the jaw: lower teeth and lip at the top front, chin below. x < 16 = zombie side."""
    c = Canvas(32, 16, KSKIN)
    for y in range(16):
        c.rect(0, y, 14 + (y % 3), y, ZSKIN)
    c.speckle(rand, [ZSKIN_D], 16, 0, 15)
    c.rect(11, 13, 21, 15, "#2a0f2e")
    for x in range(12, 21):
        c.set(x, 14, WHITE if x % 3 else "#e8e0c8")
    c.rect(11, 12, 21, 12, LIP); c.dots([(10, 13), (22, 13)], LIP)
    c.rect(14, 7, 18, 7, "#f2b08e")
    return c


def tex_kevin_torso(rand):
    """64x64: trousers at the bottom, white shirt, pink-and-white striped apron bib with straps, collar at the top."""
    c = Canvas(64, 64, "#f6f0fa")
    for x in range(0, 64, 6):
        c.rect(x, 9, x, 63, "#e6ddf0")
    c.rect(0, 0, 63, 8, TROUSER)
    c.rect(0, 9, 63, 11, PINK)
    c.rect(56, 5, 58, 10, PINK); c.rect(59, 3, 60, 8, PINK)
    for y in range(12, 48):
        half = 10 if y < 38 else 8
        for x in range(32 - half, 32 + half):
            c.set(x, y, PINK if ((x - 32) // 2) % 2 == 0 else WHITE)
        c.set(32 - half - 1, y, "#d63a86"); c.set(32 + half, y, "#d63a86")
    c.rect(22, 47, 41, 48, "#d63a86")
    c.rect(24, 48, 25, 63, PINK); c.rect(38, 48, 39, 63, PINK)
    for i in range(46):
        y = 63 - i
        c.set(-10 + i // 2 + 64, y, PINK); c.set(10 - i // 2, y, PINK)
    c.rect(27, 58, 36, 63, "#f6f0fa"); c.rect(29, 60, 34, 63, "#e8dcd0")   # collar
    c.rect(28, 18, 35, 24, WHITE); c.rect(28, 18, 35, 18, "#d63a86")        # pocket
    c.speckle(rand, ["#e6ddf0"], 30, 12, 57)
    return c


def tex_kevin_apron():
    c = Canvas(32, 32, WHITE)
    for x in range(32):
        if (x // 2) % 2 == 0:
            c.rect(x, 0, x, 31, PINK)
    c.rect(0, 29, 31, 31, "#d63a86"); c.rect(0, 0, 31, 1, "#d63a86")
    c.rect(9, 10, 22, 20, WHITE); c.rect(9, 20, 22, 20, "#d63a86")
    cone_icon(c, 15, 11, 6, MINT)
    return c


def tex_kevin_arm(zombie):
    c = Canvas(16, 32, ZSKIN if zombie else KSKIN)
    if zombie:
        c.speckle(random.Random(11), [ZSKIN_D, ZSKIN_L], 30)
        c.rect(4, 14, 9, 14, INK); c.dots([(5, 13), (5, 15), (8, 13), (8, 15)], INK)
    c.rect(0, 0, 15, 15, "#f6f0fa")
    c.rect(0, 13, 15, 15, PINK); c.rect(0, 12, 15, 12, WHITE)
    return c


def tex_kevin_leg():
    c = Canvas(16, 32, TROUSER)
    for x in (3, 11):
        c.rect(x, 0, x, 31, "#4a3f70")
    c.rect(0, 0, 15, 1, "#2a2244")
    return c


def tex_saddle_shoe():
    c = Canvas(16, 16, WHITE)
    c.rect(4, 0, 11, 15, INK)
    for y in (5, 7, 9):
        c.rect(7, y, 8, y, WHITE)
    c.rect(0, 0, 15, 1, "#d63a86")
    return c


def tex_name_tag():
    c = Canvas(24, 10, YEL)
    c.rect(0, 0, 23, 0, "#d9a01a"); c.rect(0, 9, 23, 9, "#d9a01a")
    txt3_c(c, "KEVIN", 12, 7, PINK)
    return c


def tex_paper_hat():
    c = Canvas(16, 16, WHITE)
    c.rect(0, 2, 15, 4, PINK); c.rect(0, 5, 15, 5, MINT)
    c.rect(0, 0, 15, 0, "#e8dcd0")
    cone_icon(c, 8, 7, 5, PINK)
    return c


def arm_tube(kit, piv, name, L, t_arm, hand_mat, r0=0.064):
    """Arm along the pivot's local -Z: sleeve to the elbow, forearm, hand."""
    tube(kit, f"{name}", [(0, 0, 0.02), (0, 0, -0.12), (0, 0, -L * 0.55), (0, 0, -(L - 0.06))],
         [r0, r0 * 0.9, r0 * 0.78, r0 * 0.6], t_arm, piv, sides=6, front=(0, 1, 0), bulge=(0.03, 0))
    tube(kit, f"{name} hand", [(0, 0, -(L - 0.07)), (0, 0, -(L - 0.02)), (0, 0, -(L + 0.05))],
         [(0.044, 0.032), (0.05, 0.036), (0.038, 0.028)], hand_mat, piv, sides=6, front=(0, 1, 0), bulge=(0, 0.02))


def build_kevin(kit, root, A):
    R = kit.rand
    t_head = tex_mat("kevin head", tex_kevin_head(R))
    t_jaw = tex_mat("kevin jaw", tex_kevin_jaw(R))
    t_torso = tex_mat("kevin torso", tex_kevin_torso(R))
    t_apron = tex_mat("kevin apron", tex_kevin_apron())
    t_leg = tex_mat("kevin leg", tex_kevin_leg())
    t_shoe = tex_mat("saddle shoe", tex_saddle_shoe())
    skin, zskin = solid(kit, "kevin skin", KSKIN), solid(kit, "kevin zombie skin", ZSKIN, shade=ZSKIN_D)

    # legs (hip pivots)
    for sx, nm in ((1, "L"), (-1, "R")):
        leg = kit.empty(f"leg {nm}", root, (sx * 0.088, 0.0, 0.9), (0, sx * -3, sx * 4))
        tube(kit, f"trouser {nm}", [(0, 0, 0.04), (0, 0, -0.2), (0, -0.014, -0.43), (0, 0, -0.62), (0, 0, -0.82)],
             [(0.085, 0.09), 0.072, 0.058, 0.052, 0.046], t_leg, leg, sides=6, front=(0, 1, 0))
        tube(kit, f"shoe {nm}", [(0, 0.05, -0.86), (0, -0.03, -0.855), (0, -0.13, -0.87)],
             [(0.05, 0.044), (0.056, 0.05), (0.044, 0.03)], t_shoe, leg, sides=6, front=(0, 0, 1), bulge=(0.015, 0.03))

    # slightly hunched torso, apron skirt, bowtie and the name tag
    pts = [(0, 0.0, 0.84), (0, 0.0, 0.95), (0, -0.01, 1.09), (0, -0.03, 1.23), (0, -0.055, 1.35), (0, -0.07, 1.43)]
    rad = [(0.158, 0.112), (0.165, 0.12), (0.155, 0.118), (0.168, 0.118), (0.185, 0.11), (0.085, 0.066)]
    tube(kit, "torso", pts, rad, t_torso, root, sides=10)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    grid = []
    for j, (z, rx, ry) in enumerate(((0.97, 0.17, 0.125), (0.76, 0.2, 0.15), (0.54, 0.215, 0.165))):
        grid.append([bm.verts.new((math.sin(a) * rx, -math.cos(a) * ry - 0.006, z))
                     for a in (math.radians(-64 + 128 * i / 4) for i in range(5))])
    for j in range(2):
        for i in range(4):
            fc = bm.faces.new((grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]))
            for lp, uv in zip(fc.loops, ((i / 4, 1 - (j + 1) / 2), ((i + 1) / 4, 1 - (j + 1) / 2), ((i + 1) / 4, 1 - j / 2),
                                         (i / 4, 1 - j / 2))):
                lp[uvl].uv = (min(0.995, max(0.005, uv[0])), min(0.995, max(0.005, uv[1])))
    kit.mesh_from_bmesh("apron skirt", bm, t_apron, root)
    bow = solid(kit, "bowtie", RED, 0.5, shade=DRED)
    for sx in (1, -1):
        tbox(kit, f"bowtie wing {sx}", (sx * 0.035, -0.135, 1.405), (0.06, 0.02, 0.05), bow, root, rot=(-20, 0, 0),
             taper=(1.0, 1.0))
    tbox(kit, "bowtie knot", (0, -0.142, 1.405), (0.022, 0.024, 0.026), solid(kit, "bowtie knot", "#ff6a7e"), root, rot=(-20, 0, 0))
    tbox(kit, "name tag", (0.075, -0.142, 1.255), (0.075, 0.008, 0.032), tex_mat("name tag", tex_name_tag(), 0.5), root,
         rot=(-12, 0, 6), uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.04, 0.08)})
    tube(kit, "neck", [(0, -0.068, 1.4), (0, -0.075, 1.52)], 0.046, zskin, root, sides=6)

    # head on the neck, tilted forward and a little to the side; jaw on its own hinge
    head = kit.empty("head", root, (0, -0.08, 1.47), (6, -5, 0))
    hz = [0.075, 0.11, 0.17, 0.23, 0.275, 0.305]
    hr = [(0.088, 0.09), (0.1, 0.104), (0.106, 0.112), (0.1, 0.106), (0.072, 0.076), (0.03, 0.034)]
    tube(kit, "cranium", [(0, -0.008 if z < 0.15 else 0.0, z) for z in hz], hr, t_head, head, sides=10, bulge=(0.0, 0.01))
    jaw = kit.empty("jaw", head, (0, 0.015, 0.085), (0, 0, 0))
    tube(kit, "chin", [(0, -0.03, -0.072), (0, -0.03, -0.045), (0, -0.024, -0.012), (0, -0.02, 0.0)],
         [(0.056, 0.05), (0.08, 0.075), (0.09, 0.088), (0.085, 0.085)], t_jaw, jaw, sides=10, bulge=(0.008, 0))
    ear = kit.empty("stitched ear", head, (-0.104, 0.006, 0.165), (0, 0, -12))
    lowball(kit, "borrowed ear", (-0.01, 0, 0), (0.016, 0.03, 0.042), skin, ear)
    tbox(kit, "ear stitch", (0.004, 0, 0), (0.012, 0.05, 0.004), solid(kit, "stitch", INK, 0.1), ear)
    hat = kit.empty("paper hat", head, (0, 0.0, 0.25), (0, 9, 0))
    tbox(kit, "paper hat", (0, 0, 0.035), (0.19, 0.29, 0.085), tex_mat("paper hat", tex_paper_hat()), hat, taper=(0.3, 0.84),
         uv={'pz': (0.0, 0.9, 1.0, 1.0)})
    pencil = kit.empty("pencil", head, (0.1, 0.03, 0.2), (-70, 0, 8))
    tube(kit, "pencil", [(0, 0, -0.07), (0, 0, 0.06)], 0.007, solid(kit, "pencil", YEL), pencil, sides=6)
    tube(kit, "pencil tip", [(0, 0, -0.07), (0, 0, -0.09)], [0.007, 0.001], solid(kit, "pencil wood", "#ffcf9a"), pencil,
         sides=6)
    tube(kit, "pencil eraser", [(0, 0, 0.06), (0, 0, 0.075)], 0.0075, solid(kit, "eraser", PINK), pencil, sides=6)

    # arms: left (human) leans on the counter, right (zombie) waves from the elbow
    t_arm_h, t_arm_z = tex_mat("kevin arm", tex_kevin_arm(False)), tex_mat("kevin zombie arm", tex_kevin_arm(True))
    armL = kit.empty("arm L", root, (0.2, -0.05, 1.37))
    aim(armL, Vector((0.26, -0.55, 1.14)) - Vector((0.2, -0.05, 1.37)))
    arm_tube(kit, armL, "sleeve L", 0.6, t_arm_h, skin)
    armR = kit.empty("arm R", root, (-0.2, -0.05, 1.37))
    aim(armR, Vector((-0.42, -0.14, 1.12)) - Vector((-0.2, -0.05, 1.37)))
    tube(kit, "sleeve R", [(0, 0, 0.02), (0, 0, -0.12), (0, 0, -0.3)], [0.064, 0.058, 0.052], t_arm_h, armR, sides=6,
         front=(0, 1, 0), bulge=(0.03, 0), v=(0.0, 0.5))
    fore = kit.empty("forearm R", armR, (0, 0, -0.3))
    bpy.context.view_layer.update()
    d = (root.matrix_world.inverted() @ armR.matrix_world).to_3x3().inverted() @ Vector((-0.22, -0.25, 1.0))
    fore.rotation_euler = d.normalized().to_track_quat('-Z', 'Y').to_euler()
    tube(kit, "forearm R", [(0, 0, 0.02), (0, 0, -0.14), (0, 0, -0.25)], [0.05, 0.046, 0.038], tex_mat("kevin zombie forearm",
                                                                                                         tex_kevin_arm(True)),
         fore, sides=6, front=(0, 1, 0), v=(0.5, 1.0))
    tube(kit, "hand R", [(0, 0, -0.25), (0, 0, -0.3), (0, 0, -0.36)], [(0.044, 0.026), (0.052, 0.028), (0.04, 0.022)], zskin,
         fore, sides=6, front=(0, 1, 0), bulge=(0, 0.015))
    for i, a in enumerate((-30, -10, 10, 30)):
        tube(kit, f"finger R {i}", [(math.sin(math.radians(a)) * 0.03, 0, -0.355), (math.sin(math.radians(a)) * 0.05, 0, -0.41)],
             [0.011, 0.008], zskin, fore, sides=4)
    tube(kit, "thumb R", [(0.04, -0.01, -0.3), (0.07, -0.02, -0.34)], [0.012, 0.008], zskin, fore, sides=4)
    socket(kit, A, "hand R", fore, (0, 0, -0.33))
    socket(kit, A, "hand L", armL, (0, 0, -0.6))


# ================================================================ Kevin's Stall
STALL_PEDESTALS = (-4.0, -2.4, -0.8)
PED_Y, SUP_Y = -1.2, 0.6
PED_TOP, SUP_TOP = 0.9, 0.35
KEVIN_SPOT, TALK_SPOT, SLOTS_SPOT = (2.6, 1.6), (2.6, -0.4), (4.2, -1.0)
BOOTH = (1.0, 4.4, 0.85, 2.35)        # posts: x0, x1, y_front, y_back
COUNTER = (1.15, 4.1, 0.95, 1.4, 1.05)  # x0, x1, y0, y1, height


def tex_mat_checker():
    c = Canvas(16, 16, "#e8dcff")
    c.rect(0, 0, 7, 7, "#b48cff"); c.rect(8, 8, 15, 15, "#b48cff")
    c.rect(0, 0, 15, 0, "#9a74e6")
    return c


def tex_kevins_sign(rand):
    c = Canvas(80, 24, INK)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)):
        txt3_c(c, "KEVIN'S", 40 + dx, 19 + dy, "#a02a6a", 2)
    txt3_c(c, "KEVIN'S", 40, 19, "#ffb3d9", 2)
    txt3_c(c, "DEPOT SHOP", 40, 6, MINT)
    for cx in (6, 73):
        cone_icon(c, cx, 3, 9, ZG)
    c.rect(0, 0, 79, 0, YEL); c.rect(0, 23, 79, 23, YEL); c.rect(0, 0, 0, 23, YEL); c.rect(79, 0, 79, 23, YEL)
    return c


def tex_counter_front():
    c = Canvas(64, 16, WHITE)
    for x in range(64):
        if (x // 4) % 2 == 0:
            c.rect(x, 0, x, 15, PINK)
    c.rect(0, 0, 63, 1, "#d63a86"); c.rect(0, 14, 63, 15, MINT)
    c.rect(20, 4, 43, 11, INK)
    txt3_c(c, "OPEN 24-7", 32, 10, YEL)
    return c


def tex_crate(word):
    c = Canvas(32, 32, "#e8a85a")
    for y in (0, 10, 21, 31):
        c.rect(0, y, 31, y, "#a8642a")
    c.rect(0, 0, 1, 31, "#a8642a"); c.rect(30, 0, 31, 31, "#a8642a")
    for k in range(28):
        c.set(2 + k, 2 + k, "#c98a46"); c.set(29 - k, 2 + k, "#c98a46")
    c.rect(4, 12, 27, 19, "#f2c88a")
    txt3_c(c, word, 16, 18, "#7a3a1c")
    return c


def tex_pallet():
    c = Canvas(32, 16, "#d99446")
    for y in (4, 5, 10, 11):
        c.rect(0, y, 31, y, "#5a3418")
    for x in (0, 15, 16, 31):
        c.rect(x, 0, x, 15, "#a8642a")
    c.rect(0, 15, 31, 15, "#f2bc72")
    return c


def tex_ped(base, dark, light):
    c = Canvas(16, 32, base)
    for y in range(32):
        for x in range(16):
            if (x + y) % 8 < 2:
                c.set(x, y, light)
    c.rect(0, 0, 15, 1, dark); c.rect(0, 30, 15, 31, dark)
    c.rect(5, 18, 10, 23, WHITE); c.rect(6, 19, 9, 22, YEL)
    return c


def tex_shelf_back():
    c = Canvas(32, 32, "#5b3fa0")
    for y in range(0, 32, 4):
        c.rect(0, y, 31, y, "#4a3290")
    return c


def build_stall(kit, root, A):
    R = kit.rand
    pink, mint, yel, ink, white = solid(kit, "stall pink", PINK), solid(kit, "stall mint", MINT), solid(kit, "stall yellow", YEL), \
        solid(kit, "stall dark", INK, 0.1), solid(kit, "stall white", WHITE)
    wood = solid(kit, "stall wood", "#e8a85a", shade="#c98a46")
    pole = tex_mat("candy post", tex_candy(PINK, WHITE), ext='REPEAT')
    # checker mat over the whole footprint (single quad: nothing to trip over)
    flat_quad(kit, "floor mat", -5.0, 5.0, -2.5, 2.5, 0.006, tex_mat("stall floor", tex_mat_checker(), 0.28, ext='REPEAT'), root,
              uv=(0, 0, 10, 5))
    for nm, y0, y1, x0, x1 in (("front", -2.5, -2.42, -5, 5), ("back", 2.42, 2.5, -5, 5), ("left", -2.5, 2.5, -5, -4.92),
                               ("right", -2.5, 2.5, 4.92, 5)):
        tbox(kit, f"mat edge {nm}", ((x0 + x1) / 2, (y0 + y1) / 2, 0.012), (x1 - x0, y1 - y0, 0.024), pink, root)

    # weapon pedestals (pink/mint alternating), small tops
    for i, x in enumerate(STALL_PEDESTALS):
        base, dark, light = (PINK, "#d63a86", "#ff8fc8") if i % 2 == 0 else (MINT, "#1fbf95", "#a6fbe6")
        t = tex_mat(f"pedestal {i}", tex_ped(base, dark, light), ext='REPEAT')
        trim = solid(kit, f"pedestal trim {i}", dark)
        tbox(kit, f"pedestal {i + 1} plinth", (x, PED_Y, 0.07), (0.46, 0.46, 0.14), trim, root, taper=(0.8, 0.8))
        tbox(kit, f"pedestal {i + 1} column", (x, PED_Y, 0.5), (0.22, 0.22, 0.74), t, root, uv={'all': (0, 0, 1, 1)})
        tbox(kit, f"pedestal {i + 1} top", (x, PED_Y, PED_TOP - 0.04), (0.28, 0.28, 0.08), trim, root, taper=(1.08, 1.08))
        tbox(kit, f"pedestal {i + 1} pad", (x, PED_Y, PED_TOP - 0.004), (0.24, 0.24, 0.008), white, root)
        socket(kit, A, f"weapon {i + 1}", root, (x, PED_Y, PED_TOP))
    # supply pallets
    t_pal = tex_mat("pallet", tex_pallet())
    for i, x in enumerate(STALL_PEDESTALS):
        tbox(kit, f"supply stand {i + 1}", (x, SUP_Y, (SUP_TOP - 0.03) / 2), (0.66, 0.54, SUP_TOP - 0.03), t_pal, root,
             uv={'pz': (0.1, 0.9, 0.2, 1.0)})
        tbox(kit, f"supply stand {i + 1} top", (x, SUP_Y, SUP_TOP - 0.015), (0.7, 0.58, 0.03), wood, root)
        socket(kit, A, f"supply {i + 1}", root, (x, SUP_Y, SUP_TOP))

    # booth: counter, awning on candy posts, back wall with shelves of pints
    x0, x1, yf, yb = BOOTH
    cx0, cx1, cy0, cy1, ch = COUNTER
    tbox(kit, "counter", ((cx0 + cx1) / 2, (cy0 + cy1) / 2, ch / 2 - 0.02), (cx1 - cx0, cy1 - cy0, ch - 0.04),
         tex_mat("counter front", tex_counter_front()), root, uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.2, 0.02, 0.3)})
    tbox(kit, "counter top", ((cx0 + cx1) / 2, (cy0 + cy1) / 2 - 0.03, ch - 0.02), (cx1 - cx0 + 0.1, cy1 - cy0 + 0.14, 0.04),
         mint, root)
    tbox(kit, "counter kick", ((cx0 + cx1) / 2, cy0 - 0.005, 0.04), (cx1 - cx0, 0.03, 0.08), ink, root)
    # register, tip jar and a service bell on the counter
    reg = kit.empty("register", root, (3.55, 1.22, ch))
    tbox(kit, "register body", (0, 0, 0.09), (0.36, 0.3, 0.18), pink, reg, taper=(1.0, 0.7))
    tbox(kit, "register screen", (0, 0.05, 0.24), (0.22, 0.04, 0.1), tex_mat("register screen", tex_label_c("$$$", ZG, INK)), reg,
         uv={'ny': (0, 0, 1, 1), 'all': (0, 0, 0.05, 0.05)})
    tbox(kit, "register drawer", (0, -0.16, 0.04), (0.32, 0.04, 0.06), yel, reg)
    tube(kit, "bell base", [(1.75, 1.15, ch), (1.75, 1.15, ch + 0.02)], 0.06, ink, root, sides=8)
    tube(kit, "bell dome", [(1.75, 1.15, ch + 0.02), (1.75, 1.15, ch + 0.06), (1.75, 1.15, ch + 0.08)], [0.055, 0.04, 0.01],
         solid(kit, "bell gold", "#ffd23a", shade="#d9a01a"), root, sides=8)
    tube(kit, "tip jar", [(2.05, 1.2, ch), (2.05, 1.2, ch + 0.16)], [0.06, 0.065], solid(kit, "jar glass", "#cfe8ff", 0.5), root,
         sides=8, caps=(True, False))
    for k in range(3):
        tube(kit, f"tip coin {k}", [(2.03 + k * 0.02, 1.2, ch + 0.02 + k * 0.025), (2.03 + k * 0.02, 1.2, ch + 0.035 + k * 0.025)],
             0.03, yel, root, sides=6)
    for x in (x0, x1):
        for y in (yf, yb):
            tube(kit, f"post {x:.1f} {y:.1f}", [(x, y, 0), (x, y, 2.55 if y == yf else 2.95)], 0.05, pole, root, sides=6,
                 v=(0.0, 5.0))
    # awning slopes from the back (2.95) down to the front (2.55), scallops along the front edge
    aw_len = math.hypot(yb - yf + 0.5, 0.4)
    tilt = math.degrees(math.atan2(0.4, yb - yf + 0.5))
    tbox(kit, "awning", ((x0 + x1) / 2, (yf + yb) / 2 - 0.25, 2.77), (x1 - x0 + 0.4, aw_len, 0.05),
         tex_mat("awning", tex_awning(), ext='REPEAT'), root, rot=(tilt, 0, 0), uv={'all': (0, 0, 9, 1)})
    n = 10
    for i in range(n):
        x = x0 - 0.2 + (i + 0.5) * (x1 - x0 + 0.4) / n
        lowball(kit, f"awning scallop {i}", (x, yf - 0.5, 2.54), (0.17, 0.035, 0.1), pink if i % 2 else white, root,
                smooth=False)
    tbox(kit, "back wall", ((x0 + x1) / 2, yb + 0.04, 1.4), (x1 - x0, 0.06, 2.8), tex_mat("shelf back", tex_shelf_back(), 0.25),
         root, uv={'all': (0, 0, 3, 3)})
    for lv, z in enumerate((1.25, 1.75)):
        tbox(kit, f"shelf {lv}", ((x0 + x1) / 2, yb - 0.12, z), (x1 - x0 - 0.2, 0.26, 0.04), white, root)
        for k in range(7):
            col = (MINT, PINK, YEL, BLUE, ORNG, PURP, PINK)[(k + lv * 3) % 7]
            x = x0 + 0.35 + k * (x1 - x0 - 0.7) / 6
            tube(kit, f"shelf pint {lv} {k}", [(x, yb - 0.12, z + 0.02), (x, yb - 0.12, z + 0.2)], [0.07, 0.08],
                 tex_mat(f"shelf pint {col}", tex_pint(col)), root, sides=6)
    # KEVIN'S sign standing on the awning, framed by bulbs
    sz = 3.35
    tbox(kit, "sign board", ((x0 + x1) / 2, yf + 0.55, sz), (3.0, 0.1, 0.9), tex_mat("kevins sign", tex_kevins_sign(R), 1.5), root,
         uv={'ny': (0, 0, 1, 1), 'all': (0.0, 0.0, 0.01, 0.01)})
    tbox(kit, "sign frame", ((x0 + x1) / 2, yf + 0.57, sz), (3.12, 0.08, 1.02), pink, root)
    for x in (x0 + 0.5, x1 - 0.5):
        tbox(kit, f"sign leg {x:.1f}", (x, yf + 0.6, 2.75), (0.08, 0.08, 0.6), ink, root)
    bulbs = [solid(kit, "bulb " + c, c, 2.0) for c in (YEL, WHITE, MINT, "#ff8fc8")]
    k = 0
    for i in range(12):
        for z in (sz - 0.5, sz + 0.5):
            gem(kit, f"sign bulb {k}", ((x0 + x1) / 2 - 1.43 + i * 2.86 / 11, yf + 0.5, z), 0.035, bulbs[k % 4], root); k += 1
    for z in (sz - 0.25, sz, sz + 0.25):
        for x in ((x0 + x1) / 2 - 1.55, (x0 + x1) / 2 + 1.55):
            gem(kit, f"sign bulb {k}", (x, yf + 0.5, z), 0.035, bulbs[k % 4], root); k += 1

    # string lights: booth posts to two poles at the left corners and a pole on the right
    pole_mat = solid(kit, "light pole", "#5b5fc0", shade="#474aa0")
    poles = {"A": (-4.85, -2.3), "B": (-4.85, 2.3), "C": (4.85, -2.3)}
    for nm, (x, y) in poles.items():
        tube(kit, f"light pole {nm}", [(x, y, 0), (x, y, 2.75)], [0.05, 0.04], pole_mat, root, sides=6)
        tbox(kit, f"light pole {nm} foot", (x, y, 0.04), (0.24, 0.24, 0.08), ink, root)
    wire = solid(kit, "wire", "#2a2238", 0.1)
    runs = [((x0, yf, 2.5), (-4.85, -2.3, 2.7), 0.35), ((x0, yb, 2.75), (-4.85, 2.3, 2.7), 0.3),
            ((-4.85, -2.3, 2.7), (-4.85, 2.3, 2.7), 0.4), ((x1, yf, 2.5), (4.85, -2.3, 2.7), 0.25)]
    k = 0
    for j, (a, b, sag) in enumerate(runs):
        pts = catenary(a, b, sag, 10)
        tube(kit, f"light wire {j}", [tuple(p) for p in pts], 0.01, wire, root, sides=3, caps=(False, False), smooth=False)
        nb = max(4, int((Vector(b) - Vector(a)).length / 0.6))
        for i in range(1, nb):
            p = catenary(a, b, sag, nb)[i]
            gem(kit, f"string bulb {k}", tuple(p - Vector((0, 0, 0.05))), 0.045, bulbs[k % 4], root); k += 1

    # supplies stacked at the back
    t_crate = tex_mat("supply crate", tex_crate("SUPPLY"))
    t_crate2 = tex_mat("fragile crate", tex_crate("SCOOPS"))
    stacks = [(-4.3, 1.85, 0.0, 0.55, 5, t_crate), (-4.3, 1.85, 0.55, 0.5, -8, t_crate2), (-3.55, 1.95, 0.0, 0.55, 10, t_crate2),
              (-0.4, 1.95, 0.0, 0.55, -6, t_crate), (-0.4, 1.95, 0.55, 0.45, 12, t_crate), (4.0, 2.0, 0.0, 0.5, 4, t_crate)]
    for i, (x, y, z, s, rz, t) in enumerate(stacks):
        tbox(kit, f"crate {i}", (x, y, z + s / 2), (s, s, s), t, root, rot=(0, 0, rz))
    for nm, fn, loc, rz in (("Sugar Sack", build_sugar_sack, (-2.6, 1.95, 0), -14), ("Milk Crate", build_milk_crate, (-1.6, 1.9, 0), 8),
("Cocoa Bag", build_cocoa_bag, (-3.4, 1.95, 0.55), 20)):
        sub = kit.empty(f"stack {nm} {loc[2]}", root, loc, (0, 0, rz))
        item_run(kit, sub, nm, fn)
        for ob in list(sub.children_recursive):   # set dressing: drop the item's own hand sockets
            if " socket " in ob.name:
                bpy.data.objects.remove(ob)

    socket(kit, A, "kevin", root, (KEVIN_SPOT[0], KEVIN_SPOT[1], 0))
    socket(kit, A, "talk", root, (TALK_SPOT[0], TALK_SPOT[1], 0), (0, 0, 180))
    socket(kit, A, "slots", root, (SLOTS_SPOT[0], SLOTS_SPOT[1], 0))


def tex_label_c(s, fg, bg):
    c = Canvas(text_w(s) + 4, 9, bg)
    txt3(c, s, 2, 7, fg)
    return c


ASSETS = [
    ("Kevin's Stall", prefixed("Kevin's Stall", build_stall)),
    ("Slot Machine", prefixed("Slot Machine", build_slot_machine)),
    ("Slot Brain", prefixed("Slot Brain", build_slot_brain)),
    ("Shopkeeper Kevin", prefixed("Shopkeeper Kevin", build_kevin)),
]
SPACING = 12


def build_shop_scene(kit, root):
    st = kit.empty("scene stall", root)
    prefixed("Kevin's Stall", build_stall)(kit, st)
    kv = kit.empty("scene kevin", root, (KEVIN_SPOT[0], KEVIN_SPOT[1], 0))
    prefixed("Shopkeeper Kevin", build_kevin)(kit, kv)
    sm = kit.empty("scene slots", root, (SLOTS_SPOT[0], SLOTS_SPOT[1], 0))
    prefixed("Slot Machine", build_slot_machine)(kit, sm)


SCENES = [
    dict(name="kevins shop", build=build_shop_scene, cam=((1.5, -10.5, 4.2), (0.2, 0.3, 1.2), 30), res=(1600, 900)),
    dict(name="kevin close", build=build_shop_scene, cam=((2.2, -1.6, 1.75), (2.6, 1.6, 1.5), 32), res=(1600, 900)),
    dict(name="kevin face", build=build_shop_scene, cam=((2.45, 0.35, 1.72), (2.6, 1.55, 1.64), 40), res=(1200, 900)),
]
