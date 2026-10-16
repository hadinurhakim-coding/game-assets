import bpy
import bmesh
import math
import os
from mathutils import Vector, Matrix

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

col_stands = bpy.data.collections.get("02_Stands_And_Roof")
col_pitch = bpy.data.collections.get("01_Pitch_And_Field")
col_cams = bpy.data.collections.get("05_Stadium_Cameras")

mat_concrete = bpy.data.materials.get("M_Stand_Concrete")
mat_curva_white = bpy.data.materials.get("M_Curva_Sud_White_Seats")
mat_pylon_white = bpy.data.materials.get("M_Pylon_White")
mat_pylon_red = bpy.data.materials.get("M_Pylon_Red")
mat_roof_truss = bpy.data.materials.get("M_Roof_Steel_Dark")

# New PBR material for the red-brick building and curved terrace wall
mat_brick = bpy.data.materials.get("M_Curva_Brick_Building")
if not mat_brick:
    mat_brick = bpy.data.materials.new("M_Curva_Brick_Building")
    mat_brick.use_nodes = True
    bsdf = next(n for n in mat_brick.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.65, 0.28, 0.22, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.75

# Material for blue railing
mat_railing = bpy.data.materials.get("M_Blue_Safety_Railing")
if not mat_railing:
    mat_railing = bpy.data.materials.new("M_Blue_Safety_Railing")
    mat_railing.use_nodes = True
    bsdf = next(n for n in mat_railing.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.22, 0.55, 0.78, 1.0) # Light blue/cyan railing
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Metallic'].default_value = 0.6

# Material for paved open apron
mat_apron = bpy.data.materials.get("M_Paved_Apron_Grey")
if not mat_apron:
    mat_apron = bpy.data.materials.new("M_Paved_Apron_Grey")
    mat_apron.use_nodes = True
    bsdf = next(n for n in mat_apron.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.42, 0.44, 0.46, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.85

# Material for curved terrace seats
mat_terrace_seats = bpy.data.materials.get("M_Curved_Terrace_Seats")
if not mat_terrace_seats:
    mat_terrace_seats = bpy.data.materials.new("M_Curved_Terrace_Seats")
    mat_terrace_seats.use_nodes = True
    bsdf = next(n for n in mat_terrace_seats.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = (0.75, 0.77, 0.80, 1.0) # Weathered concrete stone seats
    bsdf.inputs['Roughness'].default_value = 0.65

# 1. REMOVE OLD STRAIGHT CURVA NORD STAND & OLD CORNER WALLS ON RIGHT SIDE
for ob_name in ["Stand_Curva_Nord", "Corner_Perimeter_Wall_1_1", "Corner_Perimeter_Wall_1_-1", "Stand_Curva_Nord_Curved", "Curva_Nord_Apron", "Curva_Nord_Brick_Building"]:
    ob = bpy.data.objects.get(ob_name)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)

# 2. BUILD CURVED HORSESHOE GRANDSTAND (CURVA NORD)
# Parameters based on authentic aerial photo:
# Arc center at Xc = 28.0m, Yc = 0.0m
# Angle range: from -74 deg (Tribuna side) to +74 deg (Distinti side)
# Inner radius: Rin = 38.0m (Apex at X = 66.0m, ~13.5m behind goal line)
# Outer radius: Rout = 54.0m (Apex at X = 82.0m, radial depth 16m)
# Height: Z_front = 1.8m (front retaining wall), Z_top = 9.8m (top tier)
# 16 concentric tiers, with radial stairways, front wall, rear facade, and safety railing

Xc = 28.0
Yc = 0.0
R_in = 38.0
R_out = 54.0
Z_start = 1.8
Z_top = 9.8
num_tiers = 16
num_radial_segs = 64 # High resolution curve

theta_min = math.radians(-74.0)
theta_max = math.radians(74.0)

bm = bmesh.new()

# Create concentric stepped tiers
d_theta = (theta_max - theta_min) / num_radial_segs
d_r = (R_out - R_in) / num_tiers
d_z = (Z_top - Z_start) / num_tiers

# 5 Radial stairways / aisles at angles
aisle_angles = [math.radians(a) for a in [-50.0, -25.0, 0.0, 25.0, 50.0]]
aisle_half_w = 0.025 # radians

# Build tiers
for t in range(num_tiers):
    r0 = R_in + t * d_r
    r1 = R_in + (t + 1) * d_r
    z0 = Z_start + t * d_z
    z1 = Z_start + (t + 1) * d_z

    for s in range(num_radial_segs):
        ang0 = theta_min + s * d_theta
        ang1 = theta_min + (s + 1) * d_theta
        
        # Check if in aisle
        mid_ang = (ang0 + ang1) / 2
        is_aisle = any(abs(mid_ang - a) < aisle_half_w for a in aisle_angles)
        mat_idx = 1 if is_aisle else 0 # 0: seats, 1: concrete stairway

        # Vertices for riser (vertical face at r0)
        c0, s0 = math.cos(ang0), math.sin(ang0)
        c1, s1 = math.cos(ang1), math.sin(ang1)

        # Riser face: from z0 to z1 at radius r0
        vr1 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z0))
        vr2 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z0))
        vr3 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vr4 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        fr = bm.faces.new((vr1, vr2, vr3, vr4))
        fr.material_index = mat_idx

        # Tread face (horizontal step from r0 to r1 at z1)
        vt1 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        vt2 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vt3 = bm.verts.new((Xc + r1 * c1, Yc + r1 * s1, z1))
        vt4 = bm.verts.new((Xc + r1 * c0, Yc + r1 * s0, z1))
        ft = bm.faces.new((vt1, vt2, vt3, vt4))
        ft.material_index = mat_idx

# Front curved retaining wall (Z = 0.0 to Z = Z_start at radius R_in)
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    
    vf1 = bm.verts.new((Xc + R_in * c0, Yc + R_in * s0, 0.0))
    vf2 = bm.verts.new((Xc + R_in * c1, Yc + R_in * s1, 0.0))
    vf3 = bm.verts.new((Xc + R_in * c1, Yc + R_in * s1, Z_start))
    vf4 = bm.verts.new((Xc + R_in * c0, Yc + R_in * s0, Z_start))
    ff = bm.faces.new((vf1, vf2, vf3, vf4))
    ff.material_index = 2 # Brick / terracotta wall

# Rear curved facade (Z = 0.0 to Z = Z_top at radius R_out)
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    
    vb1 = bm.verts.new((Xc + R_out * c1, Yc + R_out * s1, 0.0))
    vb2 = bm.verts.new((Xc + R_out * c0, Yc + R_out * s0, 0.0))
    vb3 = bm.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top))
    vb4 = bm.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top))
    fb = bm.faces.new((vb1, vb2, vb3, vb4))
    fb.material_index = 1 # Concrete facade

# End caps (side walls at theta_min and theta_max)
for ang, sign in [(theta_min, -1), (theta_max, 1)]:
    ca, sa = math.cos(ang), math.sin(ang)
    for t in range(num_tiers):
        r0 = R_in + t * d_r
        r1 = R_in + (t + 1) * d_r
        z1 = Z_start + (t + 1) * d_z
        
        v1 = bm.verts.new((Xc + r0 * ca, Yc + r0 * sa, 0.0))
        v2 = bm.verts.new((Xc + r1 * ca, Yc + r1 * sa, 0.0))
        v3 = bm.verts.new((Xc + r1 * ca, Yc + r1 * sa, z1))
        v4 = bm.verts.new((Xc + r0 * ca, Yc + r0 * sa, z1))
        if sign > 0:
            fc = bm.faces.new((v1, v2, v3, v4))
        else:
            fc = bm.faces.new((v4, v3, v2, v1))
        fc.material_index = 1

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)

mesh = bpy.data.meshes.new("Stand_Curva_Nord_Curved_Mesh")
bm.to_mesh(mesh)
bm.free()

curva_curved = bpy.data.objects.new("Stand_Curva_Nord_Curved", mesh)
curva_curved.data.materials.append(mat_terrace_seats) # Slot 0: Seats
curva_curved.data.materials.append(mat_concrete)      # Slot 1: Concrete
curva_curved.data.materials.append(mat_brick)         # Slot 2: Brick/Terracotta
col_stands.objects.link(curva_curved)

# 3. ADD CURVED BLUE SAFETY RAILING ALONG TOP RIM (R = R_out, Z = Z_top to Z_top + 1.1m)
bm_rail = bmesh.new()
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    
    # Top bar
    p0 = Vector((Xc + R_out * c0, Yc + R_out * s0, Z_top + 1.1))
    p1 = Vector((Xc + R_out * c1, Yc + R_out * s1, Z_top + 1.1))
    v1 = bm_rail.verts.new(p0)
    v2 = bm_rail.verts.new(p1)
    bm_rail.edges.new((v1, v2))
    
    # Mid bar
    p0m = Vector((Xc + R_out * c0, Yc + R_out * s0, Z_top + 0.55))
    p1m = Vector((Xc + R_out * c1, Yc + R_out * s1, Z_top + 0.55))
    v1m = bm_rail.verts.new(p0m)
    v2m = bm_rail.verts.new(p1m)
    bm_rail.edges.new((v1m, v2m))

    # Vertical post every 4 segments
    if s % 4 == 0:
        vp_bot = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top))
        bm_rail.edges.new((vp_bot, v1))

rail_mesh = bpy.data.meshes.new("Curva_Nord_Railing_Mesh")
bm_rail.to_mesh(rail_mesh)
bm_rail.free()
railing_obj = bpy.data.objects.new("Curva_Nord_Railing", rail_mesh)
railing_obj.data.materials.append(mat_railing)
col_stands.objects.link(railing_obj)

# Skin modifier or bevel curve for railing
mod_skin = railing_obj.modifiers.new("Wire", type='WIREFRAME')
mod_skin.thickness = 0.04

# 4. BUILD LOWER TIERED CURVED WEDGE IN FRONT OF MAIN STAND
# (Visible in Image 2: central lower wedge with 5 steps facing pitch)
bm_low = bmesh.new()
R_low_in = 31.0
R_low_out = 37.0
Z_low_start = 0.3
Z_low_top = 1.8
low_tiers = 5
d_low_r = (R_low_out - R_low_in) / low_tiers
d_low_z = (Z_low_top - Z_low_start) / low_tiers
ang_low_min = math.radians(-32.0)
ang_low_max = math.radians(32.0)
num_low_segs = 28
d_low_ang = (ang_low_max - ang_low_min) / num_low_segs

for t in range(low_tiers):
    r0 = R_low_in + t * d_low_r
    r1 = R_low_in + (t + 1) * d_low_r
    z0 = Z_low_start + t * d_low_z
    z1 = Z_low_start + (t + 1) * d_low_z
    for s in range(num_low_segs):
        a0 = ang_low_min + s * d_low_ang
        a1 = ang_low_min + (s + 1) * d_low_ang
        ca0, sa0 = math.cos(a0), math.sin(a0)
        ca1, sa1 = math.cos(a1), math.sin(a1)
        
        # Riser
        vr1 = bm_low.verts.new((Xc + r0 * ca0, Yc + r0 * sa0, z0))
        vr2 = bm_low.verts.new((Xc + r0 * ca1, Yc + r0 * sa1, z0))
        vr3 = bm_low.verts.new((Xc + r0 * ca1, Yc + r0 * sa1, z1))
        vr4 = bm_low.verts.new((Xc + r0 * ca0, Yc + r0 * sa0, z1))
        bm_low.faces.new((vr1, vr2, vr3, vr4))
        
        # Tread
        vt1 = bm_low.verts.new((Xc + r0 * ca0, Yc + r0 * sa0, z1))
        vt2 = bm_low.verts.new((Xc + r0 * ca1, Yc + r0 * sa1, z1))
        vt3 = bm_low.verts.new((Xc + r1 * ca1, Yc + r1 * sa1, z1))
        vt4 = bm_low.verts.new((Xc + r1 * ca0, Yc + r1 * sa0, z1))
        bm_low.faces.new((vt1, vt2, vt3, vt4))

# Front & Rear of lower wedge
for s in range(num_low_segs):
    a0 = ang_low_min + s * d_low_ang
    a1 = ang_low_min + (s + 1) * d_low_ang
    ca0, sa0 = math.cos(a0), math.sin(a0)
    ca1, sa1 = math.cos(a1), math.sin(a1)
    
    # Front wall
    bm_low.faces.new((
        bm_low.verts.new((Xc + R_low_in * ca0, Yc + R_low_in * sa0, 0.0)),
        bm_low.verts.new((Xc + R_low_in * ca1, Yc + R_low_in * sa1, 0.0)),
        bm_low.verts.new((Xc + R_low_in * ca1, Yc + R_low_in * sa1, Z_low_start)),
        bm_low.verts.new((Xc + R_low_in * ca0, Yc + R_low_in * sa0, Z_low_start))
    ))

bmesh.ops.remove_doubles(bm_low, verts=bm_low.verts, dist=0.01)
low_mesh = bpy.data.meshes.new("Curva_Nord_Lower_Wedge_Mesh")
bm_low.to_mesh(low_mesh)
bm_low.free()
low_obj = bpy.data.objects.new("Curva_Nord_Lower_Wedge", low_mesh)
low_obj.data.materials.append(mat_terrace_seats)
col_stands.objects.link(low_obj)

# 5. BUILD OPEN PAVED / GRAVEL APRON FILLING THE GAP BEHIND PITCH
# (Between X = 54.0 and the curved stand at R_in = 38.0)
bm_ap = bmesh.new()
# Pitch end line at X = 54.0, from Y = -42.0 to +42.0
ap_verts = []
for s in range(num_radial_segs + 1):
    ang = theta_min + s * d_theta
    c, s_val = math.cos(ang), math.sin(ang)
    # Inner curved stand border
    vx_stand = Xc + R_in * c
    vy_stand = Yc + R_in * s_val
    # Pitch edge (clamped to pitch line X = 54.0)
    vx_pitch = 54.0
    vy_pitch = max(-42.0, min(42.0, vy_stand))

    v_p = bm_ap.verts.new((vx_pitch, vy_pitch, 0.005))
    v_s = bm_ap.verts.new((vx_stand, vy_stand, 0.005))
    ap_verts.append((v_p, v_s))

for s in range(num_radial_segs):
    bm_ap.faces.new((
        ap_verts[s][0],
        ap_verts[s+1][0],
        ap_verts[s+1][1],
        ap_verts[s][1]
    ))

bmesh.ops.remove_doubles(bm_ap, verts=bm_ap.verts, dist=0.02)
ap_mesh = bpy.data.meshes.new("Curva_Nord_Apron_Mesh")
bm_ap.to_mesh(ap_mesh)
bm_ap.free()
ap_obj = bpy.data.objects.new("Curva_Nord_Apron", ap_mesh)
ap_obj.data.materials.append(mat_apron)
col_pitch.objects.link(ap_obj)

# 6. BUILD 2-STORY RED BRICK CLUB BUILDING (TRIBUNA CORNER)
# Visible in Image 2: 2-story building with red brick, horizontal windows, curved glass stair tower
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(44.0, -44.0, 4.5))
b_main = bpy.context.object
b_main.name = "Curva_Nord_Brick_Building"
b_main.scale = (18.0, 10.0, 9.0)
bpy.ops.object.transform_apply(scale=True)
b_main.data.materials.append(mat_brick)
col_stands.objects.link(b_main)

# Semi-circular glass stair tower on front of building
bpy.ops.mesh.primitive_cylinder_add(radius=2.5, depth=10.0, location=(38.0, -39.0, 5.0), vertices=24)
stair_tower = bpy.context.object
stair_tower.name = "Curva_Nord_Building_Stair_Tower"
stair_tower.data.materials.append(mat_concrete)
col_stands.objects.link(stair_tower)

# 7. ADD DRONE POV CAMERA MATCHING USER IMAGE 2
drone_cam_name = "Cam_12_Drone_Sinigaglia_Match"
drone_data = bpy.data.cameras.get(drone_cam_name) or bpy.data.cameras.new(drone_cam_name)
drone_cam = bpy.data.objects.get(drone_cam_name) or bpy.data.objects.new(drone_cam_name, drone_data)
if drone_cam.name not in col_cams.objects:
    col_cams.objects.link(drone_cam)

# Drone camera position elevated diagonal overlooking stadium
drone_cam.location = (68.0, -78.0, 46.0)
aim_pt = Vector((0.0, -10.0, 5.0))
dir_v = aim_pt - drone_cam.location
drone_cam.rotation_euler = dir_v.to_track_quat('-Z', 'Y').to_euler()
drone_data.lens = 24.0

# Render Drone view test
bpy.context.scene.camera = drone_cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 620
out_drone = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curved_curva_nord_drone.png"
bpy.context.scene.render.filepath = out_drone
bpy.ops.render.render(write_still=True)
print("Rendered Drone view to:", out_drone)

# Also render from Pitch Penalty Spot (Cam_11_Front_Goal_Right) and Goal Action (Cam_5_Goal_Action)
for cname, out_name in [
    ("Cam_11_Front_Goal_Right", "preview_curved_curva_nord_Cam_11.png"),
    ("Cam_5_Goal_Action", "preview_curved_curva_nord_Cam_5.png"),
    ("Cam_2_Wide_Panorama", "preview_curved_curva_nord_Cam_2.png")
]:
    c_obj = bpy.data.objects.get(cname)
    if c_obj:
        bpy.context.scene.camera = c_obj
        p_path = os.path.join(r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733", out_name)
        bpy.context.scene.render.filepath = p_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {cname} to: {p_path}")

print("Curved Curva Nord construction test complete!")
