"""Fig. 9, with Gaussian-process fitting restricted to training prefixes."""
import json
from pathlib import Path
import numpy as np
from numba import njit
from scipy.linalg import solve_toeplitz
from scipy.optimize import minimize_scalar
from filters import DT, M, NT, ensemble_risk, measurements, phase_records


def kernel(kind, d, ell, period):
    sq = (np.asarray(d)/ell)**2
    if kind == "RBF":
        return np.exp(-.5*sq)
    if kind == "RQ":
        return 1/(1+.5*sq)
    if kind == "MAT32":
        t = np.sqrt(3*sq)
        return (1+t)*np.exp(-t)
    # ell is a time-lag length in samples; the source ell is dimensionless.
    per = np.exp(-.5*(np.sin(np.pi*np.asarray(d)/period)*period/(np.pi*ell))**2)
    return per if kind == "PER" else per*np.exp(-.5*(np.asarray(d)/(NT/2))**2)


@njit
def logdet_toeplitz(r):
    """Innovation decomposition of a stationary Gaussian covariance."""
    n = len(r)
    phi = np.zeros(n)
    temp = np.zeros(n)
    v = r[0]
    total = np.log(v)
    for p in range(1,n):
        residual = r[p]
        for k in range(p-1):
            residual -= phi[k]*r[p-1-k]
        reflection = residual/v
        for k in range(p-1):
            temp[k] = phi[k]-reflection*phi[p-2-k]
        temp[p-1] = reflection
        for k in range(p):
            phi[k] = temp[k]
        v *= 1-reflection**2
        total += np.log(v)
    return total


def fit(kind, y, period):
    # Maximize exact conditional Gaussian marginal likelihood; profile the variance.
    # Optimize on training prefixes only, with a documented finite initialization grid.
    lag = np.arange(y.shape[1])
    def objective(log_length, ratio):
        ell = np.exp(log_length)
        r = kernel(kind,lag,ell,period)
        r[0] += ratio
        z = solve_toeplitz(r,y.T)
        amplitude = np.sum(z*y.T)/y.size
        return np.log(amplitude)+logdet_toeplitz(r)/y.shape[1]
    roots = np.log([2.,5.,10.,20.,50.,120.,300.])
    results = []
    for noise in (.00009,.0009,.009):
        coarse = [objective(x,noise) for x in roots]
        k = np.argmin(coarse)
        lower, upper = roots[max(0,k-1)],roots[min(len(roots)-1,k+1)]
        optimum = minimize_scalar(objective,args=(noise,),bounds=(lower,upper),method="bounded",
                                   options=dict(xatol=.02,maxiter=16))
        results.append((min(optimum.fun,coarse[k]),np.exp(optimum.x if optimum.fun<coarse[k] else roots[k]),noise))
    return min(results)


def forecast(kind, y, target, ell, ratio, period):
    train = np.arange(-NT,0)
    k = kernel(kind,np.arange(NT),ell,period)
    k[0] += ratio
    z = solve_toeplitz(k,y.T)
    cross = kernel(kind,np.asarray(target)[:,None]-train,ell,period)
    return (cross@z).T


def panel_a():
    rng = np.random.default_rng(40901)
    f = phase_records(rng,M,8/9000,45000,NT+50)
    y = measurements(rng,f,.01)
    calibration = measurements(rng,phase_records(rng,3,8/9000,45000,NT),.01)
    cases = [("PER",v) for v in (-70,0,70,1000,4000)] + [(v,3000) for v in ("RBF","RQ","MAT32","QPER")]
    rows=[]
    for kind,k in cases:
        period=NT+k if kind=="PER" else k
        score, ell, ratio = fit(kind,calibration,period)
        pred = forecast(kind,y,np.arange(50),ell,ratio,period)
        rows.append(dict(kernel=kind,kappa=period-NT,ell_samples=ell,noise_ratio=ratio,
                         log_likelihood_objective=score,risk=ensemble_risk(f[:,NT:],pred).tolist()))
    return rows


def sinusoid(label, hz, kappa):
    rng = np.random.default_rng(40902)
    t = np.arange(-NT,150)
    phase = .4
    f = np.cos(2*np.pi*hz*DT*t+phase)
    y=measurements(rng,f[None,:],.01)
    period=NT+kappa
    _,ell,ratio = fit("PER",y,period)
    target=np.arange(-100,150)
    manual=forecast("PER",y,target,8.,.0009,period)[0]
    optim=forecast("PER",y,target,ell,ratio,period)[0]
    previous=forecast("PER",y,target-period,ell,ratio,period)[0]
    return dict(label=label,hz=hz,kappa=kappa,ell_samples=ell,noise_ratio=ratio,
                periodic_error=float(np.max(np.abs(optim-previous))),time=target.tolist(),
                truth=f[-len(target):].tolist(),manual=manual.tolist(),optimized=optim.tolist())


output=dict(panel_a=panel_a(),sinusoids=[sinusoid(label,f,k) for label,f,k in
            [("b",3.,0),("c",10/3,0),("d",3.,70),("e",10/3,70)]])
Path("results/gp.json").write_text(json.dumps(output,allow_nan=False)+"\n")
