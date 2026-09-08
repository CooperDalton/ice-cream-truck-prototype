"""Shared low-poly cone with a flat, packed waffle color texture."""
from pathlib import Path
import math, struct, zlib
ROOT=Path('/Users/cooperdalton/Ice Cream Truck Prototype')
TEXTURE=ROOT/'Art/Textures/WaffleCone_BaseColor.png'

def write_texture():
    w=h=512;raw=bytearray()
    for y in range(h):
        raw.append(0);v=1-y/(h-1)
        for x in range(w):
            u=x/w
            if v>.93:rgb=(194,122,49)
            elif v>.80:rgb=(227,168,87)
            else:
                t=v/.78
                phases=[9*u+3.6*t,9*u-3.6*t]
                dist=min(abs(p-round(p)) for p in phases)
                line=max(0,min(1,(.062-dist)/.018))
                # Color variation is painted into the image, with no bump input.
                toast=2.5*math.sin(2*math.pi*9*u)*math.sin(2*math.pi*7.2*t)
                base=(237+toast,174+toast,89+toast)
                rgb=tuple(round(a*(1-line)+b*line) for a,b in zip(base,(176,106,41)))
            raw.extend(rgb)
    def chunk(tag,b):return struct.pack('>I',len(b))+tag+b+struct.pack('>I',zlib.crc32(tag+b)&0xffffffff)
    TEXTURE.parent.mkdir(parents=True,exist_ok=True)
    TEXTURE.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>2I5B',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(raw),9))+chunk(b'IEND',b''))

def build_cone_mesh():
    import bpy,bmesh
    name='Shared flat-textured waffle cone'
    if name in bpy.data.meshes:return bpy.data.meshes[name]
    if not TEXTURE.exists():write_texture()
    img=bpy.data.images.load(str(TEXTURE),check_existing=True);img.colorspace_settings.name='sRGB';img.pack()
    mat=bpy.data.materials.new('Waffle cone • flat color texture');mat.use_nodes=True;mat.diffuse_color=(.8,.46,.15,1)
    nodes=mat.node_tree.nodes;bsdf=nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.8
    tex=nodes.new('ShaderNodeTexImage');tex.name='Flat waffle base color';tex.image=img;tex.interpolation='Linear';tex.extension='REPEAT'
    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
    n=20;verts=[];faces=[];uvs=[]
    for radius,z in [(.002,0),(.067,.19),(.064,.19),(.001,.025)]:
        for i in range(n):a=2*math.pi*i/n;verts.append((radius*math.cos(a),radius*math.sin(a),z))
    for layer in range(3):
        for i in range(n):
            j=(i+1)%n;faces.append((layer*n+i,layer*n+j,(layer+1)*n+j,(layer+1)*n+i))
            uvs.append([(i/n,0),((i+1)/n,0),((i+1)/n,.78),(i/n,.78)] if layer==0 else [(0.5,.96 if layer==1 else .875)]*4)
    faces.extend([tuple(reversed(range(n))),tuple(3*n+i for i in range(n))]);uvs.extend([[(.5,.96)]*n,[(.5,.875)]*n])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();mesh.materials.append(mat)
    uv=mesh.uv_layers.new(name='WaffleUV')
    for p,coords in zip(mesh.polygons,uvs):
        p.use_smooth=p.index<n or 2*n<=p.index<3*n
        for loop,co in zip(p.loop_indices,coords):uv.data[loop].uv=co
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));assert all(e.is_manifold for e in bm.edges);bm.to_mesh(mesh);bm.free()
    mesh.calc_loop_triangles();assert len(mesh.vertices)==80 and len(mesh.loop_triangles)==156
    return mesh
