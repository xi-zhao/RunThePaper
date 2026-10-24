import os
from pathlib import Path
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['MPLCONFIGDIR']=str(Path.cwd()/'scratch/mpl')
import json,sys,time,concurrent.futures,numpy as np
from haar import trajectory,channel

def main():
    cfg=json.loads(Path(sys.argv[1]).read_text());out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True);rng=np.random.default_rng(cfg['seed']);rows=[];start=time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=cfg.get('workers',4)) as pool:
        for spec in cfg.get('trajectories',[]):
            L,model,n=spec['L'],spec['model'],spec['n'];seeds=rng.integers(0,2**31-1,n).tolist();t0=time.time()
            data=list(pool.map(trajectory,[(L,model,seed,spec.get('steps',200)) for seed in seeds]))
            cuts=np.array([d['cuts'] for d in data]);averages=cuts.mean(axis=1)
            row={'L':L,'model':model,'n':n,'seeds':seeds,'data':data,'mean':averages.mean(axis=0).tolist(),'sem':(averages.std(axis=0,ddof=1)/np.sqrt(n)).tolist(),'parity_means':cuts.mean(axis=0).tolist(),'seconds':time.time()-t0}
            rows.append(row);(out/'trajectories.json').write_text(json.dumps({'config':cfg,'rows':rows,'elapsed':time.time()-start},indent=2));print('A',model,'L',L,'S_half',row['mean'][L//2],'+-',row['sem'][L//2],'secs',row['seconds'],flush=True)
        channels=[]
        for spec in cfg.get('channels',[]):
            L,model,n=spec['L'],spec['model'],spec['n'];seeds=rng.integers(0,2**31-1,n).tolist();t0=time.time()
            data=list(pool.map(channel,[(L,model,seed,200) for seed in seeds]));channels+=data
            (out/'channels.json').write_text(json.dumps(channels,indent=2));print('channel',model,L,'maxdeficit',max(d['entropy_deficit'] for d in data),'secs',time.time()-t0,flush=True)
    # Exact A1 reduction: each covered pair is an independent Haar pure 2-qubit state.
    n=200000;z=rng.normal(size=(n,4))+1j*rng.normal(size=(n,4));z/=np.linalg.norm(z,axis=1)[:,None]
    pur=1-2*abs(z[:,0]*z[:,3]-z[:,1]*z[:,2])**2;s=-np.log2(pur)
    (out/'A1-exact-reduction.json').write_text(json.dumps({'n':n,'S_pair_mean':float(s.mean()),'S_pair_sem':float(s.std(ddof=1)/np.sqrt(n)),'S_pair_exact':float((np.pi/2-4/3)/np.log(2)),'parity_averaged_S':float(s.mean()/2),'L2_both_parities_S':float(s.mean()),'scope':'p=1, original open chain; for every interior cut with L>=4 half the layers cross it. L=2 empty alternate layer leaves previous pair entropy unchanged.'},indent=2))
if __name__=='__main__':main()
