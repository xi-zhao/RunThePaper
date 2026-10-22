#!/usr/bin/env python3
"""Check manuscript denominators, frozen inputs, full roster and rendered PDF."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()]

stats = json.loads((HERE / 'figure_data.json').read_text())
cohort = json.loads((STUDY / 'cohort.json').read_text())
roster = json.loads((HERE / 'cohort_100.json').read_text())
expected = set(cohort['retained_historical_ids']) | {r['paper_id'] for r in cohort['prospective_additions']}
require(len(roster) == len(expected) == 100, 'Cohort size changed')
require({r['paper_id'] for r in roster} == expected, 'Cohort identities changed')
require(all('cohort_group' not in r for r in roster), 'Manuscript roster must use unified presentation')
for name, expected_hash in stats['input_sha256'].items():
    require(digest(STUDY / name) == expected_hash, f'Source data changed: {name}')
records = rows(STUDY / 'data/results.jsonl')
papers = rows(STUDY / 'data/papers.jsonl')
require(len(records) == stats['evidence_records'] == 3927, 'Record denominator mismatch')
require(len(papers) == stats['public_extraction_papers'] == 97, 'Available-paper denominator mismatch')
require(sum(stats['artifact_reference_contingency'].values()) == len(records), 'Joint cells do not partition records')
require(sum(stats['original_inventory_types'].values()) == stats['original_inventory_records'] == 3666, 'Inventory denominator mismatch')
unique_targets = {(r['paper_id'], t['target_id']) for r in records for t in r['archived_targets']}
require(len(unique_targets) == stats['unique_archived_targets'] == 1116, 'Repeated target links inflated denominator')
require(sum(stats['unique_target_parameter_declarations'].values()) == len(unique_targets), 'Target labels do not partition target identities')
for row in roster:
    if not row['public_extraction_available']:
        require(all(row[k] is None for k in ['public_python_present','public_data_present','stored_review_present','unmapped_targets_present','unresolved_references_present','evidence_record_count']), 'Unassessed measurement replaced by zero or false')
require(all(r['review']['outcome'] == 'not_evaluated' for r in records), 'Extraction promoted to scientific verdict')
require(stats['scientific_success_rate'] is None, 'Unestablished science rate must stay undefined')
md = (HERE / 'paper.md').read_text()
require(not re.search(r'97\s*[+＋]\s*3|historical group|prospective group', md, re.I), 'Superseded grouping in manuscript')
require(len(re.findall(r'^\d+\. ',md,re.M)) == 8, 'Reference list count changed')
for file in ['fig1_evidence_chain.pdf','fig2_availability.pdf','fig3_units_and_conditions.pdf','figS1_cohort_matrix.pdf']:
    require((HERE / 'figures' / file).is_file(), f'Missing figure: {file}')
pdf = HERE / 'PRAgent_100_Papers_Manuscript.pdf'
reader = PdfReader(pdf)
text_pages = [p.extract_text() or '' for p in reader.pages]
text = '\n'.join(text_pages)
require(len(reader.pages) == 10, 'Review pagination after layout change')
require(all(len(p) > 200 for p in text_pages), 'Empty or broken PDF page')
require('\ufffd' not in text, 'Replacement glyph in PDF text')
for phrase in ['3,666','1,721','2,114','1,116','Supplementary Fig. S1','References','Conclusion']:
    require(phrase in text, f'Missing rendered content: {phrase}')
normalized = re.sub(r'\s+', '', text)
for row in roster:
    require(re.sub(r'\s+','',row['paper_id']) in normalized, f"Identity absent from PDF supplement: {row['paper_id']}")
report = {
    'status': 'passed', 'checked_at_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'manuscript_metadata_denominators_and_rendered_content_not_scientific_acceptance',
    'cohort_papers': len(roster), 'available_public_extractions': len(papers),
    'evidence_records': len(records), 'unique_targets': len(unique_targets),
    'references': 8, 'pdf_pages': len(reader.pages),
    'approximate_markdown_word_count': len(md.split()),
    'sha256': {name: digest(HERE / name) for name in ['paper.md','paper.tex','PRAgent_100_Papers_Manuscript.pdf','figure_data.json','cohort_100.csv','cohort_100.json','claim_evidence.csv']},
}
(HERE / 'validation.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
