"""Logical-fault XOR importance proposal for the declared SD6 phase probe.

Motifs are independently enumerated, zero-full-syndrome DEM fault sets. The
mixture retains target support. Empirical errors do not certify rare tails.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import time
import numpy as np
from scipy.special import logsumexp
from simulate_sd6_factory_v2 import factory, Decoder, dem_arrays, binomial_interval
from structured_schedule import structured_tri


def weights(errors, indices, log_odds, log_pi, original_fraction):
    """Evaluate P(e)/Q(e) on the FINAL error vector, including all motifs."""
    ratios = np.zeros((len(errors), len(indices)), dtype=float)
    for k in range(indices.shape[1]):
        ix = indices[:, k]
        ratios += (1.0 - 2.0 * errors[:, ix]) * log_odds[ix]
    tilted_log_ratio = logsumexp(ratios + log_pi[None, :], axis=1)
    log_density_ratio = np.logaddexp(np.log(original_fraction),
        np.log1p(-original_fraction) + tilted_log_ratio)
    return np.exp(-log_density_ratio)


def toy_check():
    """Exhaustive disjoint-motif test with syndrome-only postselection."""
    p = np.array([.09, .16, .11, .21, .07, .13])
    h = np.array([[1, 1, 0, 0, 1, 1], [0, 0, 1, 1, 1, 1]], np.uint8)
    o = np.array([1, 0, 1, 0, 1, 0], np.uint8)
    motifs = np.array([[0, 1], [2, 3], [4, 5]])
    states = np.array(list(itertools.product([0, 1], repeat=len(p))), np.uint8)
    mass = np.prod(np.where(states, p, 1-p), axis=1)
    logs = np.log(p/(1-p)); lp = logs[motifs].sum(1); lp -= logsumexp(lp)
    pi = np.exp(lp); a = .2; q = a*mass.copy()
    assert np.all(h[:, motifs].sum(2) % 2 == 0)
    for ix, prob in zip(motifs, pi):
        flipped = states.copy(); flipped[:, ix] ^= 1
        q += (1-a)*prob*np.prod(np.where(flipped, p, 1-p), axis=1)
    w = weights(states, motifs, logs, lp, a)
    syndrome = states @ h.T % 2
    observable = states @ o % 2
    prediction = {}
    for i in np.argsort(-mass, kind='stable'):
        prediction.setdefault(tuple(syndrome[i]), int(observable[i]))
    failure = np.array([observable[i] != prediction[tuple(s)]
                        for i, s in enumerate(syndrome)])
    accepted = syndrome[:, 0] == 0
    alpha = mass[accepted].sum()
    truth = mass[accepted & failure].sum()/alpha
    estimate = (q*w)[accepted & failure].sum()/q[accepted].sum()
    checks = dict(q_sum=float(q.sum()), weighted_sum=float(q@w),
        max_weight_error=float(np.max(np.abs(q*w-mass))),
        acceptance_P=float(alpha), acceptance_Q=float(q[accepted].sum()),
        conditional_ler_P=float(truth), conditional_ler_weighted_Q=float(estimate))
    assert abs(checks['q_sum']-1) < 1e-13
    assert checks['max_weight_error'] < 1e-14
    assert abs(checks['acceptance_P']-checks['acceptance_Q']) < 1e-13
    assert abs(truth-estimate) < 1e-13
    return checks


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--config', required=True)
    ap.add_argument('--self-test-only', action='store_true'); args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    out = Path(cfg['output']); out.mkdir(parents=True, exist_ok=True)
    check = toy_check()
    (out/'self-test.json').write_text(json.dumps(check, indent=2)+'\n')
    if args.self_test_only:
        print(json.dumps(check)); return
    catalog = json.loads(Path(cfg['motifs']).read_text())['results']
    models = json.loads(Path('config/models.json').read_text())['pairs']
    rows = []
    for job in cfg['jobs']:
        t0 = time.monotonic(); m = next(m for m in models if m['quad'][0] == job['n4'])
        cat = next(v for v in catalog if v['n4'] == job['n4'])
        _, baseline, _ = factory(m, .001, .002,
                                tri_override=structured_tri(m, (0, 2, 1, 3)))
        assert hashlib.sha256(str(baseline).encode()).hexdigest() == cat['baseline_dem_sha256']
        c, dem, meta = factory(m, job['p'], job['pccz'],
                              tri_override=structured_tri(m, (0, 2, 1, 3)))
        h, o, p = dem_arrays(dem); h0, o0, _ = dem_arrays(baseline)
        assert np.array_equal(h, h0) and np.array_equal(o, o0)
        assert np.all((p > 0) & (p < .5))
        indices = np.asarray(cat['sets'], dtype=int)
        assert indices.size and np.all((indices >= 0) & (indices < len(p)))
        assert len(set(map(tuple, indices))) == len(indices)
        assert np.all(np.diff(indices, axis=1) > 0)
        assert np.all(h[:, indices].sum(2) % 2 == 0)
        logical = (o[:, indices].sum(2) % 2).T.astype(np.uint8)
        ints = np.sum(logical*(1 << np.arange(len(o))), axis=1)
        assert np.array_equal(ints, cat['logical']) and np.all(ints != 0)
        lp = np.log(p/(1-p)); log_pi = lp[indices].sum(1); log_pi -= logsumexp(log_pi)
        pi = np.exp(log_pi); a = float(cfg['original_fraction']); assert 0 < a < 1
        decoder = Decoder(dem, cfg.get('decoder_timeout', 30))
        assert np.array_equal(decoder.prob, p)
        # Stim return_errors ordering is verified against the exact DEM signature.
        sampler = dem.compile_sampler(seed=job['seed'])
        rng = np.random.default_rng(job['seed']+1)
        sl = slice(meta['post_start'], meta['npost'])
        n = accepted_count = raw_fails = injected_count = 0
        sums = np.zeros(8)  # Wf,Wf^2,Wfraction,Wfraction^2,W,W^2 (accepted); all W,W^2
        group_counts = np.zeros((2, 3), dtype=np.int64)  # draws, accepted, failures
        group_sums = np.zeros((2, 4))  # accepted block/bit sums and squares
        tag = f"n{job['n4']}_p{job['p']:.8g}_c{job['pccz']:.8g}"
        while n < job['shots']:
            batch = min(cfg.get('batch', 128), job['shots']-n)
            det, obs, errors = sampler.sample(batch, return_errors=True)
            assert errors.shape[1] == len(p)
            if n == 0:
                assert np.array_equal(errors.astype(np.uint8)@h.T % 2, det)
                assert np.array_equal(errors.astype(np.uint8)@o.T % 2, obs)
            inject = rng.random(batch) >= a
            chosen = rng.choice(len(indices), size=int(inject.sum()), p=pi)
            at = np.flatnonzero(inject)
            errors[at[:, None], indices[chosen]] ^= True
            obs[at] ^= logical[chosen].astype(bool)
            if n == 0:
                assert np.array_equal(errors.astype(np.uint8)@h.T % 2, det)
                assert np.array_equal(errors.astype(np.uint8)@o.T % 2, obs)
            w = weights(errors, indices, lp, log_pi, a)
            assert np.all(np.isfinite(w)) and np.max(w) <= 1/a + 1e-10
            accepted = ~np.any(det[:, sl], axis=1)
            ds = det[accepted].astype(np.uint8); os = obs[accepted].astype(np.uint8)
            fail = np.zeros(len(ds), bool); fraction = np.zeros(len(ds))
            if len(ds):
                patterns, inverse = np.unique(ds, axis=0, return_inverse=True)
                predictions = np.array([decoder.predict(x) for x in patterns], np.uint8)
                residual = os ^ predictions[inverse]
                fail = np.any(residual, axis=1); fraction = residual.mean(1)
            wf = w[accepted]*fail; wb = w[accepted]*fraction; wa = w[accepted]
            sums += [wf.sum(), wf@wf, wb.sum(), wb@wb, wa.sum(), wa@wa, w.sum(), w@w]
            for g in (0, 1):
                gm = inject == bool(g); am = gm[accepted]
                group_counts[g] += [gm.sum(), am.sum(), fail[am].sum()]
                group_sums[g] += [wf[am].sum(), wf[am]@wf[am], wb[am].sum(), wb[am]@wb[am]]
            n += batch; accepted_count += int(accepted.sum())
            raw_fails += int(fail.sum()); injected_count += len(at)
            progress = dict(tag=tag, shots=n, requested_shots=job['shots'], accepted=accepted_count,
                raw_failures=raw_fails, injected=injected_count, sums=sums.tolist(),
                component_counts=group_counts.tolist(), component_sums=group_sums.tolist(),
                decoder_calls=decoder.calls, decoder_seconds=decoder.seconds,
                wall_seconds=time.monotonic()-t0)
            if n % 1024 == 0 or n == job['shots']:
                (out/'progress.json').write_text(json.dumps(progress, indent=2)+'\n')
            if n % 10240 == 0: print(json.dumps(progress), flush=True)
        if accepted_count <= 1:
            raise RuntimeError('Insufficient accepted samples to estimate a conditional rate and SE; progress retained.')
        means = sums[[0, 2]]/accepted_count
        ses = np.sqrt(np.maximum(0, sums[[1, 3]]/accepted_count-means**2)/(accepted_count-1))
        row = dict(**job, acceptance=accepted_count/n, acceptance_ci95=binomial_interval(accepted_count, n),
            accepted=accepted_count, block_phase_ler=float(means[0]), per_qubit_phase_ler=float(means[1]),
            block_phase_ler_SE=float(ses[0]), per_qubit_phase_ler_SE=float(ses[1]),
            failure_weight_ESS=float(sums[0]**2/sums[1]) if sums[1] else 0,
            weight_mean=float(sums[6]/n), accepted_weight_mean=float(sums[4]/accepted_count),
            raw_failure_samples=raw_fails, injected=injected_count, motifs=len(indices),
            decoder_calls=decoder.calls, decoder_seconds=decoder.seconds,
            low_weight_certificates=decoder.certified_low_weight, wall_seconds=time.monotonic()-t0,
            baseline_dem_sha256=cat['baseline_dem_sha256'], current_dem_sha256=hashlib.sha256(str(dem).encode()).hexdigest(),
            component_counts=group_counts.tolist(), component_sums=group_sums.tolist())
        rows.append(row); print(json.dumps(row), flush=True)
        (out/'results.json').write_text(json.dumps(dict(format='qldpc.sd6-fault-tilt.v1', rows=rows,
            proposal=dict(original_fraction=a, motif_selection='product of target DEM odds, normalized',
                          estimator='mean(P/Q * failure among accepted proposal samples); no self-normalization'),
            limits=['Only the declared SD6 Clifford phase probe; full magic-state infidelity and paper curves remain unestablished.',
                    'Zero-syndrome XOR motifs preserve the entire syndrome marginal and therefore acceptance.',
                    'MLE targets independent DEM error sets, not logical coset posterior.',
                    'Empirical SE and failure ESS do not establish complete rare-tail coverage. Compare independent sampling methods.',
                    'Q retains original-target support, with P/Q bounded by 1/original_fraction.',
                    'Tri schedule (0,2,1,3), quad coloring seed 100001, perfect terminal Q readout excluded from postselection.']), indent=2)+'\n')


if __name__ == '__main__':
    main()
