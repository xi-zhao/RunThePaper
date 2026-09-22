#!/usr/bin/env python3
"""Editorial attribution domains from recorded diagnoses, not new causal verdicts."""
import collections
import csv
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ANC=HERE/'anc'
def read(name):return list(csv.DictReader((ANC/name).open()))
def write(name,rows):
 with (ANC/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
cases=read('reason_cases.csv');targets=read('reason_targets.csv')
followup={(r['paper_id'],r['target_id']):r for r in read('diagnostic_followup_targets.csv')}
selected={r['paper_id'] for r in cases if r['count_in_reason_table']=='True'}
rules={
 'publication_underspecified':('paper','reported_information_gap','Source record reports missing or ambiguous publication inputs; exact-replay limits do not establish a wrong physical conclusion.'),
 'paper_claim_discrepancy':('paper','recorded_claim_discrepancy','Publication-side discrepancy attribution retained at its recorded confidence; not newly confirmed as a paper error.'),
 'system_capability_limit':('agent','implementation_or_method','Current implementation or method does not establish the original target; this does not necessarily identify a code bug.'),
 'reproduction_method_gap':('agent','implementation_or_method','Current method lacks the scientific object or proof required by the target.'),
 'scope_definition_gap':('agent','scope','The chosen reproduction scope does not establish the full target.'),
 'review_or_evidence_process_gap':('agent','evidence_or_review','Workflow evidence or review is incomplete; no numerical fault inferred.'),
 'unresolved':('agent','diagnostic_record_maintenance','Agent workflow must reconcile the old diagnostic record; this assigns record maintenance, not the physical mismatch, to Agent.'),
 'compute_capacity_shortfall':('compute','recorded_resource_limit','Declared full-scale campaign exceeds completed resource allocation; an unexecuted job alone is not used to infer compute shortage.'),
 'external_dependency_unavailable':('','external_access_unallocated','Source access, software licensing or an unattested computing platform is not automatically a paper defect, compute shortage or missing experimental apparatus.'),
}
rows=[]
for r in targets:
 if r['paper_id'] not in selected or r['causal_disposition']=='not_required':continue
 domain,subtype,boundary=rules[r['root_cause']]
 domains=[domain] if domain else []
 f=followup.get((r['paper_id'],r['target_id']))
 extra=''
 if f and f['scorecard_root']=='compute_capacity_shortfall':
  domains.append('compute');extra='Frozen scorecard has an updated compute-capacity diagnosis; derived-state reconciliation is still an Agent workflow task.'
 rows.append({**r,'attribution_domains':' | '.join(domains),'attribution_subtype':subtype,'interpretation_boundary':boundary,
              'followup_note':extra,'followup_gap':f['explicit_remaining_gap'] if f else '',
              'followup_pointer':('anc/diagnostic_followup_targets.csv#'+r['paper_id']+'/'+r['target_id']) if f else '',
              'new_independent_causal_verdict':False})
bycase=collections.defaultdict(list)
for r in rows:bycase[r['paper_id']].append(r)
case_rows=[]
for r in cases:
 rr=bycase[r['paper_id']]
 domains=sorted({v for t in rr for v in t['attribution_domains'].split(' | ') if v})
 unallocated=[t['target_id'] for t in rr if not t['attribution_domains']]
 case_rows.append({'paper_id':r['paper_id'],'title':r['title'],'summary_science':r['summary_science'],
  'count_in_table':r['count_in_reason_table'],'attribution_domains':' | '.join(domains),
  'unallocated_external_targets':' | '.join(unallocated),
  'equipment_attribution':'not_established_from_recorded_diagnostics',
  'new_independent_causal_verdict':False})
frequency=[]
for key,label in [('paper','Paper information or claims'),('agent','Agent implementation or workflow'),('compute','Compute capacity'),('equipment','Experimental equipment')]:
 counts={s:sum(r['count_in_table']=='True' and r['summary_science']==s and key in r['attribution_domains'].split(' | ') for r in case_rows) for s in ['failed','pending']}
 frequency.append({'domain':key,'label':label,'failed':counts['failed'] if key!='equipment' else '',
  'pending':counts['pending'] if key!='equipment' else '', 'total':sum(counts.values()) if key!='equipment' else '',
  'count_status':'recorded_domain_count' if key!='equipment' else 'not_established_not_zero'})
source_names=['reason_cases.csv','reason_targets.csv','diagnostic_followup_targets.csv']
summary={'source_commit':json.loads((ANC/'reason_summary.json').read_text())['source_commit'],
 'scope':'editorial_domains_of_recorded_limitations_not_confirmed_exclusive_root_causes',
 'cohort_papers':100,'case_denominator':len(selected),'failed':27,'pending':32,'open_target_rows':len(rows),
 'counts':frequency,'categories_overlap':True,'mapping_rules':rules,
 'equipment_status':'No standalone equipment-unavailability attribution is established by this diagnostic extraction; missing calibration arrays do not prove missing apparatus. Blank is not zero.',
 'unallocated_external_target_count':sum(not r['attribution_domains'] for r in rows),
 'unallocated_external_case_ids':sorted({r['paper_id'] for r in rows if not r['attribution_domains']}),
 'cases_without_assigned_domain':[r['paper_id'] for r in case_rows if r['count_in_table']=='True' and not r['attribution_domains']],
 'source_material_access_warning':'Unavailable supplements and missing external datasets remain unallocated unless a source audit identifies a publication omission.',
 'new_independent_causal_verdicts':0,'input_hashes':{name:hashlib.sha256((ANC/name).read_bytes()).hexdigest() for name in source_names}}
assert len(selected)==59 and len(case_rows)==100
assert len(rows)==len({(r['paper_id'],r['target_id']) for r in rows})
assert summary['unallocated_external_target_count']==27
assert [r['total'] for r in frequency]==[48,33,10,'']
for name,data in [('responsibility_targets.csv',rows),('responsibility_cases.csv',case_rows),('responsibility_counts.csv',frequency)]:write(name,data)
(ANC/'responsibility_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ['case_denominator','open_target_rows','counts','cases_without_assigned_domain']},indent=2))
