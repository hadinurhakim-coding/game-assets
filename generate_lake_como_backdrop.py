from PIL import Image, ImageDraw, ImageFilter
import math
import os

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

# Generate 4096 x 1024 Seamless 360-Degree Panoramic Lake Como Environment Backdrop
# Specifically calibrated so that when wrapped around a 360-degree cylinder,
# the calm, deep slate-blue waters of Lake Como and Alpine shoreline are seamless from any viewpoint.
W, H = 4096, 1024
im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(im)

# 1. Sky Gradient (Top Italian Alpine azure fading to soft horizon haze)
# Pure horizontal gradient -> 100% horizontally seamless!
sky_limit_y = int(H * 0.40)
for y in range(sky_limit_y + 1):
    fy = y / sky_limit_y
    # Smooth atmospheric gradient: (120, 165, 215) -> (195, 215, 235)
    r = int(120 + (195 - 120) * (fy ** 1.1))
    g = int(165 + (215 - 165) * (fy ** 1.1))
    b = int(215 + (235 - 215) * (fy ** 1.1))
    draw.line([0, y, W, y], fill=(r, g, b, 255))

# 2. Distant Alpine Shoreline Mountains across Lake Como
# Integer harmonics ensure seamless 360 wrapping (f(0) == f(1))
horiz_y = int(H * 0.38)

# Far mountain ridge (soft bluish-grey haze, high Alpine peaks)
far_ridge = []
for x in range(W + 1):
    nx = x / W
    m_h = (
        0.16 * math.sin(2.0 * math.pi * nx * 2.0 + 0.4) +
        0.07 * math.sin(2.0 * math.pi * nx * 4.0 + 1.1) +
        0.03 * math.sin(2.0 * math.pi * nx * 8.0)
    )
    my = horiz_y - int((0.18 + m_h) * H)
    far_ridge.append((x, my))

far_poly = [(0, horiz_y)] + far_ridge + [(W, horiz_y)]
draw.polygon(far_poly, fill=(155, 180, 205, 255))

# Mid mountain ridge (Lake Como forested slopes with subtle aerial perspective)
mid_ridge = []
for x in range(W + 1):
    nx = x / W
    m_h = (
        0.11 * math.sin(2.0 * math.pi * nx * 3.0 + 1.8) +
        0.05 * math.sin(2.0 * math.pi * nx * 6.0 + 0.6) +
        0.02 * math.sin(2.0 * math.pi * nx * 12.0)
    )
    my = horiz_y - int((0.10 + m_h) * H)
    mid_ridge.append((x, my))

mid_poly = [(0, horiz_y)] + mid_ridge + [(W, horiz_y)]
draw.polygon(mid_poly, fill=(108, 138, 166, 255))

# Near shoreline hills (richer slate-green-blue reflecting on water)
near_ridge = []
for x in range(W + 1):
    nx = x / W
    m_h = (
        0.06 * math.sin(2.0 * math.pi * nx * 4.0 + 1.2) +
        0.03 * math.sin(2.0 * math.pi * nx * 8.0 + 2.2)
    )
    my = horiz_y - int((0.04 + m_h) * H)
    near_ridge.append((x, my))

near_poly = [(0, horiz_y)] + near_ridge + [(W, horiz_y)]
draw.polygon(near_poly, fill=(75, 105, 132, 255))

# Atmospheric haze line right above the water line
for y in range(horiz_y - 8, horiz_y + 4):
    alpha = int(90 * (1.0 - abs(y - horiz_y) / 8.0))
    draw.line([0, y, W, y], fill=(185, 205, 225, alpha))

# Tiny Italian lakeside villas & docks along the far shore
for vx in range(30, W - 30, 95):
    vy = horiz_y - 6
    # Clusters of warm white/terracotta villa lights & facades
    draw.rectangle([vx, vy, vx + 14, vy + 5], fill=(215, 205, 190, 200))
    draw.rectangle([vx + 20, vy - 3, vx + 30, vy + 4], fill=(230, 220, 205, 230))
    draw.rectangle([vx + 40, vy - 2, vx + 48, vy + 5], fill=(195, 115, 95, 210))

# 3. Lake Como Water Surface (Lower 62% of image: vast, calm, slate-blue lake)
water_start_y = horiz_y
for y in range(water_start_y, H):
    fy = (y - water_start_y) / (H - water_start_y)
    # Slate-blue Alpine lake water gradient:
    # Near horizon: soft slate-cyan (72, 98, 122)
    # Mid lake: deep Lake Como blue (42, 70, 98)
    # Foreground: deep calm water (24, 48, 76)
    r = int(76 - (76 - 22) * (fy ** 0.85))
    g = int(102 - (102 - 50) * (fy ** 0.85))
    b = int(128 - (128 - 84) * (fy ** 0.85))
    draw.line([0, y, W, y], fill=(r, g, b, 255))

# Fine horizontal water ripples (soft wavelets and specular sheen)
for y in range(water_start_y + 3, H, 4):
    fy = (y - water_start_y) / (H - water_start_y)
    alpha = int(48 * (1.0 - 0.45 * fy))
    ripple_color = (180, 210, 235, alpha)
    step = max(6, int(26 * (1.0 - 0.7 * fy)))
    for rx in range(0, W, step * 2):
        r_len = int(step * 1.5)
        draw.line([rx, y, rx + r_len, y], fill=ripple_color, width=1)

# Subtle blur for smooth photographic realism
im = im.filter(ImageFilter.GaussianBlur(radius=0.7))

out_path = os.path.join(ASSETS, "lake_como_panorama_backdrop.png")
im.save(out_path)
print("Saved 360-degree seamless Lake Como panorama backdrop to:", out_path)
