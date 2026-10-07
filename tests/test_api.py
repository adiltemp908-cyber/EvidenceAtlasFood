"""Integration against an explicitly running local app; no synthetic effectiveness claim."""
import requests

def test_api_workflow():
    base='http://127.0.0.1:8765'
    assert requests.get(base+'/api/health').status_code==200
    evaluation=requests.get(base+'/api/evaluation').json()
    assert evaluation['ai_audit']['sample_pairs']==12
    assert evaluation['ai_audit']['matches_current_corpus'] is True
    assert evaluation['ai_audit']['status'].startswith('Preliminary AI')
    coverage=requests.get(base+'/api/coverage').json()
    assert evaluation['ai_audit']['matches_current_dense_index']==(coverage['dense_index']['level']=='paper')
    run=requests.get(base+'/api/search',params={'q':'dietary sodium blood pressure','method':'bm25'}).json()
    assert run['results'] and run['trace']['index']['corpus']
    p=run['results'][0]
    paper=requests.get(base+'/api/papers/'+p['id']).json()
    assert all(x['paper_id']==p['id'] for x in paper['passages'])
    saved=requests.post(base+'/api/sessions',json={'query':run['query'],'run':run,'notes':'Integration test; no personal data.'})
    assert saved.status_code==201
    export=requests.get(base+'/api/sessions/'+saved.json()['id']+'/export')
    assert export.json()['run']['trace']['index']['corpus']==run['trace']['index']['corpus']
    assert requests.post(base+'/api/sessions',json={'query':'test'},headers={'Origin':'https://untrusted.example'}).status_code==403
    assert requests.get(base+'/api/search',params={'q':'"broken'}).status_code==400

