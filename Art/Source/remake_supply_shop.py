"""Author the walk-in depot and hanging shop sign in the master workshop."""
import json, math
from pathlib import Path
import bpy

repo = Path(__file__).resolve().parents[2]
bpy.context.window.scene = bpy.data.scenes['Ice cream truck workshop']
entries = json.loads((repo / 'Art/Previews/ToonKit/inventory.json').read_text())
cream, mint, plum, pink, steel = [bpy.data.materials['ArtReview Cel ' + name] for name in
    ['Warm vanilla', 'Mint enamel', 'Plum rubber', 'Strawberry pink', 'Brushed steel']]

def asset(name):
    entry = next(e for e in entries if e['name'] == name)
    root = bpy.data.objects[entry['root']]
    collection = bpy.data.collections[entry['collection']]
    for obj in list(collection.objects):
        if obj != root:
            bpy.data.objects.remove(obj, do_unlink=True)
    return root, collection

def box(name, position, dimensions, material, bevel=.025):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    for col in list(obj.users_collection): col.objects.unlink(obj)
    collection.objects.link(obj)
    obj.name = root.name + ' ' + name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = root; obj.location = position
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new('Soft edges', 'BEVEL'); mod.width = bevel; mod.segments = 2
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return obj

def text(name, body, position, size, material):
    data = bpy.data.curves.new(name, 'FONT'); data.body = body
    data.align_x = 'CENTER'; data.align_y = 'CENTER'; data.size = size; data.extrude = .003
    obj = bpy.data.objects.new(name, data); collection.objects.link(obj)
    obj.parent = root; obj.location = position; obj.rotation_euler = (math.pi/2,0,0)
    data.materials.append(material)

root, collection = asset('Supplier storefront')
box('Floor',(0,0,.10),(6,4,.20),cream)
box('Back wall',(0,1.94,1.75),(6,.12,3.30),mint)
for x in [-2.94,2.94]: box('Side wall',(x,0,1.75),(.12,4,3.30),mint)
for x in [-2.55,2.55]: box('Doorway pier',(x,-1.94,1.75),(.9,.15,3.30),mint)
box('Doorway lintel',(0,-1.94,3.05),(6,.15,.70),mint)
for x in [-2.08,2.08]: box('Doorway trim',(x,-2.035,1.47),(.09,.08,2.55),cream,.01)
box('Open doorway trim',(0,-2.035,2.74),(4.25,.08,.1),cream,.01)
box('Roof',(0,0,3.47),(6.25,4.25,.20),plum,.06)
box('Store sign',(0,-2.055,3.10),(4.85,.12,.55),cream,.045)
text('Supplier name','SCOOP SUPPLY',(0,-2.125,3.10),.34,plum)
# A clear aisle separates the tablet on the left from the collection counter.
box('Collection counter',(1.65,0,.64),(1.95,1.35,.88),mint)
box('Collection worktop',(1.65,0,1.12),(2.05,1.45,.10),cream)
for x in [-2.4,2.4]: box('Stock shelf upright',(x,1.60,1.2),(.08,.50,2.0),steel,.008)
for z in [.58,1.25,1.92]:
    box('Stock shelf',(0,1.60,z),(4.85,.55,.07),cream,.008)
    for i,x in enumerate([-1.9,-1.1,-.3,.5,1.3,2.0]):
        box('Supply carton',(x,1.61,z+.20),(.48,.36,.34),[pink,cream,mint][i%3],.015)
        box('Carton label',(x,1.42,z+.20),(.23,.012,.13),cream,.004)
root['entry']='One permanently open doorway'; root['collection_surface_height_m']=1.17

root, collection = asset('Open closed sign')
box('Hanging frame',(0,0,0),(1.24,.12,.62),mint,.04)
for y in [-.067,.067]: box('Sign face',(0,y,0),(1.12,.025,.50),cream,.025)
for x in [-.43,.43]: box('Hanging strap',(x,0,.45),(.045,.055,.38),plum,.008)
root['display']='Both faces show the same OPEN/CLOSED state in Unity'
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(repo / 'Ice Cream Truck Prototype/Assets/IceCreamTruckWorkshop.blend'))
print('SUPPLY_SHOP_READY: open doorway, collection counter, stock shelves; hanging double-sided sign.')
