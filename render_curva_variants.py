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

# Improved athletic digits: 14 rows high
pat_1 = [
    "    #####    ",
    "   ######    ",
    "  #######    ",
    " ########    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "    #####    ",
    "#############",
    "#############",
]

pat_9 = [
    "  #########  ",
    " ########### ",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    " ########### ",
    "  ########## ",
    "         ####",
    "         ####",
    "         ####",
    "####     ####",
    " ########### ",
    "  #########  ",
]

pat_0 = [
    "  #########  ",
    " ########### ",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    "####     ####",
    " ########### ",
    "  #########  ",
]

pat_7 = [
    "#############",
    "#############",
    "        #### ",
    "       ####  ",
    "      ####   ",
    "     ####    ",
    "    ####     ",
    "   ####      ",
    "  ####       ",
    "  ####       ",
    "  ####       ",
    "  ####       ",
    "  ####       ",
    "  ####       ",
]

# Como City Cross Shield ("+")
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

def render_curva_texture(filename, mode="four_digits"):
    im = Image.new("RGBA", (W_cv, H_cv), (0, 0, 0, 255))
    draw = ImageDraw.Draw(im)
    grid = np.zeros((num_rows, num_cols), dtype=int)
    
    if mode == "four_digits":
        # 4 evenly spaced digits: 1, 9, 0, 7
        aisles = [5, 26, 47, 48, 69, 90]
        for a in aisles:
            grid[:, max(0, a-1):min(num_cols, a+1)] = 4
        
        r_start = 3
        # 1 at 10, 9 at 31, 0 at 52, 7 at 73
        for r_idx, row_str in enumerate(pat_1):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 10 + c_idx] = 1
        for r_idx, row_str in enumerate(pat_9):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 30 + c_idx] = 1
        for r_idx, row_str in enumerate(pat_0):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 53 + c_idx] = 1
        for r_idx, row_str in enumerate(pat_7):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 73 + c_idx] = 1
        for a in aisles:
            grid[:, max(0, a-1):min(num_cols, a+1)] = 4

    elif mode == "with_crest":
        # "19" on left, City Crest in center, "07" on right
        aisles = [4, 34, 61, 91]
        for a in aisles:
            grid[:, max(0, a-1):min(num_cols, a+1)] = 4
        
        r_start = 3
        # Left sector: 19 (cols 6..32)
        for r_idx, row_str in enumerate(pat_1):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 6 + c_idx] = 1
        for r_idx, row_str in enumerate(pat_9):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 19 + c_idx] = 1
        
        # Center sector: City Crest (cols 41..54)
        for r_idx, row_str in enumerate(cross_pattern):
            for c_idx, ch in enumerate(row_str):
                if ch == '+': grid[r_start + r_idx, 41 + c_idx] = 1
                elif ch == 'R': grid[r_start + r_idx, 41 + c_idx] = 2
        
        # Right sector: 07 (cols 63..89)
        for r_idx, row_str in enumerate(pat_0):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 63 + c_idx] = 1
        for r_idx, row_str in enumerate(pat_7):
            for c_idx, ch in enumerate(row_str):
                if ch == '#': grid[r_start + r_idx, 76 + c_idx] = 1
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

    # Vomitory tunnels at the bottom (entrance arches)
    vomitories = [17, 39, 56, 78] if mode == "four_digits" else [19, 48, 77]
    for vomit_c in vomitories:
        vx0 = int((vomit_c - 2) * col_w)
        vx1 = int((vomit_c + 3) * col_w)
        vy0 = int((num_rows - 4) * row_h)
        vy1 = H_cv
        draw.rectangle([vx0, vy0, vx1, vy1], fill=(20, 22, 25, 255))
        draw.rectangle([vx0+3, vy0+3, vx1-3, vy1], fill=(10, 10, 12, 255))
        draw.line([vx0, vy0, vx1, vy0], fill=(230, 70, 70, 255), width=3)

    out_path = os.path.join(ASSETS, filename)
    im.save(out_path)
    print("Generated:", out_path)

render_curva_texture("curva_1907_four_digits.png", mode="four_digits")
render_curva_texture("curva_1907_with_crest.png", mode="with_crest")
