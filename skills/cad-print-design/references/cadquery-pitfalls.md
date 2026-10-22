# CadQuery pitfalls and fixes

These are things that went wrong while building a real part, and what fixed them.

## Fillets

- **Do all booleans first, then fillet.** Cutting or unioning after filleting, then filleting again near the old fillets, fails with `BRep_API: command not done`. It can also crash the Python process with a segfault (exit code 139), which `try/except` cannot catch.
- **Fillet many edges in one call.** A single `fillet()` over a big edge list works more often than many small calls in sequence.
- **Greedy edge set for difficult groups.** Collect the safe edges, then add the risky ones one at a time. Before adding each one, test `part.newObject(keep + [e]).fillet(r)` and keep the edge only if that test passes. Finish with one real fillet over `keep`. Edges that each fillet fine alone can fail together.
- **Select edges by geometry, not by index.** Use `cq.selectors.BoxSelector` with a small margin around the edge centre, or a predicate on `e.startPoint()`, `e.endPoint()` and `e.Center()`. For example, "all three points lie on the plane x = LIP_FREE". Chain `.edges("|X")` to filter by direction.
- **Restrict to straight edges** (`e.geomType() == "LINE"`) when you fillet a big outer set. Arcs from earlier fillets cause most failures.
- **Inside fillets** (wall to floor) are easiest as part of the 2D profile, or as the first fillet right after the main cavity cut.
- A chamfer fails in the same places a fillet does, so it is no easy fallback.
- When an experiment may crash, run it in a separate `uv run python -c ...` process so the main session keeps going.

## Rotations and orientation

- `rotate((0,0,0), (0,1,0), 90)` maps (x, y, z) to (z, y, -x). With -90 you get (-z, y, x). A sign error once sent the closed end up instead of down.
- Add a slab test after every rotation for export: intersect thin boxes near z = 0 and near the top, then compare their volumes.
- Translate the exported part so its bounding box minimum is (0, 0, 0).

## Workplanes for holes in side walls

- `cq.Workplane("XZ")` has its normal along -Y. Use `extrude(d, both=True)` centred in the wall, so the direction does not matter.
- To control the hexagon direction, build a custom plane with `cq.Plane(origin=..., xDir=..., normal=...)`. `polygon(6, d)` puts its first corner on the local X axis. Set `xDir` to the print-up direction so the hexagon points up when printed.
- **`pushPoints([])` with an empty list does not do nothing.** It places one shape at the workplane origin. This once cut a stray notch into a corner when a vent area became too small for any holes. Skip the cut when the point list is empty.
- Grid helper: return centres that fit fully inside an area (centre ± size/2) and skip keep-out circles, such as solid pads around mount points.

## Rendering views

- `cq.exporters.export(shape, "x.svg", opt={"projectionDir": ..., "showHidden": False})` gives a quick hidden-line view. Rasterize it with `uv run --with resvg-py`.
- For shaded, labeled views use `scripts/render_views.py`, which uses VTK (installed with CadQuery) offscreen.
- Matplotlib 3D renders of big meshes look wrong because it sorts depth per triangle. Do not use it for model views. It is fine for 2D section plots built from `solid.intersect(thin box).Edges()`.
- The built-in browser pane cannot open local `file://` SVGs, so render to PNG and Read that.

## Misc

- `uv init --bare --python 3.12` may still use a newer Python. CadQuery 2.8 works on 3.14.
- `vtk`, `OCP` and `cadquery` install from wheels on macOS arm64 through `uv add cadquery`. No conda is needed.
- STEP import for later rendering: `cq.importers.importStep(path).val()`.

## 3MF for Bambu Studio and OrcaSlicer

- Bambu Studio re-centres each mesh on its bounding box. Put vertices around the centre, and set the build item and `assemble_item` z to half the part height. With z = 0 the part loads half below the bed, and slicing fails with "Nothing to be sliced".
- A file tagged `Application = BambuStudio-...` without `Metadata/project_settings.config` crashes the command-line slicer (exit code 139).
- Object settings in `Metadata/model_settings.config` (`<metadata key="layer_height" value="0.28"/>` under `<object>`) override the project process. The G-code header shows the project value, so verify with the layer count.
- The command line `--load-settings` with stock profiles from the app bundle fails, because those profiles inherit from others it does not resolve. Use a project saved by the app as the template.

## Fillet trial loops are the slow part

Adding risky edges to a fillet one at a time, with a full `fillet()` as the test for each, multiplies the cost: 8 fillet operations for one result. Try the complete set once and fall back to the one-by-one loop only when that raises. Classify edges with the three points of each edge computed once and compare edges by `hashCode()` in a set, not with nested `isSame()` loops. On the mixer sleeve this took a warm build from 2.5 s to 1.1 s with identical geometry.

## Loft exact wires, not point polygons

A loft between two 128-point polygons gives 128 ruled faces, and every boolean after it pays for all of them: the gutter outlet spent 4.6 s of a 4.7 s build in three cuts and four unions. Build the profiles from `Edge.makeThreePointArc` and `Edge.makeLine`, assemble with `Wire.assembleEdges`, and give both wires the same number of edges in the same order and direction. Split the round end's arcs in proportion to the lengths of the other profile's edges, or the ruled surface twists and the wall thickness wanders. Same part: 21 faces, 0.3 s, and smooth surfaces in the STL.

## A cut that changes nothing

`part.cut(tool)` can return the part unchanged, with no error, when a face of the tool lies exactly on a face of the part (here the inner loft ended on the collar's face). Check the volume after a cut you rely on. Fix it by cutting before the union that creates the coincidence, or by moving the tool face a little past the boundary.

## A lip that reaches down prints in air

A lip whose tip hangs lower than its root, to rest on the device's edge, has its lowest point at the tip with nothing under it: the first layers of the wedge print in air. For a flat print the fill under a lip must grow out of the wall, lowest at the wall and highest at the tip, which is why the mixer sleeve's lips hover above the mixer instead of touching it. A touching lip needs supports or a different print orientation.
