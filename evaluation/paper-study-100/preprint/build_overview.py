#!/usr/bin/env python3
"""Cohort-aligned descriptive reanalysis of frozen coverage and assessment records."""
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = '43a64cd03824edb136b549f352412e8d263d9361'
ANC = HERE / 'anc'
manifest = []

def frozen(path):
    raw = subprocess.check_output(['git', 'show', f'{SOURCE}:{path}'], cwd=ROOT)
    manifest.append({'path': path, 'sha256': hashlib.sha256(raw).hexdigest()})
    return raw.decode()

def csv_rows(name):
    return list(csv.DictReader(io.StringIO(frozen(f'evaluation/claim-first-100/data/{name}.csv'))))

def write_csv(name, rows):
    with (ANC / name).open('w', newline='') as stream:
        out = csv.DictWriter(stream, fieldnames=list(rows[0]))
        out.writeheader()
        out.writerows(rows)

roster = list(csv.DictReader((ANC / 'cohort_100.csv').open()))
ids = {r['paper_id'] for r in roster}
assert len(roster) == len(ids) == 100
manifest.append({'path': 'anc/cohort_100.csv', 'sha256': hashlib.sha256((ANC / 'cohort_100.csv').read_bytes()).hexdigest()})
old_papers = csv_rows('papers')
claims = [r for r in csv_rows('claims') if r['paper_id'] in ids and r['claim_kind'] == 'numerical_claim']
checks = [r for r in csv_rows('checks') if r['paper_id'] in ids]
old_summary = json.loads(frozen('evaluation/claim-first-100/data/summary.json'))
by_claim = collections.defaultdict(list)
for c in checks:
    # The archived authored-claim table includes supporting associations.
    # A check can therefore contribute to more than one claim.
    for claim_id in c['claim_ids'].split(' | '):
        by_claim[c['paper_id'], claim_id].append(c)
assert len({r['mapping_row_id'] for r in checks}) == len(checks)
claim_data = []
by_paper = collections.defaultdict(list)
labels = ['reproduced', 'externally_blocked', 'attempted_not_reproduced', 'pending']
for c in claims:
    cc = by_claim[c['paper_id'], c['claim_id']]
    assert len(cc) == int(c['checks_total']) > 0
    counts = collections.Counter(r['disposition'] for r in cc)
    assert set(counts) <= set(labels)
    row = {'paper_id': c['paper_id'], 'claim_id': c['claim_id'], 'checks_total': len(cc)}
    for label in labels:
        assert counts[label] == int(c[label + '_checks'])
        row[label + '_checks'] = counts[label]
        row[label + '_fraction'] = counts[label] / len(cc)
    by_paper[c['paper_id']].append(row)
    claim_data.append(row)
assert {c['mapping_row_id'] for r in claim_data for c in by_claim[r['paper_id'], r['claim_id']]} == {c['mapping_row_id'] for c in checks}
reference_papers = {r['paper_id']: r for r in old_papers}
papers = []
for r in roster:
    pid = r['paper_id']
    group = by_paper.get(pid, [])
    row = {'paper_id': pid, 'title': r['title'], 'coverage_available': bool(group), 'numerical_claims': len(group)}
    for label in labels:
        row[label + '_percent'] = 100 * np.mean([c[label + '_fraction'] for c in group]) if group else ''
    if group:
        assert abs(row['reproduced_percent'] - float(reference_papers[pid]['successful_claim_coverage'])) < 1e-5
    if r['public_extraction_available'] == 'True':
        assessment = json.loads(frozen(f'cases/{pid}/outputs/checks/completion_assessment.json'))
        assert assessment['paper_id'] == pid
        row['numerical_scope'] = assessment['dimensions']['numerical_scope']
        row['science'] = assessment['dimensions']['science']
        row['independent_review'] = assessment['dimensions']['independent_review']
        row['whole_paper_complete'] = assessment['complete']
    else:
        for key in ['numerical_scope', 'science', 'independent_review', 'whole_paper_complete']:
            row[key] = 'unavailable'
    papers.append(row)
measured = [r for r in papers if r['coverage_available']]
missing = [r for r in papers if not r['coverage_available']]
pooled = {label: 100 * np.mean([c[label + '_fraction'] for c in claim_data]) for label in labels}
assert abs(sum(pooled.values()) - 100) < 1e-9
summary = {
    'source_commit': SOURCE,
    'measurement': 'cohort_aligned_historical_claim_coverage_not_new_scientific_acceptance',
    'coverage_snapshot_generated_at': old_summary['generated_at'],
    'cohort_papers': len(papers), 'papers_with_coverage': len(measured),
    'papers_without_coverage': len(missing), 'missing_paper_ids': [r['paper_id'] for r in missing],
    'excluded_legacy_paper_ids': sorted(set(reference_papers) - ids),
    'numerical_claims': len(claim_data), 'claim_checks': len(checks),
    'claim_check_memberships': sum(r['checks_total'] for r in claim_data),
    'claim_mapping': 'All archived claim_ids, including supporting associations; checks may be shared across claims.',
    'claim_weighted_percent': pooled,
    'mean_paper_coverage_measured_percent': float(np.mean([r['reproduced_percent'] for r in measured])),
    'papers_with_all_recorded_checks_reproduced': int(sum(abs(r['reproduced_percent'] - 100) < 1e-9 for r in measured)),
    'whole_paper_complete_in_available_assessments': sum(r['whole_paper_complete'] is True for r in papers),
    'assessment_counts': {key: dict(collections.Counter(r[key] for r in papers)) for key in ['numerical_scope', 'science', 'independent_review']},
    'uncertainty': 'Descriptive census of archived records; no confidence intervals or missing-score imputation.',
    'new_scientific_verdicts': 0,
    'inputs': manifest,
}
figure_order = sorted(measured, key=lambda r: (-r['reproduced_percent'], r['paper_id'])) + missing
for rank, row in enumerate(figure_order, 1):
    row['figure_rank'] = rank
write_csv('overview_papers.csv', papers)
write_csv('overview_claims.csv', claim_data)
write_csv('overview_checks.csv', checks)
(ANC / 'overview_summary.json').write_text(json.dumps(summary, indent=2) + '\n')

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.linewidth': .6, 'pdf.fonttype': 42,
                     'svg.fonttype': 'none', 'axes.labelcolor': '#23384A', 'text.color': '#23384A',
                     'xtick.color': '#52616E', 'ytick.color': '#52616E'})
navy, amber, slate, light = '#285A78', '#D2A45F', '#AAB7C3', '#EEF1F4'
fig = plt.figure(figsize=(7.2, 5.9), facecolor='white')
ax1 = fig.add_axes([.10, .805, .86, .115])
ax2 = fig.add_axes([.10, .40, .86, .265])
ax3 = fig.add_axes([.25, .065, .71, .205])
fig.text(.025, .963, 'a', fontsize=11, fontweight='bold')
fig.text(.10, .963, 'Recorded reproduction across numerical claims', fontsize=10, fontweight='bold')
fig.text(.10, .931, f'{len(claim_data):,} claims in {len(measured)} papers with measurements; equal weight per claim', fontsize=8, color='#52616E')
left = 0
for label, title, color in zip(labels[:3], ['Reproduced', 'Externally blocked', 'Attempted, not reproduced'], [navy, amber, slate]):
    value = pooled[label]
    ax1.barh(0, value, left=left, height=.65, color=color, edgecolor='white', linewidth=1)
    ax1.text(left + value/2, 0, f'{value:.1f}%', ha='center', va='center', fontweight='bold', fontsize=11, color='white' if label=='reproduced' else '#23384A')
    ax1.text(left + value/2, -.53, title, ha='center', va='center', fontsize=7.5)
    left += value
ax1.set(xlim=(0,100), ylim=(-.75,.4)); ax1.axis('off')
fig.text(.025, .720, 'b', fontsize=11, fontweight='bold')
fig.text(.10, .720, 'Coverage varies across the 100-paper project', fontsize=10, fontweight='bold')
fig.text(.10, .687, f'Mean recorded coverage: {summary["mean_paper_coverage_measured_percent"]:.1f}% among measured papers', fontsize=8, color='#52616E')
ordered = sorted(measured, key=lambda r: (-r['reproduced_percent'], r['paper_id'])) + missing
x = np.arange(1, 101)
bottom = np.zeros(100)
for label, color in zip(labels[:3], [navy, amber, slate]):
    heights = np.array([r[label + '_percent'] if r['coverage_available'] else 0 for r in ordered])
    ax2.bar(x, heights, bottom=bottom, width=.85, color=color, linewidth=0)
    bottom += heights
for rank in range(len(measured)+1, 101):
    ax2.bar(rank, 100, width=.85, color='white', edgecolor='#9BA8B4', linewidth=.4, hatch='///')
ax2.set(xlim=(0,101), ylim=(0,100), yticks=[0,50,100], xticks=[1,25,50,75,100])
ax2.set_ylabel('Claim coverage (%)', fontsize=8)
ax2.set_xlabel('Papers ordered by recorded coverage (one bar per paper)', fontsize=8, labelpad=5)
ax2.tick_params(labelsize=7, length=3)
ax2.text(1,1.035,'3 unmeasured papers: hatched',ha='right',transform=ax2.transAxes,fontsize=7,color='#52616E')
fig.text(.025, .31, 'c', fontsize=11, fontweight='bold')
fig.text(.10, .31, 'Recorded scope, scientific checks and independent review', fontsize=10, fontweight='bold')
settings = [
 ('numerical_scope', 'Numerical scope', [('complete','Complete',navy),('incomplete','Incomplete',slate)]),
 ('science','Scientific checks', [('passed','Passed',navy),('failed','Failed',amber),('pending','Pending',slate)]),
 ('independent_review','Independent review',[('passed','Passed',navy),('stale','Stale',amber),('missing','Missing',slate)]),
]
for y,(key,title,items) in zip([2,1,0],settings):
    left=0
    ax3.text(-2,y,title,ha='right',va='center',fontsize=7.5)
    for code,name,color in items:
        n=summary['assessment_counts'][key].get(code,0)
        ax3.barh(y,n,left=left,height=.58,color=color,edgecolor='white',linewidth=.8)
        ax3.text(left+n/2,y,f'{name} {n}',ha='center',va='center',fontsize=7,color='white' if color==navy else '#23384A')
        left+=n
    n=summary['assessment_counts'][key].get('unavailable',0)
    ax3.barh(y,n,left=left,height=.58,color='white',edgecolor='#9BA8B4',linewidth=.4,hatch='///')
ax3.set(xlim=(0,100),ylim=(-.55,2.6),xticks=[0,25,50,75,100],yticks=[])
ax3.spines['left'].set_visible(False)
ax3.set_xlabel('Papers (fixed denominator: 100; hatched = 3 unavailable assessments)', fontsize=7.5)
ax3.tick_params(labelsize=7,length=3)
for ext in ['pdf', 'svg', 'png']:
    fig.savefig(HERE / f'figures/fig_overall_reproduction.{ext}', dpi=300, facecolor='white')
plt.close(fig)
print(json.dumps({k:v for k,v in summary.items() if k!='inputs'},indent=2))
