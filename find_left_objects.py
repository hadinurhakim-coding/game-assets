import bpy

for o in bpy.data.objects:
    if o.type == 'MESH':
        coords_x = [(o.matrix_world @ v.co).x for v in o.data.vertices]
        if coords_x:
            min_x, max_x = min(coords_x), max(coords_x)
            if min_x < -45:
                coords_y = [(o.matrix_world @ v.co).y for v in o.data.vertices]
                coords_z = [(o.matrix_world @ v.co).z for v in o.data.vertices]
                print(f"{o.name:30} X: [{min_x:6.1f}, {max_x:6.1f}]  Y: [{min(coords_y):6.1f}, {max(coords_y):6.1f}]  Z: [{min(coords_z):5.1f}, {max(coords_z):5.1f}]  mats: {[m.name for m in o.data.materials]}")
