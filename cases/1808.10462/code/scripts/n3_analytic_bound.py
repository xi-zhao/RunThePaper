"""Continuous laser-frequency bound for the three-ion analytic construction."""
from itertools import permutations
from pathlib import Path
import json

from phase_controls import geometry,PSI,save
from chain_scaling import analytic_response
import numpy as np


def calculate(cfg,time):
    f6=cfg["figure6"]
    freq,c,_,_=geometry(cfg,3,f6["trap_hz"])
    product=c[0]*c[1]
    order=np.asarray(list(permutations(range(len(freq)))))
    # Write the final mode area as S B_base + K |A_base|^2. For a fixed
    # permutation all doubling phases depend only on differences of modes.
    size=2**len(freq)
    width=1/size
    scale=2*(2*np.pi*time*f6["rabi_hz"])**2
    acc=np.zeros((len(order),len(freq)))
    norm=np.ones_like(acc)
    for i in range(len(freq)):
        offset=freq[None,:]-freq[order[:,i,None]]
        b=-np.exp(2j*np.pi*time*offset*(2**i)*width)
        acc=2*acc+b.imag*norm
        norm*=abs(1+b)**2
    dmax=3e6
    step=250.
    grid=np.linspace(freq.min()-dmax,freq.max()+dmax,
                     int(np.ceil((2*dmax+np.ptp(freq))/step))+1)
    greatest=0.
    greatest_per_branch=np.zeros(2)
    best=None
    for batch in np.array_split(grid,256):
        x=2*np.pi*time*width*(freq[None,:]-batch[:,None])
        aa=width**2*np.sinc(x/(2*np.pi))**2
        small=abs(x)<1e-3
        b=np.empty_like(x)
        b[small]=width**2*(x[small]/6-x[small]**3/120+x[small]**5/5040)
        b[~small]=width**2*(x[~small]-np.sin(x[~small]))/x[~small]**2
        B=size*b[None]+acc[:,None]*aa[None]
        chi=np.einsum("otm,m->ot",B,product)*scale
        j,k=np.unravel_index(np.argmax(abs(chi)),chi.shape)
        if abs(chi[j,k])>greatest:
            greatest=float(abs(chi[j,k]))
            best=dict(laser_hz=float(batch[k]),phase=float(chi[j,k]),order=order[j].tolist())
        split=(freq>1.58e6, freq<1.58e6)
        greatest_per_branch=np.maximum(greatest_per_branch,[float(abs(np.einsum("otm,m->ot",B[:,:,a],product[a])*scale).max()) for a in split])
    # Lipschitz bounds use the integral of |s-r| across one segment.
    slope=float(scale*2*np.pi*time*width**3*np.max(
        np.einsum("om,m->o",size/6+abs(acc)/3,abs(product))))
    interp=slope*(grid[1]-grid[0])/2
    x_min=2*np.pi*time*width*dmax
    tail=float(scale*width**2*np.max(np.einsum("om,m->o",
        size*(x_min+1)/x_min**2+4*abs(acc)/x_min**2,abs(product))))
    found=best["laser_hz"]-freq
    _,raw=analytic_response(found[None,:],np.array([time]),np.array([best["order"]]))
    delta=float(abs(scale*np.dot(raw[0],product)-best["phase"]))
    assert delta<1e-10
    axis=np.array([scale*np.dot(raw[0,branch],product[branch]) for branch in split])
    ratio=float((np.copysign(PSI,best["phase"])-axis.sum())/(axis[0]-axis[1]))
    projection=None
    if abs(ratio)<=1:
        phase=float(np.dot(axis,[1+ratio,1-ratio]))
        projection=dict(x_squared=1+ratio,y_squared=1-ratio,phase_rad=phase,
                        angle_from_x_deg=float(np.degrees(np.arccos(np.sqrt((1+ratio)/2)))))
        assert abs(abs(phase)-PSI)<1e-12
    return dict(time_us=float(time*1e6),best=best,maximum_sampled_phase=greatest,
        interpolation_bound=interp,outer_tail_bound=tail,continuous_bound=max(greatest+interp,tail)+1e-10,
        target=PSI,recurrence_disagreement=delta,number_orders=len(order),laser_samples=len(grid),
        separate_axis_phase_at_unit_projection=greatest_per_branch.tolist(),
        best_axis_angles=axis.tolist(),projection_witness=projection)


if __name__=="__main__":
    cfg=json.loads(Path("config/followup.json").read_text())
    result=[calculate(cfg,t*1e-6) for t in (200,201)]
    save("results/n3-analytic-bound.json",result)
    for r in result:
        print(r["time_us"],r["maximum_sampled_phase"],r["continuous_bound"],r["outer_tail_bound"],flush=True)
