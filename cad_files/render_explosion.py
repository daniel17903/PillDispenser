# Renders explosionszeichnung.png from the STL files in this folder.
# Run from cad_files/:  python3 render_explosion.py explosionszeichnung.png
# Requires: pip install numpy matplotlib trimesh fast_simplification
#
# Coordinates are in the frame of bottom.stl. The mechanism poses were
# derived from a photo of the assembled mechanism (camera pose fitted to the
# four screw posts, part outlines matched to the photo), so they are accurate
# to roughly 1-2 mm.
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

# local axis -> bottom.stl axis, yaw (deg), position of bbox centre (x, y) and bottom (z)
POSES = {
    1: (np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]]).T, 16.8, (-43.8, 9.1, 6.2)),   # servo crank, upright
    2: (np.eye(3), 79.5, (-30.9, -1.7, 2.5)),                                      # lever
    3: (np.eye(3), 206.0, (-49.3, -5.2, 4.0)),                                     # pawl
    4: (np.eye(3), 91.2, (52.3, 4.2, 2.0)),                                        # block at the rim
    5: (np.diag([-1, 1, -1]), -90.2, (-0.4, -5.8, 9.3)),                           # link, upside down
    6: (np.eye(3), 79.5, (-22.9, -4.9, 14.5)),                                     # plate on the lever
}
NAMES = {1: 'Servo-Kurbel', 2: 'Hebel', 3: 'Klinke', 4: 'Block am Rand',
         5: 'Gelenkstück', 6: 'Platte 4 mm'}
MCOL = {1: '#e07b39', 2: '#e0a339', 3: '#c9b52e', 4: '#4fa3a5', 5: '#d46a8c', 6: '#9a6cc6'}
LIFT = {1: 26, 2: 38, 3: 38, 4: 30, 5: 62, 6: 62}
SHIFT = {1: (0, 26)}  # extra sideways offset so nothing is hidden
SCREW_S1 = [(-38.6, -2.0), (-18.7, -5.6), (5.5, -6.4)]            # mechanism screws (photo)
BOSSES = [(-22.9, 41.6), (44.0, 16.3), (43.9, -10.7), (-31.1, -28.3)]  # lid screws


def load(f, n=None):
    m = trimesh.load(f, force='mesh')
    if n and len(m.faces) > n:
        m = m.simplify_quadric_decimation(face_count=n)
    return m


def place(m, R0, yaw, pos):
    a = np.radians(yaw)
    Rz = np.array([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])
    V = m.vertices - np.r_[m.bounds.mean(0)[:2], m.bounds[0][2]]
    V = (Rz @ R0 @ V.T).T
    V -= np.r_[(V.min(0) + V.max(0))[:2] / 2, V[:, 2].min()]
    return trimesh.Trimesh(V + np.array(pos), m.faces, process=False)


def screw(xy, ztip, d, length, head=None):
    head = head or d * 1.9
    sh = trimesh.creation.cylinder(radius=d / 2, height=length, sections=16)
    sh.apply_translation([xy[0], xy[1], ztip + length / 2])
    hd = trimesh.creation.cylinder(radius=head / 2, height=d * 0.7, sections=24)
    hd.apply_translation([xy[0], xy[1], ztip + length + d * 0.35])
    return trimesh.util.concatenate([sh, hd])


def spring(p0, axis, length=18, od=4.5, wire=0.45, turns=9):
    t = np.linspace(0, 2 * np.pi * turns, 400)
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    u = np.cross(axis, [0, 0, 1]) if abs(axis[2]) < 0.9 else np.array([1., 0, 0])
    u /= np.linalg.norm(u)
    w = np.cross(axis, u)
    r = (od - wire) / 2
    pts = np.asarray(p0) + np.outer(t / t[-1] * length, axis) + r * (np.outer(np.cos(t), u) + np.outer(np.sin(t), w))
    segs = []
    for a, b in zip(pts[:-1], pts[1:]):
        c = trimesh.creation.cylinder(radius=wire, segment=[a, b], sections=6)
        segs.append(c)
    return trimesh.util.concatenate(segs)


def shade(m, col, light=LIGHT):
    n = m.face_normals
    s = np.abs(n @ light) * 0.62 + 0.38
    c = np.array(matplotlib.colors.to_rgb(col))
    return np.clip(c[None] * s[:, None], 0, 1)


def draw(ax, items, lims, elev, azim, box=None):
    polys, cols = [], []
    for m, col in items:
        polys.append(m.vertices[m.faces])
        cols.append(shade(m, col))
    ax.add_collection3d(Poly3DCollection(np.concatenate(polys), facecolors=np.concatenate(cols),
                                         edgecolor='none'))
    ax.set_xlim(*lims[0]); ax.set_ylim(*lims[1]); ax.set_zlim(*lims[2])
    ax.set_box_aspect(box or [l[1] - l[0] for l in lims])
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def label(ax, p, text, color='#222', size=10.5, **kw):
    ax.text(*p, text, fontsize=size, ha='center', va='bottom', color=color, zorder=50,
            bbox=dict(boxstyle='round,pad=0.25', fc='white', ec='#aaa', alpha=0.92), **kw)


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
ax = fig.add_axes([0.0, 0.13, 0.64, 0.84], projection='3d')
ax.set_proj_type('ortho')
tc = bottom.triangles_center  # crop to the centre region (faces outside are dropped)
cut = bottom.submesh([np.where((np.abs(tc[:, 0]) < 70) & (np.abs(tc[:, 1]) < 46) & (tc[:, 2] > 2.2))[0]], append=True)
slab = trimesh.creation.box(extents=[140, 92, 2]); slab.apply_translation([0, 0, 1])
items = [(slab, '#7b97bd'), (cut, '#7b97bd')]
for i, m in mech.items():
    dx, dy = SHIFT.get(i, (0, 0))
    mm = m.copy(); mm.apply_translation([dx, dy, LIFT[i]]); items.append((mm, MCOL[i]))
for j, xy in enumerate(SCREW_S1):
    items.append((screw(xy, 19 + 80, 2.2, 9.5), '#9a9a9a'))
sp = spring((-29.7, -40, 8 + 22), (0, 1, 0)); items.append((sp, '#8a8a8a'))
draw(ax, items, [(-72, 72), (-72, 72), (-5, 110)], elev=48, azim=-62, box=[144, 144, 100])
for i, m in mech.items():
    c = m.bounds.mean(0); dx, dy = SHIFT.get(i, (0, 0))
    ax.plot([c[0], c[0] + dx], [c[1], c[1] + dy], [m.bounds[1][2] + 1, m.bounds[0][2] + LIFT[i] - 1], '--', color='#333', lw=1.0, zorder=40)
    lp = (c[0] + dx + (6 if i == 6 else -6 if i == 5 else 0), c[1] + dy, m.bounds[1][2] + LIFT[i] + 4)
    label(ax, lp, f'part_{i}', color=MCOL[i])
for xy in SCREW_S1:
    ax.plot([xy[0]] * 2, [xy[1]] * 2, [98, 18], '--', color='#333', lw=0.8, zorder=40)
label(ax, (SCREW_S1[1][0], SCREW_S1[1][1], 112), 'S1 Schrauben (3×)', size=9.5)
ax.plot([-29.7, -29.7], [-22, -9], [30, 9], '--', color='#333', lw=0.8, zorder=40)
label(ax, (-29.7, -40, 36), 'P9 Feder', size=9.5)
label(ax, (40, -46, 24), '① Boden (bottom.stl, Ausschnitt Mitte)', size=11)
fig.text(0.03, 0.88, '② Mechanik', fontsize=13, weight='bold')
for k, i in enumerate(POSES):
    fig.text(0.03, 0.855 - k * 0.024, '■', color=MCOL[i], fontsize=14)
    fig.text(0.05, 0.857 - k * 0.024, f'part_{i}  {NAMES[i]}', fontsize=10.5)
fig.text(0.03, 0.70, 'Gestrichelte Linien: Einbauort im Boden', fontsize=9.5, color='#666')

# ---------- ring ----------
ax = fig.add_axes([0.60, 0.62, 0.20, 0.30], projection='3d'); ax.set_proj_type('ortho')
rl = ring.copy(); rl.apply_translation([0, 0, 70])
draw(ax, [(bottom, '#7b97bd'), (rl, '#8fb3a3')], [(-100, 100), (-100, 100), (-10, 110)], elev=30, azim=-68)
ax.plot([BC[0]] * 2, [BC[1]] * 2, [25, 70], '--', color='#333', lw=0.8)
fig.text(0.70, 0.62, '③ Fächerring (tray_parts.stl)\nwird um die Mechanik in den\nBoden ① gelegt, Verzahnung innen',
         ha='center', fontsize=10.5)

# ---------- lid with screws ----------
ax = fig.add_axes([0.80, 0.62, 0.20, 0.30], projection='3d'); ax.set_proj_type('ortho')
lid_items = [(lid, '#a7a7c9')] + [(screw(xy, 40, 2.8, 12.7), '#b8b8b8') for xy in BOSSES]
draw(ax, lid_items, [(-100, 100), (-100, 100), (-10, 70)], elev=38, azim=-68)
for xy in BOSSES:
    ax.plot([xy[0]] * 2, [xy[1]] * 2, [39, 25], ':', color='#777', lw=1)
fig.text(0.90, 0.62, '④ Deckel (top.stl)\nStifte zeigen nach innen,\nverschraubt mit S2 (4×)', ha='center', fontsize=10.5)

# ---------- standing in the foot ----------
ax = fig.add_axes([0.66, 0.17, 0.30, 0.42], projection='3d'); ax.set_proj_type('persp', focal_length=0.5)
disc = trimesh.util.concatenate([load('bottom.stl'), ring.copy(), lid.copy()])
disc.vertices = np.c_[disc.vertices[:, 0], disc.vertices[:, 2], disc.vertices[:, 1]]  # stand upright, outlet down
fv = foot.vertices
fm = trimesh.Trimesh(np.c_[-fv[:, 0] + 7 + BC[0], -fv[:, 1] + 6, fv[:, 2] - 25 + (BC[1] - 95.5) - 40], foot.faces)
draw(ax, [(disc, '#9fb0c8'), (fm, '#9c8466')], [(-110, 110), (-110, 110), (-175, 105)], elev=15, azim=-55)
ax.plot([BC[0]] * 2, [11, 11], [BC[1] - 95.5 - 3, fm.bounds[1][2] + 3], ':', color='#555', lw=1.2)
fig.text(0.81, 0.17, '⑤ Standfuß (foot.stl): Rad hochkant,\nAuslass-Schlitz nach unten', ha='center', fontsize=10.5)

# ---------- hardware strip (cad_files/Readme.md) ----------
hw = fig.add_axes([0.03, 0.015, 0.94, 0.13]); hw.set_xlim(0, 100); hw.set_ylim(0, 14); hw.axis('off')
hw.add_patch(plt.Rectangle((0, 0), 100, 14, fc='#f6f6f6', ec='#ccc'))
hw.text(1, 12.2, 'Kleinteile (aus cad_files/Readme.md)', fontsize=12, weight='bold')


def icon_screw(x, L, d):
    hw.add_patch(plt.Rectangle((x, 4.5), L, d, fc='#bbb', ec='#666'))
    hw.add_patch(plt.Rectangle((x - 0.8, 4.5 - d * 0.5), 0.8, d * 2, fc='#bbb', ec='#666'))


def icon_rod(x, L):
    hw.add_patch(plt.Rectangle((x, 5), L, 0.6, fc='#c9c9c9', ec='#666'))


icon_screw(2.5, 5, 1.1)
hw.text(1, 1.3, 'S1  Torx #2 × 3/8"\n8× Basis, 10× pro Tray', fontsize=9.5)
icon_screw(22, 6.5, 1.4)
hw.text(20.5, 1.3, 'S2  Torx #4 × 1/2"\n8× Basis, 6× pro Tray', fontsize=9.5)
xs = np.linspace(41, 50, 200)
hw.plot(xs, 5.3 + 0.9 * np.sin((xs - 41) * 2 * np.pi * 9 / 9), color='#666', lw=1.2)
hw.text(40, 1.3, 'P9  Kugelschreiberfeder 0,4×4,5×18\n3× pro Tray', fontsize=9.5)
icon_rod(62, 8)
hw.text(61, 1.3, 'P10  Stab Ø1,5 × 14 mm\n1× pro Tray', fontsize=9.5)
icon_rod(80, 7)
hw.text(79, 1.3, 'P11  Stab Ø1,5 × 12 mm\n1× pro Tray', fontsize=9.5)
hw.text(99, 12.2, 'Im Bild eingezeichnet: 3× S1 an der Mechanik, 4× S2 am Deckel, 1× P9 am Hebel',
        fontsize=9, color='#666', ha='right')

plt.savefig(OUT, dpi=110)
