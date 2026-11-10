"""Prepare and verify phase-only controls in the Milne shared-force model."""
from chain_geometry import modes
from analytic_phase import concatenate,observables,path,response,complex_list
from closed_phase import phase_candidates,prepare,real_map

import json
from pathlib import Path
import numpy as np
from scipy.linalg import toeplitz
from scipy.optimize import least_squares

PSI=np.pi/4


def geometry(cfg,n,trap):
    f,eta,z,force=modes(dict(ions=n,ion_mass_amu=cfg["mass_amu"],wavelength_m=cfg["projection_wavelength_m"],
                            transverse_com_hz=trap[:2],axial_com_hz=trap[2]))
    order=np.argsort(f)[::-1]
    return f[order],0.5*eta[:,order],z,force


def matrix_terms(detuning,t,count):
    theta=-2*np.pi*t*np.asarray(detuning)
    width=1/count
    dt=theta*width
    center=(np.arange(count)+0.5)*width
    e=np.exp(1j*theta[:,None]*center)
    a=width*np.sinc(dt[:,None]/(2*np.pi))*e
    b=np.empty_like(dt)
    y=np.empty_like(dt)
    small=abs(dt)<1e-3
    x=dt[small]
    b[small]=width**2*(x/6-x**3/120+x**5/5040)
    y[small]=width**2*(x/12-x**3/480+x**5/53760)
    x=dt[~small]
    b[~small]=width**2*(x-np.sin(x))/x**2
    y[~small]=width**2*(2*np.sin(x/2)-x*np.cos(x/2))/x**2
    first=a*center+1j*y[:,None]*e
    l=1j*abs(a[:,:1])**2*np.exp(-1j*dt[:,None]*np.arange(count))
    l[:,0]=2*b
    return a,first,l


def form_from_terms(terms,coupling,robust,weights=None):
    a,first,modal=terms
    q=toeplitz(np.einsum("p,ps->s",coupling[0]*coupling[1],modal))
    constraints=np.vstack((a,first)) if robust else a
    if weights is not None:
        constraints=constraints*weights[:,None]
    return constraints,q


def physical_pulse(x,reflection):
    return np.r_[x,x[::-1].conj()] if reflection else x


def exact_gate(detuning,t,coupling,count,rabi,robust,seed,signs=(1,-1),initial=None,attempts=3):
    terms=matrix_terms(detuning,t,count)
    constr,q=form_from_terms(terms,coupling,robust)
    basis=real_map(count,robust)
    prepared=prepare(constr,q,basis)
    cap=2*np.pi*rabi*t
    best=[]
    decisions={}
    for sign in signs:
        wave,rec=phase_candidates(prepared,sign,cap,sign*PSI,seed,attempts=attempts,initial=initial)
        decisions[str(sign)]=rec
        if wave is not None:
            actual=physical_pulse(wave,robust)
            best.append((float(abs(actual[0])/cap),sign,actual))
    if not best:
        return None,decisions
    _,sign,wave=min(best,key=lambda x:(x[1]<0,x[0]))
    return wave,decisions


def test_shapes(cfg):
    g=cfg["figure1"]
    t=g["duration_us"]*1e-6
    d=np.array(g["detunings_hz"])
    rows=[]
    for robust,count in [(False,8),(True,16)]:
        a,first,_=matrix_terms(d,t,count)
        raw=np.vstack((a,first)) if robust else a
        basis=real_map(count,robust)
        matrix=np.einsum("rs,si->ri",raw,basis)
        x,y,z=np.linalg.svd(np.vstack((matrix.real,matrix.imag)),full_matrices=False)
        rank=sum(y>y[0]*1e-12)
        q=z[:rank]
        h=q.shape[1]//2
        rng=np.random.default_rng(300100+count)

        def residual(phi):
            return np.einsum("rs,s->r",q,np.r_[np.cos(phi),np.sin(phi)])

        def jacobian(phi):
            return -q[:,:h]*np.sin(phi)+q[:,h:]*np.cos(phi)

        attempts=[least_squares(residual,rng.uniform(-np.pi,np.pi,h),jac=jacobian,gtol=1e-13,ftol=1e-13,xtol=1e-13)
                  for _ in range(4)]
        best=min(attempts,key=lambda v:np.linalg.norm(v.fun))
        wave=physical_pulse(np.exp(1j*best.x),robust)
        endpoint,_=response(d,t,wave)
        moment=np.einsum("ms,s->m",first,wave)
        assert abs(endpoint).max()<1e-10
        if robust:
            assert abs(moment).max()<1e-10
        rows.append(dict(segments=count,robust=robust,rotation=complex_list(wave),endpoint=complex_list(endpoint),
            centroid=complex_list(endpoint-moment),paths=[complex_list(path(f,t,wave)) for f in d]))
    return rows


def spectrum_scan(cfg):
    a=cfg["figure2"]
    t=a["duration_us"]*1e-6
    results=[]
    for gap in a["mode_splits_hz"]:
        freq=np.array([a["upper_mode_hz"],a["upper_mode_hz"]-gap])
        from scipy.constants import atomic_mass,hbar
        f=0.5*(2*np.pi/cfg["projection_wavelength_m"])*np.sqrt(hbar/(4*np.pi*cfg["mass_amu"]*atomic_mass*freq))
        seqs=[("unmodulated",np.ones(1),[.2,.4] if gap==70000 else [1.2,1.2])]
        if gap<20000:
            seqs.append(("phase-modulated",concatenate([-8500,-8500+gap],t),[2.5,1]))
        shifts=sorted({*np.arange(-90000,20001,250).tolist(),-12500,12500,-8500})
        for name,wave,thermal in seqs:
            rows=[]
            for x in shifts:
                d=np.array([x,x+gap])
                u,_=response(d,t,wave)
                displacement=f*u*2*np.pi*t*a["rabi_hz"]
                p1=-0.5*np.expm1(-4*np.sum((np.array(thermal)+.5)*abs(displacement)**2))
                rows.append([float(x),float(p1),*abs(u).tolist()])
            results.append(dict(gap_hz=gap,method=name,thermal=thermal,rows=rows))
    return results


def static_controls(cfg):
    p=cfg["figure4"]
    t=p["duration_us"]*1e-6
    results=[]
    for az in p["axial_variants_hz"]:
        freq,f,_,_=geometry(cfg,2,[*p["transverse_com_hz"],az])
        d=freq[-1]+p["detuning_from_lowest_hz"]-freq
        for robust,count,rabi in [(False,16,p["standard_rabi_hz"]),(True,32,p["robust_rabi_hz"])]:
            # Some rounded spectra may require more power than the experimental value.
            wave,decisions=exact_gate(d,t,f,count,rabi,robust,300400+count,attempts=5)
            fixed=wave is not None
            if wave is None:
                wave,more=exact_gate(d,t,f,count,40000,robust,300401+count,attempts=5)
            else:
                more={}
            if wave is None:
                results.append(dict(axial_hz=az,robust=robust,segments=count,decisions=decisions,more=more,matched=False))
                continue
            a,first,_=matrix_terms(d,t,count)
            actual_rabi=float(abs(wave[0])/(2*np.pi*t))
            d0,area=response(d,t,wave)
            coupled=f*d0
            cm=f*np.einsum("rs,s->r",a-first,wave)
            angle=2*np.sum(f[0]*f[1]*area)
            assert abs(abs(angle)-PSI)<1e-9 and np.sum(abs(coupled)**2)<1e-16
            if robust:
                assert np.sum(abs(cm)**2)<1e-16
            rows=[]
            for shift in np.arange(-2000,2001,25):
                alpha,B=response(d+shift,t,wave)
                phase=2*np.sum(f[0]*f[1]*B)
                pop=observables(f*alpha,phase,p["thermal"])
                rows.append(dict(shift_hz=int(shift),p1=pop[1],best_bell=pop[3],signed_phase_rad=float(phase),
                                 target_displacement=float(abs(alpha[-1]*f[0,-1]))))
            local=[]
            for shift in [1,2,4,8]:
                a1,_=response(d+shift,t,wave)
                local.append(float(np.sum(abs(f*a1)**2)))
            exponent=float(np.polyfit(np.log([1,2,4,8]),np.log(local),1)[0])
            results.append(dict(axial_hz=az,robust=robust,segments=count,printed_rabi_hz=rabi,matched=fixed,
                actual_rabi_hz=actual_rabi,nominal_phase_rad=float(angle),displacement_norm=float(np.linalg.norm(coupled)),
                centroid_norm=float(np.linalg.norm(cm)),rotation=complex_list(wave/abs(wave[0])),
                source_mode_frequencies_hz=freq.tolist(),detuning_hz=d.tolist(),exponent=exponent,
                decisions=decisions,higher_cap_decisions=more,rows=rows,
                path_at_plus_500=complex_list(path(d[-1]+500,t,wave)*f[0,-1])))
    return results


def save(path,data):
    Path(path).write_text(json.dumps(data,allow_nan=False,separators=(",",":"))+"\n")


if __name__=="__main__":
    cfg=json.loads(Path("config/followup.json").read_text())
    save("results/phase-controls.json",dict(figure1=test_shapes(cfg),figure2=spectrum_scan(cfg),figure4=static_controls(cfg)))
