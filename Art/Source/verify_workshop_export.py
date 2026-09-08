"""Round-trip the complete GLB and check every exported placement anchor."""
import bpy,json,math
from pathlib import Path
R=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
bpy.ops.wm.open_mainfile(filepath=str(R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'));bpy.context.view_layer.update()
anchors={o.name:o.matrix_world.translation.copy() for o in bpy.context.scene.objects if 'SOCKET' in o.name or 'RoadPort_' in o.name or 'PathPort_' in o.name}
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'Art/Exports/WorkshopModels.glb'));bpy.context.view_layer.update()
errors={name:(bpy.data.objects[name].matrix_world.translation-p).length for name,p in anchors.items()};assert max(errors.values())<.0001
rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE'];assert len(rigs)==6
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
  if o.find_armature():assert all(abs(sum(g.weight for g in v.groups)-1)<.001 for v in o.data.vertices)
assert any(i.packed_file for i in bpy.data.images)
r={'glb_imported_in_fresh_blender_scene':True,'anchors_checked':len(anchors),'maximum_anchor_error_m':max(errors.values()),'armatures':len(rigs),'skin_weights_normalized':True,'finite_vertex_positions':True,'cone_texture_embedded':True}
(R/'Art/Source/final-export-verification.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
