"""Source-bound comparison, independent controls and size/time sensitivity."""
import os
for name in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:
    os.environ[name]='1'
os.environ['MPLCONFIGDIR']='local-source'
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import shutil
import subprocess
import sys
import zipfile
import io
import fitz
import numpy as np
from scipy.optimize import minimize, minimize_scalar
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

root=Path.cwd()
bundle,cid,hid=sys.argv[1:4]
assets=root/'review-input/assets'
cg=assets/'experiments'/cid/'output/continuation'
hg=assets/'experiments'/hid/'output/continuation'
out=root/'continuation/review-v2'
out.mkdir(parents=True,exist_ok=True)
read=lambda p:json.loads(p.read_text())
with TemporaryDirectory(prefix='zen-check-',dir=root) as tmp:
    w=Path(tmp)
    (w/'reference/original').mkdir(parents=True)
    (w/'code').mkdir()
    for name in ['extract_reference.py','extract_collapse_reference.py']:
        shutil.copyfile(root/'code'/name,w/'code'/name)
    for p in (assets/'snapshot/reference/original').glob('*.pdf'):
        shutil.copyfile(p,w/'reference/original'/p.name)
    for name in ['extract_reference.py','extract_collapse_reference.py']:
        subprocess.run([sys.executable,'-B','code/'+name],cwd=w,check=True)
    ref=read(w/'reference/vector-data.json')
    collapse=read(w/'reference/collapse-vector-data.json')
    for name in ['fig2e','fig2f']:
        ds=fitz.open(w/f'reference/original/{name}.pdf')[0].get_drawings()
        pts=[]
        for d in ds:
            if d['type']=='f' and len(d['items'])==8 and d['rect'].width<25 and max(d['fill'])-min(d['fill'])>.1:
                r=d['rect'];pts.append([(r.x0+r.x1)/2,(r.y0+r.y1)/2])
        assert len(pts)==5
        pts=np.array(sorted(pts));x=np.polyval(ref[name]['x_calibration'],pts[:,0]);y=np.polyval(ref[name]['y_calibration'],pts[:,1])
        ref[name]['thermal_markers']={'L_nearest_even':(2*np.rint(x/2)).astype(int).tolist(),
            'x':x.tolist(),'y':y.tolist(),'center_quantization_y_bound':float(1.5*abs(ref[name]['y_calibration'][0])),
            'meaning':'Five simulated-size markers, not the 75 vertices of the analytic guide.'}
    (out/'reference.json').write_text(json.dumps({'raw':ref,'collapse':collapse},indent=2)+'\n')

for src,name in [(cg/'checks/core-validation.json','core-validation.json'),(hg/'checks/haar-validation.json','haar-validation.json')]:
    shutil.copyfile(src,out/name)
core=read(out/'core-validation.json');hv=read(out/'haar-validation.json')
haar=read(hg/'results/haar-main/trajectories.json')
channels=read(hg/'results/haar-main/channels.json')
pair=read(hg/'results/haar-main/A1-exact-reduction.json')
main=read(cg/'results/clifford-main/summary.json')
fill=read(cg/'results/clifford-fill/summary.json')
conv=read(cg/'results/clifford-convergence/summary.json')
dyn=read(cg/'results/clifford-dynamics/summary.json')
rows={}
for r in main['rows']+fill['rows']:
    key=(r['model'],r['L'],round(r['p'],5))
    if key in rows:
        raise ValueError('Duplicate independent setting must not be silently overwritten')
    rows[key]=r
# Use the common observed parity instead of mixing main/fill statistics.
for family,data in [('clifford-main',main),('clifford-fill',fill)]:
    with zipfile.ZipFile(cg/f'results/{family}/trajectories.zip') as archive:
        for r in data['rows']:
            z=np.load(io.BytesIO(archive.read(r['file'])))
            t=z['times'];e=z['entropy'].astype(float)
            even=e[:,(t>=400)&(t%2==0)].mean(axis=1)
            r['recorded_steady_mean']=r['steady_mean']
            r['steady_mean']=float(even.mean())
            r['steady_sem']=float(even.std(ddof=1)/np.sqrt(len(even)))
get=lambda model,L,p:rows[(model,int(L),round(float(p),5))]
hrows={(r['model'],r['L']):r for r in haar['rows']}

comparisons={}
for panel in ['a','b','c','d','e','f']:
    name='fig2'+panel; rr=ref[name]; points=[]
    if panel in ['e','f']:
        m=1 if panel=='e' else 2
        marker=rr['thermal_markers']
        for L,y in zip(marker['L_nearest_even'],marker['y']):
            vals=np.array([x['S_final'] for x in channels if x['L']==L and x['model']==m])
            points.append({'x':L,'reference':y,'computed':float(vals.mean()),'sem':float(vals.std(ddof=1)/np.sqrt(len(vals))),
                'reading_bound':marker['center_quantization_y_bound'],'difference':float(vals.mean()-y)})
    else:
        curve=rr['curves'][0]
        for x,y in zip(curve['x'],curve['y']):
            xx=int(round(x))
            if panel in ['a','c']:
                value=0. if panel=='a' and xx in [0,16] else pair['S_pair_exact']*(1 if panel=='c' and xx==2 else .5)
                se=0.;parities=None
            else:
                L=16 if panel=='b' else xx;cut=xx if panel=='b' else L//2;r=hrows[(2,L)]
                value=r['mean'][cut];se=r['sem'][cut];parities=[v[cut] for v in r['parity_means']]
            points.append({'x':xx,'reference':y,'computed':value,'sem':se,'difference':value-y,
                'reading_bound':rr['y_coordinate_resolution_bound'],'parity_values':parities})
    comparisons['F2'+panel]=points

for name,model in [('fig3a',1),('fig3b',2),('fig4a',1),('fig5a',2)]:
    pts=[]
    for curve in ref[name]['curves']:
        for x,y in zip(curve['x'],curve['y']):
            if name.startswith('fig3'):L=int(round(x));p=curve['parameter']
            else:L=curve['parameter'];p=round(x,3)
            r=get(model,L,p)
            pts.append({'L':L,'p':p,'reference':y,'computed':r['steady_mean'],'sem':r['steady_sem'],
                'difference':r['steady_mean']-y,'ratio':r['steady_mean']/y,
                'reading_bound':y*np.expm1(ref[name]['y_coordinate_resolution_bound'])})
    comparisons['F'+name[3:]]=pts

for name,model,pc,gamma,nu in [('fig4b',1,.15,.30,1.85),('fig5b',2,.68,.33,1.75)]:
    pts=[]
    grid=([.005]+list(np.round(np.arange(.01,.251,.01),2))+[.3]) if model==1 else ([.3,.4]+list(np.round(np.arange(.5,.851,.01),2))+[.9,1.])
    for curve in collapse[name]['curves']:
        assert len(grid)==len(curve['x'])
        L=curve['L']
        for p,x,y in zip(grid,curve['x'],curve['y']):
            r=get(model,L,p);xcalc=(p-pc)*L**(1/nu);scaled=r['steady_mean']/L**gamma
            pts.append({'L':L,'p':p,'reference_x':x,'reference_y':y,'computed_x':xcalc,'computed_y':scaled,
                'computed_sem':r['steady_sem']/L**gamma,'x_difference':xcalc-x,'y_difference':scaled-y,
                'reference_log_y_reading_bound':collapse[name]['log_y_reading_bound'],
                'grid_assignment':'Monotone original uncollapsed p grid; finite marker quantization not used to choose a different p.'})
    comparisons['F'+name[3:]]=pts

convergence=[]
archives={}
for family in ['clifford-main','clifford-convergence','clifford-dynamics']:
    archives[family]=zipfile.ZipFile(cg/f'results/{family}/trajectories.zip')
for r in conv['rows']:
    z=np.load(io.BytesIO(archives['clifford-convergence'].read(r['file'])))
    t=z['times'];e=z['entropy'].astype(float)
    early=e[:,(t>=400)&(t<=600)].mean(axis=1);late=e[:,t>=800].mean(axis=1);diff=late-early
    convergence.append({'model':r['model'],'L':r['L'],'p':r['p'],'n':len(e),
        'early_even_mean':float(early.mean()),'late_even_mean':float(late.mean()),
        'paired_difference':float(diff.mean()),'paired_se':float(diff.std(ddof=1)/np.sqrt(len(e))),
        'note':'Same trajectories; no independent-time-sample inflation.'})
parity=[]
for r in main['rows']:
    if r['L'] not in [16,128,512] or r['p'] not in [0,.15,.68,1]:continue
    z=np.load(io.BytesIO(archives['clifford-main'].read(r['file'])))
    t=z['times'];e=z['entropy'].astype(float);mask=t>=400
    even=e[:,mask&(t%2==0)].mean(axis=1);odd=e[:,mask&(t%2==1)].mean(axis=1)
    parity.append({'model':r['model'],'L':r['L'],'p':r['p'],'even_mean':float(even.mean()),'odd_mean':float(odd.mean()),
                   'difference_sem':float((even-odd).std(ddof=1)/np.sqrt(len(e)))})

def slope(xs,ys):
    return float(np.polyfit(np.log(xs),np.log(ys),1)[0])
phase_slopes=[]
for model,ps in [(1,[0,.03,.15,.3,1]),(2,[0,.3,.68,1])]:
    for p in ps:
        ls=[64,128,256,512];rs=[get(model,L,p) for L in ls]
        phase_slopes.append({'model':model,'p':p,'L_min':64,'log_slope':slope(ls,[r['steady_mean'] for r in rs])})

fits=[]
for model,pc0,g0,nu0 in [(1,.15,.30,1.85),(2,.68,.33,1.75)]:
    curves={L:sorted([r for r in rows.values() if r['model']==model and r['L']==L],key=lambda r:r['p']) for L in [16,32,64,128,256,512]}
    for lmin in [16,32,64]:
        sizes=np.array([L for L in curves if L>=lmin])
        for span in [.15,.30]:
            grid=np.linspace(-span,span,25)
            def loss(params):
                pc,g,nu=params
                if not ((.10<pc<.22 if model==1 else .55<pc<.80) and .05<g<.7 and .6<nu<3):return 1e6
                vals=[]
                for L in sizes:
                    rs=curves[L];pp=np.array([r['p'] for r in rs]);yy=np.log([r['steady_mean'] for r in rs]);query=pc+grid/L**(1/nu)
                    if query.min()<pp.min() or query.max()>pp.max():return 1e6
                    vals.append(np.interp(query,pp,yy)-g*np.log(L))
                values=np.array(vals)
                return float(np.mean((values-values.mean(axis=0))**2))
            res=minimize(loss,[pc0,g0,nu0],method='Nelder-Mead',options={'maxiter':1000,'xatol':1e-6,'fatol':1e-10})
            fits.append({'model':model,'L_min':lmin,'scaled_x_halfwidth':span,'pc_gamma_nu':res.x.tolist(),
                'loss':float(res.fun),'source_parameters_loss':loss([pc0,g0,nu0]),'converged':bool(res.success),
                'meaning':'Unweighted log-collapse/window sensitivity, NOT parameter confidence intervals or unique asymptotic exponents.'})

dynamic=[];drows={r['L']:r for r in dyn['rows']}
for c in ref['fig6_resub']['curves']:
    L=c['parameter'];r=drows[L];x=np.array(c['x']);yy=np.array(c['y']);tt=x*L
    for clock in ['layer','period']:
        t=np.array(r['times'])/(1 if clock=='layer' else 2)
        calc=np.interp(tt,t,r['mean'])/L**.30;se=np.interp(tt,t,r['sem'])/L**.30
        dynamic.append({'L':L,'clock':clock,'x':x.tolist(),'source':yy.tolist(),'computed':calc.tolist(),
            'sem':se.tolist(),'rmse':float(np.sqrt(np.mean((calc-yy)**2))),'max_abs':float(np.max(abs(calc-yy))),
            'points':len(x),'source_max_time':float(tt.max()),'generated_max_time':float(t[-1])})
dfits=[]
for lmin in [16,32,64]:
    sizes=[L for L in drows if L>=lmin]
    for lo,hi in [(.03,.15),(.05,.25),(.10,.30)]:
        xx=np.linspace(lo,hi,40)
        def dloss(z):
            values=[]
            for L in sizes:
                r=drows[L];t=np.array(r['times'])/2;vals=np.interp(xx*L**z,t,r['mean'])/L**.30
                values.append(np.log(np.maximum(vals,1e-12)))
            a=np.array(values)
            return float(np.mean((a-a.mean(axis=0))**2))
        res=minimize_scalar(dloss,bounds=(.7,1.2),method='bounded')
        dfits.append({'L_min':lmin,'scaled_time_window':[lo,hi],'z':float(res.x),'loss':float(res.fun),
            'source_z1_loss':dloss(1.),'fixed_gamma':.30,'clock':'period; multiplicative time convention is separately compared'})
early=[]
for L,r in drows.items():
    t=np.array(r['times'])/2;sv=np.array(r['mean'])
    for lo,hi in [(2,10),(4,20),(8,40)]:
        m=(t>=lo)&(t<=hi)&(t<=L*.15)&(sv>0)
        if m.sum()>=4:early.append({'L':L,'requested_window':[lo,hi],'last_time':float(t[m][-1]),'slope':slope(t[m],sv[m])})

summary={'comparisons':comparisons,'convergence':convergence,'parity':parity,'phase_slopes':phase_slopes,
    'static_fit_sensitivity':fits,'dynamic':dynamic,'dynamic_fit_sensitivity':dfits,'early_time_slopes':early,
    'pair_reduction':pair,'channels':channels,'haar_sizes':[{k:r[k] for k in ['L','model','n','mean','sem']} for r in haar['rows']],
    'selection':'Even t>=400 across all 589 settings; 259 main and 330 fill previously had different parity masks.',
    'limitations':['Pointwise finite-sample residual is not a statistical rejection without author variance.',
        'Both time conventions and layer parities retained.','Fits have finite-size/interpolation and window sensitivity; no universal exponent certification.']}
(out/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')

plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(3,2,figsize=(9,10),layout='constrained')
for panel,ax in zip('abcdef',axs.flat):
    ps=comparisons['F2'+panel];xx=[p['x'] for p in ps]
    ax.errorbar(xx,[p['computed'] for p in ps],yerr=[2*p['sem'] for p in ps],fmt='o-',ms=3,label='Independent +/-2 SEM')
    ax.plot(xx,[p['reference'] for p in ps],'x--',color='#bd6d27',label='Fixed source markers/line')
    ax.set_title('Figure 2('+panel+')');ax.set_xlabel('Cut size' if panel in 'ab' else 'System size L');ax.set_ylabel('Entropy (bits)');ax.grid(alpha=.15)
axs[0,0].legend(fontsize=7);fig.savefig(out/'haar_comparison.png',dpi=160);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for name,ax in zip(['F3a','F3b'],axs):
    ps=comparisons[name]
    for p in sorted({r['p'] for r in ps}):
        ss=sorted([r for r in ps if r['p']==p],key=lambda r:r['L']);line,=ax.loglog([r['L'] for r in ss],[r['computed'] for r in ss],lw=1,label=str(p))
        ax.loglog([r['L'] for r in ss],[r['reference'] for r in ss],'x',ms=3,color=line.get_color())
    ax.set(xlabel='L',ylabel='S(L/4), bits',title=name+': lines ours, crosses source');ax.legend(ncol=3,fontsize=6)
fig.savefig(out/'phase_comparison.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(2,2,figsize=(11,8),layout='constrained')
for name,ax in zip(['F4a','F4b','F5a','F5b'],axs.flat):
    ps=comparisons[name]
    for L in sorted({r['L'] for r in ps}):
        ss=[r for r in ps if r['L']==L]
        x=[r['p'] if name.endswith('a') else r['computed_x'] for r in ss];y=[r['computed'] if name.endswith('a') else r['computed_y'] for r in ss]
        line,=ax.semilogy(x,y,'-',lw=1,label=f'L={L}')
        ax.semilogy([r['p'] if name.endswith('a') else r['reference_x'] for r in ss],
            [r['reference'] if name.endswith('a') else r['reference_y'] for r in ss],'x',ms=2,color=line.get_color())
    ax.set_title(name+': fixed source exponents, no retuning');ax.set_xlabel('p' if name.endswith('a') else '(p-pc) L^(1/nu)');ax.set_ylabel('S' if name.endswith('a') else 'S / L^gamma');ax.legend(ncol=2,fontsize=6)
fig.savefig(out/'static_collapse.png',dpi=170);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
for clock,ax in zip(['layer','period'],axs):
    for r in dynamic:
        if r['clock']!=clock:continue
        ax.plot(r['x'],r['source'],':',lw=.8,alpha=.6)
        ax.plot(r['x'],r['computed'],lw=1,label=f'L={r["L"]}')
    ax.set(xlim=(0,1.2),xlabel='Source t / L',ylabel='S / L^0.30',title=f'F6 clock: {clock}; dotted source');ax.legend(ncol=2,fontsize=7)
fig.savefig(out/'dynamic_comparison.png',dpi=180);plt.close(fig)

D,M,C='checks/analytic-derivation.md','checks/method.md','checks/continuation_scope.md'
subprocess.run([sys.executable,'-B','code/continuation_parity_check_v2.py',cid,'continuation/review-v2'],check=True)
ev=['continuation/review-v2/'+n for n in ['analysis.json','reference.json','core-validation.json','haar-validation.json','parity_diagnostic.json']]
C='checks/continuation_interpretation.md'
findings=[]
def add(obj,check,outcome,observation,cause='none'):
    findings.append({'object_id':obj,'check_id':check,'outcome':outcome,'cause':cause,'observation':observation,
        'method':'Fresh uniform-Clifford support simulation versus dense Born wavefunctions; Haar tensor contractions versus explicit Kraus/SVD; full original vector measurements and size/time/parity controls.',
        'evidence_paths':[D,M,C]+ev,'next_action':'Preserve finite-size support and resolve source averaging/clock and critical-fit sensitivity without changing original conditions.',
        'basis':{'kind':'mixed','experiment_ids':[hid] if obj.startswith('F2') else [cid],
            'evidence':{'applicability':[D,M,C],'derivation':[D],'error_analysis':ev,'independent_check':ev}},'resolutions':[]})
valid=core['passed'] and hv['passed']
for panel in 'abcdef':
    obj='F2'+panel;ps=comparisons[obj]
    if panel in 'ef':
        ok=all(abs(x['computed']-x['reference'])<=x['reading_bound'] for x in ps)
        add(obj,'thermal_values','supports' if ok and valid else 'inconclusive',f"Five original markers (not guide vertices): {ps}. Unconditioned S tends to L, distinct from trajectory entropy.",'none' if ok and valid else 'unknown')
    else:
        add(obj,'finite_regime','supports' if valid else 'inconclusive',f"p=1 original Haar model, source-size range; A1 exact all-size area bound and mean, A2 actual finite-size trajectory values {[(p['x'],p['computed']) for p in ps]}. A2 finite sizes alone do not prove an asymptotic area law.",'none' if valid else 'implementation')
        add(obj,'source_values','inconclusive',f"All original values retained; maximum absolute residual {max(abs(p['difference']) for p in ps)}. Source parity/time averaging and sample uncertainty not published; inferred parity average is explicit.",'missing_information')
for obj in ['F3a','F3b','F4a','F5a']:
    ps=comparisons[obj]
    add(obj,'finite_regime','supports' if valid else 'inconclusive',f"All589 generated settings use the common EVEN-layer statistic, a declared comparison convention, not an inferred author fact. Mixed main/fill masks in v1 are superseded. Phase slopes {phase_slopes}. Actual finite-time and parity controls retained, not an asymptotic universality certificate.",'none' if valid else 'implementation')
    add(obj,'source_values','inconclusive',f"All {len(ps)} original vector points compared: maximum absolute residual {max(abs(p['difference']) for p in ps)}, mean absolute residual {np.mean([abs(p['difference']) for p in ps])}. No invented author SEM.",'missing_information')
for obj,model in [('F4b',1),('F5b',2)]:
    add(obj,'collapse_parameters','inconclusive',f"Caption parameters rendered without retuning; independent finite-window fits {[(r['L_min'],r['scaled_x_halfwidth'],r['pc_gamma_nu']) for r in fits if r['model']==model]}. Sensitivity is not a confidence interval or proof of exact source exponents.",'unknown')
    add(obj,'source_values','inconclusive',f"All {len(comparisons[obj])} collapsed marker centers retained with their quantization bounds; original plotting versus caption parameter rounding remains separate from generation.",'missing_information')
add('F6','dynamic_exponents','inconclusive',f"Actual 500 trajectories per L at p=.15 through1200 layers. Fixed-gamma z fits {dfits}; early-time slopes {early}. No asymptotic exponent inferred from a selected window.",'unknown')
add('F6','source_values','inconclusive',f"Both clocks compared: {[(r['L'],r['clock'],r['rmse'],r['max_abs']) for r in dynamic]}; source convention is not identified by lower RMSE alone.",'missing_information')
objects=sorted({f['object_id'] for f in findings})
report={'format':'pragent.research-report.v1','bundle_sha256':bundle,
    'reviewer':{'identity':'Research Agent','context':'same_context','context_evidence':'Same current conversation; no subagents or external model calls.',
        'isolation':'Prior work, generation and source all visible; no independent-review claim.'},'findings':findings,
    'object_assessments':[{'object_id':obj,'coverage':{'conditions':'adequate','requirements':'adequate','dependencies':'adequate',
        'rationale':'All original numerical units retained; model/clock ambiguity and unresolved exponent evidence explicitly tested, not waived.','evidence_paths':[D,M,C]+ev},
        'method':{'kind':'independent_implementation','rationale':'Dense complex wavefunction/Kraus oracle checks binary support/tensor contractions; exact Haar pair distribution and finite-time checks independent of paper ordinates.','evidence_paths':[D,M]+ev},
        'boundary':{'prior_reasoning_exposure':'present','reads':'Fixed v2 and original figures, prior methods, fresh outputs.',
            'limitations':'Same researcher; finite sizes and clusters, source sampling unknown; fits not confidence intervals.'}} for obj in objects],
    'limitations':'Numerical fit agreement and source interpretation remain unresolved; original analytic records retain their separate applicability.'}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'settings':len(rows),'static_fit_sensitivity':fits,'phase_slopes':phase_slopes,
    'dynamic_fits':dfits,'early':early,'dynamic_errors':[(r['L'],r['clock'],r['rmse']) for r in dynamic]},indent=2))
