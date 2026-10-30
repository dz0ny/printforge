# /// script
# dependencies = ["smlibpy==0.6.2", "pillow"]
# ///
"""Section views for the cocoa dispenser, with smlibpy's renderer.

The assembly is cut at y = 0, at rest and at full press, side by side in views/section_rest_pressed.png.
A close-up of the striker tongue on the rack goes to views/tongue_closeup.png.
"""
import io
import sys
from pathlib import Path

from PIL import Image
from smlibpy import Align, Box, render

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import cocoa_dispenser as m  # noqa: E402

out = here / "views"
out.mkdir(exist_ok=True)
CUT = {"origin": (0, 0, 0), "normal": (0, -1, 0)}  # Remove the front half, so the cut face shows from -Y.


def save(pic, path):
    Image.open(io.BytesIO(bytes(pic))).convert("RGB").save(path)
    return Image.open(path)


panels = []
for state, press in (("rest", 0.0), ("pressed", m.TRAVEL)):
    pic = render(list(m.parts(press).values()), view="front", section=CUT, colors="distinct", size=(900, 900))
    panels.append(save(pic, out / f"section_{state}.png"))
sheet = Image.new("RGB", (sum(i.width for i in panels), max(i.height for i in panels)), "white")
x = 0
for i in panels:
    sheet.paste(i, (x, 0))
    x += i.width
sheet.save(out / "section_rest_pressed.png")

# Close-up: the lid and the rod at rest, cut through the side of the tongue at y = 0.5.
# The tongue shows in its pocket, with its nub in the teeth.
ps = m.parts(0.0)
box = Box(17.5, 9.5, 26, align=Align.MIN).translate(-4, -9, m.BODY_Z + m.TIP_Z - 8)
piece = [ps["lid"] & box, ps["cup"] & box]
save(render(piece, view=(0.6, 1, 0.45), colors="distinct", size=(900, 900)), out / "tongue_closeup.png")
print("wrote views/section_rest_pressed.png, views/tongue_closeup.png")
