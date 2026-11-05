"""Publish a verified staged corpus/index pair, preserving sessions and a rollback backup."""
import argparse,json,os,sqlite3,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import psutil,requests
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.dense import validate_vectors
from evidenceatlas.models import MODELS
from evidenceatlas.acquisition import now

def backup(source,destination):
    a=sqlite3.connect(str(source));b=sqlite3.connect(str(destination))
    try:a.backup(b)
    finally:b.close();a.close()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='expansion-2026-10-13');parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--check-query',action='append',help='Live verification query; repeat for multiple product topics')
    args=parser.parse_args()
    settings=Settings.load();settings.initialize();folder=settings.root/'experiments'/args.run
    state=json.loads((folder/'status.json').read_text())
    if state['status']!='ready-to-publish':raise ValueError('Finish and verify indexing before publication')
    live=settings.root/'data/normalized/corpus.sqlite';staged=folder/'corpus.sqlite'
    store=Store(staged);target=store.fingerprint();store.db.close()
    active_path=settings.root/'indexes/dense-active.json';old_active=json.loads(active_path.read_text())
    new_directory=settings.root/'indexes'/Path(state['dense']['path']).name;meta=json.loads((new_directory/'manifest.json').read_text())
    if meta['corpus']!=target or meta['model']!=list(MODELS['embedding']):raise ValueError('Mismatched staged dense index')
    vectors=np.load(new_directory/'vectors.npy',mmap_mode='r');validate_vectors(vectors,len(meta['ids']));del vectors
    current=Store(live)
    if current.fingerprint()!=state['before_corpus']:raise ValueError('Live literature changed; merge before publication')
    current.db.close()
    servers=[]
    for proc in psutil.process_iter(['cmdline']):
        command=proc.info['cmdline'] or []
        if 'evidenceatlas.cli' not in command or 'serve' not in command:continue
        port=int(command[command.index('--port')+1]) if '--port' in command else 8765
        if port==args.port:servers.append(proc)
    if len(servers)>1:raise ValueError('Multiple matching servers; refusing to stop unrelated processes')
    rollback=folder/'live-before-publish.sqlite'
    if rollback.exists():raise ValueError('Rollback file already exists; preserve it and inspect state')
    app=Path(__file__).resolve().parents[1];url=f'http://127.0.0.1:{args.port}'
    def start_server():
        nonlocal process
        log=(settings.root/'tmp/interface-launch.log').open('ab')
        process=subprocess.Popen([sys.executable,'-m','evidenceatlas.cli','serve','--port',str(args.port)],cwd=app,stdin=subprocess.DEVNULL,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        log.close()
        for _ in range(60):
            try:
                if requests.get(url+'/api/health',timeout=1).json().get('status')=='ok':return process
            except requests.RequestException:pass
            if process.poll() is not None:raise RuntimeError('Server exited; see interface-launch.log')
            time.sleep(.5)
        raise RuntimeError('Server did not become ready')
    process=None;live_changed=False
    try:
        for proc in servers:proc.terminate();proc.wait(timeout=30)
        backup(live,rollback)
        latest=Store(rollback)
        try:
            if latest.fingerprint()!=state['before_corpus']:raise ValueError('Live collection changed during publication preflight')
        finally:latest.db.close()
        # Preserve notes created since the staging snapshot.
        db=sqlite3.connect(str(staged))
        try:
            db.execute('ATTACH DATABASE ? AS latest',(str(rollback),))
            with db:
                db.execute('DELETE FROM sessions');db.execute('INSERT INTO sessions SELECT * FROM latest.sessions')
            session_count=db.execute('SELECT count(*) FROM sessions').fetchone()[0]
        finally:db.close()
        state['rollback']={'database':str(rollback),'dense_active':old_active};state['status']='publishing'
        Settings.atomic_json(folder/'status.json',state)
        live_changed=True
        backup(staged,live)
        Settings.atomic_json(active_path,{'path':str(new_directory),'corpus':target})
        process=start_server();coverage=requests.get(url+'/api/coverage',timeout=30).json()
        assert coverage['index']['corpus']==target==coverage['dense_index']['corpus']
        checks=[]
        for q in args.check_query or ['Do eggs raise cholesterol?','Does eating more protein help build muscle?','Is breakfast cereal healthy?','Does yogurt help digestion?']:
            response=requests.get(url+'/api/search',params={'q':q,'method':'hybrid','rerank':'true','k':5},timeout=120)
            response.raise_for_status();data=response.json();assert data['results']
            checks.append({'query':q,'trace':data['trace'],'results':[{'id':p['id'],'title':p['title'],'availability':p['availability'],'passage_ids':[s['id'] for s in p['passages']]} for p in data['results']]})
        state.update(status='published',published_at=now(),counts=coverage['counts'],storage=coverage['storage'],sessions_preserved=session_count,server_pid=process.pid)
        Settings.atomic_json(folder/'post-expansion-searches.json',checks)
        Settings.atomic_json(folder/'status.json',state)
        print(json.dumps({'status':state['status'],'counts':state['counts'],'dense':state['dense'],'sessions_preserved':session_count},indent=2))
    except Exception as exc:
        if process is not None and process.poll() is None:process.terminate();process.wait(timeout=30)
        if live_changed:backup(rollback,live)
        Settings.atomic_json(active_path,old_active);start_server()
        state.update(status='rolled-back',error=str(exc));Settings.atomic_json(folder/'status.json',state);raise

if __name__=='__main__':main()
