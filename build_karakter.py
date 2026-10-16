import bpy, bmesh, math, os, json
from mathutils import Vector, Quaternion
from math import sin, cos, pi, exp, sqrt, atan2

ROOT = r'c:/Users/Legion 3/Documents/PROJECT/animasi/karakter'
ASSETS = ROOT + '/Assets'
OUT = ROOT + '/Output'
os.makedirs(OUT, exist_ok=True)

scene = bpy.context.scene
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
for ob in list(scene.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
for ma in list(bpy.data.materials):
    bpy.data.materials.remove(ma)

parts = []
materials = {}

def mat(name, color, rough=.45, sss=0.0, metallic=0.0, weave=False, rib=False, dimple=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1.0)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
    if 'Subsurface Weight' in p.inputs:
        p.inputs['Subsurface Weight'].default_value = sss
    if 'Specular IOR Level' in p.inputs:
        p.inputs['Specular IOR Level'].default_value = 0.45
    if weave or rib or dimple:
        tex = nt.nodes.new('ShaderNodeTexNoise' if not dimple else 'ShaderNodeTexVoronoi')
        if dimple:
            tex.inputs['Scale'].default_value = 420.0
        else:
            tex.inputs['Scale'].default_value = 620.0 if weave else 280.0
            tex.inputs['Detail'].default_value = 3.0
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = 0.12 if weave else (0.22 if rib else 0.18)
        bump.inputs['Distance'].default_value = 0.0004
        out_sock = tex.outputs['Distance'] if dimple else tex.outputs['Fac']
        nt.links.new(out_sock, bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    materials[name] = m
    return m

# Vibrant Brazil kit colors matched to reference
mannequin_black = mat('Mannequin | obsidian satin', (0.012, 0.012, 0.014), rough=0.34, metallic=0.06)
jersey_yellow   = mat('Jersey | Brazil canary yellow', (0.96, 0.56, 0.008), rough=0.52, weave=True)
collar_green    = mat('Trim | Brazil emerald green', (0.005, 0.18, 0.035), rough=0.52, rib=True)
shorts_blue     = mat('Shorts | Brazil royal blue', (0.024, 0.048, 0.62), rough=0.56, weave=True)
sock_blue       = mat('Socks | royal blue knit', (0.020, 0.042, 0.58), rough=0.64, rib=True)
sock_green      = mat('Socks | green mid-calf band', (0.004, 0.15, 0.028), rough=0.64, rib=True)
sock_navy       = mat('Socks | dark navy border stripe', (0.003, 0.006, 0.030), rough=0.64, rib=True)
boot_white      = mat('Cleats | white textured upper', (0.80, 0.82, 0.85), rough=0.40, dimple=True)
boot_grey       = mat('Cleats | grey collar & heel', (0.14, 0.15, 0.17), rough=0.54, weave=True)
boot_dark       = mat('Cleats | charcoal outsole', (0.022, 0.023, 0.025), rough=0.35, metallic=0.15)
boot_orange     = mat('Cleats | orange soleplate accent', (0.95, 0.24, 0.005), rough=0.30)
tag_black       = mat('Jersey | woven authenticity tag', (0.015, 0.015, 0.018), rough=0.65)

# Add decal projection shader onto jersey_yellow for the CBF Chest Crest (zero boxy border!)
def add_decal_to_material(base_mat, base_rgb, img_path, x_min, x_max, z_min, z_max):
    nt = base_mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    im = bpy.data.images.load(img_path, check_existing=True)
    im.pack()

    tex_coord = nt.nodes.new('ShaderNodeTexCoord')
    sep_xyz = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tex_coord.outputs['Object'], sep_xyz.inputs['Vector'])

    # Map X -> U in [0, 1], Z -> V in [0, 1] (only when Y < 0 i.e. front side!)
    # U = (X - x_min) / (x_max - x_min)
    sub_x = nt.nodes.new('ShaderNodeMath'); sub_x.operation = 'SUBTRACT'; sub_x.inputs[1].default_value = x_min
    div_x = nt.nodes.new('ShaderNodeMath'); div_x.operation = 'DIVIDE'; div_x.inputs[1].default_value = (x_max - x_min)
    nt.links.new(sep_xyz.outputs['X'], sub_x.inputs[0])
    nt.links.new(sub_x.outputs['Value'], div_x.inputs[0])

    # V = (Z - z_min) / (z_max - z_min)
    sub_z = nt.nodes.new('ShaderNodeMath'); sub_z.operation = 'SUBTRACT'; sub_z.inputs[1].default_value = z_min
    div_z = nt.nodes.new('ShaderNodeMath'); div_z.operation = 'DIVIDE'; div_z.inputs[1].default_value = (z_max - z_min)
    nt.links.new(sep_xyz.outputs['Z'], sub_z.inputs[0])
    nt.links.new(sub_z.outputs['Value'], div_z.inputs[0])

    comb_uv = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(div_x.outputs['Value'], comb_uv.inputs['X'])
    nt.links.new(div_z.outputs['Value'], comb_uv.inputs['Y'])

    tex_im = nt.nodes.new('ShaderNodeTexImage')
    tex_im.image = im
    tex_im.extension = 'CLIP'
    nt.links.new(comb_uv.outputs['Vector'], tex_im.inputs['Vector'])

    # Front-only mask: Y < -0.02
    front_cmp = nt.nodes.new('ShaderNodeMath')
    front_cmp.operation = 'LESS_THAN'
    front_cmp.inputs[1].default_value = -0.02
    nt.links.new(sep_xyz.outputs['Y'], front_cmp.inputs[0])

    mask_mul = nt.nodes.new('ShaderNodeMath')
    mask_mul.operation = 'MULTIPLY'
    nt.links.new(tex_im.outputs['Alpha'], mask_mul.inputs[0])
    nt.links.new(front_cmp.outputs['Value'], mask_mul.inputs[1])

    mix_col = nt.nodes.new('ShaderNodeMix')
    mix_col.data_type = 'RGBA'
    mix_col.inputs['A'].default_value = (*base_rgb, 1.0)
    nt.links.new(mask_mul.outputs['Value'], mix_col.inputs['Factor'])
    nt.links.new(tex_im.outputs['Color'], mix_col.inputs['B'])
    nt.links.new(mix_col.outputs['Result'], bsdf.inputs['Base Color'])

add_decal_to_material(
    jersey_yellow, (0.96, 0.56, 0.008),
    ASSETS + '/chest-crest-alpha.png',
    0.065, 0.118, 1.318, 1.388
)
add_decal_to_material(
    shorts_blue, (0.024, 0.048, 0.62),
    ASSETS + '/shorts-crest-alpha.png',
    -0.148, -0.106, 0.665, 0.728
)

def mesh(name, vs, fs, material, track=True):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    if material:
        me.materials.append(material)
    for p in me.polygons:
        p.use_smooth = True
    if track:
        parts.append(ob)
    return ob

def loft_custom(name, rings_verts, material, ring_mats=None, cap_bottom=True, cap_top=True, track=True):
    n = len(rings_verts[0])
    vs = [v for ring in rings_verts for v in ring]
    fs = []
    f_mats = []
    for k in range(len(rings_verts) - 1):
        m_idx = ring_mats[k] if ring_mats else 0
        for j in range(n):
            fs.append((k*n + j, k*n + (j+1)%n, (k+1)*n + (j+1)%n, (k+1)*n + j))
            f_mats.append(m_idx)
    if cap_bottom:
        fs.append(tuple(reversed(range(n))))
        f_mats.append(ring_mats[0] if ring_mats else 0)
    if cap_top:
        top_start = (len(rings_verts) - 1) * n
        fs.append(tuple(top_start + j for j in range(n)))
        f_mats.append(ring_mats[-1] if ring_mats else 0)
    ob = mesh(name, vs, fs, None, track=track)
    if isinstance(material, list):
        for m in material:
            ob.data.materials.append(m)
        for p, midx in zip(ob.data.polygons, f_mats):
            p.material_index = midx
    elif material:
        ob.data.materials.append(material)
    return ob

def bezier(points, count=24):
    a, b, c, d = [Vector(v) for v in points]
    return [tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d) for t in [i/(count-1) for i in range(count)]]

def tube(name, points, radii, material, sides=24, flat=1.0, up_hint=Vector((0, -1, 0)), track=True):
    vs = []
    pts = [Vector(p) for p in points]
    for i, c in enumerate(pts):
        tangent = (pts[min(i+1, len(pts)-1)] - pts[max(0, i-1)]).normalized()
        normal = up_hint - tangent * up_hint.dot(tangent)
        if normal.length < 0.01:
            normal = Vector((1, 0, 0))
        else:
            normal.normalize()
        width = tangent.cross(normal).normalized()
        r = radii[i] if isinstance(radii, list) else radii
        if isinstance(r, (list, tuple)):
            rw, rd = r
        else:
            rw, rd = r, r * flat
        for j in range(sides):
            t = 2 * pi * j / sides
            vs.append(tuple(c + width * rw * cos(t) + normal * rd * sin(t)))
    fs = []
    for i in range(len(pts) - 1):
        for j in range(sides):
            fs.append((i*sides + j, i*sides + (j+1)%sides, (i+1)*sides + (j+1)%sides, (i+1)*sides + j))
    fs.append(tuple(reversed(range(sides))))
    fs.append(tuple((len(pts)-1)*sides + j for j in range(sides)))
    ob = mesh(name, vs, fs, None, track=track)
    if isinstance(material, list):
        for m in material:
            ob.data.materials.append(m)
    elif material:
        ob.data.materials.append(material)
    return ob

def join_and_voxel_remesh(name, objs, voxel_size, mat_to_assign, smooth_iters=4):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = name
    ob.data.name = name
    mod = ob.modifiers.new('VoxelMerge', 'REMESH')
    mod.mode = 'VOXEL'
    mod.voxel_size = voxel_size
    mod.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    if smooth_iters > 0:
        smod = ob.modifiers.new('SmoothSurface', 'SMOOTH')
        smod.factor = 0.45
        smod.iterations = smooth_iters
        bpy.ops.object.modifier_apply(modifier=smod.name)
    ob.data.materials.clear()
    ob.data.materials.append(mat_to_assign)
    for p in ob.data.polygons:
        p.use_smooth = True
    parts.append(ob)
    return ob

# ==============================================================================
# 1. SCULPTED BLACK MANNEQUIN (HEAD, NECK/STERNUM, ARMS, HANDS, KNEES)
# ==============================================================================
mannequin_raw = []
N_head = 64
head_profile = [
    # Sternum base recessed slightly in Y so the green V-collar & yellow jersey sit cleanly in front of it
    (1.400, 0.088, 0.056,  0.008, 0.0, 0.0, 0.0),
    (1.435, 0.072, 0.055,  0.006, 0.0, 0.0, 0.0),
    (1.468, 0.060, 0.054,  0.005, 0.0, 0.0, 0.0),
    (1.500, 0.055, 0.054,  0.004, 0.0, 0.0, 0.0),
    (1.535, 0.054, 0.054,  0.002, 0.0, 0.0, 0.0),
    (1.565, 0.055, 0.058, -0.002, 0.2, 0.0, 0.0),
    (1.585, 0.054, 0.072, -0.016, 0.9, 0.0, 0.0),
    (1.610, 0.062, 0.080, -0.018, 0.7, 0.1, 0.0),
    (1.640, 0.068, 0.084, -0.016, 0.4, 0.5, 0.0),
    (1.670, 0.072, 0.086, -0.014, 0.1, 0.8, 0.2),
    (1.700, 0.074, 0.088, -0.012, 0.0, 0.3, 0.9),
    (1.730, 0.073, 0.087, -0.010, 0.0, 0.0, 0.3),
    (1.758, 0.066, 0.080, -0.008, 0.0, 0.0, 0.0),
    (1.780, 0.050, 0.062, -0.005, 0.0, 0.0, 0.0),
    (1.795, 0.028, 0.034, -0.003, 0.0, 0.0, 0.0),
    (1.800, 0.008, 0.010, -0.002, 0.0, 0.0, 0.0),
]
head_rings = []
for z, rx, ry, cy, jaw_f, nose_f, brow_f in head_profile:
    ring = []
    for j in range(N_head):
        t = 2 * pi * j / N_head
        x = rx * cos(t)
        y = cy + ry * sin(t)
        if sin(t) < 0:
            front_w = (-sin(t))
            y -= jaw_f * 0.012 * exp(-(x / 0.028)**2) * (front_w**3)
            y -= nose_f * 0.010 * exp(-(x / 0.014)**2) * (front_w**4)
            y -= brow_f * 0.006 * exp(-(x / 0.048)**2) * (front_w**3)
            if nose_f > 0.3:
                y += 0.0045 * exp(-((abs(x) - 0.028) / 0.016)**2) * (front_w**2)
        ring.append((x, y, z))
    head_rings.append(ring)
mannequin_raw.append(loft_custom('HeadRaw', head_rings, mannequin_black, track=False))

for s, side in [(-1, 'R'), (1, 'L')]:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=14, location=(s * 0.072, -0.006, 1.665))
    ear = bpy.context.object
    ear.scale = (0.007, 0.014, 0.024)
    ear.rotation_euler = (math.radians(-8), s * math.radians(10), 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mannequin_raw.append(ear)

    arm_pts = bezier([
        (s * 0.232, -0.001, 1.300),
        (s * 0.282,  0.002, 1.190),
        (s * 0.332, -0.045, 1.095),
        (s * 0.382, -0.120, 0.990)
    ], count=30)
    arm_radii = []
    for i in range(30):
        u = i / 29.0
        swell = 0.008 * exp(-((u - 0.38) / 0.22)**2)
        r_base = 0.045 * (1 - u) + 0.027 * u + swell
        arm_radii.append((r_base, r_base * 0.88))
    mannequin_raw.append(tube(f'ArmRaw_{side}', arm_pts, arm_radii, mannequin_black, sides=32, track=False))

    wrist_pos = Vector((s * 0.376, -0.112, 1.002))
    knuckle_center = Vector((s * 0.408, -0.158, 0.935))
    palm_pts = bezier([
        tuple(wrist_pos - Vector((s * 0.008, -0.012, -0.015))),
        tuple(wrist_pos.lerp(knuckle_center, 0.35)),
        tuple(wrist_pos.lerp(knuckle_center, 0.72)),
        tuple(knuckle_center + Vector((s * 0.005, -0.006, -0.008)))
    ], count=14)
    palm_radii = [
        (0.027 + 0.011 * sin(pi * (i / 13.0)**0.85), 0.017 * (1 - 0.12 * (i / 13.0)))
        for i in range(14)
    ]
    mannequin_raw.append(tube(f'PalmRaw_{side}', palm_pts, palm_radii, mannequin_black, sides=24, up_hint=Vector((0, -0.7, -0.7)).normalized(), track=False))

    finger_specs = [
        ('Index',  -0.021, -0.004,  0.004, 0.080, 0.0086, -0.66, 0.36),
        ('Middle', -0.007,  0.002,  0.002, 0.088, 0.0090, -0.54, 0.44),
        ('Ring',    0.008,  0.007, -0.002, 0.082, 0.0084, -0.42, 0.48),
        ('Pinky',   0.021,  0.011, -0.006, 0.068, 0.0074, -0.28, 0.52),
    ]
    for fname, dy, dx, dz, flen, r0, py, yx in finger_specs:
        f_root = knuckle_center + Vector((s * (dx - 0.005), dy + 0.005, dz + 0.008))
        f_dir = Vector((s * yx, py, -0.78)).normalized()
        f_pts = []
        f_rad = []
        for j in range(14):
            u = j / 13.0
            curv = Vector((-s * 0.006 * u * u, -0.004 * u, -0.008 * u * u))
            f_pts.append(tuple(f_root + f_dir * (flen * u) + curv))
            f_rad.append(r0 * (1.0 - 0.28 * u))
        mannequin_raw.append(tube(f'FingerRaw_{fname}_{side}', f_pts, f_rad, mannequin_black, sides=16, track=False))

    # Opposing thumb angled slightly inward (-s) so its silhouette is distinct in Front & Back views
    thumb_root = wrist_pos + Vector((-s * 0.004, -0.016, -0.012))
    thumb_pts = bezier([
        tuple(thumb_root),
        tuple(thumb_root + Vector((-s * 0.006, -0.026, -0.022))),
        tuple(thumb_root + Vector((-s * 0.012, -0.048, -0.044))),
        tuple(thumb_root + Vector((-s * 0.015, -0.064, -0.062)))
    ], count=14)
    thumb_rad = [0.0110 * (1.0 - 0.28 * (i / 13.0)) for i in range(14)]
    mannequin_raw.append(tube(f'ThumbRaw_{side}', thumb_pts, thumb_rad, mannequin_black, sides=16, track=False))

    # Exposed Knee & Lower Thigh
    knee_spec = [
        (0.505, 0.051, 0.056, s * 0.128, -0.004),
        (0.540, 0.053, 0.059, s * 0.124, -0.006),
        (0.575, 0.056, 0.063, s * 0.119, -0.010),
        (0.610, 0.061, 0.067, s * 0.114, -0.011),
        (0.660, 0.067, 0.072, s * 0.109, -0.012),
    ]
    knee_rings = []
    for z, rx, ry, cx, cy in knee_spec:
        ring = []
        for j in range(40):
            t = 2 * pi * j / 40
            ct, st = cos(t), sin(t)
            patella = 0.006 * exp(-((z - 0.575) / 0.025)**2) * exp(-(ct / 0.45)**2) * max(0, -st)
            ring.append((cx + rx * ct, cy + ry * st - patella, z))
        knee_rings.append(ring)
    mannequin_raw.append(loft_custom(f'KneeRaw_{side}', knee_rings, mannequin_black, track=False))

join_and_voxel_remesh('Mannequin Body', mannequin_raw, voxel_size=0.0022, mat_to_assign=mannequin_black, smooth_iters=3)

# ==============================================================================
# 2. SEAMLESS BRAZIL YELLOW JERSEY (TORSO + SHORT SLEEVES + REAL GEOMETRIC V-NECK)
# ==============================================================================
jersey_raw = []
N_torso = 88
torso_spec = [
    (0.893, 0.174, 0.114, -0.018),
    (0.910, 0.171, 0.112, -0.018),
    (0.950, 0.165, 0.113, -0.019),
    (1.000, 0.160, 0.116, -0.020),
    (1.050, 0.155, 0.120, -0.021),
    (1.100, 0.152, 0.124, -0.022),
    (1.150, 0.151, 0.128, -0.022),
    (1.200, 0.153, 0.132, -0.021),
    (1.250, 0.159, 0.135, -0.018),
    (1.300, 0.172, 0.136, -0.015),
    (1.350, 0.192, 0.133, -0.012),
    (1.400, 0.206, 0.120, -0.008),
    (1.445, 0.188, 0.098, -0.003),
    (1.482, 0.135, 0.076,  0.002),
    (1.508, 0.078, 0.062,  0.005),
]

torso_rings = []
for idx_r, (z_base, rx, ry, cy) in enumerate(torso_spec):
    ring = []
    u_top = max(0.0, (z_base - 1.38) / (1.508 - 1.38))
    fold_env = sin(pi * max(0.0, min(1.0, (z_base - 0.893) / (1.42 - 0.893))))
    for j in range(N_torso):
        t = 2 * pi * j / N_torso
        ct, st = cos(t), sin(t)
        x = rx * ct
        y = cy + ry * st
        if st < 0 and 1.24 < z_base < 1.42:
            pec = 0.010 * sin(pi * (z_base - 1.24) / 0.18) * exp(-((abs(x) - 0.075) / 0.055)**2) * (-st)**2
            y -= pec
        z = z_base
        if st < 0 and u_top > 0:
            v_shape = max(0.0, 1.0 - abs(ct) / 0.68) * (-st)**1.2
            z -= 0.066 * (u_top**1.4) * v_shape
            y += 0.004 * (u_top**1.4) * v_shape
        wrinkle = (
            0.0042 * sin(6 * t + 0.5 * z_base * 7) +
            0.0030 * cos(10 * t - 0.7 * z_base * 9) +
            0.0020 * sin(15 * t + z_base * 12)
        ) * fold_env
        x += ct * wrinkle * 0.65
        y += st * wrinkle
        ring.append((x, y, z))
    torso_rings.append(ring)

jersey_raw.append(loft_custom('JerseyTorsoRaw', torso_rings, jersey_yellow, track=False))

for s, side in [(-1, 'R'), (1, 'L')]:
    slv_pts = bezier([
        (s * 0.135, -0.006, 1.395),
        (s * 0.185, -0.005, 1.395),
        (s * 0.225, -0.003, 1.335),
        (s * 0.252, -0.001, 1.264)
    ], count=24)
    slv_radii = []
    for i in range(24):
        u = i / 23.0
        rw = 0.056 * (1 - u) + 0.052 * u + 0.012 * sin(pi * u**0.7)
        rd = 0.062 * (1 - u) + 0.054 * u + 0.012 * sin(pi * u**0.7)
        slv_radii.append((rw, rd))
    jersey_raw.append(tube(f'SleeveRaw_{side}', slv_pts, slv_radii, jersey_yellow, sides=40, track=False))

    cuff_pts = bezier([
        (s * 0.246, -0.001, 1.276),
        (s * 0.249, -0.001, 1.270),
        (s * 0.252, -0.001, 1.263),
        (s * 0.255, -0.001, 1.256)
    ], count=8)
    tube(f'Sleeve Green Cuff {side}', cuff_pts, [(0.0535, 0.0555)] * 8, collar_green, sides=40)

jersey_unified = join_and_voxel_remesh('Brazil Jersey', jersey_raw, voxel_size=0.0028, mat_to_assign=jersey_yellow, smooth_iters=2)

# Sculpted 3D Ribbed Green V-Neck Collar Band sitting proudly on the V-neck rim
collar_pts = []
N_col = 72
for k in range(N_col):
    t = 2 * pi * k / N_col
    ct, st = cos(t), sin(t)
    x = 0.080 * ct
    y = 0.004 + 0.064 * st
    z = 1.509
    if st < 0:
        v_shape = max(0.0, 1.0 - abs(ct) / 0.72) * (-st)**1.15
        z -= 0.068 * v_shape
        # Project slightly forward at the front V tip so it overlaps the yellow jersey edge cleanly
        y -= 0.010 * v_shape
    collar_pts.append((x, y, z))
collar_pts.append(collar_pts[0])
tube('Jersey Green V-Collar', collar_pts, (0.0105, 0.0085), collar_green, sides=20)

hem_ring = torso_rings[0] + [torso_rings[0][0]]
tube('Jersey Bottom Hem', hem_ring, (0.004, 0.003), jersey_yellow, sides=12)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0.114, -0.097, 0.916))
tag = bpy.context.object
tag.name = 'Jersey Authenticity Tag'
tag.dimensions = (0.022, 0.006, 0.013)
tag.rotation_euler = (0, 0, math.radians(-28))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
tag.data.materials.append(tag_black)
parts.append(tag)

# ==============================================================================
# 3. SEAMLESS BRAZIL ROYAL BLUE SHORTS (BIFURCATED THIGH-TO-WAIST WITHOUT CROTCH STEP)
# ==============================================================================
shorts_raw = []
for s, side in [(-1, 'R'), (1, 'L')]:
    N_leg = 56
    # Each leg lofts continuously from mid-thigh (z=0.640) all the way to the waistband (z=0.908),
    # expanding inward above z=0.775 so Left and Right halves fuse across x=0 with a natural Y-crotch!
    sleg_spec = [
        # (z, rx_outer, rx_inner, ry, cx)
        (0.640, 0.082, 0.080, 0.084, s * 0.108),
        (0.675, 0.084, 0.082, 0.086, s * 0.105),
        (0.715, 0.086, 0.084, 0.089, s * 0.101),
        (0.755, 0.088, 0.088, 0.093, s * 0.096),
        (0.790, 0.090, 0.104, 0.098, s * 0.088), # Crotch saddle merge
        (0.825, 0.090, 0.110, 0.100, s * 0.082),
        (0.865, 0.082, 0.110, 0.096, s * 0.076),
        (0.905, 0.072, 0.105, 0.088, s * 0.070),
    ]
    sleg_rings = []
    for z, rx_out, rx_in, ry, cx in sleg_spec:
        ring = []
        for j in range(N_leg):
            t = 2 * pi * j / N_leg
            ct, st = cos(t), sin(t)
            # Determine whether ct points toward outer hip (same sign as s) or inner crotch (opposite sign of s)
            is_outer = (ct * s) >= 0
            rx = rx_out if is_outer else rx_in
            fold = 0.0022 * sin(5 * t + z * 16) + 0.0014 * cos(7 * t)
            x = cx + (rx + fold) * ct
            y = -0.014 + (ry + fold) * st
            ring.append((x, y, z))
        sleg_rings.append(ring)
    shorts_raw.append(loft_custom(f'ShortsLegRaw_{side}', sleg_rings, shorts_blue, track=False))

join_and_voxel_remesh('Brazil Shorts', shorts_raw, voxel_size=0.0026, mat_to_assign=shorts_blue, smooth_iters=4)

# ==============================================================================
# 4. BRAZIL FOOTBALL SOCKS & CLEATS (LEFT & RIGHT)
# ==============================================================================
for s, side in [(-1, 'R'), (1, 'L')]:
    sock_spec = [
        (0.125, 0.038, 0.046, s * 0.148,  0.006),
        (0.165, 0.039, 0.047, s * 0.147,  0.005),
        (0.200, 0.037, 0.045, s * 0.146,  0.005),
        (0.245, 0.041, 0.049, s * 0.144,  0.006),
        (0.285, 0.046, 0.055, s * 0.142,  0.007),
        (0.308, 0.049, 0.058, s * 0.141,  0.008),
        (0.314, 0.050, 0.059, s * 0.140,  0.008),
        (0.350, 0.054, 0.063, s * 0.138,  0.009),
        (0.380, 0.055, 0.064, s * 0.137,  0.008),
        (0.386, 0.055, 0.064, s * 0.136,  0.008),
        (0.425, 0.054, 0.062, s * 0.134,  0.005),
        (0.465, 0.053, 0.060, s * 0.132,  0.001),
        (0.490, 0.055, 0.061, s * 0.130, -0.002),
        (0.515, 0.056, 0.062, s * 0.129, -0.003),
        (0.528, 0.054, 0.060, s * 0.128, -0.004),
    ]
    sock_rings = []
    for z, rx, ry, cx, cy in sock_spec:
        ring = []
        for j in range(44):
            t = 2 * pi * j / 44
            rib_flute = 0.0006 * cos(22 * t)
            ring.append((cx + (rx + rib_flute) * cos(t), cy + (ry + rib_flute) * sin(t), z))
        sock_rings.append(ring)

    sock_ring_mats = []
    for k in range(len(sock_spec) - 1):
        zm = 0.5 * (sock_spec[k][0] + sock_spec[k+1][0])
        if 0.314 <= zm <= 0.380:
            sock_ring_mats.append(1)
        elif (0.306 <= zm < 0.314) or (0.380 < zm <= 0.388):
            sock_ring_mats.append(2)
        else:
            sock_ring_mats.append(0)
    loft_custom(f'Brazil Football Sock {side}', sock_rings, [sock_blue, sock_green, sock_navy], ring_mats=sock_ring_mats)

    # CLEATS with full heel enclosure (ry_back reaches +0.058m behind ankle center!)
    yaw = -s * math.radians(7.5)
    cos_y, sin_y = cos(yaw), sin(yaw)
    bx_0, by_0 = s * 0.148, 0.006

    def boot_transform(lx, ly, lz):
        rx = lx * cos_y - ly * sin_y
        ry = lx * sin_y + ly * cos_y
        return (bx_0 + rx, by_0 + ry, lz)

    # White Upper Boot (z = 0.024 .. 0.112)
    upper_rows = [
        # (z, rx, ry_front, ry_back, cy_local)
        (0.022, 0.049, 0.185, 0.062, -0.012),
        (0.034, 0.052, 0.192, 0.065, -0.012),
        (0.050, 0.051, 0.180, 0.064, -0.010),
        (0.068, 0.048, 0.150, 0.061, -0.006),
        (0.088, 0.044, 0.105, 0.057, -0.002),
        (0.106, 0.041, 0.068, 0.053,  0.000),
    ]
    upper_rings = []
    N_boot = 48
    for z, rx, ry_f, ry_b, cy_l in upper_rows:
        ring = []
        for j in range(N_boot):
            t = 2 * pi * j / N_boot
            ct, st = cos(t), sin(t)
            ry = ry_f if st < 0 else ry_b
            lx = rx * math.copysign(abs(ct)**0.82, ct)
            ly = cy_l + ry * st
            ring.append(boot_transform(lx, ly, z))
        upper_rings.append(ring)
    loft_custom(f'Cleat White Upper {side}', upper_rings, boot_white)

    # Smooth Grey Knit Ankle Collar, Tongue & Heel Counter Cup (z = 0.032 .. 0.140)
    collar_rows = [
        (0.034, 0.050, 0.045, 0.066,  0.000),
        (0.065, 0.047, 0.115, 0.063, -0.004),
        (0.095, 0.044, 0.088, 0.058, -0.002),
        (0.120, 0.042, 0.056, 0.053,  0.000),
        (0.138, 0.040, 0.048, 0.049,  0.000),
    ]
    col_rings = []
    for z, rx, ry_f, ry_b, cy_l in collar_rows:
        ring = []
        for j in range(N_boot):
            t = 2 * pi * j / N_boot
            ct, st = cos(t), sin(t)
            ry = ry_f if st < 0 else ry_b
            lx = rx * math.copysign(abs(ct)**0.82, ct)
            ly = cy_l + ry * st
            ring.append(boot_transform(lx, ly, z))
        col_rings.append(ring)
    loft_custom(f'Cleat Grey Collar {side}', col_rings, boot_grey)

    # Orange Soleplate Trim Rim (z = 0.017 .. 0.025)
    orange_rows = [
        (0.017, 0.048, 0.182, 0.061, -0.012),
        (0.021, 0.051, 0.189, 0.064, -0.012),
        (0.025, 0.050, 0.187, 0.063, -0.012),
    ]
    or_rings = []
    for z, rx, ry_f, ry_b, cy_l in orange_rows:
        ring = []
        for j in range(N_boot):
            t = 2 * pi * j / N_boot
            ct, st = cos(t), sin(t)
            ry = ry_f if st < 0 else ry_b
            lx = rx * math.copysign(abs(ct)**0.82, ct)
            ly = cy_l + ry * st
            ring.append(boot_transform(lx, ly, z))
        or_rings.append(ring)
    loft_custom(f'Cleat Orange Rim {side}', or_rings, boot_orange)

    # Dark Charcoal Outsole Plate (z = 0.011 .. 0.018)
    sole_rows = [
        (0.011, 0.045, 0.176, 0.058, -0.012),
        (0.015, 0.048, 0.182, 0.061, -0.012),
        (0.018, 0.048, 0.182, 0.061, -0.012),
    ]
    sole_rings = []
    for z, rx, ry_f, ry_b, cy_l in sole_rows:
        ring = []
        for j in range(N_boot):
            t = 2 * pi * j / N_boot
            ct, st = cos(t), sin(t)
            ry = ry_f if st < 0 else ry_b
            lx = rx * math.copysign(abs(ct)**0.82, ct)
            ly = cy_l + ry * st
            ring.append(boot_transform(lx, ly, z))
        sole_rings.append(ring)
    loft_custom(f'Cleat Outsole {side}', sole_rings, boot_dark)

    # Grey Cross-Laces across instep
    for k in range(5):
        ly = -0.102 + k * 0.016
        lz = 0.068 + k * 0.0105
        lace_pts = [
            boot_transform(-0.025, ly, lz - 0.002),
            boot_transform(-0.012, ly, lz + 0.004),
            boot_transform( 0.000, ly, lz + 0.006),
            boot_transform( 0.012, ly, lz + 0.004),
            boot_transform( 0.025, ly, lz - 0.002),
        ]
        tube(f'Cleat Lace {side}_{k}', lace_pts, (0.0024, 0.0015), boot_grey, sides=10)

    # Molded Cleat Studs underneath (touching ground z = 0.000)
    stud_coords = [
        (-0.025, -0.148), (0.025, -0.148),
        (-0.032, -0.108), (0.032, -0.108),
        (-0.028, -0.068), (0.028, -0.068),
        (-0.024,  0.015), (0.024,  0.015),
        (-0.022,  0.042), (0.022,  0.042),
    ]
    for idx_st, (sx, sy) in enumerate(stud_coords):
        spos_top = boot_transform(sx, sy, 0.014)
        spos_mid = boot_transform(sx, sy, 0.004)
        spos_bot = boot_transform(sx, sy, 0.000)
        stud_ob = tube(
            f'Cleat Stud {side}_{idx_st}',
            [spos_bot, spos_mid, spos_top],
            [(0.0038, 0.0038), (0.0045, 0.0045), (0.0060, 0.0060)],
            [boot_dark, boot_orange],
            sides=12
        )
        for p in stud_ob.data.polygons:
            p.material_index = 1 if p.center.z < 0.005 else 0

# ==============================================================================
# 5. ORTHOGRAPHIC REFERENCE GUIDES & STUDIO LIGHTING MATCHING REFERENCE
# ==============================================================================
refs = bpy.data.collections.new('REFERENCES | Front Y- Back Y+ Side X+')
scene.collection.children.link(refs)
ref_configs = [
    ('FRONT', ASSETS + '/reference-front.png', (pi/2, 0, 0),     (0,  0.45, 0.90)),
    ('BACK',  ASSETS + '/reference-back.png',  (pi/2, 0, pi),    (0, -0.45, 0.90)),
    ('SIDE',  ASSETS + '/reference-side.png',  (pi/2, 0, pi/2),  (-0.55, 0, 0.90)),
]
for label, rpath, rot, loc in ref_configs:
    if os.path.exists(rpath):
        im = bpy.data.images.load(rpath, check_existing=True)
        im.pack()
        em = bpy.data.objects.new('REF | ' + label, None)
        refs.objects.link(em)
        em.empty_display_type = 'IMAGE'
        em.data = im
        em.empty_display_size = 1.95
        em.rotation_euler = rot
        em.location = loc
        em.color[3] = 0.30
        em.hide_render = True

buildcol = bpy.data.collections.new('BUILD | reconstruction components')
scene.collection.children.link(buildcol)
for ob in parts:
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    buildcol.objects.link(ob)

bpy.ops.object.camera_add(location=(0.0, -4.8, 0.92))
cam = bpy.context.object
cam.name = 'Turnaround Camera'
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 2.02
cam.rotation_euler = (math.radians(90), 0, 0)
scene.camera = cam

# Key light on Front-Right (+X, -Y, +Z) so floor shadow casts toward Back-Left (-X, +Y) just like reference!
lights = [
    ('Key Sun',    ( 2.6, -2.2, 2.5), 360, 0.65, (1.0, 0.98, 0.95)),
    ('Fill Soft',  (-2.4, -2.8, 1.8), 140, 3.20, (0.92, 0.95, 1.0)),
    ('Rim Back',   (-0.6,  2.8, 2.6), 210, 2.40, (1.0, 0.97, 0.92)),
]
for lname, loc, power, sz, col in lights:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lt = bpy.context.object
    lt.name = lname
    lt.data.energy = power
    lt.data.shape = 'DISK'
    lt.data.size = sz
    lt.data.color = col
    lt.rotation_euler = (Vector((0, 0, 0.90)) - lt.location).to_track_quat('-Z', 'Y').to_euler()

scene.world.use_nodes = True
bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[0].default_value = (0.102, 0.102, 0.102, 1.0)
bg.inputs[1].default_value = 1.0

scene.render.film_transparent = False
scene.render.resolution_x = 563
scene.render.resolution_y = 757
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.view_settings.view_transform = 'AgX'

out_blend = OUT + '/Karakter_Brazil_working.blend'
bpy.ops.wm.save_as_mainfile(filepath=out_blend)
print(json.dumps({
    'stage': 'build_complete',
    'components': len(parts),
    'faces': sum(len(o.data.polygons) for o in parts),
    'saved': out_blend
}))
