"""Independent calculations for repeated Rx gates in QC21."""
from pathlib import Path
import json
import numpy as np
from scipy.linalg import expm
from scipy.optimize import least_squares


def main():
    n=np.arange(1,302,2)
    epsilon,beta=.006,.002
    x=np.array([[0,1],[1,0]])
    u=expm(-.5j*(np.pi+epsilon)*x)
    rho=np.diag([1.,0.]).astype(complex)
    values=[]
    for k in range(1,n[-1]+1):
        rho=u@rho@u.conj().T
        # Isotropic Bloch-vector contraction is the exact map for Eq. 15.
        rho=np.exp(-beta)*rho+(1-np.exp(-beta))*np.eye(2)/2
        if k%2: values.append(rho[1,1].real)
    def response(params):
        e,b=params
        return .5*(1-np.exp(-b*n)*np.cos((np.pi+e)*n))
    e=float(np.max(abs(np.array(values)-response([epsilon,beta]))))
    assert e<2e-12
    fit=least_squares(lambda q:response(q)-values,[.005,.003],bounds=(0,.03),gtol=1e-13)
    assert np.max(abs(fit.x-[epsilon,beta]))<1e-10
    # Pure amplitude damping after each ideal pi pulse is an affine, not
    # isotropic, map. Its steady state is shifted from 1/2.
    q=np.exp(-beta)
    z=0.
    damping=[]
    for k in range(1,n[-1]+1):
        z=q*(1-z)
        if k%2: damping.append(z)
    exact=q/(1+q)*(1+q**n)
    assert np.max(abs(exact-damping))<2e-14
    # Opposite signed static angles have the same population.
    sign_error=float(np.max(abs(response([epsilon,beta])-response([-epsilon,beta]))))
    out=dict(pulse_counts=n.tolist(),isotropic=values,amplitude_damping=damping,
        formula_max_abs=e,fit=fit.x.tolist(),opposite_angle_max_abs=sign_error,
        pure_T1_stationary_population=float(q/(1+q)),
        t1_microseconds_for_36ns_beta=float(.036/beta))
    Path("results/response.json").write_text(json.dumps(out,allow_nan=False)+"\n")

if __name__=="__main__":
    main()
