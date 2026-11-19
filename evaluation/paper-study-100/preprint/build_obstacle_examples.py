#!/usr/bin/env python3
"""Trace illustrative diagnostic narratives to frozen public records."""
import hashlib
import json
from pathlib import Path
import subprocess
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE='43a64cd03824edb136b549f352412e8d263d9361'
choices=[
 ('10.1103-PhysRevLett.124.113601','T001','source_identifiability',
  'The archived diagnosis reports different observables under publication-compatible conventions.',
  'This does not establish a false physical claim or independently exclude implementation error.'),
 ('2502.20558','T001','implementation_scope',
  'The archived implementation lacks the required surface-code circuit and lifecycle-aware decoder.',
  'Passing a repetition-code mechanism test does not validate the original surface-code observable.'),
 ('1709.03478','T002','execution_requirement',
  'The archived diagnosis reports a measured block and an unexecuted full campaign.',
  'Resource allocation, scheduling and backend choices are not independently separated; no impossibility claim.'),
]
examples=[]
for pid,tid,question,supported,limit in choices:
 path=f'cases/{pid}/outputs/checks/authoritative_reproduction_state.json'
 raw=subprocess.check_output(['git','show',f'{SOURCE}:{path}'],cwd=ROOT)
 d=json.loads(raw);matches=[(i,t) for i,t in enumerate(d['targets']) if t['target_id']==tid];assert len(matches)==1
 i,t=matches[0]
 examples.append({'paper_id':pid,'target_id':tid,'diagnostic_question':question,
  'source_pointer':path+f'#/targets/{i}','source_file_sha256':hashlib.sha256(raw).hexdigest(),
  'archived_target_record':t,'supported_interpretation':supported,'interpretation_limit':limit,
  'underlying_tests_independently_rerun_for_report':False})
resource=examples[-1]['archived_target_record']['root_cause_statement']
assert '2784' in resource and '27.004229' in resource
out={'source_commit':SOURCE,'selection':'Illustrative selection of source identifiability, implementation scope and execution requirement; not representative sampling.',
 'purpose':'Trace manuscript narratives to archived records, not estimate cause prevalence.',
 'examples':examples,'resource_arithmetic':{'reported_tasks':2784,'reported_seconds_per_stationary_block':27.004229,
 'baseline_cpu_hours':2784*27.004229/3600,'scope':'Arithmetic from archived statements, not a new timing run or a validated bound for every task kind.'},
 'new_solver_runs':0,'new_independent_causal_verdicts':0}
(HERE/'anc/obstacle_examples.json').write_text(json.dumps(out,indent=2)+'\n')
print('Saved three source-linked illustrative diagnoses; no new causal verdicts.')
