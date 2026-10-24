"""Independent Kane-Mele model from fixed v2 Eq.(1), Eq.(2), Table I.

Units a=t=1. Basis (A up,A down,B up,B down). q_j=k.a_j.
No original figure or reference data are read by this module.
"""
import numpy as np

I2=np.eye(2,dtype=complex)
sx=np.array([[0,1],[1,0]],complex)
sy=np.array([[0,-1j],[1j,0]],complex)
sz=np.diag([1.,-1.]).astype(complex)
G=[np.kron(sx,I2),np.kron(sz,I2),np.kron(sy,sx),np.kron(sy,sy),np.kron(sy,sz)]
Gab={(a+1,b+1):(G[a]@G[b]-G[b]@G[a])/(2j) for a in range(5) for b in range(a+1,5)}
J4=np.kron(I2,1j*sy)

def bulk(q1,q2,v=.1,r=.05,so=.06,t=1.):
    x=(q1-q2)/2; y=(q1+q2)/2
    cx,snx,cy,sny=np.cos(x),np.sin(x),np.cos(y),np.sin(y)
    return (t*(1+2*cx*cy)*G[0]+v*G[1]+r*(1-cx*cy)*G[2]
       -np.sqrt(3)*r*snx*sny*G[3]-2*t*cx*sny*Gab[1,2]
       +so*(2*np.sin(2*x)-4*snx*cy)*Gab[1,5]
       -r*cx*sny*Gab[2,3]+np.sqrt(3)*r*snx*cy*Gab[2,4])

def hoppings(v=.1,r=.05,so=.06,t=1.):
    """H_ab(R) multiplies exp(+i k.R); each directed hopping returned once.
    NN from actual bond directions; SO Fourier coefficients checked separately.
    """
    h=[]
    for n1,n2,d in [(0,0,(0.,1.)),(-1,0,(-np.sqrt(3)/2,-.5)),(0,-1,(np.sqrt(3)/2,-.5))]:
        block=t*I2+1j*r*(-d[1]*sx+d[0]*sy)
        h.append((0,1,n1,n2,block))
        h.append((1,0,-n1,-n2,block.conj().T))
    for a in range(2):
        h.append((a,a,0,0,((-1)**a)*v*I2))
        for n1,n2,c in [(1,-1,-1j),(1,0,1j),(0,1,-1j)]:
            block=((-1)**a)*so*c*sz
            h.append((a,a,n1,n2,block))
            h.append((a,a,-n1,-n2,block.conj().T))
    return h

def bulk_from_bonds(q1,q2,**pars):
    H=np.zeros((4,4),complex)
    for a,b,n1,n2,h in hoppings(**pars):
        H[2*a:2*a+2,2*b:2*b+2]+=h*np.exp(1j*(q1*n1+q2*n2))
    return H

def ribbon(k,n=20,**pars):
    """Zigzag strip, 2n sites. A row j at j*a1; B row j at (j-1)*a1+d.
    The edge sites have degree two, rather than the bearded degree-one edge.
    """
    H=np.zeros((4*n,4*n),complex)
    for row in range(n):
        for a,b,n1,n2,h in hoppings(**pars):
            dest=row+n1+n2+b-a
            if 0<=dest<n:
                i=4*row+2*a; j=4*dest+2*b
                H[i:i+2,j:j+2]+=h*np.exp(-1j*k*n2)
    return H

def supercell(alpha1,alpha2,n1=2,n2=2,**pars):
    """Seam-twist gauge, L1=N1(a1+a2), L2=N2(a1-a2), Na=4N1N2.
    Primitive R has p=m1+m2, q=m1-m2, equal parity. Twists only on seams.
    """
    cells=[(p,q) for p in range(2*n1) for q in range(2*n2) if (p-q)%2==0]
    lookup={c:i for i,c in enumerate(cells)}
    H=np.zeros((4*len(cells),4*len(cells)),complex)
    for cell,(p,q) in enumerate(cells):
        for a,b,d1,d2,h in hoppings(**pars):
            pp,qq=p+d1+d2,q+d1-d2
            w1,pp=divmod(pp,2*n1);w2,qq=divmod(qq,2*n2)
            i=4*cell+2*a;j=4*lookup[pp,qq]+2*b
            H[i:i+2,j:j+2]+=h*np.exp(1j*(w1*alpha1+w2*alpha2))
    return H

def pfaffian(A):
    """Pivoted skew Gaussian elimination; O(n^3), no determinant square root."""
    A=np.array(A,dtype=complex,copy=True);n=len(A);out=1.+0j
    if n%2: return 0j
    for k in range(0,n-1,2):
        p=k+1+int(np.argmax(np.abs(A[k,k+1:])))
        if abs(A[k,p])<1e-30: return 0j
        if p!=k+1:
            A[[k+1,p],:]=A[[p,k+1],:]
            A[:,[k+1,p]]=A[:,[p,k+1]]
            out=-out
        a=A[k,k+1];out*=a
        if k+2<n:
            u=A[k,k+2:].copy();v=A[k+1,k+2:].copy()
            A[k+2:,k+2:]+=(np.outer(v,u)-np.outer(u,v))/a
    return out

def occupied(H):
    e,u=np.linalg.eigh(H)
    return e,u[:,:len(e)//2]

def overlap(U):
    J=np.kron(np.eye(U.shape[0]//2),1j*sy)
    return U.conj().T@J@U.conj()

def pf(H):
    return pfaffian(overlap(occupied(H)[1]))

def frame_pf(H,Uref):
    U=occupied(H)[1]
    a,s,b=np.linalg.svd(U.conj().T@Uref)
    U=U@(a@b)
    return pfaffian(overlap(U)),s.min()

def spin_chern(v,so=.06,ngrid=41):
    """Fukui lattice flux for the Sz-conserving limit, spin up/down separately."""
    ans=[]
    for spin in [0,1]:
        vec=np.zeros((ngrid,ngrid,2),complex)
        for i in range(ngrid):
            for j in range(ngrid):
                h=bulk(2*np.pi*i/ngrid,2*np.pi*j/ngrid,v=v,r=0,so=so)
                _,u=np.linalg.eigh(h[np.ix_([spin,spin+2],[spin,spin+2])]);vec[i,j]=u[:,0]
        ux=np.sum(vec.conj()*np.roll(vec,-1,axis=0),axis=2)
        uy=np.sum(vec.conj()*np.roll(vec,-1,axis=1),axis=2)
        ux/=abs(ux);uy/=abs(uy)
        flux=np.angle(ux*np.roll(uy,-1,axis=0)*np.roll(ux,-1,axis=1).conj()*uy.conj())
        ans.append(float(flux.sum()/(2*np.pi)))
    return ans
