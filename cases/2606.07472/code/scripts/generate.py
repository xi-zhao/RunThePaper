"""Compute independent pulse-train fringes and sensitivity to undocumented timings."""
import json
from pathlib import Path
import numpy as np
from exchange import C,TAU,filtered_nodes,step_sum,centers,integrated_exchange,survival,gamma_fit,gate_control,rb_control,schedule

cfg=json.loads(Path("config/protocol.json").read_text())
assert np.array_equal(C,cfg["c"]) and np.array_equal(TAU,cfg["tau_ns"])
timing=cfg["default_ns"]
beta=cfg["beta"]
n=cfg["repetitions"]
x=np.linspace(.955,1.045,181)
rows=[]
for g in cfg["gamma"]:
    q,w=filtered_nodes(timing,g,n)
    center,base=centers(timing,g,beta,n)
    high,_=centers(timing,g,beta,n,40)
    angle=integrated_exchange(x,beta,q,w)/base*np.pi
    rows.append(dict(gamma=g,center=center.tolist(),spread=float(np.std(center)),
        voltage_error=float(np.max(abs(q-step_sum(timing,g,n,20)))),
        refinement_error=float(np.max(abs(center-high))),
        fidelity=survival(angle).T.tolist(),fidelity_half=survival(angle/2).T.tolist()))
scan=[gamma_fit(t,b) for t in cfg["schedules_ns"] for b in cfg["beta_scan"]]
spacing=[gamma_fit([10,0,10,t],beta) for t in cfg["spacing_scan_ns"]]
fit_default=gamma_fit(timing,beta)
control=[]
for gamma in (0,.699,1):
    q,w=filtered_nodes(timing,gamma,n,40)
    # Include the complete ring-down from the final segment.
    pieces=schedule(timing,gamma)*n
    jumps=np.diff(np.r_[0.,[v for _,v in pieces],0.])
    starts=np.r_[0.,np.cumsum([t for t,_ in pieces])]
    late=np.sum(jumps[:,None]*TAU*C*(1-np.exp(-(starts[-1]-starts[:,None])/TAU)))
    nominal=n*(timing[0]-gamma*timing[2])
    control.append(dict(gamma=gamma,area_error=float(abs((q@w).sum()+late-nominal)),
                        normalized_area=nominal/n,ring_down_area=float(late)))
out=dict(config=cfg,amplitude=x.tolist(),fringes=rows,scan=scan,spacing=spacing,default=fit_default,
         pulse_area=control,cliffords=gate_control(),blind_rb=rb_control())
Path("results/pulse-scan.json").write_text(json.dumps(out,separators=(",",":"),allow_nan=False)+"\n")
