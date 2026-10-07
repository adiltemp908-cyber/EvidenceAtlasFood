from __future__ import annotations
import heapq
import json
import time
import numpy as np
from .config import Settings
from .models import embedding_model,MODELS
from .retrieval import tokens

def validate_vectors(vectors,total):
    if vectors.shape!=(total,384):raise ValueError('Embedding array shape does not match corpus')
    for start in range(0,total,4096):
        chunk=vectors[start:start+4096]
        if not np.isfinite(chunk).all():raise ValueError('Non-finite embedding values')
        if not np.allclose(np.linalg.norm(chunk,axis=1),1,atol=1e-4):raise ValueError('Missing or unnormalized embeddings')
    return {'vectors':total,'dimensions':384,'finite':True,'unit_norm_tolerance':1e-4}

def activate_dense(store,settings,level):
    if level not in ('paper','passage'):raise ValueError('Index level must be paper or passage')
    corpus=store.fingerprint();name=('dense-paper-' if level=='paper' else 'dense-')+corpus[:16]
    directory=settings.root/'indexes'/name;meta=json.loads((directory/'manifest.json').read_text())
    if meta['corpus']!=corpus or meta['model']!=list(MODELS['embedding']):raise ValueError('Index corpus/model mismatch')
    vectors=np.load(directory/'vectors.npy',mmap_mode='r');validation=validate_vectors(vectors,len(meta['ids']));del vectors
    Settings.atomic_json(settings.root/'indexes/dense-active.json',{'path':str(directory),'corpus':corpus})
    return {'level':level,'path':str(directory),'validation':validation}

def build_paper_dense(store,settings):
    """Reduced-scope semantic index: every searchable paper's title and abstract."""
    start=time.perf_counter();corpus=store.fingerprint()
    directory=settings.root/'indexes'/('dense-paper-'+corpus[:16]);directory.mkdir(exist_ok=True)
    rows=store.db.execute('SELECT id,title,abstract FROM papers WHERE id IN (SELECT DISTINCT paper_id FROM passages) ORDER BY id').fetchall()
    settings.check_space(additional=len(rows)*384*8)
    model=embedding_model(settings);vectors=np.lib.format.open_memmap(directory/'vectors.part.npy',mode='w+',dtype='float32',shape=(len(rows),384))
    truncated=0
    for offset in range(0,len(rows),32):
        batch=rows[offset:offset+32];texts=[r['title']+' '+(r['abstract'] or '') for r in batch]
        truncated+=sum(len(model.tokenizer.encode(t,truncation=False))>model.max_seq_length for t in texts)
        vectors[offset:offset+len(batch)]=model.encode(texts,batch_size=16,normalize_embeddings=True,show_progress_bar=False)
    vectors.flush();del vectors
    (directory/'vectors.part.npy').replace(directory/'vectors.npy')
    meta={'corpus':corpus,'model':MODELS['embedding'],'level':'paper','input':'title plus abstract; full text remains in lexical indexes',
          'dimensions':384,'papers':len(rows),'truncated_inputs':truncated,'truncated_passages':0,'max_tokens':model.max_seq_length,
          'elapsed_seconds':time.perf_counter()-start,'ids':[{'id':'paper:'+r['id'],'paper_id':r['id'],'zone':'title_abstract'} for r in rows],'path':str(directory)}
    Settings.atomic_json(directory/'manifest.json',meta);Settings.atomic_json(settings.root/'indexes/dense-active.json',{'path':str(directory),'corpus':corpus})
    return {k:v for k,v in meta.items() if k!='ids'}

def build_dense(store,settings):
    start=time.perf_counter();model=embedding_model(settings)
    corpus=store.fingerprint();directory=settings.root/'indexes'/('dense-'+corpus[:16]);directory.mkdir(exist_ok=True)
    total=store.db.execute('SELECT count(*) FROM passages').fetchone()[0]
    settings.check_space(additional=total*384*4,rebuild=total*384*4)
    progress_path=directory/'progress.json';part=directory/'vectors.part.npy'
    progress=json.loads(progress_path.read_text()) if progress_path.exists() else {}
    resume=bool(part.exists() and progress.get('corpus')==corpus and progress.get('model')==list(MODELS['embedding']))
    if part.exists() and not resume:raise ValueError('Existing checkpoint is incompatible; preserve it and use a new index directory')
    offset=int(progress.get('encoded',0)) if resume else 0
    if not 0<=offset<=total:raise ValueError('Invalid checkpoint offset')
    resumed_from=offset
    vectors=np.lib.format.open_memmap(part,mode='r+' if resume else 'w+',dtype='float32',shape=(total,384))
    if vectors.shape!=(total,384):raise ValueError('Checkpoint array shape differs from corpus')
    ids=[{'id':r['id'],'paper_id':r['paper_id'],'zone':r['zone']} for r in store.db.execute('SELECT id,paper_id,zone FROM passages ORDER BY id')]
    truncated=int(progress.get('truncated',0)) if resume else 0
    cursor=store.db.execute('SELECT id,paper_id,zone,text FROM passages ORDER BY id LIMIT -1 OFFSET ?',(offset,))
    while batch:=cursor.fetchmany(32):
        texts=[r['text'] for r in batch]
        # Keep truncation visible. Lexical retrieval still indexes complete source paragraphs.
        truncated+=sum(len(model.tokenizer.encode(t,add_special_tokens=True,truncation=False))>model.max_seq_length for t in texts)
        embeddings=model.encode(texts,batch_size=32,normalize_embeddings=True,show_progress_bar=False)
        vectors[offset:offset+len(batch)]=embeddings
        offset+=len(batch)
        if offset%512==0 or offset==total:
            vectors.flush();Settings.atomic_json(progress_path,{'corpus':corpus,'model':MODELS['embedding'],'encoded':offset,'truncated':truncated,'resumed_from':resumed_from,'elapsed_this_run_seconds':time.perf_counter()-start})
            elapsed=time.perf_counter()-start
            print(json.dumps({'encoded_passages':offset,'total':total,'elapsed_seconds':elapsed,'estimated_remaining_seconds':elapsed*(total-offset)/max(offset-resumed_from,1)}),flush=True)
    vectors.flush();validation=validate_vectors(vectors,total)
    if store.fingerprint()!=corpus:raise ValueError('Corpus changed during encoding; do not activate this index')
    del vectors
    (directory/'vectors.part.npy').replace(directory/'vectors.npy')
    meta={'corpus':corpus,'model':MODELS['embedding'],'level':'passage','input':'each normalized section passage; first 256 model tokens; full paragraph retained in lexical index','dimensions':384,'passages':total,'truncated_passages':truncated,'max_tokens':model.max_seq_length,'elapsed_seconds':time.perf_counter()-start,'elapsed_scope':'current invocation only; excludes earlier checkpoint work','resumed_from':resumed_from,'validation':validation,'ids':ids,'path':str(directory)}
    Settings.atomic_json(directory/'manifest.json',meta)
    Settings.atomic_json(settings.root/'indexes/dense-active.json',{'path':str(directory),'corpus':corpus})
    return {k:v for k,v in meta.items() if k!='ids'}

class DenseIndex:
    def __init__(self,settings):
        self.settings=settings;active=json.loads((settings.root/'indexes/dense-active.json').read_text());self.directory=settings.root/'indexes'/__import__('pathlib').Path(active['path']).name
        self.meta=json.loads((self.directory/'manifest.json').read_text());self.vectors=np.load(self.directory/'vectors.npy',mmap_mode='r')
        if self.meta['model']!=list(MODELS['embedding']):raise ValueError('Embedding model revision differs from index')
        validate_vectors(self.vectors,len(self.meta['ids']));self.model=embedding_model(settings)
    def search(self,store,query,k=10,filters=None):
        start=time.perf_counter();filters=filters or {}
        idx=json.loads(store.db.execute("SELECT value FROM config WHERE key='index'").fetchone()[0])
        if idx['corpus']!=self.meta['corpus']:raise ValueError('Dense/lexical corpus versions differ; rebuild dense index')
        q=self.model.encode([query],normalize_embeddings=True,show_progress_bar=False)[0];best={}
        for begin in range(0,len(self.vectors),4096):
            scores=self.vectors[begin:begin+4096]@q
            for i,score in enumerate(scores):
                meta=self.meta['ids'][begin+i];pid=meta['paper_id']
                if self.meta.get('level')!='paper' and filters.get('section') and meta['zone']!=filters['section']:continue
                if pid not in best or score>best[pid][0]:best[pid]=(float(score),meta['id'])
        results=[]
        for pid,(score,passage_id) in heapq.nlargest(len(best),best.items(),key=lambda item:item[1][0]):
            p=store.paper(pid)
            if filters.get('fulltext') and p['availability']!='full-text':continue
            if filters.get('human') and p['species']!='human (MeSH)':continue
            if filters.get('year_min') and (not p['year'] or p['year']<int(filters['year_min'])):continue
            if filters.get('year_max') and (not p['year'] or p['year']>int(filters['year_max'])):continue
            if filters.get('topic') and not store.db.execute('SELECT 1 FROM discoveries WHERE paper_id=? AND topic=? AND decision=?',(pid,filters['topic'],'accepted')).fetchone():continue
            if self.meta.get('level')=='paper':
                qt=set(tokens(query));parts=[x for x in p['passages'] if x['zone']!='title' and (not filters.get('section') or x['zone']==filters['section'])]
                if not parts:continue
                parts.sort(key=lambda x:len(qt&set(tokens(x['text']))),reverse=True);p['passages']=parts[:3]
            else:p['passages']=[x for x in p['passages'] if x['id']==passage_id]
            p.pop('metadata');p['score']=score;p['score_components']=[{'dense_cosine':score}];p['rank']=len(results)+1;results.append(p)
            if len(results)>=k:break
        return {'query':query,'results':results,'trace':{'method':'dense','index':idx,'model':self.meta['model'],'filters':filters,'candidate_papers':len(best),'latency_ms':(time.perf_counter()-start)*1000,'score_meaning':'embedding similarity, not entailment','level':self.meta.get('level','passage'),'input':self.meta.get('input','passage text'),'passage_selection':'term overlap after paper-vector retrieval' if self.meta.get('level')=='paper' else 'dense passage similarity','truncated_inputs':self.meta.get('truncated_inputs',self.meta.get('truncated_passages',0))}}

def fuse(runs,k=10):
    scores={};papers={};components={}
    for run in runs:
        for rank,p in enumerate(run['results'],1):
            pid=p['id'];scores[pid]=scores.get(pid,0)+1/(60+rank);papers.setdefault(pid,p)
            components.setdefault(pid,[]).append({'method':run['trace']['method'],'rank':rank,'score':p['score'],'rrf_contribution':1/(60+rank)})
    result=[]
    for pid in sorted(scores,key=lambda p:(-scores[p],p))[:k]:
        result.append({**papers[pid],'score':scores[pid],'score_components':components[pid],'rank':len(result)+1})
    return {'query':runs[0]['query'],'results':result,'trace':{'method':'hybrid','rrf_k':60,'index':runs[0]['trace']['index'],'runs':[r['trace'] for r in runs],'latency_ms':sum(r['trace']['latency_ms'] for r in runs),'score_meaning':'reciprocal rank fusion, not truth probability'}}
