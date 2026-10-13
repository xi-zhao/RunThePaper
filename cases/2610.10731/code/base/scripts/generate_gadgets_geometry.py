"""Source-defined CNOT gadgets, CCZ phases and neutral-atom coordinates.

No circuit-level LER is inferred from these exact algebraic/geometry checks.
The source's heuristic distance column is retained only as a reference value.
"""
import itertools as it
import json, math, re
from pathlib import Path
import numpy as np
from generate_algebra import construct, regular, rank, logical_basis, echelon, bits

# Literal Table III data: n, replacements, nonidentity A entries, depth, d estimate.
GADGETS=[
 (54,{}, {'aa':'x+x^2'},2,6),(54,{}, {'bb':'y+y^2'},2,6),(54,{}, {'cc':'xy^2+x^2y'},2,6),
 (72,{'c':'xy+x^2y'},{'cc':'1+x','bc':'x'},3,8),
 (72,{'a':'1+x'},{'aa':'1+x','ca':'x'},3,8),
 (72,{'a':'y^3+x^2y^2'},{'aa':'1+x^2y^3','ba':'y^3'},3,8),
 (162,{'c':'y^2+xy','d':'1+y^6+x+xy^2'},{'cc':'1+xy^8','cd':'y'},3,14),
 (162,{'a':'1+xy^5'},{'aa':'1+y^3','ba':'y^8','ca':'xy^3'},4,14),
 (162,{'b':'1+x'},{'bb':'1+x^2','cb':'1'},3,13),
 (162,{'c':'1+y+y^2+x^2y'},{'cc':'1+y^8','bc':'x^2y^8'},3,14),
 (162,{'a':'y^8+xy^2+x^2y^5+x^2y^7'},{'aa':'1+xy^3','ca':'y^7'},3,14),
 (162,{'c':'y^2+y^4+y^7+x^2y^3'},{'cc':'1+y^6','ac':'y^7','bc':'x^2y'},4,14),
 (228,{'c':'y^4+x'},{'cc':'1+y','bc':'y'},3,17),
 (228,{'a':'y^13+x'},{'aa':'1+y^8','ca':'y^8'},3,15),
 (228,{'c':'y^5+xy^13'},{'cc':'1+y^6','ac':'xy^11'},3,14),
 (228,{'c':'y^5+y^9+y^13+xy^15'},{'cc':'1+y^4','ac':'y^15'},3,17),
 (228,{'a':'xy^7+xy^10+xy^13+xy^16'},{'aa':'1+y^3','ca':'xy^2'},3,17),
 (228,{'a':'y^7+x+xy^9+xy^14'},{'aa':'1+y^14','ba':'y^4'},3,17)]


def parse(s,group):
    ans=set()
    for term in s.split('+'):
        coord=[0]*len(group)
        if term!='1':
            matches=list(re.finditer(r'([xyz])(?:\^(\d+))?',term))
            assert ''.join(m.group(0) for m in matches)==term
            for m in matches:coord['xyz'.index(m[1])]+=int(m[2] or 1)
        c=tuple(a%b for a,b in zip(coord,group))
        if c in ans:ans.remove(c)
        else:ans.add(c)
    return ans


def mul(a,b,g):
    out=set()
    for x in a:
        for y in b:
            z=tuple((u+v)%q for u,v,q in zip(x,y,g))
            if z in out:out.remove(z)
            else:out.add(z)
    return out


def exterior(A,k,g):
    subs=list(it.combinations(range(4),k));blocks=[]
    for rows in subs:
        line=[]
        for cols in subs:
            s=set()
            for perm in it.permutations(cols):
                v={(0,)*len(g)}
                for i,j in zip(rows,perm):v=mul(v,A[i][j],g)
                s^=v
            line.append(regular(g,s))
        blocks.append(line)
    return np.block(blocks)


def boundary(factors,k,g):
    lower=list(it.combinations(range(4),k-1));upper=list(it.combinations(range(4),k));z=np.zeros((math.prod(g),)*2,dtype=np.uint8)
    return np.block([[regular(g,factors[next(iter(set(b)-set(a)))]) if set(a)<set(b) else z for b in upper] for a in lower])


def main():
    models=json.loads(Path('config/models.json').read_text())['pairs'];by_n={m['quad'][0]:m for m in models};rows=[];arrays={};measured=[]
    for index,(n,replaced,entries,depth,dest) in enumerate(GADGETS):
        m=by_n[n];g=m['group'];ng=math.prod(g);f=[set(map(tuple,p)) for p in m['polynomials']];fp=[parse(replaced[c],g) if c in replaced else x for c,x in zip('abcd',f)]
        A=[[{(0,)*len(g)} if i==j else set() for j in range(4)] for i in range(4)]
        for ij,s in entries.items():A['abcd'.index(ij[0])]['abcd'.index(ij[1])]=parse(s,g)
        relation=[]
        for j in range(4):
            v=set()
            for i in range(4):v^=mul(A[i][j],fp[i],g)
            relation.append(len(v^f[j]))
        maps={k:exterior(A,k,g) for k in range(5)};D={k:boundary(f,k,g) for k in range(1,5)};Dp={k:boundary(fp,k,g) for k in range(1,5)}
        residues=[int(np.count_nonzero((maps[k-1]@D[k]+Dp[k]@maps[k])%2)) for k in range(1,5)]
        hx,hz=D[3].T,D[2];hxp,hzp=Dp[3].T,Dp[2];F=maps[2]
        # The compute logical Xs occupy bc, ac, ab in standard exterior order.
        tx,tz=construct(m)[4:];tl=logical_basis(tz,tx);embedded=np.zeros((3,n),np.uint8)
        for j,sector in enumerate([3,1,0]):embedded[:,sector*ng:(sector+1)*ng]=tl[:,j*ng:(j+1)*ng]
        zlogical=logical_basis(hxp,hzp);images=zlogical@F%2;coeff=images@embedded.T%2
        mb=logical_basis(np.zeros((0,3),np.uint8),np.zeros((0,3),np.uint8)) if False else None
        piv=[];old=0
        for c in coeff:
            if rank(np.array(piv+[c],np.uint8))>old:piv.append(c);old+=1
        measured.append(piv)
        max_degree=max(int(F.sum(0).max()),int(F.sum(1).max()))
        row=dict(index=index+1,n=n,replacements=replaced,A_entries=entries,polynomial_relation_residuals=relation,chain_map_residuals=residues,ancilla_k=n-rank(hxp)-rank(hzp),ancilla_max_check_weight=max(int(hxp.sum(1).max()),int(hzp.sum(1).max())),compute_embedding_cycle_residual=int(np.count_nonzero(hz@embedded.T%2)),compute_embedding_rank=rank(np.vstack([hx,embedded]))-rank(hx),measured_compute_rank=old,measured_compute_basis=[x.tolist() for x in piv],F_edge_count=int(F.sum()),minimal_bipartite_CNOT_depth=max_degree,source_depth=depth,source_fault_distance_estimate=dest,fault_distance_independently_established=False)
        rows.append(row);arrays[f'g{index+1}_F']=F
    groups=[dict(rows=list(range(j+1,j+4)),compute_joint_rank=rank(np.array(sum(measured[j:j+3],[]),np.uint8))) for j in range(0,len(rows),3)]
    # Literal CCZ shift table in Z3 x Z3. Both layers use the same three codes.
    permutations=[(0,1,2),(1,2,0),(2,0,1),(0,2,1),(1,0,2),(2,1,0)]
    shifts=[((0,1),(2,0)),((1,0),(2,1)),((1,2),(0,2)),((1,0),(0,0)),((1,0),(2,0)),((0,0),(2,0))]
    coords=list(it.product(range(3),repeat=2));ci={c:i for i,c in enumerate(coords)};gates=[]
    for perm,(s2,s23) in zip(permutations,shifts):
        s3=tuple((a-b)%3 for a,b in zip(s2,s23))
        for a in coords:
            loc=[a,tuple((x+y)%3 for x,y in zip(a,s2)),tuple((x+y)%3 for x,y in zip(a,s3))]
            gates.append(tuple(perm[i]*9+ci[loc[i]] for i in range(3)))
    tx,tz=construct(models[0])[4:];xs=[];old=0
    for x in tx:
        if rank(np.array(xs+[x]))>old:xs.append(x);old+=1
    K=np.vstack([xs,logical_basis(tz,tx)]);tensor=np.zeros((len(K),)*3,dtype=np.uint8)
    for a,b,c in gates:tensor^=np.einsum('i,j,k->ijk',K[:,a],K[:,b],K[:,c])%2
    wanted=np.zeros((3,3,3),np.uint8)
    for a,b,c in it.permutations(range(3)):wanted[a,b,c]=1
    stab=tensor.copy();stab[-3:,-3:,-3:]=0
    candidates=[];zr=echelon(bits(r) for r in tz)
    for gi,gate in enumerate(gates[:27]):
        for leg in range(3):
            support=[gate[leg]]
            for other in [j for j in range(3) if j!=leg]:support += [h[leg] for h in gates[27:] if h[other]==gate[other]]
            v=np.zeros(27,np.uint8)
            for q in support:v[q]^=1
            r=bits(v)
            while r and r.bit_length()-1 in zr:r^=zr[r.bit_length()-1]
            if not np.any(tx@v%2) and r:candidates.append(dict(first_layer_gate=gi,Z_leg=leg,target_support=np.flatnonzero(v).tolist(),weight=int(v.sum())))
    counts=[sum(2**sum(x!=0 for x in s) for pair in shifts[j:j+3] for s in pair) for j in (0,3)]
    ccz=dict(physical_gates=len(gates),gates_per_layer=[27,27],single_use_each_copy_each_layer=all(len({t[copy] for t in gates[j:j+27]})==27 for copy in range(3) for j in (0,27)),stabilizer_trilinear_residual=int(stab.sum()),logical_determinant_mismatches=int(np.count_nonzero(tensor[-3:,-3:,-3:]^wanted)),depth2_fault_candidates=candidates,naive_rigid_translation_counts=counts,fanout_disjoint_gates=len(gates),merged_16_job_schedule_verified=False)
    traps=[];labels=[];p4=math.sqrt(84)
    for copy,Y in enumerate([118,130+5*p4,142+10*p4]):
        for k in range(21):
            for d in range(6):
                for rail in (-1,1):traps.append((10+12*(k+.5*(d%2))+rail,Y+p4*d));labels.append(4)
    for copy,(Y,pitch) in enumerate([(10,10),(42,14),(82,10)]):
        for k in range(18):
            for j in range(3):
                X=10+12*(k+.5);yy=Y+pitch*j
                for rail in (-1,1):traps.append((X+rail,yy));labels.append(3)
                if copy==1:traps.append((X,yy-math.sqrt(3)));labels.append(2)
    a=np.array(traps);arrays['onarray_traps_um']=a;arrays['onarray_trap_class']=np.array(labels)
    geometry=dict(assumptions={'px_um':12,'x0_um':10,'derivation':'px follows the safety equation; x0 fixes the reported bounding box origin.'},onarray_traps=len(a),distinct_traps=len(set(traps)),traps4=labels.count(4),traps3=labels.count(3),apex=labels.count(2),bbox_um=[a.min(0).tolist(),a.max(0).tolist()],with_readout_and_reservoir=len(a)+162+216,diagonal_neighbor_clearance_um=math.hypot(p4,12/2-2),triangle_sides_um=[2.,math.hypot(1,math.sqrt(3)),math.hypot(1,math.sqrt(3))],active_compute_and_ancilla_atoms=3*(54+36)+3*54,full_moving_atom_collision_schedule_checked=False)
    p=Path('outputs/data');p.mkdir(parents=True,exist_ok=True);np.savez_compressed(p/'gadgets-geometry.npz',**arrays)
    (p/'gadgets-geometry.json').write_text(json.dumps(dict(gadgets=rows,independent_measurement_triples=groups,ccz=ccz,geometry=geometry,limits='No decoder, factory LER, full AOD fusion schedule, or gadget fault-distance lower bound is established here.'),indent=2)+'\n')

if __name__=='__main__':main()
