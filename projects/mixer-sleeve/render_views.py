# /// script
# dependencies = ["smlibpy==0.6.2", "pillow", "numpy"]
# ///
"""Render labeled views of a STEP model for review, with smlibpy.

Usage: `uv run render_views.py model.step [--labels labels.json] [--out views]`.
The labels file maps a name to {"at": [x, y, z], "normal": [nx, ny, nz]}.
A view shows a label only when its surface faces the camera.
A ray from the label to the camera must also hit nothing.
The key "_views" maps a view key to a title, for example {"left": "Mount face"}.
The output is one PNG per view and a `sheet.png` with all views.
"""
import argparse
import io
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from smlibpy import import_step, render

# Direction from the model to the camera, and the screen's up direction.
VIEWS = [
    ("iso", "Iso (front-right-top)", (1, -1, 0.8), (0, 0, 1)),
    ("front", "Front (from -Y)", (0, -1, 0), (0, 0, 1)),
    ("back", "Back (from +Y)", (0, 1, 0), (0, 0, 1)),
    ("left", "Left (from -X)", (-1, 0, 0), (0, 0, 1)),
    ("right", "Right (from +X)", (1, 0, 0), (0, 0, 1)),
    ("top", "Top (from +Z)", (0, 0, 1), (0, 1, 0)),
    ("bottom", "Bottom (from -Z)", (0, 0, -1), (0, -1, 0)),
    ("iso_back", "Iso (back-left-bottom)", (-1, 1, -0.8), (0, 0, 1)),
]
SIZE = 900


def unit(v):
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def screen_axes(to_cam, up):
    """Return the screen right and up directions in model space."""
    d = unit(to_cam)
    right = unit(np.cross(up, d))
    return right, np.cross(d, right)


def label_visible(pieces, at, normal, to_cam):
    """Return True when the label faces the camera and the ray to the camera hits no piece."""
    if np.dot(unit(normal), unit(to_cam)) <= 0.05:
        return False
    for piece in pieces:
        try:
            if piece.raycast(tuple(float(c) for c in at), tuple(float(c) for c in unit(to_cam))):
                return False
        except Exception:
            continue
    return True


def render_view(part, labels, to_cam, up):
    """Render one shaded view. Return the image and the visible labels as (name, px, py)."""
    pieces = list(part) if isinstance(part, (list, tuple)) else [part]
    pic = render(pieces, view={"direction": tuple(-unit(to_cam)), "up": up},
                 size=(SIZE, SIZE), edges=True)
    img = Image.open(io.BytesIO(bytes(pic))).convert("RGB")
    fr = pic.frame
    right, upv = screen_axes(to_cam, up)
    visible = []
    for name, lab in labels.items():
        at = np.asarray(lab["at"], float)
        if not label_visible(pieces, at, lab.get("normal", to_cam), to_cam):
            continue
        x = SIZE / 2 + (float(at @ right) - fr["mid_x"]) * fr["scale"]
        y = SIZE / 2 - (float(at @ upv) - fr["mid_y"]) * fr["scale"]
        visible.append((name, x, y))
    return img, visible


def font(size):
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def annotate(img, title, visible):
    d = ImageDraw.Draw(img)
    f, ft = font(18), font(24)
    d.text((14, 10), title, fill=(20, 20, 20), font=ft)
    placed = []
    for name, x, y in sorted(visible, key=lambda v: v[2]):
        d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(220, 50, 40))
        tx, ty = x + 12, y - 12
        w = d.textlength(name, font=f)
        tx = min(tx, SIZE - w - 8)
        while any(abs(ty - py) < 24 and abs(tx - px) < 160 for px, py in placed):
            ty += 24
        placed.append((tx, ty))
        d.line((x, y, tx - 2, ty + 11), fill=(220, 50, 40), width=2)
        d.rectangle((tx - 4, ty - 2, tx + w + 4, ty + 22), fill=(255, 255, 255), outline=(220, 50, 40))
        d.text((tx, ty), name, fill=(150, 20, 15), font=f)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step")
    ap.add_argument("--labels")
    ap.add_argument("--out", default="views")
    ap.add_argument("--only", help="comma separated view names, for example front,iso")
    a = ap.parse_args()

    part = import_step(a.step)  # One part, or a list of parts for a STEP with several bodies.
    if not isinstance(part, (list, tuple)) and hasattr(part, "__len__") and not hasattr(part, "volume"):
        part = list(part)
    labels = json.loads(Path(a.labels).read_text()) if a.labels else {}
    titles = labels.pop("_views", {})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None

    tiles = []
    for key, title, to_cam, up in VIEWS:
        if only and key not in only:
            continue
        img, visible = render_view(part, labels, to_cam, up)
        if key in titles:
            title = f"{titles[key]} - {title}"
        img = annotate(img, title, visible)
        img.save(out / f"{key}.png")
        tiles.append(img)
        print(f"{out / key}.png: {', '.join(v[0] for v in visible) or 'no labels'}")

    cols = 4 if len(tiles) > 4 else len(tiles)
    rows = (len(tiles) + cols - 1) // cols
    t = SIZE // 2
    sheet = Image.new("RGB", (cols * t, rows * t), "white")
    for i, img in enumerate(tiles):
        sheet.paste(img.resize((t, t)), ((i % cols) * t, (i // cols) * t))
    sheet.save(out / "sheet.png")
    print(f"{out / 'sheet.png'}")


if __name__ == "__main__":
    main()
