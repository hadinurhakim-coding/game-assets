import bpy
import bmesh
import math
import os
from mathutils import Vector

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

col_env = bpy.data.collections.get("04_Lake_And_Mountains")
col_stands = bpy.data.collections.get("02_Stands_And_Roof")
col_pitch = bpy.data.collections.get("01_Pitch_And_Field")
col_cams = bpy.data.collections.get("05_Stadium_Cameras")

mat_concrete = bpy.data.materials.get("M_Stand_Concrete")
mat_railing = bpy.data.materials.get("M_Blue_Safety_Railing")

# 1. SETUP REALISTIC PBR LAKE COMO WATER MATERIAL
mat_lake = bpy.data.materials.get("M_Lake_Como_Water")
if not mat_lake:
    mat_lake = bpy.data.materials.new("M_Lake_Como_Water")
mat_lake.use_nodes = True
l_nt = mat_lake.node_tree
l_nt.nodes.clear()

l_out = l_nt.nodes.new('ShaderNodeOutputMaterial')
l_bsdf = l_nt.nodes.new('ShaderNodeBsdfPrincipled')
l_tex_coord = l_nt.nodes.new('ShaderNodeTexCoord')
l_noise = l_nt.nodes.new('ShaderNodeTexNoise')
l_bump = l_nt.nodes.new('ShaderNodeBump')

# Deep clear Alpine lake water color (Como blue)
l_bsdf.inputs['Base Color'].default_value = (0.015, 0.075, 0.14, 1.0)
l_bsdf.inputs['Roughness'].default_value = 0.04
l_bsdf.inputs['Metallic'].default_value = 0.05
if 'Specular IOR Level' in l_bsdf.inputs:
    l_bsdf.inputs['Specular IOR Level'].default_value = 0.85

# Subtle water ripple bumps
l_noise.inputs['Scale'].default_value = 18.0
l_noise.inputs['Detail'].default_value = 4.0
l_noise.inputs['Roughness'].default_value = 0.45
l_bump.inputs['Strength'].default_value = 0.22
l_bump.inputs['Distance'].default_value = 0.10

l_nt.links.new(l_tex_coord.outputs['Object'], l_noise.inputs['Vector'])
l_nt.links.new(l_noise.outputs['Fac'], l_bump.inputs['Height'])
l_nt.links.new(l_bump.outputs['Normal'], l_bsdf.inputs['Normal'])
l_nt.links.new(l_bsdf.outputs['BSDF'], l_out.inputs['Surface'])

# 2. POSITION 3D WATER SURFACE EXACTLY AT SEAWALL WATERLINE (Z = -0.15m)
lake_obj = bpy.data.objects.get("Lake_Como_Water_Surface")
if not lake_obj:
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, -0.15))
    lake_obj = bpy.context.object
    lake_obj.name = "Lake_Como_Water_Surface"
    col_env.objects.link(lake_obj)

lake_obj.location = (0.0, 40.0, -0.15)
lake_obj.scale = (2400.0, 2400.0, 1.0)
bpy.ops.object.transform_apply(scale=True)
lake_obj.data.materials.clear()
lake_obj.data.materials.append(mat_lake)

# 3. BUILD LAKE COMO PANORAMA BACKDROP SCREEN (CURVED CYLINDER IN NORTH ARC)
backdrop_path = os.path.join(ASSETS, "lake_como_panorama_backdrop.png")

mat_backdrop = bpy.data.materials.get("M_Lake_Como_Panorama")
if not mat_backdrop:
    mat_backdrop = bpy.data.materials.new("M_Lake_Como_Panorama")
mat_backdrop.use_nodes = True
b_nt = mat_backdrop.node_tree
b_nt.nodes.clear()

b_out = b_nt.nodes.new('ShaderNodeOutputMaterial')
b_emit = b_nt.nodes.new('ShaderNodeEmission')
b_tex = b_nt.nodes.new('ShaderNodeTexImage')
b_tex.image = bpy.data.images.load(backdrop_path, check_existing=True)

b_emit.inputs['Strength'].default_value = 1.05
b_nt.links.new(b_tex.outputs['Color'], b_emit.inputs['Color'])
b_nt.links.new(b_emit.outputs['Emission'], b_out.inputs['Surface'])

# Remove previous backdrop if exists
old_bd = bpy.data.objects.get("Lake_Como_Panorama_Screen")
if old_bd:
    bpy.data.objects.remove(old_bd, do_unlink=True)

# Build curved cylindrical mesh spanning North / North-West (Lake side)
# Radius R = 380m, height Z from -2.0m to 120m
bm_bd = bmesh.new()
uv_bd = bm_bd.loops.layers.uv.new("UVMap")
R_bd = 380.0
Z_bd_bot = -5.0
Z_bd_top = 135.0
# Spans from East to West across the entire lake view (angle from -160 deg to +20 deg)
ang_bd_min = math.radians(-165.0)
ang_bd_max = math.radians(25.0)
num_bd_segs = 64
d_bd_ang = (ang_bd_max - ang_bd_min) / num_bd_segs

for s in range(num_bd_segs):
    a0 = ang_bd_min + s * d_bd_ang
    a1 = ang_bd_min + (s + 1) * d_bd_ang
    u0 = s / num_bd_segs
    u1 = (s + 1) / num_bd_segs

    ca0, sa0 = math.cos(a0), math.sin(a0)
    ca1, sa1 = math.cos(a1), math.sin(a1)

    v1 = bm_bd.verts.new((R_bd * ca0, 20.0 + R_bd * sa0, Z_bd_bot))
    v2 = bm_bd.verts.new((R_bd * ca1, 20.0 + R_bd * sa1, Z_bd_bot))
    v3 = bm_bd.verts.new((R_bd * ca1, 20.0 + R_bd * sa1, Z_bd_top))
    v4 = bm_bd.verts.new((R_bd * ca0, 20.0 + R_bd * sa0, Z_bd_top))

    # Face pointing inward toward stadium
    f = bm_bd.faces.new((v4, v3, v2, v1))
    f.loops[0][uv_bd].uv = (u0, 1.0)
    f.loops[1][uv_bd].uv = (u1, 1.0)
    f.loops[2][uv_bd].uv = (u1, 0.0)
    f.loops[3][uv_bd].uv = (u0, 0.0)

bd_mesh = bpy.data.meshes.new("Lake_Como_Panorama_Screen_Mesh")
bm_bd.to_mesh(bd_mesh)
bm_bd.free()

bd_obj = bpy.data.objects.new("Lake_Como_Panorama_Screen", bd_mesh)
bd_obj.data.materials.append(mat_backdrop)
col_env.objects.link(bd_obj)

# 4. OPEN UP THE CORNER GAP (CURVA SUD / DISTINTI CORNER):
# In Image 1, this corner is an open view to Lake Como!
# Replace solid 1.8m block with low curb (0.35m) + transparent vertical picket railing
old_wall = bpy.data.objects.get("Corner_Perimeter_Wall_-1_1")
if old_wall:
    bpy.data.objects.remove(old_wall, do_unlink=True)

# Build authentic open corner gate & low seawall curb
bm_cg = bmesh.new()
p_x0, p_y0 = -49.0, 42.0
p_x1, p_y1 = -56.0, 37.0
v_line = Vector((p_x1 - p_x0, p_y1 - p_y0, 0.0))
L_gate = v_line.length
dir_g = v_line.normalized()
norm_g = Vector((-dir_g.y, dir_g.x, 0.0))

# Low concrete curb (0.35m high)
curb_h = 0.35
curb_w = 0.40
p_mid = (Vector((p_x0, p_y0, 0.0)) + Vector((p_x1, p_y1, 0.0))) / 2.0
ang_g = math.atan2(dir_g.y, dir_g.x)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(p_mid.x, p_mid.y, curb_h / 2), rotation=(0, 0, ang_g))
curb = bpy.context.object
curb.name = "Corner_Seawall_Curb_NW"
curb.scale = (L_gate, curb_w, curb_h)
bpy.ops.object.transform_apply(scale=True)
curb.data.materials.append(mat_concrete)
col_stands.objects.link(curb)

# See-through vertical metal safety gate (as seen in Image 1: vertical pickets with lake water fully visible behind)
bm_gate = bmesh.new()
num_pickets = 18
picket_h = 1.30
for i in range(num_pickets + 1):
    fp = i / num_pickets
    pt = Vector((p_x0, p_y0, curb_h)) + v_line * fp
    vp1 = bm_gate.verts.new(pt)
    vp2 = bm_gate.verts.new(pt + Vector((0, 0, picket_h)))
    bm_gate.edges.new((vp1, vp2))

# Top & Mid horizontal rails
bm_gate.edges.new((
    bm_gate.verts.new((p_x0, p_y0, curb_h + picket_h)),
    bm_gate.verts.new((p_x1, p_y1, curb_h + picket_h))
))
bm_gate.edges.new((
    bm_gate.verts.new((p_x0, p_y0, curb_h + picket_h * 0.5)),
    bm_gate.verts.new((p_x1, p_y1, curb_h + picket_h * 0.5))
))

gate_mesh = bpy.data.meshes.new("Corner_Security_Gate_NW_Mesh")
bm_gate.to_mesh(gate_mesh)
bm_gate.free()
gate_obj = bpy.data.objects.new("Corner_Security_Gate_NW", gate_mesh)
gate_obj.data.materials.append(mat_railing)
mod_gw = gate_obj.modifiers.new("Wireframe", type='WIREFRAME')
mod_gw.thickness = 0.035
col_stands.objects.link(gate_obj)

# 5. CONFIGURE WORLD BACKGROUND & 3D VIEWPORT SHADING
# Setup world environment node tree with Lake Como sky & water reflections
scene = bpy.context.scene
scene.world.use_nodes = True
w_nt = scene.world.node_tree
w_nt.nodes.clear()

w_out = w_nt.nodes.new('ShaderNodeOutputWorld')
w_bg = w_nt.nodes.new('ShaderNodeBackground')
w_bg.inputs['Color'].default_value = (0.55, 0.72, 0.92, 1.0) # Clear Lake Como sky
w_bg.inputs['Strength'].default_value = 1.15
w_nt.links.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

# Set Viewport Shading for all 3D Viewport spaces in blend file:
# Force use_scene_world = True and use_scene_lights = True to ELIMINATE blurry forest.exr trees!
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.use_scene_world = True
                    space.shading.use_scene_lights = True

# 6. RENDER USER CORNER MATCH VIEW (`Cam_User_Corner_Match`)
cam_corner = bpy.data.objects.get("Cam_User_Corner_Match")
if not cam_corner:
    cd = bpy.data.cameras.new("Cam_User_Corner_Match")
    cam_corner = bpy.data.objects.new("Cam_User_Corner_Match", cd)
    col_cams.objects.link(cam_corner)

# Position matching user Image 2 perfectly
cam_corner.location = (-26.0, 12.0, 2.8)
aim = Vector((-58.0, 44.0, 5.5))
cam_corner.rotation_euler = (aim - cam_corner.location).to_track_quat('-Z', 'Y').to_euler()
cam_corner.data.lens = 28.0

bpy.context.scene.camera = cam_corner
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 620
out_test = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_lake_como_corner_view.png"
bpy.context.scene.render.filepath = out_test
bpy.ops.render.render(write_still=True)
print("Rendered Lake Como corner view to:", out_test)

# Also re-render Cam_2_Wide_Panorama and Cam_1_SerieA_Broadcast
for cname, fname in [
    ("Cam_2_Wide_Panorama", "preview_stadium_Cam_2_Wide_Panorama.png"),
    ("Cam_1_SerieA_Broadcast", "preview_stadium_Cam_1_SerieA_Broadcast.png"),
    ("Cam_User_Photo_Match", "preview_stadium_Cam_User_Photo_Match.png")
]:
    c_obj = bpy.data.objects.get(cname)
    if c_obj:
        bpy.context.scene.camera = c_obj
        p_path = os.path.join(OUTPUT, fname)
        bpy.context.scene.render.filepath = p_path
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {cname} to: {p_path}")

# Pack textures and save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved blend file with Lake Como water in corner spot!")
