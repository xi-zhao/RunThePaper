"""Coupled phase and Bell probes of the *declared* Clifford marginal model.

Physical shots are sampled once. The phase decoder uses only the marginal
syndrome; the Bell decoder also uses Z-checks. Decoder timeouts remain unknown.
Neither the Pauli channel nor its Bell infidelity is a non-Clifford factory.
"""
import argparse
import json
import time
import zipfile
from pathlib import Path
import numpy as np
from scipy.stats import beta
from simulate_sd6_factory_v2 import factory, dem_arrays, Decoder
from structured_schedule import structured_tri


def canonical(h, o, p):
    result = {}
    for a, b, q in zip(h.T, o.T, p):
        if not (a.any() or b.any()):
            continue
        key = np.packbits(np.r_[a, b]).tobytes()
        old = result.get(key, 0.)
        result[key] = old + q - 2*old*q
    return result


def cp(k, n, alpha=.05):
    if not n:
        return [0., 1.]
    return [0. if k == 0 else float(beta.ppf(alpha/2, k, n-k+1)),
            1. if k == n else float(beta.ppf(1-alpha/2, k+1, n-k))]


def decode_rows(decoder, syndrome, observations):
    patterns, inverse = np.unique(syndrome, axis=0, return_inverse=True)
    predictions = np.zeros((len(patterns), observations.shape[1]), np.uint8)
    known = np.zeros(len(patterns), bool)
    unknown = []
    for i, pattern in enumerate(patterns):
        try:
            predictions[i] = decoder.predict(pattern)
            known[i] = True
        except RuntimeError as exc:
            unknown.append(dict(pattern=i, shots=int(np.sum(inverse == i)), reason=str(exc)))
    residual = observations ^ predictions[inverse]
    residual[~known[inverse]] = 255
    return residual, known[inverse], unknown


def rate_summary(errors, known):
    n = len(known); u = int((~known).sum())
    block = int(np.any(errors[known], axis=1).sum())
    bits = errors[known].sum(axis=0).astype(int)
    # Simultaneous marginal intervals, valid without independence of bits.
    intervals = [cp(int(k), n, .05/errors.shape[1]) for k in bits]
    upper = [cp(int(k)+u, n, .05/errors.shape[1])[1] for k in bits]
    return dict(accepted=n, unknown=u, block_failures_known=block,
                bit_failures_known=bits.tolist(),
                mean_rate_identification=[float(bits.sum()/(n*len(bits))) if n else 0.,
                                          float((bits.sum()+u*len(bits))/(n*len(bits))) if n else 1.],
                mean_rate_ci95=[float(np.mean([a[0] for a in intervals])), float(np.mean(upper))],
                block_rate_ci95=[cp(block, n)[0], cp(block+u, n)[1]])


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True)
    cfg = json.loads(Path(ap.parse_args().config).read_text())
    out = Path(cfg['output_dir']); out.mkdir(parents=True, exist_ok=True)
    models = json.loads(Path('config/models.json').read_text())['pairs']
    rows = []; started = time.monotonic()
    for job in cfg['jobs']:
        start = time.monotonic()
        model = next(m for m in models if m['quad'][0] == job['n4'])
        tri = structured_tri(model, (0, 2, 1, 3))
        pc, pd, pm = factory(model, job['p'], job['pccz'], probe='phase', tri_override=tri)
        bc, bd, bm = factory(model, job['p'], job['pccz'], probe='bell', tri_override=tri)
        ph, po, pp = dem_arrays(pd); bh, bo, bp = dem_arrays(bd)
        a = canonical(ph, po, pp); b = canonical(bh[:len(ph)], bo[:3], bp)
        assert a.keys() == b.keys()
        delta = max(abs(a[k]-b[k]) for k in a)
        assert delta < 1e-12 and bm['post_start'] == pm['post_start'] and bm['npost'] == pm['npost']
        det, obs = bc.compile_detector_sampler(seed=job['seed']).sample(job['shots'], separate_observables=True)
        accept = ~det[:, bm['post_start']:bm['npost']].any(axis=1)
        ds = det[accept].astype(np.uint8); os = obs[accept].astype(np.uint8)
        phase = Decoder(pd, cfg['decoder_timeout']); bell = Decoder(bd, cfg['decoder_timeout'])
        pe, pk, pu = decode_rows(phase, ds[:, :len(ph)], os[:, :3])
        be, bk, bu = decode_rows(bell, ds, os)
        any_pauli = be[:, :3] | be[:, 3:]
        both = pk & bk
        row = dict(job, accepted=int(accept.sum()), acceptance=float(accept.mean()),
                   acceptance_ci95=cp(int(accept.sum()), job['shots']), marginal_channel_max_difference=delta,
                   phase=rate_summary(pe, pk), bell_z=rate_summary(be[:, :3], bk),
                   bell_x=rate_summary(be[:, 3:], bk), bell_any=rate_summary(any_pauli, bk),
                   paired_known=int(both.sum()),
                   phase_success_bell_failure=int(np.sum((~pe[both].any(axis=1)) & be[both].any(axis=1))),
                   phase_failure_bell_success=int(np.sum(pe[both].any(axis=1) & (~be[both].any(axis=1)))),
                   unknown_phase_patterns=pu, unknown_bell_patterns=bu,
                   exact_decoder_calls=dict(phase=phase.calls, bell=bell.calls),
                   seconds=time.monotonic()-start)
        tag=f"n{job['n4']}_p{job['p']:.8g}_s{job['seed']}"
        np.savez_compressed(out/(tag+'.npz'), det=det, obs=obs, accept=accept,
                            phase_errors=pe, phase_known=pk, bell_errors=be, bell_known=bk)
        (out/(tag+'-phase.stim')).write_text(str(pc)); (out/(tag+'-bell.stim')).write_text(str(bc))
        (out/(tag+'-metadata.json')).write_text(json.dumps(dict(phase=pm,bell=bm)))
        rows.append(row)
        (out/'results.json').write_text(json.dumps(dict(config=cfg, rows=rows, seconds=time.monotonic()-started,
            limitations=['Coupled Clifford marginal probes, not a simulation of the three-block non-Clifford factory.',
                'Most-likely independent DEM-error decoding, not maximum posterior logical-coset decoding.',
                'Same physical sample and acceptance mask; different syndrome information used by the two decoders.',
                'Every timeout remains unknown in the accepted denominator; rate intervals include worst-case unknowns.',
                'Per-point intervals; no global simultaneous coverage over all p and code sizes.']),indent=2)+'\n')
        print(json.dumps(row), flush=True)
    with zipfile.ZipFile(out/'samples-circuits.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):
            if p.suffix in ('.npz','.stim') or p.name.endswith('-metadata.json'):
                z.write(p,p.name)


if __name__ == '__main__':
    main()
