#!/usr/bin/env python3
"""Replot frozen public numerical arrays; never execute a scientific case."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
REV='43a64cd03824edb136b549f352412e8d263d9361'
INPUTS=[]

def source(path):
    data=subprocess.check_output(['git','show',f'{REV}:{path}'],cwd=ROOT)
    INPUTS.append({'path':path,'commit':REV,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    return data.decode()

def table(path): return list(csv.DictReader(io.StringIO(source(path))))
def metric_json(path): return json.loads(source(path))

def save(fig,name):
    fig.savefig(HERE/'figures'/f'{name}.pdf',bbox_inches='tight')
    fig.savefig(HERE/'figures'/f'{name}.png',bbox_inches='tight',dpi=180)
    plt.close(fig)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold','pdf.fonttype':42})
colors=['#275B86','#DA8D45','#23847B','#955F8F','#778594']
qroot='cases/1811.08017/'
wroot='cases/10.1126-science.aaw1611/'
droot='cases/0709.0548/'
q=table(qroot+'outputs/data/fig2_gate_counts.csv')
phase=table(qroot+'outputs/data/fig4_phase_estimation_counts.csv')
one=table(wroot+'outputs/data/one_particle_density.csv')
two=table(wroot+'outputs/data/two_particle_density.csv')
corr=table(wroot+'outputs/data/two_particle_correlators.csv')
disc=table(droot+'outputs/data/fig1_discord.csv')
# Source-code/method provenance is indexed, not executed or duplicated in the package.
for path in [qroot+'code/src/qdrift_resources/model.py',qroot+'docs/NUMERICAL_METHODS.md',qroot+'outputs/checks/target_checks.json',wroot+'code/src/quantum_walk.py',wroot+'docs/NUMERICAL_METHODS.md',wroot+'outputs/checks/T003_checks.json',droot+'code/src/dqc1_discord/model.py',droot+'docs/NUMERICAL_METHODS.md']:
    source(path)

fig,axs=plt.subplots(1,2,figsize=(7.2,3.25),gridspec_kw={'width_ratios':[1.3,1]})
prop=sorted([r for r in q if r['molecule']=='propane'],key=lambda r:float(r['time']))
methods=['qdrift','first_order_deterministic','first_order_random','higher_order_deterministic','higher_order_random']
labels=['qDRIFT','1st-order deterministic','1st-order randomized','Higher-order deterministic','Higher-order randomized']
for m,label,color in zip(methods,labels,colors):
    axs[0].loglog([float(r['time']) for r in prop],[float(r[m]) for r in prop],label=label,color=color,lw=1.5)
axs[0].set(xlabel='Simulation time (source units)',ylabel='Resource-bound gate count',title='a  Propane Hamiltonian resource bounds')
axs[0].legend(fontsize=6.5,frameon=False,loc='upper left')
ratios={}
for mol in ['carbon dioxide','ethane','propane']:
    row=next(r for r in phase if r['molecule']==mol and abs(float(r['failure_probability'])-.05)<1e-12)
    ratios[mol]=float(row['random_trotter_second_order'])/float(row['qdrift'])
axs[1].bar(range(3),list(ratios.values()),color=colors[0],width=.65)
for i,v in enumerate(ratios.values()):axs[1].text(i,v+30,f'{v:.2f}',ha='center',fontsize=8)
axs[1].set(xticks=range(3),xticklabels=['CO$_2$','Ethane','Propane'],ylabel='Randomized Trotter / qDRIFT',ylim=(0,1650),title='b  Phase-estimation resource ratio')
axs[1].text(.5,.91,'Failure probability = 0.05',ha='center',transform=axs[1].transAxes,fontsize=8)
fig.tight_layout(w_pad=1.6)
save(fig,'fig2_resources')

fig,axs=plt.subplots(2,2,figsize=(7.2,5.25))
rows=[r for r in one if r['launch']=='Q6'];times=sorted({float(r['time_ns']) for r in rows});sites=sorted({int(r['site']) for r in rows})
a=np.full((len(sites),len(times)),np.nan);ti={v:i for i,v in enumerate(times)};si={v:i for i,v in enumerate(sites)}
for r in rows:a[si[int(r['site'])],ti[float(r['time_ns'])]]=float(r['density'])
if not np.isfinite(a).all():raise ValueError('Incomplete density grid')
im=axs[0,0].imshow(a,origin='lower',aspect='auto',extent=[times[0],times[-1],.5,len(sites)+.5],cmap='viridis',vmin=0,vmax=1)
axs[0,0].set(xlabel='Time (ns)',ylabel='Site',title='a  One-excitation density; launch Q6')
fig.colorbar(im,ax=axs[0,0],label='Density',fraction=.05,pad=.03)
models=sorted({r['model'] for r in corr});print('Correlation models:',models)
chosen=[]
for ax,model,label in zip([axs[0,1],axs[1,0],axs[1,1]],['strong','hardcore','free'],['b  Calibrated interaction','c  Hard-core limit','d  Free bosons']):
    rows=[r for r in corr if r['model']==model and r['launch']=='Q6_Q7' and abs(float(r['time_ns'])-55.5)<1e-12]
    if len(rows)!=144:raise ValueError((model,len(rows)))
    a=np.zeros((12,12))
    for r in rows:a[int(r['site_i'])-1,int(r['site_j'])-1]=float(r['G_ij'])
    chosen.append(a)
    im=ax.imshow(a,origin='lower',extent=[.5,12.5,.5,12.5],cmap='magma',vmin=0,vmax=.20,aspect='equal')
    ax.set(xlabel='Site j',ylabel='Site i',title=label,xticks=[1,4,8,12],yticks=[1,4,8,12])
    fig.colorbar(im,ax=ax,label='$G_{ij}$',fraction=.05,pad=.03)
fig.tight_layout(h_pad=1.5,w_pad=2.6)
save(fig,'fig3_quantum_walks')

fig,axs=plt.subplots(1,2,figsize=(7.2,3.2))
x=np.array([float(r['alpha']) for r in disc]);analytic=np.array([float(r['analytic_discord']) for r in disc])
axs[0].plot(x,analytic,color='#353535',ls='--',lw=1.5,label='Analytical reference')
for prefix,label,color in [('qr_haar','QR-Haar U(32)',colors[0]),('independent_brickwork','Independent brickwork',colors[1])]:
    y=np.array([float(r[prefix+'_mean']) for r in disc]);lo=np.array([float(r[prefix+'_ci95_low']) for r in disc]);hi=np.array([float(r[prefix+'_ci95_high']) for r in disc])
    axs[0].plot(x,y,color=color,label=label,lw=1.4)
    axs[0].fill_between(x,lo,hi,color=color,alpha=.15)
    axs[1].plot(x,y-analytic,color=color,lw=1.4,label=label)
    axs[1].fill_between(x,lo-analytic,hi-analytic,color=color,alpha=.15)
axs[0].set(xlabel='Control polarization $\\alpha$',ylabel='Quantum discord (bits)',title='a  Stored ensemble means')
axs[0].legend(fontsize=7,frameon=False)
axs[1].set(xlabel='Control polarization $\\alpha$',ylabel='Mean minus analytical reference (bits)',title='b  Finite-ensemble deviations')
axs[1].axhline(0,color='#666666',lw=.6)
fig.tight_layout(w_pad=1.8)
save(fig,'fig4_discord')

fig,ax=plt.subplots(figsize=(7.2,2.6));ax.set(xlim=(0,10),ylim=(0,3.6));ax.axis('off')
boxes=[(.1,2.0,'Source and scope','Paper objects; assumptions'),(3.5,2.0,'Model and derivation','Equations; conventions; units'),(6.9,2.0,'Numerical implementation','Domain code; parameters'),(6.9,.35,'Physical diagnostics','Conservation; references'),(3.5,.35,'Versioned research case','Arrays; checks; review state'),(.1,.35,'Public research artifact','RunThePaper; reuse and study')]
for x0,y0,t,s in boxes:
 ax.add_patch(FancyBboxPatch((x0,y0),2.95,1.05,boxstyle='round,pad=0.03',facecolor='#F1F5F8',edgecolor=colors[0]))
 ax.text(x0+1.475,y0+.69,t,ha='center',fontsize=9,fontweight='bold');ax.text(x0+1.475,y0+.29,s,ha='center',fontsize=7.5)
for a,b in [((3.07,2.525),(3.45,2.525)),((6.47,2.525),(6.85,2.525)),((8.375,1.97),(8.375,1.43)),((6.85,.875),(6.5,.875)),((3.45,.875),(3.1,.875))]:ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':colors[0]})
ax.text(5,3.35,'Human-guided research with AI-assisted implementation',ha='center',fontsize=10,fontweight='bold')
save(fig,'fig1_workflow')

def conservation(data,keys,expected):
 grouped=collections.defaultdict(list)
 for r in data:grouped[tuple(r[k] for k in keys)].append(float(r['density']))
 return {'array_rows':len(data),'state_time_slices':len(grouped),'max_density_sum_error':max(abs(sum(v)-expected) for v in grouped.values())}
summary={'source_commit':REV,'phase_resource_ratios_pf_0_05':ratios,'resource_table_rows':len(q),'phase_table_rows':len(phase),'one_excitation':conservation(one,['launch','time_ns'],1),'two_excitation':conservation(two,['model','launch','time_ns'],2),'discord_grid_points':len(disc),'discord_at_alpha_1':{k:float(v) for k,v in disc[-1].items() if k!='alpha_index'},'illustrative_correlation_time_ns':55.5,'correlation_max_displayed_value':max(float(a.max()) for a in chosen),'new_solver_runs':0,'interpretation':'Read-only reanalysis of archived generated arrays; not whole-paper acceptance.'}
(HERE/'anc'/'result_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(HERE/'anc'/'input_manifest.json').write_text(json.dumps(INPUTS,indent=2)+'\n')
print(json.dumps(summary,indent=2))
