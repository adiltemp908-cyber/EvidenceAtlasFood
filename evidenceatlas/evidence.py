"""Grounded candidate extraction. No heuristic is represented as validated entailment."""
from __future__ import annotations
import re

PATTERNS={
 'food_identity':r'\b(?:coffee|caffeine|tea|milk|dairy|yogurt|sodium|salt|dietary protein|protein supplement|dietary fib(?:er|re)|sweeteners?|aspartame|sucralose|saturated fat|polyunsaturated fat|vegetable oils?|seed oils?|vitamin [A-Z0-9]+|calcium|iron|zinc|fish|whole grains?|nuts?|fruit juice|whole fruit)\b',
 'population':r'\b(?:\d+\s+)?(?:healthy\s+)?(?:adults?|participants?|patients?|children|adolescents?|women|men|mice|rats)\b',
 'baseline_status':r'\b(?:healthy|prediabetic|overweight|obese|chronic kidney disease|hemodialysis|vitamin [A-Z0-9]+.deficient|deficien\w+|hypertensive|normotensive|diabetic)\b',
 'dose':r'\b\d+(?:\.\d+)?(?:\s*[–-]\s*\d+(?:\.\d+)?)?\s*(?:mg|µg|μg|mcg|g|kg|mL|ml|kcal|IU)(?:\s*/\s*(?:kg|day|d|week|h))?\b',
 'timing':r'\b(?:\d+\s*(?:hours?|h)\s*(?:before|after)\s*\w+|morning|afternoon|evening|bedtime|overnight)\b',
 'duration':r'\b\d+(?:\s*[–-]\s*\d+)?\s*(?:weeks?|months?|years?|days?)\b',
 'frequency':r'\b(?:daily|weekly|twice daily|once daily|\d+\s*(?:times|servings|cups)\s*(?:per|a)\s*(?:day|week))\b',
 'preparation':r'\b(?:boiled|steamed|fried|roasted|raw|filtered|unfiltered|fermented|decaffeinated)\b',
 'comparator':r'\b(?:placebo|control group|usual diet|compared (?:with|to) [^.;]{3,90}|versus [^.;]{3,90})',
 'substitution':r'\b(?:replac(?:ing|ed|ement)[^.;]{3,110}|substitut(?:ing|ed|ion)[^.;]{3,110})',
 'effect_measure':r'\b(?:odds ratio|hazard ratio|relative risk|risk ratio|mean difference|OR|HR|RR|95%\s*CI)[^.;]{0,70}',
 'outcome':r'\b(?:sleep latency|sleep duration|sleep efficiency|blood pressure|body weight|weight loss|glomerular filtration rate|LDL cholesterol|blood glucose|mortality|bone mineral density)\b',
 'design':r'\b(?:randomized controlled trial|randomised controlled trial|cross.sectional|systematic review|meta.analysis|cohort study|crossover|study protocol)\b',
 'limitations':r'[^.!?]*(?:limitation|confound|observational|cannot establish|small sample|self.report)[^.!?]*[.!?]?',
}

def extract(paper):
    fields={key:[] for key in PATTERNS}
    # Prioritize methods/results/abstract. Source links retain exact local offsets.
    passages=sorted(paper['passages'],key=lambda p:0 if p['zone'] in ('methods','results','abstract') else 1)
    for p in passages:
        for field,pattern in PATTERNS.items():
            for m in re.finditer(pattern,p['text'],re.I):
                if len(fields[field])>=5:break
                value=m.group(0)
                if any(v['value'].lower()==value.lower() for v in fields[field]):continue
                fields[field].append({'value':value,'passage_id':p['id'],'section':p['section'],
                    'start':m.start(),'end':m.end(),'source_text':p['text'][max(0,m.start()-100):min(len(p['text']),m.end()+150)],
                    'status':'candidate mention; study attribution not validated'})
    return fields

def compatibility(claim,fields):
    result={}
    for name in ('food_identity','population','baseline_status','dose','frequency','timing','duration','preparation','comparator','substitution','outcome'):
        mentions=[m.group(0) for m in re.finditer(PATTERNS[name],claim,re.I)]
        result[name]={'status':'unknown','reason':'Claim or study context requires reviewed extraction','claim_mentions':mentions,'source_candidates':fields[name]}
        # Same words do not prove same study arm, population or exposure. Do not infer compatibility.
    return result

def inspect_evidence(store,claim,run):
    studies=[]
    for result in run['results']:
        paper=store.paper(result['id']);fields=extract(paper)
        studies.append({'paper_id':paper['id'],'fields':fields,'compatibility':compatibility(claim,fields),
                        'stance':{'status':'unassessed','reason':'No food-domain-validated stance classifier or human judgment attached'},
                        'overlap':'Reviews and primary reports may overlap; not adjudicated'})
    return {'status':'sources_found_assessment_pending' if studies else 'no_sources_retrieved',
            'summary':'These sources are ranked for relevance. Their findings need assessment against the claim and its conditions.' if studies else 'No matching sources were retrieved from this collection. This does not establish that the claim is false.',
            'studies':studies,'scientific_certainty':'not assessed','coverage':'This collection is incomplete; missing counterevidence does not establish consensus.'}
