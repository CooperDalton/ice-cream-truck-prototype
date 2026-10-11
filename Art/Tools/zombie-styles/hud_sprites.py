"""Draws the PS1 candy HUD sprites: python3 hud_sprites.py -> Zombie Ice Cream Truck/Assets/Art/Sprites/HUD/

Nine-slice frames (borders set by ZombieTruckSceneBuilder.SpriteBorders, drawn 3x on the 1280 x 720 HUD):
  panel.png          dark panel, pink rim                 slot.png           hotbar slot, lavender rim
  panel_mint.png     dark panel, mint rim                 slot_selected.png  thick pink rim with sprinkles
  bar_back.png       health/progress bar trough           banner.png         pink banner with frosting drips (tiled)
Plain sprites: bar_fill.png (candy stripes, filled horizontally), heart, skull, cone, speed, crosshair (16 x 16)."""
import os
from fx_sprites import write_png

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../Zombie Ice Cream Truck/Assets/Art/Sprites/HUD")


def rgba(h, a=255):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), a)


CLEAR = (0, 0, 0, 0)
INK, PINK, PINK_L, PINK_D = "#1b1033", "#ff4fa3", "#ff9fd0", "#b0306f"
MINT, MINT_L, MINT_D = "#38f2c3", "#a8ffe8", "#1f9e7a"
LAV, LAV_D, WHITE, YEL, BLUE, ZG = "#b48cff", "#6a4fb0", "#fff7ee", "#ffe14a", "#2e86ff", "#9cff57"


def canvas(w, h):
    return [[CLEAR] * w for _ in range(h)]


def frame(size, rim, light, dark, fill, fill_a, rim_w=2, cut=2):
    """Rounded pixel rectangle: rim of rim_w px with a bevel line inside it (light top and left, dark bottom and
    right), translucent fill."""
    img = canvas(size, size)
    for y in range(size):
        for x in range(size):
            corner = min(x, size - 1 - x) + min(y, size - 1 - y)
            if corner < cut:
                continue
            edge = min(x, y, size - 1 - x, size - 1 - y)
            if edge < rim_w:
                img[y][x] = rgba(rim)
            elif edge == rim_w:
                img[y][x] = rgba(light if x == rim_w or y == rim_w else dark)
            else:
                img[y][x] = rgba(fill, fill_a)
    return img


def save(name, img):
    write_png(os.path.join(OUT, name), len(img[0]), len(img), img)


def from_rows(rows, palette):
    return [[rgba(palette[c]) if c in palette else CLEAR for c in row] for row in rows]


HEART = ["................",
         "..oooo....oooo..",
         ".oPPPPo..oPPPPo.",
         "oPWWPPPooPPPPPPo",
         "oPWPPPPPPPPPPPPo",
         "oPPPPPPPPPPPPPPo",
         "oPPPPPPPPPPPPPDo",
         ".oPPPPPPPPPPPDo.",
         "..oPPPPPPPPPDo..",
         "...oPPPPPPPDo...",
         "....oPPPPPDo....",
         ".....oPPPDo.....",
         "......oPDo......",
         ".......oo.......",
         "................",
         "................"]
SKULL = ["................",
         "....oooooooo....",
         "...oGGGGGGGGo...",
         "..oGGGLGGGGGGo..",
         "..oGLGGGGGGGGo..",
         "..oGooGGGGooGo..",
         "..oGoRoGGoRoGo..",
         "..oGooGGGGooGo..",
         "..oGGGGooGGGGo..",
         "...oGGGooGGGo...",
         "....oGWGWGWo....",
         "....oGoGoGoo....",
         ".....ooooooo....",
         "................",
         "................",
         "................"]
CONE = [".....oooooo.....",
        "....oMMMMMMo....",
        "...oMLLMMMMMo...",
        "...oMLMMMMMMo...",
        "..oMMMMMMMMMMo..",
        "..oPPPPPPPPPPo..",
        "...oWYWYWYWYo...",
        "...oYWYWYWYWo...",
        "....oWYWYWYo....",
        "....oYWYWYWo....",
        ".....oWYWYo.....",
        ".....oYWYWo.....",
        "......oWYo......",
        "......oYWo......",
        ".......oo.......",
        "................"]
SPEED = ["................",
         "................",
         "....oooooooo....",
         "...oWWWWWWWWo...",
         "..oWWMWWWWYWWo..",
         ".oWWWWWWWWWWWWo.",
         ".oWMWWWWWWWPWWo.",
         ".oWWWWWWWWPWWWo.",
         ".oWWWWWWWPWWWWo.",
         ".oWWWWWWooWWWWo.",
         ".oWWWWWWooWWWWo.",
         "..oWWWWWWWWWWo..",
         "...oooooooooo...",
         "................",
         "................",
         "................"]
CROSS = ["................",
         "......oWWo......",
         "......oWWo......",
         "......oWWo......",
         "......oooo......",
         "................",
         "oooo...oo...oooo",
         "WWWo..oWWo..oWWW",
         "WWWo..oWWo..oWWW",
         "oooo...oo...oooo",
         "................",
         "......oooo......",
         "......oWWo......",
         "......oWWo......",
         "......oWWo......",
         "................"]


def main():
    os.makedirs(OUT, exist_ok=True)
    save("panel.png", frame(32, PINK, PINK_L, PINK_D, INK, 238))
    save("panel_mint.png", frame(32, MINT, MINT_L, MINT_D, INK, 238))
    save("slot.png", frame(32, LAV_D, LAV, "#3a2a6e", "#2a1f4f", 225))
    sel = frame(32, PINK, WHITE, PINK_D, "#5a2a6e", 230, rim_w=3)
    for x, y, c in ((5, 5, YEL), (26, 5, MINT), (5, 26, BLUE), (26, 26, WHITE), (6, 5, YEL), (26, 6, MINT)):
        sel[y][x] = rgba(c)
    save("slot_selected.png", sel)
    save("bar_back.png", frame(16, INK, LAV_D, INK, "#2a1f4f", 230, rim_w=1, cut=1))
    fill = canvas(64, 12)
    for y in range(12):
        for x in range(64):
            c = PINK if (x + y) // 4 % 2 == 0 else PINK_L
            fill[y][x] = rgba(WHITE if y == 2 else c if y > 1 else PINK_L) if y < 10 else rgba(PINK_D)
    save("bar_fill.png", fill)
    banner = canvas(48, 24)
    for y in range(24):
        for x in range(48):
            if y < 2:
                banner[y][x] = rgba(PINK_L)
            elif y < 16:
                banner[y][x] = rgba(PINK if y < 14 else PINK_D)
    for x0, ln in ((2, 5), (9, 3), (14, 7), (22, 4), (29, 6), (36, 3), (41, 5)):   # frosting drips under the band
        for x in range(x0, x0 + 3):
            for y in range(16, 16 + ln):
                banner[y][x] = rgba(PINK_D if y == 15 + ln else PINK)
    for x, y, c in ((5, 6, YEL), (12, 10, MINT), (20, 5, WHITE), (27, 9, BLUE), (34, 6, YEL), (43, 10, WHITE)):
        banner[y][x] = banner[y][x + 1] = rgba(c)
    save("banner.png", banner)
    save("heart.png", from_rows(HEART, {"o": INK, "P": PINK, "W": WHITE, "D": PINK_D}))
    save("skull.png", from_rows(SKULL, {"o": INK, "G": ZG, "L": "#d8ffb0", "R": "#ff2448", "W": WHITE}))
    save("cone.png", from_rows(CONE, {"o": INK, "M": MINT, "L": MINT_L, "P": PINK, "W": "#f0a43a", "Y": "#ffcf5a"}))
    save("speed.png", from_rows(SPEED, {"o": INK, "W": WHITE, "M": MINT, "Y": YEL, "P": PINK}))
    save("crosshair.png", from_rows(CROSS, {"o": INK, "W": WHITE}))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
