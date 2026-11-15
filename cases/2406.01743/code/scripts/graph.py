"""Freeze candidate graphs from the article's documented NetworkX calls."""
from pathlib import Path
import json
import networkx as nx

cases=[]
for n,k,seed,top in [(80,3,68,106),(100,3,12,135),(120,3,8,163),(156,3,0,213),(156,5,0,324)]:
    g=nx.random_regular_graph(k,n,seed=seed)
    edges=sorted([sorted([int(u),int(v)]) for u,v in g.edges()])
    assert len(edges)==n*k//2
    cases.append(dict(n=n,k=k,seed=seed,source_global_max=top,edges=edges))
Path("config/graphs.json").write_text(json.dumps(dict(networkx=nx.__version__,cases=cases),indent=2)+"\n")
