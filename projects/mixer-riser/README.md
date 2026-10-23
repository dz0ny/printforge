# Mixer riser for a Yamaha Tyros 3

Four printed parts that hold the [mixer sleeve](../mixer-sleeve) above a Tyros 3,
tilted 15° toward the player. The Tyros rear panel has four threaded holes in a
row near its top edge, an outer pair 330 mm apart and an inner pair 270 mm apart,
so each side has two holes 30 mm apart. One identical bracket per side screws
into its pair with M5 screws, hooks over the keyboard's rear edge with a ledge,
and carries a stub tilted 15°. Two identical plate halves lie on the stubs,
overlap 92 mm in the middle with a half-lap joint, and are clamped together by
the sleeve's own four M4 screws on its 80 × 80 pattern. The plate's underside
sits a thumb, 20 mm, above the rear edge. The span is wider than a 256 mm bed,
which is why it is four parts.

<p align="center">
  <img src="./views/sheet.png" alt="Labeled views of the mixer riser assembly" width="900" />
</p>

## Files

| File | What it is |
|---|---|
| `mixer_riser.py` | The parametric CadQuery model: `build()` is the assembly, `parts()` the two printable parts |
| `mixer_riser.step` | The assembly in the use orientation: panel plane at x = 0, player side +x, up +z |
| `mixer_riser_bracket.stl`, `.3mf` | The side bracket, print two, on its side with every wall vertical |
| `mixer_riser_plate_half.stl`, `.3mf` | The plate half, print two, flat with the lap step on top |
| `print_settings.json` | The recommended slicer settings that go into the 3MFs |
| `bambu_p1s_0.4.config` | Printer and filament template: Bambu Lab P1S, 0.4 mm nozzle |
| `labels.json` | Named anchor points that `render_views.py` draws as tags on the assembly |
| `check_part.py` | The checker; it checks each part and the assembly. Run with `--max-overhang-area 300`, the ceilings of the horizontal screw holes count as overhang and print fine |
| `device()`, `features()` in `mixer_riser.py` | The keyboard's panel and sloped top plus the sleeve as ghosts, and the named features with the settings behind each |

## Rebuild

```bash
uv run mixer_riser.py
uv run render_views.py mixer_riser.step --labels labels.json --out views
uv run make_3mf.py mixer_riser_bracket.stl --settings print_settings.json \
  --template bambu_p1s_0.4.config --out mixer_riser_bracket.3mf
uv run make_3mf.py mixer_riser_plate_half.stl --settings print_settings.json \
  --template bambu_p1s_0.4.config --out mixer_riser_plate_half.3mf
```

To adjust it with sliders, with the keyboard and the sleeve drawn as ghosts, from
a phone on the same network too:

```bash
uv run mixer_riser.py --serve --lan --port 8767
```

## Assembly

1. Screw a bracket to each pair of holes, M5, ledge resting on the keyboard's top.
2. Lay the left plate half on the left stub, lap step up, and the right half on the
   right stub, turned over so its lap is underneath; the two laps meet flush.
3. Two M4 screws per side through the half into the stub, nuts underneath.
4. Set the sleeve on the plate and drive its four M4 screws through both halves
   into the sleeve's mount pads; they clamp the lap together.

## Named features

| Name | Where it is |
|---|---|
| Base plate | The vertical plate against the rear panel, with its pair of screw holes |
| Panel screws | Two M5 clearance holes 30 mm apart, heads on the rear face |
| Arm | The base plate continuing up past the panel's top edge |
| Ledge | A tab from the arm that rests on the keyboard's top, over the rear edge, taking the weight |
| Stub | The bracket's tilted top, 90 mm along the slope, with two M4 holes for the plate half |
| Rib | Two ribs flush with the bracket's side faces, bracing the stub down to the ledge |
| Plate half | One of the two 221 × 90 mm plates, 6 mm thick |
| Lap joint | The 92 mm overlap in the middle, each half thinned to 3 mm, clamped by the sleeve's screws |
| Sleeve screws | The sleeve's 80 × 80 pattern, M4, through both halves |

## Main settings

| Setting | Value | Meaning |
|---|---|---|
| `OUTER`, `INNER` | 330, 270 mm | The outer and inner pairs of panel holes, measured 33 and 27 cm |
| `SCREW_D`, `HEAD_D` | M5, 9 mm | Panel screws; the two heads of a pair must not touch |
| `PANEL_TOP` | 25 mm | Height of the panel's top edge above the holes, measured |
| `EDGE_GAP` | 20 mm | Gap between the rear edge and the plate's underside: a thumb |
| `LEDGE` | 15 mm | How far the ledge reaches over the keyboard's top |
| `TILT`, `PLATE_L` | 15°, 90 mm | Slope toward the player and the plate's depth along it |
| `T`, `BRK_W` | 6 mm, 50 mm | Profile thickness and bracket width |
| `OVERLAP`, `PLATE_MARGIN` | 92 mm, 5 mm | The half-lap length and the plate's reach beyond the bracket |
| `PATTERN`, `SLEEVE_SCREW_D` | 80 mm, M4 | The sleeve's mount pattern and its screws |
| `TOP_TILT` | 8° | The keyboard top's own slope, for the ghost only |

Brackets print on their side, 50 mm tall; plate halves print flat. 4 walls and
30 % infill. It carries a 1.3 kg mixer for years, so print it in PETG or ASA.
Not printed yet.
