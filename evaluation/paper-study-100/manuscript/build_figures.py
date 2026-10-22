#!/usr/bin/env python3
"""Regenerate manuscript figures and unified cohort table from frozen public evidence.

This script only reads study metadata; it never executes scientific case code.
Run with Python 3.12+, matplotlib 3.10+, and numpy 2.x.
"""
from pathlib import Path
import csv
import hashlib
import json
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import numpy as np

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIG = HERE / 'figures'
FIG.mkdir(exist_ok=True)

def read_jsonl(name):
    return [json.loads(line) for line in (STUDY / 'data' / name).read_text().splitlines()]

papers = read_jsonl('papers.jsonl')
records = read_jsonl('results.jsonl')
cohort = json.loads((STUDY / 'cohort.json').read_text())
lookup = {p['paper_id']: p for p in papers}
additions = {p['paper_id']: p for p in cohort['prospective_additions']}
ids = sorted(cohort['retained_historical_ids'] + list(additions))
assert len(ids) == len(set(ids)) == 100
assert len(lookup) == len(papers) == 97
assert set(lookup) <= set(ids)
assert len({(r['paper_id'], r['result_id']) for r in records}) == len(records)
by_paper = {pid: [r for r in records if r['paper_id'] == pid] for pid in lookup}
unique_targets = {}
for row in records:
    for target in row['archived_targets']:
        key = (row['paper_id'], target['target_id'])
        assert key not in unique_targets or unique_targets[key] == target
        unique_targets[key] = target
orig = [r for r in records if r['record_origin'] == 'archived_original_object']
types = Counter(r['source']['item_type'] for r in orig)
labels = Counter(t['archived_parameter_match'] for t in unique_targets.values())
contingency = Counter((bool(r['artifacts']), bool(r['unresolved_public_references'])) for r in records)

fields = ['paper_id', 'title', 'public_extraction_available', 'public_python_present',
          'public_data_present', 'stored_review_present', 'unmapped_targets_present',
          'unresolved_references_present', 'evidence_record_count', 'independent_scientific_reassessment']
unified = []
for pid in ids:
    p = lookup.get(pid)
    unified.append(dict(zip(fields, [pid, (p or additions[pid])['title'], p is not None,
        None if p is None else p['public_code_files'] > 0,
        None if p is None else p['public_data_files'] > 0,
        None if p is None else p['stored_review_available'],
        None if p is None else p['unmapped_archived_target_rows'] > 0,
        None if p is None else any(r['unresolved_public_references'] for r in by_paper[pid]),
        None if p is None else p['evidence_rows'], 'not_assessed_in_this_analysis'])))
with (HERE / 'cohort_100.csv').open('w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    writer.writerows(unified)
(HERE / 'cohort_100.json').write_text(json.dumps(unified, indent=2, ensure_ascii=False)+'\n')

stats = {
    'cohort_papers': len(ids), 'public_extraction_papers': len(papers),
    'original_inventory_records': len(orig), 'unmapped_target_records': len(records)-len(orig),
    'evidence_records': len(records), 'unique_archived_targets': len(unique_targets),
    'input_files': len(read_jsonl('inputs.jsonl')),
    'papers_with_python': sum(p['public_code_files'] > 0 for p in papers),
    'papers_with_data': sum(p['public_data_files'] > 0 for p in papers),
    'papers_with_review': sum(p['stored_review_available'] for p in papers),
    'papers_with_unmapped_targets': sum(p['unmapped_archived_target_rows'] > 0 for p in papers),
    'papers_with_unresolved_references': sum(any(r['unresolved_public_references'] for r in by_paper[pid]) for pid in lookup),
    'artifact_reference_contingency': {f'artifact_{int(a)}__unresolved_{int(u)}': contingency[(a,u)] for a in [False,True] for u in [False,True]},
    'original_inventory_types': dict(sorted(types.items())),
    'unique_target_parameter_declarations': dict(sorted(labels.items())),
    'evidence_records_per_available_paper': dict(zip(['minimum','q1','median','q3','maximum'], np.percentile([p['evidence_rows'] for p in papers], [0,25,50,75,100]).tolist())),
    'new_scientific_verdicts': 0, 'scientific_success_rate': None,
    'source_commit': cohort['historical_source']['commit'],
    'input_sha256': {name: hashlib.sha256((STUDY / name).read_bytes()).hexdigest() for name in ['cohort.json','data/papers.jsonl','data/results.jsonl','data/inputs.jsonl']},
}
(HERE / 'figure_data.json').write_text(json.dumps(stats, indent=2)+'\n')

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':9, 'axes.spines.top':False,
                     'axes.spines.right':False, 'axes.labelcolor':'#203041', 'text.color':'#203041',
                     'axes.titleweight':'bold', 'savefig.facecolor':'white', 'pdf.fonttype':42})
blue, teal, amber, pale = '#355F85', '#238A86', '#CA8542', '#E6E9ED'

def save(fig, name):
    fig.savefig(FIG / f'{name}.pdf', bbox_inches='tight')
    fig.savefig(FIG / f'{name}.png', dpi=180, bbox_inches='tight')
    plt.close(fig)

# Figure 1: protocol requirements, not an assertion that all stages are complete.
fig, ax = plt.subplots(figsize=(7.15,3.0))
ax.set(xlim=(0,10), ylim=(0,4.2)); ax.axis('off')
boxes = [(0.1,2.55,'1  Source object','Version, locator, scope'),
         (3.5,2.55,'2  Physical contract','Equations, units, conditions'),
         (6.9,2.55,'3  Implementation','Traceable model and inputs'),
         (6.9,.6,'4  Execution evidence','Runtime, arrays, provenance'),
         (3.5,.6,'5  Independent assessment','Comparisons and limitations'),
         (.1,.6,'6  Public projection','Selected, linked evidence')]
for x,y,title,sub in boxes:
    ax.add_patch(FancyBboxPatch((x,y),2.95,1.1,boxstyle='round,pad=0.04',facecolor='#F1F5F8',edgecolor=blue,lw=1))
    ax.text(x+1.47,y+.72,title,ha='center',va='center',fontsize=9,fontweight='bold')
    ax.text(x+1.47,y+.32,sub,ha='center',va='center',fontsize=7.5)
for a,b in [((3.07,3.1),(3.45,3.1)),((6.47,3.1),(6.85,3.1)),((8.37,2.5),(8.37,1.78)),((6.84,1.15),(6.5,1.15)),((3.44,1.15),(3.1,1.15))]:
    ax.annotate('',xy=b,xytext=a,arrowprops={'arrowstyle':'->','color':blue,'lw':1.5})
ax.text(5,.08,'Assess separately: source coverage  |  physical fidelity  |  numerical agreement  |  review finality',ha='center',fontsize=8)
ax.text(5,4.02,'Required evidence chain',ha='center',fontsize=11,fontweight='bold')
save(fig,'fig1_evidence_chain')

# Figure 2: fixed paper denominator and mutually exclusive record cells.
fig, axs = plt.subplots(1,2,figsize=(7.15,3.1),gridspec_kw={'width_ratios':[1.05,1]})
ax=axs[0]
rowlabels=['Public extraction','Python files','Data files','Stored review']
values=[97,97,96,44]; known_absent=[0,0,1,53]
ys=np.arange(4)
ax.barh(ys,values,color=blue,label='Present')
ax.barh(ys,known_absent,left=values,color=amber,label='Absent in extraction')
ax.barh(ys,[3]*4,left=np.array(values)+known_absent,color=pale,label='Not assessed')
for i,v in enumerate(values): ax.text(v/2,i,str(v),va='center',ha='center',color='white',fontweight='bold')
ax.set(yticks=ys,yticklabels=rowlabels,xlim=(0,100),xlabel='Papers / fixed cohort of 100',title='a  Public evidence availability')
ax.invert_yaxis();ax.tick_params(axis='y',length=0)
ax.legend(loc='upper left',bbox_to_anchor=(-.02,-.23),frameon=False,fontsize=7.3)
ax=axs[1]
mat=np.array([[653,2114],[830,330]])
ax.imshow(np.array([[0.4,1.0],[.25,.15]]),cmap='Blues',vmin=0,vmax=1.3)
for i in range(2):
 for j in range(2): ax.text(j,i,f'{mat[i,j]:,}\n{mat[i,j]/3927:.1%}',ha='center',va='center',fontsize=10,color='white' if (i,j)==(0,1) else '#203041',fontweight='bold')
ax.set(xticks=[0,1],xticklabels=['None\nunresolved','Some\nunresolved'],yticks=[0,1],yticklabels=['Artifact linked','No artifact linked'],title='b  Record-level reference audit')
ax.tick_params(length=0,labelsize=7.5);ax.set_xlabel('Public references (3,927 records)')
fig.tight_layout(w_pad=2.0)
save(fig,'fig2_availability')

fig, axs=plt.subplots(1,2,figsize=(7.15,3.5),gridspec_kw={'width_ratios':[1,1.05]})
ax=axs[0]
kindlabels=['Figure series','Figure panels','All other inventory types']
kindvalues=[types['figure_series'],types['figure_panel'],len(orig)-types['figure_series']-types['figure_panel']]
ax.barh(range(3),kindvalues,color=blue)
for i,v in enumerate(kindvalues): ax.text(v+25,i,f'{v:,}',va='center',fontsize=8)
ax.set(yticks=range(3),yticklabels=kindlabels,xlim=(0,2300),xlabel='Original inventory records (n = 3,666)',title='a  Inventory granularity');ax.invert_yaxis();ax.tick_params(axis='y',length=0)
ax=axs[1]
keys=['paper_exact','paper_subset','reduced_scale','unknown','not_applicable','proxy_model']
vals=[labels[k] for k in keys]
ax.barh(range(6),vals,color=[teal,blue,amber,pale,'#ACBBC9','#AA6472'])
for i,v in enumerate(vals): ax.text(v+6,i,str(v),va='center',fontsize=8)
ax.set(yticks=range(6),yticklabels=['Paper exact','Paper subset','Reduced scale','Unknown','Not applicable','Proxy model'],xlim=(0,600),xlabel='Unique declared targets (n = 1,116)',title='b  Archived parameter labels');ax.invert_yaxis();ax.tick_params(axis='y',length=0)
fig.tight_layout(w_pad=2.2)
save(fig,'fig3_units_and_conditions')

# Supplement: all 100 identities, no origin-based grouping, null preserved.
from matplotlib.colors import ListedColormap
fig, axs = plt.subplots(1,2,figsize=(8.0,10.1))
cols=['public_extraction_available','public_python_present','public_data_present','stored_review_present','unmapped_targets_present','unresolved_references_present']
for ax, subset in zip(axs,[unified[:50],unified[50:]]):
    # Gray means not assessed, white absent, blue presence, amber a detected gap.
    data=np.array([[0 if row[c] is None or (c=='public_extraction_available' and not row[c]) else (3 if not row[c] else (2 if c in cols[-2:] else 1)) for c in cols] for row in subset])
    ax.imshow(data,aspect='auto',interpolation='none',cmap=ListedColormap([pale,blue,amber,'white']),vmin=0,vmax=3)
    ax.set(yticks=range(50),yticklabels=[r['paper_id'] for r in subset],xticks=range(6),xticklabels=['Extract','Python','Data','Review','Unmapped','Unresolved'])
    ax.xaxis.tick_top();ax.tick_params(axis='x',labelrotation=65,labelsize=7,length=0);ax.tick_params(axis='y',labelsize=6.0,length=0)
    ax.set_yticks(np.arange(-.5,50,1),minor=True);ax.grid(which='minor',axis='y',color='#F1F2F4',linewidth=.4);ax.tick_params(which='minor',length=0)
fig.text(.5,.012,'Blue: available  |  Amber: recorded gap  |  White: absent in extraction  |  Gray: not assessed',ha='center',fontsize=8)
fig.subplots_adjust(left=.23,right=.99,top=.90,bottom=.035,wspace=1.18)
save(fig,'figS1_cohort_matrix')
print(json.dumps(stats,indent=2))
