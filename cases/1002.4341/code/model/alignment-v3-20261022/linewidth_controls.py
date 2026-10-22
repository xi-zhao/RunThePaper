"""Prespecified factor-two linewidth/drive conventions, checked against whole correlation traces.
Variants never replace the printed Gamma=.1,F=.1 source condition.
"""
from pathlib import Path
import sys,json,time
import numpy as np
sys.path.insert(0,str(Path('calculation').resolve()))
from model import Model
from threadpoolctl import threadpool_limits
threadpool_limits(1)
rows=[];times=np.linspace(0,100,201);started=time.monotonic()
for G in [.05,.1,.2]:
 for F in [.05,.1,.2]:
  history=[]
  for cut in [12,16,20]:
   a=Model(3,cut,[0,.12,0],F,G);r=a.steady('propagate');history.append(dict(cut=cut,n1=float(r['n'][0]),g2=float(r['g2'][0]),tail=r['top_probability'],residual=r['residual']))
   if len(history)>1 and r['top_probability']<1e-9 and abs(history[-1]['g2']-history[-2]['g2'])<1e-5:break
  controlled=len(history)>1 and history[-1]['tail']<1e-9 and abs(history[-1]['g2']-history[-2]['g2'])<1e-5
  g=a.correlations(0,0,times)
  rows.append(dict(Gamma=G,F=F,source_condition=(G==.1 and F==.1),cutoff_history=history,controlled=controlled,g11=g.tolist(),minimum_delay_ps=float(times[np.argmin(g)]),minimum_g=float(min(g))))
  print(G,F,'g0',g[0],'min',min(g),'controlled',controlled,flush=True)
Path('calculation/alignment-v3-20261022/linewidth_controls.json').write_text(json.dumps(dict(rows=rows,time_ps=times.tolist(),seconds=time.monotonic()-started,conditions='Source E=(0,.12,0),alpha=.012; exact ordered cross coefficient4alpha and pair2alpha. Gamma is population decay, field decayGamma/2. Non-source factors are declared semantic variants, with hbar=.6582119569 meV ps kept fixed.'),indent=2))
