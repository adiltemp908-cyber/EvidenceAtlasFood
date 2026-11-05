import json
from types import SimpleNamespace
import numpy as np
import pytest
from evidenceatlas.chunking import split_spans, build_chunked, digest
from evidenceatlas import chunking
from evidenceatlas.config import Settings
from evidenceatlas.models import MODELS
from evidenceatlas.dense import DenseIndex, fuse
from test_incremental import insert
from evidenceatlas.store import Store
from test_core import corpus


class Tokenizer:
    is_fast = True
    def num_special_tokens_to_add(self, pair=False): return 2
    def __call__(self, text, **kwargs):
        import re
        offsets = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
        return {"offset_mapping": offsets}
    def encode(self, text, add_special_tokens=True, **kwargs):
        return [1] * (len(text.split()) + (2 if add_special_tokens else 0))


def test_boundaries_overlap_and_exact_unicode_source():
    tokenizer = Tokenizer()
    for text in ["", "short text", " ".join(["dose–5μg"] * 254), "  " + " ".join(["dose–5μg"] * 700) + "\n"]:
        spans = split_spans(text, tokenizer)
        assert spans[0][0] == 0 and spans[-1][1] == len(text)
        assert all(len(tokenizer.encode(text[a:b])) <= 256 for a,b in spans)
        assert all(y[0] <= x[1] for x,y in zip(spans,spans[1:]))
    assert len(split_spans("x " * 254, tokenizer)) == 1
    assert len(split_spans("x " * 255, tokenizer)) == 2
    with pytest.raises(ValueError):split_spans("x", tokenizer, overlap=254)


def test_build_reuses_short_inputs_and_future_expansion(tmp_path, monkeypatch):
    old=Store(tmp_path/"baseline.sqlite")
    insert(old,"1","nutrition " * 600)
    new=Store(tmp_path/"new.sqlite")
    old.db.backup(new.db)
    old_dir=tmp_path/"indexes/legacy";old_dir.mkdir(parents=True)
    ids=[dict(r) for r in old.db.execute("SELECT id,paper_id,zone FROM passages ORDER BY id")]
    vectors=np.zeros((len(ids),384),dtype="float32");vectors[:,0]=1
    np.save(old_dir/"vectors.npy",vectors)
    (old_dir/"manifest.json").write_text(json.dumps(dict(model=list(MODELS["embedding"]),level="passage",max_tokens=256,corpus=old.fingerprint(),ids=ids)))
    inputs=[]
    def encode(texts,**kw):
        inputs.extend(texts)
        v=np.zeros((len(texts),384),dtype="float32");v[:,1]=1
        return v
    monkeypatch.setattr(chunking,"embedding_model",lambda s:SimpleNamespace(tokenizer=Tokenizer(),max_seq_length=256,encode=encode))
    settings=Settings(tmp_path,reserve_bytes=0)
    result=build_chunked(new,settings,tmp_path/"baseline.sqlite",old_dir)
    assert result["split_passages"]==1 and result["reused_vectors"]==1
    assert result["new_vectors"]==3 and all(len(Tokenizer().encode(t))<=256 for t in inputs)
    assert new.fingerprint()==old.fingerprint()
    assert not (tmp_path/"indexes/dense-active.json").exists()
    newer=Store(tmp_path/"expanded.sqlite");new.db.backup(newer.db)
    insert(newer,"2","New food results.")
    inputs.clear()
    second=build_chunked(newer,settings,tmp_path/"new.sqlite",result["path"])
    assert second["reused_vectors"]==4 and second["new_vectors"]==2
    assert len(inputs)==2


def test_dense_span_survives_hybrid_without_modifying_source(corpus):
    original=corpus.paper("1")["passages"]
    index=DenseIndex.__new__(DenseIndex)
    source=next(p for p in corpus.paper("1")["passages"] if p["zone"]=="abstract")
    lo=source["text"].index("reduced");hi=len(source["text"])
    index.meta={"model":["fixture","fixture"],"corpus":corpus.fingerprint(),"level":"passage",
                "ids":[dict(source,char_start=lo,char_end=hi)]}
    index.vectors=np.eye(1,384,dtype="float32")
    index.model=SimpleNamespace(encode=lambda *a,**kw:np.eye(1,384,dtype="float32"))
    dense=index.search(corpus,"sleep")
    p=dense["results"][0]
    assert p["semantic_match"]["text"]==source["text"][lo:hi]
    assert p["passages"][0]["text"]==source["text"]
    lexical={"query":"sleep","trace":{"method":"bm25","index":dense["trace"]["index"],"latency_ms":0},
             "results":[dict(p,passages=corpus.paper("1")["passages"])]}
    lexical["results"][0].pop("semantic_match")
    result=fuse([lexical,dense])["results"][0]
    assert result["passages"][0]["id"]==source["id"]
    assert result["semantic_match"]["char_start"]==lo
    assert corpus.paper("1")["passages"]==original


def test_reranker_uses_semantic_tail_when_abstract_unavailable(corpus,tmp_path):
    from evidenceatlas.advanced import ResearchEngine
    from pathlib import Path
    (tmp_path/"indexes").mkdir()
    (tmp_path/"indexes/dense-active.json").write_text(json.dumps({"path":"test"}))
    paper=corpus.paper("1")
    paper['abstract']=''
    source=next(p for p in paper["passages"] if p["zone"]=="abstract")
    paper.update(score=1,rank=1,score_components=[],passages=[source],
                 semantic_match={"passage_id":source["id"],"text":"sleep duration in adults."})
    result={"query":"sleep","results":[paper],"trace":{"method":"dense","latency_ms":0}}
    engine=ResearchEngine(SimpleNamespace(root=tmp_path))
    engine.dense=SimpleNamespace(directory=Path("test"),search=lambda *a,**kw:result)
    seen=[]
    def predict(pairs,**kw):
        seen.extend(pairs)
        return [1.]
    class PairTokenizer:
        def encode(self,*args,**kwargs):return ' '.join(args).split()
    engine.reranker=SimpleNamespace(predict=predict,tokenizer=PairTokenizer())
    out=engine.run(corpus,"sleep",method="dense",rerank=True)
    assert seen==[("sleep",paper["title"]+" sleep duration in adults.")]
    assert out["results"][0]["passages"][0]["text"]==source["text"]
