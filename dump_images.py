import bpy

for img in bpy.data.images:
    print("Image:", img.name, img.size[:], img.filepath, "packed:", img.packed_file is not None)
    if "curva" in img.name.lower():
        out_p = r"C:\Users\Legion 3\.gemini\antigravity\brain\458fb468-ae24-4eba-9b53-5c7466555733\dump_" + img.name + ".png"
        try:
            img.save_render(out_p)
            print("Dumped:", out_p)
        except Exception as e:
            print("Failed to save:", e)
