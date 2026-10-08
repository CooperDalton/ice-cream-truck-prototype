"""Add the round-3 extra models for the finalist styles to the master .blend."""
import bpy, sys, math, importlib
sys.path.insert(0, "/tmp/artstyle/v2")
from mathutils import Vector
import common

FINALISTS = {"E": (4, 80), "H": (7, 120)}   # key -> (style index, y offset of the extra-models area)
SHOTS = {
    "lineup": ((0.3, -7.4, 1.7), (0.05, 0, 0.92), 38),
    "pop": ((12.9, -5.2, 1.9), (12.0, 0.2, 1.0), 35),
    "truck": ((37.0, -8.2, 3.6), (30.0, 0.6, 1.4), 32),
    "arsenal": ((51.75, -0.3, 1.2), (50.0, -0.08, 1.07), 45),
    "props": ((61.4, -2.7, 1.45), (60.0, 0.0, 0.35), 40),
}
for key, (i, yoff) in FINALISTS.items():
    mod = importlib.import_module(f"style_{key}")
    style = bpy.data.collections[f"S{i + 1} {mod.LABEL}"]
    scene = bpy.data.scenes[f"Zombie demo v2 - {mod.LABEL}"]
    stage = bpy.data.collections[f"S{i + 1} {mod.LABEL} / Review stage"]
    if f"S{i + 1} {mod.LABEL} / More" in bpy.data.collections:
        raise SystemExit("already added")
    more = bpy.data.collections.new(f"S{i + 1} {mod.LABEL} / More")
    style.children.link(more)
    cols = {}
    for shot in SHOTS:
        c = bpy.data.collections.new(f"S{i + 1} {mod.LABEL} / More / {shot.title()}")
        more.children.link(c)
        cols[shot] = c
    anchor = bpy.data.objects.new(f"{key} more anchor", None)
    more.objects.link(anchor)
    anchor.location = (500 + i * 8, yoff, 0)
    for shot, (loc, target, lens) in SHOTS.items():
        cd = bpy.data.cameras.new(f"CAM {key} more {shot}"); cd.lens = lens; cd.clip_end = 300
        cam = bpy.data.objects.new(f"CAM {key} more {shot}", cd); stage.objects.link(cam)
        cam.location = loc
        cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    fk = common.Kit(stage, getattr(mod, "SHADER", "candy"))
    fm = fk.mat(f"{key} more floor", mod.FLOOR)
    fk.prim(f"{key} more floor lineup", 'cyl', (4.2, 4.2, 0.02), fm, offset=(0.05, 0.6, -0.01), segments=64)
    fk.prim(f"{key} more floor pop", 'cyl', (3.2, 3.2, 0.02), fm, offset=(12.0, 0.4, -0.01), segments=64)
    fk.prim(f"{key} more floor props", 'cyl', (2.4, 2.4, 0.02), fm, offset=(60.0, 0.2, -0.01), segments=64)
    new_stage = [o for o in stage.objects if o.name.startswith(f"CAM {key} more") or o.name.startswith(f"{key} more floor")]

    k = mod.make_kit(cols["lineup"], seed=11)
    mod.build_player(k, k.empty(f"{key} lineup player", None, (-2.25, 0, 0), (0, 0, -6)))
    mod.build_zombie(k, k.empty(f"{key} lineup walker", None, (-0.75, 0, 0), (0, 0, 10)), hit=False)
    mod.build_sprinter(k, k.empty(f"{key} lineup sprinter", None, (0.75, 0, 0), (0, 0, 14)), hit=False)
    mod.build_bloater(k, k.empty(f"{key} lineup bloater", None, (2.35, 0.25, 0), (0, 0, 12)), pop=False)
    k = mod.make_kit(cols["pop"], seed=12)
    mod.build_bloater(k, k.empty(f"{key} pop bloater", None, (12.0, 0.4, 0), (0, 0, 8)), pop=True)
    mod.build_zombie(k, k.empty(f"{key} pop walker", None, (10.85, 0.1, 0), (0, 0, -40)), hit=True)
    mod.build_sprinter(k, k.empty(f"{key} pop sprinter", None, (13.15, 0.0, 0), (0, 0, 48)), hit=True)
    k = mod.make_kit(cols["truck"], seed=13)
    mod.build_truck(k, k.empty(f"{key} truck root", None, (30.0, 0, 0)))
    k = mod.make_kit(cols["arsenal"], seed=14)
    mod.build_gun(k, k.empty(f"{key} arsenal pistol", None, (50.0, -0.2, 1.33)))
    mod.build_shotgun(k, k.empty(f"{key} arsenal shotgun", None, (50.0, 0.0, 0.95)))
    k = mod.make_kit(cols["props"], seed=15)
    mod.build_props(k, k.empty(f"{key} props root", None, (60.0, 0, 0)))

    for ob in list(more.all_objects) + new_stage:
        if ob.parent is None and ob is not anchor:
            ob.parent = anchor
    print("ADDED", key, len(more.all_objects))
bpy.ops.wm.save_mainfile()
