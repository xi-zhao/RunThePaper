"""Matched coherent GS photon-cutoff controls; no Q dephasing.

Each trajectory resets its RNG at each cutoff. Finite paired observations
diagnose sensitivity; they are not an infinite-cutoff or ensemble certificate.
"""
import json
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from generate_coherent_packed import Packed


def job(args):
    cfg, model, model_index, indices = args
    started = time.monotonic()
    records, arrays = [], {}
    for level in cfg['levels']:
        active = {**cfg, **level}
        h = Packed(model['L'], model['N'], model['statistics'],
                   level['photon_cutoff'], cfg['delta'], cfg['gamma'])
        samples, traces, diagnostics = [], [], []
        for index in indices:
            rng = np.random.default_rng(np.random.SeedSequence(
                [cfg['seed'], model_index, index]))
            obs, trace, diag = h.trajectory(rng, active)
            samples.append(obs)
            traces.append(trace)
            diagnostics.append({**diag, 'trajectory_index': index})
            print(model['statistics'], level['id'], index,
                  round(time.monotonic() - started, 2), flush=True)
        prefix = model['statistics'] + '_' + level['id']
        for key in samples[0]:
            arrays[prefix + '_' + key] = np.array([s[key] for s in samples])
        arrays[prefix + '_traces'] = np.array(traces)
        records.append({'id': prefix, 'indices': indices,
                        'diagnostics': diagnostics})
    return arrays, records


def main():
    cfg = json.loads(Path('config/coherent-cutoff-64-controls.json').read_text())
    started = time.monotonic()
    jobs = [(cfg, m, mi, list(range(lo, min(lo + cfg['batch_size'], cfg['samples_per_model']))))
            for mi, m in enumerate(cfg['models'])
            for lo in range(0, cfg['samples_per_model'], cfg['batch_size'])]
    pieces, records = {}, []
    with ProcessPoolExecutor(max_workers=cfg['workers']) as pool:
        for a, r in pool.map(job, jobs):
            records.extend(r)
            for k, v in a.items():
                pieces.setdefault(k, []).append(v)
    arrays = {k: np.concatenate(v) for k, v in pieces.items()}
    comparisons = []
    for m in cfg['models']:
        for first, second in zip(cfg['levels'], cfg['levels'][1:]):
            a, b = (m['statistics'] + '_' + lev['id'] for lev in (first, second))
            for key in ['density', 'kinetic', 'pairing', 'entropy', 'X', 'photon', 'OdagO', 'traces']:
                delta = arrays[b + '_' + key] - arrays[a + '_' + key]
                mean = delta.mean(0)
                se = delta.std(0, ddof=1) / np.sqrt(len(delta))
                comparisons.append({'statistics': m['statistics'], 'levels': [first['id'], second['id']],
                                    'observable': key, 'mean_difference': mean.tolist(),
                                    'paired_SE': se.tolist(),
                                    'max_absolute_single_path_difference': float(np.max(abs(delta))),
                                    'samples': len(delta)})
    out = Path(cfg['output_prefix'])
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(str(out) + '.npz', **arrays)
    Path(str(out) + '.json').write_text(json.dumps({
        'config': cfg, 'records': records, 'comparisons': comparisons,
        'elapsed_seconds': time.monotonic() - started,
        'limits': ['Eight trajectories per particle statistics; rare branches may be missed.',
                   'All cutoffs use the same finite ODE tolerance; earlier controls bound only observed sensitivity.',
                   'Empirical paired SEs are not simultaneous confidence bounds or a proof of infinite-cavity convergence.',
                   'Coherence between Q sectors is retained; the initial cavity is explicitly vacuum.']
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
