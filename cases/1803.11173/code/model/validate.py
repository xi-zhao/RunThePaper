"""Independent small-system state-vector and deterministic moment checks."""
from pathlib import Path
import json,time,math
import numpy as np
from scipy.linalg import expm
I=np.eye(2,dtype=complex);X=np.array([[0,1],[1,0]],complex);Y=np.array([[0,-1j],[1j,0]]);Z=np.diag([1,-1]);PA=[X,Y,Z]

def exact_moment(n,layers):
 size=4**n;idx=np.arange(size,dtype=np.int64); labels=np.array([(idx//(4**j))%4 for j in range(n)])
 x=sum(((labels[j]==1)|(labels[j]==2)).astype(np.int64)<<j for j in range(n));z=sum(((labels[j]==2)|(labels[j]==3)).astype(np.int64)<<j for j in range(n))
 zz=z^(((x<<1)^(x>>1))&((1<<n)-1));perm=np.zeros(size,np.int64)
 for j in range(n):
  a=(x>>j)&1;b=(zz>>j)&1;perm+=(a+3*b-2*a*b)*(4**j)
 boundary=np.array([0,.25,1/6,.25])[labels[0]]
 by=np.array([0,.5,0,.5])[labels[0]]
 for j in range(1,n):boundary*=np.array([1,5/12,1/6,5/12])[labels[j]];by*=np.array([1,5/12,1/6,5/12])[labels[j]]
 p=np.zeros(size);p[15]=1;out=[];masserr=0
 for L in range(1,max(layers)+1):
  p=p[perm]
  if L in layers:out.append({'L':L,'uniform':float(p@boundary),'fixed_y':float(p@by)})
  for q in range(n):
   v=p.reshape(-1,4,4**q);v[:,1:,:]=v[:,1:,:]*.5+v[:,1:,:].sum(axis=1,keepdims=True)/6
  masserr=max(masserr,abs(float(p.sum())-1))
 return {'n':n,'values':out,'max_mass_error':masserr,'stationary':2**n/(3*(4**n-1))}

def apply(v,p,q,theta):
 B,D=v.shape;ix=np.arange(D);sgn=1-2*((ix>>q)&1);flip=v[:,ix^(1<<q)]
 pv=np.where((p==0)[:,None],flip,np.where((p==1)[:,None],-1j*sgn[None,:]*flip,sgn[None,:]*v))
 return np.cos(theta[:,None]/2)*v-1j*np.sin(theta[:,None]/2)*pv

def mc_states(n,M,layers,seed):
 rng=np.random.default_rng(seed);D=2**n;ix=np.arange(D);obs=(1-2*(ix&1))*(1-2*((ix>>1)&1));cz=np.ones(D)
 for q in range(n-1):cz*=1-2*(((ix>>q)&1)*((ix>>(q+1))&1))
 one=np.array([np.cos(np.pi/8),np.sin(np.pi/8)]);state=one
 for _ in range(n-1):state=np.kron(one,state)
 sums={L:np.zeros(5) for L in layers};normerr=0
 for start in range(0,M,250):
  B=min(250,M-start);psi=np.tile(state,(B,1)).astype(complex);tangent=np.zeros_like(psi)
  for L in range(1,max(layers)+1):
   for q in range(n):
    axis=rng.integers(0,3,B);theta=rng.uniform(0,2*np.pi,B);psi=apply(psi,axis,q,theta)
    if L==1 and q==0:
     tangent=(apply(psi,axis,q,np.full(B,np.pi))-0)/2 # R(pi)=-iP, hence derivative=-iP/2
    else:tangent=apply(tangent,axis,q,theta)
   psi*=cz;tangent*=cz
   if L in sums:
    g=2*np.real(np.sum(psi.conj()*obs*tangent,axis=1));sums[L]+=np.array([len(g),g.sum(),(g*g).sum(),(g**3).sum(),(g**4).sum()]);normerr=max(normerr,float(abs(np.sum(abs(psi)**2,axis=1)-1).max()))
 out=[]
 for L,s in sums.items():
  N,sg,s2,s3,s4=s;mean=sg/N;v=(s2-N*mean**2)/(N-1);mu4=s4/N-4*mean*s3/N+6*mean**2*s2/N-3*mean**4;se=np.sqrt(max(0,(mu4-(N-3)/(N-1)*v*v)/N))
  out.append({'L':L,'mean':mean,'variance':v,'variance_se':se,'mean_se':np.sqrt(v/N),'samples':int(N)})
 return {'n':n,'values':out,'max_normalization_error':normerr}

def gradient_checks():
 rng=np.random.default_rng(17173);errs=[]
 for n in [2,3,4]:
  D=2**n;idx=np.arange(D);obs=np.diag((1-2*(idx&1))*(1-2*((idx>>1)&1)));cz=np.ones(D)
  for q in range(n-1):cz*=1-2*(((idx>>q)&1)*((idx>>(q+1))&1))
  Ucz=np.diag(cz);psi=np.array([np.cos(np.pi/8),np.sin(np.pi/8)])
  for _ in range(n-1):psi=np.kron(np.array([np.cos(np.pi/8),np.sin(np.pi/8)]),psi)
  for trial in range(8):
   axes=rng.integers(0,3,(3,n));ang=rng.uniform(0,2*np.pi,(3,n))
   def circuit(delta=0,tangent=False):
    v=psi.astype(complex);dv=np.zeros_like(v)
    for L in range(3):
     for q in range(n):
      P=np.array([[1]],complex)
      for k in range(n-1,-1,-1):P=np.kron(P,PA[axes[L,q]] if k==q else I)
      a=ang[L,q]+(delta if L==q==0 else 0);G=np.cos(a/2)*np.eye(D)-1j*np.sin(a/2)*P
      v=G@v
      if L==q==0:dv=-.5j*P@v
      else:dv=G@dv
     v=Ucz@v;dv=Ucz@dv
    return float(np.vdot(v,obs@v).real),float(2*np.vdot(v,obs@dv).real)
   e,g=circuit();ps=.5*(circuit(np.pi/2)[0]-circuit(-np.pi/2)[0]);h=1e-5;fd=(circuit(h)[0]-circuit(-h)[0])/(2*h)
   errs.append({'n':n,'tangent':g,'shift':ps,'finite_difference':fd,'shift_error':abs(g-ps),'fd_error':abs(g-fd)})
 return errs

def haar_checks():
 rng=np.random.default_rng(1803);M=400000;r=rng.normal(size=(M,3));r/=np.linalg.norm(r,axis=1)[:,None];s=rng.normal(size=(M,3));s/=np.linalg.norm(s,axis=1)[:,None]
 # Both sides independently Haar: g = (r cross s)_z for V=Z/2,H=X.
 gs=[r[:,1],s[:,1],np.cross(r,s)[:,2]];result=[]
 for name,g,exact,paper in zip(['minus_only','plus_only','both'],gs,[1/3,1/3,2/9],[.5,.25,.25]):
  v=np.var(g,ddof=1);se=np.sqrt((np.mean((g-g.mean())**4)-v*v)/M);result.append({'case':name,'samples':M,'mean':float(g.mean()),'variance':float(v),'variance_se':float(se),'exact':exact,'paper_v1':paper,'z_exact':float((v-exact)/se)})
 # Arbitrary 2x2 identity shifts: gradient zero for H=I, but source case 2 remains positive.
 th=.7;Had=(X+Z)/np.sqrt(2);U=expm(-1j*th*Z/2)@Had;A=U.conj().T@X@U;literal=float((1j*(Z/2@A-A@Z/2))[0,0].real);V=Had.conj().T@Z/2@Had;corr=float((1j*(V@A-A@V))[0,0].real)
 sqh=(I+Had)/2+1j*(I-Had)/2;ry=expm(-1j*np.pi/8*Y)
 result.append({'case':'factorization_W','theta':th,'actual':-np.sin(th),'printed_eq3':literal,'corrected_generator':corr})
 result.append({'case':'initial_gate_identity','matrix_frobenius_difference':float(np.linalg.norm(ry-sqh)),'state_fidelity':float(abs(np.vdot(ry[:,0],sqh[:,0]))**2),'sqrtH_square_error':float(np.linalg.norm(sqh@sqh-Had))})
 result.append({'case':'identity_H_shift','actual_variance':0,'printed_case2_H_identity':.25})
 return result

t=time.monotonic();out={'gradient':gradient_checks(),'haar':haar_checks(),'exact':[],'statevector':[]}
for n in [2,3,4,5,6]:
 out['exact'].append(exact_moment(n,[1,2,4,8,16,32,64,128,256,512]));print('exact',n,flush=True)
for n,M,Ls in [(2,50000,[1,2,8,32]),(4,20000,[1,2,8,32,64]),(6,5000,[1,2,8,32,64]),(8,2000,[1,2,8,32,64])]:
 out['statevector'].append(mc_states(n,M,Ls,seed=56123+n));print('statevector',n,flush=True)
out['wall_seconds']=time.monotonic()-t
Path('checks/validation.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'seconds':out['wall_seconds'],'max_shift_error':max(r['shift_error'] for r in out['gradient']),'haar':out['haar']},indent=2))
