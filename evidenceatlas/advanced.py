from __future__ import annotations
import json
import re
import threading
import time
from .retrieval import search,normalize,tokens
from .dense import DenseIndex,fuse
from .models import cross_model,MODELS

class ResearchEngine:
    def __init__(self,settings):
        self.settings=settings;self.dense=None;self.reranker=None;self.nli=None;self.lock=threading.Lock()
    def run(self,store,query,method='hybrid',k=10,filters=None,expand=True,rerank=False):
        with self.lock:
            start=time.perf_counter();expanded,changes=normalize(query,expand)
            if self.dense is not None:
                active=json.loads((self.settings.root/'indexes/dense-active.json').read_text())
                if __import__('pathlib').Path(active['path']).name!=self.dense.directory.name:self.dense=None
            if method=='dense':
                if self.dense is None:self.dense=DenseIndex(self.settings)
                run=self.dense.search(store,expanded,k,filters)
            elif method=='hybrid':
                if self.dense is None:self.dense=DenseIndex(self.settings)
                lexical=search(store,query,'structure',k=40,filters=filters,expand=expand)
                dense=self.dense.search(store,expanded,40,filters)
                run=fuse([lexical,dense],k=20 if rerank else k)
            else:run=search(store,query,method,k=20 if rerank else k,filters=filters,expand=expand)
            if rerank and run['results']:
                if self.reranker is None:self.reranker=cross_model(self.settings,'reranker')
                pairs=[(query,p['title']+' '+p['passages'][0]['text']) for p in run['results'] if p['passages']]
                values=self.reranker.predict(pairs,batch_size=4,show_progress_bar=False)
                for p,score in zip(run['results'],values):p['score_components'].append({'pre_rerank_rank':p['rank'],'cross_encoder_score':float(score)});p['score']=float(score)
                run['results']=sorted(run['results'],key=lambda p:-p['score'])[:k]
                for i,p in enumerate(run['results'],1):p['rank']=i
                run['trace']['reranker']={'model':MODELS['reranker'],'pair_limit':20,'max_tokens':384,'candidate_text':'title plus top passage; may truncate','validation':'experimental relevance model, not a stance classifier'}
            run['query']=query;run['trace'].update({'original':query,'expanded':expanded,'expansions':changes,'latency_ms':(time.perf_counter()-start)*1000})
            return run

    def experimental_stance(self,claim,passages):
        """NLI diagnostic only. Neutral is not proof of absence of scientific evidence."""
        with self.lock:
            if self.nli is None:self.nli=cross_model(self.settings,'nli')
            labels={int(k):v for k,v in self.nli.model.config.id2label.items()}
            values=self.nli.predict([(p['text'],claim) for p in passages],batch_size=4,show_progress_bar=False)
            result=[]
            for p,row in zip(passages,values):
                label=labels[int(row.argmax())]
                mapping={'entailment':'supports','contradiction':'contradicts','neutral':'insufficient to establish'}
                result.append({'passage_id':p['id'],'model_label':label,'candidate_stance':mapping.get(label.lower(),'unmapped'),
                    'status':'experimental model inference; not human validated','compatibility':'unknown; evaluated separately',
                    'scores':{labels[i]:float(v) for i,v in enumerate(row)},'score_semantics':'uncalibrated model output, not scientific certainty',
                    'model':MODELS['nli'],'input_order':'source passage, original claim','max_tokens':384,'truncation_possible':True})
            return result

def counter_search(store,query,baseline,filters=None,k=10):
    # Preserve query entities/outcomes; alternatives are finding patterns, not a negated claim.
    core=[x for x in tokens(query) if x not in {'does','do','is','are','the','a','an','and','or','not','no','cause','causes','harmful','better','good','bad','affect','affects'}]
    if len(core)<2:return {'runs':[],'additional':[],'status':'Need a food/exposure and outcome for targeted alternatives'}
    base_ids={p['id'] for p in baseline['results']};additional={};traces=[]
    for suffix in ('null no association unchanged','adverse increased risk reduced benefit'):
        run=search(store,query+' '+suffix,'structure',k=30,filters=filters,expand=True)
        kept=[]
        for paper in run['results']:
            # Enforce substantial original-query overlap instead of accepting generic null/adverse papers.
            text=' '.join([paper['title'],paper['abstract']]+[p['text'] for p in paper['passages']]).lower()
            matched=[t for t in set(core) if re.search(r'\b'+re.escape(t)+r'\b',text)]
            if len(matched)<min(3,len(set(core))):continue
            kept.append(paper['id'])
            if paper['id'] not in base_ids and paper['id'] not in additional:additional[paper['id']]=paper
        traces.append({'query':query+' '+suffix,'purpose':'alternative-finding candidates, not established opposing evidence','retained_ids':kept,'trace':run['trace']})
    return {'runs':traces,'additional':list(additional.values())[:k],'status':'Candidate search only; stance and applicability must be assessed against original claim','original_claim':query,'iterations':2}
