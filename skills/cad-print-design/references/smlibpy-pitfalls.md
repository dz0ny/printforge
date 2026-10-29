# smlibpy pitfalls

What failed or surprised us while building parts with smlibpy 0.6.2, and what works instead.
Read this before you write fillets, holes, cuts through rounded corners or rotations.
`references/cadquery-pitfalls.md` stays for reference when you port another CadQuery script.

## API shape

- `part.volume` and `part.area` are properties. `part.volume()` raises `TypeError: 'float' object is not callable`.
- `part.bbox()` is a method. Its `.size`, `.min` and `.max` are vectors that unpack to `(x, y, z)`.
- Every primitive is centred on the origin. Use `align=(Align.CENTER, Align.MIN, Align.MIN)` to start a box at y = 0 and z = 0.
- `Cylinder` and `Cone` have no direction argument. They stand on Z, so turn them:
  - `.rotate(X, 90)` turns +Z to -Y.
  - `.rotate(X, -90)` turns +Z to +Y.
  - `.rotate(Y, 90)` turns +Z to +X.
- `Hole`, `CounterSinkHole` and `CounterBoreHole` are drilling tools. They start at the origin, with the sink there, and point down to `-depth`. Turn the tool so that -Z points into the wall, then move it onto the face. For a back plate at y = 0..WALL drilled from the inside face, use `CounterSinkHole(...).rotate(X, -90).translate(x, WALL, z)`.
- A sketch is drawn on XY around the origin: `Rectangle(w, d, fillet=r).extrude(h)` gives a block with rounded vertical edges from z = 0 to h.
- Selections are lists. Filter them in Python: `[e for e in part.edges().parallel_to(Y) if e.center().z > top - 1]`.

## Geometry

- **A straight cut through a rounded corner leaves a sliver.** In the remote holder, a box that cut the front wall down met the rounded inner corner of the pocket. A wall 0.04 mm thick was left behind. Start the cut where the corner starts to curve (`y = OUT_D - R_OUT`), so the side walls end at full thickness. `check_part.py` found this. A render did not show it.
- A flat face that only touches a cylinder (tangent) makes a fuse raise `ModelingError`. Let the bodies overlap by a fraction of a millimetre.
- A through-hole tool must be longer than the wall is thick, or a thin skin stays. A centred cylinder reaches half its height on each side.
- **`loft` can twist a profile change.** A ruled loft from the gutter's D profile to a round spigot came out lopsided: its sections ran from y -44.7 to +38.1 instead of +-44.7, and it held 15,400 mm³ too little. The kernel pairs the two outlines by its own start points. Build such a funnel from one `ruled(a, b)` face per pair of matching edges, cap both ends with `make_face(Wire(edges))`, and `stitch` it closed (`projects/gutter-outlet`, `ruled_loft`). Check a loft by its middle sections: symmetric profiles give symmetric sections.
- Fillets that meet at a corner: one `fillet(top + end, r)` call worked where two calls in a row failed with "unable to process rollover" on the second.
- **An assembly is a list, not a fuse.** Two pieces whose plates touch along a face merge into one solid when fused. Return `[left, right]` from `build()`. `export_step` and `export_stl` take the list and write separate bodies. `import_step` of such a file returns a `ShapeList` of parts.
- A boolean can leave faces that meet with tiny gaps. `part.volume` then warns "the faces of this part do not meet exactly", here about 4e-5 of the volume, while `is_valid()` stays True. The gutter outlet does this only for some settings. It is harmless for printing.
- Fillet before you shell when the walls must be rounded too. Large fillets next to thin walls fail: shell first and use smaller radii.

## Checking

- `is_valid()`, `len(part.solids()) == 1`, `bbox().size` and `volume` after every step. The volume must change in the expected direction.
- `render(..., view={"direction": d, "up": u})` returns a picture with `.frame` (`scale` in px per mm, `mid_x`, `mid_y`). The screen right is `normalize(up x to_camera)` and the screen up is `to_camera x right`. `render_views.py` uses this to place its name tags.
- `part.raycast(origin, direction)` returns the hits nearest first. An empty list means the ray left the part. `render_views.py` hides a tag when the ray from it to the camera hits the part.
- `check_part.py` casts its thin-wall rays from the centres of mesh triangles, picked by area with a fixed seed. A coarse mesh can have no triangle centre near a thin edge, so it cannot see that edge. The CadQuery gutter outlet passed with 0 mm² of thin wall; the smlibpy port of the same geometry, within 0.1 mm, found 6 mm². Look at where the thin samples are before you decide that a port changed the part.
- `a & b` gives the shared volume. Wrap it in `try` when the parts can miss each other.

## Drawings

- `to_svg(drawing_views(part))` writes arcs as exact `A` commands, other curves as polylines, and the viewBox in model mm. The configurator page reads this SVG directly, arcs included.
- Do not sample projected curves yourself with `edge.point_at`. On the gutter outlet that took 93 s for one view. `to_svg` of the same view took 0.5 s.
- `drawing_views` has no iso view. The worker turns the part so that the iso direction looks from the front, then draws the front view.

## Kernel limits found while porting

- **Crashes.** `drawing_views` and `outline` along a tilted direction killed the process (signal 11) on the mixer sleeve, at every direction tried. Views along the axes work. The configurator runs each view in a forked copy (`guarded()` in its server), so a crash costs one view, not the worker. smlibpy guards `fillet`, `shell` and some other steps itself, but not the drawings.
- **Booleans on faces that lie on each other.** The flat end rings of the cocoa wave spring had their inner and outer faces on the same cylinders as the lofted band, and every fuse failed. Making the end rings 0.1 mm wider per side fixed it. A loft whose last section repeats the first is also a bad operand: use `closed=True`.
- **Fillets that meet at corners.** On the sleeve, the kernel's overlap test for small lip-end edges gave a different answer for the same call. Round the reliable group in one call, then try each doubtful edge alone on the current part, and keep a result only when the call succeeds and `is_valid()` is True.
- **A fillet along a tangent chain.** A floor edge that runs on tangentially into floor fillets must round the whole chain, and failed at the far corner. The sleeve keeps that one edge sharp.
- **Cost of many small features.** An intersection meshes its operands: each check of the cocoa body with its 1,069 holes took seconds, and the build took 257 s. Checks against the body with a plain floor brought it to 35 s. Cut many holes from the 2D outline before the extrusion (14 s against 31 s), and mesh tiny holes with `angle=30` (6 s against 82 s at `angle=6`).
- **Old CadQuery selectors.** `RadiusNthSelector(0, directionMax=True)` picked the smallest circle, not the largest. The cocoa ports keep the edges it really picked, so the parts print as before.

## MCP server

- The `docs` tool takes `keys`, for example `docs(keys=["SKILL", "recipes/verification"])`.
- Scripts stop after 120 s unless you ask for more time.
- A session holds its own variables. Pass `session="new"` once, then the `s-...` id it returns. A second, unrelated part is a second session.
- `save(format="step", path=...)` writes the exact model. Give an absolute path in the project folder.

## Configurator comments

- A `[min:max]` range ends the comment. A period after it is allowed: `REM_W = 50.0  # Width of the remote. [30:90].` The period keeps each comment line one sentence, which the comment style checker needs.
