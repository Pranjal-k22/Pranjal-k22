"""
Prepare a portrait photo for clean ASCII conversion:
  1. remove the background (rembg) so the subject is isolated
  2. boost LOCAL contrast (CLAHE) so a flatly-lit face gains highlights and
     shadows -- this is what turns a dark blob into a recognizable face
  3. composite the subject onto pure white so the background reads as blank
     (white -> spaces in the ascii ramp)

Output: source-prepped.png (grayscale), consumed by make_ascii_svg.py.
Run once whenever the source photo changes; the ascii SVG itself is static.

    python scripts/prep_photo.py [input.jpg] [output.png]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove

HERE = os.path.dirname(os.path.abspath(__file__))

def find_input_file(arg_path=None):
    if arg_path:
        return arg_path
    for candidate in ["img2.png", "img2.jpg", "img-new.jpg", "img-new.png", "source-img.png", "source-img.jpg", "source-photo.jpg", "source-photo.png", "source-photo.jpeg"]:
        p = os.path.join(HERE, "..", candidate)
        if os.path.isfile(p):
            return p
    return os.path.join(HERE, "..", "source-photo.jpg")

INP = find_input_file(sys.argv[1] if len(sys.argv) > 1 else None)
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

if not os.path.exists(INP):
    print(f"Error: source photo not found at '{INP}'. Please place source-photo.jpg in the repo root.", file=sys.stderr)
    sys.exit(1)

print(f"Processing '{INP}' -> '{OUT}'...")

# 1. cut out the subject
session = new_session("u2net")
cut = remove(Image.open(INP).convert("RGBA"), session=session)
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])                 # 0 = background

# 2. local-contrast the luminance (CLAHE)
gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
clahe = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8))
gray = clahe.apply(gray)

# a touch of global lift so the face sits in the sparse end of the ramp
gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

# 3. paste onto white using the alpha mask (feathered a hair to avoid a halo)
mask = (alpha.astype(np.float32) / 255.0)
mask = cv2.GaussianBlur(mask, (0, 0), 1.0)
out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape)
