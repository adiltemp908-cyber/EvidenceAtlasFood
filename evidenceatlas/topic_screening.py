"""Additional scope checks for everyday human diet acquisition, not evidence grading."""
import re
from .parsing import screen, abstract_text
from .taxonomy import TOPICS, EVERYDAY_TOPICS

VERSION = 'everyday-human-scope-2'


def screen_topic(record, topic):
    decision, reason, species = screen(record, TOPICS[topic][2])
    if topic not in EVERYDAY_TOPICS:
        return decision, reason, species
    title = abstract_text(record.get('title', '')).lower()
    text = title + ' ' + abstract_text(record.get('abstractText', '')).lower()
    if species == 'animal (MeSH)' or re.search(
        r'\b(mice|mouse|rats?|murine|cats?|dogs?|canine|feline|horses?|equine|piglets?|pig|pigs|broilers?|hens?|poultry|zebrafish|aquaculture)\b', title):
        return 'needs_review', 'Everyday human diet batch: animal or veterinary study requires separate review', species
    if re.search(r'\b(wastewater|groundwater|water treatment|arsenic|antimony|pollutants?|trichloroacetic acid|microplastics?|water contamination|drinking water quality|disinfection|fluoride|fluoridation)\b', title):
        return 'needs_review', 'Water quality or contamination, rather than ordinary dietary intake', species
    if re.search(r'\b(protocol|in vitro|environmental impact|bioelectrical impedance|dual.energy x.ray absorptiometry)\b', title):
        return 'needs_review', 'Protocol, laboratory, environmental or measurement focus; direct dietary findings require review', species
    if topic == 'dairy_tolerance' and re.search(r"donor human milk|donor milk|mother.s own milk|lactation support", title):
        return 'needs_review', 'Human-milk provision rather than ordinary dairy intake or lactose tolerance', species
    human = species in ('human (MeSH)', 'mixed human/animal (MeSH)') or re.search(
        r'\b(humans?|adults?|women|men|children|adolescents?|participants?|volunteers?|patients?|people|population|pregnan\w*|elderly)\b', text)
    if not human:
        return 'needs_review', 'Human applicability is not established in title/abstract metadata', species
    if decision == 'accepted':
        reason = 'Human-context everyday diet query plus provisional nutrition/outcome screening; not expert validation'
    return decision, reason, species
