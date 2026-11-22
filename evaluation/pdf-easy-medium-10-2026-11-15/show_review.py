import json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent
terms={
'Q01':['coffee','caffeine','sleep','latency','duration'],
'Q02':['sodium','salt','blood pressure','hypertension'],
'Q03':['fiber','fibre','constipation','stool','bowel'],
'Q04':['milk','dairy','bone','fracture'],
'Q05':['boil','vitamin c','ascorbic','vegetable'],
'Q06':['oat','ldl','cholesterol','glucan'],
'Q07':['nut','weight','adipos','obes','adult'],
'Q08':['yogurt','yoghurt','lactose','milk','malabsorp'],
'Q09':['sugar','beverage','drink','diabetes'],
'Q10':['protein','resistance','muscle','hypertroph','lean mass'],
}
docs=json.loads((P/'pool.json').read_text(encoding='utf-8'))
for qid in sys.argv[1:]:
 print('\n'+qid)
 for n,p in enumerate([x for x in docs if x['query_id']==qid],1):
  abstract=p['abstract'] or ''
  sentences=re.split(r'(?<=[.!?])\s+(?=[A-Z])',abstract)
  ranked=sorted(enumerate(sentences),key=lambda x:(-sum(t in x[1].lower() for t in terms[qid]),-int(bool(re.search(r'\b(results|conclu|found|reduc|associat|increase|improv|signific)',x[1],re.I))),-x[0]))
  selected=sorted(ranked[:2])
  print(f'[{n:02}] {p["id"]} | {p["title"]}')
  print('EXTRACT: '+' '.join(s for _,s in selected))
  if not abstract:
   print('PASSAGES: '+'\n'.join(s['text'] for s in p['source_passages']))
