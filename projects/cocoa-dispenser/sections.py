# /// script
# dependencies = ["cadquery", "pillow"]
# ///
"""Section views for the cocoa dispenser: the assembly cut at y = 0, at rest and at full
press, side by side (views/section_rest_pressed.png), and a close-up of the striker
tongue on the rack (views/tongue_closeup.png). Uses render_views.py's renderer."""
import importlib.util
import os
import sys
from pathlib import Path

import cadquery as cq
from PIL import Image

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import cocoa_dispenser as m  # noqa: E402

spec = importlib.util.spec_from_file_location("render_views", here / "render_views.py")
rv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rv)

out = here / "views"
out.mkdir(exist_ok=True)


def half(shape, press):
    """Keep the y >= 0 half of the assembly, so the cut face shows from -Y."""
    big = cq.Workplane("XY").box(400, 200, 400, centered=(True, False, True))
    return shape.intersect(big)


def render(shape, path, direction, up=(0, 0, 1)):
    rv.render_view(shape.val(), {}, direction, up, str(path))


panels = []
for state, press in (("rest", 0.0), ("pressed", m.STROKE)):
    ps = m.parts(press)
    kept = []
    for p in ps.values():  # Cut the parts one by one; a compound boolean can come back empty.
        c = half(p, press)
        if c.vals() and c.val().Volume() > 0.01:
            kept.append(c.val())
    cut = cq.Workplane("XY").newObject([cq.Compound.makeCompound(kept)])
    path = out / f"section_{state}.png"
    render(cut, path, (0, -1, 0))
    panels.append(path)
imgs = [Image.open(p) for p in panels]
w = sum(i.width for i in imgs)
sheet = Image.new("RGB", (w, max(i.height for i in imgs)), "white")
x = 0
for i in imgs:
    sheet.paste(i, (x, 0))
    x += i.width
sheet.save(out / "section_rest_pressed.png")

# Close-up: lid and rod at rest, cut through the tongue's side (y = 0.5) so the tongue
# shows in its pocket with its nub in the teeth, seen from the cut face.
ps = m.parts(0.0)
box = cq.Workplane("XY").box(18, 9.5, 26, centered=(False, False, False)).translate((-4, -9, m.BODY_Z + m.TIP_Z - 8))
piece = cq.Workplane("XY").newObject([cq.Compound.makeCompound([ps["lid"].intersect(box).val(), ps["rod"].intersect(box).val()])])
render(piece, out / "tongue_closeup.png", (0.6, 1, 0.45))
print("wrote views/section_rest_pressed.png, views/tongue_closeup.png")
