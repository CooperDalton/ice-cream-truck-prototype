"""Example asset batch module."""
from style_H import *

ASSETS = [
    ("Scoop Pistol", build_gun),
    ("Pint", lambda kit, root: tbox(kit, "pint", (0, 0, 0.06), (0.09, 0.09, 0.12), solid(kit, "pint", PINK), root)),
]
SCENES = [dict(name="pistol scene", build=build_gun, cam=((0.5, -0.6, 0.3), (0, 0, 0), 50), res=(800, 600))]
