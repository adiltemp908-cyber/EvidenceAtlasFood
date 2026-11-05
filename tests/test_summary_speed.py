import copy
from evidenceatlas.summarization import cached_batches,make_batches


def test_batch_plan_reuse_and_source_model_invalidation(tmp_path):
    class Tokenizer:
        calls=0
        def tokens(self,text):
            self.calls+=1
            return len(text)//3+1
    llm=Tokenizer()
    paper={'id':'P','passages':[{'id':'p','section':'Results','text':'Long study text. '*2000}]}
    identity={'model':'a','runtime':'b'}
    first=cached_batches(paper,llm,tmp_path,identity)
    calls=llm.calls
    assert cached_batches(paper,llm,tmp_path,identity)==first
    assert llm.calls==calls, 'Repeated preparation must not tokenize again'
    changed=copy.deepcopy(paper);changed['passages'][0]['text']+=' New results.'
    other=cached_batches(changed,llm,tmp_path,identity)
    assert llm.calls>calls and other==make_batches(changed,llm)
    calls=llm.calls
    cached_batches(paper,llm,tmp_path,{'model':'new','runtime':'b'})
    assert llm.calls>calls
    calls=llm.calls
    cached_batches(paper,llm,tmp_path,{'model':'a','runtime':'new'})
    assert llm.calls>calls


def test_corrupt_plan_rebuilt_without_losing_source(tmp_path):
    class Tokenizer:
        def tokens(self,text):return len(text)//3+1
    paper={'id':'P','passages':[{'id':'p','section':'Results','text':'Exact original source.'}]}
    llm=Tokenizer();identity={'model':'a','runtime':'b'}
    expected=cached_batches(paper,llm,tmp_path,identity)
    next((tmp_path/'batch-plans').glob('*.json')).write_text('{broken')
    assert cached_batches(paper,llm,tmp_path,identity)==expected
