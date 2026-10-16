import os
import numpy as np
from PIL import Image, ImageDraw

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

W_cv, H_cv = 2048, 512
blue_seat = (18, 72, 175, 255)
blue_seat_dark = (12, 52, 135, 255)
white_seat = (245, 248, 252, 255)
white_seat_dark = (200, 205, 215, 255)
red_color = (205, 28, 38, 255)
red_dark = (155, 18, 25, 255)
concrete_grey = (145, 150, 155, 255)
concrete_dark = (115, 120, 125, 255)

num_rows = 22
num_cols = 96
row_h = H_cv / num_rows
col_w = W_cv / num_cols

# Aisles exactly matching the 3-sector division: 0.12, 0.38, 0.62, 0.88
# In 96 columns: 11, 37, 59, 85
aisles = [11, 37, 59, 85]

# Digit patterns: 14 rows high
# Digit '1' (width 9)
pat_1 = [
    "  ####   ",
    " ######  ",
    "#######  ",
    "######## ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "  #####  ",
    "#########",
    "#########",
]

# Digit '9' (width 11)
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

# Digit '0' (width 11)
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

# Digit '7' (width 11)
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

# Como City Cross Shield ("+") (width 13)
cross_pattern = [
    "RRRRRRRRRRRRR",
    "RRRRRRRRRRRRR",
    "RRRRR+++RRRRR",
    "RRRRR+++RRRRR",
    "RRRRR+++RRRRR",
    "+++++++++++++",
    "+++++++++++++",
    "+++++++++++++",
    "RRRRR+++RRRRR",
    "RRRRR+++RRRRR",
    "RRRRR+++RRRRR",
    "RRRRRRRRRRRRR",
    " RRRRRRRRRRR ",
    "  RRRRRRRRR  ",
]

def generate_curva_texture(include_crest=True, output_filename="como_curva_seats.png"):
    im = Image.new("RGBA", (W_cv, H_cv), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    grid = np.zeros((num_rows, num_cols), dtype=int)

    # Aisles (width 2 columns each)
    for a in aisles:
        grid[:, max(0, a-1):min(num_cols, a+1)] = 4

    # Top padding: 3 rows, letters are 14 rows, bottom padding: 5 rows
    r_start = 3

    # Left sector (cols 13..36): '1' at col 14, '9' at col 25
    for r_idx, row_str in enumerate(pat_1):
        for c_idx, ch in enumerate(row_str):
            if ch == '#': grid[r_start + r_idx, 14 + c_idx] = 1

    for r_idx, row_str in enumerate(pat_9):
        for c_idx, ch in enumerate(row_str):
            if ch == '#': grid[r_start + r_idx, 25 + c_idx] = 1

    # Center sector (cols 38..58):
    if include_crest:
        for r_idx, row_str in enumerate(cross_pattern):
            for c_idx, ch in enumerate(row_str):
                if ch == '+': grid[r_start + r_idx, 43 + c_idx] = 1
                elif ch == 'R': grid[r_start + r_idx, 43 + c_idx] = 2

    # Right sector (cols 61..84): '0' at col 62, '7' at col 74
    for r_idx, row_str in enumerate(pat_0):
        for c_idx, ch in enumerate(row_str):
            if ch == '#': grid[r_start + r_idx, 62 + c_idx] = 1

    for r_idx, row_str in enumerate(pat_7):
        for c_idx, ch in enumerate(row_str):
            if ch == '#': grid[r_start + r_idx, 74 + c_idx] = 1

    # Re-apply aisles so concrete stairways cut cleanly through
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
                elif stype == 2:
                    base_c, dark_c = red_color, red_dark
                else:
                    base_c, dark_c = blue_seat, blue_seat_dark

                draw.rectangle([x0, y0, x1, y1], fill=concrete_dark)
                sx0, sx1 = x0 + 1, x1 - 1
                sy0, sy1 = y0 + 2, y1 - 2
                draw.rectangle([sx0, sy0, sx1, sy1], fill=base_c)
                draw.rectangle([sx0, sy0, sx1, sy0 + int(row_h * 0.35)], fill=dark_c)
                draw.line([sx0, sy0, sx1, sy0], fill=(255, 255, 255, 60), width=1)

    # Vomitory tunnels at the bottom rows (spaced nicely under the sectors)
    for vomit_c in [24, 49, 73]:
        vx0 = int((vomit_c - 2) * col_w)
        vx1 = int((vomit_c + 3) * col_w)
        vy0 = int((num_rows - 4) * row_h)
        vy1 = H_cv
        draw.rectangle([vx0, vy0, vx1, vy1], fill=(20, 22, 25, 255))
        draw.rectangle([vx0+3, vy0+3, vx1-3, vy1], fill=(10, 10, 12, 255))
        draw.line([vx0, vy0, vx1, vy0], fill=(230, 70, 70, 255), width=3)

    out_p = os.path.join(ASSETS, output_filename)
    im.save(out_p)
    print("Saved:", out_p)

# Generate both versions
generate_curva_texture(include_crest=True, output_filename="como_curva_seats_with_crest.png")
generate_curva_texture(include_crest=False, output_filename="como_curva_seats_pure_white.png")
# Overwrite main como_curva_seats.png with the official crest version!
generate_curva_texture(include_crest=True, output_filename="como_curva_seats.png")
