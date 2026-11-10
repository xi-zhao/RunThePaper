"""Run one deterministic block using only the documented model inputs."""
import json
from pathlib import Path
import sys

import numpy as np
from scipy.special import roots_legendre
from scipy.signal.windows import dpss

from estimators import adaptive, bayes, spectral_bank
from physics import areas, detuned_probability, echo, shift, sid_loss, tapers, three_axis_ensemble, transfer


def concentration():
    n = 120
    nw = 4
    nodes,weights = roots_legendre(240)
    values = np.column_stack([echo(n,k,5) for k in range(4)]+list(tapers(n,nw,4)))
    curves = np.abs(transfer(values,np.linspace(0,64,2001)/(2*np.pi),1))**2
    inside = np.abs(transfer(values,nw*nodes,1))**2
    held_lambda = nw*(weights @ inside)/(np.sum(values**2,axis=0)/n)
    raw = np.exp(2j*np.pi*nw*nodes[:,None]*np.arange(n)/n) @ values
    dtft_lambda = nw*(weights @ np.abs(raw)**2)/(np.sum(values**2,axis=0)*n)
    grid = np.arange(n)
    kernel = (2*nw/n)*np.sinc((2*nw/n)*(grid[:,None]-grid))
    table_n = [120,2240,8192]
    table = np.stack([[dpss(size,w,11,return_ratios=True)[1] for w in range(1,6)]
                      for size in table_n])
    np.savez_compressed("results/concentration.npz",curves=curves,held_lambda=held_lambda,
        dtft_lambda=dtft_lambda,values=values,kernel=kernel,table=table,table_n=table_n,
        omega=np.linspace(0,64,2001))


def identification(settings):
    f = np.arange(0,31001,10)
    response = {}
    for row in settings["identification"]:
        name, n, nw, k, tau, alpha, modulation, carrier = row
        waveform = echo(n,k) if nw==0 else tapers(n,nw,k+1)[k]
        if modulation != "base":
            waveform = shift(waveform,tau/n,carrier,modulation)
        x = transfer(areas(waveform),f,tau)
        response[name] = x
        response[name+"_loss"] = sid_loss(x,alpha)
    np.savez_compressed("results/identification.npz",frequency=f,**response)


def tomography(settings):
    f = np.arange(15)*200.
    rows = {}
    for name,n,tau,hold,seed in settings["tomography"]:
        a = areas(tapers(n,3,2)[1])
        p,s,e = three_axis_ensemble(a,f,tau,.75,5,hold,2048,seed)
        rows[name] = p
        rows[name+"_target"] = s
        rows[name+"_mc_se"] = e
        rows[name+"_amplitude_only"] = sid_loss(transfer(a,f,tau),.75)
    np.savez_compressed("results/tomography.npz",frequency=f,**rows)


def spectral():
    omega = np.linspace(0,140000,4001)
    held, shifts, band = spectral_bank(omega)
    kernel = held/(4*np.pi)
    lines = 2*np.pi*np.arange(100,7001,100)
    height = 3.3329923e-4
    loss = np.sum(np.stack([np.interp(lines,omega,row) for row in kernel.reshape(36,-1)]),
                  axis=1).reshape(9,4)*height*(2*np.pi*100)
    history, weights, single = adaptive(omega,kernel,shifts,band,loss)
    centers = shifts+band/2
    freq,estimate,local,cond = bayes(omega,kernel,shifts,band,loss,loss*(1-loss)/10000,centers,history[-1])
    np.savez_compressed("results/spectral.npz",omega=omega,kernel=kernel,shifts=shifts,band=band,
        synthetic_loss=loss,synthetic_history=history,synthetic_weights=weights,synthetic_single=single,
        synthetic_bayes=estimate,synthetic_bayes_omega=freq,synthetic_local=local,condition=cond)


def resonances(settings):
    f = np.linspace(-100e3,100e3,801)
    curves = {}
    for name,tau,n in settings["resonances"]:
        for label,values,total in [("square",np.ones(n),3*np.pi),("k0",tapers(n,3,3)[0],3*np.pi),
                                   ("k2",tapers(n,3,3)[2],np.pi)]:
            curves[f"{name}_{label}"] = detuned_probability(areas(values,total,signed=True),f,tau)
    np.savez_compressed("results/resonances.npz",frequency=f,**curves)


def calibration():
    shifts = [10e3,50e3,100e3]
    omega = np.linspace(-400,400,1601)
    out = {}
    for nw,duration in [(1,.006),(2,.008),(3,.010),(4,.011)]:
        n = round(duration/1e-6)
        t = tapers(n,nw,1)[0]
        shaped = shift(t,duration/n,shifts[0],"COS")
        rotation = areas(shaped,400*np.pi)
        res = transfer(rotation,shifts[0]+omega,duration)
        out[f"nw{nw}"] = res
    np.savez_compressed("results/calibration.npz",frequency_offset=omega,**out)


if __name__ == "__main__":
    model = json.loads(Path("config/model.json").read_text())
    block = sys.argv[1]
    if block in {"concentration","spectral","calibration"}:
        globals()[block]()
    elif block in {"identification","tomography","resonances"}:
        globals()[block](model)
    else:
        raise SystemExit(f"unknown block {block}")
