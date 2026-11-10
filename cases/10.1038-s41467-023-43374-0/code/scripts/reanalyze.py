"""Independent fitting of published processed data; NOT independent experimental generation."""
import os
os.environ.setdefault('MPLCONFIGDIR', '/tmp/qctrl-mpl-20261109')
import json, zipfile, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares, minimize_scalar
from scipy import odr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def sheets(path):
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as z:
        strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
        result=[]
        for i in range(1,4):
            cells={}
            for c in ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml')).findall('.//m:c',ns):
                v=c.find('m:v',ns)
                if v is not None: cells[c.attrib['r']]=strings[int(v.text)] if c.get('t')=='s' else float(v.text)
            result.append(cells)
    return result

def block(cells,start,cols):
    out=[];r=start
    while isinstance(cells.get('A'+str(r)),float):
        out.append([cells[c+str(r)] for c in cols]);r+=1
    return np.array(out)

def fixed_fit(x,y):
    X=np.column_stack([np.ones(len(x)),np.cos(3*x),np.sin(3*x)])
    b=np.linalg.lstsq(X,y,rcond=None)[0];res=y-X@b
    cov=np.linalg.inv(X.T@X)*(res@res)/(len(x)-3)
    amp=np.hypot(b[1],b[2]);phase=np.arctan2(b[2],-b[1])
    jac=np.array([0,b[2],-b[1]])/amp**2
    sig=np.sqrt(jac@cov@jac)
    # Different parameterization and nonlinear solver to detect phase/covariance errors.
    fun=lambda q:q[0]-q[1]*np.cos(3*x+q[2])-y
    fit=least_squares(fun,[b[0],amp,phase],xtol=1e-13,ftol=1e-13,gtol=1e-13)
    cov2=np.linalg.inv(fit.jac.T@fit.jac)*(fit.fun@fit.fun)/(len(x)-3)
    return dict(n=len(x),phase=phase,stderr=sig,amplitude=amp,offset=b[0],single_shot=sig*np.sqrt(len(x)),
                nonlinear_phase_delta=fit.x[2]-phase,nonlinear_stderr_delta=np.sqrt(cov2[2,2])-sig), b

def main():
    import sys
    src=Path(sys.argv[1]) if len(sys.argv)>1 else Path('source/source_data.xlsx')
    out=Path('results');out.mkdir(exist_ok=True)
    s2,s3,s4=sheets(src);report={'provenance':'Independent reanalysis of author processed XLSX, not new observations','fig2':[],'fig3':[],'fig4':[]}
    plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
    fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
    starts=[5,508,1011,1514,2017,2520]
    report['fig2_duplicate_blocks']=[dict(robust_start=a,gaussian_start=b,exact_equal=bool(np.array_equal(block(s2,a,'ABC'),block(s2,b,'ABC')))) for a,b in zip(starts[:3],starts[3:])]
    for i,start in enumerate(starts):
        a=block(s2,start,'ABC');x=a[:,0];y=a[:,2];T=[5,7.5,10][i%3];kind='robust' if i<3 else 'Gaussian'
        k=np.pi*np.mean(a[:,1]*1e6/x);S=6*k*(T/1000)**2
        x0=9.79674;u=(x-x0)*S
        def linear(q):
            X=np.column_stack([np.ones(len(x)),u,np.cos(q*u),np.sin(q*u)])
            b=np.linalg.lstsq(X,y,rcond=None)[0]
            return X,b,y-np.einsum('ij,j->i',X,b)
        scan=np.linspace(.95,1.05,101);best=min(scan,key=lambda q:np.sum(linear(q)[2]**2))
        opt=minimize_scalar(lambda q:np.sum(linear(q)[2]**2),bounds=(best-.002,best+.002),method='bounded',options={'xatol':1e-14})
        q=opt.x;X,b,res=linear(q);phase=np.arctan2(b[3],-b[2]);center=x0-phase/(q*S)
        J=np.column_stack([X,u*(-b[2]*np.sin(q*u)+b[3]*np.cos(q*u))])
        cov=np.linalg.inv(J.T@J)*(res@res)/(len(x)-5)
        grad=np.array([0,0,b[3],-b[2],0])/(b[2]**2+b[3]**2)
        gc=-grad/(q*S);gc[4]=phase/(q*q*S)
        refrow=(3023 if i<3 else 3028)+i%3
        item=dict(kind=kind,T_ms=T,n=len(x),scale=q*S,scale_se=np.sqrt(cov[4,4])*S,relative_scale_error=q-1,
                  reference_scale=s2['B'+str(refrow)],center=center,center_se=np.sqrt(gc@cov@gc),
                  amplitude=np.hypot(b[2],b[3]),trend_per_accel=b[1]*S,k_from_chirp=k,rms=np.sqrt(np.mean(res**2)))
        report['fig2'].append(item)
        ax=axs[0,0 if i<3 else 1];ax.plot((x-x0)*1e3,y,'.',ms=1.5,alpha=.5);ax.plot((x-x0)*1e3,np.einsum('ij,j->i',X,b),label=f'{T} ms')
        axs[1,0].errorbar(T+(0.05 if i<3 else -.05),100*(q-1),yerr=100*np.sqrt(cov[4,4]),fmt='o',color='purple' if i<3 else 'gray')
        axs[1,1].plot((x-x0)*1e3,res,'.',ms=1,label=f'{kind} {T} ms')
    for ax,kind in zip(axs[0],['Robust','Labeled Gaussian: duplicated source rows']):ax.set(title=kind,xlabel='g - 9.79674 (mm/s²)',ylabel='Population');ax.legend()
    axs[1,0].set(xlabel='T (ms)',ylabel='Scale deviation from 6kT² (%)');axs[1,0].axhline(0,c='k',lw=.5)
    axs[1,1].set(xlabel='g - 9.79674 (mm/s²)',ylabel='Fit residual');fig.suptitle('Figure 2: independent fits to published processed data');fig.savefig(out/'figure2.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(12,5),layout='constrained')
    for i,start in enumerate([5,80,155,230,305,381,456,531,606,681]):
        a=block(s3,start,'AB');r,b=fixed_fit(a[:,0],a[:,1]);noise=[0,5,10,15,20][i%5];kind='Gaussian' if i<5 else 'robust'
        refrow=(757 if i<5 else 765)+i%5
        r.update(kind=kind,noise_percent=noise,reference_phase=s3['B'+str(refrow)],reference_stderr=s3['C'+str(refrow)])
        report['fig3'].append(r);ax=axs[0 if i<5 else 1];xx=np.linspace(0,2*np.pi,700)
        ax.plot(a[:,0],a[:,1]+.2*(i%5),'.',ms=2);ax.plot(xx,b[0]+b[1]*np.cos(3*xx)+b[2]*np.sin(3*xx)+.2*(i%5),label=f'{noise}%')
        axs[2].errorbar(r['phase'],noise+(0.3 if i<5 else -.3),xerr=r['stderr'],fmt='o',c='gray' if i<5 else 'purple')
    for ax,kind in zip(axs[:2],['Gaussian','Robust']):ax.set(title=kind,xlabel='Laser phase (rad)',ylabel='Population + offset');ax.legend()
    axs[2].set(xlabel='Fitted interferometer phase (rad)',ylabel='Intensity noise (%)');axs[2].axvline(0,c='k',ls=':');fig.suptitle('Figure 3: independent fixed-period fits');fig.savefig(out/'figure3.png',dpi=160);plt.close(fig)
    fig,axs=plt.subplots(1,2,figsize=(11,5),layout='constrained');arrays={}
    for start in [5,17,29,41,53,65,77,89]:
        a=block(s4,start,'ABCD');label=s4['A'+str(start-3)];expected=s4['B'+str(start-2)];x,sx,y,sy=a.T
        X=np.column_stack([x,np.ones(len(x))]);W=X/sy[:,None];b=np.linalg.lstsq(W,y/sy,rcond=None)[0];cov=np.linalg.inv(W.T@W)
        ols=np.linalg.lstsq(X,y,rcond=None)[0]
        orth=odr.ODR(odr.RealData(x,y,sx=sx,sy=sy),odr.Model(lambda b,x:b[0]*x+b[1]),beta0=b).run()
        T=5 if 'T=5.0' in label else 10;kind='robust' if 'error-robust' in label else 'Gaussian';noise=20 if '20.0%' in label else 0
        arrays[(kind,T,noise)]=a[np.argsort(x)]
        report['fig4'].append(dict(label=label,T_ms=T,kind=kind,noise_percent=noise,n=len(x),expected_slope=expected,
                 weighted_slope=b[0],weighted_slope_se=np.sqrt(cov[0,0]),ols_slope=ols[0],odr_slope=orth.beta[0],odr_se=orth.sd_beta[0],phase_se_range=[min(sy),max(sy)],relative_scale_error=b[0]/expected-1))
        ax=axs[0 if kind=='Gaussian' else 1];ax.errorbar(x,y,xerr=sx,yerr=sy,fmt='o',ms=3,label=f'{T} ms, {noise}%');xx=np.array([-105,105]);ax.plot(xx,expected*xx,':',c='k',lw=.7)
    ratios=[]
    for T in [5,10]:
        for noise in [0,20]:
            g=arrays['Gaussian',T,noise];r=arrays['robust',T,noise];v=g[:,3]/r[:,3]
            ratios.append(dict(T_ms=T,noise_percent=noise,mean=float(np.mean(v)),max=float(max(v)),min=float(min(v)),max_pair_accel_difference=float(max(abs(g[:,0]-r[:,0])))))
    report['fig4_precision_ratios']=ratios
    report['fig3_precision_ratios']=[report['fig3'][i]['stderr']/report['fig3'][i+5]['stderr'] for i in range(5)]
    for ax,kind in zip(axs,['Gaussian','Robust']):ax.set(title=kind,xlabel='Applied acceleration (µg)',ylabel='Interferometer phase (rad)');ax.legend()
    fig.suptitle('Figure 4: published phases and independent regression');fig.savefig(out/'figure4.png',dpi=160);plt.close(fig)
    (out/'reanalysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
