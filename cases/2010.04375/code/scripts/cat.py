"""Independent displacement, weak-noise filter, and nonnegative inversion."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import nnls
from scipy.signal.windows import dpss


def square(order, f):
    """Return integral of y(t) and t*y(t) on normalized time [0, 1]."""
    edges=np.r_[0.,(np.arange(order)+.5)/order,1.]
    width=np.diff(edges)
    midpoint=edges[:-1]+width/2
    x=np.asarray(f)[:,None]*width
    phase=np.exp(2j*np.pi*np.asarray(f)[:,None]*midpoint)*(-1.)**np.arange(order+1)
    sinc=np.sinc(x)
    dsinc=np.empty_like(x)
    small=abs(x)<1e-3
    dsinc[small]=-np.pi**2*x[small]/3+np.pi**4*x[small]**3/30
    q=x[~small]
    dsinc[~small]=(np.cos(np.pi*q)-np.sinc(q))/q
    return ((phase*(width*sinc)).sum(axis=1),
            (phase*width*(midpoint*sinc+width*dsinc/(2j*np.pi))).sum(axis=1))


def shaped(order,t):
    win=dpss(len(t),1.,norm="approximate")
    return win*np.cos(np.pi*order*t)


def curves(order, f):
    plain,moment=square(order,f)
    integrated=np.divide(plain,2j*np.pi*f,out=moment.copy(),where=f!=0)
    return abs(moment)**2,abs(integrated)**2


def dynamic_check():
    # Compare exact driven displacement under two distinct time profiles to
    # the derivatives of the corresponding filters. Square segments are
    # integrated by Gauss quadrature at their exact discontinuities.
    order=7
    f=order/2
    edges=np.r_[0.,(np.arange(order)+.5)/order,1.]
    v,w=np.polynomial.legendre.leggauss(32)
    width=np.diff(edges)/2
    t=(edges[:-1,None]+width[:,None]*(v+1)).ravel()
    weight=(width[:,None]*w*(-1.)**np.arange(order+1)[:,None]).ravel()
    phase=2*np.pi*np.arange(48)/48
    sin=np.sin(2*np.pi*f*t+phase[:,None])
    derivative=[t*sin,(np.cos(phase[:,None])-np.cos(2*np.pi*f*t+phase[:,None]))/(2*np.pi*f)]
    moment=curves(order,np.array([f]))
    results=[]
    for q,kind,a in zip(derivative,("phase-times-t","integrated-frequency"),moment,strict=True):
        finite=[]
        for epsilon in (1.,.1,.001):
            alpha=np.exp(-1j*epsilon*q)@weight
            p=-.5*np.expm1(-2*1.4*abs(alpha)**2)
            finite.append(float(np.mean(p)/epsilon**2))
        limit=1.4*a[0]/2
        assert abs(finite[-1]/limit-1)<1e-6
        results.append(dict(model=kind,weak_probability_per_epsilon_squared=limit,exact=finite))
    return results


def profile():
    v=np.arange(0.,14.01,.01)
    n=4096
    t=(np.arange(n)+.5)/n
    out={}
    for order in (1,2,3,5,7,22,42,62,124):
        center=order/2
        f=np.unique(np.r_[v,np.arange(max(0,center-1.25),center+1.251,.01),
                         np.arange(3*center-1.25,3*center+1.251,.01)])
        w=shaped(order,t)
        transform=np.fft.rfft(t*w,n=n*100)/n
        sf=abs(transform[np.rint(f*100).astype(int)])**2
        p,physical=curves(order,f)
        first=abs(f-center)<.75
        third=abs(f-3*center)<.75
        k=np.where(first)[0][p[first].argmax()]
        data=dict(f_tau=f.tolist(),square=p.tolist(),integrated_square=physical.tolist(),
            slepian=sf.tolist(),peak_f_tau=f[k],square_third_ratio=p[third].max()/p[k],
            integrated_third_ratio=physical[third].max()/physical[first].max(),
            slepian_third_ratio=sf[third].max()/sf[first].max(),signed_slepian_area=float(w.mean()))
        if order==7:
            # Keep the experiment's stated peak drive amplitudes.
            data["fig2b_peak_slepian_over_square"]=sf[first].max()/p[first].max()*(6.2/2.6)**2
        out[str(order)]=data
    return out


def solve_case(order,tau,scale,kind,f,seed):
    # First-difference penalty and odd/even cross-validation as in S16–S19.
    # Chosen truth, SEM and seed are diagnostic, separate from observed data.
    n=4096 if max(order)<300 else 16384
    t=(np.arange(n)+.5)/n
    if kind=="square":
        bank=np.array([curves(int(s),f*tau)[0] for s in order])
    else:
        win=dpss(n,1.,norm="approximate")
        k=np.rint(f*tau*4).astype(int)
        assert np.max(abs(k-f*tau*4))<1e-8
        bank=np.array([abs(np.fft.rfft(t*win*np.cos(np.pi*s*t),n=4*n)[k]/n)**2 for s in order])
    eta=.05
    bank*=1.4*(np.pi*eta*2*np.pi*scale*tau*tau)**2*(f[1]-f[0])
    if tau==.002:
        target=.002+.04/(1+f/1400)+.06*np.exp(-.5*((f-5250)/300)**2)+.09*np.exp(-.5*((f-31500)/240)**2)
    elif tau==.016:
        target=.01+.1*np.exp(-.5*((f-31400)/60)**2)
    else:
        target=.005+.06/(1+(f/120)**2)
    clean=bank@target
    rng=np.random.default_rng(seed)
    sigma=max(clean.max()*.009,1e-8)
    y=clean+rng.normal(0,sigma,len(order))
    normal=np.linalg.norm(bank,2)
    b=bank/normal
    y=y/normal
    D=np.diff(np.eye(len(f)),axis=0)
    def fit(indices,z,lam):
        A=np.vstack([b[indices],np.sqrt(lam)*D])
        rhs=np.r_[z,np.zeros(len(f)-1)]
        s=nnls(A,rhs,maxiter=20*len(f))[0]
        kkt=A.T@(A@s-rhs)
        assert min(kkt)>-1e-8 and np.max(abs(kkt[s>1e-10]),initial=0)<1e-8
        return s
    even=np.arange(0,len(order),2)
    odd=np.arange(1,len(order),2)
    candidates=[.0001,.001,.01,.1,1.]
    errors=[]
    for lam in candidates:
        e=[]
        for train,test in [(even,odd),(odd,even)]:
            for _ in range(5):
                guess=fit(train,y[train]+rng.normal(0,sigma/normal,len(train)),lam)
                e.append(np.linalg.norm(b[test]@guess-y[test]))
        errors.append(float(np.mean(e)))
    lam=candidates[int(np.argmin(errors))]
    s=fit(np.arange(len(order)),y,lam)
    return dict(kind=kind,order=order.tolist(),tau_ms=tau*1e3,rabi_hz=scale,frequency_hz=f.tolist(),
                seed=seed,diagnostic_eta=eta,synthetic_P1_max=float(clean.max()),
                selected_lambda_normalized=lam,cv_errors=errors,truth=target.tolist(),estimate=s.tolist(),
                rmse=float(np.sqrt(np.mean((s-target)**2))))


if __name__=="__main__":
    import warnings
    warnings.filterwarnings("ignore",message=".*encountered in matmul",category=RuntimeWarning)
    result=dict(profile=profile(),time_domain=dynamic_check(),
       engineered_tone=dict(beta_hz=float(np.sqrt(2*1.6*550)),linear_sigma_hz=float(550*.2/np.sqrt(2*1.6*550))),
       scaling={str(t):{"relative_tone_threshold":(.002/t)**2,"relative_white_threshold":(.002/t)**1.5}
                for t in (.002,.016,.032)})
    for i,spec in enumerate([
        (np.arange(1,194),.002,9000,"square",np.arange(0,50000+250,250)),
        (np.arange(1,194),.002,20000,"slepian",np.arange(0,50000+250,250)),
        (np.arange(986,1019),.016,900,"square",np.arange(30750,32001,15.625)),
        (np.arange(1,38),.032,300,"slepian",np.arange(0,626,7.8125))
    ]):
        result.setdefault("inversion",[]).append(solve_case(*spec,22100+i))
    Path("results/cat.json").write_text(json.dumps(result,allow_nan=False)+"\n")
    print([(q["kind"],q["tau_ms"],q["rmse"]) for q in result["inversion"]])
