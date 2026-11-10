"""Small graph API for exhaustive n<=5 enumeration; no external graph data."""
import itertools

class Graph:
    def __init__(self,n,edges=()):
        self.adj=[set() for _ in range(n)]
        for a,b in edges:self.add_edge(a,b)
    def __len__(self):return len(self.adj)
    def __getitem__(self,i):return self.adj[i]
    def has_edge(self,a,b):return b in self.adj[a]
    def add_edge(self,a,b):self.adj[a].add(b);self.adj[b].add(a)
    def remove_edge(self,a,b):self.adj[a].remove(b);self.adj[b].remove(a)
    def edges(self):return [(a,b) for a in range(len(self)) for b in self.adj[a] if a<b]
    def number_of_edges(self):return sum(map(len,self.adj))//2
    def copy(self):return Graph(len(self),self.edges())

def is_connected(g):
    seen={0};todo=[0]
    while todo:
        v=todo.pop()
        for w in g[v]-seen:seen.add(w);todo.append(w)
    return len(seen)==len(g)

def representatives(n,canonical):
    pairs=list(itertools.combinations(range(n),2));seen={}
    for mask in range(1<<len(pairs)):
        g=Graph(n,[e for i,e in enumerate(pairs) if mask>>i&1])
        if is_connected(g):seen.setdefault(canonical(g),g)
    return list(seen.values())
