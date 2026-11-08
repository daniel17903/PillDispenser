# Renders explosionszeichnung.png from the STL files in this folder.
# Run from cad_files/:  python3 render_explosion.py explosionszeichnung.png
# Requires: pip install numpy matplotlib trimesh fast_simplification
#
# Coordinates are in the frame of bottom.stl (floor at z=0, open side +z).
# Mechanism poses come from a photo of the assembled mechanism (camera pose
# fitted to the screw posts) plus the hole positions in the STL files:
#   - part_2 and part_6 share the two S1 screws (holes 20 mm apart)
#   - P11 goes through part_6 / part_2 / part_3 at the pawl end (pivot of part_3)
#   - P10 sits in the floor pin, goes through part_2 and is held by part_5,
#     whose second hole (14 mm away) takes the third S1 screw
#   - servo screw holes, spring bores and magnet recesses are taken from bottom.stl
import sys
import numpy as np
import trimesh
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

OUT = sys.argv[1] if len(sys.argv) > 1 else 'explosionszeichnung.png'
BC = np.array([0.5, 3.48])  # axis of bottom.stl
LIGHT = np.array([0.35, -0.55, 0.75]) / np.linalg.norm([0.35, -0.55, 0.75])

S1A, S1B = np.array([-38.6, -2.0]), np.array([-18.7, -5.6])   # screws on the lever
PIN = np.array([-8.5, -7.6])                                    # floor pin (P10)
S3 = np.array([5.5, -6.4])                                      # screw in part_5
U = (S1B - S1A) / np.linalg.norm(S1B - S1A)                     # lever direction (+x-ish)
P11 = S1A - 15 * U                                              # pawl pivot
MAGNETS = [(-22.9, 41.6), (44.0, 16.3), (43.9, -10.7), (-31.1, -28.3)]  # recesses on top of the posts


def ang(v):
    return np.degrees(np.arctan2(v[1], v[0]))


def rz(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])


def centre_for(hole_local, target, yaw, flip=False):
    h = np.array(hole_local, float) * ([-1, 1] if flip else [1, 1])
    return np.asarray(target) - rz(yaw) @ h


UPRIGHT = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]).T   # local x->z, y->y, z->-x
FLIP = np.diag([-1, 1, -1])                                # upside down (about local y)
yaw26 = ang(U) - 90                                        # local +y -> lever direction
yaw2 = ang(-U) - 90                                        # part_2: hook end (+y) at the pawl
yaw5 = ang(S3 - PIN) - 90
yaw3 = 88.8                                                # claw tip towards the ratchet teeth
POSES = {  # part: (local->bottom rotation, yaw, (x, y) of bbox centre, z of bottom face)
    1: (UPRIGHT, 0.0, (-43.8, 11.6), 7.5),
    2: (np.eye(3), yaw2, centre_for((-1.62, 7.5), S1A, yaw2), 2.5),
    3: (np.eye(3), yaw3, centre_for((6.04, -1.8), P11, yaw3), 2.5),
    4: (np.eye(3), -90.0, (60.4, 4.1), 2.0),
    5: (FLIP, yaw5, centre_for((0, 5.93), S3, yaw5, flip=True), 14.5),
    6: (np.eye(3), yaw26, centre_for((0, -4.0), S1A, yaw26), 14.5),
}
NAMES = {1: 'Servohebel', 2: 'Hebel', 3: 'Klinke', 4: 'Rastblock', 5: 'Halter für P10', 6: 'Platte 4 mm'}
MCOL = {1: '#e07b39', 2: '#e0a339', 3: '#c9b52e', 4: '#4fa3a5', 5: '#d46a8c', 6: '#9a6cc6'}
# explosion offsets (dx, dy, dz) per element
OFF = {1: (-18, 40, 36), 2: (0, 0, 32), 3: (0, 0, 32), 4: (26, 0, 24), 5: (0, 0, 74), 6: (0, 0, 52),
       'servo': (0, 40, 36), 'p10': (0, 0, 16), 'p11': (0, 0, 78), 'p12': (0, 0, 20), 'spring2': (0, -16, 26),
       'spring4': (12, 0, 24), 'mag': (0, 0, 26), 'screws2': (0, 0, 92), 'screw3': (0, 0, 96)}


def load(f, n=None):
    m = trimesh.load(f, force='mesh')
    if n and len(m.faces) > n:
        m = m.simplify_quadric_decimation(face_count=n)
    return m


def place(m, R0, yaw, xy, z0):
    a = np.radians(yaw)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    V = m.vertices - np.r_[m.bounds.mean(0)[:2], m.bounds[0][2]]
    V = (Rz @ R0 @ V.T).T
    V -= np.r_[(V.min(0) + V.max(0))[:2] / 2, V[:, 2].min()]
    return trimesh.Trimesh(V + np.r_[xy, z0], m.faces, process=False)


def moved(m, off):
    m = m.copy(); m.apply_translation(off); return m


def cyl(p0, p1, r, sections=20):
    return trimesh.creation.cylinder(radius=r, segment=[p0, p1], sections=sections)


def screw(tip, direction, d, length):
    direction = np.asarray(direction, float) / np.linalg.norm(direction)
    tip = np.asarray(tip, float)
    top = tip + direction * length
    head = cyl(top, top + direction * d * 0.75, d * 0.95, 24)
    return trimesh.util.concatenate([cyl(tip, top, d / 2, 12), head])


def helix(p0, axis, length, od, wire=0.45, turns=9, n=300):
    t = np.linspace(0, 2 * np.pi * turns, n)
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    u = np.cross(axis, [0, 0, 1]) if abs(axis[2]) < 0.9 else np.array([1., 0, 0])
    u /= np.linalg.norm(u); w = np.cross(axis, u); r = (od - wire) / 2
    pts = np.asarray(p0, float) + np.outer(t / t[-1] * length, axis) + r * (np.outer(np.cos(t), u) + np.outer(np.sin(t), w))
    return trimesh.util.concatenate([cyl(a, b, wire, 6) for a, b in zip(pts[:-1], pts[1:])]), pts


def torsion_spring(c, z0, legs):
    coil, pts = helix((c[0], c[1], z0), (0, 0, 1), 3.5, 5.0, turns=4, n=160)
    parts = [coil]
    for p, d in zip((pts[0], pts[-1]), legs):
        parts.append(cyl(p, p + np.r_[d, 0] * 9, 0.45, 6))
    return trimesh.util.concatenate(parts)


def servo_sg90():
    """SG90 lying on its side: shaft along -x at (y=14, z=11), tabs screwed to the posts."""
    xb, yc, zc = -13.6, 19.5, 11.0
    body = trimesh.creation.box(bounds=[[xb - 22.7, yc - 11.4, zc - 6.1], [xb, yc + 11.4, zc + 6.1]])
    tabs = trimesh.creation.box(bounds=[[xb - 18.4, yc - 16.1, zc - 6.1], [xb - 15.9, yc + 16.1, zc + 6.1]])
    bump = cyl([xb - 22.7, 14, zc], [xb - 26.7, 14, zc], 5.9, 32)
    bump2 = cyl([xb - 22.7, 20.5, zc], [xb - 25.7, 20.5, zc], 3.0, 24)
    shaft = cyl([xb - 26.7, 14, zc], [xb - 29.7, 14, zc], 2.4, 20)
    blue = trimesh.util.concatenate([body, tabs, bump, bump2])
    screws = [screw([xb - 8.5, y, zc], [-1, 0, 0], 2.0, 9.9) for y in (yc - 13.9, yc + 13.9)]
    return blue, shaft, trimesh.util.concatenate(screws)


def shade(m, col):
    s = np.abs(m.face_normals @ LIGHT) * 0.62 + 0.38
    return np.clip(np.array(matplotlib.colors.to_rgb(col))[None] * s[:, None], 0, 1)


def draw(ax, items, lims, elev, azim, box=None):
    polys = np.concatenate([m.vertices[m.faces] for m, _ in items])
    cols = np.concatenate([shade(m, c) for m, c in items])
    ax.add_collection3d(Poly3DCollection(polys, facecolors=cols, edgecolor='none'))
    ax.set_xlim(*lims[0]); ax.set_ylim(*lims[1]); ax.set_zlim(*lims[2])
    ax.set_box_aspect(box or [l[1] - l[0] for l in lims])
    ax.view_init(elev=elev, azim=azim); ax.set_axis_off()


def callout(ax, anchor, pos, text, color='#222', size=10):
    ax.plot(*zip(anchor, pos), '-', color='#555', lw=0.7, zorder=45)
    ax.text(*pos, text, fontsize=size, ha='center', va='center', color=color, zorder=50,
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#999', alpha=0.95))


def guide(ax, a, b):
    ax.plot(*zip(a, b), '--', color='#333', lw=0.8, zorder=40)


bottom = load('bottom.stl')
ring = load('tray_parts.stl'); ring.apply_translation([BC[0] - 3.15, BC[1] + 0.76, 0])
lid = load('top.stl'); lid.apply_transform(np.diag([-1, 1, -1, 1])); lid.apply_translation([BC[0] + 0.17, BC[1] + 1.37, 22])
foot = load('foot.stl')
mech = {i: place(load(f'Assembly_parts/part_{i}.stl', 5000), *POSES[i]) for i in POSES}

fig = plt.figure(figsize=(18, 12.5))
fig.text(0.5, 0.965, 'Pillenspender – Explosionszeichnung', ha='center', fontsize=20, weight='bold')
fig.text(0.5, 0.94, 'Reihenfolge: ① Boden  →  ② Mechanik  →  ③ Fächerring  →  ④ Deckel  →  ⑤ in den Standfuß stellen',
         ha='center', fontsize=12, color='#444')

# ---------- main view: bottom + exploded mechanism ----------
ax = fig.add_axes([0.0, 0.12, 0.66, 0.84], projection='3d'); ax.set_proj_type('ortho')
items = [(bottom, '#7b97bd')]
for i, m in mech.items():
    items.append((moved(m, OFF[i]), MCOL[i]))
blue, shaft, sscrews = servo_sg90()
for m, c in ((blue, '#3c4fc4'), (shaft, '#f2f2f2'), (sscrews, '#9a9a9a')):
    items.append((moved(m, OFF['servo']), c))
p10 = cyl([*PIN, 2.2], [*PIN, 16.2], 0.75, 10)
p11 = cyl([*P11, 2.5], [*P11, 14.5], 0.75, 10)
items += [(moved(p10, OFF['p10']), '#c0803a'), (moved(p11, OFF['p11']), '#c0803a')]
items.append((moved(torsion_spring(P11, 6.0, [U, -rz(60) @ U]), OFF['p12']), '#555555'))
sp2, _ = helix((-30.5, -15.0, 10.0), (0, 1, 0), 18, 4.5)          # lever spring, bore in the post
sp4, _ = helix((46.0, 4.0, 8.0), (1, 0, 0), 18, 4.5)              # spring behind part_4
items += [(moved(sp2, OFF['spring2']), '#777'), (moved(sp4, OFF['spring4']), '#777')]
mags = [cyl([x, y, 18.2], [x, y, 20.2], 2.0, 20) for x, y in MAGNETS]
items += [(moved(mg, OFF['mag']), '#8c8c96') for mg in mags]
lever_screws = [screw([*p, 14.5 + 4 - 8], [0, 0, 1], 2.2, 9.5) for p in (S1A, S1B)]
items += [(moved(s, OFF['screws2']), '#9a9a9a') for s in lever_screws]
items.append((moved(screw([*S3, 20.5 - 9.5 + 1], [0, 0, 1], 2.2, 9.5), OFF['screw3']), '#9a9a9a'))
draw(ax, items, [(-92, 92), (-92, 92), (-5, 120)], elev=42, azim=-62, box=[184, 184, 125])

# dashed assembly lines and callouts
for i, m in mech.items():
    c = m.bounds.mean(0); o = np.array(OFF[i]); top = np.r_[c[:2], m.bounds[1][2]]
    guide(ax, top + [0, 0, 1], top + o - [0, 0, m.extents[2] + 1])
guide(ax, [*PIN, 16], [*PIN, 16 + OFF['p10'][2]])
guide(ax, [*P11, 15], [*P11, 2.5 + OFF['p11'][2]])
for p in (S1A, S1B):
    guide(ax, [*p, 19], [*p, 10 + OFF['screws2'][2]])
guide(ax, [*S3, 21], [*S3, 12 + OFF['screw3'][2]])
guide(ax, [-30.5, -6, 10], [-30.5, -15 - 16 + 18, 10 + 26])
guide(ax, [64, 4, 8], [46 + 12, 4, 8 + 24])
for x, y in MAGNETS:
    guide(ax, [x, y, 21], [x, y, 18 + OFF['mag'][2]])
guide(ax, [-25, 19.5, 17], [-25, 19.5 + 40, 17 + 36])
guide(ax, [-43.8, 14, 14.5], [-43.8 - 18, 14 + 40, 14.5 + 36])

hi = lambda m, off: np.r_[m.bounds.mean(0)[:2] + off[:2], m.bounds[1][2] + off[2]]
callouts = [
    (hi(mech[1], OFF[1]), (-85, 70, 80), 'part_1', MCOL[1]),
    (hi(mech[3], OFF[3]), (-95, -10, 62), 'part_3', MCOL[3]),
    (hi(mech[2], OFF[2]), (-60, -40, 62), 'part_2', MCOL[2]),
    (hi(mech[6], OFF[6]), (-48, -30, 100), 'part_6', MCOL[6]),
    (hi(mech[5], OFF[5]), (20, -38, 110), 'part_5', MCOL[5]),
    (hi(mech[4], OFF[4]), (88, -20, 70), 'part_4', MCOL[4]),
    (np.r_[-25, 59.5, 17 + 36], (-5, 85, 95), 'P8 Servo SG90 + 2× S1', '#3c4fc4'),
    (np.r_[S1A, 19 + 92], (-75, -20, 124), 'S1 (2×)', '#444'),
    (np.r_[S3, 21 + 96], (35, -20, 126), 'S1', '#444'),
    (np.r_[P11, 14.5 + 78], (-100, 15, 112), 'P11 Ø1,5×12', '#a0662a'),
    (np.r_[PIN, 16 + 16], (25, -60, 45), 'P10 Ø1,5×14', '#a0662a'),
    (np.r_[P11, 10 + 20], (-105, -30, 40), 'P12 Drehfeder', '#444'),
    (np.r_[-30.5, -22, 36], (-55, -75, 50), 'P9 Feder', '#444'),
    (np.r_[64, 4, 32], (90, 30, 55), 'P9 Feder', '#444'),
    (np.r_[MAGNETS[1], 46], (85, 60, 75), 'Magnete (4×)', '#555'),
]
for a, p, t, c in callouts:
    callout(ax, a, p, t, c)
callout(ax, np.r_[60, -60, 10], (75, -95, 10), '① Boden (bottom.stl)', size=11)
fig.text(0.03, 0.89, '② Mechanik', fontsize=13, weight='bold')
for k, i in enumerate(POSES):
    fig.text(0.03, 0.865 - k * 0.024, '■', color=MCOL[i], fontsize=14)
    fig.text(0.05, 0.867 - k * 0.024, f'part_{i}  {NAMES[i]}', fontsize=10.5)
fig.text(0.03, 0.71, 'Gestrichelte Linien: Einbauort im Boden', fontsize=9.5, color='#666')

# ---------- ring over the bottom ----------
ax = fig.add_axes([0.62, 0.62, 0.19, 0.30], projection='3d'); ax.set_proj_type('ortho')
draw(ax, [(bottom, '#7b97bd'), (moved(ring, [0, 0, 70]), '#8fb3a3')], [(-100, 100), (-100, 100), (-10, 110)], elev=30, azim=-68)
guide(ax, [*BC, 25], [*BC, 70])
fig.text(0.715, 0.62, '③ Fächerring (tray_parts.stl)\nwird um die Mechanik in den\nBoden ① gelegt, Verzahnung innen',
         ha='center', fontsize=10.5)

# ---------- lid with magnets ----------
ax = fig.add_axes([0.81, 0.62, 0.19, 0.30], projection='3d'); ax.set_proj_type('ortho')
lid_mags = [cyl([x, y, 6], [x, y, 8], 2.0, 20) for x, y in MAGNETS]
draw(ax, [(lid, '#a7a7c9')] + [(m, '#8c8c96') for m in lid_mags], [(-100, 100), (-100, 100), (-10, 70)], elev=-35, azim=-68)
for x, y in MAGNETS:
    guide(ax, [x, y, 8], [x, y, 20])
fig.text(0.905, 0.62, '④ Deckel (top.stl), von unten\n4 Magnete in die Stifte,\nhalten am Boden ①', ha='center', fontsize=10.5)

# ---------- standing in the foot ----------
ax = fig.add_axes([0.68, 0.17, 0.30, 0.42], projection='3d'); ax.set_proj_type('persp', focal_length=0.5)
disc = trimesh.util.concatenate([load('bottom.stl'), ring.copy(), lid.copy()])
disc.vertices = np.c_[disc.vertices[:, 0], disc.vertices[:, 2], disc.vertices[:, 1]]  # stand upright, outlet down
fv = foot.vertices
fm = trimesh.Trimesh(np.c_[-fv[:, 0] + 7 + BC[0], -fv[:, 1] + 6, fv[:, 2] - 25 + (BC[1] - 95.5) - 40], foot.faces)
draw(ax, [(disc, '#9fb0c8'), (fm, '#9c8466')], [(-110, 110), (-110, 110), (-175, 105)], elev=15, azim=-55)
ax.plot([BC[0]] * 2, [11, 11], [BC[1] - 95.5 - 3, fm.bounds[1][2] + 3], ':', color='#555', lw=1.2)
fig.text(0.83, 0.17, '⑤ Standfuß (foot.stl): Rad hochkant,\nAuslass-Schlitz nach unten', ha='center', fontsize=10.5)

# ---------- hardware strip ----------
hw = fig.add_axes([0.03, 0.015, 0.94, 0.10]); hw.set_xlim(0, 100); hw.set_ylim(0, 11); hw.axis('off')
hw.add_patch(plt.Rectangle((0, 0), 100, 11, fc='#f6f6f6', ec='#ccc'))
hw.text(1, 9.3, 'Kleinteile', fontsize=12, weight='bold')
rows = [('P8', 'Servo SG90', '1×'), ('S1', 'Torx #2 × 3/8"', '5× (2 Servo, 3 Mechanik)'),
        ('P9', 'Kugelschreiberfeder 0,4×4,5×18', '2×'), ('P10', 'Stab Ø1,5 × 14 mm', '1×'),
        ('P11', 'Stab Ø1,5 × 12 mm', '1×'), ('P12', 'Drehfeder (McMaster 9271K71)', '1×'),
        ('', 'Magnet rund Ø4 × 2 mm', '4× Boden, 4× Deckel')]
for k, (code, name, n) in enumerate(rows):
    x = 1 + k * 14.1
    hw.text(x, 5.6, code, fontsize=11, weight='bold')
    hw.text(x, 3.4, name, fontsize=9.2)
    hw.text(x, 1.4, n, fontsize=9.2, color='#555')

plt.savefig(OUT, dpi=110)
