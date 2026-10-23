---
name: cad-print-design
description: Design 3D-printable parts (holders, sleeves, mounts, brackets, enclosures, adapters, clips) as parametric CadQuery models run with uv, exporting STEP, STL and a print-ready Bambu Studio/OrcaSlicer 3MF with recommended settings, and rendering labeled side views the user can inspect. Use this whenever the user asks for an STL, a 3D print, a printable holder/case/mount for a device, or wants to change dimensions, walls, lips, holes, vents or fillets on a part — even if they never say "CAD" or "CadQuery".
---

# Printable part design with CadQuery

The user iterates on a physical part by looking at pictures and saying things like "make the left wall thinner" or "remove the lip from the top 6 cm". That loop only works when both of you use the same names for the same places, the pictures are trustworthy, and every number is one clear parameter. Everything below serves that loop.

## 1. Before modelling: pin down the inputs

Ask in one round (AskUserQuestion works well), and say which defaults you will use if they skip a question:

- **The object's real body size.** Spec sheets often include knobs, feet or packaging. In one session a mixer listed as 50 mm thick was really 25 mm. Ask for a ruler measurement of the body alone, and treat spec values as placeholders you flag.
- **How it is mounted and used.** Which side faces the wall or desk, which way is up, and where the object goes in. Draw a quick sketch (an inline SVG with named sides) before writing code if the request is at all ambiguous. Users often say "draw it first".
- **Printer, nozzle, layer height and wall loops.** Ask which nozzle they print with (0.4 mm is common; 0.6 mm and 0.2 mm exist), the layer height (0.2 mm, or 0.28 mm for draft/fast), how many wall loops their profile uses (often 2–3), and the bed size. These set wall thicknesses, the smallest holes and webs, fillet sizes and fit clearances. See "Nozzle-aware sizes" below.
- **Material** (PLA, PETG or ASA) if the part carries load or sits near heat.
- **Fasteners.** Heat-set inserts, screws or magnets, with sizes and hole spacing.

When a later message uses a vague word ("height", "thickness", "side", "top"), don't guess. Reply with the named dimensions and their current values ("Length along the slide: 213.5 mm, Width: 198 mm, Depth off the wall: 32.5 mm. Which one?"). In one session "height" meant thickness, and a wrong guess cost two rebuilds.

## 2. Project setup: always uv + CadQuery

Work in a real folder the user can reach, not a hidden scratch folder, so they can run the script themselves. If the session sits in a temporary workspace, offer to move it first.

```bash
uv init --bare --name <part-name>
uv add cadquery
uv run <part>.py
```

Copy `scripts/render_views.py` from this skill into the project. It declares its own dependencies inline, so `uv run render_views.py ...` works.

## 3. The model script

Use `assets/example_mixer_sleeve.py` as a working reference. It's a complete sleeve with lips, 45° lip fills, hex vents, a low end stop, a slope and mount marks. The shape of a good script:

1. **A printer block first:** `NOZZLE`, `LINE` (about 1.1 × nozzle) and `LAYER`. Then express every thickness as a count of those: `WALL = 6 * LINE`, `BASE = 11 * LAYER`. Use lines for thicknesses that lie across the bed in the print orientation, and layers for thicknesses that stack upward. When the user changes nozzle or layer height, the whole part re-tunes. Assert that no wall is thinner than two lines.
2. **Parameters at the top, in mm, named after the features, in groups.** For example `WALL`, `BASE`, `LIP`, `LIP_FREE`, `END_H`, `HOLE_PATTERN`, with a one-line comment each. A user request should map to changing one or two of these. Derived values (`IN_D`, `OUT_H`, ...) come next.
   Start every project with the settings in groups, because the configurator (section 6b) draws each group as a collapsible section. A group is a comment line with an emoji and a short name above its settings, and runs until the next such line:

   ```python
   # 🎛️ Mixer body size in mm. Measure your mixer.
   MIX_W = 189.0   # Width, left to right, on the open short side. [100:300]
   MIX_H = 31.0    # Body thickness with feet, without knobs. [10:80]

   # 🖨️ Printer. The part prints flat, so X and Y use lines and Z uses layers.
   NOZZLE = 0.4
   LINE = 0.45     # Line width, about 1.1 x the nozzle.
   ```

   The device comes first, then the printer, then one group per feature family (shell, end stop, lips, vents, mount). Pick an emoji that reads as the feature. Give the device sizes a `[min:max]` so they get sliders.
3. **One `build()` in a design frame** that is easy to reason about, for example X along the slide, Y across, Z off the back plate.
4. **Exports:**
   - `<part>.step` in the *use* orientation (as mounted), for CAD viewing.
   - `<part>.stl` in the *print* orientation, positioned at z = 0.
   - `labels.json` with the named features, in the same frame as the STEP.
5. **Asserts that catch silly mistakes.** A rotation sign error once put the end stop on top and the opening on the build plate. Check orientation with a slab test, by comparing material volume near z = 0 with material near the top. Also check minimum floor thickness above holes, and that the part fits the bed.
6. **A section plot** (`sections.png`) through the trickiest profile helps you verify fillets, lips and holes quickly.

Read `references/cadquery-pitfalls.md` before writing fillets, rotations or vent patterns. It records what failed and what worked.

## 4. Name every side and feature

Give each side and each distinctive feature a short, stable name, and use those names everywhere: parameter comments, `labels.json`, replies to the user. Sides are things like *Back plate (mount face)*, *Left wall*, *Right wall*, *Open end*, *End stop*. Features are things like *Left lip*, *Lip fill (45°)*, *Lip-free zone*, *Bottom slope*, *Mount mark M1–M4*, *Side vents*, *Back vents*, *Floor fillet*.

Unique or easy-to-miss features especially need names, because those are what the user will want to tweak. Keep names stable across iterations. If a feature is renamed or removed, say so.

`labels.json` format (anchor 0.5 mm outside the surface, normal pointing out of it):

```json
{
  "_views": {"left": "Mount face", "right": "Inside / knob side", "top": "Open end", "bottom": "End stop"},
  "Back plate": {"at": [-0.5, 99, 106], "normal": [-1, 0, 0]},
  "Left lip":   {"at": [33, 7, 83.5],   "normal": [1, 0, 0]}
}
```

Compute anchors from the parameters in the model script, so they move when the part changes.

## 5. Views the user can inspect

After every build:

```bash
uv run render_views.py <part>.step --labels labels.json --out views
```

This writes shaded orthographic views (front, back, left, right, top, bottom) and two isometric views, all with feature edges and red name tags, plus `views/sheet.png`. A tag appears only where its surface faces the camera and isn't hidden. Use `_views` to title each view by its side name, so "left" becomes "Mount face - Left (from -X)".

Look at `sheet.png` yourself (Read it) before sending anything. You're checking that the change actually happened, the orientation is right, and no tag sits in the wrong place. Then send the sheet, plus a close-up view if the change was local, along with the STL and STEP.

## 6. Print-ready 3MF with recommended settings

An STL carries no settings. Also write a 3MF that opens in Bambu Studio or OrcaSlicer with the recommended settings already set:

1. Write `print_settings.json` next to the model, using slicer keys: `layer_height`, `initial_layer_print_height`, `wall_loops`, `top_shell_layers`, `bottom_shell_layers`, `sparse_infill_density`, `sparse_infill_pattern`, `enable_support`, `brim_type`, `seam_position`. Add a `"_why"` key with one line of reasoning. Keys that start with `_` are skipped. Match the settings to the model: wall loops so that walls are pure perimeters, a layer height the layer counts in the script assume, and supports off if the print orientation needs none.
2. Ask the user for one project they have saved in Bambu Studio with their printer and filament. Pass it, or its `Metadata/project_settings.config`, as the template.
3. Run `uv run make_3mf.py part.stl --settings print_settings.json --template <template> --out part.3mf`.
4. If Bambu Studio is installed, verify by slicing headless: `/Applications/BambuStudio.app/Contents/MacOS/BambuStudio --slice 1 --outputdir out part.3mf`. Then check `out/result.json` and the layer count (`grep -c "^; CHANGE_LAYER" out/plate_1.gcode`). Report the estimated time and grams from the G-code to the user.

The script stores the settings on the object, and object settings override the template's process (verified: 110 layers at 0.28 mm on a project set to 0.20 mm). The G-code header still prints the project values, so count layers instead of trusting the header. Without a template, the 3MF still has the geometry and the object settings. Bambu's command line cannot slice it with the stock presets, and the behaviour in the app is not verified, so prefer a template.

## 5b. Checks a render hides

Run the checker after every build, before looking at the views:

```bash
uv run check_part.py <model>.py            # add --overhang 55 or --min-wall 1.2 per part
```

It builds the model and reports, with an exit code for scripts:

- validity and that the part is one solid,
- walls thinner than two lines, found by casting rays inward from the surface and reported as an area, so a hairline notch where a fillet ends does not fail the part but a sliver or a blocked channel does,
- knife edges, where two faces fold back on each other,
- overlap with `device()`: the floor fillet running into a device's square edge, a stop that is in the way,
- `keep_clear()` volumes: a list of shapes that must stay empty, such as a water channel, a screw's access, or the path a plug travels. Define it in the model next to `device()`,
- overhangs in the print orientation, read from the exported STL.

A part that is several prints, because it spans more than the bed or prints better in pieces, defines `parts()` returning `{name: shape}` in print orientation while `build()` returns the assembly as one compound; the checker then checks each part on its own and the device against the assembly, and the script exports one STL per part.

Model the device honestly: feet, edge radii, beads and hooks. The gutter outlet's bead and the mixer's rubber feet both changed what the checks found. When a check fails, fix the geometry, not the threshold; a per-part threshold is fine when the part really needs it, and the README says so.

## 6b. Interactive configurator

For a part built around a device, give the user a page where they can adjust the device and watch the shell follow, like MakerWorld's Parametric Model Maker but with CadQuery kept as the language. The `printforge-configurator` package in `configurator/` is the server and the page; it needs no CadQuery itself.

1. Write the model so its settings are exposed without any new format. The server takes every top-level `NAME = number|bool` line above the first `def` as a parameter. The trailing comment is the description, and an optional `[min:max]` at its end makes a slider: `MIX_W = 189.0  # Width on the open side. [100:300]`. A comment line above a block of settings is the group: its leading emoji is the group's icon and the first sentence its title, and the group runs until the next heading. The page shows each group as a collapsible section, the first one open. Derived values such as `WALL = 8 * LINE` stay hidden and recompute.
2. Add a `device()` function that returns the device as a CadQuery shape in its resting position. The page draws it as a translucent ghost inside the shell. It is never exported.
2b. Describe the features in a `features()` function: `{"Left lip": {"at": (x, y, z), "normal": (0, 0, 1), "params": ["LIP", "LIP_T"]}, ...}` in the model's own frame. Build `labels()` for the views from it, so the tags and the page share one table. In the page, clicking a feature highlights its settings on the left and clicking a setting's name shows its feature on the part.
3. Plug the configurator into the project. Add the package as a dependency, from git (any project) or by path (a project inside this repo):

   ```bash
   uv add "printforge-configurator @ git+https://github.com/dz0ny/printforge#subdirectory=skills/cad-print-design/configurator"
   ```

   Then end the script's `__main__` block with a `--serve` flag:

   ```python
   if __name__ == "__main__":
       import sys
       if "--serve" in sys.argv:
           from printforge_configurator import serve
           port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8765
           host = "0.0.0.0" if "--lan" in sys.argv else "127.0.0.1"  # --lan: reachable from a phone.
           serve(__file__, port=port, open_browser="--open" in sys.argv, host=host)
           sys.exit()
       ...  # the usual exports
   ```

   `uv run model.py --serve` then serves the page at <http://127.0.0.1:8765/>; give each project its own `--port` so two can run at once, and add `--lan` to reach it from a phone on the same network (the server prints the address). For a script with nothing added, `uvx --from "git+https://github.com/dz0ny/printforge#subdirectory=skills/cad-print-design/configurator" printforge-configurator model.py` works too.
4. Add a launcher for the project in `.claude/launch.json` at the repo root, so the page opens in the Claude browser pane with the browser `preview_start` tool:

   ```json
   {"name": "mixer-sleeve", "runtimeExecutable": "uv",
    "runtimeArgs": ["run", "--project", "projects/mixer-sleeve", "projects/mixer-sleeve/mixer_sleeve.py", "--serve"],
    "port": 8765}
   ```

The page has Rebuild, an auto-rebuild switch, a Dimensions toggle that draws the overall size on the part, a Drawing view, a Download menu with the shell STL, the shell STEP, the device STL and the drawing SVG, and Save to script, which writes the values back into the Python file and keeps every comment. The server keeps one warm worker running inside the project's own uv environment, so a rebuild costs only the model's own time (under 2 s for the mixer sleeve), repeats of the same values come from an in-memory cache, and the STEP is exported only when it is downloaded. A broken edit shows its traceback in the build log and the worker restarts on the next build. The committed script stays the source of truth, so after the user saves, rebuild the views and 3MF with the usual commands.

### The drawing sheet

The Drawing view is a technical drawing of the part, made from the model, not drawn by hand. Its rules, so a user can read it:

- **One view per page.** Top, Front, Right and Iso each get a landscape page with a pager; the download is the current page or all pages stacked.
- **The view uses the maximum space and sits in the middle.** The view together with its dimension rows is one block, scaled to the largest size that fits the page above the title block, then centred. Nothing else competes for the page: the title top-left, the title block a thin strip at the bottom.
- **Dimensions are traced from the geometry.** Every straight visible edge in a projection gives a level, and the chain of gaps between levels is the dimension set. Hidden lines are drawn dashed and never dimensioned.
- **Dimensions show on hover, not all at once.** By default a page shows only the overall size on each axis and a tick at every level. Hovering an edge shows its gaps to both neighbours and its distance from the datum, with the extension line drawn through the part so it is clear what is measured. A click pins a set; Escape clears pins; a Show all switch brings back every chain, staggered over rows so labels never overprint.
- **Vector, zoomable.** Wheel and pinch zoom around the cursor, drag pans, double-click fits a view, and Fit, −, +, 1:1 are on the sheet. Text keeps its size in sheet pixels, so zooming in makes it readable.

When a part's projections have arcs, the chains measure the straight edges only; diameters are read from the settings on the left.

## 7. Each iteration

- Change the fewest parameters that do what was asked, rebuild, re-render and look.
- Reply with what changed in feature names and numbers ("Lip: 3 → 8 mm with a 45° fill; Lip-free zone stays 60 mm"), the new outside size, and anything you could not do (for example "two slope edges stay sharp, the fillet fails there").
- If a request will cause a fit or print problem, say so concretely and offer the choice. For example, a 45° lip fill eats into the corner where a square mixer edge sits.
- Never claim the part fits until the user test-prints. Say "rebuilt, not printed".
- **Check corners and cut ends after every change.** When a cut (a slope, a lowered wall, a shortened lip) meets another feature, leftovers appear: stubs of a lip sliced by a slope, or a notch from a stray cutter. Confirm the part is one solid (`len(part.solids().vals()) == 1`). Then render a close-up by intersecting the part with a box around each changed corner and running `render_views.py` on that crop. End features such as lips a few mm *before* a slope instead of letting the slope slice them.
- **Name your reading of terse requests.** "Revert again" or "go in between" can mean more than one thing. Make the most likely change, then say in one line what you took it to mean and what the other reading would be.

## Nozzle-aware sizes

Line width is about 1.1 × nozzle (0.45 mm for a 0.4 nozzle). Scale with the nozzle the user named:

| Thing | 0.4 mm nozzle | 0.6 mm nozzle | Why |
|---|---|---|---|
| Wall thickness | multiples of ~0.45: 1.2, 1.6, 2.0, 2.4, 3.0 | multiples of ~0.65: 2.0, 2.6, 3.2 | whole perimeters, no gap fill |
| Smallest hole or slot | ≥ 1.0 mm | ≥ 1.5 mm | smaller ones close up |
| Web between vent holes | ≥ 2 lines (≥ 1.0 mm), 2.5–3 for strength | ≥ 1.4 mm, 3+ for strength | thin webs break |
| Fillet radius | ≥ 0.5 mm, 1 mm reads well | ≥ 0.8 mm, 1.5 mm reads well | smaller rounds print as corners |
| Sliding fit clearance per side | 0.2–0.3 mm (0.5 loose) | 0.3–0.4 mm | wider lines grow parts |
| Engraved marks | ≥ 0.6 mm deep and ≥ 2 mm wide | ≥ 0.8 mm deep and ≥ 3 mm wide | must survive a few layers |
| Heat-set insert holes | follow the insert maker's size; boss ≈ 2.5 × insert diameter; hole depth = insert + 1–2 mm; ≥ 2–3 mm solid floor beyond | same | the melt needs somewhere to go |

## Faster prints

When the user shares a slicer screenshot and asks for a faster print:

- **Slicer first.** A coarser layer height (0.28 mm) usually saves 25–35%. With wall loops set so thin walls are pure perimeters, and 10–15% sparse infill, the walls print faster and stronger.
- **Walls that are exactly 2 × loops × line** (for example 6 lines for 3 loops) print without infill between the perimeters.
- **Fewer, larger holes on big flat areas.** Every vent hole adds perimeters and travel moves on every layer it passes through. Keep a separate, smaller hole size for low walls where large holes do not fit.
- **Thinner base plates and lower walls** remove whole layers. Keep solid pads where screws or mounts go.
- Expect the user to try sizes and go back and forth. Keep each choice as one parameter so switching is a one-line change.

## Printability rules of thumb

- Overhangs up to 45° print without support. Replace 90° undercuts (like a lip underside) with a 45° fill, or choose a print orientation where they become vertical walls.
- Holes in walls that print vertically: use hexagons or teardrops with a point facing up (+Z of the print). Round holes under 8 mm are fine.
- Put the largest flat face on the bed when you can. State the print orientation in your reply, and export the STL already in it.
- Check the part fits the bed (Bambu X1/P1/A1: 256 mm; A1 mini: 180 mm). Rotating it diagonally gains room.
