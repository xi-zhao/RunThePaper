"""Held-sample filters, Slepian tapers and constrained SSQM reconstruction."""

import numpy as np
from scipy.optimize import minimize

from base_filters import shift, tapers, transfer


def rse(frequency, duration, changes, energy):
    """Transform exact CPMG intervals, including half intervals at the edges."""
    t = np.r_[0, (np.arange(changes)+.5)*duration/max(1,changes), duration]
    dt = np.diff(t)
    mid = (t[1:]+t[:-1])/2
    f = np.asarray(frequency)[:,None]
    amplitude = (-1.)**np.arange(len(dt)) * np.sqrt(energy/duration)
    return np.sum(dt*amplitude*np.exp(2j*np.pi*f*mid)*np.sinc(f*dt),axis=1)


def normalized(values, dt, energy=900.):
    v = np.asarray(values)
    return v*np.sqrt(energy/(dt*np.sum(v**2,axis=0)))


def cos_bank(n, nw, count, dt, centers):
    windows = tapers(n,nw,count)
    carriers = np.cos(2*np.pi*np.asarray(centers)[:,None]*dt*np.arange(n))
    return normalized((carriers[:,None,:]*windows[None]).reshape(-1,n).T,dt)


def held_ff(samples, dt, f):
    return abs(transfer(samples*dt, f, len(samples)*dt))**2/4


def dpswf(values, frequency):
    # Transform discrete samples without the hold envelope.
    return transfer(values,frequency,len(values))/np.sinc(frequency).reshape((-1,)+(1,)*(values.ndim-1))


def optimal_setting(n, nw, count, starts=16):
    """Minimize the paper's in-band squared deviation on the unit sphere."""
    w = nw/n
    v = tapers(n,nw,count)
    points = np.linspace(-w,w,481)
    coeff = dpswf(v.T,points)*np.exp(-1j*np.pi*n*points[:,None])
    b,c = coeff.real,coeff.imag
    target = 1/(2*w)

    def loss(parameters):
        norm = np.linalg.norm(parameters)
        x = parameters/norm
        br,ci = b@x,c@x
        err=(br**2+ci**2)/target-1
        gradient=(4/len(points)/target)*(b.T@(err*br)+c.T@(err*ci))
        return np.mean(err**2),(gradient-x*np.dot(x,gradient))/norm

    rng = np.random.default_rng(134+n)
    initial = [np.ones(count), *rng.normal(size=(starts-1,count))]
    results=[minimize(loss,x,method="L-BFGS-B",jac=True,
              options={"maxiter":600,"ftol":1e-12,"gtol":1e-8}) for x in initial]
    opt=min(results,key=lambda x:x.fun)
    copt=opt.x/np.linalg.norm(opt.x)
    return copt@v,copt,[float(x.fun) for x in results]


def window_figures():
    output={}
    n=500
    f=np.linspace(-.06,.06,1201)
    v=tapers(n,4,4)
    f2_spectrum=(abs(dpswf(v.T,f))**2).T
    output["F2"]=dict(index=list(range(n)),frequency=f.tolist(),dpss=v.tolist(),dpswf=f2_spectrum.tolist())
    w=.008
    grid=np.linspace(-.016,.016,1025)
    output["F3"]={}
    output["F6"]={}
    for n,k in ((200,3),(400,6),(800,12),(1600,25)):
        v=tapers(n,n*w,k)
        p=np.mean(abs(dpswf(v.T,grid))**2,axis=1)
        ratio=np.trapezoid(p[abs(grid)<=w],grid[abs(grid)<=w])
        ideal=np.where(abs(grid)<=w,1/(2*w),0.0)
        a,c,loss=optimal_setting(n,n*w,k)
        # The figure caption uses K-1 to name the highest included taper. Retain
        # an alternate literal K-1-count result for sensitivity.
        short,_,short_loss=optimal_setting(n,n*w,k-1,starts=6)
        spec=abs(dpswf(a,grid))**2
        short_spec=abs(dpswf(short,grid))**2
        output["F3"][str(n)]=dict(k=k,grid=grid.tolist(),average_power=p.tolist(),
             l1_error=float(np.trapezoid(abs(ideal-p),grid)),band_integral=float(ratio))
        output["F6"][str(n)]=dict(k=k,grid=grid.tolist(),coefficient=c.tolist(),
             in_band_relative_mse=min(loss),optimizer_loss=loss,spectrum=spec.tolist(),
             alternate_k_minus_one_loss=min(short_loss),alternate_spectrum=short_spec.tolist())
    f=np.linspace(-.045,.045,1801)
    a=tapers(500,10,2)[1]
    cos=shift(a,1,.013,"COS")
    ssb=shift(a,1,.013,"SSB")
    # Time-index origin in the paper is n=0. The CS sum cancels
    # interference independently of phase origin.
    e=tapers(500,4,1)[0]
    phase=2*np.pi*.003*np.arange(e.size)
    raw=np.column_stack((a,cos,ssb,e,e*np.cos(phase),e*np.sin(phase)))
    filt=held_ff(raw,1.,f)
    plus=dpswf(e,f-.003)*np.exp(-1j*np.pi*e.size*(f-.003))
    minus=dpswf(e,f+.003)*np.exp(-1j*np.pi*e.size*(f+.003))
    cs_theory=.125*np.sinc(f)**2*(abs(plus)**2+abs(minus)**2)
    # The literal printed plus sign in the SIN cross term fails for f=0,
    # where the two real spectral components are equal.
    centered=(np.arange(len(e))-(len(e)-1)/2)
    centered_sin=e*np.sin(2*np.pi*.003*centered)
    output["F4"]=dict(frequency=f.tolist(),unshifted=filt[:,0].tolist(),COS=filt[:,1].tolist(),
        SSB=filt[:,2].tolist(),k0=filt[:,3].tolist(),COS_small=filt[:,4].tolist(),SIN=filt[:,5].tolist(),
        CS=(filt[:,4]+filt[:,5]).tolist(),
        cs_theory_error=float(max(abs(cs_theory-filt[:,4]-filt[:,5]))),
        sine_dc_time=float(abs(centered_sin.sum())**2/4),
        sine_dc_literal=float(abs(dpswf(e,np.array([.003]))[0])**2/4))
    fa=np.linspace(-.07,1.,4281)
    carrier=np.array([0,5/16,7/16])
    raw=cos_bank(500,4,1,1.,carrier)
    # Plot envelope and peak positions, with all spectra scaled to the same
    # envelope at the corresponding digital frequency.
    norm=abs(dpswf(raw,carrier)[np.arange(3),np.arange(3)])**2
    p=held_ff(raw,1.,fa)/norm
    peak=[]
    for col,nominal in ((0,0),(1,5/16),(2,7/16),(2,9/16),(1,11/16)):
        keep=abs(fa-nominal)<.01
        peak.append([nominal,float(fa[keep][np.argmax(p[keep,col])]),float(np.max(p[keep,col]))])
    output["F5"]=dict(frequency=fa.tolist(),spectrum=p.T.tolist(),peaks=peak,
        envelope=(.25*np.sinc(fa)**2).tolist())
    # Figure 1 has schematic PSDs with no physical axis labels or parameters.
    # Use declared comparison spectra and retain the original CPMG order.
    f=np.linspace(0,60,3001)
    ff=abs(rse(f,1.,12,1.))**2/4
    within=abs(f-6)<=1
    pds=[1/(1+((f-6)/2)**2),1/(1+((f-6)/2)**2)+3/(1+((f-18)/1.5)**2)]
    total=[float(np.trapezoid(ff*x,f)) for x in pds]
    inside=[float(np.trapezoid(ff[within]*x[within],f[within])) for x in pds]
    output["F1"]=dict(frequency=f.tolist(),rse_power=ff.tolist(),target=[x.tolist() for x in pds],
                      leakage_fraction=[(a-b)/a for a,b in zip(total,inside)])
    return output

