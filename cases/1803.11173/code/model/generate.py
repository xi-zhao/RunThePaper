import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'scratch'/'mpl')
os.environ['TMPDIR']=str(Path.cwd()/'scratch')
Path('scratch').mkdir(exist_ok=True)
import json,ctypes,subprocess,time,concurrent.futures
import numpy as np
cfg=json.loads(Path('config.json').read_text()); layers=np.array(cfg['layers'],dtype=np.int32)
subprocess.run(['/usr/bin/clang','-O3','-shared','-fPIC','code/moment.c','-o','scratch/moment.dylib'],check=True,env={**os.environ,'TMPDIR':str(Path.cwd()/'scratch')})
lib=ctypes.CDLL(str(Path('scratch/moment.dylib').resolve()))
lib.moment.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int,np.ctypeslib.ndpointer(np.int32,flags='C_CONTIGUOUS'),ctypes.c_uint64,np.ctypeslib.ndpointer(np.float64,flags='C_CONTIGUOUS')]
def calc(n):
 t=time.monotonic(); arr=[]
 for b in range(cfg['batches']):
  r=np.zeros((len(layers),6));lib.moment(n,cfg['trajectories']//cfg['batches'],len(layers),layers,cfg['seed']+n*100003+b*1000000007,r);arr.append(r)
 a=np.array(arr);m=a.mean(0); N=cfg['trajectories']; vals={}
 for col,name in [(0,'uniform'),(2,'fixed_y_diagnostic'),(4,'sqrt_h_diagnostic')]:
  vals[name]={'variance':m[:,col].tolist(),'se':np.sqrt(np.maximum(0,m[:,col+1]-m[:,col]**2)/(N-1)).tolist(),'batch_se':(a[:,:,col].std(0,ddof=1)/np.sqrt(cfg['batches'])).tolist()}
 res={'n':n,'layers':layers.tolist(),'trajectories':N,'values':vals,'batch_uniform':a[:,:,0].tolist(),'wall_seconds':time.monotonic()-t}
 print(json.dumps({'n':n,'seconds':res['wall_seconds'],'v500':vals['uniform']['variance'][-1],'se500':vals['uniform']['se'][-1]}),flush=True)
 return res
start=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=cfg['workers']) as pool: rows=list(pool.map(calc,cfg['qubits']))
Path('results/moments.json').write_text(json.dumps({'config':cfg,'method':'exact ensemble second moment, unbiased Pauli-path Monte Carlo','rows':rows,'wall_seconds':time.monotonic()-start},indent=2))
