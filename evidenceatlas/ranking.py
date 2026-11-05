"""Small, explicit publication-year preference for interactive search results."""
from datetime import date
import math

MAX_BONUS_FRACTION = .03
HALF_LIFE_YEARS = 5

def apply_recency(run, k, enabled=True, as_of=None):
    """Apply once after all retrieval/reranking, before cutting the displayed list.

    The bonus is additive even for negative cross-encoder logits. Its ceiling is
    3% of the absolute best relevance score in the fetched candidate pool.
    It is an unvalidated ranking preference, never a scientific-quality score.
    """
    as_of=as_of or date.today()
    if 'recency' in run['trace']:raise ValueError('Recency already applied')
    papers=run['results'];raw=[float(p['score']) for p in papers]
    if any(not math.isfinite(x) for x in raw):raise ValueError('Nonfinite relevance score')
    scale=abs(max(raw)) if raw else 0.0
    for p,score in zip(papers,raw):
        year=p.get('year');valid=isinstance(year,int) and not isinstance(year,bool) and 1800<=year<=as_of.year
        freshness=2**(-(as_of.year-year)/HALF_LIFE_YEARS) if valid else 0.0
        bonus=scale*MAX_BONUS_FRACTION*freshness if enabled else 0.0
        p['score_components'].append({'recency_bonus':bonus,'relevance_score':score,'publication_year':year})
        p['score']=score+bonus
    # Stable sorting preserves relevance order for equal adjusted scores.
    run['results']=sorted(papers,key=lambda p:-p['score'])[:k]
    for rank,p in enumerate(run['results'],1):p['rank']=rank
    run['trace']['recency']={'enabled':enabled,'as_of':as_of.isoformat(),'date_precision':'publication year',
        'max_bonus_fraction':MAX_BONUS_FRACTION,'half_life_years':HALF_LIFE_YEARS,'reference_score':scale,
        'candidate_count':len(papers),'max_absolute_bonus':scale*MAX_BONUS_FRACTION if enabled else 0.0,
        'formula':'0.03 * abs(best relevance score) * 2^(-age_years/5)',
        'missing_or_future_year':'no bonus','stage':'once, after relevance reranking and before displayed top-k',
        'validation':'user-requested ranking preference; no demonstrated accuracy or evidence-quality improvement'}
    return run
