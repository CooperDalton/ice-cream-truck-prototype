"""Draws the Divorced Dads HUD sprites in the same PS1 candy style as the zombie HUD:
python3 hud_sprites_dads.py -> Zombie Ice Cream Truck/Assets/Art/Sprites/DadsHUD/

Nine-slice frames (borders set by DivorcedDadsSceneBuilder.SpriteBorders, drawn 2x on the 1280 x 720 HUD):
  panel.png          dark panel, pink rim                 slot.png           hotbar slot, lavender rim
  panel_mint.png     dark panel, mint rim                 slot_selected.png  thick pink rim with sprinkles
  panel_gold.png     dark panel, gold rim (Big Dairy)     bar_back.png       progress bar trough
  card.png           big story card, cream rim            banner.png         pink banner with frosting drips (tiled)
Plain sprites: bar_fill.png (candy stripes), bar_fill_mint.png, and 16 x 16 glyphs: sun, moon, badge (heat), note
(jingle), carton (Big Dairy), strike, crosshair, and marker (the tutorial's bobbing arrow, pointing down)."""
import os
from fx_sprites import write_png

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../Zombie Ice Cream Truck/Assets/Art/Sprites/DadsHUD")


def rgba(h, a=255):
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16), a)


CLEAR = (0, 0, 0, 0)
INK, PINK, PINK_L, PINK_D = "#1b1033", "#ff4fa3", "#ff9fd0", "#b0306f"
MINT, MINT_L, MINT_D = "#38f2c3", "#a8ffe8", "#1f9e7a"
GOLD, GOLD_L, GOLD_D = "#ffcf3a", "#fff0a0", "#b8860b"
LAV, LAV_D, WHITE, YEL, BLUE, RED = "#b48cff", "#6a4fb0", "#fff7ee", "#ffe14a", "#2e86ff", "#ff2448"
CREAM, CREAM_D = "#fff2d6", "#e0b98a"


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


SUN = ["................",
       ".......YY.......",
       "...Y...YY...Y...",
       "....Y......Y....",
       "......oooo......",
       ".....oYYYYo.....",
       "YY..oYWYYYYo..YY",
       "YY..oYYYYYYo..YY",
       "....oYYYYYOo....",
       ".....oYYYOo.....",
       "......oooo......",
       "....Y......Y....",
       "...Y...YY...Y...",
       ".......YY.......",
       "................",
       "................"]
MOON = ["................",
        ".....oooo.......",
        "....oLLLo.......",
        "...oLLLo....W...",
        "..oLLLo.........",
        "..oLLo......W...",
        "..oLLo..........",
        "..oLLLo.........",
        "..oLLLLo....W...",
        "...oLLLLooo.....",
        "....oLLLLLLo....",
        ".....ooooooo....",
        "................",
        "................",
        "................",
        "................"]
BADGE = ["................",
         ".......oo.......",
         "......oYYo......",
         ".oooooYYYYooooo.",
         ".oYYYYYYYYYYYYo.",
         "..oYYYBBBBYYYo..",
         "...oYYBWBBYYo...",
         "....oYBBBBYo....",
         "....oYYBBYYo....",
         "...oYYYooYYYo...",
         "...oYYo..oYYo...",
         "..oYYo....oYYo..",
         "..ooo......ooo..",
         "................",
         "................",
         "................"]
NOTE = ["................",
        "........ooooooo.",
        "........oMMMMMo.",
        "........oMooooo.",
        "........oMo..oMo",
        "........oMo..oMo",
        "........oMo..oMo",
        "........oMo..oMo",
        "....oooooMo.oooo",
        "...oMMMMMMooMMMo",
        "...oMMLMMMoMMMMo",
        "...oMMMMMMoooooo",
        "....oooooo......",
        "................",
        "................",
        "................"]
CARTON = ["................",
          "......oooo......",
          ".....oWWWWo.....",
          "....oWWWWWWo....",
          "...oooooooooo...",
          "...oWWKKWWWWo...",
          "...oWKKKWWKWo...",
          "...oWWKWWWKKo...",
          "...oWWWWWWWWo...",
          "...oPPPPPPPPo...",
          "...oPWPWPWPWo...",
          "...oPPPPPPPPo...",
          "...oWKWWWKKWo...",
          "...oooooooooo...",
          "................",
          "................"]
STRIKE = ["................",
          ".oo..........oo.",
          "oRRo........oRRo",
          "oRRRo......oRRRo",
          ".oRRRo....oRRRo.",
          "..oRRRo..oRRRo..",
          "...oRRRooRRRo...",
          "....oRRRRRRo....",
          "....oRRRRRRo....",
          "...oRRRooRRRo...",
          "..oRRRo..oRRRo..",
          ".oRRRo....oRRRo.",
          "oRRRo......oRRRo",
          "oRRo........oRRo",
          ".oo..........oo.",
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
MARKER = ["................",
          "....oooooooo....",
          "....oPWPPPPo....",
          "....oPWPPPPo....",
          "....oPPPPPPo....",
          "....oPPPPPPo....",
          ".oooooPPPPDooooo",
          ".oPPPPPPPPPPPDo.",
          "..oPWPPPPPPPDo..",
          "...oPPPPPPPDo...",
          "....oPPPPPDo....",
          ".....oPPPDo.....",
          "......oPDo......",
          ".......oo.......",
          "................",
          "................"]


def stripes(light, mid, dark):
    fill = canvas(64, 12)
    for y in range(12):
        for x in range(64):
            c = mid if (x + y) // 4 % 2 == 0 else light
            fill[y][x] = rgba(WHITE if y == 2 else c if y > 1 else light) if y < 10 else rgba(dark)
    return fill


def main():
    os.makedirs(OUT, exist_ok=True)
    save("panel.png", frame(32, PINK, PINK_L, PINK_D, INK, 238))
    save("panel_mint.png", frame(32, MINT, MINT_L, MINT_D, INK, 238))
    save("panel_gold.png", frame(32, GOLD, GOLD_L, GOLD_D, INK, 238))
    card = frame(32, CREAM, WHITE, CREAM_D, INK, 244, rim_w=3)
    for x, y, c in ((6, 6, PINK), (25, 6, MINT), (6, 25, YEL), (25, 25, BLUE)):
        card[y][x] = rgba(c)
    save("card.png", card)
    save("slot.png", frame(32, LAV_D, LAV, "#3a2a6e", "#2a1f4f", 225))
    sel = frame(32, PINK, WHITE, PINK_D, "#5a2a6e", 230, rim_w=3)
    for x, y, c in ((5, 5, YEL), (26, 5, MINT), (5, 26, BLUE), (26, 26, WHITE), (6, 5, YEL), (26, 6, MINT)):
        sel[y][x] = rgba(c)
    save("slot_selected.png", sel)
    save("bar_back.png", frame(16, INK, LAV_D, INK, "#2a1f4f", 230, rim_w=1, cut=1))
    save("bar_fill.png", stripes(PINK_L, PINK, PINK_D))
    save("bar_fill_mint.png", stripes(MINT_L, MINT, MINT_D))
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
    save("sun.png", from_rows(SUN, {"o": INK, "Y": YEL, "W": WHITE, "O": "#ff8a3d"}))
    save("moon.png", from_rows(MOON, {"o": INK, "L": "#d8d0ff", "W": WHITE}))
    save("badge.png", from_rows(BADGE, {"o": INK, "Y": GOLD, "B": BLUE, "W": WHITE}))
    save("note.png", from_rows(NOTE, {"o": INK, "M": MINT, "L": MINT_L}))
    save("carton.png", from_rows(CARTON, {"o": INK, "W": WHITE, "K": INK, "P": PINK}))
    save("strike.png", from_rows(STRIKE, {"o": INK, "R": RED}))
    save("crosshair.png", from_rows(CROSS, {"o": INK, "W": WHITE}))
    save("marker.png", from_rows(MARKER, {"o": INK, "P": YEL, "W": WHITE, "D": GOLD_D}))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
