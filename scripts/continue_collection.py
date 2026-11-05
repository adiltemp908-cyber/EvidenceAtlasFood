"""Bounded, resumable acquisition on a staging corpus; never changes the live index."""
import argparse,copy,hashlib,json,sqlite3,sys,time,traceback
from dataclasses import replace
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.acquisition import EuropePMC,ingest,now
from evidenceatlas.parsing import paragraphs_jats,make_passages
from evidenceatlas.taxonomy import TOPICS

def backup(source,destination):
    a=sqlite3.connect(str(source));b=sqlite3.connect(str(destination))
    try:a.backup(b)
    finally:b.close();a.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--seconds',type=int,default=900)
    parser.add_argument('--run',default='expansion-2026-10-13')
    parser.add_argument('--topics',nargs='+',choices=sorted(TOPICS))
    parser.add_argument('--cutoff',default='2026-10-13',type=date.fromisoformat)
    parser.add_argument('--page-size',type=int,default=15)
    args=parser.parse_args()
    if args.seconds<=0 or not 1<=args.page_size<=100:parser.error('Use positive seconds and page size 1–100')
    settings=Settings.load();settings.initialize();folder=settings.root/'experiments'/args.run
    folder.mkdir(parents=True,exist_ok=True)
    baseline=folder/'baseline.sqlite';staged=folder/'corpus.sqlite';status=folder/'status.json'
    prior=json.loads(status.read_text()) if status.exists() else {}
    if prior.get('status') not in (None,'acquiring','acquired-awaiting-indexes'):
        raise ValueError('This run has entered indexing/publication; choose a new --run name')
    if not baseline.exists():
        settings.check_space(additional=(settings.root/'data/normalized/corpus.sqlite').stat().st_size*3)
        backup(settings.root/'data/normalized/corpus.sqlite',baseline)
    if not staged.exists():backup(baseline,staged)
    store=Store(staged);client=EuropePMC(settings);started=time.monotonic()
    state={**prior,'status':'acquiring','run':args.run,'started_at':now(),'before':prior.get('before',store.counts()),'before_corpus':prior.get('before_corpus',store.fingerprint())}
    Settings.atomic_json(status,state)
    backfill=state.setdefault('fulltext_backfill',[]);attempted={x['id'] for x in backfill}
    rows=store.db.execute("SELECT p.id FROM papers p WHERE p.availability != 'full-text' AND p.pmcid IS NOT NULL AND json_extract(p.metadata,'$.source_record.isOpenAccess')='Y' AND EXISTS(SELECT 1 FROM discoveries d WHERE d.paper_id=p.id AND d.decision='accepted') ORDER BY p.id").fetchall()
    for row in rows:
        if row[0] in attempted:continue
        paper=store.paper(row[0]);event={'id':paper['id'],'pmcid':paper['pmcid']}
        try:
            xml,digest=client.get('/'+paper['pmcid']+'/fullTextXML');body,details=paragraphs_jats(xml)
            details['raw_sha256']=digest;details['retrieved_at']=now()
            paper['availability']='full-text';paper['metadata']['fulltext']=details;paper['updated']=now()
            d=store.db.execute("SELECT topic,query_hash,decision,reason FROM discoveries WHERE paper_id=? AND decision='accepted' LIMIT 1",(paper['id'],)).fetchone()
            store.save(paper,make_passages(paper['id'],paper['title'],paper['abstract'],body),*d)
            with store.db:store.db.execute('DELETE FROM failures WHERE id=?',(paper['id']+':fulltext',))
            event.update(status='recovered',paragraphs=len(body))
        except Exception as exc:
            event.update(status='failed',error=str(exc)[:400])
            with store.db:store.db.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?,?,?)',(paper['id']+':fulltext',paper['id'],'fulltext',str(exc)[:500],now()))
        backfill.append(event);Settings.atomic_json(status,state);print(json.dumps(event),flush=True)
    topics=args.topics or ['egg_cholesterol','protein_muscle','breakfast_cereal','yogurt_digestion','fruit_juice','red_meat_cancer','wholegrain_metabolic','dairy_bone','meal_timing']
    periods=[('2020-01-01',args.cutoff.isoformat()),('2010-01-01','2019-12-31'),('2000-01-01','2009-12-31')]
    plan={'topics':topics,'periods':periods,'page_size':args.page_size}
    if prior.get('plan') and json.loads(json.dumps(plan))!=prior['plan']:raise ValueError('Resume with the same topics, date ranges and page size')
    state['plan']=plan;Settings.atomic_json(status,state)
    # Cycle small pages across topics and date ranges. A time/storage budget, not a paper cap, stops this run.
    tasks=[(topic,*period) for period in periods for topic in topics]
    at=state.get('next_task',0);errors=state.setdefault('errors',[])
    while time.monotonic()-started<args.seconds:
        topic,since,until=tasks[at%len(tasks)];client.settings=replace(settings,since=since,cutoff=until)
        try:
            result=ingest(store,client,[topic],pages=1,page_size=args.page_size,seconds=max(1,args.seconds-(time.monotonic()-started)))
            state.setdefault('batches',[]).append({'topic':topic,'since':since,'until':until,'new_full_texts':result['new_full_texts'],'pages':result['pages'],'completed_at':now()})
        except Exception as exc:
            errors.append({'topic':topic,'since':since,'until':until,'error':str(exc)[:500]});print(json.dumps(errors[-1]),flush=True)
        at+=1;state.update(next_task=at,counts=store.counts(),elapsed_seconds=time.monotonic()-started)
        Settings.atomic_json(status,state)
        if len(errors)>=4 and all(not b['pages'] for b in state.get('batches',[])[-4:]):break
    state.update(status='acquired-awaiting-indexes',counts=store.counts(),corpus=store.fingerprint(),elapsed_seconds=time.monotonic()-started,requests=client.requests,network_bytes=client.bytes,finished_at=now())
    Settings.atomic_json(status,state);store.db.close();print(json.dumps({k:v for k,v in state.items() if k not in ('batches','errors')}),flush=True)

if __name__=='__main__':main()
