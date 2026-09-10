"""Export selected workshop geometry without changing the Blender master."""
import bpy,json,re,sys
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'Ice Cream Truck Prototype/Assets/Art/Tycoon/Models'
OUT.mkdir(parents=True,exist_ok=True)
bpy.context.window.scene=bpy.data.scenes['Ice cream truck workshop']
bpy.context.view_layer.update()
entries=json.loads((ROOT/'Art/Previews/ToonKit/inventory.json').read_text())
entries=[e for e in entries if e['group']!='Staff']
entries += [dict(name='Floating '+e['role'],root=e['root'],collection=e['collection']) for e in json.loads((ROOT/'Art/Previews/PeopleStudy/inventory.json').read_text()) if e['direction']=='Floating crew']
source=bpy.context.scene
export=bpy.data.scenes.new('Game export');bpy.context.window.scene=export
report=[];mats={}
for entry in entries:
    if '--cottages' in sys.argv and not entry['name'].startswith('Neighborhood cottage'):continue
    if '--waffle' in sys.argv and entry['name']!='Waffle iron':continue
    if '--truck' in sys.argv and entry['name']!='Ice cream truck':continue
    bpy.context.window.scene=source;bpy.context.view_layer.update()
    root=bpy.data.objects[entry['root']];col=bpy.data.collections[entry['collection']]
    if entry['name']=='Waffle iron':
        for obj in col.objects:
            if obj.type=='EMPTY' and 'Lid_HINGE' in obj.name:obj.rotation_euler.x=0
        bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    wrapper=bpy.data.objects.new('Model',None);export.collection.objects.link(wrapper)
    copies=[]
    for obj in col.objects:
        if obj.type not in {'MESH','FONT'} or (obj.type=='FONT' and not obj.data.body):continue
        if 'outline' in obj.name.lower():continue
        ancestors=[];parent=obj.parent
        while parent:ancestors.append(parent.name);parent=parent.parent
        if '--truck' in sys.argv and (any('InteriorEquipment_ROOT' in n for n in ancestors) or 'RearEntryDoor' in obj.name):continue
        evaluated=obj.evaluated_get(deps)
        mesh=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
        if len(mesh.vertices)==0 or len(mesh.polygons)==0:
            bpy.data.meshes.remove(mesh)
            continue
        prefix='LidPart_' if any('Lid_HINGE' in n for n in ancestors) else ''
        copy=bpy.data.objects.new(prefix+obj.name,mesh);export.collection.objects.link(copy)
        copy.parent=wrapper;copy.matrix_world=Matrix.Translation(-root.matrix_world.translation)@obj.matrix_world
        for mat in mesh.materials:
            if mat:mats[mat.name]=list(mat.diffuse_color)
        copies.append(copy)
    bpy.context.window.scene=export
    bpy.ops.object.select_all(action='DESELECT')
    wrapper.select_set(True)
    for obj in copies:obj.select_set(True)
    bpy.context.view_layer.objects.active=wrapper
    filename=re.sub(r'[^A-Za-z0-9]+','_',entry['name']).strip('_')
    if '--truck' in sys.argv:filename='Truck_shell'
    bpy.ops.export_scene.fbx(filepath=str(OUT/(filename+'.fbx')),use_selection=True,object_types={'MESH','EMPTY'},axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False,use_mesh_modifiers=True)
    report.append(dict(name=entry['name'],file=filename,meshes=len(copies)))
    for obj in copies:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.objects.remove(wrapper,do_unlink=True)
if '--cottages' not in sys.argv and '--waffle' not in sys.argv and '--truck' not in sys.argv:
    (OUT.parent/'Models.json').write_text(json.dumps(dict(models=report,materials=[dict(name=k,color=v) for k,v in mats.items()]),indent=2))
print('TYCOON_EXPORTED',len(report))
