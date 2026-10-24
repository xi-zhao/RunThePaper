"""Seeded disorder ensembles with per-realization values retained."""
import os
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[key]='1'
import argparse,json,time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import numpy as np
from threadpoolctl import threadpool_limits
from xxz import evolve, free_evolve

def chunk(job):
    task,eta,start,stop=job
    L=task['L'];times=np.array(task['times']);js=task['Jzs']
    vals=np.zeros((stop-start,len(js),len(times),2));fields=np.zeros((stop-start,L));states=np.zeros(stop-start,dtype=np.int64)
    with threadpool_limits(limits=1):
        for k,r in enumerate(range(start,stop)):
            rng=np.random.default_rng(np.random.SeedSequence([task['seed'],r]))
            h=rng.uniform(-eta,eta,L)
            state=sum(1<<int(i) for i in rng.choice(L,L//2,replace=False))
            fields[k]=h;states[k]=state
            for j,Jz in enumerate(js):
                s,v=free_evolve(L,h,state,times) if Jz==0 else evolve(L,h,Jz,state,times)
                vals[k,j,:,0]=s;vals[k,j,:,1]=v
    return start,stop,vals,fields,states

def run(cfg,out):
    started=time.monotonic(); results={}; summary=[]
    with ProcessPoolExecutor(max_workers=cfg.get('workers',1)) as pool:
        for task in cfg['tasks']:
            L=task['L']; n=task['samples']; key=task['id']
            times=np.array(task['times']); js=task['Jzs']
            vals=np.zeros((n,len(js),len(times),2)); fields=np.zeros((n,L)); states=np.zeros(n,dtype=np.int64)
            ts=time.monotonic()
            batch=task.get('batch',100);done=0
            jobs=[pool.submit(chunk,(task,cfg['eta'],a,min(a+batch,n))) for a in range(0,n,batch)]
            for fut in as_completed(jobs):
                a,b,v,h,s=fut.result();vals[a:b]=v;fields[a:b]=h;states[a:b]=s;done+=b-a
                if done%max(batch,task.get('checkpoint_every',500))==0 or done==n:
                    print(json.dumps({'task':key,'done':done,'seconds':time.monotonic()-ts}),flush=True)
            results[key+'_values']=vals;results[key+'_fields']=fields;results[key+'_states']=states
            results[key+'_times']=times;results[key+'_Jzs']=np.array(js)
            summary.append({'task':key,'L':L,'samples':n,'seconds':time.monotonic()-ts,'last_means':vals[:,:,-1,:].mean(axis=0).tolist()})
            # Preserve completed task blocks even if later work is interrupted.
            np.savez_compressed(out,**results)
            print(json.dumps(summary[-1]),flush=True)
    Path(out).with_suffix('.json').write_text(json.dumps({'tasks':summary,'wall_seconds':time.monotonic()-started,'entropy_unit':'nat','config':cfg},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');p.add_argument('output');a=p.parse_args()
    run(json.loads(Path(a.config).read_text()),a.output)
