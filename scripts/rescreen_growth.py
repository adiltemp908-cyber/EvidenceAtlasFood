"""Apply current domain screening to newly acquired records; preserve metadata and raw papers."""
import argparse,json,sqlite3,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidenceatlas.store import Store
from evidenceatlas.taxonomy import TOPICS
from evidenceatlas.parsing import screen,SCREENING_VERSION
from evidenceatlas.config import Settings
from evidenceatlas.acquisition import now
from evidenceatlas.topic_screening import screen_topic, VERSION as TOPIC_SCREENING_VERSION
parser=argparse.ArgumentParser();parser.add_argument('--run',default='expansion-2026-10-13');args=parser.parse_args()
settings=Settings.load();folder=settings.root/'experiments'/args.run
state=json.loads((folder/'status.json').read_text())
if state['status']!='acquired-awaiting-indexes':raise ValueError('Run only after acquisition, before indexing')
store=Store(folder/'corpus.sqlite');store.db.execute('ATTACH DATABASE ? AS old',(str(folder/'baseline.sqlite'),))
ids=[r[0] for r in store.db.execute('SELECT p.id FROM papers p LEFT JOIN old.papers o ON o.id=p.id WHERE o.id IS NULL')]
changes=[]
for pid in ids:
    paper=store.paper(pid);record=paper['metadata']['source_record'];old_version=paper['metadata'].get('screening_version','unknown')
    discoveries=list(store.db.execute('SELECT * FROM discoveries WHERE paper_id=?',(pid,)))
    with store.db:
        for d in discoveries:
            decision,reason,species=screen_topic(record,d['topic'])
            if decision!=d['decision']:
                store.db.execute('INSERT INTO screening_history VALUES(?,?,?,?,?,?,?)',(pid,d['topic'],d['query_hash'],d['decision'],d['reason'],old_version,now()))
                store.db.execute('UPDATE discoveries SET decision=?,reason=? WHERE paper_id=? AND topic=? AND query_hash=?',(decision,reason,pid,d['topic'],d['query_hash']))
                changes.append({'id':pid,'title':paper['title'],'topic':d['topic'],'from':d['decision'],'to':decision,'reason':reason})
        paper['metadata']['screening_version']=SCREENING_VERSION
        paper['metadata']['topic_screening_version']=TOPIC_SCREENING_VERSION
        store.db.execute('UPDATE papers SET metadata=? WHERE id=?',(json.dumps(paper['metadata']),pid))
        if not store.db.execute("SELECT 1 FROM discoveries WHERE paper_id=? AND decision='accepted'",(pid,)).fetchone():
            store.db.execute('DELETE FROM passages WHERE paper_id=?',(pid,))
summary={'screening_version':SCREENING_VERSION,'topic_screening_version':TOPIC_SCREENING_VERSION,'reviewer_kind':'AI-assisted rule diagnostic, not independent human validation','reviewed_records':len(ids),'changes':changes,'counts':store.counts()}
Settings.atomic_json(folder/'screening-check.json',summary);state['screening_check']=str(folder/'screening-check.json');state['counts']=store.counts();state['corpus']=store.fingerprint()
Settings.atomic_json(folder/'status.json',state);store.db.close();print(json.dumps(summary,indent=2))
