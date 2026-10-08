"""FX batch for style H: projectiles, muzzle flashes, impact splats and decals, flavor effects, explosions, gibs and
hit markers, plus a firefight scene that shows them together.

Conventions
- Projectiles fly along -Y; origin at the projectile's center; `socket trail` sits where a runtime trail attaches.
- Muzzle flashes: origin is the gun's `muzzle` socket, flash shoots along -Y.
- Impacts, decals, flavor effects and explosions: origin at the hit point, +Z is the surface normal (floor case);
  rotate the root so +Z matches the hit normal for walls and bodies.
- Hit markers and the ice-crack overlay face -Y (toward the viewer)."""
from style_H import *

VAN = "#fff1c7"; BERRY = "#ff8fc8"; ICE = "#c8fbff"; ICE_D = "#7fe8f0"; GOLD = "#f0a43a"

FLAVORS = {
    'vanilla': dict(base=VAN, dark="#f0cf8a", light=WHITE, fleck="#a8692e", fleck2="#e3b45e", trail=YEL),
    'chocolate': dict(base="#8a4a26", dark=CHOC, light="#c98552", fleck="#4e2812", fleck2="#ffd0a0", trail="#c98552"),
    'strawberry': dict(base=BERRY, dark=PINK, light="#ffd0e6", fleck=RED, fleck2=YEL, trail=PINK),
    'mint': dict(base=MINT, dark="#1fbf95", light="#b8fff0", fleck=CHOC, fleck2="#4e2812", trail="#8ff9de"),
    'blood': dict(base=RED, dark=DRED, light="#ff6f8f", fleck=ZG, fleck2=DRED, trail=RED),
}


def pre(root):
    return root.name[:-5] if root.name.endswith(" root") else root.name


# ---------------------------------------------------------------- sprites (pixel textures with alpha)
class CanvasA(Canvas):
    """Pixel canvas with a transparent background. No x wrap: sprites and decals are flat quads."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.p = [(0.0, 0.0, 0.0, 0.0)] * (w * h)

    def set(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y * self.w + x] = (*rgb(col), 1.0)

    def opaque(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h and self.p[y * self.w + x][3] > 0

    def image(self, name):
        img = bpy.data.images.new(name, self.w, self.h, alpha=True)
        img.pixels.foreach_set([v for c in self.p for v in c])
        img.update()
        img.pack()
        return img


def sprite_mat(name, cv, emit=0.6):
    m = bpy.data.materials.new(f"ZD2 H {name}")
    nt = v1.node_tree(m)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = cv.image(f"H {name}")
    tx.interpolation = 'Closest'
    tx.extension = 'CLIP'
    p.inputs["Roughness"].default_value = 0.8
    p.inputs["Specular IOR Level"].default_value = 0.2
    p.inputs["Emission Strength"].default_value = emit
    nt.links.new(tx.outputs["Color"], p.inputs["Base Color"])
    nt.links.new(tx.outputs["Color"], p.inputs["Emission Color"])
    nt.links.new(tx.outputs["Alpha"], p.inputs["Alpha"])
    nt.links.new(p.outputs[0], out.inputs[0])
    m.surface_render_method = 'DITHERED'
    m.use_backface_culling = False
    return m


def quad(kit, name, w, h, mat, parent, loc=(0, 0, 0), rot=(0, 0, 0), plane='xz'):
    """Flat textured quad centered on loc. plane 'xz' faces -Y (sprite), 'xy' faces +Z (floor decal)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    pts = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    vs = [bm.verts.new((u, 0, v) if plane == 'xz' else (u, v, 0)) for u, v in pts]
    fc = bm.faces.new(vs)
    for lp, uv in zip(fc.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = uv
    return kit.mesh_from_bmesh(name, bm, mat, parent, loc, rot, smooth=False)


def line(c, x0, y0, x1, y1, col):
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        c.set(x0, y0, col)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 >= dy:
            err += dy; x0 += sx
        if e2 <= dx:
            err += dx; y0 += sy


GLYPHS = {
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    '$': ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
}


def text_sprite(glyphs, k, fill, shadow, edge=INK, hi=WHITE, pad=2):
    """Outlined pixel text on a transparent canvas sized to fit. glyphs: list of row tuples ('#' = ink)."""
    mask, x = set(), 0
    rows = len(glyphs[0])
    for g in glyphs:
        for r, row in enumerate(g):
            for q, b in enumerate(row):
                if b == '#':
                    for dx in range(k):
                        for dy in range(k):
                            mask.add((x + q * k + dx + pad, (rows - 1 - r) * k + dy + pad))
        x += (len(g[0]) + 1) * k
    c = CanvasA(x - k + 2 * pad, rows * k + 2 * pad)
    for (px, py) in mask:
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                c.set(px + dx, py + dy, edge)
    for (px, py) in mask:
        c.set(px + 1, py - 1, shadow); c.set(px + 1, py - 2, edge)
    for (px, py) in mask:
        c.set(px, py, hi if (px, py + 1) not in mask else fill)
    return c


# ---------------------------------------------------------------- pixel textures
def tex_scoop(F, rand):
    c = Canvas(16, 16, F['base'])
    c.speckle(rand, [F['dark']], 28)
    c.rect(6, 4, 9, 9, F['light']); c.set(7, 7, WHITE); c.set(8, 8, WHITE)
    c.rect(0, 15, 15, 15, F['dark'])
    c.speckle(rand, [F['fleck'], F['fleck2']], 12, 1, 14)
    return c


def tex_banana():
    c = Canvas(16, 32, YEL)
    for x in (0, 4, 8, 12):
        c.rect(x, 0, x, 31, "#f0c020")
    c.rect(0, 0, 15, 3, "#8a5a1e"); c.rect(0, 28, 15, 31, "#7fbf3a"); c.rect(0, 30, 15, 31, "#5a3a14")
    c.dots([(6, 12), (10, 18), (2, 21), (14, 9), (7, 24)], "#a8692e")
    c.rect(6, 6, 6, 22, "#fff3a0")
    return c


def tex_rope():
    c = Canvas(8, 16, WHITE)
    for y in range(16):
        for x in range(8):
            if (x + y) % 4 < 2:
                c.set(x, y, PINK)
    return c


def tex_ice():
    c = Canvas(8, 16, ICE)
    c.rect(2, 0, 2, 15, WHITE); c.rect(5, 0, 6, 15, ICE_D)
    c.rect(0, 0, 7, 2, MINT); c.rect(0, 13, 7, 15, WHITE)
    c.dots([(3, 6), (4, 10), (1, 9)], WHITE)
    return c


def tex_berry_chunk():
    c = Canvas(8, 8, RED)
    c.rect(5, 5, 7, 7, "#ffd0e6"); c.rect(6, 6, 7, 7, WHITE)
    c.dots([(1, 1), (4, 2), (2, 5), (6, 3), (0, 4)], YEL)
    return c


def tex_coin():
    c = Canvas(16, 16, YEL)
    disc(c, 8, 8, 7, GOLD); disc(c, 8, 8, 6, YEL)
    for r, row in enumerate(GLYPHS['$']):
        for q, b in enumerate(row):
            if b == '#':
                c.set(6 + q, 11 - r, "#d9862a")
    c.dots([(4, 11), (5, 12), (4, 12)], WHITE)
    return c


def tex_decal(F, rand, n=32):
    """Lobed splat: dark rim, bright highlight, flecks, satellite droplets. Transparent outside."""
    c = CanvasA(n, n)
    h = n / 2
    lobes = [(rand.uniform(0, 2 * math.pi), rand.uniform(0.18, 0.42)) for _ in range(6)]

    def rad(t):
        return h * (0.44 + sum(a * max(0.0, math.cos(t - p)) ** 6 for p, a in lobes))
    inside = set()
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - h, y + 0.5 - h
            if math.hypot(dx, dy) < rad(math.atan2(dy, dx)):
                inside.add((x, y))
    for _ in range(9):
        a = rand.uniform(0, 2 * math.pi)
        d = min(h - 2.5, rad(a) + rand.uniform(1.5, 4.5))
        r = rand.choice((0.5, 1.0, 1.5))
        cx, cy = h + math.cos(a) * d, h + math.sin(a) * d
        for y in range(int(cy - 2), int(cy + 3)):
            for x in range(int(cx - 2), int(cx + 3)):
                if 0 < x < n - 1 and 0 < y < n - 1 and (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r + 0.5:
                    inside.add((x, y))
    for (x, y) in inside:
        rim = any((x + dx, y + dy) not in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        c.set(x, y, F['dark'] if rim else F['base'])
    flecks = [p for p in inside if all((p[0] + dx, p[1] + dy) in inside for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    for _ in range(n // 2):
        c.set(*rand.choice(flecks), rand.choice((F['fleck'], F['fleck2'], F['dark'])))
    hx, hy = h - 3, h + 3
    for (x, y) in flecks:
        if (x + 0.5 - hx) ** 2 + (y + 0.5 - hy) ** 2 < (0.2 * h) ** 2:
            c.set(x, y, F['light'])
    c.rect(int(hx) - 1, int(hy), int(hx), int(hy) + 1, WHITE)
    c.set(int(hx) + 3, int(hy) - 2, WHITE)
    return c


def tex_frost(rand, n=32):
    """Six-armed frost flower for the freeze burst floor decal."""
    c = CanvasA(n, n)
    h = n // 2
    for i in range(6):
        a = math.pi / 3 * i + 0.2
        ex, ey = h + round(math.cos(a) * (h - 1)), h + round(math.sin(a) * (h - 1))
        line(c, h, h, ex, ey, ICE)
        for f, ln in ((0.4, 4), (0.65, 3), (0.85, 2)):
            bx, by = h + math.cos(a) * (h - 1) * f, h + math.sin(a) * (h - 1) * f
            for s in (-1, 1):
                b = a + s * 0.9
                line(c, round(bx), round(by), round(bx + math.cos(b) * ln), round(by + math.sin(b) * ln), WHITE)
    for y in range(n):
        for x in range(n):
            d = math.hypot(x - h, y - h)
            if d < h * 0.45 and (x + y) % 2 == 0 and not c.opaque(x, y):
                c.set(x, y, ICE_D if d > h * 0.3 else ICE)
    disc(c, h, h, 2, WHITE)
    return c


def tex_ice_crack(rand):
    """Screen overlay: cracks radiating from an impact point plus frost creeping in from the corners."""
    W, Hh = 64, 36
    c = CanvasA(W, Hh)
    for y in range(Hh):
        for x in range(W):
            d = min(math.hypot(x - cx, (y - cy) * 1.6) for cx in (0, W - 1) for cy in (0, Hh - 1))
            if d < 7 or (d < 15 and rand.random() < ((15 - d) / 8) ** 0.8):
                c.set(x, y, WHITE if d < 4 or rand.random() < 0.25 else ICE)
            elif d < 19 and (x + y) % 2 == 0 and rand.random() < 0.45:
                c.set(x, y, ICE_D)
    for cx, cy in ((3, 3), (60, 32), (4, 31), (59, 4)):
        for i in range(-2, 3):
            c.set(cx + i, cy, WHITE); c.set(cx, cy + i, WHITE)
    ox, oy = 40, 19
    arms = []
    for i in range(10):
        a = 2 * math.pi * i / 10 + rand.uniform(-0.2, 0.2)
        x, y, pts = float(ox), float(oy), []
        for step in range(60):
            a += rand.uniform(-0.25, 0.25)
            x += math.cos(a); y += math.sin(a) * 0.8
            if not (0 <= x < W and 0 <= y < Hh):
                break
            pts.append((round(x), round(y)))
            if step > 6 and rand.random() < 0.06:
                b = a + rand.choice((-1, 1)) * 0.8
                bx, by = x, y
                for _ in range(rand.randint(4, 9)):
                    bx += math.cos(b); by += math.sin(b) * 0.8
                    c.set(round(bx), round(by) - 1, ICE_D); c.set(round(bx), round(by), WHITE)
        arms.append(pts)
        for px, py in pts:
            c.set(px, py - 1, ICE_D)
        for px, py in pts:
            c.set(px, py, WHITE)
    for r in (5, 11):
        for i in range(10):
            if rand.random() < 0.75 and len(arms[i]) > r and len(arms[(i + 1) % 10]) > r:
                (x0, y0), (x1, y1) = arms[i][r], arms[(i + 1) % 10][r]
                line(c, x0, y0, x1, y1, WHITE)
    disc(c, ox, oy, 2, WHITE)
    c.dots([(ox - 3, oy), (ox + 3, oy), (ox, oy + 3), (ox, oy - 3)], ICE_D)
    return c


def tex_tracer():
    """Tracer streak: white core, yellow, pink edges; dithers out toward the tail (v = 1)."""
    c = CanvasA(8, 32)
    for y in range(32):
        for x in range(8):
            col = WHITE if x in (3, 4) else YEL if x in (2, 5) else PINK if x in (1, 6) else None
            if col is None:
                continue
            fade = y / 31
            edge = x in (1, 6)
            if (edge and fade > 0.45 and (x + y) % 2) or (fade > 0.7 and (x + y) % 2) or (fade > 0.88 and (x * 3 + y) % 3):
                continue
            c.set(x, y, col if fade < 0.8 or x not in (3, 4) else YEL)
    return c


def tex_shock_band():
    c = CanvasA(4, 16)
    for y in range(16):
        for x in range(4):
            if y < 6 or (y < 11 and (x + y) % 2 == 0) or (y < 14 and (x + y) % 4 == 0):
                c.set(x, y, PINK if y < 3 else WHITE if y < 6 else "#ff8fc8" if y < 11 else MINT)
    return c


def tex_puff(col, shade):
    c = Canvas(8, 8, col)
    c.speckle(random.Random(7), [shade], 14)
    c.dots([(1, 6), (2, 6), (5, 2)], WHITE)
    return c


# ---------------------------------------------------------------- mesh helpers
def star3(kit, name, c, ax, bx, points, inner, mat, parent, R=None, jit=0.25, phase=0.0):
    """Flat star fan in the plane spanned by ax, bx (vectors carry the outer radius along each axis)."""
    c, ax, bx = Vector(c), Vector(ax), Vector(bx)
    bm = bmesh.new()
    ctr = bm.verts.new(c)
    ring = []
    for i in range(points * 2):
        a = phase + math.pi * i / points
        r = inner if i % 2 else (1 - jit + 2 * jit * R.random() if R else 1.0)
        ring.append(bm.verts.new(c + ax * math.cos(a) * r + bx * math.sin(a) * r))
    for i in range(len(ring)):
        bm.faces.new((ctr, ring[i], ring[(i + 1) % len(ring)]))
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=False)


def uvball(kit, name, center, radii, mat, parent, jitter=0.0, R=None, smooth=False, subdiv=1):
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1, calc_uvs=True)
    for v in bm.verts:
        k = 1 + (R.uniform(-jitter, jitter) if R else 0)
        v.co = Vector((v.co.x * radii[0] * k, v.co.y * radii[1] * k, v.co.z * radii[2] * k)) + Vector(center)
    return kit.mesh_from_bmesh(name, bm, mat, parent, smooth=smooth)


def puff_mesh(kit, name, blobs, mats, parent, R, loc=(0, 0, 0)):
    """One merged low-poly smoke cloud: blobs = [(center, r, material index)]."""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    for c, r, mi in blobs:
        new = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r, matrix=Matrix.Translation(Vector(c)),
                                         calc_uvs=True)
        for v in new['verts']:
            v.co += (v.co - Vector(c)) * R.uniform(-0.12, 0.12)
        for f in {f for v in new['verts'] for f in v.link_faces}:
            f.material_index = mi
    return kit.mesh_from_bmesh(name, bm, mats, parent, loc, smooth=False)


def coin(kit, name, r, t, face, rim, parent, loc, rot, sides=10):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    A = [2 * math.pi * i / sides for i in range(sides)]
    front = [bm.verts.new((math.cos(a) * r, -t / 2, math.sin(a) * r)) for a in A]
    back = [bm.verts.new((math.cos(a) * r, t / 2, math.sin(a) * r)) for a in A]
    for vs, sgn in ((front, 1), (back, -1)):
        fc = bm.faces.new(vs)
        for lp, a in zip(fc.loops, A):
            lp[uvl].uv = (0.5 + sgn * math.cos(a) * 0.5, 0.5 + math.sin(a) * 0.5)
    for i in range(sides):
        fc = bm.faces.new((front[i], front[(i + 1) % sides], back[(i + 1) % sides], back[i]))
        fc.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit.mesh_from_bmesh(name, bm, [face, rim], parent, loc, rot, smooth=False)


def drop(kit, name, p, d, r, length, mat, parent, sides=6):
    """Teardrop droplet: round head at p, tail stretched back against its flight direction d."""
    d, p = Vector(d).normalized(), Vector(p)
    side = (0, 0, 1) if abs(d.z) < 0.9 else (1, 0, 0)
    return tube(kit, name, [p - d * length, p - d * length * 0.45, p], [r * 0.12, r * 0.7, r], mat, parent,
                sides=sides, side=side, bulge=(0, r * 0.9))


def cone_dir(R, axis, spread):
    axis = Vector(axis).normalized()
    u = axis.orthogonal().normalized()
    w = axis.cross(u)
    a, t = R.uniform(0, 2 * math.pi), math.radians(R.uniform(0, spread))
    return (axis * math.cos(t) + (u * math.cos(a) + w * math.sin(a)) * math.sin(t)).normalized()


def point_at(ob, d):
    ob.rotation_euler = Vector(d).to_track_quat('Z', 'Y').to_euler()


def flavor_mats(kit, F):
    return dict(base=solid(kit, "fx " + F['base'], F['base'], 0.55, shade=F['dark']),
                dark=solid(kit, "fx " + F['dark'], F['dark'], 0.45),
                light=solid(kit, "fx " + F['light'], F['light'], 0.7),
                fleck=solid(kit, "fx " + F['fleck'], F['fleck'], 0.6),
                fleck2=solid(kit, "fx " + F['fleck2'], F['fleck2'], 0.6))


def spray(kit, n, parent, S, axis, M, R, spread=70, reach=0.7, drops=10, cubes=8, blobs=3, flecks=10, scale=1.0,
          sag=0.3):
    """Flavor-colored frozen burst from S around axis: teardrops, pixel cubes, blobs and flecks."""
    S = Vector(S)

    def spot(t):
        d = cone_dir(R, axis, spread)
        return S + d * t * reach + Vector((0, 0, -sag * (t * reach) ** 2)), d
    for i in range(drops):
        p, d = spot(R.uniform(0.35, 1.0))
        r = R.uniform(0.018, 0.034) * scale
        drop(kit, f"{n} drop {i}", p, d - Vector((0, 0, 0.3)), r, r * R.uniform(3.0, 5.0), M['base'] if i % 3 else M['light'], parent)
    for i in range(cubes):
        p, _ = spot(R.uniform(0.2, 1.1))
        fx_cube(kit, parent, f"{n} cube {i}", p, R.uniform(0.022, 0.045) * scale, (M['base'], M['dark'], M['light'])[i % 3])
    for i in range(blobs):
        p, _ = spot(R.uniform(0.25, 0.8))
        r = R.uniform(0.03, 0.05) * scale
        lowball(kit, f"{n} blob {i}", p, (r, r, r * 0.85), M['base'] if i % 2 else M['light'], parent, smooth=False)
    for i in range(flecks):
        p, d = spot(R.uniform(0.15, 1.2))
        ob = tbox(kit, f"{n} fleck {i}", (0, 0, 0), (0.008 * scale, 0.008 * scale, 0.026 * scale),
                  M['fleck'] if i % 2 else M['fleck2'], parent, loc=p)
        point_at(ob, d)


# ---------------------------------------------------------------- 1. projectiles
def scoop_bullet(flavor):
    def build(kit, root):
        n, F, R = pre(root), FLAVORS[flavor], kit.rand
        M = flavor_mats(kit, F)
        body = tube(kit, f"{n} scoop", [(0, -0.05, 0), (0, -0.03, 0), (0, -0.005, 0), (0, 0.015, 0), (0, 0.03, 0),
                                        (0, 0.06, 0)],
                    [0.032, 0.047, 0.052, 0.056, 0.042, 0.016], tex_mat(f"{n} scoop", tex_scoop(F, R)), root, sides=8,
                    side=(1, 0, 0), bulge=(0.014, 0.006))
        vs = body.data.vertices
        for k in range(8):   # ragged scoop lip
            vs[3 * 8 + k].co.x *= 1.16 if k % 2 else 0.92
            vs[3 * 8 + k].co.z *= 1.16 if k % 2 else 0.92
            vs[3 * 8 + k].co.y += 0.008 if k % 2 else -0.004
        tube(kit, f"{n} streak", [(0, 0.05, 0), (0, 0.2, 0.004), (0, 0.42, 0.01)], [0.018, 0.009, 0.002],
             solid(kit, f"trail {F['trail']}", F['trail'], 1.1), root, sides=6, side=(1, 0, 0), caps=(False, True))
        for i, (y, r, dx) in enumerate(((0.13, 0.022, 0.03), (0.22, 0.017, -0.035), (0.3, 0.013, 0.02), (0.4, 0.009, -0.02))):
            drop(kit, f"{n} trail drop {i}", (dx, y, 0.005 + 0.01 * (i % 2)), (0, -1, 0.1), r, r * 3, M['base'] if i % 2 else M['light'], root)
        for i in range(5):
            fx_cube(kit, root, f"{n} trail cube {i}", (R.uniform(-0.05, 0.05), 0.08 + 0.07 * i, R.uniform(-0.04, 0.04)),
                    0.018 - 0.002 * i, (M['dark'], M['fleck'], M['light'])[i % 3])
        kit.empty(f"{n} socket trail", root, (0, 0.06, 0))
    return build


def build_sprinkle_pellet(kit, root):
    n, R = pre(root), kit.rand
    cols = [solid(kit, "sprinkle " + c, c, 0.9) for c in (PINK, BLUE, YEL, MINT, WHITE, PURP, ORNG)]
    tube(kit, f"{n} pellet", [(0, -0.03, 0), (0, 0.03, 0)], 0.011, cols[0], root, sides=6, side=(1, 0, 0),
         bulge=(0.008, 0.008))
    tbox(kit, f"{n} glint", (0, -0.008, 0.0095), (0.004, 0.03, 0.004), cols[4], root)
    tube(kit, f"{n} streak", [(0, 0.035, 0), (0, 0.16, 0), (0, 0.3, 0)], [0.01, 0.006, 0.0015],
         solid(kit, "pellet streak", YEL, 1.3), root, sides=6, side=(1, 0, 0), caps=(False, True))
    for i in range(7):
        ob = tbox(kit, f"{n} trail sprinkle {i}", (0, 0, 0), (0.006, 0.022 - 0.0015 * i, 0.006), cols[(i + 1) % 7], root,
                  loc=(R.uniform(-0.03, 0.03), 0.06 + 0.04 * i, R.uniform(-0.025, 0.025)))
        ob.rotation_euler = (0, 0, math.radians(R.uniform(-25, 25)))
    star3(kit, f"{n} spark", (0, -0.03, 0), (0.025, 0, 0), (0, 0, 0.025), 4, 0.3, solid(kit, "spark", WHITE, 1.8), root)
    kit.empty(f"{n} socket trail", root, (0, 0.03, 0))


def build_spoon_tracer(kit, root):
    n = pre(root)
    steel = solid(kit, "steel", STEEL, 0.6, shade="#a9a2e0")
    bowl = uvball(kit, f"{n} spoon bowl", (0, -0.04, 0), (0.022, 0.034, 0.009), steel, root, smooth=True)
    tube(kit, f"{n} spoon handle", [(0, -0.008, 0.002), (0, 0.04, 0.004), (0, 0.06, 0.004)], [0.0055, 0.006, 0.008], steel,
         root, sides=6, side=(1, 0, 0))
    tbox(kit, f"{n} handle tip", (0, 0.064, 0.004), (0.018, 0.012, 0.006), solid(kit, "spoon pink", PINK, 0.9), root)
    tm = sprite_mat(f"{n} tracer", tex_tracer(), 1.6)
    L = 1.6
    quad(kit, f"{n} tracer flat", 0.07, L, tm, root, (0, 0.07 + L / 2, 0), plane='xy')
    quad(kit, f"{n} tracer up", 0.07, L, tm, root, (0, 0.07 + L / 2, 0), (0, 90, 0), plane='xy')
    star3(kit, f"{n} glow", (0, -0.02, 0), (0.06, 0, 0), (0, 0, 0.06), 4, 0.25, solid(kit, "spark yellow", YEL, 1.8), root)
    star3(kit, f"{n} glow core", (0, -0.025, 0), (0.03, 0, 0), (0, 0, 0.03), 4, 0.35, solid(kit, "spark", WHITE, 1.8), root,
          phase=math.pi / 4)
    kit.empty(f"{n} socket trail", root, (0, 0.07, 0))


def build_banana_harpoon(kit, root):
    n, R = pre(root), kit.rand
    tb = tex_mat(f"{n} banana", tex_banana())
    steel = solid(kit, "steel", STEEL, 0.5, shade="#a9a2e0")
    pts = [(0, 0.13, 0.022), (0, 0.08, 0.004), (0, 0.0, -0.006), (0, -0.08, 0.004), (0, -0.13, 0.024)]
    tube(kit, f"{n} banana", pts, [0.012, 0.026, 0.03, 0.025, 0.011], tb, root, sides=5, side=(1, 0, 0), smooth=False,
         v=(1.0, 0.0), bulge=(0.006, 0.004))
    # steel harpoon head with barbs
    tube(kit, f"{n} collar", [(0, -0.125, 0.023), (0, -0.15, 0.025)], 0.016, solid(kit, "harpoon pink", PINK), root,
         sides=6, side=(1, 0, 0))
    tube(kit, f"{n} tip", [(0, -0.15, 0.025), (0, -0.165, 0.025), (0, -0.24, 0.026)], [0.012, 0.018, 0.002], steel, root,
         sides=4, side=(1, 0, 0), smooth=False)
    for sx in (1, -1):
        tbox(kit, f"{n} barb {sx}", (sx * 0.02, -0.18, 0.025), (0.006, 0.04, 0.008), steel, root, rot=(0, 0, sx * 35))
    # peel flaps flared back like fletching
    peel_in = solid(kit, "peel inside", "#fff3c0", 0.45)
    for i in range(3):
        a = math.radians(90 + 120 * i)
        o = Vector((math.cos(a), 0, math.sin(a)))
        base = Vector((0, 0.11, 0.018))
        tube(kit, f"{n} peel {i}", [base + o * 0.012, base + o * 0.04 + Vector((0, 0.05, 0)),
                                     base + o * 0.075 + Vector((0, 0.1, 0))],
             [(0.016, 0.004), (0.018, 0.004), (0.01, 0.003)], tb if i % 2 == 0 else peel_in, root, sides=4,
             side=o.cross(Vector((0, 1, 0))), smooth=False)
    # rope tail
    rope = [(0, 0.14, 0.024)]
    for i in range(1, 7):
        rope.append((0.018 * math.sin(i * 1.3), 0.14 + 0.07 * i, 0.024 + 0.015 * math.cos(i * 1.1)))
    tube(kit, f"{n} rope", rope, 0.006, tex_mat(f"{n} rope", tex_rope()), root, sides=4, side=(0, 0, 1))
    for i in range(4):
        tbox(kit, f"{n} speed line {i}", (0, 0, 0), (0.004, R.uniform(0.18, 0.3), 0.004), solid(kit, "speed", WHITE, 1.2),
             root, loc=(R.choice((-1, 1)) * R.uniform(0.05, 0.08), 0.15 + 0.06 * i, R.uniform(-0.04, 0.07)))
    kit.empty(f"{n} socket rope", root, (0, 0.14, 0.024))


# ---------------------------------------------------------------- 2. muzzle flashes
def flash_layers(kit, n, root, R, y, r, pts, cols, side_len, side_w, side_pts=7, spin=0.0, emits=(1.4, 1.8, 2.2)):
    """Front star (faces -Y) plus crossed side flames stretched along -Y, in three nested colors."""
    for i, (col, k, e) in enumerate(zip(cols, (1.0, 0.68, 0.36), emits)):
        m = solid(kit, f"flash {col}", col, e)
        star3(kit, f"{n} star {i}", (0, y - 0.004 * i, 0), (r * k, 0, 0), (0, 0, r * k), pts, 0.42, m, root, R,
              phase=spin + 0.2 * i)
        c = (0, y - side_len * k / 2, 0)
        star3(kit, f"{n} flame flat {i}", c, (side_w * k, 0, 0), (0, side_len * k / 2, 0), side_pts, 0.38, m, root, R,
              phase=-math.pi / 2)
        star3(kit, f"{n} flame up {i}", c, (0, 0, side_w * k), (0, side_len * k / 2, 0), side_pts, 0.38, m, root, R,
              phase=-math.pi / 2)


def build_flash_pistol(kit, root):
    n, R = pre(root), kit.rand
    flash_layers(kit, n, root, R, -0.02, 0.1, 5, (PINK, YEL, WHITE), 0.24, 0.07)
    for i in range(5):
        ob = tbox(kit, f"{n} sprinkle {i}", (0, 0, 0), (0.007, 0.007, 0.024),
                  solid(kit, "sprinkle " + (BLUE, MINT, YEL, PINK, WHITE)[i], (BLUE, MINT, YEL, PINK, WHITE)[i], 0.9),
                  root, loc=cone_dir(R, (0, -1, 0), 35) * R.uniform(0.12, 0.26))
        point_at(ob, (0, -1, 0))


def build_flash_shotgun(kit, root):
    n, R = pre(root), kit.rand
    flash_layers(kit, n, root, R, -0.03, 0.22, 9, (PINK, YEL, WHITE), 0.42, 0.17, side_pts=9)
    m = solid(kit, f"flash {ORNG}", ORNG, 1.4)
    for i, a in enumerate((-24, 24)):
        d = Vector((math.sin(math.radians(a)), -math.cos(math.radians(a)), 0))
        star3(kit, f"{n} fan flame {i}", d * 0.2 + Vector((0, -0.03, 0)), (0, 0, 0.07), d * 0.17, 6, 0.4, m, root, R)
    M = flavor_mats(kit, FLAVORS['vanilla'])
    B = flavor_mats(kit, FLAVORS['strawberry'])
    for i in range(9):
        d = cone_dir(R, (0, -1, 0), 22)
        p = d * R.uniform(0.3, 0.6)
        drop(kit, f"{n} pellet {i}", p, d, 0.016, 0.07, (M['base'], B['base'], M['light'])[i % 3], root)
    puffs = [solid(kit, "puff " + c, c, 0.5) for c in ("#e3cfff", "#ffd0ea", "#cff7ff")]
    for i in range(5):
        a = 2 * math.pi * i / 5
        r = R.uniform(0.04, 0.06)
        lowball(kit, f"{n} puff {i}", (math.cos(a) * 0.12, -0.06, math.sin(a) * 0.1), (r, r, r), puffs[i % 3], root,
                smooth=False)


def build_flash_smg(kit, root):
    n, R = pre(root), kit.rand
    flash_layers(kit, n, root, R, -0.015, 0.075, 4, (MINT, YEL, WHITE), 0.3, 0.035, side_pts=5, spin=math.pi / 4)
    for i in range(4):
        ob = tbox(kit, f"{n} spark {i}", (0, 0, 0), (0.005, 0.005, 0.05), solid(kit, "spark yellow", YEL, 1.8), root,
                  loc=cone_dir(R, (0, -1, 0), 40) * R.uniform(0.1, 0.2))
        point_at(ob, cone_dir(R, (0, -1, 0), 30))


def build_flash_minigun(kit, root):
    n, R = pre(root), kit.rand
    flash_layers(kit, n, root, R, -0.04, 0.26, 12, (PINK, YEL, WHITE), 0.75, 0.13, side_pts=9)
    mint = solid(kit, f"flash {MINT}", MINT, 1.6)
    ring = ring_mesh(kit, f"{n} barrel ring", 0.1, 0.15, mint, root, (0, -0.02, 0), segs=12)
    ring.rotation_euler = (math.radians(90), 0, 0)
    for i in range(6):
        a = 2 * math.pi * i / 6
        star3(kit, f"{n} barrel star {i}", (math.cos(a) * 0.062, -0.05, math.sin(a) * 0.062), (0.05, 0, 0), (0, 0, 0.05), 4,
              0.35, solid(kit, "spark", WHITE, 1.8), root, phase=math.pi / 4)
    for i in range(10):
        ob = tbox(kit, f"{n} spark {i}", (0, 0, 0), (0.008, 0.008, 0.08), solid(kit, "spark yellow", YEL, 1.8), root,
                  loc=cone_dir(R, (0, -1, 0), 50) * R.uniform(0.2, 0.5))
        point_at(ob, cone_dir(R, (0, -1, 0), 40))
    point_light(kit, root, f"{n} light", (0, -0.25, 0.05), "#ffd36b", 30, 3.0, 0.2)


# ---------------------------------------------------------------- 3. impact splats and decals
def splat_burst(flavor):
    def build(kit, root):
        n, F, R = pre(root), FLAVORS[flavor], kit.rand
        M = flavor_mats(kit, F)
        lowball(kit, f"{n} core", (0, 0, 0.035), (0.11, 0.11, 0.045), M['base'], root, smooth=True)
        lowball(kit, f"{n} core top", (-0.02, -0.02, 0.07), (0.05, 0.05, 0.03), M['light'], root, smooth=True)
        splat(kit, f"{n} puddle", (0, 0, 0), 0.2, M['dark'], root, lobes=11, z=0.003)
        for i in range(8):   # crown of droplets thrown up and out
            a = 2 * math.pi * i / 8 + R.uniform(-0.2, 0.2)
            el = math.radians(R.uniform(35, 60))
            d = Vector((math.cos(a) * math.cos(el), math.sin(a) * math.cos(el), math.sin(el)))
            t = R.uniform(0.18, 0.3)
            r = R.uniform(0.022, 0.032)
            drop(kit, f"{n} crown {i}", d * t + Vector((0, 0, 0.05)), d, r, r * 4.5, M['base'] if i % 3 else M['light'], root)
        spray(kit, n, root, (0, 0, 0.05), (0, 0, 1), M, R, spread=65, reach=0.55, drops=6, cubes=8, blobs=2, flecks=10)
        if flavor == 'blood':
            goo = solid(kit, "goo", ZG, 0.9, shade="#6fd83a")
            for i in range(5):
                fx_cube(kit, root, f"{n} goo {i}", cone_dir(R, (0, 0, 1), 60) * R.uniform(0.15, 0.45), 0.03, goo)
    return build


def splat_decal(flavor):
    def build(kit, root):
        n = pre(root)
        quad(kit, f"{n} decal", 0.8, 0.8, sprite_mat(f"{n} decal", tex_decal(FLAVORS[flavor], kit.rand), 0.5), root,
             (0, 0, 0.004), plane='xy')
    return build


# ---------------------------------------------------------------- 4. flavor effects
def build_strawberry_splash(kit, root):
    n, R = pre(root), kit.rand
    M = flavor_mats(kit, FLAVORS['strawberry'])
    # splash crown: open ring with alternating tall and short spikes
    bm = bmesh.new()
    N = 14
    lo = [bm.verts.new((math.cos(2 * math.pi * i / N) * 0.34, math.sin(2 * math.pi * i / N) * 0.34, 0.0)) for i in range(N)]
    mid = [bm.verts.new((math.cos(2 * math.pi * i / N) * 0.44, math.sin(2 * math.pi * i / N) * 0.44, 0.16)) for i in range(N)]
    hi = []
    for i in range(N):
        a = 2 * math.pi * (i + 0.5) / N
        r, z = (0.64, 0.48) if i % 2 == 0 else (0.54, 0.28)
        hi.append(bm.verts.new((math.cos(a) * r, math.sin(a) * r, z)))
    for i in range(N):
        j = (i + 1) % N
        bm.faces.new((lo[i], lo[j], mid[j], mid[i]))
        bm.faces.new((mid[i], mid[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    kit.mesh_from_bmesh(f"{n} crown", bm, M['base'], root, smooth=True)
    for i in range(0, N, 2):
        a = 2 * math.pi * (i + 0.5) / N
        lowball(kit, f"{n} crown bead {i}", (math.cos(a) * 0.68, math.sin(a) * 0.68, 0.56), (0.035, 0.035, 0.035),
                M['light'] if i % 4 else M['base'], root, smooth=False)
    # center jet with a ball on top
    tube(kit, f"{n} jet", [(0, 0, 0.0), (0, 0, 0.2), (0, 0, 0.45)], [0.12, 0.06, 0.045], M['base'], root, sides=8,
         side=(1, 0, 0), bulge=(0, 0.04))
    lowball(kit, f"{n} jet ball", (0, 0, 0.56), (0.06, 0.06, 0.07), M['light'], root, smooth=True)
    spray(kit, n, root, (0, 0, 0.2), (0, 0, 1), M, R, spread=80, reach=1.0, drops=14, cubes=10, blobs=4, flecks=12, scale=1.2)
    tb = tex_mat(f"{n} berry chunk", tex_berry_chunk())
    for i in range(6):
        d = cone_dir(R, (0, 0, 1), 70)
        tbox(kit, f"{n} berry chunk {i}", (0, 0, 0), (0.06, 0.05, 0.04), tb, root, loc=d * R.uniform(0.5, 0.85) + Vector((0, 0, 0.1)),
             rot=(R.uniform(0, 90), R.uniform(0, 90), R.uniform(0, 90)))
    ring_mesh(kit, f"{n} ring", 0.55, 0.68, solid(kit, "ring pink", PINK, 1.6), root, (0, 0, 0.012), segs=18)
    ring_mesh(kit, f"{n} ring outer", 0.95, 1.0, solid(kit, "ring red", RED, 1.4), root, (0, 0, 0.014), segs=22)
    quad(kit, f"{n} decal", 1.1, 1.1, sprite_mat(f"{n} decal", tex_decal(FLAVORS['strawberry'], R), 0.5), root,
         (0, 0, 0.006), plane='xy')


def build_mint_freeze(kit, root):
    n, R = pre(root), kit.rand
    ti = tex_mat(f"{n} ice", tex_ice(), emit=0.7)
    for i in range(11):
        a = 2 * math.pi * i / 11 + R.uniform(-0.15, 0.15)
        tilt = math.radians(R.uniform(12, 45))
        d = Vector((math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt), math.cos(tilt)))
        L = R.uniform(0.35, 0.8)
        base = Vector((math.cos(a), math.sin(a), 0)) * R.uniform(0.08, 0.3)
        r = R.uniform(0.05, 0.09)
        tube(kit, f"{n} shard {i}", [base - d * 0.05, base + d * L * 0.5, base + d * L], [r, r * 0.8, 0.004], ti, root,
             sides=4, side=(math.cos(a + 1), math.sin(a + 1), 0), smooth=False, caps=(True, False))
    tube(kit, f"{n} center spike", [(0, 0, -0.02), (0, 0, 0.5), (0, 0, 1.0)], [0.11, 0.08, 0.004], ti, root, sides=5,
         side=(1, 0, 0), smooth=False, caps=(True, False))
    ice = solid(kit, "ice cube", ICE, 0.8, shade=ICE_D)
    for i in range(12):
        d = cone_dir(R, (0, 0, 1), 75)
        tbox(kit, f"{n} ice chip {i}", (0, 0, 0), (0.05, 0.05, 0.05), ice if i % 3 else solid(kit, "fx " + WHITE, WHITE, 0.9),
             root, loc=d * R.uniform(0.5, 1.1) + Vector((0, 0, 0.1)), rot=(R.uniform(0, 90), R.uniform(0, 90), R.uniform(0, 90)))
    flake = solid(kit, "snowflake", WHITE, 1.6)
    for i in range(5):
        a = 2 * math.pi * i / 5
        star3(kit, f"{n} snowflake {i}", (math.cos(a) * 0.7, math.sin(a) * 0.7 - 0.1, R.uniform(0.6, 1.1)), (0.07, 0, 0),
              (0, 0, 0.07), 6, 0.3, flake, root)
    puffs = [solid(kit, "puff " + c, c, 0.6) for c in ("#cff7ff", WHITE)]
    for i in range(7):
        a = 2 * math.pi * i / 7
        r = R.uniform(0.08, 0.13)
        lowball(kit, f"{n} frost puff {i}", (math.cos(a) * 0.45, math.sin(a) * 0.45, r * 0.6), (r, r, r * 0.8), puffs[i % 2],
                root, smooth=False)
    ring_mesh(kit, f"{n} frost ring", 0.6, 0.74, solid(kit, "ring mint", MINT, 1.6), root, (0, 0, 0.012), segs=18)
    ring_mesh(kit, f"{n} frost ring outer", 1.0, 1.05, solid(kit, "ring ice", ICE, 1.6), root, (0, 0, 0.014), segs=22)
    quad(kit, f"{n} frost decal", 1.6, 1.6, sprite_mat(f"{n} frost", tex_frost(R), 0.9), root, (0, 0, 0.006), plane='xy')


def build_choc_tip(kit, root):
    n, R = pre(root), kit.rand
    txt = text_sprite([GLYPHS['+'], GLYPHS['$']], 2, YEL, "#d9862a")
    quad(kit, f"{n} text", 0.52, 0.52 * txt.h / txt.w, sprite_mat(f"{n} text", txt, 1.4), root, (0, 0, 0.62))
    face = tex_mat(f"{n} coin", tex_coin(), emit=0.8)
    rim = solid(kit, "coin rim", GOLD, 0.8)
    for i, (p, rot) in enumerate((((-0.26, 0.02, 0.34), (0, 30, 20)), ((0.24, -0.04, 0.42), (10, -20, -35)),
                                  ((0.06, 0.05, 0.2), (0, 70, 0)), ((-0.12, -0.06, 0.88), (-15, 15, 50)),
                                  ((0.3, 0.02, 0.86), (20, 40, -60)))):
        coin(kit, f"{n} coin {i}", 0.055, 0.014, face, rim, root, p, rot)
    M = flavor_mats(kit, FLAVORS['chocolate'])
    spray(kit, n, root, (0, 0, 0.05), (0, 0, 1), M, R, spread=55, reach=0.45, drops=6, cubes=6, blobs=2, flecks=6)
    for i, (p, r) in enumerate((((-0.34, 0, 0.62), 0.06), ((0.38, 0, 0.66), 0.05), ((0.0, 0, 0.98), 0.07),
                                 ((-0.2, 0, 0.12), 0.04))):
        star3(kit, f"{n} sparkle {i}", p, (r, 0, 0), (0, 0, r), 4, 0.22, solid(kit, "spark yellow", YEL, 1.8), root)
        star3(kit, f"{n} sparkle core {i}", (p[0], p[1] - 0.004, p[2]), (r * 0.4, 0, 0), (0, 0, r * 0.4), 4, 0.3,
              solid(kit, "spark", WHITE, 1.8), root, phase=math.pi / 4)


def build_sprinkle_shrapnel(kit, root):
    n, R = pre(root), kit.rand
    cols = [solid(kit, "sprinkle " + c, c, 0.9) for c in (PINK, BLUE, YEL, MINT, WHITE, PURP, ORNG)]
    streak = solid(kit, "streak", "#fff3c0", 1.0)
    for i in range(46):
        d = cone_dir(R, (0, 0, 1), 60)
        t = R.uniform(0.15, 1.0)
        p = d * t * 1.1 + Vector((0, 0, 0.05))
        ob = tbox(kit, f"{n} sprinkle {i}", (0, 0, 0), (0.012, 0.012, 0.045), cols[i % 7], root, loc=p)
        point_at(ob, d)
        if i % 3 == 0:
            tube(kit, f"{n} streak {i}", [p - d * (0.03 + 0.18 * t), p - d * 0.025], [0.001, 0.005], streak, root,
                     sides=4, side=d.orthogonal(), caps=(False, False))
    star3(kit, f"{n} flash", (0, 0, 0.08), (0.18, 0, 0), (0, 0, 0.18), 8, 0.42, solid(kit, "star " + YEL, YEL, 1.8), root, R)
    star3(kit, f"{n} flash core", (0, -0.005, 0.08), (0.08, 0, 0), (0, 0, 0.08), 6, 0.45, solid(kit, "spark", WHITE, 1.8), root)
    ring_mesh(kit, f"{n} ring", 0.3, 0.36, solid(kit, "ring yellow", YEL, 1.6), root, (0, 0, 0.012), segs=14)


# ---------------------------------------------------------------- 5. explosions
def blast_stars(kit, n, root, C, size):
    for i, (col, pts, k, e, tilt) in enumerate(((PINK, 12, 1.0, 1.5, 8), (YEL, 10, 0.74, 1.8, -6), (WHITE, 8, 0.4, 2.2, 14))):
        fx_star(kit, root, f"{n} star {i}", C + Vector((0, 0.1 - 0.05 * i, 0)), pts, size * k, size * k * 0.48, col, e, (0, tilt, 0))
        # a second, perpendicular layer so the blast still reads from the side
        star3(kit, f"{n} star side {i}", C + Vector((0.02 * i, 0, 0)), (0, size * k * 0.8, 0), (0, 0, size * k * 0.8), pts,
              0.48, solid(kit, "star " + col, col, e), root, kit.rand)


def build_grenade_blast(kit, root):
    n, R = pre(root), kit.rand
    C = Vector((0, 0, 0.7))
    lowball(kit, f"{n} fireball", C, (0.32, 0.32, 0.3), solid(kit, "fireball", WHITE, 2.4), root, smooth=False)
    lowball(kit, f"{n} fireball shell", C + Vector((0, 0.05, 0.05)), (0.45, 0.4, 0.42), solid(kit, "fireball pink", "#ff8fc8", 1.6),
            root, smooth=False)
    blast_stars(kit, n, root, C, 1.3)
    for i, D in enumerate((Vector((1, -0.2, 0.6)), Vector((-1, -0.2, 0.6)), Vector((0, -0.3, 1)), Vector((0.5, 0.6, 0.4)),
                           Vector((-0.5, 0.6, 0.4)), Vector((0, -1, 0.3)))):
        burst(kit, root, C, D.normalized(), f"{n} burst {i}", scale=1.0, blood=0, cream=6, sprinkles=10, blobs=2, reach=1.2)
    puffs = [solid(kit, "puff " + c, c, 0.5) for c in ("#e3cfff", "#ffd0ea", "#cff7ff")]
    for i in range(10):
        a = 2 * math.pi * i / 10 + R.uniform(-0.1, 0.1)
        r = R.uniform(0.14, 0.22)
        lowball(kit, f"{n} puff {i}", (math.cos(a) * R.uniform(0.75, 1.0), math.sin(a) * R.uniform(0.75, 1.0), r * 0.7),
                (r, r, r * 0.85), puffs[i % 3], root, smooth=False)
    ring_mesh(kit, f"{n} shock ring", 1.1, 1.24, solid(kit, "ring pink", PINK, 1.6), root, (0, 0, 0.02), 18)
    floor_splats(kit, root, Vector((0, 0, 0)), [(0, 0, 0.55, 0), (0.6, -0.4, 0.2, 1), (-0.7, -0.2, 0.18, 2),
                                                 (0.3, 0.6, 0.16, 3), (-0.4, 0.55, 0.14, 0)], f"{n}", dots=14, spread=(1.2, 1.0))
    point_light(kit, root, f"{n} light", C + Vector((0, -0.3, 0.2)), "#ffd36b", 160, 5.0, 0.5)
    kit.empty(f"{n} socket light", root, C)


def build_bloater_blast(kit, root):
    n, R = pre(root), kit.rand
    pal = fx_palette(kit)
    t_body = tex_mat(f"{n} skin", tex_bloater_body(R))
    pus = solid(kit, "pustule", ZG, 2.6, shade="#d8ff9e")
    C = Vector((0, 0, 1.12))
    lowball(kit, f"{n} fireball", C, (0.5, 0.5, 0.48), solid(kit, "goo flash", "#d8ff9e", 2.4), root, smooth=False)
    for i in range(8):
        a0 = 2 * math.pi * i / 8 + R.uniform(-0.1, 0.1)
        z0 = R.choice((0.95, 1.1, 1.25))
        ob, ctr = shell_chunk(kit, f"{n} belly chunk {i}", root, z0, z0 + 0.32, a0, a0 + 0.62, t_body, pal['creams'][0])
        out = Vector((ctr.x, ctr.y, 0)).normalized()
        ob.location = C + out * R.uniform(1.0, 1.6) + Vector((0, 0, R.uniform(-0.3, 0.9)))
        ob.rotation_euler = (R.uniform(-1.5, 1.5), R.uniform(-1.5, 1.5), R.uniform(0, 6.28))
        lowball(kit, f"{n} chunk pustule {i}", ob.location + Vector((0, 0, 0.06)), (0.04, 0.04, 0.04), pus, root)
    back = Vector((0, 0.45, 0))
    fx_star(kit, root, f"{n} star pink", C + back * 1.4 + Vector((0, 0, 0.1)), 12, 1.55, 0.75, PINK, 1.5, (0, 8, 0))
    fx_star(kit, root, f"{n} star yellow", C + back * 1.2 + Vector((0, 0, 0.1)), 10, 1.15, 0.55, YEL, 1.8, (0, -6, 0))
    fx_star(kit, root, f"{n} star white", C + back + Vector((0, 0, 0.1)), 8, 0.62, 0.32, WHITE, 2.2, (0, 14, 0))
    star3(kit, f"{n} star side", C, (0, 1.3, 0), (0, 0, 1.3), 12, 0.48, solid(kit, "star " + ZG, ZG, 1.6), root, R)
    puffs = [solid(kit, "puff " + c, c, 0.5) for c in ("#e3cfff", "#ffd0ea", "#cff7ff")]
    for i in range(12):
        a = 2 * math.pi * i / 12 + R.uniform(-0.1, 0.1)
        r = R.uniform(0.18, 0.28)
        p = C + Vector((math.cos(a) * R.uniform(1.3, 1.7), math.sin(a) * R.uniform(1.0, 1.4), R.uniform(-0.6, 0.7)))
        lowball(kit, f"{n} puff {i}", p, (r, r, r * 0.9), puffs[i % 3], root, smooth=False)
    for i, D in enumerate((Vector((1, 0.1, 0.7)), Vector((-1, 0.1, 0.7)), Vector((0, 0.3, 1)), Vector((0.6, -0.6, 0.3)),
                           Vector((-0.6, -0.6, 0.3)), Vector((0, -1, 0.5)))):
        burst(kit, root, C + Vector((0, 0, 0.25)), D.normalized(), f"{n} burst {i}", scale=1.4, blood=5, cream=5, sprinkles=14,
              blobs=2, goo=4, reach=1.6)
    ring_mesh(kit, f"{n} shock ring", 1.55, 1.75, solid(kit, "ring pink", PINK, 1.6), root, (0, 0, 0.02), 18)
    ring_mesh(kit, f"{n} shock ring 2", 2.25, 2.33, solid(kit, "ring mint", MINT, 1.6), root, (0, 0, 0.025), 22)
    floor_splats(kit, root, Vector((0, 0, 0)), [(0, 0.1, 1.15, 0), (0.9, -0.5, 0.35, 'red'), (-1.0, -0.4, 0.3, 'goo'),
                                                 (0.4, -1.1, 0.25, 'red'), (-0.5, -1.2, 0.22, 1), (1.4, 0.3, 0.2, 'goo'),
                                                 (-1.5, 0.5, 0.25, 'red'), (0.0, -1.6, 0.15, 2)], f"{n}", dots=24, spread=(2.0, 1.6))
    point_light(kit, root, f"{n} light", C + Vector((0, -0.4, 0.6)), "#ffd36b", 220, 6.0, 0.6)
    kit.empty(f"{n} socket light", root, C)


PUFF_SIZES = {'small': (0.18, 3), 'medium': (0.32, 5), 'large': (0.55, 8)}


def smoke_puff(size):
    def build(kit, root):
        n, R = pre(root), kit.rand
        r0, count = PUFF_SIZES[size]
        mats = [tex_mat(f"puff {c}", tex_puff(c, s), emit=0.5) for c, s in
                (("#e3cfff", "#c9b0f0"), ("#ffd0ea", "#f0a8cc"), ("#cff7ff", "#a8e4f0"), ("#b79ae6", "#9c7fd6"))]
        blobs = [((0, 0, r0), r0, 0)]
        for i in range(count - 1):
            a = 2 * math.pi * i / (count - 1) + R.uniform(-0.3, 0.3)
            d = r0 * R.uniform(0.7, 1.0)
            z = r0 * R.uniform(0.5, 1.5)
            r = r0 * R.uniform(0.55, 0.8)
            blobs.append(((math.cos(a) * d, math.sin(a) * d, z), r, 3 if z < r0 * 0.8 else (i % 3)))
        puff_mesh(kit, f"{n} puff", blobs, mats, root, R)
    return build


def build_shockwave(kit, root):
    n, R = pre(root), kit.rand
    ring_mesh(kit, f"{n} ring", 1.6, 1.85, solid(kit, "ring pink", PINK, 1.6), root, (0, 0, 0.01), segs=24)
    ring_mesh(kit, f"{n} ring inner", 1.3, 1.36, solid(kit, "ring yellow", YEL, 1.6), root, (0, 0, 0.012), segs=20)
    ring_mesh(kit, f"{n} ring outer", 2.05, 2.1, solid(kit, "ring mint", MINT, 1.6), root, (0, 0, 0.014), segs=28)
    tube(kit, f"{n} band", [(0, 0, 0.0), (0, 0, 0.5)], [1.72, 1.9], sprite_mat(f"{n} band", tex_shock_band(), 1.4), root,
         sides=24, side=(1, 0, 0), caps=(False, False))
    for i in range(16):
        a = 2 * math.pi * i / 16 + R.uniform(-0.1, 0.1)
        r = R.uniform(1.7, 1.95)
        fx_cube(kit, root, f"{n} dust {i}", (math.cos(a) * r, math.sin(a) * r, R.uniform(0.05, 0.4)), R.uniform(0.04, 0.07),
                solid(kit, "puff " + ("#e3cfff", "#ffd0ea", "#cff7ff")[i % 3], ("#e3cfff", "#ffd0ea", "#cff7ff")[i % 3], 0.5))


# ---------------------------------------------------------------- 6. gibs
def gib_chunk(kit, name, radii, skin, raw, parent, R, tear=(0, 0, 1)):
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1, calc_uvs=True)
    for v in bm.verts:
        v.co = Vector((v.co.x * radii[0], v.co.y * radii[1], v.co.z * radii[2])) * R.uniform(0.82, 1.15)
    bm.normal_update()
    for f in bm.faces:
        f.material_index = 1 if f.normal.dot(Vector(tear)) > 0.35 else 0
    return kit.mesh_from_bmesh(name, bm, [skin, raw], parent, smooth=False)


def build_gibs(kit, root):
    n, R = pre(root), kit.rand
    skin = solid(kit, "zombie skin", ZG, shade="#7fe03f")
    raw = solid(kit, "blood", RED, 0.55, shade=DRED)
    dred = solid(kit, "blood dark", DRED, 0.45)
    bone = solid(kit, "bone", VAN, 0.45, shade="#e8d27a")
    shirt = solid(kit, "zombie shirt", ORNG, shade="#e8752b")
    spots = iter([(x, y) for y in (-0.16, 0.16) for x in (-0.48, -0.16, 0.16, 0.48)])

    def piece(label, z, rot=(0, 0, 0)):
        x, y = next(spots)
        return kit.empty(f"{n} {label} pivot", root, (x, y, z), rot)

    # hand: palm, fingers, wrist stump with a bone nub
    p = piece("hand", 0.03, (0, 0, 20))
    tube(kit, f"{n} hand palm", [(0, 0.05, 0), (0, -0.02, 0), (0, -0.06, 0)], [(0.044, 0.024), (0.05, 0.026), (0.046, 0.02)],
         tex_mat(f"{n} hand", tex_zombie_hand()), p, sides=6, front=(0, 0, 1))
    for i, x in enumerate((-0.033, -0.011, 0.011, 0.033)):
        tube(kit, f"{n} finger {i}", [(x, -0.06, 0), (x * 1.1, -0.1, 0.004), (x * 1.2, -0.13 + 0.01 * abs(i - 1.5), -0.012)],
             0.009, skin, p, sides=5, front=(0, 0, 1))
    tube(kit, f"{n} thumb", [(0.045, 0.0, 0), (0.07, -0.04, 0.0)], 0.011, skin, p, sides=5, front=(0, 0, 1))
    tube(kit, f"{n} wrist", [(0, 0.12, 0), (0, 0.05, 0)], [0.036, 0.04], tex_mat(f"{n} wrist", tex_zombie_arm(R)), p, sides=6,
         front=(0, 0, 1), v=(0.0, 0.3), caps=(False, True))
    tube(kit, f"{n} wrist stump", [(0, 0.125, 0), (0, 0.12, 0)], 0.04, dred, p, sides=6, front=(0, 0, 1))
    lowball(kit, f"{n} wrist bone", (0, 0.14, 0.0), (0.014, 0.018, 0.014), bone, p)
    # foot: bare foot with an ankle stump
    p = piece("foot", 0.045, (0, 0, -15))
    tube(kit, f"{n} foot", [(0, 0.06, 0.0), (0, -0.03, -0.005), (0, -0.12, -0.015)],
         [(0.042, 0.036), (0.05, 0.03), (0.046, 0.018)], skin, p, sides=6, front=(0, 0, 1), bulge=(0.01, 0.02))
    tube(kit, f"{n} ankle", [(0, 0.05, 0.0), (0, 0.06, 0.09)], [0.045, 0.042], tex_mat(f"{n} ankle", tex_zombie_leg(R, True)),
         p, sides=6, front=(0, -1, 0), v=(0.9, 0.7), caps=(False, False))
    tube(kit, f"{n} ankle stump", [(0, 0.06, 0.09), (0, 0.061, 0.095)], 0.044, dred, p, sides=6, front=(0, -1, 0))
    lowball(kit, f"{n} ankle bone", (0, 0.062, 0.105), (0.016, 0.016, 0.018), bone, p)
    # rib piece: torn torso chunk with ribs sticking out
    p = piece("ribs", 0.06)
    gib_chunk(kit, f"{n} rib chunk", (0.09, 0.07, 0.05), shirt, raw, p, R, tear=(0, -0.3, 1))
    for i in range(3):
        x = -0.05 + 0.05 * i
        tube(kit, f"{n} rib {i}", [(x, 0.02, 0.02), (x, -0.03, 0.07), (x + 0.01, -0.09, 0.08), (x + 0.015, -0.13, 0.05)],
             [0.011, 0.01, 0.009, 0.007], bone, p, sides=5, side=(1, 0, 0))
    # jaw: U-shaped mandible with teeth and gums
    p = piece("jaw", 0.02, (0, 0, 10))
    pts = [(math.cos(math.radians(a)) * 0.06, math.sin(math.radians(a)) * 0.055 + 0.02, 0) for a in (190, 230, 270, 310, 350)]
    tube(kit, f"{n} jaw", pts, [0.016, 0.018, 0.02, 0.018, 0.016], skin, p, sides=6, front=(0, 0, 1))
    tube(kit, f"{n} gums", [(x, y, z + 0.016) for x, y, z in pts], 0.011, solid(kit, "gums", "#ff5d7a", 0.5), p, sides=5,
         front=(0, 0, 1))
    teeth = [solid(kit, "tooth", "#fff1c7", 0.5), solid(kit, "tooth yellow", "#e8d27a", 0.45)]
    for i in range(9):
        if i == 3:
            continue
        a = math.radians(195 + 150 * i / 8)
        tbox(kit, f"{n} tooth {i}", (math.cos(a) * 0.06, math.sin(a) * 0.055 + 0.02, 0.032), (0.012, 0.01, 0.018), teeth[i % 2], p)
    for sx in (1, -1):
        lowball(kit, f"{n} jaw stump {sx}", (sx * 0.06, 0.012, 0.0), (0.02, 0.016, 0.02), raw, p)
    # eyeball with the optic nerve
    p = piece("eyeball", 0.04, (0, 0, -30))
    ce = Canvas(16, 16, WHITE)
    ce.rect(0, 0, 15, 1, INK); ce.rect(0, 2, 15, 4, RED); ce.rect(0, 5, 15, 5, YEL)
    ce.dots([(2, 9), (3, 10), (9, 8), (10, 9), (11, 11), (6, 12), (14, 10)], RED); ce.rect(0, 14, 15, 15, "#ff8fae")
    tube(kit, f"{n} eyeball", [(0, -0.035, 0), (0, -0.02, 0), (0, 0.0, 0), (0, 0.02, 0), (0, 0.035, 0)],
         [0.02, 0.034, 0.038, 0.033, 0.018], tex_mat(f"{n} eye", ce), p, sides=8, side=(1, 0, 0), bulge=(0.008, 0.006))
    tube(kit, f"{n} optic nerve", [(0, 0.04, 0), (0.02, 0.08, -0.01), (0.0, 0.12, -0.03), (-0.03, 0.15, -0.035)],
         [0.012, 0.01, 0.008, 0.006], solid(kit, "nerve", "#ff5d7a", 0.5), p, sides=5, side=(0, 0, 1))
    # brain bit
    p = piece("brain bit", 0.04)
    tb = tex_mat(f"{n} brain", tex_brain(R))
    uvball(kit, f"{n} brain lobe", (0, 0, 0), (0.07, 0.055, 0.045), tb, p, 0.12, R)
    uvball(kit, f"{n} brain lobe 2", (0.045, 0.02, 0.02), (0.04, 0.035, 0.03), tb, p, 0.12, R)
    lowball(kit, f"{n} brain blood", (-0.03, -0.03, -0.03), (0.04, 0.03, 0.02), raw, p, smooth=False)
    # flesh chunks
    p = piece("flesh chunk A", 0.05)
    gib_chunk(kit, f"{n} flesh chunk A", (0.08, 0.06, 0.05), skin, raw, p, R, tear=(0.5, -0.5, 0.7))
    lowball(kit, f"{n} flesh A bone", (0.04, -0.03, 0.04), (0.015, 0.03, 0.015), bone, p)
    p = piece("flesh chunk B", 0.045)
    gib_chunk(kit, f"{n} flesh chunk B", (0.065, 0.075, 0.045), skin, raw, p, R, tear=(-0.6, 0.2, 0.7))
    tbox(kit, f"{n} flesh B shirt scrap", (0.0, 0.0, 0.0), (0.07, 0.05, 0.01), solid(kit, "shirt purple", PURP), p,
         loc=(0.02, 0.02, 0.042), rot=(8, -10, 25))


# ---------------------------------------------------------------- 7. hit markers
def build_hit_star(kit, root):
    n = pre(root)
    fx_star(kit, root, f"{n} star", (0, 0, 0), 8, 0.26, 0.11, YEL, 1.4, (0, 0, 0))
    fx_star(kit, root, f"{n} core", (0, -0.005, 0), 6, 0.1, 0.05, WHITE, 1.6, (0, 12, 0))
    tick = solid(kit, "tick", WHITE, 1.8)
    for i, a in enumerate((45, 135, 225, 315)):
        r = math.radians(a)
        tbox(kit, f"{n} tick {i}", (0, 0, 0), (0.035, 0.01, 0.13), tick, root, rot=(0, 90 - a, 0),
             loc=(math.cos(r) * 0.36, -0.01, math.sin(r) * 0.36))


def build_headshot_star(kit, root):
    n = pre(root)
    fx_star(kit, root, f"{n} star red", (0, 0.01, 0), 10, 0.42, 0.2, RED, 1.4, (0, 6, 0))
    fx_star(kit, root, f"{n} star pink", (0, 0, 0), 9, 0.32, 0.15, PINK, 1.5, (0, -8, 0))
    fx_star(kit, root, f"{n} star yellow", (0, -0.008, 0), 8, 0.22, 0.1, YEL, 1.8, (0, 14, 0))
    fx_star(kit, root, f"{n} core", (0, -0.014, 0), 6, 0.09, 0.05, WHITE, 2.0, (0, 0, 0))
    txt = text_sprite([FONT[ch] for ch in "HEADSHOT!"], 1, YEL, RED)
    quad(kit, f"{n} text", 0.76, 0.76 * txt.h / txt.w, sprite_mat(f"{n} text", txt, 1.4), root, (0, -0.02, -0.5))


def build_ice_crack(kit, root):
    n = pre(root)
    quad(kit, f"{n} overlay", 1.6, 0.9, sprite_mat(f"{n} overlay", tex_ice_crack(kit.rand), 0.9), root, (0, 0, 0))


# ---------------------------------------------------------------- asset list
ASSETS = [
    ("Vanilla Scoop Bullet", scoop_bullet('vanilla')),
    ("Chocolate Scoop Bullet", scoop_bullet('chocolate')),
    ("Strawberry Scoop Bullet", scoop_bullet('strawberry')),
    ("Mint Scoop Bullet", scoop_bullet('mint')),
    ("Sprinkle Pellet", build_sprinkle_pellet),
    ("Long Spoon Tracer", build_spoon_tracer),
    ("Banana Harpoon", build_banana_harpoon),
    ("Pistol Muzzle Flash", build_flash_pistol),
    ("Shotgun Muzzle Flash", build_flash_shotgun),
    ("SMG Muzzle Flash", build_flash_smg),
    ("Minigun Muzzle Flash", build_flash_minigun),
] + [(f"{f.title()} Splat Burst", splat_burst(f)) for f in ('vanilla', 'chocolate', 'strawberry', 'mint', 'blood')] + [
    (f"{f.title()} Splat Decal", splat_decal(f)) for f in ('vanilla', 'chocolate', 'strawberry', 'mint', 'blood')] + [
    ("Strawberry Splash Burst", build_strawberry_splash),
    ("Mint Freeze Burst", build_mint_freeze),
    ("Chocolate Tip Popup", build_choc_tip),
    ("Sprinkle Shrapnel Spray", build_sprinkle_shrapnel),
    ("Scoop Grenade Blast", build_grenade_blast),
    ("Bloater Pop Blast", build_bloater_blast),
    ("Smoke Puff Small", smoke_puff('small')),
    ("Smoke Puff Medium", smoke_puff('medium')),
    ("Smoke Puff Large", smoke_puff('large')),
    ("Shockwave Ring", build_shockwave),
    ("Zombie Gibs", build_gibs),
    ("Hit Star", build_hit_star),
    ("Headshot Star", build_headshot_star),
    ("Ice Crack Overlay", build_ice_crack),
]
SPACING = 12


# ---------------------------------------------------------------- scene: one frame of a firefight
def build_firefight(kit, root):
    R = kit.rand
    n = "Firefight"
    tex = tex_mat(f"{n} asphalt", tex_asphalt(R), ext='REPEAT')
    tbox(kit, f"{n} road", (0, 6, -0.05), (16, 22, 0.1), tex, root, uv={'pz': (0, 0, 8, 11)})
    line_m = solid(kit, "road line", YEL, 0.6)
    for i in range(6):
        tbox(kit, f"{n} road line {i}", (0, 0, 0), (0.12, 1.2, 0.01), line_m, root, loc=(-0.9, 0.5 + 2.6 * i, 0.002))

    def at(label, loc, rot=(0, 0, 0), parent=root, scale=1.0):
        return kit.empty(f"{n} {label} root", parent, loc, rot, (scale, scale, scale))

    def toward(ob, src, dst):
        """Orient a projectile root (flies along local -Y) from src to dst."""
        ob.rotation_euler = (Vector(src) - Vector(dst)).to_track_quat('Y', 'Z').to_euler()

    # walkers
    zA = at("walker strawberry", (-1.5, 3.4, 0), (0, 0, 18))
    build_zombie(kit, zA)
    zB = at("walker mint", (0.25, 5.0, 0), (0, 0, -6))
    build_zombie(kit, zB)
    zC = at("walker chocolate", (1.75, 3.0, 0), (0, 0, -24))
    build_zombie(kit, zC, hit=True)

    # strawberry hit on walker A's chest: splash faces the shooter
    build_strawberry_splash(kit, at("strawberry splash", (-1.45, 3.12, 1.22), (78, 0, 10), scale=0.45))
    build_hit_star(kit, at("hit star A", (-1.38, 2.95, 1.3), (0, 0, 18)))
    sb = at("strawberry bullet", (-0.95, 1.3, 1.3))
    toward(sb, (0.3, -1.2, 1.4), (-1.45, 3.1, 1.25))
    scoop_bullet('strawberry')(kit, sb)
    for i, (x, z) in enumerate(((-0.7, 1.5), (-0.4, 1.2))):
        p = at(f"sprinkle pellet {i}", (x, 1.9 + 0.6 * i, z))
        toward(p, (0.3, -1.2, 1.4), (-1.4, 3.2, 1.0 + 0.2 * i))
        build_sprinkle_pellet(kit, p)
    splat_decal('strawberry')(kit, at("strawberry decal", (-1.2, 2.6, 0)))

    # mint hit freezes walker B in place
    build_mint_freeze(kit, at("mint freeze", (0.25, 4.95, 0)))
    mb = at("mint bullet", (0.05, 2.6, 1.25))
    toward(mb, (0.3, -1.2, 1.4), (0.25, 4.9, 1.1))
    scoop_bullet('mint')(kit, mb)
    splat_burst('mint')(kit, at("mint splat", (0.2, 4.72, 1.25), (80, 0, 0)))

    # chocolate headshot on walker C: splat, headshot star, tip popup, gibs flying
    build_choc_tip(kit, at("choc tip", (1.95, 2.9, 1.7), (0, 0, -10), scale=0.8))
    splat_burst('chocolate')(kit, at("choc splat", (1.72, 2.8, 1.5), (75, 0, -20)))
    build_headshot_star(kit, at("headshot", (1.35, 2.6, 1.95), (0, 0, -12), scale=0.6))
    tr = at("spoon tracer", (1.3, 1.4, 1.5))
    toward(tr, (0.6, -1.2, 1.55), (1.72, 2.85, 1.5))
    build_spoon_tracer(kit, tr)
    splat_burst('blood')(kit, at("blood splat", (2.1, 2.9, 1.15), (60, 0, -60)))
    splat_decal('blood')(kit, at("blood decal", (2.0, 2.4, 0)))
    splat_decal('chocolate')(kit, at("choc decal", (1.4, 2.2, 0)))
    gibs = at("gibs", (0, 0, 0))
    build_gibs(kit, gibs)
    for ob, loc, rot in ((f"{n} gibs jaw", (2.45, 2.55, 1.85), (40, 20, 70)), (f"{n} gibs eyeball", (1.25, 2.4, 1.95), (0, 30, 140)),
                         (f"{n} gibs hand", (2.5, 2.1, 0.03), (0, 0, 60)), (f"{n} gibs flesh chunk A", (2.3, 2.7, 1.4), (30, 50, 0)),
                         (f"{n} gibs ribs", (1.0, 3.3, 0.06), (0, 0, 30)), (f"{n} gibs foot", (-0.6, 3.6, 0.045), (0, 0, 100)),
                         (f"{n} gibs brain bit", (2.0, 2.65, 2.15), (20, 40, 10)),
                         (f"{n} gibs flesh chunk B", (-2.0, 3.0, 1.6), (40, 10, 30))):
        o = bpy.data.objects[ob + " pivot"]
        o.location = loc
        o.rotation_euler = [math.radians(a) for a in rot]

    # scoop grenade going off behind them, smoke drifting
    build_grenade_blast(kit, at("grenade", (-0.6, 8.2, 0)))
    smoke_puff('large')(kit, at("smoke L", (3.8, 9.8, 0)))
    smoke_puff('medium')(kit, at("smoke M", (-3.2, 8.4, 0.2)))
    smoke_puff('small')(kit, at("smoke S", (1.0, 6.4, 1.6)))
    splat_decal('vanilla')(kit, at("vanilla decal", (0.9, 1.6, 0)))
    splat_burst('vanilla')(kit, at("vanilla splat", (-0.2, 2.0, 0)))

    # first-person Scoop Pistol firing, held in a gloved player hand
    gun = at("pistol", (0.5, -0.45, 1.34), (6, 0, 186))
    build_gun(kit, gun)
    build_flash_pistol(kit, kit.empty(f"{n} pistol muzzle", gun, (0, -0.208, 0.004)))
    grip = root_pos(root, gun, (0, 0.05, -0.07))
    tube(kit, f"{n} player forearm", [grip + Vector((0.16, -0.28, -0.22)), grip + Vector((0.05, -0.1, -0.08)), grip],
         [0.05, 0.045, 0.04], tex_mat(f"{n} player arm", tex_player_arm()), root, sides=6, side=(1, 0, 0))
    tube(kit, f"{n} player hand", [grip + Vector((0, -0.03, -0.01)), grip + Vector((0, 0.03, 0.02))], [0.045, 0.04],
         solid(kit, "skin", SKIN), root, sides=6, side=(1, 0, 0), bulge=(0, 0.02))
    point_light(kit, root, f"{n} flash light", (0.4, 0.2, 1.4), "#ffd36b", 60, 4.0, 0.3)


SCENES = [dict(name="Firefight", build=build_firefight, cam=((0.25, -1.25, 1.62), (0.2, 4.0, 1.15), 28), res=(1600, 900))]
