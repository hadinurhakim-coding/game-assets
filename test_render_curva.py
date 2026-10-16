import bpy
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

# Open current blend file
bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

# Reload all images
for img in bpy.data.images:
    img.reload()

# Check M_Curva_Seats material
mat = bpy.data.materials.get("M_Curva_Seats")
if mat and mat.use_nodes:
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            node.image.reload()
            print("Reloaded texture:", node.image.name, node.image.filepath)

# Create or set camera matching media_1792133622110_e64b0fe6.png
cam_name = "Cam_User_Curva_1907_Match"
cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
cam_obj = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)

if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)

# Camera position:
# Looking directly at Curva Sud (X = -56..-78, Y = 0, Z = 1.2..12)
# In the screenshot, the camera is near the center or penalty arc (X ~ -28, Y ~ 0, Z ~ 2.2)
cam_obj.location = (-26.0, 0.0, 2.4)
# Aim directly at center of Curva Sud
import math
from mathutils import Vector

aim = Vector((-56.0, 0.0, 5.0))
loc = Vector((-26.0, 0.0, 2.4))
direction = aim - loc
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
cam_data.lens = 22.0 # Wide angle to see both floodlights

bpy.context.scene.camera = cam_obj
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_match.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered Curva 1907 view to:", preview_path)
