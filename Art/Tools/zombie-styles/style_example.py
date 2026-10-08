"""Minimal example of the style module interface (not a real style)."""
from common import *

KEY = "example"
LABEL = "Example"
SHADER = 'candy'
WORLD = "#e9edf2"
FLOOR = "#ffffff"


def make_kit(col, seed):
    return Kit(col, SHADER, seed)


def build_player(kit, root):
    skin = kit.mat("skin", "#ffd0b0")
    # one continuous body: hips -> chest -> neck, legs and arms branching off
    pts = [(0, 0, 0.8), (0, 0, 1.2), (0, 0, 1.35), (0.12, 0, 0.75), (0.12, 0, 0.05), (-0.12, 0, 0.75), (-0.12, 0, 0.05),
           (0.22, 0, 1.18), (0.3, -0.35, 1.1), (-0.22, 0, 1.18), (-0.3, 0, 0.75)]
    edges = [(0, 1), (1, 2), (0, 3), (3, 4), (0, 5), (5, 6), (1, 7), (7, 8), (1, 9), (9, 10)]
    radii = [0.17, 0.2, 0.07, 0.08, 0.06, 0.08, 0.06, 0.06, 0.05, 0.06, 0.05]
    kit.skin("body", pts, edges, radii, kit.mat("shirt", "#8fc8ff"), root)
    kit.prim("head", 'sphere', (0.2, 0.2, 0.2), skin, root, offset=(0, 0, 1.55), segments=24, rings=12)
    gun = kit.empty("held gun", root, (0.3, -0.42, 1.12))
    build_gun(kit, gun)


def build_zombie(kit, root, hit=False):
    build_player(kit, root)


def build_gun(kit, root):
    kit.prim("gun body", 'box', (0.06, 0.2, 0.07), kit.mat("gun", "#8fe3c9"), root, bevel=0.01)
    kit.prim("grip", 'box', (0.05, 0.06, 0.12), kit.mat("grip", "#ff9cc4"), root, offset=(0, 0.07, -0.08), rot=(16, 0, 0), bevel=0.01)
