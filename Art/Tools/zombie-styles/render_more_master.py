import bpy, sys, os, importlib, subprocess
sys.path.insert(0, "/tmp/artstyle/v2")
OUT = os.environ["ART_OUT"]
RES = {"lineup": (1600, 900), "pop": (1400, 1000), "truck": (1600, 900), "arsenal": (1400, 1000), "props": (1400, 1000)}
for key, i in (("E", 4), ("H", 7)):
    mod = importlib.import_module(f"style_{key}")
    scene = bpy.data.scenes[f"Zombie demo v2 - {mod.LABEL}"]
    style = bpy.data.collections[f"S{i + 1} {mod.LABEL}"]
    for c in style.children:
        c.hide_render = not c.name.endswith("/ More")
    more = bpy.data.collections[f"S{i + 1} {mod.LABEL} / More"]
    stage_meshes = [o for o in bpy.data.collections[f"S{i + 1} {mod.LABEL} / Review stage"].objects if o.type == 'MESH']
    for shot, res in RES.items():
        for c in more.children:
            c.hide_render = not c.name.lower().endswith(shot)
        for o in stage_meshes:
            o.hide_render = o.name != f"{key} more floor {shot}"
        scene.camera = bpy.data.objects[f"CAM {key} more {shot}"]
        scene.render.resolution_x, scene.render.resolution_y = res
        path = f"{OUT}/{key}_more_{shot}.png"
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if hasattr(mod, "post"):
            mod.post(path)
    p = lambda s: f"{OUT}/{key}_more_{s}.png"
    subprocess.run(["magick", "(", p("lineup"), p("truck"), "+append", ")", "(", p("pop"), p("arsenal"), p("props"),
                    "-resize", "x900", "+append", ")", "-resize", "3200x", "-append", "-resize", "2400x",
                    f"{OUT}/{key}_more_sheet.png"], check=True)
    print("RENDERED", key)
