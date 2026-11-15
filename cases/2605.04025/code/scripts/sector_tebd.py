"""Number-resolved Schmidt truncation for the two spin species."""
import numpy as np
from scipy.linalg import qr,svd

from tebd import Chain


def matching(rows,cols):
    for q in np.intersect1d(rows,cols):
        yield int(q),np.flatnonzero(rows==q),np.flatnonzero(cols==q)


def blocked_qr(a,rows,cols):
    blocks=[]
    for charge,i,j in matching(rows,cols):
        q,r=qr(a[np.ix_(i,j)],mode="economic",check_finite=False)
        blocks.append((charge,i,j,q,r))
    labels=np.concatenate([np.full(len(r),charge,int) for charge,_,_,_,r in blocks])
    q=np.zeros((len(rows),len(labels)),complex)
    r=np.zeros((len(labels),len(cols)),complex)
    offset=0
    for _,i,j,qb,rb in blocks:
        k=np.arange(offset,offset+len(rb))
        q[np.ix_(i,k)]=qb
        r[np.ix_(k,j)]=rb
        offset+=len(rb)
    return q,r,labels


class SectorChain(Chain):
    def __init__(self,bits,chi,cutoff):
        super().__init__(bits,chi,cutoff)
        base=len(bits)+1
        self.weights=np.tile(np.array([base,1,1,base]),len(bits)//4+1)[:len(bits)].copy()
        self.charges=[np.array([v]) for v in np.r_[0,np.cumsum(bits*self.weights)]]
        self.fallbacks=0

    def layer(self,bonds,g):
        a=self.a
        forward=self.direction==1
        exchange=0 in bonds
        for i in (range(len(a)-1) if forward else reversed(range(len(a)-1))):
            dl,_,mid=a[i].shape
            dr=a[i+1].shape[2]
            ql, qm, qr=self.charges[i:i+3]
            if i in bonds:
                theta=(a[i].reshape(2*dl,mid)@a[i+1].reshape(mid,2*dr)).reshape(dl,4,dr)
                theta=(g@theta).reshape(2*dl,2*dr)
                if exchange:
                    self.weights[i],self.weights[i+1]=self.weights[i+1],self.weights[i]
                rows=(ql[:,None]+np.array([0,self.weights[i]])).ravel()
                cols=(qr[None,:]-np.array([0,self.weights[i+1]])[:,None]).ravel()
                parts=[]
                for charge,ix,jx in matching(rows,cols):
                    block=theta[np.ix_(ix,jx)]
                    try:
                        u,s,v=svd(block,full_matrices=False,check_finite=False,lapack_driver="gesdd")
                    except np.linalg.LinAlgError:
                        self.fallbacks+=1
                        u,s,v=svd(block,full_matrices=False,check_finite=True,lapack_driver="gesvd")
                    parts.append((charge,ix,jx,u,s,v))
                values=np.concatenate([p[4] for p in parts])
                top=np.argsort(-values,kind="stable")[:self.chi]
                top=top[values[top]>self.cutoff]
                if len(top)==0:
                    raise ValueError("empty bond after truncation")
                retained=np.zeros(len(values),bool)
                retained[top]=True
                normalization=np.linalg.norm(values[top])
                self.loss+=float(values[~retained]@values[~retained])
                self.max_rank=max(self.max_rank,len(top))
                uout=np.zeros((2*dl,len(top)),complex)
                vout=np.zeros((len(top),2*dr),complex)
                labels=[]
                offset=0
                start=0
                for charge,ix,jx,u,s,v in parts:
                    keep=np.flatnonzero(retained[offset:offset+len(s)])
                    k=np.arange(start,start+len(keep))
                    weight=s[keep]/normalization
                    uout[np.ix_(ix,k)]=u[:,keep] if forward else u[:,keep]*weight
                    vout[np.ix_(k,jx)]=weight[:,None]*v[keep] if forward else v[keep]
                    labels.extend([charge]*len(keep))
                    offset+=len(s)
                    start+=len(keep)
                a[i]=uout.reshape(dl,2,len(top))
                a[i+1]=vout.reshape(len(top),2,dr)
                self.charges[i+1]=np.array(labels)
            elif forward:
                rows=(ql[:,None]+np.array([0,self.weights[i]])).ravel()
                q,r,labels=blocked_qr(a[i].reshape(2*dl,mid),rows,qm)
                a[i]=q.reshape(dl,2,len(labels))
                a[i+1]=(r@a[i+1].reshape(mid,2*dr)).reshape(len(labels),2,dr)
                self.charges[i+1]=labels
            else:
                cols=(qr[None,:]-np.array([0,self.weights[i+1]])[:,None]).ravel()
                q,r,labels=blocked_qr(a[i+1].reshape(mid,2*dr).T,cols,qm)
                a[i+1]=q.T.reshape(len(labels),2,dr)
                a[i]=(a[i].reshape(2*dl,mid)@r.T).reshape(dl,2,len(labels))
                self.charges[i+1]=labels
        self.direction=-self.direction
