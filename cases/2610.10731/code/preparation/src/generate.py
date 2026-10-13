"""Frozen full-SD6 preparation-decoder and finite gate-order investigation."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
from pathlib import Path
import itertools
import json
import time
import hashlib
import numpy as np
from prep_decoder import (ROOT, full_factory, prep_circuit, dem_arrays,
    joint_distribution, full_frame_values, residual_from_table, mle_frame_decoder,
    select_preparation_noise, factorization_check, acceptance_joint, sample_acceptance)
from probe import exact_distribution


def posteriors(prep_dem):
    h,f,prob=dem_arrays(prep_dem);m=len(h);q=len(f)
    table,maps,stats=joint_distribution(np.vstack([h,f]),prob,m)
    best=table.argmax(axis=0)
    mapper=full_frame_values(np.arange(1<<m),best,maps[m:],m)
    mle,mle_stats=mle_frame_decoder(prep_dem)
    kmap,marginal=residual_from_table(table,maps,mapper,m,q)
    kmle,_=residual_from_table(table,maps,mle,m,q)
    return mapper,mle,kmap,kmle,marginal,dict(stats,mle=mle_stats,
        map_class_success=float(kmap[0]),mle_class_success=float(kmle[0]),
        map_mle_disagreement_syndromes=int((mapper!=mle).sum()))


def main():
    cfg=json.loads((ROOT/'config/experiment.json').read_text())
    models=json.loads((ROOT/'config/models.json').read_text())['pairs']
    out=ROOT/'outputs';out.mkdir(exist_ok=True)
    rows=[];tri_rows=[];tables={};programs={};started=time.monotonic()
    for n4 in cfg['n4']:
        model=next(m for m in models if m['quad'][0]==n4)
        for schedule in cfg['schedules']:
            for order_index,order in enumerate(cfg['orders']):
                points=cfg['points'] if order_index==0 else [cfg['basepoint']]
                posterior_cache={}
                for p,pc in points:
                    c,dem,meta=full_factory(model,p,pc,schedule,order)
                    tag=f'n{n4}_{schedule}_{order["id"]}_p{p:g}_c{pc:g}'
                    prep,pdem,prepmeta=prep_circuit(model,p,meta)
                    if p not in posterior_cache: posterior_cache[p]=posteriors(pdem)
                    mapper,mle,kmap,kmle,marginal,pstats=posterior_cache[p]
                    rest_c=select_preparation_noise(c,model,meta,False)
                    rest_dem=rest_c.detector_error_model(decompose_errors=False)
                    rest,_=exact_distribution(rest_dem,meta)
                    full,_=exact_distribution(dem,meta)
                    factor=factorization_check(dem,pdem,rest_dem,model,meta)
                    raw=float(rest@marginal)
                    assert abs(raw-full[0])<1e-11
                    assert int(rest.argmax())==0
                    row=dict(tag=tag,n4=n4,p=p,pccz=pc,schedule=schedule,order=order,
                        alpha_raw=raw,alpha_map=float(rest@kmap),alpha_mle=float(rest@kmle),
                        oracle_quad_prep_upper_bound=float(rest[0]),
                        factorization=factor,posterior=pstats,prep=prepmeta,
                        circuit_sha256=hashlib.sha256(str(c).encode()).hexdigest())
                    if [p,pc]==cfg['basepoint']:
                        joint=acceptance_joint(dem,model,meta,mapper)
                        joint.pop('syndrome_marginal')
                        row['full_joint_check']=joint
                        assert abs(joint['acceptance']-row['alpha_map'])<1e-11
                        if order_index==0:
                            row['mc']=sample_acceptance(c,model,meta,mapper,cfg['control_shots'],cfg['seed']+n4+(0 if schedule=='baseline' else 100))
                    if order_index==0 and [p,pc]==cfg['basepoint']:
                        for perm in itertools.permutations(range(4)):
                            torder=dict(order,tri=list(perm))
                            tc,td,tm=full_factory(model,p,pc,schedule,torder)
                            tr=select_preparation_noise(tc,model,tm,False).detector_error_model()
                            trp,_=exact_distribution(tr,tm)
                            factorization_check(td,pdem,tr,model,tm)
                            tri_rows.append(dict(n4=n4,schedule=schedule,tri_order=list(perm),
                                alpha_raw=float(marginal@trp),alpha_map=float(kmap@trp),
                                alpha_mle=float(kmle@trp),oracle_quad_prep_upper_bound=float(trp[0])))
                    tables[tag+'__map']=mapper.astype(np.uint16)
                    tables[tag+'__mle']=mle.astype(np.uint16)
                    tables[tag+'__map_residual']=kmap
                    tables[tag+'__mle_residual']=kmle
                    tables[tag+'__rest_distribution']=rest
                    programs[tag]=dict(meta=meta,full=str(c),prep=str(prep),rest=str(rest_c))
                    rows.append(row)
                    print(json.dumps(dict(tag=tag,alpha_map=row['alpha_map'],alpha_mle=row['alpha_mle'],
                                          oracle=row['oracle_quad_prep_upper_bound'],elapsed=time.monotonic()-started)),flush=True)
                    (out/'results.json').write_text(json.dumps(dict(complete=False,config=cfg,rows=rows,tri_order_rows=tri_rows),indent=2)+'\n')
    result=dict(complete=True,config=cfg,rows=rows,tri_order_rows=tri_rows,
        elapsed_seconds=time.monotonic()-started,
        limitations=['One-pair Clifford phase diagnostic, not full magic-state infidelity.',
        'Prep MLE uses independent DEM mechanisms; MAP maximizes frame class probability.',
        'All comparisons keep unconditional attempt denominator and complete SD6 primitive rates.',
        'Oracle and syndrome-only bounds apply to the explicitly fixed accessible information and remaining gates.',
        'Finite deterministic gate orders; no selection by source agreement or claim of globally maximal circuit distance.',
        'Float64 exact finite distributions mean no sampling error, not interval-certified arithmetic.'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    (out/'programs.json').write_text(json.dumps(programs)+'\n')
    np.savez_compressed(out/'tables.npz',**tables)


if __name__=='__main__':main()
