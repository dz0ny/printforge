# Gutter outlet funnel, NW 280 half-round to a 58 mm downpipe

An outlet that slides over the cut end of a half-round gutter and funnels it
into a round downpipe. No joint has an inner lip: the gutter goes into the
skirt, the funnel floor only ever goes down, and the pipe goes over the
spigot, so water never has a step to climb.

<p align="center">
  <img src="./views/sheet.png" alt="Labeled views of the gutter outlet" width="900" />
</p>

## Files

| File | What it is |
|---|---|
| `gutter_outlet.py` | The parametric smlibpy model. Every size is a named setting at the top, in groups |
| `gutter_outlet.stl` | Print-ready mesh, standing on the spigot tip |
| `gutter_outlet.step` | Editable CAD file in the use orientation, gutter axis along X |
| `gutter_outlet.3mf` | Bambu Studio project with the recommended print settings |
| `print_settings.json` | The recommended slicer settings that go into the 3MF |
| `bambu_p1s_0.4.config` | Printer and filament template: Bambu Lab P1S, 0.4 mm nozzle, Bambu PLA Basic |
| `labels.json` | Named anchor points that `render_views.py` draws as tags |
| `check_part.py` | The checker: run it with `--overhang 55 --max-thin-area 10`, see "Checks" below |
| `keep_clear()` in `gutter_outlet.py` | The water channel, which the checker verifies stays open |
| `device()`, `features()` in `gutter_outlet.py` | The gutter end and the pipe as a ghost for the configurator, and the named features with the settings behind each |

## Rebuild

```bash
uv run gutter_outlet.py
uv run render_views.py gutter_outlet.step --labels labels.json --out views
uv run make_3mf.py gutter_outlet.stl --settings print_settings.json \
  --template bambu_p1s_0.4.config --out gutter_outlet.3mf
```

To adjust it with sliders, with the gutter and the pipe drawn as ghosts:

```bash
uv run gutter_outlet.py --serve --open
```

## Named features

| Name | Where it is |
|---|---|
| Skirt | The half ring over the outside of the gutter end, stopped below the bead and the hook, free edges rounded |
| Funnel | The loft from the gutter's D profile down to the round spigot, floor always descending, 8 lines thick |
| Stop collar | The ring the pipe end rests against, with a 45° cone under it so it prints without support |
| Spigot | The round stub the downpipe slides over |

## Main settings

| Setting | Value | Meaning |
|---|---|---|
| `GUTTER_ID`, `SHEET`, `FIT` | 127, 0.6, 0.4 mm | Gutter inside diameter, sheet thickness, clearance per side |
| `BEAD_D`, `HOOK_D` | 16, 8 mm | The gutter's rolled front bead and rear hook, on the ghost, so the checker sees them |
| `WALL` | 2.4 mm | Spigot wall, 5 lines at 0.48 mm, so the bore stays wide |
| `FUNNEL_WALL` | 3.84 mm | Skirt and funnel wall, 8 lines, one outer surface with no step |
| `LID_START`, `ROUND` | 12 mm, 1 mm | The funnel stays open like the gutter for 12 mm before the lid closes; the skirt's free edges are rounded |
| `SKIRT_L`, `SKIRT_TOP` | 25, -8 mm | Skirt length, and how far below the gutter top it stops |
| `FUNNEL_L`, `DROP` | 50, 3 mm | Funnel length and the floor drop along it |
| `PIPE_OD`, `PIPE_WALL`, `PIPE_FIT` | 58, 1, 0.3 mm | Downpipe outside diameter and wall, clearance per side |
| `SPIGOT_L`, `COLLAR` | 40, 2.5 mm | Spigot length into the pipe, collar size beyond the pipe |

The funnel is made of ruled faces between exact arcs and lines, one face per
pair of matching edges, so the STL is smooth and the funnel cannot twist.
smlibpy's own `loft` paired the two profiles with an offset and twisted it.

Use size: 115 × 136 × 74 mm. Prints standing on the spigot tip, 115 mm tall,
with an outer brim.

## Checks

```bash
uv run check_part.py gutter_outlet.py --overhang 55 --max-thin-area 10
```

- `--overhang 55`: the corners of the lid lean 54° and print fine.
- `--max-thin-area 10`: the open zone has hairline edges that this design has always had.
  Where the flat lid cut crosses the sloping cavity roof, a ledge up to 0.25 mm thick tapers to nothing.
  The skirt's rounded top also ends in a small notch where it meets the funnel.
  The checker finds about 6 mm² of these. The CadQuery version had the same geometry, within 0.1 mm, and passed only because its random samples missed them.

## Print settings

- 0.4 mm nozzle, 0.2 mm layers, 6 wall loops, 15 % gyroid infill, no supports. The funnel wall is 8 lines, so it gets a little infill between its loops
- Sliced headless in Bambu Studio for a P1S: 575 layers, about 1 h 56 min and 99 g of PLA
- Bambu PLA Basic is fine indoors; outside in the sun and rain, print it in
  PETG or ASA
