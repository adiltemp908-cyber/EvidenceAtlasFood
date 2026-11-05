"""Acquire the specific papers missing from the October 21 diagnostic, in staging."""
import hashlib,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.acquisition import EuropePMC,now
from evidenceatlas.parsing import abstract_text,make_passages,paragraphs_jats,screen,SCREENING_VERSION

def backup(source,target):
    a=sqlite3.connect(str(source));b=sqlite3.connect(str(target))
    try:a.backup(b)
    finally:a.close();b.close()

def main():
    settings=Settings.load();settings.initialize()
    folder=settings.root/'experiments/audit-gaps-2026-10-21';folder.mkdir(exist_ok=True)
    status=folder/'status.json'
    if status.exists():raise RuntimeError('Staging already exists; inspect it before repeating acquisition.')
    live=settings.root/'data/normalized/corpus.sqlite'
    settings.check_space(additional=2*live.stat().st_size+1_000_000_000)
    backup(live,folder/'baseline.sqlite');backup(live,folder/'corpus.sqlite')
    store=Store(folder/'corpus.sqlite')
    state={'status':'acquiring','before_corpus':store.fingerprint(),'before_counts':store.counts(),'started':now(),'records':[]}
    Settings.atomic_json(status,state)
    ids=['36198293','37432300','39074168','27749919']
    query='SRC:MED AND ('+' OR '.join('EXT_ID:'+id for id in ids)+')'
    client=EuropePMC(settings);response,rawhash=client.search(query,size=len(ids))
    records=response['resultList']['result']
    if {r.get('pmid') for r in records} != set(ids):raise RuntimeError('Provider did not return all requested IDs')
    qhash=hashlib.sha256(query.encode()).hexdigest()
    for rec in records:
        decision,reason,species=screen(rec,['creatine','cereal','eating','meal'])
        if decision!='accepted':raise RuntimeError(f'Requires domain review: {rec.get("pmid")} {reason}')
        pid=store.canonical(rec);abstract=abstract_text(rec.get('abstractText'));body=None;details={}
        availability='abstract-only' if abstract else 'metadata-only'
        if rec.get('pmcid') and rec.get('isOpenAccess')=='Y':
            try:
                xml,xhash=client.get('/'+rec['pmcid']+'/fullTextXML');body,details=paragraphs_jats(xml)
                details['raw_sha256']=xhash;availability='full-text'
            except Exception as exc:
                with store.db:store.db.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?,?,?)',(pid+':fulltext',pid,'fulltext',str(exc)[:500],now()))
        paper={'id':pid,'pmid':rec.get('pmid'),'pmcid':rec.get('pmcid'),'doi':rec.get('doi'),
               'title':abstract_text(rec.get('title')),'abstract':abstract,'year':int(rec['pubYear']),
               'species':species,'availability':availability,'updated':now(),
               'metadata':{'source_record':rec,'source_sha256':rawhash,'fulltext':details,'screening_version':SCREENING_VERSION,
                           'acquisition_reason':'Missing-paper probes from the fixed three-question diagnostic; targeted coverage repair, not an unbiased acquisition sample.'}}
        passages=make_passages(pid,paper['title'],abstract,body)
        store.save(paper,passages,'audit-gap-repair',qhash,decision,reason)
        state['records'].append({'id':pid,'title':paper['title'],'availability':availability,'passages':len(passages),'screening_reason':reason})
        Settings.atomic_json(status,state)
        print(json.dumps(state['records'][-1]),flush=True)
    state.update(status='acquired-awaiting-indexes',network_bytes=client.bytes,counts=store.counts(),corpus=store.fingerprint())
    Settings.atomic_json(status,state);store.db.close()

if __name__=='__main__':main()
