"""Index integrity and exact passage selection without model downloads/inference."""
import json
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import pytest
from evidenceatlas.dense import validate_vectors,DenseIndex
from test_core import corpus

@pytest.mark.parametrize('bad',['zero','nan','shape','scaled'])
def test_reject_invalid_vectors(bad):
    v=np.zeros((2,384),dtype=np.float32);v[:,0]=1
    if bad=='zero':v[0]=0
    elif bad=='nan':v[0,0]=np.nan
    elif bad=='shape':v=v[:,:383]
    else:v[0,0]=2
    with pytest.raises(ValueError):validate_vectors(v,2)

def test_passage_match_and_section_filter(corpus):
    index=DenseIndex.__new__(DenseIndex)
    parts=[p for pid in ('1','2') for p in corpus.paper(pid)['passages']]
    index.meta={'model':['fixture','fixture'],'corpus':corpus.fingerprint(),'level':'passage','ids':parts}
    index.vectors=np.zeros((len(parts),384),dtype=np.float32);index.vectors[:,1]=1
    chosen=next(i for i,p in enumerate(parts) if p['paper_id']=='1' and p['zone']=='abstract')
    index.vectors[chosen,0]=1;index.vectors[chosen,1]=0
    index.model=SimpleNamespace(encode=lambda *a,**kw:np.eye(1,384,dtype=np.float32))
    result=index.search(corpus,'caffeine',k=1,filters={'section':'abstract'})
    assert result['results'][0]['id']=='1'
    assert result['results'][0]['passages'][0]['id']==parts[chosen]['id']
    assert result['trace']['level']=='passage'
    assert not index.search(corpus,'caffeine',filters={'section':'results'})['results']
