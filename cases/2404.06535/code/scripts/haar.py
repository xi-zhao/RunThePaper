"""Independent Haar averages for the stated T1 and ZZ scoring formulae."""
from pathlib import Path
import json
import numpy as np

rng=np.random.default_rng(15014)
n=200000
a=rng.normal(size=(n,4))+1j*rng.normal(size=(n,4))
p=abs(a)**2
p/=p.sum(axis=1,keepdims=True)
parity=p[:,0]+p[:,3]-p[:,1]-p[:,2]
full=float(np.mean(1-parity**2))
product=float(np.mean(1-rng.uniform(-1,1,n)**2*rng.uniform(-1,1,n)**2))
logical=float(np.mean(1-rng.uniform(-1,1,n)**2))
x=rng.random(n)
t=np.linspace(0,4,21)
direct=[np.mean(x+(x*x+(1-x)**2-x)*np.exp(-z)+2*x*(1-x)*np.exp(-z/2)) for z in t]
exact=.5+np.exp(-t/2)/3+np.exp(-t)/6
error=float(abs(direct-exact).max())
assert abs(full-.8)<.003 and abs(product-8/9)<.003 and abs(logical-2/3)<.003 and error<.004
Path("results/haar.json").write_text(json.dumps(dict(full_two_qubit=full,product_qubit=product,logical_parity=logical,
    analytic=[.8,8/9,2/3],sample=n,T1_max_mc_error=error),indent=2)+"\n")
