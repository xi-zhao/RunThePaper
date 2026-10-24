from pathlib import Path
import json,numpy as np
raw=json.loads(Path('results/moments.json').read_text());sv=json.loads(Path('checks/validation.json').read_text());ref=json.loads(Path('checks/reference_data.json').read_text());part=json.loads(Path('results/particle_beta025.json').read_text());fine=json.loads(Path('results/particle_fine.json').read_text())
rows={r['n']:r for r in raw['rows']};pr={r['n']:r for r in part['rows']};fr={r['n']:r for r in fine['rows']}
def fit(n,y,se=None):
 n=np.array(n,float);y=np.array(y,float);dx=n-n.mean();slope=float(np.dot(dx,np.log(y))/np.dot(dx,dx));inter=float(np.log(y).mean()-slope*n.mean());out={'slope':slope,'intercept':inter,'definition':'ordinary least squares of natural log variance vs n'}
 if se is not None:out['propagated_standard_error']=float(np.sqrt(np.sum((dx/np.dot(dx,dx)*np.array(se)/y)**2)))
 return out
ns=list(rows);limits=[2**n/(3*(4**n-1)) for n in ns];endpoint=[rows[n]['values']['uniform']['variance'][-1] for n in ns];epse=[rows[n]['values']['uniform']['se'][-1] for n in ns]
fits={'raw_L512_all':fit(ns,endpoint,epse),'raw_L512_n6plus':fit(ns[2:],endpoint[2:],epse[2:]),'analytic_limit_all':fit(ns,limits),'source_fig3':fit(ns,ref[0]['curves'][0]['variance'])}
# The finer particle calculation is selected by predeclared size, not by choosing favorable estimates.
selected={n:(fr[n] if n in fr else pr[n]) for n in ns}
svchecks=[];exactchecks=[];cross=[];refine=[];stationary=[]
for row in sv['statevector']:
 n=row['n'];r=rows[n]
 for q in row['values']:
  k=r['layers'].index(q['L']);m=r['values']['uniform'];se=np.hypot(q['variance_se'],m['se'][k]);svchecks.append({'n':n,'L':q['L'],'statevector_variance':q['variance'],'path_variance':m['variance'][k],'difference':q['variance']-m['variance'][k],'combined_se':float(se),'z':float((q['variance']-m['variance'][k])/se),'mean_z':q['mean']/q['mean_se']})
for row in sv['exact']:
 n=row['n']
 if n not in rows:continue
 r=rows[n]
 for q in row['values']:
  k=r['layers'].index(q['L']);m=r['values']['uniform'];diff=m['variance'][k]-q['uniform'];se=m['se'][k]
  exactchecks.append({'n':n,'L':q['L'],'exact':q['uniform'],'path':m['variance'][k],'difference':diff,'criterion':'absolute <=1e-11 for deterministic L1; otherwise <=5 standard errors','z':None if q['L']==1 else diff/se,'pass':bool(abs(diff)<1e-11 if q['L']==1 else abs(diff)<=5*se)})
for n,r in selected.items():
 a=np.array(r['uniform']);b=np.array(rows[n]['values']['uniform']['variance']);se=np.hypot(r['se'],rows[n]['values']['uniform']['se']);z=(a[1:]-b[1:])/se[1:]
 cross.append({'n':n,'max_abs_z':float(abs(z).max()),'L_at_max':r['layers'][1+int(abs(z).argmax())],'max_relative_se':float(max(np.array(r['se'])/a)),'deterministic_L1_error':float(abs(a[0]-5/48))})
 h=2**n/(3*(4**n-1));stationary.append({'n':n,'exact_limit':h,'raw_L512':b[-1],'raw_se':rows[n]['values']['uniform']['se'][-1],'particle_L512':a[-1],'particle_se':r['se'][-1],'particle_limit_z':(a[-1]-h)/r['se'][-1]})
 if n in fr:
  a=np.array(fr[n]['uniform']);b=np.array(pr[n]['uniform']);se=np.hypot(fr[n]['se'],pr[n]['se']);z=(a[1:]-b[1:])/se[1:];refine.append({'n':n,'max_abs_z':float(abs(z).max()),'L_at_max':r['layers'][1+int(abs(z).argmax())],'coarse_particles':20000,'fine_particles':100000,'coarse_replicates':32,'fine_replicates':64})
comparisons=[]
for c in ref[1]['curves']:
 n=c['n'];r=selected[n];a=[]
 for L,y in zip(c['x_nearest_integer'],c['variance']):
  i=r['layers'].index(L);v=r['uniform'][i];se=r['se'][i];vy=r['fixed_y'][i];a.append({'L':L,'reference':y,'independent_uniform':v,'independent_se':se,'reference_minus_independent':y-v,'reference_over_independent':y/v,'fixed_y_variant':vy,'reference_over_variant':y/vy})
 comparisons.append({'n':n,'points':a,'log_rmse_uniform':float(np.sqrt(np.mean([np.log(q['reference_over_independent'])**2 for q in a]))),'log_rmse_fixed_y_variant':float(np.sqrt(np.mean([np.log(q['reference_over_variant'])**2 for q in a])))})
ref3=[]
for n,y in zip(ns,ref[0]['curves'][0]['variance']):
 r=selected[n];k=r['layers'].index(10*n);ref3.append({'n':n,'reference':y,'raw_L512':rows[n]['values']['uniform']['variance'][-1],'exact_deep_limit':2**n/(3*(4**n-1)),'reference_over_limit':y/(2**n/(3*(4**n-1))),'diagnostic_L10n':r['uniform'][k],'diagnostic_L10n_se':r['se'][k],'diagnostic_fixedY_L10n':r['fixed_y'][k]})
flat=[q for c in comparisons for q in c['points']];deep=[q for c in comparisons for q in c['points'] if q['L']>=384]
summary={'source_version':'1803.11173v1','fits':fits,'gradient_max_shift_error':max(x['shift_error'] for x in sv['gradient']),'gradient_max_fd_error':max(x['fd_error'] for x in sv['gradient']),'max_normalization_error':max(x['max_normalization_error'] for x in sv['statevector']),'max_exact_mass_error':max(x['max_mass_error'] for x in sv['exact']),'statevector_checks':svchecks,'exact_checks':exactchecks,'particle_vs_raw':cross,'particle_refinement':refine,'stationary':stationary,'fig3_comparison':ref3,'fig4_comparison':comparisons,'reference_stats':{'fig4_points':len(flat),'deep_reference_over_uniform_median':float(np.median([q['reference_over_independent'] for q in deep])),'log_rmse_uniform_all':float(np.sqrt(np.mean([np.log(q['reference_over_independent'])**2 for q in flat]))),'log_rmse_fixedY_all':float(np.sqrt(np.mean([np.log(q['reference_over_variant'])**2 for q in flat]))),'calibration':ref[1]['calibration'],'author_sample_count':'not stated; no author sampling standard errors inferred'},'criteria':{'deterministic_tolerance':1e-11,'gradient_shift_tolerance':1e-10,'finite_difference_tolerance':1e-8,'statistical_diagnostic_sigma':5,'reference_equality':'not tested with invented author sampling uncertainty'},'failed_attempts':[{'path':'results/particle.json','reason':'beta=1 particle estimator fails known stationary limit badly at large n; rejected; retained for audit'}],'formal_receipts':'unavailable: managed execute denied before launch; these are observed sandboxed local calculations, not PRAgent execute receipts'}
Path('checks/numerical_analysis.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({'fits':fits,'max_statevector_z':max(abs(x['z']) for x in svchecks),'max_particle_raw_z':max(x['max_abs_z'] for x in cross),'max_refinement_z':max(x['max_abs_z'] for x in refine),'reference_stats':summary['reference_stats'],'stationary':stationary},indent=2))
