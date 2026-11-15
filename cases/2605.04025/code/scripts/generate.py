"""Replayable analytic, exact-sector, and bounded MPS jobs."""
import json
from pathlib import Path
import sys
import time
import numpy as np

from hubbard import Sector,free,initial,mapping_control
from tebd import trajectory
from scipy.integrate import quad
from scipy.optimize import minimize_scalar
from scipy.special import expit,ive,j0,j1,jv


def bethe(U):
    u=U/4
    def v(k):
        s,c=np.sin(k),np.cos(k)
        a=quad(lambda w:2*j1(w)*np.sin(w*s)*expit(-2*w*u),0,35/u,epsabs=1e-11)[0]
        b=quad(lambda w:j0(w)*np.cos(w*s)*expit(-2*w*u),0,35/u,epsabs=1e-11)[0]
        return (2*s+2*c*a)/(1+2*c*b)
    grid=np.linspace(0,np.pi,401)
    idx=int(np.argmax([v(k) for k in grid]))
    k=minimize_scalar(lambda k:-v(k),bounds=(grid[idx-1],grid[idx+1]),method="bounded")
    charge=-k.fun
    spin=2*ive(1,np.pi/(2*u))/ive(0,np.pi/(2*u))
    return dict(U=U,charge=float(charge),spin=float(spin),spin_over_charge=float(spin/charge))


def analytic(cfg):
    L=31
    t=np.arange(47)*.2
    exact=free(L,initial(L,15),t,15)
    sizes=(41,81,161)
    r=np.arange(-20,21)
    charge=np.stack([(r==0)-jv(r,2*t)**2 for t in (1.,2.,3.,4.)])
    limits={str(n):free(n,initial(n,n//2),[1,2,3,4],n//2) for n in sizes}
    return dict(mapping=mapping_control(2.),bethe=[bethe(U) for U in (10.,12.,14.)],
            free=dict(t=t.tolist(),**exact),infinite_check=dict(distance=r.tolist(),charge=charge.tolist(),finite=limits))


def small(cfg,U):
    L=10
    n=initial(L,cfg["l10_vacancy"])
    sector=Sector(L,n)
    steps=cfg["l10_steps"]
    dts={2.:(.15,.2,.25),6.:(.1,.15,.2),15.:(.05,.1,.15)}[U]
    base=cfg["small_time_grid"]
    target=sector.exact(U,base,round(max(dts)*steps/base))
    curves=[]
    for dt in dts:
        i=np.arange(steps+1)*round(dt/base)
        m=sector.trotter(U,dt,steps)
        f=sector.trotter(U,dt,steps,False)
        rmse=lambda a:np.sqrt(np.mean((a-target[i])**2,axis=(1,2))).tolist()
        curves.append(dict(dt=dt,t=(np.arange(steps+1)*dt).tolist(),exact=target[i].tolist(),
                           mirror=m.tolist(),first=f.tolist(),mirror_rmse=rmse(m),first_rmse=rmse(f)))
    return dict(U=U,dimensions=list(sector.shape),particle_numbers=n.sum(axis=0).tolist(),cases=curves)


def large(cfg,L,U,chi,vacancy):
    if L==31:
        dt,steps=cfg["spin_charge_parameters"][str(int(U))]
    else:
        dt,steps=cfg["l60_dt"],cfg["l60_steps"]
    n=initial(L,vacancy,up_even=L==31)
    res=trajectory(n,U,dt,steps,chi,cfg["tebd_cutoff"],center=vacancy if L==31 else None)
    return dict(L=L,U=U,chi=chi,dt=dt,vacancy=vacancy,particles=n.sum(axis=0).tolist(),**res)


def main():
    mode,out,*args=sys.argv[1:]
    cfg=json.loads(Path("config/protocol.json").read_text())
    start=time.perf_counter()
    if mode=="analytic":
        result=analytic(cfg)
    elif mode=="small":
        result=small(cfg,float(args[0]))
    elif mode=="large":
        L,U,chi,vacancy=map(int,args)
        result=large(cfg,L,float(U),chi,None if vacancy<0 else vacancy)
    else:
        raise ValueError(mode)
    result["wall_seconds"]=time.perf_counter()-start
    Path(out).write_text(json.dumps(result,separators=(",",":"),allow_nan=False)+"\n")


if __name__=="__main__":
    main()
