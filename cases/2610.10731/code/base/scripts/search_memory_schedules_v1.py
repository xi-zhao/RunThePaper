"""Bounded single-round circuit-fault search over declared macro schedules.

Stim's hypergraph search returns upper-bound witnesses, not distance proofs.
No witness found is unknown, never an infinite distance or an optimum.
"""
import json
import time
from pathlib import Path
from simulate_memory_v1 import memory_circuit


def main():
    cfg=json.loads(Path('config/memory-schedule-search-v1.json').read_text())
    models={m['quad'][0]:m for m in json.loads(Path('config/models.json').read_text())['pairs']}
    out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True);rows=[]
    for n in cfg['codes']:
        for seed in cfg['schedule_seeds']:
            for basis in ('X','Z'):
                started=time.monotonic()
                c,dem,meta=memory_circuit(models[n],.001,1,basis,'SD6',seed)
                try:
                    errors=c.search_for_undetectable_logical_errors(
                        dont_explore_detection_event_sets_with_size_above=6,
                        dont_explore_edges_with_degree_above=6,
                        dont_explore_edges_increasing_symptom_degree=True,
                        canonicalize_circuit_errors=True)
                except ValueError as e:
                    assert 'Failed to find any logical errors' in str(e)
                    errors=[]
                syndrome=set();logical=set();witness=[]
                for e in errors:
                    ds=[];ls=[]
                    for t in e.dem_error_terms:
                        target=t.dem_target
                        s=syndrome if target.is_relative_detector_id() else logical
                        v=target.val
                        s.symmetric_difference_update([v])
                        (ds if target.is_relative_detector_id() else ls).append(v)
                    witness.append(dict(detectors=ds,logical=ls,physical_locations=str(e)))
                assert not syndrome and (not errors or logical)
                rows.append(dict(n=n,seed=seed,basis=basis,rounds=1,
                    cnot_layers=meta['cnot_layers'],detectors=dem.num_detectors,
                    estimate_upper_bound=len(errors) if errors else None,
                    status='explicit_logical_fault_witness' if errors else 'search_inconclusive',
                    witness=witness,seconds=time.monotonic()-started))
                print(json.dumps({k:v for k,v in rows[-1].items() if k!='witness'}),flush=True)
                (out/'results.json').write_text(json.dumps(dict(config=cfg,rows=rows,
                    limitations=['One ideal-bounded noisy round and matching-basis syndrome for six logical observables.',
                        'Restricted hypergraph search; estimates are upper bounds, not a proof of the maximum-distance schedule.',
                        'This compares an explicit finite schedule family; the source-selected schedule and boundary remain unknown.']),indent=2)+'\n')


if __name__=='__main__':main()
