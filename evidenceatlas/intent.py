"""Visible, conservative food-query interpretation; no silent replacement of the claim."""
import re
from .taxonomy import TOPICS
from .evidence import PATTERNS

def interpret(query):
    entities=[]
    for topic,(_,_,terms) in TOPICS.items():
        matched=[t for t in terms if re.search(r'\b'+re.escape(t)+r'\b',query,re.I)]
        if matched:entities.append({'topic':topic,'mentions':matched})
    fields={name:[m.group(0) for m in re.finditer(PATTERNS[name],query,re.I)] for name in ('population','dose','timing','preparation','comparator','outcome')}
    ambiguities=[]
    if re.search(r'\b(healthy|healthier|harmful|better|bad|good)\b',query,re.I) and not fields['outcome']:ambiguities.append('Which outcome matters: sleep, glucose, heart health, weight, or something else?')
    if re.search(r'\b(seed oils?|protein|sweeteners?)\b',query,re.I):ambiguities.append('Food identity, preparation and replacement can matter; the whole category may be too broad.')
    if not fields['population']:ambiguities.append('The population is unspecified; findings may differ for children, healthy adults and people with existing conditions.')
    excluded=bool(re.search(r'\b(recipe for|buy online|shopping list|track my calories)\b',query,re.I))
    return {'original':query,'entities':entities,'context_mentions':fields,'ambiguities':ambiguities,
            'scope':'outside supported research workflow' if excluded else 'food topic recognized' if entities else 'food scope uncertain',
            'action':'clarify a food exposure and health/nutrition outcome' if excluded or not entities else 'retrieve with unresolved conditions visible'}
