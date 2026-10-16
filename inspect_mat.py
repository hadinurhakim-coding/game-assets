import bpy

mat = bpy.data.materials.get("M_Curva_Seats")
print("Material:", mat)
for n in mat.node_tree.nodes:
    if n.type == "TEX_IMAGE":
        print("Image node:", n.name, "image:", n.image.name if n.image else None, "filepath:", n.image.filepath if n.image else None)
        print("Image size:", n.image.size[:] if n.image else None)

stand = bpy.data.objects.get("Stand_Curva_Sud")
print("Stand:", stand, "materials:", [m.name for m in stand.data.materials])

# Check UVs on face 0
bm_uv = stand.data.uv_layers.active
print("UV layer active:", bm_uv.name if bm_uv else None)
for poly in stand.data.polygons[:5]:
    print("Poly", poly.index, "mat_index:", poly.material_index)
    for loop_idx in poly.loop_indices:
        print("  loop", loop_idx, "uv:", stand.data.uv_layers[0].data[loop_idx].uv[:])
