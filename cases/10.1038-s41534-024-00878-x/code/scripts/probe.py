import json
from pathlib import Path
import numpy as np

# Perfect knowledge of the category at a starting pixel does not guarantee
# reaching a small target region with a fixed action budget.
x,y=np.indices((30,30))
target=(x>=12)&(x<=15)&(y>=12)&(y<=15)
metric={}
for b in (0,2,5,10):
    d=np.maximum(12-x,0)+np.maximum(x-15,0)+np.maximum(12-y,0)+np.maximum(y-15,0)
    metric[b]=float(np.mean(d<=b))
assert metric[0]==16/900 and metric[5]<1.
Path("results/metric-demo.json").write_text(json.dumps(dict(classification_accuracy=1.,oracle_navigation=metric))+"\n")
