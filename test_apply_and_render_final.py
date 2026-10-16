import bpy
import os
from mathutils import Vector

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

# 1. Update M_Curva_Seats with punchy white 1907
tex_path = os.path.join(ASSETS, "como_curva_seats_punchy_white.png")
new_img = bpy.data.images.load(tex_path, check_existing=False)
new_img.pack()

mat = bpy.data.materials.get("M_Curva_Seats")
for n in mat.node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        n.image = new_img
        print("Updated M_Curva_Seats image to:", new_img.name)

# 2. Camera setup matching media_1792133622110_e64b0fe6.png exactly
cam_name = "Cam_User_Curva_1907_Match"
cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
cam_obj = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)
if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)

# Camera positioned in penalty arc looking at left stand
cam_obj.location = (-22.0, 0.0, 3.2)
aim = Vector((-56.0, 0.0, 5.0))
direction = aim - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
cam_data.lens = 19.0

bpy.context.scene.camera = cam_obj
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

# Render White Version
preview_white = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_punchy_white.png"
bpy.context.scene.render.filepath = preview_white
bpy.ops.render.render(write_still=True)
print("Rendered white version to:", preview_white)

# 3. Render Crest Version for comparison
tex_crest_path = os.path.join(ASSETS, "como_curva_seats_punchy_crest.png")
new_crest_img = bpy.data.images.load(tex_crest_path, check_existing=False)
new_crest_img.pack()
for n in mat.node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        n.image = new_crest_img

preview_crest = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_punchy_crest.png"
bpy.context.scene.render.filepath = preview_crest
bpy.ops.render.render(write_still=True)
print("Rendered crest version to:", preview_crest)

# Default to the pure white version (per user request: "bertulisakn 19 07 berwarna putih")
for n in mat.node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        n.image = new_img

# Pack and save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved blend file successfully!")
