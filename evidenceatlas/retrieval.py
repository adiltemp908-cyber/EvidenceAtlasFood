from __future__ import annotations
import collections
import hashlib
import heapq
import json
import math
import re
import time

INDEX_VERSION='positional-lexical-1'
STOP=set('a an the is are was were does do did of to in on for and or with as at by from this that it be have has can how what whether'.split())
WEIGHTS={'title':1.4,'abstract':1.0,'methods':0.85,'results':1.25,'discussion':1.0,'conclusion':1.1,'limitations':1.05,'background':0.6,'table':1.0,'body':1.0}
EXPANSIONS={'fibre':'fiber','high blood pressure':'hypertension','late night eating':'late eating meal timing','artificial sweeteners':'non nutritive sweeteners','seed oils':'vegetable oils','kidneys':'kidney renal'}

def tokens(text):return re.findall(r"[^\W_]+(?:[.'’][^\W_]+)*",text.casefold(),re.UNICODE)

def normalize(query,enabled=True):
    changes=[];expanded=query
    if enabled:
        for key,value in EXPANSIONS.items():
            if re.search(r'\b'+re.escape(key)+r'\b',query,re.I):
                expanded+=' '+value;changes.append({'expression':key,'added':value,'kind':'related terms; not equivalent exposure'})
    return expanded,changes

def build(store):
    start=time.perf_counter();db=store.db
    db.executescript('''
    BEGIN IMMEDIATE;
    DROP TABLE IF EXISTS postings; DROP TABLE IF EXISTS vocabulary; DROP TABLE IF EXISTS index_docs;
    CREATE TABLE index_docs(id TEXT PRIMARY KEY,paper_id TEXT,level TEXT,zone TEXT,length INTEGER,norm REAL DEFAULT 0);
    CREATE TABLE postings(term TEXT,doc TEXT,tf INTEGER,positions TEXT,PRIMARY KEY(term,doc));
    CREATE TABLE vocabulary(term TEXT,level TEXT,df INTEGER,idf REAL,PRIMARY KEY(term,level));
    CREATE INDEX posting_doc ON postings(doc);
    CREATE INDEX index_level ON index_docs(level);
    ''')
    def add(did,pid,level,zone,text):
        terms=tokens(text);positions=collections.defaultdict(list)
        for i,t in enumerate(terms):positions[t].append(i)
        db.execute('INSERT INTO index_docs(id,paper_id,level,zone,length) VALUES(?,?,?,?,?)',(did,pid,level,zone,len(terms)))
        db.executemany('INSERT INTO postings VALUES(?,?,?,?)',[(t,did,len(pos),json.dumps(pos)) for t,pos in positions.items()])
    with db:
        for row in db.execute('SELECT DISTINCT paper_id FROM passages').fetchall():
            pid=row[0];parts=db.execute('SELECT id,zone,text FROM passages WHERE paper_id=? ORDER BY ordinal',(pid,)).fetchall()
            add('flat:'+pid,pid,'paper','flat','\n'.join(r['text'] for r in parts))
            for p in parts:add(p['id'],pid,'passage',p['zone'],p['text'])
        for level in ('paper','passage'):
            n=db.execute('SELECT count(*) FROM index_docs WHERE level=?',(level,)).fetchone()[0]
            for row in db.execute('SELECT term,count(*) df FROM postings JOIN index_docs ON doc=id WHERE level=? GROUP BY term',(level,)).fetchall():
                df=row['df'];idf=math.log((1+n)/(1+df))+1
                db.execute('INSERT INTO vocabulary VALUES(?,?,?,?)',(row['term'],level,df,idf))
            for row in db.execute('SELECT id FROM index_docs WHERE level=?',(level,)).fetchall():
                norm=math.sqrt(sum(((1+math.log(r['tf']))*r['idf'])**2 for r in db.execute('SELECT tf,idf FROM postings JOIN vocabulary USING(term) WHERE doc=? AND level=?',(row[0],level))))
                db.execute('UPDATE index_docs SET norm=? WHERE id=?',(norm,row[0]))
        metadata={'version':INDEX_VERSION,'corpus':store.fingerprint(),'built_seconds':time.perf_counter()-start,'weights':WEIGHTS,'weights_status':'hypothesis; not tuned or validated'}
        db.execute('INSERT OR REPLACE INTO config VALUES(?,?)',('index',json.dumps(metadata)))
    return metadata

class BooleanParser:
    """Explicit syntax: AND/OR/NOT, parentheses, quoted positional phrases. AND > OR."""
    def __init__(self,query):
        self.parts=re.findall(r'"[^"\n]+"|\(|\)|\bAND\b|\bOR\b|\bNOT\b|[^\s()"]+',query)
        if query.count('"')%2:raise ValueError('Unclosed quoted phrase')
        self.i=0
    def peek(self):return self.parts[self.i] if self.i<len(self.parts) else None
    def pop(self):v=self.peek();self.i+=1;return v
    def parse(self):
        result=self.disjunction()
        if self.peek() is not None:raise ValueError('Unexpected Boolean token: '+self.peek())
        return result
    def disjunction(self):
        node=self.conjunction()
        while self.peek()=='OR':self.pop();node=('OR',node,self.conjunction())
        return node
    def conjunction(self):
        node=self.unary()
        while self.peek() and self.peek() not in (')','OR'):
            if self.peek()=='AND':self.pop()
            node=('AND',node,self.unary())
        return node
    def unary(self):
        part=self.pop()
        if part=='NOT':return ('NOT',self.unary())
        if part=='(':
            node=self.disjunction()
            if self.pop()!=')':raise ValueError('Missing closing parenthesis')
            return node
        if part in (None,')','AND','OR'):raise ValueError('Expected a search term')
        return ('TERM',tokens(part))

def allowed_docs(store,node,level):
    db=store.db
    if node[0]=='TERM':
        words=node[1]
        if not words:return set()
        postings=[]
        for word in words:
            postings.append({r['doc']:json.loads(r['positions']) for r in db.execute('SELECT doc,positions FROM postings JOIN index_docs ON doc=id WHERE term=? AND level=?',(word,level))})
        possible=set(postings[0])
        for p in sorted(postings[1:],key=len):possible.intersection_update(p)
        if len(words)>1:possible={did for did in possible if any(all(start+i in postings[i][did] for i in range(1,len(words))) for start in postings[0][did])}
        return possible
    if node[0]=='NOT':return {r[0] for r in db.execute('SELECT id FROM index_docs WHERE level=?',(level,))}-allowed_docs(store,node[1],level)
    left=allowed_docs(store,node[1],level);right=allowed_docs(store,node[2],level)
    return left&right if node[0]=='AND' else left|right

def search(store,query,method='bm25',k=10,filters=None,expand=False):
    start=time.perf_counter();db=store.db;filters=filters or {}
    if method not in ('tfidf','bm25','structure'):raise ValueError('Unknown retrieval method')
    if not query.strip() or len(query)>2000:raise ValueError('Query must contain 1–2000 characters')
    config=db.execute("SELECT value FROM config WHERE key='index'").fetchone()
    if not config:raise ValueError('Index has not been built')
    conf=json.loads(config[0]);level='passage' if method=='structure' else 'paper'
    advanced=bool(re.search(r'\b(AND|OR|NOT)\b|["()]',query))
    expanded,changes=normalize(query,expand and not advanced)
    terms=[t for t in tokens(expanded) if t not in STOP]
    if not terms:raise ValueError('Query has no searchable terms')
    allowed=allowed_docs(store,BooleanParser(query).parse(),level) if advanced else None
    n,avgdl=db.execute('SELECT count(*),avg(length) FROM index_docs WHERE level=?',(level,)).fetchone()
    scores=collections.defaultdict(float);contributions=collections.defaultdict(list);qnorm=0
    for term,qtf in collections.Counter(terms).items():
        vr=db.execute('SELECT df,idf FROM vocabulary WHERE term=? AND level=?',(term,level)).fetchone()
        if not vr:continue
        qw=(1+math.log(qtf))*vr['idf'];qnorm+=qw*qw
        idf=math.log(1+(n-vr['df']+0.5)/(vr['df']+0.5))
        for p in db.execute('SELECT doc,tf,length,norm,zone FROM postings JOIN index_docs ON doc=id WHERE term=? AND level=?',(term,level)):
            if allowed is not None and p['doc'] not in allowed:continue
            if method=='tfidf':value=qw*(1+math.log(p['tf']))*vr['idf']/max(p['norm'],1e-12)
            else:value=idf*p['tf']*2.2/(p['tf']+1.2*(0.25+0.75*p['length']/max(avgdl,1)))
            if method=='structure':value*=WEIGHTS.get(p['zone'],1)
            scores[p['doc']]+=value;contributions[p['doc']].append({'term':term,'tf':p['tf'],'df':vr['df'],'contribution':value})
    if method=='tfidf':
        for did in scores:scores[did]/=max(math.sqrt(qnorm),1e-12)
    # NOT-only queries have a defined set result, without inventing positive relevance.
    if allowed is not None:
        for did in allowed:scores.setdefault(did,0)
    parents={};inspected=0
    for did,score in heapq.nlargest(len(scores),scores.items(),key=lambda pair:(pair[1],pair[0])):
        row=db.execute('SELECT paper_id FROM index_docs WHERE id=?',(did,)).fetchone();pid=row[0]
        if pid in parents:continue
        p=dict(db.execute('SELECT * FROM papers WHERE id=?',(pid,)).fetchone());inspected+=1
        if filters.get('fulltext') and p['availability']!='full-text':continue
        if filters.get('human') and p['species']!='human (MeSH)':continue
        if filters.get('year_min') and (not p['year'] or p['year']<int(filters['year_min'])):continue
        if filters.get('year_max') and (not p['year'] or p['year']>int(filters['year_max'])):continue
        if filters.get('topic') and not db.execute('SELECT 1 FROM discoveries WHERE paper_id=? AND topic=? AND decision=?',(pid,filters['topic'],'accepted')).fetchone():continue
        parts=[json.loads(r[0]) for r in db.execute('SELECT payload FROM passages WHERE paper_id=?',(pid,))]
        if filters.get('section'):
            parts=[x for x in parts if x['zone']==filters['section']]
            if not parts:continue
            if method=='structure' and not any(x['id']==did for x in parts):continue
        def passage_score(p):
            if p['id']==did:return float('inf')
            terms_here=collections.Counter(tokens(p['text']))
            return sum(min(terms_here[t],3) for t in set(terms))*WEIGHTS.get(p['zone'],1)/max(1,len(terms_here)**0.3)
        parts=sorted(parts,key=passage_score,reverse=True)
        p.pop('metadata');p['passages']=parts[:3];p['score']=score;p['score_components']=contributions[did];p['rank']=len(parents)+1
        parents[pid]=p
        if len(parents)>=k:break
    return {'query':query,'results':list(parents.values()),'trace':{'method':method,'level':level,'original':query,'expanded':expanded,'expansions':changes,
             'advanced':advanced,'tokens':terms,'filters':filters,'candidate_units':len(scores),'inspected_parents':inspected,'index':conf,
             'latency_ms':(time.perf_counter()-start)*1000,'weights':WEIGHTS if method=='structure' else None,
             'formula':'log TF × smoothed IDF, cosine' if method=='tfidf' else 'BM25 k1=1.2 b=0.75; positive Robertson IDF',
             'diversification':'maximum-scoring unit per unique parent paper','score_meaning':'retrieval relevance, not truth or scientific certainty'}}
