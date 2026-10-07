"""Recompute report Precision@3, @5 and @10 from saved AI relevance judgments."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evaluation/report-v2'

def evaluate():
    protocol = json.loads((FOLDER / 'protocol.json').read_text(encoding='utf-8'))
    runs = json.loads((FOLDER / 'runs.json').read_text(encoding='utf-8'))
    labels = json.loads((FOLDER / 'judgments.json').read_text(encoding='utf-8'))
    by_run, consistent = {}, {}
    for label in labels:
        assert label['reviewer_kind'] == 'AI' and label['grade'] in (0, 1, 2)
        key = (label['topic'], label['paper_id'])
        assert key not in consistent or consistent[key] == label['grade'], 'Conflicting pair labels'
        consistent[key] = label['grade']
        assert label['paper_id'] not in by_run.setdefault(label['run'], {})
        by_run[label['run']][label['paper_id']] = label
    result = {}
    assert len({r['key'] for r in runs}) == len(runs)
    for run in runs:
        if run['judgment_status'] != 'complete':
            assert run['key'] not in by_run
            continue
        papers = run['results']
        assert len(papers) == 10 and len({p['id'] for p in papers}) == 10
        assert [p['rank'] for p in papers] == list(range(1, 11))
        assert {p['id'] for p in papers} == set(by_run[run['key']])
        fingerprint = run['trace'].get('index', {}).get('corpus')
        if fingerprint:
            assert fingerprint == protocol['corpus'], 'Corpus changed'
        grades = [by_run[run['key']][p['id']]['grade'] for p in papers]
        result[run['key']] = dict(query=run['query'], grades=grades,
            precision={str(k): sum(g == protocol['relevant_grade'] for g in grades[:k]) / k
                       for k in protocol['positions']})
    assert set(result) == set(protocol['judged_runs'])
    def mean(keys):
        return {str(k): sum(result[key]['precision'][str(k)] for key in keys) / len(keys)
                for k in protocol['positions']}
    originals = [r['key'] for r in runs if r['stage'] == 'original']
    return dict(reviewer_kind='AI', positions=protocol['positions'], selected=protocol['selected'],
        selection=protocol['selection'], metrics=result, selected_mean=mean(protocol['selected']),
        original_six_mean=mean(originals),
        paired_baseline_mean=mean([p[0] for p in protocol['baseline_pairs']]),
        paired_hybrid_mean=mean([p[1] for p in protocol['baseline_pairs']]),
        total_runs=len(runs), judged_runs=len(result), judged_positions=len(labels),
        unique_topic_paper_pairs=len(consistent), corpus=protocol['corpus'])

if __name__ == '__main__':
    result = evaluate()
    (FOLDER / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'metrics'}, indent=2))
