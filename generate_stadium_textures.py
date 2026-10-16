import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = r"c:\Users\Legion 3\Documents\PROJECT\animasi\karakter"
ASSETS = os.path.join(ROOT, "Assets")
os.makedirs(ASSETS, exist_ok=True)

# -------------------------------------------------------------------------
# 1. Distinti Stand "C O [Cross] M O" Seat Mosaic Texture
# -------------------------------------------------------------------------
# Stand dimensions: 100m wide x 25m slope.
# Let's create a 2048 x 512 texture.
W, H = 2048, 512
im_seats = Image.new("RGBA", (W, H), (0, 0, 0, 255))
draw = ImageDraw.Draw(im_seats)

# Base: deep royal blue seats (Como Azzurro)
blue_seat = (18, 72, 175, 255)
blue_seat_dark = (12, 52, 135, 255)
white_seat = (245, 248, 252, 255)
white_seat_dark = (200, 205, 215, 255)
red_color = (205, 28, 38, 255)
red_dark = (155, 18, 25, 255)
concrete_grey = (145, 150, 155, 255)
concrete_dark = (115, 120, 125, 255)

# Fill with rows of seats
num_rows = 28
num_cols = 120
row_h = H / num_rows
col_w = W / num_cols

# Create a grid matrix of seat types:
# 0 = Blue, 1 = White, 2 = Red (Cross background), 3 = White (Cross), 4 = Concrete/Stair
grid = np.zeros((num_rows, num_cols), dtype=int)

# Concrete stairways / aisles every ~20 columns and edges
aisles = [4, 26, 48, 70, 92, 114]
for a in aisles:
    grid[:, max(0, a-1):min(num_cols, a+1)] = 4

# Define Letter bitmaps on an 18 rows x 15 cols grid
r_start, r_end = 6, 23

def stamp_letter(start_c, pattern):
    for r_idx, row_str in enumerate(pattern):
        r = r_start + r_idx
        if r >= num_rows:
            break
        for c_idx, ch in enumerate(row_str):
            c = start_c + c_idx
            if c < num_cols:
                if ch == '#':
                    grid[r, c] = 1 # White
                elif ch == '+':
                    grid[r, c] = 3 # White cross
                elif ch == 'R':
                    grid[r, c] = 2 # Red shield

# "C" pattern
c_pattern = [
    "  ###########  ",
    " ############# ",
    "####       ####",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####           ",
    "####       ####",
    " ############# ",
    "  ###########  ",
    "               ",
]

# "O" pattern
o_pattern = [
    "  ###########  ",
    " ############# ",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    " ############# ",
    "  ###########  ",
    "               ",
]

# Como City Cross Shield ("+")
cross_pattern = [
    "RRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "+++++++++++++++",
    "+++++++++++++++",
    "+++++++++++++++",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRR+++RRRRRR",
    "RRRRRRRRRRRRRRR",
    "RRRRRRRRRRRRRRR",
    "               ",
]

# "M" pattern
m_pattern = [
    "####       ####",
    "#####     #####",
    "######   ######",
    "####### #######",
    "#### ##### ####",
    "####  ###  ####",
    "####   #   ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "####       ####",
    "               ",
]

# Stamp letters onto the grid:
stamp_letter(8, c_pattern)
stamp_letter(30, o_pattern)
stamp_letter(52, cross_pattern)
stamp_letter(74, m_pattern)
stamp_letter(96, o_pattern)

# Re-apply aisles so aisles cut cleanly through letters just like in real stadium!
for a in aisles:
    grid[:, max(0, a):min(num_cols, a+1)] = 4

# Now render each seat on im_seats with realistic shadows and backrests
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
            # Yellow hazard line along stair edges
            if c in aisles:
                draw.line([x0+1, y0, x0+1, y1], fill=(220, 190, 40, 255), width=2)
        else:
            if stype == 0:
                base_c, dark_c = blue_seat, blue_seat_dark
            elif stype == 1 or stype == 3:
                base_c, dark_c = white_seat, white_seat_dark
            elif stype == 2:
                base_c, dark_c = red_color, red_dark

            # Concrete step under seat
            draw.rectangle([x0, y0, x1, y1], fill=concrete_dark)
            # Seat cushion & backrest
            sx0 = x0 + 1
            sx1 = x1 - 1
            sy0 = y0 + 2
            sy1 = y1 - 2
            draw.rectangle([sx0, sy0, sx1, sy1], fill=base_c)
            # Backrest shadow / upper highlight
            draw.rectangle([sx0, sy0, sx1, sy0 + int(row_h * 0.35)], fill=dark_c)
            draw.line([sx0, sy0, sx1, sy0], fill=(255, 255, 255, 60), width=1)

# Add central vomitory tunnels at the bottom (entrance arches)
for vomit_c in [18, 59, 90]:
    vx0 = int((vomit_c - 2) * col_w)
    vx1 = int((vomit_c + 3) * col_w)
    vy0 = int((num_rows - 7) * row_h)
    vy1 = H
    draw.rectangle([vx0, vy0, vx1, vy1], fill=(20, 22, 25, 255))
    draw.rectangle([vx0+3, vy0+3, vx1-3, vy1], fill=(10, 10, 12, 255))
    # Safety railing
    draw.line([vx0, vy0, vx1, vy0], fill=(230, 70, 70, 255), width=3)

im_seats_path = os.path.join(ASSETS, "como_distinti_seats.png")
im_seats.save(im_seats_path)
print("Generated:", im_seats_path)

# -------------------------------------------------------------------------
# 2. Checkerboard Banner (Under Distinti Stand)
# -------------------------------------------------------------------------
W_chk, H_chk = 1024, 128
im_chk = Image.new("RGBA", (W_chk, H_chk), (255, 255, 255, 255))
draw_chk = ImageDraw.Draw(im_chk)
chk_size = 32
for y in range(0, H_chk, chk_size):
    for x in range(0, W_chk, chk_size):
        if (x // chk_size + y // chk_size) % 2 == 0:
            draw_chk.rectangle([x, y, x + chk_size, y + chk_size], fill=blue_seat)
        else:
            draw_chk.rectangle([x, y, x + chk_size, y + chk_size], fill=(245, 248, 252, 255))

im_chk_path = os.path.join(ASSETS, "como_checker_banner.png")
im_chk.save(im_chk_path)
print("Generated:", im_chk_path)

# -------------------------------------------------------------------------
# 3. LED Advertising Perimeter Board Texture
# -------------------------------------------------------------------------
W_led, H_led = 2048, 128
im_led = Image.new("RGBA", (W_led, H_led), (10, 14, 24, 255))
draw_led = ImageDraw.Draw(im_led)

# Repeat sponsor sequence: Revolut, COMO 1907, Serie A Enilive, emeren, Banking & Beyond
segments = [
    ("REVOLUT", (255, 255, 255), (15, 18, 28)),
    ("COMO 1907", (255, 255, 255), (14, 65, 155)),
    ("SERIE A enilive", (230, 240, 255), (5, 20, 60)),
    ("emeren", (255, 255, 255), (12, 45, 110)),
    ("BANKING & BEYOND", (255, 230, 80), (20, 25, 35)),
    ("IN NOME DI COMO COMBATTIAMO", (255, 255, 255), (10, 50, 130)),
]

seg_w = W_led // len(segments)
for i, (text, fg, bg) in enumerate(segments):
    x0 = i * seg_w
    x1 = (i + 1) * seg_w
    draw_led.rectangle([x0, 0, x1, H_led], fill=bg)
    draw_led.rectangle([x0, 0, x1, 4], fill=(255, 255, 255, 180))
    draw_led.rectangle([x0, H_led-4, x1, H_led], fill=(255, 255, 255, 180))
    # Draw simple block letters
    draw_led.text((x0 + 25, H_led // 2 - 12), text, fill=fg)

im_led_path = os.path.join(ASSETS, "como_led_boards.png")
im_led.save(im_led_path)
print("Generated:", im_led_path)

# -------------------------------------------------------------------------
# 4. Main Tribuna Seating Texture
# -------------------------------------------------------------------------
W_tr, H_tr = 1024, 512
im_tr = Image.new("RGBA", (W_tr, H_tr), (15, 55, 140, 255))
draw_tr = ImageDraw.Draw(im_tr)
# VIP center section in white and navy
draw_tr.rectangle([W_tr * 0.38, H_tr * 0.15, W_tr * 0.62, H_tr * 0.75], fill=(240, 244, 250, 255))
draw_tr.rectangle([W_tr * 0.42, H_tr * 0.25, W_tr * 0.58, H_tr * 0.65], fill=(10, 30, 80, 255))
# Stairways
for tx in [0.15, 0.36, 0.64, 0.85]:
    x_s = int(W_tr * tx)
    draw_tr.rectangle([x_s - 8, 0, x_s + 8, H_tr], fill=(130, 135, 140, 255))
    draw_tr.line([x_s, 0, x_s, H_tr], fill=(220, 190, 40, 255), width=2)
# Row lines
for r in range(0, H_tr, 18):
    draw_tr.line([0, r, W_tr, r], fill=(0, 0, 0, 90), width=2)

im_tr_path = os.path.join(ASSETS, "como_tribuna_seats.png")
im_tr.save(im_tr_path)
print("Generated:", im_tr_path)

# -------------------------------------------------------------------------
# 5. Curva Bleachers Seating Texture ("19 07" Seat Mosaic)
# -------------------------------------------------------------------------
W_cv, H_cv = 2048, 512
blue_base = (14, 75, 185, 255)
blue_dark = (10, 50, 135, 255)
white_base = (255, 255, 255, 255)
white_dark = (235, 240, 248, 255)
concrete_stair = (140, 145, 150, 255)
hazard_yellow = (235, 205, 30, 255)

num_rows_cv = 22
num_cols_cv = 96
row_h_cv = H_cv / num_rows_cv
col_w_cv = W_cv / num_cols_cv
aisles_cv = [11, 37, 59, 85]

pat_1_cv = [
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

pat_9_cv = [
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

pat_0_cv = [
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

pat_7_cv = [
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

cross_pattern_cv = [
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

def build_curva_texture(include_crest=False, filename="como_curva_seats.png"):
    im = Image.new("RGBA", (W_cv, H_cv), blue_base)
    draw = ImageDraw.Draw(im)
    grid = np.zeros((num_rows_cv, num_cols_cv), dtype=int)

    for a in aisles_cv:
        grid[:, max(0, a-1):min(num_cols_cv, a+1)] = 4

    r_start = 3
    # Left sector (13..36): '1' at 14, '9' at 25
    for r_idx, s in enumerate(pat_1_cv):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 14 + c_idx] = 1

    for r_idx, s in enumerate(pat_9_cv):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 25 + c_idx] = 1

    # Center sector
    if include_crest:
        for r_idx, s in enumerate(cross_pattern_cv):
            for c_idx, ch in enumerate(s):
                if ch == '+': grid[r_start + r_idx, 43 + c_idx] = 1
                elif ch == 'R': grid[r_start + r_idx, 43 + c_idx] = 2

    # Right sector (61..84): '0' at 62, '7' at 74
    for r_idx, s in enumerate(pat_0_cv):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 62 + c_idx] = 1

    for r_idx, s in enumerate(pat_7_cv):
        for c_idx, ch in enumerate(s):
            if ch == '#': grid[r_start + r_idx, 74 + c_idx] = 1

    for a in aisles_cv:
        grid[:, max(0, a-1):min(num_cols_cv, a+1)] = 4

    for r in range(num_rows_cv):
        y0 = int(r * row_h_cv)
        y1 = int((r + 1) * row_h_cv)
        for c in range(num_cols_cv):
            x0 = int(c * col_w_cv)
            x1 = int((c + 1) * col_w_cv)
            stype = grid[r, c]

            if stype == 4:
                draw.rectangle([x0, y0, x1, y1], fill=concrete_stair)
                draw.line([x0, y1-1, x1, y1-1], fill=(100, 105, 110, 255), width=1)
                if c in aisles_cv:
                    draw.line([x0+1, y0, x0+1, y1], fill=hazard_yellow, width=2)
            elif stype == 1:
                draw.rectangle([x0, y0, x1, y1], fill=white_base)
                draw.line([x0, y1-1, x1, y1-1], fill=white_dark, width=1)
            elif stype == 2:
                draw.rectangle([x0, y0, x1, y1], fill=(210, 25, 35, 255))
                draw.line([x0, y1-1, x1, y1-1], fill=(160, 15, 22, 255), width=1)
            else:
                draw.rectangle([x0, y0, x1, y1], fill=blue_base)
                draw.line([x0, y1-1, x1, y1-1], fill=blue_dark, width=1)

    for r in range(num_rows_cv):
        y = int(r * row_h_cv)
        draw.line([0, y, W_cv, y], fill=(0, 0, 0, 70), width=1)

    out_p = os.path.join(ASSETS, filename)
    im.save(out_p)
    print("Generated:", out_p)

build_curva_texture(include_crest=True, filename="como_curva_seats.png")
build_curva_texture(include_crest=False, filename="como_curva_seats_plain_white.png")



