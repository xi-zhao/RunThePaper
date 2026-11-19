#!/usr/bin/env python3
"""Validate planning metadata only. Never import or execute a scientific case."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
RETAINED_IDS_SHA256 = 'ddf2acf17ad9280d34d3e4aa5faf7f687b12296e521a41dcd67267beb8eaeabf'
EXCLUDED_IDS = {'2101.12558', '2211.15015', '2406.07531'}
NEW_IDS = {'quant-ph-9604005', 'quant-ph-0309131', 'cond-mat-0503172'}
SOURCE_COMMIT = '43a64cd03824edb136b549f352412e8d263d9361'
SOURCE_BLOB = '7652b4c1890fb319f8096898947a9a22ea544763'


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(plan: dict[str, Any], template: dict[str, Any]) -> dict[str, Any]:
    require(plan.get('schema_version') == 1, 'Unsupported plan schema')
    require(plan.get('status') == 'planning_only', 'This validator only accepts unexecuted plans')
    retained = plan['retained_historical_ids']
    require(len(retained) == len(set(retained)) == 97, 'Expected 97 unique historical IDs')
    digest = hashlib.sha256(('\n'.join(retained) + '\n').encode()).hexdigest()
    require(digest == RETAINED_IDS_SHA256, 'Historical cohort changed; revise transparently')
    excluded = plan['excluded_from_detailed_analysis']
    excluded_ids = {row['paper_id'] for row in excluded}
    require(len(excluded) == 3 and excluded_ids == EXCLUDED_IDS, 'Exclusion registry changed')
    require(not set(retained) & excluded_ids, 'Included and excluded sets overlap')
    require(all(row.get('reason') and row.get('retained_in_original_archive') is True
                for row in excluded), 'Preserve exclusions and their reasons')
    source = plan['historical_source']
    require(source.get('repository') == 'xi-zhao/RunThePaper', 'Unexpected source repository')
    require(source.get('commit') == SOURCE_COMMIT and source.get('git_blob_sha1') == SOURCE_BLOB,
            'Historical source must remain pinned')
    require(source.get('path') == 'evaluation/claim-first-100/data/papers.csv', 'Source path changed')
    require(source.get('original_case_count') == 100, 'Original cohort has 100 cases')
    additions = plan['prospective_additions']
    new_ids = {row['paper_id'] for row in additions}
    require(len(additions) == 3 and new_ids == NEW_IDS, 'Expected exactly the three selected papers')
    require(not new_ids & (set(retained) | excluded_ids), 'New papers duplicate historical papers')
    dois = [row['doi'].casefold() for row in additions]
    require(len(dois) == len(set(dois)), 'Duplicate publication DOI')
    for row in additions:
        require(row['paper_id'] == row['arxiv_id'].replace('/', '-'), 'Identity alias mismatch')
        require(row.get('arxiv_version') == 2, 'Selected source version changed')
        require(row['source_url'] == f"https://arxiv.org/abs/{row['arxiv_id']}v2", 'Unpinned source URL')
        require(bool(row.get('title') and row.get('publication') and row.get('selection_reason')),
                'Missing paper metadata or selection rationale')
        require(row.get('execution_status') == 'not_started', 'Planned paper must not claim execution')
        require(row.get('scientific_verdict') is None and row.get('evidence_bundle') is None,
                'Planned paper must not claim scientific evidence')
    policy = plan['policy']
    expected = {
        'old_case_scientific_execution_allowed': False,
        'old_archive_must_remain_unchanged': True,
        'selection_is_retrospective_and_outcome_informed': True,
        'new_case_selection_is_low_compute_purposive': True,
        'old_and_new_results_reported_separately': True,
        'replace_new_failures_to_reach_success_count': False,
        'new_case_execution_in_this_pr': False,
        'public_case_authority': 'PRAgent publish_manifest.json projection',
    }
    for key, value in expected.items():
        require(policy.get(key) == value, f'Policy changed: {key}')
    require(plan.get('planned_detailed_case_count') == len(retained) + len(additions) == 100,
            'Detailed analysis plan must have 100 positions')
    require(template.get('record_type') == 'template_not_evidence', 'Template is not evidence')
    require(template['review']['outcome'] == 'not_evaluated', 'Template contains a verdict')
    require(not template['artifacts'] and not template['existing_checks'], 'Template contains results')
    require(all(v is None for v in template['comparison'].values()), 'Template contains measurements')
    return {'status': 'passed', 'scope': 'planning_metadata_only',
            'historical_retained': 97, 'historical_excluded_but_preserved': 3,
            'prospective_not_started': 3, 'planned_detailed_cases': 100,
            'distinct_papers_in_selection_history': 103,
            'scientific_cases_executed': 0, 'scientific_verification': 'not_performed'}


def validate_repository_source(plan: dict[str, Any], root: Path) -> None:
    """Check the exact frozen CSV bytes without evaluating any case code."""
    path = root.resolve() / plan['historical_source']['path']
    data = path.read_bytes()
    blob = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
    require(blob == SOURCE_BLOB, 'Historical CSV differs from the pinned Git blob')
    rows = list(csv.DictReader(data.decode('utf-8-sig').splitlines()))
    ids = [row['paper_id'] for row in rows]
    require(len(ids) == len(set(ids)) == 100, 'Historical CSV has an invalid cohort')
    expected = set(plan['retained_historical_ids']) | EXCLUDED_IDS
    require(set(ids) == expected, 'Selected and excluded IDs do not reconstruct the source cohort')
    new_dois = [row['doi'].casefold() for row in plan['prospective_additions']]
    historical_titles = {row['title'].casefold() for row in rows}
    require(not any(row['title'].casefold() in historical_titles for row in plan['prospective_additions']),
            'A new title already exists in the historical cohort')
    # DOI-normalized case IDs are also checked; no claims about training-set contamination.
    require(not any(doi.replace('/', '-') in {item.casefold() for item in ids} for doi in new_dois),
            'A new DOI already exists as a historical case ID')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path)
    args = parser.parse_args()
    try:
        plan = json.loads((HERE / 'cohort.json').read_text(encoding='utf-8'))
        template = json.loads((HERE / 'RESULT_RECORD_TEMPLATE.json').read_text(encoding='utf-8'))
        result = validate(plan, template)
        if args.repository_root is not None:
            validate_repository_source(plan, args.repository_root)
            result['historical_csv_bytes_checked'] = True
        else:
            result['historical_csv_bytes_checked'] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
