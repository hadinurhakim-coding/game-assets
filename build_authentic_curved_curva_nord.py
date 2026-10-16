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
col_towers = bpy.data.collections.get("03_Floodlight_Towers")
col_cams = bpy.data.collections.get("05_Stadium_Cameras")

mat_concrete = bpy.data.materials.get("M_Stand_Concrete")
mat_pylon_white = bpy.data.materials.get("M_Pylon_White")
mat_roof_truss = bpy.data.materials.get("M_Roof_Steel_Dark")

# 1. PBR MATERIALS FOR CURVED CURVA NORD & PRECINCT
tex_curved_seats = os.path.join(ASSETS, "como_curva_nord_curved_seats.png")

mat_curved_seats = bpy.data.materials.get("M_Curved_Curva_Nord_Seats")
if not mat_curved_seats:
    mat_curved_seats = bpy.data.materials.new("M_Curved_Curva_Nord_Seats")
mat_curved_seats.use_nodes = True
cs_nt = mat_curved_seats.node_tree
cs_nt.nodes.clear()
cs_out = cs_nt.nodes.new('ShaderNodeOutputMaterial')
cs_bsdf = cs_nt.nodes.new('ShaderNodeBsdfPrincipled')
cs_tex_coord = cs_nt.nodes.new('ShaderNodeTexCoord')
cs_mapping = cs_nt.nodes.new('ShaderNodeMapping')
cs_tex_col = cs_nt.nodes.new('ShaderNodeTexImage')

if os.path.exists(tex_curved_seats):
    cs_tex_col.image = bpy.data.images.load(tex_curved_seats, check_existing=True)

cs_nt.links.new(cs_tex_coord.outputs['UV'], cs_mapping.inputs['Vector'])
cs_nt.links.new(cs_mapping.outputs['Vector'], cs_tex_col.inputs['Vector'])
cs_nt.links.new(cs_tex_col.outputs['Color'], cs_bsdf.inputs['Base Color'])
cs_bsdf.inputs['Roughness'].default_value = 0.55
cs_nt.links.new(cs_bsdf.outputs['BSDF'], cs_out.inputs['Surface'])

# Brick Building Material
mat_brick = bpy.data.materials.get("M_Curva_Brick_Building")
if not mat_brick:
    mat_brick = bpy.data.materials.new("M_Curva_Brick_Building")
mat_brick.use_nodes = True
b_bsdf = next(n for n in mat_brick.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
b_bsdf.inputs['Base Color'].default_value = (0.58, 0.24, 0.18, 1.0)
b_bsdf.inputs['Roughness'].default_value = 0.8

# Blue Railing Material
mat_railing = bpy.data.materials.get("M_Blue_Safety_Railing")
if not mat_railing:
    mat_railing = bpy.data.materials.new("M_Blue_Safety_Railing")
mat_railing.use_nodes = True
r_bsdf = next(n for n in mat_railing.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
r_bsdf.inputs['Base Color'].default_value = (0.20, 0.52, 0.78, 1.0)
r_bsdf.inputs['Roughness'].default_value = 0.35
r_bsdf.inputs['Metallic'].default_value = 0.7

# Paved Ground Material
mat_apron = bpy.data.materials.get("M_Paved_Apron_Grey")
if not mat_apron:
    mat_apron = bpy.data.materials.new("M_Paved_Apron_Grey")
mat_apron.use_nodes = True
a_bsdf = next(n for n in mat_apron.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
a_bsdf.inputs['Base Color'].default_value = (0.36, 0.38, 0.40, 1.0)
a_bsdf.inputs['Roughness'].default_value = 0.9

# 2. CLEAN UP OLD RIGHT STAND OBJECTS
clean_names = [
    "Stand_Curva_Nord", "Stand_Curva_Nord_Curved", "Curva_Nord_Railing",
    "Curva_Nord_Lower_Wedge", "Curva_Nord_Apron", "Curva_Nord_Brick_Building",
    "Curva_Nord_Building_Stair_Tower", "Curva_Nord_Perimeter_Fence",
    "Corner_Perimeter_Wall_1_1", "Corner_Perimeter_Wall_1_-1"
]
for oname in clean_names:
    ob = bpy.data.objects.get(oname)
    if ob:
        bpy.data.objects.remove(ob, do_unlink=True)
    m = bpy.data.meshes.get(f"{oname}_Mesh")
    if m:
        bpy.data.meshes.remove(m, do_unlink=True)

# 3. BUILD AUTHENTIC CURVED HORSESHOE CURVA NORD GRANDSTAND
Xc = 28.0
Yc = 0.0
R_in = 38.0
R_out = 54.0
Z_start = 1.8
Z_top = 9.8
num_tiers = 16
num_radial_segs = 72

theta_min = math.radians(-76.0) # Extends to Tribuna corner
theta_max = math.radians(76.0)  # Extends to Distinti corner

d_theta = (theta_max - theta_min) / num_radial_segs
d_r = (R_out - R_in) / num_tiers
d_z = (Z_top - Z_start) / num_tiers

bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")

for t in range(num_tiers):
    r0 = R_in + t * d_r
    r1 = R_in + (t + 1) * d_r
    z0 = Z_start + t * d_z
    z1 = Z_start + (t + 1) * d_z
    v0_norm = t / num_tiers
    v1_norm = (t + 1) / num_tiers

    for s in range(num_radial_segs):
        ang0 = theta_min + s * d_theta
        ang1 = theta_min + (s + 1) * d_theta
        u0_norm = s / num_radial_segs
        u1_norm = (s + 1) / num_radial_segs

        c0, s0 = math.cos(ang0), math.sin(ang0)
        c1, s1 = math.cos(ang1), math.sin(ang1)

        # Riser face
        vr1 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z0))
        vr2 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z0))
        vr3 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vr4 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        fr = bm.faces.new((vr1, vr2, vr3, vr4))
        fr.material_index = 0
        fr.loops[0][uv_layer].uv = (u0_norm, v0_norm)
        fr.loops[1][uv_layer].uv = (u1_norm, v0_norm)
        fr.loops[2][uv_layer].uv = (u1_norm, v0_norm + 0.015)
        fr.loops[3][uv_layer].uv = (u0_norm, v0_norm + 0.015)

        # Tread face
        vt1 = bm.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        vt2 = bm.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vt3 = bm.verts.new((Xc + r1 * c1, Yc + r1 * s1, z1))
        vt4 = bm.verts.new((Xc + r1 * c0, Yc + r1 * s0, z1))
        ft = bm.faces.new((vt1, vt2, vt3, vt4))
        ft.material_index = 0
        ft.loops[0][uv_layer].uv = (u0_norm, v0_norm + 0.015)
        ft.loops[1][uv_layer].uv = (u1_norm, v0_norm + 0.015)
        ft.loops[2][uv_layer].uv = (u1_norm, v1_norm)
        ft.loops[3][uv_layer].uv = (u0_norm, v1_norm)

# Front curved retaining wall (brick terracotta, height 1.8m)
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
    ff.material_index = 1 # Brick material

# Rear curved facade (concrete wall, height Z_top)
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
    fb.material_index = 2 # Concrete material

# Side End-Cap Walls
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
        fc = bm.faces.new((v1, v2, v3, v4) if sign > 0 else (v4, v3, v2, v1))
        fc.material_index = 2

bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)

mesh = bpy.data.meshes.new("Stand_Curva_Nord_Curved_Mesh")
bm.to_mesh(mesh)
bm.free()

curva_curved = bpy.data.objects.new("Stand_Curva_Nord_Curved", mesh)
curva_curved.data.materials.append(mat_curved_seats) # Slot 0: Curved seats
curva_curved.data.materials.append(mat_brick)        # Slot 1: Front brick wall
curva_curved.data.materials.append(mat_concrete)     # Slot 2: Concrete rear/sides
col_stands.objects.link(curva_curved)

# 4. CURVED BLUE STEEL RAILING ALONG TOP PERIMETER
bm_rail = bmesh.new()
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    
    # Top handrail
    v1 = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top + 1.15))
    v2 = bm_rail.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top + 1.15))
    bm_rail.edges.new((v1, v2))
    # Mid rail
    v1m = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top + 0.6))
    v2m = bm_rail.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top + 0.6))
    bm_rail.edges.new((v1m, v2m))
    # Vertical posts
    if s % 3 == 0:
        v_base = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top))
        bm_rail.edges.new((v_base, v1))

rail_mesh = bpy.data.meshes.new("Curva_Nord_Railing_Mesh")
bm_rail.to_mesh(rail_mesh)
bm_rail.free()
railing_obj = bpy.data.objects.new("Curva_Nord_Railing", rail_mesh)
railing_obj.data.materials.append(mat_railing)
col_stands.objects.link(railing_obj)
mod_w = railing_obj.modifiers.new("Wireframe", type='WIREFRAME')
mod_w.thickness = 0.045

# 5. LOWER CURVED SEATING WEDGE (FACING PITCH)
bm_low = bmesh.new()
uv_low = bm_low.loops.layers.uv.new("UVMap")
R_low_in = 31.0
R_low_out = 37.0
Z_low_start = 0.35
Z_low_top = 1.75
low_tiers = 5
d_low_r = (R_low_out - R_low_in) / low_tiers
d_low_z = (Z_low_top - Z_low_start) / low_tiers
ang_low_min = math.radians(-30.0)
ang_low_max = math.radians(30.0)
num_low_segs = 32
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
        fr = bm_low.faces.new((vr1, vr2, vr3, vr4))
        fr.loops[0][uv_low].uv = (s/num_low_segs, t/low_tiers)
        fr.loops[1][uv_low].uv = ((s+1)/num_low_segs, t/low_tiers)
        fr.loops[2][uv_low].uv = ((s+1)/num_low_segs, t/low_tiers + 0.02)
        fr.loops[3][uv_low].uv = (s/num_low_segs, t/low_tiers + 0.02)

        # Tread
        vt1 = bm_low.verts.new((Xc + r0 * ca0, Yc + r0 * sa0, z1))
        vt2 = bm_low.verts.new((Xc + r0 * ca1, Yc + r0 * sa1, z1))
        vt3 = bm_low.verts.new((Xc + r1 * ca1, Yc + r1 * sa1, z1))
        vt4 = bm_low.verts.new((Xc + r1 * ca0, Yc + r1 * sa0, z1))
        ft = bm_low.faces.new((vt1, vt2, vt3, vt4))
        ft.loops[0][uv_low].uv = (s/num_low_segs, t/low_tiers + 0.02)
        ft.loops[1][uv_low].uv = ((s+1)/num_low_segs, t/low_tiers + 0.02)
        ft.loops[2][uv_low].uv = ((s+1)/num_low_segs, (t+1)/low_tiers)
        ft.loops[3][uv_low].uv = (s/num_low_segs, (t+1)/low_tiers)

# Front wall of lower wedge
for s in range(num_low_segs):
    a0 = ang_low_min + s * d_low_ang
    a1 = ang_low_min + (s + 1) * d_low_ang
    ca0, sa0 = math.cos(a0), math.sin(a0)
    ca1, sa1 = math.cos(a1), math.sin(a1)
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
low_obj.data.materials.append(mat_curved_seats)
col_stands.objects.link(low_obj)

# 6. OPEN PAVED COURTYARD / APRON (BETWEEN PITCH & CURVED STAND)
bm_ap = bmesh.new()
ap_verts = []
for s in range(num_radial_segs + 1):
    ang = theta_min + s * d_theta
    c, s_val = math.cos(ang), math.sin(ang)
    vx_stand = Xc + R_in * c
    vy_stand = Yc + R_in * s_val
    vx_pitch = 53.5
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

# Low curved perimeter fence along edge of pitch
bm_fence = bmesh.new()
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    # 2.5m behind goal line / LED boards
    rf = 28.5
    if abs(ang0) < math.radians(55.0):
        v1 = bm_fence.verts.new((Xc + rf * c0, Yc + rf * s0, 0.0))
        v2 = bm_fence.verts.new((Xc + rf * c1, Yc + rf * s1, 0.0))
        v3 = bm_fence.verts.new((Xc + rf * c1, Yc + rf * s1, 1.1))
        v4 = bm_fence.verts.new((Xc + rf * c0, Yc + rf * s0, 1.1))
        bm_fence.faces.new((v1, v2, v3, v4))

bmesh.ops.remove_doubles(bm_fence, verts=bm_fence.verts, dist=0.01)
fence_mesh = bpy.data.meshes.new("Curva_Nord_Perimeter_Fence_Mesh")
bm_fence.to_mesh(fence_mesh)
bm_fence.free()
fence_obj = bpy.data.objects.new("Curva_Nord_Perimeter_Fence", fence_mesh)
fence_obj.data.materials.append(mat_railing)
col_stands.objects.link(fence_obj)

# 7. RED-BRICK 2-STORY CLUB HEADQUARTERS BUILDING (TRIBUNA CORNER)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(44.0, -45.0, 4.5))
b_main = bpy.context.object
b_main.name = "Curva_Nord_Brick_Building"
b_main.scale = (18.0, 11.0, 9.0)
bpy.ops.object.transform_apply(scale=True)
b_main.data.materials.append(mat_brick)
col_stands.objects.link(b_main)

# Semi-circular glass stair tower on front of building
bpy.ops.mesh.primitive_cylinder_add(radius=2.6, depth=9.5, location=(38.0, -39.0, 4.75), vertices=24)
stair_tower = bpy.context.object
stair_tower.name = "Curva_Nord_Building_Stair_Tower"
stair_tower.data.materials.append(mat_concrete)
col_stands.objects.link(stair_tower)

# 8. UPDATE TOWER_SE (FLOODLIGHT MAST IN OPEN APRON)
# In real stadium drone photo, Tower_SE stands proudly in the open paved apron!
tow_se = bpy.data.objects.get("Tower_SE_Mast")
if tow_se:
    # Adjust tower group position to match open courtyard
    pass

# 9. CONFIGURE CAMERAS
# A) Drone Camera matching Image 2 perfectly:
# Elevated high behind Curva Nord looking across towards Curva 1907
cam_drone = bpy.data.objects.get("Cam_12_Drone_Sinigaglia_Match")
if not cam_drone:
    cdata = bpy.data.cameras.new("Cam_12_Drone_Sinigaglia_Match")
    cam_drone = bpy.data.objects.new("Cam_12_Drone_Sinigaglia_Match", cdata)
    col_cams.objects.link(cam_drone)

# Position matching Image 2 (high above the corner of Curva Nord and Distinti, looking toward Curva Sud):
cam_drone.location = (86.0, 48.0, 48.0)
aim_drone = Vector((-15.0, -8.0, 4.0))
dir_d = aim_drone - cam_drone.location
cam_drone.rotation_euler = dir_d.to_track_quat('-Z', 'Y').to_euler()
cam_drone.data.lens = 22.0

# B) Direct View of Curved Stand from Penalty Spot (Cam_11_Front_Goal_Right)
cam11 = bpy.data.objects.get("Cam_11_Front_Goal_Right")
if cam11:
    cam11.location = (41.5, 0.0, 1.65)
    aim11 = Vector((70.0, 0.0, 4.5))
    cam11.rotation_euler = (aim11 - cam11.location).to_track_quat('-Z', 'Y').to_euler()
    cam11.data.lens = 26.0

# C) Goal Action Angle (Cam_5_Goal_Action)
cam5 = bpy.data.objects.get("Cam_5_Goal_Action")
if cam5:
    cam5.location = (40.0, -22.0, 2.6)
    aim5 = Vector((65.0, 5.0, 4.2))
    cam5.rotation_euler = (aim5 - cam5.location).to_track_quat('-Z', 'Y').to_euler()
    cam5.data.lens = 38.0

# 10. RENDER KEY VIEWS FOR VERIFICATION
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 640

renders = [
    ("Cam_12_Drone_Sinigaglia_Match", "preview_curved_curva_drone_match.png"),
    ("Cam_11_Front_Goal_Right", "preview_stadium_Cam_11_Front_Goal_Right.png"),
    ("Cam_5_Goal_Action", "preview_stadium_Cam_5_Goal_Action.png"),
    ("Cam_2_Wide_Panorama", "preview_stadium_Cam_2_Wide_Panorama.png"),
    ("Cam_1_SerieA_Broadcast", "preview_stadium_Cam_1_SerieA_Broadcast.png")
]

for cname, fname in renders:
    c = bpy.data.objects.get(cname)
    if c:
        bpy.context.scene.camera = c
        out_f = os.path.join(OUTPUT, fname)
        bpy.context.scene.render.filepath = out_f
        print(f"Rendering {cname} -> {out_f}...")
        bpy.ops.render.render(write_still=True)

# Pack textures and save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved Stadio Sinigaglia with authentic curved Curva Nord!")
