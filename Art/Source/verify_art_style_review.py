"""Reopen the saved master and compare its original objects with the backup."""
import ast
import bpy
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = ast.parse((root / 'Art/Source/build_art_style_review.py').read_text())
fingerprint_node = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'fingerprint')
exec(compile(ast.Module(body=[fingerprint_node], type_ignores=[]), '<fingerprint>', 'exec'))
bpy.ops.wm.open_mainfile(filepath=str(root / 'Art/Source/BeforeArtStyleReview_20260910.blend'))
before = {o.name: fingerprint(o) for o in bpy.data.objects}
bpy.ops.wm.open_mainfile(filepath=str(root / 'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
changed = [name for name, value in before.items() if name not in bpy.data.objects or fingerprint(bpy.data.objects[name]) != value]
assert not changed, changed
gallery = bpy.data.collections['L - Art style alternatives']
assert len(gallery.children) == 12
assert bpy.context.scene.name == 'Ice cream truck workshop'
assert len([o for o in gallery.all_objects if o.type == 'EMPTY' and o.get('style') != 'Original']) == 9
print(json.dumps({'saved_master_verified': True, 'original_objects_unchanged': len(before),
                  'review_collections': len(gallery.children), 'new_variants': 9}))
