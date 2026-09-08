"""Keep original flat faces faceted when transferring custom normals."""
from mathutils.bvhtree import BVHTree

def restore_flat_faces(mesh,original_vertices,original_faces,original_smooth):
    if all(original_smooth):return
    tree=BVHTree.FromPolygons(original_vertices,original_faces)
    mesh.update();flags=[]
    for p in mesh.polygons:
        flags.append(original_smooth[tree.find_nearest(p.center)[2]] if any(original_smooth) else False)
    old=[n.vector.copy() for n in mesh.corner_normals]
    normals=[old[i] if flags[p.index] else p.normal.copy() for p in mesh.polygons for i in p.loop_indices]
    mesh.normals_split_custom_set(normals)
    for p,flag in zip(mesh.polygons,flags):p.use_smooth=flag
    mesh.update()
