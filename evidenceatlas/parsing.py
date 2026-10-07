from __future__ import annotations
import hashlib
import html
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

PARSER_VERSION = "jats-section-2"
SCREENING_VERSION = "nutrition-screen-3"

def clean(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()

def text(node):
    if node is None:return ''
    blocks={'p','list','list-item','title','sec','tr','td','th','break'}
    def walk(n):
        value=n.text or ''
        for child in n:
            boundary=' ' if child.tag in blocks else ''
            value+=boundary+walk(child)+boundary+(child.tail or '')
        return value
    return clean(walk(node))

def abstract_text(value):
    class MarkupText(HTMLParser):
        def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
        def handle_data(self,data):self.parts.append(data)
        def handle_starttag(self,tag,attrs):
            if tag in ('p','h4','h3','br','div','li'):self.parts.append(' ')
        def handle_endtag(self,tag):
            if tag in ('p','h4','h3','div','li'):self.parts.append(' ')
    parser=MarkupText();parser.feed(value or '');parser.close()
    return clean(''.join(parser.parts))

def zone(heading):
    h=heading.lower()
    for label, terms in {"methods":("method","material","participant","procedure","statistical"),
                         "results":("result","finding"), "discussion":("discussion",),
                         "conclusion":("conclusion",), "limitations":("limitation",),
                         "background":("introduction","background")}.items():
        if any(t in h for t in terms): return label
    return "body"

def paragraphs_jats(xml):
    # ElementTree does not fetch external entities. Refuse internal declarations as well.
    if b"<!ENTITY" in xml.upper(): raise ValueError("Entity declarations are not accepted")
    root=ET.fromstring(xml)
    for n in root.iter(): n.tag=n.tag.split('}')[-1]
    body=root.find('body')
    if body is None: raise ValueError("Full text lacks an article body")
    parents={child:parent for parent in root.iter() for child in parent}
    result=[]
    def headings(n):
        hs=[]
        while n in parents:
            n=parents[n]
            if n.tag=='sec': hs.append(text(n.find('title')) or n.get('sec-type','Untitled section'))
        return list(reversed(hs))
    for n in body.iter():
        if n.tag not in ('p','table-wrap'): continue
        parent=parents.get(n)
        ancestors=[]
        while parent is not None:
            ancestors.append(parent.tag); parent=parents.get(parent)
        if any(a in ('table-wrap','fig','ref-list','p') for a in ancestors): continue
        hs=headings(n)
        if n.tag=='table-wrap':
            rows=[' | '.join(text(c) for c in row if c.tag in ('td','th')) for row in n.findall('.//tr')]
            value='\n'.join([text(n.find('label')),text(n.find('caption'))]+rows+[text(n.find('table-wrap-foot'))]).strip()
            gaps=[] if rows else ['Table image or unsupported structure; cells unavailable']
            heading=' > '.join(hs+['Table '+(text(n.find('label')) or n.get('id',''))])
            result.append({"section":heading,"zone":"table","text":value,"xml_id":n.get('id'),"gaps":gaps})
        else:
            value=text(n)
            if value: result.append({"section":" > ".join(hs) or "Body", "zone":zone(" ".join(hs)), "text":value,"xml_id":n.get('id'),"gaps":[]})
    if not result: raise ValueError("Full text body has no supported content")
    licenses=[text(n) for n in root.findall('.//permissions/license')]
    return result, {"licenses":licenses,"article_type":root.get('article-type'),"parser":PARSER_VERSION,
                    "body_paragraphs":len(result), "limitations":["Figures and supplements are not ingested", "Table cell spans are flattened; inspect source for complex headers", "Background citations do not imply this study tested the claim"]}

def make_passages(paper_id, title, abstract, body=None):
    source=[{"section":"Title","zone":"title","text":title,"gaps":[],"xml_id":None}]
    if abstract: source.append({"section":"Abstract","zone":"abstract","text":abstract,"gaps":[],"xml_id":None})
    source+=body or []
    result=[]
    for ordinal,p in enumerate(source):
        # Paragraph-based chunks retain exact offsets in the normalized paragraph.
        value=p['text']
        boundaries=[0]
        for match in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9])",value):
            if match.end()-boundaries[-1]>=900: boundaries.append(match.end())
        boundaries.append(len(value))
        section_id=f"{paper_id}:s{ordinal:05d}"
        for chunk,(start,end) in enumerate(zip(boundaries,boundaries[1:])):
            span=value[start:end]
            if not span.strip():continue
            digest=hashlib.sha256(span.encode()).hexdigest()[:12]
            result.append({**p,"id":f"{section_id}:p{chunk}:{digest}","section_id":section_id,"paper_id":paper_id,
                           "text":span,"start":start,"end":end,"ordinal":len(result),"paragraph":value})
            sentences=[];sentence_start=0
            for match in list(re.finditer(r'(?<=[.!?])\s+(?=[A-Z0-9])',span))+[None]:
                sentence_end=match.start() if match else len(span)
                if sentence_end>sentence_start:sentences.append({'id':result[-1]['id']+f':sentence{len(sentences)}','start':sentence_start,'end':sentence_end})
                sentence_start=match.end() if match else len(span)
            result[-1]['sentences']=sentences
    return result

def screen(record, topic_terms):
    title=clean(record.get('title','')).lower()
    abstract=abstract_text(record.get('abstractText','')).lower()
    combined=title+' '+abstract
    mesh=[x.get('descriptorName','') for x in record.get('meshHeadingList',{}).get('meshHeading',[])]
    excluded=re.search(r'\b(crop yield|feed conversion|broiler|packaging film|livestock feed|fertilizer|fertiliser)\b',title)
    human=re.search(r'\b(human|patients?|adults?|participants?|volunteers?|clinical|children|women|men)\b',combined)
    food=any(re.search(r'\b'+re.escape(t),combined) for t in topic_terms)
    health=re.search(r'\b(sleep|insomnia|anxiety|health|kidney|renal|dialysis|hemodialysis|nutritional status|weight|glucose|blood|cardiovascular|nutrient|vitamin|bioavailability|gut|microbi|bowel|cancer|diabet|metabolic|fracture|bone|deficiency|exposure|toxicity|mortality)',combined)
    species="human (MeSH)" if 'Humans' in mesh and 'Animals' not in mesh else "mixed human/animal (MeSH)" if 'Humans' in mesh else "animal (MeSH)" if 'Animals' in mesh else "unknown"
    dietary=re.search(r'\b(dietary|ingestion|oral intake|food intake|feeding|consumption|supplementation|nutrition)\b',combined)
    if re.search(r'\b(topical|ointment|hair growth|skin anti.aging|wound.healing)\b',title) and not dietary:
        return 'excluded','Topical/cosmetic exposure without substantive dietary route',species
    if re.search(r'\b(microbial fermentation|flavor modulation|flavour modulation|decaffeination)\b',title) and not human:
        return 'needs_review','Processing technology; health terms may be background only',species
    if re.search(r'\b(unsaponifiable fraction|anticancer agent|anti.cancer drug)\b',combined) and not dietary:
        return 'needs_review','Isolated pharmacological fraction; dietary relevance not established',species
    if excluded and not human:return 'excluded','Title indicates agricultural/industrial scope without explicit human context',species
    if food and health:return 'accepted','Nutrition entity and health/nutrient outcome found in title/abstract; provisional rule screen',species
    return 'needs_review','Metadata does not establish both nutrition exposure and relevant outcome',species
