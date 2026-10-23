# Mixer riser for a Yamaha Tyros 3

A bracket that screws into the two M5 holes on the Tyros 3 rear panel, hooks
over the keyboard's rear edge with a ledge, and holds the
[mixer sleeve](../mixer-sleeve) above the keyboard, tilted 15° toward the
player. The sleeve bolts to the bracket's plate through its own 80 × 80 mm
mount pattern. The plate's underside sits a thumb, 20 mm, above the rear edge.

<p align="center">
  <img src="./views/sheet.png" alt="Labeled views of the mixer riser" width="900" />
</p>

## Files

| File | What it is |
|---|---|
| `mixer_riser.py` | The parametric CadQuery model. Every size is a named setting at the top, in groups |
| `mixer_riser.stl` | Print-ready mesh, lying on its side so every wall of the profile is vertical |
| `mixer_riser.step` | Editable CAD file in the use orientation: panel plane at x = 0, player side +x, up +z |
| `mixer_riser.3mf` | Bambu Studio project with the recommended print settings |
| `print_settings.json` | The recommended slicer settings that go into the 3MF |
| `bambu_p1s_0.4.config` | Printer and filament template: Bambu Lab P1S, 0.4 mm nozzle |
| `labels.json` | Named anchor points that `render_views.py` draws as tags |
| `check_part.py` | The checker; run it with `--max-overhang-area 300`, the ceilings of the horizontal screw holes count as overhang and print fine |
| `device()`, `features()` in `mixer_riser.py` | The keyboard's panel and sloped top plus the sleeve as ghosts, and the named features with the settings behind each |

## Rebuild

```bash
uv run mixer_riser.py
uv run render_views.py mixer_riser.step --labels labels.json --out views
uv run make_3mf.py mixer_riser.stl --settings print_settings.json \
  --template bambu_p1s_0.4.config --out mixer_riser.3mf
```

To adjust it with sliders, with the keyboard and the sleeve drawn as ghosts:

```bash
uv run mixer_riser.py --serve --open --port 8767
```

## Named features

| Name | Where it is |
|---|---|
| Base plate | The vertical plate against the rear panel, with the two screw holes |
| Panel screws | Two M5 clearance holes, 63 mm apart, heads on the rear face |
| Arm | The base plate continuing up past the panel's top edge |
| Ledge | A tab from the arm that rests on the keyboard's top, over the rear edge, taking the weight |
| Tilted plate | The 100 × 110 mm plate sloping 15° toward the player |
| Sleeve screws | Four M4 holes on the 80 × 80 pattern, counterbored from below, into the sleeve's mount pads |
| Rib | Two ribs flush with the side faces, bracing the plate down to the ledge |

## Main settings

| Setting | Value | Meaning |
|---|---|---|
| `HOLE_PITCH`, `SCREW_D` | 63 mm, M5 | The panel's two holes, measured |
| `PANEL_TOP` | 40 mm | Height of the panel's top edge above the holes. Measure it |
| `EDGE_GAP` | 20 mm | Gap between the rear edge and the plate's underside: a thumb |
| `LEDGE` | 15 mm | How far the ledge reaches over the keyboard's top |
| `TILT`, `PLATE_L` | 15°, 110 mm | Plate slope toward the player and its length |
| `T`, `W` | 6 mm, 100 mm | Profile thickness and width across the keyboard |
| `PATTERN`, `SLEEVE_SCREW_D` | 80 mm, M4 | The sleeve's mount pattern and its screws |
| `TOP_TILT` | 8° | The keyboard top's own slope, for the ghost only |

Prints on its side, 100 mm tall, 4 walls and 30 % infill. It carries a 1.3 kg
mixer on two screws for years, so print it in PETG or ASA rather than PLA.
Not printed yet.
