"""Phase-averaged single-ion filters and two-ion Bell populations for Fig. 5."""
from phase_controls import geometry,PSI,save
from analytic_phase import concatenate,response,scaled_gate
import numpy as np
from scipy.constants import atomic_mass,hbar
from scipy.special import roots_legendre
import json
from pathlib import Path


def time_grid(count,steps):
    subdivisions=max(1,steps//count)
    n=count*subdivisions
    s=(np.arange(n)+0.5)/n
    return s,n,subdivisions


def noise_profiles(model,w,s,phases):
    x=w*s[None,:]+phases[:,None]
    if model=="amplitude":
        return np.sin(x)
    if model=="product":
        return s[None,:]*np.sin(x)
    return s[None,:]*np.sinc(w*s[None,:]/(2*np.pi))*np.sin(phases[:,None]+w*s[None,:]/2)


def dynamic_response(detuning,t,wave,cycles,beta,model,phases,steps,reference_hz=None):
    s,n,subdivisions=time_grid(len(wave),steps)
    raw=np.repeat(wave,subdivisions)
    omega=-2*np.pi*t*np.asarray(detuning)
    base=np.exp(1j*omega[:,None]*s)*raw/n
    profiles=noise_profiles(model,2*np.pi*cycles,s,phases)
    if model=="amplitude":
        controls=base[None,:,:]*(1+beta*profiles[:,None,:])
    else:
        theta=omega if reference_hz is None else -2*np.pi*t*np.full(len(omega),reference_hz)
        controls=base[None,:,:]*np.exp(1j*beta*theta[None,:,None]*profiles[:,None,:])
    alpha=controls.sum(axis=-1)
    # Ordered between-bin area. The within-bin constant-force midpoint
    # area is O(n^-2) over the full pulse and is monitored by refinement.
    p=np.cumsum(controls,axis=-1)-controls
    area=np.sum((controls*p.conj()).imag,axis=-1)
    return alpha,area


def derivative(detuning,t,wave,cycles,beta,model,reference_hz=None):
    theta=-2*np.pi*t*np.asarray(detuning)
    count=len(wave)
    x,w=roots_legendre(10)
    # Composite Gauss on a grid that includes all discontinuities.
    n=count*max(1,128//count)
    s=((np.arange(n)[:,None]+(x+1)/2)/n).ravel()
    weights=np.tile(w/(2*n),n)*np.repeat(wave,10*(n//count))
    base=np.exp(1j*theta[:,None]*s)*weights
    p=noise_profiles(model,2*np.pi*cycles,s,np.array([0,np.pi/2]))
    integral=np.einsum("ms,ps->pm",base,p)
    if model=="amplitude":
        return beta*integral
    if reference_hz is not None:
        theta=-2*np.pi*t*np.full(len(theta),reference_hz)
    return 1j*beta*theta*integral


def p1_single(displacement,thermal):
    return -0.5*np.expm1(-4*np.sum(abs(displacement)**2*(np.asarray(thermal)+0.5),axis=-1))


def scans(cfg):
    f=cfg["figure5"]
    phase=2*np.pi*np.arange(f["phase_samples"])/f["phase_samples"]
    modes=np.array([1.6e6,1.6e6-f["single_ion_gap_hz"]])
    f1=(np.pi/cfg["projection_wavelength_m"])*np.sqrt(hbar/(4*np.pi*cfg["mass_amu"]*atomic_mass*modes))
    out=[]
    x=np.unique(np.r_[np.geomspace(.01,5,91),.05,.1,.2,.5,1,2])
    for noise,duration,beta in [("detuning",f["detuning_duration_us"],f["detuning_beta"]),
                                ("amplitude",f["amplitude_duration_us"],f["amplitude_beta"])]:
        t=duration*1e-6
        delta=np.array([1/t,1/t+f["single_ion_gap_hz"]])
        primitive=np.ones(1)
        closure=[delta[1],delta[0],delta[0]] if noise=="detuning" else [delta[0],delta[0]]
        pm=concatenate(closure,t)
        nominal_area=response(delta,t,primitive)[1][0]
        pm_area=response(delta,t,pm)[1][0]
        rabi_ratio=np.sqrt(abs(nominal_area/pm_area))
        for name,wave,ratio in [("primitive",primitive,1),("PM2",pm,rabi_ratio)]:
            rabi=f["single_rabi_hz"]*ratio
            c=f1*(2*np.pi*rabi*t)
            nominal=p1_single(c*response(delta,t,wave)[0],f["single_thermal"])
            # Both the paper's t*epsilon model and integrated-frequency FM
            # receive the same sinusoidal modulation in radians per second.
            protocols=(("product",None),("integrated",None),("integrated_common",delta[0])) if noise=="detuning" else (("amplitude",None),)
            for label,ref in protocols:
                model=label.split("_")[0]
                rows=[]
                for cycles in x:
                    a,_=dynamic_response(delta,t,wave,cycles,beta,model,phase,512,ref)
                    deriv=derivative(delta,t,wave,cycles,beta,model,ref)
                    linear=float(np.mean(np.sum((2*np.asarray(f["single_thermal"])+1)*abs(c*deriv)**2,axis=1)))
                    p1=float(np.mean(p1_single(c*a,f["single_thermal"])))
                    rows.append([float(cycles),p1,linear])
                checks=[]
                for cycles in (.05,.2,1.,2.):
                    base=512
                    p0,_=dynamic_response(delta,t,wave,cycles,beta,model,phase,base,ref)
                    p2,_=dynamic_response(delta,t,wave,cycles,beta,model,phase,4*base,ref)
                    small=1e-3
                    probe=np.array([0,np.pi/2])
                    a,_=dynamic_response(delta,t,wave,cycles,beta*small,model,probe,4*base,ref)
                    b,_=dynamic_response(delta,t,wave,cycles,-beta*small,model,probe,4*base,ref)
                    fd=(a-b)/(2*small)
                    deriv=derivative(delta,t,wave,cycles,beta,model,ref)
                    checks.append(dict(cycles=cycles,p1_change=float(abs(np.mean(p1_single(c*p0,f["single_thermal"]))-
                                    np.mean(p1_single(c*p2,f["single_thermal"])))),
                                    linear_derivative_error=float(abs(fd-deriv).max())))
                out.append(dict(noise=noise,model=label,sequence=name,segments=len(wave),duration_us=duration,beta=beta,
                           rabi_hz=float(rabi),nominal_p1=float(nominal),detunings_hz=delta.tolist(),rows=rows,checks=checks))
    return out


def coherence(displacement,phase,occupation):
    f=np.asarray(occupation)+.5
    d1,d2=displacement[:,0,:],displacement[:,1,:]
    ep=np.exp(-4*np.sum(f*abs(d1+d2)**2,axis=-1))
    em=np.exp(-4*np.sum(f*abs(d1-d2)**2,axis=-1))
    c=np.exp(-4*np.sum(f*abs(d1)**2,axis=-1))
    return (2+ep+em)/4,(ep-em-4j*c*np.sin(2*phase))/8


def bell_scans(cfg):
    f=cfg["figure5"]
    t=f["bell_duration_us"]*1e-6
    modes,c,_,_=geometry(cfg,2,[1600000,1500000,500000])
    delta=modes[-1]+f["bell_detuning_from_lowest_hz"]-modes
    pulses={"primitive":np.ones(1),"PM2":concatenate([delta[3]]*2,t),
            "PM3":concatenate([delta[1],delta[2],*([delta[3]]*3)],t)}
    phase=2*np.pi*np.arange(f["phase_samples"])/f["phase_samples"]
    out=[]
    for name,wave in pulses.items():
        rabi,_,target=scaled_gate(cfg,delta,t,wave,c)
        scale=2*np.pi*rabi*t
        for model,beta,ref in [("product",f["bell_detuning_beta"],abs(delta[-1])),
                              ("integrated",f["bell_detuning_beta"],abs(delta[-1])),
                              ("amplitude",f["bell_amplitude_beta"],None)]:
            history=[]
            for steps in (512,1024,2048):
                d,a=dynamic_response(delta,t,wave,f["bell_cycles"],beta,model,phase,steps,ref)
                angle=2*np.einsum("m,pm->p",c.prod(axis=0),a)*scale**2
                pop,coh=coherence(c[None,:,:]*d[:,None,:]*scale,angle,[0,0,0,.1])
                mean=np.mean(coh)
                # Optimize one parity phase after forming the ensemble state.
                history.append(dict(steps=steps,p1=float(1-pop.mean()),bell=float(pop.mean()/2+abs(mean)),
                    fixed_nominal_bell=float(pop.mean()/2-np.sign(target)*mean.imag),
                    mean_phase_rad=float(angle.mean()),sd_phase_rad=float(angle.std())))
            out.append(dict(sequence=name,rabi_hz=rabi,nominal_signed_phase_rad=target,
                            cap_supported=rabi<=40000,model=model,beta=beta,rows=history))
    return out


if __name__=="__main__":
    cfg=json.loads(Path("config/followup.json").read_text())
    save("results/dynamic-noise.json",dict(single_ion=scans(cfg),two_ion=bell_scans(cfg)))
