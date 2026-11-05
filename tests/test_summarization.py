import json
import time
from pathlib import Path
import pytest
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.parsing import make_passages
from evidenceatlas.summarization import SummaryManager, make_batches, validate_findings, numbers_grounded, concepts_grounded, EXTRACT, SELECT, POINT, VERIFY
from evidenceatlas.local_llm import LocalLLM


class FakeLLM:
    def __init__(self):self.calls=0;self.reject=False;self.callback=None
    def manifest(self):return {"model_sha256":"fixture-model","runtime_sha256":"fixture-runtime","model":"fixture"}
    def ensure(self):pass
    def tokens(self,text):return len(text)//3+1
    def generate(self,system,user,schema,max_tokens):
        self.calls+=1
        data=json.loads(user)
        if system==EXTRACT:
            if self.callback:self.callback()
            source=next((s for s in data["sources"] if "reduced" in s["text"]),None)
            return {"findings":[{"source":source["label"],"quote":source["text"],
                "statement":"In this trial sodium reduction lowered blood pressure."}] if source else []},{}
        if system==SELECT:
            return {"selected_note_ids":[data["evidence_notes"][0]["id"]]},{}
        if system==POINT:
            assert "statement" not in data["source"]
            assert data["source"]["context"] == "", "Adjacent table rows must not reach answer generation"
            return {"text":"Sodium reduction lowered blood pressure in the reported trial."},{}
        assert all("statement" not in s and "context" in s for s in data["sources"])
        assert system==VERIFY
        return {"supported":not self.reject,"directly_answers":True,"reason":"fixture"},{}


@pytest.fixture
def setup(tmp_path):
    root=tmp_path/"data/normalized";root.mkdir(parents=True)
    s=Store(root/"corpus.sqlite")
    paper={"id":"P1","title":"A sodium trial","abstract":"In adults, reduced sodium lowered blood pressure.",
           "availability":"abstract-only","metadata":{},"updated":"test"}
    s.save(paper,make_passages("P1",paper["title"],paper["abstract"]),"sodium","q","accepted","fixture")
    fingerprint=s.fingerprint();s.db.close()
    return Settings(tmp_path,reserve_bytes=0),fingerprint


def wait(manager,job):
    end=time.monotonic()+8
    while manager.active and time.monotonic()<end:time.sleep(.01)
    assert manager.active is None
    return manager.status(job)


def test_exact_quotes_and_offsets():
    sources=[{"label":"S1","paper_id":"P","passage_id":"p","section":"Results","start":100,
              "text":"Some prefix. This was a null result in adults. End."}]
    valid,bad=validate_findings({"findings":[
        {"source":"S1","quote":"This was a null result in adults.","statement":"No effect observed."},
        {"source":"S1","quote":"This greatly improved health.","statement":"Invented finding"},
        {"source":"S9","quote":"This was a null result in adults.","statement":"Wrong source"}]},sources)
    assert len(valid)==1 and bad==2
    assert valid[0]["start"]==113
    assert sources[0]["text"][valid[0]["start"]-100:valid[0]["end"]-100]==valid[0]["quote"]


def test_reject_numbers_absent_from_cited_source():
    sources=[{"quote":"The change was −7.03 mg/dL (p = 0.03).","context":"30 adults were studied."}]
    assert numbers_grounded("The change was -7.03 mg/dL in 30 adults.",sources)
    assert not numbers_grounded("The reduction had p = 0.06.",sources)


def test_reject_cross_study_species_and_outcome_blending():
    sources=[{"quote":"Serum cholesterol decreased in rats.","context":"","title":"Rat study"}]
    assert concepts_grounded("Cholesterol decreased in rats.",sources)
    assert not concepts_grounded("Cholesterol and triglycerides decreased in mice.",sources)
    assert not concepts_grounded("Cholesterol decreased compared with baseline.",sources)
    assert not concepts_grounded("Cholesterol decreased compared with placebo.",sources)


def test_all_long_source_text_is_batched():
    text=("Long trial text with dose 5µg. "*2000)
    paper={"id":"P","passages":[{"id":"p","section":"Results","text":text}]}
    batches=make_batches(paper,FakeLLM());spans=[s for b in batches for s in b]
    assert len(batches)>1
    assert spans[0]["start"]==0 and spans[-1]["end"]==len(text)
    assert all(b["start"]<=a["end"] for a,b in zip(spans,spans[1:]))
    assert all(s["text"]==text[s["start"]:s["end"]] for s in spans)


def test_complete_cached_summary_and_source_scope(setup):
    settings,corpus=setup;llm=FakeLLM();manager=SummaryManager(settings,llm)
    job=manager.start("Does sodium affect blood pressure?",["P1"],corpus)["id"]
    state=wait(manager,job)
    assert state["status"]=="complete",state
    result=state["result"]
    assert result["papers"][0]["passages_read"]==2
    assert result["papers"][0]["availability"]=="abstract-only"
    assert result["paragraphs"][0]["citations"]==["N1"]
    count=llm.calls
    assert manager.start("Does sodium affect blood pressure?",["P1"],corpus)["cached"] is True
    assert llm.calls==count
    with pytest.raises(ValueError):manager.start("Does sodium affect blood pressure?",["P1"],"stale")
    with pytest.raises(ValueError):manager.start("Does sodium affect blood pressure?",["P1","P1"],corpus)
    with pytest.raises(ValueError):manager.status("../escape")


def test_unsupported_synthesis_is_not_shown(setup):
    settings,corpus=setup;llm=FakeLLM();llm.reject=True
    manager=SummaryManager(settings,llm)
    state=wait(manager,manager.start("Does sodium affect pressure?",["P1"],corpus)["id"])
    assert state["result"]["status"]=="insufficient"
    assert not state["result"]["paragraphs"]
    assert state["result"]["rejected_items"]==1
    assert state["result"]["insufficiency_reason"]=="validation_failed"


def test_related_findings_can_abstain_before_drafting(setup):
    settings,corpus=setup;llm=FakeLLM();original=llm.generate
    def indirect(system,user,*args,**kwargs):
        if system==SELECT:
            sources=json.loads(user)['evidence_notes']
            assert sources and 'quote' in sources[0] and 'statement' not in sources[0]
            return {'selected_note_ids':[]},{}
        assert system!=POINT, 'Indirect findings must not be drafted as answers'
        return original(system,user,*args,**kwargs)
    llm.generate=indirect;manager=SummaryManager(settings,llm)
    state=wait(manager,manager.start('Does sodium improve sleep in children?',['P1'],corpus)['id'])
    result=state['result']
    assert result['status']=='insufficient' and not result['paragraphs']
    assert result['insufficiency_reason']=='no_direct_evidence'
    assert result['citations'], 'Keep related quotations available for inspection'
    assert '1 retrieved paper I read' in result['message']
    assert 'does not mean no such studies exist' in result['message']


@pytest.mark.parametrize('directness',[False,None])
def test_supported_but_indirect_or_unknown_draft_is_suppressed(setup,directness):
    settings,corpus=setup;llm=FakeLLM();original=llm.generate
    def verdict(system,*args,**kwargs):
        if system==VERIFY:
            result={'supported':True,'reason':'Wrong outcome or unconfirmed applicability'}
            if directness is not None:result['directly_answers']=directness
            return result,{}
        return original(system,*args,**kwargs)
    llm.generate=verdict;manager=SummaryManager(settings,llm)
    state=wait(manager,manager.start('Does sodium improve sleep?',['P1'],corpus)['id'])
    result=state['result']
    assert result['status']=='insufficient' and not result['paragraphs']
    assert result['insufficiency_reason']==('no_direct_evidence' if directness is False else 'validation_failed')


def test_no_extracted_findings_gives_scoped_abstention(setup):
    settings,corpus=setup;llm=FakeLLM()
    def empty(system,*args,**kwargs):
        assert system==EXTRACT
        return {'findings':[]},{}
    llm.generate=empty;manager=SummaryManager(settings,llm)
    result=wait(manager,manager.start('Does sodium improve sleep?',['P1'],corpus)['id'])['result']
    assert result['insufficiency_reason']=='no_direct_evidence'
    assert not result['paragraphs'] and not result['citations']


def test_direct_null_finding_remains_an_answer(setup):
    settings,_=setup
    store=Store(settings.root/'data/normalized/corpus.sqlite')
    p={'id':'P1','title':'Sodium trial','abstract':'Reduced sodium did not change blood pressure in adults.',
       'availability':'abstract-only','metadata':{},'updated':'null-result'}
    store.save(p,make_passages('P1',p['title'],p['abstract']),'sodium','q','accepted','fixture')
    corpus=store.fingerprint();store.db.close()
    llm=FakeLLM();original=llm.generate
    def null_finding(system,user,*args,**kwargs):
        if system==EXTRACT:
            source=next(s for s in json.loads(user)['sources'] if s['section']=='Abstract')
            return {'findings':[{'source':source['label'],'quote':source['text'],'statement':source['text']}]},{}
        if system==POINT:return {'text':p['abstract']},{}
        return original(system,user,*args,**kwargs)
    llm.generate=null_finding;manager=SummaryManager(settings,llm)
    result=wait(manager,manager.start('Does sodium affect blood pressure?',['P1'],corpus)['id'])['result']
    assert result['status']=='answer' and result['insufficiency_reason'] is None
    assert 'did not change' in result['paragraphs'][0]['text']


def test_cancel_retains_sections_without_publishing_answer(setup):
    settings,corpus=setup;llm=FakeLLM();manager=SummaryManager(settings,llm)
    llm.callback=lambda:manager.cancel_event.set()
    job=manager.start("Does sodium affect pressure?",["P1"],corpus)["id"]
    state=wait(manager,job)
    assert state["status"]=="cancelled"
    assert list(manager.folder(job).glob("paper-*-part-*.json"))
    assert not (manager.folder(job)/"result.json").exists()


def test_context_overflow_cannot_silently_truncate(tmp_path):
    llm=LocalLLM(Settings(tmp_path))
    class Response:
        def raise_for_status(self):pass
        def json(self):return {"prompt":"oversized"}
    class Session:
        def post(self,url,**kw):
            assert url.endswith("/apply-template")
            return Response()
    llm.session=Session();llm.tokens=lambda text:9000
    with pytest.raises(ValueError,match="no text was silently truncated"):
        llm.generate("system","source",{},max_tokens=100)


def test_runtime_receives_nested_strict_schema(tmp_path):
    llm=LocalLLM(Settings(tmp_path));llm.tokens=lambda text:10
    schema={"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"],"additionalProperties":False}
    class Response:
        def __init__(self,data):self.data=data
        def raise_for_status(self):pass
        def json(self):return self.data
    class Session:
        def post(self,url,**kw):
            if url.endswith("/apply-template"):return Response({"prompt":"prompt"})
            assert kw["json"]["response_format"]=={"type":"json_schema","json_schema":{"name":"evidence","strict":True,"schema":schema}}
            return Response({"choices":[{"finish_reason":"stop","message":{"content":'{"ok":true}'}}],"usage":{}})
    llm.session=Session()
    assert llm.generate("system","source",schema)[0]=={"ok":True}


def test_status_write_retries_transient_windows_file_lock(setup,monkeypatch):
    settings,_=setup;manager=SummaryManager(settings,FakeLLM())
    original=Settings.atomic_json;calls=[]
    def write(path,value):
        calls.append(1)
        if len(calls)==1:raise PermissionError("Transient Windows sharing violation")
        original(path,value)
    monkeypatch.setattr(Settings,"atomic_json",write)
    path=manager.root/"status-test.json"
    manager.write_status(path,{"status":"running"})
    assert len(calls)==2 and json.loads(path.read_text())["status"]=="running"


def test_section_cache_reused_after_unrelated_corpus_growth(setup):
    settings,corpus=setup;llm=FakeLLM();original=llm.generate;reads=[]
    def counted(system,*args,**kwargs):
        if system==EXTRACT:reads.append(1)
        return original(system,*args,**kwargs)
    llm.generate=counted;manager=SummaryManager(settings,llm)
    query='Does sodium affect blood pressure?'
    wait(manager,manager.start(query,['P1'],corpus)['id']);count=len(reads)
    store=Store(settings.root/'data/normalized/corpus.sqlite')
    p={'id':'P2','title':'Another paper','abstract':'A different topic.','availability':'abstract-only','metadata':{},'updated':'test'}
    store.save(p,make_passages('P2',p['title'],p['abstract']),'other','other','accepted','fixture')
    corpus=store.fingerprint();store.db.close()
    state=wait(manager,manager.start(query,['P1'],corpus)['id'])
    assert state['status']=='complete' and len(reads)==count
    assert state['result']['cached_section_groups']>0


def test_local_timeout_retries_current_step_once(setup):
    import requests
    settings,corpus=setup;llm=FakeLLM();original=llm.generate;attempts=[]
    def transient(system,*args,**kwargs):
        if system==EXTRACT:
            attempts.append(1)
            if len(attempts)==1:raise requests.Timeout('fixture transient timeout')
        return original(system,*args,**kwargs)
    llm.generate=transient;manager=SummaryManager(settings,llm)
    state=wait(manager,manager.start('Does sodium affect pressure?',['P1'],corpus)['id'])
    assert state['status']=='complete' and len(attempts)==2
