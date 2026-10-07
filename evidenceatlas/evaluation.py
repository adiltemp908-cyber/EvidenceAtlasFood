"""Metrics refuse to silently treat unjudged retrievals as irrelevant."""
import math

def metrics(ranking,qrels,k=10):
    ranking=list(dict.fromkeys(ranking))[:k]
    relevant={doc for doc,grade in qrels.items() if grade>=2}
    judged=[doc for doc in ranking if doc in qrels]
    found=sum(doc in relevant for doc in ranking)
    complete=len(judged)==len(ranking)
    dcg=sum((2**qrels[doc]-1)/math.log2(i+2) for i,doc in enumerate(ranking)) if complete else None
    ideal=sum((2**grade-1)/math.log2(i+2) for i,grade in enumerate(sorted(qrels.values(),reverse=True)[:k]))
    return {'k':k,'returned':len(ranking),'judged_fraction':len(judged)/len(ranking) if ranking else 1,
            'precision_at_k':found/k if complete else None,'precision_bounds':[found/k,(found+len(ranking)-len(judged))/k],
            'recall_at_k_judged_pool':found/len(relevant) if relevant else None,
            'ndcg_at_k':dcg/ideal if complete and ideal else None,'relevant_pool_size':len(relevant),
            'protocol':'Grade>=2 relevant; unjudged not assumed irrelevant; recall is relative to judged pool'}
