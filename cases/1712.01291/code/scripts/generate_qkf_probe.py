"""Controls for the QKF discrepancy: nonlinear covariance and Gaussian bias."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import numpy as np
from scipy.linalg import solve_discrete_lyapunov, solve_toeplitz
from scipy.signal import lfilter
from filters import DT, M, NT, Q, ar_filter, ar_fit, ensemble_risk, measurements, phase_records


def covariance(a):
    f=np.vstack((a,np.eye(Q-1,Q)))
    q=np.zeros((Q,Q));q[0,0]=1.
    p=solve_discrete_lyapunov(f,q)
    scale=.65**2/p[0,0]
    row=np.empty(NT+50)
    x=p[:,0]*scale
    for k in range(len(row)):
        row[k]=x[0]
        x=f@x
    return scale,row


def evaluate(modes):
    rng=np.random.default_rng(30800+modes)
    n=NT+50
    f=phase_records(rng,M,.497,modes,NT)*.65
    a=ar_fit(measurements(rng,f,.01))
    innovation,corr=covariance(a)
    warm=12000
    truth=lfilter([1.],np.r_[1.,-a],np.sqrt(innovation)*rng.normal(size=(2*M,warm+n)),axis=1)[:,warm:]
    z=.5*np.cos(truth)
    shots=np.ascontiguousarray((rng.random((2*M,NT)) < (.5+z[:,:NT])).astype(float)-.5)
    mean=.5*np.exp(-corr[0]/2)
    # The observation covariance adds expected Bernoulli variance at zero lag only.
    c_z=.25*np.exp(-corr[0])*(np.cosh(corr)-1)
    r=c_z[:NT].copy()
    r[0]=.25-mean**2
    coeff=solve_toeplitz(r,(shots[M:]-mean).T)
    idx=np.arange(NT,NT+50)[:,None]-np.arange(NT)[None,:]
    known_gaussian=mean+(c_z[idx]@coeff).T
    # Held-out comparison with larger effective R. Choose on the other 50 sequences.
    grid=[(innovation*mult,R,init) for mult in (.1,1.,10.) for R in (.01,.08,.2) for init in (.08,.4,1.)]
    def score(pair):
        *qr,init=pair
        _,p=ar_filter(a,shots[:M],50,*qr,init,True)
        return float(np.mean(ensemble_risk(z[:M,NT:],p,mean)))
    with ThreadPoolExecutor(max_workers=4) as pool:
        scores=list(pool.map(score,grid))
    selected=int(np.argmin(scores))
    process,R,init=grid[selected]
    _,p=ar_filter(a,shots[M:],50,process,R,init,True)
    return dict(modes=modes,grid=grid,calibration_mean_risk=scores,selected=selected,
           risk_adjusted_EKF=ensemble_risk(z[M:,NT:],p,mean).tolist(),
           risk_linear_Born=ensemble_risk(z[M:,NT:],known_gaussian,mean).tolist(),
           expected_shot_variance=float(.25-mean**2-c_z[0]),
           stationary_covariance_residual=float(abs(corr[0]-.65**2)))


output=[]
for count in (20,40,60,80):
    output.append(evaluate(count))
    print("qkf-control",count,"written",flush=True)
Path("results/qkf-control.json").write_text(json.dumps(output,allow_nan=False)+"\n")
