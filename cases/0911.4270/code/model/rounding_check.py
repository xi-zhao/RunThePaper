"""Sensitivity to rounding of printed dt; a parameter interval, not best-fit tuning."""
from pathlib import Path
import json,numpy as np
from threadpoolctl import threadpool_limits
from model import star_model,evolution,observe
cfg=json.loads(Path('code/config.json').read_text()); out={}
with threadpool_limits(limits=1):
 for f in cfg['figures']:
  steps=[f['dt']+shift for shift in [-.00005,-.000025,0,.000025,.00005]]; arr=[]
  for i in range(f['alpha_count']):
   alpha=i*f['alpha_step']; h,ws,g=star_model(alpha,f['power'],f['cutoff']); row=[]
   for dt in steps:
    u,e=evolution(h,np.arange(0,21+1e-12,dt)); row.append([x[0] for x in observe(u,ws,f['temperatures'])])
   arr.append(row)
  out[f['id']]={'dt_values':steps,'I':arr,'interpretation':'Five-point sensitivity sample of the +/-0.00005 rounding interval. This is not an exhaustive error bound or identified author step. Primary generation is unchanged.'}
Path('results/rounding_sensitivity.json').write_text(json.dumps(out,indent=2))
ref=json.loads(Path('evidence/reference_curves.json').read_text())
for f,d in out.items():
 arr=np.array(d['I'])[1:]; y=np.array([c['I'] for c in ref[f]['curves']]).T
 lo=arr.min(axis=1); hi=arr.max(axis=1); outside=np.maximum.reduce([lo-y,y-hi,np.zeros_like(y)])
 print(f,'max range',np.max(hi-lo,axis=0),'max residual outside sampled envelope',np.max(outside,axis=0),'end range',lo[-1],hi[-1],flush=True)
