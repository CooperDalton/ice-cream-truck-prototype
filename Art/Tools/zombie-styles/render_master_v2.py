import bpy, sys, os, importlib, subprocess
sys.path.insert(0, "/tmp/artstyle/v2")
OUT = os.environ["ART_OUT"]
for i, key in enumerate("ABCDEFGHIJ"):
    mod = importlib.import_module(f"style_{key}")
    scene = bpy.data.scenes[f"Zombie demo v2 - {mod.LABEL}"]
    style = bpy.data.collections[f"S{i + 1} {mod.LABEL}"]
    subs = {c.name.split(" / ")[1].lower(): c for c in style.children}
    for shot in ("characters", "gun", "impact"):
        for name, c in subs.items():
            c.hide_render = name != shot
        for f in ("characters", "impact"):
            bpy.data.objects[f"{key} floor {f}"].hide_render = f != shot
        scene.camera = bpy.data.objects[f"CAM {key} {shot}"]
        scene.render.resolution_x, scene.render.resolution_y = (1000, 1000) if shot == "gun" else (1400, 1000)
        path = f"{OUT}/{key}_{shot}.png"
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=scene.name)
        if hasattr(mod, "post"):
            mod.post(path)
    subprocess.run(["magick", f"{OUT}/{key}_characters.png", f"{OUT}/{key}_impact.png", "(", f"{OUT}/{key}_gun.png",
                    "-resize", "x1000", ")", "+append", "-resize", "2400x", f"{OUT}/{key}_sheet.png"], check=True)
    print("RENDERED", key)
