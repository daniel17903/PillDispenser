Based on https://github.com/Shaztech/Pilldispenser

# Required parts:

- P8 - SG90 Servo 180° PWM Analog (blue type is fine) [1x per tray], fixed with 2x S1
- Round magnets Ø4 x 2mm [4x bottom, 4x lid] - [bought here](https://www.ebay.de/itm/256857279655?var=557385005242)
- P9 - Ball pen springs (0.4x4.5x18mm) [2x per tray: one under the lever (part_2), one behind part_4] - [bought here](https://de.aliexpress.com/item/1005004899133236.html)
- S1 - Torx Screws #2 x 3/8" - McMaster #99512A159 [5x per tray: 2x servo, 2x part_6/part_2, 1x part_5]
- P10 - Ø1.5mm x 14mm rod (I used Aluminium TIG rod, you can use anything that fit) [1x per tray] - [bought here](https://www.amazon.de/dp/B0D2V6WVT4)
- P11 - Ø1.5mm x 12mm rod (I used Aluminium TIG rod, you can use anything that fit) [1x per tray] - [bought here](https://www.amazon.de/dp/B0D2V6WVT4)
- P12 - Torsion spring - McMaster #9271K71 [1x per tray], on P11, presses part_3 against the pill ring

# Electronics (not shown in the exploded view)

- Seeed Studio XIAO ESP32S3 (dual-core 2.4 GHz, Wi-Fi, BLE 5.0, battery charging supported) [1x] - [bought here](https://www.ebay.de/itm/276152913715)
- LiPo battery 3.7 V, 3000 mAh, approx. 65 x 35 x 20 mm [1x]
- IRLB8721 MOSFET (switches the servo power) [1x]
- On/off switch [1x]

# Files

The original Shaztech files were superseded by these modified versions and removed:

- `bottom.stl` – housing / bottom
- `Assembly_parts/part_1.stl` … `part_6.stl` – mechanism parts
- `tray_parts.stl` – pill ring with ratchet teeth
- `top.stl` – lid (pins face into the housing, held by the magnets)
- `foot.stl` – stand, the wheel stands upright with the outlet facing down

See `exploded_view.png` for an exploded view. The mechanism positions were derived from a photo of the assembled mechanism (accurate to about 1–2 mm).

`render_exploded_view.py` regenerates the image (run it from this folder: `python3 render_exploded_view.py exploded_view.png`).
