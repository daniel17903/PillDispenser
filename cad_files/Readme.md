Based on https://github.com/Shaztech/Pilldispenser

# Required parts:

- P8 - SG90 Servo 180° PWM Analog (blue type is fine) [1x per tray], fixed with 2x S1
- Round magnets Ø4 x 2mm (recesses in the bottom are Ø4.1 x 2mm) [4x bottom, 4x lid]
- P9 - Ball pen springs (0.4x4.5x18mm) [3x per tray]
- S1 - Torx Screws #2 x 3/8" - McMaster #99512A159 [8x Base, 10x per tray]
- S2 - Torx Screws #4 x 1/2" - McMaster #99512A219 [8x Base, 6x per tray]
- P10 - Ø1.5mm x 14mm rod (I used Aluminium TIG rod, you can use anything that fit) [1x per tray]
- P11 - Ø1.5mm x 12mm rod (I used Aluminium TIG rod, you can use anything that fit) [1x per tray]
- P12 - Torsion spring - McMaster #9271K71 [1x per tray], on P11, presses part_3 against the pill ring

# Files

The original Shaztech files were superseded by these modified versions and removed:

- `bottom.stl` – housing / bottom
- `Assembly_parts/part_1.stl` … `part_6.stl` – mechanism parts
- `tray_parts.stl` – pill ring with ratchet teeth
- `top.stl` – lid (pins face into the housing, held by the magnets)
- `foot.stl` – stand, the wheel stands upright with the outlet facing down

See `explosionszeichnung.png` for an exploded view. The mechanism positions were derived from a photo of the assembled mechanism (accurate to about 1–2 mm).

`render_explosion.py` regenerates the image (run it from this folder: `python3 render_explosion.py explosionszeichnung.png`).
