# Cocoa dispenser with stencil

Push-button cocoa duster for latte art. Put it on the cup, slide a stencil in,
press the button 2-4 times. The agitator moves down through the cocoa and pushes
it through the sieve; the stencil shapes it. The spring lifts the button back.

![views](views/sheet.png)
![section, rest and pressed](views/section_rest_pressed.png)

## Parts

| Part | Print orientation | Notes |
|---|---|---|
| Stand | flat, as used | sits on the cup rim; stencil slot open on top, no bridges |
| Stencil | flat | heart cut-out, 1.2 mm; pull tab at the front |
| Body | flange down | sieve prints as the first 6 layers (1.0 mm holes, 2.0 mm pitch) |
| Lid | upside down | push-fit plug, rod guide hub, spring seat |
| Plunger | agitator down | 91 mm rod; 45 degree collar underside |
| Button | upside down | skirt hides the spring and stops the stroke on the lid |

Buy: one compression spring, OD 9-10 mm, wire 0.6-0.8 mm, free length about 25 mm
(it works at 21.6 mm at rest and 11.6 mm pressed).

## Assembly

1. Put the plunger rod up through the lid from below (the collar stops under the hub).
2. Put the spring over the rod into the seat on the lid.
3. Press the button onto the rod top, a drop of glue in the socket.
4. Fill the body with cocoa, push the lid in.
5. Stand on the cup, stencil into the slot, body onto the stand.

## Files

- `cocoa_dispenser.py` the model; `uv run cocoa_dispenser.py` writes everything below.
- `cocoa_dispenser.step` assembly at rest, `cocoa_dispenser_pressed.step` at full press.
- `stand.stl`, `stencil.stl`, `body.stl`, `lid.stl`, `plunger.stl`, `button.stl` per part, in print orientation.
- `cocoa_dispenser_plate.stl` and `cocoa_dispenser.3mf` all six on one 256 mm plate.
- `uv run cocoa_dispenser.py --serve` opens the configurator on port 8768.

Rebuilt, not printed. Check first: the sieve holes (1.0 mm) stay open, the cocoa
does not fall through without a press, and the lid push fit (0.2 mm per side).
