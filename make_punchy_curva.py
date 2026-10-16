import os
import numpy as np
from PIL import Image, ImageDraw

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")

W_cv, H_cv = 2048, 512
# High-contrast stadium seat colors (Como Azzurro & Brilliant White)
blue_base = (14, 75, 185, 255)
blue_dark = (10, 50, 135, 255)
white_base = (255, 255, 255, 255)
white_dark = (235, 240, 248, 255)
concrete_stair = (140, 145, 150, 255)
hazard_yellow = (235, 205, 30, 255)

num_rows = 22
num_cols = 96
row_h = H_cv / num_rows
col_w = W_cv / num_cols

# Aisles: 11, 37, 59, 85
aisles = [11, 37, 59, 85]

# Punchy, bold, wide block digits: 14 rows high
# Digit '1' (width 9)
pat_1 = [
    "  #####  ",
    " ####### ",
    "######## ",
    "#########",
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
    "###########",
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
    "      #####",
    "     ##### ",
    "    #####  ",
    "   #####   ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
    "  #####    ",
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

def make_punchy_curva(include_crest=False, out_name="como_curva_seats.png"):
    im = Image.new("RGBA", (W_cv, H_cv), blue_base)
    draw = ImageDraw.Draw(im)
    grid = np.zeros((num_rows, num_cols), dtype=int)

    # Aisles (2 columns each)
    for a in aisles:
        grid[:, max(0, a-1):min(num_cols, a+1)] = 4

    r_start = 3

    # Left sector (13..36): '1' at 14, '9' at 25
    for r_idx, s in enumerate(pat_1):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 14 + c_idx] = 1

    for r_idx, s in enumerate(pat_9):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 25 + c_idx] = 1

    # Center sector
    if include_crest:
        for r_idx, s in enumerate(cross_pattern):
            for c_idx, ch in enumerate(s):
                if ch == '+': grid[r_start + r_idx, 43 + c_idx] = 1
                elif ch == 'R': grid[r_start + r_idx, 43 + c_idx] = 2

    # Right sector (61..84): '0' at 62, '7' at 74
    for r_idx, s in enumerate(pat_0):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 62 + c_idx] = 1

    for r_idx, s in enumerate(pat_7):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 74 + c_idx] = 1

    # Reapply aisles
    for a in aisles:
        grid[:, max(0, a-1):min(num_cols, a+1)] = 4

    # Render seats with MAXIMUM PUNCH & CONTRAST
    for r in range(num_rows):
        y0 = int(r * row_h)
        y1 = int((r + 1) * row_h)
        for c in range(num_cols):
            x0 = int(c * col_w)
            x1 = int((c + 1) * col_w)
            stype = grid[r, c]

            if stype == 4:
                # Concrete stairway with yellow hazard lines
                draw.rectangle([x0, y0, x1, y1], fill=concrete_stair)
                draw.line([x0, y1-1, x1, y1-1], fill=(100, 105, 110, 255), width=1)
                if c in aisles:
                    draw.line([x0+1, y0, x0+1, y1], fill=hazard_yellow, width=2)
            elif stype == 1:
                # SOLID BRIGHT WHITE SEAT (NO dark borders to prevent distance blurring!)
                draw.rectangle([x0, y0, x1, y1], fill=white_base)
                # Subtle seat edge shadow
                draw.line([x0, y1-1, x1, y1-1], fill=white_dark, width=1)
            elif stype == 2:
                # City Red Shield
                draw.rectangle([x0, y0, x1, y1], fill=(210, 25, 35, 255))
                draw.line([x0, y1-1, x1, y1-1], fill=(160, 15, 22, 255), width=1)
            else:
                # Royal Como Blue Seat
                draw.rectangle([x0, y0, x1, y1], fill=blue_base)
                draw.line([x0, y1-1, x1, y1-1], fill=blue_dark, width=1)

    # Clean horizontal tier lines across all columns
    for r in range(num_rows):
        y = int(r * row_h)
        draw.line([0, y, W_cv, y], fill=(0, 0, 0, 70), width=1)

    out_p = os.path.join(ASSETS, out_name)
    im.save(out_p)
    print("Saved punchy texture:", out_p)

make_punchy_curva(include_crest=False, out_name="como_curva_seats_punchy_white.png")
make_punchy_curva(include_crest=True, out_name="como_curva_seats_punchy_crest.png")
# Overwrite main
make_punchy_curva(include_crest=False, out_name="como_curva_seats.png")
