"""Independent generation. Reads only model.py and config.json, never original EPS/PDF."""
from pathlib import Path
import json,time
import numpy as np
from threadpoolctl import threadpool_limits
from model import star_model,evolution,observe
cfg=json.loads(Path('code/config.json').read_text())
Path('results').mkdir(exist_ok=True)
allres={}; trajectories={}; begun=time.monotonic()
with threadpool_limits(limits=1):
 for f in cfg['figures']:
  times=np.arange(0,cfg['tmax']+1e-12,f['dt'])
  alphas=np.arange(f['alpha_count'])*f['alpha_step']
  I=[]; min_eigs=[]; uni=[]
  for idx,alpha in enumerate(alphas):
   h,ws,g=star_model(alpha,f['power'],f['cutoff'],M=cfg['M'],wmax=cfg['omega_max'],grid=cfg['grid'])
   row,vals=evolution(h,times)
   o=observe(row,ws,f['temperatures'],r=cfg['r'])
   I.append([v[0] for v in o]); min_eigs.append(float(vals[0])); uni.append(float(np.max(abs(np.sum(abs(row)**2,axis=1)-1))))
   if idx in [0,20,50,65,70,85,90,100,120,150]:
    trajectories[f"{f['id']}_{idx}"]={'alpha':float(alpha),'t':times.tolist(),'eta':(abs(row[:,0])**2).tolist(),'E':[v[1].tolist() for v in o],'noise':[v[2].tolist() for v in o]}
  allres[f['id']]={'alpha':alphas.tolist(),'I':I,'temperatures':f['temperatures'],'dt':f['dt'],'t_last':float(times[-1]),'n_times':len(times),'min_eigenvalue':min_eigs,'max_unitarity_error':max(uni)}
  print(f['id'],'done',len(alphas),'alpha values; max unitarity error',max(uni),flush=True)
Path('results/generation.json').write_text(json.dumps(allres,indent=2,allow_nan=False))
Path('results/trajectories.json').write_text(json.dumps(trajectories,allow_nan=False))
Path('results/generation_meta.json').write_text(json.dumps({'seconds':time.monotonic()-begun,'method':'Real symmetric eigendecomposition of 351-mode number-conserving Hamiltonian; analytic reduced 4x4 covariance; stable partially transposed symplectic eigenvalue; 2*sum positive entanglement increments.','reference_read':False},indent=2))
