import bpy
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

tex_curva = os.path.join(ASSETS, "como_curva_seats.png")
new_img = bpy.data.images.load(tex_curva, check_existing=False)

mat = bpy.data.materials.get("M_Curva_Seats")
if mat and mat.use_nodes:
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            node.image = new_img
            print("Assigned new image:", new_img.name, new_img.size[:])

# Check camera
cam_name = "Cam_User_Curva_1907_Match"
cam_data = bpy.data.cameras.get(cam_name) or bpy.data.cameras.new(cam_name)
cam_obj = bpy.data.objects.get(cam_name) or bpy.data.objects.new(cam_name, cam_data)
if cam_obj.name not in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.link(cam_obj)

from mathutils import Vector
cam_obj.location = (-26.0, 0.0, 3.2)
aim = Vector((-56.0, 0.0, 6.0))
loc = Vector((-26.0, 0.0, 3.2))
direction = aim - loc
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()
cam_data.lens = 22.0

bpy.context.scene.camera = cam_obj
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_match.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered to:", preview_path)
