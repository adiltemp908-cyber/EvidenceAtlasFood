from evidenceatlas.topic_screening import screen_topic
from evidenceatlas.taxonomy import EVERYDAY_TOPICS, queries


def test_human_water_requirement_is_eligible_without_mesh():
    result = screen_topic({'title': 'Daily water intake and hydration in healthy adults',
                           'abstractText': 'Participants consumed water; hydration was assessed.'}, 'water_requirements')
    assert result[0] == 'accepted' and result[2] == 'unknown'


def test_cats_and_water_contaminants_are_not_human_intake_evidence():
    for title in ('Water intake and hydration in domestic cats compared with humans',
                  'Drinking water arsenic and health in adults'):
        assert screen_topic({'title': title}, 'water_requirements')[0] == 'needs_review'


def test_old_topics_keep_the_existing_screen():
    record = {'title': 'Protein intake and renal function in rats'}
    assert screen_topic(record, 'protein_kidney')[0] == 'accepted'


def test_contamination_and_protocols_are_held_for_review():
    for title in ('Antimony leaching into drinking water and health in adults',
                  'Water intake and hydration in healthy adults: a trial protocol'):
        assert screen_topic({'title': title}, 'water_requirements')[0] == 'needs_review'


def test_dairy_screen_distinguishes_human_milk_provision():
    assert screen_topic({'title': "Mother's own milk use and health in infants: lactation support"}, 'dairy_tolerance')[0] == 'needs_review'
    assert screen_topic({'title': "Cow's milk consumption and lactose digestion in adults"}, 'dairy_tolerance')[0] == 'accepted'


def test_both_discovery_routes_include_human_context_and_cutoff():
    for topic in EVERYDAY_TOPICS:
        q = queries(topic, '2026-11-04', '2000-01-01')
        assert 'adult[Title/Abstract]' in q['mesh']
        assert '2026/11/04' in q['mesh']
        assert 'adult OR adults' in q['title_abstract']
        assert 'FIRST_PDATE:[2000-01-01 TO 2026-11-04]' in q['title_abstract']
