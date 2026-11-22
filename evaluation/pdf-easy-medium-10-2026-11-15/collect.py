"""Collect actual rankings without modifying the corpus or application settings."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
APP = HERE.parents[1]
sys.path.insert(0, str(APP))
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.advanced import ResearchEngine
from evidenceatlas.models import MODELS, index_metadata

QUESTIONS = [
 ('Q01','Easy','Does drinking coffee affect sleep?','Human coffee/caffeine consumption and sleep quality, duration or onset; caffeine trials qualify as constituent evidence.'),
 ('Q02','Easy','Does reducing salt intake lower blood pressure?','Human dietary salt/sodium reduction and measured blood pressure; potassium-only interventions are partial background.'),
 ('Q03','Easy','Does eating more fiber help with constipation?','Human dietary fiber or fiber supplementation and constipation, stool frequency or consistency; other digestive outcomes alone are background.'),
 ('Q04','Easy','Does drinking milk help keep bones strong?','Human milk/dairy intake and bone density, bone mineral content, fractures or bone turnover; dairy mixtures can be directly useful but are less specific than milk.'),
 ('Q05','Easy','Does boiling vegetables reduce their vitamin C content?','Measured vitamin C/ascorbic acid retention after boiling vegetables; food laboratory studies are directly applicable, unlike human-health queries.'),
 ('Q06','Medium','Does eating oats lower LDL cholesterol?','Human oat/oat beta-glucan consumption and LDL cholesterol; other cereal fibers or other lipid outcomes alone are partial evidence.'),
 ('Q07','Medium','Does eating nuts cause weight gain in adults?','Adult human nut consumption and body weight/adiposity; includes null findings and energy compensation, not only weight gain.'),
 ('Q08','Medium','Is yogurt easier to digest than milk for people with lactose intolerance?','Human yogurt/fermented milk versus ordinary milk or lactose digestion in lactose malabsorbers; generic probiotic/gut health studies without lactose outcomes are background.'),
 ('Q09','Medium','Are sugary drinks linked to type 2 diabetes?','Human sugar-sweetened beverage intake and type 2 diabetes incidence/risk; association is sufficient, causality is not required; glucose/weight alone is partial evidence.'),
 ('Q10','Medium','Does extra protein help build muscle during resistance training?','Human dietary protein supplementation/intake during resistance training and muscle mass or hypertrophy; strength alone or exercise without protein comparison is partial evidence.'),
]
METHODS=['tfidf','bm25','structure','dense','hybrid','hybrid_rerank']

def save(name, value):
    (HERE/name).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')

def main():
    if (HERE/'runs.json').exists():
        raise SystemExit('Rankings already exist; preserve this evaluation snapshot.')
    settings=Settings.load()
    store=Store.__new__(Store)
    store.db=sqlite3.connect((settings.root/'data/normalized/corpus.sqlite').as_uri()+'?mode=ro',uri=True)
    store.db.row_factory=sqlite3.Row
    store.db.execute('PRAGMA query_only=ON')
    store.db.execute('BEGIN')
    fingerprint=store.fingerprint()
    active=(settings.root/'indexes/dense-active.json').read_bytes()
    protocol={
      'date':'2026-11-15','source_pdf':'08eval (1).pdf',
      'source_pdf_sha256':'3117b863bed79cbf615a7781cef67102b1b4fd9c60df0944f09d2983bc9ff2b5',
      'questions':[dict(id=i,difficulty=d,query=q,information_need=n) for i,d,q,n in QUESTIONS],
      'methods':METHODS,'depth':10,'expand':True,'recency':False,'filters':{},
      'configuration_note':'Existing implementations, shared query expansion enabled, relevance-only ranking (recency preference disabled). No tuning or query rewrites after collection.',
      'pool':'Union of the top 10 unique parent papers from all six methods, separately for each query.',
      'grades':{'0':'Not relevant to the information need','1':'Related/background only; indirect exposure/outcome or species mismatch','2':'Directly useful but partial or materially limited applicability','3':'Directly addresses the information need with applicable population/exposure/outcome'},
      'binary_relevance_threshold':2,'reviewer_kind':'AI','reviewer':'Codex assistant; not independent human or expert judgments',
      'judgment_basis':'Titles and query-focused abstract excerpts for initial screening; complete abstracts and retrieved passages for ambiguous cases. Full stored abstracts and retrieved text retained; no exhaustive full-paper review.',
      'primary_study_vs_review_rule':'Primary-study background references alone count as background; directly useful source-study outcomes qualify. Review syntheses can qualify even when the relevant material is in a subsection.',
      'dcg_gain':'linear grade, as PDF pages 42-50; logarithm base 2',
      'idcg':'Common ideal top-k from all judged pooled papers for that query, shared across methods.',
      'recall_and_ap_scope':'Relevant documents in judged pool only. AP@10 denominator is all relevant pooled documents, not min(R,10). Unretrieved relevant pool documents contribute zero. Not full-corpus recall or untruncated MAP.',
      'interpolation':'11 levels 0.0 to 1.0; max observed P@r with pool Recall@r >= level; zero beyond observed recall at depth 10.',
      'query_selection':'Ten AI-authored easy/medium questions fixed before viewing rankings; convenience diagnostic set, with topics overlapping previous development evaluations; not held-out.',
      'corpus':fingerprint,'counts':store.counts(),'models':MODELS,'dense_index':index_metadata(settings),
      'git_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=APP,text=True).strip(),
      'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (APP/'evidenceatlas').glob('*.py')},
    }
    save('protocol.json',protocol)
    engine=ResearchEngine(settings)
    warmstart=time.perf_counter()
    engine.run(store,'dietary nutrition health',method='hybrid',k=1,expand=True,rerank=True)
    protocol['warmup_seconds']=time.perf_counter()-warmstart
    save('protocol.json',protocol)
    runs=[];pool={}
    for qi,(qid,difficulty,query,need) in enumerate(QUESTIONS):
        methods=METHODS[qi%6:]+METHODS[:qi%6]
        for method in methods:
            run=engine.run(store,query,method='hybrid' if method=='hybrid_rerank' else method,k=10,expand=True,rerank=method=='hybrid_rerank')
            assert len(run['results'])==10
            assert len({p['id'] for p in run['results']})==10
            runs.append(dict(query_id=qid,query=query,method=method,**{k:v for k,v in run.items() if k!='query'}))
            for p in run['results']:
                key=(qid,p['id'])
                if key not in pool:
                    pool[key]={k:p.get(k) for k in ['id','title','abstract','year','availability','species','pmid','pmcid','doi']}
                    pool[key].update(query_id=qid,source_passages={})
                for passage in p['passages']:
                    pool[key]['source_passages'][passage['id']]=passage
            save('runs.json',runs)
            print(f'{qid} {method}: {len(run["results"])} papers, {run["trace"]["latency_ms"]:.0f} ms',flush=True)
    documents=[]
    for key,p in sorted(pool.items()):
        p['source_passages']=list(p['source_passages'].values());documents.append(p)
    save('pool.json',documents)
    for qid,_,query,need in QUESTIONS:
        docs=[p for p in documents if p['query_id']==qid]
        lines=[f'{qid}: {query}',f'Information need: {need}']
        for n,p in enumerate(docs,1):
            lines += [f'\n[{n:02}] {p["id"]} | {p["title"]}',f'Availability: {p["availability"]}; species: {p["species"]}',f'ABSTRACT: {p["abstract"] or "[No abstract]"}']
            if not p['abstract']:
                lines += [f'PASSAGE {s["id"]} ({s["zone"]}): {s["text"]}' for s in p['source_passages']]
        (HERE/f'review-{qid}.txt').write_text('\n'.join(lines),encoding='utf-8')
    assert store.fingerprint()==fingerprint
    assert (settings.root/'indexes/dense-active.json').read_bytes()==active
    save('collection-checks.json',dict(runs=len(runs),ranked_positions=sum(len(r['results']) for r in runs),pooled_query_paper_pairs=len(documents),pool_per_query={q:sum(p['query_id']==q for p in documents) for q,_,_,_ in QUESTIONS},snapshot_unchanged=True))
    store.db.rollback();store.db.close()
    print('COLLECTION COMPLETE',flush=True)

if __name__=='__main__': main()
