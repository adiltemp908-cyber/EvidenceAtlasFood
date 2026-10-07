"""Pinned, CPU-only experimental models. Downloads and caches stay on the data volume."""
from __future__ import annotations
import json
from .config import Settings

MODELS={
    'embedding':('sentence-transformers/all-MiniLM-L6-v2','1110a243fdf4706b3f48f1d95db1a4f5529b4d41'),
    'reranker':('cross-encoder/ms-marco-MiniLM-L6-v2','233902d25c440f23af6f7d6e94d2946bac0bee0a'),
    'nli':('cross-encoder/nli-MiniLM2-L6-H768','b95119ce93d3e065de6214e38cd4a97b0f2f2c6d'),
}

def index_metadata(settings):
    from pathlib import Path
    active=settings.root/'indexes/dense-active.json'
    if not active.exists():return None
    pointer=json.loads(active.read_text());directory=settings.root/'indexes'/Path(pointer['path']).name
    manifest=json.loads((directory/'manifest.json').read_text())
    return {k:v for k,v in manifest.items() if k not in ('ids','path')}

def prepare(names=('embedding','reranker')):
    settings=Settings.load();settings.initialize()
    from huggingface_hub import snapshot_download
    for name in names:
        model,revision=MODELS[name];settings.check_space(additional=800_000_000)
        path=snapshot_download(model,revision=revision,local_dir=str(settings.root/'models'/name),
            allow_patterns=['*.json','*.txt','*.safetensors','README.md','1_Pooling/*'],max_workers=2)
        Settings.atomic_json(settings.root/'data/manifests'/f'model-{name}.json',{'id':model,'revision':revision,'path':path,'device':'cpu','validation':'Not independently validated for food claims'})
        print(json.dumps({'model':name,'path':path,'revision':revision}),flush=True)

def embedding_model(settings):
    import torch
    from sentence_transformers import SentenceTransformer
    torch.set_num_threads(4)
    return SentenceTransformer(str(settings.root/'models/embedding'),device='cpu',local_files_only=True,trust_remote_code=False)

def cross_model(settings,name):
    import torch
    from sentence_transformers import CrossEncoder
    torch.set_num_threads(2)
    return CrossEncoder(str(settings.root/'models'/name),device='cpu',local_files_only=True,trust_remote_code=False,max_length=384)

if __name__=='__main__':
    import sys
    prepare(tuple(sys.argv[1:]) or ('embedding','reranker'))
