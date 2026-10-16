import bpy
from mathutils import Vector

cam_name = "Cam_Goal_Closeup_Inspection"
cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
cam_obj = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)
if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)

cam_obj.location = (-50.5, -2.2, 1.8)
aim = Vector((-53.5, -3.66, 2.3))
direction = aim - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
cam_data.lens = 42.0

bpy.context.scene.camera = cam_obj
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_goal_closeup_hex.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered closeup to:", preview_path)
