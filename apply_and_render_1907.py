import bpy
import os
import math
from mathutils import Vector

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

# Unpack or replace all curva seat textures
tex_curva_white = os.path.join(ASSETS, "como_curva_seats_pure_white.png")
new_img_white = bpy.data.images.load(tex_curva_white, check_existing=False)

tex_curva_crest = os.path.join(ASSETS, "como_curva_seats_with_crest.png")
new_img_crest = bpy.data.images.load(tex_curva_crest, check_existing=False)

mat = bpy.data.materials.get("M_Curva_Seats")
tex_node = None
for n in mat.node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        tex_node = n
        break

# Test 1: Render Pure White "19 07"
tex_node.image = new_img_white

# Set up camera matching media_1792133622110_e64b0fe6.png
# In media_1792133622110_e64b0fe6.png:
# Camera is positioned near the penalty spot / arc (X = -41.0, Y = 0.0, Z = 2.4)
# Looking directly at the goal (X = -52.5) and Curva stand (X = -56..-78)
cam_name = "Cam_User_Curva_1907_Match"
cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
cam_obj = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)
if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)

cam_obj.location = (-22.0, 0.0, 3.5)
aim = Vector((-56.0, 0.0, 4.5))
direction = aim - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
cam_data.lens = 18.0 # Wide angle to capture both floodlights, just like user screenshot!

bpy.context.scene.camera = cam_obj
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

# Render Pure White version
preview_white = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_pure_white.png"
bpy.context.scene.render.filepath = preview_white
bpy.ops.render.render(write_still=True)
print("Rendered pure white to:", preview_white)

# Test 2: Render With Crest version
tex_node.image = new_img_crest
preview_crest = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_with_crest.png"
bpy.context.scene.render.filepath = preview_crest
bpy.ops.render.render(write_still=True)
print("Rendered with crest to:", preview_crest)
