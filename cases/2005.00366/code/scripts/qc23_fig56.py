"""Four independently addressed controls, full chain lengths and 10 × 5 starts."""
import itertools
import json
from pathlib import Path
import sys
import time

from qc23_matrices import geometry, matrices, physical_error

import numpy as np
from scipy.linalg import eigh, null_space, orth
from scipy.optimize import minimize


def prepare(cfg, frequency, eta, count, robust, targets, pairs):
    f=cfg["figure56"]
    duration=f["duration_us"]*1e-6
    cap=2*np.pi*duration*f["maximum_rabi_hz"]
    d,c,Q,theta=matrices(frequency,eta,f["laser_hz"],duration,count,pairs)
    half=count//2 if robust else count
    eye=np.eye(count,half)
    basis=np.column_stack((eye+eye[::-1],1j*(eye-eye[::-1])))/np.sqrt(2) if robust else np.column_stack((eye,1j*eye))
    operator=np.vstack((d,c)) if robust else d
    constraint=np.einsum("ps,sk->pk",operator,basis)
    real=np.vstack((constraint.real,constraint.imag))
    space=null_space(real,rcond=cfg["optimizer"]["svd_rcond"])
    basis=np.einsum("sk,kl->sl",basis,space)
    Qn=cap**2*np.einsum("si,psj->pij",basis.conj(),np.einsum("pst,tj->psj",Q,basis)).real
    # Keep the leading signed directions of both active pairs; the full
    # matrices for all six pairs are subsequently optimized jointly.
    spans=[]
    for form in Qn[targets!=0]:
        val,vec=eigh(form)
        spans.append(vec[:,np.argsort(abs(val))[-min(20,len(val)):]])
    compact=orth(np.column_stack(spans))
    basis=np.einsum("si,ij->sj",basis,compact)
    projected=np.einsum("ai,pab,bj->pij",compact,Qn,compact)
    direction=np.zeros((len(eta),basis.shape[1]))
    for idx in np.flatnonzero(targets):
        j,k=pairs[idx]
        val,vec=eigh(projected[idx])
        best=int(abs(val).argmax())
        factor=np.sqrt(targets[idx]/abs(val[best]))
        direction[j]=factor*vec[:,best]
        direction[k]=np.sign(val[best])*direction[j]
    s=np.linalg.svd(real,compute_uv=False)
    rank=int(np.sum(s>cfg["optimizer"]["svd_rcond"]*s[0]))
    return basis,projected,d,c,Q,theta,cap,direction,dict(
        closure_rank=rank,closure_dimension=int(space.shape[1]),optimizer_dimension=basis.shape[1],
        smallest_kept_singular=float(s[rank-1]),largest_discarded_singular=float(s[rank]) if rank<len(s) else 0)


def trial(cfg,p,eta,pairs,targets,seed):
    basis,projected,d,c,Q,theta,cap,direction,_=p
    n,rank=direction.shape
    count=len(basis)
    j,k=pairs.T
    rng=np.random.default_rng(seed)
    start=direction+rng.normal(0,0.07,size=direction.shape)

    def objective(x):
        v=x.reshape(n,rank)
        right=np.einsum("pab,pb->pa",projected,v[k])
        left=np.einsum("pab,pb->pa",projected,v[j])
        errors=np.sum(v[j]*right,axis=1)-targets
        gradient=np.zeros_like(v)
        np.add.at(gradient,j,2*errors[:,None]*right)
        np.add.at(gradient,k,2*errors[:,None]*left)
        wave=np.einsum("ik,sk->is",v,basis)
        amplitude=abs(wave)
        overflow=np.maximum(amplitude-0.985,0)
        grad=2/count*overflow*wave/np.maximum(amplitude,1e-30)
        gradient+=np.einsum("is,sk->ik",grad,basis.conj()).real
        return float(errors@errors+np.sum(overflow**2)/count),gradient.ravel()

    tic=time.perf_counter()
    cpu=time.process_time()
    ans=minimize(objective,start.ravel(),jac=True,method="L-BFGS-B",
        options={"maxiter":cfg["optimizer"]["fig56_max_iterations"],"maxls":40,"ftol":1e-14,"gtol":1e-11})
    cpu=time.process_time()-cpu
    elapsed=time.perf_counter()-tic
    v=ans.x.reshape(n,rank)
    waveform=np.einsum("ik,sk->is",v,basis)
    maximum=float(abs(waveform).max())
    pulse=cap*waveform/max(1,maximum)
    phase=np.einsum("ps,pst,pt->p",pulse[j].conj(),Q,pulse[k]).real
    motion=np.einsum("ps,js->jp",d,pulse)*eta
    moment=np.einsum("ps,js->jp",d-c,pulse)*eta
    fidelity=physical_error(phase-targets,motion,pairs,cfg["occupation"])
    row=dict(seed=seed,optimization_seconds=elapsed,cpu_seconds=cpu,iterations=int(ans.nit),
        optimizer_status=int(ans.status),physical_infidelity=fidelity,maximum_phase_error=float(abs(phase-targets).max()),
        maximum_non_target_phase=float(abs(phase[targets==0]).max()),
        displacement_norm=float(np.linalg.norm(motion)),first_moment_norm=float(np.linalg.norm(moment)),
        peak_rabi_hz=float(abs(pulse).max()/cap*cfg["figure56"]["maximum_rabi_hz"]))
    return row,pulse


def main():
    cfg=json.loads(Path("config/fig456.json").read_text())
    f=cfg["figure56"]
    n=int(sys.argv[1])
    axial=int(sys.argv[2])
    specs=f["families"] if axial==f["trap_hz"][2] else f["adjusted_families"]
    repeats=cfg["repetitions"]
    trap=[*f["trap_hz"][:2],axial]
    freq,eta,coordinates,force=geometry(cfg,n,f["addressed"],trap)
    pairs=np.array(list(itertools.combinations(range(len(f["addressed"])),2)))
    targets=np.array([np.pi/4 if list(x) in f["pairs"] else 0 for x in pairs])
    rows,pulses=[],[]
    for family in specs:
        robust=family.startswith("robust")
        count=int(family.rsplit("-",1)[-1])
        start=time.perf_counter()
        process=time.process_time()
        p=prepare(cfg,freq,eta,count,robust,targets,pairs)
        prep=time.perf_counter()-start
        prep_cpu=time.process_time()-process
        groups=[]
        for g in range(repeats["groups"]):
            seed=repeats["seed_base"]+2000000+n*10000+f["families"].index(family)*1000+g*repeats["per_group"]
            attempts=[trial(cfg,p,eta,pairs,targets,seed+k) for k in range(repeats["per_group"])]
            chosen=min(range(len(attempts)),key=lambda k:attempts[k][0]["physical_infidelity"])
            picked,wave=attempts[chosen]
            padded=np.zeros((len(eta),128),complex)
            padded[:,:count]=wave
            pulses.append(padded)
            groups.append(dict(best_index=chosen,trials=[a[0] for a in attempts],
                group_cpu_seconds=prep_cpu+sum(a[0]["cpu_seconds"] for a in attempts),
                group_wall_seconds=prep+sum(a[0]["optimization_seconds"] for a in attempts)))
        losses=np.array([g["trials"][g["best_index"]]["physical_infidelity"] for g in groups])
        seconds=np.array([g["group_cpu_seconds"] for g in groups])
        rows.append(dict(family=family,segments=count,robust=robust,groups=groups,
            mean_infidelity=float(losses.mean()),sd_infidelity=float(losses.std(ddof=1)),
            mean_group_cpu_seconds=float(seconds.mean()),sd_group_cpu_seconds=float(seconds.std(ddof=1)),
            preparation_seconds=prep,preparation_cpu_seconds=prep_cpu,geometry_diagnostics=p[-1]))
        print(n,axial,family,rows[-1]["mean_infidelity"],rows[-1]["mean_group_cpu_seconds"],flush=True)
    name=f"results/f56-{n:02d}-{axial}"
    output=dict(ions=n,axial_hz=axial,frequencies_hz=freq.tolist(),coordinates=coordinates.tolist(),
        force_residual=force,series=rows)
    Path(name+".json").write_text(json.dumps(output,allow_nan=False,separators=(",",":"))+"\n")
    np.savez_compressed(name+".npz",pulses=np.asarray(pulses))


if __name__=="__main__":
    main()
