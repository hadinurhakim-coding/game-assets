from PIL import Image, ImageDraw
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

W, H = 2048, 512
im = Image.new("RGBA", (W, H), (145, 148, 152, 255))
draw = ImageDraw.Draw(im)

num_rows = 16
row_h = H / num_rows
num_cols = 128
col_w = W / num_cols

# 4 equal bays of seats separated by 3 internal aisles and 2 border aisles
aisle_u_positions = [0.015, 0.25, 0.50, 0.75, 0.985]
aisle_col_indices = [int(u * num_cols) for u in aisle_u_positions]

# Colors
concrete_grey = (150, 155, 160, 255)
concrete_dark = (110, 114, 118, 255)
blue_seat = (28, 88, 175, 255)        # Como blue seats
blue_seat_dark = (18, 62, 128, 255)
terrace_light = (195, 200, 205, 255)  # Weathered terrace concrete
yellow_hazard = (230, 200, 30, 255)   # Safety stair line

for r in range(num_rows):
    y0 = int(r * row_h)
    y1 = int((r + 1) * row_h)
    
    # Tread concrete
    draw.rectangle([0, y0, W, y1], fill=terrace_light)
    # Riser shadow line
    draw.line([0, y0, W, y0], fill=concrete_dark, width=2)
    draw.line([0, y0+1, W, y0+1], fill=(40, 42, 45, 180), width=1)
    
    for c in range(num_cols):
        x0 = int(c * col_w)
        x1 = int((c + 1) * col_w)
        
        # Check if this column is an aisle
        is_aisle = any(abs(c - ac) <= 1 for ac in aisle_col_indices)
        
        if is_aisle:
            # Concrete stairway step
            draw.rectangle([x0, y0, x1, y1], fill=concrete_grey)
            draw.line([x0, y0, x1, y0], fill=concrete_dark, width=2)
            # Yellow hazard line along stair riser
            draw.line([x0+2, y0+2, x1-2, y0+2], fill=yellow_hazard, width=2)
        else:
            # Seat on the step
            sx0 = x0 + 2
            sx1 = x1 - 2
            sy0 = y0 + int(row_h * 0.22)
            sy1 = y1 - int(row_h * 0.12)
            
            # Blue bucket seats on lower tiers, weathered concrete terrace benches on top tiers
            if r < 12:
                # Blue bucket seats
                draw.rectangle([sx0, sy0, sx1, sy1], fill=blue_seat)
                # Seat backrest shadow
                draw.rectangle([sx0, sy0, sx1, sy0 + int(row_h * 0.28)], fill=blue_seat_dark)
                # Seat highlight
                draw.line([sx0+1, sy0+1, sx1-1, sy0+1], fill=(255, 255, 255, 80), width=1)
            else:
                # Upper weathered concrete terrace benches
                draw.rectangle([sx0, sy0, sx1, sy1], fill=(175, 180, 186, 255))
                draw.line([sx0, sy0, sx1, sy0], fill=(120, 125, 130, 255), width=2)

tex_path = os.path.join(ASSETS, "como_curva_nord_curved_seats.png")
im.save(tex_path)
print("Generated 4-bay curved stand texture:", tex_path)
