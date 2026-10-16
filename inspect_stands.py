import bpy

for obj in bpy.data.objects:
    if "Stand" in obj.name or "Curva" in obj.name:
        bbox_x = [round(min(v[0] for v in obj.bound_box), 1), round(max(v[0] for v in obj.bound_box), 1)]
        bbox_y = [round(min(v[1] for v in obj.bound_box), 1), round(max(v[1] for v in obj.bound_box), 1)]
        bbox_z = [round(min(v[2] for v in obj.bound_box), 1), round(max(v[2] for v in obj.bound_box), 1)]
        print(obj.name, "mat:", [m.name for m in obj.data.materials], "bbox_x:", bbox_x, "bbox_y:", bbox_y, "bbox_z:", bbox_z)
