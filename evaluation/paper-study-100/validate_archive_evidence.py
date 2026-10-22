#!/usr/bin/env python3
"""Validate derived records without running scientific cases, including under -O."""
import json
from pathlib import Path
from validate_plan import SOURCE_COMMIT
HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_product(root=HERE):
    def rows(name):
        return [json.loads(line) for line in (root/'data'/name).read_text().splitlines()]
    cohort=json.loads((root/'cohort.json').read_text())
    papers, records, inputs=rows('papers.jsonl'), rows('results.jsonl'), rows('inputs.jsonl')
    summary=json.loads((root/'data/summary.json').read_text())
    expected=set(cohort['retained_historical_ids'])
    require(len(papers)==97 and {p['paper_id'] for p in papers}==expected, 'fixed 97-paper population changed')
    require(len({(r['paper_id'],r['result_id']) for r in records})==len(records), 'duplicate result identity')
    require({r['paper_id'] for r in records}==expected, 'evidence population mismatch')
    require(summary['source_commit']==SOURCE_COMMIT, 'source revision changed')
    require(summary['evidence_records']==len(records), 'record count mismatch')
    require(summary['headline_success_rate'] is None, 'extraction must not infer success rate')
    require(summary['new_scientific_executions']==summary['new_scientific_verdicts']==0, 'extraction must not execute or accept science')
    require(summary['original_inventory_rows']==sum(p['original_inventory_rows'] for p in papers), 'inventory count mismatch')
    require(summary['unmapped_target_rows']==sum(p['unmapped_archived_target_rows'] for p in papers), 'unmapped count mismatch')
    by_path={r['path']:r for r in inputs}
    require(len(by_path)==len(inputs), 'duplicate input path')
    for paper in papers:
        require(paper['original_scope_rechecked'] is False and paper['new_scientific_execution'] is False, 'paper scope overstated')
        require(paper['model'] is None and paper['human_interventions'] is None, 'unknown historical provenance invented')
        actual=[r for r in records if r['paper_id']==paper['paper_id']]
        require(paper['evidence_rows']==len(actual), 'paper row count mismatch')
    for row in records:
        require(row['review']['outcome']=='not_evaluated', 'archive label promoted into new verdict')
        require(row['review']['basis']=='archive_metadata_and_bytes_inspected', 'review depth overstated')
        require(row['source']['scope_complete'] is None, 'source completeness not established')
        require(row['count_as_independent_result'] is False, 'unreviewed row counted as a result')
        require(row['execution']['new_scientific_execution'] is False, 'old case execution forbidden')
        require(row['execution']['human_interventions'] is None, 'unknown intervention count invented')
        require(all(v is None for v in row['comparison'].values()), 'comparison value invented by extraction')
        for artifact in row['artifacts']:
            indexed=by_path.get(artifact['path'])
            require(indexed is not None, 'unindexed input')
            require(artifact['sha256']==indexed['sha256'] and artifact['git_blob_sha1']==indexed['git_blob_sha1'], 'artifact integrity mismatch')
            require(artifact['scientific_contents_reverified'] is False, 'byte inspection overstated')
    return {'status':'passed','papers':len(papers),'records':len(records),'source_files':len(inputs),'scope':'metadata_and_integrity_only'}


if __name__=='__main__':
    print(json.dumps(validate_product(),indent=2))
