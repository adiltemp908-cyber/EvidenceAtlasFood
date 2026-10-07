import json
import pytest
from evidenceatlas.parsing import paragraphs_jats,make_passages,screen,abstract_text
from evidenceatlas.store import Store
from evidenceatlas.retrieval import build,search,tokens,BooleanParser,allowed_docs
from evidenceatlas.evaluation import metrics
from evidenceatlas.evidence import extract,compatibility

@pytest.fixture
def corpus():
    s=Store()
    for pid,title,body in [('1','Caffeine and sleep','400 mg caffeine reduced sleep duration in adults.'),('2','Salt intake','Reducing sodium intake lowered blood pressure.'),('3','Caffeine timing','Morning caffeine did not change sleep duration.')]:
        p={'id':pid,'title':title,'abstract':body,'pmid':pid,'pmcid':None,'doi':None,'year':2020,'species':'unknown','availability':'abstract-only','metadata':{},'updated':'2026-10-06'}
        s.save(p,make_passages(pid,title,body),'test','q','accepted','unit fixture')
    build(s);return s

def test_terms_preserve_negation_and_units():
    assert tokens('NOT 2.5 mg Caffeine')==['not','2.5','mg','caffeine']

def test_positional_phrase_and_boolean(corpus):
    assert allowed_docs(corpus,BooleanParser('"sleep duration" AND NOT morning').parse(),'paper')=={'flat:1'}
    assert allowed_docs(corpus,BooleanParser('sodium OR (caffeine AND morning)').parse(),'paper')=={'flat:2','flat:3'}

def test_baselines_and_filters(corpus):
    for m in ('tfidf','bm25','structure'):
        run=search(corpus,'sodium blood pressure',m)
        assert run['results'][0]['id']=='2'
        assert len({p['id'] for p in run['results']})==len(run['results'])
        assert not search(corpus,'sodium',m,filters={'fulltext':True})['results']

def test_jats_nested_sections_tables_references():
    xml=b'<article><front><permissions><license>CC BY</license></permissions></front><body><sec><title>Results</title><p id="p1">First <italic>result</italic>.</p><sec><title>Subgroup</title><p>Second.</p></sec><table-wrap><label>1</label><caption><p>Dose (mg)</p></caption><table><tr><th>mg</th><td>400</td></tr></table><table-wrap-foot><p>Daily</p></table-wrap-foot></table-wrap></sec></body><back><ref-list><ref>Not evidence</ref></ref-list></back></article>'
    parts,meta=paragraphs_jats(xml)
    assert len(parts)==3
    assert parts[1]['section']=='Results > Subgroup'
    assert '400' in parts[2]['text'] and 'Daily' in parts[2]['text']
    assert all('Not evidence' not in p['text'] for p in parts)
    assert meta['licenses']==['CC BY']

def test_no_body_is_not_fulltext():
    with pytest.raises(ValueError):paragraphs_jats(b'<article><front/></article>')

def test_offsets_and_grounding(corpus):
    p=corpus.paper('1');fields=extract(p)
    mention=fields['dose'][0];span=next(s for s in p['passages'] if s['id']==mention['passage_id'])
    assert span['text'][mention['start']:mention['end']]==mention['value']=='400 mg'
    assert compatibility('400 mg caffeine improves sleep',fields)['dose']['status']=='unknown'

def test_unjudged_not_irrelevant():
    m=metrics(['a','b'],{'a':3},2)
    assert m['precision_at_k'] is None and m['ndcg_at_k'] is None
    assert m['precision_bounds']==[.5,1]

def test_metric_exact_case():
    m=metrics(['a','b'],{'a':3,'b':0,'c':2},2)
    assert m['precision_at_k']==.5 and m['recall_at_k_judged_pool']==.5

def test_industrial_screen():
    d,_,_=screen({'title':'Broiler feed conversion with protein supplementation','abstractText':'Improved crop yield'},['protein'])
    assert d=='excluded'

def test_malformed_query(corpus):
    with pytest.raises(ValueError):search(corpus,'"missing quote')

def test_abstract_preserves_inequalities():
    text=abstract_text('<h4>Results</h4>p < 0.05, 95% CI 1.2-3.4; x > 2. <h4>Conclusion</h4>No effect at p &gt; 0.1.')
    assert 'p < 0.05, 95% CI 1.2-3.4; x > 2.' in text
    assert 'p > 0.1' in text

def test_sentence_offsets(corpus):
    for p in corpus.paper('1')['passages']:
        assert p['sentences']
        assert all(p['text'][s['start']:s['end']] for s in p['sentences'])

def test_topical_oil_not_dietary():
    decision,_,_=screen({'title':'Seed oil topical ointment for wound healing','abstractText':'Cell proliferation and cancer markers'},['oil'])
    assert decision=='excluded'

def test_protein_dialysis_outcome():
    decision,_,_=screen({'title':'Oral protein supplements in hemodialysis','abstractText':'A randomized clinical trial in patients'},['protein'])
    assert decision=='accepted'

@pytest.fixture
def audit_files(corpus,tmp_path):
    import sqlite3
    from evidenceatlas.audit import CLAIMS
    snapshot=tmp_path/'snapshot';snapshot.mkdir();artifacts=tmp_path/'artifacts';artifacts.mkdir()
    dest=sqlite3.connect(snapshot/'corpus.sqlite');corpus.db.backup(dest);dest.close()
    runs=[];labels=[]
    for cid in CLAIMS:
        runs.append({'claim_id':cid,'method':'hybrid_rerank','query':'Fixture claim','ranking':[{'id':pid} for pid in ('1','2','3')]})
        for pid,grade in [('1',2),('2',1),('3',0)]:
            part=next(p for p in corpus.paper(pid)['passages'] if p['zone']=='abstract')
            labels.append({'claim_id':cid,'paper_id':pid,'reviewer_id':'unit-fixture','reviewer_kind':'AI','qualifications':'Synthetic unit test, not a benchmark label','relevance':grade,'stance':'insufficient to establish','compatibility':'unknown','corpus':corpus.fingerprint(),'rationale':[{'paper_id':pid,'passage_id':part['id'],'start':0,'end':len(part['text']),'quote':part['text']}]})
    (artifacts/'runs.json').write_text(json.dumps(runs))
    (artifacts/'ai-judgments.jsonl').write_text('\n'.join(json.dumps(j) for j in labels))
    return snapshot,artifacts,labels

def test_audit_recomputes_saved_labels(audit_files):
    from evidenceatlas.audit import recompute
    snapshot,artifacts,_=audit_files;r=recompute(snapshot,artifacts)
    assert r['sample_pairs']==12 and r['macro_precision_at_3']==pytest.approx(1/3)
    assert r['grade3_fraction']==0 and r['exact_rationale_spans_validated']==12

@pytest.mark.parametrize('corruption',['quote','reviewer','missing'])
def test_audit_rejects_invalid_evidence(audit_files,corruption):
    from evidenceatlas.audit import recompute
    snapshot,artifacts,labels=audit_files
    if corruption=='quote':labels[0]['rationale'][0]['quote']='Invented finding'
    elif corruption=='reviewer':labels[0]['reviewer_kind']='human'
    else:labels.pop()
    (artifacts/'ai-judgments.jsonl').write_text('\n'.join(json.dumps(j) for j in labels))
    with pytest.raises(ValueError):recompute(snapshot,artifacts)
