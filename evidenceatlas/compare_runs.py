"""Compare frozen paper/passage retrieval runs without inventing new relevance labels."""
from pathlib import Path
import argparse,json,statistics
from .evaluation import metrics

def compare(before,after,judgments):
    left={(r['claim_id'],r['method']):r for r in json.loads((before/'runs.json').read_text())}
    right={(r['claim_id'],r['method']):r for r in json.loads((after/'runs.json').read_text())}
    corpora={r['trace']['index']['corpus'] for r in [*left.values(),*right.values()]}
    if len(corpora)!=1:raise ValueError('Comparisons require one identical frozen corpus')
    labels={}
    for line in judgments.read_text(encoding='utf-8').splitlines():
        v=json.loads(line)
        if v['reviewer_kind']!='AI':raise ValueError('Expected explicitly AI-labeled diagnostic pool')
        if v['corpus'] not in corpora:raise ValueError('AI labels belong to a different corpus')
        labels.setdefault(v['claim_id'],{})[v['paper_id']]=v['relevance']
    rows=[]
    for key,b in sorted(right.items()):
        if key not in left:raise ValueError('No matching baseline run')
        a=left[key]
        if a['query']!=b['query'] or a['trace']['index']['corpus']!=b['trace']['index']['corpus']:
            raise ValueError('Query or corpus changed; this is not a controlled index comparison')
        old=[p['id'] for p in a['ranking'][:10]];new=[p['id'] for p in b['ranking'][:10]]
        overlap=set(old)&set(new);union=set(old)|set(new)
        row={'claim_id':key[0],'method':key[1],'query':b['query'],'shared_top10':len(overlap),
             'jaccard_top10':len(overlap)/len(union) if union else 1,'same_order':old==new,
             'before_top3':old[:3],'after_top3':new[:3],
             'before_ms':a['trace']['latency_ms'],'after_ms':b['trace']['latency_ms']}
        if key[1]=='hybrid_rerank' and key[0] in labels:
            m=metrics(new,labels[key[0]],3)
            row['baseline_AI_labels_on_new_top3']={k:m[k] for k in ('judged_fraction','precision_at_k','precision_bounds')}
        rows.append(row)
    by_method={}
    for method in sorted({r['method'] for r in rows}):
        selected=[r for r in rows if r['method']==method]
        by_method[method]={'claims':len(selected),'mean_shared_top10':statistics.mean(r['shared_top10'] for r in selected),
            'queries_with_changed_order':sum(not r['same_order'] for r in selected),
            'before_median_ms':statistics.median(r['before_ms'] for r in selected),
            'after_median_ms':statistics.median(r['after_ms'] for r in selected)}
    return {'before':before.name,'after':after.name,'corpus':next(iter(right.values()))['trace']['index']['corpus'],
            'methods':by_method,'runs':rows,'interpretation':'Rank changes measure retrieval behavior, not improvement. New results are unjudged unless already in the small baseline AI pool. No accuracy gain or recall claim.',
            'timing_limit':'Single ordered runs; cache, cold model loads and host contention differ.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('judgments',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=compare(a.before,a.after,a.judgments);a.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'methods':result['methods'],'interpretation':result['interpretation']},indent=2))
