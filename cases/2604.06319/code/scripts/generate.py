"""Generate the resource curves using only the disclosed architecture parameters."""
import json
from pathlib import Path

from resource_model import (enumerate_grid_ports, failure, idle_equivalence, mid_resources,
                            route_example, rsa_resources, state_transfer)

c = json.loads(Path("config/model.json").read_text())
m,r = c["mid"],c["rsa"]
curve = []
for n in range(6,1001):
    base,st,ra = [mid_resources(n,mode,m) for mode in ["baseline","STQM","RAQM"]]
    curve.append([n,base["total"],st["total"],ra["total"],base["total"]/st["total"],base["total"]/ra["total"]])
p = 1/12
# A common prefactor estimated from the explicitly reported d=15 QPU cycle error.
pref = m["p_logical"]/p**8
pa,pb = pref*p**13,pref*(p/5)**5
ratio = idle_equivalence(pa,pb)
out = dict(mid=dict(curve=curve,at_1000={mode:{str(n):mid_resources(1000,mode,m,n) for n in (1,2)}
                                       for mode in ["baseline","STQM","RAQM"]}),
           rsa={a[0]:rsa_resources(a,r) for a in r["architectures"]},
           transfer={str(x):state_transfer(m,x) for x in [1,50,1000]},router=route_example(m),
           idle=dict(common_prefactor=pref,pa=pa,pb=pb,cycle_ratio_equal=ratio,
                     boundary_s=ratio*m["time_qubit_s"],error_a=failure(pa,1e6),error_b=failure(pb,4)),
           point_port=[dict(hops=k,manhattan=enumerate_grid_ports(k),printed=2*k*k+6*k+1) for k in range(1,7)])
Path("results/model.json").write_text(json.dumps(out,indent=2)+"\n")
