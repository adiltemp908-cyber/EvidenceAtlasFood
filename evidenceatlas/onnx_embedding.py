"""Local pinned ONNX model with documented masked-mean pooling and L2 normalization."""
import numpy as np

class OnnxEmbedding:
    def __init__(self,settings):
        import onnxruntime as ort
        from transformers import AutoTokenizer
        path=settings.root/'models/embedding'
        self.tokenizer=AutoTokenizer.from_pretrained(str(path),local_files_only=True,trust_remote_code=False)
        self.max_seq_length=256
        options=ort.SessionOptions();options.intra_op_num_threads=4;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(path/'onnx/model_quint8_avx2.onnx'),sess_options=options,providers=['CPUExecutionProvider'])
        self.names={i.name for i in self.session.get_inputs()}
    def encode(self,texts,batch_size=32,normalize_embeddings=True,show_progress_bar=False):
        results=[]
        for start in range(0,len(texts),batch_size):
            enc=self.tokenizer(texts[start:start+batch_size],padding=True,truncation=True,max_length=self.max_seq_length,return_tensors='np')
            inputs={k:v.astype(np.int64) for k,v in enc.items() if k in self.names}
            output=self.session.run(None,inputs)[0]
            mask=enc['attention_mask'][...,None].astype(np.float32)
            vectors=(output*mask).sum(axis=1)/np.maximum(mask.sum(axis=1),1e-9)
            if normalize_embeddings:vectors/=np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-9)
            results.append(vectors.astype(np.float32))
        return np.concatenate(results,axis=0)
