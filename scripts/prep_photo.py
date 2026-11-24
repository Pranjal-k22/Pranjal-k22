"""
Prepare a portrait photo for the README:
  1. Cut out the subject (rembg with u2net) to isolate foreground from background
  2. Crop to tight bounding box and resize for high-DPI display
  3. Save transparent PNG to cards/portrait.png (consumed by render_readme_cards.py)
  4. Optionally composite onto white with CLAHE if generating source-prepped.png for ASCII.

Usage:
    python scripts/prep_photo.py                   # creates cards/portrait.png from candidate images
    python scripts/prep_photo.py [input] [output]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

HERE = os.path.dirname(os.path.abspath(__file__))

def find_input_file(arg_path=None):
    if arg_path and not arg_path.startswith("-"):
        return arg_path
    for candidate in ["img4.png", "img4.jpg", "img2.png", "img2.jpg", "img-new.jpg", "img-new.png", "source-img.png", "source-img.jpg", "source-photo.jpg", "source-photo.png", "source-photo.jpeg"]:
        p = os.path.join(HERE, "..", candidate)
        if os.path.isfile(p):
            return p
    return os.path.join(HERE, "..", "source-photo.jpg")

INP = find_input_file(sys.argv[1] if len(sys.argv) > 1 else None)
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "cards", "portrait.png")

if not os.path.exists(INP):
    print(f"Error: source photo not found at '{INP}'. Please place img2.png or source-photo.jpg in the repo root.", file=sys.stderr)
    sys.exit(1)

print(f"Processing '{INP}' -> '{OUT}'...")

if os.path.basename(INP).startswith("img4"):
    # Direct illustration mode: preserve original artwork intact (no rembg/cropping)
    raw = Image.open(INP)
    target_h = 770
    target_w = int(raw.width * (target_h / raw.height))
    resized = raw.resize((target_w, target_h), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    resized.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} directly from illustration ({resized.size[0]}x{resized.size[1]}, {os.path.getsize(OUT)} bytes)")
    sys.exit(0)

# 1. cut out the subject
session = new_session("u2net")
cut = remove(Image.open(INP).convert("RGBA"), session=session)
alpha = np.array(cut.split()[-1])                 # 0 = background

# Determine output mode
if OUT.endswith("source-prepped.png"):
    # ASCII prep mode: CLAHE contrast boost on grayscale, composite on white
    rgb = np.array(cut.convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)
    mask = (alpha.astype(np.float32) / 255.0)
    mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
    out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
    out = np.clip(out, 0, 255).astype(np.uint8)
    Image.fromarray(out, mode="L").save(OUT)
    print("wrote", OUT, out.shape)
else:
    # Transparent PNG cutout mode for hero card
    rows = np.where(np.any(alpha > 20, axis=1))[0]
    cols = np.where(np.any(alpha > 20, axis=0))[0]
    ymin, ymax = max(0, rows[0] - 10), min(cut.height, rows[-1] + 10)
    xmin, xmax = max(0, cols[0] - 10), min(cut.width, cols[-1] + 10)
    cropped = cut.crop((xmin, ymin, xmax, ymax))

    # Resize to high-DPI display size (height 720px)
    target_h = 720
    target_w = int(cropped.width * (target_h / cropped.height))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    resized.save(OUT, "PNG", optimize=True)
    print(f"wrote {OUT} ({resized.size[0]}x{resized.size[1]}, {os.path.getsize(OUT)} bytes)")
