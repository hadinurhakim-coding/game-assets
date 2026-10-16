import bpy

stand = bpy.data.objects.get("Stand_Curva_Sud")
uv_layer = stand.data.uv_layers.active.data

print("Total polygons:", len(stand.data.polygons))
for p in stand.data.polygons:
    if p.material_index == 0: # Seat material
        uvs = [uv_layer[li].uv[:] for li in p.loop_indices]
        z_coords = [(stand.matrix_world @ stand.data.vertices[vi].co).z for vi in p.vertices]
        y_coords = [(stand.matrix_world @ stand.data.vertices[vi].co).y for vi in p.vertices]
        x_coords = [(stand.matrix_world @ stand.data.vertices[vi].co).x for vi in p.vertices]
        print(f"Poly {p.index:2d}: Z [{min(z_coords):4.1f}, {max(z_coords):4.1f}]  X [{min(x_coords):5.1f}, {max(x_coords):5.1f}]  Y [{min(y_coords):5.1f}, {max(y_coords):5.1f}]  UV U:[{min(u[0] for u in uvs):.2f}, {max(u[0] for u in uvs):.2f}]  V:[{min(u[1] for u in uvs):.2f}, {max(u[1] for u in uvs):.2f}]")
