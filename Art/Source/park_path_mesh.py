"""Create the park crossing as one solid mesh with a continuous top."""
import bpy

def create_park_path(root, collection, material, size, width):
    a, b = size / 2, width / 2
    outline = [(-b,-a),(b,-a),(b,-b),(a,-b),(a,b),(b,b),
               (b,a),(-b,a),(-b,b),(-a,b),(-a,-b),(-b,-b)]
    vertices = [(x,y,z) for z in (.064,.092) for x,y in outline]
    faces = [tuple(reversed(range(12))), tuple(range(12,24))]
    faces += [(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
    mesh = bpy.data.meshes.new('Park continuous crossing mesh')
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new('Park continuous crossing', mesh)
    collection.objects.link(obj)
    obj.parent = root
    return obj
