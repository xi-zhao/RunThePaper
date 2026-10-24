"""Independent numerical generation, fixed-v2 parameters, no source/reference reads."""
from pathlib import Path
import json,sys,time
import numpy as np
from scipy.linalg import eigvalsh,eigh
from scipy.optimize import brentq,minimize_scalar
from km import *

start=time.monotonic();Path('data').mkdir(exist_ok=True)
cfg=json.loads(Path('config.json').read_text());n=cfg['ribbon_rows']
k=np.linspace(0,2*np.pi,cfg['ribbon_points'])
bands={}
for label,v in [('qsh',.1),('trivial',.4)]:
    bands[label]=np.array([eigvalsh(ribbon(x,n=n,v=v),check_finite=False) for x in k])
np.savez_compressed('data/bands.npz',k=k,**bands)
print('bands',time.monotonic()-start,flush=True)

alphas=np.linspace(0,np.pi,cfg['pf_curve_points']);pfcurves={}
for label,v in [('qsh',.1),('trivial',.4),('inversion',0)]:
    pfcurves[label]=np.array([abs(pf(supercell(0,a,v=v))) for a in alphas])
np.savez_compressed('data/pf_curves.npz',alpha=alphas,**pfcurves)

def locate_zero(v):
    center=.58*np.pi;Uref=occupied(supercell(0,center,v=v))[1]
    def fun(a):return frame_pf(supercell(0,a,v=v),Uref)[0]
    phase=fun(center+.01)-fun(center-.01);phase/=abs(phase)
    root=brentq(lambda a:(fun(a)/phase).real,.5*np.pi,.65*np.pi,xtol=1e-14)
    return {'alpha':float(root),'alpha_over_pi':float(root/np.pi),'abs_pf':float(abs(fun(root)))}

obs={'config':cfg,'zero_qsh':locate_zero(.1),'zero_inversion':locate_zero(0)}
opt=minimize_scalar(lambda a:abs(pf(supercell(0,a,v=.4))),bounds=(.45*np.pi,.65*np.pi),method='bounded',options={'xatol':1e-13})
obs['trivial_min']={'alpha_over_pi':float(opt.x/np.pi),'abs_pf':float(opt.fun)}

def winding(ham,center,radius):
    Uref=occupied(ham(*center))[1];vals=[];sing=[]
    for th in np.linspace(0,2*np.pi,257):
        a=center[0]+radius*np.cos(th);b=center[1]+radius*np.sin(th)
        p,s=frame_pf(ham(a,b),Uref);vals.append(p);sing.append(s)
    return {'winding':float(np.sum(np.angle(np.array(vals)[1:]/np.array(vals)[:-1]))/(2*np.pi)),
            'min_abs_pf':float(np.min(abs(np.array(vals)))),'min_frame_overlap':float(min(sing))}
obs['bulk_vortices']=[winding(lambda q1,q2:bulk(q1,q2,v=.1), (s*2*np.pi/3,-s*2*np.pi/3),.08) for s in [1,-1]]
obs['twist_vortices']=[winding(lambda a,b:supercell(a,b,v=.1),(0,s*obs['zero_qsh']['alpha']),.08) for s in [1,-1]]
obs['trim_pf']={str(v):[float(abs(pf(supercell(a,b,v=v)))) for a,b in [(0,0),(np.pi,0),(0,np.pi),(np.pi,np.pi)]] for v in [.1,.4,0]}
obs['spin_chern']={str(v):{str(g):spin_chern(v,ngrid=g) for g in [21,41,61]} for v in [.1,.4]}
print('pf curves and invariants',time.monotonic()-start,flush=True)

delta=3*np.sqrt(3)*.06
obs['phase_boundary']=[]
for r in np.linspace(0,2*np.sqrt(3)*.06,9):
    vc=delta-9*r*r/(4*delta)
    e=eigvalsh(bulk(2*np.pi/3,-2*np.pi/3,v=vc,r=r))
    obs['phase_boundary'].append({'r':float(r),'v':float(vc),'gap':float(e[2]-e[1])})
obs['bulk_gaps']={}
qs=np.linspace(0,2*np.pi,61)
for v in [.1,.4]:
    series=[]
    for r in np.linspace(0,.05,5):
        ev=np.array([eigvalsh(bulk(q1,q2,v=v,r=r),check_finite=False) for q1 in qs for q2 in qs])
        series.append({'r':float(r),'direct':float((ev[:,2]-ev[:,1]).min()),'indirect':float(ev[:,2].min()-ev[:,1].max())})
    obs['bulk_gaps'][str(v)]=series

obs['ribbon_width']={}
for width in [20,30,40]:
    obs['ribbon_width'][str(width)]={str(v):eigvalsh(ribbon(np.pi,n=width,v=v))[2*width-2:2*width+2].tolist() for v in [.1,.4]}
obs['edge_fermi']={}
for r in [0,.05]:
    for ef in [0,.05]:
        grid=np.linspace(.55*np.pi,1.45*np.pi,181)
        ev=np.array([eigvalsh(ribbon(x,n=n,v=.1,r=r)) for x in grid])
        roots=[]
        for band in range(4*n):
            for i in range(len(grid)-1):
                if (ev[i,band]-ef)*(ev[i+1,band]-ef)<0:
                    fun=lambda x:eigvalsh(ribbon(x,n=n,v=.1,r=r))[band]-ef
                    x=brentq(fun,grid[i],grid[i+1],xtol=1e-13)
                    e,u=eigh(ribbon(x,n=n,v=.1,r=r));psi=u[:,band]
                    prob=abs(psi.reshape(n,4))**2
                    szval=float((abs(psi)**2*np.tile([.5,-.5,.5,-.5],n)).sum())
                    row=float((prob.sum(axis=1)*np.arange(n)).sum())
                    h=1e-5;velocity=float(np.vdot(psi,(ribbon(x+h,n=n,v=.1,r=r)-ribbon(x-h,n=n,v=.1,r=r))@psi).real/(2*h))
                    roots.append({'k_over_pi':float(x/np.pi),'Sz_over_hbar':szval,'mean_row':row,'velocity':velocity})
        obs['edge_fermi'][f'r={r},ef={ef}']=roots

q=np.linspace(-np.pi,np.pi,cfg['bulk_map_points']);a=np.linspace(-np.pi,np.pi,cfg['twist_map_points'])
maps={}
for label,v in [('qsh',.1),('trivial',.4),('inversion',0)]:
    maps['bulk_'+label]=np.array([[abs(pf(bulk(x,y,v=v))) for x in q] for y in q])
    maps['twist_'+label]=np.array([[abs(pf(supercell(x,y,v=v))) for x in a] for y in a])
np.savez_compressed('data/pf_maps.npz',q=q,alpha=a,**maps)
obs['runtime_seconds']=time.monotonic()-start
Path('data/observables.json').write_text(json.dumps(obs,indent=2)+'\n')
print(json.dumps({'runtime_seconds':obs['runtime_seconds'],'zero_qsh':obs['zero_qsh'],'trivial_min':obs['trivial_min'],'vortices':obs['bulk_vortices']}),flush=True)
