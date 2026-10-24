import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'scratch/mpl')
os.environ['NUMBA_CACHE_DIR']=str(Path.cwd()/'scratch/numba')
os.environ['NUMBA_NUM_THREADS']='6'
import json,time,sys,numpy as np
from clifford_core import clifford_group,ensemble
cfg=json.loads(Path(sys.argv[1]).read_text());group,_=clifford_group();outdir=Path(cfg['output_dir']);outdir.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(cfg['seed']);rows=[];start=time.time()
for job in cfg['jobs']:
    L,p,model,n=job['L'],job['p'],job['model'],job['n']
    times=np.array(job.get('times',sorted(set([0]+[t for k in range(400,601,20) for t in [k-1,k]]))),dtype=np.int64)
    seeds=rng.integers(0,2**31-1,size=n,dtype=np.int64)
    t0=time.time();data=ensemble(L,p,model,job.get('steps',int(times[-1])),seeds,group,times)
    name=f'B{model}_L{L}_p{p:.5f}';np.savez_compressed(outdir/(name+'.npz'),times=times,entropy=data,seeds=seeds)
    keep=times>=job.get('steady_after',400);av=data[:,keep].mean(axis=1) if np.any(keep) else data[:,-1].astype(float)
    row={'model':model,'L':L,'p':p,'n':n,'times':times.tolist(),'mean':data.mean(axis=0).tolist(),'sem':(data.std(axis=0,ddof=1)/np.sqrt(n)).tolist(),'steady_mean':float(av.mean()),'steady_sem':float(av.std(ddof=1)/np.sqrt(n)),'trajectory_means':av.tolist(),'seconds':time.time()-t0,'file':name+'.npz'}
    rows.append(row);(outdir/'summary.json').write_text(json.dumps({'config':cfg,'rows':rows,'elapsed':time.time()-start},indent=2))
    print(name,'S=',row['steady_mean'],'sem=',row['steady_sem'],'s=',round(row['seconds'],2),flush=True)

import zipfile
with zipfile.ZipFile(outdir/"trajectories.zip","w",compression=zipfile.ZIP_STORED) as archive:
    for path in sorted(outdir.glob("*.npz")):archive.write(path,path.name)
