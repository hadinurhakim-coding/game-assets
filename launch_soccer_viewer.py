import bpy
import os

PACK_DIR = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter\Soccer Game Pack"

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


# Set viewport shading to MATERIAL in active window
try:
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.shading.type = 'MATERIAL'
                        space.show_region_ui = True
except Exception as e:
    print("Shading setup note:", e)
