import bpy, bmesh, math, json, os
from mathutils import Vector, Quaternion

ROOT = r'c:/Users/Legion 3/Documents/PROJECT/animasi/karakter'
OUT = ROOT + '/Output'
scene = bpy.context.scene

# Join all character mesh components inside BUILD into a single multi-material character mesh 'Karakter Brazil'
buildcol = next((c for c in bpy.data.collections if c.name.startswith('BUILD |')), None)
if buildcol:
    obs = [o for o in buildcol.objects if o.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.join()
    ob = bpy.context.object
    ob.name = 'Karakter Brazil'
    ob.data.name = 'Karakter Brazil | Mesh'
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    scene.collection.objects.link(ob)
    bpy.data.collections.remove(buildcol)
else:
    ob = bpy.data.objects['Karakter Brazil']

bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
scene.cursor.location = (0, 0, 0)
bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

# Clean duplicate vertices and ensure outward normals
bm = bmesh.new()
bm.from_mesh(ob.data)
bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(ob.data)
bm.free()

# ==============================================================================
# BUILD 52-BONE ATHLETIC HUMANOID SKELETON IN RELAXED A-POSE
# ==============================================================================
arm = bpy.data.armatures.new('Karakter Brazil | Athletic Skeleton')
rig = bpy.data.objects.new('Karakter Brazil Rig', arm)
scene.collection.objects.link(rig)
rig.show_in_front = True

bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')

spec = {}
def bone(name, h, t, parent=None, connected=False, deform=True):
    b = arm.edit_bones.new(name)
    b.head = h
    b.tail = t
    if parent:
        b.parent = arm.edit_bones[parent]
        b.use_connect = connected
    b.use_deform = deform
    spec[name] = (Vector(h), Vector(t))
    return b

bone('root',   (0, 0, 0.000), (0, 0, 0.120), deform=False)
bone('pelvis', (0, -0.012, 0.785), (0, -0.016, 0.915), 'root')
bone('spine',  (0, -0.016, 0.915), (0, -0.021, 1.140), 'pelvis', True)
bone('chest',  (0, -0.021, 1.140), (0, -0.006, 1.445), 'spine', True)
bone('neck',   (0, -0.006, 1.445), (0,  0.002, 1.575), 'chest', True)
bone('head',   (0,  0.002, 1.575), (0, -0.004, 1.800), 'neck', True)

for s, side in [(1, 'L'), (-1, 'R')]:
    shoulder = (s * 0.175, -0.005, 1.425)
    elbow    = (s * 0.282,  0.002, 1.190)
    wrist    = (s * 0.376, -0.112, 1.002)
    knuckle  = (s * 0.408, -0.158, 0.935)

    bone('clavicle.' + side,  (0, -0.006, 1.430), shoulder, 'chest')
    bone('upper_arm.' + side, shoulder, elbow, 'clavicle.' + side, True)
    bone('forearm.' + side,   elbow, wrist, 'upper_arm.' + side, True)
    bone('hand.' + side,      wrist, knuckle, 'forearm.' + side, True)

    finger_specs = [
        ('index',  -0.021,  0.003,  0.004, 0.080, -0.66, 0.42),
        ('middle', -0.007,  0.005,  0.002, 0.088, -0.54, 0.45),
        ('ring',    0.008,  0.004, -0.002, 0.082, -0.42, 0.44),
        ('pinky',   0.021,  0.001, -0.006, 0.068, -0.28, 0.40),
    ]
    knuckle_vec = Vector(knuckle)
    for fn, dy, dx, dz, flen, py, yx in finger_specs:
        f_root = knuckle_vec + Vector((s * dx, dy, dz))
        f_dir = Vector((s * yx, py, -0.78)).normalized()
        prev = 'hand.' + side
        for j in range(3):
            u0, u1 = j / 3.0, (j + 1) / 3.0
            p0 = f_root + f_dir * (flen * u0) + Vector((-s * 0.006 * u0 * u0, -0.004 * u0, -0.008 * u0 * u0))
            p1 = f_root + f_dir * (flen * u1) + Vector((-s * 0.006 * u1 * u1, -0.004 * u1, -0.008 * u1 * u1))
            bname = f'{fn}.{str(j+1).zfill(2)}.{side}'
            bone(bname, tuple(p0), tuple(p1), prev, j > 0)
            prev = bname

    w_vec = Vector(wrist) + Vector((s * 0.006, -0.016, -0.010))
    t_pts = [
        tuple(w_vec),
        tuple(w_vec + Vector((s * 0.008, -0.024, -0.016))),
        tuple(w_vec + Vector((s * 0.015, -0.048, -0.034))),
        tuple(w_vec + Vector((s * 0.022, -0.072, -0.052))),
    ]
    prev = 'hand.' + side
    for j in range(3):
        bname = f'thumb.{str(j+1).zfill(2)}.{side}'
        bone(bname, t_pts[j], t_pts[j+1], prev, j > 0)
        prev = bname

    hip   = (s * 0.095, -0.012, 0.805)
    knee  = (s * 0.120, -0.008, 0.565)
    ankle = (s * 0.148,  0.005, 0.125)
    ball  = (s * 0.158, -0.095, 0.030)
    toe   = (s * 0.165, -0.185, 0.022)

    bone('thigh.' + side, hip, knee, 'pelvis')
    bone('shin.' + side,  knee, ankle, 'thigh.' + side, True)
    bone('foot.' + side,  ankle, ball, 'shin.' + side, True)
    bone('toe.' + side,   ball, toe, 'foot.' + side, True)

bpy.ops.object.mode_set(mode='OBJECT')
arm.display_type = 'OCTAHEDRAL'

# ==============================================================================
# NORMALIZED SMOOTH SKINNING WEIGHTS FOR ALL VERTICES
# ==============================================================================
groups = {name: ob.vertex_groups.new(name=name) for name in spec if name != 'root'}

def segment_distance(p, name):
    a, b = spec[name]
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
    side = 'L' if x >= 0 else 'R'

    if z > 1.565:
        weights = {'head': 1.0}
    elif z > 1.445 and abs(x) < 0.125:
        w = smoothstep(1.445, 1.565, z)
        weights = {'head': w, 'neck': 1.0 - w}
    elif abs(x) > 0.195 and 0.80 < z < 1.445:
        finger_names = [n for n in spec if n.endswith('.' + side) and any(n.startswith(f) for f in ['index', 'middle', 'ring', 'pinky', 'thumb'])]
        arm_names = ['clavicle.' + side, 'upper_arm.' + side, 'forearm.' + side, 'hand.' + side]
        if abs(x) > 0.385 and z < 0.965:
            closest = min(finger_names, key=lambda n: segment_distance(p, n))
            family = closest.split('.')[0]
            names = [n for n in finger_names if n.startswith(family + '.')] + ['hand.' + side]
            weights = blend_chain(p, names)
        else:
            weights = blend_chain(p, arm_names)
    elif z < 0.810:
        if z < 0.155:
            weights = blend_chain(p, ['shin.' + side, 'foot.' + side, 'toe.' + side], 5.0)
        else:
            weights = blend_chain(p, ['thigh.' + side, 'shin.' + side, 'pelvis'], 5.0)
            if z > 0.740:
                w = smoothstep(0.740, 0.810, z)
                weights = {n: q * (1.0 - w) for n, q in weights.items()}
                weights['pelvis'] = weights.get('pelvis', 0.0) + w
    elif z < 0.960:
        w = smoothstep(0.860, 0.960, z)
        weights = {'pelvis': 1.0 - w, 'spine': w}
    elif z < 1.220:
        w = smoothstep(1.080, 1.220, z)
        weights = {'spine': 1.0 - w, 'chest': w}
    else:
        if abs(x) > 0.130 and z > 1.320:
            w = 0.55 * smoothstep(0.130, 0.195, abs(x))
            weights = {'chest': 1.0 - w, 'clavicle.' + side: w}
        else:
            weights = {'chest': 1.0}

    total = sum(q for q in weights.values() if q > 0)
    for n, q in weights.items():
        if q > 0:
            groups[n].add([v.index], q / total, 'REPLACE')

mod = ob.modifiers.new('Athletic Skeleton Deform', 'ARMATURE')
mod.object = rig
mod.use_deform_preserve_volume = True
ob.parent = rig
ob.matrix_parent_inverse = rig.matrix_world.inverted()

# Organize collections cleanly
char_col = bpy.data.collections.new('CHARACTER | Karakter Brazil')
scene.collection.children.link(char_col)
for obj in [ob, rig]:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    char_col.objects.link(obj)

render_col = bpy.data.collections.new('RENDER | Studio Setup')
scene.collection.children.link(render_col)
for obj in list(scene.objects):
    if obj.type in {'LIGHT', 'CAMERA'}:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        render_col.objects.link(obj)

# Test deformation with temporary elbow & knee bend, then reset to rest A-pose
rest = [v.co.copy() for v in ob.data.vertices]
rig.pose.bones['forearm.L'].rotation_mode = 'XYZ'
rig.pose.bones['forearm.L'].rotation_euler[0] = math.radians(20)
rig.pose.bones['shin.R'].rotation_mode = 'XYZ'
rig.pose.bones['shin.R'].rotation_euler[0] = math.radians(18)
bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = ob.evaluated_get(deps)
me = ev.to_mesh()
delta = [(v.co - rest[i]).length for i, v in enumerate(me.vertices)]
ev.to_mesh_clear()

for pb in rig.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
bpy.context.view_layer.update()
rig.hide_set(True)

bm = bmesh.new()
bm.from_mesh(ob.data)
report = {
    'name': ob.name,
    'height_m': round(ob.dimensions.z, 4),
    'vertices': len(bm.verts),
    'faces': len(bm.faces),
    'quad_percent': round(100.0 * sum(len(f.verts) == 4 for f in bm.faces) / max(1, len(bm.faces)), 2),
    'bones': len(arm.bones),
    'materials': len(ob.data.materials),
    'unweighted_vertices': sum(not v.groups for v in ob.data.vertices),
    'pose_test_max_displacement_m': round(max(delta), 4),
    'pose_test_moved_vertices': sum(d > 1e-5 for d in delta),
}
bm.free()

with open(OUT + '/Karakter_Brazil_validation.json', 'w') as f:
    json.dump(report, f, indent=2)

bpy.ops.wm.save_as_mainfile(filepath=OUT + '/Karakter_Brazil.blend')

# Also export .glb for universal 3D / Game Engine / Animation compatibility
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
rig.hide_set(False)
rig.select_set(True)
bpy.ops.export_scene.gltf(
    filepath=OUT + '/Karakter_Brazil.glb',
    use_selection=True,
    export_format='GLB',
    export_apply=False
)
rig.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=OUT + '/Karakter_Brazil.blend')
print(json.dumps(report))
