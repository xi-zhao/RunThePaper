"""Render only the frozen independently generated arrays; no reference input."""
import os
from pathlib import Path
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'config/matplotlib-cache')
os.environ['OPENBLAS_NUM_THREADS']='1'
import json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':True,
                     'axes.spines.right':True,'figure.dpi':140,'savefig.dpi':180})
z=np.load('results/independent.npz');v=json.load(open('results/independent.json'))
out=Path('figures');out.mkdir(exist_ok=True)
colors=['#219653','#f2994a','#eb5757','#9b51e0','#2f80ed','#1d3557','#6c757d','#b5838d','#222222']
def save(fig,name):
    fig.savefig(out/(name+'.png'),bbox_inches='tight')
    fig.savefig(out/(name+'.pdf'),bbox_inches='tight')
    plt.close(fig)

fig,ax=plt.subplots(figsize=(9.8,6.5))
for i,n in enumerate([11,41,101,251,401]):
    ax.plot(z['fig1_lambda'],z[f'fig1_N{n}'][:,1],color=colors[i],lw=1.7,label=f'N={n}')
x=z['fig1_infinite_lambda'];y=z['fig1_infinite'][:,1]
for mask in [x<1,x>1]:ax.plot(x[mask],y[mask],color='black',lw=1.6,label='infinite' if mask[0] else None)
ax.set(xlim=(.7,1.3),ylim=(-1.65,.2),xlabel=r'$\lambda$',ylabel=r'$\partial_\lambda C(1)$',title='Figure 1 · Ising nearest-neighbour concurrence')
ax.legend(loc='upper right',ncol=2,fontsize=8,frameon=False)
ins=ax.inset_axes([.11,.12,.29,.30]);mi=np.array(v['minima_C1']);sel=mi[:,0]<=2701
ins.plot(np.log(mi[sel,0]),np.log(mi[sel,1]-1),'o-',ms=3,color='#2f80ed')
ins.set(xlabel=r'$\ln N$',ylabel=r'$\ln(\lambda_m-1)$');ins.tick_params(labelsize=7);ins.xaxis.label.set_size(8);ins.yaxis.label.set_size(8)
ins=ax.inset_axes([.63,.13,.30,.29]);ins.plot(z['inset_lambda'],z['inset_C1'],'k-',lw=1.3)
ins.set(xlabel=r'$\lambda$',ylabel=r'$C(1)$',xlim=(0,2),ylim=(0,.28));ins.tick_params(labelsize=7);ins.xaxis.label.set_size(8);ins.yaxis.label.set_size(8)
save(fig,'figure1')

for name,nums,title,ylabel,ylim in [
    ('fig2',[41,101,251,401,701,1001,1501,2001,2701],'Figure 2 · Ising finite-size scaling',r'$10^4\{1-\exp[C_1^\prime(\lambda)-C_1^\prime(\lambda_m)]\}$',(-37,2)),
    ('fig3',[41,101,251,401],'Figure 3 · Next-nearest-neighbour scaling',r'$10^4[C_2^{\prime\prime}(\lambda)-C_2^{\prime\prime}(\lambda_m)]$',(-5,200)),
    ('fig4',[41,101,251,401],r'Figure 4 · Universality at $\gamma=0.5$',r'$1-\exp[C_1^\prime(\lambda)-C_1^\prime(\lambda_m)]$',(-.04,.002))]:
    fig,ax=plt.subplots(figsize=(9.8,6.5))
    for i,n in enumerate(nums):ax.plot(z['collapse_x'],z[f'{name}_N{n}'],lw=1.4,color=colors[i],label=f'N={n}',marker=['o','s','^','d'][i%4],markevery=10,ms=3,mfc='none')
    ax.set(xlim=(-.2,.2),ylim=ylim,xlabel=r'$N(\lambda-\lambda_m)$',ylabel=ylabel,title=title)
    if name=='fig2':
        ax.legend(loc='lower left',ncol=3,fontsize=7,frameon=False)
        ins=ax.inset_axes([.34,.18,.35,.31]);sel=mi[:,0]<=2701;ins.plot(np.log(mi[sel,0]),mi[sel,3],'o-',ms=3,color='#2f80ed')
        ins.set(xlabel=r'$\ln N$',ylabel=r'$C_1^\prime(\lambda_m)$')
    elif name=='fig3':
        ax.legend(loc='upper right',fontsize=8,frameon=False)
        ins=ax.inset_axes([.17,.53,.40,.40])
        for i,n in enumerate([11,41,101,251,401,None]):ins.plot(z['inset_C2_lambda'],z[f'inset_C2_N{n}'],lw=1.1,color=colors[i] if n else 'black',label=f'N={n}' if n else 'infinite')
        ins.set(xlabel=r'$\lambda$',ylabel=r'$C(2)$',xlim=(.5,1.5),ylim=(0,.0145))
        ins.legend(fontsize=5.5,ncol=2,loc='upper right',frameon=False)
    else:
        ax.legend(loc='upper left',fontsize=8,frameon=False)
        ins=ax.inset_axes([.35,.16,.34,.32]);xx=z['fig4_infinite_lambda'];yy=z['fig4_infinite'][:,1]
        for mask in [xx<1,xx>1]:ins.plot(xx[mask]-1,yy[mask],color='#eb5757',lw=1.2)
        ins.set(xlabel=r'$\lambda-1$',ylabel=r'$C_1^\prime$',xlim=(-.2,.1),ylim=(-2,.5))
    ins.tick_params(labelsize=7);ins.xaxis.label.set_size(8);ins.yaxis.label.set_size(8)
    save(fig,'figure'+name[-1])

fig,axs=plt.subplots(1,2,figsize=(11,4.3))
g=v['gamma_critical']+json.load(open('checks/limits.json'))['small_gamma']
gg=np.array([r['gamma'] for r in g]);rr=np.array([r['xi_E'] for r in g]);ss=np.array([r['sum_C'] for r in g])
axs[0].loglog(gg,rr,'o-',label='computed integer range');axs[0].loglog(gg,1.15/gg,'--',label=r'$1.15/\gamma$ (asymptotic guide)')
axs[0].set(xlabel=r'$\gamma$',ylabel=r'$\xi_E$',title=r'Critical pairwise-entanglement range');axs[0].legend(fontsize=8)
axs[1].semilogx(gg,ss,'o-');axs[1].axhline(.2,ls='--',color='gray');axs[1].set(xlabel=r'$\gamma$',ylabel=r'$\sum_{r\geq1} C(r)$',title=r'At $\lambda=1$, infinite chain',ylim=(.15,.205))
fig.tight_layout();save(fig,'range_check')
Path('checks/render-provenance.json').write_text(json.dumps({'rendering_only':True,'frozen_data_sha256':hashlib.sha256(Path('results/independent.npz').read_bytes()).hexdigest(),'data_editing':False,'original_pixels_used':False,'files':[str(p) for p in sorted(out.glob('*'))]},indent=2))
print('Rendered four reproduced figures and a supplementary range check, PNG+PDF.')
