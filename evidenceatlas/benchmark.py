from __future__ import annotations
import argparse
import hashlib
import json
import random
import sqlite3
import time
from pathlib import Path
from .config import Settings
from .store import Store
from .retrieval import search
from .evaluation import metrics

CLAIMS=[
('coffee_sleep','development','Does afternoon coffee affect sleep?'),
('coffee_sleep','development','Caffeine taken six hours before bedtime reduces total sleep time in healthy adults.'),
('protein_renal','development','Does a high protein diet harm healthy kidneys?'),
('protein_renal','development','Higher dietary protein is safe for every person with chronic kidney disease.'),
('sodium_pressure','development','Does lowering salt intake lower blood pressure?'),
('sodium_pressure','development','All adults get the same blood pressure benefit from sodium reduction.'),
('meal_timing','development','Does late eating cause weight gain even when calories are the same?'),
('meal_timing','development','Time restricted eating improves glucose control independently of weight loss.'),
('sweetener_substitution','held_out','Are artificial sweeteners better than sugar for weight management?'),
('sweetener_substitution','held_out','Replacing sugar-sweetened beverages with low-calorie drinks reduces body weight.'),
('fiber_gut','held_out','Does eating more fibre improve constipation?'),
('fiber_gut','held_out','All dietary fibres have the same effect on the gut microbiome.'),
('fat_substitution','held_out','Are seed oils harmful to heart health?'),
('fat_substitution','held_out','Replacing saturated fat with polyunsaturated fat reduces cardiovascular events.'),
('cooking_nutrients','held_out','Does cooking destroy all vitamins in vegetables?'),
('cooking_nutrients','held_out','Steaming and boiling preserve equal amounts of vitamin C in broccoli.'),
('dairy_bone','held_out','Does drinking milk prevent fractures in older adults?'),
('dairy_bone','held_out','Calcium supplements and dairy foods have identical effects on bone health.'),
('mediterranean','held_out','Does a Mediterranean diet reduce cardiovascular events?'),
('processed_food','held_out','Do ultra processed foods cause weight gain?'),
('vitamin_d','held_out','Does vitamin D supplementation improve health in people who are not deficient?'),
('iron_status','held_out','Does iron supplementation improve fatigue in adults without anemia?'),
('fish_mercury','held_out','Is eating fish unsafe because of mercury?'),
('brown_sugar','held_out','Is brown sugar healthier than white sugar?'),
('energy_drinks','held_out','Do sugar-free energy drinks have no effect on adolescent sleep?'),
('fasting_athletes','held_out','Does intermittent fasting improve endurance performance in athletes?'),
('fruit_juice','held_out','Is fruit juice equivalent to whole fruit for glycemic control?'),
('soy_hormones','held_out','Does soy food consumption affect testosterone in adult men?'),
('tea_iron','held_out','Does drinking tea with meals reduce iron absorption?'),
('nuts_weight','held_out','Does adding nuts to a diet necessarily cause weight gain?'),
('fermented_foods','held_out','Do fermented foods improve digestive symptoms in healthy adults?'),
('turmeric','held_out','Can turmeric in food prevent all inflammatory diseases?'),
]

def write_claims(target):
    claims=[{'id':f'food-{i:03d}','family':family,'split':split,'claim':claim,'label_status':'unjudged','created_by':'AI-authored query set; not gold labels'} for i,(family,split,claim) in enumerate(CLAIMS,1)]
    target.write_text('\n'.join(json.dumps(c) for c in claims)+'\n',encoding='utf-8');return claims

def freeze(settings,name):
    if not name.replace('-','').replace('_','').isalnum():raise ValueError('Use an alphanumeric snapshot name')
    directory=settings.root/'experiments'/name
    if directory.exists():raise ValueError('Snapshot name exists; do not overwrite frozen evidence')
    source=Store(settings.root/'data/normalized/corpus.sqlite')
    size=source.db.execute('PRAGMA page_count').fetchone()[0]*source.db.execute('PRAGMA page_size').fetchone()[0]
    settings.check_space(additional=size,rebuild=size)
    directory.mkdir();dest=sqlite3.connect(directory/'corpus.sqlite');source.db.backup(dest)
    dest.execute('DELETE FROM sessions');dest.commit();dest.close() # Never include private notes in evaluation snapshots.
    Settings.atomic_json(directory/'manifest.json',{'corpus':source.fingerprint(),'counts':source.counts(),'created_unix':time.time(),'judgment_status':'none','private_sessions':'removed'})
    return directory

def run_benchmark(store,claims,out,methods=('tfidf','bm25','structure'),engine=None,settings=None):
    runs=[];pools={};latencies={};start=time.perf_counter()
    for c in claims:
        pool={}
        for method in methods:
            if method in ('dense','hybrid','hybrid_rerank'):
                run=engine.run(store,c['claim'],'hybrid' if method=='hybrid_rerank' else method,k=20,expand=False,rerank=method=='hybrid_rerank')
            else:
                run=search(store,c['claim'],'structure' if method=='structure_expanded' else method,k=20,expand=method=='structure_expanded')
            runs.append({'claim_id':c['id'],'method':method,'query':c['claim'],'ranking':[{'id':p['id'],'score':p['score'],'rank':p['rank'],'passage_ids':[x['id'] for x in p['passages']]} for p in run['results']],'trace':run['trace']})
            latencies.setdefault(method,[]).append(run['trace']['latency_ms'])
            for p in run['results']:pool[p['id']]=p
        docs=list(pool.values());random.Random(20261006).shuffle(docs)
        pools[c['id']]=[{'paper_id':p['id'],'title':p['title'],'availability':p['availability'],'passage_ids':[x['id'] for x in p['passages']],
                        'relevance':None,'stance':None,'compatibility':None,'reviewer':None,'qualification':None,'rationale_spans':[]} for p in docs]
    Settings.atomic_json(out/'runs.json',runs);Settings.atomic_json(out/'blinded-pool.json',pools)
    summary={'claims':len(claims),'methods':list(methods),'latencies_ms':latencies,'elapsed_seconds':time.perf_counter()-start,'quality_metrics':'Pending independent judgments; no effectiveness claim','pool_candidates':sum(map(len,pools.values())),'seed':20261006}
    if settings:
        from .models import index_metadata
        summary['dense_index']=index_metadata(settings);summary['corpus']=store.fingerprint()
    Settings.atomic_json(out/'summary.json',summary);return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['claims','freeze','run']);parser.add_argument('--name',default='development-v1');parser.add_argument('--dense',action='store_true');args=parser.parse_args()
    code_root=Path(__file__).resolve().parents[1];settings=Settings.load();settings.initialize()
    if args.command=='claims':print(len(write_claims(code_root/'evaluation/claims.jsonl')))
    elif args.command=='freeze':print(freeze(settings,args.name))
    else:
        directory=settings.root/'experiments'/args.name
        store=Store(directory/'corpus.sqlite');claims=[json.loads(x) for x in (code_root/'evaluation/claims.jsonl').read_text().splitlines()]
        # Held-out effectiveness cannot be tuned using this development run.
        claims=[c for c in claims if c['split']=='development']
        engine=None;methods=('tfidf','bm25','structure')
        if args.dense:
            from .advanced import ResearchEngine
            engine=ResearchEngine(settings);methods+=('structure_expanded','dense','hybrid','hybrid_rerank')
        print(json.dumps(run_benchmark(store,claims,directory,methods,engine,settings),indent=2))
