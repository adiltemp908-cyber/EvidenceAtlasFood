"""Recompute exploratory AI-judged Precision@k from saved rankings; no models required."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / 'evaluation/everyday-10'

def evaluate():
    protocol = json.loads((FOLDER / 'protocol.json').read_text())
    runs = json.loads((FOLDER / 'runs.json').read_text())
    labels = json.loads((FOLDER / 'judgments.json').read_text())
    judgments = {}
    for label in labels:
        key = (label['qi'], label['paper_id'])
        assert key not in judgments, 'Duplicate judgment'
        assert label['reviewer_kind'] == 'AI' and label['grade'] in (0, 1, 2)
        judgments[key] = label['grade']
    expected = {(q, m) for q in range(len(protocol['questions'])) for m in protocol['methods']}
    assert len(runs) == len(expected) and {(r['qi'], r['method']) for r in runs} == expected
    per_query = []
    used = set()
    for r in runs:
        assert r['question'] == protocol['questions'][r['qi']]
        assert len(r['results']) == 3 and len({p['id'] for p in r['results']}) == 3
        grades = [judgments[(r['qi'], p['id'])] for p in r['results']]
        used.update((r['qi'], p['id']) for p in r['results'])
        per_query.append(dict(qi=r['qi'], question=r['question'], method=r['method'], grades=grades,
            precision={str(k): sum(g >= protocol['relevance_threshold'] for g in grades[:k]) / k for k in protocol['positions']}))
    assert used == set(judgments), 'Labels and ranked pool differ'
    aggregate = {m: {str(k): sum(r['precision'][str(k)] for r in per_query if r['method'] == m) / len(protocol['questions'])
                     for k in protocol['positions']} for m in protocol['methods']}
    return dict(reviewer_kind='AI', relevance_threshold=2, queries=len(protocol['questions']),
        runs=len(runs), unique_judged_pairs=len(judgments), judged_positions=sum(len(r['results']) for r in runs),
        aggregate=aggregate, per_query=per_query,
        limitations=protocol['limitations'])

if __name__ == '__main__':
    result = evaluate()
    (FOLDER / 'metrics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'per_query'}, indent=2))
