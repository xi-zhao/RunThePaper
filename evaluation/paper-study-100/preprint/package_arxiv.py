#!/usr/bin/env python3
"""Package an explicit arXiv source allowlist and verify a clean-directory build."""
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
require(not any(s in text for s in ['/Users/','/Volumes/','fontspec','write18']),'Nonportable LaTeX source')
files=['main.tex','authors.tex',*figs,'anc/result_summary.json','anc/input_manifest.json','anc/cohort_100.csv','anc/selection_provenance.json','anc/overview_summary.json','anc/overview_papers.csv','anc/overview_claims.csv','anc/overview_checks.csv']
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
    pages=len(a)
summary=json.loads((HERE/'anc/result_summary.json').read_text())
require(summary['new_solver_runs']==0,'Solver execution boundary changed')
require(summary['one_excitation']['state_time_slices']+summary['two_excitation']['state_time_slices']==4509,'State-time count mismatch')
require(summary['one_excitation']['max_density_sum_error']<3e-15 and summary['two_excitation']['max_density_sum_error']<3e-15,'Conservation statement contradicted')
author_pending='author metadata pending' in (HERE/'authors.tex').read_text()
metadata={
    'title':'PRAgent: Building Reproducible Physics Research Workflows with AI Agents',
    'subtitle':'A Technical Report on a 100-Paper Project',
    'authors':[], 'affiliations':[], 'license':None,
    'suggested_primary_category':'physics.comp-ph','optional_cross_list':'quant-ph',
    'category_status':'editorial_suggestion_not_confirmed_by_arxiv',
    'comments':f'Technical report, {pages} pages, 5 main figures and a supplementary cohort figure. Code and public research artifacts: https://github.com/xi-zhao/RunThePaper',
    'abstract':'Turning a physics paper into executable research requires mathematical interpretation, numerical implementation and evidence that connects computed outputs to the source problem. We present PRAgent, a human-guided workflow for AI-assisted scientific reproduction, together with RunThePaper, a public collection of research cases. The workflow connects source objects and equation-level reasoning to case-specific code, generated arrays, physical diagnostics and versioned reports. We describe its use in a fixed 100-paper project and examine three implemented studies: resource estimation for randomized Hamiltonian simulation, interacting quantum walks and quantum discord. Reanalysis of archived quantum-walk arrays gives particle-number residuals below $3\\times10^{-15}$ across 4,509 stored state-time slices. Resource-estimation tables recover distinct gate-count scalings, while discord ensembles expose the importance of separating finite-instance calculations from analytical references. These examples demonstrate concrete implementations and inspectable computational outputs across different numerical tasks. The contribution is a research workflow and its reusable artifacts, rather than a new physical theory or a controlled benchmark of autonomous agents. We provide source-linked figures, analysis code and a unified cohort record to support inspection and further development.',
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
