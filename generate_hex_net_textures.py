import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

W, H = 2048, 2048

# Tiling parameters for regular hexagon grid
# We want N_x cells across W, N_y cells across H.
# Let's choose N_x = 16, N_y = 10 (or similar) with exact periodicity on [W, H]
# Center spacing:
# Row 0: x = 0, dx, 2dx, ...
# Row 1: x = dx/2, dx/2 + dx, ...
# To close periodically:
# Horizontal period: dx = W / N_x
# Vertical period: 2 * dy = H / (N_y / 2) -> dy = H / N_y
# Each hexagon has 6 vertices:
# In pointy-top hexagon:
# top vertex: (0, -R)
# top-right: (dx/2, -R/2)
# bot-right: (dx/2, R/2)
# bot vertex: (0, R)
# bot-left: (-dx/2, R/2)
# top-left: (-dx/2, -R/2)
# where R = dy * (2/3), and dx is the horizontal width.

N_x = 16
N_y = 18 # Must be even so row parity wraps seamlessly!

dx = W / N_x
dy = H / N_y
R = dy * (2.0 / 3.0)

# Create high-res canvas with transparent background
im_net = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw = ImageDraw.Draw(im_net)

rope_color = (245, 246, 248, 255) # Brilliant natural synthetic nylon
rope_highlight = (255, 255, 255, 255)
rope_shadow = (175, 178, 182, 255)
cord_radius = 14 # Solid 28-pixel thick tubular cords with knot joints


# Collect all unique edges with periodic wrap
edges = set()

for j in range(N_y):
    y_c = j * dy
    x_offset = (dx / 2.0) if (j % 2 == 1) else 0.0
    for i in range(N_x):
        x_c = i * dx + x_offset
        
        # 6 vertices of this cell
        v0 = (x_c, y_c - R)
        v1 = (x_c + dx/2.0, y_c - R/2.0)
        v2 = (x_c + dx/2.0, y_c + R/2.0)
        v3 = (x_c, y_c + R)
        v4 = (x_c - dx/2.0, y_c + R/2.0)
        v5 = (x_c - dx/2.0, y_c - R/2.0)
        
        cell_edges = [(v0, v1), (v1, v2), (v2, v3), (v3, v4), (v4, v5), (v5, v0)]
        for pA, pB in cell_edges:
            # Sort endpoints to avoid duplicate drawing
            xA, yA = pA
            xB, yB = pB
            edge_key = tuple(sorted([(round(xA, 2), round(yA, 2)), (round(xB, 2), round(yB, 2))]))
            edges.add((pA, pB))

print(f"Total hexagon edge segments: {len(edges)}")

# Function to draw wrapped segment
def draw_wrapped_line(pA, pB, width, color):
    xA, yA = pA
    xB, yB = pB
    for ox in [-W, 0, W]:
        for oy in [-H, 0, H]:
            draw.line([(xA + ox, yA + oy), (xB + ox, yB + oy)], fill=color, width=width)
            # Rounded endcaps / knot joints
            draw.ellipse([(xA + ox - width//2, yA + oy - width//2), 
                          (xA + ox + width//2, yA + oy + width//2)], fill=color)

# Draw base thick cord
for pA, pB in edges:
    draw_wrapped_line(pA, pB, width=cord_radius*2, color=rope_shadow)

for pA, pB in edges:
    draw_wrapped_line(pA, pB, width=cord_radius*2 - 3, color=rope_color)

# Draw top fiber highlight line
for pA, pB in edges:
    draw_wrapped_line(pA, pB, width=cord_radius, color=rope_highlight)

# Save Color & Alpha Net texture
out_color = os.path.join(ASSETS, "como_hex_net_color.png")
im_net.save(out_color)
print("Saved hex net color texture to:", out_color)

# Generate Normal Map from Alpha/Height
alpha = np.array(im_net.split()[3], dtype=float) / 255.0
# Compute gradients using numpy
gy, gx = np.gradient(alpha)

scale = 12.0 # Normal intensity
norm_x = -gx * scale
norm_y = -gy * scale
norm_z = np.ones_like(alpha)
mag = np.sqrt(norm_x**2 + norm_y**2 + norm_z**2)
norm_x /= mag
norm_y /= mag
norm_z /= mag

r = ((norm_x * 0.5 + 0.5) * 255).astype(np.uint8)
g = ((norm_y * 0.5 + 0.5) * 255).astype(np.uint8)
b = ((norm_z * 0.5 + 0.5) * 255).astype(np.uint8)
a = (alpha * 255).astype(np.uint8)

im_norm = Image.fromarray(np.stack([r, g, b, a], axis=-1), mode="RGBA")
out_norm = os.path.join(ASSETS, "como_hex_net_normal.png")
im_norm.save(out_norm)
print("Saved hex net normal map to:", out_norm)

# Generate AO map (contact shadow inside intersections)
ao = (1.0 - (np.abs(gx) + np.abs(gy)) * 4.0).clip(0.4, 1.0)
ao_arr = (ao * 255).astype(np.uint8)
im_ao = Image.fromarray(np.stack([ao_arr, ao_arr, ao_arr, a], axis=-1), mode="RGBA")
out_ao = os.path.join(ASSETS, "como_hex_net_ao.png")
im_ao.save(out_ao)
print("Saved hex net AO map to:", out_ao)
