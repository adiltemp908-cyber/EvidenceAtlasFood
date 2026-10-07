from __future__ import annotations
import gzip
import hashlib
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import requests
from .parsing import abstract_text,clean,make_passages,paragraphs_jats,screen,SCREENING_VERSION
from .taxonomy import TOPICS,queries,VERSION

BASE='https://www.ebi.ac.uk/europepmc/webservices/rest'
def now():return datetime.now(timezone.utc).isoformat()

class EuropePMC:
    def __init__(self,settings=None):
        self.settings=settings;self.last=0;self.bytes=0;self.requests=0
        self.session=requests.Session();self.session.headers['User-Agent']='EvidenceAtlasFood/0.1 (academic nutrition IR pilot)'
    def get(self,path,params=None):
        for attempt in range(4):
            time.sleep(max(0,1-(time.monotonic()-self.last)))
            try:
                url=path if path.startswith('https://eutils.ncbi.nlm.nih.gov/') else BASE+path
                r=self.session.get(url,params=params,timeout=(10,45));self.last=time.monotonic();self.requests+=1
                if r.status_code in (429,500,502,503,504):
                    if attempt==3:r.raise_for_status()
                    try: delay=min(45,float(r.headers.get('Retry-After',2**attempt)))
                    except ValueError:delay=2**attempt
                    time.sleep(delay);continue
                r.raise_for_status();self.bytes+=len(r.content)
                if len(r.content)>25_000_000:raise ValueError('Response exceeds 25 MB per-record safety limit')
                digest=hashlib.sha256(r.content).hexdigest()
                if self.settings:
                    self.settings.check_space(additional=len(r.content)*2)
                    p=self.settings.root/'data/raw'/(digest+'.gz')
                    if not p.exists():
                        tmp=p.with_suffix('.part');tmp.write_bytes(gzip.compress(r.content,mtime=0));tmp.replace(p)
                    entry={'url':r.url,'retrieved_at':now(),'sha256':digest,'bytes':len(r.content),'status':r.status_code}
                    with (self.settings.root/'data/manifests/requests.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(entry)+'\n')
                return r.content,digest
            except requests.RequestException:
                self.last=time.monotonic()
                if attempt==3:raise
                time.sleep(2**attempt)
        raise RuntimeError('Retry loop exhausted')
    def search(self,query,cursor='*',size=25):
        data,digest=self.get('/search',{'query':query,'format':'json','resultType':'core','cursorMark':cursor,'pageSize':size,'synonym':'false'})
        obj=json.loads(data)
        if 'resultList' not in obj:raise ValueError('Provider response lacks resultList')
        return obj,digest

    def pubmed(self,query,cursor='*',size=25):
        offset=0 if cursor=='*' else int(cursor)
        if offset+size>9999:raise ValueError('PubMed search requires date partitioning beyond 9,999 IDs; checkpoint retained')
        raw,digest=self.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            {'db':'pubmed','term':query,'retmode':'json','retstart':offset,'retmax':size,'tool':'EvidenceAtlasFood'})
        obj=json.loads(raw)
        if 'esearchresult' not in obj or obj['esearchresult'].get('ERROR'):raise ValueError('PubMed search error: '+str(obj)[:500])
        info=obj['esearchresult'];ids=info.get('idlist',[])
        if ids:
            core,digest=self.search('SRC:MED AND ('+' OR '.join('EXT_ID:'+i for i in ids)+')',size=len(ids))
        else:core={'resultList':{'result':[]}}
        core['hitCount']=int(info['count']);core['nextCursorMark']=str(offset+len(ids)) if offset+len(ids)<int(info['count']) else None
        core['pubmed_translation']=info.get('querytranslation')
        return core,digest

def ingest(store,client,topics=None,pages=1,page_size=10,fulltext=True,refresh=False,seconds=600):
    started=time.perf_counter();events=[];new_full=0;parse_times=[]
    def summary():
        return {'elapsed_seconds':time.perf_counter()-started,'network_bytes':client.bytes,'requests':client.requests,
                'new_full_texts':new_full,'parse_seconds':parse_times,'pages':events,'counts':store.counts(),
                'corpus':store.fingerprint(),'completed_at':now(),'persistent':client.settings is not None}
    for topic in topics or TOPICS:
        for mode,query in queries(topic,client.settings.cutoff if client.settings else '2026-10-06',client.settings.since if client.settings else '1900-01-01').items():
            qhash=hashlib.sha256((VERSION+query).encode()).hexdigest()
            prior=store.db.execute('SELECT payload FROM jobs WHERE id=?',(qhash,)).fetchone()
            state=json.loads(prior[0]) if prior and not refresh else {'cursor':'*','pages':0,'done':False}
            if state.get('done'):continue
            count=0
            while not state.get('done') and (pages is None or count<pages):
                if time.perf_counter()-started>seconds:return summary()
                response,rawhash=(client.pubmed if mode=='mesh' else client.search)(query,state['cursor'],page_size)
                records=response['resultList']['result']
                for rec in records:
                    pid=store.canonical(rec)
                    decision,reason,species=screen(rec,TOPICS[topic][2])
                    existing=store.paper(pid)
                    has_passages=bool(existing and existing['passages'])
                    if existing and not refresh and (has_passages or decision!='accepted'):
                        with store.db:store.db.execute('INSERT OR REPLACE INTO discoveries VALUES(?,?,?,?,?)',(pid,topic,qhash,decision,reason))
                        continue
                    abstract=abstract_text(rec.get('abstractText'));body=None;details={};availability='abstract-only' if abstract else 'metadata-only'
                    if fulltext and decision=='accepted' and rec.get('isOpenAccess')=='Y' and rec.get('pmcid'):
                        try:
                            xml,xhash=client.get('/'+rec['pmcid']+'/fullTextXML')
                            tick=time.perf_counter();body,details=paragraphs_jats(xml);parse_times.append(time.perf_counter()-tick)
                            details['raw_sha256']=xhash;availability='full-text';new_full+=1
                            with store.db:store.db.execute('DELETE FROM failures WHERE id=?',(pid+':fulltext',))
                        except (requests.RequestException,ValueError,ET.ParseError) as exc:
                            # A failed fetch never promotes an abstract to full text.
                            with store.db:store.db.execute('INSERT OR REPLACE INTO failures VALUES(?,?,?,?,?)',(pid+':fulltext',pid,'fulltext',str(exc)[:500],now()))
                    paper={'id':pid,'pmid':rec.get('pmid'),'pmcid':rec.get('pmcid'),'doi':(rec.get('doi') or '').lower() or None,
                           'title':abstract_text(rec.get('title')),'abstract':abstract,'year':int(rec['pubYear']) if rec.get('pubYear','').isdigit() else None,
                           'species':species,'availability':availability,'updated':now(),
                           'metadata':{'source_record':rec,'source_sha256':rawhash,'fulltext':details,'screening_version':SCREENING_VERSION,
                                       'status_check':{'source':'Europe PMC core pubType/commentCorrection fields','checked_at':now(),
                                                       'publication_types':rec.get('pubTypeList',{}),'corrections':rec.get('commentCorrectionList',{}),
                                                       'certainty':'Status coverage is incomplete; absence is not verification'},'overlap':'Not adjudicated'}}
                    passages=make_passages(pid,paper['title'],abstract,body) if decision=='accepted' else []
                    # Preserve a previously obtained body during metadata-only refresh/fetch failures.
                    if existing and existing['availability']=='full-text' and availability!='full-text':
                        paper['availability']='full-text';paper['metadata']['fulltext']=existing['metadata']['fulltext'];passages=existing['passages']
                    store.save(paper,passages,topic,qhash,decision,reason)
                nxt=response.get('nextCursorMark')
                state={'cursor':nxt or state['cursor'],'pages':state['pages']+1,'done':not records or not nxt or nxt==state['cursor'],
                       'hit_count':response.get('hitCount'),'query':query,'updated':now(),'taxonomy':VERSION}
                with store.db:store.db.execute('INSERT OR REPLACE INTO jobs VALUES(?,?)',(qhash,json.dumps(state)))
                count+=1;events.append({'topic':topic,'mode':mode,'returned':len(records),'hits':response.get('hitCount')})
                print(json.dumps({'event':'ingestion_page',**events[-1],'counts':store.counts()}),flush=True)
    return summary()

