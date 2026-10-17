# Mixer sleeve for the Behringer Xenyx 1002SFX

A wall sleeve that holds a Behringer Xenyx 1002SFX mixer upright. The sleeve
screws to an existing mount on the wall, and the mixer slides in from the open
top, front edge first, until it rests on the end stop. The knobs stay
reachable through the open front, and the rear jacks stay free at the top.

<p align="center">
  <img src="./views/sheet.png" alt="Labeled views of the mixer sleeve" width="900" />
</p>

## Files

| File | What it is |
|---|---|
| `mixer_sleeve.py` | The parametric CadQuery model. Every size is a named setting at the top |
| `mixer_sleeve.stl` | Print-ready mesh, already lying flat on its back |
| `mixer_sleeve.step` | Editable CAD file, standing upright as mounted |
| `labels.json` | Named anchor points that `render_views.py` draws as tags |
| `render_views.py` | Renders the labeled views in `views/` |
| `sections.png` | Cross-sections through the lip and the end stop |

## Rebuild

```bash
uv run mixer_sleeve.py
uv run render_views.py mixer_sleeve.step --labels labels.json --out views
```

## Named sides and features

Use these names when you ask for a change.

| Name | Where it is |
|---|---|
| Back plate / Mount face | The flat back that screws to the wall mount |
| Mount marks M1–M4 | Small marks for the mount screws, 80 × 80 mm apart, each in a solid pad |
| Left wall, Right wall | The long sides that grip the mixer |
| Left lip, Right lip | 8 mm lips over the mixer's front edge, with a 45° fill underneath |
| Lip-free zone | The top 60 mm, where the lips stop so the mixer goes in easily |
| Open end | The top, where the mixer slides in |
| End stop | The low 16 mm stop at the bottom that carries the mixer |
| Bottom slope | The 45° run from the walls down to the end stop |
| Back vents, Side vents | 11.5 mm hexes in the back, 9 mm hexes along each side wall |
| Floor fillet | The 4 mm rounding between the walls and the back plate |

## Main settings

| Setting | Value | Meaning |
|---|---|---|
| `MIX_W × MIX_D × MIX_H` | 191 × 248 × 25 mm | Mixer body, measured without knobs |
| `CLEAR` | 0.5 mm | Gap on each side and at the end stop |
| `SLEEVE_H` | 213.5 mm | Total height, kept below a microphone arm hinge |
| `WALL`, `END` | 2.7 mm | 6 lines: 3 wall loops per side, no infill |
| `BASE` | 3.08 mm | 11 layers at 0.28 mm |
| `LIP`, `LIP_T` | 8 mm, 1.96 mm | Lip reach and thickness |
| `LIP_FREE` | 60 mm | No lip on this length at the open end |
| `END_H` | 16 mm | End stop height, low for the mixer's curved edge |
| `HOLE_PATTERN` | 80 × 80 mm | Mount screw spacing |
| `VENT_HEX`, `SIDE_HEX` | 11.5 mm, 9 mm | Back and side vent sizes |
| `NOZZLE`, `LINE`, `LAYER` | 0.4, 0.45, 0.28 mm | Printer settings the thicknesses are counted in |

Outside size: 197.4 × 30.6 × 213.5 mm.

## Print settings

- Orientation: flat on the back plate, as the STL is exported. No supports are needed.
- 0.4 mm nozzle, 0.28 mm layers, 3 wall loops, 10–15% sparse infill
- PETG or ASA for a part that holds weight on a wall for years
