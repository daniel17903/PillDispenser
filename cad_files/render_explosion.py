# Renders explosionszeichnung.png. Run from cad_files/: python3 render_explosion.py explosionszeichnung.png
# Requires: pip install numpy matplotlib trimesh fast_simplification
import trimesh, numpy as np, matplotlib, sys
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3D
D=''
def load(f, n=None):
    m=trimesh.load(D+f,force='mesh')
    if n and len(m.faces)>n: m=m.simplify_quadric_decimation(face_count=n)
    return m
BC=np.array([0.5,3.48])            # Achse des Bodens
parts=[]  # (mesh in local disc frame, color, label, explode offset along axis)
b=load('bottom.stl'); parts.append((b,'#6f8fb8','① Boden / Gehäuse\n(bottom.stl)',0))
# Mechanik im Druck-Layout, über Mechanikbereich zentriert
mech=[]
for i in range(1,7):
    m=load(f'Assembly_parts/part_{i}.stl',6000 if i==1 else None)
    m.apply_translation([-24.2+BC[0]-4, -25.1+BC[1]+6, 2])
    mech.append(m)
mcol=['#e07b39','#e0a339','#c9c241','#7fb069','#d46a8c','#b07cc6']
for i,m in enumerate(mech): parts.append((m,mcol[i],None,70))
r=load('tray_parts.stl'); r.apply_translation([BC[0]-3.15,BC[1]+0.76,0]); parts.append((r,'#8fb3a3','③ Fächerring\n(tray_parts.stl)',150))
t=load('top.stl'); t.apply_transform(np.diag([-1,1,-1,1])); t.apply_translation([BC[0]+0.17,BC[1]+1.37,22]); parts.append((t,'#a7a7c9','④ Deckel\n(top.stl, Stifte nach innen)',240))
f=load('foot.stl')
# Weltkoordinaten: X=x, Z=y (Auslass unten), Y=z (Scheibenachse liegt waagerecht)
def world(v,off): return np.c_[v[:,0], v[:,2]+off, v[:,1]]
polys=[];cols=[]
L=np.array([0.45,0.75,0.5]);L/=np.linalg.norm(L)
def add(V,F,col):
    tri=V[F]; n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); n/=np.linalg.norm(n,axis=1)[:,None]+1e-12
    s=np.abs(n@L)*0.65+0.35
    c=np.array(matplotlib.colors.to_rgb(col))
    polys.extend(tri); cols.extend(np.clip(c[None]*s[:,None],0,1))
anchors=[]
for m,col,lab,off in parts:
    V=world(m.vertices,off); add(V,m.faces,col)
    if lab: anchors.append((V.mean(0),lab,V))
# Fuß: V-Rinne (y≈-5, z≈25) unter die Unterkante der Scheibe, 45 mm nach unten abgesetzt
fv=f.vertices.copy(); fv=np.c_[-fv[:,0]+7+BC[0], -fv[:,1]+6, fv[:,2]-25+(BC[1]-95.5)-45]
add(fv,f.faces,'#9c8466')
fig=plt.figure(figsize=(16,11)); ax=fig.add_axes([0.28,0.0,0.72,0.9],projection='3d'); ax.set_proj_type('persp',focal_length=0.35)
pc=Poly3DCollection(np.array(polys),facecolors=np.array(cols),edgecolor='none'); ax.add_collection3d(pc)
# Montageachse
ax.plot([BC[0]]*2,[-20,270],[BC[1]]*2,'--',color='#555',lw=1)
for y in (60,120,185): pass
ax.set_xlim(-130,130);ax.set_ylim(-20,280);ax.set_zlim(-190,110)
ax.set_box_aspect((260,260,300))
ax.view_init(elev=16,azim=38); ax.set_axis_off()
def lbl(p,text,dx=0,dz=0):
    ax.text(p[0]+dx,p[1],p[2]+dz,text,fontsize=11,ha='center',va='bottom',color='#222',
            bbox=dict(boxstyle='round,pad=0.3',fc='white',ec='#999',alpha=0.9))
for (c,lab,V) in anchors: lbl([c[0],c[1],V[:,2].max()],lab,dz=8)
mc=np.vstack([world(m.vertices,70) for m in mech]); 
lbl([mc[:,0].mean(),mc[:,1].mean(),mc[:,2].max()],'② Mechanik (part_1 … part_6)\nLage schematisch',dz=30)
lbl([fv[:,0].mean(),fv[:,1].mean(),fv[:,2].min()],'⑤ Standfuß (foot.stl)',dz=-28)
ax.plot([BC[0]]*2,[11,11],[BC[1]-95.5-5,fv[:,2].max()+5],'--',color='#555',lw=1)
fig.text(0.5,0.95,'Pillenspender – Explosionszeichnung',ha='center',fontsize=18,weight='bold')
fig.text(0.5,0.915,'Teile werden entlang der gestrichelten Achse in Reihenfolge ① → ④ in den Boden gesetzt; das fertige Rad steht hochkant mit dem Auslass nach unten im Standfuß ⑤.',ha='center',fontsize=11,color='#444')
# Vergrößerter Ausschnitt Mechanik
ax2=fig.add_axes([0.0,0.02,0.32,0.52],projection='3d'); ax2.patch.set_alpha(0); ax2.set_proj_type('ortho')
names=['part_1','part_2 (langer Hebel)','part_3 (Klinke)','part_4 (Block)','part_5 (Hebel)','part_6 (Platte 4 mm)']
P=[];C=[]
for i,m in enumerate(mech):
    tri=m.vertices[m.faces]; n=m.face_normals; s_=np.abs(n@np.array([0.3,-0.4,0.87]))*0.65+0.35
    P.extend(tri); C.extend(np.clip(np.array(matplotlib.colors.to_rgb(mcol[i]))[None]*s_[:,None],0,1))
    c=m.bounds.mean(0); ax2.text(c[0],c[1],m.bounds[1][2]+8,str(i+1),fontsize=12,weight='bold',ha='center',color='#222')
ax2.add_collection3d(Poly3DCollection(np.array(P),facecolors=np.array(C),edgecolor='none'))
allv=np.vstack([m.vertices for m in mech]); c=allv.mean(0); r=30
ax2.set_xlim(c[0]-r,c[0]+r);ax2.set_ylim(c[1]-r,c[1]+r);ax2.set_zlim(-10,40);ax2.set_box_aspect((1,1,0.8))
ax2.view_init(elev=50,azim=-65); ax2.set_axis_off()
fig.text(0.03,0.80,'② Mechanik (vergrößert, Drucklage)',fontsize=13,weight='bold')
for i,n in enumerate(names): fig.text(0.03,0.77-i*0.025,f'{i+1}  {n}',fontsize=10.5,color=mcol[i] if False else '#333')
plt.savefig(sys.argv[1],dpi=110)
