"""Targeted independent refinement: cusp nodes, original grid resolution, zero loops.
No reference ordinate is read. Preserve initial generation separately.
"""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import eigvalsh
from scipy.optimize import brentq,minimize_scalar
from km import *

results={};a=np.linspace(0,np.pi,1001);arrays={}
for tag,v in [('qsh',.1),('trivial',.4),('inversion',0)]:
    Uref=occupied(supercell(0,.58*np.pi,v=v))[1]
    fn=lambda x:frame_pf(supercell(0,x,v=v),Uref)[0]
    phase=fn(.59*np.pi)-fn(.57*np.pi);phase/=abs(phase)
    if v<.2:
        root=brentq(lambda x:(fn(x)/phase).real,.5*np.pi,.65*np.pi,xtol=1e-14)
        xs=np.unique(np.r_[a,root]);results[tag+'_root']=root
    else:xs=a
    arrays[tag+'_alpha']=xs;arrays[tag]=np.array([abs(pf(supercell(0,x,v=v))) for x in xs])
np.savez_compressed('data/pf_curves_refined.npz',**arrays)
k=np.linspace(0,2*np.pi,121)
np.savez_compressed('data/bands_coarse.npz',k=k,qsh=np.array([eigvalsh(ribbon(x,n=30,v=.1)) for x in k]),trivial=np.array([eigvalsh(ribbon(x,n=30,v=.4)) for x in k]))

def contour_pf(v,nside=100,nsteps=24):
    center=np.array([np.pi/2,np.pi]);U0=occupied(bulk(*center,v=v))[1]
    corners=np.array([[0,0],[np.pi,0],[np.pi,2*np.pi],[0,2*np.pi],[0,0]])
    pts=np.concatenate([np.linspace(p,q,nside,endpoint=False) for p,q in zip(corners[:-1],corners[1:])]);vals=[];smins=[]
    for target in pts:
        U=U0.copy()
        for frac in np.linspace(0,1,nsteps+1)[1:]:
            q=center+frac*(target-center);V=occupied(bulk(*q,v=v))[1]
            left,s,right=np.linalg.svd(V.conj().T@U);U=V@(left@right);smins.append(s.min())
        vals.append(pfaffian(overlap(U)))
    vals=np.asarray(vals)
    wind={}
    for delta in [0,1e-2,1e-3,1e-4,-1e-2,-1e-3,-1e-4]:
        z=vals+1j*delta
        wind[str(delta)]=float(np.sum(np.angle(np.roll(z,-1)/z))/(2*np.pi))
    return {'windings':wind,'boundary_min_absP':float(abs(vals).min()),'transport_min_singular':float(min(smins))},pts,vals

paths={}
for v in [.1,.4,0]:
    res,pts,vals=contour_pf(v);results['half_BZ_'+str(v)]=res
    paths['points_'+str(v)]=pts;paths['pf_'+str(v)]=vals
np.savez_compressed('data/half_bz.npz',**paths)

def zero_loop(ham,center,rmax):
    Uref=occupied(ham(*center))[1];p0=frame_pf(ham(*center),Uref)[0];phase=p0/abs(p0)
    roots=[];details=[]
    for th in np.linspace(0,2*np.pi,121):
        direction=np.array([np.cos(th),np.sin(th)])
        fun=lambda r:frame_pf(ham(*(center+r*direction)),Uref)[0]/phase
        rs=np.linspace(0,rmax,81);z=[fun(r) for r in rs];brackets=[i for i in range(80) if z[i].real*z[i+1].real<0]
        if not brackets:
            details.append({'angle':float(th),'state':'no_signed_bracket'});continue
        i=brackets[0];r=brentq(lambda r:fun(r).real,rs[i],rs[i+1],xtol=1e-13);p=fun(r)
        roots.append(center+r*direction);details.append({'angle':float(th),'abs_pf':float(abs(p))})
    return np.array(roots),details

bulkham=lambda kx,ky:bulk(kx/2+np.sqrt(3)*ky/2,-kx/2+np.sqrt(3)*ky/2,v=0)
bl,bd=zero_loop(bulkham,np.array([0,2*np.pi/np.sqrt(3)]),2.8)
tl,td=zero_loop(lambda a,b:supercell(a,b,v=0),np.zeros(2),3.1)
np.savez_compressed('data/zero_loops.npz',bulk=bl,twist=tl)
results['zero_loops']={'bulk_count':len(bl),'twist_count':len(tl),'bulk_details':bd,'twist_details':td}

sizes=[]
for n1,n2 in [(1,1),(1,2),(2,1),(2,3),(3,2),(3,3)]:
    xs=np.linspace(0,np.pi,101)
    ys=np.array([abs(pf(supercell(0,a,n1=n1,n2=n2,v=.1))) for a in xs])
    idx=ys.argmin();lo=xs[max(0,idx-2)];hi=xs[min(100,idx+2)]
    opt=minimize_scalar(lambda a:abs(pf(supercell(0,a,n1=n1,n2=n2,v=.1))),bounds=(lo,hi),method='bounded',options={'xatol':1e-13})
    sizes.append({'N1':n1,'N2':n2,'min_on_alpha1_zero':float(opt.fun),'alpha2_over_pi':float(opt.x/np.pi),'trim_max_deviation':max(float(abs(abs(pf(supercell(a,b,n1=n1,n2=n2,v=.1)))-1)) for a,b in [(0,0),(np.pi,0),(0,np.pi),(np.pi,np.pi)])})
results['cell_size_checks']=sizes
Path('checks/refinement_results.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps({k:v for k,v in results.items() if k!='zero_loops'},indent=2));print('loops',len(bl),len(tl), 'max residual',max(row.get('abs_pf',0) for row in bd+td))
