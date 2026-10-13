"""Out-of-sample H3 normalization investigation with frozen public solvers.

Generation reads only configuration and solver code. Original figure readings
are confined to a separate checker. Physical entropy is always retained.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'solvers'))
import numpy as np
import scipy
import generate_dynamics as ds
import generate_coherent_packed as ps


def job(args):
    config, cohort, indices = args
    initial = cohort['initial']
    coherent = initial['id'] == 'GS'
    mod = ps if coherent else ds
    original = mod.solve_ivp
    captured = []
    def capture(*args, **kwargs):
        sol = original(*args, **kwargs)
        if sol.success and not len(sol.t_events[0]):
            captured.append(float(np.vdot(sol.y[:, -1], sol.y[:, -1]).real))
        return sol
    mod.solve_ivp = capture
    cfg = dict(config, times=[0., cohort['time']])
    h = (ps.Packed if coherent else ds.Hybrid)(cohort['L'], cohort['N'],
        cohort['statistics'], cohort['photon_cutoff'], cohort['delta'], cohort['gamma'])
    arrays = {k: [] for k in ['entropy_normalized', 'entropy_raw', 'terminal_survival_norm',
                               'photon', 'OdagO', 'X', 'density', 'jumps']}
    diagnostics = []
    start = time.monotonic()
    try:
        for j, index in enumerate(indices):
            rng = np.random.default_rng(np.random.SeedSequence([
                config['seed'], cohort['seed_group'], index]))
            if coherent:
                ob, _, dg = h.trajectory(rng, cfg)
            else:
                ob, _, dg = h.trajectory(initial['occupations'], rng, np.asarray(cfg['times']),
                    cfg['rtol'], cfg['atol'], entropy=True)
            assert len(captured) == j+1, 'One terminal segment required per path'
            w = captured[-1]
            assert 0 < w <= 1+1e-7
            arrays['entropy_normalized'].append(ob['entropy'])
            arrays['entropy_raw'].append(w*np.asarray(ob['entropy'])-w*np.log(w))
            arrays['terminal_survival_norm'].append(w)
            arrays['jumps'].append(dg['jumps'])
            for k in ['photon', 'OdagO', 'X', 'density']:
                arrays[k].append(ob[k])
            diagnostics.append(dict(index=index, **dg))
    finally:
        mod.solve_ivp = original
    record = dict(id=cohort['id'], indices=indices, diagnostics=diagnostics,
                  elapsed_seconds=time.monotonic()-start)
    return {k: np.asarray(v) for k, v in arrays.items()}, record


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--config', default='config.json')
    args = p.parse_args()
    config_path = ROOT/args.config
    cfg = json.loads(config_path.read_text())
    start = time.monotonic()
    tasks = [(cfg, c, list(range(lo, min(lo+cfg['batch_size'], c['samples']))))
             for c in cfg['cohorts'] for lo in range(0, c['samples'], cfg['batch_size'])]
    pieces = {}
    records = []
    with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
        futures = [pool.submit(job, task) for task in tasks]
        for f in as_completed(futures):
            arrays, record = f.result()
            pieces.setdefault(record['id'], []).append((record['indices'], arrays))
            records.append(record)
            print(record['id'], record['indices'], round(record['elapsed_seconds'], 3), flush=True)
    arrays = {}
    summaries = []
    for cohort in cfg['cohorts']:
        name = cohort['id']
        chunks = sorted(pieces[name], key=lambda x: x[0][0])
        assert [i for inds, _ in chunks for i in inds] == list(range(cohort['samples']))
        local = {k: np.concatenate([a[k] for _, a in chunks]) for k in chunks[0][1]}
        arrays.update({name+'__'+k: v for k, v in local.items()})
        summaries.append(dict(cohort=cohort, mean={k: a.mean(0).tolist() for k, a in local.items()},
                              SE={k: (a.std(0, ddof=1)/np.sqrt(len(a))).tolist() for k, a in local.items()}))
    out = ROOT/cfg['output_directory']
    out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out/'samples.npz', **arrays)
    deps = [Path(__file__), config_path, ROOT/'requirements.lock']+list((ROOT/'solvers').glob('*.py'))
    result = dict(config=cfg, records=records, summaries=summaries,
        runtime=dict(python=sys.executable, numpy=np.__version__, scipy=scipy.__version__,
                     elapsed_seconds=time.monotonic()-start),
        input_hashes={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in deps},
        raw_definition='w*S_norm-w*ln(w), with actual terminal no-jump norm squared w',
        entropy_cut='cavity plus c matter sites on the left; c=0 is the cavity-only cut',
        limitations=['Raw quantity is not normalized von Neumann entropy.',
                     'Only paper cohorts have original source-figure reference data.',
                     'Finite photon cutoff, explicit vacuum initial cavity and photon-counting unraveling.'])
    (out/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(cohorts=len(cfg['cohorts']), trajectories=sum(c['samples'] for c in cfg['cohorts']),
                          elapsed_seconds=result['runtime']['elapsed_seconds'])), flush=True)


if __name__ == '__main__':
    main()
