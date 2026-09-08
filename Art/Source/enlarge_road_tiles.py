"""Resize the tile kit without enlarging its furniture or adding geometry."""
import bpy
from mathutils import Matrix

def enlarge_tiles():
    col=bpy.data.collections['G • Modular ground'];roots=[o for o in col.objects if o.parent is None];report=[]
    positions={'Road_Straight_ROOT':(-37.2,-48.8,0),'Road_Corner_ROOT':(-12.4,-48.8,0),'Road_TJunction_ROOT':(12.4,-48.8,0),'Road_Crossroads_ROOT':(37.2,-48.8,0),'Road_DeadEnd_ROOT':(-37.2,-24,0),'Road_Crosswalk_ROOT':(-12.4,-24,0),'Grass_Cell_ROOT':(12.4,-24,0),'Park_Cell_ROOT':(37.2,-24,0),'Sidewalk_Straight_ROOT':(53,-44,0),'Sidewalk_Corner_ROOT':(53,-27,0),'Curb_Ramp_ROOT':(53,-21,0)}
    for root in roots:
        tiled='grid_size_m' in root
        if tiled:assert root['grid_size_m']==8,root.name
        scale=(3,3,1) if tiled else (1.5,3,1) if root.name=='Sidewalk_Straight_ROOT' else (1.5,1.5,1)
        matrix=Matrix.Diagonal((*scale,1));before=0;after=0
        for ob in list(root.children):
            if ob.type=='MESH':
                ob.data.calc_loop_triangles();before+=len(ob.data.loop_triangles)
                # Bake the horizontal enlargement in root space, leaving object scales at one.
                local=ob.matrix_local.copy();ob.data=ob.data.copy();ob.data.transform(local.inverted() @ matrix @ local);ob.data.update();ob.data.calc_loop_triangles();after+=len(ob.data.loop_triangles)
            else:
                # Park props move apart but retain their original size and shared meshes.
                ob.location.x*=scale[0];ob.location.y*=scale[1]
        assert before==after
        if tiled:root['grid_size_m']=24.
        if root.get('road_ports'):
            root['road_width_m']=12.;root['sidewalk_width_m']=1.5;root['lane_width_m']=6.;root['edge_profile']='12 m road, 1.5 m sidewalks, grass to 24 m tile boundary'
        if root.name=='Grass_Cell_ROOT':
            for key in ['road_width_m','road_ports','edge_profile']:
                if key in root:del root[key]
        if root.name=='Park_Cell_ROOT':root['path_width_m']=4.2
        root.location=positions[root.name];report.append({'root':root.name,'horizontal_scale':scale[:2],'triangles_before':before,'triangles_after':after})
    bpy.context.view_layer.update();return report
