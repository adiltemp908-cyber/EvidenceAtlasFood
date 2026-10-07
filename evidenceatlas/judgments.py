"""Validate external judgments and evaluate real runs without contaminating retrieval."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .contracts import SourceSpan,EvidenceJudgment
from .evaluation import metrics
from .store import Store
from .config import Settings

def evaluate(snapshot,judgment_file,reviewer_kind):
    store=Store(snapshot/'corpus.sqlite');labels={};reviewers=set()
    for line in judgment_file.read_text(encoding='utf-8').splitlines():
        value=json.loads(line);value['rationale']=[SourceSpan(**span) for span in value.get('rationale',[])]
        judgment=EvidenceJudgment(**value);judgment.validate(store)
        if judgment.reviewer_kind!=reviewer_kind:continue
        key=(judgment.claim_id,judgment.paper_id)
        if key in labels and labels[key]!=judgment.relevance:raise ValueError('Unadjudicated disagreement; do not silently pick a reviewer')
        labels[key]=judgment.relevance;reviewers.add(judgment.reviewer_id)
    if not labels:raise ValueError('No matching reviewed judgments supplied; effectiveness metrics unavailable')
    runs=json.loads((snapshot/'runs.json').read_text());output=[]
    for run in runs:
        qrels={pid:grade for (cid,pid),grade in labels.items() if cid==run['claim_id']}
        if not qrels:continue
        output.append({'claim_id':run['claim_id'],'method':run['method'],'metrics':metrics([p['id'] for p in run['ranking']],qrels,10)})
    report={'reviewer_kind':reviewer_kind,'reviewers':sorted(reviewers),'judged_pairs':len(labels),'results':output,
            'status':'Human reviewed; check qualifications/adjudication' if reviewer_kind=='human' else 'AI-provisional diagnostic; not human gold'}
    Settings.atomic_json(snapshot/f'metrics-{reviewer_kind}.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('judgments',type=Path);p.add_argument('--reviewer-kind',choices=['human','AI'],required=True);a=p.parse_args()
    print(json.dumps(evaluate(a.snapshot,a.judgments,a.reviewer_kind),indent=2))
