"""Enumerate all one/two DEM mechanisms; preserve failure and tie boundaries.

This audits logical safety of accepting repaired records. It does not substitute
a phase-parity diagnostic for full magic-state infidelity.
"""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import json
from pathlib import Path
import time
import numpy as np
from prep_decoder import ROOT, full_factory, prep_circuit, dem_arrays
from generate import posteriors
from generate_algebra import construct, nullspace


def audit(model, schedule, order, p, pc):
    c,dem,meta=full_factory(model,p,pc,schedule,order)
    _,pd,_=prep_circuit(model,p,meta)
    mapper,mle,_,_,_,_=posteriors(pd)
    h,o,prob=dem_arrays(dem); weights=np.log((1-prob)/prob)
    signatures=[sum(int(x)<<i for i,x in enumerate(v)) for v in h.T]
    logicals=[sum(int(x)<<i for i,x in enumerate(v)) for v in o.T]
    min_three=float(np.sort(weights)[:3].sum())
    best={0:(0.,0,[],False)}
    def offer(s,logical,cost,indices):
        old=best.get(s)
        if old is None or cost<old[0]-1e-11: best[s]=(cost,logical,indices,False)
        elif abs(cost-old[0])<=1e-11 and old[1]!=logical:
            best[s]=(old[0],old[1],old[2],True)
    for i,(s,l,w) in enumerate(zip(signatures,logicals,weights)):offer(s,l,float(w),[i])
    one=dict(best)
    distance_witness=None
    for i,s in enumerate(signatures):
        if s==0 and logicals[i]:distance_witness=[i];break
    if distance_witness is None:
        seen={}
        for i,(s,l) in enumerate(zip(signatures,logicals)):
            if s in seen and seen[s][0]!=l:distance_witness=[seen[s][1],i];break
            seen[s]=(l,i)
    triple=None;quadruple=None
    for i in range(len(prob)):
        for j in range(i):
            s=signatures[i]^signatures[j];l=logicals[i]^logicals[j]
            if triple is None and s in one and one[s][1]!=l:
                candidate=list(dict.fromkeys(one[s][2]+[j,i]))
                if len(candidate)==3:triple=candidate
            if quadruple is None and s in best and best[s][1]!=l:
                candidate=list(dict.fromkeys(best[s][2]+[j,i]))
                if len(candidate)==4:quadruple=candidate
            offer(s,l,float(weights[i]+weights[j]),[j,i])
    if distance_witness is not None:distance_lower=distance_upper=len(distance_witness)
    elif triple is not None:distance_lower=distance_upper=3;distance_witness=triple
    elif quadruple is not None:distance_lower=distance_upper=4;distance_witness=quadruple
    else:distance_lower=5;distance_upper=None
    if distance_witness:
        assert not np.bitwise_xor.reduce(h[:,distance_witness],axis=1).any()
        assert np.bitwise_xor.reduce(o[:,distance_witness],axis=1).any()
    nt=len(nullspace(construct(model)[-1].T));m=meta['post_start']-nt;q=meta['npost']-meta['post_start']
    no_fault=float(np.prod(1-prob));odds=prob/(1-prob)
    methods={name:{'one':dict(accepted=0,wrong_certified=0,unresolved=0,wrong_probability_lower_bound=0.),
                   'two':dict(accepted=0,wrong_certified=0,unresolved=0,wrong_probability_lower_bound=0.),
                   'witnesses':[]} for name in ('raw','map','mle')}
    def examine(indices,s,l,mass):
        syndrome=(s>>nt)&((1<<m)-1);post=(s>>meta['post_start'])&((1<<q)-1)
        guess=best[s]
        certified=guess[0]<min_three-1e-10 and not guess[3]
        for name,wanted in [('raw',0),('map',int(mapper[syndrome])),('mle',int(mle[syndrome]))]:
            if post!=wanted:continue
            row=methods[name]['one' if len(indices)==1 else 'two'];row['accepted']+=1
            if not certified:row['unresolved']+=1;continue
            if l!=guess[1]:
                row['wrong_certified']+=1;row['wrong_probability_lower_bound']+=mass
                if len(methods[name]['witnesses'])<6:
                    methods[name]['witnesses'].append(dict(actual=indices,inferred=guess[2],
                        actual_logical=l,inferred_logical=guess[1],syndrome_integer=s,
                        actual_cost=float(sum(weights[i] for i in indices)),best_cost=guess[0],
                        min_three_lower_bound=min_three,configuration_probability=mass))
    for i,s in enumerate(signatures):examine([i],s,logicals[i],no_fault*odds[i])
    for i in range(len(prob)):
        for j in range(i):examine([j,i],signatures[i]^signatures[j],logicals[i]^logicals[j],no_fault*odds[i]*odds[j])
    return dict(n4=model['quad'][0],schedule=schedule,order=order,p=p,pccz=pc,
        mechanisms=len(prob),unique_syndromes_up_to_two=len(best),min_three_cost_lower_bound=min_three,
        full_raw_phase_detector_distance=dict(lower=distance_lower,upper=distance_upper,witness=distance_witness),methods=methods,
        limitations=['Mechanism counts refer to the exact independent DEM representation, not original physical location counts.',
        'Full raw syndrome is used for inference; final quad readout is excluded from every acceptance mask.',
        'Ties or costs not certified against >=3 mechanisms remain unresolved.',
        'Failure probabilities are rigorous-subset lower bounds within float64 DEM MLE, not estimates of total LER.',
        'Three logical X parities are a phase diagnostic; not full magic-state infidelity.'])


def main():
    cfg=json.loads((ROOT/'config/experiment.json').read_text());models=json.loads((ROOT/'config/models.json').read_text())['pairs']
    rows=[];start=time.monotonic();out=ROOT/'fault-audit';out.mkdir(exist_ok=True)
    for n4 in cfg['n4']:
        for order in cfg['orders']:
            model=next(m for m in models if m['quad'][0]==n4)
            row=audit(model,'fresh_aligned',order,*cfg['basepoint']);rows.append(row)
            print(json.dumps(dict(n4=n4,order=order['id'],distance=row['full_raw_phase_detector_distance'],
                failures={k:row['methods'][k]['two']['wrong_certified'] for k in row['methods']},seconds=time.monotonic()-start)),flush=True)
            (out/'results.json').write_text(json.dumps(dict(complete=False,rows=rows),indent=2)+'\n')
    (out/'results.json').write_text(json.dumps(dict(complete=True,rows=rows,elapsed_seconds=time.monotonic()-start),indent=2)+'\n')


if __name__=='__main__':main()
