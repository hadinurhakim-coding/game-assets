import bpy, bmesh, math, os, json
from mathutils import Vector, Quaternion, Euler, Matrix
from math import sin, cos, pi, exp, sqrt

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
for ar in list(bpy.data.armatures):
    bpy.data.armatures.remove(ar)
for ac in list(bpy.data.actions):
    bpy.data.actions.remove(ac)

parts = []
materials = {}

def mat(name, color, rough=.45, metallic=0.0, weave=False, rib=False, dimple=False):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    nt = m.node_tree
    p = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1.0)
    p.inputs['Roughness'].default_value = rough
    p.inputs['Metallic'].default_value = metallic
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

mannequin_black = mat('MI_Mannequin_Black', (0.012, 0.012, 0.014), rough=0.34, metallic=0.06)
jersey_yellow   = mat('MI_Jersey_Brazil_Yellow', (0.96, 0.56, 0.008), rough=0.52, weave=True)
collar_green    = mat('MI_Trim_Brazil_Green', (0.005, 0.18, 0.035), rough=0.52, rib=True)
shorts_blue     = mat('MI_Shorts_Brazil_Blue', (0.024, 0.048, 0.62), rough=0.56, weave=True)
sock_blue       = mat('MI_Socks_Brazil_Blue', (0.020, 0.042, 0.58), rough=0.64, rib=True)
sock_green      = mat('MI_Socks_Green_Band', (0.004, 0.15, 0.028), rough=0.64, rib=True)
sock_navy       = mat('MI_Socks_Navy_Stripe', (0.003, 0.006, 0.030), rough=0.64, rib=True)
boot_white      = mat('MI_Cleats_White_Upper', (0.80, 0.82, 0.85), rough=0.40, dimple=True)
boot_grey       = mat('MI_Cleats_Grey_Collar', (0.14, 0.15, 0.17), rough=0.54, weave=True)
boot_dark       = mat('MI_Cleats_Dark_Outsole', (0.022, 0.023, 0.025), rough=0.35, metallic=0.15)
boot_orange     = mat('MI_Cleats_Orange_Accent', (0.95, 0.24, 0.005), rough=0.30)
tag_black       = mat('MI_Jersey_Tag_Black', (0.015, 0.015, 0.018), rough=0.65)

def add_decal_to_material(base_mat, base_rgb, img_path, uv_layer_name):
    nt = base_mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    im = bpy.data.images.load(img_path, check_existing=True)
    im.pack()

    uv_node = nt.nodes.new('ShaderNodeUVMap')
    uv_node.uv_map = uv_layer_name

    tex_im = nt.nodes.new('ShaderNodeTexImage')
    tex_im.image = im
    tex_im.extension = 'CLIP'
    nt.links.new(uv_node.outputs['UV'], tex_im.inputs['Vector'])

    mix_col = nt.nodes.new('ShaderNodeMix')
    mix_col.data_type = 'RGBA'
    mix_col.inputs['A'].default_value = (*base_rgb, 1.0)
    nt.links.new(tex_im.outputs['Alpha'], mix_col.inputs['Factor'])
    nt.links.new(tex_im.outputs['Color'], mix_col.inputs['B'])
    nt.links.new(mix_col.outputs['Result'], bsdf.inputs['Base Color'])

add_decal_to_material(jersey_yellow, (0.96, 0.56, 0.008), ASSETS + '/chest-crest-alpha.png', 'UV_Chest_Crest')
add_decal_to_material(shorts_blue, (0.024, 0.048, 0.62), ASSETS + '/shorts-crest-alpha.png', 'UV_Shorts_Crest')

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

def bezier(points, count=20):
    a, b, c, d = [Vector(v) for v in points]
    return [tuple((1-t)**3*a + 3*(1-t)**2*t*b + 3*(1-t)*t*t*c + t**3*d) for t in [i/(count-1) for i in range(count)]]

def tube(name, points, radii, material, sides=20, flat=1.0, up_hint=Vector((0, -1, 0)), track=True):
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

def join_and_voxel_remesh(name, objs, voxel_size, mat_to_assign, smooth_iters=3, decimate_ratio=None):
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
    if decimate_ratio:
        dmod = ob.modifiers.new('GameOptimize', 'DECIMATE')
        dmod.ratio = decimate_ratio
        bpy.ops.object.modifier_apply(modifier=dmod.name)
    ob.data.materials.clear()
    ob.data.materials.append(mat_to_assign)
    for p in ob.data.polygons:
        p.use_smooth = True
    parts.append(ob)
    return ob

# ==============================================================================
# 1. BUILD GAME-OPTIMIZED CHARACTER GEOMETRY (~24,000 TRIS FOR UE5 22-PLAYER MATCH ENGINE)
# ==============================================================================
mannequin_raw = []
N_head = 48
head_profile = [
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
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=12, location=(s * 0.072, -0.006, 1.665))
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
    ], count=24)
    arm_radii = []
    for i in range(24):
        u = i / 23.0
        swell = 0.008 * exp(-((u - 0.38) / 0.22)**2)
        r_base = 0.045 * (1 - u) + 0.027 * u + swell
        arm_radii.append((r_base, r_base * 0.88))
    mannequin_raw.append(tube(f'ArmRaw_{side}', arm_pts, arm_radii, mannequin_black, sides=24, track=False))

    wrist_pos = Vector((s * 0.376, -0.112, 1.002))
    knuckle_center = Vector((s * 0.408, -0.158, 0.935))
    palm_pts = bezier([
        tuple(wrist_pos - Vector((s * 0.008, -0.012, -0.015))),
        tuple(wrist_pos.lerp(knuckle_center, 0.35)),
        tuple(wrist_pos.lerp(knuckle_center, 0.72)),
        tuple(knuckle_center + Vector((s * 0.005, -0.006, -0.008)))
    ], count=10)
    palm_radii = [
        (0.027 + 0.011 * sin(pi * (i / 9.0)**0.85), 0.017 * (1 - 0.12 * (i / 9.0)))
        for i in range(10)
    ]
    mannequin_raw.append(tube(f'PalmRaw_{side}', palm_pts, palm_radii, mannequin_black, sides=18, up_hint=Vector((0, -0.7, -0.7)).normalized(), track=False))

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
        for j in range(10):
            u = j / 9.0
            curv = Vector((-s * 0.006 * u * u, -0.004 * u, -0.008 * u * u))
            f_pts.append(tuple(f_root + f_dir * (flen * u) + curv))
            f_rad.append(r0 * (1.0 - 0.28 * u))
        mannequin_raw.append(tube(f'FingerRaw_{fname}_{side}', f_pts, f_rad, mannequin_black, sides=12, track=False))

    thumb_root = wrist_pos + Vector((-s * 0.004, -0.016, -0.012))
    thumb_pts = bezier([
        tuple(thumb_root),
        tuple(thumb_root + Vector((-s * 0.006, -0.026, -0.022))),
        tuple(thumb_root + Vector((-s * 0.012, -0.048, -0.044))),
        tuple(thumb_root + Vector((-s * 0.015, -0.064, -0.062)))
    ], count=10)
    thumb_rad = [0.0110 * (1.0 - 0.28 * (i / 9.0)) for i in range(10)]
    mannequin_raw.append(tube(f'ThumbRaw_{side}', thumb_pts, thumb_rad, mannequin_black, sides=12, track=False))

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
        for j in range(28):
            t = 2 * pi * j / 28
            ct, st = cos(t), sin(t)
            patella = 0.006 * exp(-((z - 0.575) / 0.025)**2) * exp(-(ct / 0.45)**2) * max(0, -st)
            ring.append((cx + rx * ct, cy + ry * st - patella, z))
        knee_rings.append(ring)
    mannequin_raw.append(loft_custom(f'KneeRaw_{side}', knee_rings, mannequin_black, track=False))

join_and_voxel_remesh('Mannequin Body', mannequin_raw, voxel_size=0.0032, mat_to_assign=mannequin_black, smooth_iters=3, decimate_ratio=0.14)

jersey_raw = []
N_torso = 64
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
    ], count=18)
    slv_radii = []
    for i in range(18):
        u = i / 17.0
        rw = 0.056 * (1 - u) + 0.052 * u + 0.012 * sin(pi * u**0.7)
        rd = 0.062 * (1 - u) + 0.054 * u + 0.012 * sin(pi * u**0.7)
        slv_radii.append((rw, rd))
    jersey_raw.append(tube(f'SleeveRaw_{side}', slv_pts, slv_radii, jersey_yellow, sides=28, track=False))

    cuff_pts = bezier([
        (s * 0.246, -0.001, 1.276),
        (s * 0.249, -0.001, 1.270),
        (s * 0.252, -0.001, 1.263),
        (s * 0.255, -0.001, 1.256)
    ], count=5)
    tube(f'Sleeve Green Cuff {side}', cuff_pts, [(0.0535, 0.0555)] * 5, collar_green, sides=28)

join_and_voxel_remesh('Brazil Jersey', jersey_raw, voxel_size=0.0038, mat_to_assign=jersey_yellow, smooth_iters=2, decimate_ratio=0.16)

collar_pts = []
N_col = 48
for k in range(N_col):
    t = 2 * pi * k / N_col
    ct, st = cos(t), sin(t)
    x = 0.080 * ct
    y = 0.004 + 0.064 * st
    z = 1.509
    if st < 0:
        v_shape = max(0.0, 1.0 - abs(ct) / 0.72) * (-st)**1.15
        z -= 0.068 * v_shape
        y -= 0.010 * v_shape
    collar_pts.append((x, y, z))
collar_pts.append(collar_pts[0])
tube('Jersey Green V-Collar', collar_pts, (0.0105, 0.0085), collar_green, sides=14)

hem_ring = torso_rings[0] + [torso_rings[0][0]]
tube('Jersey Bottom Hem', hem_ring, (0.004, 0.003), jersey_yellow, sides=10)

bpy.ops.mesh.primitive_cube_add(size=1, location=(0.114, -0.097, 0.916))
tag = bpy.context.object
tag.name = 'Jersey Authenticity Tag'
tag.dimensions = (0.022, 0.006, 0.013)
tag.rotation_euler = (0, 0, math.radians(-28))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
tag.data.materials.append(tag_black)
parts.append(tag)

shorts_raw = []
for s, side in [(-1, 'R'), (1, 'L')]:
    N_leg = 40
    sleg_spec = [
        (0.640, 0.082, 0.080, 0.084, s * 0.108),
        (0.675, 0.084, 0.082, 0.086, s * 0.105),
        (0.715, 0.086, 0.084, 0.089, s * 0.101),
        (0.755, 0.088, 0.088, 0.093, s * 0.096),
        (0.790, 0.090, 0.104, 0.098, s * 0.088),
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
            is_outer = (ct * s) >= 0
            rx = rx_out if is_outer else rx_in
            fold = 0.0022 * sin(5 * t + z * 16) + 0.0014 * cos(7 * t)
            x = cx + (rx + fold) * ct
            y = -0.014 + (ry + fold) * st
            ring.append((x, y, z))
        sleg_rings.append(ring)
    shorts_raw.append(loft_custom(f'ShortsLegRaw_{side}', sleg_rings, shorts_blue, track=False))

join_and_voxel_remesh('Brazil Shorts', shorts_raw, voxel_size=0.0038, mat_to_assign=shorts_blue, smooth_iters=3, decimate_ratio=0.16)

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
        for j in range(28):
            t = 2 * pi * j / 28
            rib_flute = 0.0006 * cos(14 * t)
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

    yaw = -s * math.radians(7.5)
    cos_y, sin_y = cos(yaw), sin(yaw)
    bx_0, by_0 = s * 0.148, 0.006

    def boot_transform(lx, ly, lz):
        rx = lx * cos_y - ly * sin_y
        ry = lx * sin_y + ly * cos_y
        return (bx_0 + rx, by_0 + ry, lz)

    N_boot = 28
    upper_rows = [
        (0.022, 0.049, 0.185, 0.062, -0.012),
        (0.034, 0.052, 0.192, 0.065, -0.012),
        (0.050, 0.051, 0.180, 0.064, -0.010),
        (0.068, 0.048, 0.150, 0.061, -0.006),
        (0.088, 0.044, 0.105, 0.057, -0.002),
        (0.106, 0.041, 0.068, 0.053,  0.000),
    ]
    upper_rings = []
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
        tube(f'Cleat Lace {side}_{k}', lace_pts, (0.0024, 0.0015), boot_grey, sides=8)

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
            sides=8
        )
        for p in stud_ob.data.polygons:
            p.material_index = 1 if p.center.z < 0.005 else 0

# Join all character parts into one UE5 Skeletal Mesh 'SK_Brazil_Player'
bpy.ops.object.select_all(action='DESELECT')
for o in parts:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.join()
ob = bpy.context.object
ob.name = 'SK_Brazil_Player'
ob.data.name = 'SK_Brazil_Player_Mesh'
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# Create skin-locked UV maps for Chest Crest and Shorts Crest so decals deform with the mesh!
uv_chest = ob.data.uv_layers.new(name='UV_Chest_Crest')
uv_shorts = ob.data.uv_layers.new(name='UV_Shorts_Crest')
verts = ob.data.vertices
for poly in ob.data.polygons:
    for li in poly.loop_indices:
        vi = ob.data.loops[li].vertex_index
        co = verts[vi].co
        if co.y < -0.02:
            uv_chest.data[li].uv = ((co.x - 0.065) / (0.118 - 0.065), (co.z - 1.318) / (1.388 - 1.318))
            uv_shorts.data[li].uv = ((co.x - (-0.148)) / (-0.106 - (-0.148)), (co.z - 0.665) / (0.728 - 0.665))
        else:
            uv_chest.data[li].uv = (-1.0, -1.0)
            uv_shorts.data[li].uv = (-1.0, -1.0)

# ==============================================================================
# 2. BUILD UNREAL ENGINE 5 (MANNY/QUINN) + FIFA/FOOTBALL MANAGER PITCH RIG
# ==============================================================================
arm = bpy.data.armatures.new('UE5_Football_Skeleton')
rig = bpy.data.objects.new('root', arm)
scene.collection.objects.link(rig)
rig.show_in_front = True

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')

deform_spec = {}
def add_bone(name, head, tail, parent=None, connected=False, deform=True, roll=0.0):
    b = arm.edit_bones.new(name)
    b.head = head
    b.tail = tail
    b.roll = roll
    if parent and parent in arm.edit_bones:
        b.parent = arm.edit_bones[parent]
        b.use_connect = connected
    b.use_deform = deform
    if deform:
        deform_spec[name] = (Vector(head), Vector(tail))
    return b

add_bone('root',     (0,  0.000, 0.000), (0,  0.000, 0.120), parent=None, deform=False)
add_bone('pelvis',   (0, -0.012, 0.785), (0, -0.015, 0.895), 'root',      connected=False, deform=True)
add_bone('spine_01', (0, -0.015, 0.895), (0, -0.018, 1.005), 'pelvis',    connected=True,  deform=True)
add_bone('spine_02', (0, -0.018, 1.005), (0, -0.020, 1.115), 'spine_01',  connected=True,  deform=True)
add_bone('spine_03', (0, -0.020, 1.115), (0, -0.018, 1.225), 'spine_02',  connected=True,  deform=True)
add_bone('spine_04', (0, -0.018, 1.225), (0, -0.012, 1.335), 'spine_03',  connected=True,  deform=True)
add_bone('spine_05', (0, -0.012, 1.335), (0, -0.006, 1.445), 'spine_04',  connected=True,  deform=True)
add_bone('neck_01',  (0, -0.006, 1.445), (0, -0.002, 1.510), 'spine_05',  connected=True,  deform=True)
add_bone('neck_02',  (0, -0.002, 1.510), (0,  0.002, 1.575), 'neck_01',   connected=True,  deform=True)
add_bone('head',     (0,  0.002, 1.575), (0, -0.004, 1.800), 'neck_02',   connected=True,  deform=True)

for s, suf in [(1, 'l'), (-1, 'r')]:
    # Arm joints: Shoulder (-Y front) -> Elbow (+Y back, olecranon) -> Wrist (-Y front, relaxed A-pose)
    shoulder = Vector((s * 0.175, -0.005, 1.425))
    elbow    = Vector((s * 0.285,  0.012, 1.190))  # Natural backward (+Y) pre-bend matching olecranon
    wrist    = Vector((s * 0.376, -0.112, 1.002))  # Forward (-Y) in relaxed A-pose
    knuckle  = Vector((s * 0.408, -0.158, 0.935))
    mid_fore = elbow.lerp(wrist, 0.52)

    add_bone(f'clavicle_{suf}',          (s * 0.022, -0.008, 1.425), tuple(shoulder), 'spine_05', False, True)
    add_bone(f'upperarm_{suf}',          tuple(shoulder), tuple(elbow), f'clavicle_{suf}', True, True)
    add_bone(f'lowerarm_{suf}',          tuple(elbow), tuple(wrist), f'upperarm_{suf}', True, True)
    add_bone(f'lowerarm_twist_01_{suf}', tuple(mid_fore), tuple(wrist), f'lowerarm_{suf}', False, True)
    add_bone(f'hand_{suf}',              tuple(wrist), tuple(knuckle), f'lowerarm_{suf}', True, True)

    finger_specs = [
        ('index',  -0.021, -0.004,  0.004, 0.080, -0.66, 0.36),
        ('middle', -0.007,  0.002,  0.002, 0.088, -0.54, 0.44),
        ('ring',    0.008,  0.007, -0.002, 0.082, -0.42, 0.48),
        ('pinky',   0.021,  0.011, -0.006, 0.068, -0.28, 0.52),
    ]
    for fn, dy, dx, dz, flen, py, yx in finger_specs:
        f_root = knuckle + Vector((s * (dx - 0.005), dy + 0.005, dz + 0.008))
        f_dir = Vector((s * yx, py, -0.78)).normalized()
        prev = f'hand_{suf}'
        for j in range(3):
            u0, u1 = j / 3.0, (j + 1) / 3.0
            p0 = f_root + f_dir * (flen * u0) + Vector((-s * 0.006 * u0 * u0, -0.004 * u0, -0.008 * u0 * u0))
            p1 = f_root + f_dir * (flen * u1) + Vector((-s * 0.006 * u1 * u1, -0.004 * u1, -0.008 * u1 * u1))
            bname = f'{fn}_0{j+1}_{suf}'
            add_bone(bname, tuple(p0), tuple(p1), prev, j > 0, True)
            prev = bname

    t_root = wrist + Vector((-s * 0.004, -0.016, -0.012))
    t_pts = [
        tuple(t_root),
        tuple(t_root + Vector((-s * 0.006, -0.026, -0.022))),
        tuple(t_root + Vector((-s * 0.012, -0.048, -0.044))),
        tuple(t_root + Vector((-s * 0.015, -0.064, -0.062))),
    ]
    prev = f'hand_{suf}'
    for j in range(3):
        bname = f'thumb_0{j+1}_{suf}'
        add_bone(bname, t_pts[j], t_pts[j+1], prev, j > 0, True)
        prev = bname

    # Leg joints: Hip (+Y back in acetabulum) -> Knee (-Y front, patella) -> Ankle (-Y front)
    hip   = Vector((s * 0.095,  0.006, 0.785))  # Centered in pelvic socket
    knee  = Vector((s * 0.119, -0.024, 0.555))  # Natural forward (-Y) pre-bend matching patella
    ankle = Vector((s * 0.145, -0.010, 0.115))  # Biomechanical ankle hinge
    ball  = Vector((s * 0.158, -0.098, 0.026))
    toe   = Vector((s * 0.165, -0.185, 0.018))
    heel  = Vector((s * 0.145,  0.058, 0.000))

    mid_thigh = hip.lerp(knee, 0.50)
    mid_calf  = knee.lerp(ankle, 0.50)

    add_bone(f'thigh_{suf}',          tuple(hip),       tuple(knee),  'pelvis',      False, True)
    add_bone(f'thigh_twist_01_{suf}', tuple(mid_thigh), tuple(knee),  f'thigh_{suf}', False, True)
    add_bone(f'calf_{suf}',           tuple(knee),      tuple(ankle), f'thigh_{suf}', True,  True)
    add_bone(f'calf_twist_01_{suf}',  tuple(mid_calf),  tuple(ankle), f'calf_{suf}',  False, True)
    add_bone(f'foot_{suf}',           tuple(ankle),     tuple(ball),  f'calf_{suf}',  True,  True)
    add_bone(f'ball_{suf}',           tuple(ball),      tuple(toe),   f'foot_{suf}',  True,  True)

    add_bone(f'CTRL_Foot_IK_{suf}',    tuple(ankle), tuple(ankle + Vector((0, -0.10, 0))), 'root', False, False)
    add_bone(f'MCH_Heel_Pivot_{suf}',  tuple(heel),  tuple(toe),   f'CTRL_Foot_IK_{suf}',   False, False)
    add_bone(f'MCH_Toe_Pivot_{suf}',   tuple(toe),   tuple(ball),  f'MCH_Heel_Pivot_{suf}', False, False)
    add_bone(f'MCH_Ball_Roll_{suf}',   tuple(ball),  tuple(ankle), f'MCH_Toe_Pivot_{suf}',  False, False)
    add_bone(f'CTRL_Knee_Pole_{suf}',  tuple(knee + Vector((0, -0.42, 0))), tuple(knee + Vector((0, -0.50, 0))), 'root', False, False)
    add_bone(f'CTRL_Hand_IK_{suf}',    tuple(wrist), tuple(wrist + Vector((0, -0.08, 0))), 'root', False, False)
    add_bone(f'CTRL_Elbow_Pole_{suf}', tuple(elbow + Vector((0,  0.38, 0))), tuple(elbow + Vector((0,  0.46, 0))), 'root', False, False)
    add_bone(f'socket_ball_{suf}',     tuple(ball + Vector((0, -0.12, 0.09))), tuple(ball + Vector((0, -0.20, 0.09))), f'ball_{suf}', False, False)

add_bone('ik_foot_root', (0, 0, 0), (0, -0.12, 0), 'root', False, True)
add_bone('ik_foot_l',    ( 0.145, -0.010, 0.115), ( 0.158, -0.098, 0.026), 'ik_foot_root', False, True)
add_bone('ik_foot_r',    (-0.145, -0.010, 0.115), (-0.158, -0.098, 0.026), 'ik_foot_root', False, True)

add_bone('ik_hand_root', (0, 0, 0), (0, 0, 0.12), 'root', False, True)
add_bone('ik_hand_gun',  ( 0.376, -0.112, 1.002), ( 0.408, -0.158, 0.935), 'ik_hand_root', False, True)
add_bone('ik_hand_l',    ( 0.376, -0.112, 1.002), ( 0.408, -0.158, 0.935), 'ik_hand_gun',  False, True)
add_bone('ik_hand_r',    (-0.376, -0.112, 1.002), (-0.408, -0.158, 0.935), 'ik_hand_gun',  False, True)

add_bone('CTRL_Ball_Target',   (0.0, -0.32, 0.11), (0.0, -0.32, 0.25), 'root', False, False)
add_bone('CTRL_LookAt_Target', (0.0, -1.20, 1.65), (0.0, -1.35, 1.65), 'root', False, False)

bpy.ops.object.mode_set(mode='OBJECT')

# ==============================================================================
# 3. ASSIGN NORMALIZED UE5 VERTEX WEIGHTS TO SK_Brazil_Player
# ==============================================================================
weighted_bones = [n for n in deform_spec if not n.startswith('ik_')]
groups = {name: ob.vertex_groups.new(name=name) for name in weighted_bones}
for ik_name in ['ik_foot_root', 'ik_foot_l', 'ik_foot_r', 'ik_hand_root', 'ik_hand_gun', 'ik_hand_l', 'ik_hand_r']:
    ob.vertex_groups.new(name=ik_name)

def segment_distance(p, name):
    a, b = deform_spec[name]
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(1e-8, ab.length_squared)))
    return (p - a - ab * t).length

def blend_chain(p, names, power=4.5):
    dd = sorted([(segment_distance(p, n), n) for n in names])[:3]
    raw = {n: 1.0 / max(0.003, d)**power for d, n in dd}
    total = sum(raw.values())
    return {n: w / total for n, w in raw.items() if w / total > 0.001}

def smoothstep(a, b, v):
    t = max(0.0, min(1.0, (v - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)

for v in ob.data.vertices:
    p = v.co
    x, y, z = p
    suf = 'l' if x >= 0 else 'r'

    if z > 1.575:
        weights = {'head': 1.0}
    elif z > 1.445 and abs(x) < 0.125:
        if z > 1.510:
            w = smoothstep(1.510, 1.575, z)
            weights = {'head': w, 'neck_02': 1.0 - w}
        else:
            w = smoothstep(1.445, 1.510, z)
            weights = {'neck_02': w, 'neck_01': 1.0 - w}
    elif abs(x) > 0.195 and 0.80 < z < 1.445:
        finger_names = [n for n in weighted_bones if n.endswith('_' + suf) and any(n.startswith(f) for f in ['index', 'middle', 'ring', 'pinky', 'thumb'])]
        arm_names = [f'clavicle_{suf}', f'upperarm_{suf}', f'lowerarm_{suf}', f'lowerarm_twist_01_{suf}', f'hand_{suf}']
        if abs(x) > 0.385 and z < 0.965:
            closest = min(finger_names, key=lambda n: segment_distance(p, n))
            family = closest.split('_')[0]
            names = [n for n in finger_names if n.startswith(family + '_')] + [f'hand_{suf}']
            weights = blend_chain(p, names)
        else:
            weights = blend_chain(p, arm_names)
    elif z < 0.810:
        if z < 0.145:
            weights = blend_chain(p, [f'calf_{suf}', f'foot_{suf}', f'ball_{suf}'], 5.0)
        else:
            weights = blend_chain(p, [f'thigh_{suf}', f'thigh_twist_01_{suf}', f'calf_{suf}', f'calf_twist_01_{suf}', 'pelvis'], 5.0)
            if z > 0.740:
                w = smoothstep(0.740, 0.810, z)
                weights = {n: q * (1.0 - w) for n, q in weights.items()}
                weights['pelvis'] = weights.get('pelvis', 0.0) + w
    else:
        spine_chain = ['pelvis', 'spine_01', 'spine_02', 'spine_03', 'spine_04', 'spine_05']
        weights = blend_chain(p, spine_chain, 4.0)
        if abs(x) > 0.125 and z > 1.320:
            w = 0.55 * smoothstep(0.125, 0.195, abs(x))
            weights = {n: q * (1.0 - w) for n, q in weights.items()}
            weights[f'clavicle_{suf}'] = weights.get(f'clavicle_{suf}', 0.0) + w

    total = sum(q for q in weights.values() if q > 0)
    for n, q in weights.items():
        if q > 0:
            groups[n].add([v.index], q / total, 'REPLACE')

mod = ob.modifiers.new('UE5_Armature', 'ARMATURE')
mod.object = rig
mod.use_deform_preserve_volume = True
ob.parent = rig
ob.matrix_parent_inverse = rig.matrix_world.inverted()

# ==============================================================================
# 4. CONFIGURE LIVE FOOT/HAND IK + REVERSE FOOT + BALL TARGET CONSTRAINTS
# ==============================================================================
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='POSE')

for pb in rig.pose.bones:
    pb.rotation_mode = 'XYZ'

for suf in ['l', 'r']:
    c_ik = rig.pose.bones[f'calf_{suf}'].constraints.new('IK')
    c_ik.name = f'Football_Leg_IK_{suf}'
    c_ik.target = rig
    c_ik.subtarget = f'MCH_Ball_Roll_{suf}'
    c_ik.pole_target = rig
    c_ik.pole_subtarget = f'CTRL_Knee_Pole_{suf}'
    c_ik.pole_angle = math.radians(-90)
    c_ik.chain_count = 2
    c_ik.influence = 0.0

    c_uf = rig.pose.bones[f'ik_foot_{suf}'].constraints.new('COPY_TRANSFORMS')
    c_uf.target = rig
    c_uf.subtarget = f'foot_{suf}'

    c_uh = rig.pose.bones[f'ik_hand_{suf}'].constraints.new('COPY_TRANSFORMS')
    c_uh.target = rig
    c_uh.subtarget = f'hand_{suf}'

# ==============================================================================
# 5. CREATE 4 BAKED FOOTBALL MATCH ENGINE ANIMATION ACTIONS FOR UNREAL ENGINE 5
#    Using exact World-Space Delta Rotation -> Bone Local Matrix conversion!
#    World Axes:
#      +X (Left):
#        - For downward limbs (thigh, calf, arm): +wx swings FORWARD (-Y), -wx swings/bends BACKWARD (+Y)
#        - For upward torso (pelvis, spine, neck): -wx leans FORWARD (-Y), +wx leans BACKWARD (+Y)
#      +Y (Back): roll / abduction
#      +Z (Up):   horizontal twist / yaw
# ==============================================================================
deform_pose_bones = [pb for pb in rig.pose.bones if pb.bone.use_deform]

def reset_pose():
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
        pb.scale = (1, 1, 1)

def key_all_deform(frame):
    for pb in deform_pose_bones:
        pb.keyframe_insert(data_path='location', frame=frame)
        pb.keyframe_insert(data_path='rotation_euler', frame=frame)

def set_world_rot(bname, wx=0.0, wy=0.0, wz=0.0):
    if bname not in rig.pose.bones:
        return
    pb = rig.pose.bones[bname]
    b_rest = pb.bone.matrix_local.to_3x3()
    m_world = Euler((math.radians(wx), math.radians(wy), math.radians(wz)), 'XYZ').to_matrix()
    m_local = b_rest.inverted() @ m_world @ b_rest
    pb.rotation_euler = m_local.to_euler('XYZ')

# --- Action 1: A_FM_Rest_APose ---
act_rest = bpy.data.actions.new('A_FM_Rest_APose')
act_rest.use_fake_user = True
rig.animation_data_create()
rig.animation_data.action = act_rest
for f in [1, 2]:
    scene.frame_set(f)
    reset_pose()
    key_all_deform(f)

# --- Action 2: A_FM_Idle_Pitch (Frames 1..40 cyclic tactical pitch stance) ---
act_idle = bpy.data.actions.new('A_FM_Idle_Pitch')
act_idle.use_fake_user = True
rig.animation_data.action = act_idle
for f, phase in [(1, 0.0), (20, 1.0), (40, 0.0)]:
    scene.frame_set(f)
    reset_pose()
    rig.pose.bones['pelvis'].location = (0, 0, -0.015 - 0.008 * phase)
    set_world_rot('pelvis',   wx=-4 - 2*phase, wy=0, wz=0)
    set_world_rot('spine_01', wx=-3 - 2*phase, wy=0, wz=0)
    set_world_rot('spine_03', wx=-4 - 2*phase, wy=0, wz=0)
    set_world_rot('neck_01',  wx= 6 + 2*phase, wy=0, wz=0)
    set_world_rot('upperarm_l', wx=-6,  wy=-14, wz=0)
    set_world_rot('upperarm_r', wx=-6,  wy= 14, wz=0)
    set_world_rot('lowerarm_l', wx=24 + 4*phase, wy=0, wz=0)
    set_world_rot('lowerarm_r', wx=24 + 4*phase, wy=0, wz=0)
    set_world_rot('thigh_l', wx= 14 + 3*phase, wy=0, wz=0)
    set_world_rot('thigh_r', wx= 14 + 3*phase, wy=0, wz=0)
    set_world_rot('calf_l',  wx=-24 - 5*phase, wy=0, wz=0)
    set_world_rot('calf_r',  wx=-24 - 5*phase, wy=0, wz=0)
    set_world_rot('foot_l',  wx= 10 + 2*phase, wy=0, wz=0)
    set_world_rot('foot_r',  wx= 10 + 2*phase, wy=0, wz=0)
    key_all_deform(f)

# --- Action 3: A_FM_Run_Dribble (Frames 1..25 cyclic football run stride) ---
act_run = bpy.data.actions.new('A_FM_Run_Dribble')
act_run.use_fake_user = True
rig.animation_data.action = act_run
run_frames = [
    (1,   38, -22,  10,  -30, -62, -15,  -10, -0.025),
    (7,    8, -28,   5,   12, -78, -20,    0, -0.042),
    (13, -30, -62, -15,   38, -22,  10,   10, -0.025),
    (19,  12, -78, -20,    8, -28,   5,    0, -0.042),
    (25,  38, -22,  10,  -30, -62, -15,  -10, -0.025),
]
for f, lt, lc, lf, rt, rc, rf, syaw, pz in run_frames:
    scene.frame_set(f)
    reset_pose()
    rig.pose.bones['pelvis'].location = (0, 0, pz)
    set_world_rot('pelvis',   wx=-10, wy=0, wz=-syaw*0.5)
    set_world_rot('spine_01', wx=-5,  wy=0, wz=syaw*0.5)
    set_world_rot('spine_03', wx=-6,  wy=0, wz=syaw*0.8)
    set_world_rot('neck_01',  wx= 12, wy=0, wz=-syaw*0.6)
    set_world_rot('thigh_l', wx=lt, wy=0, wz=0)
    set_world_rot('calf_l',  wx=lc, wy=0, wz=0)
    set_world_rot('foot_l',  wx=lf, wy=0, wz=0)
    set_world_rot('thigh_r', wx=rt, wy=0, wz=0)
    set_world_rot('calf_r',  wx=rc, wy=0, wz=0)
    set_world_rot('foot_r',  wx=rf, wy=0, wz=0)
    set_world_rot('upperarm_l', wx=rt*0.7, wy=-18, wz=0)
    set_world_rot('lowerarm_l', wx=48, wy=0, wz=0)
    set_world_rot('upperarm_r', wx=lt*0.7, wy= 18, wz=0)
    set_world_rot('lowerarm_r', wx=48, wy=0, wz=0)
    key_all_deform(f)

# --- Action 4: A_FM_Kick_PowerShot (Frames 1..36 Biomechanical Right-Foot Power Strike) ---
act_kick = bpy.data.actions.new('A_FM_Kick_PowerShot')
act_kick.use_fake_user = True
rig.animation_data.action = act_kick
kick_keyframes = [
    (1,  dict(pelv_z=-0.02, pelv=(-6, 0, -8), spine=(-5, 0, 8),
              thigh_l=( 18, 0, 0), calf_l=(-26, 0, 0), foot_l=( 8, 0, 0),
              thigh_r=(-14, 0, 0), calf_r=(-35, 0, 0), foot_r=(-10, 0, 0),
              uarm_l=( 18, -12, 0), larm_l=(28, 0, 0), uarm_r=(-12, 12, 0), larm_r=(25, 0, 0))),
    (12, dict(pelv_z=-0.03, pelv=(-8, 6, -16), spine=(-6, -5, 20),
              thigh_l=( 24, -4, 0), calf_l=(-32, 0, 0), foot_l=( 10, 0, 0),
              thigh_r=(-38,  6, 8), calf_r=(-78, 0, 0), foot_r=(-24, 0, 0),
              uarm_l=( 34, -10, -14), larm_l=(22, 0, 0), uarm_r=(-22, 10, 10), larm_r=(38, 0, 0))),
    (20, dict(pelv_z=-0.02, pelv=( 6, 8, 14), spine=(-8, -6, -16),
              thigh_l=( 10, -5, 0),  calf_l=(-20, 0, 0), foot_l=( 10, 0, 0),
              thigh_r=( 44, -6, -8), calf_r=(-10, 0, 0), foot_r=(-28, 0, 0),
              uarm_l=(-16, -12, -10), larm_l=(35, 0, 0), uarm_r=( 22, 12, 14), larm_r=(30, 0, 0))),
    (28, dict(pelv_z=-0.01, pelv=( 10, 5, 20), spine=(-10, -4, -18),
              thigh_l=(-6, -4, 0),   calf_l=(-14, 0, 0), foot_l=( 14, 0, 0),
              thigh_r=( 64, -10, -12), calf_r=(-18, 0, 0), foot_r=(-16, 0, 0),
              uarm_l=(-24, -14, -8), larm_l=(40, 0, 0), uarm_r=( 28, 10, 16), larm_r=(32, 0, 0))),
    (36, dict(pelv_z=-0.02, pelv=(-6, 0, 0), spine=(-5, 0, 0),
              thigh_l=( 14, 0, 0), calf_l=(-24, 0, 0), foot_l=( 10, 0, 0),
              thigh_r=( 14, 0, 0), calf_r=(-24, 0, 0), foot_r=( 10, 0, 0),
              uarm_l=(-6, -14, 0), larm_l=(24, 0, 0), uarm_r=(-6, 14, 0),   larm_r=(24, 0, 0))),
]
for f, k in kick_keyframes:
    scene.frame_set(f)
    reset_pose()
    rig.pose.bones['pelvis'].location = (0, 0, k['pelv_z'])
    set_world_rot('pelvis',     *k['pelv'])
    set_world_rot('spine_01',   *(v * 0.4 for v in k['spine']))
    set_world_rot('spine_03',   *(v * 0.6 for v in k['spine']))
    set_world_rot('neck_01',    *(-v * 0.5 for v in k['spine']))
    set_world_rot('thigh_l',    *k['thigh_l'])
    set_world_rot('calf_l',     *k['calf_l'])
    set_world_rot('foot_l',     *k['foot_l'])
    set_world_rot('thigh_r',    *k['thigh_r'])
    set_world_rot('calf_r',     *k['calf_r'])
    set_world_rot('foot_r',     *k['foot_r'])
    set_world_rot('upperarm_l', *k['uarm_l'])
    set_world_rot('lowerarm_l', *k['larm_l'])
    set_world_rot('upperarm_r', *k['uarm_r'])
    set_world_rot('lowerarm_r', *k['larm_r'])
    key_all_deform(f)

# Push all 4 actions to NLA tracks so FBX & GLB exporters include all 4 animations automatically!
for act_obj in [act_rest, act_idle, act_run, act_kick]:
    track = rig.animation_data.nla_tracks.new()
    track.name = act_obj.name
    strip = track.strips.new(act_obj.name, int(act_obj.frame_range[0]), act_obj)
    track.mute = True

scene.timeline_markers.clear()
rig.animation_data.action = act_rest
scene.frame_start = 1
scene.frame_end = 40
scene.frame_set(1)
reset_pose()
bpy.ops.object.mode_set(mode='OBJECT')

# ==============================================================================
# 6. EXPORT UE5-READY FBX, GLB, AND MASTER BLEND FILE
# ==============================================================================
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

fbx_path = OUT + '/Karakter_Brazil_UE5.fbx'
bpy.ops.export_scene.fbx(
    filepath=fbx_path,
    use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_armature_deform_only=True, # Excludes CTRL/MCH helper bones so UE5 gets a 100% pure Manny-compatible skeleton!
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=True,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    axis_forward='-Y',
    axis_up='Z',
    path_mode='COPY',
    embed_textures=True
)

glb_path = OUT + '/Karakter_Brazil_UE5.glb'
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    use_selection=True,
    export_format='GLB',
    export_def_bones=True,
    export_animations=True
)

# ==============================================================================
# 7. RENDER AN ACTION SHOWCASE OF THE POWER SHOT KICK + PITCH BALL FOR VERIFICATION
# ==============================================================================
# Add a 3D Football at the strike point (0.04, -0.32, 0.11) for the action preview render
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.11, location=(0.06, -0.34, 0.11))
ball_ob = bpy.context.object
ball_ob.name = 'Match_Ball_Preview'
bmat = mat('MI_Match_Ball', (0.92, 0.92, 0.94), rough=0.35, dimple=True)
ball_ob.data.materials.append(bmat)
for p in ball_ob.data.polygons:
    p.use_smooth = True

# Add green football pitch turf floor for the UE5 match engine showcase render
bpy.ops.mesh.primitive_plane_add(size=10.0, location=(0, 0, 0.0))
pitch = bpy.context.object
pitch.name = 'Pitch_Turf_Preview'
pmat = mat('MI_Pitch_Turf', (0.018, 0.12, 0.022), rough=0.82, weave=True)
pitch.data.materials.append(pmat)

# Camera & Studio Stadium Floodlights
bpy.ops.object.camera_add(location=(1.85, -3.65, 1.15))
cam = bpy.context.object
cam.name = 'UE5_Action_Camera'
cam.rotation_euler = (Vector((0.0, -0.10, 0.88)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = cam

lights = [
    ('Stadium Key',  ( 2.6, -2.2, 3.2), 450, 1.2, (1.0, 0.98, 0.95)),
    ('Stadium Fill', (-2.4, -2.8, 2.2), 180, 3.2, (0.90, 0.95, 1.0)),
    ('Stadium Rim',  (-0.8,  2.8, 2.8), 260, 2.4, (1.0, 0.97, 0.92)),
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
bg.inputs[0].default_value = (0.06, 0.08, 0.12, 1.0)
bg.inputs[1].default_value = 1.0

# Evaluate Frame 19 (Power Shot Ball Impact!) for the action render
rig.animation_data.action = act_kick
scene.frame_set(19)
bpy.context.view_layer.update()

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 750
scene.render.resolution_y = 900
scene.render.filepath = OUT + '/preview_ue5_kick_action.png'
bpy.ops.render.render(write_still=True)

# Remove temporary preview ball/turf and return character to Rest A-Pose before saving master .blend
bpy.data.objects.remove(ball_ob, do_unlink=True)
bpy.data.objects.remove(pitch, do_unlink=True)
rig.animation_data.action = act_rest
scene.frame_set(1)
bpy.context.view_layer.update()

blend_path = OUT + '/Karakter_Brazil_UE5.blend'
bpy.ops.wm.save_as_mainfile(filepath=blend_path)

report = {
    'mesh_name': ob.name,
    'skeleton_root': rig.name,
    'vertices': len(ob.data.vertices),
    'polygons': len(ob.data.polygons),
    'total_rig_bones': len(arm.bones),
    'ue5_deform_and_ik_bones': sum(b.use_deform for b in arm.bones),
    'control_helper_bones': sum(not b.use_deform for b in arm.bones),
    'baked_actions': [a.name for a in bpy.data.actions],
    'exports': [blend_path, fbx_path, glb_path]
}
with open(OUT + '/Karakter_Brazil_UE5_validation.json', 'w') as f:
    json.dump(report, f, indent=2)
print(json.dumps(report))
