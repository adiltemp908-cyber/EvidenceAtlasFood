"""Bounded real-corpus integration, not an accuracy benchmark. Requires local server."""
import json
from pathlib import Path
import requests

base='http://127.0.0.1:8765'
report={'checks':[],'effectiveness':'Not measured; these are integration checks'}
for method,rerank in [('dense',False),('hybrid',False),('hybrid',True)]:
    r=requests.get(base+'/api/search',params={'q':'dietary sodium blood pressure','method':method,'rerank':str(rerank).lower(),'fulltext':'true','section':'results','k':5},timeout=120)
    r.raise_for_status();v=r.json()
    assert v['results'] and len({p['id'] for p in v['results']})==len(v['results'])
    assert all(p['availability']=='full-text' and all(x['zone']=='results' for x in p['passages']) for p in v['results'])
    if rerank:assert v['trace']['reranker']['pair_limit']==20
    report['checks'].append({'method':method,'rerank':rerank,'unique_filtered_results':len(v['results']),'latency_ms':v['trace']['latency_ms']})
assert requests.get(base+'/api/search',params={'q':'sodium AND salt','method':'dense'},timeout=30).status_code==400
report['checks'].append('Dense search rejects unsupported Boolean constraints')
r=requests.post(base+'/api/analyze',json={'claim':'Reducing dietary sodium lowers blood pressure in adults.'},timeout=180)
r.raise_for_status();v=r.json();assert 0<len(v['predictions'])<=24
sources={s['passage_id']:s for s in v['sources']}
for prediction in v['predictions']:
    source=sources[prediction['passage_id']]
    paper=requests.get(base+'/api/papers/'+source['paper_id'],timeout=30).json()
    p=next(p for p in paper['passages'] if p['id']==source['passage_id'])
    assert p['text']==source['text'] and p['zone'] in ('results','conclusion','abstract','discussion','limitations')
    assert prediction['compatibility'].startswith('unknown')
report['checks'].append({'experimental_nli_predictions':len(v['predictions']),'all_sources_exact':True,'title_only_inputs':0,'alternative_searches':len(v['counterevidence']['runs'])})
root=Path(__file__).resolve().parents[1]
(root/'docs/checks/model-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
