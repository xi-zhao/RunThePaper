"""Finite SD6 convention diagnostics. No author/reference values are read."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import json, hashlib, time, math, itertools
import numpy as np
import stim
from audit_sd6_timing_v3 import timing_circuit
from simulate_sd6_factory_v2 import dem_arrays
from generate_algebra import construct, nullspace

ROOT=Path(__file__).resolve().parents[1]

def build(model,p,pc,schedule,profile):
    ideal,_,meta=timing_circuit(model,0,0,schedule)
    # Parent builder's explicit physical program; frozen original detector tail retained.
    tail=stim.Circuit();ticks=0
    for op in ideal:
        if ticks>=len(meta['layers']):tail.append(op)
        if op.name=='TICK':ticks+=1
    circuit=stim.Circuit();noise_events=[]
    n=model['tri'][0];quad=set(range(2*n,4*n+len(construct(model)[0])))
    for layer in meta['layers']:
        for op in layer['operations']:
            stage,g,qs=op['stage'],op['gate'],op['targets']
            if g=='R':circuit.append(g,qs);cat='reset';ng='X_ERROR';rate=p*profile.get('reset_scale',1)
            elif g=='M':cat='measurement';ng=None;rate=p*profile.get('measurement_scale',1)
            elif g=='H':circuit.append(g,qs);cat='H';ng='DEPOLARIZE1';rate=p*profile.get('depol1_scale',1)*profile.get('H_scale',1)
            elif g=='CX':circuit.append(g,qs);cat='CX';ng='DEPOLARIZE2';rate=p*profile.get('depol2_scale',1)
            elif g=='DEPOLARIZE1':cat='CCZ';ng=g;rate=16*pc/21*profile.get('ccz_scale',1)
            else:raise ValueError(g)
            if cat in profile.get('omit_categories',[]):rate=0
            noisy_qs=qs
            if cat!='CCZ' and profile.get('perfect_quad_prep'):
                noisy_qs=([q for pair in zip(qs[::2],qs[1::2]) if not all(t in quad for t in pair) for q in pair] if cat=='CX' else [q for q in qs if q not in quad])
            if g=='M':
                for q in qs:circuit.append('M',[q],rate if q in noisy_qs else 0)
            elif rate and noisy_qs:circuit.append(ng,noisy_qs,rate)
            noise_events.append(dict(tick=layer['tick'],category=cat,stage=stage,gate=ng or 'M',targets=noisy_qs,probability=rate))
        qs=layer['idle'];rate=p*profile.get('depol1_scale',1)*profile.get('idle_scale',1)
        if profile.get('idle_boundary')=='exclude_first_last':
            future={t for l in meta['layers'][layer['tick']+1:] for o in l['operations'] for t in o['targets']}
            qs=[t for t in qs if t in future]
        if profile.get('perfect_quad_prep'):
            # This profile suppresses only primitive noise on quad preparation, not its idle channels.
            pass
        if qs and rate:circuit.append('DEPOLARIZE1',qs,rate)
        noise_events.append(dict(tick=layer['tick'],category='idle',stage='idle',gate='DEPOLARIZE1',targets=qs,probability=rate))
        circuit.append('TICK')
    circuit+=tail
    dem=circuit.detector_error_model(decompose_errors=False)
    return circuit,dem,meta,noise_events

def exact_distribution(dem,meta):
    h,_,ps=dem_arrays(dem);sel=h[meta['post_start']:meta['npost']];q=len(sel)
    signs=np.array([int.from_bytes(np.packbits(col,bitorder='little').tobytes(),'little') for col in sel.T],np.int64)
    logs=np.zeros(1<<q);np.add.at(logs,signs,np.log1p(-2*ps))
    w=logs.copy()
    for step in (1<<i for i in range(q)):
        a=w.reshape(-1,2*step);x=a[:,:step].copy();y=a[:,step:].copy();a[:,:step]=x+y;a[:,step:]=x-y
    chars=np.exp((logs.sum()-w)/2);probs=chars.copy()
    for step in (1<<i for i in range(q)):
        a=probs.reshape(-1,2*step);x=a[:,:step].copy();y=a[:,step:].copy();a[:,:step]=x+y;a[:,step:]=x-y
    probs/=len(probs)
    assert probs.min()>-1e-13 and abs(probs.sum()-1)<1e-12
    # Removing linearly dependent detector rows cannot change the event; every delete-one checked.
    indices=np.arange(1<<q);drop=[float(probs[(indices & ~(1<<i))==0].sum()) for i in range(q)]
    return probs,drop

def sample_conditions(c,meta,model,shots,seed):
    tri_count=len(nullspace(construct(model)[5].T))
    # 0:tri_count tricycle metachecks, tri_count:post_start quadcycle metachecks.
    counts=dict(tele=0,tri=0,quad=0,prep=0,joint=0,tele_tri=0,tele_quad=0)
    sampler=c.compile_detector_sampler(seed=seed)
    remaining=shots
    while remaining:
        batch=min(100000,remaining);d=sampler.sample(batch)
        a=~d[:,meta['post_start']:meta['npost']].any(1);t=~d[:,:tri_count].any(1);q=~d[:,tri_count:meta['post_start']].any(1);b=t&q
        for key,mask in [('tele',a),('tri',t),('quad',q),('prep',b),('joint',a&b),('tele_tri',a&t),('tele_quad',a&q)]:counts[key]+=int(mask.sum())
        remaining-=batch
    out=dict(shots=shots,seed=seed,counts=counts,tri_metachecks=tri_count,quad_metachecks=meta['post_start']-tri_count)
    out['acceptance']=counts['tele']/shots
    for name,num,den in [('tele_given_tri','tele_tri','tri'),('tele_given_quad','tele_quad','quad'),('tele_given_prep','joint','prep')]:
        value=counts[num]/counts[den];out[name]=dict(value=value,se=math.sqrt(value*(1-value)/counts[den]),denominator=counts[den])
    return out

def main():
    cfg=json.loads((ROOT/'config/probe.json').read_text());models=json.loads((ROOT/'config/models.json').read_text())['pairs'];out=Path(cfg['output']);out.mkdir(parents=True,exist_ok=True)
    rows=[];controls={};tick=time.monotonic()
    for n4 in cfg['n4']:
      model=next(m for m in models if m['quad'][0]==n4)
      for si,schedule in enumerate(cfg['schedules']):
       for pi,profile in enumerate(cfg['profiles']):
        points=cfg['curve_points'] if profile['id'] in cfg['sweep_profiles'] and schedule in cfg['sweep_schedules'] else [[.001,.002]]
        for vi,(p,pc) in enumerate(points):
          c,d,m,events=build(model,p,pc,schedule,profile);probs,drop=exact_distribution(d,m)
          tag=f"n{n4}_{schedule}_{profile['id']}_p{p:g}_c{pc:g}"
          row=dict(tag=tag,n4=n4,p=p,pccz=pc,schedule=schedule,profile=profile['id'],alpha=float(probs[0]),drop_one_detector=drop,post_start=m['post_start'],npost=m['npost'],circuit_sha256=hashlib.sha256(str(c).encode()).hexdigest())
          if p==.001 and pc==.002:
            shots=cfg['conditional_shots'] if profile['id']=='sd6' else cfg['control_shots']
            sample=sample_conditions(c,m,model,shots,cfg['seed']+n4*1000+si*100+pi)
            sample['z']=(sample['acceptance']-row['alpha'])/math.sqrt(row['alpha']*(1-row['alpha'])/shots)
            row['mc']=sample
          if profile['id']=='sd6' or (p==.001 and pc==.002 and schedule in cfg['sweep_schedules']):
            # Machine-readable gate arguments avoid Stim string's p rounding.
            ops=[dict(gate=op.name,args=op.gate_args_copy(),targets=[t.value if not t.is_measurement_record_target else 'rec['+str(t.value)+']' for t in op.targets_copy()]) for op in c]
            controls[tag]=dict(ops=ops,meta={k:m[k] for k in ('post_start','npost','n3','n4')},noise_events=events)
          rows.append(row)
      print(json.dumps(dict(n4=n4,rows=len(rows),elapsed=time.monotonic()-tick)),flush=True)
    result=dict(format='qldpc.convention-probe.v1',rows=rows,wall_seconds=time.monotonic()-tick,limits=['Finite diagnostic profiles, not identified author circuit.','No model is adopted by matching source data.','Exact means deterministic DEM expectation in float64, not rigorous interval arithmetic.','Conditional acceptance uses distinct denominators and Monte Carlo uncertainty.','Logical error rate is outside this focused experiment.'])
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');(out/'circuits.json').write_text(json.dumps(controls)+'\n')
    (out/'source_hashes.json').write_text(json.dumps({str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(ROOT.rglob('*')) if f.is_file() and '.pragent' not in f.parts and f.suffix in ('.py','.json','.lock') and 'outputs' not in f.parts},indent=2)+'\n')

if __name__=='__main__':main()
