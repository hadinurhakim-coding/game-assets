import bpy

stand = bpy.data.objects.get("Stand_Curva_Sud")
mesh = stand.data
print("Stand_Curva_Sud vertices:", len(mesh.vertices), "polygons:", len(mesh.polygons))

# Print materials
for i, m in enumerate(stand.data.materials):
    print("Slot", i, ":", m.name)

# Count polygons by material
mat_counts = {}
for p in mesh.polygons:
    mat_counts[p.material_index] = mat_counts.get(p.material_index, 0) + 1
print("Polygons by material index:", mat_counts)

# Check UVs of faces with material_index == 0
uv_data = mesh.uv_layers.active.data
u_vals, v_vals = [], []
for p in mesh.polygons:
    if p.material_index == 0:
        for li in p.loop_indices:
            u, v = uv_data[li].uv
            u_vals.append(u)
            v_vals.append(v)

print(f"UV U range: [{min(u_vals):.3f}, {max(u_vals):.3f}]")
print(f"UV V range: [{min(v_vals):.3f}, {max(v_vals):.3f}]")

# Check shader node of M_Curva_Seats
mat = bpy.data.materials.get("M_Curva_Seats")
for n in mat.node_tree.nodes:
    print("Node:", n.name, n.type)
    if n.type == 'TEX_IMAGE':
        print("  image:", n.image.name if n.image else None, "size:", n.image.size[:] if n.image else None)
    if n.type == 'BSDF_PRINCIPLED':
        print("  Base color input connected:", n.inputs['Base Color'].is_linked)
        if n.inputs['Base Color'].is_linked:
            print("  connected to:", n.inputs['Base Color'].links[0].from_node.name)
