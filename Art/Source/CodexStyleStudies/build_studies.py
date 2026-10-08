"""Original Blender style studies. Run with blender -b --python build_studies.py.

Everything is modeled here, including the paper and voxel geometry. No source
assets from the existing workshop are loaded or modified.
"""
import bpy, bmesh, math, random, json, sys
from mathutils import Vector
from pathlib import Path
from math import sin, cos, pi

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'Art/Previews/CodexStyleStudies'
BLEND = ROOT / 'Art/Source/Codex_ArtStyleStudies.blend'
OUT.mkdir(parents=True, exist_ok=True)
random.seed(1047)
bpy.ops.wm.read_factory_settings(use_empty=True)
FONT = bpy.data.fonts.load('/usr/share/fonts/noto/NotoSans-Regular.ttf')
BOLD = bpy.data.fonts.load('/usr/share/fonts/noto/NotoSans-Bold.ttf')

STYLES = [
 ('A','Candy smooth','Pastel shells / marshmallow shapes / sprinkle confetti','candy','#c5d9dc'),
 ('B','Faceted low poly','Long silhouettes / cut planes / scavenged hardware','facet','#202c32'),
 ('C','Ink comic','Three-tone color / heavy ink / graphic impact','comic','#e1c87e'),
 ('D','Vinyl toy','Oversized heads / molded shells / removable joints','vinyl','#a4bdd1'),
 ('E','1950s B-movie','Soda-jerk uniforms / atomic rayguns / printed halftones','retro','#c7b987'),
 ('F','Gummy','Translucent candy / sugar dust / suspended bones','gummy','#293348'),
 ('G','Claymation','Hand-pressed forms / rolled seams / thumbprints','clay','#ba9d9c'),
 ('H','PS1 bright','Hard triangles / pixel textures / electric color','ps1','#25213e'),
 ('I','Paper cutout','Layered cardstock / white sticker edges / torn shapes','paper','#b6c5b6'),
 ('J','Voxel','Stepped silhouettes / chunky pixels / cube debris','voxel','#899fad'),
]

def rgba(h):
    h = h.lstrip('#')
    vals = [int(h[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in vals)+(1,)

def material(name, color, rough=.5, metal=0, kind='', glow=0):
    m=bpy.data.materials.new(name); m.diffuse_color=rgba(color); m.use_nodes=True
    nt=m.node_tree; nt.nodes.clear(); n=nt.nodes; l=nt.links
    out=n.new('ShaderNodeOutputMaterial'); bs=n.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=rgba(color)
    bs.inputs['Roughness'].default_value=rough; bs.inputs['Metallic'].default_value=metal
    l.new(bs.outputs['BSDF'],out.inputs['Surface'])
    if glow:
        bs.inputs['Emission Color'].default_value=rgba(color)
        bs.inputs['Emission Strength'].default_value=glow
    if kind=='gummy':
        bs.inputs['Roughness'].default_value=.19
        bs.inputs['Transmission Weight'].default_value=.72
        bs.inputs['IOR'].default_value=1.39
        bs.inputs['Coat Weight'].default_value=.4
        bs.inputs['Subsurface Weight'].default_value=.06
    if kind in ('candy','vinyl'):
        bs.inputs['Coat Weight'].default_value=.34 if kind=='candy' else .7
        bs.inputs['Coat Roughness'].default_value=.16
    if kind=='clay':
        bs.inputs['Roughness'].default_value=.84
        noise=n.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=32
        noise.inputs['Detail'].default_value=2.5
        bump=n.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.23; bump.inputs['Distance'].default_value=.025
        l.new(noise.outputs['Fac'],bump.inputs['Height']); l.new(bump.outputs['Normal'],bs.inputs['Normal'])
        bs.inputs['Subsurface Weight'].default_value=.04
    if kind in ('comic','retro'):
        diffuse=n.new('ShaderNodeBsdfDiffuse'); diffuse.inputs['Color'].default_value=(.8,.8,.8,1)
        rgb=n.new('ShaderNodeShaderToRGB'); l.new(diffuse.outputs[0],rgb.inputs[0])
        ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.interpolation='CONSTANT'
        ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
        base=rgba(color)
        for i,(pos,mul) in enumerate(((0,.24),(.31,.65),(.62,1.12))):
            e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos)
            e.position=pos; e.color=tuple(min(1,c*mul) for c in base[:3])+(1,)
        l.new(rgb.outputs[0],ramp.inputs[0]); col=ramp.outputs[0]
        if kind=='retro':
            tex=n.new('ShaderNodeTexCoord'); vor=n.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value=53
            l.new(tex.outputs['Generated'],vor.inputs['Vector'])
            dot=n.new('ShaderNodeMath'); dot.operation='LESS_THAN'; dot.inputs[1].default_value=.26
            l.new(vor.outputs['Distance'],dot.inputs[0])
            mix=n.new('ShaderNodeMixRGB'); mix.blend_type='MULTIPLY'; mix.inputs[2].default_value=(.30,.24,.15,1)
            l.new(dot.outputs[0],mix.inputs[0]); l.new(col,mix.inputs[1]); col=mix.outputs[0]
        emit=n.new('ShaderNodeEmission'); l.new(col,emit.inputs[0]); l.new(emit.outputs[0],out.inputs[0])
    if kind=='ps1':
        size=32; im=bpy.data.images.new(name+'_32px',width=size,height=size)
        base=rgba(color); pixels=[]
        for y in range(size):
            for x in range(size):
                t=random.choice((.66,.82,1,1,1.14))
                if (x//4+y//4)%7==0: t*=.8
                pixels.extend([min(1,c*t) for c in base[:3]]+[1])
        im.pixels=pixels; im.pack()
        tex=n.new('ShaderNodeTexImage'); tex.image=im; tex.interpolation='Closest'; tex.projection='BOX'
        coord=n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Generated'],tex.inputs[0]); l.new(tex.outputs[0],bs.inputs['Base Color'])
        bs.inputs['Roughness'].default_value=1
    return m

INK=material('Ink / charcoal','#17202b',1)
INK.use_backface_culling=True
WHITE=material('Lettering / ivory','#fff8e7',1,glow=1)
DARK=material('Lettering / navy','#26303d',1,glow=.6)
for m,color in ((WHITE,'#fff8e7'),(DARK,'#26303d')):
    nt=m.node_tree; nt.nodes.clear()
    emit=nt.nodes.new('ShaderNodeEmission'); emit.inputs[0].default_value=rgba(color)
    out=nt.nodes.new('ShaderNodeOutputMaterial'); nt.links.new(emit.outputs[0],out.inputs[0])

class Builder:
    def __init__(self, style, collection):
        self.style=style; self.coll=collection; self.origin=Vector((0,0,0)); self.prefix=''; self.parts=[]
    def finish(self,o,name,mat):
        o.name=self.prefix+name
        for c in list(o.users_collection): c.objects.unlink(o)
        self.coll.objects.link(o)
        o.location+=self.origin
        if mat: o.data.materials.append(mat)
        self.parts.append(o)
        if self.style in ('comic','retro') and o.type=='MESH' and mat!=INK:
            bpy.context.view_layer.objects.active=o
            bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
            hull=o.copy(); hull.data=o.data.copy(); self.coll.objects.link(hull)
            hull.name=o.name+' / ink contour'; hull.data.materials.clear(); hull.data.materials.append(INK)
            bm=bmesh.new(); bm.from_mesh(hull.data); bm.normal_update()
            for v in bm.verts: v.co+=v.normal*(.019 if self.style=='comic' else .012)
            bmesh.ops.reverse_faces(bm,faces=list(bm.faces)); bm.to_mesh(hull.data); bm.free()
            self.parts.append(hull)
        return o
    def ell(self,name,p,s,mat):
        if self.style=='voxel': return self.vox(name,p,s,mat,'ell')
        if self.style in ('facet','ps1'):
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1 if self.style=='ps1' else 2,radius=1,location=p)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,radius=1,location=p)
        o=bpy.context.object; o.scale=s
        if self.style=='clay':
            for v in o.data.vertices:
                v.co*=1+.025*sin(v.co.x*13+v.co.z*7)+random.uniform(-.009,.009)
        for f in o.data.polygons: f.use_smooth=self.style not in ('facet','ps1')
        return self.finish(o,name,mat)
    def box(self,name,p,s,mat,bevel=.07):
        if self.style=='voxel': return self.vox(name,p,tuple(v/2 for v in s),mat,'box')
        bpy.ops.mesh.primitive_cube_add(size=1,location=p); o=bpy.context.object; o.scale=s
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        if bevel and self.style not in ('facet','ps1','paper'):
            mod=o.modifiers.new('Soft molded edges','BEVEL'); mod.width=bevel; mod.segments=3
            bpy.ops.object.modifier_apply(modifier=mod.name)
            for f in o.data.polygons: f.use_smooth=True
            mod=o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
        return self.finish(o,name,mat)
    def cone(self,name,p,r1,r2,depth,mat,axis=None,verts=None):
        if self.style=='voxel':
            g=.105; direction=Vector(axis or (0,0,1)).normalized(); center=Vector(p)
            reach=max(r1,r2)+depth/2; cells=set()
            for x in range(math.floor((p[0]-reach)/g),math.ceil((p[0]+reach)/g)):
                for y in range(math.floor((p[1]-reach)/g),math.ceil((p[1]+reach)/g)):
                    for z in range(math.floor((p[2]-reach)/g),math.ceil((p[2]+reach)/g)):
                        delta=Vector(((x+.5)*g,(y+.5)*g,(z+.5)*g))-center
                        along=delta.dot(direction)
                        if abs(along)<=max(depth/2,g*.51):
                            radius=r1+(r2-r1)*max(0,min(1,along/depth+.5))
                            if (delta-direction*along).length<=max(radius,g*.65): cells.add((x,y,z))
            if not cells: cells.add(tuple(math.floor(v/g) for v in p))
            return self.cellmesh(name,cells,mat)
        if verts is None: verts=8 if self.style in ('facet','ps1') else 32
        bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=depth,location=p)
        o=bpy.context.object
        if axis: o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler()
        for f in o.data.polygons: f.use_smooth=self.style not in ('facet','ps1','voxel')
        return self.finish(o,name,mat)
    def rod(self,name,a,b,r,mat,r2=None):
        a,b=Vector(a),Vector(b)
        if self.style=='voxel':
            steps=max(2,int((b-a).length/.08)); cells=set()
            for i in range(steps+1):
                v=a.lerp(b,i/steps); rr=r if r2 is None else r+(r2-r)*i/steps
                occupied=self.cells(v,(rr,rr,rr),'ell')
                if not occupied: occupied.add(tuple(math.floor(c/.105) for c in v))
                cells.update(occupied)
            return self.cellmesh(name,cells,mat)
        return self.cone(name,(a+b)/2,r,r if r2 is None else r2,(b-a).length,mat,b-a)
    def curve(self,name,points,r,mat):
        if self.style in ('facet','ps1','voxel'):
            for i in range(len(points)-1): self.rod(name+str(i),points[i],points[i+1],r,mat)
            return
        c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.resolution_u=12; c.bevel_depth=r; c.bevel_resolution=3
        s=c.splines.new('BEZIER'); s.bezier_points.add(len(points)-1)
        for b,p in zip(s.bezier_points,points): b.co=p; b.handle_left_type='AUTO'; b.handle_right_type='AUTO'
        o=bpy.data.objects.new(name,c); self.coll.objects.link(o); o.location=self.origin; c.materials.append(mat); self.parts.append(o); return o
    def poly(self,name,points,depth,y,mat,edge=False):
        # Draw a cardstock silhouette in X/Z, with separate front and back faces.
        n=len(points); verts=[(x,y+d,z) for d in (-depth/2,depth/2) for x,z in points]
        faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); self.coll.objects.link(o)
        if edge:
            cx=sum(p[0] for p in points)/n; cz=sum(p[1] for p in points)/n
            self.poly(name+' / white paper edge',[(cx+(x-cx)*1.06,cz+(z-cz)*1.05) for x,z in points],depth,y+.035,PALETTE['white'])
        return self.finish(o,name,mat)
    def cells(self,p,s,shape):
        g=.105; cells=set()
        for x in range(math.floor((p[0]-s[0])/g),math.ceil((p[0]+s[0])/g)):
            for y in range(math.floor((p[1]-s[1])/g),math.ceil((p[1]+s[1])/g)):
                for z in range(math.floor((p[2]-s[2])/g),math.ceil((p[2]+s[2])/g)):
                    if shape=='box' or sum((((v+.5)*g-c)/r)**2 for v,c,r in zip((x,y,z),p,s))<=1:
                        cells.add((x,y,z))
        return cells
    def vox(self,name,p,s,mat,shape):
        cells=self.cells(p,s,shape)
        if not cells: cells.add(tuple(math.floor(v/.105) for v in p))
        return self.cellmesh(name,cells,mat)
    def cellmesh(self,name,cells,mat):
        g=.105; verts=[]; faces=[]
        dirs=[((1,0,0),((1,0,0),(1,1,0),(1,1,1),(1,0,1))),((-1,0,0),((0,0,1),(0,1,1),(0,1,0),(0,0,0))),((0,1,0),((0,1,0),(0,1,1),(1,1,1),(1,1,0))),((0,-1,0),((1,0,0),(1,0,1),(0,0,1),(0,0,0))),((0,0,1),((1,0,1),(1,1,1),(0,1,1),(0,0,1))),((0,0,-1),((0,0,0),(0,1,0),(1,1,0),(1,0,0)))]
        for x,y,z in cells:
            for (dx,dy,dz),corners in dirs:
                if (x+dx,y+dy,z+dz) not in cells:
                    start=len(verts); verts.extend([((x+a)*g,(y+b)*g,(z+c)*g) for a,b,c in corners]); faces.append(tuple(range(start,start+4)))
        me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update(); o=bpy.data.objects.new(name,me); self.coll.objects.link(o)
        return self.finish(o,name,mat)

def palette(kind):
    colors=dict(skin='#d99769',green='#80bb72',shirt='#65bfc3',pink='#ed8395',pants='#304a68',white='#fff0cf',dark='#342c40',red='#d65a5f',cone='#d8a35f',metal='#bccdd3',yellow='#f6ca5c',bone='#eee6c4')
    changes={
      'candy':dict(skin='#f0b393',green='#a8d2a0',shirt='#97d6d4',pink='#efa3b7',pants='#827baf'),
      'facet':dict(skin='#b08769',green='#798578',shirt='#668d94',pink='#9c5359',pants='#373e4d',white='#d5c8a2',metal='#74838a',red='#732e36'),
      'comic':dict(skin='#e7a657',green='#a1c633',shirt='#24a9bb',pink='#f1426c',pants='#3b3672',yellow='#ffe330'),
      'vinyl':dict(skin='#d49d7f',green='#a2c7a5',shirt='#efae5f',pink='#cb5a77',pants='#324f63'),
      'retro':dict(skin='#deb98a',green='#93a276',shirt='#e7dfbe',pink='#b8443b',pants='#394d51',white='#f4e8ba',metal='#93a4a1'),
      'gummy':dict(skin='#f5ad38',green='#79cd2f',shirt='#ed4866',pink='#ea477e',pants='#d45926',white='#ffeece'),
      'clay':dict(skin='#d2a07e',green='#929d63',shirt='#79978c',pink='#c76b64',pants='#716280',white='#e2cc99'),
      'ps1':dict(skin='#efa43d',green='#7cd629',shirt='#23dae2',pink='#fa3e9c',pants='#633ad3',white='#f0fa9d',metal='#a7bad2'),
      'voxel':dict(skin='#dca677',green='#91b46b',shirt='#50a9af',pink='#df7588',pants='#40597c')}
    colors.update(changes.get(kind,{}))
    return {k:material(kind+' / '+k,v,.29 if kind in ('candy','vinyl') else .65,.55 if k=='metal' else 0,kind if k not in ('dark','bone') else '') for k,v in colors.items()}

def character(b,zombie=False):
    p=PALETTE; k=b.style
    # Different body proportions are authored per direction, not a material swap.
    cfg={
      'candy': (1.35,2.02,2.96,.65,.66,.48,.65),
      'facet': (1.65,2.35,3.45,.46,.38,.35,.50),
      'comic': (1.37,2.13,3.28,.76,.52,.40,.59),
      'vinyl': (1.08,1.65,2.83,.52,.82,.57,.79),
      'retro': (1.57,2.17,3.21,.56,.48,.37,.66),
      'gummy': (1.1,1.77,2.86,.63,.65,.48,.68),
      'clay': (1.28,1.98,3.08,.63,.61,.46,.65),
      'ps1': (1.50,2.20,3.22,.62,.48,.38,.58),
      'voxel': (1.28,1.99,3.09,.65,.60,.46,.63)}
    hip,chest,hz,width,hx,hy,hh=cfg[k]
    if zombie:
        width*=.89; hz-=.16; hx*=1.08; hh*=1.02
    skin=p['green'] if zombie else p['skin']; cloth=p['pink'] if zombie else p['shirt']
    head_y=-.14 if zombie else 0
    # Stance: planted vendor, dragging and reaching zombie.
    for side in (-1,1):
        x=side*.29; knee=(x+(.09*side if zombie else 0),0,hip*.55)
        ankle=(x+(.19*side if zombie else .03*side),-.13 if side==-1 and zombie else .04,.41)
        b.rod('trouser / upper',(x,0,hip),knee,.23,p['pants'],.19)
        b.rod('trouser / lower',knee,ankle,.18,p['pants'],.14)
        if k=='vinyl':
            b.ell('knee ball',knee,(.22,.22,.22),p['metal'])
        b.box('boot',(ankle[0],ankle[1]-.16,.26),(.51,.78,.36),p['dark'],.12)
        b.box('sole',(ankle[0],ankle[1]-.17,.115),(.52,.79,.10),p['white'],.04)
        if k not in ('facet','gummy'):
            for j in range(2): b.box('lace',(ankle[0],ankle[1]-.45,.43+j*.06),(.27,.04,.036),p['white'],.01)
    if k in ('facet','comic','ps1'):
        points=[(-width*.54,hip-.1),(width*.54,hip-.1),(width,chest+.3),(width*.65,chest+.49),(-width*.65,chest+.49),(-width,chest+.3)]
        b.poly('angular work jacket',points,.65,.02,cloth)
    else:
        b.ell('work jacket',(0,0,(hip+chest)/2+.12),(width,.39,(chest-hip)/2+.50),cloth)
    b.rod('neck',(0,head_y,chest+.3),(0,head_y,hz-.28),.21,skin)
    if k=='vinyl':
        b.box('molded bobble head',(0,head_y,hz),(hx*2,hy*2,hh*1.77),skin,.28)
    else: b.ell('head',(0,head_y,hz),(hx,hy,hh),skin)
    for side in (-1,1):
        if not (zombie and side==1): b.ell('ear',(side*hx*.98,head_y-.01,hz-.03),(.14,.13,.22),skin)
    front=head_y-hy
    # Vendor apron and collar retain the same readable role across styles.
    if not zombie:
        b.box('apron bib',(0,-.387,chest-.10),(width*1.15,.085,.67),p['pink'],.1)
        b.box('apron skirt',(0,-.355,hip+.08),(width*1.50,.15,.61),p['pink'],.09)
        b.box('apron hem',(0,-.455,hip-.12),(width*1.48,.055,.10),p['white'],.02)
        for side in (-1,1):
            b.rod('apron strap',(side*width*.38,-.39,chest-.1),(side*width*.56,-.27,chest+.36),.045,p['pink'])
            b.ell('collar',(side*.18,-.38,chest+.32),(.21,.045,.11),p['white'])
        b.box('pocket',(0,-.467,hip+.14),(.38,.042,.22),p['white'],.03)
        b.cone('apron cone badge',(0,-.48,chest-.11),0,.09,.20,p['cone'])
        b.ell('apron scoop badge',(0,-.48,chest+.02),(.125,.065,.10),p['white'])
        # Brown hair at the temples, under a different hat silhouette.
        for side in (-1,1): b.ell('sideburn',(side*hx*.88,head_y+.04,hz+.18),(.095,.11,.22),p['dark'])
        if k=='retro':
            b.poly('paper soda jerk cap',[(-.48,hz+.45),(.5,hz+.45),(.42,hz+.89),(-.35,hz+.96)],.51,.0,p['white'])
            for side in (-1,1): b.ell('bow tie',(side*.13,-.48,chest+.22),(.16,.075,.09),p['red'])
        elif k=='facet':
            b.poly('folded tall cap',[(-.43,hz+.35),(.41,hz+.39),(.32,hz+.94),(-.18,hz+1.01),(-.4,hz+.8)],.54,.05,p['white'])
            b.box('hat band',(0,-.28,hz+.48),(.83,.09,.14),p['pink'],0)
        elif k=='vinyl':
            b.ell('cap shell',(0,.045,hz+hh*.7),(.85,.59,.29),p['shirt'])
            b.ell('cap bill',(.06,-.55,hz+hh*.56),(.64,.41,.095),p['shirt'])
            b.box('cap badge',(0,-.55,hz+hh*.85),(.31,.07,.19),p['white'],.05)
        else:
            b.ell('hat band',(0,0,hz+hh*.76),(hx*.96,hy*.99,.12),p['pink'])
            for x,s in ((-.27,.28),(0,.35),(.28,.25)):
                b.ell('sundae cap',(x,0,hz+hh*.89+.13),(s,.35,s*.7),p['white'])
            b.ell('cherry',(0,-.03,hz+hh+(.3 if k!='voxel' else .23)),(.115,.11,.115),p['red'])
        # Friendly but slightly tired expression.
        for side in (-1,1):
            b.ell('eye',(side*hx*.39,front-.018,hz+.045),(.068,.05,.11),p['dark'])
            b.rod('brow',(side*hx*.39-.07,front+.015,hz+.25),(side*hx*.39+.065,front-.005,hz+.26),.033,p['dark'])
        b.ell('nose',(0,front-.07,hz-.06),(.105,.12,.10),skin)
        b.curve('smile',[(-.17,front-.015,hz-.20),(0,front-.052,hz-.255),(.17,front-.015,hz-.20)],.024,p['dark'])
    else:
        # A missing ear, skewed eyes, split work shirt and an exposed rib patch.
        b.ell('open jaw',(.035,front+.01,hz-.28),(.34,.14,.22),p['dark'])
        for j in range(4):
            b.box('uneven tooth',(-.20+j*.13,front-.13,hz-.20),(.085,.07,.11+(j%2)*.035),p['bone'],.015)
        b.ell('tongue',(.12,front-.12,hz-.405),(.14,.065,.07),p['red'])
        for side in (-1,1):
            ex=side*hx*.41; ez=hz+.09+(side*.06)
            b.ell('eye socket',(ex,front+.025,ez),(.21,.095,.23),p['dark'])
            b.ell('bulging eye',(ex,front-.045,ez),(.155,.10,.17),p['white'])
            b.ell('wandering pupil',(ex+.035*side,front-.14,ez-.025),(.042,.033,.065),p['dark'])
        b.ell('broken nose',(-.04,front-.095,hz-.08),(.10,.14,.105),skin)
        b.ell('exposed brain',(hx*.3,-.01,hz+hh*.91),(.26,.29,.11),p['pink'])
        for j in range(3):
            b.curve('brain fold',[(hx*.3-.15+j*.10,-.20,hz+hh*.93),(hx*.3-.19+j*.10,0,hz+hh+ .04),(hx*.3-.15+j*.10,.18,hz+hh*.95)],.028,p['red'])
        b.poly('torn shirt tail',[(-width*.85,hip+.38),(-width*.66,hip-.19),(-.24,hip+.01),(-.07,hip-.22),(.12,hip+.05),(.39,hip-.11),(width*.7,hip+.42)],.10,-.37,cloth)
        b.ell('rib cavity',(.16,-.37,chest-.23),(.27,.055,.34),p['dark'])
        for j in range(3): b.curve('exposed rib',[(-.045,-.447,chest-.02-j*.16),(.10,-.48,chest-.10-j*.16),(.35,-.42,chest-.075-j*.16)],.044,p['bone'])
        b.rod('loose tie',(-.13,-.47,chest+.18),(-.27,-.48,chest-.37),.074,p['pants'],.13)
        b.curve('brow scar',[(.06,front+.01,hz+.35),(.30,front+.05,hz+.43)],.023,p['red'])
        for j in range(3): b.rod('stitch',(.12+j*.07,front-.01,hz+.32+j*.025),(.10+j*.07,front-.01,hz+.43+j*.025),.012,p['dark'])
    # Articulated limbs and readable mitt-like hands.
    for side in (-1,1):
        shoulder=(side*width*.87,.01,chest+.23)
        elbow=(side*(width+.19),-.09,chest-.27)
        hand=(side*(width+.29),-.30,chest-.70)
        if zombie:
            elbow=(side*(width+.21),-.21,chest-.10 if side==-1 else chest-.31)
            hand=(side*(width+.37),-.69,chest-.11 if side==-1 else chest-.66)
        b.rod('sleeve',shoulder,elbow,.23,cloth,.18)
        if k=='vinyl': b.ell('shoulder joint',shoulder,(.23,.23,.23),p['metal'])
        if k=='vinyl' and zombie and side==1:
            b.cone('exposed arm peg',(elbow[0],elbow[1],elbow[2]-.08),.095,.095,.27,p['metal'])
            elbow=(elbow[0]+.13,elbow[1]-.08,elbow[2]-.28); hand=(hand[0]+.13,hand[1]-.08,hand[2]-.20)
        b.ell('elbow joint',elbow,(.175,.18,.17),skin if k!='vinyl' else p['metal'])
        b.rod('forearm',elbow,hand,.155,skin,.13)
        b.ell('hand',hand,(.205,.17,.22),skin if zombie else p['white'])
        for f in range(3):
            x=hand[0]+(f-1)*.115
            b.rod('finger',(x,hand[1]-.03,hand[2]-.08),(x+.025*side,hand[1]-.12,hand[2]-.27),.052,skin if zombie else p['white'])
        b.ell('thumb',(hand[0]-.17*side,hand[1]-.08,hand[2]+.01),(.085,.09,.14),skin if zombie else p['white'])
    if k=='vinyl':
        b.curve('head mold seam',[(0,head_y+hy+.004,hz-.46),(0,head_y+hy+.005,hz),(0,head_y+hy+.004,hz+.46)],.007,p['white'])
        for side in (-1,1): b.ell('hip joint',(side*.29,-.005,hip),(.23,.23,.22),p['metal'])
    if k=='clay':
        for x,z in ((-.31,chest-.06),(.24,chest+.18),(.27,hz+.29)):
            for ring in range(3):
                pts=[(x+(.035+ring*.018)*cos(a),front-.012 if z>hz else -.398,z+(.05+ring*.025)*sin(a)) for a in [i*pi/12 for i in range(25)]]
                b.curve('pressed fingerprint',pts,.004,skin if z>hz else cloth)
        b.curve('rolled apron seam',[(-.42,-.44,hip-.03),(0,-.48,hip-.05),(.43,-.44,hip-.03)],.026,p['white'])
    if k=='gummy':
        # Opaque candy bones sit inside the transparent torso and limbs.
        b.rod('sugar spine',(0,.06,hip+.03),(0,.06,chest+.3),.085,p['bone'])
        for j in range(4):
            b.curve('suspended sugar rib',[(-.32,0,chest-.08-j*.14),(0,-.08,chest-.16-j*.14),(.32,0,chest-.08-j*.14)],.035,p['bone'])
        for j in range(24):
            a=random.uniform(0,2*pi); zz=random.uniform(hip,hz+hh)
            b.ell('sugar crystal',(.4*cos(a),-.34-.045*sin(a),zz),(.018,.018,.026),p['white'])

def paper_character(b,zombie=False):
    p=PALETTE; skin=p['green'] if zombie else p['skin']; shirt=p['pink'] if zombie else p['shirt']
    def cut(name,pts,y,mat):
        shape=b.poly(name,pts,.045,y,mat,True)
        shape['Construction']='Layered cardstock'
        return shape
    for side in (-1,1):
        x=side*.30
        cut('folded trouser',[(x-.21,.35),(x+.20,.35),(x+.23,1.65),(x-.22,1.61)],.06,p['pants'])
        cut('shoe',[(x-.26,.14),(x+.31,.14),(x+.27,.45),(x-.17,.51),(x-.30,.32)],-.02,p['dark'])
    cut('jacket',[(-.47,1.28),(.5,1.27),(.70,2.46),(.39,2.67),(-.44,2.63),(-.69,2.42)],0,shirt)
    cut('neck',[(-.18,2.48),(.20,2.48),(.20,2.94),(-.17,2.94)],-.01,skin)
    head=[(-.5,2.84),(-.62,3.21),(-.47,3.68),(-.13,3.82),(.43,3.7),(.59,3.43),(.5,2.96),(.19,2.76),(-.24,2.77)]
    if zombie: head=[(x+.1,z-.12) for x,z in head]
    cut('cut head',head,-.12,skin)
    for side in (-1,1):
        x=side*.72
        cut('sleeve',[(x-side*.2,2.49),(x+side*.22,2.38),(x+side*.31,1.97),(x-side*.04,1.85)],-.015,shirt)
        cut('forearm',[(x+side*.02,2.04),(x+side*.29,2.04),(x+side*.37,1.47),(x+side*.09,1.38)],-.035,skin)
        cut('mitten',[(x+side*.10,1.62),(x+side*.40,1.52),(x+side*.41,1.25),(x+side*.15,1.19),(x-side*.02,1.38)],-.07,skin if zombie else p['white'])
    if zombie:
        b.poly('mouth',[(-.23,2.97),(.34,3.0),(.43,2.75),(.03,2.68),(-.27,2.78)],.024,-.19,p['dark'])
        for j in range(4): b.box('paper tooth',(-.14+j*.13,-.218,2.92),(.09,.02,.13),p['white'],0)
        for side in (-1,1):
            b.ell('paper eye',(side*.25+.06,-.205,3.30+side*.055),(.17,.019,.20),p['white'])
            b.ell('ink pupil',(side*.24+.09,-.228,3.29+side*.055),(.04,.01,.075),p['dark'])
        b.poly('torn ribs',[(-.18,2.25),(.36,2.38),(.39,1.88),(.13,1.78),(-.08,1.89)],.02,-.09,p['dark'])
        for j in range(3): b.box('paper ribs',(.15,-.115,2.21-j*.13),(.4,.018,.065),p['bone'],0)
        cut('brain',[(-.08,3.66),(.02,3.86),(.24,3.91),(.38,3.74)],-.135,p['pink'])
    else:
        cut('apron',[(-.31,2.50),(.30,2.50),(.44,1.30),(-.44,1.30)],-.085,p['pink'])
        b.box('pocket',(0,-.128,1.59),(.36,.025,.22),p['white'],0)
        for side in (-1,1): b.ell('ink eye',(side*.22,-.16,3.30),(.052,.015,.095),p['dark'])
        b.poly('nose',[(-.03,3.3),(.08,3.12),(-.07,3.12)],.02,-.195,p['cone'])
        b.curve('ink smile',[(-.17,-.20,3.01),(0,-.21,2.96),(.19,-.20,3.04)],.015,p['dark'])
        cut('folded cap',[(-.52,3.62),(.44,3.62),(.38,4.04),(.03,4.13),(-.4,3.98)],-.08,p['white'])
        b.box('hat stripe',(-.01,-.13,3.70),(.91,.03,.12),p['pink'],0)
        b.ell('paper cherry',(.02,-.13,4.12),(.10,.03,.10),p['red'])

def gun(b):
    p=PALETTE; k=b.style
    if k=='paper':
        b.poly('pistol sticker silhouette',[(-1.10,2.60),(-.58,2.90),(.71,2.81),(1.24,2.54),(1.17,2.14),(.05,2.09),(-.19,1.24),(-.70,1.32),(-.50,2.10),(-.99,2.17)],.075,0,p['shirt'],True)
        b.poly('waffle grip',[(-.56,2.03),(-.05,2.00),(-.24,1.27),(-.69,1.33)],.025,-.06,p['cone'])
        b.poly('paper barrel',[(.13,2.68),(1.11,2.57),(1.12,2.26),(.13,2.28)],.04,-.08,p['white'],True)
        b.ell('pint disc',(-.37,-.1,2.43),(.33,.025,.30),p['pink'])
        b.ell('cream paper scoop',(-.56,-.015,3.01),(.40,.055,.38),p['white'])
        b.ell('cherry',(-.53,-.02,3.36),(.115,.045,.115),p['red'])
        for j in range(3): b.rod('waffle fold',(-.62+j*.13,-.095,1.39),(-.31+j*.1,-.095,1.91),.014,p['white'])
        b.box('muzzle',(.98,-.12,2.43),(.14,.025,.19),p['dark'],0)
        b.poly('trigger guard',[(-.03,2.09),(.30,2.08),(.23,1.74),(-.15,1.69)],.035,-.025,p['pink'])
        return
    # A cone-grip, pint-fed scoop pistol, shown independently at inspection scale.
    if k=='retro':
        b.ell('atomic receiver',(-.18,0,2.40),(.92,.34,.39),p['metal'])
        b.poly('raygun fin',[(-.83,2.58),(-.59,3.14),(-.21,2.76),(.19,2.69)],.12,.05,p['red'])
        for j in range(3): b.cone('cooling ring',(.4+j*.18,0,2.42),.31-j*.035,.31-j*.035,.065,p['red'],(1,0,0))
    elif k=='gummy':
        b.ell('candy receiver',(-.15,0,2.42),(.86,.36,.36),p['shirt'])
        b.rod('suspended sugar barrel',(-.7,0,2.42),(.9,0,2.42),.12,p['bone'])
    else:
        b.box('receiver',(-.27,0,2.40),(1.35,.62,.61),p['shirt'],.19)
        b.box('slide rail',(-.19,0,2.74),(1.43,.41,.12),p['white'],.04)
        b.box('heel bumper',(-.95,0,2.40),(.18,.68,.54),p['pink'],.08)
    b.rod('barrel',(.13,0,2.42),(1.00,0,2.42),.24,p['metal'])
    if k=='voxel':
        b.box('square cone muzzle',(1.01,0,2.42),(.41,.73,.73),p['cone'],0)
        b.box('black bore',(1.23,-.005,2.42),(.025,.38,.38),p['dark'],0)
    else:
        b.cone('waffle muzzle',(.99,0,2.42),.25,.38,.47,p['cone'],(1,0,0))
        b.cone('muzzle rim',(1.235,0,2.42),.375,.375,.09,p['white'],(1,0,0))
        b.cone('dark bore',(1.285,0,2.42),.259,.259,.017,p['dark'],(1,0,0))
        b.cone('inner bore',(1.299,0,2.42),.12,.12,.02,p['pink'],(1,0,0))
    grip=b.box('waffle grip',(-.50,0,1.83),(.48,.47,1.03),p['cone'],.09)
    grip.rotation_euler[1]=.20
    b.box('grip heel',(-.61,0,1.33),(.59,.53,.16),p['pink'],.05)
    for j in range(5):
        z=1.46+j*.145
        b.rod('waffle diagonal',(-.75,-.249,z),(-.29,-.249,z+.25),.017,p['white'])
        b.rod('waffle crosshatch',(-.76,-.255,z+.23),(-.29,-.255,z),.014,p['pink'])
    b.curve('trigger guard',[(-.16,0,2.14),(.34,0,2.07),(.33,0,1.66),(-.36,0,1.64)],.052,p['pink'])
    b.curve('trigger',[(.035,0,2.10),(.035,0,1.88),(-.055,0,1.82)],.038,p['metal'])
    b.cone('flavor selector',(-.40,-.349,2.42),.25,.25,.06,p['pink'],(0,-1,0))
    b.cone('flavor dial insert',(-.40,-.389,2.42),.17,.17,.027,p['white'],(0,-1,0))
    b.rod('selector pointer',(-.40,-.412,2.42),(-.31,-.415,2.52),.025,p['dark'])
    for j in range(3): b.box('vent',(.11+j*.14,-.327,2.48),(.052,.023,.25),p['dark'],.015)
    b.cone('pint hopper',(-.43,0,2.92),.30,.37,.40,p['pink'])
    b.cone('pint collar',(-.43,0,3.11),.38,.38,.08,p['white'])
    if k=='facet':
        b.ell('faceted scoop',(-.43,0,3.21),(.34,.32,.29),p['white'])
    else:
        for j,(r,z) in enumerate(((.33,3.19),(.26,3.34),(.17,3.49))):
            b.ell('soft serve coil',(-.43+j*.028,0,z),(r,r,.16),p['white'])
        b.cone('cream tip',(-.33,0,3.59),.11,0,.22,p['white'])
    b.ell('cherry',(-.30,0,3.76 if k!='facet' else 3.50),(.105,.105,.105),p['red'])
    for j in range(10):
        a=j*2.4; z=3.21+(j%3)*.11
        x=-.43+(.27-(j%3)*.04)*sin(a); y=-.16-abs(.12*cos(a))
        b.rod('sprinkle',(x,y,z),(x+.055,y-.018,z+.06),.017,[p['pink'],p['shirt'],p['yellow']][j%3])
    b.box('rear sight',(-.9,0,2.86),(.14,.24,.13),p['dark'],.02)
    b.box('front sight',(.58,0,2.72),(.10,.11,.12),p['pink'],.02)

def fx(b):
    p=PALETTE; k=b.style
    b.origin=Vector((.2,.45,.15)); b.prefix='FX / '
    if k in ('candy','gummy','clay'):
        for j in range(6):
            x=.62+j*.085; y=-.60+.20*sin(j*2); z=.045
            b.ell('goo drop',(x,y,z),(.13-j*.009,.13-j*.01,.05),p['red'] if k=='gummy' else p['pink'])
        for j in range(8):
            b.ell('floating chunk',(1.04+random.uniform(-.2,.2),-.03+random.uniform(-.2,.2),.35+j*.11),(.06,.055,.075),p['pink'])
    elif k=='comic':
        pts=[]
        for i in range(18):
            a=i*pi/9; r=.46 if i%2==0 else .21
            pts.append((1.07+cos(a)*r,.9+sin(a)*r))
        b.poly('impact burst',pts,.08,.30,p['yellow'])
        for j in range(3): b.rod('speed line',(.76+j*.14,.28,1.10+j*.10),(1.18+j*.12,.28,1.26+j*.10),.022,p['dark'])
    elif k=='retro':
        for j in range(5): b.ell('flat smoke puff',(.85+j*.10,.45,.12+j*.16),(.22,.035,.15),p['white'])
    elif k in ('facet','ps1','paper','voxel'):
        for j in range(7):
            x=.8+random.uniform(-.2,.38); z=.15+j*.10
            if k=='paper':
                b.poly('torn confetti',[(x,z),(x+.11,z+.04),(x+.08,z+.17),(x-.03,z+.15)],.02,.2,p['pink'])
            elif k=='voxel': b.box('cube debris',(x,.1,z),(.13,.13,.13),p['pink'],0)
            else: b.ell('flying shard',(x,.1,z),(.09,.045,.14),p['red'])

def text_object(scene,name,body,pos,size,mat,font=BOLD,align='LEFT',camera=None):
    c=bpy.data.curves.new(name,'FONT'); c.body=body; c.size=size; c.font=font; c.align_x=align
    o=bpy.data.objects.new(name,c); scene.collection.objects.link(o); c.materials.append(mat)
    if camera: o.parent=camera
    o.location=pos
    return o

def aim(o,p):
    direction=Vector(p)-o.location
    o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()

def light(scene,name,pos,energy,color,size,target=(0,0,2)):
    d=bpy.data.lights.new(name,'AREA'); d.energy=energy; d.shape='DISK'; d.size=size; d.color=color
    o=bpy.data.objects.new(name,d); scene.collection.objects.link(o); o.location=pos; aim(o,target)

def setup_scene(letter,title,desc,kind,bg):
    scene=bpy.data.scenes.new(letter+' / '+title); bpy.context.window.scene=scene
    scene.render.engine='BLENDER_EEVEE'
    scene.render.resolution_x=1440; scene.render.resolution_y=960; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.render.image_settings.color_mode='RGBA'
    scene.render.filepath=str(OUT/(letter+'_'+kind+'.png'))
    scene.world=bpy.data.worlds.new(title+' / world'); scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=rgba(bg)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.40
    scene.view_settings.view_transform='AgX' if kind in ('gummy','vinyl','candy','clay','paper','voxel') else 'Standard'
    scene.view_settings.look='AgX - Medium High Contrast' if kind in ('gummy','vinyl','candy','clay','paper','voxel') else 'None'
    scene.view_settings.exposure=0
    if kind=='gummy':
        scene.render.engine='CYCLES'; scene.cycles.samples=64; scene.cycles.use_denoising=True
        scene.cycles.max_bounces=10; scene.cycles.transmission_bounces=7
    if kind=='ps1':
        scene.render.resolution_x=480; scene.render.resolution_y=320
    col=bpy.data.collections.new(letter+' | '+title+' | Models'); scene.collection.children.link(col)
    stagecol=bpy.data.collections.new(letter+' | Studio'); scene.collection.children.link(stagecol)
    b=Builder('candy',stagecol)
    floor=material(kind+' / stage',bg,.82)
    b.box('Cyclorama',(0,0,-.24),(200,200,.30),floor,.0)
    trim=material(kind+' / podium','#eee4ca' if kind in ('retro','paper') else bg,.7)
    for x in (-3.0,0,3.12):
        b.cone('Display plinth',(x,0,-.01),1.26,1.26,.18,trim,verts=64)
        b.cone('Fine plinth edge',(x,0,-.09),1.27,1.27,.025,PALETTE['white'],verts=64)
    # Small museum stand supports the separately displayed weapon.
    b.rod('Gun display stand',(3.12,.13,.11),(3.12,.13,1.7),.028,PALETTE['metal'])
    b.box('Gun stand foot',(3.12,.1,.13),(.61,.38,.05),PALETTE['metal'],.035)
    camera_data=bpy.data.cameras.new(title+' / camera'); camera=bpy.data.objects.new(title+' / camera',camera_data)
    scene.collection.objects.link(camera); camera.location=(5,-28,11.2); aim(camera,(0,0,2.0))
    camera_data.type='ORTHO'; camera_data.ortho_scale=11.8; camera_data.lens=50; scene.camera=camera
    light(scene,'Key / large softbox',(-4,-6,9),1400,(1,.89,.78),6)
    light(scene,'Fill / cool',(5,-3,6),1000,(.76,.88,1),5)
    light(scene,'Rim',(1,5,7),1700,(1,.88,.7),4)
    if kind=='gummy': light(scene,'Candy transmission',(0,3,4),1700,(.9,1,.82),3)
    contrast=WHITE if kind in ('facet','gummy','ps1') else DARK
    # Camera-parented typography remains editable and is included in each render.
    text_object(scene,'Title',letter+' / '+title.upper(),(-5.42,3.18,-10),.31,contrast,camera=camera)
    text_object(scene,'Subtitle',desc,(-5.40,2.84,-10),.134,contrast,FONT,camera=camera)
    text_object(scene,'Series','SCOOP CREW', (5.42,3.30,-10),.14,contrast,align='RIGHT',camera=camera)
    text_object(scene,'Issue','CODEX / STYLE STUDY '+letter,(5.42,3.08,-10),.09,contrast,FONT,'RIGHT',camera)
    for x,heading,sub in ((-3.18,'01 / PLAYER','Ice cream vendor'),(-.16,'02 / ZOMBIE','The late customer'),(2.97,'03 / SCOOP PISTOL','Pint hopper + waffle grip')):
        text_object(scene,'Asset label',heading,(x,-2.72,-10),.16,contrast,align='CENTER',camera=camera)
        text_object(scene,'Asset caption',sub,(x,-2.96,-10),.118,contrast,FONT,'CENTER',camera)
    text_object(scene,'Footer','ORIGINAL 3D MODELS  /  MATERIAL + SILHOUETTE EXPLORATION',(-5.4,-3.42,-10),.095,contrast,FONT,camera=camera)
    text_object(scene,'Footer count',letter+'  /  10',(5.4,-3.42,-10),.095,contrast,FONT,'RIGHT',camera)
    return scene,col

def gallery_scene(sets):
    scene=bpy.data.scenes.new('00 / All ten styles'); bpy.context.window.scene=scene
    scene.world=bpy.data.worlds.new('Gallery world'); scene.world.color=(.15,.15,.15)
    for i,(letter,title,col) in enumerate(sets):
        inst=bpy.data.objects.new(letter+' / '+title,None); inst.instance_type='COLLECTION'; inst.instance_collection=col
        scene.collection.objects.link(inst); inst.location=((i%5)*12,(i//5)*10,0)
        label=text_object(scene,letter+' / style label',letter+' / '+title,(inst.location.x-4.2,inst.location.y-1.5,4.9),.40,DARK)
        label.rotation_euler=(pi/2,0,0)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_distance=35
                area.spaces.active.region_3d.view_location=(24,4,2)
                area.spaces.active.shading.type='MATERIAL'
    return scene

sets=[]; manifests=[]
for letter,title,desc,kind,bg in STYLES:
    PALETTE=palette(kind)
    scene,col=setup_scene(letter,title,desc,kind,bg)
    b=Builder(kind,col)
    for name,x,is_zombie in (('Player',-3,False),('Zombie',0,True)):
        asset=bpy.data.collections.new(letter+' | '+name); col.children.link(asset); b.coll=asset; b.origin=Vector((x,0,.1)); b.prefix=name+' / '
        paper_character(b,is_zombie) if kind=='paper' else character(b,is_zombie)
    asset=bpy.data.collections.new(letter+' | Scoop Pistol'); col.children.link(asset); b.coll=asset; b.origin=Vector((3.12,0,.1)); b.prefix='Pistol / '; gun(b)
    effects=bpy.data.collections.new(letter+' | Style FX'); col.children.link(effects); b.coll=effects; fx(b)
    # Visible properties provide orientation and scope when inspecting the file.
    col['Study']=desc; col['Role']='Original editable art direction models; unrigged'
    sets.append((letter,title,col))
    manifests.append(dict(style=letter,name=title,scene=scene.name,objects=len(col.all_objects),meshes=sum(o.type=='MESH' for o in col.all_objects),vertices=sum(len(o.data.vertices) for o in col.all_objects if o.type=='MESH')))
    print('BUILT',letter,title,manifests[-1],flush=True)

gallery=gallery_scene(sets)
if 'Scene' in bpy.data.scenes and not bpy.data.scenes['Scene'].objects:
    bpy.data.scenes.remove(bpy.data.scenes['Scene'])
# Open directly on the first camera render layout; the gallery is in the scene menu.
bpy.context.window.scene=bpy.data.scenes['A / Candy smooth']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D': area.spaces.active.region_3d.view_perspective='CAMERA'
readme=bpy.data.texts.new('START HERE / Style studies')
readme.write('SCOOP CREW / CODEX STYLE STUDIES\n\nTen original interpretations of the requested A-J styles.\nEach scene contains a player, a zombie, a scoop pistol, style FX and a lit studio.\nChoose scenes A-J for individual views, or 00 / All ten styles for the gallery.\nModels are separated into labeled collections and retain editable component meshes.\nThis is an art direction study, without animation rigs, UV unwraps or game export setup.\nComic / retro Shader to RGB materials use Eevee. Gummy uses Cycles transmission.\nPS1 uses packed 32px textures. Paper is extruded layered geometry. Voxel surfaces are real blocks.\nThe existing workshop and other source files were not loaded or modified.\n\nGenerator: Art/Source/CodexStyleStudies/build_studies.py\nRenders: Art/Previews/CodexStyleStudies/\n')
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND),compress=True)
(OUT/'manifest.json').write_text(json.dumps(manifests,indent=2)+'\n')
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--build-only' not in args:
    only=args[args.index('--only')+1] if '--only' in args else 'ABCDEFGHIJ'
    for letter,title,desc,kind,bg in STYLES:
        if letter not in only: continue
        scene=bpy.data.scenes[letter+' / '+title]; bpy.context.window.scene=scene
        print('RENDERING',letter,flush=True)
        bpy.ops.render.render(write_still=True,scene=scene.name)
        print('RENDERED',scene.render.filepath,flush=True)
