from datetime import date
from copy import deepcopy
import pytest
from evidenceatlas.ranking import apply_recency

def run(items):
    return {'results':[{'id':pid,'score':score,'year':year,'rank':i,'score_components':[]} for i,(pid,score,year) in enumerate(items,1)],'trace':{}}

def test_newer_near_tie_can_cross_display_cutoff_but_not_large_gap():
    r=apply_recency(run([('strong',12,1990),('old',10,2000),('new',9.9,2026)]),2,as_of=date(2026,10,19))
    assert [p['id'] for p in r['results']]==['strong','new']
    assert r['results'][1]['score_components'][-1]['recency_bonus']==pytest.approx(.36)
    assert r['trace']['recency']['candidate_count']==3

def test_disabled_reproduces_original_order_and_scores():
    original=run([('old',10,1990),('new',9.99,2026)])
    r=apply_recency(deepcopy(original),2,False,as_of=date(2026,10,19))
    assert [(p['id'],p['score']) for p in r['results']]==[(p['id'],p['score']) for p in original['results']]

def test_negative_logits_are_bonus_not_penalty_and_invalid_years_get_none():
    r=apply_recency(run([('old',-1,2000),('new',-1.01,2026),('future',-1.01,2027),('missing',-1.01,None)]),4,as_of=date(2026,10,19))
    assert r['results'][0]['id']=='new' and r['results'][0]['score']==pytest.approx(-.98)
    assert all(p['score']==-1.01 for p in r['results'] if p['id'] in ('future','missing'))

def test_bonus_halves_every_five_years_and_cannot_be_applied_twice():
    r=apply_recency(run([('new',1,2026),('five',1,2021),('ten',1,2016)]),3,as_of=date(2026,10,19))
    assert [p['score_components'][-1]['recency_bonus'] for p in r['results']]==pytest.approx([.03,.015,.0075])
    with pytest.raises(ValueError,match='already applied'):apply_recency(r,3)

def test_empty_and_zero_score_queries_do_not_invent_relevance():
    assert not apply_recency(run([]),3)['results']
    assert apply_recency(run([('new',0,2026)]),1,as_of=date(2026,10,19))['results'][0]['score']==0


def test_product_screen_keeps_nutrition_trials_and_quarantines_technology():
    from evidenceatlas.parsing import screen
    assert screen({'title':'Nanozyme sensor array for soy milk traceability','abstractText':'Soy milk protein supports nutrition and health'},['soy'])[0]=='needs_review'
    assert screen({'title':'Liposomal drug delivery of creatine for health'},['creatine'])[0]=='needs_review'
    assert screen({'title':'Oral collagen supplementation improves skin hydration: a randomized trial'},['collagen'])[0]=='accepted'
    assert screen({'title':'Creatine supplementation and exercise performance in adults'},['creatine'])[0]=='accepted'
