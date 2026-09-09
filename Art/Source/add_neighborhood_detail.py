"""Add neighborhood models to the master workshop and export the new collection."""
import bpy, math, random, shutil
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]
master=R/'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'
backup=R/'Ice Cream Truck Prototype/Library/CodexBackups/BeforeNeighborhoodModels.blend'
backup.parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(master,backup)
bpy.ops.wm.open_mainfile(filepath=str(master))
assert 'K - Neighborhood detail' not in bpy.data.collections
collection=bpy.data.collections.new('K - Neighborhood detail')
bpy.context.scene.collection.children.link(collection)
rng=random.Random(94)
roots=[]
def material(name,color):
    m=bpy.data.materials.new('Neighborhood - '+name)
    m.diffuse_color=(*color,1); m.use_nodes=True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*color,1)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
    return m
bark=material('Bark',(.22,.105,.048)); birch=material('Birch',(.78,.71,.53))
green=material('Cedar',(.065,.22,.13)); leaf=material('Birch leaves',(.27,.46,.09))
rock=material('Slate',(.28,.31,.32)); rocklight=material('Sandstone',(.44,.39,.28))
hedge=material('Shrub',(.16,.34,.12)); flower=material('Flowers',(.72,.28,.38))
grass=material('Meadow',(.29,.43,.16)); grasslight=material('Meadow light',(.37,.48,.2))
blue=material('Blue house',(.24,.4,.49)); coral=material('Coral house',(.64,.3,.23))
trim=material('Porch trim',(.89,.8,.62)); roofing=material('Porch roof',(.24,.22,.2))
root=None

def newroot(name,index):
    global root
    root=bpy.data.objects.new(name,None); collection.objects.link(root)
    root.location=(-18+index%6*8,38+index//6*12,0)
    roots.append(root);return root

def link(obj,name,mat):
    obj.name=name
    for c in list(obj.users_collection):c.objects.unlink(obj)
    collection.objects.link(obj);obj.parent=root
    obj.data.materials.append(mat);return obj

def cube(name,pos,size,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=link(bpy.context.object,name,mat);o.scale=size
    return o

def ico(name,pos,size,mat,sub=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=pos)
    o=link(bpy.context.object,name,mat);o.scale=size
    for v in o.data.vertices:v.co*=rng.uniform(.88,1.1)
    return o

def cone(name,pos,r1,r2,height,mat):
    bpy.ops.mesh.primitive_cone_add(vertices=9,radius1=r1,radius2=r2,depth=height,location=pos)
    return link(bpy.context.object,name,mat)

newroot('Tree_Whitebirch_ROOT',0)
cone('Birch trunk',(0,0,3.5),.25,.14,7,birch)
for z in [1,2,3,4,5]:cube('Birch bark stripe',(0,-.2,z),(.3,.03,.13),bark)
for x,y,z in [(-.65,0,5.3),(.6,.15,6.4),(0,-.3,7.4)]:ico('Birch crown',(x,y,z),(1.4,1.25,1.8),leaf,2)
newroot('Tree_Tallcedar_ROOT',1)
cone('Cedar trunk',(0,0,3.7),.3,.15,7.4,bark)
for z,r in [(3.2,2.1),(4.8,1.75),(6.3,1.3),(7.5,.8)]:cone('Cedar canopy',(0,0,z),r,.12,2.7,green)
for index,(name,size,mat) in enumerate([('Rock_Boulder_ROOT',(1.3,.95,1.2),rock),('Rock_Outcrop_ROOT',(1.8,1.1,1.5),rocklight),('Rock_Cluster_ROOT',(.8,.7,.65),rock)]):
    newroot(name,index+2)
    ico('Weathered rock',(0,0,size[2]*.55),size,mat,1)
    if index==2:
        ico('Small rock',(.9,.2,.27),(.6,.6,.5),rocklight,1)
        ico('Flat rock',(-.65,-.3,.16),(.7,.5,.25),rock,1)
newroot('Shrub_Flowering_ROOT',5)
for x,y,z in [(-.45,0,.4),(.45,.1,.5),(0,-.3,.55)]:ico('Leaf mound',(x,y,z),(.8,.65,.6),hedge,1)
for x,y,z in [(-.6,-.4,.75),(.4,-.4,.85),(.1,.3,1.05),(.7,0,.8)]:ico('Flower bunch',(x,y,z),(.2,.2,.15),flower,1)
newroot('Shrub_Hedge_ROOT',6)
for x in [-.6,0,.6]:ico('Hedge foliage',(x,0,.65),(.65,.65,.8),hedge,1)
for index in range(2):
    newroot('Hill_Grassy'+str(index+1)+'_ROOT',7+index)
    verts=[];faces=[]
    for radius,height in [(3.0,0),(2.5,.55),(1.25,1.25+index*.6),(0,1.6+index*.7)]:
        for i in range(12):
            a=i*math.tau/12
            verts.append((math.cos(a)*radius,math.sin(a)*radius*.72,height))
    for ring in range(3):
        for i in range(12):faces.append((ring*12+i,ring*12+(i+1)%12,(ring+1)*12+(i+1)%12,(ring+1)*12+i))
    mesh=bpy.data.meshes.new('Grassy rise');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new('Grassy rise',mesh);collection.objects.link(o);o.parent=root
    mesh.materials.append(grass);mesh.materials.append(grasslight)
    for p in mesh.polygons:p.material_index=rng.randrange(2)
for index,(source,name,wall) in enumerate([('House_Cottage_ROOT','House_Porchcottage_ROOT',coral),('House_Family_ROOT','House_Tallblue_ROOT',blue)]):
    newroot(name,9+index)
    old=bpy.data.objects[source];mapping={old:root}
    for child in old.children_recursive:
        copy=child.copy()
        if child.type=='MESH':copy.data=child.data.copy()
        collection.objects.link(copy);mapping[child]=copy
    for original,copy in mapping.items():
        if original==old:continue
        copy.parent=mapping[original.parent]
        if copy.type=='MESH':
            for slot in copy.material_slots:
                if slot.material and any(t in slot.material.name.lower() for t in ['wall','plaster','siding']):slot.material=wall
    if index==1:
        root.scale.z=1.22
    else:
        cube('Porch deck',(0,-3.15,.18),(3.7,1.65,.36),trim)
        cube('Porch awning',(0,-3.15,2.8),(3.9,1.8,.2),roofing)
        for x in [-1.65,1.65]:cube('Porch post',(x,-3.8,1.5),(.15,.15,2.7),trim)
# Keep exports independent of the workshop's review transforms.
bpy.ops.object.select_all(action='DESELECT')
for o in collection.all_objects:o.hide_set(False);o.select_set(True)
bpy.context.view_layer.update()
export=R/'Ice Cream Truck Prototype/Assets/Art/NeighborhoodDetails.fbx'
bpy.ops.export_scene.fbx(filepath=str(export),use_selection=True,object_types={'EMPTY','MESH'},apply_unit_scale=True,axis_forward='-Z',axis_up='Y',bake_anim=False,add_leaf_bones=False)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(master))
print('ADDED_MODELS', [o.name for o in roots])
