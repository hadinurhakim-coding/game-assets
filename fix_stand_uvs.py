import bpy
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

stand = bpy.data.objects.get("Stand_Curva_Sud")
mesh = stand.data
uv_layer = mesh.uv_layers.active.data
verts = mesh.vertices

# Stand local bounds: X[-37.0, 37.0] Y[56.0, 78.0] Z[0.0, 12.0]
num_tiers = 22
y_start, y_end = 56.0, 78.0
z_start, z_end = 1.2, 12.0
dy = (y_end - y_start) / num_tiers
dz = (z_end - z_start) / num_tiers

for poly in mesh.polygons:
    if poly.material_index == 0: # Seats
        poly_zs = [verts[vi].co.z for vi in poly.vertices]
        poly_ys = [verts[vi].co.y for vi in poly.vertices]
        is_riser = abs(max(poly_ys) - min(poly_ys)) < 0.01 # Vertical riser (constant Y)
        
        avg_z = sum(poly_zs) / len(poly_zs)
        tier_i = int(max(0, min(num_tiers - 1, (avg_z - z_start) / dz)))
        
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            vx, vy, vz = verts[vi].co
            
            # U is across width (X: -37 to +37)
            # Stand has rotation_euler = (0, 0, +90 deg).
            # When rotated +90 deg: world X = -local Y, world Y = +local X.
            # Looking from pitch (-X):
            # viewer left is -world Y = -local X (vx = -37).
            # viewer right is +world Y = +local X (vx = +37).
            # So u = (vx - (-37)) / 74 goes 0.0 (left) to 1.0 (right)!
            u = (vx - (-37.0)) / 74.0
            
            # V goes up the stand (0.0 at bottom, 1.0 at top)
            if is_riser:
                # Vertical face: bottom of riser is tier_i / 22, top is (tier_i + 0.45) / 22
                z_bot = z_start + tier_i * dz
                z_top = z_start + (tier_i + 1) * dz
                frac_z = (vz - z_bot) / max(0.001, (z_top - z_bot))
                v = (tier_i + frac_z * 0.45) / num_tiers
            else:
                # Horizontal tread: front is (tier_i + 0.45) / 22, back is (tier_i + 1.0) / 22
                y_front = y_start + tier_i * dy
                y_back = y_start + (tier_i + 1) * dy
                frac_y = (vy - y_front) / max(0.001, (y_back - y_front))
                v = (tier_i + 0.45 + frac_y * 0.55) / num_tiers
            
            uv_layer[li].uv = (u, v)

mesh.update()

# Set material emission to 0.15 (clean daylight vibrancy)
mat = bpy.data.materials.get("M_Curva_Seats")
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
if 'Emission Strength' in bsdf.inputs:
    bsdf.inputs['Emission Strength'].default_value = 0.15

# Render
cam = bpy.data.objects.get("Cam_User_Curva_1907_Match")
bpy.context.scene.camera = cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_perfect_uv.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered perfect UV to:", preview_path)

# Pack and save
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved blend successfully!")
