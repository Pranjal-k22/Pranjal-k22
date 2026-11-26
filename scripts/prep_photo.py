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

from PIL import Image
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

try:
    from rembg import new_session, remove
except ImportError:
    new_session = None
    remove = None

HERE = os.path.dirname(os.path.abspath(__file__))

def find_input_file(arg_path=None):
    if arg_path and not arg_path.startswith("-"):
        return arg_path
    for candidate in ["img1.png", "img1.jpg", "img4.png", "img4.jpg", "img2.png", "img2.jpg", "img-new.jpg", "img-new.png", "source-img.png", "source-img.jpg", "source-photo.jpg", "source-photo.png", "source-photo.jpeg"]:
        p = os.path.join(HERE, "..", candidate)
        if os.path.isfile(p):
            return p
    return os.path.join(HERE, "..", "source-photo.jpg")

INP = find_input_file(sys.argv[1] if len(sys.argv) > 1 else None)
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "cards", "portrait.png")

if not os.path.exists(INP):
    print(f"Error: source photo not found at '{INP}'. Please place img1.png or img4.png in the repo root.", file=sys.stderr)
    sys.exit(1)

print(f"Processing '{INP}' -> '{OUT}'...")

if os.path.basename(INP).startswith("img1"):
    # Panoramic landscape mode: zoom to fit full vertical height (face to toe complete)
    # in 880x420 aspect ratio (1760x840 for 2x retina) with smooth left feather
    raw = Image.open(INP).convert("L")
    canvas_w, canvas_h = 1760, 840
    PAPER_GRAY = 243

    # Scale to match canvas height exactly (zero vertical cropping: full face to toe visible)
    scale = canvas_h / raw.height
    w_img = int(raw.width * scale)
    h_img = canvas_h

    resized = raw.resize((w_img, h_img), Image.Resampling.LANCZOS)
    try:
        import numpy as np
        arr_img = np.array(resized, dtype=np.float32)
        fade_w = min(220, w_img // 4)
        ramp = np.linspace(0.0, 1.0, fade_w)[None, :]
        arr_img[:, :fade_w] = (1.0 - ramp) * PAPER_GRAY + ramp * arr_img[:, :fade_w]
        canvas_arr = np.full((canvas_h, canvas_w), PAPER_GRAY, dtype=np.uint8)
        x_start = max(0, canvas_w - w_img)
        canvas_arr[:, x_start:] = np.clip(arr_img, 0, 255).astype(np.uint8)
        banner = Image.fromarray(canvas_arr)
    except Exception:
        canvas_img = Image.new("L", (canvas_w, canvas_h), PAPER_GRAY)
        x_start = max(0, canvas_w - w_img)
        canvas_img.paste(resized, (x_start, 0))
        banner = canvas_img

    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    banner.save(OUT, "PNG", optimize=True)
    print(f"wrote panoramic banner to {OUT} ({banner.size[0]}x{banner.size[1]}, {os.path.getsize(OUT)} bytes)")
    sys.exit(0)

if os.path.basename(INP).startswith("img4"):
    # Precise transparent PNG mode: floodfill outer background so complete person on the rock is kept
    raw = Image.open(INP).convert("RGB")
    arr = np.array(raw)
    h_img, w_img, _ = arr.shape
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    is_white = (gray >= 248).astype(np.uint8)
    flood = is_white.copy()
    mask = np.zeros((h_img + 2, w_img + 2), np.uint8)

    for x in range(0, w_img):
        if flood[0, x] == 1:
            cv2.floodFill(flood, mask, (x, 0), 2)
    for y in range(0, h_img):
        if flood[y, 0] == 1:
            cv2.floodFill(flood, mask, (0, y), 2)
        if flood[y, w_img - 1] == 1:
            cv2.floodFill(flood, mask, (w_img - 1, y), 2)

    outer_bg = (flood == 2)
    alpha = np.where(outer_bg, 0, 255).astype(np.uint8)

    # Edge anti-aliasing feather
    dist_bg = cv2.distanceTransform(outer_bg.astype(np.uint8), cv2.DIST_L2, 3)
    dist_fg = cv2.distanceTransform((~outer_bg).astype(np.uint8), cv2.DIST_L2, 3)
    edge_zone = (dist_bg < 2.0) & (dist_fg < 2.0)
    for y_idx, x_idx in zip(*np.where(edge_zone)):
        brightness = gray[y_idx, x_idx]
        if brightness > 230:
            fade = max(0.0, min(1.0, (255 - brightness) / 25.0))
            alpha[y_idx, x_idx] = int(fade * 255)

    rgba = np.dstack([arr, alpha])
    res_img = Image.fromarray(rgba, mode="RGBA")
    bbox = res_img.getbbox()
    cropped = res_img.crop(bbox)

    target_h = 770
    target_w = int(cropped.width * (target_h / cropped.height))
    resized = cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
    resized.save(OUT, "PNG", optimize=True)
    print(f"wrote transparent cutout with complete rock to {OUT} ({resized.size[0]}x{resized.size[1]}, {os.path.getsize(OUT)} bytes)")
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
