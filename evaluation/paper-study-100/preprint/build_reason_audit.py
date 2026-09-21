#!/usr/bin/env python3
"""Extract recorded impediments; never infer new case outcomes or root causes."""
import collections
import csv
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE='43a64cd03824edb136b549f352412e8d263d9361'
ANC=HERE/'anc'
roster=list(csv.DictReader((ANC/'overview_papers.csv').open()))
assert len(roster)==len({r['paper_id'] for r in roster})==100
CATEGORIES={
 'source_or_external_input': ('Source or external input unavailable', {'publication_underspecified','external_dependency_unavailable'}, 'Obtain the missing parameter, definition, reference or external resource; rerun the fixed comparison.'),
 'compute_capacity': ('Compute capacity', {'compute_capacity_shortfall'}, 'Execute the declared full-scale campaign and its convergence checks on a suitable backend.'),
 'method_or_scope': ('Method, capability or scope limitation', {'system_capability_limit','reproduction_method_gap','scope_definition_gap'}, 'Repair or extend the method/scope and retest the original scientific requirement.'),
 'result_discrepancy': ('Scientific result discrepancy', {'paper_claim_discrepancy'}, 'Independently review the equations, implementation and source claim; a paper error is not established.'),
 'evidence_process': ('Evidence or review process gap', {'review_or_evidence_process_gap'}, 'Repair evidence links and obtain valid execution and review records.'),
 'unresolved': ('Root cause unresolved', {'unresolved'}, 'Run discriminating checks before choosing between a code defect and an external limitation.'),
}
case_rows=[]; target_rows=[]; inputs=[]
for p in roster:
 pid=p['paper_id']; summary_status=p['science']
 if summary_status=='unavailable':
  case_rows.append({'paper_id':pid,'title':p['title'],'summary_science':summary_status,'detail_science':'unavailable','science_states_match':'unavailable','count_in_reason_table':False,'open_root_categories':'','review_status':p['independent_review'],'diagnostic_target_ids':'','source_pointer':'','note':'No archived assessment for this roster identity; no failure cause inferred.'})
  continue
 path=f'cases/{pid}/outputs/checks/authoritative_reproduction_state.json'
 raw=subprocess.check_output(['git','show',f'{SOURCE}:{path}'],cwd=ROOT)
 inputs.append({'path':path,'sha256':hashlib.sha256(raw).hexdigest()})
 d=json.loads(raw);assert d['paper_id']==pid
 detailed=d['dimensions']['science'];match=summary_status==detailed
 cats=set();tids=[]
 for i,t in enumerate(d['targets']):
  opened=t.get('causal_disposition')!='not_required'
  root=t.get('root_cause','')
  for key,(_,codes,_) in CATEGORIES.items():
   if opened and root in codes:cats.add(key)
  if t.get('blockers') or opened:tids.append(t['target_id'])
  target_rows.append({
   'paper_id':pid,'target_id':t['target_id'],'summary_science':summary_status,'detail_science':detailed,
   'target_science':t.get('science_status',''),'causal_disposition':t.get('causal_disposition',''),
   'root_cause':root,'root_cause_confidence':t.get('root_cause_confidence',''),
   'direct_cause':t.get('direct_cause',''),'direct_cause_statement':t.get('direct_cause_statement',''),
   'root_cause_statement':t.get('root_cause_statement',''),'code_fault_status':t.get('code_fault_status',''),
   'next_discriminating_test':t.get('next_discriminating_test',''),
   'science_reasons':' | '.join(t.get('science_reasons',[])),
   'blockers':' | '.join(t.get('blockers',[])),
   'source_pointer':f'{path}#/targets/{i}'})
 case_rows.append({'paper_id':pid,'title':p['title'],'summary_science':summary_status,'detail_science':detailed,
  'science_states_match':match,'count_in_reason_table':match and summary_status in ['failed','pending'],
  'open_root_categories':' | '.join(sorted(cats)),'review_status':p['independent_review'],
  'diagnostic_target_ids':' | '.join(tids),'source_pointer':path,
  'note':'Summary and detailed science states disagree; reconcile in PRAgent before assigning a single current cause.' if not match else 'Recorded open diagnostic themes; multiple causes may coexist and individual targets can already pass.'})

selected=[r for r in case_rows if r['count_in_reason_table']]
frequency=[]
for key,(label,_,action) in CATEGORIES.items():
 counts={s:sum(r['summary_science']==s and key in r['open_root_categories'].split(' | ') for r in selected) for s in ['failed','pending']}
 frequency.append({'category':key,'label':label,**counts,'total':sum(counts.values()),'next_step':action})
mismatch=[r for r in case_rows if r['science_states_match'] is False]
summary={'source_commit':SOURCE,'scope':'recorded_impediments_not_new_causal_adjudication',
 'cohort_papers':100,'available_detailed_states':len(inputs),'target_rows':len(target_rows),
 'focus_papers':sum(r['summary_science'] in ['failed','pending'] for r in case_rows),
 'reason_table_denominators':dict(collections.Counter(r['summary_science'] for r in selected)),
 'science_snapshot_mismatches':[{'paper_id':r['paper_id'],'summary':r['summary_science'],'detail':r['detail_science']} for r in mismatch],
 'excluded_focus_mismatch_ids':[r['paper_id'] for r in mismatch if r['summary_science'] in ['failed','pending']],
 'reason_counts':frequency,'reason_categories_overlap':True,'independent_scientific_reassessment':False,
 'category_root_codes':{k:sorted(v[1]) for k,v in CATEGORIES.items()},'inputs':inputs}
for name,rows in [('reason_cases.csv',case_rows),('reason_targets.csv',target_rows),('reason_counts.csv',frequency)]:
 with (ANC/name).open('w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');writer.writeheader();writer.writerows(rows)
(ANC/'reason_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
assert summary['focus_papers']==63 and len(selected)==59 and len(mismatch)==6
assert set(summary['reason_table_denominators'])=={'failed','pending'}
print(json.dumps({k:v for k,v in summary.items() if k not in ['inputs','category_root_codes']},indent=2))
