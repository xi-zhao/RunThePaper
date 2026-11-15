"""Bounded reconstruction using measured values visible in QC22's publication."""

import json
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import nnls
from scipy.signal import find_peaks

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cat import shaped, square

INPUT = "config/public-measurements.json"
RESULT = "results/public-inversion.json"
LAMBDAS = np.array([1e-5,1e-4,1e-3,1e-2,.1,1.])
GRID = {
    "square_2ms": (0, 50000, 250),
    "slepian_2ms": (0, 50000, 250),
    "square_16ms": (30750, 32000, 15.625),
    "slepian_32ms": (0, 625, 7.8125),
}
SCENARIOS = {
    "fixed_zero_even_odd": (False, 1, False, 0),
    "fit_floor_even_odd": (True, 1, False, 0),
    "fit_floor_resample_even_odd": (True, 1, True, 0),
    "fit_floor_resample_blocks": (True, 5, True, 0),
}
CAPTION_SHIFT = "fit_floor_resample_caption_order"
WEAK_SIGNAL = "fit_floor_resample_weak_signal"


def fit_tone(panel):
    frequency, measured, sem = np.array(panel["points"]).T
    theory_f, theory_p = np.array(panel["theory"]).T
    printed = np.interp(frequency,theory_f,theory_p)
    order,tau = panel["order"],panel["tau_s"]
    if panel["kind"]=="slepian":
        t = (np.arange(4096)+.5)/4096
        k = abs(np.exp(2j*np.pi*frequency[:,None]*tau*t)@(t*shaped(order,t))/len(t))**2
    else:
        _, moment = square(order,frequency*tau)
        k = abs(moment)**2
    a = np.column_stack([np.ones(len(frequency)),k/k.max()])
    beta = nnls(a/sem[:,None],measured/sem)[0]
    residual = (measured-a@beta)/sem
    print_residual = (measured-printed)/sem
    n = np.argsort(abs(print_residual))[-3:][::-1]
    return dict(points=len(frequency), rms_error_sem=float(np.sqrt(np.mean(print_residual**2))),
                fitted_rms_error_sem=float(np.sqrt(np.mean(residual**2))),
                largest_printed_residual_hz_sem=np.column_stack([frequency[n],print_residual[n]]).tolist(),
                fitted_baseline=float(beta[0]), fitted_peak_above_baseline=float(beta[1]),
                max_measured_probability=float(measured.max()),
                predicted=printed.tolist(), fitted=(a@beta).tolist())


def filter_bank(key, order, tau):
    start, end, delta = GRID[key]
    f = np.arange(start, end+delta/2, delta)
    if key.startswith("square"):
        h = np.array([abs(square(int(s),f*tau)[1])**2 for s in order])
    else:
        n=4096
        t=(np.arange(n)+.5)/n
        k=np.rint(f*tau*4).astype(int)
        assert max(abs(k-f*tau*4)) < 1e-9
        h=np.array([abs(np.fft.rfft(t*shaped(int(s),t),n=4*n)[k]/n)**2 for s in order])
    scale = np.linalg.norm(h,2)
    return f,h/scale,scale


def prepare(key,panel,scenario):
    floor, block, perturb, shift = SCENARIOS.get(scenario, (True, 1, True, int(scenario == CAPTION_SHIFT)))
    data=panel["points"]
    if scenario==WEAK_SIGNAL:
        data=[row for row in data if row[1]<=.10]
    s = np.array([r[0] for r in data])+shift
    y = np.array([r[1] for r in data])
    sigma = np.array([r[2] if r[2] is not None else 0. for r in data])
    f, h, norm = filter_bank(key,s,panel["tau_s"])
    difference = np.diff(np.eye(len(f)),axis=0)
    if floor:
        h=np.column_stack((h,np.ones(len(s))/np.sqrt(len(s))))
        difference=np.column_stack((difference,np.zeros(len(f)-1)))
    folds=(np.arange(len(s))//block)%2
    return s,y,sigma,f,h,norm,difference,folds,floor,perturb


def fit(h,d,y,lam):
    a=np.vstack((h,np.sqrt(lam)*d))
    rhs=np.r_[y,np.zeros(len(d))]
    return nnls(a,rhs,maxiter=5000)[0]


def invert(key,panel,scenario):
    s,y,sigma,f,h,norm,d,folds,floor,perturb=prepare(key,panel,scenario)
    rng=np.random.default_rng(222026)
    repeated=[y]
    if perturb:
        repeated += [y+rng.normal(0.,sigma) for _ in range(3)]
    errors=[]
    for lam in LAMBDAS:
        fold_errors=[]
        for side in (0,1):
            train=folds==side
            test=~train
            for z in repeated:
                c=fit(h[train],d,z[train],lam)
                fold_errors.append(float(np.sqrt(np.mean((h[test]@c-y[test])**2))))
        errors.append(float(np.mean(fold_errors)))
    lam=float(LAMBDAS[np.argmin(errors)])
    c=fit(h,d,y,lam)
    assert np.isfinite(c).all()
    spec=c[:len(f)]
    predicted=h@c
    peaks=find_peaks(spec,prominence=.03*spec.max())[0]
    ranked=sorted(peaks,key=lambda i:-spec[i])[:10]
    g=h.T@(predicted-y)+lam*(d.T@(d@c))
    return dict(order=s.tolist(),frequency_hz=f.tolist(),spectrum_relative=spec.tolist(),
        baseline_p1=float(c[-1]/np.sqrt(len(s))) if floor else 0.,kernel_norm=float(norm),
        coefficient_vector=c.tolist(),p1_predicted=predicted.tolist(),
        lambda_grid=LAMBDAS.tolist(),selected_lambda=lam,fold_rmse=errors,
        training_rmse=float(np.sqrt(np.mean((predicted-y)**2))),
        largest_interior_peaks_hz=[float(f[i]) for i in ranked],largest_bin_hz=float(f[spec.argmax()]),
        first_order_max_residual=float(max(np.max(abs(g[c>1e-9]),initial=0.),-g.min())))


def main():
    data=json.loads(Path(INPUT).read_text())
    tone={}
    for key,panel in data["fig2"].items():
        panel={**panel,"kind":key.split("_")[0]}
        tone[key]=fit_tone(panel)
    inverse={}
    for key,panel in data["sm3"].items():
        inverse[key]={}
        cases=list(SCENARIOS)
        if key=="square_16ms":
            cases.append(CAPTION_SHIFT)
        if any(r[1]>.10 for r in panel["points"]):
            cases.append(WEAK_SIGNAL)
        for scenario in cases:
            inverse[key][scenario]=invert(key,panel,scenario)
            print(key,scenario,inverse[key][scenario]["largest_interior_peaks_hz"][:3],flush=True)
    Path(RESULT).write_text(json.dumps(dict(fig2=tone,sm3=inverse),indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    # Accelerate sometimes sets floating-point flags after finite matrix products.
    with np.errstate(divide="ignore", over="ignore", invalid="ignore"):
        main()
