"""Real passage-index API checks, without repeating unchanged NLI inference."""
import json
from pathlib import Path
import requests

base='http://127.0.0.1:8765';checks=[]
coverage=requests.get(base+'/api/coverage',timeout=30).json()
assert coverage['dense_index']['level']=='passage' and coverage['dense_index']['passages']==37975
for method,rerank in [('dense',False),('hybrid',False),('hybrid',True)]:
    r=requests.get(base+'/api/search',params={'q':'dietary sodium blood pressure','method':method,'rerank':str(rerank).lower(),'fulltext':'true','section':'results','k':5},timeout=120)
    r.raise_for_status();run=r.json();hits=run['results'];assert len(hits)==5 and len({p['id'] for p in hits})==5
    if method=='dense':assert run['trace']['level']=='passage'
    else:assert any(t.get('level')=='passage' and t['method']=='dense' for t in run['trace']['runs'])
    for p in hits:
        assert p['availability']=='full-text'
        source=requests.get(base+'/api/papers/'+p['id'],timeout=30).json()
        for part in p['passages']:
            assert part['zone']=='results'
            assert any(x['id']==part['id'] and x['text']==part['text'] for x in source['passages'])
    checks.append({'method':method,'rerank':rerank,'unique_filtered_results':len(hits),'source_texts_match':True,'latency_ms':run['trace']['latency_ms']})
report={'index_level':'passage','passages':37975,'checks':checks,'quality_claim':'Integration only, not scientific accuracy'}
(Path(__file__).resolve().parents[1]/'docs/checks/passage-integration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
