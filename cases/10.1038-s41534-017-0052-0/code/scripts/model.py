"""Independent implementation of main Eq.2 and supplement Table S3.
Time ordering in every list is left to right; matrices multiply on left.
"""
import numpy as np
from scipy.linalg import expm
P=np.array([[[0,1],[1,0]],[[0,-1j],[1j,0]],[[1,0],[0,-1]]],complex)
I=np.eye(2,dtype=complex)
TABLE=[['i'],['x'],['y'],['z'],['X'],['Y'],['Z'],['a'],['b'],['c'],['z','X'],['z','a'],['Z','x'],['c','x'],['Z','X'],['Z','a'],['X','c'],['z','b'],['Z','b'],['c','Y'],['z','Y'],['c','X'],['Z','Y'],['c','a']]
SPEC={'i':(-1,np.pi),'x':(0,np.pi),'y':(1,np.pi),'z':(2,np.pi),'X':(0,np.pi/2),'Y':(1,np.pi/2),'Z':(2,np.pi/2),'a':(0,-np.pi/2),'b':(1,-np.pi/2),'c':(2,-np.pi/2)}
def pulse(label,d):
 axis,theta=SPEC[label];d=np.asarray(d)
 if axis==2: return np.broadcast_to(expm(-.5j*theta*P[2]),d.shape+(2,2)).copy()
 if axis==-1:
  out=np.zeros(d.shape+(2,2),complex);out[...,0,0]=np.exp(-.5j*theta*(1+d));out[...,1,1]=np.exp(-.5j*theta*(1-d));return out
 h=np.zeros(d.shape+(3,));h[...,axis]=theta/2;h[...,2]=abs(theta)*d/2
 r=np.linalg.norm(h,axis=-1);return np.cos(r)[...,None,None]*I-1j*np.sinc(r/np.pi)[...,None,None]*np.einsum('...k,kij->...ij',h,P)
def cliff(k,d):
 u=np.broadcast_to(I,np.shape(d)+(2,2)).copy()
 for p in TABLE[k]: u=pulse(p,d)@u
 return u
C=np.array([cliff(k,0.) for k in range(24)])
def sequences(rng,n,J):
 s=rng.integers(0,24,(n,J));u=np.broadcast_to(I,(n,2,2)).copy()
 for j in range(J-1):u=C[s[:,j]]@u
 overlaps=abs(np.einsum('kab,nba->nk',C,u))/2
 s[:,-1]=overlaps.argmax(axis=1)
 assert np.min(overlaps.max(axis=1))>1-1e-12
 return s
def walks(s):
 u=np.broadcast_to(I,(len(s),2,2)).copy();v=np.zeros((len(s),3))
 for j in range(s.shape[1]):
  q=u.conj().swapaxes(-1,-2)@P[2]@u
  v+=np.einsum('nab,kba->nk',q,P).real/2
  u=C[s[:,j]]@u
 return np.sum(v[:,:2]**2,axis=1)
def simulate(s,noise,mode):
 # noise shape (nreal,) for common DC samples, or (nseq,nreal,J)
 n=len(s);nr=noise.shape[-2] if mode=='white' else len(noise)
 u=np.broadcast_to(I,(n,nr,2,2)).copy()
 for j in range(s.shape[1]):
  if mode=='dc': gates=np.array([cliff(k,noise) for k in range(24)])[s[:,j]]
  else:
   gates=np.empty_like(u)
   for k in range(24):
    mask=s[:,j]==k
    if np.any(mask):gates[mask]=cliff(k,noise[mask,:,j])
  u=gates@u
 return 1-abs(u[...,0,0])**2
