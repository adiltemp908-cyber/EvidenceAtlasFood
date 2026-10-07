from __future__ import annotations
import json
import mimetypes
import re
import uuid
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse,parse_qs,unquote
from .store import Store
from .retrieval import search
from .evidence import inspect_evidence,extract
from .acquisition import now

WEB=Path(__file__).resolve().parent.parent/'web'

def serve(settings,port=8765):
    engine=None
    def get_engine():
        nonlocal engine
        if engine is None:
            from .advanced import ResearchEngine
            engine=ResearchEngine(settings)
        return engine
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args):pass  # Private claims and notes do not go into access logs.
        def send(self,value,status=200,kind='application/json; charset=utf-8',filename=None):
            raw=json.dumps(value,ensure_ascii=False).encode() if kind.startswith('application/json') else value.encode() if isinstance(value,str) else value
            self.send_response(status);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(raw)))
            self.send_header('X-Content-Type-Options','nosniff');self.send_header('Cache-Control','no-store')
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'")
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            self.end_headers();self.wfile.write(raw)
        def valid_host(self):return self.headers.get('Host') in (f'127.0.0.1:{port}',f'localhost:{port}')
        def do_GET(self):
            if not self.valid_host():return self.send({'error':'Localhost access only'},403)
            parsed=urlparse(self.path);q=parse_qs(parsed.query);path=unquote(parsed.path)
            store=Store(settings.root/'data/normalized/corpus.sqlite')
            try:
                if path=='/api/health':return self.send({'status':'ok','version':'0.1.0'})
                if path=='/api/coverage':
                    from .models import index_metadata
                    idx=store.db.execute("SELECT value FROM config WHERE key='index'").fetchone()
                    return self.send({'counts':store.counts(),'storage':settings.report(),'index':json.loads(idx[0]) if idx else None,
                        'capabilities':{'dense':(settings.root/'indexes/dense-active.json').exists(),'reranker':(settings.root/'models/reranker/config.json').exists(),'experimental_nli':(settings.root/'models/nli/config.json').exists()},'dense_index':index_metadata(settings),
                        'jobs':[json.loads(r[0]) for r in store.db.execute('SELECT payload FROM jobs')],
                        'limitations':['Provisional metadata screening; not independently validated','Pilot/development collection, not comprehensive nutrition coverage','Model stance and claim synthesis are not yet validated']})
                if path=='/api/search':
                    query=q.get('q',[''])[0];method=q.get('method',['structure'])[0]
                    filters={key:q[key][0] for key in ('topic','section','year_min','year_max') if q.get(key) and q[key][0]}
                    filters.update({key:q.get(key,['false'])[0]=='true' for key in ('fulltext','human')})
                    count=min(30,max(1,int(q.get('k',['10'])[0])));expanded=q.get('expand',['true'])[0]=='true'
                    if method in ('hybrid','dense') or q.get('rerank',['false'])[0]=='true':
                        if any(c in query for c in ('"','(',')')) or re.search(r'\b(AND|OR|NOT)\b',query):raise ValueError('Use lexical retrieval for Boolean/phrase constraints; dense syntax is natural language only')
                        run=get_engine().run(store,query,method,k=count,filters=filters,expand=expanded,rerank=q.get('rerank',['false'])[0]=='true')
                    else:run=search(store,query,method,k=count,filters=filters,expand=expanded)
                    from .intent import interpret
                    run['intent']=interpret(query);run['evidence']=inspect_evidence(store,query,run);return self.send(run)
                if path.startswith('/api/papers/'):
                    paper=store.paper(path.removeprefix('/api/papers/'))
                    if paper:paper['fields']=extract(paper)
                    return self.send(paper or {'error':'Paper not found'},200 if paper else 404)
                if path=='/api/sessions':
                    return self.send([{'id':r['id'],'created':r['created'],'query':json.loads(r['payload']).get('query','')} for r in store.db.execute('SELECT * FROM sessions ORDER BY created DESC')])
                if path.startswith('/api/sessions/'):
                    sid=path.removeprefix('/api/sessions/').split('/')[0];row=store.db.execute('SELECT payload FROM sessions WHERE id=?',(sid,)).fetchone()
                    if not row:return self.send({'error':'Session not found'},404)
                    value=json.loads(row[0])
                    if path.endswith('/export'):return self.send(value,filename='evidenceatlas-session.json')
                    return self.send(value)
                if path=='/api/bibliography':
                    ids=q.get('ids',[''])[0].split(',')[:30];lines=[]
                    for pid in ids:
                        p=store.paper(pid)
                        if not p:continue
                        def safe(v):return re.sub(r'[\r\n]+',' ',str(v or ''))
                        lines+=['TY  - JOUR','TI  - '+safe(p['title']),'PY  - '+safe(p['year'])]
                        for a in p['metadata']['source_record'].get('authorList',{}).get('author',[]):lines.append('AU  - '+safe(a.get('fullName')))
                        if p.get('doi'):lines.append('DO  - '+safe(p['doi']))
                        if p.get('pmid'):lines.append('UR  - https://pubmed.ncbi.nlm.nih.gov/'+safe(p['pmid'])+'/')
                        lines+=['ER  - ','']
                    return self.send('\n'.join(lines),kind='application/x-research-info-systems; charset=utf-8',filename='evidenceatlas.ris')
                if path=='/api/evaluation':
                    audit_path=WEB.parent/'evaluation/delivery/ai-audit-summary.json'
                    audit=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.exists() else None
                    if audit:
                        from .models import index_metadata
                        active=index_metadata(settings)
                        audit['matches_current_corpus']=audit['corpus']==store.fingerprint()
                        audit['retrieval_variant']='paper-level title/abstract embeddings'
                        audit['matches_current_dense_index']=bool(active and active.get('level')=='paper' and audit['matches_current_corpus'])
                    summaries=[]
                    for summary in sorted((settings.root/'experiments').glob('*/summary.json')):
                        value=json.loads(summary.read_text(encoding='utf-8'));value['name']=summary.parent.name;summaries.append(value)
                    reviewed=[]
                    for metrics in sorted((settings.root/'experiments').glob('*/metrics-human.json')):
                        value=json.loads(metrics.read_text(encoding='utf-8'));value['name']=metrics.parent.name;reviewed.append(value)
                    return self.send({'protocol':'evaluation/PROTOCOL.md','human_judgments':sum(v['judged_pairs'] for v in reviewed),'metrics_status':'Reviewed snapshot reports available; inspect coverage and qualifications' if reviewed else 'Not available without reviewed qrels','experiments':summaries,'reviewed_reports':reviewed,'ai_audit':audit})
                assets={'/':'index.html','/app.js':'app.js','/styles.css':'styles.css','/favicon.svg':'favicon.svg'}
                if path in assets:
                    f=WEB/assets[path];return self.send(f.read_bytes(),kind=mimetypes.guess_type(f.name)[0] or 'text/plain')
                self.send({'error':'Not found'},404)
            except (ValueError,KeyError) as e:self.send({'error':str(e)},400)
            except Exception:self.send({'error':'Request could not be completed. Check index availability and retry.'},500)
            finally:store.db.close()
        def do_POST(self):
            if not self.valid_host():return self.send({'error':'Localhost access only'},403)
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{port}',f'http://localhost:{port}'):return self.send({'error':'Cross-origin write denied'},403)
            if self.headers.get('Content-Type','').split(';')[0]!='application/json':return self.send({'error':'JSON required'},415)
            try:
                length=int(self.headers.get('Content-Length',0))
                if length<1 or length>2_000_000:return self.send({'error':'Invalid request size'},413)
                value=json.loads(self.rfile.read(length))
                if self.path=='/api/analyze':
                    claim=value.get('claim','')
                    if not isinstance(claim,str) or not 3<=len(claim)<=1000:raise ValueError('Claim must contain 3–1000 characters')
                    if claim.rstrip().endswith('?') or re.match(r'^(does|do|is|are|can|what|how)\b',claim,re.I):
                        return self.send({'error':'Enter a declarative claim for passage stance analysis. The original question remains in your investigation.'},400)
                    store=Store(settings.root/'data/normalized/corpus.sqlite')
                    try:
                        from .advanced import counter_search
                        filters=value.get('filters') or {};baseline=search(store,claim,'structure',k=8,filters=filters,expand=True)
                        counter=counter_search(store,claim,baseline,filters,k=4)
                        papers=baseline['results']+counter['additional'];passages=[]
                        for paper in papers:
                            eligible=[p for p in store.paper(paper['id'])['passages'] if p['zone'] in ('results','conclusion','abstract','discussion','limitations')]
                            claim_terms=set(re.findall(r'\w+',claim.lower()))-{'the','a','in','and','of','to'}
                            eligible.sort(key=lambda p:sum(t in set(re.findall(r'\w+',p['text'].lower())) for t in claim_terms)+(2 if p['zone'] in ('results','conclusion') else 0),reverse=True)
                            for p in eligible[:2]:passages.append(p)
                        predictions=get_engine().experimental_stance(claim,passages[:24]) if passages else []
                        result={'claim':claim,'created':now(),'corpus':baseline['trace']['index']['corpus'],'predictions':predictions,
                            'sources':[{'paper_id':p['paper_id'],'passage_id':p['id'],'section':p['section'],'text':p['text']} for p in passages[:24]],
                            'counterevidence':counter,'assessment':'Experimental passage labels only. Study applicability and overall scientific certainty remain unassessed.',
                            'limitations':['NLI trained outside this food benchmark','No independent domain validation','Passages may discuss other studies','Model inputs may be truncated','No claim-level true/false verdict is inferred']}
                        return self.send(result)
                    finally:store.db.close()
                if self.path!='/api/sessions':return self.send({'error':'Not found'},404)
                if not isinstance(value,dict) or not isinstance(value.get('query'),str):raise ValueError('A query is required')
                settings.check_space(additional=length*2)
                store=Store(settings.root/'data/normalized/corpus.sqlite');sid=str(uuid.uuid4());value['saved_at']=now()
                with store.db:store.db.execute('INSERT INTO sessions VALUES(?,?,?)',(sid,now(),json.dumps(value)))
                store.db.close();self.send({'id':sid},201)
            except (ValueError,TypeError):self.send({'error':'Invalid request JSON or input'},400)
            except Exception:self.send({'error':'Analysis or persistence unavailable. Check local model/index availability and available memory.'},503)
    print(f'EvidenceAtlas Food http://127.0.0.1:{port}',flush=True)
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()
