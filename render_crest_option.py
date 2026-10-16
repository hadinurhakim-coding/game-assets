import bpy
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

# Assign crest image
crest_path = os.path.join(ASSETS, "como_curva_seats_punchy_crest.png")
crest_img = bpy.data.images.load(crest_path, check_existing=False)

mat = bpy.data.materials.get("M_Curva_Seats")
for n in mat.node_tree.nodes:
    if n.type == 'TEX_IMAGE':
        n.image = crest_img

cam = bpy.data.objects.get("Cam_User_Curva_1907_Match")
bpy.context.scene.camera = cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_crest_option.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered crest option to:", preview_path)
