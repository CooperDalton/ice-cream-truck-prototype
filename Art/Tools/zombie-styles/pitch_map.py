"""Draws the heist pitch area map: one town seen from above like a pause-menu minimap, with icons for the truck, crew,
kids and cops, patrol sight cones, a legend and the quota, plus the map alone and the serving-window shot with the
minimap in its corner. Reads the top-down render and icon positions written by PitchShots.CaptureMap (Tools > Zombie
Truck > Capture Pitch Map) and writes map.png, map_only.png and 01_serving_window_minimap.png next to them. Text is in
Fredoka and Nunito (OFL, in fonts/), which read better on slides than the HUD pixel fonts.
    uv run --with pillow python pitch_map.py"""
import json, math, os
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.normpath(os.path.join(HERE, "..", "..", "..", "Zombie Ice Cream Truck"))
PITCH = os.path.join(PROJECT, "Library", "CodexPlaytests", "pitch")
SPRITES = os.path.join(PROJECT, "Assets", "Art", "Sprites")
FONTS = os.path.join(HERE, "fonts")

MAP_SCALE = 0.5    # canvas pixels per render pixel
ICON_PIXEL = 3     # canvas pixels per icon pixel
FRAME_PIXEL = 3    # canvas pixels per HUD sprite pixel

INK = (27, 16, 51); PINK = (255, 79, 163); MINT = (56, 242, 195); YEL = (255, 225, 74); BLUE = (46, 134, 255)
WHITE = (255, 247, 238); RED = (255, 36, 72); LAV = (180, 140, 255); TAN = (214, 168, 92); GREEN = (60, 190, 90)
COLORS = {"K": INK, "P": PINK, "M": MINT, "Y": YEL, "B": BLUE, "W": WHITE, "R": RED, "L": LAV, "T": TAN,
          "G": (40, 44, 90), "C": (222, 160, 90), "N": (70, 50, 30), "D": (30, 34, 60), "E": GREEN}
TEAM = {"1": PINK, "2": BLUE, "3": MINT, "4": YEL}

TRUCK = ["..WWW..", ".WGGGW.", ".WGGGW.", "WWWWWWW", "PMMMMMP", "PMWWWMP", "PMMMMMP", "PMWWWMP", "PMMMMMP", "PPPPPPP",
         ".YKYKY."]
POLICE = ["..WWW..", ".KKKKK.", ".KGGGK.", "WWWWWWW", "WRRKBBW", "WWWWWWW", ".KGGGK.", ".KKKKK.", "..KKK.."]
CONE = ["..PP..", ".PPPP.", "PPPPPP", ".CCCC.", ".CCCC.", "..CC..", "..CC.."]
DIGITS = {"1": [".#.", "##.", ".#.", ".#.", "###"], "2": ["##.", "..#", ".#.", "#..", "###"],
          "3": ["##.", "..#", ".#.", "..#", "##."], "4": ["#.#", "#.#", "###", "..#", "..#"],
          "?": ["##.", "..#", ".#.", "...", ".#."],
          "*": ["#.#", ".#.", "###", ".#.", "#.#"]}


def font(name, size, weight):
    f = ImageFont.truetype(os.path.join(FONTS, name), size)
    f.set_variation_by_axes([weight] + [100] * (len(f.get_variation_axes()) - 1))
    return f


TITLE = lambda size: font("Fredoka.ttf", size, 700)
BODY = lambda size: font("Nunito.ttf", size, 700)


def sprite(rows, outline=INK):
    """Pixel grid (rows of palette letters, '.' clear) with a 1 px outline, scaled to ICON_PIXEL."""
    h, w = len(rows) + 2, len(rows[0]) + 2
    img = Image.new("RGBA", (w, h))
    filled = {(x + 1, y + 1) for y, row in enumerate(rows) for x, c in enumerate(row) if c != "."}
    for y, row in enumerate(rows):
        for x, c in enumerate(row):
            if c != ".":
                img.putpixel((x + 1, y + 1), COLORS[c] + (255,))
    for y in range(h):
        for x in range(w):
            if (x, y) not in filled and any((x + dx, y + dy) in filled for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                img.putpixel((x, y), outline + (255,))
    return img.resize((w * ICON_PIXEL, h * ICON_PIXEL), Image.NEAREST)


def badge(fill, glyph, ink=INK, rim=WHITE):
    """Round 9 px badge with a 3x5 glyph in the middle."""
    rows = []
    for y in range(9):
        row = ""
        for x in range(9):
            d = math.hypot(x - 4, y - 4)
            row += "." if d > 4.5 else "o" if d > 3.5 else "f"
        rows.append(row)
    for r, line in enumerate(DIGITS[glyph]):
        for q, b in enumerate(line):
            if b == "#":
                rows[2 + r] = rows[2 + r][:3 + q] + "g" + rows[2 + r][4 + q:]
    COLORS.update({"o": rim, "f": fill, "g": ink})
    return sprite(rows)


def place(layer, img, x, y, yaw=0):
    """Pastes an icon centered on (x, y), turned clockwise by yaw (degrees, 0 = up)."""
    if yaw % 360:
        img = img.rotate(-yaw, resample=Image.NEAREST, expand=True)
    layer.alpha_composite(img, (round(x - img.width / 2), round(y - img.height / 2)))


def label(draw, text, x, y, size=26, color=WHITE, anchor="mm"):
    draw.text((x, y), text, font=TITLE(size), fill=color, anchor=anchor, stroke_width=4, stroke_fill=INK)


def nine_slice(name, width, height, border=8):
    """A HUD frame sprite stretched to width x height canvas pixels at FRAME_PIXEL, corners kept."""
    src = Image.open(os.path.join(SPRITES, "HUD", name + ".png")).convert("RGBA")
    w, h = width // FRAME_PIXEL, height // FRAME_PIXEL
    out = Image.new("RGBA", (w, h))
    sw, sh = src.size
    xs = [(0, border, 0, border), (border, sw - border, border, w - border), (sw - border, sw, w - border, w)]
    ys = [(0, border, 0, border), (border, sh - border, border, h - border), (sh - border, sh, h - border, h)]
    for sx0, sx1, dx0, dx1 in xs:
        for sy0, sy1, dy0, dy1 in ys:
            piece = src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
            out.alpha_composite(piece, (dx0, dy0))
    return out.resize((w * FRAME_PIXEL, h * FRAME_PIXEL), Image.NEAREST)


def dithered(layer, polygon, color, alpha):
    """Fills a polygon with a checkerboard of color (PS1-style dithered transparency) and outlines it."""
    mask = Image.new("L", layer.size)
    ImageDraw.Draw(mask).polygon(polygon, fill=255)
    tint = Image.new("RGBA", layer.size, color + (alpha,))
    checker = Image.new("L", layer.size)
    px = checker.load()
    for y in range(0, layer.height, 1):
        for x in range((y // 2) % 2 * 2, layer.width, 4):
            px[x, y] = px[x + 1 if x + 1 < layer.width else x, y] = 255
    combined = Image.composite(mask, Image.new("L", layer.size), checker)
    layer.paste(tint, (0, 0), combined)
    ImageDraw.Draw(layer).line(polygon + [polygon[0]], fill=color + (220,), width=3)


def sight_cone(layer, x, y, yaw, meters, ppm, color):
    reach = meters * ppm
    points = [(x, y)]
    for a in range(-32, 33, 8):
        t = math.radians(yaw + a)
        points.append((x + math.sin(t) * reach, y - math.cos(t) * reach))
    dithered(layer, points, color, 150)


def across(yaw, half):
    """Offsets to both sides of a heading, perpendicular to it."""
    t = math.radians(yaw + 90)
    return math.sin(t) * half, -math.cos(t) * half


def draw_map(base, icons, ppm):
    size = (round(base.width * MAP_SCALE), round(base.height * MAP_SCALE))
    layer = ImageEnhance.Brightness(base.convert("RGBA").resize(size, Image.LANCZOS)).enhance(0.85)
    ppm *= MAP_SCALE
    draw = ImageDraw.Draw(layer)
    at = lambda icon: (icon["x"] * MAP_SCALE, icon["y"] * MAP_SCALE)
    # Sight cones and road marks first, icons on top.
    for icon in icons:
        x, y = at(icon)
        kind = icon["icon"].split()[0]
        if kind == "patrol":
            sight_cone(layer, x, y, icon["yaw"], 26, ppm, RED)
        elif kind == "cop":
            sight_cone(layer, x, y, icon["yaw"], 12, ppm, BLUE)
        elif kind == "townline":
            dx, dy = across(icon["yaw"], 6 * ppm)
            for i in range(12):
                a, b = i / 12, (i + 1) / 12
                draw.line([(x - dx + 2 * dx * a, y - dy + 2 * dy * a), (x - dx + 2 * dx * b, y - dy + 2 * dy * b)],
                          fill=YEL if i % 2 else WHITE, width=7)
            label(draw, "TOWN LINE", x, y - 38)
    truck = next(i for i in icons if i["icon"] == "truck")
    aboard = 0
    for icon in icons:
        x, y = at(icon)
        kind, _, detail = icon["icon"].partition(" ")
        yaw = icon["yaw"]
        if kind == "truck":
            place(layer, sprite(TRUCK), x, y, yaw)
        elif kind == "aboard":
            # Crew inside the truck: small numbered pips stacked beside the truck icon.
            tx, ty = at(truck)
            place(layer, badge(TEAM[detail], detail, ink=INK if detail in "34" else WHITE), tx + 30, ty - 14 + aboard * 30)
            aboard += 1
        elif kind == "crew":
            place(layer, badge(TEAM[detail], detail, ink=INK if detail in "34" else WHITE), x, y)
        elif kind == "kids":
            bubble = sprite(["WWWWWWWW", "WWWPPWWW", "WWPPPPWW", "WWWCCWWW", "WWWCCWWW", "WWWWWWWW", ".WW....."])
            place(layer, bubble, x - 14, y)
            label(draw, "x" + detail, x - 62, y, 26, YEL)
        elif kind == "detective":
            place(layer, badge(TAN, "?"), x, y)
        elif kind == "cop":
            place(layer, badge(BLUE, "*", ink=YEL), x, y)
        elif kind in ("patrol", "parked"):
            place(layer, sprite(POLICE, outline=WHITE), x, y, yaw)
        elif kind == "exit":
            arrow = sprite(["...Y...", "..YYY..", ".YYYYY.", "YYYYYYY", "..YYY..", "..YYY..", "..YYY.."])
            place(layer, arrow, x, y, yaw)
            label(draw, "NEXT TOWN", x - 80, y - 38, 26, YEL)
    for name, kind_detail, dx, dy in (("SCHOOL STOP", "kids 5", -20, 40), ("PARK STOP", "kids 4", 40, -36)):
        icon = next(i for i in icons if i["icon"] == kind_detail)
        x, y = at(icon)
        label(draw, name, x + dx, y + dy, 26, PINK)
    return layer


LEGEND = [
    ("truck", "Your truck"), ("crew", "Crew (players 1-4)"), ("kids", "Kids who want ice cream"),
    ("detective", "Detective: slows sales"), ("cop", "Cop on foot + sight"), ("patrol", "Patrol car + sight cone"),
    ("townline", "Town line: hit the quota to cross"),
]


def legend_icon(kind):
    if kind == "truck":
        return sprite(TRUCK)
    if kind == "crew":
        return badge(PINK, "1", ink=WHITE)
    if kind == "kids":
        return sprite(["WWWWWWWW", "WWWPPWWW", "WWPPPPWW", "WWWCCWWW", "WWWCCWWW", "WWWWWWWW", ".WW....."])
    if kind == "detective":
        return badge(TAN, "?")
    if kind == "cop":
        return badge(BLUE, "*", ink=YEL)
    if kind == "patrol":
        return sprite(POLICE, outline=WHITE)
    stripe = Image.new("RGBA", (54, 14))
    d = ImageDraw.Draw(stripe)
    for i in range(6):
        d.rectangle([i * 9, 0, i * 9 + 8, 13], fill=YEL if i % 2 else WHITE)
    return stripe


def main():
    base = Image.open(os.path.join(PITCH, "map_base.png"))
    data = json.load(open(os.path.join(PITCH, "map_icons.json")))
    layer = draw_map(base, data["icons"], data["pixelsPerMeter"])

    canvas = Image.new("RGBA", (1920, 1080), INK + (255,))
    bg = ImageDraw.Draw(canvas)
    for y in range(0, 1080, 6):
        for x in range((y // 6) % 2 * 6, 1920, 12):
            bg.rectangle([x, y, x + 2, y + 2], fill=(38, 24, 70))
    mx, my = 60, 152
    canvas.alpha_composite(nine_slice("panel", layer.width + 48, layer.height + 48), (mx - 24, my - 24))
    canvas.alpha_composite(layer, (mx, my))
    draw = ImageDraw.Draw(canvas)
    label(draw, "N", mx + layer.width - 30, my + 26, 34, WHITE)
    draw.polygon([(mx + layer.width - 30, my + 44), (mx + layer.width - 40, my + 62), (mx + layer.width - 20, my + 62)], fill=WHITE)

    banner = Image.open(os.path.join(SPRITES, "HUD", "banner.png")).convert("RGBA")
    banner = banner.resize((banner.width * FRAME_PIXEL, banner.height * FRAME_PIXEL), Image.NEAREST)
    for x in range(36, 1880, banner.width):
        canvas.alpha_composite(banner.crop((0, 0, min(banner.width, 1884 - x), banner.height)), (x, 30))
    label(draw, "MAPLEWOOD  -  TOWN 2 OF 5", 960, 60, 48, WHITE)

    lx, ly, lw = mx + layer.width + 60, my - 24, 1920 - (mx + layer.width + 60) - 36
    lh = layer.height + 48
    canvas.alpha_composite(nine_slice("panel_mint", lw, lh), (lx, ly))
    label(draw, "MAP", lx + lw // 2, ly + 52, 40, MINT)
    row = (lh - 250) // len(LEGEND)
    for i, (kind, text) in enumerate(LEGEND):
        y = ly + 100 + i * row + row // 2
        place(canvas, legend_icon(kind), lx + 60, y)
        draw.text((lx + 110, y), text, font=BODY(30), fill=WHITE, anchor="lm")

    # The quota: cash in hand against what it takes to cross the town line.
    qy = ly + lh - 140
    draw.text((lx + 30, qy), "QUOTA", font=TITLE(30), fill=YEL, anchor="lm")
    draw.text((lx + lw - 30, qy), "$340 / $500", font=TITLE(30), fill=WHITE, anchor="rm")
    trough = nine_slice("bar_back", lw - 60, 42, border=4)
    canvas.alpha_composite(trough, (lx + 30, qy + 24))
    fill = Image.open(os.path.join(SPRITES, "HUD", "bar_fill.png")).convert("RGBA")
    fill = fill.resize((fill.width * FRAME_PIXEL, fill.height * FRAME_PIXEL), Image.NEAREST)
    inner = int((lw - 84) * 340 / 500)
    for x in range(0, inner, fill.width):
        canvas.alpha_composite(fill.crop((0, 0, min(fill.width, inner - x), 30)), (lx + 42 + x, qy + 30))
    draw.text((lx + lw // 2, qy + 96), "3 patrols  -  2 cops on foot  -  1 detective", font=BODY(26), fill=LAV, anchor="mm")
    # How to read it, along the bottom.
    canvas.alpha_composite(nine_slice("panel", 1920 - 72, 138), (36, 920))
    draw.text((960, 968), "Sell ice cream at the stops until you hit the quota, then cross the town line.",
              font=BODY(32), fill=WHITE, anchor="mm")
    draw.text((960, 1014), "Stay out of the sight cones: a patrol that spots the truck gives chase.", font=BODY(32), fill=YEL, anchor="mm")
    canvas.convert("RGB").save(os.path.join(PITCH, "map.png"))
    alone = layer.copy()
    alone_draw = ImageDraw.Draw(alone)
    label(alone_draw, "N", alone.width - 30, 26, 34, WHITE)
    alone_draw.polygon([(alone.width - 30, 44), (alone.width - 40, 62), (alone.width - 20, 62)], fill=WHITE)
    alone.convert("RGB").save(os.path.join(PITCH, "map_only.png"))

    # The minimap in the bottom right corner of the serving-window shot (where the ammo panel was), centered on the truck.
    truck = next(i for i in data["icons"] if i["icon"] == "truck")
    size = 300
    cx, cy = truck["x"] * MAP_SCALE, truck["y"] * MAP_SCALE
    crop = Image.new("RGBA", (size, size), INK + (255,))
    crop.alpha_composite(layer.crop((round(cx - size / 2), round(cy - size / 2), round(cx + size / 2), round(cy + size / 2))))
    shot = Image.open(os.path.join(PITCH, "01_serving_window.png")).convert("RGBA")
    ox, oy = 1920 - 24 - size - 24, 1080 - 24 - size - 24
    shot.alpha_composite(nine_slice("panel_mint", size + 48, size + 48), (ox - 24, oy - 24))
    shot.alpha_composite(crop, (ox, oy))
    shot_draw = ImageDraw.Draw(shot)
    label(shot_draw, "N", ox + size - 18, oy + 20, 26, WHITE)
    shot.convert("RGB").save(os.path.join(PITCH, "01_serving_window_minimap.png"))
    print("wrote map.png, map_only.png and 01_serving_window_minimap.png")


main()
