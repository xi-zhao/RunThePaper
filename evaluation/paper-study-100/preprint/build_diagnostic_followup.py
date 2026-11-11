#!/usr/bin/env python3
"""Reconcile legacy diagnostic labels with explicit archived statements.

This is documentary analysis, not scientific acceptance or a new numerical run.
"""
import csv
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ANC=HERE/'anc'
SOURCE='43a64cd03824edb136b549f352412e8d263d9361'
FINDINGS={
 '10.1038-s41467-025-67768-4': (
  'Calibration and benchmark definitions are incomplete; aggregate noise models reproduce trends but not all source curves.',
  'Gate/readout calibration, per-round noise and surface injection parameters are not specified in the recorded source contract.',
  'Resolve source calibration and independently test source alignment; do not infer a code defect or blame the source solely from curve disagreement.'),
 '1805.00931': (
  'Executed data use smaller Hilbert spaces, ensembles and transfer times; the full-scale implementations have not completed.',
  'T001/T002 use L=8 and 128 samples rather than L=15 and 9490; T004 uses t=7 rather than t=13. Separate high-time CUDA targets have resource diagnostics.',
  'Run and attest the declared full-scale campaign; smaller-system consistency does not establish source-scale agreement.'),
 '1807.01815': (
  'Reduced-size dynamics and unexecuted full-scale campaigns coexist with missing source size/procedure specifications.',
  'The target ledger separates code-ready MPS/quench campaigns from accepted data; some original quench sizes and the level-statistics size sequence are not printed.',
  'Clarify the missing size/procedure contract and complete the declared full-scale/convergence runs before quantitative acceptance.'),
 '1807.10676': (
  'Finite sampling grids support qualitative/topological checks; paper-scale theory and licensed DFT campaigns are not attested.',
  'Ten legacy unresolved theory targets retain explicit finite-resolution gaps. The separate DFT scope requires a licensed VASP/PAW campaign.',
  'Execute the higher-resolution convergence campaign; obtain the licensed DFT environment for the separate external targets. Do not equate a finite grid with a numerical defect.'),
 '2407.01296': (
  'Full-size and dense-grid computations remain unexecuted; selected eigenstate energies and some geometric conventions are not fixed by the source.',
  'T004/T005/T006/T008 declare unrun scale/sampling profiles; T007 additionally lacks selected eigenstate energies.',
  'Complete the declared profiles and resolve state-selection/convention inputs; reduced runs alone cannot establish the missing comparisons.'),
 '2506.06669': (
  'Legacy targets mix theory/experimental scope, missing hardware calibration and unspecified random seeds/grids. A separate pulse-sensitive discrepancy has a recorded follow-up diagnosis.',
  'T001/T003/T005 are auxiliary source-schematic/experimental counterparts in the item ledger. D001 is attributed by the scorecard to unspecified channel-resolved pulse functions/timing, but its cited detailed test JSON is absent from the public snapshot.',
  'Reconcile eligible scope and calibration; provide the D001 pulse-comparison evidence and independently verify it before accepting the attribution.'),
 '2510.12880': (
  'The legacy T002 label concerns unavailable solver settings despite recorded marker agreement; five separate source claims lack implementations.',
  'The ledger records T002 25/25 marker comparisons and explicit missing eigensolver/threshold/tolerance metadata. V003-V007 are unimplemented open-boundary/parity/perturbative claims.',
  'Validate solver/degeneracy robustness and implement V003-V007 with claim-specific tests; do not call the known missing implementation a mysterious physics failure.'),
 '2607.02157': (
  'The detailed state is out of sync with target-specific compute diagnostics; a provenance-bound full-scale campaign has not completed.',
  'All three scorecard targets now diagnose compute_capacity_shortfall. The resource benchmark enumerates 12665500 sequence evaluations, 1125000000 filter updates and 400101 eigendecompositions; historical arrays are not accepted as final-run evidence.',
  'Complete and attest the frozen campaign, audit readout/configuration hashes and reconcile the derived state. Existing narrative claims are not a substitute for a bound run.')
}
inputs=[]
def read(path,required=True):
 p=subprocess.run(['git','show',f'{SOURCE}:{path}'],cwd=ROOT,capture_output=True)
 if p.returncode:
  if required:raise ValueError('Missing frozen source: '+path)
  inputs.append({'path':path,'available':False});return None
 inputs.append({'path':path,'available':True,'sha256':hashlib.sha256(p.stdout).hexdigest()})
 return p.stdout.decode()

cases=list(csv.DictReader((ANC/'reason_cases.csv').open()))
targets=list(csv.DictReader((ANC/'reason_targets.csv').open()))
selected={r['paper_id'] for r in cases if r['count_in_reason_table']=='True' and 'unresolved' in r['open_root_categories'].split(' | ')}
assert selected==set(FINDINGS)
case_rows=[];target_rows=[]
for pid in sorted(selected):
 state_targets=[t for t in targets if t['paper_id']==pid and t['root_cause']=='unresolved' and t['causal_disposition']!='not_required']
 score_path=f'cases/{pid}/outputs/checks/similarity_scorecard.json'
 score=json.loads(read(score_path));by_id={t['target_id']:(i,t) for i,t in enumerate(score['targets'])}
 doc_refs=[]
 for name in ['CONSISTENCY_REPORT.md','TARGET_LEDGER.md']:
  path=f'cases/{pid}/docs/{name}';text=read(path)
  doc_refs.append(path)
 for t in state_targets:
  index,new=by_id[t['target_id']]
  diag=new.get('evaluation',{}).get('causal_diagnosis',{})
  root=diag.get('root_cause',{}).get('category','')
  gap=new.get('remaining_gap','')
  assert gap, (pid,t['target_id'])
  target_rows.append({'paper_id':pid,'target_id':t['target_id'],'legacy_root':t['root_cause'],
   'scorecard_root':root,'explicit_remaining_gap':gap,
   'scorecard_direct_statement':diag.get('direct_cause',{}).get('statement',''),
   'source_pointer':f'{score_path}#/targets/{index}','scientific_reassessment':'not_performed'})
 finding,detail,next_step=FINDINGS[pid]
 case_rows.append({'paper_id':pid,'legacy_target_count':len(state_targets),'documented_blocker':finding,
  'specific_evidence':detail,'remaining_verification':next_step,'source_docs':' | '.join(doc_refs),
  'conclusion_level':'documentary_reconciliation_not_scientific_acceptance'})
benchmark=json.loads(read('cases/2607.02157/outputs/checks/resource_benchmark.json'))
assert benchmark['paper_exact_workload']['total_sequence_evaluations']==12665500
assert benchmark['available_accelerator_boundary']['completed_attested_paper_run'] is False
missing_path='cases/2506.06669/outputs/checks/implementation_closure/D001.json'
assert read(missing_path,required=False) is None
assert len(target_rows)==44
updated=[r for r in target_rows if r['scorecard_root']!='unresolved']
assert len(updated)==3 and {r['paper_id'] for r in updated}=={'2607.02157'}
summary={'source_commit':SOURCE,'cases_examined':8,'legacy_targets_examined':44,
 'legacy_targets_with_explicit_gap_statements':44,'targets_with_updated_structured_diagnosis':3,
 'remaining_legacy_unresolved_codes':41,'diagnosis_accepted_by_new_scientific_review':False,
 'missing_public_supporting_file':missing_path,
 'interpretation':'The eight-case count measures unreconciled causal records, not eight unexplained physical failures. Explicit boundaries exist; documentation does not by itself establish causal correctness.',
 'inputs':inputs}
for name,rows in [('diagnostic_followup_cases.csv',case_rows),('diagnostic_followup_targets.csv',target_rows)]:
 with (ANC/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
(ANC/'diagnostic_followup_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
lines=['# 八个旧归因记录的复查','', '这是公开冻结记录的交叉核对，不是新一轮科学验收。8个案例共44条旧记录都有具体边界说明；其中3条已有更新的结构化诊断，41条仍保留旧unresolved编码。不能把这个元数据计数解释为8个完全不知原因的物理失败。','']
for r in case_rows:
 lines.extend([f"## {r['paper_id']}",'',r['documented_blocker'],'',r['specific_evidence'],'', 'Still required: '+r['remaining_verification'],'', 'Evidence: '+r['source_docs'],''])
(HERE/'qa/DIAGNOSTIC_FOLLOWUP.md').write_text('\n'.join(lines).rstrip()+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='inputs'},indent=2))
