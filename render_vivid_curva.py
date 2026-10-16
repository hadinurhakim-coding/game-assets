import bpy
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
OUTPUT = os.path.join(ROOT, "Output")
BLEND_FILE = os.path.join(OUTPUT, "Stadio_Sinigaglia_Como.blend")

bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

# Add subtle emission link so seats look vivid and bright under any lighting
mat = bpy.data.materials.get("M_Curva_Seats")
nt = mat.node_tree
bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
tex_node = next(n for n in nt.nodes if n.type == 'TEX_IMAGE')

# Connect texture color to emission
if 'Emission Color' in bsdf.inputs:
    nt.links.new(tex_node.outputs['Color'], bsdf.inputs['Emission Color'])
    bsdf.inputs['Emission Strength'].default_value = 0.25

# Check world ambient strength
w_bg = next(n for n in bpy.context.scene.world.node_tree.nodes if n.type == 'BACKGROUND')
w_bg.inputs['Strength'].default_value = 1.6

# Render Pure White view
cam = bpy.data.objects.get("Cam_User_Curva_1907_Match")
bpy.context.scene.camera = cam
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 600

preview_path = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\preview_curva_1907_vivid_white.png"
bpy.context.scene.render.filepath = preview_path
bpy.ops.render.render(write_still=True)
print("Rendered vivid white to:", preview_path)

# Save blend file
bpy.ops.file.pack_all()
bpy.ops.wm.save_mainfile(filepath=BLEND_FILE)
print("Saved blend file successfully!")
