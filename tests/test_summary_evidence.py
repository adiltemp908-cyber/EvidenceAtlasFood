import json
import pytest
from evidenceatlas.summary_evidence import eligible_note,source_context,scope_supported,study_type
from evidenceatlas.summarization import validate_findings
from evidenceatlas.advanced import rerank_text
from evidenceatlas.retrieval import normalize

def paper(abstract,title='Randomized trial of meal timing',zone='abstract',section='Abstract'):
    return {'title':title,'abstract':abstract,'metadata':{},'passages':[{'id':'p','zone':zone,'section':section,'text':abstract}]}

def note(quote,section='Abstract'):
    return {'quote':quote,'section':section,'passage_id':'p','title':'Trial','availability':'full-text','species':'human (MeSH)'}

def test_title_is_not_eligible_finding():
    quote='Creatine increases muscle mass.'
    valid,bad=validate_findings({'findings':[{'source':'S1','quote':quote,'statement':quote}]},
        [{'label':'S1','section':'Title','text':quote}])
    assert valid==[] and bad==1

def test_abstract_background_and_methods_do_not_become_results():
    abstract='Background Eating at night increases diabetes risk. Methods Adults were randomized. Results Night eating raised glucose.'
    p=paper(abstract)
    assert not eligible_note(note('Eating at night increases diabetes risk.'),p)
    assert not eligible_note(note('Adults were randomized.'),p)
    assert eligible_note(note('Night eating raised glucose.'),p)

def test_primary_discussion_is_not_primary_finding_but_review_can_synthesize():
    quote='Prior trials found higher glucose after late meals [35].'
    n=note(quote,'Discussion');p=paper(quote,zone='discussion',section='Discussion')
    assert not eligible_note(n,p)
    p['title']='Meal timing: a systematic review'
    assert eligible_note(n,p)

def test_methods_context_has_exact_offsets_and_excludes_outcomes_and_tables():
    text='Methods Thirty adults aged 20-40 were randomized to two meal times. Results Late eating raised glucose.'
    p=paper(text);p['passages'].append({'id':'table','section':'Table 1','zone':'table','text':'12 months | 4 capsules'})
    source=source_context(note('Late eating raised glucose.'),p)
    assert len(source['context_quotes'])==1
    span=source['context_quotes'][0]
    assert text[span['start']:span['end']]==span['quote']
    assert 'raised glucose' not in source['context'] and 'capsules' not in source['context']

@pytest.mark.parametrize('claim',[
    'The review does not provide information about older adults.',
    'The paper does not specify effects without exercise.',
    'There is no information on older participants.',
    'Older adults were not examined.',
    'The study does not evaluate daily consumption.',
    'The study does not establish causation or evaluate overall health benefits.',
    'The trial did not measure older participants.'
])
def test_absence_in_excerpt_is_not_absence_in_paper(claim):
    assert not scope_supported(claim,[{'quote':'Muscle mass increased.','study_type':'review'}])

def test_study_type_and_hedging_survive_generation():
    source={'quote':'These findings suggest a possible effect.','study_type':'intervention study'}
    assert not scope_supported('The review proves an effect.',[source])
    assert not scope_supported('The study establishes an effect.',[source])
    assert scope_supported('The study suggests a possible effect.',[source])
    source['quote']='Cereal intake was associated with lower weight.'
    assert not scope_supported('Cereal intake reduced weight.',[source])

def test_intervention_is_not_review_due_to_background_word():
    p=paper('A previous review found mixed results. Participants were randomized.')
    assert study_type(p)=='intervention study'

def test_reranking_uses_abstract_outcome_instead_of_incidental_body_match():
    class Tokenizer:
        def encode(self,*args,**kwargs):return ' '.join(args).split()
    p={'title':'Creatine trial','abstract':'We studied adults. Creatine increased lean mass with training.',
       'passages':[{'text':'Muscle damage and soreness were background concerns.','zone':'discussion'}]}
    text=rerank_text(p,'creatine muscle hypertrophy lean mass',Tokenizer(),max_tokens=24)
    assert 'increased lean mass' in text and 'soreness' not in text
    assert len(Tokenizer().encode('creatine muscle hypertrophy lean mass',text))<=24

def test_muscle_growth_expansion_preserves_original_question():
    query='Does creatine help build muscle?';expanded,changes=normalize(query)
    assert expanded.startswith(query) and 'hypertrophy' in expanded and changes


def test_outcome_sentence_is_not_descriptive_context():
    text="The major findings were that cereal consumed at breakfast provided more fiber."
    assert source_context(note(text),paper(text))["context_quotes"]==[]
