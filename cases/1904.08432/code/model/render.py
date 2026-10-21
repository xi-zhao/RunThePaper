"""Render independently generated arrays without paper reference coordinates."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'calculation/report'
DATA=np.load(ROOT/'calculation/results/generation.npz')
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})
COLORS=['#3073bd','#cf3d42','#7469a8','#ab8d20']


def save(fig,name):
    fig.savefig(OUT/name,bbox_inches='tight',dpi=170);plt.close(fig)


def dots(ax,key):
    return  # Paper reference coordinates are not redistributed.


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    fig,ax=plt.subplots(figsize=(7,4.2),layout='constrained')
    for name,color in zip('ABCD',COLORS):
        key='fig2a_A_minimum_norm' if name=='A' else 'fig2a_'+name
        ax.loglog(DATA['fig2_time'],DATA[key],color=color,label=name);dots(ax,'F2a_'+name)
    ax.set(xlabel='Time t',ylabel='RMS cell-density deviation',ylim=(1e-8,1.2),xlim=(1,1000),title='Fig. 2(a) · independent numerical curves')
    ax.legend(title='A: dark-empty reference',fontsize=9);save(fig,'F2a.png')
    fig,axes=plt.subplots(2,2,figsize=(8,6),layout='constrained')
    for name,ax in zip('ABCD',axes.ravel()):
        p=DATA['fig2b_'+name+'_pbc'];o=DATA['fig2b_'+name+'_obc'];ax.scatter(p.real,p.imag,s=4,color='#3073bd',label='PBC');ax.scatter(o.real,o.imag,s=3,color='#cf3d42',label='OBC')
        ax.set(xlabel='Re eigenvalue',ylabel='Im eigenvalue',title=name);ax.legend(fontsize=8)
    fig.suptitle('Fig. 2(b) · independent finite spectra, 150 cells',fontsize=12);save(fig,'F2b.png')
    t=DATA['dynamic_time'];fig,axes=plt.subplots(2,1,figsize=(7,7.2),layout='constrained')
    axes[0].semilogy(t,DATA['periodic_minimum_norm_30'],color='#777',label='PBC L30, dark-empty (inferred)');dots(axes[0],'F3a_periodic')
    for length,color in zip([30,40,50,60],COLORS):
        axes[0].semilogy(t,np.sqrt(np.mean(DATA[f'open_{length}']**2,axis=1)),color=color,label='OBC L'+str(length));dots(axes[0],'F3a_open_'+str(length))
    axes[0].set(xlim=(0,80),ylim=(1e-14,2),ylabel='RMS deviation',title='Fig. 3(a)');axes[0].legend(fontsize=8)
    axes[1].semilogy(t,DATA['periodic_minimum_norm_60'],color='#777',label='PBC L60, dark-empty');dots(axes[1],'F3b_periodic')
    for site,color in zip([1,10,20,30],COLORS):
        axes[1].semilogy(t,DATA['open_60'][:,site-1],color=color,label='OBC x'+str(site));dots(axes[1],'F3b_x_'+str(site))
    axes[1].set(xlabel='Time t',ylabel='Local density deviation',xlim=(0,60),ylim=(1e-12,2),title='Fig. 3(b)');axes[1].legend(fontsize=8)
    fig.suptitle('Independently generated dynamics',fontsize=12);save(fig,'F3.png')
    fig,axes=plt.subplots(2,2,figsize=(9,6.4),layout='constrained')
    mask=t<=70
    periodic=np.repeat(DATA['periodic_minimum_norm_60'][mask,None],60,axis=1)
    for ax,values,title,maxtime in [(axes[0,0],periodic,'I · PBC, dark-empty reference',70),(axes[0,1],DATA['open_60'][mask],'I · OBC',70),
      (axes[1,0],DATA['control_periodic'],'II · PBC',20),(axes[1,1],DATA['control_open'],'II · OBC',20)]:
        image=ax.imshow(values,origin='lower',aspect='auto',extent=(.5,60.5,0,maxtime),cmap='magma',vmin=0,vmax=max(1.,float(values.max())))
        ax.set(xlabel='Cell x',ylabel='Time t',title=title);fig.colorbar(image,ax=ax,label='Density deviation',shrink=.8)
    fig.suptitle('Fig. 4 · independent dynamics (color style differs from source)',fontsize=12);save(fig,'F4.png')
    fig,axes=plt.subplots(1,2,figsize=(9,3.8),layout='constrained')
    for label,key in [('Dark-empty reference (+1/120)','periodic_minimum_norm_60'),('Half reference','periodic_60'),('Filled actual limit (-1/120)','periodic_actual_60')]:
        axes[0].plot(t,DATA[key],label=label)
    axes[0].set(xlabel='Time t',ylabel='Cell-density deviation',title='One evolution, three stationary references');axes[0].legend(fontsize=7)
    c=json.loads((ROOT/'calculation/checks/results.json').read_text())
    for name,row in c['thermodynamic_asymptotes'].items():
        axes[1].loglog(row['times'],row['density'],label=f"{name}: fit {row['fitted_exponent']:.4f}")
    axes[1].set(xlabel='Time t',ylabel='Infinite-grid density deviation',title='Finite-window approach to power laws');axes[1].legend(fontsize=8)
    save(fig,'conventions.png')
    print(json.dumps({'figures':len(list(OUT.glob('*.png'))),'data':'recorded generation/check results'}))


if __name__=='__main__':main()
