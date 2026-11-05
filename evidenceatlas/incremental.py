"""Reuse verified passage vectors when expanding a corpus; publish is a separate step."""
import json,time
from pathlib import Path
import numpy as np
from .config import Settings
from .dense import validate_vectors
from .models import MODELS,embedding_model
from .store import Store

def build_incremental(store,settings,baseline_path,previous_directory,batch_size=8):
    started=time.perf_counter();baseline=Store(baseline_path)
    old_directory=Path(previous_directory)
    old=json.loads((old_directory/'manifest.json').read_text())
    if old.get('chunking'):
        baseline.db.close()
        from .chunking import build_chunked
        return build_chunked(store,settings,baseline_path,previous_directory,batch_size)
    if old.get('level')!='passage' or old['model']!=list(MODELS['embedding']):
        raise ValueError('Only passage vectors from the same pinned model can be reused')
    if baseline.fingerprint()!=old['corpus']:raise ValueError('Source corpus does not match source embeddings')
    baseline.db.close()
    old_vectors=np.load(old_directory/'vectors.npy',mmap_mode='r')
    validate_vectors(old_vectors,len(old['ids']))
    positions={p['id']:i for i,p in enumerate(old['ids'])}
    corpus=store.fingerprint();ids=[dict(r) for r in store.db.execute('SELECT id,paper_id,zone FROM passages ORDER BY id')]
    directory=settings.root/'indexes'/('dense-'+corpus[:16]);directory.mkdir(parents=True,exist_ok=True)
    if directory.resolve()==old_directory.resolve():raise ValueError('No changed corpus; leave the existing index intact')
    settings.check_space(additional=len(ids)*384*8)
    model=embedding_model(settings)
    if model.max_seq_length!=old['max_tokens']:raise ValueError('Token limit differs; cannot reuse representations')
    part=directory/'vectors.part.npy';progress_path=directory/'incremental-progress.json'
    state=json.loads(progress_path.read_text()) if progress_path.exists() else {}
    identity={'corpus':corpus,'source_corpus':old['corpus'],'model':list(MODELS['embedding']),'max_tokens':model.max_seq_length}
    if part.exists() and any(state.get(k)!=v for k,v in identity.items()):raise ValueError('Incompatible checkpoint; preserving it')
    offset=state.get('completed',0) if part.exists() else 0
    if not 0<=offset<=len(ids):raise ValueError('Invalid checkpoint size')
    reused=state.get('reused',0) if offset else 0;encoded=state.get('encoded_new',0) if offset else 0
    truncated=state.get('truncated',0) if offset else 0
    vectors=np.lib.format.open_memmap(part,mode='r+' if part.exists() else 'w+',dtype='float32',shape=(len(ids),384))
    store.db.execute('ATTACH DATABASE ? AS previous',(str(baseline_path),))
    cursor=store.db.execute('SELECT n.id,n.text,b.text AS previous_text FROM passages n LEFT JOIN previous.passages b ON b.id=n.id ORDER BY n.id LIMIT -1 OFFSET ?',(offset,))
    while batch:=cursor.fetchmany(64):
        missing=[];destinations=[]
        for j,row in enumerate(batch):
            truncated+=len(model.tokenizer.encode(row['text'],add_special_tokens=True,truncation=False))>model.max_seq_length
            old_index=positions.get(row['id'])
            # The complete text is compared, not just the truncated hash embedded in a passage ID.
            if old_index is not None and row['text']==row['previous_text']:
                vectors[offset+j]=old_vectors[old_index];reused+=1
            else:missing.append(row['text']);destinations.append(offset+j)
        if missing:
            fresh=model.encode(missing,batch_size=batch_size,normalize_embeddings=True,show_progress_bar=False)
            vectors[destinations]=fresh;encoded+=len(missing)
        offset+=len(batch)
        if offset%256==0 or offset==len(ids):
            vectors.flush();state={**identity,'completed':offset,'reused':reused,'encoded_new':encoded,'truncated':truncated,'elapsed_seconds':time.perf_counter()-started}
            Settings.atomic_json(progress_path,state);print(json.dumps(state),flush=True)
    validation=validate_vectors(vectors,len(ids))
    if store.fingerprint()!=corpus:raise ValueError('Corpus changed while encoding; not publishing')
    vectors.flush();del vectors;part.replace(directory/'vectors.npy')
    metadata={**identity,'level':'passage','input':'each normalized section passage; first 256 model tokens; full paragraph retained in lexical index',
        'dimensions':384,'passages':len(ids),'truncated_passages':truncated,'reused_vectors':reused,'new_vectors':encoded,
        'elapsed_seconds':time.perf_counter()-started,'validation':validation,'ids':ids,'path':str(directory),
        'activation':'staged; activate only with the matching corpus'}
    Settings.atomic_json(directory/'manifest.json',metadata)
    # Deliberately do not change dense-active.json while the live corpus is still the old version.
    store.db.execute('DETACH DATABASE previous')
    return {k:v for k,v in metadata.items() if k!='ids'}
