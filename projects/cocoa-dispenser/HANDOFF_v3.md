# Cocoa dispenser: handoff for version 3 (vibrating sieve, ratchet tapper)

Project: `projects/cocoa-dispenser` in the printforge repo. Follow `skills/cad-print-design/SKILL.md`.
Run from this folder: `uv sync`, then `uv run cocoa_dispenser.py` (writes STEP, STLs, labels),
`uv run check_part.py cocoa_dispenser.py`, `uv run render_views.py cocoa_dispenser.step --labels labels.json --out views`,
`uv run make_3mf.py cocoa_dispenser_plate.stl --settings print_settings.json --template bambu_p1s_0.4.config --out cocoa_dispenser.3mf`,
`uv run cocoa_dispenser.py --serve --port 8768` for the configurator (also in `.claude/launch.json`).
The views were rendered in a headless Linux VM with `xvfb-run -a`; on the Mac, VTK renders without it.

## State of the files

- `cocoa_dispenser.py`: **version 2** (push-to-turn rotating shutter). Builds, all checks pass.
- `cocoa_dispenser_v1.py.bak`: version 1 (up-and-down agitator above a 1 mm sieve, no shutter).
- `cocoa_dispenser_v2.py.bak`: copy of version 2.
- `views/`, `renders/` (Codex AI images of v1), `renders/v2/` (AI images of v2), `README.md` (v2).
- The 3MF and the STLs are v2. Nothing is committed to git.
- An edit toward "v2 + drop chamber + aperture disc" was started and rejected; it is NOT in the file.

## Why version 3

Reference product: LatteShot by relief_art (Cults3D). Photos of its internals show:
- The powder lies on a **thin printed sieve disc with fine holes** inside the lens barrel. Three
  sieve discs with a tab, different hole sizes (fine for cinnamon, larger for cocoa).
- **No shutter.** Fine holes hold the powder at rest (cocoa bridges). The shutter button slides a
  **toothed rack past a tongue**; each tooth is one tap. One press = a burst of taps = an even,
  fine dust. (Bought parts there: one 608 bearing, rubber bands, M3x20. We print everything.)
- The stencil card lies flat under the sieve, near the cup.

Our v2 rotating shutter works on paper but has 9 parts and prints the hole pattern (six wedges,
empty centre) onto the foam because the sieve is 3 mm above the stencil. v3 is simpler and matches
the proven design.

## Version 3 design (all printed, 7 parts + nothing bought)

Keep the v2 file structure (printer block, parameter groups with emoji headings and [min:max],
`build()`, `device()`, `features()`, `labels()`, `parts(press)`, `PRINT_FLIP`, per-part STLs,
`merge_stls` plate, slab tests, interference checks at rest and at full press). Start from
`cocoa_dispenser.py` (v2) and remove the rotor, pivot post, keeper, vanes, twisted rod, square
follower. Use frame: Z up, z = 0 at the cup rim, stencil tab to -Y.

Parts:
1. **Stand**: base ring on the cup rim (STAND_D 112, WINDOW_D 70), stencil slot open to the
   front (SLOT_PLAY 0.4, SLOT_SIDE 0.3), then a **drop chamber** tube above the slot
   (DROP_H 15, CHAMBER_D 80, wall 6 lines) so the hole pattern mixes before it lands, a top
   ring under the body flange and the locating rim (RIM_H 3, RIM_PLAY 0.5).
2. **Stencil**: disc STENCIL_D 90, 6 layers thick, HEART_W 52 heart cut-out (keep
   `heart_points`), lip STENCIL_LIP 3 (3 lines wide) so it is a tray, pour spout SPOUT_W 12 as a
   gap in the lip at the back (+Y), pull tab TAB_W 30, TAB_L 18 with a finger hole.
3. **Body**: hopper HOP_D 72, HOP_H 75, WALL 5 lines, flange FLANGE_D 104 x 15 layers.
   Floor = **sieve plate** SIEVE_T 6 layers, holes over the whole floor: SIEVE_HOLE 0.8,
   SIEVE_PITCH 1.6 hex grid (web 0.8 = ~2 lines; assert web >= 2*LINE and hole >= 2*NOZZLE),
   SIEVE_D 60 (keep the 45-degree cone from SIEVE_D to the hopper bore). Give the hole size a
   slider [0.6:1.2]: 0.8 for cocoa, 0.6-0.7 for cinnamon (needs a 0.2 nozzle or a test).
   Optional: make the sieve a separate drop-in disc with a tab (as LatteShot) so hole sizes can be
   swapped: `SIEVE_SEPARATE = True` -> body floor is a ring ledge, disc SIEVE_D - 0.6 sits on it.
   Default False to keep 7 parts.
4. **Rod**: square ROD_SQ 6, straight (no twist). On one face a **rack**: triangular teeth,
   RACK_PITCH 1.5, RACK_DEPTH 0.8, over RACK_L = STROKE + 6 mm, placed so the tongue is on the
   rack for the whole stroke. Bottom of the rod ends 2 mm above the sieve at full press (ROD_FOOT
   = STROKE + 2). A small flat **agitator foot** (disc 20 mm, 2 mm thick) at the rod bottom is
   optional (AGI_FOOT = True): it also stirs the cocoa 2 mm above the sieve at full press.
5. **Lid**: push-fit plug (LID_PLUG 6, LID_FIT 0.2), plate LID_T 16 layers, **square guide hole**
   ROD_SQ + 2*ROD_PLAY so the rack face stays aligned, spring seat SEAT_DEPTH 8 layers, and the
   **striker tongue**: a cantilever finger in the lid hub, TONGUE_T 2 lines (0.9 mm) thick,
   TONGUE_L 8 mm long, TONGUE_W 4 mm, pointing at the rack face with TONGUE_BITE 0.5 mm
   engagement into the teeth. The tongue prints in the lid's print orientation (lid upside down ->
   tongue stands vertical, fine). The tongue root sits in a slot in the hub so it can flex; the free
   end carries a small rounded tip. Each tooth deflects the tongue 0.5 mm and lets it snap back: one
   tap into the lid, which is push-fit into the body, which carries the sieve.
6. **Button**: BTN_D from the spring + skirt wall, square socket ROD_PRESS 0.05 (glue), skirt
   hides the spring and lands on the lid at full press (STROKE 10), finger dimple.
7. **Spring**: keep the PETG **wave spring** from v2 exactly (`wave_ring`, `wave_spring`,
   PRELOAD 2, WS_* parameters, rate estimate). `PRINT_SPRING = False` keeps the bought-spring path.

Checks to add:
- rack: TONGUE_BITE < RACK_DEPTH; tongue stress: deflection 0.5 mm on an 8 mm PETG finger 0.9
  thick is fine (strain ~0.5*3*0.9/8^2*... keep < 2%); assert TONGUE_L >= 6.
- the tongue tip stays on the rack over the whole stroke (rest and pressed).
- interference: tongue vs rod must overlap by exactly the bite at rest (the only allowed
  overlap; exclude the tongue from the no-overlap assert or model the tongue deflected).
- all existing checks (one solid per part, slab test, bed fit, plate layout no overlap,
  spring preload and solid height).

Dose logic to explain in the README: one press = ~6 taps down + 6 up (STROKE / RACK_PITCH each
way). Dose is set by SIEVE_HOLE, by the number of presses, and by the amount of cocoa in the
hopper (more cocoa = more pressure on the sieve = larger dose; say "fill 20-30 mm").

Print settings (`print_settings.json`): 0.2 mm layers, 3 walls, 15 % infill, no supports, rod
standing with a brim. PETG for spring, rod, lid (tongue); food-safe PETG/PLA elsewhere.

Plate layout for 256 mm (keep the `layout` dict and the overlap assert): stand 112, body 104,
stencil 90 x 120, lid 72, button ~32, rod 9 x 9 standing, spring 22.

Deliver: STEP (rest + pressed), per-part STLs, plate STL, 3MF, `labels.json`, `views/sheet.png`,
a section view at rest and pressed (`views/section_rest_pressed.png`, cut at y = 0 through the
tongue and rack), a close-up of the tongue on the rack, README updated to v3 with assembly
steps, and `renders/v3/` Codex images if wanted (prompt pattern in `renders/v2/prompt.txt`;
run `~/.local/bin/codex exec --skip-git-repo-check -s workspace-write -i <refs> - < prompt.txt`
in that folder; the Homebrew codex is an old 0.22 and hangs, use `~/.local/bin/codex` 0.163).

Say in the README: rebuilt, not printed. Test the tongue first: print the lid alone and the rod,
click the rack past the tongue by hand; if the taps are weak, raise TONGUE_BITE to 0.7 or make the
tongue 3 lines thick; if it breaks, lengthen TONGUE_L.
