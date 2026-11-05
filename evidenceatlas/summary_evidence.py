"""Conservative source-role checks; scientific quality still requires review."""
import re

ABSTRACT_HEADINGS = re.compile(r'\b(Background|Objectives?|Aims?|Methods?|Design|Results?|Findings|Conclusions?)\b')

def study_type(paper):
    record=paper.get('metadata',{}).get('source_record',{})
    types=' '.join(record.get('pubTypeList',{}).get('pubType',[])).lower()
    title=paper.get('title','').lower()
    if re.search(r'\breview\b|meta.analysis',title+' '+types):return 'review'
    if re.search(r'clinical trial|randomized controlled trial',types):return 'intervention study'
    abstract=paper.get('abstract','').lower()
    if re.search(r'randomi[sz]|cross.over|intervention',abstract):return 'intervention study'
    if re.search(r'observational|cross.sectional|cohort|longitudinal',abstract):return 'observational study'
    return 'study (design not established)'

def abstract_role(abstract,quote):
    start=abstract.find(quote)
    if start<0:return 'unstructured abstract'
    headings=list(ABSTRACT_HEADINGS.finditer(abstract[:start+1]))
    return headings[-1].group(1).lower() if headings else 'unstructured abstract'

def eligible_note(note,paper):
    section=note['section'].lower()
    passage=next((p for p in paper['passages'] if p['id']==note['passage_id']),{})
    zone=passage.get('zone','')
    kind=study_type(paper)
    if section=='title' or zone in ('title','table','methods','background') or re.search(r'\btable\b',section):return False
    if kind!='review' and (zone=='discussion' or 'discussion' in section):return False
    if section=='abstract':
        role=abstract_role(paper.get('abstract',''),note['quote'])
        if role in ('background','objective','objectives','aim','aims','method','methods','design'):return False
    if re.search(r'\b(previous studies|prior studies|has been shown|is well established|we hypothesi[sz]|our hypothesis|the purpose|the aim|we aimed)\b',note['quote'],re.I):return False
    if kind!='review' and re.search(r'\[\d+(?:[\s,\u2013-]\d+)*\]',note['quote']):return False
    return True

def note_priority(note,paper,query):
    words=set(re.findall(r'[a-z]{3,}',query.lower()))-{'does','the','are','and','can','how','good','bad','every','day'}
    overlap=len(words & set(re.findall(r'[a-z]{3,}',note['quote'].lower())))
    section=note['section'].lower()
    role=abstract_role(paper.get('abstract',''),note['quote']) if section=='abstract' else section
    # Prefer actual results and conclusions over incidental keyword-rich discussion.
    strength=3 if re.search(r'result|finding|conclusion',role) else 2 if section=='abstract' else 1
    return -(strength*3+overlap)

def source_context(note,paper):
    kind=study_type(paper)
    raw={k:note[k] for k in ('title','availability','species','section','quote')}
    raw.update(study_type=kind,evidence_role='review synthesis' if kind=='review' else 'reported findings',
               context='',context_quotes=[])
    # Descriptive context is from the same primary paper's methods, not neighbouring
    # table rows or other studies mentioned by a review. Each span stays inspectable.
    if kind!='review':
        for p in paper['passages']:
            if p.get('zone') not in ('methods','abstract'):continue
            for match in re.finditer(r'[^.!?]+(?:[.!?](?=\s|$)|$)',p['text']):
                text=match.group().strip()
                if len(text)<25 or len(text)>650:continue
                if not re.search(r'participants?|patients?|enrolled|recruited|randomi[sz]ed|aged?\b|consumed|administered|assigned|study design|cross.sectional|cohort',text,re.I):continue
                if re.search(r'previous|prior|results?|findings?|conclusions?|associated|significant|improved|reduced|increased',text,re.I):continue
                if p.get('zone')=='abstract' and abstract_role(paper.get('abstract',''),text) in ('result','results','conclusion','conclusions'):continue
                start=p['text'].find(text,match.start())
                raw['context_quotes'].append({'passage_id':p['id'],'section':p['section'],'quote':text,'start':start,'end':start+len(text)})
                if len(raw['context_quotes'])==3:break
            if len(raw['context_quotes'])==3:break
    raw['context']='\n'.join(x['quote'] for x in raw['context_quotes'])
    return raw

def scope_supported(text,sources):
    """Block the audited errors that exact-quotation matching cannot catch."""
    # A selected excerpt cannot establish paper-wide absence of evidence.
    if re.search(r'\b(?:does|do|did) not (?:provide|specify|address|examine|investigate|report|include|discuss|assess|evaluate|test|measure|determine)|\bno (?:information|data|evidence) (?:on|about|regarding)|\bnot (?:examined|discussed|investigated|specified)\b',text,re.I):return False
    if re.search(r'\b(?:does|do|did) not\b[^.!?]{0,140}\b(?:evaluate|examine|assess|investigate|test|measure|determine)\b',text,re.I):return False
    if any(s.get('study_type')!='review' for s in sources) and re.search(r'\breview\b',text,re.I):return False
    quote=' '.join(s['quote'] for s in sources)
    if re.search(r'\b(?:hypothes\w*|may|might|could|suggest\w*|uncertain\w*)\b',quote,re.I):
        if not re.search(r'\b(?:hypothes\w*|may|might|could|suggest\w*|uncertain\w*)\b',text,re.I):return False
    if re.search(r'\bassociat\w*\b',quote,re.I) and not re.search(r'\bassociat\w*|correlat\w*|linked\b',text,re.I):return False
    return True
