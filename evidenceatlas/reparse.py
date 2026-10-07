"""Rebuild normalized text from preserved raw source records without redownloading."""
import gzip
import json
from .config import Settings
from .store import Store
from .parsing import abstract_text,paragraphs_jats,make_passages,screen,PARSER_VERSION,SCREENING_VERSION
from .acquisition import now
from .taxonomy import TOPICS
from .retrieval import build

def reparse(settings):
    s=Store(settings.root/'data/normalized/corpus.sqlite');changed=0
    for row in s.db.execute('SELECT id FROM papers').fetchall():
        paper=s.paper(row[0]);record=paper['metadata']['source_record']
        paper['title']=abstract_text(record.get('title'));paper['abstract']=abstract_text(record.get('abstractText'))
        body=None;full=paper['metadata'].get('fulltext',{})
        if paper['availability']=='full-text':
            raw=settings.root/'data/raw'/(full['raw_sha256']+'.gz')
            body,details=paragraphs_jats(gzip.decompress(raw.read_bytes()));details['raw_sha256']=full['raw_sha256'];paper['metadata']['fulltext']=details
        discoveries=s.db.execute('SELECT * FROM discoveries WHERE paper_id=?',(paper['id'],)).fetchall()
        with s.db:
            for d in discoveries:
                decision,reason,species=screen(record,TOPICS[d['topic']][2])
                s.db.execute('INSERT INTO screening_history VALUES(?,?,?,?,?,?,?)',(paper['id'],d['topic'],d['query_hash'],d['decision'],d['reason'],paper['metadata'].get('screening_version','unknown'),now()))
                s.db.execute('UPDATE discoveries SET decision=?,reason=? WHERE paper_id=? AND topic=? AND query_hash=?',(decision,reason,paper['id'],d['topic'],d['query_hash']))
                paper['species']=species
        paper['metadata']['screening_version']=SCREENING_VERSION
        discoveries=s.db.execute('SELECT * FROM discoveries WHERE paper_id=?',(paper['id'],)).fetchall()
        accepted=any(d['decision']=='accepted' for d in discoveries)
        parts=make_passages(paper['id'],paper['title'],paper['abstract'],body) if accepted else []
        if discoveries:
            d=discoveries[0];s.save(paper,parts,d['topic'],d['query_hash'],d['decision'],d['reason'])
        changed+=1
    settings.check_space(rebuild=500_000_000)
    index=build(s)
    print(json.dumps({'reparsed_papers':changed,'parser':PARSER_VERSION,'index':index,'counts':s.counts()},indent=2))

if __name__=='__main__':
    settings=Settings.load();settings.initialize();reparse(settings)
