"""Render selected scenes from Codex_ArtStyleStudies.blend (arguments: A..J)."""
import bpy, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'Art/Previews/CodexStyleStudies'
letters=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'ABCDEFGHIJ'
for scene in list(bpy.data.scenes):
    letter=scene.name.split(' / ')[0]
    if letter not in letters or len(letter)!=1: continue
    bpy.context.window.scene=scene
    if scene.render.engine=='CYCLES':
        scene.cycles.device='CPU'
        print('CYCLES DEVICE',scene.cycles.device,flush=True)
    print('RENDERING',scene.name,flush=True)
    bpy.ops.render.render(write_still=True,scene=scene.name)
    print('RENDERED',scene.render.filepath,flush=True)
