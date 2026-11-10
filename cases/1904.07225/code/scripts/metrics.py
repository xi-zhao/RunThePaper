"""Paper SSIM and separately preserved archival implementation."""
import numpy as np


def error_ssim(x,y,legacy=False,constant=.01):
    x=np.asarray(x,float)
    y=np.asarray(y,float)
    a=np.mean(x,axis=-1)
    b=np.mean(y,axis=-1)
    u=x-a[...,None]
    v=y-b[...,None]
    n=x.shape[-1]-1
    vx=np.sum(u*u,axis=-1)/n
    vy=np.sum(v*v,axis=-1)/n
    cov=np.sum(u*v,axis=-1)/n
    s=(2*a*b+constant)*(2*cov+constant)/((a*a+b*b+constant)*(vx+(vx if legacy else vy)+constant))
    return abs(1-s)


def birth(phi):
    return .5*(1+np.cos(phi))


def phase(prob):
    return np.arccos(np.clip(2*np.asarray(prob)-1,-1,1))


def crossover(budget,measured,thresholds):
    from scipy.interpolate import interp1d
    a,b=np.moveaxis(np.asarray(measured),-1,0)
    # Notebook protocol sorts by loss for a piecewise-linear inverse.
    f=interp1d(a,budget,bounds_error=False,fill_value="extrapolate")
    g=interp1d(b,budget,bounds_error=False,fill_value="extrapolate")
    x,y=f(thresholds),g(thresholds)
    ratio=np.divide(y,x,out=np.zeros_like(y),where=(x>0)&(y>0))
    inside=(thresholds>=max(min(a),min(b)))&(thresholds<=min(max(a),max(b)))
    return ratio,inside
