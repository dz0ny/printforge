# CAD configurator

A local web page that exposes the parameters of a CadQuery model script, rebuilds
the part when they change, and shows the result next to a ghost of the device the
part is designed around. It is the PrintForge answer to MakerWorld's Parametric
Model Maker, with CadQuery kept as the modelling language.

## Why

Adjusting a sleeve to a device means editing numbers at the top of a script,
rebuilding, and looking at renders. The page turns that into sliders and a live
3D view. The device stays a hidden inner object: it is never exported, but you can
see it inside the shell and change its size.

## Decisions

- CadQuery stays. CadQuery cannot run in the browser (its sketch solver needs
  nlopt and casadi, which have no Pyodide builds), so a small local server
  rebuilds the model. OpenSCAD and build123d were considered and rejected to keep
  every existing script working.
- No new parameter format. The server reads the top-level `NAME = number|bool`
  lines above the first function with the `ast` module. The trailing comment is
  the description; an optional `[min:max]` at its end sets a slider range. A
  comment line above a block of settings is the group title. Derived values such
  as `WALL = 8 * LINE` stay hidden and recompute.
- The device is a plain `device()` function in the model that returns a CadQuery
  shape. The page draws it translucent with a toggle.
- Builds run in one warm worker subprocess, started with `uv run --project` in
  the model's own folder so it uses the project's locked CadQuery. The worker
  imports CadQuery once and keeps the last part, so a rebuild costs only the
  model's own time (about 5 s for the mixer, against 117 s for a cold process in
  a separate environment) and the STEP is exported only on download. A crash
  shows up in the build log and the worker restarts on the next build. Rebuild
  is a button, with an optional auto-rebuild.
- "Save to script" writes the values back into the Python file. The committed
  script stays the source of truth.
- Each project gets an entry in `.claude/launch.json`, so the page opens in the
  Claude browser pane with one command.

## Parts

- `skills/cad-print-design/scripts/serve.py`: the server and build worker.
- `skills/cad-print-design/scripts/configurator.html`: the page.
- A `device()` function and `[min:max]` ranges in each model script.
