"""Linear Coulomb chain and source segmented common-drive optimization."""
import os
for key in ("OPENBLAS_NUM_THREADS","OMP_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
    os.environ[key]="1"
import json
from pathlib import Path
import sys
import time
import numpy as np
from scipy.constants import atomic_mass,hbar
from scipy.optimize import root,least_squares
from scipy.linalg import eigh,null_space
from two_ion_gate import segment_integrals,observe
from two_ion_response import thermal_error


def equilibrium(ions):
    def equations(z):
        differences=z[:,None]-z[None,:]
        np.fill_diagonal(differences,np.inf)
        force=np.zeros_like(differences)
        finite=np.isfinite(differences)
        force[finite]=np.sign(differences[finite])/abs(differences[finite])**2
        return z-force.sum(axis=1)
    answer=root(equations,np.linspace(-1,1,ions)*ions**0.55,tol=1e-12)
    z=np.sort(answer.x)
    assert max(abs(equations(z)))<1e-10 and min(np.diff(z))>0
    differences=abs(z[:,None]-z[None,:]);np.fill_diagonal(differences,np.inf)
    weight=differences**-3
    laplacian=np.diag(weight.sum(axis=1))-weight
    return z,laplacian,float(max(abs(equations(z))))


def modes(config):
    z,L,force_error=equilibrium(config["ions"])
    freq,part=[],[]
    for com in config["transverse_com_hz"]:
        vals,vec=eigh(com**2*np.eye(len(z))-config["axial_com_hz"]**2*L)
        assert vals.min()>0,"linear chain is unstable"
        freq.extend(np.sqrt(vals[::-1]));part.append(vec[:,::-1])
    freq=np.array(freq);vectors=np.column_stack(part)
    eta=vectors*np.sqrt(hbar/(4*np.pi*config["ion_mass_amu"]*atomic_mass*freq))[None,:]*(2*np.pi/config["wavelength_m"])
    return freq,eta,np.asarray(z),force_error


def source_matrices(config,robust):
    f,eta,z,residual=modes(config)
    count=config["robust_segments"] if robust else config["standard_segments"]
    theta=2*np.pi*config["duration_s"]*(f-config["laser_detuning_hz"])
    M=[];moment=[];C=np.zeros((count,count),complex)
    j,k=config["addressed"]
    for p,t in enumerate(theta):
        v,w,diag=segment_integrals(t,count)
        M.append(v/2);moment.append(w/2)
        K=np.tril(v[:,None]*v.conj()[None,:],-1)+1j*diag*np.eye(count)
        C+=0.5*eta[j,p]*eta[k,p]*K
    Q=(C.T-C.conj())/(2j)
    assert np.max(abs(Q-Q.conj().T))<1e-12
    return np.asarray(M),np.asarray(moment),Q,theta,eta[config["addressed"]],dict(mode_frequencies_hz=f.tolist(),equilibrium_z=z.tolist(),force_residual=residual,lamb_dicke=eta.tolist())


def pulse_and_jacobian(x,family,robust,dimension,max_u):
    if family=="AM":
        h=max_u*x.astype(complex)
        jac=max_u*np.eye(dimension,dtype=complex)
    elif family=="PM":
        phase=x[1:];rotation=np.exp(1j*phase)
        h=max_u*x[0]*rotation
        jac=np.column_stack((max_u*rotation,1j*np.diag(h)))
    elif family=="AMPM":
        amplitude=x[:dimension];phase=x[dimension:]
        rotation=np.exp(1j*phase)
        h=max_u*amplitude*rotation
        jac=np.column_stack((max_u*np.diag(rotation),1j*np.diag(h)))
    else:raise ValueError(family)
    if robust:return np.r_[h,h[::-1].conj()],np.vstack((jac,jac[::-1].conj()))
    return h,jac


def optimize_one(config,family,robust,seed):
    M,R,Q,theta,eta,geometry=source_matrices(config,robust)
    count=M.shape[1];dim=count//2 if robust else count
    max_u=2*np.pi*config["maximum_rabi_hz"]*config["duration_s"]
    rng=np.random.default_rng(seed)
    if robust:
        half=np.eye(count,dim)
        realbasis=half+half[::-1]
        B=realbasis if family=="AM" else np.column_stack((realbasis,1j*(half-half[::-1])))
    else:
        B=np.eye(count,dtype=complex) if family=="AM" else np.column_stack((np.eye(count),1j*np.eye(count)))
    linear=np.einsum("ps,sj->pj",M,B)
    constraints=[linear.real,linear.imag]
    if robust:
        moment_linear=np.einsum("ps,sj->pj",R,B)
        constraints.extend((moment_linear.real,moment_linear.imag))
    V=null_space(np.vstack(constraints),rcond=1e-10)
    Qb=np.einsum("si,sj->ij",B.conj(),np.einsum("st,tj->sj",Q,B)).real
    G=np.einsum("si,sj->ij",B.conj(),B).real
    Qn=np.einsum("ia,ib->ab",V,np.einsum("ij,jb->ib",Qb,V))
    Gn=np.einsum("ia,ib->ab",V,np.einsum("ij,jb->ib",G,V))
    eigenvalues,eigenvectors=eigh(Qn,Gn)
    target=np.pi*config["target_phase_over_pi"]["robust" if robust else "standard"]
    chosen=-1 if target>0 else 0
    assert eigenvalues[chosen]*target>0,"No requested phase sign in selected nullspace"
    coeff=np.einsum("ia,a->i",V,eigenvectors[:,chosen])
    nullpulse=np.einsum("si,i->s",B,coeff)*np.sqrt(target/eigenvalues[chosen])
    guess=nullpulse[:dim]
    if family=="AM":
        initial=np.clip(guess.real/max_u+rng.normal(0,.03,dim),-.99,.99)
        low=-np.ones(dim);high=np.ones(dim)
    elif family=="PM":
        initial=np.r_[np.clip(np.sqrt(np.mean(abs(guess)**2))/max_u,.01,.99),np.angle(guess)+rng.normal(0,.15,dim)]
        low=np.r_[0,np.full(dim,-4*np.pi)];high=np.r_[1,np.full(dim,4*np.pi)]
    else:
        initial=np.r_[np.clip(abs(guess)/max_u+rng.normal(0,.02,dim),.001,.99),np.angle(guess)+rng.normal(0,.15,dim)]
        low=np.r_[np.zeros(dim),np.full(dim,-4*np.pi)];high=np.r_[np.ones(dim),np.full(dim,4*np.pi)]
    cache={}
    def values(x):
        if "x" in cache and np.array_equal(x,cache["x"]):return cache["residual"],cache["jacobian"]
        u,J=pulse_and_jacobian(x,family,robust,dim,max_u)
        qu=np.einsum("ij,j->i",Q,u)
        phase=float(np.sum(u.conj()*qu).real)
        phase_jac=2*np.einsum("sp,s->p",J.conj(),qu).real
        closure=np.einsum("ps,s->p",M,u)
        closure_jac=np.einsum("ps,sj->pj",M,J)
        residual=[np.array([phase-target]),np.sqrt(2)*closure.real,np.sqrt(2)*closure.imag]
        jacobian=[phase_jac[None,:],np.sqrt(2)*closure_jac.real,np.sqrt(2)*closure_jac.imag]
        if robust:
            moment=np.einsum("ps,s->p",R,u)
            moment_jac=np.einsum("ps,sj->pj",R,J)
            residual.extend((np.sqrt(2)*moment.real,np.sqrt(2)*moment.imag))
            jacobian.extend((np.sqrt(2)*moment_jac.real,np.sqrt(2)*moment_jac.imag))
        rv=np.concatenate(residual);jv=np.vstack(jacobian)
        cache.update(x=x.copy(),residual=rv,jacobian=jv)
        return rv,jv
    # Verify the analytic Jacobian at the initial point before any optimization.
    rv,jv=values(initial);probes=np.unique(np.linspace(0,len(initial)-1,min(7,len(initial)),dtype=int))
    err=[]
    for idx in probes:
        e=np.zeros_like(initial);e[idx]=1e-6
        fd=(values(initial+e)[0]-values(initial-e)[0])/2e-6
        err.append(float(np.max(abs(fd-jv[:,idx]))))
    assert max(err)<1e-5,max(err)
    start=time.monotonic()
    tol=config["solver_tolerances"]
    result=least_squares(lambda x:values(x)[0],initial,jac=lambda x:values(x)[1],bounds=(low,high),
                         ftol=tol,gtol=tol,xtol=tol,max_nfev=config["max_nfev"],method="trf")
    elapsed=time.monotonic()-start
    u,_=pulse_and_jacobian(result.x,family,robust,dim,max_u)
    phase,d,m=observe(u,theta,eta)
    cost=float(np.sum(values(result.x)[0]**2))
    summary=dict(family=family,robust=robust,seed=seed,nfev=result.nfev,njev=result.njev,termination=result.status,
                 optimality=float(result.optimality),cost=cost,seconds=elapsed,jacobian_max_error=max(err),
                 phase_error=float(phase-target),maximum_displacement=float(abs(d).max()),first_moment_norm=float(np.linalg.norm(m)),
                 nominal_infidelity=thermal_error(phase-target,d,config["occupation"]),maximum_rabi_hz=float(abs(u).max()/(2*np.pi*config["duration_s"])))
    summary["initial_exact_nullspace_peak_rabi_hz"]=float(abs(nullpulse).max()/(2*np.pi*config["duration_s"]))
    summary["nullspace_dimension"]=int(V.shape[1])
    summary["target_phase"]=float(target)
    summary["nullspace_phase_eigenvalues_range"]=[float(eigenvalues[0]),float(eigenvalues[-1])]
    scan=[]
    for shift in config["detuning_error_hz"]:
        p,disp,_=observe(u,theta-shift*2*np.pi*config["duration_s"],eta)
        scan.append(dict(shift_hz=shift,phase_error=float(p-target),infidelity=thermal_error(p-target,disp,config["occupation"])))
    summary["detuning_scan"]=scan
    return u,summary,geometry


def main():
    family=sys.argv[1];robust=bool(int(sys.argv[2]))
    config=json.loads(Path("config/five-ion.json").read_text())
    name=family+("-robust" if robust else "-standard")
    runs=[];pulses=[]
    for seed in config["seeds"]:
        u,row,geo=optimize_one(config,family,robust,seed)
        runs.append(row);pulses.append(u)
        print(json.dumps({k:v for k,v in row.items() if k!="detuning_scan"}),flush=True)
    selected=int(np.argmin([r["cost"] for r in runs]))
    Path("results").mkdir(exist_ok=True)
    np.savez_compressed("results/five-ion-"+name+".npz",pulses=np.asarray(pulses),selected=np.array(selected))
    Path("results/five-ion-"+name+".json").write_text(json.dumps(dict(conditions=config,geometry=geo,runs=runs,selected=selected),indent=2,allow_nan=False)+"\n")


if __name__=="__main__":main()
