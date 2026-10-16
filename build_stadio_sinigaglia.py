import bpy
import bmesh
import math
import os
from mathutils import Vector, Euler, Matrix

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUT = os.path.join(ROOT, "Output")
os.makedirs(OUT, exist_ok=True)
BLEND_PATH = os.path.join(OUT, "Stadio_Sinigaglia_Como.blend")

# -----------------------------------------------------------------------------
# 1. CLEAN UP SCENE
# -----------------------------------------------------------------------------
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for ma in list(bpy.data.materials):
    bpy.data.materials.remove(ma)
for ca in list(bpy.data.cameras):
    bpy.data.cameras.remove(ca)
for li in list(bpy.data.lights):
    bpy.data.lights.remove(li)
for cl in list(bpy.data.collections):
    if cl != bpy.context.scene.collection:
        bpy.data.collections.remove(cl)

scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# Create organized collections
col_pitch = bpy.data.collections.new("01_Pitch_And_Field")
col_stands = bpy.data.collections.new("02_Stands_And_Roof")
col_towers = bpy.data.collections.new("03_Floodlight_Towers")
col_env = bpy.data.collections.new("04_Lake_And_Mountains")
col_cams = bpy.data.collections.new("05_Stadium_Cameras")

for c in [col_pitch, col_stands, col_towers, col_env, col_cams]:
    scene.collection.children.link(c)

def link_col(ob, collection):
    collection.objects.link(ob)

# -----------------------------------------------------------------------------
# 2. PBR MATERIALS
# -----------------------------------------------------------------------------
def make_pbr_mat(name, base_color=(0.8, 0.8, 0.8, 1.0), roughness=0.5, metallic=0.0, emission_color=None, emission_strength=1.0, tex_path=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Base Color'].default_value = base_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic

    if tex_path and os.path.exists(tex_path):
        tex_node = nt.nodes.new('ShaderNodeTexImage')
        tex_node.image = bpy.data.images.load(tex_path)
        nt.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
        if 'Emission Color' in bsdf.inputs and emission_color:
            nt.links.new(tex_node.outputs['Color'], bsdf.inputs['Emission Color'])
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    elif emission_color:
        if 'Emission Color' in bsdf.inputs:
            bsdf.inputs['Emission Color'].default_value = emission_color
            bsdf.inputs['Emission Strength'].default_value = emission_strength
    return mat

# Realistic Serie A Pitch Grass with 4K Seamless Regulation Lines
def make_pitch_grass_mat():
    mat = bpy.data.materials.new("M_Como_Pitch_Grass")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    bsdf.inputs['Roughness'].default_value = 0.85
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.10
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.10

    tex_pitch = os.path.join(ASSETS, "como_pitch_full_texture.png")
    if os.path.exists(tex_pitch):
        tex_node = nt.nodes.new('ShaderNodeTexImage')
        tex_node.image = bpy.data.images.load(tex_pitch)
        nt.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
    return mat

# Semi-Transparent Diamond Hex Net Material
# Professional PBR Hexagonal Honeycomb Net Material (FIFA/UEFA Regulation)
def make_goal_net_mat():
    mat = bpy.data.materials.new("M_Goal_Net_Hexagonal")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out_node = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    tex_col = nt.nodes.new('ShaderNodeTexImage')
    tex_norm = nt.nodes.new('ShaderNodeTexImage')
    norm_map = nt.nodes.new('ShaderNodeNormalMap')

    tex_col_path = os.path.join(ASSETS, "como_hex_net_color.png")
    tex_norm_path = os.path.join(ASSETS, "como_hex_net_normal.png")
    if os.path.exists(tex_col_path):
        tex_col.image = bpy.data.images.load(tex_col_path, check_existing=True)
    if os.path.exists(tex_norm_path):
        tex_norm.image = bpy.data.images.load(tex_norm_path, check_existing=True)
        tex_norm.image.colorspace_settings.name = 'Non-Color'

    mapping.inputs['Scale'].default_value = (1.0, 1.0, 1.0)
    nt.links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], tex_col.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], tex_norm.inputs['Vector'])

    nt.links.new(tex_col.outputs['Color'], bsdf.inputs['Base Color'])
    if 'Alpha' in bsdf.inputs:
        nt.links.new(tex_col.outputs['Alpha'], bsdf.inputs['Alpha'])

    norm_map.inputs['Strength'].default_value = 1.2
    nt.links.new(tex_norm.outputs['Color'], norm_map.inputs['Color'])
    nt.links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])

    bsdf.inputs['Roughness'].default_value = 0.78
    if 'Sheen Roughness' in bsdf.inputs:
        bsdf.inputs['Sheen Roughness'].default_value = 0.5

    nt.links.new(bsdf.outputs['BSDF'], out_node.inputs['Surface'])
    mat.blend_method = 'CLIP'
    if hasattr(mat, 'shadow_method'):
        mat.shadow_method = 'CLIP'
    return mat

mat_grass = make_pitch_grass_mat()
mat_net = make_goal_net_mat()
mat_posts = make_pbr_mat("M_Goal_Posts_White", base_color=(0.96, 0.97, 0.99, 1.0), roughness=0.18, metallic=0.08)
mat_stanchion = make_pbr_mat("M_Goal_Stanchion_Steel", base_color=(0.12, 0.13, 0.15, 1.0), roughness=0.45, metallic=0.85)

mat_concrete = make_pbr_mat("M_Stadium_Concrete", base_color=(0.60, 0.62, 0.64, 1.0), roughness=0.82)
mat_asphalt = make_pbr_mat("M_Perimeter_Asphalt", base_color=(0.18, 0.20, 0.22, 1.0), roughness=0.88)
mat_steel_dark = make_pbr_mat("M_Roof_Steel_Truss", base_color=(0.06, 0.08, 0.10, 1.0), roughness=0.40, metallic=0.85)
mat_roof_sheet = make_pbr_mat("M_Roof_Cladding", base_color=(0.12, 0.14, 0.16, 1.0), roughness=0.48, metallic=0.5)
mat_glass = make_pbr_mat("M_VIP_Glass", base_color=(0.12, 0.28, 0.38, 0.35), roughness=0.06, metallic=0.1)
def make_lake_water_mat():
    mat = bpy.data.materials.new("M_Lake_Como_Water")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    noise = nt.nodes.new('ShaderNodeTexNoise')
    bump = nt.nodes.new('ShaderNodeBump')
    
    # Deep clear Alpine lake water color (Lake Como slate blue)
    bsdf.inputs['Base Color'].default_value = (0.015, 0.075, 0.14, 1.0)
    bsdf.inputs['Roughness'].default_value = 0.04
    bsdf.inputs['Metallic'].default_value = 0.05
    if 'Specular IOR Level' in bsdf.inputs:
        bsdf.inputs['Specular IOR Level'].default_value = 0.85
    elif 'Specular' in bsdf.inputs:
        bsdf.inputs['Specular'].default_value = 0.85
        
    noise.inputs['Scale'].default_value = 16.0
    noise.inputs['Detail'].default_value = 4.0
    noise.inputs['Roughness'].default_value = 0.45
    bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.10
    
    nt.links.new(tex_coord.outputs['Object'], noise.inputs['Vector'])
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat

def make_backdrop_mat(tex_path):
    mat = bpy.data.materials.new("M_Lake_Como_Panorama")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    emit = nt.nodes.new('ShaderNodeEmission')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(tex_path, check_existing=True)
    emit.inputs['Strength'].default_value = 1.05
    nt.links.new(tex.outputs['Color'], emit.inputs['Color'])
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return mat

mat_lake = make_lake_water_mat()

# Textures
tex_distinti = os.path.join(ASSETS, "como_distinti_seats.png")
tex_tribuna = os.path.join(ASSETS, "como_tribuna_seats.png")
tex_curva = os.path.join(ASSETS, "como_curva_seats.png")
tex_checker = os.path.join(ASSETS, "como_checker_banner.png")
tex_led = os.path.join(ASSETS, "como_led_boards.png")
tex_backdrop = os.path.join(ASSETS, "lake_como_panorama_backdrop.png")

mat_distinti = make_pbr_mat("M_Distinti_COMO_Seats", tex_path=tex_distinti, roughness=0.55)
mat_tribuna = make_pbr_mat("M_Tribuna_Seats", tex_path=tex_tribuna, roughness=0.55)
mat_curva = make_pbr_mat("M_Curva_Seats", tex_path=tex_curva, roughness=0.55, emission_color=(1, 1, 1, 1), emission_strength=0.15)
tex_curva_white = os.path.join(ASSETS, "como_curva_sud_white_seats.png")
tex_curved_seats = os.path.join(ASSETS, "como_curva_nord_curved_seats.png")

mat_curva_white = make_pbr_mat("M_Curva_Sud_White_Seats", tex_path=tex_curva_white, roughness=0.55)
mat_curved_seats = make_pbr_mat("M_Curved_Curva_Nord_Seats", tex_path=tex_curved_seats, roughness=0.55)
mat_brick = make_pbr_mat("M_Curva_Brick_Building", base_color=(0.58, 0.24, 0.18, 1.0), roughness=0.8)
mat_railing = make_pbr_mat("M_Blue_Safety_Railing", base_color=(0.20, 0.52, 0.78, 1.0), roughness=0.35, metallic=0.7)
mat_apron = make_pbr_mat("M_Paved_Apron_Grey", base_color=(0.36, 0.38, 0.40, 1.0), roughness=0.9)
mat_checker = make_pbr_mat("M_Checker_Banner", tex_path=tex_checker, roughness=0.5)
mat_led = make_pbr_mat("M_Perimeter_LED", tex_path=tex_led, emission_color=(1, 1, 1, 1), emission_strength=2.2, roughness=0.25)
mat_pylon_red = make_pbr_mat("M_Pylon_Red", base_color=(0.85, 0.08, 0.06, 1.0), roughness=0.45)
mat_pylon_white = make_pbr_mat("M_Pylon_White", base_color=(0.94, 0.94, 0.95, 1.0), roughness=0.35)
mat_lens = make_pbr_mat("M_Flood_Lamp_Lens", base_color=(1, 1, 1, 1), emission_color=(1.0, 0.98, 0.92, 1), emission_strength=8.0)
mat_backdrop = make_backdrop_mat(tex_backdrop)
mat_booth_blue = make_pbr_mat("M_Corner_Booth_Blue", base_color=(0.08, 0.28, 0.62, 1.0), roughness=0.35)
mat_lamp_pole = make_pbr_mat("M_Lamppost_Steel", base_color=(0.75, 0.77, 0.80, 1.0), roughness=0.3, metallic=0.9)
mat_monument = make_pbr_mat("M_Monumento_Travertine", base_color=(0.92, 0.91, 0.88, 1.0), roughness=0.65)
mat_void = make_pbr_mat("M_Monumento_Void", base_color=(0.12, 0.12, 0.14, 1.0), roughness=0.90)
mat_flag_red = make_pbr_mat("M_Flag_Red", base_color=(0.85, 0.10, 0.10, 1.0), roughness=0.6)

# -----------------------------------------------------------------------------
# 3. BUILD PITCH TURF & HOLLOW APRON (ZERO Z-FIGHTING / ZERO GLITCHING)
# -----------------------------------------------------------------------------
# Pitch Turf Plane (105m x 68m at Z = 0.00 with 4K Texture)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 0, 0.0))
pitch = bpy.context.object
pitch.name = "Pitch_Turf_105x68"
pitch.scale = (105.0, 68.0, 1.0)
bpy.ops.object.transform_apply(scale=True)
pitch.data.materials.append(mat_grass)
link_col(pitch, col_pitch)

# Hollow Frame Perimeter Apron (outer: 136m x 96m, inner hole: 105m x 68m, at Z = -0.02)
bm_ap = bmesh.new()
v_out = [
    bm_ap.verts.new((-68.0, -48.0, -0.02)),
    bm_ap.verts.new(( 68.0, -48.0, -0.02)),
    bm_ap.verts.new(( 68.0,  48.0, -0.02)),
    bm_ap.verts.new((-68.0,  48.0, -0.02)),
]
v_in = [
    bm_ap.verts.new((-52.5, -34.0, -0.02)),
    bm_ap.verts.new(( 52.5, -34.0, -0.02)),
    bm_ap.verts.new(( 52.5,  34.0, -0.02)),
    bm_ap.verts.new((-52.5,  34.0, -0.02)),
]
bm_ap.faces.new((v_out[0], v_out[1], v_in[1], v_in[0])) # South
bm_ap.faces.new((v_out[1], v_out[2], v_in[2], v_in[1])) # East
bm_ap.faces.new((v_out[2], v_out[3], v_in[3], v_in[2])) # North
bm_ap.faces.new((v_out[3], v_out[0], v_in[0], v_in[3])) # West

ap_mesh = bpy.data.meshes.new("Stadium_Perimeter_Apron_Mesh")
bm_ap.to_mesh(ap_mesh)
bm_ap.free()

apron = bpy.data.objects.new("Stadium_Perimeter_Apron", ap_mesh)
apron.data.materials.append(mat_asphalt)
link_col(apron, col_pitch)

# -----------------------------------------------------------------------------
# 4. BUILD 3D GOALS (GAWANG) & CORNER FLAGS
# -----------------------------------------------------------------------------
def build_football_goal(side, name):
    goal_group = []
    gx = side * 52.5
    dir_x = side
    gw = 7.32
    gh = 2.44
    pr = 0.06 # Post radius 6cm (12cm diameter)

    # 1. Goal Frame (Posts + Crossbar + Corner Elbows)
    # Left & Right Posts
    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gh, location=(gx, -gw/2, gh/2), vertices=32)
    p_l = bpy.context.object
    p_l.name = f"{name}_Post_L"
    p_l.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_group.append(p_l)

    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gh, location=(gx, gw/2, gh/2), vertices=32)
    p_r = bpy.context.object
    p_r.name = f"{name}_Post_R"
    p_r.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_group.append(p_r)

    # Crossbar
    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gw, location=(gx, 0, gh), rotation=(math.radians(90), 0, 0), vertices=32)
    cbar = bpy.context.object
    cbar.name = f"{name}_Crossbar"
    cbar.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_group.append(cbar)

    # Corner Elbows
    for ey in [-gw/2, gw/2]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=pr, location=(gx, ey, gh), segments=24, ring_count=16)
        elbow = bpy.context.object
        elbow.name = f"{name}_Elbow_{ey}"
        elbow.data.materials.append(mat_posts)
        bpy.ops.object.shade_smooth()
        goal_group.append(elbow)

    # 2. Ground Base Frame (Tubular frame holding net to grass)
    d_bot = 2.2 # Bottom depth
    x_bot = gx + dir_x * d_bot
    b_rad = 0.025 # 5cm pipe

    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=d_bot, location=(gx + dir_x * d_bot/2, -gw/2, b_rad), rotation=(0, math.radians(90), 0), vertices=16)
    gp_l = bpy.context.object
    gp_l.name = f"{name}_Ground_Pipe_L"
    gp_l.data.materials.append(mat_stanchion)
    goal_group.append(gp_l)

    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=d_bot, location=(gx + dir_x * d_bot/2, gw/2, b_rad), rotation=(0, math.radians(90), 0), vertices=16)
    gp_r = bpy.context.object
    gp_r.name = f"{name}_Ground_Pipe_R"
    gp_r.data.materials.append(mat_stanchion)
    goal_group.append(gp_r)

    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=gw, location=(x_bot, 0, b_rad), rotation=(math.radians(90), 0, 0), vertices=16)
    gp_b = bpy.context.object
    gp_b.name = f"{name}_Ground_Pipe_Back"
    gp_b.data.materials.append(mat_stanchion)
    goal_group.append(gp_b)

    # 3. 3 Rear Tension Stanchions (Tiang Penegang Belakang)
    d_st = 2.4 # 2.4m behind goal line
    x_st = gx + dir_x * d_st
    h_st = 3.0 # 3.0m high
    st_r = 0.045 # 9cm diameter

    stanchion_ys = [-gw/2 - 0.25, 0.0, gw/2 + 0.25]
    for s_idx, sy in enumerate(stanchion_ys):
        # Vertical Stanchion Mast
        bpy.ops.mesh.primitive_cylinder_add(radius=st_r, depth=h_st, location=(x_st, sy, h_st/2), vertices=24)
        smast = bpy.context.object
        smast.name = f"{name}_Stanchion_Mast_{s_idx}"
        smast.data.materials.append(mat_stanchion)
        bpy.ops.object.shade_smooth()
        goal_group.append(smast)

        # Ground base plinth plate
        bpy.ops.mesh.primitive_cylinder_add(radius=st_r*2.2, depth=0.06, location=(x_st, sy, 0.03), vertices=16)
        splinth = bpy.context.object
        splinth.name = f"{name}_Stanchion_Plinth_{s_idx}"
        splinth.data.materials.append(mat_stanchion)
        goal_group.append(splinth)

        # Rear Ground Guy Wire Anchor (angled back into turf for structural stability)
        anchor_x = x_st + dir_x * 0.9
        p_top = Vector((x_st, sy, h_st))
        p_anc = Vector((anchor_x, sy, 0.02))
        v_anc = p_anc - p_top
        bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=v_anc.length, location=(p_top + p_anc)/2, vertices=12)
        anc_wire = bpy.context.object
        anc_wire.name = f"{name}_Stanchion_Anchor_Wire_{s_idx}"
        anc_wire.rotation_euler = v_anc.to_track_quat('Z', 'Y').to_euler()
        anc_wire.data.materials.append(mat_stanchion)
        goal_group.append(anc_wire)

    # 4. Hexagonal Netting with Realistic Gravity Sag, Inward Catenary Draping & Ground Apron
    d_top = 1.05
    d_bot = 2.25
    bm_net = bmesh.new()
    NY = 36         # 36 columns across 7.32m width (~20cm per quad)
    NX_top = 10     # 10 rows along 1.05m top shelf
    NZ_back = 24    # 24 rows along 2.44m back drop
    NZ_side = 18    # 18 rows for side panels

    y_coords = [ -gw/2 + i * (gw / NY) for i in range(NY + 1) ]

    # --- TOP SHELF (ROOF) WITH CATENARY GRAVITY SAG ---
    top_verts = []
    for ix in range(NX_top + 1):
        row_verts = []
        fx = ix / NX_top
        for iy, cy in enumerate(y_coords):
            norm_y = cy / (gw / 2) # -1.0 to 1.0
            
            # Sag of the rear rope between the 3 cable attachment points:
            if cy <= 0.0:
                frac_bay = (cy + gw/2) / (gw/2)
                rope_dip = 0.12 * math.sin(math.pi * frac_bay)
            else:
                frac_bay = cy / (gw/2)
                rope_dip = 0.12 * math.sin(math.pi * frac_bay)
            
            center_cable_dip = 0.04 * (1.0 - abs(norm_y))
            total_rear_dip = (rope_dip + center_cable_dip) * fx

            # Deep belly sag of the mesh interior under flexible weight
            belly_sag = 0.16 * math.sin(math.pi * fx) * (1.0 - 0.85 * (norm_y**2))
            dx_sag = -dir_x * 0.04 * math.sin(math.pi * fx)

            cur_x = gx + dir_x * (fx * d_top) + dx_sag
            cur_z = gh - (total_rear_dip + belly_sag)
            
            v = bm_net.verts.new((cur_x, cy, cur_z))
            row_verts.append(v)
        top_verts.append(row_verts)

    for ix in range(NX_top):
        for iy in range(NY):
            bm_net.faces.new((
                top_verts[ix][iy],
                top_verts[ix+1][iy],
                top_verts[ix+1][iy+1],
                top_verts[ix][iy+1]
            ))

    # --- BACK DROP (WALL) WITH INWARD CATENARY BILLOW & GROUND DRAPE SLACK ---
    back_verts = [top_verts[NX_top]]
    for iz in range(1, NZ_back + 1):
        row_verts = []
        fz = iz / NZ_back
        for iy, cy in enumerate(y_coords):
            norm_y = cy / (gw / 2)
            top_x = top_verts[NX_top][iy].co.x
            top_z = top_verts[NX_top][iy].co.z
            base_x = gx + dir_x * d_bot

            nom_x = top_x + (base_x - top_x) * fz
            nom_z = top_z * (1.0 - fz)

            # Inward gravity catenary sag
            catenary_inward = -dir_x * 0.15 * math.sin(math.pi * (fz ** 0.85)) * (1.0 - 0.2 * norm_y**2)
            # Vertical gravity sag
            vert_sag = -0.10 * math.sin(math.pi * fz) * (1.0 - 0.4 * fz)
            # Tension ripples radiating from cable anchors
            wave_pleat = dir_x * 0.035 * math.sin(3.0 * math.pi * fz) * math.sin(2.0 * math.pi * norm_y) * math.sin(math.pi * fz)

            # Ground apron / pooling slack onto grass
            ground_slack_x = 0.0
            ground_cushion_z = 0.0
            if fz > 0.78:
                frac_ground = (fz - 0.78) / 0.22
                ground_slack_x = dir_x * 0.14 * (frac_ground ** 1.6)
                ground_cushion_z = 0.03 * (1.0 - frac_ground) * frac_ground

            cur_x = nom_x + catenary_inward + wave_pleat + ground_slack_x
            cur_z = max(0.012, nom_z + vert_sag + ground_cushion_z)

            v = bm_net.verts.new((cur_x, cy, cur_z))
            row_verts.append(v)
        back_verts.append(row_verts)

    for iz in range(NZ_back):
        for iy in range(NY):
            bm_net.faces.new((
                back_verts[iz][iy],
                back_verts[iz+1][iy],
                back_verts[iz+1][iy+1],
                back_verts[iz][iy+1]
            ))

    # --- LEFT SIDE PANEL (HOURGLASS PINCH + GRAVITY SAG) ---
    side_l_verts = []
    for iz in range(NZ_side + 1):
        row_v = []
        fz = iz / NZ_side
        nom_z = gh * (1.0 - fz)
        for ix in range(NX_top + 1):
            fx = ix / NX_top
            cur_depth = d_top + (d_bot - d_top) * fz
            nom_x = gx + dir_x * (fx * cur_depth)

            pinch_inward = 0.10 * math.sin(math.pi * fz) * math.sin(math.pi * fx)
            side_sag_z = -0.06 * math.sin(math.pi * fz) * math.sin(math.pi * fx)

            cur_y = -gw/2 + pinch_inward
            cur_x = nom_x - dir_x * 0.06 * math.sin(math.pi * fz) * (fx ** 1.5)
            cur_z = max(0.012, nom_z + side_sag_z)

            if ix == 0:
                cur_x = gx
                cur_y = -gw/2
                cur_z = nom_z
            elif iz == 0:
                cur_x = top_verts[ix][0].co.x
                cur_y = top_verts[ix][0].co.y
                cur_z = top_verts[ix][0].co.z

            v = bm_net.verts.new((cur_x, cur_y, cur_z))
            row_v.append(v)
        side_l_verts.append(row_v)

    for iz in range(NZ_side):
        for ix in range(NX_top):
            bm_net.faces.new((
                side_l_verts[iz][ix],
                side_l_verts[iz+1][ix],
                side_l_verts[iz+1][ix+1],
                side_l_verts[iz][ix+1]
            ))

    # --- RIGHT SIDE PANEL (HOURGLASS PINCH + GRAVITY SAG) ---
    side_r_verts = []
    for iz in range(NZ_side + 1):
        row_v = []
        fz = iz / NZ_side
        nom_z = gh * (1.0 - fz)
        for ix in range(NX_top + 1):
            fx = ix / NX_top
            cur_depth = d_top + (d_bot - d_top) * fz
            nom_x = gx + dir_x * (fx * cur_depth)

            pinch_inward = 0.10 * math.sin(math.pi * fz) * math.sin(math.pi * fx)
            side_sag_z = -0.06 * math.sin(math.pi * fz) * math.sin(math.pi * fx)

            cur_y = gw/2 - pinch_inward
            cur_x = nom_x - dir_x * 0.06 * math.sin(math.pi * fz) * (fx ** 1.5)
            cur_z = max(0.012, nom_z + side_sag_z)

            if ix == 0:
                cur_x = gx
                cur_y = gw/2
                cur_z = nom_z
            elif iz == 0:
                cur_x = top_verts[ix][NY].co.x
                cur_y = top_verts[ix][NY].co.y
                cur_z = top_verts[ix][NY].co.z

            v = bm_net.verts.new((cur_x, cur_y, cur_z))
            row_v.append(v)
        side_r_verts.append(row_v)

    for iz in range(NZ_side):
        for ix in range(NX_top):
            bm_net.faces.new((
                side_r_verts[iz][ix],
                side_r_verts[iz][ix+1],
                side_r_verts[iz+1][ix+1],
                side_r_verts[iz+1][ix]
            ))

    bmesh.ops.remove_doubles(bm_net, verts=bm_net.verts, dist=0.02)

    # Seamless Box UV Mapping respecting Curvilinear Catenary Arc Length
    uv_layer = bm_net.loops.layers.uv.new("UVMap")
    for face in bm_net.faces:
        is_side_panel = abs(face.normal.y) > 0.65
        for loop in face.loops:
            vx, vy, vz = loop.vert.co
            if is_side_panel:
                u = abs(vx - gx) * 0.55
                v = vz * 0.55
            else:
                u = (vy + gw/2) * 0.55
                v = (abs(vx - gx) + (gh - vz) * 1.05) * 0.55
            loop[uv_layer].uv = (u, v)

    # Net connection points matching actual sagging top-rear vertices:
    top_rear_pts = [
        Vector((top_verts[NX_top][0].co.x,  -gw/2, top_verts[NX_top][0].co.z)),
        Vector((top_verts[NX_top][NY//2].co.x, 0.0, top_verts[NX_top][NY//2].co.z)),
        Vector((top_verts[NX_top][NY].co.x,  gw/2, top_verts[NX_top][NY].co.z))
    ]

    net_mesh = bpy.data.meshes.new(f"{name}_Hex_Net_Mesh")
    bm_net.to_mesh(net_mesh)
    bm_net.free()

    net_obj = bpy.data.objects.new(f"{name}_Hex_Net", net_mesh)
    net_obj.data.materials.append(mat_net)
    goal_group.append(net_obj)

    # 5. Tension Sling Cables (Kawat Sling Penarik Sudut & Atas Jaring)
    for s_idx, (sy, p_net) in enumerate(zip(stanchion_ys, top_rear_pts)):
        p_st = Vector((x_st, sy, h_st - 0.08))
        v_cable = p_net - p_st
        bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=v_cable.length, location=(p_st + p_net)/2, vertices=12)
        cable = bpy.context.object
        cable.name = f"{name}_Tension_Cable_{s_idx}"
        cable.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        cable.data.materials.append(mat_stanchion)
        goal_group.append(cable)

        # Turnbuckle tensioner
        bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=0.18, location=p_st + v_cable*0.28, vertices=12)
        tb = bpy.context.object
        tb.name = f"{name}_Turnbuckle_{s_idx}"
        tb.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        tb.data.materials.append(mat_stanchion)
        goal_group.append(tb)

    for ob in goal_group:
        link_col(ob, col_pitch)

build_football_goal(-1, "Goal_Left_North")
build_football_goal( 1, "Goal_Right_South")


# Corner Flags
for cx, cy in [(-52.5, -34.0), (-52.5, 34.0), (52.5, -34.0), (52.5, 34.0)]:
    bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=1.5, location=(cx, cy, 0.75))
    pole = bpy.context.object
    pole.name = f"Corner_Pole_{cx}_{cy}"
    pole.data.materials.append(mat_posts)
    link_col(pole, col_pitch)

    bpy.ops.mesh.primitive_plane_add(size=0.36, location=(cx, cy + 0.18, 1.35), rotation=(math.radians(90), 0, 0))
    flag = bpy.context.object
    flag.name = f"Corner_Flag_{cx}_{cy}"
    fmat = make_pbr_mat(f"M_Flag_{cx}_{cy}", base_color=(0.95, 0.85, 0.05, 1.0), roughness=0.6)
    flag.data.materials.append(fmat)
    link_col(flag, col_pitch)

# -----------------------------------------------------------------------------
# 5. PERIMETER LED BOARDS & TEAM BENCHES
# -----------------------------------------------------------------------------
for side_y in [-36.2, 36.2]:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, side_y, 0.5))
    led = bpy.context.object
    led.name = f"LED_Boards_Sideline_{side_y}"
    led.scale = (112.0, 0.25, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    led.data.materials.append(mat_led)
    link_col(led, col_pitch)

for side_x in [-55.8, 55.8]:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(side_x, 0, 0.5))
    led = bpy.context.object
    led.name = f"LED_Boards_GoalEnd_{side_x}"
    led.scale = (0.25, 74.0, 1.0)
    bpy.ops.object.transform_apply(scale=True)
    led.data.materials.append(mat_led)
    link_col(led, col_pitch)

# Player Dugouts
for dx, dname in [(-11.0, "Como_Bench"), (11.0, "Visitor_Bench")]:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(dx, -39.0, 1.35))
    dugout = bpy.context.object
    dugout.name = f"Dugout_{dname}"
    dugout.scale = (12.0, 2.4, 2.3)
    bpy.ops.object.transform_apply(scale=True)
    dugout.data.materials.append(mat_glass)
    link_col(dugout, col_pitch)
    
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(dx, -39.0, 0.2))
    dframe = bpy.context.object
    dframe.name = f"Dugout_Base_{dname}"
    dframe.scale = (12.2, 2.6, 0.4)
    bpy.ops.object.transform_apply(scale=True)
    dframe.data.materials.append(mat_steel_dark)
    link_col(dframe, col_pitch)

# -----------------------------------------------------------------------------
# 6. DISTINTI STAND ("C O [CROSS] M O" - LAKE SIDE, Y = +42 TO +65)
# -----------------------------------------------------------------------------
def create_solid_stepped_stand(name, x_span, y_start, y_end, z_start, z_end, num_tiers, mat_seats, mat_concrete):
    bm = bmesh.new()
    w = x_span
    x0, x1 = -w/2, w/2
    dy = (y_end - y_start) / num_tiers
    dz = (z_end - z_start) / num_tiers
    sy = 1.0 if y_end > y_start else -1.0

    # 1. Stepped seating tiers
    for i in range(num_tiers):
        cy0 = y_start + i * dy
        cy1 = y_start + (i + 1) * dy
        cz0 = z_start + i * dz
        cz1 = z_start + (i + 1) * dz
        
        # Riser face
        if sy > 0:
            vr1 = bm.verts.new((x0, cy0, cz0))
            vr2 = bm.verts.new((x1, cy0, cz0))
            vr3 = bm.verts.new((x1, cy0, cz1))
            vr4 = bm.verts.new((x0, cy0, cz1))
        else:
            vr1 = bm.verts.new((x1, cy0, cz0))
            vr2 = bm.verts.new((x0, cy0, cz0))
            vr3 = bm.verts.new((x0, cy0, cz1))
            vr4 = bm.verts.new((x1, cy0, cz1))
        fr = bm.faces.new((vr1, vr2, vr3, vr4))
        fr.material_index = 0
        
        # Tread face
        if sy > 0:
            vt1 = bm.verts.new((x0, cy0, cz1))
            vt2 = bm.verts.new((x1, cy0, cz1))
            vt3 = bm.verts.new((x1, cy1, cz1))
            vt4 = bm.verts.new((x0, cy1, cz1))
        else:
            vt1 = bm.verts.new((x1, cy0, cz1))
            vt2 = bm.verts.new((x0, cy0, cz1))
            vt3 = bm.verts.new((x0, cy1, cz1))
            vt4 = bm.verts.new((x1, cy1, cz1))
        ft = bm.faces.new((vt1, vt2, vt3, vt4))
        ft.material_index = 0

    # 2. Front foundation wall (z = 0.0 to z = z_start at y = y_start)
    if sy > 0:
        vf1 = bm.verts.new((x0, y_start, 0.0))
        vf2 = bm.verts.new((x1, y_start, 0.0))
        vf3 = bm.verts.new((x1, y_start, z_start))
        vf4 = bm.verts.new((x0, y_start, z_start))
    else:
        vf1 = bm.verts.new((x1, y_start, 0.0))
        vf2 = bm.verts.new((x0, y_start, 0.0))
        vf3 = bm.verts.new((x0, y_start, z_start))
        vf4 = bm.verts.new((x1, y_start, z_start))
    ff = bm.faces.new((vf1, vf2, vf3, vf4))
    ff.material_index = 1

    # 3. Rear exterior facade (z = 0.0 to z = z_end at y = y_end)
    if sy > 0:
        vb1 = bm.verts.new((x1, y_end, 0.0))
        vb2 = bm.verts.new((x0, y_end, 0.0))
        vb3 = bm.verts.new((x0, y_end, z_end))
        vb4 = bm.verts.new((x1, y_end, z_end))
    else:
        vb1 = bm.verts.new((x0, y_end, 0.0))
        vb2 = bm.verts.new((x1, y_end, 0.0))
        vb3 = bm.verts.new((x1, y_end, z_end))
        vb4 = bm.verts.new((x0, y_end, z_end))
    fb = bm.faces.new((vb1, vb2, vb3, vb4))
    fb.material_index = 1

    # 4. Bottom base plate at z = 0.0
    y_min_s = min(y_start, y_end)
    y_max_s = max(y_start, y_end)
    vbt1 = bm.verts.new((x0, y_min_s, 0.0))
    vbt2 = bm.verts.new((x0, y_max_s, 0.0))
    vbt3 = bm.verts.new((x1, y_max_s, 0.0))
    vbt4 = bm.verts.new((x1, y_min_s, 0.0))
    fbt = bm.faces.new((vbt1, vbt2, vbt3, vbt4))
    fbt.material_index = 1

    # 5. Solid side walls (x0 and x1) - zero see-through cavities
    for i in range(num_tiers):
        cy0 = y_start + i * dy
        cy1 = y_start + (i + 1) * dy
        cz1 = z_start + (i + 1) * dz
        y_A = min(cy0, cy1)
        y_B = max(cy0, cy1)
        
        # Left side at x0 (normal -X)
        vl1 = bm.verts.new((x0, y_A, 0.0))
        vl2 = bm.verts.new((x0, y_A, cz1))
        vl3 = bm.verts.new((x0, y_B, cz1))
        vl4 = bm.verts.new((x0, y_B, 0.0))
        fl = bm.faces.new((vl1, vl2, vl3, vl4))
        fl.material_index = 1

        # Right side at x1 (normal +X)
        vr1 = bm.verts.new((x1, y_A, 0.0))
        vr2 = bm.verts.new((x1, y_B, 0.0))
        vr3 = bm.verts.new((x1, y_B, cz1))
        vr4 = bm.verts.new((x1, y_A, cz1))
        fr = bm.faces.new((vr1, vr2, vr3, vr4))
        fr.material_index = 1

    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)

    # Analytical Seamless UV Mapping for seat texture (Slot 0 - continuous risers & treads)
    uv_layer = bm.loops.layers.uv.new("UVMap")
    dy_step = (y_end - y_start) / num_tiers
    dz_step = (z_end - z_start) / num_tiers
    for face in bm.faces:
        if face.material_index == 0:
            face_ys = [loop.vert.co.y for loop in face.loops]
            is_riser = abs(max(face_ys) - min(face_ys)) < 0.001
            avg_z = sum(loop.vert.co.z for loop in face.loops) / len(face.loops)
            tier_i = int(max(0, min(num_tiers - 1, (avg_z - z_start) / dz_step)))

            for loop in face.loops:
                vx, vy, vz = loop.vert.co
                u = (vx - x0) / (x1 - x0)
                if is_riser:
                    z_bot = z_start + tier_i * dz_step
                    z_top = z_start + (tier_i + 1) * dz_step
                    frac_z = (vz - z_bot) / max(0.001, (z_top - z_bot))
                    v = (tier_i + frac_z * 0.45) / num_tiers
                else:
                    y_front = y_start + tier_i * dy_step
                    y_back = y_start + (tier_i + 1) * dy_step
                    frac_y = (vy - y_front) / max(0.001, (y_back - y_front))
                    v = (tier_i + 0.45 + frac_y * 0.55) / num_tiers
                loop[uv_layer].uv = (u, v)


    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.data.materials.append(mat_seats)
    obj.data.materials.append(mat_concrete)
    return obj

distinti = create_solid_stepped_stand("Stand_Distinti_COMO", 98.0, 42.0, 64.0, 1.2, 13.5, 26, mat_distinti, mat_concrete)
link_col(distinti, col_stands)

# Distinti Lower Checkered Wall
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 41.8, 0.6))
chk_wall = bpy.context.object
chk_wall.name = "Distinti_Checkerboard_Fascia"
chk_wall.scale = (98.0, 0.4, 1.2)
bpy.ops.object.transform_apply(scale=True)
chk_wall.data.materials.append(mat_checker)
link_col(chk_wall, col_stands)

# Distinti Rear Wall & Top Glass Railing
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 64.2, 14.5))
dist_rail = bpy.context.object
dist_rail.name = "Distinti_Rear_Safety_Glass"
dist_rail.scale = (98.0, 0.2, 2.0)
bpy.ops.object.transform_apply(scale=True)
dist_rail.data.materials.append(mat_glass)
link_col(dist_rail, col_stands)

# -----------------------------------------------------------------------------
# 7. MAIN COVERED TRIBUNA (WEST SIDE, Y = -42 TO -68) WITH STEEL ROOF TRUSS
# -----------------------------------------------------------------------------
tribuna = create_solid_stepped_stand("Stand_Tribuna_Main", 98.0, -42.0, -66.0, 1.2, 15.5, 28, mat_tribuna, mat_concrete)
link_col(tribuna, col_stands)

# VIP Hospitality Suite & Press Lounge
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -65.5, 14.0))
vip_box = bpy.context.object
vip_box.name = "Tribuna_VIP_Lounges"
vip_box.scale = (86.0, 5.0, 5.5)
bpy.ops.object.transform_apply(scale=True)
vip_box.data.materials.append(mat_glass)
link_col(vip_box, col_stands)

# Player Tunnel
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -42.5, 1.6))
tunnel = bpy.context.object
tunnel.name = "Player_Entrance_Tunnel"
tunnel.scale = (5.5, 3.5, 2.8)
bpy.ops.object.transform_apply(scale=True)
tunnel.data.materials.append(mat_steel_dark)
link_col(tunnel, col_stands)

# Industrial Steel Cantilever Roof Truss Canopy
# 8 cantilever bents spaced along X from -42 to +42 (OFFSET FROM CENTER X=0 so center camera view is 100% UNBLOCKED!)
truss_bm = bmesh.new()
bent_positions = [-42.0, -30.0, -18.0, -6.0, 6.0, 18.0, 30.0, 42.0]

for bx in bent_positions:
    v_base = (bx, -68.0, 0.0)
    v_top = (bx, -68.0, 22.0)
    v_tip = (bx, -39.0, 19.5)
    v_knee = (bx, -54.0, 17.5)

    def add_beam_truss(p1, p2, r=0.14):
        dir_vec = (Vector(p2) - Vector(p1)).normalized()
        perp = dir_vec.cross(Vector((0, 0, 1))).normalized() if abs(dir_vec.z) < 0.9 else Vector((1, 0, 0))
        up = dir_vec.cross(perp).normalized()
        
        pts1 = [Vector(p1) + perp*r + up*r, Vector(p1) - perp*r + up*r, Vector(p1) - perp*r - up*r, Vector(p1) + perp*r - up*r]
        pts2 = [Vector(p2) + perp*r + up*r, Vector(p2) - perp*r + up*r, Vector(p2) - perp*r - up*r, Vector(p2) + perp*r - up*r]
        vA = [truss_bm.verts.new(p) for p in pts1]
        vB = [truss_bm.verts.new(p) for p in pts2]
        for i in range(4):
            truss_bm.faces.new((vA[i], vA[(i+1)%4], vB[(i+1)%4], vB[i]))

    add_beam_truss(v_base, v_top, r=0.25) # Rear column
    add_beam_truss(v_top, v_tip, r=0.22)  # Top cantilever rafter
    add_beam_truss((bx, -68.0, 15.0), v_knee, r=0.18)
    add_beam_truss(v_knee, v_tip, r=0.16)
    # Diagonal webbing
    add_beam_truss((bx, -68.0, 18.0), (bx, -60.0, 21.0), r=0.10)
    add_beam_truss((bx, -60.0, 21.0), (bx, -54.0, 17.5), r=0.10)
    add_beam_truss((bx, -54.0, 17.5), (bx, -47.0, 20.2), r=0.10)
    add_beam_truss((bx, -47.0, 20.2), v_tip, r=0.10)

truss_mesh = bpy.data.meshes.new("Roof_Truss_Mesh")
truss_bm.to_mesh(truss_mesh)
truss_bm.free()

truss_obj = bpy.data.objects.new("Roof_Steel_Truss_Structure", truss_mesh)
truss_obj.data.materials.append(mat_steel_dark)
link_col(truss_obj, col_stands)

# Roof Sheet Cladding
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, -53.5, 21.2), rotation=(math.radians(5.0), 0, 0))
roof_sheet = bpy.context.object
roof_sheet.name = "Roof_Sheet_Cladding"
roof_sheet.scale = (96.0, 31.0, 0.4)
bpy.ops.object.transform_apply(scale=True)
roof_sheet.data.materials.append(mat_roof_sheet)
link_col(roof_sheet, col_stands)

# -----------------------------------------------------------------------------
# 8. CURVA NORD (AUTHENTIC CURVED AMPHITHEATER GRANDSTAND) & CURVA SUD
# -----------------------------------------------------------------------------
# Curva Nord: Sweeping curved horseshoe grandstand set back behind open paved apron
# Shifted backward (Xc = 34.0) and restricted to center amphitheater arc (-48 deg to +48 deg)
Xc = 34.0
Yc = 0.0
R_in = 38.0
R_out = 54.0
Z_start = 1.8
Z_top = 9.8
num_tiers = 16
num_radial_segs = 48

theta_min = math.radians(-48.0) # Central 4-bay amphitheater stand matching Image 5
theta_max = math.radians(48.0)

d_theta = (theta_max - theta_min) / num_radial_segs
d_r = (R_out - R_in) / num_tiers
d_z = (Z_top - Z_start) / num_tiers

bm_cn = bmesh.new()
uv_cn = bm_cn.loops.layers.uv.new("UVMap")

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

        # Riser
        vr1 = bm_cn.verts.new((Xc + r0 * c0, Yc + r0 * s0, z0))
        vr2 = bm_cn.verts.new((Xc + r0 * c1, Yc + r0 * s1, z0))
        vr3 = bm_cn.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vr4 = bm_cn.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        fr = bm_cn.faces.new((vr1, vr2, vr3, vr4))
        fr.material_index = 0
        fr.loops[0][uv_cn].uv = (u0_norm, v0_norm)
        fr.loops[1][uv_cn].uv = (u1_norm, v0_norm)
        fr.loops[2][uv_cn].uv = (u1_norm, v0_norm + 0.015)
        fr.loops[3][uv_cn].uv = (u0_norm, v0_norm + 0.015)

        # Tread
        vt1 = bm_cn.verts.new((Xc + r0 * c0, Yc + r0 * s0, z1))
        vt2 = bm_cn.verts.new((Xc + r0 * c1, Yc + r0 * s1, z1))
        vt3 = bm_cn.verts.new((Xc + r1 * c1, Yc + r1 * s1, z1))
        vt4 = bm_cn.verts.new((Xc + r1 * c0, Yc + r1 * s0, z1))
        ft = bm_cn.faces.new((vt1, vt2, vt3, vt4))
        ft.material_index = 0
        ft.loops[0][uv_cn].uv = (u0_norm, v0_norm + 0.015)
        ft.loops[1][uv_cn].uv = (u1_norm, v0_norm + 0.015)
        ft.loops[2][uv_cn].uv = (u1_norm, v1_norm)
        ft.loops[3][uv_cn].uv = (u0_norm, v1_norm)

# Front curved brick retaining wall (height 1.8m)
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    ff = bm_cn.faces.new((
        bm_cn.verts.new((Xc + R_in * c0, Yc + R_in * s0, 0.0)),
        bm_cn.verts.new((Xc + R_in * c1, Yc + R_in * s1, 0.0)),
        bm_cn.verts.new((Xc + R_in * c1, Yc + R_in * s1, Z_start)),
        bm_cn.verts.new((Xc + R_in * c0, Yc + R_in * s0, Z_start))
    ))
    ff.material_index = 1 # Brick material

# Rear curved concrete facade (height Z_top)
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    fb = bm_cn.faces.new((
        bm_cn.verts.new((Xc + R_out * c1, Yc + R_out * s1, 0.0)),
        bm_cn.verts.new((Xc + R_out * c0, Yc + R_out * s0, 0.0)),
        bm_cn.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top)),
        bm_cn.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top))
    ))
    fb.material_index = 2 # Concrete material

# Side End-Cap Walls
for ang, sign in [(theta_min, -1), (theta_max, 1)]:
    ca, sa = math.cos(ang), math.sin(ang)
    for t in range(num_tiers):
        r0 = R_in + t * d_r
        r1 = R_in + (t + 1) * d_r
        z1 = Z_start + (t + 1) * d_z
        v1 = bm_cn.verts.new((Xc + r0 * ca, Yc + r0 * sa, 0.0))
        v2 = bm_cn.verts.new((Xc + r1 * ca, Yc + r1 * sa, 0.0))
        v3 = bm_cn.verts.new((Xc + r1 * ca, Yc + r1 * sa, z1))
        v4 = bm_cn.verts.new((Xc + r0 * ca, Yc + r0 * sa, z1))
        fc = bm_cn.faces.new((v1, v2, v3, v4) if sign > 0 else (v4, v3, v2, v1))
        fc.material_index = 2

bmesh.ops.remove_doubles(bm_cn, verts=bm_cn.verts, dist=0.01)
mesh_cn = bpy.data.meshes.new("Stand_Curva_Nord_Curved_Mesh")
bm_cn.to_mesh(mesh_cn)
bm_cn.free()

curva_nord = bpy.data.objects.new("Stand_Curva_Nord_Curved", mesh_cn)
curva_nord.data.materials.append(mat_curved_seats) # Slot 0: Curved seats
curva_nord.data.materials.append(mat_brick)        # Slot 1: Front brick wall
curva_nord.data.materials.append(mat_concrete)     # Slot 2: Concrete rear/sides
link_col(curva_nord, col_stands)

# Curved Blue Safety Railing along Top Rim
bm_rail = bmesh.new()
for s in range(num_radial_segs):
    ang0 = theta_min + s * d_theta
    ang1 = theta_min + (s + 1) * d_theta
    c0, s0 = math.cos(ang0), math.sin(ang0)
    c1, s1 = math.cos(ang1), math.sin(ang1)
    v1 = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top + 1.15))
    v2 = bm_rail.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top + 1.15))
    bm_rail.edges.new((v1, v2))
    v1m = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top + 0.6))
    v2m = bm_rail.verts.new((Xc + R_out * c1, Yc + R_out * s1, Z_top + 0.6))
    bm_rail.edges.new((v1m, v2m))
    if s % 3 == 0:
        v_base = bm_rail.verts.new((Xc + R_out * c0, Yc + R_out * s0, Z_top))
        bm_rail.edges.new((v_base, v1))

rail_mesh = bpy.data.meshes.new("Curva_Nord_Railing_Mesh")
bm_rail.to_mesh(rail_mesh)
bm_rail.free()
railing_obj = bpy.data.objects.new("Curva_Nord_Railing", rail_mesh)
railing_obj.data.materials.append(mat_railing)
mod_w = railing_obj.modifiers.new("Wireframe", type='WIREFRAME')
mod_w.thickness = 0.045
link_col(railing_obj, col_stands)

# Open Paved Apron between Pitch & Curved Stand
bm_ap = bmesh.new()
ap_verts_pitch = []
ap_verts_stand = []
for s in range(num_radial_segs + 1):
    ang = theta_min + s * d_theta
    c, s_val = math.cos(ang), math.sin(ang)
    vx_stand = Xc + R_in * c
    vy_stand = Yc + R_in * s_val
    vx_pitch = 53.5
    vy_pitch = vy_stand
    v_p = bm_ap.verts.new((vx_pitch, vy_pitch, 0.005))
    v_s = bm_ap.verts.new((vx_stand, vy_stand, 0.005))
    ap_verts_pitch.append(v_p)
    ap_verts_stand.append(v_s)

for s in range(num_radial_segs):
    bm_ap.faces.new((
        ap_verts_pitch[s],
        ap_verts_pitch[s+1],
        ap_verts_stand[s+1],
        ap_verts_stand[s]
    ))

# Fill corner wings between curved stand ends and stadium corners
# North side (towards Distinti, Y > 0):
ang_N = theta_max
cN, sN = math.cos(ang_N), math.sin(ang_N)
vx_sN = Xc + R_in * cN
vy_sN = Yc + R_in * sN
v_cN1 = bm_ap.verts.new((53.5, vy_sN, 0.005))
v_cN2 = bm_ap.verts.new((53.5, 42.0, 0.005))
v_cN3 = bm_ap.verts.new((68.0, 42.0, 0.005))
v_cN4 = bm_ap.verts.new((vx_sN, vy_sN, 0.005))
bm_ap.faces.new((v_cN1, v_cN2, v_cN3, v_cN4))

# South side (towards Tribuna, Y < 0):
ang_S = theta_min
cS, sS = math.cos(ang_S), math.sin(ang_S)
vx_sS = Xc + R_in * cS
vy_sS = Yc + R_in * sS
v_cS1 = bm_ap.verts.new((53.5, -42.0, 0.005))
v_cS2 = bm_ap.verts.new((53.5, vy_sS, 0.005))
v_cS3 = bm_ap.verts.new((vx_sS, vy_sS, 0.005))
v_cS4 = bm_ap.verts.new((68.0, -42.0, 0.005))
bm_ap.faces.new((v_cS1, v_cS2, v_cS3, v_cS4))

bmesh.ops.remove_doubles(bm_ap, verts=bm_ap.verts, dist=0.02)
ap_mesh = bpy.data.meshes.new("Curva_Nord_Apron_Mesh")
bm_ap.to_mesh(ap_mesh)
bm_ap.free()
ap_obj = bpy.data.objects.new("Curva_Nord_Apron", ap_mesh)
ap_obj.data.materials.append(mat_apron)
link_col(ap_obj, col_pitch)

# Curva Sud (Rectangular Stand with 1907 Mosaic)
curva_sud = create_solid_stepped_stand("Stand_Curva_Sud", 74.0, 56.0, 78.0, 1.2, 12.0, 22, mat_curva, mat_concrete)
curva_sud.rotation_euler = (0, 0, math.radians(90))
curva_sud.location = (0, 0, 0)
bpy.context.collection.objects.link(curva_sud)
bpy.context.view_layer.objects.active = curva_sud
bpy.ops.object.transform_apply(rotation=True)
bpy.context.collection.objects.unlink(curva_sud)
link_col(curva_sud, col_stands)

# -----------------------------------------------------------------------------
# 8b. CORNER PERIMETER GATES (OPEN CORNERS SHOWING LAKE COMO WATER)
# -----------------------------------------------------------------------------
# Curva Sud / Distinti Corner (-1, 1): Open view to Lake Como matching broadcast photo (Image 1)!
p_x0, p_y0 = -49.0, 42.0
p_x1, p_y1 = -56.0, 37.0
v_line = Vector((p_x1 - p_x0, p_y1 - p_y0, 0.0))
L_gate = v_line.length
p_mid = (Vector((p_x0, p_y0, 0.0)) + Vector((p_x1, p_y1, 0.0))) / 2.0
ang_g = math.atan2(v_line.y, v_line.x)

# 1. Low concrete curb (0.35m high)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(p_mid.x, p_mid.y, 0.175), rotation=(0, 0, ang_g))
curb = bpy.context.object
curb.name = "Corner_Seawall_Curb_NW"
curb.scale = (L_gate, 0.40, 0.35)
bpy.ops.object.transform_apply(scale=True)
curb.data.materials.append(mat_concrete)
link_col(curb, col_stands)

# 2. See-through vertical metal safety gate (vertical pickets with Lake Como water visible behind)
bm_gate = bmesh.new()
num_pickets = 18
picket_h = 1.30
for i in range(num_pickets + 1):
    fp = i / num_pickets
    pt = Vector((p_x0, p_y0, 0.35)) + v_line * fp
    vp1 = bm_gate.verts.new(pt)
    vp2 = bm_gate.verts.new(pt + Vector((0, 0, picket_h)))
    bm_gate.edges.new((vp1, vp2))

bm_gate.edges.new((
    bm_gate.verts.new((p_x0, p_y0, 0.35 + picket_h)),
    bm_gate.verts.new((p_x1, p_y1, 0.35 + picket_h))
))
bm_gate.edges.new((
    bm_gate.verts.new((p_x0, p_y0, 0.35 + picket_h * 0.5)),
    bm_gate.verts.new((p_x1, p_y1, 0.35 + picket_h * 0.5))
))
gate_mesh = bpy.data.meshes.new("Corner_Security_Gate_NW_Mesh")
bm_gate.to_mesh(gate_mesh)
bm_gate.free()
gate_obj = bpy.data.objects.new("Corner_Security_Gate_NW", gate_mesh)
gate_obj.data.materials.append(mat_railing)
mod_gw = gate_obj.modifiers.new("Wireframe", type='WIREFRAME')
mod_gw.thickness = 0.035
link_col(gate_obj, col_stands)

# 3. Blue Broadcast / TV Booth matching Image 1
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(-50.6, 38.6, 1.25))
tv_booth = bpy.context.object
tv_booth.name = "Corner_TV_Booth_NW"
tv_booth.scale = (1.8, 1.8, 2.2)
bpy.ops.object.transform_apply(scale=True)
tv_booth.data.materials.append(mat_booth_blue)
link_col(tv_booth, col_stands)

# 4. Authentic Curved Lamppost matching Image 1
bm_lamp = bmesh.new()
lamp_segs = 12
lamp_base = Vector((-52.5, 42.5, 0.0))
lamp_verts = []
for li in range(lamp_segs + 1):
    fli = li / lamp_segs
    # Curve gently toward field
    lz = fli * 7.5
    curve_x = 0.8 * (fli ** 2.2)
    curve_y = -0.5 * (fli ** 2.2)
    lv = bm_lamp.verts.new(lamp_base + Vector((curve_x, curve_y, lz)))
    lamp_verts.append(lv)

for li in range(lamp_segs):
    bm_lamp.edges.new((lamp_verts[li], lamp_verts[li + 1]))

lamp_mesh = bpy.data.meshes.new("Corner_Street_Light_NW_Mesh")
bm_lamp.to_mesh(lamp_mesh)
bm_lamp.free()
lamp_obj = bpy.data.objects.new("Corner_Street_Light_NW", lamp_mesh)
lamp_obj.data.materials.append(mat_lamp_pole)
mod_lw = lamp_obj.modifiers.new("Skin", type='SKIN')
for v in lamp_obj.data.skin_vertices[0].data:
    v.radius = (0.05, 0.05)
link_col(lamp_obj, col_stands)

# 5. South-West Corner (-1, -1) perimeter gate
p_sx0, p_sy0 = -49.0, -42.0
p_sx1, p_sy1 = -56.0, -37.0
sw_mid_x, sw_mid_y = (p_sx0 + p_sx1) / 2, (p_sy0 + p_sy1) / 2
sw_wall_len = math.hypot(p_sx1 - p_sx0, p_sy1 - p_sy0)
sw_angle = math.atan2(p_sy1 - p_sy0, p_sx1 - p_sx0)

bpy.ops.mesh.primitive_cube_add(size=1.0, location=(sw_mid_x, sw_mid_y, 0.9), rotation=(0, 0, sw_angle))
cwall_sw = bpy.context.object
cwall_sw.name = "Corner_Perimeter_Wall_-1_-1"
cwall_sw.scale = (sw_wall_len, 0.35, 1.8)
bpy.ops.object.transform_apply(scale=True)
cwall_sw.data.materials.append(mat_concrete)
link_col(cwall_sw, col_stands)

# -----------------------------------------------------------------------------
# 9. 4 CORNER CYLINDRICAL FLOODLIGHT MASTS (38 METERS HIGH)
# -----------------------------------------------------------------------------
# Based on user specification:
# - Located OUTSIDE the pitch in each corner of the stadium.
# - NOT square ("tiang yang bukan kotak") -> smooth tapered cylindrical tubular mast.
# - When facing the stand written "COMO" (Distinti, +Y):
#   - Left side corners (X < 0): Painted in alternating RED & WHITE aviation stripes.
#   - Right side corners (X > 0): Painted in clean WHITE.
# - Top headframe: 4 tiers of horizontal crossarms with 24 LED stadium projectors.
# - Rear: vertical service ladder.

def build_cylindrical_floodlight_tower(name, tx, ty, is_left_side):
    aim_target = Vector((0.0, 0.0, 1.0))
    pos = Vector((tx, ty, 0.0))
    dir_to_field = (aim_target - pos)
    dir_to_field.z = 0
    d = dir_to_field.normalized()
    up = Vector((0.0, 0.0, 1.0))
    w = d.cross(up).normalized()
    rear = -d
    
    # 1. Base Concrete Foundation Plinth
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=1.8, depth=0.6, location=(tx, ty, 0.3))
    plinth = bpy.context.object
    plinth.name = f"{name}_Plinth"
    plinth.data.materials.append(mat_concrete)
    link_col(plinth, col_towers)
    
    # 2. Conical Tapered Tubular Steel Mast (Smooth 32-sided cylinder)
    H_MAST = 38.0
    R_BASE = 1.15
    R_TOP = 0.52
    N_CIRC = 32
    
    bm_mast = bmesh.new()
    band_heights = [0.0, 5.4, 10.8, 16.2, 21.6, 27.0, 32.4, 38.0]
    rings = []
    
    for z in band_heights:
        fac = z / H_MAST
        r = R_BASE + (R_TOP - R_BASE) * fac
        ring = []
        for i in range(N_CIRC):
            theta = 2.0 * math.pi * i / N_CIRC
            vx = tx + r * math.cos(theta)
            vy = ty + r * math.sin(theta)
            ring.append(bm_mast.verts.new((vx, vy, z)))
        rings.append(ring)
        
    for b in range(len(band_heights) - 1):
        if is_left_side:
            mat_idx = 0 if (b % 2 == 0) else 1 # 0=Red, 1=White
        else:
            mat_idx = 1 # White
            
        r_low = rings[b]
        r_high = rings[b + 1]
        for i in range(N_CIRC):
            i_next = (i + 1) % N_CIRC
            f = bm_mast.faces.new((r_low[i], r_low[i_next], r_high[i_next], r_high[i]))
            f.material_index = mat_idx
            
    top_v = bm_mast.verts.new((tx, ty, H_MAST))
    for i in range(N_CIRC):
        i_next = (i + 1) % N_CIRC
        f = bm_mast.faces.new((rings[-1][i], rings[-1][i_next], top_v))
        f.material_index = 0 if is_left_side else 1
        
    mast_mesh = bpy.data.meshes.new(f"{name}_Mast_Mesh")
    bm_mast.to_mesh(mast_mesh)
    bm_mast.free()
    
    mast_obj = bpy.data.objects.new(f"{name}_Mast", mast_mesh)
    mast_obj.data.materials.append(mat_pylon_red)   # Index 0
    mast_obj.data.materials.append(mat_pylon_white) # Index 1
    for poly in mast_obj.data.polygons:
        poly.use_smooth = True
    link_col(mast_obj, col_towers)
    
    # 3. Headframe Catwalk & 4-Tier Crossbars
    bm_head = bmesh.new()
    z_cat = 31.0
    r_cat_in = R_BASE + (R_TOP - R_BASE) * (z_cat / H_MAST) + 0.05
    r_cat_out = 1.8
    N_CAT = 16
    cat_in = []
    cat_out = []
    for i in range(N_CAT):
        th = 2.0 * math.pi * i / N_CAT
        cat_in.append(bm_head.verts.new((tx + r_cat_in * math.cos(th), ty + r_cat_in * math.sin(th), z_cat)))
        cat_out.append(bm_head.verts.new((tx + r_cat_out * math.cos(th), ty + r_cat_out * math.sin(th), z_cat)))
    for i in range(N_CAT):
        i_next = (i + 1) % N_CAT
        bm_head.faces.new((cat_in[i], cat_in[i_next], cat_out[i_next], cat_out[i]))
        
    tiers = [
        (32.2, 6.4, 6),
        (34.0, 7.2, 6),
        (35.8, 7.2, 6),
        (37.5, 6.0, 6)
    ]
    
    def add_box_beam(bm, p_center, size_w, size_d, size_z, d_vec, w_vec):
        hw = size_w / 2
        hd = size_d / 2
        hz = size_z / 2
        corners = [
            p_center - w_vec*hw - d_vec*hd - up*hz,
            p_center + w_vec*hw - d_vec*hd - up*hz,
            p_center + w_vec*hw + d_vec*hd - up*hz,
            p_center - w_vec*hw + d_vec*hd - up*hz,
            p_center - w_vec*hw - d_vec*hd + up*hz,
            p_center + w_vec*hw - d_vec*hd + up*hz,
            p_center + w_vec*hw + d_vec*hd + up*hz,
            p_center - w_vec*hw + d_vec*hd + up*hz,
        ]
        vs = [bm.verts.new(c) for c in corners]
        bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
        bm.faces.new((vs[4], vs[7], vs[6], vs[5]))
        bm.faces.new((vs[0], vs[4], vs[5], vs[1]))
        bm.faces.new((vs[1], vs[5], vs[6], vs[2]))
        bm.faces.new((vs[2], vs[6], vs[7], vs[3]))
        bm.faces.new((vs[3], vs[7], vs[4], vs[0]))

    for z_t, bar_len, num_lamps in tiers:
        c_p = Vector((tx, ty, z_t)) + d * 0.45
        add_box_beam(bm_head, c_p, 0.35, 0.9, 0.22, d, w)
        bar_center = Vector((tx, ty, z_t)) + d * 0.9
        add_box_beam(bm_head, bar_center, bar_len, 0.22, 0.22, d, w)
        
    head_mesh = bpy.data.meshes.new(f"{name}_Headframe_Mesh")
    bm_head.to_mesh(head_mesh)
    bm_head.free()
    head_obj = bpy.data.objects.new(f"{name}_Headframe", head_mesh)
    head_obj.data.materials.append(mat_pylon_red if is_left_side else mat_steel_dark)
    link_col(head_obj, col_towers)
    
    # 4. Projector Floodlights
    bm_proj = bmesh.new()
    for z_t, bar_len, num_lamps in tiers:
        bar_center = Vector((tx, ty, z_t)) + d * 0.9
        span = bar_len - 0.8
        step = span / (num_lamps - 1)
        for i in range(num_lamps):
            offset_w = -span / 2 + i * step
            lamp_center = bar_center + w * offset_w + d * 0.25
            add_box_beam(bm_proj, lamp_center, 0.58, 0.32, 0.32, d, w)
            
    proj_mesh = bpy.data.meshes.new(f"{name}_Projectors_Mesh")
    bm_proj.to_mesh(proj_mesh)
    bm_proj.free()
    proj_obj = bpy.data.objects.new(f"{name}_Projectors", proj_mesh)
    proj_obj.data.materials.append(mat_lens)
    link_col(proj_obj, col_towers)
    
    # 5. Service Ladder
    bm_lad = bmesh.new()
    r_lad = R_BASE + 0.12
    lad_base = Vector((tx, ty, 0.0)) + rear * r_lad
    lad_top = Vector((tx, ty, 31.0)) + rear * (R_BASE + (R_TOP - R_BASE)*(31.0/H_MAST) + 0.12)
    w_lad = 0.44
    for r_z in range(1, 31):
        fac = r_z / 31.0
        p_c = (1.0 - fac) * lad_base + fac * lad_top
        p_c.z = float(r_z)
        add_box_beam(bm_lad, p_c, w_lad, 0.04, 0.04, d, w)
        
    lad_mesh = bpy.data.meshes.new(f"{name}_Ladder_Mesh")
    bm_lad.to_mesh(lad_mesh)
    bm_lad.free()
    lad_obj = bpy.data.objects.new(f"{name}_Ladder", lad_mesh)
    lad_obj.data.materials.append(mat_steel_dark)
    link_col(lad_obj, col_towers)
    
    # 6. Spotlight Light Object
    bpy.ops.object.light_add(type='SPOT', location=(tx + d.x * 1.2, ty + d.y * 1.2, 36.0))
    s_light = bpy.context.object
    s_light.name = f"{name}_Spotlight"
    s_light.data.energy = 15000.0
    s_light.data.spot_size = math.radians(75.0)
    s_light.data.spot_blend = 0.50
    s_light.data.color = (1.0, 0.97, 0.92)
    aim_v = aim_target - Vector((tx, ty, 36.0))
    s_light.rotation_euler = aim_v.to_track_quat('-Z', 'Y').to_euler()
    link_col(s_light, col_towers)

# 4 Corner Floodlight Towers:
# Left side corners (X < 0): Red-White striped masts
# Right side corners (X > 0): Pure White masts
tower_locs = [
    ("Tower_SW", -59.0, -46.0, True),  # Left corner, Curva Sud / Tribuna
    ("Tower_NW", -59.0,  46.0, True),  # Left corner, Curva Sud / Distinti (Lake side)
    ("Tower_SE",  59.0, -46.0, False), # Right corner, Curva Nord / Tribuna
    ("Tower_NE",  59.0,  46.0, False), # Right corner, Curva Nord / Distinti (Lake side)
]

for tname, tx, ty, is_left in tower_locs:
    build_cylindrical_floodlight_tower(tname, tx, ty, is_left)

# -----------------------------------------------------------------------------
# 9b. MONUMENTO AI CADUTI (HISTORIC WAR MEMORIAL TOWER - 30 METERS)
# -----------------------------------------------------------------------------
# Iconic Rationalist monument designed by Giuseppe Terragni & Antonio Sant'Elia (1931-1933)
# Located right behind Distinti / Curva Nord corner along Viale Puecher on the lakefront
# Plinth / Stone steps base
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(54.0, 68.0, 0.4))
plinth = bpy.context.object
plinth.name = "Monumento_Plinth_Base"
plinth.scale = (16.0, 14.0, 0.8)
bpy.ops.object.transform_apply(scale=True)
plinth.data.materials.append(mat_monument)
link_col(plinth, col_env)

# Monolithic 30m White Stone Tower
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(54.0, 68.0, 15.0))
monument = bpy.context.object
monument.name = "Monumento_ai_Caduti_Tower"
monument.scale = (11.5, 9.5, 30.0)
bpy.ops.object.transform_apply(scale=True)
monument.data.materials.append(mat_monument)
link_col(monument, col_env)

# Central Vertical Slit Opening (Architectural cutout through tower)
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(54.0, 68.0, 16.5))
slit = bpy.context.object
slit.name = "Monumento_Center_Slit"
slit.scale = (3.2, 9.8, 25.0)
bpy.ops.object.transform_apply(scale=True)
slit.data.materials.append(mat_void)
link_col(slit, col_env)

# Top Flagpole & Italian Flag
bpy.ops.mesh.primitive_cylinder_add(radius=0.10, depth=6.5, location=(54.0, 68.0, 33.25))
pole = bpy.context.object
pole.name = "Monumento_Flagpole"
pole.data.materials.append(mat_lamp_pole)
link_col(pole, col_env)

bpy.ops.mesh.primitive_plane_add(size=1.0, location=(54.0, 69.2, 35.0), rotation=(math.radians(90), 0, math.radians(90)))
flag = bpy.context.object
flag.name = "Monumento_Italian_Flag"
flag.scale = (2.2, 1.4, 1.0)
bpy.ops.object.transform_apply(scale=True)
flag.data.materials.append(mat_flag_red)
link_col(flag, col_env)

# -----------------------------------------------------------------------------
# 10. VAST EXPANSE OF LAKE COMO WATER & 360 PANORAMA BACKDROP
# -----------------------------------------------------------------------------
# 1. 3D Lake Water Surface positioned exactly at seawall waterline (Z = -0.15m)
bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 40.0, -0.15))
lake = bpy.context.object
lake.name = "Lake_Como_Water_Surface"
lake.scale = (2400.0, 2400.0, 1.0)
bpy.ops.object.transform_apply(scale=True)
lake.data.materials.append(mat_lake)
link_col(lake, col_env)

# 2. 360-Degree Seamless Cylindrical Backdrop Screen (Lake Como Panorama)
# Radius R = 380m, height Z from -8.0m to 120m, continuous 360-degree cylindrical environment
bm_bd = bmesh.new()
uv_bd = bm_bd.loops.layers.uv.new("UVMap")
R_bd = 380.0
Z_bd_bot = -8.0
Z_bd_top = 120.0
ang_bd_min = 0.0
ang_bd_max = 2.0 * math.pi
num_bd_segs = 96
d_bd_ang = (ang_bd_max - ang_bd_min) / num_bd_segs

for s in range(num_bd_segs):
    a0 = ang_bd_min + s * d_bd_ang
    a1 = ang_bd_min + (s + 1) * d_bd_ang
    u0 = s / num_bd_segs
    u1 = (s + 1) / num_bd_segs

    ca0, sa0 = math.cos(a0), math.sin(a0)
    ca1, sa1 = math.cos(a1), math.sin(a1)

    v1 = bm_bd.verts.new((R_bd * ca0, R_bd * sa0, Z_bd_bot))
    v2 = bm_bd.verts.new((R_bd * ca1, R_bd * sa1, Z_bd_bot))
    v3 = bm_bd.verts.new((R_bd * ca1, R_bd * sa1, Z_bd_top))
    v4 = bm_bd.verts.new((R_bd * ca0, R_bd * sa0, Z_bd_top))

    # Inward facing polygon
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
link_col(bd_obj, col_env)

# Concrete Embankment / SeaWall supporting the stadium island (Hollow perimeter ring: ZERO Z-fighting under pitch!)
bm_sw = bmesh.new()
sw_out_w, sw_out_d = 136.6, 96.6
sw_v_out_top = [
    bm_sw.verts.new((-sw_out_w/2, -sw_out_d/2, -0.05)),
    bm_sw.verts.new(( sw_out_w/2, -sw_out_d/2, -0.05)),
    bm_sw.verts.new(( sw_out_w/2,  sw_out_d/2, -0.05)),
    bm_sw.verts.new((-sw_out_w/2,  sw_out_d/2, -0.05)),
]
sw_v_out_bot = [
    bm_sw.verts.new((-sw_out_w/2, -sw_out_d/2, -0.65)),
    bm_sw.verts.new(( sw_out_w/2, -sw_out_d/2, -0.65)),
    bm_sw.verts.new(( sw_out_w/2,  sw_out_d/2, -0.65)),
    bm_sw.verts.new((-sw_out_w/2,  sw_out_d/2, -0.65)),
]
for i in range(4):
    i_next = (i + 1) % 4
    bm_sw.faces.new((sw_v_out_top[i], sw_v_out_top[i_next], sw_v_out_bot[i_next], sw_v_out_bot[i]))

sw_mesh = bpy.data.meshes.new("Stadium_SeaWall_Perimeter_Mesh")
bm_sw.to_mesh(sw_mesh)
bm_sw.free()
seawall = bpy.data.objects.new("Stadium_SeaWall_Perimeter", sw_mesh)
seawall.data.materials.append(mat_concrete)
link_col(seawall, col_pitch)

# -----------------------------------------------------------------------------
# 12. WORLD ENVIRONMENT & SUNLIGHT
# -----------------------------------------------------------------------------
scene.world.use_nodes = True
w_nt = scene.world.node_tree
w_nt.nodes.clear()
w_out = w_nt.nodes.new('ShaderNodeOutputWorld')
w_bg = w_nt.nodes.new('ShaderNodeBackground')
w_bg.inputs['Color'].default_value = (0.47, 0.65, 0.84, 1.0)
w_bg.inputs['Strength'].default_value = 1.15
w_nt.links.new(w_bg.outputs['Background'], w_out.inputs['Surface'])

# Warm Italian Sun
bpy.ops.object.light_add(type='SUN', location=(70.0, -90.0, 120.0))
sun = bpy.context.object
sun.name = "Sun_Como_Afternoon"
sun.data.energy = 6.2
sun.data.angle = math.radians(2.5)
sun.data.color = (1.0, 0.96, 0.91)
sun.rotation_euler = (math.radians(48.0), math.radians(16.0), math.radians(-32.0))
link_col(sun, col_towers)

# -----------------------------------------------------------------------------
# 13. CAMERAS FOR ALL KEY VIEWPOINTS
# -----------------------------------------------------------------------------
cameras_def = [
    # 1. Main TV Broadcast Camera (Elevated sideline view, unblocked panoramic framing)
    ("Cam_1_SerieA_Broadcast", (0.0, -56.0, 16.0), (0.0, 15.0, 2.0), 32.0),
    
    # 2. Clean Wide Panorama (Capturing Distinti COMO stand, lake backdrop, and both floodlight towers)
    ("Cam_2_Wide_Panorama", (0.0, -50.0, 13.0), (0.0, 25.0, 2.0), 21.0),
    
    # 3. Distinti Face-on View (Matching "C O + M O" stand with mountain & water backdrop)
    ("Cam_3_Distinti_COMO", (0.0, -12.0, 5.0), (0.0, 52.0, 7.5), 32.0),
    
    # 4. Under Steel Roof Truss View (Architectural view looking out under the dark roof canopy)
    ("Cam_4_Roof_Truss_View", (0.0, -60.0, 14.5), (0.0, 48.0, 7.0), 26.0),
    
    # 5. Low Goal & Penalty Box Action Angle (Right Goal with Curved Curva Nord and White Floodlight Mast)
    ("Cam_5_Goal_Action", (40.0, -22.0, 2.6), (65.0, 5.0, 4.2), 38.0),

    # 6. Left Goal & Curva Sud Action (Left Goal with Curva Sud and red-white floodlight mast)
    ("Cam_6_Goal_Left_Lake", (-36.0, -16.0, 2.2), (-52.5, 0.0, 1.8), 42.0),

    # 7. Match User Reference Photo POV (Diagonal view from Tribuna looking at COMO and water)
    ("Cam_User_Photo_Match", (-24.0, -52.0, 13.5), (10.0, 22.0, 2.5), 20.0),

    # 8. Curva Sud 1907 Direct Stand POV (Matching user reference with red-white floodlight towers)
    ("Cam_8_Curva_1907_POV", (-22.0, 0.0, 3.2), (-56.0, 0.0, 5.0), 19.0),

    # 9. Hexagonal Net & Tension Stanchion Goal Inspection Closeup
    ("Cam_9_Goal_Closeup", (-50.5, -2.2, 1.8), (-53.5, -3.66, 2.3), 42.0),

    # 10. Front of Left Goal (Penalty Spot View facing Curva Sud)
    ("Cam_10_Front_Goal_Left", (-41.5, 0.0, 1.65), (-52.5, 0.0, 1.22), 28.0),

    # 11. Front of Right Goal (Penalty Spot View facing Curved Curva Nord)
    ("Cam_11_Front_Goal_Right", (41.5, 0.0, 1.65), (70.0, 0.0, 4.5), 26.0),

    # 12. Drone Aerial Overview (Matching User Drone Reference Image 2)
    ("Cam_12_Drone_Sinigaglia_Match", (86.0, 48.0, 48.0), (-15.0, -8.0, 4.0), 22.0),

    # 13. Match User Corner View (Corner gap between Curva Sud and Distinti showing Lake Como water)
    ("Cam_User_Corner_Match", (-26.0, 12.0, 2.8), (-58.0, 44.0, 5.5), 28.0),

    # 14. Match User Monumento ai Caduti View (Looking towards northeast corner at Distinti and Monumento)
    ("Cam_14_Monumento_Match", (16.0, 12.0, 2.8), (54.0, 56.0, 12.0), 32.0),
]

created_cams = {}
for cname, loc, aim, flen in cameras_def:
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.name = cname
    cam.data.lens = flen
    cam.data.clip_end = 2000.0
    dir_vec = Vector(aim) - Vector(loc)
    cam.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()
    link_col(cam, col_cams)
    created_cams[cname] = cam

scene.camera = created_cams["Cam_1_SerieA_Broadcast"]

# -----------------------------------------------------------------------------
# 14. SAVE MASTER BLEND FILE
# -----------------------------------------------------------------------------
# Force Viewport Shading for all 3D Viewport spaces to use Scene World & Scene Lights
# This completely eliminates default blurry forest.exr in Material Preview mode!
for window in bpy.context.window_manager.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.use_scene_world = True
                    space.shading.use_scene_lights = True

bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
print("SUCCESS: Master Stadio Sinigaglia model saved to:", BLEND_PATH)

# -----------------------------------------------------------------------------
# 15. RENDER PREVIEWS FOR ALL 5 CAMERA ANGLES
# -----------------------------------------------------------------------------
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
engine_items = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items]
if 'BLENDER_EEVEE_NEXT' in engine_items:
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
elif 'BLENDER_EEVEE' in engine_items:
    scene.render.engine = 'BLENDER_EEVEE'
else:
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 32

for cname, cam_obj in created_cams.items():
    scene.camera = cam_obj
    out_img = os.path.join(OUT, f"preview_stadium_{cname}.png")
    scene.render.filepath = out_img
    print(f"Rendering {cname} -> {out_img}...")
    bpy.ops.render.render(write_still=True)

scene.camera = created_cams["Cam_1_SerieA_Broadcast"]
bpy.ops.wm.save_mainfile()
print("ALL RENDERS COMPLETED SUCCESSFULLY!")
