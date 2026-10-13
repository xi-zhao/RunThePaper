"""Noise/order/observable controls under explicit finite search boundaries."""
from pathlib import Path
import json
import itertools
import time
from simulate_sd6_factory_v2 import factory, edge_color
from structured_schedule import structured_tri
from generate_algebra import construct
from audit_sd6_timing_v3 import timing_circuit, exact_acceptance


def main():
    models=json.loads(Path('config/models.json').read_text())['pairs']
    out=Path('outputs/timing-order-definitions-v3/results.json')
    out.parent.mkdir(parents=True,exist_ok=True)
    result={'quad_layer_orders':[], 'quad_coloring_seeds':[], 'noise_controls':[], 'observable_controls':[]}
    started=time.monotonic()
    for n in (54,72):
        model=next(m for m in models if m['quad'][0]==n)
        hx=construct(model)[0]
        tri=structured_tri(model,(0,2,1,3))
        quad=edge_color(hx,100001)
        orders=list(itertools.permutations(range(len(quad)))) if n==54 else [
            tuple((i+offset)%len(quad) for i in (range(len(quad)) if sign==1 else reversed(range(len(quad)))))
            for sign in (1,-1) for offset in range(len(quad))]
        for order in orders:
            c,d,m=factory(model,.001,.002,tri_override=tri,quad_override=[quad[i] for i in order])
            result['quad_layer_orders'].append(dict(n4=n,order=order,acceptance=exact_acceptance(d,m)))
        for seed in range(100001,100033):
            c,d,m=factory(model,.001,.002,tri_override=tri,quad_override=edge_color(hx,seed))
            result['quad_coloring_seeds'].append(dict(n4=n,seed=seed,acceptance=exact_acceptance(d,m)))
        for omit in (['one_qubit'],['idle','one_qubit']):
            c,d,m=timing_circuit(model,.001,.002,omit=omit)
            result['noise_controls'].append(dict(n4=n,omitted=omit,acceptance=exact_acceptance(d,m),
                interpretation='diagnostic departure from the paper full SD6, not a repair'))
        for probe in ('phase','bell'):
            c,d,m=factory(model,.001,.002,probe=probe,tri_override=tri)
            alpha=exact_acceptance(d,m)
            meta=dict(m,post_start=0)
            # Full-prefix acceptance has >12 checks, so compare the same
            # detector realization with and without preparation postselection.
            det=c.compile_detector_sampler(seed=261012735+n).sample(200000)
            a=int((~det[:,m['post_start']:m['npost']].any(axis=1)).sum())
            b=int((~det[:,:m['npost']].any(axis=1)).sum())
            result['observable_controls'].append(dict(n4=n,probe=probe,observables=d.num_observables,
                full_detectors=d.num_detectors,teleport_acceptance_exact=alpha,shots=200000,
                accepted_teleport_only=a,accepted_all_prefix=b))
        print(n,'completed',round(time.monotonic()-started,2),flush=True)
        result['wall_seconds']=time.monotonic()-started
        result['scope']=['54: all 720 temporal permutations of ONE fixed quad coloring; 72:16 cyclic/reversed permutations of ONE coloring.',
            'Both codes:32 deterministic edge-coloring seeds. Fixed structured tricycle ordering (0,2,1,3).',
            'This is not an exhaustive search of all edge colorings or a circuit-distance optimization.',
            'Phase probe measures three logical X parities. Bell probe measures paired X/Z parities of a declared Clifford channel; neither is full non-Clifford magic-state infidelity.',
            'All-prefix postselection includes preparation redundancies and differs from declared teleport-only baseline; no terminal quad readout is postselected.',
            'Acceptance does not depend on a decoder or the subsequent logical-error normalization.']
        out.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    main()
