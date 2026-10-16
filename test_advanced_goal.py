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

# -----------------------------------------------------------------------------
# 1. PBR MATERIALS FOR PROFESSIONAL TENSION-STANCHION GOAL
# -----------------------------------------------------------------------------
# Material 1: Glossy Powder-Coated Aluminum Posts & Crossbar
mat_posts = bpy.data.materials.get("M_Goal_Posts_White")
if not mat_posts:
    mat_posts = bpy.data.materials.new("M_Goal_Posts_White")
mat_posts.use_nodes = True
p_nt = mat_posts.node_tree
p_bsdf = next(n for n in p_nt.nodes if n.type == 'BSDF_PRINCIPLED')
p_bsdf.inputs['Base Color'].default_value = (0.96, 0.97, 0.99, 1.0)
p_bsdf.inputs['Roughness'].default_value = 0.18
p_bsdf.inputs['Metallic'].default_value = 0.08
if 'Specular IOR Level' in p_bsdf.inputs:
    p_bsdf.inputs['Specular IOR Level'].default_value = 0.55

# Material 2: Dark Galvanized Steel Stanchions & Tension Cables
mat_stanchion = bpy.data.materials.get("M_Goal_Stanchion_Steel")
if not mat_stanchion:
    mat_stanchion = bpy.data.materials.new("M_Goal_Stanchion_Steel")
mat_stanchion.use_nodes = True
s_nt = mat_stanchion.node_tree
s_bsdf = next(n for n in s_nt.nodes if n.type == 'BSDF_PRINCIPLED')
s_bsdf.inputs['Base Color'].default_value = (0.12, 0.13, 0.15, 1.0)
s_bsdf.inputs['Roughness'].default_value = 0.45
s_bsdf.inputs['Metallic'].default_value = 0.85

# Material 3: Hexagonal Honeycomb PBR Netting
mat_net = bpy.data.materials.get("M_Goal_Net_Hexagonal")
if not mat_net:
    mat_net = bpy.data.materials.new("M_Goal_Net_Hexagonal")
mat_net.use_nodes = True
n_nt = mat_net.node_tree
n_nt.nodes.clear()

n_out = n_nt.nodes.new('ShaderNodeOutputMaterial')
n_bsdf = n_nt.nodes.new('ShaderNodeBsdfPrincipled')
n_tex_coord = n_nt.nodes.new('ShaderNodeTexCoord')
n_mapping = n_nt.nodes.new('ShaderNodeMapping')
n_tex_col = n_nt.nodes.new('ShaderNodeTexImage')
n_tex_norm = n_nt.nodes.new('ShaderNodeTexImage')
n_norm_map = n_nt.nodes.new('ShaderNodeNormalMap')

# Load net textures
tex_col_path = os.path.join(ASSETS, "como_hex_net_color.png")
tex_norm_path = os.path.join(ASSETS, "como_hex_net_normal.png")
img_col = bpy.data.images.load(tex_col_path, check_existing=True)
img_norm = bpy.data.images.load(tex_norm_path, check_existing=True)
img_norm.colorspace_settings.name = 'Non-Color'

n_tex_col.image = img_col
n_tex_norm.image = img_norm

# UV tiling scale: exactly 1.0 so texture tiles at FIFA regulation cell density (~11cm cells)
n_mapping.inputs['Scale'].default_value = (1.0, 1.0, 1.0)


# Connect nodes
n_nt.links.new(n_tex_coord.outputs['UV'], n_mapping.inputs['Vector'])
n_nt.links.new(n_mapping.outputs['Vector'], n_tex_col.inputs['Vector'])
n_nt.links.new(n_mapping.outputs['Vector'], n_tex_norm.inputs['Vector'])

# Color & Alpha
n_nt.links.new(n_tex_col.outputs['Color'], n_bsdf.inputs['Base Color'])
if 'Alpha' in n_bsdf.inputs:
    n_nt.links.new(n_tex_col.outputs['Alpha'], n_bsdf.inputs['Alpha'])

# Normal map
n_norm_map.inputs['Strength'].default_value = 1.2
n_nt.links.new(n_tex_norm.outputs['Color'], n_norm_map.inputs['Color'])
n_nt.links.new(n_norm_map.outputs['Normal'], n_bsdf.inputs['Normal'])

# Nylon rope roughness & sheen
n_bsdf.inputs['Roughness'].default_value = 0.78
if 'Sheen Roughness' in n_bsdf.inputs:
    n_bsdf.inputs['Sheen Roughness'].default_value = 0.5

n_nt.links.new(n_bsdf.outputs['BSDF'], n_out.inputs['Surface'])

# Transparency settings
mat_net.blend_method = 'CLIP'
if hasattr(mat_net, 'shadow_method'):
    mat_net.shadow_method = 'CLIP'

# -----------------------------------------------------------------------------
# 2. BUILD ADVANCED FIFA GOAL GEOMETRY
# -----------------------------------------------------------------------------
def build_advanced_football_goal(side, name):
    col_pitch = bpy.data.collections.get("01_Pitch_And_Field")
    
    # Remove existing old goal objects if any
    for obj in list(bpy.data.objects):
        if obj.name.startswith(name):
            bpy.data.objects.remove(obj, do_unlink=True)
            
    gx = side * 52.5
    dir_x = side
    gw = 7.32
    gh = 2.44
    pr = 0.06 # Post radius 6cm
    
    goal_objs = []
    
    # A. Goal Frame (Posts + Crossbar + Corner Elbows)
    # Left Post
    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gh, location=(gx, -gw/2, gh/2), vertices=32)
    p_l = bpy.context.object
    p_l.name = f"{name}_Post_L"
    p_l.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_objs.append(p_l)
    
    # Right Post
    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gh, location=(gx, gw/2, gh/2), vertices=32)
    p_r = bpy.context.object
    p_r.name = f"{name}_Post_R"
    p_r.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_objs.append(p_r)
    
    # Crossbar
    bpy.ops.mesh.primitive_cylinder_add(radius=pr, depth=gw, location=(gx, 0, gh), rotation=(math.radians(90), 0, 0), vertices=32)
    cbar = bpy.context.object
    cbar.name = f"{name}_Crossbar"
    cbar.data.materials.append(mat_posts)
    bpy.ops.object.shade_smooth()
    goal_objs.append(cbar)
    
    # Corner elbow spheres
    for ey in [-gw/2, gw/2]:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=pr, location=(gx, ey, gh), segments=24, ring_count=16)
        elbow = bpy.context.object
        elbow.name = f"{name}_Elbow_{ey}"
        elbow.data.materials.append(mat_posts)
        bpy.ops.object.shade_smooth()
        goal_objs.append(elbow)

    # B. Ground Base Frame (Tubular frame holding net to grass)
    d_bot = 2.2 # Bottom depth
    x_bot = gx + dir_x * d_bot
    b_rad = 0.025 # 5cm pipe
    
    # Left ground pipe
    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=d_bot, location=(gx + dir_x * d_bot/2, -gw/2, b_rad), rotation=(0, math.radians(90), 0), vertices=16)
    gp_l = bpy.context.object
    gp_l.name = f"{name}_Ground_Pipe_L"
    gp_l.data.materials.append(mat_stanchion)
    goal_objs.append(gp_l)
    
    # Right ground pipe
    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=d_bot, location=(gx + dir_x * d_bot/2, gw/2, b_rad), rotation=(0, math.radians(90), 0), vertices=16)
    gp_r = bpy.context.object
    gp_r.name = f"{name}_Ground_Pipe_R"
    gp_r.data.materials.append(mat_stanchion)
    goal_objs.append(gp_r)
    
    # Rear ground cross pipe
    bpy.ops.mesh.primitive_cylinder_add(radius=b_rad, depth=gw, location=(x_bot, 0, b_rad), rotation=(math.radians(90), 0, 0), vertices=16)
    gp_b = bpy.context.object
    gp_b.name = f"{name}_Ground_Pipe_Back"
    gp_b.data.materials.append(mat_stanchion)
    goal_objs.append(gp_b)

    # C. 3 Rear Tension Stanchions (Tiang Penegang Belakang)
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
        goal_objs.append(smast)
        
        # Ground base plinth plate
        bpy.ops.mesh.primitive_cylinder_add(radius=st_r*2.2, depth=0.06, location=(x_st, sy, 0.03), vertices=16)
        splinth = bpy.context.object
        splinth.name = f"{name}_Stanchion_Plinth_{s_idx}"
        splinth.data.materials.append(mat_stanchion)
        goal_objs.append(splinth)
        
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
        goal_objs.append(anc_wire)

    # D. Tension Sling Cables (Kawat Sling Penarik Sudut & Atas Jaring)
    d_top = 1.0 # 1.0m top net shelf depth
    x_top = gx + dir_x * d_top
    
    # 3 tension connection points on net:
    net_conn_pts = [
        Vector((x_top, -gw/2, gh)),     # Top-Left corner
        Vector((x_top, 0.0, gh - 0.05)),# Top-Center edge
        Vector((x_top,  gw/2, gh))      # Top-Right corner
    ]
    
    for s_idx, (sy, p_net) in enumerate(zip(stanchion_ys, net_conn_pts)):
        p_st = Vector((x_st, sy, h_st - 0.08))
        v_cable = p_net - p_st
        bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=v_cable.length, location=(p_st + p_net)/2, vertices=12)
        cable = bpy.context.object
        cable.name = f"{name}_Tension_Cable_{s_idx}"
        cable.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        cable.data.materials.append(mat_stanchion)
        goal_objs.append(cable)
        
        # Turnbuckle tensioner
        bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=0.15, location=p_st + v_cable*0.25, vertices=12)
        tb = bpy.context.object
        tb.name = f"{name}_Turnbuckle_{s_idx}"
        tb.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        tb.data.materials.append(mat_stanchion)
        goal_objs.append(tb)

    # E. Hexagonal Netting with Realistic Gravity Sag / Catenary Draping
    bm_net = bmesh.new()
    
    # Subdivided grid resolution
    NY = 28 # Along width (-3.66 to +3.66)
    NX_top = 8 # Along top shelf (gx to x_top)
    NZ_back = 16 # Along back drop (x_top,gh down to x_bot,0)
    
    y_coords = [ -gw/2 + i * (gw / NY) for i in range(NY + 1) ]
    
    # 1. Top Panel Vertices (Roof)
    top_verts = []
    for ix in range(NX_top + 1):
        row_verts = []
        fx = ix / NX_top # 0.0 at crossbar, 1.0 at rear edge
        cur_x = gx + dir_x * (fx * d_top)
        
        for iy, cy in enumerate(y_coords):
            # Parabolic gravity sag: max sag 9 cm in center of roof
            fy = cy / (gw / 2) # -1.0 to +1.0
            sag = 0.09 * (1.0 - fy**2) * math.sin(math.pi * fx)
            cur_z = gh - sag
            
            v = bm_net.verts.new((cur_x, cy, cur_z))
            row_verts.append(v)
        top_verts.append(row_verts)
        
    # Top Panel Faces & UV
    for ix in range(NX_top):
        for iy in range(NY):
            bm_net.faces.new((
                top_verts[ix][iy],
                top_verts[ix+1][iy],
                top_verts[ix+1][iy+1],
                top_verts[ix][iy+1]
            ))

    # 2. Back Panel Vertices (Drop)
    back_verts = [top_verts[NX_top]] # Share the rear top row!
    for iz in range(1, NZ_back + 1):
        row_verts = []
        fz = iz / NZ_back # 0.0 at top, 1.0 at ground
        cur_x = x_top + (x_bot - x_top) * fz
        cur_z = gh * (1.0 - fz)
        
        for iy, cy in enumerate(y_coords):
            fy = cy / (gw / 2)
            # Subtle wave / drape near bottom
            sag_x = dir_x * 0.03 * (1.0 - fy**2) * math.sin(math.pi * fz)
            v = bm_net.verts.new((cur_x + sag_x, cy, cur_z))
            row_verts.append(v)
        back_verts.append(row_verts)
        
    # Back Panel Faces
    for iz in range(NZ_back):
        for iy in range(NY):
            bm_net.faces.new((
                back_verts[iz][iy],
                back_verts[iz+1][iy],
                back_verts[iz+1][iy+1],
                back_verts[iz][iy+1]
            ))

    # 3. Left Side Panel Vertices & Faces
    # Left side drops from top_verts[ix][0] down to ground
    side_l_verts = []
    NZ_side = 12
    for iz in range(NZ_side + 1):
        row_v = []
        fz = iz / NZ_side
        cur_z = gh * (1.0 - fz)
        for ix in range(NX_top + 1):
            fx = ix / NX_top
            cur_x = gx + dir_x * (fx * (d_top + (d_bot - d_top) * fz))
            # Subtle hourglass pinch inward
            pinch_y = 0.02 * math.sin(math.pi * fz) * math.sin(math.pi * fx)
            cur_y = -gw/2 + pinch_y
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

    # 4. Right Side Panel Vertices & Faces
    side_r_verts = []
    for iz in range(NZ_side + 1):
        row_v = []
        fz = iz / NZ_side
        cur_z = gh * (1.0 - fz)
        for ix in range(NX_top + 1):
            fx = ix / NX_top
            cur_x = gx + dir_x * (fx * (d_top + (d_bot - d_top) * fz))
            pinch_y = 0.02 * math.sin(math.pi * fz) * math.sin(math.pi * fx)
            cur_y = gw/2 - pinch_y
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

    # Remove overlapping doubles along shared seams
    bmesh.ops.remove_doubles(bm_net, verts=bm_net.verts, dist=0.015)

    # Seamless Box UV Mapping for Hexagonal Net
    uv_layer = bm_net.loops.layers.uv.new("UVMap")
    for face in bm_net.faces:
        is_side_panel = abs(face.normal.y) > 0.70
        for loop in face.loops:
            vx, vy, vz = loop.vert.co
            if is_side_panel:
                u = abs(vx - gx) * 0.55
                v = vz * 0.55
            else:
                u = (vy + gw/2) * 0.55
                v = (abs(vx - gx) + vz) * 0.55
            loop[uv_layer].uv = (u, v)



    net_mesh = bpy.data.meshes.new(f"{name}_Hex_Net_Mesh")
    bm_net.to_mesh(net_mesh)
    bm_net.free()
    
    net_obj = bpy.data.objects.new(f"{name}_Hex_Net", net_mesh)
    net_obj.data.materials.append(mat_net)
    goal_objs.append(net_obj)

    # Link all objects to Pitch Collection
    for ob in goal_objs:
        if col_pitch and ob.name not in col_pitch.objects:
            col_pitch.objects.link(ob)
    print(f"Built advanced goal '{name}' with {len(goal_objs)} components.")

# Build both goals
build_advanced_football_goal(-1, "Goal_Left_North")
build_advanced_football_goal( 1, "Goal_Right_South")

# Set up Cam_5_Goal_Action and render test
cam = bpy.data.objects.get("Cam_5_Goal_Action")
bpy.context.scene.camera = cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_goal = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_advanced_goal_Cam_5.png"
bpy.context.scene.render.filepath = preview_goal
bpy.ops.render.render(write_still=True)
print("Rendered goal test to:", preview_goal)

# Also render Cam_6_Goal_Left_Lake
cam6 = bpy.data.objects.get("Cam_6_Goal_Left_Lake")
bpy.context.scene.camera = cam6
preview_cam6 = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_advanced_goal_Cam_6.png"
bpy.context.scene.render.filepath = preview_cam6
bpy.ops.render.render(write_still=True)
print("Rendered Cam 6 test to:", preview_cam6)

# Pack and save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved upgraded blend file successfully!")
