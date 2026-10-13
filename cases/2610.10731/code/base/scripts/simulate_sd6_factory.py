"""Independent SD6 phase-probe factory circuit and exact DEM-error decoder.

This is a declared Clifford probe of the published single-pair marginal model.
It does not simulate the three-copy ideal CCZ or establish full magic-state
fidelity. All schedule, readout and detector choices are exported explicitly.
"""
from pathlib import Path
import argparse
import itertools
import json
import math
import time
import numpy as np
import stim
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_matrix, hstack, diags
from generate_algebra import construct, logical_basis, nullspace

def solve_gf2(a, b):
    """One solution of a x=b over GF(2), with all free variables zero."""
    a=np.asarray(a,dtype=np.uint8).copy(); b=np.asarray(b,dtype=np.uint8).copy()
    m,n=a.shape; piv=[]; r=0
    for c in range(n):
        hits=np.flatnonzero(a[r:,c])
        if not len(hits): continue
        k=r+hits[0]; a[[r,k]]=a[[k,r]]; b[[r,k]]=b[[k,r]]
        for k in np.flatnonzero(a[:,c]):
            if k!=r: a[k]^=a[r]; b[k]^=b[r]
        piv.append(c); r+=1
        if r==m: break
    if np.any(b[r:]): raise ValueError("inconsistent binary system")
    x=np.zeros(n,np.uint8); x[piv]=b[:r]
    return x

def edge_color(h, seed):
    """Delta matchings by completing a bipartite multigraph to regularity."""
    from scipy.optimize import linear_sum_assignment
    m,n=h.shape; size=max(m,n); degree=int(max(h.sum(0).max(),h.sum(1).max()))
    graph=np.zeros((size,size),int); graph[:m,:n]=h
    real=np.zeros_like(graph); real[:m,:n]=h
    left=degree-graph.sum(1); right=degree-graph.sum(0)
    for i in range(size):
        for j in range(size):
            take=min(left[i],right[j]); graph[i,j]+=take
            left[i]-=take; right[j]-=take
    rng=np.random.default_rng(seed); layers=[]
    for _ in range(degree):
        cost=rng.random((size,size)); cost[graph==0]=1e6
        rr,cc=linear_sum_assignment(cost)
        assert np.all(graph[rr,cc]>0)
        layer=[]
        for i,j in zip(rr,cc):
            graph[i,j]-=1
            if real[i,j]:
                real[i,j]-=1; layer.append((int(i),int(j)))
        layers.append(layer)
    assert not np.any(real)
    return layers

def factory(model,p,pccz,seed=1,terminal_readout_noise=False,probe='phase'):
    hx,hz,mx,mz,tx,tz=construct(model); n=tx.shape[1]; nq=2*n
    T=list(range(n)); F=list(range(n,2*n)); Q=list(range(2*n,4*n))
    A=list(range(4*n,4*n+len(hx))); total=4*n+len(hx)
    circuit=stim.Circuit(); live=set(); layers=[]; meas=0
    def layer(name, operations, active_new=(), remove=()):
        nonlocal meas
        live.update(active_new); acted=set()
        for gate,targets,prob in operations:
            circuit.append(gate,targets,prob) if prob is not None else circuit.append(gate,targets)
            acted.update(targets)
            if gate in ('M','MX'): meas+=len(targets)
            if gate=='R' and p: circuit.append('X_ERROR',targets,p)
            elif gate in ('H','I') and p: circuit.append('DEPOLARIZE1',targets,p)
            elif gate=='CX' and p: circuit.append('DEPOLARIZE2',targets,p)
        idle=sorted(live-acted)
        if idle and p: circuit.append('DEPOLARIZE1',idle,p)
        layers.append(dict(name=name,operations=[dict(gate=g,targets=t,probability=v) for g,t,v in operations],idles=idle))
        circuit.append('TICK'); live.difference_update(remove)
    layer('initialize',[('R',T+F+Q+A,None)],T+F+Q+A)
    layer('prepare_plus',[('H',T+A,None)])
    logical=logical_basis(tz,tx)
    embedded=np.c_[np.zeros_like(logical),logical]
    zlogical=np.array([solve_gf2(np.vstack([hx,embedded]),np.r_[np.zeros(len(hx),np.uint8),np.eye(len(logical),dtype=np.uint8)[i]]) for i in range(len(logical))])
    refs=list(range(total,total+len(logical)))
    if probe=='bell':
        if terminal_readout_noise: raise ValueError('Bell diagnostics use noiseless virtual terminal products.')
        # Virtual reference encoding defines a Pauli-channel diagnostic only.
        circuit.append('R',refs)
        for ref,z in zip(refs,zlogical[:,n:]):
            circuit.append('CX',[v for j in np.flatnonzero(z) for v in (T[j],ref)])
    tri=edge_color(tz,seed); quad=edge_color(hx,seed+100000)
    st=0; sq=0
    for k in range(max(len(tri),len(quad))):
        operations=[]
        if k<len(tri): operations.append(('CX',[v for a,d in tri[k] for v in (T[d],F[a])],None))
        if k<len(quad): operations.append(('CX',[v for a,d in quad[k] for v in (A[a],Q[d])],None))
        # Early tricycle measurement/reset uses otherwise idle layers, preserving reuse.
        if k==len(tri):
            st=meas; operations.append(('M',F,p))
        if k==len(tri)+1: operations.append(('R',F,None))
        layer(f'syndrome_{k}',operations)
    if len(quad)<=len(tri):
        st=meas; layer('tricycle_syndrome_readout',[('M',F,p)])
        layer('fanout_reset',[('R',F,None)])
    elif len(quad)==len(tri)+1: layer('fanout_reset',[('R',F,None)])
    layer('fanout_and_quad_H',[('CX',[v for t,f in zip(T,F) for v in (t,f)],None),('H',A,None)])
    sq=meas
    # A single CCZ error marginal replaces the non-Clifford layer of the probe.
    ops=[('M',A,p),('DEPOLARIZE1',T+F,16*pccz/21)]
    layer('ccz_marginal_and_quad_readout',ops,remove=A)
    layer('escape',[('CX',[v for t,q in zip(T,Q[n:]) for v in (t,q)],None)])
    layer('tricycle_H',[('H',T+F,None)])
    sout=meas; layer('tricycle_readout',[('M',T+F,p)],remove=T+F)
    def detector(indices):
        circuit.append('DETECTOR',[stim.target_rec(int(i)-meas) for i in sorted(set(indices))])
    # All accessible preparation redundancies, without postselection on final Q readout.
    for v in nullspace(tz.T): detector([st+i for i in np.flatnonzero(v)])
    for v in nullspace(hx.T): detector([sq+i for i in np.flatnonzero(v)])
    post_start=circuit.num_detectors
    for row,v in enumerate(tx):
        embed=np.r_[np.zeros(n,np.uint8),v]
        coefficients=np.zeros(len(hx),np.uint8)
        coefficients[3*len(tx)+row]=1
        assert np.array_equal(hx.T@coefficients%2,embed)
        detector([sout+i for i in np.flatnonzero(v)]+[sout+n+i for i in np.flatnonzero(v)]+[sq+i for i in np.flatnonzero(coefficients)])
    npost=circuit.num_detectors
    qout=meas
    if probe=='bell':
        def product(pauli,indices):
            targets=[]
            for i in indices:
                if targets:targets.append(stim.target_combiner())
                targets.append(stim.target_x(int(i)) if pauli=='X' else stim.target_z(int(i)))
            return targets
        for i,v in enumerate(hx):
            circuit.append('MPP',product('X',[Q[j] for j in np.flatnonzero(v)]));meas+=1
            detector([sq+i,meas-1])
        for v in hz:
            circuit.append('MPP',product('Z',[Q[j] for j in np.flatnonzero(v)]));meas+=1
            coefficients=solve_gf2(tz.T,v[n:])
            detector([st+j for j in np.flatnonzero(coefficients)]+[meas-1])
        for i,v in enumerate(logical):
            circuit.append('MPP',product('X',[refs[i]]+[Q[n+j] for j in np.flatnonzero(v)]));meas+=1
            ids=[sout+j for j in np.flatnonzero(v)]+[sout+n+j for j in np.flatnonzero(v)]+[meas-1]
            circuit.append('OBSERVABLE_INCLUDE',[stim.target_rec(int(j)-meas) for j in ids],i)
        for i,v in enumerate(zlogical):
            circuit.append('MPP',product('Z',[refs[i]]+[Q[j] for j in np.flatnonzero(v)]));meas+=1
            circuit.append('OBSERVABLE_INCLUDE',[stim.target_rec(-1)],i+len(logical))
    elif terminal_readout_noise:
        layer('terminal_quad_H',[('H',Q,None)])
        layer('terminal_quad_readout',[('M',Q,p)],remove=Q)
    else:
        circuit.append('MX',Q); meas+=len(Q)
    if probe!='bell':
        for i,v in enumerate(hx): detector([sq+i]+[qout+j for j in np.flatnonzero(v)])
        for i,v in enumerate(logical):
            ids=[sout+j for j in np.flatnonzero(v)]+[sout+n+j for j in np.flatnonzero(v)]+[qout+n+j for j in np.flatnonzero(v)]
            circuit.append('OBSERVABLE_INCLUDE',[stim.target_rec(int(j)-meas) for j in ids],i)
    # Validates that every declared detector and observable is deterministic ideally.
    dem=circuit.detector_error_model(decompose_errors=False)
    return circuit,dem,dict(n3=n,n4=nq,npost=npost,post_start=post_start,nlogical=len(logical),total_qubits=total,
                           schedule_seed=seed,tri_layers=tri,quad_layers=quad,layers=layers,
                           terminal_readout_noise=terminal_readout_noise,probe=probe)

def dem_arrays(dem):
    cols=[]; logical=[]; probs=[]
    for inst in dem.flattened():
        if inst.type!='error': continue
        d=[];o=[]
        for t in inst.targets_copy():
            if t.is_relative_detector_id(): d.append(t.val)
            elif t.is_logical_observable_id(): o.append(t.val)
            else: raise ValueError('Unexpected decomposed DEM target')
        if not d and not o: continue
        cols.append(d);logical.append(o);probs.append(inst.args_copy()[0])
    a=np.zeros((dem.num_detectors,len(cols)),np.uint8)
    b=np.zeros((dem.num_observables,len(cols)),np.uint8)
    for j,ds in enumerate(cols):a[ds,j]=1
    for j,os in enumerate(logical):b[os,j]=1
    return a,b,np.array(probs)

class Decoder:
    def __init__(self,dem,time_limit=30):
        self.h,self.obs,self.prob=dem_arrays(dem); m,n=self.h.shape
        self.matrix=hstack([csc_matrix(self.h,dtype=float),-2*diags(np.ones(m))],format='csc')
        self.cost=np.r_[np.log((1-self.prob)/self.prob),np.zeros(m)]
        self.bounds=Bounds(np.zeros(n+m),np.r_[np.ones(n),np.ceil(self.h.sum(1)/2)])
        self.integrality=np.ones(n+m);self.limit=time_limit
        self.cache={bytes(m):np.zeros(len(self.obs),np.uint8)}
        self.calls=0;self.seconds=0.;self.failures=0
        self.certified_low_weight=0
        self.weights=self.cost[:n]
        self.keys=[int.from_bytes(np.packbits(self.h[:,i],bitorder='little').tobytes(),'little') for i in range(n)]
        self.one={}
        for i,k in enumerate(self.keys):self.one.setdefault(k,[]).append(i)
        for v in self.one.values():v.sort(key=lambda i:self.weights[i])
        self.min_three=float(np.sort(self.weights)[:3].sum())
    def predict(self,syndrome):
        key=bytes(syndrome.astype(np.uint8))
        if key in self.cache:return self.cache[key]
        integer=int.from_bytes(np.packbits(syndrome,bitorder='little').tobytes(),'little')
        best=float('inf');selected=[]
        if integer in self.one:
            i=self.one[integer][0];best=float(self.weights[i]);selected=[i]
        for i,k in enumerate(self.keys):
            for j in self.one.get(integer^k,[])[:2]:
                if i==j:continue
                cost=float(self.weights[i]+self.weights[j])
                if cost<best:best=cost;selected=[i,j]
                break
        # Exhaustive weight <=2 and a strict cost lower bound for all >=3 sets.
        if best<self.min_three-1e-10:
            prediction=np.bitwise_xor.reduce(self.obs[:,selected],axis=1)
            self.cache[key]=prediction;self.certified_low_weight+=1
            return prediction
        start=time.monotonic()
        result=milp(self.cost,integrality=self.integrality,bounds=self.bounds,
                    constraints=LinearConstraint(self.matrix,syndrome,syndrome),
                    options={'time_limit':self.limit,'mip_rel_gap':0.0,'threads':1})
        self.seconds+=time.monotonic()-start;self.calls+=1
        if self.calls%100==0:print('certified MILP calls',self.calls,'seconds',round(self.seconds,2),flush=True)
        if result.status!=0:
            self.failures+=1;raise RuntimeError(f'MLE not proved optimal: {result.message}')
        e=np.rint(result.x[:len(self.prob)]).astype(np.uint8)
        assert np.array_equal(self.h@e%2,syndrome)
        prediction=self.obs@e%2;self.cache[key]=prediction
        return prediction

def binomial_interval(k,n):
    from scipy.stats import beta
    return [0.0 if k==0 else float(beta.ppf(.025,k,n-k+1)),
            1.0 if k==n else float(beta.ppf(.975,k+1,n-k))]

def simulate(cfg):
    models=json.loads(Path('config/models.json').read_text())['pairs']
    out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True)
    rows=[];started=time.monotonic()
    for job in cfg['jobs']:
        model=next(m for m in models if m['quad'][0]==job['n4'])
        probe=job.get('probe','bell')
        circuit,dem,meta=factory(model,job['p'],job['pccz'],job['schedule_seed'],job.get('terminal_readout_noise',False),probe)
        tag=f"n{job['n4']}_p{job['p']:.8g}_c{job['pccz']:.8g}_s{job['schedule_seed']}_r{int(job.get('terminal_readout_noise',False))}"
        (out/(tag+'.stim')).write_text(str(circuit));(out/(tag+'.dem')).write_text(str(dem))
        (out/(tag+'-schedule.json')).write_text(json.dumps(meta,indent=2)+'\n')
        sampler=circuit.compile_detector_sampler(seed=job['seed']);decoder=Decoder(dem,cfg.get('decoder_timeout',30))
        accepted=0; failures=0;failed_bits=np.zeros(dem.num_observables,np.int64);failed_qubits=np.zeros(3,np.int64);n=0;t0=time.monotonic()
        while n<job['shots']:
            count=min(cfg.get('batch',10000),job['shots']-n)
            det,obs=sampler.sample(count,separate_observables=True)
            start=0 if job.get('postselection','teleport_only')=='all_prefix' else meta['post_start']
            mask=~np.any(det[:,start:meta['npost']],axis=1);ds=det[mask].astype(np.uint8);os=obs[mask].astype(np.uint8)
            accepted+=len(ds)
            if job.get('decode',True):
                patterns,inverse=np.unique(ds,axis=0,return_inverse=True)
                predictions=np.array([decoder.predict(x) for x in patterns],np.uint8)
                errors=os^predictions[inverse];failures+=int(np.any(errors,axis=1).sum());failed_bits+=errors.sum(0).astype(np.int64)
                per_qubit=(errors[:,:3]|errors[:,3:]) if probe=='bell' else errors
                failed_qubits+=per_qubit.sum(0).astype(np.int64)
            n+=count
        row={**job,'accepted':accepted,'acceptance':accepted/n,'acceptance_ci95':binomial_interval(accepted,n),
             'logical_failure_shots':failures if job.get('decode',True) else None,
             'logical_bit_failures':failed_bits.tolist() if job.get('decode',True) else None,
             'block_ler':failures/accepted if job.get('decode',True) and accepted else None,
             'block_ler_ci95':binomial_interval(failures,accepted) if job.get('decode',True) and accepted else None,
             'logical_per_qubit':float(failed_qubits.sum()/(3*accepted)) if job.get('decode',True) and accepted else None,
             'failed_qubits':failed_qubits.tolist(),'phase_only':probe=='phase','probe':probe,'npost':meta['npost'],'detectors':dem.num_detectors,'dem_mechanisms':len(decoder.prob),
             'decoder_calls':decoder.calls,'decoder_seconds':decoder.seconds,'decoder_failures':decoder.failures,
             'wall_seconds':time.monotonic()-t0,'tag':tag}
        rows.append(row);print(json.dumps(row),flush=True)
        (out/'results.json').write_text(json.dumps({'format':'qldpc.sd6-phase-probe.v1','rows':rows,
          'limits':['Full SD6 channels; ideal CCZ replaced by identity plus the published one-leg depolarizing marginal.',
                    'Declared phase or virtual Bell-reference Pauli-channel diagnostic, not full magic-state infidelity or source-curve acceptance.',
                    'Independent optimal-depth edge color schedule, not author benchmark schedule.',
                    'Exact most-likely independent DEM error (not maximum-likelihood logical coset).',
                    'Final Q measurements are excluded from postselection. Readout noise is an explicit per-job option.'],
          'wall_seconds':time.monotonic()-started},indent=2)+'\n')
    return rows

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    simulate(json.loads(Path(args.config).read_text()))
