"""Quadcycle memory with declared SD6 timing and W=3, S=1 window MLE.

Nested interleaving is independently implemented from Tan et al. Sec. 4.2.
The chosen schedule, ideal boundaries and decoder tie convention are explicit;
none is claimed to be the unprovided author-selected circuit. No source curves
are input. Incomplete MLE solves remain unknown shots, never discarded passes.
"""
import argparse
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import stim
from generate_algebra import construct, logical_basis
from simulate_sd6_factory_v2 import Decoder, binomial_interval, dem_arrays


def macroschedule(model, seed):
    rng=np.random.default_rng(seed)
    factors=[]
    for i,terms in enumerate(model['polynomials']):
        blocks=[]
        for term in terms:
            polys=[[],[],[],[]];polys[i]=[term]
            hx,hz,*_=construct(dict(group=model['group'],polynomials=polys))
            blocks.append((np.argwhere(hx).tolist(),np.argwhere(hz).tolist(),term))
        factors.append([blocks[j] for j in rng.permutation(len(blocks))])
    order=rng.permutation(4).tolist();center=order[-1];layers=[]
    def add(i,x,z):
        layers.append(dict(factor=i,x_edges=x[0],z_edges=z[1],x_term=x[2],z_term=z[2]))
    for i in order[:-1]:
        fs=factors[i];half=len(fs)//2
        for j in range(half):add(i,fs[half+j],fs[j])
    for term in factors[center]:add(center,term,term)
    for i in reversed(order[:-1]):
        fs=factors[i];half=len(fs)//2
        for j in range(half):add(i,fs[j],fs[half+j])
    hx,hz,*_=construct(model)
    for field,h in [('x_edges',hx),('z_edges',hz)]:
        observed=np.zeros_like(h,dtype=int)
        for lay in layers:
            for a,d in lay[field]:observed[a,d]+=1
        assert np.array_equal(observed,h), 'Every specified check edge exactly once'
    for lay in layers:
        targets=[('d',d) for a,d in lay['x_edges']+lay['z_edges']]
        targets += [('x',a) for a,d in lay['x_edges']]+[('z',a) for a,d in lay['z_edges']]
        assert len(targets)==len(set(targets)), 'Qubit collision in parallel layer'
    assert len(layers)==int(np.max(hx.sum(0)+hz.sum(0)))
    return layers,order


def pauli_string(row,basis):
    return stim.PauliString(''.join(basis if b else 'I' for b in row))


def memory_circuit(model,p,rounds,basis,noise,seed,syndrome_information='matching_basis'):
    hx,hz,*_=construct(model);n=hx.shape[1]
    logs=logical_basis(hz,hx) if basis=='X' else logical_basis(hx,hz)
    stabs=[pauli_string(v,'X') for v in hx]+[pauli_string(v,'Z') for v in hz]
    stabs += [pauli_string(v,basis) for v in logs]
    c=stim.Tableau.from_stabilizers(stabs,allow_redundant=True).to_circuit('elimination')
    ax=list(range(n,n+len(hx)));az=list(range(n+len(hx),n+len(hx)+len(hz)))
    allq=set(range(n+len(hx)+len(hz)));anc=ax+az;m=len(anc)
    selected=list(range(m)) if syndrome_information=='both_bases' else (
        list(range(len(hx))) if basis=='X' else list(range(len(hx),m)))
    layers,order=macroschedule(model,seed);full=p if noise=='SD6' else 0.
    def layer(gates):
        used=set()
        for gate,targets in gates:
            used.update(targets)
            c.append(gate,targets,full) if gate=='M' else c.append(gate,targets)
            if gate=='R' and full:c.append('X_ERROR',targets,full)
            elif gate=='H' and full:c.append('DEPOLARIZE1',targets,full)
            elif gate=='CX' and p:c.append('DEPOLARIZE2',targets,p)
        idle=sorted(allq-used)
        if full and idle:c.append('DEPOLARIZE1',idle,full)
        c.append('TICK')
    for r in range(rounds):
        layer([('R',anc)]);layer([('H',ax)])
        for lay in layers:
            edges=[v for a,d in lay['x_edges'] for v in (ax[a],d)]
            edges += [v for a,d in lay['z_edges'] for v in (d,az[a])]
            layer([('CX',edges)])
        layer([('H',ax)]);layer([('M',anc)])
        for j in selected:
            rec=[stim.target_rec(j-m)]
            if r:rec.append(stim.target_rec(j-2*m))
            c.append('DETECTOR',rec,[j,r])
    def mpp(v,b):
        targets=[]
        for j in np.flatnonzero(v):
            if targets:targets.append(stim.target_combiner())
            targets.append(stim.target_x(int(j)) if b=='X' else stim.target_z(int(j)))
        c.append('MPP',targets)
    for j,(b,v) in enumerate([('X',v) for v in hx]+[('Z',v) for v in hz]):
        mpp(v,b)
        if j in selected:c.append('DETECTOR',[stim.target_rec(-1),stim.target_rec(-m-1)],[j,rounds])
    for j,v in enumerate(logs):
        mpp(v,basis);c.append('OBSERVABLE_INCLUDE',[stim.target_rec(-1)],j)
    dem=c.detector_error_model(decompose_errors=False)
    return c,dem,dict(n=n,k=len(logs),checks_per_round=len(selected),rounds=rounds,basis=basis,noise=noise,
        syndrome_information=syndrome_information,
        schedule_seed=seed,factor_order=order,cnot_layers=len(layers),layers=layers,
        boundary='ideal encoded initial state and ideal terminal stabilizer/logical products',
        timing='all data and syndrome ancillas live through R,H,CX layers,H,M; unacted qubits idle every layer')


class BPLSD:
    """Fast candidate decoder; successful syndrome replay is not MLE proof."""
    def __init__(self,dem,time_limit=None):
        from ldpc import BpLsdDecoder
        from scipy.sparse import csr_matrix
        self.h,self.obs,self.prob=dem_arrays(dem)
        self.decoder=BpLsdDecoder(csr_matrix(self.h),error_channel=self.prob.tolist(),
            max_iter=100,bp_method='minimum_sum',ms_scaling_factor=.625,
            schedule='serial',random_schedule_seed=0,lsd_method='LSD_CS',lsd_order=2)
        self.cache={bytes(len(self.h)):np.zeros(len(self.obs),np.uint8)}
        self.calls=0;self.seconds=0.;self.failures=0;self.certified_low_weight=0
    def predict(self,syndrome):
        key=bytes(syndrome)
        if key in self.cache:return self.cache[key]
        started=time.monotonic();e=np.asarray(self.decoder.decode(syndrome),dtype=np.uint8)
        self.seconds+=time.monotonic()-started;self.calls+=1
        if np.any((self.h@e%2)^syndrome):
            self.failures+=1;raise RuntimeError('BP+LSD returned an unsatisfied syndrome')
        result=self.obs@e%2;self.cache[key]=result;return result


class SlidingMLE:
    def __init__(self,dem,per_round,window,timeout,algorithm='MLE'):
        self.algorithm=algorithm
        self.h,self.l,prob=dem_arrays(dem);self.nd,self.nv=self.h.shape
        self.k=len(self.l);self.rows_per_round=per_round;blocks=self.nd//per_round
        first=np.full(self.nv,blocks)
        for j in range(self.nv):
            ds=np.flatnonzero(self.h[:,j])
            if len(ds):first[j]=ds[0]//per_round
        self.decoders=[]
        for start in range(blocks-window+1):
            end=start+window;last=end==blocks
            columns=np.flatnonzero((first>=start)&(first<end))
            local=stim.DetectorErrorModel()
            for j in columns:
                detector=np.flatnonzero(self.h[start*per_round:end*per_round,j])
                targets=[stim.target_relative_detector_id(int(i)) for i in detector]
                if last or first[j]==start:
                    label=np.r_[self.h[:,j],self.l[:,j]]
                    targets += [stim.target_logical_observable_id(int(i)) for i in np.flatnonzero(label)]
                local.append('error',float(prob[j]),targets)
            local.append('detector',[],[stim.target_relative_detector_id(window*per_round-1)])
            local.append('logical_observable',[],[stim.target_logical_observable_id(self.nd+self.k-1)])
            self.decoders.append((start,end,(Decoder if algorithm=='MLE' else BPLSD)(local,timeout)))
        self.unknown_patterns=set()
    def predict(self,syndrome):
        key=bytes(syndrome)
        if key in self.unknown_patterns:return None
        res=syndrome.copy();prediction=np.zeros(self.k,np.uint8)
        try:
            for start,end,decoder in self.decoders:
                correction=decoder.predict(res[start*self.rows_per_round:end*self.rows_per_round])
                res ^= correction[:self.nd];prediction ^= correction[self.nd:]
                assert not np.any(res[:(start+1)*self.rows_per_round])
            assert not np.any(res),'Window commits must explain the entire syndrome'
            return prediction
        except RuntimeError:
            self.unknown_patterns.add(key);return None
    def stats(self):
        return dict(algorithm=self.algorithm,solver_calls=sum(d.calls for _,_,d in self.decoders),
            milp_seconds=sum(d.seconds for _,_,d in self.decoders),
            certified_low_weight=sum(d.certified_low_weight for _,_,d in self.decoders),
            incomplete_solves=sum(d.failures for _,_,d in self.decoders),
            unique_cache_entries=sum(len(d.cache) for _,_,d in self.decoders))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text());out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    models={m['quad'][0]:m for m in json.loads(Path('config/models.json').read_text())['pairs']}
    rows=[];all_start=time.monotonic()
    for ji,job in enumerate(cfg['jobs']):
        started=time.monotonic();model=models[job['n']]
        c,dem,meta=memory_circuit(model,job['p'],job['rounds'],job['basis'],job['noise'],job['schedule_seed'],job.get('syndrome_information','matching_basis'))
        tag=f"job{ji:02d}_n{job['n']}_{job['basis']}_{job['noise']}_p{job['p']:g}_R{job['rounds']}"
        (out/(tag+'.stim')).write_text(str(c));(out/(tag+'-schedule.json')).write_text(json.dumps(meta,indent=2)+'\n')
        ideal=c.without_noise().compile_detector_sampler(seed=job['seed'])
        ds,os=ideal.sample(32,separate_observables=True)
        assert not np.any(ds) and not np.any(os)
        det,obs=c.compile_detector_sampler(seed=job['seed']).sample(job['shots'],separate_observables=True)
        algorithm=job.get('decoder','MLE')
        decoder=SlidingMLE(dem,meta['checks_per_round'],3,cfg.get('decoder_timeout',30),algorithm)
        failures=0;unknown=0;errors=[];unknown_indices=[]
        for i,(d,o) in enumerate(zip(det,obs)):
            pred=decoder.predict(d.astype(np.uint8))
            if pred is None:unknown+=1;unknown_indices.append(i);continue
            e=o.astype(np.uint8)^pred;errors.append(e);failures+=int(np.any(e))
            if (i+1)%100==0:print(json.dumps(dict(job=ji,processed=i+1,failures=failures,unknown=unknown,seconds=time.monotonic()-started)),flush=True)
        errors=np.asarray(errors,dtype=np.uint8).reshape(-1,meta['k']);N=job['shots'];K=meta['k'];R=job['rounds']
        lower=binomial_interval(failures,N)[0];upper=binomial_interval(failures+unknown,N)[1]
        bits=int(errors.sum());mean=bits/(N*K)
        row=dict(**{k:v for k,v in job.items() if k!='decoder'},observables=K,detectors=dem.num_detectors,dem_errors=dem.num_errors,
            conclusive_shots=N-unknown,unknown_shots=unknown,block_failures=failures,
            block_failure_bounds=[failures/N,(failures+unknown)/N],block_ci95_allowing_unknown=[lower,upper],
            logical_failures_by_bit=errors.sum(0).astype(int).tolist(),
            mean_bit_failure_bounds=[mean,(bits+unknown*K)/(N*K)],
            per_round_linear_bounds=[mean/R,(bits+unknown*K)/(N*K*R)],
            binomial_per_round_upper=upper/R,
            rate_definition='mean over k logical parity failures / measured rounds; finite ideal boundaries; correlations kept per shot',
            complete_mle=(unknown==0 and algorithm=='MLE'),decoder=decoder.stats(),elapsed_seconds=time.monotonic()-started)
        if not unknown:
            shot_means=errors.mean(1)
            row['per_round_mean_se']=float(np.std(shot_means,ddof=1)/math.sqrt(N)/R) if N>1 else None
            row['stationary_parity_inverted_rate']=(1-max(0.,1-2*mean)**(1/R))/2
        np.savez_compressed(out/(tag+'-samples.npz'),detectors=det,observables=obs,logical_errors=errors,
                            unknown_indices=np.array(unknown_indices,dtype=int))
        rows.append(row);print(json.dumps(row),flush=True)
        (out/'results.json').write_text(json.dumps(dict(config=cfg,rows=rows,elapsed_seconds=time.monotonic()-all_start,
            interpretation='Independent declared macroschedules and W3 S1 most-likely DEM error windows. Missing author winner and boundary convention remain comparison limitations; unknown decoder shots are retained.'),indent=2)+'\n')
    assert len(rows)==len(cfg['jobs'])

if __name__=='__main__':main()
