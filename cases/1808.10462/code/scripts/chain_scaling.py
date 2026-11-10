"""Fig. 6 analytic recurrence and a discretized phase-only search on ion chains."""
from phase_controls import PSI,geometry,matrix_terms,form_from_terms,physical_pulse,save
from analytic_phase import response,complex_list
from closed_phase import phase_candidates,prepare,real_map

from itertools import combinations
import json
from pathlib import Path
import sys
import numpy as np
from scipy.optimize import minimize


def analytic_response(detuning,duration,order):
    """Endpoint and ordered area at any prefix; doubling uses one modal vector."""
    m=detuning.shape[-1]
    theta=-2*np.pi*np.asarray(duration)[...,None]*detuning
    width=2.**-m
    step=theta*width
    alpha=width*np.sinc(step/(2*np.pi))*np.exp(0.5j*step)
    area=np.empty_like(step)
    tiny=abs(step)<1e-3
    z=step[tiny]
    area[tiny]=width**2*(z/6-z**3/120+z**5/5040)
    z=step[~tiny]
    area[~tiny]=width**2*(z-np.sin(z))/z**2
    for i in range(m):
        target=np.take_along_axis(theta,order[...,i,None],axis=-1)
        b=-np.exp(1j*(theta-target)*width)
        area=2*area+b.imag*abs(alpha)**2
        alpha=alpha*(1+b)
        width*=2
    return alpha,area


def analytic_search(freq,product,f):
    lasers=np.linspace(freq.min()-10000,freq.max()+10000,33)
    d=lasers[:,None]-freq
    order=np.argsort(abs(d),axis=1)[:,::-1]
    out=[]
    top=[]
    for start in range(10,f["maximum_analytic_duration_us"]+1,1000):
        times=np.arange(start,min(start+1000,f["maximum_analytic_duration_us"]+1),10)
        t=times[:,None]*1e-6
        alpha,area=analytic_response(d[None,:,:],t,order[None,:,:])
        scale=2*np.pi*t*f["rabi_hz"]
        phase=2*np.einsum("tlm,m->tl",area,product)*scale**2
        for j,tus in enumerate(times):
            k=int(np.argmax(abs(phase[j])))
            out.append([int(tus),float(lasers[k]),float(phase[j,k])])
            if abs(phase[j,k])>=PSI and not top:
                top=dict(time_us=int(tus),laser_hz=float(lasers[k]),angle_at_cap=float(phase[j,k]),
                         peak_rabi_hz=float(f["rabi_hz"]*np.sqrt(PSI/abs(phase[j,k]))),
                         order=order[k].tolist(),detuning_hz=d[k].tolist(),endpoint_max=float(abs(alpha[j,k]).max()))
                return dict(status="witness",first=top,grid=out)
    return dict(status="not_found_on_grid",first=None,grid=out)


def record(wave,freq,laser,t,coupling,robust,threshold,sign=1):
    d=laser-freq
    a,area=response(d,t,wave)
    w=matrix_terms(d,t,len(wave))
    cm=np.einsum("ms,s->m",w[0]-w[1],wave)
    phase=2*np.sum(coupling.prod(axis=0)*area)
    return dict(angle_rad=float(phase),displacement_squared=float(np.sum(abs(coupling*a)**2)),
                centroid_squared=float(np.sum(abs(coupling*cm)**2)),
                metric=float(np.sum(abs(coupling*(cm if robust else a))**2)),
                phase_consistent=bool(abs(phase-sign*PSI)<1e-8),within_source_tolerance=bool(np.sum(abs(coupling*(cm if robust else a))**2)<=threshold))


def relaxed(terms,coupling,cap,reflection,threshold,start,sign=1):
    """Source Appendix E uses a bound on displacement or trajectory centroid."""
    count=terms[0].shape[1]
    basis=real_map(count,reflection)
    q=form_from_terms(terms,coupling,reflection)[1]
    a,first,_=terms
    a=a-first if reflection else a
    a=np.linalg.norm(coupling,axis=0)[:,None]*a
    A=np.einsum("ms,sj->mj",a,basis)
    C=cap**2*np.einsum("mi,mj->ij",A.conj(),A).real/threshold
    Q=sign*cap**2*np.einsum("si,sj->ij",basis.conj(),np.einsum("st,tj->sj",q,basis)).real
    h=len(Q)//2

    def evaluate(x,m):
        c,s=np.cos(x),np.sin(x)
        v=np.r_[c,s]
        product=np.einsum("ij,j->i",m,v)
        return float(np.dot(v,product)),2*(c*product[h:]-s*product[:h])

    def target(x):
        loss,j=evaluate(x,Q)
        return -loss,-j

    def limit(x):
        return 1-evaluate(x,C)[0]

    def jac(x):
        return -evaluate(x,C)[1]

    result=minimize(target,np.angle(start),jac=True,method="SLSQP",constraints=[dict(type="ineq",fun=limit,jac=jac)],
                    options=dict(maxiter=120,ftol=1e-10))
    phase=-result.fun
    if phase>=PSI and limit(result.x)>-1e-8:
        return physical_pulse(cap*np.exp(1j*result.x)*np.sqrt(PSI/phase),reflection)
    return None


def search_sign(freq,coupling,robust,terms,center,lasers,sample,basis,t,cap,threshold,seed,sign):
    a,q=form_from_terms(terms,coupling,robust)
    prob=prepare(a,q,basis)
    candidates={}
    wave,_=phase_candidates(prob,sign,cap,sign*1e-8,seed,attempts=1)
    if wave is not None:
        shape=physical_pulse(wave/abs(wave[0]),robust)
    else:
        h=basis.shape[1]//2
        vec=prob[3][:,-1 if sign>0 else 0]
        shape=physical_pulse(np.exp(1j*np.angle(vec[:h]+1j*vec[h:])),robust)
    fast=[]
    for laser in lasers:
        moved=shape*np.exp(2j*np.pi*(laser-center)*t*sample)
        alpha,area=response(laser-freq,t,moved)
        angle=float(sign*2*np.sum(coupling.prod(axis=0)*area)*cap**2)
        fast.append(angle)
        if angle>=PSI:
            scaled=moved*cap*np.sqrt(PSI/angle)
            info=record(scaled,freq,laser,t,coupling,robust,threshold,sign)
            if info["within_source_tolerance"] and info["phase_consistent"]:
                candidates[laser]=(angle,scaled,info,"transferred_shape")
    if not candidates:
        ranking=np.argsort(fast)[::-1]
        for idx in ranking[:3]:
            laser=lasers[idx]
            mat=matrix_terms(laser-freq,t,len(sample))
            a,q=form_from_terms(mat,coupling,robust)
            p=prepare(a,q,basis)
            starting=(shape*np.exp(2j*np.pi*(laser-center)*t*sample))[:basis.shape[1]//2]
            exact,_=phase_candidates(p,sign,cap,sign*PSI,seed+int(idx),attempts=1,initial=starting)
            got=physical_pulse(exact,robust) if exact is not None else None
            how="exact_closure"
            if got is None and max(fast)>0.66*PSI:
                got=relaxed(mat,coupling,cap,robust,threshold,starting,sign)
                how="source_tolerance"
            if got is not None:
                info=record(got,freq,laser,t,coupling,robust,threshold,sign)
                if info["phase_consistent"] and info["metric"]<=threshold*(1+1e-8):
                    candidates[laser]=(float(PSI*(cap/abs(got[0]))**2),got,info,how)
    if not candidates:
        return None,float(max(fast))
    laser,(angle,winner,info,how)=max(candidates.items(),key=lambda x:x[1][0])
    best=dict(laser_hz=float(laser),peak_rabi_hz=float(abs(winner[0])/(2*np.pi*t)),signed_branch=sign,
              solve_method=how,rotation=complex_list(winner/abs(winner[0])),**info)
    return best,float(max(fast))


def shortest(freq,coupling,f,robust,seed):
    count=len(freq)*(8 if robust else 4)
    center=np.mean(freq)
    lasers=np.linspace(freq.min()-10000,freq.max()+10000,f["laser_grid_points"])
    sample=(np.arange(count)+.5)/count-.5
    basis=real_map(count,robust)
    threshold=f["motion_threshold"]
    grid=[]
    lower=np.sqrt(np.pi*PSI/np.sum(abs(coupling.prod(axis=0))))/(2*np.pi*f["rabi_hz"])*1e6
    step=f["numeric_time_step_us"]
    start=max(f["minimum_duration_us"],int(np.floor(lower/step)*step)-step)
    for tus in range(start,f["numeric_maximum_duration_us"]+1,step):
        t=tus*1e-6
        cap=2*np.pi*t*f["rabi_hz"]
        terms=matrix_terms(center-freq,t,count)
        positive,pos=search_sign(freq,coupling,robust,terms,center,lasers,sample,basis,t,cap,threshold,seed+tus,1)
        negative,neg=search_sign(freq,coupling,robust,terms,center,lasers,sample,basis,t,cap,threshold,seed+tus,-1)
        grid.append(dict(time_us=int(tus),positive_transferred_angle_rad=pos,negative_transferred_magnitude_rad=neg,
                         positive_witness=positive is not None,negative_witness=negative is not None))
        # Keep the signed provenance. A negative phase makes the other
        # maximally entangled state and needs a local Z conjugation to
        # match the Appendix E positive-angle operator.
        first=positive if positive is not None else negative
        if first is not None:
            first["time_us"]=int(tus)
            assert first["peak_rabi_hz"]<=f["rabi_hz"]*(1+1e-10)
            return dict(status="witness",segments=count,first=first,grid=grid,closed_isoperimetric_lower_us=float(lower))
    return dict(status="not_found_on_grid",segments=count,first=None,grid=grid,closed_isoperimetric_lower_us=float(lower))


def main():
    cfg=json.loads(Path("config/followup.json").read_text())
    f=cfg["figure6"]
    mode=sys.argv[1]
    if mode=="length":
        n=int(sys.argv[2])
        freq,c,z,residual=geometry(cfg,n,f["trap_hz"])
        coupling=c[:2]
        out=dict(ions=n,mode_frequencies_hz=freq.tolist(),equilibrium_positions=z.tolist(),
                 force_residual=residual,couplings=coupling.tolist(),analytic=analytic_search(freq,coupling.prod(axis=0),f))
        for j,k in [(False,"standard"),(True,"robust")]:
            out[k]=shortest(freq,coupling,f,j,306000+n*100)
        print(n,[(k,(out[k]["first"] or {}).get("time_us")) for k in ("analytic","standard","robust")],flush=True)
        save(f"results/scale-length-{n:02d}.json",out)
    else:
        start,end=map(int,sys.argv[2:])
        freq,c,z,residual=geometry(cfg,10,f["trap_hz"])
        rows=[]
        for i,(j,k) in enumerate(list(combinations(range(10),2))[start:end],start):
            coupling=c[[j,k]]
            r=shortest(freq,coupling,f,False,309000+i*1000)
            print(j+1,k+1,(r["first"] or {}).get("time_us"),flush=True)
            product=abs(coupling.prod(axis=0))
            rows.append(dict(pair=[j+1,k+1],couplings=coupling.tolist(),normed_product=(product/product.max()).tolist(),result=r))
        save(f"results/scale-pairs-{start:02d}-{end:02d}.json",
             dict(ions=10,mode_frequencies_hz=freq.tolist(),equilibrium_positions=z.tolist(),force_residual=residual,rows=rows))


if __name__=="__main__":
    main()
