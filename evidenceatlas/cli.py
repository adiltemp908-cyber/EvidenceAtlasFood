from __future__ import annotations
import argparse
import gzip
import json
import statistics
import time
from dataclasses import replace
from pathlib import Path
import psutil
from .config import Settings
from .store import Store
from .acquisition import EuropePMC,ingest
from .retrieval import build,search

def main():
    parser=argparse.ArgumentParser(description='EvidenceAtlas Food reproducible local pipeline')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('ingest','probe'):
        p=sub.add_parser(name);p.add_argument('--topics',nargs='+');p.add_argument('--pages',type=int,default=1);p.add_argument('--page-size',type=int,default=10);p.add_argument('--seconds',type=int,default=600)
        p.add_argument('--refresh',action='store_true');p.add_argument('--report',type=Path)
        p.add_argument('--since',default='1900-01-01');p.add_argument('--until',default='2026-10-06')
    sub.add_parser('index');sub.add_parser('inventory');sub.add_parser('dense-index');sub.add_parser('paper-dense-index')
    p=sub.add_parser('dense-activate');p.add_argument('--level',choices=['paper','passage'],required=True)
    p=sub.add_parser('search');p.add_argument('query');p.add_argument('--method',default='bm25',choices=['bm25','tfidf','structure']);p.add_argument('--expand',action='store_true')
    p=sub.add_parser('serve');p.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    settings=None
    if args.command=='probe':
        store=Store();client=EuropePMC()
    else:
        settings=Settings.load()
        if args.command=='ingest':settings=replace(settings,since=args.since,cutoff=args.until)
        settings.initialize();store=Store(settings.root/'data/normalized/corpus.sqlite');client=EuropePMC(settings)
    if args.command in ('ingest','probe'):
        before=psutil.Process().memory_info().rss
        result=ingest(store,client,args.topics,None if args.pages==0 else args.pages,args.page_size,refresh=args.refresh,seconds=args.seconds)
        if settings:
            size=store.db.execute('PRAGMA page_count').fetchone()[0]*store.db.execute('PRAGMA page_size').fetchone()[0]
            settings.check_space(rebuild=max(size*3,100_000_000))
        result['index']=build(store)
        runs=[]
        for q in ['caffeine sleep timing dose','dietary protein kidney function','sodium blood pressure','late eating weight gain']:
            for method in ('tfidf','bm25','structure'):
                run=search(store,q,method,k=3)
                # Reports preserve IDs/ranks and measurements, not bulk article text on C:.
                runs.append({'query':q,'method':method,'trace':run['trace'],'hits':[{'id':p['id'],'title':p['title'],'score':p['score'],'availability':p['availability'],'passage_ids':[v['id'] for v in p['passages']]} for p in run['results']]})
        result['retrieval_experiments']=runs
        serialized=store.db.serialize() if settings is None else None
        result['measurements']={'sqlite_bytes':store.db.execute('PRAGMA page_count').fetchone()[0]*store.db.execute('PRAGMA page_size').fetchone()[0],
                                'sqlite_gzip_bytes':len(gzip.compress(serialized,mtime=0)) if serialized else None,
                                'rss_before_bytes':before,'rss_after_bytes':psutil.Process().memory_info().rss,
                                'available_ram_bytes':psutil.virtual_memory().available,
                                'pilot_limit_note':'Pages bound this measurement job only; --pages 0 continues until budget/time/source exhaustion.'}
        result['quality_metrics']={'status':'Unavailable: independent relevance judgments not supplied','human_review':False}
        if settings:
            result['storage']=settings.report();target=args.report or settings.root/'experiments'/('ingest-'+str(int(time.time()))+'.json')
        else:
            result['limitation']='Transient RAM-only feasibility probe; E: persistence is blocked. Corpus is not retained.'
            target=args.report
        if target:Settings.atomic_json(target,result)
        print(json.dumps(result,ensure_ascii=True,indent=2))
    elif args.command=='index':print(json.dumps(build(store),indent=2))
    elif args.command=='dense-index':
        from .dense import build_dense
        print(json.dumps(build_dense(store,settings),indent=2))
    elif args.command=='dense-activate':
        from .dense import activate_dense
        print(json.dumps(activate_dense(store,settings,args.level),indent=2))
    elif args.command=='paper-dense-index':
        from .dense import build_paper_dense
        print(json.dumps(build_paper_dense(store,settings),indent=2))
    elif args.command=='inventory':print(json.dumps({'counts':store.counts(),'storage':settings.report(),'corpus':store.fingerprint()},indent=2))
    elif args.command=='search':print(json.dumps(search(store,args.query,args.method,expand=args.expand),ensure_ascii=True,indent=2))
    elif args.command=='serve':
        from .server import serve
        serve(settings,args.port)

if __name__=='__main__':main()
