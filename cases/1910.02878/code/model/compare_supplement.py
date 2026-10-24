"""Vector-reference comparison for main-claim dependencies S2 and S3(a)."""
from pathlib import Path
import os
os.environ['MPLCONFIGDIR']=str(Path.cwd()/'cache'/'matplotlib')
import json,re,numpy as np
from scipy.optimize import linear_sum_assignment
from compare_reference import circles
a=np.load('results/generated.npz')
out={'note':'All comparisons use independent arrays and source axes. No translations fitted to data are applied in the raw metrics.'}

def matching(ref,gen):
 d=abs(ref[:,None]-gen[None,:]);ii,jj=linear_sum_assignment(d);err=d[ii,jj]
 return {'reference_count':len(ref),'generated_count':len(gen),'RMSE':float(np.sqrt(np.mean(err**2))),'max_error':float(err.max()),'complex_mean_delta':[float(np.mean(ref[ii]-gen[jj]).real),float(np.mean(ref[ii]-gen[jj]).imag)]},ii,jj

ssh=circles('source/extracted/NH-SSH.eps')
out['SSH']={}
for idx,panel,x0,x1,y0,y1 in [(0,'b',414.332,666.516,374-307.152,374-54.969),(1,'d',1100.254,1352.438,374-309.188,374-57.004)]:
 y0-=.854706;y1-=.854706 # Both markers and axes share the EPS enclosing concat.
 sel=[p for p in ssh if x0<p['x']<x1]
 ref=(np.array([p['y'] for p in sel])-(y0+y1)/2)/((y1-y0)/4)+1j*(np.array([p['x'] for p in sel])-(x0+x1)/2)/((x1-x0)/4)
 gen=a[f'ssh{idx}_obc'];met,ii,jj=matching(ref,gen)
 met['vector_reading_bound']=float(np.hypot(.02/((y1-y0)/4),.02/((x1-x0)/4)))
 met['within_reading_bound']=met['max_error']<=met['vector_reading_bound']
 out['SSH'][panel]=met
 np.savetxt(f'checks/ssh_{panel}_residuals.csv',np.column_stack([ref[ii].real,ref[ii].imag,gen[jj].real,gen[jj].imag,abs(ref[ii]-gen[jj])]),delimiter=',',header='ref_ReE,ref_ImE,gen_ReE,gen_ImE,error',comments='')

# Periodic SSH polylines are original vector paths (not author arrays). Check
# every path vertex against the analytic equation for E^2, plus range coverage.
text=Path('source/extracted/NH-SSH.eps').read_text()
num=r'-?\d+(?:\.\d+)?'
polylines=[]
for match in re.finditer(rf'q 1 0 0 -1 0 374 cm\s+((?:{num}\s+){{2}}m\s+(?:(?:{num}\s+){{2}}l\s*){{20,}})S Q',text):
 xy=np.array(re.findall(rf'({num})\s+({num})\s+[ml]',match.group(1)),float)
 polylines.append(xy)
for idx,panel,lims,pars in [(0,'a',(66.430,318.613,55.590,307.773),(1/3,1.,.5)),(1,'c',(751.059,1003.242,55.199,307.383),(.75,1.,1.2))]:
 x0,x1,y0,y1=lims
 paths=[p for p in polylines if np.min(p[:,0])>=x0 and np.max(p[:,0])<=x1]
 points=np.vstack(paths)
 E=((y0+y1)/2-points[:,1])/((y1-y0)/4)+1j*(points[:,0]-(x0+x1)/2)/((x1-x0)/4)
 v,w,g=pars;base=v*v-g*g+w*w
 elliptical=((E*E).real-base)/(2*v*w)+1j*(E*E).imag/(2*g*w)
 k=np.angle(elliptical);ideal=np.sqrt(base+2*v*w*np.cos(k)+2j*g*w*np.sin(k))
 distance=np.minimum(abs(E-ideal),abs(E+ideal))
 out['SSH'][panel]={'path_count':len(paths),'vertex_count':len(E),'ellipse_equation_max_residual':float(abs(abs(elliptical)**2-1).max()),'distance_to_analytic_curve_max':float(distance.max()),'distance_to_analytic_curve_RMSE':float(np.sqrt(np.mean(distance**2))),'phase_coverage_radians':float(np.ptp(k)),'vector_reading_bound':float(np.hypot(.02/((y1-y0)/4),.02/((x1-x0)/4)))}

rows=json.loads(Path('checks/s3_reference_markers.json').read_text())['markers']
coords={}
for label,values,pts in [('x',[-.5,0,.5],[120.773,182.266,243.762]),('y',[-1,-.5,0,.5,1],446.196838+np.array([-244.344,-205.984,-167.629,-129.270,-90.910]))]:
 s,o=np.polyfit(values,pts,1);coords[label]={'scale':s,'offset':o,'tick_residual_pt':float(abs(np.array(pts)-(s*np.array(values)+o)).max())}
out['S3a']={'calibration':coords,'vector_reading_bound':float(np.hypot(.02/coords['x']['scale'],.02/coords['y']['scale']))}
for key,color in [('pbc2',[.368627,.505882,.709804]),('cylinder',[0.,1.,0.]),('full2',[1.,0.,0.])]:
 sel=[p for p in rows if p['x']<400 and p['color']==color]
 ref=(np.array([p['y'] for p in sel])-coords['y']['offset'])/coords['y']['scale']+1j*(np.array([p['x'] for p in sel])-coords['x']['offset'])/coords['x']['scale']
 met,ii,jj=matching(ref,a[key]);met['within_reading_bound']=met['max_error']<=out['S3a']['vector_reading_bound']
 unmatched=np.delete(a[key],jj)
 met['unmatched_generated_count']=len(unmatched)
 if len(unmatched):met['unmatched_abs_ImE_range']=[float(abs(unmatched.imag).min()),float(abs(unmatched.imag).max())]
 out['S3a'][key]=met
 np.savetxt(f'checks/s3a_{key}_residuals.csv',np.column_stack([ref[ii].real,ref[ii].imag,a[key][jj].real,a[key][jj].imag,abs(ref[ii]-a[key][jj])]),delimiter=',',header='ref_ReE,ref_ImE,gen_ReE,gen_ImE,error',comments='')
Path('checks/supplement_comparison.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
