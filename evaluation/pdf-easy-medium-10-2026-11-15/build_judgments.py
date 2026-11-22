"""Materialize the assistant's explicit review notes; no inferred or default grades."""
import hashlib,json,re
from pathlib import Path
P=Path(__file__).resolve().parent
pool=json.loads((P/'pool.json').read_text(encoding='utf-8'))
notes={};qid=None
for line in (P/'review_notes.txt').read_text(encoding='utf-8').splitlines():
    if not line.strip():continue
    if re.fullmatch(r'Q\d\d',line):qid=line;notes[qid]=[];continue
    n,g,why=line.split('|',2)
    assert int(n)==len(notes[qid])+1 and int(g) in (0,1,2,3)
    notes[qid].append((int(g),why))
labels=[]
for qid,entries in notes.items():
    docs=[p for p in pool if p['query_id']==qid]
    assert len(entries)==len(docs),(qid,len(entries),len(docs))
    for p,(grade,why) in zip(docs,entries):
        evidence=[]
        if p['abstract']:evidence.append(dict(source='abstract',text=p['abstract']))
        evidence += [dict(source=s['id'],zone=s['zone'],text=s['text']) for s in p['source_passages']]
        assert evidence
        labels.append(dict(query_id=qid,paper_id=p['id'],title=p['title'],grade=grade,
            reviewer_kind='AI',reviewer='Codex assistant',rationale=why,
            review_scope='Title and query-focused abstract screening; complete abstracts and retrieved source passages inspected for ambiguous cases. No exhaustive full-paper review.',
            evidence=evidence,evidence_sha256=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False).encode()).hexdigest()))
assert len(labels)==len(pool)==310
(P/'judgments.json').write_text(json.dumps(labels,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'Saved {len(labels)} explicit judgments.')
