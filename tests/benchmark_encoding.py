import json,time
import numpy as np
from evidenceatlas.config import Settings
from evidenceatlas.store import Store
from evidenceatlas.models import embedding_model
from evidenceatlas.onnx_embedding import OnnxEmbedding

s=Settings.load();s.initialize();store=Store(s.root/'data/normalized/corpus.sqlite')
texts=[r[0] for r in store.db.execute("SELECT text FROM passages WHERE zone='results' ORDER BY id LIMIT 64")]
torch=embedding_model(s);start=time.perf_counter();a=torch.encode(texts,batch_size=32,normalize_embeddings=True,show_progress_bar=False);first=time.perf_counter()-start
onnx=OnnxEmbedding(s);start=time.perf_counter();b=onnx.encode(texts);second=time.perf_counter()-start
similarities=(a*b).sum(axis=1)
report={'passages':len(texts),'torch_seconds':first,'onnx_seconds':second,'speedup':first/second,'mean_pair_cosine':float(similarities.mean()),'minimum_pair_cosine':float(similarities.min()),'note':'Runtime/numerical agreement diagnostic, not food retrieval quality. Concurrent encoding job may affect timing.'}
(s.root/'experiments/encoding-comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
