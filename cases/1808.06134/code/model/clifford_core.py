"""Independent phase-free stabilizer simulation of the v2 UP brickwork model.
Columns [X0,Z0,X1,Z1,...] are packed stabilizer-generator bits. Phases are
unnecessary ONLY because neither gate ensemble nor measurement locations depend
on outcomes; all pure-stabilizer Rényi entropies depend on binary support alone.
"""
import os
from pathlib import Path
os.environ.setdefault('NUMBA_NUM_THREADS','6')
os.environ.setdefault('NUMBA_CACHE_DIR',str(Path.cwd()/'scratch/numba'))
import numpy as np
from numba import njit,prange

def primitive(v,op):
    x0,z0,x1,z1=[(v>>i)&1 for i in range(4)]
    if op==0:x0,z0=z0,x0
    if op==1:x1,z1=z1,x1
    if op==2:z0^=x0
    if op==3:z1^=x1
    if op==4:x1^=x0;z0^=z1
    return x0|(z0<<1)|(x1<<2)|(z1<<3)

def clifford_group():
    identity=(1,2,4,8); elements=[identity]; words=[()]; index={identity:0}
    for m,word in zip(elements,words):
        for op in range(5):
            new=tuple(primitive(v,op) for v in m)
            if new not in index:
                index[new]=len(elements);elements.append(new);words.append(word+(op,))
    assert len(elements)==720
    return np.array(elements,dtype=np.uint8),words

@njit
def initial(L):
    s=np.zeros((2*L,(L+63)//64),dtype=np.uint64)
    for q in range(L):s[2*q,q//64]=np.uint64(1)<<np.uint64(q%64)
    return s

@njit
def gate(s,q,m):
    nw=s.shape[1]
    for w in range(nw):
        old=np.empty(4,dtype=np.uint64)
        for i in range(4):old[i]=s[2*q+i,w]
        for j in range(4):
            val=np.uint64(0)
            for i in range(4):
                if (m[i]>>j)&1:val^=old[i]
            s[2*q+j,w]=val

@njit
def measure(s,q,parity):
    nw=s.shape[1]; a=np.empty(nw,dtype=np.uint64);pw=-1;pb=0
    for w in range(nw):
        a[w]=s[2*q,w]
        if parity:a[w]^=s[2*q+2,w]
        if pw<0 and a[w]!=0:
            pw=w
            for bit in range(64):
                if ((a[w]>>np.uint64(bit))&np.uint64(1))!=0:pb=bit;break
    if pw<0:return False
    mask=np.uint64(1)<<np.uint64(pb)
    a[pw]^=mask
    for c in range(s.shape[0]):
        if s[c,pw]&mask:
            for w in range(nw):s[c,w]^=a[w]
        s[c,pw]&=~mask
    s[2*q+1,pw]|=mask
    if parity:s[2*q+3,pw]|=mask
    return True

@njit
def entropy(s,LA):
    L=s.shape[0]//2;nw=s.shape[1]
    basis=np.zeros((L,nw),dtype=np.uint64);occupied=np.zeros(L,dtype=np.uint8);rank=0
    for c in range(2*LA):
        v=s[c].copy()
        for p in range(L):
            if (v[p//64]>>np.uint64(p%64))&np.uint64(1):
                if occupied[p]:
                    for w in range(nw):v[w]^=basis[p,w]
                else:
                    basis[p]=v;occupied[p]=1;rank+=1;break
    return rank-LA

@njit(parallel=True)
def ensemble(L,p,model,steps,seeds,group,record_times):
    n=len(seeds);out=np.zeros((n,len(record_times)),dtype=np.int16)
    for r in prange(n):
        np.random.seed(int(seeds[r]));s=initial(L);k=0
        if record_times[0]==0:out[r,0]=0;k=1
        for t in range(1,steps+1):
            for q in range((t-1)%2,L-1,2):
                if np.random.random()<p:
                    if model==1:measure(s,q,False);measure(s,q+1,False)
                    else:measure(s,q,True)
                gate(s,q,group[np.random.randint(len(group))])
            if k<len(record_times) and t==record_times[k]:
                out[r,k]=entropy(s,L//4);k+=1
    return out

@njit
def trace_circuit(L,positions,gate_ids,measure_types,group):
    s=initial(L);out=np.zeros((len(positions),L-1),dtype=np.int16)
    for k in range(len(positions)):
        q=positions[k]
        if measure_types[k]==1:measure(s,q,False);measure(s,q+1,False)
        if measure_types[k]==2:measure(s,q,True)
        gate(s,q,group[gate_ids[k]])
        for a in range(1,L):out[k,a-1]=entropy(s,a)
    return out,s
