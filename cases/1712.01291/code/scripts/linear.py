"""Paper-scale held-out linear tests and independently seeded tuning."""
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from filters import DT, M, NT, Q, ar_filter, ar_fit, ensemble_risk, extrapolate, lkffb_row, measurements, oscillator_basis, phase_records


SCENARIOS = [
    ("grid80", .5, 80, .01), ("near80", .499, 80, .01),
    ("dense45k", 8/9000, 45000, .01), ("dense80k", 8/9000, 80000, .01),
    ("small20", .497, 20, .01), ("small40", .497, 40, .01),
    ("small60", .497, 60, .01), ("small80", .497, 80, .01), ("small200", .497, 200, .01),
    ("dense45k-low", 8/9000, 45000, .001), ("dense45k-high", 8/9000, 45000, .1),
    ("dense45k-max", 8/9000, 45000, .25),
]


def candidates(seed):
    rng = np.random.default_rng(seed)
    return 10**rng.uniform([-12., -7.], [-2., 3.], size=(75, 2))


def choose(results):
    losses = np.asarray(results)
    cut = .1*np.median(losses, axis=0)
    overlap = np.flatnonzero(np.all(losses < cut, axis=1))
    best = min(overlap, key=lambda i: losses[i, 0]) if len(overlap) else losses[:, 1].argmin()
    return int(best), overlap.tolist(), cut.tolist()


def loss(truth, posterior, forecast):
    return [float(np.mean((posterior[:, -50:]-truth[:, NT-50:NT])**2)),
            float(np.mean((forecast[:, :50]-truth[:, NT:NT+50])**2))]


def lkffb(observed, basis, process, readout):
    return [np.asarray(x) for x in zip(*(lkffb_row(y,basis,process,readout) for y in observed))]


def linear_case(index):
    name, fundamental, modes, level = SCENARIOS[index]
    seed = 231200+100*(2 if modes==45000 else index)
    fit = phase_records(np.random.default_rng(seed), M, fundamental, modes, NT)
    cal = phase_records(np.random.default_rng(seed+1), M, fundamental, modes, NT+100)
    truth = phase_records(np.random.default_rng(seed+2), M, fundamental, modes, NT+100)
    a = ar_fit(measurements(np.random.default_rng(seed+3), fit, level))
    y_cal = measurements(np.random.default_rng(seed+4), cal, level)
    y = measurements(np.random.default_rng(seed+5), truth, level)
    basis = oscillator_basis(truth.shape[1])
    grid = candidates(seed+6)
    def akf_trial(pair):
        return loss(cal, *ar_filter(a, y_cal, 100, *pair, 0.))
    with ThreadPoolExecutor(max_workers=6) as pool:
        akf_loss = list(pool.map(akf_trial, grid))
    ai, ao, ac = choose(akf_loss)
    train, akf = ar_filter(a, y, 100, *grid[ai], 0.)
    lsf = np.array([extrapolate(a, np.ascontiguousarray(row[-Q:][::-1]), 100) for row in y])
    run_lkffb = index < 9 or name=="dense45k-high"
    out = dict(name=name,seed=seed,fundamental=fundamental,modes=modes,noise_level=level,
               coefficients=a.tolist(), candidate_sigma2_R=grid.tolist(), akf_loss=akf_loss,
               akf_selection=ai,akf_overlap=ao,akf_low_loss_cut=ac,
               risk_AKF=ensemble_risk(truth[:, NT:],akf).tolist(),risk_LSF=ensemble_risk(truth[:, NT:],lsf).tolist(),
               sample=dict(truth=truth[0, NT-100:].tolist(), measured=y[0,-100:].tolist(),
                           AKF=train[0,-100:].tolist()+akf[0].tolist(), LSF=lsf[0].tolist()))
    if run_lkffb:
        # Use the same 75-point protocol for both algorithms in each
        # simulated scenario where the fixed Fourier basis is used.
        def fourier_trial(pair):
            past, future, _ = lkffb(y_cal, basis, *pair)
            return loss(cal,past,future)
        with ThreadPoolExecutor(max_workers=6) as pool:
            lk_loss = list(pool.map(fourier_trial,grid))
        fi, fo, fc = choose(lk_loss)
        past, future, state = lkffb(y, basis, *grid[fi])
        out.update(lkffb_loss=lk_loss,lkffb_selection=fi,lkffb_overlap=fo,lkffb_low_loss_cut=fc,
                   risk_LKFFB=ensemble_risk(truth[:, NT:],future).tolist())
        out["sample"]["LKFFB"] = past[0,-100:].tolist()+future[0].tolist()
        frequency=np.arange(1,201)*.5
        transfer=1-np.exp(-2j*np.pi*DT*frequency[:,None]*np.arange(1,Q+1))@a
        out["spectrum"] = dict(frequency_Hz=frequency.tolist(),
            AKF_psd_rad2_per_Hz=(2*DT*grid[ai,0]/np.abs(transfer)**2).tolist(),
            LKFFB_psd_rad2_per_Hz=(state[0,:100]**2+state[0,100:]**2).tolist())
    return out
