"""Core zombies from style_H, wrapped as library assets."""
from style_H import *

ASSETS = [
    ("Walker", lambda kit, root: build_zombie(kit, root, hit=False)),
    ("Walker Hit", lambda kit, root: build_zombie(kit, root, hit=True)),
    ("Sprinter", lambda kit, root: build_sprinter(kit, root, hit=False)),
    ("Sprinter Climb", lambda kit, root: build_sprinter(kit, root, climb=True)),
    ("Sprinter Hit", lambda kit, root: build_sprinter(kit, root, hit=True)),
    ("Bloater", lambda kit, root: build_bloater(kit, root, pop=False)),
    ("Bloater Pop", lambda kit, root: build_bloater(kit, root, pop=True)),
]
SPACING = 6
