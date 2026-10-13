"""Independent complex-Haar bases on the already verified physical kernels.

Source plots and source readings are not inputs. Complete orthonormal bases,
not independent pure-state samples, are the statistical sampling unit.
"""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
from generate_statics import schmidt_maps,entropies,main as regenerate_kernels


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',required=True);args=parser.parse_args()
    cfg=json.loads(Path(args.config).read_text());out=Path(cfg['output_dir']);out.mkdir(parents=True,exist_ok=True)
    regenerate_kernels()
    data=Path('outputs/data/statics.npz');arr=np.load(data)
    metadata=json.loads(Path('outputs/data/statics.json').read_text())
    rows=[];samples={};started=time.monotonic()
    for j,row in enumerate(metadata['sectors']):
        key=f"{row['statistics']}_X{row['X']}_Np{row['Np']}"
        states=arr[key+'_states'];V=arr[key+'_kernel'];D=V.shape[1];L=states.shape[1]
        assert np.linalg.norm(V.conj().T@V-np.eye(D))<1e-10
        maps=schmidt_maps([tuple(v) for v in states],L);rng=np.random.default_rng(cfg['seed']+j)
        projected=np.einsum('si,sl,sj->lij',V.conj(),states,V)
        mean=np.trace(projected,axis1=1,axis2=2).real/D
        variance=(np.einsum('lij,lji->l',projected,projected).real/D-mean**2)/(D+1)
        dstd=[];smean=[];sstd=[];mean_error=0.
        for draw in range(cfg['draws']):
            z=rng.normal(size=(D,D))+1j*rng.normal(size=(D,D));Q,R=np.linalg.qr(z)
            d=np.diag(R);Q*=d.conj()/abs(d)
            vectors=V@Q;density=(abs(vectors)**2).T@states
            S=entropies(vectors,maps)
            dstd.append(density.std(0));smean.append(S.mean(0));sstd.append(S.std(0))
            mean_error=max(mean_error,float(np.max(abs(density.mean(0)-mean))))
        dstd=np.asarray(dstd);smean=np.asarray(smean);sstd=np.asarray(sstd)
        for field,value in [('density_sd',dstd),('entropy_mean',smean),('entropy_sd',sstd)]:samples[key+'_'+field]=value
        vmean=(dstd**2).mean(0);vse=(dstd**2).std(0,ddof=1)/math.sqrt(cfg['draws'])
        rows.append(dict(id=key,Ns=D,statistics=row['statistics'],X=row['X'],Np=row['Np'],L=L,
            density_mean=mean.tolist(),exact_Haar_population_variance=np.maximum(0.,variance).tolist(),
            observed_population_variance_mean=vmean.tolist(),observed_population_variance_mean_SE=vse.tolist(),
            density_mean_invariance_max_error=mean_error,
            variance_mean_max_standardized_difference=float(np.max(abs(vmean-variance)/np.maximum(vse,1e-12)))))
        np.savez_compressed(out/'samples.npz',**samples)
        (out/'results.json').write_text(json.dumps(dict(config=cfg,rows=rows,elapsed_seconds=time.monotonic()-started,
            source_kernel_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),
            sampling_unit='one complete complex-Haar orthonormal basis per fixed (X,Np) sector',
            variance_formula='E[population variance]=[Tr(A^2)/D-(Tr(A)/D)^2]/(D+1)',
            population_sd_ddof=0,log_base='e'),indent=2)+'\n')
        print(json.dumps(dict(id=key,draws=cfg['draws'],elapsed_seconds=time.monotonic()-started)),flush=True)

if __name__=='__main__':main()
