#!/usr/bin/env python3
"""Package an explicit arXiv source allowlist and verify a clean-directory build."""
import collections
import math
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent

def require(condition,message):
    if not condition:raise ValueError(message)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

text=(HERE/'main.tex').read_text()
figs=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',text)
require(len(figs)==len(set(figs))==6,'Expected five main figures and one cohort figure')
require(figs==['figures/fig1_workflow.pdf','figures/fig2_resources.pdf','figures/fig3_quantum_walks.pdf','figures/fig4_discord.pdf','figures/fig_overall_reproduction.pdf','figures/figS1_cohort_matrix.pdf'],'Figure order differs from capability narrative')
require(not any(s in text for s in ['/Users/','/Volumes/','fontspec','write18']),'Nonportable LaTeX source')
files=['main.tex','authors.tex',*figs,'anc/result_summary.json','anc/input_manifest.json','anc/cohort_100.csv','anc/selection_provenance.json','anc/overview_summary.json','anc/overview_papers.csv','anc/overview_claims.csv','anc/overview_checks.csv','anc/reason_summary.json','anc/reason_cases.csv','anc/reason_targets.csv','anc/reason_counts.csv','anc/diagnostic_followup_summary.json','anc/diagnostic_followup_cases.csv','anc/diagnostic_followup_targets.csv','anc/obstacle_examples.json']
files += ['anc/'+name for name in ['audit_case_states.csv','audit_state_conflicts.csv','audit_result_objects.csv','audit_completion_blockers.csv','audit_joint_states.csv','audit_check_sensitivity.csv','audit_precision.csv','audit_summary.json','audit_system_chain.json','audit_qdrift_check_record.json']]
for name in files:
    require(bool(re.fullmatch(r'[a-zA-Z0-9_+.,=/\-]+',name)),f'Unsupported filename: {name}')
    require((HERE/name).is_file(),f'Missing input: {name}')
archive=HERE/'arxiv_source_draft.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for name in files:z.write(HERE/name,name)
with tempfile.TemporaryDirectory(prefix='pragent-arxiv-check-') as td:
    root=Path(td)
    with zipfile.ZipFile(archive) as z:z.extractall(root)
    for _ in range(2):
        result=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=root,capture_output=True,text=True)
        require(result.returncode==0,result.stdout[-4000:])
    log=(root/'main.log').read_text()
    warnings=[line for line in log.splitlines() if any(w in line for w in ['Overfull','Missing character','undefined references'])]
    require(not warnings,'Layout warnings: '+repr(warnings))
    built=PdfReader(root/'main.pdf');delivered=PdfReader(HERE/'PRAgent_Technical_Report.pdf')
    a=[p.extract_text() for p in built.pages];b=[p.extract_text() for p in delivered.pages]
    require(a==b,'Packaged-source rendering differs from delivered PDF text')
    flat=re.sub(r'\s+','',''.join(a))
    roster=list(csv.DictReader((root/'anc/cohort_100.csv').open()))
    require(len(roster)==len({r['paper_id'] for r in roster})==100,'Cohort identity mismatch')
    for row in roster:require(row['paper_id'] in flat,'Missing rendered identity: '+row['paper_id'])
    overview=json.loads((root/'anc/overview_summary.json').read_text())
    paper_rows=list(csv.DictReader((root/'anc/overview_papers.csv').open()))
    claim_rows=list(csv.DictReader((root/'anc/overview_claims.csv').open()))
    check_rows=list(csv.DictReader((root/'anc/overview_checks.csv').open()))
    require({r['paper_id'] for r in paper_rows}=={r['paper_id'] for r in roster} and len(paper_rows)==100,'Overview roster mismatch')
    require(len(claim_rows)==overview['numerical_claims']==1399,'Overview claim denominator mismatch')
    require(len(check_rows)==len({r['mapping_row_id'] for r in check_rows})==overview['claim_checks']==3667,'Overview check denominator mismatch')
    require(sum(r['coverage_available']=='True' for r in paper_rows)==97,'Overview measurement coverage mismatch')
    require(all(r['reproduced_percent']=='' for r in paper_rows if r['coverage_available']=='False'),'Missing paper scores must remain empty')
    for key in ['reproduced','externally_blocked','attempted_not_reproduced','pending']:
        rebuilt=100*sum(int(r[key+'_checks'])/int(r['checks_total']) for r in claim_rows)/len(claim_rows)
        require(abs(rebuilt-overview['claim_weighted_percent'][key])<1e-9,'Overview aggregate mismatch: '+key)
    require(overview['new_scientific_verdicts']==0,'Overview scientific boundary changed')
    reasons=json.loads((root/'anc/reason_summary.json').read_text())
    reason_cases=list(csv.DictReader((root/'anc/reason_cases.csv').open()))
    reason_targets=list(csv.DictReader((root/'anc/reason_targets.csv').open()))
    require(len(reason_cases)==100 and {r['paper_id'] for r in reason_cases}=={r['paper_id'] for r in roster},'Reason ledger roster mismatch')
    require(len(reason_targets)==reasons['target_rows']==1116,'Target reason ledger mismatch')
    require(sum(r['count_in_reason_table']=='True' for r in reason_cases)==59,'Reason denominator mismatch')
    require(sum(r['science_states_match']=='False' for r in reason_cases)==6,'Snapshot discrepancy mismatch')
    for category in reasons['reason_counts']:
        for status in ['failed','pending']:
            count=sum(r['count_in_reason_table']=='True' and r['summary_science']==status and category['category'] in r['open_root_categories'].split(' | ') for r in reason_cases)
            require(count==category[status],'Reason category count mismatch')
    require(reasons['independent_scientific_reassessment'] is False,'Reason audit boundary changed')
    followup=json.loads((root/'anc/diagnostic_followup_summary.json').read_text())
    followup_cases=list(csv.DictReader((root/'anc/diagnostic_followup_cases.csv').open()))
    followup_targets=list(csv.DictReader((root/'anc/diagnostic_followup_targets.csv').open()))
    legacy_ids={r['paper_id'] for r in reason_cases if r['count_in_reason_table']=='True' and 'unresolved' in r['open_root_categories'].split(' | ')}
    require(len(followup_cases)==8 and {r['paper_id'] for r in followup_cases}==legacy_ids,'Diagnostic follow-up cohort mismatch')
    require(len(followup_targets)==len({(r['paper_id'],r['target_id']) for r in followup_targets})==44,'Diagnostic target count mismatch')
    require(all(r['explicit_remaining_gap'] for r in followup_targets),'Missing target-specific explanation')
    require(sum(r['scorecard_root']=='unresolved' for r in followup_targets)==41,'Legacy label count mismatch')
    require(followup['diagnosis_accepted_by_new_scientific_review'] is False,'Follow-up acceptance boundary changed')
    obstacles=json.loads((root/'anc/obstacle_examples.json').read_text())
    require(len(obstacles['examples'])==3,'Expected three illustrative diagnostic examples')
    original_targets={(r['paper_id'],r['target_id']):r for r in reason_targets}
    for example in obstacles['examples']:
        original=original_targets[(example['paper_id'],example['target_id'])]
        require(example['source_pointer']==original['source_pointer'],'Obstacle source mismatch')
        for field in ['direct_cause_statement','root_cause_statement','root_cause_confidence']:
            require(example['archived_target_record'][field]==original[field],'Obstacle diagnosis mismatch')
        require(example['underlying_tests_independently_rerun_for_report'] is False,'Obstacle execution boundary changed')
    require(obstacles['new_solver_runs']==obstacles['new_independent_causal_verdicts']==0,'Obstacle verdict boundary changed')
    require(not any('responsibility_' in name for name in files),'Withdrawn attribution files in source package')
    require('Attribution domain & Failed' not in text and '48 cases' not in text,'Withdrawn causal count table remains')
    audit=json.loads((root/'anc/audit_summary.json').read_text())
    def audit_rows(name):return list(csv.DictReader((root/'anc'/name).open()))
    states=audit_rows('audit_case_states.csv'); objects=audit_rows('audit_result_objects.csv')
    conflicts=audit_rows('audit_state_conflicts.csv'); joints=audit_rows('audit_joint_states.csv')
    require(len(states)==100 and {r['paper_id'] for r in states}=={r['paper_id'] for r in roster},'Audit roster mismatch')
    available=[r for r in states if r['summary_available']=='True' and r['detail_available']=='True']
    require(len(available)==audit['available_case_pairs']==97,'Audit available-state mismatch')
    require(len(objects)==len({(r['paper_id'],r['item_id']) for r in objects})==audit['object_records']==3241,'Result-object identity mismatch')
    require(len({r['paper_id'] for r in objects})==audit['cases_with_object_records']==95,'Result-object case count mismatch')
    require(dict(collections.Counter(r['evidence_scope'] for r in objects))==audit['evidence_scope_counts'],'Evidence scope counts mismatch')
    require(all(r['assessment_limit'] and r['source_pointer'] for r in objects),'Missing object audit limitation or source')
    require(dict(collections.Counter(r['dimension'] for r in conflicts))==audit['dimension_conflicts'],'State-conflict counts mismatch')
    require(audit['agreed_dimensions']==overview['record_agreement_counts'],'Figure and audit record agreement differ')
    for dim,counts in audit['agreed_dimensions'].items():
        positive='complete' if dim=='numerical_scope' else 'passed'
        require(sum(r['summary_'+dim]==r['detail_'+dim]==positive for r in available)==counts['agreed_positive'],'Agreed positive count mismatch')
        require(sum(r['summary_'+dim]!=r['detail_'+dim] for r in available)==counts['conflict'],'Conflict count mismatch')
        require(sum(counts.values())==100,'Agreement denominator mismatch')
    for row in joints:
        positive=lambda r: r['historical_all_checks_reproduced']=='True' if row['basis']=='historical_full_vs_summary_review' else r['summary_science']=='passed'
        ids={r['paper_id'] for r in available if positive(r)==(row['row_positive']=='True') and (r['summary_independent_review']=='passed')==(row['column_positive']=='True')}
        require(len(ids)==int(row['cases']) and ids==set(filter(None,row['paper_ids'].split(' | '))),'Joint-state membership mismatch')
    require(audit['full_and_summary_review_intersection']==[] and len(audit['summary_science_and_review_intersection'])==1,'Headline joint-state mismatch')
    require(all(r['summary_complete']==r['detail_complete']=='False' for r in available),'Unexpected completed case')
    for name,digest in audit['derived_input_hashes'].items():require(sha(root/'anc'/name)==digest,'Stale audit input: '+name)
    chain=json.loads((root/'anc/audit_system_chain.json').read_text())
    require(chain['scorecard_fields']['physics_status']=='passed' and chain['scorecard_fields']['final_reproduction_eligible'] is False,'Proxy acceptance distinction changed')
    require(chain['detailed_state']['science_status']=='failed' and chain['cited_attempt_file_presence']=={'data':True,'check':False,'attestation':False},'Proxy evidence boundary changed')
    precision=audit_rows('audit_precision.csv')
    for row in precision:
        n=int(row['stored_gate_count'])
        require(math.ulp(float(n))==float(row['binary64_spacing']) and (float(n)==float(n-1))==(row['adjacent_integer_values_collapse']=='True'),'Integer resolution mismatch')
    require(sum(r['adjacent_integer_values_collapse']=='True' for r in precision)==4,'Precision statement mismatch')
    require(audit['new_solver_runs']==audit['new_scientific_acceptance_verdicts']==0,'Audit scientific boundary changed')
    pages=len(a)
summary=json.loads((HERE/'anc/result_summary.json').read_text())
require(summary['new_solver_runs']==0,'Solver execution boundary changed')
require(summary['one_excitation']['state_time_slices']+summary['two_excitation']['state_time_slices']==4509,'State-time count mismatch')
require(summary['one_excitation']['max_density_sum_error']<3e-15 and summary['two_excitation']['max_density_sum_error']<3e-15,'Conservation statement contradicted')
author_pending='author metadata pending' in (HERE/'authors.tex').read_text()
manuscript=(HERE/'report.md').read_text()
report_title=re.search(r"^title: '(.+)'$",manuscript,re.M).group(1)
report_subtitle=re.search(r"^subtitle: '(.+)'$",manuscript,re.M).group(1)
report_abstract=' '.join(manuscript.split(r'\begin{abstract}',1)[1].split(r'\end{abstract}',1)[0].split())
require(bool(report_abstract),'Missing manuscript abstract')
metadata={
    'title':report_title,
    'subtitle':report_subtitle,
    'authors':[], 'affiliations':[], 'license':None,
    'suggested_primary_category':'physics.comp-ph','optional_cross_list':'quant-ph',
    'category_status':'editorial_suggestion_not_confirmed_by_arxiv',
    'comments':f'Technical report, {pages} pages, 5 main figures and a supplementary cohort figure. Code and public research artifacts: https://github.com/xi-zhao/RunThePaper',
    'abstract':report_abstract,
    'ready_for_submission':False,'submission_status':'not_submitted',
    'remaining_inputs':['Author names, order and affiliations','Author confirmation of final manuscript and responsibilities','Distribution license and account/category eligibility'],
}
# Preserve user-supplied metadata when packaging a later revision.
mp=HERE/'submission_metadata.json'
if mp.exists():
    old=json.loads(mp.read_text())
    for key in ['authors','affiliations','license']:metadata[key]=old.get(key,metadata[key])
mp.write_text(json.dumps(metadata,indent=2)+'\n')
report={'status':'passed','scope':'local_source_package_compilation_and_array_consistency','source_files':files,'pages':pages,'cohort_papers':len(roster),'author_metadata_pending':author_pending,'arxiv_submission':'not_attempted','source_zip_sha256':sha(archive),'pdf_sha256':sha(HERE/'PRAgent_Technical_Report.pdf'),'input_file_hashes':{f:sha(HERE/f) for f in files}}
(HERE/'package_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='input_file_hashes'},indent=2))
