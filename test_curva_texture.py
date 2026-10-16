import os
import numpy as np
from PIL import Image, ImageDraw

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

W_cv, H_cv = 2048, 512
im_cv = Image.new("RGBA", (W_cv, H_cv), (0, 0, 0, 255))
draw = ImageDraw.Draw(im_cv)

blue_seat = (18, 72, 175, 255)
blue_seat_dark = (12, 52, 135, 255)
white_seat = (245, 248, 252, 255)
white_seat_dark = (200, 205, 215, 255)
concrete_grey = (145, 150, 155, 255)
concrete_dark = (115, 120, 125, 255)

num_rows = 22
num_cols = 96
row_h = H_cv / num_rows
col_w = W_cv / num_cols

# 0 = Blue seat, 1 = White seat, 4 = Concrete stairway
grid = np.zeros((num_rows, num_cols), dtype=int)

# Aisles / stairways
aisles = [6, 26, 47, 48, 69, 89]
for a in aisles:
    grid[:, max(0, a-1):min(num_cols, a+1)] = 4

# Digit definitions (14 rows high, ~12-14 cols wide)
# '1'
pat_1 = [
    "   #####   ",
    "  ######   ",
    " #######   ",
    "########   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "   #####   ",
    "###########",
    "###########",
]

# '9'
pat_9 = [
    " ######### ",
    "###########",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "###########",
    " ##########",
    "       ####",
    "       ####",
    "       ####",
    "####   ####",
    "###########",
    " ######### ",
]

# '0'
pat_0 = [
    " ######### ",
    "###########",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "####   ####",
    "###########",
    " ######### ",
]

# '7'
pat_7 = [
    "###########",
    "###########",
    "      #### ",
    "     ####  ",
    "    ####   ",
    "    ####   ",
    "   ####    ",
    "  ####     ",
    "  ####     ",
    "  ####     ",
    "  ####     ",
    "  ####     ",
    "  ####     ",
    "  ####     ",
]

def stamp_digit(start_c, start_r, pattern):
    for r_idx, row_str in enumerate(pattern):
        r = start_r + r_idx
        if r >= num_rows:
            break
        for c_idx, ch in enumerate(row_str):
            c = start_c + c_idx
            if c < num_cols and ch == '#':
                grid[r, c] = 1

# Place "19" in left sector, "07" in right sector
# Top rows: start at row 4 (out of 22), so rows 4..17
r_start = 4
stamp_digit(11, r_start, pat_1)
stamp_digit(30, r_start, pat_9)
stamp_digit(53, r_start, pat_0)
stamp_digit(73, r_start, pat_7)

# Re-apply aisles so stairways cut cleanly through
for a in aisles:
    grid[:, max(0, a-1):min(num_cols, a+1)] = 4

# Render seats
for r in range(num_rows):
    y0 = int(r * row_h)
    y1 = int((r + 1) * row_h)
    for c in range(num_cols):
        x0 = int(c * col_w)
        x1 = int((c + 1) * col_w)
        stype = grid[r, c]

        if stype == 4:
            # Concrete stairway
            draw.rectangle([x0, y0, x1, y1], fill=concrete_grey)
            draw.line([x0, y1-1, x1, y1-1], fill=concrete_dark, width=1)
            if c in aisles:
                draw.line([x0+1, y0, x0+1, y1], fill=(220, 190, 40, 255), width=2)
        else:
            if stype == 1:
                base_c, dark_c = white_seat, white_seat_dark
            else:
                base_c, dark_c = blue_seat, blue_seat_dark

            # Step base
            draw.rectangle([x0, y0, x1, y1], fill=concrete_dark)
            # Seat cushion
            sx0 = x0 + 1
            sx1 = x1 - 1
            sy0 = y0 + 2
            sy1 = y1 - 2
            draw.rectangle([sx0, sy0, sx1, sy1], fill=base_c)
            # Upper backrest shadow
            draw.rectangle([sx0, sy0, sx1, sy0 + int(row_h * 0.35)], fill=dark_c)
            draw.line([sx0, sy0, sx1, sy0], fill=(255, 255, 255, 60), width=1)

# Add vomitory tunnels at the bottom rows
for vomit_c in [18, 38, 61, 81]:
    vx0 = int((vomit_c - 2) * col_w)
    vx1 = int((vomit_c + 3) * col_w)
    vy0 = int((num_rows - 5) * row_h)
    vy1 = H_cv
    draw.rectangle([vx0, vy0, vx1, vy1], fill=(20, 22, 25, 255))
    draw.rectangle([vx0+3, vy0+3, vx1-3, vy1], fill=(10, 10, 12, 255))
    draw.line([vx0, vy0, vx1, vy0], fill=(230, 70, 70, 255), width=3)

test_path = os.path.join(ASSETS, "test_curva_1907.png")
im_cv.save(test_path)
print("Saved test texture to:", test_path)
