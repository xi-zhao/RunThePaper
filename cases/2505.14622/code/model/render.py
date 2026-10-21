"""Presentation only: all plotted numerical values come from recorded arrays/checks."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'calculation/report'
DATA=np.load(ROOT/'calculation/results/generation.npz')
GEN=json.loads((ROOT/'calculation/results/generation.json').read_text())
CHECK=json.loads((ROOT/'calculation/checks/results.json').read_text())
plt.rcParams.update({'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':150})


def save(fig,name):
    fig.savefig(OUT/name,bbox_inches='tight',dpi=170)
    plt.close(fig)


def fields(group,figure,unit='trace'):
    fig,axes=plt.subplots(1,2,figsize=(9,4.4),layout='constrained')
    key='stationary_constrained_'+group
    scale=.5 if unit=='trace' else 1.
    all_speed=np.concatenate([np.linalg.norm(DATA[key+'_'+label+'_velocity'],axis=-1).ravel() for label in ['final','auxiliary']])*scale
    for ax,label in zip(axes,['final','auxiliary']):
        x=DATA['field_x'];y=DATA['field_y'];v=DATA[key+'_'+label+'_velocity'];speed=scale*np.linalg.norm(v,axis=-1)
        speed=np.where(DATA['field_mask'],speed,np.nan)
        image=ax.pcolormesh(x,y,speed,cmap='rainbow_r',alpha=.6,vmin=all_speed.min(),vmax=all_speed.max(),shading='auto',rasterized=True)
        st=slice(None,None,3);mask=DATA['field_mask'][st,st]
        norm=np.linalg.norm(v[st,st,:2],axis=-1);u=np.where(mask,v[st,st,0]/np.maximum(norm,1e-15),np.nan);w=np.where(mask,v[st,st,1]/np.maximum(norm,1e-15),np.nan)
        ax.quiver(x[st,st],y[st,st],u,w,color='#222',scale=32,width=.003)
        path=DATA[key+'_'+label];ax.plot(path[:,0],path[:,1],color='#2668d5' if label=='final' else '#157347',lw=2)
        for p in GEN['variants']['stationary_constrained'][group]['protocols'][:1]:
            if label=='final':
                path=DATA[p['array_key']];ts=DATA['time']>=p['switch'];ax.plot(path[ts,0],path[ts,1],color='#e39800',lw=2)
        angle=np.linspace(0,2*np.pi,300);ax.plot(np.cos(angle),np.sin(angle),color='#555',lw=1)
        ax.set(xlim=(-1,1),ylim=(-1,1),aspect='equal',xlabel='$r_1$',ylabel='$r_2$',title=f'{figure} — {label} bath')
        fig.colorbar(image,ax=ax,label='Trace-distance speed $|dr/dt|/2$' if unit=='trace' else 'Bloch speed $|dr/dt|$',shrink=.75)
    fig.suptitle('Independent calculation · stationary-constrained parameters',fontsize=12)
    save(fig,figure+('' if unit=='trace' else '-bloch')+'.png')


def traces(variant):
    fig,axes=plt.subplots(3,1,figsize=(7,8),sharex=True,layout='constrained')
    for group,ax in zip(['a','b','c'],axes):
        key=variant+'_'+group;t=DATA['time'];g=GEN['variants'][variant][group]
        ax.plot(t,DATA[key+'_distance_final'],color='#2668d5',label='Direct F')
        ax.plot(t,DATA[key+'_distance_auxiliary'],color='#157347',label='Auxiliary A')
        for p in g['protocols']:
            mask=t>=p['switch'];v=np.linalg.norm(DATA[p['array_key']]-g['final_stationary'],axis=1)/2
            ax.plot(t[mask],v[mask],color='#e39800',alpha=.9,label=f"Switch {p['switch']}: {p['class']}")
            ax.axvline(p['switch'],color='#aaa',lw=.5,ls=':')
        ax.set(ylabel='Trace distance',ylim=(-.01,.68),title='Fig. 2('+group+')');ax.legend(fontsize=8,loc='upper right')
    axes[-1].set(xlabel='Time t',xlim=(0,1.5));fig.suptitle('Independent calculation · '+variant,fontsize=12)
    save(fig,'F2-'+variant+'.png')
    key=variant+'_q';g=GEN['variants'][variant]['q'];p=g['protocols'][0];fig,ax=plt.subplots(figsize=(7,3.8),layout='constrained')
    ax.plot(t,DATA[key+'_distance_final'],color='#2668d5',label='Direct F');ax.plot(t,DATA[key+'_distance_auxiliary'],color='#157347',label='Auxiliary A')
    v=np.linalg.norm(DATA[p['array_key']]-g['final_stationary'],axis=1)/2
    ax.plot(t[t>=p['switch']],v[t>=p['switch']],color='#e39800',label='Two-step, switch .1')
    ax.set(xlabel='Time t',ylabel='Trace distance',xlim=(0,1.5),title='Fig. 4 · '+variant);ax.legend(fontsize=9)
    save(fig,'F4-'+variant+'.png')


def main():
    OUT.mkdir(exist_ok=True,parents=True)
    for unit in ['trace','bloch']:
        fields('c','F1',unit);fields('q','F3',unit)
    for variant in ['printed','stationary_constrained']:traces(variant)
    fig,ax=plt.subplots(figsize=(7,3.5),layout='constrained');t=DATA['time'];mask=t<=.02
    d=DATA['stationary_constrained_c_distance_auxiliary']
    ax.plot(t[mask],d[mask],color='#157347',marker='.',label='Independent auxiliary trajectory')
    minimum=CHECK['fig2c_initial_slope']['stationary_constrained'];ax.scatter([minimum['minimum_time']],[minimum['minimum_distance']],color='#c84426',zorder=4,label='GKSL minimum')
    ax.axhline(.5,color='#999',ls='--',lw=1);ax.set(xlabel='Time t',ylabel='Trace distance',title='Fig. 2(c) · resolved initial shallow minimum');ax.legend(fontsize=8)
    save(fig,'initial-minimum.png')
    print(json.dumps({'figures':len(list(OUT.glob('*.png'))),'all_data':'recorded generation.npz and checks/results.json'}))


if __name__=='__main__':main()
