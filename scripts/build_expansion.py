"""Build lexical and incremental semantic indexes for the isolated collection."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.retrieval import build
from evidenceatlas.incremental import build_incremental

parser=argparse.ArgumentParser();parser.add_argument('--run',default='expansion-2026-10-13');args=parser.parse_args()
settings=Settings.load();settings.initialize();folder=settings.root/'experiments'/args.run
state=json.loads((folder/'status.json').read_text())
if state['status'] not in ('acquired-awaiting-indexes','indexing'):raise ValueError('Finish acquisition first')
state['status']='indexing';Settings.atomic_json(folder/'status.json',state)
store=Store(folder/'corpus.sqlite');state['lexical']=build(store);Settings.atomic_json(folder/'status.json',state)
previous=json.loads((settings.root/'indexes/dense-active.json').read_text())
if previous['corpus']!=state['before_corpus']:raise ValueError('The active corpus changed; do not reuse an unrelated index')
state['dense']=build_incremental(store,settings,folder/'baseline.sqlite',settings.root/'indexes'/Path(previous['path']).name)
state['status']='ready-to-publish';state['counts']=store.counts();state['corpus']=store.fingerprint()
Settings.atomic_json(folder/'status.json',state);store.db.close()
print(json.dumps({k:v for k,v in state.items() if k not in ('batches','errors')},indent=2))
