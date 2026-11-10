"""Exact finite-state moment propagation including inverse Clifford; no Monte Carlo."""
from model import *
from scipy.linalg import expm_frechet
from pathlib import Path
import json

def generators(reverse=False,identity_half=False):
 cc=[];aa=[]
 for row in TABLE:
  u=I.copy();du=np.zeros((2,2),complex)
  for p in (row[::-1] if reverse else row):
   axis,t=SPEC[p];t=t/2 if identity_half and p=='i' else t
   h=-.5j*t*(I if axis<0 else P[axis]);v=-.5j*abs(t)*P[2] if axis!=2 else np.zeros((2,2))
   g,dg=expm_frechet(h,v);du=dg@u+g@du;u=g@u
  cc.append(u);aa.append(1j*u.conj().T@du)
 return np.array(cc),np.array(aa)
def moments(cc,aa,Js):
 trans=np.zeros((24,24),int);r=np.empty((24,24,3));inv=np.zeros(24,int)
 for k in range(24):
  for g in range(24):
   trans[k,g]=np.argmax(abs(np.einsum('aij,ij->a',cc.conj(),cc[g]@cc[k])))
   r[k,g]=np.einsum('ij,aji->a',cc[k].conj().T@aa[g]@cc[k],P).real/2
  inv[k]=np.argmax(abs(np.einsum('aij,ji->a',cc,cc[k])))
 p=np.zeros(24);p[0]=1;m=np.zeros((24,3));q=np.zeros(24);white=np.zeros(24);out={}
 for n in range(1,max(Js)):
  pn=np.zeros(24);mn=np.zeros((24,3));qn=np.zeros(24);wn=np.zeros(24)
  for g in range(24):
   t=trans[:,g];v=r[:,g];v2=np.sum(v[:,:2]**2,axis=1)
   np.add.at(pn,t,p/24);np.add.at(mn,t,(m+p[:,None]*v)/24)
   np.add.at(qn,t,(q+2*np.sum(m[:,:2]*v[:,:2],axis=1)+p*v2)/24)
   np.add.at(wn,t,(white+p*v2)/24)
  p,m,q,white=pn,mn,qn,wn
  J=n+1
  if J in Js:
   v=r[np.arange(24),inv];v2=np.sum(v[:,:2]**2,axis=1)
   out[str(J)]={'dc_coefficient':float(np.sum(q+2*np.sum(m[:,:2]*v[:,:2],axis=1)+p*v2)/J),'white_coefficient':float(np.sum(white+p*v2)/J)}
 return out
out={}
for name,reverse,half in [('literal',False,False),('reverse_pulse_order_control',True,False),('half_idle_control',False,True)]:
 c,a=generators(reverse,half);out[name]=moments(c,a,[2,25,50,100,200])
c,_=generators();out['interleaved_z_control']=moments(c,np.broadcast_to(P[2],(24,2,2)),[2,25,100,200])
Path('results/transfer.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
