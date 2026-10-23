# /// script
# dependencies = ["cadquery", "pillow"]
# ///
"""Render labeled views of a STEP model for review.

Usage: `uv run render_views.py model.step [--labels labels.json] [--out views]`.
The labels file maps a name to {"at": [x, y, z], "normal": [nx, ny, nz]}.
A view shows a label only when its surface faces the camera and nothing hides it.
The key "_views" maps a view key to a title, for example {"left": "Mount face"}.
The output is one PNG per view and a `sheet.png` with all views.
"""
import argparse
import json
from pathlib import Path

import cadquery as cq
import vtk
from PIL import Image, ImageDraw, ImageFont

# Camera direction is the direction from the model centre to the camera.
VIEWS = [
    ("iso", "Iso (front-right-top)", (1, -1, 0.8), (0, 0, 1)),
    ("front", "Front (from -Y)", (0, -1, 0), (0, 0, 1)),
    ("back", "Back (from +Y)", (0, 1, 0), (0, 0, 1)),
    ("left", "Left (from -X)", (-1, 0, 0), (0, 0, 1)),
    ("right", "Right (from +X)", (1, 0, 0), (0, 0, 1)),
    ("top", "Top (from +Z)", (0, 0, 1), (0, 1, 0)),
    ("bottom", "Bottom (from -Z)", (0, 0, -1), (0, 1, 0)),
    ("iso_back", "Iso (back-left-bottom)", (-1, 1, -0.8), (0, 0, 1)),
]
SIZE = 900


def model_actors(shape):
    poly = shape.toVtkPolyData(0.05, 0.1, True)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(poly)
    body = vtk.vtkActor()
    body.SetMapper(mapper)
    body.GetProperty().SetColor(0.78, 0.80, 0.84)
    body.GetProperty().SetSpecular(0.2)

    edges = vtk.vtkFeatureEdges()
    edges.SetInputData(poly)
    edges.BoundaryEdgesOn()
    edges.FeatureEdgesOn()
    edges.SetFeatureAngle(35)
    edges.ManifoldEdgesOff()
    edges.NonManifoldEdgesOff()
    emap = vtk.vtkPolyDataMapper()
    emap.SetInputConnection(edges.GetOutputPort())
    emap.ScalarVisibilityOff()
    lines = vtk.vtkActor()
    lines.SetMapper(emap)
    lines.GetProperty().SetColor(0.15, 0.15, 0.18)
    lines.GetProperty().SetLineWidth(1.2)
    return [body, lines]


def render_view(shape, labels, direction, up, path):
    ren = vtk.vtkRenderer()
    ren.SetBackground(1, 1, 1)
    for a in model_actors(shape):
        ren.AddActor(a)
    win = vtk.vtkRenderWindow()
    win.SetOffScreenRendering(1)
    win.SetSize(SIZE, SIZE)
    win.AddRenderer(ren)

    bb = shape.BoundingBox()
    c = bb.center
    cam = ren.GetActiveCamera()
    cam.ParallelProjectionOn()
    cam.SetFocalPoint(c.x, c.y, c.z)
    cam.SetPosition(c.x + direction[0] * 1000, c.y + direction[1] * 1000, c.z + direction[2] * 1000)
    cam.SetViewUp(*up)
    ren.ResetCamera()
    cam.Zoom(0.85)
    win.Render()

    # Keep only the labels that the camera can see.
    visible = []
    zbuf = vtk.vtkFloatArray()
    win.GetZbufferData(0, 0, SIZE - 1, SIZE - 1, zbuf)
    for name, spec in labels.items():
        p = spec["at"] if isinstance(spec, dict) else spec
        n = spec.get("normal") if isinstance(spec, dict) else None
        if n and sum(a * b for a, b in zip(n, direction)) <= 0.2:
            continue
        ren.SetWorldPoint(*p, 1.0)
        ren.WorldToDisplay()
        x, y, depth = ren.GetDisplayPoint()
        if not (0 <= x < SIZE and 0 <= y < SIZE):
            continue
        if depth <= zbuf.GetValue(int(y) * SIZE + int(x)) + 0.0005:
            visible.append((name, x, SIZE - 1 - y))

    grab = vtk.vtkWindowToImageFilter()
    grab.SetInput(win)
    grab.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(grab.GetOutputPort())
    writer.Write()
    win.Finalize()
    return visible


def font(size):
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/SFNS.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def annotate(path, title, visible):
    img = Image.open(path).convert("RGB")
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
    img.save(path)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step")
    ap.add_argument("--labels")
    ap.add_argument("--out", default="views")
    ap.add_argument("--only", help="comma separated view names, for example front,iso")
    a = ap.parse_args()

    shape = cq.importers.importStep(a.step).val()
    labels = json.loads(Path(a.labels).read_text()) if a.labels else {}
    titles = labels.pop("_views", {})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None

    tiles = []
    for key, title, direction, up in VIEWS:
        if only and key not in only:
            continue
        path = out / f"{key}.png"
        visible = render_view(shape, labels, direction, up, path)
        if key in titles:
            title = f"{titles[key]} - {title}"
        tiles.append(annotate(path, title, visible))
        print(f"{path}: {len(visible)} labels visible")

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
