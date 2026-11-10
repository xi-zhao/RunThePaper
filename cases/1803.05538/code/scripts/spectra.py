"""Numerical experiments from Sections IV and V, with exact shot budgets."""

import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.linalg import solve

from base_filters import tapers
from filters import cos_bank, held_ff, normalized, optimal_setting, rse


def integral(f, curves, points):
    """Integrate piecewise-linear tabulations at arbitrary band boundaries."""
    point=np.asarray(points)
    x=np.clip(np.searchsorted(f,point,side="right")-1,0,len(f)-2)
    delta=point-f[x]
    accum=cumulative_trapezoid(curves,f,axis=-1,initial=0)
    slope=(curves[...,x+1]-curves[...,x])/(f[x+1]-f[x])
    return accum[...,x]+delta*(curves[...,x]+delta*slope/2)


def band_integrals(f, kernel, centers, half_width):
    return np.array([integral(f,c,s+half_width)-integral(f,c,max(0.,s-half_width))
                     for s,c in zip(centers,kernel,strict=True)])


def statistics(f, kernel, centers, width, target, shots, rng):
    normal=2*band_integrals(f,kernel,centers,width)
    signal=2*np.trapezoid(kernel*target, f, axis=-1)
    assert np.all((signal>=0)&(signal<=1))
    count=rng.binomial(shots,signal)
    observed=count/shots/normal
    return dict(normal=normal,signal=signal,expected=signal/normal,count=count,
                estimate=observed,std=np.sqrt(signal*(1-signal)/shots)/normal,
                exact_gaussian_bias=(.5*(-np.expm1(-2*signal))-signal)/normal)


def lorentzian(f, peak, width, amplitude):
    return amplitude/(1+((f-peak)/width)**2)


def lorentzian_comparison(rng):
    order=np.r_[0,np.arange(2,41)]
    centers=order*250.
    f=np.r_[np.arange(0,30_000,2.),np.arange(30_000,250_000,25.),np.arange(250_000,1_000_001,100.)]
    a=cos_bank(500,1,1,4e-6,centers)
    ds=held_ff(a,4e-6,f).T
    rr=np.array([abs(rse(f,.002,n,900.))**2/4 for n in order])
    p=np.linspace(0,10000,2001)
    shown=[0,1,2,3,6]
    curves=dict(frequency=p,rse=np.array([np.interp(p,f,rr[i]) for i in shown]),
                dpss=np.array([np.interp(p,f,ds[i]) for i in shown]),centers=centers[shown])
    bias={}
    for tag,n in (("centered",0),("off_center",4620)):
        spec=lorentzian(f,n,1110,.0004)
        truth=lorentzian(centers,n,1110,.0004)
        expected={}
        for name, filt in (("RSE",rr),("DPSS",ds)):
            z=statistics(f,filt,centers,500.,spec,2000,rng)
            z["relative_bias"]=(z["expected"]-truth)/truth
            z["relative_std"]=z["std"]/truth
            z["lowband_max_relative_bias"]=float(np.max(abs(z["relative_bias"][centers<=2000])))
            z["lowband_mean_std"]=float(np.mean(z["std"][centers<=2000]))
            expected[name]=z
        bias[tag]=dict(frequency=centers,truth=truth,**expected)
    return curves,bias


def comb_factor(f, tau, repeats):
    cycles=f*tau
    phase=cycles-np.rint(cycles)
    return (repeats*np.sinc(repeats*phase)/np.sinc(phase))**2


def two_peaks(f):
    return .0005*np.exp(-.5*(f/3500)**2)+.00035*np.exp(-.5*((f-23900)/6210)**2)


def alias_comparison(rng):
    f=np.arange(0,130_000+2,2.)
    target=two_peaks(f)
    output={}
    for key,base,n,dt in (("low",942e-6,260,39.3e-6),("high",245e-6,1000,10.2e-6)):
        h=np.arange(1,13)
        harmonic=h/base
        scale=20
        rows=base/h
        design=np.array([2*scale/tau*abs(rse(harmonic,tau,2,900.))**2/4
                         for tau in rows])
        design[(h[None,:] % h[:,None])!=0] = 0
        measurements=np.array([2*np.trapezoid(abs(rse(f,tau,2,900.))**2/4*
                          comb_factor(f,tau,scale)*target,f) for tau in rows])
        comb=solve(design,measurements)
        centers=np.arange(0,1/(2*dt),1/942e-6) if key=="high" else harmonic
        taper=cos_bank(n,1,1,dt,centers)
        spec=held_ff(taper,dt,f).T
        ds=statistics(f,spec,centers,1/(n*dt),target,2600,rng)
        output[key]=dict(comb_frequency=harmonic, comb=comb, comb_condition=float(np.linalg.cond(design)),
             comb_resolution_hz=1/base, dpss_frequency=centers, dpss=ds["expected"],
             nyquist_dpss=1/(2*dt), nyquist_comb=12/base,
             truth_on_comb=two_peaks(harmonic),truth_on_dpss=two_peaks(centers))
    return output


def line(f):
    return lorentzian(f,7960,80,.004)+.0002*(f<=17500)


def adaptive_weights(f, kernels, norm, centers, half_width, estimate):
    history=[estimate[:,0]]
    for _ in range(3):
        guess=np.interp(f,centers,history[-1],right=history[-1][-1])*(f<=17500)
        weighted=kernels*guess
        inside=band_integrals(f,weighted,centers,half_width)
        outside=2*(np.trapezoid(weighted,f,axis=-1)-inside)/norm
        anchor=np.maximum(history[-1][:,None],1e-12)
        weight=anchor/(anchor+outside)
        weight=weight/weight.sum(axis=1,keepdims=True)
        history.append(np.sum(weight*estimate,axis=1))
    return weight,np.array(history)


def line_detection(rng):
    f=np.arange(0,50000+2,2.)
    centers=np.arange(9)*1750.
    half=1750.
    dt=8e-6
    ds=held_ff(cos_bank(500,7,13,dt,centers),dt,f).T.reshape(9,13,len(f))
    setting,c,loss=optimal_setting(500,7,13)
    carrier=np.cos(2*np.pi*centers[:,None]*dt*np.arange(500))
    single=held_ff(normalized((carrier*setting).T,dt),dt,f).T
    k0=statistics(f,ds[:,0],centers,half,line(f),2600,rng)
    ssqm=statistics(f,single,centers,half,line(f),2600,rng)
    all_k=statistics(f,ds,centers,half,line(f),200,rng)
    adaptive, history=adaptive_weights(f,ds,all_k["normal"],centers,half,all_k["estimate"])
    adaptive_mu, expected_history=adaptive_weights(f,ds,all_k["normal"],centers,half,all_k["expected"])
    effective=np.sum(adaptive[:,:,None]*ds/all_k["normal"][:,:,None],axis=1)
    variance=np.sum((adaptive*all_k["std"])**2,axis=1)
    crop=(f>=3500)&(f<=11000)&(np.arange(len(f))%5==0)
    data=dict(centers=centers,target_frequency=f[::10],target=line(f[::10]), k0=k0,SSQM=ssqm,AQM=all_k,
             adaptive=adaptive,history=history,mean_history=expected_history,iteration_max_change=np.max(abs(np.diff(history,axis=0)),axis=1),
             coefficient=c,optimizer_loss=loss,frequency=f[crop],kernels=[ds[3:6,0][:,crop],single[3:6][:,crop],effective[3:6][:,crop]],
             narrowline_estimate=[k0["expected"][4:6],ssqm["expected"][4:6],expected_history[-1][4:6]])
    return data,(f,centers,effective,variance,history[-1],expected_history[-1])


def posterior_line(rng,broad):
    f,_,effective,variance,rough,rough_mean=broad
    edges=150.*np.arange(95)
    bins=(edges[1:]+edges[:-1])/2
    B=2*np.diff(integral(f,effective,edges),axis=-1)
    fisher=B**2/variance[:,None]
    w=(fisher/fisher.sum(axis=0,keepdims=True)).T
    prior=w@rough
    prior_expected=w@rough_mean
    prior_cov=(w*variance)@w.T
    centers=5300+150.*np.arange(1,35)
    dt=20e-6
    ff=held_ff(cos_bank(500,1,1,dt,centers),dt,f).T
    obs=statistics(f,ff,centers,100.,line(f),2600,rng)
    H=2*np.diff(integral(f,ff,edges),axis=-1)/obs["normal"][:,None]
    sigma=obs["std"]**2
    error_floor=np.eye(len(bins))
    sweep={}
    for factor in (0.25,1.,4.):
        # λ is omitted in the paper; keep a documented scale sensitivity.
        ridge=2.25e-8*factor
        C=prior_cov+ridge*error_floor
        L=H@C@H.T+np.diag(sigma)
        G=solve(L,(C@H.T).T,assume_a="pos").T
        updated=prior+G@(obs["estimate"]-H@prior)
        updated_expected=prior_expected+G@(obs["expected"]-H@prior_expected)
        updated_cov=C-G@(H@C)
        use=(bins>=5400)&(bins<=10300)
        truth=line(bins)
        sweep[str(factor)]=dict(prior_std=np.sqrt(np.diag(C)),posterior=updated,
            posterior_expected=updated_expected,posterior_std=np.sqrt(np.diag(updated_cov)),
            prior_cond=np.linalg.cond(C),variance_reduction=np.mean(np.diag(updated_cov)[use]/np.diag(C)[use]),
            posterior_peak_hz=bins[np.argmax(updated)],prior_rmse=np.sqrt(np.mean((prior[use]-truth[use])**2)),
            posterior_rmse=np.sqrt(np.mean((updated[use]-truth[use])**2)),
            expected_posterior_rmse=np.sqrt(np.mean((updated_expected[use]-truth[use])**2)))
    probe=np.linspace(5000,11000,1501)
    rep=held_ff(cos_bank(500,1,1,dt,[7500]),dt,probe)[:,0]
    return dict(bins_hz=bins,truth=line(bins),prior=prior,prior_expected=prior_expected,
        fisher_row_sums=w.sum(axis=1),narrow_centers=centers,narrow_observed=obs,
        representative_filter=dict(frequency=probe,value=rep/rep.max()),regularization=sweep)


def all_spectra(seed):
    rng=np.random.default_rng(seed)
    f7,f8=lorentzian_comparison(rng)
    f9=alias_comparison(rng)
    f10,broad=line_detection(rng)
    f11=posterior_line(rng,broad)
    return dict(F7=f7,F8=f8,F9=f9,F10=f10,F11=f11)

