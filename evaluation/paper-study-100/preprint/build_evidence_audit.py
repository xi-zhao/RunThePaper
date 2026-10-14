#!/usr/bin/env python3
"""Audit public record consistency and evidence scope; never run case code."""
import collections,csv,hashlib,io,json,math,posixpath,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]; ANC=HERE/'anc'
SOURCE='43a64cd03824edb136b549f352412e8d263d9361'
manifest={}; local_manifest={}
paths=set(subprocess.check_output(['git','ls-tree','-r','--name-only',SOURCE],cwd=ROOT,text=True).splitlines())
def raw(path):
 b=subprocess.check_output(['git','show',f'{SOURCE}:{path}'],cwd=ROOT);manifest[path]=hashlib.sha256(b).hexdigest();return b.decode()
def get(path):return json.loads(raw(path))
def write(name,rows):
 with (ANC/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
def local(name):
 data=(ANC/name).read_bytes();local_manifest[name]=hashlib.sha256(data).hexdigest();return list(csv.DictReader(io.StringIO(data.decode())))
roster=local('overview_papers.csv');records=[];conflicts=[];objects=[];blockers=[];by_pid={};A={};D={}
for p in roster:
 pid=p['paper_id'];r={'paper_id':pid,'historical_reproduced_check_percent':p['reproduced_percent'],'historical_all_checks_reproduced':bool(p['reproduced_percent']) and abs(float(p['reproduced_percent'])-100)<1e-9}
 if p['science']=='unavailable':
  r.update({'summary_available':False,'detail_available':False,'object_records':0})
  records.append(r);continue
 base=f'cases/{pid}/outputs/checks/'
 a=get(base+'completion_assessment.json');d=get(base+'authoritative_reproduction_state.json');sc=get(base+'similarity_scorecard.json');A[pid]=a;D[pid]=d
 r.update({'summary_available':True,'detail_available':True,'summary_complete':a['complete'],'detail_complete':d['complete']})
 for k in sorted(set(a['dimensions'])|set(d['dimensions'])):
  av=a['dimensions'].get(k,'absent');dv=d['dimensions'].get(k,'absent');r['summary_'+k]=av;r['detail_'+k]=dv;r['agreement_'+k]=av==dv
  if av!=dv:conflicts.append({'paper_id':pid,'dimension':k,'summary_value':av,'detail_value':dv,'audit_disposition':'unconfirmed_conflicting_records','summary_pointer':base+'completion_assessment.json#/dimensions/'+k,'detail_pointer':base+'authoritative_reproduction_state.json#/dimensions/'+k})
 r['blocker_codes']=' | '.join(sorted({b['code'] for b in d.get('blockers',[])}))
 for i,b in enumerate(d.get('blockers',[])):blockers.append({'paper_id':pid,'target_id':b.get('target_id',''),'code':b['code'],'message':b.get('message',''),'source_pointer':base+f'authoritative_reproduction_state.json#/blockers/{i}'})
 score={t['target_id']:t for t in sc['targets']};targets={t['target_id']:t for t in d['targets']}
 items=d.get('reproduction_measure',{}).get('items',[]);r['object_records']=len(items)
 for idx,it in enumerate(items):
  tids=it.get('target_ids',[]);ts=[score[t] for t in tids if t in score];evs=[t.get('evaluation',{}) for t in ts]
  cond=[e.get('parameter_match','unknown') for e in evs];refs=[e.get('reference_comparison','not_available') for e in evs]
  if not tids or len(ts)!=len(tids):tier='mapping_gap'
  elif any(c in ['proxy_model','reduced_scale','paper_subset'] for c in cond):tier='limited_scope_record'
  elif any(c!='paper_exact' for c in cond):tier='conditions_unspecified'
  elif all(x in ['analytic_reference','table_exact','author_data','digitized_curve'] for x in refs):tier='numerical_reference_record'
  elif all(x in ['source_figure_only','visual_feature_contract'] for x in refs):tier='figure_or_feature_record'
  else:tier='comparison_gap_or_mixed'
  cited=set()
  for t in ts:
   for e in t.get('evidence',[]):
    if isinstance(e,str):cited.add(e.split('#')[0])
  present=[];absent=[]
  for e in sorted(cited):
   q=e if e.startswith('cases/') else f'cases/{pid}/'+e
   (present if q in paths else absent).append(q)
  objects.append({'paper_id':pid,'item_id':it['item_id'],'item_type':it.get('item_type',''),'denominator_role':it.get('denominator_role','not_recorded'),
   'source_ref':it.get('source_ref',''),'scientific_object':it.get('scientific_object',''),'target_ids':' | '.join(tids),
   'recorded_conditions':' | '.join(sorted(set(cond))),'recorded_reference_types':' | '.join(sorted(set(refs))),
   'recorded_science_states':' | '.join(sorted({targets[t].get('science_status','unknown') for t in tids if t in targets})),
   'evidence_scope':tier,'public_cited_files':' | '.join(present),'unavailable_cited_files':' | '.join(absent),
   'source_pointer':base+f'authoritative_reproduction_state.json#/reproduction_measure/items/{idx}',
   'scorecard_pointer':base+'similarity_scorecard.json','remaining_gaps':' | '.join(sorted({t.get('remaining_gap','') for t in ts if t.get('remaining_gap')})),
   'assessment_limit':'Documentary linkage/scope audit; comparator accuracy, source conditions and execution not independently revalidated.'})
 records.append(r);by_pid[pid]=r
keys=list(dict.fromkeys(k for r in records for k in r));records=[{k:r.get(k,'unavailable') for k in keys} for r in records]
full={r['paper_id'] for r in records if r['historical_all_checks_reproduced']}
review={pid for pid,a in A.items() if a['dimensions']['independent_review']=='passed'}
science={pid for pid,a in A.items() if a['dimensions']['science']=='passed'}
joints=[]
for basis,sets in [('historical_full_vs_summary_review',(full,review)),('summary_science_vs_summary_review',(science,review))]:
 x,y=sets
 for a in [True,False]:
  for b in [True,False]:
   ids=sorted(pid for pid in A if (pid in x)==a and (pid in y)==b);joints.append({'basis':basis,'row_positive':a,'column_positive':b,'cases':len(ids),'paper_ids':' | '.join(ids)})
full_dims={k:dict(collections.Counter(D[pid]['dimensions'].get(k,'absent') for pid in full)) for k in ['science','independent_review','execution','numerical_scope','paper_assessment']}
fc=collections.Counter()
for pid in full:fc.update({b['code'] for b in D[pid].get('blockers',[])})
# Audit the check metric's association semantics, without assigning new scientific outcomes.
checks=local('overview_checks.csv');claim_members=collections.defaultdict(list);primary=collections.defaultdict(list)
for c in checks:
 for cid in c['claim_ids'].split(' | '):claim_members[c['paper_id'],cid].append(c)
 if c['claim_id']:primary[c['paper_id'],c['claim_id']].append(c)
primary_vals=[];sensitivity=[]
for cl in local('overview_claims.csv'):
 key=cl['paper_id'],cl['claim_id'];cc=claim_members[key];pp=primary[key]
 if pp:primary_vals.append(sum(c['disposition']=='reproduced' for c in pp)/len(pp))
 n=len(cc);k=sum(c['disposition']=='reproduced' for c in cc)
 if 0<k<n:sensitivity.append({'paper_id':key[0],'claim_id':key[1],'checks':n,'marked_reproduced':k,'original_fraction':k/n,'fraction_after_duplicating_one_positive_check':(k+1)/(n+1),'interpretation':'Counterfactual check-list sensitivity, not a changed scientific result.'})
sensitivity.sort(key=lambda r:(-(r['fraction_after_duplicating_one_positive_check']-r['original_fraction']),r['paper_id'],r['claim_id']))
# Exact stored integer / float-resolution audit, no bound evaluation or case-code import.
qpath='cases/1811.08017/outputs/data/fig2_gate_counts.csv';q=list(csv.DictReader(io.StringIO(raw(qpath))));qexample=q[0]
methods=['qdrift','first_order_deterministic','first_order_random','higher_order_deterministic','higher_order_random'];precision=[]
for m in methods:
 n=int(qexample[m]);precision.append({'molecule':qexample['molecule'],'time':qexample['time'],'method':m,'stored_gate_count':str(n),'binary64_spacing':math.ulp(float(n)),'adjacent_integer_values_collapse':float(n)==float(n-1),'source_pointer':qpath+'#data_row=1','scope':'Representation test on archived integer only; not a bound certificate.'})
# Concrete frozen system chain; preserve missing detailed evidence instead of inventing a trajectory.
pid='2502.20558';base=f'cases/{pid}/';proxy=get(base+'outputs/checks/fig2b_proxy.json');validation=get(base+'outputs/data/implementation_validation/t001.json');final=get(base+'outputs/checks/final_disposition_evidence.json');score=get(base+'outputs/checks/similarity_scorecard.json');t=next(t for t in score['targets'] if t['target_id']=='T001');state=next(t for t in D[pid]['targets'] if t['target_id']=='T001');attempt=next(t for t in final['system_capability_attempts'] if t['target_id']=='T001')
chain={'paper_id':pid,'target_id':'T001','source_items':[r['item_id'] for r in validation['rows']],
 'proxy_check':proxy,'validation_scope':validation['scientific_scope'],'validation_acceptance':validation['scientific_acceptance'],
 'scorecard_fields':{k:t[k] for k in ['physics_status','final_reproduction_eligible','final_reproduction_gate','evaluation','remaining_gap']},
 'final_attempt':attempt,'detailed_state':state,
 'cited_attempt_file_presence':{k:(base+attempt[k] in paths) for k in ['data','check','attestation']},
 'public_state_history':subprocess.check_output(['git','log',SOURCE,'--format=%H','--',base+'outputs/checks/authoritative_reproduction_state.json'],cwd=ROOT,text=True).splitlines(),
 'inference':'A frozen distinction between a passing proxy check and a rejected paper target. No timestamped independent-review intervention or repaired surface-code implementation is established.'}
qchecks=get('cases/1811.08017/outputs/checks/target_checks.json');raw('cases/1811.08017/code/src/qdrift_resources/model.py');raw('cases/0709.0548/code/src/dqc1_discord/model.py');raw('cases/0709.0548/docs/NUMERICAL_METHODS.md');raw('cases/0709.0548/code/config/paper_scale.json');raw('cases/0709.0548/code/scripts/run_reproduction_impl.py')
summary={'source_commit':SOURCE,'audit_unit':'Public evidence record, not a new scientific acceptance verdict','cohort_papers':100,'available_case_pairs':len(A),
 'object_records':len(objects),'cases_with_object_records':sum(r['object_records']>0 for r in records),
 'cases_without_object_inventory':[pid for pid in A if by_pid[pid]['object_records']==0],
 'evidence_scope_counts':dict(collections.Counter(o['evidence_scope'] for o in objects)),
 'interpretation_of_scope_counts':'Counts of archived object records with distinct granularity; not success rates or established direct-result agreement.',
 'dimension_conflicts':dict(collections.Counter(c['dimension'] for c in conflicts)),
 'historical_full_ids':sorted(full),'summary_review_passed_ids':sorted(review),'full_and_summary_review_intersection':sorted(full&review),
 'summary_science_and_review_intersection':sorted(science&review),'full_detail_dimensions':full_dims,'full_detail_blocker_case_counts':dict(fc),
 'joint_tables':joints,'agreed_dimensions':{},'claim_check_memberships':sum(len(v) for v in claim_members.values()),
 'primary_only_mean_fraction':sum(primary_vals)/len(primary_vals),'primary_only_claim_denominator':len(primary_vals),
 'historical_metric_interpretation':'Claim-weighted fraction of associated checks carrying an archived reproduced label; supporting/shared associations included. Not result reproduction degree.',
 'new_solver_runs':0,'new_scientific_acceptance_verdicts':0,
 'new_documentary_findings':['Cross-record conflicts and joint-set relationships','Source-result linkage and recorded comparison scope','Stored integer binary64 resolution','Frozen proxy-to-target acceptance distinction'],
 'derived_input_hashes':local_manifest,
 'inputs':[{'path':p,'sha256':h} for p,h in sorted(manifest.items())]}
for dim in ['numerical_scope','science','independent_review']:
 positive='complete' if dim=='numerical_scope' else 'passed'
 summary['agreed_dimensions'][dim]={'agreed_positive':sum(a['dimensions'][dim]==D[pid]['dimensions'][dim]==positive for pid,a in A.items()),
 'agreed_other':sum(a['dimensions'][dim]==D[pid]['dimensions'][dim]!=positive for pid,a in A.items()),
 'conflict':sum(a['dimensions'][dim]!=D[pid]['dimensions'][dim] for pid,a in A.items()),'unavailable':3}
assert len(records)==100 and len(A)==97 and len(full)==len(review)==26 and len(full&review)==0
assert len(objects)==len({(r['paper_id'],r['item_id']) for r in objects})==3241
for name,rows in [('audit_case_states.csv',records),('audit_state_conflicts.csv',conflicts),('audit_result_objects.csv',objects),('audit_completion_blockers.csv',blockers),('audit_joint_states.csv',joints),('audit_check_sensitivity.csv',sensitivity[:10]),('audit_precision.csv',precision)]:write(name,rows)
for name,obj in [('audit_summary.json',summary),('audit_system_chain.json',chain),('audit_qdrift_check_record.json',qchecks)]: (ANC/name).write_text(json.dumps(obj,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['inputs','historical_full_ids','summary_review_passed_ids','joint_tables']},indent=2))
