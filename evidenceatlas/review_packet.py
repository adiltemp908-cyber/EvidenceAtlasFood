"""Create a small unlabeled onboarding packet from actual frozen development runs."""
from pathlib import Path
import argparse,json,random,shutil,statistics
from .store import Store
from .config import Settings

def make(snapshot,out):
    out.mkdir(exist_ok=True,parents=True);store=Store(snapshot/'corpus.sqlite')
    corpus=store.fingerprint();runs=json.loads((snapshot/'runs.json').read_text())
    claims=[json.loads(s) for s in (Path(__file__).resolve().parents[1]/'evaluation/claims.jsonl').read_text().splitlines()]
    # Declarative development claims only. This onboarding subset cannot yield full-pool recall.
    claims=[c for c in claims if c['split']=='development' and not c['claim'].endswith('?')]
    packet=[]
    for c in claims:
        candidates={}
        for r in runs:
            if r['claim_id']!=c['id']:continue
            for p in r['ranking'][:3]:candidates.setdefault(p['id'],set()).update(p['passage_ids'])
        ids=list(candidates);random.Random(20261007).shuffle(ids)
        for pid in ids:
            p=store.paper(pid);passages=[x for x in p['passages'] if x['id'] in candidates[pid] and x['zone']!='title']
            packet.append({'claim_id':c['id'],'claim':c['claim'],'paper_id':pid,'title':p['title'],'availability':p['availability'],
                'source_url':'https://pubmed.ncbi.nlm.nih.gov/'+p['pmid']+'/' if p['pmid'] else None,
                'local_context_url':'http://127.0.0.1:8765/api/papers/'+pid,
                'candidate_passages':[{'passage_id':x['id'],'section':x['section'],'text':x['text'],'start':0,'end':len(x['text'])} for x in passages],
                'judgment':{'claim_id':c['id'],'paper_id':pid,'reviewer_id':None,'reviewer_kind':None,'qualifications':None,'relevance':None,'stance':None,'compatibility':None,'corpus':corpus,'rationale':[]}})
    Settings.atomic_json(out/'review-packet.json',{'purpose':'Unlabeled onboarding subset, union of top 3 from seven methods; source candidates are not adjudicated rationales','corpus':corpus,'claims':len(claims),'pairs':len(packet),'items':packet})
    summary=json.loads((snapshot/'summary.json').read_text())
    summary['median_latency_ms']={m:statistics.median(v) for m,v in summary['latencies_ms'].items()}
    summary['corpus']=corpus;summary['snapshot']=str(snapshot);summary['review_packet_pairs']=len(packet)
    Settings.atomic_json(out/'delivery-summary.json',summary)
    for name in ('runs.json','blinded-pool.json','manifest.json'):shutil.copyfile(snapshot/name,out/name)
    store.db.close();return {'claims':len(claims),'pairs':len(packet),'median_latency_ms':summary['median_latency_ms']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('snapshot',type=Path);p.add_argument('out',type=Path);a=p.parse_args();print(json.dumps(make(a.snapshot,a.out),indent=2))
