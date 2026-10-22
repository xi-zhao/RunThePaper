"""Direct Fock-basis master equation. Three-mode density blocks use exact U(1) symmetry."""
import itertools
import numpy as np
from scipy.sparse import coo_matrix,diags,csr_matrix
from scipy.sparse.linalg import spsolve,expm_multiply
from scipy.optimize import brentq

class Model:
    def __init__(self,modes,cut,E,F,Gamma,alpha=.012,J=.5,dephasing=0.,cross_factor=4.):
        self.modes=modes;self.cut=cut;self.Gamma=Gamma
        self.basis=np.array([b for b in itertools.product(range(cut+1),repeat=modes) if sum(b)<=cut])
        lookup={tuple(b):i for i,b in enumerate(self.basis)};self.d=len(self.basis)
        self.a=[]
        for mode in range(modes):
            rows=[];cols=[];vals=[]
            for i,b in enumerate(self.basis):
                if b[mode]:
                    c=b.copy();c[mode]-=1;rows.append(lookup[tuple(c)]);cols.append(i);vals.append(np.sqrt(b[mode]))
            self.a.append(coo_matrix((vals,(rows,cols)),shape=(self.d,self.d)).tocsr())
        n=self.basis;energy=n@np.array(E)+alpha*np.sum(n*(n-1),axis=1)
        if modes==3:energy+=cross_factor*alpha*(n[:,0]*n[:,1]+n[:,0]*n[:,2]+n[:,1]*n[:,2])
        H=diags(energy,dtype=complex)
        if modes==2:H-=J*(self.a[0].T@self.a[1]+self.a[1].T@self.a[0]);pump=0
        elif modes==3:
            pair=self.a[0].T@self.a[2].T@self.a[1]@self.a[1];H+=2*alpha*(pair+pair.T);pump=1
        else:pump=0
        H+=F*self.a[pump].T+np.conj(F)*self.a[pump];self.H=H.tocsr()
        charge=n[:,0]-n[:,2] if modes==3 else np.zeros(self.d,int)
        ii,jj=np.where(charge[:,None]==charge[None,:]);self.ii=ii;self.jj=jj
        self.lookup=np.full((self.d,self.d),-1,int);self.lookup[ii,jj]=np.arange(len(ii));K=len(ii)
        rows=[];cols=[];values=[];column=np.arange(K)
        # Column-major element labels are explicit; no silent transpose convention.
        Hc=self.H.tocsc();Hr=self.H.tocsr()
        for col,(i,j) in enumerate(zip(ii,jj)):
            for ptr in range(Hc.indptr[i],Hc.indptr[i+1]):
                k=Hc.indices[ptr];row=self.lookup[k,j]
                if row>=0:rows.append(row);cols.append(col);values.append(-1j*Hc.data[ptr])
            for ptr in range(Hr.indptr[j],Hr.indptr[j+1]):
                k=Hr.indices[ptr];row=self.lookup[i,k]
                if row>=0:rows.append(row);cols.append(col);values.append(1j*Hr.data[ptr])
        L=coo_matrix((values,(rows,cols)),shape=(K,K)).tocsr()
        L+=diags(-Gamma/2*(n[ii].sum(axis=1)+n[jj].sum(axis=1))
                 -dephasing/2*np.sum((n[ii]-n[jj])**2,axis=1))
        for mode,a in enumerate(self.a):
            ac=a.tocsc();target=np.full(self.d,-1);strength=np.zeros(self.d)
            for i in range(self.d):
                if ac.indptr[i]<ac.indptr[i+1]:target[i]=ac.indices[ac.indptr[i]];strength[i]=ac.data[ac.indptr[i]]
            valid=(target[ii]>=0)&(target[jj]>=0)
            rr=self.lookup[target[ii[valid]],target[jj[valid]]]
            L+=coo_matrix((Gamma*strength[ii[valid]]*strength[jj[valid]],(rr,column[valid])),shape=(K,K)).tocsr()
        self.L=L;self.diag=self.lookup[np.arange(self.d),np.arange(self.d)]
        self.trace_row=np.zeros(K);self.trace_row[self.diag]=1

    def steady(self,method='direct'):
        if method=='propagate':
            rho=np.zeros(len(self.ii),complex);rho[self.lookup[0,0]]=1
            for iteration in range(30):
                previous=rho
                rho=expm_multiply(self.L*(20/self.Gamma),rho)
                if np.max(abs(rho-previous))<2e-12 and np.max(abs(self.L@rho))<2e-12:break
            else:raise ValueError('vacuum-to-stationary propagation not converged')
        else:
            M=self.L.tolil();M[0,:]=self.trace_row;rhs=np.zeros(len(self.ii),complex);rhs[0]=1
            rho=spsolve(M.tocsc(),rhs)
        pop=rho[self.diag].real
        self.rho=rho;self.pop=pop
        mean=pop@self.basis;mom=pop@(self.basis*(self.basis-1))
        residual=float(np.linalg.norm(self.L@rho,np.inf));hermitian=float(np.max(abs(rho-rho[self.lookup[self.jj,self.ii]].conj())))
        if residual>1e-9 or min(pop)<-1e-10 or hermitian>1e-9:raise ValueError(('bad steady state',residual,min(pop),hermitian))
        return {'n':mean,'g2':mom/np.maximum(mean**2,1e-30),'residual':residual,
                'top_probability':float(pop[self.basis.sum(axis=1)==self.cut].sum()),'prob_more_than_one_mode1':float(pop[self.basis[:,0]>1].sum())}
    def matrix(self,v):
        a=np.zeros((self.d,self.d),complex);a[self.ii,self.jj]=v;return a
    def vector(self,a):return a[self.ii,self.jj]
    def correlations(self,trigger,observed,times_ps):
        a=self.a[trigger];condition=self.vector(a@self.matrix(self.rho)@a.T)
        physical=times_ps/.6582119569
        values=expm_multiply(self.L,condition,start=0,stop=float(physical[-1]),num=len(physical))
        return (values[:,self.diag].real@self.basis[:,observed])/(self.pop@self.basis[:,trigger])/(self.pop@self.basis[:,observed])

def gaussian(n1,J=.5,E1=.07,E2=.05,Gamma=.2,alpha=.012):
    b1=np.sqrt(n1)
    if J:
        n2=brentq(lambda n:n*((E2+2*alpha*n)**2+(Gamma/2)**2)-J*J*n1,0,max(1,100*n1))
        b2=J*b1/(E2+2*alpha*n2-1j*Gamma/2);beta=np.array([b1,b2]);A=np.array([[E1+4*alpha*n1,-J],[-J,E2+4*alpha*n2]])
    else:beta=np.array([b1]);A=np.array([[E1+4*alpha*n1]])
    n=len(beta);B=np.diag(2*alpha*beta**2)
    M=np.block([[-1j*A-Gamma/2*np.eye(n),-1j*B],[1j*B.conj(),1j*A-Gamma/2*np.eye(n)]])
    D=np.zeros((2*n,2*n));D[:n,n:]=Gamma*np.eye(n)
    C=np.linalg.solve(np.kron(np.eye(2*n),M)+np.kron(M,np.eye(2*n)),-D.ravel(order='F')).reshape(2*n,2*n,order='F')
    g2=1+2*C[n,0].real/n1+2*C[0,0].real/n1
    return float(g2),float(np.max(np.linalg.eigvals(M).real))
