import bpy
import os
import math
from mathutils import Matrix, Vector, Euler, Quaternion

PROJECT_DIR = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
PACK_DIR    = os.path.join(PROJECT_DIR, "Soccer Game Pack")
OUT_DIR     = os.path.join(PROJECT_DIR, "Output")
BLEND_PATH  = os.path.join(OUT_DIR, "Karakter_Brazil_UE5.blend")

# 1. Open Karakter_Brazil_UE5.blend
bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)

main_scene = bpy.data.scenes.get("Scene")
bpy.context.window.scene = main_scene

# Remove any old preview scenes if they exist
for sname in list(bpy.data.scenes.keys()):
    if sname != "Scene":
        bpy.data.scenes.remove(bpy.data.scenes[sname])

# Clean up any leftover Mixamo objects in main_scene
for obj in list(main_scene.objects):
    if obj.name.startswith("Mixamo") or obj.name.startswith("Armature") or obj.name == "nico_paz":
        bpy.data.objects.remove(obj, do_unlink=True)

rig_ue5 = main_scene.objects.get("root")
mesh_ue5 = main_scene.objects.get("SK_Brazil_Player")

# ==============================================================================
# 2. CREATE SCENE 2: "Soccer_Preview" (Nico Paz + Mixamo T-Pose Reference Skeleton)
# ==============================================================================
preview_scene = bpy.data.scenes.new("Soccer_Preview")
bpy.context.window.scene = preview_scene

# Import nico-paz.fbx (A-Pose Mesh + Armature)
nico_fbx = os.path.join(PACK_DIR, "nico-paz.fbx")
before_objs = set(bpy.data.objects.keys())
bpy.ops.import_scene.fbx(filepath=nico_fbx)
new_objs = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - before_objs]

nico_arm = None
nico_mesh = None
for o in new_objs:
    if o.type == 'ARMATURE':
        nico_arm = o
    elif o.type == 'MESH':
        nico_mesh = o

nico_arm.name = "Nico_Armature"
nico_mesh.name = "nico_paz"
nico_arm.scale = (1.0, 1.0, 1.0)
nico_mesh.scale = (1.0, 1.0, 1.0)
nico_arm.show_in_front = False
nico_arm.hide_viewport = False

# Assign clean material to nico_paz
if len(nico_mesh.data.materials) == 0 or nico_mesh.data.materials[0] is None:
    mat_nico = bpy.data.materials.new(name="MI_NicoPaz_Kit")
    mat_nico.use_nodes = True
    bsdf = mat_nico.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (0.18, 0.48, 0.88, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.38
    nico_mesh.data.materials.clear()
    nico_mesh.data.materials.append(mat_nico)

# Import a T-Pose Mixamo animation FBX to serve as the T-Pose Skeleton in Soccer_Preview
kneeing_fbx = os.path.join(PACK_DIR, "kneeing soccerball.fbx")
before_objs = set(bpy.data.objects.keys())
before_acts = set(bpy.data.actions.keys())
bpy.ops.import_scene.fbx(filepath=kneeing_fbx)
new_objs = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - before_objs]
new_acts = [bpy.data.actions[k] for k in set(bpy.data.actions.keys()) - before_acts]

tpose_skel = [o for o in new_objs if o.type == 'ARMATURE'][0]
tpose_skel.name = "Mixamo_TPose_Skeleton"
tpose_skel.scale = (1.0, 1.0, 1.0)
tpose_skel.location = (1.15, 0.0, 0.0) # Placed 1.15m to the left so user sees BOTH Nico Paz AND pure T-Pose Skeleton!
tpose_skel.data.display_type = 'OCTAHEDRAL'
tpose_skel.show_in_front = True

if new_acts:
    act_knee = new_acts[0]
    act_knee.name = "SP_Kneeing_Soccerball"
    act_knee.use_fake_user = True
    if not tpose_skel.animation_data:
        tpose_skel.animation_data_create()
    tpose_skel.animation_data.action = act_knee
    if hasattr(act_knee, 'slots') and len(act_knee.slots) > 0:
        tpose_skel.animation_data.action_slot_handle = act_knee.slots[0].handle

# Drive Nico_Armature from Mixamo_TPose_Skeleton via POSE-space Copy Rotation + Hips Copy Location!
# This 100% eliminates the 73.5-degree T-Pose vs A-Pose arm twisting!
if nico_arm.animation_data:
    nico_arm.animation_data_clear()

for pb_m in nico_arm.pose.bones:
    for c in list(pb_m.constraints):
        pb_m.constraints.remove(c)
    if pb_m.name in tpose_skel.pose.bones:
        if pb_m.name == "mixamorig:Hips":
            cl = pb_m.constraints.new('COPY_LOCATION')
            cl.name = "TPose_Retarget_Loc"
            cl.target = tpose_skel
            cl.subtarget = pb_m.name
            cl.target_space = 'POSE'
            cl.owner_space = 'POSE'
        cr = pb_m.constraints.new('COPY_ROTATION')
        cr.name = "TPose_Retarget_Rot"
        cr.target = tpose_skel
        cr.subtarget = pb_m.name
        cr.target_space = 'POSE'
        cr.owner_space = 'POSE'

# Add Pitch Floor, Camera, and Stadium Lights to Soccer_Preview
bpy.ops.mesh.primitive_plane_add(size=14.0, location=(0.5, 0, 0))
floor_p = bpy.context.object
floor_p.name = "Soccer_Floor"
if "MI_Pitch_Turf" in bpy.data.materials:
    floor_p.data.materials.append(bpy.data.materials["MI_Pitch_Turf"])

bpy.ops.object.camera_add(location=(0.55, -3.8, 1.15))
cam_p = bpy.context.object
cam_p.name = "Preview_Camera"
cam_p.rotation_euler = (Vector((0.55, 0.0, 0.95)) - cam_p.location).to_track_quat('-Z', 'Y').to_euler()
preview_scene.camera = cam_p

for lname, loc, energy in [("Key_Light", (2.8, -2.6, 3.4), 500), ("Fill_Light", (-2.2, -2.5, 2.4), 250), ("Rim_Light", (0.5, 2.8, 2.8), 300)]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    lt = bpy.context.object
    lt.name = lname
    lt.data.energy = energy
    lt.data.size = 2.5

preview_scene.frame_start = 1
preview_scene.frame_end = 28
preview_scene.frame_set(15)

# ==============================================================================
# 3. SETUP REAL-TIME MIXAMO -> UE5 BRAZIL PLAYER RETARGETER IN MAIN "Scene"
# ==============================================================================
bpy.context.window.scene = main_scene

# Import Mixamo_Driver into main_scene
before_objs = set(bpy.data.objects.keys())
bpy.ops.import_scene.fbx(filepath=kneeing_fbx)
new_objs = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - before_objs]
mix_driver = [o for o in new_objs if o.type == 'ARMATURE'][0]
mix_driver.name = "Mixamo_Driver"

bone_map = [
    ("mixamorig:Hips",          "pelvis"),
    ("mixamorig:Spine",         "spine_01"),
    ("mixamorig:Spine1",        "spine_03"),
    ("mixamorig:Spine2",        "spine_05"),
    ("mixamorig:Neck",          "neck_01"),
    ("mixamorig:Head",          "head"),
    ("mixamorig:LeftShoulder",  "clavicle_l"),
    ("mixamorig:LeftArm",       "upperarm_l"),
    ("mixamorig:LeftForeArm",   "lowerarm_l"),
    ("mixamorig:LeftHand",      "hand_l"),
    ("mixamorig:RightShoulder", "clavicle_r"),
    ("mixamorig:RightArm",      "upperarm_r"),
    ("mixamorig:RightForeArm",  "lowerarm_r"),
    ("mixamorig:RightHand",     "hand_r"),
    ("mixamorig:LeftUpLeg",     "thigh_l"),
    ("mixamorig:LeftLeg",       "calf_l"),
    ("mixamorig:LeftFoot",      "foot_l"),
    ("mixamorig:LeftToeBase",   "ball_l"),
    ("mixamorig:RightUpLeg",    "thigh_r"),
    ("mixamorig:RightLeg",      "calf_r"),
    ("mixamorig:RightFoot",     "foot_r"),
    ("mixamorig:RightToeBase",  "ball_r"),
]

# Compute exact C_roll adapter matrices between Nico_Armature (A-pose) and rig_ue5 (A-pose)
mw_mix = nico_arm.matrix_world.to_3x3().normalized()
c_roll_map = {}
for m_name, u_name in bone_map:
    bm = nico_arm.data.bones.get(m_name)
    bu = rig_ue5.data.bones.get(u_name)
    w_mix_rest = mw_mix @ bm.matrix_local.to_3x3()
    w_ue5_rest = bu.matrix_local.to_3x3()
    ym = w_mix_rest.col[1].normalized()
    yu = w_ue5_rest.col[1].normalized()
    r_shaft = ym.rotation_difference(yu).to_matrix()
    c_roll = (r_shaft @ w_mix_rest).inverted() @ w_ue5_rest
    c_roll_map[(m_name, u_name)] = c_roll

# Add RET_<u_name> helper bones to Mixamo_Driver in Edit Mode
bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT')
mix_driver.select_set(True)
bpy.context.view_layer.objects.active = mix_driver
bpy.ops.object.mode_set(mode='EDIT')

ebones = mix_driver.data.edit_bones
for m_name, u_name in bone_map:
    ret_name = f"RET_{u_name}"
    if ret_name in ebones:
        ebones.remove(ebones[ret_name])
    eb_parent = ebones.get(m_name)
    eb_ret = ebones.new(ret_name)
    eb_ret.parent = eb_parent
    eb_ret.use_connect = False
    eb_ret.use_deform = False

    r_anim = eb_parent.matrix.to_3x3().normalized()
    r_ret = r_anim @ c_roll_map[(m_name, u_name)]

    mat4 = Matrix.Identity(4)
    for r in range(3):
        for c in range(3):
            mat4[r][c] = r_ret[r][c]
    mat4.translation = eb_parent.head.copy()
    eb_ret.length = 0.05
    eb_ret.matrix = mat4

bpy.ops.object.mode_set(mode='OBJECT')

# Scale Mixamo_Driver so Hips rest Z (1.0031) matches UE5 Pelvis rest Z (0.785)
scale_f = 0.785 / 1.0031
mix_driver.scale = (scale_f, scale_f, scale_f)
mix_driver.location = (0.0, -0.012, 0.0)
mix_driver.hide_viewport = True
mix_driver.hide_render = True

# Add Mixamo_Retarget constraints on rig_ue5 (default influence = 1.0 when playing Soccer Pack, 0.0 when playing native UE5 actions)
for pb in rig_ue5.pose.bones:
    for c in list(pb.constraints):
        if c.name.startswith("Mixamo_Retarget"):
            pb.constraints.remove(c)

pelv_pb = rig_ue5.pose.bones["pelvis"]
cl = pelv_pb.constraints.new('COPY_LOCATION')
cl.name = "Mixamo_Retarget_Loc"
cl.target = mix_driver
cl.subtarget = "mixamorig:Hips"
cl.target_space = 'WORLD'
cl.owner_space = 'WORLD'
cl.influence = 1.0

for m_name, u_name in bone_map:
    pb_u = rig_ue5.pose.bones.get(u_name)
    cr = pb_u.constraints.new('COPY_ROTATION')
    cr.name = "Mixamo_Retarget_Rot"
    cr.target = mix_driver
    cr.subtarget = f"RET_{u_name}"
    cr.target_space = 'WORLD'
    cr.owner_space = 'WORLD'
    cr.influence = 1.0

# Clear active action on rig_ue5 while Mixamo_Driver drives it, and assign SP_Kneeing_Soccerball to Mixamo_Driver
rig_ue5.animation_data.action = None
if not mix_driver.animation_data:
    mix_driver.animation_data_create()
mix_driver.animation_data.action = bpy.data.actions["SP_Kneeing_Soccerball"]
if hasattr(mix_driver.animation_data.action, 'slots') and len(mix_driver.animation_data.action.slots) > 0:
    mix_driver.animation_data.action_slot_handle = mix_driver.animation_data.action.slots[0].handle

# Pre-load flagship Soccer Game Pack animations so they are immediately available in bpy.data.actions!
flagship_files = [
    ("scissor kick.fbx",            "SP_Scissor_Kick"),
    ("soccer penalty kick.fbx",     "SP_Penalty_Kick"),
    ("soccer tackle.fbx",           "SP_Sliding_Tackle"),
    ("header soccerball.fbx",       "SP_Header_Ball"),
    ("kneeing soccerball.fbx",      "SP_Kneeing_Soccerball"),
    ("goalkeeper diving save.fbx",  "SP_GK_Diving_Save"),
    ("goalkeeper drop kick.fbx",    "SP_GK_Drop_Kick"),
    ("jog forward.fbx",             "SP_Jog_Forward"),
    ("kick soccerball.fbx",         "SP_Kick_Soccerball"),
    ("receive soccerball.fbx",      "SP_Receive_Ball"),
    ("throw in.fbx",                "SP_Throw_In"),
]

for fname, act_name in flagship_files:
    if act_name in bpy.data.actions:
        continue
    fpath = os.path.join(PACK_DIR, fname)
    if os.path.exists(fpath):
        b_objs = set(bpy.data.objects.keys())
        b_acts = set(bpy.data.actions.keys())
        bpy.ops.import_scene.fbx(filepath=fpath)
        n_objs = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - b_objs]
        n_acts = [bpy.data.actions[k] for k in set(bpy.data.actions.keys()) - b_acts]
        if n_acts:
            a = n_acts[0]
            a.name = act_name
            a.use_fake_user = True
        for o in n_objs:
            bpy.data.objects.remove(o, do_unlink=True)

# Set initial action on both Mixamo_Driver (Scene) and Mixamo_TPose_Skeleton (Soccer_Preview) to SP_Scissor_Kick!
act_init = bpy.data.actions.get("SP_Scissor_Kick") or bpy.data.actions.get("SP_Kneeing_Soccerball")
for drv in [mix_driver, tpose_skel]:
    drv.animation_data.action = act_init
    if hasattr(act_init, 'slots') and len(act_init.slots) > 0:
        drv.animation_data.action_slot_handle = act_init.slots[0].handle

main_scene.frame_start = int(act_init.frame_range[0])
main_scene.frame_end = int(act_init.frame_range[1])
main_scene.frame_set(24)

preview_scene.frame_start = int(act_init.frame_range[0])
preview_scene.frame_end = int(act_init.frame_range[1])
preview_scene.frame_set(24)

# ==============================================================================
# 4. EMBED AUTO-RUN UI CONTROLLER SCRIPT INSIDE THE BLEND FILE
# ==============================================================================
ui_script_code = '''import bpy
import os

PACK_DIR = r"c:\\Users\\Legion 3\\Documents\\PROJECT\\animasi\\karakter\\Soccer Game Pack"

def set_retarget_constraints(rig_ue5, enabled):
    if not rig_ue5:
        return
    inf = 1.0 if enabled else 0.0
    for pb in rig_ue5.pose.bones:
        for c in pb.constraints:
            if c.name.startswith("Mixamo_Retarget"):
                c.influence = inf

class WM_OT_SwitchSoccerScene(bpy.types.Operator):
    bl_idname = "wm.switch_soccer_scene"
    bl_label = "Switch Character Scene"
    scene_target: bpy.props.StringProperty()

    def execute(self, context):
        sc = bpy.data.scenes.get(self.scene_target)
        if sc:
            context.window.scene = sc
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    for space in area.spaces:
                        if space.type == 'VIEW_3D':
                            space.shading.type = 'MATERIAL'
        return {'FINISHED'}

class WM_OT_PlaySoccerPackAction(bpy.types.Operator):
    bl_idname = "wm.play_soccer_pack_action"
    bl_label = "Play Soccer Pack Animation"
    file_name: bpy.props.StringProperty()
    act_name: bpy.props.StringProperty()

    def execute(self, context):
        act = bpy.data.actions.get(self.act_name)
        if not act and self.file_name:
            fpath = os.path.join(PACK_DIR, self.file_name)
            if os.path.exists(fpath):
                b_objs = set(bpy.data.objects.keys())
                b_acts = set(bpy.data.actions.keys())
                bpy.ops.import_scene.fbx(filepath=fpath)
                n_objs = [bpy.data.objects[k] for k in set(bpy.data.objects.keys()) - b_objs]
                n_acts = [bpy.data.actions[k] for k in set(bpy.data.actions.keys()) - b_acts]
                if n_acts:
                    act = n_acts[0]
                    act.name = self.act_name
                    act.use_fake_user = True
                for o in n_objs:
                    bpy.data.objects.remove(o, do_unlink=True)

        if not act:
            self.report({'WARNING'}, f"Animation {self.act_name} not found")
            return {'CANCELLED'}

        # Apply to both Mixamo_Driver (Brazil UE5) and Mixamo_TPose_Skeleton (Nico Paz + Skeleton)
        rig_ue5 = bpy.data.objects.get("root")
        if rig_ue5 and rig_ue5.animation_data:
            rig_ue5.animation_data.action = None
        set_retarget_constraints(rig_ue5, True)

        for drv_name in ["Mixamo_Driver", "Mixamo_TPose_Skeleton"]:
            drv = bpy.data.objects.get(drv_name)
            if drv:
                if not drv.animation_data:
                    drv.animation_data_create()
                drv.animation_data.action = act
                if hasattr(act, 'slots') and len(act.slots) > 0:
                    drv.animation_data.action_slot_handle = act.slots[0].handle

        for sc_name in ["Scene", "Soccer_Preview"]:
            sc = bpy.data.scenes.get(sc_name)
            if sc:
                sc.frame_start = int(act.frame_range[0])
                sc.frame_end = int(act.frame_range[1])
                sc.frame_set(sc.frame_start)

        if not context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()
        return {'FINISHED'}

class FM_PT_UnifiedSoccerPanel(bpy.types.Panel):
    bl_label = "Soccer Pack & UE5 Browser"
    bl_idname = "FM_PT_unified_soccer_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Soccer Pack'

    def draw(self, context):
        layout = self.layout
        
        box_mode = layout.box()
        box_mode.label(text="1. Pilih Tampilan Karakter:", icon='ARMATURE_DATA')
        row = box_mode.row(align=True)
        op1 = row.operator("wm.switch_soccer_scene", text="Karakter Brasil UE5", icon='USER')
        op1.scene_target = "Scene"
        op2 = row.operator("wm.switch_soccer_scene", text="Nico Paz + T-Pose", icon='OUTLINER_OB_ARMATURE')
        op2.scene_target = "Soccer_Preview"

        box_sp = layout.box()
        box_sp.label(text="2. Gerakan Soccer Game Pack (Retargeted):", icon='PLAY')
        col = box_sp.column(align=True)
        
        sp_items = [
            ("scissor kick.fbx",           "SP_Scissor_Kick",       "Scissor Kick (Salto)"),
            ("soccer penalty kick.fbx",    "SP_Penalty_Kick",       "Penalty Kick (Penalti)"),
            ("soccer tackle.fbx",          "SP_Sliding_Tackle",     "Sliding Tackle"),
            ("header soccerball.fbx",      "SP_Header_Ball",        "Header (Sundulan)"),
            ("kneeing soccerball.fbx",     "SP_Kneeing_Soccerball", "Kneeing (Kontrol Paha)"),
            ("goalkeeper diving save.fbx", "SP_GK_Diving_Save",     "GK Diving Save (Kiper)"),
            ("goalkeeper drop kick.fbx",   "SP_GK_Drop_Kick",       "GK Drop Kick"),
            ("kick soccerball.fbx",        "SP_Kick_Soccerball",    "Kick Soccerball"),
            ("receive soccerball.fbx",     "SP_Receive_Ball",       "Receive Pass"),
            ("throw in.fbx",               "SP_Throw_In",           "Throw In (Lemparan)"),
            ("jog forward.fbx",            "SP_Jog_Forward",        "Jog Forward (Lari)"),
        ]
        for fname, aname, label in sp_items:
            op = col.operator("wm.play_soccer_pack_action", text=label, icon='ACTION')
            op.file_name = fname
            op.act_name = aname

        layout.separator()
        layout.operator("screen.animation_play", text="Play / Pause (Spasi)", icon='TIME')

classes = [
    WM_OT_SwitchSoccerScene,
    WM_OT_PlaySoccerPackAction,
    FM_PT_UnifiedSoccerPanel,
]

for cls in classes:
    try:
        bpy.utils.unregister_class(cls)
    except Exception:
        pass
    bpy.utils.register_class(cls)
'''

txt_name = "ui_soccer_pack_controller.py"
if txt_name in bpy.data.texts:
    bpy.data.texts.remove(bpy.data.texts[txt_name])
txt = bpy.data.texts.new(txt_name)
txt.write(ui_script_code)
txt.use_module = True

# Also write startup script to disk so launching Blender runs it + starts playback!
startup_path = os.path.join(PROJECT_DIR, "launch_soccer_viewer.py")
with open(startup_path, "w", encoding="utf-8") as f:
    f.write(ui_script_code + "\n")
    f.write('''
# Set viewport shading to MATERIAL in active window
try:
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
except Exception as e:
    print("Shading setup note:", e)
''')

# ==============================================================================
# 5. RENDER VERIFICATION PREVIEWS FOR BOTH SCENES
# ==============================================================================
# Render 1: Karakter Brasil UE5 performing Retargeted Scissor Kick (Frame 25)
bpy.context.window.scene = main_scene
main_scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
main_scene.render.resolution_x = 900
main_scene.render.resolution_y = 900
main_scene.frame_set(25)
bpy.context.view_layer.update()
main_scene.render.filepath = os.path.join(OUT_DIR, "preview_brazil_scissor_kick.png")
bpy.ops.render.render(write_still=True)

# Render 2: Nico Paz + Mixamo T-Pose Skeleton side by side performing Kneeing (Frame 15)
act_knee = bpy.data.actions.get("SP_Kneeing_Soccerball")
tpose_skel.animation_data.action = act_knee
if hasattr(act_knee, 'slots') and len(act_knee.slots) > 0:
    tpose_skel.animation_data.action_slot_handle = act_knee.slots[0].handle

bpy.context.window.scene = preview_scene
preview_scene.render.engine = main_scene.render.engine
preview_scene.render.resolution_x = 1100
preview_scene.render.resolution_y = 850
preview_scene.frame_set(15)
bpy.context.view_layer.update()
preview_scene.render.filepath = os.path.join(OUT_DIR, "preview_nico_tpose_fixed.png")
bpy.ops.render.render(write_still=True)

# Reset both to SP_Kneeing_Soccerball at frame 15 and default to main_scene (Karakter Brasil UE5)
mix_driver.animation_data.action = act_knee
if hasattr(act_knee, 'slots') and len(act_knee.slots) > 0:
    mix_driver.animation_data.action_slot_handle = act_knee.slots[0].handle
main_scene.frame_start = int(act_knee.frame_range[0])
main_scene.frame_end = int(act_knee.frame_range[1])
main_scene.frame_set(15)

bpy.context.window.scene = main_scene
bpy.ops.wm.save_mainfile(filepath=BLEND_PATH)
print("SUCCESS: Built and saved unified Karakter_Brazil_UE5.blend with Opsi 1 & Opsi 2!")
