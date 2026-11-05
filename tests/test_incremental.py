import json
from types import SimpleNamespace
import numpy as np
from evidenceatlas import incremental
from evidenceatlas.config import Settings
from evidenceatlas.models import MODELS
from evidenceatlas.store import Store
from evidenceatlas.parsing import make_passages,screen

def insert(store,pid,body):
    paper={'id':pid,'title':'Nutrition '+pid,'abstract':body,'availability':'abstract-only','metadata':{},'updated':'test'}
    store.save(paper,make_passages(pid,paper['title'],body),'topic','query','accepted','fixture')

def test_reuse_requires_exact_text_and_does_not_activate(tmp_path,monkeypatch):
    old=Store(tmp_path/'old.sqlite');insert(old,'1','Original protein and muscle text.')
    current=Store(tmp_path/'new.sqlite');insert(current,'1','Original protein and muscle text.');insert(current,'2','New egg cholesterol text.')
    old_ids=[dict(r) for r in old.db.execute('SELECT id,paper_id,zone FROM passages ORDER BY id')]
    old_dir=tmp_path/'indexes/source';old_dir.mkdir(parents=True)
    old_vec=np.zeros((len(old_ids),384),dtype=np.float32);old_vec[:,0]=1;np.save(old_dir/'vectors.npy',old_vec)
    (old_dir/'manifest.json').write_text(json.dumps({'level':'passage','model':list(MODELS['embedding']),'corpus':old.fingerprint(),'ids':old_ids,'max_tokens':256}))
    changed=old_ids[0]['id']
    with current.db:current.db.execute('UPDATE passages SET text=? WHERE id=?',('Changed text under same ID',changed))
    encoded=[]
    def encode(texts,**kwargs):
        encoded.extend(texts);v=np.zeros((len(texts),384),dtype=np.float32);v[:,1]=1;return v
    fake=SimpleNamespace(max_seq_length=256,tokenizer=SimpleNamespace(encode=lambda text,**kw:text.split()),encode=encode)
    monkeypatch.setattr(incremental,'embedding_model',lambda settings:fake)
    settings=Settings(tmp_path,reserve_bytes=0)
    result=incremental.build_incremental(current,settings,tmp_path/'old.sqlite',old_dir)
    assert result['reused_vectors']==1 and result['new_vectors']==3
    assert len(encoded)==3 and 'Changed text under same ID' in encoded
    assert not (tmp_path/'indexes/dense-active.json').exists()
    vectors=np.load(result['path']+'/vectors.npy')
    assert (vectors[:,0]==1).sum()==1 and (vectors[:,1]==1).sum()==3

def test_new_food_outcomes_and_agricultural_exclusion():
    assert screen({'title':'Dietary protein supplementation and muscle strength in adults'},['protein'])[0]=='accepted'
    assert screen({'title':'Oat breakfast cereal improves satiety'},['oat','cereal'])[0]=='accepted'
    assert screen({'title':'Broiler feed conversion with protein supplementation'},['protein'])[0]=='excluded'


def test_food_acronyms_and_poultry_do_not_enter_search():
    assert screen({'title':'OATS osteochondral allograft transplantation','abstractText':'Patients with bone degeneration received OATS'},['oat'])[0]=='excluded'
    assert screen({'title':'Egg quality and serum cholesterol in laying ducks','abstractText':'Dietary supplementation improves yolk health'},['egg'])[0]=='needs_review'
