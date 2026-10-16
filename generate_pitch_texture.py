import os
import math
from PIL import Image, ImageDraw

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
os.makedirs(ASSETS, exist_ok=True)

# Pitch real dimensions: 105.0m x 68.0m
# Texture resolution: 4096 x 2652 (approx 39.01 pixels per meter -> ~2.56 cm per pixel)
W, H = 4096, 2652
scale_x = W / 105.0
scale_y = H / 68.0

# Colors
dark_green = (12, 58, 16, 255)   # Deep rich emerald
light_green = (22, 92, 28, 255)  # Vibrant cut grass
line_white = (250, 252, 255, 255)
line_shadow = (210, 225, 215, 255)

im = Image.new("RGBA", (W, H), dark_green)
draw = ImageDraw.Draw(im)

# 1. Alternating mowing stripes along length (19 stripes of 5.526m each)
num_stripes = 19
stripe_w = W / num_stripes
for i in range(num_stripes):
    if i % 2 == 1:
        x0 = int(i * stripe_w)
        x1 = int((i + 1) * stripe_w)
        draw.rectangle([x0, 0, x1, H], fill=light_green)

# Line width: 12 cm -> pixels
lw_px = max(4, int(0.12 * scale_x))

def to_px(x_m, y_m):
    # Field center is at (0, 0).
    # x_m in [-52.5, +52.5] -> px in [0, W]
    # y_m in [-34.0, +34.0] -> px in [0, H]
    px = int((x_m + 52.5) * scale_x)
    py = int((y_m + 34.0) * scale_y)
    return px, py

# 2. Touchlines and Goal Lines (Border)
x0, y0 = to_px(-52.5, -34.0)
x1, y1 = to_px( 52.5,  34.0)
# Outer rectangle
draw.rectangle([x0, y0, x1, y1], outline=line_white, width=lw_px)

# 3. Halfway Line
hx, _ = to_px(0.0, 0.0)
draw.line([hx, y0, hx, y1], fill=line_white, width=lw_px)

# 4. Center Circle (radius 9.15m) & Center Spot (radius 0.18m)
cx, cy = to_px(0.0, 0.0)
r_circle_x = int(9.15 * scale_x)
r_circle_y = int(9.15 * scale_y)
draw.ellipse([cx - r_circle_x, cy - r_circle_y, cx + r_circle_x, cy + r_circle_y], outline=line_white, width=lw_px)
r_spot = max(6, int(0.18 * scale_x))
draw.ellipse([cx - r_spot, cy - r_spot, cx + r_spot, cy + r_spot], fill=line_white)

# 5. Penalty Areas (16.5m from goal lines, 40.32m wide)
# Left Penalty Box
lb_x0, lb_y0 = to_px(-52.5, -20.16)
lb_x1, lb_y1 = to_px(-52.5 + 16.5, 20.16)
draw.rectangle([lb_x0, lb_y0, lb_x1, lb_y1], outline=line_white, width=lw_px)

# Right Penalty Box
rb_x0, rb_y0 = to_px(52.5 - 16.5, -20.16)
rb_x1, rb_y1 = to_px(52.5, 20.16)
draw.rectangle([rb_x0, rb_y0, rb_x1, rb_y1], outline=line_white, width=lw_px)

# 6. 6-yard Goal Areas (5.5m from goal lines, 18.32m wide)
lg_x0, lg_y0 = to_px(-52.5, -9.16)
lg_x1, lg_y1 = to_px(-52.5 + 5.5, 9.16)
draw.rectangle([lg_x0, lg_y0, lg_x1, lg_y1], outline=line_white, width=lw_px)

rg_x0, rg_y0 = to_px(52.5 - 5.5, -9.16)
rg_x1, rg_y1 = to_px(52.5, 9.16)
draw.rectangle([rg_x0, rg_y0, rg_x1, rg_y1], outline=line_white, width=lw_px)

# 7. Penalty Spots (11.0m from goal line)
lp_x, lp_y = to_px(-52.5 + 11.0, 0.0)
draw.ellipse([lp_x - r_spot, lp_y - r_spot, lp_x + r_spot, lp_y + r_spot], fill=line_white)

rp_x, rp_y = to_px(52.5 - 11.0, 0.0)
draw.ellipse([rp_x - r_spot, rp_y - r_spot, rp_x + r_spot, rp_y + r_spot], fill=line_white)

# 8. Penalty Arcs ("D") - radius 9.15m from penalty spot, outside penalty box
arc_deg = math.degrees(math.acos(5.5 / 9.15))
# Left penalty arc
draw.arc([lp_x - r_circle_x, lp_y - r_circle_y, lp_x + r_circle_x, lp_y + r_circle_y],
         start=-arc_deg, end=arc_deg, fill=line_white, width=lw_px)
# Right penalty arc
draw.arc([rp_x - r_circle_x, rp_y - r_circle_y, rp_x + r_circle_x, rp_y + r_circle_y],
         start=180 - arc_deg, end=180 + arc_deg, fill=line_white, width=lw_px)

# 9. Corner Arcs (radius 1.0m at 4 corners)
r_cor_x = int(1.0 * scale_x)
r_cor_y = int(1.0 * scale_y)
# Top-Left
draw.arc([x0 - r_cor_x, y0 - r_cor_y, x0 + r_cor_x, y0 + r_cor_y], start=0, end=90, fill=line_white, width=lw_px)
# Bottom-Left
draw.arc([x0 - r_cor_x, y1 - r_cor_y, x0 + r_cor_x, y1 + r_cor_y], start=270, end=360, fill=line_white, width=lw_px)
# Top-Right
draw.arc([x1 - r_cor_x, y0 - r_cor_y, x1 + r_cor_x, y0 + r_cor_y], start=90, end=180, fill=line_white, width=lw_px)
# Bottom-Right
draw.arc([x1 - r_cor_x, y1 - r_cor_y, x1 + r_cor_x, y1 + r_cor_y], start=180, end=270, fill=line_white, width=lw_px)

out_tex = os.path.join(ASSETS, "como_pitch_full_texture.png")
im.save(out_tex, "PNG")
print("SUCCESS: Generated 4K seamless pitch texture:", out_tex)
