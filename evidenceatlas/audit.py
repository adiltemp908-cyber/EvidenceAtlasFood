"""Recompute the bounded AI audit from saved labels and frozen source text."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .contracts import EvidenceJudgment, SourceSpan
from .evaluation import metrics
from .store import Store

CLAIMS = ('food-002', 'food-004', 'food-006', 'food-008')

def recompute(snapshot: Path, artifacts: Path):
    if not (snapshot/'corpus.sqlite').is_file():
        raise ValueError('Frozen corpus is missing; cannot validate source spans')
    runs = json.loads((artifacts/'runs.json').read_text(encoding='utf-8'))
    selected = [r for r in runs if r['method']=='hybrid_rerank' and r['claim_id'] in CLAIMS]
    if len(selected)!=4 or len({r['claim_id'] for r in selected})!=4:
        raise ValueError('Expected exactly four frozen development runs')
    expected = {(r['claim_id'], p['id']) for r in selected for p in r['ranking'][:3]}
    if len(expected)!=12:raise ValueError('Expected twelve distinct claim-paper pairs')
    store=Store(snapshot/'corpus.sqlite')
    try:
        labels={};availability={}
        for line in (artifacts/'ai-judgments.jsonl').read_text(encoding='utf-8').splitlines():
            v=json.loads(line);v['rationale']=[SourceSpan(**s) for s in v['rationale']]
            j=EvidenceJudgment(**v);j.validate(store)
            if j.reviewer_kind!='AI':raise ValueError('AI audit cannot include human labels')
            key=(j.claim_id,j.paper_id)
            if key in labels:raise ValueError('Duplicate audit judgment')
            labels[key]=j.relevance
            paper=store.paper(j.paper_id)
            if not paper:raise ValueError('Judged paper absent from frozen corpus')
            availability[paper['availability']]=availability.get(paper['availability'],0)+1
        if set(labels)!=expected:raise ValueError('Labels do not match the predeclared top-three sample')
        results=[]
        for r in selected:
            qrels={pid:g for (cid,pid),g in labels.items() if cid==r['claim_id']}
            m=metrics([p['id'] for p in r['ranking']],qrels,3)
            results.append({'claim_id':r['claim_id'],'claim':r['query'],'relevant_at_3':sum(g>=2 for g in qrels.values()),
                            'precision_at_3':m['precision_at_k'],'grade3_at_3':sum(g==3 for g in qrels.values()),'judged_fraction':m['judged_fraction']})
        return {'status':'Preliminary AI self-audit; not independent validation or overall accuracy','method':'hybrid_rerank',
                'corpus':store.fingerprint(),'sample_pairs':len(labels),'claims':4,
                'selection':'Top three per declarative development claim, fixed before labeling',
                'macro_precision_at_3':sum(r['precision_at_3'] for r in results)/4,
                'relevance_grade_counts':{str(g):list(labels.values()).count(g) for g in range(4)},
                'grade3_fraction':sum(g==3 for g in labels.values())/len(labels),
                'exact_rationale_spans_validated':len(labels),'availability':availability,'results':results,
                'unmeasured':['Held-out effectiveness','NLI/stance accuracy','Citation entailment accuracy','Recall','Scientific certainty','Human reviewer agreement']}
    finally:store.db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('--artifacts',type=Path,default=Path(__file__).resolve().parents[1]/'evaluation/delivery');p.add_argument('--output',type=Path)
    a=p.parse_args();result=recompute(a.snapshot,a.artifacts)
    if a.output:a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
