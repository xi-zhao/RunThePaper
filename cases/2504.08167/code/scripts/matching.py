"""Independent magnetic map observability and height controls."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

rng=np.random.default_rng(1101)
x=np.linspace(0,210000,501)
wavelength=np.array([18000,51000,122000])
k=2*np.pi/wavelength
amp=np.array([20.,35.,45.])
phase=np.array([.2,-.5,1.3])
heights=np.array([3600,19000])*.3048


def field(x,h):
    return np.cos(np.asarray(x)[:,None]*k+phase)@(amp*np.exp(-h*k))


out=[]
for h in heights:
    y=field(x+800,h)+7+rng.normal(0,.9,len(x))
    ans=least_squares(lambda p:field(x+p[0]*1000,h)+p[1]-y,[0.,0.],gtol=1e-10)
    deriv=(field(x+.01,h)-field(x-.01,h))/.02
    jac=np.column_stack([1000*deriv,np.ones(len(x))])
    cov=.9**2*np.linalg.inv(jac.T@jac)
    out.append(dict(h_m=float(h),truth_shift_m=800,estimated_shift_m=float(1000*ans.x[0]),
        truth_bias_nt=7.,estimated_bias_nt=float(ans.x[1]),shift_sd_m=float(1000*np.sqrt(cov[0,0])),
        attenuation=np.exp(-h*k).tolist()))
linear=np.column_stack([np.full(len(x),.25),np.ones(len(x))])
assert np.linalg.matrix_rank(linear)==1
assert all(abs(a["estimated_shift_m"]-800)<6*a["shift_sd_m"] for a in out)
Path("results/matching.json").write_text(json.dumps(dict(seed=1101,n=len(x),wavelength_m=wavelength.tolist(),fit=out,
 rank_constant_gradient=1,parameters=2),allow_nan=False)+"\n")
