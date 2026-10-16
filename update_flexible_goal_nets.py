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
col_pitch = bpy.data.collections.get("01_Pitch_And_Field") or bpy.context.scene.collection

# Retrieve PBR Materials
mat_net = bpy.data.materials.get("M_Goal_Net_Hexagonal")
mat_posts = bpy.data.materials.get("M_Goal_Posts_White")
mat_stanchion = bpy.data.materials.get("M_Goal_Stanchion_Steel")

def build_gravity_flexible_net(side, name):
    gx = side * 52.5
    dir_x = side
    gw = 7.32
    gh = 2.44
    d_top = 1.05
    d_bot = 2.25

    # Remove previous net object if exists
    old_net = bpy.data.objects.get(f"{name}_Hex_Net")
    if old_net:
        bpy.data.objects.remove(old_net, do_unlink=True)
    old_mesh = bpy.data.meshes.get(f"{name}_Hex_Net_Mesh")
    if old_mesh:
        bpy.data.meshes.remove(old_mesh, do_unlink=True)

    # Remove and rebuild tension cables to match sagging attachment points
    for s_idx in range(3):
        old_cb = bpy.data.objects.get(f"{name}_Tension_Cable_{s_idx}")
        if old_cb:
            bpy.data.objects.remove(old_cb, do_unlink=True)
        old_tb = bpy.data.objects.get(f"{name}_Turnbuckle_{s_idx}")
        if old_tb:
            bpy.data.objects.remove(old_tb, do_unlink=True)

    # 1. GENERATE FLEXIBLE NET MESH WITH NATURAL GRAVITY DRAPE
    bm = bmesh.new()
    NY = 36         # 36 columns across 7.32m width (~20cm per quad)
    NX_top = 10     # 10 rows along 1.05m top shelf
    NZ_back = 24    # 24 rows along 2.44m back drop
    NZ_side = 18    # 18 rows for side panels

    y_coords = [ -gw/2 + i * (gw / NY) for i in range(NY + 1) ]

    # Stanchion attachment Y positions: left corner, center, right corner
    stanchion_ys = [-gw/2 - 0.25, 0.0, gw/2 + 0.25]
    cable_anchor_ys = [-gw/2, 0.0, gw/2]

    # --- TOP SHELF (ROOF) WITH CATENARY GRAVITY SAG ---
    top_verts = []
    for ix in range(NX_top + 1):
        row_verts = []
        fx = ix / NX_top
        
        for iy, cy in enumerate(y_coords):
            norm_y = cy / (gw / 2) # -1.0 to 1.0
            
            # Sag of the rear rope between the 3 cable attachment points:
            if cy <= 0.0:
                # Left bay: between -gw/2 and 0.0
                frac_bay = (cy + gw/2) / (gw/2) # 0 to 1
                rope_dip = 0.12 * math.sin(math.pi * frac_bay)
            else:
                # Right bay: between 0.0 and gw/2
                frac_bay = cy / (gw/2) # 0 to 1
                rope_dip = 0.12 * math.sin(math.pi * frac_bay)
            
            # Center cable has a slight 4cm compliance dip relative to rigid corner posts
            center_cable_dip = 0.04 * (1.0 - abs(norm_y))
            total_rear_dip = (rope_dip + center_cable_dip) * fx

            # Deep belly sag of the mesh interior under its own flexible weight
            belly_sag = 0.16 * math.sin(math.pi * fx) * (1.0 - 0.85 * (norm_y**2))

            # Forward pull in X due to gravity sagging downward
            dx_sag = -dir_x * 0.04 * math.sin(math.pi * fx)

            cur_x = gx + dir_x * (fx * d_top) + dx_sag
            cur_z = gh - (total_rear_dip + belly_sag)
            
            v = bm.verts.new((cur_x, cy, cur_z))
            row_verts.append(v)
        top_verts.append(row_verts)

    for ix in range(NX_top):
        for iy in range(NY):
            bm.faces.new((
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
            norm_y = cy / (gw / 2) # -1.0 to 1.0
            
            # Starting top coordinates for this column
            top_x = top_verts[NX_top][iy].co.x
            top_z = top_verts[NX_top][iy].co.z

            # Ground coordinates for this column
            base_x = gx + dir_x * d_bot
            base_z = 0.0

            # Nominal diagonal interpolation
            nom_x = top_x + (base_x - top_x) * fz
            nom_z = top_z * (1.0 - fz)

            # 1. Inward gravity catenary sag (the net hangs with a visible belly curve)
            # Nets hang inward toward the goal under gravity
            catenary_inward = -dir_x * 0.15 * math.sin(math.pi * (fz ** 0.85)) * (1.0 - 0.2 * norm_y**2)

            # 2. Vertical gravity sag (net stretches downward, accelerating drop in mid-section)
            vert_sag = -0.10 * math.sin(math.pi * fz) * (1.0 - 0.4 * fz)

            # 3. Organic drapery waves / pleats radiating down from tension cables
            wave_pleat = dir_x * 0.035 * math.sin(3.0 * math.pi * fz) * math.sin(2.0 * math.pi * norm_y) * math.sin(math.pi * fz)

            # 4. Ground apron / slack pooling onto the grass at the bottom (fz > 0.78)
            ground_slack_x = 0.0
            ground_cushion_z = 0.0
            if fz > 0.78:
                frac_ground = (fz - 0.78) / 0.22
                ground_slack_x = dir_x * 0.14 * (frac_ground ** 1.6)
                ground_cushion_z = 0.03 * (1.0 - frac_ground) * frac_ground

            cur_x = nom_x + catenary_inward + wave_pleat + ground_slack_x
            cur_z = max(0.012, nom_z + vert_sag + ground_cushion_z)

            v = bm.verts.new((cur_x, cy, cur_z))
            row_verts.append(v)
        back_verts.append(row_verts)

    for iz in range(NZ_back):
        for iy in range(NY):
            bm.faces.new((
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
        
        # Nominal height from post top (2.44) down to 0
        nom_z = gh * (1.0 - fz)
        
        for ix in range(NX_top + 1):
            fx = ix / NX_top
            
            # Diagonal back boundary at this height
            cur_depth = d_top + (d_bot - d_top) * fz
            nom_x = gx + dir_x * (fx * cur_depth)

            # Inward hourglass pinch (flexible net sucked inward toward center of goal)
            pinch_inward = 0.10 * math.sin(math.pi * fz) * math.sin(math.pi * fx)
            
            # Side downward sag
            side_sag_z = -0.06 * math.sin(math.pi * fz) * math.sin(math.pi * fx)

            cur_y = -gw/2 + pinch_inward
            cur_x = nom_x - dir_x * 0.06 * math.sin(math.pi * fz) * (fx ** 1.5)
            cur_z = max(0.012, nom_z + side_sag_z)

            # Anchor boundary vertices exactly to posts and top shelf
            if ix == 0:
                cur_x = gx
                cur_y = -gw/2
                cur_z = nom_z
            elif iz == 0:
                cur_x = top_verts[ix][0].co.x
                cur_y = top_verts[ix][0].co.y
                cur_z = top_verts[ix][0].co.z

            v = bm.verts.new((cur_x, cur_y, cur_z))
            row_v.append(v)
        side_l_verts.append(row_v)

    for iz in range(NZ_side):
        for ix in range(NX_top):
            bm.faces.new((
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

            # Anchor boundaries
            if ix == 0:
                cur_x = gx
                cur_y = gw/2
                cur_z = nom_z
            elif iz == 0:
                cur_x = top_verts[ix][NY].co.x
                cur_y = top_verts[ix][NY].co.y
                cur_z = top_verts[ix][NY].co.z

            v = bm.verts.new((cur_x, cur_y, cur_z))
            row_v.append(v)
        side_r_verts.append(row_v)

    for iz in range(NZ_side):
        for ix in range(NX_top):
            bm.faces.new((
                side_r_verts[iz][ix],
                side_r_verts[iz][ix+1],
                side_r_verts[iz+1][ix+1],
                side_r_verts[iz+1][ix]
            ))

    # Weld shared seam vertices seamlessly
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.02)

    # Seamless Box UV Mapping respecting Curvilinear Catenary Arc Length
    uv_layer = bm.loops.layers.uv.new("UVMap")
    for face in bm.faces:
        is_side = abs(face.normal.y) > 0.65
        for loop in face.loops:
            vx, vy, vz = loop.vert.co
            if is_side:
                # Project along side profile
                u = abs(vx - gx) * 0.55
                v = vz * 0.55
            else:
                # Top and back panels: U follows width (Y), V follows cumulative arc length
                u = (vy + gw/2) * 0.55
                # Surface arc length projection
                v = (abs(vx - gx) + (gh - vz) * 1.05) * 0.55
            loop[uv_layer].uv = (u, v)

    # Net connection points matching actual sagging top-rear vertices:
    top_rear_pts = [
        Vector((top_verts[NX_top][0].co.x,  -gw/2, top_verts[NX_top][0].co.z)),
        Vector((top_verts[NX_top][NY//2].co.x, 0.0, top_verts[NX_top][NY//2].co.z)),
        Vector((top_verts[NX_top][NY].co.x,  gw/2, top_verts[NX_top][NY].co.z))
    ]

    net_mesh = bpy.data.meshes.new(f"{name}_Hex_Net_Mesh")
    bm.to_mesh(net_mesh)
    bm.free()

    net_obj = bpy.data.objects.new(f"{name}_Hex_Net", net_mesh)
    net_obj.data.materials.append(mat_net)
    if col_pitch and net_obj.name not in col_pitch.objects:
        col_pitch.objects.link(net_obj)

    # 2. REBUILD REALISTIC TENSION CABLES WITH SUBTLE CATENARY DRAPE
    d_st = 2.4
    x_st = gx + dir_x * d_st
    h_st = 3.0

    for s_idx, (sy_st, p_net) in enumerate(zip(stanchion_ys, top_rear_pts)):
        p_st = Vector((x_st, sy_st, h_st - 0.08))
        v_cable = p_net - p_st
        
        # Cable cylinder
        bpy.ops.mesh.primitive_cylinder_add(radius=0.005, depth=v_cable.length, location=(p_st + p_net)/2, vertices=12)
        cable = bpy.context.object
        cable.name = f"{name}_Tension_Cable_{s_idx}"
        cable.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        cable.data.materials.append(mat_stanchion)
        if col_pitch and cable.name not in col_pitch.objects:
            col_pitch.objects.link(cable)

        # Turnbuckle tensioner
        bpy.ops.mesh.primitive_cylinder_add(radius=0.013, depth=0.18, location=p_st + v_cable * 0.28, vertices=12)
        tb = bpy.context.object
        tb.name = f"{name}_Turnbuckle_{s_idx}"
        tb.rotation_euler = v_cable.to_track_quat('Z', 'Y').to_euler()
        tb.data.materials.append(mat_stanchion)
        if col_pitch and tb.name not in col_pitch.objects:
            col_pitch.objects.link(tb)

    print(f"Successfully generated flexible gravity net for {name}!")

# Update both goals
build_gravity_flexible_net(-1, "Goal_Left_North")
build_gravity_flexible_net( 1, "Goal_Right_South")

# Render preview cameras to verify flexibility & gravity sag
cameras_to_render = [
    ("Cam_10_Front_Goal_Left", "preview_stadium_Cam_10_Front_Goal_Left.png"),
    ("Cam_9_Goal_Closeup", "preview_stadium_Cam_9_Goal_Closeup.png"),
    ("Cam_6_Goal_Left_Lake", "preview_stadium_Cam_6_Goal_Left_Lake.png"),
    ("Cam_5_Goal_Action", "preview_stadium_Cam_5_Goal_Action.png"),
    ("Cam_11_Front_Goal_Right", "preview_stadium_Cam_11_Front_Goal_Right.png"),
]

bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

for cname, img_name in cameras_to_render:
    cam = bpy.data.objects.get(cname)
    if cam:
        bpy.context.scene.camera = cam
        out_path = os.path.join(OUTPUT, img_name)
        bpy.context.scene.render.filepath = out_path
        print(f"Rendering {cname} -> {out_path}...")
        bpy.ops.render.render(write_still=True)

# Pack and save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved upgraded blend file with flexible gravity nets!")
