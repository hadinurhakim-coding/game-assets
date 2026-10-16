import bpy

for m in bpy.data.materials:
    if "curva" in m.name.lower():
        print("Material:", m.name)
        for n in m.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                print("  Node:", n.name, "image:", n.image.name if n.image else None, "size:", n.image.size[:] if n.image else None)
