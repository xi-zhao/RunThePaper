#!/usr/bin/env python3
"""Render descriptive archive tables; no scientific case imports or execution."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
from validate_archive_evidence import validate_product
HERE=Path(__file__).resolve().parent


def build_report(root=HERE):
    integrity=validate_product(root)
    papers=[json.loads(s) for s in (root/'data/papers.jsonl').read_text().splitlines()]
    records=[json.loads(s) for s in (root/'data/results.jsonl').read_text().splitlines()]
    summary=json.loads((root/'data/summary.json').read_text())
    by_paper={p['paper_id']:[r for r in records if r['paper_id']==p['paper_id']] for p in papers}
    stats={**summary,'hashed_source_files':integrity['source_files'],
        'papers_with_unmapped_targets':sum(p['unmapped_archived_target_rows']>0 for p in papers),
        'papers_with_unresolved_public_references':sum(any(r['unresolved_public_references'] for r in by_paper[p['paper_id']]) for p in papers),
        'papers_with_referenced_public_artifacts':sum(any(r['artifacts'] for r in by_paper[p['paper_id']]) for p in papers),
        'papers_with_public_python_files':sum(p['public_code_files']>0 for p in papers),
        'papers_with_public_data_files':sum(p['public_data_files']>0 for p in papers),
        'papers_with_stored_review_file':sum(p['stored_review_available'] for p in papers)}
    output=root/'analysis'; output.mkdir(exist_ok=True)
    (output/'archive_descriptive_counts.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
    queue=[]
    for paper in papers:
        pid=paper['paper_id']; rows=by_paper[pid]
        queue.append({'paper_id':pid,'original_objects':paper['original_inventory_rows'],
            'unmapped_targets':paper['unmapped_archived_target_rows'],'records_with_artifacts':sum(bool(r['artifacts']) for r in rows),
            'records_with_unresolved_references':sum(bool(r['unresolved_public_references']) for r in rows),
            'source_semantics_status':'not_rechecked','required_action':'Read original source and listed artifacts; reconcile granularity; retain missing evidence; no execution.'})
    with (output/'semantic_review_queue.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(queue[0]),lineterminator="\n"); writer.writeheader(); writer.writerows(queue)
    lines=['# 97篇归档证据提取报告','',
       '**这是归档目录与字节完整性结果，尚未形成新的科学一致性判断。**','',
       '固定来源为 RunThePaper `'+summary['source_commit']+'`。提取器仅通过 Git 对象读取原有材料，未导入案例代码，未运行旧求解器、测试或科学检查器。','',
       '| 观察项 | 数量 | 含义 |','|---|---:|---|',
       f"| 固定历史论文 | {len(papers)} | 原100篇中预先登记纳入本分析的97篇 |",
       f"| 原归档对象条目 | {summary['original_inventory_rows']} | 原清单的粒度不同，不能作为统一成果分母 |",
       f"| 清单未映射的历史目标 | {summary['unmapped_target_rows']} | 单独保留以供补核对，不增加独立结果数 |",
       f"| 当前证据记录 | {len(records)} | 对象条目加未映射目标；不是科学成果数 |",
       f"| 已读取并哈希的来源文件 | {integrity['source_files']} | 能复核提取输入的字节与Git对象 |",
       f"| 有可定位公共工件的记录 | {summary['records_with_referenced_public_artifacts']} | 文件存在，不代表其科学内容正确 |",
       f"| 有公共引用缺口的记录 | {summary['records_with_unresolved_public_references']} | 与上一行可重叠；不推断私有档案也缺失 |",
       '| 新科学执行 / 新验收结论 | 0 / 0 | 无旧案例重跑，无新成功率 |','',
       '模型、人工干预、实际物理条件和逐值比较仍为未知。历史标签保存在独立字段，不能由 `paper_exact`、`passed`、旧混合分或文件数量推导新结论。', '',
       '## 每篇的核对入口','',
       '以下所有行的原文语义核对状态均为 `not_rechecked`。对象数不齐或粒度不同必须回到原文核齐后再决定分母。','',
       '| 论文 | 原对象 | 未映射目标 | 有工件的记录 | 有引用缺口的记录 |','|---|---:|---:|---:|---:|']
    for q in queue:
        pid=q['paper_id']
        link='https://github.com/xi-zhao/RunThePaper/tree/'+summary['source_commit']+'/cases/'+pid
        lines.append(f"| [{pid}]({link}) | {q['original_objects']} | {q['unmapped_targets']} | {q['records_with_artifacts']} | {q['records_with_unresolved_references']} |")
    lines+=['','## 复算与接续','',
        '`build_archive_evidence.py` 从固定Git版本重建 data；`validate_archive_evidence.py` 校验身份、计数和证据索引；`build_archive_report.py` 重建本报告、描述计数和核对队列。所有工具仅处理归档资料。','',
        '后续逐结果核对应另行追加可定位的审阅记录，保留本次提取快照。先确认原文版本、原始对象、条件和数据字段，再写有单位的比较值。原文未核齐时不得报告整篇覆盖率。','']
    (output/'ARCHIVE_REPORT.md').write_text('\n'.join(lines))
    return stats


if __name__=='__main__':
    print(json.dumps(build_report(),ensure_ascii=False,indent=2))
